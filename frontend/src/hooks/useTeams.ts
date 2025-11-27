/**
 * React Query hooks for team data.
 */

import { useQuery } from "@tanstack/react-query";
import * as teamService from "@/services/teamService";

/**
 * Fetch teams with optional league and season filters.
 */
export const useTeams = (league?: string, season?: string) => {
  return useQuery({
    queryKey: ["teams", league, season],
    queryFn: () => teamService.getTeams(league, season),
  });
};

/**
 * @deprecated Use useTeams which now returns TeamStats[]
 * Fetch teams as string array (legacy).
 */
export const useTeamNames = (league?: string) => {
  return useQuery({
    queryKey: ["teamNames", league],
    queryFn: () => teamService.fetchTeams(league),
  });
};

