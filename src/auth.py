import json
import logging
import time
from typing import Dict, Optional
import httpx
from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import jwt
from jwt import PyJWKClient
from cryptography.hazmat.primitives import serialization

from .config import settings
from .tools import current_user_context, current_auth_token

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Security scheme for Bearer token
security = HTTPBearer()

# JWKS cache
JWKS_CACHE: Dict = {
    "keys": None,
    "fetched_at": 0,
    "client": None
}

class JWTValidationError(Exception):
    """Custom exception for JWT validation errors"""
    pass

async def get_jwks_keys() -> Dict:
    """
    Fetch JWKS keys from Django backend with caching
    """
    current_time = time.time()
    
    # Check if cache is still valid
    if (JWKS_CACHE["keys"] is not None and
        current_time - JWKS_CACHE["fetched_at"] < settings.JWKS_CACHE_TTL):
        return JWKS_CACHE["keys"]
    
    try:
        # Initialize PyJWKClient if not exists
        if JWKS_CACHE["client"] is None:
            JWKS_CACHE["client"] = PyJWKClient(settings.JWKS_URL)
        
        # Fetch fresh keys
        async with httpx.AsyncClient() as client:
            response = await client.get(settings.JWKS_URL, timeout=10.0)
            response.raise_for_status()
            jwks_data = response.json()
            
            JWKS_CACHE["keys"] = jwks_data
            JWKS_CACHE["fetched_at"] = current_time
            
            logger.info("JWKS keys refreshed successfully")
            return jwks_data
            
    except Exception as e:
        logger.error(f"Failed to fetch JWKS keys: {e}")
        # If we have cached keys, use them even if expired
        if JWKS_CACHE["keys"] is not None:
            logger.warning("Using expired JWKS cache due to fetch failure")
            return JWKS_CACHE["keys"]
        raise JWTValidationError(f"Failed to fetch JWKS keys: {e}")

async def validate_jwt_token(token: str) -> Dict:
    """
    Validate JWT token using Django's JWKS endpoint or public key
    Returns decoded token payload if valid
    """
    try:
        # Method 1: Use PyJWKClient for JWKS-based validation (preferred)
        if not settings.JWT_PUBLIC_KEY:
            if JWKS_CACHE["client"] is None:
                JWKS_CACHE["client"] = PyJWKClient(settings.JWKS_URL)
            
            # Get signing key from JWKS
            signing_key = JWKS_CACHE["client"].get_signing_key_from_jwt(token)
            
            # Decode and validate token
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=settings.JWT_AUDIENCE,
                issuer=settings.JWT_ISSUER,
                options={
                    "verify_exp": True,
                    "verify_aud": True,
                    "verify_iss": True,
                }
            )
        else:
            # Method 2: Use static public key (fallback)
            # Read public key from file for robustness
            from pathlib import Path
            BASE_DIR = Path(__file__).resolve().parent.parent.parent
            try:
                with open(BASE_DIR / 'jwt_public_key.pem', 'r') as f:
                    public_key_pem = f.read()
                public_key = serialization.load_pem_public_key(
                    public_key_pem.encode()
                )
            except (FileNotFoundError, ValueError) as e:
                logger.error(f"Failed to load public key from file: {e}")
                raise JWTValidationError(f"Server configuration error: Could not load public key.")

            payload = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                audience=settings.JWT_AUDIENCE,
                issuer=settings.JWT_ISSUER,
                options={
                    "verify_exp": True,
                    "verify_aud": True,
                    "verify_iss": True,
                }
            )
        
        # Log successful validation (without sensitive data)
        logger.info(f"JWT validated successfully for user_id: {payload.get('user_id', 'unknown')}")
        return payload
        
    except jwt.ExpiredSignatureError:
        raise JWTValidationError("Token has expired")
    except jwt.InvalidAudienceError:
        raise JWTValidationError("Invalid token audience")
    except jwt.InvalidIssuerError:
        raise JWTValidationError("Invalid token issuer")
    except jwt.InvalidTokenError as e:
        raise JWTValidationError(f"Invalid token: {str(e)}")
    except Exception as e:
        logger.error(f"JWT validation error: {e}")
        raise JWTValidationError(f"Token validation failed: {str(e)}")

# Authentication middleware
class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip authentication for public endpoints
        public_paths = [
            "/.well-known/",           # OAuth2 discovery endpoints
            "/oauth2/register",        # Dynamic client registration
            "/oauth2/authorize",       # Authorization endpoint (handles its own validation)
            "/oauth2/callback",        # OAuth callback endpoint
            "/oauth2/token",          # Token exchange endpoint
            "/oauth2/userinfo",       # User info endpoint (validates token internally)
            "/oauth2/introspect"      # Token introspection endpoint
        ]
        
        # Skip authentication for MCP discovery endpoints
        if request.url.path.startswith("/mcp//.well-known/"):
            return await call_next(request)
        
        # Check if the current path should skip authentication
        for path in public_paths:
            if request.url.path.startswith(path):
                return await call_next(request)

        try:
            # Extract Authorization header
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                raise HTTPException(
                    status_code=401,
                    detail="Missing or invalid authorization header"
                )

            token = auth_header.split(" ")[1]

            # Validate JWT token
            try:
                payload = await validate_jwt_token(token)
                
                # Attach user information to request state
                user_info = {
                    "id": payload.get("user_id"),
                    "email": payload.get("email"),
                    "username": payload.get("username"),
                    "token_type": payload.get("token_type"),
                    "exp": payload.get("exp"),
                    "iat": payload.get("iat"),
                    "jti": payload.get("jti"),
                }
                request.state.user = user_info
                
                # Set context variables for tools to access
                current_user_context.set(user_info)
                current_auth_token.set(token)
                
                logger.debug(f"User authenticated: {user_info['email']}")
                
            except JWTValidationError as e:
                logger.warning(f"JWT validation failed: {e}")
                raise HTTPException(status_code=401, detail=str(e))

        except HTTPException as e:
            # Return proper OAuth2 error response
            error_response = {
                "error": "invalid_token" if e.status_code == 401 else "insufficient_scope",
                "error_description": e.detail
            }
            
            headers = {
                "WWW-Authenticate": f'Bearer realm="cccrm-api"'
            }
            
            # Add resource metadata URL if configured
            if settings.RESOURCE_METADATA_URL:
                headers["WWW-Authenticate"] += f', resource_metadata="{settings.RESOURCE_METADATA_URL}"'
            
            return JSONResponse(
                status_code=e.status_code,
                content=error_response,
                headers=headers
            )

        return await call_next(request)