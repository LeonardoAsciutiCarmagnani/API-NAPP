import os
import logging
from logging.handlers import RotatingFileHandler

class CustomFormatter(logging.Formatter):
    def format(self, record):
        if record.levelname == 'INFO':
            record.levelname = 'API'
        elif record.levelname == 'ERROR':
            record.levelname = 'API-ERROR'
        elif record.levelname == 'CRITICAL':
            record.levelname = 'API-CRITICAL'
        return super().format(record)

def api_setup_logger():
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger('api_logger')
    if not logger.hasHandlers():
        logger.setLevel(logging.INFO)
        file_handler = logging.FileHandler(os.path.join(log_dir, 'logs.log'))
        file_handler.setLevel(logging.INFO)
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        formatter = CustomFormatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger

def basic_setup_logger():
    log_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
    os.makedirs(log_directory, exist_ok=True)

    logger = logging.getLogger('normal_logger')
    if not logger.hasHandlers():
        logger.setLevel(logging.INFO)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        log_filename = os.path.join(log_directory, 'logs.log')
        file_handler = RotatingFileHandler(log_filename, maxBytes=10*1024*1024, backupCount=5)
        file_handler.setLevel(logging.INFO)

        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger
