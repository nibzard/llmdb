LQL 1.0 – Language Specification
(A strict superset of ISO SQL:2023 Core, enriched for bitemporal data, graphs, vectors and in-database WebAssembly)

⸻

1 Scope & Compatibility

Topic	LQL 1.0 rule	Notes
SQL baseline	Fully accepts any statement valid in ISO 9075-2:2023 Core (“SQL/Foundation”).	Parser follows identical lexical rules; keywords added by LQL are non-reserved unless stated below. A vendor may initially implement only a subset, but if a statement parses and is recognised as standard SQL it must behave identically.
Extensions	Temporal, Graph (SQL/PGQ †), Vector, WASM, Meta-DDL	All extensions are optional to the caller: a plain SQL client can ignore them.
Strict mode	SET lql.strict = ON; warns if vendor deviates from ANSI semantics.	

† ISO/IEC 9075-16:2023 Property Graph Queries  ￼
Temporal foundation inspired by SQL:2011/2016 system & application time features  ￼

⸻

2 Lexical & Syntactic Additions

<statement>          ::=  <sql-statement>
                       |  <lql-extension>

<lql-extension>      ::=  <temporal-clause>
                       |  <graph-statement>
                       |  <vector-search>
                       |  <wasm-hint>
                       |  <meta-command>

2.1 New reserved keywords

GRAPH, MATCH, NODE, EDGE, VECTOR, EMBEDDED, WASM, MODULE, VALID, TX, VERSIONS, ASOF, BETWEEN_TX, PERIOD, BITEMPORAL.
All other added identifiers are non-reserved (they may be used as table/column names when escaped).

⸻

3 Data-Types

Name	Definition
VECTOR(d INT)	Fixed-length float32[d]; stored packed, SIMD aligned.
PERIOD<TIMESTAMP>	Half-open interval [start,end) in UTC.
EDGE<NODE_ID_TYPE, PROPS JSON>	Internal record: (from, to, props, validPeriod, txTime); serialised as opaque.

All Core SQL types are supported unchanged.

⸻

4 Temporal Extensions

4.1 Table Definition

CREATE TABLE payment (
    id            UUID PRIMARY KEY,
    amount        DECIMAL(12,2),
    valid_period  PERIOD<TIMESTAMP>,
    PERIOD FOR VALID_TIME (valid_period),   -- application time
    PERIOD FOR TX_TIME    (tx_start, tx_end),
    WITH SYSTEM VERSIONING                    -- enables tx time
) WITH (BITEMPORAL = TRUE);

Behaviour
	•	Every row automatically gains transaction time (tx_start, tx_end) and is immutable post-commit.
	•	DML automatically splits periods as in SQL:2011.

4.2 Query Predicates

Form	Semantics
AS OF VALID '2025-07-01'	Snapshot of application time.
VERSIONS BETWEEN TX '2025-01-01' AND '2025-02-01'	Returns row history over system time.
BETWEEN_TX (d1,d2)	Shorthand function usable in WHERE.


⸻

5 Graph Extensions (PGQ-Compatible Subset)

5.1 Graph Projection

CREATE GRAPH friends_graph
  AS TABLE users   KEY(id)
     VERTEX PROPERTIES (name, age),
     TABLE relations  KEY(rel_id)
     EDGE  SOURCE KEY(src_id)  DESTINATION KEY(dst_id)
     PROPERTIES (since DATE);

5.2 Pattern Query

SELECT n.id , m.id, e.since
FROM GRAPH friends_graph
MATCH (n)-[e]->(m)
WHERE n.id = :uid
  AND AS OF VALID '2025-07-01';

Semantics match ISO / PGQ Part 16. Unsupported PGQ clauses must raise FEATURE_NOT_SUPPORTED.

⸻

6 Vector Extension

6.1 Data Definition

ALTER TABLE doc_embeddings
ADD COLUMN embedding VECTOR(1536);

6.2 Search Clause

SELECT id, distance
FROM VECTOR SEARCH doc_embeddings
ORDER BY L2_DISTANCE(embedding, :query_vec) ASC
LIMIT 10;

VECTOR SEARCH acts as a table function producing (rowid, distance) pairs; the engine must choose an approximate index if declared.

⸻

7 In-Database WASM

7.1 Module Lifecycle

UPLOAD MODULE 'infer_reverse' FROM 'file:///tmp/infer_reverse.wasm';
ATTACH MODULE infer_reverse TO GRAPH friends_graph
  ON EVENT EDGE_INSERT;

