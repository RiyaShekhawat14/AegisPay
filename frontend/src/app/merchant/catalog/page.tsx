"use client";
import AppShell from "@/components/AppShell";
import { Badge, Button, Input } from "@/components/ui";
import { Panel, PageHeader } from "@/components/ui";
import { useState, useEffect } from "react";
import { createProduct, getProducts, getSession, inr, Product } from "@/lib/api";

export default function CatalogPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [sku, setSku] = useState(""); const [name, setName] = useState(""); const [price, setPrice] = useState(""); const [image, setImage] = useState(""); const [msg, setMsg] = useState("");

  function load() {
    const { token } = getSession();
    getProducts(token || undefined).then(setProducts).catch((e) => setMsg(e.message)).finally(() => setLoaded(true));
  }

  useEffect(() => { load(); }, []);

  async function add(e: React.FormEvent) {
    e.preventDefault();
    const { token } = getSession();
    if (!token) return setMsg("Add an access token on the login page to create products.");
    const priceMinor = Math.round(Number(price) * 100);
    if (!sku || !name || Number.isNaN(priceMinor)) return setMsg("Fill name, SKU and price.");
    try {
      await createProduct(token, { sku, name, price_minor: priceMinor, category: "general", image_url: image.trim() || undefined });
      setSku(""); setName(""); setPrice(""); setImage(""); setMsg(""); load();
    } catch (err) { setMsg((err as Error).message); }
  }

  return (
    <AppShell role="merchant">
      <PageHeader
        title="Catalog"
        crumb="what AI buyers can see"
        action={<Button variant="primary" onClick={load}>{loaded ? "Refresh" : "Load"}</Button>}
      />

      <Panel className="mb-4" title="Server-owned prices">
        <p className="text-xs text-muted">Prices are owned by the store and read-only to AI. Descriptions are treated as <b>data</b>, never as instructions.</p>
      </Panel>

      <form onSubmit={add} className="mb-4 grid gap-3 rounded-[10px] border border-border bg-surface p-4 md:grid-cols-4">
        <Input label="Name" value={name} onChange={(e) => setName(e.target.value)} placeholder="Runner Pro" />
        <Input label="SKU" value={sku} onChange={(e) => setSku(e.target.value)} placeholder="RS-BLK-42" />
        <Input label="Price (₹)" type="number" value={price} onChange={(e) => setPrice(e.target.value)} placeholder="3499" />
        <Input label="Image URL" value={image} onChange={(e) => setImage(e.target.value)} placeholder="https://…/product.jpg" />
        <div className="flex items-end"><Button type="submit" variant="primary">+ Add product</Button></div>
      </form>
      {msg && <p className="mb-3 text-xs text-err">{msg}</p>}

      <Panel title="Products">
        {products.length === 0 && !loaded ? (
          <p className="text-sm text-muted">Load the catalog to see products.</p>
        ) : products.length === 0 ? (
          <p className="text-sm text-muted">No products yet. Add your first.</p>
        ) : (
          <table className="w-full text-sm">
            <thead><tr className="border-b border-border text-left text-[10.5px] uppercase tracking-wide text-muted">
              <th className="py-2">Product</th><th>Category</th><th>Price</th><th>Status</th>
            </tr></thead>
            <tbody className="divide-y divide-border2">
              {products.map((p) => (
                <tr key={p.id}>
                  <td className="py-2.5"><div className="flex items-center gap-2.5">
                    {p.image_url ? <img src={p.image_url} alt={p.name} className="h-8 w-8 rounded object-cover" /> : <div className="flex h-8 w-8 items-center justify-center rounded bg-hover text-sm">🛍️</div>}
                    <div><b>{p.name}</b> <span className="ml-1 text-xs text-muted">{p.sku}</span></div>
                  </div></td>
                  <td className="text-xs text-muted">{p.category ?? "—"}</td>
                  <td className="font-semibold tabular-nums">{inr(p.price_minor)}</td>
                  <td><Badge tone={p.status === "ACTIVE" ? "ok" : "warn"}>{p.status}</Badge></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Panel>
    </AppShell>
  );
}
