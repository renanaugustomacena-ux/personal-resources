# Redis: Caching Patterns

> Autori: Team Data Encyclopedia  
> Ultimo aggiornamento: 2026-05-22  
> Versione: 2.0.0  
> Stato: expanded

## Skip list
- [x] Bozza iniziale
- [x] Review tecnica
- [ ] Formattazione
- [ ] Pubblicazione

## Indice
1. Cache-Aside Pattern
2. Read-Through
3. Write-Through
4. Write-Behind (Write-Back)
5. Refresh-Ahead
6. Session Store
7. Rate Limiting
8. Client-Side Caching (Redis 6+)
9. Cache Invalidation Strategies
10. Cache Stampede Prevention
11. Multi-Layer Caching
12. Configuration Reference
13. Monitoring and Observability
14. Performance Tuning
15. Operational Procedures
16. Real-World Patterns
17. Troubleshooting
18. FAQ

---

## 1. Cache-Aside Pattern

### 1.1 How It Works

The application manages both cache and database directly. On a read, the application first checks the cache. On a miss, it queries the database, stores the result in the cache, and returns it. The cache is never populated automatically -- the application is fully responsible.

```python
import redis
import json

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

def get_user(user_id):
    cache_key = f"user:{user_id}"

    # Step 1: Try cache
    cached = r.get(cache_key)
    if cached:
        return json.loads(cached)

    # Step 2: Cache miss -- query database
    user = db.query("SELECT * FROM users WHERE id = %s", (user_id,))

    # Step 3: Populate cache with TTL
    if user:
        r.setex(cache_key, 3600, json.dumps(user))

    return user
```

### 1.2 Write Handling

On writes, the application updates the database and then either invalidates the cache entry or updates it:

```python
def update_user(user_id, data):
    # Update database first
    db.execute("UPDATE users SET name=%s WHERE id=%s", (data['name'], user_id))

    # Option A: Invalidate (simpler, recommended)
    r.delete(f"user:{user_id}")

    # Option B: Update cache (risks stale data if DB write fails)
    # r.setex(f"user:{user_id}", 3600, json.dumps(data))
```

### 1.3 Advantages and Disadvantages

| Pros | Cons |
|---|---|
| Simple to implement | Application must handle cache logic |
| Cache contains only requested data | First request always hits DB (cold start) |
| Cache failure does not break reads | Potential for stale data between write and invalidation |
| Flexible TTL per key | N+1 cache problem possible |

### 1.4 When to Use

- General-purpose caching for read-heavy workloads
- When you need control over what gets cached
- When cache misses are tolerable (not latency-critical on first hit)

---

## 2. Read-Through

### 2.1 How It Works

The cache sits between the application and the database. On a miss, the cache itself loads the data from the database (via a configured loader function). The application always reads from the cache.

```python
class ReadThroughCache:
    def __init__(self, redis_client, loader_fn, default_ttl=3600):
        self.r = redis_client
        self.loader = loader_fn
        self.ttl = default_ttl

    def get(self, key):
        cached = self.r.get(key)
        if cached is not None:
            return json.loads(cached)

        # Cache loads from source automatically
        value = self.loader(key)
        if value is not None:
            self.r.setex(key, self.ttl, json.dumps(value))
        return value

# Usage
def db_loader(key):
    """Load user from database given cache key like 'user:123'."""
    user_id = key.split(':')[1]
    return db.query("SELECT * FROM users WHERE id = %s", (user_id,))

cache = ReadThroughCache(r, db_loader, default_ttl=1800)
user = cache.get("user:123")
```

### 2.2 Read-Through vs Cache-Aside

| Aspect | Cache-Aside | Read-Through |
|---|---|---|
| Who loads on miss | Application | Cache layer |
| Application complexity | Higher (handles miss logic) | Lower (just calls cache.get) |
| Coupling | Loose | Cache layer coupled to data source |
| Testing | Easier to mock | Loader function must be testable |

---

## 3. Write-Through

### 3.1 How It Works

Every write goes through the cache, which synchronously writes to the database. The cache is always consistent with the database (no stale data window).

```python
class WriteThroughCache:
    def __init__(self, redis_client, writer_fn, default_ttl=3600):
        self.r = redis_client
        self.writer = writer_fn
        self.ttl = default_ttl

    def put(self, key, value):
        # Write to database first (synchronous)
        self.writer(key, value)

        # Then update cache
        self.r.setex(key, self.ttl, json.dumps(value))

    def get(self, key):
        cached = self.r.get(key)
        if cached is not None:
            return json.loads(cached)
        return None

# Usage
def db_writer(key, value):
    user_id = key.split(':')[1]
    db.execute("UPDATE users SET data=%s WHERE id=%s", (json.dumps(value), user_id))

cache = WriteThroughCache(r, db_writer)
cache.put("user:123", {"name": "John", "email": "john@test.com"})
```

