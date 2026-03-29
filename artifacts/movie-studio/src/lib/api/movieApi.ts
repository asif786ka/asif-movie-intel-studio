import type { APIResponse, MovieSearchResult, MovieDetails, CompareResponse } from "../types";
import { fetchWithBackoff } from "../../utils/retryWithBackoff";

const BASE = import.meta.env.BASE_URL + "api";

export async function searchMovies(query: string, page = 1): Promise<MovieSearchResult[]> {
  if (!query) return [];
  const res = await fetchWithBackoff(
    `${BASE}/movies/search?query=${encodeURIComponent(query)}&page=${page}`,
    undefined,
    { maxRetries: 4, baseDelay: 3000 }
  );
  if (!res.ok) throw new Error("Search failed");
  const json: APIResponse<MovieSearchResult[]> = await res.json();
  return json.data;
}

export async function getMovieDetails(id: number): Promise<MovieDetails> {
  const res = await fetchWithBackoff(`${BASE}/movies/${id}`, undefined, { maxRetries: 3 });
  if (!res.ok) throw new Error("Failed to fetch movie details");
  const json: APIResponse<MovieDetails> = await res.json();
  return json.data;
}

export async function getMovieBrief(id: number): Promise<unknown> {
  const res = await fetchWithBackoff(`${BASE}/movies/${id}/brief`, undefined, { maxRetries: 3 });
  if (!res.ok) throw new Error("Failed to fetch movie brief");
  const json = await res.json();
  return json.data;
}

export async function compareMovies(
  movieIds: number[],
  dimensions: string[] = ["themes", "critic_reception", "audience_reception", "awards", "timeline", "cast_and_director"]
): Promise<APIResponse<CompareResponse>> {
  const res = await fetchWithBackoff(
    `${BASE}/movies/compare`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ movie_ids: movieIds, dimensions }),
    },
    { maxRetries: 4, baseDelay: 4000 }
  );
  if (!res.ok) throw new Error("Comparison failed");
  return res.json();
}
