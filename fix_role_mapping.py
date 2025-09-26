#!/usr/bin/env python3
"""
修复角色映射问题

分析新旧项目类型的角色配置差异，并修复角色映射
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
from config.settings import MEEGLE_CONFIG


def analyze_role_configurations(sdk: MeegleSDK):
    """分析新旧项目类型的角色配置"""
    print("="*80)
    print("分析新旧项目类型的角色配置")
    print("="*80)
    
    # 分析老项目的角色配置
    print("\n步骤1: 分析老项目的角色配置...")
    old_projects = sdk.work_items.get_all_work_items(
        work_item_type_keys=["642ec373f4af608bb3cb1c90"]
    )
    
    old_roles = set()
    for project in old_projects[:10]:  # 分析前10个项目
        fields = project.get('fields', [])
        for field in fields:
            if field.get('field_key') == 'role_owners':
                role_owners = field.get('field_value', [])
                if role_owners:
                    for role_owner in role_owners:
                        role = role_owner.get('role')
                        if role:
                            old_roles.add(role)
    
    print(f"老项目类型的角色: {sorted(old_roles)}")
    
    # 分析新项目的角色配置
    print("\n步骤2: 分析新项目的角色配置...")
    new_projects = sdk.work_items.get_all_work_items(
        work_item_type_keys=["68afee24c92ef633f847d304"]
    )
    
    new_roles = set()
    for project in new_projects:
        fields = project.get('fields', [])
        for field in fields:
            if field.get('field_key') == 'role_owners':
                role_owners = field.get('field_value', [])
                if role_owners:
                    for role_owner in role_owners:
                        role = role_owner.get('role')
                        if role:
                            new_roles.add(role)
    
    print(f"新项目类型的角色: {sorted(new_roles)}")
    
    # 分析角色差异
    print(f"\n步骤3: 角色差异分析...")
    only_in_old = old_roles - new_roles
    only_in_new = new_roles - old_roles
    common_roles = old_roles & new_roles
    
    print(f"共同角色: {sorted(common_roles)}")
    print(f"仅在老项目中: {sorted(only_in_old)}")
    print(f"仅在新项目中: {sorted(only_in_new)}")
    
    # 建议角色映射
    print(f"\n步骤4: 建议角色映射...")
    role_mapping = {}
    
    for old_role in only_in_old:
        if old_role == 'assignee':
            # assignee 可能映射到 role_project_owner 或其他角色
            if 'role_project_owner' in new_roles:
                role_mapping[old_role] = 'role_project_owner'
                print(f"建议映射: {old_role} -> role_project_owner")
            elif new_roles:
                # 选择第一个可用的新角色
                first_new_role = sorted(new_roles)[0]
                role_mapping[old_role] = first_new_role
                print(f"建议映射: {old_role} -> {first_new_role}")
        else:
            print(f"需要手动配置映射: {old_role}")
    
    return role_mapping


def main():
    """主函数"""
    # 初始化 SDK
    sdk = MeegleSDK(
        base_url=MEEGLE_CONFIG['base_url'],
        project_key=MEEGLE_CONFIG['project_key'],
        plugin_secret=MEEGLE_CONFIG['plugin_secret']
    )
    
    # 分析角色配置
    role_mapping = analyze_role_configurations(sdk)
    
    print(f"\n{'='*80}")
    print("建议的解决方案:")
    print("="*80)
    
    if role_mapping:
        print("1. 在 ProjectMigrator 中添加角色映射:")
        print("```python")
        print("# 在 ProjectMigrator 类中添加角色映射")
        print(f"ROLE_MAPPING = {role_mapping}")
        print("```")
        
        print("\n2. 或者跳过有问题角色的项目:")
        print("```python")
        print("# 跳过包含不兼容角色的项目")
        print("if 'assignee' in role_owners_roles:")
        print("    logger.warning('跳过包含不兼容角色的项目')")
        print("    return None")
        print("```")
    else:
        print("未发现明显的角色映射方案，建议:")
        print("1. 检查新项目类型的角色配置")
        print("2. 考虑跳过 role_owners 字段的迁移")
        print("3. 或者手动配置角色映射")
    
    print("="*80)


if __name__ == "__main__":
    main()

