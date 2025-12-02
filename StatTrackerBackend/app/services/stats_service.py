"""Stats calculation service."""

from typing import List, Optional, Dict
from app.models.stats import HitterTotal
from app.models.plate_appearance import PlateAppearance
from app.models.game import Game
from app.repositories.stats_repository import StatsRepository
from app.repositories.game_repository import GameRepository
from app.repositories.player_repository import PlayerRepository
from app.utils.stat_calculators import compute_derived_stats, compute_derived_stats_from_raw, get_game_avg
from app.storage.memory_store import store


class StatsService:
    """Service for statistics calculations."""
    
    def __init__(
        self,
        stats_repo: StatsRepository,
        game_repo: GameRepository,
        player_repo: PlayerRepository
    ):
        """Initialize the stats service."""
        self.stats_repo = stats_repo
        self.game_repo = game_repo
        self.player_repo = player_repo
    
    def recompute_hitter_totals(self, league: str, season: str) -> None:
        """Recompute all HitterTotal records for a given league and season."""
        import logging
        logger = logging.getLogger(__name__)
        
        # Get all plate appearances for this league/season
        all_pas = store.get_all_plate_appearances()
        games = {g.id: g for g in store.get_games(limit=10000)}
        
        logger.info(f"Recomputing hitter totals: Found {len(all_pas)} total PAs, {len(games)} total games")
        
        # Filter by league/season
        relevant_pas = [
            pa for pa in all_pas
            if pa.game_id in games and games[pa.game_id].league == league and games[pa.game_id].season == season
        ]
        
        logger.info(f"Filtered to {len(relevant_pas)} PAs for league={league}, season={season}")
        
        # Group by player_id
        player_stats: Dict[int, Dict] = {}
        for pa in relevant_pas:
            if pa.player_id not in player_stats:
                player_stats[pa.player_id] = {
                    'AB': 0, 'H': 0, 'double': 0, 'triple': 0, 'HR': 0,
                    'BB': 0, 'HBP': 0, 'SF': 0, 'SH': 0, 'K': 0,
                    'R': 0, 'RBI': 0, 'SB': 0, 'CS': 0,
                    'games': set()
                }
            
            stats = player_stats[pa.player_id]
            stats['AB'] += pa.AB
            stats['H'] += pa.H
            stats['double'] += pa.double
            stats['triple'] += pa.triple
            stats['HR'] += pa.HR
            stats['BB'] += pa.BB
            stats['HBP'] += pa.HBP
            stats['SF'] += pa.SF
            stats['SH'] += pa.SH
            stats['K'] += pa.K
            stats['R'] += pa.R
            stats['RBI'] += pa.RBI
            stats['SB'] += pa.SB
            stats['CS'] += pa.CS
            stats['games'].add(pa.game_id)
        
        # Update or create HitterTotal records
        for player_id, stats in player_stats.items():
            hitter_total = self.stats_repo.get_hitter_total(player_id, league, season)
            
            if hitter_total is None:
                hitter_total = HitterTotal(
                    player_id=player_id,
                    league=league,
                    season=season
                )
            
            # Update stats
            hitter_total.games = len(stats['games'])
            hitter_total.AB = stats['AB']
            hitter_total.H = stats['H']
            hitter_total.double = stats['double']
            hitter_total.triple = stats['triple']
            hitter_total.HR = stats['HR']
            hitter_total.BB = stats['BB']
            hitter_total.HBP = stats['HBP']
            hitter_total.SF = stats['SF']
            hitter_total.SH = stats['SH']
            hitter_total.K = stats['K']
            hitter_total.R = stats['R']
            hitter_total.RBI = stats['RBI']
            hitter_total.SB = stats['SB']
            hitter_total.CS = stats['CS']
            
            # Compute derived stats
            compute_derived_stats(hitter_total)
            
            self.stats_repo.create_or_update_hitter_total(hitter_total)
    
    def get_player_stats_by_team(
        self,
        league: Optional[str] = None,
        season: Optional[str] = None,
        team: Optional[str] = None
    ) -> List[Dict]:
        """Get aggregated player stats grouped by (team, player_name, league, season)."""
        all_pas = store.get_all_plate_appearances()
        games = {g.id: g for g in store.get_games(limit=10000)}
        players = {p.id: p for p in store.get_all_players()}
        
        # Filter plate appearances
        filtered_pas = []
        for pa in all_pas:
            game = games.get(pa.game_id)
            if not game:
                continue
            if league and game.league != league:
                continue
            if season and game.season != season:
                continue
            if team and pa.team != team:
                continue
            filtered_pas.append((pa, game))
        
        # Group by (team, player_name, league, season)
        stats_dict: Dict[tuple, Dict] = {}
        
        for pa, game in filtered_pas:
            player = players.get(pa.player_id)
            if not player:
                continue
            
            key = (pa.team, player.name, game.league, game.season)
            
            if key not in stats_dict:
                stats_dict[key] = {
                    'player_id': player.id,
                    'player_name': player.name,
                    'team': pa.team,
                    'league': game.league,
                    'season': game.season,
                    'games': set(),
                    'AB': 0, 'H': 0, 'double': 0, 'triple': 0, 'HR': 0,
                    'BB': 0, 'HBP': 0, 'SF': 0, 'SH': 0, 'K': 0,
                    'R': 0, 'RBI': 0, 'SB': 0, 'CS': 0,
                }
            
            stats = stats_dict[key]
            stats['AB'] += pa.AB
            stats['H'] += pa.H
            stats['double'] += pa.double
            stats['triple'] += pa.triple
            stats['HR'] += pa.HR
            stats['BB'] += pa.BB
            stats['HBP'] += pa.HBP
            stats['SF'] += pa.SF
            stats['SH'] += pa.SH
            stats['K'] += pa.K
            stats['R'] += pa.R
            stats['RBI'] += pa.RBI
            stats['SB'] += pa.SB
            stats['CS'] += pa.CS
            stats['games'].add(game.id)
        
        # Convert to list and compute derived stats
        result_list = []
        for key, stats in stats_dict.items():
            stats['games'] = len(stats['games'])
            
            # Compute derived stats
            derived = compute_derived_stats_from_raw(
                ab=stats['AB'],
                h=stats['H'],
                double=stats['double'],
                triple=stats['triple'],
                hr=stats['HR'],
                bb=stats['BB'],
                hbp=stats['HBP'],
                sf=stats['SF'],
                sh=stats['SH'],
            )
            
            stats.update(derived)
            result_list.append(stats)
        
        return result_list
    
    @staticmethod
    def get_game_avg(h: int, ab: int) -> float:
        """Compute batting average for a single game plate appearance."""
        return get_game_avg(h, ab)

