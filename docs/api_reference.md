# API Reference

This document provides a comprehensive reference for the API endpoints and functions exposed by the 3D NAND Optimization Tool.

## Table of Contents
1. [NAND Controller](#nand-controller)
   - [read_page](#read_page)
   - [write_page](#write_page)
   - [erase_block](#erase_block)
   - [mark_bad_block](#mark_bad_block)
   - [is_bad_block](#is_bad_block)
   - [get_next_good_block](#get_next_good_block)
   - [get_least_worn_block](#get_least_worn_block)
   - [generate_firmware_spec](#generate_firmware_spec)
   - [read_metadata](#read_metadata)
   - [write_metadata](#write_metadata)
   - [execute_parallel_operations](#execute_parallel_operations)
   - [get_device_info](#get_device_info)
   - [load_data](#load_data)
   - [save_data](#save_data)
   - [batch_operations](#batch_operations)
2. [NAND Defect Handling](#nand-defect-handling)
   - [ECCHandler](#ecchandler)
   - [BadBlockManager](#badblockmanager)
   - [WearLevelingEngine](#wearlevelingengine)
   - [BCH](#bch)
   - [LDPC](#ldpc)
3. [Performance Optimization](#performance-optimization)
   - [DataCompressor](#datacompressor)
   - [CachingSystem](#cachingsystem)
   - [ParallelAccessManager](#parallelaccessmanager)
4. [Firmware Integration](#firmware-integration)
   - [FirmwareSpecGenerator](#firmwarespecgenerator)
   - [FirmwareSpecValidator](#firmwarespecvalidator)
   - [TestBenchRunner](#testbenchrunner)
   - [ValidationScriptExecutor](#validationscriptexecutor)
5. [NAND Characterization](#nand-characterization)
   - [DataCollector](#datacollector)
   - [DataAnalyzer](#dataanalyzer)
   - [DataVisualizer](#datavisualizer)
6. [Utilities](#utilities)
   - [Config](#config)
   - [NANDInterface](#nandinterface)
   - [NANDSimulator](#nandsimulator)

## NAND Controller

The `NANDController` class is the central component of the 3D NAND Optimization Tool. It orchestrates the interaction between different modules and provides a unified API for NAND flash operations.

### Constructor
```python
def __init__(self, config, interface=None, simulation_mode=False):
    """
    Initialize the NAND controller with the provided configuration.
    
    Args:
        config: Configuration object with NAND parameters
        interface: Optional NANDInterface instance (for testing with mocks)
        simulation_mode: Whether to use simulator instead of hardware interface
    """
```

### initialize
```python
def initialize(self):
    """
    Initialize the NAND controller and its components.
    
    Raises:
        RuntimeError: If initialization fails
    """
```

### shutdown
```python
def shutdown(self):
    """
    Shut down the NAND controller and release resources.
    
    Raises:
        Exception: If shutdown fails
    """
```

### read_page
```python
def read_page(self, block, page):
    """
    Read a page from the NAND flash with all optimizations applied.
    
    Args:
        block (int): The block number
        page (int): The page number within the block
        
    Returns:
        bytes: The data read from the page
        
    Raises:
        IOError: If the block is marked as bad
        ValueError: If block or page is invalid
        RuntimeError: If the NAND controller is not initialized
    """
```

### write_page
```python
def write_page(self, block, page, data):
    """
    Write data to a page in the NAND flash with all optimizations applied.
    
    Args:
        block (int): The block number
        page (int): The page number within the block
        data (bytes): The data to be written
        
    Raises:
        IOError: If the block is marked as bad
        ValueError: If block, page, or data size is invalid
        RuntimeError: If the NAND controller is not initialized
    """
```

### erase_block
```python
def erase_block(self, block):
    """
    Erase a block in the NAND flash.
    
    Args:
        block (int): The block number
        
    Raises:
        IOError: If the block is marked as bad
        ValueError: If block is invalid
        RuntimeError: If the NAND controller is not initialized
    """
```

### mark_bad_block
```python
def mark_bad_block(self, block):
    """
    Mark a block as bad in the bad block table.
    
    Args:
        block (int): The block number
        
    Raises:
        ValueError: If block is invalid
    """
```

### is_bad_block
```python
def is_bad_block(self, block):
    """
    Check if a block is marked as bad.
    
    Args:
        block (int): The block number
        
    Returns:
        bool: True if the block is bad, False otherwise
        
    Raises:
        ValueError: If block is invalid
    """
```

### get_next_good_block
```python
def get_next_good_block(self, block):
    """
    Find the next good block starting from the given block.
    
    Args:
        block (int): The starting block number
        
    Returns:
        int: The next good block number
        
    Raises:
        ValueError: If block is invalid
        RuntimeError: If no good blocks are available
    """
```

### get_least_worn_block
```python
def get_least_worn_block(self):
    """
    Find the block with the least wear level.
    
    Returns:
        int: The block number with the least wear level
    """
```

### generate_firmware_spec
```python
def generate_firmware_spec(self):
    """
    Generate the firmware specification based on the current configuration.
    
    Returns:
        str: The generated firmware specification
    """
```

### read_metadata
```python
def read_metadata(self, block):
    """
    Read metadata from a block.
    
    Args:
        block (int): The block number
        
    Returns:
        dict: The metadata read from the block or None if no valid metadata
        
    Raises:
        ValueError: If block is invalid
    """
```

### write_metadata
```python
def write_metadata(self, block, metadata):
    """
    Write metadata to a block.
    
    Args:
        block (int): The block number
        metadata (dict): The metadata to write
        
    Raises:
        ValueError: If block is invalid or metadata is too large
        IOError: If the block is marked as bad
    """
```

### execute_parallel_operations
```python
def execute_parallel_operations(self, operations):
    """
    Execute multiple NAND operations in parallel.
    
    Args:
        operations (list): List of operation dictionaries, each containing:
            - type (str): Operation type ('read', 'write', 'erase')
            - block (int): Block number
            - page (int, optional): Page number (for read/write)
            - data (bytes, optional): Data to write (for write)
            
    Returns:
        list: Results of the operations
    """
```

### get_device_info
```python
def get_device_info(self):
    """
    Get information about the NAND device.
    
    Returns:
        dict: Device information including configuration, firmware details,
             status, and statistics
    """
```

### load_data
```python
def load_data(self, file_path):
    """
    Load data from a file to the NAND flash.
    
    Args:
        file_path (str): Path to the file to load
        
    Raises:
        ValueError: If file is too large for available blocks
        IOError: If file cannot be read
        RuntimeError: If NAND controller is not initialized
    """
```

### save_data
```python
def save_data(self, file_path, start_block=0, end_block=None, metadata_block=None):
    """
    Save data from the NAND flash to a file.
    
    Args:
        file_path (str): Path to save the file
        start_block (int, optional): First block to read (default: 0)
        end_block (int, optional): Last block to read (default: all user blocks)
        metadata_block (int, optional): Block containing file metadata
        
    Raises:
        IOError: If file cannot be written
        RuntimeError: If NAND controller is not initialized
    """
```

### batch_operations
```python
def batch_operations(self):
    """
    Context manager for batching operations.
    
    Example:
        with nand_controller.batch_operations():
            nand_controller.write_page(0, 0, data1)
            nand_controller.write_page(0, 1, data2)
            
    Raises:
        Exception: If any operation in the batch fails
    """
```

### translate_address
```python
def translate_address(self, logical_block):
    """
    Translate logical block address to physical block address.
    
    Args:
        logical_block (int): Logical block number
        
    Returns:
        int: Physical block number
        
    Raises:
        ValueError: If logical block exceeds available user blocks
    """
```

## NAND Defect Handling

### ECCHandler

The `ECCHandler` class provides error correction capabilities for NAND flash data.

#### Constructor
```python
def __init__(self, config):
    """
    Initialize the ECC handler with the specified configuration.
    
    Args:
        config: Configuration object containing ECC parameters
    """
```

#### encode
```python
def encode(self, data):
    """
    Encode data using the configured ECC algorithm.
    
    Args:
        data: Data to encode (bytes or bytearray)
        
    Returns:
        bytes or numpy.ndarray: Encoded data with ECC
        
    Raises:
        RuntimeError: If encoding fails
    """
```

#### decode
```python
def decode(self, data):
    """
    Decode data using the configured ECC algorithm and correct errors.
    
    Args:
        data: Data to decode (bytes, bytearray, or numpy.ndarray)
        
    Returns:
        tuple: (decoded_data, num_errors) - Decoded data and number of corrected errors
        
    Raises:
        ValueError: If data contains uncorrectable errors
    """
```

#### is_correctable
```python
def is_correctable(self, data):
    """
    Check if the data can be corrected with the configured ECC.
    
    Args:
        data: Data to check (with ECC)
        
    Returns:
        bool: True if data can be corrected, False otherwise
    """
```

### BadBlockManager

The `BadBlockManager` class handles bad blocks in the NAND flash.

#### Constructor
```python
def __init__(self, config):
    """
    Initialize the bad block manager with the specified configuration.
    
    Args:
        config: Configuration object containing bad block management parameters
    """
```

#### mark_bad_block
```python
def mark_bad_block(self, block_address):
    """
    Mark a block as bad in the bad block table.
    
    Args:
        block_address (int): Block number to mark as bad
        
    Raises:
        IndexError: If block address is out of range
    """
```

#### is_bad_block
```python
def is_bad_block(self, block_address):
    """
    Check if a block is marked as bad.
    
    Args:
        block_address (int): Block number to check
        
    Returns:
        bool: True if the block is bad, False otherwise
        
    Raises:
        IndexError: If block address is out of range
    """
```

#### get_next_good_block
```python
def get_next_good_block(self, block_address):
    """
    Find the next good block starting from the given block address.
    
    Args:
        block_address (int): Starting block address
        
    Returns:
        int: Next good block address
        
    Raises:
        IndexError: If block_address is out of range
        RuntimeError: If no good blocks are available
    """
```

### WearLevelingEngine

The `WearLevelingEngine` class manages wear leveling for NAND flash blocks.

#### Constructor
```python
def __init__(self, config):
    """
    Initialize the wear leveling engine with the specified configuration.
    
    Args:
        config: Configuration object containing wear leveling parameters
    """
```

#### update_wear_level
```python
def update_wear_level(self, block_address):
    """
    Update the wear level of a block.
    
    Args:
        block_address (int): Block number
        
    Raises:
        IndexError: If block address is out of range
    """
```

#### should_perform_wear_leveling
```python
def should_perform_wear_leveling(self):
    """
    Check if wear leveling should be performed.
    
    Returns:
        bool: True if wear leveling should be performed, False otherwise
    """
```

#### get_least_worn_block
```python
def get_least_worn_block(self):
    """
    Find the block with the least wear level.
    
    Returns:
        int: Block number with the least wear level
    """
```

#### get_most_worn_block
```python
def get_most_worn_block(self):
    """
    Find the block with the most wear level.
    
    Returns:
        int: Block number with the most wear level
    """
```

### BCH

The `BCH` class implements the BCH error correction code.

#### Constructor
```python
def __init__(self, m, t):
    """
    Initialize BCH encoder/decoder with given parameters.
    
    Args:
        m (int): Defines the Galois Field GF(2^m) (3-16)
        t (int): Maximum number of correctable errors
        
    Raises:
        ValueError: If parameters are invalid
    """
```

#### encode
```python
def encode(self, data):
    """
    Encode data using BCH code.
    
    Args:
        data (bytes or bytearray): Input data to encode
        
    Returns:
        bytes: ECC parity bits
        
    Raises:
        TypeError: If input data is not bytes or bytearray
        ValueError: If input data exceeds maximum size
    """
```

#### decode
```python
def decode(self, encoded_data):
    """
    Decode and correct errors in BCH encoded data.
    
    Args:
        encoded_data (bytes or bytearray): Data + ECC bytes to decode
        
    Returns:
        tuple: (corrected_data, num_errors) - Corrected data and number of errors found
        
    Raises:
        TypeError: If input data is not bytes or bytearray
        ValueError: If input data is too small or has uncorrectable errors
    """
```

### LDPC

The LDPC module provides functions for Low-Density Parity-Check code.

#### make_ldpc
```python
def make_ldpc(n, d_v, d_c, systematic=True, sparse=True):
    """
    Generate LDPC code matrices H (parity-check matrix) and G (generator matrix).
    
    Args:
        n (int): Codeword length
        d_v (int): Variable node degree (number of checks per variable)
        d_c (int): Check node degree (number of variables per check)
        systematic (bool): Whether to create systematic code
        sparse (bool): Whether to return sparse matrices
        
    Returns:
        tuple: (H, G) - parity-check matrix and generator matrix
        
    Raises:
        ValueError: If parameters are invalid or incompatible
    """
```

#### encode
```python
def encode(G, data):
    """
    Encode data using LDPC code.
    
    Args:
        G: Generator matrix (sparse or dense)
        data: Data bits to encode (bytes, array, or binary sequence)
        
    Returns:
        numpy.ndarray: Encoded codeword
        
    Raises:
        ValueError: If input data exceeds capacity
    """
```

#### decode
```python
def decode(H, received_codeword, max_iterations=50, early_termination=True):
    """
    Decode LDPC codeword using belief propagation algorithm.
    
    Args:
        H: Parity-check matrix (sparse or dense)
        received_codeword: Received codeword bits
        max_iterations (int): Maximum number of belief propagation iterations
        early_termination (bool): Whether to stop when valid codeword is found
        
    Returns:
        tuple: (decoded_data, success) - decoded data bits and success flag
    """
```

## Performance Optimization

### DataCompressor

The `DataCompressor` class provides data compression capabilities.

#### Constructor
```python
def __init__(self, algorithm='lz4', level=3):
    """
    Initialize the data compressor.
    
    Args:
        algorithm (str): Compression algorithm ('lz4' or 'zstd')
        level (int): Compression level (1-9)
    """
```

#### compress
```python
def compress(self, data):
    """
    Compresses the input data using the specified algorithm.
    
    Args:
        data (bytes): The data to compress
        
    Returns:
        bytes: The compressed data
        
    Raises:
        ValueError: If compression algorithm is unsupported
    """
```

#### decompress
```python
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
```

### CachingSystem

The `CachingSystem` class provides caching capabilities with various eviction policies.

#### Constructor
```python
def __init__(self, capacity=1024, policy=EvictionPolicy.LRU, ttl=None, 
             max_size_bytes=None, thread_safe=True, on_evict=None):
    """
    Initialize the caching system.
    
    Args:
        capacity (int): Maximum number of items to store in the cache
        policy (EvictionPolicy): Cache eviction policy 
        ttl (int, optional): Default Time-To-Live in seconds for cache entries
        max_size_bytes (int, optional): Maximum cache size in bytes
        thread_safe (bool): Whether to make operations thread-safe
        on_evict (callable, optional): Callback function called when items are evicted
    """
```

#### get
```python
def get(self, key, default=None):
    """
    Retrieve an item from the cache.
    
    Args:
        key: The cache key
        default: Value to return if key is not found
        
    Returns:
        The cached value or default if not found
    """
```

#### put
```python
def put(self, key, value, ttl=None):
    """
    Add or update an item in the cache.
    
    Args:
        key: The cache key
        value: The value to cache
        ttl (int, optional): Time-To-Live in seconds for this specific entry
    """
```

#### invalidate
```python
def invalidate(self, key):
    """
    Remove an item from the cache.
    
    Args:
        key: The key to remove
        
    Returns:
        The removed value or None if key wasn't in cache
    """
```

#### clear
```python
def clear(self):
    """
    Clear the entire cache.
    """
```

#### get_hit_ratio
```python
def get_hit_ratio(self):
    """
    Calculate the cache hit ratio.
    
    Returns:
        float: The ratio of cache hits to total accesses, or 0 if no accesses
    """
```

#### get_stats
```python
def get_stats(self):
    """
    Get cache statistics.
    
    Returns:
        dict: Dictionary with cache statistics
    """
```

### ParallelAccessManager

The `ParallelAccessManager` class manages parallel execution of tasks.

#### Constructor
```python
def __init__(self, max_workers=4):
    """
    Initialize the parallel access manager.
    
    Args:
        max_workers (int): Maximum number of worker threads
    """
```

#### submit_task
```python
def submit_task(self, task, *args, **kwargs):
    """
    Submit a task for parallel execution.
    
    Args:
        task: The task function to execute
        *args: Positional arguments for the task
        **kwargs: Keyword arguments for the task
        
    Returns:
        concurrent.futures.Future: Future object representing the task
        
    Raises:
        RuntimeError: If the executor has been shut down
    """
```

#### wait_for_tasks
```python
def wait_for_tasks(self, futures):
    """
    Wait for tasks to complete.
    
    Args:
        futures: Collection of Future objects
        
    Returns:
        tuple: Sets of done and not done futures
    """
```

#### shutdown
```python
def shutdown(self):
    """
    Shut down the executor.
    
    This method does not wait for pending tasks to complete.
    """
```

## Firmware Integration

### FirmwareSpecGenerator

The `FirmwareSpecGenerator` class generates firmware specifications.

#### Constructor
```python
def __init__(self, template_file=None, config=None):
    """
    Initialize the firmware specification generator.
    
    Args:
        template_file (str, optional): Path to the template file
        config: Configuration object
    """
```

#### generate_spec
```python
def generate_spec(self, config=None):
    """
    Generates a firmware specification based on the provided configuration.
    
    Args:
        config: Dictionary containing configuration parameters. If None, uses self.config.
        
    Returns:
        str: The generated firmware specification as a YAML string
    """
```

#### save_spec
```python
def save_spec(self, spec, output_file=None):
    """
    Saves the generated specification to a file.
    
    Args:
        spec (str): The specification string to save
        output_file (str, optional): The file path to save to. Defaults to self.output_file.
    """
```

### FirmwareSpecValidator

The `FirmwareSpecValidator` class validates firmware specifications.

#### Constructor
```python
def __init__(self, logger=None):
    """
    Initialize the validator.
    
    Args:
        logger: Optional logger instance to use for logging validation issues
    """
```

#### validate
```python
def validate(self, firmware_spec):
    """
    Validate the firmware specification against schema and rules.
    
    Args:
        firmware_spec: Dictionary or YAML string of the firmware specification
        
    Returns:
        bool: True if specification is valid, False otherwise
    """
```

#### get_errors
```python
def get_errors(self):
    """
    Get all validation errors.
    
    Returns:
        list: List of validation error messages
    """
```

### TestBenchRunner

The `TestBenchRunner` class executes test benches for firmware validation.

#### Constructor
```python
def __init__(self, test_cases_file=None):
    """
    Initialize the test bench runner.
    
    Args:
        test_cases_file (str, optional): Path to the test cases file
    """
```

#### run_tests
```python
def run_tests(self):
    """
    Run the test cases.
    
    Returns:
        unittest.TestResult: Result of the test execution
    """
```

### ValidationScriptExecutor

The `ValidationScriptExecutor` class executes validation scripts.

#### Constructor
```python
def __init__(self, script_dir):
    """
    Initialize the validation script executor.
    
    Args:
        script_dir (str): Directory containing validation scripts
    """
```

#### execute_script
```python
def execute_script(self, script_name, args):
    """
    Execute a validation script.
    
    Args:
        script_name (str): Name of the script to execute
        args (list): Arguments to pass to the script
        
    Returns:
        str: Output of the script
        
    Raises:
        subprocess.CalledProcessError: If the script execution fails
    """
```

## NAND Characterization

### DataCollector

The `DataCollector` class collects data from NAND flash devices.

#### Constructor
```python
def __init__(self, nand_interface):
    """
    Initialize the data collector.
    
    Args:
        nand_interface: NANDInterface instance to use for data collection
    """
```

#### collect_data
```python
def collect_data(self, num_samples, output_file):
    """
    Collect NAND characterization data.
    
    Args:
        num_samples (int): Number of samples to collect
        output_file (str): Path to the output CSV file
    """
```

### DataAnalyzer

The `DataAnalyzer` class analyzes NAND flash characterization data.

#### Constructor
```python
def __init__(self, data_file):
    """
    Initialize the data analyzer.
    
    Args:
        data_file (str): Path to the CSV data file
    """
```

#### analyze_erase_count_distribution
```python
def analyze_erase_count_distribution(self):
    """
    Analyze erase count distribution.
    
    Returns:
        dict: Statistical measures of the erase count distribution
              - mean: Mean erase count
              - std_dev: Standard deviation
              - min: Minimum erase count
              - max: Maximum erase count
              - quartiles: 25th, 50th, and 75th percentiles
    """
```

#### analyze_bad_block_trend
```python
def analyze_bad_block_trend(self):
    """
    Analyze the correlation between erase counts and bad blocks.
    
    Returns:
        dict: Linear regression results
              - slope: Slope of the trend line
              - intercept: Intercept of the trend line
              - r_value: Correlation coefficient
              - p_value: Statistical significance
              - std_err: Standard error
    """
```

### DataVisualizer

The `DataVisualizer` class creates visualizations of NAND flash data.

#### Constructor
```python
def __init__(self, data_file):
    """
    Initialize the data visualizer.
    
    Args:
        data_file (str): Path to the CSV data file
    """
```

#### plot_erase_count_distribution
```python
def plot_erase_count_distribution(self, output_file):
    """
    Plot erase count distribution histogram.
    
    Args:
        output_file (str): Path to save the plot image
    """
```

#### plot_bad_block_trend
```python
def plot_bad_block_trend(self, output_file):
    """
    Plot bad block trend analysis.
    
    Args:
        output_file (str): Path to save the plot image
    """
```

## Utilities

### Config

The `Config` class manages configuration settings.

#### Constructor
```python
def __init__(self, config):
    """
    Initialize the configuration object.
    
    Args:
        config: Dictionary containing configuration settings
    """
```

#### get
```python
def get(self, key, default=None):
    """
    Get a configuration value.
    
    Args:
        key (str): Configuration key
        default: Default value if key is not found
        
    Returns:
        Configuration value or default
    """
```

#### set
```python
def set(self, key, value):
    """
    Set a configuration value.
    
    Args:
        key (str): Configuration key
        value: Value to set
    """
```

#### save
```python
def save(self, config_file):
    """
    Save configuration to a file.
    
    Args:
        config_file (str): Path to the configuration file
    """
```

### NANDInterface

The `NANDInterface` abstract class defines the interface for NAND flash operations.

#### initialize
```python
def initialize(self):
    """
    Initialize the NAND device for operations.
    
    Raises:
        RuntimeError: If initialization fails
    """
```

#### shutdown
```python
def shutdown(self):
    """
    Shut down the NAND device properly.
    
    Raises:
        RuntimeError: If shutdown fails
    """
```

#### read_page
```python
def read_page(self, block, page):
    """
    Read a page from the NAND device.
    
    Args:
        block (int): Block number
        page (int): Page number within the block
        
    Returns:
        bytes: Raw data read from the page
        
    Raises:
        ValueError: If block or page is invalid
        IOError: If read operation fails
    """
```

#### write_page
```python
def write_page(self, block, page, data):
    """
    Write data to a page in the NAND device.
    
    Args:
        block (int): Block number
        page (int): Page number within the block
        data (bytes): Data to write to the page
        
    Raises:
        ValueError: If block, page, or data size is invalid
        IOError: If write operation fails
    """
```

#### erase_block
```python
def erase_block(self, block):
    """
    Erase a block in the NAND device.
    
    Args:
        block (int): Block number to erase
        
    Raises:
        ValueError: If block is invalid
        IOError: If erase operation fails
    """
```

#### get_status
```python
def get_status(self, block=None, page=None):
    """
    Get status information from the NAND device.
    
    Args:
        block (int, optional): Block number to check
        page (int, optional): Page number to check
        
    Returns:
        dict: Status information
        
    Raises:
        ValueError: If block or page is invalid
    """
```

### NANDSimulator

The `NANDSimulator` class simulates a NAND flash device for testing and development.

#### Constructor
```python
def __init__(self, config):
    """
    Initialize the NAND simulator.
    
    Args:
        config: Configuration object with NAND parameters
    """
```

#### initialize
```python
def initialize(self):
    """
    Initialize the simulated NAND device.
    """
```

#### shutdown
```python
def shutdown(self):
    """
    Shut down the simulated NAND device.
    """
```

#### read_page
```python
def read_page(self, block, page):
    """
    Read a page from the simulated NAND.
    
    Args:
        block (int): Block number
        page (int): Page number within the block
        
    Returns:
        bytes: Raw data read from the page
        
    Raises:
        ValueError: If block or page is invalid
        RuntimeError: If NAND simulator is not initialized
    """
```

#### write_page
```python
def write_page(self, block, page, data):
    """
    Write data to a page in the simulated NAND.
    
    Args:
        block (int): Block number
        page (int): Page number within the block
        data (bytes): Data to write to the page
        
    Raises:
        ValueError: If block, page, or data size is invalid
        RuntimeError: If NAND simulator is not initialized
    """
```

#### erase_block
```python
def erase_block(self, block):
    """
    Erase a block in the simulated NAND.
    
    Args:
        block (int): Block number to erase
        
    Raises:
        ValueError: If block is invalid
        RuntimeError: If NAND simulator is not initialized
    """
```

#### get_status
```python
def get_status(self, block=None, page=None):
    """
    Get status information from the simulated NAND.
    
    Args:
        block (int, optional): Block number to check
        page (int, optional): Page number to check
        
    Returns:
        dict: Status information
        
    Raises:
        ValueError: If block or page is invalid
        RuntimeError: If NAND simulator is not initialized
    """
```

#### execute_sequence
```python
def execute_sequence(self, sequence):
    """
    Execute a sequence of operations for testing.
    
    Args:
        sequence (list): List of operation dictionaries
        
    Returns:
        list: Results of the operations
        
    Raises:
        RuntimeError: If NAND simulator is not initialized
    """
```

#### set_error_rate
```python
def set_error_rate(self, rate):
    """
    Set the error rate for the simulator.
    
    Args:
        rate (float): Error rate (0.0 to 1.0)
        
    Raises:
        ValueError: If rate is outside valid range
    """
```

#### mark_block_bad
```python
def mark_block_bad(self, block):
    """
    Manually mark a block as bad.
    
    Args:
        block (int): Block number to mark as bad
        
    Raises:
        ValueError: If block is invalid
    """
```

This API reference provides detailed information about the available classes, functions, parameters, and return values. It serves as a guide for developers who want to integrate the 3D NAND Optimization Tool into their own applications or extend its functionality.

For examples and usage scenarios, please refer to the User Manual and the inline documentation in the source code.