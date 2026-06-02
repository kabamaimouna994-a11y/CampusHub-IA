"""
Tests pour les routes de mentorat (MentorLoop).

Règles métier importantes :
- Le mentor doit avoir un niveau SUPÉRIEUR au mentoré (B1→B2→B3→M1→M2)
- Seul le MENTOR peut créer/supprimer une session
- Le mentoré crée la demande de mentorat
"""
import pytest
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient


def _future_date(days=7) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


def _past_date(days=1) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


class TestMentorships:
    async def test_get_mentorships_empty(self, client: AsyncClient, auth_headers: dict):
        response = await client.get("/api/mentorat/", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    async def test_create_mentorship(self, client: AsyncClient, auth_headers: dict, mentor_user: dict):
        """Le mentoré (B2) contacte le mentor (M1) — hiérarchie respectée."""
        response = await client.post("/api/mentorat/", json={
            "mentor_id": mentor_user["id"]
        }, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert "id" in data

    async def test_create_mentorship_unknown_mentor(self, client: AsyncClient, auth_headers: dict):
        response = await client.post("/api/mentorat/", json={
            "mentor_id": 99999
        }, headers=auth_headers)
        assert response.status_code == 404

    async def test_get_mentorships_after_create(self, client: AsyncClient, auth_headers: dict, mentor_user: dict):
        await client.post("/api/mentorat/", json={
            "mentor_id": mentor_user["id"]
        }, headers=auth_headers)

        response = await client.get("/api/mentorat/", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()) >= 1


class TestMessages:
    async def _create_mentorship(self, client, auth_headers, mentor_user) -> int:
        """Le mentoré crée la demande."""
        res = await client.post("/api/mentorat/", json={
            "mentor_id": mentor_user["id"]
        }, headers=auth_headers)
        assert res.status_code == 201, res.text
        return res.json()["id"]

    async def test_send_message(self, client: AsyncClient, auth_headers: dict, mentor_user: dict):
        mentorship_id = await self._create_mentorship(client, auth_headers, mentor_user)
        response = await client.post(
            f"/api/mentorat/{mentorship_id}/messages",
            json={"content": "Bonjour, je voudrais un mentorat !"},
            headers=auth_headers
        )
        assert response.status_code == 201

    async def test_get_messages(self, client: AsyncClient, auth_headers: dict, mentor_user: dict):
        mentorship_id = await self._create_mentorship(client, auth_headers, mentor_user)

        await client.post(
            f"/api/mentorat/{mentorship_id}/messages",
            json={"content": "Premier message"},
            headers=auth_headers
        )

        response = await client.get(
            f"/api/mentorat/{mentorship_id}/messages",
            headers=auth_headers
        )
        assert response.status_code == 200
        messages = response.json()
        assert len(messages) == 1
        assert messages[0]["content"] == "Premier message"
        assert messages[0]["is_mine"] is True

    async def test_get_messages_unauthenticated(self, client: AsyncClient):
        response = await client.get("/api/mentorat/1/messages")
        assert response.status_code == 401

    async def test_send_message_unknown_mentorship(self, client: AsyncClient, auth_headers: dict):
        response = await client.post(
            "/api/mentorat/99999/messages",
            json={"content": "Message fantôme"},
            headers=auth_headers
        )
        assert response.status_code == 404


class TestSessions:
    async def _setup(self, client, auth_headers, mentor_user, mentor_headers) -> int:
        """
        Le mentoré crée la demande, on retourne l'id du mentorat.
        Les sessions sont créées par le mentor.
        """
        res = await client.post("/api/mentorat/", json={
            "mentor_id": mentor_user["id"]
        }, headers=auth_headers)
        assert res.status_code == 201, res.text
        return res.json()["id"]

    async def test_create_session_success(
        self, client: AsyncClient,
        auth_headers: dict, mentor_user: dict, mentor_headers: dict
    ):
        """Seul le mentor peut créer une session."""
        mentorship_id = await self._setup(client, auth_headers, mentor_user, mentor_headers)

        response = await client.post(
            f"/api/mentorat/{mentorship_id}/sessions",
            json={
                "scheduled_at": _future_date(),
                "duration_min": 60,
                "location": "Google Meet",
                "topic": "Introduction Python"
            },
            headers=mentor_headers  # ← le mentor crée la session
        )
        assert response.status_code == 201
        data = response.json()
        assert data["topic"] == "Introduction Python"
        assert data["status"] == "scheduled"

    async def test_mentee_cannot_create_session(
        self, client: AsyncClient,
        auth_headers: dict, mentor_user: dict, mentor_headers: dict
    ):
        """Le mentoré ne peut PAS créer une session — 403 attendu."""
        mentorship_id = await self._setup(client, auth_headers, mentor_user, mentor_headers)

        response = await client.post(
            f"/api/mentorat/{mentorship_id}/sessions",
            json={"scheduled_at": _future_date(), "duration_min": 60},
            headers=auth_headers  # ← le mentoré tente de créer
        )
        assert response.status_code == 403

    async def test_create_session_past_date(
        self, client: AsyncClient,
        auth_headers: dict, mentor_user: dict, mentor_headers: dict
    ):
        mentorship_id = await self._setup(client, auth_headers, mentor_user, mentor_headers)

        response = await client.post(
            f"/api/mentorat/{mentorship_id}/sessions",
            json={"scheduled_at": _past_date(), "duration_min": 60},
            headers=mentor_headers  # ← le mentor
        )
        assert response.status_code == 400
        assert "futur" in response.json()["detail"].lower()

    async def test_get_sessions(
        self, client: AsyncClient,
        auth_headers: dict, mentor_user: dict, mentor_headers: dict
    ):
        mentorship_id = await self._setup(client, auth_headers, mentor_user, mentor_headers)

        await client.post(
            f"/api/mentorat/{mentorship_id}/sessions",
            json={"scheduled_at": _future_date(days=3), "duration_min": 30, "topic": "Session test"},
            headers=mentor_headers
        )

        response = await client.get(
            f"/api/mentorat/{mentorship_id}/sessions",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert len(response.json()) >= 1

    async def test_delete_session(
        self, client: AsyncClient,
        auth_headers: dict, mentor_user: dict, mentor_headers: dict
    ):
        mentorship_id = await self._setup(client, auth_headers, mentor_user, mentor_headers)

        create_res = await client.post(
            f"/api/mentorat/{mentorship_id}/sessions",
            json={"scheduled_at": _future_date(days=5), "duration_min": 60, "topic": "À supprimer"},
            headers=mentor_headers
        )
        assert create_res.status_code == 201
        session_id = create_res.json()["id"]

        delete_res = await client.delete(
            f"/api/mentorat/{mentorship_id}/sessions/{session_id}",
            headers=mentor_headers
        )
        assert delete_res.status_code == 200

    async def test_create_session_unknown_mentorship(self, client: AsyncClient, mentor_headers: dict):
        response = await client.post(
            "/api/mentorat/99999/sessions",
            json={"scheduled_at": _future_date(), "duration_min": 60},
            headers=mentor_headers
        )
        assert response.status_code == 404
