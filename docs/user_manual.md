# User Manual

Welcome to the 3D NAND Optimization Tool! This user manual provides a comprehensive guide on how to install, configure, and use the tool effectively.

## Table of Contents
1. [Installation](#installation)
2. [Configuration](#configuration)
   - [config.yaml](#configyaml)
   - [template.yaml](#templateyaml)
3. [Usage](#usage)
   - [Graphical User Interface (GUI)](#graphical-user-interface-gui)
   - [Command-Line Interface (CLI)](#command-line-interface-cli)
4. [Optimization Techniques](#optimization-techniques)
   - [NAND Defect Handling](#nand-defect-handling)
   - [Performance Optimization](#performance-optimization)
   - [Firmware Integration](#firmware-integration)
   - [NAND Characterization](#nand-characterization)
5. [Troubleshooting](#troubleshooting)
6. [FAQ](#faq)

## Installation

1. Ensure that you have Python 3.9 or above installed on your system.
2. Clone the repository:
   ```
   git clone https://github.com/muditbhargava66/3D-NAND-Flash-Storage-Optimization-Tool.git
   ```
3. Navigate to the project directory:
   ```
   cd 3d-nand-optimization-tool
   ```
4. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Configuration

The 3D NAND Optimization Tool relies on two configuration files: `config.yaml` and `template.yaml`. These files allow you to customize various aspects of the tool's behavior and specify the desired optimization settings.

### config.yaml

The `config.yaml` file contains the main configuration settings for the tool. It is located in the `resources/config/` directory. The file is divided into several sections, each controlling a specific aspect of the tool:

#### NAND Configuration
```yaml
nand_config:
  page_size: 4096   # Page size in bytes
  block_size: 256   # pages per block
  num_blocks: 1024
  oob_size: 128
  num_planes: 1
```

#### Optimization Configuration
```yaml
optimization_config:
  error_correction:
    algorithm: "bch"  # Options: "bch", "ldpc", "none"
    bch_params:
      m: 8            # Galois Field parameter (3-16)
      t: 4            # Error correction capability
    strength: 4       # Error correction strength parameter for template
  compression:
    algorithm: "lz4"  # Options: "lz4", "zstd"
    level: 3          # Compression level (1-9)
    enabled: true     # Enable/disable compression
  caching:
    capacity: 1024    # Number of entries to cache
    policy: "lru"     # Options: "lru", "lfu", "fifo", "ttl"
    enabled: true     # Enable/disable caching
  parallelism:
    max_workers: 4    # Maximum number of parallel worker threads
  wear_leveling:
    wear_level_threshold: 1000  # Threshold for wear leveling activation
```

#### Firmware Configuration
```yaml
firmware_config:
  version: "1.0.0"
  read_retry: true
  max_read_retries: 3
  data_scrambling: false
```

#### Bad Block Management Configuration
```yaml
bbm_config:
  max_bad_blocks: 100
```

#### Wear Leveling Configuration
```yaml
wl_config:
  wear_leveling_threshold: 1000
```

#### Logging Configuration
```yaml
logging:
  level: "INFO"       # Options: "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
  file: "logs/nand_optimization.log"
  max_size: 10485760  # 10 MB
  backup_count: 5
```

#### User Interface Configuration
```yaml
ui_config:
  theme: "light"      # Options: "light", "dark"
  font_size: 12
  window_size: [1200, 800]
```

#### Simulation Configuration
```yaml
simulation:
  enabled: true       # Use simulator by default for safety
  error_rate: 0.0001
  initial_bad_block_rate: 0.002
```

To modify the configuration, open the `config.yaml` file in a text editor and adjust the values according to your requirements. Save the file after making the desired changes.

### template.yaml

The `template.yaml` file serves as a template for generating the firmware specification. It is located in the `resources/config/` directory. The file contains placeholders that are replaced with actual values from the `config.yaml` file during the firmware specification generation process.

```yaml
---
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
```

The placeholders in the `template.yaml` file correspond to the configuration settings in the `config.yaml` file. For example, `{{ firmware_version }}` will be replaced with the actual firmware version specified in the `config.yaml` file.

You can customize the `template.yaml` file to match your specific firmware requirements. Modify the file in a text editor, adding or removing placeholders as needed, and save the changes.

## Usage

The 3D NAND Optimization Tool can be used through either a graphical user interface (GUI) or a command-line interface (CLI).

### Graphical User Interface (GUI)

To run the tool with the GUI, use the following command:
```
python src/main.py --gui
```

The GUI window will open, providing an intuitive interface to interact with the tool. The main window consists of:

1. **Menu Bar**: 
   - **File menu**: Options to open files, save data, and exit the application
   - **Settings menu**: Access to configuration settings
   - **Tools menu**: Options to run tests and generate firmware
   - **Help menu**: Access to the About dialog

2. **Dashboard Tab**:
   - **NAND Status**: Displays device information, health indicators, and initialization status
   - **Performance Statistics**: Shows operation counts, performance metrics, and wear leveling graph
   - **Quick Actions**: Provides buttons for common operations
   - **Progress Bar**: Shows the progress of ongoing operations

3. **Operations Tab**:
   - **Read Operations**: Interface for reading pages from specific blocks
   - **Write Operations**: Interface for writing data to pages and erasing blocks
   - **Batch Operations**: Interface for loading and running batch operation files

4. **Monitoring Tab**:
   - **Block Health**: Table showing the status and wear level of blocks
   - **Performance Monitoring**: Graphs displaying performance metrics over time

5. **Results Tab**:
   - Displays optimization results and test outcomes
   - Provides visualization options for result data

### Command-Line Interface (CLI)

To run the tool in CLI mode, use the following command:
```
python src/main.py
```

The tool will execute in command-line mode with an interactive prompt. Available commands include:

- `read <block> <page>`: Read a page from a specific block
- `write <block> <page> <data>`: Write data to a specific page in a block
- `erase <block>`: Erase a specific block
- `info`: Display device information
- `stats`: Display performance statistics
- `exit`: Exit the application

For all commands, the tool will provide feedback on the operation's success or failure, as well as any relevant data or error messages.

Additional command-line options:

- `--config <file>`: Specify a custom configuration file
- `--check-resources`: Check and create required resource files if missing

## Optimization Techniques

The 3D NAND Optimization Tool employs various optimization techniques to enhance the performance, reliability, and efficiency of NAND flash storage systems.

### NAND Defect Handling

#### Error Correction
The tool implements advanced error correction algorithms to detect and correct bit errors in NAND flash pages:

- **BCH (Bose-Chaudhuri-Hocquenghem)**:
  - Powerful algebraic error correction code especially effective for random bit errors
  - Configurable parameters: `m` (Galois Field size) and `t` (error correction capability)
  - Complete implementation with Galois Field arithmetic, generator polynomial calculation, and error location algorithms

- **LDPC (Low-Density Parity-Check)**:
  - High-performance error correction code approaching Shannon limit error-correcting capability
  - Progressive Edge-Growth (PEG) algorithm for optimized parity-check matrices
  - Belief propagation algorithm for soft-decision decoding
  - Configurable parameters for different code rates and error correction capabilities

#### Bad Block Management
The tool maintains a bad block table and implements strategies for handling blocks that have been marked as bad:

- Records and tracks factory-marked bad blocks and runtime-detected bad blocks
- Provides methods to mark blocks as bad and check if a block is bad
- Implements next-good-block finding algorithms and block replacement strategies
- Stores the bad block table in a reserved area of the NAND flash for persistence

#### Wear Leveling
The tool implements wear leveling algorithms to evenly distribute write and erase operations:

- Tracks the erase count and wear level of each block
- Dynamic block remapping based on wear thresholds
- Statistical wear analysis for optimization decisions
- Reserved blocks for wear leveling operations

### Performance Optimization

#### Data Compression
The tool applies data compression to reduce the amount of data written to the NAND flash:

- **LZ4**: Fast compression algorithm with good compression ratio, ideal for storage applications
- **Zstandard (zstd)**: Higher compression ratio with reasonable speed, suitable for archival data
- Configurable compression levels to balance speed vs. compression ratio
- Adaptive compression based on data patterns and achieved ratios

#### Advanced Caching
The tool implements a sophisticated caching mechanism with multiple eviction policies:

- **LRU (Least Recently Used)**: Evicts items that haven't been accessed recently
- **LFU (Least Frequently Used)**: Evicts items that are accessed least often
- **FIFO (First In First Out)**: Simple queue-based eviction
- **TTL (Time To Live)**: Automatic expiration of stale data
- Thread-safe operations for concurrent access
- Detailed cache statistics and monitoring

#### Parallel Access
The tool utilizes parallel access techniques to optimize read and write operations:

- Thread pool-based execution for I/O operations
- Concurrent operation handling for multi-plane NAND devices
- Task submission and management interface
- Automatic resource management and clean shutdown

### Firmware Integration

#### Firmware Specification Generation
The tool generates firmware specifications based on the current configuration:

- Uses the `template.yaml` file as a template for the firmware specification
- Replaces placeholders with actual values from the `config.yaml` file
- Supports customization of firmware parameters (version, NAND configuration, etc.)
- Produces a complete YAML-based firmware specification file

#### Firmware Specification Validation
The tool provides comprehensive validation of firmware specifications:

- Schema validation for structure, required fields, and data types
- Semantic validation for format rules and logical constraints
- Cross-field validation for parameter compatibility
- Detailed error reporting with specific validation failures

#### Test Benches
The tool includes a framework for executing test benches to validate firmware functionality:

- Utilizes the `test_cases.yaml` file to define test cases
- Executes the firmware with the provided test cases
- Compares actual output with expected output
- Reports discrepancies or failures

### NAND Characterization

#### Data Collection
The tool collects data from the NAND flash device to characterize its behavior:

- Gathers page data, block metadata, and error correction information
- Samples blocks and pages across the device
- Records erase counts, bad block status, and other metrics
- Stores collected data in CSV format for analysis

#### Data Analysis
The tool analyzes collected data to extract insights about the NAND flash:

- Calculates statistical measures of erase count distribution
- Analyzes bad block trends and correlations with erase counts
- Identifies patterns and anomalies in the data
- Provides metrics for performance and reliability assessment

#### Data Visualization
The tool generates visualizations to help interpret the analyzed data:

- Creates erase count distribution histograms
- Plots bad block trend analysis
- Visualizes wear leveling effectiveness
- Exports visualizations as PNG files for documentation and reporting

## Troubleshooting

### Common Issues and Solutions

#### Initialization Failures
- **Issue**: The NAND controller fails to initialize.
- **Solution**: 
  - Check that the configuration file exists and has valid parameters
  - Verify that all required resources are available in the `resources` directory
  - Run the tool with the `--check-resources` flag to create missing resource files
  - Check the log file for specific error messages

#### Read/Write Errors
- **Issue**: Read or write operations fail with error messages.
- **Solution**:
  - Check if the block is marked as bad using the `is_bad_block` method
  - Ensure the block has been erased before writing to it
  - Verify that the page number is within the valid range for the block
  - Check if the data size exceeds the page size

#### Performance Issues
- **Issue**: The tool is running slower than expected.
- **Solution**:
  - Adjust the compression level in the configuration
  - Increase the cache capacity for frequently accessed data
  - Optimize the number of parallel workers based on your system's capabilities
  - Disable features that are not needed for your specific use case

#### GUI Not Displaying Correctly
- **Issue**: The GUI elements are not displaying correctly or are not responsive.
- **Solution**:
  - Ensure all dependencies are installed, including PyQt5
  - Try switching to a different theme in the settings
  - Check if the window size settings are appropriate for your display
  - Restart the application with the `--gui` flag

### Error Messages and Their Meanings

#### "NAND hardware not initialized"
- **Meaning**: The NAND controller has not been initialized yet.
- **Action**: Call the `initialize()` method on the NAND controller before performing operations.

#### "Block X is marked as bad"
- **Meaning**: The specified block is marked as bad in the bad block table.
- **Action**: Use a different block or get the next good block using `get_next_good_block()`.

#### "Program operation failed for block X, page Y"
- **Meaning**: Writing to the specified page failed, possibly due to a worn-out block.
- **Action**: Mark the block as bad and use a different block for future operations.

#### "Erase operation failed for block X"
- **Meaning**: Erasing the specified block failed, possibly due to a hardware issue.
- **Action**: Mark the block as bad and use a different block for future operations.

#### "Too many errors to correct"
- **Meaning**: The number of bit errors exceeds the error correction capability.
- **Action**: Try reading with read retry if enabled, or use a more powerful error correction algorithm.

## FAQ

1. **Q: Can I use this tool with real NAND flash hardware?**  
   **A:** Yes, the tool supports both simulation mode and real hardware mode. For real hardware, ensure that the hardware interface is properly configured and connected.

2. **Q: Which error correction algorithm should I use?**  
   **A:** BCH is suitable for most applications with moderate error correction needs. LDPC provides stronger error correction capabilities but requires more computational resources.

3. **Q: How does the tool handle bad blocks?**  
   **A:** The tool maintains a bad block table to track blocks that are marked as bad. When a bad block is encountered, the tool automatically finds a replacement block using the bad block management module.

4. **Q: Can I customize the firmware specification template?**  
   **A:** Yes, you can customize the `template.yaml` file to include additional parameters or modify existing ones based on your firmware requirements.

5. **Q: How do I interpret the NAND characterization results?**  
   **A:** The characterization results provide insights into the wear distribution and bad block trends of the NAND flash. Higher erase counts indicate more worn blocks, and a positive correlation between erase counts and bad blocks suggests wear-induced failures.

6. **Q: Is there a way to speed up the optimization process?**  
   **A:** Yes, you can adjust several settings to improve performance:
   - Increase the number of parallel workers
   - Use a faster compression algorithm (LZ4 instead of Zstandard)
   - Adjust the cache capacity and policy based on your access patterns
   - Disable features that are not essential for your use case

7. **Q: How can I contribute to the project?**  
   **A:** Contributions are welcome! Please refer to the README.md file in the project repository for guidelines on how to contribute, report issues, and submit pull requests.

8. **Q: Does the tool work with different types of NAND flash?**  
   **A:** Yes, the tool is designed to work with various types of NAND flash, including SLC, MLC, TLC, and QLC. You can configure the parameters in the `config.yaml` file to match your specific NAND flash characteristics.

For more detailed information and API references, please refer to the `api_reference.md` file.