"use client";
import AppShell from "@/components/AppShell";
import { Badge, Button, Chip, Kpi, Panel, Pipeline, Row, Table } from "@/components/ui";
import { useEffect, useState } from "react";
import { getProducts, getSession, inr, Product } from "@/lib/api";

const STEPS = ["AI proposes", "Validates", "Policy", "Risk", "Approve", "Pay"];

export default function MerchantDashboard() {
  const [products, setProducts] = useState<Product[]>([]);

  useEffect(() => {
    const { token } = getSession();
    getProducts(token || undefined)
      .then(setProducts)
      .catch(() => setProducts([]));
  }, []);

  const active = products.filter((p) => p.status === "ACTIVE").length;

  return (
    <AppShell role="merchant">
      <div className="mb-5 overflow-hidden rounded-2xl border border-border bg-gradient-to-br from-surface to-primarySoft p-6">
        <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-primary">AegisPay · Merchant Console</div>
        <h1 className="mt-2 text-2xl font-bold tracking-tight">Grow the merchant — control first.</h1>
        <p className="mt-1 max-w-xl text-sm text-muted">
          One workspace to let AI help revenue, with a deterministic control plane between the AI and money. Red only for actions and active state.
        </p>
      </div>

      <div className="mb-4 flex flex-wrap items-center gap-3">
        <div className="ml-auto flex items-center gap-2 text-xs text-muted">
          <span className="h-1.5 w-1.5 rounded-full bg-ok" /> control plane operational
        </div>
      </div>

      <Pipeline steps={STEPS} active={0} />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Kpi label="Total GMV" value="₹4.8L" delta="▲ 12% vs prior 30d" note="organic + AI" />
        <Kpi label="AI-driven revenue" chip="AI" value="₹1.6L" delta="▲ 34%" note="attributed, not assumed" />
        <Kpi label="Needs attention" value="4" delta="▲ 3 approvals queued" deltaTone="warn" note="awaiting your decision" />
        <Kpi label="Operating safely" value={<span className="text-ok">0 blocked</span>} delta="3,412 checks passed" note="no unauthorized action" />
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-3">
        <Panel title="Revenue" sub="GMV by source" className="lg:col-span-2">
          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-lg border border-border p-3">
              <div className="text-xs text-muted">Organic</div>
              <div className="mt-1 text-lg font-bold">₹3.3L</div>
              <div className="text-[11px] text-muted">baseline, unchanged</div>
            </div>
            <div className="rounded-lg border border-border p-3">
              <div className="flex items-center gap-1.5 text-xs text-muted">AI-generated <Chip tone="ai">AI</Chip></div>
              <div className="mt-1 text-lg font-bold">₹1.0L</div>
              <div className="text-[11px] text-ok">▲ 22%</div>
            </div>
          </div>
          <div className="mt-4 flex h-20 items-end gap-3 px-1">
            <div className="flex-1 rounded bg-border2" style={{ height: "44%" }} />
            <div className="flex-1 rounded bg-border2" style={{ height: "62%" }} />
            <div className="flex-1 rounded bg-border2" style={{ height: "54%" }} />
            <div className="flex-1 rounded bg-border2" style={{ height: "70%" }} />
            <div className="flex-1 rounded bg-border2" style={{ height: "84%" }} />
            <div className="flex-1 rounded bg-primary" style={{ height: "76%" }} />
            <div className="flex-1 rounded bg-primary" style={{ height: "92%" }} />
          </div>
          <div className="mt-2 text-[11px] text-muted">Last segment from an AI campaign (A/B). Gray = organic; red = AI-led.</div>
        </Panel>

        <div className="space-y-4">
          <Panel title="Trust &amp; control">
            <ul className="space-y-2 text-xs">
              <TrustRow label="Control plane" value={<span className="flex items-center gap-1.5"><span className="h-1.5 w-1.5 rounded-full bg-ok" />operational</span>} />
              <TrustRow label="Policy active" value={<span className="font-semibold">policy_v12</span>} />
              <TrustRow label="Kill switch" value={<span className="flex items-center gap-1.5"><span className="h-1.5 w-1.5 rounded-full bg-ok" />armed</span>} />
              <TrustRow label="Audit chain" value={<span className="text-ok">verified</span>} />
              <TrustRow label="Autonomy" value={<span>L2 · low-risk auto</span>} />
            </ul>
          </Panel>
          <Panel title="Limits" sub="shopping-agent">
            <div className="flex justify-between text-xs"><span className="text-muted">Per transaction</span><span className="font-semibold">₹3,000</span></div>
            <div className="mt-2 flex justify-between text-xs"><span className="text-muted">Daily</span><span className="font-semibold">₹10,000</span></div>
          </Panel>
        </div>
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <Panel title="AI activity" action={<Chip tone="ai">AI</Chip>} sub="live">
          <div className="divide-y divide-border2">
            <Row icon="✦" iconTone="info" time="2m" meta="Running Shoes → Socks · affinity 34%">Opportunity detected</Row>
            <Row icon="◈" iconTone="warn" time="8m" meta="Runner + Socks cross-sell · 10% · ₹50k">Campaign proposed</Row>
            <Row icon="◈" iconTone="warn" time="12m" meta="₹8,999 · Electronics bundle">Approval requested</Row>
            <Row icon="↻" iconTone="ok" time="31m" meta="₹499 · Razorpay timeout → completed">Payment reconciled</Row>
          </div>
        </Panel>

        <Panel title="Recently approved" sub="human decisions">
          <Table headers={["Item", "Amount", "Risk", "Decided"]}>
            <tr><td className="py-2 pr-4">Office chair · ergonomic</td><td className="pr-4 font-semibold">₹6,499</td><td className="pr-4"><Badge tone="warn">HIGH</Badge></td><td className="text-muted">2h ago</td></tr>
            <tr><td className="py-2 pr-4">Monitor 27&quot; QHD</td><td className="pr-4 font-semibold">₹4,200</td><td className="pr-4"><Badge tone="neutral">MED</Badge></td><td className="text-muted">6h ago</td></tr>
            <tr><td className="py-2 pr-4">Socks 3-pack</td><td className="pr-4 font-semibold">₹500</td><td className="pr-4"><Badge tone="ok">LOW</Badge></td><td className="text-muted">1d ago</td></tr>
          </Table>
        </Panel>
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-3">
        <span className="text-xs text-muted">Catalog: {products.length} products · {active} active</span>
        <div className="ml-auto flex gap-2">
          <Button variant="secondary" size="sm">Export</Button>
          <Button variant="primary" size="sm">+ Add product</Button>
        </div>
      </div>
    </AppShell>
  );
}

function TrustRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <li className="flex items-center justify-between border-t border-border2 pt-2 first:border-0 first:pt-0">
      <span className="w-28 text-muted">{label}</span>
      <span className="text-xs">{value}</span>
    </li>
  );
}
