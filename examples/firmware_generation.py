#!/usr/bin/env python3
# examples/firmware_generation.py

"""
Example demonstrating firmware specification generation and validation.

This example shows how to:
1. Configure firmware parameters
2. Generate firmware specifications from templates
3. Validate generated specifications
4. Customize firmware for different NAND configurations
"""

import os
import sys

# Add the project root directory to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

try:
    from src.firmware_integration.firmware_specs import FirmwareSpecGenerator, FirmwareSpecValidator
    from src.utils.config import Config
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Make sure you're running this example from the project root directory")
    sys.exit(1)


def print_yaml(yaml_str):
    """Print YAML string with formatting."""
    print("\n" + "-" * 40)
    print(yaml_str)
    print("-" * 40)


def create_basic_firmware_spec():
    """Create a basic firmware specification."""
    print("\nCreating basic firmware specification...")
    
    # Basic configuration
    config = {
        'firmware_version': '1.0.0',
        'nand_config': {
            'page_size': 4096,
            'block_size': 256,  # pages per block
            'num_blocks': 1024,
            'oob_size': 128
        },
        'ecc_config': {
            'algorithm': 'bch',
            'bch_params': {
                'm': 8,
                't': 4
            },
            'strength': 4  # Error correction strength
        },
        'bbm_config': {
            'max_bad_blocks': 100
        },
        'wl_config': {
            'wear_leveling_threshold': 1000
        }
    }
    
    # Create template path
    template_path = os.path.join('resources', 'config', 'template.yaml')
    if not os.path.exists(template_path):
        # If template doesn't exist, create a simplified one
        print(f"Template file not found: {template_path}")
        print("Creating a simplified template file...")
        
        template_content = """---
firmware_version: "{{ firmware_version }}"
nand_config:
  page_size: {{ nand_config.page_size }}
  block_size: {{ nand_config.block_size }}
  num_blocks: {{ nand_config.num_blocks }}
  oob_size: {{ nand_config.oob_size }}
ecc_config:
  algorithm: "{{ ecc_config.algorithm }}"
  strength: {{ ecc_config.strength }}
bbm_config:
  max_bad_blocks: {{ bbm_config.max_bad_blocks }}
wl_config:
  wear_leveling_threshold: {{ wl_config.wear_leveling_threshold }}
"""
        os.makedirs(os.path.dirname(template_path), exist_ok=True)
        with open(template_path, 'w') as file:
            file.write(template_content)
        print(f"Created template file: {template_path}")
    
    # Create generator with the template file
    generator = FirmwareSpecGenerator(template_path)
    
    # Generate the firmware specification
    spec = generator.generate_spec(config)
    
    print("Basic firmware specification generated:")
    print_yaml(spec)
    
    return spec


def validate_firmware_spec(spec):
    """Validate a firmware specification."""
    print("\nValidating firmware specification...")
    
    validator = FirmwareSpecValidator()
    is_valid = validator.validate(spec)
    
    if is_valid:
        print("✅ Firmware specification is valid!")
    else:
        print("❌ Firmware specification is invalid!")
        print("Validation errors:")
        for error in validator.get_errors():
            print(f"  - {error}")
    
    return is_valid


def customize_firmware_for_different_nand():
    """Create firmware specifications for different NAND configurations."""
    print("\nGenerating firmware specifications for different NAND configurations...")
    
    # Template file path
    template_path = os.path.join('resources', 'config', 'template.yaml')
    generator = FirmwareSpecGenerator(template_path)
    
    # Array of different NAND configurations
    nand_configs = [
        {
            'name': 'Small MLC NAND',
            'config': {
                'firmware_version': '1.0.0',
                'nand_config': {
                    'page_size': 2048,
                    'block_size': 64,
                    'num_blocks': 512,
                    'oob_size': 64
                },
                'ecc_config': {
                    'algorithm': 'bch',
                    'bch_params': {'m': 8, 't': 4},
                    'strength': 4
                },
                'bbm_config': {'max_bad_blocks': 50},
                'wl_config': {'wear_leveling_threshold': 500}
            }
        },
        {
            'name': 'Standard TLC NAND',
            'config': {
                'firmware_version': '1.0.0',
                'nand_config': {
                    'page_size': 4096,
                    'block_size': 256,
                    'num_blocks': 1024,
                    'oob_size': 128
                },
                'ecc_config': {
                    'algorithm': 'bch',
                    'bch_params': {'m': 10, 't': 8},
                    'strength': 8
                },
                'bbm_config': {'max_bad_blocks': 100},
                'wl_config': {'wear_leveling_threshold': 1000}
            }
        },
        {
            'name': 'High-Density QLC NAND',
            'config': {
                'firmware_version': '1.0.0',
                'nand_config': {
                    'page_size': 16384,
                    'block_size': 512,
                    'num_blocks': 2048,
                    'oob_size': 256
                },
                'ecc_config': {
                    'algorithm': 'ldpc',
                    'ldpc_params': {'n': 2048, 'd_v': 3, 'd_c': 6},
                    'strength': 12
                },
                'bbm_config': {'max_bad_blocks': 200},
                'wl_config': {'wear_leveling_threshold': 200}
            }
        }
    ]
    
    validator = FirmwareSpecValidator()
    
    # Generate and validate firmware for each configuration
    for nand in nand_configs:
        print(f"\nGenerating firmware for {nand['name']}...")
        spec = generator.generate_spec(nand['config'])
        
        print(f"Firmware specification for {nand['name']}:")
        print_yaml(spec)
        
        # Validate the specification
        is_valid = validator.validate(spec)
        if is_valid:
            print(f"✅ {nand['name']} firmware specification is valid!")
        else:
            print(f"❌ {nand['name']} firmware specification is invalid!")
            print("Validation errors:")
            for error in validator.get_errors():
                print(f"  - {error}")
        
        # Save the specification to a file
        output_file = f"firmware_spec_{nand['name'].lower().replace(' ', '_')}.yaml"
        generator.save_spec(spec, output_file)
        print(f"Saved specification to {output_file}")


