#!/usr/bin/env python3
# src/main.py

import argparse
import os
import sys
import tempfile

import yaml

# Add the parent directory to the Python path so we can use relative imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nand_controller import NANDController
from PyQt5.QtWidgets import QApplication

# Import our modules after fixing the path
from ui.main_window import MainWindow
from utils.config import Config, load_config
from utils.logger import get_logger, setup_logger


def setup_config(config_path=None):
    """
    Set up configuration with improved error handling and fallbacks

    Args:
        config_path: Path to the configuration file

    Returns:
        Config: Configuration object
    """
    print("Initializing configuration...")

    # Default configuration paths to try
    default_paths = [
        config_path,  # User-provided path (if any)
        os.path.join("resources", "config", "config.yaml"),
        os.path.join(os.path.dirname(__file__), "..", "resources", "config", "config.yaml"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "resources", "config", "config.yaml"),
        "config.yaml",
    ]

    # Try each path until we find a valid one
    for path in default_paths:
        if path and os.path.exists(path):
            try:
                print(f"Loading configuration from {path}")
                config = load_config(path)
                print(f"Configuration loaded successfully from {path}")
                return config
            except Exception as e:
                print(f"Warning: Failed to load configuration from {path}: {e}")

    # If no config file found, create a basic default configuration
    print("Warning: No configuration file found. Using default configuration.")
    default_config = {
        "nand_config": {
            "page_size": 4096,
            "block_size": 256,  # pages per block
            "num_blocks": 1024,
            "oob_size": 128,
            "num_planes": 1,
        },
        "optimization_config": {
            "error_correction": {
                "algorithm": "bch",
                "bch_params": {"m": 8, "t": 4},
                "strength": 4,  # Add explicit strength parameter for template
            },
            "compression": {"enabled": True, "algorithm": "lz4", "level": 3},
            "caching": {"enabled": True, "capacity": 1024, "policy": "lru"},
            "wear_leveling": {"wear_level_threshold": 1000},
            "parallelism": {"max_workers": 4},
        },
        "firmware_config": {"version": "1.0.0", "read_retry": True, "max_read_retries": 3, "data_scrambling": False},
        "bbm_config": {
            "max_bad_blocks": 100,  # Add explicit max_bad_blocks for template
        },
        "wl_config": {"wear_leveling_threshold": 1000},  # Add explicit parameter for template
        "logging": {
            "level": "INFO",
            "file": "logs/nand_optimization.log",
            "max_size": 10 * 1024 * 1024,  # 10 MB
            "backup_count": 5,
        },
        "ui_config": {"theme": "light", "font_size": 12, "window_size": [1200, 800]},
        "simulation": {"enabled": True, "error_rate": 0.0001, "initial_bad_block_rate": 0.002},  # Use simulator by default
    }

    return Config(default_config)


def setup_logging_directory(config):
    """
    Create the logging directory if it doesn't exist

    Args:
        config: Configuration object
    """
    log_file = config.get("logging", {}).get("file", "logs/nand_optimization.log")
    log_dir = os.path.dirname(log_file)

    if log_dir and not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir)
        except Exception as e:
            print(f"Warning: Failed to create log directory {log_dir}: {e}")
            # Use a temp file as fallback
            temp_log = os.path.join(tempfile.gettempdir(), "nand_optimization.log")
            config.set("logging", {"file": temp_log})


def run_gui(config):
    """
    Run the application in GUI mode

    Args:
        config: Configuration object
    """
    logger = get_logger("main")
    logger.info("Starting application in GUI mode")

    # Get UI configuration
    ui_config = config.get("ui_config", {})
    window_size = ui_config.get("window_size", [1200, 800])

    # Create the NAND controller
    simulation_mode = config.get("simulation", {}).get("enabled", False)
    nand_controller = NANDController(config, simulation_mode=simulation_mode)
    logger.info("NAND controller created")

    # Create application and main window
    app = QApplication(sys.argv)

    # Apply theme if specified
    theme = ui_config.get("theme", "light")
    if theme == "dark":
        try:
            import qdarkstyle

            app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        except ImportError:
            logger.warning("qdarkstyle not installed. Dark theme not applied.")

    # Create and show the main window
    main_window = MainWindow(nand_controller)
    logger.info("Main window created")

    # Set window size from configuration
    if isinstance(window_size, list) and len(window_size) >= 2:
        main_window.resize(window_size[0], window_size[1])

    main_window.show()
    logger.info("Main window shown")

    # Run the application event loop
    return app.exec_()


