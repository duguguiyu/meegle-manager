"""
Project Manager Examples

This module demonstrates how to use the ProjectManager business layer
to update project code and description for project work items.
"""

import sys
import os
import logging

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from meegle_sdk import MeegleSDK
from meegle_business import ProjectManager
from config.settings import get_meegle_config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def update_project_code_and_description_example():
    """
    Example of updating both project code and description
    """
    logger.info("=== Project Manager: Update Code and Description ===")
    
    try:
        # Initialize SDK and project manager
        config = get_meegle_config()
        sdk = MeegleSDK(
            user_key=config['user_key'],
            plugin_token=config['plugin_token'],
            project_key=config['project_key']
        )
        
        project_manager = ProjectManager(sdk)
        
        # Example project ID (replace with actual project ID)
        project_id = 123456  # Replace with actual project ID
        
        # Update both project code and description
        result = project_manager.update_project_info(
            project_id=project_id,
            code="PRJ-001",
            description="Updated project description via Project Manager"
        )
        
        logger.info(f"Project updated successfully: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to update project: {e}")
        raise


def update_project_code_only_example():
    """
    Example of updating only the project code
    """
    logger.info("=== Project Manager: Update Code Only ===")
    
    try:
        # Initialize SDK and project manager
        config = get_meegle_config()
        sdk = MeegleSDK(
            user_key=config['user_key'],
            plugin_token=config['plugin_token'],
            project_key=config['project_key']
        )
        
        project_manager = ProjectManager(sdk)
        
        # Example project ID (replace with actual project ID)
        project_id = 123456  # Replace with actual project ID
        
        # Update only project code using convenience method
        result = project_manager.update_project_code(
            project_id=project_id,
            code="PRJ-002"
        )
        
        logger.info(f"Project code updated successfully: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to update project code: {e}")
        raise


def update_project_description_only_example():
    """
    Example of updating only the project description
    """
    logger.info("=== Project Manager: Update Description Only ===")
    
    try:
        # Initialize SDK and project manager
        config = get_meegle_config()
        sdk = MeegleSDK(
            user_key=config['user_key'],
            plugin_token=config['plugin_token'],
            project_key=config['project_key']
        )
        
        project_manager = ProjectManager(sdk)
        
        # Example project ID (replace with actual project ID)
        project_id = 123456  # Replace with actual project ID
        
        # Update only project description using convenience method
        result = project_manager.update_project_description(
            project_id=project_id,
            description="Updated project description only"
        )
        
        logger.info(f"Project description updated successfully: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to update project description: {e}")
        raise


def update_project_with_validation_example():
    """
    Example of updating project with validation
    """
    logger.info("=== Project Manager: Update with Validation ===")
    
    try:
        # Initialize SDK and project manager
        config = get_meegle_config()
        sdk = MeegleSDK(
            user_key=config['user_key'],
            plugin_token=config['plugin_token'],
            project_key=config['project_key']
        )
        
        project_manager = ProjectManager(sdk)
        
        # Example project ID (replace with actual project ID)
        project_id = 123456  # Replace with actual project ID
        
        # Update with validation (checks if project exists first)
        result = project_manager.update_project_with_validation(
            project_id=project_id,
            code="PRJ-003",
            description="Validated project update",
            validate_exists=True
        )
        
        logger.info(f"Project updated with validation: {result}")
        return result
        
    except ValueError as e:
        logger.error(f"Validation failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to update project with validation: {e}")
        raise


def get_project_details_example():
    """
    Example of getting project details
    """
    logger.info("=== Project Manager: Get Project Details ===")
    
    try:
        # Initialize SDK and project manager
        config = get_meegle_config()
        sdk = MeegleSDK(
            user_key=config['user_key'],
            plugin_token=config['plugin_token'],
            project_key=config['project_key']
        )
        
        project_manager = ProjectManager(sdk)
        
        # Example project ID (replace with actual project ID)
        project_id = 123456  # Replace with actual project ID
        
        # Get project details
        details = project_manager.get_project_details(project_id=project_id)
        
        logger.info(f"Project details: {details}")
        
        # Extract current code and description for reference
        current_code = details.get('name', 'N/A')  # Project code is in 'name' field
        current_description = details.get('field_28829a', 'N/A')  # Project description is in 'field_28829a'
        
        logger.info(f"Current project code: {current_code}")
        logger.info(f"Current project description: {current_description}")
        
        return details
        
    except Exception as e:
        logger.error(f"Failed to get project details: {e}")
        raise


