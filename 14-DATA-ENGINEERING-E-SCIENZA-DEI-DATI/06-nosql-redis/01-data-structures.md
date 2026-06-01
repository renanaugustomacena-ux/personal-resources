# Redis Data Structures e Use Cases

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
1. Redis Overview
2. Strings
3. Lists
4. Sets
5. Sorted Sets
6. Hashes
7. HyperLogLog
8. Bitmaps
9. Streams
10. Geospatial Indexes
11. Redis 7+ Data Type Enhancements
12. Internal Encoding and Memory
13. Key Management
14. Configuration Reference
15. Monitoring and Observability
16. Troubleshooting
17. FAQ

---

## 1. Redis Overview

### 1.1 What is Redis

Redis is an in-memory data structure store used as a database, cache, and message broker. Unlike simple key-value stores, Redis supports complex data types with atomic operations on each type. All data lives in memory for sub-millisecond latency, with optional persistence to disk.

**Key Features**:
- In-memory storage with optional disk persistence (RDB/AOF)
- Rich data structures: Strings, Lists, Sets, Sorted Sets, Hashes, Streams, and more
- Master-replica replication with automatic failover (Sentinel)
- Horizontal scaling via Redis Cluster (16384 hash slots)
- Pub/Sub and Streams for messaging
- Lua scripting and Redis Functions for server-side logic
- TTL-based key expiration with multiple eviction policies
- Transactions (MULTI/EXEC) and optimistic locking (WATCH)

### 1.2 Architecture at a Glance

```
Client → Network I/O → Command Parser → Single-threaded Event Loop → Data Structures (in memory)
                                                                          ↕
                                                                    Persistence (RDB/AOF on disk)
```

Redis processes commands sequentially in a single thread. This eliminates locking overhead and guarantees atomicity of individual commands. Redis 6+ offloads network I/O to separate threads (configurable via `io-threads`), but command execution remains single-threaded.

### 1.3 Data Types Summary

| Type | Internal Encoding | Primary Operations | Typical Use Case |
|---|---|---|---|
| String | int, embstr, raw | GET, SET, INCR, APPEND | Cache, counters, flags |
| List | listpack, quicklist | LPUSH, RPOP, LRANGE | Queues, timelines |
| Set | listpack, hashtable | SADD, SISMEMBER, SINTER | Tags, unique items |
| Sorted Set | listpack, skiplist+hashtable | ZADD, ZRANGE, ZRANK | Leaderboards, priority queues |
| Hash | listpack, hashtable | HSET, HGET, HGETALL | Objects, user profiles |
| Stream | radix tree + listpack | XADD, XREAD, XREADGROUP | Event logs, message queues |
| HyperLogLog | String (sparse or dense) | PFADD, PFCOUNT, PFMERGE | Unique visitor counting |
| Bitmap | String | SETBIT, GETBIT, BITCOUNT | Daily active users, flags |
| Geospatial | Sorted Set | GEOADD, GEOSEARCH | Location-based search |

---

## 2. Strings

### 2.1 What Strings Are

Strings are the most fundamental Redis data type. A String value can hold text, serialized JSON, binary data (images, protobuf), or numeric values. The maximum size is 512 MB, though values over 1 MB are an anti-pattern.

### 2.2 Basic Operations

```bash
# Set/Get
SET user:1 "John"
GET user:1

# Set with TTL (seconds)
SET session:abc "user_data" EX 3600

# Set with TTL (milliseconds)
SET session:abc "user_data" PX 3600000

# Set only if key does NOT exist (atomic create)
SET lock:resource "owner123" NX EX 10

# Set only if key already exists (atomic update)
SET user:1 "Jane" XX

# Get and set atomically (returns old value)
GETSET counter 0

# Get and delete atomically (Redis 6.2+)
GETDEL temp:key

# Get and set expiration atomically (Redis 6.2+)
GETEX mykey EX 300
```

### 2.3 Numeric Operations

```bash
# Increment/Decrement
INCR counter              # +1 (atomic)
DECR counter              # -1
INCRBY counter 10         # +10
DECRBY counter 5          # -5
INCRBYFLOAT counter 1.5   # +1.5 (floating point)

# These operations are atomic -- safe for concurrent access
# INCR on a non-existent key initializes it to 0 before incrementing
```

### 2.4 Multiple Keys

```bash
# Set multiple keys atomically
MSET key1 value1 key2 value2 key3 value3

# Set multiple keys only if NONE exist (atomic)
MSETNX key1 value1 key2 value2

# Get multiple keys in one call
MGET key1 key2 key3
```

### 2.5 String Manipulation

```bash
# Append
APPEND mykey " world"       # "hello" -> "hello world"

# Get substring
GETRANGE mykey 0 4           # "hello"

# Set substring
SETRANGE mykey 6 "Redis"     # "hello Redis"

# String length
STRLEN mykey                 # 11
```

