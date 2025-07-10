#!/usr/bin/env python3
"""
导出视图时间表数据到CSV
使用改进的ViewTimelineExtractor：
1. 使用 points 字段作为工作时间（actual_work_time优先，回退到points）
2. 每个人每个story每天只有一个timesheet entity（自动聚合）
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

# 添加项目根目录到路径
sys.path.append('.')

from meegle_sdk import MeegleSDK
from meegle_business.timeline.view_extractor import ViewTimelineExtractor
from meegle_business.export.csv_exporter import CSVExporter
from config.settings import get_meegle_config, get_export_config

def export_view_timeline(view_id: str, limit: int = None, filename: str = None):
    """
    导出视图时间线数据到CSV
    
    Args:
        view_id: 视图ID
        limit: 可选的工作项限制数量
        filename: 可选的输出文件名
    """
    print("=" * 80)
    print("📊 导出视图时间表数据")
    print("=" * 80)
    
    try:
        # 初始化SDK
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
        
        # 初始化提取器和导出器
        extractor = ViewTimelineExtractor(sdk)
        exporter = CSVExporter()
        print("✅ 提取器和导出器初始化完成")
        
        # 显示参数
        limit_text = f"（限制：前{limit}个工作项）" if limit else "（无限制）"
        print(f"\n📋 导出参数：")
        print(f"  视图ID: {view_id}")
        print(f"  工作项限制: {limit_text}")
        print(f"  自定义文件名: {filename or '自动生成'}")
        
        # 提取时间线数据
        print(f"\n⏳ 从视图 {view_id} 提取时间线数据{limit_text}...")
        start_time = datetime.now()
        
        timeline_data = extractor.extract_timeline_from_view(view_id, 'story', max_items=limit)
        
        extraction_time = (datetime.now() - start_time).total_seconds()
        print(f"⏱️ 提取完成，耗时 {extraction_time:.2f} 秒")
        
        # 显示提取结果摘要
        print(f"\n📊 提取结果摘要：")
        print(f"  📈 时间线条目数：{len(timeline_data.entries)}")
        print(f"  ⏰ 总工作小时：{timeline_data.total_hours:.2f}")
        print(f"  👥 唯一用户数：{timeline_data.unique_users}")
        print(f"  📅 日期范围：{timeline_data.date_range}")
        
        if not timeline_data.entries:
            print("⚠️ 没有时间线数据可导出")
            return None
        
        # 导出到CSV
        print(f"\n💾 导出数据到CSV...")
        export_start_time = datetime.now()
        
        # 生成文件名
        if not filename:
            filename = f"view_timeline_{view_id}"
            if limit:
                filename += f"_limit{limit}"
        
        csv_filepath = exporter.export_timeline_to_csv(timeline_data, filename)
        
        export_time = (datetime.now() - export_start_time).total_seconds()
        print(f"⏱️ 导出完成，耗时 {export_time:.2f} 秒")
        
        # 显示导出结果
        print(f"\n🎉 导出成功！")
        print(f"  📁 文件路径：{csv_filepath}")
        print(f"  📊 文件大小：{csv_filepath.stat().st_size / 1024:.1f} KB")
        print(f"  ⏱️ 总耗时：{(datetime.now() - start_time).total_seconds():.2f} 秒")
        
        # 显示统计信息
        print(f"\n📈 统计信息：")
        user_hours = {}
        for entry in timeline_data.entries:
            user_hours[entry.member_email] = user_hours.get(entry.member_email, 0) + entry.work_load_hours
        
        print(f"  👥 按用户工作小时（前5名）：")
        for user, hours in sorted(user_hours.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"    {user}: {hours:.2f} 小时")
        
        # 显示改进说明
        print(f"\n✨ 改进特性：")
        print(f"  🔢 使用 points 字段作为工作时间（actual_work_time优先）")
        print(f"  📅 每个人每个story每天只有一个timesheet entity")
        print(f"  🚫 自动过滤工时为0的条目")
        print(f"  📊 自动聚合同一天的多个任务")
        
        return csv_filepath
        
    except Exception as e:
        print(f"❌ 导出失败: {e}")
        logger.error(f"导出失败: {e}")
        return None

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="导出Meegle视图时间表数据到CSV",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python3 export_view_timesheet.py OXnKluvHR
  python3 export_view_timesheet.py OXnKluvHR --limit 10
  python3 export_view_timesheet.py OXnKluvHR --limit 5 --filename custom_export

改进特性:
  • 使用 points 字段作为工作时间（actual_work_time优先）
  • 每个人每个story每天只有一个timesheet entity
  • 自动过滤工时为0的条目
  • 自动聚合同一天的多个任务
        """
    )
    
    parser.add_argument(
        'view_id',
        help='视图ID（例如：OXnKluvHR）'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        help='限制处理的工作项数量（用于测试）'
    )
    
    parser.add_argument(
        '--filename',
        help='自定义输出文件名（不包含扩展名）'
    )
    
    args = parser.parse_args()
    
    # 执行导出
    result = export_view_timeline(
        view_id=args.view_id,
        limit=args.limit,
        filename=args.filename
    )
    
    if result:
        print(f"\n✅ 导出完成：{result}")
        sys.exit(0)
    else:
        print(f"\n❌ 导出失败")
        sys.exit(1)

if __name__ == "__main__":
    main() 