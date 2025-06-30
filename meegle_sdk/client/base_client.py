"""
Base API Client for Meegle SDK with retry and error handling
"""

import time
import logging
import requests
from typing import Dict, Optional, Any

from ..models.base_models import APIError, RateLimitError, AuthenticationError
from ..auth.token_manager import TokenManager
from config.settings import get_meegle_config

logger = logging.getLogger(__name__)


class BaseAPIClient:
    """
    Base API client with common functionality
    
    Features:
    - Automatic retry with exponential backoff
    - Rate limit handling
    - Error handling and logging
    - Authentication token management
    """
    
    def __init__(self, token_manager: TokenManager, project_key: str, 
                 max_retries: int = 3, request_timeout: int = 30):
        """
        Initialize Base API Client
        
        Args:
            token_manager: Token manager instance
            project_key: Meegle project key
            max_retries: Maximum number of retries for failed requests
            request_timeout: Request timeout in seconds
        """
        self.token_manager = token_manager
        self.project_key = project_key
        self.max_retries = max_retries
        self.request_timeout = request_timeout
        
        config = get_meegle_config()
        self.base_url = config['base_url']
    
    def _get_headers(self, additional_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """
        Get request headers with authentication
        
        Args:
            additional_headers: Additional headers to include
            
        Returns:
            Complete headers dictionary
        """
        token = self.token_manager.get_valid_token()
        
        headers = {
            "Content-Type": "application/json",
            "X-User-Key": self.token_manager.user_key,
            "X-Plugin-Token": token
        }
        
        if additional_headers:
            headers.update(additional_headers)
            
        return headers
    
    def _make_request(self, method: str, endpoint: str, 
                     headers: Optional[Dict] = None,
                     params: Optional[Dict] = None, 
                     json_data: Optional[Dict] = None,
                     description: str = "API request", 
                     base_delay: float = 1.0) -> Dict[str, Any]:
        """
        Make API request with retry mechanism
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (relative to base URL)
            headers: Additional headers
            params: Query parameters
            json_data: JSON request body
            description: Description for logging
            base_delay: Base delay between retries
            
        Returns:
            API response data
            
        Raises:
            APIError: If request fails after all retries
            RateLimitError: If rate limit exceeded
            AuthenticationError: If authentication fails
        """
        url = f"{self.base_url}/{endpoint}"
        request_headers = self._get_headers(headers)
        
        logger.debug(f"Making {method} request to: {url}")
        
        for attempt in range(self.max_retries):
            try:
                # Add delay for retries
                if attempt > 0:
                    wait_time = min(base_delay * (3 ** attempt), 30)
                    logger.info(f"Retrying {description} (attempt {attempt + 1}/{self.max_retries})")
                    logger.info(f"Waiting {wait_time:.1f} seconds before retry...")
                    time.sleep(wait_time)
                elif base_delay > 0:
                    time.sleep(base_delay)
                
                # Make the request
                response = requests.request(
                    method=method,
                    url=url,
                    headers=request_headers,
                    params=params,
                    json=json_data,
                    timeout=self.request_timeout
                )
                
                logger.debug(f"Response status: {response.status_code}")
                
                # Handle successful response
                if response.status_code == 200:
                    try:
                        data = response.json()
                        err_code = data.get('err_code', data.get('error', {}).get('code'))
                        
                        # Check for API-level errors
                        if err_code == 0 or err_code is None:
                            result = data.get('data', {})
                            logger.debug(f"Request successful: {description}")
                            return result
                        else:
                            err_msg = data.get('err_msg', data.get('error', {}).get('msg', 'Unknown error'))
                            logger.error(f"API error in {description}: {err_msg}")
                            raise APIError(f"API error: {err_msg}", response.status_code, data)
                            
                    except ValueError as e:
                        logger.error(f"Invalid JSON response: {e}")
                        raise APIError(f"Invalid JSON response: {e}", response.status_code)
                
                # Handle rate limiting
                elif response.status_code == 429:
                    # Log detailed 429 response information
                    logger.error(f"=== 429 Rate Limit Details ===")
                    logger.error(f"URL: {url}")
                    logger.error(f"Headers: {dict(response.headers)}")
                    logger.error(f"Response Text: {response.text}")
                    try:
                        response_json = response.json()
                        logger.error(f"Response JSON: {response_json}")
                    except:
                        logger.error("Response is not valid JSON")
                    logger.error(f"================================")
                    
                    if attempt < self.max_retries - 1:
                        rate_limit_delay = min(30 * (2 ** attempt), 300)  # Much longer waits: 30s, 60s, 120s
                        logger.warning(f"Rate limit hit (429). Waiting {rate_limit_delay} seconds...")
                        time.sleep(rate_limit_delay)
                        continue
                    else:
                        logger.error(f"Rate limit exceeded after {self.max_retries} attempts")
                        raise RateLimitError(f"Rate limit exceeded after {self.max_retries} attempts")
                
                # Handle authentication errors
                elif response.status_code in [401, 403]:
                    logger.error(f"Authentication error: {response.status_code}")
                    # Invalidate current token
                    self.token_manager.invalidate_token()
                    if attempt < self.max_retries - 1:
                        # Try to get a new token for retry
                        continue
                    else:
                        raise AuthenticationError(f"Authentication failed: {response.text}")
                
                # Handle other HTTP errors
                else:
                    if attempt == self.max_retries - 1:
                        logger.error(f"HTTP error {response.status_code}: {response.text}")
                        raise APIError(f"HTTP {response.status_code}: {response.text}", response.status_code)
                    else:
                        logger.warning(f"HTTP error {response.status_code}, will retry")
                        
            except requests.RequestException as e:
                logger.warning(f"Network error during {description}: {e}")
                if attempt == self.max_retries - 1:
                    raise APIError(f"Network error: {e}")
            except (AuthenticationError, RateLimitError):
                # Re-raise these specific exceptions
                raise
            except Exception as e:
                logger.warning(f"Unexpected error during {description}: {e}")
                if attempt == self.max_retries - 1:
                    raise APIError(f"Unexpected error: {e}")
        
        raise APIError(f"Max retries exceeded for {description}")
    
    def get(self, endpoint: str, params: Optional[Dict] = None, 
            description: str = "GET request", **kwargs) -> Dict[str, Any]:
        """Make GET request"""
        return self._make_request("GET", endpoint, params=params, 
                                description=description, **kwargs)
    
    def post(self, endpoint: str, json_data: Optional[Dict] = None,
             description: str = "POST request", **kwargs) -> Dict[str, Any]:
        """Make POST request"""
        return self._make_request("POST", endpoint, json_data=json_data,
                                description=description, **kwargs)
    
    def put(self, endpoint: str, json_data: Optional[Dict] = None,
            description: str = "PUT request", **kwargs) -> Dict[str, Any]:
        """Make PUT request"""
        return self._make_request("PUT", endpoint, json_data=json_data,
                                description=description, **kwargs)
    
    def delete(self, endpoint: str, description: str = "DELETE request", 
               **kwargs) -> Dict[str, Any]:
        """Make DELETE request"""
        return self._make_request("DELETE", endpoint, description=description, **kwargs) 