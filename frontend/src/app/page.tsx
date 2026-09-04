"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { saveSession } from "@/lib/api";

const ROLES = [
  {
    value: "merchant" as const,
    mark: "◈",
    title: "Merchant / Admin",
    sub: "GROW · Merchant Console",
    desc: "Manage catalog, launch capped campaigns, approve high-risk actions and audit every step.",
    points: ["Grow revenue with AI", "Budget-capped campaigns", "Approvals & audit"],
    accent: "from-primary/15 to-primarySoft",
    btn: "bg-primary text-white",
  },
  {
    value: "buyer" as const,
    mark: "🛒",
    title: "AI Buyer",
    sub: "SELL · AI Buyer Checkout",
    desc: "Let an AI help you shop — discover products, build a cart, authorize and pay in test mode.",
    points: ["Find the best match", "Server-owned prices", "Safe, gated checkout"],
    accent: "from-info/10 to-infoSoft",
    btn: "bg-ink text-white",
  },
];

export default function Home() {
  const router = useRouter();
  const [token, setToken] = useState("");

  function enter(role: "merchant" | "buyer") {
    saveSession(role, token.trim());
    router.push(role === "merchant" ? "/merchant" : "/shop");
  }

  return (
    <div className="relative min-h-screen overflow-hidden bg-bg text-ink">
      {/* ambient gradient */}
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top,_rgba(211,47,91,0.08),_transparent_55%),radial-gradient(ellipse_at_bottom_right,_rgba(37,99,235,0.06),_transparent_55%)]" />

      <header className="relative z-10 mx-auto flex max-w-6xl items-center gap-2 px-6 py-5">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-ink text-white">◈</div>
        <div>
          <div className="text-sm font-bold leading-tight">AegisPay</div>
          <div className="text-[9px] tracking-wide text-muted">THE TRUST &amp; GROWTH LAYER</div>
        </div>
        <div className="ml-auto flex items-center gap-2 text-xs">
          <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer" className="rounded-lg px-3 py-1.5 text-muted hover:bg-hover">API docs</a>
          <a href="http://localhost:8001/docs" target="_blank" rel="noreferrer" className="rounded-lg px-3 py-1.5 text-muted hover:bg-hover">AI runtime</a>
        </div>
      </header>

      <main className="relative z-10 mx-auto flex max-w-5xl flex-col items-center px-6 pb-20 pt-8 text-center">
        <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-border bg-surface px-3 py-1 text-[10px] font-semibold tracking-wide text-muted">
          <span className="h-1.5 w-1.5 rounded-full bg-ok" /> control plane operational
        </div>

        <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-primary">AegisPay · Merchant Console &amp; AI Buyer</div>
        <h1 className="mt-3 max-w-3xl text-4xl font-extrabold leading-tight tracking-tight md:text-6xl">
          AI can reason &amp; recommend.<br />
          <span className="bg-gradient-to-r from-primary to-warn bg-clip-text text-transparent">Only AegisPay moves money.</span>
        </h1>
        <p className="mt-5 max-w-2xl text-sm leading-relaxed text-muted md:text-base">
          One workspace where AI grows and sells for your store — with a deterministic control plane
          (policy → risk → authorization → payment) between the AI and money.
        </p>

        {/* pipeline strip */}
        <div className="mt-8 flex flex-wrap items-center justify-center gap-1 text-[11px] text-muted">
          {["AI proposes", "Validates", "Policy", "Risk", "Approve", "Pay", "Verify", "Audit"].map((s, i, arr) => (
            <span key={s} className="flex items-center">
              <span className="flex items-center gap-1.5 rounded-full border border-border bg-surface px-2.5 py-1 font-semibold">{s}</span>
              {i < arr.length - 1 && <span className="mx-1 text-[#CBD0D9]">→</span>}
            </span>
          ))}
        </div>

        {/* role cards */}
        <div className="mt-10 grid w-full gap-5 md:grid-cols-2">
          {ROLES.map((r) => (
            <div
              key={r.value}
              className={`group flex flex-col rounded-2xl border border-border bg-surface p-6 text-left transition hover:-translate-y-1 hover:shadow-[0_20px_60px_-15px_rgba(211,47,91,0.25)]`}
            >
              <div className={`mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br text-xl ${r.accent}`}>{r.mark}</div>
              <div className="text-[10px] font-semibold uppercase tracking-wide text-primary">{r.sub}</div>
              <div className="mt-1 text-lg font-bold">{r.title}</div>
              <p className="mt-2 text-sm text-muted">{r.desc}</p>
              <ul className="mt-4 space-y-1.5 text-xs text-muted">
                {r.points.map((p) => (
                  <li key={p} className="flex items-center gap-2"><span className="text-ok">✓</span>{p}</li>
                ))}
              </ul>
              <div className="mt-5 flex items-center gap-2">
                <input
                  type="password"
                  value={token}
                  onChange={(e) => setToken(e.target.value)}
                  placeholder="Access token (optional)"
                  className="flex-1 rounded-lg border border-border bg-bg px-3 py-2 text-xs outline-none focus:border-primary"
                />
                <button onClick={() => enter(r.value)} className={`rounded-lg px-4 py-2 text-sm font-semibold transition group-hover:brightness-95 ${r.btn}`}>
                  Enter {r.title.split(" ")[0]} →
                </button>
              </div>
            </div>
          ))}
        </div>

        <p className="mt-8 max-w-lg text-[11px] leading-relaxed text-muted">
          The AI never receives payment keys, DB credentials or money tools — it only requests. Test-mode Razorpay, tenant-isolated, tamper-evident audit.
        </p>
      </main>
    </div>
  );
}
