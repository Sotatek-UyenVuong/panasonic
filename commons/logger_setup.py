import logging
import os
from logging.handlers import RotatingFileHandler
import sys
from pathlib import Path

def setup_logger(
    logger_name: str, 
    log_file: str, 
    level: int = logging.DEBUG,
    max_bytes: int = 10**7, 
    backup_count: int = 2,
    log_to_console: bool = True
) -> logging.Logger:
    log_file = os.path.abspath(log_file)
    
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    logger.handlers = []
    try:
        log_dir = os.path.dirname(log_file)
        os.makedirs(log_dir, exist_ok=True)
        
        file_handler = RotatingFileHandler(log_file, mode='a', maxBytes=max_bytes, backupCount=backup_count)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)', '%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Error setting up file handler: {str(e)}")
    if log_to_console:
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    return logger