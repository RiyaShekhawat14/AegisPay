"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { forgotPassword, resetPassword, saveSession } from "@/lib/api";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Mode = "login" | "signup" | "forgot" | "reset";

function strength(pw: string): { score: number; label: string; color: string } {
  let score = 0;
  if (pw.length >= 8) score++;
  if (pw.length >= 12) score++;
  if (/[A-Z]/.test(pw) && /[a-z]/.test(pw)) score++;
  if (/\d/.test(pw)) score++;
  if (/[^A-Za-z0-9]/.test(pw)) score++;
  const labels = [
    { score: 0, label: "Too weak", color: "#e00" },
    { score: 1, label: "Weak", color: "#e00" },
    { score: 2, label: "Fair", color: "#f90" },
    { score: 3, label: "Good", color: "#fa0" },
    { score: 4, label: "Strong", color: "#0a0" },
    { score: 5, label: "Strong", color: "#0a0" },
  ];
  return labels[Math.min(score, labels.length - 1)];
}

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<Mode>("login");
  const [role, setRole] = useState<"buyer" | "merchant">("buyer");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [merchantName, setMerchantName] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState(false);
  // Forgot / reset flow
  const [resetToken, setResetToken] = useState("");
  const [hint, setHint] = useState("");

  const pw = strength(password);
  const mismatch = mode === "signup" && confirm.length > 0 && confirm !== password;

  function backToLogin(message = "") {
    setMode("login");
    setMsg(message);
    setPassword("");
    setConfirm("");
    setResetToken("");
    setHint("");
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setMsg("");
    setHint("");

    if (mode === "forgot") {
      setBusy(true);
      try {
        const data = await forgotPassword(email);
        // In non-prod the token is returned so the demo can complete the flow.
        if (data.reset_token) {
          setResetToken(data.reset_token);
          setHint("Reset link generated. Enter the new password below or copy the token.");
          setMode("reset");
        } else {
          setMsg(data.message ?? "If that account exists, a reset link has been sent.");
        }
      } catch {
        setMsg("Could not reach the control plane at " + BASE);
      } finally {
        setBusy(false);
      }
      return;
    }

    if (mode === "reset") {
      setBusy(true);
      try {
        const data = await resetPassword(resetToken, password);
        backToLogin(data.message ?? "Password updated. Please log in.");
      } catch (err) {
        setMsg(err instanceof Error ? err.message : "Reset failed.");
      } finally {
        setBusy(false);
      }
      return;
    }

    setBusy(true);
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
      saveSession(targetRole, data.token, data.agent_id ?? "");
      router.push(targetRole === "merchant" ? "/merchant" : "/shop");
    } catch (err) {
      setMsg("Could not reach the control plane at " + BASE);
      setBusy(false);
    }
  }

  const isLogin = mode === "login";
  const isSignup = mode === "signup";

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
          {mode === "forgot" || mode === "reset" ? (
            <div className="space-y-3">
              <div>
                <h2 className="text-sm font-semibold">Reset password</h2>
                <p className="text-xs text-muted">We'll help you set a new password.</p>
              </div>
              {mode === "forgot" && (
                <label className="block">
                  <span className="text-xs font-semibold">Email</span>
                  <input type="email" required autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" className="aegis-input mt-1 w-full px-3 py-2" />
                </label>
              )}
              {mode === "reset" && (
                <>
                  {resetToken && (
                    <label className="block">
                      <span className="text-xs font-semibold">Reset token</span>
                      <input autoComplete="off" value={resetToken} onChange={(e) => setResetToken(e.target.value)} className="aegis-input mt-1 w-full px-3 py-2" />
                      {hint && <span className="mt-1 block text-[11px] text-muted">{hint}</span>}
                    </label>
                  )}
                  <label className="block">
                    <span className="text-xs font-semibold">New password</span>
                    <div className="relative mt-1">
                      <input type={showPw ? "text" : "password"} required autoComplete="new-password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" className="aegis-input w-full px-3 py-2 pr-10" />
                      <button type="button" onClick={() => setShowPw((v) => !v)} className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-primary">{showPw ? "Hide" : "Show"}</button>
                    </div>
                  </label>
                  <label className="block">
                    <span className="text-xs font-semibold">Confirm</span>
                    <input type={showPw ? "text" : "password"} required autoComplete="new-password" value={confirm} onChange={(e) => setConfirm(e.target.value)} placeholder="••••••••" className="aegis-input mt-1 w-full px-3 py-2" />
                  </label>
                </>
              )}
              {msg && <p className="text-xs text-err">{msg}</p>}
              <button type="submit" disabled={busy} className="mt-2 w-full rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-white transition hover:brightness-95 disabled:opacity-55">
                {busy ? "Working…" : mode === "forgot" ? "Send reset link" : "Set new password"}
              </button>
              <div className="text-center text-xs text-muted">
                <button type="button" onClick={() => backToLogin()} className="font-semibold text-primary hover:underline">Back to login</button>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
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

              <label className="block">
                <span className="text-xs font-semibold">Email</span>
                <input type="email" required autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" className="aegis-input mt-1 w-full px-3 py-2" />
              </label>
              <label className="block">
                <span className="text-xs font-semibold">Password</span>
                <div className="relative mt-1">
                  <input type={showPw ? "text" : "password"} required autoComplete={isSignup ? "new-password" : "current-password"} minLength={isSignup ? 8 : undefined} value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" className="aegis-input w-full px-3 py-2 pr-10" />
                  <button type="button" onClick={() => setShowPw((v) => !v)} className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-primary">{showPw ? "Hide" : "Show"}</button>
                </div>
              </label>

              {isSignup && (
                <>
                  <label className="block">
                    <span className="text-xs font-semibold">Confirm password</span>
                    <input type={showPw ? "text" : "password"} required minLength={8} autoComplete="new-password" value={confirm} onChange={(e) => setConfirm(e.target.value)} placeholder="••••••••" className="aegis-input mt-1 w-full px-3 py-2" />
                  </label>
                  <div className="space-y-1">
                    <div className="flex gap-1">
                      {[0, 1, 2, 3, 4].map((i) => (
                        <div key={i} className="h-1 flex-1 rounded transition" style={{ background: i < pw.score ? pw.color : "var(--border)" }} />
                      ))}
                    </div>
                    <div className="flex justify-between text-[11px] text-muted">
                      <span>Password strength</span>
                      <span style={{ color: pw.color }}>{password ? pw.label : "Enter a password"}</span>
                    </div>
                  </div>
                  {mismatch && <p className="text-xs text-err">Passwords do not match.</p>}
                </>
              )}

              {isSignup && role === "merchant" && (
                <label className="block">
                  <span className="text-xs font-semibold">Store name</span>
                  <input autoComplete="organization" value={merchantName} onChange={(e) => setMerchantName(e.target.value)} placeholder="ABC Store" className="aegis-input mt-1 w-full px-3 py-2" />
                </label>
              )}

              {msg && <p className="text-xs text-err">{msg}</p>}

              <button type="submit" disabled={busy || mismatch} className="mt-2 w-full rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-white transition hover:brightness-95 disabled:opacity-55">
                {busy ? "Working…" : isLogin ? `Login as ${role === "merchant" ? "Merchant" : "Buyer"}` : `Create ${role === "merchant" ? "Merchant" : "Buyer"} account`}
              </button>

              {isLogin && (
                <div className="text-center text-xs text-muted">
                  <button type="button" onClick={() => { setMode("forgot"); setMsg(""); }} className="font-semibold text-primary hover:underline">Forgot password?</button>
                </div>
              )}

              <div className="mt-2 flex items-center justify-center gap-2 text-xs text-muted">
                <span>{isLogin ? "New here?" : "Already have an account?"}</span>
                <button type="button" onClick={() => { setMode(isLogin ? "signup" : "login"); setMsg(""); setConfirm(""); }} className="font-semibold text-primary hover:underline">
                  {isLogin ? "Sign up" : "Login"}
                </button>
              </div>

              <p className="mt-2 text-center text-[11px] text-muted">The AI can reason and recommend — only the AegisPay control plane authorizes and executes payments.</p>
            </div>
          )}
        </form>
      </div>
    </div>
  );
}