### 3.2 Advantages and Disadvantages

| Pros | Cons |
|---|---|
| Cache always consistent with DB | Higher write latency (two writes per request) |
| Simplifies read logic | Write amplification |
| No stale data | Cache may hold data that is never read |
| Data loss protection (DB write is synchronous) | More complex failure handling |

---

## 4. Write-Behind (Write-Back)

### 4.1 How It Works

The application writes to the cache immediately, and the cache asynchronously writes to the database after a configurable delay. This reduces write latency and enables write coalescing (multiple updates to the same key become a single DB write).

```python
import threading
import time
from collections import defaultdict

class WriteBehindCache:
    def __init__(self, redis_client, writer_fn, flush_interval=5):
        self.r = redis_client
        self.writer = writer_fn
        self.dirty_keys = set()
        self.lock = threading.Lock()
        self.flush_interval = flush_interval
        self._start_flusher()

    def put(self, key, value):
        # Write to cache immediately
        self.r.set(key, json.dumps(value))
        with self.lock:
            self.dirty_keys.add(key)

    def get(self, key):
        cached = self.r.get(key)
        return json.loads(cached) if cached else None

    def _start_flusher(self):
        def flush_loop():
            while True:
                time.sleep(self.flush_interval)
                with self.lock:
                    keys_to_flush = list(self.dirty_keys)
                    self.dirty_keys.clear()
                for key in keys_to_flush:
                    value = self.r.get(key)
                    if value:
                        try:
                            self.writer(key, json.loads(value))
                        except Exception:
                            # Re-add to dirty set for retry
                            with self.lock:
                                self.dirty_keys.add(key)

        t = threading.Thread(target=flush_loop, daemon=True)
        t.start()
```

### 4.2 Write Coalescing

If a key is updated 100 times in 5 seconds, only the final value is written to the database -- a 100x reduction in DB writes.

### 4.3 Risk: Data Loss

If Redis crashes before the dirty keys are flushed to the database, those writes are lost. Mitigate by:
- Using AOF with `appendfsync everysec`
- Keeping the flush interval short
- Using Redis Streams as a write-ahead log for dirty keys

---

## 5. Refresh-Ahead

### 5.1 How It Works

The cache proactively refreshes entries before they expire, so the application never experiences a cache miss on hot data.

```python
import threading

class RefreshAheadCache:
    def __init__(self, redis_client, loader_fn, ttl=3600, refresh_threshold=0.2):
        self.r = redis_client
        self.loader = loader_fn
        self.ttl = ttl
        self.refresh_threshold = refresh_threshold  # refresh when TTL < 20% remaining
        self._refreshing = set()

    def get(self, key):
        cached = self.r.get(key)
        remaining_ttl = self.r.ttl(key)

        if cached is not None:
            # Check if approaching expiration
            if remaining_ttl > 0 and remaining_ttl < self.ttl * self.refresh_threshold:
                self._async_refresh(key)
            return json.loads(cached)

        # Cold miss -- synchronous load
        value = self.loader(key)
        if value is not None:
            self.r.setex(key, self.ttl, json.dumps(value))
        return value

    def _async_refresh(self, key):
        if key in self._refreshing:
            return
        self._refreshing.add(key)

        def refresh():
            try:
                value = self.loader(key)
                if value is not None:
                    self.r.setex(key, self.ttl, json.dumps(value))
            finally:
                self._refreshing.discard(key)

        threading.Thread(target=refresh, daemon=True).start()
```

### 5.2 When to Use

- High-traffic keys where cache miss latency is unacceptable
- Frequently-read data with predictable access patterns (product pages, configuration)
- Not suitable for rarely-accessed data (wastes resources refreshing unused entries)

---

## 6. Session Store

### 6.1 Session Management

```python
import uuid
import json
import time

def create_session(user_id, data, ttl=86400):
    """Create a new session with 24-hour TTL."""
    session_id = str(uuid.uuid4())
    session_key = f"session:{session_id}"

    session_data = {
        'user_id': user_id,
        'created_at': int(time.time()),
        'data': data
    }

    r.setex(session_key, ttl, json.dumps(session_data))
    return session_id

def get_session(session_id):
    """Retrieve session data."""
    key = f"session:{session_id}"
    data = r.get(key)
    return json.loads(data) if data else None

def refresh_session(session_id, ttl=86400):
    """Extend session TTL on activity (sliding expiration)."""
    key = f"session:{session_id}"
    if r.exists(key):
        r.expire(key, ttl)
        return True
    return False

def destroy_session(session_id):
    """Explicitly invalidate a session (logout)."""
    return r.delete(f"session:{session_id}")
```

