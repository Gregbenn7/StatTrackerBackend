"""Storyline model."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class GameStorylines(BaseModel):
    """Game storylines model for AI-generated game summaries."""
    
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

