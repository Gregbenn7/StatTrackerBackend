"""Game service for business logic."""

from typing import List, Optional
from app.models.game import Game
from app.repositories.game_repository import GameRepository


class GameService:
    """Service for game-related business logic."""
    
    def __init__(self, game_repo: GameRepository):
        """Initialize the game service."""
        self.game_repo = game_repo
    
    def create_game(self, game: Game) -> Game:
        """Create a new game."""
        return self.game_repo.create(game)
    
    def get_game(self, game_id: int) -> Optional[Game]:
        """Get a game by ID."""
        return self.game_repo.get(game_id)
    
    def get_games(
        self,
        limit: int = 50,
        offset: int = 0,
        league: Optional[str] = None,
        season: Optional[str] = None
    ) -> List[Game]:
        """Get games with optional filtering and pagination."""
        return self.game_repo.get_all(limit=limit, offset=offset, league=league, season=season)

