#!/usr/bin/env python3
"""
Date Filtering Examples for ViewTimelineExtractor

This script demonstrates how to use the date filtering functionality
to extract timeline data for specific date ranges.
"""

import logging
from datetime import datetime, timedelta

from meegle_sdk import MeegleSDK
from meegle_business.timeline.view_extractor import ViewTimelineExtractor
from meegle_business.export.csv_exporter import CSVExporter

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def example_date_filtering():
    """Example: Extract timeline data with date filtering"""
    
    # Initialize SDK, extractor, and exporter
    sdk = MeegleSDK()
    extractor = ViewTimelineExtractor(sdk)
    exporter = CSVExporter()
    
    # Replace with your actual view ID
    view_id = "6765e4b8b6e59e55b79b9b5b"
    
    print("Date Filtering Examples")
    print("=" * 50)
    
    # Example 1: Extract data for a specific date range
    print("\n1. Extract data for specific date range")
    start_date = "2024-12-01"
    end_date = "2024-12-07"
    
    timeline_data = extractor.extract_timeline_from_view(
        view_id,
        start_date=start_date,
        end_date=end_date
    )
    
    print(f"   Date range: {start_date} to {end_date}")
    print(f"   Entries: {len(timeline_data.entries)}")
    print(f"   Total hours: {timeline_data.total_hours:.2f}")
    print(f"   Unique users: {timeline_data.unique_users}")
    
    # Export to CSV
    filepath = exporter.export_view_timeline_to_csv(
        view_id, extractor,
        filename="custom_date_range",
        start_date=start_date,
        end_date=end_date
    )
    print(f"   Exported to: {filepath}")

def example_convenience_methods():
    """Example: Use convenience methods for common date ranges"""
    
    sdk = MeegleSDK()
    extractor = ViewTimelineExtractor(sdk)
    exporter = CSVExporter()
    view_id = "6765e4b8b6e59e55b79b9b5b"
    
    print("\n" + "=" * 50)
    print("Convenience Methods Examples")
    print("=" * 50)
    
    # Example 2: This week
    print("\n2. Extract this week's data")
    timeline_data = extractor.extract_timeline_this_week(view_id)
    print(f"   This week entries: {len(timeline_data.entries)}")
    print(f"   Date range: {timeline_data.date_range}")
    
    # Export this week's data
    filepath = exporter.export_view_timeline_this_week(view_id, extractor)
    print(f"   Exported to: {filepath}")
    
    # Example 3: Last week
    print("\n3. Extract last week's data")
    timeline_data = extractor.extract_timeline_last_week(view_id)
    print(f"   Last week entries: {len(timeline_data.entries)}")
    print(f"   Date range: {timeline_data.date_range}")
    
    # Export last week's data
    filepath = exporter.export_view_timeline_last_week(view_id, extractor)
    print(f"   Exported to: {filepath}")
    
    # Example 4: This month
    print("\n4. Extract this month's data")
    timeline_data = extractor.extract_timeline_this_month(view_id)
    print(f"   This month entries: {len(timeline_data.entries)}")
    print(f"   Date range: {timeline_data.date_range}")
    
    # Export this month's data
    filepath = exporter.export_view_timeline_this_month(view_id, extractor)
    print(f"   Exported to: {filepath}")
    
    # Example 5: Last month
    print("\n5. Extract last month's data")
    timeline_data = extractor.extract_timeline_last_month(view_id)
    print(f"   Last month entries: {len(timeline_data.entries)}")
    print(f"   Date range: {timeline_data.date_range}")
    
    # Export last month's data
    filepath = exporter.export_view_timeline_last_month(view_id, extractor)
    print(f"   Exported to: {filepath}")
    
    # Example 6: This quarter
    print("\n6. Extract this quarter's data")
    timeline_data = extractor.extract_timeline_this_quarter(view_id)
    print(f"   This quarter entries: {len(timeline_data.entries)}")
    print(f"   Date range: {timeline_data.date_range}")
    
    # Export this quarter's data
    filepath = exporter.export_view_timeline_this_quarter(view_id, extractor)
    print(f"   Exported to: {filepath}")
    
    # Example 7: Last N days
    print("\n7. Extract last 14 days data")
    timeline_data = extractor.extract_timeline_last_n_days(view_id, 14)
    print(f"   Last 14 days entries: {len(timeline_data.entries)}")
    print(f"   Date range: {timeline_data.date_range}")
    
    # Export last 14 days data
    filepath = exporter.export_view_timeline_last_n_days(view_id, extractor, 14)
    print(f"   Exported to: {filepath}")

