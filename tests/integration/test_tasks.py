import pytest
from httpx import AsyncClient

TASKS_URL = "/tasks"

SAMPLE_TASK = {
    "title": "Write unit tests",
    "description": "Cover all endpoints with pytest",
    "priority": "high",
}


@pytest.mark.asyncio
async def test_create_task_success(client: AsyncClient, auth_headers: dict):
    resp = await client.post(TASKS_URL, json=SAMPLE_TASK, headers=auth_headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == SAMPLE_TASK["title"]
    assert body["status"] == "pending"
    assert body["priority"] == "high"
    assert "id" in body


@pytest.mark.asyncio
async def test_create_task_unauthenticated(client: AsyncClient):
    resp = await client.post(TASKS_URL, json=SAMPLE_TASK)
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_list_tasks_returns_all(client: AsyncClient, auth_headers: dict):
    await client.post(TASKS_URL, json=SAMPLE_TASK, headers=auth_headers)
    await client.post(TASKS_URL, json={**SAMPLE_TASK, "title": "Second task"}, headers=auth_headers)
    resp = await client.get(TASKS_URL, headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    assert len(body["items"]) == 2


@pytest.mark.asyncio
async def test_list_tasks_filter_by_status(client: AsyncClient, auth_headers: dict):
    await client.post(TASKS_URL, json={**SAMPLE_TASK, "status": "done"}, headers=auth_headers)
    await client.post(TASKS_URL, json=SAMPLE_TASK, headers=auth_headers)
    resp = await client.get(TASKS_URL, params={"status": "done"}, headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["status"] == "done"


@pytest.mark.asyncio
async def test_get_task(client: AsyncClient, auth_headers: dict):
    create_resp = await client.post(TASKS_URL, json=SAMPLE_TASK, headers=auth_headers)
    task_id = create_resp.json()["id"]
    resp = await client.get(f"{TASKS_URL}/{task_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == task_id


@pytest.mark.asyncio
async def test_get_task_not_found(client: AsyncClient, auth_headers: dict):
    resp = await client.get(f"{TASKS_URL}/00000000-0000-0000-0000-000000000000", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_task_partial(client: AsyncClient, auth_headers: dict):
    create_resp = await client.post(TASKS_URL, json=SAMPLE_TASK, headers=auth_headers)
    task_id = create_resp.json()["id"]
    resp = await client.patch(
        f"{TASKS_URL}/{task_id}",
        json={"status": "in_progress"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "in_progress"
    assert body["title"] == SAMPLE_TASK["title"]  # unchanged


@pytest.mark.asyncio
async def test_delete_task(client: AsyncClient, auth_headers: dict):
    create_resp = await client.post(TASKS_URL, json=SAMPLE_TASK, headers=auth_headers)
    task_id = create_resp.json()["id"]
    del_resp = await client.delete(f"{TASKS_URL}/{task_id}", headers=auth_headers)
    assert del_resp.status_code == 204
    get_resp = await client.get(f"{TASKS_URL}/{task_id}", headers=auth_headers)
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_task_isolation_between_users(client: AsyncClient, auth_headers: dict):
    create_resp = await client.post(TASKS_URL, json=SAMPLE_TASK, headers=auth_headers)
    task_id = create_resp.json()["id"]

    # Register and login a second user
    await client.post("/auth/register", json={
        "email": "bob@example.com",
        "username": "bob",
        "password": "bobpassword123",
    })
    login_resp = await client.post("/auth/login", json={
        "email": "bob@example.com",
        "password": "bobpassword123",
    })
    bob_headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    resp = await client.get(f"{TASKS_URL}/{task_id}", headers=bob_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_tasks_pagination(client: AsyncClient, auth_headers: dict):
    for i in range(5):
        await client.post(TASKS_URL, json={**SAMPLE_TASK, "title": f"Task {i}"}, headers=auth_headers)
    resp = await client.get(TASKS_URL, params={"limit": 3, "offset": 0}, headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 5
    assert len(body["items"]) == 3
