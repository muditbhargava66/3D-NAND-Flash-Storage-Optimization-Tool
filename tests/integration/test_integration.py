# tests/integration/test_integration.py

import unittest
import tempfile
import os
from nand_controller import NANDController
from nand_defect_handling import ECCHandler, BadBlockManager, WearLevelingEngine
from performance_optimization import DataCompressor, CachingSystem, ParallelAccessManager
from firmware_integration import FirmwareSpecGenerator, TestBenchRunner, ValidationScriptExecutor
from nand_characterization import DataCollector, DataAnalyzer, DataVisualizer

class TestIntegration(unittest.TestCase):
    def setUp(self):
        self.config = {
            'page_size': 4096,
            'block_size': 256,
            'num_blocks': 1024,
            'oob_size': 128,
            'ecc_strength': 8,
            'max_bad_blocks': 50,
            'wear_leveling_threshold': 1000,
            'ecc_config': {},  # Add this key
            'bbm_config': {},  # Add this key
            'wl_config': {}  # Add this key
        }
        self.nand_controller = NANDController(self.config)
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        self.nand_controller.shutdown()
        os.rmdir(self.temp_dir)

    def test_integration(self):
        # NAND Defect Handling
        # ecc_handler = ECCHandler()
        ecc_handler = ECCHandler(self.config)
        bad_block_manager = BadBlockManager(self.config)
        wear_leveling_engine = WearLevelingEngine(self.config)

        # Write and read data with ECC
        data = b'Hello, World!'
        encoded_data = ecc_handler.encode(data)
        self.nand_controller.write_page(0, 0, encoded_data)
        read_data = self.nand_controller.read_page(0, 0)
        decoded_data, _ = ecc_handler.decode(read_data)
        self.assertEqual(data, decoded_data)

        # Mark a block as bad and get the next good block
        self.nand_controller.mark_block_bad(10)
        self.assertTrue(bad_block_manager.is_bad_block(10))
        next_good_block = bad_block_manager.get_next_good_block(10)
        self.assertNotEqual(next_good_block, 10)

        # Update wear level and get the least worn block
        wear_leveling_engine.update_wear_level(20)
        least_worn_block = wear_leveling_engine.get_least_worn_block()
        self.assertNotEqual(least_worn_block, 20)

        # Performance Optimization
        data_compressor = DataCompressor()
        caching_system = CachingSystem()
        parallel_access_manager = ParallelAccessManager()

        # Compress and decompress data
        compressed_data = data_compressor.compress(data)
        decompressed_data = data_compressor.decompress(compressed_data)
        self.assertEqual(data, decompressed_data)

        # Cache data and verify cache hit
        caching_system.put('key', data)
        cached_data = caching_system.get('key')
        self.assertEqual(data, cached_data)

        # Submit parallel tasks and wait for completion
        def task1():
            return 1

        def task2():
            return 2

        future1 = parallel_access_manager.submit_task(task1)
        future2 = parallel_access_manager.submit_task(task2)
        parallel_access_manager.wait_for_tasks([future1, future2])
        self.assertEqual(future1.result(), 1)
        self.assertEqual(future2.result(), 2)

        # Firmware Integration
        firmware_spec_generator = FirmwareSpecGenerator('template.yaml')
        test_bench_runner = TestBenchRunner('test_cases.yaml')
        validation_script_executor = ValidationScriptExecutor('scripts')

        # Generate firmware specification
        firmware_config = {
            'firmware_version': '1.0.0',
            'nand_config': self.config,
            'ecc_config': {'algorithm': 'BCH', 'strength': 8},
            'bbm_config': {'max_bad_blocks': 50},
            'wl_config': {'wear_leveling_threshold': 1000}
        }
        firmware_spec = firmware_spec_generator.generate_spec(firmware_config)
        self.assertIsInstance(firmware_spec, str)
        self.assertIn('firmware_version: 1.0.0', firmware_spec)

        # Run test benches
        test_bench_runner.run_tests()

        # Execute validation script
        validation_output = validation_script_executor.execute_script('validate.py', ['arg1', 'arg2'])
        self.assertIsInstance(validation_output, str)

        # NAND Characterization
        data_collector = DataCollector(self.nand_controller)
        data_analyzer = DataAnalyzer('data.csv')
        data_visualizer = DataVisualizer('data.csv')

        # Collect and save characterization data
        num_samples = 100
        data_file = os.path.join(self.temp_dir, 'data.csv')
        data_collector.collect_data(num_samples, data_file)
        self.assertTrue(os.path.exists(data_file))

        # Analyze characterization data
        erase_count_dist = data_analyzer.analyze_erase_count_distribution()
        bad_block_trend = data_analyzer.analyze_bad_block_trend()
        self.assertIsInstance(erase_count_dist, dict)
        self.assertIsInstance(bad_block_trend, dict)

        # Visualize characterization data
        erase_count_dist_plot = os.path.join(self.temp_dir, 'erase_count_dist.png')
        bad_block_trend_plot = os.path.join(self.temp_dir, 'bad_block_trend.png')
        data_visualizer.plot_erase_count_distribution(erase_count_dist_plot)
        data_visualizer.plot_bad_block_trend(bad_block_trend_plot)
        self.assertTrue(os.path.exists(erase_count_dist_plot))
        self.assertTrue(os.path.exists(bad_block_trend_plot))

if __name__ == '__main__':
    unittest.main()