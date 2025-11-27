/**
 * React Query hooks for game data.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import * as gameService from "@/services/gameService";
import type { UploadMetadata } from "@/types";

/**
 * Fetch games with optional filters.
 */
export const useGames = (league?: string, season?: string, limit: number = 50, offset: number = 0) => {
  return useQuery({
    queryKey: ["games", league, season, limit, offset],
    queryFn: () => gameService.fetchGames(league, season, limit, offset),
  });
};

/**
 * Fetch a single game by ID.
 */
export const useGame = (gameId: number) => {
  return useQuery({
    queryKey: ["game", gameId],
    queryFn: () => gameService.fetchGame(gameId),
    enabled: !!gameId,
  });
};

/**
 * Fetch game storylines.
 */
export const useGameStorylines = (gameId: number | string) => {
  return useQuery({
    queryKey: ["game-storylines", gameId],
    queryFn: () => gameService.fetchGameStorylines(gameId),
    enabled: !!gameId,
  });
};

/**
 * Upload CSV mutation.
 */
export const useUploadGameCsv = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ file, metadata }: { file: File; metadata: UploadMetadata }) =>
      gameService.uploadGameCsv(file, metadata),
    onSuccess: () => {
      // CRITICAL: Invalidate ALL relevant queries to refetch updated data
      queryClient.invalidateQueries({ queryKey: ["games"] });
      queryClient.invalidateQueries({ queryKey: ["leaderboard"] });
      queryClient.invalidateQueries({ queryKey: ["teams"] }); // ADD THIS - fixes team filter not appearing
      queryClient.invalidateQueries({ queryKey: ["players"] });
    },
  });
};

/**
 * Create game storylines mutation.
 */
export const useCreateGameStorylines = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (gameId: number | string) => gameService.createGameStorylines(gameId),
    onSuccess: (_, gameId) => {
      queryClient.invalidateQueries({ queryKey: ["game-storylines", gameId] });
      queryClient.invalidateQueries({ queryKey: ["game", gameId] });
    },
  });
};

