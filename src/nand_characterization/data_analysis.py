# src/nand_characterization/data_analysis.py

import pandas as pd
import numpy as np
from scipy import stats

class DataAnalyzer:
    def __init__(self, data_file: str):
        self.data = pd.read_csv(data_file)

    def analyze_erase_count_distribution(self):
        erase_counts = self.data['erase_count']
        mean = np.mean(erase_counts)
        std_dev = np.std(erase_counts)
        min_val = np.min(erase_counts)
        max_val = np.max(erase_counts)
        quartiles = np.percentile(erase_counts, [25, 50, 75])
        return {
            'mean': mean,
            'std_dev': std_dev,
            'min': min_val,
            'max': max_val,
            'quartiles': quartiles
        }

    def analyze_bad_block_trend(self):
        bad_block_counts = self.data['bad_block_count']
        erase_counts = self.data['erase_count']
        slope, intercept, r_value, p_value, std_err = stats.linregress(erase_counts, bad_block_counts)
        return {
            'slope': slope,
            'intercept': intercept,
            'r_value': r_value,
            'p_value': p_value,
            'std_err': std_err
        }