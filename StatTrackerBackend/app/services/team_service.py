"""Team service for managing team statistics and rosters."""

from typing import List, Optional, Dict
from app.models.team import TeamStats, TeamStanding
from app.repositories.game_repository import GameRepository
from app.repositories.stats_repository import StatsRepository
from app.repositories.player_repository import PlayerRepository
from app.storage.memory_store import MemoryStore


class TeamService:
    """Business logic for team management and statistics."""
    
    def __init__(
        self,
        store: MemoryStore,
        game_repo: GameRepository,
        stats_repo: StatsRepository,
        player_repo: PlayerRepository
    ):
        """Initialize team service with repositories."""
        self.store = store
        self.game_repo = game_repo
        self.stats_repo = stats_repo
        self.player_repo = player_repo
    
    def get_all_teams(
        self, 
        league: Optional[str] = None, 
        season: Optional[str] = None
    ) -> List[TeamStats]:
        """
        Get all unique teams with their records and stats.
        
        Args:
            league: Filter by league (optional)
            season: Filter by season (optional)
        
        Returns:
            List of TeamStats objects sorted by win percentage
        """
        games = self.game_repo.get_all(limit=10000, league=league, season=season)
        
        teams: Dict[str, Dict] = {}
        
        for game in games:
            # Process home team
            if game.home_team not in teams:
                teams[game.home_team] = {
                    'name': game.home_team,
                    'league': game.league,
                    'season': game.season,
                    'wins': 0,
                    'losses': 0,
                    'games_played': 0,
                    'runs_scored': 0,
                    'runs_allowed': 0
                }
            
            team = teams[game.home_team]
            team['games_played'] += 1
            team['runs_scored'] += game.home_score
            team['runs_allowed'] += game.away_score
            
            if game.winner == game.home_team:
                team['wins'] += 1
            elif game.winner and game.winner != "Tie":
                team['losses'] += 1
            elif game.winner is None:
                # Tie game - no win or loss
                pass
            else:
                # Away team won
                team['losses'] += 1
            
            # Process away team
            if game.away_team not in teams:
                teams[game.away_team] = {
                    'name': game.away_team,
                    'league': game.league,
                    'season': game.season,
                    'wins': 0,
                    'losses': 0,
                    'games_played': 0,
                    'runs_scored': 0,
                    'runs_allowed': 0
                }
            
            team = teams[game.away_team]
            team['games_played'] += 1
            team['runs_scored'] += game.away_score
            team['runs_allowed'] += game.home_score
            
            if game.winner == game.away_team:
                team['wins'] += 1
            elif game.winner and game.winner != "Tie":
                team['losses'] += 1
            elif game.winner is None:
                # Tie game - no win or loss
                pass
            else:
                # Home team won
                team['losses'] += 1
        
        # Calculate derived stats
        result = []
        for team_data in teams.values():
            if team_data['games_played'] > 0:
                team_data['win_pct'] = team_data['wins'] / team_data['games_played']
            else:
                team_data['win_pct'] = 0.0
            
            team_data['run_differential'] = (
                team_data['runs_scored'] - team_data['runs_allowed']
            )
            
            # Calculate team batting stats from plate appearances
            plate_apps = self.stats_repo.get_plate_appearances_by_team(
                team_name=team_data['name'],
                league=league,
                season=season
            )
            
            if plate_apps:
                total_ab = sum(pa.AB for pa in plate_apps)
                total_h = sum(pa.H for pa in plate_apps)
                total_singles = total_h - sum(pa.double + pa.triple + pa.HR for pa in plate_apps)
                total_tb = total_singles + (2 * sum(pa.double for pa in plate_apps)) + \
                          (3 * sum(pa.triple for pa in plate_apps)) + (4 * sum(pa.HR for pa in plate_apps))
                total_bb = sum(pa.BB for pa in plate_apps)
                total_hbp = sum(pa.HBP for pa in plate_apps)
                total_sf = sum(pa.SF for pa in plate_apps)
                
                if total_ab > 0:
                    team_data['team_avg'] = total_h / total_ab
                    team_data['team_slg'] = total_tb / total_ab
                else:
                    team_data['team_avg'] = 0.0
                    team_data['team_slg'] = 0.0
                
                total_pa = total_ab + total_bb + total_hbp + total_sf
                if total_pa > 0:
                    team_data['team_obp'] = (total_h + total_bb + total_hbp) / total_pa
                else:
                    team_data['team_obp'] = 0.0
                
                team_data['team_ops'] = team_data['team_obp'] + team_data['team_slg']
            else:
                team_data['team_avg'] = 0.0
                team_data['team_obp'] = 0.0
                team_data['team_slg'] = 0.0
                team_data['team_ops'] = 0.0
            
            result.append(TeamStats(**team_data))
        
        # Sort by win percentage (descending)
        result.sort(key=lambda x: (x.win_pct, x.run_differential), reverse=True)
        
        return result
    
    def get_team_roster(
        self,
        team_name: str,
        league: Optional[str] = None,
        season: Optional[str] = None
    ) -> List[Dict]:
        """
        Get all players on a team with their aggregated stats.
        
        Args:
            team_name: Name of team
            league: Filter by league (optional)
            season: Filter by season (optional)
        
        Returns:
            List of player stat dictionaries
        """
        plate_apps = self.stats_repo.get_plate_appearances_by_team(
            team_name=team_name,
            league=league,
            season=season
        )
        
        # Aggregate by player
        players: Dict[int, Dict] = {}
        
        for pa in plate_apps:
            if pa.player_id not in players:
                player = self.player_repo.get(pa.player_id)
                if not player:
                    continue
                players[pa.player_id] = {
                    'player_id': pa.player_id,
                    'player_name': player.name,
                    'team': team_name,
                    'games': set(),
                    'ab': 0,
                    'h': 0,
                    'doubles': 0,
                    'triples': 0,
                    'hr': 0,
                    'rbi': 0,
                    'bb': 0,
                    'so': 0,
                    'r': 0,
                    'hbp': 0,
                    'sf': 0,
                    'sh': 0,
                    'sb': 0,
                    'cs': 0
                }
            
            player = players[pa.player_id]
            player['games'].add(pa.game_id)
            player['ab'] += pa.AB
            player['h'] += pa.H
            player['doubles'] += pa.double
            player['triples'] += pa.triple
            player['hr'] += pa.HR
            player['rbi'] += pa.RBI
            player['bb'] += pa.BB
            player['so'] += pa.K
            player['r'] += pa.R
            player['hbp'] += pa.HBP
            player['sf'] += pa.SF
            player['sh'] += pa.SH
            player['sb'] += pa.SB
            player['cs'] += pa.CS
        
        # Convert games set to count and calculate batting stats
        result = []
        for player in players.values():
            player['games'] = len(player['games'])
            
            if player['ab'] > 0:
                player['avg'] = player['h'] / player['ab']
                
                singles = player['h'] - player['doubles'] - player['triples'] - player['hr']
                tb = singles + (2 * player['doubles']) + (3 * player['triples']) + (4 * player['hr'])
                player['slg'] = tb / player['ab']
                
                pa_count = player['ab'] + player['bb'] + player['hbp'] + player['sf']
                if pa_count > 0:
                    player['obp'] = (player['h'] + player['bb'] + player['hbp']) / pa_count
                    player['ops'] = player['obp'] + player['slg']
                else:
                    player['obp'] = 0.0
                    player['ops'] = 0.0
            else:
                player['avg'] = 0.0
                player['obp'] = 0.0
                player['slg'] = 0.0
                player['ops'] = 0.0
            
            result.append(player)
        
        # Sort by OPS descending
        result.sort(key=lambda x: x['ops'], reverse=True)
        
        return result
    
    def get_team_games(
        self,
        team_name: str,
        league: Optional[str] = None,
        season: Optional[str] = None
    ) -> List:
        """Get all games for a specific team."""
        all_games = self.game_repo.get_all(limit=10000, league=league, season=season)
        return [
            game for game in all_games 
            if game.home_team == team_name or game.away_team == team_name
        ]

