/**
 * Game-related API service calls.
 */

import { api } from "./api";
import type { Game, GameDetail, UploadMetadata, UploadResponse, GameStoryline } from "@/types";

/**
 * Upload a CSV file with game stats.
 * Teams are automatically detected from CSV if home_team and away_team are not provided.
 */
export const uploadGameCsv = async (
  file: File,
  metadata: UploadMetadata
): Promise<UploadResponse> => {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("league", metadata.league);
  formData.append("season", metadata.season);
  formData.append("date_str", metadata.date_str);
  // Teams are optional - will be auto-detected if not provided
  if (metadata.home_team) {
    formData.append("home_team", metadata.home_team);
  }
  if (metadata.away_team) {
    formData.append("away_team", metadata.away_team);
  }

  return await api.post<UploadResponse>("/games/upload_csv", formData);
};

/**
 * Fetch games with optional filters.
 */
export const fetchGames = async (
  league?: string,
  season?: string,
  limit: number = 50,
  offset: number = 0
): Promise<Game[]> => {
  const params = new URLSearchParams();
  if (league) params.append("league", league);
  if (season) params.append("season", season);
  params.append("limit", limit.toString());
  params.append("offset", offset.toString());

  return await api.get<Game[]>(`/games?${params.toString()}`);
};

/**
 * Fetch a single game by ID.
 */
export const fetchGame = async (gameId: number): Promise<GameDetail> => {
  return await api.get<GameDetail>(`/games/${gameId}`);
};

/**
 * Fetch storylines for a game.
 */
export const fetchGameStorylines = async (
  gameId: number | string
): Promise<GameStoryline | null> => {
  try {
    const data = await api.get(`/games/${gameId}/storylines`);

    // Transform backend format to frontend format
    const summary = data.summary || {};

    // Extract headline from first key storyline or first sentence of recap
    let headline = "Game Recap";
    if (summary.key_storylines && summary.key_storylines.length > 0) {
      headline = summary.key_storylines[0];
    } else if (summary.recap) {
      const firstSentence = summary.recap.split(/[.!?]/)[0];
      if (firstSentence && firstSentence.trim()) {
        headline = firstSentence.trim();
      }
    }

    return {
      id: String(gameId),
      game_id: String(gameId),
      league_id: "1",
      primary_headline: headline,
      recap_body: summary.recap || "",
      key_moments: Array.isArray(summary.key_storylines)
        ? summary.key_storylines.filter((m: any) => m && m.trim())
        : [],
      player_of_game: summary.player_of_game || "",
      social_captions: Array.isArray(summary.social_captions)
        ? summary.social_captions.filter((c: any) => c && c.trim())
        : [],
      created_at: data.created_at || new Date().toISOString(),
    };
  } catch (error: any) {
    if (error.message.includes("404") || error.message.includes("not found")) {
      return null;
    }
    throw error;
  }
};

/**
 * Create storylines for a game.
 */
export const createGameStorylines = async (
  gameId: number | string
): Promise<GameStoryline> => {
  const data = await api.post(`/games/${gameId}/storylines`);

  // Transform backend format to frontend format
  const summary = data.summary || {};

  let headline = "Game Recap";
  if (summary.key_storylines && summary.key_storylines.length > 0) {
    headline = summary.key_storylines[0];
  } else if (summary.recap) {
    const firstSentence = summary.recap.split(/[.!?]/)[0];
    if (firstSentence && firstSentence.trim()) {
      headline = firstSentence.trim();
    }
  }

  return {
    id: String(gameId),
    game_id: String(gameId),
    league_id: "1",
    primary_headline: headline,
    recap_body: summary.recap || "",
    key_moments: Array.isArray(summary.key_storylines)
      ? summary.key_storylines.filter((m: any) => m && m.trim())
      : [],
    player_of_game: summary.player_of_game || "",
    social_captions: Array.isArray(summary.social_captions)
      ? summary.social_captions.filter((c: any) => c && c.trim())
      : [],
    created_at: data.created_at || new Date().toISOString(),
  };
};

