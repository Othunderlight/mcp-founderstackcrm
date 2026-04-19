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


# Companies

@mcp.tool()
async def list_companies(filters: Optional[Dict] = None) -> Dict:
    """
    Lists all companies for the authenticated user, with optional filters.

    Args:
        filters: Optional dictionary of query filters (e.g., {"search": "term", "location__icontains": "dubai"}).

    Returns:
        A dictionary containing a list of companies or an error message.
    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")

    try:
        if filters:
            tool_output = await tu.list_companies(**filters)
        else:
            tool_output = await tu.list_companies()
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

@mcp.tool()
async def get_company(company_id: str) -> Dict:
    """
    Retrieves a specific company by ID.

    Args:
        company_id: The UUID of the company to retrieve.

    Returns:
        A dictionary containing the company details or an error message.
    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")

    try:
        tool_output = await tu.get_company(company_id)
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

@mcp.tool()
async def create_company(data: Dict) -> Dict:
    """
    Creates a new company.

    Args:
        data: A dictionary containing company details (e.g., {"name": "Acme Corp", "domain": "acme.com"}).

    Returns:
        A dictionary containing the created company or an error message.
    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")

    try:
        tool_output = await tu.create_company(data)
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

@mcp.tool()
async def update_company(company_id: str, data: Dict) -> Dict:
    """
    Updates an existing company.

    Args:
        company_id: The UUID of the company to update.
        data: A dictionary of fields to update (e.g., {"employees": "500-1000"}).

    Returns:
        A dictionary containing the updated company or an error message.
    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")

    try:
        tool_output = await tu.update_company(company_id, data)
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

@mcp.tool()
async def delete_company(company_id: str) -> Dict:
    """
    Deletes a company.

    Args:
        company_id: The UUID of the company to delete.

    Returns:
        A dictionary confirming deletion or an error message.
    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")

    try:
        tool_output = await tu.delete_company(company_id)
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

@mcp.tool()
async def import_companies(companies: List[Dict]) -> Dict:
    """
    Bulk imports companies.

    Args:
        companies: A list of company dictionaries to import.

    Returns:
        A dictionary containing the import results or an error message.
    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")

    try:
        tool_output = await tu.import_companies(companies)
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


# Notes

@mcp.tool()
async def list_notes(filters: Optional[Dict] = None) -> Dict:
    """
    Lists all notes for the authenticated user, with optional filters.

    Args:
        filters: Optional dictionary of query filters (e.g., {"search": "term", "title__icontains": "meeting"}).

    Returns:
        A dictionary containing a list of notes or an error message.
    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")

    try:
        if filters:
            tool_output = await tu.list_notes(**filters)
        else:
            tool_output = await tu.list_notes()
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

@mcp.tool()
async def get_note(note_id: str) -> Dict:
    """
    Retrieves a specific note by ID.

    Args:
        note_id: The UUID of the note to retrieve.

    Returns:
        A dictionary containing the note details or an error message.
    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")

    try:
        tool_output = await tu.get_note(note_id)
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

@mcp.tool()
async def create_note(data: Dict) -> Dict:
    """
    Creates a new note.

    Args:
        data: A dictionary containing note details (e.g., {"title": "Meeting Notes", "content": "..."}).

    Returns:
        A dictionary containing the created note or an error message.
    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")

    try:
        tool_output = await tu.create_note(data)
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

@mcp.tool()
async def update_note(note_id: str, data: Dict) -> Dict:
    """
    Updates an existing note.

    Args:
        note_id: The UUID of the note to update.
        data: A dictionary of fields to update (e.g., {"content": "Updated content"}).

    Returns:
        A dictionary containing the updated note or an error message.
    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")

    try:
        tool_output = await tu.update_note(note_id, data)
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

