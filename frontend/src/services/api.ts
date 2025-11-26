const API_BASE_URL =
  import.meta.env.VITE_NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

export interface PlayerStats {
  player_name: string;
  team_name: string;
  games_played: number;
  ab: number;
  h: number;
  avg: number;
  hr: number;
  rbi: number;
  obp: number;
  slg: number;
  ops: number;
  doubles?: number;
  triples?: number;
  bb?: number;
  k?: number;
  r?: number;
  sb?: number;
}

export interface UploadMetadata {
  league: string;
  season: string;
  date_str: string; // YYYY-MM-DD format
  home_team: string;
  away_team: string;
}

export const uploadCSV = async (
  file: File,
  metadata: UploadMetadata
): Promise<{ game_id: number; rows_ingested: number; message: string }> => {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("league", metadata.league);
  formData.append("season", metadata.season);
  formData.append("date_str", metadata.date_str);
  formData.append("home_team", metadata.home_team);
  formData.append("away_team", metadata.away_team);

  const response = await fetch(`${API_BASE_URL}/games/upload_csv`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const errorText = await response.text();
    let errorMessage = "Upload failed";
    try {
      const errorJson = JSON.parse(errorText);
      errorMessage = errorJson.detail || errorMessage;
    } catch {
      errorMessage = errorText || errorMessage;
    }
    throw new Error(errorMessage);
  }

  return response.json();
};

export const getTotals = async (league?: string, season?: string): Promise<PlayerStats[]> => {
  const params = new URLSearchParams();
  if (league) params.append("league", league);
  if (season) params.append("season", season);
  
  const queryString = params.toString();
  const url = `${API_BASE_URL}/stats/leaderboard${queryString ? `?${queryString}` : ""}`;
  
  const response = await fetch(url, {
    method: "GET",
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(error || "Failed to fetch totals");
  }

  // Transform backend format to frontend format
  const leaderboardEntries = await response.json();
  return leaderboardEntries.map((entry: any) => ({
    player_name: entry.player_name,
    team_name: entry.team,
    games_played: entry.games,
    ab: entry.AB,
    h: entry.H,
    avg: entry.AVG,
    hr: entry.HR,
    rbi: entry.RBI,
    obp: entry.OBP,
    slg: entry.SLG,
    ops: entry.OPS,
  }));
};

export async function uploadGameCsv(formData: FormData) {
  const res = await fetch(`${API_BASE_URL}/games/upload_csv`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    throw new Error(`Upload failed: ${res.status}`);
  }
  return res.json(); // { game_id, rows_ingested, message }
}

export async function fetchPlayers(league: string, season: string) {
  const params = new URLSearchParams({ league, season });
  const res = await fetch(`${API_BASE_URL}/players?` + params.toString());

  if (!res.ok) {
    throw new Error(`Fetch players failed: ${res.status}`);
  }
  return res.json(); // array of players + stats
}

export async function fetchLeaderboard(league?: string, season?: string) {
  const params = new URLSearchParams();
  if (league) params.append("league", league);
  if (season) params.append("season", season);
  
  const queryString = params.toString();
  const url = `${API_BASE_URL}/stats/leaderboard${queryString ? `?${queryString}` : ""}`;
  const res = await fetch(url);

  if (!res.ok) {
    throw new Error(`Fetch leaderboard failed: ${res.status}`);
  }
  return res.json();
}

export async function fetchTeams(league?: string): Promise<string[]> {
  const params = new URLSearchParams();
  if (league) params.append("league", league);
  
  const queryString = params.toString();
  const url = `${API_BASE_URL}/teams${queryString ? `?${queryString}` : ""}`;
  const res = await fetch(url);

  if (!res.ok) {
    throw new Error(`Fetch teams failed: ${res.status}`);
  }
  const data = await res.json();
  return data.teams || [];
}

export async function fetchGames(league?: string, season?: string) {
  const params = new URLSearchParams();
  if (league) params.append("league", league);
  if (season) params.append("season", season);
  
  const queryString = params.toString();
  const url = `${API_BASE_URL}/games${queryString ? `?${queryString}` : ""}`;
  const res = await fetch(url);

  if (!res.ok) {
    throw new Error(`Fetch games failed: ${res.status}`);
  }
  return res.json();
}

export async function fetchGameStorylines(gameId: number | string) {
  const res = await fetch(`${API_BASE_URL}/games/${gameId}/storylines`);
  
  if (!res.ok) {
    if (res.status === 404) {
      return null; // Storylines don't exist yet
    }
    const errorText = await res.text();
    throw new Error(`Fetch game storylines failed: ${res.status} - ${errorText}`);
  }
  const data = await res.json();
  
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
    league_id: "1", // Not in backend response, using placeholder
    primary_headline: headline,
    recap_body: summary.recap || "",
    key_moments: Array.isArray(summary.key_storylines) ? summary.key_storylines.filter((m: any) => m && m.trim()) : [],
    player_of_game: summary.player_of_game || "",
    social_captions: Array.isArray(summary.social_captions) ? summary.social_captions.filter((c: any) => c && c.trim()) : [],
    created_at: data.created_at || new Date().toISOString(),
  };
}

export async function createGameStorylines(gameId: number | string) {
  const res = await fetch(`${API_BASE_URL}/games/${gameId}/storylines`, {
    method: "POST",
  });
  
  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`Create game storylines failed: ${res.status} - ${errorText}`);
  }
  const data = await res.json();
  
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
    key_moments: Array.isArray(summary.key_storylines) ? summary.key_storylines.filter((m: any) => m && m.trim()) : [],
    player_of_game: summary.player_of_game || "",
    social_captions: Array.isArray(summary.social_captions) ? summary.social_captions.filter((c: any) => c && c.trim()) : [],
    created_at: data.created_at || new Date().toISOString(),
  };
}
