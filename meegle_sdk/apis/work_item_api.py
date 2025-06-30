"""
Work Item API for Meegle SDK
"""

import logging
from typing import Dict, Any, List, Optional

from ..client.base_client import BaseAPIClient
from ..models.base_models import WorkItem, APIError

logger = logging.getLogger(__name__)


class WorkItemAPI:
    """
    Work Item API client for managing Meegle work items
    
    Provides methods to:
    - Get work items/projects
    - Query work item details
    - List work items with filters
    """
    
    def __init__(self, client: BaseAPIClient):
        """
        Initialize Work Item API
        
        Args:
            client: Base API client instance
        """
        self.client = client
    
    def get_projects(self, item_types: Optional[List[str]] = None,
                    page_size: int = 100, page_num: int = 1) -> List[Dict[str, Any]]:
        """
        Get work items/projects with pagination
        
        Args:
            item_types: List of item types to filter (e.g., ['story', 'epic'])
            page_size: Number of items per page
            page_num: Page number to retrieve
            
        Returns:
            List of work items
            
        Raises:
            APIError: If work item retrieval fails
        """
        endpoint = f"{self.client.project_key}/work_items"
        
        # Default item types
        if item_types is None:
            item_types = ["story", "epic", "task", "bug"]
        
        params = {
            "item_types": item_types,
            "page_size": page_size,
            "page_num": page_num
        }
        
        logger.info(f"Fetching work items (page {page_num}, size {page_size})")
        
        try:
            data = self.client.get(
                endpoint=endpoint,
                params=params,
                description=f"fetch work items page {page_num}",
                base_delay=1.5
            )
            
            items = data.get('items', [])
            total_count = data.get('total_count', 0)
            
            logger.info(f"Retrieved {len(items)} work items (total: {total_count})")
            
            return items
            
        except APIError as e:
            logger.error(f"Failed to retrieve work items: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error retrieving work items: {e}")
            raise APIError(f"Failed to retrieve work items: {e}")
    
    def get_all_projects(self, item_types: Optional[List[str]] = None,
                        page_size: int = 100) -> List[Dict[str, Any]]:
        """
        Get all work items across all pages
        
        Args:
            item_types: List of item types to filter
            page_size: Number of items per page
            
        Returns:
            Complete list of work items
        """
        all_items = []
        page_num = 1
        
        logger.info("Fetching all work items across pages")
        
        while True:
            try:
                items = self.get_projects(
                    item_types=item_types,
                    page_size=page_size,
                    page_num=page_num
                )
                
                if not items:
                    break
                
                all_items.extend(items)
                
                # Check if we got fewer items than page size (last page)
                if len(items) < page_size:
                    break
                
                page_num += 1
                
            except APIError as e:
                logger.error(f"Error fetching work items page {page_num}: {e}")
                break
        
        logger.info(f"Retrieved {len(all_items)} total work items")
        return all_items
    
    def get_work_item_details(self, item_key: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a specific work item
        
        Args:
            item_key: Work item key/ID
            
        Returns:
            Work item details or None if not found
        """
        endpoint = f"{self.client.project_key}/work_items/{item_key}"
        
        try:
            data = self.client.get(
                endpoint=endpoint,
                description=f"fetch work item {item_key}"
            )
            
            logger.info(f"Retrieved details for work item: {item_key}")
            return data
            
        except APIError as e:
            logger.warning(f"Work item {item_key} not found or inaccessible: {e}")
            return None
    
    def search_work_items(self, query: str, item_types: Optional[List[str]] = None,
                         limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search work items by query
        
        Args:
            query: Search query string
            item_types: List of item types to search in
            limit: Maximum number of results
            
        Returns:
            List of matching work items
        """
        endpoint = f"{self.client.project_key}/work_items/search"
        
        json_data = {
            "query": query,
            "limit": limit
        }
        
        if item_types:
            json_data["item_types"] = item_types
        
        try:
            data = self.client.post(
                endpoint=endpoint,
                json_data=json_data,
                description=f"search work items: {query}"
            )
            
            results = data.get('items', [])
            logger.info(f"Found {len(results)} work items matching query: {query}")
            
            return results
            
        except APIError as e:
            logger.error(f"Work item search failed: {e}")
            raise
    
    def create_work_item_objects(self, items_data: List[Dict[str, Any]]) -> List[WorkItem]:
        """
        Convert raw work item data to WorkItem objects
        
        Args:
            items_data: List of raw work item data
            
        Returns:
            List of WorkItem objects
        """
        work_items = []
        
        for item_data in items_data:
            try:
                work_item = WorkItem.from_dict(item_data)
                work_items.append(work_item)
            except Exception as e:
                logger.warning(f"Failed to parse work item: {e}")
                continue
        
        logger.info(f"Created {len(work_items)} WorkItem objects")
        return work_items 