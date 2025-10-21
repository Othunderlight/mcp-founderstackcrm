# Django Integration Guide

This guide shows how to integrate the MCP Server with your Django backend for OAuth2 authentication with Google.

### before you start
- you should already have the allauth (for me i only uses google), JWT for DRF configured
- fastapi (the mcp server) runs on 10000
- my base backend (django runs on 8000) 

## 1. Django Setup Requirements

### Required Apps

Ensure your Django `INSTALLED_APPS` includes:

```python
INSTALLED_APPS = [
    # ... other apps
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'rest_framework',
    'rest_framework_simplejwt',
    'dj_rest_auth',
    'dj_rest_auth.registration',
]
```

### JWT Configuration

Your Django `settings.py` should have:

```python
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,

    'ALGORITHM': 'RS256',
    'SIGNING_KEY': env('JWT_PRIVATE_KEY'),  # RS256 private key
    'VERIFYING_KEY': env('JWT_PUBLIC_KEY'),  # RS256 public key
    'AUDIENCE': env('JWT_AUDIENCE', default='cccrm-api'),
    'ISSUER': env('JWT_ISSUER', default='cccrm-backend'),

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}

# DRF Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
}

# Google OAuth Configuration
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'OAUTH_PKCE_ENABLED': True,
    }
}
```

## 2. Add MCP Integration Views

Copy the provided `mcp_django_views.py` file to your Django app and add the views:

```python
# In your app directory: your_app/mcp_views.py
# Copy the entire content from mcp_django_views.py
```

## 3. Add URL Patterns

Add these URL patterns to your Django `urls.py`:

```python
# In your main urls.py or app urls.py
from django.urls import path, include
from . import mcp_views  # Import your MCP views

urlpatterns = [
    # ... your existing URLs
    
    # Existing auth URLs
    path('oauth/', include('allauth.urls')),
    path('auth/', include('dj_rest_auth.urls')),
    path('auth/registration/', include('dj_rest_auth.registration.urls')),
    
    # MCP OAuth2 Integration URLs
    path('mcp/oauth2/callback/', mcp_views.mcp_oauth_callback, name='mcp_oauth_callback'),
    path('api/mcp/user/', mcp_views.mcp_get_user_info, name='mcp_get_user_info'),
    path('api/mcp/jwt/', mcp_views.mcp_generate_jwt, name='mcp_generate_jwt'),
]
```

## 4. Environment Variables

Add these to your Django `.env` file:

```env
# JWT Keys (generate using the provided script)
JWT_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC...
-----END PRIVATE KEY-----

JWT_PUBLIC_KEY=-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAwrR7...
-----END PUBLIC KEY-----

## or just use with open fro the .pem files instead, as i did with the code  

# JWT Settings
JWT_AUDIENCE=
JWT_ISSUER=


```

## 5. Generate JWT Keys

Use this script to generate RSA key pairs:

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

print("Add these to your Django .env file:")
print(f"JWT_PRIVATE_KEY={private_pem}")
print(f"JWT_PUBLIC_KEY={public_pem}")

# Save to files for MCP server if needed
with open('jwt_private_key.pem', 'w') as f:
    f.write(private_pem)
with open('jwt_public_key.pem', 'w') as f:
    f.write(public_pem)
```

Run it:
```bash
python generate_jwt_keys.py
```

## 6. JWKS Endpoint

Add a JWKS endpoint to expose your public key:

```python
# In your Django app views.py
import json
from django.http import JsonResponse
from django.conf import settings
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import load_pem_public_key
import base64
import hashlib