### 2.6 Use Cases

```bash
# Cache: store serialized objects
SET user:1:profile '{"name":"John","email":"john@example.com"}'
GET user:1:profile

# Session: with TTL
SET session:abc "user_data" EX 3600

# Counter: atomic increment
INCR page_views:home

# Rate limiter: increment with TTL
INCR ratelimit:ip:192.168.1.1
EXPIRE ratelimit:ip:192.168.1.1 60

# Distributed lock: NX + EX
SET lock:order:1001 "worker-5" NX EX 10
```

---

## 3. Lists

### 3.1 What Lists Are

Redis Lists are ordered sequences of strings implemented as doubly-linked lists (quicklist in practice: a linked list of ziplist/listpack nodes). They support O(1) push/pop at both ends and O(N) indexed access.

### 3.2 List Operations

```bash
# Push (left = head, right = tail)
LPUSH mylist "first"        # ["first"]
RPUSH mylist "last"         # ["first", "last"]
LPUSH mylist "new_first"    # ["new_first", "first", "last"]

# Pop
LPOP mylist                 # "new_first"
RPOP mylist                 # "last"

# Pop multiple (Redis 6.2+)
LPOP mylist 3               # ["a", "b", "c"]

# Blocking pop (wait for element)
BLPOP queue:tasks 30        # Block up to 30 seconds
BRPOP queue:tasks 0         # Block indefinitely

# Range
LRANGE mylist 0 -1          # All elements
LRANGE mylist 0 9           # First 10

# Trim (keep only specified range)
LTRIM mylist 0 99           # Keep first 100

# Index access
LINDEX mylist 0             # Get element at index 0
LSET mylist 0 "new_value"   # Set element at index 0

# Length
LLEN mylist

# Insert
LINSERT mylist BEFORE "pivot" "new_element"
LINSERT mylist AFTER "pivot" "new_element"

# Remove elements by value
LREM mylist 2 "value"       # Remove first 2 occurrences of "value"
LREM mylist -2 "value"      # Remove last 2 occurrences
LREM mylist 0 "value"       # Remove all occurrences

# Move between lists (Redis 6.2+)
LMOVE source destination LEFT RIGHT   # Pop from source head, push to destination tail
BLMOVE source destination LEFT RIGHT 30  # Blocking version

# Pop from one list, push to another (atomic)
RPOPLPUSH source destination           # Deprecated in Redis 6.2, use LMOVE
```

### 3.3 Use Cases

```bash
# Message queue (FIFO)
LPUSH queue:tasks "task1"
RPOP queue:tasks             # Process oldest first

# Blocking queue (consumer waits for work)
BRPOP queue:tasks 30

# Recent items (bounded list)
LPUSH recent:views "item:123"
LTRIM recent:views 0 99     # Keep last 100

# Timeline
LPUSH timeline:user:1 "post:456"
LRANGE timeline:user:1 0 19  # Last 20 posts

# Reliable queue (RPOPLPUSH pattern)
RPOPLPUSH queue:tasks queue:processing
# Process... then remove from processing list
```

---

## 4. Sets

### 4.1 What Sets Are

Redis Sets are unordered collections of unique strings. They support O(1) membership tests and standard set operations (union, intersection, difference).

### 4.2 Set Operations

```bash
# Add/Remove
SADD tags:post:1 "redis" "database" "nosql"
SREM tags:post:1 "nosql"

# Membership test
SISMEMBER tags:post:1 "redis"        # 1 (true)
SMISMEMBER tags:post:1 "redis" "sql" # [1, 0] (Redis 6.2+)

# Members
SMEMBERS tags:post:1                  # All members (O(N), avoid on large sets)
SRANDMEMBER tags:post:1 3             # 3 random members
SPOP tags:post:1                      # Remove and return random member

# Cardinality
SCARD tags:post:1                     # Count of members

# Set operations
SINTER set1 set2                      # Intersection
SUNION set1 set2                      # Union
SDIFF set1 set2                       # Difference (in set1 but not set2)

# Store set operation results
SINTERSTORE result set1 set2
SUNIONSTORE result set1 set2
SDIFFSTORE result set1 set2

# Scan (non-blocking iteration for large sets)
SSCAN tags:post:1 0 MATCH "r*" COUNT 100
```

### 4.3 Use Cases

```bash
# Unique visitors
SADD visitors:2024-01-01 "user:123"
SCARD visitors:2024-01-01            # Count unique

# Tags / labels
SADD tags:article:1 "tech" "database"
SINTER tags:article:1 tags:article:2 # Articles with common tags

# Online users
SADD online:users "user:1" "user:2"
SISMEMBER online:users "user:1"      # Is user online?
SREM online:users "user:1"           # User went offline

# Social: mutual friends
SINTER friends:user:1 friends:user:2 # Mutual friends
SDIFF friends:user:1 friends:user:2  # Friends of user1 not friends of user2
```

