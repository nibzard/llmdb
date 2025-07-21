# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LLMDB is a time-aware, schema-rewritable, WASM-powered memory store for autonomous agents. It combines LMDB's speed with bitemporal versioning, embedded WebAssembly execution, and LLM-friendly APIs.

## Development Commands

- `make test`: Run ruff formatter, black, mypy type checker, and pytest unit tests  
- `make typecheck`: Run mypy static type analysis only
- `make bench`: Run performance benchmarks
- `./scripts/dev_setup.sh`: Install dependencies and setup development environment
- `./scripts/run_server.sh`: Start the FastAPI MCP server with auto-reload
- `pip install -e ".[server]"`: Install package in development mode with server dependencies
- `ruff --fix .`: Auto-fix code style issues (required before commits)
- `pytest -q`: Run tests quietly
- `pytest -q tests/benchmarks`: Run benchmark suite only

## Architecture

### Core Components

- **Storage Engine** (`src/llmdb/kv/`): Thin LMDB wrapper with bitemporal keys and typed values
- **Temporal System** (`src/llmdb/temporal.py`): Clock abstraction and time management  
- **Graph Interface** (`src/llmdb/graph.py`): Property graph façade over KV store
- **WASM Executor** (`src/llmdb/wasm_exec.py`): Sandboxed WebAssembly runtime
- **MCP Server** (`src/mcp_server/`): FastAPI-based HTTP interface

### Key Data Structures

- **Bitemporal Keys**: `[partition_id: u32][user_key: bytes][valid_from: u64][tx_id: u64]`
- **Type-tagged Values**: 1-byte prefix indicating RawBytes, JSON, MsgPack, etc.
- **Clock Injection**: Use `Clock` interface instead of direct wall time access

### Multi-layered Architecture

```
API Layer (REST/gRPC) → Query Engine → Data Model Adaptors → 
Core Storage (MVCC/Pages) → WASM Layer → Physical Storage (LMDB)
```

## Code Standards (from AGENTS.md)

- **Language**: Python 3.12+ with LMDB >= 0.4
- **Formatting**: Black with Ruff defaults, 120-column soft wrap
- **Type Hints**: Mandatory in `llmdb/` modules
- **Coverage**: Maintain ≥90% test coverage for new code
- **Dependencies**: Avoid heavy deps (>5 MiB wheels) unless in extras

## Testing

Tests are in `tests/unit/` and `tests/integration/`. Key test files:
- `test_kv.py`: Core key-value storage tests
- `test_temporal.py`: Time-based functionality tests  
- `test_graph.py`: Graph interface tests
- `test_mcp_roundtrip.py`: End-to-end MCP server tests

## Project Structure

- `src/llmdb/`: Core library modules
- `src/mcp_server/`: HTTP server implementation with handlers in `handlers/`  
- `examples/`: Usage examples and demos
- `docs/`: Architecture and API documentation
- `AGENTS.md`: Detailed guidelines for autonomous coding agents