# scripts/characterization.py

import random
from src.nand_controller import NANDController
from src.nand_characterization import DataCollector, DataAnalyzer, DataVisualizer

def generate_random_data(size):
    return bytearray(random.getrandbits(8) for _ in range(size))

def characterize_nand(nand_controller, num_samples):
    data_collector = DataCollector(nand_controller)
    data_file = 'data/nand_characteristics/vendor_a/data.csv'
    data_collector.collect_data(num_samples, data_file)
    
    data_analyzer = DataAnalyzer(data_file)
    erase_count_dist = data_analyzer.analyze_erase_count_distribution()
    bad_block_trend = data_analyzer.analyze_bad_block_trend()
    
    data_visualizer = DataVisualizer(data_file)
    erase_count_dist_plot = 'data/nand_characteristics/vendor_a/erase_count_dist.png'
    bad_block_trend_plot = 'data/nand_characteristics/vendor_a/bad_block_trend.png'
    data_visualizer.plot_erase_count_distribution(erase_count_dist_plot)
    data_visualizer.plot_bad_block_trend(bad_block_trend_plot)
    
    print(f"NAND characterization completed with {num_samples} samples")
    print(f"Erase count distribution: {erase_count_dist}")
    print(f"Bad block trend: {bad_block_trend}")

def main():
    config = {
        'page_size': 4096,
        'block_size': 256,
        'num_blocks': 1024,
        'oob_size': 128
    }
    nand_controller = NANDController(config)
    nand_controller.initialize()
    
    num_samples = 1000
    characterize_nand(nand_controller, num_samples)
    
    nand_controller.shutdown()

if __name__ == '__main__':
    main()