"""
Logging utility for the AI Trading System
"""

import logging
import sys
from pathlib import Path
from config.settings import LOG_DIR, LOGGING_CONFIG

def setup_logging():
    """Set up logging configuration"""
    
    # Ensure log directory exists
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    # Configure logging
    log_level = getattr(logging, LOGGING_CONFIG.get('level', 'INFO'))
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    if LOGGING_CONFIG.get('log_to_console', True):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # File handler
    if LOGGING_CONFIG.get('log_to_file', True):
        log_file = LOG_DIR / 'trading_system.log'
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    return root_logger

# Initialize logging when module is imported
logger = setup_logging()