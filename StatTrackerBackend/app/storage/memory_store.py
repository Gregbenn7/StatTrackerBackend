"""
In-memory data storage for the application.

This module provides a thread-safe in-memory storage system that persists
data only during runtime. Data resets on server restart.
"""

import logging
from typing import Dict, List, Optional, Set
from datetime import datetime, date
import threading
from app.models.player import Player
from app.models.game import Game
from app.models.plate_appearance import PlateAppearance
from app.models.stats import HitterTotal
from app.models.storyline import GameStorylines

logger = logging.getLogger(__name__)


class MemoryStore:
    """
    Thread-safe in-memory storage for all application data.
    
    Uses dictionaries and lists to store entities. Each entity type
    has its own collection, and relationships are maintained through IDs.
    """
    
    _instance: Optional['MemoryStore'] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern to ensure one instance across the application."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the memory store with empty collections."""
        if self._initialized:
            return
        
        self._lock = threading.Lock()
        
        # Entity storage: {id: entity}
        self._players: Dict[int, Player] = {}
        self._games: Dict[int, Game] = {}
        self._plate_appearances: Dict[int, PlateAppearance] = {}
        self._hitter_totals: Dict[int, HitterTotal] = {}
        self._storylines: Dict[int, GameStorylines] = {}  # keyed by game_id
        
        # Indexes for faster lookups
        self._player_id_counter = 0
        self._game_id_counter = 0
        self._plate_appearance_id_counter = 0
        self._hitter_total_id_counter = 0
        self._storyline_id_counter = 0
        
        # Indexes: (name, team) -> player_id
        self._player_index: Dict[tuple, int] = {}
        
        # Indexes: (player_id, league, season) -> hitter_total_id
        self._hitter_total_index: Dict[tuple, int] = {}
        
        self._initialized = True
    
    # Player operations
    def create_player(self, player: Player) -> Player:
        """Create a new player and return with assigned ID."""
        with self._lock:
            self._player_id_counter += 1
            player.id = self._player_id_counter
            player.created_at = datetime.utcnow()
            self._players[player.id] = player
            # Update index
            key = (player.name.lower().strip(), player.team.lower().strip())
            self._player_index[key] = player.id
            return player
    
    def get_player(self, player_id: int) -> Optional[Player]:
        """Get a player by ID."""
        return self._players.get(player_id)
    
    def get_player_by_name_team(self, name: str, team: str) -> Optional[Player]:
        """Find a player by name and team."""
        key = (name.lower().strip(), team.lower().strip())
        player_id = self._player_index.get(key)
        if player_id:
            return self._players.get(player_id)
        return None
    
    def get_all_players(self) -> List[Player]:
        """Get all players."""
        return list(self._players.values())
    
    # Game operations
    def create_game(self, game: Game) -> Game:
        """Create a new game and return with assigned ID."""
        with self._lock:
            self._game_id_counter += 1
            game.id = self._game_id_counter
            game.created_at = datetime.utcnow()
            self._games[game.id] = game
            logger.info(f"✓ Added game #{game.id}: {game.home_team} vs {game.away_team} | Total games in memory: {len(self._games)}")
            return game
    
    def get_game(self, game_id: int) -> Optional[Game]:
        """Get a game by ID."""
        return self._games.get(game_id)
    
    def check_duplicate_game(
        self,
        date: date,
        league: str,
        season: str,
        home_team: str,
        away_team: str
    ) -> Optional[Game]:
        """
        Check if a game with the same date, league, season, and teams already exists.
        
        Args:
            date: Game date
            league: League name
            season: Season identifier
            home_team: Home team name
            away_team: Away team name
        
        Returns:
            Existing Game if duplicate found, None otherwise
        """
        # Normalize team names for comparison (case-insensitive, strip whitespace)
        home_normalized = home_team.strip().lower() if home_team else ""
        away_normalized = away_team.strip().lower() if away_team else ""
        
        for game in self._games.values():
            # Check if date, league, season match
            if (game.date == date and 
                game.league == league and 
                game.season == season):
                
                # Check if teams match (case-insensitive)
                game_home = game.home_team.strip().lower() if game.home_team else ""
                game_away = game.away_team.strip().lower() if game.away_team else ""
                
                # Check both team order combinations (home/away could be swapped)
                if ((game_home == home_normalized and game_away == away_normalized) or
                    (game_home == away_normalized and game_away == home_normalized)):
                    logger.info(f"Duplicate game found: {game.home_team} vs {game.away_team} on {date} ({league}/{season})")
                    return game
        
        return None
    
    def get_games(
        self, 
        limit: int = 50, 
        offset: int = 0,
        league: Optional[str] = None,
        season: Optional[str] = None
    ) -> List[Game]:
        """Get games with optional filtering and pagination."""
        games = list(self._games.values())  # Get ALL games
        
        logger.debug(f"get_games: Found {len(games)} total games in memory")
        
        # Apply filters
        if league:
            games = [g for g in games if g.league == league]
            logger.debug(f"get_games: After league filter '{league}': {len(games)} games")
        if season:
            games = [g for g in games if g.season == season]
            logger.debug(f"get_games: After season filter '{season}': {len(games)} games")
        
        # Sort by date descending, then created_at descending
        games.sort(key=lambda g: (g.date, g.created_at if g.created_at else datetime.min), reverse=True)
        
        # Apply pagination (skip if limit is very large)
        if limit >= 10000:
            logger.debug(f"get_games: Returning all {len(games)} games (limit >= 10000)")
            return games
        result = games[offset:offset + limit]
        logger.debug(f"get_games: Returning {len(result)} games (offset={offset}, limit={limit})")
        return result
    
    # PlateAppearance operations
    def create_plate_appearance(self, plate_app: PlateAppearance) -> PlateAppearance:
        """Create a new plate appearance and return with assigned ID."""
        with self._lock:
            self._plate_appearance_id_counter += 1
            plate_app.id = self._plate_appearance_id_counter
            self._plate_appearances[plate_app.id] = plate_app
            if self._plate_appearance_id_counter % 10 == 0:  # Log every 10th PA to avoid spam
                logger.debug(f"✓ Added plate appearance #{plate_app.id} | Total PAs in memory: {len(self._plate_appearances)}")
            return plate_app
    
    def get_plate_appearances_by_game(self, game_id: int) -> List[PlateAppearance]:
        """Get all plate appearances for a game. Pass -1 to get all."""
        if game_id == -1:
            return list(self._plate_appearances.values())
        return [
            pa for pa in self._plate_appearances.values()
            if pa.game_id == game_id
        ]
    
    def get_all_plate_appearances(self) -> List[PlateAppearance]:
        """Get all plate appearances."""
        return list(self._plate_appearances.values())
    
    def get_plate_appearances_by_player(self, player_id: int) -> List[PlateAppearance]:
        """Get all plate appearances for a player."""
        return [
            pa for pa in self._plate_appearances.values()
            if pa.player_id == player_id
        ]
    
    def get_plate_appearances_by_team(
        self,
        team_name: str,
        league: Optional[str] = None,
        season: Optional[str] = None
    ) -> List[PlateAppearance]:
        """
        Get all plate appearances for a team with optional filters.
        
        Args:
            team_name: Name of the team (case-insensitive comparison)
            league: Filter by league (optional)
            season: Filter by season (optional)
        
        Returns:
            List of PlateAppearance objects
        """
        # Normalize team name for case-insensitive matching
        team_name_normalized = team_name.strip().lower() if team_name else ""
        
        logger.debug(f"get_plate_appearances_by_team: Searching for team '{team_name}' (normalized: '{team_name_normalized}')")
        logger.debug(f"Filters: league={league}, season={season}")
        
        # Get all games first to filter by league/season if needed
        if league or season:
            games = self.get_games(limit=10000, league=league, season=season)
            game_ids = {game.id for game in games}
            plate_apps = [
                pa for pa in self._plate_appearances.values()
                if pa.team and pa.team.strip().lower() == team_name_normalized and pa.game_id in game_ids
            ]
        else:
            plate_apps = [
                pa for pa in self._plate_appearances.values()
                if pa.team and pa.team.strip().lower() == team_name_normalized
            ]
        
        # Log unique team names found in plate appearances for debugging
        if plate_apps:
            unique_teams = {pa.team for pa in plate_apps}
            logger.debug(f"Found {len(plate_apps)} plate appearances for team '{team_name}' (matched teams: {unique_teams})")
        else:
            # Debug: show what team names are actually in the data
            all_teams_in_data = {pa.team.strip() for pa in self._plate_appearances.values() if pa.team}
            logger.warning(f"No plate appearances found for team '{team_name}'. Available teams in data: {sorted(all_teams_in_data)}")
        
        return plate_apps
    
    def get_plate_appearances_by_game_and_player(
        self, game_id: int, player_id: int
    ) -> Optional[PlateAppearance]:
        """Get a specific plate appearance by game and player."""
        for pa in self._plate_appearances.values():
            if pa.game_id == game_id and pa.player_id == player_id:
                return pa
        return None
    
    # HitterTotal operations
    def create_or_update_hitter_total(self, hitter_total: HitterTotal) -> HitterTotal:
        """Create or update a hitter total."""
        with self._lock:
            key = (hitter_total.player_id, hitter_total.league, hitter_total.season)
            existing_id = self._hitter_total_index.get(key)
            
            if existing_id and existing_id in self._hitter_totals:
                # Update existing
                existing = self._hitter_totals[existing_id]
                # Update all fields
                for field, value in hitter_total.model_dump(exclude={'id'}).items():
                    setattr(existing, field, value)
                return existing
            else:
                # Create new
                self._hitter_total_id_counter += 1
                hitter_total.id = self._hitter_total_id_counter
                self._hitter_totals[hitter_total.id] = hitter_total
                self._hitter_total_index[key] = hitter_total.id
                return hitter_total
    
    def get_hitter_total(
        self, player_id: int, league: str, season: str
    ) -> Optional[HitterTotal]:
        """Get a hitter total by player, league, and season."""
        key = (player_id, league, season)
        hitter_total_id = self._hitter_total_index.get(key)
        if hitter_total_id:
            return self._hitter_totals.get(hitter_total_id)
        return None
    
    def get_hitter_totals(
        self, league: Optional[str] = None, season: Optional[str] = None
    ) -> List[HitterTotal]:
        """Get hitter totals with optional filtering."""
        totals = list(self._hitter_totals.values())
        
        if league:
            totals = [ht for ht in totals if ht.league == league]
        if season:
            totals = [ht for ht in totals if ht.season == season]
        
        return totals
    
    def get_hitter_totals_by_player(self, player_id: int) -> List[HitterTotal]:
        """Get all hitter totals for a player."""
        return [
            ht for ht in self._hitter_totals.values()
            if ht.player_id == player_id
        ]
    
    # Storyline operations
    def create_or_update_storyline(self, storyline: GameStorylines) -> GameStorylines:
        """Create or update game storylines."""
        with self._lock:
            existing = self._storylines.get(storyline.game_id)
            if existing:
                # Update existing
                existing.storylines_text = storyline.storylines_text
                existing.json_summary = storyline.json_summary
                existing.created_at = datetime.utcnow()
                return existing
            else:
                # Create new
                self._storyline_id_counter += 1
                storyline.id = self._storyline_id_counter
                storyline.created_at = datetime.utcnow()
                self._storylines[storyline.game_id] = storyline
                return storyline
    
    def get_storyline(self, game_id: int) -> Optional[GameStorylines]:
        """Get storylines for a game."""
        return self._storylines.get(game_id)
    
    # Utility methods
    def get_unique_teams(self, league: Optional[str] = None) -> List[str]:
        """Get unique team names, optionally filtered by league."""
        teams: Set[str] = set()
        
        for pa in self._plate_appearances.values():
            # Get the game to check league
            game = self._games.get(pa.game_id)
            if game:
                if league and game.league != league:
                    continue
                if pa.team:
                    # Normalize team name (strip whitespace) for consistency
                    teams.add(pa.team.strip())
        
        sorted_teams = sorted(list(teams))
        logger.debug(f"get_unique_teams: Found {len(sorted_teams)} unique teams: {sorted_teams}")
        return sorted_teams
    
    def clear_all(self):
        """Clear all data (useful for testing)."""
        with self._lock:
            self._players.clear()
            self._games.clear()
            self._plate_appearances.clear()
            self._hitter_totals.clear()
            self._storylines.clear()
            self._player_index.clear()
            self._hitter_total_index.clear()
            self._player_id_counter = 0
            self._game_id_counter = 0
            self._plate_appearance_id_counter = 0
            self._hitter_total_id_counter = 0
            self._storyline_id_counter = 0


# Global singleton instance
store = MemoryStore()

