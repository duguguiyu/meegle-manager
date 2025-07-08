"""
View-based Timeline Extractor for Meegle workflows
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Set, Optional, Tuple

from meegle_sdk import MeegleSDK
from .models import TimelineEntry, TimelineData
from .extractor import TimelineExtractor

logger = logging.getLogger(__name__)


class ViewTimelineExtractor(TimelineExtractor):
    """
    Extract timeline data from Meegle views and workflows
    
    This extractor works differently from the chart-based extractor:
    1. Gets work items from a specific view
    2. Extracts workflow information for each work item
    3. Calculates workload distribution based on schedules
    4. Generates timeline entries for each person/day/workflow
    
    Workflow Processing:
    - For nodes with sub-tasks: distribute points across tasks and owners
    - For nodes without sub-tasks: use node-level scheduling
    - Calculate daily workload based on date ranges and points
    """
    
    def __init__(self, sdk: MeegleSDK):
        """
        Initialize View Timeline Extractor
        
        Args:
            sdk: Meegle SDK instance
        """
        super().__init__(sdk)
        self._workflow_cache = {}
        self._work_item_cache = {}
        self._failed_project_ids = set()  # Track failed project lookups to avoid retries
        self._batch_size = 50  # Process work items in batches
        
    def extract_timeline_from_view(self, view_id: str, work_item_type_key: str = "story", 
                                  max_items: Optional[int] = None) -> TimelineData:
        """
        Extract timeline data from a specific view
        
        Args:
            view_id: View ID to extract timeline from
            work_item_type_key: Type of work items to process (default: "story")
            max_items: Maximum number of work items to process (for testing/debugging)
            
        Returns:
            TimelineData object containing timeline entries
        """
        logger.info(f"Extracting timeline from view: {view_id}")
        
        try:
            # Step 1: Get work item IDs from view
            work_item_ids = self.sdk.work_items.get_all_work_items_in_view(view_id)
            if not work_item_ids:
                logger.warning(f"No work items found in view {view_id}")
                return TimelineData(entries=[], total_hours=0.0, unique_users=0, date_range="")
            
            # Limit items if specified (for testing)
            if max_items and len(work_item_ids) > max_items:
                work_item_ids = work_item_ids[:max_items]
                logger.info(f"Limited to first {max_items} work items for testing")
            
            logger.info(f"Found {len(work_item_ids)} work items in view {view_id}")
            
            # Step 2: Get work item details in batches
            all_entries = []
            processed_count = 0
            
            for i in range(0, len(work_item_ids), self._batch_size):
                batch_ids = work_item_ids[i:i + self._batch_size]
                logger.info(f"Processing batch {i//self._batch_size + 1}: items {i+1}-{min(i+self._batch_size, len(work_item_ids))}")
                
                try:
                    work_items = self.sdk.work_items.get_work_items_by_ids(batch_ids, work_item_type_key)
                    logger.info(f"Retrieved details for {len(work_items)} work items in batch")
                    
                    # Process each work item in the batch
                    for work_item in work_items:
                        try:
                            entries = self._process_work_item_workflow(work_item, work_item_type_key)
                            all_entries.extend(entries)
                            processed_count += 1
                            
                            if processed_count % 10 == 0:
                                logger.info(f"Processed {processed_count}/{len(work_item_ids)} work items, "
                                          f"generated {len(all_entries)} timeline entries so far")
                            
                        except Exception as e:
                            logger.error(f"Error processing work item {work_item.get('id')}: {e}")
                            continue
                            
                except Exception as e:
                    logger.error(f"Error processing batch {i//self._batch_size + 1}: {e}")
                    continue
            
            # Step 3: Calculate statistics
            total_hours = sum(entry.work_load_hours for entry in all_entries)
            unique_users = len(set(entry.member_email for entry in all_entries))
            date_range = self._calculate_date_range(all_entries)
            
            logger.info(f"Extraction complete: {len(all_entries)} timeline entries from view {view_id}")
            logger.info(f"Total hours: {total_hours:.2f}, Unique users: {unique_users}")
            logger.info(f"Failed project lookups: {len(self._failed_project_ids)}")
            
            return TimelineData(
                entries=all_entries,
                total_hours=total_hours,
                unique_users=unique_users,
                date_range=date_range
            )
            
        except Exception as e:
            logger.error(f"Failed to extract timeline from view {view_id}: {e}")
            return TimelineData(entries=[], total_hours=0.0, unique_users=0, date_range="")
    
    def _process_work_item_workflow(self, work_item: Dict[str, Any], work_item_type_key: str) -> List[TimelineEntry]:
        """
        Process a work item's workflow to extract timeline entries
        
        Args:
            work_item: Work item data
            work_item_type_key: Work item type key
            
        Returns:
            List of timeline entries for this work item
        """
        work_item_id = work_item.get('id')
        if not work_item_id:
            logger.warning(f"Work item has no ID: {work_item}")
            return []
        
        logger.debug(f"Processing workflow for work item {work_item_id}")
        
        try:
            # Get workflow nodes
            nodes = self.sdk.workflows.get_workflow_nodes(work_item_id, work_item_type_key)
            if not nodes:
                logger.debug(f"No workflow nodes found for work item {work_item_id}")
                return []
            
            # Extract project information from work item (with optimized caching)
            project_info = self._extract_project_info_from_work_item(work_item)
            
            # Process each node to generate timeline entries
            all_entries = []
            for node in nodes:
                try:
                    node_entries = self._process_workflow_node(node, work_item, project_info)
                    all_entries.extend(node_entries)
                    logger.debug(f"Node {node.get('id')}: {len(node_entries)} entries")
                except Exception as e:
                    logger.debug(f"Error processing node {node.get('id')}: {e}")
                    continue
            
            return all_entries
            
        except Exception as e:
            logger.debug(f"Error processing workflow for work item {work_item_id}: {e}")
            return []
    
    def _process_workflow_node(self, node: Dict[str, Any], work_item: Dict[str, Any], 
                              project_info: Dict[str, str]) -> List[TimelineEntry]:
        """
        Process a workflow node to generate timeline entries
        
        Args:
            node: Workflow node data
            work_item: Work item data
            project_info: Project information
            
        Returns:
            List of timeline entries for this node
        """
        node_id = node.get('id')
        node_name = node.get('name', node_id)
        
        # Extract schedules from node
        schedules = self.sdk.workflows.extract_node_schedules(node)
        if not schedules:
            logger.debug(f"No schedules found for node {node_id}")
            return []
        
        entries = []
        for schedule in schedules:
            try:
                schedule_entries = self._process_schedule(schedule, work_item, project_info, node_name)
                entries.extend(schedule_entries)
            except Exception as e:
                logger.debug(f"Error processing schedule in node {node_id}: {e}")
                continue
        
        return entries
    
    def _process_schedule(self, schedule: Dict[str, Any], work_item: Dict[str, Any], 
                         project_info: Dict[str, str], node_name: str) -> List[TimelineEntry]:
        """
        Process a schedule to generate timeline entries
        
        Args:
            schedule: Schedule data
            work_item: Work item data
            project_info: Project information
            node_name: Node name
            
        Returns:
            List of timeline entries for this schedule
        """
        owners = schedule.get('owners', [])
        points = schedule.get('points', 0)
        start_date = schedule.get('estimate_start_date')
        end_date = schedule.get('estimate_end_date')
        
        if not owners or points <= 0:
            logger.debug(f"Schedule has no owners or points: {schedule}")
            return []
        
        # Convert timestamps to dates
        start_dt, end_dt = self._parse_schedule_dates(start_date, end_date)
        if not start_dt or not end_dt:
            logger.debug(f"Invalid schedule dates: start={start_date}, end={end_date}")
            return []
        
        # Calculate workload distribution
        total_days = (end_dt - start_dt).days + 1
        daily_hours_per_person = points / len(owners) / total_days if total_days > 0 else 0
        
        if daily_hours_per_person <= 0:
            logger.debug(f"No workload to distribute: points={points}, owners={len(owners)}, days={total_days}")
            return []
        
        # Generate timeline entries for each owner and each day
        entries = []
        current_date = start_dt
        
        while current_date <= end_dt:
            for owner_key in owners:
                try:
                    # Get user email from owner key
                    user_email = self._get_user_email_from_key(owner_key)
                    
                    # Create timeline entry
                    entry = TimelineEntry(
                        date=current_date.strftime('%Y-%m-%d'),
                        project_code=project_info.get('project_code', 'Unknown'),
                        project_type=project_info.get('project_type', 'Product'),
                        project_status=project_info.get('project_status', 'Open'),
                        project_name=project_info.get('project_name', 'Unknown Project'),
                        activity_code=schedule.get('type', 'Development'),
                        market_region='',
                        category_function='Product',
                        entity='',
                        member_email=user_email,
                        work_load_hours=daily_hours_per_person,
                        submission_date=datetime.now().strftime('%Y-%m-%d'),
                        description=f"{node_name} - {schedule.get('task_name', 'Node work')}",
                        manager_signoff='',
                        remark=f"Work item: {work_item.get('id')}, Node: {schedule.get('node_id')}"
                    )
                    
                    entries.append(entry)
                    
                except Exception as e:
                    logger.debug(f"Error creating timeline entry for owner {owner_key}: {e}")
                    continue
            
            current_date += timedelta(days=1)
        
        logger.debug(f"Generated {len(entries)} timeline entries for schedule")
        return entries
    
    def _extract_project_info_from_work_item(self, work_item: Dict[str, Any]) -> Dict[str, str]:
        """
        Extract project information from work item with optimized caching
        
        Args:
            work_item: Work item data
            
        Returns:
            Dictionary with project information
        """
        # Look for related project field (field_c0a56e as mentioned by user)
        project_id = self._extract_field_value(work_item, ['field_c0a56e', 'related_project', 'project_id'])
        
        if project_id and project_id != 'N/A':
            # Check if we've already failed to get this project (avoid retries)
            if project_id in self._failed_project_ids:
                logger.debug(f"Skipping failed project ID {project_id}")
                return self._get_fallback_project_info()
            
            # Get project details with caching
            project_info = self.get_project_info_by_id(project_id)
            if project_info:
                return project_info
            else:
                # Mark as failed to avoid future retries
                self._failed_project_ids.add(project_id)
                logger.debug(f"Added project ID {project_id} to failed list")
        
        # Fallback to default project info
        return self._get_fallback_project_info()
    
    def _get_fallback_project_info(self) -> Dict[str, str]:
        """Get fallback project information when project lookup fails"""
        return {
            'project_code': 'Unknown',
            'project_type': 'Product',
            'project_status': 'Open',
            'project_name': 'Unknown Project'
        }
    
    def get_project_info_by_id(self, project_id: str) -> Optional[Dict[str, str]]:
        """
        Get project information by project ID with improved caching and error handling
        
        Args:
            project_id: Project ID
            
        Returns:
            Dictionary with project information or None if not found
        """
        try:
            # Try to get project from cache first
            if project_id in self._work_item_cache:
                project = self._work_item_cache[project_id]
                logger.debug(f"Retrieved project {project_id} from cache")
            else:
                # Get project details from API using correct project type ID
                logger.debug(f"Fetching project {project_id} from API")
                project = self.sdk.work_items.get_work_item_by_id(project_id, "642ebe04168eea39eeb0d34a")
                if project:
                    self._work_item_cache[project_id] = project
                    logger.debug(f"Cached project {project_id}")
                else:
                    logger.debug(f"Project {project_id} not found")
                    return None
            
            if project:
                return {
                    'project_code': self._extract_field_value(project, ['name'], project_id),
                    'project_type': self._extract_field_value(project, ['template'], 'Product'),
                    'project_status': self._extract_field_value(project, ['work_item_status'], 'Open'),
                    'project_name': self._extract_field_value(project, ['field_28829a'], 'Unknown Project')
                }
            
        except Exception as e:
            logger.debug(f"Error getting project info for ID {project_id}: {e}")
        
        return None
    
    def _get_user_email_from_key(self, user_key: str) -> str:
        """
        Get user email from user key
        
        Args:
            user_key: User key
            
        Returns:
            User email address
        """
        users = self.get_users_cache()
        
        # Look for user by key
        for user_id, user in users.items():
            if user_id == user_key or user.get('key') == user_key:
                return user.get('email', user.get('emailAddress', f"{user_key}@company.com"))
        
        # Fallback
        return f"{user_key}@company.com"
    
    def _parse_schedule_dates(self, start_date: Any, end_date: Any) -> Tuple[Optional[datetime], Optional[datetime]]:
        """
        Parse schedule dates from various formats
        
        Args:
            start_date: Start date (timestamp or string)
            end_date: End date (timestamp or string)
            
        Returns:
            Tuple of (start_datetime, end_datetime) or (None, None) if parsing fails
        """
        try:
            start_dt = self._parse_timestamp(start_date)
            end_dt = self._parse_timestamp(end_date)
            
            if start_dt and end_dt and start_dt <= end_dt:
                return start_dt, end_dt
            
        except Exception as e:
            logger.error(f"Error parsing schedule dates: {e}")
        
        return None, None
    
    def _parse_timestamp(self, timestamp: Any) -> Optional[datetime]:
        """
        Parse timestamp to datetime
        
        Args:
            timestamp: Timestamp value
            
        Returns:
            Datetime object or None if parsing fails
        """
        if not timestamp:
            return None
        
        try:
            if isinstance(timestamp, (int, float)):
                # Handle milliseconds
                if timestamp > 1e10:
                    timestamp = timestamp / 1000
                return datetime.fromtimestamp(timestamp)
            elif isinstance(timestamp, str):
                # Try various string formats
                for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S']:
                    try:
                        return datetime.strptime(timestamp, fmt)
                    except:
                        continue
        except Exception as e:
            logger.error(f"Error parsing timestamp {timestamp}: {e}")
        
        return None
    
    def _calculate_date_range(self, entries: List[TimelineEntry]) -> str:
        """
        Calculate date range from timeline entries
        
        Args:
            entries: List of timeline entries
            
        Returns:
            Date range string
        """
        if not entries:
            return ""
        
        dates = [entry.date for entry in entries if entry.date]
        if not dates:
            return ""
        
        min_date = min(dates)
        max_date = max(dates)
        
        if min_date == max_date:
            return min_date
        else:
            return f"{min_date} to {max_date}"
    
    def get_extraction_stats(self) -> Dict[str, Any]:
        """
        Get extraction statistics for monitoring performance
        
        Returns:
            Dictionary with extraction statistics
        """
        return {
            'workflow_cache_size': len(self._workflow_cache),
            'work_item_cache_size': len(self._work_item_cache),
            'failed_project_ids_count': len(self._failed_project_ids),
            'failed_project_ids': list(self._failed_project_ids)
        } 