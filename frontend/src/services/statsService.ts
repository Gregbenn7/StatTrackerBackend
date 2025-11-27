/**
 * Statistics-related API service calls.
 */

import { api } from "./api";
import type { LeaderboardEntry } from "@/types";

/**
 * Fetch leaderboard with optional filters.
 */
export const fetchLeaderboard = async (
  league?: string,
  season?: string,
  team?: string
): Promise<LeaderboardEntry[]> => {
  const params = new URLSearchParams();
  if (league) params.append("league", league);
  if (season) params.append("season", season);
  if (team) params.append("team", team);

  const queryString = params.toString();
  return await api.get<LeaderboardEntry[]>(
    `/stats/leaderboard${queryString ? `?${queryString}` : ""}`
  );
};

