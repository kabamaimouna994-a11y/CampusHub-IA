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
from models.mentorship import Mentorship, MentoringSession, MentorMessage


def _ensure_aware(dt: datetime) -> datetime:
    """S'assure que le datetime est timezone-aware (UTC)."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


# ⭐ ORDRE DES NIVEAUX POUR LE MENTORAT ⭐
LEVEL_ORDER = {
    "B1": 1,
    "B2": 2,
    "B3": 3,
    "M1": 4,
    "M2": 5
}


router = APIRouter()


class MentorshipCreate(BaseModel):
    mentor_id: int
    goals: Optional[str] = None


class SessionCreate(BaseModel):
    scheduled_at: datetime
    duration_min: int = 60
    location: Optional[str] = None
    topic: Optional[str] = None


class SessionFeedback(BaseModel):
    rating: int
    feedback: Optional[str] = None


class SessionUpdate(BaseModel):
    status: Optional[str] = None
    location: Optional[str] = None
    topic: Optional[str] = None
    scheduled_at: Optional[datetime] = None


class MessageCreate(BaseModel):
    content: str


# ========== MENTORATS ==========

@router.get("/")
async def get_my_mentorships(
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    """Récupère toutes les relations de mentorat de l'utilisateur"""
    
    stmt = select(Mentorship).where(
        (Mentorship.mentor_id == current_user.id) | (Mentorship.mentee_id == current_user.id)
    ).options(selectinload(Mentorship.mentor), selectinload(Mentorship.mentee))
    result = await db.execute(stmt)
    mentorships = result.scalars().all()

    output = []
    for m in mentorships:
        if m.mentor_id == current_user.id:
            partner = m.mentee
            role = "mentor"
        else:
            partner = m.mentor
            role = "mentoré"
        
        output.append({
            "id": m.id,
            "role": role,
            "partner_name": partner.full_name,
            "partner_year_level": partner.year_level.value if partner.year_level else None,
            "status": m.status,
        })
    return output


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_mentorship(
    data: MentorshipCreate, 
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    """Crée une relation de mentorat - ⭐ Vérifie la hiérarchie des niveaux ⭐"""
    
    result = await db.execute(select(User).where(User.id == data.mentor_id))
    mentor = result.scalar_one_or_none()
    if not mentor:
        raise HTTPException(status_code=404, detail="Mentor introuvable")
    
    # ⭐ VÉRIFICATION DE LA HIÉRARCHIE ⭐
    mentee_level = current_user.year_level.value if current_user.year_level else "B1"
    mentor_level = mentor.year_level.value if mentor.year_level else "B1"
    
    mentee_order = LEVEL_ORDER.get(mentee_level, 1)
    mentor_order = LEVEL_ORDER.get(mentor_level, 1)
    
    if mentor_order <= mentee_order:
        raise HTTPException(
            status_code=400, 
            detail=f"Le mentor doit avoir un niveau supérieur. "
                   f"Votre niveau: {mentee_level}, Niveau du mentor: {mentor_level}. "
                   f"Hiérarchie acceptée: B1 → B2 → B3 → M1 → M2"
        )
    
    # Vérifier si une relation existe déjà
    existing = await db.execute(
        select(Mentorship).where(
            Mentorship.mentor_id == data.mentor_id,
            Mentorship.mentee_id == current_user.id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Vous avez déjà contacté ce mentor")
    
    mentorship = Mentorship(
        mentor_id=data.mentor_id, 
        mentee_id=current_user.id, 
        goals=data.goals,
        status="pending"
    )
    db.add(mentorship)
    await db.flush()
    
    return {
        "id": mentorship.id, 
        "mentor_name": mentor.full_name, 
        "mentor_level": mentor_level,
        "message": "Demande de mentorat envoyée"
    }


# ========== MESSAGES ==========

@router.post("/{mentorship_id}/messages", status_code=status.HTTP_201_CREATED)
async def send_message(
    mentorship_id: int, 
    data: MessageCreate, 
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Mentorship).where(Mentorship.id == mentorship_id))
    mentorship = result.scalar_one_or_none()
    if not mentorship:
        raise HTTPException(status_code=404, detail="Relation introuvable")

    message = MentorMessage(mentorship_id=mentorship_id, sender_id=current_user.id, content=data.content)
    db.add(message)
    await db.flush()
    return {"id": message.id, "message": "Message envoyé"}


@router.get("/{mentorship_id}/messages")
async def get_messages(
    mentorship_id: int, 
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Mentorship)
        .where(Mentorship.id == mentorship_id)
        .options(selectinload(Mentorship.messages))
    )
    mentorship = result.scalar_one_or_none()
    if not mentorship:
        raise HTTPException(status_code=404, detail="Relation introuvable")

    return [
        {
            "id": m.id,
            "sender_id": m.sender_id,
            "content": m.content,
            "sent_at": m.sent_at.isoformat(),
            "is_mine": m.sender_id == current_user.id,
            "is_read": m.is_read
        }
        for m in mentorship.messages
    ]


@router.put("/{mentorship_id}/messages/{message_id}/read")
async def mark_message_as_read(
    mentorship_id: int,
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MentorMessage).where(
            MentorMessage.id == message_id,
            MentorMessage.mentorship_id == mentorship_id
        )
    )
    message = result.scalar_one_or_none()
    
    if not message:
        raise HTTPException(status_code=404, detail="Message introuvable")
    
    if message.sender_id == current_user.id:
        raise HTTPException(status_code=403, detail="Vous ne pouvez pas marquer vos propres messages comme lus")
    
    message.is_read = True
    await db.flush()
    
    return {"message": "Message marqué comme lu"}


