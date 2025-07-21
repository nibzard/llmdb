# LLMDB Performance Guide

This document outlines performance targets, benchmarking methodology, and optimization strategies for LLMDB.

## Performance Targets

Based on the specifications, LLMDB aims to achieve:

| Metric | Target | Current Status | Notes |
|--------|--------|----------------|-------|
| **Read latency (p99)** | < 60 µs | TBD | 256-byte value on NVMe SSD |
| **Write throughput** | 250 MB/s | TBD | Single writer, sustained |
| **WASM map throughput** | ≥ 8M pages/s | TBD | 32-byte keys |
| **Startup memory** | ≤ 5 MB RSS | TBD | Minimal footprint |
| **Max database size** | 128 TB | ✅ | 64-bit address space |
| **Crash recovery time** | < 1 s | TBD | After power loss |

## Benchmark Suite

### 1. Microbenchmarks

#### Read Latency (`benchmarks/read_latency.py`)
```python
# Measures p50, p95, p99 latencies for various key/value sizes
# Tests both hot (cached) and cold (disk) reads
# Runs with different database sizes (1GB, 10GB, 100GB)
```

#### Write Throughput (`benchmarks/write_throughput.py`)
```python
# Measures sustained write rate in MB/s
# Tests various value sizes (256B, 1KB, 4KB, 1MB)
# Includes WAL and no-WAL scenarios
```

#### Temporal Queries (`benchmarks/temporal_queries.py`)
```python
# Measures overhead of temporal operations
# AS OF queries at various time depths
# Range scans with temporal predicates
```

#### WASM Execution (`benchmarks/wasm_perf.py`)
```python
# Maps pages through WASM functions
# Tests various function complexities
# Measures JIT compilation overhead
```

### 2. Workload Benchmarks

#### YCSB Workloads
- **Workload A**: 50% reads, 50% updates
- **Workload B**: 95% reads, 5% updates  
- **Workload C**: 100% reads
- **Workload D**: 95% reads, 5% inserts (latest)
- **Workload E**: 95% scans, 5% inserts
- **Workload F**: 50% reads, 50% read-modify-write

#### Time-Series Workload
- Continuous inserts with current timestamp
- Periodic range queries for time windows
- Downsampling via WASM functions

#### Graph Workload
- Social graph traversals
- Shortest path queries
- Community detection algorithms

### 3. System Benchmarks

#### Memory Usage
- RSS growth over time
- Page cache efficiency
- WASM memory overhead

#### Concurrent Access
- Multiple readers with single writer
- Reader throughput under write load
- Lock contention analysis

#### Recovery Performance
- Time to recover from crashes
- Data integrity verification
- WAL replay speed

## Running Benchmarks

### Quick Benchmark
```bash
# Run core performance tests
make bench-quick

# Output includes:
# - Read latency histogram
# - Write throughput graph
# - Comparison with targets
```

### Full Benchmark Suite
```bash
# Run all benchmarks (takes ~30 minutes)
make bench-full

# Generates detailed report in bench-results/
# Includes regression detection
```

### Continuous Benchmarking
```bash
# Run in CI to detect regressions
make bench-ci

# Fails if performance degrades >5%
# Posts results to PR comments
```

## Performance Optimization Guide

### 1. Storage Layer Optimizations

#### Page Size Tuning
- Default: 4KB pages (matches OS page size)
- Large values: Consider 16KB or 64KB pages
- Trade-off: Larger pages reduce B-tree depth but increase write amplification

#### MMAP Configuration
```python
# Optimize mmap settings
env = lmdb.open(
    path,
    map_size=1099511627776,  # 1TB map size
    metasync=False,          # Rely on OS sync
    sync=False,              # Batch syncs
    writemap=True,           # Direct writes
)
```

#### Write Batching
- Group small writes into transactions
- Use write-ahead log for durability
- Tune fsync frequency based on durability needs

### 2. Temporal Key Optimizations

#### Key Encoding
- Pack keys for cache efficiency
- Use varint encoding for timestamps
- Align to 8-byte boundaries

#### Temporal Indexes
- Maintain separate index for valid time
- Use bloom filters for existence checks
- Cache recent time ranges

### 3. WASM Execution Optimizations

