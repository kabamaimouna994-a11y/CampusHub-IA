from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
import shutil
import os
from datetime import datetime, timedelta
from collections import defaultdict

from core.database import get_db
from core.security import get_current_user
from models.user import User
from models.mentorship import MentorMessage
from models.project import ProjectApplication

router = APIRouter()

# Dossier pour les avatars
AVATAR_DIR = "static/avatars"
os.makedirs(AVATAR_DIR, exist_ok=True)


class UserUpdateRequest(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    specialty: str | None = None
    bio: str | None = None
    linkedin_url: str | None = None
    hours_per_week: int | None = None
    is_available: bool | None = None


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "role": current_user.role.value,
        "year_level": current_user.year_level.value if current_user.year_level else None,
        "specialty": current_user.specialty,
        "bio": current_user.bio,
        "avatar_url": current_user.avatar_url,
        "is_available": current_user.is_available,
        "hours_per_week": current_user.hours_per_week,
        "linkedin_url": current_user.linkedin_url,
        "created_at": current_user.created_at.isoformat(),
    }


@router.put("/me")
async def update_me(
    data: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(current_user, field, value)
    return {"message": "Profil mis à jour"}


@router.post("/me/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Uploader une photo de profil"""
    
    # Vérifier le type de fichier
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Le fichier doit être une image")
    
    # Vérifier la taille (max 2MB)
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    if file_size > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Le fichier ne doit pas dépasser 2MB")
    
    # Générer un nom unique
    file_extension = file.filename.split('.')[-1].lower()
    if file_extension not in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
        raise HTTPException(status_code=400, detail="Format non supporté")
    
    file_name = f"avatar_{current_user.id}_{int(datetime.now().timestamp())}.{file_extension}"
    file_path = os.path.join(AVATAR_DIR, file_name)
    
    # Sauvegarder le fichier
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Supprimer l'ancien avatar s'il existe
    if current_user.avatar_url:
        old_path = os.path.join(".", current_user.avatar_url.lstrip('/'))
        if os.path.exists(old_path):
            os.remove(old_path)
    
    # Mettre à jour l'URL dans la base
    avatar_url = f"/static/avatars/{file_name}"
    current_user.avatar_url = avatar_url
    await db.flush()
    
    return {"avatar_url": avatar_url, "message": "Avatar mis à jour"}


@router.delete("/me")
async def delete_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await db.delete(current_user)
    return {"message": "Compte supprimé définitivement"}


# ⭐ ENDPOINT DE RECHERCHE D'ÉTUDIANTS (AVEC TOUS LES FILTRES) ⭐
# ⚠️ IMPORTANT : Ce endpoint doit être placé AVANT "/{user_id}"
@router.get("/search")
async def search_students(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Recherche d'étudiants par nom, niveau et compétence"""
    
    # Récupérer tous les paramètres
    q = request.query_params.get('q', '')
    year_level = request.query_params.get('year_level', '')
    skill = request.query_params.get('skill', '')
    
    print(f"🔍 Recherche - q:'{q}', year_level:'{year_level}', skill:'{skill}'")
    
    query = select(User).where(User.role == "student", User.id != current_user.id)
    
    # Filtre par nom
    if q and len(q.strip()) > 0:
        query = query.where(
            or_(
                User.first_name.ilike(f"%{q}%"),
                User.last_name.ilike(f"%{q}%")
            )
        )
    
    # Filtre par niveau (uniquement si différent de "Tous" et non vide)
    if year_level and year_level != "" and year_level != "Tous":
        try:
            from models.user import YearLevel
            year_level_enum = YearLevel(year_level)
            query = query.where(User.year_level == year_level_enum)
            print(f"   🎓 Filtre niveau: {year_level}")
        except ValueError:
            print(f"   ⚠️ Niveau invalide: {year_level}")
    
    # Filtre par compétence
    if skill and len(skill.strip()) > 0:
        query = query.where(User.skills.any(name=skill))
        print(f"   ⚡ Filtre compétence: {skill}")
    
    query = query.options(selectinload(User.skills))
    result = await db.execute(query)
    users = result.scalars().all()
    
    print(f"🔍 {len(users)} étudiants trouvés")
    
    output = []
    for u in users:
        output.append({
            "id": u.id,
            "full_name": f"{u.first_name} {u.last_name}",
            "first_name": u.first_name,
            "last_name": u.last_name,
            "email": u.email,
            "year_level": u.year_level.value if u.year_level else None,
            "specialty": u.specialty,
            "avatar_url": u.avatar_url,
            "bio": u.bio,
            "skills": [{"name": s.name, "level": s.level.value} for s in u.skills],
            "is_available": u.is_available
        })
    
    return output


# ⭐ ENDPOINT /{user_id} - DOIT ÊTRE APRÈS /search ⭐
@router.get("/{user_id}")
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    return {
        "id": user.id,
        "full_name": user.full_name,
        "year_level": user.year_level.value if user.year_level else None,
        "specialty": user.specialty,
        "bio": user.bio,
        "avatar_url": user.avatar_url,
        "is_available": user.is_available,
        "skills": [{"name": s.name, "level": s.level.value} for s in user.skills],
    }


# ⭐ ENDPOINT ACTIVITÉ HEBDOMADAIRE ⭐
@router.get("/me/activity")
async def get_user_activity(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Récupère l'activité hebdomadaire de l'utilisateur (messages, candidatures, connexions)"""
    
    today = datetime.utcnow()
    week_start = today - timedelta(days=6)
    
    # Compter les messages envoyés par jour
    stmt = select(
        func.date(MentorMessage.sent_at).label("date"),
        func.count(MentorMessage.id).label("count")
    ).where(
        MentorMessage.sender_id == current_user.id,
        MentorMessage.sent_at >= week_start
    ).group_by(func.date(MentorMessage.sent_at))
    
    result = await db.execute(stmt)
    message_counts = {row[0]: row[1] for row in result.fetchall()}
    
    # Compter les candidatures à des projets par jour
    stmt2 = select(
        func.date(ProjectApplication.created_at).label("date"),
        func.count(ProjectApplication.id).label("count")
    ).where(
        ProjectApplication.applicant_id == current_user.id,
        ProjectApplication.created_at >= week_start
    ).group_by(func.date(ProjectApplication.created_at))
    
    result2 = await db.execute(stmt2)
    app_counts = {row[0]: row[1] for row in result2.fetchall()}
    
    # Générer les 7 derniers jours
    weekly_activity = []
    days_of_week = []
    
    for i in range(7):
        day = week_start + timedelta(days=i)
        day_str = day.strftime('%Y-%m-%d')
        days_of_week.append(day.strftime('%a'))
        
        # Total d'actions = messages + candidatures + 1 (connexion de base)
        activity = message_counts.get(day_str, 0) + app_counts.get(day_str, 0) + 1
        weekly_activity.append(activity)
    
    return {
        "weekly_activity": weekly_activity,
        "days": days_of_week,
        "message_counts": dict(message_counts),
        "application_counts": dict(app_counts),
        "total_actions": sum(weekly_activity)
    }