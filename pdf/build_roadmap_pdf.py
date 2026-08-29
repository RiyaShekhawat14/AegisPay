"""Render the reviewed implementation roadmap as a PDF.

This intentionally uses only ReportLab so the export works without Pandoc or a browser.
It is a small Markdown subset renderer for this roadmap's headings, lists, tables, code
blocks, blockquotes, and inline emphasis.
"""

from html import escape
from pathlib import Path
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    PageTemplate,
    Paragraph,
    Preformatted,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "51-implementation-roadmap.md"
OUTPUT = ROOT / "docs" / "pdf" / "AegisPay-Implementation-Roadmap.pdf"

FONT = Path(r"C:\Windows\Fonts\arial.ttf")
FONT_BOLD = Path(r"C:\Windows\Fonts\arialbd.ttf")
if FONT.exists() and FONT_BOLD.exists():
    pdfmetrics.registerFont(TTFont("Arial", str(FONT)))
    pdfmetrics.registerFont(TTFont("Arial-Bold", str(FONT_BOLD)))
    BODY_FONT, BOLD_FONT = "Arial", "Arial-Bold"
else:
    BODY_FONT, BOLD_FONT = "Helvetica", "Helvetica-Bold"

styles = getSampleStyleSheet()
BODY = ParagraphStyle(
    "RoadmapBody", parent=styles["BodyText"], fontName=BODY_FONT,
    fontSize=8.6, leading=11.2, textColor=colors.HexColor("#202938"),
    spaceAfter=4,
)
H1 = ParagraphStyle(
    "RoadmapH1", parent=BODY, fontName=BOLD_FONT, fontSize=18, leading=22,
    textColor=colors.HexColor("#0B3D6B"), spaceBefore=4, spaceAfter=10,
)
H2 = ParagraphStyle(
    "RoadmapH2", parent=BODY, fontName=BOLD_FONT, fontSize=13, leading=16,
    textColor=colors.HexColor("#12377B"), spaceBefore=10, spaceAfter=6,
)
H3 = ParagraphStyle(
    "RoadmapH3", parent=BODY, fontName=BOLD_FONT, fontSize=10.5, leading=13,
    textColor=colors.HexColor("#20406B"), spaceBefore=7, spaceAfter=4,
)
QUOTE = ParagraphStyle(
    "RoadmapQuote", parent=BODY, fontName=BOLD_FONT, backColor=colors.HexColor("#EDF3FA"),
    borderPadding=6, borderColor=colors.HexColor("#B7CCE4"), borderWidth=0.5,
)
CODE = ParagraphStyle(
    "RoadmapCode", parent=BODY, fontName="Courier", fontSize=7.2, leading=9,
    backColor=colors.HexColor("#F3F5F7"), borderPadding=5,
)
TABLE_HEAD = ParagraphStyle(
    "RoadmapTableHead", parent=BODY, fontName=BOLD_FONT, fontSize=7.6,
    leading=9.5, textColor=colors.white,
)
TABLE_CELL = ParagraphStyle("RoadmapTableCell", parent=BODY, fontSize=7.4, leading=9)


def inline(text: str) -> str:
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


def p(text: str, style=BODY) -> Paragraph:
    return Paragraph(inline(text), style)


def is_table_row(line: str) -> bool:
    return line.strip().startswith("|") and line.strip().endswith("|")


def table_flow(lines: list[str]):
    rows = []
    for line in lines:
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if all(set(cell) <= {"-", ":", " "} for cell in cells):
            continue
        rows.append(cells)
    if not rows:
        return []
    width = max(len(row) for row in rows)
    rows = [row + [""] * (width - len(row)) for row in rows]
    data = [[p(cell, TABLE_HEAD if i == 0 else TABLE_CELL) for cell in row]
            for i, row in enumerate(rows)]
    col_widths = [175 * mm / width] * width
    result = Table(data, colWidths=col_widths, repeatRows=1, hAlign="LEFT")
    result.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0B3D6B")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F7FA")]),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#C7D2DE")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return [result, Spacer(1, 4)]


def build_story() -> list:
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    story = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
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
            story.append(Preformatted("\n".join(code), CODE))
            i += 1
            continue
        if stripped.startswith("|"):
            rows = []
            while i < len(lines) and is_table_row(lines[i]):
                rows.append(lines[i])
                i += 1
            story.extend(table_flow(rows))
            continue
        match = re.match(r"^(#{1,3})\s+(.*)$", stripped)
        if match:
            level, title = len(match.group(1)), match.group(2)
            story.append(p(title, {1: H1, 2: H2, 3: H3}[level]))
            i += 1
            continue
        if stripped.startswith(">"):
            story.append(p(stripped[1:].strip(), QUOTE))
            i += 1
            continue
        if re.match(r"^[-*]\s+", stripped):
            story.append(p("• " + re.sub(r"^[-*]\s+", "", stripped)))
            i += 1
            continue
        if re.match(r"^\d+\.\s+", stripped):
            story.append(p(stripped))
            i += 1
            continue
        story.append(p(stripped))
        i += 1
    return story


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont(BODY_FONT, 7)
    canvas.setFillColor(colors.HexColor("#687586"))
    canvas.drawString(18 * mm, 9 * mm, "AegisPay | Complete Implementation Roadmap")
    canvas.drawRightString(A4[0] - 18 * mm, 9 * mm, f"Page {doc.page}")
    canvas.setStrokeColor(colors.HexColor("#D6DEE8"))
    canvas.line(18 * mm, 13 * mm, A4[0] - 18 * mm, 13 * mm)
    canvas.restoreState()


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    frame = Frame(18 * mm, 16 * mm, A4[0] - 36 * mm, A4[1] - 32 * mm,
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc = BaseDocTemplate(str(OUTPUT), pagesize=A4, title="AegisPay Implementation Roadmap",
                          author="AegisPay Engineering")
    doc.addPageTemplates([PageTemplate(id="roadmap", frames=[frame], onPage=footer)])
    doc.build(build_story())
    print(f"PDF written to {OUTPUT} ({OUTPUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
