# tests/unit/test_nand_characterization.py

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import unittest
from unittest.mock import MagicMock, patch

import pandas as pd

from src.nand_characterization.data_analysis import DataAnalyzer
from src.nand_characterization.data_collection import DataCollector
from src.nand_characterization.visualization import DataVisualizer


class TestDataCollector(unittest.TestCase):
    def setUp(self):
        self.nand_interface = MagicMock()
        self.data_collector = DataCollector(self.nand_interface)

    def test_collect_data(self):
        num_samples = 10
        output_file = "data.csv"

        self.nand_interface.read_block.return_value = b"block_data"
        self.nand_interface.get_erase_count.return_value = 100
        self.nand_interface.get_bad_block_count.return_value = 5

        with patch("pandas.DataFrame.to_csv") as mock_to_csv:
            self.data_collector.collect_data(num_samples, output_file)

            self.assertEqual(self.nand_interface.read_block.call_count, num_samples)
            self.assertEqual(self.nand_interface.get_erase_count.call_count, num_samples)
            self.assertEqual(self.nand_interface.get_bad_block_count.call_count, num_samples)

            mock_to_csv.assert_called_once_with(output_file, index=False)


class TestDataAnalyzer(unittest.TestCase):
    def setUp(self):
        self.data_file = "data.csv"
        # Create a mock DataFrame instead of reading from file
        mock_data = {"erase_count": [100, 200, 300, 400, 500], "bad_block_count": [5, 10, 15, 20, 25]}
        with patch("pandas.read_csv", return_value=pd.DataFrame(mock_data)):
            self.data_analyzer = DataAnalyzer(self.data_file)

    def test_analyze_erase_count_distribution(self):
        result = self.data_analyzer.analyze_erase_count_distribution()

        self.assertIsInstance(result, dict)
        self.assertIn("mean", result)
        self.assertIn("std_dev", result)
        self.assertIn("min", result)
        self.assertIn("max", result)
        self.assertIn("quartiles", result)

        # Test specific values
        self.assertEqual(result["mean"], 300)
        self.assertEqual(result["min"], 100)
        self.assertEqual(result["max"], 500)

    def test_analyze_bad_block_trend(self):
        result = self.data_analyzer.analyze_bad_block_trend()

        self.assertIsInstance(result, dict)
        self.assertIn("slope", result)
        self.assertIn("intercept", result)
        self.assertIn("r_value", result)
        self.assertIn("p_value", result)
        self.assertIn("std_err", result)

        # Linear relationship is perfect in our mock data, so r_value should be 1.0
        self.assertAlmostEqual(result["r_value"], 1.0)


class TestDataVisualizer(unittest.TestCase):
    def setUp(self):
        self.data_file = "data.csv"
        # Create a mock DataFrame instead of reading from file
        mock_data = {"erase_count": [100, 200, 300, 400, 500], "bad_block_count": [5, 10, 15, 20, 25]}
        with patch("pandas.read_csv", return_value=pd.DataFrame(mock_data)):
            self.data_visualizer = DataVisualizer(self.data_file)

    @patch("matplotlib.pyplot.savefig")
    @patch("matplotlib.pyplot.close")
    def test_plot_erase_count_distribution(self, mock_close, mock_savefig):
        output_file = "erase_count_dist.png"

        # Mock the plotting functions to avoid actual rendering
        with patch("seaborn.histplot"), patch("matplotlib.pyplot.figure"), patch("matplotlib.pyplot.xlabel"), patch("matplotlib.pyplot.ylabel"), patch(
            "matplotlib.pyplot.title"
        ), patch("matplotlib.pyplot.tight_layout"):

            self.data_visualizer.plot_erase_count_distribution(output_file)

        mock_savefig.assert_called_once_with(output_file)
        mock_close.assert_called_once()

    @patch("matplotlib.pyplot.savefig")
    @patch("matplotlib.pyplot.close")
    def test_plot_bad_block_trend(self, mock_close, mock_savefig):
        output_file = "bad_block_trend.png"

        # Mock the plotting functions to avoid actual rendering
        with patch("seaborn.regplot"), patch("matplotlib.pyplot.figure"), patch("matplotlib.pyplot.xlabel"), patch("matplotlib.pyplot.ylabel"), patch(
            "matplotlib.pyplot.title"
        ), patch("matplotlib.pyplot.tight_layout"):

            self.data_visualizer.plot_bad_block_trend(output_file)

        mock_savefig.assert_called_once_with(output_file)
        mock_close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
