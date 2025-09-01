"""
Update Work Item Examples for Meegle SDK

This module demonstrates how to use the workflow API to update work items
based on the Meegle API documentation.
"""

import sys
import os
import logging

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from meegle_sdk.client.meegle_client import MeegleClient
from meegle_sdk.auth.token_manager import TokenManager
from config.settings import get_meegle_config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def update_work_item_basic_example():
    """
    Basic example of updating work item fields
    """
    logger.info("=== Basic Work Item Update Example ===")
    
    try:
        # Initialize client
        config = get_meegle_config()
        token_manager = TokenManager(
            user_key=config['user_key'],
            plugin_token=config['plugin_token']
        )
        client = MeegleClient(token_manager, config['project_key'])
        
        # Example work item details
        work_item_id = 123456  # Replace with actual work item ID
        work_item_type_key = "task"  # Replace with actual work item type
        
        # Update fields using the main update_work_item method
        update_fields = [
            {
                "field_key": "field_184c63",  # Replace with actual field key
                "field_value": 1646409600000  # Timestamp value
            },
            {
                "field_key": "title",  # Assuming title field
                "field_value": "Updated Task Title"
            },
            {
                "field_key": "description",  # Assuming description field
                "field_value": "This task has been updated via API"
            }
        ]
        
        result = client.workflow.update_work_item(
            work_item_id=work_item_id,
            work_item_type_key=work_item_type_key,
            update_fields=update_fields
        )
        
        logger.info(f"Work item updated successfully: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to update work item: {e}")
        raise


def update_work_item_role_owners_example():
    """
    Example of updating work item with role owners
    """
    logger.info("=== Role Owners Update Example ===")
    
    try:
        # Initialize client
        config = get_meegle_config()
        token_manager = TokenManager(
            user_key=config['user_key'],
            plugin_token=config['plugin_token']
        )
        client = MeegleClient(token_manager, config['project_key'])
        
        # Example work item details
        work_item_id = 123456  # Replace with actual work item ID
        work_item_type_key = "task"  # Replace with actual work item type
        
        # Create role owners field using helper method
        role_owners_field = client.workflow.create_role_owners_field([
            {
                "role": "rd",  # Development role
                "owners": ["user1", "user2"]  # Replace with actual user keys
            },
            {
                "role": "pm",  # Project manager role
                "owners": ["user3"]  # Replace with actual user key
            }
        ])
        
        # Update with role owners
        update_fields = [role_owners_field]
        
        result = client.workflow.update_work_item(
            work_item_id=work_item_id,
            work_item_type_key=work_item_type_key,
            update_fields=update_fields
        )
        
        logger.info(f"Work item role owners updated successfully: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to update work item role owners: {e}")
        raise


def update_work_item_fields_example():
    """
    Example using the convenience method update_work_item_fields
    """
    logger.info("=== Convenience Method Update Example ===")
    
    try:
        # Initialize client
        config = get_meegle_config()
        token_manager = TokenManager(
            user_key=config['user_key'],
            plugin_token=config['plugin_token']
        )
        client = MeegleClient(token_manager, config['project_key'])
        
        # Example work item details
        work_item_id = 123456  # Replace with actual work item ID
        work_item_type_key = "task"  # Replace with actual work item type
        
        # Update using keyword arguments (convenience method)
        result = client.workflow.update_work_item_fields(
            work_item_id=work_item_id,
            work_item_type_key=work_item_type_key,
            title="Updated Title via Convenience Method",
            description="Updated description",
            priority="high",
            status="in_progress"
        )
        
        logger.info(f"Work item updated via convenience method: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to update work item via convenience method: {e}")
        raise


def create_field_value_pairs_example():
    """
    Example of creating field value pairs using helper methods
    """
    logger.info("=== Field Value Pairs Creation Example ===")
    
    try:
        # Initialize client
        config = get_meegle_config()
        token_manager = TokenManager(
            user_key=config['user_key'],
            plugin_token=config['plugin_token']
        )
        client = MeegleClient(token_manager, config['project_key'])
        
        # Create individual field value pairs
        title_field = client.workflow.create_field_value_pair(
            field_key="title",
            field_value="New Task Title"
        )
        
        description_field = client.workflow.create_field_value_pair(
            field_alias="desc",  # Using field alias instead of field key
            field_value="New task description"
        )
        
        timestamp_field = client.workflow.create_field_value_pair(
            field_key="field_184c63",
            field_value=1646409600000
        )
        
        logger.info(f"Created field value pairs:")
        logger.info(f"Title: {title_field}")
        logger.info(f"Description: {description_field}")
        logger.info(f"Timestamp: {timestamp_field}")
        
        # Use these fields to update work item
        work_item_id = 123456  # Replace with actual work item ID
        work_item_type_key = "task"  # Replace with actual work item type
        
        update_fields = [title_field, description_field, timestamp_field]
        
        result = client.workflow.update_work_item(
            work_item_id=work_item_id,
            work_item_type_key=work_item_type_key,
            update_fields=update_fields
        )
        
        logger.info(f"Work item updated with created field pairs: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to create field value pairs: {e}")
        raise


def main():
    """
    Run all update work item examples
    """
    logger.info("Starting Update Work Item Examples")
    
    try:
        # Note: These examples require actual work item IDs and field keys
        # Replace the placeholder values with real ones from your Meegle instance
        
        logger.info("Note: Please update work_item_id, work_item_type_key, and field keys")
        logger.info("with actual values from your Meegle instance before running.")
        
        # Uncomment the examples you want to run:
        
        # update_work_item_basic_example()
        # update_work_item_role_owners_example()
        # update_work_item_fields_example()
        # create_field_value_pairs_example()
        
        logger.info("Update Work Item Examples completed")
        
    except Exception as e:
        logger.error(f"Examples failed: {e}")
        raise


if __name__ == "__main__":
    main()