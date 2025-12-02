"""Game repository for data access."""

from typing import Optional, List
from app.models.game import Game
from app.storage.memory_store import store


class GameRepository:
    """Repository for game data access."""
    
    def create(self, game: Game) -> Game:
        """Create a new game."""
        return store.create_game(game)
    
    def get(self, game_id: int) -> Optional[Game]:
        """Get a game by ID."""
        return store.get_game(game_id)
    
    def get_all(
        self,
        limit: int = 50,
        offset: int = 0,
        league: Optional[str] = None,
        season: Optional[str] = None
    ) -> List[Game]:
        """Get games with optional filtering and pagination."""
        return store.get_games(limit=limit, offset=offset, league=league, season=season)

