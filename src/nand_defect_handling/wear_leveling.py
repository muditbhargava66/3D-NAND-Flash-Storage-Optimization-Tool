# src/nand_defect_handling/wear_leveling.py

import numpy as np
from utils.config import Config

class WearLevelingEngine:
    def __init__(self, config: Config):
        # self.wl_config = config.wl_config
        self.wl_config = config.get('wl_config', {})  # Use get() method to provide a default value
        self.wear_level_table = self._init_wear_level_table()

    def _init_wear_level_table(self):
        num_blocks = self.wl_config.get('num_blocks', 1024)
        return np.zeros(num_blocks, dtype=np.uint32)

    def update_wear_level(self, block_address):
        self.wear_level_table[block_address] += 1
        self._perform_wear_leveling()

    def _perform_wear_leveling(self):
        max_wear_level = self.wear_level_table.max()
        min_wear_level = self.wear_level_table.min()
        if max_wear_level - min_wear_level > self.wl_config.get('wear_level_threshold', 1000):
            # Perform wear leveling by swapping data between blocks
            min_wear_block = self.get_least_worn_block()
            max_wear_block = self.get_most_worn_block()
            # Swap data between min_wear_block and max_wear_block
            # Update the wear level table accordingly
            self.wear_level_table[min_wear_block] = max_wear_level
            self.wear_level_table[max_wear_block] = min_wear_level

    def get_least_worn_block(self):
        return np.argmin(self.wear_level_table)

    def get_most_worn_block(self):
        return np.argmax(self.wear_level_table)