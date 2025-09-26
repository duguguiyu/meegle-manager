#!/usr/bin/env python3
"""
Check project mapping between old and new projects
"""

import logging
from config.settings import get_meegle_config
from meegle_sdk import MeegleSDK

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Check project mapping"""
    
    print("=" * 80)
    print("检查项目映射")
    print("=" * 80)
    
    # The 7 unique project names from features
    feature_project_names = [
        "PJT-GLOBAL-AII-EKYC-Infrastructure",
        "PRD-CMS-OP", 
        "PRD-GLOBAL-AIPL-IdentityVerification",
        "PRD-GLOBAL-AIPL-LivenessDetection",
        "PRD-ID-AII-EKYC-FaceComparison",
        "PRD-ID-BPS-ICS-006-V1",
        "PRD-PH-ADVI-EKYC-IDForgery"
    ]
    
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
        old_project_dict = {proj.get('name'): proj.get('id') for proj in old_projects}
        
        # Get all new projects
        print("获取所有新项目...")
        new_projects = sdk.work_items.get_all_work_items(["68afee24c92ef633f847d304"])
        new_project_dict = {proj.get('name'): proj.get('id') for proj in new_projects}
        
        print(f"找到 {len(old_projects)} 个老项目")
        print(f"找到 {len(new_projects)} 个新项目")
        print()
        
        # Check each feature project name
        print("检查 feature 中的项目名称:")
        print("-" * 60)
        
        for project_name in feature_project_names:
            old_exists = project_name in old_project_dict
            new_exists = project_name in new_project_dict
            
            print(f"项目名称: {project_name}")
            print(f"  老项目中存在: {'✅' if old_exists else '❌'}")
            if old_exists:
                print(f"  老项目ID: {old_project_dict[project_name]}")
            print(f"  新项目中存在: {'✅' if new_exists else '❌'}")
            if new_exists:
                print(f"  新项目ID: {new_project_dict[project_name]}")
            print()
        
        # Show some sample new project names
        print("新项目名称示例:")
        print("-" * 40)
        for name in list(new_project_dict.keys())[:10]:
            print(f"  {name}")
        
        # Look for similar names in new projects
        print("\n查找相似的项目名称:")
        print("-" * 40)
        for feature_name in feature_project_names:
            similar_names = []
            for new_name in new_project_dict.keys():
                # Check if names are similar (contain common words)
                feature_words = set(feature_name.split('-'))
                new_words = set(new_name.split('-'))
                common_words = feature_words.intersection(new_words)
                if len(common_words) >= 2:  # At least 2 common words
                    similar_names.append(new_name)
            
            if similar_names:
                print(f"{feature_name}:")
                for similar in similar_names:
                    print(f"  -> {similar}")
            else:
                print(f"{feature_name}: 未找到相似项目")
        
    except Exception as e:
        logger.error(f"检查失败: {e}")
        print(f"❌ 检查失败: {e}")

if __name__ == "__main__":
    main()

