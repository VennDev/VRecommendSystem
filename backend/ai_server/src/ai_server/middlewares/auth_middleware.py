from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Callable
import loguru


async def verify_authentication(request: Request, call_next: Callable):
    """
    Middleware to verify user authentication for private routes.

    This middleware checks if the user has a valid session cookie.
    If not authenticated, returns a 401 Unauthorized response.
    """

    path = request.url.path

    public_paths = [
        "/api/v1/health",
        "/api/v1/recommend",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/metrics"
    ]

    is_public = any(path.startswith(public_path) for public_path in public_paths)

    if is_public:
        response = await call_next(request)
        return response

    session_cookie = request.cookies.get("session")

    if not session_cookie:
        loguru.logger.warning(f"Unauthorized access attempt to {path} - No session cookie")
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "detail": "Authentication required. Please login to access this resource.",
                "authenticated": False
            }
        )

    loguru.logger.debug(f"Authenticated request to {path}")

    response = await call_next(request)
    return response
