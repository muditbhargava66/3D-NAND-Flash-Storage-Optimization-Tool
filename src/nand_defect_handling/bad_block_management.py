# src/nand_defect_handling/bad_block_management.py

import numpy as np

from src.utils.config import Config


class BadBlockManager:
    def __init__(self, config: Config):
        # self.bbm_config = config.bbm_config
        self.bbm_config = config.get("bbm_config", {})  # Use get() method to provide a default value
        # If 'num_blocks' is not provided, use the value from 'nand_config'
        self.num_blocks = self.bbm_config.get("num_blocks", config.get("nand_config", {}).get("num_blocks", 1024))
        self.bad_block_table = self._init_bad_block_table()

    def _init_bad_block_table(self):
        # Use self.num_blocks which now has a fallback value
        return np.zeros(self.num_blocks, dtype=bool)

    def mark_bad_block(self, block_address):
        if 0 <= block_address < self.num_blocks:
            self.bad_block_table[block_address] = True
        else:
            raise IndexError(f"Block address {block_address} is out of range")

    def is_bad_block(self, block_address):
        if 0 <= block_address < self.num_blocks:
            return self.bad_block_table[block_address]
        else:
            raise IndexError(f"Block address {block_address} is out of range")

    def get_next_good_block(self, block_address):
        """
        Find the next good block starting from the given block address.

        Args:
            block_address: Starting block address

        Returns:
            int: Next good block address

        Raises:
            IndexError: If block_address is out of range
            RuntimeError: If no good blocks are available
        """
        if block_address >= self.num_blocks:
            raise IndexError(f"Block address {block_address} is out of range")

        # Search for good blocks after the current block (including current if it's good)
        for i in range(block_address, self.num_blocks):
            if not self.is_bad_block(i):
                return i

        # If no good block is found after, search from the beginning up to current block
        for i in range(block_address):
            if not self.is_bad_block(i):
                return i

        # If no good block is found at all
        raise RuntimeError("No good blocks available")
