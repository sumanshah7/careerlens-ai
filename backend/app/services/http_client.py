"""
HTTP client wrapper with timeouts, retries, and circuit breaker integration
"""
import httpx
import asyncio
from typing import Optional, Dict, Any
from app.services.circuit_breaker import circuit_breaker


class ResilientHTTPClient:
    """HTTP client with resilience features"""
    
    def __init__(
        self,
        timeout: float = 12.0,
        connect_timeout: float = 5.0,
        max_retries: int = 2,
        retry_delay: float = 1.0,
    ):
        """
        Initialize resilient HTTP client
        
        Args:
            timeout: Total request timeout in seconds
            connect_timeout: Connection timeout in seconds
            max_retries: Maximum number of retries
            retry_delay: Initial delay between retries (exponential backoff)
        """
        self.timeout = httpx.Timeout(timeout, connect=connect_timeout)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
    async def get(
        self,
        url: str,
        provider_name: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        """
        GET request with retries and circuit breaker
        
        Args:
            url: Request URL
            provider_name: Provider name for circuit breaker
            headers: Request headers
            params: Query parameters
        
        Returns:
            httpx.Response
        
        Raises:
            httpx.HTTPError: If all retries fail
        """
        # Check circuit breaker
        if circuit_breaker.is_open(provider_name):
            raise httpx.HTTPError(f"Circuit breaker is open for {provider_name}")
        
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(url, headers=headers, params=params)
                    response.raise_for_status()
                    
                    # Success - record and return
                    circuit_breaker.record_success(provider_name)
                    return response
                    
            except (httpx.HTTPStatusError, httpx.TimeoutException, httpx.ConnectError) as e:
                last_error = e
                
                # If last attempt, record failure and raise
                if attempt == self.max_retries:
                    circuit_breaker.record_failure(provider_name)
                    raise
                
                # Exponential backoff
                delay = self.retry_delay * (2 ** attempt)
                await asyncio.sleep(delay)
        
        # Should never reach here, but just in case
        circuit_breaker.record_failure(provider_name)
        raise last_error or httpx.HTTPError("Request failed")
    
    async def post(
        self,
        url: str,
        provider_name: str,
        headers: Optional[Dict[str, str]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        """
        POST request with retries and circuit breaker
        
        Args:
            url: Request URL
            provider_name: Provider name for circuit breaker
            headers: Request headers
            json: JSON body
        
        Returns:
            httpx.Response
        
        Raises:
            httpx.HTTPError: If all retries fail
        """
        # Check circuit breaker
        if circuit_breaker.is_open(provider_name):
            raise httpx.HTTPError(f"Circuit breaker is open for {provider_name}")
        
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(url, headers=headers, json=json)
                    response.raise_for_status()
                    
                    # Success - record and return
                    circuit_breaker.record_success(provider_name)
                    return response
                    
            except (httpx.HTTPStatusError, httpx.TimeoutException, httpx.ConnectError) as e:
                last_error = e
                
                # If last attempt, record failure and raise
                if attempt == self.max_retries:
                    circuit_breaker.record_failure(provider_name)
                    raise
                
                # Exponential backoff
                delay = self.retry_delay * (2 ** attempt)
                await asyncio.sleep(delay)
        
        # Should never reach here, but just in case
        circuit_breaker.record_failure(provider_name)
        raise last_error or httpx.HTTPError("Request failed")


# Global client instance
http_client = ResilientHTTPClient(timeout=12.0, connect_timeout=5.0, max_retries=2)

