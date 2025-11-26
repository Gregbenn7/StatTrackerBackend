from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from typing import Optional, List
from datetime import date
import os
import json
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.database import get_session, create_db_and_tables
from app.models import Player, Game, PlateAppearance, HitterTotal, GameStorylines
from app.schemas import (
    UploadCsvResponse, LeaderboardEntry, PlayerBasic, PlayerStats, 
    PlayerDetail, GameBasic, PlateAppearanceDetail, GameDetail,
    GameStorylinesResponse, StorylineSummary, ScoutingReportResponse
)
from app.ingest import ingest_game_csv
from app.services.stats import recompute_hitter_totals, get_game_avg
from app.services.storylines import generate_storylines, build_game_summary_json
from openai import OpenAI

load_dotenv()

app = FastAPI(title="Baseball League API", version="1.0.0")

# Configure CORS
# Allow all origins for development - can restrict via FRONTEND_ORIGIN env var if needed
frontend_origin = os.getenv("FRONTEND_ORIGIN")
if frontend_origin:
    # If FRONTEND_ORIGIN is set, use it (production mode)
    cors_origins = [frontend_origin]
    allow_credentials = True
else:
    # Otherwise allow all origins (development mode)
    cors_origins = ["*"]
    allow_credentials = False  # Can't use credentials with wildcard origin

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    """Create database tables on startup."""
    create_db_and_tables()


@app.get("/")
def root():
    return {"message": "Baseball League API", "version": "1.0.0"}


@app.post("/games/upload_csv", response_model=UploadCsvResponse)
async def upload_csv(
    file: UploadFile = File(...),
    league: str = Form(...),
    season: str = Form(...),
    date_str: str = Form(...),
    home_team: str = Form(...),
    away_team: str = Form(...),
    db: Session = Depends(get_session)
):
    """
    Upload a single-game HitTrax CSV, ingest stats, and store them in the DB.
    """
    logger.info(f"Received upload request: file={file.filename}, league={league}, season={season}, date={date_str}, home={home_team}, away={away_team}")
    
    # Parse the date string safely
    try:
        from datetime import datetime
        game_date: date = datetime.strptime(date_str, "%Y-%m-%d").date()
        logger.info(f"Parsed date: {game_date}")
    except ValueError as e:
        logger.error(f"Invalid date format: {date_str}, error: {e}")
        raise HTTPException(status_code=400, detail="Invalid date format, expected YYYY-MM-DD")
    
    try:
        logger.info("Starting CSV ingestion...")
        # Delegate CSV parsing + DB insert to the ingest service
        rows_ingested, game_id = await ingest_game_csv(
            db=db,
            file=file,
            league=league,
            season=season,
            game_date=game_date,
            home_team=home_team,
            away_team=away_team,
        )
        logger.info(f"CSV ingested successfully: {rows_ingested} rows, game_id={game_id}")
        
        # Recompute hitter totals for this league/season
        logger.info(f"Recomputing hitter totals for {league}/{season}...")
        recompute_hitter_totals(db, league, season)
        logger.info("Hitter totals recomputed successfully")
        
        return UploadCsvResponse(
            game_id=game_id,
            rows_ingested=rows_ingested,
            message="Game CSV ingested successfully",
        )
    except ValueError as e:
        logger.error(f"ValueError during upload: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Exception during upload: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error ingesting CSV: {str(e)}")


@app.get("/stats/leaderboard", response_model=List[LeaderboardEntry])
def get_leaderboard(
    league: Optional[str] = Query(None),
    season: Optional[str] = Query(None),
    session: Session = Depends(get_session)
):
    """Get hitting leaderboard, ordered by OPS descending.
    
    If league/season filters are provided, shows stats for that specific league/season.
    If no filters are provided, aggregates stats across all leagues/seasons per player
    to ensure each player appears only once.
    """
    from app.services.stats import compute_derived_stats_from_raw
    
    # Normalize empty strings to None
    if league == "":
        league = None
    if season == "":
        season = None
    
    logger.info(f"Leaderboard request: league={league}, season={season}")
    
    statement = select(HitterTotal, Player).join(
        Player, HitterTotal.player_id == Player.id
    )
    
    if league:
        statement = statement.where(HitterTotal.league == league)
    if season:
        statement = statement.where(HitterTotal.season == season)
    
    results = session.exec(statement).all()
    logger.info(f"Found {len(results)} HitterTotal records")
    
    # Aggregate stats per player to avoid duplicates
    # Only skip aggregation if BOTH league AND season filters are provided (unique HitterTotal per player)
    # Otherwise, aggregate to ensure each player appears only once
    needs_aggregation = not (league and season)
    logger.info(f"Needs aggregation: {needs_aggregation}")
    
    if needs_aggregation:
        logger.info("Aggregating stats per player...")
        # Aggregate stats by player_id
        player_aggregates = {}
        for hitter_total, player in results:
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
        return entries
    else:
        logger.info("Using filtered results without aggregation")
        # With filters, each HitterTotal is already unique per player for that league/season
        entries = []
        for hitter_total, player in results:
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
        return entries


