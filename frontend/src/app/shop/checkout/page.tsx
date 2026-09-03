"use client";
import AppShell from "@/components/AppShell";
import { Badge, Button, Panel } from "@/components/ui";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { checkout, getProducts, getSession, inr, Product, requestAuthorization } from "@/lib/api";

export default function CheckoutPage() {
  const router = useRouter();
  const [line, setLine] = useState<{ productId: string; qty: number }[]>([]);
  const [products, setProducts] = useState<Product[]>([]);

  useEffect(() => {
    const cart = JSON.parse(localStorage.getItem("aegispay.cart") ?? '{"cartId":"","items":{}}') as { cartId: string; items: Record<string, number> };
    setLine(Object.entries(cart.items).map(([productId, qty]) => ({ productId, qty })));
    getProducts(getSession().token || undefined).then(setProducts).catch(() => setProducts([]));
  }, []);

  const priceOf = (id: string) => products.find((p) => p.id === id)?.price_minor ?? 0;
  const total = line.reduce((s, it) => s + priceOf(it.productId) * it.qty, 0);

  async function pay() {
    const cart = JSON.parse(localStorage.getItem("aegispay.cart") ?? '{"cartId":"","items":{}}');
    const { token } = getSession();
    try {
      if (token && cart.cartId) {
        const order = await checkout(token, cart.cartId);
        await requestAuthorization(token, order.cart_id);
      }
      router.push("/shop/success");
    } catch (e) {
      alert((e as Error).message);
    }
  }

  const names = line.map((it) => products.find((p) => p.id === it.productId)?.name ?? it.productId).join(" + ");

  return (
    <AppShell role="buyer">
      <div className="mx-auto max-w-md">
        <div className="mb-4 flex items-center gap-2 border-b border-border pb-3">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-ink text-sm text-white">◈</div>
          <div><b className="text-sm">One last confirmation</b><div className="text-[11px] text-muted">you stay in control</div></div>
        </div>

        <Panel title="Amount">
          <div className="text-xl font-bold">{inr(total)}</div>
          <div className="text-xs text-muted">to <b>ABC Store</b> via Razorpay</div>
        </Panel>

        <div className="mt-3 grid grid-cols-2 gap-3">
          <div className="rounded-lg bg-bg p-3">
            <div className="text-[10px] font-semibold uppercase tracking-wide text-muted">What it is</div>
            <div className="text-sm font-semibold">{names || "—"}</div>
          </div>
          <div className="rounded-lg bg-bg p-3">
            <div className="text-[10px] font-semibold uppercase tracking-wide text-muted">Buying for you</div>
            <div className="text-sm font-semibold">shopping-agent v3</div>
          </div>
        </div>

        <div className="mt-3 rounded-lg bg-hover px-3 py-2 text-xs">
          <Badge tone="info" className="mr-1">authorized</Badge> A valid mandate covers this amount. Revocable any time.
        </div>

        <Button variant="primary" className="mt-4 w-full" onClick={pay}>Authorize &amp; pay {inr(total)}</Button>
        <p className="mt-2 text-center text-[11px] text-muted">Low risk · auto-approved by policy. <b>No human needed.</b></p>
      </div>
    </AppShell>
  );
}