def run_cli(config):
    """
    Run the application in command-line mode

    Args:
        config: Configuration object
    """
    logger = get_logger("main")
    logger.info("Starting application in command-line mode")

    # Create the NAND controller
    simulation_mode = config.get("simulation", {}).get("enabled", False)
    nand_controller = NANDController(config, simulation_mode=simulation_mode)
    logger.info("NAND controller created")

    # Initialize the NAND controller
    try:
        nand_controller.initialize()
        logger.info("NAND controller initialized")

        # Display basic system information
        print("3D NAND Flash Storage Optimization Tool")
        print("======================================")
        print(f"Firmware Version: {nand_controller.firmware_config.get('version', 'Unknown')}")
        print(f"Page Size: {nand_controller.page_size} bytes")
        print(f"Block Size: {nand_controller.block_size} pages")
        print(f"Number of Blocks: {nand_controller.num_blocks}")

        # Get device info
        device_info = nand_controller.get_device_info()

        # Extract some basic statistics if available
        if "statistics" in device_info:
            stats = device_info["statistics"]
            if "bad_blocks" in stats:
                bb = stats["bad_blocks"]
                print(f"Bad Blocks: {bb.get('count', 0)} ({bb.get('percentage', 0):.2f}%)")

            if "wear_leveling" in stats:
                wl = stats["wear_leveling"]
                print(
                    f"Erase Counts: Min={wl.get('min_erase_count', 0)}, " + f"Max={wl.get('max_erase_count', 0)}, " + f"Avg={wl.get('avg_erase_count', 0):.2f}"
                )

        # Display available commands
        print("\nAvailable Commands:")
        print("  read <block> <page> - Read a page")
        print("  write <block> <page> <data> - Write data to a page")
        print("  erase <block> - Erase a block")
        print("  info - Show device information")
        print("  stats - Show statistics")
        print("  exit - Exit the application")

        # Simple command loop
        while True:
            try:
                command = input("\nCommand> ").strip()

                if command == "":
                    continue

                parts = command.split()

                if parts[0] == "exit":
                    break

                elif parts[0] == "read":
                    if len(parts) < 3:
                        print("Usage: read <block> <page>")
                        continue

                    block = int(parts[1])
                    page = int(parts[2])

                    try:
                        data = nand_controller.read_page(block, page)
                        print(f"Data: {data[:50]}{'...' if len(data) > 50 else ''}")
                    except Exception as e:
                        print(f"Error: {str(e)}")

                elif parts[0] == "write":
                    if len(parts) < 4:
                        print("Usage: write <block> <page> <data>")
                        continue

                    block = int(parts[1])
                    page = int(parts[2])
                    data = " ".join(parts[3:]).encode("utf-8")

                    try:
                        nand_controller.write_page(block, page, data)
                        print("Write successful")
                    except Exception as e:
                        print(f"Error: {str(e)}")

                elif parts[0] == "erase":
                    if len(parts) < 2:
                        print("Usage: erase <block>")
                        continue

                    block = int(parts[1])

                    try:
                        nand_controller.erase_block(block)
                        print("Erase successful")
                    except Exception as e:
                        print(f"Error: {str(e)}")

                elif parts[0] == "info":
                    device_info = nand_controller.get_device_info()
                    print("\nDevice Information:")
                    print(yaml.dump(device_info, default_flow_style=False))

                elif parts[0] == "stats":
                    device_info = nand_controller.get_device_info()
                    stats = device_info.get("statistics", {})
                    print("\nDevice Statistics:")
                    print(yaml.dump(stats, default_flow_style=False))

                else:
                    print(f"Unknown command: {parts[0]}")

            except KeyboardInterrupt:
                print("\nExiting...")
                break

            except Exception as e:
                print(f"Error: {str(e)}")

        # Shutdown the NAND controller
        nand_controller.shutdown()
        logger.info("NAND controller shut down")

    except Exception as e:
        logger.exception(f"Failed to initialize NAND controller: {str(e)}")
        print(f"Error: {str(e)}")
        return 1

    return 0


