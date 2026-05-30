from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.security import get_current_user
from models.user import User
from models.skill import UserSkill, SkillLevel, SkillCategory

router = APIRouter()


class SkillCreate(BaseModel):
    name: str
    category: SkillCategory = SkillCategory.OTHER
    level: SkillLevel = SkillLevel.BEGINNER
    description: Optional[str] = None


class SkillUpdate(BaseModel):
    level: Optional[SkillLevel] = None
    category: Optional[SkillCategory] = None
    description: Optional[str] = None


@router.get("/")
async def get_my_skills(current_user: User = Depends(get_current_user)):
    return [
        {
            "id": s.id,
            "name": s.name,
            "category": s.category.value,
            "level": s.level.value,
            "is_validated": s.is_validated,
            "description": s.description,
        }
        for s in current_user.skills
    ]


@router.post("/", status_code=status.HTTP_201_CREATED)
async def add_skill(data: SkillCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    existing = next((s for s in current_user.skills if s.name.lower() == data.name.lower()), None)
    if existing:
        raise HTTPException(status_code=400, detail="Compétence déjà présente dans votre profil")

    skill = UserSkill(
        user_id=current_user.id,
        name=data.name,
        category=data.category,
        level=data.level,
        description=data.description,
    )
    db.add(skill)
    await db.flush()
    return {"id": skill.id, "message": "Compétence ajoutée"}


@router.put("/{skill_id}")
async def update_skill(skill_id: int, data: SkillUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    skill = next((s for s in current_user.skills if s.id == skill_id), None)
    if not skill:
        raise HTTPException(status_code=404, detail="Compétence introuvable")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(skill, field, value)
    return {"message": "Compétence mise à jour"}


@router.delete("/{skill_id}")
async def delete_skill(skill_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    skill = next((s for s in current_user.skills if s.id == skill_id), None)
    if not skill:
        raise HTTPException(status_code=404, detail="Compétence introuvable")
    await db.delete(skill)
    return {"message": "Compétence supprimée"}