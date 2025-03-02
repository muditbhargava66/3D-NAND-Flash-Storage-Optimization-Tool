# src/nand_characterization/data_collection.py

import pandas as pd

from src.utils.nand_interface import NANDInterface


class DataCollector:
    def __init__(self, nand_interface: NANDInterface):
        self.nand_interface = nand_interface

    def collect_data(self, num_samples: int, output_file: str):
        data = []
        for _ in range(num_samples):
            block_data = self.nand_interface.read_block()
            erase_count = self.nand_interface.get_erase_count()
            bad_block_count = self.nand_interface.get_bad_block_count()
            data.append({"block_data": block_data, "erase_count": erase_count, "bad_block_count": bad_block_count})

        df = pd.DataFrame(data)
        df.to_csv(output_file, index=False)
