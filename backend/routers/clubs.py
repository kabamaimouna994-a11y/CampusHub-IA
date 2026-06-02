from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from core.database import get_db
from core.security import get_current_user
from models.user import User
from models.club import Club, ClubMember

router = APIRouter()


class ClubCreate(BaseModel):
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    category: Optional[str] = None


class ClubResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    icon: Optional[str]
    category: Optional[str]
    member_count: int
    is_member: bool = False
    events_count: int = 0
    admin_id: int  # ⭐ AJOUTÉ
    created_at: Optional[str] = None


@router.get("/", response_model=List[ClubResponse])
async def get_clubs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Récupère tous les clubs avec le statut d'adhésion de l'utilisateur"""
    
    result = await db.execute(
        select(Club).where(Club.is_active == True).options(
            selectinload(Club.members),
            selectinload(Club.events)
        )
    )
    clubs = result.scalars().all()
    
    user_memberships = await db.execute(
        select(ClubMember.club_id).where(
            ClubMember.user_id == current_user.id, 
            ClubMember.is_active == True
        )
    )
    member_club_ids = {row[0] for row in user_memberships.fetchall()}
    
    response = []
    for club in clubs:
        response.append(ClubResponse(
            id=club.id,
            name=club.name,
            description=club.description,
            icon=club.icon,
            category=club.category,
            member_count=club.active_members_count,
            is_member=club.id in member_club_ids,
            events_count=len(club.events) if club.events else 0,
            admin_id=club.admin_id,  # ⭐ AJOUTÉ
            created_at=club.created_at.isoformat() if club.created_at else None
        ))
    
    return response


@router.get("/kpis")
async def get_kpis(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Récupère les KPIs des clubs"""
    
    total_clubs = await db.execute(select(func.count(Club.id)).where(Club.is_active == True))
    total_clubs = total_clubs.scalar() or 0
    
    active_members = await db.execute(
        select(func.count(ClubMember.user_id.distinct())).where(ClubMember.is_active == True)
    )
    active_members = active_members.scalar() or 0
    
    top_clubs_result = await db.execute(
        select(Club.id, Club.name, Club.icon, func.count(ClubMember.id).label("member_count"))
        .join(ClubMember, Club.id == ClubMember.club_id)
        .where(Club.is_active == True, ClubMember.is_active == True)
        .group_by(Club.id)
        .order_by(func.count(ClubMember.id).desc())
        .limit(5)
    )
    top_clubs = [
        {"id": row[0], "name": row[1], "icon": row[2], "members": row[3]}
        for row in top_clubs_result.fetchall()
    ]
    
    return {
        "total_clubs": total_clubs,
        "active_members": active_members,
        "top_clubs": top_clubs
    }


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_club(
    data: ClubCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Crée un nouveau club et ajoute le créateur comme président"""
    
    existing = await db.execute(select(Club).where(Club.name == data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Un club avec ce nom existe déjà")
    
    club = Club(
        name=data.name,
        description=data.description,
        icon=data.icon or "🏛️",
        category=data.category,
        admin_id=current_user.id,
        is_active=True
    )
    db.add(club)
    await db.flush()
    
    member = ClubMember(
        club_id=club.id,
        user_id=current_user.id,
        role="président",
        is_active=True
    )
    db.add(member)
    await db.commit()
    await db.refresh(club)
    
    return {
        "id": club.id,
        "name": club.name,
        "admin_id": club.admin_id,  # ⭐ AJOUTÉ
        "message": f"Club '{club.name}' créé avec succès"
    }


@router.post("/{club_id}/join")
async def join_club(
    club_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Rejoindre un club"""
    
    result = await db.execute(select(Club).where(Club.id == club_id, Club.is_active == True))
    club = result.scalar_one_or_none()
    if not club:
        raise HTTPException(status_code=404, detail="Club introuvable")
    
    existing = await db.execute(
        select(ClubMember).where(
            ClubMember.club_id == club_id,
            ClubMember.user_id == current_user.id,
            ClubMember.is_active == True
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Vous êtes déjà membre de ce club")
    
    member = ClubMember(
        club_id=club_id,
        user_id=current_user.id,
        role="member",
        is_active=True
    )
    db.add(member)
    await db.commit()
    
    return {"message": f"Vous avez rejoint le club {club.name}"}


@router.delete("/{club_id}/leave")
async def leave_club(
    club_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Quitter un club"""
    
    result = await db.execute(
        select(ClubMember).where(
            ClubMember.club_id == club_id,
            ClubMember.user_id == current_user.id,
            ClubMember.is_active == True
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Vous n'êtes pas membre de ce club")
    
    if member.role == "président":
        other_members = await db.execute(
            select(func.count(ClubMember.id)).where(
                ClubMember.club_id == club_id,
                ClubMember.user_id != current_user.id,
                ClubMember.is_active == True
            )
        )
        if other_members.scalar() > 0:
            raise HTTPException(
                status_code=400, 
                detail="Vous êtes président. Transférez d'abord la présidence ou supprimez le club."
            )
    
    member.is_active = False
    await db.commit()
    
    return {"message": "Vous avez quitté le club"}


# ─────────────────────────────────────────────────────────────
# DELETE /clubs/{club_id} (Supprimer un club)
# ─────────────────────────────────────────────────────────────

@router.delete("/{club_id}")
async def delete_club(
    club_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Supprimer un club - seul l'administrateur peut le faire"""
    
    result = await db.execute(
        select(Club).where(Club.id == club_id)
    )
    club = result.scalar_one_or_none()
    
    if not club:
        raise HTTPException(status_code=404, detail="Club non trouvé")
    
    if club.admin_id != current_user.id:
        raise HTTPException(status_code=403, detail="Seul l'administrateur du club peut le supprimer")
    
    await db.delete(club)
    await db.commit()
    
    return {"message": "Club supprimé avec succès"}