import logging
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .tools import current_user_context, current_auth_token

from .config import settings

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Simple auth middleware — extracts Bearer token and stores it in context.
    No JWT validation here; Django validates on each proxied API call.
    """

    async def dispatch(self, request: Request, call_next):
        # Skip authentication for public endpoints
        public_paths = [
            "/.well-known/",
            "/oauth2/register",
            "/oauth2/authorize",
            "/oauth2/callback",
            "/oauth2/token",
        ]

        # Skip MCP discovery endpoints
        if request.url.path.startswith("/mcp/.well-known/"):
            return await call_next(request)

        for path in public_paths:
            if request.url.path.startswith(path):
                return await call_next(request)

        # Extract Bearer token
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            # RFC 9728 requires resource_metadata in the WWW-Authenticate header
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

        # Store token in context — tools use this to proxy requests to Django
        current_auth_token.set(token)

        # We don't decode the JWT; set minimal context so tools know a token exists
        current_user_context.set({"authenticated": True})

        logger.debug(f"Bearer token forwarded for request: {request.url.path}")

        return await call_next(request)