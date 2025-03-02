# src/nand_defect_handling/ldpc.py
#
# LDPC (Low-Density Parity-Check) Error Correction Code Implementation
# Provides extremely strong error correction for NAND flash memory

import numpy as np
import scipy.sparse as sparse


def make_ldpc(n, d_v, d_c, systematic=True, sparse=True):
    """
    Generate LDPC code matrices H (parity-check matrix) and G (generator matrix).

    Args:
        n (int): Codeword length
        d_v (int): Variable node degree (number of checks per variable)
        d_c (int): Check node degree (number of variables per check)
        systematic (bool): Whether to create systematic code
        sparse (bool): Whether to return sparse matrices

    Returns:
        tuple: (H, G) - parity-check matrix and generator matrix
    """
    # Validate parameters
    if n <= 0:
        raise ValueError("Codeword length n must be positive")
    if d_v <= 1:
        raise ValueError("Variable degree d_v must be at least 2")
    if d_c <= 1:
        raise ValueError("Check degree d_c must be at least 2")

    # Calculate number of check nodes
    # n * d_v = m * d_c (total number of edges must match)
    m = (n * d_v) // d_c
    if (n * d_v) % d_c != 0:
        raise ValueError(f"Can't create regular LDPC with n={n}, d_v={d_v}, d_c={d_c}")

    # Check that the parameters allow for a proper code
    k = n - m  # Number of information bits
    if k <= 0:
        raise ValueError("Parameters result in a code with no information bits (rate=0)")

    # Create parity-check matrix H using Progressive Edge-Growth (PEG) algorithm
    H = _create_peg_matrix(n, m, d_v, d_c)

    # If systematic form is requested, convert H to systematic form
    if systematic:
        H, P = _convert_to_systematic(H)
        G = _create_generator_matrix(H, P, k, n)
    else:
        # Non-systematic form
        G = _create_general_generator_matrix(H, n)

    # Convert to sparse representation if requested
    if sparse:
        H = sparse.csr_matrix(H)
        G = sparse.csr_matrix(G)

    return H, G


def encode(G, data):
    """
    Encode data using LDPC code.

    Args:
        G: Generator matrix (sparse or dense)
        data: Data bits to encode (bytes, array, or binary sequence)

    Returns:
        numpy.ndarray: Encoded codeword
    """
    # Convert input data to binary array if not already
    if isinstance(data, (bytes, bytearray)):
        data_bits = np.unpackbits(np.frombuffer(data, dtype=np.uint8))
    else:
        data_bits = np.asarray(data, dtype=np.uint8)

    # Check if data size matches generator matrix
    k = G.shape[1]  # Number of information bits
    if data_bits.size > k:
        raise ValueError(f"Input data exceeds capacity ({data_bits.size} > {k} bits)")

    # Pad data if smaller than k
    if data_bits.size < k:
        padded_data = np.zeros(k, dtype=np.uint8)
        padded_data[: data_bits.size] = data_bits
        data_bits = padded_data

    # Encode using generator matrix (c = G * d)
    if sparse.issparse(G):
        codeword = G.dot(data_bits) % 2
    else:
        codeword = np.mod(G @ data_bits, 2)

    return codeword


