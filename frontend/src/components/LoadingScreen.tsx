import { Icon } from "./Icon";

export function LoadingScreen() {
  return (
    <div className="relative flex min-h-[60vh] flex-col items-center justify-center px-4 py-12">
      <div className="pointer-events-none absolute inset-0 p-8 opacity-30">
        <div className="mt-8 grid grid-cols-1 gap-6 md:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className={`h-48 overflow-hidden rounded-2xl border border-outline-variant/30 bg-surface-container ${i > 1 ? "hidden md:block" : ""}`}
            >
              <div className="h-32 animate-pulse bg-surface-dim" />
              <div className="space-y-3 p-4">
                <div className="h-4 w-3/4 animate-pulse rounded bg-surface-dim" />
                <div className="h-3 w-1/2 animate-pulse rounded bg-surface-dim" />
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="relative z-10 flex max-w-md flex-col items-center text-center">
        <div className="relative mb-8 flex h-24 w-24 items-center justify-center">
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="h-20 w-20 animate-pulsering rounded-full bg-primary/10" />
          </div>
          <div className="relative animate-float rounded-full border border-primary/20 bg-surface p-4 shadow-card">
            <Icon name="restaurant" className="text-primary" size={48} filled />
          </div>
        </div>
        <h2 className="font-display text-2xl font-bold text-on-background md:text-3xl">
          Finding recommendations…
        </h2>
        <p className="mt-2 text-on-surface-variant">
          Our AI is ranking the best matches for you. This may take 5–15 seconds.
        </p>
        <div className="mt-6 h-1.5 w-48 overflow-hidden rounded-full bg-outline-variant">
          <div className="ai-shimmer h-full w-full rounded-full" />
        </div>
      </div>
    </div>
  );
}
