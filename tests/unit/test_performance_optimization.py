# tests/unit/test_performance_optimization.py

import unittest
from unittest.mock import MagicMock, patch
from src.performance_optimization import DataCompressor, CachingSystem, ParallelAccessManager

class TestDataCompressor(unittest.TestCase):
    def setUp(self):
        self.data_compressor = DataCompressor()

    def test_compress_decompress(self):
        data = b'Hello, World!'
        compressed_data = self.data_compressor.compress(data)
        self.assertNotEqual(data, compressed_data)

        decompressed_data = self.data_compressor.decompress(compressed_data)
        self.assertEqual(data, decompressed_data)

class TestCachingSystem(unittest.TestCase):
    def setUp(self):
        self.caching_system = CachingSystem()

    def test_get_put(self):
        self.assertIsNone(self.caching_system.get('key1'))

        self.caching_system.put('key1', 'value1')
        self.assertEqual(self.caching_system.get('key1'), 'value1')

    def test_cache_eviction(self):
        self.caching_system.capacity = 2

        self.caching_system.put('key1', 'value1')
        self.caching_system.put('key2', 'value2')
        self.caching_system.put('key3', 'value3')

        self.assertIsNone(self.caching_system.get('key1'))
        self.assertEqual(self.caching_system.get('key2'), 'value2')
        self.assertEqual(self.caching_system.get('key3'), 'value3')

class TestParallelAccessManager(unittest.TestCase):
    def setUp(self):
        self.parallel_access_manager = ParallelAccessManager()

    def test_submit_task(self):
        task = MagicMock()
        future = self.parallel_access_manager.submit_task(task, 1, 2, a=3, b=4)
        self.parallel_access_manager.wait_for_tasks([future])

        task.assert_called_once_with(1, 2, a=3, b=4)

    def test_shutdown(self):
        self.parallel_access_manager.shutdown()
        self.assertTrue(self.parallel_access_manager.executor._shutdown)

if __name__ == '__main__':
    unittest.main()