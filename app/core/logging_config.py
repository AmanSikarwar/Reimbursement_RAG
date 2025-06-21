"""
Logging configuration for the application.

This module sets up structured logging with appropriate formatters and handlers.
"""

import logging
import logging.config
import os
from datetime import datetime

from app.core.config import settings


def setup_logging():
    """
    Set up logging configuration for the application.

    Creates log directory if it doesn't exist and configures loggers
    with appropriate handlers and formatters.
    """
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    log_filename = f"{log_dir}/app_{datetime.now().strftime('%Y%m%d')}.log"

    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "simple": {"format": "%(levelname)s - %(message)s"},
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "simple",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "detailed",
                "filename": log_filename,
                "maxBytes": 10485760,
                "backupCount": 5,
            },
        },
        "loggers": {
            "": {
                "level": settings.LOG_LEVEL.value,
                "handlers": ["console", "file"],
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "fastapi": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False,
            },
        },
    }

    logging.config.dictConfig(LOGGING_CONFIG)

    logger = logging.getLogger(__name__)
    logger.info("Logging system initialized")
    logger.info(f"Log file: {log_filename}")
    logger.info(f"Log level: {settings.LOG_LEVEL.value}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    Args:
        name: The name for the logger (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
