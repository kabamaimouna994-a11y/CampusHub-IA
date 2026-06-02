from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from core.config import settings


def _build_engine_kwargs() -> dict:
    """
    Retourne les kwargs du moteur selon la base de données utilisée.
    SQLite ne supporte pas pool_size / max_overflow.
    """
    url = settings.DATABASE_URL
    if url.startswith("sqlite"):
        return {
            "echo": settings.DEBUG,
            "connect_args": {"check_same_thread": False},
        }
    # PostgreSQL (ou autre SGBD)
    return {
        "echo": settings.DEBUG,
        "pool_size": 10,
        "max_overflow": 20,
        "pool_pre_ping": True,   # vérifie que la connexion est vivante
        "pool_recycle": 3600,    # recycle les connexions après 1h
    }


engine = create_async_engine(
    settings.DATABASE_URL,
    **_build_engine_kwargs(),
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def create_tables():
    """Crée toutes les tables en base de données."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    """Injecteur de session pour les routes FastAPI."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()