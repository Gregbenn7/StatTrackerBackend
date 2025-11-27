/**
 * Player-related API service calls.
 */

import { api } from "./api";
import type { Player, PlayerDetail, PlayerStats, ScoutingReport } from "@/types";

/**
 * Fetch all players with optional filters.
 */
export const fetchPlayers = async (
  league?: string,
  season?: string,
  team?: string
): Promise<PlayerStats[]> => {
  const params = new URLSearchParams();
  if (league) params.append("league", league);
  if (season) params.append("season", season);
  if (team) params.append("team", team);

  const queryString = params.toString();
  return await api.get<PlayerStats[]>(`/players${queryString ? `?${queryString}` : ""}`);
};

/**
 * Fetch a single player by ID.
 */
export const fetchPlayer = async (playerId: number): Promise<PlayerDetail> => {
  return await api.get<PlayerDetail>(`/players/${playerId}`);
};

/**
 * Fetch scouting report for a player.
 */
export const fetchPlayerScoutingReport = async (playerId: number): Promise<ScoutingReport> => {
  return await api.get<ScoutingReport>(`/players/${playerId}/scouting_report`);
};

