# Python for Data Analytics — Pandas, NumPy, and the Data Science Stack

## 1. NumPy Foundation

### ndarray Internals

NumPy's `ndarray` is a fixed-size, homogeneous, contiguous block of memory interpreted through metadata: shape, dtype, strides, and flags. Understanding this architecture explains why NumPy outperforms Python lists by 10-100x for numerical work.

```python
import numpy as np

arr = np.arange(12).reshape(3, 4)

# Inspect internals
print(arr.dtype)        # int64
print(arr.shape)        # (3, 4)
print(arr.strides)      # (32, 8) — bytes to jump per axis
print(arr.flags)        # C_CONTIGUOUS: True, F_CONTIGUOUS: False
print(arr.data)         # <memory at 0x...>
print(arr.nbytes)       # 96 bytes (12 elements * 8 bytes)
```

**Strides** define how many bytes to skip to reach the next element along each axis. For a C-contiguous (row-major) int64 array with shape (3, 4):
- stride[0] = 4 * 8 = 32 bytes (jump an entire row)
- stride[1] = 8 bytes (jump one element)

```python
# C-order (row-major) vs Fortran-order (column-major)
c_arr = np.array([[1, 2, 3], [4, 5, 6]], order='C')
f_arr = np.array([[1, 2, 3], [4, 5, 6]], order='F')

print(c_arr.strides)  # (24, 8) — rows contiguous
print(f_arr.strides)  # (8, 16) — columns contiguous

# Performance implication: iterate along contiguous axis
# Row iteration on C-order is fast; column iteration on F-order is fast
```

**dtypes** define element interpretation:

```python
# Common dtypes and their sizes
dtypes_info = {
    'float16': 2,   # half precision
    'float32': 4,   # single precision
    'float64': 8,   # double precision (default)
    'int8': 1,      # -128 to 127
    'int16': 2,     # -32768 to 32767
    'int32': 4,     # ~2 billion range
    'int64': 8,     # default integer
    'bool': 1,      # True/False
    'complex128': 16,
}

# Structured arrays — heterogeneous records in contiguous memory
dt = np.dtype([
    ('timestamp', 'datetime64[ns]'),
    ('value', 'float64'),
    ('category', 'U10'),
    ('flag', 'bool')
])
records = np.zeros(1000, dtype=dt)
records['timestamp'][0] = np.datetime64('2026-01-15T10:30:00')
records['value'][0] = 42.5
records['category'][0] = 'sensor_A'
```

### Vectorization and Broadcasting

Vectorization is the single most important concept for NumPy performance. When you write `a + b` on two arrays, NumPy does not loop in Python — it dispatches the operation to a compiled C routine that iterates over contiguous memory with CPU-level optimizations (SIMD instructions, cache-line prefetching, loop unrolling). The overhead of the Python interpreter is paid once per operation, not once per element.

This means that the performance gap between vectorized and loop-based code grows with array size. For small arrays (< 100 elements), the dispatch overhead may make NumPy slower than a raw loop. For large arrays (> 10K elements), the compiled code path dominates and delivers 10-100x speedups.

```python
# BAD: Python loop — ~100x slower
def normalize_loop(arr):
    result = np.empty_like(arr)
    mean = arr.mean()
    std = arr.std()
    for i in range(len(arr)):
        result[i] = (arr[i] - mean) / std
    return result

# GOOD: Vectorized — single pass through compiled code
def normalize_vectorized(arr):
    return (arr - arr.mean()) / arr.std()

# Benchmark
data = np.random.randn(1_000_000)
# normalize_loop: ~850ms
# normalize_vectorized: ~8ms
```

**Broadcasting rules** allow operations between arrays of different shapes without copying data. When two arrays have different shapes, NumPy checks compatibility from the trailing dimensions backward. Broadcasting avoids the memory cost of replicating data — the smaller array is logically stretched without allocating a full-size copy. This makes operations like subtracting column means from a matrix both memory-efficient and fast.

1. Arrays are right-aligned by shape
2. Dimensions of size 1 are stretched to match
3. Incompatible dimensions (neither equal nor 1) raise an error

```python
# Broadcasting examples
a = np.arange(12).reshape(3, 4)   # shape (3, 4)
b = np.array([1, 2, 3, 4])        # shape (4,) → broadcast to (3, 4)
c = np.array([[10], [20], [30]])   # shape (3, 1) → broadcast to (3, 4)

result_ab = a + b   # each row gets b added
result_ac = a + c   # each column gets c added
result_bc = b + c   # outer addition: shape (3, 4)

# Practical: standardize columns independently
matrix = np.random.randn(1000, 50)
col_means = matrix.mean(axis=0)    # shape (50,)
col_stds = matrix.std(axis=0)      # shape (50,)
standardized = (matrix - col_means) / col_stds  # broadcasts across rows
```

### Universal Functions (ufuncs)

Ufuncs (universal functions) are the core mechanism behind NumPy's vectorized operations. Every arithmetic operator, trigonometric function, and comparison on arrays ultimately calls a ufunc. Ufuncs support broadcasting, automatic type promotion (e.g., int + float yields float), and output arrays. They also expose reduction methods (`.reduce`, `.accumulate`, `.outer`) that implement common patterns without Python-level loops. Understanding ufuncs matters because custom performance-critical code should target the ufunc interface rather than Python-level iteration.

```python
# Arithmetic ufuncs
np.add(a, b)          # a + b
np.multiply(a, b)     # a * b
np.power(a, 2)        # a ** 2
np.mod(a, 3)          # a % 3

# Trigonometric
angles = np.linspace(0, 2*np.pi, 100)
np.sin(angles)
np.cos(angles)

# Comparison (returns boolean array)
np.greater(a, 5)      # a > 5
np.logical_and(a > 2, a < 8)

# Reduction methods on ufuncs
np.add.reduce([1, 2, 3, 4])          # 10 (cumulative sum)
np.add.accumulate([1, 2, 3, 4])      # [1, 3, 6, 10]
np.multiply.outer([1, 2, 3], [4, 5]) # outer product

# Custom ufunc via np.frompyfunc (slower than compiled, but vectorizes interface)
def custom_clip(x, low, high):
    return min(max(x, low), high)

clip_ufunc = np.frompyfunc(custom_clip, 3, 1)
clip_ufunc(np.array([1, 5, 10, 15]), 3, 12)
```

### Linear Algebra

```python
from numpy.linalg import inv, det, eig, svd, solve, norm, qr

A = np.array([[3, 1], [1, 2]], dtype=np.float64)
b_vec = np.array([9, 8])

# Solve Ax = b
x = solve(A, b_vec)  # more numerically stable than inv(A) @ b

# Decompositions
eigenvalues, eigenvectors = eig(A)
U, sigma, Vt = svd(A)
Q, R = qr(A)

# Matrix operations
print(det(A))          # determinant
print(norm(A, 'fro'))  # Frobenius norm
print(A @ A.T)         # matrix multiply (prefer @ over np.dot for clarity)

# Batch linear algebra — solve many systems at once
# Shape (100, 3, 3) @ shape (100, 3) → shape (100, 3)
batch_A = np.random.randn(100, 3, 3)
batch_b = np.random.randn(100, 3)
batch_x = np.linalg.solve(batch_A, batch_b)
```

### Random Number Generation (Generator API)

The legacy `np.random.seed()` global state API is deprecated. Use the Generator API for reproducibility and thread safety.

```python
from numpy.random import default_rng

rng = default_rng(seed=42)  # PCG64 by default

# Distributions
samples_normal = rng.normal(loc=0, scale=1, size=(1000, 10))
samples_uniform = rng.uniform(low=0, high=1, size=5000)
samples_poisson = rng.poisson(lam=5, size=1000)
samples_binomial = rng.binomial(n=10, p=0.3, size=1000)
samples_exponential = rng.exponential(scale=2.0, size=1000)

# Permutations and choices
indices = rng.permutation(100)
bootstrap_sample = rng.choice(data, size=len(data), replace=True)

# Parallel streams for reproducibility across workers
from numpy.random import SeedSequence, PCG64

ss = SeedSequence(12345)
child_seeds = ss.spawn(4)  # 4 independent streams
rngs = [default_rng(PCG64(s)) for s in child_seeds]
```

### Performance: NumPy vs Python Loops

```python
import time

n = 10_000_000

# Python list comprehension
py_list = list(range(n))
start = time.perf_counter()
result_py = [x * 2 + 1 for x in py_list]
time_py = time.perf_counter() - start

# NumPy vectorized
np_arr = np.arange(n)
start = time.perf_counter()
result_np = np_arr * 2 + 1
time_np = time.perf_counter() - start

print(f"Python: {time_py:.3f}s")   # ~1.5s
print(f"NumPy:  {time_np:.3f}s")   # ~0.015s
print(f"Speedup: {time_py/time_np:.0f}x")  # ~100x

# Where NumPy loses: element-wise branching with Python objects
# Solution: use np.where, np.select, or np.piecewise
conditions = [np_arr < 100, np_arr < 1000, np_arr >= 1000]
choices = [np_arr * 10, np_arr * 5, np_arr]
result = np.select(conditions, choices)
```

---

## 2. Pandas Core

### Series and DataFrame Internals

A DataFrame is a dict-like container of Series objects sharing a common Index. Each Series wraps a NumPy array (or Extension Array) plus an Index. Internally, pandas groups columns by dtype into "blocks" of contiguous memory (the BlockManager). This means columns of the same dtype share a single 2D NumPy array, which makes column-wise operations on same-dtype groups efficient. The Copy-on-Write (CoW) mode introduced in pandas 2.0 and defaulting in 3.0 changes this: modifications create a lazy copy, eliminating a class of mutation bugs where a view of a DataFrame accidentally modifies the parent.

Understanding the BlockManager matters for performance: adding a single float column to an all-integer DataFrame triggers a new block allocation, while operations on columns within the same block can share memory. The PyArrow backend (available since pandas 2.0) replaces the BlockManager with Apache Arrow's columnar format, offering better memory efficiency, native string support without Python object overhead, and interoperability with other Arrow-based tools.

```python
import pandas as pd

# Series — 1D labeled array
s = pd.Series([10, 20, 30], index=['a', 'b', 'c'], name='values', dtype='int64')
print(s.array)   # underlying ExtensionArray or ndarray
print(s.index)   # Index(['a', 'b', 'c'], dtype='object')

# DataFrame — 2D labeled structure
df = pd.DataFrame({
    'timestamp': pd.date_range('2026-01-01', periods=5, freq='h'),
    'value': [1.1, 2.2, 3.3, 4.4, 5.5],
    'category': pd.Categorical(['A', 'B', 'A', 'B', 'A']),
    'flag': pd.array([True, False, True, None, True], dtype='boolean'),
})

# Internal block structure
print(df._mgr)  # BlockManager showing how columns group by dtype
```

### Index Types

