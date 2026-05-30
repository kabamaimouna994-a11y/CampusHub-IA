from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from core.database import get_db
from core.security import require_roles
from models.user import User
from models.project import Project
from models.mentorship import Mentorship
from models.club import Club
from models.event import Event

router = APIRouter()


@router.get("/dashboard")
async def admin_dashboard(db: AsyncSession = Depends(get_db), current_user: User = Depends(require_roles("admin"))):
    users_count = await db.scalar(select(func.count(User.id)))
    projects_count = await db.scalar(select(func.count(Project.id)))
    mentorships_count = await db.scalar(select(func.count(Mentorship.id)))
    clubs_count = await db.scalar(select(func.count(Club.id)))
    events_count = await db.scalar(select(func.count(Event.id)))

    return {
        "stats": {
            "total_users": users_count,
            "total_projects": projects_count,
            "total_mentorships": mentorships_count,
            "total_clubs": clubs_count,
            "total_events": events_count,
        }
    }


@router.get("/users")
async def list_users(db: AsyncSession = Depends(get_db), current_user: User = Depends(require_roles("admin"))):
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role.value,
            "year_level": u.year_level.value if u.year_level else None,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat(),
        }
        for u in users
    ]