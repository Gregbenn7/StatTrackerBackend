"""Request schemas."""

from pydantic import BaseModel


class UploadCsvRequest(BaseModel):
    """Request schema for CSV upload (used internally, not directly in API)."""
    
    league: str
    season: str
    date_str: str  # YYYY-MM-DD format
    home_team: str
    away_team: str

