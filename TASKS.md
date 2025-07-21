# Development Tasks

## TODO Style Guide

- Use markdown checkboxes `- [ ]` for open items and `- [x]` when complete.
- Start each task with an imperative verb.
- Mention file paths or components in backticks where helpful.
- Group related tasks under phase headings to show order.
- Indent subtasks by two spaces underneath a parent item.
- Include acceptance criteria for each major task.
- Remove the entry or mark it done when merged.

## Phase 1 – Repository Bootstrap ✅

- [x] Expand `README.md` with summary and setup instructions.
- [x] Add `AGENTS.md` outlining rules for autonomous contributors.
- [x] Scaffold directories from `START.md` (src/, tests/, docs/, scripts/...)
- [x] Create `pyproject.toml` and `.pre-commit-config.yaml`.

## Phase 2 – Core Storage Engine ✅

- [x] Implement minimal `src/llmdb/kv.py` wrapping `lmdb.Environment` (read-only).
  - [x] Basic get/put operations
  - [x] Bitemporal key structure
  - [x] Type-tagged values
- [x] Write unit tests in `tests/unit/test_kv.py`.
- [x] Document the API in `docs/api/`.

## Phase 3 – Write Path & Recovery 🚧

- [ ] Add single-writer support with proper locking
  - [ ] Implement write lock acquisition in `KV.put()`
  - [ ] Add transaction ID generation
  - [ ] Update transaction time on writes
  
- [ ] Implement write-ahead log (WAL)
  - [ ] Create `src/llmdb/wal.py` module
  - [ ] Add WAL configuration options
  - [ ] Implement group commit for throughput
  - [ ] Add configurable fsync policies
  
- [ ] Add crash recovery mechanisms
  - [ ] Implement CRC validation for pages
  - [ ] Add recovery from last valid root
  - [ ] Truncate incomplete transactions
  - [ ] Create recovery CLI command: `llmdb recover`
  
- [ ] Provide crash-recovery tests
  - [ ] Simulate power loss scenarios
  - [ ] Test partial write recovery
  - [ ] Verify data integrity after recovery
  - [ ] Add chaos testing framework

**Acceptance Criteria:**
- Database survives simulated crashes without data loss
- Recovery completes in < 1 second
- All writes are durable after fsync
- Performance: 250 MB/s write throughput

## Phase 4 – Bitemporal Keys

- [ ] Enhance key schema with proper temporal support
  - [ ] Add valid time range queries
  - [ ] Implement transaction time tracking
  - [ ] Create temporal key indexes
  
- [ ] Implement temporal query operators
  - [ ] `AS OF VALID <timestamp>` - point-in-time queries
  - [ ] `AS OF TRANSACTION <tx_id>` - transaction time queries  
  - [ ] `BETWEEN VALID <start> AND <end>` - range queries
  - [ ] `VERSIONS BETWEEN` - all versions in range
  
- [ ] Add temporal predicates to query planner
  - [ ] Optimize temporal range scans
  - [ ] Push down temporal filters
  - [ ] Create temporal join operators
  
- [ ] Create comprehensive temporal tests
  - [ ] Test all temporal operators
  - [ ] Verify temporal consistency
  - [ ] Performance benchmarks for temporal queries

**Acceptance Criteria:**
- All temporal operators return correct results
- Temporal queries use indexes efficiently
- < 100µs overhead for temporal operations
- Complete SQL:2011 temporal compliance

## Phase 5 – WASM Execution

- [ ] Integrate Wasmtime runtime
  - [ ] Replace stub in `src/llmdb/wasm_exec.py`
  - [ ] Add Wasmtime Python bindings to dependencies
  - [ ] Implement WASI preview2 host functions
  - [ ] Create module cache for JIT compilation
  
- [ ] Implement resource limits
  - [ ] Fuel metering (25ms CPU limit)
  - [ ] Memory limits (64 MiB max)
  - [ ] Stack depth limits
  - [ ] Wall clock timeouts
  
- [ ] Add WASM function types
  - [ ] `map_pages(input, output)` - transform pages
  - [ ] `reduce_pages(pages) -> value` - aggregation
  - [ ] `tx_hook(before, after)` - transaction triggers
  - [ ] `custom_index(key, value) -> index_entries` - indexing
  
- [ ] Create module management
  - [ ] Store modules in `_meta/code/{hash}`
  - [ ] SHA-256 deduplication
  - [ ] Module versioning and dependencies
  - [ ] Hot reload without downtime
  
- [ ] Security hardening
  - [ ] Capability-based permissions
  - [ ] No filesystem access by default
  - [ ] Network isolation
  - [ ] Audit logging of WASM calls

**Acceptance Criteria:**
- WASM functions cannot escape sandbox
- Resource limits enforced accurately
- > 8M pages/second processing rate
- Zero security vulnerabilities in fuzzing

## Phase 6 – LQL Parser & RPC Layer

- [ ] Design LQL (LLMDB Query Language) syntax
  - [ ] SQL core compatibility
  - [ ] Temporal extensions
  - [ ] WASM execution hints
  - [ ] Schema evolution commands
  
