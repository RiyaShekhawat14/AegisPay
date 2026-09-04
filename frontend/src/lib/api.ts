// Typed API client for the AegisPay control plane.
const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const TIMEOUT_MS = 5000;

type Role = "buyer" | "merchant";

export type Product = {
  id: string;
  sku: string;
  name: string;
  category?: string | null;
  price_minor: number;
  currency: string;
  status: string;
};

export type Opportunity = {
  id: string;
  kind: string;
  anchor_product: string | null;
  target_products: unknown[];
  confidence: number | null;
  status: string;
};

export type Campaign = {
  id: string;
  name: string;
  status: string;
  budget_minor: number;
  spent_minor: number;
};

export type Cart = {
  id: string;
  status: string;
  currency: string;
  total_minor: number;
  cart_hash: string | null;
  items: { product_id: string; quantity: number; unit_price_minor: number; line_total_minor: number }[];
};

export type Order = { id: string; cart_id: string; status: string; total_minor: number; currency: string; cart_hash: string };

export type Authorization = { id: string; cart_id: string; status: string; amount_minor: number; currency: string };

export async function api<T>(path: string, init?: RequestInit & { token?: string }): Promise<T> {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), TIMEOUT_MS);
  try {
    const res = await fetch(`${BASE}${path}`, {
      ...init,
      signal: ctrl.signal,
      headers: {
        "Content-Type": "application/json",
        ...(init?.token ? { Authorization: `Bearer ${init.token}` } : {}),
        ...(init?.headers ?? {}),
      },
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body?.message ?? body?.detail ?? `Request failed: ${res.status}`);
    }
    return res.json() as Promise<T>;
  } finally {
    clearTimeout(timer);
  }
}

// Graceful degradation: true only when the control plane is actually reachable.
export async function controlPlaneUp(): Promise<boolean> {
  try {
    const r = await api<{ status: string }>("/v1/health");
    return r.status === "ok";
  } catch {
    return false;
  }
}

export const getProducts = (token?: string) => api<Product[]>("/v1/products", { token });
export const getOpportunities = (token?: string) => api<Opportunity[]>("/v1/opportunities", { token });
export const createProduct = (token: string, body: { sku: string; name: string; price_minor: number; category?: string }) =>
  api<Product>("/v1/products", { method: "POST", token, body: JSON.stringify(body) });
export const generateOpportunities = (token: string, agentId: string) =>
  api<Opportunity[]>("/v1/opportunities/generate", { method: "POST", token, body: JSON.stringify({ agent_id: agentId }) });
export const createCampaign = (
  token: string,
  body: { agent_id: string; name: string; budget_minor: number; discount_pct: number; margin_pct: number; duration_days: number },
) => api<Campaign>("/v1/campaigns", { method: "POST", token, body: JSON.stringify(body) });
export const createCart = (token: string, agentId: string) =>
  api<Cart>("/v1/carts", { method: "POST", token, body: JSON.stringify({ agent_id: agentId }) });
export const addCartItem = (token: string, cartId: string, productId: string, quantity: number) =>
  api<Cart>(`/v1/carts/${cartId}/items`, { method: "POST", token, body: JSON.stringify({ product_id: productId, quantity }) });
export const checkout = (token: string, cartId: string) => api<Order>(`/v1/carts/${cartId}/checkout`, { method: "POST", token });
export const requestAuthorization = (token: string, cartId: string) =>
  api<Authorization>("/v1/authorizations", { method: "POST", token, body: JSON.stringify({ cart_id: cartId }) });

// Client-side session (auth is token-based; login/signup issues a JWT).
const ROLE_KEY = "aegispay.role";
const TOKEN_KEY = "aegispay.token";
const AGENT_KEY = "aegispay.agent";

export function saveSession(role: Role, token = "", agentId = "") {
  localStorage.setItem(ROLE_KEY, role);
  localStorage.setItem(TOKEN_KEY, token);
  if (agentId) localStorage.setItem(AGENT_KEY, agentId);
}
export function getSession(): { role: Role | null; token: string; agentId: string } {
  if (typeof window === "undefined") return { role: null, token: "", agentId: "" };
  return {
    role: (localStorage.getItem(ROLE_KEY) as Role | null) ?? null,
    token: localStorage.getItem(TOKEN_KEY) ?? "",
    agentId: localStorage.getItem(AGENT_KEY) ?? "",
  };
}
export function clearSession() {
  localStorage.removeItem(ROLE_KEY);
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(AGENT_KEY);
}

export function inr(minor: number): string {
  return `₹${(minor / 100).toLocaleString("en-IN")}`;
}
