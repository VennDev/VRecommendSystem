from fastapi import Request, status
from fastapi.responses import JSONResponse
from typing import Callable
import loguru
import jwt
import os


async def verify_authentication(request: Request, call_next: Callable):
    """
    Middleware to verify user authentication for private routes.

    This middleware checks if the user has a valid JWT token in cookies.
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

    auth_token = request.cookies.get("auth_token")

    if not auth_token:
        loguru.logger.warning(f"Unauthorized access attempt to {path} - No auth token")
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "detail": "Authentication required. Please login to access this resource.",
                "authenticated": False
            }
        )

    try:
        secret_key = os.getenv("JWT_SECRET_KEY") or os.getenv("SESSION_SECRET")
        if not secret_key:
            loguru.logger.error("JWT_SECRET_KEY or SESSION_SECRET not configured")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail": "Server configuration error",
                    "authenticated": False
                }
            )

        payload = jwt.decode(auth_token, secret_key, algorithms=["HS256"])

        user_id = payload.get("user_id")
        email = payload.get("email")

        if not user_id or not email:
            loguru.logger.warning(f"Invalid token payload for {path}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "detail": "Invalid authentication token",
                    "authenticated": False
                }
            )

        loguru.logger.debug(f"Authenticated request to {path} from user {email}")

        request.state.user_id = user_id
        request.state.user_email = email

    except jwt.ExpiredSignatureError:
        loguru.logger.warning(f"Expired token for {path}")
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "detail": "Authentication token has expired. Please login again.",
                "authenticated": False
            }
        )
    except jwt.InvalidTokenError as e:
        loguru.logger.warning(f"Invalid token for {path}: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "detail": "Invalid authentication token",
                "authenticated": False
            }
        )

    response = await call_next(request)
    return response
