import time
import base64
import json
from collections import defaultdict, deque
from typing import Tuple
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from src.config import settings

class RateLimiter:
    def __init__(self):
        self.history = defaultdict(deque)

    def check_rate_limit(self, identifier: str, limit: int, window_seconds: int) -> Tuple[bool, int, float]:
        now = time.time()
        user_history = self.history[identifier]
        
        while user_history and user_history[0] <= now - window_seconds:
            user_history.popleft()
            
        if len(user_history) >= limit:
            retry_after = (user_history[0] + window_seconds) - now
            return False, 0, max(0.0, retry_after)
            
        user_history.append(now)
        remaining = limit - len(user_history)
        return True, remaining, 0.0

general_limiter = RateLimiter()
run_creation_limiter = RateLimiter()

def get_client_identifier(request: Request) -> str:
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]
        parts = token.split(".")
        if len(parts) == 3:
            try:
                payload_part = parts[1]
                payload_part += "=" * ((4 - len(payload_part) % 4) % 4)
                payload_bytes = base64.urlsafe_b64decode(payload_part)
                payload = json.loads(payload_bytes)
                user_id = payload.get("user_id") or payload.get("sub")
                if user_id:
                    return str(user_id)
            except Exception:
                pass
    
    if request.client and request.client.host:
        return request.client.host
    return "unknown"

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        if path.startswith("/auth/") or path.startswith("/docs") or path == "/openapi.json":
            return await call_next(request)
            
        identifier = get_client_identifier(request)
        
        if path == "/runs" and request.method == "POST":
            limit = settings.RATE_LIMIT_RUNS_PER_HOUR
            window = 3600
            allowed, remaining, retry_after = run_creation_limiter.check_rate_limit(identifier, limit, window)
            window_str = "1 hour"
        elif path.startswith("/runs/") and path.endswith("/review") and request.method == "POST":
            limit = settings.RATE_LIMIT_REQUESTS_PER_MINUTE
            window = 60
            allowed, remaining, retry_after = general_limiter.check_rate_limit(identifier, limit, window)
            window_str = "1 minute"
        else:
            # Skip rate limiting for cheap operations (polling status, fetching history)
            return await call_next(request)
            
        if not allowed:
            headers = {
                "Retry-After": str(int(retry_after)),
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(time.time() + retry_after))
            }
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded",
                    "retry_after": retry_after,
                    "limit": limit,
                    "window": window_str
                },
                headers=headers
            )
            
        response = await call_next(request)
        
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + window))
        
        return response
