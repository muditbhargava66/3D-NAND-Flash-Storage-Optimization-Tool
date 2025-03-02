# 3D NAND Optimization Tool Examples

This directory contains example code that demonstrates various features of the 3D NAND Optimization Tool. These examples are intended to help you understand how to use the tool effectively in your own applications.

## Available Examples

### [Basic Operations](basic_operations.py)
Demonstrates fundamental NAND flash operations:
- Initialization and shutdown procedures
- Reading and writing data to pages
- Erasing blocks
- Bad block handling
- Error detection and recovery
- Device information retrieval

### [Error Correction](error_correction.py)
Shows NAND flash error correction capabilities:
- BCH (Bose-Chaudhuri-Hocquenghem) code implementation
- LDPC (Low-Density Parity-Check) code implementation
- Error introduction and correction simulation
- Performance comparison between different correction methods
- Unified error correction handling interface

### [Compression](compression.py)
Demonstrates data compression techniques for NAND flash:
- LZ4 compression algorithm implementation
- Zstandard (zstd) compression algorithm integration
- Compression level tuning for different workloads
- Performance and compression ratio comparisons across data types
- Visual analysis of compression effectiveness

### [Wear Leveling](wear_leveling.py)
Demonstrates advanced wear leveling techniques:
- Monitoring wear distribution across blocks
- Handling uneven workloads with hot/cold data patterns
- Manual wear leveling operations
- Threshold-based automatic wear leveling
- Visualizing wear distribution before and after optimization

### [Caching](caching.py)
Showcases the advanced caching system:
- Different eviction policies (LRU, LFU, FIFO)
- Time-based cache expiration (TTL)
- Cache statistics and monitoring
- Performance comparison across access patterns
- Visualization of hit rates and execution times

### [Firmware Generation](firmware_generation.py)
Shows how to create and validate firmware specifications:
- Configuring firmware parameters
- Generating firmware specifications from templates
- Validating specifications against schema and business rules
- Customizing firmware for different NAND configurations (MLC, TLC, QLC)
- Creating advanced templates with extended configuration options

## Running the Examples

To run these examples, execute them from the project root directory:

```bash
python examples/basic_operations.py
python examples/error_correction.py
python examples/compression.py
python examples/wear_leveling.py
python examples/caching.py
python examples/firmware_generation.py
```

Make sure you've installed the required dependencies first:

```bash
pip install -r requirements.txt
```

## Expected Output

Each example will produce visual and/or file outputs that demonstrate the functionality:

- The **basic_operations** example shows console output for various NAND operations
- The **error_correction** example demonstrates error correction capabilities with statistics
- The **compression** example generates graphs comparing compression algorithms and ratios
- The **wear_leveling** example produces graphs showing wear distribution
- The **caching** example creates visualizations of cache performance across policies
- The **firmware_generation** example creates YAML files with firmware specifications

## Using in Your Code

You can use these examples as a starting point for integrating the 3D NAND Optimization Tool into your own applications. The key components demonstrated here can be adapted to your specific use cases and requirements.

## Dependencies

The examples rely on the following main dependencies:
- NumPy for numerical operations
- Matplotlib for visualization
- PyYAML for configuration handling

Additional specific dependencies may be required for certain examples, which are documented in the respective files.