import colorlog
import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logger(log_file, max_file_size=2048*2048, backup_count=5):
    """
    Set up the logger with color formatting for console output and file logging.
    
    :param log_file: Name of the log file
    :param max_file_size: Maximum size of the log file before it rolls over
    :param backup_count: Number of backup files to keep
    :return: Configured logger
    """
    logger = colorlog.getLogger()
    logger.setLevel(logging.INFO)

    # Console Handler (with colors)
    console_handler = colorlog.StreamHandler()
    console_handler.setFormatter(colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s - %(levelname)s - %(message)s',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        },
        secondary_log_colors={},
        style='%'
    ))

    # Ensure log directory exists
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # File Handler
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=max_file_size, 
        backupCount=backup_count
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    ))

    # Add both handlers to the logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
