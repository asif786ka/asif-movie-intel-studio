/**
 * Movie Search & Data Hooks — React hooks for TMDB movie operations.
 *
 * Architecture Note (Senior AI Architect):
 *   These hooks abstract all movie-related API interactions:
 *
 *   useMovieSearch: Debounced search with built-in 300ms delay.
 *     - Prevents API spam on rapid keystrokes
 *     - Uses useRef for timer cleanup (no memory leaks)
 *     - TanStack Query caches results by [endpoint, query] key
 *
 *   useSearchMovies: Direct paginated search (no debounce).
 *     - Used when user explicitly triggers search (e.g., Enter key)
 *     - Supports pagination via page parameter
 *
 *   useMovieDetails: Fetch full movie details by TMDB ID.
 *     - enabled: !!id prevents fetching with null/undefined ID
 *     - Results cached by movie ID for instant re-renders
 *
 *   useCompareMovies: Mutation for multi-movie comparison.
 *     - Uses useMutation (not useQuery) because it's a POST
 *     - Sends array of movie IDs to /api/movies/compare
 *
 *   Data Flow:
 *     Component → useMovieSearch(query) → movieApi.searchMovies()
 *       → fetch(/api/movies/search?query=X)
 *       → Express proxy → Python FastAPI → TMDB API / Seed Data
 */

import { useState, useEffect, useRef } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { movieApi } from "../lib/api";

export function useMovieSearch(initialQuery = "", debounceMs = 300) {
  const [query, setQuery] = useState(initialQuery);
  const [debouncedQuery, setDebouncedQuery] = useState(initialQuery);
  const timerRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  useEffect(() => {
    timerRef.current = setTimeout(() => {
      setDebouncedQuery(query);
    }, debounceMs);
    return () => clearTimeout(timerRef.current);
  }, [query, debounceMs]);

  const result = useQuery({
    queryKey: ["/api/movies/search", debouncedQuery],
    queryFn: () => movieApi.searchMovies(debouncedQuery),
    enabled: !!debouncedQuery,
  });

  return { query, setQuery, debouncedQuery, ...result };
}

export function useSearchMovies(query: string, page = 1) {
  return useQuery({
    queryKey: ["/api/movies/search", query, page],
    queryFn: () => movieApi.searchMovies(query, page),
    enabled: !!query,
  });
}

export function useMovieDetails(id: number | null) {
  return useQuery({
    queryKey: ["/api/movies", id],
    queryFn: () => movieApi.getMovieDetails(id!),
    enabled: !!id,
  });
}

export function useCompareMovies() {
  return useMutation({
    mutationFn: (movieIds: number[]) => movieApi.compareMovies(movieIds),
  });
}
