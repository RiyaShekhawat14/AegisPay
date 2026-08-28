import subprocess
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer,
                                Image, Table, TableStyle, PageBreak, KeepTogether,
                                ListFlowable, ListItem)

ROOT = Path(r"C:\Users\hp\OneDrive\Desktop\AgeisPay")
BUILD = ROOT/"pdf"/"_build_dbe"; BUILD.mkdir(parents=True, exist_ok=True)
MMDC = r"C:\Users\hp\AppData\Roaming\npm\node_modules\@mermaid-js\mermaid-cli\src\cli.js"
OUT = ROOT/"AegisPay-Database-Schema.pdf"

D = {
"er_a": r"""
erDiagram
  TENANTS ||--o{ TENANT_USERS : has
  USERS ||--o{ TENANT_USERS : member
  TENANTS ||--o{ AGENTS : owns
  AGENTS ||--o{ AGENT_SESSIONS : opens
""",
"er_b": r"""
erDiagram
  TENANTS ||--o{ PRODUCTS : sells
  TENANTS ||--o{ CARTS : owns
  AGENTS ||--o{ CARTS : builds
  CARTS ||--o{ CART_ITEMS : has
  CART_ITEMS }o--|| PRODUCTS : references
  PRODUCTS ||--o{ INVENTORY_RESERVATIONS : reserved_by
  CARTS ||--o{ INVENTORY_RESERVATIONS : holds
  CARTS ||--o| ORDERS : becomes
  ORDERS ||--o{ ORDER_ITEMS : has
  ORDER_ITEMS }o--|| PRODUCTS : snapshot
""",
"er_c": r"""
erDiagram
  TENANTS ||--o{ POLICIES : sets
  ORDERS ||--o| AUTHORIZATIONS : uses
  AUTHORIZATIONS ||--o{ APPROVALS : may need
  ORDERS ||--o{ PAYMENTS : paid_by
  PAYMENTS ||--o{ REFUNDS : refunded
  TENANTS ||--o{ WEBHOOK_EVENTS : receives
""",
"er_d": r"""
erDiagram
  AGENTS ||--o{ OPPORTUNITIES : detects
  OPPORTUNITIES ||--o{ CAMPAIGNS : launches
  CAMPAIGNS ||--o{ CAMPAIGN_BUDGET_LEDGER : ledger
  TENANTS ||--o{ IDEMPOTENCY_KEYS : namespaced
  TENANTS ||--o{ OUTBOX_EVENTS : emits
  TENANTS ||--o{ AUDIT_EVENTS : records
""",
"sec": r"""
flowchart LR
  A[Request] --> B[Authentication]
  B --> C[Tenant membership]
  C --> D[Server sets tenant context]
  D --> E[Row-Level Security]
  E --> F[(Database)]
""",
"sell": r"""
flowchart LR
  User --> AS[Agent session]
  AS --> CT[Cart]
  CT --> CI[Cart items]
  CI --> IR[Inventory reservation]
  CT --> ORD[Order]
  ORD --> AUZ[Authorization]
  ORD --> PAY[Payment]
  PAY --> WH[Webhook]
  ORD --> AUD[Audit]
""",
"grow": r"""
flowchart LR
  M[Merchant] --> OP[Opportunity]
  OP --> CA[Campaign]
  CA --> BL[Budget ledger]
  CA --> ORD[Orders]
  ORD --> MEAS[Measurement]
  CA --> AUD[Audit]
""",
}
def render(text,name):
    mmd=BUILD/(name+".mmd"); png=BUILD/(name+".png"); mmd.write_text(text.strip(),encoding="utf-8")
    if png.exists(): png.unlink()
    try: subprocess.run(["node",MMDC,"-q","-i",str(mmd),"-o",str(png),"-t","neutral"],check=True,capture_output=True)
    except subprocess.CalledProcessError as e: raise RuntimeError(f"{name}: {e.stderr.decode()[:300]}")
    if not png.exists(): raise RuntimeError(f"mmdc failed {name}")
    return png
for n,s in D.items(): render(s,n)
print("Rendered",len(D))

