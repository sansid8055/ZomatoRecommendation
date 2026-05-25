"use client";

import { useState } from "react";
import type { RankedRecommendation } from "@/lib/types";
import { Icon } from "./Icon";

function formatCost(cost: number | null): string {
  if (cost == null) return "Cost N/A";
  return `₹${cost.toLocaleString("en-IN")} for two`;
}

function formatRating(rating: number | null): string {
  if (rating == null) return "N/A";
  return rating.toFixed(1);
}

const PLACEHOLDER_GRADIENTS = [
  "from-primary/20 via-primary-container/30 to-secondary/20",
  "from-secondary/20 via-tertiary/20 to-primary/10",
  "from-tertiary/30 via-primary-fixed/20 to-surface-container",
];

export function RecommendationCard({ rec }: { rec: RankedRecommendation }) {
  const [expanded, setExpanded] = useState(rec.rank === 1);
  const gradient = PLACEHOLDER_GRADIENTS[(rec.rank - 1) % PLACEHOLDER_GRADIENTS.length];
  const locality = rec.locality ? ` · ${rec.locality}` : "";

  return (
    <article className="group flex flex-col overflow-hidden rounded-2xl border border-outline-variant/30 bg-surface-container-lowest shadow-card transition hover:shadow-card-hover md:flex-row">
      <div
        className={`relative flex h-40 w-full shrink-0 items-center justify-center bg-gradient-to-br md:h-auto md:w-1/3 ${gradient}`}
      >
        <Icon name="restaurant" className="text-primary/40" size={64} />
        <div className="absolute left-3 top-3 flex items-center gap-1 rounded-full bg-primary px-3 py-1 text-xs font-semibold text-on-primary shadow-lg">
          <Icon name="workspace_premium" size={14} filled />
          #{rec.rank} Recommendation
        </div>
        {rec.rank === 1 && (
          <div className="absolute bottom-3 right-3 rounded-lg bg-white/80 px-2 py-1 text-xs font-bold text-primary backdrop-blur-sm">
            Top pick
          </div>
        )}
      </div>

      <div className="flex flex-1 flex-col justify-between p-4 md:p-6">
        <div>
          <div className="mb-1 flex items-start justify-between gap-2">
            <h3 className="font-display text-xl font-bold text-on-surface line-clamp-2">
              {rec.name}
            </h3>
            <div className="flex shrink-0 items-center gap-1 rounded-lg bg-surface-container-high px-2 py-1">
              <Icon name="star" className="text-amber-500" size={18} filled />
              <span className="text-sm font-bold">{formatRating(rec.rating)}</span>
            </div>
          </div>
          <p className="mb-4 flex flex-wrap gap-x-3 text-sm text-on-surface-variant">
            <span>{rec.cuisine}</span>
            <span className="text-outline">•</span>
            <span>{formatCost(rec.approx_cost)}</span>
            <span className="text-outline">•</span>
            <span>
              {rec.location}
              {locality}
            </span>
          </p>
        </div>

        <div className="rounded-xl border-l-4 border-primary bg-primary/5 p-4">
          <button
            type="button"
            onClick={() => setExpanded(!expanded)}
            className="flex w-full items-center justify-between text-left"
          >
            <span className="flex items-center gap-2 text-sm font-semibold text-primary">
              <Icon name="auto_awesome" size={18} filled />
              Why we recommend this
            </span>
            <Icon name={expanded ? "expand_less" : "expand_more"} className="text-primary" />
          </button>
          {expanded && (
            <p className="mt-2 text-sm leading-relaxed text-on-surface">{rec.explanation}</p>
          )}
        </div>
      </div>
    </article>
  );
}
