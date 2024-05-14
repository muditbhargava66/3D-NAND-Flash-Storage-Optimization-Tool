# tests/unit/test_firmware_integration.py

import unittest
from unittest.mock import MagicMock, patch
from firmware_integration import FirmwareSpecGenerator, TestBenchRunner, ValidationScriptExecutor

class TestFirmwareSpecGenerator(unittest.TestCase):
    def setUp(self):
        self.template_file = 'template.yaml'
        self.firmware_spec_generator = FirmwareSpecGenerator(self.template_file)

    def test_generate_spec(self):
        config = {
            'firmware_version': '1.0.0',
            'nand_config': {'page_size': 4096, 'block_size': 256},
            'ecc_config': {'algorithm': 'BCH', 'strength': 8},
            'bbm_config': {'bad_block_ratio': 0.05},
            'wl_config': {'wear_leveling_threshold': 1000}
        }

        spec = self.firmware_spec_generator.generate_spec(config)
        self.assertIsInstance(spec, str)
        self.assertIn('firmware_version: 1.0.0', spec)
        self.assertIn('page_size: 4096', spec)
        self.assertIn('algorithm: BCH', spec)
        self.assertIn('bad_block_ratio: 0.05', spec)
        self.assertIn('wear_leveling_threshold: 1000', spec)

    @patch('builtins.open', new_callable=MagicMock)
    def test_save_spec(self, mock_open):
        spec = 'firmware_version: 1.0.0'
        output_file = 'output.yaml'

        self.firmware_spec_generator.save_spec(spec, output_file)

        mock_open.assert_called_once_with(output_file, 'w')
        mock_open.return_value.__enter__.return_value.write.assert_called_once_with(spec)

class TestTestBenchRunner(unittest.TestCase):
    def setUp(self):
        self.test_cases_file = 'test_cases.yaml'
        self.test_bench_runner = TestBenchRunner(self.test_cases_file)

    @patch('src.firmware_integration.NANDSimulator')
    def test_run_tests(self, mock_nand_simulator):
        self.test_bench_runner.test_cases = [
            {
                'name': 'TestCase1',
                'nand_config': {'page_size': 4096, 'block_size': 256},
                'test_methods': [
                    {
                        'name': 'test_method1',
                        'sequence': ['write', 'read', 'erase'],
                        'expected_output': [0, 1, 2]
                    }
                ]
            }
        ]

        mock_nand_simulator.return_value.execute_sequence.return_value = None
        mock_nand_simulator.return_value.get_output.return_value = [0, 1, 2]

        with patch('unittest.TextTestRunner.run'):
            self.test_bench_runner.run_tests()

        mock_nand_simulator.assert_called_once_with({'page_size': 4096, 'block_size': 256})
        mock_nand_simulator.return_value.execute_sequence.assert_called_once_with(['write', 'read', 'erase'])
        mock_nand_simulator.return_value.get_output.assert_called_once()

class TestValidationScriptExecutor(unittest.TestCase):
    def setUp(self):
        self.script_dir = 'scripts'
        self.validation_script_executor = ValidationScriptExecutor(self.script_dir)

    @patch('subprocess.check_output')
    def test_execute_script(self, mock_check_output):
        script_name = 'validate.py'
        args = ['arg1', 'arg2']
        expected_output = 'Validation passed'

        mock_check_output.return_value = expected_output

        output = self.validation_script_executor.execute_script(script_name, args)
        self.assertEqual(output, expected_output)

        expected_command = ['scripts/validate.py', 'arg1', 'arg2']
        mock_check_output.assert_called_once_with(expected_command, stderr=-2, universal_newlines=True)

if __name__ == '__main__':
    unittest.main()