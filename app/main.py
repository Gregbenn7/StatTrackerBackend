"""Main FastAPI application."""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import games, players, stats, storylines, teams

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="A FastAPI-based backend API for managing a HitTrax-based adult baseball league"
)

# Configure CORS
frontend_origin = settings.FRONTEND_ORIGIN
if frontend_origin:
    cors_origins = [frontend_origin]
    allow_credentials = True
else:
    cors_origins = ["*"]
    allow_credentials = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(games.router)
app.include_router(players.router)
app.include_router(stats.router)
app.include_router(storylines.router)
app.include_router(teams.router)

@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": settings.APP_NAME,
        "version": "2.0.0",
        "docs": "/docs",
        "features": ["automatic_team_detection", "team_statistics", "leaderboards"]
    }

logger.info(f"Application started: {settings.APP_NAME}")
