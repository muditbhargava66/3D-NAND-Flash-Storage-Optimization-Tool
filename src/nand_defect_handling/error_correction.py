# src/nand_defect_handling/error_correction.py

import numpy as np
from utils.config import Config

class ECCHandler:
    def __init__(self, config: Config):
        self.ecc_config = config.ecc_config
        self.ecc_engine = self._init_ecc_engine()

    def _init_ecc_engine(self):
        ecc_type = self.ecc_config.get('algorithm', 'bch')
        if ecc_type == 'bch':
            from bchlib import BCH
            return BCH(self.ecc_config.get('bch_params', {}).get('m', 255),
                       self.ecc_config.get('bch_params', {}).get('t', 15))
        elif ecc_type == 'ldpc':
            from pyldpc import make_ldpc, encode, decode
            n = self.ecc_config.get('ldpc_params', {}).get('n', 1024)
            d_v = self.ecc_config.get('ldpc_params', {}).get('d_v', 3)
            d_c = self.ecc_config.get('ldpc_params', {}).get('d_c', 4)
            h, g = make_ldpc(n, d_v, d_c, systematic=True, sparse=True)
            return h, g
        else:
            raise ValueError(f"Unsupported ECC type: {ecc_type}")

    def encode(self, data):
        ecc_type = self.ecc_config['type']
        if ecc_type == 'BCH':
            ecc_data = self.ecc_engine.encode(data)
            return np.concatenate((data, ecc_data))
        elif ecc_type == 'LDPC':
            h, g = self.ecc_engine
            return encode(g, data)
        else:
            raise ValueError(f"Unsupported ECC type: {ecc_type}")

    def decode(self, data):
        ecc_type = self.ecc_config['type']
        if ecc_type == 'BCH':
            decoded_data, num_errors = self.ecc_engine.decode(data)
            return decoded_data, num_errors
        elif ecc_type == 'LDPC':
            h, g = self.ecc_engine
            decoded_data, success = decode(h, data)
            return decoded_data, not success
        else:
            raise ValueError(f"Unsupported ECC type: {ecc_type}")

    def is_correctable(self, data):
        _, num_errors = self.decode(data)
        return num_errors == 0