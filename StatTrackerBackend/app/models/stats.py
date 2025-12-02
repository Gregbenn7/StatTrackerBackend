"""Stats models."""

from typing import Optional
from pydantic import BaseModel, Field


class HitterTotal(BaseModel):
    """Hitter total model representing aggregated season stats for a player."""
    
    id: Optional[int] = Field(default=None)
    player_id: int = Field(..., description="Player ID")
    league: str = Field(..., description="League name")
    season: str = Field(..., description="Season identifier")
    
    games: int = Field(default=0, description="Games played")
    
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
    
    # Derived stats
    singles: int = Field(default=0, description="Singles")
    PA: int = Field(default=0, description="Plate appearances")
    TB: int = Field(default=0, description="Total bases")
    
    # Rate stats
    AVG: float = Field(default=0.0, description="Batting average")
    OBP: float = Field(default=0.0, description="On-base percentage")
    SLG: float = Field(default=0.0, description="Slugging percentage")
    OPS: float = Field(default=0.0, description="On-base plus slugging")
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "id": 1,
                "player_id": 1,
                "league": "Major League",
                "season": "2024",
                "games": 10,
                "AB": 40,
                "H": 12,
                "double": 2,
                "triple": 1,
                "HR": 2,
                "BB": 5,
                "HBP": 1,
                "SF": 0,
                "SH": 0,
                "K": 8,
                "R": 10,
                "RBI": 8,
                "SB": 2,
                "CS": 0,
                "singles": 7,
                "PA": 46,
                "TB": 22,
                "AVG": 0.300,
                "OBP": 0.391,
                "SLG": 0.550,
                "OPS": 0.941
            }
        }

