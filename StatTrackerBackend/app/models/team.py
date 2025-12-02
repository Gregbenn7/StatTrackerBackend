"""Team models."""

from typing import Optional
from pydantic import BaseModel, Field


class Team(BaseModel):
    """Team model."""
    
    name: str = Field(..., description="Team name")
    league: str = Field(..., description="League name")
    season: str = Field(..., description="Season identifier")


class TeamStats(BaseModel):
    """Aggregated team statistics."""
    
    name: str = Field(..., description="Team name")
    league: str = Field(..., description="League name")
    season: str = Field(..., description="Season identifier")
    games_played: int = Field(default=0, description="Games played")
    wins: int = Field(default=0, description="Wins")
    losses: int = Field(default=0, description="Losses")
    win_pct: float = Field(default=0.0, description="Win percentage")
    runs_scored: int = Field(default=0, description="Total runs scored")
    runs_allowed: int = Field(default=0, description="Total runs allowed")
    run_differential: int = Field(default=0, description="Run differential")
    team_avg: float = Field(default=0.0, description="Team batting average")
    team_obp: float = Field(default=0.0, description="Team on-base percentage")
    team_slg: float = Field(default=0.0, description="Team slugging percentage")
    team_ops: float = Field(default=0.0, description="Team OPS")


class TeamStanding(BaseModel):
    """Team standing in league."""
    
    rank: int = Field(..., description="Standing rank")
    name: str = Field(..., description="Team name")
    wins: int = Field(..., description="Wins")
    losses: int = Field(..., description="Losses")
    win_pct: float = Field(..., description="Win percentage")
    games_behind: float = Field(default=0.0, description="Games behind first place")
    runs_scored: int = Field(..., description="Runs scored")
    runs_allowed: int = Field(..., description="Runs allowed")
    run_differential: int = Field(..., description="Run differential")