UPLOAD MODULE stores the raw bytes under _meta/code/{hash} and validates imports.

7.2 Query Hint

SELECT *
FROM orders
EMBEDDED WASM infer_tax('calc', country_code);

Rules
	1.	EMBEDDED WASM <module>('func', arg …) may appear in SELECT, WHERE, ORDER BY, GROUP BY.
	2.	The call executes per row batch inside the transactional context, subject to fuel limits.

⸻

8 Meta-Commands

Command	Purpose
SHOW STORAGE;	file path, map size, freelist pages
EXPLAIN <stmt>;	logical & physical plan incl. WASM stages
MIGRATION APPLY '<json>';	writes a migration record to _meta/schema
`SET lql.strict = {ON	OFF};`


⸻

9 Error Codes (additions)

Code	Meaning
LQL001	Temporal predicate references non-temporal table
LQL010	VECTOR dimension mismatch
LQL020	WASM fuel exhausted
LQL030	Graph projection not found
LQL040	Feature not enabled at compile time

Codes use the SQLSTATE vendor area ('LX' class suggested).

⸻

10 BNF Fragment (extensions only)

temporal-clause ::=  "AS" "OF" "VALID" <timestamp>
                  |  "VERSIONS" "BETWEEN" "TX" <timestamp> "AND" <timestamp>;

graph-statement ::=  "CREATE" "GRAPH" <ident> "AS" table-ref-list
                  |  "MATCH" "(" node-pattern ")" edge-pattern "(" node-pattern ")";

vector-search   ::=  "VECTOR" "SEARCH" <table> [ "USING" index-hint ]
                     "ORDER" "BY" distance-fn "ASC" "LIMIT" <n>;

wasm-hint       ::=  "EMBEDDED" "WASM" <module-name> "(" <string> ["," arg-list] ")";

meta-command    ::=  "UPLOAD" "MODULE" <string> "FROM" <string>
                  |  "ATTACH" "MODULE" <ident> "TO" <object>
                  |  "SHOW" "STORAGE"
                  |  "MIGRATION" "APPLY" <string>;


⸻

11 Examples

11.1 Time-Travel Read

SELECT *
FROM invoices
AS OF VALID '2024-12-31'
WHERE customer_id = 'C001';

11.2 Graph + Vector Hybrid

WITH nearest AS (
  SELECT id
  FROM VECTOR SEARCH doc_embeddings
  ORDER BY COSINE_DISTANCE(embedding, :q) ASC
  LIMIT 50
)
SELECT p.id, m.id
FROM GRAPH purchase_graph
MATCH (p)-[:bought]->(m)
WHERE p.id IN (SELECT id FROM nearest);

11.3 Transactional WASM Trigger

INSERT INTO relations (src_id, dst_id, since)
VALUES ('u1', 'u2', CURRENT_DATE)
EMBEDDED WASM infer_reverse('auto_add_reverse_edge');


⸻

12 Conformance Levels

Level	Required features
LQL-Core	Full SQL Core + temporal predicates (AS OF VALID, VERSIONS BETWEEN TX).
LQL-Graph	Core + GRAPH … MATCH … subset identical to SQL/PGQ.
LQL-Vector	Core + VECTOR type and VECTOR SEARCH.
LQL-WASM	Core + WASM hints and module DDL.
LQL-Full	All of the above.

A vendor must declare its level via SELECT lql_version();.

⸻

13 Reserved Words & Migration Guidance

Only the words in §2.1 become reserved.
When upgrading an existing SQL schema you need to escape those identifiers ("VECTOR") if already in use.

⸻

14 Rationale & Design Goals
	•	Superset guarantee: Any ANSI-SQL tool works unchanged; LQL tokens are parsed but ignored when syntactically legal.
	•	Declarative first: Temporal and graph constructs integrate with the optimiser; WASM appears as costed UDF.
	•	No bespoke keywords for simple things: Temporal predicates mirror SQL:2011/2016 wording; graph mirrors SQL/PGQ so existing know-how transfers.
	•	Edge computing ready: WASM is strictly opt-in and sandboxed.

⸻

References
	•	ISO/IEC 9075-16:2023 — Property Graph Queries (SQL/PGQ)  ￼
	•	ISO/IEC 9075-2:2016, -2:2023 drafts — SQL/Foundation
	•	Temporal features in SQL:2011  ￼

⸻

End of LQL 1.0 specification.
