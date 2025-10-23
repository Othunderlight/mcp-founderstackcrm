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
from . import tools_utils as tu


# Emails

# tool 1:
# list_email_accounts

@mcp.tool()
async def list_email_accounts() -> Dict:
    """
    Lists all email accounts associated with the current user.

    Returns:
        A dictionary containing a list of email accounts or an error message.
    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")

    try:
        tool_output = await tu.list_email_accounts()
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


# tool 2: 
## multiple funcs (note these should not happen in pparlel, we add the new email account and wait
## for the success, then test its connection. the example code tool will not work):
### 1:
### connect_email_account
### 2:
### test_email_account_connection

@mcp.tool()
async def connect_and_test_email_account(data: Dict) -> Dict:
    """
    Connects a new email account and then tests the connection.

    Args:
        data: A dictionary containing the new email account details.

    Returns:
        A dictionary with the results of both operations.
    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")

    try:
        connection_result = await tu.connect_email_account(data)
        
        # Check if the connection was successful and get the new account's ID
        if connection_result.get("email_account") and connection_result.get("email_account").get("id"):
            account_id = connection_result["email_account"]["id"]
            test_result = await tu.test_email_account_connection(account_id)
            
            return {
                "results": {
                    "connection": connection_result,
                    "connection_test": test_result
                },
                "user_id": user_info.get("id"),
                "status": "success"
            }
        else:
            # Handle case where connection failed or didn't return an ID
            return {
                "results": {
                    "connection": connection_result,
                },
                "user_id": user_info.get("id"),
                "status": "success",
                "message": "Email account connection was made, but no ID was returned to test the connection."
            }

    except Exception as e:
        return {
            "error": str(e),
            "user_id": user_info.get("id"),
            "status": "Failed"
        }


# tool 3:
# test_email_account_connection

@mcp.tool()
async def test_email_account_connection(account_id: int) -> Dict:
    """
    Tests the connection for a specific email account.

    Args:
        account_id: The ID of the email account to test.

    Returns:
        A dictionary with the result of the connection test.
    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")

    try:
        tool_output = await tu.test_email_account_connection(account_id)
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






# Leads Lists

# tool 1:
# list_lead_lists

@mcp.tool()
async def list_lead_lists() -> Dict:
    """
    Lists all lead lists for the authenticated user.

    Returns:
        A dictionary containing a list of lead lists or an error message.
    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")

    try:
        tool_output = await tu.list_lead_lists()
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



# tool 2: 
## multiple funcs (note these should not happen in pparlel, we dont call the instruction untill the list is created 
## the example code tool will not work):
### 1:
### create_lead_list
### 2:
### add_leads_instructions; args: new_list=True

@mcp.tool()
async def create_lead_list_and_get_instructions(data: Dict) -> Dict:
    """
    Creates a new lead list and then provides instructions for adding leads.

    Args:
        data: A dictionary containing the new lead list details.

    Returns:
        A dictionary with the results of both operations.
    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")

    try:
        creation_result = await tu.create_lead_list(data)

        if creation_result.get("lead_list") and creation_result.get("lead_list").get("id"):
            instructions_result = await tu.add_leads_instructions(new_list=True)
            return {
                "results": {
                    "creation": creation_result,
                    "instructions": instructions_result
                },
                "user_id": user_info.get("id"),
                "status": "success"
            }
        else:
            return {
                "results": {
                    "creation": creation_result,
                },
                "user_id": user_info.get("id"),
                "status": "success",
                "message": "Lead list creation was made, but no ID was returned to get instructions."
            }

    except Exception as e:
        return {
            "error": str(e),
            "user_id": user_info.get("id"),
            "status": "Failed"
        }



# tools 3
# add_leads_instructions; args: no need: default new_list=False

@mcp.tool()
async def get_add_leads_instructions() -> Dict:
    """
    Provides instructions on how to add leads to an existing list.

    Returns:
        A dictionary containing instructions.
    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")

    try:
        tool_output = await tu.add_leads_instructions(new_list=False)
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






# Msgs

# tool 1:
# list_messages

@mcp.tool()
async def list_messages() -> Dict:
    """
    Lists all messages for the authenticated user.

    Returns:
        A dictionary containing a list of messages or an error message.
    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")

    try:
        tool_output = await tu.list_messages()
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


# tool 2: 
## multiple funcs (parlele is ok):
### 1:
### create_new_message
### 2:
### get_lead_info_vars

@mcp.tool()
async def create_message_and_get_lead_vars(data: Dict) -> Dict:
    """
    Creates a new message and gets lead info variables in parallel.

    Args:
        data: A dictionary containing the new message details.

    Returns:
        A dictionary with the results of both operations.
    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")

    try:
        new_message, lead_vars = await asyncio.gather(
            tu.create_new_message(data),
            tu.get_lead_info_vars()
        )

        return {
            "results": {
                "new_message": new_message,
                "lead_variables": lead_vars
            },
            "user_id": user_info.get("id"),
            "status": "success"
        }
    except Exception as e:
        return {
            "error": str(e),
            "user_id": user_info.get("id"),
            "status": "Failed"
        }



