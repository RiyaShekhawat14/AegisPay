"""Isolated AI Runtime.

This service is the ONLY thing that talks to the LLM. It has NO database credentials, NO
Razorpay secrets, and NO money tools. It compiles agent output into a validated
CommerceIntent and requests actions via the control plane. Security is a process/permission
boundary, not a language split.
"""

from typing import Annotated

from fastapi import Depends, FastAPI

from ai_runtime.agent import run_agent
from ai_runtime.buyer import run_buyer
from ai_runtime.schemas import AgentReply, BuyerReport, CommerceIntent, RunIn
from ai_runtime.tools.client import ControlPlaneClient
from api.core.config import get_settings

app = FastAPI(title="AegisPay AI Runtime", version="0.1.0")


def get_client() -> ControlPlaneClient:
    s = get_settings()
    return ControlPlaneClient(base_url=s.control_plane_url, token=s.control_plane_token)


Client = Annotated[ControlPlaneClient, Depends(get_client)]


@app.post("/agent/run", response_model=AgentReply)
async def agent_run(body: RunIn, client: Client) -> AgentReply:
    intent = CommerceIntent(
        agent_id=body.agent_id, kind=body.kind, summary=body.summary, items=body.items
    )
    return AgentReply(**await run_agent(intent, client))


@app.post("/agent/buy", response_model=BuyerReport)
async def agent_buy(body: RunIn, client: Client) -> BuyerReport:
    intent = CommerceIntent(
        agent_id=body.agent_id, kind="buy", summary=body.summary, items=body.items
    )
    result = await run_buyer(intent, client)
    result.pop("_catalog_count", None)
    return BuyerReport(**result)
