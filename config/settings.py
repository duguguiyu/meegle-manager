"""
Meegle Manager Configuration Settings
"""
import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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