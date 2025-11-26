from datetime import datetime, date
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, Integer, Date, DateTime, Text, JSON
from sqlalchemy.sql import func


class Player(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    team: str = Field(index=True)
    league: Optional[str] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Game(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    league: str = Field(index=True)
    season: str = Field(index=True)
    date: date
    home_team: str
    away_team: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PlateAppearance(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    game_id: int = Field(foreign_key="game.id", index=True)
    player_id: int = Field(foreign_key="player.id", index=True)
    team: str
    
    # Counting stats
    AB: int = Field(default=0)
    H: int = Field(default=0)
    double: int = Field(default=0)
    triple: int = Field(default=0)
    HR: int = Field(default=0)
    BB: int = Field(default=0)
    HBP: int = Field(default=0)
    SF: int = Field(default=0)
    SH: int = Field(default=0)
    K: int = Field(default=0)
    R: int = Field(default=0)
    RBI: int = Field(default=0)
    SB: int = Field(default=0)
    CS: int = Field(default=0)
    
    # Store raw JSON for reference
    raw_json: Optional[str] = Field(default=None)


class HitterTotal(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    player_id: int = Field(foreign_key="player.id", index=True)
    league: str = Field(index=True)
    season: str = Field(index=True)
    
    games: int = Field(default=0)
    
    # Counting stats
    AB: int = Field(default=0)
    H: int = Field(default=0)
    double: int = Field(default=0)
    triple: int = Field(default=0)
    HR: int = Field(default=0)
    BB: int = Field(default=0)
    HBP: int = Field(default=0)
    SF: int = Field(default=0)
    SH: int = Field(default=0)
    K: int = Field(default=0)
    R: int = Field(default=0)
    RBI: int = Field(default=0)
    SB: int = Field(default=0)
    CS: int = Field(default=0)
    
    # Derived stats
    singles: int = Field(default=0)
    PA: int = Field(default=0)
    TB: int = Field(default=0)
    
    # Rate stats
    AVG: float = Field(default=0.0)
    OBP: float = Field(default=0.0)
    SLG: float = Field(default=0.0)
    OPS: float = Field(default=0.0)


class GameStorylines(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    game_id: int = Field(foreign_key="game.id", unique=True, index=True)
    storylines_text: str = Field(sa_column=Column(Text))
    json_summary: str = Field(sa_column=Column(Text))
    created_at: datetime = Field(default_factory=datetime.utcnow)

