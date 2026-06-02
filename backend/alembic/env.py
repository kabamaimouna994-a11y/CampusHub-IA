"""
Configuration Alembic — supporte SQLite (dev) et PostgreSQL (prod).
Détecte automatiquement le driver async et utilise un wrapper sync pour les migrations.
"""
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool, engine_from_config
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# ─── Import de la config et des modèles ───────────────────────────────────────
from core.config import settings
from core.database import Base

# Import de TOUS les modèles pour qu'Alembic les découvre
from models.user import User, UserRole, YearLevel
from models.skill import UserSkill, SkillLevel, SkillCategory
from models.mentorship import Mentorship, MentoringSession, MentorMessage
from models.project import Project, ProjectMember, ProjectApplication
from models.club import Club, ClubMember
from models.event import Event, EventRegistration
from models.certification import Certification

# ─── Config Alembic ───────────────────────────────────────────────────────────
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _get_sync_url(url: str) -> str:
    """
    Convertit une URL async en URL sync pour Alembic.
    Alembic ne supporte pas les drivers async nativement.
    """
    return (
        url
        .replace("sqlite+aiosqlite", "sqlite")
        .replace("postgresql+asyncpg", "postgresql+psycopg2")
    )


def run_migrations_offline() -> None:
    """
    Mode offline : génère le SQL sans connexion à la base.
    Utile pour review ou pour appliquer manuellement.
    """
    url = _get_sync_url(settings.DATABASE_URL)
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Mode online : se connecte à la base et applique les migrations.
    Utilise un moteur synchrone (requis par Alembic).
    """
    sync_url = _get_sync_url(settings.DATABASE_URL)

    connectable = engine_from_config(
        {"sqlalchemy.url": sync_url},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        do_run_migrations(connection)

    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()