```python
# RangeIndex — default, memory-efficient (stores only start/stop/step)
df_range = pd.DataFrame({'x': range(1_000_000)})
print(df_range.index)  # RangeIndex(start=0, stop=1000000, step=1)
print(df_range.index.memory_usage())  # 128 bytes regardless of size

# DatetimeIndex — time series foundation
dti = pd.DatetimeIndex(
    pd.date_range('2026-01-01', periods=365, freq='D', tz='UTC')
)
# Enables .loc['2026-03'], slicing by date strings, resampling

# MultiIndex — hierarchical indexing
arrays = [
    ['NYC', 'NYC', 'LA', 'LA'],
    ['2025', '2026', '2025', '2026']
]
mi = pd.MultiIndex.from_arrays(arrays, names=['city', 'year'])
df_multi = pd.DataFrame({'revenue': [100, 120, 80, 95]}, index=mi)
df_multi.loc['NYC']           # slice by first level
df_multi.loc[('NYC', '2026')] # exact multi-level lookup

# CategoricalIndex — for repeated string values
cat_idx = pd.CategoricalIndex(['low', 'medium', 'high', 'low', 'medium'],
                               categories=['low', 'medium', 'high'],
                               ordered=True)
```

### Data Loading

```python
# CSV — most common, many options
df = pd.read_csv(
    'data.csv',
    dtype={'user_id': 'int32', 'category': 'category'},
    parse_dates=['created_at'],
    usecols=['user_id', 'category', 'amount', 'created_at'],
    na_values=['', 'NULL', 'N/A'],
    low_memory=False,  # avoid mixed-type inference across chunks
)

# Parquet — columnar, compressed, preserves dtypes
df = pd.read_parquet('data.parquet', columns=['col_a', 'col_b'])
df.to_parquet('output.parquet', engine='pyarrow', compression='zstd')

# JSON — nested structures
df = pd.read_json('data.json', orient='records', lines=True)
# For nested JSON:
import json
with open('nested.json') as f:
    raw = json.load(f)
df = pd.json_normalize(raw, record_path='events', meta=['user_id', 'session'])

# SQL — via SQLAlchemy
from sqlalchemy import create_engine
engine = create_engine('postgresql://user:pass@host:5432/db')
df = pd.read_sql('SELECT * FROM events WHERE date > %s', engine, params=['2026-01-01'])

# Excel — requires openpyxl
df = pd.read_excel('report.xlsx', sheet_name='Q1', header=1, skiprows=[2])

# API responses → DataFrame
import requests
resp = requests.get('https://api.example.com/metrics', timeout=30)
resp.raise_for_status()
df = pd.DataFrame(resp.json()['data'])
```

### Dtype Optimization

Pandas defaults to int64, float64, and Python object for strings. This wastes enormous memory on typical datasets. A 10-column, 10M-row DataFrame with default dtypes can consume 800MB+; with proper downcasting and categorical conversion, the same data often fits in 100-200MB. The dtype optimization pattern below should be standard practice for any dataset exceeding a few hundred thousand rows. The PyArrow backend provides an alternative path: it stores strings as native Arrow strings (variable-length binary, no Python object overhead) and supports nullable types without the float-promotion hack that pandas uses when an integer column contains NaN values.

```python
# Default dtypes are wasteful
df = pd.read_csv('large_file.csv')
print(df.memory_usage(deep=True).sum() / 1e6, "MB")

# Downcast integers
for col in df.select_dtypes(include=['int64']).columns:
    df[col] = pd.to_numeric(df[col], downcast='integer')

# Downcast floats
for col in df.select_dtypes(include=['float64']).columns:
    df[col] = pd.to_numeric(df[col], downcast='float')

# Category for low-cardinality strings
for col in df.select_dtypes(include=['object']).columns:
    if df[col].nunique() / len(df) < 0.05:  # <5% unique values
        df[col] = df[col].astype('category')

# Nullable integer (avoids float promotion for int columns with NAs)
df['count'] = df['count'].astype('Int32')  # capital I = nullable
df['active'] = df['active'].astype('boolean')  # nullable boolean

# PyArrow backend — significant memory savings + speed
df_arrow = pd.read_csv('data.csv', dtype_backend='pyarrow')
# Or convert existing:
df_arrow = df.convert_dtypes(dtype_backend='pyarrow')
```

---

## 3. Data Manipulation

### Selection

```python
# loc — label-based (inclusive of both endpoints)
df.loc[0:5, 'col_a':'col_c']          # rows 0-5, columns col_a through col_c
df.loc[df['status'] == 'active', :]     # boolean mask

# iloc — integer position-based (exclusive of end)
df.iloc[0:5, 0:3]                       # first 5 rows, first 3 columns
df.iloc[-10:]                            # last 10 rows

# at/iat — scalar access (faster than loc/iloc for single values)
val = df.at[42, 'amount']               # label-based scalar
val = df.iat[42, 3]                     # position-based scalar

# Boolean indexing with multiple conditions
mask = (df['amount'] > 100) & (df['category'] == 'premium') & df['active']
filtered = df.loc[mask]

# query() — string expression, often more readable for complex filters
filtered = df.query(
    'amount > 100 and category == "premium" and active == True'
)
# query() with variables
threshold = 100
cat = 'premium'
filtered = df.query('amount > @threshold and category == @cat')

# isin for multiple values
filtered = df[df['status'].isin(['active', 'pending'])]

# between for ranges
filtered = df[df['amount'].between(50, 200)]
```

### Transformation

```python
# apply — row/column-wise arbitrary function (slow for simple ops, use vectorized first)
df['log_amount'] = df['amount'].apply(np.log1p)

# map — element-wise on Series (good for lookups)
status_map = {'active': 1, 'inactive': 0, 'pending': 0.5}
df['status_code'] = df['status'].map(status_map)

# transform — returns same-shape result (useful in groupby)
df['amount_zscore'] = df.groupby('category')['amount'].transform(
    lambda x: (x - x.mean()) / x.std()
)

# pipe — chain operations for readability
def remove_outliers(df, col, n_std=3):
    mean, std = df[col].mean(), df[col].std()
    return df[df[col].between(mean - n_std*std, mean + n_std*std)]

def add_derived_columns(df):
    return df.assign(
        amount_log=np.log1p(df['amount']),
        days_since=( pd.Timestamp('2026-05-07') - df['created_at']).dt.days,
    )

result = (
    df
    .pipe(remove_outliers, 'amount')
    .pipe(add_derived_columns)
    .query('days_since < 90')
)
```

### Reshaping

```python
# melt — wide to long
df_wide = pd.DataFrame({
    'id': [1, 2],
    'jan_revenue': [100, 200],
    'feb_revenue': [110, 210],
    'mar_revenue': [120, 220],
})
df_long = df_wide.melt(
    id_vars='id',
    value_vars=['jan_revenue', 'feb_revenue', 'mar_revenue'],
    var_name='month',
    value_name='revenue'
)

# pivot — long to wide (unique values required)
df_pivoted = df_long.pivot(index='id', columns='month', values='revenue')

# pivot_table — aggregation for non-unique combinations
pt = df.pivot_table(
    values='amount',
    index='category',
    columns='region',
    aggfunc=['mean', 'sum', 'count'],
    fill_value=0,
    margins=True  # adds All row/column
)

# stack/unstack — move index levels to/from columns
stacked = pt.stack(level='region')
unstacked = df_multi.unstack(level='year')

# explode — expand list-valued cells into rows
df_lists = pd.DataFrame({
    'id': [1, 2],
    'tags': [['python', 'pandas'], ['numpy', 'scipy', 'sklearn']]
})
df_exploded = df_lists.explode('tags')
# id=1 gets 2 rows, id=2 gets 3 rows
```

### Merging

```python
# merge — SQL-style joins
left = pd.DataFrame({'key': ['a', 'b', 'c'], 'val_l': [1, 2, 3]})
right = pd.DataFrame({'key': ['b', 'c', 'd'], 'val_r': [4, 5, 6]})

inner = pd.merge(left, right, on='key', how='inner')   # b, c
left_j = pd.merge(left, right, on='key', how='left')   # a, b, c
outer = pd.merge(left, right, on='key', how='outer')    # a, b, c, d

# Multi-key merge
merged = pd.merge(
    orders, customers,
    left_on=['customer_id', 'region'],
    right_on=['id', 'region'],
    how='left',
    suffixes=('_order', '_customer'),
    validate='m:1',  # ensure no unexpected duplicates
    indicator=True   # adds _merge column showing join status
)

# merge_asof — nearest-key join (critical for time series)
trades = pd.DataFrame({
    'time': pd.to_datetime(['10:01', '10:03', '10:06']),
    'price': [100, 101, 99]
})
quotes = pd.DataFrame({
    'time': pd.to_datetime(['10:00', '10:02', '10:04', '10:05']),
    'bid': [99, 100, 100, 101]
})
result = pd.merge_asof(trades, quotes, on='time', direction='backward')

# concat — stack DataFrames
combined = pd.concat([df1, df2, df3], axis=0, ignore_index=True)
# axis=1 for column-wise concatenation (like a horizontal join)

# Performance note: merge on sorted keys with merge_ordered for time-aligned data
```

### String and Datetime Methods

```python
# String accessor (.str)
df['name_clean'] = (
    df['name']
    .str.strip()
    .str.lower()
    .str.replace(r'[^a-z0-9\s]', '', regex=True)
)
df['domain'] = df['email'].str.extract(r'@(.+)$')
df['has_error'] = df['log_message'].str.contains('ERROR|CRITICAL', regex=True)

# Datetime accessor (.dt)
df['created_at'] = pd.to_datetime(df['created_at'], utc=True)
df['year'] = df['created_at'].dt.year
df['month'] = df['created_at'].dt.month
df['day_of_week'] = df['created_at'].dt.day_name()
df['hour'] = df['created_at'].dt.hour
df['is_weekend'] = df['created_at'].dt.dayofweek >= 5
df['quarter'] = df['created_at'].dt.to_period('Q')

# Time deltas
df['days_since_signup'] = (pd.Timestamp.now(tz='UTC') - df['created_at']).dt.days
df['tenure_months'] = (
    (pd.Timestamp.now(tz='UTC') - df['created_at']) / pd.Timedelta(days=30.44)
).astype(int)
```

---

## 4. Aggregation and Grouping

### GroupBy Mechanics (Split-Apply-Combine)

The groupby operation follows the split-apply-combine paradigm: split the data into groups based on one or more keys, apply a function to each group independently, and combine the results into a new data structure. The `groupby()` call itself is lazy — it computes nothing until an action (aggregation, transformation, or filtering) is triggered. This laziness allows pandas to optimize the execution plan.

Internally, pandas builds a mapping from group keys to row indices. For sorted data, this is efficient (groups are contiguous in memory). For unsorted data, pandas must build a hash table of keys. Sorting the DataFrame by the group key before groupby can improve performance by 20-50% for large datasets because it improves cache locality during aggregation.

```python
# Basic groupby
grouped = df.groupby('category')

# The grouped object is lazy — no computation until an action
print(grouped.ngroups)          # number of groups
print(grouped.groups.keys())    # group labels
print(grouped.get_group('A'))   # extract one group

# Single aggregation
df.groupby('category')['amount'].mean()
df.groupby('category')['amount'].agg(['mean', 'median', 'std', 'count'])

# Multiple columns, multiple functions
df.groupby('category').agg(
    total_amount=('amount', 'sum'),
    avg_amount=('amount', 'mean'),
    n_transactions=('amount', 'count'),
    max_value=('value', 'max'),
    first_date=('created_at', 'min'),
    last_date=('created_at', 'max'),
)

# Multi-level groupby
df.groupby(['region', 'category', 'year']).agg(
    revenue=('amount', 'sum'),
    customers=('customer_id', 'nunique'),
)
```

