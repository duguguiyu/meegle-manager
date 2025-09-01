"""
Business Layer Work Item Examples

This module demonstrates how to use the business layer WorkItemManager
to update work item name and description.
"""

import sys
import os
import logging

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from meegle_sdk import MeegleSDK
from meegle_business import WorkItemManager
from config.settings import get_meegle_config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def update_work_item_name_and_description_example():
    """
    Example of updating both name and description using business layer
    """
    logger.info("=== Business Layer: Update Name and Description ===")
    
    try:
        # Initialize SDK and business manager
        config = get_meegle_config()
        sdk = MeegleSDK(
            user_key=config['user_key'],
            plugin_token=config['plugin_token'],
            project_key=config['project_key']
        )
        
        work_item_manager = WorkItemManager(sdk)
        
        # Example work item details
        work_item_id = 123456  # Replace with actual work item ID
        work_item_type_key = "task"  # Replace with actual work item type
        
        # Update both name and description
        result = work_item_manager.update_work_item_basic_info(
            work_item_id=work_item_id,
            work_item_type_key=work_item_type_key,
            name="Updated Task Name via Business Layer",
            description="This task has been updated using the business layer manager"
        )
        
        logger.info(f"Work item updated successfully: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to update work item: {e}")
        raise


def update_work_item_name_only_example():
    """
    Example of updating only the name using business layer
    """
    logger.info("=== Business Layer: Update Name Only ===")
    
    try:
        # Initialize SDK and business manager
        config = get_meegle_config()
        sdk = MeegleSDK(
            user_key=config['user_key'],
            plugin_token=config['plugin_token'],
            project_key=config['project_key']
        )
        
        work_item_manager = WorkItemManager(sdk)
        
        # Example work item details
        work_item_id = 123456  # Replace with actual work item ID
        work_item_type_key = "task"  # Replace with actual work item type
        
        # Update only name using convenience method
        result = work_item_manager.update_work_item_name(
            work_item_id=work_item_id,
            work_item_type_key=work_item_type_key,
            name="New Task Name Only"
        )
        
        logger.info(f"Work item name updated successfully: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to update work item name: {e}")
        raise


def update_work_item_description_only_example():
    """
    Example of updating only the description using business layer
    """
    logger.info("=== Business Layer: Update Description Only ===")
    
    try:
        # Initialize SDK and business manager
        config = get_meegle_config()
        sdk = MeegleSDK(
            user_key=config['user_key'],
            plugin_token=config['plugin_token'],
            project_key=config['project_key']
        )
        
        work_item_manager = WorkItemManager(sdk)
        
        # Example work item details
        work_item_id = 123456  # Replace with actual work item ID
        work_item_type_key = "task"  # Replace with actual work item type
        
        # Update only description using convenience method
        result = work_item_manager.update_work_item_description(
            work_item_id=work_item_id,
            work_item_type_key=work_item_type_key,
            description="Updated description only via business layer"
        )
        
        logger.info(f"Work item description updated successfully: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to update work item description: {e}")
        raise


def update_work_item_with_validation_example():
    """
    Example of updating work item with validation
    """
    logger.info("=== Business Layer: Update with Validation ===")
    
    try:
        # Initialize SDK and business manager
        config = get_meegle_config()
        sdk = MeegleSDK(
            user_key=config['user_key'],
            plugin_token=config['plugin_token'],
            project_key=config['project_key']
        )
        
        work_item_manager = WorkItemManager(sdk)
        
        # Example work item details
        work_item_id = 123456  # Replace with actual work item ID
        work_item_type_key = "task"  # Replace with actual work item type
        
        # Update with validation (checks if work item exists first)
        result = work_item_manager.update_work_item_with_validation(
            work_item_id=work_item_id,
            work_item_type_key=work_item_type_key,
            name="Validated Update Name",
            description="This update was validated before execution",
            validate_exists=True
        )
        
        logger.info(f"Work item updated with validation: {result}")
        return result
        
    except ValueError as e:
        logger.error(f"Validation failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to update work item with validation: {e}")
        raise


