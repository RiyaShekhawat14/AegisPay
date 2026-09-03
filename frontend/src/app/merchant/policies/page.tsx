"use client";
import AppShell from "@/components/AppShell";
import { Badge, Button, Panel, PageHeader } from "@/components/ui";

const RULES = [
  { rule: "Per-transaction limit", value: "₹3,000" },
  { rule: "Daily limit (per agent)", value: "₹10,000" },
  { rule: "Allowed categories", value: "food, grocery, household" },
  { rule: "Human approval above", value: "₹2,000" },
  { rule: "Blocked categories", value: "alcohol, tobacco" },
  { rule: "Allowed hours", value: "08:00 – 22:00" },
];

export default function PoliciesPage() {
  return (
    <AppShell role="merchant">
      <PageHeader title="Policies &amp; limits" crumb="deterministic and versioned" action={<><Badge tone="neutral">policy_v12</Badge><Button variant="primary">+ New version</Button></>} />

      <Panel className="mb-4" title="Immutable">
        <p className="text-xs text-muted">Immutable after publish. Only a <b>policy admin</b> can edit — never the AI. Rollback is a version switch.</p>
      </Panel>

      <Panel title="Rules">
        <table className="w-full text-sm">
          <thead><tr className="border-b border-border text-left text-[10.5px] uppercase tracking-wide text-muted">
            <th className="py-2">Rule</th><th>Value</th>
          </tr></thead>
          <tbody className="divide-y divide-border2">
            {RULES.map((r) => (
              <tr key={r.rule}><td className="py-2.5 pr-4 text-muted">{r.rule}</td><td className="font-semibold">{r.value}</td></tr>
            ))}
          </tbody>
        </table>
      </Panel>
    </AppShell>
  );
}
