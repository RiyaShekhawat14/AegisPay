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
BUILD = ROOT / "pdf" / "_build_v2"
BUILD.mkdir(parents=True, exist_ok=True)
MMDC = r"C:\Users\hp\AppData\Roaming\npm\node_modules\@mermaid-js\mermaid-cli\src\cli.js"

# ---------------- Mermaid diagrams ----------------
D = {
# ARCH
"v2_arch": r"""
flowchart TB
  subgraph U["People and AI"]
    USER[User] --> AIB[AI Buyer Agent]
    MERCH[Merchant] --> GROW[Growth Agent]
  end
  subgraph CP["AegisPay Control Plane - the trusted decision layer"]
    GW[Protocol Gateway] --> ORCH[Commerce Orchestrator]
    ORCH --> POLICY[Policy]
    ORCH --> RISK[Risk]
    ORCH --> AUTHZ[Authorization]
    AUTHZ --> HITL[Human Approval]
    AUTHZ --> PAY[Payment Engine]
    RULES[Versioned rules] --> POLICY
    AUDIT[Audit Ledger + Passport]
  end
  subgraph OUT["Where money moves"]
    RAZ[Razorpay]
  end
  AIB --> GW
  GROW --> GW
  PAY --> RAZ
  RAZ --> WEB[Verified Webhook + Reconciliation]
  WEB --> ORCH
  ORCH --> AUDIT
""",
"v2_trust": r"""
flowchart LR
  subgraph AI["AI side - thinks only"]
    INTENT[Structured intent]
    RECOMMEND[Recommendations]
  end
  subgraph DET["Deterministic side - decides and acts"]
    POL2[Policy + Risk]
    AUTH2[Authorization]
    PAY2[Payment execution]
  end
  INTENT --> POL2
  POL2 --> AUTH2
  AUTH2 --> PAY2
""",
"v2_ai_buyer": r"""
flowchart TD
  A[User asks to buy] --> B[Understand request]
  B --> C[Search catalog]
  C --> D[Recommend]
  D --> E[Build cart with server prices]
  E --> F[Lock price + reserve stock]
  F --> G[Check policy and risk]
  G --> H{Authorize?}
  H -- allow --> I[Pay]
  H -- need a human --> J[Human approves]
  J --> I
  H -- deny --> K[Blocked and logged]
  I --> L[Razorpay]
  L --> M[Verified webhook or reconcile]
  M --> N[Passport + audit]
""",
"v2_growth": r"""
flowchart TD
  A[Merchant sales data] --> B[Find opportunity]
  B --> C[AI proposes an offer]
  C --> D[Check fixed rules]
  D --> E{Passes?}
  E -- no --> X[Reject or cap]
  E -- yes --> F[Estimate uplift]
  F --> G[Merchant approves]
  G --> H[Run campaign inside budget]
  H --> I[A/B test]
  I --> J[Measure incremental revenue]
  J --> K[Learn and repeat]
""",
"v2_gate": r"""
flowchart TD
  I[Intent] --> P[Policy: limits, categories, hours]
  P --> R[Risk: score and why]
  R --> A{Decision}
  A -- allow --> OK[Authorize]
  A -- need a person --> AP[Approval]
  A -- deny --> NO[Block + reason]
""",
"v2_approval": r"""
flowchart TD
  H[High-risk action] --> RQ[Approval request]
  RQ --> S{Is it scoped, expiring, single-use?}
  S -- yes --> E[Human approves or rejects]
  S -- no --> RE[Reject safely]
  E --> D[Decision recorded + audited]
""",
"v2_payment_state": r"""
stateDiagram-v2
  [*] --> Created
  Created --> Authorized
  Authorized --> Capturing
  Capturing --> Captured
  Capturing --> Failed
  Authorized --> Failed
  Capturing --> Unknown
  Unknown --> Captured: verified webhook
  Unknown --> Failed: provider says failed
  Unknown --> StillUnknown: no answer yet
  Captured --> [*]
  Failed --> [*]
  StillUnknown --> Escalate
""",
"v2_webhook": r"""
flowchart TD
  W[Webhook arrives] --> V[Verify signature]
  V --> T[Check timestamp]
  T --> U{Is it a duplicate?}
  U -- yes --> N[Ignore - already applied]
  U -- no --> P[Save the event]
  P --> Q[Apply to the state machine]
  Q --> A[Audit it]
""",
"v2_reconcile": r"""
flowchart TD
  X[Payment is Unknown] --> R[Wait - do not retry]
  R --> L[Ask the provider what happened]
  L --> F{Found?}
  F -- paid --> D[Complete the purchase]
  F -- failed --> E[Mark failed - safe]
  F -- no answer --> A[Try again later]
""",
"v2_tenant": r"""
flowchart LR
  A[Merchant A] --> DB[(Shared PostgreSQL)]
  B[Merchant B] --> DB
  DB --> R[Row-Level Security]
  R --> X[A sees only its own rows]
  R --> Y[B sees only its own rows]
""",
"v2_audit": r"""
flowchart LR
  E1[Event 1] --> E2[Event 2]
  E2 --> E3[Event 3]
  E3 --> AN[Anchor]
  E1 -. hash .-> E2
  E2 -. hash .-> E3
""",
"v2_aws": r"""
flowchart TB
  US[Users] --> CF[CloudFront + WAF]
  CF --> LB[Load Balancer]
  LB --> API[AegisPay API on ECS]
  API --> PG[(PostgreSQL)]
  API --> RD[(Redis)]
  API --> Q[(Queue)]
  LB --> AI[AI Runtime]
  AI --> LLM[LLM]
  Q --> WK[Workers]
  WK --> PG
  WK --> RAZ[Razorpay]
  API --> SM[(Secrets Manager)]
""",
# GROW
"grow_flow": r"""
flowchart TD
  A[Merchant sales data] --> B[Find a real opportunity]
  B --> C[AI suggests an offer]
  C --> D[Check the fixed rules]
  D --> E{Allowed?}
  E -- no --> F[Reject or cap it]
  E -- yes --> G[Estimate an uplift range]
  G --> H[Merchant approves]
  H --> I[Run inside the budget]
  I --> J["A/B test (test vs control)"]
  J --> K[Measure the real uplift]
  K --> L[Learn and repeat]
""",
"grow_rules": r"""
flowchart TD
  P[AI offer] --> D1{Discount too big?}
  D1 -- yes --> X[Cap it]
  D1 -- no --> D2{Budget too high?}
  D2 -- yes --> X
  D2 -- no --> D3{Margin too low?}
  D3 -- yes --> X
  D3 -- no --> D4{Contact the same person too often?}
  D4 -- yes --> X
  D4 -- no --> Y[Merchant approves]
""",
"grow_budget": r"""
flowchart LR
  B["Budget = Rs 50,000"] --> S[Spent counter]
  S --> C{Spent less than budget?}
  C -- yes --> RUN[Offer applies]
  RUN --> S
  C -- no --> STOP[Campaign pauses]
""",
# SELL
"sell_flow": r"""
flowchart TD
  A[User asks to buy] --> B[Understand intent]
  B --> C[Search catalog with a typed query]
  C --> D[Recommend]
  D --> E[Build cart with server prices]
  E --> F[Lock price and reserve stock]
  F --> G[Validate the intent]
  G --> H[Policy + Risk]
  H --> I[Authorization]
  I --> J{Need a human?}
  J -- yes --> K[Human approves]
  K --> L[Payment Engine]
  J -- no --> L
  L --> M[Razorpay]
  M --> N[Verified webhook or reconcile]
  N --> O[Transaction Passport]
""",
"sell_safety": r"""
stateDiagram-v2
  [*] --> Created
  Created --> Pending
  Pending --> Paid: provider confirms
  Pending --> Unknown: timeout
  Unknown --> Paid: reconcile finds success
  Unknown --> Failed: provider says failed
  Unknown --> Escalated: still unknown
  Paid --> [*]
  Failed --> [*]
""",
}

