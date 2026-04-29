import pytest
import aiosqlite

from app.db import init_db
from app.memory.chunker import chunk_text
from app.memory.store import ingest


@pytest.fixture(autouse=True)
async def clean_db(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr("app.config.settings.db_path", db_path)
    monkeypatch.setattr("app.memory.store.settings.db_path", db_path)
    await init_db()
    yield
    

class TestChunker:
    def test_short_text_stays_one_chunk(self):
        chunks = chunk_text("第一段。\n\n第二段。")
        assert len(chunks) == 1

    def test_long_text_splits(self):
        chunks = chunk_text("x" * 1000, max_chars=512)
        assert len(chunks) > 1

    def test_no_empty_chunks(self):
        chunks = chunk_text("段落一。\n\n段落二。\n\n段落三。")
        assert all(len(c) > 0 for c in chunks)


class TestIngest:
    async def test_ingest_returns_doc_id(self):
        doc_id = await ingest("标题", "人工智能是一门学科。\n\n机器学习是其子领域。")
        assert isinstance(doc_id, int)
        assert doc_id > 0

    async def test_ingest_creates_chunks(self):
        await ingest("标题", "第一段内容。\n\n第二段内容。\n\n第三段内容。")
        async with aiosqlite.connect("data/xia.db") as db:
            rows = await (await db.execute("SELECT count(*) FROM memory_chunk")).fetchone()
            assert rows[0] > 0