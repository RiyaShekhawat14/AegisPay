"use client";
import AppShell from "@/components/AppShell";
import { Badge, Button, Card, Input } from "@/components";
import { useState } from "react";
import { createProduct, getProducts, getSession, inr, Product } from "@/lib/api";

export default function CatalogPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [sku, setSku] = useState("");
  const [name, setName] = useState("");
  const [price, setPrice] = useState("");
  const [msg, setMsg] = useState("");

  function load() {
    const { token } = getSession();
    getProducts(token || undefined)
      .then(setProducts)
      .catch((e) => setMsg(e.message))
      .finally(() => setLoaded(true));
  }

  async function add(e: React.FormEvent) {
    e.preventDefault();
    const { token } = getSession();
    if (!token) return setMsg("Add an access token on the login page to create products.");
    const priceMinor = Math.round(Number(price) * 100);
    if (!sku || !name || Number.isNaN(priceMinor)) return setMsg("Fill name, SKU and price.");
    try {
      await createProduct(token, { sku, name, price_minor: priceMinor, category: "general" });
      setSku(""); setName(""); setPrice(""); setMsg("");
      load();
    } catch (err) {
      setMsg((err as Error).message);
    }
  }

  return (
    <AppShell role="merchant">
      <div className="mb-5 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold tracking-tight">Catalog</h1>
          <p className="text-sm text-muted">what AI buyers can see — prices are server-owned</p>
        </div>
        <Button variant="primary" onClick={load}>
          {loaded ? "Refresh" : "Load"}
        </Button>
      </div>

      <form onSubmit={add} className="mb-4 grid gap-3 rounded-xl border border-border bg-surface p-4 md:grid-cols-4">
        <Input label="Name" value={name} onChange={(e) => setName(e.target.value)} placeholder="Runner Pro" />
        <Input label="SKU" value={sku} onChange={(e) => setSku(e.target.value)} placeholder="RS-BLK-42" />
        <Input label="Price (₹)" type="number" value={price} onChange={(e) => setPrice(e.target.value)} placeholder="3499" />
        <div className="flex items-end">
          <Button type="submit" variant="primary">+ Add product</Button>
        </div>
      </form>
      {msg && <p className="mb-3 text-xs text-err">{msg}</p>}

      <Card title="Products">
        {products.length === 0 && !loaded ? (
          <p className="text-sm text-muted">Load the catalog to see products.</p>
        ) : products.length === 0 ? (
          <p className="text-sm text-muted">No products yet. Add your first.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs uppercase text-muted">
                <th className="py-2">Product</th><th>Category</th><th>Price</th><th>Status</th>
              </tr>
            </thead>
            <tbody>
              {products.map((p) => (
                <tr key={p.id} className="border-b border-border/60">
                  <td className="py-2"><b>{p.name}</b> <span className="ml-1 text-xs text-muted">{p.sku}</span></td>
                  <td className="text-xs text-muted">{p.category ?? "—"}</td>
                  <td className="font-semibold">{inr(p.price_minor)}</td>
                  <td><Badge tone={p.status === "ACTIVE" ? "ok" : "warn"}>{p.status}</Badge></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </AppShell>
  );
}
