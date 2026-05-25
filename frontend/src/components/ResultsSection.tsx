import type { RecommendationResponse } from "@/lib/types";
import { Icon } from "./Icon";
import { RecommendationCard } from "./RecommendationCard";

export function ResultsSection({ response }: { response: RecommendationResponse }) {
  const { recommendations, summary, metadata, message } = response;
  const count = recommendations.length;

  return (
    <section className="space-y-6">
      <div>
        <h2 className="font-display text-2xl font-bold text-on-surface md:text-3xl">
          Your recommendations
        </h2>
        <p className="mt-1 flex items-center gap-1 text-sm text-on-surface-variant">
          <Icon name="travel_explore" size={16} />
          {count} recommendation{count !== 1 ? "s" : ""} (from {metadata.total_matched}{" "}
          matches, {metadata.candidate_count} sent to AI)
        </p>
      </div>

      {metadata.degraded_mode && (
        <div className="flex items-start gap-3 rounded-xl border border-secondary/20 bg-secondary-container/10 p-4">
          <Icon name="info" className="shrink-0 text-secondary" />
          <p className="text-sm text-on-surface">
            {message ?? "Showing top-rated matches (AI ranking unavailable)."}
          </p>
        </div>
      )}

      {summary && (
        <div className="ai-shimmer rounded-2xl border border-primary/20 bg-surface-container-low p-4">
          <div className="flex items-start gap-4">
            <div className="shrink-0 rounded-lg bg-primary-container p-2 text-on-primary">
              <Icon name="auto_awesome" filled />
            </div>
            <p className="text-sm leading-relaxed text-on-surface">{summary}</p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 gap-6">
        {recommendations.map((rec) => (
          <RecommendationCard key={rec.restaurant_id} rec={rec} />
        ))}
      </div>
    </section>
  );
}
