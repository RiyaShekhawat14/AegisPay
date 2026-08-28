# 06 — Data Dictionary

Machine-readable summary of the canonical fields. Types: `BIGINT` money (minor units),
`TIMESTAMPTZ`, `VARCHAR`, `JSONB`, `BYTEA` (encrypted), `CHAR(64)` (hash). `_enc` =
field-level encrypted. Every tenant table has `tenant_id`, `created_at`, `updated_at`,
optional `deleted_at`, and RLS. Full table definitions in `docs/05`.

## merchants
id · tenant_id · name · slug · business_type · country · currency · status(enum) ·
default_autonomy_level(L0..L4) · razorpay_key_id · kms_ref · created_at · updated_at · deleted_at

## merchant_users
id · tenant_id · user_id · email_enc · name · role(RBAC) · password_hash · oidc_sub ·
mfa_enabled · status · last_login_at · created_at · updated_at · deleted_at

## agents
id · tenant_id · agent_key · owner_user_id · agent_type · version · scopes(jsonb) ·
allowed_tools(jsonb) · trust_level · status(ACTIVE|SUSPENDED|REVOKED|EXPIRED) ·
expires_at · created_at · updated_at · deleted_at

## agent_credentials
id · tenant_id · agent_id · name · credential_hash · credential_prefix · scopes(jsonb) ·
last_used_at · revoked_at · expires_at · created_at · updated_at

## agent_sessions
id · tenant_id · agent_id · session_key · ip · device · user_agent · started_at ·
ended_at · revoked_at

## customers
id · tenant_id · customer_ref · email_enc · phone_enc · name_enc · status ·
created_at · updated_at · deleted_at

## customer_authorizations (mandates)
id · tenant_id · customer_id · agent_id · version · scope · upper_value_minor ·
per_txn_minor · valid_from · valid_to · status · mandate_hash · created_at · updated_at · deleted_at

## mandates
id · tenant_id · customer_authorization_id · agent_id · terms(jsonb) ·
value_limit_minor · per_txn_minor · valid_from · valid_to · mandate_hash · status ·
signed_by · created_at · deleted_at

## catalogs
id · tenant_id · name · slug · description · status · created_at · updated_at · deleted_at

## products
id · tenant_id · catalog_id · sku · name · name_indexed(tsvector) · description ·
category · price_minor · currency · status · allow_list · block_list · metadata(jsonb) ·
created_at · updated_at · deleted_at

## inventory
id · tenant_id · product_id · stock · version · reserved · updated_at · deleted_at

## carts
id · tenant_id · customer_id · agent_id · status · currency · cart_hash · expires_at ·
created_at · updated_at · deleted_at

## cart_items
id · tenant_id · cart_id · product_id · quantity · unit_price_minor · line_total_minor ·
hash_component · created_at · updated_at · deleted_at

## commerce_intents
id · tenant_id · agent_id · user_id · kind · summary · raw_hash · intent_hash ·
intent_payload(jsonb) · status · expires_at · created_at · updated_at · deleted_at

## intent_items
id · tenant_id · intent_id · product_id · product_snapshot(jsonb) · quantity ·
unit_price_minor · line_total_minor · hash_component · created_at

## orders
id · tenant_id · cart_id · intent_id · customer_id · agent_id · currency · total_minor ·
status(enum) · policy_version · risk_score · authorization_id · created_at · updated_at · deleted_at

## order_items
id · tenant_id · order_id · product_id · product_snapshot(jsonb) · quantity ·
unit_price_minor · line_total_minor · created_at

## payments
id · tenant_id · order_id · amount_minor · currency · provider · provider_payment_id ·
provider_order_id · capture_id · status(enum) · idempotency_key · attempt_count ·
unknown_since · created_at · updated_at

## payment_attempts
id · tenant_id · payment_id · attempt_no · provider_txn_id · request_hash · outcome ·
provider_response_hash · created_at

## refunds
id · tenant_id · payment_id · amount_minor · currency · reason · status ·
idempotency_key · provider_refund_id · created_at · updated_at

## policies
id · tenant_id · name · version · status · dsl(text) · effective_at · supersedes_pointer ·
created_by · created_at · updated_at

## policy_versions
id · tenant_id · policy_id · version · dsl · checksum · published_at · retired_at · created_by

## policy_rules
id · tenant_id · policy_id · rule_id · effect(ALLOW|DENY|REQUIRE_APPROVAL|REQUIRE_STEPUP) ·
dimension · operator · value(jsonb) · precedence · not_before · enabled

## risk_assessments
id · tenant_id · target_type · target_id · score · level(LOW|MEDIUM|HIGH|CRITICAL) ·
factors(jsonb) · recommended_action · model_version · created_at

## approval_requests
id · tenant_id · order_id · agent_id · requester_user_id · scope_hash ·
require_approver_role · amount_minor · status · expires_at · decided_at · created_at · updated_at

## approval_decisions
id · tenant_id · approval_request_id · approver_user_id · decision(APPROVE|REJECT) ·
reason · decision_hash · created_at

## campaigns
id · tenant_id · agent_id · name · budget_minor · spent_minor · status · targeting(jsonb) ·
discount_policy_ref · policy_version · risk_score · created_at · updated_at · deleted_at

## campaign_actions
id · tenant_id · campaign_id · kind(recommend|upsell|coupon) · product_id · payload(jsonb) ·
order_id · created_at

## protocol_sessions
id · tenant_id · agent_id · protocol · external_session_id · authn_ref · scopes(jsonb) ·
started_at · ended_at

## audit_events
id · tenant_id · event_type · actor · actor_type · correlation_id · causation_id ·
trace_id · payload(jsonb) · previous_hash · event_hash · event_signature · created_at

## audit_event_hashes
id · tenant_id · anchor_ts · chain_start · chain_end · anchor_hash · anchored_to · created_at

## idempotency_keys
key · tenant_id · endpoint · request_hash · response · status · expires_at · created_at

## webhook_events
id · tenant_id · provider · provider_event_id · event_type · payload_hash ·
raw_reference · signature_verified · status · received_at · created_at

## webhook_deliveries
id · tenant_id · webhook_event_id · delivery_no · status · next_attempt_at · attempts ·
max_attempts · last_error · created_at

## reconciliation_jobs
id · tenant_id · payment_id · job_no · status · next_attempt_at · attempts · max_attempts ·
result · escalated · created_at · updated_at

## notifications
id · tenant_id · channel · recipient_ref · kind · payload(jsonb) · status · attempts ·
next_attempt_at · created_at