def jwks_endpoint(request):
    """
    JSON Web Key Set endpoint for MCP server to validate JWT tokens.
    """
    try:
        # Load public key
        public_key = load_pem_public_key(settings.SIMPLE_JWT['VERIFYING_KEY'].encode())
        
        # Extract key components for JWK
        public_numbers = public_key.public_numbers()
        
        # Convert to base64url
        def to_base64url(data):
            return base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii')
        
        # Create JWK
        n = to_base64url(public_numbers.n.to_bytes((public_numbers.n.bit_length() + 7) // 8, 'big'))
        e = to_base64url(public_numbers.e.to_bytes((public_numbers.e.bit_length() + 7) // 8, 'big'))
        
        # Generate key ID from public key
        key_data = settings.SIMPLE_JWT['VERIFYING_KEY'].encode()
        kid = hashlib.sha256(key_data).hexdigest()[:16]
        
        jwk = {
            "kty": "RSA",
            "use": "sig",
            "alg": "RS256",
            "kid": kid,
            "n": n,
            "e": e
        }
        
        jwks = {
            "keys": [jwk]
        }
        
        return JsonResponse(jwks)
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

# Add to urls.py:
# path('auth/.well-known/jwks.json', views.jwks_endpoint, name='jwks'),
```

## 7. Google OAuth Setup

1. **Google Cloud Console Setup:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing
   - Enable Google+ API
   - Create OAuth 2.0 credentials
   - Add your domain to authorized domains
   - Add redirect URIs:
     - `http://localhost:8000/oauth/google/callback/` (development)
     - `https://yourdomain.com/oauth/google/callback/` (production)

2. **Django Allauth Configuration:**
   ```python
   # In Django admin or programmatically:
   from allauth.socialaccount.models import SocialApp
   
   SocialApp.objects.create(
       provider='google',
       name='Google OAuth',
       client_id='your_google_client_id',
       secret='your_google_client_secret',
   )
   
   # Add your site to the social app
   from django.contrib.sites.models import Site
   site = Site.objects.get(id=1)
   social_app.sites.add(site)
   ```

## 8. Testing the Integration

1. **Start Django Server:**
   ```bash
   python manage.py runserver
   ```

2. **Start MCP Server:**
   ```bash
   cd mcp-auth-test
   mcp-server
   # or
   python -m src.server
   ```

3. **Test OAuth2 Registration:**
   ```bash
   curl -X POST http://localhost:10000/oauth2/register \
     -H "Content-Type: application/json" \
     -d '{
       "client_name": "Test Client",
       "redirect_uris": ["http://localhost:3000/callback"]
     }'
   ```

4. **Test Authorization Flow:**
   - Use the returned `client_id` to build authorization URL
   - Visit: `http://localhost:10000/oauth2/authorize?client_id=YOUR_CLIENT_ID&redirect_uri=http://localhost:3000/callback&response_type=code&state=test`
   - Should redirect to Google OAuth
   - After authentication, should redirect back with authorization code

5. **Test Token Exchange:**
   ```bash
   curl -X POST http://localhost:10000/oauth2/token \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "grant_type=authorization_code&client_id=YOUR_CLIENT_ID&client_secret=YOUR_CLIENT_SECRET&code=YOUR_AUTH_CODE&redirect_uri=http://localhost:3000/callback"
   ```

## 9. Production Considerations

### Security
- Use HTTPS in production
- Set proper CORS origins
- Use secure session cookies
- Implement rate limiting
- Store client secrets securely

### Environment Variables
```env
# Production Django settings
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# MCP Server settings
DJANGO_BASE_URL=https://yourdomain.com
```

### Database
- Use PostgreSQL/MySQL in production
- Set up proper database migrations
- Configure connection pooling

### Deployment
- Use gunicorn/uwsgi for Django
- Use uvicorn for MCP server
- Set up reverse proxy (nginx)
- Configure proper logging
- Set up monitoring

## 10. Troubleshooting

### Common Issues

1. **JWKS Fetch Errors:**
   ```
   Error: Failed to fetch JWKS keys
   ```
   - Ensure Django JWKS endpoint is accessible
   - Check DJANGO_BASE_URL configuration
   - Verify JWT keys are properly configured

2. **OAuth Callback Errors:**
   ```
   Error: Invalid authorization request
   ```
   - Check state parameter consistency
   - Verify callback URL configuration
   - Ensure proper URL encoding

3. **JWT Validation Errors:**
   ```
   Error: Invalid token issuer/audience
   ```
   - Verify JWT_ISSUER and JWT_AUDIENCE match between Django and MCP server
   - Check that JWT keys are identical

4. **Google OAuth Issues:**
   ```
   Error: OAuth error: invalid_client
   ```
   - Verify Google OAuth credentials
   - Check authorized redirect URIs
   - Ensure Google+ API is enabled

### Debug Mode
Enable debug logging in both Django and MCP server:

```python
# Django settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'allauth': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'your_app.mcp_views': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

```python
# MCP server: set logging level to DEBUG
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 11. API Endpoints Summary

### Django Endpoints (to implement)
- `GET /mcp/oauth2/callback/` - OAuth callback from MCP server
- `GET /api/mcp/user/` - Get user info for MCP server
- `POST /api/mcp/jwt/` - Generate JWT tokens for MCP server
- `GET /auth/.well-known/jwks.json` - JWKS endpoint

### MCP Server Endpoints (already implemented)
- `POST /oauth2/register` - Dynamic client registration
- `GET /oauth2/authorize` - OAuth authorization endpoint
- `GET /oauth2/callback` - OAuth callback handler
- `POST /oauth2/token` - Token exchange endpoint
- `GET /.well-known/oauth-authorization-server` - OAuth metadata
- `GET /.well-known/oauth-protected-resource/mcp` - Resource metadata

This completes the Django integration for OAuth2 Dynamic Client Registration with Google authentication!