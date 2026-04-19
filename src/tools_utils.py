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


# Companies
async def list_companies(**filters) -> Dict:
    """List/search companies."""
    try:
        companies = await make_django_request("/api/companies/", "GET", data=filters if filters else None)
        return {
            "companies": companies,
            "message": "Companies retrieved successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to retrieve companies"
        }

async def get_company(company_id: str) -> Dict:
    """Retrieve a company by ID."""
    try:
        company = await make_django_request(f"/api/companies/{company_id}/", "GET")
        return {
            "company": company,
            "message": "Company retrieved successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to retrieve company"
        }

async def create_company(data: Dict) -> Dict:
    """Create a new company."""
    try:
        company = await make_django_request("/api/companies/", "POST", data=data)
        return {
            "company": company,
            "message": "Company created successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to create company"
        }

async def update_company(company_id: str, data: Dict) -> Dict:
    """Update a company."""
    try:
        company = await make_django_request(f"/api/companies/{company_id}/", "PATCH", data=data)
        return {
            "company": company,
            "message": "Company updated successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to update company"
        }

async def delete_company(company_id: str) -> Dict:
    """Delete a company."""
    try:
        result = await make_django_request(f"/api/companies/{company_id}/", "DELETE")
        return {
            "result": result,
            "message": "Company deleted successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to delete company"
        }

async def import_companies(companies: list[Dict]) -> Dict:
    """Bulk create companies."""
    try:
        result = await make_django_request("/api/companies/import/", "POST", data=companies)
        return {
            "result": result,
            "message": "Companies imported successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to import companies"
        }


# Notes
async def list_notes(**filters) -> Dict:
    """List/search notes."""
    try:
        notes = await make_django_request("/api/notes/", "GET", data=filters if filters else None)
        return {
            "notes": notes,
            "message": "Notes retrieved successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to retrieve notes"
        }

async def get_note(note_id: str) -> Dict:
    """Retrieve a note by ID."""
    try:
        note = await make_django_request(f"/api/notes/{note_id}/", "GET")
        return {
            "note": note,
            "message": "Note retrieved successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to retrieve note"
        }

async def create_note(data: Dict) -> Dict:
    """Create a new note."""
    try:
        note = await make_django_request("/api/notes/", "POST", data=data)
        return {
            "note": note,
            "message": "Note created successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to create note"
        }

async def update_note(note_id: str, data: Dict) -> Dict:
    """Update a note."""
    try:
        note = await make_django_request(f"/api/notes/{note_id}/", "PATCH", data=data)
        return {
            "note": note,
            "message": "Note updated successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to update note"
        }

async def delete_note(note_id: str) -> Dict:
    """Delete a note."""
    try:
        result = await make_django_request(f"/api/notes/{note_id}/", "DELETE")
        return {
            "result": result,
            "message": "Note deleted successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to delete note"
        }

async def import_notes(notes: list[Dict]) -> Dict:
    """Bulk create notes."""
    try:
        result = await make_django_request("/api/notes/import/", "POST", data=notes)
        return {
            "result": result,
            "message": "Notes imported successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to import notes"
        }


# People
async def list_people(**filters) -> Dict:
    """List/search people."""
    try:
        people = await make_django_request("/api/people/", "GET", data=filters if filters else None)
        return {
            "people": people,
            "message": "People retrieved successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to retrieve people"
        }

async def get_person(person_id: str) -> Dict:
    """Retrieve a person by ID."""
    try:
        person = await make_django_request(f"/api/people/{person_id}/", "GET")
        return {
            "person": person,
            "message": "Person retrieved successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to retrieve person"
        }

async def get_person_context(person_id: str, sections: str = "all") -> Dict:
    """Get related data for a person."""
    try:
        context = await make_django_request(f"/api/people/{person_id}/context/", "GET", data={"section": sections})
        return {
            "context": context,
            "message": "Person context retrieved successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to retrieve person context"
        }

