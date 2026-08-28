"""Isolated AI Runtime.

This service is the ONLY thing that talks to the LLM. It has NO database credentials, NO
Razorpay secrets, and NO money tools. It compiles agent output into a validated
CommerceIntent and calls the control plane. Security here is a process/permission
boundary, not a language split.
"""
from fastapi import FastAPI

from ai_runtime.schemas import CommerceIntent

app = FastAPI(title="AegisPay AI Runtime", version="0.1.0")


@app.post("/internal/intent/compile", response_model=CommerceIntent)
async def compile_intent() -> CommerceIntent:
    # TODO: run the LangGraph proposal graph, validate the structured output,
    # and return a typed CommerceIntent for the control plane to gate.
    raise NotImplementedError("intent compilation wired in a later milestone")
