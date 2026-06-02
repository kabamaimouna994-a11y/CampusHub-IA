"""Test de validation de l'environnement CI"""
import pytest
from core.database import Base
from sqlalchemy import text

def test_imports():
    """Vérifie que toutes les dépendances sont importables"""
    import fastapi
    import sqlalchemy
    import aiosqlite
    import pytest_asyncio
    assert True

def test_database_config():
    """Vérifie que la configuration base de données est valide"""
    from core.database import DATABASE_URL
    assert DATABASE_URL is not None
    print(f"Database URL: {DATABASE_URL}")

def test_pytest_works():
    """Test simple qui passe toujours"""
    assert 1 + 1 == 2