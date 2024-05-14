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
   - [get_results](#get_results)
   - [load_data](#load_data)
   - [save_data](#save_data)
2. [NAND Defect Handling](#nand-defect-handling)
   - [ECCHandler](#ecchandler)
     - [encode](#encode)
     - [decode](#decode)
   - [BadBlockManager](#badblockmanager)
     - [mark_bad_block](#mark_bad_block-1)
     - [is_bad_block](#is_bad_block-1)
     - [get_next_good_block](#get_next_good_block-1)
   - [WearLevelingEngine](#wearlevelingengine)
     - [update_wear_level](#update_wear_level)
     - [get_least_worn_block](#get_least_worn_block-1)
     - [get_most_worn_block](#get_most_worn_block)
3. [Performance Optimization](#performance-optimization)
   - [DataCompressor](#datacompressor)
     - [compress](#compress)
     - [decompress](#decompress)
   - [CachingSystem](#cachingsystem)
     - [get](#get)
     - [put](#put)
     - [invalidate](#invalidate)
     - [get_hit_ratio](#get_hit_ratio)
   - [ParallelAccessManager](#parallelaccessmanager)
     - [submit_task](#submit_task)
     - [shutdown](#shutdown)
4. [Firmware Integration](#firmware-integration)
   - [FirmwareSpecGenerator](#firmwarespecgenerator)
     - [generate_spec](#generate_spec)
   - [FirmwareSpecValidator](#firmwarespecvalidator)
     - [validate](#validate)
5. [NAND Characterization](#nand-characterization)
   - [DataCollector](#datacollector)
     - [collect_data](#collect_data)
   - [DataAnalyzer](#dataanalyzer)
     - [analyze_erase_count_distribution](#analyze_erase_count_distribution)
     - [analyze_bad_block_trend](#analyze_bad_block_trend)
   - [DataVisualizer](#datavisualizer)
     - [plot_erase_count_distribution](#plot_erase_count_distribution)
     - [plot_bad_block_trend](#plot_bad_block_trend)

## NAND Controller
### read_page
```python
def read_page(block: int, page: int) -> bytes:
    """
    Reads a page from the NAND flash.

    Args:
        block (int): The block number.
        page (int): The page number within the block.

    Returns:
        bytes: The data read from the page.
    """
```

### write_page
```python
def write_page(block: int, page: int, data: bytes) -> None:
    """
    Writes data to a page in the NAND flash.

    Args:
        block (int): The block number.
        page (int): The page number within the block.
        data (bytes): The data to be written.
    """
```

### erase_block
```python
def erase_block(block: int) -> None:
    """
    Erases a block in the NAND flash.

    Args:
        block (int): The block number.
    """
```

### mark_bad_block
```python
def mark_bad_block(block: int) -> None:
    """
    Marks a block as bad in the bad block table.

    Args:
        block (int): The block number.
    """
```

### is_bad_block
```python
def is_bad_block(block: int) -> bool:
    """
    Checks if a block is marked as bad.

    Args:
        block (int): The block number.

    Returns:
        bool: True if the block is bad, False otherwise.
    """
```

### get_next_good_block
```python
def get_next_good_block(block: int) -> int:
    """
    Finds the next good block starting from the given block.

    Args:
        block (int): The starting block number.

    Returns:
        int: The next good block number.
    """
```

### get_least_worn_block
```python
def get_least_worn_block() -> int:
    """
    Finds the block with the least wear level.

    Returns:
        int: The block number with the least wear level.
    """
```

### generate_firmware_spec
```python
def generate_firmware_spec() -> str:
    """
    Generates the firmware specification.

    Returns:
        str: The generated firmware specification.
    """
```

### read_metadata
```python
def read_metadata(block: int) -> int:
    """
    Reads metadata from a block.

    Args:
        block (int): The block number.

    Returns:
        int: The metadata value.
    """
```

### write_metadata
```python
def write_metadata(block: int, metadata: int) -> None:
    """
    Writes metadata to a block.

    Args:
        block (int): The block number.
        metadata (int): The metadata value to be written.
    """
```

### execute_parallel_operations
```python
def execute_parallel_operations(operations: List[Dict]) -> List[Any]:
    """
    Executes NAND operations in parallel.

    Args:
        operations (List[Dict]): A list of NAND operations to be executed in parallel.

    Returns:
        List[Any]: The results of the parallel operations.
    """
```

### get_results
```python
def get_results() -> Dict:
    """
    Retrieves the optimization results.

    Returns:
        Dict: A dictionary containing the optimization results.
    """
```

### load_data
```python
def load_data(file_path: str) -> None:
    """
    Loads data from a file.

    Args:
        file_path (str): The path to the file to be loaded.
    """
```

### save_data
```python
def save_data(file_path: str) -> None:
    """
    Saves data to a file.

    Args:
        file_path (str): The path to the file where the data will be saved.
    """
```

## NAND Defect Handling
### ECCHandler
#### encode
```python
def encode(data: bytes) -> bytes:
    """
    Encodes the input data using the ECC algorithm.

    Args:
        data (bytes): The data to be encoded.

    Returns:
        bytes: The encoded data.
    """
```

#### decode
```python
def decode(data: bytes) -> Tuple[bytes, int]:
    """
    Decodes the input data using the ECC algorithm.

    Args:
        data (bytes): The data to be decoded.

    Returns:
        Tuple[bytes, int]: A tuple containing the decoded data and the number of corrected errors.
    """
```

### BadBlockManager
#### mark_bad_block
```python
def mark_bad_block(block: int) -> None:
    """
    Marks a block as bad in the bad block table.

    Args:
        block (int): The block number.
    """
```

#### is_bad_block
```python
def is_bad_block(block: int) -> bool:
    """
    Checks if a block is marked as bad.

    Args:
        block (int): The block number.

    Returns:
        bool: True if the block is bad, False otherwise.
    """
```

#### get_next_good_block
```python
def get_next_good_block(block: int) -> int:
    """
    Finds the next good block starting from the given block.

    Args:
        block (int): The starting block number.

    Returns:
        int: The next good block number.
    """
```

### WearLevelingEngine
#### update_wear_level
```python
def update_wear_level(block: int) -> None:
    """
    Updates the wear level of a block.

    Args:
        block (int): The block number.
    """
```

#### get_least_worn_block
```python
def get_least_worn_block() -> int:
    """
    Finds the block with the least wear level.

    Returns:
        int: The block number with the least wear level.
    """
```

#### get_most_worn_block
```python
def get_most_worn_block() -> int:
    """
    Finds the block with the most wear level.

    Returns:
        int: The block number with the most wear level.
    """
```

## Performance Optimization
### DataCompressor
#### compress
```python
def compress(data: bytes) -> bytes:
    """
    Compresses the input data using the specified compression algorithm.

    Args:
        data (bytes): The data to be compressed.

    Returns:
        bytes: The compressed data.
    """
```

#### decompress
```python
def decompress(data: bytes) -> bytes:
    """
    Decompresses the input data using the specified compression algorithm.

    Args:
        data (bytes): The compressed data.

    Returns:
        bytes: The decompressed data.
    """
```

### CachingSystem
#### get
```python
def get(key: str) -> Optional[bytes]:
    """
    Retrieves data from the cache.

    Args:
        key (str): The cache key.

    Returns:
        Optional[bytes]: The cached data if found, None otherwise.
    """
```

#### put
```python
def put(key: str, data: bytes) -> None:
    """
    Puts data into the cache.

    Args:
        key (str): The cache key.
        data (bytes): The data to be cached.
    """
```

#### invalidate
```python
def invalidate(key: str) -> None:
    """
    Invalidates data in the cache.

    Args:
        key (str): The cache key.
    """
```

#### get_hit_ratio
```python
def get_hit_ratio() -> float:
    """
    Retrieves the cache hit ratio.

    Returns:
        float: The cache hit ratio.
    """
```

### ParallelAccessManager
#### submit_task
```python
def submit_task(task: Callable, *args, **kwargs) -> Future:
    """
    Submits a task for parallel execution.

    Args:
        task (Callable): The task function to be executed.
        *args: Positional arguments to be passed to the task function.
        **kwargs: Keyword arguments to be passed to the task function.

    Returns:
        Future: A future object representing the result of the task.
    """
```

#### shutdown
```python
def shutdown() -> None:
    """
    Shuts down the parallel access manager.
    """
```

## Firmware Integration
### FirmwareSpecGenerator
#### generate_spec
```python
def generate_spec() -> str:
    """
    Generates the firmware specification.

    Returns:
        str: The generated firmware specification.
    """
```

### FirmwareSpecValidator
#### validate
```python
def validate(firmware_spec: str) -> bool:
    """
    Validates the firmware specification.

    Args:
        firmware_spec (str): The firmware specification to be validated.

    Returns:
        bool: True if the firmware specification is valid, False otherwise.
    """
```

## NAND Characterization
### DataCollector
#### collect_data
```python
def collect_data(num_samples: int, output_file: str) -> None:
    """
    Collects NAND characterization data.

    Args:
        num_samples (int): The number of data samples to collect.
        output_file (str): The path to the output file for storing the collected data.
    """
```

### DataAnalyzer
#### analyze_erase_count_distribution
```python
def analyze_erase_count_distribution() -> Dict:
    """
    Analyzes the erase count distribution.

    Returns:
        Dict: The analysis results containing statistical measures of the erase count distribution.
    """
```

#### analyze_bad_block_trend
```python
def analyze_bad_block_trend() -> Dict:
    """
    Analyzes the bad block trend.

    Returns:
        Dict: The analysis results containing the trend analysis of bad blocks.
    """
```

### DataVisualizer
#### plot_erase_count_distribution
```python
def plot_erase_count_distribution(output_file: str) -> None:
    """
    Plots the erase count distribution.

    Args:
        output_file (str): The path to the output file for saving the plot.
    """
```

#### plot_bad_block_trend
```python
def plot_bad_block_trend(output_file: str) -> None:
    """
    Plots the bad block trend.

    Args:
        output_file (str): The path to the output file for saving the plot.
    """
```

This API reference provides detailed information about the available functions and their parameters and return values. It serves as a guide for developers who want to integrate the 3D NAND Optimization Tool into their own applications or extend its functionality.

Please refer to the source code and inline documentation for more specific details on how to use each API endpoint effectively.

---