async def create_person(data: Dict) -> Dict:
    """Create a new person."""
    try:
        person = await make_django_request("/api/people/", "POST", data=data)
        return {
            "person": person,
            "message": "Person created successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to create person"
        }

async def update_person(person_id: str, data: Dict) -> Dict:
    """Update a person."""
    try:
        person = await make_django_request(f"/api/people/{person_id}/", "PATCH", data=data)
        return {
            "person": person,
            "message": "Person updated successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to update person"
        }

async def delete_person(person_id: str) -> Dict:
    """Delete a person."""
    try:
        result = await make_django_request(f"/api/people/{person_id}/", "DELETE")
        return {
            "result": result,
            "message": "Person deleted successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to delete person"
        }

async def import_people(people: list[Dict], auto_create_company: bool = False) -> Dict:
    """Bulk create people."""
    try:
        if auto_create_company:
            data = {"data": people, "auto_create": {"company": True}}
        else:
            data = people
        result = await make_django_request("/api/people/import/", "POST", data=data)
        return {
            "result": result,
            "message": "People imported successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to import people"
        }


# Search
async def global_search(q: str) -> Dict:
    """Perform a global search across People, Companies, Tasks, and Notes."""
    try:
        results = await make_django_request("/api/search/", "GET", data={"q": q})
        return {
            "results": results,
            "message": "Search completed successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to perform search"
        }


# Tasks
async def list_tasks(**filters) -> Dict:
    """List/search tasks."""
    try:
        tasks = await make_django_request("/api/tasks/", "GET", data=filters if filters else None)
        return {
            "tasks": tasks,
            "message": "Tasks retrieved successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to retrieve tasks"
        }

async def get_task(task_id: str) -> Dict:
    """Retrieve a task by ID."""
    try:
        task = await make_django_request(f"/api/tasks/{task_id}/", "GET")
        return {
            "task": task,
            "message": "Task retrieved successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to retrieve task"
        }

async def create_task(data: Dict) -> Dict:
    """Create a new task."""
    try:
        task = await make_django_request("/api/tasks/", "POST", data=data)
        return {
            "task": task,
            "message": "Task created successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to create task"
        }

async def update_task(task_id: str, data: Dict) -> Dict:
    """Update a task."""
    try:
        task = await make_django_request(f"/api/tasks/{task_id}/", "PATCH", data=data)
        return {
            "task": task,
            "message": "Task updated successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to update task"
        }

async def delete_task(task_id: str) -> Dict:
    """Delete a task."""
    try:
        result = await make_django_request(f"/api/tasks/{task_id}/", "DELETE")
        return {
            "result": result,
            "message": "Task deleted successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to delete task"
        }

async def import_tasks(tasks: list[Dict], auto_create_related_person: bool = False) -> Dict:
    """Bulk create tasks."""
    try:
        if auto_create_related_person:
            data = {"data": tasks, "auto_create": {"related_person": True}}
        else:
            data = tasks
        result = await make_django_request("/api/tasks/import/", "POST", data=data)
        return {
            "result": result,
            "message": "Tasks imported successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to import tasks"
        }


# Activities
async def list_activities(**filters) -> Dict:
    """List/search activities."""
    try:
        activities = await make_django_request("/api/activities/", "GET", data=filters if filters else None)
        return {
            "activities": activities,
            "message": "Activities retrieved successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to retrieve activities"
        }

async def create_activity(data: Dict) -> Dict:
    """Create a new activity."""
    try:
        activity = await make_django_request("/api/activities/", "POST", data=data)
        return {
            "activity": activity,
            "message": "Activity created successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to create activity"
        }

async def import_activities(activities: list[Dict], auto_create_related_person: bool = False, auto_create_related_company: bool = False) -> Dict:
    """Bulk create activities."""
    try:
        auto_create = {}
        if auto_create_related_person:
            auto_create["related_person"] = True
        if auto_create_related_company:
            auto_create["related_company"] = True
        if auto_create:
            data = {"data": activities, "auto_create": auto_create}
        else:
            data = activities
        result = await make_django_request("/api/activities/import/", "POST", data=data)
        return {
            "result": result,
            "message": "Activities imported successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to import activities"
        }


