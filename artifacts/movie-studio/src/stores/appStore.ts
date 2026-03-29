import { create } from "zustand";
import type { ChatMessage, MovieSearchResult } from "../lib/types";

interface ChatState {
  messages: ChatMessage[];
  sessionId: string | undefined;
  isStreaming: boolean;
  addMessage: (msg: ChatMessage) => void;
  updateMessage: (id: string, updates: Partial<ChatMessage>) => void;
  setSessionId: (id: string) => void;
  setStreaming: (streaming: boolean) => void;
  clearMessages: () => void;
}

interface SearchState {
  query: string;
  results: MovieSearchResult[];
  selectedMovieId: number | null;
  setQuery: (q: string) => void;
  setResults: (results: MovieSearchResult[]) => void;
  setSelectedMovieId: (id: number | null) => void;
}

interface UploadState {
  file: File | null;
  metadata: {
    movie_title: string;
    source_type: string;
    director: string;
    release_year: string;
    franchise: string;
  };
  uploadHistory: Array<{
    filename: string;
    chunk_count: number;
    status: string;
    timestamp: number;
  }>;
  setFile: (file: File | null) => void;
  setMetadata: (metadata: Partial<UploadState["metadata"]>) => void;
  resetMetadata: () => void;
  addToHistory: (entry: UploadState["uploadHistory"][0]) => void;
}

interface CompareState {
  selectedMovies: MovieSearchResult[];
  addMovie: (movie: MovieSearchResult) => void;
  removeMovie: (id: number) => void;
  clearMovies: () => void;
}

const defaultMetadata: UploadState["metadata"] = {
  movie_title: "",
  source_type: "document",
  director: "",
  release_year: "",
  franchise: "",
};

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  sessionId: undefined,
  isStreaming: false,
  addMessage: (msg) => set((s) => ({ messages: [...s.messages, msg] })),
  updateMessage: (id, updates) =>
    set((s) => ({
      messages: s.messages.map((m) => (m.id === id ? { ...m, ...updates } : m)),
    })),
  setSessionId: (id) => set({ sessionId: id }),
  setStreaming: (streaming) => set({ isStreaming: streaming }),
  clearMessages: () => set({ messages: [], sessionId: undefined }),
}));

export const useSearchStore = create<SearchState>((set) => ({
  query: "",
  results: [],
  selectedMovieId: null,
  setQuery: (q) => set({ query: q }),
  setResults: (results) => set({ results }),
  setSelectedMovieId: (id) => set({ selectedMovieId: id }),
}));

export const useUploadStore = create<UploadState>((set) => ({
  file: null,
  metadata: { ...defaultMetadata },
  uploadHistory: [],
  setFile: (file) => set({ file }),
  setMetadata: (updates) =>
    set((s) => ({ metadata: { ...s.metadata, ...updates } })),
  resetMetadata: () => set({ metadata: { ...defaultMetadata }, file: null }),
  addToHistory: (entry) =>
    set((s) => ({ uploadHistory: [entry, ...s.uploadHistory] })),
}));

export const useCompareStore = create<CompareState>((set) => ({
  selectedMovies: [],
  addMovie: (movie) =>
    set((s) => {
      if (s.selectedMovies.length >= 5) return s;
      if (s.selectedMovies.find((m) => m.id === movie.id)) return s;
      return { selectedMovies: [...s.selectedMovies, movie] };
    }),
  removeMovie: (id) =>
    set((s) => ({
      selectedMovies: s.selectedMovies.filter((m) => m.id !== id),
    })),
  clearMovies: () => set({ selectedMovies: [] }),
}));
