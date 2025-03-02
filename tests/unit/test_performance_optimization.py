# tests/unit/test_performance_optimization.py

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import time
import unittest
from concurrent.futures import Future

from src.performance_optimization.caching import CachingSystem, EvictionPolicy
from src.performance_optimization.data_compression import DataCompressor
from src.performance_optimization.parallel_access import ParallelAccessManager


class TestDataCompressor(unittest.TestCase):
    def setUp(self):
        self.data_compressor = DataCompressor()

    def test_compress_decompress(self):
        data = b"Hello, World!" * 100  # Make the data longer to ensure compression
        compressed_data = self.data_compressor.compress(data)
        self.assertNotEqual(data, compressed_data)
        self.assertLess(len(compressed_data), len(data))

        decompressed_data = self.data_compressor.decompress(compressed_data)
        self.assertEqual(data, decompressed_data)

    def test_compress_empty_data(self):
        data = b""
        compressed_data = self.data_compressor.compress(data)
        self.assertEqual(data, compressed_data)

    def test_decompress_invalid_data(self):
        invalid_data = b"This is not compressed data"
        with self.assertRaises(ValueError):
            self.data_compressor.decompress(invalid_data)


class TestCachingSystem(unittest.TestCase):
    def setUp(self):
        # Create a cache with a specific capacity
        self.caching_system = CachingSystem(100)

    def test_get_put(self):
        self.assertIsNone(self.caching_system.get("key1"))

        self.caching_system.put("key1", "value1")
        self.assertEqual(self.caching_system.get("key1"), "value1")

    def test_cache_eviction(self):
        # Fill the cache beyond capacity
        for i in range(101):
            self.caching_system.put(f"key{i}", f"value{i}")

        # The oldest item (key0) should be evicted
        self.assertIsNone(self.caching_system.get("key0"))
        self.assertEqual(self.caching_system.get("key100"), "value100")

    def test_update_existing_key(self):
        self.caching_system.put("key1", "value1")
        self.caching_system.put("key1", "new_value1")
        self.assertEqual(self.caching_system.get("key1"), "new_value1")

    def test_hit_ratio(self):
        # Put some items in the cache
        self.caching_system.put("key1", "value1")
        self.caching_system.put("key2", "value2")

        # Miss (key3 doesn't exist)
        self.assertIsNone(self.caching_system.get("key3"))

        # Hit (key1 exists)
        self.assertEqual(self.caching_system.get("key1"), "value1")

        # Hit (key2 exists)
        self.assertEqual(self.caching_system.get("key2"), "value2")

        # Expected hit ratio: 2 hits / 3 total = 0.667
        self.assertAlmostEqual(self.caching_system.get_hit_ratio(), 2 / 3, places=2)

    def test_clear(self):
        # Add some items
        self.caching_system.put("key1", "value1")
        self.caching_system.put("key2", "value2")

        # Verify items are in cache
        self.assertEqual(self.caching_system.get("key1"), "value1")

        # Clear the cache
        self.caching_system.clear()

        # Verify cache is empty
        self.assertIsNone(self.caching_system.get("key1"))
        self.assertIsNone(self.caching_system.get("key2"))

    def test_ttl_expiration(self):
        # Create a cache with TTL support
        ttl_cache = CachingSystem(100, ttl=0.1)  # 100ms TTL

        # Add an item
        ttl_cache.put("key1", "value1")

        # Item should be available immediately
        self.assertEqual(ttl_cache.get("key1"), "value1")

        # Wait for TTL to expire
        time.sleep(0.2)

        # Item should be expired
        self.assertIsNone(ttl_cache.get("key1"))

    def test_different_eviction_policies(self):
        # Test LRU (default)
        lru_cache = CachingSystem(2, policy=EvictionPolicy.LRU)
        lru_cache.put("key1", "value1")
        lru_cache.put("key2", "value2")

        # Access key1 to make key2 the least recently used
        lru_cache.get("key1")

        # Adding key3 should evict key2
        lru_cache.put("key3", "value3")
        self.assertIsNone(lru_cache.get("key2"))
        self.assertEqual(lru_cache.get("key1"), "value1")
        self.assertEqual(lru_cache.get("key3"), "value3")

        # Test LFU
        lfu_cache = CachingSystem(2, policy=EvictionPolicy.LFU)
        lfu_cache.put("key1", "value1")
        lfu_cache.put("key2", "value2")

        # Access key1 twice to make it more frequently used
        lfu_cache.get("key1")
        lfu_cache.get("key1")

        # Access key2 once
        lfu_cache.get("key2")

        # Adding key3 should evict key2 (least frequently used)
        lfu_cache.put("key3", "value3")
        self.assertIsNone(lfu_cache.get("key2"))
        self.assertEqual(lfu_cache.get("key1"), "value1")
        self.assertEqual(lfu_cache.get("key3"), "value3")

        # Test FIFO
        fifo_cache = CachingSystem(2, policy=EvictionPolicy.FIFO)
        fifo_cache.put("key1", "value1")
        fifo_cache.put("key2", "value2")

        # Access key1 to make sure it doesn't affect FIFO order
        fifo_cache.get("key1")

        # Adding key3 should evict key1 (first in)
        fifo_cache.put("key3", "value3")
        self.assertIsNone(fifo_cache.get("key1"))
        self.assertEqual(fifo_cache.get("key2"), "value2")
        self.assertEqual(fifo_cache.get("key3"), "value3")

    def test_size_based_eviction(self):
        # Create a cache with max size in bytes
        size_cache = CachingSystem(100, max_size_bytes=50)

        # Add items with different sizes
        size_cache.put("key1", "x" * 20)  # 20 bytes
        size_cache.put("key2", "x" * 20)  # 20 bytes

        # Both items should fit
        self.assertEqual(size_cache.get("key1"), "x" * 20)
        self.assertEqual(size_cache.get("key2"), "x" * 20)

        # Add another item that pushes us over the limit
        size_cache.put("key3", "x" * 30)  # 30 bytes

        # First item should be evicted
        self.assertIsNone(size_cache.get("key1"))
        self.assertEqual(size_cache.get("key2"), "x" * 20)
        self.assertEqual(size_cache.get("key3"), "x" * 30)

    def test_callback(self):
        # Track evicted keys
        evicted_keys = []

        def on_evict_callback(key):
            evicted_keys.append(key)

        # Create cache with callback
        callback_cache = CachingSystem(2, on_evict=on_evict_callback)

        # Fill the cache
        callback_cache.put("key1", "value1")
        callback_cache.put("key2", "value2")

        # This should trigger eviction of key1
        callback_cache.put("key3", "value3")

        # Check if callback was called with correct key
        self.assertEqual(evicted_keys, ["key1"])

        # Manually invalidate should also trigger callback
        callback_cache.invalidate("key2")
        self.assertEqual(evicted_keys, ["key1", "key2"])