def create_custom_template():
    """Create a custom firmware template with advanced options."""
    print("\nCreating custom firmware template with advanced options...")
    
    custom_template = """---
# Advanced Firmware Template
# Includes extended configurations

firmware_info:
  version: "{{ firmware_version }}"
  release_date: "{{ current_date }}"
  vendor: "3D NAND Optimization Tool"
  compatibility: "v1.x"

nand_physical_config:
  page_size_bytes: {{ nand_config.page_size }}
  pages_per_block: {{ nand_config.block_size }}
  total_blocks: {{ nand_config.num_blocks }}
  oob_size_bytes: {{ nand_config.oob_size }}
  planes_per_die: {{ nand_config.num_planes | default(1) }}
  
error_correction:
  primary_algorithm: "{{ ecc_config.algorithm }}"
  correction_strength: {{ ecc_config.strength }}
  {% if ecc_config.algorithm == 'bch' %}
  bch_configuration:
    m_value: {{ ecc_config.bch_params.m }}
    t_value: {{ ecc_config.bch_params.t }}
  {% elif ecc_config.algorithm == 'ldpc' %}
  ldpc_configuration:
    codeword_length: {{ ecc_config.ldpc_params.n }}
    variable_degree: {{ ecc_config.ldpc_params.d_v }}
    check_degree: {{ ecc_config.ldpc_params.d_c }}
  {% endif %}
  
defect_management:
  bad_block_handling:
    max_allowed_bad_blocks: {{ bbm_config.max_bad_blocks }}
    bad_block_table_location: [0, 1]  # Redundant blocks for BBT
  
  wear_leveling:
    algorithm: "dynamic"
    erase_difference_threshold: {{ wl_config.wear_leveling_threshold }}
    
performance_tuning:
  read_retry_levels: 3
  data_scrambling: enabled
  command_queue_depth: 8
  
advanced_features:
  background_operations:
    - name: "garbage_collection"
      trigger: "85% capacity usage"
    - name: "wear_leveling_scan"
      schedule: "every 24 hours"
  
  power_loss_protection: enabled
  thermal_management:
    critical_temperature: 85
    throttling_temperature: 75
"""
    
    # Save the custom template
    custom_template_path = "custom_firmware_template.yaml"
    with open(custom_template_path, 'w') as file:
        file.write(custom_template)
    
    print(f"Custom template saved to {custom_template_path}")
    
    # Create configuration with all required fields
    config = {
        'firmware_version': '2.0.0',
        'current_date': '2025-03-02',
        'nand_config': {
            'page_size': 8192,
            'block_size': 256,
            'num_blocks': 2048,
            'oob_size': 256,
            'num_planes': 2
        },
        'ecc_config': {
            'algorithm': 'ldpc',
            'ldpc_params': {
                'n': 2048,
                'd_v': 3,
                'd_c': 6
            },
            'strength': 12
        },
        'bbm_config': {
            'max_bad_blocks': 150
        },
        'wl_config': {
            'wear_leveling_threshold': 500
        }
    }
    
    # Generate firmware spec using custom template
    generator = FirmwareSpecGenerator(custom_template_path)
    spec = generator.generate_spec(config)
    
    print("\nAdvanced firmware specification generated:")
    print_yaml(spec)
    
    # Save the specification
    advanced_spec_path = "advanced_firmware_spec.yaml"
    generator.save_spec(spec, advanced_spec_path)
    print(f"Advanced specification saved to {advanced_spec_path}")
    
    return custom_template_path, advanced_spec_path


def demonstrate_firmware_generation():
    """Main function demonstrating firmware generation."""
    print("3D NAND Optimization Tool - Firmware Generation Example")
    print("====================================================")
    
    # 1. Create a basic firmware specification
    basic_spec = create_basic_firmware_spec()
    
    # 2. Validate the firmware specification
    is_valid = validate_firmware_spec(basic_spec)
    
    # 3. Create an invalid specification to demonstrate validation
    print("\nCreating an intentionally invalid specification...")
    invalid_config = {
        'firmware_version': 'not_semver',  # Invalid format
        'nand_config': {
            'page_size': 4096,
            'block_size': 255,  # Not a power of 2
            'num_blocks': 1024,
            'oob_size': 128
        },
        'ecc_config': {
            'algorithm': 'unknown',  # Unknown algorithm
            'strength': -1  # Negative strength
        },
        'bbm_config': {
            'max_bad_blocks': 100
        },
        'wl_config': {
            'wear_leveling_threshold': 1000
        }
    }
    
    generator = FirmwareSpecGenerator()
    invalid_spec = generator.generate_spec(invalid_config)
    
    print("Invalid firmware specification:")
    print_yaml(invalid_spec)
    
    # Validate the invalid specification
    is_invalid_valid = validate_firmware_spec(invalid_spec)
    
    # 4. Generate firmware for different NAND configurations
    customize_firmware_for_different_nand()
    
    # 5. Create a custom template with advanced options
    custom_template_path, advanced_spec_path = create_custom_template()
    
    print("\nFirmware generation example completed.")
    print("\nFiles created:")
    print(f"  - {custom_template_path}")
    print(f"  - {advanced_spec_path}")
    
    # List other generated files
    yaml_files = [f for f in os.listdir('.') if f.endswith('.yaml') and f.startswith('firmware_spec_')]
    for file in yaml_files:
        print(f"  - {file}")


if __name__ == "__main__":
    demonstrate_firmware_generation()
