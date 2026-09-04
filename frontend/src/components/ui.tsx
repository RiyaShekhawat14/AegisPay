"use client";
import type { InputHTMLAttributes, ReactNode } from "react";

// ---- Input (label + field) ----
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

// ---- Badge (tones match the design system) ----
type Tone = "neutral" | "ok" | "warn" | "err" | "info" | "primary" | "red";
const toneCls: Record<Tone, string> = {
  neutral: "bg-hover text-muted",
  ok: "bg-okSoft text-ok",
  warn: "bg-warnSoft text-warn",
  err: "bg-errSoft text-err",
  info: "bg-infoSoft text-info",
  primary: "bg-primarySoft text-primary",
  red: "bg-primarySoft text-primary",
};
export function Badge({ tone = "neutral", children, className = "" }: { tone?: Tone; children: ReactNode; className?: string }) {
  return (
    <span className={`inline-flex items-center gap-1 whitespace-nowrap rounded-md px-2 py-0.5 text-xs font-semibold ${toneCls[tone]} ${className}`}>
      {children}
    </span>
  );
}

// ---- Button (primary / secondary / ghost + sm) ----
type BtnVariant = "primary" | "secondary" | "ghost";
const btnCls: Record<BtnVariant, string> = {
  primary: "bg-primary text-white border-transparent hover:brightness-95",
  secondary: "bg-surface text-ink border-border hover:bg-hover",
  ghost: "bg-transparent text-muted border-transparent hover:bg-hover",
};
export function Button({
  variant = "secondary",
  size = "md",
  className = "",
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: BtnVariant; size?: "sm" | "md" }) {
  return (
    <button
      className={`inline-flex items-center gap-2 rounded-lg border font-semibold transition disabled:opacity-55 ${
        size === "sm" ? "px-2.5 py-1 text-xs" : "px-3 py-2 text-sm"
      } ${btnCls[variant]} ${className}`}
      {...props}
    />
  );
}

// ---- Chip (small label) ----
const chipTone: Record<string, string> = {
  ai: "bg-infoSoft text-info",
  red: "bg-primarySoft text-primary",
  ok: "bg-okSoft text-ok",
  warn: "bg-warnSoft text-warn",
  neutral: "bg-hover text-muted",
};
export function Chip({ tone = "neutral", children }: { tone?: keyof typeof chipTone; children: ReactNode }) {
  return <span className={`inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-[10px] font-semibold ${chipTone[tone]}`}>{children}</span>;
}

// ---- PageHeader ----
export function PageHeader({ title, crumb, action }: { title: string; crumb?: string; action?: ReactNode }) {
  return (
    <div className="mb-5 flex flex-wrap items-center gap-3">
      <div>
        <h1 className="text-xl font-bold tracking-tight">{title}</h1>
        {crumb && <p className="text-xs text-muted">{crumb}</p>}
      </div>
      <div className="ml-auto">{action}</div>
    </div>
  );
}

// ---- Pipeline strip (architecture: control > ai) ----
export function Pipeline({ steps, active = 0 }: { steps: string[]; active?: number }) {
  return (
    <div className="mb-4 flex items-center overflow-x-auto rounded-lg border border-border bg-surface px-3 py-2">
      {steps.map((s, i) => (
        <div key={s} className="flex items-center">
          <div className={`flex items-center gap-1.5 whitespace-nowrap text-[11px] ${i === active ? "font-semibold text-ink" : "text-muted"}`}>
            <span className={`flex h-4 w-4 items-center justify-center rounded-full border text-[9px] ${i === active ? "border-primary text-primary" : "border-border"}`}>
              {i + 1}
            </span>
            {s}
          </div>
          {i < steps.length - 1 && <span className="mx-2 text-[#CBD0D9]">→</span>}
        </div>
      ))}
    </div>
  );
}

// ---- Card / Panel ----
export function Panel({ title, sub, action, children, className = "" }: { title?: ReactNode; sub?: ReactNode; action?: ReactNode; children: ReactNode; className?: string }) {
  return (
    <section className={`rounded-[10px] border border-border bg-surface p-4 ${className}`}>
      {(title || action) && (
        <div className="mb-3 flex flex-wrap items-center gap-2">
          <div className="text-[13px] font-semibold">{title}</div>
          {sub && <span className="text-[11px] text-muted">{sub}</span>}
          <div className="ml-auto flex items-center gap-2">{action}</div>
        </div>
      )}
      {children}
    </section>
  );
}

// ---- KPI card ----
export function Kpi({ label, chip, value, delta, note, deltaTone = "up" }: { label: string; chip?: string; value: ReactNode; delta?: string; note?: string; deltaTone?: "up" | "down" | "warn" }) {
  return (
    <div className="rounded-[10px] border border-border bg-surface p-4">
      <div className="flex items-center gap-1.5 text-xs text-muted">
        {label}
        {chip && <Chip tone="ai">{chip}</Chip>}
      </div>
      <div className="mt-1.5 text-2xl font-bold tracking-tight">{value}</div>
      {delta && (
        <div className={`text-xs font-semibold ${deltaTone === "up" ? "text-ok" : deltaTone === "down" ? "text-err" : "text-warn"}`}>{delta}</div>
      )}
      {note && <div className="mt-1 text-[11px] text-muted">{note}</div>}
    </div>
  );
}

// ---- Row (feed / list item) ----
export function Row({ icon, iconTone = "muted", children, time, meta }: { icon: string; iconTone?: "info" | "warn" | "ok" | "err" | "muted"; children: ReactNode; time?: string; meta?: string }) {
  const tone: Record<string, string> = { info: "text-info", warn: "text-warn", ok: "text-ok", err: "text-err", muted: "text-muted" };
  return (
    <div className="flex gap-2.5 py-2">
      <div className={`flex h-6.5 w-6.5 h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-hover text-sm ${tone[iconTone]}`}>{icon}</div>
      <div className="min-w-0 flex-1 text-xs text-ink/80">
        <div className="font-semibold text-ink">{children}</div>
        {meta && <div className="text-[11px] text-muted">{meta}</div>}
      </div>
      {time && <div className="whitespace-nowrap text-[11px] text-muted">{time}</div>}
    </div>
  );
}

// ---- Table (design-table look) ----
export function Table({ headers, children }: { headers: string[]; children: ReactNode }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border text-left text-[10.5px] uppercase tracking-wide text-muted">
            {headers.map((h) => (
              <th key={h} className="py-2 pr-4 font-semibold">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-border2">{children}</tbody>
      </table>
    </div>
  );
}
