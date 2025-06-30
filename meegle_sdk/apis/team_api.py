"""
Team API for Meegle SDK
"""

import logging
from typing import Dict, Any, List, Optional, Set

from ..client.base_client import BaseAPIClient
from ..models.base_models import Team, APIError

logger = logging.getLogger(__name__)


class TeamAPI:
    """
    Team API client for managing Meegle teams
    
    Provides methods to:
    - Get all teams
    - Get team details
    - Get team members
    - Extract user keys from teams
    """
    
    def __init__(self, client: BaseAPIClient):
        """
        Initialize Team API
        
        Args:
            client: Base API client instance
        """
        self.client = client
    
    def get_all_teams(self) -> List[Dict[str, Any]]:
        """
        Get all teams for the project
        
        Returns:
            List of team data dictionaries
            
        Raises:
            APIError: If team retrieval fails
        """
        endpoint = f"{self.client.project_key}/teams/all"
        
        logger.info("Fetching all teams")
        
        try:
            data = self.client.get(
                endpoint=endpoint,
                description="fetch all teams",
                base_delay=1.0
            )
            
            # Handle different response formats
            teams = data if isinstance(data, list) else data.get('teams', [])
            
            logger.info(f"Retrieved {len(teams)} teams")
            
            return teams
            
        except APIError as e:
            logger.error(f"Failed to retrieve teams: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error retrieving teams: {e}")
            raise APIError(f"Failed to retrieve teams: {e}")
    
    def get_team_details(self, team_key: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a specific team
        
        Args:
            team_key: Team key/ID
            
        Returns:
            Team details or None if not found
        """
        endpoint = f"{self.client.project_key}/teams/{team_key}"
        
        try:
            data = self.client.get(
                endpoint=endpoint,
                description=f"fetch team {team_key}"
            )
            
            logger.info(f"Retrieved details for team: {team_key}")
            return data
            
        except APIError as e:
            logger.warning(f"Team {team_key} not found or inaccessible: {e}")
            return None
    
    def get_team_members(self, team_key: str) -> List[str]:
        """
        Get member user keys for a specific team
        
        Args:
            team_key: Team key/ID
            
        Returns:
            List of user keys
        """
        team_data = self.get_team_details(team_key)
        
        if not team_data:
            return []
        
        user_keys = team_data.get('user_keys', [])
        logger.info(f"Team {team_key} has {len(user_keys)} members")
        
        return user_keys
    
    def extract_all_user_keys(self, teams_data: Optional[List[Dict[str, Any]]] = None) -> Set[str]:
        """
        Extract all unique user keys from teams
        
        Args:
            teams_data: Optional pre-fetched teams data
            
        Returns:
            Set of unique user keys
        """
        if teams_data is None:
            teams_data = self.get_all_teams()
        
        user_keys: Set[str] = set()
        
        for team in teams_data:
            team_user_keys = team.get('user_keys', [])
            user_keys.update(team_user_keys)
            
            logger.debug(f"Team '{team.get('name', 'unknown')}' has {len(team_user_keys)} members")
        
        logger.info(f"Extracted {len(user_keys)} unique user keys from {len(teams_data)} teams")
        
        return user_keys
    
    def create_team_objects(self, teams_data: List[Dict[str, Any]]) -> List[Team]:
        """
        Convert raw team data to Team objects
        
        Args:
            teams_data: List of raw team data
            
        Returns:
            List of Team objects
        """
        teams = []
        
        for team_data in teams_data:
            try:
                team = Team.from_dict(team_data)
                teams.append(team)
            except Exception as e:
                logger.warning(f"Failed to parse team: {e}")
                continue
        
        logger.info(f"Created {len(teams)} Team objects")
        return teams
    
    def get_teams_by_user(self, user_key: str) -> List[Dict[str, Any]]:
        """
        Get all teams that contain a specific user
        
        Args:
            user_key: User key to search for
            
        Returns:
            List of teams containing the user
        """
        all_teams = self.get_all_teams()
        user_teams = []
        
        for team in all_teams:
            team_user_keys = team.get('user_keys', [])
            if user_key in team_user_keys:
                user_teams.append(team)
        
        logger.info(f"User {user_key} is in {len(user_teams)} teams")
        return user_teams 