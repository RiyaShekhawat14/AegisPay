"""AegisPay Control Plane — the only component allowed to move money.

FastAPI modular monolith. All financial state, policy, risk, authorization, provider
interaction, audit and reconciliation live here. The isolated AI runtime calls this
service; it never touches the database or payment keys directly.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # TODO: initialise otel, engine, outbox/worker hooks here.
    yield


app = FastAPI(title="AegisPay Control Plane", version="0.1.0", lifespan=lifespan)
app.include_router(router)
