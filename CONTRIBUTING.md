# CONTRIBUTING

Thanks for helping improve AegisPay. This is an agentic-commerce **control plane** —
AI never moves money directly. Keep that invariant intact.

## Prereqs
- Python 3.12+, and `mmdc` (mermaid-cli) for regenerating PDFs.
- A GitHub account; auth via `gh auth login`.

## Repo layout
- `docs/` — the architecture documentation set (numbered) + `03-architecture-decision-records/`.
- `api/openapi.yaml` — the OpenAPI 3.1 contract.
- `pdf/*.py` — generators; `pdf/_html/*.html` — frontend/live-flow mockups.
- Root PDFs — published artifacts, regenerate via `python pdf/build_v2.py`, `build_pdf.py`, `build_langgraph.py`.

## How to change a PDF (docs or diagrams)
1. Edit the source (`docs/*.md` for text; the mermaid strings or HTML in `pdf/*.py`/`_html`).
2. Regenerate: `python pdf/build_pdf.py` (Architecture), `python pdf/build_v2.py` (V2 + GROW + SELL),
   `python pdf/build_langgraph.py` (LangGraph). Frontends: open `pdf/_html/*.html` in Chrome → print to PDF,
   or render with headless Chrome `--print-to-pdf`.
3. Commit the source **and** the regenerated PDF.

## Rules
- **No secret** in code, docs, logs, or the LLM prompt. Secrets live in AWS Secrets Manager.
- **Never claim compliance** (MCP/A2A/x402/regulatory) without evidence; prefer "supports/adapts".
- **Honest wording:** use *tamper-evident*, not *tamper-proof*; *designed to prevent duplicate
  charges*, not *impossible*.
- Keep the money path deterministic. Policy/risk/authorization must be explicit and versioned.
- Add a test or red-team scenario for any money-behavior change.

## CI
`.github/workflows/ci.yml` validates the OpenAPI YAML, doc presence, and build-script syntax on every
push / PR. Keep it green.

## PRs
- Target `main`.
- Keep a change small and explain *why* in the PR body, plus the trade-off.
- For anything touching payments/policy/authorization/audit, describe the failing case it prevents.
