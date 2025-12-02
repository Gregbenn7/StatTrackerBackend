"""Player-related API routes."""

import logging
import json
from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException, Depends
from openai import OpenAI
from app.schemas.responses import PlayerStats, PlayerDetail, ScoutingReportResponse
from app.services.player_service import PlayerService
from app.services.stats_service import StatsService
from app.api.deps import get_player_service, get_stats_service
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/players", tags=["players"])


@router.get("", response_model=List[PlayerStats])
def get_players(
    league: Optional[str] = Query(None),
    season: Optional[str] = Query(None),
    team: Optional[str] = Query(None),
    stats_service: StatsService = Depends(get_stats_service),
):
    """Get all players with their stats grouped by (team, player_name, league, season)."""
    stats_list = stats_service.get_player_stats_by_team(
        league=league,
        season=season,
        team=team
    )
    
    if not stats_list:
        return []
    
    # Convert to Pydantic models
    player_stats_list = []
    for stats in stats_list:
        player_stats_list.append(PlayerStats(**stats))
    
    return player_stats_list


@router.get("/{player_id}", response_model=PlayerDetail)
def get_player(
    player_id: int,
    player_service: PlayerService = Depends(get_player_service),
    stats_service: StatsService = Depends(get_stats_service),
):
    """Get a specific player's info and all their stats."""
    player = player_service.get_player(player_id)
    if not player:
        raise HTTPException(status_code=404, detail=f"Player {player_id} not found")
    
    # Get all hitter totals for this player
    from app.repositories.stats_repository import StatsRepository
    from app.api.deps import get_stats_repo
    stats_repo = get_stats_repo()
    hitter_totals = stats_repo.get_hitter_totals_by_player(player_id)
    
    stats_list = []
    for ht in hitter_totals:
        stats_list.append(PlayerStats(
            player_id=player.id,
            player_name=player.name,
            team=player.team,
            league=ht.league,
            season=ht.season,
            games=ht.games,
            AB=ht.AB,
            H=ht.H,
            singles=ht.singles,
            double=ht.double,
            triple=ht.triple,
            HR=ht.HR,
            BB=ht.BB,
            HBP=ht.HBP,
            SF=ht.SF,
            SH=ht.SH,
            K=ht.K,
            R=ht.R,
            RBI=ht.RBI,
            SB=ht.SB,
            CS=ht.CS,
            PA=ht.PA,
            TB=ht.TB,
            AVG=ht.AVG,
            OBP=ht.OBP,
            SLG=ht.SLG,
            OPS=ht.OPS
        ))
    
    return PlayerDetail(
        id=player.id,
        name=player.name,
        team=player.team,
        league=player.league,
        created_at=player.created_at or None,
        stats=stats_list
    )


@router.get("/{player_id}/scouting_report", response_model=ScoutingReportResponse)
def get_player_scouting_report(
    player_id: int,
    player_service: PlayerService = Depends(get_player_service),
):
    """Generate an AI scouting report for a player."""
    player = player_service.get_player(player_id)
    if not player:
        raise HTTPException(status_code=404, detail=f"Player {player_id} not found")
    
    # Get all hitter totals for this player
    from app.repositories.stats_repository import StatsRepository
    from app.api.deps import get_stats_repo
    stats_repo = get_stats_repo()
    hitter_totals = stats_repo.get_hitter_totals_by_player(player_id)
    
    if not hitter_totals:
        raise HTTPException(status_code=404, detail=f"No stats found for player {player_id}")
    
    # Build stats summary
    stats_summary = []
    for ht in hitter_totals:
        stats_summary.append({
            "league": ht.league,
            "season": ht.season,
            "games": ht.games,
            "AB": ht.AB,
            "H": ht.H,
            "HR": ht.HR,
            "RBI": ht.RBI,
            "AVG": ht.AVG,
            "OBP": ht.OBP,
            "SLG": ht.SLG,
            "OPS": ht.OPS
        })
    
    # Check if OpenAI is configured
    if not settings.OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
    
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    prompt = f"""You are a baseball scout analyzing a HitTrax adult league player. Given this player's stats across multiple seasons/leagues, write a brief scouting report (2-3 paragraphs) covering:

- Overall hitting profile and strengths
- Areas for improvement or notable trends
- Projected role/value

Player: {player.name}
Team: {player.team}

Stats by league/season:
{json.dumps(stats_summary, indent=2)}

Write the scouting report in a professional but accessible tone."""
    
    try:
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a professional baseball scout."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        report = response.choices[0].message.content
        
        return ScoutingReportResponse(
            player_id=player_id,
            report=report
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating scouting report: {str(e)}")


@router.get("/teams/list")
def get_teams(
    league: Optional[str] = Query(None),
    stats_service: StatsService = Depends(get_stats_service),
):
    """Get list of unique teams, optionally filtered by league."""
    from app.api.deps import get_stats_repo
    stats_repo = get_stats_repo()
    teams = stats_repo.get_unique_teams(league=league)
    return {"teams": teams}