### 6.2 Session with Hash (Structured Fields)

```python
def create_structured_session(user_id, data, ttl=86400):
    session_id = str(uuid.uuid4())
    key = f"session:{session_id}"

    r.hset(key, mapping={
        'user_id': str(user_id),
        'created_at': str(int(time.time())),
        'ip': data.get('ip', ''),
        'user_agent': data.get('user_agent', ''),
        'role': data.get('role', 'user')
    })
    r.expire(key, ttl)
    return session_id

def get_session_field(session_id, field):
    """Get a single session field without deserializing everything."""
    return r.hget(f"session:{session_id}", field)

def update_session_field(session_id, field, value):
    """Update one field without touching others."""
    r.hset(f"session:{session_id}", field, value)
```

### 6.3 Active Session Tracking

```python
def track_active_session(user_id, session_id):
    """Track all sessions for a user (multi-device support)."""
    r.sadd(f"user:{user_id}:sessions", session_id)

def get_active_sessions(user_id):
    """List all active sessions for a user."""
    session_ids = r.smembers(f"user:{user_id}:sessions")
    active = []
    for sid in session_ids:
        if r.exists(f"session:{sid}"):
            active.append(sid)
        else:
            # Cleanup expired sessions from the set
            r.srem(f"user:{user_id}:sessions", sid)
    return active

def destroy_all_sessions(user_id):
    """Logout from all devices."""
    session_ids = r.smembers(f"user:{user_id}:sessions")
    for sid in session_ids:
        r.delete(f"session:{sid}")
    r.delete(f"user:{user_id}:sessions")
```

---

## 7. Rate Limiting

### 7.1 Fixed Window Counter

```python
def is_rate_limited_fixed(identifier, limit, window_seconds):
    """Fixed window rate limiter. Simple but has boundary burst issues."""
    key = f"ratelimit:{identifier}:{int(time.time()) // window_seconds}"
    count = r.incr(key)
    if count == 1:
        r.expire(key, window_seconds)
    return count > limit, count
```

### 7.2 Sliding Window Log

```python
def is_rate_limited_sliding(identifier, limit, window_seconds):
    """Sliding window using sorted set. Most accurate but higher memory."""
    key = f"ratelimit:sw:{identifier}"
    now = time.time()
    window_start = now - window_seconds

    pipe = r.pipeline()
    pipe.zremrangebyscore(key, 0, window_start)
    pipe.zadd(key, {f"{now}:{uuid.uuid4().hex[:8]}": now})
    pipe.zcard(key)
    pipe.expire(key, window_seconds)
    results = pipe.execute()

    count = results[2]
    return count > limit, count
```

### 7.3 Token Bucket

```lua
-- token_bucket.lua
-- KEYS[1] = bucket key
-- ARGV[1] = max tokens (bucket capacity)
-- ARGV[2] = refill rate (tokens per second)
-- ARGV[3] = tokens to consume (usually 1)
-- ARGV[4] = current timestamp (seconds, float)

local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local requested = tonumber(ARGV[3])
local now = tonumber(ARGV[4])

local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
local tokens = tonumber(bucket[1]) or capacity
local last_refill = tonumber(bucket[2]) or now

-- Refill tokens based on elapsed time
local elapsed = now - last_refill
local refill = elapsed * refill_rate
tokens = math.min(capacity, tokens + refill)

-- Attempt to consume
local allowed = 0
if tokens >= requested then
    tokens = tokens - requested
    allowed = 1
end

-- Update bucket
redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
redis.call('EXPIRE', key, math.ceil(capacity / refill_rate) * 2)

return { allowed, math.floor(tokens) }
```

```python
# Load and execute the token bucket script
with open('token_bucket.lua', 'r') as f:
    script = f.read()

token_bucket = r.register_script(script)

def check_rate_limit(identifier, capacity=100, refill_rate=10, tokens=1):
    """Token bucket: 100 capacity, refills 10/sec."""
    result = token_bucket(
        keys=[f"bucket:{identifier}"],
        args=[capacity, refill_rate, tokens, time.time()]
    )
    allowed, remaining = result
    return bool(allowed), remaining
```

### 7.4 Rate Limiting Response Headers

```python
from flask import Flask, request, jsonify, make_response

app = Flask(__name__)

@app.before_request
def rate_limit_middleware():
    client_ip = request.remote_addr
    allowed, remaining = check_rate_limit(client_ip, capacity=100, refill_rate=1.67)

    if not allowed:
        resp = make_response(jsonify({"error": "Rate limit exceeded"}), 429)
        resp.headers['Retry-After'] = '60'
        resp.headers['X-RateLimit-Remaining'] = '0'
        return resp

    # Set rate limit headers on all responses
    @app.after_request
    def add_rate_limit_headers(response):
        response.headers['X-RateLimit-Limit'] = '100'
        response.headers['X-RateLimit-Remaining'] = str(remaining)
        return response
```

