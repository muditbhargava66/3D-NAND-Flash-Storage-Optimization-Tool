# src/utils/config.py

import yaml

class Config:
    def __init__(self, config):
        self.config = config

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value

    def save(self, config_file):
        with open(config_file, 'w') as file:
            yaml.safe_dump(self.config, file)

    @property
    def ecc_config(self):
        return self.get('optimization_config', {}).get('error_correction', {})

    @property
    def bbm_config(self):
        return self.get('nand_config', {})

    @property
    def wl_config(self):
        return self.get('optimization_config', {}).get('wear_leveling', {})

def load_config(config_file):
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
    return Config(config)

def save_config(config, config_file):
    with open(config_file, 'w') as file:
        yaml.safe_dump(config.config, file)