#!/usr/bin/env python3
# examples/wear_leveling.py

"""
Example demonstrating advanced wear leveling techniques.

This example shows how to:
1. Initialize the NAND controller
2. Monitor wear levels across blocks
3. Perform manual wear leveling operations
4. Visualize wear distribution
"""

import os
import random
import sys

import matplotlib.pyplot as plt
import numpy as np

# Add the project root directory to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

try:
    from src.nand_controller import NANDController
    from src.nand_defect_handling.wear_leveling import WearLevelingEngine
    from src.utils.config import Config, load_config
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Make sure you're running this example from the project root directory")
    sys.exit(1)


def plot_wear_distribution(wear_levels, title="Block Wear Distribution"):
    """Plot the wear level distribution across blocks."""
    plt.figure(figsize=(12, 6))
    
    # Plot wear levels for each block
    plt.bar(range(len(wear_levels)), wear_levels, alpha=0.7)
    
    # Add mean and standard deviation lines
    mean = np.mean(wear_levels)
    std_dev = np.std(wear_levels)
    plt.axhline(y=mean, color='r', linestyle='-', label=f'Mean: {mean:.2f}')
    plt.axhline(y=mean + std_dev, color='g', linestyle='--', 
               label=f'Mean + StdDev: {(mean + std_dev):.2f}')
    plt.axhline(y=max(0, mean - std_dev), color='g', linestyle='--',
               label=f'Mean - StdDev: {max(0, mean - std_dev):.2f}')
    
    # Add labels and title
    plt.xlabel('Block Number')
    plt.ylabel('Erase Count')
    plt.title(title)
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()


def simulate_workload(nand_controller, num_operations=100, hot_blocks_percentage=0.2):
    """
    Simulate a workload with "hot" blocks that get more activity.
    
    Args:
        nand_controller: NANDController instance
        num_operations: Number of operations to simulate
        hot_blocks_percentage: Percentage of blocks that will be "hot"
    """
    print(f"Simulating workload with {num_operations} operations...")
    
    # Get valid block range, avoiding reserved blocks
    reserved_blocks = list(nand_controller.reserved_blocks.values())
    start_block = max(reserved_blocks) + 1
    end_block = nand_controller.num_blocks - 1
    valid_blocks = [b for b in range(start_block, end_block) 
                   if not nand_controller.is_bad_block(b)]
    
    if not valid_blocks:
        print("No valid blocks found for the workload simulation")
        return
    
    # Designate some blocks as "hot" blocks
    num_hot_blocks = max(1, int(len(valid_blocks) * hot_blocks_percentage))
    hot_blocks = random.sample(valid_blocks, num_hot_blocks)
    
    print(f"Designated {len(hot_blocks)} blocks as 'hot': {hot_blocks}")
    
    # Simulate operations with a bias towards hot blocks
    for i in range(num_operations):
        # 80% of operations go to hot blocks, 20% to other valid blocks
        if random.random() < 0.8:
            block = random.choice(hot_blocks)
        else:
            # Choose from non-hot valid blocks
            other_blocks = [b for b in valid_blocks if b not in hot_blocks]
            if other_blocks:
                block = random.choice(other_blocks)
            else:
                block = random.choice(valid_blocks)
        
        # Randomly choose an operation: write or erase
        operation = random.choice(['write', 'erase'])
        
        try:
            if operation == 'write':
                # Write to random page in the block
                page = random.randint(0, nand_controller.pages_per_block - 1)
                data = bytes([random.randint(0, 255) for _ in range(64)])  # Small test data
                nand_controller.write_page(block, page, data)
            elif operation == 'erase':
                # Erase the block
                nand_controller.erase_block(block)
            
            # Print progress
            if (i + 1) % 10 == 0:
                print(f"Completed {i + 1}/{num_operations} operations")
                
        except Exception as e:
            print(f"Error in operation {operation} on block {block}: {e}")


