import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Django JWT Configuration
    DJANGO_BASE_URL: str = os.environ.get("DJANGO_BASE_URL", "http://127.0.0.1:8000")
    JWT_PUBLIC_KEY: str = os.environ.get("JWT_PUBLIC_KEY", "")
    JWT_AUDIENCE: str = os.environ.get("JWT_AUDIENCE", "cccrm-api")
    JWT_ISSUER: str = os.environ.get("JWT_ISSUER", "cccrm-backend")
    
    # MCP OAuth metadata configuration
    AUTHORIZATION_SERVER_URL: str = os.environ.get("AUTHORIZATION_SERVER_URL", "")
    RESOURCE_METADATA_URL: str = os.environ.get("RESOURCE_METADATA_URL", "")
    METADATA_JSON_RESPONSE: str = os.environ.get("METADATA_JSON_RESPONSE", "")

    # Optional: Tavily API Key (for tools)
    TAVILY_API_KEY: str = os.environ.get("TAVILY_API_KEY", "")

    # Server Port
    PORT: int = int(os.environ.get("PORT", 10000))
    
    # JWKS caching settings
    JWKS_CACHE_TTL: int = int(os.environ.get("JWKS_CACHE_TTL", "3600"))  # 1 hour
    
    @property
    def JWKS_URL(self) -> str:
        """Generate JWKS URL from Django base URL"""
        return f"{self.DJANGO_BASE_URL.rstrip('/')}/auth/.well-known/jwks.json"

    def __post_init__(self):
        if not self.DJANGO_BASE_URL:
            raise ValueError("DJANGO_BASE_URL environment variable not set")
        if not self.JWT_PUBLIC_KEY and not self.JWKS_URL:
            raise ValueError("Either JWT_PUBLIC_KEY or DJANGO_BASE_URL must be set for JWT validation")

settings = Settings()