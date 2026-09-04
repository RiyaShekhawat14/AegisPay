-- AegisPay v1 schema. One shared database, many merchants.
-- Money is BIGINT minor units. Every tenant-owned table has tenant_id and RLS.
-- The application role cannot bypass RLS; a separate migration role owns DDL.

create extension if not exists pgcrypto;

-- ---- identity & tenants ----
create table if not exists tenants (
  id uuid primary key default gen_random_uuid(),
  slug text not null unique,
  name text not null,
  currency char(3) not null default 'INR',
  status text not null default 'ACTIVE',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists users (
  id uuid primary key default gen_random_uuid(),
  email text not null unique,
  password_hash text not null,
  tenant_id uuid references tenants(id),
  role text not null default 'member',
  status text not null default 'ACTIVE',
  created_at timestamptz not null default now()
);

create table if not exists tenant_users (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id),
  user_id uuid not null references users(id),
  role text not null,
  created_at timestamptz not null default now(),
  unique (tenant_id, user_id)
);

create table if not exists agents (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id),
  owner_user uuid references users(id),
  name text not null,
  type text not null,
  version text,
  scopes jsonb not null default '[]'::jsonb,
  allowed_tools jsonb not null default '[]'::jsonb,
  trust_level text not null default 'HIGH',
  status text not null default 'ACTIVE',
  expires_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists agent_sessions (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id),
  agent_id uuid not null references agents(id),
  session_key text not null,
  started_at timestamptz not null default now(),
  ended_at timestamptz,
  revoked_at timestamptz
);

-- ---- commerce (SELL) ----
create table if not exists products (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id),
  sku text not null,
  name text not null,
  category text,
  price_minor bigint not null check (price_minor >= 0),
  currency char(3) not null default 'INR',
  status text not null default 'ACTIVE',
  agent_safe_summary text,
  meta jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (tenant_id, sku)
);

create table if not exists carts (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id),
  agent_id uuid not null references agents(id),
  status text not null default 'CREATED',
  currency char(3) not null default 'INR',
  cart_hash text,
  price_version text,
  total_minor bigint not null default 0,
  expires_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists cart_items (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id),
  cart_id uuid not null references carts(id),
  product_id uuid not null references products(id),
  quantity int not null check (quantity > 0),
  unit_price_minor bigint not null,
  line_total_minor bigint not null,
  created_at timestamptz not null default now()
);

create table if not exists inventory_reservations (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id),
  product_id uuid not null references products(id),
  cart_id uuid not null references carts(id),
  quantity int not null check (quantity > 0),
  reserved_until timestamptz not null,
  status text not null default 'RESERVED',
  created_at timestamptz not null default now()
);

create table if not exists orders (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id),
  cart_id uuid not null references carts(id),
  agent_id uuid not null references agents(id),
  authorization_id uuid,
  cart_hash text not null,
  policy_version text not null,
  currency char(3) not null default 'INR',
  total_minor bigint not null,
  status text not null default 'CREATED',
  intent jsonb,
  idempotency_key text unique,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists order_items (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id),
  order_id uuid not null references orders(id),
  product_id uuid references products(id),
  product_snapshot jsonb not null,
  quantity int not null check (quantity > 0),
  unit_price_minor bigint not null,
  line_total_minor bigint not null,
  created_at timestamptz not null default now()
);

-- ---- control & safety ----
create table if not exists policies (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id),
  name text not null,
  version int not null,
  status text not null default 'ACTIVE',
  rules jsonb not null default '{}'::jsonb,
  effective_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  unique (tenant_id, name, version)
);

create table if not exists authorizations (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id),
  agent_id uuid not null references agents(id),
  user_id uuid references users(id),
  cart_id uuid not null references carts(id),
  cart_hash text not null,
  amount_minor bigint not null,
  currency char(3) not null default 'INR',
  policy_version text not null,
  status text not null default 'VALID',
  single_use boolean not null default true,
  expires_at timestamptz not null,
  used_at timestamptz,
  risk jsonb,
  created_at timestamptz not null default now()
);

create table if not exists approvals (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id),
  authorization_id uuid not null references authorizations(id),
  order_id uuid references orders(id),
  scope_hash text not null,
  approver_id uuid references users(id),
  decision text,
  reason text,
  status text not null default 'PENDING',
  expires_at timestamptz not null,
  created_at timestamptz not null default now()
);

-- ---- payments ----
create table if not exists payments (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id),
  order_id uuid not null references orders(id),
  amount_minor bigint not null,
  currency char(3) not null default 'INR',
  provider text not null,
  provider_order_id text,
  provider_payment_id text,
  capture_id text,
  status text not null default 'CREATED',
  idempotency_key text unique,
  attempt_count int not null default 0,
  unknown_since timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists refunds (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id),
  payment_id uuid not null references payments(id),
  amount_minor bigint not null check (amount_minor > 0),
  currency char(3) not null default 'INR',
  reason text,
  status text not null default 'PENDING',
  provider_refund_id text,
  idempotency_key text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists webhook_events (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id),
  provider text not null,
  provider_event_id text not null,
  event_type text,
  payload jsonb,
  payload_hash text,
  signature_verified boolean not null default false,
  status text not null default 'RECEIVED',
  created_at timestamptz not null default now(),
  unique (provider, provider_event_id)
);

