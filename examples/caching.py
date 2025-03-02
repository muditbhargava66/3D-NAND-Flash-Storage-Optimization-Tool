#!/usr/bin/env python3
# examples/caching.py
# 
# This example demonstrates the advanced caching system:
# - Different eviction policies (LRU, LFU, FIFO)
# - Time-based expiration
# - Cache statistics
# - Performance comparison

import os
import random
import sys
import time
from collections import Counter

import matplotlib.pyplot as plt
import numpy as np

# Add the project root directory to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

from src.performance_optimization.caching import CachingSystem, EvictionPolicy


def print_separator():
    """Print a nice separator for readability"""
    print("\n" + "="*80 + "\n")

# Define a function that simulates expensive operations
def expensive_operation(key, delay=0.01):
    """
    Simulate an expensive operation (like reading from NAND flash)
    
    Args:
        key: The key to process
        delay: Time in seconds to simulate operation delay
        
    Returns:
        str: Result of the operation
    """
    time.sleep(delay)  # Simulate delay
    return f"Data for {key} (computed at {time.time():.6f})"

def generate_keys(num_keys, distribution='uniform'):
    """
    Generate test keys with different access patterns
    
    Args:
        num_keys: Number of unique keys to generate
        distribution: Distribution pattern ('uniform', 'pareto', 'zipf')
        
    Returns:
        list: List of keys
    """
    # Generate base keys
    base_keys = [f'key_{i}' for i in range(num_keys)]
    
    if distribution == 'uniform':
        # Uniform distribution - each key has equal probability
        return base_keys
    
    elif distribution == 'pareto':
        # Pareto distribution - 20% of keys account for 80% of accesses
        popular_keys = base_keys[:int(num_keys * 0.2)]  # Top 20%
        regular_keys = base_keys[int(num_keys * 0.2):]  # Remaining 80%
        
        # Generate sequence with 80% popular keys
        keys = []
        for _ in range(num_keys):
            if random.random() < 0.8:
                keys.append(random.choice(popular_keys))
            else:
                keys.append(random.choice(regular_keys))
        return keys
    
    elif distribution == 'zipf':
        # Zipfian distribution - frequency proportional to 1/rank
        # Create probabilities based on Zipf's law
        probs = [1/(i+1) for i in range(num_keys)]
        total = sum(probs)
        probs = [p/total for p in probs]
        
        # Generate sequence based on probabilities
        return random.choices(base_keys, weights=probs, k=num_keys)
    
    return base_keys  # Default to uniform

def demonstrate_lru_cache():
    """
    Demonstrate Least Recently Used (LRU) caching
    """
    print_separator()
    print("LRU (Least Recently Used) Cache Demonstration")
    print_separator()
    
    # Create LRU cache
    cache_capacity = 5
    lru_cache = CachingSystem(capacity=cache_capacity, policy=EvictionPolicy.LRU)
    print(f"Created LRU cache with capacity {cache_capacity}")
    
    # Demonstrate basic usage
    print("\n--- Basic Usage ---")
    for i in range(1, 6):
        key = f"item_{i}"
        value = f"value_{i}"
        print(f"Putting {key}: {value}")
        lru_cache.put(key, value)
    
    # Show all items in cache
    print("\nInitial cache contents:")
    for key in lru_cache.get_keys():
        print(f"  {key}: {lru_cache.get(key)}")
    
    # Access an item to make it most recently used
    print("\nAccessing item_2")
    print(f"  Result: {lru_cache.get('item_2')}")
    
    # Add a new item that will cause eviction
    print("\nAdding item_6 - this will cause eviction")
    lru_cache.put("item_6", "value_6")
    
    # Show updated cache contents - item_1 should be evicted (least recently used)
    print("\nUpdated cache contents:")
    for key in lru_cache.get_keys():
        print(f"  {key}: {lru_cache.get(key)}")
    
    # Check for evicted item
    item1 = lru_cache.get("item_1")
    if item1 is None:
        print("\nitem_1 was correctly evicted as the least recently used item")
    else:
        print(f"\nUnexpected: item_1 is still in cache: {item1}")
    
    # Update an existing item
    print("\nUpdating item_3 with new value")
    lru_cache.put("item_3", "updated_value_3")
    print(f"  New value: {lru_cache.get('item_3')}")
    
    # Demonstrate cache statistics
    print("\n--- Cache Statistics ---")
    stats = lru_cache.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

