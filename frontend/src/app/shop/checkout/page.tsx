"use client";
import AppShell from "@/components/AppShell";
import { Badge, Button, Panel } from "@/components/ui";
import { Pipeline } from "@/components/ui";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { checkout, getProducts, getSession, initiatePayment, inr, Product, requestAuthorization } from "@/lib/api";

declare global {
  interface Window { Razorpay?: any }
}

const RAZORPAY_KEY = process.env.NEXT_PUBLIC_RAZORPAY_KEY_ID ?? "";

export default function CheckoutPage() {
  const router = useRouter();
  const [line, setLine] = useState<{ productId: string; qty: number }[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  useEffect(() => {
    const cart = JSON.parse(localStorage.getItem("aegispay.cart") ?? '{"cartId":"","items":{}}') as { cartId: string; items: Record<string, number> };
    setLine(Object.entries(cart.items).map(([productId, qty]) => ({ productId, qty })));
    getProducts(getSession().token || undefined).then(setProducts).catch(() => setProducts([]));
    // Load the Razorpay checkout SDK once, when a test key is configured.
    if (RAZORPAY_KEY && !window.Razorpay) {
      const s = document.createElement("script");
      s.src = "https://checkout.razorpay.com/v1/checkout.js";
      s.async = true;
      document.body.appendChild(s);
    }
  }, []);

  const priceOf = (id: string) => products.find((p) => p.id === id)?.price_minor ?? 0;
  const total = line.reduce((s, it) => s + priceOf(it.productId) * it.qty, 0);

  async function pay() {
    const cart = JSON.parse(localStorage.getItem("aegispay.cart") ?? '{"cartId":"","items":{}}') as { cartId: string; items: Record<string, number> };
    const { token } = getSession();
    setBusy(true); setErr("");
    try {
      if (!token || !cart.cartId) throw new Error("No cart yet. Add items first.");
      const order = await checkout(token, cart.cartId);
      const authz = await requestAuthorization(token, order.cart_id);
      if (authz.status !== "VALID") {
        localStorage.setItem("aegispay.pendingAuthz", authz.id);
        router.push("/shop/approval");
        return;
      }
      const payment = await initiatePayment(token, order.id, authz.id);

      // Razorpay test mode: open the hosted checkout when a key is configured.
      if (RAZORPAY_KEY && payment.provider_order_id) {
        await new Promise<void>((resolve, reject) => {
          const rzp = new window.Razorpay({
            key: RAZORPAY_KEY,
            amount: String(total),
            currency: "INR",
            order_id: payment.provider_order_id,
            name: "AegisPay",
            description: "Test mode payment",
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

  const names = line.map((it) => products.find((p) => p.id === it.productId)?.name ?? it.productId).join(" + ");

  return (
    <AppShell role="buyer">
      <div className="mx-auto max-w-md">
        <Pipeline steps={["Propose", "Validate", "Policy", "Risk", "Approve", "Razorpay", "Verify", "Audit"]} active={4} />
        <div className="mb-4 flex items-center gap-2 border-b border-border pb-3">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-ink text-sm text-white">◈</div>
          <div><b className="text-sm">One last confirmation</b><div className="text-[11px] text-muted">you stay in control</div></div>
        </div>

        <Panel title="Amount">
          <div className="text-xl font-bold">{inr(total)}</div>
          <div className="text-xs text-muted">via Razorpay (test mode)</div>
        </Panel>

        <div className="mt-3 grid grid-cols-2 gap-3">
          <div className="rounded-lg bg-bg p-3">
            <div className="text-[10px] font-semibold uppercase tracking-wide text-muted">What it is</div>
            <div className="text-sm font-semibold">{names || "—"}</div>
          </div>
          <div className="rounded-lg bg-bg p-3">
            <div className="text-[10px] font-semibold uppercase tracking-wide text-muted">Buying for you</div>
            <div className="text-sm font-semibold">shopping-agent</div>
          </div>
        </div>

        <div className="mt-3 rounded-lg bg-hover px-3 py-2 text-xs">
          <Badge tone="info" className="mr-1">authorized</Badge> A valid mandate covers this amount. Revocable any time.
        </div>

        {err && <p className="mt-3 text-xs text-err">{err}</p>}

        <Button variant="primary" className="mt-4 w-full" disabled={busy} onClick={pay}>
          {busy ? "Working…" : `Authorize & pay ${inr(total)}`}
        </Button>
        <p className="mt-2 text-center text-[11px] text-muted">Low risk · auto-approved by policy. <b>No human needed.</b></p>
      </div>
    </AppShell>
  );
}