# OLD VERSION (commented for reference):
# @app.get("/players", response_model=List[PlayerStats])
# def get_players(
#     league: Optional[str] = Query(None),
#     season: Optional[str] = Query(None),
#     session: Session = Depends(get_session)
# ):
#     """Get all players with their stats."""
#     statement = select(HitterTotal, Player).join(
#         Player, HitterTotal.player_id == Player.id
#     )
#     
#     if league:
#         statement = statement.where(HitterTotal.league == league)
#     if season:
#         statement = statement.where(HitterTotal.season == season)
#     
#     results = session.exec(statement).all()
#     
#     player_stats_list = []
#     for hitter_total, player in results:
#         player_stats_list.append(PlayerStats(
#             player=PlayerBasic(
#                 id=player.id,
#                 name=player.name,
#                 team=player.team,
#                 league=player.league
#             ),
#             league=hitter_total.league,
#             season=hitter_total.season,
#             games=hitter_total.games,
#             AB=hitter_total.AB,
#             H=hitter_total.H,
#             HR=hitter_total.HR,
#             RBI=hitter_total.RBI,
#             AVG=hitter_total.AVG,
#             OBP=hitter_total.OBP,
#             SLG=hitter_total.SLG,
#             OPS=hitter_total.OPS
#         ))
#     
#     return player_stats_list


@app.get("/players", response_model=List[PlayerStats])
def get_players(
    league: Optional[str] = Query(None),
    season: Optional[str] = Query(None),
    team: Optional[str] = Query(None),
    session: Session = Depends(get_session)
):
    """
    Get all players with their stats grouped by (team, player_name, league, season).
    Stats are aggregated from PlateAppearance records.
    
    Optional query parameters:
    - league: Filter by league
    - season: Filter by season  
    - team: Filter by team name
    """
    from app.services.stats import get_player_stats_by_team
    
    # Get aggregated stats
    stats_list = get_player_stats_by_team(
        session=session,
        league=league,
        season=season,
        team=team
    )
    
    # Handle empty case
    if not stats_list:
        return []
    
    # Convert to Pydantic models
    player_stats_list = []
    for stats in stats_list:
        player_stats_list.append(PlayerStats(
            player_id=stats['player_id'],
            player_name=stats['player_name'],
            team=stats['team'],
            league=stats['league'],
            season=stats['season'],
            games=stats['games'],
            AB=stats['AB'],
            H=stats['H'],
            singles=stats['singles'],
            double=stats['double'],
            triple=stats['triple'],
            HR=stats['HR'],
            BB=stats['BB'],
            HBP=stats['HBP'],
            SF=stats['SF'],
            SH=stats['SH'],
            K=stats['K'],
            R=stats['R'],
            RBI=stats['RBI'],
            SB=stats['SB'],
            CS=stats['CS'],
            PA=stats['PA'],
            TB=stats['TB'],
            AVG=stats['AVG'],
            OBP=stats['OBP'],
            SLG=stats['SLG'],
            OPS=stats['OPS']
        ))
    
    return player_stats_list


@app.get("/teams")
def get_teams(
    league: Optional[str] = Query(None),
    session: Session = Depends(get_session)
):
    """Get list of unique teams, optionally filtered by league."""
    # Get unique teams from PlateAppearance records (more reliable than Player records)
    # This ensures we get teams that actually have game data
    from app.models import PlateAppearance, Game
    
    if league:
        # Join with Game to filter by league
        statement = select(PlateAppearance.team).join(
            Game, PlateAppearance.game_id == Game.id
        ).where(Game.league == league).distinct()
    else:
        # Get all teams without filtering
        statement = select(PlateAppearance.team).distinct()
    
    teams = session.exec(statement).all()
    
    # Return as simple list of team names
    return {"teams": [team for team in teams if team]}


