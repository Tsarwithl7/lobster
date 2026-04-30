import pytest
import aiosqlite

from app.config import settings
from app.db import init_db
from app.memory.chunker import chunk_text
from app.memory.store import ingest
from app.memory.retriever import retrieve


@pytest.fixture(autouse=True)
async def clean_db(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test.db")
    # settings 是单例，改一次所有模块都生效
    monkeypatch.setattr("app.config.settings.db_path", db_path)
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
        async with aiosqlite.connect(settings.db_path) as db:
            rows = await (await db.execute("SELECT count(*) FROM memory_chunk")).fetchone()
            assert rows[0] > 0


class TestRetriever:
    async def test_retrieve_finds_relevant(self):
        await ingest("AI文档", "人工智能是计算机科学的一个分支。\n\n机器学习是其核心技术。")
        results = await retrieve("人工智能", n=3)
        assert len(results) > 0
        assert any("人工智能" in r["content"] for r in results)

    async def test_retrieve_returns_dict(self):
        await ingest("测试", "Python是一种编程语言。")
        results = await retrieve("编程", n=3)
        for r in results:
            assert "id" in r
            assert "content" in r
