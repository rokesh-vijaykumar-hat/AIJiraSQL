import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_429_TOO_MANY_REQUESTS
import asyncio
from collections import defaultdict
from datetime import datetime, timedelta

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware for rate limiting API requests based on client IP.
    """
    def __init__(self, app):
        super().__init__(app)
        self.request_counts = defaultdict(list)
        self.lock = asyncio.Lock()
        logger.info(f"Rate limiting middleware initialized: {settings.RATE_LIMIT_REQUESTS} requests per {settings.RATE_LIMIT_PERIOD} seconds")

    async def dispatch(self, request: Request, call_next):
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)

        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Clean up old request timestamps
        now = datetime.now()
        window_start = now - timedelta(seconds=settings.RATE_LIMIT_PERIOD)
        
        async with self.lock:
            # Remove timestamps older than the rate limit window
            self.request_counts[client_ip] = [
                timestamp for timestamp in self.request_counts[client_ip]
                if timestamp > window_start
            ]
            
            # Count requests within the rate limit window
            request_count = len(self.request_counts[client_ip])
            
            if request_count >= settings.RATE_LIMIT_REQUESTS:
                logger.warning(f"Rate limit exceeded for IP: {client_ip}")
                response = Response(
                    content={"error": "Rate limit exceeded. Please try again later."},
                    status_code=HTTP_429_TOO_MANY_REQUESTS,
                    media_type="application/json"
                )
                response.headers["Retry-After"] = str(settings.RATE_LIMIT_PERIOD)
                return response
                
            # Record this request
            self.request_counts[client_ip].append(now)
        
        # Process the request normally
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Add X-Process-Time header
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
