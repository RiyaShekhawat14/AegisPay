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
