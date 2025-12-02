"""Main FastAPI application."""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import games, players, stats, teams

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import storylines with detailed error handling
try:
    from app.api.routes import storylines
    STORYLINES_AVAILABLE = True
    logger.info("✓ Storylines module imported successfully")
except ImportError as e:
    STORYLINES_AVAILABLE = False
    logger.error(f"✗ Failed to import storylines module: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    STORYLINES_AVAILABLE = False
    logger.error(f"✗ Unexpected error importing storylines: {e}")
    import traceback
    traceback.print_exc()

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="A FastAPI-based backend API for managing a HitTrax-based adult baseball league"
)

# Configure CORS - Comprehensive list of common development origins
# Note: Cannot use "*" with allow_credentials=True, so we list common ports
cors_origins = [
    # Vite default ports
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    # React default
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    # Vue default
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    # Other common ports
    "http://localhost:5175",
    "http://localhost:5176",
    "http://localhost:5177",
    "http://127.0.0.1:5175",
    "http://127.0.0.1:5176",
    "http://127.0.0.1:5177",
]

# Also allow the configured origin if different
if settings.FRONTEND_ORIGIN and settings.FRONTEND_ORIGIN not in cors_origins:
    cors_origins.append(settings.FRONTEND_ORIGIN)

logger.info(f"CORS allowed origins: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Register routers with debug logging
logger.info("Registering routers...")

app.include_router(games.router)
logger.info("✓ Games router registered")

app.include_router(players.router)
logger.info("✓ Players router registered")

app.include_router(stats.router)
logger.info("✓ Stats router registered")

app.include_router(teams.router)
logger.info("✓ Teams router registered")

if STORYLINES_AVAILABLE:
    app.include_router(storylines.router)
    logger.info("✓ Storylines router registered")
else:
    logger.warning("✗ Storylines router NOT registered (import failed)")

@app.on_event("startup")
async def startup_event():
    """Log all registered routes on startup."""
    import asyncio
    await asyncio.sleep(0.1)  # Small delay to ensure all routes are registered
    logger.info("\n" + "="*60)
    logger.info("REGISTERED API ROUTES:")
    logger.info("="*60)
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            methods = ', '.join(route.methods)
            logger.info(f"{methods:10s} {route.path}")
    logger.info("="*60 + "\n")
    
    # OpenAI status
    if settings.validate_openai_key():
        logger.info("✓ OpenAI API key is configured")
    else:
        logger.warning("✗ OpenAI API key NOT configured")

@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": settings.APP_NAME,
        "version": "2.0.0",
        "docs": "/docs",
        "features": ["automatic_team_detection", "team_statistics", "leaderboards"],
        "storylines_enabled": STORYLINES_AVAILABLE
    }

@app.get("/health")
def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "openai_configured": settings.validate_openai_key(),
        "storylines_available": STORYLINES_AVAILABLE
    }

@app.get("/debug/routes")
def debug_routes():
    """Debug endpoint to see all registered routes."""
    routes = []
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            routes.append({
                "path": route.path,
                "methods": list(route.methods),
                "name": route.name if hasattr(route, 'name') else None
            })
    return {"routes": routes, "total": len(routes)}

logger.info(f"Application started: {settings.APP_NAME}")
