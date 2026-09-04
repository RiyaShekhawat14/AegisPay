"use client";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { saveSession } from "@/lib/api";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function LoginForm() {
  const router = useRouter();
  const params = useSearchParams();
  const [role, setRole] = useState<"buyer" | "merchant">((params.get("role") as "buyer" | "merchant") || "buyer");
  const [token, setToken] = useState("");
  const [email, setEmail] = useState("");
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setMsg("");
    // JWT authentication: verify the token against the control plane (GET /v1/me). If it
    // works, the session is real; if no token is provided we allow a demo session.
    if (token.trim()) {
      try {
        const res = await fetch(`${BASE}/v1/me`, { headers: { Authorization: `Bearer ${token.trim()}` } });
        if (!res.ok) {
          setMsg(res.status === 401 ? "Invalid or expired token — try again or leave blank for demo." : "Could not reach the control plane.");
          setBusy(false);
          return;
        }
      } catch {
        setMsg("Could not reach the control plane at " + BASE);
        setBusy(false);
        return;
      }
    }
    saveSession(role, token.trim());
    router.push(role === "merchant" ? "/merchant" : "/shop");
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-bg p-6 text-ink">
      <div className="w-full max-w-md">
        <div className="mb-6 flex items-center justify-center gap-2">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-ink text-lg text-white">◈</div>
          <div>
            <h1 className="text-xl font-bold tracking-tight">AegisPay</h1>
            <p className="text-xs text-muted">The Trust &amp; Growth Layer for Agentic Commerce</p>
          </div>
        </div>

        <form onSubmit={submit} className="rounded-2xl border border-border bg-surface p-6 shadow-card">
          <div className="grid grid-cols-2 gap-2">
            <button type="button" onClick={() => setRole("buyer")} className={`rounded-lg border p-3 text-left transition ${role === "buyer" ? "border-primary bg-primarySoft" : "border-border hover:bg-hover"}`}>
              <div className="text-sm font-semibold">Buyer</div>
              <div className="text-[11px] text-primary">SELL · AI Buyer</div>
            </button>
            <button type="button" onClick={() => setRole("merchant")} className={`rounded-lg border p-3 text-left transition ${role === "merchant" ? "border-primary bg-primarySoft" : "border-border hover:bg-hover"}`}>
              <div className="text-sm font-semibold">Merchant</div>
              <div className="text-[11px] text-primary">GROW · Console</div>
            </button>
          </div>

          <div className="mt-4 space-y-3">
            <label className="block">
              <span className="text-xs font-semibold">Email</span>
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" className="aegis-input mt-1 w-full px-3 py-2" />
            </label>
            <label className="block">
              <span className="text-xs font-semibold">Access token (JWT)</span>
              <input type="password" value={token} onChange={(e) => setToken(e.target.value)} placeholder="Paste your bearer token for the control plane" className="aegis-input mt-1 w-full px-3 py-2" />
            </label>
          </div>

          {msg && <p className="mt-3 text-xs text-err">{msg}</p>}

          <button type="submit" disabled={busy} className="mt-5 w-full rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-white transition hover:brightness-95 disabled:opacity-55">
            {busy ? "Verifying…" : `Login as ${role === "merchant" ? "Merchant" : "Buyer"}`}
          </button>
          <p className="mt-3 text-center text-[11px] text-muted">
            Leave the token blank for a demo session. The AI can reason and recommend — only the AegisPay control plane authorizes and executes payments.
          </p>
        </form>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={null}>
      <LoginForm />
    </Suspense>
  );
}
