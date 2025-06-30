"""
Timeline data extractor for Meegle charts
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Set, Optional

from meegle_sdk import MeegleSDK
from .models import TimelineEntry, TimelineData

logger = logging.getLogger(__name__)


class TimelineExtractor:
    """
    Extract timeline data from Meegle charts
    
    Provides methods to:
    - Extract timeline data for specific dates
    - Process chart data into timeline entries
    - Handle user name to email mapping
    - Support different date ranges
    """
    
    def __init__(self, sdk: MeegleSDK):
        """
        Initialize Timeline Extractor
        
        Args:
            sdk: Meegle SDK instance
        """
        self.sdk = sdk
        
        # Activity type mapping
        self.activity_mapping = {
            'Feature': 'Development',
            'Operation': 'Maintenance', 
            'Bug': 'Maintenance',
            'Task': 'Development',
            'Epic': 'Development',
            'Story': 'Development'
        }
        
        # Cache for user data
        self._user_name_to_email: Optional[Dict[str, str]] = None
        self._projects_cache: Optional[List[Dict[str, Any]]] = None
    
    def _get_name_to_email_mapping(self) -> Dict[str, str]:
        """
        Get cached name to email mapping
        
        Returns:
            Dictionary mapping name_cn to email
        """
        if self._user_name_to_email is None:
            logger.info("Loading user name to email mapping")
            
            # Get all users (will use cache if available)
            users = self.sdk.users.get_all_users()
            self._user_name_to_email = self.sdk.users.get_name_to_email_mapping()
            
            logger.info(f"Loaded {len(self._user_name_to_email)} name-to-email mappings")
        
        return self._user_name_to_email
    
    def _get_projects(self) -> List[Dict[str, Any]]:
        """
        Get cached projects data
        
        Returns:
            List of project dictionaries
        """
        if self._projects_cache is None:
            logger.info("Loading projects data")
            self._projects_cache = self.sdk.work_items.get_all_work_items()
            logger.info(f"Loaded {len(self._projects_cache)} projects")
        
        return self._projects_cache
    
    def extract_timeline_from_chart(self, chart_data: Dict[str, Any], 
                                  target_date: str) -> TimelineData:
        """
        Extract timeline data for a specific date from chart data
        
        Args:
            chart_data: Chart data from Meegle API
            target_date: Target date in YYYY-MM-DD format
            
        Returns:
            TimelineData object with extracted entries
        """
        logger.info(f"Extracting timeline data for date: {target_date}")
        
        if not self._validate_chart_data(chart_data):
            logger.warning("Invalid chart data provided")
            return TimelineData(entries=[])
        
        # Get user mappings and projects
        name_to_email = self._get_name_to_email_mapping()
        projects = self._get_projects()
        
        # Extract raw timeline data
        raw_entries = self._extract_raw_timeline_data(chart_data, target_date)
        
        if not raw_entries:
            logger.warning(f"No data found for date: {target_date}")
            return TimelineData(entries=[], date_range=target_date)
        
        # Process raw entries into TimelineEntry objects
        timeline_entries = []
        
        for raw_entry in raw_entries:
            try:
                timeline_entry = self._process_raw_entry(
                    raw_entry, target_date, name_to_email, projects
                )
                if timeline_entry and timeline_entry.is_valid():
                    timeline_entries.append(timeline_entry)
            except Exception as e:
                logger.warning(f"Failed to process raw entry: {e}")
                continue
        
        logger.info(f"Processed {len(timeline_entries)} valid timeline entries for {target_date}")
        
        return TimelineData(
            entries=timeline_entries,
            date_range=target_date
        )
    
    def _validate_chart_data(self, chart_data: Dict[str, Any]) -> bool:
        """Validate chart data structure"""
        return self.sdk.charts.validate_chart_data(chart_data)
    
    def _extract_raw_timeline_data(self, chart_data: Dict[str, Any], 
                                 target_date: str) -> List[tuple]:
        """
        Extract raw timeline data from chart for specific date
        
        Args:
            chart_data: Chart data dictionary
            target_date: Target date string
            
        Returns:
            List of tuples containing raw timeline data
        """
        timeline_data = []
        dataset = chart_data['chart_data_list'][0]
        
        for data_point in dataset:
            dims = data_point.get('dim', {})
            values = data_point.get('value', {})
            
            # Check if this data point is for our target date
            date = dims.get('3')  # Date dimension
            if not date or date != target_date:
                continue
            
            # Get work hours value
            value = float(values.get('0', 0))
            if value == 0.0:
                continue
            
            # Extract data tuple
            entry = (
                dims.get('0', ''),  # project code
                dims.get('1', ''),  # activity type
                dims.get('2', ''),  # member name
                value               # hours worked
            )
            timeline_data.append(entry)
        
        logger.debug(f"Extracted {len(timeline_data)} raw entries for {target_date}")
        return timeline_data
    
    def _process_raw_entry(self, raw_entry: tuple, target_date: str,
                          name_to_email: Dict[str, str], 
                          projects: List[Dict[str, Any]]) -> Optional[TimelineEntry]:
        """
        Process a raw entry into a TimelineEntry
        
        Args:
            raw_entry: Tuple of (project_code, activity_type, member_name, hours)
            target_date: Target date string
            name_to_email: Name to email mapping
            projects: Projects data
            
        Returns:
            TimelineEntry object or None if processing fails
        """
        project_code, activity_type, member_name, work_hours = raw_entry
        
        # Clean up project code
        if project_code == '(空)':
            project_code = ''
        
        # Map activity type
        mapped_activity = self.activity_mapping.get(activity_type, activity_type)
        
        # Determine project type and status
        project_type = "Project" if project_code else "Product"
        project_status = "Open"
        
        # Get member email
        member_email = name_to_email.get(member_name, '')
        
        # Create description
        if project_code:
            description = f"{mapped_activity} work on {project_code}"
        else:
            description = f"{mapped_activity} work"
        
        # Create timeline entry
        timeline_entry = TimelineEntry(
            project_code=project_code,
            project_type=project_type,
            project_status=project_status,
            project_name=project_code,  # Using project code as name for now
            activity_code=mapped_activity,
            market_region='',
            category_function=mapped_activity,
            entity='',
            member_email=member_email,
            date=target_date,
            work_load_hours=work_hours,
            description=description,
            submission_date=datetime.now().strftime('%Y-%m-%d'),
            manager_signoff='',
            remark=''
        )
        
        return timeline_entry
    
    def extract_current_day_timeline(self, chart_data: Dict[str, Any]) -> TimelineData:
        """
        Extract timeline for current day
        
        Args:
            chart_data: Chart data from API
            
        Returns:
            TimelineData for current day
        """
        current_date = datetime.now().strftime('%Y-%m-%d')
        return self.extract_timeline_from_chart(chart_data, current_date)
    
    def extract_yesterday_timeline(self, chart_data: Dict[str, Any]) -> TimelineData:
        """
        Extract timeline for yesterday
        
        Args:
            chart_data: Chart data from API
            
        Returns:
            TimelineData for yesterday
        """
        yesterday = datetime.now() - timedelta(days=1)
        yesterday_date = yesterday.strftime('%Y-%m-%d')
        return self.extract_timeline_from_chart(chart_data, yesterday_date)
    
    def extract_date_range_timeline(self, chart_data: Dict[str, Any], 
                                  days_back: int = 7) -> TimelineData:
        """
        Extract timeline for a range of dates
        
        Args:
            chart_data: Chart data from API
            days_back: Number of days to go back
            
        Returns:
            TimelineData for the date range
        """
        logger.info(f"Extracting timeline for last {days_back} days")
        
        all_entries = []
        dates = []
        
        # Generate date list
        for i in range(days_back):
            date = datetime.now() - timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            dates.append(date_str)
        
        # Extract data for each date
        for date_str in dates:
            timeline_data = self.extract_timeline_from_chart(chart_data, date_str)
            all_entries.extend(timeline_data.entries)
        
        date_range = f"{dates[-1]} to {dates[0]}"  # oldest to newest
        
        logger.info(f"Extracted {len(all_entries)} total entries for date range: {date_range}")
        
        return TimelineData(
            entries=all_entries,
            date_range=date_range
        )
    
    def extract_timeline_by_chart_id(self, chart_id: str, 
                                   target_date: Optional[str] = None,
                                   days_back: Optional[int] = None) -> TimelineData:
        """
        Extract timeline data by chart ID
        
        Args:
            chart_id: Chart ID to extract from
            target_date: Specific date (YYYY-MM-DD) or None
            days_back: Number of days back or None
            
        Returns:
            TimelineData object
        """
        logger.info(f"Extracting timeline from chart ID: {chart_id}")
        
        # Get chart data
        chart_data = self.sdk.charts.get_chart_details(chart_id)
        
        if not chart_data:
            logger.error(f"Failed to retrieve chart data for ID: {chart_id}")
            return TimelineData(entries=[])
        
        # Extract based on parameters
        if target_date:
            return self.extract_timeline_from_chart(chart_data, target_date)
        elif days_back:
            return self.extract_date_range_timeline(chart_data, days_back)
        else:
            # Default to current day
            return self.extract_current_day_timeline(chart_data)
    
    def clear_cache(self):
        """Clear cached data"""
        logger.info("Clearing timeline extractor cache")
        self._user_name_to_email = None
        self._projects_cache = None 