@mcp.tool()
async def delete_note(note_id: str) -> Dict:
    """
    Deletes a note.

    Args:
        note_id: The UUID of the note to delete.

    Returns:
        A dictionary confirming deletion or an error message.
    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")

    try:
        tool_output = await tu.delete_note(note_id)
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

@mcp.tool()
async def import_notes(notes: List[Dict]) -> Dict:
    """
    Bulk imports notes.

    Args:
        notes: A list of note dictionaries to import.

    Returns:
        A dictionary containing the import results or an error message.
    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")

    try:
        tool_output = await tu.import_notes(notes)
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


# People

@mcp.tool()
async def list_people(filters: Optional[Dict] = None) -> Dict:
    """
    Lists all people for the authenticated user, with optional filters.

    Args:
        filters: Optional dictionary of query filters (e.g., {"search": "ahmed", "stage": "Qualified"}).

    Returns:
        A dictionary containing a list of people or an error message.
    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")

    try:
        if filters:
            tool_output = await tu.list_people(**filters)
        else:
            tool_output = await tu.list_people()
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

@mcp.tool()
async def get_person(person_id: str) -> Dict:
    """
    Retrieves a specific person by ID.

    Args:
        person_id: The UUID of the person to retrieve.

    Returns:
        A dictionary containing the person details or an error message.
    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")

    try:
        tool_output = await tu.get_person(person_id)
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

@mcp.tool()
async def get_person_context(person_id: str, sections: str = "all") -> Dict:
    """
    Retrieves related data for a specific person.

    Args:
        person_id: The UUID of the person.
        sections: Section to retrieve ("activities", "tasks", "notes", or "all"). Default "all".

    Returns:
        A dictionary containing the context data or an error message.
    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")

    try:
        tool_output = await tu.get_person_context(person_id, sections)
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

@mcp.tool()
async def create_person(data: Dict) -> Dict:
    """
    Creates a new person.

    Args:
        data: A dictionary containing person details (e.g., {"name": "John Doe", "email": "john@example.com"}).

    Returns:
        A dictionary containing the created person or an error message.
    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")

    try:
        tool_output = await tu.create_person(data)
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

@mcp.tool()
async def update_person(person_id: str, data: Dict) -> Dict:
    """
    Updates an existing person.

    Args:
        person_id: The UUID of the person to update.
        data: A dictionary of fields to update (e.g., {"job_title": "Manager"}).

    Returns:
        A dictionary containing the updated person or an error message.
    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")

    try:
        tool_output = await tu.update_person(person_id, data)
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

@mcp.tool()
async def delete_person(person_id: str) -> Dict:
    """
    Deletes a person.

    Args:
        person_id: The UUID of the person to delete.

    Returns:
        A dictionary confirming deletion or an error message.
    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")

    try:
        tool_output = await tu.delete_person(person_id)
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

@mcp.tool()
async def import_people(people: List[Dict], auto_create_company: bool = False) -> Dict:
    """
    Bulk imports people.

    Args:
        people: A list of person dictionaries to import.
        auto_create_company: If True, create companies by name if they don't exist.

    Returns:
        A dictionary containing the import results or an error message.
    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")

    try:
        tool_output = await tu.import_people(people, auto_create_company)
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


# Search

@mcp.tool()
async def global_search(q: str) -> Dict:
    """
    Performs a global search across People, Companies, Tasks, and Notes.

    Args:
        q: The search query string.

    Returns:
        A dictionary containing relevance-scored results from all models or an error message.
    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")

    try:
        tool_output = await tu.global_search(q)
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


# Tasks

@mcp.tool()
async def list_tasks(filters: Optional[Dict] = None) -> Dict:
    """
    Lists all tasks for the authenticated user, with optional filters.

    Args:
        filters: Optional dictionary of query filters (e.g., {"status": "Todo", "due_date__gt": "2024-01-01"}).

    Returns:
        A dictionary containing a list of tasks or an error message.
    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")

    try:
        if filters:
            tool_output = await tu.list_tasks(**filters)
        else:
            tool_output = await tu.list_tasks()
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

@mcp.tool()
async def get_task(task_id: str) -> Dict:
    """
    Retrieves a specific task by ID.

    Args:
        task_id: The UUID of the task to retrieve.

    Returns:
        A dictionary containing the task details or an error message.
    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")

    try:
        tool_output = await tu.get_task(task_id)
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