---

## 8. Client-Side Caching (Redis 6+)

### 8.1 How It Works

Redis 6 introduced server-assisted client-side caching. The server tracks which keys each client has read and sends invalidation messages when those keys are modified. The client maintains a local in-memory cache and evicts entries when invalidated.

### 8.2 Tracking Mode

```bash
# Enable tracking on a client connection
CLIENT TRACKING ON

# Enable with BCAST (broadcast) mode -- receive invalidations for all key changes
CLIENT TRACKING ON BCAST

# Enable with PREFIX (broadcast) mode -- only keys matching prefixes
CLIENT TRACKING ON BCAST PREFIX user: PREFIX session:

# Enable with REDIRECT -- send invalidation to a different client connection
CLIENT TRACKING ON REDIRECT <client-id>

# Disable tracking
CLIENT TRACKING OFF

# Check tracking status
CLIENT TRACKINGINFO
```

### 8.3 Client-Side Caching with redis-py

```python
# redis-py 5.x supports client-side caching natively
import redis

# Create client with caching enabled
r = redis.Redis(
    host='localhost',
    port=6379,
    protocol=3,  # RESP3 required for push notifications
    cache_enabled=True,
    cache_max_size=10000,  # Max entries in local cache
    cache_ttl=300  # Local cache TTL (seconds)
)

# First GET: fetches from server, stores locally
value = r.get('user:123')

# Second GET: served from local cache (no network round trip)
value = r.get('user:123')

# If another client modifies 'user:123', server pushes invalidation
# Next GET will fetch from server again
```

### 8.4 RESP3 Protocol

Client-side caching requires RESP3 (Redis Serialization Protocol 3):

```bash
# Connect with RESP3
redis-cli --resp3

# In application code, set protocol=3 when creating the connection
```

### 8.5 Invalidation Modes

| Mode | How it works | Best for |
|---|---|---|
| Default (tracking) | Server tracks read keys per client | Low number of tracked keys |
| BCAST (broadcast) | Server broadcasts all key changes | Many clients, prefix-based filtering |
| REDIRECT | Invalidations sent to a dedicated Pub/Sub connection | Multiplexed connection architectures |

---

## 9. Cache Invalidation Strategies

### 9.1 TTL-Based Expiration

The simplest strategy. Keys automatically expire after a set time.

```bash
# Set TTL at write time
SET cache:page:home "<html>..." EX 300

# Jittered TTL to prevent stampede
# Python: add random variation
import random
base_ttl = 3600
jitter = random.randint(0, 360)  # +/- 10%
r.setex(key, base_ttl + jitter, value)
```

### 9.2 Event-Driven Invalidation

Invalidate on database write events:

```python
# After database update, delete relevant cache entries
def on_user_updated(user_id):
    keys_to_invalidate = [
        f"user:{user_id}",
        f"user:{user_id}:profile",
        f"cache:page:user:{user_id}"
    ]
    r.delete(*keys_to_invalidate)

# With pattern-based invalidation (use SCAN, not KEYS)
def invalidate_by_pattern(pattern):
    cursor = 0
    while True:
        cursor, keys = r.scan(cursor=cursor, match=pattern, count=100)
        if keys:
            r.delete(*keys)
        if cursor == 0:
            break
```

### 9.3 Version-Based Invalidation

Instead of deleting cache entries, increment a version counter. Cache keys include the version, so old entries are naturally ignored:

```python
def get_cached_with_version(entity_type, entity_id):
    version = r.get(f"version:{entity_type}:{entity_id}") or "0"
    cache_key = f"cache:{entity_type}:{entity_id}:v{version}"

    cached = r.get(cache_key)
    if cached:
        return json.loads(cached)

    value = load_from_db(entity_type, entity_id)
    r.setex(cache_key, 3600, json.dumps(value))
    return value

def invalidate_version(entity_type, entity_id):
    r.incr(f"version:{entity_type}:{entity_id}")
    # Old versioned cache keys expire naturally via TTL
```

### 9.4 Tag-Based Invalidation

Group related cache entries under tags. Invalidate all entries sharing a tag:

