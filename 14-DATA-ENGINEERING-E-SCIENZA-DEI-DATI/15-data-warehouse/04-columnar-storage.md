# Columnar Storage in Data Warehouses

Columnar storage is the single most important architectural innovation behind the
performance of modern analytical databases. In traditional row-oriented databases
(PostgreSQL, MySQL), all columns of a row are stored physically adjacent on disk. In
column-oriented databases (BigQuery, Snowflake, Redshift, ClickHouse), all values of a
single column are stored adjacent. This seemingly low-level difference produces enormous
performance gains for analytical workloads — often 10x–100x improvement in I/O, with
further gains from compression and vectorised execution.

---

## Table of Contents

1. Row-Oriented vs Column-Oriented Storage
2. Why Columnar Is Superior for Analytics
3. Column Encoding Techniques
4. Apache Parquet — Deep Dive
5. Apache ORC
6. Apache Arrow — In-Memory Columnar
7. Modern Table Formats: Delta Lake, Iceberg, Hudi
8. Predicate Pushdown and Partition Pruning
9. Vectorised Execution
10. Compression Algorithms
11. Performance Patterns for Columnar Queries
12. Columnar Storage in Cloud Data Warehouses
13. Troubleshooting
14. Frequently Asked Questions
15. Exercises

---

## 1. Row-Oriented vs Column-Oriented Storage

### 1.1 Physical Layout

```
Data: 4 orders with 5 columns

ROW-ORIENTED (PostgreSQL, MySQL):
Disk block: [1,C001,2024-01-15,49.99,3] [2,C002,2024-01-15,129.00,1] [3,C001,2024-01-16,89.50,2] ...
             ↑ complete row 1 ↑          ↑ complete row 2 ↑

COLUMN-ORIENTED (BigQuery, Snowflake, Redshift, ClickHouse):
Disk block col_1: [1] [2] [3] [4]                                ← order_id
Disk block col_2: [C001] [C002] [C001] [C003]                    ← customer_id
Disk block col_3: [2024-01-15] [2024-01-15] [2024-01-16] ...     ← date
Disk block col_4: [49.99] [129.00] [89.50] [199.99]              ← amount
Disk block col_5: [3] [1] [2] [5]                                ← quantity
```

### 1.2 I/O Implications

```sql
-- Query: SELECT SUM(amount) FROM orders

-- Row-oriented:
--   Reads ALL 5 columns for every row, even though only 'amount' is needed.
--   Wasted I/O: order_id, customer_id, date, quantity are read but discarded.
--   For 100M rows × 5 columns × ~200 bytes/row = ~20 GB read.

-- Column-oriented:
--   Reads ONLY the 'amount' column.
--   For 100M rows × 8 bytes (NUMERIC) = ~800 MB read.
--   Speedup from I/O alone: 25x.
```

### 1.3 When Row-Oriented Is Better

Row-oriented storage is not obsolete. It excels at:

| Workload                       | Why rows win                                               |
|--------------------------------|------------------------------------------------------------|
| Point lookups (SELECT by PK)   | One disk seek reads the entire row; no reassembly needed   |
| INSERT / UPDATE / DELETE       | Writes land in a single location per row                   |
| Small result sets              | Fetching 10 rows of 50 columns is 1 seek, not 50 seeks    |
| OLTP transactions              | Latency-sensitive; each operation touches few rows          |

**Rule of thumb**: if the workload touches few rows but many columns → row store. If it
touches many rows but few columns → column store.

---

## 2. Why Columnar Is Superior for Analytics

### 2.1 Projection Pushdown

Analytical queries typically select a small subset of columns from wide tables. Columnar
storage reads only the requested columns.

```sql
-- OLAP table: 100M rows, 50 columns, 50 GB total on disk

-- Row-oriented: SELECT year, SUM(revenue) → reads 50 GB (all columns)
-- Columnar:     SELECT year, SUM(revenue) → reads 2 GB (2 columns)
-- Reduction: 25x I/O savings
```

### 2.2 Compression Efficiency

Values within a single column share the same data type and often have low entropy
(repetitive values, sequential numbers, limited cardinality). This makes columnar data
far more compressible than row data.

```
Example: column "status" VARCHAR(10) with 5 distinct values over 100M rows

Row storage:   100M × 10 bytes = 1 GB
Columnar with dictionary encoding:
  Dictionary:  5 values × 10 bytes = 50 bytes
  Data:        100M × 3 bits (index into dictionary of 5 values) ≈ 37 MB
  Compression ratio: ~27x for this column alone
```

### 2.3 CPU Cache Efficiency

When scanning a column, all values are adjacent in memory. The CPU's L1/L2 cache lines
are filled with relevant data, not with unrelated column values. Cache hit rates for
columnar scans are dramatically higher than for row scans.

### 2.4 SIMD and Vectorised Processing

Modern CPUs have SIMD (Single Instruction, Multiple Data) instructions that can operate on
multiple values simultaneously. Columnar layouts let the engine apply a single operation
(e.g., "compare against threshold") to a batch of values in one CPU cycle.

---

## 3. Column Encoding Techniques

Encoding transforms raw column values into a more compact representation before general-
purpose compression is applied. Encoding is type-aware and semantics-preserving — the
engine can often operate directly on encoded data without decoding.

### 3.1 Dictionary Encoding

Replaces repeated string values with integer codes referencing a dictionary.

```
Raw data:    ['completed', 'pending', 'completed', 'shipped', 'completed', 'pending']
Dictionary:  {0: 'completed', 1: 'pending', 2: 'shipped'}
Encoded:     [0, 1, 0, 2, 0, 1]

Storage: dictionary (3 entries) + 6 integers (each 2 bits) vs 6 strings
Ideal for: low-cardinality columns (status, country, category, boolean-like flags)
```

