#!/usr/bin/env bash
set -euo pipefail
psql -h localhost -U aegispay_migration -d aegispay -f api/migrations/0001_init.sql
cd api && pytest -q tests/integration
