import httpx
import logging
from contextvars import ContextVar
from mcp.server.fastmcp import FastMCP
from typing import Dict, List, Optional
import asyncio

from .config import settings

logger = logging.getLogger(__name__)

# Context variables to store user information across request lifecycle
current_user_context: ContextVar[Optional[Dict]] = ContextVar('current_user_context', default=None)
current_auth_token: ContextVar[Optional[str]] = ContextVar('current_auth_token', default=None)

mcp = FastMCP("CCCRM API 🚀", streamable_http_path="/", stateless_http=True)

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



# example tool

async def tool_function(args):
    return "Example Tool Call"

@mcp.tool()
async def example_tool() -> Dict:
    """
    What does the tool do
    
    Args:
        - arg1: describtion of it
        - arg2: describtion of it

    Return:
        over all describtion

        - return1: describtion of it
        - return2: describtion of it


    # example 1: full example if iam querying a db:

    Queries a table with an optional condition.

    Args:
        table_name: The name of the table to query.
        columns: Comma-separated list of columns to retrieve (e.g., "id, name"). Defaults to "*".
        condition: Optional SQL WHERE clause condition (e.g., "id = 1" or "completed = 0").
    Returns:
        A list of dictionaries, where each dictionary represents a row.

    # example 2: full example if iam inserting data to the db:

    Inserts a new row of data into the specified table.

    Args:
        table_name (str): The name of the table to insert data into.
        data (dict): A dictionary where keys are column names and values are the
                     corresponding values for the new row.

    Returns:
        dict: A dictionary with keys 'success' (bool) and 'message' (str).
              If successful, 'message' includes the ID of the newly inserted row.

    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")
    
    try:
        # await for the tool action function to complete
        tool_output = await tool_function(args)

        # make sure to handle the case if there is two tools calls =>
        # result1, result2 = await asyncio.gather(
        #     tool_function_1(args1),
        #     tool_function_2(args2)
        # )

        # return {
        #     "results": {
        #         "first (here you name the key a name that is relvant)": result1,
        #         "second (same for here)": result2
        #     },
        #     "user_id": user_info.get("id"),
        #     "status": "success"
        # }

        return {
            "results": tool_output,
            "user_id": user_info.get("id"),
            "status": "success"
        }
    except Exception as e:
        return {
            "error": str(e),
            "user_id": user_info.get("id"),
            "status": "Failed"
        }




# tools, your code goes here:
from .tools_utils import *


# Emails

# tool 1:
# list_email_accounts

# tool 2: 
## multiple funcs (note these should not happen in pparlel, we add the new email account and wait
## for the success, then test its connection. the example code tool will not work):
### 1:
### connect_email_account
### 2:
### test_email_account_connection

# tool 3:
# test_email_account_connection





# Leads Lists

# tool 1:
# list_lead_lists


# tool 2: 
## multiple funcs (note these should not happen in pparlel, we dont call the instruction untill the list is created 
## the example code tool will not work):
### 1:
### create_lead_list
### 2:
### add_leads_instructions; args: new_list=True


# tools 3
# add_leads_instructions; args: no need: default new_list=False





# Msgs

# tool 1:
# list_messages

# tool 2: 
## multiple funcs (parlele is ok):
### 1:
### create_new_message
### 2:
### get_lead_info_vars


# Campaigns
# tool 1:
# list_campaigns

# tool 2:
# get_campaign_stats

# tool 3:
# get_campaign_message_assignments_performance

# tool 4:
# get_campaign_leads_count

# tool 5:
# get_campaign_leads_lists

# tool 6:
# get_campaign_messages

# tool 7:
# get_campaign_options

# tool 8:
# launch new campaign

# Msg Performance By msg assignment
# tool 1
# get_message_assignments_performance
# do it but leave it commented since its as todo

# provide feedback
# tool 1
# provide_feedback; args: 
## instant=True if the user wanana give instant and fast feedback
## instant=False if the user wanana give describetive feedback