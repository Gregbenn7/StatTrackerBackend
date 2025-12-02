"""Stats-related API routes."""

import logging
from typing import List, Optional
from fastapi import APIRouter, Query, Depends
from app.schemas.responses import LeaderboardEntry
from app.services.stats_service import StatsService
from app.api.deps import get_stats_service
from app.repositories.stats_repository import StatsRepository
from app.repositories.player_repository import PlayerRepository
from app.api.deps import get_stats_repo, get_player_repo
from app.utils.stat_calculators import compute_derived_stats_from_raw

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/leaderboard", response_model=List[LeaderboardEntry])
def get_leaderboard(
    league: Optional[str] = Query(None),
    season: Optional[str] = Query(None),
    team: Optional[str] = Query(None),
    stats_repo: StatsRepository = Depends(get_stats_repo),
    player_repo: PlayerRepository = Depends(get_player_repo),
):
    """
    Get hitting leaderboard, ordered by OPS descending.
    
    Query params:
        league: Filter by league (optional)
        season: Filter by season (optional)
        team: Filter by team name (optional)
    """
    # Normalize empty strings to None
    if league == "":
        league = None
    if season == "":
        season = None
    if team == "":
        team = None
    
    logger.info("=" * 60)
    logger.info("=== LEADERBOARD REQUEST ===")
    logger.info(f"Filters: league={league}, season={season}, team={team}")
    
    # Import store to check total data
    from app.storage.memory_store import store
    logger.info(f"📊 Current data in memory:")
    logger.info(f"   - Total games: {len(store._games)}")
    logger.info(f"   - Total plate appearances: {len(store._plate_appearances)}")
    logger.info(f"   - Total players: {len(store._players)}")
    logger.info("=" * 60)
    
    # Get hitter totals (filtered by team if provided via plate appearances)
    if team:
        # Normalize team name (strip whitespace)
        team_normalized = team.strip()
        
        # If team filter is provided, get plate appearances and aggregate
        plate_apps = stats_repo.get_plate_appearances_by_team(
            team_name=team_normalized,
            league=league,
            season=season
        )
        logger.info(f"Team filter '{team_normalized}': Found {len(plate_apps)} plate appearances")
        # Aggregate by player from plate appearances
        player_aggregates = {}
        players = {p.id: p for p in player_repo.get_all()}
        
        for pa in plate_apps:
            player = players.get(pa.player_id)
            if not player:
                continue
            
            if pa.player_id not in player_aggregates:
                player_aggregates[pa.player_id] = {
                    'player': player,
                    'games': set(),
                    'AB': 0,
                    'H': 0,
                    'double': 0,
                    'triple': 0,
                    'HR': 0,
                    'RBI': 0,
                    'BB': 0,
                    'HBP': 0,
                    'SF': 0,
                    'SH': 0,
                }
            
            agg = player_aggregates[pa.player_id]
            agg['games'].add(pa.game_id)
            agg['AB'] += pa.AB
            agg['H'] += pa.H
            agg['double'] += pa.double
            agg['triple'] += pa.triple
            agg['HR'] += pa.HR
            agg['RBI'] += pa.RBI
            agg['BB'] += pa.BB
            agg['HBP'] += pa.HBP
            agg['SF'] += pa.SF
            agg['SH'] += pa.SH
        
        # Convert games set to count and compute stats
        entries = []
        for player_id, agg in player_aggregates.items():
            player = agg['player']
            derived = compute_derived_stats_from_raw(
                ab=agg['AB'],
                h=agg['H'],
                double=agg['double'],
                triple=agg['triple'],
                hr=agg['HR'],
                bb=agg['BB'],
                hbp=agg['HBP'],
                sf=agg['SF'],
                sh=agg['SH']
            )
            
            entries.append(LeaderboardEntry(
                player_id=player.id,
                player_name=player.name,
                team=player.team,
                games=len(agg['games']),
                AB=agg['AB'],
                H=agg['H'],
                HR=agg['HR'],
                RBI=agg['RBI'],
                AVG=derived['AVG'],
                OBP=derived['OBP'],
                SLG=derived['SLG'],
                OPS=derived['OPS']
            ))
        
        entries.sort(key=lambda x: x.OPS, reverse=True)
        return entries
    
    # Get hitter totals (original logic)
    hitter_totals = stats_repo.get_hitter_totals(league=league, season=season)
    players = {p.id: p for p in player_repo.get_all()}
    
    logger.info(f"Found {len(hitter_totals)} HitterTotal records")
    logger.info(f"Found {len(players)} total players in system")
    
    # Aggregate stats per player to avoid duplicates
    needs_aggregation = not (league and season)
    logger.info(f"Needs aggregation: {needs_aggregation}")
    
    if needs_aggregation:
        logger.info("Aggregating stats per player...")
        player_aggregates = {}
        for hitter_total in hitter_totals:
            player = players.get(hitter_total.player_id)
            if not player:
                continue
                
            player_id = player.id
            if player_id not in player_aggregates:
                player_aggregates[player_id] = {
                    'player': player,
                    'games': 0,
                    'AB': 0,
                    'H': 0,
                    'double': 0,
                    'triple': 0,
                    'HR': 0,
                    'RBI': 0,
                    'BB': 0,
                    'HBP': 0,
                    'SF': 0,
                    'SH': 0,
                }
            
            agg = player_aggregates[player_id]
            agg['games'] += hitter_total.games
            agg['AB'] += hitter_total.AB
            agg['H'] += hitter_total.H
            agg['double'] += hitter_total.double
            agg['triple'] += hitter_total.triple
            agg['HR'] += hitter_total.HR
            agg['RBI'] += hitter_total.RBI
            agg['BB'] += hitter_total.BB
            agg['HBP'] += hitter_total.HBP
            agg['SF'] += hitter_total.SF
            agg['SH'] += hitter_total.SH
        
        # Compute derived stats for each aggregated player
        entries = []
        for player_id, agg in player_aggregates.items():
            player = agg['player']
            derived = compute_derived_stats_from_raw(
                ab=agg['AB'],
                h=agg['H'],
                double=agg['double'],
                triple=agg['triple'],
                hr=agg['HR'],
                bb=agg['BB'],
                hbp=agg['HBP'],
                sf=agg['SF'],
                sh=agg['SH']
            )
            
            entries.append(LeaderboardEntry(
                player_id=player.id,
                player_name=player.name,
                team=player.team,
                games=agg['games'],
                AB=agg['AB'],
                H=agg['H'],
                HR=agg['HR'],
                RBI=agg['RBI'],
                AVG=derived['AVG'],
                OBP=derived['OBP'],
                SLG=derived['SLG'],
                OPS=derived['OPS']
            ))
        
        # Sort by OPS descending
        entries.sort(key=lambda x: x.OPS, reverse=True)
        logger.info(f"Returning {len(entries)} aggregated entries")
        logger.info("=" * 60)
        return entries
    else:
        logger.info("Using filtered results without aggregation")
        entries = []
        for hitter_total in hitter_totals:
            player = players.get(hitter_total.player_id)
            if not player:
                continue
            entries.append(LeaderboardEntry(
                player_id=player.id,
                player_name=player.name,
                team=player.team,
                games=hitter_total.games,
                AB=hitter_total.AB,
                H=hitter_total.H,
                HR=hitter_total.HR,
                RBI=hitter_total.RBI,
                AVG=hitter_total.AVG,
                OBP=hitter_total.OBP,
                SLG=hitter_total.SLG,
                OPS=hitter_total.OPS
            ))
        
        # Sort by OPS descending
        entries.sort(key=lambda x: x.OPS, reverse=True)
        logger.info(f"Returning {len(entries)} entries (no aggregation needed)")
        logger.info("=" * 60)
        return entries

