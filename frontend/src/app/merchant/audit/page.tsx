"use client";
import AppShell from "@/components/AppShell";
import { Badge, Button, Panel, PageHeader } from "@/components/ui";

const EVENTS = [
  { event: "approval.approved", actor: "admin@abc", target: "order ord_11", ts: "10:42:01", id: "evt_8f9 · 12ab" },
  { event: "campaign.proposed", actor: "growth-agent", target: "cam_01 cross-sell", ts: "09:15:33", id: "evt_7c2 · 98ca" },
  { event: "policy.evaluated", actor: "system", target: "campaign cam_01", ts: "10:41:22", id: "evt_8f3 · abc123" },
  { event: "risk.assessed", actor: "system", target: "order ord_11", ts: "10:41:24", id: "evt_8f4 · def456" },
  { event: "payment.reconciled", actor: "reconcile", target: "pay_77 · ₹499", ts: "10:03:55", id: "evt_8aa · c09f" },
  { event: "agent.suspended", actor: "admin@abc", target: "shopping-agent", ts: "10:11:00", id: "evt_8bd · 7fe1" },
];

export default function AuditPage() {
  return (
    <AppShell role="merchant">
      <PageHeader title="Audit trail" crumb="append-only · hash-chained" action={<span className="flex items-center gap-1.5 text-xs text-ok"><span className="h-1.5 w-1.5 rounded-full bg-ok" />Chain integrity: <b>verified</b></span>} />

      <Panel className="mb-4">
        <div className="flex flex-wrap gap-2">
          <input className="aegis-input flex-1 min-w-48 px-3 py-1.5 text-xs" placeholder="Search events, actor, transaction…" />
          <select className="aegis-input px-2 py-1.5 text-xs"><option>All types</option></select>
          <select className="aegis-input px-2 py-1.5 text-xs"><option>Last 7 days</option></select>
        </div>
      </Panel>

      <Panel title="Events">
        <table className="aegis-table w-full text-sm">
          <thead><tr><th>Event</th><th>Actor</th><th>Target</th><th>Timestamp</th><th>Event ID</th><th>Action</th></tr></thead>
          <tbody>
            {EVENTS.map((e) => (
              <tr key={e.id}>
                <td className="font-semibold">{e.event}</td>
                <td className="text-xs text-muted">{e.actor}</td>
                <td className="text-xs">{e.target}</td>
                <td className="text-xs text-muted">{e.ts}</td>
                <td className="text-xs font-mono text-muted">{e.id}</td>
                <td><Button variant="ghost" size="sm">View</Button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>
    </AppShell>
  );
}