```python
import pyarrow as pa

# PyArrow: explicit dictionary encoding
array = pa.array(['completed', 'pending', 'completed', 'shipped', 'completed', 'pending'])
dict_array = array.dictionary_encode()

print(dict_array.type)          # dictionary<int8, string>
print(dict_array.indices)       # [0, 1, 0, 2, 0, 1]
print(dict_array.dictionary)    # ['completed', 'pending', 'shipped']
```

### 3.2 Run-Length Encoding (RLE)

Replaces consecutive repeated values with (value, count) pairs.

```
Raw data:    [A, A, A, A, B, B, C, C, C, C, C, C, A, A]
RLE encoded: [(A, 4), (B, 2), (C, 6), (A, 2)]

Ideal for: sorted columns, columns with long runs of the same value
Worst case: alternating values (A, B, A, B, ...) — RLE expands the data
```

**When RLE helps**: if the column is used as a sort key (or cluster key), values naturally
form long runs. A `date_key` column sorted in order produces runs of the same date across
all rows for that day.

### 3.3 Delta Encoding (Frame of Reference)

Stores the difference between consecutive values instead of the absolute values. Combined
with bit-packing, this dramatically reduces space for monotonically increasing sequences.

```
Raw data:    [1000, 1001, 1003, 1004, 1005, 1010]
Base value:  1000
Deltas:      [0, 1, 3, 4, 5, 10]

Each delta fits in 4 bits (max delta = 10 < 16) instead of the 10+ bits for the raw value.

Ideal for: timestamps, auto-increment IDs, sequential counters
```

### 3.4 Bit-Packing

Uses the minimum number of bits needed to represent each value, instead of a full 32-bit
or 64-bit integer.

```
Raw data (INT32, 32 bits each): [3, 1, 4, 1, 5, 9, 2, 6]
Maximum value: 9, which needs 4 bits (ceil(log2(9+1)) = 4)
Bit-packed:    4 bits × 8 values = 32 bits = 4 bytes
Original:      32 bits × 8 values = 256 bits = 32 bytes
Compression:   8x

Ideal for: small integers, dictionary indices, delta-encoded values
```

### 3.5 Byte Stream Split

Splits multi-byte floating-point values into separate byte streams (all first bytes
together, all second bytes together, etc.). Each byte stream has higher redundancy and
compresses better.

```
Raw FLOAT32 values (4 bytes each): [3.14, 3.15, 3.16, 3.17]
Bytes per value:  [B0 B1 B2 B3], [B0 B1 B2 B3], [B0 B1 B2 B3], [B0 B1 B2 B3]

Byte stream split:
  Stream 0: [B0, B0, B0, B0]   ← all first bytes (often identical for similar values)
  Stream 1: [B1, B1, B1, B1]
  Stream 2: [B2, B2, B2, B2]
  Stream 3: [B3, B3, B3, B3]

Each stream has higher redundancy → compresses better with LZ4/ZSTD.

Ideal for: floating-point sensor data, scientific measurements, financial prices
```

### 3.6 Encoding Selection Guidelines

```
┌─────────────────────────────┬─────────────────────────────────────────┐
│ Column characteristics      │ Best encoding                          │
├─────────────────────────────┼─────────────────────────────────────────┤
│ Low cardinality strings     │ Dictionary                             │
│ Sorted / clustered values   │ RLE + bit-packing                      │
│ Monotonic integers/timestamps│ Delta + bit-packing                   │
│ Small range integers        │ Bit-packing                            │
│ Floating point (similar)    │ Byte stream split + LZ4/ZSTD           │
│ High cardinality strings    │ Plain + LZ4/ZSTD                       │
│ Boolean                     │ Bit-packing (1 bit per value)          │
└─────────────────────────────┴─────────────────────────────────────────┘
```

---

## 4. Apache Parquet — Deep Dive

Parquet is the most widely used open-source columnar file format. It is the default storage
format for Spark, the backing format for Delta Lake and Iceberg, and is natively read by
Athena, BigQuery (external tables), DuckDB, Polars, and virtually every modern data tool.

### 4.1 File Structure

```
┌───────────────────────────────────────────────────┐
│                  Parquet File                      │
├───────────────────────────────────────────────────┤
│  Magic number: "PAR1" (4 bytes)                   │
│                                                   │
│  ┌─────────────────────────────────────────────┐  │
│  │           Row Group 0                       │  │
│  │  ┌───────────┐ ┌───────────┐ ┌───────────┐ │  │
│  │  │ Column 0  │ │ Column 1  │ │ Column 2  │ │  │
│  │  │  Chunk    │ │  Chunk    │ │  Chunk    │ │  │
│  │  │ ┌───────┐ │ │ ┌───────┐ │ │ ┌───────┐ │ │  │
│  │  │ │ Page 0│ │ │ │ Page 0│ │ │ │ Page 0│ │ │  │
│  │  │ ├───────┤ │ │ ├───────┤ │ │ ├───────┤ │ │  │
│  │  │ │ Page 1│ │ │ │ Page 1│ │ │ │ Page 1│ │ │  │
│  │  │ └───────┘ │ │ └───────┘ │ │ └───────┘ │ │  │
│  │  └───────────┘ └───────────┘ └───────────┘ │  │
│  └─────────────────────────────────────────────┘  │
│                                                   │
│  ┌─────────────────────────────────────────────┐  │
│  │           Row Group 1                       │  │
│  │  (same structure)                           │  │
│  └─────────────────────────────────────────────┘  │
│                                                   │
│  ┌─────────────────────────────────────────────┐  │
│  │           File Footer (Metadata)            │  │
│  │  - Schema                                   │  │
│  │  - Row group metadata                       │  │
│  │  - Column chunk metadata (offsets, sizes)    │  │
│  │  - Column statistics (min, max, null_count)  │  │
│  │  - Encoding info                            │  │
│  │  - Key-value metadata (user-defined)        │  │
│  └─────────────────────────────────────────────┘  │
│                                                   │
│  Footer length (4 bytes)                          │
│  Magic number: "PAR1" (4 bytes)                   │
└───────────────────────────────────────────────────┘
```

**Key concepts:**