---

## 5. Sorted Sets

### 5.1 What Sorted Sets Are

Sorted Sets (ZSets) combine Set uniqueness with score-based ordering. Each member has an associated floating-point score. Members are unique, but scores can repeat. Internally implemented as a skip list + hash table for O(log N) insertion and O(log N + M) range queries.

### 5.2 ZSet Operations

```bash
# Add with score
ZADD leaderboard 100 "player1"
ZADD leaderboard 200 "player2" 150 "player3"

# Update score (ZADD updates if member exists)
ZADD leaderboard 250 "player1"       # Update player1's score

# Flags (Redis 6.2+)
ZADD leaderboard GT 300 "player1"    # Only update if new score > current
ZADD leaderboard LT 50 "player1"    # Only update if new score < current
ZADD leaderboard NX 100 "player4"   # Only add, never update
ZADD leaderboard XX 100 "player1"   # Only update, never add

# Range by rank (index)
ZRANGE leaderboard 0 9              # Top 10 (ascending)
ZRANGE leaderboard 0 9 REV          # Top 10 (descending) -- Redis 6.2+
ZREVRANGE leaderboard 0 9 WITHSCORES # Top 10 descending with scores

# Range by score
ZRANGEBYSCORE leaderboard 100 200
ZRANGEBYSCORE leaderboard -inf +inf  # All members
ZRANGEBYSCORE leaderboard 100 200 LIMIT 0 10  # Paginate

# Redis 6.2+ unified ZRANGE
ZRANGE leaderboard 100 200 BYSCORE LIMIT 0 10
ZRANGE leaderboard "[a" "[z" BYLEX   # Lexicographic range

# Score operations
ZINCRBY leaderboard 50 "player1"     # Increment score
ZSCORE leaderboard "player1"         # Get score
ZMSCORE leaderboard "player1" "player2" # Multiple scores (Redis 6.2+)

# Rank
ZRANK leaderboard "player1"          # Rank (ascending, 0-based)
ZREVRANK leaderboard "player1"       # Rank (descending, 0-based)

# Cardinality
ZCARD leaderboard                    # Total members
ZCOUNT leaderboard 100 200           # Members with score in range

# Remove
ZREM leaderboard "player1"
ZREMRANGEBYRANK leaderboard 0 -11    # Keep top 10
ZREMRANGEBYSCORE leaderboard -inf 50 # Remove low scores

# Pop (Redis 5+)
ZPOPMIN leaderboard 1                # Remove lowest score member
ZPOPMAX leaderboard 1                # Remove highest score member
BZPOPMIN leaderboard 30              # Blocking version
BZPOPMAX leaderboard 30

# Set operations
ZUNIONSTORE result 2 set1 set2 WEIGHTS 1 2   # Weighted union
ZINTERSTORE result 2 set1 set2 AGGREGATE MAX  # Intersection with MAX
ZDIFFSTORE result 2 set1 set2                 # Difference (Redis 6.2+)

# Scan
ZSCAN leaderboard 0 MATCH "player:*" COUNT 100
```

### 5.3 Use Cases

```bash
# Leaderboard
ZADD game:scores 1500 "player1"
ZREVRANGE game:scores 0 9 WITHSCORES    # Top 10

# Priority queue
ZADD priority_queue 1 "critical_task"
ZADD priority_queue 5 "low_task"
ZPOPMIN priority_queue 1                 # Process highest priority

# Time-series index (score = timestamp)
ZADD events:2024 1704067200 "event:1"
ZRANGEBYSCORE events:2024 1704067200 1704153600  # Events in time range

# Delayed job scheduler
ZADD delayed:jobs 1704067200 '{"job":"send_email","to":"user@example.com"}'
# Worker polls: ZRANGEBYSCORE delayed:jobs 0 <current_timestamp> LIMIT 0 10

# Autocomplete
ZADD autocomplete 0 "redis"
ZADD autocomplete 0 "react"
ZADD autocomplete 0 "ruby"
ZRANGEBYLEX autocomplete "[re" "[re\xff" LIMIT 0 10  # Prefix search

# Ranking with ties
ZADD rankings 95.5 "Alice"
ZADD rankings 95.5 "Bob"    # Same score: sorted lexicographically
ZREVRANGE rankings 0 -1 WITHSCORES
```

---

## 6. Hashes

### 6.1 What Hashes Are

Redis Hashes are maps of field-value pairs, ideal for representing objects. A Hash with fewer than `hash-max-listpack-entries` fields (default 128) uses a memory-efficient listpack encoding.

### 6.2 Hash Operations

