import type { InputHTMLAttributes } from "react";

export function Input({ label, className = "", ...props }: InputHTMLAttributes<HTMLInputElement> & { label?: string }) {
  return (
    <label className="flex flex-col gap-1.5">
      {label && <span className="text-xs font-semibold text-ink">{label}</span>}
      <input
        className={`rounded-lg border border-border bg-surface px-3 py-2 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/10 ${className}`}
        {...props}
      />
    </label>
  );
}