- **Row Group**: a horizontal partition of the data. Each row group contains a chunk of
  rows (typically 50K–1M rows). Row groups are the unit of parallelism and predicate
  pushdown.
- **Column Chunk**: the data for one column within one row group. This is what gets read
  when you query a specific column.
- **Page**: the smallest unit of I/O within a column chunk. Pages are individually
  compressed and encoded. Default page size is 1 MB.
- **Footer**: metadata section at the end of the file. Contains schema, row group offsets,
  and column statistics. A reader reads the footer first, then seeks to only the column
  chunks and row groups it needs.

### 4.2 Column Statistics

Each column chunk stores min/max statistics (and optionally null_count, distinct_count).
These statistics enable predicate pushdown without reading the actual data.

```python
import pyarrow.parquet as pq

# Inspect Parquet file metadata
pf = pq.ParquetFile('sales.parquet')

# File-level metadata
print(f"Number of row groups: {pf.metadata.num_row_groups}")
print(f"Number of columns:    {pf.metadata.num_columns}")
print(f"Number of rows:       {pf.metadata.num_rows}")

# Row group 0, column 3 (amount) statistics
stats = pf.metadata.row_group(0).column(3).statistics
print(f"Min:        {stats.min}")           # e.g., 1.99
print(f"Max:        {stats.max}")           # e.g., 9999.99
print(f"Null count: {stats.null_count}")    # e.g., 0
print(f"Num values: {stats.num_values}")    # e.g., 100000
print(f"Has min/max:{stats.has_min_max}")   # True
```

### 4.3 Writing Parquet Files

```python
import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd
import numpy as np

# Create sample data
n = 1_000_000
df = pd.DataFrame({
    'order_id':    range(n),
    'customer_id': np.random.choice([f'C{i:04d}' for i in range(500)], n),
    'date':        pd.date_range('2024-01-01', periods=n, freq='s'),
    'amount':      np.random.exponential(100, n).round(2),
    'status':      np.random.choice(['completed', 'pending', 'returned', 'cancelled'], n),
    'quantity':    np.random.randint(1, 20, n)
})

# Explicit schema with optimal types
schema = pa.schema([
    ('order_id',    pa.int32()),
    ('customer_id', pa.dictionary(pa.int16(), pa.string())),  # dictionary for low cardinality
    ('date',        pa.timestamp('us')),                       # microsecond precision
    ('amount',      pa.decimal128(10, 2)),                     # exact decimal
    ('status',      pa.dictionary(pa.int8(), pa.string())),   # dictionary for 4 values
    ('quantity',    pa.int16())                                # small int, not int64
])

table = pa.Table.from_pandas(df, schema=schema)

# Write with optimal settings
pq.write_table(
    table,
    'sales_optimised.parquet',
    compression='zstd',              # best ratio-to-speed for most workloads
    compression_level=3,             # zstd level (1=fast, 22=max compression)
    use_dictionary=True,             # enable dictionary encoding
    write_statistics=True,           # enable min/max stats for predicate pushdown
    row_group_size=100_000,          # 100K rows per row group
    data_page_size=1_048_576,        # 1 MB pages
    version='2.6'                    # Parquet format version
)


# Write partitioned dataset (for data lake / Hive-style layouts)
pq.write_to_dataset(
    table,
    root_path='s3://my-datalake/sales/',
    partition_cols=['date'],          # creates date=YYYY-MM-DD/ directories
    compression='zstd',
    row_group_size=100_000,
    use_dictionary=True,
    write_statistics=True,
    existing_data_behavior='overwrite_or_ignore'
)
```

### 4.4 Reading Parquet Files with Pushdown

```python
import pyarrow.parquet as pq
import pyarrow.dataset as ds

# ------------------------------------------------------------------
# Method 1: PyArrow read_table with row-group-level pushdown
# ------------------------------------------------------------------
table = pq.read_table(
    'sales_optimised.parquet',
    columns=['order_id', 'amount', 'status'],      # projection pushdown
    filters=[
        ('amount', '>=', 100.0),                     # predicate pushdown (uses stats)
        ('status', '=', 'completed')
    ]
)
print(f"Rows returned: {table.num_rows}")

# ------------------------------------------------------------------
# Method 2: PyArrow Dataset API (for partitioned data lakes)
# ------------------------------------------------------------------
dataset = ds.dataset(
    's3://my-datalake/sales/',
    format='parquet',
    partitioning='hive'                              # date=YYYY-MM-DD/
)

scanner = dataset.scanner(
    columns=['order_id', 'customer_id', 'amount'],   # projection pushdown
    filter=(
        (ds.field('date') >= '2024-01-01') &          # partition pruning
        (ds.field('date') <  '2024-02-01') &
        (ds.field('status') == 'completed')           # predicate pushdown
    )
)

# Materialise as pandas
df = scanner.to_table().to_pandas()

# ------------------------------------------------------------------
# Method 3: DuckDB for SQL on Parquet (zero-copy, fast)
# ------------------------------------------------------------------
import duckdb

result = duckdb.sql("""
    SELECT
        customer_id,
        SUM(amount)  AS total_amount,
        COUNT(*)     AS order_count
    FROM read_parquet('s3://my-datalake/sales/**/*.parquet', hive_partitioning=true)
    WHERE date >= '2024-01-01'
      AND date <  '2024-02-01'
      AND status = 'completed'
    GROUP BY customer_id
    ORDER BY total_amount DESC
    LIMIT 20
""").fetchdf()
```

### 4.5 Parquet Row Group Sizing

The row group size is a critical tuning parameter:

| Row group size  | Pros                                  | Cons                                  |
|-----------------|---------------------------------------|---------------------------------------|
| Small (10K)     | Fine-grained predicate pushdown       | Many row groups → metadata overhead   |
| Medium (100K)   | Good balance (recommended default)    | —                                     |
| Large (1M+)     | Better compression, fewer row groups  | Coarser predicate pushdown            |

