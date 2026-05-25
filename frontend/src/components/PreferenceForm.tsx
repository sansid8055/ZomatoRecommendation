"use client";

import type { BudgetTier, PreferencesInput } from "@/lib/types";
import { Icon } from "./Icon";

interface PreferenceFormProps {
  locations: string[];
  value: PreferencesInput;
  onChange: (v: PreferencesInput) => void;
  disabled?: boolean;
}

const BUDGETS: { id: BudgetTier; label: string }[] = [
  { id: "low", label: "Low" },
  { id: "medium", label: "Medium" },
  { id: "high", label: "High" },
];

export function PreferenceForm({
  locations,
  value,
  onChange,
  disabled,
}: PreferenceFormProps) {
  const set = <K extends keyof PreferencesInput>(key: K, v: PreferencesInput[K]) =>
    onChange({ ...value, [key]: v });

  return (
    <div className="rounded-2xl border border-outline-variant/30 bg-surface-container-lowest p-4 shadow-card md:p-6">
      <form className="space-y-6" onSubmit={(e) => e.preventDefault()}>
        <div className="space-y-2">
          <label className="flex items-center gap-2 text-sm font-semibold text-on-surface-variant">
            <Icon name="location_on" size={22} />
            Location
          </label>
          <div className="relative">
            <select
              className="h-12 w-full appearance-none rounded-lg border border-outline-variant bg-surface px-4 transition focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 disabled:opacity-60"
              value={value.location}
              onChange={(e) => set("location", e.target.value)}
              disabled={disabled || locations.length === 0}
            >
              {locations.length === 0 ? (
                <option value="">Loading cities…</option>
              ) : (
                locations.map((loc) => (
                  <option key={loc} value={loc}>
                    {loc}
                  </option>
                ))
              )}
            </select>
            <Icon
              name="expand_more"
              className="pointer-events-none absolute right-4 top-3 text-outline"
            />
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex items-end justify-between">
            <label className="flex items-center gap-2 text-sm font-semibold text-on-surface-variant">
              <Icon name="payments" size={22} />
              Budget
            </label>
            <span className="text-xs italic text-outline">Based on cost-for-two bands</span>
          </div>
          <div className="grid grid-cols-3 gap-1 rounded-xl border border-outline-variant bg-surface-container p-1">
            {BUDGETS.map((b) => (
              <button
                key={b.id}
                type="button"
                disabled={disabled}
                onClick={() => set("budget", b.id)}
                className={`rounded-lg py-3 text-sm font-semibold transition ${
                  value.budget === b.id
                    ? "border border-outline-variant/50 bg-surface-container-lowest text-primary shadow-sm"
                    : "text-on-surface-variant hover:bg-surface-container-high"
                }`}
              >
                {b.label}
              </button>
            ))}
          </div>
        </div>

        <div className="space-y-2">
          <label className="flex items-center gap-2 text-sm font-semibold text-on-surface-variant">
            <Icon name="restaurant_menu" size={22} />
            Cuisine <span className="font-normal text-outline">(optional)</span>
          </label>
          <input
            type="text"
            placeholder="e.g., Italian, Chinese, North Indian"
            maxLength={100}
            disabled={disabled}
            className="h-12 w-full rounded-lg border border-outline-variant bg-surface px-4 transition focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
            value={value.cuisine ?? ""}
            onChange={(e) => set("cuisine", e.target.value)}
          />
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label className="flex items-center gap-2 text-sm font-semibold text-on-surface-variant">
              <Icon name="star" size={22} />
              Minimum Rating
            </label>
            <span className="font-display text-xl font-bold text-primary">
              {(value.min_rating ?? 4).toFixed(1)}
            </span>
          </div>
          <input
            type="range"
            min={0}
            max={5}
            step={0.5}
            disabled={disabled}
            className="rating-slider h-2 w-full cursor-pointer appearance-none rounded-lg bg-outline-variant"
            value={value.min_rating ?? 4}
            onChange={(e) => set("min_rating", parseFloat(e.target.value))}
          />
          <div className="flex justify-between text-xs text-outline">
            <span>0.0 (skip)</span>
            <span>5.0</span>
          </div>
        </div>

        <div className="space-y-2">
          <label className="flex items-center gap-2 text-sm font-semibold text-on-surface-variant">
            <Icon name="tune" size={22} />
            Additional Preferences <span className="font-normal text-outline">(optional)</span>
          </label>
          <textarea
            rows={4}
            maxLength={500}
            disabled={disabled}
            placeholder="e.g., rooftop, family-friendly, quick service, good for a date night…"
            className="w-full resize-none rounded-lg border border-outline-variant bg-surface p-4 transition focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
            value={value.additional_preferences ?? ""}
            onChange={(e) => set("additional_preferences", e.target.value)}
          />
        </div>
      </form>
    </div>
  );
}
