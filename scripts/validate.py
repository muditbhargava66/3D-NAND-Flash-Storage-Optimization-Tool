# scripts/validate.py

import argparse
import yaml
from src.firmware_integration import FirmwareSpecValidator
from src.nand_controller import NANDController

def validate_firmware(firmware_file):
    with open(firmware_file, 'r') as file:
        firmware_spec = yaml.safe_load(file)
    
    validator = FirmwareSpecValidator()
    is_valid = validator.validate(firmware_spec)
    
    if is_valid:
        return "Firmware validation passed"
    else:
        return "Firmware validation failed"

def validate_hardware():
    config = {
        'page_size': 4096,
        'block_size': 256,
        'num_blocks': 1024,
        'oob_size': 128
    }
    
    try:
        nand_controller = NANDController(config)
        nand_controller.initialize()
        nand_controller.shutdown()
        return "Hardware validation passed"
    except Exception as e:
        return f"Hardware validation failed: {str(e)}"

def main():
    parser = argparse.ArgumentParser(description='Validation script')
    parser.add_argument('firmware_file', help='Firmware file to validate')
    args = parser.parse_args()

    firmware_result = validate_firmware(args.firmware_file)
    hardware_result = validate_hardware()

    print(firmware_result)
    print(hardware_result)

if __name__ == '__main__':
    main()