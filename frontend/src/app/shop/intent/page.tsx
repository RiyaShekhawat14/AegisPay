"use client";
import AppShell from "@/components/AppShell";
import { Badge, Panel } from "@/components/ui";

export default function IntentPage() {
  return (
    <AppShell role="buyer">
      <div className="mx-auto max-w-lg">
        <div className="mb-4 flex items-center gap-2 border-b border-border pb-3">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-ink text-sm text-white">◈</div>
          <div><b className="text-sm">Behind the scenes</b><div className="text-[11px] text-muted">how your sentence becomes a database search</div></div>
          <Badge tone="neutral" className="ml-auto">core</Badge>
        </div>

        <Panel title="What you typed">
          <p className="text-sm">“Find running shoes under ₹4,000 for daily running.”</p>
        </Panel>

        <Panel className="mt-3" title="Parsed, typed intent (JSON)">
          <pre className="overflow-x-auto rounded-lg bg-bg px-3 py-2 font-mono text-[11px] leading-relaxed">{JSON.stringify({ action: "discover & buy", product: { type: "running_shoes", category: "shoes/running" }, quantity: 1, budget_max_minor: 400000, attributes: { use_case: "daily_running" } }, null, 2)}</pre>
          <div className="mt-2 flex items-center gap-2 text-[11px] text-muted"><Badge tone="ok">validated</Badge> schema-checked before use.</div>
        </Panel>

        <Panel className="mt-3" title="Used to search the merchant catalog">
          <pre className="overflow-x-auto rounded-lg bg-bg px-3 py-2 font-mono text-[11px] leading-relaxed">{`select * from products
where tenant_id = :store and status = 'active'
  and category = 'shoes/running' and price_minor <= 400000;`}</pre>
          <div className="mt-2 text-[11px] text-muted"><Badge tone="ok">3 found</Badge> Prices come from the database — the AI never makes them up.</div>
        </Panel>
      </div>
    </AppShell>
  );
}
