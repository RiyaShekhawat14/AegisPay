import subprocess, json
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer,
                                Image, Table, TableStyle, PageBreak, KeepTogether,
                                ListFlowable, ListItem)

ROOT=Path(r"C:\Users\hp\OneDrive\Desktop\AgeisPay"); BUILD=ROOT/"pdf"/"_build_v4s"; BUILD.mkdir(parents=True,exist_ok=True)
MMDC=r"C:\Users\hp\AppData\Roaming\npm\node_modules\@mermaid-js\mermaid-cli\src\cli.js"
CFG=BUILD/"mermaid.json"
json.dump({"theme":"neutral","themeVariables":{"fontSize":"18px","fontFamily":"Helvetica","lineColor":"#64748B","primaryColor":"#FFFFFF","primaryBorderColor":"#334155","clusterBkg":"#F4F5F7"}}, open(CFG,"w"))
OUT=ROOT/"AegisPay-Agentic-Commerce-Architecture-V4.pdf"

D={
"gateway": r"""
flowchart LR
  A2A["A2A"] & MCP["MCP"] & UCP["UCP"] & ACP["ACP"] & AP2["AP2"] & X4["x402"] & A2UI["A2UI"] & UPI["UPI / UAP"] --> G["Protocol Gateway"]
  G --> N["Canonical Intent"]
  N --> C["Control Plane"]
  C --> P["Policy"] --> R["Risk"] --> AU["Authorize"] --> PAY["Payment"]
  PAY --> PROV["Razorpay / UPI / x402"]
""",
"system": r"""
flowchart TB
  A["AI / Agent layer<br/>(proposes)"] --> GW["Protocol Gateway<br/>(one entry)"]
  GW --> CP["AegisPay Control Plane<br/>Policy - Risk - Authorization - Payment - Audit"]
  CP --> DB["PostgreSQL + RLS"]
  CP --> RD["Redis"]
  CP --> Q["SQS"]
  CP --> PR["Razorpay / UPI / x402"]
  PR --> WH["Verified webhook"] --> CP
""",
"decision": r"""
flowchart TD
  I["Intent"] --> P["Policy"] --> R["Risk"] --> A{"OK?"}
  A -- "allow" --> AU["Authorize"] --> PAY["Pay"]
  A -- "human" --> HU["Human approves"] --> PAY
  A -- "deny" --> NO["Block + audit"]
""",
"payment": r"""
stateDiagram-v2
  [*] --> Created
  Created --> Cart_Locked
  Cart_Locked --> Auth_Pending
  Auth_Pending --> Authorized
  Auth_Pending --> Expired
  Authorized --> Pay_Pending
  Pay_Pending --> Paid
  Pay_Pending --> Failed
  Pay_Pending --> Unknown
  Unknown --> Paid: reconcile finds success
  Unknown --> Failed: reconcile finds failed
  Paid --> Completed
  Paid --> Refund_Pending
  Refund_Pending --> Refunded
""",
"webhook": r"""
flowchart LR
  W["Webhook"] --> V["Verify signature"] --> D{"Duplicate?"}
  D -- "yes" --> N["Safe no-op"]
  D -- "no" --> S["Apply to state"] --> A["Audit"]
""",
"outbox": r"""
flowchart LR
  TX["DB txn"] --> ST["State update"]
  TX --> OB["Outbox row"]
  OB --> WK["Worker"] --> Q["SQS"]
""",
"sell": r"""
flowchart LR
  U["User"] --> I["Intent"] --> CA["Cart"] --> OR["Order"] --> AUZ["Authorize"] --> PA["Razorpay"] --> WH["Webhook"] --> PP["Passport"]
""",
"grow": r"""
flowchart LR
  M["Merchant"] --> OP["Opportunity"] --> CAM["Campaign"] --> BL["Budget ledger"] --> ORD["Orders"] --> MEAS["Measure"]
""",
"rls": r"""
flowchart LR
  REQ["Request"] --> AUTH["Auth + tenant"] --> SET["SET LOCAL tenant_id"] --> RLS["Row-Level Security"] --> DB["Database"]
""",
}
def render(text,name):
    mmd=BUILD/(name+".mmd"); png=BUILD/(name+".png"); mmd.write_text(text.strip(),encoding="utf-8")
    if png.exists(): png.unlink()
    try: subprocess.run(["node",MMDC,"-c",str(CFG),"-q","-i",str(mmd),"-o",str(png),"-s","2"],check=True,capture_output=True)
    except subprocess.CalledProcessError as e: raise RuntimeError(f"{name}: {e.stderr.decode()[:300]}")
    if not png.exists(): raise RuntimeError(f"mmdc failed {name}")
    return png
