import sqlite_vec
import numpy as np
import aiosqlite

from app.config import settings
from app.memory.embedder import embed
from app.memory.chunker import chunk_text


# Ingest text: chunk → embed → store in FTS + vector index for hybrid search
async def ingest(title: str, text: str, source: str = "", mime_type: str = "text/plain") -> int:
    chunks = chunk_text(text)
    vecs = embed(chunks)

    async with aiosqlite.connect(settings.db_path) as db:
        
        await db.enable_load_extension(True)
        await db.load_extension(sqlite_vec.loadable_path())
        await db.enable_load_extension(False)
        
        cur = await db.execute(
            "INSERT INTO document(title, source, mime_type) VALUES (?, ?, ?)",
            (title, source, mime_type),
        ) 
        doc_id = cur.lastrowid

        for i, (chunk, vec) in enumerate(zip(chunks, vecs)):
            cur = await db.execute(
                "INSERT INTO memory_chunk(document_id, content, chunk_index) VALUES (?, ?, ?)",
                (doc_id, chunk, i),
            )
            chunk_id = cur.lastrowid
            
            await db.execute(
                "INSERT INTO chunk_fts(rowid, content) VALUES (?, ?)",
                (chunk_id, chunk),
            )


            await db.execute(
                "INSERT INTO chunk_vec(chunk_id, embedding) VALUES (?, ?)",
                (chunk_id, sqlite_vec.serialize_float32(vec.tolist())),
            )
        
        
        await db.commit()
        return doc_id