```bash
# Set/Get fields
HSET user:1 name "John" email "john@example.com" age "30"
HGET user:1 name
HMGET user:1 name email        # Multiple fields

# All fields and values
HGETALL user:1

# Fields and values separately
HKEYS user:1                   # All field names
HVALS user:1                   # All values
HLEN user:1                    # Number of fields

# Field existence
HEXISTS user:1 name            # 1 (true) or 0 (false)

# Delete field
HDEL user:1 age

# Increment numeric field
HINCRBY user:1 age 1
HINCRBYFLOAT user:1 balance 10.50

# Set field only if it does NOT exist
HSETNX user:1 created_at "2024-01-01"

# String length of a field value
HSTRLEN user:1 name

# Random fields (Redis 6.2+)
HRANDFIELD user:1 3            # 3 random field names
HRANDFIELD user:1 3 WITHVALUES # 3 random field-value pairs

# Scan (non-blocking iteration)
HSCAN user:1 0 MATCH "e*" COUNT 100
```

### 6.3 Use Cases

```bash
# Object storage (user profile)
HSET user:10 name "John" age "30" city "NYC" role "admin"
HGETALL user:10

# Counters per object
HINCRBY page:home views 1
HINCRBY page:home unique_visitors 1

# Configuration store
HSET config:app feature_x "enabled" max_retries "3" timeout "5000"
HGET config:app feature_x

# Session data (individual field access without full deserialization)
HSET session:abc user_id "123" ip "10.0.0.1" role "user"
HGET session:abc role
```

---

## 7. HyperLogLog

### 7.1 What HyperLogLog Is

HyperLogLog (HLL) is a probabilistic data structure for estimating cardinality (count of unique elements) with a standard error of 0.81%. It uses only 12 KB of memory regardless of the number of elements added -- making it ideal for counting unique items at scale.

### 7.2 HLL Operations

```bash
# Add elements
PFADD hll:visitors "user1" "user2" "user3"

# Count unique elements (approximate)
PFCOUNT hll:visitors           # 3

# Adding duplicates does not increase count
PFADD hll:visitors "user1"
PFCOUNT hll:visitors           # Still 3

# Merge multiple HLLs
PFADD hll:day1 "user1" "user2"
PFADD hll:day2 "user2" "user3"
PFMERGE hll:all hll:day1 hll:day2
PFCOUNT hll:all                # 3 (user2 counted once)
```

### 7.3 Use Cases

```bash
# Unique visitors per page
PFADD uv:home:2024-01-01 "visitor_uuid_1"
PFCOUNT uv:home:2024-01-01

# Weekly uniques (merge daily HLLs)
PFMERGE uv:home:week1 uv:home:2024-01-01 uv:home:2024-01-02 ... uv:home:2024-01-07
PFCOUNT uv:home:week1

# Unique search queries
PFADD queries:2024-01 "how to use redis" "redis tutorial"
PFCOUNT queries:2024-01

# Memory: 12 KB per HLL, regardless of count
# 10,000 pages * 365 days * 12 KB = ~42 GB
# vs. storing actual IDs: potentially terabytes
```

---

## 8. Bitmaps

### 8.1 What Bitmaps Are

Bitmaps are not a separate data type -- they are String values treated as bit arrays. Each bit can be set or cleared individually. This makes bitmaps extremely space-efficient for tracking boolean states across a large population.

### 8.2 Bitmap Operations

```bash
# Set bit at offset (0-based)
SETBIT user:logins:2024-01 123 1   # User 123 logged in today

# Get bit
GETBIT user:logins:2024-01 123     # 1 (logged in) or 0 (not)

# Count set bits
BITCOUNT user:logins:2024-01       # Total users who logged in

# Count set bits in byte range
BITCOUNT user:logins:2024-01 0 15  # Bits in first 16 bytes

# Bitwise operations between bitmaps
BITOP AND result:both day1 day2     # Users active both days
BITOP OR result:either day1 day2    # Users active either day
BITOP XOR result:exclusive day1 day2 # Users active one day but not both
BITOP NOT result:inactive day1      # Users NOT active on day1

# Find first bit set to 0 or 1
BITPOS user:logins:2024-01 1       # Position of first set bit
BITPOS user:logins:2024-01 0       # Position of first unset bit

# Bitfield (Redis 3.2+): treat string as array of integers
BITFIELD mybitfield SET u8 0 42    # Set unsigned 8-bit int at bit offset 0
BITFIELD mybitfield GET u8 0       # Get unsigned 8-bit int at bit offset 0
BITFIELD mybitfield INCRBY u8 0 1  # Increment by 1
```

### 8.3 Use Cases

