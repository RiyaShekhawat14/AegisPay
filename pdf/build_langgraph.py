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
BUILD = ROOT / "pdf" / "_build_lg"
BUILD.mkdir(parents=True, exist_ok=True)
MMDC_CLI = r"C:\Users\hp\AppData\Roaming\npm\node_modules\@mermaid-js\mermaid-cli\src\cli.js"

# ---------------- Mermaid diagrams ----------------
SELL_DIAGRAMS = {
"sell_overview": r"""
flowchart TD
  subgraph AGG["The Agent Graph (LangGraph) — thinks and proposes"]
    direction TB
    S["User asks<br/>to buy something"] --> A[1. Understand<br/>the request]
    A --> B[2. Search the<br/>merchant catalog]
    B --> C[3. Rank and<br/>recommend]
    C --> D{Need more<br/>info?}
    D -- Yes --> ASK[Ask the user<br/>a clear question] --> A
    D -- No --> E[4. Build a cart<br/>with real prices]
    E --> F[5. Check the<br/>structured intent]
    F --> G[6. Ask AegisPay<br/>to authorize]
    G --> H{Policy and<br/>risk say?}
    H -- ALLOW --> OUT[7. Return a ready<br/>business intent]
    H -- NEED A HUMAN --> HU[8. A person approves
        in the dashboard] --> OUT
    H -- DENIED --> DEN[Blocked<br/>with a reason]
  end
  subgraph CP["The AegisPay Control Plane (outside the graph)"]
    PO[Policy + Risk]
    PAY[Payment Engine]
    AU[Audit + Passport]
  end
  OUT --> PO
  PO --> PAY
  PAY --> AU
""",
"sell_state": r"""
stateDiagram-v2
  [*] --> Interpret
  Interpret --> Search
  Search --> Rank
  Rank --> Clarify: ambiguous
  Rank --> BuildCart
  Clarify --> Interpret
  BuildCart --> Validate
  Validate --> Authorize
  Authorize --> EmitIntent: ALLOW
  Authorize --> HumanApprove: APPROVAL_REQUIRED
  Authorize --> Blocked: DENIED
  HumanApprove --> EmitIntent: approved and resumed
  EmitIntent --> [*]
  Blocked --> [*]
""",
"sell_boundary": r"""
flowchart LR
  subgraph AI["The AI side - only thinks"]
    AG[Reasoning,<br/>recommendation,<br/>cart, intent]
  end
  subgraph CP["The deterministic side - only acts"]
    PLC[Policy<br/>Risk<br/>Authorization]
    PAY[Payment execution]
    AUD[Audit + Passport]
  end
  AG -- "structured intent only" --> PLC
  PLC -- "authorized" --> PAY
  PAY --> AUD
""",
}

GROW_DIAGRAMS = {
"grow_overview": r"""
flowchart TD
  data["Merchant purchase data<br/>(aggregate; no customer PII)"] --> A[1. Load and clean<br/>the data]
  A --> B[2. Find opportunities<br/>by real correlation]
  B -->   C["3. Draft a campaign<br/>(offer, discount, budget)"]
  C --> D[4. Check the campaign<br/>against fixed rules]
  D --> E{Passes the rules?}
  E -- Yes --> F[5. Estimate uplift<br/>with an honest label]
  F --> G[6. Ask the merchant<br/>to approve]
  G --> H{Merchant says?}
  H -- Approves --> I[7. Run the campaign<br/>within its budget]
  H -- Rejects --> J[Discard + explain]
  I --> K[8. Measure the result]
  K --> M[Learn and repeat]
  E -- No --> FIX[Explain what to fix<br/>or limit the offer] --> C
  J --> M
""",
"grow_guardrails": r"""
flowchart TD
  P[draft campaign] --> R1{Discount too<br/>big?}
  R1 -- Yes --> X[Reject / cap]
  R1 -- No --> R2{Budget too<br/>high?}
  R2 -- Yes --> X
  R2 -- No --> R3{Margin too<br/>low?}
  R3 -- Yes --> X
  R3 -- No --> R4{Too many<br/>emails?}
  R4 -- Yes --> X
  R4 -- No --> OK[Human approves<br/>then it runs]
""",
}

# ---------------- Rendering ----------------
def render(text, name):
    mmd = BUILD / (name + ".mmd")
    png = BUILD / (name + ".png")
    mmd.write_text(text.strip(), encoding="utf-8")
    if png.exists():
        png.unlink()
    try:
        subprocess.run(["node", MMDC_CLI, "-q", "-i", str(mmd), "-o", str(png), "-t", "neutral"],
                       check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"{name} render failed: {e.stderr.decode()[:500]}")
    if not png.exists():
        raise RuntimeError(f"mmdc failed for {name}")
    return png

