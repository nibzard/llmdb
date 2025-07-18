# Development Tasks

## TODO Style Guide

- Use markdown checkboxes `- [ ]` for open items and `- [x]` when complete.
- Start each task with an imperative verb.
- Mention file paths or components in backticks where helpful.
- Group related tasks under phase headings to show order.
- Indent subtasks by two spaces underneath a parent item.
- Remove the entry or mark it done when merged.

## Phase 1 – Repository Bootstrap

- [x] Expand `README.md` with summary and setup instructions.
- [x] Add `AGENTS.md` outlining rules for autonomous contributors.
- [x] Scaffold directories from `START.md` (src/, tests/, docs/, scripts/...)
- [x] Create `pyproject.toml` and `.pre-commit-config.yaml`.

## Phase 2 – Core Storage Engine

- [ ] Implement minimal `src/llmdb/kv.py` wrapping `lmdb.Environment` (read-only).
- [ ] Write unit tests in `tests/unit/test_kv.py`.
- [ ] Document the API in `docs/api/`.

## Phase 3 – Write Path & Recovery

- [ ] Add single-writer support and write-ahead log.
- [ ] Provide crash-recovery tests.

## Phase 4 – Bitemporal Keys

- [ ] Add key schema with valid and transaction time.
- [ ] Support range queries with temporal predicates.

## Phase 5 – WASM Execution

- [ ] Integrate Wasmtime via `src/llmdb/wasm_exec.py`.
- [ ] Enforce fuel and memory limits; unit test sandboxing.

## Phase 6 – LQL Parser & RPC Layer

- [ ] Build LQL parser covering SQL core plus extensions.
- [ ] Expose gRPC API for queries.
- [ ] Document protocol under `docs/protocol/`.

## Phase 7 – Data Model Adaptors

- [ ] Implement document store and property-graph façades.
- [ ] Add vector index plugin.

## Phase 8 – Replication & Security

- [ ] Introduce RAFT-style replication.
- [ ] Harden security: mTLS, auth, resource quotas.

## Phase 9 – MCP Demo

- [ ] Build FastAPI server in `src/mcp_server`.
- [ ] Provide verbs (`ping`, CRUD) and integration test.
- [ ] Supply example client demonstrating usage.
