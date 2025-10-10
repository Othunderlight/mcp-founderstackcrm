import secrets
import time
import uuid
from typing import Dict, Optional
import httpx
from fastapi import FastAPI, HTTPException, Query, Request, Form
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel
import logging

from .config import settings

logger = logging.getLogger(__name__)

# In-memory storage for dynamic clients (in production, use Redis/Database)
DYNAMIC_CLIENTS: Dict[str, Dict] = {}
AUTHORIZATION_CODES: Dict[str, Dict] = {}

# OAuth2 Dynamic Client Registration Models
class ClientRegistrationRequest(BaseModel):
    client_name: str
    client_uri: Optional[str] = None
    redirect_uris: list[str]
    grant_types: Optional[list[str]] = ["authorization_code"]
    response_types: Optional[list[str]] = ["code"]
    scope: Optional[str] = "openid profile email"

class ClientRegistrationResponse(BaseModel):
    client_id: str
    client_secret: str
    client_name: str
    client_uri: Optional[str] = None
    redirect_uris: list[str]
    grant_types: list[str]
    response_types: list[str]
    scope: str
    client_id_issued_at: int
    client_secret_expires_at: int

def create_oauth2_router():
    """Create FastAPI router for OAuth2 endpoints"""
    from fastapi import APIRouter
    
    router = APIRouter()
    
    @router.post("/oauth2/register")
    async def dynamic_client_registration(registration: ClientRegistrationRequest) -> ClientRegistrationResponse:
        """
        OAuth2 Dynamic Client Registration endpoint.
        Allows MCP clients to register themselves and get client credentials.
        """
        try:
            # Generate client credentials
            client_id = f"mcp_client_{uuid.uuid4().hex[:16]}"
            client_secret = secrets.token_urlsafe(32)
            
            # Store client information
            client_data = {
                "client_id": client_id,
                "client_secret": client_secret,
                "client_name": registration.client_name,
                "client_uri": registration.client_uri,
                "redirect_uris": registration.redirect_uris,
                "grant_types": registration.grant_types or ["authorization_code"],
                "response_types": registration.response_types or ["code"],
                "scope": registration.scope or "openid profile email",
                "client_id_issued_at": int(time.time()),
                "client_secret_expires_at": 0,  # No expiration
                "created_at": time.time()
            }
            
            DYNAMIC_CLIENTS[client_id] = client_data
            
            logger.info(f"Registered new OAuth2 client: {client_id} ({registration.client_name})")
            
            return ClientRegistrationResponse(**client_data)
            
        except Exception as e:
            logger.error(f"Client registration failed: {e}")
            raise HTTPException(status_code=500, detail="Client registration failed")
    
    @router.get("/oauth2/authorize")
    async def authorization_endpoint(
        client_id: str = Query(...),
        redirect_uri: str = Query(...),
        response_type: str = Query(..., regex="^code$"),
        scope: str = Query(default="openid profile email"),
        state: Optional[str] = Query(None),
        code_challenge: Optional[str] = Query(None),
        code_challenge_method: Optional[str] = Query(None)
    ):
        """
        OAuth2 Authorization endpoint.
        Redirects users to Django's Google OAuth flow.
        """
        try:
            # Validate client
            client = DYNAMIC_CLIENTS.get(client_id)
            if not client:
                raise HTTPException(status_code=400, detail="Invalid client_id")
            
            # Validate redirect_uri
            if redirect_uri not in client["redirect_uris"]:
                raise HTTPException(status_code=400, detail="Invalid redirect_uri")
            
            # Generate state for CSRF protection if not provided
            if not state:
                state = secrets.token_urlsafe(16)
            
            # Store authorization request details
            auth_request_id = secrets.token_urlsafe(16)
            auth_request = {
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "scope": scope,
                "state": state,
                "code_challenge": code_challenge,
                "code_challenge_method": code_challenge_method,
                "created_at": time.time()
            }
            
            # Build Django OAuth URL with proper callback
            callback_params = f"auth_request_id={auth_request_id}"
            if state:
                callback_params += f"&state={state}"
            
            # Store auth request for callback
            AUTHORIZATION_CODES[auth_request_id] = auth_request
            
            # Django Google OAuth URL with MCP callback
            django_oauth_url = f"{settings.DJANGO_BASE_URL.rstrip('/')}/oauth/google/"
            django_callback_url = f"{settings.DJANGO_BASE_URL.rstrip('/')}/mcp/oauth2/callback/?mcp_callback_params={callback_params}"
            django_redirect_url = f"{django_oauth_url}?next={django_callback_url}"
            
            logger.info(f"Redirecting client {client_id} to Django OAuth: {django_redirect_url}")
            
            return RedirectResponse(url=django_redirect_url, status_code=302)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authorization endpoint error: {e}")
            raise HTTPException(status_code=500, detail="Authorization failed")
    
    @router.get("/oauth2/callback")
    async def oauth_callback(
        request: Request,
        auth_request_id: str = Query(...),
        state: Optional[str] = Query(None),
        django_user_id: Optional[int] = Query(None),
        django_user_email: Optional[str] = Query(None),
        error: Optional[str] = Query(None),
        error_description: Optional[str] = Query(None)
    ):
        """
        OAuth2 callback endpoint.
        Handles the callback from Django after Google OAuth completion.
        """
        try:
            # Handle OAuth errors
            if error:
                logger.error(f"OAuth error: {error} - {error_description}")
                return JSONResponse(
                    status_code=400,
                    content={"error": error, "error_description": error_description}
                )
            
            # Retrieve stored auth request
            auth_request = AUTHORIZATION_CODES.get(auth_request_id)
            if not auth_request:
                raise HTTPException(status_code=400, detail="Invalid authorization request")
            
            # Verify state parameter
            if state != auth_request.get("state"):
                raise HTTPException(status_code=400, detail="Invalid state parameter")
            
            # Validate user info from Django callback
            if not django_user_id or not django_user_email:
                raise HTTPException(status_code=400, detail="Missing user information from Django")
            
            # Create user info object
            user_info = {
                "id": django_user_id,
                "email": django_user_email,
                "username": django_user_email  # Use email as username fallback
            }
            
            # Generate authorization code
            auth_code = secrets.token_urlsafe(32)
            
            # Store authorization code with user info
            code_data = {
                "client_id": auth_request["client_id"],
                "redirect_uri": auth_request["redirect_uri"],
                "scope": auth_request["scope"],
                "user_info": user_info,
                "code_challenge": auth_request.get("code_challenge"),
                "code_challenge_method": auth_request.get("code_challenge_method"),
                "created_at": time.time(),
                "expires_at": time.time() + 600  # 10 minutes
            }
            
            AUTHORIZATION_CODES[auth_code] = code_data
            
            # Clean up auth request
            del AUTHORIZATION_CODES[auth_request_id]
            
            # Redirect back to client with authorization code
            redirect_url = f"{auth_request['redirect_uri']}?code={auth_code}&state={state}"
            
            logger.info(f"OAuth callback successful for client {auth_request['client_id']}, user: {django_user_email}")
            
            return RedirectResponse(url=redirect_url, status_code=302)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"OAuth callback error: {e}")
            raise HTTPException(status_code=500, detail="OAuth callback failed")
    
    @router.post("/oauth2/token")
    async def token_endpoint(
        grant_type: str = Form(...),
        client_id: str = Form(...),
        client_secret: str = Form(...),
        code: Optional[str] = Form(None),
        redirect_uri: Optional[str] = Form(None),
        code_verifier: Optional[str] = Form(None)
    ):
        """
        OAuth2 Token endpoint.
        Exchanges authorization codes for JWT access tokens.
        """
        try:
            # Validate client credentials
            client = DYNAMIC_CLIENTS.get(client_id)
            if not client or client["client_secret"] != client_secret:
                raise HTTPException(status_code=401, detail="Invalid client credentials")
            
            if grant_type == "authorization_code":
                if not code or not redirect_uri:
                    raise HTTPException(status_code=400, detail="Missing required parameters")
                
                # Validate authorization code
                code_data = AUTHORIZATION_CODES.get(code)
                if not code_data:
                    raise HTTPException(status_code=400, detail="Invalid authorization code")
                
                # Check expiration
                if time.time() > code_data["expires_at"]:
                    del AUTHORIZATION_CODES[code]
                    raise HTTPException(status_code=400, detail="Authorization code expired")
                
                # Validate redirect_uri
                if redirect_uri != code_data["redirect_uri"]:
                    raise HTTPException(status_code=400, detail="Invalid redirect_uri")
                
                # Validate PKCE if used
                if code_data.get("code_challenge"):
                    if not code_verifier:
                        raise HTTPException(status_code=400, detail="Missing code_verifier")
                    # In production, validate PKCE challenge
                
                # Request JWT tokens from Django
                jwt_tokens = await get_jwt_tokens_from_django(code_data["user_info"])
                
                # Clean up authorization code
                del AUTHORIZATION_CODES[code]
                
                response_data = {
                    "access_token": jwt_tokens["access_token"],
                    "token_type": "Bearer",
                    "expires_in": 3600,  # 1 hour
                    "scope": code_data["scope"]
                }
                
                if "refresh_token" in jwt_tokens:
                    response_data["refresh_token"] = jwt_tokens["refresh_token"]
                
                logger.info(f"Issued JWT tokens for client {client_id}")
                
                return JSONResponse(content=response_data)
            
            else:
                raise HTTPException(status_code=400, detail="Unsupported grant type")
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Token endpoint error: {e}")
            raise HTTPException(status_code=500, detail="Token issuance failed")
    
    return router

