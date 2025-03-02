#!/usr/bin/env python3
# examples/basic_operations.py
# 
# This example demonstrates basic NAND flash operations including:
# - Initialization
# - Reading
# - Writing
# - Erasing
# - Error handling
# - Shutdown

import os
import sys
import time

# Add the project root directory to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

from src.nand_controller import NANDController
from src.utils.config import Config, load_config


def load_configuration():
    """Load configuration with fallback to default locations"""
    # Look for config in standard locations
    config_paths = [
        os.path.join(project_root, 'resources', 'config', 'config.yaml'),
        os.path.join('resources', 'config', 'config.yaml'),
        'config.yaml'
    ]
    
    for path in config_paths:
        if os.path.exists(path):
            print(f"Loading configuration from {path}")
            return load_config(path)
    
    # Create minimal default configuration if no file found
    print("No configuration file found. Using default configuration.")
    config_dict = {
        'nand_config': {
            'page_size': 4096,
            'block_size': 64,
            'num_blocks': 1024,
            'oob_size': 128
        },
        'simulation': {
            'enabled': True,  # Use simulator
            'error_rate': 0.0001,
            'initial_bad_block_rate': 0.001
        }
    }
    return Config(config_dict)

def basic_operations_example():
    """
    Demonstrate basic operations with NAND flash controller
    """
    print("=== Basic NAND Flash Operations Example ===")
    
    # Load configuration
    config = load_configuration()
    
    # Create NAND controller (simulation mode for safety)
    config_dict = config.config if hasattr(config, 'config') else config
    config_dict['simulation'] = {'enabled': True}
    
    controller = NANDController(Config(config_dict))
    print("NAND controller created")
    
    try:
        # Initialize the controller
        print("\n--- Initializing NAND Controller ---")
        controller.initialize()
        print("NAND controller initialized successfully")
        
        # Get and show device information
        device_info = controller.get_device_info()
        print("\n--- NAND Device Information ---")
        print(f"Page Size: {device_info['config']['page_size']} bytes")
        print(f"Block Size: {device_info['config']['block_size']} pages")
        print(f"Number of Blocks: {device_info['config']['num_blocks']}")
        
        # Find a good block for the demonstration
        print("\n--- Finding a Good Block ---")
        block = None
        for b in range(10, 20):  # Try blocks 10-19 to avoid system blocks
            if not controller.is_bad_block(b):
                block = b
                print(f"Found good block: {block}")
                break
        
        if block is None:
            print("Could not find a good block. Exiting.")
            return
            
        # Erase the block first
        print("\n--- Erasing Block ---")
        controller.erase_block(block)
        print(f"Block {block} erased successfully")
        
        # Write to the first page
        print("\n--- Writing Data ---")
        page = 0
        test_data = f"Test data written to block {block}, page {page} at {time.time()}".encode('utf-8')
        controller.write_page(block, page, test_data)
        print(f"Data written to block {block}, page {page}")
        
        # Read from the first page
        print("\n--- Reading Data ---")
        read_data = controller.read_page(block, page)
        print(f"Read {len(read_data)} bytes from block {block}, page {page}")
        
        # Verify the data
        if test_data in read_data:
            print("Data verification successful!")
            print(f"Original: {test_data}")
            print(f"Read: {read_data[:len(test_data)]}")
        else:
            print("Data verification failed!")
            print(f"Original: {test_data}")
            print(f"Read: {read_data[:100]}")
            
        # Demonstrate bad block handling
        print("\n--- Bad Block Handling ---")
        next_good = controller.get_next_good_block(block)
        print(f"Next good block after {block} is {next_good}")
        
        # Demonstrate error handling
        print("\n--- Error Handling Example ---")
        try:
            # Try to access an invalid block (beyond range)
            invalid_block = controller.num_blocks + 10
            controller.read_page(invalid_block, 0)
        except Exception as e:
            print(f"Expected error caught: {e}")
        
        # Get usage statistics
        print("\n--- NAND Usage Statistics ---")
        device_info = controller.get_device_info()
        stats = device_info.get('statistics', {})
        
        print(f"Total reads: {stats.get('reads', 0)}")
        print(f"Total writes: {stats.get('writes', 0)}")
        print(f"Total erases: {stats.get('erases', 0)}")
        
        if 'bad_blocks' in stats:
            bad_block_stats = stats['bad_blocks']
            print(f"Bad blocks: {bad_block_stats.get('count', 0)} ({bad_block_stats.get('percentage', 0):.2f}%)")
        
        if 'wear_leveling' in stats:
            wear_stats = stats['wear_leveling']
            print(f"Min erase count: {wear_stats.get('min_erase_count', 0)}")
            print(f"Max erase count: {wear_stats.get('max_erase_count', 0)}")
            print(f"Avg erase count: {wear_stats.get('avg_erase_count', 0):.2f}")
            
    except Exception as e:
        print(f"Error during operations: {e}")
    finally:
        # Always shut down the controller properly
        print("\n--- Shutting Down NAND Controller ---")
        controller.shutdown()
        print("NAND controller shut down successfully")

if __name__ == "__main__":
    basic_operations_example()
