"use client";
import AppShell from "@/components/AppShell";
import { Badge, Button, Panel, PageHeader } from "@/components/ui";
import { useEffect, useState } from "react";
import { approveAuthorization, getSession, inr, listPendingAuthorizations, Authorization } from "@/lib/api";

function jwtSub(token: string): string {
  try {
    const p = token.split(".")[1];
    const b = atob(p.replace(/-/g, "+").replace(/_/g, "/"));
    return (JSON.parse(decodeURIComponent(escape(b))) as { sub?: string }).sub ?? "";
  } catch {
    return "";
  }
}

const riskTone = (risk: unknown): "warn" | "neutral" => {
  const level = (risk as { level?: string } | null)?.level;
  return level === "HIGH" || level === "MEDIUM" ? "warn" : "neutral";
};

export default function ApprovalsPage() {
  const [items, setItems] = useState<Authorization[]>([]);
  const [msg, setMsg] = useState("");

  async function load() {
    const { token } = getSession();
    if (!token) return;
    try {
      setItems(await listPendingAuthorizations(token));
      setMsg("");
    } catch (e) {
      setMsg((e as Error).message);
    }
  }

  useEffect(() => { load(); }, []);

  async function approve(a: Authorization) {
    const { token } = getSession();
    const approverId = jwtSub(token || "");
    if (!token || !approverId) { setMsg("Unable to determine approver. Re-login."); return; }
    try {
      await approveAuthorization(token, a.id, approverId);
      setMsg("Approved.");
      load();
    } catch (e) {
      setMsg((e as Error).message);
    }
  }

  return (
    <AppShell role="merchant">
      <PageHeader
        title="Approval inbox"
        crumb={`${items.length} pending · high value or risky`}
        action={<><Button variant="ghost" onClick={load}>Refresh</Button><Badge tone="warn">{items.length} pending</Badge></>}
      />
      {msg && <p className="mb-3 text-xs text-err">{msg}</p>}

      <Panel title="Actions">
        {items.length === 0 ? (
          <p className="text-sm text-muted">No pending approvals right now.</p>
        ) : (
          <table className="w-full text-sm">
            <thead><tr className="border-b border-border text-left text-[10.5px] uppercase tracking-wide text-muted">
              <th className="py-2">Request</th><th>Amount / Risk</th><th>Policy</th><th>Decide</th>
            </tr></thead>
            <tbody className="divide-y divide-border2">
              {items.map((a) => (
                <tr key={a.id}>
                  <td className="py-3 pr-4 font-semibold">AI purchase</td>
                  <td className="pr-4 font-semibold tabular-nums">{inr(a.amount_minor)} <Badge tone={riskTone(a.risk)}>{((a.risk as { level?: string } | null)?.level ?? "risk")}</Badge></td>
                  <td className="pr-4 text-xs text-muted">{a.policy_version}</td>
                  <td className="flex gap-2">
                    <Button variant="primary" size="sm" onClick={() => approve(a)}>Approve</Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Panel>
      <p className="mt-3 text-[11px] text-muted">Every approval is scoped to this action, expires, and can be used once. It cannot be replayed. Decisions are audited.</p>
    </AppShell>
  );
}
