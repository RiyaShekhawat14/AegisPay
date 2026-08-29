#!/usr/bin/env bash
set -euo pipefail
psql -h localhost -U aegispay_migration -d aegispay -f db/migrations/0001_initial.sql
cd api && pytest -q tests/integration
