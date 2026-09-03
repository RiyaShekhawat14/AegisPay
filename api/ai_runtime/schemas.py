from typing import Literal

from pydantic import BaseModel, Field


class IntentItem(BaseModel):
    product_id: str
    quantity: int = Field(ge=1)


class CommerceIntent(BaseModel):
    """The typed, validated proposal the AI hands to the control plane.

    The control plane re-validates all of this before any money moves.
    """

    agent_id: str
    kind: Literal["discover", "buy", "recommend"]
    summary: str
    items: list[IntentItem]


class RunIn(BaseModel):
    agent_id: str
    kind: Literal["discover", "buy", "recommend"] = "buy"
    summary: str = ""
    items: list[IntentItem]


class AgentAction(BaseModel):
    tool: str
    product_id: str
    quantity: int
    authorization_id: str | None = None


class AgentReply(BaseModel):
    kind: str
    summary: str
    catalog_count: int = 0
    actions: list[AgentAction]


class BuyerReport(BaseModel):
    order_id: str | None
    authorization_id: str | None
    authorization_status: str | None
    items: list[IntentItem]
