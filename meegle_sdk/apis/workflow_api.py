"""
Workflow API for Meegle SDK
"""

import logging
from typing import Dict, Any, List, Optional

from ..client.base_client import BaseAPIClient

logger = logging.getLogger(__name__)


class WorkflowAPI:
    """
    API for workflow operations
    
    Provides methods to:
    - Get workflow details for work items
    - Query workflow nodes and connections
    - Extract workflow scheduling information
    - Update work items with field modifications
    - Create field value pairs for updates
    """
    
    def __init__(self, client: BaseAPIClient):
        """
        Initialize Workflow API
        
        Args:
            client: Base client instance
        """
        self.client = client
    
    def get_workflow_details(self, work_item_id: int, work_item_type_key: str, 
                           flow_type: int = 0, fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get workflow details for a specific work item
        
        Args:
            work_item_id: Work item ID
            work_item_type_key: Work item type key
            flow_type: Workflow type (0: node flow, 1: state flow)
            fields: Optional list of fields to return
            
        Returns:
            Dictionary containing workflow details
        """
        logger.info(f"Getting workflow details for work item {work_item_id}")
        
        endpoint = f"{self.client.project_key}/work_item/{work_item_type_key}/{work_item_id}/workflow/query"
        
        # Prepare request body
        request_body = {
            "flow_type": flow_type
        }
        
        if fields:
            request_body["fields"] = fields
        
        try:
            data = self.client.post(endpoint, json_data=request_body)
            logger.info(f"Successfully retrieved workflow details for work item {work_item_id}")
            return data
            
        except Exception as e:
            logger.error(f"Failed to get workflow details for work item {work_item_id}: {e}")
            raise
    
    def get_workflow_nodes(self, work_item_id: int, work_item_type_key: str) -> List[Dict[str, Any]]:
        """
        Get workflow nodes for a work item
        
        Args:
            work_item_id: Work item ID
            work_item_type_key: Work item type key
            
        Returns:
            List of workflow nodes
        """
        logger.info(f"Getting workflow nodes for work item {work_item_id}")
        
        try:
            workflow_data = self.get_workflow_details(work_item_id, work_item_type_key, flow_type=0)
            
            if not workflow_data:
                logger.warning(f"No workflow data found for work item {work_item_id}")
                return []
            
            # Handle different response formats
            if 'data' in workflow_data:
                nodes = workflow_data['data'].get('workflow_nodes', [])
            else:
                nodes = workflow_data.get('workflow_nodes', [])
            
            logger.info(f"Found {len(nodes)} workflow nodes for work item {work_item_id}")
            return nodes
            
        except Exception as e:
            logger.error(f"Failed to get workflow nodes for work item {work_item_id}: {e}")
            return []
    
    def get_workflow_connections(self, work_item_id: int, work_item_type_key: str) -> List[Dict[str, Any]]:
        """
        Get workflow connections for a work item
        
        Args:
            work_item_id: Work item ID
            work_item_type_key: Work item type key
            
        Returns:
            List of workflow connections
        """
        logger.info(f"Getting workflow connections for work item {work_item_id}")
        
        try:
            workflow_data = self.get_workflow_details(work_item_id, work_item_type_key, flow_type=0)
            
            if not workflow_data:
                logger.warning(f"No workflow data found for work item {work_item_id}")
                return []
            
            # Handle different response formats
            if 'data' in workflow_data:
                connections = workflow_data['data'].get('connections', [])
            else:
                connections = workflow_data.get('connections', [])
            
            logger.info(f"Found {len(connections)} workflow connections for work item {work_item_id}")
            return connections
            
        except Exception as e:
            logger.error(f"Failed to get workflow connections for work item {work_item_id}: {e}")
            return []
    
    def extract_node_schedules(self, node: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract scheduling information from a workflow node
        
        Logic:
        1. If node has sub_tasks AND node-level schedules:
           - Calculate workload per owner from sub_tasks
           - Calculate workload per owner from node-level schedules
           - For each owner, use sub_tasks if workload >= node workload, else use node distribution
        2. If node has only sub_tasks: use sub_tasks
        3. If node has no sub_tasks: use node-level schedules
        
        Args:
            node: Workflow node data
            
        Returns:
            List of schedule information
        """
        schedules = []
        
        # Check if node has sub tasks
        sub_tasks = node.get('sub_tasks', [])
        
        if sub_tasks:
            logger.debug(f"Node {node.get('id')} has {len(sub_tasks)} sub tasks")
            
            # Extract sub_tasks schedules and calculate per-owner workload
            sub_task_schedules = []
            sub_task_workload_by_owner = {}  # {owner_key: total_workload}
            
            for task in sub_tasks:
                task_schedules = task.get('schedules', [])
                for schedule in task_schedules:
                    schedule_info = {
                        'type': 'sub_task',
                        'task_id': task.get('id'),
                        'task_name': task.get('name'),
                        'node_id': node.get('id'),
                        'node_name': node.get('name'),
                        'owners': schedule.get('owners', []),
                        'estimate_start_date': schedule.get('estimate_start_date'),
                        'estimate_end_date': schedule.get('estimate_end_date'),
                        'points': schedule.get('points', 0),
                        'actual_work_time': schedule.get('actual_work_time', 0)
                    }
                    sub_task_schedules.append(schedule_info)
                    
                    # Accumulate workload per owner
                    owners = schedule.get('owners', [])
                    work_time = schedule.get('actual_work_time', 0)
                    if owners and work_time > 0:
                        per_owner_time = work_time / len(owners)
                        for owner in owners:
                            sub_task_workload_by_owner[owner] = sub_task_workload_by_owner.get(owner, 0) + per_owner_time
            
            # Check if node has node-level schedules
            node_schedules_raw = self._extract_node_level_schedules(node)
            
            if node_schedules_raw:
                logger.debug(f"Node {node.get('id')} has both sub_tasks and node-level schedules, comparing workloads")
                
                # Calculate per-owner workload from node-level schedules
                node_workload_by_owner = {}
                for schedule in node_schedules_raw:
                    owners = schedule.get('owners', [])
                    work_time = schedule.get('actual_work_time', 0)
                    if owners and work_time > 0:
                        per_owner_time = work_time / len(owners)
                        for owner in owners:
                            node_workload_by_owner[owner] = node_workload_by_owner.get(owner, 0) + per_owner_time
                
                # Determine which schedules to use per owner
                all_owners = set(sub_task_workload_by_owner.keys()) | set(node_workload_by_owner.keys())
                
                owners_use_subtasks = set()
                owners_use_node = set()
                
                for owner in all_owners:
                    subtask_workload = sub_task_workload_by_owner.get(owner, 0)
                    node_workload = node_workload_by_owner.get(owner, 0)
                    
                    if subtask_workload >= node_workload:
                        owners_use_subtasks.add(owner)
                        logger.debug(f"Owner {owner}: sub_tasks workload ({subtask_workload:.2f}) >= node workload ({node_workload:.2f}), using sub_tasks")
                    else:
                        owners_use_node.add(owner)
                        logger.debug(f"Owner {owner}: sub_tasks workload ({subtask_workload:.2f}) < node workload ({node_workload:.2f}), using node distribution")
                
                # Build final schedules based on decision
                # Add sub_task schedules for owners who use sub_tasks
                for schedule_info in sub_task_schedules:
                    # Filter owners to only include those who should use sub_tasks
                    filtered_owners = [owner for owner in schedule_info['owners'] if owner in owners_use_subtasks]
                    if filtered_owners:
                        schedule_copy = schedule_info.copy()
                        schedule_copy['owners'] = filtered_owners
                        schedules.append(schedule_copy)
                
                # Add node schedules for owners who use node distribution
                for schedule in node_schedules_raw:
                    # Filter owners to only include those who should use node distribution
                    filtered_owners = [owner for owner in schedule.get('owners', []) if owner in owners_use_node]
                    if filtered_owners:
                        schedule_info = {
                            'type': schedule.get('type', 'node'),
                            'task_id': None,
                            'task_name': None,
                            'node_id': node.get('id'),
                            'node_name': node.get('name'),
                            'owners': filtered_owners,
                            'estimate_start_date': schedule.get('estimate_start_date'),
                            'estimate_end_date': schedule.get('estimate_end_date'),
                            'points': schedule.get('points', 0),
                            'actual_work_time': schedule.get('actual_work_time', 0)
                        }
                        schedules.append(schedule_info)
            else:
                # No node-level schedules, just use sub_tasks
                schedules = sub_task_schedules
        else:
            # No sub_tasks, extract node-level schedules
            node_schedules_raw = self._extract_node_level_schedules(node)
            
            for schedule in node_schedules_raw:
                schedule_info = {
                    'type': schedule.get('type', 'node'),
                    'task_id': None,
                    'task_name': None,
                    'node_id': node.get('id'),
                    'node_name': node.get('name'),
                    'owners': schedule.get('owners', []),
                    'estimate_start_date': schedule.get('estimate_start_date'),
                    'estimate_end_date': schedule.get('estimate_end_date'),
                    'points': schedule.get('points', 0),
                    'actual_work_time': schedule.get('actual_work_time', 0)
                }
                schedules.append(schedule_info)
        
        logger.debug(f"Extracted {len(schedules)} schedules from node {node.get('id')}")
        return schedules
    
    def _extract_node_level_schedules(self, node: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract node-level schedules (either from schedules array or node_schedule)
        
        Args:
            node: Workflow node data
            
        Returns:
            List of raw schedule data from node level
        """
        schedules = []
        
        # Priority 1: Check schedules array (for dynamic calculation with per-user breakdown)
        individual_schedules = node.get('schedules', [])
        if individual_schedules:
            logger.debug(f"Node {node.get('id')} has {len(individual_schedules)} individual schedules")
            for schedule in individual_schedules:
                schedule_data = {
                    'type': 'node_individual',
                    'owners': schedule.get('owners', []),
                    'estimate_start_date': schedule.get('estimate_start_date'),
                    'estimate_end_date': schedule.get('estimate_end_date'),
                    'points': schedule.get('points', 0),
                    'actual_work_time': schedule.get('actual_work_time', 0)
                }
                schedules.append(schedule_data)
        else:
            # Priority 2: Fallback to node_schedule if no individual schedules
            node_schedule = node.get('node_schedule')
            if node_schedule:
                logger.debug(f"Node {node.get('id')} has node-level schedule")
                schedule_data = {
                    'type': 'node',
                    'owners': node_schedule.get('owners', []),
                    'estimate_start_date': node_schedule.get('estimate_start_date'),
                    'estimate_end_date': node_schedule.get('estimate_end_date'),
                    'points': node_schedule.get('points', 0),
                    'actual_work_time': node_schedule.get('actual_work_time', 0)
                }
                schedules.append(schedule_data)
        
        return schedules
    
    def update_work_item(self, work_item_id: int, work_item_type_key: str, 
                        update_fields: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Update a work item with specified fields
        
        Args:
            work_item_id: Work item ID
            work_item_type_key: Work item type key
            update_fields: List of field value pairs to update
                Each item should contain:
                - field_key or field_alias: Field identifier
                - field_value: New field value
                
        Returns:
            Dictionary containing update response
            
        Example:
            update_fields = [
                {
                    "field_key": "field_184c63",
                    "field_value": 1646409600000
                },
                {
                    "field_key": "role_owners",
                    "field_value": [
                        {
                            "role": "rd",
                            "owners": ["testuser"]
                        }
                    ]
                }
            ]
        """
        logger.info(f"Updating work item {work_item_id} of type {work_item_type_key}")
        
        endpoint = f"{self.client.project_key}/work_item/{work_item_type_key}/{work_item_id}"
        
        # Prepare request body
        request_body = {
            "update_fields": update_fields
        }
        
        try:
            data = self.client.put(endpoint, json_data=request_body)
            logger.info(f"Successfully updated work item {work_item_id}")
            return data
            
        except Exception as e:
            logger.error(f"Failed to update work item {work_item_id}: {e}")
            raise
    
    def create_field_value_pair(self, field_key: str = None, field_alias: str = None, 
                               field_value: Any = None) -> Dict[str, Any]:
        """
        Create a field value pair for work item updates
        
        Args:
            field_key: Field key (must provide either field_key or field_alias)
            field_alias: Field alias (must provide either field_key or field_alias)
            field_value: Field value (required)
            
        Returns:
            Dictionary containing field value pair
            
        Raises:
            ValueError: If neither field_key nor field_alias is provided, or if field_value is None
        """
        if not field_key and not field_alias:
            raise ValueError("Either field_key or field_alias must be provided")
        
        if field_value is None:
            raise ValueError("field_value must be provided")
        
        field_pair = {"field_value": field_value}
        
        if field_key:
            field_pair["field_key"] = field_key
        else:
            field_pair["field_alias"] = field_alias
            
        return field_pair
    
    def create_role_owners_field(self, role_owners: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a role_owners field value pair
        
        Args:
            role_owners: List of role owner mappings
                Each item should contain:
                - role: Role name
                - owners: List of user keys
                
        Returns:
            Dictionary containing role_owners field value pair
            
        Example:
            role_owners = [
                {
                    "role": "rd",
                    "owners": ["user1", "user2"]
                },
                {
                    "role": "pm",
                    "owners": ["user3"]
                }
            ]
        """
        return self.create_field_value_pair(
            field_key="role_owners",
            field_value=role_owners
        )
    
    def update_work_item_fields(self, work_item_id: int, work_item_type_key: str,
                               **field_updates) -> Dict[str, Any]:
        """
        Update work item fields using keyword arguments
        
        Args:
            work_item_id: Work item ID
            work_item_type_key: Work item type key
            **field_updates: Field updates as keyword arguments
                Key should be field_key or field_alias
                Value should be the field value
                
        Returns:
            Dictionary containing update response
            
        Example:
            api.update_work_item_fields(
                work_item_id=123,
                work_item_type_key="task",
                field_184c63=1646409600000,
                title="New Title",
                description="New Description"
            )
        """
        update_fields = []
        
        for field_key, field_value in field_updates.items():
            field_pair = self.create_field_value_pair(
                field_key=field_key,
                field_value=field_value
            )
            update_fields.append(field_pair)
        
        return self.update_work_item(work_item_id, work_item_type_key, update_fields)