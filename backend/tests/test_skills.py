"""
Tests pour les routes de compétences (SkillShare).
Les routes skills sont déclarées avec un slash final (/),
on utilise follow_redirects=True pour éviter les 307.
"""
import pytest
from httpx import AsyncClient


class TestSkills:
    async def test_get_skills_empty(self, client: AsyncClient, auth_headers: dict):
        response = await client.get("/api/skills/", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    async def test_create_skill_success(self, client: AsyncClient, auth_headers: dict):
        response = await client.post("/api/skills/", json={
            "name": "Python",
            "category": "Développement",
            "level": "avancé"
        }, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert "id" in data

    async def test_create_skill_missing_name(self, client: AsyncClient, auth_headers: dict):
        response = await client.post("/api/skills/", json={
            "category": "Développement",
            "level": "avancé"
        }, headers=auth_headers)
        assert response.status_code == 422

    async def test_create_skill_unauthenticated(self, client: AsyncClient):
        response = await client.post("/api/skills/", json={
            "name": "Python",
            "category": "Développement",
            "level": "avancé"
        })
        assert response.status_code == 401

    async def test_get_skills_after_create(self, client: AsyncClient, auth_headers: dict):
        await client.post("/api/skills/", json={
            "name": "React",
            "category": "Développement",
            "level": "intermédiaire"
        }, headers=auth_headers)

        response = await client.get("/api/skills/", headers=auth_headers)
        assert response.status_code == 200
        names = [s["name"] for s in response.json()]
        assert "React" in names

    async def test_update_skill_level(self, client: AsyncClient, auth_headers: dict):
        create_res = await client.post("/api/skills/", json={
            "name": "Docker",
            "category": "Développement",
            "level": "débutant"
        }, headers=auth_headers)
        assert create_res.status_code == 201
        skill_id = create_res.json()["id"]

        update_res = await client.put(f"/api/skills/{skill_id}", json={
            "level": "intermédiaire"
        }, headers=auth_headers)
        assert update_res.status_code == 200

    async def test_delete_skill(self, client: AsyncClient, auth_headers: dict):
        create_res = await client.post("/api/skills/", json={
            "name": "À supprimer",
            "category": "Autre",
            "level": "débutant"
        }, headers=auth_headers)
        assert create_res.status_code == 201
        skill_id = create_res.json()["id"]

        delete_res = await client.delete(f"/api/skills/{skill_id}", headers=auth_headers)
        assert delete_res.status_code == 200

        get_res = await client.get("/api/skills/", headers=auth_headers)
        ids = [s["id"] for s in get_res.json()]
        assert skill_id not in ids

    async def test_delete_other_user_skill(
        self, client: AsyncClient, auth_headers: dict,
        mentor_user: dict, mentor_headers: dict
    ):
        """Un utilisateur ne peut pas supprimer les compétences d'un autre."""
        create_res = await client.post("/api/skills/", json={
            "name": "Compétence du mentor",
            "category": "Data & IA",
            "level": "expert"
        }, headers=mentor_headers)
        assert create_res.status_code == 201
        skill_id = create_res.json()["id"]

        delete_res = await client.delete(f"/api/skills/{skill_id}", headers=auth_headers)
        assert delete_res.status_code in [403, 404]
