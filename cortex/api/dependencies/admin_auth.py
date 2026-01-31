"""Admin API authentication dependency"""
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from cortex.core.config.execution_env import ExecutionEnv

API_KEY_HEADER = APIKeyHeader(name="X-Admin-API-Key", auto_error=True)


async def verify_admin_api_key(api_key: str = Security(API_KEY_HEADER)) -> str:
    """Verify admin API key from request header
    
    Args:
        api_key: The admin API key from X-Admin-API-Key header
        
    Returns:
        The validated API key
        
    Raises:
        HTTPException: 500 if key not configured, 403 if invalid
    """
    expected_key = ExecutionEnv.get_key("CORTEX_ADMIN_API_KEY", "")
    
    if not expected_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Admin API key not configured"
        )
    
    if api_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin API key"
        )
    
    return api_key
