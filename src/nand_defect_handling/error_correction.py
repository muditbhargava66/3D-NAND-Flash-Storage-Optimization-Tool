# src/nand_defect_handling/error_correction.py

import numpy as np
from utils.config import Config
from .bch import BCH
from .ldpc import make_ldpc, encode as ldpc_encode, decode as ldpc_decode

class ECCHandler:
    def __init__(self, config: Config):
        # self.ecc_config = config.ecc_config
        self.ecc_config = config.get('ecc_config', {})  # Use get() method to provide a default value
        self.ecc_engine = self._init_ecc_engine()

    def _init_ecc_engine(self):
        ecc_type = self.ecc_config.get('algorithm', 'bch')
        if ecc_type == 'bch':
            m = self.ecc_config.get('bch_params', {}).get('m', 8)
            t = self.ecc_config.get('bch_params', {}).get('t', 4)
            if m < 2 or t < 1 or t > m:
                raise RuntimeError(f"Invalid parameters for BCH: m={m}, t={t}")
            elif t > (m - 1) // 2:
                t = (m - 1) // 2
                print(f"Adjusted t to {t} to ensure valid BCH parameters")
            return BCH(m, t)
        elif ecc_type == 'ldpc':
            n = self.ecc_config.get('ldpc_params', {}).get('n', 1024)
            d_v = self.ecc_config.get('ldpc_params', {}).get('d_v', 3)
            d_c = self.ecc_config.get('ldpc_params', {}).get('d_c', 4)
            h, g = make_ldpc(n, d_v, d_c, systematic=True, sparse=True)
            return h, g
        else:
            raise ValueError(f"Unsupported ECC type: {ecc_type}")

    def encode(self, data):
        ecc_type = self.ecc_config.get('algorithm', 'bch')
        if ecc_type == 'bch':
            ecc_data = self.ecc_engine.encode(data)
            data = np.atleast_1d(data)
            ecc_data = np.atleast_1d(ecc_data)
            return np.concatenate((data, ecc_data))
        elif ecc_type == 'ldpc':
            h, g = self.ecc_engine
            return ldpc_encode(g, data)
        else:
            raise ValueError(f"Unsupported ECC type: {ecc_type}")

    def decode(self, data):
        ecc_type = self.ecc_config.get('algorithm', 'bch')
        if ecc_type == 'bch':
            decoded_data, num_errors = self.ecc_engine.decode(data)
            return decoded_data, num_errors
        elif ecc_type == 'ldpc':
            h, g = self.ecc_engine
            decoded_data, success = ldpc_decode(h, data)
            return decoded_data, not success
        else:
            raise ValueError(f"Unsupported ECC type: {ecc_type}")

    def is_correctable(self, data):
        _, num_errors = self.decode(data)
        return num_errors == 0
    
    def encode_data(self, data):
        # Implement the encode_data method here
        pass
    
    def correct_errors(self, raw_data):
        # implement the logic to correct errors in the raw data
        # for example, you can use a different error correction algorithm
        corrected_data = self.correct_errors_impl(raw_data)
        return corrected_data

    def correct_errors_impl(self, raw_data):
        # implement the logic to correct errors in the raw data
        # for example, you can use a BCH decoder or other error correction algorithm
        corrected_data = self.bch_decoder.decode(raw_data)
        return corrected_data