#!/usr/bin/env python3
"""
重试失败的项目迁移

从迁移日志中提取失败的项目ID，并重新尝试迁移
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


def retry_failed_projects():
    """重试失败的项目"""
    
    # 初始化 SDK
    sdk = MeegleSDK(
        base_url=MEEGLE_CONFIG['base_url'],
        project_key=MEEGLE_CONFIG['project_key'],
        plugin_secret=MEEGLE_CONFIG['plugin_secret']
    )
    
    # 初始化迁移器
    migrator = ProjectMigrator(sdk)
    
    print("="*80)
    print("重试失败的项目迁移")
    print("="*80)
    
    # 失败的项目ID列表（从之前的日志中提取）
    failed_project_ids = [
        7315577,  # PJT-GLOBAL-AII-EKYC-Infrastructure
        6852464,  # PRD-GLOBAL-AIPL-IdentityVerification
        6852401,  # PRD-ID-AII-EKYC-FaceComparison
        6852400,  # PRD-GLOBAL-AIPL-LivenessDetection
        5014050,  # PRD-CMS-OP
    ]
    
    print(f"准备重试 {len(failed_project_ids)} 个失败的项目...")
    
    # 获取所有老项目
    old_projects = migrator.get_old_projects()
    
    # 找到对应的项目对象
    failed_projects = []
    for project in old_projects:
        if project.get('id') in failed_project_ids:
            failed_projects.append(project)
    
    print(f"找到 {len(failed_projects)} 个需要重试的项目:")
    for project in failed_projects:
        print(f"  - {project.get('name')} (ID: {project.get('id')})")
    
    if not failed_projects:
        print("❌ 未找到需要重试的项目")
        return
    
    # 确认重试
    confirm = input(f"\n确定要重试这 {len(failed_projects)} 个项目吗？ (y/N): ").strip().lower()
    
    if confirm != 'y':
        print("取消重试")
        return
    
    print(f"\n开始重试迁移...")
    
    # 重试每个失败的项目
    retry_results = []
    
    for i, project in enumerate(failed_projects):
        project_id = project.get('id')
        project_name = project.get('name')
        
        print(f"\n重试项目 {i+1}/{len(failed_projects)}: {project_name} (ID: {project_id})")
        print("-" * 60)
        
        try:
            # 尝试迁移单个项目
            result = migrator.migrate_single_project(project)
            retry_results.append(result)
            
            if result.success:
                print(f"✅ 重试成功: 新项目 ID {result.new_project_id}")
            else:
                print(f"❌ 重试仍然失败: {result.error_message}")
                
        except Exception as e:
            print(f"❌ 重试异常: {e}")
            # 创建失败结果
            from meegle_business.work_item.project_migrator import MigrationResult
            result = MigrationResult(
                old_project_id=project_id,
                new_project_id=None,
                success=False,
                error_message=str(e)
            )
            retry_results.append(result)
    
    # 显示重试结果汇总
    print(f"\n{'='*80}")
    print("重试结果汇总")
    print("="*80)
    
    successful_retries = [r for r in retry_results if r.success]
    failed_retries = [r for r in retry_results if not r.success]
    
    print(f"总重试项目: {len(retry_results)}")
    print(f"重试成功: {len(successful_retries)}")
    print(f"仍然失败: {len(failed_retries)}")
    
    if successful_retries:
        print(f"\n✅ 重试成功的项目:")
        for result in successful_retries:
            print(f"  老项目 {result.old_project_id} -> 新项目 {result.new_project_id}")
    
    if failed_retries:
        print(f"\n❌ 仍然失败的项目:")
        for result in failed_retries:
            print(f"  项目 {result.old_project_id}: {result.error_message}")
            
        # 分析失败原因
        print(f"\n失败原因分析:")
        error_types = {}
        for result in failed_retries:
            error_msg = result.error_message
            if "Related features" in error_msg and "expired" in error_msg:
                error_types["Related features 配置过期"] = error_types.get("Related features 配置过期", 0) + 1
            elif "role" in error_msg and "not exist" in error_msg:
                error_types["角色配置问题"] = error_types.get("角色配置问题", 0) + 1
            else:
                error_types["其他错误"] = error_types.get("其他错误", 0) + 1
        
        for error_type, count in error_types.items():
            print(f"  {error_type}: {count} 个项目")
        
        if "Related features 配置过期" in error_types:
            print(f"\n💡 建议:")
            print(f"  'Related features' 字段配置过期问题可能需要:")
            print(f"  1. 联系管理员更新字段配置")
            print(f"  2. 或者在迁移时跳过该字段")
            print(f"  3. 或者清空/更新该字段的值")
    
    print("="*80)


if __name__ == "__main__":
    retry_failed_projects()

