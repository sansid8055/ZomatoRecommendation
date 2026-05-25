export type BudgetTier = "low" | "medium" | "high";

export interface PreferencesInput {
  location: string;
  budget: BudgetTier;
  cuisine?: string;
  min_rating?: number;
  additional_preferences?: string;
}

export interface RankedRecommendation {
  rank: number;
  restaurant_id: string;
  name: string;
  cuisine: string;
  rating: number | null;
  approx_cost: number | null;
  location: string;
  locality: string | null;
  explanation: string;
}

export interface ResponseMetadata {
  candidate_count: number;
  total_matched: number;
  filters_applied: Record<string, unknown>;
  filter_duration_ms?: number | null;
  llm_duration_ms?: number | null;
  degraded_mode: boolean;
}

export interface RecommendationResponse {
  success: boolean;
  summary: string | null;
  recommendations: RankedRecommendation[];
  metadata: ResponseMetadata;
  message: string | null;
  suggestions: string[];
}

export interface AppConfig {
  api_key_configured: boolean;
  dataset_ready: boolean;
  llm_provider: string;
  llm_model: string;
  top_k_results: number;
  max_candidates: number;
}

export type AppView = "form" | "loading" | "results" | "empty" | "error";