```python
def cache_with_tags(key, value, tags, ttl=3600):
    pipe = r.pipeline()
    pipe.setex(key, ttl, json.dumps(value))
    for tag in tags:
        pipe.sadd(f"tag:{tag}", key)
        pipe.expire(f"tag:{tag}", ttl + 60)
    pipe.execute()

def invalidate_tag(tag):
    tag_key = f"tag:{tag}"
    keys = r.smembers(tag_key)
    if keys:
        r.delete(*keys)
    r.delete(tag_key)

# Usage
cache_with_tags("page:product:42", html, tags=["products", "category:electronics"])
invalidate_tag("products")  # Clears all product page caches
```

---

## 10. Cache Stampede Prevention

### 10.1 The Problem

When a hot cache key expires, many concurrent requests simultaneously hit the database to regenerate it. This can overwhelm the database.

### 10.2 Locking (Mutex)

Only one process regenerates the cache; others wait or serve stale data:

```python
def get_with_lock(key, loader, ttl=3600, lock_timeout=10):
    cached = r.get(key)
    if cached is not None:
        return json.loads(cached)

    lock_key = f"lock:{key}"
    acquired = r.set(lock_key, "1", nx=True, ex=lock_timeout)

    if acquired:
        try:
            value = loader()
            r.setex(key, ttl, json.dumps(value))
            return value
        finally:
            r.delete(lock_key)
    else:
        # Wait for lock holder to populate cache
        for _ in range(lock_timeout * 10):
            time.sleep(0.1)
            cached = r.get(key)
            if cached is not None:
                return json.loads(cached)

        # Fallback: load directly
        return loader()
```

### 10.3 Probabilistic Early Recomputation (XFetch)

Proactively recompute before TTL expires. The closer to expiration, the higher the probability of refresh:

```python
import math
import random

def xfetch(key, loader, ttl=3600, beta=1.0):
    cached = r.get(key)
    remaining = r.ttl(key)

    if cached is not None and remaining > 0:
        # XFetch: probability of early recompute increases near expiry
        delta = ttl - remaining
        if remaining - delta * beta * math.log(random.random()) > 0:
            return json.loads(cached)

    value = loader()
    r.setex(key, ttl, json.dumps(value))
    return value
```

### 10.4 Stale-While-Revalidate

Serve stale data immediately while refreshing in the background:

```python
def get_stale_while_revalidate(key, loader, ttl=3600, stale_ttl=600):
    cached = r.get(key)
    remaining = r.ttl(key)

    if cached is not None:
        if remaining < stale_ttl:
            # Serve stale, refresh in background
            threading.Thread(
                target=lambda: r.setex(key, ttl, json.dumps(loader())),
                daemon=True
            ).start()
        return json.loads(cached)

    # True miss
    value = loader()
    r.setex(key, ttl, json.dumps(value))
    return value
```

---

## 11. Multi-Layer Caching

### 11.1 L1 (In-Process) + L2 (Redis) Architecture

```
Client Request
    │
    ▼
┌──────────────────┐
│ L1: Process Cache │  (dict/LRU, ~1ms, process-local)
│   (in-memory)     │
└────────┬─────────┘
         │ miss
         ▼
┌──────────────────┐
│ L2: Redis Cache   │  (network, ~1-5ms, shared)
└────────┬─────────┘
         │ miss
         ▼
┌──────────────────┐
│ Database / API    │  (disk, ~10-100ms)
└──────────────────┘
```

```python
from functools import lru_cache
import time

# L1: in-process LRU cache (per-process, no network)
_l1_cache = {}
_l1_ttl = {}

def l1_get(key, max_age=60):
    if key in _l1_cache:
        if time.time() - _l1_ttl[key] < max_age:
            return _l1_cache[key]
        del _l1_cache[key]
        del _l1_ttl[key]
    return None

def l1_set(key, value):
    _l1_cache[key] = value
    _l1_ttl[key] = time.time()

def get_multi_layer(key, loader, l1_ttl=60, l2_ttl=3600):
    # L1 check
    value = l1_get(key, l1_ttl)
    if value is not None:
        return value

    # L2 check (Redis)
    cached = r.get(key)
    if cached is not None:
        value = json.loads(cached)
        l1_set(key, value)
        return value

    # Miss: load from source
    value = loader()
    r.setex(key, l2_ttl, json.dumps(value))
    l1_set(key, value)
    return value
```

### 11.2 L1 Invalidation with Pub/Sub

```python
# Invalidation channel listener (runs in each process)
def start_invalidation_listener():
    pubsub = r.pubsub()
    pubsub.subscribe('cache:invalidate')

    def listener():
        for message in pubsub.listen():
            if message['type'] == 'message':
                key = message['data']
                _l1_cache.pop(key, None)
                _l1_ttl.pop(key, None)

    threading.Thread(target=listener, daemon=True).start()

# When invalidating, publish to all instances
def invalidate(key):
    r.delete(key)
    r.publish('cache:invalidate', key)
```

---

