"""Stats repository for data access."""

from typing import Optional, List
from app.models.stats import HitterTotal
from app.models.plate_appearance import PlateAppearance
from app.storage.memory_store import store


class StatsRepository:
    """Repository for statistics data access."""
    
    def create_plate_appearance(self, plate_app: PlateAppearance) -> PlateAppearance:
        """Create a new plate appearance."""
        return store.create_plate_appearance(plate_app)
    
    def get_plate_appearances_by_game(self, game_id: int) -> List[PlateAppearance]:
        """Get all plate appearances for a game."""
        return store.get_plate_appearances_by_game(game_id)
    
    def get_plate_appearances_by_player(self, player_id: int) -> List[PlateAppearance]:
        """Get all plate appearances for a player."""
        return store.get_plate_appearances_by_player(player_id)
    
    def create_or_update_hitter_total(self, hitter_total: HitterTotal) -> HitterTotal:
        """Create or update a hitter total."""
        return store.create_or_update_hitter_total(hitter_total)
    
    def get_hitter_total(
        self, player_id: int, league: str, season: str
    ) -> Optional[HitterTotal]:
        """Get a hitter total by player, league, and season."""
        return store.get_hitter_total(player_id, league, season)
    
    def get_hitter_totals(
        self, league: Optional[str] = None, season: Optional[str] = None
    ) -> List[HitterTotal]:
        """Get hitter totals with optional filtering."""
        return store.get_hitter_totals(league=league, season=season)
    
    def get_hitter_totals_by_player(self, player_id: int) -> List[HitterTotal]:
        """Get all hitter totals for a player."""
        return store.get_hitter_totals_by_player(player_id)
    
    def get_unique_teams(self, league: Optional[str] = None) -> List[str]:
        """Get unique team names."""
        return store.get_unique_teams(league=league)
    
    def get_plate_appearances_by_team(
        self,
        team_name: str,
        league: Optional[str] = None,
        season: Optional[str] = None
    ) -> List[PlateAppearance]:
        """Get all plate appearances for a team with optional filters."""
        return store.get_plate_appearances_by_team(
            team_name=team_name,
            league=league,
            season=season
        )

