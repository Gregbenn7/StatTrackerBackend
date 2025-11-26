import json
import os
from typing import Dict, List
from pathlib import Path
from sqlmodel import Session, select
from openai import OpenAI
from dotenv import load_dotenv
from app.models import Game, PlateAppearance, Player, GameStorylines

# Load .env file from project root
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)
    print(f"Loaded .env from: {env_path}")

# Also try loading from current directory as fallback
load_dotenv(override=True)

client = None
api_key = os.getenv("OPENAI_API_KEY")
if api_key and api_key.strip():
    try:
        client = OpenAI(api_key=api_key.strip())
        print("[OK] OpenAI client initialized successfully")
    except Exception as e:
        print(f"[ERROR] Error initializing OpenAI client: {e}")
        client = None
else:
    print("[WARNING] OPENAI_API_KEY not found in environment variables")
    print(f"  Current working directory: {os.getcwd()}")
    print(f"  .env file exists: {env_path.exists()}")


def build_game_summary_json(session: Session, game_id: int) -> Dict:
    """Build a JSON summary of game stats for OpenAI prompt."""
    # Get game
    game = session.get(Game, game_id)
    if not game:
        raise ValueError(f"Game {game_id} not found")
    
    # Get all plate appearances for this game
    statement = select(PlateAppearance, Player).join(
        Player, PlateAppearance.player_id == Player.id
    ).where(
        PlateAppearance.game_id == game_id
    )
    results = session.exec(statement).all()
    
    # Group by team
    home_stats = {'runs': 0, 'hits': 0, 'hitters': []}
    away_stats = {'runs': 0, 'hits': 0, 'hitters': []}
    
    for plate_app, player in results:
        team_stats = home_stats if plate_app.team == game.home_team else away_stats
        
        # Calculate game AVG
        game_avg = plate_app.H / plate_app.AB if plate_app.AB > 0 else 0.0
        total_bases = (plate_app.H - plate_app.double - plate_app.triple - plate_app.HR) + \
                     2 * plate_app.double + 3 * plate_app.triple + 4 * plate_app.HR
        game_slg = total_bases / plate_app.AB if plate_app.AB > 0 else 0.0
        game_obp = (plate_app.H + plate_app.BB + plate_app.HBP) / \
                  (plate_app.AB + plate_app.BB + plate_app.HBP + plate_app.SF) \
                  if (plate_app.AB + plate_app.BB + plate_app.HBP + plate_app.SF) > 0 else 0.0
        game_ops = game_obp + game_slg
        
        hitter_data = {
            'name': player.name,
            'AB': plate_app.AB,
            'H': plate_app.H,
            'HR': plate_app.HR,
            'RBI': plate_app.RBI,
            'R': plate_app.R,
            '2B': plate_app.double,
            '3B': plate_app.triple,
            'BB': plate_app.BB,
            'K': plate_app.K,
            'AVG': round(game_avg, 3),
            'OPS': round(game_ops, 3)
        }
        team_stats['hitters'].append(hitter_data)
        team_stats['runs'] += plate_app.R
        team_stats['hits'] += plate_app.H
    
    # Sort hitters by OPS (descending)
    home_stats['hitters'].sort(key=lambda x: x['OPS'], reverse=True)
    away_stats['hitters'].sort(key=lambda x: x['OPS'], reverse=True)
    
    summary = {
        'game': {
            'date': str(game.date),
            'home_team': game.home_team,
            'away_team': game.away_team,
            'league': game.league,
            'season': game.season
        },
        'home_team': {
            'name': game.home_team,
            'runs': home_stats['runs'],
            'hits': home_stats['hits'],
            'top_hitters': home_stats['hitters'][:5]  # Top 5 by OPS
        },
        'away_team': {
            'name': game.away_team,
            'runs': away_stats['runs'],
            'hits': away_stats['hits'],
            'top_hitters': away_stats['hitters'][:5]  # Top 5 by OPS
        }
    }
    
    return summary


def generate_storylines(session: Session, game_id: int) -> GameStorylines:
    """Generate AI storylines for a game using OpenAI."""
    # Re-check API key in case it wasn't loaded at module import time
    global client
    if not client:
        # Try to reload from environment
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key and api_key.strip():
            try:
                client = OpenAI(api_key=api_key.strip())
            except Exception as e:
                raise ValueError(f"OpenAI API key not configured properly. Error: {e}")
        else:
            raise ValueError("OpenAI API key not configured. Set OPENAI_API_KEY in .env file.")
    
    # Build game summary
    game_summary = build_game_summary_json(session, game_id)
    
    # Create prompt
    prompt = f"""You are a baseball beat writer for an adult HitTrax league. Given this JSON of game stats, write:
- A short recap paragraph for this game (2-3 sentences)
- 3 bullet-point key storylines
- A 'Player of the Game' blurb (1-2 sentences)
- 3 short, social-media-ready captions (under 120 characters each)

JSON:
{json.dumps(game_summary, indent=2)}

Format your response as JSON with this exact structure:
{{
  "recap": "Your recap paragraph here",
  "key_storylines": ["Storyline 1", "Storyline 2", "Storyline 3"],
  "player_of_game": "Your player of the game blurb here",
  "social_captions": ["Caption 1", "Caption 2", "Caption 3"]
}}"""
    
    # Call OpenAI
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a baseball beat writer. Always respond with valid JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    
    response_text = response.choices[0].message.content
    
    # Try to extract JSON from response
    try:
        # Try to parse as-is
        structured = json.loads(response_text)
    except json.JSONDecodeError:
        # Try to extract JSON from markdown code blocks
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            structured = json.loads(response_text[json_start:json_end].strip())
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            structured = json.loads(response_text[json_start:json_end].strip())
        else:
            # Fallback: create a structured version from the raw text
            structured = {
                "recap": response_text[:500],
                "key_storylines": ["See full storylines text for details"],
                "player_of_game": "See full storylines text for details",
                "social_captions": ["See full storylines text for details"]
            }
    
    # Check if storylines already exist for this game
    statement = select(GameStorylines).where(GameStorylines.game_id == game_id)
    existing = session.exec(statement).first()
    
    if existing:
        existing.storylines_text = response_text
        existing.json_summary = json.dumps(structured)
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing
    else:
        game_storylines = GameStorylines(
            game_id=game_id,
            storylines_text=response_text,
            json_summary=json.dumps(structured)
        )
        session.add(game_storylines)
        session.commit()
        session.refresh(game_storylines)
        return game_storylines

