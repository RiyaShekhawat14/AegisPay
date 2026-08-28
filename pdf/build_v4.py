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
BUILD = ROOT/"pdf"/"_build_v4"; BUILD.mkdir(parents=True, exist_ok=True)
MMDC = r"C:\Users\hp\AppData\Roaming\npm\node_modules\@mermaid-js\mermaid-cli\src\cli.js"
OUT = ROOT/"AegisPay-Agentic-Commerce-Architecture-V4.pdf"

D = {
"v4_overview": r"""
flowchart TB
  CLIENTS["Agents & external systems (A2A / MCP / UCP / ACP / AP2 / x402 / A2UI / UPI)"]
  subgraph GW["PROTOCOL GATEWAY"]
    direction TB
    AD[Protocol Adapters]
    NORM[Normalized AegisPay Intent]
  end
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
  CLIENTS --> AD
  AD --> NORM
  NORM --> ORCH
  ORCH --> PG["PostgreSQL<br/>state + RLS + audit + outbox"]
  ORCH --> RD["Redis<br/>cache + locks + rate"]
  ORCH --> SQ["SQS<br/>async events"]
  PAY --> RAZ[Razorpay / UPI / x402]
  RAZ --> WH[Verified webhook]
  WH --> REC
  REC --> PAS[Transaction Passport]
""",
"v4_gateway": r"""
flowchart LR
  A2A[A2A] & MCP[MCP] & UCP[UCP] & ACP[ACP] & AP2[AP2] & X4[x402] & A2UI[A2UI] & UPI["UPI / UAP"] --> GATE[Protocol Gateway]
  GATE --> AD[Adapter]
  AD --> NI[Normalized Intent]
  NI --> CP[AegisPay Control Plane]
  CP --> P[Policy]
  P --> R[Risk]
  R --> AU[Authorization]
  AU --> PAY[Payment]
  PAY --> PROV["Razorpay / UPI / x402"]
""",
"v4_adapter": r"""
flowchart LR
  subgraph X["External protocol"]
    P1["A2A task / MCP tool / ACP message / AP2 mandate / x402 pay"]
  end
  subgraph G["Gateway (per adapter)"]
    A1[Authenticate identity]
    A2[Validate schema]
    A3[Map to canonical intent]
    A4[Check scope + allowlist]
  end
  X --> A1 --> A2 --> A3 --> A4 --> CP[AegisPay Control Plane]
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
  AI2[Proposal] --> POL[Policy]
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
  A1 --> R1{Replay?}
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
  APP["Application role - no bypass"] --> PG[(PostgreSQL RLS)]
  MIG["Migration role - schema only"] --> PG
  PG --> R[RLS enforced per tenant_id]
""",
"a_aws": r"""
flowchart TB
  US[CloudFront + WAF]
  US --> LB[Load Balancer]
  LB --> ECS["ECS - Control Plane"]
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

LR=15*mm; TB=14*mm
ACC=colors.HexColor("#8B1E3F"); INK=colors.HexColor("#17181C"); MUT=colors.HexColor("#667085")
BORD=colors.HexColor("#E5E7EB"); NEUT=colors.HexColor("#F4F5F7")
OK=colors.HexColor("#15803D"); WARN=colors.HexColor("#B45309"); ERR=colors.HexColor("#DC2626"); INFO=colors.HexColor("#2563EB")
st=getSampleStyleSheet()
H1=ParagraphStyle("H1",parent=st["Heading1"],fontName="Helvetica-Bold",fontSize=16.5,textColor=ACC,spaceAfter=7,spaceBefore=2)
H2=ParagraphStyle("H2",parent=st["Heading2"],fontName="Helvetica-Bold",fontSize=13,textColor=INK,spaceAfter=6,spaceBefore=13)
BODY=ParagraphStyle("Body",parent=st["BodyText"],fontName="Helvetica",fontSize=10,leading=14.4,spaceAfter=6,textColor=INK)
LI=ParagraphStyle("LI",parent=BODY,leftIndent=14,spaceAfter=3)
CAP=ParagraphStyle("Cap",parent=BODY,fontSize=8.6,leading=11,textColor=MUT,alignment=TA_CENTER,spaceBefore=2,spaceAfter=10)
CALL=ParagraphStyle("Call",parent=BODY,fontName="Helvetica-Bold",fontSize=10.4,leading=15.2,textColor=ACC,backColor=colors.HexColor("#FDF6F7"),borderPadding=8,borderWidth=0.6,borderColor=colors.HexColor("#E7BCCA"),spaceAfter=9)
TITLE=ParagraphStyle("Title",parent=st["Title"],fontName="Helvetica-Bold",fontSize=21,textColor=INK,alignment=TA_CENTER,leading=28,spaceAfter=5)
SUB=ParagraphStyle("Sub",parent=BODY,fontSize=11.5,textColor=ACC,alignment=TA_CENTER,spaceAfter=2)
TH=ParagraphStyle("th",parent=BODY,fontName="Helvetica-Bold",fontSize=8.1,textColor=colors.white,leading=11)
TD=ParagraphStyle("td",parent=BODY,fontSize=7.9,leading=11,textColor=INK)
NOTE=ParagraphStyle("note",parent=BODY,fontSize=8.9,leading=12.4,textColor=MUT)

def para(t,s=BODY): return Paragraph(t,s)
def bullets(it): return ListFlowable([ListItem(Paragraph(t,LI),leftIndent=12) for t in it],bulletType="bullet",start="\u2022",leftIndent=12,bulletFontSize=8,spaceAfter=6)
def numbered(it): return ListFlowable([ListItem(Paragraph(t,LI),leftIndent=16) for t in it],bulletType="1",start=1,leftIndent=16,spaceAfter=6)
def table(rows,widths):
    data=[[Paragraph(c,TH) for c in rows[0]]]
    for r in rows[1:]: data.append([Paragraph(c,TD) for c in r])
    t=Table(data,colWidths=widths,hAlign="LEFT",repeatRows=1)
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),ACC),("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#FAFAFB")]),
      ("GRID",(0,0),(-1,-1),0.4,BORD),("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),4),
      ("RIGHTPADDING",(0,0),(-1,-1),4),("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3)]))
    return t
def image_flow(path,max_w=178*mm):
    from PIL import Image as PILImage
    iw,ih=PILImage.open(path).size; r=ih/float(iw); w=min(max_w,iw/4.0); return Image(str(path),width=w,height=w*r)
def diag(name,cap): return KeepTogether([Spacer(1,3),image_flow(BUILD/(name+".png")),Paragraph(cap,CAP)])

def onp(c,d):
    c.saveState(); c.setFont("Helvetica",8); c.setFillColor(MUT)
    c.drawString(LR,8*mm,"AegisPay · Agentic Commerce Architecture V4")
    c.drawRightString(A4[0]-LR,8*mm,f"Page {d.page}")
    c.setStrokeColor(BORD); c.setLineWidth(.5); c.line(LR,12*mm,A4[0]-LR,12*mm); c.restoreState()
frame=Frame(LR,TB,A4[0]-2*LR,A4[1]-2*TB,id="n",leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)
doc=BaseDocTemplate(str(OUT),pagesize=A4,leftMargin=LR,rightMargin=LR,topMargin=TB,bottomMargin=TB,title="AegisPay Agentic Commerce Architecture V4",author="AegisPay Engineering")
doc.addPageTemplates([PageTemplate(id="all",frames=[frame],onPage=onp)])

def sec(n,t): return [para(f"{n}. {t}",H2)]
def why():
    return [Spacer(1,9), para("Why AegisPay is different",H2),
            para("Different protocols can enter AegisPay, but none can bypass the AegisPay Control Plane.",CALL),
            bullets(["<b>One control plane.</b> Every protocol resolves to a normalized intent that the control plane gates deterministically.",
                     "<b>No direct money path.</b> The AI runtime has no payment keys, no DB credentials, no unrestricted money tools.",
                     "<b>Deterministic authorization.</b> Policy, risk and a scoped, expiring authorization gate every action.",
                     "<b>Provider truth.</b> Payment finality comes from verified webhooks or reconciliation, never a guess.",
                     "<b>Escape hatch free.</b> A new protocol is a new adapter over the same canonical model — it cannot introduce a new money path.",
                     "<b>Tamper-evident.</b> Every decision is recorded in a hash-chained audit ledger and Transaction Passport."])]

F=[Spacer(1,21), para("AEGISPAY",TITLE), para("Agentic Commerce Architecture V4",SUB),
   Spacer(1,8), para("The protocol-aware Trust &amp; Growth Layer for Agentic Commerce. AI proposes. AegisPay deterministically validates, authorizes and controls. Razorpay executes only approved actions.",BODY),
   Spacer(1,7), para("Different protocols can enter AegisPay, but none can bypass the AegisPay Control Plane.",CALL)]

F+=[PageBreak()]+sec(1,"What is AegisPay?")+[para("AegisPay sits between AI agents and payment providers. This V4 adds the modern agentic-commerce protocol ecosystem as a single, unified entry point: every protocol enters through one gateway and collapses into one normalized intent before the control plane.",BODY),
  table([["Pillar","What it means"],["GROW","AI helps a merchant increase revenue (upsell, cross-sell, bundles, campaigns, experiments)."],
         ["SELL","AI buyers understand intent, discover, recommend, build carts, get authorization and pay."],
         ["PROTECT","AI can reason and recommend, but never directly controls money."]],[30*mm,144*mm])]

F+=[PageBreak()]+sec(2,"GROW / SELL / PROTECT")+[diag("v4_overview","Figure 1 - Full system: external protocols -> Protocol Gateway -> Control Plane -> providers"),
  para("Protocols arrive on the left as adapters; they become one normalized intent; the control plane gates it; only then does a provider move money. There is exactly one money path.",BODY)]

F+=[PageBreak()]+sec(3,"The Protocol Gateway")+[
  diag("v4_gateway","Figure 2 - Every protocol enters through the gateway and collapses into one normalized intent"),
  para("A single <b>Protocol Gateway</b> normalizes all external protocols into the <b>canonical AegisPay intent</b>. The core never imports a protocol SDK. A new protocol is a new adapter - it changes the transport, never the money path.",BODY),
  diag("v4_adapter","Figure 3 - Each adapter authenticates, validates, normalizes and scope-checks before the control plane")]

F+=sec(4,"Protocol ecosystem &amp; maturity")+[
  table([["Protocol","Role in AegisPay","Maturity","Honest note"],
   ["MCP","controlled agent tools / context","Core","implemented adapter; safe tools only"],
   ["A2A","agent-to-agent communication","Adapter-ready","agent endpoint over the canonical model"],
   ["UCP","commerce interoperability","Adapter-ready","map to canonical commerce actions"],
   ["ACP","agentic checkout / commerce","Adapter-ready","message &amp; card mapping"],
   ["AP2","payment mandates &amp; verifiable authorization","Experimental","map where semantics align; no claim"],
   ["x402","machine / pay-per-use payments","Experimental","route through a normal provider-funded action"],
   ["A2UI","agent-driven UI","Experimental","watch-list; no claim"],
   ["NPCI UAP / UPI","India agentic-payment ecosystem","Future","watch; no compliance claim"]],
   [44*mm,58*mm,30*mm,42*mm]),
  para("Maturity labels are honest: <b>Core</b> is implemented, <b>Adapter-ready</b> has a mapping, <b>Experimental</b> maps only where semantics align, and <b>Future</b> is a watch-list with no compliance claim. We never state a protocol is supported unless the adapter actually normalizes it.",NOTE)]

F+=[PageBreak()]+sec(5,"Component architecture")+[table([["Component","What it does","Fails safely by"],
  ["Protocol Gateway","authenticate + validate + normalize external protocols","rejects anything it can't normalize"],
  ["Commerce Orchestrator","runs the purchase journey","only allowed state transitions"],
  ["Policy Engine","fixed limits (amount, category, hours)","denies if unsure"],
  ["Risk Engine","explainable score + why","escalates on doubt"],
  ["Authorization Engine","binds consent to one transaction","expires, single-use"],
  ["Payment Engine","provider-abstract lifecycle (Razorpay / UPI / x402)","returns UNKNOWN, never guesses"],
  ["Human Approval","person decides high value","scoped, expiring, non-reusable"],
  ["Webhook Gateway","verifies + dedupes provider events","drops bad/duplicate events"],
  ["Reconciliation","resolves UNKNOWN from provider truth","never retries blindly"],
  ["Audit + Passport","records every decision","tamper-evident chain"]],[40*mm,72*mm,62*mm])]

F+=sec(6,"AI / Control-plane trust boundary")+[diag("a_trust","Figure 4 - The AI thinks; the control plane decides and acts"),
  para("The AI runtime has <b>no payment keys, no database credentials, no unrestricted money tools and no policy mutation capability</b>. A manipulated agent can only produce an intent the control plane gates, regardless of which protocol it arrived through.",BODY)]

F+=sec(7,"SELL flow")+[para("Intent -> catalog -> recommendation -> cart -> authorization -> payment -> verified webhook -> reconciliation -> Passport. Detail in the SELL document.",BODY)]
F+=sec(8,"GROW flow")+[para("Data -> opportunity -> proposal -> rules -> estimate -> approval -> budget -> execution -> A/B -> incremental measurement -> learn. Detail in the GROW document.",BODY)]

F+=[PageBreak()]+sec(9,"Protocol-specific security")+[table([["Concern","How it is handled"],
  ["Authentication","OAuth / client-credential per protocol, mapped to a canonical identity"],
  ["Agent identity","protocol subject -> canonical agent_id; no identity confusion across protocols"],
  ["Schema validation","strict typed schema on the normalized intent; free text never trusted"],
  ["Replay protection","single-use nonce, expiry, binding to a transaction digest"],
  ["Scoped authorization","one action, one amount, one policy version; expiring"],
  ["Idempotency","key per command; designed to prevent duplicate financial effects"],
  ["Tool allowlisting","only safe tools exposed; no money tool to any protocol"],
  ["Tenant isolation","tenant resolved from auth; RLS at the database"]],[52*mm,122*mm])]

F+=sec(10,"Policy / Risk / Authorization")+[diag("a_gate","Figure 5 - Every money action passes a deterministic gate"),
  bullets(["<b>Policy</b> is versioned and merchant-owned; the AI cannot change it.",
           "<b>Risk</b> is explainable: a score plus the reasons.",
           "<b>Authorization</b> is scoped, transaction-bound, expiring and single-use."])]

F+=sec(11,"Human approval")+[diag("a_approval","Figure 6 - A proposal escalates to a person only when required, then resumes"),
  para("An approval is scoped to this exact action, single-use, transaction-bound, expiring and immutable after issuance - it cannot be replayed or stretched into a bigger purchase.",BODY)]

F+=[PageBreak()]+sec(12,"Payment state machine")+[para("The full lifecycle with failure/recovery states. <b>UNKNOWN is a first-class state</b> and exits only on provider truth. We never blindly retry an UNKNOWN payment.",BODY),
  diag("a_payment","Figure 7 - Complete payment state machine, including failure and recovery states")]

F+=sec(13,"Webhook + idempotency")+[diag("a_webhook","Figure 8 - Webhooks are untrusted until verified and deduped; duplicates are safe no-ops"),
  table([["Command","Idempotency scope","Effect"],["create order","order key + request hash","same request returns the same order"],
   ["payment operation","payment key","retry returns the prior provider result"],["refund","(payment, refund key)","one effective refund per key"],
   ["webhook processing","(provider, event id)","duplicates are safe no-ops"],["campaign budget","(campaign, spend request)","atomic reservation; no double-spend"]],[52*mm,52*mm,70*mm]),
  para("Every financial command carries an idempotency key. This is <b>designed to prevent duplicate financial effects</b> - we do not claim duplicate payments are impossible.",NOTE)]

F+=sec(14,"Transactional Outbox")+[diag("a_outbox","Figure 9 - A state change and its event are written in one transaction"),
  para("Because the state update and the outbox event commit together, you cannot have a state change with no event, or an event with no state change. A worker publishes to SQS at-least-once, and consumers are idempotent.",BODY)]

F+=sec(15,"Reconciliation")+[diag("a_reconcile","Figure 10 - UNKNOWN payments are checked, never blindly retried"),
  para("A timed-out or unknown payment is never re-created. We wait, ask the provider, then complete or fail safely, with backoff and escalation.",BODY)]

F+=[PageBreak()]+sec(16,"Cart / Price / Inventory protection")+[diag("a_cart","Figure 11 - If price, version or stock changes, authorization becomes invalid"),
  table([["Guard","What it does"],["Server-owned prices","price from the DB, never the AI or client"],
   ["Cart hash","snapshot; a change invalidates authorization"],["Price version","a price change is detected and checkout re-validated"],
   ["Inventory reservation","stock is held so it can't oversell"],["Cart expiry","a stale cart cannot be paid"],
   ["Product ownership lock","a product belongs to one merchant; cross-merchant reference rejected"]],[40*mm,134*mm])]

F+=sec(17,"Refund architecture")+[para("Refunds are controlled. The AI has <b>no</b> unrestricted refund tool - a refund needs policy, authorization and provider verification.",BODY),
  diag("a_refund","Figure 12 - Refund flow gated by policy and authorization")]

F+=sec(18,"Agent security")+[table([["Threat","Prevention"],["Prompt injection","catalog is data, not instructions; intent schema-validated"],
  ["Tool abuse","only safe tools exposed; no money tool"],["Agent impersonation","signed credentials, session binding, revocation"],
  ["Credential theft","hashed, rotatable, scoped keys"],["Authorization replay","transaction-bound, single-use, expiring authz"],
  ["Self-escalation","no tool to change own limits/policy"],["Malicious catalog / input","typed, validated, injection classifier"]],[52*mm,122*mm])]

F+=[PageBreak()]+sec(19,"Multi-tenancy + RLS")+[para("Shared PostgreSQL, shared schema, Row-Level Security. Two DB roles: an application role that cannot bypass RLS, and a migration/owner role for schema only.",BODY),
  diag("a_tenant","Figure 13 - Application role respects RLS; migration role only changes schema")]

F+=sec(20,"Audit + Transaction Passport")+[diag("a_audit","Figure 14 - Events are linked by hash into a tamper-evident, anchored chain"),
  para("Append-only, RLS read-only, hash-chained and anchored to an immutable root. The Transaction Passport bundles the who/what/why/approval/provider. It is <b>tamper-evident</b>, not tamper-proof.",BODY)]

F+=sec(21,"AWS deployment")+[diag("a_aws","Figure 15 - Two ECS services, managed data, one queue"),
  para("CloudFront + WAF -> ALB -> ECS (Control Plane + AI Runtime). PostgreSQL RDS, Redis, SQS, Secrets Manager + KMS. No Kubernetes - not needed at this scale.",BODY)]

F+=[PageBreak()]+sec(22,"Observability + SLOs")+[para("Dashboards cover the money path, the decision path and AI health. Logs carry correlation, tenant, transaction and agent ids; secrets and PII are never logged.",BODY),
  table([["Signal","What it shows"],["Payment success / UNKNOWN rate","provider finality and ambiguity"],["Webhook latency / duplicate rate","ingest health"],
   ["Policy denial / risk escalation","decision guardrails"],["Human approval latency","time to a decision"],["Reconciliation backlog","stuck UNKNOWN"],
   ["AI tool failure / agent completion","agent reliability"],["Campaign ROI","growth effectiveness"]],[64*mm,110*mm]),
  para("Realistic SLOs: API availability ~99.9% (honest, single-region multi-AZ); RPO &lt;= 15 min; RTO &lt;= 1 hour; payment state transition typically &lt; 2 s; webhook processing within seconds; reconciliation auto-resolves &gt;= 95% of UNKNOWN.",NOTE)]

F+=sec(23,"Disaster recovery")+[para("Multi-AZ, PITR backups (RPO &lt;= 15 min), quarterly restore drills, documented RTO &lt;= 1 hour. Audit integrity stays independent of DB restore via the hash chain + S3 anchor.",BODY)]

F+=sec(24,"Threat model")+[table([["Threat","Attack surface","Impact","Prevent","Detect","Recover"],
 ["Prompt injection","catalog, prompts","unauthorized spend","DATA-only, schema, allowlist","injection + denial alerts","block, revoke, audit"],
 ["Tool abuse","agent tool calls","misuse","allowlist, rate limit, budget","anomaly alerts","throttle, suspend"],
 ["Agent impersonation","credentials","spend as another agent","signed creds, mTLS, session binding","auth anomalies","revoke, re-issue"],
 ["Protocol spoofing","gateway adapters","false intent","authenticate + schema validate","adapter anomalies","reject, reconcile"],
 ["Webhook spoofing","webhook endpoint","false state","signature + timestamp verify","signature failure alerts","ignore, reconcile"],
 ["Replay attack","authz / webhook / approval","repeat an action","single-use, dedupe, nonce","replay detectors","reject"],
 ["Duplicate payment","retries","double effect","idempotency keys","duplicate detectors","return prior result"],
 ["Price manipulation","cart / intent","wrong amount","server-owned prices + hash","price mismatch","reject"],
 ["Tenant escape","queries","cross-tenant leak","RLS + tenant context + app role","isolation tests","block + audit"],
 ["Compromised AI runtime","LLM service","attempt money path","no secrets, no money tools, allowlist","red-team + anomalies","quarantine"]],[42*mm,28*mm,24*mm,36*mm,28*mm,20*mm])]

F+=[PageBreak()]+sec(25,"Failure testing")+[table([["Fault","Detection","Safe state","Recovery","Audit"],
 ["Razorpay timeout","long call / missing webhook","PAYMENT_UNKNOWN","reconcile -> complete/fail","payment.unknown / reconciled"],
 ["Duplicate webhook","same event id","no-op","acknowledge only","webhook.deduped"],
 ["Invalid webhook","signature check","reject, no state","alert + ignore","webhook.failed"],
 ["Price changed in checkout","price version mismatch","authorization invalid","revalidate, ask consent","cart.rejected"],
 ["Inventory unavailable","reservation fails","cart not locked","re-select / notify","inventory.reserve_failed"],
 ["Protocol adapter rejects","schema/auth failure","no intent produced","return typed error","gateway.rejected"],
 ["AI unavailable","timeout","agent path degrades","control plane still reconciles","agent.unavailable"],
 ["Policy violation","policy decision","DENY, no payment","record reason","policy.denied"],
 ["Expired approval","approval timer","expire, no action","re-request approval","approval.expired"],
 ["DB / outbox failure","publish error","transaction rolls back","retry from outbox","outbox.retry"],
 ["Campaign budget exhaustion","atomic check","deny / pause","no spend","campaign.budget_exceeded"]],[34*mm,32*mm,34*mm,44*mm,30*mm])]

F+=sec(26,"Production readiness checklist")+[table([["Area","Present"],
 ["AI","No money path, tool allowlist, structured output, policy + risk, human approval, red-team"],
 ["Protocols","Single gateway, adapters normalize to one intent, protocol security, honest maturity"],
 ["Payments","Idempotency, full state machine, webhook verify + dedupe, reconciliation, refund caps"],
 ["Trust","Versioned policy, explainable risk, scoped/expiring authz, Transaction Passport, outbox"],
 ["Growth","Atomic budget ledger, kill switch, A/B + incremental measurement"],
 ["Security","Auth (user, agent, service), secrets isolation, RLS app role, encryption, rate limits"],
 ["Reliability","Timeouts, retries, circuit breakers, outbox + DLQ, backups + DR, SLOs"],
 ["Observability","Metrics, logs with IDs, tracing, alerts, dashboards"]],[40*mm,134*mm])]

F+=why()

doc.build(F)
print("PDF written:",OUT,OUT.stat().st_size,"bytes")
