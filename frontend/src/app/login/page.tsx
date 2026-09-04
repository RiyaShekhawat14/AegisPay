"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { saveSession } from "@/lib/api";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [role, setRole] = useState<"buyer" | "merchant">("buyer");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [merchantName, setMerchantName] = useState("");
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setMsg("");
    try {
      const payload = mode === "signup"
        ? { email, password, role: role === "merchant" ? "admin" : "member", merchant_name: merchantName || (role === "merchant" ? "My Store" : "Buyer") }
        : { email, password };
      const res = await fetch(`${BASE}/v1/auth/${mode}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        setMsg(data?.detail ?? data?.message ?? `Request failed: ${res.status}`);
        setBusy(false);
        return;
      }
      // Decide the console from the verified role, or the chosen role.
      const targetRole = data.role === "admin" || role === "merchant" ? "merchant" : "buyer";
      saveSession(targetRole, data.token);
      router.push(targetRole === "merchant" ? "/merchant" : "/shop");
    } catch (err) {
      setMsg("Could not reach the control plane at " + BASE);
      setBusy(false);
    }
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
          {/* role */}
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
              <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" className="aegis-input mt-1 w-full px-3 py-2" />
            </label>
            <label className="block">
              <span className="text-xs font-semibold">Password</span>
              <input type="password" required minLength={6} value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" className="aegis-input mt-1 w-full px-3 py-2" />
            </label>
            {mode === "signup" && role === "merchant" && (
              <label className="block">
                <span className="text-xs font-semibold">Store name</span>
                <input value={merchantName} onChange={(e) => setMerchantName(e.target.value)} placeholder="ABC Store" className="aegis-input mt-1 w-full px-3 py-2" />
              </label>
            )}
          </div>

          {msg && <p className="mt-3 text-xs text-err">{msg}</p>}

          <button type="submit" disabled={busy} className="mt-5 w-full rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-white transition hover:brightness-95 disabled:opacity-55">
            {busy ? "Working…" : mode === "login" ? `Login as ${role === "merchant" ? "Merchant" : "Buyer"}` : `Create ${role === "merchant" ? "Merchant" : "Buyer"} account`}
          </button>

          <div className="mt-4 flex items-center justify-center gap-2 text-xs text-muted">
            <span>{mode === "login" ? "New here?" : "Already have an account?"}</span>
            <button type="button" onClick={() => setMode(mode === "login" ? "signup" : "login")} className="font-semibold text-primary hover:underline">
              {mode === "login" ? "Sign up" : "Login"}
            </button>
          </div>

          <p className="mt-3 text-center text-[11px] text-muted">The AI can reason and recommend — only the AegisPay control plane authorizes and executes payments.</p>
        </form>
      </div>
    </div>
  );
}
