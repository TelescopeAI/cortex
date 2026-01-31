"""HTTP client for calling Cortex admin APIs"""
import httpx
import logging
from typing import Optional
from cortex.core.config.execution_env import ExecutionEnv

logger = logging.getLogger(__name__)


class CortexAdminAPIClient:
    """HTTP client for calling Cortex admin APIs
    
    Handles communication with the API server's admin endpoints,
    allowing the jobs server to trigger operations in distributed deployments.
    """
    
    def __init__(
        self, 
        api_base_url: Optional[str] = None,
        admin_api_key: Optional[str] = None,
        timeout: float = 30.0
    ):
        """Initialize the admin API client
        
        Args:
            api_base_url: Base URL of the API server (defaults to CORTEX_API_BASE_URL env var)
            admin_api_key: Admin API key for authentication (defaults to CORTEX_ADMIN_API_KEY env var)
            timeout: Request timeout in seconds (default: 30.0)
        """
        self.api_base_url = api_base_url or ExecutionEnv.get_key(
            "CORTEX_API_BASE_URL", 
            "http://localhost:9002"
        )
        self.admin_api_key = admin_api_key or ExecutionEnv.get_key(
            "CORTEX_ADMIN_API_KEY", 
            ""
        )
        self.timeout = timeout
        
        if not self.admin_api_key:
            logger.warning("CORTEX_ADMIN_API_KEY not set - admin API calls will fail")
    
    async def evict_cache(self) -> dict:
        """Call admin API to evict cache
        
        Returns:
            Dictionary with evicted_files count and status
            
        Raises:
            httpx.HTTPStatusError: If the API request fails
            httpx.RequestError: If the connection fails
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_base_url}/api/v1/admin/cache/evict",
                    headers={"X-Admin-API-Key": self.admin_api_key}
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Admin API request failed: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Failed to connect to admin API: {e}")
            raise
    
    async def get_cache_status(self) -> dict:
        """Get cache status from admin API
        
        Returns:
            Dictionary with cache_size_gb, max_size_gb, and entries_count
            
        Raises:
            httpx.HTTPStatusError: If the API request fails
            httpx.RequestError: If the connection fails
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.api_base_url}/api/v1/admin/cache/status",
                    headers={"X-Admin-API-Key": self.admin_api_key}
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Admin API request failed: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Failed to connect to admin API: {e}")
            raise
