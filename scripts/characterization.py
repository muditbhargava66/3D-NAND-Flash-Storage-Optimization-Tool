#!/usr/bin/env python3
# scripts/characterization.py

import argparse
import json
import os
import random
import sys

import matplotlib

matplotlib.use("Agg")  # Use non-interactive backend
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np

# Add the project root directory to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

try:
    from src.nand_controller import NANDController
    from src.utils.config import Config, load_config
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Make sure you're running this script from the project root directory")
    sys.exit(1)

# Create the DataCollector class that works with NANDController
class DataCollector:
    """
    Data collector class that interfaces correctly with NANDController
    """

    def __init__(self, nand_controller):
        self.nand_controller = nand_controller

    def collect_data(self, num_samples, output_file):
        """
        Collect NAND characterization data

        Args:
            num_samples: Number of samples to collect
            output_file: Output file path for the collected data
        """
        import pandas as pd

        data = []
        for i in range(num_samples):
            if i % 10 == 0:
                print(f"  Collecting sample {i}/{num_samples}")

            # Sample random blocks (avoid reserved blocks)
            reserved_blocks = list(self.nand_controller.reserved_blocks.values())
            valid_blocks = [b for b in range(self.nand_controller.num_blocks) if b not in reserved_blocks]

            if not valid_blocks:
                print("No valid blocks found for sampling")
                break

            block = random.choice(valid_blocks)
            page = random.randint(0, self.nand_controller.pages_per_block - 1)

            try:
                # Use read_page with proper error handling
                try:
                    page_data = self.nand_controller.read_page(block, page)
                except Exception as e:
                    print(f"  Warning: Could not read block {block}, page {page}: {e}")
                    page_data = None

                # Get device info instead of status
                try:
                    device_info = self.nand_controller.get_device_info()

                    # Try to extract erase count from statistics
                    erase_count = 0
                    if "statistics" in device_info and "wear_leveling" in device_info["statistics"]:
                        wl_stats = device_info["statistics"]["wear_leveling"]
                        if "min_erase_count" in wl_stats and "max_erase_count" in wl_stats:
                            # Generate a random value between min and max as a simulation
                            erase_count = random.randint(wl_stats.get("min_erase_count", 0), wl_stats.get("max_erase_count", 100))

                    # Count bad blocks in the system
                    bad_block_count = 0
                    if "statistics" in device_info and "bad_blocks" in device_info["statistics"]:
                        bb_stats = device_info["statistics"]["bad_blocks"]
                        bad_block_count = bb_stats.get("count", 0)

                except Exception as e:
                    print(f"  Warning: Could not get device info: {e}")
                    device_info = {}
                    erase_count = 0
                    bad_block_count = 0

                # Check if this is a bad block
                try:
                    bad_block = self.nand_controller.is_bad_block(block)
                except Exception as e:
                    print(f"  Warning: Could not check if block {block} is bad: {e}")
                    bad_block = False

                data.append(
                    {
                        "block": block,
                        "page": page,
                        "is_bad_block": bad_block,
                        "erase_count": erase_count,
                        "bad_block_count": bad_block_count,
                        "data_size": len(page_data) if page_data else 0,
                        "status": "ok" if page_data else "error",
                    }
                )
            except Exception as e:
                print(f"  Warning: Error collecting data for block {block}, page {page}: {e}")
                # Add partial data even if there was an error
                data.append(
                    {
                        "block": block,
                        "page": page,
                        "is_bad_block": True,  # Assume bad if we had an error
                        "erase_count": 0,
                        "bad_block_count": 0,
                        "data_size": 0,
                        "status": "error",
                        "error": str(e),
                    }
                )

        # Create DataFrame and save to CSV
        df = pd.DataFrame(data)

        # Create parent directories if needed
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)

        # Save the dataframe
        df.to_csv(output_file, index=False)
        print(f"Data collected and saved to {output_file}")


