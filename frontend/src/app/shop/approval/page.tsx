"use client";
import AppShell from "@/components/AppShell";
import { Badge, Button, Panel } from "@/components/ui";
import { useRouter } from "next/navigation";

export default function ApprovalPage() {
  const router = useRouter();
  return (
    <AppShell role="buyer">
      <div className="mx-auto max-w-md">
        <div className="mb-4 flex items-center gap-2 border-b border-border pb-3">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-ink text-sm text-white">◈</div>
          <div><b className="text-sm">Approval needed</b><div className="text-[11px] text-muted">a person must confirm</div></div>
          <span className="ml-auto flex items-center gap-1.5 rounded-md bg-warnSoft px-2 py-1 text-[10.5px] font-semibold text-warn">⏱ expires 00:24:10</span>
        </div>

        <Panel title="Amount · high risk">
          <div className="flex items-center gap-2 text-xl font-bold">₹8,999 <Badge tone="warn">HIGH</Badge></div>
          <div className="mt-1 text-xs text-muted">Electronics bundle · first in category · new device · new merchant</div>
        </Panel>

        <div className="mt-3 grid grid-cols-2 gap-3">
          <div className="rounded-lg bg-bg p-3">
            <div className="text-[10px] font-semibold uppercase tracking-wide text-muted">Who wants this</div>
            <div className="text-sm font-semibold">shopping-agent v3</div>
          </div>
          <div className="rounded-lg bg-bg p-3">
            <div className="text-[10px] font-semibold uppercase tracking-wide text-muted">Policy</div>
            <div className="text-sm font-semibold">policy_v12</div>
          </div>
        </div>

        <div className="mt-3 rounded-lg bg-hover px-3 py-2 text-xs">
          <Badge tone="warn" className="mr-1">why here?</Badge> Above your auto-limit, so a human decides.
        </div>

        <Button variant="primary" className="mt-4 w-full" onClick={() => router.push("/shop/success")}>Approve this purchase</Button>
        <Button variant="secondary" className="mt-2 w-full" onClick={() => router.push("/shop")}>Reject with reason</Button>
        <p className="mt-2 text-center text-[11px] text-muted">Scoped to this cart · expires · can’t be reused</p>
      </div>
    </AppShell>
  );
}
