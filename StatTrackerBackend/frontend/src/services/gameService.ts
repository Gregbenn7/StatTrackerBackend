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
 * Check if storyline exists for a game.
 */
export const checkStorylineExists = async (
  gameId: number | string
): Promise<boolean> => {
  try {
    const response = await api.get<{ exists: boolean; game_id: string }>(
      `/storylines/games/${gameId}/exists`
    );
    return response.exists;
  } catch (error: any) {
    console.error("Error checking storyline exists:", error);
    return false;
  }
};

/**
 * Fetch storylines for a game.
 */
export const fetchGameStorylines = async (
  gameId: number | string
): Promise<GameStoryline | null> => {
  try {
    const data = await api.get(`/storylines/games/${gameId}`);

    // Backend returns new GameStoryline format with: headline, recap, key_players, game_summary, generated_at
    // Transform to frontend format
    const keyPlayers = Array.isArray(data.key_players) ? data.key_players : [];
    
    // Extract key moments from recap (first few sentences or bullet points)
    let keyMoments: string[] = [];
    if (data.recap) {
      // Try to extract bullet points or numbered items
      const lines = data.recap.split('\n');
      const bulletLines = lines
        .filter(line => line.trim().match(/^[-*•]\s+|^\d+[.)]\s+/))
        .map(line => line.replace(/^[-*•]\s+|^\d+[.)]\s+/, '').trim())
        .filter(line => line.length > 10);
      
      if (bulletLines.length > 0) {
        keyMoments = bulletLines.slice(0, 4);
      } else {
        // Fallback: use first few sentences
        const sentences = data.recap.split(/[.!?]+/).filter(s => s.trim().length > 20);
        keyMoments = sentences.slice(1, 4); // Skip first sentence (usually in headline)
      }
    }
    
    // If no moments extracted, use player names as fallback
    if (keyMoments.length === 0 && keyPlayers.length > 0) {
      keyMoments = keyPlayers.slice(0, 3).map(p => `${p} delivered a strong performance`);
    }
    
    return {
      id: data.id || String(gameId),
      game_id: data.game_id || String(gameId),
      league_id: "1",
      primary_headline: data.headline || "Game Recap",
      recap_body: data.recap || "",
      key_moments: keyMoments,
      player_of_game: keyPlayers.length > 0
        ? `${keyPlayers[0]} was the standout player`
        : "",
      social_captions: data.headline
        ? [
            data.headline.substring(0, 120),
            data.game_summary ? data.game_summary.substring(0, 120) : "",
            keyPlayers.length > 0 ? `${keyPlayers[0]} leads ${data.game_summary || 'team to victory'}`.substring(0, 120) : ""
          ].filter(c => c)
        : [],
      created_at: data.generated_at || new Date().toISOString(),
    };
  } catch (error: any) {
    if (error.message.includes("404") || error.message.includes("not found")) {
      return null;
    }
    throw error;
  }
};

/**
 * Generate storylines for a game.
 */
export const generateGameStoryline = async (
  gameId: number | string
): Promise<GameStoryline> => {
  const data = await api.post(`/storylines/games/${gameId}/generate`);

  // Backend returns new GameStoryline format
  // Transform to frontend format (same as fetchGameStorylines)
  const keyPlayers = Array.isArray(data.key_players) ? data.key_players : [];
  
  let keyMoments: string[] = [];
  if (data.recap) {
    const lines = data.recap.split('\n');
    const bulletLines = lines
      .filter(line => line.trim().match(/^[-*•]\s+|^\d+[.)]\s+/))
      .map(line => line.replace(/^[-*•]\s+|^\d+[.)]\s+/, '').trim())
      .filter(line => line.length > 10);
    
    if (bulletLines.length > 0) {
      keyMoments = bulletLines.slice(0, 4);
    } else {
      const sentences = data.recap.split(/[.!?]+/).filter(s => s.trim().length > 20);
      keyMoments = sentences.slice(1, 4);
    }
  }
  
  if (keyMoments.length === 0 && keyPlayers.length > 0) {
    keyMoments = keyPlayers.slice(0, 3).map(p => `${p} delivered a strong performance`);
  }
  
  return {
    id: data.id || String(gameId),
    game_id: data.game_id || String(gameId),
    league_id: "1",
    primary_headline: data.headline || "Game Recap",
    recap_body: data.recap || "",
    key_moments: keyMoments,
    player_of_game: keyPlayers.length > 0
      ? `${keyPlayers[0]} was the standout player`
      : "",
    social_captions: data.headline
      ? [
          data.headline.substring(0, 120),
          data.game_summary ? data.game_summary.substring(0, 120) : "",
          keyPlayers.length > 0 ? `${keyPlayers[0]} leads ${data.game_summary || 'team to victory'}`.substring(0, 120) : ""
        ].filter(c => c)
      : [],
    created_at: data.generated_at || new Date().toISOString(),
  };
};

