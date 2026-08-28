import subprocess
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph,
                                Spacer, Image, Table, TableStyle, PageBreak, KeepTogether,
                                ListFlowable, ListItem)

ROOT = Path(r"C:\Users\hp\OneDrive\Desktop\AgeisPay")
BUILD = ROOT / "pdf" / "_build_v3"
BUILD.mkdir(parents=True, exist_ok=True)
MMDC = r"C:\Users\hp\AppData\Roaming\npm\node_modules\@mermaid-js\mermaid-cli\src\cli.js"

D = {
# ---- ARCH ----
"a_overview": r"""
flowchart TB
  AI["AI / AGENT LAYER - proposes only"]
  AI --> IA[SELL Agent]
  AI --> IB[GROW Agent]
  IA --> INT["Structured Intent"]
  IB --> INT
  INT --> ORCH
  subgraph CP["AEGISPAY CONTROL PLANE - deterministic and trusted"]
    direction TB
    ORCH[Commerce Orchestrator]
    POL[Policy Engine]
    RSK[Risk Engine]
    AUT[Authorization Engine]
    HITL[Human Approval]
    PAY[Payment Engine]
    REC[Reconciliation]
    AUD[Audit + Passport]
    ORCH --> POL --> RSK --> AUT
    AUT --> HITL
    AUT --> PAY
    PAY --> REC
    ORCH --> AUD
  end
  ORCH --> PG["PostgreSQL<br/>state + RLS + audit + outbox"]
  ORCH --> RD["Redis<br/>cache + locks + rate"]
  ORCH --> SQ["SQS<br/>async events"]
  PAY --> RAZ[Razorpay]
  RAZ --> WH[Verified webhook]
  WH --> REC
  REC --> PAS[Transaction Passport]
""",
"a_trust": r"""
flowchart LR
  subgraph AI["AI RUNTIME - proposes only"]
    TOOL["tool allowlist + structured output"]
  end
  subgraph CT["CONTROL PLANE - validates, authorizes, executes"]
    GEN[Policy + Risk + Authorization]
    PAY2[Payment Engine]
    RZ[Razorpay]
  end
  TOOL -- "structured intent only" --> GEN
  GEN --> PAY2
  PAY2 --> RZ
""",
"a_services": r"""
flowchart LR
  A["AI RUNTIME (FastAPI)"]
  B["CONTROL PLANE (FastAPI)"]
  A -- "no DB, no secrets, no money tools" --> B
  B --> PG[(PostgreSQL)]
  B --> RD[(Redis)]
  B --> SQ[(SQS)]
  B --> RZ[Razorpay]
""",
"a_gate": r"""
flowchart TD
  I[Intent] --> P[Policy - limits, categories, hours]
  P --> R[Risk - score and why]
  R --> A{Decision}
  A -- allow --> OK[Authorize]
  A -- needs human --> AP[Approval]
  A -- deny --> NO[Block and reason]
""",
"a_approval": r"""
flowchart TD
  AI[AI proposal] --> POL[Policy]
  POL --> RSK[Risk]
  RSK --> RQ[APPROVAL REQUIRED]
  RQ --> HU[Human]
  HU --> DEC{scoped, single-use, expiring?}
  DEC -- yes --> AP[Approve / Reject]
  DEC -- no --> SAFE[Reject safely]
  AP --> RES[Resume from checkpoint]
""",
"a_payment": r"""
stateDiagram-v2
  [*] --> CREATED
  CREATED --> CART_LOCKED
  CART_LOCKED --> AUTHORIZATION_PENDING
  AUTHORIZATION_PENDING --> AUTHORIZED: allowed, no human
  AUTHORIZATION_PENDING --> HUMAN_APPROVAL: needs human
  HUMAN_APPROVAL --> AUTHORIZED: approved
  HUMAN_APPROVAL --> AUTHORIZATION_EXPIRED: not decided
  AUTHORIZATION_PENDING --> AUTHORIZATION_EXPIRED: expired
  AUTHORIZATION_PENDING --> PRICE_CHANGED: price changed
  AUTHORIZATION_PENDING --> INVENTORY_EXPIRED: stock gone
  AUTHORIZED --> PAYMENT_PENDING
  PAYMENT_PENDING --> PAID: provider confirms
  PAYMENT_PENDING --> PAYMENT_FAILED: provider failed
  PAYMENT_PENDING --> PAYMENT_UNKNOWN: timeout or no webhook
  PAYMENT_UNKNOWN --> PAID: reconcile finds success
  PAYMENT_UNKNOWN --> PAYMENT_FAILED: reconcile finds failed
  PAYMENT_UNKNOWN --> ORDER_FAILED: still unknown
  PAID --> ORDER_CONFIRMED
  PAID --> REFUND_PENDING
  REFUND_PENDING --> REFUNDED
  ORDER_CONFIRMED --> [*]
  REFUNDED --> [*]
  PAYMENT_FAILED --> ORDER_FAILED
  ORDER_FAILED --> [*]
""",
"a_webhook": r"""
flowchart TD
  W[Webhook arrives] --> A1[Verify authenticity - signature + timestamp]
  A1 --> R1{Is it a replay?}
  R1 -- yes --> IGN[Safe no-op]
  R1 -- no --> D1{Same event id?}
  D1 -- yes --> IGN
  D1 -- no --> P[Persist event]
  P --> X[Apply to state machine - idempotent]
  X --> AU[Audit + outbox event]
""",
"a_outbox": r"""
flowchart TD
  TX["PostgreSQL transaction"]
  TX --> STATE["Business state update"]
  TX --> OUT["Outbox row written atomically (same txn)"]
  OUT --> WK[Outbox worker]
  WK --> SQ[SQS]
""",
"a_reconcile": r"""
flowchart TD
  X[Payment UNKNOWN] --> W[Wait - do not retry]
  W --> L[Ask the provider]
  L --> F{Found?}
  F -- paid --> D[Complete]
  F -- failed --> E[Mark failed - safe]
  F -- no answer --> S[Try again with backoff]
""",
"a_cart": r"""
flowchart TD
  C[Add to cart] --> P[Server reads price + version]
  P --> R[Reserve inventory]
  R --> H[Compute cart hash]
  H --> X{Price or stock changed?}
  X -- yes --> INV[Authorization invalid]
  INV --> RE[Rebuild and revalidate cart]
  RE --> Q[Ask consent again if required]
  X -- no --> L[Lock cart + expiry]
""",
"a_refund": r"""
flowchart TD
  CAP[Payment captured] --> RQ[Refund requested]
  RQ --> PO[Policy - amount, reason, role]
  PO --> AUZ[Authorization - who may refund?]
  AUZ --> RZ[Razorpay refund]
  RZ --> WH[Verified webhook]
  WH --> REC[Reconcile]
  REC --> RD[REFUNDED]
  PO -- blocked --> NO[Reject + audit]
""",
"a_tenant": r"""
flowchart LR
  APP["Application role - no RLS bypass"] --> PG[(PostgreSQL RLS)]
  MIG["Migration role - schema only"] --> PG
  PG --> R[RLS enforced per tenant_id]
""",
"a_aws": r"""
flowchart TB
  US[CloudFront + WAF]
  US --> LB[Load Balancer]
  LB --> ECS["ECS - AegisPay Control Plane"]
  LB --> AI2["ECS - AI Runtime"]
  ECS --> PG[(PostgreSQL RDS)]
  ECS --> RD[(Redis)]
  ECS --> SQ[(SQS)]
  PG --> OB[Outbox worker]
  OB --> SQ
  SQ --> WK[Workers]
  WK --> RAZ[Razorpay]
  LB --> SM[(Secrets Manager + KMS)]
""",
"a_audit": r"""
flowchart LR
  E1[Event 1] --> E2[Event 2]
  E2 --> E3[Event 3]
  E3 --> AN[Anchor in S3]
  E1 -. hash .-> E2
  E2 -. hash .-> E3
""",
# ---- GROW ----
"g_flow": r"""
flowchart TD
  A[Merchant data] --> B[Opportunity detection]
  B --> C[Draft proposal]
  C --> D[Deterministic rules]
  D --> E{Allowed?}
  E -- no --> F[Reject, no campaign]
  E -- yes --> G[Impact estimate range]
  G --> H[Merchant approval]
  H --> I[Budget reservation]
  I --> J[Campaign execution]
  J --> K[A/B experiment]
  K --> L[Incremental revenue measurement]
  L --> M[Learn]
""",
"g_budget": r"""
flowchart TD
  R[Requested spend] --> C{Atomic budget check}
  C -- no budget --> D[Deny]
  C -- yes --> T[Reserve]
  T --> E[Execute]
""",
"g_ab": r"""
flowchart TD
  EL[Eligible users] --> SP{/ split \}
  SP --> CTRL[Control group - no offer]
  SP --> TRT[Treatment group - offer]
  CTRL --> MEAS[Measure]
  TRT --> MEAS
  MEAS --> UP[Incremental conversion + revenue + profit]
""",
# ---- SELL ----
"s_flow": r"""
flowchart TD
  A[User request] --> B[Typed intent]
  B --> C[Catalog search]
  C --> D[Recommend]
  D --> E{Need clarification?}
  E -- yes --> F[Ask the user] --> B
  E -- no --> G[Build cart - server price]
  G --> H[Reserve inventory]
  H --> I[Cart hash]
  I --> J[Intent validation]
  J --> K[Policy]
  K --> L[Risk]
  L --> M[Authorization]
  M --> N{Need human?}
  N -- yes --> O[Human approval]
  O --> P[Razorpay]
  N -- no --> P
  P --> Q[Verified webhook]
  Q --> R[Reconcile if unknown]
  R --> S[Transaction Passport]
""",
}

