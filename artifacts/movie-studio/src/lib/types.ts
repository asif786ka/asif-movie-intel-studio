export interface APIResponse<T> {
  success: boolean;
  data: T;
  trace_id?: string;
  latency_ms?: number;
  route_type?: string;
  error?: string;
}

export interface MovieSearchResult {
  id: number;
  title: string;
  overview: string;
  release_date: string;
  vote_average: number;
  vote_count: number;
  poster_path: string | null;
  genre_ids: number[];
}

export interface MovieDetails {
  id: number;
  title: string;
  overview: string;
  release_date: string;
  vote_average: number;
  genres: { id: number; name: string }[];
  runtime: number;
  budget: number;
  revenue: number;
  tagline: string;
  poster_path: string | null;
}

export interface MovieBrief {
  id: number;
  title: string;
  year: string;
  rating: number;
  genres: string[];
  director: string;
  poster_url: string | null;
}

export interface CitationRef {
  source: string;
  chunk_id?: string;
  score?: number;
}

export interface ComparisonSection {
  dimension: string;
  content: string;
  citations: CitationRef[];
}

export interface CompareResponse {
  movies: MovieBrief[];
  summary: string;
  themes?: ComparisonSection;
  critic_reception?: ComparisonSection;
  audience_reception?: ComparisonSection;
  awards?: ComparisonSection;
  timeline?: ComparisonSection;
  cast_and_director?: ComparisonSection;
  sections: ComparisonSection[];
  confidence: number;
}

export interface Citation {
  chunk_text: string;
  metadata: Record<string, string | number | boolean | null>;
  score?: number;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  traceId?: string;
  latency?: number;
  queryType?: string;
  routeType?: string;
}

export interface EvalMetric {
  name: string;
  value: number;
  description: string;
  threshold: number | null;
  passed: boolean | null;
}

export interface EvalRun {
  run_id: string;
  timestamp: string;
  metrics: EvalMetric[];
  total_queries: number;
  passed: number;
  failed: number;
  dataset_name: string;
  adversarial_results?: AdversarialResult[];
}

export interface AdversarialResult {
  prompt: string;
  expected_behavior: string;
  actual_behavior: string;
  passed: boolean;
}

export interface TraceSummary {
  trace_id: string;
  query: string;
  route_type: string;
  latency_ms: number;
  timestamp: string;
  citation_count: number;
}

export interface AdminMetrics {
  total_queries: number;
  total_chunks: number;
  avg_citation_count: number;
  citation_rate: number;
  refusal_rate: number;
  unsupported_claim_rate: number;
  p95_latency_ms: number;
  route_distribution: {
    structured_only: number;
    rag_only: number;
    hybrid: number;
  };
  prompt_versions: Record<string, string> | { prompts: Record<string, string>; pipeline: Record<string, string> };
  recent_traces?: TraceSummary[];
  last_eval_run?: EvalRun | null;
}
