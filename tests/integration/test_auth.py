import pytest
from httpx import AsyncClient

REGISTER_URL = "/auth/register"
LOGIN_URL = "/auth/login"
REFRESH_URL = "/auth/refresh"

VALID_USER = {
    "email": "alice@example.com",
    "username": "alice",
    "password": "alicepassword123",
}


async def _register_and_login(client: AsyncClient, user: dict = VALID_USER) -> dict:
    await client.post(REGISTER_URL, json=user)
    resp = await client.post(LOGIN_URL, json={"email": user["email"], "password": user["password"]})
    return resp.json()


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    resp = await client.post(REGISTER_URL, json=VALID_USER)
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == VALID_USER["email"]
    assert body["username"] == VALID_USER["username"]
    assert "id" in body
    assert "hashed_password" not in body


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    await client.post(REGISTER_URL, json=VALID_USER)
    resp = await client.post(REGISTER_URL, json=VALID_USER)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_register_duplicate_username_different_email(client: AsyncClient):
    await client.post(REGISTER_URL, json=VALID_USER)
    resp = await client.post(REGISTER_URL, json={**VALID_USER, "email": "other@example.com"})
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_register_short_password_fails_validation(client: AsyncClient):
    resp = await client.post(REGISTER_URL, json={**VALID_USER, "password": "short"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    tokens = await _register_and_login(client)
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await client.post(REGISTER_URL, json=VALID_USER)
    resp = await client.post(LOGIN_URL, json={"email": VALID_USER["email"], "password": "WRONG"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    resp = await client.post(LOGIN_URL, json={"email": "ghost@example.com", "password": "doesnotmatter"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_returns_new_access_token(client: AsyncClient):
    tokens = await _register_and_login(client)
    resp = await client.post(REFRESH_URL, json={"refresh_token": tokens["refresh_token"]})
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    # Verify the new access token actually works
    tasks_resp = await client.get("/tasks", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert tasks_resp.status_code == 200


@pytest.mark.asyncio
async def test_refresh_token_cannot_be_reused(client: AsyncClient):
    tokens = await _register_and_login(client)
    await client.post(REFRESH_URL, json={"refresh_token": tokens["refresh_token"]})
    resp = await client.post(REFRESH_URL, json={"refresh_token": tokens["refresh_token"]})
    assert resp.status_code == 401