for name, src in {**SELL_DIAGRAMS, **GROW_DIAGRAMS}.items():
    render(src, name)
print("Rendered", len(SELL_DIAGRAMS) + len(GROW_DIAGRAMS), "LangGraph diagrams")

# ---------------- PDF helpers ----------------
LEFT_RIGHT = 17*mm
TOP_BOTTOM = 15*mm
styles = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=16.5,
                    textColor=colors.HexColor("#0B3D6B"), spaceAfter=8, spaceBefore=4)
H2 = ParagraphStyle("H2", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=13,
                    textColor=colors.HexColor("#12377B"), spaceAfter=6, spaceBefore=11)
H3 = ParagraphStyle("H3", parent=styles["Heading3"], fontName="Helvetica-Bold", fontSize=11,
                    textColor=colors.HexColor("#20406B"), spaceAfter=4, spaceBefore=8)
BODY = ParagraphStyle("Body", parent=styles["BodyText"], fontName="Helvetica", fontSize=10,
                      leading=14.5, spaceAfter=6, textColor=colors.HexColor("#191919"))
LI = ParagraphStyle("LI", parent=BODY, leftIndent=14, spaceAfter=3)
CAPTION = ParagraphStyle("Caption", parent=BODY, fontSize=8.8, leading=12,
                         textColor=colors.HexColor("#666666"), alignment=TA_CENTER,
                         spaceBefore=2, spaceAfter=10)
CALLOUT = ParagraphStyle("Callout", parent=BODY, fontName="Helvetica-Bold", fontSize=10.3,
                         leading=15, textColor=colors.HexColor("#0B3D6B"),
                         backColor=colors.HexColor("#EDF3FA"), borderPadding=6,
                         borderWidth=0.5, borderColor=colors.HexColor("#B7CCE4"), spaceAfter=8)
TITLE = ParagraphStyle("Title", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=23,
                       textColor=colors.HexColor("#0B3D6B"), alignment=TA_CENTER, leading=29,
                       spaceAfter=6)
SUB = ParagraphStyle("Sub", parent=BODY, fontSize=12, textColor=colors.HexColor("#20406B"),
                     alignment=TA_CENTER, spaceAfter=2)

def image_flow(path, max_w=172*mm):
    from PIL import Image as PILImage
    iw, ih = PILImage.open(path).size
    ratio = ih / float(iw)
    w = min(max_w, iw/4.0)
    return Image(str(path), width=w, height=w*ratio)

def PARA(t, st=BODY):
    return Paragraph(t, st)

def bullets(items):
    return ListFlowable([ListItem(Paragraph(t, LI), leftIndent=12) for t in items],
                        bulletType="bullet", start="&#8226;", leftIndent=12,
                        bulletFontSize=8, spaceAfter=6)

def numbered(items):
    return ListFlowable([ListItem(Paragraph(t, LI), leftIndent=16) for t in items],
                        bulletType="1", start=1, leftIndent=16, spaceAfter=6)

def table(rows, widths, header=True):
    th = ParagraphStyle("th", parent=BODY, fontName="Helvetica-Bold", fontSize=8.8,
                        textColor=colors.white, leading=12)
    td = ParagraphStyle("td", parent=BODY, fontSize=8.8, leading=12)
    data = [[Paragraph(c, th) for c in rows[0]]] if header else []
    for r in rows[1:]:
        data.append([Paragraph(c, td) for c in r])
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
    return KeepTogether([Spacer(1, 3), image_flow(BUILD / (name + ".png")),
                         Paragraph(caption, CAPTION)])

