import csv
import json
import io
import pandas as pd
import logging
from typing import Dict, List, Optional, Tuple
from sqlmodel import Session, select
from datetime import date, datetime
from fastapi import UploadFile

from app.models import Player, PlateAppearance, Game

logger = logging.getLogger(__name__)


def _parse_decimal(value):
    """
    Helper to convert things like '.333' or '1.250' into float or None.
    Handles NaN / missing gracefully.
    """
    if value is None:
        return None
    try:
        s = str(value).strip()
        if s == "" or s.lower() == "nan":
            return None
        # HitTrax sometimes uses '.333' style strings; float() handles that.
        return float(s)
    except Exception:
        return None


def find_or_create_player(session: Session, name: str, team: str, league: Optional[str] = None) -> Player:
    """Find existing player or create a new one."""
    statement = select(Player).where(
        Player.name == name,
        Player.team == team
    )
    player = session.exec(statement).first()
    
    if player is None:
        player = Player(name=name, team=team, league=league)
        session.add(player)
        session.commit()
        session.refresh(player)
    
    return player


async def ingest_game_csv(
    db: Session,
    file: UploadFile,
    league: str,
    season: str,
    game_date: date,
    home_team: str,
    away_team: str,
) -> Tuple[int, int]:
    """
    Parse a HitTrax game CSV and insert rows into the DB.
    Returns (rows_ingested, game_id).
    """
    # Read file content
    await file.seek(0)
    content = await file.read()
    
    # Decode bytes → text and load into pandas
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        text = content.decode("latin-1")
    
    df = pd.read_csv(io.StringIO(text))
    
    # CRITICAL: Strip whitespace from column names FIRST
    # HitTrax CSVs have headers like " AB", " 2B", " 3B", etc.
    df.columns = [col.strip() for col in df.columns]
    
    # The sample HitTrax export has columns like:
    # ['Tetons','Batting Order','AB','R','H','EBH','2B','3B','HR','RBI',
    #  '#P','SO','DP','BB','AVG','SLG','OBP','OPS','BA/RSP',
    #  'AvgVel','MaxVel','AvgDist','MaxDist','UserId','AvgPts','MaxPts']
    #
    # The first column header is typically the team name, and the values are player names
    # We need to detect which team this CSV represents
    
    # Determine the team from the first column header (before we rename it)
    csv_team_name = None
    first_col = df.columns[0]
    
    # If the first column is not a standard stat column, it's likely the team name
    standard_columns = {'Player', 'Batting Order', 'AB', 'R', 'H', 'HR', 'RBI', 'BB', 'AVG', 'OBP', 'SLG', 'OPS'}
    if first_col not in standard_columns and first_col.strip() not in standard_columns:
        # This is likely a team name (e.g., "Tetons")
        csv_team_name = first_col.strip()
        # Check if this matches home_team or away_team
        if csv_team_name == home_team:
            team_name_default = home_team
        elif csv_team_name == away_team:
            team_name_default = away_team
        else:
            # Default to home_team if we can't match
            team_name_default = home_team
            logger.warning(f"CSV team '{csv_team_name}' doesn't match home_team or away_team. Using home_team as default.")
    else:
        team_name_default = home_team  # fallback
    
    # Rename the first column to "player_name" if it's not already "Player"
    if first_col not in ["Player", "player_name"]:
        df = df.rename(columns={first_col: "player_name"})
    elif "Player" in df.columns:
        df = df.rename(columns={"Player": "player_name"})
    
    # Optional additional renames for clarity (only if they exist)
    rename_map = {
        "Batting Order": "batting_order",
        "#P": "pitches",
        "BA/RSP": "ba_rsp",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
    
    # Normalize remaining column names to lowercase for easier lookup
    # But keep the original column names in the dataframe for now
    column_lookup = {col.lower().strip(): col for col in df.columns}
    
    # Create or get a Game record
    game = Game(
        league=league,
        season=season,
        date=game_date,
        home_team=home_team,
        away_team=away_team,
    )
    db.add(game)
    db.flush()  # so game.id is available
    db.refresh(game)
    
    rows_ingested = 0
    
    # Helper function to safely get int values
    def safe_int(row, col_name, default=0):
        """Safely extract integer from row, handling various column name formats."""
        # Try direct lookup first
        if col_name in df.columns:
            val = row.get(col_name)
        else:
            # Try lowercase lookup
            val = row.get(column_lookup.get(col_name.lower(), col_name))
        
        if pd.isna(val) or val is None:
            return default
        try:
            return int(float(str(val)))
        except (ValueError, TypeError):
            return default
    
    # Helper to get player name from row
    def get_player_name(row):
        """Extract player name from row, checking multiple possible columns."""
        if "player_name" in df.columns:
            val = row.get("player_name")
        elif "Player" in df.columns:
            val = row.get("Player")
        elif "Tetons" in df.columns:
            val = row.get("Tetons")
        else:
            # Try case-insensitive search
            for col in df.columns:
                if col.lower() in ["player", "name", "batter", "hitter"]:
                    val = row.get(col)
                    break
            else:
                val = None
        
        if pd.isna(val) or val is None:
            return None
        return str(val).strip()
    
    for _, row in df.iterrows():
        player_name = get_player_name(row)
        
        if not player_name:
            continue
        
        # Determine team for this player
        # Priority: 1) "Team" column in CSV, 2) team detected from CSV header, 3) default to home_team
        team_name = team_name_default  # Use the team we detected from the CSV header
        
        # Check if there's a "Team" column that specifies the team per row
        if "Team" in df.columns:
            team_val = row.get("Team")
            if not pd.isna(team_val) and team_val:
                team_name = str(team_val).strip()
        
        # Query for existing player by name and league/team
        statement = select(Player).where(
            Player.name == player_name,
            Player.team == team_name
        )
        player = db.exec(statement).first()
        
        if not player:
            player = Player(name=player_name, team=team_name, league=league)
            db.add(player)
            db.flush()
            db.refresh(player)
        
        # Extract stats from row
        # Use the normalized column names (stripped) for lookup
        ab = safe_int(row, "AB")
        r = safe_int(row, "R")
        h = safe_int(row, "H")
        hr = safe_int(row, "HR")
        rbi = safe_int(row, "RBI")
        bb = safe_int(row, "BB")
        so = safe_int(row, "SO")
        
        # Get doubles and triples
        double_val = safe_int(row, "2B")
        triple_val = safe_int(row, "3B")
        
        # Get optional stats
        hbp = safe_int(row, "HBP")
        sf = safe_int(row, "SF")
        sh = safe_int(row, "SH")
        sb = safe_int(row, "SB")
        cs = safe_int(row, "CS")
        
        # Parse decimal stats (AVG, OBP, SLG, OPS) for raw_json storage
        avg = _parse_decimal(row.get("AVG") if "AVG" in df.columns else None)
        obp = _parse_decimal(row.get("OBP") if "OBP" in df.columns else None)
        slg = _parse_decimal(row.get("SLG") if "SLG" in df.columns else None)
        ops = _parse_decimal(row.get("OPS") if "OPS" in df.columns else None)
        
        # Store raw row data as JSON for reference
        raw_row_dict = row.to_dict()
        raw_json_str = json.dumps(raw_row_dict, default=str)
        
        # Create PlateAppearance record
        plate_app = PlateAppearance(
            game_id=game.id,
            player_id=player.id,
            team=team_name,
            AB=ab,
            R=r,
            H=h,
            double=double_val,
            triple=triple_val,
            HR=hr,
            BB=bb,
            HBP=hbp,
            K=so,  # SO maps to K
            RBI=rbi,
            SB=sb,
            CS=cs,
            SF=sf,
            SH=sh,
            raw_json=raw_json_str
        )
        
        db.add(plate_app)
        rows_ingested += 1
    
    db.commit()
    return rows_ingested, game.id


# Legacy functions for backward compatibility
def normalize_column_name(col: str) -> str:
    """Normalize column names to lowercase and stripped."""
    if pd.isna(col):
        return ""
    return str(col).strip().lower()


def normalize_row(row: Dict[str, str]) -> Dict[str, any]:
    """Normalize a CSV row to our standard format (legacy function)."""
    normalized = {}
    
    # Normalize column names
    for key, value in row.items():
        normalized_key = normalize_column_name(key)
        normalized[normalized_key] = value
    
    # Ensure we have player name and team (required)
    player_name = (
        normalized.get('player') or 
        normalized.get('name') or 
        normalized.get('player name') or
        row.get('Player') or
        row.get('Name') or
        row.get('PLAYER')
    )
    
    team = (
        normalized.get('team') or
        row.get('Team') or
        row.get('TEAM')
    )
    
    if not player_name:
        raise ValueError("CSV row missing required 'player' or 'name' column")
    if not team:
        raise ValueError("CSV row missing required 'team' column")
    
    # Convert numeric fields, defaulting to 0 if missing or invalid
    numeric_fields = [
        'AB', 'H', 'double', 'triple', 'HR', 'BB', 'HBP', 
        'SF', 'SH', 'K', 'R', 'RBI', 'SB', 'CS'
    ]
    
    result = {
        'player_name': str(player_name).strip(),
        'team': str(team).strip(),
    }
    
    for field in numeric_fields:
        value = normalized.get(field, '0')
        try:
            result[field] = int(float(str(value).strip() or '0'))
        except (ValueError, TypeError):
            result[field] = 0
    
    # Validate required fields
    if result.get('AB') is None:
        raise ValueError(f"Row for {player_name} missing required 'AB' column")
    if result.get('H') is None:
        raise ValueError(f"Row for {player_name} missing required 'H' column")
    if result.get('HR') is None:
        raise ValueError(f"Row for {player_name} missing required 'HR' column")
    
    # Store raw row for reference
    result['raw_json'] = json.dumps(row)
    
    return result


def ingest_csv_rows(
    session: Session,
    csv_content: str,
    game_id: int,
    league: str
) -> int:
    """
    Parse CSV content and create PlateAppearance records (legacy function).
    Returns the number of rows ingested.
    """
    # Parse CSV
    reader = csv.DictReader(csv_content.splitlines())
    rows = list(reader)
    
    ingested = 0
    
    for row in rows:
        # Skip empty rows
        if not any(row.values()):
            continue
        
        try:
            # Normalize row
            normalized = normalize_row(row)
            
            # Find or create player
            player = find_or_create_player(
                session,
                normalized['player_name'],
                normalized['team'],
                league
            )
            
            # Create plate appearance
            plate_app = PlateAppearance(
                game_id=game_id,
                player_id=player.id,
                team=normalized['team'],
                AB=normalized['AB'],
                H=normalized['H'],
                double=normalized.get('double', 0),
                triple=normalized.get('triple', 0),
                HR=normalized['HR'],
                BB=normalized.get('BB', 0),
                HBP=normalized.get('HBP', 0),
                SF=normalized.get('SF', 0),
                SH=normalized.get('SH', 0),
                K=normalized.get('K', 0),
                R=normalized.get('R', 0),
                RBI=normalized.get('RBI', 0),
                SB=normalized.get('SB', 0),
                CS=normalized.get('CS', 0),
                raw_json=normalized.get('raw_json')
            )
            
            session.add(plate_app)
            ingested += 1
            
        except Exception as e:
            # Log error but continue processing other rows
            print(f"Error processing row: {e}")
            continue
    
    session.commit()
    return ingested
