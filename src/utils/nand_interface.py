# src/utils/nand_interface.py

import logging
import random
import time
from abc import ABC, abstractmethod
from contextlib import contextmanager


class NANDInterface(ABC):
    """
    Abstract base class defining the interface for NAND flash operations.

    This interface defines the contract that must be implemented by both
    real hardware interfaces and simulation interfaces.
    """

    @abstractmethod
    def initialize(self):
        """Initialize the NAND device for operations."""
        pass

    @abstractmethod
    def shutdown(self):
        """Shut down the NAND device properly."""
        pass

    @abstractmethod
    def read_page(self, block, page):
        """
        Read a page from the NAND device.

        Args:
            block (int): Block number
            page (int): Page number within the block

        Returns:
            bytes: Raw data read from the page
        """
        pass

    @abstractmethod
    def write_page(self, block, page, data):
        """
        Write data to a page in the NAND device.

        Args:
            block (int): Block number
            page (int): Page number within the block
            data (bytes): Data to write to the page
        """
        pass

    @abstractmethod
    def erase_block(self, block):
        """
        Erase a block in the NAND device.

        Args:
            block (int): Block number to erase
        """
        pass

    @abstractmethod
    def get_status(self, block=None, page=None):
        """
        Get status information from the NAND device.

        Args:
            block (int, optional): Block number to check
            page (int, optional): Page number to check

        Returns:
            dict: Status information
        """
        pass


