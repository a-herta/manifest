"""Logging utilities for Steam Manifest Tool."""

import logging
from colorlog import ColoredFormatter

from ..core.config import Config


def setup_logger(debug: bool = False) -> logging.Logger:
    """Set up and configure the logger.
    
    Args:
        debug: Whether to enable debug mode
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(__name__)
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create console handler
    handler = logging.StreamHandler()
    formatter = ColoredFormatter(Config.LOG_FORMAT)
    handler.setFormatter(formatter)
    
    # Configure logger
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    logger.propagate = False
    
    return logger