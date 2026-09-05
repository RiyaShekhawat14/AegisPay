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
  crossSell?: Product[];
  added?: string;
};

// Simple intent -> category keywords, plus a cross-sell suggestion (what people also buy).
const INTENTS: { match: string[]; label: string; cross: { match: string[]; label: string } | null }[] = [
  { match: ["shoe", "sneaker", "running", "trainer", "footwear", "jog"], label: "shoes", cross: { match: ["sock"], label: "socks" } },
  { match: ["sock"], label: "socks", cross: null },
  { match: ["shirt", "tee", "apparel", "cloth"], label: "clothes", cross: null },
  { match: ["bottle", "gear"], label: "gear", cross: null },
  { match: ["bag", "messenger"], label: "bags", cross: null },
  { match: ["sticker"], label: "accessories", cross: null },
];

function matchCategory(q: string, p: Product): boolean {
  const cat = `${p.category ?? ""} ${p.name}`.toLowerCase();
  for (const it of INTENTS) {
    if (it.match.some((k) => q.includes(k))) {
      return it.match.some((k) => cat.includes(k));
    }
  }
  return true; // no recognized intent -> show everything
}

function crossSellFor(q: string, products: Product[]): Product[] {
  for (const it of INTENTS) {
    if (it.cross && it.match.some((k) => q.includes(k))) {
      return products.filter((p) => {
        const cat = `${p.category ?? ""} ${p.name}`.toLowerCase();
        return it.cross!.match.some((k) => cat.includes(k));
      });
    }
  }
  return [];
}

export default function ShopPage() {
  const [messages, setMessages] = useState<Msg[]>([
    { from: "ai", text: "Hi! Tell me what you need — e.g. “show me shoes”. I'll pull real options and suggest useful add-ons." },
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
    const all = await fetchProducts();
    setBusy(false);

    const main = all.filter((p) => matchCategory(q, p));
    const cross = crossSellFor(q, all).filter((p) => !main.some((m) => m.id === p.id));

    const mainLabel = main.length ? `Found ${main.length} for your request. Tap “Add to cart” to choose.` : "I couldn't find a match — here's everything we have.";
    const crossLabel = cross.length ? "Also, people who bought these usually add these too — want one?" : "";

    setMessages((m) => [...m, {
      from: "ai",
      text: `${mainLabel}${crossLabel ? ` ${crossLabel}` : ""} Prices are server-owned — the AI only shows them.`,
      products: main,
      crossSell: cross,
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

  function productCard(p: Product) {
    return (
      <div key={p.id} className="flex flex-col rounded-xl border border-border bg-surface p-2.5">
        <div className="flex h-24 items-center justify-center overflow-hidden rounded-lg bg-hover">
          {p.image_url ? <img src={p.image_url} alt={p.name} className="h-full w-full object-cover" /> : <span className="text-2xl">🛍️</span>}
        </div>
        <div className="mt-2 text-xs font-semibold">{p.name}</div>
        <div className="text-[10px] text-muted">{p.category ?? "general"}</div>
        <div className="mt-1 text-sm font-bold">{inr(p.price_minor)}</div>
        <Button className="mt-2 w-full" variant="secondary" size="sm" onClick={() => addToCart(p)}>
          Add to cart
        </Button>
      </div>
    );
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
                {m.text && (
                  <span dangerouslySetInnerHTML={{ __html: m.text.replace(/\*\*(.+?)\*\*/g, "<b>$1</b>") }} />
                )}
                {m.products && (
                  <div className="mt-3 grid grid-cols-2 gap-2.5 sm:grid-cols-3">
                    {m.products.map(productCard)}
                    {m.products.length === 0 && <p className="text-xs text-muted">No products match.</p>}
                  </div>
                )}
                {m.crossSell && m.crossSell.length > 0 && (
                  <div className="mt-3 rounded-xl border border-dashed border-primary/40 bg-primarySoft/40 p-2.5">
                    <div className="mb-2 text-[11px] font-semibold text-primary">✨ You might also want</div>
                    <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-3">
                      {m.crossSell.map(productCard)}
                    </div>
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
              placeholder='Ask me, e.g. "show me shoes"'
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
