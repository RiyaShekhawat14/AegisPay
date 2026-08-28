import os, glob, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(r"C:\Users\hp\OneDrive\Desktop\AgeisPay")
BUILD = ROOT / "pdf" / "_build"
BUILD.mkdir(parents=True, exist_ok=True)
OUT_PDF = ROOT / "AegisPay-Architecture.pdf"

# ---------- Mermaid diagram sources (plain, readable, not complex) ----------
DIAGRAMS = {
"d1_architecture": r"""
flowchart TB
  subgraph S1["You and the AI"]
    direction LR
    U[You] --> AB[AI Buyer Agent]
  end
  subgraph S2["AegisPay Control Plane — decides what is allowed"]
    direction TB
    GW[Agent Gateway] --> ORCH[Commerce Orchestrator]
    ORCH --> POLICY[Policy<br/>limits]
    POLICY --> RISK[Risk<br/>score]
    RISK --> AUTHZ[Authorization]
    AUTHZ --> HITL[Human<br/>Approval]
    AUTHZ --> PAY[Payment Engine]
    HITL --> PAY
    ORCH --> AUDIT[Audit Ledger<br/>+ Transaction Passport]
  end
  subgraph S3["Where money actually moves"]
    RAZ[Razorpay]
  end
  AB --> GW
  PAY --> RAZ
  RAZ -. "webhook reply" .-> ORCH
""",
"d2_invariant": r"""
flowchart TD
  A[AI proposes an action] --> B[Compiled into a structured intent]
  B --> C[Policy check]
  C --> D[Risk check]
  D --> E[Authorization]
  E --> F{Needs a person?}
  F -- Yes --> G[Human approves]
  G --> H[Payment Engine]
  F -- No --> H
  H --> I[Razorpay]
  I --> J[Verified webhook / reconciliation]
  J --> K[Transaction Passport + Audit]
""",
"d3_purchase_workflow": r"""
sequenceDiagram
  participant User
  participant Agent
  participant AegisPay
  participant Razorpay
  User->>Agent: "Find running shoes under Rs 4000"
  Agent->>AegisPay: Compile intent + build cart
  AegisPay->>AegisPay: Check policy + risk
  AegisPay-->>Agent: Route depends on risk
  alt Low risk (within limits)
    AegisPay->>AegisPay: Auto authorise
  else High risk / big amount
    AegisPay->>AegisPay: Ask human to approve
  end
  AegisPay->>Razorpay: Create order + payment
  Razorpay-->>AegisPay: Payment result (or timeout)
  AegisPay->>AegisPay: Record passport + audit
  AegisPay-->>User: Confirmation
""",
"d4_safety_layers": r"""
flowchart TD
  Q{Request} --> P1{Within limits?}
  P1 -- No --> BLOCKED[BLOCKED - never money moved]
  P1 -- Yes --> P2{Allowed category?}
  P2 -- No --> BLOCKED
  P2 -- Yes --> R{Risk level}
  R -- LOW --> ALLOW[AUTO APPROV]
  R -- MEDIUM --> STEPUP[Ask user to confirm]
  R -- HIGH --> HUMAN[Send to a human]
  R -- CRITICAL --> BLOCKED
""",
"d5_failure_recovery": r"""
flowchart LR
  A[Payment sent] --> B{"Razorpay replies?"}
  B -- Yes + paid --> DONE[Success - done]
  B -- Yes + failed --> FAILED[Failed - safe stop]
  B -- No reply / timeout --> UNK[UNKNOWN]
  UNK --> R1[Wait, do NOT retry]
  R1 --> R2[Reconciliation checks provider]
  R2 --> C{Found?}
  C -- Yes paid --> DONE
  C -- Yes failed --> FAILED
  C -- Still unknown --> ESC[Escalate to a human]
""",
"d5b_duplicate_guard": r"""
flowchart LR
  X[Same request twice] --> Y["Idempotency key = 1 chance"]
  Y --> Z["(Request id, order id) stored"]
  Z --> W{Second copy?}
  W -- Yes --> N[Return same result - <br/>no second charge]
  W -- No --> P[Process once]
""",
"d6_multitenant": r"""
flowchart LR
  A[Merchant A app] --> DB[(Shared PostgreSQL)]
  B[Merchant B app] --> DB
  DB --> RL[Row Level Security]
  RL --> PA[A only reads its rows]
  RL --> PB[B only reads its rows]
""",
"d7_aws": r"""
flowchart TB
  Users --> CF[CloudFront + WAF]
  CF --> LB[Load Balancer]
  LB --> API[FastAPI Control Plane on ECS]
  API --> PG[(PostgreSQL RDS)]
  API --> RD[(Redis)]
  API --> Q[(Queue / SQS)]
  LB --> AI[FastAPI AI Runtime]
  AI --> LLM[LLM]
  Q --> WK[Workers]
  WK --> PG
  WK --> RAZ[Razorpay]
  API --> SM[(Secrets Manager)]
""",
"d8_audit_chain": r"""
flowchart LR
  E1[Event 1] --> E2[Event 2]
  E2 --> E3[Event 3]
  E3 --> AN[Anchor in S3]
  E1 -.hash.-> E2
  E2 -.hash.-> E3
  AN --> V[Verifier checks chain]
""",
}