def demonstrate_wear_leveling():
    """Main function demonstrating wear leveling techniques."""
    print("3D NAND Optimization Tool - Wear Leveling Example")
    print("===============================================")
    
    # Load configuration
    config_path = os.path.join('resources', 'config', 'config.yaml')
    if not os.path.exists(config_path):
        print(f"Configuration file not found: {config_path}")
        alternative_path = 'config.yaml'
        if os.path.exists(alternative_path):
            config_path = alternative_path
            print(f"Using alternative configuration: {config_path}")
        else:
            print("No configuration file found. Using default settings.")
            config_dict = {
                'nand_config': {
                    'page_size': 4096,
                    'block_size': 256,
                    'num_blocks': 1024,
                    'oob_size': 128
                },
                'simulation': {
                    'enabled': True,
                    'error_rate': 0.0001
                }
            }
            config = Config(config_dict)
    else:
        config = load_config(config_path)
    
    # Ensure simulation is enabled for safety
    config_dict = config.config if hasattr(config, 'config') else config
    if 'simulation' not in config_dict:
        config_dict['simulation'] = {}
    config_dict['simulation']['enabled'] = True
    
    # Create NAND controller
    print("Initializing NAND controller...")
    nand_controller = NANDController(Config(config_dict))
    nand_controller.initialize()
    
    try:
        # 1. Show initial wear distribution
        print("\nInitial wear distribution:")
        initial_wear = nand_controller.wear_leveling_engine.wear_level_table.copy()
        plot_wear_distribution(initial_wear, "Initial Block Wear Distribution")
        
        # 2. Simulate an uneven workload
        simulate_workload(nand_controller, num_operations=100, hot_blocks_percentage=0.1)
        
        # 3. Show wear distribution after workload
        print("\nWear distribution after workload:")
        after_workload_wear = nand_controller.wear_leveling_engine.wear_level_table.copy()
        plot_wear_distribution(after_workload_wear, "Wear Distribution After Workload")
        
        # 4. Get wear leveling statistics
        min_wear = np.min(after_workload_wear)
        max_wear = np.max(after_workload_wear)
        mean_wear = np.mean(after_workload_wear)
        std_dev = np.std(after_workload_wear)
        
        print("\nWear Leveling Statistics:")
        print(f"  Minimum wear level: {min_wear}")
        print(f"  Maximum wear level: {max_wear}")
        print(f"  Mean wear level: {mean_wear:.2f}")
        print(f"  Standard deviation: {std_dev:.2f}")
        print(f"  Max/Min ratio: {max_wear/min_wear if min_wear > 0 else 'N/A'}")
        
        # 5. Perform manual wear leveling
        print("\nPerforming manual wear leveling...")
        
        # Find least worn block (that's not reserved)
        wear_table = nand_controller.wear_leveling_engine.wear_level_table
        reserved_blocks = list(nand_controller.reserved_blocks.values())
        
        valid_indices = [i for i in range(len(wear_table)) if i not in reserved_blocks]
        valid_wear = [wear_table[i] for i in valid_indices]
        
        least_worn_idx = valid_indices[np.argmin(valid_wear)]
        most_worn_idx = valid_indices[np.argmax(valid_wear)]
        
        print(f"Least worn block: {least_worn_idx} (wear level: {wear_table[least_worn_idx]})")
        print(f"Most worn block: {most_worn_idx} (wear level: {wear_table[most_worn_idx]})")
        
        # Simulate block swap (in real implementation, this would copy data)
        print(f"Swapping blocks {least_worn_idx} and {most_worn_idx}")
        
        # Swap wear levels for demonstration
        temp = wear_table[least_worn_idx]
        wear_table[least_worn_idx] = wear_table[most_worn_idx]
        wear_table[most_worn_idx] = temp
        
        # 6. Show wear distribution after wear leveling
        print("\nWear distribution after manual wear leveling:")
        after_leveling_wear = nand_controller.wear_leveling_engine.wear_level_table.copy()
        plot_wear_distribution(after_leveling_wear, "Wear Distribution After Manual Leveling")
        
        # 7. Demonstrate threshold-based wear leveling
        print("\nDemonstrating threshold-based wear leveling:")
        current_threshold = nand_controller.wear_leveling_engine.wear_threshold
        print(f"Current wear threshold: {current_threshold}")
        
        # Manually calculate if wear leveling should be performed
        should_level = nand_controller.wear_leveling_engine.should_perform_wear_leveling()
        print(f"Should perform wear leveling: {should_level}")
        
        # 8. Show how to set different wear leveling thresholds
        new_threshold = 500
        print(f"\nSetting new wear threshold: {new_threshold}")
        nand_controller.wear_leveling_engine.wear_threshold = new_threshold
        
        # Check again with new threshold
        should_level = nand_controller.wear_leveling_engine.should_perform_wear_leveling()
        print(f"Should perform wear leveling with new threshold: {should_level}")
        
    finally:
        # Shutdown the NAND controller
        print("\nShutting down NAND controller...")
        nand_controller.shutdown()
        
    print("\nWear leveling demonstration completed.")


if __name__ == "__main__":
    demonstrate_wear_leveling()
