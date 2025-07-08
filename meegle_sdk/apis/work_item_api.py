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
        - Projects: 642ec373f4af608bb3cb1c90
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
                - ["642ec373f4af608bb3cb1c90"] for projects
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

    def get_work_item_by_id(self, work_item_id: str, work_item_type_key: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific work item by ID using the query endpoint
        
        Args:
            work_item_id: Work item ID to retrieve
            work_item_type_key: Work item type key (e.g., "642ec373f4af608bb3cb1c90" for projects)
            
        Returns:
            Work item data dictionary or None if not found
        """
        try:
            # Use the correct query endpoint for getting work item details
            endpoint = f"{self.client.project_key}/work_item/{work_item_type_key}/query"
            
            # Use POST method with work item IDs in the request body
            json_data = {
                "work_item_ids": [work_item_id]
            }
            
            data = self.client.post(
                endpoint=endpoint,
                json_data=json_data,
                description=f"fetch work item {work_item_id} of type {work_item_type_key}",
            )
            
            # Handle response format
            if isinstance(data, dict):
                if 'items' in data and data['items']:
                    return data['items'][0]
                elif 'data' in data and data['data']:
                    return data['data'][0]
                elif 'results' in data and data['results']:
                    return data['results'][0]
                elif 'work_items' in data and data['work_items']:
                    return data['work_items'][0]
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
                - ["642ec373f4af608bb3cb1c90"] for projects
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
        return self.get_all_work_items(work_item_type_keys=["642ec373f4af608bb3cb1c90"])

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
        
        # First try to get by ID directly
        story = self.get_work_item_by_id(story_id)
        if story:
            return story
            
        # If direct lookup fails, search through all stories
        stories = self.get_stories()
        
        for story in stories:
            story_id_field = story.get('id') or story.get('fields', {}).get('id')
            if story_id_field == story_id:
                logger.info(f"Found story with ID {story_id}")
                return story
                
        logger.warning(f"Story with ID {story_id} not found")
        return None 