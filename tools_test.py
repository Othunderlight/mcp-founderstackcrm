"""
Integration tests for MCP tools.
Run: uv run python tools_test.py
"""

import asyncio
import uuid
import httpx

BASE_URL = "http://127.0.0.1:8000"
API_KEY = "9N8o03ss3Wi7pIT1669xg1UMpsmBdp2v7mNFRL-l4NY"


def is_api_key(token: str) -> bool:
    return bool(token) and not token.count(".") == 2


async def make_django_request(endpoint, method="GET", data=None, params=None, user_token=None):
    url = f"{BASE_URL}{endpoint}"
    headers = {}

    token = user_token
    if token:
        if is_api_key(token):
            headers["Authorization"] = f"Api-Key {token}"
        else:
            headers["Authorization"] = f"Bearer {token}"

    try:
        async with httpx.AsyncClient() as client:
            if method.upper() == "GET":
                response = await client.get(url, headers=headers, params=params, timeout=30.0)
            elif method.upper() == "POST":
                response = await client.post(url, json=data, headers=headers, params=params, timeout=30.0)
            elif method.upper() == "PATCH":
                response = await client.patch(url, json=data, headers=headers, params=params, timeout=30.0)
            elif method.upper() == "PUT":
                response = await client.put(url, json=data, headers=headers, params=params, timeout=30.0)
            elif method.upper() == "DELETE":
                response = await client.delete(url, headers=headers, params=params, timeout=30.0)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            # DELETE returns 204 No Content
            if response.status_code == 204:
                return {}
            return response.json()

    except httpx.HTTPStatusError as e:
        print(f"Django API error: {e.response.status_code} - {e.response.text}")
        raise Exception(f"Django API error: {e.response.status_code}")
    except Exception as e:
        print(f"Request to Django failed: {e}")
        raise Exception(f"Request to Django backend failed: {str(e)}")


# ============== COMPANIES ==============

async def test_list_companies():
    result = await make_django_request("/api/companies/", "GET", params={"limit": 1}, user_token=API_KEY)
    print(f"list_companies: OK - {result.get('count')} companies")
    return "PASS"


async def test_create_company():
    company_data = {"name": f"Test Co {uuid.uuid4().hex[:6]}", "domain": f"{uuid.uuid4().hex[:6]}.com"}
    result = await make_django_request("/api/companies/", "POST", data=company_data, user_token=API_KEY)
    company_id = result.get("id")
    print(f"create_company: OK - id={company_id}")
    
    # Get
    result = await make_django_request(f"/api/companies/{company_id}/", "GET", user_token=API_KEY)
    print(f"get_company: OK")
    
    # Update
    result = await make_django_request(f"/api/companies/{company_id}/", "PATCH", data={"name": "Updated"}, user_token=API_KEY)
    print(f"update_company: OK")
    
    # Delete
    await make_django_request(f"/api/companies/{company_id}/", "DELETE", user_token=API_KEY)
    print(f"delete_company: OK")
    return "PASS"


# ============== PEOPLE ==============

async def test_list_people():
    result = await make_django_request("/api/people/", "GET", params={"limit": 1}, user_token=API_KEY)
    print(f"list_people: OK - {result.get('count')} people")
    return "PASS"


async def test_create_person():
    person_data = {"name": f"Test Person {uuid.uuid4().hex[:6]}", "email": f"test{uuid.uuid4().hex[:6]}@test.com"}
    result = await make_django_request("/api/people/", "POST", data=person_data, user_token=API_KEY)
    person_id = result.get("id")
    print(f"create_person: OK - id={person_id}")
    
    # Get
    result = await make_django_request(f"/api/people/{person_id}/", "GET", user_token=API_KEY)
    print(f"get_person: OK")
    
    # Update
    result = await make_django_request(f"/api/people/{person_id}/", "PATCH", data={"job_title": "Tester"}, user_token=API_KEY)
    print(f"update_person: OK")
    
    # Delete
    await make_django_request(f"/api/people/{person_id}/", "DELETE", user_token=API_KEY)
    print(f"delete_person: OK")
    return "PASS"