### Transform and Filter in GroupBy

```python
# transform — broadcast group result back to original shape
# Useful for within-group normalization, ranking, filling

# Z-score within each group
df['amount_zscore'] = df.groupby('category')['amount'].transform(
    lambda x: (x - x.mean()) / x.std()
)

# Rank within group
df['rank_in_category'] = df.groupby('category')['amount'].transform('rank', ascending=False)

# Fill missing with group median
df['amount_filled'] = df.groupby('category')['amount'].transform(
    lambda x: x.fillna(x.median())
)

# filter — keep/drop entire groups based on condition
large_groups = df.groupby('category').filter(lambda x: len(x) >= 100)
high_avg_groups = df.groupby('category').filter(lambda x: x['amount'].mean() > 50)
```

### Window Functions

Window functions compute statistics over a sliding or expanding window of observations. They are fundamental for time series analysis, signal processing, and feature engineering. Pandas provides three window types: `rolling` (fixed-size window sliding forward), `expanding` (cumulative from the start of the series), and `ewm` (exponentially weighted, giving more weight to recent observations). Each supports the standard aggregation functions (mean, std, min, max, sum, quantile) plus custom functions via `.apply()`.

The `min_periods` parameter controls how many non-null values are required in the window before producing a result. Setting `min_periods=1` avoids NaN values at the beginning of the series but may produce noisy statistics with very few observations. Time-based windows (e.g., `rolling('7D')`) allow variable numbers of observations per window, which is essential for irregularly spaced time series.

```python
# Rolling — fixed-size sliding window
df = df.sort_values('date')
df['ma_7d'] = df['value'].rolling(window=7).mean()
df['ma_30d'] = df['value'].rolling(window=30).mean()
df['rolling_std'] = df['value'].rolling(window=7).std()
df['rolling_max'] = df['value'].rolling(window=14).max()

# Rolling with min_periods (handle start of series)
df['ma_7d'] = df['value'].rolling(window=7, min_periods=1).mean()

# Time-based rolling (variable number of observations)
df = df.set_index('date')
df['ma_7d'] = df['value'].rolling('7D').mean()  # all obs within 7 days

# Expanding — cumulative from start
df['cumulative_mean'] = df['value'].expanding().mean()
df['cumulative_max'] = df['value'].expanding().max()
df['cumulative_sum'] = df['value'].expanding().sum()

# EWM — Exponentially Weighted Moving average
df['ewma_span10'] = df['value'].ewm(span=10).mean()
df['ewma_halflife_5d'] = df['value'].ewm(halflife='5D').mean()

# Rolling within groups
df['group_rolling_avg'] = (
    df.groupby('category')['value']
    .transform(lambda x: x.rolling(7, min_periods=1).mean())
)
```

### Resample for Time Series

```python
# Resample — time-based groupby
ts = df.set_index('timestamp')

# Downsample: high-freq → low-freq
daily = ts['value'].resample('D').agg(['mean', 'sum', 'count'])
weekly = ts['value'].resample('W-MON').sum()
monthly = ts.resample('ME').agg({
    'value': 'sum',
    'sessions': 'sum',
    'users': 'nunique',
})

# Upsample: low-freq → high-freq
hourly = ts['value'].resample('h').ffill()       # forward fill
hourly_interp = ts['value'].resample('h').interpolate(method='linear')

# Business day resampling
business = ts['value'].resample('B').last()  # last value per business day
```

### Custom Aggregation Functions

```python
# Custom agg function
def weighted_avg(group, value_col='amount', weight_col='quantity'):
    return (group[value_col] * group[weight_col]).sum() / group[weight_col].sum()

# Apply custom function per group
result = df.groupby('category').apply(
    weighted_avg, value_col='price', weight_col='volume',
    include_groups=False
)

# Percentile aggregation
def percentile(n):
    def percentile_(x):
        return x.quantile(n / 100)
    percentile_.__name__ = f'p{n}'
    return percentile_

df.groupby('category')['amount'].agg([
    percentile(25), percentile(50), percentile(75), percentile(95)
])

# Multiple custom functions
def coefficient_of_variation(x):
    return x.std() / x.mean() if x.mean() != 0 else np.nan

df.groupby('region')['revenue'].agg(
    mean='mean',
    cv=coefficient_of_variation,
    iqr=lambda x: x.quantile(0.75) - x.quantile(0.25),
)
```

---

## 5. Performance Optimization

### Memory Optimization

Memory optimization is not premature optimization for data work — it directly impacts whether your analysis fits in RAM and how fast it runs. A DataFrame that consumes 4GB with default dtypes might shrink to 800MB after optimization, turning an out-of-memory failure into a comfortable in-memory workflow. The three pillars of pandas memory optimization are: (1) downcast numeric types to the smallest size that fits the data range, (2) convert low-cardinality string columns to categorical, and (3) use the PyArrow backend for string-heavy datasets. These techniques compose — applying all three can yield 80-90% memory reduction on typical production datasets.

```python
def optimize_dataframe(df):
    """Reduce DataFrame memory footprint by downcasting and categorizing."""
    start_mem = df.memory_usage(deep=True).sum() / 1e6

    for col in df.columns:
        col_type = df[col].dtype

        if col_type == 'object':
            # Convert low-cardinality strings to category
            if df[col].nunique() / len(df) < 0.05:
                df[col] = df[col].astype('category')
        elif col_type in ['int64', 'int32']:
            df[col] = pd.to_numeric(df[col], downcast='integer')
        elif col_type in ['float64', 'float32']:
            df[col] = pd.to_numeric(df[col], downcast='float')

    end_mem = df.memory_usage(deep=True).sum() / 1e6
    print(f"Memory: {start_mem:.1f}MB → {end_mem:.1f}MB "
          f"({100 * (1 - end_mem/start_mem):.0f}% reduction)")
    return df

# PyArrow backend — often 50-70% memory reduction
df = pd.read_parquet('data.parquet', dtype_backend='pyarrow')
```

### Vectorization over iterrows

```python
# NEVER DO THIS for large DataFrames
# iterrows: ~1 row/ms → 1M rows = 1000 seconds
for idx, row in df.iterrows():
    df.at[idx, 'result'] = row['a'] * row['b'] + row['c']

# Vectorized: ~1M rows in milliseconds
df['result'] = df['a'] * df['b'] + df['c']

# For conditional logic, use np.where or np.select
df['tier'] = np.select(
    [df['amount'] > 1000, df['amount'] > 100, df['amount'] > 0],
    ['gold', 'silver', 'bronze'],
    default='none'
)

# When you truly need row-wise logic, use .apply with raw=True
# (passes numpy arrays, ~5-10x faster than default)
df['result'] = df[['a', 'b', 'c']].apply(
    lambda row: row[0] * row[1] + row[2], axis=1, raw=True
)

# Or better: use numba for compiled row operations
from numba import njit

@njit
def compute_metric(a, b, c):
    n = len(a)
    result = np.empty(n)
    for i in range(n):
        result[i] = a[i] * b[i] + np.log(c[i] + 1)
    return result

df['metric'] = compute_metric(df['a'].values, df['b'].values, df['c'].values)
```

### eval() and query() for Large DataFrames

```python
# eval uses numexpr under the hood — less memory for intermediate results
# Useful for DataFrames > 100K rows

# Instead of:
df['result'] = df['a'] + df['b'] * df['c'] - df['d'] / df['e']

# Use:
df.eval('result = a + b * c - d / e', inplace=True)

# Complex expressions
df.eval('''
    profit = revenue - cost
    margin = profit / revenue
    is_profitable = profit > 0
''', inplace=True)

# query for filtering (avoids creating intermediate boolean arrays)
result = df.query('amount > 100 and category in @valid_categories and not is_deleted')
```

### Chunked Processing

```python
# Process large CSV in chunks
chunk_results = []
for chunk in pd.read_csv('huge_file.csv', chunksize=100_000):
    # Process each chunk independently
    processed = chunk.groupby('category')['amount'].sum()
    chunk_results.append(processed)

# Combine chunk results
final = pd.concat(chunk_results).groupby(level=0).sum()

# Generator pattern for memory-bounded processing
def process_large_csv(path, chunksize=100_000):
    reader = pd.read_csv(path, chunksize=chunksize)
    for chunk in reader:
        yield chunk.query('status == "active"')

active_df = pd.concat(process_large_csv('data.csv'))
```

### Polars as Alternative

Polars is a DataFrame library written in Rust that has emerged as the primary alternative to pandas for performance-critical work. Its key architectural advantages are: (1) a lazy query engine that optimizes the entire computation graph before execution (predicate pushdown, projection pushdown, common subexpression elimination), (2) automatic multi-threaded execution without user configuration, (3) Apache Arrow as the memory format (zero-copy interop with other Arrow tools), and (4) a Rust backend that avoids Python's GIL entirely. For analytical workloads on datasets between 1M and 100M rows, Polars typically outperforms pandas by 5-20x while using less memory. The API is different from pandas — it uses an expression system rather than method chaining on DataFrames — but the learning curve is moderate for experienced pandas users.

```python
import polars as pl

# Polars: Rust-based, lazy evaluation, zero-copy, multi-threaded
df_pl = pl.read_csv('data.csv')

# Lazy evaluation — build query plan, execute once
result = (
    pl.scan_csv('data.csv')  # lazy reader
    .filter(pl.col('amount') > 100)
    .group_by('category')
    .agg([
        pl.col('amount').sum().alias('total'),
        pl.col('amount').mean().alias('avg'),
        pl.col('user_id').n_unique().alias('users'),
    ])
    .sort('total', descending=True)
    .collect()  # execute the plan
)

# Expression API — composable, no lambda overhead
df_pl = df_pl.with_columns([
    (pl.col('amount') * pl.col('quantity')).alias('total_value'),
    pl.col('created_at').str.to_datetime('%Y-%m-%d').alias('date'),
    pl.when(pl.col('amount') > 1000).then(pl.lit('high'))
      .when(pl.col('amount') > 100).then(pl.lit('medium'))
      .otherwise(pl.lit('low')).alias('tier'),
])

# Window functions (no groupby/transform split needed)
df_pl = df_pl.with_columns([
    pl.col('amount').mean().over('category').alias('category_avg'),
    pl.col('amount').rank().over('category').alias('rank_in_category'),
])
```

### Dask for Out-of-Core

```python
import dask.dataframe as dd

# Dask mirrors pandas API but operates on partitions
ddf = dd.read_parquet('data/*.parquet')  # reads metadata, lazy

# Build computation graph
result = (
    ddf
    .query('status == "active"')
    .groupby('category')
    .agg({'amount': ['sum', 'mean'], 'user_id': 'nunique'})
)

# Execute — triggers actual computation
result_pd = result.compute()  # returns pandas DataFrame

# Persist in memory for repeated use
ddf_cached = ddf.persist()  # distributed memory (requires cluster)
```

---

## 6. SciPy and Statistical Analysis

### Hypothesis Testing

Statistical hypothesis testing provides the framework for making decisions from data under uncertainty. The core workflow is: (1) state a null hypothesis H0 (typically "no effect" or "no difference"), (2) choose a test statistic and significance level alpha (usually 0.05), (3) compute the test statistic from the data, (4) compare the p-value to alpha to decide whether to reject H0. Critical considerations: p-values are not the probability that H0 is true; they measure how surprising the data would be if H0 were true. Multiple testing requires correction (Bonferroni, Benjamini-Hochberg). Effect size and confidence intervals are often more informative than bare p-values. Always check test assumptions (normality, equal variance, independence) before interpreting results.

