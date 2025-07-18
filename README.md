# LLMDB \U0001F39B\FE0F

**Tiny, time-aware LMDB wrapper and demo MCP server.**

LLMDB exposes Lightning MDB through a Python API and showcases a FastAPI-based MCP server. The project is bootstrapped so both humans and autonomous agents can contribute safely.

## Features

- Zero-copy LMDB core
- Bitemporal keys for history tracking
- Pluggable façades (KV, document, graph)
- Async MCP server example

## Installation

```bash
git clone https://example.com/llmdb.git
cd llmdb
./scripts/dev_setup.sh      # install Python toolchain and liblmdb
pip install -e .[server]    # or use your favourite PEP 517 frontend
```

## Running the demo

```bash
./scripts/run_server.sh &
python examples/simple_client.py
```

See `docs/setup/quick_start.md` for details.

## Contributing

1. Fork the repo and create a feature branch.
2. Run `pre-commit run --all-files` before committing.
3. Ensure `pytest -q` succeeds.

Happy hacking!
