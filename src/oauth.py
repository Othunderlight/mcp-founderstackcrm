"""
Simplified OAuth2 Authorization Server for MCP.

No database — uses in-memory dicts with TTL-based expiry.
Redirects to the React frontend for login, then passes through Django JWTs.
"""

import secrets
import time
import uuid
import asyncio
import logging
from typing import Dict, Optional
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Query, Request, Form
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel

from .config import settings

logger = logging.getLogger(__name__)

# ── In-memory stores (TTL-based, cleaned periodically) ───────────────────

# Registered OAuth2 clients: { client_id: { client_secret, client_name, redirect_uris, ... } }
registered_clients: Dict[str, Dict] = {}

# Pending authorization requests: { auth_id: { client_id, redirect_uri, state, scope, created_at } }
pending_auth_requests: Dict[str, Dict] = {}

# Issued authorization codes: { code: { token, client_id, redirect_uri, created_at } }
auth_codes: Dict[str, Dict] = {}

# TTL constants (seconds)
AUTH_REQUEST_TTL = 600  # 10 minutes
AUTH_CODE_TTL = 300  # 5 minutes
CLIENT_TTL = 86400 * 30  # 30 days


async def cleanup_expired():
    """Background task to clean up expired entries."""
    while True:
        now = time.time()

        expired_requests = [
            k
            for k, v in pending_auth_requests.items()
            if now - v["created_at"] > AUTH_REQUEST_TTL
        ]
        for k in expired_requests:
            del pending_auth_requests[k]

        expired_codes = [
            k for k, v in auth_codes.items() if now - v["created_at"] > AUTH_CODE_TTL
        ]
        for k in expired_codes:
            del auth_codes[k]

        if expired_requests or expired_codes:
            logger.info(
                f"Cleanup: removed {len(expired_requests)} expired requests, "
                f"{len(expired_codes)} expired codes"
            )

        await asyncio.sleep(60)  # Run every minute


# ── Pydantic models ─────────────────────────────────────────────────────


class ClientRegistrationRequest(BaseModel):
    client_name: str
    redirect_uris: list[str]
    client_uri: Optional[str] = None
    grant_types: Optional[list[str]] = ["authorization_code"]
    response_types: Optional[list[str]] = ["code"]
    scope: Optional[str] = "openid profile email"


class ClientRegistrationResponse(BaseModel):
    client_id: str
    client_secret: str
    client_name: str
    redirect_uris: list[str]
    grant_types: list[str]
    response_types: list[str]
    scope: str
    client_id_issued_at: int
    client_secret_expires_at: int


# ── Router ───────────────────────────────────────────────────────────────


