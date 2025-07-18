"""Stub for future WASM execution hooks."""

from __future__ import annotations

__all__ = ["WasmExecutor"]


class WasmExecutor:
    """Placeholder for WASM execution sandbox."""

    def execute(self, code: bytes) -> None:
        raise NotImplementedError("WASM execution not yet implemented")
