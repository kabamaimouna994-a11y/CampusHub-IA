"""
Configuration globale des tests.
Utilise une base SQLite en mémoire pour isoler chaque session de test.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from core.database import Base, get_db
from main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session():
    async with test_engine.begin() as conn:
        async with AsyncSession(conn, expire_on_commit=False) as session:
            yield session
            await conn.rollback()


@pytest_asyncio.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# ─── Helpers ──────────────────────────────────────────────────────────────────

async def _register(client, email, password, first_name, last_name, year_level="B2", **kwargs):
    """Helper pour créer un utilisateur — retourne la réponse complète."""
    return await client.post("/api/auth/register", json={
        "email": email,
        "password": password,
        "first_name": first_name,
        "last_name": last_name,
        "year_level": year_level,
        **kwargs
    })


async def _login(client, email, password):
    """Helper pour se connecter — retourne les headers Authorization."""
    res = await client.post("/api/auth/login", json={
        "email": email,
        "password": password
    })
    assert res.status_code == 200, f"Login échoué: {res.text}"
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


# ─── Fixtures utilisateurs ────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def registered_user(client: AsyncClient) -> dict:
    """Crée et retourne un utilisateur enregistré."""
    res = await _register(client, "test@campushub.app", "TestPassword123!", "Test", "User")
    assert res.status_code == 201, res.text
    return res.json()


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient, registered_user: dict) -> dict:
    """Retourne les headers d'authentification."""
    return await _login(client, "test@campushub.app", "TestPassword123!")


@pytest_asyncio.fixture
async def mentor_user(client: AsyncClient) -> dict:
    """Crée un second utilisateur mentor et retourne ses données + id."""
    res = await _register(
        client, "mentor@campushub.app", "MentorPassword123!",
        "Mentor", "User", year_level="M1"
    )
    assert res.status_code == 201, res.text
    data = res.json()
    # La route register retourne user_id — on normalise en 'id' pour les tests
    data["id"] = data["user_id"]
    return data


@pytest_asyncio.fixture
async def mentor_headers(client: AsyncClient, mentor_user: dict) -> dict:
    """Retourne les headers d'authentification du mentor."""
    return await _login(client, "mentor@campushub.app", "MentorPassword123!")