```bash
# Daily active users (1 bit per user ID)
SETBIT dau:2024-01-01 12345 1      # User 12345 was active
BITCOUNT dau:2024-01-01             # Total active users
# 10 million users = 1.25 MB per day

# Feature flags per user
SETBIT feature:dark_mode 12345 1   # Enable dark mode for user 12345
GETBIT feature:dark_mode 12345     # Check if enabled

# Cohort analysis
BITOP AND retained:w1 dau:2024-01-01 dau:2024-01-08  # Week 1 retention
BITCOUNT retained:w1                # Users active both weeks
```

---

## 9. Streams

### 9.1 What Streams Are

Redis Streams are an append-only log data structure for event sourcing and message queuing. Each entry has an auto-generated time-based ID and consists of field-value pairs (similar to a Hash). Streams support consumer groups for load-balanced processing.

### 9.2 Stream Operations

```bash
# Add entry (auto-generated ID)
XADD mystream * field1 value1 field2 value2
# Returns: "1684934400000-0"

# Add with max length cap
XADD mystream MAXLEN ~ 1000 * field1 value1

# Read range
XRANGE mystream - + COUNT 10        # First 10 entries
XREVRANGE mystream + - COUNT 10      # Last 10

# Read new entries (tail follow)
XREAD COUNT 10 BLOCK 5000 STREAMS mystream $

# Consumer groups
XGROUP CREATE mystream group1 0 MKSTREAM
XREADGROUP GROUP group1 consumer1 COUNT 10 BLOCK 5000 STREAMS mystream >

# Acknowledge processed entries
XACK mystream group1 1684934400000-0

# Stream info
XLEN mystream
XINFO STREAM mystream
XINFO GROUPS mystream
XINFO CONSUMERS mystream group1

# Trim
XTRIM mystream MAXLEN ~ 10000
XTRIM mystream MINID ~ 1684900000000-0

# Delete specific entries
XDEL mystream 1684934400000-0

# Claim idle messages (consumer recovery)
XAUTOCLAIM mystream group1 consumer2 30000 0-0 COUNT 10
```

### 9.3 Use Cases

```bash
# Event log
XADD events * type "order_created" order_id "1001" amount "59.99"

# Activity feed
XADD feed:user:1 MAXLEN ~ 1000 * action "like" target "post:456"

# IoT sensor data
XADD sensors:temp * device "sensor-42" value "22.5" unit "celsius"

# Message queue with consumer groups (competing consumers)
XGROUP CREATE tasks processors 0 MKSTREAM
XADD tasks * type "email" to "user@example.com"
XREADGROUP GROUP processors worker-1 COUNT 10 BLOCK 5000 STREAMS tasks >
XACK tasks processors <message_id>
```

---

## 10. Geospatial Indexes

### 10.1 What Geospatial Is

Redis Geospatial is built on top of Sorted Sets. Longitude/latitude pairs are encoded into a geohash score. This enables efficient radius searches and distance calculations.

### 10.2 Geospatial Operations

```bash
# Add locations (longitude, latitude, member)
GEOADD locations -73.985428 40.748817 "Empire State Building"
GEOADD locations -73.968285 40.785091 "Central Park"

# Get coordinates
GEOPOS locations "Empire State Building"

# Distance between members
GEODIST locations "Empire State Building" "Central Park" km

# Geohash
GEOHASH locations "Empire State Building"

# Radius search (Redis 6.2+: GEOSEARCH replaces GEORADIUS)
GEOSEARCH locations FROMLONLAT -73.980 40.750 BYRADIUS 5 km ASC COUNT 10 WITHCOORD WITHDIST

# Search by bounding box
GEOSEARCH locations FROMLONLAT -73.980 40.750 BYBOX 10 10 km ASC

# Store search results
GEOSEARCHSTORE result locations FROMLONLAT -73.980 40.750 BYRADIUS 5 km ASC COUNT 10

# Remove member
ZREM locations "Empire State Building"  # Geo uses sorted set internally
```

### 10.3 Use Cases

```bash
# Nearby restaurants
GEOADD restaurants -73.985 40.748 "Pizza Palace"
GEOADD restaurants -73.975 40.752 "Sushi Bar"
GEOSEARCH restaurants FROMLONLAT -73.980 40.750 BYRADIUS 2 km ASC WITHCOORD WITHDIST

# Driver tracking (ride-sharing)
GEOADD drivers:active -73.985 40.748 "driver:42"
GEOSEARCH drivers:active FROMLONLAT -73.980 40.750 BYRADIUS 3 km ASC COUNT 5

# Store locator
GEOADD stores -73.985 40.748 "store:1"
GEOSEARCH stores FROMLONLAT -73.980 40.750 BYRADIUS 10 km ASC
```

---

## 11. Redis 7+ Data Type Enhancements

### 11.1 Listpack Everywhere

