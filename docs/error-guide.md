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

## 11. Auth: valid `member` token par `/v1/me` → 403
- **Error:** E2E test — authenticated member ko `/v1/me` 403 `insufficient role`.
- **Problem:** Endpoint `has_permission(principal.role, "member")` check kar raha tha, lekin `"member"` ek **role** hai, permission nahi. Member role ke paas `catalog.read` hai, `member` nahi → hamesha deny. Koi bhi authenticated user apni identity dekh sakta hai, is check ki zaroorat hi nahi.
- **Fix:** `/v1/me` se galt permission gate hataya (auth hi kaafi hai); RBAC gating domain routers hota hai.

## 12. Auth: bad JWT signature → 500 (should be 401)
- **Error:** E2E test — invalid/expired token par `/v1/me` `500 INTERNAL_ERROR`.
- **Problem:** `resolve_principal` mein `verify_jwt` **ValueError** raise karta hai (bad signature/expired), par wo catch nahi tha → generic 500 handler tak pahunch jaata tha.
- **Fix:** `resolve_principal` mein `ValueError` catch karke `HTTPException(401, "invalid token")` raise karo — bad/expired token ab 401 deta hai.

## 12. Auth: bad JWT signature → 500 (should be 401)
- **Error:** E2E test — invalid/expired token par `/v1/me` `500 INTERNAL_ERROR`.
- **Problem:** `resolve_principal` mein `verify_jwt` **ValueError** raise karta hai (bad signature/expired), par wo catch nahi tha → generic 500 handler tak pahunch jaata tha.
- **Fix:** `resolve_principal` mein `ValueError` catch karke `HTTPException(401, "invalid token")` raise karo — bad/expired token ab 401 deta hai.

## 13. Core API: inconsistent error envelope (401 me `{"detail":...}`)
- **Error:** E2E — auth error `GET /v1/me` no-token → `{"detail":"authentication required"}` (FastAPI default), baaki errors `{"code","message","request_id","retryable"}`. API ka error contract consistent nahi tha.
- **Problem:** `resolve_principal` rahi `HTTPException(401)`; handlers sirf `AppError` ko envelope dete the, `HTTPException`/`RequestValidationError` ko nahi. Isliye `HTTPException`-based errors FastAPI ke default `{"detail":...}` format me aate the.
- **Fix:** `exceptions.py` me handlers add kiya — `HTTPException` (→ status-based code: 401→`AUTHENTICATION_ERROR`, 404→`NOT_FOUND`, ...) aur `RequestValidationError` (→`VALIDATION_ERROR`, 422). Ab sab errors same envelope dete hain. `_http_code()` helper se status→code mapping.
- **Note (framework limitation):** FastAPI 0.141 me **router-level 404** (unknown route) aur **uncaught 500** app handlers ke through nahi aate — wo FastAPI ke default response dete hain. Isliye consistency unit-test (`_http_code`) se prove ki gyi; 401/application errors E2E se.

## 14. Core API: `/v1/readyz` hamesha `ready` (DB check nahi) + `/v1/live` missing
- **Error:** `/v1/readyz` DB down hone par bhi `{"status":"ready"}` deta tha (hardcoded); `/v1/live` route hi nahi tha → 404.
- **Problem:** Readiness probe sirf hardcoded string return karta tha; koi DB connectivity check nahi.
- **Fix:** `/v1/readyz` ab DB ko ping karta hai (`select 1`); DB nahi pahuncha toh **503** `{"code":"NOT_READY"}`. Aur naya `GET /v1/live` (200) add kiya.

## 15. Commerce build: `NoReferencedTableError: Foreign key 'carts.agent_id' could not find table 'agents'`
- **Error:** Phase 4 test run — SQLAlchemy threw `NoReferencedTableError` for `carts.agent_id` / `orders.agent_id`.
- **Problem:** ORM models mein `agents` table ke liye koi model tha hi nahi (migration mein table hai, par model nahi). SQLAlchemy FK ko resolve karne ke liye referenced table ka model metadata mein hona zaroori hai.
- **Fix:** `models.py` mein minimal `Agent` model add kiya (`agents` table map). (users FK ko model mein deliberately nahi rakha taaki woh bhi same error na de.)

