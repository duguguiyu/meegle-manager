#!/usr/bin/env python3
"""
CSV 批量更新项目示例

演示如何使用 CSVProjectUpdater 批量更新项目信息
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
from meegle_business import CSVProjectUpdater
from config.settings import MEEGLE_CONFIG


def main():
    """主函数"""
    # 初始化 SDK
    sdk = MeegleSDK(
        base_url=MEEGLE_CONFIG['base_url'],
        project_key=MEEGLE_CONFIG['project_key'],
        plugin_secret=MEEGLE_CONFIG['plugin_secret']
    )
    
    # 初始化批量更新器
    updater = CSVProjectUpdater(sdk)
    
    # CSV 文件路径
    csv_file_path = project_root / "project_code_list.csv"
    
    if not csv_file_path.exists():
        print(f"错误: CSV 文件不存在: {csv_file_path}")
        return
    
    print("="*60)
    print("CSV 项目批量更新工具")
    print("="*60)
    
    # 步骤 1: 分析更新需求
    print("\n步骤 1: 分析更新需求...")
    try:
        analysis = updater.analyze_update_needs(str(csv_file_path))
        updater.print_analysis_summary(analysis)
        
        # 显示详细信息（仅显示前10个需要更新的项目）
        print("\n需要更新的项目详情 (前10个):")
        print("-" * 80)
        update_count = 0
        for detail in analysis['details']:
            if detail['status'] == 'needs_update' and update_count < 10:
                print(f"项目代码: {detail['code']}")
                print(f"项目ID: {detail['project_id']}")
                updates = detail['updates']
                if updates['field_28829a']['needed']:
                    print(f"  field_28829a: '{updates['field_28829a']['current']}' -> '{updates['field_28829a']['new']}'")
                if updates['description']['needed']:
                    current_desc = updates['description']['current'] or ''
                    new_desc = updates['description']['new'][:100] + '...' if len(updates['description']['new']) > 100 else updates['description']['new']
                    print(f"  description: '{current_desc[:50]}...' -> '{new_desc}'")
                print()
                update_count += 1
        
        if analysis['updates_needed'] == 0:
            print("没有需要更新的项目。")
            return
        
    except Exception as e:
        print(f"分析失败: {e}")
        return
    
    # 步骤 2: 询问用户是否继续
    print(f"\n发现 {analysis['updates_needed']} 个项目需要更新。")
    
    # 先进行试运行
    print("\n步骤 2: 执行试运行...")
    try:
        dry_run_results = updater.batch_update_projects(str(csv_file_path), dry_run=True)
        updater.print_update_summary(dry_run_results, dry_run=True)
        
    except Exception as e:
        print(f"试运行失败: {e}")
        return
    
    # 询问是否执行实际更新
    response = input(f"\n是否执行实际更新？(y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("操作已取消。")
        return
    
    # 步骤 3: 执行实际更新
    print("\n步骤 3: 执行实际更新...")
    try:
        results = updater.batch_update_projects(str(csv_file_path), dry_run=False)
        updater.print_update_summary(results, dry_run=False)
        
        # 显示失败的更新详情
        if results['failed_updates'] > 0:
            print("\n失败的更新详情:")
            print("-" * 50)
            for detail in results['details']:
                if detail['status'] == 'failed':
                    print(f"项目: {detail['code']} (ID: {detail['project_id']})")
                    print(f"错误: {detail['error']}")
                    print()
        
        print(f"\n批量更新完成！成功更新 {results['successful_updates']} 个项目。")
        
    except Exception as e:
        print(f"批量更新失败: {e}")


if __name__ == "__main__":
    main()
