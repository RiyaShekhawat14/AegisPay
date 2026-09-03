"use client";
import AppShell from "@/components/AppShell";
import { Badge, Button, Card } from "@/components";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { addCartItem, createCart, getProducts, getSession, inr, Product } from "@/lib/api";

const CART_KEY = "aegispay.cart";

function readCart(): { cartId: string; items: Record<string, number> } {
  if (typeof window === "undefined") return { cartId: "", items: {} };
  try {
    return JSON.parse(localStorage.getItem(CART_KEY) ?? '{"cartId":"","items":{}}');
  } catch {
    return { cartId: "", items: {} };
  }
}

export default function ShopPage() {
  const router = useRouter();
  const [products, setProducts] = useState<Product[]>([]);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    const { token } = getSession();
    getProducts(token || undefined)
      .then(setProducts)
      .catch(() => setProducts(DEMO));
  }, []);

  async function add(p: Product, quantity = 1) {
    const cart = readCart();
    const { token } = getSession();
    if (!token) {
      // demo: no token -> client-side cart
      cart.items[p.id] = (cart.items[p.id] ?? 0) + quantity;
      localStorage.setItem(CART_KEY, JSON.stringify(cart));
      setMsg(`Added ${p.name} to cart (demo).`);
      return;
    }
    try {
      let cartId = cart.cartId;
      if (!cartId) {
        const c = await createCart(token, "shopping-agent");
        cartId = c.id;
        localStorage.setItem(CART_KEY, JSON.stringify({ cartId, items: cart.items }));
      }
      await addCartItem(token, cartId, p.id, quantity);
      setMsg(`Added ${p.name} to cart.`);
    } catch (err) {
      setMsg((err as Error).message);
    }
  }

  return (
    <AppShell role="buyer">
      <div className="mb-5 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold tracking-tight">Find products</h1>
          <p className="text-sm text-muted">real store prices — the AI only shows them, never sets them</p>
        </div>
        <Button variant="primary" onClick={() => router.push("/shop/cart")}>View cart →</Button>
      </div>
      {msg && <p className="mb-3 text-xs text-ok">{msg}</p>}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {products.map((p) => (
          <Card key={p.id} className="flex flex-col">
            <div className="mb-2 flex h-20 items-center justify-center rounded-lg bg-hover text-3xl">🛍️</div>
            <div className="font-semibold">{p.name}</div>
            <div className="text-xs text-muted">{p.category ?? "general"} · {p.status}</div>
            <div className="mt-1 text-lg font-bold">{inr(p.price_minor)}</div>
            <Button className="mt-3" variant="secondary" onClick={() => add(p)}>Add to cart</Button>
          </Card>
        ))}
        {products.length === 0 && (
          <Card className="sm:col-span-3"><p className="text-sm text-muted">No products found.</p></Card>
        )}
      </div>
    </AppShell>
  );
}

// Offline/demo catalog so the SELL UI is navigable without the control plane running.
const DEMO: Product[] = [
  { id: "p1", sku: "RS-42", name: "Runner Pro 42", category: "shoes/running", price_minor: 349900, currency: "INR", status: "ACTIVE" },
  { id: "p2", sku: "SR-40", name: "Street Run 40", category: "shoes/running", price_minor: 279900, currency: "INR", status: "ACTIVE" },
  { id: "p3", sku: "SK-3", name: "Run Sock 3-pack", category: "apparel/socks", price_minor: 49900, currency: "INR", status: "ACTIVE" },
  { id: "p4", sku: "TB-42", name: "T-Shirt Classic", category: "apparel", price_minor: 79900, currency: "INR", status: "ACTIVE" },
];
