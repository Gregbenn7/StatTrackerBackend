/**
 * React Query hooks for statistics data.
 */

import { useQuery } from "@tanstack/react-query";
import * as statsService from "@/services/statsService";

/**
 * Fetch leaderboard with optional filters.
 */
export const useLeaderboard = (league?: string, season?: string, team?: string | null) => {
  return useQuery({
    queryKey: ["leaderboard", league, season, team || null],
    queryFn: () => statsService.fetchLeaderboard(league, season, team || undefined),
  });
};

