export function Icon({
  name,
  filled = false,
  className = "",
  size = 24,
}: {
  name: string;
  filled?: boolean;
  className?: string;
  size?: number;
}) {
  return (
    <span
      className={`material-symbols-outlined ${filled ? "material-symbols-filled" : ""} ${className}`}
      style={{ fontSize: size }}
    >
      {name}
    </span>
  );
}
