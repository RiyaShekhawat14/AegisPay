"use client";
import AppShell from "@/components/AppShell";
import { Badge, Kpi, Panel, PageHeader } from "@/components/ui";

export default function AnalyticsPage() {
  return (
    <AppShell role="merchant">
      <PageHeader title="Revenue analytics" crumb="last 30 days" action={<Badge tone="neutral">A/B controlled</Badge>} />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Kpi label="AI-generated" chip="AI" value="₹1.01L" delta="▲ 22%" />
        <Kpi label="AI-assisted" value="₹48K" delta="▲ 9%" />
        <Kpi label="Organic" value="₹3.31L" delta="baseline" deltaTone="warn" />
        <Kpi label="Attribution" value={<span className="text-base">honest split</span>} note="no double-counting" />
      </div>

      <Panel className="mt-4" title="Conversion &amp; uplift" sub="test vs control">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Kpi label="Conversion uplift" value="+6.4%" note="vs control" />
          <Kpi label="AOV uplift" value="+3%" />
          <Kpi label="Campaign ROI" value="3.1x" />
          <Kpi label="Margin after discount" value="19%" note="+1%" />
        </div>
      </Panel>

      <p className="mt-4 text-[11px] text-muted">Honest incrementality with a control group; AI impact is labelled, not implied.</p>
    </AppShell>
  );
}
