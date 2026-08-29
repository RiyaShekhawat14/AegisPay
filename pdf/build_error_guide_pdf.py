"""Render the project error & troubleshooting guide (docs/error-guide.md) as a PDF."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pdf.markdown_pdf import render  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "error-guide.md"
OUTPUT = ROOT / "docs" / "pdf" / "AegisPay-Error-Guide.pdf"


def main():
    render(
        SOURCE.read_text(encoding="utf-8"),
        OUTPUT,
        brand="AegisPay | Error & Troubleshooting Guide",
        doc_title="AegisPay Error & Troubleshooting Guide",
    )
    print(f"PDF written to {OUTPUT} ({OUTPUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