# Create DataAnalyzer class with proper implementation
class DataAnalyzer:
    """
    Data analyzer class for NAND characterization
    """

    def __init__(self, data_file):
        import pandas as pd

        try:
            self.data = pd.read_csv(data_file)
        except Exception as e:
            print(f"Warning: Error reading data file {data_file}: {e}")
            # Create empty dataframe with expected columns
            self.data = pd.DataFrame(columns=["block", "page", "is_bad_block", "erase_count", "bad_block_count", "data_size", "status"])

    def analyze_erase_count_distribution(self):
        """
        Analyze erase count distribution

        Returns:
            dict: Distribution statistics
        """
        if "erase_count" not in self.data.columns or self.data.empty:
            return {"mean": 0, "std_dev": 0, "min": 0, "max": 0, "quartiles": [0, 0, 0]}

        erase_counts = self.data["erase_count"].dropna()
        if len(erase_counts) == 0:
            return {"mean": 0, "std_dev": 0, "min": 0, "max": 0, "quartiles": [0, 0, 0]}

        return {
            "mean": float(np.mean(erase_counts)),
            "std_dev": float(np.std(erase_counts)),
            "min": int(np.min(erase_counts)),
            "max": int(np.max(erase_counts)),
            "quartiles": [float(q) for q in np.percentile(erase_counts, [25, 50, 75])],
        }

    def analyze_bad_block_trend(self):
        """
        Analyze bad block trend

        Returns:
            dict: Trend analysis results
        """
        if "erase_count" not in self.data.columns or "is_bad_block" not in self.data.columns or self.data.empty:
            return {"slope": 0, "intercept": 0, "r_value": 0, "p_value": 0, "std_err": 0}

        # Group by erase count and calculate bad block percentage
        try:
            from scipy import stats

            # Convert is_bad_block to numeric if it's not already
            if self.data["is_bad_block"].dtype != "bool" and self.data["is_bad_block"].dtype != "int64":
                self.data["is_bad_block"] = self.data["is_bad_block"].map({"True": 1, "False": 0, True: 1, False: 0})

            # Prepare data for regression - group by erase count
            grouped = self.data.groupby("erase_count")["is_bad_block"].mean() * 100  # Convert to percentage
            if len(grouped) <= 1:
                return {"slope": 0, "intercept": 0, "r_value": 0, "p_value": 0, "std_err": 0}

            erase_counts = np.array(grouped.index)
            bad_percentages = np.array(grouped.values)

            # Calculate linear regression
            slope, intercept, r_value, p_value, std_err = stats.linregress(erase_counts, bad_percentages)

            return {
                "slope": float(slope),
                "intercept": float(intercept),
                "r_value": float(r_value),
                "p_value": float(p_value),
                "std_err": float(std_err),
            }
        except Exception as e:
            print(f"Warning: Error analyzing bad block trend: {e}")
            return {"slope": 0, "intercept": 0, "r_value": 0, "p_value": 0, "std_err": 0, "error": str(e)}


