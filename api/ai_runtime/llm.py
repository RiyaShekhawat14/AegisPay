"""Ollama client for the AI runtime.

The AI *reasons* here (natural-language recommendation) but can never move money — it only
produces a suggestion. A failure to reach Ollama is graceful: the caller falls back to the
deterministic plan.
"""

from __future__ import annotations

import httpx


async def recommend(prompt: str, *, base_url: str, model: str) -> str:
    """Ask Ollama for a short recommendation. Returns '' on any failure (graceful)."""
    if not base_url:
        return ""
    try:
        r = await httpx.AsyncClient(timeout=30).post(
            f"{base_url.rstrip('/')}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"num_predict": 120},
            },
        )
        r.raise_for_status()
        return (r.json().get("response") or "").strip()
    except Exception:  # noqa: BLE001 - graceful fallback if Ollama is unreachable
        return ""