```python
from scipy import stats

# Independent samples t-test
group_a = df[df['variant'] == 'control']['metric'].values
group_b = df[df['variant'] == 'treatment']['metric'].values

t_stat, p_value = stats.ttest_ind(group_a, group_b, equal_var=False)  # Welch's t-test
print(f"t={t_stat:.3f}, p={p_value:.4f}")

# Paired t-test (before/after on same subjects)
t_stat, p_value = stats.ttest_rel(before_scores, after_scores)

# Chi-squared test for categorical variables
contingency = pd.crosstab(df['treatment'], df['outcome'])
chi2, p_value, dof, expected = stats.chi2_contingency(contingency)

# ANOVA — compare means across 3+ groups
groups = [df[df['segment'] == s]['revenue'].values for s in df['segment'].unique()]
f_stat, p_value = stats.f_oneway(*groups)

# Non-parametric: Mann-Whitney U (doesn't assume normality)
u_stat, p_value = stats.mannwhitneyu(group_a, group_b, alternative='two-sided')

# Kruskal-Wallis (non-parametric ANOVA)
h_stat, p_value = stats.kruskal(*groups)

# Kolmogorov-Smirnov test (distribution comparison)
ks_stat, p_value = stats.kstest(data, 'norm', args=(data.mean(), data.std()))
```

### Confidence Intervals and Effect Size

```python
import numpy as np
from scipy import stats

def confidence_interval(data, confidence=0.95):
    """Compute confidence interval for the mean."""
    n = len(data)
    mean = np.mean(data)
    se = stats.sem(data)
    h = se * stats.t.ppf((1 + confidence) / 2, n - 1)
    return mean - h, mean, mean + h

# Bootstrap confidence interval (non-parametric)
def bootstrap_ci(data, statistic=np.mean, n_boot=10000, confidence=0.95):
    rng = np.random.default_rng(42)
    boot_stats = np.array([
        statistic(rng.choice(data, size=len(data), replace=True))
        for _ in range(n_boot)
    ])
    alpha = (1 - confidence) / 2
    return np.percentile(boot_stats, [100*alpha, 50, 100*(1-alpha)])

# Cohen's d (effect size)
def cohens_d(group1, group2):
    n1, n2 = len(group1), len(group2)
    var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
    pooled_std = np.sqrt(((n1-1)*var1 + (n2-1)*var2) / (n1+n2-2))
    return (np.mean(group1) - np.mean(group2)) / pooled_std

effect = cohens_d(group_a, group_b)
# |d| < 0.2: negligible, 0.2-0.5: small, 0.5-0.8: medium, > 0.8: large
```

### Power Analysis

```python
from statsmodels.stats.power import TTestIndPower, NormalIndPower

power_analysis = TTestIndPower()

# Calculate required sample size
sample_size = power_analysis.solve_power(
    effect_size=0.3,    # expected Cohen's d
    alpha=0.05,         # significance level
    power=0.8,          # desired power (1 - Type II error)
    ratio=1.0,          # ratio of group sizes
    alternative='two-sided'
)
print(f"Required n per group: {int(np.ceil(sample_size))}")

# Calculate achievable power given sample size
achieved_power = power_analysis.solve_power(
    effect_size=0.3,
    alpha=0.05,
    nobs1=500,
    ratio=1.0,
    alternative='two-sided'
)
print(f"Achieved power: {achieved_power:.3f}")
```

### Regression

```python
from scipy import stats
import statsmodels.api as sm

# Simple linear regression (scipy)
slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

# Multiple linear regression (statsmodels — full statistical output)
X = sm.add_constant(df[['feature1', 'feature2', 'feature3']])
model = sm.OLS(df['target'], X).fit()
print(model.summary())
# Gives: coefficients, std errors, t-stats, p-values, R², F-stat, AIC/BIC

# Logistic regression
X = sm.add_constant(df[['score', 'age', 'tenure']])
logit_model = sm.Logit(df['churn'], X).fit()
print(logit_model.summary())
odds_ratios = np.exp(logit_model.params)

# Robust regression (handles outliers)
rlm_model = sm.RLM(df['target'], X, M=sm.robust.norms.HuberT()).fit()
```

### Interpolation and Optimization

```python
from scipy.interpolate import interp1d, CubicSpline
from scipy.optimize import minimize, minimize_scalar, curve_fit

# Interpolation
x_known = np.array([0, 1, 2, 3, 4, 5])
y_known = np.array([0, 0.8, 0.9, 0.1, -0.8, -1.0])

# Linear interpolation
f_linear = interp1d(x_known, y_known)

# Cubic spline (smooth)
cs = CubicSpline(x_known, y_known)
x_fine = np.linspace(0, 5, 100)
y_smooth = cs(x_fine)

# Curve fitting
def model_func(x, a, b, c):
    return a * np.exp(-b * x) + c

popt, pcov = curve_fit(model_func, x_data, y_data)
# popt = optimal parameters, pcov = covariance matrix

# Optimization
def objective(params):
    a, b = params
    predictions = a * x_data + b
    return np.sum((predictions - y_data) ** 2)

result = minimize(objective, x0=[0, 0], method='Nelder-Mead')
print(f"Optimal params: {result.x}, Min loss: {result.fun}")
```

---

## 7. Data Cleaning Patterns

### Duplicate Detection and Removal

Duplicates in production data arise from multiple sources: ETL failures that replay records, user double-submissions, merge operations that produce cartesian products, and CDC (change data capture) systems that emit multiple versions of the same record. Detection strategy depends on the data: exact duplicates (all columns identical) are easy to spot with `duplicated()`, but real-world deduplication typically requires fuzzy matching on a subset of columns, handling of case/whitespace differences, and business rules about which record to keep (most recent, most complete, highest priority source).

```python
# Exact duplicates
n_dupes = df.duplicated().sum()
df_deduped = df.drop_duplicates()

# Duplicates on subset of columns
df_deduped = df.drop_duplicates(subset=['email', 'phone'], keep='last')

# Find duplicate groups for manual review
dupes = df[df.duplicated(subset=['name', 'address'], keep=False)]
dupe_groups = dupes.groupby(['name', 'address']).apply(
    lambda g: g.index.tolist(), include_groups=False
)

# Near-duplicate detection with hashing
import hashlib

def content_hash(row, cols):
    content = '|'.join(str(row[c]).lower().strip() for c in cols)
    return hashlib.md5(content.encode()).hexdigest()

df['content_hash'] = df.apply(content_hash, axis=1, cols=['name', 'email', 'phone'])
df_deduped = df.drop_duplicates(subset='content_hash', keep='first')
```

### Data Type Coercion

```python
# Safe numeric conversion
df['amount'] = pd.to_numeric(df['amount'], errors='coerce')  # invalid → NaN

# Date parsing with multiple formats
def robust_date_parse(series):
    """Try multiple date formats."""
    for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d-%m-%Y', '%Y%m%d']:
        try:
            return pd.to_datetime(series, format=fmt)
        except (ValueError, TypeError):
            continue
    return pd.to_datetime(series, infer_datetime_format=True, errors='coerce')

df['date'] = robust_date_parse(df['date_raw'])

# Boolean coercion from messy data
bool_map = {
    'yes': True, 'no': False, 'y': True, 'n': False,
    '1': True, '0': False, 'true': True, 'false': False,
    'si': True, 'on': True, 'off': False,
}
df['active'] = df['active_raw'].str.lower().str.strip().map(bool_map)
```

### Standardization

```python
import re

def standardize_phone(phone):
    """Normalize phone to E.164-like format."""
    if pd.isna(phone):
        return None
    digits = re.sub(r'[^\d+]', '', str(phone))
    if digits.startswith('00'):
        digits = '+' + digits[2:]
    elif not digits.startswith('+'):
        digits = '+1' + digits  # assume US if no country code
    if len(digits) < 10 or len(digits) > 15:
        return None
    return digits

df['phone_clean'] = df['phone'].apply(standardize_phone)

def standardize_address(addr):
    """Basic address normalization."""
    if pd.isna(addr):
        return None
    addr = addr.upper().strip()
    replacements = {
        r'\bST\.?\b': 'STREET', r'\bAVE\.?\b': 'AVENUE',
        r'\bBLVD\.?\b': 'BOULEVARD', r'\bDR\.?\b': 'DRIVE',
        r'\bRD\.?\b': 'ROAD', r'\bAPT\.?\b': 'APT',
        r'\s+': ' ',
    }
    for pattern, replacement in replacements.items():
        addr = re.sub(pattern, replacement, addr)
    return addr

# Date standardization
def standardize_date(date_str):
    """Parse dates from various formats to ISO 8601."""
    formats = ['%m/%d/%Y', '%d-%m-%Y', '%Y%m%d', '%B %d, %Y', '%d %b %Y']
    for fmt in formats:
        try:
            return pd.Timestamp(date_str).strftime('%Y-%m-%d')
        except (ValueError, TypeError):
            continue
    return None
```

### Fuzzy Matching

Fuzzy matching addresses the reality that the same entity appears differently across data sources: "Apple Inc.", "APPLE INC", "Apple, Incorporated", and "Apple Computer Inc." all refer to the same company. String similarity algorithms (Levenshtein distance, Jaro-Winkler, token-based ratios) quantify how close two strings are. For production entity resolution at scale, the key challenge is performance: comparing every pair in two 100K-record datasets yields 10 billion comparisons. The solution is blocking — narrow the candidate pairs using cheap heuristics (same first letter, same ZIP code, phonetic encoding) before applying expensive fuzzy comparisons.

The `rapidfuzz` library (a faster drop-in replacement for `fuzzywuzzy`, written in C++) and the `recordlinkage` library (which implements blocking, comparison, and classification in a structured pipeline) are the standard tools for this work in Python.

```python
from rapidfuzz import fuzz, process

# Single pair comparison
score = fuzz.ratio("Apple Inc.", "Apple Incorporated")  # ~75
score = fuzz.token_sort_ratio("John Smith Jr", "Smith, John Jr.")  # ~90

# Match against a list of known values
known_companies = ['Apple Inc.', 'Google LLC', 'Microsoft Corp.', 'Amazon.com Inc.']

def fuzzy_match_company(name, choices=known_companies, threshold=80):
    """Match company name against known list."""
    if pd.isna(name):
        return None, 0
    result = process.extractOne(name, choices, scorer=fuzz.token_sort_ratio)
    if result and result[1] >= threshold:
        return result[0], result[1]
    return None, 0

# Apply to DataFrame
matches = df['company_raw'].apply(
    lambda x: pd.Series(fuzzy_match_company(x), index=['matched', 'score'])
)
df = pd.concat([df, matches], axis=1)

# Record linkage for entity resolution
import recordlinkage

indexer = recordlinkage.Index()
indexer.sortedneighbourhood('last_name', window=3)
candidate_pairs = indexer.index(df_a, df_b)

compare = recordlinkage.Compare()
compare.string('first_name', 'first_name', method='jarowinkler', threshold=0.85)
compare.string('last_name', 'last_name', method='jarowinkler', threshold=0.85)
compare.exact('date_of_birth', 'date_of_birth')
compare.string('address', 'address', method='levenshtein', threshold=0.7)

features = compare.compute(candidate_pairs, df_a, df_b)
matches = features[features.sum(axis=1) >= 3]  # at least 3 matching fields
```

