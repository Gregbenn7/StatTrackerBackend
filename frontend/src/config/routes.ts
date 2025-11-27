/**
 * Route constants for the application.
 */

export const routes = {
  home: "/",
  dashboard: "/dashboard",
  leaderboard: "/leaderboard",
  games: "/games",
  players: "/players",
  upload: "/upload",
} as const;

export type Route = typeof routes[keyof typeof routes];

