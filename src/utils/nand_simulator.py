# src/utils/nand_simulator.py

import logging
import random
import time

import numpy as np

from .nand_interface import NANDInterface


class NANDSimulator(NANDInterface):
    """
    NAND flash simulator for testing and development.

    This class implements the NANDInterface and simulates the behavior of
    a NAND flash memory device, including errors, latency, and wear effects.
    It provides an in-memory simulation for testing NAND controller code
    without actual hardware.
    """

    def __init__(self, config):
        """
        Initialize the NAND simulator.

        Args:
            config: Configuration object with NAND parameters
        """
        self.logger = logging.getLogger(__name__)

        # NAND configuration parameters
        self.page_size = config.get("nand_config", {}).get("page_size", 4096)
        self.oob_size = config.get("nand_config", {}).get("oob_size", 64)
        self.block_size = config.get("nand_config", {}).get("block_size", 256)
        self.num_blocks = config.get("nand_config", {}).get("num_blocks", 1024)
        self.pages_per_block = config.get("nand_config", {}).get("pages_per_block", 64)

        # Simulation parameters
        self.sim_config = config.get("simulation", {})
        self.error_rate = self.sim_config.get("error_rate", 0.0001)
        self.latency = self.sim_config.get("latency", {})
        self.read_latency = self.latency.get("read", 0.0001)  # seconds
        self.write_latency = self.latency.get("write", 0.0005)  # seconds
        self.erase_latency = self.latency.get("erase", 0.002)  # seconds

        # Internal simulator state
        self.data = {}  # Simulated NAND memory
        self.erase_counts = np.zeros(self.num_blocks, dtype=np.uint32)
        self.bad_blocks = np.zeros(self.num_blocks, dtype=bool)
        self.is_initialized = False

    def initialize(self):
        """Initialize the simulated NAND device."""
        self.logger.info("Initializing NAND simulator")

        # Generate some initial bad blocks (typical for real NAND)
        bad_block_rate = self.sim_config.get("initial_bad_block_rate", 0.002)
        num_initial_bad = int(self.num_blocks * bad_block_rate)
        initial_bad_blocks = random.sample(range(self.num_blocks), num_initial_bad)

        for block in initial_bad_blocks:
            self.bad_blocks[block] = True
            self.logger.debug(f"Block {block} marked as initially bad")

        self.is_initialized = True
        self.logger.info(f"NAND simulator initialized with {num_initial_bad} initial bad blocks")

    def shutdown(self):
        """Shut down the simulated NAND device."""
        if not self.is_initialized:
            return

        self.logger.info("Shutting down NAND simulator")
        self.data.clear()
        self.is_initialized = False

    def read_page(self, block, page):
        """
        Read a page from the simulated NAND.

        Args:
            block (int): Block number
            page (int): Page number within the block

        Returns:
            bytes: Raw data read from the page
        """
        if not self.is_initialized:
            raise RuntimeError("NAND simulator not initialized")

        if block >= self.num_blocks or page >= self.pages_per_block:
            raise ValueError(f"Invalid block/page: {block}/{page}")

        # Simulate read latency
        time.sleep(self.read_latency)

        # Check if the block is bad
        if self.bad_blocks[block]:
            self.logger.warning(f"Attempt to read from bad block {block}")
            return b"\xFF" * self.page_size  # Bad blocks typically read as all 1's

        # Get data from the simulated memory
        key = (block, page)
        if key not in self.data:
            # Unwritten pages typically read as all 1's
            return b"\xFF" * self.page_size

        # Retrieve the stored data
        data = bytearray(self.data[key])

        # Simulate random bit errors based on error rate
        if random.random() < self.error_rate * self.erase_counts[block]:
            # Introduce 1-3 bit errors
            num_errors = random.randint(1, 3)
            for _ in range(num_errors):
                pos = random.randint(0, len(data) - 1)
                bit = random.randint(0, 7)
                data[pos] ^= 1 << bit  # Flip a random bit

            self.logger.debug(f"Simulated {num_errors} bit errors in block {block}, page {page}")

        return bytes(data)

    def write_page(self, block, page, data):
        """
        Write data to a page in the simulated NAND.

        Args:
            block (int): Block number
            page (int): Page number within the block
            data (bytes): Data to write to the page
        """
        if not self.is_initialized:
            raise RuntimeError("NAND simulator not initialized")

        if block >= self.num_blocks or page >= self.pages_per_block:
            raise ValueError(f"Invalid block/page: {block}/{page}")

        if len(data) > self.page_size:
            raise ValueError(f"Data size ({len(data)}) exceeds page size ({self.page_size})")

        # Check if the block is bad
        if self.bad_blocks[block]:
            self.logger.warning(f"Attempt to write to bad block {block}")
            return  # Silently fail, like some real NAND chips

        # Simulate write latency
        time.sleep(self.write_latency)

        # In real NAND, you must erase a block before writing to it again
        key = (block, page)
        if key in self.data:
            if any(b != 0xFF for b in self.data[key]):
                self.logger.warning(f"Writing to unerased page {page} in block {block}")
                # Some NAND allows programming 1->0 but not 0->1
                # Simulate this by performing a logical AND with existing data
                new_data = bytearray(data)
                for i in range(len(new_data)):
                    if i < len(self.data[key]):
                        new_data[i] &= self.data[key][i]
                data = bytes(new_data)

        # Pad data to page size if necessary
        if len(data) < self.page_size:
            data = data + b"\xFF" * (self.page_size - len(data))

        # Store the data in our simulated memory
        self.data[key] = data

        # Simulate program failures (more likely in heavily used blocks)
        fail_probability = self.error_rate * self.erase_counts[block] * 10
        if random.random() < fail_probability:
            # Simulate a program failure by corrupting some bits
            corrupted_data = bytearray(data)
            num_errors = random.randint(1, 5)
            for _ in range(num_errors):
                pos = random.randint(0, len(corrupted_data) - 1)
                bit = random.randint(0, 7)
                corrupted_data[pos] ^= 1 << bit

            self.data[key] = bytes(corrupted_data)
            self.logger.debug(f"Simulated program failure in block {block}, page {page}")

            # Mark block as bad if it's severely worn
            if self.erase_counts[block] > 10000:  # Typical NAND endurance ~10,000 cycles
                self.bad_blocks[block] = True
                self.logger.info(f"Block {block} marked bad due to wear-out")

    def erase_block(self, block):
        """
        Erase a block in the simulated NAND.

        Args:
            block (int): Block number to erase
        """
        if not self.is_initialized:
            raise RuntimeError("NAND simulator not initialized")

        if block >= self.num_blocks:
            raise ValueError(f"Invalid block: {block}")

        # Check if the block is bad
        if self.bad_blocks[block]:
            self.logger.warning(f"Attempt to erase bad block {block}")
            return  # Silently fail, like some real NAND chips

        # Simulate erase latency
        time.sleep(self.erase_latency)

        # Remove all pages in this block from our simulated memory
        for page in range(self.pages_per_block):
            key = (block, page)
            if key in self.data:
                self.data[key] = b"\xFF" * self.page_size  # Erased state is all 1's

        # Increment erase count for this block
        self.erase_counts[block] += 1

        # Simulate erase failures (more likely in heavily used blocks)
        if self.erase_counts[block] > 1000:  # Start introducing failures after 1000 erases
            fail_probability = (self.erase_counts[block] - 1000) / 9000  # Linear increase in failure rate
            if random.random() < fail_probability:
                # Simulate an erase failure by leaving some cells unprogrammed
                for page in range(self.pages_per_block):
                    key = (block, page)
                    if key in self.data:
                        corrupted_data = bytearray(b"\xFF" * self.page_size)
                        num_errors = random.randint(1, 20)
                        for _ in range(num_errors):
                            pos = random.randint(0, self.page_size - 1)
                            bit = random.randint(0, 7)
                            corrupted_data[pos] &= ~(1 << bit)  # Set a random bit to 0

                        self.data[key] = bytes(corrupted_data)

                self.logger.debug(f"Simulated erase failure in block {block}")

                # Mark block as bad if it's severely worn
                if self.erase_counts[block] > 9000:  # Near end of life
                    self.bad_blocks[block] = True
                    self.logger.info(f"Block {block} marked bad due to erase failure")

    def get_status(self, block=None, page=None):
        """
        Get status information from the simulated NAND.

        Args:
            block (int, optional): Block number to check
            page (int, optional): Page number to check

        Returns:
            dict: Status information
        """
        if not self.is_initialized:
            raise RuntimeError("NAND simulator not initialized")

        status = {
            "ready": True,
            "write_protected": False,
            "error": False,
            "simulator_info": {
                "total_blocks": self.num_blocks,
                "bad_blocks": int(np.sum(self.bad_blocks)),
                "total_memory_usage": len(self.data) * self.page_size,
            },
        }

        if block is not None:
            if block >= self.num_blocks:
                raise ValueError(f"Invalid block: {block}")

            status.update(
                {
                    "block_info": {
                        "is_bad": self.bad_blocks[block],
                        "erase_count": int(self.erase_counts[block]),
                        "remaining_life": max(0, 10000 - self.erase_counts[block]) / 10000,
                    }
                }
            )

            if page is not None:
                if page >= self.pages_per_block:
                    raise ValueError(f"Invalid page: {page}")

                key = (block, page)
                status["page_info"] = {
                    "is_written": key in self.data,
                    "is_erased": key not in self.data or all(b == 0xFF for b in self.data[key]),
                }

        return status

    def execute_sequence(self, sequence):
        """
        Execute a sequence of operations for testing.

        Args:
            sequence (list): List of operation dictionaries

        Returns:
            list: Results of the operations
        """
        if not self.is_initialized:
            raise RuntimeError("NAND simulator not initialized")

        results = []

        for op in sequence:
            op_type = op.get("type")
            block = op.get("block", 0)
            page = op.get("page", 0)
            data = op.get("data", b"")

            if op_type == "read":
                result = self.read_page(block, page)
                results.append(result)
            elif op_type == "write":
                self.write_page(block, page, data)
                results.append(None)
            elif op_type == "erase":
                self.erase_block(block)
                results.append(None)
            elif op_type == "status":
                result = self.get_status(block, page)
                results.append(result)
            else:
                self.logger.warning(f"Unknown operation type: {op_type}")
                results.append(None)

        return results

    def get_output(self):
        """
        Get the current state of the simulated NAND memory.

        Returns:
            dict: Current memory state
        """
        if not self.is_initialized:
            raise RuntimeError("NAND simulator not initialized")

        return {
            "data": {str(key): self.data[key] for key in self.data},
            "bad_blocks": self.bad_blocks.tolist(),
            "erase_counts": self.erase_counts.tolist(),
        }

    def set_error_rate(self, rate):
        """
        Set the error rate for the simulator.

        Args:
            rate (float): Error rate (0.0 to 1.0)
        """
        if rate < 0.0 or rate > 1.0:
            raise ValueError("Error rate must be between 0.0 and 1.0")

        self.error_rate = rate
        self.logger.info(f"Error rate set to {rate}")

    def mark_block_bad(self, block):
        """
        Manually mark a block as bad.

        Args:
            block (int): Block number to mark as bad
        """
        if block >= self.num_blocks:
            raise ValueError(f"Invalid block: {block}")

        self.bad_blocks[block] = True
        self.logger.info(f"Block {block} manually marked as bad")

    def set_latency(self, operation, latency):
        """
        Set the simulated latency for an operation.

        Args:
            operation (str): Operation type ('read', 'write', or 'erase')
            latency (float): Latency in seconds
        """
        if operation == "read":
            self.read_latency = latency
        elif operation == "write":
            self.write_latency = latency
        elif operation == "erase":
            self.erase_latency = latency
        else:
            raise ValueError(f"Unknown operation type: {operation}")

        self.logger.info(f"{operation.capitalize()} latency set to {latency} seconds")