### Pipeline Pattern for Cleaning

Ad-hoc cleaning scripts become maintenance nightmares as datasets evolve. The pipeline pattern (borrowed from scikit-learn) encapsulates each cleaning step as a transformer with `fit` and `transform` methods. Benefits: (1) reproducibility — the same pipeline applies identically to train and test data, (2) composability — swap, add, or remove steps without rewriting the rest, (3) serialization — pickle the fitted pipeline for deployment, (4) auditability — each step is named and inspectable. For data cleaning specifically, the `fit` step learns parameters from the training data (e.g., outlier bounds, category mappings, imputation values) and `transform` applies them, ensuring no data leakage from test/production data into learned parameters.

```python
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline

class ColumnDropper(BaseEstimator, TransformerMixin):
    def __init__(self, columns):
        self.columns = columns

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return X.drop(columns=self.columns, errors='ignore')

class TypeOptimizer(BaseEstimator, TransformerMixin):
    def __init__(self, category_threshold=0.05):
        self.category_threshold = category_threshold
        self.category_cols_ = []

    def fit(self, X, y=None):
        for col in X.select_dtypes(include='object').columns:
            if X[col].nunique() / len(X) < self.category_threshold:
                self.category_cols_.append(col)
        return self

    def transform(self, X):
        X = X.copy()
        for col in self.category_cols_:
            if col in X.columns:
                X[col] = X[col].astype('category')
        return X

class OutlierClipper(BaseEstimator, TransformerMixin):
    def __init__(self, columns, n_std=3):
        self.columns = columns
        self.n_std = n_std
        self.bounds_ = {}

    def fit(self, X, y=None):
        for col in self.columns:
            mean, std = X[col].mean(), X[col].std()
            self.bounds_[col] = (mean - self.n_std*std, mean + self.n_std*std)
        return self

    def transform(self, X):
        X = X.copy()
        for col, (lower, upper) in self.bounds_.items():
            X[col] = X[col].clip(lower, upper)
        return X

class DateParser(BaseEstimator, TransformerMixin):
    def __init__(self, columns):
        self.columns = columns

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X = X.copy()
        for col in self.columns:
            X[col] = pd.to_datetime(X[col], errors='coerce', utc=True)
        return X

# Compose the pipeline
cleaning_pipeline = Pipeline([
    ('drop_cols', ColumnDropper(['internal_id', 'debug_info'])),
    ('parse_dates', DateParser(['created_at', 'updated_at'])),
    ('optimize_types', TypeOptimizer(category_threshold=0.05)),
    ('clip_outliers', OutlierClipper(['amount', 'latency_ms'])),
])

df_clean = cleaning_pipeline.fit_transform(df_raw)
```

---

## 8. Time Series Analysis

### Datetime Indexing and Resampling

Time series data requires special handling because the index carries semantic meaning — it determines which operations are valid and how they execute. A DataFrame with a proper DatetimeIndex gains access to pandas' time series machinery: date-string slicing (`ts['2026-03']`), frequency-aware operations, resampling, and time-zone handling. The index should be monotonic (sorted) and ideally have a known frequency. Missing timestamps create gaps that propagate through rolling windows and resampling; `reindex` with a complete date range followed by interpolation is the standard fix.

Resampling is conceptually a time-based groupby: you specify a target frequency and an aggregation method. Downsampling (high-freq to low-freq) reduces data volume and requires choosing an aggregation. Upsampling (low-freq to high-freq) creates gaps that must be filled via forward-fill, interpolation, or explicit NaN handling.

```python
# Create proper time series
ts = df.set_index('timestamp').sort_index()
ts.index = pd.DatetimeIndex(ts.index, freq='infer')

# Slice by date
jan_2026 = ts['2026-01']
q1 = ts['2026-01':'2026-03']

# Resample with multiple aggregations
daily = ts.resample('D').agg({
    'value': ['mean', 'std', 'min', 'max'],
    'count': 'sum',
})

# Handle missing timestamps
full_idx = pd.date_range(ts.index.min(), ts.index.max(), freq='h')
ts_complete = ts.reindex(full_idx)
ts_complete['value'] = ts_complete['value'].interpolate(method='time')
```

### Rolling Statistics and Decomposition

```python
from statsmodels.tsa.seasonal import seasonal_decompose, STL

# Rolling statistics for trend detection
ts['rolling_mean'] = ts['value'].rolling(window=30, center=True).mean()
ts['rolling_std'] = ts['value'].rolling(window=30, center=True).std()

# Classical decomposition
decomposition = seasonal_decompose(
    ts['value'].dropna(),
    model='additive',  # or 'multiplicative'
    period=24          # 24 hours for daily seasonality
)
trend = decomposition.trend
seasonal = decomposition.seasonal
residual = decomposition.resid

# STL decomposition (more robust)
stl = STL(ts['value'].dropna(), period=24, robust=True)
result = stl.fit()
# result.trend, result.seasonal, result.resid
```

### Stationarity Tests

A time series is stationary when its statistical properties (mean, variance, autocorrelation) do not change over time. Most forecasting models (ARIMA, exponential smoothing) assume stationarity, so testing for it is a prerequisite before model fitting. The Augmented Dickey-Fuller (ADF) test has the null hypothesis that the series has a unit root (is non-stationary), while the KPSS test has the opposite null hypothesis (series is stationary). Running both provides a decision matrix: if ADF rejects and KPSS fails to reject, the series is stationary; if ADF fails and KPSS rejects, it is non-stationary and needs differencing; if both reject, the series is trend-stationary (remove the trend, or difference once).

```python
from statsmodels.tsa.stattools import adfuller, kpss

def test_stationarity(series, name='series'):
    """Run ADF and KPSS tests for stationarity."""
    # ADF test: H0 = non-stationary
    adf_result = adfuller(series.dropna(), autolag='AIC')
    adf_stat, adf_p = adf_result[0], adf_result[1]

    # KPSS test: H0 = stationary
    kpss_result = kpss(series.dropna(), regression='c', nlags='auto')
    kpss_stat, kpss_p = kpss_result[0], kpss_result[1]

    print(f"--- {name} ---")
    print(f"ADF:  stat={adf_stat:.4f}, p={adf_p:.4f} "
          f"{'[stationary]' if adf_p < 0.05 else '[non-stationary]'}")
    print(f"KPSS: stat={kpss_stat:.4f}, p={kpss_p:.4f} "
          f"{'[stationary]' if kpss_p > 0.05 else '[non-stationary]'}")

    # Decision matrix:
    # ADF rejects + KPSS fails to reject → stationary
    # ADF fails + KPSS rejects → non-stationary
    # Both reject → trend-stationary (difference once)
    # Both fail → inconclusive

# Make series stationary via differencing
ts_diff = ts['value'].diff().dropna()
test_stationarity(ts_diff, 'first_difference')
```

### Autocorrelation

```python
from statsmodels.tsa.stattools import acf, pacf
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf

# Compute ACF and PACF
acf_values = acf(ts['value'].dropna(), nlags=48)
pacf_values = pacf(ts['value'].dropna(), nlags=48)

# Interpretation for ARIMA order selection:
# ACF tails off, PACF cuts off after lag p → AR(p)
# ACF cuts off after lag q, PACF tails off → MA(q)
# Both tail off → ARMA(p,q)

# Ljung-Box test for white noise (residual diagnostics)
from statsmodels.stats.diagnostic import acorr_ljungbox
lb_result = acorr_ljungbox(residuals, lags=20, return_df=True)
print(lb_result)  # If all p-values > 0.05, residuals are white noise
```

### Basic Forecasting

```python
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.statespace.sarimax import SARIMAX

# ARIMA
model = ARIMA(ts['value'], order=(2, 1, 2))  # (p, d, q)
fitted = model.fit()
print(fitted.summary())

forecast = fitted.forecast(steps=30)
conf_int = fitted.get_forecast(30).conf_int()

# SARIMA (seasonal ARIMA)
model = SARIMAX(
    ts['value'],
    order=(1, 1, 1),
    seasonal_order=(1, 1, 1, 24),  # (P, D, Q, S)
    enforce_stationarity=False,
)
fitted = model.fit(disp=False)
forecast = fitted.forecast(steps=48)

# Exponential Smoothing (Holt-Winters)
model = ExponentialSmoothing(
    ts['value'],
    trend='add',
    seasonal='add',
    seasonal_periods=24,
)
fitted = model.fit()
forecast = fitted.forecast(steps=48)

# Prophet (if installed)
# from prophet import Prophet
# prophet_df = ts.reset_index().rename(columns={'timestamp': 'ds', 'value': 'y'})
# model = Prophet(daily_seasonality=True, yearly_seasonality=True)
# model.fit(prophet_df)
# future = model.make_future_dataframe(periods=30, freq='D')
# forecast = model.predict(future)
```

### Time Series Anomaly Detection

Anomaly detection in time series must account for seasonality, trend, and changing variance. A value that looks anomalous in absolute terms may be perfectly normal for that time of day or season. The three standard approaches are: (1) statistical methods using rolling z-scores or IQR relative to a local window, (2) decomposition-based methods that isolate the residual component and flag extreme residuals, and (3) model-based methods that train a forecasting model and flag points where the prediction error exceeds a threshold. In practice, ensemble approaches that combine multiple detectors and require consensus (2-out-of-3 or 3-out-of-4 methods agree) produce fewer false positives than any single method.

```python
def detect_anomalies_zscore(series, window=24, threshold=3.0):
    """Detect anomalies using rolling z-score."""
    rolling_mean = series.rolling(window=window, center=False).mean()
    rolling_std = series.rolling(window=window, center=False).std()
    z_scores = (series - rolling_mean) / rolling_std
    anomalies = z_scores.abs() > threshold
    return anomalies

def detect_anomalies_iqr(series, window=24, k=1.5):
    """Detect anomalies using rolling IQR method."""
    rolling_q1 = series.rolling(window=window).quantile(0.25)
    rolling_q3 = series.rolling(window=window).quantile(0.75)
    rolling_iqr = rolling_q3 - rolling_q1
    lower = rolling_q1 - k * rolling_iqr
    upper = rolling_q3 + k * rolling_iqr
    anomalies = (series < lower) | (series > upper)
    return anomalies

def detect_anomalies_stl(series, period=24, threshold=3.0):
    """Detect anomalies using STL residuals."""
    stl = STL(series.dropna(), period=period, robust=True)
    result = stl.fit()
    residuals = result.resid
    resid_mean = residuals.mean()
    resid_std = residuals.std()
    anomalies = ((residuals - resid_mean) / resid_std).abs() > threshold
    return anomalies

# Apply multiple methods and take consensus
anomalies_z = detect_anomalies_zscore(ts['value'])
anomalies_iqr = detect_anomalies_iqr(ts['value'])
anomalies_stl = detect_anomalies_stl(ts['value'])

# Consensus: flag as anomaly if at least 2/3 methods agree
consensus = (anomalies_z.astype(int) + anomalies_iqr.astype(int) +
             anomalies_stl.astype(int)) >= 2
ts['is_anomaly'] = consensus
```

---