async def test_get_person_context():
    # First get a person_id
    result = await make_django_request("/api/people/", "GET", params={"limit": 1}, user_token=API_KEY)
    if result.get("results"):
        person_id = result["results"][0]["id"]
        context = await make_django_request(f"/api/people/{person_id}/context/", "GET", params={"sections": "all"}, user_token=API_KEY)
        print(f"get_person_context: OK")
        return "PASS"
    print("get_person_context: SKIP - no people")
    return "SKIP"


# ============== TASKS ==============

async def test_list_tasks():
    result = await make_django_request("/api/tasks/", "GET", params={"limit": 1}, user_token=API_KEY)
    print(f"list_tasks: OK - {result.get('count')} tasks")
    return "PASS"


async def test_create_task():
    task_data = {"title": f"Test Task {uuid.uuid4().hex[:6]}", "status": "Todo"}
    result = await make_django_request("/api/tasks/", "POST", data=task_data, user_token=API_KEY)
    task_id = result.get("id")
    print(f"create_task: OK - id={task_id}")
    
    # Get
    result = await make_django_request(f"/api/tasks/{task_id}/", "GET", user_token=API_KEY)
    print(f"get_task: OK")
    
    # Update
    result = await make_django_request(f"/api/tasks/{task_id}/", "PATCH", data={"status": "Done"}, user_token=API_KEY)
    print(f"update_task: OK")
    
    # Delete
    await make_django_request(f"/api/tasks/{task_id}/", "DELETE", user_token=API_KEY)
    print(f"delete_task: OK")
    return "PASS"


# ============== NOTES ==============

async def test_list_notes():
    result = await make_django_request("/api/notes/", "GET", params={"limit": 1}, user_token=API_KEY)
    print(f"list_notes: OK - {result.get('count')} notes")
    return "PASS"


async def test_create_note():
    note_data = {"title": f"Test Note {uuid.uuid4().hex[:6]}", "content": "test content"}
    result = await make_django_request("/api/notes/", "POST", data=note_data, user_token=API_KEY)
    note_id = result.get("id")
    print(f"create_note: OK - id={note_id}")
    
    # Get
    result = await make_django_request(f"/api/notes/{note_id}/", "GET", user_token=API_KEY)
    print(f"get_note: OK")
    
    # Update
    result = await make_django_request(f"/api/notes/{note_id}/", "PATCH", data={"content": "updated"}, user_token=API_KEY)
    print(f"update_note: OK")
    
    # Delete
    await make_django_request(f"/api/notes/{note_id}/", "DELETE", user_token=API_KEY)
    print(f"delete_note: OK")
    return "PASS"


# ============== ACTIVITIES ==============

async def test_list_activities():
    result = await make_django_request("/api/activities/", "GET", params={"limit": 1}, user_token=API_KEY)
    print(f"list_activities: OK - {result.get('count')} activities")
    return "PASS"


async def test_create_activity():
    activity_data = {"type": "call", "title": f"Test Activity {uuid.uuid4().hex[:6]}", "content": "Test content"}
    result = await make_django_request("/api/activities/", "POST", data=activity_data, user_token=API_KEY)
    activity_id = result.get("id")
    print(f"create_activity: OK - id={activity_id}")
    
    # Get
    result = await make_django_request(f"/api/activities/{activity_id}/", "GET", user_token=API_KEY)
    print(f"get_activity: OK")
    
    # Update
    result = await make_django_request(f"/api/activities/{activity_id}/", "PATCH", data={"title": "Updated"}, user_token=API_KEY)
    print(f"update_activity: OK")
    
    # Delete
    await make_django_request(f"/api/activities/{activity_id}/", "DELETE", user_token=API_KEY)
    print(f"delete_activity: OK")
    return "PASS"


# ============== SEARCH ==============

async def test_global_search():
    result = await make_django_request("/api/search/", "GET", params={"q": "test"}, user_token=API_KEY)
    print(f"global_search: OK - {len(result.get('results', []))} results")
    return "PASS"


# ============== INTERACTION TYPES ==============

async def test_list_interaction_types():
    result = await make_django_request("/api/interaction-types/", "GET", params={"limit": 1}, user_token=API_KEY)
    print(f"list_interaction_types: OK - {result.get('count')} types")
    return "PASS"


