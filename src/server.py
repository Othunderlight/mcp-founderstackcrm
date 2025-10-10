
import contextlib
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .auth import AuthMiddleware
from .config import settings
from .tools import mcp as tools_server
from .oauth import create_oauth2_router, get_oauth2_metadata
import json

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
        base_url = f"http://localhost:{settings.PORT}"
        return {
            "resource_server_metadata": {
                "resource_identifier": "cccrm-api",
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

# Create and mount the MCP server with authentication
mcp_server = tools_server.streamable_http_app()
app.add_middleware(AuthMiddleware)
app.mount("/", mcp_server)

def main():
    """Main entry point for the MCP server."""
    uvicorn.run(app, host="localhost", port=settings.PORT, log_level="debug")

if __name__ == "__main__":
    main()
