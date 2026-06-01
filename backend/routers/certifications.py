from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from datetime import datetime
import os
import shutil

from core.database import get_db
from core.security import get_current_user
from models.user import User
from models.certification import Certification

router = APIRouter()

# Dossier pour les certifications
CERTIF_DIR = "static/certifications"
os.makedirs(CERTIF_DIR, exist_ok=True)


class CertificationCreate(BaseModel):
    title: str
    issuer: Optional[str] = None
    issue_date: Optional[datetime] = None
    credential_id: Optional[str] = None
    credential_url: Optional[str] = None


class CertificationResponse(BaseModel):
    id: int
    title: str
    issuer: Optional[str]
    issue_date: Optional[datetime]
    credential_id: Optional[str]
    credential_url: Optional[str]
    file_path: Optional[str]
    is_verified: bool
    created_at: datetime


@router.get("/", response_model=List[CertificationResponse])
async def get_my_certifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Récupère toutes les certifications de l'utilisateur"""
    
    result = await db.execute(
        select(Certification).where(Certification.user_id == current_user.id)
    )
    certifications = result.scalars().all()
    
    return [
        CertificationResponse(
            id=c.id,
            title=c.title,
            issuer=c.issuer,
            issue_date=c.issue_date,
            credential_id=c.credential_id,
            credential_url=c.credential_url,
            file_path=c.file_path,
            is_verified=bool(c.is_verified),
            created_at=c.created_at
        )
        for c in certifications
    ]


@router.post("/", status_code=201)
async def add_certification(
    cert_data: CertificationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Ajouter une certification"""
    
    new_cert = Certification(
        user_id=current_user.id,
        title=cert_data.title,
        issuer=cert_data.issuer,
        issue_date=cert_data.issue_date,
        credential_id=cert_data.credential_id,
        credential_url=cert_data.credential_url,
        is_verified=False
    )
    
    db.add(new_cert)
    await db.commit()
    await db.refresh(new_cert)
    
    return CertificationResponse(
        id=new_cert.id,
        title=new_cert.title,
        issuer=new_cert.issuer,
        issue_date=new_cert.issue_date,
        credential_id=new_cert.credential_id,
        credential_url=new_cert.credential_url,
        file_path=new_cert.file_path,
        is_verified=bool(new_cert.is_verified),
        created_at=new_cert.created_at
    )


@router.post("/upload")
async def upload_certificate_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Uploader un fichier de certification"""
    
    allowed_types = ['application/pdf', 'image/jpeg', 'image/png', 'image/jpg']
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Format non supporté. Utilisez PDF, JPEG ou PNG")
    
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    if file_size > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Le fichier ne doit pas dépasser 5MB")
    
    file_extension = file.filename.split('.')[-1].lower()
    file_name = f"certif_{current_user.id}_{int(datetime.now().timestamp())}.{file_extension}"
    file_path = os.path.join(CERTIF_DIR, file_name)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return {"file_path": f"/static/certifications/{file_name}", "message": "Fichier uploadé"}


@router.delete("/{certification_id}")
async def delete_certification(
    certification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Supprimer une certification"""
    
    result = await db.execute(
        select(Certification).where(
            Certification.id == certification_id,
            Certification.user_id == current_user.id
        )
    )
    cert = result.scalar_one_or_none()
    
    if not cert:
        raise HTTPException(status_code=404, detail="Certification non trouvée")
    
    if cert.file_path:
        old_path = os.path.join(".", cert.file_path.lstrip('/'))
        if os.path.exists(old_path):
            os.remove(old_path)
    
    await db.delete(cert)
    await db.commit()
    
    return {"message": "Certification supprimée"}