async def test_create_interaction_type():
    type_data = {"name": f"Test Type {uuid.uuid4().hex[:6]}"}
    result = await make_django_request("/api/interaction-types/", "POST", data=type_data, user_token=API_KEY)
    type_id = result.get("id")
    print(f"create_interaction_type: OK - id={type_id}")
    
    # Get
    result = await make_django_request(f"/api/interaction-types/{type_id}/", "GET", user_token=API_KEY)
    print(f"get_interaction_type: OK")
    
    # Update
    result = await make_django_request(f"/api/interaction-types/{type_id}/", "PATCH", data={"description": "test"}, user_token=API_KEY)
    print(f"update_interaction_type: OK")
    
    # Delete
    await make_django_request(f"/api/interaction-types/{type_id}/", "DELETE", user_token=API_KEY)
    print(f"delete_interaction_type: OK")
    return "PASS"


# ============== INTERACTIONS ==============

async def test_list_interactions():
    result = await make_django_request("/api/interactions/", "GET", params={"limit": 1}, user_token=API_KEY)
    print(f"list_interactions: OK - {result.get('count')} interactions")
    return "PASS"


async def test_create_interaction():
    # First get an interaction type
    types = await make_django_request("/api/interaction-types/", "GET", params={"limit": 1}, user_token=API_KEY)
    if types.get("results"):
        type_id = types["results"][0]["id"]
    else:
        # Create one
        type_data = {"name": f"Test Type {uuid.uuid4().hex[:6]}"}
        type_result = await make_django_request("/api/interaction-types/", "POST", data=type_data, user_token=API_KEY)
        type_id = type_result.get("id")
    
    interaction_data = {"interaction_type": type_id, "notes": "test note"}
    result = await make_django_request("/api/interactions/", "POST", data=interaction_data, user_token=API_KEY)
    interaction_id = result.get("id")
    print(f"create_interaction: OK - id={interaction_id}")
    
    # Get
    result = await make_django_request(f"/api/interactions/{interaction_id}/", "GET", user_token=API_KEY)
    print(f"get_interaction: OK")
    
    # Update
    result = await make_django_request(f"/api/interactions/{interaction_id}/", "PATCH", data={"notes": "updated"}, user_token=API_KEY)
    print(f"update_interaction: OK")
    
    # Delete
    await make_django_request(f"/api/interactions/{interaction_id}/", "DELETE", user_token=API_KEY)
    print(f"delete_interaction: OK")
    return "PASS"


# ============== RUN ALL ==============

async def run_all_tests():
    print("=" * 60)
    print("MCP Tools Integration Tests")
    print("=" * 60)
    
    tests = [
        ("list_companies", test_list_companies),
        ("create/get/update/delete company", test_create_company),
        ("list_people", test_list_people),
        ("create/get/update/delete person", test_create_person),
        ("get_person_context", test_get_person_context),
        ("list_tasks", test_list_tasks),
        ("create/get/update/delete task", test_create_task),
        ("list_notes", test_list_notes),
        ("create/get/update/delete note", test_create_note),
        ("list_activities", test_list_activities),
        ("create/get/update/delete activity", test_create_activity),
        ("global_search", test_global_search),
        ("list_interaction_types", test_list_interaction_types),
        ("create/get/update/delete interaction_type", test_create_interaction_type),
        ("list_interactions", test_list_interactions),
        ("create/get/update/delete interaction", test_create_interaction),
    ]
    
    results = {}
    for name, test_fn in tests:
        print(f"\n--- {name} ---")
        try:
            results[name] = await test_fn()
        except Exception as e:
            results[name] = f"FAIL: {e}"
            print(f"Error: {e}")
    
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    passed = sum(1 for v in results.values() if v == "PASS")
    skipped = sum(1 for v in results.values() if v == "SKIP")
    failed = len(results) - passed - skipped
    for name, status in results.items():
        print(f"  {name}: {status}")
    print(f"\nTotal: {len(results)} | Passed: {passed} | Skipped: {skipped} | Failed: {failed}")


if __name__ == "__main__":
    asyncio.run(run_all_tests())