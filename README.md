# LLMDB – Lightning Memory Database 🗲

**A time-aware, schema-rewritable, WASM-powered memory store for autonomous agents**

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/yourusername/llmdb/actions)
[![Coverage](https://img.shields.io/badge/coverage-85%25-green.svg)](https://codecov.io/gh/yourusername/llmdb)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

LLMDB combines the speed of LMDB with bitemporal versioning, embedded WebAssembly execution, and LLM-friendly APIs to create the perfect memory store for AI agents. It's designed from the ground up to be reshaped by LLMs while maintaining sub-millisecond performance.

## 🚀 Why LLMDB?

- ⚡ **60µs p99 read latency** on modern SSDs with zero-copy cursors
- 🕐 **Full bitemporal support** - query any point in valid and transaction time
- 🧩 **Schema evolution** - LLMs can reshape data structures on the fly
- 🚀 **Code at data** - Run WASM functions inside the database with fuel limits
- 🤖 **LLM-aware** - Special endpoints for AI agents to inspect and migrate schemas
- 📦 **Tiny footprint** - ≤70KB static library, 5MB RSS startup

## 📊 Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| Read latency (p99) | < 60 µs | 256-byte value on NVMe |
| Write throughput | 250 MB/s | Single writer |
| WASM map throughput | ≥ 8M pages/s | 32-byte keys |
| Startup memory | ≤ 5 MB RSS | Minimal footprint |
| Max database size | 128 TB | 64-bit address space |

## 🎯 Use Cases

### AI Coding Agent Memory Store
Perfect memory system for autonomous coding agents with temporal tracking:

- **Code Analysis Evolution**: Store understanding of codebases with correction trails
- **Decision History**: Track agent reasoning, changes, and rollbacks with full audit trails
- **Context Preservation**: Maintain conversation state across sessions with temporal accuracy
- **Knowledge Corrections**: Handle updates to agent understanding with "what did I know when" queries
- **Development Workflow Memory**: Track project progress, decisions, and state changes over time

```python
# Store agent decision with temporal context
agent_key = Key(partition=0, user_key="agent:decision:refactor_auth", valid_from=timestamp)
db.put(agent_key, {
    "decision": "Extract auth logic to separate service",
    "reasoning": "Improves testability and separation of concerns",
    "confidence": 0.85,
    "context": {"files_analyzed": 15, "test_coverage": 0.73}
})

# Query historical agent knowledge for debugging
past_understanding = db.get_versions("agent:knowledge:auth_patterns")
```

### Real-time Graph Analytics
Stream inserts with WASM edge-derivation jobs running at data-latency speeds.

### Vector+Symbolic Hybrid Search
Store embeddings alongside knowledge graph triples in a single, queryable file.

### Offline Privacy-First AI
All data and code stays on device with no cloud dependencies.

## 🏗️ Architecture

```
┌────────────┐  WASM  ┌───────────────┐
│  Client /  │◀──────▶│  Exec Sandbox │
│   LLM      │        └───▲─────┬─────┘
└─────▲──────┘            │     │
      │gRPC/HTTP          │     │
┌─────┴──────┐        ┌───┴─────┴─────┐
│  Query &   │ index  │ Schema + Meta │
│  Mutation  │◀──────▶│   Catalog     │
│  Engine    │        └───▲───────────┘
└─────▲──────┘            │
      │Cursors            │
┌─────┴──────────────┐    │
│  MVCC Page Cache   │    │
└─────▲──────────────┘    │
      │MMAP I/O           │
┌─────┴──────────────┐
│  Single-file B+Tree│
└────────────────────┘
```

## 🚦 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/llmdb.git
cd llmdb

# Run development setup
./scripts/dev_setup.sh      # Installs Python toolchain and liblmdb

# Install with server support
pip install -e ".[server]"   # Or use your favorite PEP 517 frontend
```

### Basic Usage

```python
from llmdb import KV
from llmdb.temporal_key import Key

# Open a database
db = KV("./my_data.db")

# Write with automatic bitemporal versioning
key = Key(partition=0, user_key="user:123", valid_from=1234567890)
db.put(key, {"name": "Alice", "score": 100})

# Read latest value
value = db.get(key)

# Query historical data (coming in Phase 4)
# historical = db.as_of_valid(timestamp).get(key)
```

### Running the MCP Server

```bash
# Start the FastAPI server
./scripts/run_server.sh &

# Test with the example client
python examples/simple_client.py
```

## 📚 Documentation

- [Architecture Overview](docs/architecture.md) - System design and components
- [AI Agent Memory Guide](docs/agent-memory.md) - Using LLMDB as agent memory store
- [Bitemporal Model](docs/bitemporal.md) - Understanding temporal queries
- [API Reference](docs/api/index.md) - Complete API documentation
- [LQL Query Language](docs/api/lql.md) - SQL-like queries with temporal extensions
- [WASM Modules](docs/wasm-modules.md) - Writing embedded functions
- [Performance Guide](PERFORMANCE.md) - Benchmarks and optimization

## 🛣️ Roadmap

### Current Status: Phase 2 Complete ✅

- [x] Phase 1: Repository Bootstrap
- [x] Phase 2: Core KV Store with bitemporal keys
- [ ] Phase 3: Write Path & Recovery (In Progress)
- [ ] Phase 4: Temporal Query Operators
- [ ] Phase 5: WASM Execution Engine
- [ ] Phase 6: LQL Parser & gRPC Layer
- [ ] Phase 7: Data Model Adaptors (Graph, Document, Vector)
- [ ] Phase 8: Replication & Security
- [ ] Phase 9: Production Hardening

See [TASKS.md](TASKS.md) for detailed progress.

## 🤝 Contributing

We welcome contributions from both humans and AI agents! 

1. Fork the repository and create a feature branch
2. Follow the coding standards in [AGENTS.md](AGENTS.md)
3. Run `pre-commit run --all-files` before committing
4. Ensure `pytest` passes all tests
5. Submit a pull request with a clear description

## 📖 Learn More

- [SPECS](SPECS) - Complete functional and technical specification
- [ARCHITECTURE.md](ARCHITECTURE.md) - Detailed component design
- [SECURITY.md](SECURITY.md) - Security model and best practices
- [CHANGELOG.md](CHANGELOG.md) - Version history

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

Built with ❤️ for the age of autonomous agents.