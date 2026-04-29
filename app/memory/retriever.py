import sqlite_vec
import aiosqlite
import numpy as np

from app.config import settings
from app.memory.embedder import embed


def _rrf(ranked_lists: list[list[int]], k: int = 60) -> list[int]:
    scores: dict[int, float] = {}
    for ranked in ranked_lists:
        for rank, doc_id in enumerate(ranked):
            scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)
    return sorted(scores, key=lambda x: scores[x], reverse=True)


async def retrieve(query: str, n: int = 5) -> list[dict]:
    async with aiosqlite.connect(settings.db_path) as db:
        db.row_factory = aiosqlite.Row
        await db.enable_load_extension(True)
        await db.load_extension(sqlite_vec.loadable_path())
        await db.enable_load_extension(False)

        # BM25 路
        fts_rows = await (await db.execute(
            "SELECT rowid FROM chunk_fts WHERE chunk_fts MATCH ? ORDER BY rank LIMIT 20",
            (query,),
        )).fetchall()
        bm25_ids = [r["rowid"] for r in fts_rows]

        # Dense 路
        vec = embed([query])[0]
        vec_rows = await (await db.execute(
            "SELECT chunk_id FROM chunk_vec ORDER BY vec_distance_cosine(embedding, ?) LIMIT 20",
            (sqlite_vec.serialize_float32(vec.tolist()),),
        )).fetchall()
        dense_ids = [r["chunk_id"] for r in vec_rows]

        # RRF 融合
        fused_ids = _rrf([bm25_ids, dense_ids])[:n]

        if not fused_ids:
            return []

        placeholders = ",".join("?" * len(fused_ids))
        chunks = await (await db.execute(
            f"SELECT id, content FROM memory_chunk WHERE id IN ({placeholders})",
            fused_ids,
        )).fetchall()

        id_to_chunk = {r["id"]: r["content"] for r in chunks}
        return [{"id": i, "content": id_to_chunk[i]} for i in fused_ids if i in id_to_chunk]