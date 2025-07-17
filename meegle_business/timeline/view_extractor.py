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
                                  max_items: Optional[int] = None,
                                  start_date: Optional[str] = None,
                                  end_date: Optional[str] = None) -> TimelineData:
        """
        Extract timeline data from a specific view with optional date filtering
        
        Args:
            view_id: View ID to extract timeline from
            work_item_type_key: Type of work items to process (default: "story")
            max_items: Maximum number of work items to process (for testing/debugging)
            start_date: Start date filter in YYYY-MM-DD format (inclusive)
            end_date: End date filter in YYYY-MM-DD format (inclusive)
            
        Returns:
            TimelineData object containing timeline entries within the specified date range
        """
        logger.info(f"Extracting timeline from view: {view_id}")
        if start_date or end_date:
            logger.info(f"Date filter: {start_date or 'no start'} to {end_date or 'no end'}")
        
        # Parse and validate date filters
        start_dt, end_dt = self._parse_date_filters(start_date, end_date)
        
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
            
            # Step 3: Apply date filtering if specified
            if start_dt or end_dt:
                filtered_entries = self._filter_entries_by_date(all_entries, start_dt, end_dt)
                logger.info(f"Date filtering: {len(all_entries)} entries -> {len(filtered_entries)} entries")
                all_entries = filtered_entries
            
            # Step 4: Calculate statistics
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
    
    def extract_timeline_this_week(self, view_id: str, work_item_type_key: str = "story", 
                                  max_items: Optional[int] = None) -> TimelineData:
        """
        Extract timeline data for this week (Monday to Sunday)
        
        Args:
            view_id: View ID to extract timeline from
            work_item_type_key: Type of work items to process (default: "story")
            max_items: Maximum number of work items to process (for testing/debugging)
            
        Returns:
            TimelineData object containing timeline entries for this week
        """
        start_date, end_date = self._get_this_week_range()
        logger.info(f"Extracting timeline for this week: {start_date} to {end_date}")
        return self.extract_timeline_from_view(view_id, work_item_type_key, max_items, start_date, end_date)
    
    def extract_timeline_last_week(self, view_id: str, work_item_type_key: str = "story", 
                                  max_items: Optional[int] = None) -> TimelineData:
        """
        Extract timeline data for last week (Monday to Sunday)
        
        Args:
            view_id: View ID to extract timeline from
            work_item_type_key: Type of work items to process (default: "story")
            max_items: Maximum number of work items to process (for testing/debugging)
            
        Returns:
            TimelineData object containing timeline entries for last week
        """
        start_date, end_date = self._get_last_week_range()
        logger.info(f"Extracting timeline for last week: {start_date} to {end_date}")
        return self.extract_timeline_from_view(view_id, work_item_type_key, max_items, start_date, end_date)
    
    def extract_timeline_this_month(self, view_id: str, work_item_type_key: str = "story", 
                                   max_items: Optional[int] = None) -> TimelineData:
        """
        Extract timeline data for this month (1st to last day)
        
        Args:
            view_id: View ID to extract timeline from
            work_item_type_key: Type of work items to process (default: "story")
            max_items: Maximum number of work items to process (for testing/debugging)
            
        Returns:
            TimelineData object containing timeline entries for this month
        """
        start_date, end_date = self._get_this_month_range()
        logger.info(f"Extracting timeline for this month: {start_date} to {end_date}")
        return self.extract_timeline_from_view(view_id, work_item_type_key, max_items, start_date, end_date)
    
    def extract_timeline_last_month(self, view_id: str, work_item_type_key: str = "story", 
                                   max_items: Optional[int] = None) -> TimelineData:
        """
        Extract timeline data for last month (1st to last day)
        
        Args:
            view_id: View ID to extract timeline from
            work_item_type_key: Type of work items to process (default: "story")
            max_items: Maximum number of work items to process (for testing/debugging)
            
        Returns:
            TimelineData object containing timeline entries for last month
        """
        start_date, end_date = self._get_last_month_range()
        logger.info(f"Extracting timeline for last month: {start_date} to {end_date}")
        return self.extract_timeline_from_view(view_id, work_item_type_key, max_items, start_date, end_date)
    
    def extract_timeline_this_quarter(self, view_id: str, work_item_type_key: str = "story", 
                                     max_items: Optional[int] = None) -> TimelineData:
        """
        Extract timeline data for this quarter
        
        Args:
            view_id: View ID to extract timeline from
            work_item_type_key: Type of work items to process (default: "story")
            max_items: Maximum number of work items to process (for testing/debugging)
            
        Returns:
            TimelineData object containing timeline entries for this quarter
        """
        start_date, end_date = self._get_this_quarter_range()
        logger.info(f"Extracting timeline for this quarter: {start_date} to {end_date}")
        return self.extract_timeline_from_view(view_id, work_item_type_key, max_items, start_date, end_date)
    
    def extract_timeline_last_quarter(self, view_id: str, work_item_type_key: str = "story", 
                                     max_items: Optional[int] = None) -> TimelineData:
        """
        Extract timeline data for last quarter
        
        Args:
            view_id: View ID to extract timeline from
            work_item_type_key: Type of work items to process (default: "story")
            max_items: Maximum number of work items to process (for testing/debugging)
            
        Returns:
            TimelineData object containing timeline entries for last quarter
        """
        start_date, end_date = self._get_last_quarter_range()
        logger.info(f"Extracting timeline for last quarter: {start_date} to {end_date}")
        return self.extract_timeline_from_view(view_id, work_item_type_key, max_items, start_date, end_date)
    
    def extract_timeline_last_n_days(self, view_id: str, days: int, work_item_type_key: str = "story", 
                                    max_items: Optional[int] = None) -> TimelineData:
        """
        Extract timeline data for the last N days
        
        Args:
            view_id: View ID to extract timeline from
            days: Number of days to go back
            work_item_type_key: Type of work items to process (default: "story")
            max_items: Maximum number of work items to process (for testing/debugging)
            
        Returns:
            TimelineData object containing timeline entries for the last N days
        """
        start_date, end_date = self._get_last_n_days_range(days)
        logger.info(f"Extracting timeline for last {days} days: {start_date} to {end_date}")
        return self.extract_timeline_from_view(view_id, work_item_type_key, max_items, start_date, end_date)
    
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
            
            # Aggregate entries by date and user for this work item
            aggregated_entries = self._aggregate_work_item_entries(all_entries)
            logger.debug(f"Work item {work_item_id}: {len(all_entries)} entries aggregated to {len(aggregated_entries)} entries")
            
            return aggregated_entries
            
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
        actual_work_time = schedule.get('actual_work_time', 0)
        start_date = schedule.get('estimate_start_date')
        end_date = schedule.get('estimate_end_date')
        
        if not owners or actual_work_time <= 0:
            logger.debug(f"Schedule has no owners or work time: {schedule}")
            return []
        
        # Convert timestamps to dates
        start_dt, end_dt = self._parse_schedule_dates(start_date, end_date)
        if not start_dt or not end_dt:
            logger.debug(f"Invalid schedule dates: start={start_date}, end={end_date}")
            return []
        
        # Calculate workload distribution
        total_days = (end_dt - start_dt).days + 1
        daily_hours_per_person = actual_work_time / len(owners) / total_days if total_days > 0 else 0
        
        if daily_hours_per_person <= 0:
            logger.debug(f"No workload to distribute: actual_work_time={actual_work_time}, owners={len(owners)}, days={total_days}")
            return []
        
        # Generate timeline entries for each owner and each day
        entries = []
        current_date = start_dt
        
        while current_date <= end_dt:
            for owner_key in owners:
                try:
                    # Get user email and name from owner key
                    user_email, user_name = self._get_user_info_from_key(owner_key)
                    
                    # Parse project code components
                    project_code = project_info.get('project_code', 'Unknown')
                    market_region, category_function, entity = self._parse_project_code(project_code)
                    
                    # Get activity code from story template
                    activity_code = self._get_activity_code_from_template(work_item)
                    
                    # Get work item creation date for submission_date
                    created_at = work_item.get('created_at')
                    submission_date = self._format_timestamp_to_date(created_at) if created_at else datetime.now().strftime('%Y-%m-%d')
                    
                    # Create timeline entry
                    entry = TimelineEntry(
                        date=current_date.strftime('%Y-%m-%d'),
                        project_code=project_code,
                        project_type=project_info.get('project_type', 'Product'),
                        project_status=project_info.get('project_status', 'Open'),
                        project_name=project_info.get('project_name', ''),  # Keep empty if not available
                        activity_code=activity_code,
                        market_region=market_region,
                        category_function=category_function,
                        entity=entity,
                        member_email=user_email,
                        member_name=user_name,
                        work_load_hours=daily_hours_per_person,
                        submission_date=submission_date,
                        description=work_item.get('name', ''),  # Use story name
                        manager_signoff='',
                        remark=f"@https://project.larksuite.com/advance_ai/story/detail/{work_item.get('id')}"
                    )
                    
                    entries.append(entry)
                    
                except Exception as e:
                    logger.debug(f"Error creating timeline entry for owner {owner_key}: {e}")
                    continue
            
            current_date += timedelta(days=1)
        
        logger.debug(f"Generated {len(entries)} timeline entries for schedule")
        return entries
    
    def _aggregate_work_item_entries(self, entries: List[TimelineEntry]) -> List[TimelineEntry]:
        """
        Aggregate timeline entries by date and user for a single work item
        
        Args:
            entries: List of timeline entries for a work item
            
        Returns:
            List of aggregated timeline entries
        """
        if not entries:
            return []
        
        # Group entries by (date, member_email)
        aggregation_map = {}
        
        for entry in entries:
            # Skip entries with zero work hours
            if entry.work_load_hours <= 0:
                continue
                
            # Create aggregation key
            key = (entry.date, entry.member_email)
            
            if key not in aggregation_map:
                # First entry for this date/user combination
                aggregation_map[key] = entry
            else:
                # Aggregate with existing entry
                existing_entry = aggregation_map[key]
                
                # Sum work hours
                existing_entry.work_load_hours += entry.work_load_hours
                
                # Combine descriptions (avoid duplicates)
                if entry.description and entry.description not in existing_entry.description:
                    if existing_entry.description:
                        existing_entry.description += f"; {entry.description}"
                    else:
                        existing_entry.description = entry.description
                
                # Combine remarks (avoid duplicates)
                if entry.remark and entry.remark not in existing_entry.remark:
                    if existing_entry.remark:
                        existing_entry.remark += f"; {entry.remark}"
                    else:
                        existing_entry.remark = entry.remark
        
        # Convert back to list and filter out zero work hours (just in case)
        aggregated_entries = [entry for entry in aggregation_map.values() if entry.work_load_hours > 0]
        
        logger.debug(f"Aggregated {len(entries)} entries to {len(aggregated_entries)} entries")
        return aggregated_entries
    
    def _parse_project_code(self, project_code: str) -> tuple[str, str, str]:
        """
        Parse project code to extract market/region, category/function, and entity
        
        Format: [Type]-[Market/Region]-[Entity]-[Category/Function]-[Unique Identifier][-Version Number]
        
        Args:
            project_code: Project code string
            
        Returns:
            Tuple of (market_region, category_function, entity)
        """
        if not project_code or project_code == 'Unknown':
            return '', '', ''
        
        try:
            # Split by dash
            parts = project_code.split('-')
            
            # Need at least 4 parts: [Type]-[Market/Region]-[Entity]-[Category/Function]
            if len(parts) >= 4:
                market_region = parts[1]
                entity = parts[2]
                category_function = parts[3]
                return market_region, category_function, entity
            else:
                # Format doesn't match standard, return empty strings
                return '', '', ''
                
        except Exception as e:
            logger.debug(f"Error parsing project code {project_code}: {e}")
            return '', '', ''
    
    def _get_activity_code_from_template(self, work_item: Dict[str, Any]) -> str:
        """
        Get activity code based on story template
        
        Args:
            work_item: Work item data containing template information
            
        Returns:
            Activity code string (based on template_id or intelligent inference)
        """
        # Try to get template ID from fields first (most reliable)
        fields = work_item.get('fields', [])
        for field in fields:
            if isinstance(field, dict) and field.get('field_key') == 'template':
                field_value = field.get('field_value', {})
                if isinstance(field_value, dict):
                    template_id = field_value.get('id')
                    if template_id:
                        # Enhanced template mapping with intelligent inference
                        activity_code = self._map_template_id_to_activity_code(template_id, work_item)
                        return activity_code
        
        # Fallback: try top-level template_id
        template_id = work_item.get('template_id')
        if template_id:
            activity_code = self._map_template_id_to_activity_code(template_id, work_item)
            return activity_code
        
        # Final fallback: intelligent inference based on work item content
        return self._infer_activity_code_from_content(work_item)
    
    def _map_template_id_to_activity_code(self, template_id: int, work_item: Dict[str, Any]) -> str:
        """
        Map template ID to activity code with intelligent inference
        
        Args:
            template_id: Template ID
            work_item: Work item data for context
            
        Returns:
            Activity code string
        """
        # Known template mappings based on documentation
        template_mapping = {
            95066: 'Feature',      # Feature development template
            96984: 'Bug',          # Bug fixing template
            116177: 'Operation',   # Operation template
            118092: 'Enhancement', # Enhancement template
            123041: 'Research',    # Research template
        }
        
        # If we have a direct mapping, use it
        if template_id in template_mapping:
            return template_mapping[template_id]
        
        # If not, try to infer from work item content
        inferred_code = self._infer_activity_code_from_content(work_item)
        if inferred_code != 'Development':  # If we got a specific inference
            return inferred_code
        
        # Fallback to template ID
        return f'Template_{template_id}'
    
    def _infer_activity_code_from_content(self, work_item: Dict[str, Any]) -> str:
        """
        Infer activity code from work item content
        
        Args:
            work_item: Work item data
            
        Returns:
            Inferred activity code
        """
        work_item_name = work_item.get('name', '').lower()
        description = work_item.get('description', '').lower()
        
        # Keywords for different activity types
        bug_keywords = ['bug', 'issue', 'fix', 'defect', 'error', '问题', '缺陷', '修复', '错误']
        research_keywords = ['research', 'investigation', 'analysis', 'study', 'explore', 
                           '研究', '调研', '分析', '探索', '调查']
        enhancement_keywords = ['enhancement', 'improvement', 'optimize', 'upgrade', 'refactor',
                              '优化', '改进', '增强', '升级', '重构']
        operation_keywords = ['deploy', 'ops', 'operation', 'maintenance', 'config', 'setup',
                            '部署', '运维', '运营', '维护', '配置']
        
        # Check work item name and description for keywords
        content = f"{work_item_name} {description}"
        
        if any(keyword in content for keyword in bug_keywords):
            return 'Bug'
        elif any(keyword in content for keyword in research_keywords):
            return 'Research'
        elif any(keyword in content for keyword in enhancement_keywords):
            return 'Enhancement'
        elif any(keyword in content for keyword in operation_keywords):
            return 'Operation'
        
        # Default to Feature for development work
        return 'Feature'
    
    def _extract_project_info_from_work_item(self, work_item: Dict[str, Any]) -> Dict[str, str]:
        """
        Extract project information from work item with optimized caching
        
        Args:
            work_item: Work item data
            
        Returns:
            Dictionary with project information
        """
        # Look for related project field (field_c0a56e as confirmed by debugging)
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
                # Use story info as fallback
                return self._get_fallback_project_info()
        
        # Fallback to default project info
        return self._get_fallback_project_info()
    
    def _get_fallback_project_info(self) -> Dict[str, str]:
        """Get fallback project information when project lookup fails"""
        return {
            'project_code': '',
            'project_type': '',
            'project_status': '',
            'project_name': ''
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
                project = self.sdk.work_items.get_work_item_by_id(project_id, "642ec373f4af608bb3cb1c90")
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
                    'project_name': self._extract_field_value(project, ['field_28829a'], '')  # Keep empty if not available
                }
            
        except Exception as e:
            logger.debug(f"Error getting project info for ID {project_id}: {e}")
        
        return None
    
    def _get_user_info_from_key(self, user_key: str) -> tuple[str, str]:
        """
        Get user email and name from user key with fallback to server lookup
        
        Args:
            user_key: User key
            
        Returns:
            Tuple of (email, name)
        """
        users = self.get_users_cache()
        
        # Look for user by key in cache first
        for user_id, user in users.items():
            if user_id == user_key or user.get('key') == user_key:
                email = user.get('email', user.get('emailAddress', f"{user_key}@company.com"))
                name = user.get('name_cn', user.get('name', user_key))
                return email, name
        
        # If not found in cache, try to fetch from server
        logger.debug(f"User {user_key} not found in cache, attempting server lookup")
        try:
            # Try to get user details from server
            user_details = self.sdk.users.get_user_details([user_key])
            if user_details:
                # Update cache with new user data
                for user in user_details:
                    user_key_from_api = user.get('user_key')
                    if user_key_from_api:
                        users[user_key_from_api] = user
                        logger.debug(f"Added user {user_key_from_api} to cache from server")
                        
                        # If this is the user we're looking for, return their email and name
                        if user_key_from_api == user_key:
                            email = user.get('email', user.get('emailAddress', f"{user_key}@company.com"))
                            name = user.get('name_cn', user.get('name', user_key))
                            return email, name
            
        except Exception as e:
            logger.debug(f"Failed to fetch user {user_key} from server: {e}")
        
        # Final fallback if server lookup also fails
        logger.debug(f"Using fallback email and name for user {user_key}")
        return f"{user_key}@company.com", user_key
    
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
    
    def _format_timestamp_to_date(self, timestamp: Any) -> str:
        """
        Format timestamp to date string (YYYY-MM-DD)
        
        Args:
            timestamp: Timestamp value (int, float, or string)
            
        Returns:
            Date string in YYYY-MM-DD format
        """
        try:
            if isinstance(timestamp, (int, float)):
                # Handle milliseconds
                if timestamp > 1e10:
                    timestamp = timestamp / 1000
                dt = datetime.fromtimestamp(timestamp)
                return dt.strftime('%Y-%m-%d')
            elif isinstance(timestamp, str):
                # Try to parse string timestamp
                try:
                    # Try as timestamp first
                    ts = float(timestamp)
                    if ts > 1e10:
                        ts = ts / 1000
                    dt = datetime.fromtimestamp(ts)
                    return dt.strftime('%Y-%m-%d')
                except ValueError:
                    # Try various string formats
                    for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S']:
                        try:
                            dt = datetime.strptime(timestamp, fmt)
                            return dt.strftime('%Y-%m-%d')
                        except ValueError:
                            continue
        except Exception as e:
            logger.debug(f"Error formatting timestamp {timestamp}: {e}")
        
        # Fallback to current date
        return datetime.now().strftime('%Y-%m-%d')
    
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
    
    def _parse_date_filters(self, start_date: Optional[str], end_date: Optional[str]) -> Tuple[Optional[datetime], Optional[datetime]]:
        """
        Parse and validate date filter strings
        
        Args:
            start_date: Start date string in YYYY-MM-DD format
            end_date: End date string in YYYY-MM-DD format
            
        Returns:
            Tuple of (start_datetime, end_datetime) or (None, None) if parsing fails
        """
        start_dt = None
        end_dt = None
        
        try:
            if start_date:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                
            if end_date:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                
            # Validate date range
            if start_dt and end_dt and start_dt > end_dt:
                logger.warning(f"Start date {start_date} is after end date {end_date}, swapping them")
                start_dt, end_dt = end_dt, start_dt
                
        except ValueError as e:
            logger.error(f"Invalid date format: {e}. Use YYYY-MM-DD format.")
            return None, None
            
        return start_dt, end_dt
    
    def _filter_entries_by_date(self, entries: List[TimelineEntry], 
                               start_dt: Optional[datetime], end_dt: Optional[datetime]) -> List[TimelineEntry]:
        """
        Filter timeline entries by date range
        
        Args:
            entries: List of timeline entries
            start_dt: Start date (inclusive)
            end_dt: End date (inclusive)
            
        Returns:
            Filtered list of timeline entries
        """
        if not start_dt and not end_dt:
            return entries
        
        filtered_entries = []
        
        for entry in entries:
            try:
                entry_date = datetime.strptime(entry.date, '%Y-%m-%d')
                
                # Check if entry date is within range
                if start_dt and entry_date < start_dt:
                    continue
                if end_dt and entry_date > end_dt:
                    continue
                    
                filtered_entries.append(entry)
                
            except ValueError:
                logger.warning(f"Invalid date format in entry: {entry.date}")
                continue
        
        return filtered_entries
    
    def _get_this_week_range(self) -> Tuple[str, str]:
        """Get start and end dates for this week (Monday to Sunday)"""
        today = datetime.now()
        monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=6)
        return monday.strftime('%Y-%m-%d'), sunday.strftime('%Y-%m-%d')
    
    def _get_last_week_range(self) -> Tuple[str, str]:
        """Get start and end dates for last week (Monday to Sunday)"""
        today = datetime.now()
        last_monday = today - timedelta(days=today.weekday() + 7)
        last_sunday = last_monday + timedelta(days=6)
        return last_monday.strftime('%Y-%m-%d'), last_sunday.strftime('%Y-%m-%d')
    
    def _get_this_month_range(self) -> Tuple[str, str]:
        """Get start and end dates for this month"""
        today = datetime.now()
        first_day = today.replace(day=1)
        
        # Get last day of month
        if today.month == 12:
            next_month = today.replace(year=today.year + 1, month=1, day=1)
        else:
            next_month = today.replace(month=today.month + 1, day=1)
        last_day = next_month - timedelta(days=1)
        
        return first_day.strftime('%Y-%m-%d'), last_day.strftime('%Y-%m-%d')
    
    def _get_last_month_range(self) -> Tuple[str, str]:
        """Get start and end dates for last month"""
        today = datetime.now()
        
        # Get first day of last month
        if today.month == 1:
            first_day = today.replace(year=today.year - 1, month=12, day=1)
        else:
            first_day = today.replace(month=today.month - 1, day=1)
        
        # Get last day of last month
        last_day = today.replace(day=1) - timedelta(days=1)
        
        return first_day.strftime('%Y-%m-%d'), last_day.strftime('%Y-%m-%d')
    
    def _get_this_quarter_range(self) -> Tuple[str, str]:
        """Get start and end dates for this quarter"""
        today = datetime.now()
        quarter = (today.month - 1) // 3 + 1
        
        # First month of quarter
        first_month = (quarter - 1) * 3 + 1
        first_day = today.replace(month=first_month, day=1)
        
        # Last month of quarter
        last_month = quarter * 3
        if last_month == 12:
            next_quarter_start = today.replace(year=today.year + 1, month=1, day=1)
        else:
            next_quarter_start = today.replace(month=last_month + 1, day=1)
        last_day = next_quarter_start - timedelta(days=1)
        
        return first_day.strftime('%Y-%m-%d'), last_day.strftime('%Y-%m-%d')
    
    def _get_last_quarter_range(self) -> Tuple[str, str]:
        """Get start and end dates for last quarter"""
        today = datetime.now()
        current_quarter = (today.month - 1) // 3 + 1
        
        if current_quarter == 1:
            # Last quarter was Q4 of previous year
            last_quarter = 4
            year = today.year - 1
        else:
            last_quarter = current_quarter - 1
            year = today.year
        
        # First month of last quarter
        first_month = (last_quarter - 1) * 3 + 1
        first_day = datetime(year, first_month, 1)
        
        # Last month of last quarter
        last_month = last_quarter * 3
        if last_month == 12:
            next_quarter_start = datetime(year + 1, 1, 1)
        else:
            next_quarter_start = datetime(year, last_month + 1, 1)
        last_day = next_quarter_start - timedelta(days=1)
        
        return first_day.strftime('%Y-%m-%d'), last_day.strftime('%Y-%m-%d')
    
    def _get_last_n_days_range(self, days: int) -> Tuple[str, str]:
        """Get start and end dates for the last N days"""
        today = datetime.now()
        start_date = today - timedelta(days=days - 1)  # -1 because we include today
        return start_date.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d') 