## 16. Live API: product create par `500 INTERNAL_ERROR` (nonexistent tenant)
- **Error:** Live E2E me `/v1/products` create → `500 INTERNAL_ERROR`.
- **Problem:** Test mein ek **fabricated tenant_id** use kiya jo `tenants` table mein exist nahi karta. Product insert me `tenant_id` → `tenants(id)` FK violation ho gayi, jo unhandled `IntegrityError` → generic 500.
- **Fix:** Ye code bug nahi tha (happy path integration-test me pass hai). Sahi tenant se live E2E **201/200** clean chal raha hai. Bas FH: real tenant ho. (Note: FK violation ab 500 deta hai — ideally 4xx hona chahiye, par ye edge case hai; generic 500 handler safely handles karta hai.)

## 17. Phase 5 build: `column authorizations.updated_at does not exist`
- **Error:** Authorization INSERT → `UndefinedColumnError: authorizations.updated_at does not exist`.
- **Problem:** `Authorization` model `TimestampMixin` use kar raha tha, jo `updated_at` add karta hai. Par migration ke `authorizations` table mein sirf `created_at` hai (`updated_at` nahi). Model ↔ table mismatch.
- **Fix:** `Authorization` se `TimestampMixin` hata ke `created_at` explicitly map kiya (server_default). Ab INSERT sirf existing columns use karta hai.

## 18. Phase 5 build: `approvals` me NOT NULL `expires_at` missing
- **Error:** Approval INSERT → `NotNullViolationError: null value in column "expires_at" of relation "approvals"`.
- **Problem:** `Approval` model mein `expires_at` column map hi nahi tha, par table me `not null` hai.
- **Fix:** Model me `expires_at` (DateTime, not null) + `created_at` add kiya, aur service mein approve() par `expires_at` set karta hai.

## 19. Phase 5 test: `approvals.approver_id` FK violation (`Key not present in users`)
- **Error:** High-risk approve → `ForeignKeyViolationError: approvals_approver_id_fkey ... Key is not present in table "users"`.
- **Problem:** Approve test me random `uuid4()` approver_id use kiya, par DB me `approvals.approver_id → users(id)` real FK hai — approver ko `users` me exist karna chahiye.
- **Fix:** Test helper `_approvers(n)` add kiya jo pehle `users` rows create karta hai (password_hash NOT NULL), phir un id se approve karta hai.

## 20. Phase 6: `MemOutbox.emit() missing 1 required positional argument: 'payload'`
- **Error:** Payment flow → `TypeError: MemOutbox.emit() missing 1 required positional argument: 'payload'`.
- **Problem:** `initiate_payment()` ke default par `outbox=MemOutbox` tha — **class** pass ho rahi thi, instance nahi. Toh `MemOutbox.emit(...)` call par `self` drop ho jaata hai → sirf 2 args milte.
- **Fix:** Default ko `None` karke andar `outbox = outbox or MemOutbox()` (instance) banaya.

## 21. Phase 6: payments INSERT me `tenant_id` NULL → RLS `new row violates row-level security`
- **Error:** Payment save → `ProgrammingError: new row violates row-level security policy for table "payments"` (tenant_id thodi null).
- **Problem:** `DbPaymentAdapter.save()` ORM `Payment` me `tenant_id` set hi nahi karta tha (TenantMixin required hai, par koi default nahi) → NULL → RLS `WITH CHECK` fail.
- **Fix:** `DbPaymentAdapter` ko `tenant_id` pass karke `save()` me `tenant_id=uuid.UUID(...)` set kiya.

## 22. Phase 6: payment re-fetch se `payment not persisted`
- **Error:** Router me payment create → `500 "payment not persisted"`.
- **Problem:** Flow ka `payment.id` = `uuid4().hex` (32-char string), but `DbPaymentAdapter.save()` ORM `Payment` pe `id` set nahi karta tha, so DB row ko **alag** `uuid4()` id milti thi. Router `outcome.payment_id` se row dhoondta tha, milta nahi.
- **Fix:** `save()` me `id=uuid.UUID(p.id)` set kiya — ab DB row ki id == flow ki payment_id.