def create_oauth2_router() -> APIRouter:
    router = APIRouter()

    # ── Dynamic Client Registration ──────────────────────────────────

    @router.post("/oauth2/register")
    async def register_client(
        req: ClientRegistrationRequest,
    ) -> ClientRegistrationResponse:
        """Register an MCP client dynamically."""
        client_id = f"mcp_{uuid.uuid4().hex[:16]}"
        client_secret = secrets.token_urlsafe(32)
        now = int(time.time())

        registered_clients[client_id] = {
            "client_secret": client_secret,
            "client_name": req.client_name,
            "client_uri": req.client_uri,
            "redirect_uris": req.redirect_uris,
            "grant_types": req.grant_types or ["authorization_code"],
            "response_types": req.response_types or ["code"],
            "scope": req.scope or "openid profile email",
            "created_at": now,
        }

        logger.info(f"Registered client: {client_id} ({req.client_name})")

        return ClientRegistrationResponse(
            client_id=client_id,
            client_secret=client_secret,
            client_name=req.client_name,
            redirect_uris=req.redirect_uris,
            grant_types=req.grant_types or ["authorization_code"],
            response_types=req.response_types or ["code"],
            scope=req.scope or "openid profile email",
            client_id_issued_at=now,
            client_secret_expires_at=0,
        )

    # ── Authorization Endpoint ───────────────────────────────────────

    @router.get("/oauth2/authorize")
    async def authorize(
        client_id: str = Query(...),
        redirect_uri: str = Query(...),
        response_type: str = Query(...),
        scope: str = Query(default="openid profile email"),
        state: Optional[str] = Query(None),
        code_challenge: Optional[str] = Query(None),
        code_challenge_method: Optional[str] = Query(None),
    ):
        """
        OAuth2 authorize — redirects to the React frontend for login.
        """
        # Auto-register unknown clients (for dev tools like MCP Inspector)
        if client_id not in registered_clients:
            if client_id.startswith("mcp_"):
                registered_clients[client_id] = {
                    "client_secret": "",
                    "client_name": "MCP Client",
                    "redirect_uris": [redirect_uri],
                    "grant_types": ["authorization_code"],
                    "response_types": ["code"],
                    "scope": scope,
                    "created_at": int(time.time()),
                }
                logger.info(f"Auto-registered client: {client_id}")
            else:
                raise HTTPException(status_code=400, detail="Unknown client_id")

        client = registered_clients[client_id]

        # Validate redirect_uri (lenient for localhost/dev)
        valid = any(
            redirect_uri.rstrip("/") == allowed.rstrip("/")
            for allowed in client["redirect_uris"]
        )
        if not valid and redirect_uri.startswith(
            ("http://127.0.0.1:", "http://localhost:", "vscode://")
        ):
            valid = True
            logger.info(f"Allowing dev redirect_uri: {redirect_uri}")

        if not valid:
            raise HTTPException(status_code=400, detail="Invalid redirect_uri")

        if not state:
            state = secrets.token_urlsafe(16)

        # Store pending auth request
        auth_id = secrets.token_urlsafe(16)
        pending_auth_requests[auth_id] = {
            "client_id": client_id,
            "client_name": client.get("client_name", "MCP Client"),
            "redirect_uri": redirect_uri,
            "scope": scope,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": code_challenge_method,
            "created_at": time.time(),
        }

        # Build frontend redirect URL
        mcp_server_url = settings.MCP_PUBLIC_BASE_URL
        frontend_params = urlencode(
            {
                "auth_id": auth_id,
                "state": state,
                "client_name": client.get("client_name", "MCP Client"),
                "callback_url": f"{mcp_server_url}/oauth2/callback",
            }
        )
        frontend_url = f"{settings.FRONTEND_URL}/#/mcp/connect?{frontend_params}"

        logger.info(f"Redirecting to frontend for auth: {frontend_url}")
        return RedirectResponse(url=frontend_url, status_code=302)

    # ── Callback (from frontend after login) ─────────────────────────

    @router.get("/oauth2/callback")
    async def callback(
        auth_id: str = Query(...),
        token: str = Query(...),
        state: Optional[str] = Query(None),
    ):
        """
        Receives the JWT from the frontend after successful login.
        Generates an auth code and redirects back to the MCP client.
        """
        auth_request = pending_auth_requests.pop(auth_id, None)
        if not auth_request:
            raise HTTPException(
                status_code=400, detail="Invalid or expired auth request"
            )

        if state and state != auth_request["state"]:
            raise HTTPException(status_code=400, detail="State mismatch")

        # Generate auth code and store the JWT
        code = secrets.token_urlsafe(32)
        auth_codes[code] = {
            "token": token,
            "client_id": auth_request["client_id"],
            "redirect_uri": auth_request["redirect_uri"],
            "created_at": time.time(),
        }

        # Redirect back to MCP client with auth code
        redirect_params = urlencode(
            {
                "code": code,
                "state": auth_request["state"],
            }
        )
        redirect_url = f"{auth_request['redirect_uri']}?{redirect_params}"

        logger.info(f"Auth callback successful, redirecting to client: {redirect_url}")
        return RedirectResponse(url=redirect_url, status_code=302)

    # ── Token Exchange ───────────────────────────────────────────────

    @router.post("/oauth2/token")
    async def token_exchange(
        grant_type: str = Form(...),
        code: Optional[str] = Form(None),
        redirect_uri: Optional[str] = Form(None),
        client_id: Optional[str] = Form(None),
        client_secret: Optional[str] = Form(None),
        code_verifier: Optional[str] = Form(None),
    ):
        """
        Exchange authorization code for the JWT access token.
        This is a pass-through — returns the Django JWT stored during callback.
        """
        if grant_type != "authorization_code":
            raise HTTPException(status_code=400, detail="Unsupported grant_type")

        if not code:
            raise HTTPException(status_code=400, detail="Missing authorization code")

        code_data = auth_codes.pop(code, None)
        if not code_data:
            raise HTTPException(
                status_code=400, detail="Invalid or expired authorization code"
            )

        if time.time() - code_data["created_at"] > AUTH_CODE_TTL:
            raise HTTPException(status_code=400, detail="Authorization code expired")

        if redirect_uri and redirect_uri != code_data["redirect_uri"]:
            raise HTTPException(status_code=400, detail="redirect_uri mismatch")

        logger.info(f"Token exchange successful for client: {code_data['client_id']}")

        return JSONResponse(
            content={
                "access_token": code_data["token"],
                "token_type": "Bearer",
                "scope": "openid profile email",
            }
        )

    return router


# ── OAuth2 Metadata ─────────────────────────────────────────────────────


def get_oauth2_metadata() -> Dict:
    """OAuth2 Authorization Server Metadata."""
    base_url = settings.MCP_PUBLIC_BASE_URL

    return {
        "issuer": base_url,
        "authorization_endpoint": f"{base_url}/oauth2/authorize",
        "token_endpoint": f"{base_url}/oauth2/token",
        "registration_endpoint": f"{base_url}/oauth2/register",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code"],
        "token_endpoint_auth_methods_supported": ["client_secret_post", "none"],
        "code_challenge_methods_supported": ["S256", "plain"],
        "scopes_supported": ["openid", "profile", "email"],
    }
