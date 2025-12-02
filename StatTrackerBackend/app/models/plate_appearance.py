"""PlateAppearance model."""

from typing import Optional
from pydantic import BaseModel, Field


class PlateAppearance(BaseModel):
    """Plate appearance model representing a player's stats in a single game."""
    
    id: Optional[int] = Field(default=None)
    game_id: int = Field(..., description="Game ID")
    player_id: int = Field(..., description="Player ID")
    team: str = Field(..., description="Team name")
    
    # Counting stats
    AB: int = Field(default=0, description="At bats")
    H: int = Field(default=0, description="Hits")
    double: int = Field(default=0, description="Doubles")
    triple: int = Field(default=0, description="Triples")
    HR: int = Field(default=0, description="Home runs")
    BB: int = Field(default=0, description="Walks")
    HBP: int = Field(default=0, description="Hit by pitch")
    SF: int = Field(default=0, description="Sacrifice fly")
    SH: int = Field(default=0, description="Sacrifice bunt")
    K: int = Field(default=0, description="Strikeouts")
    R: int = Field(default=0, description="Runs")
    RBI: int = Field(default=0, description="Runs batted in")
    SB: int = Field(default=0, description="Stolen bases")
    CS: int = Field(default=0, description="Caught stealing")
    
    # Raw JSON for reference
    raw_json: Optional[str] = Field(default=None, description="Raw CSV row data as JSON")
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "id": 1,
                "game_id": 1,
                "player_id": 1,
                "team": "Yankees",
                "AB": 4,
                "H": 2,
                "double": 1,
                "triple": 0,
                "HR": 0,
                "BB": 1,
                "HBP": 0,
                "SF": 0,
                "SH": 0,
                "K": 1,
                "R": 1,
                "RBI": 2,
                "SB": 0,
                "CS": 0
            }
        }

