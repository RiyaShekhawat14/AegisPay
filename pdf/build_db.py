import subprocess
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer,
                                Image, Table, TableStyle, PageBreak, KeepTogether,
                                ListFlowable, ListItem, Preformatted)

ROOT = Path(r"C:\Users\hp\OneDrive\Desktop\AgeisPay")
BUILD = ROOT / "pdf" / "_build_db"
BUILD.mkdir(parents=True, exist_ok=True)
MMDC = r"C:\Users\hp\AppData\Roaming\npm\node_modules\@mermaid-js\mermaid-cli\src\cli.js"

D = {
"er_commerce": r"""
erDiagram
  TENANTS ||--o{ PRODUCTS : owns
  TENANTS ||--o{ CARTS : owns
  CARTS ||--o{ CART_ITEMS : contains
  CART_ITEMS }o--|| PRODUCTS : references
  TENANTS ||--o{ INVENTORY_RESERVATIONS : owns
  INVENTORY_RESERVATIONS }o--|| PRODUCTS : reserves
  TENANTS ||--o{ ORDERS : owns
  ORDERS ||--o{ ORDER_ITEMS : has
  ORDER_ITEMS }o--|| PRODUCTS : snapshot
  CARTS ||--o| ORDERS : becomes
  TENANTS {
    uuid id PK
    text slug
    char currency
    text status
  }
  PRODUCTS {
    uuid id PK
    uuid tenant_id FK
    text sku
    bigint price_minor
    text status
  }
  CARTS {
    uuid id PK
    uuid tenant_id FK
    text cart_hash
    bigint total_minor
    text status
  }
  ORDERS {
    uuid id PK
    uuid tenant_id FK
    text policy_version
    text status
  }
""",
"er_trust": r"""
erDiagram
  TENANTS ||--o{ TENANT_USERS : has
  USERS ||--o{ TENANT_USERS : member
  TENANTS ||--o{ AGENTS : owns
  TENANTS ||--o{ POLICIES : owns
  TENANTS ||--o{ AUTHORIZATIONS : grants
  AUTHORIZATIONS }o--|| ORDERS : binds
  TENANTS ||--o{ APPROVALS : has
  TENANTS ||--o{ WEBHOOK_EVENTS : receives
  TENANTS ||--o{ IDEMPOTENCY_KEYS : namespaced
  TENANTS ||--o{ OUTBOX_EVENTS : emits
  TENANTS ||--o{ AUDIT_EVENTS : records
""",
"er_growth": r"""
erDiagram
  TENANTS ||--o{ AGENTS : owns
  AGENTS ||--o{ OPPORTUNITIES : detects
  OPPORTUNITIES ||--o{ CAMPAIGNS : launches
  CAMPAIGNS ||--o{ CAMPAIGN_BUDGET_LEDGER : ledger
""",
"rls": r"""
flowchart LR
  APP[App role - DML only] --> DB[(Shared PostgreSQL)]
  MIG[Migration role - owns tables] --> DB
  DB --> R[Row Level Security]
  R --> S["SET LOCAL app.tenant_id"]
  S --> T1[Merchant A sees only A rows]
  S --> T2[Merchant B sees only B rows]
""",
"outbox": r"""
flowchart TD
  TX[DB transaction] --> ST[Business update]
  TX --> OB[Insert outbox_event]
  OB --> WK[Outbox worker]
  WK --> Q[SQS]
""",
"paystate": r"""
stateDiagram-v2
  [*] --> CREATED
  CREATED --> CART_LOCKED
  CART_LOCKED --> AUTHORIZATION_PENDING
  AUTHORIZATION_PENDING --> AUTHORIZED
  AUTHORIZATION_PENDING --> AUTHORIZATION_EXPIRED
  AUTHORIZATION_PENDING --> PRICE_CHANGED
  AUTHORIZATION_PENDING --> INVENTORY_EXPIRED
  AUTHORIZED --> PAYMENT_PENDING
  PAYMENT_PENDING --> PAID: provider confirms
  PAYMENT_PENDING --> PAYMENT_FAILED
  PAYMENT_PENDING --> PAYMENT_UNKNOWN: timeout
  PAYMENT_UNKNOWN --> PAID: reconcile finds success
  PAYMENT_UNKNOWN --> PAYMENT_FAILED: reconcile finds failed
  PAYMENT_UNKNOWN --> ORDER_FAILED: still unknown
  PAID --> ORDER_CONFIRMED
  PAID --> REFUND_PENDING
  REFUND_PENDING --> REFUNDED
""",
"audit": r"""
flowchart LR
  E1[Event 1] --> E2[Event 2]
  E2 --> E3[Event 3]
  E3 --> AN[Anchor]
  E1 -. hash .-> E2
  E2 -. hash .-> E3
""",
}

