"use client";
import AppShell from "@/components/AppShell";
import { Panel } from "@/components/ui";

const TL = [
  { t: "10:41:20 · Intent", v: "“Find running shoes under ₹4,000”", hash: "sha256 abc…" },
  { t: "10:41:21 · Cart", v: "Runner Pro + Socks · locked", hash: "sha256 def…" },
  { t: "10:41:23 · Policy", v: "ALLOW · policy_v12", hash: "policy_v12" },
  { t: "10:41:24 · Risk", v: "21 / LOW", hash: "risk_scored" },
  { t: "10:41:25 · Authorization", v: "bound to cart · valid", hash: "authz_valid" },
  { t: "10:41:26 · Order", v: "order_xxx · ₹3,998", hash: "cart_hash" },
  { t: "10:41:26 · Payment", v: "Razorpay initiated", hash: "pay_yyy" },
  { t: "10:41:28 · Webhook verified", v: "payment.succeeded", hash: "verified" },
  { t: "10:41:28 · Passport", v: "verified", hash: "anchored" },
];

export default function AuditTimelinePage() {
  return (
    <AppShell role="buyer">
      <div className="mx-auto max-w-lg">
        <div className="mb-4 flex items-center gap-2 border-b border-border pb-3">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-ink text-sm text-white">◈</div>
          <div><b className="text-sm">Transaction audit trail</b><div className="text-[11px] text-muted">txn_82931 · every step recorded</div></div>
          <span className="ml-auto flex items-center gap-1.5 text-xs text-ok"><span className="h-1.5 w-1.5 rounded-full bg-ok" /><b>Chain integrity: verified</b><span className="text-muted">· anchored</span></span>
        </div>

        <div className="ml-3 border-l-2 border-border2 pl-4 ">
          {TL.map((e, i) => (
            <div key={e.t} className={`relative pb-4 ${i === TL.length - 1 ? "pb-0" : ""}`}>
              <span className={`absolute -left-[21px] top-1.5 h-2.5 w-2.5 rounded-full border-2 ${i < TL.length ? "border-ok bg-surface" : "border-border bg-surface"}`} />
              <div className="text-[10px] font-semibold uppercase tracking-wide text-muted">{e.t}</div>
              <div className="text-sm font-semibold">{e.v}</div>
              <div className="font-mono text-[10.5px] text-muted">{e.hash}</div>
            </div>
          ))}
        </div>
      </div>
    </AppShell>
  );
}