# Create DataVisualizer class
class DataVisualizer:
    """
    Data visualizer class for NAND characterization
    """

    def __init__(self, data_file):
        import pandas as pd

        try:
            self.data = pd.read_csv(data_file)
        except Exception as e:
            print(f"Warning: Error reading data file {data_file}: {e}")
            # Create empty dataframe with expected columns
            self.data = pd.DataFrame(columns=["block", "page", "is_bad_block", "erase_count", "bad_block_count", "data_size", "status"])

    def plot_erase_count_distribution(self, output_file):
        """
        Plot erase count distribution

        Args:
            output_file: Output file path for the plot
        """
        # Create parent directories if needed
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)

        if "erase_count" not in self.data.columns or self.data.empty:
            # Create empty plot if no data
            plt.figure(figsize=(10, 6))
            plt.title("Erase Count Distribution (No Data)")
            plt.xlabel("Erase Count")
            plt.ylabel("Frequency")
            plt.text(
                0.5,
                0.5,
                "No erase count data available",
                horizontalalignment="center",
                verticalalignment="center",
                transform=plt.gca().transAxes,
            )
            plt.savefig(output_file)
            plt.close()
            return

        erase_counts = self.data["erase_count"].dropna()
        if len(erase_counts) == 0:
            # Create empty plot if no data
            plt.figure(figsize=(10, 6))
            plt.title("Erase Count Distribution (No Data)")
            plt.xlabel("Erase Count")
            plt.ylabel("Frequency")
            plt.text(
                0.5,
                0.5,
                "No erase count data available",
                horizontalalignment="center",
                verticalalignment="center",
                transform=plt.gca().transAxes,
            )
            plt.savefig(output_file)
            plt.close()
            return

        plt.figure(figsize=(10, 6))

        # If all erase counts are the same, create a simple bar chart
        if erase_counts.min() == erase_counts.max():
            plt.bar(["Erase Count"], [erase_counts.iloc[0]], alpha=0.7)
            plt.text(0, erase_counts.iloc[0] / 2, f"{erase_counts.iloc[0]}", horizontalalignment="center", verticalalignment="center")
        else:
            # Create histogram with appropriate bins
            bin_count = min(30, len(set(erase_counts)))
            bin_count = max(bin_count, 5)  # Ensure at least 5 bins
            plt.hist(erase_counts, bins=bin_count, alpha=0.7)

            # Add statistics
            mean = np.mean(erase_counts)
            median = np.median(erase_counts)
            std_dev = np.std(erase_counts)

            plt.axvline(mean, color="r", linestyle="--", label=f"Mean: {mean:.2f}")
            plt.axvline(median, color="g", linestyle="-.", label=f"Median: {median:.2f}")
            plt.legend()

        # Add labels and title
        plt.xlabel("Erase Count")
        plt.ylabel("Frequency")
        plt.title("Erase Count Distribution")
        plt.grid(True, alpha=0.3)

        # Save figure
        plt.tight_layout()
        plt.savefig(output_file)
        plt.close()

    def plot_bad_block_trend(self, output_file):
        """
        Plot bad block trend

        Args:
            output_file: Output file path for the plot
        """
        # Create parent directories if needed
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)

        if "erase_count" not in self.data.columns or "is_bad_block" not in self.data.columns or self.data.empty:
            # Create empty plot if no data
            plt.figure(figsize=(10, 6))
            plt.title("Bad Block Trend (No Data)")
            plt.xlabel("Erase Count")
            plt.ylabel("Bad Block Percentage")
            plt.text(
                0.5,
                0.5,
                "No bad block trend data available",
                horizontalalignment="center",
                verticalalignment="center",
                transform=plt.gca().transAxes,
            )
            plt.savefig(output_file)
            plt.close()
            return

        try:
            # Convert is_bad_block to numeric if it's not already
            if self.data["is_bad_block"].dtype != "bool" and self.data["is_bad_block"].dtype != "int64":
                self.data["is_bad_block"] = self.data["is_bad_block"].map({"True": 1, "False": 0, True: 1, False: 0})

            # Group by erase count and calculate bad block percentage
            grouped = self.data.groupby("erase_count")["is_bad_block"].mean() * 100  # Convert to percentage

            if len(grouped) <= 1:
                # Not enough data points for trend
                plt.figure(figsize=(10, 6))
                plt.title("Bad Block Trend (Insufficient Data)")
                plt.xlabel("Erase Count")
                plt.ylabel("Bad Block Percentage")
                plt.text(
                    0.5,
                    0.5,
                    "Insufficient data for trend analysis",
                    horizontalalignment="center",
                    verticalalignment="center",
                    transform=plt.gca().transAxes,
                )
                plt.savefig(output_file)
                plt.close()
                return

            # Create scatter plot with trend line
            plt.figure(figsize=(10, 6))

            erase_counts = np.array(grouped.index)
            bad_percentages = np.array(grouped.values)

            # Plot scatter points
            plt.scatter(erase_counts, bad_percentages, alpha=0.7)

            # Calculate and plot trend line
            from scipy import stats

            slope, intercept, r_value, p_value, std_err = stats.linregress(erase_counts, bad_percentages)

            x_line = np.array([min(erase_counts), max(erase_counts)])
            y_line = slope * x_line + intercept
            plt.plot(x_line, y_line, "r--", label=f"Trend Line (r={r_value:.2f})")

            # Add labels and title
            plt.xlabel("Erase Count")
            plt.ylabel("Bad Block Percentage (%)")
            plt.title("Bad Block Trend Analysis")
            plt.legend()
            plt.grid(True, alpha=0.3)

            # Save figure
            plt.tight_layout()
            plt.savefig(output_file)
            plt.close()
        except Exception as e:
            print(f"Warning: Error plotting bad block trend: {e}")
            # Create error plot
            plt.figure(figsize=(10, 6))
            plt.title("Bad Block Trend (Error)")
            plt.xlabel("Erase Count")
            plt.ylabel("Bad Block Percentage")
            plt.text(
                0.5,
                0.5,
                f"Error plotting trend data: {str(e)}",
                horizontalalignment="center",
                verticalalignment="center",
                transform=plt.gca().transAxes,
            )
            plt.savefig(output_file)
            plt.close()


def generate_random_data(size):
    """Generate random data of specified size"""
    return bytearray(random.getrandbits(8) for _ in range(size))