Redis 7 replaced ziplist with listpack as the compact encoding for small Hashes, Sets, Sorted Sets, and Streams. Listpack is more memory-efficient and avoids the cascading update problem of ziplist.

```bash
# Configuration thresholds (Redis 7+)
hash-max-listpack-entries 128    # Was hash-max-ziplist-entries
hash-max-listpack-value 64       # Was hash-max-ziplist-value
zset-max-listpack-entries 128
zset-max-listpack-value 64
set-max-listpack-entries 128
list-max-listpack-size -2        # -2 = 8KB per node

# Check encoding of a key
OBJECT ENCODING mykey
# Possible values: listpack, hashtable, skiplist, quicklist, intset, raw, int, embstr
```

### 11.2 OBJECT ENCODING Reference

| Type | Small Encoding | Large Encoding | Transition Trigger |
|---|---|---|---|
| String | int (integer) / embstr (<=44 bytes) | raw | Value > 44 bytes or not integer |
| Hash | listpack | hashtable | Entries > 128 or value > 64 bytes |
| Set | listpack / intset | hashtable | Entries > 128 or non-integer members |
| Sorted Set | listpack | skiplist | Entries > 128 or value > 64 bytes |
| List | listpack | quicklist | Always quicklist (chain of listpacks) |
| Stream | radix tree + listpack | Same | Always radix tree |

### 11.3 OBJECT Commands

```bash
# Encoding
OBJECT ENCODING mykey

# Reference count
OBJECT REFCOUNT mykey

# Idle time (seconds since last access)
OBJECT IDLETIME mykey

# Access frequency (requires LFU eviction policy)
OBJECT FREQ mykey

# Help
OBJECT HELP
```

### 11.4 Sharded Pub/Sub (Redis 7+)

Redis 7 added `SSUBSCRIBE` / `SPUBLISH` for cluster-efficient channel routing. See the Streaming/Pub/Sub document for details.

### 11.5 EXPIRE with Conditions (Redis 7+)

```bash
EXPIRE key 3600 NX   # Set only if no expiry exists
EXPIRE key 3600 XX   # Set only if expiry already exists
EXPIRE key 3600 GT   # Set only if new TTL > current TTL
EXPIRE key 3600 LT   # Set only if new TTL < current TTL
```

---

## 12. Internal Encoding and Memory

### 12.1 How Redis Stores Data Internally

Every Redis key-value pair consists of:
- **dictEntry**: 24 bytes (key pointer, value pointer, next pointer)
- **redisObject**: 16 bytes (type, encoding, LRU, refcount, data pointer)
- **SDS (Simple Dynamic String)** for the key: header + key bytes + null terminator

Total overhead per key: ~70-100 bytes, depending on key length.

### 12.2 Memory Optimization via Encoding

```bash
# Small Hash (listpack): ~10x less memory than equivalent separate keys
HSET user:1 name "John" email "john@test.com" age "30"
OBJECT ENCODING user:1
# "listpack" -- very compact

# vs. 3 separate keys:
SET user:1:name "John"
SET user:1:email "john@test.com"
SET user:1:age "30"
# 3 * ~90 bytes = ~270 bytes vs. ~100 bytes for the hash

# Integer set (intset): very compact for small sets of integers
SADD myset 1 2 3 4 5
OBJECT ENCODING myset
# "intset" -- 8 bytes per integer with no per-entry overhead
```

### 12.3 Checking Memory Usage

```bash
# Per-key memory
MEMORY USAGE mykey
MEMORY USAGE mykey SAMPLES 0    # Exact (slower for large values)

# Overall memory
INFO memory

# Big key detection
redis-cli --bigkeys

# Memory key analysis
redis-cli --memkeys
```

---

## 13. Key Management

### 13.1 Key Lifecycle

```bash
# Check existence
EXISTS key1 key2               # Returns count of existing keys

# Delete
DEL key1 key2                  # Synchronous delete
UNLINK key1 key2               # Async delete (Redis 4+, non-blocking)

# Type
TYPE mykey                     # Returns: string, list, set, zset, hash, stream

# Rename
RENAME oldkey newkey           # Atomic rename (overwrites newkey if exists)
RENAMENX oldkey newkey         # Rename only if newkey does not exist

# TTL management
EXPIRE key 3600                # Set TTL in seconds
PEXPIRE key 3600000            # Set TTL in milliseconds
EXPIREAT key 1700000000        # Expire at Unix timestamp
PERSIST key                    # Remove TTL

TTL key                        # Remaining seconds (-1 = no expiry, -2 = does not exist)
PTTL key                       # Remaining milliseconds

# Serialization
DUMP key                       # Serialize key to binary
RESTORE key 0 "<serialized>"   # Restore from binary

# Copy (Redis 6.2+)
COPY source destination        # Copy key
COPY source destination REPLACE # Overwrite destination if exists
COPY source destination DB 2   # Copy to different database
```

