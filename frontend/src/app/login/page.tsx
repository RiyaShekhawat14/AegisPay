"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { getSession, saveSession } from "@/lib/api";

const ROLES = [
  { value: "buyer", title: "AI Buyer", sub: "Shop & buy — SELL", desc: "Discover products, build a cart and checkout." },
  { value: "merchant", title: "Merchant / Admin", sub: "Manage & grow — GROW", desc: "Catalog, campaigns, approvals and audit." },
] as const;

export default function LoginPage() {
  const router = useRouter();
  const [role, setRole] = useState< "buyer" | "merchant" >("buyer");
  const [email, setEmail] = useState("");
  const [token, setToken] = useState("");
  const [error, setError] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    // There is no user/password login endpoint yet; auth is token-based. The session picker
    // stores the role (+ optional token) and gates the app. A real login hooks here later.
    saveSession(role, token.trim());
    router.push(role === "merchant" ? "/merchant" : "/shop");
  }

  const active = ROLES.find((r) => r.value === role)!;

  return (
    <div className="flex min-h-screen items-center justify-center bg-bg p-6 text-ink">
      <div className="w-full max-w-md">
        <div className="mb-6 text-center">
          <div className="mb-2 inline-flex h-10 w-10 items-center justify-center rounded-xl bg-ink text-lg text-white">◈</div>
          <h1 className="text-2xl font-bold tracking-tight">AegisPay</h1>
          <p className="mt-1 text-sm text-muted">The Trust &amp; Growth Layer for Agentic Commerce</p>
        </div>

        <form onSubmit={submit} className="rounded-xl border border-border bg-surface p-6 shadow-sm">
          <div className="grid grid-cols-2 gap-2">
            {ROLES.map((r) => (
              <button
                type="button"
                key={r.value}
                onClick={() => setRole(r.value)}
                className={`rounded-lg border p-3 text-left transition ${
                  role === r.value ? "border-primary bg-primary/5" : "border-border hover:bg-hover"
                }`}
              >
                <div className="text-sm font-semibold">{r.title}</div>
                <div className="text-xs text-primary">{r.sub}</div>
                <div className="mt-1 text-[11px] text-muted">{r.desc}</div>
              </button>
            ))}
          </div>

          <div className="mt-4 space-y-3">
            <label className="block">
              <span className="text-xs font-semibold">Email</span>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="mt-1 w-full rounded-lg border border-border px-3 py-2 text-sm outline-none focus:border-primary"
              />
            </label>
            <label className="block">
              <span className="text-xs font-semibold">Access token (optional)</span>
              <input
                type="password"
                value={token}
                onChange={(e) => setToken(e.target.value)}
                placeholder="Bearer token for the control plane"
                className="mt-1 w-full rounded-lg border border-border px-3 py-2 text-sm outline-none focus:border-primary"
              />
            </label>
          </div>

          {error && <p className="mt-3 text-xs text-err">{error}</p>}

          <button
            type="submit"
            className="mt-5 w-full rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-white transition hover:brightness-95"
          >
            Continue as {active.title}
          </button>
          <p className="mt-3 text-center text-[11px] text-muted">
            The AI can reason and recommend. Only the AegisPay control plane authorizes and executes payments.
          </p>
        </form>
      </div>
    </div>
  );
}
