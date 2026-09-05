"use client";
import AppShell from "@/components/AppShell";
import { Badge, Button, Panel } from "@/components/ui";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { approveAuthorization, getAuthorization, getSession, initiatePayment, inr, Authorization } from "@/lib/api";

declare global {
  interface Window { Razorpay?: any }
}

function jwtSub(token: string): string {
  try {
    const p = token.split(".")[1];
    const b = atob(p.replace(/-/g, "+").replace(/_/g, "/"));
    return (JSON.parse(decodeURIComponent(escape(b))) as { sub?: string }).sub ?? "";
  } catch {
    return "";
  }
}

const RAZORPAY_KEY = process.env.NEXT_PUBLIC_RAZORPAY_KEY_ID ?? "";

export default function ApprovalPage() {
  const router = useRouter();
  const [authz, setAuthz] = useState<Authorization | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  const authzId = typeof window !== "undefined" ? localStorage.getItem("aegispay.pendingAuthz") : null;
  const orderId = typeof window !== "undefined" ? localStorage.getItem("aegispay.pendingOrder") : null;

  async function pay() {
    const { token } = getSession();
    if (!token || !authzId || !orderId) { setErr("No pending authorization. Go back and try again."); return; }
    setBusy(true); setErr("");
    try {
      const payment = await initiatePayment(token, orderId, authzId);
      if (RAZORPAY_KEY && payment.provider_order_id) {
        await new Promise<void>((resolve, reject) => {
          const rzp = new window.Razorpay({
            key: RAZORPAY_KEY,
            amount: String(authz?.amount_minor ?? payment.amount_minor),
            currency: "INR",
            order_id: payment.provider_order_id,
            name: "AegisPay",
            description: "Approved purchase",
            handler: () => { localStorage.setItem("aegispay.paid", payment.id); resolve(); },
            modal: { ondismiss: () => reject(new Error("Payment cancelled.")) },
          });
          rzp.on("payment.failed", () => reject(new Error("Payment failed.")));
          rzp.open();
        });
      }
      localStorage.setItem("aegispay.paid", payment.id);
      router.push("/shop/success");
    } catch (e) {
      setErr((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function approveAndPay() {
    const { token } = getSession();
    const approverId = jwtSub(token || "");
    if (!token || !authzId || !approverId) { setErr("Unable to confirm this purchase. Re-login."); return; }
    setBusy(true); setErr("");
    try {
      // Demo: the account confirms its own high-value purchase (single-user tenant).
      const a = await approveAuthorization(token, authzId, approverId);
      setAuthz(a);
      await pay();
    } catch (e) {
      setErr((e as Error).message);
      setBusy(false);
    }
  }

  async function refresh() {
    const { token } = getSession();
    if (!token || !authzId) return;
    const a = await getAuthorization(token, authzId).catch(() => null);
    if (a) setAuthz(a);
  }

  // Poll every 3s until the authorization becomes valid, then load the amount.
  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 3000);
    return () => clearInterval(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const amount = authz?.amount_minor ?? 0;
  const isHigh = authz?.risk && (authz.risk as { level?: string })?.level === "HIGH";

  return (
    <AppShell role="buyer">
      <div className="mx-auto max-w-md">
        <div className="mb-4 flex items-center gap-2 border-b border-border pb-3">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-ink text-sm text-white">◈</div>
          <div><b className="text-sm">Approval needed</b><div className="text-[11px] text-muted">a person must confirm</div></div>
          <Badge tone="warn" className="ml-auto">{authz?.status === "VALID" ? "approved" : "pending"}</Badge>
        </div>

        <Panel title={authz?.status === "VALID" ? "Approved · proceed to pay" : "Amount · awaiting approval"}>
          <div className="flex items-center gap-2 text-xl font-bold">{inr(amount)} {isHigh ? <Badge tone="warn">HIGH</Badge> : <Badge tone="neutral">{authz?.risk ? "risk" : "—"}</Badge>}</div>
          <div className="mt-1 text-xs text-muted">Above your auto-limit, so a person decides. You’re notified when it’s approved.</div>
        </Panel>

        <div className="mt-3 rounded-lg bg-hover px-3 py-2 text-xs">
          <Badge tone="info" className="mr-1">scoped</Badge> Limited to this cart · expires · can’t be reused.
        </div>

        {err && <p className="mt-3 text-xs text-err">{err}</p>}

        {authz?.status === "VALID" ? (
          <Button variant="primary" className="mt-4 w-full" disabled={busy} onClick={pay}>
            {busy ? "Opening Razorpay…" : `Pay ${inr(amount)} via Razorpay`}
          </Button>
        ) : (
          <>
            <div className="mt-4 flex items-center justify-center gap-2 rounded-lg bg-hover px-3 py-2 text-xs text-muted">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-warn" /> Waiting for merchant approval…
            </div>
            <Button variant="primary" className="mt-2 w-full" disabled={busy} onClick={approveAndPay}>
              {busy ? "Opening Razorpay…" : `Confirm & pay ${inr(amount)} now`}
            </Button>
            <Button variant="secondary" className="mt-2 w-full" onClick={refresh}>Check status</Button>
          </>
        )}

        <Button variant="ghost" className="mt-2 w-full" onClick={() => router.push("/shop")}>Back to shop</Button>
      </div>
    </AppShell>
  );
}
