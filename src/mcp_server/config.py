"""Configuration helpers for the MCP server."""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    db_path: str = "./data"
    host: str = "127.0.0.1"
    port: int = 8000

