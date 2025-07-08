#!/usr/bin/env python3
"""
Business Examples - Demonstrate how to use Meegle Business Layer
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path to import meegle packages
sys.path.insert(0, str(Path(__file__).parent.parent))

from meegle_sdk import MeegleSDK
from meegle_business.timeline.extractor import TimelineExtractor
from meegle_business.export.csv_exporter import CSVExporter
from meegle_business.timeline.models import TimelineData
from config.settings import get_meegle_config, setup_logging

# Initialize logging first
log_file = setup_logging()

logger = logging.getLogger(__name__)
logger.info(f"Business examples started. Log file: {log_file}")


def example_timeline_extraction(sdk: MeegleSDK):
    """Timeline extraction example"""
    print("=" * 50)
    print("Timeline Extraction Example")
    print("=" * 50)
    
    try:
        # Initialize extractor
        extractor = TimelineExtractor(sdk)
        
        # Example chart ID
        chart_id = "7452978372562386950"
        
        print(f"Extracting timeline data from chart: {chart_id}")
        
        # Extract timeline for last 7 days
        timeline_data = extractor.extract_timeline_last_7_days()
        
        if timeline_data.entries:
            print(f"✅ Extracted {len(timeline_data.entries)} timeline entries")
            
            # Show summary
            summary = timeline_data.get_summary()
            print(f"📊 Summary:")
            print(f"  - Total entries: {summary['total_entries']}")
            print(f"  - Valid entries: {summary['valid_entries']}")
            print(f"  - Total hours: {summary['total_hours']:.1f}")
            print(f"  - Unique users: {summary['unique_users']}")
            print(f"  - Date range: {summary['date_range']}")
            
            # Show first few entries
            print("\n📋 First few entries:")
            for i, entry in enumerate(timeline_data.entries[:3], 1):
                print(f"  {i}. {entry.member_email} - {entry.work_load_hours}h on {entry.date}")
                print(f"     Project: {entry.project_code or 'N/A'}")
                print(f"     Activity: {entry.activity_code}")
                print()
        else:
            print("❌ No timeline data extracted")
            
        return timeline_data
        
    except Exception as e:
        print(f"❌ Error extracting timeline: {e}")
        return None


def example_csv_export(timeline_data: TimelineData):
    """CSV export example"""
    print("\n" + "=" * 50)
    print("CSV Export Example")
    print("=" * 50)
    
    if not timeline_data or not timeline_data.entries:
        print("❌ No timeline data to export")
        return
    
    try:
        # Initialize CSV exporter
        exporter = CSVExporter()
        
        print("Exporting timeline data to CSV...")
        
        # Export timeline data
        csv_file = exporter.export_timeline_to_csv(
            timeline_data=timeline_data,
            filename="example_timeline"
        )
        
        print(f"✅ Timeline exported to: {csv_file}")
        
        # Get export summary
        export_summary = exporter.get_export_summary(timeline_data)
        print(f"📊 Export Summary:")
        print(f"  - Output directory: {export_summary['output_dir']}")
        print(f"  - Encoding: {export_summary['encoding']}")
        print(f"  - Export timestamp: {export_summary['export_timestamp']}")
        
        return csv_file
        
    except Exception as e:
        print(f"❌ Error exporting CSV: {e}")
        return None


def example_timeline_filtering(sdk: MeegleSDK):
    """Timeline filtering example"""
    print("\n" + "=" * 50)
    print("Timeline Filtering Example")
    print("=" * 50)
    
    try:
        # Initialize extractor
        extractor = TimelineExtractor(sdk)
        
        # Extract timeline data
        chart_id = "7452978372562386950"
        timeline_data = extractor.extract_timeline_last_7_days()
        
        if not timeline_data.entries:
            print("❌ No timeline data to filter")
            return
        
        print(f"Original data: {len(timeline_data.entries)} entries")
        
        # Filter by date range
        from datetime import datetime, timedelta
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
        
        filtered_by_date = timeline_data.filter_by_date(start_date, end_date)
        print(f"Filtered by date ({start_date} to {end_date}): {len(filtered_by_date.entries)} entries")
        
        # Filter by user (if any entries exist)
        if timeline_data.entries:
            first_user_email = timeline_data.entries[0].member_email
            if first_user_email:
                filtered_by_user = timeline_data.filter_by_user(first_user_email)
                print(f"Filtered by user ({first_user_email}): {len(filtered_by_user.entries)} entries")
        
        print("✅ Filtering examples completed")
        
    except Exception as e:
        print(f"❌ Error in filtering example: {e}")


def example_multiple_exports(sdk: MeegleSDK):
    """Multiple exports example"""
    print("\n" + "=" * 50)
    print("Multiple Exports Example")
    print("=" * 50)
    
    try:
        # Initialize extractor
        extractor = TimelineExtractor(sdk)
        
        # Get chart data
        chart_id = "7452978372562386950"
        chart_data = sdk.charts.get_chart_details(chart_id)
        
        if not chart_data:
            print("❌ Failed to get chart data")
            return
        
        # Extract different time periods
        timelines = {
            'today': extractor.extract_timeline_today(),
            'yesterday': extractor.extract_timeline_yesterday(),
            'last_7_days': extractor.extract_timeline_last_7_days()
        }
        
        # Export all timelines
        exporter = CSVExporter()
        exported_files = exporter.export_multiple_timelines(
            timeline_dict=timelines,
            base_filename="timeline_export"
        )
        
        print(f"✅ Exported {len(exported_files)} files:")
        for file_path in exported_files:
            print(f"  - {file_path}")
        
    except Exception as e:
        print(f"❌ Error in multiple exports: {e}")


def example_complete_workflow(sdk: MeegleSDK):
    """Complete workflow example"""
    print("\n" + "=" * 50)
    print("Complete Workflow Example")
    print("=" * 50)
    
    try:
        # Step 1: Test connection
        print("Step 1: Testing connection...")
        if not sdk.get_client().test_connection():
            print("❌ Connection failed, stopping workflow")
            return
        
        # Step 2: Initialize business layer
        print("Step 2: Initializing business layer...")
        extractor = TimelineExtractor(sdk)
        exporter = CSVExporter()
        
        # Step 3: Extract timeline data
        print("Step 3: Extracting timeline data...")
        chart_id = "7452978372562386950"
        timeline_data = extractor.extract_timeline_last_7_days()
        
        if not timeline_data.entries:
            print("❌ No timeline data extracted")
            return
        
        # Step 4: Export to CSV
        print("Step 4: Exporting to CSV...")
        csv_file = exporter.export_timeline_to_csv(
            timeline_data=timeline_data,
            filename="complete_workflow"
        )
        
        # Step 5: Show results
        print("Step 5: Workflow completed successfully!")
        summary = timeline_data.get_summary()
        print(f"📊 Results:")
        print(f"  - Entries processed: {summary['total_entries']}")
        print(f"  - Valid entries: {summary['valid_entries']}")
        print(f"  - Total hours: {summary['total_hours']:.1f}")
        print(f"  - Exported to: {csv_file}")
        
        print("✅ Complete workflow finished successfully!")
        
    except Exception as e:
        print(f"❌ Error in complete workflow: {e}")


def main():
    """Run all business layer examples"""
    import time
    
    print("🚀 Meegle Business Layer Examples")
    print("=" * 50)
    
    try:
        # Initialize SDK once and reuse
        print("Initializing SDK...")
        sdk = MeegleSDK()
        print("✅ SDK initialized successfully")
        print("=" * 50)
        
        # Run examples with delays to avoid rate limiting
        timeline_data = example_timeline_extraction(sdk)
        if timeline_data:
            example_csv_export(timeline_data)
        
        time.sleep(3)  # Wait between API calls
        example_timeline_filtering(sdk)
        
        time.sleep(3)
        example_multiple_exports(sdk)
        
        time.sleep(3)
        example_complete_workflow(sdk)
        
        print("\n" + "=" * 50)
        print("✅ All business layer examples completed!")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Failed to run examples: {e}")


if __name__ == "__main__":
    main()