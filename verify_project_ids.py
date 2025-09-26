#!/usr/bin/env python3
"""
Verify if field_c0a56e values correspond to old project IDs
"""

import logging
from config.settings import get_meegle_config
from meegle_sdk import MeegleSDK

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Verify project IDs"""
    
    print("=" * 80)
    print("验证项目ID对应关系")
    print("=" * 80)
    
    # Sample IDs from the debug output
    sample_project_ids = [5014050, 6852400, 6852379, 7181567, 6852464]
    
    try:
        # Initialize SDK
        api_config = get_meegle_config()
        sdk = MeegleSDK(
            base_url=api_config['base_url'],
            plugin_id=api_config['plugin_id'],
            plugin_secret=api_config['plugin_secret'],
            user_key=api_config['user_key'],
            project_key=api_config['project_key']
        )
        
        # Get all old projects
        print("获取所有老项目...")
        old_projects = sdk.work_items.get_all_work_items(["642ec373f4af608bb3cb1c90"])
        old_project_dict = {proj.get('id'): proj.get('name') for proj in old_projects}
        
        print(f"找到 {len(old_projects)} 个老项目")
        print()
        
        # Check each sample ID
        print("检查样本 ID:")
        for project_id in sample_project_ids:
            if project_id in old_project_dict:
                project_name = old_project_dict[project_id]
                print(f"✅ {project_id} -> {project_name}")
            else:
                print(f"❌ {project_id} -> 未找到对应项目")
        
        print()
        
        # Show some examples of old project IDs and names
        print("老项目 ID 示例:")
        for i, (proj_id, proj_name) in enumerate(list(old_project_dict.items())[:10]):
            print(f"  {proj_id} -> {proj_name}")
        
    except Exception as e:
        logger.error(f"验证失败: {e}")
        print(f"❌ 验证失败: {e}")

if __name__ == "__main__":
    main()

