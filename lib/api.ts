export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

/**
 * Fetch leaderboard data from the backend
 * @param league - Optional league name filter
 * @param season - Optional season name filter
 * @returns Array of leaderboard entries ordered by OPS descending
 */
export async function fetchLeaderboard(league?: string, season?: string) {
  const qs = new URLSearchParams({});
  if (league) qs.append("league", league);
  if (season) qs.append("season", season);

  const res = await fetch(`${API_BASE_URL}/stats/leaderboard?${qs.toString()}`);
  if (!res.ok) throw new Error("Failed to fetch leaderboard");
  return await res.json();
}

/**
 * Fetch players data from the backend
 * @param league - Optional league name filter
 * @param season - Optional season name filter
 * @returns Array of player stats grouped by (team, player_name, league, season)
 */
export async function fetchPlayers(league?: string, season?: string) {
  const qs = new URLSearchParams({});
  if (league) qs.append("league", league);
  if (season) qs.append("season", season);

  const res = await fetch(`${API_BASE_URL}/players?${qs}`);
  if (!res.ok) throw new Error("Failed to fetch players");
  return await res.json();
}

/**
 * Fetch games list from the backend
 * @param league - Optional league name filter
 * @param season - Optional season name filter
 * @returns Array of game basic information
 */
export async function fetchGames(league?: string, season?: string) {
  const qs = new URLSearchParams({});
  if (league) qs.append("league", league);
  if (season) qs.append("season", season);

  const res = await fetch(`${API_BASE_URL}/games?${qs}`);
  if (!res.ok) throw new Error("Failed to fetch games");
  return await res.json();
}

/**
 * Upload a game CSV file to the backend
 * @param formData - FormData containing:
 *   - file: File object (the CSV file)
 *   - league: string
 *   - season: string
 *   - date_str: string (YYYY-MM-DD format)
 *   - home_team: string
 *   - away_team: string
 * @returns Upload response with game_id, rows_ingested, and message
 */
export async function uploadGameCsv(formData: FormData) {
  const res = await fetch(`${API_BASE_URL}/games/upload_csv`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error("CSV upload failed: " + text);
  }

  return await res.json();
}

/**
 * Helper function to create FormData for CSV upload
 * This ensures all required fields match the backend exactly
 */
export function createGameUploadFormData(
  file: File,
  league: string,
  season: string,
  date: string, // YYYY-MM-DD format
  homeTeam: string,
  awayTeam: string
): FormData {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("league", league);
  formData.append("season", season);
  formData.append("date_str", date);
  formData.append("home_team", homeTeam);
  formData.append("away_team", awayTeam);
  return formData;
}

