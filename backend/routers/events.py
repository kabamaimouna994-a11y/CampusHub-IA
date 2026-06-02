from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from core.database import get_db
from core.security import get_current_user
from models.user import User
from models.event import Event, EventRegistration

router = APIRouter()


class EventCreate(BaseModel):
    title: str
    description: str
    emoji: Optional[str] = None
    event_date: datetime
    location: Optional[str] = None
    event_type: str
    capacity: int = 50
    club_id: Optional[int] = None


def to_naive_utc(dt: datetime) -> datetime:
    """Convertit un datetime avec timezone en naive UTC."""
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


@router.get("/")
async def get_events(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Event).where(Event.is_published == True, Event.is_cancelled == False)
        .options(selectinload(Event.registrations))
        .order_by(Event.event_date)
    )
    events = result.scalars().all()
    return [
        {
            "id": e.id,
            "title": e.title,
            "description": e.description,
            "emoji": e.emoji,
            "event_date": e.event_date.isoformat(),
            "location": e.location,
            "event_type": e.event_type,
            "capacity": e.capacity,
            "registered_count": e.confirmed_registrations_count,
            "available_spots": e.available_spots,
            "fill_rate": round(e.fill_rate * 100),
            "organizer_id": e.organizer_id,  # ⭐ AJOUTÉ
        }
        for e in events
    ]


@router.get("/recommended")
async def get_recommended_events(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Event).where(Event.is_published == True, Event.is_cancelled == False)
        .options(selectinload(Event.registrations))
        .order_by(Event.event_date)
    )
    events = result.scalars().all()

    user_skills = {s.name.lower() for s in current_user.skills}
    scored = []
    for e in events:
        tags = set((e.skill_tags or "").lower().split(","))
        overlap = len(user_skills & tags) if tags else 0
        score = 50 + overlap * 10
        scored.append({
            "id": e.id,
            "title": e.title,
            "emoji": e.emoji,
            "event_date": e.event_date.isoformat(),
            "event_type": e.event_type,
            "capacity": e.capacity,
            "registered_count": e.confirmed_registrations_count,
            "available_spots": e.available_spots,
            "match_score": min(score, 99),
            "organizer_id": e.organizer_id,  # ⭐ AJOUTÉ
        })
    scored.sort(key=lambda x: x["match_score"], reverse=True)
    return scored


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_event(
    data: EventCreate, 
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    event_date_naive = to_naive_utc(data.event_date)
    
    event = Event(
        title=data.title,
        description=data.description,
        emoji=data.emoji,
        event_date=event_date_naive,
        location=data.location,
        event_type=data.event_type,
        capacity=data.capacity,
        club_id=data.club_id,
        organizer_id=current_user.id,
        is_published=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(event)
    await db.flush()
    return {"id": event.id, "message": "Événement créé", "organizer_id": current_user.id}


@router.post("/{event_id}/register")
async def register_event(
    event_id: int, 
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Event).where(Event.id == event_id).options(selectinload(Event.registrations)))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Événement introuvable")

    existing = next((r for r in event.registrations if r.user_id == current_user.id and r.status == "confirmed"), None)
    if existing:
        raise HTTPException(status_code=400, detail="Vous êtes déjà inscrit")

    reg = EventRegistration(event_id=event_id, user_id=current_user.id)
    db.add(reg)
    await db.commit()
    return {"message": "Inscription confirmée"}


@router.delete("/{event_id}/register")
async def unregister_event(
    event_id: int, 
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(EventRegistration).where(EventRegistration.event_id == event_id, EventRegistration.user_id == current_user.id)
    )
    reg = result.scalar_one_or_none()
    if not reg:
        raise HTTPException(status_code=404, detail="Inscription introuvable")
    await db.delete(reg)
    await db.commit()
    return {"message": "Désinscription effectuée"}


# ─────────────────────────────────────────────────────────────
# DELETE /events/{event_id} (Supprimer un événement)
# ─────────────────────────────────────────────────────────────

@router.delete("/{event_id}")
async def delete_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Supprimer un événement - seul l'organisateur peut le faire"""
    
    result = await db.execute(
        select(Event).where(Event.id == event_id)
    )
    event = result.scalar_one_or_none()
    
    if not event:
        raise HTTPException(status_code=404, detail="Événement non trouvé")
    
    if event.organizer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Seul l'organisateur peut supprimer cet événement")
    
    await db.delete(event)
    await db.commit()
    
    return {"message": "Événement supprimé avec succès"}