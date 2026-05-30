from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import shutil
import os
from datetime import datetime

from core.database import get_db
from core.security import get_current_user
from models.user import User

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