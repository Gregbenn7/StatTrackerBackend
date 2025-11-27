/**
 * Game-related TypeScript types.
 */

export interface Game {
  id: number;
  league: string;
  season: string;
  date: string;
  home_team: string;
  away_team: string;
  home_score?: number;
  away_score?: number;
  winner?: string | null;
  created_at?: string;
}

export interface PlateAppearance {
  id: number;
  player_name: string;
  team: string;
  AB: number;
  H: number;
  HR: number;
  RBI: number;
  AVG: number;
}

export interface GameDetail extends Game {
  plate_appearances: PlateAppearance[];
}

export interface GameStoryline {
  id: string;
  game_id: string;
  league_id: string;
  primary_headline: string;
  recap_body: string;
  key_moments: string[];
  player_of_game: string;
  social_captions: string[];
  created_at: string;
}

export interface UploadMetadata {
  league: string;
  season: string;
  date_str: string; // YYYY-MM-DD format
  home_team?: string; // Optional - will be auto-detected from CSV
  away_team?: string; // Optional - will be auto-detected from CSV
}

export interface UploadResponse {
  game_id: number;
  rows_ingested: number;
  message: string;
}

