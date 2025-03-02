# src/nand_defect_handling/bch.py
#
# BCH (Bose-Chaudhuri-Hocquenghem) Error Correction Code Implementation
# Provides forward error correction capabilities widely used in NAND flash

from functools import lru_cache

import methodtools
import numpy as np


class BCH:
    """
    Implements BCH (Bose-Chaudhuri-Hocquenghem) code for error correction.

    BCH codes are cyclic error-correcting codes constructed using finite fields.
    They're widely used in NAND flash memory due to their strong mathematical
    properties and ability to correct multiple bit errors.

    Parameters:
        m (int): Defines the Galois Field GF(2^m)
        t (int): Maximum number of correctable errors
    """

    def __init__(self, m, t):
        """
        Initialize BCH encoder/decoder with given parameters.

        Args:
            m (int): Defines the Galois Field GF(2^m)
            t (int): Maximum number of correctable errors
        """
        if m < 3 or m > 16:
            raise ValueError(f"Parameter m must be between 3 and 16, got {m}")
        if t < 1 or t > 2**m - 1:
            raise ValueError(f"Parameter t must be between 1 and 2^m-1, got {t}")

        self.m = m
        self.t = t

        # Length of codeword in bits (n = 2^m - 1)
        self.n = (1 << m) - 1

        # Calculate primitive polynomial for field
        self.primitive_poly = self._find_primitive_polynomial(m)

        # Generate lookup tables for finite field operations
        self.alpha_to, self.index_of = self._generate_gf_tables(m, self.primitive_poly)

        # Calculate generator polynomial
        self.generator_poly = self._compute_generator_polynomial()

        # Calculate number of parity bits and message bits
        self.parity_bits = self.generator_poly.size - 1
        self.data_bits = self.n - self.parity_bits

        # For convenience, calculate byte sizes
        self.data_bytes = (self.data_bits + 7) // 8
        self.ecc_bytes = (self.parity_bits + 7) // 8
        self.code_bytes = (self.n + 7) // 8

    def encode(self, data):
        """
        Encode data using BCH code.

        Args:
            data (bytes or bytearray): Input data to encode

        Returns:
            bytes: ECC parity bits
        """
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("Input data must be bytes or bytearray")

        if len(data) > self.data_bytes:
            raise ValueError(f"Input data exceeds maximum size ({len(data)} > {self.data_bytes})")

        # Convert bytes to binary array (MSB first)
        data_bits = np.unpackbits(np.frombuffer(data, dtype=np.uint8))

        # Pad data if needed
        padded_data = np.zeros(self.data_bits, dtype=np.uint8)
        padded_data[: data_bits.size] = data_bits[: self.data_bits]

        # Systematic encoding
        parity = self._calculate_parity(padded_data)

        # Convert parity bits to bytes
        parity_bytes = np.packbits(parity).tobytes()

        return parity_bytes

    def decode(self, encoded_data):
        """
        Decode and correct errors in BCH encoded data.

        Args:
            encoded_data (bytes or bytearray): Data + ECC bytes to decode

        Returns:
            tuple: (corrected_data, num_errors)
        """
        if not isinstance(encoded_data, (bytes, bytearray)):
            raise TypeError("Input data must be bytes or bytearray")

        # For NAND applications, the data and ECC are usually separate
        if len(encoded_data) <= self.ecc_bytes:
            raise ValueError(f"Input data too small, expected at least {self.ecc_bytes+1} bytes")

        # Split into data and ECC parts
        data = encoded_data[: -self.ecc_bytes]
        received_ecc = encoded_data[-self.ecc_bytes :]

        # Convert to bit arrays
        data_bits = np.unpackbits(np.frombuffer(data, dtype=np.uint8))[: self.data_bits]
        ecc_bits = np.unpackbits(np.frombuffer(received_ecc, dtype=np.uint8))[: self.parity_bits]

        # Combine data and ECC for syndrome calculation
        received_codeword = np.zeros(self.n, dtype=np.uint8)
        received_codeword[: self.data_bits] = data_bits
        received_codeword[self.data_bits : self.data_bits + self.parity_bits] = ecc_bits

        # Calculate syndromes
        syndromes = self._calculate_syndromes(received_codeword)

        # Check if any errors
        if not np.any(syndromes):
            return data, 0

        # Find error locations using Berlekamp-Massey algorithm
        error_locator_poly = self._berlekamp_massey(syndromes)

        # Find roots of error locator polynomial using Chien search
        error_locations = self._chien_search(error_locator_poly)

        if error_locations is None:
            # Too many errors to correct
            return None, self.t + 1

        # Create corrected codeword
        corrected_codeword = received_codeword.copy()
        for loc in error_locations:
            corrected_codeword[loc] ^= 1  # Flip the error bit

        # Extract corrected data part
        corrected_data_bits = corrected_codeword[: self.data_bits]

        # If data was partial, truncate back to original size
        original_size = min(len(data) * 8, self.data_bits)
        corrected_data_bits = corrected_data_bits[:original_size]

        # Pad to byte boundary if needed
        if len(corrected_data_bits) % 8 != 0:
            padding = 8 - (len(corrected_data_bits) % 8)
            corrected_data_bits = np.pad(corrected_data_bits, (0, padding), "constant")

        # Convert back to bytes
        corrected_data = np.packbits(corrected_data_bits).tobytes()

        return corrected_data, len(error_locations)

    def _calculate_parity(self, data_bits):
        """
        Calculate parity bits for given data bits using generator polynomial.

        Args:
            data_bits (numpy.ndarray): Data bits to encode

        Returns:
            numpy.ndarray: Parity bits
        """
        # Polynomial multiplication in GF(2) is equivalent to convolution with XOR
        # First, append zeros for parity bits
        message_poly = np.zeros(self.n, dtype=np.uint8)
        message_poly[: self.data_bits] = data_bits

        # Calculate remainder using synthetic division
        remainder = message_poly.copy()
        for i in range(self.data_bits):
            if remainder[i] != 0:
                for j in range(1, self.generator_poly.size):
                    remainder[i + j] ^= self.generator_poly[j]

        # Extract parity bits
        parity = remainder[self.data_bits : self.n]
        return parity

    def _calculate_syndromes(self, received_codeword):
        """
        Calculate syndrome values for received codeword.

        Args:
            received_codeword (numpy.ndarray): Received codeword bits

        Returns:
            numpy.ndarray: Syndrome values
        """
        syndromes = np.zeros(2 * self.t, dtype=np.int32)

        # Calculate syndrome for each power of alpha
        for i in range(2 * self.t):
            power = i + 1  # Syndromes are indexed 1 to 2t
            syndrome = 0

            for j in range(self.n):
                if received_codeword[j] == 1:
                    # Calculate alpha^(power*j) using discrete logarithm
                    idx = (power * j) % self.n
                    syndrome ^= self.alpha_to[idx]

            syndromes[i] = syndrome

        return syndromes

    def _berlekamp_massey(self, syndromes):
        """
        Implement Berlekamp-Massey algorithm to find the error locator polynomial.

        Args:
            syndromes (numpy.ndarray): Syndrome values

        Returns:
            numpy.ndarray: Coefficients of error locator polynomial
        """
        n = len(syndromes)
        L = 0  # Current length of error locator polynomial
        C = np.zeros(n + 1, dtype=np.int32)  # Current error locator polynomial
        B = np.zeros(n + 1, dtype=np.int32)  # Previous error locator polynomial
        C[0] = 1
        B[0] = 1

        for m in range(n):
            # Calculate discrepancy
            d = syndromes[m]
            for i in range(1, L + 1):
                if C[i] != 0 and m - i >= 0:
                    d ^= self._gf_mul(C[i], syndromes[m - i])

            if d == 0:
                # No adjustment needed
                continue

            # Adjust error locator polynomial
            T = C.copy()

            # C(x) = C(x) - d*B(x)*x^(m-L)
            for i in range(n + 1 - (m - L)):
                C[i + (m - L)] ^= self._gf_mul(d, B[i])

            if 2 * L <= m:
                L = m + 1 - L
                # B(x) = C(x)/d
                for i in range(n + 1):
                    B[i] = self._gf_div(T[i], d)

        # Return error locator polynomial up to degree L
        return C[: L + 1]

    def _chien_search(self, error_locator_poly):
        """
        Implement Chien search to find roots of the error locator polynomial.

        Args:
            error_locator_poly (numpy.ndarray): Coefficients of error locator polynomial

        Returns:
            list: Error locations (indices in codeword)
        """
        # The Chien search evaluates the polynomial at all elements of the field
        # and finds which ones are roots (give zero)
        error_locations = []

        for i in range(self.n):
            # Evaluate polynomial at alpha^(-i)
            eval_result = 0
            for j, coef in enumerate(error_locator_poly):
                if coef != 0:
                    # Calculate alpha^(j*(-i)) = alpha^(j*(n-i))
                    power = (j * (self.n - i)) % self.n
                    eval_result ^= self._gf_mul(coef, self.alpha_to[power])

            if eval_result == 0:
                # We found a root at alpha^(-i), which means position i has an error
                error_locations.append(i)

        # Verify number of errors matches degree of polynomial
        if len(error_locations) != len(error_locator_poly) - 1:
            # This indicates more errors than we can correct
            return None

        return error_locations

    def _gf_mul(self, a, b):
        """
        Multiply two elements in the Galois field.

        Args:
            a, b: Field elements

        Returns:
            int: Product in the field
        """
        if a == 0 or b == 0:
            return 0

        log_a = self.index_of[a]
        log_b = self.index_of[b]

        return self.alpha_to[(log_a + log_b) % self.n]

    def _gf_div(self, a, b):
        """
        Divide two elements in the Galois field.

        Args:
            a: Numerator
            b: Denominator (must not be zero)

        Returns:
            int: Quotient in the field
        """
        if a == 0:
            return 0
        if b == 0:
            raise ZeroDivisionError("Division by zero in Galois Field")

        log_a = self.index_of[a]
        log_b = self.index_of[b]

        return self.alpha_to[(log_a - log_b + self.n) % self.n]

    def _find_primitive_polynomial(self, m):
        """
        Find primitive polynomial for GF(2^m).

        Args:
            m (int): Field size parameter

        Returns:
            numpy.ndarray: Coefficients of primitive polynomial
        """
        # Precomputed primitive polynomials for common values of m
        primitive_polys = {
            3: [1, 1, 0, 1],  # x^3 + x + 1
            4: [1, 1, 0, 0, 1],  # x^4 + x + 1
            5: [1, 0, 1, 0, 0, 1],  # x^5 + x^2 + 1
            6: [1, 1, 0, 0, 0, 0, 1],  # x^6 + x + 1
            7: [1, 0, 0, 1, 0, 0, 0, 1],  # x^7 + x^3 + 1
            8: [1, 0, 1, 1, 1, 0, 0, 0, 1],  # x^8 + x^4 + x^3 + x^2 + 1
            9: [1, 0, 0, 0, 1, 0, 0, 0, 0, 1],  # x^9 + x^4 + 1
            10: [1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1],  # x^10 + x^3 + 1
            11: [1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1],  # x^11 + x^2 + 1
            12: [1, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1],  # x^12 + x^6 + x^4 + x + 1
            13: [1, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1],  # x^13 + x^4 + x^3 + x + 1
            14: [1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1],  # x^14 + x^6 + x + 1
            15: [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1],  # x^15 + x^8 + 1
            16: [1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1],  # x^16 + x^12 + x^3 + 1
        }

        if m in primitive_polys:
            return np.array(primitive_polys[m], dtype=np.uint8)
        else:
            raise ValueError(f"No precomputed primitive polynomial for m={m}")

    def _generate_gf_tables(self, m, primitive_poly):
        """
        Generate Galois Field lookup tables for multiplication and division.

        Args:
            m (int): Field size parameter
            primitive_poly (numpy.ndarray): Primitive polynomial coefficients

        Returns:
            tuple: (alpha_to, index_of) - lookup tables
        """
        n = (1 << m) - 1  # Field size

        # Initialize tables
        alpha_to = np.zeros(n + 1, dtype=np.int32)
        index_of = np.zeros(n + 1, dtype=np.int32)

        # alpha_to[i] = α^i, where α is the primitive element
        # index_of[alpha_to[i]] = i

        # Initialize with α^0 = 1
        alpha_to[0] = 1
        index_of[1] = 0

        # Set default value for index_of
        index_of[0] = -1  # Special case: log(0) is undefined

        # Generate tables
        mask = 1
        for i in range(1, n):
            # Multiply by α (primitive element)
            alpha_to[i] = alpha_to[i - 1] << 1

            # If we overflow the field size, apply modulo reduction using primitive polynomial
            if alpha_to[i] & (1 << m):
                # Subtract the primitive polynomial
                alpha_to[i] ^= 1 << m  # Clear the highest bit

                # Apply the rest of the primitive polynomial
                # (excluding the highest term which was just cleared)
                for j in range(m):
                    if primitive_poly[j] == 1:
                        alpha_to[i] ^= 1 << j

            # Update the index table
            index_of[alpha_to[i]] = i

        return alpha_to, index_of

    def _compute_generator_polynomial(self):
        """
        Compute generator polynomial for BCH code.

        Returns:
            numpy.ndarray: Coefficients of generator polynomial
        """
        # The generator polynomial is the LCM of minimal polynomials
        # of α^1, α^3, α^5, ..., α^(2t-1)

        # Start with g(x) = 1
        g = np.array([1], dtype=np.uint8)

        # Keep track of roots we've included
        roots = set()

        # For each consecutive power of α that should be a root
        for i in range(1, 2 * self.t, 2):
            # Check if this root is already covered
            root = i
            if root in roots:
                continue

            # Find the minimal polynomial for α^root
            min_poly = self._find_minimal_polynomial(root)

            # Multiply g(x) by this minimal polynomial
            g = self._polynomial_multiply(g, min_poly)

            # Add all conjugate roots to our set
            for j in range(1, self.m + 1):
                roots.add((root * (2**j)) % self.n)

        return g

    @methodtools.lru_cache(maxsize=128)
    def _find_minimal_polynomial(self, root):
        """
        Find minimal polynomial for α^root.

        Args:
            root: Power of α

        Returns:
            numpy.ndarray: Coefficients of minimal polynomial
        """
        # Initialize with (x + α^root)
        min_poly = np.array([1, self.alpha_to[root % self.n]], dtype=np.uint8)

        # Add conjugate roots (α^(root*2^i))
        for i in range(1, self.m):
            conjugate_root = (root * (2**i)) % self.n
            factor = np.array([1, self.alpha_to[conjugate_root]], dtype=np.uint8)
            min_poly = self._polynomial_multiply(min_poly, factor)

            # Check if we've come full circle
            if conjugate_root == root:
                break

        return min_poly

    def _polynomial_multiply(self, a, b):
        """
        Multiply two polynomials over GF(2).

        Args:
            a, b (numpy.ndarray): Polynomial coefficients

        Returns:
            numpy.ndarray: Coefficients of product polynomial
        """
        result = np.zeros(len(a) + len(b) - 1, dtype=np.uint8)

        for i in range(len(a)):
            for j in range(len(b)):
                result[i + j] ^= a[i] & b[j]  # XOR for addition in GF(2)

        return result