LR=16*mm; TB=14*mm
ACC=colors.HexColor("#8B1E3F"); INK=colors.HexColor("#17181C"); MUT=colors.HexColor("#667085")
BORD=colors.HexColor("#E5E7EB"); NEUT=colors.HexColor("#F4F5F7")
OK=colors.HexColor("#15803D"); ER=colors.HexColor("#DC2626")
st=getSampleStyleSheet()
H1=ParagraphStyle("H1",parent=st["Heading1"],fontName="Helvetica-Bold",fontSize=16.5,textColor=ACC,spaceAfter=6,spaceBefore=2)
H2=ParagraphStyle("H2",parent=st["Heading2"],fontName="Helvetica-Bold",fontSize=13.2,textColor=INK,spaceAfter=6,spaceBefore=13)
H3=ParagraphStyle("H3",parent=st["Heading3"],fontName="Helvetica-Bold",fontSize=11,textColor=colors.HexColor("#4A2430"),spaceAfter=4,spaceBefore=10)
BODY=ParagraphStyle("Body",parent=st["BodyText"],fontName="Helvetica",fontSize=10.2,leading=14.6,spaceAfter=6,textColor=INK)
LI=ParagraphStyle("LI",parent=BODY,leftIndent=13,spaceAfter=4)
CAP=ParagraphStyle("Cap",parent=BODY,fontSize=8.6,leading=11,textColor=MUT,alignment=TA_CENTER,spaceBefore=2,spaceAfter=10)
CALL=ParagraphStyle("Call",parent=BODY,fontName="Helvetica-Bold",fontSize=10.4,leading=15.5,textColor=ACC,backColor=colors.HexColor("#FDF4F6"),borderPadding=8,borderWidth=0.6,borderColor=colors.HexColor("#E7BCCA"),spaceAfter=8)
TITLE=ParagraphStyle("Title",parent=st["Title"],fontName="Helvetica-Bold",fontSize=22,textColor=INK,alignment=TA_CENTER,leading=29,spaceAfter=5)
SUB=ParagraphStyle("Sub",parent=BODY,fontSize=11.5,textColor=ACC,alignment=TA_CENTER,spaceAfter=2)
TH=ParagraphStyle("th",parent=BODY,fontName="Helvetica-Bold",fontSize=8.0,textColor=colors.white,leading=10.5)
TD=ParagraphStyle("td",parent=BODY,fontName="Helvetica",fontSize=7.9,leading=10.6,textColor=INK)
TDM=ParagraphStyle("tdm",parent=BODY,fontName="Monospace",fontSize=7.9,leading=10.6,textColor=INK)
NOTE=ParagraphStyle("note",parent=BODY,fontSize=8.8,leading=12.3,textColor=MUT)
SMALL=ParagraphStyle("small",parent=BODY,fontSize=9.2,leading=12,textColor=INK)

