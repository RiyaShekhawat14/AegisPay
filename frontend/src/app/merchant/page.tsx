"use client";
import AppShell from "@/components/AppShell";
import { Badge, Card } from "@/components";
import { useEffect, useState } from "react";
import { getProducts, getSession, Product } from "@/lib/api";

export default function MerchantDashboard() {
  const [products, setProducts] = useState<Product[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    const { token } = getSession();
    getProducts(token || undefined)
      .then(setProducts)
      .catch((e) => setError(e.message));
  }, []);

  const active = products.filter((p) => p.status === "ACTIVE").length;

  return (
    <AppShell role="merchant">
      <div className="mb-5 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold tracking-tight">Overview</h1>
          <p className="text-sm text-muted">Grow the merchant — control first.</p>
        </div>
        <Badge tone="ok">operational</Badge>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Card title="Catalog">
          <div className="text-2xl font-bold">{products.length || "—"}</div>
          <p className="text-xs text-muted">products {error ? "· API offline" : ""}</p>
        </Card>
        <Card title="Active products">
          <div className="text-2xl font-bold">{active || "—"}</div>
          <p className="text-xs text-muted">available to AI buyers</p>
        </Card>
        <Card title="Operating safely">
          <div className="text-2xl font-bold text-ok">0 blocked</div>
          <p className="text-xs text-muted">no unauthorized action</p>
        </Card>
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <Card title="Trust &amp; control">
          <ul className="space-y-2 text-sm">
            <li className="flex justify-between"><span className="text-muted">Control plane</span><Badge tone="ok">operational</Badge></li>
            <li className="flex justify-between"><span className="text-muted">Policy active</span><span className="font-semibold">policy_v1</span></li>
            <li className="flex justify-between"><span className="text-muted">Audit chain</span><Badge tone="ok">verified</Badge></li>
            <li className="flex justify-between"><span className="text-muted">Autonomy</span><span className="font-semibold">L2 · low-risk auto</span></li>
          </ul>
        </Card>
        <Card title="AI activity (demo)">
          <ul className="space-y-2 text-sm">
            <li className="flex gap-2"><span>✦</span><div><b>Opportunity detected</b><div className="text-xs text-muted">Running Shoes → Socks · affinity 34%</div></div></li>
            <li className="flex gap-2"><span>◈</span><div><b>Campaign proposed</b><div className="text-xs text-muted">Runner + Socks cross-sell · 10%</div></div></li>
            <li className="flex gap-2"><span>↻</span><div><b>Payment reconciled</b><div className="text-xs text-muted">Razorpay timeout → completed</div></div></li>
          </ul>
        </Card>
      </div>
    </AppShell>
  );
}