# ---------- Render each diagram to PNG with mmdc ----------
MMDC_CLI = r"C:\Users\hp\AppData\Roaming\npm\node_modules\@mermaid-js\mermaid-cli\src\cli.js"

def render(text, name):
    mmd = BUILD / (name + ".mmd")
    png = BUILD / (name + ".png")
    mmd.write_text(text.strip(), encoding="utf-8")
    if png.exists():
        png.unlink()
    cmd = ["node", MMDC_CLI, "-q", "-i", str(mmd), "-o", str(png), "-t", "neutral"]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except FileNotFoundError:
        subprocess.run(["mmdc", "-q", "-i", str(mmd), "-o", str(png), "-t", "neutral"],
                       check=True, capture_output=True)
    if not png.exists():
        raise RuntimeError(f"mmdc failed for {name}")
    return png

for name, src in DIAGRAMS.items():
    render(src, name)
print("Rendered", len(DIAGRAMS), "diagrams")

# ---------- Build the PDF ----------
from reportlab.lib.pagesizes import A4, landscape, portrait
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph,
                                Spacer, Image, Table, TableStyle, PageBreak, KeepTogether,
                                ListFlowable, ListItem)

PAGE = A4
LEFT_RIGHT = 18*mm
TOP_BOTTOM = 16*mm

styles = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=styles["Heading1"], fontName="Helvetica-Bold",
                    fontSize=17, textColor=colors.HexColor("#0B3D6B"), spaceAfter=8, spaceBefore=6)
H2 = ParagraphStyle("H2", parent=styles["Heading2"], fontName="Helvetica-Bold",
                    fontSize=13.5, textColor=colors.HexColor("#12377B"), spaceAfter=6, spaceBefore=12)
H3 = ParagraphStyle("H3", parent=styles["Heading3"], fontName="Helvetica-Bold",
                    fontSize=11.5, textColor=colors.HexColor("#20406B"), spaceAfter=4, spaceBefore=8)
BODY = ParagraphStyle("Body", parent=styles["BodyText"], fontName="Helvetica",
                      fontSize=10.3, leading=15, spaceAfter=6, textColor=colors.HexColor("#1A1A1A"))
LI = ParagraphStyle("LI", parent=BODY, leftIndent=14, bulletIndent=2, spaceAfter=3)
CAPTION = ParagraphStyle("Caption", parent=BODY, fontSize=9, leading=12,
                         textColor=colors.HexColor("#555555"), alignment=TA_CENTER,
                         spaceBefore=2, spaceAfter=10)
CALLOUT = ParagraphStyle("Callout", parent=BODY, fontName="Helvetica-Bold",
                         fontSize=10.5, leading=15, textColor=colors.HexColor("#0B3D6B"),
                         backColor=colors.HexColor("#EDF3FA"), borderPadding=6,
                         borderWidth=0.5, borderColor=colors.HexColor("#B7CCE4"), spaceAfter=8)
BOX = ParagraphStyle("BOX", parent=BODY, fontSize=9.6, leading=13,
                     backColor=colors.HexColor("#F5F7FA"), borderPadding=6)
TITLE = ParagraphStyle("Title", parent=styles["Title"], fontName="Helvetica-Bold",
                       fontSize=24, textColor=colors.HexColor("#0B3D6B"), alignment=TA_CENTER,
                       leading=30, spaceAfter=6)
SUB = ParagraphStyle("Sub", parent=BODY, fontSize=12.5, textColor=colors.HexColor("#20406B"),
                     alignment=TA_CENTER, spaceAfter=2)

