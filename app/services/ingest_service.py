"""CSV ingestion service with automatic team detection."""

import io
import json
import logging
import re
import pandas as pd
from datetime import date, datetime
from fastapi import UploadFile
from typing import Tuple, Dict, List, Any, Optional, Union
from app.models.player import Player
from app.models.game import Game
from app.models.plate_appearance import PlateAppearance
from app.repositories.game_repository import GameRepository
from app.repositories.player_repository import PlayerRepository
from app.repositories.stats_repository import StatsRepository
from app.utils.csv_helpers import parse_decimal

logger = logging.getLogger(__name__)


class IngestService:
    """Service for ingesting CSV game data with automatic team detection."""
    
    def __init__(
        self,
        game_repo: GameRepository,
        player_repo: PlayerRepository,
        stats_repo: StatsRepository
    ):
        """Initialize the ingest service with repositories."""
        self.game_repo = game_repo
        self.player_repo = player_repo
        self.stats_repo = stats_repo
    
    def _normalize_column_name(self, col: str) -> str:
        """Normalize column names to handle variations."""
        col_lower = str(col).lower().strip()
        
        # Player name variations
        if col_lower in ['player', 'name', 'player name', 'player_name', 'batter', 'hitter']:
            return 'player'
        # Team variations
        elif col_lower in ['team', 'team name', 'team_name']:
            return 'team'
        # Stats variations
        elif col_lower in ['ab', 'at bats', 'at-bats', 'at_bats']:
            return 'ab'
        elif col_lower in ['h', 'hits', 'hit']:
            return 'h'
        elif col_lower in ['2b', 'double', 'doubles', '2 b']:
            return 'doubles'
        elif col_lower in ['3b', 'triple', 'triples', '3 b']:
            return 'triples'
        elif col_lower in ['hr', 'home runs', 'homeruns', 'home_run', 'homer']:
            return 'hr'
        elif col_lower in ['rbi', 'runs batted in', 'runs_batted_in']:
            return 'rbi'
        elif col_lower in ['bb', 'walks', 'walk', 'base on balls']:
            return 'bb'
        elif col_lower in ['so', 'k', 'strikeouts', 'strikeout', 'strike outs']:
            return 'so'
        elif col_lower in ['r', 'runs', 'run']:
            return 'r'
        elif col_lower in ['hbp', 'hit by pitch', 'hit_by_pitch']:
            return 'hbp'
        elif col_lower in ['sf', 'sacrifice fly', 'sac_fly']:
            return 'sf'
        elif col_lower in ['sh', 'sacrifice hit', 'sacrifice bunt', 'sac_bunt']:
            return 'sh'
        elif col_lower in ['sb', 'stolen bases', 'stolen_base']:
            return 'sb'
        elif col_lower in ['cs', 'caught stealing', 'caught_stealing']:
            return 'cs'
        else:
            return col_lower
    
    def _detect_teams_from_hittrax_format(self, csv_content: Union[str, bytes]) -> Dict[str, Any]:
        """
        Detect teams from HitTrax CSV format with multi-header rows.
        
        Handles multiple HitTrax format variations:
        - Format 1: Team name in first column, followed by "Batting Order"
        - Format 2: Team name as standalone row
        - Format 3: Team sections separated by empty lines
        
        Args:
            csv_content: Either text string or bytes content of CSV file
            
        Returns:
            Dict with team detection results
            
        Raises:
            ValueError: If CSV doesn't contain exactly 2 teams
        """
        # Decode bytes → text if needed
        if isinstance(csv_content, bytes):
            try:
                text = csv_content.decode("utf-8")
            except UnicodeDecodeError:
                try:
                    text = csv_content.decode("latin-1")
                except UnicodeDecodeError:
                    text = csv_content.decode("utf-8", errors="ignore")
        else:
            text = csv_content
        
        lines = text.splitlines()
        
        logger.info(f"=== Parsing HitTrax CSV - Total lines: {len(lines)} ===")
        
        # Find team header rows (they contain "Batting Order")
        teams = []
        team_sections = []
        
        for i, line in enumerate(lines):
            # Check if line contains team header indicators (case-insensitive)
            if 'Batting Order' in line or 'batting order' in line.lower():
                # Extract team name from first column
                parts = line.split(',')
                if parts:
                    team_name = parts[0].strip()
                    # Clean up team name - remove quotes, extra spaces
                    team_name = team_name.strip('"').strip("'").strip()
                    
                    # Skip if empty or if it's just "Batting Order"
                    if team_name and team_name.lower() != 'batting order':
                        teams.append(team_name)
                        team_sections.append(i)
                        logger.info(f"Found team: '{team_name}' at line {i}")
        
        # Validate we found exactly 2 teams
        if len(teams) < 2:
            logger.warning(f"Found {len(teams)} teams using 'Batting Order' method: {teams}")
            logger.info("Trying alternative parsing methods...")
            
            # Alternative method: Look for lines that are mostly non-numeric
            potential_teams = []
            for i, line in enumerate(lines[:50]):  # Check first 50 lines
                if line.strip() and ',' in line:
                    first_col = line.split(',')[0].strip().strip('"').strip("'")
                    
                    # Check if it looks like a team name
                    if (first_col and 
                        len(first_col) > 2 and 
                        len(first_col) < 50 and
                        not first_col.replace(' ', '').isdigit() and
                        first_col.lower() not in ['player', 'name', 'batting order', 'team']):
                        
                        # Check if next few lines have player-like data (contain numbers)
                        if i + 1 < len(lines):
                            next_line = lines[i + 1]
                            if ',' in next_line and any(c.isdigit() for c in next_line):
                                # Make sure we don't already have this team
                                if first_col not in [t for t in teams]:
                                    potential_teams.append((i, first_col))
                                    logger.info(f"Potential team found: '{first_col}' at line {i}")
            
            # If we found potential teams, use them
            if len(potential_teams) >= 2:
                teams = [t[1] for t in potential_teams[:2]]
                team_sections = [t[0] for t in potential_teams[:2]]
                logger.info(f"Using alternative method - found teams: {teams}")
            elif len(potential_teams) == 1 and len(teams) == 1:
                # One team from each method - combine them
                teams = teams + [potential_teams[0][1]]
                team_sections = team_sections + [potential_teams[0][0]]
                logger.info(f"Combined methods - found teams: {teams}")
        
        if len(teams) < 2:
            # Show first few lines for debugging
            sample_lines = '\n'.join(lines[:10])
            raise ValueError(
                f"CSV must contain exactly 2 teams in HitTrax format. "
                f"Found {len(teams)} team(s): {teams}\n"
                f"Please ensure your CSV has two team header rows containing 'Batting Order'.\n"
                f"First 10 lines of CSV:\n{sample_lines}"
            )
        
        if len(teams) > 2:
            logger.warning(f"Found {len(teams)} teams, using first 2: {teams[:2]}")
            teams = teams[:2]
            team_sections = team_sections[:2]
        
        team1_name = teams[0]
        team2_name = teams[1]
        
        logger.info(f"Final teams: '{team1_name}' vs '{team2_name}'")
        
        # Parse team 1 players (between first and second team header)
        team1_start = team_sections[0] + 1
        team1_end = team_sections[1] if len(team_sections) > 1 else len(lines)
        team1_lines = lines[team1_start:team1_end]
        
        logger.info(f"Team 1 section: lines {team1_start} to {team1_end} ({len(team1_lines)} lines)")
        
        team1_players = self._parse_hittrax_team_section(team1_lines, team1_name)
        
        # Parse team 2 players (from second team header to end)
        team2_start = team_sections[1] + 1 if len(team_sections) > 1 else 0
        team2_lines = lines[team2_start:]
        
        logger.info(f"Team 2 section: lines {team2_start} to end ({len(team2_lines)} lines)")
        
        team2_players = self._parse_hittrax_team_section(team2_lines, team2_name)
        
        logger.info(f"Parsed {len(team1_players)} players for {team1_name}")
        logger.info(f"Parsed {len(team2_players)} players for {team2_name}")
        
        # Validate we got players
        if len(team1_players) == 0 or len(team2_players) == 0:
            raise ValueError(
                f"Failed to parse player data. "
                f"Team 1 ({team1_name}): {len(team1_players)} players, "
                f"Team 2 ({team2_name}): {len(team2_players)} players. "
                f"Make sure your CSV has player rows with stats after each team header."
            )
        
        # Calculate team totals (runs scored)
        team1_runs = sum(player['r'] for player in team1_players)
        team2_runs = sum(player['r'] for player in team2_players)
        
        # Determine winner
        if team1_runs > team2_runs:
            winner = team1_name
        elif team2_runs > team1_runs:
            winner = team2_name
        else:
            winner = None  # Tie
        
        logger.info(f"Score: {team1_name} {team1_runs} - {team2_runs} {team2_name}, Winner: {winner or 'Tie'}")
        
        # Create DataFrames from parsed players for compatibility
        if team1_players:
            team1_df = pd.DataFrame(team1_players)
        else:
            team1_df = pd.DataFrame()
        
        if team2_players:
            team2_df = pd.DataFrame(team2_players)
        else:
            team2_df = pd.DataFrame()
        
        return {
            'teams': [team1_name, team2_name],
            'team1_name': team1_name,
            'team2_name': team2_name,
            'team1_df': team1_df,
            'team2_df': team2_df,
            'team1_runs': team1_runs,
            'team2_runs': team2_runs,
            'winner': winner,
            'team1_players': team1_players,
            'team2_players': team2_players
        }
    
    def _parse_hittrax_team_section(self, lines: List[str], team_name: str) -> List[Dict[str, Any]]:
        """
        Parse a section of CSV lines for one team in HitTrax format.
        
        HitTrax format columns:
        0: Player Name
        1: Batting Order
        2: AB
        3: R (Runs)
        4: H (Hits)
        5: EBH (Extra Base Hits)
        6: 2B (Doubles)
        7: 3B (Triples)
        8: HR (Home Runs)
        9: RBI
        10: #P (Pitches)
        11: SO (Strikeouts)
        12: DP (Double Plays)
        13: BB (Walks)
        
        Args:
            lines: List of CSV lines for this team
            team_name: Name of the team
            
        Returns:
            List of player stat dictionaries
        """
        players = []
        
        logger.debug(f"  Parsing section for {team_name} ({len(lines)} lines)")
        
        for line_num, line in enumerate(lines):
            # Skip empty lines
            if not line.strip():
                continue
            
            # Skip header lines
            if 'Batting Order' in line or 'batting order' in line.lower():
                continue
            
            # Skip lines that look like headers
            lower_line = line.lower()
            if any(header in lower_line for header in ['player', 'name', 'ab', 'avg', 'slg']):
                if not any(c.isdigit() for c in line):  # No numbers = probably header
                    continue
            
            # Parse player row
            values = [v.strip().strip('"').strip("'") for v in line.split(',')]
            
            # Need at least 10 columns for basic HitTrax format
            if len(values) < 10:
                continue
            
            # Skip if first column is empty or looks like header
            if not values[0] or values[0].lower() in ['player', 'name', 'team', 'batting order']:
                continue
            
            try:
                # HitTrax format columns:
                # 0: Player Name
                # 1: Batting Order
                # 2: AB
                # 3: R (Runs)
                # 4: H (Hits)
                # 5: EBH (Extra Base Hits)
                # 6: 2B (Doubles)
                # 7: 3B (Triples)
                # 8: HR (Home Runs)
                # 9: RBI
                # 10: #P (Pitches)
                # 11: SO (Strikeouts)
                # 12: DP (Double Plays)
                # 13: BB (Walks)
                
                player_stats = {
                    'player_name': values[0].strip(),
                    'team': team_name,
                    'ab': self._safe_int(values[2] if len(values) > 2 else 0),
                    'r': self._safe_int(values[3] if len(values) > 3 else 0),
                    'h': self._safe_int(values[4] if len(values) > 4 else 0),
                    'doubles': self._safe_int(values[6] if len(values) > 6 else 0),
                    'triples': self._safe_int(values[7] if len(values) > 7 else 0),
                    'hr': self._safe_int(values[8] if len(values) > 8 else 0),
                    'rbi': self._safe_int(values[9] if len(values) > 9 else 0),
                    'so': self._safe_int(values[11] if len(values) > 11 else 0),
                    'bb': self._safe_int(values[13] if len(values) > 13 else 0),
                    'hbp': 0,  # Not in HitTrax export
                    'sf': 0,   # Not in HitTrax export
                    'sh': 0,   # Not in HitTrax export
                    'sb': 0,   # Not in HitTrax export
                    'cs': 0    # Not in HitTrax export
                }
                
                # Only add if player name is valid and has at least some stats
                if (player_stats['player_name'] and 
                    player_stats['player_name'] != 'Unknown' and
                    (player_stats['ab'] > 0 or player_stats['h'] > 0 or player_stats['r'] > 0)):
                    players.append(player_stats)
                    logger.debug(f"    ✓ Parsed: {player_stats['player_name']} - {player_stats['ab']} AB, {player_stats['h']} H, {player_stats['r']} R")
                    
            except (ValueError, IndexError) as e:
                # Skip rows that can't be parsed
                logger.warning(f"    ✗ Could not parse line {line_num}: {line[:60]}... Error: {e}")
                continue
        
        return players
    
    def _detect_teams_from_csv(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Detect teams from CSV by analyzing the Team column (fallback method).
        
        This method is used when CSV has a 'Team' column. For HitTrax format
        with multi-header rows, use _detect_teams_from_hittrax_format instead.
        
        Args:
            df: DataFrame with normalized columns
            
        Returns:
            Dict with team detection results
            
        Raises:
            ValueError: If CSV doesn't contain exactly 2 teams
        """
        # Check if 'team' column exists
        if 'team' not in df.columns:
            raise ValueError(
                "CSV must contain a 'Team' column for automatic team detection, "
                "or be in HitTrax format with team names as header rows containing 'Batting Order'."
            )
        
        # Extract unique teams (normalize and filter out NaN)
        unique_teams = df['team'].dropna().astype(str).str.strip().unique().tolist()
        unique_teams = [t for t in unique_teams if t and t.lower() != 'nan']
        
        if len(unique_teams) < 2:
            raise ValueError(
                f"CSV must contain exactly 2 teams. Found {len(unique_teams)} team(s): {unique_teams}. "
                "Please ensure the CSV has a 'Team' column with exactly 2 different team names."
            )
        
        if len(unique_teams) > 2:
            raise ValueError(
                f"CSV must contain exactly 2 teams. Found {len(unique_teams)} teams: {unique_teams}. "
                "Please split the CSV or ensure only 2 teams are present."
            )
        
        team1_name = unique_teams[0].strip()
        team2_name = unique_teams[1].strip()
        
        # Separate data by team
        team1_df = df[df['team'].astype(str).str.strip() == team1_name].copy()
        team2_df = df[df['team'].astype(str).str.strip() == team2_name].copy()
        
        # Calculate team totals (runs scored)
        team1_runs = 0
        team2_runs = 0
        
        if 'r' in team1_df.columns:
            team1_runs = int(team1_df['r'].fillna(0).astype(float).sum())
        if 'r' in team2_df.columns:
            team2_runs = int(team2_df['r'].fillna(0).astype(float).sum())
        
        # Determine winner
        if team1_runs > team2_runs:
            winner = team1_name
        elif team2_runs > team1_runs:
            winner = team2_name
        else:
            winner = None  # Tie
        
        logger.info(f"Detected teams: {team1_name} ({team1_runs} runs) vs {team2_name} ({team2_runs} runs), Winner: {winner or 'Tie'}")
        
        return {
            'teams': [team1_name, team2_name],
            'team1_name': team1_name,
            'team2_name': team2_name,
            'team1_df': team1_df,
            'team2_df': team2_df,
            'team1_runs': team1_runs,
            'team2_runs': team2_runs,
            'winner': winner
        }
    
    def _safe_int(self, value, default: int = 0) -> int:
        """
        Safely convert value to int, returning 0 if conversion fails.
        
        Handles various input formats:
        - Strings with numbers
        - Strings with numbers and text (extracts first number)
        - NaN/None values
        - Empty strings
        """
        if pd.isna(value) or value is None:
            return default
        
        if isinstance(value, (int, float)):
            try:
                return int(value)
            except (ValueError, OverflowError):
                return default
        
        # Convert to string and clean
        str_value = str(value).strip().strip('"').strip("'")
        if not str_value or str_value.lower() == 'nan':
            return default
        
        try:
            # Try direct conversion
            return int(float(str_value))
        except (ValueError, TypeError):
            # Try extracting first number from string
            try:
                numbers = re.findall(r'-?\d+\.?\d*', str_value)
                if numbers:
                    return int(float(numbers[0]))
            except (ValueError, IndexError):
                pass
            return default
    
    def _parse_player_row(self, row: pd.Series, team: str) -> Dict[str, Any]:
        """Parse a single player's stats from a CSV row."""
        return {
            'player_name': str(row.get('player', 'Unknown')).strip(),
            'team': team,
            'ab': self._safe_int(row.get('ab', 0)),
            'h': self._safe_int(row.get('h', 0)),
            'doubles': self._safe_int(row.get('doubles', 0)),
            'triples': self._safe_int(row.get('triples', 0)),
            'hr': self._safe_int(row.get('hr', 0)),
            'rbi': self._safe_int(row.get('rbi', 0)),
            'bb': self._safe_int(row.get('bb', 0)),
            'so': self._safe_int(row.get('so', 0)),
            'r': self._safe_int(row.get('r', 0)),
            'hbp': self._safe_int(row.get('hbp', 0)),
            'sf': self._safe_int(row.get('sf', 0)),
            'sh': self._safe_int(row.get('sh', 0)),
            'sb': self._safe_int(row.get('sb', 0)),
            'cs': self._safe_int(row.get('cs', 0))
        }
    
    async def ingest_game_csv(
        self,
        file: UploadFile,
        league: str,
        season: str,
        game_date: date,
        home_team: Optional[str] = None,
        away_team: Optional[str] = None,
    ) -> Tuple[int, int, Dict[str, Any]]:
        """
        Parse a HitTrax game CSV and insert rows into storage.
        Automatically detects teams from CSV if home_team and away_team are not provided.
        
        Args:
            file: Uploaded CSV file
            league: League name
            season: Season identifier
            game_date: Game date
            home_team: Home team name (optional - will be auto-detected if not provided)
            away_team: Away team name (optional - will be auto-detected if not provided)
            
        Returns:
            Tuple of (rows_ingested, game_id, game_info_dict)
            
        Raises:
            ValueError: If required data is missing or invalid
        """
        # Read file content first to check format
        await file.seek(0)
        content = await file.read()
        
        # Decode bytes → text
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            text = content.decode("latin-1")
        
        # Check if this is HitTrax format (has "Batting Order" in header rows)
        is_hittrax_format = 'Batting Order' in text
        
        # Auto-detect teams if not provided
        if not home_team or not away_team:
            if is_hittrax_format:
                # Use HitTrax format parser - pass the text content we already have
                team_data = self._detect_teams_from_hittrax_format(text)
                home_team = team_data['team1_name']
                away_team = team_data['team2_name']
                team1_players = team_data['team1_players']
                team2_players = team_data['team2_players']
                home_score = team_data['team1_runs']
                away_score = team_data['team2_runs']
                winner = team_data['winner']
                
                # Create DataFrames from parsed players for processing
                if team1_players:
                    team1_df = pd.DataFrame(team1_players)
                else:
                    team1_df = pd.DataFrame()
                
                if team2_players:
                    team2_df = pd.DataFrame(team2_players)
                else:
                    team2_df = pd.DataFrame()
            else:
                # Use standard CSV format with Team column
                df = pd.read_csv(io.StringIO(text))
                
                # Strip whitespace from column names
                df.columns = [col.strip() for col in df.columns]
                
                # Normalize column names
                normalized_columns = {col: self._normalize_column_name(col) for col in df.columns}
                df = df.rename(columns=normalized_columns)
                
                team_data = self._detect_teams_from_csv(df)
                home_team = team_data['team1_name']
                away_team = team_data['team2_name']
                team1_df = team_data['team1_df']
                team2_df = team_data['team2_df']
                home_score = team_data['team1_runs']
                away_score = team_data['team2_runs']
                winner = team_data['winner']
                team1_players = None  # Will be parsed from DataFrame
                team2_players = None
        else:
            # Manual team assignment - need to load DataFrame first
            df = pd.read_csv(io.StringIO(text))
            
            # Strip whitespace from column names
            df.columns = [col.strip() for col in df.columns]
            
            # Normalize column names
            normalized_columns = {col: self._normalize_column_name(col) for col in df.columns}
            df = df.rename(columns=normalized_columns)
            
            # Filter by team column if it exists
            if 'team' in df.columns:
                unique_teams = df['team'].dropna().astype(str).str.strip().unique().tolist()
                team1_df = df[df['team'].astype(str).str.strip() == home_team].copy() if home_team in unique_teams else df
                team2_df = df[df['team'].astype(str).str.strip() == away_team].copy() if away_team in unique_teams else pd.DataFrame()
            else:
                # If no team column, assign all players to home team (legacy behavior)
                team1_df = df
                team2_df = pd.DataFrame()
            
            # Calculate scores
            home_score = int(team1_df['r'].fillna(0).astype(float).sum()) if 'r' in team1_df.columns else 0
            away_score = int(team2_df['r'].fillna(0).astype(float).sum()) if 'r' in team2_df.columns else 0
            
            # Determine winner
            if home_score > away_score:
                winner = home_team
            elif away_score > home_score:
                winner = away_team
            else:
                winner = None
            
            # Set players to None (will be parsed from DataFrame)
            team1_players = None
            team2_players = None
        
        # Create game with scores
        game = Game(
            league=league,
            season=season,
            date=game_date,
            home_team=home_team,
            away_team=away_team,
            home_score=home_score,
            away_score=away_score,
            winner=winner,
            created_at=datetime.utcnow()
        )
        game = self.game_repo.create(game)
        
        rows_ingested = 0
        
        # Process team 1 players
        if team1_players is not None:
            # Already parsed from HitTrax format
            for player_stats in team1_players:
                if not player_stats['player_name'] or player_stats['player_name'] == 'Unknown':
                    continue
                
                # Find or create player
                player = self.player_repo.get_by_name_team(player_stats['player_name'], home_team)
                if not player:
                    player = Player(name=player_stats['player_name'], team=home_team, league=league)
                    player = self.player_repo.create(player)
                
                # Create PlateAppearance
                plate_app = PlateAppearance(
                    game_id=game.id,
                    player_id=player.id,
                    team=home_team,
                    AB=player_stats['ab'],
                    R=player_stats['r'],
                    H=player_stats['h'],
                    double=player_stats['doubles'],
                    triple=player_stats['triples'],
                    HR=player_stats['hr'],
                    BB=player_stats['bb'],
                    HBP=player_stats['hbp'],
                    K=player_stats['so'],
                    RBI=player_stats['rbi'],
                    SB=player_stats['sb'],
                    CS=player_stats['cs'],
                    SF=player_stats['sf'],
                    SH=player_stats['sh'],
                    raw_json=json.dumps(player_stats, default=str)
                )
                
                self.stats_repo.create_plate_appearance(plate_app)
                rows_ingested += 1
        else:
            # Parse from DataFrame (standard format)
            for _, row in team1_df.iterrows():
                player_stats = self._parse_player_row(row, home_team)
                
                if not player_stats['player_name'] or player_stats['player_name'] == 'Unknown':
                    continue
                
                # Find or create player
                player = self.player_repo.get_by_name_team(player_stats['player_name'], home_team)
                if not player:
                    player = Player(name=player_stats['player_name'], team=home_team, league=league)
                    player = self.player_repo.create(player)
                
                # Store raw row data as JSON
                raw_row_dict = row.to_dict()
                raw_json_str = json.dumps(raw_row_dict, default=str)
                
                # Create PlateAppearance
                plate_app = PlateAppearance(
                    game_id=game.id,
                    player_id=player.id,
                    team=home_team,
                    AB=player_stats['ab'],
                    R=player_stats['r'],
                    H=player_stats['h'],
                    double=player_stats['doubles'],
                    triple=player_stats['triples'],
                    HR=player_stats['hr'],
                    BB=player_stats['bb'],
                    HBP=player_stats['hbp'],
                    K=player_stats['so'],
                    RBI=player_stats['rbi'],
                    SB=player_stats['sb'],
                    CS=player_stats['cs'],
                    SF=player_stats['sf'],
                    SH=player_stats['sh'],
                    raw_json=raw_json_str
                )
                
                self.stats_repo.create_plate_appearance(plate_app)
                rows_ingested += 1
        
        # Process team 2 players
        if team2_players is not None:
            # Already parsed from HitTrax format
            for player_stats in team2_players:
                if not player_stats['player_name'] or player_stats['player_name'] == 'Unknown':
                    continue
                
                # Find or create player
                player = self.player_repo.get_by_name_team(player_stats['player_name'], away_team)
                if not player:
                    player = Player(name=player_stats['player_name'], team=away_team, league=league)
                    player = self.player_repo.create(player)
                
                # Create PlateAppearance
                plate_app = PlateAppearance(
                    game_id=game.id,
                    player_id=player.id,
                    team=away_team,
                    AB=player_stats['ab'],
                    R=player_stats['r'],
                    H=player_stats['h'],
                    double=player_stats['doubles'],
                    triple=player_stats['triples'],
                    HR=player_stats['hr'],
                    BB=player_stats['bb'],
                    HBP=player_stats['hbp'],
                    K=player_stats['so'],
                    RBI=player_stats['rbi'],
                    SB=player_stats['sb'],
                    CS=player_stats['cs'],
                    SF=player_stats['sf'],
                    SH=player_stats['sh'],
                    raw_json=json.dumps(player_stats, default=str)
                )
                
                self.stats_repo.create_plate_appearance(plate_app)
                rows_ingested += 1
        else:
            # Parse from DataFrame (standard format)
            for _, row in team2_df.iterrows():
                player_stats = self._parse_player_row(row, away_team)
                
                if not player_stats['player_name'] or player_stats['player_name'] == 'Unknown':
                    continue
                
                # Find or create player
                player = self.player_repo.get_by_name_team(player_stats['player_name'], away_team)
                if not player:
                    player = Player(name=player_stats['player_name'], team=away_team, league=league)
                    player = self.player_repo.create(player)
                
                # Store raw row data as JSON
                raw_row_dict = row.to_dict()
                raw_json_str = json.dumps(raw_row_dict, default=str)
                
                # Create PlateAppearance
                plate_app = PlateAppearance(
                    game_id=game.id,
                    player_id=player.id,
                    team=away_team,
                    AB=player_stats['ab'],
                    R=player_stats['r'],
                    H=player_stats['h'],
                    double=player_stats['doubles'],
                    triple=player_stats['triples'],
                    HR=player_stats['hr'],
                    BB=player_stats['bb'],
                    HBP=player_stats['hbp'],
                    K=player_stats['so'],
                    RBI=player_stats['rbi'],
                    SB=player_stats['sb'],
                    CS=player_stats['cs'],
                    SF=player_stats['sf'],
                    SH=player_stats['sh'],
                    raw_json=raw_json_str
                )
                
                self.stats_repo.create_plate_appearance(plate_app)
                rows_ingested += 1
        
        game_info = {
            'home_team': home_team,
            'away_team': away_team,
            'home_score': home_score,
            'away_score': away_score,
            'winner': winner,
            'team1_player_count': len(team1_df),
            'team2_player_count': len(team2_df)
        }
        
        return rows_ingested, game.id, game_info
