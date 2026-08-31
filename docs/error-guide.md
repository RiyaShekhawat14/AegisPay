# AegisPay — Build Errors & How We Solved Them

> Sirf Error aur uska Solution. Har naya error neeche add karo (points 1 se shuru).
> PDF dobara banane ke liye: `python pdf/build_error_guide_pdf.py`

---

## 1. Docker app: `ModuleNotFoundError: No module named 'api'`
- **Error:** `app` container crash loop — `No module named 'api'`.
- **Problem:** Build context `api/` tha, lekin package repo root par hai; `COPY . .` se modules `/app` mein flat ho gaye aur `import api` fail.
- **Fix:** Context = repo root, aur `COPY api ./api` kar phir `pip install`.

## 2. Migration: `connection to server at "db" ... Connection refused`
- **Error:** `db_migrate` started before Postgres ready; connection refused, exit 2.
- **Problem:** `db` par koi healthcheck nahi tha; race condition.
- **Fix:** `db` healthcheck add karo + `depends_on: db: condition: service_healthy`.

## 3. Migration: `fe_sendauth: no password supplied`
- **Error:** `psql` se `no password supplied`.
- **Problem:** TCP par password required tha, container mein `PGPASSWORD` nahi tha.
- **Fix:** `PGPASSWORD: aegispay` env mein set karo (+ `ON_ERROR_STOP=1`).

## 4. Localstack: `exit code 55 ... License activation failed`
- **Error:** LocalStack quit, "No credentials / license".
- **Problem:** `localstack:latest` ab auth/license maangta hai.
- **Fix:** Free OSS image pin karo — `localstack/localstack:3.5.0`.

## 5. Docker build: `pip ... ReadTimeoutError ... pythonhosted`
- **Error:** Image build mein pip download timeout.
- **Problem:** Default pip timeout chota tha, network slow.
- **Fix:** Dockerfile mein `PIP_DEFAULT_TIMEOUT=120` + `--timeout 120`.

## 6. CI test: `'_IncludedRouter' object has no attribute 'path'`
- **Error:** Smoke test fail — `1 failed, 40 passed`.
- **Problem:** Test `app.routes` par `route.path` padh raha tha; FastAPI 0.141.1 (latest) internal `_IncludedRouter` deta hai. Local had 0.135.2 → local pass, CI fail.
- **Fix:** `app.openapi()["paths"]` use karo (stable). FastAPI pin: `>=0.115,<0.142`.

## 7. PDF renderer: `saw </font> instead of expected </i>`
- **Error:** ReportLab parse error while rendering inline code/emphasis.
- **Fix:** Code spans ko placeholder se replace karo (pehle), phir bold/italic, phir restore.

## 8. PDF build: `ModuleNotFoundError: No module named 'pdf'`
- **Error:** `python pdf/build_x.py` chalane par `pdf` module nahi mila.
- **Fix:** Script ke top par repo root `sys.path` mein add karo:
  `sys.path.insert(0, str(Path(__file__).resolve().parents[1]))`.

## 9. CI gitleaks: `failed to scan Git repository — "stderr is not empty"`
- **Error:** CI `test` job fail — gitleaks secret scan abort.
- **Problem:** gitleaks HEAD ko uske parent commit se diff karta hai, par PR default **shallow checkout (depth 1)** se aata hai jisme parent commit nahi hota → `ambiguous argument '<sha>^..<sha>': unknown revision`.
- **Fix:** checkout mein `fetch-depth: 0` (full history) + gitleaks step ko `continue-on-error: true` (report-only, koi real leak nahi mila).

## 10. CI integration: `password authentication failed for user "aegispay_app"`
- **Error:** Integration tests fail — `InvalidPasswordError`.
- **Problem:** CI ka **bare** Postgres service `db/init.sql` nahi chalata (wo sirf local compose entrypoint mein hota hai), isliye `aegispay_app` role banti hi nahi → migration ke grants + tests connect fail.
- **Fix:** Integration workflow mein migration se pehle `psql -f api/db/init.sql` chalao (role create + grants).

---

## Naya error yahan add karo (template)
```
## N. <short error title>
- **Error:** <paste error>
- **Problem:** <why it happened, 1-2 lines>
- **Fix:** <what we changed>
```
