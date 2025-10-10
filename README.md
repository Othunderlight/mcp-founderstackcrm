# MCP Server with Django JWT Authentication & OAuth2

This is a FastAPI-based MCP (Model Context Protocol) server that provides secure authentication using JWT tokens from a Django backend with Allauth and SimpleJWT. It supports **OAuth2 Dynamic Client Registration** with automatic Google OAuth flow.

## Architecture

```
┌───────────────┐    OAuth2   ┌───────────────┐   Google   ┌───────────────┐         ┌───────────────┐
│ MCP Client    │────────────▶│ MCP Server    │───────────▶│ Django Backend│────────▶│ Google OAuth  │
│ (e.g. GPT)    │ Register+   │ (FastAPI)     │ Redirect   │ (Allauth+DRF) │ OAuth   │ Provider      │
│               │ Authorize   │               │            │               │         │               │
└───────────────┘             └───────────────┘            └───────────────┘         └───────────────┘
        │                             │                             │                         │
        │         JWT Access Token    │      JWT Token Exchange     │    User Info + Session │
        └─────────────────────────────┼─────────────────────────────┼─────────────────────────┘
                                      │                             │
                                      └─────────────────────────────┘
                                             API Calls with JWT
```

## Features

- **OAuth2 Dynamic Client Registration**: Automatic client registration for MCP clients
- **Google OAuth Integration**: Seamless authentication via Django's Google OAuth flow
- **JWT Authentication**: Validates tokens issued by Django backend using RS256
- **JWKS Support**: Automatically fetches and caches public keys from Django's JWKS endpoint
- **User Context**: Attaches authenticated user information to requests
- **MCP Tools**: Provides authenticated access to Django backend APIs
- **Caching**: Efficient JWKS key caching with configurable TTL
- **Error Handling**: Proper OAuth2 error responses
- **Standards Compliant**: Full OAuth2 authorization code flow with PKCE support

## Setup

### 1. Install Dependencies

```bash
cd mcp-auth-test
pip install -e .
# or using uv
uv pip install -e .
```

### 2. Configure Environment

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` with your Django backend configuration:

```env
# Django Backend Configuration
DJANGO_BASE_URL=http://localhost:8000

# JWT Configuration (these should match your Django settings)
JWT_AUDIENCE=cccrm-api
JWT_ISSUER=cccrm-backend

# Optional: Provide static public key (otherwise JWKS will be used)
# JWT_PUBLIC_KEY=-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----

# Server Configuration
PORT=10000

# Optional: Tavily API for web search tool
TAVILY_API_KEY=your-tavily-api-key
```

### 3. Django Backend Setup

Ensure your Django backend has the following configuration in `settings.py`:

```python
# JWT Configuration
SIMPLE_JWT = {
    'ALGORITHM': 'RS256',
    'SIGNING_KEY': env('JWT_PRIVATE_KEY'),
    'VERIFYING_KEY': env('JWT_PUBLIC_KEY'),
    'AUDIENCE': env('JWT_AUDIENCE', default='cccrm-api'),
    'ISSUER': env('JWT_ISSUER', default='cccrm-backend'),
    # ... other settings
}

# Expose JWKS endpoint
# Add this URL pattern to expose /.well-known/jwks.json
```

### 4. Generate JWT Keys (if needed)

If you need to generate RS256 key pairs for your Django backend:

```python
# generate_jwt_keys.py
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

# Generate private key
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048
)

# Get public key
public_key = private_key.public_key()


## OAuth2 Dynamic Client Registration

The MCP server supports OAuth2 Dynamic Client Registration, allowing clients to automatically register and authenticate users via Google OAuth through Django.

### OAuth2 Flow

