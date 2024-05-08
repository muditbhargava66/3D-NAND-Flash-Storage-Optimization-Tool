# src/nand_defect_handling/bad_block_management.py

import numpy as np
from utils.config import Config

class BadBlockManager:
    def __init__(self, config: Config):
        self.bbm_config = config.bbm_config
        self.bad_block_table = self._init_bad_block_table()

    def _init_bad_block_table(self):
        num_blocks = self.bbm_config.get('num_blocks', 0)
        return np.zeros(num_blocks, dtype=bool)

    def mark_bad_block(self, block_address):
        self.bad_block_table[block_address] = True

    def is_bad_block(self, block_address):
        return self.bad_block_table[block_address]

    def get_next_good_block(self, block_address):
        num_blocks = self.bbm_config.get('num_blocks', 0)
        for i in range(block_address + 1, num_blocks):
            if not self.is_bad_block(i):
                return i
        for i in range(block_address):
            if not self.is_bad_block(i):
                return i
        raise RuntimeError("No good blocks available")