-- Product images: an optional URL the merchant provides so buyers see the product.
-- Nullable (existing rows keep working); never interpreted as code by the AI.

alter table products add column if not exists image_url text;