```
1. Client Registration
   MCP Client ──────────POST /oauth2/register──────────▶ MCP Server
                                                           │
                                                           ▼
                                                      Generate client_id/secret
                                                           │
                                                           ▼
   MCP Client ◀──────────client_id + client_secret───────┘

2. Authorization Request  
   MCP Client ──────────GET /oauth2/authorize─────────▶ MCP Server
                                                           │
                                                           ▼
                                                      Redirect to Django
                                                           │
                                                           ▼
   User Browser ────────/oauth/google/?next=callback──▶ Django Backend
                                                           │
                                                           ▼
                                                      Google OAuth
                                                           │
                                                           ▼
   User Browser ◀──────────Google Login Page──────────── Google
                                                           │
                                                           ▼
                                                      User authenticates
                                                           │
                                                           ▼
   User Browser ─────────Callback with auth code──────▶ Django Backend
                                                           │
                                                           ▼
                                                      Django callback
                                                           │
                                                           ▼
   User Browser ─────────Redirect to MCP callback─────▶ MCP Server
                                                           │
                                                           ▼
                                                      Generate auth code
                                                           │
                                                           ▼
   MCP Client ◀─────────Authorization code─────────────── MCP Server

3. Token Exchange
   MCP Client ──────────POST /oauth2/token────────────▶ MCP Server
                           (auth code + client creds)      │
                                                           ▼
                                                      Call Django for JWT
                                                           │
                                                           ▼
   MCP Client ◀─────────JWT Access Token──────────────── MCP Server
```

### OAuth2 Endpoints

#### 1. Dynamic Client Registration

```http
POST /oauth2/register
Content-Type: application/json

{
  "client_name": "My MCP Client",
  "client_uri": "https://example.com",
  "redirect_uris": ["https://example.com/callback"],
  "grant_types": ["authorization_code"],
  "response_types": ["code"],
  "scope": "openid profile email"
}
```

**Response:**
```json
{
  "client_id": "mcp_client_abc123...",
  "client_secret": "secret_xyz789...",
  "client_name": "My MCP Client",
  "redirect_uris": ["https://example.com/callback"],
  "grant_types": ["authorization_code"],
  "response_types": ["code"],
  "scope": "openid profile email",
  "client_id_issued_at": 1699123456,
  "client_secret_expires_at": 0
}
```

#### 2. Authorization Request

```http
GET /oauth2/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope=openid%20profile%20email&state={state}&code_challenge={challenge}&code_challenge_method=S256
```

This will redirect the user to:
```
Django: /oauth/google/?next=/mcp/oauth2/callback/?mcp_callback_params=...
```

#### 3. Token Exchange

```http
POST /oauth2/token
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&
client_id={client_id}&
client_secret={client_secret}&
code={authorization_code}&
redirect_uri={redirect_uri}&
code_verifier={verifier}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "openid profile email",
  "refresh_token": "refresh_token_here..."
}
```

### OAuth2 Discovery

#### Authorization Server Metadata

```http
GET /.well-known/oauth-authorization-server
```

**Response:**
```json
{
  "issuer": "http://localhost:10000",
  "authorization_endpoint": "http://localhost:10000/oauth2/authorize",
  "token_endpoint": "http://localhost:10000/oauth2/token",
  "registration_endpoint": "http://localhost:10000/oauth2/register",
  "jwks_uri": "http://localhost:8000/auth/.well-known/jwks.json",
  "response_types_supported": ["code"],
  "grant_types_supported": ["authorization_code"],
  "token_endpoint_auth_methods_supported": ["client_secret_post"],
  "scopes_supported": ["openid", "profile", "email"],
  "code_challenge_methods_supported": ["S256", "plain"],
  "subject_types_supported": ["public"]
}
```

#### Resource Server Metadata

```http
GET /.well-known/oauth-protected-resource/mcp
```

**Response:**
```json
{
  "resource_server_metadata": {
    "resource_identifier": "cccrm-api",
    "authorization_servers": ["http://localhost:10000"],
    "authorization_server_metadata_url": "http://localhost:10000/.well-known/oauth-authorization-server",
    "jwks_uri": "http://localhost:8000/auth/.well-known/jwks.json",
    "audience": "cccrm-api",
    "issuer": "cccrm-backend",
    "oauth2_dynamic_registration": true,
    "registration_endpoint": "http://localhost:10000/oauth2/register"
  }
}
```

# Serialize private key
private_pem = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
).decode()

# Serialize public key
public_pem = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
).decode()

print("Private Key:")
print(private_pem)
print("\nPublic Key:")
print(public_pem)
```

## Running the Server

```bash
# Using the entry point
mcp-server

# Or directly
python -m src.server

# Or with uvicorn
uvicorn src.server:app --host localhost --port 10000 --reload
```

## Authentication Flow

### 1. User Authentication

Users first authenticate with your Django backend:

```bash
# Login to get JWT token
curl -X POST http://localhost:8000/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9...",
  "refresh_token": "...",
  "user": {
    "id": 1,
    "email": "user@example.com"
  }
}
```

### 2. MCP Client Connection

MCP clients connect to the server with the JWT token:

```bash
# Example MCP request
curl -X POST http://localhost:10000/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "get_user_profile",
      "arguments": {}
    }
  }'
