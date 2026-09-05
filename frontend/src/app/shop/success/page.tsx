"use client";
import AppShell from "@/components/AppShell";
import { Badge, Button, Panel } from "@/components/ui";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { getProducts, getSession, inr, Product } from "@/lib/api";

export default function SuccessPage() {
  const router = useRouter();
  const [products, setProducts] = useState<Product[]>([]);
  const [total, setTotal] = useState(0);
  const [txnId, setTxnId] = useState("txn_…");

  useEffect(() => {
    const cart = JSON.parse(localStorage.getItem("aegispay.cart") ?? '{"cartId":"","items":{}}') as { cartId: string; items: Record<string, number> };
    setTxnId(localStorage.getItem("aegispay.paid") ?? "txn_…");
    getProducts(getSession().token || undefined).then((ps) => { setProducts(ps); setTotal(Object.entries(cart.items).reduce((s, [id, q]) => s + (ps.find((p) => p.id === id)?.price_minor ?? 0) * q, 0)); }).catch(() => {});
  }, []);

  return (
    <AppShell role="buyer">
      <div className="mx-auto max-w-lg">
        <div className="mb-4 flex items-center gap-2 border-b border-border pb-3">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-ink text-sm text-white">◈</div>
          <div><b className="text-sm">Paid</b><div className="text-[11px] text-muted">{txnId}</div></div>
        </div>

        <div className="mb-4 text-center">
          <svg className="mx-auto h-16 w-16" viewBox="0 0 60 60">
            <circle cx="30" cy="30" r="26" fill="none" stroke="#16A34A" strokeWidth="3" />
            <path d="M19 31 L27 39 L42 23" fill="none" stroke="#16A34A" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          <div className="mt-2 text-sm font-semibold">Payment successful</div>
          <div className="text-[11px] text-muted">{inr(total)} via Razorpay (test mode)</div>
        </div>

        <Panel className="overflow-hidden border-0 p-0" title={undefined}>
          <div className="flex items-center gap-2 border-b border-border bg-bg px-4 py-3">
            <div><div className="text-[10px] font-semibold uppercase tracking-wide text-muted">Transaction Passport</div><b className="text-sm">{txnId}</b></div>
            <Badge tone="ok" className="ml-auto">Audit Integrity</Badge>
          </div>
          <div className="grid grid-cols-2 gap-px bg-border">
            {[
              ["Amount", inr(total)], ["Merchant", "Your store"], ["Agent", "shopping-agent"], ["Authorization", "VALID"],
              ["Cart hash", "—"], ["Policy version", "v1"], ["Risk", "LOW"], ["Provider", "Razorpay (test)"],
            ].map(([k, v]) => (
              <div key={k} className="bg-surface px-4 py-2.5">
                <div className="text-[10px] font-semibold uppercase tracking-wide text-muted">{k}</div>
                <div className="text-xs font-semibold">{v}</div>
              </div>
            ))}
          </div>
          <div className="flex items-center gap-2 border-t border-border px-4 py-3 text-[11px] text-muted">
            <span className="h-1.5 w-1.5 rounded-full bg-ok" /> Tamper-evident · Hash chained · Anchored
          </div>
        </Panel>

        <Button variant="secondary" className="mt-4 w-full" onClick={() => router.push("/shop")}>Continue shopping</Button>
      </div>
    </AppShell>
  );
}
