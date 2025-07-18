# Instructions for Autonomous Coding Agents \U0001F916

Welcome, synthetic contributor! Follow these guidelines to collaborate smoothly.

## 1. Repository Context

- **Language stack**: Python 3.12 and LMDB >= 0.4
- Source lives under `src/`
- Tests must pass `pytest -q` and type-check with `mypy .`

## 2. What You MAY Do

| Task | Example |
|------|---------|
| Create modules | `src/llmdb/vector.py` |
| Add MCP verbs  | `src/mcp_server/handlers/` |
| Improve docs   | Markdown in `docs/` or docstrings |

## 3. What You MUST Do

1. **Run `ruff --fix .`** before committing.
2. **Add or adjust unit tests** so new logic has at least 90% coverage.
3. **Keep the public API stable** – bump `__all_changes__` in `CHANGELOG.md` when changing `llmdb.*`.
4. **Avoid nondeterminism** – inject clocks instead of using wall time directly.

## 4. Prohibited Actions

- Writing secrets, API keys or personal data.
- Changing CI config in `.github/workflows/` without approval.
- Introducing heavy dependencies (>5&nbsp;MiB wheels) unless declared in extras.

## 5. CI Commands Reference

| Command | Purpose |
|--------|---------|
| `make test` | Run lint, type checks and unit tests |
| `make typecheck` | Run mypy for static analysis |
| `make bench` | Run micro-benchmarks |

## 6. Code Style

- Black formatting with Ruff defaults
- 120-column soft wrap
- Type hints are mandatory in `llmdb/`

## 7. Prompt Template

> "Implement `<feature>` in `src/llmdb/...` following project conventions; update or create tests in `tests/` to maintain coverage ≥ 90 %. Do not modify `.github/workflows`."

Happy committing! 🤖
