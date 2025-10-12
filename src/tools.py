import httpx
import logging
from contextvars import ContextVar
from mcp.server.fastmcp import FastMCP
from typing import Dict, List, Optional

from .config import settings

logger = logging.getLogger(__name__)

# Context variables to store user information across request lifecycle
current_user_context: ContextVar[Optional[Dict]] = ContextVar('current_user_context', default=None)
current_auth_token: ContextVar[Optional[str]] = ContextVar('current_auth_token', default=None)

mcp = FastMCP("CCCRM API 🚀", streamable_http_path="/mcp", host="127.0.0.1", port=settings.PORT)

def get_current_user() -> Optional[Dict]:
    """Get the current authenticated user information"""
    return current_user_context.get()

def get_current_token() -> Optional[str]:
    """Get the current authentication token"""
    return current_auth_token.get()

async def make_django_request(
    endpoint: str,
    method: str = "GET",
    data: Optional[Dict] = None,
    user_token: Optional[str] = None
) -> Dict:
    """
    Make an authenticated request to the Django backend
    """
    url = f"{settings.DJANGO_BASE_URL.rstrip('/')}{endpoint}"
    headers = {}
    
    # Use provided token or get from context
    token = user_token or get_current_token()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        async with httpx.AsyncClient() as client:
            if method.upper() == "GET":
                response = await client.get(url, headers=headers, timeout=30.0)
            elif method.upper() == "POST":
                response = await client.post(url, json=data, headers=headers, timeout=30.0)
            elif method.upper() == "PUT":
                response = await client.put(url, json=data, headers=headers, timeout=30.0)
            elif method.upper() == "DELETE":
                response = await client.delete(url, headers=headers, timeout=30.0)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
    except httpx.HTTPStatusError as e:
        logger.error(f"Django API error: {e.response.status_code} - {e.response.text}")
        raise Exception(f"Django API error: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        logger.error(f"Request to Django failed: {e}")
        raise Exception(f"Request to Django backend failed: {str(e)}")

@mcp.tool()
def add_numbers(a: int, b: int) -> int:
    """Add two numbers - simple demo tool"""
    return a + b

@mcp.tool()
async def get_user_profile() -> Dict:
    """Get the current authenticated user's profile information"""
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")
    
    # You can extend this to fetch more detailed profile from Django
    try:
        # Make request to Django API to get full profile
        endpoint = "/api/user/profile/"  # Adjust based on your Django API endpoints
        # For now, we'll return the JWT claims since we don't have the full API endpoint
        return {
            "user_id": user_info.get("id"),
            "email": user_info.get("email"),
            "username": user_info.get("username"),
            "token_exp": user_info.get("exp"),
            "message": "Profile retrieved successfully"
        }
    except Exception as e:
        # Fallback to JWT claims
        return {
            "user_id": user_info.get("id"),
            "email": user_info.get("email"),
            "username": user_info.get("username"),
            "source": "jwt_claims",
            "error": f"Could not fetch full profile: {str(e)}"
        }

@mcp.tool()
async def list_campaigns() -> Dict:
    """List all campaigns for the authenticated user"""
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")
    
    try:
        # Make request to Django API
        campaigns = await make_django_request("/api/campaigns/", "GET")
        return {
            "campaigns": campaigns,
            "user_id": user_info.get("id"),
            "message": "Campaigns retrieved successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "user_id": user_info.get("id"),
            "message": "Failed to retrieve campaigns"
        }

@mcp.tool()
async def create_campaign(name: str, description: str = "") -> Dict:
    """Create a new campaign for the authenticated user"""
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")
    
    try:
        campaign_data = {
            "name": name,
            "description": description
        }
        
        # Make request to Django API
        result = await make_django_request("/api/campaigns/", "POST", campaign_data)
        return {
            "campaign": result,
            "user_id": user_info.get("id"),
            "message": "Campaign created successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "user_id": user_info.get("id"),
            "message": "Failed to create campaign"
        }

@mcp.tool()
async def get_leads_count() -> Dict:
    """Get the total number of leads for the authenticated user"""
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")
    
    try:
        # Make request to Django API
        leads_data = await make_django_request("/api/leads/count/", "GET")
        return {
            "leads_count": leads_data.get("count", 0),
            "user_id": user_info.get("id"),
            "message": "Leads count retrieved successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "user_id": user_info.get("id"),
            "message": "Failed to retrieve leads count"
        }

@mcp.tool()
async def search_web(query: str) -> Dict:
    """Search the web using Tavily API (demonstration of external API integration)"""
    if not settings.TAVILY_API_KEY:
        return {
            "error": "Tavily API key not configured",
            "message": "Please set TAVILY_API_KEY environment variable"
        }
    
    try:
        from tavily import TavilyClient
        
        tavily_client = TavilyClient(api_key=settings.TAVILY_API_KEY)
        results = tavily_client.search(query=query, max_results=5)
        
        return {
            "query": query,
            "results": results.get("results", []),
            "message": "Web search completed successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "query": query,
            "message": "Web search failed"
        }
