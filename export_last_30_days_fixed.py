#!/usr/bin/env python3
"""
Export last 30 days timesheet with fixed pagination
"""

import logging
from meegle_sdk import MeegleSDK
from meegle_business.timeline.view_extractor import ViewTimelineExtractor
from meegle_business.export.csv_exporter import CSVExporter

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def export_last_30_days_timesheet_fixed():
    """Export last 30 days timesheet with fixed pagination"""
    
    print("正在导出近30天 timesheet (修复分页后)...")
    print("=" * 50)
    
    try:
        # Initialize SDK, extractor, and exporter
        sdk = MeegleSDK()
        extractor = ViewTimelineExtractor(sdk)
        exporter = CSVExporter()
        
        # Use the correct view ID
        view_id = "OXnKluvHR"
        
        # Show date range that will be processed
        start_date, end_date = extractor._get_last_n_days_range(30)
        print(f"日期范围: {start_date} 到 {end_date}")
        print(f"视图 ID: {view_id}")
        
        # First check how many work items we'll process
        print("\n1. 检查视图中的工作项数量:")
        all_work_item_ids = sdk.work_items.get_all_work_items_in_view(view_id)
        print(f"   视图中总工作项数量: {len(all_work_item_ids)}")
        print()
        
        # Extract timeline data for last 30 days
        print("2. 开始提取近30天的时间线数据...")
        timeline_data = extractor.extract_timeline_last_n_days(
            view_id=view_id,
            days=30,
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
        
        # Export to CSV
        print("3. 正在导出到 CSV 文件...")
        csv_path = exporter.export_timeline_to_csv(timeline_data, "last_30_days_timesheet_fixed.csv")
        
        print(f"✅ 成功导出到: {csv_path}")
        print(f"   文件大小: {csv_path.stat().st_size} 字节")
        
        # Show extraction statistics
        stats = extractor.get_extraction_stats()
        print(f"\n📊 提取统计:")
        print(f"   工作流缓存: {stats['workflow_cache_size']} 项")
        print(f"   工作项缓存: {stats['work_item_cache_size']} 项")
        print(f"   失败的项目查找: {stats['failed_project_ids_count']} 个")
        
        # Compare with previous export
        print(f"\n📈 对比:")
        print(f"   修复前: 处理 200 个工作项")
        print(f"   修复后: 处理 {len(all_work_item_ids)} 个工作项")
        print(f"   增加: {len(all_work_item_ids) - 200} 个工作项 (+{((len(all_work_item_ids) - 200) / 200 * 100):.1f}%)")
        
    except Exception as e:
        print(f"❌ 导出失败: {e}")
        logger.error(f"Export failed: {e}", exc_info=True)

if __name__ == "__main__":
    export_last_30_days_timesheet_fixed() 