def build(pdf_name, sections):
    def on_page(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8); canvas.setFillColor(colors.HexColor("#888888"))
        canvas.drawString(LEFT_RIGHT, 9*mm, "AegisPay — LangGraph Architecture")
        canvas.drawRightString(A4[0]-LEFT_RIGHT, 9*mm, f"Page {doc.page}")
        canvas.setStrokeColor(colors.HexColor("#D6DEE8")); canvas.setLineWidth(0.5)
        canvas.line(LEFT_RIGHT, 13*mm, A4[0]-LEFT_RIGHT, 13*mm)
        canvas.restoreState()
    frame = Frame(LEFT_RIGHT, TOP_BOTTOM, A4[0]-2*LEFT_RIGHT, A4[1]-2*TOP_BOTTOM, id="n",
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    out = ROOT / pdf_name
    doc = BaseDocTemplate(str(out), pagesize=A4, leftMargin=LEFT_RIGHT, rightMargin=LEFT_RIGHT,
                          topMargin=TOP_BOTTOM, bottomMargin=TOP_BOTTOM,
                          title="AegisPay LangGraph Architecture", author="AegisPay Engineering")
    doc.addPageTemplates([PageTemplate(id="all", frames=[frame], onPage=on_page)])
    doc.build(sections)
    return out

# ==================== SELL PDF ====================
SL = []
SL += [Spacer(1, 24), PARA("AEGISPAY", TITLE),
       PARA("LangGraph Architecture — SELL (AI Buyer Checkout)", SUB), Spacer(1, 8),
       PARA("How an AI buys a product for a real customer, step by step — <b>without the AI ever touching the money</b>.", BODY),
       Spacer(1, 10)]

SL += [PARA("1. What this graph does (in plain English)", H2),
       PARA("A user says something like: <i>\u201cFind running shoes under Rs 4,000.\u201d</i> The SELL agent graph turns that sentence into a <b>ready-to-pay business intent</b>. It understands, searches, recommends, builds a cart, and asks for permission. It never swipes a card.", BODY),
       PARA("The most important idea", H3),
       PARA("LangGraph is only the <b>brain</b>. The <b>money</b> lives in a separate AegisPay control plane that the graph cannot reach. The graph hands over a validated intent; only the control plane can say yes and move money.", CALLOUT),
       diag("sell_overview", "Figure 1 — The SELL agent graph (top) and the money control plane (bottom) it cannot reach")]

SL += [PageBreak(), PARA("2. What happens at each step", H2),
       table([["#", "Node", "What it does", "Minder (the safety rail)"],
              ["1", "Understand", "Reads the request as a typed intent (product, budget, limits).", "Pydantic schema; budget is read to the diagram, not trusted later."],
              ["2", "Search catalog", "Finds matching products from the merchant catalog.", "Only typed catalog data; never raw product text as instructions."],
              ["3", "Rank & recommend", "Chooses the best few with a short reason.", "Prices and stock come from the server, not from the AI."],
              ["4", "Clarify", "Asks the user a clear question if anything is unclear.", "Limited to asking a question; cannot change a price."],
              ["5", "Build cart", "Adds chosen items with server prices; computes a cart hash.", "Cart is locked and hashed, so it cannot be silently changed later."],
              ["6", "Validate intent", "Checks the whole plan is structured and complete.", "Any malformed or suspicious intent is rejected, not guessed."],
              ["7", "Authorize", "Calls AegisPay to check policy + risk.", "AegisPay decides; the AI cannot decide."],
              ["8", "Human / finish", "Low risk = done; high risk = a person approves, then it resumes.", "Approval is scoped, expiring, and can't be reused."]],
             [6*mm, 32*mm, 66*mm, 68*mm])]

SL += [PARA("3. The state machine (how it pauses for a person)", H2),
       PARA("A purchase is not a one-shot answer. When AegisPay says <b>human approval</b> is needed, LangGraph <b>pauses</b> in the middle, the person approves in the dashboard, and the same graph <b>resumes</b> where it stopped. Nothing is lost or redone.", BODY),
       diag("sell_state", "Figure 2 — The graph's internal states, including the human-approval pause")]

SL += [PageBreak(), PARA("4. The safety boundary (the thing that makes it trustworthy)", H2),
       diag("sell_boundary", "Figure 3 — The AI thinks; the control plane acts. Only a structured intent crosses the line."),
       table([["Only the AI side may...", "Only the control plane may..."],
              ["Understand a request", "Run policy and risk checks"],
              ["Search and recommend", "Decide ALLOW / APPROVAL / DENY"],
              ["Build and lock a cart", "Authorize the payment"],
              ["Ask for a permission", "Move money through Razorpay"],
              ["Produce a structured intent", "Write the Passport and audit trail"]],
             [86*mm, 86*mm])]

SL += [PARA("5. Built to run in production", H2),
       bullets([
        "<b>Resumes safely.</b> Every step is saved (checkpointed) so a pause, crash, or approval can continue exactly where it left off.",
        "<b>No double work.</b> An idempotency key means a retried step does not run twice and cannot create a second cart or intent.",
        "<b>It can't invent prices.</b> Prices, stock and totals are always the server's answer, so the AI cannot change the amount.",
        "<b>It can't skip limits.</b> Every intent passes policy + risk in the control plane, no matter what the AI says.",
        "<b>You can watch it.</b> The graph logs its trace, and every decision is written to the audit ledger and shown as a Transaction Passport.",
        "<b>It fails safely.</b> If the AI is slow, wrong, or unavailable, the control plane simply keeps the money safe and waits.",
        "<b>It's tested.</b> Unit tests for every node, plus a red-team that tries to cheat the graph (prompt injection, price tampering, fake approval) and must fail.",
      ])]

SL += [PARA("6. What you get", H2),
       PARA("A user can buy through an AI safely and confidently. The merchant sells more (SELL). The customer and the merchant have full proof of every decision. And the AI was never in charge of money.", CALLOUT)]

output_sell = build("AegisPay-LangGraph-SELL.pdf", SL)

# ==================== GROW PDF ====================
GL = []
GL += [Spacer(1, 24), PARA("AEGISPAY", TITLE),
       PARA("LangGraph Architecture — GROW (Merchant Revenue Agent)", SUB), Spacer(1, 8),
       PARA("How an AI looks at a merchant's sales and safely invents offers that make money — <b>without giving itself an unlimited budget</b>.", BODY),
       Spacer(1, 10)]

GL += [PARA("1. What this graph does (in plain English)", H2),
       PARA("A merchant sells shoes. The GROW agent reads the sales history, notices \u201ccustomers who buy running shoes often buy running socks\u201d, and proposes a small cross-sell offer. But it cannot switch the offer on by itself — a merchant approves it, and it runs only inside a fixed budget.", BODY),
       PARA("The most important idea", H3),
       PARA("The AI is the <b>idea person</b>. It proposes. A merchant decides. And iron rules (max discount, max budget, minimum margin) are always enforced — no matter how confident the AI sounds.", CALLOUT),
       diag("grow_overview", "Figure 1 — The GROW agent graph: from merchant data, through rules and approval, to a measured campaign")]

GL += [PageBreak(), PARA("2. What happens at each step", H2),
       table([["#", "Node", "What it does", "Minder (the safety rail)"],
              ["1", "Load data", "Pulls grouped sales history. No personal customer data needed.", "Uses aggregate numbers only (affinity of product pairs, not who bought)."],
              ["2", "Find opportunities", "Finds real correlations (shoe + socks, bottle + shirt).", "Uses math (affinity, confidence), not a guess."],
              ["3", "Draft campaign", "Writes the offer: a discount, a budget, a target audience.", "It only proposes. It cannot switch it on."],
              ["4", "Check rules", "Tests the offer against fixed limits.", "Max discount, max budget, minimum margin, duration, email frequency."],
              ["5", "Estimate impact", "Predicts a possible lift, clearly labelled as an estimate.", "It never claims a fake number; the estimate is a range, not a promise."],
              ["6", "Approve", "The merchant sees the why and says yes or no.", "A merchant (or a policy) decides; the AI cannot approve itself."],
              ["7", "Run campaign", "Turns the offer on inside its budget.", "The moment the budget is spent, it stops by itself."],
              ["8", "Measure", "Counts what actually happened.", "If the offer did not help, it learns and does not repeat blindly."]],
             [6*mm, 32*mm, 66*mm, 68*mm])]

GL += [PARA("3. The rules that stop bad AI ideas", H2),
       diag("grow_guardrails", "Figure 2 — Every proposed offer is filtered by fixed limits before a human ever sees it"),
       table([["Risk", "The rule that stops it"],
              ["Discount too big", "A hard maximum discount percent."],
              ["Budget too high", "A hard maximum campaign budget; it auto-stops when spent."],
              ["Eating into profit", "A minimum margin floor - the offer must still make money."],
              ["Spamming customers", "A limit on how many times one customer is contacted."],
              ["Unfair targeting", "Only value/behaviour segments are allowed; never protected personal traits."]],
             [52*mm, 120*mm])]

GL += [PageBreak(), PARA("4. Built to run in production", H2),
       bullets([
        "<b>Propose, never force.</b> The graph always ends at a proposal that needs a merchant's yes.",
        "<b>Hard caps, always.</b> Discount, budget, margin, duration and frequency are deterministic rules the AI cannot change.",
        "<b>Stops when it should.</b> If the budget is used up, the campaign pauses by itself. No overspend.",
        "<b>Honest numbers.</b> Revenue predictions are labelled as estimates with a range, never a fake confidence.",
        "<b>Audited end-to-end.</b> Every proposal, approval and action is written to the audit ledger.",
        "<b>Safe against abuse.</b> The red-team tries to make the AI invent a giant discount or a huge campaign, and the tests make sure it is blocked.",
        "<b>Improves, doesn't burn money.</b> It measures results and only repeats what actually worked.",
      ])]

GL += [PARA("5. What you get", H2),
       PARA("A merchant earns more without risking the business: the AI spots and proposes real opportunities, and the merchant stays in control of every rupee. The AI grows the store — it does not gamble with it.", CALLOUT)]

output_grow = build("AegisPay-LangGraph-GROW.pdf", GL)

print("SELL PDF:", output_sell, output_sell.stat().st_size, "bytes")
print("GROW PDF:", output_grow, output_grow.stat().st_size, "bytes")
