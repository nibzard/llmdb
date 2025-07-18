"""FastAPI-based MCP server."""

from __future__ import annotations

from fastapi import FastAPI

from .handlers import ping
from .config import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    app = FastAPI()
    app.include_router(ping.router)
    return app