def render(text, name):
    mmd = BUILD/(name+".mmd"); png = BUILD/(name+".png")
    mmd.write_text(text.strip(), encoding="utf-8")
    if png.exists(): png.unlink()
    try:
        subprocess.run(["node", MMDC, "-q", "-i", str(mmd), "-o", str(png), "-t", "neutral"],
                       check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"{name}: {e.stderr.decode()[:400]}")
    if not png.exists(): raise RuntimeError(f"mmdc failed {name}")
    return png

for n, s in D.items(): render(s, n)
print("Rendered", len(D), "diagrams")

# ---------- styles ----------
LR = 15*mm; TB = 14*mm
ACCENT = colors.HexColor("#8B1E3F")   # deep maroon
INK = colors.HexColor("#17181C")
MUT = colors.HexColor("#667085")
BORD = colors.HexColor("#E5E7EB")
NEUT = colors.HexColor("#F4F5F7")     # light neutral table header
OK = colors.HexColor("#15803D")
WARN = colors.HexColor("#B45309")
ERR = colors.HexColor("#DC2626")

st = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=st["Heading1"], fontName="Helvetica-Bold", fontSize=16.5, textColor=ACCENT, spaceAfter=7, spaceBefore=3)
H2 = ParagraphStyle("H2", parent=st["Heading2"], fontName="Helvetica-Bold", fontSize=13, textColor=INK, spaceAfter=6, spaceBefore=13)
H3 = ParagraphStyle("H3", parent=st["Heading3"], fontName="Helvetica-Bold", fontSize=11.2, textColor=colors.HexColor("#4A2430"), spaceAfter=4, spaceBefore=8)
BODY = ParagraphStyle("Body", parent=st["BodyText"], fontName="Helvetica", fontSize=10, leading=14.4, spaceAfter=6, textColor=INK)
LI = ParagraphStyle("LI", parent=BODY, leftIndent=14, spaceAfter=3)
CAP = ParagraphStyle("Cap", parent=BODY, fontSize=8.6, leading=12, textColor=MUT, alignment=TA_CENTER, spaceBefore=2, spaceAfter=10)
CALL = ParagraphStyle("Call", parent=BODY, fontName="Helvetica-Bold", fontSize=10.2, leading=15, textColor=ACCENT, backColor=colors.HexColor("#FDF6F7"), borderPadding=7, borderWidth=0.6, borderColor=colors.HexColor("#E7BCCA"), spaceAfter=8)
TITLE = ParagraphStyle("Title", parent=st["Title"], fontName="Helvetica-Bold", fontSize=21, textColor=INK, alignment=TA_CENTER, leading=28, spaceAfter=6)
SUB = ParagraphStyle("Sub", parent=BODY, fontSize=12, textColor=ACCENT, alignment=TA_CENTER, spaceAfter=2)
TBLTH = ParagraphStyle("th", parent=BODY, fontName="Helvetica-Bold", fontSize=8.1, textColor=INK, leading=11)
TBLTD = ParagraphStyle("td", parent=BODY, fontSize=7.9, leading=11, textColor=INK)
NOTE = ParagraphStyle("note", parent=BODY, fontSize=9.4, leading=13, textColor=MUT)