**Guidance:**
- For data lake files read by Spark/Athena: 100K–500K rows per row group.
- For small files (< 100K rows): one row group for the entire file.
- For very wide tables (100+ columns): smaller row groups to limit memory during reads.

### 4.6 Parquet Page Types

- **Data page**: contains the actual encoded and compressed column values.
- **Dictionary page**: appears at the start of a column chunk when dictionary encoding is
  used. Contains the dictionary (mapping from codes to values).
- **Index page** (Parquet 2.x): optional column index and offset index for fine-grained
  page-level predicate pushdown (as opposed to row-group-level).

---

## 5. Apache ORC

ORC (Optimized Row Columnar) is the columnar format native to the Hive/Hadoop ecosystem.
It shares many design principles with Parquet but has some differences.

### 5.1 ORC File Structure

```
┌──────────────────────────────┐
│        ORC File              │
├──────────────────────────────┤
│ ┌──────────────────────────┐ │
│ │ Stripe 0 (≈ row group)  │ │    Stripe = ORC's equivalent of a Parquet row group
│ │  - Index data            │ │    Default stripe size: 64 MB (vs Parquet's row-count based)
│ │  - Row data (columns)   │ │
│ │  - Stripe footer         │ │
│ └──────────────────────────┘ │
│ ┌──────────────────────────┐ │
│ │ Stripe 1                 │ │
│ └──────────────────────────┘ │
│ ...                          │
│ ┌──────────────────────────┐ │
│ │ File footer              │ │    Contains: schema, stripe info, statistics
│ └──────────────────────────┘ │
│ Postscript (compression info)│
└──────────────────────────────┘
```

### 5.2 ORC vs Parquet Comparison

```
┌─────────────────────────┬─────────────────────────┬─────────────────────────┐
│ Feature                 │ Parquet                 │ ORC                     │
├─────────────────────────┼─────────────────────────┼─────────────────────────┤
│ Ecosystem               │ Spark, Arrow, dbt, DuckDB│ Hive, Presto, Trino    │
│ Schema evolution        │ Excellent (add/remove)  │ Good (add columns)      │
│ Nested types            │ Dremel encoding (native)│ Flattened structs       │
│ Statistics granularity  │ Row group + page (v2)   │ Stripe + row index      │
│                         │                         │ (every 10K rows)        │
│ ACID support            │ Via Delta/Iceberg       │ Native (Hive ACID)      │
│ Default compression     │ Snappy                  │ ZLIB                    │
│ Bloom filters           │ Supported (v2)          │ Built-in, per-column    │
│ Language support        │ Broad (Java, C++, Python│ Primarily Java          │
│                         │  Rust, Go)              │                         │
│ Recommendation          │ New projects            │ Legacy Hive workloads   │
└─────────────────────────┴─────────────────────────┴─────────────────────────┘
```

**Practical guidance**: use Parquet for new projects. Use ORC only if you are operating in
an existing Hive ecosystem and migration is not justified.

---

## 6. Apache Arrow — In-Memory Columnar

Arrow is not a file format — it is an in-memory columnar data representation standard.
Its purpose is to eliminate serialisation/deserialisation overhead when data moves between
systems (Spark → Pandas, DuckDB → Polars, database → application).

### 6.1 Arrow's Design Principles

- **Zero-copy reads**: data can be shared between processes and languages without
  converting formats.
- **Cache-friendly**: contiguous memory layout for each column.
- **SIMD-optimised**: fixed-width data layouts enable vectorised operations.
- **Language-agnostic**: the same memory layout is used in C++, Java, Python, Rust, Go, R.

### 6.2 Arrow in Practice

```python
import pyarrow as pa
import pyarrow.compute as pc

# Create an Arrow table in memory
table = pa.table({
    'customer_id': pa.array(['C001', 'C002', 'C001', 'C003'], type=pa.string()),
    'amount':      pa.array([49.99, 129.00, 89.50, 199.99], type=pa.float64()),
    'status':      pa.array(['completed', 'completed', 'returned', 'completed'])
})

# Arrow compute: vectorised operations on columnar data
completed = pc.equal(table.column('status'), 'completed')
filtered = table.filter(completed)
total = pc.sum(filtered.column('amount'))
print(f"Total completed: {total.as_py()}")   # 378.99

# Zero-copy conversion to Pandas (no data copied if types align)
df = table.to_pandas(self_destruct=True)     # releases Arrow memory as Pandas takes over

# Arrow IPC (Inter-Process Communication): share data between processes
sink = pa.BufferOutputStream()
writer = pa.ipc.new_stream(sink, table.schema)
writer.write_table(table)
writer.close()
buf = sink.getvalue()
# Another process reads:
reader = pa.ipc.open_stream(buf)
received_table = reader.read_all()
```

### 6.3 Arrow Flight — High-Speed Data Transfer

Arrow Flight is an RPC framework that transfers Arrow record batches over gRPC. It avoids
the overhead of serialising to CSV/JSON and deserialising back.

```
Client (Python)  ←── Arrow Flight (gRPC) ──→  Server (DuckDB / Spark / custom)
                       ↑
                 Data transferred as Arrow record batches
                 No serialisation overhead
                 Can saturate 10 Gbps+ network
```

---

## 7. Modern Table Formats: Delta Lake, Iceberg, Hudi

Parquet files alone lack ACID transactions, schema evolution, time travel, and efficient
row-level updates. Modern table formats add these capabilities on top of Parquet (or ORC),
transforming a collection of files into a proper table with database semantics.

### 7.1 Comparison Matrix

