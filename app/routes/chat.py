import json
from pathlib import Path

import aiosqlite
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sse_starlette.sse import EventSourceResponse

from app.config import settings
from app.db import get_db
from app.llm import stream_chat

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).parent.parent / "templates")


@router.get("/", response_class=HTMLResponse)
async def index(request: Request, db=Depends(get_db)):
    rows = await (
        await db.execute(
            "SELECT id, title FROM conversation ORDER BY id DESC LIMIT 20"
        )
    ).fetchall()
    return templates.TemplateResponse(
        request=request,
        name="chat.html",
        context={"conversations": rows, "messages": [], "cid": None},
    )


@router.post("/conversation")
async def create_conv(db=Depends(get_db)):
    cur = await db.execute("INSERT INTO conversation(title) VALUES (?)", ("New chat",))
    await db.commit()
    return {"id": cur.lastrowid}


@router.get("/conversation/{cid}", response_class=HTMLResponse)
async def show_conv(cid: int, request: Request, db=Depends(get_db)):
    convs = await (
        await db.execute("SELECT id, title FROM conversation ORDER BY id DESC LIMIT 20")
    ).fetchall()
    msgs = await (
        await db.execute(
            "SELECT role, content FROM message WHERE conversation_id=? ORDER BY id",
            (cid,),
        )
    ).fetchall()
    return templates.TemplateResponse(
        request=request,
        name="chat.html",
        context={"conversations": convs, "messages": msgs, "cid": cid},
    )


@router.delete("/conversation/{cid}")
async def delete_conv(cid: int, db=Depends(get_db)):
    await db.execute("DELETE FROM message WHERE conversation_id=?", (cid,))
    await db.execute("DELETE FROM conversation WHERE id=?", (cid,))
    await db.commit()
    return JSONResponse({"ok": True})


@router.post("/chat/{cid}/stream")
async def chat_stream(cid: int, content: str = Form(...)):
    async with aiosqlite.connect(settings.db_path) as db:
        db.row_factory = aiosqlite.Row
        await db.execute(
            "INSERT INTO message(conversation_id, role, content) VALUES (?, 'user', ?)",
            (cid, content),
        )
        await db.commit()
        rows = await (
            await db.execute(
                "SELECT role, content FROM message WHERE conversation_id=? ORDER BY id",
                (cid,),
            )
        ).fetchall()
        history = [{"role": r["role"], "content": r["content"]} for r in rows]

    async def gen():
        buf = []
        async for tok in stream_chat(history):
            buf.append(tok)
            yield {"event": "token", "data": json.dumps({"t": tok})}
        full = "".join(buf)
        async with aiosqlite.connect(settings.db_path) as db:
            await db.execute(
                "INSERT INTO message(conversation_id, role, content) VALUES (?, 'assistant', ?)",
                (cid, full),
            )
            await db.commit()
        yield {"event": "done", "data": "1"}

    return EventSourceResponse(gen())
