from typing import Any, Dict

from toon import encode

from .tools import make_django_request


async def list_companies(**filters) -> Dict:
    """List/search companies."""
    try:
        companies = await make_django_request(
            "/api/companies/", "GET", params=filters if filters else None
        )
        return {
            "companies": encode(companies),
            "message": "Companies retrieved successfully",
        }
    except Exception as e:
        return {"error": str(e), "message": "Failed to retrieve companies"}


async def get_company(company_id: str) -> Dict:
    """Retrieve a company by ID."""
    try:
        company = await make_django_request(f"/api/companies/{company_id}/", "GET")
        return {"company": encode(company), "message": "Company retrieved successfully"}
    except Exception as e:
        return {"error": str(e), "message": "Failed to retrieve company"}


async def create_company(data: Dict) -> Dict:
    """Create a new company."""
    try:
        company = await make_django_request("/api/companies/", "POST", data=data)
        return {"company": encode(company), "message": "Company created successfully"}
    except Exception as e:
        return {"error": str(e), "message": "Failed to create company"}


async def update_company(company_id: str, data: Dict) -> Dict:
    """Update a company."""
    try:
        company = await make_django_request(
            f"/api/companies/{company_id}/", "PATCH", data=data
        )
        return {"company": encode(company), "message": "Company updated successfully"}
    except Exception as e:
        return {"error": str(e), "message": "Failed to update company"}


async def delete_company(company_id: str) -> Dict:
    """Delete a company."""
    try:
        result = await make_django_request(f"/api/companies/{company_id}/", "DELETE")
        return {"result": encode(result), "message": "Company deleted successfully"}
    except Exception as e:
        return {"error": str(e), "message": "Failed to delete company"}


async def import_companies(companies: list[Dict]) -> Dict:
    """Bulk create companies."""
    try:
        result = await make_django_request(
            "/api/companies/import/", "POST", data=companies
        )
        return {"result": encode(result), "message": "Companies imported successfully"}
    except Exception as e:
        return {"error": str(e), "message": "Failed to import companies"}


# Notes
async def list_notes(**filters) -> Dict:
    """List/search notes."""
    try:
        notes = await make_django_request(
            "/api/notes/", "GET", params=filters if filters else None
        )
        return {"notes": encode(notes), "message": "Notes retrieved successfully"}
    except Exception as e:
        return {"error": str(e), "message": "Failed to retrieve notes"}


async def get_note(note_id: str) -> Dict:
    """Retrieve a note by ID."""
    try:
        note = await make_django_request(f"/api/notes/{note_id}/", "GET")
        return {"note": encode(note), "message": "Note retrieved successfully"}
    except Exception as e:
        return {"error": str(e), "message": "Failed to retrieve note"}


async def create_note(data: Dict) -> Dict:
    """Create a new note."""
    try:
        note = await make_django_request("/api/notes/", "POST", data=data)
        return {"note": encode(note), "message": "Note created successfully"}
    except Exception as e:
        return {"error": str(e), "message": "Failed to create note"}


async def update_note(note_id: str, data: Dict) -> Dict:
    """Update a note."""
    try:
        note = await make_django_request(f"/api/notes/{note_id}/", "PATCH", data=data)
        return {"note": encode(note), "message": "Note updated successfully"}
    except Exception as e:
        return {"error": str(e), "message": "Failed to update note"}


async def delete_note(note_id: str) -> Dict:
    """Delete a note."""
    try:
        result = await make_django_request(f"/api/notes/{note_id}/", "DELETE")
        return {"result": encode(result), "message": "Note deleted successfully"}
    except Exception as e:
        return {"error": str(e), "message": "Failed to delete note"}


async def import_notes(notes: list[Dict]) -> Dict:
    """Bulk create notes."""
    try:
        result = await make_django_request("/api/notes/import/", "POST", data=notes)
        return {"result": encode(result), "message": "Notes imported successfully"}
    except Exception as e:
        return {"error": str(e), "message": "Failed to import notes"}


# People
async def list_people(**filters) -> Dict:
    """List/search people."""
    try:
        people = await make_django_request(
            "/api/people/", "GET", params=filters if filters else None
        )
        return {"people": encode(people), "message": "People retrieved successfully"}
    except Exception as e:
        return {"error": str(e), "message": "Failed to retrieve people"}


async def get_person(person_id: str) -> Dict:
    """Retrieve a person by ID."""
    try:
        person = await make_django_request(f"/api/people/{person_id}/", "GET")
        return {"person": encode(person), "message": "Person retrieved successfully"}
    except Exception as e:
        return {"error": str(e), "message": "Failed to retrieve person"}


async def get_person_context(person_id: str, sections: str = "all") -> Dict:
    """Get related data for a person."""
    try:
        context = await make_django_request(
            f"/api/people/{person_id}/context/ai/", "GET", params={"sections": sections}
        )
        return {
            "context": encode(context),
            "message": "Person context retrieved successfully",
        }
    except Exception as e:
        return {"error": str(e), "message": "Failed to retrieve person context"}


