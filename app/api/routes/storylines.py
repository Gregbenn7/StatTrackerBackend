"""Storyline-related API routes."""

import json
import logging
from fastapi import APIRouter, HTTPException, Depends
from app.schemas.responses import GameStorylinesResponse, StorylineSummary
from app.services.storyline_service import StorylineService
from app.services.game_service import GameService
from app.api.deps import get_storyline_service, get_game_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/games", tags=["storylines"])


@router.post("/{game_id}/storylines", response_model=GameStorylinesResponse)
def create_game_storylines(
    game_id: int,
    game_service: GameService = Depends(get_game_service),
    storyline_service: StorylineService = Depends(get_storyline_service),
):
    """Generate AI storylines for a game."""
    game = game_service.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail=f"Game {game_id} not found")
    
    try:
        game_storylines = storyline_service.generate_storylines(game_id)
        
        # Parse JSON summary
        summary_dict = json.loads(game_storylines.json_summary)
        
        return GameStorylinesResponse(
            game_id=game_storylines.game_id,
            storylines_text=game_storylines.storylines_text,
            json_summary=game_storylines.json_summary,
            created_at=game_storylines.created_at,
            summary=StorylineSummary(**summary_dict)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating storylines: {str(e)}")


@router.get("/{game_id}/storylines", response_model=GameStorylinesResponse)
def get_game_storylines(
    game_id: int,
    game_service: GameService = Depends(get_game_service),
    storyline_service: StorylineService = Depends(get_storyline_service),
):
    """Get saved storylines for a game."""
    game = game_service.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail=f"Game {game_id} not found")
    
    game_storylines = storyline_service.get_storyline(game_id)
    
    if not game_storylines:
        raise HTTPException(status_code=404, detail=f"Storylines not found for game {game_id}")
    
    # Parse JSON summary
    summary_dict = json.loads(game_storylines.json_summary)
    
    return GameStorylinesResponse(
        game_id=game_storylines.game_id,
        storylines_text=game_storylines.storylines_text,
        json_summary=game_storylines.json_summary,
        created_at=game_storylines.created_at,
        summary=StorylineSummary(**summary_dict)
    )

