"""
Meegle SDK - Python SDK for Meegle API
"""

from .client.meegle_client import MeegleClient
from .auth.token_manager import TokenManager
from .models.base_models import APIError

__version__ = "0.1.0"
__all__ = ["MeegleSDK", "TokenManager", "APIError"]


class MeegleSDK:
    """
    Main SDK class providing access to all Meegle APIs
    
    Usage:
        sdk = MeegleSDK(
            plugin_id="your_plugin_id",
            plugin_secret="your_plugin_secret", 
            user_key="your_user_key"
        )
        
        # Access different APIs
        chart_data = sdk.charts.get_chart_details("chart_id")
        work_items = sdk.work_items.get_work_items()
        users = sdk.users.get_all_users()
    """
    
    def __init__(self, plugin_id: str = None, plugin_secret: str = None, 
                 user_key: str = None, project_key: str = None, 
                 base_url: str = None, **kwargs):
        """
        Initialize Meegle SDK
        
        Args:
            plugin_id: Meegle plugin ID
            plugin_secret: Meegle plugin secret
            user_key: Meegle user key
            project_key: Meegle project key
            base_url: Meegle API base URL
            **kwargs: Additional configuration options
        """
        self._client = MeegleClient(
            plugin_id=plugin_id,
            plugin_secret=plugin_secret,
            user_key=user_key,
            project_key=project_key,
            base_url=base_url,
            **kwargs
        )
    
    @property
    def charts(self):
        """Access to Chart APIs"""
        return self._client.charts
    
    @property
    def work_items(self):
        """Access to Work Item APIs"""
        return self._client.work_items
    
    @property
    def teams(self):
        """Access to Team APIs"""
        return self._client.teams
    
    @property
    def users(self):
        """Access to User APIs"""
        return self._client.users
    
    def get_client(self):
        """Get the underlying client instance"""
        return self._client 