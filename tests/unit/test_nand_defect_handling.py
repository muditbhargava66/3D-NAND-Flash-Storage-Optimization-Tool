# tests/unit/test_nand_defect_handling.py

import unittest
from unittest.mock import MagicMock, patch
from src.nand_defect_handling import ECCHandler, BadBlockManager, WearLevelingEngine

class TestECCHandler(unittest.TestCase):
    def setUp(self):
        self.ecc_handler = ECCHandler()

    def test_encode_decode(self):
        data = b'Hello, World!'
        encoded_data = self.ecc_handler.encode(data)
        self.assertNotEqual(data, encoded_data)

        decoded_data, num_errors = self.ecc_handler.decode(encoded_data)
        self.assertEqual(data, decoded_data)
        self.assertEqual(num_errors, 0)

    def test_is_correctable(self):
        data = b'Hello, World!'
        encoded_data = self.ecc_handler.encode(data)
        self.assertTrue(self.ecc_handler.is_correctable(encoded_data))

        # Simulate a bit flip error
        corrupted_data = bytearray(encoded_data)
        corrupted_data[0] ^= 1
        self.assertTrue(self.ecc_handler.is_correctable(corrupted_data))

class TestBadBlockManager(unittest.TestCase):
    def setUp(self):
        self.bad_block_manager = BadBlockManager()

    def test_mark_bad_block(self):
        block_address = 100
        self.assertFalse(self.bad_block_manager.is_bad_block(block_address))

        self.bad_block_manager.mark_bad_block(block_address)
        self.assertTrue(self.bad_block_manager.is_bad_block(block_address))

    def test_get_next_good_block(self):
        self.bad_block_manager.mark_bad_block(50)
        self.bad_block_manager.mark_bad_block(51)
        self.bad_block_manager.mark_bad_block(52)

        next_good_block = self.bad_block_manager.get_next_good_block(49)
        self.assertEqual(next_good_block, 53)

class TestWearLevelingEngine(unittest.TestCase):
    def setUp(self):
        self.wear_leveling_engine = WearLevelingEngine()

    def test_update_wear_level(self):
        block_address = 100
        initial_wear_level = self.wear_leveling_engine.wear_level_table[block_address]

        self.wear_leveling_engine.update_wear_level(block_address)
        updated_wear_level = self.wear_leveling_engine.wear_level_table[block_address]
        self.assertEqual(updated_wear_level, initial_wear_level + 1)

    def test_get_least_most_worn_blocks(self):
        self.wear_leveling_engine.wear_level_table[50] = 100
        self.wear_leveling_engine.wear_level_table[51] = 200
        self.wear_leveling_engine.wear_level_table[52] = 300

        least_worn_block = self.wear_leveling_engine.get_least_worn_block()
        self.assertEqual(least_worn_block, 50)

        most_worn_block = self.wear_leveling_engine.get_most_worn_block()
        self.assertEqual(most_worn_block, 52)

if __name__ == '__main__':
    unittest.main()