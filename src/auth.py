import logging
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

import httpx

from .tools import current_user_context, current_auth_token

from .config import settings

logger = logging.getLogger(__name__)


async def validate_api_key(api_key: str) -> dict | None:
    """
    Validate API key against Django's connection test endpoint.
    Returns user info dict if valid, None if invalid.
    """
    try:
        url = f"{settings.DJANGO_BASE_URL.rstrip('/')}/api/connection-test/"
        headers = {"Authorization": f"Api-Key {api_key}"}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=10.0)

            if response.status_code == 200:
                data = response.json()
                if data.get("authenticated"):
                    return {
                        "authenticated": True,
                        "user": data.get("user"),
                        "email": data.get("user"),
                    }
            return None

    except Exception as e:
        logger.error(f"API key validation failed: {e}")
        return None


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Auth middleware supporting both Bearer tokens and API keys.
    API keys are validated against Django's connection-test endpoint first.
    """

    async def dispatch(self, request: Request, call_next):
        public_paths = [
            "/.well-known/",
            "/oauth2/register",
            "/oauth2/authorize",
            "/oauth2/callback",
            "/oauth2/token",
        ]

        if request.url.path.startswith("/mcp/.well-known/"):
            return await call_next(request)

        for path in public_paths:
            if request.url.path.startswith(path):
                return await call_next(request)

        auth_header = request.headers.get("Authorization")

        if auth_header and auth_header.startswith("Api-Key "):
            api_key = auth_header.split(" ", 1)[1]
            user_info = await validate_api_key(api_key)

            if user_info:
                current_auth_token.set(api_key)
                current_user_context.set(user_info)
                logger.debug(f"API key authenticated for request: {request.url.path}")
                return await call_next(request)
            else:
                return JSONResponse(
                    status_code=401,
                    content={
                        "error": "invalid_token",
                        "error_description": "Invalid or expired API key",
                    },
                )

        if not auth_header or not auth_header.startswith("Bearer "):
            resource_metadata_url = (
                f"{settings.MCP_PUBLIC_BASE_URL}/.well-known/oauth-protected-resource/mcp"
            )
            return JSONResponse(
                status_code=401,
                content={
                    "error": "invalid_token",
                    "error_description": "Missing or invalid authorization header",
                },
                headers={
                    "WWW-Authenticate": f'Bearer realm="mcp", resource_metadata="{resource_metadata_url}"'
                },
            )

        token = auth_header.split(" ", 1)[1]

        current_auth_token.set(token)
        current_user_context.set({"authenticated": True})

        logger.debug(f"Bearer token forwarded for request: {request.url.path}")

        return await call_next(request)