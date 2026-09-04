"use client";
import AppShell from "@/components/AppShell";
import { Badge, Button } from "@/components/ui";
import { useEffect, useRef, useState } from "react";

type Msg = { from: "user" | "ai"; text: string };

export default function ShopPage() {
  const [messages, setMessages] = useState<Msg[]>([
    { from: "ai", text: "Hi, I can help you shop from ABC Store. Tell me what you need and I’ll find the best option within your limits." },
  ]);
  const [input, setInput] = useState("");
  const [typing, setTyping] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, typing]);

  function send() {
    const q = input.trim();
    if (!q) return;
    setMessages((m) => [...m, { from: "user", text: q }]);
    setInput("");
    setTyping(true);
    setTimeout(() => {
      setTyping(false);
      setMessages((m) => [...m, {
        from: "ai",
        text: "Searching the store catalog… I found a few matches. Prices are real and fixed by the store — I only show them. Would you like to add one to your cart?",
      }]);
    }, 900);
  }

  return (
    <AppShell role="buyer">
      <div className="mx-auto flex h-[calc(100vh-6.5rem)] max-w-3xl flex-col">
        {/* shop bar */}
        <div className="flex items-center gap-2 border-b border-border pb-3">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-ink text-sm text-white">◈</div>
          <div className="min-w-0">
            <b className="text-sm">AegisPay · ABC Store</b>
            <div className="text-[11px] text-muted">shopping-agent v3 · <span className="text-ok">secure</span></div>
          </div>
          <span className="ml-auto flex items-center rounded-lg bg-bg px-2.5 py-1.5 text-[11px] text-muted">🔍 <span className="ml-1.5">shopping-agent v3</span></span>
        </div>

        {/* big chat area */}
        <div className="flex-1 space-y-3 overflow-y-auto py-4">
          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.from === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${m.from === "user" ? "rounded-br-md bg-ink text-white" : "rounded-bl-md border border-border bg-surface text-ink"}`}>
                {m.text}
              </div>
            </div>
          ))}
          {typing && (
            <div className="flex justify-start">
              <span className="flex items-center gap-1 rounded-2xl rounded-bl-md border border-border bg-surface px-4 py-3">
                <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-muted" style={{ animationDelay: "0ms" }} />
                <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-muted" style={{ animationDelay: "150ms" }} />
                <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-muted" style={{ animationDelay: "300ms" }} />
              </span>
            </div>
          )}
          <div ref={endRef} />
        </div>

        {/* composer */}
        <div className="border-t border-border pt-3">
          <div className="flex items-center gap-2 rounded-xl border border-border bg-surface p-1.5 focus-within:border-primary">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && send()}
              placeholder="Type a message…"
              className="flex-1 bg-transparent px-3 py-2 text-sm outline-none"
            />
            <Button variant="primary" onClick={send}>Ask</Button>
          </div>
          <p className="mt-2 text-center text-[11px] text-muted">Server-owned prices · gated checkout · the AI can&apos;t change the amount</p>
        </div>
      </div>
    </AppShell>
  );
}
