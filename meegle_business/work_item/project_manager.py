"""
Project Manager - Business logic for project work item operations
"""

import logging
from typing import Dict, Any, Optional

from meegle_sdk import MeegleSDK

logger = logging.getLogger(__name__)

# Project work item type constant
PROJECT_WORK_ITEM_TYPE = "642ec373f4af608bb3cb1c90"


class ProjectManager:
    """
    Business layer manager for project work item operations
    
    Provides high-level business methods for:
    - Updating project basic information (code, name/description)
    - Validating project updates
    - Managing project lifecycle
    
    Field Mappings (based on user confirmation):
    - Project Name: 'field_28829a' field (as confirmed by user) ✅ CONFIRMED
    - Project Description: 'description' field (in fields array) ✅ TESTED
    
    Note: User has confirmed that field_28829a definitely exists for project name updates.
    """
    
    def __init__(self, sdk: MeegleSDK):
        """
        Initialize Project Manager
        
        Args:
            sdk: Meegle SDK instance
        """
        self.sdk = sdk
        # Fixed field mapping based on testing and analysis
        self.field_mapping = {
            "name": "field_28829a",   # Project name uses 'field_28829a' field (as confirmed by user)
            "description": "description"  # Project description uses 'description' field
        }
    
    def update_project_info(self, project_id: int, 
                           name: Optional[str] = None, 
                           description: Optional[str] = None) -> Dict[str, Any]:
        """
        Update basic information of a project (name and/or description)
        
        Args:
            project_id: Project work item ID
            name: New project name (optional) - stored in 'field_28829a' field
            description: New project description (optional) - stored in 'description' field
            
        Returns:
            Dictionary containing update response
            
        Raises:
            ValueError: If neither name nor description is provided
            Exception: If update operation fails
            
        Example:
            # Update both name and description
            manager.update_project_info(
                project_id=123,
                name="Non-Document Verification(NG BVN/NIN)",
                description="Updated project description"
            )
            
            # Update only name
            manager.update_project_info(
                project_id=123,
                name="New Project Name"
            )
            
            # Update only description
            manager.update_project_info(
                project_id=123,
                description="New project description"
            )
        """
        logger.info(f"Updating project info for project {project_id}")
        
        # Validate input
        if name is None and description is None:
            raise ValueError("At least one of 'name' or 'description' must be provided")
        
        # Build update fields
        update_fields = []
        
        if name is not None:
            logger.debug(f"Updating project name to: {name}")
            name_field_key = self.field_mapping["name"]
            name_field = self.sdk.workflows.create_field_value_pair(
                field_key=name_field_key,
                field_value=name
            )
            update_fields.append(name_field)
            logger.debug(f"Using field key '{name_field_key}' for project name field")
        
        if description is not None:
            logger.debug(f"Updating project description to: {description}")
            description_field_key = self.field_mapping["description"]
            description_field = self.sdk.workflows.create_field_value_pair(
                field_key=description_field_key,
                field_value=description
            )
            update_fields.append(description_field)
            logger.debug(f"Using field key '{description_field_key}' for project description field")
        
        try:
            # Perform the update using the project work item type
            result = self.sdk.workflows.update_work_item(
                work_item_id=project_id,
                work_item_type_key=PROJECT_WORK_ITEM_TYPE,
                update_fields=update_fields
            )
            
            logger.info(f"Successfully updated project info for project {project_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to update project info for project {project_id}: {e}")
            raise
    
    def update_project_name(self, project_id: int, name: str) -> Dict[str, Any]:
        """
        Update only the project name
        
        Args:
            project_id: Project work item ID
            name: New project name
            
        Returns:
            Dictionary containing update response
        """
        return self.update_project_info(
            project_id=project_id,
            name=name
        )
    
    def update_project_description(self, project_id: int, description: str) -> Dict[str, Any]:
        """
        Update only the project description
        
        Args:
            project_id: Project work item ID
            description: New project description
            
        Returns:
            Dictionary containing update response
        """
        return self.update_project_info(
            project_id=project_id,
            description=description
        )
    
    def get_project_details(self, project_id: int) -> Dict[str, Any]:
        """
        Get detailed information about a project
        
        Args:
            project_id: Project work item ID
            
        Returns:
            Dictionary containing project details
        """
        logger.info(f"Getting details for project {project_id}")
        
        try:
            # Use the project-specific work item type
            result = self.sdk.work_items.get_work_item_by_id(
                work_item_id=str(project_id),
                work_item_type_key=PROJECT_WORK_ITEM_TYPE
            )
            
            logger.info(f"Successfully retrieved details for project {project_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to get details for project {project_id}: {e}")
            raise
    
    def validate_project_exists(self, project_id: int) -> bool:
        """
        Validate that a project exists and is accessible
        
        Args:
            project_id: Project work item ID
            
        Returns:
            True if project exists and is accessible, False otherwise
        """
        logger.debug(f"Validating existence of project {project_id}")
        
        try:
            self.get_project_details(project_id)
            logger.debug(f"Project {project_id} exists and is accessible")
            return True
            
        except Exception as e:
            logger.warning(f"Project {project_id} validation failed: {e}")
            return False
    
    def update_project_with_validation(self, project_id: int,
                                      name: Optional[str] = None, 
                                      description: Optional[str] = None,
                                      validate_exists: bool = True) -> Dict[str, Any]:
        """
        Update project info with optional validation
        
        Args:
            project_id: Project work item ID
            name: New project name (optional)
            description: New project description (optional)
            validate_exists: Whether to validate project exists before updating
            
        Returns:
            Dictionary containing update response
            
        Raises:
            ValueError: If project doesn't exist (when validation is enabled)
        """
        logger.info(f"Updating project {project_id} with validation={validate_exists}")
        
        # Validate project exists if requested
        if validate_exists:
            if not self.validate_project_exists(project_id):
                raise ValueError(f"Project {project_id} does not exist or is not accessible")
        
        # Perform the update
        return self.update_project_info(
            project_id=project_id,
            name=name,
            description=description
        )
    
    def get_field_mapping(self) -> Dict[str, str]:
        """
        Get the current field mapping for projects
        
        Returns:
            Dictionary containing project field mapping
            
        Note:
            This mapping is fixed based on user confirmation:
            - 'name' -> 'field_28829a' (project name stored in field_28829a field)
            - 'description' -> 'description' (project description stored in description field)
        """
        return self.field_mapping.copy()
    
    def find_project_by_code(self, project_code: str) -> Optional[Dict[str, Any]]:
        """
        Find a project by its code using the SDK's built-in method
        
        Args:
            project_code: Project code to search for
            
        Returns:
            Project work item or None if not found
        """
        logger.info(f"Searching for project with code: {project_code}")
        
        try:
            project = self.sdk.work_items.find_project_by_code(project_code)
            if project:
                logger.info(f"Found project with code {project_code}: {project.get('id', 'unknown')}")
            else:
                logger.warning(f"Project with code {project_code} not found")
            return project
            
        except Exception as e:
            logger.error(f"Failed to find project by code {project_code}: {e}")
            raise