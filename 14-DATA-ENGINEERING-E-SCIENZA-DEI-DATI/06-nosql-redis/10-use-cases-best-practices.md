# Redis: Use Cases e Best Practices

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
1. Cache Layer
2. Session Store
3. Leaderboard/Counters
4. Message Queue
5. Real-time Analytics
6. Rate Limiting
7. Distributed Lock
8. Geospatial Indexes
9. Full-Text Search with RediSearch
10. Client-Side Caching
11. Best Practices
12. Anti-Patterns
13. Configuration Best Practices
14. Monitoring and Observability
15. Operational Procedures
16. Troubleshooting
17. FAQ

---

## 1. Cache Layer

### 1.1 Web Application Cache

```python
# Django/Flask + Redis cache
import redis
import json

r = redis.Redis(host='redis', decode_responses=True)

def get_user_profile(user_id):
    cache_key = f"user:profile:{user_id}"

    # Try cache
    cached = r.get(cache_key)
    if cached:
        return json.loads(cached)

    # Query DB
    user = db.query("SELECT * FROM users WHERE id = %s", (user_id,))

    # Store in cache (TTL 1 hour)
    if user:
        r.setex(cache_key, 3600, json.dumps(user))

    return user
```

### 1.2 HTML Fragment Cache

```python
def get_cached_page(section):
    key = f"page:section:{section}"
    cached = r.get(key)
    if cached:
        return cached

    html = render_section(section)
    r.setex(key, 300, html)  # 5 min
    return html
```

### 1.3 API Response Cache

```python
import hashlib

def cached_api_call(endpoint, params, ttl=120):
    """Cache external API responses to reduce quota usage and latency."""
    param_hash = hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()[:16]
    cache_key = f"api:{endpoint}:{param_hash}"

    cached = r.get(cache_key)
    if cached:
        return json.loads(cached)

    response = requests.get(endpoint, params=params)
    if response.status_code == 200:
        r.setex(cache_key, ttl, json.dumps(response.json()))
    return response.json()
```

### 1.4 Computed Result Cache

```python
def get_dashboard_stats(org_id, ttl=60):
    """Cache expensive aggregation queries."""
    cache_key = f"stats:dashboard:{org_id}"

    cached = r.get(cache_key)
    if cached:
        return json.loads(cached)

    stats = {
        'total_users': db.count("SELECT COUNT(*) FROM users WHERE org_id=%s", (org_id,)),
        'active_today': db.count("SELECT COUNT(*) FROM sessions WHERE org_id=%s AND date=CURRENT_DATE", (org_id,)),
        'revenue_mtd': db.sum("SELECT SUM(amount) FROM payments WHERE org_id=%s AND date >= date_trunc('month', CURRENT_DATE)", (org_id,)),
    }

    r.setex(cache_key, ttl, json.dumps(stats))
    return stats
```

---

## 2. Session Store

### 2.1 Web Session

```python
import uuid
import json
import time

def create_session(user_id, data):
    session_id = str(uuid.uuid4())
    session_key = f"session:{session_id}"

    session_data = {
        'user_id': user_id,
        'login_time': time.time(),
        'data': data
    }

    r.setex(session_key, 86400, json.dumps(session_data))  # 24h
    return session_id

def get_session(session_id):
    key = f"session:{session_id}"
    data = r.get(key)
    return json.loads(data) if data else None

def refresh_session(session_id, ttl=86400):
    r.expire(f"session:{session_id}", ttl)
```

### 2.2 Shopping Cart

```python
def add_to_cart(session_id, product_id, quantity):
    key = f"cart:{session_id}"
    r.hincrby(key, product_id, quantity)
    r.expire(key, 604800)  # 7 days

def get_cart(session_id):
    key = f"cart:{session_id}"
    return r.hgetall(key)

def remove_from_cart(session_id, product_id):
    r.hdel(f"cart:{session_id}", product_id)

def clear_cart(session_id):
    r.delete(f"cart:{session_id}")
```

### 2.3 JWT Token Blacklist

```python
def blacklist_token(jti, expires_in):
    """Add a JWT token ID to the blacklist (used on logout)."""
    r.setex(f"blacklist:jwt:{jti}", expires_in, "1")

def is_token_blacklisted(jti):
    return r.exists(f"blacklist:jwt:{jti}")
```

---

## 3. Leaderboard/Counters

### 3.1 Gaming Leaderboard

