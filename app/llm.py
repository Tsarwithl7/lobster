import json
from typing import AsyncIterator

import httpx

from app.config import settings

_client: httpx.AsyncClient | None = None


def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=120)
    return _client


async def stream_chat(messages: list[dict]) -> AsyncIterator[str]:
    async with get_client().stream(
        "POST",
        f"{settings.vllm_base_url}/v1/chat/completions",
        json={
            "model": settings.llm_model,
            "messages": messages,
            "stream": True,
        },
    ) as resp:
        async for line in resp.aiter_lines():
            if not line.startswith("data: "):
                continue
            payload = line[6:]
            if payload == "[DONE]":
                break
            data = json.loads(payload)
            tok = data["choices"][0]["delta"].get("content", "")
            if tok:
                yield tok