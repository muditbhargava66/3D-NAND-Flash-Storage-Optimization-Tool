# src/performance_optimization/data_compression.py

import lz4.frame
import zstd

class DataCompressor:
    def __init__(self, algorithm='lz4', level=3):
        self.algorithm = algorithm
        self.level = level

    def compress(self, data):
        if self.algorithm == 'lz4':
            return lz4.frame.compress(data, compression_level=self.level)
        elif self.algorithm == 'zstd':
            return zstd.compress(data, self.level)
        else:
            raise ValueError(f"Unsupported compression algorithm: {self.algorithm}")

    def decompress(self, data):
        if self.algorithm == 'lz4':
            return lz4.frame.decompress(data)
        elif self.algorithm == 'zstd':
            return zstd.decompress(data)
        else:
            raise ValueError(f"Unsupported compression algorithm: {self.algorithm}")