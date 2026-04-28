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
    model = settings.llm_model.removeprefix("ollama/")
    async with get_client().stream(
        "POST",
        f"{settings.ollama_base_url}/api/chat",
        json={"model": model, "messages": messages, "stream": True},
    ) as resp:
        async for line in resp.aiter_lines():
            if not line:
                continue
            data = json.loads(line)
            tok = data.get("message", {}).get("content", "")
            if tok:
                yield tok
