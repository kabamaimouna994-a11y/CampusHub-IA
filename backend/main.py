from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from core.database import create_tables
from routers import auth, users, skills, matching, mentorat, clubs, events, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise la base de données au démarrage."""
    await create_tables()
    yield


app = FastAPI(
    title="CampusHub IA",
    description="Plateforme intelligente de matching compétences",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configuration CORS - Version qui fonctionne
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

# Servir les fichiers statiques
app.mount("/static", StaticFiles(directory="static"), name="static")

# Routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentification"])
app.include_router(users.router, prefix="/api/users", tags=["Utilisateurs"])
app.include_router(skills.router, prefix="/api/skills", tags=["SkillShare"])
app.include_router(matching.router, prefix="/api/matching", tags=["TalentMatch"])
app.include_router(mentorat.router, prefix="/api/mentorat", tags=["MentorLoop"])
app.include_router(clubs.router, prefix="/api/clubs", tags=["KPIs Campus"])
app.include_router(events.router, prefix="/api/events", tags=["EventBoost"])
app.include_router(admin.router, prefix="/api/admin", tags=["Administration"])


@app.get("/")
async def root():
    return {"status": "ok", "service": "CampusHub IA", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}