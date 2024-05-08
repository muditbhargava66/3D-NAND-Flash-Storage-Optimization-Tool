# src/firmware_integration/firmware_specs.py

import yaml

class FirmwareSpecGenerator:
    def __init__(self, template_file):
        with open(template_file, 'r') as file:
            self.template = yaml.safe_load(file)

    def generate_spec(self, config):
        spec = self.template.copy()
        spec['firmware_version'] = config['firmware_version']
        spec['nand_config'] = config['nand_config']
        spec['ecc_config'] = config['ecc_config']
        spec['bbm_config'] = config['bbm_config']
        spec['wl_config'] = config['wl_config']
        return yaml.dump(spec, default_flow_style=False)

    def save_spec(self, spec, output_file):
        with open(output_file, 'w') as file:
            file.write(spec)