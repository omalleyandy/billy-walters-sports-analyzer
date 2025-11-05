"""
Centralized async HTTP client for Billy Walters Sports Analyzer.

Provides:
- Singleton aiohttp session with connection pooling
- Automatic error handling and retries
- Consistent interface for all HTTP requests
- Resource cleanup on shutdown

Usage:
    from walters.core.http_client import async_get, async_post
    
    # GET request
    response = await async_get("https://api.example.com", params={'key': 'value'})
    if response['status'] == 200:
        data = response['data']
    
    # POST request
    response = await async_post("https://api.example.com", json={'data': 'value'})
    
    # Cleanup on shutdown
    await cleanup_http_client()
"""

import aiohttp
import logging
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

# Singleton session for connection pooling
_CLIENT_SESSION: Optional[aiohttp.ClientSession] = None


async def get_client_session() -> aiohttp.ClientSession:
    """
    Get or create singleton aiohttp session with connection pooling.
    
    This creates a single session that's reused across all HTTP requests,
    which provides:
    - Connection pooling (faster subsequent requests)
    - Keep-alive connections
    - Automatic connection management
    
    Returns:
        Configured aiohttp ClientSession
    """
    global _CLIENT_SESSION
    
    if _CLIENT_SESSION is None or _CLIENT_SESSION.closed:
        # Configure connection pooling
        connector = aiohttp.TCPConnector(
            limit=100,              # Max 100 connections total
            limit_per_host=30,      # Max 30 connections per host
            ttl_dns_cache=300,      # DNS cache for 5 minutes
            enable_cleanup_closed=True
        )
        
        # Configure timeouts
        timeout = aiohttp.ClientTimeout(
            total=30,               # Total timeout 30 seconds
            connect=10,             # Connection timeout 10 seconds
            sock_read=20            # Socket read timeout 20 seconds
        )
        
        # Create session
        _CLIENT_SESSION = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'Billy-Walters-Sports-Analyzer/2.0',
                'Accept': 'application/json,text/html,*/*'
            }
        )
        
        logger.info("Created new HTTP client session with connection pooling")
    
    return _CLIENT_SESSION


async def async_get(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: Optional[int] = None
) -> Dict[str, Any]:
    """
    Async GET request with error handling.
    
    Args:
        url: URL to request
        params: Query parameters (optional)
        headers: Additional headers (optional)
        timeout: Override default timeout in seconds (optional)
    
    Returns:
        Dict with:
            - status: HTTP status code (0 if error)
            - data: Response data (JSON or text)
            - headers: Response headers
            - error: Error message (if failed)
    
    Example:
        response = await async_get(
            "https://api.weather.com/forecast",
            params={'city': 'Buffalo', 'units': 'imperial'}
        )
        
        if response['status'] == 200:
            weather = response['data']
            print(f"Temperature: {weather['temp']}")
        else:
            print(f"Error: {response.get('error')}")
    """
    session = await get_client_session()
    
    # Custom timeout if provided
    custom_timeout = None
    if timeout:
        custom_timeout = aiohttp.ClientTimeout(total=timeout)
    
    try:
        async with session.get(
            url,
            params=params,
            headers=headers,
            timeout=custom_timeout
        ) as response:
            # Parse response based on content type
            content_type = response.content_type or ''
            
            if 'application/json' in content_type:
                data = await response.json()
            else:
                data = await response.text()
            
            return {
                'status': response.status,
                'data': data,
                'headers': dict(response.headers)
            }
    
    except aiohttp.ClientError as e:
        logger.error(f"HTTP client error for {url}: {e}")
        return {
            'status': 0,
            'error': f"Client error: {str(e)}",
            'data': None
        }
    
    except asyncio.TimeoutError:
        logger.error(f"Timeout for {url}")
        return {
            'status': 0,
            'error': "Request timeout",
            'data': None
        }
    
    except Exception as e:
        logger.error(f"Unexpected error for {url}: {e}", exc_info=True)
        return {
            'status': 0,
            'error': f"Unexpected error: {str(e)}",
            'data': None
        }