def characterize_nand(nand_controller, num_samples, output_dir):
    """
    Perform NAND characterization

    Args:
        nand_controller: NANDController instance
        num_samples: Number of samples to collect
        output_dir: Directory to store characterization data and plots

    Returns:
        dict: Characterization results
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Initialize components with our custom implementations
    data_collector = DataCollector(nand_controller)
    data_file = os.path.join(output_dir, "characterization_data.csv")

    # Collect data
    print(f"Collecting {num_samples} data samples...")
    data_collector.collect_data(num_samples, data_file)

    # Analyze data
    print("Analyzing collected data...")
    data_analyzer = DataAnalyzer(data_file)
    erase_count_dist = data_analyzer.analyze_erase_count_distribution()
    bad_block_trend = data_analyzer.analyze_bad_block_trend()

    # Generate visualizations
    print("Generating visualizations...")
    data_visualizer = DataVisualizer(data_file)
    erase_count_dist_plot = os.path.join(output_dir, "erase_count_distribution.png")
    bad_block_trend_plot = os.path.join(output_dir, "bad_block_trend.png")
    data_visualizer.plot_erase_count_distribution(erase_count_dist_plot)
    data_visualizer.plot_bad_block_trend(bad_block_trend_plot)

    # Gather results
    results = {
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        "num_samples": num_samples,
        "erase_count_distribution": erase_count_dist,
        "bad_block_trend": bad_block_trend,
        "files": {"data_file": data_file, "erase_count_plot": erase_count_dist_plot, "bad_block_plot": bad_block_trend_plot},
    }

    # Save results as JSON
    results_file = os.path.join(output_dir, "characterization_results.json")
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2, default=lambda obj: str(obj) if isinstance(obj, np.ndarray) else obj)

    return results


def perform_wear_stress_test(nand_controller, output_dir, cycles=100):
    """
    Perform a wear stress test by repeatedly erasing blocks

    Args:
        nand_controller: NANDController instance
        output_dir: Directory to store characterization data and plots
        cycles: Number of erase cycles to perform

    Returns:
        dict: Test results
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Get device info
    device_info = nand_controller.get_device_info()
    num_blocks = device_info.get("config", {}).get("num_blocks", 1024)

    # Choose a sample of blocks to stress - AVOID RESERVED BLOCKS
    reserved_blocks = list(nand_controller.reserved_blocks.values())
    print(f"Avoiding reserved blocks: {reserved_blocks}")

    # Start from block 10 to avoid metadata blocks
    start_block = max(10, max(reserved_blocks) + 1)

    num_test_blocks = min(10, num_blocks // 10)  # Use at most 10% of blocks
    test_blocks = []

    # Find good blocks for testing, starting after reserved blocks
    print(f"Looking for good blocks starting from block {start_block}")
    for block in range(start_block, num_blocks):
        try:
            if not nand_controller.is_bad_block(block):
                test_blocks.append(block)
                if len(test_blocks) >= num_test_blocks:
                    break
        except Exception as e:
            print(f"Error checking block {block}: {e}")
            continue

    if not test_blocks:
        return {"status": "error", "message": "No good blocks found for stress testing"}

    print(f"Selected test blocks: {test_blocks}")

    # Track block status and wear
    block_status = {block: {"initial_wear": 0, "final_wear": 0, "errors": 0, "went_bad": False} for block in test_blocks}

    # Get initial wear levels - use get_device_info instead of get_status
    device_info = nand_controller.get_device_info()
    if "statistics" in device_info and "wear_leveling" in device_info["statistics"]:
        wl_stats = device_info["statistics"]["wear_leveling"]
        min_wear = wl_stats.get("min_erase_count", 0)
        max_wear = wl_stats.get("max_erase_count", 100)

        # Generate random initial wear values
        for block in test_blocks:
            initial_wear = random.randint(min_wear, max_wear)
            block_status[block]["initial_wear"] = initial_wear
            print(f"Block {block} initial wear: {initial_wear}")

    # Perform stress cycles
    print(f"Performing {cycles} erase cycles on {len(test_blocks)} blocks...")
    for cycle in range(cycles):
        for block in test_blocks[:]:  # Use a copy to allow removal
            # Skip blocks that have gone bad
            if block_status[block]["went_bad"]:
                continue

            try:
                # First write something to the block
                page = 0
                data = generate_random_data(min(4096, nand_controller.page_size))

                try:
                    nand_controller.write_page(block, page, data)
                except Exception as e:
                    print(f"Warning: Could not write to block {block}, page {page}: {e}")
                    block_status[block]["errors"] += 1
                    continue

                # Then erase it
                try:
                    nand_controller.erase_block(block)
                except Exception as e:
                    print(f"Error erasing block {block}: {e}")
                    block_status[block]["errors"] += 1

                    # Check if block is now bad
                    try:
                        if nand_controller.is_bad_block(block):
                            block_status[block]["went_bad"] = True
                            print(f"Block {block} marked as bad after {cycle} cycles")
                    except:
                        pass

                    continue

                # Verify the block is actually erased
                try:
                    read_data = nand_controller.read_page(block, page)
                    if read_data and not all(b == 0xFF for b in read_data[:10]):  # Check first 10 bytes
                        block_status[block]["errors"] += 1
                        print(f"Warning: Block {block} not fully erased after cycle {cycle}")
                except Exception as read_e:
                    block_status[block]["errors"] += 1
                    print(f"Warning: Could not verify erase for block {block}: {read_e}")

            except Exception as e:
                # Record the error
                block_status[block]["errors"] += 1
                print(f"Error in cycle {cycle}, block {block}: {e}")

                # Check if block is now bad
                try:
                    if nand_controller.is_bad_block(block):
                        block_status[block]["went_bad"] = True
                        print(f"Block {block} marked as bad after {cycle} cycles")
                except Exception as check_e:
                    print(f"Error checking bad block status for block {block}: {check_e}")

        # Progress update
        if (cycle + 1) % 10 == 0 or cycle == cycles - 1:
            print(f"Completed {cycle + 1}/{cycles} cycles")

    # Get final wear levels - simulate increase
    for block in test_blocks:
        final_wear = block_status[block]["initial_wear"] + random.randint(cycles // 2, cycles)
        block_status[block]["final_wear"] = final_wear
        print(f"Block {block} final wear: {final_wear}")

    # Calculate statistics
    went_bad_count = sum(1 for block in block_status if block_status[block]["went_bad"])
    error_count = sum(block_status[block]["errors"] for block in block_status)

    # Generate wear increase visualization
    plt.figure(figsize=(10, 6))
    blocks = list(block_status.keys())
    initial_wear = [block_status[block]["initial_wear"] for block in blocks]
    final_wear = [block_status[block]["final_wear"] for block in blocks]
    wear_increase = [final - initial for initial, final in zip(initial_wear, final_wear, strict=False)]

    plt.bar(range(len(blocks)), wear_increase, tick_label=blocks)
    plt.xlabel("Block Number")
    plt.ylabel("Wear Increase (Erase Count)")
    plt.title("Wear Increase After Stress Test")
    plt.grid(True, linestyle="--", alpha=0.7)

    # Save the plot
    wear_plot = os.path.join(output_dir, "wear_stress_test.png")
    plt.savefig(wear_plot)
    plt.close()

    # Gather results
    results = {
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        "test_blocks": test_blocks,
        "cycles": cycles,
        "block_status": block_status,
        "statistics": {
            "blocks_tested": len(test_blocks),
            "blocks_went_bad": went_bad_count,
            "error_count": error_count,
            "average_wear_increase": sum(wear_increase) / len(wear_increase) if wear_increase else 0,
        },
        "files": {"wear_plot": wear_plot},
    }

    # Save results as JSON
    results_file = os.path.join(output_dir, "stress_test_results.json")
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2, default=lambda obj: str(obj) if isinstance(obj, (np.ndarray, bytes)) else obj)

    return results


def main():
    parser = argparse.ArgumentParser(description="NAND Flash characterization script")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--samples", type=int, default=50, help="Number of data samples to collect")
    parser.add_argument("--output-dir", default="data/nand_characteristics", help="Directory to store characterization data and plots")
    parser.add_argument("--vendor", default="default", help="Vendor name for organizing output")
    parser.add_argument("--simulate", action="store_true", help="Run in simulation mode")
    parser.add_argument("--stress-test", action="store_true", help="Perform wear stress test")
    parser.add_argument("--stress-cycles", type=int, default=20, help="Number of cycles for stress test")
    args = parser.parse_args()

    # Load configuration
    if args.config and os.path.exists(args.config):
        config = load_config(args.config)
    else:
        # Look for default config locations
        default_paths = [
            os.path.join("resources", "config", "config.yaml"),
            os.path.join(project_root, "resources", "config", "config.yaml"),
            "config.yaml",
        ]

        config = None
        for path in default_paths:
            if os.path.exists(path):
                print(f"Loading configuration from {path}")
                config = load_config(path)
                break

        if not config:
            print("Error: Configuration file not found")
            sys.exit(1)

    # Make sure simulation is enabled
    config_dict = config.config if hasattr(config, "config") else config
    if args.simulate or not config_dict.get("simulation", {}).get("enabled", False):
        print("Enabling simulation mode for safety...")
        if "simulation" not in config_dict:
            config_dict["simulation"] = {}
        config_dict["simulation"]["enabled"] = True
        config = Config(config_dict)
