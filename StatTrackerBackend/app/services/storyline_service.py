"""Storyline generation service using OpenAI."""

import json
import logging
from typing import Dict, List, Any
from openai import OpenAI
from app.models.storyline import GameStorylines
from app.models.game import Game
from app.models.plate_appearance import PlateAppearance
from app.models.player import Player
from app.core.config import settings
from app.storage.memory_store import store

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Initialize OpenAI client
try:
    if settings.OPENAI_API_KEY and settings.validate_openai_key():
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        logger.info("✓ OpenAI client initialized successfully")
    else:
        client = None
        logger.warning("OpenAI API key not configured")
except Exception as e:
    logger.error(f"✗ Failed to initialize OpenAI client: {e}")
    client = None

if not client:
    logger.warning("✗ OpenAI client is None - storylines will not work")


class StorylineService:
    """Generate AI-powered ESPN-style game recaps."""
    
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
    
    @staticmethod
    def generate_game_recap(
        game: Game,
        team1_players: List[PlateAppearance],
        team2_players: List[PlateAppearance]
    ) -> Dict[str, Any]:
        """
        Generate ESPN/GameChanger-style game recap using OpenAI.
        
        Args:
            game: Game object with teams, scores, winner
            team1_players: Plate appearances for home team
            team2_players: Plate appearances for away team
        
        Returns:
            {
                'headline': str (max 12 words),
                'recap': str (full formatted recap),
                'key_players': List[str],
                'game_summary': str
            }
        """
        
        logger.info("generate_game_recap called")
        logger.info(f"  Game: {game.home_team} vs {game.away_team}")
        logger.info(f"  Team 1 players: {len(team1_players)}")
        logger.info(f"  Team 2 players: {len(team2_players)}")
        
        if client is None:
            logger.error("OpenAI client is None!")
            raise ValueError(
                "OpenAI client not initialized. "
                "Please set OPENAI_API_KEY in your .env file."
            )
        
        # Format team statistics
        home_team_stats = StorylineService._format_team_stats(
            team1_players, 
            game.home_team
        )
        away_team_stats = StorylineService._format_team_stats(
            team2_players, 
            game.away_team
        )
        
        # Identify top performers across both teams
        all_players = team1_players + team2_players
        top_performers = StorylineService._get_top_performers(all_players, top_n=3)
        
        # Build the enhanced ESPN-style prompt
        prompt = f"""You are a professional sports recap writer producing ESPN/GameChanger-style summaries.

GOAL: Generate a clear, energetic game recap using ONLY the provided stats and play data.

FORMAT:

1. Headline (max 12 words)
2. Opening Summary – winner, final score, main storyline
3. Key Game Moments – 2–4 major plays or turning points
4. Standout Players – highlight top performers with specific stats
5. Team Notes – efficiency, batting performance, offensive trends
6. Closing Line – short, strong concluding sentence

RULES:

- No invented stats or guesses
- Use ESPN-quality tone
- Keep paragraphs tight and professional
- Focus on standout performances and decisive plays
- Never mention missing info
- Use baseball terminology appropriately (hits, runs, RBIs, extra-base hits)
- Make it exciting but factual

INPUT DATA:

Sport: Baseball (Adult Baseball League)

Date: {game.date}

Teams: {game.home_team} vs {game.away_team}

Final Score: {game.home_team} {game.home_score}, {game.away_team} {game.away_score}

Winner: {game.winner}

{game.home_team} PLAYER STATS:

{home_team_stats}

{game.away_team} PLAYER STATS:

{away_team_stats}

TOP PERFORMERS (Cross-Team):

{StorylineService._format_top_performers(top_performers)}

KEY CONTEXT:

- Total Runs: {game.home_score + game.away_score}
- Run Differential: {abs(game.home_score - game.away_score)}
- Competitive Level: {"Close game" if abs(game.home_score - game.away_score) <= 2 else "Dominant performance"}

TASK: Generate the full game recap following the format above. Make it engaging, professional, and ESPN-quality."""

        try:
            logger.info(f"\n=== Generating Game Recap ===")
            logger.info(f"Game: {game.home_team} vs {game.away_team}")
            logger.info(f"Score: {game.home_score}-{game.away_score}")
            
            # Call OpenAI API
            response = client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert sports journalist specializing in baseball. "
                            "Write professional, engaging game recaps in the style of ESPN. "
                            "Use only the stats provided - never invent or assume data."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=settings.OPENAI_MAX_TOKENS,
                temperature=settings.OPENAI_TEMPERATURE
            )
            
            full_recap = response.choices[0].message.content.strip()
            
            # Extract headline (typically first line)
            lines = [line.strip() for line in full_recap.split('\n') if line.strip()]
            headline = lines[0].strip('#').strip() if lines else f"{game.winner} Defeats {game.away_team if game.winner == game.home_team else game.home_team}"
            
            # Generate concise summary
            summary = f"{game.winner} defeats {game.away_team if game.winner == game.home_team else game.home_team} {max(game.home_score, game.away_score)}-{min(game.home_score, game.away_score)}"
            
            logger.info(f"✓ Recap generated successfully")
            logger.info(f"  Headline: {headline}")
            logger.info("===============================\n")
            
            return {
                'headline': headline,
                'recap': full_recap,
                'key_players': [p['name'] for p in top_performers],
                'game_summary': summary
            }
            
        except Exception as e:
            logger.error(f"✗ Error generating storyline: {str(e)}")
            
            # Return fallback recap
            fallback_headline = f"{game.winner} Wins {max(game.home_score, game.away_score)}-{min(game.home_score, game.away_score)}"
            fallback_recap = f"""# {fallback_headline}

The {game.winner} defeated the {game.away_team if game.winner == game.home_team else game.home_team} by a score of {max(game.home_score, game.away_score)}-{min(game.home_score, game.away_score)} on {game.date}.

## Top Performers

{StorylineService._format_top_performers(top_performers)}

Game statistics show a competitive matchup between both teams."""
            
            return {
                'headline': fallback_headline,
                'recap': fallback_recap,
                'key_players': [p['name'] for p in top_performers],
                'game_summary': f"{game.winner} wins {max(game.home_score, game.away_score)}-{min(game.home_score, game.away_score)}"
            }
    
    def generate_storylines(self, game_id: int) -> GameStorylines:
        """Generate AI storylines for a game using OpenAI."""
        if not client:
            raise ValueError("OpenAI API key not configured. Set OPENAI_API_KEY in .env file.")
        
        # Get game
        game = store.get_game(game_id)
        if not game:
            raise ValueError(f"Game {game_id} not found")
        
        # Get all plate appearances for this game
        plate_apps = store.get_plate_appearances_by_game(game_id)
        players = {p.id: p for p in store.get_all_players()}
        
        if not plate_apps:
            raise ValueError(f"No player data found for game {game_id}")
        
        # Separate by team
        home_team_pas = [pa for pa in plate_apps if pa.team == game.home_team]
        away_team_pas = [pa for pa in plate_apps if pa.team == game.away_team]
        
        if not home_team_pas or not away_team_pas:
            raise ValueError("Incomplete game data. Both teams must have player stats.")
        
        # Generate recap
        recap_data = StorylineService.generate_game_recap(
            game=game,
            team1_players=home_team_pas,
            team2_players=away_team_pas
        )
        
        # Create structured JSON response (for backward compatibility)
        structured = {
            "recap": recap_data['recap'],
            "key_storylines": [
                f"{recap_data['headline']}",
                f"Final Score: {game.home_team} {game.home_score}, {game.away_team} {game.away_score}",
                f"Winner: {recap_data['game_summary']}"
            ],
            "player_of_game": f"Top performers: {', '.join(recap_data['key_players'])}",
            "social_captions": [
                recap_data['headline'][:120],
                recap_data['game_summary'][:120],
                f"{game.winner} takes the win!"[:120]
            ]
        }
        
        # Create or update storylines
        storyline = GameStorylines(
            game_id=game_id,
            storylines_text=recap_data['recap'],
            json_summary=json.dumps(structured)
        )
        
        return store.create_or_update_storyline(storyline)
    
    def get_storyline(self, game_id: int) -> GameStorylines | None:
        """Get storylines for a game."""
        return store.get_storyline(game_id)
    
    @staticmethod
    def _format_team_stats(plate_apps: List[PlateAppearance], team_name: str) -> str:
        """Format team player stats for the prompt."""
        if not plate_apps:
            return f"{team_name}: No player data available"
        
        players = {p.id: p for p in store.get_all_players()}
        lines = []
        
        for pa in plate_apps:
            player = players.get(pa.player_id)
            if not player:
                continue
            
            avg = f"{(pa.H / pa.AB):.3f}" if pa.AB > 0 else ".000"
            
            parts = [f"{player.name}: {pa.AB} AB, {pa.H} H"]
            
            if pa.double > 0:
                parts.append(f"{pa.double} 2B")
            if pa.triple > 0:
                parts.append(f"{pa.triple} 3B")
            if pa.HR > 0:
                parts.append(f"{pa.HR} HR")
            if pa.RBI > 0:
                parts.append(f"{pa.RBI} RBI")
            if pa.R > 0:
                parts.append(f"{pa.R} R")
            if pa.BB > 0:
                parts.append(f"{pa.BB} BB")
            
            parts.append(f"(AVG: {avg})")
            lines.append("- " + ", ".join(parts))
        
        return "\n".join(lines) if lines else f"{team_name}: No player data available"
    
    @staticmethod
    def _get_top_performers(
        plate_apps: List[PlateAppearance], 
        top_n: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Identify top performers using a weighted performance score.
        
        Score = (H * 2) + (2B * 3) + (3B * 5) + (HR * 8) + (RBI * 2) + (R * 1.5)
        """
        players = {p.id: p for p in store.get_all_players()}
        player_scores = []
        
        for pa in plate_apps:
            player = players.get(pa.player_id)
            if not player:
                continue
            
            score = (
                (pa.H * 2) +
                (pa.double * 3) +
                (pa.triple * 5) +
                (pa.HR * 8) +
                (pa.RBI * 2) +
                (pa.R * 1.5)
            )
            
            player_scores.append({
                'name': player.name,
                'team': pa.team,
                'score': score,
                'stats': pa
            })
        
        # Sort by score and return top N
        player_scores.sort(key=lambda x: x['score'], reverse=True)
        return player_scores[:top_n]
    
    @staticmethod
    def _format_top_performers(performers: List[Dict[str, Any]]) -> str:
        """Format top performers for the prompt."""
        lines = []
        for i, p in enumerate(performers, 1):
            pa = p['stats']
            highlights = []
            
            if pa.H > 0:
                highlights.append(f"{pa.H} hits")
            if pa.HR > 0:
                highlights.append(f"{pa.HR} HR")
            if pa.RBI > 0:
                highlights.append(f"{pa.RBI} RBI")
            if pa.R > 0:
                highlights.append(f"{pa.R} runs")
            
            performance = ", ".join(highlights) if highlights else "solid performance"
            lines.append(f"{i}. {p['name']} ({p['team']}): {performance}")
        
        return "\n".join(lines) if lines else "No standout performers"

