"""Dependency injection for routes."""

from app.repositories.game_repository import GameRepository
from app.repositories.player_repository import PlayerRepository
from app.repositories.stats_repository import StatsRepository
from app.services.ingest_service import IngestService
from app.services.stats_service import StatsService
from app.services.game_service import GameService
from app.services.player_service import PlayerService
from app.services.storyline_service import StorylineService


# Create repository instances (singletons)
_game_repo = GameRepository()
_player_repo = PlayerRepository()
_stats_repo = StatsRepository()

# Create service instances
_ingest_service = IngestService(_game_repo, _player_repo, _stats_repo)
_stats_service = StatsService(_stats_repo, _game_repo, _player_repo)
_game_service = GameService(_game_repo)
_player_service = PlayerService(_player_repo)
_storyline_service = StorylineService()


def get_ingest_service() -> IngestService:
    """Get ingest service instance."""
    return _ingest_service


def get_stats_service() -> StatsService:
    """Get stats service instance."""
    return _stats_service


def get_game_service() -> GameService:
    """Get game service instance."""
    return _game_service


def get_player_service() -> PlayerService:
    """Get player service instance."""
    return _player_service


def get_storyline_service() -> StorylineService:
    """Get storyline service instance."""
    return _storyline_service


def get_game_repo() -> GameRepository:
    """Get game repository instance."""
    return _game_repo


def get_player_repo() -> PlayerRepository:
    """Get player repository instance."""
    return _player_repo


def get_stats_repo() -> StatsRepository:
    """Get stats repository instance."""
    return _stats_repo