## 12. Configuration Reference

### 12.1 Eviction and Memory

```bash
# Memory limit
maxmemory 4gb

# Eviction policy (for cache use cases)
maxmemory-policy allkeys-lfu    # Best for most caching workloads
# allkeys-lru is also good

# Eviction sampling
maxmemory-samples 10

# Lazy free on eviction (background deletion)
lazyfree-lazy-eviction yes
lazyfree-lazy-expire yes
```

### 12.2 Client-Side Caching Config

```bash
# Maximum number of tracked keys per client (default 0 = unlimited)
tracking-table-max-keys 1000000

# Note: when this limit is reached, Redis evicts the oldest tracked key
# and sends an invalidation to the tracking client
```

### 12.3 Key Expiration Settings

```bash
# Active expiration cycle frequency
hz 10                   # Default: 10 cycles/sec for expiration checks
dynamic-hz yes          # Adapt based on number of clients

# Lazy expiration: keys are checked on access
# Active expiration: background process samples expired keys
# Both mechanisms work together
```

---

## 13. Monitoring and Observability

### 13.1 Cache Hit Ratio

```bash
# Get cache hit/miss statistics
INFO stats
# keyspace_hits: total GET hits
# keyspace_misses: total GET misses

# Hit ratio = keyspace_hits / (keyspace_hits + keyspace_misses)
```

```python
def get_cache_hit_ratio():
    info = r.info('stats')
    hits = info['keyspace_hits']
    misses = info['keyspace_misses']
    total = hits + misses
    if total == 0:
        return 0.0
    return hits / total

# Target: > 0.90 for a well-tuned cache
```

### 13.2 Eviction Monitoring

```bash
INFO stats
# evicted_keys: total number of evicted keys since startup
# If this number is climbing rapidly, increase maxmemory or review TTLs

INFO memory
# used_memory: current memory usage
# maxmemory: configured limit
```

### 13.3 Key Expiration Stats

```bash
INFO keyspace
# db0:keys=5000,expires=4500,avg_ttl=1800000
# avg_ttl in milliseconds -- if very low, keys are expiring too quickly
```

### 13.4 Prometheus Metrics to Export

```
redis_keyspace_hits_total
redis_keyspace_misses_total
redis_evicted_keys_total
redis_expired_keys_total
redis_memory_used_bytes
redis_memory_max_bytes
redis_connected_clients
redis_db_keys{db="0"}
redis_db_expires{db="0"}
redis_db_avg_ttl_seconds{db="0"}
```

---

## 14. Performance Tuning

### 14.1 TTL Jitter

Prevent stampede by adding random jitter to TTL:

```python
import random

def set_with_jitter(key, value, base_ttl, jitter_pct=0.1):
    jitter = int(base_ttl * jitter_pct)
    ttl = base_ttl + random.randint(-jitter, jitter)
    r.setex(key, ttl, value)
```

### 14.2 Pipeline Batch Caching

```python
def cache_batch(items, ttl=3600):
    """Cache multiple items in a single pipeline call."""
    pipe = r.pipeline(transaction=False)
    for key, value in items.items():
        pipe.setex(key, ttl + random.randint(0, 360), json.dumps(value))
    pipe.execute()
```

### 14.3 Compression for Large Values

```python
import zlib

COMPRESSION_THRESHOLD = 1024  # bytes

def cache_set_compressed(key, value, ttl=3600):
    serialized = json.dumps(value).encode()
    if len(serialized) > COMPRESSION_THRESHOLD:
        compressed = zlib.compress(serialized, level=6)
        r.setex(key, ttl, b'Z' + compressed)  # prefix 'Z' = compressed
    else:
        r.setex(key, ttl, serialized)

def cache_get_compressed(key):
    data = r.get(key)
    if data is None:
        return None
    if data[:1] == b'Z':
        return json.loads(zlib.decompress(data[1:]))
    return json.loads(data)
```

---

## 15. Operational Procedures

### 15.1 Cache Warmup

```python
def warm_cache(keys_and_loaders):
    """Pre-populate cache on application startup or before traffic spike."""
    pipe = r.pipeline(transaction=False)
    for key, loader in keys_and_loaders:
        value = loader()
        if value is not None:
            pipe.setex(key, 3600, json.dumps(value))
    pipe.execute()
```

### 15.2 Monitoring Cache Health