def para(t,s=BODY): return Paragraph(t,s)
def bullets(it): return ListFlowable([ListItem(Paragraph(t,LI),leftIndent=12) for t in it],bulletType="bullet",start="\u2022",leftIndent=12,bulletFontSize=8,spaceAfter=4)
def table(rows,widths,header=True):
    data=[]
    if header: data.append([Paragraph(c,TH) for c in rows[0]])
    for r in rows[1:]: data.append([Paragraph(c,TDM if False else TD) for c in r])
    t=Table(data,colWidths=widths,hAlign="LEFT",repeatRows=1)
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),ACC if header else colors.white),("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#FAFAFC")]),
      ("GRID",(0,0),(-1,-1),0.4,BORD),("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),5),
      ("RIGHTPADDING",(0,0),(-1,-1),5),("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3)]))
    return t
def table2(rows,widths):
    data=[]
    for r in rows: data.append([Paragraph(c,TD) for c in r])
    t=Table(data,colWidths=widths,hAlign="LEFT",repeatRows=1)
    t.setStyle(TableStyle([("GRID",(0,0),(-1,-1),0.4,BORD),("VALIGN",(0,0),(-1,-1),"TOP"),
      ("LEFTPADDING",(0,0),(-1,-1),5),("RIGHTPADDING",(0,0),(-1,-1),5),("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3)]))
    return t
def image_flow(path,max_w=178*mm):
    from PIL import Image as PILImage
    iw,ih=PILImage.open(path).size; r=ih/float(iw); w=min(max_w,iw/4.0); return Image(str(path),width=w,height=w*r)
def diag(name,cap): return KeepTogether([Spacer(1,3),image_flow(BUILD/(name+".png")),Paragraph(cap,CAP)])

def onp(c,d):
    c.saveState(); c.setFont("Helvetica",7.8); c.setFillColor(MUT)
    c.drawString(LR,8*mm,"AegisPay · Production Database Schema")
    c.drawRightString(A4[0]-LR,8*mm,f"Page {d.page}")
    c.setStrokeColor(BORD); c.setLineWidth(.5); c.line(LR,12*mm,A4[0]-LR,12*mm); c.restoreState()
frame=Frame(LR,TB,A4[0]-2*LR,A4[1]-2*TB,id="n",leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)
doc=BaseDocTemplate(str(OUT),pagesize=A4,leftMargin=LR,rightMargin=LR,topMargin=TB,bottomMargin=TB,title="AegisPay Production Database Schema",author="AegisPay Engineering")
doc.addPageTemplates([PageTemplate(id="all",frames=[frame],onPage=onp)])

# ---- table data ----
SERVICES=["AI Runtime","Control Plane","Merchant Dashboard","Payment Service","Webhook Worker","Reconciliation Worker","GROW Engine"]
def U(*yes): return {s:(s in yes) for s in SERVICES}
TBL=[
 dict(name="tenants",group="Identity & Tenants",purpose="One merchant. This is the top of the whole tenant tree.",
  cols=[("id","UUID","Merchant ID"),("slug","TEXT","short unique name"),("name","TEXT","display name"),("currency","CHAR(3)","INR"),("status","TEXT","ACTIVE / SUSPENDED"),("created_at","TIMESTAMP","when created")],
  pk="id",fks=["none (top of tree)"],idxs=["slug (unique)"],used=U("Control Plane","Merchant Dashboard")),
 dict(name="users",group="Identity & Tenants",purpose="A person who can log in. Global identity, shared across merchants.",
  cols=[("id","UUID","User ID"),("email","TEXT","login email (unique)"),("password_hash","TEXT","never plaintext"),("status","TEXT","ACTIVE / DISABLED"),("created_at","TIMESTAMP","when created")],
  pk="id",fks=["none"],idxs=["email (unique)"],used=U("Control Plane","Merchant Dashboard")),
 dict(name="tenant_users",group="Identity & Tenants",purpose="Links a user to a merchant with a role. This is the access-control boundary.",
  cols=[("id","UUID","Row ID"),("tenant_id","UUID","merchant"),("user_id","UUID","person"),("role","TEXT","admin / ops / approver"),("created_at","TIMESTAMP","when added")],
  pk="id",fks=["tenant_id → tenants.id","user_id → users.id"],idxs=["(tenant_id, role)","(tenant_id, user_id) unique"],used=U("Control Plane","Merchant Dashboard")),
 dict(name="agents",group="Identity & Tenants",purpose="An AI agent's identity, its permissions and allowed tools.",
  cols=[("id","UUID","Agent ID"),("tenant_id","UUID","merchant"),("type","TEXT","SELL / GROW"),("scopes","JSONB","what it may do"),("allowed_tools","JSONB","which tools it may call"),("trust_level","TEXT","HIGH / MED / LOW"),("status","TEXT","ACTIVE / SUSPENDED / REVOKED"),("expires_at","TIMESTAMP","optional expiry")],
  pk="id",fks=["tenant_id → tenants.id","owner_user → users.id"],idxs=["(tenant_id, status)"],used=U("AI Runtime","Control Plane","Merchant Dashboard","GROW Engine")),
 dict(name="agent_sessions",group="Identity & Tenants",purpose="One live session for an agent, so it can be revoked.",
  cols=[("id","UUID","Session ID"),("tenant_id","UUID","merchant"),("agent_id","UUID","agent"),("session_key","TEXT","opaque key"),("device","TEXT","device hint"),("started_at","TIMESTAMP","when started"),("ended_at","TIMESTAMP","when ended")],
  pk="id",fks=["tenant_id → tenants.id","agent_id → agents.id"],idxs=["(agent_id)"],used=U("AI Runtime","Control Plane")),

 dict(name="products",group="Commerce",purpose="Catalog. The price lives here and is read-only to the AI.",
  cols=[("id","UUID","Product ID"),("tenant_id","UUID","merchant"),("sku","TEXT","stock code"),("name","TEXT","product name"),("category","TEXT","shoes / food"),("price_minor","BIGINT","price in paise / kobo"),("currency","CHAR(3)","INR"),("status","TEXT","ACTIVE / HIDDEN"),("agent_safe_summary","TEXT","what AI may display"),("meta","JSONB","extra attributes")],
  pk="id",fks=["tenant_id → tenants.id"],idxs=["(tenant_id, sku) unique","(tenant_id, category, status)"],used=U("AI Runtime","Control Plane","Merchant Dashboard","GROW Engine")),
 dict(name="carts",group="Commerce",purpose="A basket. Server-priced and hashed so it can't be silently changed.",
  cols=[("id","UUID","Cart ID"),("tenant_id","UUID","merchant"),("agent_id","UUID","agent that built it"),("status","TEXT","ACTIVE / LOCKED / EXPIRED"),("cart_hash","TEXT","snapshot of contents"),("price_version","TEXT","price snapshot"),("total_minor","BIGINT","sum total"),("expires_at","TIMESTAMP","when it times out")],
  pk="id",fks=["tenant_id → tenants.id","agent_id → agents.id","customer_id → users.id"],idxs=["(tenant_id, status)"],used=U("AI Runtime","Control Plane","Merchant Dashboard")),
 dict(name="cart_items",group="Commerce",purpose="The lines inside a cart; each has a server-copied price.",
  cols=[("id","UUID","Line ID"),("tenant_id","UUID","merchant"),("cart_id","UUID","cart"),("product_id","UUID","product"),("quantity","INT","how many"),("unit_price_minor","BIGINT","price copied from product"),("line_total_minor","BIGINT","qty × price")],
  pk="id",fks=["cart_id → carts.id","product_id → products.id"],idxs=["(cart_id)"],used=U("AI Runtime","Control Plane")),
 dict(name="inventory_reservations",group="Commerce",purpose="Holds stock during checkout so it can't oversell.",
  cols=[("id","UUID","Reservation ID"),("tenant_id","UUID","merchant"),("product_id","UUID","product"),("cart_id","UUID","cart"),("quantity","INT","reserved qty"),("reserved_until","TIMESTAMP","release time"),("status","TEXT","RESERVED / CONSUMED / RELEASED")],
  pk="id",fks=["product_id → products.id","cart_id → carts.id"],idxs=["(product_id, status)"],used=U("Control Plane")),
 dict(name="orders",group="Commerce",purpose="The frozen purchase. Carries policy version, cart hash and the AI intent snapshot.",
  cols=[("id","UUID","Order ID"),("tenant_id","UUID","merchant"),("cart_id","UUID","source cart"),("agent_id","UUID","agent"),("authorization_id","UUID","permission used"),("cart_hash","TEXT","cart snapshot"),("policy_version","TEXT","which policy ran"),("total_minor","BIGINT","final amount"),("status","TEXT","order state"),("intent","JSONB","AI intent snapshot"),("idempotency_key","TEXT","no duplicate order")],
  pk="id",fks=["cart_id → carts.id","agent_id → agents.id","authorization_id → authorizations.id"],idxs=["(tenant_id, status)","(tenant_id, created_at)"],used=U("Control Plane","Merchant Dashboard","Payment Service","Reconciliation Worker")),
 dict(name="order_items",group="Commerce",purpose="Immutable product snapshot per line — proof of the price at purchase time.",
  cols=[("id","UUID","Line ID"),("tenant_id","UUID","merchant"),("order_id","UUID","order"),("product_id","UUID","product"),("product_snapshot","JSONB","name + price frozen"),("quantity","INT","qty"),("unit_price_minor","BIGINT","price"),("line_total_minor","BIGINT","total")],
  pk="id",fks=["order_id → orders.id","product_id → products.id"],idxs=["(order_id)"],used=U("Control Plane","Merchant Dashboard")),

 dict(name="policies",group="Control & Safety",purpose="The merchant's deterministic rules. Versioned as new rows (no separate versions table).",
  cols=[("id","UUID","Policy ID"),("tenant_id","UUID","merchant"),("name","TEXT","policy name"),("version","INT","version number"),("status","TEXT","ACTIVE / ARCHIVED"),("rules","JSONB","the DSL / caps"),("created_at","TIMESTAMP","when created")],
  pk="id",fks=["tenant_id → tenants.id"],idxs=["(tenant_id, name, version) unique"],used=U("Control Plane","Merchant Dashboard")),
 dict(name="authorizations",group="Control & Safety",purpose="An explicit permission to pay this exact cart — bound, single-use and expiring. Holds the risk decision.",
  cols=[("id","UUID","Authorization ID"),("tenant_id","UUID","merchant"),("agent_id","UUID","agent"),("user_id","UUID","person"),("cart_id","UUID","cart"),("cart_hash","TEXT","bound cart"),("amount_minor","BIGINT","bound amount"),("policy_version","TEXT","policy that ran"),("status","TEXT","VALID / USED / EXPIRED / REVOKED"),("single_use","BOOL","true"),("expires_at","TIMESTAMP","when it expires"),("risk","JSONB","risk score + factors")],
  pk="id",fks=["tenant_id → tenants.id","agent_id → agents.id","cart_id → carts.id","user_id → users.id"],idxs=["(tenant_id, status)"],used=U("Control Plane")),
 dict(name="approvals",group="Control & Safety",purpose="A human's yes/no on a risky action. Scoped, expiring, single-use.",
  cols=[("id","UUID","Approval ID"),("tenant_id","UUID","merchant"),("authorization_id","UUID","what it approves"),("order_id","UUID","related order"),("scope_hash","TEXT","the exact approved scope"),("approver_id","UUID","who decided"),("decision","TEXT","APPROVE / REJECT"),("expires_at","TIMESTAMP","deadline"),("created_at","TIMESTAMP","when requested")],
  pk="id",fks=["authorization_id → authorizations.id","order_id → orders.id","approver_id → users.id"],idxs=["(tenant_id, status)"],used=U("Control Plane","Merchant Dashboard")),

 dict(name="payments",group="Payments",purpose="The complete payment lifecycle. UNKNOWN is a real state.",
  cols=[("id","UUID","Payment ID"),("tenant_id","UUID","merchant"),("order_id","UUID","related order"),("authorization_id","UUID","permission used"),("provider","TEXT","razorpay"),("provider_order_id","TEXT","Razorpay order"),("provider_payment_id","TEXT","Razorpay payment"),("amount_minor","BIGINT","amount"),("currency","CHAR(3)","INR"),("status","TEXT","payment state, incl UNKNOWN"),("idempotency_key","TEXT","duplicate protection"),("failure_code","TEXT","machine code"),("failure_reason","TEXT","readable reason")],
  pk="id",fks=["order_id → orders.id","authorization_id → authorizations.id","tenant_id → tenants.id"],idxs=["(tenant_id, status)","(tenant_id, created_at)"],used=U("Control Plane","Payment Service","Webhook Worker","Reconciliation Worker","Merchant Dashboard")),
 dict(name="refunds",group="Payments",purpose="A controlled refund, capped to what was captured. The AI has no unrestricted refund tool.",
  cols=[("id","UUID","Refund ID"),("tenant_id","UUID","merchant"),("payment_id","UUID","payment"),("amount_minor","BIGINT","refund amount"),("currency","CHAR(3)","INR"),("reason","TEXT","why"),("status","TEXT","PENDING / PROCESSED / REFUNDED / FAILED"),("provider_refund_id","TEXT","Razorpay refund"),("idempotency_key","TEXT","one refund per key")],
  pk="id",fks=["payment_id → payments.id","tenant_id → tenants.id"],idxs=["(tenant_id, status)","(tenant_id, idempotency_key) unique"],used=U("Control Plane","Payment Service","Webhook Worker","Reconciliation Worker","Merchant Dashboard")),
 dict(name="webhook_events",group="Payments",purpose="Provider events, verified and deduplicated. Raw payload saved.",
  cols=[("id","UUID","Event ID"),("tenant_id","UUID","merchant"),("provider","TEXT","razorpay"),("provider_event_id","TEXT","id for dedupe"),("event_type","TEXT","payment.failed etc"),("payload","JSONB","raw payload"),("signature_verified","BOOL","true after check"),("status","TEXT","RECEIVED / APPLIED / DEDUPED"),("created_at","TIMESTAMP","when received")],
  pk="id",fks=["tenant_id → tenants.id"],idxs=["(provider, provider_event_id) unique","(tenant_id, status)"],used=U("Webhook Worker","Control Plane")),

 dict(name="opportunities",group="GROW",purpose="A revenue idea the AI detected from real purchase affinity.",
  cols=[("id","UUID","Opportunity ID"),("tenant_id","UUID","merchant"),("agent_id","UUID","growth agent"),("kind","TEXT","cross_sell / upsell / bundle"),("anchor_product","UUID","product"),("target_products","JSONB","suggested products"),("affinity","NUMERIC","correlation"),("confidence","NUMERIC","how sure"),("status","TEXT","OPEN / ACTED")],
  pk="id",fks=["tenant_id → tenants.id","agent_id → agents.id","anchor_product → products.id"],idxs=["(tenant_id, status)"],used=U("GROW Engine","AI Runtime","Control Plane")),
 dict(name="campaigns",group="GROW",purpose="A budget-capped offer with margin, discount, targeting and A/B config. Budget & spent live here.",
  cols=[("id","UUID","Campaign ID"),("tenant_id","UUID","merchant"),("agent_id","UUID","growth agent"),("name","TEXT","campaign name"),("status","TEXT","PENDING / APPROVED / ACTIVE / PAUSED"),("budget_minor","BIGINT","max spend"),("spent_minor","BIGINT","spent so far"),("discount_pct","NUMERIC","cap"),("min_margin_pct","NUMERIC","floor"),("targeting","JSONB","who it targets"),("ab_config","JSONB","A/B split")],
  pk="id",fks=["tenant_id → tenants.id","agent_id → agents.id"],idxs=["(tenant_id, status)"],used=U("GROW Engine","Control Plane","Merchant Dashboard")),
 dict(name="campaign_budget_ledger",group="GROW",purpose="Every budget move as a row, so spend is atomic and cannot overspend.",
  cols=[("id","UUID","Row ID"),("tenant_id","UUID","merchant"),("campaign_id","UUID","campaign"),("amount_minor","BIGINT","amount"),("kind","TEXT","reserve / consume / release"),("idempotency_key","TEXT","atomic, no double-spend"),("created_at","TIMESTAMP","when")],
  pk="id",fks=["campaign_id → campaigns.id","tenant_id → tenants.id"],idxs=["(campaign_id)"],used=U("Control Plane","GROW Engine")),

 dict(name="idempotency_keys",group="Platform Reliability",purpose="Replay cache — a repeated request returns the same result instead of repeating.",
  cols=[("id","TEXT(built)","(tenant, scope, key)"),("tenant_id","UUID","merchant"),("scope","TEXT","order / payment / refund / webhook / budget"),("key","TEXT","the idempotency key"),("request_hash","TEXT","hash of the request"),("response","JSONB","the stored result"),("expires_at","TIMESTAMP","when it expires")],
  pk="(tenant_id, scope, key)",fks=["tenant_id → tenants.id"],idxs=["(tenant_id, scope, key) primary"],used=U("Control Plane","Payment Service","Webhook Worker","GROW Engine")),
 dict(name="outbox_events",group="Platform Reliability",purpose="Event written in the same transaction as the change, so nothing is lost.",
  cols=[("id","UUID","Event ID"),("tenant_id","UUID","merchant"),("aggregate_type","TEXT","order / payment"),("aggregate_id","TEXT","which row"),("event_type","TEXT","payment.succeeded"),("payload","JSONB","event body"),("published_at","TIMESTAMP","null until sent")],
  pk="id",fks=["tenant_id → tenants.id"],idxs=["(published_at) where null"],used=U("Control Plane","Webhook Worker","Payment Service")),
 dict(name="audit_events",group="Platform Reliability",purpose="Append-only, hash-chained, tamper-evident record of every decision.",
  cols=[("id","BIGSERIAL","Row ID"),("tenant_id","UUID","merchant"),("event_type","TEXT","approval.approved"),("actor_type","TEXT","USER / AGENT / SYSTEM / WEBHOOK"),("actor_id","TEXT","who"),("correlation_id","TEXT","journey id"),("transaction_id","TEXT","business id"),("payload","JSONB","details"),("prev_hash","TEXT","previous link"),("event_hash","TEXT","this event's hash")],
  pk="id",fks=["tenant_id → tenants.id"],idxs=["(tenant_id, created_at)","(transaction_id)"],used=U("Control Plane","Merchant Dashboard","Webhook Worker","Reconciliation Worker")),
]

def render_table(t):
    rows=[["Column","Type","Meaning"]]
    for c in t["cols"]: rows.append([c[0],c[1],c[2]])
    # used-by rows: a compact two-column list (YES green, NO-gray "no direct access")
    ub=[["Service","Access"]]
    for s in SERVICES:
        if t["used"][s]:
            ub.append([f"<font color=\"{OK.hexval().replace('0x','#').upper()}\">&#10003; {s}</font>","yes"])
        else:
            ub.append([f"<font color=\"{MUT.hexval().replace('0x','#').upper()}\">&#10007; {s}</font>","no direct access"])
    fl=[Spacer(1,4),
        para(f"TABLE: {t['name']}",H3),
        para("Purpose",SMALL), para(t["purpose"],NOTE),
        para("Columns",SMALL), table(rows,[46*mm,26*mm,102*mm]),
        para("Primary Key",SMALL), para("<b>"+t["pk"]+"</b>",NOTE),
        para("Foreign Keys",SMALL), bullets([f for f in t["fks"]]),
        para("Important Indexes",SMALL), bullets([f for f in t["idxs"]]),
        para("Used by",SMALL), table2(ub,[96*mm,28*mm]),
        Spacer(1,10)]
    return [KeepTogether(fl)]

F=[Spacer(1,20), para("AEGISPAY",TITLE), para("Production Database Schema",SUB),
   Spacer(1,8), para("Simple, Secure &amp; Multi-Tenant PostgreSQL Design.",BODY),
   Spacer(1,6), para("One shared PostgreSQL database for every merchant. Which tables exist, what each stores, and how they connect — in plain words.",CALL)]

F+=[PageBreak(), para("1. Database overview",H2),
  para("AegisPay uses <b>one</b> PostgreSQL database for <b>many merchants</b>. Each table that belongs to a merchant carries a <b>tenant_id</b>, and PostgreSQL Row-Level Security (RLS) keeps them apart. The schema stays small by reusing tables and JSONB instead of creating new tables.",BODY),
  table2([["Group","Tables"],["Identity &amp; Tenants","tenants · users · tenant_users · agents · agent_sessions"],
    ["Commerce","products · carts · cart_items · inventory_reservations · orders · order_items"],
    ["Control &amp; Safety","policies · authorizations · approvals"],
    ["Payments","payments · refunds · webhook_events"],
    ["GROW","opportunities · campaigns · campaign_budget_ledger"],
    ["Platform Reliability","idempotency_keys · outbox_events · audit_events"]],[40*mm,134*mm])]

F+=[PageBreak(), para("2. Database architecture",H2),
  para("The data is split into a few small groups. The AI layer can propose (catalog, carts, opportunities), but the financial and audit tables are owned by the control plane and payment services.",BODY),
  table2([["Group","Tables"],["Identity &amp; Tenants","tenants · users · tenant_users · agents · agent_sessions"],
    ["Commerce","products · carts · cart_items · inventory_reservations · orders · order_items"],
    ["Control &amp; Safety","policies · authorizations · approvals"],
    ["Payments","payments · refunds · webhook_events"],
    ["GROW","opportunities · campaigns · campaign_budget_ledger"],
    ["Platform Reliability","idempotency_keys · outbox_events · audit_events"]],[40*mm,134*mm])]

F+=[PageBreak(), para("3. Complete ER diagram",H2),
  para("The database is one shared PostgreSQL database. To keep it readable, the relationships are shown in <b>four clean views</b> instead of one crowded diagram. Each table's own columns are on its card in the next sections.",NOTE),
  diag("er_a","Figure 1 — Identity &amp; tenants: who owns what"),
  diag("er_b","Figure 2 — Commerce: products, carts, orders"),
  diag("er_c","Figure 3 — Control &amp; payments: authorization, payment, refund"),
  diag("er_d","Figure 4 — Growth &amp; reliability: campaigns, idempotency, outbox, audit")]

groups=[("Identity &amp; Tenants",["tenants","users","tenant_users","agents","agent_sessions"]),
        ("Commerce",["products","carts","cart_items","inventory_reservations","orders","order_items"]),
        ("Control &amp; Safety",["policies","authorizations","approvals"]),
        ("Payments",["payments","refunds","webhook_events"]),
        ("GROW",["opportunities","campaigns","campaign_budget_ledger"]),
        ("Platform Reliability",["idempotency_keys","outbox_events","audit_events"])]

sectnum=4
for grp,names in groups:
    F+=[PageBreak(), para(f"{sectnum}. {grp} tables",H2)]
    for n in names:
        t=next(x for x in TBL if x["name"]==n)
        F+=render_table(t)
    sectnum+=1

F+=[PageBreak(), para("10. Shared database security / RLS",H2),
  para("Merchant-owned tables carry a <b>tenant_id</b>. The application DB role can never bypass RLS, and the frontend never decides the tenant.",BODY),
  bullets(["Merchant A has tenant_id = A, Merchant B has tenant_id = B.",
           "<b>PostgreSQL RLS</b> automatically blocks A from reading B's rows — even on a buggy query.",
           "Tenant context is set server-side per request with <b>SET LOCAL</b>, never taken from the client.",
           "One role migrates/owns the schema; a separate application role only does DML and cannot bypass RLS."]),
  diag("sec","Figure 5 — Request → authentication → tenant membership → server sets tenant → RLS → database"),
  para("Frontends can request only what belongs to the authenticated tenant. The database enforces it too.",NOTE)]

F+=[PageBreak(), para("11. State tables",H2),
  para("Simple, readable state transitions — no complicated diagrams.",BODY),
  para("Payment",H3), table2([["State","Next"],["created","payment_pending"],["payment_pending","captured"],["captured","completed"],["payment_pending","unknown (timeout / no webhook)"],["unknown","reconciliation → provider truth"],["unknown","captured / failed / still unknown"]],[70*mm,104*mm]),
  para("Refund",H3), table2([["State","Next"],["pending","processing"],["processing","refunded"]],[70*mm,104*mm]),
  para("Authorization",H3), table2([["State","Next"],["pending","approved"],["approved","consumed"],["pending","rejected / expired"]],[70*mm,104*mm]),
  para("Cart",H3), table2([["State","Next"],["active","locked"],["locked","expired"],["locked","converted_to_order"]],[70*mm,104*mm]),
  para("If the provider is slow, the payment is <b>unknown</b> — we never retry it blindly. We reconcile (ask the provider), then finish or fail safely.",CALL)]

F+=[PageBreak(), para("12. SELL database flow",H2), diag("sell","Figure 6 — How a purchase moves through the database"),
  para("13. GROW database flow",H2), diag("grow","Figure 7 — How a campaign starts, spends and is measured")]

F+=[PageBreak(), para("14. Audit + Transaction Passport",H2),
  para("There is <b>no</b> passport table. The Transaction Passport is <b>generated</b> from the order, order items, authorization, policy, approval, payment and audit events. The audit trail is append-only and hash-chained — it is <b>tamper-evident</b>, not tamper-proof.",BODY),
  para("Source of truth",H2),
  table2([["Thing","Where it lives"],["Product price","products.price_minor"],["Cart price","cart_items.unit_price_minor"],
    ["Order price","orders.total_minor"],["Payment status","payments.status"],["Provider truth","Razorpay + verified webhook/reconciliation"],
    ["Policy","policies"],["Authorization","authorizations"],["Audit","audit_events"],["Cache","Redis — never the source of truth"]],[80*mm,94*mm])]

F+=[PageBreak(), para("15. Idempotency + Outbox",H2),
  bullets(["<b>Idempotency.</b> Every financial command carries a key; a repeated request returns the stored result. <b>Designed to prevent duplicate financial effects</b>, not 'impossible'.",
           "<b>Transactional outbox.</b> The business change and its event are written in one transaction, so nothing is lost; a worker publishes to SQS."]),
  para("16. Why we kept the schema simple",H2),
  para("We intentionally did <b>not</b> create separate tables for:",BODY),
  bullets(["Transaction Passport · Risk Decision · AI Intent · Policy Version · Price History · Agent Permissions · Campaign Variants"]),
  para("Reason: these are safely represented using existing tables, immutable snapshots (order_items.product_snapshot), JSONB (risk, intent, scopes, ab_config, rules) or derived views — at this scale. It keeps AegisPay easier to understand and maintain.",NOTE),
  para("17. Final production checklist",H2),
  bullets(["Every merchant table has tenant_id + RLS; app role can't bypass it.",
           "Money is an exact whole number (BIGINT) + a currency; no floats.",
           "All financial commands are idempotent.",
           "Payment UNKNOWN is handled and reconciled; no blind retry.",
           "Webhooks are verified and deduplicated.",
           "Outbox + tamper-evident audit are in place.",
           "Authorization is scoped, expiring and single-use.",
           "Refunds are capped and controlled; no unrestricted AI refund.",
           "Secrets are in AWS Secrets Manager, never in the database."])]

doc.build(F)
print("PDF written:",OUT,OUT.stat().st_size,"bytes")
