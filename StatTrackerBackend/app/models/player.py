"""Player model."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class Player(BaseModel):
    """Player model representing a baseball player."""
    
    id: Optional[int] = Field(default=None)
    name: str = Field(..., description="Player name")
    team: str = Field(..., description="Team name")
    league: Optional[str] = Field(default=None, description="League name")
    created_at: Optional[datetime] = Field(default=None)
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "John Doe",
                "team": "Yankees",
                "league": "Major League",
                "created_at": "2024-01-01T00:00:00"
            }
        }

