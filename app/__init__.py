from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import init_db
from app.routes import chat, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="xia", lifespan=lifespan)
app.include_router(health.router)
app.include_router(chat.router)
