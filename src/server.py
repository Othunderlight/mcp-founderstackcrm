
import io
import asyncio
import contextlib
import uvicorn
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from .auth import AuthMiddleware
from .config import settings
from .tools import mcp as tools_server
from .oauth import create_oauth2_router, get_oauth2_metadata
import json

logger = logging.getLogger(__name__)

# Create a combined lifespan to manage the MCP session manager
@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    async with tools_server.session_manager.run():
        yield

app = FastAPI(lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your actual origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include OAuth2 router
oauth2_router = create_oauth2_router()
app.include_router(oauth2_router, prefix="", tags=["oauth2"])

# OAuth2 Authorization Server Metadata endpoint
@app.get("/.well-known/oauth-authorization-server")
async def oauth_authorization_server_metadata():
    """
    OAuth 2.0 Authorization Server Metadata endpoint.
    Provides OAuth2 configuration for dynamic client registration and authorization.
    """
    return get_oauth2_metadata()

# MCP-specific OAuth2 Authorization Server Metadata endpoint
@app.get("/.well-known/oauth-authorization-server/mcp")
async def oauth_authorization_server_metadata_mcp():
    """
    MCP-specific OAuth 2.0 Authorization Server Metadata endpoint.
    Required by Cursor for OAuth discovery and to show the "Open in Cursor" button.
    """
    return get_oauth2_metadata()

# OpenID Connect Configuration endpoint for MCP
@app.get("/.well-known/openid-configuration/mcp")
async def openid_configuration_mcp():
    """
    OpenID Connect Configuration endpoint for MCP.
    Required by Gemini CLI for OAuth discovery.
    """
    base_url = f"http://127.0.0.1:{settings.PORT}"
    return {
        "issuer": base_url,
        "authorization_endpoint": f"{base_url}/oauth2/authorize",
        "token_endpoint": f"{base_url}/oauth2/token",
        "userinfo_endpoint": f"{base_url}/oauth2/userinfo",
        "jwks_uri": settings.JWKS_URL,
        "registration_endpoint": f"{base_url}/oauth2/register",
        "scopes_supported": ["openid", "profile", "email"],
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "client_credentials"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["RS256"],
        "token_endpoint_auth_methods_supported": ["client_secret_basic", "client_secret_post", "none"],
        "claims_supported": ["sub", "iss", "aud", "exp", "iat", "email", "email_verified", "name"],
        "code_challenge_methods_supported": ["S256", "plain"]
    }

# MCP well-known endpoint
@app.get("/.well-known/oauth-protected-resource/mcp")
async def oauth_protected_resource_metadata():
    """
    OAuth 2.0 Protected Resource Metadata endpoint for MCP client discovery.
    Required by the MCP specification for authorization server discovery.
    """
    if settings.METADATA_JSON_RESPONSE:
        response = json.loads(settings.METADATA_JSON_RESPONSE)
        return response
    else:
        # Default metadata response with OAuth2 support
        base_url = f"http://127.0.0.1:{settings.PORT}"
        return {
            "resource": "cccrm-api",
            "resource_server_metadata": {
                "authorization_servers": [base_url],
                "authorization_server_metadata_url": f"{base_url}/.well-known/oauth-authorization-server",
                "jwks_uri": settings.JWKS_URL,
                "audience": settings.JWT_AUDIENCE,
                "issuer": settings.JWT_ISSUER,
                "oauth2_dynamic_registration_supported": True,
                "registration_endpoint": f"{base_url}/oauth2/register",
                "mcp_version": "1.0",
                "mcp_capabilities": {
                    "dynamic_client_registration": True,
                    "pkce_support": True,
                    "google_oauth_integration": True
                }
            }
        }

class TrailingSlashMiddleware(BaseHTTPMiddleware):
    """Middleware to handle trailing slash normalization for all endpoints"""
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Define endpoints that should NOT have trailing slashes
        no_trailing_slash_endpoints = [
            "/oauth2/register",
            "/oauth2/authorize", 
            "/oauth2/callback",
            "/oauth2/token",
            "/oauth2/userinfo",
            "/oauth2/introspect"
        ]
        
        current_path = request.url.path
        
        # Check if this is an endpoint that should not have a trailing slash
        for endpoint in no_trailing_slash_endpoints:
            if current_path == endpoint + "/":
                # Redirect to version without trailing slash
                from starlette.responses import RedirectResponse
                redirect_url = str(request.url).replace(endpoint + "/", endpoint)
                logger.info(f"Redirecting {current_path} to {endpoint}")
                return RedirectResponse(url=redirect_url, status_code=301)
        
        return await call_next(request)

# Add trailing slash normalization middleware
app.add_middleware(TrailingSlashMiddleware)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        logger.info(f"MCP Request Path: {request.url.path}")
        logger.info(f"MCP Request Method: {request.method}")
        logger.info(f"MCP Request Headers: {request.headers}")
        
        # Read and log the request body
        body = await request.body()
        logger.info(f"MCP Request Body: {body.decode('utf-8')}")
        
        # To allow the body to be read again by the actual endpoint,
        # we need to replace the stream.
        request.scope['stream'] = io.BytesIO(body)
        
        response = await call_next(request)
        return response

# Create and mount the MCP server with authentication
mcp_server = tools_server.streamable_http_app()
mcp_server.add_middleware(RequestLoggingMiddleware)
mcp_server.add_middleware(AuthMiddleware)
app.mount("/mcp", mcp_server)

def main():
    """Main entry point for the MCP server."""
    uvicorn.run(app, host="127.0.0.1", port=settings.PORT, log_level="debug")

if __name__ == "__main__":
    main()
