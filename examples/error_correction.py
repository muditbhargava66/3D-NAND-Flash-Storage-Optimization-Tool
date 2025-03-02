#!/usr/bin/env python3
# examples/error_correction.py
# 
# This example demonstrates NAND flash error correction using:
# - BCH (Bose-Chaudhuri-Hocquenghem) codes
# - LDPC (Low-Density Parity-Check) codes
# - Error introduction and correction simulation

import os
import random
import sys
import time

import numpy as np

# Add the project root directory to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

from src.nand_defect_handling.bch import BCH
from src.nand_defect_handling.error_correction import ECCHandler
from src.nand_defect_handling.ldpc import decode as ldpc_decode
from src.nand_defect_handling.ldpc import encode as ldpc_encode
from src.nand_defect_handling.ldpc import make_ldpc
from src.utils.config import Config


def print_separator():
    """Print a nice separator for readability"""
    print("\n" + "="*80 + "\n")

def introduce_random_errors(data, error_count):
    """
    Introduce a specified number of random bit errors into a byte array
    
    Args:
        data (bytes): Original data
        error_count (int): Number of bit errors to introduce
        
    Returns:
        bytes: Corrupted data with bit errors
    """
    # Convert to bytearray for manipulation
    corrupted = bytearray(data)
    data_len = len(corrupted)
    
    # Introduce random bit errors
    for _ in range(error_count):
        # Select random byte
        pos = random.randint(0, data_len - 1)
        # Select random bit in that byte
        bit = random.randint(0, 7)
        # Flip the bit
        corrupted[pos] ^= (1 << bit)
        
    return bytes(corrupted)

def demonstrate_bch():
    """
    Demonstrate BCH error correction capabilities
    """
    print_separator()
    print("BCH (Bose-Chaudhuri-Hocquenghem) Error Correction Demonstration")
    print_separator()
    
    # Set up BCH parameters
    m = 8  # Field size parameter (GF(2^m))
    t = 4  # Error correction capability (bits)
    print(f"Creating BCH code with m={m}, t={t}")
    print(f"This allows correction of up to {t} bit errors")
    
    # Create BCH codec
    bch = BCH(m, t)
    print("BCH codec created successfully")
    print(f"Code length: {bch.n} bits")
    print(f"Data bits: {bch.data_bits}")
    print(f"Parity bits: {bch.parity_bits}")
    
    # Create test data
    test_data = b"This is a test message for BCH error correction demonstration"
    print(f"\nOriginal data ({len(test_data)} bytes): {test_data}")
    
    # Encode the data
    print("\nEncoding data...")
    start_time = time.time()
    encoded_data = bch.encode(test_data)
    encoding_time = time.time() - start_time
    print(f"Encoding completed in {encoding_time:.6f} seconds")
    print(f"ECC size: {len(encoded_data)} bytes")
    
    # Introduce errors
    error_count = min(t, 3)  # Stay within correction capability
    print(f"\nIntroducing {error_count} random bit errors...")
    corrupted_data = test_data + introduce_random_errors(encoded_data, error_count)
    
    # Decode and correct
    print("\nDecoding and correcting errors...")
    start_time = time.time()
    corrected_data, corrected_errors = bch.decode(corrupted_data)
    decoding_time = time.time() - start_time
    print(f"Decoding completed in {decoding_time:.6f} seconds")
    print(f"Detected and corrected {corrected_errors} errors")
    
    # Verify correction
    print("\nVerifying correction...")
    if corrected_data == test_data:
        print("SUCCESS: Corrected data matches original data!")
    else:
        print("ERROR: Corrected data does not match original data")
        
    print(f"Original: {test_data}")
    print(f"Corrected: {corrected_data}")
    
    # Test correction limits
    print("\nTesting correction limits...")
    # Introduce more errors than the code can correct
    excessive_errors = t + 2
    heavily_corrupted = test_data + introduce_random_errors(encoded_data, excessive_errors)
    
    try:
        decoded_heavy, errors_found = bch.decode(heavily_corrupted)
        print(f"Attempted to correct {excessive_errors} errors (beyond the t={t} capability)")
        print(f"Detected {errors_found} errors")
        
        if decoded_heavy == test_data:
            print("Unexpectedly corrected all errors (should not happen)")
        else:
            print("As expected, could not correct all errors")
    except ValueError as e:
        print(f"Error detected when exceeding correction capability: {e}")