```

## Available Tools

### 1. `get_user_profile`
Get the current authenticated user's profile information.

```json
{
  "method": "tools/call",
  "params": {
    "name": "get_user_profile",
    "arguments": {}
  }
}
```

### 2. `list_campaigns`
List all campaigns for the authenticated user.

```json
{
  "method": "tools/call",
  "params": {
    "name": "list_campaigns",
    "arguments": {}
  }
}
```

### 3. `create_campaign`
Create a new campaign for the authenticated user.

```json
{
  "method": "tools/call",
  "params": {
    "name": "create_campaign",
    "arguments": {
      "name": "My New Campaign",
      "description": "Campaign description"
    }
  }
}
```

### 4. `get_leads_count`
Get the total number of leads for the authenticated user.

```json
{
  "method": "tools/call",
  "params": {
    "name": "get_leads_count",
    "arguments": {}
  }
}
```

### 5. `search_web` (Optional)
Search the web using Tavily API (requires TAVILY_API_KEY).

```json
{
  "method": "tools/call",
  "params": {
    "name": "search_web",
    "arguments": {
      "query": "latest news about AI"
    }
  }
}
```

### 6. `add_numbers`
Simple demo tool for adding two numbers.

```json
{
  "method": "tools/call",
  "params": {
    "name": "add_numbers",
    "arguments": {
      "a": 5,
      "b": 3
    }
  }
}
```

## Security Features

### JWT Validation

- **RS256 Algorithm**: Uses asymmetric cryptography for secure token validation
- **JWKS Integration**: Automatically fetches public keys from Django's JWKS endpoint
- **Claim Validation**: Validates issuer, audience, and expiration claims
- **Caching**: Caches JWKS keys with configurable TTL for performance

### Request Context

The middleware attaches user information to each request:

```python
request.state.user = {
    "id": payload.get("user_id"),
    "email": payload.get("email"),
    "username": payload.get("username"),
    "token_type": payload.get("token_type"),
    "exp": payload.get("exp"),
    "iat": payload.get("iat"),
    "jti": payload.get("jti"),
}
```

## Error Handling

The server returns proper OAuth2 error responses:

```json
{
  "error": "invalid_token",
  "error_description": "Token has expired"
}
```

Common error types:
- `invalid_token`: Token is malformed, expired, or invalid
- `insufficient_scope`: Token doesn't have required permissions

## Development

### Adding New Tools

1. Add your tool function to `src/tools.py`:

```python
@mcp.tool
async def my_new_tool(request: Request, param1: str, param2: int = 0) -> Dict:
    """Description of what this tool does"""
    if not hasattr(request.state, 'user') or not request.state.user:
        raise Exception("User not authenticated")
    
    # Your tool logic here
    return {"result": "success"}
```

2. Tools automatically have access to:
   - `request.state.user`: Authenticated user information
   - `request.headers.get("Authorization")`: Original JWT token for backend requests

### Testing

```bash
# Install test dependencies
pip install pytest httpx pytest-asyncio

# Run tests (when available)
pytest tests/
```

## Configuration Reference

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `DJANGO_BASE_URL` | Base URL of Django backend | `http://localhost:8000` |
| `JWT_AUDIENCE` | Expected JWT audience claim | `cccrm-api` |
| `JWT_ISSUER` | Expected JWT issuer claim | `cccrm-backend` |
| `JWT_PUBLIC_KEY` | Static RSA public key (optional) | - |
| `JWKS_CACHE_TTL` | JWKS cache TTL in seconds | `3600` |
| `PORT` | Server port | `10000` |
| `TAVILY_API_KEY` | Tavily API key for web search | - |

## Troubleshooting

### Common Issues

1. **"Failed to fetch JWKS keys"**
   - Check that `DJANGO_BASE_URL` is correct
   - Ensure Django backend is running and accessible
   - Verify JWKS endpoint is available at `/auth/.well-known/jwks.json`

2. **"Invalid token issuer/audience"**
   - Ensure `JWT_ISSUER` and `JWT_AUDIENCE` match Django settings
   - Check that tokens are issued with correct claims

3. **"Token validation failed"**
   - Verify token is not expired
   - Check that JWT keys match between Django and MCP server
   - Ensure RS256 algorithm is used

### Debugging

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## License

[Your License Here]