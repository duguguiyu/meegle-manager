"""
Base models and exceptions for Meegle SDK
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime


class APIError(Exception):
    """Base API error exception"""
    
    def __init__(self, message: str, status_code: Optional[int] = None, 
                 response_data: Optional[Dict] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_data = response_data or {}


class AuthenticationError(APIError):
    """Authentication related errors"""
    pass


class RateLimitError(APIError):
    """Rate limit exceeded errors"""
    pass


class ValidationError(APIError):
    """Request validation errors"""
    pass


@dataclass
class TokenInfo:
    """Token information"""
    token: str
    expires_at: float
    
    @property
    def is_expired(self) -> bool:
        """Check if token is expired (with 5 minute buffer)"""
        import time
        return time.time() >= (self.expires_at - 300)


@dataclass
class User:
    """User information"""
    user_key: str
    name_cn: str
    name_en: Optional[str] = None
    email: Optional[str] = None
    avatar: Optional[str] = None
    department: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Create User from API response"""
        return cls(
            user_key=data.get('user_key', ''),
            name_cn=data.get('name_cn', ''),
            name_en=data.get('name_en'),
            email=data.get('email'),
            avatar=data.get('avatar'),
            department=data.get('department')
        )


@dataclass
class Team:
    """Team information"""
    team_key: str
    name: str
    description: Optional[str] = None
    user_keys: Optional[List[str]] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Team':
        """Create Team from API response"""
        return cls(
            team_key=data.get('team_key', ''),
            name=data.get('name', ''),
            description=data.get('description'),
            user_keys=data.get('user_keys', [])
        )


@dataclass
class WorkItem:
    """Work item information"""
    item_key: str
    item_type: str
    title: str
    status: Optional[str] = None
    assignee: Optional[str] = None
    creator: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkItem':
        """Create WorkItem from API response"""
        return cls(
            item_key=data.get('item_key', ''),
            item_type=data.get('item_type', ''),
            title=data.get('title', ''),
            status=data.get('status'),
            assignee=data.get('assignee'),
            creator=data.get('creator'),
            created_at=cls._parse_timestamp(data.get('created_at')),
            updated_at=cls._parse_timestamp(data.get('updated_at'))
        )
    
    @staticmethod
    def _parse_timestamp(timestamp: Optional[str]) -> Optional[datetime]:
        """Parse timestamp string to datetime"""
        if not timestamp:
            return None
        try:
            return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None


@dataclass
class ChartData:
    """Chart data information"""
    chart_id: str
    name: str
    chart_type: str
    data: Dict[str, Any]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChartData':
        """Create ChartData from API response"""
        return cls(
            chart_id=data.get('chart_id', ''),
            name=data.get('name', ''),
            chart_type=data.get('chart_type', ''),
            data=data.get('data', {})
        ) 