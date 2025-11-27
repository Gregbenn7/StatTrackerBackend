"""Player service for business logic."""

from typing import List, Optional
from app.models.player import Player
from app.repositories.player_repository import PlayerRepository


class PlayerService:
    """Service for player-related business logic."""
    
    def __init__(self, player_repo: PlayerRepository):
        """Initialize the player service."""
        self.player_repo = player_repo
    
    def create_player(self, player: Player) -> Player:
        """Create a new player."""
        return self.player_repo.create(player)
    
    def get_player(self, player_id: int) -> Optional[Player]:
        """Get a player by ID."""
        return self.player_repo.get(player_id)
    
    def get_player_by_name_team(self, name: str, team: str) -> Optional[Player]:
        """Find a player by name and team."""
        return self.player_repo.get_by_name_team(name, team)
    
    def get_all_players(self) -> List[Player]:
        """Get all players."""
        return self.player_repo.get_all()

