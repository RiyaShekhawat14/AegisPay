# AegisPay — CI Failure Log

> Living document. Every time CI fails, record the error, the root cause, the fix, and the
> prevention here so the same class of failure does not recur. Run `make verify` (lint + type +
> test) locally before pushing to catch these in seconds instead of minutes.

## How to reproduce locally

```bash
# match the CI environment exactly (CI installs the latest allowed versions)
cd api && pip install -e ".[dev]"
make verify                 # lint + type + test
```

Check CI yourself:

```bash
gh run list --limit 5
gh run view <RUN_ID> --log-failed
```

---

## 1. `AttributeError: '_IncludedRouter' object has no attribute 'path'`

- **When:** push `4ba9146`, API CI, job `test`, step "Unit tests".
- **What failed:** `api/tests/unit/test_smoke.py::test_app_imports_and_lists_health_route`
  — `1 failed, 40 passed`.
- **Exact error:**
  ```
  AttributeError: '_IncludedRouter' object has no attribute 'path'
  tests/unit/test_smoke.py:15: AttributeError
  ```
- **Why (root cause):** The smoke test enumerated routes by iterating `app.routes` and reading
  `route.path` on each element. FastAPI's iteration contract for `app.routes` is a private
  implementation detail. In the FastAPI version pinned by CI (`0.141.1`, resolved from the
  open-ended `fastapi>=0.115`), `include_router` stores an internal `_IncludedRouter` object
  that has no `.path` attribute, so the comprehension raised `AttributeError`.

  The local dev box happened to have an older FastAPI (`0.135.2`) where `app.routes` still
  contained `APIRoute`/`Route` objects with `.path`. The exact same code passed locally and
  failed in CI because of **dependency version skew**: CI resolves `>=` ranges to the latest
  release (nothing was pinned or locked to a tested version).

- **Fix (committed):** Stop using `app.routes` internals. Enumerate paths from the stable,
  public OpenAPI schema instead:
  ```python
  paths = set(app.openapi()["paths"])
  assert "/v1/health" in paths
  assert "/v1/me" in paths
  ```
  Verified green against FastAPI `0.141.1` (the exact CI version) — 41/41 tests pass.

- **Prevention (so it does not recur):**
  1. Never introspect `app.routes`; use `app.openapi()` for path/route assertions.
  2. Bounded the FastAPI range in `api/pyproject.toml` to a tested window
     (`fastapi>=0.115,<0.142`) so CI cannot silently jump to an untested release. Other deps
     already carry upper bounds for the same reason.
  3. Reproduce CI locally with `pip install -e .[dev]` (install the latest resolved versions)
     before pushing — that is what surfaced the mismatch.
  4. The smoke test is now version-agnostic, so a FastAPI upgrade no longer breaks it.

---

## 2. (Template) Post-new failures here

- **When:** <commit / run id>
- **What failed:** <job + step>
- **Exact error:** <paste error>
- **Why (root cause):** <analysis>
- **Fix (committed):** <change>
- **Prevention:** <guard / test / pin>

---

## Prevention checklist (before every push)

- [ ] `make verify` locally green (lint + type + test).
- [ ] `ruff format --check api` clean (100 files).
- [ ] New code adds a test so the suite grows, never shrinks.
- [ ] Env reproduces CI: `pip install -e "api[dev]"` (latest resolved), not a stale base env.
- [ ] No secrets or untracked artifacts staged.
