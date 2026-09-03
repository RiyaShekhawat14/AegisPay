"use client";
import AppShell from "@/components/AppShell";
import { Badge, Button, Panel, PageHeader } from "@/components/ui";

const APPROVALS = [
  { action: "AI buy · Electronics bundle", amount: "₹8,999", risk: "HIGH", why: "new category + new device", expires: "in 24h" },
  { action: "Campaign · Runner + Socks", amount: "₹50,000", risk: "MED", why: "new budget envelope", expires: "in 3d" },
  { action: "Refund · duplicate charge", amount: "₹499", risk: "LOW", why: "reclaim from failed payment", expires: "in 12h" },
];

const tone = (r: string): "warn" | "neutral" | "ok" => (r === "HIGH" ? "warn" : r === "MED" ? "neutral" : "ok");

export default function ApprovalsPage() {
  return (
    <AppShell role="merchant">
      <PageHeader title="Approval inbox" crumb="3 pending · high value or risky" action={<Badge tone="warn">3 pending</Badge>} />

      <Panel title="Actions">
        <table className="w-full text-sm">
          <thead><tr className="border-b border-border text-left text-[10.5px] uppercase tracking-wide text-muted">
            <th className="py-2">Action</th><th>Amount / Risk</th><th>Why</th><th>Expires</th><th>Decide</th>
          </tr></thead>
          <tbody className="divide-y divide-border2">
            {APPROVALS.map((a) => (
              <tr key={a.action}>
                <td className="py-3 pr-4 font-semibold">{a.action}</td>
                <td className="pr-4 font-semibold tabular-nums">{a.amount} <Badge tone={tone(a.risk)}>{a.risk}</Badge></td>
                <td className="pr-4 text-xs text-muted">{a.why}</td>
                <td className="pr-4 text-xs text-muted">{a.expires}</td>
                <td className="flex gap-2">
                  <Button variant="primary" size="sm">Approve</Button>
                  <Button variant="secondary" size="sm">Reject</Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>
      <p className="mt-3 text-[11px] text-muted">Every approval is scoped to this action, expires, and can be used once. It cannot be replayed. Decisions are audited.</p>
    </AppShell>
  );
}
