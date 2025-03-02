# tests/unit/test_firmware_integration.py

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import unittest
from unittest.mock import MagicMock, patch

import yaml

from src.firmware_integration.firmware_specs import FirmwareSpecGenerator, FirmwareSpecValidator
from src.firmware_integration.test_benches import TestBenchRunner
from src.firmware_integration.validation_scripts import ValidationScriptExecutor


class TestFirmwareSpecGenerator(unittest.TestCase):
    def setUp(self):
        self.template_file = "template.yaml"
        self.firmware_spec_generator = FirmwareSpecGenerator(self.template_file)

    @patch("builtins.open")
    def test_generate_spec(self, mock_open):
        # Mock file content for template.yaml
        mock_file = MagicMock()
        mock_file.__enter__().read.return_value = """
firmware_version: {{ firmware_version }}
nand_config:
  page_size: {{ nand_config.page_size }}
  block_size: {{ nand_config.block_size }}
ecc_config:
  algorithm: {{ ecc_config.algorithm }}
  strength: {{ ecc_config.strength }}
bbm_config:
  bad_block_ratio: {{ bbm_config.bad_block_ratio }}
wl_config:
  wear_leveling_threshold: {{ wl_config.wear_leveling_threshold }}
"""
        # Make the mock file content load as YAML
        mock_yaml_content = {
            "firmware_version": "{{ firmware_version }}",
            "nand_config": {"page_size": "{{ nand_config.page_size }}", "block_size": "{{ nand_config.block_size }}"},
            "ecc_config": {"algorithm": "{{ ecc_config.algorithm }}", "strength": "{{ ecc_config.strength }}"},
            "bbm_config": {"bad_block_ratio": "{{ bbm_config.bad_block_ratio }}"},
            "wl_config": {"wear_leveling_threshold": "{{ wl_config.wear_leveling_threshold }}"},
        }

        # Configure the mock open to return mock_file for template.yaml
        mock_open.return_value.__enter__.return_value = mock_file

        # Set up mock for yaml.safe_load to return our mock YAML content
        with patch("yaml.safe_load", return_value=mock_yaml_content):
            config = {
                "firmware_version": "1.0.0",
                "nand_config": {"page_size": 4096, "block_size": 256},
                "ecc_config": {"algorithm": "BCH", "strength": 8},
                "bbm_config": {"bad_block_ratio": 0.05},
                "wl_config": {"wear_leveling_threshold": 1000},
            }

            spec = self.firmware_spec_generator.generate_spec(config)

            # Check that key values are in the YAML string
            # Note: The actual format might vary depending on how yaml.dump formats it
            self.assertIsInstance(spec, str)

            # These might be nested differently in the actual output
            # so we'll check for the values in a more flexible way
            self.assertIn("1.0.0", spec)  # firmware_version
            self.assertIn("4096", spec)  # page_size
            self.assertIn("256", spec)  # block_size
            self.assertIn("BCH", spec)  # algorithm
            self.assertIn("0.05", spec)  # bad_block_ratio
            self.assertIn("1000", spec)  # wear_leveling_threshold

    @patch("builtins.open", new_callable=MagicMock)
    def test_save_spec(self, mock_open):
        spec = "firmware_version: 1.0.0"
        output_file = "output.yaml"

        self.firmware_spec_generator.save_spec(spec, output_file)

        mock_open.assert_called_once_with(output_file, "w")
        mock_open.return_value.__enter__.return_value.write.assert_called_once_with(spec)


