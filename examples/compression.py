#!/usr/bin/env python3
# examples/compression.py
# 
# This example demonstrates NAND flash data compression using:
# - LZ4 compression algorithm
# - Zstandard (zstd) compression algorithm
# - Compression level tuning
# - Performance and compression ratio comparisons

import os
import random
import string
import sys
import time

import matplotlib.pyplot as plt
import numpy as np

# Add the project root directory to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

from src.performance_optimization.data_compression import DataCompressor


def print_separator():
    """Print a nice separator for readability"""
    print("\n" + "="*80 + "\n")

def create_test_data(pattern_type='random', size=10000):
    """
    Create test data of different types to evaluate compression performance
    
    Args:
        pattern_type (str): Type of data pattern to generate:
            - 'random': Random bytes
            - 'text': Text with natural language patterns
            - 'repeating': Highly compressible repeating data
            - 'json': JSON-like structured data
            - 'binary': Binary data with some patterns
        size (int): Approximate size of the data in bytes
        
    Returns:
        bytes: Generated test data
    """
    if pattern_type == 'random':
        # Completely random data (least compressible)
        return os.urandom(size)
        
    elif pattern_type == 'text':
        # Text data with natural language patterns
        words = ['the', 'quick', 'brown', 'fox', 'jumps', 'over', 'lazy', 'dog',
                 'lorem', 'ipsum', 'dolor', 'sit', 'amet', 'consectetur', 
                 'adipiscing', 'elit', 'sed', 'do', 'eiusmod', 'tempor', 
                 'incididunt', 'ut', 'labore', 'et', 'dolore', 'magna', 'aliqua']
        
        # Generate text by randomly selecting words
        text = ""
        while len(text) < size:
            sentence_length = random.randint(5, 15)
            sentence = ' '.join(random.choice(words) for _ in range(sentence_length))
            text += sentence + '. '
            
        return text[:size].encode('utf-8')
        
    elif pattern_type == 'repeating':
        # Highly compressible repeating data
        pattern = b'abcdefghijklmnopqrstuvwxyz0123456789'
        repeats = size // len(pattern) + 1
        return (pattern * repeats)[:size]
        
    elif pattern_type == 'json':
        # JSON-like structured data
        json_template = '{{"id": {}, "name": "{}", "value": {}, "active": {}}}'
        json_data = "["
        
        entries = size // 100  # Approximate number of JSON entries
        for i in range(entries):
            name = ''.join(random.choices(string.ascii_letters, k=8))
            value = random.uniform(0, 100)
            active = random.choice(['true', 'false'])
            
            json_data += json_template.format(i, name, value, active)
            if i < entries - 1:
                json_data += ", "
                
        json_data += "]"
        return json_data[:size].encode('utf-8')
        
    elif pattern_type == 'binary':
        # Binary data with some patterns
        # Create a mix of patterns and random data
        binary_data = bytearray()
        
        while len(binary_data) < size:
            # Add some structured data
            if random.random() < 0.7:  # 70% chance of pattern
                pattern_size = random.randint(10, 50)
                pattern = bytes([random.randint(0, 255) for _ in range(10)])
                binary_data.extend(pattern * (pattern_size // 10))
            else:
                # Add some random data
                random_size = random.randint(10, 50)
                binary_data.extend(os.urandom(random_size))
                
        return bytes(binary_data[:size])
    
    # Default to random data
    return os.urandom(size)

def run_compression_test(data, algorithm, levels=None):
    """
    Run compression test on the given data
    
    Args:
        data (bytes): Data to compress
        algorithm (str): Compression algorithm to use ('lz4' or 'zstd')
        levels (list): List of compression levels to test
        
    Returns:
        dict: Test results including compression ratio, speed, etc.
    """
    # Default compression levels if none provided
    if levels is None:
        if algorithm == 'lz4':
            levels = [1, 3, 6, 9]  # LZ4 levels
        else:  # zstd
            levels = [1, 3, 10, 22]  # Zstandard levels
    
    results = []
    original_size = len(data)
    
    print(f"Testing {algorithm} compression on {original_size} bytes of data")
    print(f"{'Level':<10} {'Size (bytes)':<15} {'Ratio':<10} {'Compress Time':<15} {'Decompress Time':<15} {'Speed (MB/s)':<15}")
    print("-" * 80)
    
    for level in levels:
        # Create compressor with the current level
        compressor = DataCompressor(algorithm=algorithm, level=level)
        
        # Compress
        compress_start = time.time()
        compressed_data = compressor.compress(data)
        compress_time = time.time() - compress_start
        
        # Decompress
        decompress_start = time.time()
        decompressed_data = compressor.decompress(compressed_data)
        decompress_time = time.time() - decompress_start
        
        # Calculate metrics
        compressed_size = len(compressed_data)
        compression_ratio = original_size / compressed_size if compressed_size > 0 else 0
        
        # Calculate compression speed in MB/s
        compress_speed = (original_size / 1024 / 1024) / compress_time if compress_time > 0 else 0
        
        # Verify decompression
        if decompressed_data != data:
            print(f"WARNING: Decompression failed for {algorithm} level {level}!")
            verification = False
        else:
            verification = True
        
        # Store results
        result = {
            'algorithm': algorithm,
            'level': level,
            'original_size': original_size,
            'compressed_size': compressed_size,
            'compression_ratio': compression_ratio,
            'compress_time': compress_time,
            'decompress_time': decompress_time,
            'compress_speed': compress_speed,
            'verification': verification
        }
        results.append(result)
        
        # Print result
        print(f"{level:<10} {compressed_size:<15} {compression_ratio:.2f}x{'':<8} "
              f"{compress_time:.6f}s{'':<8} {decompress_time:.6f}s{'':<8} "
              f"{compress_speed:.2f}")
    
    return results

def visualize_results(all_results, data_types):
    """
    Create visualizations of compression results
    
    Args:
        all_results (dict): Dictionary mapping data types to lists of result dictionaries
        data_types (list): List of data types tested
    """
    # Create a figure directory if it doesn't exist
    fig_dir = os.path.join(script_dir, 'figures')
    os.makedirs(fig_dir, exist_ok=True)
    
    # Extract algorithms
    algorithms = list(set(result['algorithm'] for results in all_results.values() for result in results))
    
    # ======== Plot Compression Ratio ========
    plt.figure(figsize=(12, 8))
    
    # Group by data type
    for data_type in data_types:
        results = all_results[data_type]
        
        # Group by algorithm
        for algorithm in algorithms:
            algo_results = [r for r in results if r['algorithm'] == algorithm]
            if not algo_results:
                continue
                
            levels = [r['level'] for r in algo_results]
            ratios = [r['compression_ratio'] for r in algo_results]
            
            plt.plot(levels, ratios, marker='o', label=f"{data_type} - {algorithm}")
    
    plt.title('Compression Ratio by Algorithm, Level, and Data Type')
    plt.xlabel('Compression Level')
    plt.ylabel('Compression Ratio (higher is better)')
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # Save figure
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, 'compression_ratio.png'))
    
    # ======== Plot Compression Speed ========
    plt.figure(figsize=(12, 8))
    
    # Group by data type
    for data_type in data_types:
        results = all_results[data_type]
        
        # Group by algorithm
        for algorithm in algorithms:
            algo_results = [r for r in results if r['algorithm'] == algorithm]
            if not algo_results:
                continue
                
            levels = [r['level'] for r in algo_results]
            speeds = [r['compress_speed'] for r in algo_results]
            
            plt.plot(levels, speeds, marker='o', label=f"{data_type} - {algorithm}")
    
    plt.title('Compression Speed by Algorithm, Level, and Data Type')
    plt.xlabel('Compression Level')
    plt.ylabel('Compression Speed (MB/s, higher is better)')
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # Save figure
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, 'compression_speed.png'))
    
    # ======== Plot Compression vs Decompression Time ========
    plt.figure(figsize=(12, 8))
    
    bar_width = 0.35
    index = np.arange(len(data_types))
    
    for i, algorithm in enumerate(algorithms):
        compress_times = []
        decompress_times = []
        
        for data_type in data_types:
            # Find best compression level result for this algorithm and data type
            algo_results = [r for r in all_results[data_type] if r['algorithm'] == algorithm]
            if algo_results:
                # Use level 3 as a middle ground
                level_results = [r for r in algo_results if r['level'] == 3]
                if level_results:
                    result = level_results[0]
                else:
                    result = algo_results[0]  # Fallback to first result
                    
                compress_times.append(result['compress_time'])
                decompress_times.append(result['decompress_time'])
            else:
                compress_times.append(0)
                decompress_times.append(0)
        
        plt.bar(index + i*bar_width, compress_times, bar_width, 
                alpha=0.8, label=f'{algorithm} Compress')
        plt.bar(index + i*bar_width, decompress_times, bar_width, 
                alpha=0.5, bottom=compress_times, label=f'{algorithm} Decompress')
    
    plt.xlabel('Data Type')
    plt.ylabel('Time (seconds, lower is better)')
    plt.title('Compression and Decompression Time by Algorithm and Data Type')
    plt.xticks(index + bar_width/2, data_types)
    plt.legend()
    
    # Save figure
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, 'compression_time.png'))
    
    print(f"\nVisualization figures saved to {fig_dir}")