class HardwareNANDInterface(NANDInterface):
    """
    Implementation of NANDInterface for real NAND flash hardware.

    This class communicates with physical NAND flash memory chips
    through appropriate hardware interfaces and controllers.

    Note: This implementation uses platform-independent abstractions
    and will require hardware-specific adapters for actual hardware control.
    """

    # NAND Flash command set (based on ONFI standard)
    CMD_READ_1 = 0x00
    CMD_READ_2 = 0x30
    CMD_READ_PARAM = 0xEC
    CMD_READ_ID = 0x90
    CMD_WRITE_1 = 0x80
    CMD_WRITE_2 = 0x10
    CMD_ERASE_1 = 0x60
    CMD_ERASE_2 = 0xD0
    CMD_RESET = 0xFF
    CMD_READ_STATUS = 0x70

    # Status register bit masks
    STATUS_FAIL = 0x01
    STATUS_READY = 0x40
    STATUS_WRITE_PROTECT = 0x80

    def __init__(self, config):
        """
        Initialize the hardware interface.

        Args:
            config: Configuration object with NAND parameters
        """
        self.logger = logging.getLogger(__name__)
        self.page_size = config.get("nand_config", {}).get("page_size", 4096)
        self.oob_size = config.get("nand_config", {}).get("oob_size", 64)
        self.pages_per_block = config.get("nand_config", {}).get("pages_per_block", 64)
        self.block_size = self.page_size * self.pages_per_block
        self.num_blocks = config.get("nand_config", {}).get("num_blocks", 1024)
        self.num_planes = config.get("nand_config", {}).get("num_planes", 1)

        # Hardware configuration
        self.hw_config = config.get("hardware_config", {})
        self.spi_device = self.hw_config.get("spi_device", "/dev/spidev0.0")
        self.spi_speed = self.hw_config.get("spi_speed", 20000000)  # 20MHz default
        self.cs_pin = self.hw_config.get("cs_pin", 0)
        self.wp_pin = self.hw_config.get("wp_pin", None)
        self.hold_pin = self.hw_config.get("hold_pin", None)

        # Initialize hardware-specific components
        self.spi = None
        self.hw_controller = None
        self.device = None
        self.is_initialized = False

        # Statistics
        self.stats = {"reads": 0, "writes": 0, "erases": 0, "errors": 0}

    def initialize(self):
        """Initialize the NAND hardware."""
        try:
            self.logger.info("Initializing NAND hardware interface")

            # Initialize hardware communication interface
            self._init_hardware_interface()

            # Reset the device
            self._reset_device()

            # Read device ID and validate
            device_id = self._read_device_id()
            self.logger.info(f"NAND device ID: 0x{device_id:08x}")

            # Read parameters and configure the device
            self._configure_device()

            self.is_initialized = True
            self.logger.info("NAND hardware interface initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize NAND hardware: {str(e)}")
            raise RuntimeError(f"NAND hardware initialization failed: {str(e)}")

    def shutdown(self):
        """Shut down the NAND hardware properly."""
        if not self.is_initialized:
            return

        try:
            self.logger.info("Shutting down NAND hardware interface")

            # Ensure all pending operations are complete
            self._wait_ready()

            # Put device in standby mode
            self._send_command(self.CMD_RESET)

            # Close hardware interfaces
            self._close_hardware_interface()

            self.is_initialized = False
            self.logger.info("NAND hardware interface shut down successfully")

        except Exception as e:
            self.logger.error(f"Error during NAND hardware shutdown: {str(e)}")

    def read_page(self, block, page):
        """
        Read a page from the NAND hardware.

        Args:
            block (int): Block number
            page (int): Page number within the block

        Returns:
            bytes: Raw data read from the page
        """
        if not self.is_initialized:
            raise RuntimeError("NAND hardware not initialized")

        if block >= self.num_blocks or page >= self.pages_per_block:
            raise ValueError(f"Invalid block/page: {block}/{page}")

        try:
            self.logger.debug(f"Reading page {page} from block {block}")
            self.stats["reads"] += 1

            # Calculate physical address
            row_address = (block * self.pages_per_block) + page

            # Send read command sequence
            self._chip_select(True)
            self._send_command(self.CMD_READ_1)

            # Send address cycles (column address = 0, row address)
            self._send_address_cycles(0, row_address)

            # Send second read command
            self._send_command(self.CMD_READ_2)

            # Wait for operation to complete
            self._wait_ready()

            # Read data
            data = self._read_data(self.page_size + self.oob_size)

            self._chip_select(False)

            # Check for read errors
            status = self._read_status()
            if status & self.STATUS_FAIL:
                self.logger.warning(f"Read error detected in block {block}, page {page}")
                self.stats["errors"] += 1

            return data[: self.page_size]  # Return page data without OOB

        except Exception as e:
            self.logger.error(f"Error reading page {page} from block {block}: {str(e)}")
            self.stats["errors"] += 1
            raise

    def write_page(self, block, page, data):
        """
        Write data to a page in the NAND hardware.

        Args:
            block (int): Block number
            page (int): Page number within the block
            data (bytes): Data to write to the page
        """
        if not self.is_initialized:
            raise RuntimeError("NAND hardware not initialized")

        if block >= self.num_blocks or page >= self.pages_per_block:
            raise ValueError(f"Invalid block/page: {block}/{page}")

        if len(data) > self.page_size:
            raise ValueError(f"Data size ({len(data)}) exceeds page size ({self.page_size})")

        try:
            self.logger.debug(f"Writing page {page} to block {block}")
            self.stats["writes"] += 1

            # Calculate physical address
            row_address = (block * self.pages_per_block) + page

            # Send program command sequence
            self._chip_select(True)
            self._send_command(self.CMD_WRITE_1)

            # Send address cycles (column address = 0, row address)
            self._send_address_cycles(0, row_address)

            # Pad data if needed
            if len(data) < self.page_size:
                data = data + b"\xff" * (self.page_size - len(data))

            # Write data
            self._write_data(data)

            # Generate OOB data (typically would include ECC here)
            oob_data = b"\xff" * self.oob_size
            self._write_data(oob_data)

            # Send program confirm command
            self._send_command(self.CMD_WRITE_2)

            self._chip_select(False)

            # Wait for program operation to complete
            self._wait_ready()

            # Check for program errors
            status = self._read_status()
            if status & self.STATUS_FAIL:
                self.logger.warning(f"Program error detected in block {block}, page {page}")
                self.stats["errors"] += 1
                raise IOError(f"Program operation failed for block {block}, page {page}")

        except Exception as e:
            self.logger.error(f"Error writing page {page} to block {block}: {str(e)}")
            self.stats["errors"] += 1
            raise

    def erase_block(self, block):
        """
        Erase a block in the NAND hardware.

        Args:
            block (int): Block number to erase
        """
        if not self.is_initialized:
            raise RuntimeError("NAND hardware not initialized")

        if block >= self.num_blocks:
            raise ValueError(f"Invalid block: {block}")

        try:
            self.logger.debug(f"Erasing block {block}")
            self.stats["erases"] += 1

            # Calculate row address for the block
            row_address = block * self.pages_per_block

            # Send erase command sequence
            self._chip_select(True)
            self._send_command(self.CMD_ERASE_1)

            # Send row address (only block address needed)
            self._send_row_address(row_address)

            # Send erase confirm command
            self._send_command(self.CMD_ERASE_2)

            self._chip_select(False)

            # Wait for erase operation to complete
            self._wait_ready()

            # Check for erase errors
            status = self._read_status()
            if status & self.STATUS_FAIL:
                self.logger.warning(f"Erase error detected in block {block}")
                self.stats["errors"] += 1
                raise IOError(f"Erase operation failed for block {block}")

        except Exception as e:
            self.logger.error(f"Error erasing block {block}: {str(e)}")
            self.stats["errors"] += 1
            raise

    def get_status(self, block=None, page=None):
        """
        Get status information from the NAND hardware.

        Args:
            block (int, optional): Block number to check
            page (int, optional): Page number to check

        Returns:
            dict: Status information including ready state, error flags, etc.
        """
        if not self.is_initialized:
            raise RuntimeError("NAND hardware not initialized")

        try:
            # Read device status register
            status_byte = self._read_status()

            # Basic status info from status register
            status = {
                "ready": (status_byte & self.STATUS_READY) != 0,
                "write_protected": (status_byte & self.STATUS_WRITE_PROTECT) == 0,
                "error": (status_byte & self.STATUS_FAIL) != 0,
                "raw_status": status_byte,
                "stats": {
                    "reads": self.stats["reads"],
                    "writes": self.stats["writes"],
                    "erases": self.stats["erases"],
                    "errors": self.stats["errors"],
                },
            }

            # Get block-specific information if requested
            if block is not None:
                if block >= self.num_blocks:
                    raise ValueError(f"Invalid block: {block}")

                # Read block information (e.g., erase count, bad block status)
                # This would typically be stored in a specific page of the block
                # or in a separate metadata area
                try:
                    block_info = self._read_block_metadata(block)
                    status["block_info"] = block_info
                except Exception as e:
                    self.logger.warning(f"Could not read block metadata for block {block}: {str(e)}")
                    status["block_info"] = {"error": str(e)}

                # Get page-specific information if requested
                if page is not None:
                    if page >= self.pages_per_block:
                        raise ValueError(f"Invalid page: {page}")

                    try:
                        page_info = self._read_page_metadata(block, page)
                        status["page_info"] = page_info
                    except Exception as e:
                        self.logger.warning(f"Could not read page metadata for block {block}, page {page}: {str(e)}")
                        status["page_info"] = {"error": str(e)}

            return status

        except Exception as e:
            self.logger.error(f"Error getting NAND status: {str(e)}")
            raise

    # Hardware-specific private methods

    def _init_hardware_interface(self):
        """
        Initialize the hardware communication interface.

        This method uses a platform-independent approach and should be adapted
        for specific hardware platforms as needed.
        """
        try:
            # First try to import and use SPI if appropriate for the platform
            try:
                self._init_spi()
                self.logger.debug(f"SPI interface initialized with device {self.spi_device}")
            except ImportError:
                self.logger.warning("SPI module not available, using simulated hardware")
                self._init_simulated_hardware()

        except Exception as e:
            self.logger.error(f"Failed to initialize hardware interface: {str(e)}")
            # Fall back to simulation
            self.logger.warning("Falling back to simulated hardware")
            self._init_simulated_hardware()

    def _init_spi(self):
        """
        Initialize the SPI interface if available on the platform.

        This is a platform-specific method and may need to be adapted
        for different operating systems and hardware.
        """
        try:
            # Attempt to import spidev - this will only work on platforms
            # that support it (like Linux with proper modules)
            import spidev

            self.spi = spidev.SpiDev()
            self.spi.open(0, self.cs_pin)  # SPI bus 0, CS pin
            self.spi.max_speed_hz = self.spi_speed
            self.spi.mode = 0  # CPOL=0, CPHA=0

        except ImportError:
            self.logger.warning("spidev module not available")
            raise ImportError("SPI interface not supported on this platform")

    def _init_simulated_hardware(self):
        """Initialize a simulated hardware interface for testing and development."""
        self.logger.info("Using simulated hardware interface")

        class SimulatedHardware:
            def __init__(self):
                self.data = {}  # Simulated flash memory

            def transfer(self, data_out):
                """Simulate SPI transfer."""
                # In a real device, this would interact with hardware
                # Here we just return a predefined response
                return [0xFF] * len(data_out)

            def select(self, active):
                """Simulate chip select."""
                pass

            def close(self):
                """Close the simulated interface."""
                pass

        self.hw_controller = SimulatedHardware()

    def _close_hardware_interface(self):
        """Close the hardware communication interface."""
        if self.spi is not None:
            try:
                self.spi.close()
                self.spi = None
            except Exception as e:
                self.logger.warning(f"Error closing SPI interface: {str(e)}")

        if self.hw_controller is not None:
            try:
                self.hw_controller.close()
                self.hw_controller = None
            except Exception as e:
                self.logger.warning(f"Error closing hardware controller: {str(e)}")

    def _reset_device(self):
        """Reset the NAND device."""
        self._chip_select(True)
        self._send_command(self.CMD_RESET)
        self._chip_select(False)

        # Wait for reset to complete
        time.sleep(0.001)  # 1ms reset time
        self._wait_ready()

    def _read_device_id(self):
        """
        Read the device ID from the NAND flash.

        Returns:
            int: Device ID
        """
        self._chip_select(True)
        self._send_command(self.CMD_READ_ID)
        self._send_address(0x00)  # Address 0x00 for device ID

        # Read 4 bytes of ID data
        id_bytes = self._read_data(4)
        self._chip_select(False)

        # Convert bytes to integer
        device_id = 0
        for i, b in enumerate(id_bytes):
            device_id |= b << (i * 8)

        return device_id

    def _configure_device(self):
        """Configure the NAND device based on parameters."""
        # Read parameter page
        self._chip_select(True)
        self._send_command(self.CMD_READ_PARAM)
        self._send_address(0x00)

        # Wait for operation to complete
        self._wait_ready()

        # Read parameter data
        param_data = self._read_data(256)  # Parameter page is typically 256 bytes
        self._chip_select(False)

        # Parse parameter data and configure the device
        # This would include setting timing, features, etc.
        # For now, we'll just log the first few bytes
        self.logger.debug(f"Parameter page data (first 16 bytes): {param_data[:16].hex()}")

    def _send_command(self, command):
        """
        Send a command to the NAND device.

        Args:
            command (int): Command byte
        """
        if self.spi is not None:
            self.spi.xfer2([command])
        elif self.hw_controller is not None:
            self.hw_controller.transfer([command])

    def _send_address(self, address):
        """
        Send a single address byte to the NAND device.

        Args:
            address (int): Address byte
        """
        if self.spi is not None:
            self.spi.xfer2([address])
        elif self.hw_controller is not None:
            self.hw_controller.transfer([address])

    def _send_address_cycles(self, column_address, row_address):
        """
        Send address cycles to the NAND device.

        Args:
            column_address (int): Column address (within page)
            row_address (int): Row address (page and block)
        """
        # Send column address (typically 2 bytes for large page devices)
        self._send_address(column_address & 0xFF)
        self._send_address((column_address >> 8) & 0xFF)

        # Send row address (typically 3 bytes)
        self._send_address(row_address & 0xFF)
        self._send_address((row_address >> 8) & 0xFF)
        self._send_address((row_address >> 16) & 0xFF)

    def _send_row_address(self, row_address):
        """
        Send row address cycles to the NAND device.

        Args:
            row_address (int): Row address (page and block)
        """
        # Send row address (typically 3 bytes)
        self._send_address(row_address & 0xFF)
        self._send_address((row_address >> 8) & 0xFF)
        self._send_address((row_address >> 16) & 0xFF)

    def _read_data(self, length):
        """
        Read data from the NAND device.

        Args:
            length (int): Number of bytes to read

        Returns:
            bytes: Data read from the device
        """
        # In real SPI NAND, you'd first send a "read data" command (0x03)
        result = bytearray()

        # Read data in chunks to avoid large transfers
        chunk_size = 1024
        for i in range(0, length, chunk_size):
            size = min(chunk_size, length - i)

            # Send dummy bytes to receive data
            if self.spi is not None:
                chunk = self.spi.xfer2([0] * size)
            elif self.hw_controller is not None:
                chunk = self.hw_controller.transfer([0] * size)
            else:
                # Fallback to simulated data
                chunk = [0xFF] * size

            result.extend(chunk)

        return bytes(result)

    def _write_data(self, data):
        """
        Write data to the NAND device.

        Args:
            data (bytes): Data to write
        """
        # In real SPI NAND, the data is sent after the address cycles

        # Write data in chunks to avoid large transfers
        chunk_size = 1024
        for i in range(0, len(data), chunk_size):
            chunk = data[i : i + chunk_size]

            if self.spi is not None:
                self.spi.xfer2(list(chunk))
            elif self.hw_controller is not None:
                self.hw_controller.transfer(list(chunk))

    def _read_status(self):
        """
        Read the status register from the NAND device.

        Returns:
            int: Status register value
        """
        self._chip_select(True)
        self._send_command(self.CMD_READ_STATUS)

        # Send dummy byte to receive status
        if self.spi is not None:
            status = self.spi.xfer2([0])[0]
        elif self.hw_controller is not None:
            status = self.hw_controller.transfer([0])[0]
        else:
            # Fallback to simulated status (ready, no errors)
            status = self.STATUS_READY

        self._chip_select(False)
        return status

    def _wait_ready(self, timeout=1.0):
        """
        Wait for the NAND device to be ready.

        Args:
            timeout (float): Timeout in seconds

        Raises:
            TimeoutError: If device is not ready within timeout period
        """
        start_time = time.time()

        while True:
            status = self._read_status()

            if status & self.STATUS_READY:
                return  # Device is ready

            if time.time() - start_time > timeout:
                raise TimeoutError(f"NAND device not ready after {timeout} seconds")

            # Small delay to avoid hammering the device
            time.sleep(0.001)

    def _chip_select(self, select):
        """
        Control the chip select line.

        Args:
            select (bool): True to select (active), False to deselect
        """
        if self.hw_controller is not None:
            self.hw_controller.select(select)
        # For spidev, CS is handled automatically during transfers

    def _read_block_metadata(self, block):
        """
        Read metadata for a specific block.

        Args:
            block (int): Block number

        Returns:
            dict: Block metadata
        """
        # In a real implementation, this would read from a reserved area
        # or from a specific page in the block that stores metadata
        # For now, we'll return dummy data

        return {"erase_count": random.randint(0, 1000), "is_bad": False, "last_updated": time.time() - random.randint(0, 3600)}

    def _read_page_metadata(self, block, page):
        """
        Read metadata for a specific page.

        Args:
            block (int): Block number
            page (int): Page number

        Returns:
            dict: Page metadata
        """
        # In a real implementation, this would read from the OOB area
        # or from a specific metadata page
        # For now, we'll return dummy data

        return {
            "write_count": random.randint(0, 10),
            "last_written": time.time() - random.randint(0, 3600),
            "has_valid_data": True,
        }


@contextmanager
def nand_operation_context(nand_interface, operation_name):
    """
    Context manager for NAND operations with error handling and logging.

    Args:
        nand_interface: NANDInterface instance
        operation_name: Name of the operation for logging
    """
    logger = logging.getLogger(__name__)

    try:
        logger.debug(f"Starting NAND operation: {operation_name}")
        start_time = time.time()
        yield
        elapsed_time = (time.time() - start_time) * 1000
        logger.debug(f"Completed NAND operation: {operation_name} in {elapsed_time:.2f}ms")
    except Exception as e:
        logger.error(f"Error during NAND operation {operation_name}: {str(e)}")
        raise
