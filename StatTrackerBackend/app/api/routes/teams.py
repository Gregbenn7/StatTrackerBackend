"""Team-related API routes."""

import logging
from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException, Depends
from app.models.team import TeamStats
from app.services.team_service import TeamService
from app.repositories.game_repository import GameRepository
from app.repositories.stats_repository import StatsRepository
from app.repositories.player_repository import PlayerRepository
from app.api.deps import get_game_repo, get_stats_repo, get_player_repo
from app.storage.memory_store import store

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/teams", tags=["teams"])


def get_team_service() -> TeamService:
    """Get team service instance."""
    game_repo = get_game_repo()
    stats_repo = get_stats_repo()
    player_repo = get_player_repo()
    return TeamService(store, game_repo, stats_repo, player_repo)


@router.get("/", response_model=List[TeamStats])
def get_teams(
    league: Optional[str] = Query(None),
    season: Optional[str] = Query(None),
    team_service: TeamService = Depends(get_team_service),
):
    """
    Get all teams with their records and stats.
    
    Query params:
        league: Filter by league (optional, None = show all)
        season: Filter by season (optional, None = show all)
    
    Returns:
        List of TeamStats sorted by win percentage
    """
    # Normalize empty strings to None
    if league == "":
        league = None
    if season == "":
        season = None
    
    logger.info("=" * 60)
    logger.info("=== TEAMS REQUEST ===")
    logger.info(f"Filters: league={league}, season={season}")
    
    # Import store to check total data
    from app.storage.memory_store import store
    logger.info(f"📊 Current data in memory:")
    logger.info(f"   - Total games: {len(store._games)}")
    logger.info(f"   - Total plate appearances: {len(store._plate_appearances)}")
    
    teams = team_service.get_all_teams(league=league, season=season)
    
    logger.info(f"Found {len(teams)} unique teams:")
    for team in teams:
        logger.info(f"   - {team.name}: {team.wins}W-{team.losses}L ({team.games_played} GP)")
    logger.info("=" * 60)
    
    return teams


@router.get("/{team_name}/stats", response_model=TeamStats)
def get_team_stats(
    team_name: str,
    league: str = Query(...),
    season: str = Query(...),
    team_service: TeamService = Depends(get_team_service),
):
    """
    Get detailed stats for a specific team.
    
    Path params:
        team_name: Name of the team
    
    Query params:
        league: League name (required)
        season: Season (required)
    
    Returns:
        TeamStats object
    """
    teams = team_service.get_all_teams(league=league, season=season)
    team = next((t for t in teams if t.name == team_name), None)
    
    if not team:
        raise HTTPException(status_code=404, detail=f"Team '{team_name}' not found")
    
    return team


@router.get("/{team_name}/roster")
def get_team_roster(
    team_name: str,
    league: Optional[str] = Query(None),
    season: Optional[str] = Query(None),
    team_service: TeamService = Depends(get_team_service),
):
    """
    Get all players on a team with their aggregated stats.
    
    Path params:
        team_name: Name of the team
    
    Query params:
        league: Filter by league (optional)
        season: Filter by season (optional)
    
    Returns:
        List of player stat dictionaries
    """
    roster = team_service.get_team_roster(team_name, league=league, season=season)
    
    if not roster:
        raise HTTPException(
            status_code=404, 
            detail=f"No players found for team '{team_name}'"
        )
    
    return roster


@router.get("/{team_name}/games")
def get_team_games(
    team_name: str,
    league: Optional[str] = Query(None),
    season: Optional[str] = Query(None),
    team_service: TeamService = Depends(get_team_service),
):
    """
    Get all games for a specific team.
    
    Path params:
        team_name: Name of the team
    
    Query params:
        league: Filter by league (optional)
        season: Filter by season (optional)
    
    Returns:
        List of Game objects where team participated
    """
    games = team_service.get_team_games(team_name, league=league, season=season)
    
    if not games:
        raise HTTPException(
            status_code=404,
            detail=f"No games found for team '{team_name}'"
        )
    
    return games

