# src/utils/config.py

import yaml

class Config:
    def __init__(self, config_file):
        self.config_file = config_file
        self.config = self.load_config()

    def load_config(self):
        with open(self.config_file, 'r') as file:
            config = yaml.safe_load(file)
        return config

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value

    def save(self):
        with open(self.config_file, 'w') as file:
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
    return Config(config_file)

def save_config(config_file, config):
    with open(config_file, 'w') as file:
        yaml.safe_dump(config, file)