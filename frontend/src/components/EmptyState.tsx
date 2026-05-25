import { Icon } from "./Icon";

interface EmptyStateProps {
  message?: string;
  suggestions: string[];
  onReset: () => void;
}

export function EmptyState({ message, suggestions, onReset }: EmptyStateProps) {
  return (
    <div className="mx-auto w-full max-w-lg py-8 text-center">
      <div className="relative mb-6 inline-block">
        <div className="absolute -top-12 left-1/2 -z-10 h-64 w-64 -translate-x-1/2 animate-pulse rounded-full bg-primary/5 blur-[80px]" />
        <div className="mx-auto flex h-48 w-48 items-center justify-center rounded-full border border-outline-variant/30 bg-surface-container-low">
          <Icon name="search_off" className="text-outline" size={80} />
        </div>
        <div className="absolute bottom-2 right-2 flex h-12 w-12 items-center justify-center rounded-xl border border-outline-variant bg-white shadow-md">
          <Icon name="close" className="text-primary" size={28} />
        </div>
      </div>

      <h2 className="font-display text-2xl font-bold text-on-surface md:text-3xl">
        No restaurants match your criteria
      </h2>
      <p className="mx-auto mt-2 max-w-md text-on-surface-variant">
        {message ??
          "Our AI searched the dataset, but your current filters are too specific."}
      </p>

      {suggestions.length > 0 && (
        <div className="ai-shimmer mt-8 rounded-2xl border border-outline-variant/40 bg-surface-container-lowest p-6 text-left shadow-card">
          <div className="mb-4 flex items-center gap-2 text-primary">
            <Icon name="lightbulb" size={20} />
            <span className="text-xs font-semibold uppercase tracking-wider">
              Try these adjustments
            </span>
          </div>
          <ul className="space-y-3">
            {suggestions.map((tip) => (
              <li key={tip} className="flex items-start gap-3 text-sm text-on-surface">
                <Icon name="chevron_right" className="mt-0.5 shrink-0 text-secondary" size={18} />
                {tip}
              </li>
            ))}
          </ul>
        </div>
      )}

      <button
        type="button"
        onClick={onReset}
        className="mt-8 w-full rounded-xl bg-primary px-10 py-4 font-semibold uppercase tracking-wide text-on-primary shadow-md transition hover:bg-primary-container active:scale-[0.98] md:w-auto"
      >
        Reset preferences
      </button>
    </div>
  );
}
