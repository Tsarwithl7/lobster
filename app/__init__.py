from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import init_db
from app.routes import chat, health, memory


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    try:
        yield
    finally:
        await cleanup_browser()


app = FastAPI(title="xia", lifespan=lifespan)
app.include_router(health.router)
app.include_router(chat.router)
app.include_router(memory.router)