```
┌──────────────────────┬─────────────────┬──────────────────┬────────────────┐
│ Feature              │ Delta Lake      │ Apache Iceberg   │ Apache Hudi    │
├──────────────────────┼─────────────────┼──────────────────┼────────────────┤
│ Origin               │ Databricks      │ Netflix → Apache │ Uber → Apache  │
│ ACID transactions    │ Yes             │ Yes              │ Yes            │
│ Time travel          │ Yes (versions)  │ Yes (snapshots)  │ Yes (timeline) │
│ Schema evolution     │ Add/rename cols │ Full evolution   │ Add/rename cols│
│ Partition evolution  │ Manual          │ Hidden partitions│ Manual         │
│ Row-level deletes    │ Merge/Delete    │ Position/equality│ Log-based      │
│ Z-order/clustering   │ OPTIMIZE ZORDER │ Sort order spec  │ Clustering     │
│ Catalog integration  │ Unity Catalog   │ Hive/Glue/REST   │ Hive           │
│ File format          │ Parquet only    │ Parquet, ORC, Avro│ Parquet, ORC  │
│ Transaction log      │ JSON (_delta_log)│ JSON/Avro (metadata)│ Timeline   │
│ Engine support       │ Spark, Flink,   │ Spark, Flink,    │ Spark, Flink   │
│                      │ Trino, DuckDB   │ Trino, DuckDB    │                │
│ Adoption trend       │ Databricks-led  │ Broad multi-vendor│ Uber-centric  │
└──────────────────────┴─────────────────┴──────────────────┴────────────────┘
```

### 7.2 Delta Lake Example

```python
from delta import DeltaTable
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .config("spark.jars.packages", "io.delta:delta-spark_2.12:3.1.0") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog",
            "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .getOrCreate()

# Write a Delta table
df = spark.createDataFrame([
    (1, 'C001', '2024-01-15', 49.99),
    (2, 'C002', '2024-01-15', 129.00),
    (3, 'C001', '2024-01-16', 89.50)
], ['order_id', 'customer_id', 'date', 'amount'])

df.write.format("delta") \
    .mode("overwrite") \
    .partitionBy("date") \
    .save("s3://my-datalake/delta/sales/")

# Time travel: read a previous version
df_v0 = spark.read.format("delta") \
    .option("versionAsOf", 0) \
    .load("s3://my-datalake/delta/sales/")

# MERGE (upsert)
delta_table = DeltaTable.forPath(spark, "s3://my-datalake/delta/sales/")
new_data = spark.createDataFrame([
    (1, 'C001', '2024-01-15', 59.99),   # updated amount
    (4, 'C004', '2024-01-17', 199.99)   # new order
], ['order_id', 'customer_id', 'date', 'amount'])

delta_table.alias("target").merge(
    new_data.alias("source"),
    "target.order_id = source.order_id"
).whenMatchedUpdateAll() \
 .whenNotMatchedInsertAll() \
 .execute()

# Schema evolution: add a column
df_new = spark.createDataFrame([
    (5, 'C005', '2024-01-17', 75.00, 'express')
], ['order_id', 'customer_id', 'date', 'amount', 'shipping_type'])

df_new.write.format("delta") \
    .mode("append") \
    .option("mergeSchema", "true") \
    .save("s3://my-datalake/delta/sales/")

# OPTIMIZE: compact small files + Z-ORDER for multi-dimensional clustering
spark.sql("""
    OPTIMIZE delta.`s3://my-datalake/delta/sales/`
    ZORDER BY (customer_id, date)
""")

# VACUUM: remove old files no longer needed (after time travel window)
spark.sql("""
    VACUUM delta.`s3://my-datalake/delta/sales/`
    RETAIN 168 HOURS
