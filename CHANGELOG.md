# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]
### Added
- Typed value envelopes for KV (`RawValue`, `JSONValue`).
- Bitemporal key packing utilities.
- Graph façade with `put_edge` and `out_edges` helpers.
- MCP CRUD verbs and dependency injection.
- `make typecheck` target and pytest coverage hook.
- `KV.delete` convenience method.
### Changed
- Pre-commit now runs pytest with coverage.