```python
# Sorted set per leaderboard
def add_score(game_id, player_id, score):
    key = f"leaderboard:{game_id}"
    r.zadd(key, {player_id: score})

def get_top_players(game_id, count=10):
    key = f"leaderboard:{game_id}"
    # ZREVRANGE returns highest scores first
    return r.zrevrange(key, 0, count - 1, withscores=True)

def get_player_rank(game_id, player_id):
    key = f"leaderboard:{game_id}"
    # ZREVRANK: 0 = highest
    rank = r.zrevrank(key, player_id)
    return rank + 1 if rank is not None else None

def get_player_score(game_id, player_id):
    key = f"leaderboard:{game_id}"
    return r.zscore(key, player_id)

def get_players_around(game_id, player_id, window=5):
    """Get players ranked around a specific player."""
    rank = r.zrevrank(f"leaderboard:{game_id}", player_id)
    if rank is None:
        return []
    start = max(0, rank - window)
    end = rank + window
    return r.zrevrange(f"leaderboard:{game_id}", start, end, withscores=True)
```

### 3.2 Real-time Counter

```python
# Page views
def increment_page_view(page_id):
    key = f"pageviews:{page_id}"
    return r.incr(key)

# Daily counter with automatic cleanup
def increment_daily(key):
    date = datetime.now().strftime('%Y-%m-%d')
    full_key = f"{key}:{date}"
    r.incr(full_key)
    r.expire(full_key, 86400 * 2)  # 2 days buffer

# Multi-dimensional counter
def track_event(event_type, dimensions):
    """Track events across multiple dimensions."""
    pipe = r.pipeline()
    ts = datetime.now()

    # Per-minute granularity
    minute_key = f"events:{event_type}:{ts.strftime('%Y%m%d%H%M')}"
    pipe.incr(minute_key)
    pipe.expire(minute_key, 86400)

    # Per dimension
    for dim_name, dim_value in dimensions.items():
        dim_key = f"events:{event_type}:{dim_name}:{dim_value}:{ts.strftime('%Y%m%d')}"
        pipe.incr(dim_key)
        pipe.expire(dim_key, 86400 * 7)

    pipe.execute()
```

### 3.3 Atomic Counter with Floor/Ceiling

```python
def bounded_increment(key, amount, max_value):
    """Increment but never exceed max_value. Returns new value or -1 if at max."""
    script = """
    local current = tonumber(redis.call('GET', KEYS[1]) or 0)
    local amount = tonumber(ARGV[1])
    local max_val = tonumber(ARGV[2])
    if current + amount > max_val then
        return -1
    end
    return redis.call('INCRBY', KEYS[1], amount)
    """
    return r.eval(script, 1, key, amount, max_value)
```

---

## 4. Message Queue

### 4.1 Basic Queue (List-based)

```python
# Producer
def enqueue_task(queue_name, task_data):
    r.lpush(f"queue:{queue_name}", json.dumps(task_data))

# Consumer
def dequeue_task(queue_name):
    # BRPOP: blocking pop (waits if empty)
    result = r.brpop(f"queue:{queue_name}", timeout=30)
    if result:
        _, task = result
        return json.loads(task)
    return None
```

### 4.2 Reliable Queue (RPOPLPUSH Pattern)

```python
def reliable_dequeue(queue_name, consumer_id, timeout=30):
    """Move task to processing list atomically. If consumer crashes,
    task can be recovered from the processing list."""
    processing_key = f"queue:{queue_name}:processing:{consumer_id}"
    result = r.brpoplpush(f"queue:{queue_name}", processing_key, timeout=timeout)
    return json.loads(result) if result else None

def ack_task(queue_name, consumer_id, task_data):
    """Acknowledge task completion by removing from processing list."""
    processing_key = f"queue:{queue_name}:processing:{consumer_id}"
    r.lrem(processing_key, 1, json.dumps(task_data))

def requeue_stale_tasks(queue_name, consumer_id, max_age=300):
    """Re-queue tasks from dead consumers."""
    processing_key = f"queue:{queue_name}:processing:{consumer_id}"
    tasks = r.lrange(processing_key, 0, -1)
    for task in tasks:
        r.lpush(f"queue:{queue_name}", task)
    r.delete(processing_key)
```

### 4.3 Priority Queue

```python
def enqueue_priority(queue_name, priority, task_data):
    # Priority: higher = more important (processed first)
    score = priority * 1e10 + time.time()
    r.zadd(f"queue:{queue_name}", {json.dumps(task_data): score})

def dequeue_priority(queue_name):
    result = r.zpopmax(f"queue:{queue_name}", 1)
    if result:
        task, _ = result[0]
        return json.loads(task)
    return None
```

### 4.4 Delayed Queue

```python
def enqueue_delayed(queue_name, task_data, delay_seconds):
    """Schedule a task for future execution."""
    execute_at = time.time() + delay_seconds
    r.zadd(f"queue:delayed:{queue_name}", {json.dumps(task_data): execute_at})

def process_delayed_queue(queue_name):
    """Move ready tasks from delayed queue to main queue."""
    now = time.time()
    ready = r.zrangebyscore(f"queue:delayed:{queue_name}", 0, now, start=0, num=100)
    if ready:
        pipe = r.pipeline()
        for task in ready:
            pipe.lpush(f"queue:{queue_name}", task)
            pipe.zrem(f"queue:delayed:{queue_name}", task)
        pipe.execute()
```

