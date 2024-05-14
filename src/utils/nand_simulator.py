class NANDSimulator:
    def __init__(self, config):
        self.page_size = config.get('page_size', 4096)
        self.block_size = config.get('block_size', 256)
        self.num_blocks = config.get('num_blocks', 1024)
        self.pages_per_block = self.block_size // self.page_size
        self.data = {}

    def execute_sequence(self, sequence):
        for operation in sequence:
            if operation == 'write':
                self._write_page()
            elif operation == 'read':
                self._read_page()
            elif operation == 'erase':
                self._erase_block()

    def get_output(self):
        return list(self.data.values())

    def _write_page(self):
        # Simulate writing a page
        pass

    def _read_page(self):
        # Simulate reading a page
        pass

    def _erase_block(self):
        # Simulate erasing a block
        pass