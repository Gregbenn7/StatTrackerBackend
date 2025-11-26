from typing import Optional, List
from pydantic import BaseModel
from datetime import date, datetime


class UploadCsvResponse(BaseModel):
    game_id: int
    rows_ingested: int
    message: str


# Keep alias for backward compatibility
CsvUploadResponse = UploadCsvResponse


class LeaderboardEntry(BaseModel):
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
    id: int
    name: str
    team: str
    league: Optional[str] = None


class PlayerStats(BaseModel):
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
    id: int
    name: str
    team: str
    league: Optional[str]
    created_at: datetime
    stats: List[PlayerStats]


class GameBasic(BaseModel):
    id: int
    league: str
    season: str
    date: date
    home_team: str
    away_team: str


class PlateAppearanceDetail(BaseModel):
    id: int
    player_name: str
    team: str
    AB: int
    H: int
    HR: int
    RBI: int
    AVG: float


class GameDetail(BaseModel):
    id: int
    league: str
    season: str
    date: date
    home_team: str
    away_team: str
    created_at: datetime
    plate_appearances: List[PlateAppearanceDetail]


class StorylineSummary(BaseModel):
    recap: str
    key_storylines: List[str]
    player_of_game: str
    social_captions: List[str]


class GameStorylinesResponse(BaseModel):
    game_id: int
    storylines_text: str
    json_summary: str
    created_at: datetime
    summary: StorylineSummary


class ScoutingReportResponse(BaseModel):
    player_id: int
    report: str