def decode(H, received_codeword, max_iterations=50, early_termination=True):
    """
    Decode LDPC codeword using belief propagation algorithm.

    Args:
        H: Parity-check matrix (sparse or dense)
        received_codeword: Received codeword bits
        max_iterations (int): Maximum number of belief propagation iterations
        early_termination (bool): Whether to stop when valid codeword is found

    Returns:
        tuple: (decoded_data, success) - decoded data bits and success flag
    """
    # Convert input to numpy array if not already
    if isinstance(received_codeword, (bytes, bytearray)):
        received_bits = np.unpackbits(np.frombuffer(received_codeword, dtype=np.uint8))
    else:
        received_bits = np.asarray(received_codeword, dtype=np.uint8)

    # Get matrix dimensions
    if sparse.issparse(H):
        H_dense = H.toarray()
        m, n = H.shape
    else:
        H_dense = H
        m, n = H.shape

    # Calculate number of information bits
    k = n - m

    # Initialize channel LLRs (Log-Likelihood Ratios)
    # For hard-decision decoding, we'll use simple values
    # LLR = +inf for received 0, -inf for received 1
    # Use large but finite values for numerical stability
    llrs = np.zeros(n, dtype=np.float64)
    for i in range(n):
        if received_bits[i] == 0:
            llrs[i] = 10.0  # Strong belief in 0
        else:
            llrs[i] = -10.0  # Strong belief in 1

    # Perform belief propagation decoding
    decoded_bits = _belief_propagation_decode(H_dense, llrs, max_iterations, early_termination)

    # Check if valid codeword (H * c = 0)
    if sparse.issparse(H):
        syndrome = H.dot(decoded_bits) % 2
    else:
        syndrome = np.mod(H @ decoded_bits, 2)

    success = np.all(syndrome == 0)

    # If this is a systematic code, extract information bits
    # Otherwise, return full codeword
    if k > 0 and k < n:
        return decoded_bits[:k], success
    else:
        return decoded_bits, success


def _belief_propagation_decode(H, llrs, max_iterations, early_termination):
    """
    Perform belief propagation decoding.

    Args:
        H: Parity-check matrix (dense)
        llrs: Channel log-likelihood ratios
        max_iterations: Maximum number of iterations
        early_termination: Whether to stop when valid codeword is found

    Returns:
        numpy.ndarray: Decoded codeword bits
    """
    m, n = H.shape

    # Create factor graph structure
    var_to_check = []  # For each variable node, list of connected check nodes
    check_to_var = []  # For each check node, list of connected variable nodes

    for i in range(n):
        var_to_check.append(np.where(H[:, i] == 1)[0])

    for j in range(m):
        check_to_var.append(np.where(H[j, :] == 1)[0])

    # Initialize messages
    # Variable-to-check messages (initialized with channel LLRs)
    v_to_c = {}
    for i in range(n):
        for j in var_to_check[i]:
            v_to_c[(i, j)] = llrs[i]

    # Check-to-variable messages (initialized with zeros)
    c_to_v = {}
    for j in range(m):
        for i in check_to_var[j]:
            c_to_v[(j, i)] = 0.0

    # Belief propagation iterations
    for _ in range(max_iterations):
        # Update check-to-variable messages
        for j in range(m):
            for i in check_to_var[j]:
                # Compute product of tanh(v_to_c/2) excluding the current edge
                prod = 1.0
                for i2 in check_to_var[j]:
                    if i2 != i:
                        prod *= np.tanh(v_to_c[(i2, j)] / 2)

                # Update message
                if abs(prod) > 0.99999:  # Handle numerical issues
                    prod = 0.99999 * np.sign(prod)

                c_to_v[(j, i)] = 2 * np.arctanh(prod)

        # Update variable-to-check messages
        for i in range(n):
            for j in var_to_check[i]:
                # Sum all incoming messages except from current check
                v_to_c[(i, j)] = llrs[i]
                for j2 in var_to_check[i]:
                    if j2 != j:
                        v_to_c[(i, j)] += c_to_v[(j2, i)]

        # Compute current beliefs
        beliefs = llrs.copy()
        for i in range(n):
            for j in var_to_check[i]:
                beliefs[i] += c_to_v[(j, i)]

        # Make hard decisions
        decoded_bits = np.zeros(n, dtype=np.uint8)
        for i in range(n):
            if beliefs[i] < 0:
                decoded_bits[i] = 1

        # Check if valid codeword
        if early_termination:
            valid = True
            for j in range(m):
                # Calculate parity for this check
                parity = 0
                for i in check_to_var[j]:
                    parity ^= decoded_bits[i]

                if parity != 0:
                    valid = False
                    break

            if valid:
                return decoded_bits

    # Return best estimate after max iterations
    return decoded_bits