def render(text, name):
    mmd = BUILD / (name + ".mmd"); png = BUILD / (name + ".png")
    mmd.write_text(text.strip(), encoding="utf-8")
    if png.exists(): png.unlink()
    try:
        subprocess.run(["node", MMDC, "-q", "-i", str(mmd), "-o", str(png), "-t", "neutral"],
                       check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"{name}: {e.stderr.decode()[:400]}")
    if not png.exists(): raise RuntimeError(f"mmdc failed for {name}")
    return png

render_batch = {}
def get(name):
    if name not in render_batch:
        from PIL import Image as I
        try:
            # already have render helper; call again? store dict
            pass
        except Exception: pass
    return BUILD / (name + ".png")

# render all
for name, src in D.items():
    render(src, name)
print("Rendered", len(D), "diagrams")

# ---------------- layout helpers ----------------
LR = 17*mm; TB = 15*mm
ACCENT = colors.HexColor("#8B1E3F")
DARK = colors.HexColor("#4C0E22")
LIGHT = colors.HexColor("#FBF3F5")
BORD = colors.HexColor("#EFD8DE")
INK = colors.HexColor("#2A0E18")
MUT = colors.HexColor("#6D6475")
GREEN = colors.HexColor("#15803D")

st = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=st["Heading1"], fontName="Helvetica-Bold", fontSize=16.5, textColor=ACCENT, spaceAfter=8, spaceBefore=4)
H2 = ParagraphStyle("H2", parent=st["Heading2"], fontName="Helvetica-Bold", fontSize=13, textColor=DARK, spaceAfter=6, spaceBefore=12)
H3 = ParagraphStyle("H3", parent=st["Heading3"], fontName="Helvetica-Bold", fontSize=11.2, textColor=colors.HexColor("#5E142E"), spaceAfter=4, spaceBefore=8)
BODY = ParagraphStyle("Body", parent=st["BodyText"], fontName="Helvetica", fontSize=10, leading=14.5, spaceAfter=6, textColor=INK)
LI = ParagraphStyle("LI", parent=BODY, leftIndent=14, spaceAfter=3)
CAP = ParagraphStyle("Cap", parent=BODY, fontSize=8.8, leading=12, textColor=MUT, alignment=TA_CENTER, spaceBefore=2, spaceAfter=10)
CALLOUT = ParagraphStyle("Callout", parent=BODY, fontName="Helvetica-Bold", fontSize=10.3, leading=15, textColor=ACCENT, backColor=LIGHT, borderPadding=6, borderWidth=0.6, borderColor=BORD, spaceAfter=8)
TITLE = ParagraphStyle("Title", parent=st["Title"], fontName="Helvetica-Bold", fontSize=22, textColor=DARK, alignment=TA_CENTER, leading=29, spaceAfter=6)
SUB = ParagraphStyle("Sub", parent=BODY, fontSize=12, textColor=ACCENT, alignment=TA_CENTER, spaceAfter=2)
BOXD = ParagraphStyle("Boxd", parent=BODY, fontSize=9.2, leading=13, backColor=colors.HexColor("#FBF3F5"), borderColor=BORD, borderWidth=0.5, borderPadding=6, textColor=INK)

