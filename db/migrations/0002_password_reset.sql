-- Password reset tokens. Global identity table (user-scoped, NOT tenant-scoped) so a reset
-- can be requested/redeemed without knowing the tenant. Stores only a SHA-256 hash of the
-- opaque reset token, never the token itself. Single-use with an expiry.

create table if not exists password_reset_tokens (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id),
  token_hash text not null,
  expires_at timestamptz not null,
  used_at timestamptz,
  created_at timestamptz not null default now()
);

create index if not exists password_reset_tokens_user_idx on password_reset_tokens (user_id);
create index if not exists password_reset_tokens_token_hash_idx on password_reset_tokens (token_hash);

-- Keep the app role able to insert/lookup tokens, but only the app role (which is NOT a
-- superuser and cannot bypass RLS) uses it; the migration role owns the DDL.
grant select, insert, update on password_reset_tokens to aegispay_app;