---

## 5. Real-time Analytics

### 5.1 Unique Visitors

```python
# HyperLogLog per conteggio unici
def track_visitor(page_id, visitor_id):
    key = f"uv:{page_id}"
    r.pfadd(key, visitor_id)

def get_unique_visitors(page_id):
    key = f"uv:{page_id}"
    return r.pfcount(key)

# Merge multiple days
def get_weekly_unique(page_id):
    keys = [f"uv:{page_id}:{(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')}" for i in range(7)]
    r.pfmerge(f"uv:{page_id}:week", *keys)
    return r.pfcount(f"uv:{page_id}:week")
```

### 5.2 Time-series Metrics

```python
# INCR + EXPIRE per rate metrics
def record_metric(metric_name, value=1):
    now = int(time.time())
    minute_key = f"metric:{metric_name}:{now // 60}"
    hour_key = f"metric:{metric_name}:{now // 3600}"

    pipe = r.pipeline()
    pipe.incrby(minute_key, value)
    pipe.incrby(hour_key, value)
    pipe.expire(minute_key, 86400)
    pipe.expire(hour_key, 604800)
    pipe.execute()

def get_metric_last_hour(metric_name):
    """Get per-minute metric values for the last hour."""
    now = int(time.time())
    pipe = r.pipeline()
    for i in range(60):
        minute = (now // 60) - i
        pipe.get(f"metric:{metric_name}:{minute}")
    results = pipe.execute()
    return [(i, int(v or 0)) for i, v in enumerate(results)]
```

### 5.3 Bitmap Analytics

```python
# Track daily active users with bitmaps (1 bit per user)
def mark_user_active(user_id, date=None):
    date = date or datetime.now().strftime('%Y-%m-%d')
    r.setbit(f"active:{date}", user_id, 1)

def count_active_users(date=None):
    date = date or datetime.now().strftime('%Y-%m-%d')
    return r.bitcount(f"active:{date}")

def users_active_both_days(date1, date2):
    """Count users active on both days (AND operation)."""
    r.bitop('AND', 'active:both', f'active:{date1}', f'active:{date2}')
    return r.bitcount('active:both')

def users_active_either_day(date1, date2):
    """Count users active on either day (OR operation)."""
    r.bitop('OR', 'active:either', f'active:{date1}', f'active:{date2}')
    return r.bitcount('active:either')

# 10 million users: only 1.25 MB per day!
```

---

## 6. Rate Limiting

### 6.1 Simple Rate Limit

```python
def is_rate_limited(identifier, limit, window_seconds):
    key = f"ratelimit:{identifier}"
    count = r.incr(key)

    if count == 1:
        r.expire(key, window_seconds)

    return count > limit, count

# Usage in API
allowed, count = is_rate_limited(client_ip, 100, 60)
if not allowed:
    return 429, "Rate limit exceeded"
```

### 6.2 Sliding Window

```lua
-- Redis script per sliding window
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local now = tonumber(ARGV[3])

redis.call('ZREMRANGEBYSCORE', key, 0, now - window)
local count = redis.call('ZCARD', key)

if count >= limit then
    return 0
end

redis.call('ZADD', key, now, tostring(now) .. ':' .. tostring(math.random(100000)))
redis.call('EXPIRE', key, window)
return 1
```

### 6.3 Tiered Rate Limiting

```python
def check_tiered_rate_limit(user_id, user_tier):
    """Different limits per tier."""
    tiers = {
        'free': {'per_minute': 10, 'per_hour': 100, 'per_day': 500},
        'pro': {'per_minute': 60, 'per_hour': 1000, 'per_day': 10000},
        'enterprise': {'per_minute': 300, 'per_hour': 5000, 'per_day': 50000},
    }

    limits = tiers.get(user_tier, tiers['free'])
    now = int(time.time())

    checks = [
        (f"rl:{user_id}:m:{now // 60}", limits['per_minute'], 60),
        (f"rl:{user_id}:h:{now // 3600}", limits['per_hour'], 3600),
        (f"rl:{user_id}:d:{now // 86400}", limits['per_day'], 86400),
    ]

    pipe = r.pipeline()
    for key, _, _ in checks:
        pipe.incr(key)
    counts = pipe.execute()

    pipe = r.pipeline()
    for i, (key, _, window) in enumerate(checks):
        if counts[i] == 1:
            pipe.expire(key, window)
    pipe.execute()

    for i, (_, limit, _) in enumerate(checks):
        if counts[i] > limit:
            return False, f"Rate limit exceeded at tier level"

    return True, "OK"
```

---

## 7. Distributed Lock

