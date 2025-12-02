"""Storyline model."""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class GameStoryline(BaseModel):
    """AI-generated game storyline/recap with simplified structure."""
    
    id: str
    game_id: str
    headline: str
    recap: str
    key_players: List[str]
    game_summary: str
    generated_at: str
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "id": "uuid-here",
                "game_id": "1",
                "headline": "Team A Defeats Team B in Thriller",
                "recap": "Full game recap text...",
                "key_players": ["Player 1", "Player 2", "Player 3"],
                "game_summary": "Team A defeats Team B 5-3",
                "generated_at": "2024-01-15T00:00:00"
            }
        }


class GameStorylines(BaseModel):
    """Game storylines model for AI-generated game summaries (legacy format)."""
    
    id: Optional[int] = Field(default=None)
    game_id: int = Field(..., description="Game ID")
    storylines_text: str = Field(..., description="Full storylines text from OpenAI")
    json_summary: str = Field(..., description="Structured JSON summary")
    created_at: Optional[datetime] = Field(default=None)
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "id": 1,
                "game_id": 1,
                "storylines_text": "Game recap text...",
                "json_summary": '{"recap": "...", "key_storylines": [...]}',
                "created_at": "2024-01-15T00:00:00"
            }
        }