@app.get("/players/{player_id}", response_model=PlayerDetail)
def get_player(
    player_id: int,
    session: Session = Depends(get_session)
):
    """Get a specific player's info and all their stats."""
    player = session.get(Player, player_id)
    if not player:
        raise HTTPException(status_code=404, detail=f"Player {player_id} not found")
    
    # Get all hitter totals for this player
    statement = select(HitterTotal).where(HitterTotal.player_id == player_id)
    hitter_totals = session.exec(statement).all()
    
    stats_list = []
    for ht in hitter_totals:
        stats_list.append(PlayerStats(
            player=PlayerBasic(
                id=player.id,
                name=player.name,
                team=player.team,
                league=player.league
            ),
            league=ht.league,
            season=ht.season,
            games=ht.games,
            AB=ht.AB,
            H=ht.H,
            HR=ht.HR,
            RBI=ht.RBI,
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
        created_at=player.created_at,
        stats=stats_list
    )


@app.get("/games", response_model=List[GameBasic])
def get_games(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    league: Optional[str] = Query(None),
    season: Optional[str] = Query(None),
    session: Session = Depends(get_session)
):
    """Get recent games with pagination, optionally filtered by league and/or season."""
    statement = select(Game).order_by(Game.date.desc(), Game.created_at.desc())
    
    if league:
        statement = statement.where(Game.league == league)
    if season:
        statement = statement.where(Game.season == season)
    
    statement = statement.offset(offset).limit(limit)
    games = session.exec(statement).all()
    
    return [
        GameBasic(
            id=game.id,
            league=game.league,
            season=game.season,
            date=game.date,
            home_team=game.home_team,
            away_team=game.away_team
        )
        for game in games
    ]


@app.get("/games/{game_id}", response_model=GameDetail)
def get_game(
    game_id: int,
    session: Session = Depends(get_session)
):
    """Get a specific game with all plate appearances."""
    game = session.get(Game, game_id)
    if not game:
        raise HTTPException(status_code=404, detail=f"Game {game_id} not found")
    
    # Get plate appearances for this game
    statement = select(PlateAppearance, Player).join(
        Player, PlateAppearance.player_id == Player.id
    ).where(
        PlateAppearance.game_id == game_id
    )
    results = session.exec(statement).all()
    
    plate_appearances = []
    for plate_app, player in results:
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
        created_at=game.created_at,
        plate_appearances=plate_appearances
    )


@app.post("/games/{game_id}/storylines", response_model=GameStorylinesResponse)
def create_game_storylines(
    game_id: int,
    session: Session = Depends(get_session)
):
    """Generate AI storylines for a game."""
    game = session.get(Game, game_id)
    if not game:
        raise HTTPException(status_code=404, detail=f"Game {game_id} not found")
    
    try:
        game_storylines = generate_storylines(session, game_id)
        
        # Parse JSON summary
        summary_dict = json.loads(game_storylines.json_summary)
        
        return GameStorylinesResponse(
            game_id=game_storylines.game_id,
            storylines_text=game_storylines.storylines_text,
            json_summary=game_storylines.json_summary,
            created_at=game_storylines.created_at,
            summary=StorylineSummary(**summary_dict)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating storylines: {str(e)}")


@app.get("/games/{game_id}/storylines", response_model=GameStorylinesResponse)
def get_game_storylines(
    game_id: int,
    session: Session = Depends(get_session)
):
    """Get saved storylines for a game."""
    game = session.get(Game, game_id)
    if not game:
        raise HTTPException(status_code=404, detail=f"Game {game_id} not found")
    
    statement = select(GameStorylines).where(GameStorylines.game_id == game_id)
    game_storylines = session.exec(statement).first()
    
    if not game_storylines:
        raise HTTPException(status_code=404, detail=f"Storylines not found for game {game_id}")
    
    # Parse JSON summary
    summary_dict = json.loads(game_storylines.json_summary)
    
    return GameStorylinesResponse(
        game_id=game_storylines.game_id,
        storylines_text=game_storylines.storylines_text,
        json_summary=game_storylines.json_summary,
        created_at=game_storylines.created_at,
        summary=StorylineSummary(**summary_dict)
    )


@app.get("/players/{player_id}/scouting_report", response_model=ScoutingReportResponse)
def get_player_scouting_report(
    player_id: int,
    session: Session = Depends(get_session)
):
    """Generate an AI scouting report for a player."""
    player = session.get(Player, player_id)
    if not player:
        raise HTTPException(status_code=404, detail=f"Player {player_id} not found")
    
    # Get all hitter totals for this player
    statement = select(HitterTotal).where(HitterTotal.player_id == player_id).order_by(
        HitterTotal.season.desc(), HitterTotal.league
    )
    hitter_totals = session.exec(statement).all()
    
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
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
    
    client = OpenAI(api_key=api_key)
    
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
            model="gpt-4o-mini",
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