#### Module Caching
- Pre-compile frequently used modules
- Share compiled code across invocations
- Use memory mapping for large modules

#### Fuel Tuning
```python
# Adjust fuel based on function complexity
config = WasmConfig(
    fuel_per_instruction=1,
    max_fuel=25_000_000,  # 25ms at ~1ns/instruction
    cache_size=100,       # Module cache entries
)
```

#### Batch Processing
- Process multiple pages per WASM call
- Amortize invocation overhead
- Use SIMD instructions where possible

### 4. Query Optimization

#### Predicate Pushdown
- Push temporal filters to storage layer
- Minimize data movement
- Use covering indexes

#### Result Streaming
- Return results as they're computed
- Avoid materializing full result sets
- Use async/await for I/O overlap

### 5. System-Level Optimizations

#### CPU Affinity
```bash
# Pin LLMDB to specific cores
taskset -c 0-3 llmdb-server

# Isolate from other processes
# Reduce context switches
```

#### I/O Scheduling
```bash
# Use deadline scheduler for predictable latency
echo deadline > /sys/block/nvme0n1/queue/scheduler

# Tune read-ahead for sequential scans
echo 256 > /sys/block/nvme0n1/queue/read_ahead_kb
```

#### Huge Pages
```bash
# Enable transparent huge pages
echo always > /sys/kernel/mm/transparent_hugepage/enabled

# Pre-allocate huge pages
echo 1000 > /proc/sys/vm/nr_hugepages
```

## Profiling Tools

### 1. Built-in Profiler
```bash
llmdb profile --duration 60 --output profile.json

# Captures:
# - Function call counts
# - Latency distributions  
# - Resource usage
```

### 2. Flame Graphs
```bash
# Generate flame graph of CPU usage
llmdb flamegraph --pid $(pgrep llmdb)

# Visualize hot paths
# Identify optimization targets
```

### 3. I/O Analysis
```bash
# Trace I/O operations
llmdb iotrace --duration 10

# Shows:
# - Read/write patterns
# - Seek distances
# - Cache hit rates
```

## Performance Anti-Patterns

### 1. Avoid These Patterns

❌ **Random writes to cold pages**
- Causes excessive page faults
- Fragments B-tree
- Solution: Batch writes by key locality

❌ **Unbounded temporal queries**
- Scans entire history
- Memory explosion
- Solution: Always include time bounds

❌ **Large WASM modules**
- Slow compilation
- Memory pressure
- Solution: Split into smaller functions

❌ **Synchronous fsync on every write**
- Destroys throughput
- Solution: Use group commit

### 2. Best Practices

✅ **Batch related operations**
- Amortize transaction overhead
- Improve locality
- Reduce lock contention

✅ **Use appropriate value types**
- Raw bytes for opaque data
- JSON for structured data
- Specialized types for graphs/vectors

✅ **Monitor resource usage**
- Set up alerts for degradation
- Track trends over time
- Capacity planning

## Benchmarking Methodology

### 1. Environment Setup
- Dedicated hardware (no virtualization)
- Consistent CPU frequency (disable turbo)
- Sufficient warm-up period
- Multiple runs for statistical significance

### 2. Measurement Best Practices
- Use high-resolution timers (CLOCK_MONOTONIC)
- Account for coordinated omission
- Measure tail latencies, not just average
- Include GC/compaction effects

### 3. Reporting Guidelines
- Include hardware specifications
- Document configuration parameters
- Provide reproducible scripts
- Compare against baseline

## Future Performance Work

### Near-term (Phase 3-4)
- [ ] Implement WAL for write batching
- [ ] Add temporal query optimization
- [ ] Create benchmark CI pipeline

### Medium-term (Phase 5-6)
- [ ] Optimize WASM JIT compilation
- [ ] Implement query result caching
- [ ] Add vectorized operations

### Long-term (Phase 7-8)
- [ ] GPU acceleration for vectors
- [ ] Distributed query execution
- [ ] Adaptive indexing

## Getting Help

- Performance issues: Create GitHub issue with benchmark results
- Optimization advice: See [docs/tuning.md](docs/tuning.md)
- Custom benchmarks: Contribute to `benchmarks/` directory

Remember: Measure first, optimize second. Use the built-in profiling tools to identify bottlenecks before making changes.