@mcp.tool()
async def create_task(data: Dict) -> Dict:
    """
    Creates a new task.

    Args:
        data: A dictionary containing task details (e.g., {"title": "Follow up", "status": "Todo"}).

    Returns:
        A dictionary containing the created task or an error message.
    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")

    try:
        tool_output = await tu.create_task(data)
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

@mcp.tool()
async def update_task(task_id: str, data: Dict) -> Dict:
    """
    Updates an existing task.

    Args:
        task_id: The UUID of the task to update.
        data: A dictionary of fields to update (e.g., {"status": "Done"}).

    Returns:
        A dictionary containing the updated task or an error message.
    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")

    try:
        tool_output = await tu.update_task(task_id, data)
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

@mcp.tool()
async def delete_task(task_id: str) -> Dict:
    """
    Deletes a task.

    Args:
        task_id: The UUID of the task to delete.

    Returns:
        A dictionary confirming deletion or an error message.
    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")

    try:
        tool_output = await tu.delete_task(task_id)
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

@mcp.tool()
async def import_tasks(tasks: List[Dict], auto_create_related_person: bool = False) -> Dict:
    """
    Bulk imports tasks.

    Args:
        tasks: A list of task dictionaries to import.
        auto_create_related_person: If True, create persons by name if they don't exist.

    Returns:
        A dictionary containing the import results or an error message.
    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")

    try:
        tool_output = await tu.import_tasks(tasks, auto_create_related_person)
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


# Activities

@mcp.tool()
async def list_activities(filters: Optional[Dict] = None) -> Dict:
    """
    Lists all activities for the authenticated user, with optional filters.

    Args:
        filters: Optional dictionary of query filters (e.g., {"type": "call", "channel": "linkedin", "direction": "sent"}).

    Returns:
        A dictionary containing a list of activities or an error message.
    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")

    try:
        if filters:
            tool_output = await tu.list_activities(**filters)
        else:
            tool_output = await tu.list_activities()
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

@mcp.tool()
async def create_activity(data: Dict) -> Dict:
    """
    Creates a new activity.

    Args:
        data: A dictionary containing activity details (e.g., {"type": "call", "title": "Discovery Call", "channel": "linkedin", "direction": "sent", "content": "...", "related_person": "PERSON_UUID", "user": "USER_UUID"}).
                  Fields: type (required), channel, direction, title, content, date, related_person, related_company, user.

    Returns:
        A dictionary containing the created activity or an error message.
    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")

    try:
        tool_output = await tu.create_activity(data)
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

@mcp.tool()
async def import_activities(activities: List[Dict], auto_create_related_person: bool = False, auto_create_related_company: bool = False) -> Dict:
    """
    Bulk imports activities.

    Args:
        activities: A list of activity dictionaries to import.
        auto_create_related_person: If True, create persons by name if they don't exist.
        auto_create_related_company: If True, create companies by name if they don't exist.

    Returns:
        A dictionary containing the import results or an error message.
    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")

    try:
        tool_output = await tu.import_activities(activities, auto_create_related_person, auto_create_related_company)
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


# Interaction Types

@mcp.tool()
async def list_interaction_types(filters: Optional[Dict] = None) -> Dict:
    """
    Lists all interaction types for the authenticated user, with optional filters.

    Args:
        filters: Optional dictionary of query filters (e.g., {"name__icontains": "call"}).

    Returns:
        A dictionary containing a list of interaction types or an error message.
    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")

    try:
        if filters:
            tool_output = await tu.list_interaction_types(**filters)
        else:
            tool_output = await tu.list_interaction_types()
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

