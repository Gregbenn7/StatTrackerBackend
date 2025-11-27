/**
 * Statistics-related TypeScript types.
 */

export interface LeaderboardEntry {
  player_id: number;
  player_name: string;
  team: string;
  games: number;
  AB: number;
  H: number;
  HR: number;
  RBI: number;
  AVG: number;
  OBP: number;
  SLG: number;
  OPS: number;
}