```bash
# Quick health check script
#!/bin/bash
HITS=$(redis-cli INFO stats | grep keyspace_hits | awk -F: '{print $2}' | tr -d '\r')
MISSES=$(redis-cli INFO stats | grep keyspace_misses | awk -F: '{print $2}' | tr -d '\r')
EVICTED=$(redis-cli INFO stats | grep evicted_keys | awk -F: '{print $2}' | tr -d '\r')
MEM=$(redis-cli INFO memory | grep used_memory_human | awk -F: '{print $2}' | tr -d '\r')
MAXMEM=$(redis-cli INFO memory | grep maxmemory_human | awk -F: '{print $2}' | tr -d '\r')

echo "Hits: $HITS | Misses: $MISSES | Evictions: $EVICTED | Memory: $MEM / $MAXMEM"

TOTAL=$((HITS + MISSES))
if [ $TOTAL -gt 0 ]; then
    RATIO=$(echo "scale=4; $HITS / $TOTAL" | bc)
    echo "Hit Ratio: $RATIO"
fi
```

### 15.3 Graceful Cache Flush

```bash
# Never use FLUSHALL in production (blocks until complete)
# Instead, use SCAN + DEL for targeted cleanup

# Flush by pattern (non-blocking)
redis-cli --scan --pattern "cache:*" | xargs -L 100 redis-cli DEL

# Or with UNLINK (non-blocking delete, Redis 4+)
redis-cli --scan --pattern "cache:*" | xargs -L 100 redis-cli UNLINK
```

---

## 16. Real-World Patterns

### 16.1 API Response Caching with ETag

```python
import hashlib

def get_api_response(endpoint, params):
    cache_key = f"api:{endpoint}:{hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()}"

    cached = r.hgetall(cache_key)
    if cached:
        return {
            'data': json.loads(cached['data']),
            'etag': cached['etag'],
            'cached': True
        }

    # Fetch from upstream
    response = fetch_upstream(endpoint, params)
    etag = hashlib.sha256(json.dumps(response).encode()).hexdigest()[:16]

    pipe = r.pipeline()
    pipe.hset(cache_key, mapping={'data': json.dumps(response), 'etag': etag})
    pipe.expire(cache_key, 300)
    pipe.execute()

    return {'data': response, 'etag': etag, 'cached': False}
```

### 16.2 Database Query Cache

```python
def cached_query(sql, params, ttl=300):
    """Cache database query results keyed by query hash."""
    query_hash = hashlib.sha256(f"{sql}:{params}".encode()).hexdigest()[:16]
    cache_key = f"qcache:{query_hash}"

    cached = r.get(cache_key)
    if cached:
        return json.loads(cached)

    result = db.execute(sql, params).fetchall()
    r.setex(cache_key, ttl, json.dumps(result))
    return result
```

### 16.3 Shopping Cart with Hash

```python
def add_to_cart(session_id, product_id, quantity):
    key = f"cart:{session_id}"
    r.hincrby(key, product_id, quantity)
    r.expire(key, 604800)  # 7 days

def remove_from_cart(session_id, product_id):
    r.hdel(f"cart:{session_id}", product_id)

def get_cart(session_id):
    return r.hgetall(f"cart:{session_id}")

def get_cart_total(session_id):
    cart = r.hgetall(f"cart:{session_id}")
    total = 0
    for product_id, qty in cart.items():
        price = r.hget(f"product:{product_id}", 'price')
        total += float(price) * int(qty)
    return total
```

---

## 17. Troubleshooting

### 17.1 Low Cache Hit Ratio

**Symptoms**: Hit ratio below 80%.

**Diagnosis**:
```bash
INFO stats  # keyspace_hits / keyspace_misses
```

**Common causes**: TTL too short, cache keys not matching read patterns, high churn rate, insufficient memory causing evictions.

**Resolution**: Increase TTL, review key naming, increase `maxmemory`, analyze access patterns with `OBJECT FREQ`.

### 17.2 Cache Stampede / Thundering Herd

**Symptoms**: Database load spikes correlating with cache key expirations.

**Resolution**: Implement one of the stampede prevention patterns (section 10): locking, XFetch, or stale-while-revalidate. Add TTL jitter.

### 17.3 Stale Data After Write

**Symptoms**: Application reads old data even after database update.

**Common causes**: Race condition between write and invalidation, or cache populated by a concurrent read before invalidation completed.

**Resolution**: Invalidate cache before or during the write transaction. Use version-based invalidation for strong consistency.

### 17.4 Memory Spike from Unbounded Cache

**Symptoms**: Redis memory grows indefinitely.

**Cause**: Keys without TTL being added continuously.

**Resolution**: Always set TTL on cache entries. Set `maxmemory` with an appropriate eviction policy.

### 17.5 Rate Limiter Race Condition

**Symptoms**: Rate limit exceeds configured maximum during concurrent requests.

**Cause**: Non-atomic check-and-increment (INCR + EXPIRE is not atomic if separate).

**Resolution**: Use Lua script for atomic rate limiting, or use `SET key value NX EX` for the initial set.

