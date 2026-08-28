export function StatusDot({ on = true }: { on?: boolean }) {
  return (
    <span
      className={`inline-block h-2 w-2 rounded-full ${on ? "bg-ok" : "bg-border"}`}
      aria-hidden
    />
  );
}
