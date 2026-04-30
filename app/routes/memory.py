from pathlib import Path
import tempfile

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request

from app.db import get_db
from app.memory.store import ingest
from app.memory.parser import parse
from app.memory.browser import fetch_page

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).parent.parent / "templates")


@router.get("/memory", response_class=HTMLResponse)
async def memory_page(request: Request, db=Depends(get_db)):
    # 查所有已摄入的文档，显示在页面上
    docs = await (
        await db.execute("SELECT id, title, source, created_at FROM document ORDER BY id DESC")
    ).fetchall()
    return templates.TemplateResponse(
        request=request,
        name="memory.html",
        context={"docs": docs},
    )


@router.post("/memory/upload")
async def upload_file(file: UploadFile = File(...)):
    # 把上传文件写到临时目录，解析后摄入记忆库
    suffix = Path(file.filename).suffix
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    text = parse(tmp_path)
    doc_id = await ingest(title=file.filename, text=text, source=file.filename, mime_type=file.content_type)
    Path(tmp_path).unlink()  # 解析完删掉临时文件
    return {"doc_id": doc_id, "title": file.filename}


@router.post("/memory/fetch-url")
async def fetch_url(url: str = Form(...)):
    # 用 Playwright 抓网页正文，摄入记忆库
    text = await fetch_page(url)
    doc_id = await ingest(title=url, text=text, source=url, mime_type="text/html")
    return {"doc_id": doc_id, "title": url}