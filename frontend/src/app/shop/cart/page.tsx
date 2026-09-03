"use client";
import AppShell from "@/components/AppShell";
import { Badge, Button, Panel } from "@/components/ui";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { getProducts, getSession, inr, Product } from "@/lib/api";

export default function CartPage() {
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

  function setQty(id: string, d: number) {
    const cart = JSON.parse(localStorage.getItem("aegispay.cart") ?? '{"cartId":"","items":{}}') as { cartId: string; items: Record<string, number> };
    cart.items[id] = (cart.items[id] ?? 0) + d;
    if (cart.items[id] <= 0) delete cart.items[id];
    localStorage.setItem("aegispay.cart", JSON.stringify(cart));
    setLine(Object.entries(cart.items).map(([productId, qty]) => ({ productId, qty })));
  }

  return (
    <AppShell role="buyer">
      <div className="mx-auto max-w-lg">
        <div className="mb-4 flex items-center gap-2 border-b border-border pb-3">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-ink text-sm text-white">◈</div>
          <div><b className="text-sm">Your cart</b><div className="text-[11px] text-muted">locked &amp; hashed</div></div>
          <Badge tone="neutral" className="ml-auto">server-priced</Badge>
        </div>

        {line.length === 0 ? (
          <Panel title="Items"><p className="text-sm text-muted">Your cart is empty.</p></Panel>
        ) : (
          <Panel title="Items">
            <div className="space-y-2">
              {line.map((it) => (
                <div key={it.productId} className="flex items-center gap-3 rounded-lg border border-border p-2.5">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-hover text-lg">🛍️</div>
                  <div className="min-w-0 flex-1"><b className="text-sm">{products.find((p) => p.id === it.productId)?.name ?? it.productId}</b></div>
                  <div className="flex items-center gap-2">
                    <button onClick={() => setQty(it.productId, -1)} className="h-5 w-5 rounded border border-border text-xs">−</button>
                    <span className="text-sm">{it.qty}</span>
                    <button onClick={() => setQty(it.productId, 1)} className="h-5 w-5 rounded border border-border text-xs">+</button>
                  </div>
                  <div className="font-semibold tabular-nums">{inr(priceOf(it.productId))}</div>
                </div>
              ))}
            </div>
            <div className="mt-3 border-t border-border pt-3">
              <div className="flex justify-between text-sm text-muted"><span>Subtotal</span><span className="font-semibold text-ink">{inr(total)}</span></div>
              <div className="flex justify-between text-sm text-muted"><span>Shipping</span><span>₹0</span></div>
              <div className="mt-1 flex justify-between text-base font-bold"><span>Total</span><span>{inr(total)}</span></div>
            </div>
          </Panel>
        )}

        {line.length > 0 && (
          <div className="mt-3 rounded-lg bg-hover px-3 py-2 text-xs">
            <Badge tone="ok">locked</Badge> Within your ₹4,000 limit. The amount is final — the AI can&apos;t change it.
          </div>
        )}

        <div className="mt-4 flex gap-2">
          <Button variant="ghost" className="flex-1" onClick={() => router.push("/shop")}>← Keep shopping</Button>
          {line.length > 0 && <Button variant="primary" className="flex-1" onClick={() => router.push("/shop/checkout")}>Proceed to checkout</Button>}
        </div>
      </div>
    </AppShell>
  );
}
