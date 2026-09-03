"""Idempotent seed: a merchant tenant, an agent, and products so the app has real data.

Run with DATABASE_URL set to the app role. Safe to re-run (skips existing rows by slug/sku).
"""
import asyncio
import sys
import uuid
from pathlib import Path

from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root for `api` imports

from api.core.rls import pin_tenant  # noqa: E402
from api.db.session import Session  # noqa: E402

TENANT_SLUG = "abc-store"
TENANT_NAME = "ABC Store"
AGENT_NAME = "shopping-agent"

PRODUCTS = [
    {"sku": "RS-BLK-42", "name": "Runner Pro 42", "category": "shoes/running", "price_minor": 349900},
    {"sku": "SR-WHT-40", "name": "Street Run 40", "category": "shoes/running", "price_minor": 279900},
    {"sku": "SK-3PK-01", "name": "Run Sock 3-pack", "category": "apparel/socks", "price_minor": 49900},
    {"sku": "TS-CLS-01", "name": "T-Shirt Classic", "category": "apparel", "price_minor": 79900},
    {"sku": "BT-SPT-01", "name": "Sport Bottle", "category": "gear/bottles", "price_minor": 99900},
    {"sku": "CN-MED-01", "name": "Canvas Messenger", "category": "bags", "price_minor": 189900},
]


async def main() -> None:
    async with Session() as s:
        row = (await s.execute(text("select id from tenants where slug = :s"), {"s": TENANT_SLUG})).first()
        if row:
            tenant_id = row[0]
            print(f"tenant exists: {tenant_id}")
        else:
            tenant_id = uuid.uuid4()
            await s.execute(
                text("insert into tenants (id, slug, name, currency, status) values (:i, :s, :n, 'INR', 'ACTIVE')"),
                {"i": tenant_id, "s": TENANT_SLUG, "n": TENANT_NAME},
            )
            print(f"created tenant: {tenant_id}")
        await s.commit()

    agent_id = uuid.uuid4()
    async with Session() as s:
        await pin_tenant(s, str(tenant_id))
        agent = (await s.execute(text("select id from agents where tenant_id = :t and name = :n"), {"t": tenant_id, "n": AGENT_NAME})).first()
        if agent:
            agent_id = agent[0]
            print(f"agent exists: {agent_id}")
        else:
            await s.execute(
                text("insert into agents (id, tenant_id, name, type, status) values (:i, :t, :n, 'SELL', 'ACTIVE')"),
                {"i": agent_id, "t": tenant_id, "n": AGENT_NAME},
            )
            print(f"created agent: {agent_id}")
        await s.commit()

    created = 0
    existing = 0
    async with Session() as s:
        await pin_tenant(s, str(tenant_id))
        for p in PRODUCTS:
            dup = (await s.execute(text("select id from products where tenant_id = :t and sku = :sku"), {"t": tenant_id, "sku": p["sku"]})).first()
            if dup:
                existing += 1
                continue
            pid = uuid.uuid4()
            await s.execute(
                text("insert into products (id, tenant_id, sku, name, category, price_minor, currency, status) values (:i, :t, :sku, :n, :c, :p, 'INR', 'ACTIVE')"),
                {"i": pid, "t": tenant_id, "sku": p["sku"], "n": p["name"], "c": p["category"], "p": p["price_minor"]},
            )
            created += 1
        await s.commit()

    print(f"products created={created}, existing={existing}, total={len(PRODUCTS)}")
    print(f"TENANT_ID={tenant_id}  AGENT_ID={agent_id}")


asyncio.run(main())