def validate_project_exists_example():
    """
    Example of validating project existence
    """
    logger.info("=== Project Manager: Validate Project Exists ===")
    
    try:
        # Initialize SDK and project manager
        config = get_meegle_config()
        sdk = MeegleSDK(
            user_key=config['user_key'],
            plugin_token=config['plugin_token'],
            project_key=config['project_key']
        )
        
        project_manager = ProjectManager(sdk)
        
        # Example project ID (replace with actual project ID)
        project_id = 123456  # Replace with actual project ID
        
        # Validate existence
        exists = project_manager.validate_project_exists(project_id=project_id)
        
        if exists:
            logger.info(f"Project {project_id} exists and is accessible")
        else:
            logger.warning(f"Project {project_id} does not exist or is not accessible")
        
        return exists
        
    except Exception as e:
        logger.error(f"Failed to validate project existence: {e}")
        raise


def find_project_by_code_example():
    """
    Example of finding a project by its code
    """
    logger.info("=== Project Manager: Find Project by Code ===")
    
    try:
        # Initialize SDK and project manager
        config = get_meegle_config()
        sdk = MeegleSDK(
            user_key=config['user_key'],
            plugin_token=config['plugin_token'],
            project_key=config['project_key']
        )
        
        project_manager = ProjectManager(sdk)
        
        # Example project code (replace with actual project code)
        project_code = "PRJ-001"  # Replace with actual project code
        
        # Find project by code
        project = project_manager.find_project_by_code(project_code)
        
        if project:
            project_id = project.get('id', 'unknown')
            logger.info(f"Found project with code {project_code}: ID = {project_id}")
            logger.info(f"Project details: {project}")
        else:
            logger.warning(f"Project with code {project_code} not found")
        
        return project
        
    except Exception as e:
        logger.error(f"Failed to find project by code: {e}")
        raise


def show_field_mapping_example():
    """
    Example of showing the project field mapping
    """
    logger.info("=== Project Manager: Field Mapping ===")
    
    try:
        # Initialize SDK and project manager
        config = get_meegle_config()
        sdk = MeegleSDK(
            user_key=config['user_key'],
            plugin_token=config['plugin_token'],
            project_key=config['project_key']
        )
        
        project_manager = ProjectManager(sdk)
        
        # Get field mapping
        field_mapping = project_manager.get_field_mapping()
        
        logger.info("Project field mapping:")
        logger.info(f"  - Project Code: logical 'code' -> actual '{field_mapping['code']}'")
        logger.info(f"  - Project Description: logical 'description' -> actual '{field_mapping['description']}'")
        
        logger.info("This mapping is based on the export logic analysis:")
        logger.info("  - Project code is stored in the 'name' field")
        logger.info("  - Project description is stored in the 'field_28829a' field")
        
        return field_mapping
        
    except Exception as e:
        logger.error(f"Failed to show field mapping: {e}")
        raise


def main():
    """
    Run all project manager examples
    """
    logger.info("Starting Project Manager Examples")
    
    try:
        # Note: These examples require actual project IDs
        # Replace the placeholder values with real ones from your Meegle instance
        
        logger.info("Note: Please update project_id with actual values")
        logger.info("from your Meegle instance before running.")
        logger.info("Project work item type is: 642ebe04168eea39eeb0d34a")
        
        # Show field mapping first
        show_field_mapping_example()
        
        # Uncomment the examples you want to run:
        
        # validate_project_exists_example()
        # get_project_details_example()
        # find_project_by_code_example()
        # update_project_code_only_example()
        # update_project_description_only_example()
        # update_project_code_and_description_example()
        # update_project_with_validation_example()
        
        logger.info("Project Manager Examples completed")
        
    except Exception as e:
        logger.error(f"Examples failed: {e}")
        raise


if __name__ == "__main__":
    main()