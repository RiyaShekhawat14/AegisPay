"use client";
import AppShell from "@/components/AppShell";
import { Badge, Button } from "@/components/ui";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { addCartItem, createCart, getProducts, getSession, inr, Product } from "@/lib/api";

const CART_KEY = "aegispay.cart";
type Msg = {
  from: "user" | "ai";
  text?: string;
  products?: Product[];
  added?: string;
};

export default function ShopPage() {
  const [messages, setMessages] = useState<Msg[]>([
    { from: "ai", text: "Hi, I can help you shop. Ask to see the products currently in this store." },
  ]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);
  const tokenRef = useRef(getSession().token);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  async function fetchProducts(): Promise<Product[]> {
    const { token } = getSession();
    try {
      return await getProducts(token || undefined);
    } catch {
      return [];
    }
  }

  async function send() {
    const q = input.trim();
    if (!q || busy) return;
    setMessages((m) => [...m, { from: "user", text: q }]);
    setInput("");
    setBusy(true);
    // This is the "AI is reasoning via the control plane" beat.
    const results = await fetchProducts();
    setBusy(false);
    setMessages((m) => [...m, {
      from: "ai",
      text: `Here’s what’s in the store${q ? ` for: “${q}”` : ""}. Prices are server-owned — the AI only shows them. Tap “Add to cart” to choose.`,
      products: results,
    }]);
  }

  async function addToCart(p: Product) {
    const cart = JSON.parse(localStorage.getItem(CART_KEY) ?? '{"cartId":"","items":{}}') as { cartId: string; items: Record<string, number> };
    const { token, agentId } = getSession();
    if (!token || !agentId) {
      setMessages((m) => [...m, { from: "ai", text: "Please sign in and configure an active agent before adding items to a cart." }]);
      return;
    }
    try {
      let cartId = cart.cartId;
      if (!cartId) {
        const c = await createCart(token, agentId);
        cartId = c.id;
        localStorage.setItem(CART_KEY, JSON.stringify({ cartId, items: cart.items }));
      }
      await addCartItem(token, cartId, p.id, 1);
      cart.items[p.id] = (cart.items[p.id] ?? 0) + 1;
      localStorage.setItem(CART_KEY, JSON.stringify({ cartId, items: cart.items }));
      setMessages((m) => [...m, { from: "ai", text: `Added **${p.name}** (${inr(p.price_minor)}) to your cart.` }]);
    } catch {
      setMessages((m) => [...m, { from: "ai", text: "I couldn’t add that item. Please check the control plane and try again." }]);
    }
  }

  return (
    <AppShell role="buyer">
      <div className="mx-auto flex h-[calc(100vh-6.5rem)] max-w-4xl flex-col">
        <div className="flex items-center gap-2 border-b border-border pb-3">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-ink text-sm text-white">◈</div>
          <div className="min-w-0">
            <b className="text-sm">AegisPay store</b>
            <div className="text-[11px] text-muted">secure checkout</div>
          </div>
          <Link href="/shop/cart" className="ml-auto rounded-lg border border-border bg-surface px-3 py-1.5 text-xs font-semibold transition hover:bg-hover">
            🛒 View cart →
          </Link>
        </div>

        <div className="flex-1 space-y-3 overflow-y-auto py-4">
          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.from === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[85%] ${m.from === "user" ? "" : "min-w-[70%]"} rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${m.from === "user" ? "rounded-br-md bg-ink text-white" : "rounded-bl-md border border-border bg-surface text-ink"}`}>
                {m.text && m.text.includes("**") ? (
                  <span dangerouslySetInnerHTML={{ __html: m.text.replace(/\*\*(.+?)\*\*/g, "<b>$1</b>") }} />
                ) : (
                  <span>{m.text}</span>
                )}
                {m.products && (
                  <div className="mt-3 grid grid-cols-2 gap-2.5 sm:grid-cols-3">
                    {m.products.map((p) => (
                      <div key={p.id} className="flex flex-col rounded-xl border border-border bg-surface p-2.5">
                        <div className="flex h-14 items-center justify-center rounded-lg bg-hover text-2xl">🛍️</div>
                        <div className="mt-2 text-xs font-semibold">{p.name}</div>
                        <div className="text-[10px] text-muted">{p.category ?? "general"} · {p.status}</div>
                        <div className="mt-1 text-sm font-bold">{inr(p.price_minor)}</div>
                        <Button className="mt-2 w-full" variant={m.added ? "primary" : "secondary"} size="sm" onClick={() => addToCart(p)}>
                          {m.added ? "Added ✓" : "Add to cart"}
                        </Button>
                      </div>
                    ))}
                    {m.products.length === 0 && <p className="text-xs text-muted">No products yet.</p>}
                  </div>
                )}
              </div>
            </div>
          ))}
          {busy && (
            <div className="flex justify-start">
              <span className="flex items-center gap-1 rounded-2xl rounded-bl-md border border-border bg-surface px-4 py-3">
                <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-muted" />
                <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-muted" style={{ animationDelay: "150ms" }} />
                <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-muted" style={{ animationDelay: "300ms" }} />
              </span>
            </div>
          )}
          <div ref={endRef} />
        </div>

        <div className="border-t border-border pt-3">
          <div className="flex items-center gap-2 rounded-xl border border-border bg-surface p-1.5 focus-within:border-primary">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && send()}
              placeholder='Ask me to show products, e.g. "show running shoes under ₹4,000"'
              className="flex-1 bg-transparent px-3 py-2 text-sm outline-none"
            />
            <Button variant="primary" onClick={send} disabled={busy}>Ask</Button>
          </div>
          <p className="mt-2 text-center text-[11px] text-muted">Server-owned prices · gated checkout · the AI can’t change the amount</p>
        </div>
      </div>
    </AppShell>
  );
}
