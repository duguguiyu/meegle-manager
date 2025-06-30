"""
Token Manager for Meegle API authentication
"""

import json
import time
import logging
import requests
from pathlib import Path
from typing import Optional, Dict, Any

from ..models.base_models import TokenInfo, AuthenticationError, APIError
from config.settings import get_cache_config

logger = logging.getLogger(__name__)


class TokenManager:
    """
    Manages Meegle API authentication tokens with caching
    
    Features:
    - Automatic token refresh
    - File-based caching
    - Thread-safe operations
    """
    
    def __init__(self, plugin_id: str, plugin_secret: str, user_key: str, 
                 base_url: str, cache_file: Optional[str] = None):
        """
        Initialize Token Manager
        
        Args:
            plugin_id: Meegle plugin ID
            plugin_secret: Meegle plugin secret
            user_key: Meegle user key
            base_url: Meegle API base URL
            cache_file: Optional custom cache file path
        """
        self.plugin_id = plugin_id
        self.plugin_secret = plugin_secret
        self.user_key = user_key
        self.base_url = base_url
        
        # Set up cache file
        cache_config = get_cache_config()
        self.cache_file = cache_file or cache_config['token_cache_file']
        self._ensure_cache_dir()
        
        # Current token info
        self._token_info: Optional[TokenInfo] = None
        self._load_cached_token()
    
    def _ensure_cache_dir(self):
        """Ensure cache directory exists"""
        cache_path = Path(self.cache_file)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _load_cached_token(self):
        """Load token from cache file"""
        try:
            if Path(self.cache_file).exists():
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._token_info = TokenInfo(
                        token=data.get('token', ''),
                        expires_at=data.get('expires_at', 0)
                    )
                    logger.debug("Loaded cached token")
        except (json.JSONDecodeError, IOError, KeyError) as e:
            logger.warning(f"Failed to load cached token: {e}")
            self._token_info = None
    
    def _save_token_to_cache(self, token_info: TokenInfo):
        """Save token to cache file"""
        try:
            cache_data = {
                'token': token_info.token,
                'expires_at': token_info.expires_at,
                'cached_at': time.time()
            }
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2)
            logger.debug("Saved token to cache")
        except IOError as e:
            logger.warning(f"Failed to save token to cache: {e}")
    
    def get_valid_token(self) -> str:
        """
        Get a valid authentication token
        
        Returns:
            Valid authentication token
            
        Raises:
            AuthenticationError: If unable to obtain valid token
        """
        # Check if current token is valid
        if self._token_info and not self._token_info.is_expired:
            logger.debug("Using cached valid token")
            return self._token_info.token
        
        # Request new token
        logger.info("Requesting new authentication token")
        try:
            new_token_info = self._request_new_token()
            self._token_info = new_token_info
            self._save_token_to_cache(new_token_info)
            logger.info("Successfully obtained new token")
            return new_token_info.token
        except Exception as e:
            logger.error(f"Failed to obtain authentication token: {e}")
            raise AuthenticationError(f"Failed to authenticate: {e}")
    
    def _request_new_token(self) -> TokenInfo:
        """
        Request a new token from Meegle API
        
        Returns:
            New token information
            
        Raises:
            AuthenticationError: If token request fails
        """
        url = f"{self.base_url}/authen/plugin_token"
        payload = {
            "plugin_id": self.plugin_id,
            "plugin_secret": self.plugin_secret,
            "user_key": self.user_key
        }
        
        logger.debug(f"Requesting token from: {url}")
        
        try:
            response = requests.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            logger.debug(f"Token response status: {response.status_code}")
            
            if response.status_code != 200:
                raise AuthenticationError(
                    f"Token request failed with status {response.status_code}: {response.text}"
                )
            
            try:
                data = response.json()
            except json.JSONDecodeError as e:
                raise AuthenticationError(f"Invalid JSON response: {e}")
            
            # Check for API errors
            error = data.get('error', {})
            error_code = error.get('code', -1)
            
            if error_code != 0:
                error_msg = error.get('msg', 'Unknown authentication error')
                raise AuthenticationError(f"Authentication failed: {error_msg}")
            
            # Extract token information
            token_data = data.get('data', {})
            if not token_data:
                raise AuthenticationError("No token data in response")
            
            token = token_data.get('token', '')
            expire_time = token_data.get('expire_time', 3600)
            
            if not token:
                raise AuthenticationError("Empty token in response")
            
            expires_at = time.time() + expire_time
            
            logger.info(f"Token obtained successfully, expires in {expire_time} seconds")
            
            return TokenInfo(token=token, expires_at=expires_at)
            
        except requests.RequestException as e:
            raise AuthenticationError(f"Network error during token request: {e}")
        except Exception as e:
            raise AuthenticationError(f"Unexpected error during token request: {e}")
    
    def invalidate_token(self):
        """Invalidate current token and clear cache"""
        self._token_info = None
        try:
            Path(self.cache_file).unlink(missing_ok=True)
            logger.info("Token cache cleared")
        except IOError as e:
            logger.warning(f"Failed to clear token cache: {e}")
    
    def is_token_valid(self) -> bool:
        """Check if current token is valid"""
        return self._token_info is not None and not self._token_info.is_expired 