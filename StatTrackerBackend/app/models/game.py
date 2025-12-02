"""Game model."""

from typing import Optional
from datetime import date as date_type, datetime
from pydantic import BaseModel, Field


class Game(BaseModel):
    """Game model representing a single game."""
    
    id: Optional[int] = Field(default=None)
    league: str = Field(..., description="League name")
    season: str = Field(..., description="Season identifier")
    date: date_type = Field(..., description="Game date")
    home_team: str = Field(..., description="Home team name")
    away_team: str = Field(..., description="Away team name")
    home_score: int = Field(default=0, description="Home team runs scored")
    away_score: int = Field(default=0, description="Away team runs scored")
    winner: Optional[str] = Field(default=None, description="Winning team name, or None for tie")
    created_at: Optional[datetime] = Field(default=None)
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "id": 1,
                "league": "Major League",
                "season": "2024",
                "date": "2024-01-15",
                "home_team": "Yankees",
                "away_team": "Red Sox",
                "created_at": "2024-01-15T00:00:00"
            }
        }

