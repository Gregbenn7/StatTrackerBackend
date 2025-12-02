/**
 * React Query hooks for player data.
 */

import { useQuery } from "@tanstack/react-query";
import * as playerService from "@/services/playerService";

/**
 * Fetch players with optional filters.
 */
export const usePlayers = (league?: string, season?: string, team?: string) => {
  return useQuery({
    queryKey: ["players", league, season, team],
    queryFn: () => playerService.fetchPlayers(league, season, team),
  });
};

/**
 * Fetch a single player by ID.
 */
export const usePlayer = (playerId: number) => {
  return useQuery({
    queryKey: ["player", playerId],
    queryFn: () => playerService.fetchPlayer(playerId),
    enabled: !!playerId,
  });
};

/**
 * Fetch player scouting report.
 */
export const usePlayerScoutingReport = (playerId: number) => {
  return useQuery({
    queryKey: ["player-scouting-report", playerId],
    queryFn: () => playerService.fetchPlayerScoutingReport(playerId),
    enabled: !!playerId,
  });
};