def para(t,s=BODY): return Paragraph(t,s)
def bullets(items):
    return ListFlowable([ListItem(Paragraph(t,LI), leftIndent=12) for t in items], bulletType="bullet", start="&#8226;", leftIndent=12, bulletFontSize=8, spaceAfter=6)
def numbered(items):
    return ListFlowable([ListItem(Paragraph(t,LI), leftIndent=16) for t in items], bulletType="1", start=1, leftIndent=16, spaceAfter=6)
def table(rows, widths):
    data=[[Paragraph(c,TBLTH) for c in rows[0]]]
    for r in rows[1:]:
        data.append([Paragraph(c,TBLTD) for c in r])
    t=Table(data, colWidths=widths, hAlign="LEFT", repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),NEUT),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.HexColor("#FAFAFB")]),
        ("GRID",(0,0),(-1,-1),0.4,BORD),("VALIGN",(0,0),(-1,-1),"TOP"),
        ("LEFTPADDING",(0,0),(-1,-1),4),("RIGHTPADDING",(0,0),(-1,-1),4),
        ("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3)]))
    return t
def image_flow(path, max_w=176*mm):
    from PIL import Image as PILImage
    iw,ih=PILImage.open(path).size; r=ih/float(iw); w=min(max_w,iw/4.0)
    return Image(str(path), width=w, height=w*r)
def diag(name, cap): return KeepTogether([Spacer(1,3), image_flow(BUILD/(name+".png")), Paragraph(cap,CAP)])

def build(pdf_name, flow):
    def onp(c,d):
        c.saveState(); c.setFont("Helvetica",8); c.setFillColor(MUT)
        c.drawString(LR,8*mm,"AegisPay · Architecture V3")
        c.drawRightString(A4[0]-LR,8*mm,f"Page {d.page}")
        c.setStrokeColor(BORD); c.setLineWidth(.5); c.line(LR,12*mm,A4[0]-LR,12*mm); c.restoreState()
    frame=Frame(LR,TB,A4[0]-2*LR,A4[1]-2*TB,id="n",leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)
    out=ROOT/pdf_name
    doc=BaseDocTemplate(str(out),pagesize=A4,leftMargin=LR,rightMargin=LR,topMargin=TB,bottomMargin=TB,title="AegisPay Architecture V3",author="AegisPay Engineering")
    doc.addPageTemplates([PageTemplate(id="all",frames=[frame],onPage=onp)])
    doc.build(flow); return out

def why():
    return [Spacer(1,9), para("Why AegisPay is different", H2),
            para("AI can reason and recommend, but only the deterministic AegisPay control plane validates, authorizes and controls financial actions. Razorpay executes only approved actions.", CALL),
            bullets(["<b>No direct money path.</b> The AI runtime has no payment keys, no DB credentials, no unrestricted money tools.",
                     "<b>Deterministic authorization.</b> Policy, risk and a scoped, expiring authorization gate every action.",
                     "<b>Provider truth.</b> Payment finality comes only from a verified webhook or reconciliation — never a guess.",
                     "<b>Prevents, not promises.</b> Idempotency + UNKNOWN-never-blind-retry are designed to prevent duplicate financial effects.",
                     "<b>Tamper-evident.</b> Every decision is recorded in a hash-chained, anchored audit ledger and Transaction Passport.",
                     "<b>Simple to run.</b> Two services, PostgreSQL + Redis + SQS on ECS — no unnecessary complexity."])]

# ============ PDF 1 — ARCH V3 ============
A=[Spacer(1,22), para("AEGISPAY", TITLE), para("Architecture V3 — Production Trust & Growth Layer for Agentic Commerce", SUB),
   Spacer(1,8), para("AI proposes. AegisPay deterministically validates, authorizes and controls. Razorpay executes only approved financial actions.", BODY), Spacer(1,12)]

def secA(n,t):
    return [para(f"{n}. {t}", H2)]

A+=secA(1,"What is AegisPay?")+[para("AegisPay sits between AI agents and payment providers. It does three jobs, and PROTECT is built in — so the AI is useful without ever being trusted with money. This document is the production design.", BODY),
  table([["Job","What it means"],["GROW","AI helps a merchant increase revenue via upsell, cross-sell, bundles, campaigns and experimentation."],
         ["SELL","AI buyers understand intent, discover products, recommend, build carts, get authorization and pay through Razorpay."],
         ["PROTECT","AI can reason and recommend, but never directly controls money."]],[30*mm,144*mm])]

A+=[PageBreak()]+secA(2,"GROW / SELL / PROTECT")+[diag("a_overview","Figure 1 — The full system: AI layer (top), AegisPay control plane (middle), data + Razorpay (bottom)"),
  para("Read it top to bottom: agents propose a structured intent; the control plane runs policy, risk and authorization; only then does it call Razorpay. Every step is recorded.", BODY)]

A+=secA(3,"Architecture overview")+[para("Two focused services, one control plane owning all financial state, and boring, reliable infrastructure.", BODY),
  table([["Layer","Component","Owns"],["AI / Agent","SELL Agent, GROW Agent","proposals, recommendations, structured intents"],
          ["Control Plane","Commerce Orchestrator, Policy, Risk, Authorization, Payment, Approval, Reconciliation, Audit","financial state, determinism, provider interaction, money path"],
          ["Data","PostgreSQL (state, RLS, audit, outbox), Redis (cache/locks/rate), SQS (async)","truth, isolation, reliability"],
          ["External","Razorpay, verified webhooks","money movement, provider truth"]],[26*mm,92*mm,56*mm])]

A+=secA(4,"Component architecture")+[table([["Component","What it does","Fails safely by"],
  ["Commerce Orchestrator","Runs the purchase journey","Only allowed state transitions"],
  ["Policy Engine","Fixed limits (amount, category, hours)","Denies if unsure"],
  ["Risk Engine","Explainable score + why","Escalates to a human on doubt"],
  ["Authorization Engine","Binds consent to one transaction","Expires, single-use"],
  ["Payment Engine","Talks to Razorpay via one adapter","Returns UNKNOWN, never guesses"],
  ["Human Approval","Person decides high value","Scoped, expiring, non-reusable"],
  ["Webhook Gateway","Verifies + dedupes provider events","Drops bad/duplicate events"],
  ["Reconciliation","Resolves UNKNOWN from provider truth","Never retries blindly"],
  ["Audit + Passport","Records every decision","Tamper-evident chain"]],[40*mm,70*mm,64*mm])]

A+=[PageBreak()]+secA(5,"AI / Control-plane trust boundary")+[diag("a_trust","Figure 2 — The AI thinks; the control plane decides and acts, sharing only a structured intent"),
  para("The AI runtime has <b>no payment keys, no database credentials, no unrestricted money tools and no policy mutation capability</b>. A manipulated agent can therefore only produce an intent that the control plane will deterministically gate.", BODY)]

A+=secA(6,"Service boundaries")+[para("Exactly two services. The AI runtime is isolated by privilege, not by language — both are FastAPI, but only the control plane can touch money.", BODY),
  diag("a_services","Figure 3 — AI Runtime (no DB, no secrets, no money tools) and Control Plane (owns state, policy, authz, provider, audit)")
]

A+=secA(7,"SELL flow")+[para("Intent → catalog → recommendation → cart → authorization → Razorpay → verified webhook → reconciliation → Passport. The full walkthrough is in the SELL document.", BODY)]

A+=secA(8,"GROW flow")+[para("Data → opportunity → proposal → rules → estimate → approval → budget → execution → A/B → incremental measurement → learn. Full detail in the GROW document.", BODY)]

A+=[PageBreak()]+secA(9,"Policy / Risk / Authorization")+[diag("a_gate","Figure 4 — Every money action passes a deterministic gate"),
  bullets(["<b>Policy</b> is versioned and merchant-owned; the AI cannot change it.",
           "<b>Risk</b> is explainable: a score plus the reasons.",
           "<b>Authorization</b> is scoped, transaction-bound, expiring and single-use."])]

A+=secA(10,"Human approval")+[diag("a_approval","Figure 5 — A proposal escalates to a person only when required, and resumes from a checkpoint"),
  para("Approval is scoped to one action, single-use, transaction-bound, expiring and immutable after issuance — it cannot be replayed or stretched into a bigger purchase.", BODY)]

A+=secA(11,"Payment state machine")+[para("The full lifecycle, with failure/recovery states. <b>UNKNOWN is a first-class state</b> and exits only on provider truth. We never blindly retry an UNKNOWN payment.", BODY),
  diag("a_payment","Figure 6 — Complete payment state machine, including failure and recovery states")]

A+=[PageBreak()]+secA(12,"Webhook + idempotency")+[diag("a_webhook","Figure 7 — Webhooks are untrusted until verified and deduped; duplicates are safe no-ops"),
  table([["Command","Idempotency key scope","Effect"],
         ["Create order","order key + request hash","same request returns the same order"],
         ["Payment operation","payment key","retry returns the prior provider result"],
         ["Refund","(payment, refund key)","one effective refund per key"],
         ["Webhook processing","(provider, event id)","duplicates are safe no-ops"],
         ["Campaign budget","(campaign, spend request)","atomic reservation, never double-spends"]],[52*mm,52*mm,70*mm]),
  para("Every financial command carries an idempotency key. This is <b>designed to prevent duplicate financial effects</b> — we do not claim duplicate payments are impossible.", NOTE)]

A+=secA(13,"Transactional Outbox")+[diag("a_outbox","Figure 8 — A state change and its event are written in one transaction"),
  para("Because the business-state update and the outbox event commit together, you cannot get a state change with no event (committed but not emitted) or an event with no state change (emitted but not committed). The outbox worker then publishes to SQS at-least-once, and consumers are idempotent.", BODY)]

A+=secA(14,"Reconciliation")+[diag("a_reconcile","Figure 9 — UNKNOWN payments are checked, never blindly retried"),
  para("A timed-out or unknown payment is never re-created. We wait, ask the provider, then complete or fail safely, with backoff and escalation. This is designed to prevent duplicate financial effects.", BODY)]

A+=[PageBreak()]+secA(15,"Cart / Price / Inventory protection")+[diag("a_cart","Figure 10 — If price, version or stock changes, authorization becomes invalid"),
  table([["Guard","What it does"],["Server-owned prices","Price comes from the DB, never the AI or client"],
    ["Cart hash","Snapshot; a change invalidates authorization"],["Price version","A price change is detected and checkout re-validated"],
    ["Inventory reservation","Stock is held during checkout so it can't oversell"],["Cart expiry","A stale cart cannot be paid"],
    ["Product ownership lock","A product belongs to exactly one merchant (tenant). SKU is unique per merchant, and a reference must resolve to the same merchant as the cart — two merchants cannot share or add the same product, and a cross-merchant product in a cart is rejected."]],
    [40*mm,134*mm]),
  para("Because products are tenant-owned and referenced only within their own merchant, a product from another merchant can never be injected into a purchase. This is enforced by the tenant context on every query plus a `unique (tenant_id, sku)` constraint.", NOTE)]

A+=secA(16,"Refund architecture")+[para("Refunds are controlled. The AI has <b>no</b> unrestricted refund tool — a refund needs policy, authorization and Razorpay verification.", BODY),
  diag("a_refund","Figure 11 — Refund flow gated by policy and authorization")]

A+=secA(17,"Agent security")+[table([["Threat","Prevention"],["Prompt injection","Catalog is data, not instructions; intent schema-validated"],
  ["Tool abuse","Only safe tools exposed; no money tool"],["Agent impersonation","Signed credentials, session binding, revocation"],
  ["Credential theft","Hashed, rotatable, scoped keys"],["Authorization replay","Transaction-bound, single-use, expiring authz"],
  ["Self-escalation","No tool to change own limits/policy"],["Malicious catalog / merchant input","Typed, validated, injection classifier"]],[52*mm,122*mm])]

A+=[PageBreak()]+secA(18,"Multi-tenancy + RLS")+[para("Shared PostgreSQL, shared schema, Row-Level Security. Two DB roles are kept separate so the application role cannot bypass RLS.", BODY),
  diag("a_tenant","Figure 12 — Application role respects RLS; migration role only changes schema"),
  bullets(["Application role: no DDL, no BYPASSRLS, scoped to tenant via a per-request `SET LOCAL app.tenant_id`.",
           "Migration role: used only during deploys for schema changes.",
           "Every request carries tenant context; tenant is derived from auth, never from the body.",
           "Products are tenant-owned: `unique (tenant_id, sku)` and a cart/order may only reference products of its own merchant. Two merchants cannot add or share the same product."])]

A+=secA(19,"Audit + Transaction Passport")+[diag("a_audit","Figure 13 — Events are linked by hash into a tamper-evident, anchored chain"),
  para("Append-only, RLS read-only, hash-chained and anchored to an immutable root. The Transaction Passport bundles the who/what/why/approval/provider so any purchase can be verified. It is <b>tamper-evident</b>, not tamper-proof.", BODY)]

A+=secA(20,"AWS deployment")+[diag("a_aws","Figure 14 — Two ECS services, managed data, one queue"),
  para("CloudFront + WAF → ALB → ECS (Control Plane + AI Runtime). PostgreSQL RDS, Redis, SQS, Secrets Manager + KMS. No Kubernetes — not needed at this scale.", BODY)]

A+=[PageBreak()]+secA(21,"Observability + SLOs")+[para("Dashboards cover the money path, the decision path and AI health. Every log carries correlation, tenant, transaction and agent ids; secrets and PII are never logged.", BODY),
  table([["Signal","What it shows"],["Payment success / UNKNOWN rate","provider finality and ambiguity"],
   ["Webhook latency / duplicate rate","ingest health and provider behaviour"],["Policy denial / risk escalation","decision guardrails"],
   ["Human approval latency","time to a decision"],["Reconciliation backlog","how many are stuck UNKNOWN"],
   ["AI tool failure / agent completion","agent reliability"],["Campaign ROI","growth effectiveness"]],[64*mm,110*mm]),
  para("SLOs (realistic, not fabricated): API availability ~99.9% (single-region multi-AZ, honest); RPO ≤ 15 min; RTO ≤ 1 hour; payment state transition typically < 2 s; webhook processing within seconds; reconciliation auto-resolves ≥ 95% of UNKNOWN; approvals expire on a timer.", NOTE)]

A+=secA(22,"Disaster recovery")+[para("Multi-AZ, PITR backups (RPO ≤ 15 min), quarterly restore drills, documented RTO ≤ 1 hour. Audit integrity is independent of DB restore via the hash chain + S3 anchor.", BODY)]

A+=secA(23,"Threat model")+[table([["Threat","Attack surface","Impact","Prevent","Detect","Recover"],
 ["Prompt injection","catalog, prompts","unauthorized spend","catalog DATA-only, schema, allowlist","injection + denial alerts","block, revoke, audit"],
 ["Tool abuse","agent tool calls","misuse","allowlist, rate limit, budget","anomaly alerts","throttle, suspend"],
 ["Agent impersonation","credentials","spend as another agent","signed creds, mTLS, session binding","auth anomalies","revoke, re-issue"],
 ["Webhook spoofing","webhook endpoint","false state","signature + timestamp verify","signature failure alerts","ignore, reconcile"],
 ["Replay attack","authz / webhook / approval","repeat an action","single-use authz, dedupe, nonce","replay detectors","reject"],
 ["Duplicate payment","retries","double effect","idempotency keys","duplicate detectors","return prior result"],
 ["Price manipulation","cart / intent","wrong amount","server-owned prices + hash","price mismatch","reject"],
 ["Tenant escape","queries","cross-tenant leak","RLS + tenant context + app role","isolation tests","block + audit"],
 ["Authorization replay","authz reuse","second spend","scoped, expiring, single-use","duplicate authz","deny, revoke"],
  ["Compromised AI runtime","LLM service","attempt money path","no secrets, no money tools, allowlist","red-team + anomalies","quarantine"]],[42*mm,30*mm,26*mm,34*mm,28*mm,20*mm])]

A+=[PageBreak()]+secA(24,"Failure testing")+[para("Every failure behaves safely: detect → safe state → recover → audit. Introduced via a chaos/red-team harness in staging.", BODY),
  table([["Fault","Detection","Safe state","Recovery","Audit"],
   ["Razorpay timeout","long call / missing webhook","PAYMENT_UNKNOWN","reconcile → complete/fail","payment.unknown, payment.reconciled"],
   ["Duplicate webhook","same event id","no-op","acknowledge only","webhook.deduped"],
   ["Invalid webhook","signature check","reject, no state","alert + ignore","webhook.failed"],
   ["Price changed in checkout","price version mismatch","authorization invalid","revalidate, ask consent","cart.rejected"],
   ["Inventory unavailable","reservation fails","cart not locked","re-select / notify","inventory.reserve_failed"],
   ["AI unavailable","timeout","agent path degrades","control plane still reconciles","agent.unavailable"],
   ["Policy violation","policy decision","DENY, no payment","record reason","policy.denied"],
   ["Expired approval","approval timer","expire, no action","re-request approval","approval.expired"],
   ["DB / outbox failure","publish error","transaction rolls back","retry from outbox","outbox.retry"],
   ["Campaign budget exhaustion","atomic check","deny / pause","no spend","campaign.budget_exceeded"]],[34*mm,32*mm,34*mm,44*mm,30*mm])]

A+=secA(25,"Production readiness checklist")+[table([["Area","Present"],
 ["AI","No money path, tool allowlist, structured output, policy + risk, human approval, red-team"],
 ["Payments","Idempotency, full state machine, webhook verify + dedupe, reconciliation, refund caps"],
 ["Trust","Versioned policy, explainable risk, scoped/expiring authz, Transaction Passport, outbox"],
 ["Growth","Atomic budget ledger, kill switch, A/B + incremental measurement"],
 ["Security","Auth (user, agent, service), secrets isolation, RLS app role, encryption, rate limits"],
 ["Reliability","Timeouts, retries, circuit breakers, outbox + DLQ, backups + DR, SLOs"],
 ["Observability","Metrics, logs with IDs, tracing, alerts, dashboards"]],[40*mm,134*mm])]

A+=why()
out1=build("AegisPay-Architecture-V3.pdf", A); print("PDF1:",out1.name)

# ============ PDF 2 — GROW V3 ============
G=[Spacer(1,22), para("AEGISPAY — GROW", TITLE), para("LangGraph growth agent · V3", SUB),
   Spacer(1,8), para("How the AI safely grows a merchant's revenue. The AI decides what to propose; the control plane decides what may be authorized — clearly separated.", BODY), Spacer(1,12)]

G+=[para("The flow", H2), diag("g_flow","Figure 1 — From merchant data to a measured, budget-limited campaign"),
  numbered(["<b>Merchant data.</b> Grouped sales, no customer PII.",
   "<b>Opportunity detection.</b> Real correlation (shoe → socks).",
   "<b>Draft proposal.</b> The AI suggests an offer, budget, target.",
   "<b>Deterministic rules.</b> Max discount, max budget, min margin, duration, frequency, allowed targeting.",
   "<b>Impact estimate.</b> An honest range, labelled an estimate.",
   "<b>Merchant approval.</b> The AI cannot start it alone.",
   "<b>Budget reservation.</b> Atomic, so it can never overspend.",
   "<b>Campaign execution.</b> Inside the reserved budget.",
   "<b>A/B experiment.</b> Control vs treatment.",
   "<b>Incremental revenue.</b> Test − control, not raw sales.",
   "<b>Learn.</b> Repeat what works, drop what doesn't."]),
  Spacer(1,6), para("The rule that separates AI from money: <b>the AI decides what to propose; the control plane decides what may be authorized.</b>", CALL)]

G+=[PageBreak()]+[para("Safety rails", H2), table([["Rail","Bound"],
 ["Maximum discount","hard % cap"],["Maximum budget","hard ₹ cap"],["Minimum margin","margin floor after discount"],
 ["Campaign duration","days cap"],["Frequency cap","per-customer contact limit"],["Allowed targeting","value/behaviour only; no protected attributes"],
 ["Atomic budget ledger","`spent + cost <= budget` in one operation"],["Kill switch","halt all campaign spend instantly"]],[56*mm,118*mm]),
 para("Budget ledger (atomic)", H2), diag("g_budget","Figure 2 — Concurrent requests reserve budget atomically; no overspend and no double-spend"),
 para("The AI cannot raise its own budget. Only a merchant/policy admin can, and that change is audited.", NOTE)]

G+=[para("A/B + incremental measurement (GROW)", H2), diag("g_ab","Figure 3 — Control vs treatment; measure the increment, not the campaign's headline"),
  bullets(["Campaign revenue is <b>not</b> automatically campaign-generated revenue — it must beat a control group.",
   "<b>Incremental uplift</b> = treatment − control (conversion, revenue, profit).",
   "Results are a range with a confidence level, labelled an estimate.",
   "The AI is only scaled if the measured effect is real and positive."])]

G+=[PageBreak(), para("One realistic failure", H2),
  table([["Step","Result"],["AI proposes a campaign budget","₹20,000"],["Merchant policy allows","₹5,000"],
   ["Deterministic rules","reject the proposal"],["Campaign starts?","no"],["Audit record","campaign.rejected · reason: budget exceeds cap"]],[80*mm,94*mm]),
  para("The AI made a suggestion. Policy said no. No money moved, and the rejection is recorded. That is the point.", NOTE)]

G+=why()
out2=build("AegisPay-LangGraph-GROW-V3.pdf", G); print("PDF2:",out2.name)

# ============ PDF 3 — SELL V3 ============
S=[Spacer(1,22), para("AEGISPAY — SELL", TITLE), para("LangGraph AI-buyer checkout · V3", SUB),
   Spacer(1,8), para("A safe end-to-end purchase where the AI helps but never controls money. Payment finality comes from the provider.", BODY), Spacer(1,12)]

S+=[para("The flow", H2), diag("s_flow","Figure 1 — From a user request to a verified Passport"),
  numbered(["<b>User request.</b> “Find running shoes under ₹4,000.”",
   "<b>Typed intent.</b> The AI's output is a strict, validated schema.",
   "<b>Catalog search.</b> A real, parameterized query.",
   "<b>Recommend.</b> Best matches, priced by the store.",
   "<b>Clarify if needed.</b> Ask, then continue.",
   "<b>Build cart.</b> Server-owned price.",
   "<b>Reserve inventory.</b> Stock held so it can't oversell.",
   "<b>Cart hash.</b> A change invalidates authorization.",
   "<b>Validate intent.</b> Strictly checked.",
   "<b>Policy.</b> Limits, categories, hours.",
   "<b>Risk.</b> Explainable score.",
   "<b>Authorization.</b> Scoped, expiring, single-use.",
   "<b>Human if required.</b> High value → a person approves.",
   "<b>Razorpay.</b> Only approved money moves.",
   "<b>Verified webhook.</b> Provider truth.",
   "<b>Reconcile if unknown.</b> Never a blind retry.",
   "<b>Transaction Passport.</b> Full verifiable proof."])]

S+=[PageBreak()]+[para("Explicit failure paths", H2), table([["Failure","Safe state","Recovery"],
 ["Price changed","authorization invalid","revalidate cart, ask consent again"],
 ["Inventory expired","cart not locked","re-select / notify"],
 ["Approval expired","no action, expires","re-request approval"],
 ["Payment failed","PAYMENT_FAILED","order failed safely; retry is a new attempt"],
 ["Payment UNKNOWN","UNKNOWN, first-class","reconcile → complete / fail; never blind retry"],
 ["Webhook duplicate","safe no-op","acknowledge only"],
 ["Refund","gated by policy + authorization","idempotent, capped to captured"]],[50*mm,60*mm,64*mm]),
 para("The payment state machine (simplified)", H2),
 para("<b>CREATED → CART_LOCKED → AUTHORIZATION_PENDING → AUTHORIZED → PAYMENT_PENDING → PAID → ORDER_CONFIRMED</b>, with failure states AUTHORIZATION_EXPIRED, PRICE_CHANGED, INVENTORY_EXPIRED, PAYMENT_FAILED, PAYMENT_UNKNOWN, ORDER_FAILED, REFUND_PENDING → REFUNDED, and CANCELLED.", BODY),
 bullets(["<b>UNKNOWN is first-class.</b> It exits only on a verified webhook or reconciliation result.",
          "<b>Never blindly retry UNKNOWN.</b> That is how duplicate charges happen.",
          "<b>Provider truth.</b> The frontend and the agent never set payment state."]),
 para("Key protections", H2),
  bullets(["Typed intent · server-owned prices · cart hash · price version · inventory reservation · cart expiry · idempotency (designed to prevent duplicate financial effects) · scoped/expiring authorization · agent identity · prompt-injection defense · refund/cancellation controlled and audited.",
           "Product ownership lock: a product is bound to one merchant (tenant) with a per-merchant unique SKU. It can only be added to a cart whose merchant matches — two merchants cannot share or add the same product, and a cross-merchant product is rejected."])]

S+=why()
out3=build("AegisPay-LangGraph-SELL-V3.pdf", S); print("PDF3:",out3.name)
print("done")
