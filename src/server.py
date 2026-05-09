import asyncio
import contextlib
import uvicorn
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import Message

from .auth import AuthMiddleware
from .config import settings
from .tools import mcp as tools_server
from .oauth import (
    create_oauth2_router,
    get_oauth2_metadata,
    cleanup_expired,
    is_origin_allowed,
)

logger = logging.getLogger(__name__)


# ── Dynamic CORS ───────────────────────────────────────────────────────────


class DynamicCORSMiddleware(CORSMiddleware):
    """
    CORS middleware that validates origins dynamically against registered clients.
    """

    def is_allowed_origin(self, origin: str) -> bool:
        return is_origin_allowed(origin)


# Create MCP server first
mcp_server = tools_server.http_app(path="/", stateless_http=True)

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for the FastAPI app.
    Starts background tasks and manages MCP server lifespan.
    """
    logger.info("Application starting up...")
    # Start background tasks
    cleanup_task = asyncio.create_task(cleanup_expired())

    try:
        # Run MCP server lifespan (required for FastMCP 3.0)
        async with mcp_server.lifespan(app):
            yield
    finally:
        logger.info("Application shutting down...")
        # Clean up background tasks
        cleanup_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await cleanup_task
        logger.info("Application shutdown complete.")


# Create FastAPI app with combined lifespan
app = FastAPI(lifespan=lifespan)


# ── Security Headers ──────────────────────────────────────────────────────


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        # Prevent Clickjacking (sec-2.md Requirement)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = "frame-ancestors 'none'"
        # Prevent MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response


app.add_middleware(SecurityHeadersMiddleware)

# CORS (Replaced allow_origins=["*"] with DynamicCORSMiddleware)
app.add_middleware(
    DynamicCORSMiddleware,
    allow_origins=[],  # Handled by DynamicCORSMiddleware.is_allowed_origin
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# OAuth2 routes
oauth2_router = create_oauth2_router()
app.include_router(oauth2_router, prefix="", tags=["oauth2"])


# ── Health check endpoint ─────────────────────────────────────────────────


@app.get("/health")
async def health_check():
    """Health check endpoint to verify the service is running."""
    return {"status": "healthy", "service": "mcp-server"}


# ── Well-known endpoints ─────────────────────────────────────────────────


@app.get("/.well-known/oauth-authorization-server")
async def oauth_metadata():
    return get_oauth2_metadata()


@app.get("/.well-known/oauth-authorization-server/mcp")
async def oauth_metadata_mcp():
    """MCP-specific metadata (for Cursor)."""
    return get_oauth2_metadata()


@app.get("/.well-known/openid-configuration/mcp")
async def openid_config_mcp():
    """OpenID Connect config (for Gemini CLI)."""
    return get_oauth2_metadata()


@app.get("/.well-known/oauth-protected-resource/mcp")
async def protected_resource_metadata():
    """Protected Resource Metadata for MCP client discovery (RFC 9728)."""
    return {
        "resource": settings.MCP_PUBLIC_BASE_URL + "/mcp/",
        "authorization_servers": [settings.MCP_PUBLIC_BASE_URL],
        "scopes_supported": ["openid", "profile", "email", "mcp:tools"],
    }


# ── Trailing slash normalization ─────────────────────────────────────────


class TrailingSlashMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        no_trailing = [
            "/oauth2/register",
            "/oauth2/authorize",
            "/oauth2/callback",
            "/oauth2/token",
        ]
        path = request.url.path
        for endpoint in no_trailing:
            if path == endpoint + "/":
                from starlette.responses import RedirectResponse

                return RedirectResponse(
                    url=str(request.url).replace(endpoint + "/", endpoint),
                    status_code=301,
                )
        return await call_next(request)


app.add_middleware(TrailingSlashMiddleware)


# ── Request logging (debug) ──────────────────────────────────────────────


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        body = await request.body()

        logger.info(f"MCP Request: {request.method} {request.url.path}")
        if body:
            logger.debug(f"MCP Request Body: {body.decode('utf-8')}")

        async def receive() -> Message:
            return {"type": "http.request", "body": body}

        new_request = Request(request.scope, receive)
        return await call_next(new_request)


# Add middleware to MCP server
mcp_server.add_middleware(RequestLoggingMiddleware)
mcp_server.add_middleware(AuthMiddleware)

# Mount MCP server
app.mount("/mcp", mcp_server)


def main():
    """Main entry point for the MCP server."""
    uvicorn.run(app, host="127.0.0.1", port=settings.PORT, log_level="info")


if __name__ == "__main__":
    main()
