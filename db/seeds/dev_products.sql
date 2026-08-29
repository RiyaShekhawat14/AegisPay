-- Sample catalog for local dev
insert into products (tenant_id, sku, name, category, price_minor, currency, status) values
  (gen_random_uuid(), 'RS-BLK-42', 'Runner Pro 42', 'shoes/running', 349900, 'INR', 'ACTIVE');