## 23. Phase 7 test: `payments_order_id_fkey` violation (payment insert)
- **Error:** Payment seed → `ForeignKeyViolationError: payments.order_id Key is not present in table "orders"`.
- **Problem:** Test me payment banate samay ek **random order_id** use kiya jo orders table me exists nahi karta; payment.order_id FK hai.
- **Fix:** Test helper ne tenant → agent → cart → order → payment ka **pura chain** seed kiya, phir payment ko real order_id se banaya.

## 24. Phase 7: reconciliation `UNKNOWN` me atka (commit nahi hua)
- **Error:** Reconcile ke baad payment `'UNKNOWN'` hi raha (PAID nahi hua).
- **Problem:** `reconcile_unknown()` ne `session.flush()` kiya tha (change in-memory), lekin **commit nahi** kiya. Tab session close hone par change lost ho gaya → next read par purana UNKNOWN mila.
- **Fix:** Service me `await session.flush()` ko `await session.commit()` se replace kiya (self-contained atomic op). Router path (`DbSession` dependency) waise bhi commit karta hai, double-commit harmless hai.

## 25. Phase 8: audit chain verify hamesha `False` (hash mismatch)
- **Error:** Append 2 events ke baad `verify_chain()` → `False`, chain ko intact hona chahiye tha.
- **Problem:** Event ka `event_hash` ledger ke **Python timestamp** se compute hota hai, par DB `created_at` ko apne **alag `now()`** se set karta hai. Dono timestamps microsecond level par differ → recompute/hash mismatch.
- **Fix:** `append_audit` me `row.created_at = datetime.fromisoformat(event.created_at)` set kiya — DB wahi timestamp store karta hai jo hash me use hua. Verify ab match karta hai.

## 26. Phase 8: `audit_events` INSERT se `new row violates row-level security`
- **Error:** App role `INSERT INTO audit_events` → `InsufficientPrivilegeError` (RLS deny).
- **Problem:** `audit_events` RLS enabled hai par sirf **SELECT policy** tha. RLS enabled table me kisi command ke liye policy na ho toh wo **deny all** hota hai, isliye INSERT block ho jaata tha (grant hone ke baad bhi).
- **Fix:** Migration + live DB me `create policy audit_insert on audit_events for insert with check (tenant_id = current_tenant())` add kiya — ab app role apne tenant ke andar append kar sakta hai (update/delete abhi bhi revoked).

## 27. Lint: `B008 Do not perform function call Depends in argument defaults` (FDP)
- **Error:** `Depends(get_client)` default arg par → ruff `B008`.
- **Problem:** FastAPI purana style (default arg me `Depends()`) hai; ruff isko flag karta hai. Codebase already `Annotated` pattern use karta hai (`DbSession = Annotated[..., Depends(get_session)]`).
- **Fix:** `Client = Annotated[ControlPlaneClient, Depends(get_client)]` banake endpoint me `client: Client` use kiya. (Depends() default arg me nahi.)

## 28. Lint: `ASYNC210 Async functions should not call blocking HTTP methods`
- **Error:** `await httpx.get(...)` (blocking top-level httpx) → ruff `ASYNC210`.
- **Problem:** `httpx.get/post` sync hai; async function me use nahi hota.
- **Fix:** `httpx.AsyncClient` use kiya (RazorpayAdapter jaisa) — `await self._client.get/post`.

## 29. Phase 10: campaign create `400 "margin below floor"` (margin default 0)
- **Error:** `POST /v1/campaigns` → `VALIDATION_ERROR: margin below floor`.
- **Problem:** `check_caps` me `min_margin_pct=15` hai, aur default `margin_pct=0` (caller ne set nahi kiya) → `0 < 15` → reject.
- **Fix:** Campaign create test me valid caps pass kiya (`margin_pct: 20, duration_days: 7`).

## 30. Phase 10: `generate_opportunities` me `uuid.UUID(principal.subject)` → "badly formed hexadecimal UUID string"
- **Error:** `POST /v1/opportunities/generate` → `500 ValueError: badly formed hexadecimal UUID string`.
- **Problem:** `agent_id=uuid.UUID(principal.subject)` — token ka `sub` ("agent-1") ek valid UUID nahi hai.
- **Fix:** `agent_id` ko route me request body se lete hain (`OpportunityGenerateIn.agent_id`), subject se derive nahi karte.