# Campaigns
# tool 1:
# list_campaigns

@mcp.tool()
async def list_campaigns() -> Dict:
    """
    Lists all campaigns for the authenticated user.

    Returns:
        A dictionary containing a list of campaigns or an error message.
    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")

    try:
        tool_output = await tu.list_campaigns()
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


# tool 2:
# get_campaign_stats

@mcp.tool()
async def get_campaign_stats(campaign_id: int) -> Dict:
    """
    Get stats for a specific campaign.

    Args:
        campaign_id: The ID of the campaign.

    Returns:
        A dictionary containing campaign stats or an error message.
    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")

    try:
        tool_output = await tu.get_campaign_stats(campaign_id)
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


# tool 3:
# get_campaign_message_assignments_performance

@mcp.tool()
async def get_campaign_message_assignments_performance(campaign_id: int, filters: str, search: Optional[str] = None) -> Dict:
    """
    Get performance of message assignments for a specific campaign.

    Args:
        campaign_id: The ID of the campaign.
        filters: The filters to apply.
        search: An optional search query.

    Returns:
        A dictionary containing the performance data or an error message.
    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")

    try:
        tool_output = await tu.get_campaign_message_assignments_performance(campaign_id, filters, search)
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


# tool 4:
# get_campaign_leads_count

@mcp.tool()
async def get_campaign_leads_count(campaign_id: int) -> Dict:
    """
    Get the leads count for a specific campaign.

    Args:
        campaign_id: The ID of the campaign.

    Returns:
        A dictionary containing the leads count or an error message.
    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")

    try:
        tool_output = await tu.get_campaign_leads_count(campaign_id)
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


# tool 5:
# get_campaign_leads_lists

@mcp.tool()
async def get_campaign_leads_lists(campaign_id: int) -> Dict:
    """
    Get the leads lists for a specific campaign.

    Args:
        campaign_id: The ID of the campaign.

    Returns:
        A dictionary containing the lead lists or an error message.
    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")

    try:
        tool_output = await tu.get_campaign_leads_lists(campaign_id)
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


# tool 6:
# get_campaign_messages

@mcp.tool()
async def get_campaign_messages(campaign_id: int) -> Dict:
    """
    Get messages for a specific campaign.

    Args:
        campaign_id: The ID of the campaign.

    Returns:
        A dictionary containing campaign messages or an error message.
    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")

    try:
        tool_output = await tu.get_campaign_messages(campaign_id)
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


# tool 7:
# get_campaign_options

@mcp.tool()
async def get_campaign_options(campaign_id: int) -> Dict:
    """
    Get options for a specific campaign.

    Args:
        campaign_id: The ID of the campaign.

    Returns:
        A dictionary containing campaign options or an error message.
    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")

    try:
        tool_output = await tu.get_campaign_options(campaign_id)
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


# tool 8:
# launch new campaign

@mcp.tool()
async def launch_new_campaign() -> Dict:
    """
    Provides instructions on how to launch a new campaign.

    Returns:
        A dictionary containing instructions for launching a campaign.
    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")

    try:
        tool_output = await tu.launch_campaign()
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


# Msg Performance By msg assignment
# tool 1
# get_message_assignments_performance
# do it but leave it commented since its as todo

# @mcp.tool()
# async def get_message_assignments_performance(message_id: int) -> Dict:
#     """
#     Get assignments performance for a specific message.
#
#     Args:
#         message_id: The ID of the message.
#
#     Returns:
#         A dictionary containing the assignments performance or an error message.
#     """
#     user_info = get_current_user()
#     if not user_info:
#         raise Exception("User not authenticated")
#
#     try:
#         tool_output = await tu.get_message_assignments_performance(message_id)
#         return {
#             "results": tool_output,
#             "user_id": user_info.get("id"),
#             "status": "success"
#         }
#     except Exception as e:
#         return {
#             "error": str(e),
#             "user_id": user_info.get("id"),
#             "status": "Failed"
#         }


# provide feedback
# tool 1
# provide_feedback; args: 
## instant=True if the user wanana give instant and fast feedback
## instant=False if the user wanana give describetive feedback

@mcp.tool()
async def provide_feedback(instant: bool = True) -> Dict:
    """
    Allows the user to provide feedback.

    Args:
        instant: If True, provides a way for instant feedback. 
                 If False, provides a way for descriptive feedback.

    Returns:
        A dictionary confirming the feedback was received.
    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")

    try:
        tool_output = await tu.provide_feedback(instant)
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