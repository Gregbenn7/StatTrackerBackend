"""Player repository for data access."""

from typing import Optional, List
from app.models.player import Player
from app.storage.memory_store import store


class PlayerRepository:
    """Repository for player data access."""
    
    def create(self, player: Player) -> Player:
        """Create a new player."""
        return store.create_player(player)
    
    def get(self, player_id: int) -> Optional[Player]:
        """Get a player by ID."""
        return store.get_player(player_id)
    
    def get_by_name_team(self, name: str, team: str) -> Optional[Player]:
        """Find a player by name and team."""
        return store.get_player_by_name_team(name, team)
    
    def get_all(self) -> List[Player]:
        """Get all players."""
        return store.get_all_players()