### 7.1 Simple Lock

```python
def acquire_lock(lock_name, ttl_seconds=10):
    lock_key = f"lock:{lock_name}"
    return r.set(lock_key, "1", nx=True, ex=ttl_seconds)

def release_lock(lock_name):
    r.delete(f"lock:{lock_name}")

# Usage
if acquire_lock("process:data"):
    try:
        process_data()
    finally:
        release_lock("process:data")
```

### 7.2 Safe Lock (Owner-based with Lua)

```lua
-- Lock with owner token (prevents accidental release by other processes)
-- acquire_lock.lua
local lock_key = KEYS[1]
local owner = ARGV[1]
local ttl = tonumber(ARGV[2])

if redis.call('SET', lock_key, owner, 'PX', ttl, 'NX') then
    return 1
end
return 0
```

```lua
-- release_lock.lua (only release if we own it)
local lock_key = KEYS[1]
local owner = ARGV[1]

local current_owner = redis.call('GET', lock_key)
if current_owner == owner then
    redis.call('DEL', lock_key)
    return 1
end
return 0
```

```python
import uuid

class DistributedLock:
    def __init__(self, redis_client, name, ttl_ms=10000):
        self.r = redis_client
        self.name = f"lock:{name}"
        self.owner = str(uuid.uuid4())
        self.ttl_ms = ttl_ms

        self._acquire_script = self.r.register_script("""
            if redis.call('SET', KEYS[1], ARGV[1], 'PX', ARGV[2], 'NX') then
                return 1
            end
            return 0
        """)

        self._release_script = self.r.register_script("""
            if redis.call('GET', KEYS[1]) == ARGV[1] then
                return redis.call('DEL', KEYS[1])
            end
            return 0
        """)

    def acquire(self):
        return bool(self._acquire_script(keys=[self.name], args=[self.owner, self.ttl_ms]))

    def release(self):
        return bool(self._release_script(keys=[self.name], args=[self.owner]))

    def __enter__(self):
        if not self.acquire():
            raise RuntimeError(f"Failed to acquire lock: {self.name}")
        return self

    def __exit__(self, *args):
        self.release()

# Usage
with DistributedLock(r, "process:orders"):
    process_orders()
```

### 7.3 Lock Extension (Watchdog Pattern)

```python
import threading

class ExtendableLock(DistributedLock):
    def __init__(self, redis_client, name, ttl_ms=10000, extend_interval_ms=None):
        super().__init__(redis_client, name, ttl_ms)
        self.extend_interval = (extend_interval_ms or ttl_ms // 3) / 1000
        self._watchdog = None

        self._extend_script = self.r.register_script("""
            if redis.call('GET', KEYS[1]) == ARGV[1] then
                return redis.call('PEXPIRE', KEYS[1], ARGV[2])
            end
            return 0
        """)

    def _start_watchdog(self):
        def extend_loop():
            while self._active:
                time.sleep(self.extend_interval)
                if self._active:
                    self._extend_script(keys=[self.name], args=[self.owner, self.ttl_ms])

        self._active = True
        self._watchdog = threading.Thread(target=extend_loop, daemon=True)
        self._watchdog.start()

    def acquire(self):
        result = super().acquire()
        if result:
            self._start_watchdog()
        return result

    def release(self):
        self._active = False
        return super().release()
```

---

## 8. Geospatial Indexes

### 8.1 Storing Locations

```bash
# Add locations with longitude, latitude, and member name
GEOADD locations -73.985428 40.748817 "Empire State Building"
GEOADD locations -73.968285 40.785091 "Central Park"
GEOADD locations -74.044500 40.689247 "Statue of Liberty"
```

### 8.2 Geospatial Queries

```python
# Add locations
r.geoadd('restaurants', (-73.985, 40.748, 'restaurant-a'))
r.geoadd('restaurants', (-73.975, 40.752, 'restaurant-b'))
r.geoadd('restaurants', (-73.965, 40.760, 'restaurant-c'))

# Find restaurants within 2km of a point
nearby = r.geosearch(
    'restaurants',
    longitude=-73.980,
    latitude=40.750,
    radius=2,
    unit='km',
    sort='ASC',
    withcoord=True,
    withdist=True
)
# Returns: [(name, distance, (lon, lat)), ...]

# Distance between two members
dist = r.geodist('restaurants', 'restaurant-a', 'restaurant-b', unit='km')

# Get coordinates of a member
coords = r.geopos('restaurants', 'restaurant-a')

# Geohash
hash_val = r.geohash('restaurants', 'restaurant-a')
```

### 8.3 Ride-Sharing Driver Tracking

