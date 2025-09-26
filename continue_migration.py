#!/usr/bin/env python3
"""
继续项目迁移

所有问题已解决：
1. ✅ Business 字段兼容性问题已解决
2. ✅ 角色映射问题已解决 (assignee -> role_project_owner)
3. ✅ 字段映射正常工作 (field_f7f3d2 -> field_696f08)

现在可以安全地继续迁移剩余的项目
"""

import sys
import logging
from pathlib import Path

# 设置日志级别
logging.basicConfig(level=logging.INFO)

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from meegle_sdk import MeegleSDK
from meegle_business import ProjectMigrator
from config.settings import MEEGLE_CONFIG


def continue_migration():
    """继续项目迁移"""
    
    # 初始化 SDK
    sdk = MeegleSDK(
        base_url=MEEGLE_CONFIG['base_url'],
        project_key=MEEGLE_CONFIG['project_key'],
        plugin_secret=MEEGLE_CONFIG['plugin_secret']
    )
    
    # 初始化迁移器
    migrator = ProjectMigrator(sdk)
    
    print("="*80)
    print("继续项目迁移 - 所有问题已解决")
    print("="*80)
    
    print("已解决的问题:")
    print("✅ Business 字段兼容性 - 支持直接传递")
    print("✅ 角色映射 - assignee -> role_project_owner")
    print("✅ 字段映射 - field_f7f3d2 -> field_696f08")
    print("✅ API 响应解析 - 正确处理创建响应")
    
    # 获取迁移状态
    old_projects = migrator.get_old_projects()
    print(f"\n总项目数: {len(old_projects)}")
    
    # 检查已迁移的项目
    new_projects = sdk.work_items.get_all_work_items(
        work_item_type_keys=[migrator.NEW_PROJECT_TYPE]
    )
    
    # 过滤出迁移创建的项目（排除测试项目）
    migrated_projects = []
    test_keywords = ['测试', '迁移测试', 'Business测试', '角色测试']
    
    for project in new_projects:
        project_name = project.get('name', '')
        is_test = any(keyword in project_name for keyword in test_keywords)
        if not is_test:
            migrated_projects.append(project)
    
    print(f"已迁移项目数: {len(migrated_projects)}")
    print(f"剩余待迁移: {len(old_projects) - len(migrated_projects)}")
    
    if len(migrated_projects) > 0:
        print(f"\n已迁移的项目:")
        for project in migrated_projects:
            print(f"  - {project.get('name')} (ID: {project.get('id')})")
    
    # 建议下一步迁移策略
    remaining = len(old_projects) - len(migrated_projects)
    
    if remaining > 0:
        print(f"\n建议的迁移策略:")
        
        if remaining <= 10:
            print(f"1. 小规模迁移：剩余 {remaining} 个项目，建议一次性迁移")
            batch_size = remaining
        elif remaining <= 50:
            print(f"2. 中等规模迁移：剩余 {remaining} 个项目，建议分批迁移")
            batch_size = 10
        else:
            print(f"3. 大规模迁移：剩余 {remaining} 个项目，建议分批迁移")
            batch_size = 20
        
        print(f"   建议批次大小: {batch_size}")
        
        # 询问是否继续迁移
        print(f"\n是否继续迁移？")
        print(f"输入要迁移的项目数量 (1-{remaining})，或 'all' 迁移全部，或 'q' 退出:")
        
        user_input = input().strip().lower()
        
        if user_input == 'q':
            print("退出迁移")
            return
        elif user_input == 'all':
            limit = None
            print(f"准备迁移全部 {remaining} 个项目...")
        else:
            try:
                limit = int(user_input)
                if limit < 1 or limit > remaining:
                    print(f"输入的数量超出范围，使用建议值: {batch_size}")
                    limit = batch_size
                print(f"准备迁移 {limit} 个项目...")
            except ValueError:
                print(f"输入无效，使用建议值: {batch_size}")
                limit = batch_size
        
        # 确认迁移
        if limit:
            confirm = input(f"确定要迁移 {limit} 个项目吗？ (y/N): ").strip().lower()
        else:
            confirm = input(f"确定要迁移全部 {remaining} 个项目吗？ (y/N): ").strip().lower()
        
        if confirm == 'y':
            print(f"\n开始迁移...")
            
            # 执行迁移
            results = migrator.migrate_all_projects(dry_run=False, limit=limit)
            
            # 显示结果
            migrator.print_migration_summary(results, dry_run=False)
            
            print(f"\n迁移完成！")
            
        else:
            print("取消迁移")
    else:
        print(f"\n🎉 所有项目已完成迁移！")
    
    print("="*80)


if __name__ == "__main__":
    continue_migration()

