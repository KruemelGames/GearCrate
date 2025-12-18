"""
Centralized logging system for GearCrate
Supports console output with emojis and optional file logging
"""
import logging
import os
import sys
from datetime import datetime

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


class CleanFormatter(logging.Formatter):
    """Custom formatter without emojis - clean professional output"""

    def format(self, record):
        # Ignore emoji parameter completely - clean output only
        return super().format(record)


def setup_logger(name, log_file=None, level=logging.INFO):
    """
    Setup centralized logger with console and optional file output

    Args:
        name: Logger name (usually __name__)
        log_file: Optional path to log file (default: None)
        level: Logging level (default: logging.INFO)

    Returns:
        Configured logger instance

    Example:
        logger = setup_logger(__name__)
        logger.info("Message")
        logger.warning("Warning")
        logger.error("Error")
    """
    logger = logging.getLogger(name)

    # Don't add handlers if they already exist (prevents duplicates)
    if logger.handlers:
        return logger

    logger.setLevel(level)
    logger.propagate = False  # Don't propagate to root logger

    # Console Handler - clean output without emojis
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_format = CleanFormatter('%(message)s')
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File Handler (optional) without emojis
    if log_file:
        # Ensure log directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

    return logger


def get_logger(name):
    """
    Get existing logger or create new one with default settings

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logger(name)
    return logger