```python
def update_driver_location(driver_id, lon, lat):
    """Update driver position and track availability."""
    r.geoadd('drivers:active', (lon, lat, driver_id))
    r.setex(f'driver:heartbeat:{driver_id}', 60, '1')

def find_nearest_drivers(rider_lon, rider_lat, radius_km=5, count=10):
    """Find nearest available drivers."""
    return r.geosearch(
        'drivers:active',
        longitude=rider_lon,
        latitude=rider_lat,
        radius=radius_km,
        unit='km',
        sort='ASC',
        count=count,
        withcoord=True,
        withdist=True
    )

def remove_inactive_drivers():
    """Clean up drivers who stopped sending heartbeats."""
    members = r.zrange('drivers:active', 0, -1)
    for driver_id in members:
        if not r.exists(f'driver:heartbeat:{driver_id}'):
            r.zrem('drivers:active', driver_id)
```

---

## 9. Full-Text Search with RediSearch

### 9.1 Overview

RediSearch is a Redis module providing full-text search, secondary indexing, and aggregation. Available in Redis Stack or as a standalone module.

```bash
# Create an index
FT.CREATE idx:products ON HASH PREFIX 1 "product:"
  SCHEMA
    name TEXT WEIGHT 5.0
    description TEXT
    price NUMERIC SORTABLE
    category TAG
    location GEO
```

### 9.2 Querying

```bash
# Full-text search
FT.SEARCH idx:products "wireless headphones"

# Filtered search with price range
FT.SEARCH idx:products "headphones @price:[50 200]"

# Tag filter
FT.SEARCH idx:products "@category:{electronics|audio}"

# Geo filter
FT.SEARCH idx:products "@location:[-73.98 40.75 10 km]"

# Aggregation
FT.AGGREGATE idx:products "*"
  GROUPBY 1 @category
  REDUCE COUNT 0 AS total
  SORTBY 2 @total DESC
```

---

## 10. Client-Side Caching

### 10.1 Server-Assisted Client Caching (Redis 6+)

```python
# redis-py 5.x with RESP3 and tracking
r = redis.Redis(
    host='localhost',
    port=6379,
    protocol=3,
    cache_enabled=True,
    cache_max_size=10000,
    cache_ttl=300
)

# First call: server roundtrip
value = r.get('config:feature_flag')

# Second call: served from local cache
value = r.get('config:feature_flag')

# If another client modifies 'config:feature_flag', the server pushes
# an invalidation message, and the next get() fetches from server
```

### 10.2 When to Use Client-Side Caching

| Scenario | Benefit |
|---|---|
| Configuration flags read by every request | Eliminates roundtrip for hot keys |
| User profile data in API gateway | Sub-microsecond reads |
| Feature flags | Near-zero latency |
| Session data (read-heavy) | Reduces Redis QPS |

---

## 11. Best Practices

### 11.1 Key Naming

```python
# Convention: object-type:id:field
# Use colons as separators (community standard)

# Good
user:123:profile
session:abc123
cache:page:home
queue:emails:pending

# Avoid
u123p              # ambiguous
profile_123        # inconsistent separator
User:123:Profile   # inconsistent casing
```

### 11.2 TTL Management

```python
# Always set TTL on cache keys (prevent memory leaks)
r.setex('temp:data', 3600, value)     # 1 hour
r.setex('session:xyz', 86400, value)  # 24 hours

# Update TTL on access (sliding expiration)
r.expire('cache:item', 3600)

# Add jitter to prevent stampede
import random
base_ttl = 3600
jitter = random.randint(-360, 360)
r.setex(key, base_ttl + jitter, value)

# WARNING: no TTL = permanent memory consumption
# Always audit keys without TTL:
# redis-cli --scan | while read key; do
#   ttl=$(redis-cli TTL "$key")
#   if [ "$ttl" = "-1" ]; then echo "NO TTL: $key"; fi
# done
```

### 11.3 Memory Optimization

```python
# Use Hashes for small related data (listpack encoding saves memory)
r.hset('user:123', mapping={'name': 'John', 'email': 'john@test.com', 'age': '30'})

# vs individual keys (much higher memory overhead)
r.set('user:123:name', 'John')  # ~90 bytes per key
r.set('user:123:email', 'john@test.com')
r.set('user:123:age', '30')

# Compress large values
import zlib
compressed = zlib.compress(json.dumps(large_data).encode())
r.setex('large:data', 3600, compressed)
# Decompress on read
data = json.loads(zlib.decompress(r.get('large:data')))
```

### 11.4 Pipeline Everything

```python
# BAD: 100 round trips
for key in keys:
    r.get(key)

# GOOD: 1 round trip
pipe = r.pipeline(transaction=False)
for key in keys:
    pipe.get(key)
results = pipe.execute()
```

### 11.5 Use SCAN, Never KEYS

```python
# BAD (blocks Redis, O(N) on entire keyspace)
keys = r.keys('user:*')

# GOOD (non-blocking, cursor-based iteration)
cursor = 0
all_keys = []
while True:
    cursor, keys = r.scan(cursor=cursor, match='user:*', count=100)
    all_keys.extend(keys)
    if cursor == 0:
        break
```

