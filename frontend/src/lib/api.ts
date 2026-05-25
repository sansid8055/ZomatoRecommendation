import type {
  AppConfig,
  PreferencesInput,
  RecommendationResponse,
} from "./types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:8000";

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });

  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (body.detail?.message) detail = body.detail.message;
      else if (typeof body.detail === "string") detail = body.detail;
      else if (body.message) detail = body.message;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }

  return res.json() as Promise<T>;
}

export async function getConfig(): Promise<AppConfig> {
  return fetchJson<AppConfig>("/api/config");
}

export async function getLocations(): Promise<string[]> {
  const data = await fetchJson<{ locations: string[] }>("/api/locations");
  return data.locations;
}

export async function postRecommendations(
  prefs: PreferencesInput,
): Promise<RecommendationResponse> {
  return fetchJson<RecommendationResponse>("/api/recommendations", {
    method: "POST",
    body: JSON.stringify({
      ...prefs,
      min_rating: prefs.min_rating && prefs.min_rating > 0 ? prefs.min_rating : null,
      cuisine: prefs.cuisine?.trim() || null,
      additional_preferences: prefs.additional_preferences?.trim() || null,
    }),
  });
}