## 9. Integration with Databases

### SQLAlchemy + Pandas

The standard integration between pandas and relational databases flows through SQLAlchemy. The `read_sql` function accepts either a raw SQL string or a SQLAlchemy `text()` object (preferred for parameter binding and SQL injection prevention). Connection pooling is critical for production use — creating a new database connection per query adds 50-200ms of overhead, while pooled connections are reused instantly. The `to_sql` method handles writes, but its default row-by-row INSERT is extremely slow for large DataFrames; always use `method='multi'` for batch inserts, or COPY-based approaches for PostgreSQL at scale.

The key architectural decision is query pushdown vs pull-and-process: push filtering, joining, and aggregation into the database when the data volume is large (the database's query optimizer, indexes, and compiled execution engine will outperform pandas); pull data into pandas when you need operations that are awkward or impossible in SQL (complex window functions with custom logic, fuzzy matching, ML feature engineering, reshaping operations).

```python
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool

# Connection with pooling
engine = create_engine(
    'postgresql://user:pass@host:5432/analytics',
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args={'options': '-c statement_timeout=30000'}  # 30s timeout
)

# Read with parameterized query (SQL injection safe)
query = text("""
    SELECT user_id, event_type, created_at, properties
    FROM events
    WHERE created_at BETWEEN :start AND :end
    AND event_type IN :event_types
""")
df = pd.read_sql(
    query, engine,
    params={
        'start': '2026-01-01',
        'end': '2026-05-07',
        'event_types': ('login', 'purchase', 'logout'),
    },
    parse_dates=['created_at'],
)

# Write back to database
df_results.to_sql(
    'analysis_results',
    engine,
    if_exists='append',  # 'replace' drops and recreates
    index=False,
    method='multi',      # batch inserts
    chunksize=10000,     # write in chunks
    dtype={              # explicit SQL types
        'user_id': 'INTEGER',
        'score': 'DOUBLE PRECISION',
        'created_at': 'TIMESTAMP WITH TIME ZONE',
    }
)
```

### Chunked Reading for Large Tables

```python
# Read large table in chunks to avoid OOM
def read_large_table(engine, query, chunksize=100_000):
    """Stream large query results in chunks."""
    chunks = pd.read_sql(query, engine, chunksize=chunksize)
    processed = []
    for i, chunk in enumerate(chunks):
        # Process each chunk independently
        chunk_result = chunk.groupby('category').agg(
            total=('amount', 'sum'),
            count=('amount', 'count'),
        )
        processed.append(chunk_result)
        if (i + 1) % 10 == 0:
            print(f"Processed {(i+1) * chunksize:,} rows")

    return pd.concat(processed).groupby(level=0).sum()

# COPY for bulk inserts (PostgreSQL, much faster than INSERT)
from io import StringIO

def bulk_insert_copy(df, table_name, engine):
    """Use COPY FROM for fast bulk insert (psycopg2)."""
    buffer = StringIO()
    df.to_csv(buffer, index=False, header=False, sep='\t', na_rep='\\N')
    buffer.seek(0)

    raw_conn = engine.raw_connection()
    try:
        cursor = raw_conn.cursor()
        cursor.copy_from(buffer, table_name, sep='\t', null='\\N',
                         columns=df.columns.tolist())
        raw_conn.commit()
    finally:
        raw_conn.close()
```

### Query Pushdown vs Pull-and-Process

```python
# BAD: Pull entire table, filter in Python
df = pd.read_sql('SELECT * FROM events', engine)
result = df[df['created_at'] > '2026-04-01'].groupby('type').size()

# GOOD: Push filtering and aggregation to the database
query = text("""
    SELECT event_type, COUNT(*) as cnt
    FROM events
    WHERE created_at > :cutoff
    GROUP BY event_type
    ORDER BY cnt DESC
""")
result = pd.read_sql(query, engine, params={'cutoff': '2026-04-01'})

# HYBRID: Push heavy filtering, pull for complex pandas-specific transforms
query = text("""
    SELECT user_id, event_type, properties, created_at
    FROM events
    WHERE created_at > :cutoff
    AND event_type IN :types
""")
df = pd.read_sql(query, engine, params={
    'cutoff': '2026-04-01',
    'types': ('purchase', 'refund')
})
# Complex window operations that are awkward in SQL
df['cumulative_spend'] = df.groupby('user_id')['amount'].cumsum()
df['days_between'] = df.groupby('user_id')['created_at'].diff().dt.days
```

### Pandas + DuckDB for Analytical Queries

DuckDB is an in-process analytical database (like SQLite, but column-oriented and optimized for OLAP). Its killer feature for data analysts: it reads pandas DataFrames directly via zero-copy (or near-zero-copy) without data serialization, lets you run full SQL against them, and returns results as DataFrames. This means you can mix pandas transformations with SQL queries in the same script, choosing whichever is more expressive for each step. DuckDB's vectorized execution engine typically outperforms pandas by 5-15x on aggregation-heavy queries, and it can read Parquet files directly without loading them into memory first — making it ideal for larger-than-RAM datasets stored in Parquet format.

```python
import duckdb

# DuckDB reads pandas DataFrames directly (zero-copy when possible)
conn = duckdb.connect()

# Register DataFrame as a virtual table
conn.register('events', df_events)
conn.register('users', df_users)

# Run SQL against DataFrames — faster than pandas for complex queries
result = conn.execute("""
    SELECT
        u.segment,
        DATE_TRUNC('month', e.created_at) as month,
        COUNT(DISTINCT e.user_id) as active_users,
        SUM(e.amount) as total_revenue,
        AVG(e.amount) as avg_order_value,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY e.amount) as median_order
    FROM events e
    JOIN users u ON e.user_id = u.id
    WHERE e.event_type = 'purchase'
    GROUP BY u.segment, DATE_TRUNC('month', e.created_at)
    ORDER BY month, total_revenue DESC
""").fetchdf()  # returns pandas DataFrame

# DuckDB can also read Parquet/CSV directly without loading into memory
result = duckdb.sql("""
    SELECT *
    FROM read_parquet('data/events_*.parquet')
    WHERE created_at > '2026-01-01'
""").fetchdf()

# Combine DuckDB SQL with pandas operations
cohort_base = conn.execute("""
    SELECT user_id, MIN(DATE_TRUNC('week', created_at)) as cohort_week
    FROM events WHERE event_type = 'signup'
    GROUP BY user_id
""").fetchdf()

# Then use pandas for the retention matrix calculation
merged = df_events.merge(cohort_base, on='user_id')
merged['weeks_since'] = (
    (merged['created_at'] - merged['cohort_week']).dt.days // 7
)
retention = merged.pivot_table(
    index='cohort_week', columns='weeks_since',
    values='user_id', aggfunc='nunique'
)
```

### asyncpg for High-Performance Async Access

```python
import asyncio
import asyncpg

async def fetch_events(pool, start_date, end_date):
    """Fetch events using async connection pool."""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT user_id, event_type, amount, created_at
            FROM events
            WHERE created_at BETWEEN $1 AND $2
            ORDER BY created_at
        """, start_date, end_date)
        return pd.DataFrame(rows, columns=['user_id', 'event_type', 'amount', 'created_at'])

async def main():
    pool = await asyncpg.create_pool(
        'postgresql://user:pass@host:5432/db',
        min_size=5, max_size=20
    )

    # Parallel fetches for different date ranges
    tasks = [
        fetch_events(pool, f'2026-0{m}-01', f'2026-0{m+1}-01')
        for m in range(1, 5)
    ]
    results = await asyncio.gather(*tasks)
    df = pd.concat(results, ignore_index=True)

    await pool.close()
    return df

# df = asyncio.run(main())
```

---

## 10. Lab Exercises

### Lab 1: Complete Data Analysis Pipeline

Build an end-to-end pipeline: load, clean, transform, analyze, visualize.

```python
"""
Lab 1: E-commerce Transaction Analysis Pipeline
Dataset: transaction records with customer info, product data, and timestamps.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# --- STEP 1: Generate realistic synthetic data ---
rng = np.random.default_rng(42)
n_records = 50_000

customers = pd.DataFrame({
    'customer_id': range(1, 5001),
    'segment': rng.choice(['enterprise', 'mid-market', 'startup'], 5000, p=[0.1, 0.3, 0.6]),
    'region': rng.choice(['EMEA', 'NA', 'APAC', 'LATAM'], 5000, p=[0.25, 0.35, 0.25, 0.15]),
    'signup_date': pd.date_range('2024-01-01', periods=5000, freq='3h'),
})

transactions = pd.DataFrame({
    'tx_id': range(n_records),
    'customer_id': rng.choice(range(1, 5001), n_records),
    'amount': np.round(rng.lognormal(mean=4.0, sigma=1.2, size=n_records), 2),
    'product_category': rng.choice(
        ['SaaS', 'Consulting', 'Hardware', 'Training', 'Support'], n_records,
        p=[0.4, 0.2, 0.15, 0.15, 0.1]
    ),
    'status': rng.choice(['completed', 'refunded', 'pending', 'failed'], n_records,
                          p=[0.85, 0.05, 0.07, 0.03]),
    'created_at': pd.date_range('2025-01-01', periods=n_records, freq='10min'),
})

# Inject some data quality issues
mask_nulls = rng.random(n_records) < 0.02
transactions.loc[mask_nulls, 'amount'] = np.nan
mask_outliers = rng.random(n_records) < 0.005
transactions.loc[mask_outliers, 'amount'] = rng.uniform(50000, 200000, mask_outliers.sum())

# --- STEP 2: Clean ---
print(f"Raw shape: {transactions.shape}")
print(f"Nulls:\n{transactions.isnull().sum()}")
print(f"Duplicates: {transactions.duplicated().sum()}")

# Remove failed transactions
tx_clean = transactions.query('status != "failed"').copy()

# Handle missing amounts: fill with median by category
tx_clean['amount'] = tx_clean.groupby('product_category')['amount'].transform(
    lambda x: x.fillna(x.median())
)

# Clip outliers using IQR per category
def clip_iqr(group, col='amount', k=3.0):
    q1, q3 = group[col].quantile(0.25), group[col].quantile(0.75)
    iqr = q3 - q1
    return group.assign(**{col: group[col].clip(q1 - k*iqr, q3 + k*iqr)})

tx_clean = tx_clean.groupby('product_category', group_keys=False).apply(clip_iqr)

# --- STEP 3: Transform ---
# Merge customer info
df = tx_clean.merge(customers, on='customer_id', how='left')

# Feature engineering
df['month'] = df['created_at'].dt.to_period('M')
df['day_of_week'] = df['created_at'].dt.day_name()
df['hour'] = df['created_at'].dt.hour
df['is_weekend'] = df['created_at'].dt.dayofweek >= 5
df['days_since_signup'] = (df['created_at'] - df['signup_date']).dt.days
df['amount_log'] = np.log1p(df['amount'])

# RFM scoring
snapshot_date = df['created_at'].max() + pd.Timedelta(days=1)
rfm = df.groupby('customer_id').agg(
    recency=('created_at', lambda x: (snapshot_date - x.max()).days),
    frequency=('tx_id', 'count'),
    monetary=('amount', 'sum'),
)
for col in ['recency', 'frequency', 'monetary']:
    rfm[f'{col}_score'] = pd.qcut(
        rfm[col], q=5, labels=[5, 4, 3, 2, 1] if col == 'recency' else [1, 2, 3, 4, 5]
    )

# --- STEP 4: Analyze ---
# Revenue by segment and product
revenue_analysis = df.pivot_table(
    values='amount',
    index='segment',
    columns='product_category',
    aggfunc='sum',
    margins=True,
)
print("\nRevenue by Segment x Product:\n", revenue_analysis.round(0))

# Cohort retention
df['cohort_month'] = df.groupby('customer_id')['created_at'].transform('min').dt.to_period('M')
df['months_since'] = (df['month'] - df['cohort_month']).apply(lambda x: x.n)

cohort_data = df.groupby(['cohort_month', 'months_since']).agg(
    users=('customer_id', 'nunique')
).reset_index()

cohort_sizes = cohort_data[cohort_data['months_since'] == 0].set_index('cohort_month')['users']
retention = cohort_data.pivot(index='cohort_month', columns='months_since', values='users')
retention_pct = retention.div(cohort_sizes, axis=0) * 100

print("\nCohort Retention (%):\n", retention_pct.round(1))

# Statistical test: does enterprise spend more than mid-market?
from scipy import stats
enterprise_amounts = df[df['segment'] == 'enterprise']['amount']
midmarket_amounts = df[df['segment'] == 'mid-market']['amount']
t_stat, p_val = stats.ttest_ind(enterprise_amounts, midmarket_amounts, equal_var=False)
print(f"\nEnterprise vs Mid-Market: t={t_stat:.2f}, p={p_val:.4f}")
```

### Lab 2: Security Log Analysis with Pandas

```python
"""
Lab 2: Security Event Log Analysis
Parse and analyze auth logs, detect brute force, privilege escalation, anomalous access.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# --- Generate synthetic security logs ---
rng = np.random.default_rng(123)
n_events = 200_000

base_time = pd.Timestamp('2026-04-01', tz='UTC')
timestamps = base_time + pd.to_timedelta(
    rng.exponential(scale=120, size=n_events).cumsum(), unit='s'
)

users = [f'user_{i:04d}' for i in range(500)]
ips = [f'10.0.{rng.integers(1,255)}.{rng.integers(1,255)}' for _ in range(1000)]

# Normal events
events = pd.DataFrame({
    'timestamp': timestamps,
    'user': rng.choice(users, n_events),
    'source_ip': rng.choice(ips, n_events),
    'event_type': rng.choice(
        ['login_success', 'login_failure', 'logout', 'password_change',
         'privilege_escalation', 'file_access', 'api_call'],
        n_events,
        p=[0.35, 0.15, 0.20, 0.02, 0.01, 0.15, 0.12]
    ),
    'resource': rng.choice(
        ['/api/data', '/admin/users', '/api/auth', '/files/sensitive',
         '/api/reports', '/dashboard', '/settings'],
        n_events
    ),
    'status_code': rng.choice([200, 201, 401, 403, 404, 500], n_events,
                               p=[0.70, 0.05, 0.10, 0.05, 0.05, 0.05]),
})

# Inject attack patterns: brute force from specific IPs
attack_ips = ['192.168.1.100', '192.168.1.101']
brute_force_events = pd.DataFrame({
    'timestamp': pd.date_range('2026-04-15 02:00', periods=500, freq='2s', tz='UTC'),
    'user': rng.choice(users[:10], 500),
    'source_ip': rng.choice(attack_ips, 500),
    'event_type': 'login_failure',
    'resource': '/api/auth',
    'status_code': 401,
})

events = pd.concat([events, brute_force_events], ignore_index=True).sort_values('timestamp')

# --- Analysis ---

# 1. Brute Force Detection: >10 failures from same IP within 5 minutes
def detect_brute_force(events, threshold=10, window_minutes=5):
    """Detect IPs with excessive login failures in a short window."""
    failures = events[events['event_type'] == 'login_failure'].copy()
    failures = failures.set_index('timestamp').sort_index()

    # Count failures per IP in rolling window
    brute_force_ips = (
        failures.groupby('source_ip')
        .resample(f'{window_minutes}min')
        .size()
        .reset_index(name='failure_count')
    )
    alerts = brute_force_ips[brute_force_ips['failure_count'] >= threshold]
    return alerts

brute_alerts = detect_brute_force(events)
print(f"Brute force alerts: {len(brute_alerts)}")
print(brute_alerts.head(10))

# 2. Privilege Escalation Detection: unusual privilege events
def detect_priv_escalation(events):
    """Flag privilege escalation from users who don't normally access admin."""
    admin_events = events[
        (events['event_type'] == 'privilege_escalation') |
        (events['resource'].str.contains('/admin'))
    ]

    # Users with infrequent admin access
    user_admin_freq = admin_events.groupby('user').size()
    normal_admin_users = user_admin_freq[user_admin_freq > 10].index

    # Flag unusual admin access
    suspicious = admin_events[~admin_events['user'].isin(normal_admin_users)]
    return suspicious

priv_alerts = detect_priv_escalation(events)
print(f"\nSuspicious privilege events: {len(priv_alerts)}")

# 3. Anomalous Access Patterns: access outside normal hours
def detect_off_hours_access(events, start_hour=6, end_hour=22):
    """Detect sensitive resource access outside business hours."""
    sensitive_resources = ['/admin/users', '/files/sensitive']
    sensitive_events = events[events['resource'].isin(sensitive_resources)].copy()
    sensitive_events['hour'] = sensitive_events['timestamp'].dt.hour
    off_hours = sensitive_events[
        (sensitive_events['hour'] < start_hour) | (sensitive_events['hour'] >= end_hour)
    ]
    return off_hours

off_hours_alerts = detect_off_hours_access(events)
print(f"\nOff-hours sensitive access: {len(off_hours_alerts)}")

# 4. Summary Dashboard
summary = events.groupby('event_type').agg(
    total_count=('event_type', 'size'),
    unique_users=('user', 'nunique'),
    unique_ips=('source_ip', 'nunique'),
    error_rate=('status_code', lambda x: (x >= 400).mean()),
).sort_values('total_count', ascending=False)

print("\n--- Event Summary ---")
print(summary.round(3))

# 5. Hourly pattern analysis
hourly_pattern = (
    events.groupby([events['timestamp'].dt.hour, 'event_type'])
    .size()
    .unstack(fill_value=0)
)
# Identify hours with anomalous failure rates
hourly_failure_rate = (
    events.groupby(events['timestamp'].dt.hour)['status_code']
    .apply(lambda x: (x == 401).mean())
)
anomalous_hours = hourly_failure_rate[hourly_failure_rate > hourly_failure_rate.mean() + 2*hourly_failure_rate.std()]
print(f"\nAnomalous hours (high 401 rate): {anomalous_hours.index.tolist()}")
```

### Lab 3: Time Series Anomaly Detector for Database Metrics

```python
"""
Lab 3: Database Metrics Anomaly Detection
Monitor query latency, connection count, and error rates.
Detect anomalies using multiple methods and generate alerts.
"""
import pandas as pd
import numpy as np
from scipy import stats
from statsmodels.tsa.seasonal import STL

# --- Generate synthetic DB metrics (1-minute resolution, 7 days) ---
rng = np.random.default_rng(456)
n_points = 7 * 24 * 60  # 7 days of minute-level data
timestamps = pd.date_range('2026-04-01', periods=n_points, freq='min', tz='UTC')

# Base patterns
hour_of_day = timestamps.hour + timestamps.minute / 60
day_of_week = timestamps.dayofweek

# Query latency: daily pattern + weekly pattern + noise + injected anomalies
daily_pattern = 20 + 30 * np.sin(np.pi * (hour_of_day - 6) / 12) ** 2  # peaks at noon
weekly_factor = np.where(day_of_week < 5, 1.0, 0.4)  # weekends are quieter
noise = rng.normal(0, 3, n_points)

query_latency_ms = daily_pattern * weekly_factor + noise
query_latency_ms = np.maximum(query_latency_ms, 1)

# Inject latency spikes (simulating slow queries, lock contention)
spike_times = [1000, 3500, 5600, 8200]
for t in spike_times:
    query_latency_ms[t:t+15] += rng.uniform(100, 300, 15)

# Connection count
connections = 50 + 80 * np.sin(np.pi * (hour_of_day - 8) / 10) ** 2 * weekly_factor
connections += rng.normal(0, 5, n_points)
connections = np.maximum(connections, 5).astype(int)

# Error rate (normally very low, spikes during incidents)
error_rate = rng.exponential(0.005, n_points)
error_rate[2000:2030] = rng.uniform(0.1, 0.3, 30)  # incident
error_rate[6000:6010] = rng.uniform(0.2, 0.5, 10)  # incident

metrics = pd.DataFrame({
    'timestamp': timestamps,
    'query_latency_ms': query_latency_ms,
    'connections': connections,
    'error_rate': error_rate,
}).set_index('timestamp')

# --- Anomaly Detection System ---

class MetricAnomalyDetector:
    """Multi-method anomaly detection for time series metrics."""

    def __init__(self, period=1440, zscore_threshold=3.0, iqr_k=2.5):
        self.period = period  # expected seasonality period (1440 min = 1 day)
        self.zscore_threshold = zscore_threshold
        self.iqr_k = iqr_k

    def detect_zscore(self, series, window=60):
        """Rolling z-score based detection."""
        rolling_mean = series.rolling(window=window, min_periods=10).mean()
        rolling_std = series.rolling(window=window, min_periods=10).std()
        z_scores = (series - rolling_mean) / rolling_std.replace(0, np.nan)
        return z_scores.abs() > self.zscore_threshold

    def detect_iqr(self, series, window=120):
        """Rolling IQR based detection."""
        q1 = series.rolling(window=window, min_periods=20).quantile(0.25)
        q3 = series.rolling(window=window, min_periods=20).quantile(0.75)
        iqr = q3 - q1
        lower = q1 - self.iqr_k * iqr
        upper = q3 + self.iqr_k * iqr
        return (series < lower) | (series > upper)

    def detect_stl_residual(self, series):
        """STL decomposition residual analysis."""
        try:
            stl = STL(series.dropna(), period=self.period, robust=True)
            result = stl.fit()
            residuals = result.resid
            resid_z = (residuals - residuals.mean()) / residuals.std()
            return resid_z.abs() > self.zscore_threshold
        except Exception:
            return pd.Series(False, index=series.index)

    def detect_rate_of_change(self, series, window=5, threshold=5.0):
        """Detect sudden rate of change (derivative spike)."""
        diff = series.diff()
        rolling_std = diff.rolling(window=60, min_periods=10).std()
        z_diff = diff / rolling_std.replace(0, np.nan)
        return z_diff.abs() > threshold

    def run_all(self, series, min_consensus=2):
        """Run all detectors, return consensus anomalies."""
        results = pd.DataFrame(index=series.index)
        results['zscore'] = self.detect_zscore(series)
        results['iqr'] = self.detect_iqr(series)
        results['stl'] = self.detect_stl_residual(series)
        results['rate_change'] = self.detect_rate_of_change(series)

        results['score'] = results.sum(axis=1)
        results['is_anomaly'] = results['score'] >= min_consensus
        return results

# Run detection
detector = MetricAnomalyDetector(period=1440, zscore_threshold=3.0)

latency_anomalies = detector.run_all(metrics['query_latency_ms'])
error_anomalies = detector.run_all(metrics['error_rate'])
connection_anomalies = detector.run_all(metrics['connections'])

# Generate alerts
def generate_alerts(metric_name, anomaly_results, metric_values):
    """Group consecutive anomalies into alert windows."""
    anomaly_mask = anomaly_results['is_anomaly']
    if not anomaly_mask.any():
        return pd.DataFrame()

    # Find contiguous anomaly groups
    groups = (~anomaly_mask).cumsum()[anomaly_mask]
    alerts = []
    for group_id, group_idx in groups.groupby(groups):
        start = group_idx.index[0]
        end = group_idx.index[-1]
        duration = (end - start).total_seconds() / 60
        peak_value = metric_values[start:end].max()
        avg_score = anomaly_results.loc[start:end, 'score'].mean()

        alerts.append({
            'metric': metric_name,
            'start': start,
            'end': end,
            'duration_min': duration,
            'peak_value': peak_value,
            'severity_score': avg_score,
            'severity': 'CRITICAL' if avg_score >= 3 else 'HIGH' if avg_score >= 2 else 'MEDIUM',
        })

    return pd.DataFrame(alerts)

latency_alerts = generate_alerts('query_latency_ms', latency_anomalies, metrics['query_latency_ms'])
error_alerts = generate_alerts('error_rate', error_anomalies, metrics['error_rate'])

all_alerts = pd.concat([latency_alerts, error_alerts], ignore_index=True)
all_alerts = all_alerts.sort_values('start')

print("--- Anomaly Detection Results ---")
print(f"Latency anomalies: {latency_anomalies['is_anomaly'].sum()} points")
print(f"Error rate anomalies: {error_anomalies['is_anomaly'].sum()} points")
print(f"\nAlerts generated: {len(all_alerts)}")
print(all_alerts[['metric', 'start', 'duration_min', 'peak_value', 'severity']].to_string())
```

### Lab 4: Performance Benchmark — Pandas vs Polars vs DuckDB

```python
"""
Lab 4: Performance Comparison
Benchmark identical analytical queries across pandas, Polars, and DuckDB.
"""
import pandas as pd
import numpy as np
import time
from contextlib import contextmanager

@contextmanager
def timer(label):
    start = time.perf_counter()
    yield
    elapsed = time.perf_counter() - start
    print(f"  {label}: {elapsed:.3f}s")

# --- Generate benchmark data ---
rng = np.random.default_rng(789)
n = 5_000_000

print("Generating benchmark data...")
df = pd.DataFrame({
    'user_id': rng.integers(1, 100_001, n),
    'product_id': rng.integers(1, 10_001, n),
    'category': rng.choice(['electronics', 'clothing', 'food', 'books', 'home'], n),
    'amount': np.round(rng.lognormal(3.5, 1.0, n), 2),
    'quantity': rng.integers(1, 10, n),
    'timestamp': pd.date_range('2025-01-01', periods=n, freq='6s'),
    'region': rng.choice(['NA', 'EMEA', 'APAC', 'LATAM'], n, p=[0.35, 0.25, 0.25, 0.15]),
})
print(f"DataFrame: {n:,} rows, {df.memory_usage(deep=True).sum()/1e6:.0f} MB")

# --- Benchmark 1: Filtered Aggregation ---
print("\n=== Benchmark 1: Filtered Aggregation ===")

# Pandas
with timer("pandas"):
    result_pd = (
        df[df['amount'] > 50]
        .groupby(['category', 'region'])
        .agg(
            total_revenue=('amount', 'sum'),
            avg_amount=('amount', 'mean'),
            n_orders=('amount', 'count'),
            unique_users=('user_id', 'nunique'),
        )
        .sort_values('total_revenue', ascending=False)
    )

# Polars
import polars as pl
df_pl = pl.from_pandas(df)

with timer("polars"):
    result_pl = (
        df_pl
        .filter(pl.col('amount') > 50)
        .group_by(['category', 'region'])
        .agg([
            pl.col('amount').sum().alias('total_revenue'),
            pl.col('amount').mean().alias('avg_amount'),
            pl.col('amount').count().alias('n_orders'),
            pl.col('user_id').n_unique().alias('unique_users'),
        ])
        .sort('total_revenue', descending=True)
    )

# DuckDB
import duckdb
conn = duckdb.connect()
conn.register('orders', df)

with timer("duckdb"):
    result_duck = conn.execute("""
        SELECT category, region,
               SUM(amount) as total_revenue,
               AVG(amount) as avg_amount,
               COUNT(*) as n_orders,
               COUNT(DISTINCT user_id) as unique_users
        FROM orders
        WHERE amount > 50
        GROUP BY category, region
        ORDER BY total_revenue DESC
    """).fetchdf()

# --- Benchmark 2: Window Functions ---
print("\n=== Benchmark 2: Window Functions (Top-N per group) ===")

with timer("pandas"):
    top_products_pd = (
        df.groupby(['category', 'product_id'])['amount']
        .sum()
        .reset_index()
        .sort_values(['category', 'amount'], ascending=[True, False])
        .groupby('category')
        .head(10)
    )

with timer("polars"):
    top_products_pl = (
        df_pl
        .group_by(['category', 'product_id'])
        .agg(pl.col('amount').sum())
        .sort('amount', descending=True)
        .group_by('category')
        .head(10)
    )

with timer("duckdb"):
    top_products_duck = conn.execute("""
        WITH product_totals AS (
            SELECT category, product_id, SUM(amount) as total,
                   ROW_NUMBER() OVER (PARTITION BY category ORDER BY SUM(amount) DESC) as rn
            FROM orders
            GROUP BY category, product_id
        )
        SELECT * FROM product_totals WHERE rn <= 10
    """).fetchdf()

# --- Benchmark 3: Time-based Rolling Aggregation ---
print("\n=== Benchmark 3: Monthly Cohort Revenue ===")

with timer("pandas"):
    df_ts = df.set_index('timestamp')
    monthly_pd = df_ts.resample('ME').agg({
        'amount': ['sum', 'mean', 'count'],
        'user_id': 'nunique',
    })

with timer("polars"):
    monthly_pl = (
        df_pl
        .group_by_dynamic('timestamp', every='1mo')
        .agg([
            pl.col('amount').sum().alias('total'),
            pl.col('amount').mean().alias('avg'),
            pl.col('amount').count().alias('count'),
            pl.col('user_id').n_unique().alias('unique_users'),
        ])
    )

with timer("duckdb"):
    monthly_duck = conn.execute("""
        SELECT DATE_TRUNC('month', timestamp) as month,
               SUM(amount) as total,
               AVG(amount) as avg,
               COUNT(*) as count,
               COUNT(DISTINCT user_id) as unique_users
        FROM orders
        GROUP BY DATE_TRUNC('month', timestamp)
        ORDER BY month
    """).fetchdf()

# --- Benchmark 4: Join Performance ---
print("\n=== Benchmark 4: Join + Aggregation ===")

# Create a dimension table
users_dim = pd.DataFrame({
    'user_id': range(1, 100_001),
    'tier': rng.choice(['free', 'pro', 'enterprise'], 100_000, p=[0.7, 0.2, 0.1]),
    'country': rng.choice(['US', 'UK', 'DE', 'FR', 'JP', 'BR', 'IN'], 100_000),
})
users_dim_pl = pl.from_pandas(users_dim)
conn.register('users_dim', users_dim)

with timer("pandas"):
    joined_pd = df.merge(users_dim, on='user_id', how='left')
    result_pd = joined_pd.groupby(['tier', 'category']).agg(
        revenue=('amount', 'sum'),
        orders=('amount', 'count'),
    )

with timer("polars"):
    result_pl = (
        df_pl
        .join(users_dim_pl, on='user_id', how='left')
        .group_by(['tier', 'category'])
        .agg([
            pl.col('amount').sum().alias('revenue'),
            pl.col('amount').count().alias('orders'),
        ])
    )

with timer("duckdb"):
    result_duck = conn.execute("""
        SELECT u.tier, o.category,
               SUM(o.amount) as revenue,
               COUNT(*) as orders
        FROM orders o
        LEFT JOIN users_dim u ON o.user_id = u.user_id
        GROUP BY u.tier, o.category
    """).fetchdf()

# --- Summary ---
print("\n=== Typical Results (5M rows) ===")
print("""
| Operation              | pandas  | Polars  | DuckDB  |
|------------------------|---------|---------|---------|
| Filtered Aggregation   | ~1.2s   | ~0.15s  | ~0.12s  |
| Window / Top-N         | ~2.5s   | ~0.25s  | ~0.18s  |
| Monthly Resample       | ~0.8s   | ~0.10s  | ~0.08s  |
| Join + Aggregation     | ~3.0s   | ~0.35s  | ~0.20s  |

Key takeaways:
- Polars: 5-10x faster than pandas, Rust backend, lazy evaluation
- DuckDB: 10-15x faster for SQL-native queries, columnar engine
- Pandas: most flexible API, largest ecosystem, best for <1M rows
- For >10M rows or complex joins: prefer Polars or DuckDB
- DuckDB excels at analytical SQL; Polars excels at expression-based transforms
""")

conn.close()
```

---

## Reference: Essential Import Patterns

```python
# Core stack
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm

# Performance alternatives
import polars as pl
import duckdb

# Data loading
from sqlalchemy import create_engine, text
from pathlib import Path

# Type hints for pandas
from pandas import DataFrame, Series
from numpy.typing import NDArray

# Common configuration
pd.set_option('display.max_columns', 50)
pd.set_option('display.max_rows', 100)
pd.set_option('display.float_format', '{:.2f}'.format)
pd.set_option('mode.copy_on_write', True)  # pandas 2.0+ CoW

# Suppress warnings in notebooks (not production)
import warnings
warnings.filterwarnings('ignore', category=FutureWarning)
```

## Reference: Performance Decision Tree

```
Need to process data?
├── < 1M rows → pandas (familiar API, rich ecosystem)
├── 1M-100M rows
│   ├── SQL-shaped query? → DuckDB (fastest for GROUP BY, JOIN, window)
│   ├── Complex transforms? → Polars (expression API, lazy eval)
│   └── Existing pandas code? → eval()/query() + vectorize
├── > 100M rows (out-of-core)
│   ├── Fits in Parquet partitions? → DuckDB / Polars scan
│   ├── Distributed cluster available? → Dask / Spark
│   └── Single machine, iterative? → chunked pandas + aggregation
└── Real-time / streaming?
    └── Don't use pandas. Use dedicated stream processors.
```

## Reference: Memory Usage Cheat Sheet

| dtype | Bytes/element | 1M rows | Notes |
|-------|--------------|---------|-------|
| int64 | 8 | 7.6 MB | Default integer |
| int32 | 4 | 3.8 MB | Downcast when range fits |
| int16 | 2 | 1.9 MB | -32K to 32K |
| int8 | 1 | 0.95 MB | -128 to 127 |
| float64 | 8 | 7.6 MB | Default float |
| float32 | 4 | 3.8 MB | Acceptable precision loss for most analytics |
| bool | 1 | 0.95 MB | |
| category | varies | ~0.1-1 MB | Huge savings for low cardinality |
| object (str) | 50-100+ | 50-100 MB | Worst case — convert to category |
| PyArrow string | varies | ~5-15 MB | 5-10x better than object |
