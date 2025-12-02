/**
 * Player-related TypeScript types.
 */

export interface Player {
  id: number;
  name: string;
  team: string;
  league?: string;
  created_at?: string;
}

export interface PlayerStats {
  player_id: number;
  player_name: string;
  team: string;
  league: string;
  season: string;
  games: number;
  AB: number;
  H: number;
  singles: number;
  double: number;
  triple: number;
  HR: number;
  BB: number;
  HBP: number;
  SF: number;
  SH: number;
  K: number;
  R: number;
  RBI: number;
  SB: number;
  CS: number;
  PA: number;
  TB: number;
  AVG: number;
  OBP: number;
  SLG: number;
  OPS: number;
}

export interface PlayerDetail extends Player {
  stats: PlayerStats[];
}

export interface ScoutingReport {
  player_id: number;
  report: string;
}