### 13.2 Key Scanning

```bash
# SCAN: cursor-based, non-blocking iteration
SCAN 0 MATCH "user:*" COUNT 100 TYPE string
# Returns: [new_cursor, [matching_keys]]
# When cursor returns 0, iteration is complete

# Type-specific scans
HSCAN myhash 0 MATCH "field*" COUNT 100
SSCAN myset 0 MATCH "member*" COUNT 100
ZSCAN myzset 0 MATCH "member*" COUNT 100

# Full iteration example:
# cursor=0
# while True:
#     cursor, keys = SCAN cursor MATCH "pattern" COUNT 100
#     process(keys)
#     if cursor == 0: break
```

### 13.3 Key Sorting

```bash
# SORT: sorts list, set, or sorted set elements
SORT mylist                    # Numeric sort (ascending)
SORT mylist DESC               # Descending
SORT mylist ALPHA              # Alphabetical sort
SORT mylist LIMIT 0 10         # First 10 results

# Sort by external key
SORT mylist BY weight:*        # Sort by referenced keys
SORT mylist GET object:*->name # Fetch external data

# Store sorted result
SORT mylist STORE sorted:mylist
```

---

## 14. Configuration Reference

```bash
# Listpack thresholds (controls compact encoding)
hash-max-listpack-entries 128
hash-max-listpack-value 64
zset-max-listpack-entries 128
zset-max-listpack-value 64
set-max-listpack-entries 128
list-max-listpack-size -2       # -2 = 8KB per node
list-compress-depth 0           # 0 = no compression

# Stream configuration
stream-node-max-bytes 4096
stream-node-max-entries 100

# String configuration
# No specific config; strings use embstr for <= 44 bytes

# HyperLogLog
# Fixed 12 KB per HLL; no configuration

# Lazy free (background deletion of large keys)
lazyfree-lazy-eviction yes
lazyfree-lazy-expire yes
lazyfree-lazy-server-del yes
lazyfree-lazy-user-del yes
```

---

## 15. Monitoring and Observability

### 15.1 Per-Key Analysis

```bash
# Memory per key
MEMORY USAGE key SAMPLES 0

# Encoding
OBJECT ENCODING key

# Idle time
OBJECT IDLETIME key

# Frequency (with LFU policy)
OBJECT FREQ key

# Type
TYPE key
```

### 15.2 Keyspace Overview

```bash
# Keyspace statistics
INFO keyspace
# db0:keys=10000,expires=5000,avg_ttl=1800000

# Total keys
DBSIZE

# Big key analysis
redis-cli --bigkeys

# Memory analysis
redis-cli --memkeys
```

### 15.3 Data Structure Metrics

```bash
# For each data structure, monitor:
# 1. Number of keys of each type (via SCAN + TYPE)
# 2. Average size per key (via MEMORY USAGE sampling)
# 3. Encoding distribution (listpack vs hashtable)
# 4. TTL distribution

# Example monitoring script
redis-cli --scan --pattern "*" | head -1000 | while read key; do
    type=$(redis-cli TYPE "$key" | awk '{print $1}')
    mem=$(redis-cli MEMORY USAGE "$key")
    enc=$(redis-cli OBJECT ENCODING "$key" 2>/dev/null)
    echo "$key|$type|$mem|$enc"
done
```

---

## 16. Troubleshooting

### 16.1 Wrong Type Error

**Symptoms**: `WRONGTYPE Operation against a key holding the wrong kind of value`

**Cause**: Calling a command on a key of incompatible type (e.g., `LPUSH` on a String key).

**Resolution**: Check the key's type with `TYPE key` before operating. Delete the key if the type conflict is unintentional.

### 16.2 Key Not Found but Should Exist

**Symptoms**: `GET key` returns nil but the key was recently set.

**Causes**: TTL expired, evicted by maxmemory policy, deleted by another client, wrong database (use `SELECT` to change).

**Resolution**: Check `TTL key`, `INFO memory` for evictions, `MONITOR` briefly to trace.

### 16.3 Hash Switched to hashtable Encoding

**Symptoms**: Memory usage spikes after adding a field to a Hash.

**Cause**: Exceeding `hash-max-listpack-entries` or `hash-max-listpack-value` thresholds.

**Resolution**: Increase thresholds if the Hash will remain small. Or accept the encoding change for large Hashes (hashtable is faster for > 128 entries).

### 16.4 SORT Command Slow or OOM

**Symptoms**: `SORT` on a large set takes seconds or causes OOM.

**Cause**: `SORT` is O(N+M*log(M)) and creates a temporary copy.

**Resolution**: Add `LIMIT`, reduce result size, or use a Sorted Set instead (pre-sorted).

### 16.5 SMEMBERS on Large Set

