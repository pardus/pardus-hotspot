#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pardus Hotspot Logging Configuration
Log file path: ~/.config/pardus/pardus-hotspot/logs/app.log
"""

import logging
import logging.handlers
from pathlib import Path


def setup_logging():

    # Create log directory
    log_dir = Path.home() / ".config" / "pardus" / "pardus-hotspot" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "app.log"

    # Logger config
    logger = logging.getLogger('pardus-hotspot')
    logger.setLevel(logging.INFO)

    # If handlers already added, skip setup
    if logger.handlers:
        return logger

    # File handler (10MB, 3 backup files)
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=3,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)

    # Console handler (only WARNING and above to console)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)

    # Detailed format for file
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Simple format for console
    console_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Initial log message
    logger.info("Pardus Hotspot logging system initialized")
    logger.debug(f"Log file: {log_file}")

    return logger


def get_logger():

    return logging.getLogger('pardus-hotspot')


# Init logging on import
_logger = setup_logging()
