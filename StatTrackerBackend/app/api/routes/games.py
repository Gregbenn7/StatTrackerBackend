"""Game-related API routes."""

import logging
import io
import pandas as pd
from datetime import datetime, date
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query, Depends
from app.schemas.responses import GameBasic, GameDetail, PlateAppearanceDetail, UploadCsvResponse
from app.services.ingest_service import IngestService
from app.services.stats_service import StatsService
from app.services.game_service import GameService
from app.api.deps import get_ingest_service, get_stats_service, get_game_service
from app.repositories.stats_repository import StatsRepository
from app.repositories.player_repository import PlayerRepository
from app.api.deps import get_stats_repo, get_player_repo
from app.utils.stat_calculators import get_game_avg

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/games", tags=["games"])


@router.post("/upload_csv", response_model=UploadCsvResponse)
async def upload_csv(
    file: UploadFile = File(...),
    league: str = Form(...),
    season: str = Form(...),
    date_str: str = Form(...),
    home_team: str = Form(None),
    away_team: str = Form(None),
    ingest_service: IngestService = Depends(get_ingest_service),
    stats_service: StatsService = Depends(get_stats_service),
):
    """
    Upload a single-game HitTrax CSV, ingest stats, and store them.
    Teams are automatically detected from CSV if home_team and away_team are not provided.
    """
    logger.info(f"Received upload request: file={file.filename}, league={league}, season={season}, date={date_str}, home={home_team}, away={away_team}")
    
    try:
        game_date: date = datetime.strptime(date_str, "%Y-%m-%d").date()
        logger.info(f"Parsed date: {game_date}")
    except ValueError as e:
        logger.error(f"Invalid date format: {date_str}, error: {e}")
        raise HTTPException(status_code=400, detail="Invalid date format, expected YYYY-MM-DD")
    
    try:
        # Import memory store to check current state
        from app.storage.memory_store import store
        
        logger.info("=" * 60)
        logger.info("=== CSV UPLOAD STARTED ===")
        logger.info(f"File: {file.filename}")
        logger.info(f"League: {league}, Season: {season}, Date: {date_str}")
        logger.info(f"Teams provided: home={home_team}, away={away_team}")
        logger.info("=" * 60)
        logger.info(f"📊 CURRENT STATE BEFORE UPLOAD:")
        logger.info(f"   - Total games in memory: {len(store._games)}")
        logger.info(f"   - Total plate appearances: {len(store._plate_appearances)}")
        logger.info("=" * 60)
        
        # First, parse CSV to detect teams (if not provided) to check for duplicates
        # We need to know the teams before we can check for duplicates
        logger.info("Parsing CSV to detect teams for duplicate check...")
        
        # Read file content for parsing
        file.file.seek(0)
        content = file.file.read()
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            text = content.decode("latin-1")
        
        # Detect teams from CSV if not provided
        detected_home_team = home_team
        detected_away_team = away_team
        
        if not home_team or not away_team:
            is_hittrax_format = 'Batting Order' in text
            if is_hittrax_format:
                team_data = ingest_service._detect_teams_from_hittrax_format(text)
                detected_home_team = team_data['team1_name']
                detected_away_team = team_data['team2_name']
            else:
                # Standard CSV format
                df = pd.read_csv(io.StringIO(text))
                df.columns = [col.strip() for col in df.columns]
                normalized_columns = {col: ingest_service._normalize_column_name(col) for col in df.columns}
                df = df.rename(columns=normalized_columns)
                team_data = ingest_service._detect_teams_from_csv(df)
                detected_home_team = team_data['team1_name']
                detected_away_team = team_data['team2_name']
        
        logger.info(f"Detected teams: {detected_home_team} vs {detected_away_team}")
        
        # Check for duplicate game
        existing_game = store.check_duplicate_game(
            date=game_date,
            league=league,
            season=season,
            home_team=detected_home_team,
            away_team=detected_away_team
        )
        
        if existing_game:
            duplicate_msg = (
                f"This game already exists in the system!\n"
                f"Game: {existing_game.home_team} vs {existing_game.away_team}\n"
                f"Date: {existing_game.date}\n"
                f"League: {existing_game.league}, Season: {existing_game.season}\n"
                f"Please upload a different game or check your files."
            )
            logger.warning(f"Duplicate upload attempt blocked: {duplicate_msg}")
            raise HTTPException(status_code=409, detail=duplicate_msg)
        
        logger.info("No duplicate found. Proceeding with upload...")
        
        # Reset file pointer for full ingestion
        file.file.seek(0)
        
        logger.info("Starting CSV ingestion...")
        rows_ingested, game_id, game_info = await ingest_service.ingest_game_csv(
            file=file,
            league=league,
            season=season,
            game_date=game_date,
            home_team=home_team if home_team else None,
            away_team=away_team if away_team else None,
        )
        
        # Import memory store to check state after upload
        from app.storage.memory_store import store
        
        logger.info("=" * 60)
        logger.info("=== CSV UPLOAD SUCCESSFUL ===")
        logger.info(f"Game ID: {game_id}")
        logger.info(f"Rows ingested: {rows_ingested}")
        logger.info(f"Teams: {game_info['home_team']} vs {game_info['away_team']}")
        logger.info(f"Score: {game_info['home_score']} - {game_info['away_score']}")
        logger.info(f"Winner: {game_info['winner'] or 'Tie'}")
        logger.info(f"Team 1 players: {game_info.get('team1_player_count', 'N/A')}")
        logger.info(f"Team 2 players: {game_info.get('team2_player_count', 'N/A')}")
        logger.info("=" * 60)
        logger.info(f"📊 CURRENT STATE AFTER UPLOAD:")
        logger.info(f"   - Total games in memory: {len(store._games)}")
        logger.info(f"   - Total plate appearances: {len(store._plate_appearances)}")
        logger.info("=" * 60)
        
        # Recompute hitter totals
        logger.info(f"Recomputing hitter totals for {league}/{season}...")
        stats_service.recompute_hitter_totals(league, season)
        logger.info("Hitter totals recomputed successfully")
        
        # Build success message with game info
        score_msg = f"{game_info['home_score']}-{game_info['away_score']}"
        winner_msg = f", Winner: {game_info['winner']}" if game_info['winner'] else ", Tie"
        message = f"Game uploaded: {game_info['home_team']} vs {game_info['away_team']}, Score: {score_msg}{winner_msg}"
        
        return UploadCsvResponse(
            game_id=game_id,
            rows_ingested=rows_ingested,
            message=message,
        )
    except ValueError as e:
        logger.error("=" * 60)
        logger.error("=== CSV UPLOAD FAILED (Validation Error) ===")
        logger.error(f"Error: {str(e)}")
        logger.error("=" * 60)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("=" * 60)
        logger.error("=== CSV UPLOAD FAILED (Server Error) ===")
        logger.error(f"Error: {str(e)}")
        logger.error("Full traceback:", exc_info=True)
        logger.error("=" * 60)
        raise HTTPException(status_code=500, detail=f"Error ingesting CSV: {str(e)}")


