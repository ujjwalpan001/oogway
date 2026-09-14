import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.database import Base, get_db
from app.config import settings

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture(scope="function")
async def db_session():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with SessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_health_endpoint(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "version" in data
    assert "checks" in data


@pytest.mark.asyncio
async def test_create_session(client):
    resp = await client.post("/sessions", json={"title": "Test session"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Test session"
    assert "id" in data
    assert "model_provider" in data


@pytest.mark.asyncio
async def test_list_sessions(client):
    await client.post("/sessions", json={"title": "Session 1"})
    await client.post("/sessions", json={"title": "Session 2"})
    resp = await client.get("/sessions")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_get_session(client):
    create_resp = await client.post("/sessions", json={"title": "My Session"})
    session_id = create_resp.json()["id"]
    resp = await client.get(f"/sessions/{session_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == session_id
    assert "messages" in resp.json()


@pytest.mark.asyncio
async def test_get_session_not_found(client):
    resp = await client.get("/sessions/nonexistent-id")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_session(client):
    create_resp = await client.post("/sessions", json={"title": "To Delete"})
    session_id = create_resp.json()["id"]
    del_resp = await client.delete(f"/sessions/{session_id}")
    assert del_resp.status_code == 204
    get_resp = await client.get(f"/sessions/{session_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_chat_requires_valid_session(client):
    resp = await client.post("/chat/stream", json={
        "session_id": "bad-session-id",
        "message": "Hello"
    })
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_chat_message_too_short(client):
    resp = await client.post("/chat/stream", json={
        "session_id": "any",
        "message": ""
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_root_endpoint(client):
    resp = await client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert "name" in data
    assert "version" in data