### 17.6 Client-Side Cache Not Invalidating

**Symptoms**: Application serves stale data even after Redis key is updated.

**Diagnosis**: Check if `CLIENT TRACKING ON` is active, RESP3 is being used, and the client library supports tracking.

```bash
CLIENT TRACKINGINFO
```

**Resolution**: Ensure `protocol=3`, verify client library version supports tracking.

### 17.7 Session Expiring Prematurely

**Symptoms**: Users logged out before expected session TTL.

**Cause**: `maxmemory-policy` is evicting session keys. Or `EXPIRE` was called with a shorter TTL than intended.

**Resolution**: Use `volatile-*` eviction policy and ensure session keys have appropriate TTL. Consider dedicated Redis instance for sessions.

### 17.8 Cache Key Collision

**Symptoms**: Different data returned for logically different queries.

**Cause**: Cache key does not fully encode the query parameters.

**Resolution**: Include all varying parameters in the cache key. Use a hash of the full query.

### 17.9 Excessive Memory from Large Values

**Symptoms**: Few keys consuming most of the memory.

**Diagnosis**:
```bash
redis-cli --bigkeys
MEMORY USAGE key_name
```

**Resolution**: Compress large values (section 14.3), split into smaller chunks, or use a different storage layer for large blobs.

### 17.10 Eviction Happening on Non-Cache Keys

**Symptoms**: Critical keys (sessions, locks) being evicted alongside cache entries.

**Cause**: Using `allkeys-*` eviction policy.

**Resolution**: Use `volatile-*` eviction policy (only evicts keys with TTL). Or separate cache and persistent data into different Redis instances.

### 17.11 Negative Cache Missing

**Symptoms**: Database overwhelmed by repeated lookups for non-existent entities.

**Cause**: Cache miss on non-existent entities always hits the database.

**Resolution**: Cache negative results (null/empty markers) with shorter TTL:
```python
TOMBSTONE_TTL = 60
if result is None:
    r.setex(key, TOMBSTONE_TTL, "__NULL__")
```

---

## 18. FAQ

### Q1: What eviction policy is best for caching?

`allkeys-lfu` for most workloads. It keeps frequently accessed keys and evicts rarely used ones. Use `allkeys-lru` if recency matters more than frequency.

### Q2: Should I use Redis or Memcached for caching?

Redis for: structured data, persistence, Pub/Sub, Lua scripting, client-side caching, Streams. Memcached for: pure key-value caching with multi-threaded performance and lower memory overhead per key.

### Q3: How do I handle cache for paginated queries?

Cache each page separately:
```
cache:products:page:1:size:20:sort:price_asc → [page 1 data]
cache:products:page:2:size:20:sort:price_asc → [page 2 data]
```
Invalidate all pages on data change using tag-based invalidation.

### Q4: What TTL should I use?

Depends on data freshness requirements. Common values: 60s for volatile data, 5-15min for API responses, 1hr for user profiles, 24hr for static content. Always add jitter.

### Q5: How many keys can Redis cache effectively?

Redis can hold billions of keys. The practical limit is memory. Each key has ~70 bytes of overhead. Plan memory accordingly.

### Q6: Does client-side caching work with Redis Cluster?

Yes, since Redis 7.0. Tracking and invalidation work across cluster nodes. Client libraries must support cluster-mode tracking.

### Q7: How do I prevent cache warming from overwhelming the database?

Warm in batches with rate limiting. Use pipelines for Redis writes. Stagger warm-up across application instances (e.g., each instance warms a different subset).

### Q8: Should I cache null results?

Yes (negative caching). Without it, non-existent keys cause repeated DB lookups. Cache a sentinel value with a short TTL (30-60 seconds).

### Q9: How do I debug what is in the cache?

```bash
SCAN 0 MATCH cache:* COUNT 100
TYPE cache:key
TTL cache:key
MEMORY USAGE cache:key
DEBUG OBJECT cache:key  # encoding, refcount, LRU age
```

### Q10: Is write-behind safe for financial data?

No. Write-behind has a data loss window between the cache write and the async DB write. Use write-through or cache-aside with database-first writes for financial data.

### Q11: How do I cache data with complex relationships?

Use tag-based invalidation. Tag each cached entry with the entities it depends on. When any entity changes, invalidate all entries tagged with it.

### Q12: What is the difference between EXPIRE and EXPIREAT?

`EXPIRE key 300` sets relative TTL (300 seconds from now). `EXPIREAT key 1700000000` sets absolute expiration (Unix timestamp). Use `EXPIREAT` when you need all instances of a cached item to expire at the same wall-clock time.

---

*Questo documento fa parte del modulo 06 "NoSQL Redis" della Data Encyclopedia.*
