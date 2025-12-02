export interface League {
  id: string;
  name: string;
  state?: string;
  created_at: string;
}

export interface Team {
  id: string;
  league_id: string;
  name: string;
  created_at: string;
}

export interface Player {
  id: string;
  league_id: string;
  team_id?: string;
  full_name: string;
  nickname?: string;
  created_at: string;
}

export interface Game {
  id: string;
  league_id: string;
  home_team_id: string;
  away_team_id: string;
  game_date: string;
  raw_csv_url?: string;
  created_at: string;
}

export interface GameHittingStats {
  id: string;
  game_id: string;
  player_id: string;
  team_id: string;
  batting_order?: number;
  ab: number;
  h: number;
  doubles: number;
  triples: number;
  hr: number;
  bb: number;
  hbp: number;
  sf: number;
  sh: number;
  k: number;
  r: number;
  rbi: number;
  sb: number;
  cs: number;
  exit_velo_avg?: number;
  launch_angle_avg?: number;
}

export interface HitterSeasonTotals {
  id: string;
  league_id: string;
  player_id: string;
  team_id: string;
  player_name?: string;
  team_name?: string;
  games_played: number;
  ab: number;
  h: number;
  singles: number;
  doubles: number;
  triples: number;
  hr: number;
  bb: number;
  hbp: number;
  sf: number;
  sh: number;
  k: number;
  r: number;
  rbi: number;
  sb: number;
  cs: number;
  pa: number;
  tb: number;
  avg: number;
  obp: number;
  slg: number;
  ops: number;
  created_at: string;
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

export interface WeeklyStoryline {
  id: string;
  league_id: string;
  week_start: string;
  week_end: string;
  headline: string;
  recap_body: string;
  hot_players: Array<{ name: string; stats: string }>;
  power_rankings: Array<{ team: string; commentary: string }>;
  social_captions: string[];
  created_at: string;
}