- [ ] Build LQL parser
  - [ ] Create `src/llmdb/parser/` module
  - [ ] Lexer for LQL tokens
  - [ ] Recursive descent parser
  - [ ] AST representation
  - [ ] Query validation
  
- [ ] Implement query planner
  - [ ] Cost-based optimization
  - [ ] Temporal predicate pushdown
  - [ ] WASM function inlining
  - [ ] Join order optimization
  
- [ ] Add execution engine
  - [ ] Interpret query plans
  - [ ] Streaming result sets
  - [ ] Memory management
  - [ ] Progress reporting
  
- [ ] Expose gRPC API
  - [ ] Define protobuf schemas
  - [ ] Implement service handlers
  - [ ] Add streaming support
  - [ ] mTLS authentication
  
- [ ] Document protocol under `docs/protocol/`
  - [ ] Wire format specification
  - [ ] Error codes and handling
  - [ ] Client implementation guide

**Acceptance Criteria:**
- Parse all example queries from SPECS
- < 1ms query planning for simple queries
- Streaming results for large datasets
- gRPC performance > 100k QPS

## Phase 7 – Data Model Adaptors

- [ ] Complete document store façade
  - [ ] JSON/BSON projection from KV
  - [ ] Nested query support
  - [ ] Schema validation
  - [ ] Index on JSON paths
  
- [ ] Enhance property-graph façade
  - [ ] Efficient edge traversal
  - [ ] Graph algorithms in WASM
  - [ ] Shortest path queries
  - [ ] Community detection
  
- [ ] Implement vector index
  - [ ] f32[] block storage (4KB aligned)
  - [ ] SIMD dot product
  - [ ] Approximate nearest neighbor
  - [ ] Hybrid symbolic+vector search
  
- [ ] Add columnar storage
  - [ ] Column chunk organization
  - [ ] Compression (snappy/zstd)
  - [ ] Vectorized operations
  - [ ] Parquet compatibility

**Acceptance Criteria:**
- Each adaptor passes its test suite
- < 10% overhead vs native format
- Seamless switching between views
- LLM can discover and use adaptors

## Phase 8 – Replication & Security

- [ ] Implement RAFT consensus
  - [ ] Leader election
  - [ ] Log replication
  - [ ] Snapshot transfers
  - [ ] Configuration changes
  
- [ ] Add async replication
  - [ ] WAL shipping
  - [ ] Conflict resolution
  - [ ] Read replicas
  - [ ] Geographic distribution
  
- [ ] Security hardening
  - [ ] mTLS everywhere
  - [ ] SPIFFE workload identity
  - [ ] Role-based access control
  - [ ] Audit logging
  
- [ ] Resource quotas
  - [ ] Per-tenant limits
  - [ ] Rate limiting
  - [ ] Storage quotas
  - [ ] Compute budgets

**Acceptance Criteria:**
- 3-node cluster survives 1 failure
- < 10ms replication lag
- Zero auth bypasses in pen testing
- Multi-tenant isolation verified

## Phase 9 – MCP Demo & Production

- [x] Build FastAPI server in `src/mcp_server`
  - [x] Basic REST endpoints
  - [x] KV operations
  - [x] Health checks
  
- [ ] Complete MCP implementation
  - [ ] Full REST API surface
  - [ ] WebSocket support
  - [ ] Schema discovery endpoints
  - [ ] WASM module uploads
  
- [ ] Production features
  - [ ] Prometheus metrics
  - [ ] Distributed tracing
  - [ ] Health checks
  - [ ] Graceful shutdown
  
- [ ] Operational tooling
  - [ ] CLI: `llmdb` command
  - [ ] Backup/restore tools
  - [ ] Migration utilities
  - [ ] Performance profiler
  
- [ ] Integration tests
  - [ ] End-to-end scenarios
  - [ ] Load testing
  - [ ] Fault injection
  - [ ] Multi-version compatibility
  
- [ ] Documentation
  - [ ] Operations guide
  - [ ] Troubleshooting
  - [ ] Performance tuning
  - [ ] Migration playbook

**Acceptance Criteria:**
- 99.9% uptime in 30-day test
- < 60µs p99 latency maintained
- All operational procedures documented
- Zero data loss in chaos tests

## Infrastructure & Quality

- [ ] CI/CD Pipeline
  - [ ] GitHub Actions workflow
  - [ ] Automated testing
  - [ ] Performance regression detection
  - [ ] Security scanning
  
- [ ] Development Environment
  - [ ] Docker compose setup
  - [ ] Dev container configuration
  - [ ] Local k8s testing
  - [ ] Benchmark suite
  
- [ ] Documentation
  - [ ] API reference generation
  - [ ] Architecture diagrams
  - [ ] Tutorial series
  - [ ] Video walkthroughs

## Stretch Goals

- [ ] GPU-accelerated vector operations
- [ ] Homomorphic encryption support
- [ ] GraphQL API
- [ ] Jupyter notebook integration
- [ ] Cloud-native operators (k8s)
- [ ] Multi-language SDKs

---

**Note:** Tasks are ordered by dependency. Each phase builds on the previous ones. Acceptance criteria ensure we meet the ambitious goals set in SPECS.