def compression_example():
    """
    Main example function demonstrating data compression techniques
    """
    print("=== NAND Flash Data Compression Example ===")
    
    # Data types to test
    data_types = ['random', 'text', 'repeating', 'json', 'binary']
    data_size = 100000  # 100KB for a quick example
    
    # Generate test data for each type
    print("\nGenerating test data...")
    test_data = {}
    for data_type in data_types:
        test_data[data_type] = create_test_data(data_type, data_size)
        print(f"Created {len(test_data[data_type])} bytes of {data_type} data")
    
    # Test LZ4 compression
    print_separator()
    print("Testing LZ4 Compression")
    lz4_results = {}
    
    for data_type in data_types:
        print_separator()
        print(f"Testing LZ4 on {data_type} data:")
        lz4_results[data_type] = run_compression_test(test_data[data_type], 'lz4')
    
    # Test Zstandard compression
    print_separator()
    print("Testing Zstandard (zstd) Compression")
    zstd_results = {}
    
    for data_type in data_types:
        print_separator()
        print(f"Testing Zstandard on {data_type} data:")
        zstd_results[data_type] = run_compression_test(test_data[data_type], 'zstd')
    
    # Combine results for visualization
    all_results = {}
    for data_type in data_types:
        all_results[data_type] = lz4_results[data_type] + zstd_results[data_type]
    
    # Visualize results
    print_separator()
    print("Generating visualizations...")
    try:
        visualize_results(all_results, data_types)
    except Exception as e:
        print(f"Error generating visualizations: {e}")
    
    # Summary
    print_separator()
    print("Data Compression Summary")
    print_separator()
    
    for data_type in data_types:
        print(f"Data type: {data_type}")
        
        # Find best LZ4 result
        best_lz4 = max(lz4_results[data_type], key=lambda x: x['compression_ratio'])
        
        # Find best Zstandard result
        best_zstd = max(zstd_results[data_type], key=lambda x: x['compression_ratio'])
        
        print(f"Best LZ4: Level {best_lz4['level']}, Ratio: {best_lz4['compression_ratio']:.2f}x, Speed: {best_lz4['compress_speed']:.2f} MB/s")
        print(f"Best Zstd: Level {best_zstd['level']}, Ratio: {best_zstd['compression_ratio']:.2f}x, Speed: {best_zstd['compress_speed']:.2f} MB/s")
        
        # Compare
        if best_lz4['compression_ratio'] > best_zstd['compression_ratio']:
            ratio_winner = "LZ4"
        else:
            ratio_winner = "Zstd"
            
        if best_lz4['compress_speed'] > best_zstd['compress_speed']:
            speed_winner = "LZ4"
        else:
            speed_winner = "Zstd"
            
        print(f"Best compression ratio: {ratio_winner}")
        print(f"Best compression speed: {speed_winner}")
        print()

if __name__ == "__main__":
    compression_example()
