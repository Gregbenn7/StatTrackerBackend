"""Storyline-related API routes."""

import logging
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException
from app.models.storyline import GameStoryline
from app.services.storyline_service import StorylineService
from app.core.config import settings
from app.storage.memory_store import store

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create router
router = APIRouter(prefix="/storylines", tags=["storylines"])

logger.info(f"Storylines router created with prefix: {router.prefix}")

# In-memory cache for storylines (simple dictionary)
storylines_cache: dict[str, GameStoryline] = {}


@router.post("/games/{game_id}/generate", response_model=GameStoryline)
def generate_storyline(game_id: str):
    """Generate AI game recap."""
    
    logger.info(f"\n{'='*60}")
    logger.info(f"POST /storylines/games/{game_id}/generate")
    logger.info(f"Generating storyline for game: {game_id}")
    
    # Validate OpenAI configuration
    if not settings.validate_openai_key():
        logger.error("OpenAI API key not configured")
        raise HTTPException(
            status_code=500,
            detail=(
                "OpenAI API key not configured. "
                "Set OPENAI_API_KEY in .env file to enable game recaps."
            )
        )
    
    # Convert string game_id to int for service calls
    try:
        game_id_int = int(game_id)
    except ValueError:
        logger.error(f"Invalid game_id format: {game_id}")
        raise HTTPException(status_code=400, detail=f"Invalid game_id: {game_id}")
    
    # Find game
    game = store.get_game(game_id_int)
    if not game:
        logger.error(f"Game {game_id} not found")
        available_games = [str(g.id) for g in store.get_all_games() if g.id is not None]
        logger.info(f"Available games: {available_games}")
        raise HTTPException(status_code=404, detail=f"Game {game_id} not found")
    
    logger.info(f"Game found: {game.home_team} vs {game.away_team}")
    
    # Get plate appearances for this game
    all_pas = store.get_all_plate_appearances()
    game_pas = [pa for pa in all_pas if pa.game_id == game_id_int]
    
    logger.info(f"Total PAs in store: {len(all_pas)}, PAs for game {game_id_int}: {len(game_pas)}")
    
    if not game_pas:
        logger.error("No player data found for this game")
        raise HTTPException(
            status_code=400,
            detail="No player data found for this game. Cannot generate recap."
        )
    
    # Separate by team
    team1_pas = [pa for pa in game_pas if pa.team == game.home_team]
    team2_pas = [pa for pa in game_pas if pa.team == game.away_team]
    
    logger.info(f"Player stats: {len(team1_pas)} + {len(team2_pas)} plate appearances")
    
    if not team1_pas or not team2_pas:
        logger.error("Insufficient game data")
        raise HTTPException(
            status_code=400,
            detail="Incomplete game data. Both teams must have player stats."
        )
    
    logger.info(f"Score: {game.home_score}-{game.away_score}")
    
    try:
        logger.info("Calling OpenAI API...")
        
        # Generate recap using the service
        recap_data = StorylineService.generate_game_recap(
            game=game,
            team1_players=team1_pas,
            team2_players=team2_pas
        )
        
        logger.info("OpenAI API call successful")
        
        # Create storyline object
        storyline = GameStoryline(
            id=str(uuid.uuid4()),
            game_id=game_id,
            headline=recap_data['headline'],
            recap=recap_data['recap'],
            key_players=recap_data['key_players'],
            game_summary=recap_data['game_summary'],
            generated_at=datetime.now().isoformat()
        )
        
        # Cache it
        storylines_cache[game_id] = storyline
        
        logger.info(f"✓ Storyline generated: {storyline.headline}")
        logger.info(f"✓ Cached for game: {game_id}")
        logger.info(f"{'='*60}\n")
        
        return storyline
        
    except ValueError as e:
        logger.error(f"ValueError: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate: {str(e)}")


@router.get("/games/{game_id}", response_model=GameStoryline)
def get_storyline(game_id: str):
    """Get cached storyline."""
    logger.info(f"GET /storylines/games/{game_id}")
    logger.info(f"Checking cache for game: {game_id}")
    logger.info(f"Cache contains: {list(storylines_cache.keys())}")
    
    storyline = storylines_cache.get(game_id)
    if not storyline:
        logger.warning(f"No storyline found in cache for game: {game_id}")
        raise HTTPException(status_code=404, detail="No recap found. Generate one first.")
    
    logger.info(f"✓ Returning cached storyline: {storyline.headline}")
    return storyline


@router.get("/games/{game_id}/exists")
def check_exists(game_id: str):
    """Check if storyline exists."""
    exists = game_id in storylines_cache
    logger.info(f"GET /storylines/games/{game_id}/exists -> {exists}")
    return {
        "exists": exists,
        "game_id": game_id
    }


@router.get("/debug/info")
def debug_info():
    """Debug information about storyline system."""
    all_games = store.get_games(limit=10000)  # Get all games
    game_ids = [str(g.id) for g in all_games if g.id is not None]
    return {
        "router_prefix": router.prefix,
        "cached_storylines": list(storylines_cache.keys()),
        "total_cached": len(storylines_cache),
        "available_games": game_ids
    }

# Log registered endpoints
logger.info("Storylines router endpoints registered:")
for route in router.routes:
    if hasattr(route, 'methods') and hasattr(route, 'path'):
        methods = ', '.join(route.methods)
        logger.info(f"  {methods:10s} {route.path}")

