#!/usr/bin/env python3
# scripts/validate.py

import argparse
import os
import sys

import yaml

# Add the project root directory to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

try:
    from src.firmware_integration import FirmwareSpecValidator
    from src.nand_controller import NANDController
    from src.utils.config import Config, load_config
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Make sure you're running this script from the project root directory")
    sys.exit(1)


def validate_firmware(firmware_file):
    """
    Validate a firmware specification file

    Args:
        firmware_file (str): Path to the firmware specification file

    Returns:
        str: Validation result message
    """
    try:
        with open(firmware_file, "r") as file:
            firmware_spec = yaml.safe_load(file)

        validator = FirmwareSpecValidator()
        is_valid = validator.validate(firmware_spec)

        if is_valid:
            return "Firmware validation passed"
        else:
            errors = validator.get_errors()
            error_msg = "Firmware validation failed:\n"
            for i, error in enumerate(errors, 1):
                error_msg += f"  {i}. {error}\n"
            return error_msg
    except Exception as e:
        return f"Error validating firmware: {str(e)}"


def validate_hardware(config_file=None):
    """
    Validate hardware configuration by initializing the NAND controller

    Args:
        config_file (str, optional): Path to the configuration file

    Returns:
        str: Validation result message
    """
    try:
        # Load configuration
        if config_file and os.path.exists(config_file):
            config = load_config(config_file)
        else:
            # Look for default config locations
            default_paths = [
                os.path.join("resources", "config", "config.yaml"),
                os.path.join(project_root, "resources", "config", "config.yaml"),
                "config.yaml",
            ]

            config = None
            for path in default_paths:
                if os.path.exists(path):
                    config = load_config(path)
                    break

            if not config:
                return "Hardware validation failed: Configuration file not found"

        # Create NAND controller with simulation enabled for safety
        config_dict = config.config if hasattr(config, "config") else config
        config_dict["simulation"] = {"enabled": True}
        nand_controller = NANDController(Config(config_dict))

        # Initialize controller
        nand_controller.initialize()

        # Get device info for validation
        device_info = nand_controller.get_device_info()
        if not device_info:
            return "Hardware validation failed: Could not get device information"

        # Check for required configuration values
        required_keys = ["page_size", "block_size", "num_blocks"]
        if "config" in device_info:
            config = device_info["config"]
            missing_keys = [key for key in required_keys if key not in config]
            if missing_keys:
                return f"Hardware validation failed: Missing required configuration {', '.join(missing_keys)}"
        else:
            return "Hardware validation failed: Missing configuration information"

        # Shutdown controller
        nand_controller.shutdown()

        return "Hardware validation passed"
    except Exception as e:
        return f"Hardware validation failed: {str(e)}"


def main():
    parser = argparse.ArgumentParser(description="NAND Flash validation script")
    parser.add_argument("--firmware", help="Firmware file to validate")
    parser.add_argument("--config", help="Configuration file for hardware validation")
    parser.add_argument("--hardware", action="store_true", help="Validate hardware configuration")
    args = parser.parse_args()

    if args.firmware:
        result = validate_firmware(args.firmware)
        print(result)

    if args.hardware:
        result = validate_hardware(args.config)
        print(result)

    if not args.firmware and not args.hardware:
        print("No validation specified. Use --firmware or --hardware.")
        parser.print_help()


if __name__ == "__main__":
    main()
