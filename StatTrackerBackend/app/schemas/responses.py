"""Response schemas."""

from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel


class UploadCsvResponse(BaseModel):
    """Response schema for CSV upload."""
    game_id: int
    rows_ingested: int
    message: str


# Keep alias for backward compatibility
CsvUploadResponse = UploadCsvResponse


class LeaderboardEntry(BaseModel):
    """Leaderboard entry response schema."""
    player_id: int
    player_name: str
    team: str
    games: int
    AB: int
    H: int
    HR: int
    RBI: int
    AVG: float
    OBP: float
    SLG: float
    OPS: float


class PlayerBasic(BaseModel):
    """Basic player information."""
    id: int
    name: str
    team: str
    league: Optional[str] = None


class PlayerStats(BaseModel):
    """Player statistics response schema."""
    player_id: int
    player_name: str
    team: str
    league: str
    season: str
    games: int
    AB: int
    H: int
    singles: int
    double: int
    triple: int
    HR: int
    BB: int
    HBP: int
    SF: int
    SH: int
    K: int
    R: int
    RBI: int
    SB: int
    CS: int
    PA: int
    TB: int
    AVG: float
    OBP: float
    SLG: float
    OPS: float


class PlayerDetail(BaseModel):
    """Detailed player information with stats."""
    id: int
    name: str
    team: str
    league: Optional[str]
    created_at: datetime
    stats: List[PlayerStats]


class GameBasic(BaseModel):
    """Basic game information."""
    id: int
    league: str
    season: str
    date: date
    home_team: str
    away_team: str
    home_score: int = 0
    away_score: int = 0
    winner: Optional[str] = None


class PlateAppearanceDetail(BaseModel):
    """Plate appearance detail for game responses."""
    id: int
    player_name: str
    team: str
    AB: int
    H: int
    HR: int
    RBI: int
    AVG: float


class GameDetail(BaseModel):
    """Detailed game information with plate appearances."""
    id: int
    league: str
    season: str
    date: date
    home_team: str
    away_team: str
    home_score: int = 0
    away_score: int = 0
    winner: Optional[str] = None
    created_at: datetime
    plate_appearances: List[PlateAppearanceDetail]


class StorylineSummary(BaseModel):
    """Storyline summary extracted from JSON."""
    recap: str
    key_storylines: List[str]
    player_of_game: str
    social_captions: List[str]


class GameStorylinesResponse(BaseModel):
    """Game storylines response schema."""
    game_id: int
    storylines_text: str
    json_summary: str
    created_at: datetime
    summary: StorylineSummary


class ScoutingReportResponse(BaseModel):
    """Scouting report response schema."""
    player_id: int
    report: str