**Symptoms**: `SMEMBERS` blocks Redis for seconds on a set with millions of members.

**Resolution**: Use `SSCAN` for non-blocking iteration. Avoid `SMEMBERS` on sets > 10000 members.

### 16.6 List Grows Unbounded

**Symptoms**: Memory keeps increasing from a List that is never trimmed.

**Resolution**: Use `LTRIM` after every `LPUSH` to cap the list, or use `XADD MAXLEN ~` with Streams.

### 16.7 Sorted Set ZRANGEBYSCORE Returns Nothing

**Symptoms**: No results despite known members in the score range.

**Cause**: Score format mismatch (string vs. number), or wrong range boundary syntax.

**Resolution**: Verify scores with `ZSCORE key member`. Use `(` prefix for exclusive boundaries: `ZRANGEBYSCORE key (100 200`.

### 16.8 Stream XADD Failing with MAXLEN

**Symptoms**: `XADD` returns error or unexpected behavior.

**Cause**: Using `NOMKSTREAM` flag and the stream does not exist yet.

**Resolution**: Create the stream first or remove `NOMKSTREAM`.

### 16.9 Bitmap Memory Spike

**Symptoms**: Bitmap consumes much more memory than expected.

**Cause**: Setting a bit at a very high offset (e.g., `SETBIT key 100000000 1`) allocates memory for the entire range.

**Resolution**: Use offset values within a reasonable range. For sparse bitmaps, consider HyperLogLog or Sets instead.

### 16.10 OBJECT FREQ Returns 0

**Symptoms**: `OBJECT FREQ` always returns 0.

**Cause**: LFU eviction policy is not enabled. Frequency is only tracked with `allkeys-lfu` or `volatile-lfu`.

**Resolution**: Set `maxmemory-policy allkeys-lfu` or `volatile-lfu`.

---

## 17. FAQ

### Q1: When should I use a Hash vs. individual String keys?

Use Hashes when you have multiple fields for the same entity (user profile, product, config). Hashes use ~10x less memory than equivalent individual keys when they stay in listpack encoding (< 128 entries with small values).

### Q2: What is the maximum number of elements in a List/Set/ZSet?

Over 4 billion (2^32 - 1). The practical limit is available memory.

### Q3: When should I use HyperLogLog instead of a Set?

When you only need the count of unique elements, not the elements themselves, and the dataset is large. HyperLogLog uses 12 KB regardless of cardinality; a Set storing 10 million UUIDs uses ~500 MB.

### Q4: Are Redis Streams a replacement for Kafka?

For moderate throughput (tens of thousands of messages per second) and simple consumer group patterns, Streams work well. For millions of messages per second, multi-partition ordering, and compacted topics, Kafka is more appropriate.

### Q5: How do I choose between List and Stream for a queue?

Use Streams for: consumer groups, acknowledgment, replay, message metadata. Use Lists for: simple FIFO/LIFO, blocking pop, when you do not need consumer tracking.

### Q6: Can I use SORT on a Hash?

No. `SORT` works on Lists, Sets, and Sorted Sets. For Hash field sorting, fetch all fields and sort in the application, or maintain a Sorted Set as a secondary index.

### Q7: What is the overhead of a Sorted Set vs. a Set?

Sorted Sets store an additional 8-byte float score per member and use a skip list + hash table internally. For small sizes (listpack encoding), the difference is minimal. For large sizes, Sorted Sets use ~2x the memory of Sets.

### Q8: How do GEOSEARCH results work internally?

GEOSEARCH is built on Sorted Sets. Coordinates are encoded as a 52-bit geohash stored as the member's score. The search uses the geohash to find nearby members efficiently.

### Q9: Can I iterate over all elements of a data structure without blocking?

Yes. Use `SCAN` for the keyspace, `HSCAN` for Hashes, `SSCAN` for Sets, and `ZSCAN` for Sorted Sets. These are cursor-based and return partial results per call.

### Q10: What happens when listpack encoding converts to hashtable?

The conversion is one-way and automatic. Once a Hash or Set exceeds the listpack threshold, it converts to the full data structure (hashtable). It does not convert back even if you delete fields. To revert, delete and recreate the key.

### Q11: Is there a way to store nested data structures (Hash of Hashes)?

No. Redis data structures are flat. To model nested structures, use key naming conventions (`user:1:address:city`), serialize nested data as JSON in a String, or use the RedisJSON module.

### Q12: What is the difference between RPOPLPUSH and LMOVE?

`LMOVE` (Redis 6.2+) is the modern replacement for `RPOPLPUSH`. It supports all four directional combinations (LEFT/RIGHT for source and destination), while `RPOPLPUSH` only moves from the right of the source to the left of the destination.

---

*Questo documento fa parte del modulo 06 "NoSQL Redis" della Data Encyclopedia.*
