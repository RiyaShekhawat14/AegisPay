"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { clearSession, getSession } from "@/lib/api";
import type { ReactNode } from "react";
import { useEffect, useState } from "react";

type Role = "buyer" | "merchant";

const NAV: Record<Role, { href: string; label: string; icon: string }[]> = {
  merchant: [
    { href: "/merchant", label: "Dashboard", icon: "▦" },
    { href: "/merchant/catalog", label: "Catalog", icon: "▪" },
    { href: "/merchant/opportunities", label: "Opportunities", icon: "◇" },
    { href: "/merchant/campaigns", label: "Campaigns", icon: "▣" },
  ],
  buyer: [
    { href: "/shop", label: "Find products", icon: "🔍" },
    { href: "/shop/cart", label: "Cart", icon: "🛒" },
  ],
};

export default function AppShell({ role, children }: { role: Role; children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const s = getSession();
    if (s.role !== role) router.replace("/login");
    else setReady(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [role]);

  function logout() {
    clearSession();
    router.replace("/login");
  }

  const brand = role === "merchant" ? { title: "AegisPay", sub: "MERCHANT CONSOLE" } : { title: "AegisPay", sub: "AI BUYER" };

  return (
    <div className="min-h-screen bg-bg text-ink">
      <div className="flex min-h-screen">
        <aside className="hidden w-52 shrink-0 border-r border-border bg-surface p-3 md:block">
          <div className="mb-4 flex items-center gap-2 px-2 pt-1">
            <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-ink text-xs text-white">◈</div>
            <div>
              <div className="text-sm font-bold leading-tight">{brand.title}</div>
              <div className="text-[9px] tracking-wide text-muted">{brand.sub}</div>
            </div>
          </div>
          <nav className="space-y-1 text-sm">
            {NAV[role].map((item) => {
              const active = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-2 rounded-lg px-2 py-2 transition ${
                    active ? "bg-primary/5 font-semibold text-primary" : "text-ink/80 hover:bg-hover"
                  }`}
                >
                  <span className="w-4 text-center">{item.icon}</span>
                  {item.label}
                </Link>
              );
            })}
          </nav>
          <div className="mt-6 space-y-1 text-sm">
            <button onClick={logout} className="w-full rounded-lg px-2 py-2 text-left text-muted hover:bg-hover">
              ↪ Log out
            </button>
          </div>
        </aside>

        <div className="flex min-w-0 flex-1 flex-col">
          <header className="flex items-center gap-3 border-b border-border bg-surface px-5 py-3">
            <div className="text-[11px] text-muted md:hidden">{brand.sub}</div>
            <div className="flex-1" />
            <div className="hidden items-center rounded-lg bg-bg px-3 py-1.5 text-xs text-muted md:flex">
              Search orders, products…
            </div>
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-ink text-xs font-semibold text-white">
              {role === "merchant" ? "A" : "B"}
            </div>
          </header>
          {ready ? <main className="p-5">{children}</main> : <main className="p-5" />}
        </div>
      </div>
    </div>
  );
}