def render(text, name):
    mmd=BUILD/(name+".mmd"); png=BUILD/(name+".png"); mmd.write_text(text.strip(),encoding="utf-8")
    if png.exists(): png.unlink()
    try:
        subprocess.run(["node",MMDC,"-q","-i",str(mmd),"-o",str(png),"-t","neutral"],check=True,capture_output=True)
    except subprocess.CalledProcessError as e: raise RuntimeError(f"{name}: {e.stderr.decode()[:400]}")
    if not png.exists(): raise RuntimeError(f"mmdc failed {name}")
    return png
for n,s in D.items(): render(s,n)
print("Rendered",len(D),"diagrams")

LR=15*mm; TB=13*mm
ACC=colors.HexColor("#8B1E3F"); INK=colors.HexColor("#17181C"); MUT=colors.HexColor("#667085")
BORD=colors.HexColor("#E5E7EB"); NEUT=colors.HexColor("#F4F5F7"); OK=colors.HexColor("#15803D")
st=getSampleStyleSheet()
H1=ParagraphStyle("H1",parent=st["Heading1"],fontName="Helvetica-Bold",fontSize=16,textColor=ACC,spaceAfter=6,spaceBefore=2)
H2=ParagraphStyle("H2",parent=st["Heading2"],fontName="Helvetica-Bold",fontSize=12.6,textColor=INK,spaceAfter=5,spaceBefore=12)
H3=ParagraphStyle("H3",parent=st["Heading3"],fontName="Helvetica-Bold",fontSize=10.8,textColor=colors.HexColor("#4A2430"),spaceAfter=3,spaceBefore=8)
BODY=ParagraphStyle("Body",parent=st["BodyText"],fontName="Helvetica",fontSize=9.8,leading=14,spaceAfter=5,textColor=INK)
LI=ParagraphStyle("LI",parent=BODY,leftIndent=13,spaceAfter=3)
CAP=ParagraphStyle("Cap",parent=BODY,fontSize=8.4,leading=11,textColor=MUT,alignment=TA_CENTER,spaceBefore=2,spaceAfter=9)
CALL=ParagraphStyle("Call",parent=BODY,fontName="Helvetica-Bold",fontSize=10,leading=14.5,textColor=ACC,backColor=colors.HexColor("#FDF6F7"),borderPadding=7,borderWidth=0.6,borderColor=colors.HexColor("#E7BCCA"),spaceAfter=7)
TITLE=ParagraphStyle("Title",parent=st["Title"],fontName="Helvetica-Bold",fontSize=20,textColor=INK,alignment=TA_CENTER,leading=27,spaceAfter=5)
SUB=ParagraphStyle("Sub",parent=BODY,fontSize=11.5,textColor=ACC,alignment=TA_CENTER,spaceAfter=2)
TH=ParagraphStyle("th",parent=BODY,fontName="Helvetica-Bold",fontSize=7.9,textColor=INK,leading=10.5)
TD=ParagraphStyle("td",parent=BODY,fontName="Helvetica",fontSize=7.7,leading=10.5,textColor=INK)
NOTE=ParagraphStyle("note",parent=BODY,fontSize=8.8,leading=12.3,textColor=MUT)
CODE=ParagraphStyle("code",parent=BODY,fontName="Courier",fontSize=7.1,leading=8.9,textColor=INK,spaceBefore=4)

