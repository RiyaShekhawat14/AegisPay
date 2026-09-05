"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import { clearSession, controlPlaneUp, getSession } from "@/lib/api";

type Role = "buyer" | "merchant";
type NavItem = { href: string; label: string; icon: string; pill?: string };

const NAV: Record<Role, { group: string; items: NavItem[] }[]> = {
  merchant: [
    {
      group: "Commerce",
      items: [
        { href: "/merchant", label: "Dashboard", icon: "▦" },
        { href: "/merchant/catalog", label: "Catalog", icon: "▪" },
        { href: "/merchant/agents", label: "Agents", icon: "⚙" },
      ],
    },
    {
      group: "Growth",
      items: [
        { href: "/merchant/opportunities", label: "Opportunities", icon: "◇" },
        { href: "/merchant/campaigns", label: "Campaigns", icon: "▣" },
      ],
    },
    {
      group: "Control",
      items: [
        { href: "/merchant/approvals", label: "Approvals", icon: "✓", pill: "3" },
        { href: "/merchant/policies", label: "Policies", icon: "◈" },
        { href: "/merchant/analytics", label: "Analytics", icon: "◫" },
        { href: "/merchant/audit", label: "Audit", icon: "◷" },
      ],
    },
  ],
  buyer: [
    {
      group: "Shop",
      items: [
        { href: "/shop", label: "Find products", icon: "🔍" },
        { href: "/shop/intent", label: "How it works", icon: "◈" },
        { href: "/shop/cart", label: "Your cart", icon: "🛒" },
        { href: "/shop/checkout", label: "Checkout", icon: "▸" },
        { href: "/shop/approval", label: "Approval", icon: "✓" },
        { href: "/shop/audit-timeline", label: "Audit trail", icon: "◷" },
      ],
    },
  ],
};

export default function AppShell({ role, children }: { role: Role; children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [ready, setReady] = useState(false);
  const [offline, setOffline] = useState(false);

  useEffect(() => {
    const s = getSession();
    if (s.role !== role) router.replace("/login");
    else setReady(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [role]);

  useEffect(() => {
    let alive = true;
    controlPlaneUp().then((up) => { if (alive) setOffline(!up); });
    const id = setInterval(() => {
      controlPlaneUp().then((up) => { if (alive) setOffline(!up); });
    }, 15000);
    return () => { alive = false; clearInterval(id); };
  }, []);

  function logout() {
    clearSession();
    router.replace("/login");
  }

  const brand = role === "merchant" ? { mark: "◈", title: "AegisPay", sub: "MERCHANT CONSOLE" } : { mark: "◈", title: "AegisPay", sub: "AI BUYER" };

  return (
    <div className="min-h-screen bg-bg text-ink">
      <div className="flex min-h-screen">
        <aside className="hidden w-[200px] shrink-0 border-r border-border bg-surface px-2.5 py-3.5 md:block">
          <div className="mb-4 flex items-center gap-2 px-2 pb-4">
            <div className="flex h-6.5 w-6.5 h-7 w-7 items-center justify-center rounded-lg bg-ink text-sm text-white">{brand.mark}</div>
            <div>
              <div className="text-[13px] font-bold leading-tight">{brand.title}</div>
              <div className="text-[9px] tracking-wide text-muted">{brand.sub}</div>
            </div>
          </div>

          {NAV[role].map((g) => (
            <div key={g.group}>
              <div className="px-2 pb-1 pt-2.5 text-[10px] font-semibold uppercase tracking-wide text-muted">{g.group}</div>
              {g.items.map((item) => {
                const active = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`relative flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-[12.5px] transition ${
                      active ? "bg-primarySoft font-semibold text-primary" : "text-ink/70 hover:bg-hover"
                    }`}
                  >
                    {active && <span className="absolute -left-2.5 inset-y-1.5 w-0.5 rounded bg-primary" />}
                    <span className="w-4 text-center opacity-85">{item.icon}</span>
                    <span className="flex-1">{item.label}</span>
                    {item.pill && <span className="rounded-md bg-errSoft px-1.5 py-0.5 text-[10px] font-semibold text-err">{item.pill}</span>}
                  </Link>
                );
              })}
            </div>
          ))}

          <div className="mt-6 border-t border-border pt-2">
            <button onClick={logout} className="w-full rounded-lg px-2.5 py-2 text-left text-[12.5px] text-muted hover:bg-hover">
              ↪ Log out
            </button>
          </div>
        </aside>

        <div className="flex min-w-0 flex-1 flex-col">
          {offline && (
            <div className="flex items-center gap-2 border-b border-warnSoft bg-warnSoft px-5 py-2 text-xs font-semibold text-warn">
              <span className="h-1.5 w-1.5 rounded-full bg-warn" /> Control plane unreachable. Live data is unavailable.
            </div>
          )}
          <header className="flex items-center gap-3 border-b border-border bg-surface px-5 py-3">
            <div className="text-[11px] text-muted md:hidden">{brand.sub}</div>
            <div className="flex-1" />
            <div className="hidden w-[220px] items-center rounded-lg bg-bg px-3 py-1.5 text-xs text-muted md:flex">
              🔍 Search orders, products…
            </div>
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-ink text-xs font-semibold text-white">
              {role === "merchant" ? "A" : "B"}
            </div>
          </header>
          {ready ? <main className="p-6">{children}</main> : <main className="p-6" />}
        </div>
      </div>
    </div>
  );
}
