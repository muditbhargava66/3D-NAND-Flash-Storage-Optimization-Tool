import logging
from pathlib import Path

def setup_logger(name, config):
    logger = logging.getLogger(name)
    logger.setLevel(config.get('logging', {}).get('level', 'INFO'))

    log_file = config.get('logging', {}).get('file', '/logs/app.log')
    log_dir = Path(log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(console_handler)

    return logger

def get_logger(name):
    return logging.getLogger(name)