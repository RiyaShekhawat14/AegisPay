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
BUILD = ROOT / "pdf" / "_build_dbs"
BUILD.mkdir(parents=True, exist_ok=True)
MMDC = r"C:\Users\hp\AppData\Roaming\npm\node_modules\@mermaid-js\mermaid-cli\src\cli.js"

D = {
"er": r"""
erDiagram
  MERCHANTS ||--o{ AGENTS : owns
  MERCHANTS ||--o{ PRODUCTS : sells
  MERCHANTS ||--o{ POLICIES : sets
  AGENTS ||--o{ CARTS : builds
  CARTS ||--o{ CART_ITEMS : has
  CART_ITEMS }o--|| PRODUCTS : line
  CARTS ||--o{ ORDERS : becomes
  ORDERS ||--o{ ORDER_ITEMS : has
  ORDER_ITEMS }o--|| PRODUCTS : snapshot
  ORDERS ||--o{ PAYMENTS : paid by
  PAYMENTS ||--o{ REFUNDS : refunded
  ORDERS }o--o| AUTHORIZATIONS : authorized
  AUTHORIZATIONS ||--o{ APPROVALS : may need
  AGENTS ||--o{ CAMPAIGNS : grows
  MERCHANTS ||--o{ WEBHOOK_EVENTS : receives
  MERCHANTS ||--o{ AUDIT_EVENTS : audits
""",
"buy": r"""
flowchart LR
  PRODUCTS --> CARTS --> CART_ITEMS
  CARTS --> ORDERS --> ORDER_ITEMS
  ORDERS --> AUTHORIZATIONS --> APPROVALS
  ORDERS --> PAYMENTS
  PAYMENTS --> REFUNDS
  PAYMENTS -. webhook .-> WEBHOOK_EVENTS
  ORDERS --> AUDIT_EVENTS
""",
"grow": r"""
flowchart LR
  AGENTS --> CAMPAIGNS
  CAMPAIGNS --> ORDERS
  CAMPAIGNS --> AUDIT_EVENTS
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
st=getSampleStyleSheet()
H1=ParagraphStyle("H1",parent=st["Heading1"],fontName="Helvetica-Bold",fontSize=16.5,textColor=ACC,spaceAfter=6,spaceBefore=2)
H2=ParagraphStyle("H2",parent=st["Heading2"],fontName="Helvetica-Bold",fontSize=13,textColor=INK,spaceAfter=5,spaceBefore=12)
BODY=ParagraphStyle("Body",parent=st["BodyText"],fontName="Helvetica",fontSize=10.2,leading=14.6,spaceAfter=6,textColor=INK)
LI=ParagraphStyle("LI",parent=BODY,leftIndent=13,spaceAfter=4)
CAP=ParagraphStyle("Cap",parent=BODY,fontSize=8.6,leading=11,textColor=MUT,alignment=TA_CENTER,spaceBefore=2,spaceAfter=10)
CALL=ParagraphStyle("Call",parent=BODY,fontName="Helvetica-Bold",fontSize=10.2,leading=15,textColor=ACC,backColor=colors.HexColor("#FDF6F7"),borderPadding=7,borderWidth=0.6,borderColor=colors.HexColor("#E7BCCA"),spaceAfter=8)
TITLE=ParagraphStyle("Title",parent=st["Title"],fontName="Helvetica-Bold",fontSize=21,textColor=INK,alignment=TA_CENTER,leading=28,spaceAfter=5)
SUB=ParagraphStyle("Sub",parent=BODY,fontSize=11.5,textColor=ACC,alignment=TA_CENTER,spaceAfter=2)
TH=ParagraphStyle("th",parent=BODY,fontName="Helvetica-Bold",fontSize=9,textColor=INK,leading=12)
TD=ParagraphStyle("td",parent=BODY,fontName="Helvetica",fontSize=9,leading=12,textColor=INK)
CODE=ParagraphStyle("code",parent=BODY,fontName="Courier",fontSize=8.2,leading=10.4,textColor=INK,spaceBefore=4)
NOTE=ParagraphStyle("note",parent=BODY,fontSize=8.8,leading=12.3,textColor=MUT)

def para(t,s=BODY): return Paragraph(t,s)
def bullets(it): return ListFlowable([ListItem(Paragraph(t,LI),leftIndent=12) for t in it],bulletType="bullet",start="&#8226;",leftIndent=12,bulletFontSize=8,spaceAfter=5)
def table(rows,widths):
    data=[[Paragraph(c,TH) for c in rows[0]]]
    for r in rows[1:]: data.append([Paragraph(c,TD) for c in r])
    t=Table(data,colWidths=widths,hAlign="LEFT",repeatRows=1)
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),NEUT),("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#FAFAFB")]),
      ("GRID",(0,0),(-1,-1),0.4,BORD),("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),5),
      ("RIGHTPADDING",(0,0),(-1,-1),5),("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4)]))
    return t
def image_flow(path,max_w=178*mm):
    from PIL import Image as PILImage
    iw,ih=PILImage.open(path).size; r=ih/float(iw); w=min(max_w,iw/4.0); return Image(str(path),width=w,height=w*r)
def diag(name,cap): return KeepTogether([Spacer(1,3),image_flow(BUILD/(name+".png")),Paragraph(cap,CAP)])
def block(t): return Preformatted(t,CODE)

def onp(c,d):
    c.saveState(); c.setFont("Helvetica",7.8); c.setFillColor(MUT)
    c.drawString(LR,8*mm,"AegisPay · Database Schema (Simple)")
    c.drawRightString(A4[0]-LR,8*mm,f"Page {d.page}")
    c.setStrokeColor(BORD); c.setLineWidth(.5); c.line(LR,12*mm,A4[0]-LR,12*mm); c.restoreState()
frame=Frame(LR,TB,A4[0]-2*LR,A4[1]-2*TB,id="n",leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)
out=ROOT/"AegisPay-Database-Schema-Simple.pdf"
doc=BaseDocTemplate(str(out),pagesize=A4,leftMargin=LR,rightMargin=LR,topMargin=TB,bottomMargin=TB,title="AegisPay Database Schema (Simple)",author="AegisPay Engineering")
doc.addPageTemplates([PageTemplate(id="all",frames=[frame],onPage=onp)])

F=[Spacer(1,20), para("AEGISPAY",TITLE), para("Database Schema — Simple version",SUB),
   Spacer(1,8), para("One PostgreSQL database. Every merchant lives in the same place, and the database keeps them apart. Just 15 simple tables.",BODY), Spacer(1,10),
   para("In one line",H2),
   para("Merchants own everything. An AI agent builds a cart, an order is created, a payment happens, and every step is recorded for audit. GROW adds campaigns on top.",CALL)]

F+=[PageBreak(), para("The tables (15)",H2),
  para("Here is every table we need, in plain words.",BODY),
  table([["Table","What it stores","In plain words"],
   ["merchants","the merchant (one tenant)","the business"],
   ["agents","an AI agent + its limits and tools","who the AI is, what it may do"],
   ["products","catalog items with the real price","what is for sale"],
   ["carts","a basket; server price + hash + expiry","what's in the basket"],
   ["cart_items","each line in a basket","one item, one price"],
   ["orders","a locked purchase + policy version","the buy is confirmed"],
   ["order_items","frozen product snapshot per line","proof of the price at that moment"],
   ["payments","the Razorpay payment + status","did the money move"],
   ["refunds","a controlled refund","give money back safely"],
   ["policies","the merchant's rules (in JSON)","limits and caps"],
   ["authorizations","a permission to pay this exact cart","one-time, expires"],
   ["approvals","a human's yes/no on a risky one","a person decides"],
   ["webhook_events","Razorpay's reply, verified","the provider's truth"],
   ["campaigns","a budget-capped offer + A/B config","grow revenue, bounded"],
   ["audit_events","every important step, hash-chained","the proof"]],[34*mm,74*mm,66*mm])]

F+=[PageBreak(), para("How they connect",H2), diag("er","Figure 1 — The simple relationship map. Everything hangs off a merchant."),
  para("SELL (buy) path",H2), diag("buy","Figure 2 — A purchase: products → cart → order → authorize → pay → webhook → audit"),
  para("GROW path",H2), diag("grow","Figure 3 — An agent runs a campaign; it creates orders and is audited")]

F+=[para("The 5 rules that do the hard work",H2),
  bullets(["<b>Merchant stored everywhere.</b> Every table has a tenant_id, and the database (Row-Level Security) makes sure one merchant can never see another's rows.",
           "<b>Money is exact.</b> Amounts are whole numbers (the smallest unit) + a currency. Never decimals.",
           "<b>One-time permission.</b> An authorization is tied to one cart, one amount, one policy version, and it expires.",
           "<b>If the provider is slow, we wait.</b> A payment can be 'unknown'; we never retry it blindly — we check with the provider first.",
           "<b>Every step is recorded.</b> The audit trail is linked by a hash (tamper-evident, not tamper-proof)."])]

F+=[PageBreak(), para("A tiny example (just the important columns)",H2),
  block("""
-- product
create table products (
  id uuid primary key,
  tenant_id uuid not null,      -- which merchant
  sku text,
  name text,
  price_minor bigint,           -- simplest currency unit, e.g. paise
  currency char(3)
);

-- cart (server-priced, hashed)
create table carts (
  id uuid primary key,
  tenant_id uuid not null,
  agent_id uuid,
  cart_hash text,               -- snapshot so it can't be silently changed
  price_version text,
  total_minor bigint,
  expires_at timestamptz
);

-- order (the locked buy)
create table orders (
  id uuid primary key,
  tenant_id uuid not null,
  cart_id uuid,
  policy_version text,
  total_minor bigint,
  status text
);

-- payment
create table payments (
  id uuid primary key,
  tenant_id uuid not null,
  order_id uuid,
  amount_minor bigint,
  provider text,                 -- razorpay
  status text,                   -- includes UNKNOWN
  idempotency_key text unique
);

-- isolation (app role cannot bypass this)
alter table orders enable row level security;
create policy tenant_isolation on orders
  using (tenant_id = current_setting('app.tenant_id')::uuid)
  with check (tenant_id = current_setting('app.tenant_id')::uuid);"""),
  para("That's it. More columns exist, but this is the shape.",NOTE)]

doc.build(F)
print("PDF written:", out, out.stat().st_size, "bytes")
