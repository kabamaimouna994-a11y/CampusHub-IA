"""
Tests pour les routes d'authentification.
"""
import pytest
from httpx import AsyncClient


class TestRegister:
    async def test_register_success(self, client: AsyncClient):
        response = await client.post("/api/auth/register", json={
            "email": "new@campushub.app",
            "password": "Password123!",
            "first_name": "Nouvel",
            "last_name": "Utilisateur",
            "year_level": "B1"
        })
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "user_id" in data
        assert "password" not in data

    async def test_register_duplicate_email(self, client: AsyncClient, registered_user: dict):
        response = await client.post("/api/auth/register", json={
            "email": "test@campushub.app",
            "password": "Password123!",
            "first_name": "Doublon",
            "last_name": "Test",
            "year_level": "B1"
        })
        assert response.status_code == 400

    async def test_register_invalid_email(self, client: AsyncClient):
        response = await client.post("/api/auth/register", json={
            "email": "pas-un-email",
            "password": "Password123!",
            "first_name": "Test",
            "last_name": "Test",
            "year_level": "B1"
        })
        assert response.status_code == 422

    async def test_register_missing_fields(self, client: AsyncClient):
        response = await client.post("/api/auth/register", json={
            "email": "test2@campushub.app"
        })
        assert response.status_code == 422

    async def test_register_invalid_year_level(self, client: AsyncClient):
        response = await client.post("/api/auth/register", json={
            "email": "test3@campushub.app",
            "password": "Password123!",
            "first_name": "Test",
            "last_name": "Test",
            "year_level": "X9"
        })
        assert response.status_code == 422


class TestLogin:
    async def test_login_success(self, client: AsyncClient, registered_user: dict):
        response = await client.post("/api/auth/login", json={
            "email": "test@campushub.app",
            "password": "TestPassword123!"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client: AsyncClient, registered_user: dict):
        response = await client.post("/api/auth/login", json={
            "email": "test@campushub.app",
            "password": "MauvaisMotDePasse"
        })
        assert response.status_code == 401

    async def test_login_unknown_email(self, client: AsyncClient):
        response = await client.post("/api/auth/login", json={
            "email": "inconnu@campushub.app",
            "password": "Password123!"
        })
        assert response.status_code == 401

    async def test_login_returns_refresh_token(self, client: AsyncClient, registered_user: dict):
        response = await client.post("/api/auth/login", json={
            "email": "test@campushub.app",
            "password": "TestPassword123!"
        })
        assert response.status_code == 200
        assert "refresh_token" in response.json()

    async def test_login_returns_user_info(self, client: AsyncClient, registered_user: dict):
        response = await client.post("/api/auth/login", json={
            "email": "test@campushub.app",
            "password": "TestPassword123!"
        })
        data = response.json()
        assert "user_id" in data
        assert "full_name" in data
        assert "year_level" in data


class TestGetMe:
    async def test_get_me_authenticated(self, client: AsyncClient, auth_headers: dict):
        response = await client.get("/api/users/me", headers=auth_headers)
        assert response.status_code == 200

    async def test_get_me_unauthenticated(self, client: AsyncClient):
        response = await client.get("/api/users/me")
        assert response.status_code == 401

    async def test_get_me_invalid_token(self, client: AsyncClient):
        response = await client.get("/api/users/me", headers={
            "Authorization": "Bearer token_invalide"
        })
        assert response.status_code == 401
