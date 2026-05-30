from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from core.database import get_db
from core.security import get_current_user
from models.user import User
from models.club import Club, ClubMember

router = APIRouter()


class ClubCreate(BaseModel):
    name: str
    description: str
    icon: Optional[str] = None
    category: Optional[str] = None


@router.get("/")
async def get_clubs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Club).where(Club.is_active == True).options(selectinload(Club.members)))
    clubs = result.scalars().all()
    return [
        {"id": c.id, "name": c.name, "description": c.description, "icon": c.icon, "members_count": c.active_members_count}
        for c in clubs
    ]


@router.get("/kpis")
async def get_kpis(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Club).where(Club.is_active == True).options(selectinload(Club.members), selectinload(Club.events)))
    clubs = result.scalars().all()
    return {
        "total_clubs": len(clubs),
        "total_members": sum(c.active_members_count for c in clubs),
        "clubs": [{"id": c.id, "name": c.name, "icon": c.icon, "members_count": c.active_members_count, "events_count": len(c.events)} for c in clubs],
    }


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_club(data: ClubCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    club = Club(name=data.name, description=data.description, icon=data.icon, category=data.category, admin_id=current_user.id)
    db.add(club)
    await db.flush()
    member = ClubMember(club_id=club.id, user_id=current_user.id, role="président")
    db.add(member)
    return {"id": club.id, "message": "Club créé avec succès"}


@router.post("/{club_id}/join")
async def join_club(club_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Club).where(Club.id == club_id))
    club = result.scalar_one_or_none()
    if not club:
        raise HTTPException(status_code=404, detail="Club introuvable")

    existing = await db.execute(select(ClubMember).where(ClubMember.club_id == club_id, ClubMember.user_id == current_user.id))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Vous êtes déjà membre de ce club")

    member = ClubMember(club_id=club_id, user_id=current_user.id)
    db.add(member)
    return {"message": f"Vous avez rejoint le club {club.name}"}


@router.delete("/{club_id}/leave")
async def leave_club(club_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ClubMember).where(ClubMember.club_id == club_id, ClubMember.user_id == current_user.id))
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Vous n'êtes pas membre de ce club")
    await db.delete(member)
    return {"message": "Vous avez quitté le club"}