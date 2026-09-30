"""FastAPI application entrypoint."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import __version__
from .api.routes import router
from .config import settings
from .db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # v1 creates tables on startup; production would run migrations instead.
    init_db()
    yield


app = FastAPI(title=settings.app_name, version=__version__, lifespan=lifespan)

# The Next.js frontend proxies to us server-side, but permissive CORS also lets
# the browser call the API directly during local development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/", tags=["ops"])
def root() -> dict:
    return {"app": settings.app_name, "version": __version__, "docs": "/docs"}