def para(t,s=BODY): return Paragraph(t,s)
def bullets(it): return ListFlowable([ListItem(Paragraph(t,LI),leftIndent=12) for t in it],bulletType="bullet",start="&#8226;",leftIndent=12,bulletFontSize=8,spaceAfter=5)
def numbered(it): return ListFlowable([ListItem(Paragraph(t,LI),leftIndent=15) for t in it],bulletType="1",start=1,leftIndent=15,spaceAfter=5)
def table(rows,widths):
    data=[[Paragraph(c,TH) for c in rows[0]]]
    for r in rows[1:]: data.append([Paragraph(c,TD) for c in r])
    t=Table(data,colWidths=widths,hAlign="LEFT",repeatRows=1)
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),NEUT),("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#FAFAFB")]),
      ("GRID",(0,0),(-1,-1),0.4,BORD),("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),4),
      ("RIGHTPADDING",(0,0),(-1,-1),4),("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3)]))
    return t
def image_flow(path,max_w=178*mm):
    from PIL import Image as PILImage
    iw,ih=PILImage.open(path).size; r=ih/float(iw); w=min(max_w,iw/4.0); return Image(str(path),width=w,height=w*r)
def diag(name,cap): return KeepTogether([Spacer(1,3),image_flow(BUILD/(name+".png")),Paragraph(cap,CAP)])
def block(ddl): return Preformatted(ddl,CODE)

def onp(c,d):
    c.saveState(); c.setFont("Helvetica",7.6); c.setFillColor(MUT)
    c.drawString(LR,7.5*mm,"AegisPay · Production Database Schema V1")
    c.drawRightString(A4[0]-LR,7.5*mm,f"Page {d.page}")
    c.setStrokeColor(BORD); c.setLineWidth(.5); c.line(LR,12*mm,A4[0]-LR,12*mm); c.restoreState()
frame=Frame(LR,TB,A4[0]-2*LR,A4[1]-2*TB,id="n",leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)
out=ROOT/"AegisPay-Database-Schema-V1.pdf"
doc=BaseDocTemplate(str(out),pagesize=A4,leftMargin=LR,rightMargin=LR,topMargin=TB,bottomMargin=TB,title="AegisPay Database Schema V1",author="AegisPay Engineering")
doc.addPageTemplates([PageTemplate(id="all",frames=[frame],onPage=onp)])

F=[Spacer(1,20), para("AEGISPAY",TITLE), para("Production Database Schema V1",SUB),
   Spacer(1,8), para("One shared PostgreSQL database for many merchants, secured with Row-Level Security, designed to be simple, auditable, idempotent and failure-aware.",BODY), Spacer(1,10)]

F+=[Spacer(1,2), table([["Money","BIGINT in the smallest unit · always a currency · never FLOAT"],["Tenants","every tenant-owned table has tenant_id UUID NOT NULL"],
   ["Isolation","app role cannot bypass RLS · tenant context set with SET LOCAL"],["Truth","payment finality from provider webhooks/reconciliation; UNKNOWN is first-class"]],[88*mm,86*mm])]

F+=[PageBreak(), para("1. Database architecture overview",H2),
  para("One database · many merchants. A single schema holds every tenant; Row-Level Security keeps them apart. Two database roles keep privileges clean: a migration/owner role that does DDL, and an application role that only does DML and can never bypass RLS.",BODY),
  diag("rls","Figure 1 — Shared database, tenant context set server-side, RLS enforced in PostgreSQL"),
  para("2. Design principles",H2),
  bullets(["<b>Simple over clever.</b> Reuse tables and JSONB instead of adding tables for their own sake.",
           "<b>Money is exact.</b> BIGINT minor units + currency column; no floats.",
           "<b>Tenant isolation in the DB.</b> RLS is a real boundary, not just app checks.",
           "<b>Idempotent money.</b> Every financial command is replay-safe.",
           "<b>Auditable.</b> An append-only, hash-chained, tamper-evident audit trail.",
           "<b>Failure-aware.</b> UNKNOWN state and reconciliation are first-class."])]

F+=[para("3. Shared database + tenant security (roles & tenant context)",H2),
  para("There are two roles. The application role never runs DDL and never sets BYPASSRLS. Tenant context is injected server-side per request with SET LOCAL, and tenant_id is never trusted from the client.",BODY),
  block("""
-- roles (created by the migration/owner, once)
create role aegispay_migration;   -- owner of tables: runs DDL, creates policies
create role aegispay_app;         -- application: DML only, cannot bypass RLS

grant usage on schema public to aegispay_app;
grant select, insert, update, delete on all tables in schema public to aegispay_app;

-- every tenant-owned table is owned by migration and has RLS
alter table orders owner to aegispay_migration;
alter table orders enable row level security;
create policy tenant_isolation on orders
  for all
  using (tenant_id = current_setting('app.tenant_id')::uuid)
  with check (tenant_id = current_setting('app.tenant_id')::uuid);

-- the app sets tenant context per request (server-side, never from the client)
begin;
  set local app.tenant_id = '<uuid-of-merchant-a>';
  ... -- queries/updates here are automatically restricted to tenant A
commit;""")]

F+=[PageBreak(), para("4. Complete ER diagram",H2),
  para("The schema is deliberately flat. Grouped below for readability: commerce core, trust/control, and growth.",BODY),
  diag("er_commerce","Figure 2 — Consumer commerce core (products, carts, orders, inventory)"),
  diag("er_trust","Figure 3 — Identity and control (users, agents, policies, authorization, approvals, webhooks, audit) taken as a group"),
  diag("er_growth","Figure 4 — Growth (opportunities, campaigns, atomic budget ledger)")]

F+=[PageBreak(), para("5. Table-by-table explanation",H2),
  para("23 tables. Each is listed with its purpose, keys and why it exists. Column types are in the full schema in the appendix.",BODY),
  para("Identity & tenancy",H3),
  table([["Table","Purpose / why it exists","PK / FK / unique"],
    ["tenants","One row per merchant; the top of each tenant tree.","PK id · unique slug"],
    ["users","Global login identity (not tenant-scoped) so a person can belong to many merchants.","PK id · unique email"],
    ["tenant_users","Joins a user to a tenant with a role; this is the RBAC boundary.","PK id · unique (tenant_id,user_id) · FK tenant,user"],
    ["agents","An AI agent's identity, scopes and allowed tools (JSONB).","PK id · FK tenant,owner_user"],
    ["agent_sessions","A live agent session for binding and revocation.","PK id · FK tenant,agent"]],[40*mm,104*mm,30*mm]),
  para("Commerce (SELL)",H3),
  table([["Table","Purpose / why it exists","PK / FK / unique"],
    ["products","Catalog; server-owned price; per-merchant SKU lock.","PK id · unique(tenant_id,sku) · FK tenant"],
    ["carts","Server-priced, hashed cart with expiry.","PK id · FK tenant,agent"],
    ["cart_items","Lines in a cart; price copied from the product.","PK id · FK cart,product"],
    ["inventory_reservations","Holds stock during checkout so it can't oversell.","PK id · FK product,cart"],
    ["orders","Frozen purchase; carries policy_version + cart_hash.","PK id · FK cart,agent,authorization"],
    ["order_items","Immutable product snapshot per order line.","PK id · FK order,product"]],[40*mm,104*mm,30*mm]),
  para("Control (PROTECT)",H3),
  table([["Table","Purpose / why it exists","PK / FK / unique"],
    ["policies","Deterministic, versioned rules (DSL in JSONB). A new version is a new row — no separate table needed.","PK id · FK tenant · unique(tenant,name,version)"],
    ["authorizations","Transaction-bound consent (cart_hash, amount, policy_version, expiry, single-use). Risk decision + AI intent live here as JSONB.","PK id · FK tenant,agent,user,cart"],
    ["approvals","Human decision, scoped + expiring, bound to an authorization.","PK id · FK authorization,order"],
    ["payments","Provider payment; status from a state machine; UNKNOWN first-class.","PK id · FK order · unique idempotency_key"],
    ["refunds","Separate lifecycle; capped to captured; idempotent.","PK id · FK payment · unique(tenant,idempotency_key)"],
    ["webhook_events","Raw provider events with signature flag + event id for dedupe.","PK id · unique(provider,provider_event_id)"],
    ["idempotency_keys","Replay cache for every financial command.","PK (tenant_id,scope,key)"],
    ["outbox_events","Transactional outbox: event written atomically with the state change.","PK id · FK tenant"],
    ["audit_events","Append-only tamper-evident chain. RLS read-only.","PK id · FK tenant"]],[40*mm,104*mm,30*mm]),
  para("Growth (GROW)",H3),
  table([["Table","Purpose / why it exists","PK / FK / unique"],
    ["opportunities","An AI-detected revenue idea (affinity JSONB).","PK id · FK tenant,agent"],
    ["campaigns","A bounded campaign with budget, margin, discount, targeting and A/B config (JSONB).","PK id · FK tenant,agent"],
    ["campaign_budget_ledger","Atomic spend ledger — every reservation/consumption is a row.","PK id · FK campaign"]],[40*mm,104*mm,30*mm]),
  para("6–8. Columns, keys and relationships",H2),
  para("Exact columns and types are in the appendix schema. Relationships are shown in Figures 2–4. Key bindings: an order references its cart and its authorization; the authorization references the cart's current hash and amount; a payment references an order; a refund references a payment.",BODY)]

F+=[PageBreak(), para("9. State machines",H2), diag("paystate","Figure 5 — Payment state machine; UNKNOWN is first-class and resolved only by provider truth"),
  para("<b>Never blindly retry UNKNOWN.</b> A payment in UNKNOWN is reconciled: the system asks the provider, then completes or fails safely.",BODY),
  para("10. RLS security model",H2),
  para("The application role cannot bypass RLS (it is not a superuser and has no BYPASSRLS). Tenant context is set per transaction with SET LOCAL, and tenant_id is sourced from authenticated identity, never from the client. Every tenant-owned table is made tenant-aware the same way.",BODY),
  block("""
-- one policy pattern applied to every tenant-owned table
create policy tenant_isolation on <table>
  for all
  using (tenant_id = current_setting('app.tenant_id')::uuid)
  with check (tenant_id = current_setting('app.tenant_id')::uuid);

-- identity tables (tenants, users) are not tenant-prefixed:
-- tenants uses its own id as the boundary,
-- users is a global identity and is read via tenant_users.

-- audit_events is read-only for the app (append-only)
revoke update, delete on audit_events from aegispay_app;""")]

F+=[para("11. Indexing strategy",H2),
  table([["Pattern","Used on"],["(tenant_id, status)","orders, payments, refunds, campaigns, agents, webhook_events"],
    ["(tenant_id, created_at)","audit_events, outbox_events, idempotency_keys"],["(tenant_id, entity_id)","cart_items, order_items, inventory_reservations"],
    ["Unique","(tenant_id,sku) products · (tenant_id,scope,key) idempotency · (provider,provider_event_id) webhook_events"]],[50*mm,124*mm]),
  para("12. Idempotency design",H2),
  table([["Command","Scope + key","Behaviour"],["create order","(tenant, scope:'order', key)","replay returns the same order"],
    ["payment operation","(tenant, scope:'payment', key)","retry returns the prior provider result"],
    ["refund","(tenant, scope:'refund', key)","one effective refund per key"],
    ["webhook","(provider, provider_event_id)","duplicates are safe no-ops"],
    ["campaign budget","(tenant, scope:'budget', campaign, request)","atomic reservation; no double-spend"]],[56*mm,66*mm,52*mm]),
  para("This is <b>designed to prevent duplicate financial effects</b> — we do not claim duplicate payments are impossible.",NOTE)]

F+=[PageBreak(), para("13. Webhook design",H2),
  bullets(["Store the provider <b>event id</b> and the <b>raw payload</b> (JSONB).","<b>Verify signature</b> and timestamp before processing; bad ones are ignored and alerted.",
   "<b>Deduplicate</b> on a unique provider_event_id so a duplicate is a safe no-op.","Handle duplicate/out-of-order events by applying them idempotently to the state machine."]),
  para("14. Transactional outbox",H2), diag("outbox","Figure 6 — State change and outbox event commit in the same transaction"),
  para("Because the business update and the outbox event commit together, you cannot have a state change with no event, or an event with no state change. A worker publishes to SQS; consumers are idempotent.",BODY),
  para("15. Audit + Transaction Passport",H2), diag("audit","Figure 7 — Events are hash-chained and anchored for tamper evidence"),
  para("<b>No passport table.</b> The Transaction Passport is <b>generated</b> from the order + order_items + authorization + policy + approvals + payment + audit events. The audit trail is append-only and hash-chained — it is <b>tamper-evident</b>, not tamper-proof.",BODY)]

F+=[para("16. GROW database flow",H2),
  numbered(["AI <b>detects</b> an opportunity (insert into opportunities).",
            "A <b>campaign</b> is proposed with budget, margin and discount caps.",
            "Deterministic <b>policy</b> and <b>merchant approval</b> gate it.",
            "<b>Budget is reserved atomically</b> in campaign_budget_ledger (spent + cost ≤ budget).",
            "The campaign runs inside the reserved envelope; an A/B config (JSONB) splits users.",
            "<b>Incremental</b> revenue = treatment − control is measured (campaign revenue is not automatically campaign-generated revenue)."]),
  para("17. SELL database flow",H2),
  numbered(["A cart is built with <b>server-owned prices</b> and a <b>cart_hash</b> and <b>price_version</b>.",
            "<b>Inventory</b> is reserved; stock changes invalidate the cart.",
            "<b>Policy + risk + authorization</b> produce a transaction-bound, expiring, single-use authorization.",
            "An <b>order</b> is created from the cart; a <b>payment</b> is made through the provider.",
            "A <b>verified webhook</b> (or reconciliation) moves the payment to its true state.",
            "The <b>Transaction Passport</b> is generated on read from the order trail."]),
  para("18. Failure / recovery handling",H2),
  table([["Failure","Database behaviour"],["Provider timeout","payment.status = UNKNOWN; reconciliation resolves truth"],
   ["Duplicate webhook","dedupe no-op"],["Price/inventory changed","authorization invalid; revalidate cart"],
   ["Approval expired","approval expires by timer; no action"],["DB / outbox failure","transaction rolls back; outbox retries"],
   ["Budget exhausted","atomic deny / pause"]],[70*mm,104*mm]),
  para("19. Production checklist",H2),
  bullets(["Every tenant-owned table has tenant_id + RLS policy.","App role can't bypass RLS; migration role owns DDL.",
           "Money is BIGINT minor units + currency.","All financial commands are idempotent.",
           "UNKNOWN is handled and reconciled.","Webhooks verified + deduped.","Outbox + audit are correct and tamper-evident.",
           "Decisions are scoped, expiring, single-use.","No secret in the database (KMS-encrypted / keys in Secrets Manager)."])]

DDL = r"""
-- ===== AegisPay PostgreSQL schema (compact) =====
-- money = BIGINT minor units + currency ; tenant-owned tables have tenant_id UUID

create table tenants (
  id            uuid primary key default gen_random_uuid(),
  slug          text not null unique,
  name          text not null,
  currency      char(3) not null default 'INR',
  status        text not null default 'ACTIVE',
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);

create table users (
  id            uuid primary key default gen_random_uuid(),
  email         citext not null unique,
  password_hash text not null,
  status        text not null default 'ACTIVE',
  created_at    timestamptz not null default now()
);

create table tenant_users (
  id         uuid primary key default gen_random_uuid(),
  tenant_id  uuid not null references tenants(id),
  user_id    uuid not null references users(id),
  role       text not null,           -- admin | ops | policy_admin | approver
  created_at timestamptz not null default now(),
  unique (tenant_id, user_id)
);

create table agents (
  id           uuid primary key default gen_random_uuid(),
  tenant_id    uuid not null references tenants(id),
  owner_user   uuid references users(id),
  name         text not null,
  type         text not null,         -- SELL | GROW
  version      text,
  scopes       jsonb not null default '[]'::jsonb,
  allowed_tools jsonb not null default '[]'::jsonb,
  trust_level  text not null default 'HIGH',
  status       text not null default 'ACTIVE',   -- ACTIVE|SUSPENDED|REVOKED|EXPIRED
  expires_at   timestamptz,
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now()
);

create table agent_sessions (
  id          uuid primary key default gen_random_uuid(),
  tenant_id   uuid not null references tenants(id),
  agent_id    uuid not null references agents(id),
  session_key text not null,
  ip          inet,
  device      text,
  started_at  timestamptz not null default now(),
  ended_at    timestamptz,
  revoked_at  timestamptz
);

create table products (
  id                 uuid primary key default gen_random_uuid(),
  tenant_id          uuid not null references tenants(id),
  sku                text not null,
  name               text not null,
  category           text,
  price_minor        bigint not null check (price_minor >= 0),
  currency           char(3) not null default 'INR',
  status             text not null default 'ACTIVE',
  agent_safe_summary text,
  meta               jsonb not null default '{}'::jsonb,
  created_at         timestamptz not null default now(),
  updated_at         timestamptz not null default now(),
  deleted_at         timestamptz,
  unique (tenant_id, sku)
);

create table carts (
  id            uuid primary key default gen_random_uuid(),
  tenant_id     uuid not null references tenants(id),
  agent_id      uuid not null references agents(id),
  customer_id   uuid references users(id),
  status        text not null default 'CREATED',  -- CREATED|MODIFIED|LOCKED|EXPIRED
  currency      char(3) not null default 'INR',
  cart_hash     text,
  price_version text,
  total_minor   bigint not null default 0,
  expires_at    timestamptz,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);

create table cart_items (
  id              uuid primary key default gen_random_uuid(),
  tenant_id       uuid not null references tenants(id),
  cart_id         uuid not null references carts(id),
  product_id      uuid not null references products(id),
  quantity        int not null check (quantity > 0),
  unit_price_minor bigint not null,     -- server-owned
  line_total_minor bigint not null,
  created_at      timestamptz not null default now()
);

create table inventory_reservations (
  id            uuid primary key default gen_random_uuid(),
  tenant_id     uuid not null references tenants(id),
  product_id    uuid not null references products(id),
  cart_id       uuid not null references carts(id),
  quantity      int not null check (quantity > 0),
  reserved_until timestamptz not null,
  status        text not null default 'RESERVED', -- RESERVED|CONSUMED|RELEASED|EXPIRED
  created_at    timestamptz not null default now()
);

create table orders (
  id             uuid primary key default gen_random_uuid(),
  tenant_id      uuid not null references tenants(id),
  cart_id        uuid not null references carts(id),
  agent_id       uuid not null references agents(id),
  customer_id    uuid references users(id),
  authorization_id uuid references authorizations(id),
  cart_hash      text not null,
  policy_version text not null,
  currency       char(3) not null default 'INR',
  total_minor    bigint not null,
  status         text not null default 'CREATED',
  intent         jsonb,               -- AI intent snapshot (no separate table)
  idempotency_key text unique,
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now()
);

create table order_items (
  id               uuid primary key default gen_random_uuid(),
  tenant_id        uuid not null references tenants(id),
  order_id         uuid not null references orders(id),
  product_id       uuid references products(id),
  product_snapshot jsonb not null,     -- name + price at purchase time
  quantity         int not null check (quantity > 0),
  unit_price_minor bigint not null,
  line_total_minor bigint not null,
  created_at       timestamptz not null default now()
);

create table policies (
  id           uuid primary key default gen_random_uuid(),
  tenant_id    uuid not null references tenants(id),
  name         text not null,
  version      int not null,
  status       text not null default 'ACTIVE',
  rules        jsonb not null default '{}'::jsonb,  -- deterministic DSL
  effective_at timestamptz not null default now(),
  created_at   timestamptz not null default now(),
  unique (tenant_id, name, version)
);

create table authorizations (
  id            uuid primary key default gen_random_uuid(),
  tenant_id     uuid not null references tenants(id),
  agent_id      uuid not null references agents(id),
  user_id       uuid references users(id),
  cart_id       uuid not null references carts(id),
  cart_hash     text not null,
  amount_minor  bigint not null,
  currency      char(3) not null default 'INR',
  policy_version text not null,
  status        text not null default 'VALID',   -- VALID|USED|EXPIRED|REVOKED
  single_use    boolean not null default true,
  expires_at    timestamptz not null,
  used_at       timestamptz,
  risk          jsonb,               -- risk_score, risk_level, factors, model_version
  created_at    timestamptz not null default now()
);

create table approvals (
  id              uuid primary key default gen_random_uuid(),
  tenant_id       uuid not null references tenants(id),
  authorization_id uuid not null references authorizations(id),
  order_id        uuid references orders(id),
  scope_hash      text not null,
  requested_by    text not null,      -- actor that requested
  approver_id     uuid references users(id),
  decision        text,               -- APPROVE | REJECT
  reason          text,
  status          text not null default 'PENDING', -- PENDING|DECIDED|EXPIRED
  expires_at      timestamptz not null,
  decided_at      timestamptz,
  created_at      timestamptz not null default now()
);

create table payments (
  id               uuid primary key default gen_random_uuid(),
  tenant_id        uuid not null references tenants(id),
  order_id         uuid not null references orders(id),
  amount_minor     bigint not null,
  currency         char(3) not null default 'INR',
  provider         text not null,                 -- razorpad
  provider_order_id text,
  provider_payment_id text,
  capture_id       text,
  status           text not null default 'CREATED',
  idempotency_key  text unique,
  attempt_count    int not null default 0,
  unknown_since    timestamptz,
  created_at       timestamptz not null default now(),
  updated_at       timestamptz not null default now()
);

create table refunds (
  id                uuid primary key default gen_random_uuid(),
  tenant_id         uuid not null references tenants(id),
  payment_id        uuid not null references payments(id),
  amount_minor      bigint not null check (amount_minor > 0),
  currency          char(3) not null default 'INR',
  reason            text,
  status            text not null default 'PENDING', -- PENDING|PROCESSED|FAILED|REFUNDED
  provider_refund_id text,
  requested_by      text,
  idempotency_key   text,
  created_at        timestamptz not null default now(),
  updated_at        timestamptz not null default now()
);

create table webhook_events (
  id                 uuid primary key default gen_random_uuid(),
  tenant_id          uuid not null references tenants(id),
  provider           text not null,
  provider_event_id  text not null,
  event_type         text,
  payload            jsonb,
  payload_hash       text,
  signature_verified boolean not null default false,
  status             text not null default 'RECEIVED',
  received_at        timestamptz not null default now(),
  unique (provider, provider_event_id)
);

create table opportunities (
  id             uuid primary key default gen_random_uuid(),
  tenant_id      uuid not null references tenants(id),
  agent_id       uuid not null references agents(id),
  kind           text not null,       -- cross_sell | upsell | bundle
  anchor_product uuid references products(id),
  target_products jsonb not null default '[]'::jsonb,
  affinity       numeric(5,4),
  confidence     numeric(5,4),
  data_window    text,
  status         text not null default 'OPEN',
  created_at     timestamptz not null default now()
);

create table campaigns (
  id             uuid primary key default gen_random_uuid(),
  tenant_id      uuid not null references tenants(id),
  agent_id       uuid not null references agents(id),
  name           text not null,
  status         text not null default 'DRAFT', -- DRAFT|PENDING|APPROVED|ACTIVE|PAUSED|COMPLETED|REJECTED
  budget_minor   bigint not null,
  spent_minor    bigint not null default 0,
  discount_pct   numeric(5,2),
  min_margin_pct numeric(5,2),
  max_duration_days int,
  frequency_cap  int,
  targeting      jsonb not null default '{}'::jsonb,
  ab_config      jsonb not null default '{}'::jsonb,  -- A/B split config (no separate table)
  policy_version text,
  started_at     timestamptz,
  ended_at       timestamptz,
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now()
);

create table campaign_budget_ledger (
  id           uuid primary key default gen_random_uuid(),
  tenant_id    uuid not null references tenants(id),
  campaign_id  uuid not null references campaigns(id),
  amount_minor bigint not null,
  kind         text not null,         -- reserve | consume | release
  idempotency_key text,
  created_at   timestamptz not null default now()
);

create table idempotency_keys (
  tenant_id    uuid not null,
  scope        text not null,         -- order | payment | refund | webhook | budget
  key          text not null,
  request_hash text,
  response     jsonb,
  status       text not null default 'IN_PROGRESS',
  expires_at   timestamptz,
  created_at   timestamptz not null default now(),
  primary key (tenant_id, scope, key)
);

create table outbox_events (
  id            uuid primary key default gen_random_uuid(),
  tenant_id     uuid not null references tenants(id),
  aggregate_type text not null,
  aggregate_id  text not null,
  event_type    text not null,
  payload       jsonb not null default '{}'::jsonb,
  published_at  timestamptz,
  created_at    timestamptz not null default now()
);

create table audit_events (
  id            bigserial primary key,
  tenant_id     uuid not null references tenants(id),
  event_id      uuid not null default gen_random_uuid(),
  event_type    text not null,
  actor_type    text not null,        -- USER | AGENT | SYSTEM | WEBHOOK
  actor_id      text,
  correlation_id text,
  transaction_id text,
  payload       jsonb not null default '{}'::jsonb,
  prev_hash     text not null default '',
  event_hash    text not null,
  created_at    timestamptz not null default now()
);

-- Useful indexes (tenant-prefixed)
create index on orders (tenant_id, status);
create index on orders (tenant_id, created_at);
create index on payments (tenant_id, status);
create index on payments (order_id);
create index on refunds (tenant_id, status);
create index on campaigns (tenant_id, status);
create index on agents (tenant_id, status);
create index on webhook_events (tenant_id, status);
create index on audit_events (tenant_id, created_at);
create index on outbox_events (published_at) where published_at is null;
create index on cart_items (cart_id);
create index on order_items (order_id);
create index on inventory_reservations (product_id, status);
"""

F+=[PageBreak(), para("Appendix A — Complete CREATE TABLE schema",H2),
  para("Compact but complete. Money is BIGINT minor units; every tenant-owned table has tenant_id UUID. JSONB is used where a flexible shape is safer than a new table.",NOTE),
  block(DDL)]

F+=[para("Appendix B — Key transaction examples",H2),
  block("""
-- Atomic budget reservation (GROW)
begin;
  select budget into b from campaigns where id = :camp for update;
  if b.spent + :cost > b.budget then
    raise exception 'budget exhausted';   -- translated to a DENY, audited
  end if;
  update campaigns set spent = spent + :cost, updated_at = now() where id = :camp;
  insert into campaign_budget_ledger(campaign_id, amount_minor, kind) values (:camp, :cost, 'reserve');
  insert into outbox_events(aggregate_type, aggregate_id, event_type, payload)
    values ('campaign', :camp, 'campaign.budget_reserved', jsonb_build_object('cost', :cost));
commit;

-- Create order (idempotent) — lock cart, snapshot products, authorize
begin;
  insert into orders(id, tenant_id, cart_id, authorization_id, cart_hash, policy_version, status)
    values (:order, :tenant, :cart, :auth, :cart_hash, :policy_version, 'AUTHORIZATION_PENDING')
  on conflict (tenant_id, idempotency_key) do nothing;
  insert into order_items(tenant_id, order_id, product_id, product_snapshot, quantity, unit_price_minor, line_total_minor)
    select :tenant, :order, product_id, jsonb_build_object('name', name, 'price', price_minor), quantity, unit_price_minor, line_total_minor
    from cart_items where cart_id = :cart;
  insert into outbox_events(...) ... ;  insert into audit_events(...) ... ;
commit;""")]

doc.build(F)
print("PDF written:", out, out.stat().st_size, "bytes")
