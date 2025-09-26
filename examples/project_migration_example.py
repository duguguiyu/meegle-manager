#!/usr/bin/env python3
"""
项目迁移示例

演示如何使用 ProjectMigrator 从老的项目类型迁移到新的项目类型
"""

import sys
import os
import logging
from pathlib import Path

# 设置日志级别
logging.basicConfig(level=logging.INFO)

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from meegle_sdk import MeegleSDK
from meegle_business import ProjectMigrator
from config.settings import MEEGLE_CONFIG


def main():
    """主函数"""
    # 初始化 SDK
    sdk = MeegleSDK(
        base_url=MEEGLE_CONFIG['base_url'],
        project_key=MEEGLE_CONFIG['project_key'],
        plugin_secret=MEEGLE_CONFIG['plugin_secret']
    )
    
    # 初始化项目迁移器
    migrator = ProjectMigrator(sdk)
    
    print("="*60)
    print("项目迁移工具")
    print("="*60)
    print(f"从老项目类型: {migrator.OLD_PROJECT_TYPE}")
    print(f"到新项目类型: {migrator.NEW_PROJECT_TYPE}")
    print(f"字段映射: {migrator.FIELD_MAPPING}")
    
    # 步骤 1: 分析迁移可行性
    print("\n步骤 1: 分析迁移可行性...")
    try:
        analysis = migrator.analyze_migration_feasibility()
        
        print(f"老项目数量: {analysis['old_projects_count']}")
        print(f"样本字段: {analysis['sample_fields'][:10]}...")  # 显示前10个字段
        
        if analysis['field_mapping_analysis']:
            print("字段映射分析:")
            for old_field, mapping_info in analysis['field_mapping_analysis'].items():
                print(f"  {old_field} -> {mapping_info['maps_to']} (有值: {mapping_info['has_value']})")
        
        if analysis['potential_issues']:
            print("潜在问题:")
            for issue in analysis['potential_issues']:
                print(f"  ⚠️  {issue}")
            
            response = input("\n发现潜在问题，是否继续？(y/N): ").strip().lower()
            if response not in ['y', 'yes']:
                print("操作已取消。")
                return
        
        if analysis['old_projects_count'] == 0:
            print("没有找到需要迁移的老项目。")
            return
            
    except Exception as e:
        print(f"分析失败: {e}")
        return
    
    # 步骤 2: 试运行迁移
    print(f"\n步骤 2: 试运行迁移 (限制前5个项目)...")
    try:
        dry_run_results = migrator.migrate_all_projects(dry_run=True, limit=5)
        migrator.print_migration_summary(dry_run_results, dry_run=True)
        
        # 显示详细的试运行信息
        print("\n试运行详情 (前3个项目):")
        for i, result in enumerate(dry_run_results[:3]):
            print(f"项目 {result.old_project_id}:")
            print(f"  将迁移字段: {result.migrated_fields}")
            
    except Exception as e:
        print(f"试运行失败: {e}")
        return
    
    # 步骤 3: 询问是否执行实际迁移
    print(f"\n发现 {analysis['old_projects_count']} 个项目需要迁移。")
    
    # 询问迁移数量
    while True:
        try:
            limit_input = input(f"请输入要迁移的项目数量 (1-{analysis['old_projects_count']}, 或 'all' 迁移全部): ").strip()
            if limit_input.lower() == 'all':
                migration_limit = None
                break
            else:
                migration_limit = int(limit_input)
                if 1 <= migration_limit <= analysis['old_projects_count']:
                    break
                else:
                    print(f"请输入 1-{analysis['old_projects_count']} 之间的数字，或 'all'")
        except ValueError:
            print("请输入有效的数字或 'all'")
    
    # 确认执行
    confirm_msg = f"确定要迁移 {'全部' if migration_limit is None else migration_limit} 个项目吗？"
    response = input(f"\n{confirm_msg} (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("操作已取消。")
        return
    
    # 步骤 4: 执行实际迁移
    print(f"\n步骤 3: 执行实际迁移...")
    try:
        results = migrator.migrate_all_projects(dry_run=False, limit=migration_limit)
        migrator.print_migration_summary(results, dry_run=False)
        
        # 显示成功迁移的项目详情
        successful_results = [r for r in results if r.success]
        if successful_results:
            print(f"\n成功迁移的项目详情:")
            for result in successful_results[:10]:  # 显示前10个
                print(f"  老项目 {result.old_project_id} -> 新项目 {result.new_project_id}")
                print(f"    迁移字段: {result.migrated_fields}")
        
        print(f"\n迁移完成！成功迁移 {len(successful_results)} 个项目。")
        
    except Exception as e:
        print(f"迁移失败: {e}")


if __name__ == "__main__":
    main()

