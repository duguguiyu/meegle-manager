"""
Chart API for Meegle SDK
"""

import logging
from typing import Dict, Any, Optional

from ..client.base_client import BaseAPIClient
from ..models.base_models import ChartData, APIError

logger = logging.getLogger(__name__)


class ChartAPI:
    """
    Chart API client for managing Meegle charts
    
    Provides methods to:
    - Get chart details
    - Retrieve chart data
    - Query chart information
    
    Note:
        Chart API has special handling for performance and concurrency:
        - Uses 5-minute timeout (300 seconds) instead of default 30 seconds
        - Disables retry mechanism to prevent concurrency issues
        - Uses 10-second base delay between requests
        
        This is required because chart requests are very slow and the server
        does not allow concurrent chart requests.
    """
    
    def __init__(self, client: BaseAPIClient):
        """
        Initialize Chart API
        
        Args:
            client: Base API client instance
        """
        self.client = client
    
    def get_chart_details(self, chart_id: str) -> Dict[str, Any]:
        """
        Get detailed chart data
        
        Args:
            chart_id: Chart ID to retrieve
            
        Returns:
            Chart data dictionary
            
        Raises:
            APIError: If chart retrieval fails
        """
        endpoint = f"{self.client.project_key}/measure/{chart_id}"
        
        logger.info(f"Fetching chart details for ID: {chart_id}")
        
        try:
            data = self.client.get(
                endpoint=endpoint,
                description=f"fetch chart {chart_id}",
                base_delay=10.0,  # Chart requests need much longer delay due to strict rate limits
                disable_retry=True,  # Disable retry for chart requests to avoid concurrency issues
                custom_timeout=300  # Use 5-minute timeout for chart requests as they can be very slow
            )
            
            logger.info(f"Successfully retrieved chart data for ID: {chart_id}")
            logger.debug(f"Chart data keys: {list(data.keys())}")
            
            if 'chart_data_list' in data:
                chart_list_length = len(data.get('chart_data_list', []))
                logger.info(f"Chart data list contains {chart_list_length} items")
            
            return data
            
        except APIError as e:
            logger.error(f"Failed to retrieve chart {chart_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error retrieving chart {chart_id}: {e}")
            raise APIError(f"Failed to retrieve chart: {e}")
    
    def get_chart_info(self, chart_id: str) -> Optional[ChartData]:
        """
        Get basic chart information
        
        Args:
            chart_id: Chart ID to retrieve
            
        Returns:
            ChartData object or None if not found
        """
        try:
            raw_data = self.get_chart_details(chart_id)
            
            # Extract basic chart info
            chart_info = {
                'chart_id': chart_id,
                'name': raw_data.get('name', ''),
                'chart_type': raw_data.get('chart_type', 'unknown'),
                'data': raw_data
            }
            
            return ChartData.from_dict(chart_info)
            
        except APIError:
            logger.warning(f"Chart {chart_id} not found or inaccessible")
            return None
    
    def list_charts(self, project_key: Optional[str] = None) -> Dict[str, Any]:
        """
        List available charts for a project
        
        Args:
            project_key: Project key (uses default if not provided)
            
        Returns:
            List of available charts
            
        Note:
            This method may need adjustment based on actual Meegle API
        """
        project = project_key or self.client.project_key
        endpoint = f"{project}/measures"
        
        try:
            data = self.client.get(
                endpoint=endpoint,
                description="list charts",
                disable_retry=True,  # Disable retry for chart requests to avoid concurrency issues
                custom_timeout=300  # Use 5-minute timeout for chart requests as they can be very slow
            )
            
            logger.info(f"Retrieved chart list for project: {project}")
            return data
            
        except APIError as e:
            logger.error(f"Failed to list charts for project {project}: {e}")
            raise
    
    def validate_chart_data(self, chart_data: Dict[str, Any]) -> bool:
        """
        Validate chart data structure
        
        Args:
            chart_data: Chart data to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not chart_data:
            logger.warning("Empty chart data")
            return False
        
        if 'chart_data_list' not in chart_data:
            logger.warning("Missing chart_data_list in chart data")
            return False
        
        chart_list = chart_data['chart_data_list']
        if not isinstance(chart_list, list) or len(chart_list) == 0:
            logger.warning("Empty or invalid chart_data_list")
            return False
        
        logger.debug("Chart data validation passed")
        return True 