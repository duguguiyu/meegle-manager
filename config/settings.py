"""
Configuration settings for Meegle Manager
"""

import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging to file
def setup_logging():
    """Setup logging configuration with file output
    
    Returns:
        Path to the log file
    """
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Create log filename with timestamp
    log_filename = f"meegle_api_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    log_file = log_dir / log_filename
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()  # Also log to console
        ]
    )
    
    # Set specific logger levels
    logging.getLogger("meegle_sdk").setLevel(logging.INFO)
    logging.getLogger("meegle_business").setLevel(logging.INFO)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    return log_file

# Default Meegle API Configuration
DEFAULT_MEEGLE_CONFIG = {
    "base_url": "https://project.larksuite.com/open_api",
    "max_retries": 3,
    "request_timeout": 30,
    "cache_expiry_hours": 24 * 365 * 10,  # 10 years for permanent cache
}

# Meegle API Configuration - can be overridden by environment variables
MEEGLE_CONFIG = {
    "plugin_id": os.getenv("MEEGLE_PLUGIN_ID", "MII_AB83624BA588E329"),
    "plugin_secret": os.getenv("MEEGLE_PLUGIN_SECRET", "8D6D56228DE0344EADF5AA243C6E8419"),
    "user_key": os.getenv("MEEGLE_USER_KEY", "7351585340534063109"),
    "project_key": os.getenv("MEEGLE_PROJECT_KEY", "advance_ai"),
    **DEFAULT_MEEGLE_CONFIG
}

# Cache Configuration
CACHE_CONFIG = {
    "token_cache_file": ".token_cache.json",
    "user_cache_file": ".user_cache.json",
    "cache_dir": ".cache"
}

# Export Configuration
EXPORT_CONFIG = {
    "output_dir": "exports",
    "csv_encoding": "utf-8"
}

# Logging Configuration
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "log_file": "meegle_manager.log"
}

def get_meegle_config() -> Dict[str, Any]:
    """Get Meegle configuration with environment variable overrides"""
    return MEEGLE_CONFIG.copy()

def get_cache_config() -> Dict[str, Any]:
    """Get cache configuration"""
    return CACHE_CONFIG.copy()

def get_export_config() -> Dict[str, Any]:
    """Get export configuration"""
    return EXPORT_CONFIG.copy()

def get_logging_config() -> Dict[str, Any]:
    """Get logging configuration"""
    return LOGGING_CONFIG.copy() 