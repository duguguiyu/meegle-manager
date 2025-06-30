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
    - Get work items
    - Query work item details
    - Search work items
    - List work items with filters
    """
    
    def __init__(self, client: BaseAPIClient):
        """
        Initialize Work Item API
        
        Args:
            client: Base API client instance
        """
        self.client = client
    
    def get_work_items(self, work_item_type_id: Optional[str] = None, 
                      page_size: int = 100, page_num: int = 1) -> List[Dict[str, Any]]:
        """
        Get work items with pagination
        
        Args:
            work_item_type_id: Work item type ID (optional, for filtering by type)
            page_size: Number of items per page
            page_num: Page number to retrieve
            
        Returns:
            List of work items
            
        Raises:
            APIError: If work item retrieval fails
        """
        if work_item_type_id:
            # Work item API with specific type
            endpoint = f"{self.client.project_key}/work_item_types/{work_item_type_id}/work_items"
            logger.info(f"Fetching work items for type: {work_item_type_id}")
        else:
            # General work items endpoint
            endpoint = f"{self.client.project_key}/work_items"
            logger.info("Fetching all work items")
        
        logger.info(f"Using endpoint: {endpoint}")
        
        try:
            # Try the work item endpoint
            params = {}
            if page_size != 100:
                params["page_size"] = page_size
            if page_num != 1:
                params["page_num"] = page_num
                
            data = self.client.get(
                endpoint=endpoint,
                params=params if params else None,
                description=f"fetch work items (page {page_num})",
                base_delay=1.5
            )
            
            # Handle different response formats
            items = data if isinstance(data, list) else data.get('items', data.get('work_items', []))
            
            logger.info(f"Retrieved {len(items)} work items")
            
            return items
            
        except APIError as e:
            logger.warning(f"Primary endpoint failed, trying alternatives: {e}")
            
            # Try alternative endpoint structures
            alternative_endpoints = [
                f"{self.client.project_key}/work_items/all",
                f"{self.client.project_key}/items",
                f"{self.client.project_key}/items/all"
            ]
            
            for alt_endpoint in alternative_endpoints:
                try:
                    logger.info(f"Trying alternative endpoint: {alt_endpoint}")
                    
                    params = {}
                    if work_item_type_id:
                        params["work_item_type_id"] = work_item_type_id
                    if page_size != 100:
                        params["page_size"] = page_size
                    if page_num != 1:
                        params["page_num"] = page_num
                    
                    data = self.client.get(
                        endpoint=alt_endpoint,
                        params=params if params else None,
                        description=f"fetch work items from {alt_endpoint}",
                        base_delay=1.5
                    )
                    
                    items = data if isinstance(data, list) else data.get('items', data.get('work_items', []))
                    logger.info(f"Retrieved {len(items)} work items from alternative endpoint")
                    return items
                    
                except APIError as alt_e:
                    logger.warning(f"Alternative endpoint {alt_endpoint} failed: {alt_e}")
                    continue
            
            # If all endpoints fail, raise the original error
            logger.error(f"All work item endpoints failed. Original error: {e}")
            raise
            
        except Exception as e:
            logger.error(f"Unexpected error retrieving work items: {e}")
            raise APIError(f"Failed to retrieve work items: {e}")
    
    def get_all_work_items(self, work_item_type_id: Optional[str] = None,
                          page_size: int = 100) -> List[Dict[str, Any]]:
        """
        Get all work items across all pages
        
        Args:
            work_item_type_id: Work item type ID (optional, for filtering by type)
            page_size: Number of items per page
            
        Returns:
            Complete list of work items
        """
        all_items = []
        page_num = 1
        
        logger.info("Fetching all work items across pages")
        
        while True:
            try:
                items = self.get_work_items(
                    work_item_type_id=work_item_type_id,
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
    
    def get_work_item_details(self, item_key: str, work_item_type_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a specific work item
        
        Args:
            item_key: Work item key/ID
            work_item_type_id: Work item type ID (optional, for type-specific endpoint)
            
        Returns:
            Work item details or None if not found
        """
        # Try work item type specific endpoint first if type is provided
        if work_item_type_id:
            endpoint = f"{self.client.project_key}/work_item_types/{work_item_type_id}/work_items/{item_key}"
            
            try:
                data = self.client.get(
                    endpoint=endpoint,
                    description=f"fetch work item {item_key} (type-specific)"
                )
                
                logger.info(f"Retrieved details for work item: {item_key}")
                return data
                
            except APIError as e:
                logger.warning(f"Work item {item_key} not found with type endpoint, trying generic endpoint: {e}")
        
        # Try generic endpoint
        try:
            endpoint = f"{self.client.project_key}/work_items/{item_key}"
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