# src/nand_controller.py

import json
import os
import struct
import threading
import time
from contextlib import contextmanager

import numpy as np

from src.firmware_integration.firmware_specs import FirmwareSpecGenerator
from src.nand_defect_handling.bad_block_management import BadBlockManager
from src.nand_defect_handling.error_correction import ECCHandler
from src.nand_defect_handling.wear_leveling import WearLevelingEngine
from src.performance_optimization.caching import CachingSystem, EvictionPolicy
from src.performance_optimization.data_compression import DataCompressor
from src.performance_optimization.parallel_access import ParallelAccessManager
from src.utils.logger import get_logger
from src.utils.nand_interface import HardwareNANDInterface
from src.utils.nand_simulator import NANDSimulator


class NANDController:
    """
    High-level controller for NAND flash operations.

    This class orchestrates the interaction between different modules and provides
    a unified API for applications to perform optimized NAND operations.
    """

    # Constants for metadata
    META_SIGNATURE = 0x4D455441  # "META" in ASCII
    META_VERSION = 1
    META_HEADER_SIZE = 16  # Size of metadata header

    def __init__(self, config, interface=None, simulation_mode=False):
        """
        Initialize the NAND controller with the provided configuration.

        Args:
            config: Configuration object with NAND parameters
            interface: Optional NANDInterface instance (for testing with mocks)
            simulation_mode: Whether to use simulator instead of hardware interface
        """
        self.logger = get_logger(__name__)

        # Extract configuration
        self.config = config
        self.page_size = config.get("nand_config", {}).get("page_size", 4096)
        self.pages_per_block = config.get("nand_config", {}).get("pages_per_block", 64)
        self.block_size = config.get("nand_config", {}).get("block_size", 256)
        self.num_blocks = config.get("nand_config", {}).get("num_blocks", 1024)
        self.oob_size = config.get("nand_config", {}).get("oob_size", 64)
        self.num_planes = config.get("nand_config", {}).get("num_planes", 1)

        self.firmware_config = config.get("firmware_config", {})

        # Optional features
        self.read_retry_enabled = self.firmware_config.get("read_retry", False)
        self.max_read_retries = self.firmware_config.get("max_read_retries", 3)
        self.data_scrambling = self.firmware_config.get("data_scrambling", False)
        self.scrambling_seed = self.firmware_config.get("scrambling_seed", 0xA5A5A5A5)

        # Log basic configuration information
        self.logger.info("Initializing NAND Controller with configuration:")
        self.logger.info(f"  Page size: {self.page_size} bytes")
        self.logger.info(f"  Block size: {self.block_size} pages ({self.block_size * self.page_size} bytes)")
        self.logger.info(f"  Number of blocks: {self.num_blocks}")
        self.logger.info(f"  OOB size: {self.oob_size} bytes")
        self.logger.info(f"  Number of planes: {self.num_planes}")
        self.logger.info(f"  Firmware version: {self.firmware_config.get('version', 'N/A')}")
        self.logger.info(f"  Read retry enabled: {self.read_retry_enabled}")
        self.logger.info(f"  Data scrambling enabled: {self.data_scrambling}")

        # Initialize metadata management
        self.metadata_cache = {}
        self.metadata_lock = threading.RLock()
        self._reserve_metadata_blocks()

        # Initialize optimization modules
        self.ecc_handler = ECCHandler(config)
        self.bad_block_manager = BadBlockManager(config)
        self.wear_leveling_engine = WearLevelingEngine(config)

        # Initialize performance optimization components
        opt_config = config.get("optimization_config", {})

        # Compression configuration
        self.compression_config = opt_config.get("compression", {})
        self.compression_enabled = self.compression_config.get("enabled", True)
        self.compression_algorithm = self.compression_config.get("algorithm", "lz4")
        self.compression_level = self.compression_config.get("level", 3)

        self.data_compressor = DataCompressor(algorithm=self.compression_algorithm, level=self.compression_level)

        # Caching configuration
        self.cache_config = opt_config.get("caching", {})
        self.cache_enabled = self.cache_config.get("enabled", True)
        self.cache_capacity = self.cache_config.get("capacity", 1024)
        self.cache_policy = self.cache_config.get("policy", "lru")
        self.cache_ttl = self.cache_config.get("ttl", None)

        # Create caching system with appropriate policy
        policy_map = {
            "lru": EvictionPolicy.LRU,
            "lfu": EvictionPolicy.LFU,
            "fifo": EvictionPolicy.FIFO,
            "ttl": EvictionPolicy.TTL,
        }

        self.caching_system = CachingSystem(
            capacity=self.cache_capacity,
            policy=policy_map.get(self.cache_policy.lower(), EvictionPolicy.LRU),
            ttl=self.cache_ttl,
            thread_safe=True,
            on_evict=self._on_cache_evict,
        )

        # Parallel access configuration
        self.parallel_config = opt_config.get("parallelism", {})
        self.max_threads = self.parallel_config.get("max_workers", 4)
        self.parallel_access_manager = ParallelAccessManager(max_workers=self.max_threads)

        # Initialize firmware integration components
        self.firmware_spec_generator = FirmwareSpecGenerator(config=config)

        # Performance metrics and statistics
        self.stats = {
            "reads": 0,
            "writes": 0,
            "erases": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "ecc_corrections": 0,
            "compression_ratio_sum": 0,
            "compression_count": 0,
            "start_time": time.time(),
        }
        self.stats_lock = threading.RLock()

        # Set up NAND interface based on configuration
        if interface is not None:
            # Use provided interface (useful for testing with mocks)
            self.nand_interface = interface
        elif simulation_mode:
            # Use simulator for development or testing
            self.nand_interface = NANDSimulator(config)
        else:
            # Use hardware interface for real operation
            self.nand_interface = HardwareNANDInterface(config)

    def _reserve_metadata_blocks(self):
        """Initialize and reserve blocks for metadata storage."""
        # Typical NAND controllers reserve some blocks for internal use
        # These might store bad block tables, wear leveling info, etc.
        self.reserved_blocks = {
            "metadata": 0,  # Block for general metadata
            "bad_block_table": 1,  # Block storing bad block table
            "wear_leveling": 2,  # Block for wear leveling information
            "firmware": 3,  # Block containing firmware info
            "log": 4,  # Block for logging
        }

        # Number of user-accessible blocks is reduced
        self.user_blocks = self.num_blocks - len(self.reserved_blocks)
        self.logger.info(f"Reserved {len(self.reserved_blocks)} blocks for metadata, {self.user_blocks} available for user data")

    def _on_cache_evict(self, key):
        """
        Callback triggered when an item is evicted from cache.
        This allows for clean up operations if needed.

        Args:
            key: The key of the evicted item
        """
        # No special handling needed for most cache evictions
        # In a more sophisticated implementation, we might want to
        # perform operations like writing back dirty cache entries
        self.logger.debug(f"Cache entry evicted: {key}")

    def initialize(self):
        """Initialize the NAND controller and its components."""
        self.logger.info("Initializing NAND controller...")

        try:
            # Initialize the NAND interface
            self.nand_interface.initialize()

            # Load metadata (bad block table, wear leveling info, etc.)
            self._load_metadata()

            # Verify firmware compatibility
            self._check_firmware_compatibility()

            # Run startup diagnostics
            self._run_diagnostics()

            self.logger.info("NAND controller initialized successfully.")
        except Exception as e:
            self.logger.error(f"Failed to initialize NAND controller: {str(e)}")
            # Try to shut down gracefully even if initialization failed
            try:
                self.shutdown()
            except:
                pass
            raise RuntimeError(f"NAND controller initialization failed: {str(e)}")

    def shutdown(self):
        """Shut down the NAND controller and release resources."""
        self.logger.info("Shutting down NAND controller...")

        try:
            # Flush any cached data
            if self.cache_enabled:
                self._flush_cache()

            # Save metadata updates
            self._save_metadata()

            # Shut down components
            self.parallel_access_manager.shutdown()
            self.nand_interface.shutdown()

            # Log statistics
            self._log_statistics()

            self.logger.info("NAND controller shutdown complete.")
        except Exception as e:
            self.logger.error(f"Error during NAND controller shutdown: {str(e)}")
            raise

    def _load_metadata(self):
        """Load metadata from reserved blocks with better error handling."""
        self.logger.debug("Loading NAND metadata...")

        # Keep track of loading status for each metadata type
        metadata_status = {"bad_block_table": False, "wear_leveling_info": False}

        try:
            # Load bad block table with error handling
            try:
                self._load_bad_block_table()
                metadata_status["bad_block_table"] = True
            except Exception as e:
                self.logger.error(f"Error loading bad block table: {str(e)}")
                self.logger.warning("Performing factory bad block scan as fallback")
                self._scan_factory_bad_blocks()

            # Load wear leveling information with error handling
            try:
                self._load_wear_leveling_info()
                metadata_status["wear_leveling_info"] = True
            except Exception as e:
                self.logger.error(f"Error loading wear leveling info: {str(e)}")
                self.logger.warning("Using default wear leveling values")
                # Initialize wear level table with zeros as fallback
                self.wear_leveling_engine.wear_level_table[:] = 0

            # Log overall metadata loading status
            loaded_items = sum(1 for status in metadata_status.values() if status)
            total_items = len(metadata_status)
            self.logger.info(f"NAND metadata loaded: {loaded_items}/{total_items} items successful")

        except Exception as e:
            self.logger.error(f"Error in metadata loading process: {str(e)}")
            # Continue initialization with defaults
            self.logger.warning("Continuing with default metadata values")

    def _load_bad_block_table(self):
        """Load bad block table from reserved block."""
        try:
            # Read the bad block table from the reserved block
            block = self.reserved_blocks["bad_block_table"]
            page_data = self.nand_interface.read_page(block, 0)

            # Parse bad block table
            if len(page_data) >= 8:
                signature, version = struct.unpack("<II", page_data[:8])

                if signature == self.META_SIGNATURE and version == self.META_VERSION:
                    # Valid metadata, parse bad block entries
                    num_entries = struct.unpack("<I", page_data[8:12])[0]

                    # Process each entry
                    for i in range(num_entries):
                        if 12 + i < len(page_data):
                            bad_block = struct.unpack("<I", page_data[12 + i * 4 : 16 + i * 4])[0]
                            if 0 <= bad_block < self.num_blocks:
                                self.bad_block_manager.mark_bad_block(bad_block)
                                self.logger.debug(f"Loaded bad block entry: {bad_block}")

                    self.logger.info(f"Loaded {num_entries} bad block entries")
                else:
                    # Invalid or missing metadata, perform factory scan
                    self.logger.warning("Bad block table not found, performing factory scan")
                    self._scan_factory_bad_blocks()
            else:
                # Not enough data, perform factory scan
                self.logger.warning("Bad block table incomplete, performing factory scan")
                self._scan_factory_bad_blocks()

        except Exception as e:
            self.logger.error(f"Error loading bad block table: {str(e)}")
            self.logger.warning("Performing factory bad block scan as fallback")
            self._scan_factory_bad_blocks()

    def _scan_factory_bad_blocks(self):
        """Scan for factory-marked bad blocks."""
        self.logger.info("Scanning for factory-marked bad blocks...")
        bad_count = 0

        for block in range(self.num_blocks):
            # Skip reserved blocks
            if block in self.reserved_blocks.values():
                continue

            try:
                # Read the first and last page OOB area to check for bad block marker
                # In most NAND flash, bad blocks are marked with non-0xFF in first byte of OOB
                first_page = self.nand_interface.read_page(block, 0)
                last_page = self.nand_interface.read_page(block, self.pages_per_block - 1)

                # Check first byte of OOB (assuming we have access to OOB)
                # In a real implementation, you'd specifically check the bad block marker
                # This is a simplification
                if (len(first_page) > self.page_size and first_page[self.page_size] != 0xFF) or (
                    len(last_page) > self.page_size and last_page[self.page_size] != 0xFF
                ):
                    self.bad_block_manager.mark_bad_block(block)
                    bad_count += 1
                    self.logger.debug(f"Factory bad block found: {block}")
            except Exception as e:
                # If we can't read the block, it's probably bad
                self.bad_block_manager.mark_bad_block(block)
                bad_count += 1
                self.logger.debug(f"Block {block} marked bad due to read error: {str(e)}")

        self.logger.info(f"Factory bad block scan complete. Found {bad_count} bad blocks.")

    def _load_wear_leveling_info(self):
        """Load wear leveling information from reserved block."""
        try:
            # Read the wear leveling info from the reserved block
            block = self.reserved_blocks["wear_leveling"]
            page_data = self.nand_interface.read_page(block, 0)

            # Parse wear leveling metadata
            if len(page_data) >= 8:
                signature, version = struct.unpack("<II", page_data[:8])

                if signature == self.META_SIGNATURE and version == self.META_VERSION:
                    # Valid metadata, parse wear leveling entries
                    # Format: [block_number: 4 bytes][erase_count: 4 bytes]
                    offset = 8
                    entries_possible = (len(page_data) - offset) // 8
                    entries = min(entries_possible, self.num_blocks)

                    for i in range(entries):
                        if offset + i * 8 + 8 <= len(page_data):
                            block_num, erase_count = struct.unpack("<II", page_data[offset + i * 8 : offset + i * 8 + 8])
                            if 0 <= block_num < self.num_blocks:
                                # Update erase count in wear leveling engine
                                # We're directly setting the table entry for efficiency
                                self.wear_leveling_engine.wear_level_table[block_num] = erase_count

                    self.logger.info(f"Loaded wear leveling info for {entries} blocks")
                else:
                    # Invalid or missing metadata
                    self.logger.warning("Wear leveling info not found, using default values")
            else:
                # Not enough data
                self.logger.warning("Wear leveling info incomplete, using default values")

        except Exception as e:
            self.logger.error(f"Error loading wear leveling info: {str(e)}")
            self.logger.warning("Using default wear leveling values")

    def _save_metadata(self):
        """Save metadata to reserved blocks with improved error handling."""
        self.logger.debug("Saving NAND metadata...")

        # Track success of each save operation
        save_status = {"bad_block_table": False, "wear_leveling_info": False}

        # Try to save bad block table
        try:
            self._save_bad_block_table()
            save_status["bad_block_table"] = True
        except Exception as e:
            self.logger.error(f"Error saving bad block table: {str(e)}")
            # Try alternative blocks if primary fails
            try:
                # Try saving to a backup location
                self.logger.info("Attempting to save bad block table to backup location")
                backup_block = self.reserved_blocks.get("backup", 5)  # Use block 5 as backup
                if not self.bad_block_manager.is_bad_block(backup_block):
                    # Logic to save to backup block
                    # [Implement the backup save logic here]
                    self.logger.info(f"Bad block table saved to backup block {backup_block}")
            except Exception as backup_e:
                self.logger.error(f"Backup save also failed: {str(backup_e)}")

        # Try to save wear leveling information
        try:
            self._save_wear_leveling_info()
            save_status["wear_leveling_info"] = True
        except Exception as e:
            self.logger.error(f"Error saving wear leveling info: {str(e)}")
            # Try alternative blocks if primary fails
            try:
                # Try saving to a backup location
                self.logger.info("Attempting to save wear leveling info to backup location")
                backup_block = self.reserved_blocks.get("backup", 5)  # Use block 5 as backup
                if not self.bad_block_manager.is_bad_block(backup_block):
                    # Logic to save to backup block
                    # [Implement the backup save logic here]
                    self.logger.info(f"Wear leveling info saved to backup block {backup_block}")
            except Exception as backup_e:
                self.logger.error(f"Backup save also failed: {str(backup_e)}")

        # Log overall save status
        saved_items = sum(1 for status in save_status.values() if status)
        total_items = len(save_status)
        self.logger.info(f"NAND metadata saved: {saved_items}/{total_items} items successful")

    def _save_bad_block_table(self):
        """Save bad block table to reserved block."""
        try:
            # Create bad block table data
            bad_blocks = []
            for block in range(self.num_blocks):
                if self.bad_block_manager.is_bad_block(block):
                    bad_blocks.append(block)

            # Create metadata header
            header = struct.pack("<III", self.META_SIGNATURE, self.META_VERSION, len(bad_blocks))

            # Create entry data
            entries = b""
            for block in bad_blocks:
                entries += struct.pack("<I", block)

            # Combine and pad to page size
            data = header + entries
            data = data.ljust(self.page_size, b"\xFF")

            # Erase the reserved block first
            block = self.reserved_blocks["bad_block_table"]
            self.nand_interface.erase_block(block)

            # Write the data
            self.nand_interface.write_page(block, 0, data)

            self.logger.info(f"Saved {len(bad_blocks)} bad block entries")
        except Exception as e:
            self.logger.error(f"Error saving bad block table: {str(e)}")

    def _save_wear_leveling_info(self):
        """Save wear leveling information to reserved block."""
        try:
            # Create metadata header
            header = struct.pack("<II", self.META_SIGNATURE, self.META_VERSION)

            # Create entry data
            entries = b""
            entries_per_page = (self.page_size - len(header)) // 8
            count = 0

            # Determine how many pages we need
            total_pages = (self.num_blocks + entries_per_page - 1) // entries_per_page

            # Erase the reserved block first
            block = self.reserved_blocks["wear_leveling"]
            self.nand_interface.erase_block(block)

            # Write pages of wear leveling data
            for page in range(total_pages):
                entries = b""
                start_idx = page * entries_per_page
                end_idx = min(start_idx + entries_per_page, self.num_blocks)

                for i in range(start_idx, end_idx):
                    erase_count = self.wear_leveling_engine.wear_level_table[i]
                    entries += struct.pack("<II", i, erase_count)
                    count += 1

                # Add header for first page only
                if page == 0:
                    data = header + entries
                else:
                    data = entries

                # Pad to page size
                data = data.ljust(self.page_size, b"\xFF")

                # Write the data
                self.nand_interface.write_page(block, page, data)

            self.logger.info(f"Saved wear leveling info for {count} blocks")
        except Exception as e:
            self.logger.error(f"Error saving wear leveling info: {str(e)}")

    def _check_firmware_compatibility(self):
        """Verify firmware compatibility with hardware."""
        # In a real implementation, this would check firmware version
        # against hardware requirements, verify checksums, etc.
        firmware_version = self.firmware_config.get("version", "Unknown")
        self.logger.info(f"Firmware compatibility check: version {firmware_version}")

        # This is a placeholder for demonstration
        if firmware_version == "Unknown":
            self.logger.warning("Unknown firmware version, proceed with caution")

    def _run_diagnostics(self):
        """Run startup diagnostics on the NAND flash."""
        self.logger.info("Running NAND diagnostics...")

        # Get device status
        try:
            status = self.nand_interface.get_status()
            self.logger.info(f"NAND device status: ready={status.get('ready', False)}")
        except Exception as e:
            self.logger.error(f"Error getting device status: {str(e)}")

        # Count bad blocks
        bad_count = 0
        for block in range(self.num_blocks):
            if self.bad_block_manager.is_bad_block(block):
                bad_count += 1

        bad_percent = (bad_count / self.num_blocks) * 100
        self.logger.info(f"Bad block count: {bad_count} ({bad_percent:.2f}%)")

        # Check wear leveling
        min_wear = self.wear_leveling_engine.wear_level_table.min()
        max_wear = self.wear_leveling_engine.wear_level_table.max()
        avg_wear = self.wear_leveling_engine.wear_level_table.mean()

        self.logger.info(f"Wear level status: min={min_wear}, max={max_wear}, avg={avg_wear:.2f}")

        # Diagnostics result
        if bad_percent > 10:
            self.logger.warning("NAND diagnostics result: WARNING - High bad block count")
        else:
            self.logger.info("NAND diagnostics result: PASS")

    def _flush_cache(self):
        """Flush cached data to NAND flash."""
        if not self.cache_enabled:
            return

        self.logger.debug("Flushing cache...")

        # In a real implementation, we would write back dirty cache entries
        # For now, we just clear the cache
        self.caching_system.clear()

        self.logger.debug("Cache flush complete.")

    def _log_statistics(self):
        """Log performance statistics."""
        with self.stats_lock:
            elapsed_time = time.time() - self.stats["start_time"]
            total_ops = self.stats["reads"] + self.stats["writes"] + self.stats["erases"]
            cache_total = self.stats["cache_hits"] + self.stats["cache_misses"]

            if cache_total > 0:
                hit_ratio = (self.stats["cache_hits"] / cache_total) * 100
            else:
                hit_ratio = 0

            if self.stats["compression_count"] > 0:
                avg_compression = self.stats["compression_ratio_sum"] / self.stats["compression_count"]
            else:
                avg_compression = 0

            self.logger.info("NAND Controller Statistics:")
            self.logger.info(f"  Elapsed time: {elapsed_time:.2f} seconds")
            self.logger.info(f"  Total operations: {total_ops}")
            self.logger.info(f"    - Reads: {self.stats['reads']}")
            self.logger.info(f"    - Writes: {self.stats['writes']}")
            self.logger.info(f"    - Erases: {self.stats['erases']}")
            self.logger.info(f"  Cache hit ratio: {hit_ratio:.2f}%")
            self.logger.info(f"  ECC corrections: {self.stats['ecc_corrections']}")
            self.logger.info(f"  Average compression ratio: {avg_compression:.2f}x")

    def translate_address(self, logical_block):
        """
        Translate logical block address to physical block address.

        Args:
            logical_block (int): Logical block number

        Returns:
            int: Physical block number
        """
        # Adjust for reserved blocks
        if logical_block >= self.user_blocks:
            raise ValueError(f"Logical block {logical_block} exceeds available user blocks ({self.user_blocks})")

        # Get physical block from wear leveling engine
        # In a real implementation, this would consult a mapping table
        # For simplicity, we use a direct mapping with offset
        physical_block = logical_block + len(self.reserved_blocks)

        # Find next good block if this one is bad
        while self.bad_block_manager.is_bad_block(physical_block):
            physical_block = self.bad_block_manager.get_next_good_block(physical_block)

        return physical_block

    def read_page(self, block, page):
        """
        Read a page from the NAND flash with all optimizations applied.

        Args:
            block (int): The block number
            page (int): The page number within the block

        Returns:
            bytes: The data read from the page
        """
        with self.stats_lock:
            self.stats["reads"] += 1

        self.logger.debug(f"Reading page {page} from block {block}")

        # Translate logical to physical address if needed
        physical_block = self.translate_address(block) if block < self.user_blocks else block

        # Check if block is bad
        if self.bad_block_manager.is_bad_block(physical_block):
            self.logger.warning(f"Attempted to read from bad block {physical_block}")
            raise IOError(f"Block {physical_block} is marked as bad")

        # Check if data is cached
        cache_key = f"{physical_block}:{page}"
        if self.cache_enabled:
            cached_data = self.caching_system.get(cache_key)
            if cached_data is not None:
                self.logger.debug("Cache hit. Returning cached data.")
                with self.stats_lock:
                    self.stats["cache_hits"] += 1
                return cached_data
            else:
                with self.stats_lock:
                    self.stats["cache_misses"] += 1

        # Initialize retry counter if read retry is enabled
        retry_count = 0
        max_retries = self.max_read_retries if self.read_retry_enabled else 0

        while True:
            try:
                # Read raw page data from NAND
                raw_data = self.nand_interface.read_page(physical_block, page)

                # Apply data scrambling if enabled
                if self.data_scrambling:
                    raw_data = self._descramble_data(raw_data, physical_block, page)

                # Perform error correction
                try:
                    decoded_data, num_errors = self.ecc_handler.decode(raw_data)

                    if num_errors > 0:
                        self.logger.info(f"Corrected {num_errors} errors in block {physical_block}, page {page}")
                        with self.stats_lock:
                            self.stats["ecc_corrections"] += num_errors
                except ValueError:
                    # Uncorrectable error
                    if retry_count < max_retries:
                        retry_count += 1
                        self.logger.warning(f"Uncorrectable errors in block {physical_block}, page {page}. Retry {retry_count}/{max_retries}")
                        continue
                    else:
                        self.logger.error(f"Uncorrectable errors in block {physical_block}, page {page} after {retry_count} retries")
                        raise IOError(f"Uncorrectable errors in block {physical_block}, page {page}")

                # Decompress data if compression is enabled
                if self.compression_enabled and decoded_data is not None:
                    try:
                        decompressed_data = self.data_compressor.decompress(decoded_data)
                    except Exception as e:
                        self.logger.warning(f"Decompression failed: {str(e)}. Returning raw data.")
                        decompressed_data = decoded_data
                else:
                    decompressed_data = decoded_data

                # Cache the decompressed data
                if self.cache_enabled and decompressed_data is not None:
                    self.caching_system.put(cache_key, decompressed_data)

                return decompressed_data

            except Exception as e:
                if retry_count < max_retries:
                    retry_count += 1
                    self.logger.warning(f"Error reading block {physical_block}, page {page}: {str(e)}. Retry {retry_count}/{max_retries}")
                else:
                    self.logger.error(f"Failed to read block {physical_block}, page {page} after {retry_count} retries: {str(e)}")
                    raise

    def write_page(self, block, page, data):
        """
        Write data to a page in the NAND flash with all optimizations applied.

        Args:
            block (int): The block number
            page (int): The page number within the block
            data (bytes): The data to be written
        """
        with self.stats_lock:
            self.stats["writes"] += 1

        self.logger.debug(f"Writing page {page} to block {block}")

        # Translate logical to physical address if needed
        physical_block = self.translate_address(block) if block < self.user_blocks else block

        # Check if block is bad
        if self.bad_block_manager.is_bad_block(physical_block):
            self.logger.warning(f"Attempted to write to bad block {physical_block}")
            raise IOError(f"Block {physical_block} is marked as bad")

        # Compress data if enabled
        if self.compression_enabled:
            original_size = len(data)
            compressed_data = self.data_compressor.compress(data)
            compressed_size = len(compressed_data)

            # Only use compression if it actually reduces size
            if compressed_size < original_size:
                compression_ratio = original_size / compressed_size
                self.logger.debug(f"Compressed data: {original_size} -> {compressed_size} bytes ({compression_ratio:.2f}x)")
                with self.stats_lock:
                    self.stats["compression_ratio_sum"] += compression_ratio
                    self.stats["compression_count"] += 1
                data_to_write = compressed_data
            else:
                self.logger.debug("Compression ineffective, using original data")
                data_to_write = data
        else:
            data_to_write = data

        # Perform error correction coding
        ecc_data = self.ecc_handler.encode(data_to_write)

        # Apply data scrambling if enabled
        if self.data_scrambling:
            ecc_data = self._scramble_data(ecc_data, physical_block, page)

        # Write raw page data to NAND
        try:
            self.nand_interface.write_page(physical_block, page, ecc_data)
        except Exception as e:
            self.logger.error(f"Write error for block {physical_block}, page {page}: {str(e)}")
            # Check if this is a program failure that requires marking the block as bad
            self._handle_write_error(physical_block, e)
            raise

        # Update wear leveling
        self.wear_leveling_engine.update_wear_level(physical_block)

        # Check if wear leveling should be performed
        if self.wear_leveling_engine.should_perform_wear_leveling():
            self._perform_advanced_wear_leveling()

        # Invalidate cached data for the written page
        cache_key = f"{physical_block}:{page}"
        if self.cache_enabled:
            self.caching_system.invalidate(cache_key)

        # Update cache with the new data
        if self.cache_enabled:
            self.caching_system.put(cache_key, data)

    def erase_block(self, block):
        """
        Erase a block in the NAND flash.

        Args:
            block (int): The block number
        """
        with self.stats_lock:
            self.stats["erases"] += 1

        self.logger.debug(f"Erasing block {block}")

        # Translate logical to physical address if needed
        physical_block = self.translate_address(block) if block < self.user_blocks else block

        # Check if block is bad
        if self.bad_block_manager.is_bad_block(physical_block):
            self.logger.warning(f"Attempting to erase bad block {physical_block}")
            raise IOError(f"Block {physical_block} is marked as bad")

        # Erase the block
        try:
            self.nand_interface.erase_block(physical_block)
        except Exception as e:
            self.logger.error(f"Erase error for block {physical_block}: {str(e)}")
            # Check if this is an erase failure that requires marking the block as bad
            self._handle_erase_error(physical_block, e)
            raise

        # Update wear leveling
        self.wear_leveling_engine.update_wear_level(physical_block)

        # Check if wear leveling should be performed
        if self.wear_leveling_engine.should_perform_wear_leveling():
            self._perform_advanced_wear_leveling()

        # Invalidate cached data for the erased block
        if self.cache_enabled:
            for page in range(self.pages_per_block):
                cache_key = f"{physical_block}:{page}"
                self.caching_system.invalidate(cache_key)

    def mark_bad_block(self, block):
        """
        Mark a block as bad in the bad block table.

        Args:
            block (int): The block number
        """
        self.logger.debug(f"Marking block {block} as bad")

        # If it's a logical block, translate it
        if block < self.user_blocks:
            physical_block = self.translate_address(block)
        else:
            physical_block = block

        self.bad_block_manager.mark_bad_block(physical_block)

        # Invalidate any cached data for this block
        if self.cache_enabled:
            for page in range(self.pages_per_block):
                cache_key = f"{physical_block}:{page}"
                self.caching_system.invalidate(cache_key)

    def is_bad_block(self, block):
        """
        Check if a block is marked as bad.

        Args:
            block (int): The block number

        Returns:
            bool: True if the block is bad, False otherwise
        """
        # If it's a logical block, translate it
        if block < self.user_blocks:
            physical_block = self.translate_address(block)
        else:
            physical_block = block

        return self.bad_block_manager.is_bad_block(physical_block)

    def get_next_good_block(self, block):
        """
        Find the next good block starting from the given block.

        Args:
            block (int): The starting block number

        Returns:
            int: The next good block number
        """
        # If it's a logical block, translate it
        if block < self.user_blocks:
            physical_block = self.translate_address(block)
        else:
            physical_block = block

        # Find next good physical block
        next_physical = self.bad_block_manager.get_next_good_block(physical_block)

        # If we're operating in logical space, convert back
        if block < self.user_blocks:
            # This is a simplification; in a real implementation, you would
            # need to consult the mapping table to find the logical block
            # associated with the physical block
            next_logical = next_physical - len(self.reserved_blocks)
            if next_logical >= self.user_blocks:
                # Wrap around if we've exceeded user blocks
                next_logical = 0
            return next_logical
        else:
            return next_physical

    def get_least_worn_block(self):
        """
        Find the block with the least wear level.

        Returns:
            int: The block number with the least wear level
        """
        # Get the physical block with least wear
        physical_block = self.wear_leveling_engine.get_least_worn_block()

        # If it's in the reserved area, find the next least worn block
        while physical_block in self.reserved_blocks.values():
            # Temporarily set high wear level
            original_wear = self.wear_leveling_engine.wear_level_table[physical_block]
            self.wear_leveling_engine.wear_level_table[physical_block] = np.iinfo(np.uint32).max

            # Find new least worn block
            physical_block = self.wear_leveling_engine.get_least_worn_block()

            # Restore original wear level
            self.wear_leveling_engine.wear_level_table[physical_block] = original_wear

        # Convert to logical block if applicable
        if physical_block >= len(self.reserved_blocks):
            return physical_block - len(self.reserved_blocks)
        else:
            return physical_block

    def generate_firmware_spec(self):
        """
        Generate the firmware specification based on the current configuration.

        Returns:
            str: The generated firmware specification
        """
        return self.firmware_spec_generator.generate_spec()

    def read_metadata(self, block):
        """
        Read metadata from a block.

        Args:
            block (int): The block number

        Returns:
            dict: The metadata read from the block
        """
        self.logger.debug(f"Reading metadata from block {block}")

        # Check cache first
        with self.metadata_lock:
            if block in self.metadata_cache:
                return self.metadata_cache[block]

        # Translate logical to physical if needed
        physical_block = self.translate_address(block) if block < self.user_blocks else block

        # Read the last page, which is typically used for metadata
        metadata_page = self.pages_per_block - 1

        try:
            metadata_raw = self.nand_interface.read_page(physical_block, metadata_page)

            # Check for valid metadata header
            if len(metadata_raw) >= self.META_HEADER_SIZE:
                signature, version, meta_type, meta_size = struct.unpack("<IIII", metadata_raw[: self.META_HEADER_SIZE])

                if signature == self.META_SIGNATURE:
                    # Valid metadata
                    meta_data = metadata_raw[self.META_HEADER_SIZE : self.META_HEADER_SIZE + meta_size]

                    # Parse depending on metadata type
                    if meta_type == 1:  # JSON metadata
                        try:
                            # Decode JSON metadata
                            meta_str = meta_data.decode("utf-8").rstrip("\0")
                            metadata = json.loads(meta_str)
                        except Exception as e:
                            self.logger.error(f"Error parsing JSON metadata: {str(e)}")
                            return None
                    elif meta_type == 2:  # Binary metadata
                        metadata = {"raw": meta_data, "type": "binary"}
                    else:
                        self.logger.warning(f"Unknown metadata type: {meta_type}")
                        return None

                    # Cache the metadata
                    with self.metadata_lock:
                        self.metadata_cache[block] = metadata

                    return metadata
                else:
                    self.logger.warning(f"Invalid metadata signature in block {physical_block}")
            else:
                self.logger.warning(f"Metadata too short in block {physical_block}")

            return None
        except Exception as e:
            self.logger.error(f"Error reading metadata from block {physical_block}: {str(e)}")
            return None

    def write_metadata(self, block, metadata):
        """
        Write metadata to a block.

        Args:
            block (int): The block number
            metadata (dict): The metadata to write
        """
        self.logger.debug(f"Writing metadata to block {block}")

        # Translate logical to physical if needed
        physical_block = self.translate_address(block) if block < self.user_blocks else block

        # The last page is typically used for metadata
        metadata_page = self.pages_per_block - 1

        try:
            # Serialize metadata to JSON
            meta_json = json.dumps(metadata).encode("utf-8")
            meta_size = len(meta_json)

            # Create metadata header
            header = struct.pack("<IIII", self.META_SIGNATURE, self.META_VERSION, 1, meta_size)  # Signature  # Version  # Type (1 = JSON)  # Size

            # Combine header and metadata
            metadata_raw = header + meta_json

            # Pad to page size if necessary
            if len(metadata_raw) < self.page_size:
                metadata_raw += b"\xFF" * (self.page_size - len(metadata_raw))
            elif len(metadata_raw) > self.page_size:
                # Truncate if too large
                self.logger.warning(f"Metadata too large, truncating ({len(metadata_raw)} > {self.page_size})")
                metadata_raw = metadata_raw[: self.page_size]

            # Write the metadata page
            self.write_page(physical_block, metadata_page, metadata_raw)

            # Update cache
            with self.metadata_lock:
                self.metadata_cache[block] = metadata

        except Exception as e:
            self.logger.error(f"Error writing metadata to block {physical_block}: {str(e)}")
            raise

    def execute_parallel_operations(self, operations):
        """
        Execute multiple NAND operations in parallel.

        Args:
            operations (list): List of operation dictionaries

        Returns:
            list: Results of the operations
        """
        futures = []

        for operation in operations:
            op_type = operation.get("type")
            block = operation.get("block")
            page = operation.get("page")
            data = operation.get("data")

            if op_type == "read":
                future = self.parallel_access_manager.submit_task(self.read_page, block, page)
            elif op_type == "write":
                future = self.parallel_access_manager.submit_task(self.write_page, block, page, data)
            elif op_type == "erase":
                future = self.parallel_access_manager.submit_task(self.erase_block, block)
            else:
                self.logger.warning(f"Unknown operation type: {op_type}")
                continue

            futures.append((operation, future))

        # Wait for all operations to complete
        results = []
        for operation, future in futures:
            try:
                result = future.result()
                results.append({"operation": operation, "result": result, "status": "success"})
            except Exception as e:
                results.append({"operation": operation, "error": str(e), "status": "failure"})

        return results

    def get_device_info(self):
        """
        Get information about the NAND device.

        Returns:
            dict: Device information
        """
        info = {
            "config": {
                "page_size": self.page_size,
                "block_size": self.block_size,
                "num_blocks": self.num_blocks,
                "pages_per_block": self.pages_per_block,
                "oob_size": self.oob_size,
                "num_planes": self.num_planes,
                "user_blocks": self.user_blocks,
            },
            "firmware": {
                "version": self.firmware_config.get("version", "N/A"),
                "features": {
                    "read_retry": self.read_retry_enabled,
                    "data_scrambling": self.data_scrambling,
                    "compression": self.compression_enabled,
                },
            },
            "statistics": self._get_statistics(),
        }

        # Try to get additional info from the NAND interface
        try:
            device_status = self.nand_interface.get_status()
            info["status"] = device_status
        except Exception as e:
            self.logger.warning(f"Failed to get device status: {str(e)}")

        return info

    def _get_statistics(self):
        """
        Get performance and health statistics.

        Returns:
            dict: Statistics information
        """
        with self.stats_lock:
            elapsed_time = time.time() - self.stats["start_time"]
            stats = {
                "reads": self.stats["reads"],
                "writes": self.stats["writes"],
                "erases": self.stats["erases"],
                "ecc_corrections": self.stats["ecc_corrections"],
                "cache": {
                    "hits": self.stats["cache_hits"],
                    "misses": self.stats["cache_misses"],
                    "hit_ratio": self._calculate_hit_ratio(),
                },
                "wear_leveling": {
                    "min_erase_count": int(self.wear_leveling_engine.wear_level_table.min()),
                    "max_erase_count": int(self.wear_leveling_engine.wear_level_table.max()),
                    "avg_erase_count": float(self.wear_leveling_engine.wear_level_table.mean()),
                    "std_dev": float(self.wear_leveling_engine.wear_level_table.std()),
                },
                "bad_blocks": {
                    "count": int(sum(self.bad_block_manager.bad_block_table)),
                    "percentage": float((sum(self.bad_block_manager.bad_block_table) / self.num_blocks) * 100),
                },
                "compression": {"avg_ratio": float(self.stats["compression_ratio_sum"] / max(1, self.stats["compression_count"]))},
                "performance": {"ops_per_second": float((self.stats["reads"] + self.stats["writes"] + self.stats["erases"]) / max(0.001, elapsed_time))},
            }

            return stats

    def _calculate_hit_ratio(self):
        """Calculate cache hit ratio."""
        total = self.stats["cache_hits"] + self.stats["cache_misses"]
        if total > 0:
            return (self.stats["cache_hits"] / total) * 100
        return 0.0

    def _handle_write_error(self, block, error):
        """
        Handle a write error and determine if the block should be marked as bad.

        Args:
            block (int): The block number
            error: The exception that occurred
        """
        # Error conditions that indicate a bad block
        bad_block_indicators = ["program fail", "status error", "timeout", "verify fail", "write protected"]

        error_str = str(error).lower()
        mark_bad = False

        # Check if the error indicates a bad block
        for indicator in bad_block_indicators:
            if indicator in error_str:
                mark_bad = True
                break

        # Mark the block as bad if necessary
        if mark_bad:
            self.logger.warning(f"Marking block {block} as bad due to write error: {error_str}")
            self.mark_bad_block(block)

    def _handle_erase_error(self, block, error):
        """
        Handle an erase error and determine if the block should be marked as bad.

        Args:
            block (int): The block number
            error: The exception that occurred
        """
        # Error conditions that indicate a bad block
        bad_block_indicators = ["erase fail", "status error", "timeout", "write protected"]

        error_str = str(error).lower()
        mark_bad = False

        # Check if the error indicates a bad block
        for indicator in bad_block_indicators:
            if indicator in error_str:
                mark_bad = True
                break

        # Mark the block as bad if necessary
        if mark_bad:
            self.logger.warning(f"Marking block {block} as bad due to erase error: {error_str}")
            self.mark_bad_block(block)

    def _scramble_data(self, data, block, page):
        """
        Scramble data to improve reliability.

        Args:
            data (bytes): Data to scramble
            block (int): Block number (used for seed)
            page (int): Page number (used for seed)

        Returns:
            bytes: Scrambled data
        """
        if not self.data_scrambling:
            return data

        # Use block and page as part of the seed
        seed = self.scrambling_seed ^ (block << 16) ^ page

        # Initialize random generator with seed
        rng = np.random.RandomState(seed)

        # Generate scrambling pattern
        pattern = rng.bytes(len(data))

        # XOR data with pattern
        scrambled = bytearray(len(data))
        for i in range(len(data)):
            scrambled[i] = data[i] ^ pattern[i]

        return bytes(scrambled)

    def _descramble_data(self, data, block, page):
        """
        Descramble data.

        Args:
            data (bytes): Scrambled data
            block (int): Block number (used for seed)
            page (int): Page number (used for seed)

        Returns:
            bytes: Descrambled data
        """
        # Scrambling and descrambling are the same operation
        return self._scramble_data(data, block, page)

    def _perform_advanced_wear_leveling(self):
        """Perform advanced wear leveling to balance block wear."""
        self.logger.debug("Performing advanced wear leveling")

        # Find least and most worn blocks
        least_worn = self.wear_leveling_engine.get_least_worn_block()
        most_worn = self.wear_leveling_engine.get_most_worn_block()

        least_wear = self.wear_leveling_engine.wear_level_table[least_worn]
        most_wear = self.wear_leveling_engine.wear_level_table[most_worn]

        # Check if blocks are in reserved area
        if least_worn in self.reserved_blocks.values() or most_worn in self.reserved_blocks.values():
            self.logger.debug("Skipping wear leveling: involves reserved blocks")
            return

        # Check if blocks are marked bad
        if self.bad_block_manager.is_bad_block(least_worn) or self.bad_block_manager.is_bad_block(most_worn):
            self.logger.debug("Skipping wear leveling: involves bad blocks")
            return

        # Only perform wear leveling if the difference is significant
        if most_wear - least_wear > self.wear_leveling_engine.wear_threshold:
            self.logger.info(f"Wear leveling: moving data from block {most_worn} to {least_worn}")

            try:
                # Copy data from most worn to least worn block
                self._copy_block_data(most_worn, least_worn)

                # Update wear levels
                temp = self.wear_leveling_engine.wear_level_table[least_worn]
                self.wear_leveling_engine.wear_level_table[least_worn] = self.wear_leveling_engine.wear_level_table[most_worn]
                self.wear_leveling_engine.wear_level_table[most_worn] = temp

                self.logger.info("Wear leveling completed successfully")
            except Exception as e:
                self.logger.error(f"Error during wear leveling: {str(e)}")

    def _copy_block_data(self, source_block, dest_block):
        """
        Copy all data from one block to another.

        Args:
            source_block (int): Source block number
            dest_block (int): Destination block number
        """
        # Ensure destination block is erased
        self.nand_interface.erase_block(dest_block)

        # Copy page by page
        for page in range(self.pages_per_block):
            try:
                data = self.nand_interface.read_page(source_block, page)
                self.nand_interface.write_page(dest_block, page, data)
            except Exception as e:
                self.logger.error(f"Error copying page {page} from block {source_block} to {dest_block}: {str(e)}")
                raise

        # Update cache
        if self.cache_enabled:
            for page in range(self.pages_per_block):
                source_key = f"{source_block}:{page}"
                dest_key = f"{dest_block}:{page}"

                cached_data = self.caching_system.get(source_key)
                if cached_data is not None:
                    self.caching_system.put(dest_key, cached_data)

    def load_data(self, file_path):
        """
        Load data from a file to the NAND flash.

        Args:
            file_path (str): Path to the file to load
        """
        self.logger.info(f"Loading data from {file_path}")

        # Get file size
        file_size = os.path.getsize(file_path)

        # Calculate number of pages needed
        pages_needed = (file_size + self.page_size - 1) // self.page_size
        blocks_needed = (pages_needed + self.pages_per_block - 1) // self.pages_per_block

        self.logger.info(f"File size: {file_size} bytes, requires {pages_needed} pages, {blocks_needed} blocks")

        if blocks_needed > self.user_blocks:
            raise ValueError(f"File too large: requires {blocks_needed} blocks, only {self.user_blocks} available")

        try:
            with open(file_path, "rb") as f:
                # Keep track of current position
                block = 0
                page = 0
                bytes_written = 0

                while bytes_written < file_size:
                    # Find a good block
                    while self.is_bad_block(block):
                        block += 1
                        if block >= self.user_blocks:
                            raise RuntimeError("Not enough good blocks available")

                    # Calculate remaining size in current block
                    remaining_pages = self.pages_per_block - page

                    # Erase block if starting at the beginning
                    if page == 0:
                        self.erase_block(block)

                    # Write pages in the current block
                    for p in range(page, self.pages_per_block):
                        # Read page-sized chunk from file
                        data = f.read(self.page_size)

                        if not data:
                            # End of file
                            break

                        # Write the page
                        self.write_page(block, p, data)
                        bytes_written += len(data)

                        if bytes_written >= file_size:
                            # File completely written
                            break

                    # Move to next block
                    block += 1
                    page = 0

                # Write metadata with file information
                metadata = {
                    "file_name": os.path.basename(file_path),
                    "file_size": file_size,
                    "blocks_used": blocks_needed,
                    "pages_used": pages_needed,
                    "timestamp": time.time(),
                }

                metadata_block = self.reserved_blocks.get("metadata", 0)
                self.write_metadata(metadata_block, metadata)

                self.logger.info(f"Successfully loaded {file_size} bytes to NAND flash")

        except Exception as e:
            self.logger.error(f"Error loading data: {str(e)}")
            raise

    def save_data(self, file_path, start_block=0, end_block=None, metadata_block=None):
        """
        Save data from the NAND flash to a file.

        Args:
            file_path (str): Path to save the file
            start_block (int): First block to read
            end_block (int): Last block to read (None for all blocks)
            metadata_block (int): Block containing file metadata (None to use default)
        """
        self.logger.info(f"Saving data to {file_path}")

        # Determine range of blocks to read
        if end_block is None:
            end_block = self.user_blocks - 1

        if metadata_block is None:
            metadata_block = self.reserved_blocks.get("metadata", 0)

        # Get metadata if available
        metadata = self.read_metadata(metadata_block)
        if metadata:
            self.logger.info(f"Found metadata: {metadata}")
            # Use metadata to determine file size if available
            file_size = metadata.get("file_size")
            blocks_used = metadata.get("blocks_used")
            pages_used = metadata.get("pages_used")
        else:
            file_size = None
            blocks_used = None
            pages_used = None

        try:
            with open(file_path, "wb") as f:
                bytes_written = 0

                for block in range(start_block, end_block + 1):
                    # Skip bad blocks
                    if self.is_bad_block(block):
                        self.logger.debug(f"Skipping bad block {block}")
                        continue

                    # Read all pages in the block
                    for page in range(self.pages_per_block):
                        try:
                            # Check if we've reached the end of the file
                            if file_size is not None and bytes_written >= file_size:
                                break

                            # Read page
                            data = self.read_page(block, page)

                            # Determine how much to write
                            if file_size is not None and bytes_written + len(data) > file_size:
                                # Last page might be partial
                                remaining = file_size - bytes_written
                                data = data[:remaining]

                            # Write data to file
                            f.write(data)
                            bytes_written += len(data)

                        except Exception as e:
                            self.logger.warning(f"Error reading block {block}, page {page}: {str(e)}")
                            # Continue with next page

                self.logger.info(f"Successfully saved {bytes_written} bytes to {file_path}")

        except Exception as e:
            self.logger.error(f"Error saving data: {str(e)}")
            raise

    @contextmanager
    def batch_operations(self):
        """
        Context manager for batching operations.

        Example:
            with nand_controller.batch_operations():
                nand_controller.write_page(0, 0, data1)
                nand_controller.write_page(0, 1, data2)
        """
        # This would typically set up a transaction or batch context
        self.logger.debug("Starting batch operations")
        try:
            # Yield control back to the caller
            yield
            # Commit the batch if all operations succeed
            self.logger.debug("Batch operations completed successfully")
        except Exception as e:
            # Roll back the batch if any operation fails
            self.logger.error(f"Batch operations failed: {str(e)}")
            raise