-- ---- growth (GROW) ----
create table if not exists opportunities (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id),
  agent_id uuid not null references agents(id),
  kind text not null,
  anchor_product uuid references products(id),
  target_products jsonb not null default '[]'::jsonb,
  affinity numeric(5,4),
  confidence numeric(5,4),
  status text not null default 'OPEN',
  created_at timestamptz not null default now()
);

create table if not exists campaigns (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id),
  agent_id uuid not null references agents(id),
  name text not null,
  status text not null default 'DRAFT',
  budget_minor bigint not null,
  spent_minor bigint not null default 0,
  discount_pct numeric(5,2),
  min_margin_pct numeric(5,2),
  targeting jsonb not null default '{}'::jsonb,
  ab_config jsonb not null default '{}'::jsonb,
  policy_version text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists campaign_budget_ledger (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id),
  campaign_id uuid not null references campaigns(id),
  amount_minor bigint not null,
  kind text not null,
  idempotency_key text,
  created_at timestamptz not null default now()
);

-- ---- platform reliability ----
create table if not exists idempotency_keys (
  tenant_id uuid not null,
  scope text not null,
  key text not null,
  request_hash text,
  response jsonb,
  status text not null default 'IN_PROGRESS',
  expires_at timestamptz,
  created_at timestamptz not null default now(),
  primary key (tenant_id, scope, key)
);

create table if not exists outbox_events (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id),
  aggregate_type text not null,
  aggregate_id text not null,
  event_type text not null,
  payload jsonb not null default '{}'::jsonb,
  published_at timestamptz,
  created_at timestamptz not null default now()
);

create table if not exists audit_events (
  id bigserial primary key,
  tenant_id uuid not null references tenants(id),
  event_id uuid not null default gen_random_uuid(),
  event_type text not null,
  actor_type text not null,
  actor_id text,
  correlation_id text,
  transaction_id text,
  payload jsonb not null default '{}'::jsonb,
  prev_hash text not null default '',
  event_hash text not null,
  created_at timestamptz not null default now()
);

-- ---- indexes (tenant-prefixed) ----
create index if not exists orders_tenant_id_idx on orders (tenant_id, status);
create index if not exists orders_tenant_id_created_at_idx on orders (tenant_id, created_at);
create index if not exists payments_tenant_id_status_idx on payments (tenant_id, status);
create index if not exists payments_order_id_idx on payments (order_id);
create index if not exists refunds_tenant_id_status_idx on refunds (tenant_id, status);
create index if not exists campaigns_tenant_id_status_idx on campaigns (tenant_id, status);
create index if not exists agents_tenant_id_status_idx on agents (tenant_id, status);
create index if not exists webhook_events_tenant_id_status_idx on webhook_events (tenant_id, status);
create index if not exists audit_events_tenant_id_created_at_idx on audit_events (tenant_id, created_at);
create index if not exists outbox_events_published_at_idx on outbox_events (published_at) where published_at is null;
create index if not exists cart_items_cart_id_idx on cart_items (cart_id);
create index if not exists order_items_order_id_idx on order_items (order_id);
create index if not exists inventory_reservations_product_id_status_idx on inventory_reservations (product_id, status);

-- ---- rows-level security (application role cannot bypass) ----
create or replace function current_tenant() returns uuid
  language sql stable as $$ select nullif(current_setting('app.tenant_id', true), '')::uuid $$;

do $$
declare t text;
begin
  foreach t in array array['tenant_users','agents','agent_sessions','products','carts','cart_items',
    'inventory_reservations','orders','order_items','policies','authorizations','approvals',
    'payments','refunds','webhook_events','opportunities','campaigns','campaign_budget_ledger',
    'outbox_events'] loop
    execute format('alter table %I enable row level security', t);
    execute format('drop policy if exists tenant_isolation on %I', t);
    execute format($p$ create policy tenant_isolation on %I
      for all using (tenant_id = current_tenant())
      with check (tenant_id = current_tenant()) $p$, t);
  end loop;
end $$;

-- audit_events is append-only for the application role
alter table audit_events enable row level security;
drop policy if exists audit_isolation on audit_events;
create policy audit_isolation on audit_events
  for select using (tenant_id = current_tenant());
-- allow the app role to append (WITH CHECK scopes it to its tenant); update/delete stay revoked
drop policy if exists audit_insert on audit_events;
create policy audit_insert on audit_events
  for insert with check (tenant_id = current_tenant());

-- ---- application role grants ----
-- The app role (created in db/init.sql) does DML only. It is NOT a superuser and has no
-- BYPASSRLS, so RLS on every tenant-owned table is a hard boundary.
grant select, insert, update, delete on all tables in schema public to aegispay_app;
grant usage on all sequences in schema public to aegispay_app;

-- audit_events is append-only for the app role (no update / delete)
revoke update, delete on audit_events from aegispay_app;
