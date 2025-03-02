# src/nand_defect_handling/wear_leveling.py

import numpy as np

from src.utils.config import Config


class WearLevelingEngine:
    def __init__(self, config: Config):
        # self.wl_config = config.wl_config
        self.wl_config = config.get("wl_config", {})  # Use get() method to provide a default value
        # If num_blocks is not provided in wl_config, get it from nand_config
        self.num_blocks = self.wl_config.get("num_blocks", config.get("nand_config", {}).get("num_blocks", 1024))
        self.wear_threshold = self.wl_config.get("wear_level_threshold", 1000)
        self.wear_level_table = self._init_wear_level_table()

    def _init_wear_level_table(self):
        return np.zeros(self.num_blocks, dtype=np.uint32)

    def update_wear_level(self, block_address):
        if 0 <= block_address < self.num_blocks:
            self.wear_level_table[block_address] += 1
            self._perform_wear_leveling()
        else:
            raise IndexError(f"Block address {block_address} is out of range")

    def _perform_wear_leveling(self):
        max_wear_level = self.wear_level_table.max()
        min_wear_level = self.wear_level_table.min()
        if max_wear_level - min_wear_level > self.wear_threshold:
            # Perform wear leveling by swapping data between blocks
            min_wear_block = self.get_least_worn_block()
            max_wear_block = self.get_most_worn_block()
            # Swap data between min_wear_block and max_wear_block
            # Update the wear level table accordingly
            temp = self.wear_level_table[min_wear_block]
            self.wear_level_table[min_wear_block] = self.wear_level_table[max_wear_block]
            self.wear_level_table[max_wear_block] = temp

    def should_perform_wear_leveling(self):
        """Check if wear leveling should be performed."""
        max_wear_level = self.wear_level_table.max()
        min_wear_level = self.wear_level_table.min()
        return max_wear_level - min_wear_level > self.wear_threshold

    def get_least_worn_block(self):
        return np.argmin(self.wear_level_table)

    def get_most_worn_block(self):
        return np.argmax(self.wear_level_table)