async def create_person(data: Dict) -> Dict:
    """Create a new person."""
    try:
        person = await make_django_request("/api/people/", "POST", data=data)
        return {"person": encode(person), "message": "Person created successfully"}
    except Exception as e:
        return {"error": str(e), "message": "Failed to create person"}


async def update_person(person_id: str, data: Dict) -> Dict:
    """Update a person."""
    try:
        person = await make_django_request(
            f"/api/people/{person_id}/", "PATCH", data=data
        )
        return {"person": encode(person), "message": "Person updated successfully"}
    except Exception as e:
        return {"error": str(e), "message": "Failed to update person"}


async def delete_person(person_id: str) -> Dict:
    """Delete a person."""
    try:
        result = await make_django_request(f"/api/people/{person_id}/", "DELETE")
        return {"result": encode(result), "message": "Person deleted successfully"}
    except Exception as e:
        return {"error": str(e), "message": "Failed to delete person"}


async def import_people(people: list[Dict], auto_create_company: bool = False) -> Dict:
    """Bulk create people."""
    try:
        if auto_create_company:
            data = {"data": people, "auto_create": {"company": True}}
        else:
            data = people
        result = await make_django_request("/api/people/import/", "POST", data=data)
        return {"result": encode(result), "message": "People imported successfully"}
    except Exception as e:
        return {"error": str(e), "message": "Failed to import people"}


# Search
async def global_search(q: str) -> Dict:
    """Perform a global search across People, Companies, Tasks, and Notes."""
    try:
        results = await make_django_request("/api/search/", "GET", params={"q": q})
        return {"results": encode(results), "message": "Search completed successfully"}
    except Exception as e:
        return {"error": str(e), "message": "Failed to perform search"}


# Tasks
async def list_tasks(**filters) -> Dict:
    """List/search tasks."""
    try:
        tasks = await make_django_request(
            "/api/tasks/", "GET", params=filters if filters else None
        )
        return {"tasks": encode(tasks), "message": "Tasks retrieved successfully"}
    except Exception as e:
        return {"error": str(e), "message": "Failed to retrieve tasks"}


async def get_task(task_id: str) -> Dict:
    """Retrieve a task by ID."""
    try:
        task = await make_django_request(f"/api/tasks/{task_id}/", "GET")
        return {"task": encode(task), "message": "Task retrieved successfully"}
    except Exception as e:
        return {"error": str(e), "message": "Failed to retrieve task"}


async def create_task(data: Dict) -> Dict:
    """Create a new task."""
    try:
        task = await make_django_request("/api/tasks/", "POST", data=data)
        return {"task": encode(task), "message": "Task created successfully"}
    except Exception as e:
        return {"error": str(e), "message": "Failed to create task"}


async def update_task(task_id: str, data: Dict) -> Dict:
    """Update a task."""
    try:
        task = await make_django_request(f"/api/tasks/{task_id}/", "PATCH", data=data)
        return {"task": encode(task), "message": "Task updated successfully"}
    except Exception as e:
        return {"error": str(e), "message": "Failed to update task"}


async def delete_task(task_id: str) -> Dict:
    """Delete a task."""
    try:
        result = await make_django_request(f"/api/tasks/{task_id}/", "DELETE")
        return {"result": encode(result), "message": "Task deleted successfully"}
    except Exception as e:
        return {"error": str(e), "message": "Failed to delete task"}


async def import_tasks(
    tasks: list[Dict], auto_create_related_person: bool = False
) -> Dict:
    """Bulk create tasks."""
    try:
        if auto_create_related_person:
            data = {"data": tasks, "auto_create": {"related_person": True}}
        else:
            data = tasks
        result = await make_django_request("/api/tasks/import/", "POST", data=data)
        return {"result": encode(result), "message": "Tasks imported successfully"}
    except Exception as e:
        return {"error": str(e), "message": "Failed to import tasks"}


# Activities
async def list_activities(**filters) -> Dict:
    """List/search activities."""
    try:
        activities = await make_django_request(
            "/api/activities/", "GET", params=filters if filters else None
        )
        return {
            "activities": encode(activities),
            "message": "Activities retrieved successfully",
        }
    except Exception as e:
        return {"error": str(e), "message": "Failed to retrieve activities"}


async def create_activity(data: Dict) -> Dict:
    """Create a new activity."""
    try:
        activity = await make_django_request("/api/activities/", "POST", data=data)
        return {
            "activity": encode(activity),
            "message": "Activity created successfully",
        }
    except Exception as e:
        return {"error": str(e), "message": "Failed to create activity"}


async def get_activity(activity_id: str) -> Dict:
    """Retrieve an activity by ID."""
    try:
        activity = await make_django_request(f"/api/activities/{activity_id}/", "GET")
        return {
            "activity": encode(activity),
            "message": "Activity retrieved successfully",
        }
    except Exception as e:
        return {"error": str(e), "message": "Failed to retrieve activity"}


async def update_activity(activity_id: str, data: Dict) -> Dict:
    """Update an activity."""
    try:
        activity = await make_django_request(
            f"/api/activities/{activity_id}/", "PATCH", data=data
        )
        return {
            "activity": encode(activity),
            "message": "Activity updated successfully",
        }
    except Exception as e:
        return {"error": str(e), "message": "Failed to update activity"}


