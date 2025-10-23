import secrets
import time
import uuid
import json
from typing import Dict, Optional
import httpx
from fastapi import FastAPI, HTTPException, Query, Request, Form
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel
import logging

from .config import settings
from . import database as db

logger = logging.getLogger(__name__)

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
            client_id = f"mcp_client_{uuid.uuid4().hex[:16]}"
            client_secret = secrets.token_urlsafe(32)
            
            client_data = {
                "client_id": client_id,
                "client_secret": client_secret,
                "client_name": registration.client_name,
                "client_uri": registration.client_uri,
                "redirect_uris": json.dumps(registration.redirect_uris),
                "grant_types": json.dumps(registration.grant_types or ["authorization_code"]),
                "response_types": json.dumps(registration.response_types or ["code"]),
                "scope": registration.scope or "openid profile email",
                "client_id_issued_at": int(time.time()),
                "client_secret_expires_at": 0,  # No expiration
                "created_at": time.time()
            }
            
            conn = db.get_db_connection()
            conn.execute(
                "INSERT INTO oauth_clients (client_id, client_secret, client_name, client_uri, redirect_uris, grant_types, response_types, scope, client_id_issued_at, client_secret_expires_at, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                list(client_data.values())
            )
            conn.commit()
            conn.close()
            
            logger.info(f"Registered new OAuth2 client: {client_id} ({registration.client_name})")
            
            client_data['redirect_uris'] = registration.redirect_uris
            client_data['grant_types'] = registration.grant_types or ["authorization_code"]
            client_data['response_types'] = registration.response_types or ["code"]

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
            conn = db.get_db_connection()
            client_row = conn.execute("SELECT * FROM oauth_clients WHERE client_id = ?", (client_id,)).fetchone()
            conn.close()
            client = db.dict_to_client(client_row)

            if not client:
                if client_id.startswith("mcp_client_"):
                    client = {
                        "client_id": client_id,
                        "client_secret": "dummy_secret",
                        "client_name": "MCP Inspector",
                        "client_uri": "",
                        "redirect_uris": ["http://localhost:6274/oauth/callback/debug"],
                        "grant_types": ["authorization_code"],
                        "response_types": ["code"],
                        "scope": "openid profile email",
                        "client_id_issued_at": int(time.time()),
                        "client_secret_expires_at": 0,
                        "created_at": time.time()
                    }
                    conn = db.get_db_connection()
                    conn.execute(
                        "INSERT INTO oauth_clients (client_id, client_secret, client_name, client_uri, redirect_uris, grant_types, response_types, scope, client_id_issued_at, client_secret_expires_at, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (client['client_id'], client['client_secret'], client['client_name'], client['client_uri'], json.dumps(client['redirect_uris']), json.dumps(client['grant_types']), json.dumps(client['response_types']), client['scope'], client['client_id_issued_at'], client['client_secret_expires_at'], client['created_at'])
                    )
                    conn.commit()
                    conn.close()
                    logger.info(f"Created default MCP client: {client_id}")
                else:
                    logger.error(f"Authorization attempt with unknown client_id: {client_id}")
                    raise HTTPException(status_code=400, detail="Invalid client_id")
            
            valid_redirect = False
            for allowed_uri in client["redirect_uris"]:
                if (redirect_uri == allowed_uri or
                    redirect_uri.rstrip('/') == allowed_uri.rstrip('/') or
                    redirect_uri.rstrip('/') == allowed_uri):
                    valid_redirect = True
                    break

            if not valid_redirect:
                logger.warning(f"Redirect URI {redirect_uri} not in allowed list {client['redirect_uris']}, allowing for development")
                if redirect_uri.startswith(('http://127.0.0.1:', 'http://localhost:', 'vscode://')):
                    logger.info(f"Allowing 127.0.0.1/VSCode redirect_uri for development: {redirect_uri}")
                    valid_redirect = True
                else:
                    logger.error(f"Invalid redirect_uri: {redirect_uri}, allowed: {client['redirect_uris']}")
                    raise HTTPException(status_code=400, detail="Invalid redirect_uri")
            
            if not state:
                state = secrets.token_urlsafe(16)
            
            auth_request_id = secrets.token_urlsafe(16)
            auth_request = {
                "code": auth_request_id,
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "scope": scope,
                "user_info": json.dumps({"state": state}), # Store state here
                "code_challenge": code_challenge,
                "code_challenge_method": code_challenge_method,
                "created_at": time.time(),
                "expires_at": time.time() + 600
            }
            
            conn = db.get_db_connection()
            conn.execute(
                "INSERT INTO oauth_codes (code, client_id, redirect_uri, scope, user_info, code_challenge, code_challenge_method, created_at, expires_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                list(auth_request.values())
            )
            conn.commit()
            conn.close()

            django_bridge_url = f"{settings.DJANGO_BASE_URL.rstrip('/')}/mcp/google-login/"
            django_redirect_url = f"{django_bridge_url}?auth_request_id={auth_request_id}&state={state}"

            logger.info(f"Redirecting client {client_id} to Django bridge for OAuth: {django_redirect_url}")
            
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
            conn = db.get_db_connection()
            auth_request_row = conn.execute("SELECT * FROM oauth_codes WHERE code = ?", (auth_request_id,)).fetchone()
            conn.close()
            auth_request = db.dict_to_code(auth_request_row)

            if not auth_request:
                raise HTTPException(status_code=400, detail="Invalid authorization request")

            original_state = auth_request.get("user_info", {}).get("state")

            if error:
                logger.error(f"OAuth error from Django: {error} - {error_description}")
                from urllib.parse import urlencode
                error_params = {"error": error, "error_description": error_description}
                if original_state:
                    error_params["state"] = original_state
                
                redirect_url = f"{auth_request['redirect_uri']}?{urlencode(error_params)}"
                return RedirectResponse(url=redirect_url)

            if state != original_state:
                raise HTTPException(status_code=400, detail="Invalid state parameter")
            
            if not django_user_id or not django_user_email:
                raise HTTPException(status_code=400, detail="Missing user information from Django")
            
            user_info = {
                "id": django_user_id,
                "email": django_user_email,
                "username": django_user_email
            }
            
            auth_code = secrets.token_urlsafe(32)
            
            code_data = {
                "code": auth_code,
                "client_id": auth_request["client_id"],
                "redirect_uri": auth_request["redirect_uri"],
                "scope": auth_request["scope"],
                "user_info": json.dumps(user_info),
                "code_challenge": auth_request.get("code_challenge"),
                "code_challenge_method": auth_request.get("code_challenge_method"),
                "created_at": time.time(),
                "expires_at": time.time() + 600
            }
            
            conn = db.get_db_connection()
            conn.execute("DELETE FROM oauth_codes WHERE code = ?", (auth_request_id,))
            conn.execute(
                "INSERT INTO oauth_codes (code, client_id, redirect_uri, scope, user_info, code_challenge, code_challenge_method, created_at, expires_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                list(code_data.values())
            )
            conn.commit()
            conn.close()
            
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
        request: Request,
        grant_type: str = Form(...),
        client_id: Optional[str] = Form(None),
        client_secret: Optional[str] = Form(None),
        code: Optional[str] = Form(None),
        redirect_uri: Optional[str] = Form(None),
        code_verifier: Optional[str] = Form(None)
    ):
        """
        OAuth2 Token endpoint.
        Exchanges authorization codes for JWT access tokens.
        """
        try:
            logger.info(f"Token request - grant_type: {grant_type}, client_id: {client_id}, code: {code}")
            
            conn = db.get_db_connection()

            if not client_id and code:
                code_row = conn.execute("SELECT * FROM oauth_codes WHERE code = ?", (code,)).fetchone()
                if code_row:
                    client_id = db.dict_to_code(code_row).get("client_id")
                    logger.info(f"Extracted client_id from authorization code: {client_id}")

            if not client_id:
                conn.close()
                raise HTTPException(status_code=400, detail="Missing client_id")
            
            client_row = conn.execute("SELECT * FROM oauth_clients WHERE client_id = ?", (client_id,)).fetchone()
            client = db.dict_to_client(client_row)

            if not client:
                conn.close()
                logger.error(f"Token request with unknown client_id: {client_id}")
                raise HTTPException(status_code=401, detail="Invalid client credentials")

            if client_id.startswith("mcp_client_"):
                pass
            elif client.get("client_secret") and client_secret and client["client_secret"] != client_secret:
                conn.close()
                logger.error(f"Invalid client_secret for client: {client_id}")
                raise HTTPException(status_code=401, detail="Invalid client credentials")
            elif client.get("client_secret") and not client_secret:
                logger.warning(f"Missing client_secret for pre-registered client: {client_id}")
                pass
            
            if grant_type == "authorization_code":
                if not code or not redirect_uri:
                    conn.close()
                    raise HTTPException(status_code=400, detail="Missing required parameters")
                
                code_row = conn.execute("SELECT * FROM oauth_codes WHERE code = ?", (code,)).fetchone()
                code_data = db.dict_to_code(code_row)

                if not code_data:
                    conn.close()
                    raise HTTPException(status_code=400, detail="Invalid authorization code")
                
                if time.time() > code_data["expires_at"]:
                    conn.execute("DELETE FROM oauth_codes WHERE code = ?", (code,))
                    conn.commit()
                    conn.close()
                    raise HTTPException(status_code=400, detail="Authorization code expired")
                
                if redirect_uri != code_data["redirect_uri"]:
                    conn.close()
                    raise HTTPException(status_code=400, detail="Invalid redirect_uri")
                
                if code_data.get("code_challenge"):
                    if not code_verifier:
                        conn.close()
                        raise HTTPException(status_code=400, detail="Missing code_verifier")
                
                jwt_tokens = await get_jwt_tokens_from_django(code_data["user_info"])
                
                conn.execute("DELETE FROM oauth_codes WHERE code = ?", (code,))
                conn.commit()
                conn.close()
                
                response_data = {
                    "access_token": jwt_tokens["access_token"],
                    "token_type": "Bearer",
                    "expires_in": 3600,
                    "scope": code_data["scope"]
                }
                
                if "refresh_token" in jwt_tokens:
                    response_data["refresh_token"] = jwt_tokens["refresh_token"]
                
                logger.info(f"Issued JWT tokens for client {client_id}")
                
                return JSONResponse(content=response_data)
            
            else:
                conn.close()
                raise HTTPException(status_code=400, detail="Unsupported grant type")
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Token endpoint error: {e}")
            raise HTTPException(status_code=500, detail="Token issuance failed")
    
    @router.get("/oauth2/userinfo")
    async def userinfo_endpoint(request: Request):
        """
        OAuth2 UserInfo endpoint.
        Returns information about the authenticated user.
        """
        try:
            # Extract Authorization header
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

            # For now, return basic user info
            # In a full implementation, you'd validate the token and return actual user data
            return {
                "sub": "user123",
                "email": "user@example.com",
                "email_verified": True,
                "name": "MCP User",
                "given_name": "MCP",
                "family_name": "User",
                "picture": "https://example.com/avatar.jpg"
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"UserInfo endpoint error: {e}")
            raise HTTPException(status_code=500, detail="UserInfo failed")

    @router.post("/oauth2/introspect")
    async def introspect_endpoint(token: str = Form(...)):
        """
        OAuth2 Token Introspection endpoint.
        Validates and returns information about a token.
        """
        try:
            # In a full implementation, validate the token here
            return {
                "active": True,
                "client_id": "mcp_client",
                "username": "user@example.com",
                "scope": "openid profile email",
                "exp": int(time.time()) + 3600,
                "iat": int(time.time()),
                "sub": "user123"
            }
        except Exception as e:
            logger.error(f"Introspection endpoint error: {e}")
            raise HTTPException(status_code=500, detail="Introspection failed")
    
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
    base_url = f"http://127.0.0.1:{settings.PORT}"
    
    return {
        "issuer": base_url,
        "authorization_endpoint": f"{base_url}/oauth2/authorize",
        "token_endpoint": f"{base_url}/oauth2/token",
        "registration_endpoint": f"{base_url}/oauth2/register",
        "jwks_uri": settings.JWKS_URL,
        
        # Dynamic Client Registration Support
        "registration_endpoint_auth_methods_supported": ["none"],
        "registration_endpoint_auth_signing_alg_values_supported": [],
        
        # Supported OAuth2 flows
        "response_types_supported": ["code"],
        "response_modes_supported": ["query", "fragment"],
        "grant_types_supported": ["authorization_code"],
        "token_endpoint_auth_methods_supported": ["client_secret_post", "client_secret_basic"],
        
        # PKCE Support
        "code_challenge_methods_supported": ["S256", "plain"],
        
        # Scopes and Claims
        "scopes_supported": ["openid", "profile", "email"],
        "claims_supported": ["sub", "email", "email_verified", "name", "given_name", "family_name", "picture"],
        "subject_types_supported": ["public"],
        
        # Client Registration
        "client_registration_types_supported": ["automatic"],
        "client_registration_endpoint_auth_methods_supported": ["none"],
        
        # Additional OAuth2 Discovery fields
        "userinfo_endpoint": f"{base_url}/oauth2/userinfo",
        "end_session_endpoint": f"{base_url}/oauth2/logout",
        "introspection_endpoint": f"{base_url}/oauth2/introspect",
        "revocation_endpoint": f"{base_url}/oauth2/revoke",
        
        # Algorithm support
        "id_token_signing_alg_values_supported": ["RS256"],
        "token_endpoint_auth_signing_alg_values_supported": ["RS256"],
        
        # Additional capabilities
        "request_parameter_supported": True,
        "request_uri_parameter_supported": False,
        "require_request_uri_registration": False,
        "claims_parameter_supported": False,
        
        # MCP-specific metadata
        "mcp_dynamic_registration_supported": True,
        "mcp_version": "1.0"
    }