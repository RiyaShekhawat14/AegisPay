"""Shared, dependency-light Markdown -> PDF renderer for AegisPay docs.

Uses only ReportLab (no Pandoc/browser). Supports the Markdown subset used by the AegisPay
docs: headings (1-3), bullet lists, numbered lists, fenced code blocks, blockquotes, tables,
horizontal rules, and inline emphasis / inline code.
"""

from html import escape
from pathlib import Path
import re

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageTemplate,
    Paragraph,
    Preformatted,
    Spacer,
    Table,
    TableStyle,
)

_FONTS = None


def _fonts() -> tuple[str, str]:
    global _FONTS
    if _FONTS:
        return _FONTS
    plain = Path(r"C:\Windows\Fonts\arial.ttf")
    bold = Path(r"C:\Windows\Fonts\arialbd.ttf")
    if plain.exists() and bold.exists():
        pdfmetrics.registerFont(TTFont("Arial", str(plain)))
        pdfmetrics.registerFont(TTFont("Arial-Bold", str(bold)))
        _FONTS = ("Arial", "Arial-Bold")
    else:
        _FONTS = ("Helvetica", "Helvetica-Bold")
    return _FONTS


def _make_styles() -> dict:
    body, bold = _fonts()
    base = getSampleStyleSheet()
    return {
        "body": ParagraphStyle("DocBody", parent=base["BodyText"], fontName=body,
                               fontSize=8.6, leading=11.2, textColor=colors.HexColor("#202938"),
                               spaceAfter=4),
        "h1": ParagraphStyle("DocH1", fontName=bold, fontSize=18, leading=22,
                             textColor=colors.HexColor("#0B3D6B"), spaceBefore=4, spaceAfter=10),
        "h2": ParagraphStyle("DocH2", fontName=bold, fontSize=13, leading=16,
                             textColor=colors.HexColor("#12377B"), spaceBefore=10, spaceAfter=6),
        "h3": ParagraphStyle("DocH3", fontName=bold, fontSize=10.5, leading=13,
                             textColor=colors.HexColor("#20406B"), spaceBefore=7, spaceAfter=4),
        "quote": ParagraphStyle("DocQuote", fontName=bold, backColor=colors.HexColor("#EDF3FA"),
                                borderPadding=6, borderColor=colors.HexColor("#B7CCE4"),
                                borderWidth=0.5),
        "code": ParagraphStyle("DocCode", fontName="Courier", fontSize=7.2, leading=9,
                               backColor=colors.HexColor("#F3F5F7"), borderPadding=5),
        "th": ParagraphStyle("DocTH", fontName=bold, fontSize=7.6, leading=9.5,
                             textColor=colors.white),
        "td": ParagraphStyle("DocTD", fontSize=7.4, leading=9),
    }


def _inline(text: str) -> str:
    code_spans = []

    def save_code(match):
        code_spans.append(escape(match.group(1), quote=False))
        return f"@@CODE{len(code_spans) - 1}@@"

    text = re.sub(r"`([^`]+)`", save_code, text)
    text = escape(text, quote=False)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", text)
    for index, code in enumerate(code_spans):
        text = text.replace(f"@@CODE{index}@@", f"<font name='Courier'>{code}</font>")
    return text.replace("→", "-&gt;")


def _is_table_row(line: str) -> bool:
    return line.strip().startswith("|") and line.strip().endswith("|")


def _table_flow(lines: list[str], styles: dict, width_pt: float):
    rows = []
    for line in lines:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if all(set(c) <= {"-", ":", " "} for c in cells):
            continue
        rows.append(cells)
    if not rows:
        return []
    ncols = max(len(r) for r in rows)
    rows = [r + [""] * (ncols - len(r)) for r in rows]
    data = [[_p(cell, styles["th"] if i == 0 else styles["td"]) for cell in row]
            for i, row in enumerate(rows)]
    tbl = Table(data, colWidths=[width_pt / ncols] * ncols, repeatRows=1, hAlign="LEFT")
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0B3D6B")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F7FA")]),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#C7D2DE")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return [tbl, Spacer(1, 4)]


def _p(text: str, style) -> Paragraph:
    return Paragraph(_inline(text), style)


def _story(source: str, styles: dict, width_pt: float) -> list:
    lines = source.splitlines()
    story = []
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        if not stripped:
            i += 1
            continue
        if stripped == "---":
            story.append(Spacer(1, 4))
            i += 1
            continue
        if stripped.startswith("```"):
            code = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            story.append(Preformatted("\n".join(code), styles["code"]))
            i += 1
            continue
        if stripped.startswith("|"):
            rows = []
            while i < len(lines) and _is_table_row(lines[i]):
                rows.append(lines[i])
                i += 1
            story.extend(_table_flow(rows, styles, width_pt))
            continue
        m = re.match(r"^(#{1,3})\s+(.*)$", stripped)
        if m:
            level, title = len(m.group(1)), m.group(2)
            story.append(_p(title, {1: styles["h1"], 2: styles["h2"], 3: styles["h3"]}[level]))
            i += 1
            continue
        if stripped.startswith(">"):
            story.append(_p(stripped[1:].strip(), styles["quote"]))
            i += 1
            continue
        if re.match(r"^[-*]\s+", stripped):
            story.append(_p("• " + re.sub(r"^[-*]\s+", "", stripped), styles["body"]))
            i += 1
            continue
        if re.match(r"^\d+\.\s+", stripped):
            story.append(_p(stripped, styles["body"]))
            i += 1
            continue
        story.append(_p(stripped, styles["body"]))
        i += 1
    return story


def render(source: str, output: Path, *, brand: str, doc_title: str,
           doc_author: str = "AegisPay Engineering") -> Path:
    """Render a Markdown string to a PDF at `output`."""
    output.parent.mkdir(parents=True, exist_ok=True)
    styles = _make_styles()
    body, bold = _fonts()
    width_pt = A4[0] - 36 * mm

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont(body, 7)
        canvas.setFillColor(colors.HexColor("#687586"))
        canvas.drawString(18 * mm, 9 * mm, brand)
        canvas.drawRightString(A4[0] - 18 * mm, 9 * mm, f"Page {doc.page}")
        canvas.setStrokeColor(colors.HexColor("#D6DEE8"))
        canvas.line(18 * mm, 13 * mm, A4[0] - 18 * mm, 13 * mm)
        canvas.restoreState()

    frame = Frame(18 * mm, 16 * mm, width_pt, A4[1] - 32 * mm,
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc = BaseDocTemplate(str(output), pagesize=A4, title=doc_title, author=doc_author)
    doc.addPageTemplates([PageTemplate(id="doc", frames=[frame], onPage=footer)])
    doc.build(_story(source, styles, width_pt))
    return output
