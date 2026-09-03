"use client";
import AppShell from "@/components/AppShell";
import { Badge, Button, Chip, Input, Panel, PageHeader } from "@/components/ui";
import { useState } from "react";
import { createCampaign, getSession } from "@/lib/api";

const POLICY = [
  { rule: "Max discount", value: "10%", cap: "12%", ok: true },
  { rule: "Max budget", value: "₹50,000", cap: "₹1,00,000", ok: true },
  { rule: "Min margin", value: "18%", cap: "18%", ok: true },
];

export default function CampaignsPage() {
  const [name, setName] = useState("Runner + Socks cross-sell");
  const [budget, setBudget] = useState("50000"); const [discount, setDiscount] = useState("10"); const [margin, setMargin] = useState("18");
  const [msg, setMsg] = useState(""); const [created, setCreated] = useState<{ name: string; budget_minor: number } | null>(null);

  async function create(e: React.FormEvent) {
    e.preventDefault();
    const { token } = getSession();
    if (!token) return setMsg("Add an access token on the login page to create a campaign.");
    try {
      const c = await createCampaign(token, { agent_id: "growth-agent", name, budget_minor: Math.round(Number(budget) * 100), discount_pct: Number(discount), margin_pct: Number(margin), duration_days: 30 });
      setCreated(c); setMsg("");
    } catch (err) { setMsg((err as Error).message); }
  }

  return (
    <AppShell role="merchant">
      <PageHeader title="New campaign" crumb="drafted by the growth agent" action={<Chip tone="ai">AI</Chip>} />

      <Panel className="mb-4" title="Why this offer?" sub="growth-agent v1">
        <p className="text-sm">34% of buyers of <b>Running Shoes</b> also bought <b>Running Socks</b> (last 90 days).</p>
        <p className="mt-1 text-[11px] text-muted">Estimated uplift <b>+3% to +8%</b> — a range, not a promise</p>
      </Panel>

      <form onSubmit={create} className="grid gap-3 rounded-[10px] border border-border bg-surface p-4 md:grid-cols-2">
        <Input label="Offer name" value={name} onChange={(e) => setName(e.target.value)} />
        <Input label="Budget (₹)" type="number" value={budget} onChange={(e) => setBudget(e.target.value)} />
        <Input label="Discount (%)" type="number" value={discount} onChange={(e) => setDiscount(e.target.value)} />
        <Input label="Minimum margin (%)" type="number" value={margin} onChange={(e) => setMargin(e.target.value)} />
        <div className="md:col-span-2 flex items-center gap-2">
          <Button type="submit" variant="primary">Send for approval</Button>
          <Button type="button" variant="secondary">Save draft</Button>
          <span className="ml-auto text-[11px] text-muted">AI approved suggestion · merchant decides</span>
        </div>
      </form>
      {msg && <p className="mt-3 text-xs text-err">{msg}</p>}
      {created && (
        <Panel className="mt-4" title="✓ Created" action={<Badge tone="ok">OK</Badge>}>
          <p className="text-sm"><b>{created.name}</b> · budget ₹{(created.budget_minor / 100).toLocaleString("en-IN")}</p>
          <p className="text-xs text-muted">Budget is capped — the growth agent can never overspend.</p>
        </Panel>
      )}

      <Panel className="mt-4" title="Policy check" sub="validated before anything runs">
        <table className="w-full text-sm">
          <thead><tr className="border-b border-border text-left text-[10.5px] uppercase tracking-wide text-muted">
            <th className="py-2">Rule</th><th>Value</th><th>Cap</th><th>Verdict</th>
          </tr></thead>
          <tbody className="divide-y divide-border2">
            {POLICY.map((p) => (
              <tr key={p.rule}>
                <td className="py-2.5 pr-4">{p.rule}</td><td className="pr-4 font-semibold">{p.value}</td><td className="pr-4 text-muted">{p.cap}</td>
                <td><Badge tone="ok">OK</Badge></td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>
    </AppShell>
  );
}
