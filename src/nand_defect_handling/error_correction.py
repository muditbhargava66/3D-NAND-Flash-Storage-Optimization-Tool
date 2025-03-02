# src/nand_defect_handling/error_correction.py

import numpy as np

from src.utils.config import Config
from src.utils.logger import get_logger

from .bch import BCH
from .ldpc import decode as ldpc_decode
from .ldpc import encode as ldpc_encode
from .ldpc import make_ldpc


class ECCHandler:
    """
    Handles error correction coding (ECC) for NAND flash data.

    This class provides a unified interface for different error correction
    algorithms like BCH and LDPC, handling encoding, decoding, and error
    detection/correction operations.
    """

    def __init__(self, config: Config):
        """
        Initialize the ECC handler with the specified configuration.

        Args:
            config: Configuration object containing ECC parameters
        """
        self.ecc_config = config.get("optimization_config", {}).get("error_correction", {})
        self.logger = get_logger(__name__)
        self.ecc_engine, self.ecc_type = self._init_ecc_engine()

    def _init_ecc_engine(self):
        """
        Initialize the appropriate ECC engine based on configuration.

        Returns:
            tuple: (ecc_engine, ecc_type) - The initialized ECC engine and its type
        """
        ecc_type = self.ecc_config.get("algorithm", "bch").lower()

        if ecc_type == "bch":
            # Initialize BCH codec
            m = self.ecc_config.get("bch_params", {}).get("m", 8)
            t = self.ecc_config.get("bch_params", {}).get("t", 4)

            self.logger.info(f"Initializing BCH codec with m={m}, t={t}")

            if m < 3 or t < 1 or t > 2 ** (m - 1) - 1:
                err_msg = f"Invalid parameters for BCH: m={m}, t={t}"
                self.logger.error(err_msg)
                raise RuntimeError(err_msg)

            return BCH(m, t), ecc_type

        elif ecc_type == "ldpc":
            # Initialize LDPC codec
            n = self.ecc_config.get("ldpc_params", {}).get("n", 1024)
            d_v = self.ecc_config.get("ldpc_params", {}).get("d_v", 3)
            d_c = self.ecc_config.get("ldpc_params", {}).get("d_c", 6)
            systematic = self.ecc_config.get("ldpc_params", {}).get("systematic", True)
            sparse = self.ecc_config.get("ldpc_params", {}).get("sparse", True)

            self.logger.info(f"Initializing LDPC codec with n={n}, d_v={d_v}, d_c={d_c}")

            try:
                h, g = make_ldpc(n, d_v, d_c, systematic=systematic, sparse=sparse)
                return (h, g), ecc_type
            except Exception as e:
                err_msg = f"Failed to initialize LDPC: {str(e)}"
                self.logger.error(err_msg)
                raise RuntimeError(err_msg)
        else:
            err_msg = f"Unsupported ECC type: {ecc_type}"
            self.logger.error(err_msg)
            raise ValueError(err_msg)

    def encode(self, data):
        """
        Encode data using the configured ECC algorithm.

        Args:
            data: Data to encode (bytes or bytearray)

        Returns:
            bytes or numpy.ndarray: Encoded data with ECC
        """
        if not isinstance(data, (bytes, bytearray, np.ndarray)):
            data = np.array(data, dtype=np.uint8)

        try:
            if self.ecc_type == "bch":
                # For BCH, we return data + ECC
                ecc_data = self.ecc_engine.encode(data)

                if isinstance(data, (bytes, bytearray)):
                    # If data is bytes, return data + ECC as bytes
                    return data + ecc_data
                else:
                    # If data is numpy array, concatenate arrays
                    data_array = np.asarray(data)
                    ecc_array = np.frombuffer(ecc_data, dtype=np.uint8)
                    return np.concatenate((data_array, ecc_array))

            elif self.ecc_type == "ldpc":
                # For LDPC, we return the full codeword
                h, g = self.ecc_engine
                codeword = ldpc_encode(g, data)

                if isinstance(data, (bytes, bytearray)):
                    # If data is bytes, return codeword as bytes
                    return np.packbits(codeword).tobytes()
                else:
                    # If data is numpy array, return codeword as array
                    return codeword

        except Exception as e:
            self.logger.error(f"Error encoding data: {str(e)}")
            raise RuntimeError(f"ECC encoding failed: {str(e)}")

    def decode(self, data):
        """
        Decode data using the configured ECC algorithm and correct errors.

        Args:
            data: Data to decode (bytes, bytearray, or numpy.ndarray)

        Returns:
            tuple: (decoded_data, num_errors) - Decoded data and number of corrected errors
        """
        if data is None:
            self.logger.error("Received None as input data to decode")
            return None, 0

        try:
            if self.ecc_type == "bch":
                # For BCH, data should contain both data and ECC
                decoded_data, num_errors = self.ecc_engine.decode(data)

                if decoded_data is None:
                    self.logger.warning(f"BCH decoding failed with {num_errors} errors")
                    if num_errors > self.ecc_engine.t:
                        raise ValueError(f"Too many errors to correct: {num_errors} > {self.ecc_engine.t}")
                    # Return input data without ECC as fallback
                    if isinstance(data, (bytes, bytearray)):
                        return data[: -self.ecc_engine.ecc_bytes], num_errors
                    else:
                        return data[: -self.ecc_engine.ecc_bytes], num_errors

                return decoded_data, num_errors

            elif self.ecc_type == "ldpc":
                # For LDPC, data is the full codeword
                h, g = self.ecc_engine

                # If data is bytes, convert to bit array
                if isinstance(data, (bytes, bytearray)):
                    data_bits = np.unpackbits(np.frombuffer(data, dtype=np.uint8))
                else:
                    data_bits = np.asarray(data, dtype=np.uint8)

                # Get code parameters
                n = h.shape[1]  # Codeword length
                k = g.shape[1]  # Information length

                # Ensure data has correct length
                if len(data_bits) < n:
                    # Pad with zeros if needed
                    padded_data = np.zeros(n, dtype=np.uint8)
                    padded_data[: len(data_bits)] = data_bits
                    data_bits = padded_data
                elif len(data_bits) > n:
                    # Truncate if too long
                    data_bits = data_bits[:n]

                # Decode
                decoded_bits, success = ldpc_decode(h, data_bits)

                if not success:
                    self.logger.warning("LDPC decoding failed")
                    # Return original data as fallback (for systematic codes)
                    if isinstance(data, (bytes, bytearray)):
                        # Information bits are at the beginning for systematic codes
                        return data[: k // 8], 0
                    else:
                        return data_bits[:k], 0

                # For systematic codes, information bits are at the beginning
                if isinstance(data, (bytes, bytearray)):
                    # Convert bits back to bytes
                    return np.packbits(decoded_bits[:k]).tobytes(), 0
                else:
                    return decoded_bits, 0

        except Exception as e:
            self.logger.error(f"Error decoding data: {str(e)}")
            raise ValueError(f"ECC decoding failed: {str(e)}")

    def is_correctable(self, data):
        """
        Check if the data can be corrected with the configured ECC.

        Args:
            data: Data to check (with ECC)

        Returns:
            bool: True if data can be corrected, False otherwise
        """
        try:
            _, num_errors = self.decode(data)
            return True
        except ValueError:
            return False  # Not correctable

    def encode_data(self, data):
        """
        Alias for encode method.

        Args:
            data: Data to encode

        Returns:
            bytes or numpy.ndarray: Encoded data with ECC
        """
        return self.encode(data)

    def correct_errors(self, raw_data):
        """
        Decode and correct errors in the raw data.

        Args:
            raw_data: Raw data with ECC to correct

        Returns:
            bytes or numpy.ndarray: Corrected data without ECC
        """
        decoded_data, _ = self.decode(raw_data)
        return decoded_data
