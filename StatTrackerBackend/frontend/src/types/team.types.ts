/** Team-related types. */

export interface Team {
  name: string;
  league: string;
  season: string;
}

export interface TeamStats {
  name: string;
  league: string;
  season: string;
  games_played: number;
  wins: number;
  losses: number;
  win_pct: number;
  runs_scored: number;
  runs_allowed: number;
  run_differential: number;
  team_avg: number;
  team_obp: number;
  team_slg: number;
  team_ops: number;
}

export interface TeamStanding {
  rank: number;
  name: string;
  wins: number;
  losses: number;
  win_pct: number;
  games_behind: number;
  runs_scored: number;
  runs_allowed: number;
  run_differential: number;
}

