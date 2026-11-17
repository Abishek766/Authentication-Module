"""Centralised logging configuration for the Authentication Service.

Provides a named logger instance (`auth_service`) that is imported by
exception handlers and service components throughout the application.
"""

import logging

LOG_FORMAT: str = "%(asctime)s %(levelname)s %(name)s %(message)s"
LOGGER_NAME: str = "auth_service"


def _configure_logger() -> logging.Logger:
    """Create and configure the auth_service logger."""
    logger = logging.getLogger(LOGGER_NAME)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(handler)
    logger.setLevel(logging.ERROR)
    return logger


logger: logging.Logger = _configure_logger()
