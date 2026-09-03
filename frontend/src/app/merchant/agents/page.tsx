"use client";
import AppShell from "@/components/AppShell";
import { Badge, Chip, Panel, PageHeader } from "@/components/ui";

const AGENTS = [
  { name: "shopping-agent v3", type: "AI buyer", trust: "High", tools: "search, recommend, cart, checkout", limits: "₹2,000/txn · ₹10,000/day", status: "ACTIVE" },
  { name: "growth-agent v1", type: "Growth", trust: "High", tools: "recommend, campaign (capped)", limits: "budget cap only", status: "ACTIVE" },
];

const LEVELS = ["L0 Observe", "L1 Recommend", "L2 Auto low-risk", "L3 Delegated", "L4 Highly autonomous"];

export default function AgentsPage() {
  return (
    <AppShell role="merchant">
      <PageHeader title="Agents &amp; autonomy" crumb="who the AI is and what it may do" action={<button className="rounded-lg bg-primary px-3 py-2 text-sm font-semibold text-white">+ New agent</button>} />

      <Panel className="mb-4" title="Autonomy dial" sub="raises what the AI may propose, never its money limits">
        <div className="flex flex-wrap gap-2">
          {LEVELS.map((l, i) => (
            <span key={l} className={`rounded-md px-2 py-1 text-[10px] font-semibold ${i === 2 ? "bg-primarySoft text-primary" : "bg-hover text-muted"}`}>{l}</span>
          ))}
        </div>
      </Panel>

      <Panel title="Agents">
        <table className="w-full text-sm">
          <thead><tr className="border-b border-border text-left text-[10.5px] uppercase tracking-wide text-muted">
            <th className="py-2">Agent</th><th>Type</th><th>Trust</th><th>Allowed tools</th><th>Spend limits</th><th>Status</th>
          </tr></thead>
          <tbody className="divide-y divide-border2">
            {AGENTS.map((a) => (
              <tr key={a.name}>
                <td className="py-2.5 pr-4"><b>{a.name}</b></td>
                <td className="pr-4 text-xs">{a.type}</td>
                <td className="pr-4"><Badge tone="ok">{a.trust}</Badge></td>
                <td className="pr-4 text-xs">{a.tools}</td>
                <td className="pr-4 text-xs">{a.limits}</td>
                <td><Badge tone="ok">{a.status}</Badge></td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>
      <p className="mt-3 text-[11px] text-muted">Autonomy only broadens what the AI may propose. Money limits and policies stay deterministic.</p>
    </AppShell>
  );
}