def get_work_item_details_example():
    """
    Example of getting work item details before updating
    """
    logger.info("=== Business Layer: Get Work Item Details ===")
    
    try:
        # Initialize SDK and business manager
        config = get_meegle_config()
        sdk = MeegleSDK(
            user_key=config['user_key'],
            plugin_token=config['plugin_token'],
            project_key=config['project_key']
        )
        
        work_item_manager = WorkItemManager(sdk)
        
        # Example work item details
        work_item_id = 123456  # Replace with actual work item ID
        work_item_type_key = "task"  # Replace with actual work item type
        
        # Get current details
        details = work_item_manager.get_work_item_details(
            work_item_id=work_item_id,
            work_item_type_key=work_item_type_key
        )
        
        logger.info(f"Work item details: {details}")
        
        # Extract current name and description for reference
        current_name = details.get('name', 'N/A')
        current_description = details.get('description', 'N/A')
        
        logger.info(f"Current name: {current_name}")
        logger.info(f"Current description: {current_description}")
        
        return details
        
    except Exception as e:
        logger.error(f"Failed to get work item details: {e}")
        raise


def validate_work_item_exists_example():
    """
    Example of validating work item existence
    """
    logger.info("=== Business Layer: Validate Work Item Exists ===")
    
    try:
        # Initialize SDK and business manager
        config = get_meegle_config()
        sdk = MeegleSDK(
            user_key=config['user_key'],
            plugin_token=config['plugin_token'],
            project_key=config['project_key']
        )
        
        work_item_manager = WorkItemManager(sdk)
        
        # Example work item details
        work_item_id = 123456  # Replace with actual work item ID
        work_item_type_key = "task"  # Replace with actual work item type
        
        # Validate existence
        exists = work_item_manager.validate_work_item_exists(
            work_item_id=work_item_id,
            work_item_type_key=work_item_type_key
        )
        
        if exists:
            logger.info(f"Work item {work_item_id} exists and is accessible")
        else:
            logger.warning(f"Work item {work_item_id} does not exist or is not accessible")
        
        return exists
        
    except Exception as e:
        logger.error(f"Failed to validate work item existence: {e}")
        raise


def field_mapping_example():
    """
    Example of using custom field mapping
    """
    logger.info("=== Business Layer: Custom Field Mapping ===")
    
    try:
        # Initialize SDK and business manager
        config = get_meegle_config()
        sdk = MeegleSDK(
            user_key=config['user_key'],
            plugin_token=config['plugin_token'],
            project_key=config['project_key']
        )
        
        # Initialize with custom field mapping
        custom_field_mapping = {
            "name": "title",  # Use "title" field for name
            "description": "desc"  # Use "desc" field for description
        }
        
        work_item_manager = WorkItemManager(sdk, field_mapping=custom_field_mapping)
        
        # Show current field mapping
        current_mapping = work_item_manager.get_field_mapping()
        logger.info(f"Current field mapping: {current_mapping}")
        
        # Example work item details
        work_item_id = 123456  # Replace with actual work item ID
        work_item_type_key = "task"  # Replace with actual work item type
        
        # Update using custom field mapping
        result = work_item_manager.update_work_item_basic_info(
            work_item_id=work_item_id,
            work_item_type_key=work_item_type_key,
            name="Updated via Custom Mapping",
            description="Description updated via custom field mapping"
        )
        
        logger.info(f"Work item updated with custom field mapping: {result}")
        
        # Update field mapping at runtime
        work_item_manager.set_field_mapping({
            "name": "work_item_name",
            "description": "work_item_description"
        })
        
        updated_mapping = work_item_manager.get_field_mapping()
        logger.info(f"Updated field mapping: {updated_mapping}")
        
        return result
        
    except Exception as e:
        logger.error(f"Failed field mapping example: {e}")
        raise


def main():
    """
    Run all business layer work item examples
    """
    logger.info("Starting Business Layer Work Item Examples")
    
    try:
        # Note: These examples require actual work item IDs and field keys
        # Replace the placeholder values with real ones from your Meegle instance
        
        logger.info("Note: Please update work_item_id and work_item_type_key")
        logger.info("with actual values from your Meegle instance before running.")
        logger.info("Also adjust field mappings according to your Meegle configuration.")
        
        # Uncomment the examples you want to run:
        
        # validate_work_item_exists_example()
        # get_work_item_details_example()
        # update_work_item_name_only_example()
        # update_work_item_description_only_example()
        # update_work_item_name_and_description_example()
        # update_work_item_with_validation_example()
        # field_mapping_example()
        
        logger.info("Business Layer Work Item Examples completed")
        
    except Exception as e:
        logger.error(f"Examples failed: {e}")
        raise


if __name__ == "__main__":
    main()