# src/performance_optimization/data_compression.py

import lz4.frame
import zstd


class DataCompressor:
    def __init__(self, algorithm="lz4", level=3):
        self.algorithm = algorithm
        self.level = level

    def compress(self, data):
        """
        Compresses the input data using the specified algorithm.

        Args:
            data (bytes): The data to compress

        Returns:
            bytes: The compressed data
        """
        if not data:  # Handle empty data case specially
            return b""

        if self.algorithm == "lz4":
            return lz4.frame.compress(data, compression_level=self.level)
        elif self.algorithm == "zstd":
            return zstd.compress(data, self.level)
        else:
            raise ValueError(f"Unsupported compression algorithm: {self.algorithm}")

    def decompress(self, data):
        """
        Decompresses the input data using the specified algorithm.

        Args:
            data (bytes): The compressed data

        Returns:
            bytes: The decompressed data

        Raises:
            ValueError: If the data is invalid or not compressed with the expected algorithm
        """
        if not data:  # Handle empty data case specially
            return b""

        try:
            if self.algorithm == "lz4":
                return lz4.frame.decompress(data)
            elif self.algorithm == "zstd":
                return zstd.decompress(data)
            else:
                raise ValueError(f"Unsupported compression algorithm: {self.algorithm}")
        except Exception as e:
            # Catch any exception that might happen during decompression
            # This handles both RuntimeError from lz4 and any errors from zstd
            raise ValueError(f"Invalid compressed data: {str(e)}")