def para(t, s=BODY): return Paragraph(t, s)
def bullets(items):
    return ListFlowable([ListItem(Paragraph(t, LI), leftIndent=12) for t in items], bulletType="bullet", start="&#8226;", leftIndent=12, bulletFontSize=8, spaceAfter=6)
def numbered(items):
    return ListFlowable([ListItem(Paragraph(t, LI), leftIndent=16) for t in items], bulletType="1", start=1, leftIndent=16, spaceAfter=6)
def table(rows, widths):
    th = ParagraphStyle("th", parent=BODY, fontName="Helvetica-Bold", fontSize=8.6, textColor=colors.white, leading=12)
    td = ParagraphStyle("td", parent=BODY, fontSize=8.6, leading=12)
    data = [[Paragraph(c, th) for c in rows[0]]]
    for r in rows[1:]: data.append([Paragraph(c, td) for c in r])
    t = Table(data, colWidths=widths, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0), ACCENT),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.HexColor("#FBF3F5")]),
        ("GRID",(0,0),(-1,-1),0.4, BORD),("VALIGN",(0,0),(-1,-1),"TOP"),
        ("LEFTPADDING",(0,0),(-1,-1),5),("RIGHTPADDING",(0,0),(-1,-1),5),
        ("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3)]))
    return t
def image_flow(path, max_w=172*mm):
    from PIL import Image as PILImage
    iw, ih = PILImage.open(path).size; ratio = ih/float(iw); w = min(max_w, iw/4.0)
    return Image(str(path), width=w, height=w*ratio)
def diag(name, caption): return KeepTogether([Spacer(1,3), image_flow(BUILD/(name+".png")), Paragraph(caption, CAP)])

def build(pdf_name, flow):
    def onp(c, d):
        c.saveState(); c.setFont("Helvetica",8); c.setFillColor(MUT)
        c.drawString(LR,9*mm,"AegisPay — Architecture V2")
        c.drawRightString(A4[0]-LR,9*mm,f"Page {d.page}")
        c.setStrokeColor(BORD); c.setLineWidth(.5); c.line(LR,13*mm,A4[0]-LR,13*mm); c.restoreState()
    frame = Frame(LR, TB, A4[0]-2*LR, A4[1]-2*TB, id="n", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    out = ROOT/pdf_name
    doc = BaseDocTemplate(str(out), pagesize=A4, leftMargin=LR, rightMargin=LR, topMargin=TB, bottomMargin=TB, title="AegisPay Architecture", author="AegisPay Engineering")
    doc.addPageTemplates([PageTemplate(id="all", frames=[frame], onPage=onp)])
    doc.build(flow)
    return out

def WHY(pdf_label):
    return [Spacer(1,10), para("Why AegisPay is difficult to reject", H2),
            para("The AI can reason and recommend, but only AegisPay's deterministic control plane can authorize and execute financial actions. That is the whole product.", CALLOUT),
            bullets([
              "<b>It is safe by design, not by promise.</b> The AI has no money keys and no payment endpoint — only a request that is always checked.",
              "<b>It handles failure honestly.</b> Unknown payments are reconciled rather than blindly retried; duplicates are designed out, not hoped away.",
              "<b>You can prove it.</b> Every decision is written to a tamper-evident audit ledger and a Transaction Passport.",
              "<b>It is simple to run.</b> One FastAPI service, PostgreSQL + Redis + one queue on AWS ECS — no unnecessary complexity.",
              "<b>It grows and sells.</b> GROW lifts revenue with bounded risk; SELL lets AI buyers transact end-to-end. PROTECT keeps both safe.",
            ])]

# ============ PDF 1 — ARCHITECTURE V2 ============
A = [Spacer(1,24), para("AEGISPAY", TITLE), para("Architecture V2 — Trust & Growth Layer for Agentic Commerce", SUB),
     Spacer(1,8), para("AI can reason. AegisPay controls whether it is allowed to act. Razorpay only executes approved actions.", BODY), Spacer(1,12)]

A += [para("1. What is AegisPay?", H2),
      para("AegisPay sits between AI agents (a shopping assistant, a growth agent) and payment providers (Razorpay). It does three jobs:", BODY),
      table([["Job","What it means"],
             ["GROW","Use AI to help a merchant sell more: upsells, cross-sells, bundles, campaigns."],
             ["SELL","Let an AI buyer find a product, build a cart and pay end-to-end."],
             ["PROTECT","Make every AI money step explainable, limited, approved, recorded and safe to recover from failure."]],
            [34*mm, 140*mm]),
      Spacer(1,6), para("PROTECT is built into the architecture, not bolted on. That is why the AI can be useful and still never be trusted with money.", BODY)]

A += [PageBreak(), para("2. High-level architecture", H2), diag("v2_arch", "Figure 1 — People and AI (top), AegisPay control plane (middle), Razorpay (bottom)"),
      para("Read it left to right: a user asks an AI buyer; everything flows into the AegisPay control plane, which checks policy, risk and authorization; only then does it call Razorpay. Razorpay replies through a verified webhook and reconciliation.", BODY)]

A += [para("3. Component architecture", H2),
      table([["Component","What it does","Fails safely by"],
             ["Commerce Orchestrator","Runs the purchase journey (intent, cart, order).","Only moves on allowed state transitions."],
             ["Policy Engine","Checks fixed limits (amount, category, hours).","Denies if it is unsure."],
             ["Risk Engine","Gives an explainable risk score + why.","Escalates to a human on doubt."],
             ["Authorization Engine","Binds a valid consent to this one transaction.","Expires and can't be reused."],
             ["Human Approval","A person decides high-value actions.","Scoped, expiring, single-use."],
             ["Payment Engine","Talks to Razorpay through one adapter.","Returns UNKNOWN rather than guessing."],
             ["Webhook Gateway","Checks and dedupes Razorpay events.","Ignores duplicates and bad signatures."],
             ["Reconciliation","Resolves UNKNOWN payments from provider truth.","Never retries blindly."],
             ["Audit + Passport","Records every decision.","Tamper-evident chain."]],
            [40*mm,76*mm,58*mm])]

A += [PageBreak(), para("4. The AI / control-plane trust boundary", H2),
      para("The most important line in the system. The AI <b>thinks</b> on one side; AegisPay <b>decides and acts</b> on the other. They only share a structured intent.", BODY),
      diag("v2_trust","Figure 2 — The AI side hands a validated intent to the deterministic side"),
      bullets(["The AI never sees payment keys, database credentials or unrestricted refund/payment tools.",
               "It only sends a typed, validated intent. The control plane re-checks everything.",
               "Even a manipulated AI cannot get a payment through — there is no path to money."])]

A += [para("5. AI buyer flow (SELL)", H2), diag("v2_ai_buyer","Figure 3 — A purchase from request to Passport"),
      para("The AI understands, searches, recommends and builds a cart. AegisPay locks prices, checks policy/risk and authorizes. If it is high value, a human approves first. Only then does Razorpay move money.", BODY)]
A += [para("6. Merchant growth flow (GROW)", H2), diag("v2_growth","Figure 4 — From sales data to a measured, budget-limited campaign"),
      para("The AI spots real patterns and proposes an offer. Fixed rules cap discount, budget and margin. A merchant approves, it runs inside budget and is A/B tested, so the uplift is measured, not claimed.", BODY)]

A += [PageBreak(), para("7. Policy / Risk / Authorization", H2),
      diag("v2_gate","Figure 5 — Every money action passes a deterministic gate"),
      bullets(["<b>Policy</b> is versioned and fixed by the merchant — the AI cannot change it.",
               "<b>Risk</b> is explainable: a score plus the reasons (new merchant, unusual amount, new device).",
               "<b>Authorization</b> is bound to one transaction, expires, and can't be reused."])]

A += [para("8. Human approval", H2),
      diag("v2_approval","Figure 6 — A high-risk action goes to a person, safely"),
      para("An approval is scoped to this exact action, expires soon, and can be used only once. It cannot be replayed or stretched into a bigger purchase.", BODY)]

A += [para("9. Payment state machine", H2),
      para("A payment is not a single 'success/fail' moment. It has a real lifecycle. The important state is <b>UNKNOWN</b> — when we don't know what happened yet.", BODY),
      diag("v2_payment_state","Figure 7 — Payment states, including the UNKNOWN recovery path"),
      para("Front-end state is never trusted. The payment moves only on provider truth from a verified webhook or reconciliation.", BODY)]

A += [PageBreak(), para("10. Razorpay integration", H2),
      bullets(["One <b>PaymentProvider</b> interface; Razorpay is just one adapter.",
               "Test Mode first: create order, initiate, capture, refund, fetch, verify webhook.",
               "Provider secrets are read only inside the adapter, never in logs or the AI."]),
      para("11. Webhook + idempotency", H2),
      diag("v2_webhook","Figure 8 — Webhooks are untrusted until verified and deduped"),
      bullets(["Signature + timestamp checked first; bad ones are ignored and alerted.",
               "A duplicate event is a no-op (no double effect).",
               "Every money request carries an idempotency key — designed to prevent duplicate charges."])]

A += [para("12. Reconciliation (unknown payments)", H2),
      diag("v2_reconcile","Figure 9 — Unknown payments are checked, never blindly retried"),
      para("If Razorpay times out, we do not retry. We wait, ask the provider what really happened, and then finish or fail safely. This is designed so a payment cannot be charged twice.", BODY)]

A += [para("13. Cart, price and inventory protection", H2),
      table([["Guard","What it does"],
             ["Server-owned prices","Prices come from the database, never from the AI or the client."],
             ["Cart hash","Signed snapshot of the cart; a change invalidates the authorization."],
             ["Price version","A price change is detected; the checkout is re-validated."],
             ["Inventory reservation","Stock is held/locked during checkout so it can't oversell."],
             ["Cart expiry","An old cart expires; you can't pay with a stale quote."]],
            [44*mm,130*mm])]

A += [PageBreak(), para("14. Agent security", H2),
      table([["Threat","Protection"],
             ["Prompt injection","Catalog is data, never instructions; intent is schema-validated."],
             ["Tool abuse","Only safe tools are exposed to the AI; no money tool."],
             ["Agent impersonation","Signed credentials, session binding, revocation."],
             ["Agent self-escalation","No tool lets an agent change its own limits or policy."]],
            [42*mm,132*mm])]

A += [para("15. Multi-tenancy", H2), diag("v2_tenant","Figure 10 — Many merchants, one database, hard isolation"),
      para("Every row has a tenant id, and the database enforces it with Row-Level Security. Merchant A can never read Merchant B's data, even by mistake.", BODY)]

A += [para("16. Audit + Transaction Passport", H2), diag("v2_audit","Figure 11 — Events are linked by hash into a tamper-evident chain"),
      para("Every decision is written to an append-only, hash-chained ledger. A Transaction Passport bundles the who/what/why/approval/provider so anyone can verify a purchase end-to-end. The chain is <b>tamper-evident</b>: changing an old record breaks the links.", BODY)]

A += [PageBreak(), para("17. AWS deployment", H2), diag("v2_aws","Figure 12 — Simple, boring, reliable infrastructure"),
      table([["Layer","Choice","Why"],
             ["Compute","AWS ECS (not Kubernetes)","Simple to run, easy to scale, less to go wrong at this scale."],
             ["Data","RDS PostgreSQL multi-AZ","Auditable, correct, per-tenant security, easy backup."],
             ["Cache / locks","ElastiCache Redis","Fast caching, rate limits, locks — never the source of truth."],
             ["Queue","SQS","Reliable background work (webhooks, reconciliation)."],
             ["Secrets","AWS Secrets Manager + KMS","Keys never in code, logs, or the AI."],
             ["Edge","CloudFront + WAF","TLS + protection."],
             ["AI runtime","Separate FastAPI service","No DB, no secrets, no money tools."]],
            [30*mm,66*mm,78*mm])]

A += [para("18. Observability + disaster recovery", H2),
      bullets(["Metrics: payment success/failure/unknown rate, policy/risk/approval rates, webhook duplicates, reconciliation success.",
               "Logs: correlation, tenant, transaction and agent ids; secrets and PII are never logged.",
               "Tracing: user → agent → tool → policy → risk → authorization → payment → webhook.",
               "DR targets: backups + point-in-time restore, RPO ≤ 15 minutes, RTO ≤ 1 hour, multi-AZ, quarterly restore drills.",
               "A global kill switch can stop all new AI-initiated money movement instantly if something looks wrong."])]

A += [para("19. Production-readiness checklist", H2),
      table([["Area","Must be in place"],
             ["Payments","Idempotency, state machine, webhook verification, reconciliation, refund caps."],
             ["AI","Structured output, tool allowlist, policy + risk, human approval, red-team passing."],
             ["Security","Auth (user, agent, service), secrets, encryption, rate limits, tenant isolation."],
             ["Trust","Versioned policy, explainable risk, Transaction Passport, tamper-evident audit."],
             ["Reliability","Timeouts, retries, circuit breakers, queue + DLQ, backups + DR."],
             ["Observability","Metrics, logs, tracing, alerts, dashboards."]],
            [40*mm,134*mm])]

A += WHY("ARCH")

out1 = build("AegisPay-Architecture-V2.pdf", A)
print("PDF1:", out1.name)

# ============ PDF 2 — GROW ============
G = [Spacer(1,24), para("AEGISPAY — GROW", TITLE), para("The merchant revenue agent (simplified)", SUB),
     Spacer(1,8), para("How AI safely grows a merchant's revenue — in one minute.", BODY), Spacer(1,12)]

G += [para("The one-minute flow", H2), diag("grow_flow","Figure 1 — From sales data to a measured, budget-limited campaign"),
      numbered(["<b>Merchant data.</b> Read grouped sales (no customer PII needed).",
                "<b>Find an opportunity.</b> Real correlation: people who buy shoes often buy socks.",
                "<b>AI proposes an offer.</b> A small cross-sell, a discount, a target group, a budget.",
                "<b>Check fixed rules.</b> Max discount, max budget, minimum margin, contact frequency.",
                "<b>Estimate uplift.</b> An honest range (e.g. +3% to +8%), never a fake promise.",
                "<b>Merchant approves.</b> The AI cannot start it by itself.",
                "<b>Run inside budget.</b> It stops the moment the budget is spent.",
                "<b>A/B test.</b> Some customers get the offer, some don't.",
                "<b>Measure real uplift.</b> Compare the two groups, not a guess.",
                "<b>Learn.</b> Repeat what worked, drop what didn't."]),
      Spacer(1,6), para("The rule that makes it safe: <b>the AI proposes; a merchant decides; fixed rules always bind.</b>", BOXD)]

G += [PageBreak(), para("What it does and what it never does", H2),
      table([["GROW does","GROW never does"],
             ["Suggest cross-sells, upsells and bundles","Change a price on its own"],
             ["Draft a campaign with a capped budget","Exceed the approved budget"],
             ["Propose discounts under a cap","Give an unlimited discount"],
             ["Estimate revenue with a range","Guarantee a number"],
             ["Ask the merchant to approve","Approve its own campaign"],
             ["Contact customers within a limit","Spam customers"]],
            [86*mm,88*mm]),
      para("The fixed rules", H2),
      diag("grow_rules","Figure 2 — Every proposed offer is filtered by fixed limits before a human sees it"),
      para("These limits are set by the merchant and cannot be changed by the AI. That is what stops a bad idea before it becomes a bad spend.", BODY)]

G += [PageBreak(), para("Budget ledger (no overspend)", H2),
      diag("grow_budget","Figure 3 — The campaign spends only up to its budget, then pauses"),
      para("A campaign has a budget and a spent counter. Every discount costs against it. When spent reaches the budget, the offer stops by itself.", BODY),
      para("Honest revenue measurement", H2),
      bullets(["A/B test: a control group (no offer) vs a test group (offer).",
               "Incremental revenue = test group − control group, so you see the real effect.",
               "Results are labelled as estimates; we never present a plausible guess as a fact."]),
      para("Human approval + kill switch + audit", H2),
      bullets(["Every campaign needs a merchant approval before it runs.",
               "A global kill switch can stop all campaign spending instantly if needed.",
               "Every proposal, approval, spend and result is written to the tamper-evident audit trail."])]

G += WHY("GROW")
out2 = build("AegisPay-GROW.pdf", G)
print("PDF2:", out2.name)

# ============ PDF 3 — SELL ============
S = [Spacer(1,24), para("AEGISPAY — SELL", TITLE), para("The AI buyer checkout (simplified)", SUB),
     Spacer(1,8), para("How a customer safely buys through an AI — in one minute.", BODY), Spacer(1,12)]

S += [para("The one-minute flow", H2), diag("sell_flow","Figure 1 — From 'I want running shoes' to a verified purchase"),
      numbered(["<b>User asks.</b> “Find running shoes under ₹4,000.”",
                "<b>Understand intent.</b> The AI turns it into a typed, structured intent (product, budget, limits).",
                "<b>Search catalog.</b> A real query against the merchant's products.",
                "<b>Recommend.</b> The best few, priced by the store.",
                "<b>Build cart.</b> Prices are server-owned; the AI can't change them.",
                "<b>Lock price + reserve stock.</b> A price version is captured and inventory is held.",
                "<b>Validate intent.</b> Strictly checked — nothing malformed gets through.",
                "<b>Policy + Risk.</b> Limits and an explainable risk score.",
                "<b>Authorization.</b> Scoped, expiring, bound to this one purchase.",
                "<b>Human if needed.</b> High value → a person approves first.",
                "<b>Payment Engine → Razorpay.</b> Only approved money moves.",
                "<b>Verified webhook / reconcile.</b> Provider truth resolves the outcome.",
                "<b>Transaction Passport.</b> Full, verifiable proof of the purchase."]),
      Spacer(1,6), para("The core rule: <b>the AI reasons and proposes; AegisPay decides; Razorpay executes only approved actions.</b>", BOXD)]

S += [PageBreak(), para("Key safety details", H2),
      table([["What","What it means"],
             ["Typed intent","The AI's output is a strict, validated schema — not free text."],
             ["Server-owned prices","Price comes from the database, never from the AI or the browser."],
             ["Cart hash","A snapshot of the cart; any change invalidates the authorization."],
             ["Price version + inventory reserve","A price change is caught; stock is held so it can't oversell."],
             ["Cart expiry","A stale cart expires — you can't pay an old quote."],
             ["Idempotency","Same request twice = one result. Designed to prevent duplicate charges."],
             ["Scoped/expiring authorization","Bound to one purchase, expires, single-use."],
             ["Agent identity","The agent is authenticated and scoped; it can't impersonate or elevate."],
             ["Prompt injection defense","Catalog is data, not instructions; the intent is validated."],
             ["Failure recovery","Timed-out payments are reconciled, never blindly retried."],
             ["Refund/cancellation","Safe, idempotent, capped to what was captured."],
             ["Audit trail","Every step is recorded tamper-evidently."]],
            [46*mm,128*mm])]

S += [para("Payment safety (the important part)", H2),
      diag("sell_safety","Figure 2 — The payment lifecycle, including the UNKNOWN recovery path"),
      para("if Razorpay is slow, the payment becomes UNKNOWN. We do not retry — that could charge twice. We check with the provider, then finish or fail safely. This is <b>designed to prevent duplicate charges</b>.", BODY),
      para("Refund & cancellation", H2),
      bullets(["Refunds are idempotent and capped to the captured amount.",
               "Cancellation only from an allowed state, and it is audited.",
               "A person can always review and reverse an AI-driven action."])]

S += WHY("SELL")
out3 = build("AegisPay-SELL.pdf", S)
print("PDF3:", out3.name)
print("done")