---

## 12. Anti-Patterns

### 12.1 Redis as Primary Database Without Backup

Storing data exclusively in Redis without persistence or backup is a recipe for data loss. Redis can be a primary store, but it must have AOF enabled and regular backups.

### 12.2 Storing Large Blobs

```python
# BAD: 50MB video file in Redis
r.set('video:123', video_bytes)  # Wastes expensive RAM

# GOOD: Store metadata in Redis, blob in object storage
r.hset('video:123', mapping={
    'url': 's3://bucket/videos/123.mp4',
    'size': '52428800',
    'duration': '120'
})
```

### 12.3 Using Redis as a General-Purpose Database

Redis lacks: transactions with rollback, JOINs, complex queries, referential integrity. Use it for what it excels at (cache, session, queue, real-time analytics), not as a replacement for PostgreSQL.

### 12.4 Unbounded Collections

```python
# BAD: List that grows forever
r.lpush('all_events', json.dumps(event))

# GOOD: Bounded list
r.lpush('recent_events', json.dumps(event))
r.ltrim('recent_events', 0, 9999)  # Keep last 10000
```

### 12.5 Relying on KEYS for Application Logic

```python
# BAD: scanning keys as a poor-man's index
keys = r.keys('order:*:status:pending')  # Blocks Redis

# GOOD: maintain an explicit index
r.sadd('orders:pending', order_id)
pending_orders = r.smembers('orders:pending')
```

### 12.6 Hot Key Problem

```python
# BAD: single counter for all traffic
r.incr('global:page_views')  # Bottleneck

# GOOD: shard the counter
shard = hash(request_id) % 10
r.incr(f'page_views:shard:{shard}')

# Aggregate periodically
total = sum(int(r.get(f'page_views:shard:{i}') or 0) for i in range(10))
```

---

## 13. Configuration Best Practices

### 13.1 Production Configuration Template

```bash
# Memory
maxmemory 4gb
maxmemory-policy allkeys-lfu
maxmemory-samples 10

# Persistence
appendonly yes
appendfsync everysec
aof-use-rdb-preamble yes
save 3600 1
save 300 100
no-appendfsync-on-rewrite yes

# Network
bind 10.0.0.1 127.0.0.1
protected-mode yes
tcp-keepalive 300
tcp-backlog 511
timeout 300

# Clients
maxclients 10000

# Security
requirepass <strong-password>
rename-command FLUSHALL ""
rename-command FLUSHDB ""
rename-command DEBUG ""

# Performance
lazyfree-lazy-eviction yes
lazyfree-lazy-expire yes
lazyfree-lazy-server-del yes
lazyfree-lazy-user-del yes

# I/O threads (Redis 6+)
io-threads 4
io-threads-do-reads yes

# Listpack thresholds (Redis 7+)
hash-max-listpack-entries 128
hash-max-listpack-value 64
zset-max-listpack-entries 128
zset-max-listpack-value 64

# Logging
loglevel notice
logfile /var/log/redis/redis-server.log

# Slow log
slowlog-log-slower-than 10000
slowlog-max-len 256
```

### 13.2 OS Tuning

```bash
# Disable THP
echo never > /sys/kernel/mm/transparent_hugepage/enabled

# Memory overcommit
sysctl vm.overcommit_memory=1

# Max open files
ulimit -n 65535

# TCP tuning
sysctl net.core.somaxconn=65535
sysctl net.ipv4.tcp_max_syn_backlog=65535

# Low swappiness
sysctl vm.swappiness=1
```

---

## 14. Monitoring and Observability

### 14.1 Essential Metrics

```bash
# Commands/second
INFO stats
# instantaneous_ops_per_sec

# Memory usage
INFO memory
# used_memory, used_memory_rss, mem_fragmentation_ratio

# Cache hit ratio
# keyspace_hits / (keyspace_hits + keyspace_misses)

# Connected clients
INFO clients
# connected_clients, blocked_clients

# Evicted keys
INFO stats
# evicted_keys (should be 0 for non-cache workloads)

# Replication lag
INFO replication
# master_repl_offset vs slave_repl_offset
```

### 14.2 Health Check Script

