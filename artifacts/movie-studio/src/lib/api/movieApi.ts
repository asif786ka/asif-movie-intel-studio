import type { APIResponse, MovieSearchResult, MovieDetails, CompareResponse } from "../types";

const BASE = import.meta.env.BASE_URL + "api";

async function fetchWithRetry(url: string, options?: RequestInit, retries = 3): Promise<Response> {
  for (let i = 0; i <= retries; i++) {
    const res = await fetch(url, options);
    if (res.status === 503 && i < retries) {
      await new Promise((r) => setTimeout(r, 5000));
      continue;
    }
    return res;
  }
  return fetch(url, options);
}

export async function searchMovies(query: string, page = 1): Promise<MovieSearchResult[]> {
  if (!query) return [];
  const res = await fetchWithRetry(`${BASE}/movies/search?query=${encodeURIComponent(query)}&page=${page}`);
  if (!res.ok) throw new Error("Search failed");
  const json: APIResponse<MovieSearchResult[]> = await res.json();
  return json.data;
}

export async function getMovieDetails(id: number): Promise<MovieDetails> {
  const res = await fetch(`${BASE}/movies/${id}`);
  if (!res.ok) throw new Error("Failed to fetch movie details");
  const json: APIResponse<MovieDetails> = await res.json();
  return json.data;
}

export async function getMovieBrief(id: number): Promise<unknown> {
  const res = await fetch(`${BASE}/movies/${id}/brief`);
  if (!res.ok) throw new Error("Failed to fetch movie brief");
  const json = await res.json();
  return json.data;
}

export async function compareMovies(
  movieIds: number[],
  dimensions: string[] = ["themes", "critic_reception", "audience_reception", "awards", "timeline", "cast_and_director"]
): Promise<APIResponse<CompareResponse>> {
  const res = await fetch(`${BASE}/movies/compare`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ movie_ids: movieIds, dimensions }),
  });
  if (!res.ok) throw new Error("Comparison failed");
  return res.json();
}
