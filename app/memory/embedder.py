from __future__ import annotations

import numpy as np
from sentence_transformers import SentenceTransformer

from app.config import settings

_model: SentenceTransformer | None = None


def get_embedder() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.embed_model, device=settings.embed_device)
    return _model


def embed(texts: list[str]) -> np.ndarray:
    return get_embedder().encode(texts, normalize_embeddings=True)