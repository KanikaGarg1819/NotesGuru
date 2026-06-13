from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import health, auth, notes, syllabus, guides
from app.core.config import settings
from app.db.session import engine, Base
import app.models  # noqa

@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="NotesGuru API",
    description="Syllabus-Driven AI Study Portal",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router,   tags=["Health"])
app.include_router(auth.router,     prefix="/auth",     tags=["Auth"])
app.include_router(notes.router,    prefix="/notes",    tags=["Notes"])
app.include_router(syllabus.router, prefix="/syllabus", tags=["Syllabus"])
app.include_router(guides.router,   prefix="/guides",   tags=["Guides"])