def demonstrate_ldpc():
    """
    Demonstrate LDPC error correction capabilities
    """
    print_separator()
    print("LDPC (Low-Density Parity-Check) Error Correction Demonstration")
    print_separator()
    
    # LDPC parameters
    n = 128  # Codeword length (smaller for demonstration)
    d_v = 3   # Variable node degree
    d_c = 6   # Check node degree
    
    print(f"Creating LDPC code with n={n}, d_v={d_v}, d_c={d_c}")
    print("n = codeword length, d_v = variable node degree, d_c = check node degree")
    
    # Create parity-check and generator matrices
    print("\nGenerating LDPC matrices...")
    start_time = time.time()
    h, g = make_ldpc(n, d_v, d_c, systematic=True, sparse=True)
    matrix_time = time.time() - start_time
    print(f"Matrix generation completed in {matrix_time:.6f} seconds")
    
    k = g.shape[1]  # Number of information bits
    print(f"LDPC code created: [{n},{k}] code")
    print(f"Code rate: {k/n:.4f}")
    
    # Create test data
    data_size = k // 8  # Convert to bytes
    test_data = np.random.randint(0, 2, k, dtype=np.uint8)  # Random binary data
    print(f"\nOriginal data ({data_size} bytes equivalent)")
    
    # Encode the data
    print("\nEncoding data...")
    start_time = time.time()
    codeword = ldpc_encode(g, test_data)
    encoding_time = time.time() - start_time
    print(f"Encoding completed in {encoding_time:.6f} seconds")
    
    # Introduce errors
    error_rate = 0.05  # 5% error rate
    num_errors = int(n * error_rate)
    print(f"\nIntroducing {num_errors} random bit errors ({error_rate*100:.1f}% error rate)...")
    
    # Clone the codeword
    corrupted = codeword.copy()
    
    # Flip random bits
    error_positions = random.sample(range(n), num_errors)
    for pos in error_positions:
        corrupted[pos] = 1 - corrupted[pos]  # Flip the bit
        
    # Decode and correct
    print("\nDecoding and correcting errors...")
    start_time = time.time()
    decoded, success = ldpc_decode(h, corrupted, max_iterations=50)
    decoding_time = time.time() - start_time
    print(f"Decoding completed in {decoding_time:.6f} seconds")
    
    # Calculate how many errors were corrected
    corrected_positions = sum(1 for i in error_positions if decoded[i] == test_data[i])
    print(f"Corrected {corrected_positions} out of {num_errors} errors")
    
    # Verify correction
    bit_errors = sum(1 for i in range(k) if decoded[i] != test_data[i])
    bit_error_rate = bit_errors / k
    
    print("\nVerifying correction...")
    print(f"Information bit errors after correction: {bit_errors}/{k} ({bit_error_rate*100:.2f}%)")
    
    if bit_errors == 0:
        print("SUCCESS: All information bits were corrected!")
    else:
        print(f"PARTIAL SUCCESS: {bit_errors} information bits still have errors")
    
    # Test with different error rates
    print("\nTesting LDPC with different error rates...")
    error_rates = [0.02, 0.05, 0.10, 0.15]
    
    for rate in error_rates:
        num_errors = int(n * rate)
        corrupted = codeword.copy()
        
        # Flip random bits
        error_positions = random.sample(range(n), num_errors)
        for pos in error_positions:
            corrupted[pos] = 1 - corrupted[pos]
            
        # Decode
        decoded, success = ldpc_decode(h, corrupted, max_iterations=50)
        
        # Calculate success rate
        info_bit_errors = sum(1 for i in range(k) if decoded[i] != test_data[i])
        print(f"Error rate {rate*100:.1f}%: corrected {num_errors-info_bit_errors} of {num_errors} errors, success={success}")

def demonstrate_ecc_handler():
    """
    Demonstrate the unified ECCHandler for both BCH and LDPC
    """
    print_separator()
    print("ECCHandler Unified Interface Demonstration")
    print_separator()
    
    # Create configuration for ECCHandler
    config_dict = {
        'optimization_config': {
            'error_correction': {
                'algorithm': 'bch',
                'bch_params': {
                    'm': 8,
                    't': 4
                },
                'ldpc_params': {
                    'n': 128,
                    'd_v': 3,
                    'd_c': 6
                }
            }
        }
    }
    config = Config(config_dict)
    
    # Initialize ECCHandler with BCH
    print("\nInitializing ECCHandler with BCH algorithm...")
    ecc_handler = ECCHandler(config)
    print(f"ECCHandler initialized with {ecc_handler.ecc_type} algorithm")
    
    # Test data
    test_data = b"This is a test message for the unified ECCHandler interface"
    print(f"\nOriginal data ({len(test_data)} bytes): {test_data}")
    
    # Encode
    print("\nEncoding data...")
    encoded_data = ecc_handler.encode(test_data)
    print(f"Data encoded with {ecc_handler.ecc_type}, size: {len(encoded_data)} bytes")
    
    # Introduce errors
    error_count = 3
    print(f"\nIntroducing {error_count} random bit errors...")
    corrupted_data = introduce_random_errors(encoded_data, error_count)
    
    # Decode and correct
    print("\nDecoding and correcting errors...")
    corrected_data, corrected_errors = ecc_handler.decode(corrupted_data)
    print(f"Detected and corrected {corrected_errors} errors")
    
    # Verify correction
    print("\nVerifying correction...")
    if test_data in corrected_data:
        print("SUCCESS: Corrected data contains original data!")
    else:
        print("ERROR: Corrected data does not contain original data")
        
    # Switch to LDPC
    print_separator()
    print("Switching ECCHandler to LDPC algorithm")
    
    config_dict['optimization_config']['error_correction']['algorithm'] = 'ldpc'
    config = Config(config_dict)
    
    # Initialize ECCHandler with LDPC
    ecc_handler = ECCHandler(config)
    print(f"ECCHandler initialized with {ecc_handler.ecc_type} algorithm")
    
    # Use smaller data for LDPC demo
    test_data = b"LDPC test"
    print(f"\nOriginal data ({len(test_data)} bytes): {test_data}")
    
    # Encode
    print("\nEncoding data...")
    try:
        encoded_data = ecc_handler.encode(test_data)
        print(f"Data encoded with {ecc_handler.ecc_type}, size: {len(encoded_data)} bytes")
        
        # LDPC encode/decode demo
        print("\nLDPC processing requires more complex logic in practice.")
        print("This is a simplified demonstration.")
    except Exception as e:
        print(f"Note: LDPC encoding might require specific data sizing: {e}")
        print("This is normal in the example environment without full LDPC implementation.")

def error_correction_example():
    """
    Main example function demonstrating different error correction techniques
    """
    print("=== NAND Flash Error Correction Example ===")
    
    try:
        # Demonstrate BCH error correction
        demonstrate_bch()
        
        # Demonstrate LDPC error correction
        demonstrate_ldpc()
        
        # Demonstrate unified ECCHandler
        demonstrate_ecc_handler()
        
    except Exception as e:
        print(f"Error during demonstration: {e}")

if __name__ == "__main__":
    error_correction_example()