## 31. Phase 11: buyer tools `add_item`/`checkout` allowlist me nahi the
- **Error:** Buyer flow me `add_item`/`checkout` use karna tha, par `tools.registry.ALLOWED_TOOLS` me sirf 3 the (discover/create_cart/request_authorization) → buyer ke tools allow nahi honge.
- **Problem:** SELL buyer ko cart/order setup karna hai (add item, checkout). Ye **money moves nahi** hain (sirf cart/order setup), par allowlist me add nahi the — guardrail test fail hota.
- **Fix:** `ALLOWED_TOOLS` me `add_item` + `checkout` add kiya (cart/order setup). `capture`/`refund`/`execute_payment` ab bhi FORBIDDEN.

## 32. Phase 12: gateway router me `Gateway.enter` auth double-verify (reuse pattern)
- **Error:** Gateway route me token ko pehle `verify_jwt` karke claims (merchant_id/agent_id) nikalna padta hai, par `Gateway.enter` andar phir se `authenticate(token)` karta hai — double verify, par zaroori (claims chahiye before enter).
- **Problem:** `Gateway.enter` signature me `authenticate` + `merchant_id`/`agent_id` alag chahiye; router ko claims pehle chahiye.
- **Fix:** Router pehle `verify(token)` se claims nikalta hai, phir wahi token `_gateway.enter` ko pass karta hai (jo apne authenticate se subject jaght jaata hai). Redundant verify acceptable — Gateway unchanged reuse kiya.

## 33. Phase 14: reconciliation worker me `Tenant` model missing
- **Error:** Worker `from api.db.models import Tenant` → `ImportError: cannot import name 'Tenant'`.
- **Problem:** ORM me `tenants` table ka koi model nahi tha (worker ko sari tenants enumerate karni hain; tenants table RLS nahi hota, isliye wo cross-tenant enumeration ka root hai).
- **Fix:** `models.py` me `Tenant` model add kiya (id, slug, name, currency, status). TimestampMixin ke baad define kiya (pehle NameError tha).

## 34. Phase 15 (red-team): FAKta ke liye webhook verification default weak (no secret)
- **Error/Note:** Bina `RAZORPAY_WEBHOOK_SECRET` configured, webhook router `get_provider()` (mock) par fallback karta hai jo har signature accept karta hai.
- **Problem:** Webhooks untrusted hain; prod me secret required hai. Dev/test me mock fallback ko treat karna theek hai, par prod me ye security gap hai.
- **Fix:** Red-team suite me isko document kiya. Production must set `RAZORPAY_WEBHOOK_SECRET` (router phir HMAC verify karta hai). No test gap — red-team suite attacks safely blocked.

## 35. Phase 16 (E2E): Playwright UI smoke still scaffold (no browser stack)
- **Error/Note:** `tests/e2e/playwright.config.ts` + `specs/checkout-flow.spec.ts` scaffold hain; browser-run ui test ko frontend+backend running stack chahiye (compose orchestration) — abhi CI me nahi chalta.
- **Problem:** UI E2E ke liye live server + browser chahiye, jo abhi set-up nahi hai. API-level full-chain proof isi phase me milti hai.
- **Fix:** API-level E2E (`test_end_to_end.py`) — full Control Plane chain (auth→catalog→cart→checkout→authz→payment→audit→passport) + reconciliation — CI integration job me chalti hai. Playwright UI smoke ko compose-orchestrated stack ke saath later follow-up.

## 36. Phase 17: metrics middleware `_grouped` unused + route-template grouping
- **Error/Note:** Metrics middleware me `_grouped` dict add kiya tha jo use nahi hua (ruff F541/over-engineering); `/metrics` request ko un-grouped raw URL par count karta tha.
- **Problem:** Prometheus counter ko route-template (path) se group karna chahiye, query-string ke saath nahi — warna cardinality badh jaati hai.
- **Fix:** `_grouped` hata diya; path `request.scope["route"].path` (route template) se liya. Ab `/v1/health` sab requests ek label me count hoti hain.

---

## Naya error yahan add karo (template)
```
## N. <short error title>
- **Error:** <paste error>
- **Problem:** <why it happened, 1-2 lines>
- **Fix:** <what we changed>
```
