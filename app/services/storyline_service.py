"""Storyline generation service using OpenAI."""

import json
import logging
from typing import Dict
from openai import OpenAI
from app.models.storyline import GameStorylines
from app.models.game import Game
from app.models.plate_appearance import PlateAppearance
from app.models.player import Player
from app.core.config import settings
from app.storage.memory_store import store

logger = logging.getLogger(__name__)


class StorylineService:
    """Service for generating AI storylines."""
    
    def __init__(self):
        """Initialize the storyline service."""
        self.client: OpenAI | None = None
        if settings.OPENAI_API_KEY:
            try:
                self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.error(f"Error initializing OpenAI client: {e}")
    
    def build_game_summary_json(self, game_id: int) -> Dict:
        """Build a JSON summary of game stats for OpenAI prompt."""
        game = store.get_game(game_id)
        if not game:
            raise ValueError(f"Game {game_id} not found")
        
        # Get all plate appearances for this game
        plate_apps = store.get_plate_appearances_by_game(game_id)
        players = {p.id: p for p in store.get_all_players()}
        
        # Group by team
        home_stats = {'runs': 0, 'hits': 0, 'hitters': []}
        away_stats = {'runs': 0, 'hits': 0, 'hitters': []}
        
        for pa in plate_apps:
            player = players.get(pa.player_id)
            if not player:
                continue
                
            team_stats = home_stats if pa.team == game.home_team else away_stats
            
            # Calculate game stats
            game_avg = pa.H / pa.AB if pa.AB > 0 else 0.0
            total_bases = (pa.H - pa.double - pa.triple - pa.HR) + \
                         2 * pa.double + 3 * pa.triple + 4 * pa.HR
            game_slg = total_bases / pa.AB if pa.AB > 0 else 0.0
            game_obp = (pa.H + pa.BB + pa.HBP) / \
                      (pa.AB + pa.BB + pa.HBP + pa.SF) \
                      if (pa.AB + pa.BB + pa.HBP + pa.SF) > 0 else 0.0
            game_ops = game_obp + game_slg
            
            hitter_data = {
                'name': player.name,
                'AB': pa.AB,
                'H': pa.H,
                'HR': pa.HR,
                'RBI': pa.RBI,
                'R': pa.R,
                '2B': pa.double,
                '3B': pa.triple,
                'BB': pa.BB,
                'K': pa.K,
                'AVG': round(game_avg, 3),
                'OPS': round(game_ops, 3)
            }
            team_stats['hitters'].append(hitter_data)
            team_stats['runs'] += pa.R
            team_stats['hits'] += pa.H
        
        # Sort hitters by OPS
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
                'top_hitters': home_stats['hitters'][:5]
            },
            'away_team': {
                'name': game.away_team,
                'runs': away_stats['runs'],
                'hits': away_stats['hits'],
                'top_hitters': away_stats['hitters'][:5]
            }
        }
        
        return summary
    
    def generate_storylines(self, game_id: int) -> GameStorylines:
        """Generate AI storylines for a game using OpenAI."""
        if not self.client:
            raise ValueError("OpenAI API key not configured. Set OPENAI_API_KEY in .env file.")
        
        # Build game summary
        game_summary = self.build_game_summary_json(game_id)
        
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
        response = self.client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a baseball beat writer. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        response_text = response.choices[0].message.content
        
        # Try to extract JSON from response
        try:
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
                structured = {
                    "recap": response_text[:500],
                    "key_storylines": ["See full storylines text for details"],
                    "player_of_game": "See full storylines text for details",
                    "social_captions": ["See full storylines text for details"]
                }
        
        # Create or update storylines
        storyline = GameStorylines(
            game_id=game_id,
            storylines_text=response_text,
            json_summary=json.dumps(structured)
        )
        
        return store.create_or_update_storyline(storyline)
    
    def get_storyline(self, game_id: int) -> GameStorylines | None:
        """Get storylines for a game."""
        return store.get_storyline(game_id)

