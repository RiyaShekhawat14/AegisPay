"use client";
import AppShell from "@/components/AppShell";
import { Badge, Button, Chip, Panel, PageHeader } from "@/components/ui";
import { useState } from "react";
import { generateOpportunities, getOpportunities, getSession, Opportunity } from "@/lib/api";

export default function OpportunitiesPage() {
  const [items, setItems] = useState<Opportunity[]>([]);
  const [msg, setMsg] = useState("");

  function load() {
    const { token } = getSession();
    getOpportunities(token || undefined).then(setItems).catch((e) => setMsg(e.message));
  }
  async function generate() {
    const { token } = getSession();
    if (!token) return setMsg("Add an access token on the login page to generate opportunities.");
    try {
      const list = await generateOpportunities(token, "growth-agent");
      setItems(list); setMsg("");
    } catch (e) { setMsg((e as Error).message); }
  }

  return (
    <AppShell role="merchant">
      <PageHeader
        title="Growth opportunities"
        crumb="detected from real purchase affinity"
        action={<><Button variant="ghost" onClick={load}>Refresh</Button><Button variant="primary" onClick={generate}>Generate (AI)</Button></>}
      />
      {msg && <p className="mb-3 text-xs text-err">{msg}</p>}

      <Panel title="Suggestions" action={<Chip tone="ai">AI</Chip>}>
        {items.length === 0 ? (
          <p className="text-sm text-muted">No opportunities yet. Generate suggestions from your catalog.</p>
        ) : (
          <div className="divide-y divide-border2">
            {items.map((o, i) => (
              <div key={o.id} className="flex flex-wrap items-center gap-3 py-3 first:pt-0 last:pb-0">
                <div className="w-12 text-right text-xl font-bold">{Math.round((o.confidence ?? 0) * 100)}%</div>
                <div className="min-w-0 flex-1">
                  <div className="text-sm font-semibold">Cross-sell · {o.kind}</div>
                  <div className="text-[11px] text-muted">anchor: {o.anchor_product ?? "—"} · confidence {o.confidence ?? 0} · {i === 0 ? "last 90 days" : "last 90 days"}</div>
                </div>
                <Badge tone={i === 0 ? "ok" : i === 1 ? "ok" : "neutral"}>{i < 2 ? "High value" : "Review"}</Badge>
                <Button variant={i < 2 ? "primary" : "ghost"} size="sm">{i < 2 ? "Create campaign" : "See reasons"}</Button>
              </div>
            ))}
          </div>
        )}
      </Panel>
      <p className="mt-3 text-[11px] text-muted">The AI proposes. It cannot run anything here — you decide, and fixed rules stay in force.</p>
    </AppShell>
  );
}