class TestFirmwareSpecValidator(unittest.TestCase):
    def setUp(self):
        self.validator = FirmwareSpecValidator()

        # Create a valid firmware spec for testing
        self.valid_spec = {
            "firmware_version": "1.0.0",
            "nand_config": {
                "page_size": 4096,
                "block_size": 4096 * 64,  # Multiple of page_size
                "num_blocks": 1024,
                "num_planes": 2,
                "oob_size": 64,
            },
            "ecc_config": {"algorithm": "bch", "bch_params": {"m": 8, "t": 4}},
            "bbm_config": {"max_bad_blocks": 100, "bad_block_ratio": 0.05},
            "wl_config": {"wear_level_threshold": 1000, "wear_leveling_method": "dynamic"},
        }

    def test_valid_firmware_spec(self):
        """Test validation of a valid firmware spec"""
        result = self.validator.validate(self.valid_spec)
        self.assertTrue(result)
        self.assertEqual(len(self.validator.get_errors()), 0)

    def test_invalid_firmware_version(self):
        """Test validation with invalid firmware version format"""
        invalid_spec = dict(self.valid_spec)
        invalid_spec["firmware_version"] = "invalid_version"

        result = self.validator.validate(invalid_spec)
        self.assertFalse(result)
        self.assertGreater(len(self.validator.get_errors()), 0)

        # Check if error message mentions version format
        error_found = any("firmware_version" in error for error in self.validator.get_errors())
        self.assertTrue(error_found)

    def test_missing_required_fields(self):
        """Test validation with missing required fields"""
        invalid_spec = dict(self.valid_spec)
        del invalid_spec["nand_config"]["page_size"]

        result = self.validator.validate(invalid_spec)
        self.assertFalse(result)
        self.assertGreater(len(self.validator.get_errors()), 0)

    def test_block_size_alignment(self):
        """Test validation of block size alignment with page size"""
        invalid_spec = dict(self.valid_spec)
        invalid_spec["nand_config"]["block_size"] = 100000  # Not a multiple of page_size

        result = self.validator.validate(invalid_spec)
        self.assertFalse(result)
        self.assertGreater(len(self.validator.get_errors()), 0)

        # Check if error message mentions block size alignment
        error_found = any("multiple of page size" in error for error in self.validator.get_errors())
        self.assertTrue(error_found)

    def test_ecc_configuration(self):
        """Test validation of ECC configuration"""
        invalid_spec = dict(self.valid_spec)
        # Set an invalid BCH parameter combination
        invalid_spec["ecc_config"]["bch_params"]["m"] = 5
        invalid_spec["ecc_config"]["bch_params"]["t"] = 20  # t too large for m=5

        result = self.validator.validate(invalid_spec)
        self.assertFalse(result)
        self.assertGreater(len(self.validator.get_errors()), 0)

        # Check if error message mentions BCH parameters
        error_found = any("BCH parameter" in error for error in self.validator.get_errors())
        self.assertTrue(error_found)

    def test_ldpc_configuration(self):
        """Test validation of LDPC configuration"""
        invalid_spec = dict(self.valid_spec)
        # Change to LDPC with invalid parameters
        invalid_spec["ecc_config"]["algorithm"] = "ldpc"
        invalid_spec["ecc_config"]["ldpc_params"] = {"n": 100, "d_v": 3, "d_c": 7}  # This makes n*d_v not divisible by d_c

        result = self.validator.validate(invalid_spec)
        self.assertFalse(result)
        self.assertGreater(len(self.validator.get_errors()), 0)

        # Check if error message mentions LDPC parameters
        error_found = any("LDPC parameters" in error for error in self.validator.get_errors())
        self.assertTrue(error_found)

    def test_wear_leveling_config(self):
        """Test validation of wear leveling configuration"""
        invalid_spec = dict(self.valid_spec)
        # Set an extremely high threshold compared to number of blocks
        invalid_spec["wl_config"]["wear_level_threshold"] = 1000000  # Much higher than num_blocks

        result = self.validator.validate(invalid_spec)
        self.assertFalse(result)
        self.assertGreater(len(self.validator.get_errors()), 0)

        # Check if error message mentions wear level threshold
        error_found = any("Wear level threshold" in error for error in self.validator.get_errors())
        self.assertTrue(error_found)

    def test_yaml_string_validation(self):
        """Test validation with YAML string input"""
        # Convert valid spec to YAML string
        valid_yaml = yaml.dump(self.valid_spec)

        result = self.validator.validate(valid_yaml)
        self.assertTrue(result)
        self.assertEqual(len(self.validator.get_errors()), 0)

        # Test with invalid YAML string
        invalid_yaml = "firmware_version: 1.0.0\ninvalid yaml:"

        result = self.validator.validate(invalid_yaml)
        self.assertFalse(result)
        self.assertGreater(len(self.validator.get_errors()), 0)


class TestBenchRunnerTest(unittest.TestCase):
    def test_initialization(self):
        """Test that the TestBenchRunner class can be instantiated"""
        runner = TestBenchRunner("test_cases.yaml")
        self.assertEqual(runner.test_cases_file, "test_cases.yaml")

    def test_run_tests_with_empty_cases(self):
        """Test run_tests method with empty test cases"""
        # Create the runner with a non-existent file path
        # The implementation should handle this gracefully
        runner = TestBenchRunner("non_existent_file.yaml")

        # Since we don't have the actual file, let's set test_cases manually
        runner.test_cases = []

        # This test just verifies no exceptions are raised
        # We won't actually run any tests
        with patch("unittest.TestSuite"):
            with patch("unittest.TextTestRunner"):
                runner.run_tests()


class TestValidationScriptExecutor(unittest.TestCase):
    def setUp(self):
        self.script_dir = "scripts"
        self.validation_script_executor = ValidationScriptExecutor(self.script_dir)

    @patch("subprocess.check_output")
    def test_execute_script(self, mock_check_output):
        script_name = "validate.py"
        args = ["arg1", "arg2"]
        expected_output = "Validation passed"

        mock_check_output.return_value = expected_output

        output = self.validation_script_executor.execute_script(script_name, args)
        self.assertEqual(output, expected_output)

        expected_command = ["scripts/validate.py", "arg1", "arg2"]
        mock_check_output.assert_called_once_with(expected_command, stderr=-2, universal_newlines=True)


if __name__ == "__main__":
    unittest.main()