```bash
#!/bin/bash
# redis-health.sh

REDIS_CLI="redis-cli -a $REDIS_PASSWORD"

echo "=== Redis Health Check ==="

# Ping
$REDIS_CLI PING

# Memory
MEM=$($REDIS_CLI INFO memory | grep used_memory_human | cut -d: -f2 | tr -d '\r')
MAXMEM=$($REDIS_CLI INFO memory | grep maxmemory_human | cut -d: -f2 | tr -d '\r')
echo "Memory: $MEM / $MAXMEM"

# Hit ratio
HITS=$($REDIS_CLI INFO stats | grep keyspace_hits | cut -d: -f2 | tr -d '\r')
MISSES=$($REDIS_CLI INFO stats | grep keyspace_misses | cut -d: -f2 | tr -d '\r')
TOTAL=$((HITS + MISSES))
if [ $TOTAL -gt 0 ]; then
    RATIO=$(echo "scale=4; $HITS / $TOTAL * 100" | bc)
    echo "Hit Ratio: ${RATIO}%"
fi

# OPS/sec
OPS=$($REDIS_CLI INFO stats | grep instantaneous_ops_per_sec | cut -d: -f2 | tr -d '\r')
echo "OPS/sec: $OPS"

# Connected clients
CLIENTS=$($REDIS_CLI INFO clients | grep connected_clients | cut -d: -f2 | tr -d '\r')
echo "Clients: $CLIENTS"

# Slowlog entries
SLOW=$($REDIS_CLI SLOWLOG LEN)
echo "Slowlog entries: $SLOW"
```

### 14.3 Alerting Thresholds

| Metric | Warning | Critical |
|---|---|---|
| Memory usage | > 80% maxmemory | > 95% maxmemory |
| Hit ratio | < 90% | < 70% |
| Evicted keys/sec | > 100 | > 1000 |
| Connected clients | > 80% maxclients | > 95% maxclients |
| Replication lag | > 1 second | > 10 seconds |
| Slowlog entries/min | > 10 | > 100 |

---

## 15. Operational Procedures

### 15.1 Capacity Planning

```bash
# Estimate memory per key type
MEMORY USAGE user:123              # Per-key memory
redis-cli --bigkeys                # Find largest keys
redis-cli --memkeys                # Full memory analysis

# Formula:
# Total memory = (avg_key_size * num_keys) + (overhead * num_keys) + redis_base_memory
# Overhead per key ≈ 70-100 bytes (dictEntry + SDS + redisObject)
# Plan for: maxmemory = total_memory * 1.3 (headroom for fragmentation + COW)
```

### 15.2 Scale-Up Checklist

When Redis needs more capacity:

1. **First**: Optimize key design (Hashes vs individual keys, shorter key names)
2. **Second**: Compress large values
3. **Third**: Set appropriate TTLs (reduce waste)
4. **Fourth**: Increase maxmemory
5. **Fifth**: Add replicas for read scaling
6. **Sixth**: Migrate to Redis Cluster for horizontal scaling

### 15.3 Production Deployment Checklist

```
Pre-deploy:
  [ ] maxmemory set with appropriate policy
  [ ] Persistence configured (AOF + RDB)
  [ ] bind restricted to private interfaces
  [ ] Authentication enabled (requirepass or ACLs)
  [ ] TLS enabled for inter-node and client traffic
  [ ] Dangerous commands disabled/restricted
  [ ] Monitoring and alerting configured
  [ ] Backup automation in place
  [ ] OS tuning applied (THP, overcommit, ulimit)

Post-deploy:
  [ ] Verify PING responds
  [ ] Verify persistence is active (INFO persistence)
  [ ] Verify clients can connect
  [ ] Run redis-benchmark for baseline
  [ ] Verify backup cron is running
  [ ] Test restore from backup
```

---

## 16. Troubleshooting

### 16.1 Redis Running Out of Memory

**Symptoms**: `OOM command not allowed when used memory > 'maxmemory'`

**Diagnosis**:
```bash
INFO memory
redis-cli --bigkeys
```

**Resolution**: Increase `maxmemory`, set eviction policy, audit keys without TTL, compress large values.

### 16.2 High Latency on Simple Commands

**Symptoms**: GET/SET latency > 5ms intermittently.

**Diagnosis**:
```bash
LATENCY LATEST
SLOWLOG GET 20
redis-cli --latency-history
```

**Common causes**: BGSAVE fork, THP, swap, expensive commands (KEYS, SORT), Lua scripts.

### 16.3 Connection Refused

**Symptoms**: Clients get `ECONNREFUSED`.

**Diagnosis**: Check `maxclients`, firewall, bind address, `protected-mode`.

```bash
CONFIG GET maxclients
redis-cli CLIENT LIST | wc -l
netstat -tlnp | grep 6379
```

### 16.4 Data Missing After Restart

**Symptoms**: `DBSIZE` returns 0 after restart.

**Cause**: Persistence not configured, or `SHUTDOWN NOSAVE` was used.

**Resolution**: Check `appendonly` and `save` settings. Restore from backup if available.

### 16.5 Replica Lag Increasing

**Symptoms**: `INFO replication` shows growing offset difference.

**Cause**: Network bandwidth, high write rate, slow disk on replica.

**Resolution**: Check network, increase replica's disk I/O capacity, consider diskless replication.

