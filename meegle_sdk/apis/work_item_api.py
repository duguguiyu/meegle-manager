"""
Work Item API for Meegle
"""

import logging
from typing import Dict, Any, List, Optional

from meegle_sdk.client.base_client import BaseAPIClient

logger = logging.getLogger(__name__)


class WorkItemAPI:
    """
    Work Item API client for managing Meegle work items
    
    Provides methods to:
    - Get work items by type (projects, stories/features)
    - Query work items with filtering
    - Retrieve work item details
    
    Note:
        Work item type IDs:
        - Projects: 642ebe04168eea39eeb0d34a
        - Stories/Features: story
    """
    
    def __init__(self, client: BaseAPIClient):
        """
        Initialize Work Item API
        
        Args:
            client: Base API client instance
        """
        self.client = client

    def get_work_items(self, work_item_type_keys: List[str], 
                      page_size: int = 100, page_num: int = 1) -> List[Dict[str, Any]]:
        """
        Get work items with pagination using the correct Meegle API endpoint
        
        Args:
            work_item_type_keys: List of work item type keys (required)
                - ["642ebe04168eea39eeb0d34a"] for projects
                - ["story"] for features/stories
            page_size: Number of items per page (max 200)
            page_num: Page number starting from 1 (default is 1)
            
        Returns:
            List of work items
            
        Raises:
            APIError: If work item retrieval fails
            ValueError: If work_item_type_keys is empty
        """
        if not work_item_type_keys:
            raise ValueError("work_item_type_keys cannot be empty")
            
        # Validate pagination parameters
        if page_size > 200:
            raise ValueError("page_size cannot exceed 200")
        if page_num < 1:
            raise ValueError("page_num must be >= 1")
            
        try:
            # Use the correct Meegle API endpoint
            endpoint = f"{self.client.project_key}/work_item/filter"
            
            # Prepare parameters
            params = {
                "page_size": page_size,
                "page_num": page_num,
                "work_item_type_keys": work_item_type_keys
            }
            
            logger.info(f"Fetching work items from endpoint: {endpoint}")
            logger.info(f"Parameters: {params}")
            
            data = self.client.post(
                endpoint=endpoint,
                json_data=params,
                description=f"fetch work items with types {work_item_type_keys or 'all'}",
            )
            
            # Handle different response formats
            if isinstance(data, dict):
                if 'items' in data:
                    items = data['items']
                elif 'data' in data:
                    items = data['data']
                elif 'results' in data:
                    items = data['results']
                elif 'work_items' in data:
                    items = data['work_items']
                else:
                    # Assume the response itself is the items array
                    items = data if isinstance(data, list) else [data]
            elif isinstance(data, list):
                items = data
            else:
                items = []
            
            logger.info(f"Successfully retrieved {len(items)} work items")
            return items
            
        except Exception as e:
            logger.error(f"Failed to get work items: {e}")
            return []

    def get_work_item_by_id(self, work_item_id: str, work_item_type_key: str = "story") -> Optional[Dict[str, Any]]:
        """
        Get a specific work item by ID using the query endpoint
        
        Args:
            work_item_id: Work item ID to retrieve
            work_item_type_key: Work item type key (e.g., "story", "project")
            
        Returns:
            Work item data dictionary or None if not found
        """
        try:
            # Use the efficient query endpoint for getting work item details
            endpoint = f"{self.client.project_key}/work_item/{work_item_type_key}/query"
            
            # Use POST method with work item IDs in the request body
            json_data = {
                "work_item_ids": [str(work_item_id)],
                "expand": {
                    "need_workflow": True,
                    "need_multi_text": False,
                    "relation_fields_detail": True,
                    "need_user_detail": False
                }
            }
            
            data = self.client.post(
                endpoint=endpoint,
                json_data=json_data,
                description=f"fetch work item {work_item_id} of type {work_item_type_key}",
            )
            
            # Handle response format - the API returns data in 'data' field
            if isinstance(data, dict):
                if 'data' in data and isinstance(data['data'], list) and data['data']:
                    return data['data'][0]
                elif 'data' in data and isinstance(data['data'], dict):
                    return data['data']
            elif isinstance(data, list) and data:
                return data[0]
            
            logger.warning(f"Work item {work_item_id} not found")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get work item {work_item_id}: {e}")
            return None

    def get_all_work_items(self, work_item_type_keys: List[str],
                          page_size: int = 100) -> List[Dict[str, Any]]:
        """
        Get all work items across all pages
        
        Args:
            work_item_type_keys: List of work item type keys (required)
                - ["642ebe04168eea39eeb0d34a"] for projects
                - ["story"] for features/stories
            page_size: Number of items per page (max 200)
            
        Returns:
            Complete list of work items (empty list if no items or API fails)
        """
        all_items = []
        page_num = 1
        
        logger.info(f"Fetching all work items for types: {work_item_type_keys or 'all'}")
        
        try:
            while True:
                try:
                    items = self.get_work_items(
                        work_item_type_keys=work_item_type_keys,
                        page_size=page_size,
                        page_num=page_num
                    )
                    
                    if not items:
                        # No more items, break the loop
                        break
                    
                    all_items.extend(items)
                    logger.info(f"Page {page_num}: Retrieved {len(items)} items, total so far: {len(all_items)}")
                    
                    # If we got fewer items than page_size, we've reached the end
                    if len(items) < page_size:
                        break
                    
                    page_num += 1
                    
                    # Safety check to prevent infinite loops
                    if page_num > 100:  # Maximum 10,000 items
                        logger.warning("Reached maximum page limit (100), stopping pagination")
                        break
                        
                except Exception as e:
                    logger.error(f"Error on page {page_num}: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"Error in get_all_work_items: {e}")
            
        logger.info(f"Total work items retrieved: {len(all_items)}")
        return all_items

    def get_projects(self) -> List[Dict[str, Any]]:
        """
        Get all project work items
        
        Returns:
            List of project work items
        """
        logger.info("Fetching all project work items")
        return self.get_all_work_items(work_item_type_keys=["642ebe04168eea39eeb0d34a"])

    def get_stories(self) -> List[Dict[str, Any]]:
        """
        Get all story/feature work items
        
        Returns:
            List of story/feature work items
        """
        logger.info("Fetching all story/feature work items")
        return self.get_all_work_items(work_item_type_keys=["story"])

    def find_project_by_code(self, project_code: str) -> Optional[Dict[str, Any]]:
        """
        Find a project by its code
        
        Args:
            project_code: Project code to search for
            
        Returns:
            Project work item or None if not found
        """
        logger.info(f"Searching for project with code: {project_code}")
        projects = self.get_projects()
        
        for project in projects:
            # Check various possible field names for project code
            project_fields = project.get('fields', {}) if 'fields' in project else project
            
            code_fields = ['code', 'project_code', 'projectCode', 'name', 'title']
            for field in code_fields:
                if field in project_fields and project_fields[field] == project_code:
                    logger.info(f"Found project with code {project_code}: {project.get('id', 'unknown')}")
                    return project
                    
        logger.warning(f"Project with code {project_code} not found")
        return None

    def find_story_by_id(self, story_id: str) -> Optional[Dict[str, Any]]:
        """
        Find a story/feature by its ID
        
        Args:
            story_id: Story ID to search for
            
        Returns:
            Story work item or None if not found
        """
        logger.info(f"Searching for story with ID: {story_id}")
        
        # Use the efficient get_work_item_by_id method directly
        return self.get_work_item_by_id(story_id, "story") 

    def get_work_items_in_view(self, view_id: str, page_size: int = 200, page_num: int = 1) -> Dict[str, Any]:
        """
        Get work items in a specific view
        
        Args:
            view_id: View ID to get work items from
            page_size: Number of items per page (max 200)
            page_num: Page number (starting from 1)
            
        Returns:
            Dictionary containing view data and work item IDs
        """
        logger.info(f"Getting work items in view: {view_id}")
        
        endpoint = f"{self.client.project_key}/fix_view/{view_id}"
        params = {
            'page_size': page_size,
            'page_num': page_num
        }
        
        try:
            data = self.client.get(endpoint, params=params)
            logger.info(f"Successfully retrieved view data for {view_id}")
            return data
            
        except Exception as e:
            logger.error(f"Failed to get work items in view {view_id}: {e}")
            raise
    
    def get_all_work_items_in_view(self, view_id: str) -> List[int]:
        """
        Get all work item IDs in a view (handles pagination)
        
        Args:
            view_id: View ID to get work items from
            
        Returns:
            List of work item IDs
        """
        logger.info(f"Getting all work items in view: {view_id}")
        
        all_work_item_ids = []
        page_num = 1
        page_size = 200
        
        while True:
            try:
                response = self.get_work_items_in_view(view_id, page_size, page_num)
                
                if not response:
                    break
                
                # Handle different response formats
                if 'data' in response:
                    view_data = response['data']
                    work_item_ids = view_data.get('work_item_id_list', [])
                else:
                    # Direct response format
                    work_item_ids = response.get('work_item_id_list', [])
                
                if not work_item_ids:
                    break
                
                all_work_item_ids.extend(work_item_ids)
                logger.info(f"Page {page_num}: Retrieved {len(work_item_ids)} work item IDs")
                
                # Check if we have more pages
                pagination = response.get('pagination', {})
                total = pagination.get('total', 0)
                current_count = page_num * page_size
                
                if current_count >= total:
                    break
                
                page_num += 1
                
            except Exception as e:
                logger.error(f"Error getting work items in view {view_id} page {page_num}: {e}")
                break
        
        logger.info(f"Retrieved total {len(all_work_item_ids)} work item IDs from view {view_id}")
        return all_work_item_ids
    
    def get_work_items_by_ids(self, work_item_ids: List[int], work_item_type_key: str = "story") -> List[Dict[str, Any]]:
        """
        Get work items by their IDs using the efficient query API
        
        Args:
            work_item_ids: List of work item IDs to retrieve
            work_item_type_key: Work item type key (e.g., "story", "project")
            
        Returns:
            List of work item details
        """
        if not work_item_ids:
            return []
        
        logger.info(f"Getting {len(work_item_ids)} work items by IDs")
        
        all_work_items = []
        
        # Process in batches (API supports up to 50 work items at a time)
        batch_size = 50
        for i in range(0, len(work_item_ids), batch_size):
            batch_ids = work_item_ids[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}: {len(batch_ids)} work items")
            
            try:
                # Use the efficient query endpoint directly
                endpoint = f"{self.client.project_key}/work_item/{work_item_type_key}/query"
                
                # Convert IDs to strings if they're integers
                work_item_ids_str = [str(id_) for id_ in batch_ids]
                
                json_data = {
                    "work_item_ids": work_item_ids_str,
                    "expand": {
                        "need_workflow": True,
                        "need_multi_text": False,
                        "relation_fields_detail": True,
                        "need_user_detail": False
                    }
                }
                
                data = self.client.post(
                    endpoint=endpoint,
                    json_data=json_data,
                    description=f"fetch {len(batch_ids)} work items of type {work_item_type_key}",
                )
                
                # Handle response format - the API returns data in 'data' field
                batch_items = []
                if isinstance(data, dict):
                    if 'data' in data and isinstance(data['data'], list):
                        batch_items = data['data']
                    elif isinstance(data.get('data'), dict):
                        # Single item wrapped in data
                        batch_items = [data['data']]
                elif isinstance(data, list):
                    batch_items = data
                
                all_work_items.extend(batch_items)
                logger.info(f"Found {len(batch_items)} matching work items in batch")
                
            except Exception as e:
                logger.error(f"Error getting work items batch {i//batch_size + 1}: {e}")
                continue
        
        logger.info(f"Retrieved {len(all_work_items)} work items by IDs")
        return all_work_items 