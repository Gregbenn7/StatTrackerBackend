/**
 * Team-related API service calls.
 */

import { api } from "./api";
import type { TeamStats } from "@/types/team.types";

/**
 * Get all teams with optional filters.
 */
export const getTeams = async (league?: string, season?: string): Promise<TeamStats[]> => {
  const params = new URLSearchParams();
  if (league) params.append("league", league);
  if (season) params.append("season", season);

  return await api.get<TeamStats[]>(`/teams?${params.toString()}`);
};

/**
 * Get stats for a specific team.
 */
export const getTeamStats = async (
  teamName: string,
  league: string,
  season: string
): Promise<TeamStats> => {
  const params = new URLSearchParams();
  params.append("league", league);
  params.append("season", season);
  
  return await api.get<TeamStats>(`/teams/${encodeURIComponent(teamName)}/stats?${params.toString()}`);
};

/**
 * Get roster for a specific team.
 */
export const getTeamRoster = async (
  teamName: string,
  league?: string,
  season?: string
): Promise<any[]> => {
  const params = new URLSearchParams();
  if (league) params.append("league", league);
  if (season) params.append("season", season);

  return await api.get<any[]>(`/teams/${encodeURIComponent(teamName)}/roster?${params.toString()}`);
};

/**
 * Get all games for a specific team.
 */
export const getTeamGames = async (
  teamName: string,
  league?: string,
  season?: string
): Promise<any[]> => {
  const params = new URLSearchParams();
  if (league) params.append("league", league);
  if (season) params.append("season", season);

  return await api.get<any[]>(`/teams/${encodeURIComponent(teamName)}/games?${params.toString()}`);
};

/**
 * @deprecated Use getTeams instead
 * Fetch unique teams, optionally filtered by league.
 */
export const fetchTeams = async (league?: string): Promise<string[]> => {
  const params = new URLSearchParams();
  if (league) params.append("league", league);

  const queryString = params.toString();
  const data = await api.get<{ teams: string[] }>(`/teams${queryString ? `?${queryString}` : ""}`);
  return data.teams || [];
};