@router.get("", response_model=List[GameBasic])
def get_games(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    league: Optional[str] = Query(None),
    season: Optional[str] = Query(None),
    game_service: GameService = Depends(get_game_service),
):
    """Get recent games with pagination, optionally filtered by league and/or season."""
    # Normalize empty strings to None
    if league == "":
        league = None
    if season == "":
        season = None
    
    games = game_service.get_games(limit=limit, offset=offset, league=league, season=season)
    
    return [
        GameBasic(
            id=game.id,
            league=game.league,
            season=game.season,
            date=game.date,
            home_team=game.home_team,
            away_team=game.away_team,
            home_score=game.home_score,
            away_score=game.away_score,
            winner=game.winner
        )
        for game in games
    ]


@router.get("/{game_id}", response_model=GameDetail)
def get_game(
    game_id: int,
    game_service: GameService = Depends(get_game_service),
    stats_repo: StatsRepository = Depends(get_stats_repo),
    player_repo: PlayerRepository = Depends(get_player_repo),
):
    """Get a specific game with all plate appearances."""
    game = game_service.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail=f"Game {game_id} not found")
    
    # Get plate appearances for this game
    plate_apps = stats_repo.get_plate_appearances_by_game(game_id)
    players = {p.id: p for p in player_repo.get_all()}
    
    plate_appearances = []
    for plate_app in plate_apps:
        player = players.get(plate_app.player_id)
        if not player:
            continue
        plate_appearances.append(PlateAppearanceDetail(
            id=plate_app.id,
            player_name=player.name,
            team=plate_app.team,
            AB=plate_app.AB,
            H=plate_app.H,
            HR=plate_app.HR,
            RBI=plate_app.RBI,
            AVG=get_game_avg(plate_app.H, plate_app.AB)
        ))
    
    return GameDetail(
        id=game.id,
        league=game.league,
        season=game.season,
        date=game.date,
        home_team=game.home_team,
        away_team=game.away_team,
        home_score=game.home_score,
        away_score=game.away_score,
        winner=game.winner,
        created_at=game.created_at or datetime.utcnow(),
        plate_appearances=plate_appearances
    )

