"""
Timeline business models for Meegle Manager
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Optional


@dataclass
class TimelineEntry:
    """
    Timeline data entry representing work log information
    
    This model represents a single timeline entry in the Meegle system,
    containing all necessary information for reporting and analysis.
    """
    project_code: str           # 项目代码
    project_type: str           # 项目类型 (Project/Product)
    project_status: str         # 项目状态
    project_name: str           # 项目描述
    activity_code: str          # 活动代码 (Development/Maintenance)
    market_region: str          # 市场
    category_function: str      # 产品线
    entity: str                 # 事业部
    member_email: str           # 员工邮箱
    date: str                   # 日期 (YYYY-MM-DD)
    work_load_hours: float      # 耗时 (小时)
    description: str            # 工作内容具体描述
    submission_date: str        # 提交日期
    manager_signoff: str        # 审批记录
    remark: str                 # 备注
    
    def __post_init__(self):
        """Validate and normalize data after initialization"""
        # Ensure numeric values are proper types
        if isinstance(self.work_load_hours, str):
            try:
                self.work_load_hours = float(self.work_load_hours)
            except ValueError:
                self.work_load_hours = 0.0
        
        # Normalize empty values
        if not self.project_code or self.project_code == '(空)':
            self.project_code = ''
        
        # Ensure required fields are not None
        for field in ['project_type', 'project_status', 'project_name', 
                     'activity_code', 'market_region', 'category_function', 
                     'entity', 'member_email', 'description', 
                     'submission_date', 'manager_signoff', 'remark']:
            if getattr(self, field) is None:
                setattr(self, field, '')
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TimelineEntry':
        """
        Create TimelineEntry from dictionary
        
        Args:
            data: Dictionary containing timeline entry data
            
        Returns:
            TimelineEntry instance
        """
        return cls(
            project_code=data.get('project_code', ''),
            project_type=data.get('project_type', 'Project'),
            project_status=data.get('project_status', 'Open'),
            project_name=data.get('project_name', ''),
            activity_code=data.get('activity_code', 'Development'),
            market_region=data.get('market_region', ''),
            category_function=data.get('category_function', ''),
            entity=data.get('entity', ''),
            member_email=data.get('member_email', ''),
            date=data.get('date', ''),
            work_load_hours=data.get('work_load_hours', 0.0),
            description=data.get('description', ''),
            submission_date=data.get('submission_date', ''),
            manager_signoff=data.get('manager_signoff', ''),
            remark=data.get('remark', '')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert TimelineEntry to dictionary
        
        Returns:
            Dictionary representation of the timeline entry
        """
        return {
            'project_code': self.project_code,
            'project_type': self.project_type,
            'project_status': self.project_status,
            'project_name': self.project_name,
            'activity_code': self.activity_code,
            'market_region': self.market_region,
            'category_function': self.category_function,
            'entity': self.entity,
            'member_email': self.member_email,
            'date': self.date,
            'work_load_hours': self.work_load_hours,
            'description': self.description,
            'submission_date': self.submission_date,
            'manager_signoff': self.manager_signoff,
            'remark': self.remark
        }
    
    def is_valid(self) -> bool:
        """
        Check if the timeline entry is valid
        
        Returns:
            True if entry has required fields, False otherwise
        """
        # Check required fields
        if not self.date or not self.member_email:
            return False
        
        # Check if work hours is positive
        if self.work_load_hours <= 0:
            return False
        
        return True
    
    def get_csv_row(self) -> List[str]:
        """
        Get timeline entry as CSV row
        
        Returns:
            List of strings representing CSV row
        """
        return [
            '',  # Empty first column
            self.project_code,
            self.project_type,
            self.project_status,
            self.project_name,
            self.activity_code,
            self.market_region,
            self.category_function,
            self.entity,
            self.member_email,
            self.date,
            str(self.work_load_hours),
            self.description,
            self.submission_date,
            self.manager_signoff,
            self.remark,
            '', '', ''  # Empty trailing columns
        ]


@dataclass
class TimelineData:
    """
    Collection of timeline entries with metadata
    """
    entries: List[TimelineEntry]
    date_range: Optional[str] = None
    total_hours: Optional[float] = None
    unique_users: Optional[int] = None
    generated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Calculate metadata after initialization"""
        if self.generated_at is None:
            self.generated_at = datetime.now()
        
        # Calculate total hours
        self.total_hours = sum(entry.work_load_hours for entry in self.entries)
        
        # Calculate unique users
        unique_emails = set(entry.member_email for entry in self.entries if entry.member_email)
        self.unique_users = len(unique_emails)
    
    def filter_by_date(self, start_date: str, end_date: str) -> 'TimelineData':
        """
        Filter entries by date range
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            New TimelineData with filtered entries
        """
        filtered_entries = [
            entry for entry in self.entries
            if start_date <= entry.date <= end_date
        ]
        
        return TimelineData(
            entries=filtered_entries,
            date_range=f"{start_date} to {end_date}"
        )
    
    def filter_by_user(self, user_email: str) -> 'TimelineData':
        """
        Filter entries by user email
        
        Args:
            user_email: User email to filter by
            
        Returns:
            New TimelineData with filtered entries
        """
        filtered_entries = [
            entry for entry in self.entries
            if entry.member_email == user_email
        ]
        
        return TimelineData(
            entries=filtered_entries,
            date_range=f"user: {user_email}"
        )
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics
        
        Returns:
            Dictionary with summary information
        """
        if not self.entries:
            return {
                'total_entries': 0,
                'total_hours': 0.0,
                'unique_users': 0,
                'date_range': self.date_range,
                'generated_at': self.generated_at
            }
        
        dates = [entry.date for entry in self.entries if entry.date]
        
        return {
            'total_entries': len(self.entries),
            'total_hours': self.total_hours,
            'unique_users': self.unique_users,
            'date_range': self.date_range or f"{min(dates)} to {max(dates)}" if dates else None,
            'generated_at': self.generated_at,
            'valid_entries': sum(1 for entry in self.entries if entry.is_valid())
        } 