### 16.6 High CPU with Low QPS

**Symptoms**: CPU near 100% despite low command rate.

**Diagnosis**:
```bash
INFO commandstats
SLOWLOG GET 50
```

**Cause**: Expensive commands (ZUNIONSTORE on large sets, SORT, pattern-based SCAN, Lua scripts).

### 16.7 Cache Stampede After Restart

**Symptoms**: Database overwhelmed after Redis restart (cold cache).

**Resolution**: Implement cache warming at startup. Use stale-while-revalidate pattern. Implement locking on cache miss.

### 16.8 Memory Fragmentation

**Symptoms**: `used_memory_rss` is much higher than `used_memory`.

**Diagnosis**:
```bash
INFO memory
# mem_fragmentation_ratio > 1.5 indicates fragmentation
```

**Resolution**: Enable `activedefrag yes`. For extreme fragmentation (ratio > 2), consider restarting Redis.

### 16.9 Pub/Sub Messages Lost

**Symptoms**: Subscribers miss messages.

**Cause**: Pub/Sub is fire-and-forget. If subscriber was disconnected, messages are lost.

**Resolution**: Use Redis Streams for reliable delivery with acknowledgment.

### 16.10 Lock Not Released After Crash

**Symptoms**: Distributed lock stays acquired after the lock holder crashes.

**Cause**: Lock was acquired without TTL, or TTL is too long.

**Resolution**: Always set a TTL on locks. Use the owner-based lock pattern with Lua-based release.

### 16.11 Hot Key Bottleneck

**Symptoms**: One key receives disproportionate traffic, causing that node (in cluster) to be overloaded.

**Diagnosis**:
```bash
redis-cli --hotkeys  # Requires LFU policy
OBJECT FREQ hot_key
```

**Resolution**: Shard the key (e.g., counter sharding), use client-side caching, replicate for read distribution.

---

## 17. FAQ

### Q1: How many keys can Redis handle?

Theoretically 2^32 (4+ billion). Practically limited by memory. Each key has ~70-100 bytes of overhead.

### Q2: When should I choose Redis over Memcached?

Choose Redis for: data structures beyond strings, persistence, replication, Pub/Sub, Lua scripting, Streams. Choose Memcached for: pure key-value caching with multi-threaded performance.

### Q3: Is Redis thread-safe?

Redis command execution is single-threaded (atomic). Client libraries handle thread safety via connection pooling (pooled clients) or multiplexed connections (Lettuce, ioredis).

### Q4: How do I handle cache invalidation?

Options: TTL-based expiration, event-driven invalidation (delete on write), version-based invalidation, Pub/Sub broadcast invalidation across app instances.

### Q5: What is the maximum value size in Redis?

512 MB per string value. However, values over 1MB are an anti-pattern. Compress or split large values.

### Q6: Should I use separate Redis instances for different concerns?

Yes, for production. Separate cache (volatile, eviction enabled) from session store (durable, no eviction) from queue (durable, different TTL). Different eviction policies and persistence settings per concern.

### Q7: How do I handle Redis failover in my application?

Use Sentinel-aware clients (redis-py Sentinel, ioredis sentinel config) that automatically discover the new master. Handle `ReadOnlyError` with retry logic. Implement circuit breaker for extended outages.

### Q8: Can Redis replace a message queue like RabbitMQ or Kafka?

For simple queues: yes (Lists with BRPOP, or Streams with consumer groups). For complex routing, dead-letter exchanges, or multi-consumer patterns at scale: RabbitMQ or Kafka are more appropriate.

### Q9: How do I secure Redis in production?

1. Bind to private interfaces only
2. Enable authentication (ACLs)
3. Enable TLS
4. Disable dangerous commands
5. Use firewall rules to restrict access
6. Run as unprivileged user
7. Keep Redis updated

### Q10: What is the difference between DEL and UNLINK?

`DEL` is synchronous -- it blocks Redis until the key is freed (O(N) for large collections). `UNLINK` (Redis 4+) is asynchronous -- it removes the key from the keyspace immediately and frees memory in a background thread.

### Q11: How do I migrate from standalone Redis to Redis Cluster?

1. Analyze key access patterns for multi-key operations
2. Add hash tags where multi-key atomicity is needed
3. Set up the cluster (minimum 6 nodes)
4. Use `redis-cli --cluster import` to migrate data
5. Update client code to use cluster-aware clients
6. Switch traffic

### Q12: What is the Redis Modules ecosystem?

Key modules: RediSearch (full-text search), RedisJSON (JSON document operations), RedisTimeSeries (time-series data), RedisGraph (graph database), RedisBloom (probabilistic data structures). Available individually or bundled in Redis Stack.

---

*Questo documento fa parte del modulo 06 "NoSQL Redis" della Data Encyclopedia.*