async def delete_activity(activity_id: str) -> Dict:
    """Delete an activity."""
    try:
        result = await make_django_request(f"/api/activities/{activity_id}/", "DELETE")
        return {"result": encode(result), "message": "Activity deleted successfully"}
    except Exception as e:
        return {"error": str(e), "message": "Failed to delete activity"}


async def import_activities(
    activities: list[Dict],
    auto_create_related_person: bool = False,
    auto_create_related_company: bool = False,
) -> Dict:
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
        return {"result": encode(result), "message": "Activities imported successfully"}
    except Exception as e:
        return {"error": str(e), "message": "Failed to import activities"}


# Interaction Types
async def list_interaction_types(**filters) -> Dict:
    """List/search interaction types."""
    try:
        types = await make_django_request(
            "/api/interaction-types/", "GET", params=filters if filters else None
        )
        return {
            "interaction_types": encode(types),
            "message": "Interaction types retrieved successfully",
        }
    except Exception as e:
        return {"error": str(e), "message": "Failed to retrieve interaction types"}


async def create_interaction_type(data: Dict) -> Dict:
    """Create a new interaction type."""
    try:
        interaction_type = await make_django_request(
            "/api/interaction-types/", "POST", data=data
        )
        return {
            "interaction_type": encode(interaction_type),
            "message": "Interaction type created successfully",
        }
    except Exception as e:
        return {"error": str(e), "message": "Failed to create interaction type"}


async def get_interaction_type(type_id: str) -> Dict:
    """Retrieve an interaction type by ID."""
    try:
        interaction_type = await make_django_request(
            f"/api/interaction-types/{type_id}/", "GET"
        )
        return {
            "interaction_type": encode(interaction_type),
            "message": "Interaction type retrieved successfully",
        }
    except Exception as e:
        return {"error": str(e), "message": "Failed to retrieve interaction type"}


async def update_interaction_type(type_id: str, data: Dict) -> Dict:
    """Update an interaction type."""
    try:
        interaction_type = await make_django_request(
            f"/api/interaction-types/{type_id}/", "PATCH", data=data
        )
        return {
            "interaction_type": encode(interaction_type),
            "message": "Interaction type updated successfully",
        }
    except Exception as e:
        return {"error": str(e), "message": "Failed to update interaction type"}


async def delete_interaction_type(type_id: str) -> Dict:
    """Delete an interaction type."""
    try:
        result = await make_django_request(
            f"/api/interaction-types/{type_id}/", "DELETE"
        )
        return {
            "result": encode(result),
            "message": "Interaction type deleted successfully",
        }
    except Exception as e:
        return {"error": str(e), "message": "Failed to delete interaction type"}


# Interactions (Logs)
async def list_interactions(**filters) -> Dict:
    """List/search interactions."""
    try:
        interactions = await make_django_request(
            "/api/interactions/", "GET", params=filters if filters else None
        )
        return {
            "interactions": encode(interactions),
            "message": "Interactions retrieved successfully",
        }
    except Exception as e:
        return {"error": str(e), "message": "Failed to retrieve interactions"}


async def create_interaction(data: Dict) -> Dict:
    """Create a new interaction."""
    try:
        interaction = await make_django_request("/api/interactions/", "POST", data=data)
        return {
            "interaction": encode(interaction),
            "message": "Interaction created successfully",
        }
    except Exception as e:
        return {"error": str(e), "message": "Failed to create interaction"}


async def get_interaction(interaction_id: str) -> Dict:
    """Retrieve an interaction by ID."""
    try:
        interaction = await make_django_request(
            f"/api/interactions/{interaction_id}/", "GET"
        )
        return {
            "interaction": encode(interaction),
            "message": "Interaction retrieved successfully",
        }
    except Exception as e:
        return {"error": str(e), "message": "Failed to retrieve interaction"}


async def update_interaction(interaction_id: str, data: Dict) -> Dict:
    """Update an interaction."""
    try:
        interaction = await make_django_request(
            f"/api/interactions/{interaction_id}/", "PATCH", data=data
        )
        return {
            "interaction": encode(interaction),
            "message": "Interaction updated successfully",
        }
    except Exception as e:
        return {"error": str(e), "message": "Failed to update interaction"}


async def delete_interaction(interaction_id: str) -> Dict:
    """Delete an interaction."""
    try:
        result = await make_django_request(
            f"/api/interactions/{interaction_id}/", "DELETE"
        )
        return {"result": encode(result), "message": "Interaction deleted successfully"}
    except Exception as e:
        return {"error": str(e), "message": "Failed to delete interaction"}


async def import_interactions(
    interactions: list[Dict],
    auto_create_related_person: bool = False,
    auto_create_related_company: bool = False,
) -> Dict:
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
        result = await make_django_request(
            "/api/interactions/import/", "POST", data=data
        )
        return {
            "result": encode(result),
            "message": "Interactions imported successfully",
        }
    except Exception as e:
        return {"error": str(e), "message": "Failed to import interactions"}
