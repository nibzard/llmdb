"""Ping verb."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/ping")
async def ping() -> dict[str, str]:
    return {"pong": "ok"}

