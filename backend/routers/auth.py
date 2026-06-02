from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import get_db
from core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from models.user import User, YearLevel, UserRole

router = APIRouter()


class RegisterRequest(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str
    year_level: str = "B1"
    specialty: Optional[str] = None

    @field_validator("email")
    @classmethod
    def email_valid(cls, v: str) -> str:
        if "@" not in v or "." not in v:
            raise ValueError("Email invalide")
        return v

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Le mot de passe doit contenir au moins 8 caractères")
        return v

    @field_validator("year_level")
    @classmethod
    def year_level_valid(cls, v: str) -> str:
        if v not in ["B1", "B2", "B3", "M1", "M2"]:
            raise ValueError("Niveau invalide")
        return v


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: int
    role: str
    year_level: Optional[str]
    full_name: str


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Vérifier si l'email existe déjà
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Un compte existe déjà avec cet email")

    # Convertir year_level de str à YearLevel enum
    year_level_enum = None
    if data.year_level:
        try:
            year_level_enum = YearLevel(data.year_level)
        except ValueError:
            raise HTTPException(status_code=400, detail="Niveau académique invalide")

    # Créer l'utilisateur avec le rôle défini
    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        year_level=year_level_enum,
        specialty=data.specialty,
        role=UserRole.STUDENT,  # ⭐ Définition explicite du rôle
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    return TokenResponse(
        access_token=create_access_token({"sub": str(user.id)}),
        refresh_token=create_refresh_token({"sub": str(user.id)}),
        user_id=user.id,
        role=user.role.value,
        year_level=user.year_level.value if user.year_level else None,
        full_name=user.full_name,
    )


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Compte désactivé")

    return TokenResponse(
        access_token=create_access_token({"sub": str(user.id)}),
        refresh_token=create_refresh_token({"sub": str(user.id)}),
        user_id=user.id,
        role=user.role.value,
        year_level=user.year_level.value if user.year_level else None,
        full_name=user.full_name,
    )


@router.post("/refresh", response_model=dict)
async def refresh(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    payload = decode_token(data.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=400, detail="Token de type 'refresh' attendu")

    result = await db.execute(select(User).where(User.id == int(payload["sub"])))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Utilisateur introuvable")

    return {
        "access_token": create_access_token({"sub": str(user.id)}),
        "token_type": "bearer",
    }


@router.post("/logout")
async def logout():
    return {"message": "Déconnexion réussie — supprimez vos tokens locaux"}