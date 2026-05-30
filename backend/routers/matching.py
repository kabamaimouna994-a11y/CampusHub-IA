from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from core.database import get_db
from core.security import get_current_user
from models.user import User, YearLevel
from models.project import Project, ProjectStatus, ProjectApplication
from services.matching_service import (
    match_user_to_project,
    match_mentor_to_mentee,
)

router = APIRouter()

# Ordre des niveaux pour le mentorat
YEAR_ORDER = {"B1": 1, "B2": 2, "B3": 3, "M1": 4, "M2": 5}


class ProjectMatchResponse(BaseModel):
    project_id: int
    project_title: str
    project_type: str
    project_description: str
    total_score: float
    score_percent: int
    skill_score: float
    availability_score: float
    interest_score: float
    explanation: str
    available_slots: int
    required_skills: list


class MentorMatchResponse(BaseModel):
    mentor_id: int
    mentor_name: str
    year_level: Optional[str]
    specialty: Optional[str]
    score_percent: int
    total_score: float
    explanation: str
    is_available: bool
    active_mentees: int


# ─────────────────────────────────────────────────────────────
# GET /matching/projects
# ─────────────────────────────────────────────────────────────

@router.get("/projects", response_model=List[ProjectMatchResponse])
async def get_project_matches(
    top_k: int = Query(default=10, ge=1, le=50),
    min_score: float = Query(default=0.30, ge=0.0, le=1.0),
    type: Optional[str] = Query(default=None, description="Filtrer par type de projet"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retourne les projets ouverts triés par score de matching IA."""
    
    stmt = select(Project).where(Project.status == ProjectStatus.OPEN).options(selectinload(Project.members))
    if type:
        stmt = stmt.where(Project.type == type)

    result = await db.execute(stmt)
    projects = result.scalars().all()

    user_skills = [{"name": s.name, "level": s.level.value} for s in current_user.skills]
    user_history = {"completed_projects": 0, "avg_rating": 0.0}

    matches = []
    for project in projects:
        match = match_user_to_project(
            user_skills=user_skills,
            user_specialty=current_user.specialty,
            user_hours_per_week=current_user.hours_per_week,
            user_history=user_history,
            project={
                "id": project.id,
                "type": project.type.value,
                "required_skills": project.required_skills or [],
                "required_hours_per_week": project.required_hours_per_week,
            },
        )

        if match.total_score >= min_score:
            matches.append(ProjectMatchResponse(
                project_id=project.id,
                project_title=project.title,
                project_type=project.type.value,
                project_description=project.description[:200] + "…" if len(project.description) > 200 else project.description,
                total_score=match.total_score,
                score_percent=match.score_percent,
                skill_score=match.skill_score,
                availability_score=match.availability_score,
                interest_score=match.interest_score,
                explanation=match.explanation,
                available_slots=project.available_slots,
                required_skills=project.required_skills or [],
            ))

    matches.sort(key=lambda x: x.total_score, reverse=True)
    return matches[:top_k]


# ─────────────────────────────────────────────────────────────
# POST /matching/projects/{id}/apply
# ─────────────────────────────────────────────────────────────

@router.post("/projects/{project_id}/apply", status_code=status.HTTP_201_CREATED)
async def apply_to_project(
    project_id: int,
    message: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Postuler à un projet."""
    
    result = await db.execute(
        select(Project)
        .where(Project.id == project_id)
        .options(selectinload(Project.members), selectinload(Project.applications))
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Projet introuvable")
    if project.status != ProjectStatus.OPEN:
        raise HTTPException(status_code=400, detail="Ce projet n'accepte plus de candidatures")
    if project.available_slots == 0:
        raise HTTPException(status_code=400, detail="Aucune place disponible dans ce projet")

    existing = next((a for a in project.applications if a.applicant_id == current_user.id), None)
    if existing:
        raise HTTPException(status_code=400, detail="Vous avez déjà postulé à ce projet")

    user_skills = [{"name": s.name, "level": s.level.value} for s in current_user.skills]
    match = match_user_to_project(
        user_skills=user_skills,
        user_specialty=current_user.specialty,
        user_hours_per_week=current_user.hours_per_week,
        user_history={"completed_projects": 0, "avg_rating": 0.0},
        project={
            "id": project.id,
            "type": project.type.value,
            "required_skills": project.required_skills or [],
            "required_hours_per_week": project.required_hours_per_week,
        },
    )

    application = ProjectApplication(
        project_id=project_id,
        applicant_id=current_user.id,
        match_score=match.total_score,
        message=message,
    )
    db.add(application)
    await db.flush()

    return {
        "message": "Candidature envoyée avec succès",
        "application_id": application.id,
        "match_score_percent": match.score_percent,
    }


# ─────────────────────────────────────────────────────────────
# GET /matching/mentors
# ─────────────────────────────────────────────────────────────

@router.get("/mentors", response_model=List[MentorMatchResponse])
async def get_mentor_matches(
    top_k: int = Query(default=10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retourne les mentors compatibles pour l'utilisateur connecté.
    Un mentor doit avoir un niveau supérieur (B1 → B2 → B3 → M1 → M2).
    """
    # Ordre des niveaux
    level_order = {"B1": 1, "B2": 2, "B3": 3, "M1": 4, "M2": 5}
    
    # Niveau du mentoré (utilisateur connecté)
    mentee_level_str = current_user.year_level.value if current_user.year_level else "B1"
    mentee_order = level_order.get(mentee_level_str, 1)
    
    # Déterminer les niveaux supérieurs
    eligible_levels = []
    for level, order in level_order.items():
        if order > mentee_order:
            eligible_levels.append(level)
    
    print(f"[MATCHING] Mentoré: {mentee_level_str} (ordre {mentee_order})")
    print(f"[MATCHING] Niveaux éligibles pour mentor: {eligible_levels}")
    
    if not eligible_levels:
        # Si l'utilisateur est déjà au niveau maximum (M2)
        return []
    
    # Rechercher les mentors potentiels
    stmt = select(User).where(
        User.year_level.in_(eligible_levels),
        User.is_active == True,
        User.is_available == True
    ).options(selectinload(User.skills), selectinload(User.mentorships_as_mentor))
    
    result = await db.execute(stmt)
    mentors = result.scalars().all()
    
    print(f"[MATCHING] Mentors trouvés: {len(mentors)}")
    
    # Construire la réponse
    matches = []
    for mentor in mentors:
        # Compter les mentorés actifs
        active_mentees = len([m for m in mentor.mentorships_as_mentor if m.status == "active"])
        
        # Calculer un score simple basé sur la spécialité
        score = 85
        if current_user.specialty and mentor.specialty:
            if current_user.specialty.lower() in mentor.specialty.lower() or mentor.specialty.lower() in current_user.specialty.lower():
                score = 95
        
        matches.append(MentorMatchResponse(
            mentor_id=mentor.id,
            mentor_name=mentor.full_name,
            year_level=mentor.year_level.value if mentor.year_level else None,
            specialty=mentor.specialty,
            score_percent=score,
            total_score=score / 100,
            explanation=f"Mentor de niveau {mentor.year_level.value} - Spécialité: {mentor.specialty or 'Non renseignée'}",
            is_available=mentor.is_available,
            active_mentees=active_mentees,
        ))
    
    # Trier par score
    matches.sort(key=lambda x: x.score_percent, reverse=True)
    return matches[:top_k]