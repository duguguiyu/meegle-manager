"""
Main Meegle Client integrating all APIs
"""

import logging
from typing import Optional

from ..auth.token_manager import TokenManager
from ..client.base_client import BaseAPIClient
from ..apis.chart_api import ChartAPI
from ..apis.work_item_api import WorkItemAPI
from ..apis.team_api import TeamAPI
from ..apis.user_api import UserAPI
from ..apis.workflow_api import WorkflowAPI
from config.settings import get_meegle_config

logger = logging.getLogger(__name__)


class MeegleClient:
    """
    Main Meegle API Client
    
    Integrates all Meegle APIs with centralized configuration and authentication
    
    Provides access to:
    - Chart API
    - Work Item API  
    - Team API
    - User API
    """
    
    def __init__(self, plugin_id: Optional[str] = None, 
                 plugin_secret: Optional[str] = None,
                 user_key: Optional[str] = None, 
                 project_key: Optional[str] = None,
                 base_url: Optional[str] = None, 
                 **kwargs):
        """
        Initialize Meegle Client
        
        Args:
            plugin_id: Meegle plugin ID (uses config default if not provided)
            plugin_secret: Meegle plugin secret (uses config default if not provided)
            user_key: Meegle user key (uses config default if not provided)
            project_key: Meegle project key (uses config default if not provided)
            base_url: Meegle API base URL (uses config default if not provided)
            **kwargs: Additional configuration options
        """
        # Get configuration
        config = get_meegle_config()
        
        # Use provided values or fall back to config
        self.plugin_id = plugin_id or config['plugin_id']
        self.plugin_secret = plugin_secret or config['plugin_secret']
        self.user_key = user_key or config['user_key']
        self.project_key = project_key or config['project_key']
        self.base_url = base_url or config['base_url']
        
        # Additional settings
        self.max_retries = kwargs.get('max_retries', config.get('max_retries', 3))
        self.request_timeout = kwargs.get('request_timeout', config.get('request_timeout', 30))
        
        logger.info(f"Initializing Meegle client for project: {self.project_key}")
        
        # Initialize token manager
        self._token_manager = TokenManager(
            plugin_id=self.plugin_id,
            plugin_secret=self.plugin_secret,
            user_key=self.user_key,
            base_url=self.base_url
        )
        
        # Initialize base API client
        self._base_client = BaseAPIClient(
            token_manager=self._token_manager,
            project_key=self.project_key,
            max_retries=self.max_retries,
            request_timeout=self.request_timeout
        )
        
        # Initialize API instances
        self._team_api = TeamAPI(self._base_client)
        self._chart_api = ChartAPI(self._base_client)
        self._work_item_api = WorkItemAPI(self._base_client)
        self._user_api = UserAPI(self._base_client, self._team_api)
        self._workflow_api = WorkflowAPI(self._base_client)
        
        logger.info("Meegle client initialized successfully")
    
    @property
    def charts(self) -> ChartAPI:
        """Access to Chart API"""
        return self._chart_api
    
    @property
    def work_items(self) -> WorkItemAPI:
        """Access to Work Item API"""
        return self._work_item_api
    
    @property
    def teams(self) -> TeamAPI:
        """Access to Team API"""
        return self._team_api
    
    @property
    def users(self) -> UserAPI:
        """Access to User API"""
        return self._user_api
    
    @property
    def workflows(self) -> WorkflowAPI:
        """Access to Workflow API"""
        return self._workflow_api
    
    @property
    def token_manager(self) -> TokenManager:
        """Access to Token Manager"""
        return self._token_manager
    
    @property
    def base_client(self) -> BaseAPIClient:
        """Access to Base API Client"""
        return self._base_client
    
    def test_connection(self) -> bool:
        """
        Test the connection to Meegle API
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            logger.info("Testing Meegle API connection")
            
            # Try to get teams as a simple connectivity test
            teams = self.teams.get_all_teams()
            
            if teams is not None:
                logger.info(f"Connection test successful - found {len(teams)} teams")
                return True
            else:
                logger.warning("Connection test failed - no teams returned")
                return False
                
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def get_client_info(self) -> dict:
        """
        Get client configuration information
        
        Returns:
            Dictionary with client configuration details
        """
        return {
            'project_key': self.project_key,
            'user_key': self.user_key,
            'base_url': self.base_url,
            'max_retries': self.max_retries,
            'request_timeout': self.request_timeout,
            'token_valid': self._token_manager.is_token_valid()
        }
    
    def refresh_token(self):
        """Force refresh the authentication token"""
        logger.info("Forcing token refresh")
        self._token_manager.invalidate_token()
        # Next API call will automatically get a new token
        
    def clear_all_caches(self):
        """Clear all caches"""
        logger.info("Clearing all caches")
        self._token_manager.invalidate_token()
        self._user_api.clear_cache()
        logger.info("All caches cleared")