def demonstrate_lfu_cache():
    """
    Demonstrate Least Frequently Used (LFU) caching
    """
    print_separator()
    print("LFU (Least Frequently Used) Cache Demonstration")
    print_separator()
    
    # Create LFU cache
    cache_capacity = 5
    lfu_cache = CachingSystem(capacity=cache_capacity, policy=EvictionPolicy.LFU)
    print(f"Created LFU cache with capacity {cache_capacity}")
    
    # Add initial items
    print("\n--- Initial Setup ---")
    for i in range(1, 6):
        key = f"item_{i}"
        value = f"value_{i}"
        print(f"Putting {key}: {value}")
        lfu_cache.put(key, value)
    
    # Access some items multiple times to increase their frequency
    print("\n--- Accessing items to change frequency ---")
    access_pattern = {
        "item_1": 3,  # Access 3 times
        "item_2": 5,  # Access 5 times
        "item_3": 1,  # Access 1 time
        "item_4": 2,  # Access 2 times
        "item_5": 1   # Access 1 time
    }
    
    for key, frequency in access_pattern.items():
        for _ in range(frequency):
            value = lfu_cache.get(key)
            print(f"Accessing {key}: {value}")
    
    # Add a new item that will cause eviction
    print("\n--- Adding new item to cause eviction ---")
    lfu_cache.put("item_6", "value_6")
    
    # Show updated cache contents - item_3 or item_5 should be evicted (least frequently used)
    print("\nUpdated cache contents:")
    for key in lfu_cache.get_keys():
        print(f"  {key}: {lfu_cache.get(key)}")
    
    # Check for expected eviction
    evicted_keys = []
    for key in ["item_1", "item_2", "item_3", "item_4", "item_5"]:
        if lfu_cache.get(key) is None:
            evicted_keys.append(key)
    
    if evicted_keys:
        print(f"\nThe following items were evicted: {evicted_keys}")
        print("The LFU policy evicts the least frequently accessed item")
    else:
        print("\nUnexpected: No items were evicted")

def demonstrate_fifo_cache():
    """
    Demonstrate First-In-First-Out (FIFO) caching
    """
    print_separator()
    print("FIFO (First-In-First-Out) Cache Demonstration")
    print_separator()
    
    # Create FIFO cache
    cache_capacity = 5
    fifo_cache = CachingSystem(capacity=cache_capacity, policy=EvictionPolicy.FIFO)
    print(f"Created FIFO cache with capacity {cache_capacity}")
    
    # Add initial items
    print("\n--- Initial Setup ---")
    for i in range(1, 6):
        key = f"item_{i}"
        value = f"value_{i}"
        print(f"Putting {key}: {value}")
        fifo_cache.put(key, value)
    
    # Access an item - should not affect eviction order in FIFO
    print("\n--- Accessing items (should not affect FIFO order) ---")
    for i in range(5, 0, -1):  # Access in reverse order
        key = f"item_{i}"
        value = fifo_cache.get(key)
        print(f"Accessing {key}: {value}")
    
    # Add a new item that will cause eviction
    print("\n--- Adding new item to cause eviction ---")
    fifo_cache.put("item_6", "value_6")
    
    # Show updated cache contents - item_1 should be evicted (first in)
    print("\nUpdated cache contents:")
    for key in fifo_cache.get_keys():
        print(f"  {key}: {fifo_cache.get(key)}")
    
    # Check for expected eviction
    item1 = fifo_cache.get("item_1")
    if item1 is None:
        print("\nitem_1 was correctly evicted as the first-in item")
    else:
        print(f"\nUnexpected: item_1 is still in cache: {item1}")

