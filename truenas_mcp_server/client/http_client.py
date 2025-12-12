"""
HTTP Client implementation with connection pooling, retry logic, and logging
"""

import asyncio
import logging
from typing import Optional, Dict, Any, Union
from functools import wraps
import httpx
from httpx import Response, HTTPError, TimeoutException, ConnectError

from ..config import get_settings
from ..exceptions import (
    TrueNASError,
    TrueNASConnectionError,
    TrueNASAuthenticationError,
    TrueNASAPIError,
    TrueNASTimeoutError,
    TrueNASRateLimitError
)

logger = logging.getLogger(__name__)


def retry_on_failure(max_retries: int = 3, backoff_factor: float = 2.0):
    """
    Decorator for retrying failed HTTP requests with exponential backoff
    
    Args:
        max_retries: Maximum number of retry attempts
        backoff_factor: Multiplier for exponential backoff
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except (TimeoutException, ConnectError) as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        wait_time = backoff_factor ** attempt
                        logger.warning(
                            f"Request failed (attempt {attempt + 1}/{max_retries}), "
                            f"retrying in {wait_time}s: {str(e)}"
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"Request failed after {max_retries} attempts: {str(e)}")
                except HTTPError as e:
                    # Don't retry on client errors (4xx)
                    if hasattr(e, 'response') and e.response and 400 <= e.response.status_code < 500:
                        raise
                    last_exception = e
                    if attempt < max_retries - 1:
                        wait_time = backoff_factor ** attempt
                        logger.warning(
                            f"HTTP error (attempt {attempt + 1}/{max_retries}), "
                            f"retrying in {wait_time}s: {str(e)}"
                        )
                        await asyncio.sleep(wait_time)
            
            # If we get here, all retries failed
            if isinstance(last_exception, TimeoutException):
                raise TrueNASTimeoutError(f"Request timed out after {max_retries} attempts")
            elif isinstance(last_exception, ConnectError):
                raise TrueNASConnectionError(f"Connection failed after {max_retries} attempts")
            else:
                raise TrueNASAPIError(f"Request failed after {max_retries} attempts: {str(last_exception)}")
        
        return wrapper
    return decorator


class TrueNASClient:
    """
    HTTP client for TrueNAS API interactions
    
    Provides connection pooling, retry logic, and proper error handling
    """
    
    def __init__(self, settings=None):
        """
        Initialize the TrueNAS client
        
        Args:
            settings: Optional Settings instance (uses get_settings() if not provided)
        """
        self.settings = settings or get_settings()
        self._client = None
        self._request_count = 0
        self._error_count = 0
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def connect(self):
        """Initialize the HTTP client"""
        if self._client is None:
            transport = httpx.AsyncHTTPTransport(
                retries=0,  # We handle retries ourselves
                limits=httpx.Limits(
                    max_connections=self.settings.http_pool_connections,
                    max_keepalive_connections=self.settings.http_pool_maxsize,
                    keepalive_expiry=30.0
                )
            )
            
            self._client = httpx.AsyncClient(
                base_url=self.settings.api_base_url,
                headers=self.settings.headers,
                verify=self.settings.truenas_verify_ssl,
                timeout=httpx.Timeout(self.settings.http_timeout),
                transport=transport,
                follow_redirects=True
            )
            
            logger.info(f"Connected to TrueNAS at {self.settings.truenas_url}")
    
    async def close(self):
        """Close the HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.info("Disconnected from TrueNAS")
    
    async def ensure_connected(self):
        """Ensure the client is connected"""
        if self._client is None:
            await self.connect()
    
    def _log_request(self, method: str, url: str, **kwargs):
        """Log outgoing request"""
        self._request_count += 1
        logger.debug(f"Request #{self._request_count}: {method} {url}")
        if self.settings.log_level == "DEBUG" and kwargs.get("json"):
            logger.debug(f"Request body: {kwargs['json']}")
    
    def _log_response(self, response: Response):
        """Log incoming response"""
        logger.debug(f"Response: {response.status_code} ({response.elapsed.total_seconds():.2f}s)")
        if self.settings.log_level == "DEBUG" and response.content:
            try:
                logger.debug(f"Response body: {response.json()}")
            except:
                pass  # Not JSON response
    
    def _handle_error_response(self, response: Response):
        """Handle error responses from the API"""
        status_code = response.status_code
        
        try:
            error_data = response.json()
            error_message = error_data.get("message", response.text)
        except:
            error_message = response.text
        
        self._error_count += 1
        
        if status_code == 401:
            raise TrueNASAuthenticationError(f"Authentication failed: {error_message}")
        elif status_code == 403:
            raise TrueNASAuthenticationError(f"Permission denied: {error_message}")
        elif status_code == 429:
            raise TrueNASRateLimitError(f"Rate limit exceeded: {error_message}")
        elif 400 <= status_code < 500:
            raise TrueNASAPIError(f"Client error ({status_code}): {error_message}")
        elif 500 <= status_code < 600:
            raise TrueNASAPIError(f"Server error ({status_code}): {error_message}")
        else:
            raise TrueNASAPIError(f"Unexpected status ({status_code}): {error_message}")
    
    @retry_on_failure()
    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Send GET request to TrueNAS API
        
        Args:
            endpoint: API endpoint (relative to base URL)
            params: Optional query parameters
            
        Returns:
            Response data as dictionary
        """
        await self.ensure_connected()
        
        self._log_request("GET", endpoint, params=params)
        response = await self._client.get(endpoint, params=params)
        self._log_response(response)
        
        if response.status_code >= 400:
            self._handle_error_response(response)
        
        return response.json()
    
    @retry_on_failure()
    async def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Send POST request to TrueNAS API
        
        Args:
            endpoint: API endpoint (relative to base URL)
            data: Request body data
            
        Returns:
            Response data as dictionary
        """
        await self.ensure_connected()
        
        self._log_request("POST", endpoint, json=data)
        response = await self._client.post(endpoint, json=data)
        self._log_response(response)
        
        if response.status_code >= 400:
            self._handle_error_response(response)
        
        return response.json()
    
    @retry_on_failure()
    async def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Send PUT request to TrueNAS API
        
        Args:
            endpoint: API endpoint (relative to base URL)
            data: Request body data
            
        Returns:
            Response data as dictionary
        """
        await self.ensure_connected()
        
        self._log_request("PUT", endpoint, json=data)
        response = await self._client.put(endpoint, json=data)
        self._log_response(response)
        
        if response.status_code >= 400:
            self._handle_error_response(response)
        
        return response.json()
    
    @retry_on_failure()
    async def delete(self, endpoint: str) -> bool:
        """
        Send DELETE request to TrueNAS API
        
        Args:
            endpoint: API endpoint (relative to base URL)
            
        Returns:
            True if successful
        """
        await self.ensure_connected()
        
        self._log_request("DELETE", endpoint)
        response = await self._client.delete(endpoint)
        self._log_response(response)
        
        if response.status_code >= 400:
            self._handle_error_response(response)
        
        return response.status_code < 300
    
    def get_stats(self) -> Dict[str, int]:
        """Get client statistics"""
        return {
            "requests": self._request_count,
            "errors": self._error_count,
            "error_rate": self._error_count / max(self._request_count, 1)
        }


# Global client instance
_client: Optional[TrueNASClient] = None


async def get_client() -> TrueNASClient:
    """
    Get or create the global TrueNAS client instance
    
    Returns:
        TrueNASClient instance
    """
    global _client
    if _client is None:
        _client = TrueNASClient()
        await _client.connect()
    return _client


async def close_client():
    """Close the global client instance"""
    global _client
    if _client:
        await _client.close()
        _client = None