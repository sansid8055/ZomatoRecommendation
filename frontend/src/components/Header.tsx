import { Icon } from "./Icon";

export function Header() {
  return (
    <header className="fixed top-0 left-0 z-50 flex h-16 w-full items-center justify-between border-b border-outline-variant/30 bg-surface px-margin-mobile shadow-sm">
      <div className="flex items-center gap-2">
        <Icon name="restaurant" className="text-primary" size={28} filled />
        <span className="font-display text-xl font-bold text-primary">Zomato AI</span>
      </div>
      <div className="hidden items-center gap-4 md:flex">
        <div className="flex items-center rounded-full border border-secondary/20 bg-secondary-container/10 px-3 py-1">
          <Icon name="bolt" className="mr-2 text-secondary" size={18} filled />
          <span className="text-xs font-semibold text-secondary">Powered by Groq AI</span>
        </div>
      </div>
    </header>
  );
}
