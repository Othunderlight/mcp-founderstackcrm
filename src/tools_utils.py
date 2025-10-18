from typing import Dict, Any

from .tools import make_django_request

from typing import Dict, Any

# Emails
async def list_email_accounts() -> Dict:
    """List all email accounts for the authenticated user."""    
    try:
        email_accounts = await make_django_request("/api/core/email-accounts/", "GET")
        return {
            "email_accounts": email_accounts,
            "message": "Email accounts retrieved successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to retrieve email accounts"
        }

async def connect_email_account(data: Dict) -> Dict:
    """Connect a new email account."""    
    try:
        new_email_account = await make_django_request("/api/core/email-accounts/", "POST", data=data)
        return {
            "email_account": new_email_account,
            "message": "Email account connected successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to connected email account"
        }

async def test_email_account_connection(account_id: int) -> Dict:
    """Test the connection for a specific email account."""    
    try:
        result = await make_django_request(f"/api/email-accounts/{account_id}/test-connection/", "POST")
        return {
            "result": result,
            "message": "Email account connection test initiated"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to test email account connection"
        }







# Lead Lists
async def list_lead_lists() -> Dict:
    """List all lead lists for the authenticated user."""    
    try:
        lead_lists = await make_django_request("/api/core/leadlists/", "GET")
        return {
            "lead_lists": lead_lists,
            "message": "Lead lists retrieved successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to retrieve lead lists"
        }

async def create_lead_list(data: Dict) -> Dict:
    """Create a new lead list."""    
    try:
        new_lead_list = await make_django_request("/api/core/leadlists/", "POST", data=data)
        return {
            "lead_list": new_lead_list,
            "message": "Lead list created successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to create lead list"
        }

async def add_leads_instructions(new_list=False):
    """ instructions iin adding new leads, leads only allowed to add to an existing list"""
    if new_list:
        instructions= "describe what the user need to do and give it links"

        return {
            "instructions": instructions,
            "link": ""
        }

    instructions= "describe what the user need to do and give it links"

    return {
        "instructions": instructions,
        "link": ""
    }


# Messages
async def list_messages() -> Dict:
    """List all messages for the authenticated user."""    
    try:
        messages = await make_django_request("/api/core/messages/", "GET")
        return {
            "messages": messages,
            "message": "Messages retrieved successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to retrieve messages"
        }

async def create_new_message(data: Dict) -> Dict:
    """Create a new message."""    
    try:
        new_message = await make_django_request("/api/core/messages/", "POST", data=data)
        return {
            "message": new_message,
            "message": "Message created successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to create message"
        }

async def get_lead_info_vars():
    """Get Lead Model Fields as Vars"""    
    try:
        new_message = await make_django_request("/api/core/messages/", "GET")
        return {
            "message": new_message,
            "message": "Message created successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to create message"
        }

# Campaigns
async def list_campaigns() -> Dict:
    """List all campaigns for the authenticated user"""    
    try:
        # Make request to Django API
        campaigns = await make_django_request("/api/core/campaigns/", "GET")
        return {
            "campaigns": campaigns,
            "message": "Campaigns retrieved successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to retrieve campaigns"
        }

async def get_campaign_stats(campaign_id: int) -> Dict:
    """Get stats for a specific campaign."""    
    try:
        stats = await make_django_request(f"/api/core/campaigns/{campaign_id}/stats/", "GET")
        return {
            "stats": stats,
            "message": "Campaign stats retrieved successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to retrieve campaign stats"
        }
    
async def get_campaign_message_assignments_performance(campaign_id: int, filters: str, search=None) -> Dict:
    """Get assignments for a specific message."""
    try:
        if search is not None:
            data ={"status":filters, 'search':search}
        else: data ={"status":filters}  
        assignments = await make_django_request(f"/api/core/campaigns/{campaign_id}/assignments/", "GET",  data=data)
        return {
            "assignments": assignments,
            "message": "Message assignments retrieved successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to retrieve message assignments"
        }    

async def get_campaign_leads_count(campaign_id: int):
    """Get Leads Count for a specific Campaign."""    
    try:
        assignments = await make_django_request(f"/api/core/campaigns/{campaign_id}/assignments/", "GET")
        return {
            "assignments": assignments,
            "message": "Message assignments retrieved successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to retrieve message assignments"
        } 

async def get_campaign_leads_lists(campaign_id: int):
    """Get Leads Lists for a specific Campaign."""    
    try:
        assignments = await make_django_request(f"/api/core/campaigns/{campaign_id}/assignments/", "GET")
        return {
            "assignments": assignments,
            "message": "Message assignments retrieved successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to retrieve message assignments"
        } 

async def get_campaign_messages(campaign_id: int) -> Dict:
    """Get messages for a specific campaign."""    
    try:
        messages = await make_django_request(f"/api/core/campaigns/{campaign_id}/messages/", "GET")
        return {
            "messages": messages,
            "message": "Campaign messages retrieved successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to retrieve campaign messages"
        }

async def get_campaign_options(campaign_id: int) -> Dict:
    """Get options for a specific campaign."""    
    try:
        options = await make_django_request(f"/api/core/campaigns/{campaign_id}/options/", "GET")
        return {
            "options": options,
            "message": "Campaign options retrieved successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to retrieve campaign options"
        }


async def launch_campaign():
    instructions= "describe what the user need to do and give it links"

    return {
        "instructions": instructions,
        "link": ""
    }   

# Message Performance By Msg
async def get_message_assignments_performance(message_id: int) -> Dict:
    """Get assignments for a specific message."""    
    try:
        assignments = await make_django_request(f"/api/core/messages/{message_id}/assignments/", "GET")
        return {
            "assignments": assignments,
            "message": "Message assignments retrieved successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to retrieve message assignments"
        }
    



async def provide_feedback(instant=True):
    """
    type: instant or describteve
    """
    pass