def _create_peg_matrix(n, m, d_v, d_c):
    """
    Create LDPC matrix using Progressive Edge-Growth (PEG) algorithm.

    Args:
        n (int): Number of variable nodes (columns)
        m (int): Number of check nodes (rows)
        d_v (int): Variable node degree
        d_c (int): Check node degree

    Returns:
        numpy.ndarray: Binary parity-check matrix
    """
    H = np.zeros((m, n), dtype=np.uint8)
    check_degrees = np.zeros(m, dtype=np.uint8)

    # Add edges for each variable node
    for j in range(n):
        # Find check nodes with lowest degrees
        for _ in range(d_v):
            available_checks = np.where(check_degrees < d_c)[0]
            if len(available_checks) == 0:
                raise ValueError("Cannot construct valid LDPC matrix with given parameters")

            # Choose check node with minimum degree
            min_degree_checks = available_checks[check_degrees[available_checks] == min(check_degrees[available_checks])]
            i = np.random.choice(min_degree_checks)

            H[i, j] = 1
            check_degrees[i] += 1

    return H


def _convert_to_systematic(H):
    """
    Convert parity-check matrix to systematic form [P|I].

    Args:
        H: Original parity-check matrix

    Returns:
        tuple: (H_systematic, P) - Systematic form of H and P matrix
    """
    m, n = H.shape
    k = n - m

    # Perform Gaussian elimination
    H_work = _row_echelon_form(H.copy())

    # Extract P and create systematic form
    P = H_work[:, :k]
    H_systematic = np.hstack((P, np.eye(m, dtype=np.uint8)))

    return H_systematic, P


def _create_generator_matrix(H, P, k, n):
    """
    Create generator matrix G for systematic LDPC code.

    Args:
        H: Systematic parity-check matrix
        P: P matrix from systematic form [P|I]
        k: Number of information bits
        n: Codeword length

    Returns:
        numpy.ndarray: Generator matrix G
    """
    # For systematic code, G = [I|P^T]
    G = np.hstack((np.eye(k, dtype=np.uint8), P.T))
    return G


def _create_general_generator_matrix(H, n):
    """
    Create generator matrix G for non-systematic LDPC code.

    Args:
        H: Parity-check matrix
        n: Codeword length

    Returns:
        numpy.ndarray: Generator matrix G
    """
    # Find null space of H to get G
    # First convert H to reduced row echelon form
    H_rref = _row_echelon_form(H.copy())
    m = H.shape[0]
    k = n - m

    # Create generator matrix
    G = np.zeros((k, n), dtype=np.uint8)
    rank = 0
    pivot_cols = []

    # Find pivot columns
    for r in range(m):
        for c in range(n):
            if H_rref[r, c] == 1:
                pivot_cols.append(c)
                rank += 1
                break

    # Set non-pivot columns in G
    g_row = 0
    for c in range(n):
        if c not in pivot_cols:
            G[g_row, c] = 1
            for i, p_col in enumerate(pivot_cols):
                G[g_row, p_col] = H_rref[i, c]
            g_row += 1

    return G


def _row_echelon_form(A):
    """
    Transform matrix to row echelon form using Gaussian elimination.

    Args:
        A: Matrix to transform

    Returns:
        numpy.ndarray: Matrix in row echelon form
    """
    m, n = A.shape

    # Start from the leftmost column
    r = 0
    for c in range(n):
        # Find a row with a 1 in the current column
        for i in range(r, m):
            if A[i, c] == 1:
                # Swap rows
                A[[r, i]] = A[[i, r]]
                break
        else:
            # No pivot in this column, move to the next
            continue

        # Eliminate 1s below the pivot
        for i in range(r + 1, m):
            if A[i, c] == 1:
                A[i] = np.mod(A[i] + A[r], 2)

        r += 1
        if r == m:
            # Full rank, done
            break

    # Back-substitution (make it reduced row echelon form)
    for r in range(m - 1, 0, -1):
        # Find pivot column
        pivot_col = -1
        for c in range(n):
            if A[r, c] == 1:
                pivot_col = c
                break

        if pivot_col >= 0:
            # Eliminate 1s above the pivot
            for i in range(r):
                if A[i, pivot_col] == 1:
                    A[i] = np.mod(A[i] + A[r], 2)

    return A