for n,s in D.items(): render(s,n)
print("Rendered",len(D))

LR=15*mm; TB=15*mm
ACC=colors.HexColor("#8B1E3F"); INK=colors.HexColor("#17181C"); MUT=colors.HexColor("#667085"); BORD=colors.HexColor("#E5E7EB"); NEUT=colors.HexColor("#F4F5F7")
st=getSampleStyleSheet()
H1=ParagraphStyle("H1",parent=st["Heading1"],fontName="Helvetica-Bold",fontSize=17,textColor=ACC,spaceAfter=7,spaceBefore=2)
H2=ParagraphStyle("H2",parent=st["Heading2"],fontName="Helvetica-Bold",fontSize=13.5,textColor=INK,spaceAfter=6,spaceBefore=13)
BODY=ParagraphStyle("Body",parent=st["BodyText"],fontName="Helvetica",fontSize=10.4,leading=15,spaceAfter=6,textColor=INK)
LI=ParagraphStyle("LI",parent=BODY,leftIndent=14,spaceAfter=3)
CAP=ParagraphStyle("Cap",parent=BODY,fontSize=8.8,leading=11,textColor=MUT,alignment=TA_CENTER,spaceBefore=2,spaceAfter=10)
CALL=ParagraphStyle("Call",parent=BODY,fontName="Helvetica-Bold",fontSize=10.6,leading=15.5,textColor=ACC,backColor=colors.HexColor("#FDF6F7"),borderPadding=8,borderWidth=0.6,borderColor=colors.HexColor("#E7BCCA"),spaceAfter=9)
TITLE=ParagraphStyle("Title",parent=st["Title"],fontName="Helvetica-Bold",fontSize=23,textColor=INK,alignment=TA_CENTER,leading=30,spaceAfter=5)
SUB=ParagraphStyle("Sub",parent=BODY,fontSize=12,textColor=ACC,alignment=TA_CENTER,spaceAfter=2)
TH=ParagraphStyle("th",parent=BODY,fontName="Helvetica-Bold",fontSize=9,textColor=colors.white,leading=12)
TD=ParagraphStyle("td",parent=BODY,fontSize=8.8,leading=12,textColor=INK)
NOTE=ParagraphStyle("note",parent=BODY,fontSize=9,leading=12.6,textColor=MUT)