def check_resource_files():
    """Check critical resource files and create them if missing"""
    # Create resources directory structure if it doesn't exist
    dirs = [
        os.path.join("resources"),
        os.path.join("resources", "config"),
        os.path.join("resources", "images"),
        os.path.join("logs"),
    ]

    for directory in dirs:
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
                print(f"Created directory: {directory}")
            except Exception as e:
                print(f"Warning: Unable to create directory {directory}: {e}")

    # Template file
    template_path = os.path.join("resources", "config", "template.yaml")
    if not os.path.exists(template_path):
        try:
            template_content = """---
firmware_version: "{{ firmware_version }}"
nand_config:
  page_size: {{ nand_config.page_size }}
  block_size: {{ nand_config.block_size }}
  num_blocks: {{ nand_config.num_blocks }}
  oob_size: {{ nand_config.oob_size }}
ecc_config:
  algorithm: "{{ ecc_config.algorithm }}"
  strength: {{ ecc_config.strength }}
bbm_config:
  max_bad_blocks: {{ bbm_config.max_bad_blocks }}
wl_config:
  wear_leveling_threshold: {{ wl_config.wear_leveling_threshold }}
"""
            with open(template_path, "w") as f:
                f.write(template_content)
            print(f"Created template file: {template_path}")
        except Exception as e:
            print(f"Warning: Unable to create template file {template_path}: {e}")

    # Default config file
    config_path = os.path.join("resources", "config", "config.yaml")
    if not os.path.exists(config_path):
        try:
            config_content = """# NAND Flash Configuration
nand_config:
  page_size: 4096
  block_size: 256  # pages per block
  num_blocks: 1024
  oob_size: 128
  num_planes: 1

# Optimization Configuration
optimization_config:
  error_correction:
    algorithm: "bch"
    bch_params:
      m: 8
      t: 4
    strength: 4  # Error correction strength (number of correctable bits)
  compression:
    algorithm: "lz4"
    level: 3
  caching:
    capacity: 1024
    policy: "lru"
  parallelism:
    max_workers: 4

# Firmware Configuration
firmware_config:
  version: "1.0.0"
  read_retry: true
  data_scrambling: false

bbm_config:
  max_bad_blocks: 100

wl_config:
  wear_leveling_threshold: 1000

# Logging Configuration
logging:
  level: "INFO"
  file: "logs/nand_optimization.log"
  max_size: 10485760
  backup_count: 5

# User Interface Configuration
ui_config:
  theme: "light"
  font_size: 12
  window_size: [1200, 800]

# Simulation Configuration
simulation:
  enabled: true
  error_rate: 0.0001
  initial_bad_block_rate: 0.002
"""
            with open(config_path, "w") as f:
                f.write(config_content)
            print(f"Created config file: {config_path}")
        except Exception as e:
            print(f"Warning: Unable to create config file {config_path}: {e}")


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="3D NAND Flash Storage Optimization Tool")
    parser.add_argument("--gui", action="store_true", help="Run the tool with graphical user interface")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--check-resources", action="store_true", help="Check and create required resource files")
    args = parser.parse_args()

    try:
        # Check and create resource files if needed
        if args.check_resources:
            check_resource_files()

        # Set up configuration
        config = setup_config(args.config)

        # Set up logging directory
        setup_logging_directory(config)

        # Set up logger
        logger = setup_logger("main", config)
        logger.info("Application started")

        # Run in GUI or CLI mode
        if args.gui:
            ret = run_gui(config)
        else:
            ret = run_cli(config)

        # Exit with the return code
        sys.exit(ret)

    except Exception as e:
        # If logger is not set up yet, print to console
        try:
            logger.exception(f"An unhandled error occurred: {str(e)}")
        except:
            print(f"Fatal error: {str(e)}", file=sys.stderr)

        sys.exit(1)


if __name__ == "__main__":
    main()