@mcp.tool()
async def create_interaction_type(data: Dict) -> Dict:
    """
    Creates a new interaction type.

    Args:
        data: A dictionary containing interaction type details (e.g., {"name": "Discovery Call", "description": "...", "color": "#4CAF50", "icon": "phone"}).

    Returns:
        A dictionary containing the created interaction type or an error message.
    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")

    try:
        tool_output = await tu.create_interaction_type(data)
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

@mcp.tool()
async def get_interaction_type(type_id: str) -> Dict:
    """
    Retrieves a specific interaction type by ID.

    Args:
        type_id: The UUID of the interaction type to retrieve.

    Returns:
        A dictionary containing the interaction type details or an error message.
    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")

    try:
        tool_output = await tu.get_interaction_type(type_id)
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

@mcp.tool()
async def update_interaction_type(type_id: str, data: Dict) -> Dict:
    """
    Updates an existing interaction type.

    Args:
        type_id: The UUID of the interaction type to update.
        data: A dictionary of fields to update (e.g., {"description": "Updated description"}).

    Returns:
        A dictionary containing the updated interaction type or an error message.
    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")

    try:
        tool_output = await tu.update_interaction_type(type_id, data)
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

@mcp.tool()
async def delete_interaction_type(type_id: str) -> Dict:
    """
    Deletes an interaction type.

    Args:
        type_id: The UUID of the interaction type to delete.

    Returns:
        A dictionary confirming deletion or an error message.
    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")

    try:
        tool_output = await tu.delete_interaction_type(type_id)
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


# Interactions (Logs)

@mcp.tool()
async def list_interactions(filters: Optional[Dict] = None) -> Dict:
    """
    Lists all interactions for the authenticated user, with optional filters.

    Args:
        filters: Optional dictionary of query filters (e.g., {"interaction_type": "TYPE_UUID", "related_person": "PERSON_UUID"}).

    Returns:
        A dictionary containing a list of interactions or an error message.
    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")

    try:
        if filters:
            tool_output = await tu.list_interactions(**filters)
        else:
            tool_output = await tu.list_interactions()
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

@mcp.tool()
async def create_interaction(data: Dict) -> Dict:
    """
    Creates a new interaction.

    Args:
        data: A dictionary containing interaction details (e.g., {"interaction_type": "TYPE_UUID", "notes": "...", "related_person": "PERSON_UUID"}).

    Returns:
        A dictionary containing the created interaction or an error message.
    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")

    try:
        tool_output = await tu.create_interaction(data)
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

@mcp.tool()
async def get_interaction(interaction_id: str) -> Dict:
    """
    Retrieves a specific interaction by ID.

    Args:
        interaction_id: The UUID of the interaction to retrieve.

    Returns:
        A dictionary containing the interaction details or an error message.
    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")

    try:
        tool_output = await tu.get_interaction(interaction_id)
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

@mcp.tool()
async def update_interaction(interaction_id: str, data: Dict) -> Dict:
    """
    Updates an existing interaction.

    Args:
        interaction_id: The UUID of the interaction to update.
        data: A dictionary of fields to update (e.g., {"notes": "Updated notes"}).

    Returns:
        A dictionary containing the updated interaction or an error message.
    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")

    try:
        tool_output = await tu.update_interaction(interaction_id, data)
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

@mcp.tool()
async def delete_interaction(interaction_id: str) -> Dict:
    """
    Deletes an interaction.

    Args:
        interaction_id: The UUID of the interaction to delete.

    Returns:
        A dictionary confirming deletion or an error message.
    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")

    try:
        tool_output = await tu.delete_interaction(interaction_id)
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

@mcp.tool()
async def import_interactions(interactions: List[Dict], auto_create_related_person: bool = False, auto_create_related_company: bool = False) -> Dict:
    """
    Bulk imports interactions.

    Args:
        interactions: A list of interaction dictionaries to import.
        auto_create_related_person: If True, create persons by name if they don't exist.
        auto_create_related_company: If True, create companies by name if they don't exist.

    Returns:
        A dictionary containing the import results or an error message.
    """
    user_info = get_current_user()
    if not user_info:
        raise Exception("User not authenticated")

    try:
        tool_output = await tu.import_interactions(interactions, auto_create_related_person, auto_create_related_company)
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