#!/usr/bin/env python3
"""
Debug script to examine feature fields structure
"""

import logging
import json
from config.settings import get_meegle_config
from meegle_sdk import MeegleSDK

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Debug feature fields"""
    
    view_id = "2p_eWOrHg"
    
    print("=" * 80)
    print("调试 Feature 字段结构")
    print("=" * 80)
    
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
        
        # Get first 5 work items from view
        print("获取视图中的前5个工作项...")
        work_item_ids = sdk.work_items.get_all_work_items_in_view(view_id)
        sample_ids = work_item_ids[:5]
        
        print(f"样本工作项 IDs: {sample_ids}")
        
        # Get detailed information for these items
        features_data = sdk.work_items.get_work_item_details(
            work_item_ids=sample_ids,
            work_item_type_key="story"
        )
        
        if features_data and 'data' in features_data:
            features = features_data['data']
            print(f"\n获取到 {len(features)} 个 feature 详情")
            
            for i, feature in enumerate(features):
                print(f"\n{'='*60}")
                print(f"Feature {i+1}: {feature.get('name', 'Unnamed')} (ID: {feature.get('id')})")
                print(f"{'='*60}")
                
                # Print basic info
                print(f"名称: {feature.get('name')}")
                print(f"ID: {feature.get('id')}")
                print(f"类型: {feature.get('work_item_type_key')}")
                
                # Print all fields
                fields = feature.get('fields', [])
                print(f"\n字段数量: {len(fields)}")
                
                if fields:
                    print("\n所有字段:")
                    for field in fields:
                        field_key = field.get('field_key', 'unknown')
                        field_value = field.get('field_value')
                        field_alias = field.get('field_alias', '')
                        
                        # Check if this looks like a project-related field
                        is_project_related = any(keyword in field_key.lower() for keyword in 
                                               ['project', 'field_f7f3d2', 'field_696f08'])
                        
                        if is_project_related:
                            print(f"  🎯 {field_key} ({field_alias}): {field_value}")
                        else:
                            # Show value preview
                            if isinstance(field_value, (list, dict)):
                                value_preview = str(field_value)[:100] + "..." if len(str(field_value)) > 100 else str(field_value)
                            else:
                                value_preview = str(field_value)[:50] + "..." if len(str(field_value)) > 50 else str(field_value)
                            print(f"  • {field_key} ({field_alias}): {value_preview}")
                
                # Look for any field that might contain project information
                print(f"\n可能的项目相关字段:")
                project_candidates = []
                for field in fields:
                    field_key = field.get('field_key', '').lower()
                    field_alias = field.get('field_alias', '').lower()
                    field_value = field.get('field_value')
                    
                    # Check for various project-related keywords
                    project_keywords = ['project', 'proj', 'related', 'feature', 'parent', 'link']
                    
                    if any(keyword in field_key for keyword in project_keywords) or \
                       any(keyword in field_alias for keyword in project_keywords) or \
                       field_key in ['field_f7f3d2', 'field_696f08']:
                        project_candidates.append({
                            'field_key': field.get('field_key'),
                            'field_alias': field.get('field_alias'),
                            'field_value': field_value
                        })
                
                if project_candidates:
                    for candidate in project_candidates:
                        print(f"  🔍 {candidate['field_key']} ({candidate['field_alias']})")
                        print(f"      值: {candidate['field_value']}")
                else:
                    print("  ❌ 未找到明显的项目相关字段")
                
                print()
        
    except Exception as e:
        logger.error(f"调试失败: {e}")
        print(f"❌ 调试失败: {e}")

if __name__ == "__main__":
    main()