class TestParallelAccessManager(unittest.TestCase):
    def setUp(self):
        self.parallel_access_manager = ParallelAccessManager()

    def test_submit_task(self):
        def task(x):
            return x * 2

        future = self.parallel_access_manager.submit_task(task, 5)
        self.assertIsInstance(future, Future)
        self.assertEqual(future.result(), 10)

    def test_wait_for_tasks(self):
        def slow_task(duration):
            time.sleep(duration)
            return duration

        futures = [
            self.parallel_access_manager.submit_task(slow_task, 0.1),
            self.parallel_access_manager.submit_task(slow_task, 0.2),
            self.parallel_access_manager.submit_task(slow_task, 0.3),
        ]

        start_time = time.time()
        self.parallel_access_manager.wait_for_tasks(futures)
        end_time = time.time()

        # Check if all tasks completed
        self.assertTrue(all(future.done() for future in futures))

        # Check if the total time is less than the sum of individual task durations
        self.assertLess(end_time - start_time, 0.6)

    def test_shutdown(self):
        self.parallel_access_manager.shutdown()

        # Attempting to submit a task after shutdown should raise an exception
        with self.assertRaises(RuntimeError):
            self.parallel_access_manager.submit_task(lambda: None)


if __name__ == "__main__":
    unittest.main()
