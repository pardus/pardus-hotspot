#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pardus Hotspot Logging Configuration
Log file path: ~/.local/share/pardus/pardus-hotspot/logs/app.log
"""

import logging
import logging.handlers
from pathlib import Path


def setup_logging():

    # Create log directory
    log_dir = Path.home() / ".local" / "share" / "pardus" / "pardus-hotspot" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "app.log"

    # Logger config
    logger = logging.getLogger('pardus-hotspot')
    logger.setLevel(logging.INFO)

    # If handlers already added, skip setup
    if logger.handlers:
        return logger

    # File handler (5MB, 2 backup files = max 15MB total)
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=5*1024*1024,  # 5MB
        backupCount=2,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)

    # Console handler (only WARNING and above to console)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)

    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%H:%M:%S'
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

    return logger


def get_logger():

    return logging.getLogger('pardus-hotspot')


# Init logging on import
_logger = setup_logging()
