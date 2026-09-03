"use client";
import AppShell from "@/components/AppShell";
import { Badge, Button, Card } from "@/components";
import { useState } from "react";
import { generateOpportunities, getOpportunities, getSession, Opportunity } from "@/lib/api";

export default function OpportunitiesPage() {
  const [items, setItems] = useState<Opportunity[]>([]);
  const [msg, setMsg] = useState("");

  function load() {
    const { token } = getSession();
    getOpportunities(token || undefined)
      .then(setItems)
      .catch((e) => setMsg(e.message));
  }

  async function generate() {
    const { token } = getSession();
    if (!token) return setMsg("Add an access token on the login page to generate opportunities.");
    try {
      const list = await generateOpportunities(token, getSession().role === "merchant" ? "growth-agent" : "agent-1");
      setItems(list);
      setMsg("");
    } catch (err) {
      setMsg((err as Error).message);
    }
  }

  return (
    <AppShell role="merchant">
      <div className="mb-5 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold tracking-tight">Growth opportunities</h1>
          <p className="text-sm text-muted">detected from real purchase affinity</p>
        </div>
        <div className="flex gap-2">
          <Button variant="ghost" onClick={load}>Refresh</Button>
          <Button variant="primary" onClick={generate}>Generate (AI)</Button>
        </div>
      </div>
      {msg && <p className="mb-3 text-xs text-err">{msg}</p>}

      <Card title="Suggestions">
        {items.length === 0 ? (
          <p className="text-sm text-muted">No opportunities yet. Generate suggestions from your catalog.</p>
        ) : (
          <ul className="divide-y divide-border/60 text-sm">
            {items.map((o) => (
              <li key={o.id} className="flex items-center gap-3 py-2">
                <div className="w-12 text-right text-xl font-bold">{Math.round((o.confidence ?? 0) * 100)}%</div>
                <div className="flex-1">
                  <div className="font-semibold">Cross-sell · {o.kind}</div>
                  <div className="text-xs text-muted">anchor: {o.anchor_product ?? "—"} · confidence {o.confidence ?? 0}</div>
                </div>
                <Badge tone={o.status === "OPEN" ? "ok" : "warn"}>{o.status}</Badge>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </AppShell>
  );
}
