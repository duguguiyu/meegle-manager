#!/usr/bin/env python3
"""
Export last week's timesheet data
"""

import logging
from meegle_sdk import MeegleSDK
from meegle_business.timeline.view_extractor import ViewTimelineExtractor
from meegle_business.export.csv_exporter import CSVExporter

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def export_last_week_timesheet():
    """Export last week's timesheet data"""
    
    print("正在导出上周 timesheet 数据...")
    print("=" * 50)
    
    try:
        # Initialize SDK, extractor, and exporter
        sdk = MeegleSDK()
        extractor = ViewTimelineExtractor(sdk)
        exporter = CSVExporter()
        
        # Use the same view ID as the 30-day export
        view_id = "OXnKluvHR"
        
        # Show date range that will be processed
        start_date, end_date = extractor._get_last_week_range()
        print(f"日期范围: {start_date} 到 {end_date} (上周 周一到周日)")
        print(f"视图 ID: {view_id}")
        
        # First check how many work items we'll process
        print("\n1. 检查视图中的工作项数量:")
        all_work_item_ids = sdk.work_items.get_all_work_items_in_view(view_id)
        print(f"   视图中总工作项数量: {len(all_work_item_ids)}")
        print()
        
        # Extract timeline data for last week
        print("2. 开始提取上周的时间线数据...")
        timeline_data = extractor.extract_timeline_last_week(
            view_id=view_id,
            work_item_type_key="story"
        )
        
        if not timeline_data.entries:
            print("❌ 没有找到时间线数据")
            return
        
        print(f"✅ 成功提取 {len(timeline_data.entries)} 条时间线记录")
        print(f"   总工时: {timeline_data.total_hours:.2f} 小时")
        print(f"   参与人数: {timeline_data.unique_users} 人")
        print(f"   日期范围: {timeline_data.date_range}")
        print()
        
        # Show some sample entries
        print("3. 示例时间线条目:")
        for i, entry in enumerate(timeline_data.entries[:5], 1):
            print(f"   {i}. {entry.date} - {entry.member_name} ({entry.member_email})")
            print(f"      工时: {entry.work_load_hours:.2f}h - {entry.description[:50]}...")
            print()
        
        # Export to CSV
        print("4. 正在导出到 CSV 文件...")
        csv_path = exporter.export_timeline_to_csv(timeline_data, "last_week_timesheet")
        
        print(f"✅ 成功导出到: {csv_path}")
        print(f"   文件大小: {csv_path.stat().st_size} 字节")
        
        # Show extraction statistics
        stats = extractor.get_extraction_stats()
        print(f"\n📊 提取统计:")
        print(f"   工作流缓存: {stats['workflow_cache_size']} 项")
        print(f"   工作项缓存: {stats['work_item_cache_size']} 项")
        print(f"   失败的项目查找: {stats['failed_project_ids_count']} 个")
        
        # Show user breakdown
        if timeline_data.entries:
            print(f"\n👥 用户工时分布:")
            user_hours = {}
            for entry in timeline_data.entries:
                user_key = f"{entry.member_name} ({entry.member_email})"
                user_hours[user_key] = user_hours.get(user_key, 0) + entry.work_load_hours
            
            # Sort by hours descending
            sorted_users = sorted(user_hours.items(), key=lambda x: x[1], reverse=True)
            for user, hours in sorted_users[:10]:  # Show top 10 users
                print(f"   {user}: {hours:.2f}h")
        
        # Show daily breakdown
        print(f"\n📅 每日工时分布:")
        daily_hours = {}
        for entry in timeline_data.entries:
            daily_hours[entry.date] = daily_hours.get(entry.date, 0) + entry.work_load_hours
        
        # Sort by date
        sorted_days = sorted(daily_hours.items())
        for date, hours in sorted_days:
            print(f"   {date}: {hours:.2f}h")
        
        print(f"\n📈 数据概览:")
        print(f"   处理的工作项: {len(all_work_item_ids)} 个")
        print(f"   生成的时间线条目: {len(timeline_data.entries)} 条")
        print(f"   平均每个工作项生成: {len(timeline_data.entries) / len(all_work_item_ids):.2f} 条记录")
        
    except Exception as e:
        print(f"❌ 导出失败: {e}")
        logger.error(f"Export failed: {e}", exc_info=True)

if __name__ == "__main__":
    export_last_week_timesheet() 