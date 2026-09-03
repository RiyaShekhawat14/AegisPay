"use client";
import AppShell from "@/components/AppShell";
import { Badge, Button, Panel } from "@/components/ui";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { addCartItem, createCart, getProducts, getSession, inr, Product } from "@/lib/api";
import { Card, Input } from "@/components";

const CART_KEY = "aegispay.cart";
function readCart(): { cartId: string; items: Record<string, number> } {
  if (typeof window === "undefined") return { cartId: "", items: {} };
  try { return JSON.parse(localStorage.getItem(CART_KEY) ?? '{"cartId":"","items":{}}'); } catch { return { cartId: "", items: {} }; }
}

export default function ShopPage() {
  const router = useRouter();
  const [products, setProducts] = useState<Product[]>([]);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    const { token } = getSession();
    getProducts(token || undefined).then(setProducts).catch(() => setProducts(DEMO));
  }, []);

  async function add(p: Product, quantity = 1) {
    const cart = readCart();
    const { token } = getSession();
    if (!token) {
      cart.items[p.id] = (cart.items[p.id] ?? 0) + quantity;
      localStorage.setItem(CART_KEY, JSON.stringify(cart));
      setMsg(`Added ${p.name} to cart (demo).`);
      return;
    }
    try {
      let cartId = cart.cartId;
      if (!cartId) { const c = await createCart(token, "shopping-agent"); cartId = c.id; localStorage.setItem(CART_KEY, JSON.stringify({ cartId, items: cart.items })); }
      await addCartItem(token, cartId, p.id, quantity);
      setMsg(`Added ${p.name} to cart.`);
    } catch (err) { setMsg((err as Error).message); }
  }

  return (
    <AppShell role="buyer">
      <div className="mx-auto max-w-2xl">
        <div className="mb-4 flex items-center gap-2 border-b border-border pb-3">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-ink text-sm text-white">◈</div>
          <div><b className="text-sm">AegisPay · ABC Store</b><div className="text-[11px] text-muted">shopping-agent v3 · <span className="text-ok">secure</span></div></div>
          <div className="ml-auto flex h-8 w-8 items-center justify-center rounded-full bg-hover">👤</div>
        </div>

        <div className="mb-3 space-y-2">
          <div className="max-w-[85%] rounded-lg border border-border bg-surface px-3 py-2 text-sm">Hi, I can help you shop from <b>ABC Store</b>. Tell me what you need and I’ll find the best option within your limits.</div>
          <div className="ml-auto max-w-[85%] rounded-lg bg-ink px-3 py-2 text-sm text-white">Find running shoes under ₹4,000 for daily running.</div>
          <div className="max-w-[85%] rounded-lg border border-border bg-surface px-3 py-2 text-sm text-muted">Prices are real and fixed by the store — the AI only shows them.</div>
        </div>

        <div className="mb-4 flex items-center gap-2">
          <Input placeholder="Type a message…" className="flex-1" />
          <Button variant="primary">Ask</Button>
        </div>
        {msg && <p className="mb-3 text-xs text-ok">{msg}</p>}

        <Panel title="Best matches" sub="3 found under ₹4,000">
          <div className="grid grid-cols-2 gap-3">
            {products.map((p) => (
              <div key={p.id} className="flex flex-col rounded-lg border border-border p-2.5">
                <div className="flex h-16 items-center justify-center rounded-lg bg-hover text-2xl">🛍️</div>
                <div className="mt-2 text-sm font-semibold">{p.name}</div>
                <div className="text-[10px] text-muted">{p.category ?? "general"} · in stock</div>
                <div className="mt-1 text-sm font-bold">{inr(p.price_minor)}</div>
                <Button className="mt-2 w-full" size="sm" onClick={() => add(p)}>Add to cart</Button>
              </div>
            ))}
          </div>
        </Panel>
        <div className="mt-3 flex items-center justify-center">
          <Button variant="primary" onClick={() => router.push("/shop/cart")}>View cart →</Button>
        </div>
      </div>
    </AppShell>
  );
}

const DEMO: Product[] = [
  { id: "p1", sku: "RS-42", name: "Runner Pro 42", category: "shoes/running", price_minor: 349900, currency: "INR", status: "ACTIVE" },
  { id: "p2", sku: "SR-40", name: "Street Run 40", category: "shoes/running", price_minor: 279900, currency: "INR", status: "ACTIVE" },
  { id: "p3", sku: "SK-3", name: "Run Sock 3-pack", category: "apparel/socks", price_minor: 49900, currency: "INR", status: "ACTIVE" },
  { id: "p4", sku: "TS-1", name: "T-Shirt Classic", category: "apparel", price_minor: 79900, currency: "INR", status: "ACTIVE" },
];
