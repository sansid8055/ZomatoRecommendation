"use client";

import { useCallback, useEffect, useState } from "react";
import { getConfig, getLocations, postRecommendations } from "@/lib/api";
import type {
  AppConfig,
  AppView,
  PreferencesInput,
  RecommendationResponse,
} from "@/lib/types";
import { EmptyState } from "./EmptyState";
import { Header } from "./Header";
import { Icon } from "./Icon";
import { LoadingScreen } from "./LoadingScreen";
import { PreferenceForm } from "./PreferenceForm";
import { ResultsSection } from "./ResultsSection";
import { SetupSidebar } from "./SetupSidebar";

const DEFAULT_PREFS: PreferencesInput = {
  location: "Bangalore",
  budget: "medium",
  cuisine: "",
  min_rating: 4,
  additional_preferences: "",
};

export function HomePage() {
  const [view, setView] = useState<AppView>("form");
  const [prefs, setPrefs] = useState<PreferencesInput>(DEFAULT_PREFS);
  const [locations, setLocations] = useState<string[]>([]);
  const [config, setConfig] = useState<AppConfig | null>(null);
  const [response, setResponse] = useState<RecommendationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([getConfig(), getLocations()])
      .then(([cfg, locs]) => {
        setConfig(cfg);
        setLocations(locs);
        if (locs.includes("Bangalore")) {
          setPrefs((p) => ({ ...p, location: "Bangalore" }));
        } else if (locs[0]) {
          setPrefs((p) => ({ ...p, location: locs[0] }));
        }
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load app"));
  }, []);

  const handleSubmit = useCallback(async () => {
    setError(null);
    if (!config?.api_key_configured) {
      setError("GROQ_API_KEY is not set. Add it to .env in the project root.");
      return;
    }
    if (!config?.dataset_ready) {
      setError("Dataset not found. Run: python scripts/download_dataset.py");
      return;
    }

    setView("loading");
    try {
      const result = await postRecommendations(prefs);
      setResponse(result);
      if (result.recommendations.length === 0) {
        setView("empty");
      } else {
        setView("results");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed");
      setView("error");
    }
  }, [config, prefs]);

  const handleRefine = () => {
    setResponse(null);
    setError(null);
    setView("form");
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const showForm = view === "form" || view === "error";
  const showStickyCta = showForm;

  return (
    <>
      <Header />

      <main className="mx-auto max-w-content px-margin-mobile pb-32 pt-20 md:px-margin-desktop md:pb-24">
        {view === "loading" && <LoadingScreen />}

        {showForm && (
          <>
            <section className="mb-8 text-center md:text-left">
              <h1 className="font-display text-3xl font-bold text-on-background md:text-4xl">
                Personalized picks from real Zomato data
              </h1>
              <p className="mt-2 max-w-2xl text-on-surface-variant">
                Filtered locally from 51k+ restaurants, ranked and explained by Groq AI.
              </p>
            </section>

            {error && (
              <div
                role="alert"
                className="mb-6 flex items-start gap-3 rounded-xl border border-error/30 bg-error-container p-4 text-on-error-container"
              >
                <Icon name="error" className="shrink-0" />
                <p className="text-sm">{error}</p>
              </div>
            )}

            {!response && view === "form" && (
              <div className="mb-6 flex items-start gap-3 rounded-xl border border-secondary/20 bg-secondary-container/10 p-4">
                <Icon name="info" className="shrink-0 text-secondary" />
                <p className="text-sm text-on-surface">
                  Select your preferences and click <strong>Get recommendations</strong> to
                  see personalized cards with AI explanations.
                </p>
              </div>
            )}

            <div className="flex flex-col gap-6 lg:flex-row lg:gap-8">
              <SetupSidebar config={config} />
              <section className="min-w-0 flex-1">
                <PreferenceForm
                  locations={locations}
                  value={prefs}
                  onChange={setPrefs}
                  disabled={false}
                />
              </section>
            </div>
          </>
        )}

        {view === "results" && response && (
          <div className="flex flex-col gap-8 lg:flex-row">
            <SetupSidebar config={config} showRefine onRefine={handleRefine} />
            <div className="min-w-0 flex-1">
              <ResultsSection response={response} />
            </div>
          </div>
        )}

        {view === "empty" && response && (
          <div className="flex flex-col gap-8 lg:flex-row">
            <SetupSidebar config={config} showRefine onRefine={handleRefine} />
            <div className="min-w-0 flex-1">
              <EmptyState
                message={response.message ?? undefined}
                suggestions={response.suggestions}
                onReset={handleRefine}
              />
            </div>
          </div>
        )}
      </main>

      {showStickyCta && (
        <div className="fixed bottom-0 left-0 z-50 w-full border-t border-outline-variant/20 bg-surface px-margin-mobile py-4 shadow-footer">
          <div className="mx-auto max-w-content">
            <button
              type="button"
              onClick={handleSubmit}
              className="flex w-full items-center justify-center gap-3 rounded-xl bg-primary py-4 font-display text-lg font-semibold text-on-primary shadow-lg transition hover:bg-primary-container active:scale-[0.98]"
            >
              <Icon name="auto_awesome" filled />
              Get recommendations
            </button>
          </div>
        </div>
      )}
    </>
  );
}