def example_comparison():
    """Example: Compare different time periods"""
    
    sdk = MeegleSDK()
    extractor = ViewTimelineExtractor(sdk)
    view_id = "6765e4b8b6e59e55b79b9b5b"
    
    print("\n" + "=" * 50)
    print("Time Period Comparison")
    print("=" * 50)
    
    # Get data for different periods
    this_week = extractor.extract_timeline_this_week(view_id)
    last_week = extractor.extract_timeline_last_week(view_id)
    this_month = extractor.extract_timeline_this_month(view_id)
    last_month = extractor.extract_timeline_last_month(view_id)
    
    print(f"\nWorkload Comparison:")
    print(f"   This week:  {this_week.total_hours:.2f} hours ({len(this_week.entries)} entries)")
    print(f"   Last week:  {last_week.total_hours:.2f} hours ({len(last_week.entries)} entries)")
    print(f"   This month: {this_month.total_hours:.2f} hours ({len(this_month.entries)} entries)")
    print(f"   Last month: {last_month.total_hours:.2f} hours ({len(last_month.entries)} entries)")
    
    # Calculate weekly averages
    if this_month.total_hours > 0:
        weekly_avg_this_month = this_month.total_hours / 4  # Approximate
        print(f"\nWeekly average this month: {weekly_avg_this_month:.2f} hours")
    
    if last_month.total_hours > 0:
        weekly_avg_last_month = last_month.total_hours / 4  # Approximate
        print(f"Weekly average last month: {weekly_avg_last_month:.2f} hours")

def example_advanced_filtering():
    """Example: Advanced filtering scenarios"""
    
    sdk = MeegleSDK()
    extractor = ViewTimelineExtractor(sdk)
    exporter = CSVExporter()
    view_id = "6765e4b8b6e59e55b79b9b5b"
    
    print("\n" + "=" * 50)
    print("Advanced Filtering Examples")
    print("=" * 50)
    
    # Example: Extract data for a specific sprint (2 weeks)
    print("\n8. Extract data for a 2-week sprint")
    today = datetime.now()
    sprint_start = (today - timedelta(days=13)).strftime('%Y-%m-%d')
    sprint_end = today.strftime('%Y-%m-%d')
    
    timeline_data = extractor.extract_timeline_from_view(
        view_id,
        start_date=sprint_start,
        end_date=sprint_end
    )
    
    print(f"   Sprint period: {sprint_start} to {sprint_end}")
    print(f"   Sprint entries: {len(timeline_data.entries)}")
    print(f"   Sprint total hours: {timeline_data.total_hours:.2f}")
    
    # Export sprint data
    filepath = exporter.export_view_timeline_to_csv(
        view_id, extractor,
        filename="sprint_timeline",
        start_date=sprint_start,
        end_date=sprint_end
    )
    print(f"   Exported to: {filepath}")
    
    # Example: Extract data for business days only (Monday to Friday)
    print("\n9. Extract weekday-only data (last 7 business days)")
    
    # Calculate last 7 business days
    business_days = []
    current_date = today
    while len(business_days) < 7:
        if current_date.weekday() < 5:  # Monday=0, Friday=4
            business_days.append(current_date)
        current_date -= timedelta(days=1)
    
    business_start = business_days[-1].strftime('%Y-%m-%d')
    business_end = business_days[0].strftime('%Y-%m-%d')
    
    timeline_data = extractor.extract_timeline_from_view(
        view_id,
        start_date=business_start,
        end_date=business_end
    )
    
    print(f"   Business days: {business_start} to {business_end}")
    print(f"   Business entries: {len(timeline_data.entries)}")
    print(f"   Business hours: {timeline_data.total_hours:.2f}")
    
    # Filter out weekends from the timeline data (additional processing)
    weekday_entries = []
    for entry in timeline_data.entries:
        try:
            entry_date = datetime.strptime(entry.date, '%Y-%m-%d')
            if entry_date.weekday() < 5:  # Monday to Friday
                weekday_entries.append(entry)
        except ValueError:
            continue
    
    print(f"   Weekday-only entries: {len(weekday_entries)}")
    weekday_hours = sum(entry.work_load_hours for entry in weekday_entries)
    print(f"   Weekday-only hours: {weekday_hours:.2f}")

def show_available_date_ranges():
    """Show all available date ranges"""
    
    sdk = MeegleSDK()
    extractor = ViewTimelineExtractor(sdk)
    
    print("\n" + "=" * 50)
    print("Available Date Ranges")
    print("=" * 50)
    
    # Get all date ranges
    ranges = {
        "This week": extractor._get_this_week_range(),
        "Last week": extractor._get_last_week_range(),
        "This month": extractor._get_this_month_range(),
        "Last month": extractor._get_last_month_range(),
        "This quarter": extractor._get_this_quarter_range(),
        "Last quarter": extractor._get_last_quarter_range(),
        "Last 7 days": extractor._get_last_n_days_range(7),
        "Last 30 days": extractor._get_last_n_days_range(30),
        "Last 90 days": extractor._get_last_n_days_range(90),
    }
    
    for name, (start, end) in ranges.items():
        print(f"   {name:<15}: {start} to {end}")
    
    print(f"\nToday is: {datetime.now().strftime('%Y-%m-%d (%A)')}")

if __name__ == "__main__":
    try:
        # Show available date ranges first
        show_available_date_ranges()
        
        # Run examples
        example_date_filtering()
        example_convenience_methods()
        example_comparison()
        example_advanced_filtering()
        
        print("\n" + "=" * 50)
        print("All examples completed successfully!")
        
    except KeyboardInterrupt:
        print("\nExamples interrupted by user")
    except Exception as e:
        logger.error(f"Example failed: {e}")
        raise 