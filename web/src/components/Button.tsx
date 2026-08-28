import type { ButtonHTMLAttributes } from "react";

type Variant = "primary" | "secondary" | "ghost";

const styles: Record<Variant, string> = {
  primary: "bg-primary text-white border-transparent hover:brightness-95",
  secondary: "bg-surface text-ink border-border hover:bg-hover",
  ghost: "bg-transparent text-muted border-transparent hover:bg-hover",
};

export function Button({
  variant = "secondary",
  className = "",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant }) {
  return (
    <button
      className={`inline-flex items-center gap-2 rounded-lg border px-3 py-2 text-sm font-semibold transition ${styles[variant]} ${className}`}
      {...props}
    />
  );
}