async def get_user_from_django_session(session_id: str) -> Optional[Dict]:
    """Get user information from Django session"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.DJANGO_BASE_URL.rstrip('/')}/api/mcp/user/",
                cookies={"sessionid": session_id},
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("user")
            else:
                logger.error(f"Failed to get user from Django session: {response.status_code}")
                return None
                
    except Exception as e:
        logger.error(f"Error getting user from Django: {e}")
        return None

async def get_jwt_tokens_from_django(user_info: Dict) -> Dict:
    """Get JWT tokens from Django for the authenticated user"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.DJANGO_BASE_URL.rstrip('/')}/api/mcp/jwt/",
                json={
                    "user_id": user_info["id"],
                    "email": user_info["email"]
                },
                headers={"Content-Type": "application/json"},
                timeout=10.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get JWT tokens from Django: {response.status_code} - {response.text}")
                raise Exception("Failed to get JWT tokens")
                
    except Exception as e:
        logger.error(f"Error getting JWT tokens from Django: {e}")
        raise Exception("Failed to get JWT tokens")

def get_oauth2_metadata() -> Dict:
    """Generate OAuth2 metadata for discovery"""
    base_url = f"http://localhost:{settings.PORT}"
    
    return {
        "issuer": base_url,
        "authorization_endpoint": f"{base_url}/oauth2/authorize",
        "token_endpoint": f"{base_url}/oauth2/token",
        "registration_endpoint": f"{base_url}/oauth2/register",
        "jwks_uri": settings.JWKS_URL,
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code"],
        "token_endpoint_auth_methods_supported": ["client_secret_post"],
        "scopes_supported": ["openid", "profile", "email"],
        "code_challenge_methods_supported": ["S256", "plain"],
        "subject_types_supported": ["public"]
    }