def image_flow(path, max_w=170*mm):
    from PIL import Image as PILImage
    iw, ih = PILImage.open(path).size
    ratio = ih / float(iw)
    w = min(max_w, iw/4.0)
    h = w * ratio
    return Image(str(path), width=w, height=h)

def bullet(items):
    return ListFlowable(
        [ListItem(Paragraph(t, LI), leftIndent=12, value="striped") for t in items],
        bulletType="bullet", start="&#8226;", leftIndent=12,
        bulletFontSize=8, spaceBefore=2, spaceAfter=6)

def numbered(items):
    return ListFlowable(
        [ListItem(Paragraph(t, LI), leftIndent=16) for t in items],
        bulletType="1", start=1, leftIndent=16, spaceAfter=6)

def table(rows, widths, header=True):
    data = [[Paragraph(c, ParagraphStyle("th", parent=BODY, fontName="Helvetica-Bold",
                fontSize=9, textColor=colors.white, leading=12)) for c in rows[0]]] if header else []
    for r in rows[1:]:
        data.append([Paragraph(c, ParagraphStyle("td", parent=BODY, fontSize=9, leading=12)) for c in r])
    t = Table(data, colWidths=widths, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#0B3D6B") if header else colors.white),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#F5F7FA")]),
        ("GRID", (0,0), (-1,-1), 0.4, colors.HexColor("#C7D2DE")),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 5), ("RIGHTPADDING", (0,0), (-1,-1), 5),
        ("TOPPADDING", (0,0), (-1,-1), 3), ("BOTTOMPADDING", (0,0), (-1,-1), 3),
    ]))
    return t

def diag(name, caption):
    return KeepTogether([Spacer(1, 4), image_flow(BUILD / (name+".png"), max_w=175*mm),
                         Paragraph(caption, CAPTION)])

# ---------- Page setup ----------
def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#888888"))
    canvas.drawString(LEFT_RIGHT, 9*mm, "AegisPay — The Trust & Growth Layer for Agentic Commerce")
    canvas.drawRightString(A4[0]-LEFT_RIGHT, 9*mm, f"Page {doc.page}")
    canvas.setStrokeColor(colors.HexColor("#D6DEE8"))
    canvas.setLineWidth(0.5)
    canvas.line(LEFT_RIGHT, 13*mm, A4[0]-LEFT_RIGHT, 13*mm)
    canvas.restoreState()

frame = Frame(LEFT_RIGHT, TOP_BOTTOM, A4[0]-2*LEFT_RIGHT, A4[1]-2*TOP_BOTTOM,
              id="normal", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)

doc = BaseDocTemplate(str(OUT_PDF), pagesize=A4,
                      leftMargin=LEFT_RIGHT, rightMargin=LEFT_RIGHT,
                      topMargin=TOP_BOTTOM, bottomMargin=TOP_BOTTOM,
                      title="AegisPay Architecture", author="AegisPay Engineering")
doc.addPageTemplates([PageTemplate(id="all", frames=[frame], onPage=on_page)])

S = []
PARA = lambda t, st=BODY: Paragraph(t, st)

S += [Spacer(1, 24), PARA("AEGISPAY", TITLE), PARA("The Trust &amp; Growth Layer for Agentic Commerce", SUB),
      Spacer(1, 8),
      PARA("A production-ready architecture for letting AI agents grow and sell — <b>without ever giving the AI control of money</b>.", BODY),
      Spacer(1, 16)]

# Title box with the core rule
S.append(table([
    ["The one rule that makes AegisPay safe"],
    ["<b>AI may propose a financial action. Only the deterministic AegisPay control plane may authorize and execute it.</b> No AI can move money on its own."],
], [175*mm], header=False))
S.append(Spacer(1, 14))

# Section 1
S += [PARA("1. What is AegisPay?", H2),
      PARA("AegisPay sits between AI agents (like a shopping assistant) and payment providers (like Razorpay). It has three jobs, written simply:", BODY),
      table([["Job", "Plain-English meaning"],
             ["GROW", "Use AI to help a merchant sell more (suggest cross-sells, upsells, bundles, campaigns)."],
             ["SELL", "Let an AI buyer find a product, build a cart, and pay end-to-end."],
             ["PROTECT", "Make every AI-driven money step explainable, limited, approved, recorded, and safe to recover from failures."]],
            [40*mm, 135*mm]),
      Spacer(1, 8),
      PARA("The reason AegisPay is trusted is that <b>PROTECT is baked into the architecture</b> — GROW and SELL work because money can never be moved by the AI alone.", BODY)]

