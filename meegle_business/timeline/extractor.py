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
    
    Chart Dimensions:
    - Dimension 0: Project Code (used to lookup project info via work items)
    - Dimension 1: Feature ID (used to lookup feature info from story work items) 
    - Dimension 2: User Name (converted to email via user mapping)
    """
    
    def __init__(self, sdk: MeegleSDK):
        """
        Initialize Timeline Extractor
        
        Args:
            sdk: Meegle SDK instance
        """
        self.sdk = sdk
        self._users_cache = None
        self._projects_cache = None
        self._stories_cache = None
        
    def get_users_cache(self) -> Dict[str, Any]:
        """Get cached user data, loading if not already cached"""
        if self._users_cache is None:
            logger.info("Loading users cache...")
            try:
                self._users_cache = self.sdk.users.get_all_users()
                logger.info(f"Loaded {len(self._users_cache)} users")
            except Exception as e:
                logger.warning(f"Failed to load users: {e}")
                self._users_cache = {}
        return self._users_cache
    
    def get_projects_cache(self) -> List[Dict[str, Any]]:
        """Get cached project data, loading if not already cached"""
        if self._projects_cache is None:
            logger.info("Loading projects cache...")
            try:
                self._projects_cache = self.sdk.work_items.get_projects()
                logger.info(f"Loaded {len(self._projects_cache)} projects")
            except Exception as e:
                logger.warning(f"Failed to load projects: {e}")
                self._projects_cache = []
        return self._projects_cache
    
    def get_stories_cache(self) -> List[Dict[str, Any]]:
        """Get cached story/feature data, loading if not already cached"""
        if self._stories_cache is None:
            logger.info("Loading stories cache...")
            try:
                self._stories_cache = self.sdk.work_items.get_stories()
                logger.info(f"Loaded {len(self._stories_cache)} stories")
            except Exception as e:
                logger.warning(f"Failed to load stories: {e}")
                self._stories_cache = []
        return self._stories_cache
    
    def get_user_email_by_name(self, username: str) -> str:
        """Convert username to email address"""
        users = self.get_users_cache()
        
        # Try to find user by various name fields
        for user_key, user in users.items():
            # Check displayName, name, username fields
            if (user.get('displayName') == username or 
                user.get('name') == username or 
                user.get('username') == username or
                user.get('login') == username or
                user.get('name_cn') == username or
                user.get('name_en') == username):
                return user.get('email', user.get('emailAddress', f"{username}@unknown.com"))
        
        # If not found, generate email from username
        return f"{username.lower().replace(' ', '.')}@company.com"
    
    def get_project_info_by_code(self, project_code: str) -> Dict[str, str]:
        """Get project information by project code"""
        projects = self.get_projects_cache()
        
        for project in projects:
            # Check the 'name' field for project code (as specified by user)
            project_name_field = project.get('name')
            if project_name_field == project_code:
                # Extract project information using correct field mappings
                project_info = {
                    'project_type': self._extract_field_value(project, ['template'], 'Product'),
                    'project_status': self._extract_field_value(project, ['work_item_status'], 'Open'),
                    'project_name': self._extract_field_value(project, ['field_28829a'], project_code)
                }
                logger.debug(f"Found project info for {project_code}: {project_info}")
                return project_info
            
            # Also check in fields structure if direct field lookup fails
            project_fields = project.get('fields', []) if 'fields' in project else []
            if isinstance(project_fields, list):
                # Convert fields list to dictionary for easier lookup
                fields_dict = {}
                for field in project_fields:
                    if isinstance(field, dict) and 'field_key' in field and 'field_value' in field:
                        fields_dict[field['field_key']] = field['field_value']
                
                # Check if the 'name' field in fields matches project_code
                if fields_dict.get('name') == project_code:
                    project_info = {
                        'project_type': fields_dict.get('template', 'Product'),
                        'project_status': fields_dict.get('work_item_status', 'Open'),
                        'project_name': fields_dict.get('field_28829a', project_code)
                    }
                    logger.debug(f"Found project info in fields for {project_code}: {project_info}")
                    return project_info
        
        logger.warning(f"Project not found for code: {project_code}")
        return {
            'project_type': 'Product',
            'project_status': 'Open', 
            'project_name': project_code
        }
    
    def get_feature_info_by_id(self, feature_id: str) -> Dict[str, str]:
        """Get feature information by feature ID"""
        stories = self.get_stories_cache()
        
        for story in stories:
            # Check various possible field names for story ID
            story_fields = story.get('fields', []) if 'fields' in story else []
            
            # Extract field values from the fields list
            fields_dict = {}
            if isinstance(story_fields, list):
                for field in story_fields:
                    if isinstance(field, dict) and 'field_key' in field and 'field_value' in field:
                        fields_dict[field['field_key']] = field['field_value']
            
            story_id_fields = [
                story.get('id'),
                fields_dict.get('id'),
                fields_dict.get('System.Id'),
                story.get('workItemId'),
                story.get('key')
            ]
            
            if feature_id in [str(field) for field in story_id_fields if field is not None]:
                # Extract feature information
                feature_info = {
                    'activity_code': self._extract_field_value(story, ['workflow_type', 'workflowType', 'type'], 'Development'),
                    'business_line': self._extract_field_value(story, ['business_line', 'businessLine', 'area'], 'Product'),
                    'submission_date': self._extract_submission_date(story),
                    'description': self._extract_field_value(story, ['name', 'title', 'description'], 'N/A'),
                    'manager_signoff': '',
                    'remark': f"@https://project.larksuite.com/advance_ai/story/detail/{feature_id}"
                }
                logger.debug(f"Found feature info for {feature_id}: {feature_info}")
                return feature_info
        
        logger.warning(f"Feature not found for ID: {feature_id}")
        return {
            'activity_code': 'Development',
            'business_line': 'Product',
            'submission_date': datetime.now().strftime('%Y-%m-%d'),
            'description': f"Feature {feature_id}",
            'manager_signoff': '',
            'remark': f"@https://project.larksuite.com/advance_ai/story/detail/{feature_id}"
        }
    
    def _extract_field_value(self, work_item: Dict[str, Any], field_names: List[str], default: str = 'N/A') -> str:
        """Extract field value from work item, trying multiple possible field names"""
        # Try direct fields first
        for field_name in field_names:
            if field_name in work_item:
                value = work_item[field_name]
                # Handle different value types
                if isinstance(value, dict):
                    # For template field, we might want to use a default value
                    if field_name == 'template':
                        return 'Product'  # Default template type
                    # For work_item_status, extract the state_key
                    elif field_name == 'work_item_status' and 'state_key' in value:
                        return value['state_key']
                    # For other dict values, try to get 'name' field
                    elif 'name' in value:
                        return value['name']
                    # For dict values, try to get 'value' field
                    elif 'value' in value:
                        return str(value['value'])
                elif isinstance(value, str):
                    return value
                elif value is not None:
                    return str(value)
        
        # Try nested fields structure (fields is a list of field objects)
        fields_list = work_item.get('fields', [])
        if isinstance(fields_list, list):
            # Convert fields list to dictionary for easier lookup
            fields_dict = {}
            for field in fields_list:
                if isinstance(field, dict) and 'field_key' in field and 'field_value' in field:
                    fields_dict[field['field_key']] = field['field_value']
            
            for field_name in field_names:
                if field_name in fields_dict:
                    value = fields_dict[field_name]
                    # Handle different value types
                    if isinstance(value, dict):
                        # For template field, we might want to use a default value
                        if field_name == 'template':
                            return 'Product'  # Default template type
                        # For work_item_status, extract the state_key
                        elif field_name == 'work_item_status' and 'state_key' in value:
                            return value['state_key']
                        # For other dict values, try to get 'name' field
                        elif 'name' in value:
                            return value['name']
                        # For dict values, try to get 'value' field
                        elif 'value' in value:
                            return str(value['value'])
                    elif isinstance(value, str):
                        return value
                    elif value is not None:
                        return str(value)
            
            # Try System.* fields (Azure DevOps style)
            for field_name in field_names:
                system_field = f"System.{field_name.title()}"
                if system_field in fields_dict:
                    value = fields_dict[system_field]
                    if isinstance(value, dict) and 'name' in value:
                        return value['name']
                    elif isinstance(value, str):
                        return value
        
        return default
    
    def _extract_submission_date(self, work_item: Dict[str, Any]) -> str:
        """Extract submission date from work item"""
        date_fields = [
            'created_at', 'createdAt', 'creation_date', 'creationDate',
            'submitted_at', 'submittedAt', 'submission_date', 'submissionDate',
            'updated_at', 'updatedAt', 'modified_date', 'modifiedDate'
        ]
        
        # Try direct fields
        for field_name in date_fields:
            date_value = work_item.get(field_name)
            if date_value:
                return self._parse_date(date_value)
        
        # Try nested fields structure (fields is a list of field objects)
        fields_list = work_item.get('fields', [])
        if isinstance(fields_list, list):
            # Convert fields list to dictionary for easier lookup
            fields_dict = {}
            for field in fields_list:
                if isinstance(field, dict) and 'field_key' in field and 'field_value' in field:
                    fields_dict[field['field_key']] = field['field_value']
            
            for field_name in date_fields:
                date_value = fields_dict.get(field_name)
                if date_value:
                    return self._parse_date(date_value)
            
            # Try System.* fields (Azure DevOps style)
            system_date_fields = [
                'System.CreatedDate', 'System.ChangedDate', 'System.AuthorizedDate'
            ]
            for field_name in system_date_fields:
                date_value = fields_dict.get(field_name)
                if date_value:
                    return self._parse_date(date_value)
        
        # Default to current date
        return datetime.now().strftime('%Y-%m-%d')
    
    def _parse_date(self, date_value: Any) -> str:
        """Parse various date formats to YYYY-MM-DD string"""
        if isinstance(date_value, str):
            try:
                # Try parsing ISO format
                dt = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                return dt.strftime('%Y-%m-%d')
            except:
                try:
                    # Try parsing other common formats
                    for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y/%m/%d']:
                        try:
                            dt = datetime.strptime(date_value, fmt)
                            return dt.strftime('%Y-%m-%d')
                        except:
                            continue
                except:
                    pass
        elif isinstance(date_value, (int, float)):
            try:
                # Assume Unix timestamp
                if date_value > 1e10:  # Milliseconds
                    date_value = date_value / 1000
                dt = datetime.fromtimestamp(date_value)
                return dt.strftime('%Y-%m-%d')
            except:
                pass
        
        # Default to current date if parsing fails
        return datetime.now().strftime('%Y-%m-%d')

    def _process_chart_data(self, chart_data: Dict[str, Any], target_date: datetime) -> List[TimelineEntry]:
        """
        Process chart data into timeline entries
        
        Args:
            chart_data: Chart data from API
            target_date: Target date for the timeline
            
        Returns:
            List of timeline entries
        """
        entries = []
        
        if not chart_data or 'chart_data_list' not in chart_data:
            logger.warning("No chart data list found")
            return entries
            
        chart_data_list = chart_data['chart_data_list']
        if not chart_data_list:
            logger.warning("Empty chart data list")
            return entries
            
        # The chart_data_list is a nested list, get the actual data entries
        actual_data_entries = chart_data_list[0] if chart_data_list and isinstance(chart_data_list[0], list) else []
        logger.info(f"Processing {len(actual_data_entries)} chart data entries")
        
        # Process each chart data entry
        for i, data_entry in enumerate(actual_data_entries):
            try:
                # Each entry has 'dim' (dimensions) and 'value' (values) fields
                if not isinstance(data_entry, dict) or 'dim' not in data_entry or 'value' not in data_entry:
                    logger.warning(f"Invalid data entry format at index {i}: {data_entry}")
                    continue
                
                dim = data_entry['dim']
                value = data_entry['value']
                
                # Check if dim and value are dictionaries
                if not isinstance(dim, dict) or not isinstance(value, dict):
                    logger.warning(f"Invalid dim/value format at index {i}: dim={type(dim)}, value={type(value)}")
                    continue
                
                # Extract dimensions
                project_code = str(dim.get('0', '')) if dim.get('0') else ""
                feature_id = str(dim.get('1', '')) if dim.get('1') else ""
                user_name = str(dim.get('2', '')) if dim.get('2') else ""
                entry_date = str(dim.get('3', '')) if dim.get('3') else ""
                
                # Extract work hours from value
                work_hours_str = str(value.get('0', '0.00')) if value.get('0') else "0.00"
                try:
                    work_hours = float(work_hours_str)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid work hours value: {work_hours_str}")
                    work_hours = 0.0
                
                logger.debug(f"Processing entry {i}: project={project_code}, feature={feature_id}, user={user_name}, date={entry_date}, hours={work_hours}")
                
                # Skip entries with no work hours or invalid user name
                if work_hours <= 0 or not user_name or user_name == '(空)':
                    continue
                
                # Check if entry date matches target date (if specified)
                if target_date and entry_date != target_date.strftime('%Y-%m-%d'):
                    continue
                    
                # Get project information
                project_info = self.get_project_info_by_code(project_code)
                
                # Get feature information
                feature_info = self.get_feature_info_by_id(feature_id)
                
                # Get user email
                user_email = self.get_user_email_by_name(user_name)
                
                # Create timeline entry
                entry = TimelineEntry(
                    date=entry_date or (target_date.strftime('%Y-%m-%d') if target_date else entry_date),
                    project_code=project_code,
                    project_type=project_info['project_type'],
                    project_status=project_info['project_status'],
                    project_name=project_info['project_name'],
                    activity_code=feature_info['activity_code'],
                    market_region='',  # Default empty
                    category_function=feature_info['business_line'],  # Use business_line for category_function
                    entity='',  # Default empty
                    member_email=user_email,
                    work_load_hours=work_hours,
                    submission_date=feature_info['submission_date'],
                    description=feature_info['description'],
                    manager_signoff=feature_info['manager_signoff'],
                    remark=feature_info['remark']
                )
                
                entries.append(entry)
                
            except Exception as e:
                logger.error(f"Error processing chart data entry {i}: {e}")
                continue
                
        logger.info(f"Successfully processed {len(entries)} timeline entries")
        return entries

    def extract_timeline_for_date(self, target_date: datetime) -> TimelineData:
        """
        Extract timeline data for a specific date
        
        Args:
            target_date: Date to extract timeline data for
            
        Returns:
            TimelineData object containing entries for the date
        """
        logger.info(f"Extracting timeline data for date: {target_date.strftime('%Y-%m-%d')}")
        
        try:
            # Get chart data for the specific date
            chart_data = self.sdk.charts.get_chart_details("7452978372562386950")
            
            if not chart_data:
                logger.warning("No chart data received")
                return TimelineData(entries=[], total_hours=0.0, unique_users=0, date_range="")
            
            entries = self._process_chart_data(chart_data, target_date)
            
            # Calculate statistics
            total_hours = sum(entry.work_load_hours for entry in entries)
            unique_users = len(set(entry.member_email for entry in entries))
            date_range = target_date.strftime('%Y-%m-%d')
            
            logger.info(f"Extracted {len(entries)} timeline entries, {total_hours} total hours, {unique_users} unique users")
            
            return TimelineData(
                entries=entries,
                total_hours=total_hours,
                unique_users=unique_users,
                date_range=date_range
            )
            
        except Exception as e:
            logger.error(f"Failed to extract timeline data for {target_date}: {e}")
            return TimelineData(entries=[], total_hours=0.0, unique_users=0, date_range="")

    def extract_timeline_for_range(self, start_date: datetime, end_date: datetime) -> TimelineData:
        """
        Extract timeline data for a date range
        
        Args:
            start_date: Start date of the range
            end_date: End date of the range (inclusive)
            
        Returns:
            TimelineData object containing entries for the range
        """
        logger.info(f"Extracting timeline data for range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        all_entries = []
        current_date = start_date
        
        while current_date <= end_date:
            daily_data = self.extract_timeline_for_date(current_date)
            all_entries.extend(daily_data.entries)
            current_date += timedelta(days=1)
        
        # Calculate statistics
        total_hours = sum(entry.work_load_hours for entry in all_entries)
        unique_users = len(set(entry.member_email for entry in all_entries))
        date_range = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        
        logger.info(f"Extracted {len(all_entries)} total timeline entries for range")
        
        return TimelineData(
            entries=all_entries,
            total_hours=total_hours,
            unique_users=unique_users,
            date_range=date_range
        )

    def extract_timeline_today(self) -> TimelineData:
        """Extract timeline data for today"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        return self.extract_timeline_for_date(today)

    def extract_timeline_yesterday(self) -> TimelineData:
        """Extract timeline data for yesterday"""
        yesterday = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
        return self.extract_timeline_for_date(yesterday)

    def extract_timeline_last_7_days(self) -> TimelineData:
        """Extract timeline data for the last 7 days"""
        end_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
        start_date = end_date - timedelta(days=6)
        return self.extract_timeline_for_range(start_date, end_date) 