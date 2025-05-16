from fastapi import Security, HTTPException, status, Depends
from fastapi.security.api_key import APIKeyHeader, APIKey
from typing import Optional

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Optional API key header for protected endpoints
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_api_key(api_key_header: Optional[str] = Security(api_key_header)) -> Optional[str]:
    """
    Validate the API key if provided.
    
    Args:
        api_key_header: The API key from the request header
        
    Returns:
        The validated API key
        
    Raises:
        HTTPException: If an invalid API key is provided
    """
    # If API key security is not configured, allow all requests
    if not hasattr(settings, "API_KEY") or not settings.API_KEY:
        return None
        
    if api_key_header is None:
        logger.warning("Missing API key in request")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key"
        )
        
    if api_key_header != settings.API_KEY:
        logger.warning("Invalid API key provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
        
    return api_key_header