def para(t,s=BODY): return Paragraph(t,s)
def bullets(it): return ListFlowable([ListItem(Paragraph(t,LI),leftIndent=12) for t in it],bulletType="bullet",start="\u2022",leftIndent=12,bulletFontSize=8.5,spaceAfter=6)
def table(rows,widths):
    data=[[Paragraph(c,TH) for c in rows[0]]]
    for r in rows[1:]: data.append([Paragraph(c,TD) for c in r])
    t=Table(data,colWidths=widths,hAlign="LEFT",repeatRows=1)
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),ACC),("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#FAFAFB")]),
      ("GRID",(0,0),(-1,-1),0.4,BORD),("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),6),
      ("RIGHTPADDING",(0,0),(-1,-1),6),("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4)]))
    return t
def image_flow(path,max_w=183*mm):
    from PIL import Image as PILImage
    iw,ih=PILImage.open(path).size; r=ih/float(iw); w=min(max_w,iw/3.2); return Image(str(path),width=w,height=w*r)
def diag(name,cap,max_w=183*mm):
    from PIL import Image as PILImage
    p=BUILD/(name+".png"); iw,ih=PILImage.open(p).size; r=ih/float(iw); w=min(max_w,230*mm/r)
    return KeepTogether([Spacer(1,3),Image(str(p),width=w,height=w*r),Paragraph(cap,CAP)])

def onp(c,d):
    c.saveState(); c.setFont("Helvetica",8); c.setFillColor(MUT)
    c.drawString(LR,9*mm,"AegisPay · Agentic Commerce Architecture V4")
    c.drawRightString(A4[0]-LR,9*mm,f"Page {d.page}")
    c.setStrokeColor(BORD); c.setLineWidth(.5); c.line(LR,13*mm,A4[0]-LR,13*mm); c.restoreState()
frame=Frame(LR,TB,A4[0]-2*LR,A4[1]-2*TB,id="n",leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)
doc=BaseDocTemplate(str(OUT),pagesize=A4,leftMargin=LR,rightMargin=LR,topMargin=TB,bottomMargin=TB,title="AegisPay Agentic Commerce Architecture V4",author="AegisPay Engineering")
doc.addPageTemplates([PageTemplate(id="all",frames=[frame],onPage=onp)])

F=[Spacer(1,20), para("AEGISPAY",TITLE), para("Agentic Commerce Architecture V4",SUB),
   Spacer(1,8), para("The protocol-aware Trust &amp; Growth Layer for Agentic Commerce. AI proposes. AegisPay deterministically validates, authorizes and controls. Razorpay executes only approved actions.",BODY),
   Spacer(1,6), para("Different protocols can enter AegisPay, but none can bypass the AegisPay Control Plane.",CALL)]

F+=[PageBreak(), para("1. The Protocol Gateway",H2),
  para("Every external protocol enters through <b>one</b> gateway, is normalized into a single canonical intent, and only then reaches the control plane. A new protocol is a new adapter — it changes the transport, never the money path.",BODY),
  diag("gateway","Figure 1 — All protocols collapse into one normalized intent")
  ,para("Protocols &amp; maturity",H2),
  table([["Protocol","Role","Maturity"],
   ["MCP","controlled agent tools / context","Core"],
   ["A2A","agent-to-agent communication","Adapter-ready"],
   ["UCP","commerce interoperability","Adapter-ready"],
   ["ACP","agentic checkout / commerce","Adapter-ready"],
   ["AP2","payment mandates &amp; verifiable authorization","Experimental"],
   ["x402","machine / pay-per-use payments","Experimental"],
   ["A2UI","agent-driven UI","Experimental"],
   ["NPCI UAP / UPI","India agentic-payment ecosystem","Future"]],[56*mm,74*mm,44*mm]),
  para("Maturity is honest: <b>Core</b> is implemented, <b>Adapter-ready</b> has a mapping, <b>Experimental</b> maps only where semantics align, <b>Future</b> is a watch-list with no compliance claim.",NOTE)]

F+=[PageBreak(), para("2. The full system",H2), diag("system","Figure 2 — One control plane, one money path"),
  para("The AI layer proposes. Everything funnels through the gateway into the control plane, which gates and executes. There is exactly one money path.",BODY),
  para("AI / Control-plane boundary",H2),
  bullets(["The AI runtime has <b>no payment keys, no database credentials, no unrestricted money tools, no policy mutation</b>.",
           "It can only produce an intent that the control plane gates — regardless of which protocol it arrived through."])]

F+=[PageBreak(), para("3. Decision path (Policy · Risk · Authorization)",H2), diag("decision","Figure 3 — Every money action passes a deterministic gate"),
  bullets(["<b>Policy</b> is versioned and merchant-owned; the AI cannot change it.",
           "<b>Risk</b> is explainable: a score plus the reasons.",
           "<b>Authorization</b> is scoped, transaction-bound, expiring and single-use.",
           "<b>Human approval</b> happens only when required, then resumes from a checkpoint."])]

F+=[para("4. Payment state machine",H2), diag("payment","Figure 4 — UNKNOWN is first-class and resolved only by provider truth"),
  para("We never blindly retry an UNKNOWN payment — we reconcile (ask the provider), then complete or fail safely.",BODY)]

F+=[PageBreak(), para("5. Webhooks, idempotency &amp; outbox",H2),
  table([["Concern","How it works"],
   ["Webhook security","verify signature + timestamp, then deduplicate; bad/duplicate events are safe no-ops"],
   ["Idempotency","every financial command carries a key; designed to prevent duplicate financial effects"],
   ["Transactional outbox","state change + outbox event commit together; a worker publishes to SQS"],
   ["Reconciliation","UNKNOWN payments are resolved from provider truth, never a blind retry"]],[56*mm,118*mm]),
  diag("webhook","Figure 5 — Webhooks are untrusted until verified and deduped"),
  diag("outbox","Figure 6 — State change and event are written in one transaction")]

F+=[para("6. SELL &amp; GROW flows",H2), diag("sell","Figure 7 — SELL: intent → cart → order → authorize → Razorpay → webhook → Passport"),
  diag("grow","Figure 8 — GROW: opportunity → campaign → budget ledger → orders → measure")]

F+=[PageBreak(), para("7. Security &amp; multi-tenancy",H2),
  table([["Concern","How it's handled"],
   ["Protocol security","auth per protocol, schema validation, replay protection, tool allowlisting"],
   ["Agent security","prompt-injection defense, no self-escalation, signed credentials, revocable"],
   ["Cart / price / inventory","server-owned price, cart hash, price version, inventory reservation, expiry, product ownership lock"],
   ["Refunds","controlled; the AI has no unrestricted refund tool"],
   ["Multi-tenancy","shared PostgreSQL + RLS; app role cannot bypass RLS; tenant set server-side with SET LOCAL"]],[56*mm,118*mm]),
  diag("rls","Figure 9 — Tenant context is set server-side; RLS enforces isolation")]

F+=[para("8. Production checklist",H2),
  table([["Area","In place"],
   ["AI","no money path, tool allowlist, structured output, policy + risk, human approval"],
   ["Protocols","single gateway, adapters normalize, protocol security, honest maturity"],
   ["Payments","idempotency, state machine, webhook verify + dedupe, reconciliation, refund caps"],
   ["Trust","versioned policy, explainable risk, scoped/expiring authz, Passport, outbox"],
   ["Growth","atomic budget ledger, kill switch, A/B incremental measurement"],
   ["Security","secrets isolation, RLS app role, encryption, rate limits"],
   ["Reliability","timeouts, retries, circuit breakers, outbox + DLQ, backups + DR, SLOs"]],[40*mm,134*mm])]

F+=[Spacer(1,10), para("Why AegisPay is different",H2),
  para("Different protocols can enter AegisPay, but none can bypass the AegisPay Control Plane.",CALL),
  bullets(["<b>One control plane.</b> Every protocol resolves to a normalized intent the control plane gates.",
           "<b>No direct money path.</b> The AI has no keys, no DB credentials, no money tools.",
           "<b>Provider truth.</b> Payment finality comes only from verified webhooks or reconciliation.",
           "<b>Deterministic authorization.</b> Policy, risk and a scoped/expiring authorization gate every action.",
           "<b>Tamper-evident.</b> Every decision is recorded in a hash-chained audit ledger and Transaction Passport."])]

doc.build(F)
print("PDF written:",OUT,OUT.stat().st_size,"bytes")
