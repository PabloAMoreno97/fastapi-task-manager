import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.api.dependencies import get_session
from src.api.main import app
from src.core.rate_limiter import limiter
from src.db.base import Base
from src.db.models import User, Task, RefreshToken  # noqa: F401 — registers models with metadata

DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def client():
    # Reset rate limiter counters so tests don't accumulate toward the 10/min limit
    limiter._storage.reset()

    engine = create_async_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_session() -> AsyncSession:  # type: ignore[return]
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict:
    await client.post("/auth/register", json={
        "email": "fixture@example.com",
        "username": "fixtureuser",
        "password": "fixturepassword123",
    })
    resp = await client.post("/auth/login", json={
        "email": "fixture@example.com",
        "password": "fixturepassword123",
    })
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
