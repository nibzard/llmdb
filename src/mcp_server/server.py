"""FastAPI-based MCP server."""

from __future__ import annotations

from fastapi import FastAPI

from .handlers import ping
from .handlers import kv as kv_router
from .config import Settings
from llmdb.kv import KV
from llmdb.temporal import Clock, MonotonicClock


def create_app(
    settings: Settings | None = None,
    kv: KV | None = None,
    clock: Clock | None = None,
) -> FastAPI:
    settings = settings or Settings()
    kv = kv or KV(settings.db_path, clock=clock or MonotonicClock())
    app = FastAPI()
    app.dependency_overrides[KV] = lambda: kv
    app.include_router(ping.router)
    app.include_router(kv_router.router)
    return app
