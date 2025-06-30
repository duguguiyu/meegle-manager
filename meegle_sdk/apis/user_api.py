"""
User API for Meegle SDK
"""

import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Set

from ..client.base_client import BaseAPIClient
from ..models.base_models import User, APIError
from ..apis.team_api import TeamAPI
from config.settings import get_cache_config

logger = logging.getLogger(__name__)


class UserAPI:
    """
    User API client for managing Meegle users with permanent caching
    
    Provides methods to:
    - Get user details by keys
    - Get all users with intelligent caching
    - Manage permanent user cache
    - Get name to email mappings
    """
    
    def __init__(self, client: BaseAPIClient, team_api: TeamAPI, 
                 cache_file: Optional[str] = None):
        """
        Initialize User API
        
        Args:
            client: Base API client instance
            team_api: Team API instance for getting user keys
            cache_file: Optional custom cache file path
        """
        self.client = client
        self.team_api = team_api
        
        # Set up cache file
        cache_config = get_cache_config()
        self.cache_file = cache_file or cache_config['user_cache_file']
        self._ensure_cache_dir()
        
        # User cache (permanent - 10 years expiry)
        self.user_cache: Dict[str, Dict] = {}
        self.cache_expiry_hours = 24 * 365 * 10  # 10 years
        
        self._load_cache_from_file()
    
    def _ensure_cache_dir(self):
        """Ensure cache directory exists"""
        cache_path = Path(self.cache_file)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _load_cache_from_file(self):
        """Load user cache from file"""
        if Path(self.cache_file).exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    self.user_cache = cache_data.get('users', {})
                    
                    if self.user_cache:
                        cache_age_days = (time.time() - cache_data.get('timestamp', 0)) / (24 * 3600)
                        logger.info(f"Loaded {len(self.user_cache)} users from permanent cache "
                                  f"(age: {cache_age_days:.1f} days)")
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load user cache: {e}")
                self.user_cache = {}
    
    def _save_cache_to_file(self):
        """Save user cache to file"""
        try:
            cache_data = {
                'timestamp': time.time(),
                'users': self.user_cache,
                'note': 'Permanent cache for user data - expires in 10 years'
            }
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
                
            logger.debug("Saved user cache to file")
            
        except IOError as e:
            logger.warning(f"Failed to save user cache: {e}")
    
    def get_user_details(self, user_keys: List[str]) -> List[Dict[str, Any]]:
        """
        Get user details by user keys
        
        Args:
            user_keys: List of user keys to retrieve
            
        Returns:
            List of user detail dictionaries
            
        Raises:
            APIError: If user retrieval fails
        """
        endpoint = "user/query"
        json_data = {"user_keys": user_keys}
        
        logger.info(f"Fetching details for {len(user_keys)} users")
        
        try:
            data = self.client.post(
                endpoint=endpoint,
                json_data=json_data,
                description=f"fetch details for {len(user_keys)} users",
                base_delay=1.5
            )
            
            # Handle different response formats
            users = data if isinstance(data, list) else data.get('users', [])
            
            logger.info(f"Retrieved details for {len(users)} users")
            
            return users
            
        except APIError as e:
            logger.error(f"Failed to retrieve user details: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error retrieving user details: {e}")
            raise APIError(f"Failed to retrieve user details: {e}")
    
    def get_users_by_keys(self, user_keys: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Get users by keys with caching
        
        Args:
            user_keys: List of user keys
            
        Returns:
            Dictionary mapping user_key to user data
        """
        result = {}
        missing_keys = []
        
        # Check cache first
        for key in user_keys:
            if key in self.user_cache:
                result[key] = self.user_cache[key]
            else:
                missing_keys.append(key)
        
        # Fetch missing users from API
        if missing_keys:
            logger.info(f"Fetching {len(missing_keys)} users from API (cache miss)")
            
            # Process in batches to avoid overwhelming the API
            batch_size = 50
            
            for i in range(0, len(missing_keys), batch_size):
                batch = missing_keys[i:i + batch_size]
                
                try:
                    users = self.get_user_details(batch)
                    
                    for user in users:
                        user_key = user.get('user_key')
                        if user_key:
                            self.user_cache[user_key] = user
                            result[user_key] = user
                    
                    # Add delay between batches
                    if i + batch_size < len(missing_keys):
                        time.sleep(2.0)
                        
                except APIError as e:
                    logger.error(f"Failed to fetch user batch: {e}")
                    continue
            
            # Save cache after fetching new users
            if missing_keys:
                self._save_cache_to_file()
        
        return result
    
    def get_all_users(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all users with intelligent incremental updates
        
        Returns:
            Dictionary mapping user_key to user data
        """
        logger.info("Getting all users with intelligent caching")
        
        # Get all user keys from teams
        try:
            user_keys = self.team_api.extract_all_user_keys()
        except APIError as e:
            logger.error(f"Failed to get user keys from teams: {e}")
            return self.user_cache
        
        if not user_keys:
            logger.warning("No users found in any team")
            return self.user_cache
        
        # Check which users are missing from cache
        cached_keys = set(self.user_cache.keys())
        new_user_keys = user_keys - cached_keys
        
        if new_user_keys:
            logger.info(f"Found {len(new_user_keys)} new users to add to permanent cache")
            self.get_users_by_keys(list(new_user_keys))
        else:
            logger.info(f"All {len(user_keys)} users already in permanent cache - no API calls needed!")
        
        return self.user_cache
    
    def get_name_to_email_mapping(self) -> Dict[str, str]:
        """
        Get mapping from user names (Chinese) to email addresses
        
        Returns:
            Dictionary mapping name_cn to email
        """
        name_to_email = {}
        
        for user in self.user_cache.values():
            name_cn = user.get('name_cn', '')
            email = user.get('email', '')
            
            if name_cn and email:
                name_to_email[name_cn] = email
        
        logger.info(f"Created name-to-email mapping for {len(name_to_email)} users")
        
        return name_to_email
    
    def create_user_objects(self, users_data: List[Dict[str, Any]]) -> List[User]:
        """
        Convert raw user data to User objects
        
        Args:
            users_data: List of raw user data
            
        Returns:
            List of User objects
        """
        users = []
        
        for user_data in users_data:
            try:
                user = User.from_dict(user_data)
                users.append(user)
            except Exception as e:
                logger.warning(f"Failed to parse user: {e}")
                continue
        
        logger.info(f"Created {len(users)} User objects")
        return users
    
    def search_users_by_name(self, name: str) -> List[Dict[str, Any]]:
        """
        Search users by name (Chinese or English)
        
        Args:
            name: Name to search for
            
        Returns:
            List of matching users
        """
        matching_users = []
        
        name_lower = name.lower()
        
        for user in self.user_cache.values():
            name_cn = user.get('name_cn', '').lower()
            name_en = user.get('name_en', '').lower()
            
            if name_lower in name_cn or name_lower in name_en:
                matching_users.append(user)
        
        logger.info(f"Found {len(matching_users)} users matching name: {name}")
        return matching_users
    
    def clear_cache(self):
        """Clear the user cache"""
        self.user_cache = {}
        try:
            Path(self.cache_file).unlink(missing_ok=True)
            logger.info("User cache cleared")
        except IOError as e:
            logger.warning(f"Failed to clear user cache: {e}") 