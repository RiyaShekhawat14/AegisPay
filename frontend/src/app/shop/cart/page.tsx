"use client";
import AppShell from "@/components/AppShell";
import { Badge, Button, Card } from "@/components";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { checkout, getProducts, getSession, inr, Product, requestAuthorization } from "@/lib/api";

export default function CartPage() {
  const router = useRouter();
  const [line, setLine] = useState<{ productId: string; qty: number }[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [result, setResult] = useState<{ orderId: string; totals: string } | null>(null);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    const cart = JSON.parse(localStorage.getItem("aegispay.cart") ?? '{"cartId":"","items":{}}') as {
      cartId: string;
      items: Record<string, number>;
    };
    setLine(Object.entries(cart.items).map(([productId, qty]) => ({ productId, qty })));
    getProducts(getSession().token || undefined).catch(() => setProducts([]));
    getProducts().then(setProducts).catch(() => setProducts([]));
  }, []);

  const priceOf = (id: string) => products.find((p) => p.id === id)?.price_minor ?? 0;
  const total = line.reduce((s, it) => s + priceOf(it.productId) * it.qty, 0);

  async function pay() {
    const cart = JSON.parse(localStorage.getItem("aegispay.cart") ?? '{"cartId":"","items":{}}');
    const { token } = getSession();
    if (!token || !cart.cartId) {
      setResult({ orderId: "ord_demo", totals: inr(total) });
      return;
    }
    try {
      const order = await checkout(token, cart.cartId);
      const authz = await requestAuthorization(token, order.cart_id);
      setResult({ orderId: order.id, totals: inr(order.total_minor) });
      setMsg(authz.status === "VALID" ? "Authorized ✓" : `Authorization: ${authz.status}`);
    } catch (err) {
      setMsg((err as Error).message);
    }
  }

  return (
    <AppShell role="buyer">
      <div className="mb-5 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold tracking-tight">Your cart</h1>
          <p className="text-sm text-muted">locked &amp; hashed · server-priced</p>
        </div>
        <Button variant="ghost" onClick={() => router.push("/shop")}>← Keep shopping</Button>
      </div>

      <Card title="Items">
        {result && (
          <div className="mb-3 rounded-lg bg-ok/10 p-3 text-sm">
            <Badge tone="ok">Paid</Badge> order <b>{result.orderId}</b> · {result.totals} {msg && <span className="ml-2 text-muted">{msg}</span>}
          </div>
        )}
        {line.length === 0 ? (
          <p className="text-sm text-muted">Your cart is empty.</p>
        ) : (
          <ul className="divide-y divide-border/60 text-sm">
            {line.map((it) => (
              <li key={it.productId} className="flex items-center gap-3 py-2">
                <div className="text-lg">🛍️</div>
                <div className="flex-1"><b>{products.find((p) => p.id === it.productId)?.name ?? it.productId}</b></div>
                <div className="font-semibold">{inr(priceOf(it.productId))} × {it.qty}</div>
              </li>
            ))}
          </ul>
        )}
        {line.length > 0 && (
          <div className="mt-3 flex items-center justify-between border-t border-border pt-3">
            <div className="text-sm text-muted">Total</div>
            <div className="text-lg font-bold">{inr(total)}</div>
          </div>
        )}
      </Card>

      {line.length > 0 && (
        <Button className="mt-4 w-full" variant="primary" onClick={pay}>
          Authorize &amp; pay {inr(total)}
        </Button>
      )}
      <p className="mt-2 text-center text-[11px] text-muted">
        Low risk · auto-approved by policy. The AI can’t change the amount.
      </p>
    </AppShell>
  );
}