def demonstrate_ttl_cache():
    """
    Demonstrate Time-To-Live (TTL) caching
    """
    print_separator()
    print("TTL (Time-To-Live) Cache Demonstration")
    print_separator()
    
    # Create TTL cache
    cache_capacity = 10
    ttl = 1.0  # 1 second TTL
    ttl_cache = CachingSystem(capacity=cache_capacity, policy=EvictionPolicy.TTL, ttl=ttl)
    print(f"Created TTL cache with capacity {cache_capacity} and TTL {ttl} seconds")
    
    # Add items to cache
    print("\n--- Adding items to cache ---")
    for i in range(1, 6):
        key = f"item_{i}"
        value = f"value_{i}"
        print(f"Putting {key}: {value}")
        ttl_cache.put(key, value)
    
    # Verify items are in cache
    print("\nInitial cache contents:")
    for key in ttl_cache.get_keys():
        print(f"  {key}: {ttl_cache.get(key)}")
    
    # Wait for TTL to expire
    print(f"\nWaiting {ttl+0.1} seconds for TTL to expire...")
    time.sleep(ttl + 0.1)
    
    # Check cache contents after TTL expiration
    print("\nCache contents after TTL expiration:")
    items_found = False
    for i in range(1, 6):
        key = f"item_{i}"
        value = ttl_cache.get(key)
        print(f"  {key}: {value}")
        if value is not None:
            items_found = True
    
    if not items_found:
        print("\nAll items have correctly expired and been removed from the cache")
    else:
        print("\nUnexpected: Some items are still in the cache after TTL expiration")
    
    # Demonstrate setting individual TTL
    print("\n--- Setting individual TTL for items ---")
    
    # Add item with short TTL
    print("Adding item_short with 0.5 second TTL")
    ttl_cache.put("item_short", "short_ttl_value")
    ttl_cache.set_ttl("item_short", 0.5)
    
    # Add item with longer TTL
    print("Adding item_long with 2 second TTL")
    ttl_cache.put("item_long", "long_ttl_value")
    ttl_cache.set_ttl("item_long", 2.0)
    
    # Wait for short TTL to expire
    print("\nWaiting 0.6 seconds for short TTL to expire...")
    time.sleep(0.6)
    
    # Check items
    print("\nChecking items after 0.6 seconds:")
    print(f"  item_short: {ttl_cache.get('item_short')}")
    print(f"  item_long: {ttl_cache.get('item_long')}")
    
    # Wait for long TTL to expire
    print("\nWaiting 1.5 more seconds for long TTL to expire...")
    time.sleep(1.5)
    
    # Check items again
    print("\nChecking items after 2.1 total seconds:")
    print(f"  item_short: {ttl_cache.get('item_short')}")
    print(f"  item_long: {ttl_cache.get('item_long')}")

