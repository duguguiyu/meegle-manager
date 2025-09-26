#!/usr/bin/env python3
"""
Feature Reassignment Script

This script reassigns features from old projects to new projects based on project names.
It processes features from a specified view and updates their project associations.
"""

import logging
import sys
from config.settings import get_meegle_config
from meegle_sdk import MeegleSDK
from meegle_business import FeatureReassignment

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main function to reassign features to new projects"""
    
    # Configuration
    view_id = "2p_eWOrHg"  # The view ID provided by the user
    
    print("=" * 80)
    print("Feature 重新分配工具")
    print("=" * 80)
    print(f"视图 ID: {view_id}")
    print()
    
    try:
        # Initialize SDK
        logger.info("初始化 Meegle SDK...")
        api_config = get_meegle_config()
        sdk = MeegleSDK(
            base_url=api_config['base_url'],
            plugin_id=api_config['plugin_id'],
            plugin_secret=api_config['plugin_secret'],
            user_key=api_config['user_key'],
            project_key=api_config['project_key']
        )
        print("✅ SDK 初始化完成")
        
        # Initialize feature reassignment tool
        reassignment_tool = FeatureReassignment(sdk)
        print("✅ Feature 重新分配工具初始化完成")
        print()
        
        # Step 1: Analyze features in the view (dry run first)
        print("1️⃣ 分析视图中的 feature...")
        print("-" * 40)
        
        features = reassignment_tool.get_features_from_view(view_id)
        if not features:
            print("❌ 视图中没有找到 feature")
            return
        
        print(f"✅ 找到 {len(features)} 个 feature")
        
        # Step 2: Analyze project associations
        print("\n2️⃣ 分析项目关联...")
        print("-" * 40)
        
        analysis = reassignment_tool.analyze_feature_project_associations(features)
        
        print(f"📊 分析结果:")
        print(f"  • 总 feature 数: {analysis['total_features']}")
        print(f"  • 有项目关联的: {analysis['features_with_projects']}")
        print(f"  • 无项目关联的: {analysis['features_without_projects']}")
        print(f"  • 唯一项目名称数: {len(analysis['unique_project_names'])}")
        
        if analysis['project_field_counts']:
            print(f"  • 项目字段统计:")
            for field_key, count in analysis['project_field_counts'].items():
                print(f"    - {field_key}: {count} 个 feature")
        
        if analysis['unique_project_names']:
            print(f"  • 关联的项目名称:")
            for name in sorted(analysis['unique_project_names'])[:10]:  # Show first 10
                print(f"    - {name}")
            if len(analysis['unique_project_names']) > 10:
                print(f"    - ... 还有 {len(analysis['unique_project_names']) - 10} 个")
        
        # Step 3: Build project mapping
        print("\n3️⃣ 构建项目映射...")
        print("-" * 40)
        
        project_mapping = reassignment_tool.build_project_name_mapping()
        print(f"✅ 找到 {len(project_mapping)} 个项目映射")
        
        if project_mapping:
            print("📋 项目映射示例:")
            for old_name, new_id in list(project_mapping.items())[:5]:
                print(f"  • {old_name} -> 新项目 ID {new_id}")
            if len(project_mapping) > 5:
                print(f"  • ... 还有 {len(project_mapping) - 5} 个映射")
        
        # Check which projects from features have mappings
        features_with_mapping = 0
        for project_name in analysis['unique_project_names']:
            if project_name in project_mapping:
                features_with_mapping += 1
        
        print(f"📈 映射覆盖率: {features_with_mapping}/{len(analysis['unique_project_names'])} 个项目有映射")
        
        # Step 4: Dry run first
        print("\n4️⃣ 执行 DRY RUN...")
        print("-" * 40)
        
        dry_run_results = reassignment_tool.reassign_features_to_new_projects(view_id, dry_run=True)
        
        if not dry_run_results:
            print("❌ 没有可以重新分配的 feature")
            return
        
        successful_dry_run = [r for r in dry_run_results if r.success]
        failed_dry_run = [r for r in dry_run_results if not r.success]
        
        print(f"📊 DRY RUN 结果:")
        print(f"  • 可以成功重新分配: {len(successful_dry_run)} 个")
        print(f"  • 无法重新分配: {len(failed_dry_run)} 个")
        
        if failed_dry_run:
            print(f"  • 失败原因统计:")
            error_counts = {}
            for result in failed_dry_run:
                error = result.error_message or "未知错误"
                error_counts[error] = error_counts.get(error, 0) + 1
            for error, count in error_counts.items():
                print(f"    - {error}: {count} 个")
        
        # Step 5: Ask for confirmation to proceed
        print("\n5️⃣ 确认执行...")
        print("-" * 40)
        
        if len(successful_dry_run) == 0:
            print("❌ 没有可以成功重新分配的 feature，停止执行")
            return
        
        print(f"准备重新分配 {len(successful_dry_run)} 个 feature 到新项目")
        
        while True:
            response = input("确定要执行实际的重新分配吗？ (y/N): ").strip().lower()
            if response in ['y', 'yes']:
                break
            elif response in ['n', 'no', '']:
                print("❌ 用户取消操作")
                return
            else:
                print("请输入 y 或 n")
        
        # Step 6: Execute actual reassignment
        print("\n6️⃣ 执行实际重新分配...")
        print("-" * 40)
        
        actual_results = reassignment_tool.reassign_features_to_new_projects(view_id, dry_run=False)
        
        # Step 7: Print final summary
        print("\n7️⃣ 最终结果...")
        print("-" * 40)
        
        reassignment_tool.print_reassignment_summary(actual_results)
        
        # Success statistics
        successful_actual = [r for r in actual_results if r.success]
        failed_actual = [r for r in actual_results if not r.success]
        
        if len(successful_actual) > 0:
            print(f"🎉 成功重新分配了 {len(successful_actual)} 个 feature！")
        
        if len(failed_actual) > 0:
            print(f"⚠️  有 {len(failed_actual)} 个 feature 重新分配失败")
            
    except KeyboardInterrupt:
        print("\n❌ 用户中断操作")
        sys.exit(1)
    except Exception as e:
        logger.error(f"执行失败: {e}")
        print(f"❌ 执行失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

