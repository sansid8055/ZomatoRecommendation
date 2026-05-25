import type { AppConfig } from "@/lib/types";
import { Icon } from "./Icon";

interface SetupSidebarProps {
  config: AppConfig | null;
  onRefine?: () => void;
  showRefine?: boolean;
}

export function SetupSidebar({ config, onRefine, showRefine }: SetupSidebarProps) {
  const apiOk = config?.api_key_configured ?? false;
  const datasetOk = config?.dataset_ready ?? false;

  return (
    <aside className="w-full shrink-0 space-y-4 lg:w-72">
      <div className="rounded-2xl border border-outline-variant bg-surface-container-lowest p-4 shadow-card">
        <h3 className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-on-surface-variant">
          <Icon name="settings" size={18} />
          Setup Status
        </h3>

        <div
          className={`mb-2 flex items-center gap-3 rounded-lg border p-3 ${
            apiOk
              ? "border-tertiary/20 bg-tertiary-container/10"
              : "border-error/30 bg-error-container"
          }`}
        >
          <div
            className={`h-3 w-3 rounded-full ${apiOk ? "animate-pulse bg-tertiary" : "bg-error"}`}
          />
          <span className="text-sm font-medium text-on-surface">
            {apiOk ? "API key configured" : "GROQ_API_KEY missing"}
          </span>
        </div>

        {!datasetOk && (
          <p className="mb-2 rounded-lg bg-error-container p-2 text-xs text-on-error-container">
            Dataset missing. Run:{" "}
            <code className="font-mono">python scripts/download_dataset.py</code>
          </p>
        )}

        {config && (
          <div className="mt-3 flex flex-wrap gap-2">
            <span className="rounded-lg bg-surface-container-high px-2 py-1 text-xs text-on-surface-variant">
              {config.llm_model}
            </span>
            <span className="rounded-lg bg-surface-container-high px-2 py-1 text-xs text-on-surface-variant">
              {config.llm_provider}
            </span>
            <span className="rounded-lg bg-secondary-container/10 px-2 py-1 text-xs text-secondary">
              Top {config.top_k_results}
            </span>
          </div>
        )}

        {!apiOk && (
          <a
            href="https://console.groq.com/keys"
            target="_blank"
            rel="noopener noreferrer"
            className="mt-3 inline-block text-sm font-semibold text-secondary hover:underline"
          >
            Get Groq API key →
          </a>
        )}
      </div>

      {showRefine && onRefine && (
        <button
          type="button"
          onClick={onRefine}
          className="w-full rounded-xl border border-outline-variant bg-surface-container-lowest py-3 text-sm font-semibold text-on-surface transition hover:bg-surface-container-high"
        >
          Refine search
        </button>
      )}

      <div className="relative overflow-hidden rounded-2xl border border-primary/10 bg-primary/5 p-4">
        <div className="glass-shimmer pointer-events-none absolute inset-0 opacity-20" />
        <h4 className="relative font-display text-lg font-semibold text-primary">Pro Tip</h4>
        <p className="relative mt-1 text-sm text-on-surface-variant">
          Mention vibes like &quot;brunch&quot;, &quot;family-friendly&quot;, or &quot;quiet
          work cafe&quot; in additional preferences.
        </p>
      </div>
    </aside>
  );
}