def cache_performance_test():
    """
    Test and compare performance of different caching policies
    """
    print_separator()
    print("Cache Performance Comparison")
    print_separator()
    
    # Cache configurations
    capacity = 100
    operations = 1000
    unique_keys = 300  # More than cache capacity to cause evictions
    access_delay = 0.001  # Simulated access delay in seconds
    
    # Create caches with different policies
    caches = {
        'LRU': CachingSystem(capacity=capacity, policy=EvictionPolicy.LRU),
        'LFU': CachingSystem(capacity=capacity, policy=EvictionPolicy.LFU),
        'FIFO': CachingSystem(capacity=capacity, policy=EvictionPolicy.FIFO)
    }
    
    # Test distributions
    distributions = ['uniform', 'pareto', 'zipf']
    
    # Initialize result storage
    results = {}
    for policy in caches.keys():
        results[policy] = {}
        for dist in distributions:
            results[policy][dist] = {
                'hit_ratio': 0,
                'execution_time': 0,
                'hits': 0,
                'misses': 0
            }
    
    # Run tests for each distribution
    for distribution in distributions:
        print(f"\n--- Testing with {distribution} distribution ---")
        
        # Generate keys for this distribution
        keys = generate_keys(operations, distribution)
        
        # Count key frequency for analysis
        key_counts = Counter(keys)
        print(f"Generated {len(keys)} keys with {len(key_counts)} unique values")
        print(f"Most common: {key_counts.most_common(5)}")
        
        # Run test for each cache policy
        for policy_name, cache in caches.items():
            print(f"\nTesting {policy_name} cache...")
            
            # Clear cache
            cache.clear()
            
            # Track hits and misses
            hits = 0
            misses = 0
            
            # Measure execution time
            start_time = time.time()
            
            # Perform operations
            for key in keys:
                # Try to get from cache
                value = cache.get(key)
                
                if value is None:
                    # Cache miss - perform expensive operation
                    misses += 1
                    value = expensive_operation(key, access_delay)
                    cache.put(key, value)
                else:
                    # Cache hit
                    hits += 1
            
            # Measure elapsed time
            execution_time = time.time() - start_time
            
            # Calculate hit ratio
            hit_ratio = hits / len(keys) if len(keys) > 0 else 0
            
            # Store results
            results[policy_name][distribution]['hit_ratio'] = hit_ratio
            results[policy_name][distribution]['execution_time'] = execution_time
            results[policy_name][distribution]['hits'] = hits
            results[policy_name][distribution]['misses'] = misses
            
            # Print policy results
            print(f"  Hits: {hits}, Misses: {misses}")
            print(f"  Hit ratio: {hit_ratio:.2%}")
            print(f"  Execution time: {execution_time:.2f} seconds")
    
    # Create visualization
    # Create a figure directory if it doesn't exist
    fig_dir = os.path.join(script_dir, 'figures')
    os.makedirs(fig_dir, exist_ok=True)
    
    # Plot hit ratios
    plt.figure(figsize=(10, 6))
    
    x = np.arange(len(distributions))
    width = 0.25
    
    for i, (policy, policy_results) in enumerate(results.items()):
        hit_ratios = [policy_results[dist]['hit_ratio'] for dist in distributions]
        plt.bar(x + i*width, hit_ratios, width, label=policy)
    
    plt.ylabel('Hit Ratio')
    plt.title('Cache Hit Ratio by Policy and Distribution')
    plt.xticks(x + width, distributions)
    plt.ylim(0, 1.0)
    plt.legend()
    plt.grid(axis='y', alpha=0.3)
    
    # Save hit ratio figure
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, 'cache_hit_ratio.png'))
    
    # Plot execution times
    plt.figure(figsize=(10, 6))
    
    for i, (policy, policy_results) in enumerate(results.items()):
        exec_times = [policy_results[dist]['execution_time'] for dist in distributions]
        plt.bar(x + i*width, exec_times, width, label=policy)
    
    plt.ylabel('Execution Time (seconds)')
    plt.title('Cache Execution Time by Policy and Distribution')
    plt.xticks(x + width, distributions)
    plt.legend()
    plt.grid(axis='y', alpha=0.3)
    
    # Save execution time figure
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, 'cache_execution_time.png'))
    
    print(f"\nPerformance visualization figures saved to {fig_dir}")
    
    # Results summary
    print_separator()
    print("Cache Performance Summary")
    print_separator()
    
    print("Hit Ratio by Policy and Distribution:")
    for dist in distributions:
        print(f"\n{dist.capitalize()} Distribution:")
        for policy, policy_results in results.items():
            hit_ratio = policy_results[dist]['hit_ratio']
            print(f"  {policy}: {hit_ratio:.2%}")
    
    print("\nBest Policy for Each Distribution:")
    for dist in distributions:
        best_policy = max(results.keys(), key=lambda p: results[p][dist]['hit_ratio'])
        best_ratio = results[best_policy][dist]['hit_ratio']
        print(f"  {dist.capitalize()}: {best_policy} ({best_ratio:.2%})")

def caching_example():
    """
    Main example function demonstrating different caching techniques
    """
    print("=== NAND Flash Caching System Example ===")
    
    try:
        # Demonstrate different cache eviction policies
        demonstrate_lru_cache()
        demonstrate_lfu_cache()
        demonstrate_fifo_cache()
        demonstrate_ttl_cache()
        
        # Performance comparison
        cache_performance_test()
        
    except Exception as e:
        print(f"Error during cache demonstration: {e}")

if __name__ == "__main__":
    caching_example()
