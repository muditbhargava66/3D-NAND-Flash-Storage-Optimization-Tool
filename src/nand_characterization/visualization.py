# src/nand_characterization/visualization.py

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


class DataVisualizer:
    def __init__(self, data_file: str):
        self.data = pd.read_csv(data_file)

    def plot_erase_count_distribution(self, output_file: str):
        plt.figure(figsize=(8, 6))
        sns.histplot(data=self.data, x="erase_count", kde=True)
        plt.xlabel("Erase Count")
        plt.ylabel("Frequency")
        plt.title("Erase Count Distribution")
        plt.tight_layout()
        plt.savefig(output_file)
        plt.close()

    def plot_bad_block_trend(self, output_file: str):
        plt.figure(figsize=(8, 6))
        sns.regplot(data=self.data, x="erase_count", y="bad_block_count")
        plt.xlabel("Erase Count")
        plt.ylabel("Bad Block Count")
        plt.title("Bad Block Trend")
        plt.tight_layout()
        plt.savefig(output_file)
        plt.close()
