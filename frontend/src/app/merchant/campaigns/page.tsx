"use client";
import AppShell from "@/components/AppShell";
import { Button, Card, Input } from "@/components";
import { useState } from "react";
import { createCampaign, getSession, inr } from "@/lib/api";

export default function CampaignsPage() {
  const [name, setName] = useState("Runner + Socks cross-sell");
  const [budget, setBudget] = useState("50000");
  const [discount, setDiscount] = useState("10");
  const [margin, setMargin] = useState("18");
  const [msg, setMsg] = useState("");
  const [created, setCreated] = useState<{ budget_minor: number; name: string } | null>(null);

  async function create(e: React.FormEvent) {
    e.preventDefault();
    const { token } = getSession();
    if (!token) return setMsg("Add an access token on the login page to create a campaign.");
    try {
      const c = await createCampaign(token, {
        agent_id: getSession().role === "merchant" ? "growth-agent" : "agent-1",
        name,
        budget_minor: Math.round(Number(budget) * 100),
        discount_pct: Number(discount),
        margin_pct: Number(margin),
        duration_days: 30,
      });
      setCreated(c);
      setMsg("");
    } catch (err) {
      setMsg((err as Error).message);
    }
  }

  return (
    <AppShell role="merchant">
      <div className="mb-5">
        <h1 className="text-xl font-bold tracking-tight">New campaign</h1>
        <p className="text-sm text-muted">AI pre-fills · merchant decides · policy caps hold</p>
      </div>

      {created && (
        <Card title="Created ✓" className="mb-4">
          <p className="text-sm">
            <b>{created.name}</b> · budget {inr(created.budget_minor)}
          </p>
          <p className="text-xs text-muted">Budget is capped — the growth agent can never overspend.</p>
        </Card>
      )}
      {msg && <p className="mb-3 text-xs text-err">{msg}</p>}

      <form onSubmit={create} className="grid gap-3 rounded-xl border border-border bg-surface p-4 md:grid-cols-2">
        <Input label="Offer name" value={name} onChange={(e) => setName(e.target.value)} />
        <Input label="Budget (₹)" type="number" value={budget} onChange={(e) => setBudget(e.target.value)} />
        <Input label="Discount (%)" type="number" value={discount} onChange={(e) => setDiscount(e.target.value)} />
        <Input label="Minimum margin (%)" type="number" value={margin} onChange={(e) => setMargin(e.target.value)} />
        <div className="md:col-span-2">
          <Button type="submit" variant="primary">Send for approval</Button>
        </div>
      </form>
    </AppShell>
  );
}