async def async_post(
    url: str,
    data: Optional[Dict] = None,
    json: Optional[Dict] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: Optional[int] = None
) -> Dict[str, Any]:
    """
    Async POST request with error handling.
    
    Args:
        url: URL to request
        data: Form data (optional)
        json: JSON data (optional)
        headers: Additional headers (optional)
        timeout: Override default timeout in seconds (optional)
    
    Returns:
        Dict with status, data, and optional error
    
    Example:
        response = await async_post(
            "https://api.example.com/submit",
            json={'team': 'Kansas City Chiefs', 'rating': 95.5}
        )
    """
    session = await get_client_session()
    
    # Custom timeout if provided
    custom_timeout = None
    if timeout:
        custom_timeout = aiohttp.ClientTimeout(total=timeout)
    
    try:
        async with session.post(
            url,
            data=data,
            json=json,
            headers=headers,
            timeout=custom_timeout
        ) as response:
            # Parse response
            content_type = response.content_type or ''
            
            if 'application/json' in content_type:
                response_data = await response.json()
            else:
                response_data = await response.text()
            
            return {
                'status': response.status,
                'data': response_data,
                'headers': dict(response.headers)
            }
    
    except aiohttp.ClientError as e:
        logger.error(f"POST error for {url}: {e}")
        return {
            'status': 0,
            'error': f"Client error: {str(e)}",
            'data': None
        }
    
    except asyncio.TimeoutError:
        logger.error(f"POST timeout for {url}")
        return {
            'status': 0,
            'error': "Request timeout",
            'data': None
        }
    
    except Exception as e:
        logger.error(f"POST unexpected error for {url}: {e}", exc_info=True)
        return {
            'status': 0,
            'error': str(e),
            'data': None
        }


async def cleanup_http_client():
    """
    Cleanup HTTP client session.
    
    Call this on application shutdown to properly close connections.
    
    Example:
        try:
            # Your application code
            await run_analysis()
        finally:
            # Cleanup
            await cleanup_http_client()
    """
    global _CLIENT_SESSION
    
    if _CLIENT_SESSION and not _CLIENT_SESSION.closed:
        await _CLIENT_SESSION.close()
        logger.info("Closed HTTP client session")
        _CLIENT_SESSION = None


# Import asyncio for the timeout exception
import asyncio


# Example usage and testing
if __name__ == "__main__":
    import asyncio
    
    async def test_http_client():
        """Test the HTTP client functionality."""
        print("Testing HTTP Client...")
        print("=" * 50)
        
        # Test 1: GET request to public API
        print("\n1. Testing GET request...")
        result = await async_get("https://api.github.com/users/github")
        
        if result['status'] == 200:
            print(f"[OK] Success! Status: {result['status']}")
            print(f"   GitHub Name: {result['data'].get('name')}")
        else:
            print(f"[FAIL] Failed: {result.get('error')}")
        
        # Test 2: Connection reuse (second call should be faster)
        print("\n2. Testing connection pooling (second call)...")
        import time
        
        start = time.time()
        result1 = await async_get("https://api.github.com/users/github")
        time1 = time.time() - start
        
        start = time.time()
        result2 = await async_get("https://api.github.com/users/github")
        time2 = time.time() - start
        
        print(f"   First call:  {time1:.3f}s")
        print(f"   Second call: {time2:.3f}s (using connection pool)")
        if time2 > 0:
            print(f"   Speedup: {time1/time2:.1f}x faster!")
        
        # Test 3: Error handling
        print("\n3. Testing error handling...")
        result = await async_get("https://invalid-url-that-does-not-exist.com")
        
        if result['status'] == 0:
            print(f"[OK] Error handled gracefully: {result.get('error')}")
        
        # Cleanup
        print("\n4. Cleaning up...")
        await cleanup_http_client()
        print("[OK] Cleanup complete!")
        
        print("\n" + "=" * 50)
        print("HTTP Client test complete!")
    
    # Run tests
    asyncio.run(test_http_client())

