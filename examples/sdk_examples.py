#!/usr/bin/env python3
"""
SDK Examples - Demonstrate how to use Meegle SDK APIs individually
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path to import meegle_sdk
sys.path.insert(0, str(Path(__file__).parent.parent))

from meegle_sdk import MeegleSDK
from meegle_sdk.models import APIError, AuthenticationError
from config.settings import get_meegle_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def example_basic_sdk_usage(sdk: MeegleSDK):
    """Basic SDK usage example"""
    print("=" * 50)
    print("Basic SDK Usage Example")
    print("=" * 50)
    
    try:
        # Test connection
        print("Testing connection...")
        if sdk.get_client().test_connection():
            print("✅ Connection successful!")
        else:
            print("❌ Connection failed!")
            return False
        
        # Show client info
        client_info = sdk.get_client().get_client_info()
        print(f"Client Info: {client_info}")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def example_chart_api(sdk: MeegleSDK):
    """Chart API example"""
    print("\n" + "=" * 50)
    print("Chart API Example")
    print("=" * 50)
    
    try:
        # Example chart ID (replace with actual chart ID)
        chart_id = "7452978372562386950"
        
        print(f"Fetching chart details for ID: {chart_id}")
        chart_data = sdk.charts.get_chart_details(chart_id)
        
        if chart_data:
            print(f"✅ Chart data retrieved successfully!")
            print(f"Chart data keys: {list(chart_data.keys())}")
            
            # Validate chart data
            if sdk.charts.validate_chart_data(chart_data):
                print("✅ Chart data is valid")
            else:
                print("❌ Chart data is invalid")
        else:
            print("❌ No chart data retrieved")
            
    except APIError as e:
        print(f"❌ API Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def example_work_items_api(sdk: MeegleSDK):
    """Work Items API example"""
    print("\n" + "=" * 50)
    print("Work Items API Example")
    print("=" * 50)
    
    try:
        # Get first page of work items
        print("Fetching work items (first page)...")
        # Use specific work item type ID, or None for all types
        work_items = sdk.work_items.get_work_items(
            work_item_type_id="642ec373f4af608bb3cb1c90",  # Project type (replace with your type ID)
            page_size=10, 
            page_num=1
        )
        
        if work_items:
            print(f"✅ Retrieved {len(work_items)} work items")
            
            # Show first item details
            if work_items:
                first_item = work_items[0]
                print(f"First item: {first_item.get('title', 'No title')}")
                print(f"Item type: {first_item.get('item_type', 'Unknown')}")
        else:
            print("❌ No work items retrieved")
            
    except APIError as e:
        print(f"❌ API Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def example_teams_api(sdk: MeegleSDK):
    """Teams API example"""
    print("\n" + "=" * 50)
    print("Teams API Example")
    print("=" * 50)
    
    try:
        print("Fetching all teams...")
        teams = sdk.teams.get_all_teams()
        
        if teams:
            print(f"✅ Retrieved {len(teams)} teams")
            
            # Extract user keys
            user_keys = sdk.teams.extract_all_user_keys(teams)
            print(f"Total unique users across teams: {len(user_keys)}")
            
            # Show first few teams
            for i, team in enumerate(teams[:3], 1):
                team_name = team.get('name', 'Unknown')
                team_members = len(team.get('user_keys', []))
                print(f"Team {i}: {team_name} ({team_members} members)")
        else:
            print("❌ No teams retrieved")
            
    except APIError as e:
        print(f"❌ API Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def example_users_api(sdk: MeegleSDK):
    """Users API example"""
    print("\n" + "=" * 50)
    print("Users API Example")
    print("=" * 50)
    
    try:
        print("Getting all users (with intelligent caching)...")
        users = sdk.users.get_all_users()
        
        if users:
            print(f"✅ Retrieved {len(users)} users from cache")
            
            # Get name to email mapping
            name_to_email = sdk.users.get_name_to_email_mapping()
            print(f"Name-to-email mappings: {len(name_to_email)}")
            
            # Show first few users
            user_list = list(users.values())[:3]
            for i, user in enumerate(user_list, 1):
                name = user.get('name_cn', 'Unknown')
                email = user.get('email', 'No email')
                print(f"User {i}: {name} ({email})")
        else:
            print("❌ No users retrieved")
            
    except APIError as e:
        print(f"❌ API Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def example_error_handling():
    """Error handling example"""
    print("\n" + "=" * 50)
    print("Error Handling Example")
    print("=" * 50)
    
    try:
        # Try to initialize with invalid credentials
        sdk = MeegleSDK(
            plugin_id="invalid_id",
            plugin_secret="invalid_secret",
            user_key="invalid_user"
        )
        
        # This should fail
        teams = sdk.teams.get_all_teams()
        print("❌ This should not succeed!")
        
    except AuthenticationError as e:
        print(f"✅ Authentication error handled correctly: {e}")
    except APIError as e:
        print(f"✅ API error handled correctly: {e}")
    except Exception as e:
        print(f"✅ General error handled: {e}")


def main():
    """Run all SDK examples"""
    import time
    
    print("🚀 Meegle SDK Examples")
    print("=" * 50)
    
    try:
        # Check configuration
        config = get_meegle_config()
        print(f"Using base URL: {config['base_url']}")
        print(f"Using project: {config['project_key']}")
        print("=" * 50)
        
        # Initialize SDK once and reuse
        print("Initializing SDK...")
        sdk = MeegleSDK()
        print("✅ SDK initialized successfully")
        
        # Run examples with delays to avoid rate limiting
        if not example_basic_sdk_usage(sdk):
            print("❌ Basic usage failed, skipping other examples")
            return
            
        time.sleep(3)  # Wait between API calls
        example_chart_api(sdk)
        
        time.sleep(3)
        example_work_items_api(sdk)
        
        time.sleep(3) 
        example_teams_api(sdk)
        
        time.sleep(3)
        example_users_api(sdk)
        
        time.sleep(2)
        example_error_handling()
        
        print("\n" + "=" * 50)
        print("✅ All SDK examples completed!")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Failed to run examples: {e}")


if __name__ == "__main__":
    main()