export function Card({
  title,
  action,
  children,
  className = "",
}: {
  title?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section className={`rounded-xl border border-border bg-surface p-4 ${className}`}>
      {(title || action) && (
        <div className="mb-3 flex items-center gap-2">
          {title && <h3 className="text-sm font-semibold">{title}</h3>}
          <div className="ms-auto">{action}</div>
        </div>
      )}
      {children}
    </section>
  );
}
