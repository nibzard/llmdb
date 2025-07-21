# LLMDB Architecture

This document describes the detailed architecture of LLMDB, a time-aware, schema-rewritable, WASM-powered memory store for autonomous agents.

## Table of Contents

1. [Overview](#overview)
2. [Core Components](#core-components)
3. [Data Flow](#data-flow)
4. [Key Design Decisions](#key-design-decisions)
5. [Component Details](#component-details)
6. [Performance Considerations](#performance-considerations)
7. [Future Extensions](#future-extensions)

## Overview

LLMDB is built as a layered system with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────┐
│                    API Layer                            │
│  REST/HTTP  │  gRPC  │  CLI  │  Embedded (FFI)        │
├─────────────────────────────────────────────────────────┤
│                 Query & Mutation Engine                 │
│  LQL Parser │ Query Planner │ Execution Engine        │
├─────────────────────────────────────────────────────────┤
│                  Data Model Adaptors                    │
│  KV Store │ Document │ Graph │ Vector │ Columnar      │
├─────────────────────────────────────────────────────────┤
│                    Core Storage                         │
│  Bitemporal Keys │ MVCC │ Page Cache │ WAL           │
├─────────────────────────────────────────────────────────┤
│                  WASM Execution Layer                   │
│  Wasmtime Runtime │ Fuel Limits │ Sandboxing         │
├─────────────────────────────────────────────────────────┤
│              Physical Storage (LMDB)                    │
│         Single-file B+Tree │ MMAP I/O                  │
└─────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Storage Engine (`src/llmdb/kv/`)

The foundation is a thin wrapper around LMDB that adds:

- **Bitemporal key structure**: Every key includes partition, user key, valid time, and transaction time
- **Type-tagged values**: 1-byte prefix indicating RawBytes, JSON, MsgPack, Protobuf, EdgeRecord, or VectorBlock
- **Zero-copy cursors**: Direct memory-mapped access for reads
- **Single writer, multiple readers**: MVCC-style isolation

**Key Files:**
- `kv/__init__.py`: Main KV interface
- `temporal_key.py`: Bitemporal key encoding/decoding
- `_codec.py`: Value type encoding/decoding

### 2. Temporal Subsystem (`src/llmdb/temporal.py`)

Manages time across the system:

- **Clock abstraction**: Pluggable time sources (monotonic, wall clock, logical)
- **Valid time**: When a fact is true in the real world
- **Transaction time**: When a fact was recorded in the database
- **Temporal queries**: AS OF, BETWEEN operators for time travel

### 3. WASM Execution Engine (`src/llmdb/wasm_exec.py`)

Runs user code at data latency:

- **Wasmtime integration**: WASI-preview2 sandbox
- **Resource limits**: 64 MiB memory, 25ms CPU time, fuel metering
- **Function types**: map_pages, reduce_pages, tx_hook, custom_index
- **Module storage**: WASM blobs stored in `_meta/code/{hash}`

### 4. Query Engine (Future)

Processes LQL (LLMDB Query Language):

- **SQL-like syntax**: With temporal extensions
- **WASM hints**: `EMBEDDED WASM` clause for in-query computation
- **Query planner**: Optimizes temporal range scans
- **Execution engine**: Pushes predicates to storage layer

### 5. Data Model Adaptors

Provides different views of the same underlying KV store:

#### Document Store Façade
- Projects KV pairs as JSON/BSON documents
- Schema stored in `_meta/schema/{collection}/{version}`
- Supports nested queries and projections

#### Property Graph Façade (`src/llmdb/graph.py`)
- Nodes: `(nodeId) → properties`
- Edges: `(edgeId) → {from, to, props}`
- Efficient traversals using edge indexes
- WASM-powered graph algorithms

#### Vector Index Façade
- Fixed-size f32[] blocks (4 KiB aligned)
- SIMD-friendly layout for dot products
- Hybrid search with symbolic predicates

#### Columnar Façade
- Groups pages into column chunks
- Compression-friendly layout
- Analytics workloads

### 6. Schema & Migration System

LLM-friendly schema evolution:

- **Schema storage**: `_meta/schema/{name}/{version}`
- **Migration records**: Predicate + WASM transform
- **Lazy migration**: Background rewrite on read
- **Zero-downtime**: Old schemas remain readable

### 7. API Layer (`src/mcp_server/`)

Multiple access methods:

- **REST API**: Simple JSON interface for LLMs
- **gRPC**: High-performance binary protocol
- **CLI**: Interactive REPL and management commands
- **Embedded**: Direct FFI for in-process use

## Data Flow

### Write Path

1. Client sends write request (REST/gRPC/FFI)
2. Query engine validates and plans operation
3. Acquires write lock (single writer)
4. Generates transaction timestamp
5. Encodes bitemporal key and typed value
6. Writes to WAL (if enabled)
7. Updates B+Tree pages
8. Triggers any tx_hook WASM functions
9. Releases lock and returns

### Read Path

1. Client sends read request
2. Query engine parses temporal predicates
3. Acquires read transaction (snapshot)
4. Scans B+Tree with temporal key ranges
5. Applies any WASM map functions
6. Projects through data model adaptor
7. Returns results

### WASM Execution Path

1. Query includes `EMBEDDED WASM` hint
2. Engine loads module from `_meta/code/`
3. Validates fuel budget and capabilities
4. Instantiates Wasmtime sandbox
5. Passes page slices to WASM function
6. Monitors resource usage
7. Returns results or aborts on limit

## Key Design Decisions

### 1. Bitemporal by Default

Every write automatically captures both valid and transaction time. This enables:
- Complete audit trails
- Point-in-time queries
- Temporal joins
- Compliance with regulations

### 2. Single File Storage

Following LMDB's design:
- Simplifies deployment (one file to backup)
- Enables zero-copy reads via mmap
- Atomic durability with copy-on-write

### 3. WASM for User Code

Instead of stored procedures:
- Language agnostic (compile from any language)
- Sandboxed security
- Deterministic execution
- Resource limits enforced

### 4. Schema as Data

Schemas are just another type of data:
- LLMs can inspect current schemas
- Propose migrations programmatically
- No special DDL language needed

### 5. Type-Tagged Values

1-byte prefix enables:
- Efficient dispatch to codecs
- Mixed-type storage in same database
- Future extensibility

## Component Details

### Bitemporal Key Encoding

```
[partition_id: u32][user_key: bytes][valid_from: u64][tx_id: u64]
```

- **partition_id**: Enables sharding across nodes
- **user_key**: Application-defined identifier
- **valid_from**: Microseconds since epoch (valid time)
- **tx_id**: Monotonic transaction counter

### Value Type Tags

```python
class ValueType(Enum):
    RAW_BYTES = 0x00
    JSON = 0x01
    MSGPACK = 0x02
    PROTOBUF = 0x03
    EDGE_RECORD = 0x10
    VECTOR_BLOCK = 0x20
```

### WASM Module Interface

```rust
// Example WASM module in Rust
#[no_mangle]
pub extern "C" fn map_pages(
    input_ptr: *const u8,
    input_len: usize,
    output_ptr: *mut u8,
    output_capacity: usize,
) -> usize {
    // Transform pages
}
```

### Page Layout

Following LMDB's design:
- 4KB pages (configurable)
- B+Tree structure
- Copy-on-write updates
- Free list for space reuse

## Performance Considerations

### 1. Zero-Copy Reads

- Direct mmap access avoids serialization
- Page cache managed by OS
- No allocation in hot path

### 2. Temporal Key Locality

- Keys with same user_key but different times are adjacent
- Enables efficient time-range scans
- Natural compression of historical data

### 3. WASM JIT Compilation

- Wasmtime compiles to native code
- Amortized over many invocations
- Near-native performance for hot functions

### 4. Write Batching

- Optional WAL for write batching
- Group commit for throughput
- Configurable fsync policy

### 5. Cache-Aware Data Structures

- 64-byte aligned structures
- SIMD-friendly vector blocks
- Minimize cache line bouncing

## Future Extensions

### 1. Distributed Features

- RAFT consensus for replication
- Consistent hashing for sharding
- Cross-region replication

### 2. Advanced Temporal

- Tri-temporal (add decision time)
- Temporal constraints and triggers
- Time-series specific optimizations

### 3. GPU Acceleration

- GPU-native vector operations
- CUDA/ROCm WASM extensions
- Hybrid CPU/GPU query execution

### 4. Privacy Features

- Differential privacy for queries
- Homomorphic encryption support
- Secure multi-party computation

### 5. Cloud Native

- S3-compatible object storage backend
- Kubernetes operators
- Serverless query execution

## AI Agent Memory Patterns

LLMDB's bitemporal architecture enables sophisticated memory patterns for AI coding agents:

### Agent Knowledge Storage Patterns

#### 1. Code Analysis Evolution
```python
# Store evolving understanding of code structure
analysis_key = Key(
    partition=0,
    user_key=f"agent:analysis:{file_hash}",
    valid_from=analysis_timestamp
)
db.put(analysis_key, {
    "file_path": "src/auth/login.py", 
    "complexity_score": 8.5,
    "dependencies": ["bcrypt", "jwt"],
    "patterns": ["factory", "decorator"],
    "issues": ["missing_error_handling", "hardcoded_timeout"],
    "confidence": 0.87
})

# Track corrections to analysis
corrected_analysis = {
    "complexity_score": 7.2,  # Corrected after deeper analysis
    "patterns": ["factory", "decorator", "singleton"],
    "correction_reason": "Found hidden singleton pattern in config class"
}
db.put(analysis_key, corrected_analysis)  # New transaction time, same valid time
```

#### 2. Decision History with Reasoning
```python
# Store agent decisions with complete context
decision_key = Key(
    partition=0,
    user_key=f"agent:decision:refactor_{task_id}",
    valid_from=decision_timestamp
)
db.put(decision_key, {
    "decision": "Extract database layer to separate module",
    "reasoning": [
        "Reduces coupling between business logic and persistence",
        "Enables easier testing with mock databases",
        "Follows single responsibility principle"
    ],
    "alternatives_considered": [
        "Keep current structure with better abstractions",
        "Use dependency injection without extraction"
    ],
    "confidence": 0.75,
    "context": {
        "files_analyzed": 23,
        "current_test_coverage": 0.68,
        "estimated_effort_hours": 16
    }
})
```

#### 3. Conversation Context Management
```python
# Maintain conversation state across sessions
context_key = Key(
    partition=0,
    user_key=f"agent:context:{session_id}",
    valid_from=message_timestamp
)
db.put(context_key, {
    "current_task": "implementing_auth_service",
    "conversation_summary": "Discussing JWT token validation patterns",
    "relevant_files": ["src/auth/", "tests/auth/", "config/jwt.py"],
    "user_preferences": {
        "coding_style": "functional_first",
        "test_framework": "pytest",
        "documentation_level": "detailed"
    },
    "pending_questions": [
        "Should we use RS256 or HS256 for JWT signing?",
        "Preference for database migration strategy?"
    ]
})
```

### Temporal Query Patterns for Agents

#### 1. Knowledge Evolution Tracking
```python
# Track how agent understanding evolved
def get_knowledge_evolution(topic: str) -> List[Dict]:
    """Get complete evolution of agent knowledge on a topic"""
    key_prefix = f"agent:knowledge:{topic}"
    versions = db.get_versions(key_prefix)
    
    evolution = []
    for valid_time, tx_id, knowledge in versions:
        evolution.append({
            "timestamp": valid_time,
            "transaction": tx_id,
            "knowledge": knowledge,
            "confidence_change": knowledge.get("confidence", 0) - 
                               (evolution[-1]["knowledge"].get("confidence", 0) if evolution else 0)
        })
    return evolution
```

#### 2. Decision Rollback and Replay
```python
# Implement agent decision rollback
def rollback_to_decision(decision_id: str, rollback_timestamp: int):
    """Rollback agent state to a specific decision point"""
    # Query what the agent knew at that time
    historical_context = db.as_of_transaction(rollback_timestamp)
    
    # Restore agent knowledge state
    agent_state = historical_context.get(f"agent:context:{decision_id}")
    
    # Mark current decisions as superseded
    current_key = Key(
        partition=0,
        user_key=f"agent:decision:{decision_id}:superseded",
        valid_from=get_current_timestamp()
    )
    db.put(current_key, {
        "status": "rolled_back",
        "reason": "user_requested_different_approach",
        "rollback_timestamp": rollback_timestamp
    })
    
    return agent_state
```

#### 3. Context-Aware Code Suggestions
```python
# Use temporal data for better code suggestions
def get_contextual_suggestions(file_path: str) -> Dict:
    """Get code suggestions based on historical analysis"""
    
    # Get latest analysis
    current_analysis = db.get(f"agent:analysis:{hash(file_path)}")
    
    # Get previous issues that were resolved
    resolved_issues = []
    for valid_time, tx_id, analysis in db.get_versions(f"agent:analysis:{hash(file_path)}"):
        if "issues_resolved" in analysis:
            resolved_issues.extend(analysis["issues_resolved"])
    
    # Generate suggestions avoiding past issues
    suggestions = {
        "refactoring_opportunities": current_analysis.get("refactoring_ops", []),
        "avoid_patterns": [issue["pattern"] for issue in resolved_issues],
        "recommended_tests": generate_test_suggestions(current_analysis),
        "confidence": current_analysis.get("confidence", 0.5)
    }
    
    return suggestions
```

### Agent Memory Schema Patterns

#### Standard Agent Namespaces
- `agent:context:{session_id}` - Conversation and task context
- `agent:analysis:{file_hash}` - Code analysis results
- `agent:decision:{task_id}` - Decisions and reasoning
- `agent:knowledge:{domain}` - Domain-specific knowledge
- `agent:progress:{project_id}` - Project progress tracking
- `agent:preferences:{user_id}` - User preferences and patterns
- `agent:errors:{error_id}` - Error analysis and resolution patterns

#### Temporal Metadata
Each agent record includes temporal context:
```python
{
    "content": {...},  # The actual data
    "confidence": 0.85,  # Agent confidence in the data
    "source": "static_analysis",  # How the data was obtained
    "dependencies": ["file1.py", "file2.py"],  # What this data depends on
    "correction_reason": None,  # Why this corrects previous data
    "expires_at": None  # Optional expiration for cached analysis
}
```

## Conclusion

LLMDB's architecture is designed to be:

1. **Simple**: Single-file storage, minimal dependencies
2. **Fast**: Zero-copy reads, native-speed WASM
3. **Flexible**: Multiple data models, LLM-driven evolution
4. **Temporal**: Complete history tracking built-in
5. **Secure**: Sandboxed execution, capability-based access

This architecture enables autonomous agents to have a fast, evolvable memory store that maintains complete history while supporting complex computations at data latency. The bitemporal model is particularly powerful for AI agents, providing both decision audit trails and knowledge evolution tracking essential for reliable autonomous behavior.