S.append(PageBreak())

# Section 2
S += [PARA("2. The architecture at a glance", H2),
      PARA("This is the whole system. Read it from left to right: a user asks an AI buyer, the agent talks to AegisPay, AegisPay checks everything, and only then does it ask Razorpay to move money. Razorpay replies through verified webhooks, and AegisPay records every step.", BODY),
      diag("d1_architecture", "Figure 1 — AegisPay high-level architecture"),
      PARA("Why this is hard to reject:", H3),
      bullet([
        "<b>No secret</b> is given to the AI — no payment keys, no database passwords.",
        "<b>No payment code</b> is reachable by the AI. The AI only <i>requests</i>; AegisPay decides.",
        "<b>Every action is logged</b> in a tamper-proof audit ledger and a Transaction Passport.",
        "<b>Failures are safe</b> — if Razorpay is slow, AegisPay waits and checks, it never guesses and never double-charges.",
      ])]

# Section 3
S += [PARA("3. The one rule, every time", H2),
      PARA("Every financial action follows this exact path. There is no shortcut, and no AI can skip a step.", BODY),
      diag("d2_invariant", "Figure 2 — The decision path every money action must pass"),
      PARA("The important bit: the AI produces the <i>idea</i> (an intent). AegisPay converts that idea into a checked, structured request and decides yes/no using rules, not guesses.", BODY)]

# Section 4
S += [PARA("4. Step-by-step: a real purchase", H2),
      PARA("Here is the exact journey for a person asking an AI to buy running shoes under Rs 4,000.", BODY),
      numbered([
        "The user tells the AI buyer: \u201cFind running shoes under Rs 4,000.\u201d",
        "The AI searches the merchant's catalog and recommends shoes.",
        "The AI builds a <b>cart</b>. AegisPay writes the prices itself — the AI cannot set a price.",
        "AegisPay turns the AI's plan into a structured <b>intent</b>.",
        "AegisPay checks <b>policy</b>: is this amount allowed, is this category allowed, is it within today's limit?",
        "AegisPay checks <b>risk</b>: is this a normal purchase or risky?",
        "AegisPay <b>authorizes</b>: if low risk it approves; if high risk it asks a human first.",
        "Only then does AegisPay ask <b>Razorpay</b> to create the order and take payment.",
        "Razorpay confirms through a <b>signed webhook</b> (and reconciliation if needed).",
        "AegisPay writes the <b>Transaction Passport</b> and the <b>audit record</b>.",
        "The user gets a confirmation with the full evidence.",
      ]),
      diag("d3_purchase_workflow", "Figure 3 — Automated purchase workflow (including the human-approval branch)")]

S.append(PageBreak())

# Section 5
S += [PARA("5. The safety layers", H2),
      PARA("AegisPay does not give the AI freedom. It gives the AI freedom <i>inside limits</i>, and it escalates when it should.", BODY),
      diag("d4_safety_layers", "Figure 4 — Decision layers: limits, then risk, then people"),
      table([["Outcome", "What it means"],
             ["AUTO APPROVE", "Low-risk, within all limits. No human needed."],
             ["ASK USER (step-up)", "Medium risk. The user must confirm that one action."],
             ["SEND TO A HUMAN", "High risk. A person reviews the whys and decides."],
             ["BLOCK", "Outside limits or critical risk. Money never moves; the attempt is recorded."]],
            [48*mm, 127*mm])]

# Section 6 — failures
S += [PARA("6. What happens when things go wrong", H2),
      PARA("Payment systems are judged by how they fail. AegisPay fails safely.", BODY),
      PARA("Scenario — Razorpay is slow and does not answer in time:", H3),
      diag("d5_failure_recovery", "Figure 5 — Unknown payment is resolved by checking, never by guessing"),
      PARA("The key: <b>AegisPay never blindly retries.</b> If the first attempt actually worked, retrying would double-charge the customer. So AegisPay marks the payment UNKNOWN, then quietly asks Razorpay what really happened, and finishes the job safely.", BODY),
      PARA("Scenario — the same request is sent twice by accident:", H3),
      diag("d5b_duplicate_guard", "Figure 6 — Duplicate request guard (idempotency)"),
      PARA("Every money request gets a unique key. A repeated request returns the same stored answer and is never charged twice.", BODY)]