""")
```

### 7.3 Apache Iceberg Example

```sql
-- Iceberg: partition evolution (change partitioning without rewriting data)
CREATE TABLE catalog.db.events (
    event_id    BIGINT,
    event_time  TIMESTAMP,
    user_id     STRING,
    event_type  STRING,
    payload     STRING
)
USING iceberg
PARTITIONED BY (days(event_time));   -- hidden partition on day granularity

-- Later, switch to hourly partitioning without rewriting existing data
ALTER TABLE catalog.db.events
    ADD PARTITION FIELD hours(event_time);

-- Iceberg handles both old (daily) and new (hourly) partitions transparently.

-- Time travel
SELECT * FROM catalog.db.events
    FOR SYSTEM_TIME AS OF TIMESTAMP '2024-01-15 10:00:00';

-- Snapshot expiration (equivalent to Delta VACUUM)
CALL catalog.system.expire_snapshots('db.events', TIMESTAMP '2024-01-10 00:00:00');
```

---

## 8. Predicate Pushdown and Partition Pruning

### 8.1 Partition Pruning

When data is partitioned by a column (e.g., `date`), a query with a filter on that column
reads only the relevant partitions (directories/files), skipping everything else.

```
File system layout (Hive-style partitioning):
s3://sales/date=2024-01-01/part-00000.parquet
s3://sales/date=2024-01-02/part-00000.parquet
s3://sales/date=2024-01-03/part-00000.parquet
...
s3://sales/date=2024-12-31/part-00000.parquet

Query: WHERE date = '2024-01-15'
Engine reads: s3://sales/date=2024-01-15/part-00000.parquet (1 file)
Engine skips: 364 other files
```

### 8.2 Predicate Pushdown (Row Group / Stripe Level)

Within a file, the engine reads column statistics (min/max) from the row group metadata.
If the predicate cannot be satisfied by the statistics, the entire row group is skipped.

```
Row Group 0: amount min=1.00,  max=50.00
Row Group 1: amount min=45.00, max=200.00
Row Group 2: amount min=180.00, max=9999.99

Query: WHERE amount > 500

Row Group 0: max=50.00 < 500 → SKIP (no rows can match)
Row Group 1: max=200.00 < 500 → SKIP
Row Group 2: max=9999.99 > 500 → READ (some rows may match)
```

### 8.3 Page-Level Predicate Pushdown (Parquet Column Index)

Parquet 2.x introduced column indexes and offset indexes that store min/max statistics per
page within a column chunk. This enables even finer-grained skipping.

```
Column chunk "amount" in Row Group 2:
  Page 0: min=180.00, max=350.00  → amount > 500? SKIP
  Page 1: min=320.00, max=620.00  → amount > 500? READ
  Page 2: min=500.00, max=9999.99 → amount > 500? READ
```

### 8.4 Bloom Filters

For equality predicates on high-cardinality columns (e.g., `customer_id = 'C00042'`),
min/max statistics are useless (every row group's range includes C00042). Bloom filters
provide a probabilistic answer: "definitely not in this row group" or "maybe in this row
group."

```python
# Writing Parquet with Bloom filters
pq.write_table(
    table,
    'sales_bloom.parquet',
    write_statistics=True,
    column_config={
        'customer_id': {
            'bloom_filter_enabled': True,
            'bloom_filter_fpp': 0.01,       # 1% false positive rate
            'bloom_filter_ndv': 10000        # expected distinct values
        }
    }
)
```

---

## 9. Vectorised Execution

Vectorised execution processes data in batches (vectors) of values rather than one row at
a time. This is the complement to columnar storage at the compute layer.

### 9.1 Row-at-a-Time vs Vectorised

```
Row-at-a-time (traditional):
for each row:
    read row
    evaluate predicate
    if match: emit row
→ High per-row overhead (function calls, virtual dispatch, branch misprediction)

Vectorised:
for each batch of 1024 values:
    load column batch into CPU register
    apply predicate to entire batch (SIMD)
    produce selection vector (which positions matched)
    use selection vector to gather matching rows
→ Amortised overhead, SIMD parallelism, cache-friendly
```

### 9.2 Engines Using Vectorised Execution

| Engine        | Vectorisation approach                                     |
|---------------|------------------------------------------------------------|
| DuckDB        | Full vectorised engine (batches of 2048 values)            |
| ClickHouse    | Column-at-a-time processing                                |
| Velox (Meta)  | Vectorised execution library (used by Presto/Trino)        |
| DataFusion    | Vectorised, Rust-based (used by Apache Arrow project)      |
| BigQuery      | Dremel engine with vectorised column processing            |
| Snowflake     | Proprietary vectorised engine                              |
| Redshift      | Vectorised scans (AQUA layer)                              |

### 9.3 Late Materialisation

In vectorised engines, columns are processed independently as long as possible. Rows are
only "materialised" (assembled from multiple columns) at the very end, when the final
result needs to be returned.

```
Query: SELECT name, amount FROM orders WHERE status = 'completed' AND amount > 100

Step 1: Scan 'status' column → selection vector A (positions where status = completed)
Step 2: Scan 'amount' column using selection vector A → filter → selection vector B
Step 3: Use selection vector B to gather 'name' and 'amount' columns → final result

The 'name' column is never read for rows that don't match the predicates.
```

---

## 10. Compression Algorithms

### 10.1 Algorithm Comparison

```python
import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd
import numpy as np
import os
import time

def generate_test_data(n: int = 1_000_000) -> pd.DataFrame:
    return pd.DataFrame({
        'id':          range(n),
        'category':    np.random.choice(['A', 'B', 'C', 'D', 'E'], n),
        'timestamp':   pd.date_range('2024-01-01', periods=n, freq='s'),
        'value':       np.random.exponential(100, n).round(2),
        'description': [f'Order {i}' for i in range(n)]
    })

df = generate_test_data()
table = pa.Table.from_pandas(df)

codecs = ['none', 'snappy', 'gzip', 'brotli', 'zstd', 'lz4']
for codec in codecs:
    path = f'/tmp/test_{codec}.parquet'
    t0 = time.time()
    pq.write_table(table, path, compression=codec)
    write_s = time.time() - t0
    size_mb = os.path.getsize(path) / 1024 / 1024
    t0 = time.time()
    _ = pq.read_table(path)
    read_s = time.time() - t0
    print(f"{codec:10s}: {size_mb:6.1f} MB  write={write_s:.2f}s  read={read_s:.2f}s")
```

### 10.2 Typical Results and Guidance

```
┌────────────┬──────────┬───────────┬───────────┬─────────────────────────────────┐
│ Codec      │ Size     │ Write     │ Read      │ Best for                        │
├────────────┼──────────┼───────────┼───────────┼─────────────────────────────────┤
│ none       │ 85.0 MB  │ fastest   │ fastest   │ Temporary/intermediate files    │
│ snappy     │ 38.0 MB  │ fast      │ fast      │ Spark default, real-time ingest │
│ lz4        │ 36.0 MB  │ fast      │ fast      │ Similar to snappy, slightly     │
│            │          │           │           │ better ratio                    │
│ zstd       │ 26.0 MB  │ moderate  │ fast      │ Best ratio-to-speed; rec. for   │
│            │          │           │           │ new projects                    │
│ gzip       │ 28.0 MB  │ slow      │ moderate  │ Legacy compatibility            │
│ brotli     │ 25.0 MB  │ slowest   │ moderate  │ Archival, cold storage          │
└────────────┴──────────┴───────────┴───────────┴─────────────────────────────────┘
```

**Recommendation**: use **zstd** as the default for new projects. It offers the best
balance of compression ratio and decompression speed. Use **snappy** when write speed is
critical (streaming ingestion). Use **gzip** or **brotli** only for cold archival data
where read speed is less important than storage cost.

### 10.3 Compression Levels (zstd)

zstd supports compression levels from 1 (fastest, least compression) to 22 (slowest, best
compression). Level 3 is the default and is a good general-purpose choice.

```python
# zstd level comparison
for level in [1, 3, 6, 9, 15]:
    path = f'/tmp/test_zstd_{level}.parquet'
    pq.write_table(table, path, compression='zstd', compression_level=level)
    size_mb = os.path.getsize(path) / 1024 / 1024
    print(f"zstd level {level:2d}: {size_mb:.1f} MB")

# Typical results:
# zstd level  1: 28.0 MB
# zstd level  3: 26.0 MB   ← default, recommended
# zstd level  6: 24.5 MB
# zstd level  9: 23.8 MB
# zstd level 15: 23.0 MB   (diminishing returns, much slower write)
```

---

## 11. Performance Patterns for Columnar Queries

### 11.1 Select Only Needed Columns

```sql
-- BAD: SELECT * reads all columns — defeats the purpose of columnar storage
SELECT * FROM fact_sales WHERE date_key = 20240115;

-- GOOD: select only the columns you need
SELECT order_id, customer_key, net_revenue
FROM fact_sales
WHERE date_key = 20240115;
```

This is the single most important optimisation for columnar databases. In BigQuery, it
directly affects cost (you pay per byte scanned). In Snowflake, it affects the number of
micro-partitions read.

### 11.2 Partition by the Most Common Filter Column

```sql
-- BigQuery: partition by date + cluster by frequently filtered columns
CREATE TABLE `project.dataset.fact_sales`
PARTITION BY DATE(created_at)
CLUSTER BY customer_key, product_key
AS SELECT * FROM staging.fact_sales_raw;

-- Snowflake: cluster by date (micro-partitions reordered)
CREATE TABLE fact_sales_clustered (
  date_key     INT,
  customer_key INT,
  product_key  INT,
  net_revenue  NUMERIC(12,2)
)
CLUSTER BY (date_key);

-- Query that benefits from both partition pruning and clustering
SELECT
  customer_key,
  SUM(net_revenue) AS total
FROM fact_sales
WHERE date_key BETWEEN 20240101 AND 20240131   -- partition pruning
  AND customer_key IN (1001, 1002, 1003)        -- cluster pruning
GROUP BY customer_key;
```

### 11.3 Sort Data Before Writing

If you control the data pipeline, sort data by the most-queried column before writing to
Parquet. This creates clean min/max ranges in row group statistics, maximising predicate
pushdown effectiveness.

```python
# Sort by date before writing → row group 0 has dates Jan 1-15,
# row group 1 has Jan 16-31, etc. Queries for a specific date skip most row groups.
df_sorted = df.sort_values('date')
table = pa.Table.from_pandas(df_sorted)
pq.write_table(table, 'sales_sorted.parquet', row_group_size=100_000)
```

### 11.4 Avoid Small Files

Many small Parquet files (< 10 MB each) create excessive metadata overhead and prevent
effective predicate pushdown. Compact small files into larger ones.

```python
# BAD: 10,000 files of 1 MB each (100 bytes of metadata per file × 10K = overhead)
# GOOD: 100 files of 100 MB each

# Spark: repartition before writing
df.repartition(100).write.parquet('s3://output/')

# Delta Lake: OPTIMIZE command compacts small files
# spark.sql("OPTIMIZE delta.`s3://my-table/`")
```

### 11.5 Choose Appropriate Data Types

Narrow data types compress better and process faster.

```python
# BAD: using int64 for a quantity that never exceeds 1000
schema_bad = pa.schema([('quantity', pa.int64())])    # 8 bytes per value

# GOOD: using int16 for a quantity that fits in [-32768, 32767]
schema_good = pa.schema([('quantity', pa.int16())])   # 2 bytes per value
# 4x storage reduction for this column
```

---

## 12. Columnar Storage in Cloud Data Warehouses

### 12.1 Snowflake Micro-Partitions

Snowflake stores data in immutable micro-partitions (50–500 MB compressed, ~16 MB each
uncompressed). Each micro-partition stores data in columnar format with automatic
compression and maintains min/max metadata per column for pruning.

```sql
-- Check micro-partition pruning efficiency
SELECT
  query_id,
  partitions_scanned,
  partitions_total,
  ROUND(partitions_scanned * 100.0 / NULLIF(partitions_total, 0), 2) AS pct_scanned,
  bytes_scanned / 1024 / 1024 AS mb_scanned
FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY(
  date_range_start => DATEADD('hours', -1, CURRENT_TIMESTAMP())
))
WHERE execution_status = 'SUCCESS'
ORDER BY total_elapsed_time DESC
LIMIT 10;

-- If pct_scanned is high (>50%), consider adding CLUSTER BY on the filter column.
```

### 12.2 BigQuery Capacitor Format

BigQuery uses a proprietary columnar format called Capacitor, stored on Google's Colossus
distributed file system. It automatically applies encoding (dictionary, RLE, delta) per
column and maintains statistics for predicate pushdown.

```sql
-- Estimate bytes scanned before running a query
-- BigQuery shows this in the UI; programmatically:
SELECT
  total_bytes_processed,
  total_bytes_billed,
  cache_hit
FROM `region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
WHERE job_id = 'bqjob_r1234_00001234567890';
```

### 12.3 Redshift Columnar Blocks

Redshift stores data in 1 MB columnar blocks. Each block stores a single column's data
for a range of rows. Zone maps (min/max per block) are maintained automatically.

```sql
-- Check compression encoding per column
SELECT
  "column",
  type,
  encoding,
  distkey,
  sortkey
FROM pg_table_def
WHERE tablename = 'fact_sales';

-- Redshift ANALYZE COMPRESSION: suggests optimal encoding per column
ANALYZE COMPRESSION fact_sales;
-- Output example:
-- column      | encoding | est_reduction_pct
-- customer_key| az64     | 85.00
-- date_key    | delta    | 92.00
-- status      | bytedict | 95.00
```

---

## 13. Troubleshooting

### Problem: Parquet file reads are slow despite columnar format

**Possible causes:**
1. **SELECT ***: reading all columns defeats columnar benefits. Fix: select only needed
   columns.
2. **No partition pruning**: query does not filter on the partition column. Fix: add a
   WHERE clause on the partition column.
3. **Unsorted data**: row group statistics (min/max) span the entire value range, so no
   row groups can be skipped. Fix: sort data by the query's filter column before writing.
4. **Too many small files**: each file has fixed metadata overhead. Fix: compact into
   fewer, larger files (100–500 MB).
5. **Wrong compression codec**: using brotli for interactive queries. Fix: switch to zstd
   or snappy.

### Problem: Parquet file is much larger than expected

**Possible causes:**
1. **No compression**: written with `compression='none'`. Fix: use zstd.
2. **High cardinality strings without dictionary**: long unique strings stored as plain
   text. Fix: check if dictionary encoding is appropriate; if not, accept the size or
   consider external compression.
3. **int64 for small integers**: storing boolean-like values as 8-byte integers. Fix: use
   appropriate narrow types (int8, int16, boolean).
4. **Timestamps with nanosecond precision**: 8 bytes per value. Fix: use microsecond or
   millisecond precision if nano is not needed.

### Problem: Predicate pushdown is not working

**Diagnosis:**
```python
# Check if statistics are present
pf = pq.ParquetFile('suspect_file.parquet')
col_meta = pf.metadata.row_group(0).column(0)
print(f"Has stats: {col_meta.statistics is not None}")
print(f"Has min/max: {col_meta.statistics.has_min_max if col_meta.statistics else 'N/A'}")
```

**Possible causes:**
1. **Statistics not written**: the file was created with `write_statistics=False`. Fix:
   rewrite with `write_statistics=True`.
2. **Predicate on a derived expression**: `WHERE YEAR(date) = 2024` cannot use stats on
   the `date` column directly. Fix: rewrite as `WHERE date >= '2024-01-01' AND date <
   '2025-01-01'`.
3. **Dictionary fallback**: if a column has too many distinct values, dictionary encoding
   falls back to plain encoding, and stats may be less useful.

---

## 14. Frequently Asked Questions

**Q: When should I use Parquet vs CSV?**

Always use Parquet for analytical workloads. CSV is appropriate only for human-readable
interchange or for small, one-off data transfers. Parquet is typically 2–10x smaller, 10–
100x faster to query (due to column pruning and predicate pushdown), and preserves schema
information (types, nullability).

**Q: What is the ideal Parquet file size?**

128 MB to 1 GB (compressed) is the sweet spot for most data lake engines. Below 10 MB, the
per-file overhead dominates. Above 2 GB, a single file takes too long to process for some
engines. For data warehouses that shard internally (BigQuery, Snowflake), this is managed
automatically — you load data and the engine handles file sizing.

**Q: Should I use Parquet or Delta Lake / Iceberg?**

If you need any of the following, use a table format (Delta, Iceberg): ACID transactions,
time travel, upserts (MERGE), schema evolution, concurrent writes. If you are writing
append-only data that is never updated and do not need transaction guarantees, plain
Parquet is simpler and has no overhead.

**Q: How does columnar storage handle nested data (structs, arrays, maps)?**

Parquet uses Google's Dremel encoding (repetition and definition levels) to flatten nested
structures into columnar representation. Each leaf field in a nested schema becomes its own
column. This allows columnar benefits even for semi-structured data, though deeply nested
schemas can create many internal columns and reduce performance.

**Q: Can I update a single row in a Parquet file?**

No. Parquet files are immutable. To "update" a row, you rewrite the affected file (or row
group) with the updated data. Table formats (Delta, Iceberg, Hudi) handle this by writing
new files and maintaining a transaction log that logically supersedes the old data.

**Q: What is the relationship between Arrow and Parquet?**

Arrow is an in-memory columnar format; Parquet is an on-disk columnar format. They share
the same type system and are designed to convert between each other with minimal overhead.
A typical data pipeline reads Parquet from disk into Arrow in memory, processes it, and
writes back to Parquet.

---

## 15. Exercises

### Exercise 1: I/O Estimation

A table has 200M rows, 40 columns, and is stored row-oriented at 300 bytes per row. A
query selects 3 columns and scans all rows.

1. How much data does the row-oriented engine read?
2. If the average column width is 7.5 bytes, how much does the columnar engine read?
3. What is the I/O speedup factor?

### Exercise 2: Encoding Selection

For each column below, identify the best encoding and explain why:

| Column              | Type        | Cardinality   | Distribution             |
|---------------------|-------------|---------------|--------------------------|
| `country_code`      | VARCHAR(3)  | ~200          | 80% are 'US' or 'GB'    |
| `event_timestamp`   | TIMESTAMP   | ~200M unique  | Monotonically increasing |
| `is_active`         | BOOLEAN     | 2             | 70% TRUE                 |
| `sensor_reading`    | FLOAT64     | High          | Values cluster near 22.5 |
| `user_id`           | VARCHAR(36) | ~50M unique   | UUID, no pattern         |

### Exercise 3: Predicate Pushdown Analysis

A Parquet file has 5 row groups (200K rows each). The `amount` column has these statistics:

| Row Group | min    | max      |
|-----------|--------|----------|
| 0         | 1.00   | 150.00   |
| 1         | 120.00 | 500.00   |
| 2         | 450.00 | 2000.00  |
| 3         | 1800.00| 5000.00  |
| 4         | 4500.00| 99999.00 |

For each query, identify which row groups are read and which are skipped:

1. `WHERE amount = 75.00`
2. `WHERE amount > 3000`
3. `WHERE amount BETWEEN 200 AND 600`
4. `WHERE amount < 100 OR amount > 50000`

### Exercise 4: File Size Optimisation

You have a dataset of 10M rows with these columns:

- `id` (INT64), `name` (STRING avg 20 chars), `status` (STRING, 4 distinct values),
  `created_at` (TIMESTAMP), `amount` (FLOAT64), `is_verified` (BOOLEAN)

The uncompressed Parquet file is 850 MB.

1. What schema changes would reduce the file size?
2. What compression codec would you choose and why?
3. Estimate the final compressed size with your optimisations.

### Exercise 5: Table Format Selection

For each scenario, recommend plain Parquet, Delta Lake, or Apache Iceberg and justify:

1. Append-only IoT sensor data, 1 TB/day, never updated, queried by time range.
2. Customer master data, 50M rows, updated daily via MERGE (upsert), needs time travel.
3. Multi-engine environment (Spark, Trino, DuckDB, Flink) with partition evolution needs.
4. Small analytics team on Databricks, building a lakehouse, 100 GB total.
5. Regulatory data retention requiring exact point-in-time queries for audits.
