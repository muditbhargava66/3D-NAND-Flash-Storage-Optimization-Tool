# scripts/performance_test.py

import time
import random
from src.nand_controller import NANDController

def measure_read_performance(nand_controller, num_iterations):
    block = random.randint(0, nand_controller.num_blocks - 1)
    page = random.randint(0, nand_controller.pages_per_block - 1)
    
    start_time = time.time()
    for _ in range(num_iterations):
        nand_controller.read_page(block, page)
    end_time = time.time()
    
    execution_time = end_time - start_time
    throughput = num_iterations / execution_time
    return throughput

def measure_write_performance(nand_controller, num_iterations):
    block = random.randint(0, nand_controller.num_blocks - 1)
    page = random.randint(0, nand_controller.pages_per_block - 1)
    data = bytearray(random.getrandbits(8) for _ in range(nand_controller.page_size))
    
    start_time = time.time()
    for _ in range(num_iterations):
        nand_controller.write_page(block, page, data)
    end_time = time.time()
    
    execution_time = end_time - start_time
    throughput = num_iterations / execution_time
    return throughput

def main():
    config = {
        'page_size': 4096,
        'block_size': 256,
        'num_blocks': 1024,
        'oob_size': 128
    }
    nand_controller = NANDController(config)
    nand_controller.initialize()
    
    num_iterations = 1000
    
    read_throughput = measure_read_performance(nand_controller, num_iterations)
    write_throughput = measure_write_performance(nand_controller, num_iterations)
    
    print(f"Read throughput: {read_throughput:.2f} operations/second")
    print(f"Write throughput: {write_throughput:.2f} operations/second")
    
    nand_controller.shutdown()

if __name__ == '__main__':
    main()