# Bitemporal Data Model in LLMDB

This document explains LLMDB's bitemporal data model, which tracks two dimensions of time for every piece of data: when it was true in the real world (valid time) and when it was recorded in the database (transaction time).

## Table of Contents

1. [Temporal Concepts](#temporal-concepts)
2. [Key Structure](#key-structure)
3. [Temporal Queries](#temporal-queries)
4. [Use Cases](#use-cases)
5. [Implementation Details](#implementation-details)
6. [Performance Considerations](#performance-considerations)
7. [Examples](#examples)

## Temporal Concepts

### Valid Time
The time period during which a fact is true in the real world, regardless of when it was recorded in the database.

**Example**: A person's employment period from 2020-01-01 to 2022-12-31, even if this information was only entered into the database in 2023.

### Transaction Time  
The time period during which a fact was stored in the database and can be retrieved.

**Example**: The employment record was inserted on 2023-01-15 and corrected on 2023-02-01, creating two transaction time periods.

### Bitemporal Model
LLMDB tracks both dimensions simultaneously, creating a complete audit trail that answers:
- **What did we know?** (transaction time)
- **When was it true?** (valid time)
- **When did we know it?** (combination of both)

## Key Structure

Every LLMDB key contains four components:

```
[partition_id: u32][user_key: bytes][valid_from: u64][tx_id: u64]
```

### Components Explained

#### Partition ID (u32)
- Enables horizontal sharding across nodes
- Groups related data together
- Range: 0 to 4,294,967,295

#### User Key (bytes)
- Application-defined identifier
- Can be any byte sequence
- Typical formats: strings, UUIDs, structured keys

#### Valid From (u64) 
- Microseconds since Unix epoch (1970-01-01 00:00:00 UTC)
- Start of the validity period
- Automatically assigned if not specified

#### Transaction ID (u64)
- Monotonic counter per database
- Assigned when the record is committed
- Used for transaction-time queries

### Key Encoding

```python
from llmdb.temporal_key import Key, pack, unpack

# Create a key
key = Key(
    partition=0,
    user_key="user:alice",
    valid_from=1640995200_000000,  # 2022-01-01 00:00:00 UTC in microseconds
    tx_id=12345
)

# Encode to bytes for storage
encoded = pack(key)

# Decode from bytes
decoded = unpack(encoded)
```

## Temporal Queries

LLMDB supports SQL:2011 temporal query operators:

### AS OF VALID
Query data as it was valid at a specific point in time:

```sql
-- Get user data valid on 2022-06-15
SELECT * FROM users 
AS OF VALID TIMESTAMP '2022-06-15 12:00:00'
WHERE user_id = 'alice';
```

```python
# Python API
from datetime import datetime
timestamp = datetime(2022, 6, 15, 12, 0, 0)
value = db.get_as_of_valid(key, timestamp)
```

### AS OF TRANSACTION  
Query data as it existed in the database at a specific transaction:

```sql
-- Get data as it existed at transaction 10000
SELECT * FROM users
AS OF TRANSACTION 10000
WHERE user_id = 'alice';
```

### BETWEEN VALID
Query all versions that were valid during a time range:

```sql
-- Get all versions valid during Q2 2022
SELECT * FROM users
BETWEEN VALID TIMESTAMP '2022-04-01' AND TIMESTAMP '2022-06-30'
WHERE user_id = 'alice';
```

### VERSIONS BETWEEN
Get all versions recorded during a transaction range:

```sql
-- Get all versions recorded between transactions 5000 and 6000
SELECT * FROM users
VERSIONS BETWEEN 5000 AND 6000
WHERE user_id = 'alice';
```

### Combined Temporal Queries
Query both dimensions simultaneously:

```sql
-- What did we know about Alice on 2022-06-15, 
-- as recorded by transaction 8000?
SELECT * FROM users
AS OF VALID TIMESTAMP '2022-06-15 12:00:00'
AS OF TRANSACTION 8000
WHERE user_id = 'alice';
```

## Use Cases

### 1. Audit Trail
Track all changes to critical data:

```python
# Original record
db.put(Key(0, "account:123", valid_from=datetime(2022, 1, 1)), 
       {"balance": 1000, "status": "active"})

# Balance update
db.put(Key(0, "account:123", valid_from=datetime(2022, 6, 15)), 
       {"balance": 1500, "status": "active"})

# Status change  
db.put(Key(0, "account:123", valid_from=datetime(2022, 12, 1)), 
       {"balance": 1500, "status": "frozen"})

# Query: What was the balance on July 1st?
balance = db.get_as_of_valid(Key(0, "account:123"), datetime(2022, 7, 1))
# Returns: {"balance": 1500, "status": "active"}
```

### 2. Slowly Changing Dimensions
Handle data that changes over time:

```python
# Employee record with changing salary
db.put(Key(0, "employee:alice", valid_from=datetime(2020, 1, 1)), 
       {"salary": 50000, "department": "engineering"})

db.put(Key(0, "employee:alice", valid_from=datetime(2021, 1, 1)), 
       {"salary": 55000, "department": "engineering"})  # Raise

db.put(Key(0, "employee:alice", valid_from=datetime(2022, 1, 1)), 
       {"salary": 60000, "department": "management"})  # Promotion

# Query salary history
for record in db.scan_versions(Key(0, "employee:alice")):
    print(f"From {record.valid_from}: ${record.value['salary']}")
```

### 3. Regulatory Compliance
Maintain complete historical records:

```python
# GDPR: User consents to data processing
db.put(Key(0, "consent:alice", valid_from=datetime(2022, 5, 1)), 
       {"marketing": True, "analytics": True})

# User withdraws marketing consent
db.put(Key(0, "consent:alice", valid_from=datetime(2022, 8, 15)), 
       {"marketing": False, "analytics": True})

# Audit: Was marketing consent valid on July 1st?
consent = db.get_as_of_valid(Key(0, "consent:alice"), datetime(2022, 7, 1))
can_send_marketing = consent["marketing"]  # True
```

### 4. Error Correction
Fix historical data while preserving the correction trail:

```python
# Incorrect record entered
db.put(Key(0, "temperature:sensor1", valid_from=datetime(2022, 6, 15, 14, 0)), 
       {"celsius": 250})  # Obviously wrong!

# Correction: the actual temperature was 25°C
db.put(Key(0, "temperature:sensor1", valid_from=datetime(2022, 6, 15, 14, 0)), 
       {"celsius": 25})

# The correction has a later transaction time, so current queries return 25°C
# But we can still see the original incorrect value if needed
```

## Implementation Details

### Storage Layout
Keys are stored in lexicographic order, which provides natural clustering:

```
partition:0|user:alice|valid:1640995200000000|tx:100
partition:0|user:alice|valid:1640995200000000|tx:200  # Same valid time, different tx
partition:0|user:alice|valid:1672531200000000|tx:150  # Different valid time
partition:0|user:bob|valid:1640995200000000|tx:101    # Different user
```

### Indexing Strategy
- **Primary Index**: Full bitemporal key (partition, user_key, valid_from, tx_id)
- **Valid Time Index**: (partition, user_key, valid_from) for temporal queries
- **Transaction Time Index**: (tx_id) for transaction-time queries
- **Current Version Index**: (partition, user_key) pointing to latest versions

### Version Resolution
When multiple versions exist, LLMDB uses these rules:

1. **Latest Valid Time**: For a given transaction time, use the version with the latest valid_from ≤ query_time
2. **Latest Transaction**: For overlapping valid times, use the version with the highest transaction ID

### Garbage Collection
Old versions can be cleaned up based on policies:

```python
# Retention policies
retention_policy = {
    "keep_versions": 100,        # Keep last 100 versions per key
    "keep_duration": "1 year",   # Keep versions for 1 year
    "keep_transactions": 10000,  # Keep last 10000 transactions
}
```

## Performance Considerations

### Query Performance
- **Point Queries**: O(log n) where n is number of versions for a key
- **Range Queries**: O(log n + k) where k is result size
- **Temporal Scans**: Optimized with temporal indexes

### Storage Overhead
- **Key Size**: ~32 bytes overhead per key (vs 16 bytes for simple KV)
- **Index Space**: Additional indexes consume ~50% more space
- **Compression**: Temporal keys compress well due to locality

### Write Performance
- **Transaction Assignment**: Monotonic counter, no conflicts
- **Valid Time Assignment**: Can be batched for bulk loads
- **Index Updates**: All indexes updated atomically

### Memory Usage
- **Version Cache**: LRU cache of recent versions
- **Index Cache**: B-tree nodes cached in memory
- **Query Cache**: Compiled temporal query plans cached

## Examples

### Basic Operations

```python
from llmdb import KV
from llmdb.temporal_key import Key
from datetime import datetime

# Open database
db = KV("./temporal_demo.db")

# Insert with explicit valid time
key = Key(partition=0, user_key="product:123")
db.put_valid_at(key, {"price": 29.99, "stock": 100}, 
                valid_from=datetime(2022, 1, 1))

# Insert with current valid time (default)
db.put(key, {"price": 32.99, "stock": 85})

# Query current version
current = db.get(key)
print(f"Current price: ${current['price']}")

# Query historical version
historical = db.get_as_of_valid(key, datetime(2022, 6, 1))
print(f"Price in June: ${historical['price']}")

# Get all versions
for version in db.get_versions(key):
    print(f"{version.valid_from}: ${version.value['price']}")
```

### Complex Temporal Queries

```python
# Find all products with price changes in Q2 2022
products_with_changes = []
for product_key in db.scan_keys(prefix="product:"):
    versions = db.get_versions_between_valid(
        product_key, 
        start=datetime(2022, 4, 1),
        end=datetime(2022, 6, 30)
    )
    if len(versions) > 1:
        products_with_changes.append(product_key)

# Calculate revenue at different points in time
def calculate_revenue(date):
    total = 0
    for product_key in db.scan_keys(prefix="product:"):
        product = db.get_as_of_valid(product_key, date)
        if product:
            total += product.get('price', 0) * product.get('stock', 0)
    return total

q1_revenue = calculate_revenue(datetime(2022, 3, 31))
q2_revenue = calculate_revenue(datetime(2022, 6, 30))
print(f"Revenue growth: {(q2_revenue - q1_revenue) / q1_revenue * 100:.1f}%")
```

The bitemporal model is one of LLMDB's most powerful features, enabling applications to maintain complete historical accuracy while supporting complex temporal analytics and compliance requirements.