# Interaction Types
async def list_interaction_types(**filters) -> Dict:
    """List/search interaction types."""
    try:
        types = await make_django_request("/api/interaction-types/", "GET", data=filters if filters else None)
        return {
            "interaction_types": types,
            "message": "Interaction types retrieved successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to retrieve interaction types"
        }

async def create_interaction_type(data: Dict) -> Dict:
    """Create a new interaction type."""
    try:
        interaction_type = await make_django_request("/api/interaction-types/", "POST", data=data)
        return {
            "interaction_type": interaction_type,
            "message": "Interaction type created successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to create interaction type"
        }

async def get_interaction_type(type_id: str) -> Dict:
    """Retrieve an interaction type by ID."""
    try:
        interaction_type = await make_django_request(f"/api/interaction-types/{type_id}/", "GET")
        return {
            "interaction_type": interaction_type,
            "message": "Interaction type retrieved successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to retrieve interaction type"
        }

async def update_interaction_type(type_id: str, data: Dict) -> Dict:
    """Update an interaction type."""
    try:
        interaction_type = await make_django_request(f"/api/interaction-types/{type_id}/", "PATCH", data=data)
        return {
            "interaction_type": interaction_type,
            "message": "Interaction type updated successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to update interaction type"
        }

async def delete_interaction_type(type_id: str) -> Dict:
    """Delete an interaction type."""
    try:
        result = await make_django_request(f"/api/interaction-types/{type_id}/", "DELETE")
        return {
            "result": result,
            "message": "Interaction type deleted successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to delete interaction type"
        }


# Interactions (Logs)
async def list_interactions(**filters) -> Dict:
    """List/search interactions."""
    try:
        interactions = await make_django_request("/api/interactions/", "GET", data=filters if filters else None)
        return {
            "interactions": interactions,
            "message": "Interactions retrieved successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to retrieve interactions"
        }

async def create_interaction(data: Dict) -> Dict:
    """Create a new interaction."""
    try:
        interaction = await make_django_request("/api/interactions/", "POST", data=data)
        return {
            "interaction": interaction,
            "message": "Interaction created successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to create interaction"
        }

async def get_interaction(interaction_id: str) -> Dict:
    """Retrieve an interaction by ID."""
    try:
        interaction = await make_django_request(f"/api/interactions/{interaction_id}/", "GET")
        return {
            "interaction": interaction,
            "message": "Interaction retrieved successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to retrieve interaction"
        }

async def update_interaction(interaction_id: str, data: Dict) -> Dict:
    """Update an interaction."""
    try:
        interaction = await make_django_request(f"/api/interactions/{interaction_id}/", "PATCH", data=data)
        return {
            "interaction": interaction,
            "message": "Interaction updated successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to update interaction"
        }

async def delete_interaction(interaction_id: str) -> Dict:
    """Delete an interaction."""
    try:
        result = await make_django_request(f"/api/interactions/{interaction_id}/", "DELETE")
        return {
            "result": result,
            "message": "Interaction deleted successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to delete interaction"
        }

async def import_interactions(interactions: list[Dict], auto_create_related_person: bool = False, auto_create_related_company: bool = False) -> Dict:
    """Bulk create interactions."""
    try:
        auto_create = {}
        if auto_create_related_person:
            auto_create["related_person"] = True
        if auto_create_related_company:
            auto_create["related_company"] = True
        if auto_create:
            data = {"data": interactions, "auto_create": auto_create}
        else:
            data = interactions
        result = await make_django_request("/api/interactions/import/", "POST", data=data)
        return {
            "result": result,
            "message": "Interactions imported successfully"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to import interactions"
        }