# Section 7 — multitenant
S += [PARA("7. Many merchants, no leaks", H2),
      diag("d6_multitenant", "Figure 7 — Tenant isolation"),
      PARA("Thousands of merchants share one database, but each can only see its own rows. AegisPay gives every table a <b>tenant id</b> and enforces it at the database level using <b>Row-Level Security</b>, plus checks in the code. Merchant A can never read Merchant B's data.", BODY)]

S.append(PageBreak())

# Section 8 — audit/passport
S += [PARA("8. Proof you can actually use", H2),
      PARA("Every decision leaves a tamper-proof trail. Events are linked like a chain, so if anyone changes an old record, the chain breaks and the system flags it.", BODY),
      diag("d8_audit_chain", "Figure 8 — The audit chain"),
      PARA("<b>Transaction Passport.</b> For any transaction you get one clean, human-readable page showing: what was bought, who wanted it, which agent, which policy version, the risk, the approval, the Razorpay order id, and a verified integrity stamp. That is answer to \u201cwhy did this happen?\u201d", BODY),
      table([["Passport field", "Purpose"],
             ["Intent / cart hashes", "Proves the approved cart is exactly what was paid for."],
             ["Policy version", "Tells you exactly which rules were applied."],
             ["Risk score", "Shows how risky this was and why."],
             ["Authorization hash", "Proves an authorized person/agent backed it."],
             ["Human approval", "Shows whether a person approved it."],
             ["Provider order id", "Links to the real Razorpay record."],
             ["Audit integrity", "Verifies nothing was altered afterwards."]],
            [55*mm, 120*mm])]

# Section 9 — infrastructure / stack
S += [PARA("9. The technology (kept simple and reliable)", H2),
      PARA("AegisPay is <b>all Python/FastAPI</b> — one language, one toolchain, easy for any team to read and run. The AI part is a <i>separate</i> FastAPI service that is not allowed to touch money. AegisPay uses boring, dependable technology because money needs boring.", BODY),
      diag("d7_aws", "Figure 9 — AWS deployment"),
      table([["Layer", "Choice", "Why"],
             ["Core", "Python / FastAPI", "One language, fast to build, real-time async, strong typed validation. Safe for money logic."],
             ["AI runtime", "Python / FastAPI (separate)", "Same language, but a separate service that never touches money — keeps the AI safe."],
             ["Database", "PostgreSQL", "Correct, auditable, per-tenant security, easy backup."],
             ["Cache / locks", "Redis", "Fast caching and rate limits; never the source of truth."],
             ["Queue", "SQS", "Reliable background work (webhooks, reconciliation, reports)."],
             ["Cloud", "AWS ECS (not Kubernetes)", "Simple, reliable, less to go wrong at this scale."],
             ["Frontend", "Next.js + TypeScript", "Merchant dashboard, approval inbox, catalogs, analytics."]],
            [32*mm, 40*mm, 103*mm])]

# Section 10 — why this is good architecture
S += [PARA("10. Why this is a good architecture", H2),
      PARA("Anyone can draw a clever diagram. What makes this one good is that <b>safety is built in</b>, not bolted on. Here is what that means:", BODY),
      table([["Quality", "How this architecture provides it"],
             ["Safe by default", "The AI can never move money. It has no payment keys and no payment tool — only a request the system always checks."],
             ["No double charges", "Idempotency keys + never-retry-unknown + reconciliation make duplicate payments impossible."],
             ["No way around the rules", "Every money action must pass policy, risk and authorization. There is no code path that skips them."],
             ["A person is always in charge", "High-risk actions go to a human; limits are set by the merchant, not by the AI."],
             ["You can prove things", "The audit chain and Transaction Passport answer who, what, when and why with evidence."],
             ["Grows safely", "Autonomy is dialed up gradually, and every higher level gets more scrutiny — never less."],
             ["Ready for the future", "MCP, A2A and new protocols plug in as adapters without touching the safe money core."],
             ["Simple to run", "One main service, one database, one queue. Fewer moving parts means fewer things to break."]],
            [42*mm, 133*mm]),
      PARA("In one line: <b>AegisPay lets AI grow and sell — and is the amount of trust you would actually hand to an AI.</b>", CALLOUT)]

doc.build(S)
print("PDF written to", OUT_PDF, "| size:", OUT_PDF.stat().st_size, "bytes")