# ========== SESSIONS ==========

@router.get("/{mentorship_id}/sessions")
async def get_mentorship_sessions(
    mentorship_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Récupère toutes les sessions d'un mentorat (uniquement les futures)"""
    result = await db.execute(
        select(Mentorship).where(Mentorship.id == mentorship_id)
    )
    mentorship = result.scalar_one_or_none()
    
    if not mentorship:
        raise HTTPException(status_code=404, detail="Mentorat non trouvé")
    
    if mentorship.mentor_id != current_user.id and mentorship.mentee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(MentoringSession)
        .where(
            MentoringSession.mentorship_id == mentorship_id,
            MentoringSession.scheduled_at >= now
        )
        .order_by(MentoringSession.scheduled_at)
    )
    sessions = result.scalars().all()
    
    output = []
    for session in sessions:
        output.append({
            "id": session.id,
            "mentorship_id": session.mentorship_id,
            "scheduled_at": session.scheduled_at.isoformat(),
            "duration_min": session.duration_min,
            "location": session.location,
            "topic": session.topic,
            "status": session.status,
            "mentee_rating": session.mentee_rating,
            "mentee_feedback": session.mentee_feedback,
            "mentor_feedback": session.mentor_feedback
        })
    
    return output


@router.post("/{mentorship_id}/sessions", status_code=201)
async def create_mentorship_session(
    mentorship_id: int,
    session_data: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Crée une nouvelle session de mentorat - ⭐ Seul le mentor peut le faire ⭐"""
    
    result = await db.execute(
        select(Mentorship).where(Mentorship.id == mentorship_id)
    )
    mentorship = result.scalar_one_or_none()
    
    if not mentorship:
        raise HTTPException(status_code=404, detail="Mentorat non trouvé")
    
    # ⭐ VÉRIFICATION : Seul le mentor peut créer une session ⭐
    if mentorship.mentor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Seul le mentor peut planifier une session")
    
    if _ensure_aware(session_data.scheduled_at) <= datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="La date de la session doit être dans le futur")
    
    new_session = MentoringSession(
        mentorship_id=mentorship_id,
        scheduled_at=session_data.scheduled_at,
        duration_min=session_data.duration_min,
        location=session_data.location,
        topic=session_data.topic,
        status="scheduled"
    )
    
    db.add(new_session)
    await db.flush()
    await db.refresh(new_session)
    
    return {
        "id": new_session.id,
        "mentorship_id": new_session.mentorship_id,
        "scheduled_at": new_session.scheduled_at.isoformat(),
        "duration_min": new_session.duration_min,
        "location": new_session.location,
        "topic": new_session.topic,
        "status": new_session.status
    }


@router.delete("/{mentorship_id}/sessions/{session_id}")
async def delete_session(
    mentorship_id: int,
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Supprimer une session (uniquement par le mentor)"""
    
    result = await db.execute(
        select(Mentorship).where(Mentorship.id == mentorship_id)
    )
    mentorship = result.scalar_one_or_none()
    
    if not mentorship:
        raise HTTPException(status_code=404, detail="Mentorat non trouvé")
    
    if mentorship.mentor_id != current_user.id and mentorship.mentee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    result = await db.execute(
        select(MentoringSession).where(
            MentoringSession.mentorship_id == mentorship_id,
            MentoringSession.id == session_id
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session non trouvée")
    
    await db.delete(session)
    await db.commit()
    
    return {"message": "Session supprimée avec succès"}


@router.get("/{mentorship_id}/sessions/{session_id}")
async def get_session_detail(
    mentorship_id: int,
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Récupère les détails d'une session spécifique"""
    result = await db.execute(
        select(Mentorship).where(Mentorship.id == mentorship_id)
    )
    mentorship = result.scalar_one_or_none()
    
    if not mentorship:
        raise HTTPException(status_code=404, detail="Mentorat non trouvé")
    
    if mentorship.mentor_id != current_user.id and mentorship.mentee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    result = await db.execute(
        select(MentoringSession).where(
            MentoringSession.mentorship_id == mentorship_id,
            MentoringSession.id == session_id
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session non trouvée")
    
    return {
        "id": session.id,
        "mentorship_id": session.mentorship_id,
        "scheduled_at": session.scheduled_at.isoformat(),
        "duration_min": session.duration_min,
        "location": session.location,
        "topic": session.topic,
        "status": session.status,
        "mentee_rating": session.mentee_rating,
        "mentee_feedback": session.mentee_feedback,
        "mentor_feedback": session.mentor_feedback
    }


@router.patch("//{mentorship_id}/sessions/{session_id}")
async def update_session(
    mentorship_id: int,
    session_id: int,
    session_update: SessionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Met à jour une session (annuler, reporter, modifier)"""
    result = await db.execute(
        select(Mentorship).where(Mentorship.id == mentorship_id)
    )
    mentorship = result.scalar_one_or_none()
    
    if not mentorship:
        raise HTTPException(status_code=404, detail="Mentorat non trouvé")
    
    if mentorship.mentor_id != current_user.id and mentorship.mentee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    result = await db.execute(
        select(MentoringSession).where(
            MentoringSession.mentorship_id == mentorship_id,
            MentoringSession.id == session_id
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session non trouvée")
    
    update_data = session_update.dict(exclude_unset=True)
    
    if "status" in update_data:
        valid_statuses = ["scheduled", "completed", "cancelled", "in_progress"]
        if update_data["status"] not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Statut invalide. Choisir parmi: {valid_statuses}")
        session.status = update_data["status"]
    
    if "location" in update_data:
        session.location = update_data["location"]
    
    if "topic" in update_data:
        session.topic = update_data["topic"]
    
    if "scheduled_at" in update_data:
        if _ensure_aware(update_data["scheduled_at"]) <= datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="La date doit être dans le futur")
        session.scheduled_at = update_data["scheduled_at"]
    
    await db.flush()
    
    return {"message": "Session mise à jour", "status": session.status}


@router.post("/{mentorship_id}/sessions/{session_id}/feedback")
async def submit_session_feedback(
    mentorship_id: int,
    session_id: int,
    feedback: SessionFeedback,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Soumet une évaluation pour une session (par le mentoré)"""
    result = await db.execute(
        select(Mentorship).where(Mentorship.id == mentorship_id)
    )
    mentorship = result.scalar_one_or_none()
    
    if not mentorship:
        raise HTTPException(status_code=404, detail="Mentorat non trouvé")
    
    if mentorship.mentee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Seul le mentoré peut évaluer la session")
    
    result = await db.execute(
        select(MentoringSession).where(
            MentoringSession.mentorship_id == mentorship_id,
            MentoringSession.id == session_id
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session non trouvée")
    
    if _ensure_aware(session.scheduled_at) > datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Impossible d'évaluer une session future")
    
    if session.mentee_rating is not None:
        raise HTTPException(status_code=400, detail="Cette session a déjà été évaluée")
    
    if feedback.rating < 1 or feedback.rating > 5:
        raise HTTPException(status_code=400, detail="La note doit être comprise entre 1 et 5")
    
    session.mentee_rating = float(feedback.rating)
    session.mentee_feedback = feedback.feedback
    session.status = "completed"
    
    await db.flush()
    
    return {
        "message": "Évaluation enregistrée avec succès",
        "rating": feedback.rating
    }


# ========== SUPPRIMER UNE CONVERSATION (MENTORAT) ==========

@router.delete("/{mentorship_id}")
async def delete_mentorship(
    mentorship_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Supprimer une conversation (mentorat) et tous ses messages"""
    
    result = await db.execute(
        select(Mentorship).where(Mentorship.id == mentorship_id)
    )
    mentorship = result.scalar_one_or_none()
    
    if not mentorship:
        raise HTTPException(status_code=404, detail="Conversation introuvable")
    
    # Vérifier que l'utilisateur est bien impliqué dans la conversation
    if mentorship.mentor_id != current_user.id and mentorship.mentee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    # Supprimer le mentorat (les messages et sessions sont supprimés en cascade)
    await db.delete(mentorship)
    await db.commit()
    
    return {"message": "Conversation supprimée avec succès"}