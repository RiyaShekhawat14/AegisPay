# Architecture
One control plane (FastAPI) + an isolated AI runtime, over PostgreSQL (RLS multi-tenant) + Redis + SQS. A Protocol Gateway normalizes all agent protocols into one canonical intent; no protocol can bypass the control plane.
See docs/02-system-architecture.md, docs/00-architecture-master.md, docs/pdf/AegisPay-Agentic-Commerce-Architecture-V4.pdf.
