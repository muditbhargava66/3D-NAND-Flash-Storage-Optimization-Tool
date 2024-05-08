# tests/unit/test_nand_characterization.py

import unittest
from unittest.mock import MagicMock, patch
from src.nand_characterization import DataCollector, DataAnalyzer, DataVisualizer

class TestDataCollector(unittest.TestCase):
    def setUp(self):
        self.nand_interface = MagicMock()
        self.data_collector = DataCollector(self.nand_interface)

    def test_collect_data(self):
        num_samples = 10
        output_file = 'data.csv'

        self.nand_interface.read_block.return_value = b'block_data'
        self.nand_interface.get_erase_count.return_value = 100
        self.nand_interface.get_bad_block_count.return_value = 5

        with patch('pandas.DataFrame.to_csv') as mock_to_csv:
            self.data_collector.collect_data(num_samples, output_file)

            self.assertEqual(self.nand_interface.read_block.call_count, num_samples)
            self.assertEqual(self.nand_interface.get_erase_count.call_count, num_samples)
            self.assertEqual(self.nand_interface.get_bad_block_count.call_count, num_samples)

            mock_to_csv.assert_called_once_with(output_file, index=False)

class TestDataAnalyzer(unittest.TestCase):
    def setUp(self):
        self.data_file = 'data.csv'
        self.data_analyzer = DataAnalyzer(self.data_file)

    def test_analyze_erase_count_distribution(self):
        self.data_analyzer.data = MagicMock()
        self.data_analyzer.data.__getitem__.return_value = [100, 200, 300, 400, 500]

        result = self.data_analyzer.analyze_erase_count_distribution()

        self.assertIsInstance(result, dict)
        self.assertIn('mean', result)
        self.assertIn('std_dev', result)
        self.assertIn('min', result)
        self.assertIn('max', result)
        self.assertIn('quartiles', result)

    def test_analyze_bad_block_trend(self):
        self.data_analyzer.data = MagicMock()
        self.data_analyzer.data.__getitem__.side_effect = [[1, 2, 3, 4, 5], [5, 10, 15, 20, 25]]

        result = self.data_analyzer.analyze_bad_block_trend()

        self.assertIsInstance(result, dict)
        self.assertIn('slope', result)
        self.assertIn('intercept', result)
        self.assertIn('r_value', result)
        self.assertIn('p_value', result)
        self.assertIn('std_err', result)

class TestDataVisualizer(unittest.TestCase):
    def setUp(self):
        self.data_file = 'data.csv'
        self.data_visualizer = DataVisualizer(self.data_file)

    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    def test_plot_erase_count_distribution(self, mock_close, mock_savefig):
        output_file = 'erase_count_dist.png'
        self.data_visualizer.data = MagicMock()

        self.data_visualizer.plot_erase_count_distribution(output_file)

        mock_savefig.assert_called_once_with(output_file)
        mock_close.assert_called_once()

    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    def test_plot_bad_block_trend(self, mock_close, mock_savefig):
        output_file = 'bad_block_trend.png'
        self.data_visualizer.data = MagicMock()

        self.data_visualizer.plot_bad_block_trend(output_file)

        mock_savefig.assert_called_once_with(output_file)
        mock_close.assert_called_once()

if __name__ == '__main__':
    unittest.main()