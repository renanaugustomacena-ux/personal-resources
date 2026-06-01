# Redis: Lua Scripting

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
1. Introduzione a Lua in Redis
2. Comandi EVAL/EVALSHA
3. Redis Functions (Redis 7+)
4. Redis Lua API
5. Pattern Comuni
6. Error Handling
7. Performance Considerations
8. Atomicity and Concurrency
9. Debug e Development
10. Best Practices
11. Configuration Reference
12. Monitoring and Observability
13. Operational Procedures
14. Real-World Patterns
15. Troubleshooting
16. FAQ

---

## 1. Introduzione a Lua in Redis

Redis integra Lua 5.1 come linguaggio per script lato server. Gli script Lua permettono di eseguire operazioni atomiche complesse sul server, riducendo latenza di rete e round-trip.

### 1.1 Why Lua Scripting

Lua scripts provide three key guarantees:

1. **Atomicity**: The entire script executes as a single atomic operation. No other command can run between statements.
2. **Reduced round trips**: Complex multi-step operations that would require multiple client-server exchanges execute in a single call.
3. **Server-side logic**: Conditional logic, loops, and data transformation run on the server, avoiding data transfer.

```bash
# Esempio base - esegui script inline
EVAL "return 'Hello World'" 0

# Con argomenti
EVAL "return redis.call('GET', KEYS[1])" 1 mykey

# With multiple keys and arguments
EVAL "return redis.call('SET', KEYS[1], ARGV[1])" 1 mykey myvalue
```

### 1.2 Lua 5.1 Language Basics

Redis embeds Lua 5.1 (not 5.3/5.4). Key differences from modern Lua:

```lua
-- No integers in Lua 5.1, only doubles
-- No bitwise operators (use redis.call for BITOP)
-- No goto statement
-- String patterns, not full regex

-- String operations
local s = "hello"
local len = #s                    -- 5
local upper = string.upper(s)     -- "HELLO"
local sub = string.sub(s, 1, 3)   -- "hel"

-- Table operations (arrays and maps)
local arr = {"a", "b", "c"}
local len = #arr                  -- 3
table.insert(arr, "d")

local map = {key1 = "val1", key2 = "val2"}
local v = map.key1                -- "val1"

-- Loops
for i = 1, 10 do
    -- do something
end

for i, v in ipairs(arr) do
    -- i = index, v = value
end

for k, v in pairs(map) do
    -- k = key, v = value
end

-- Type conversion
local n = tonumber("42")         -- 42
local s = tostring(42)           -- "42"
```

---

## 2. Comandi EVAL/EVALSHA

### 2.1 EVAL - Esecuzione Inline

```bash
# EVAL syntax
EVAL script numkeys [key [key ...]] [arg [arg ...]]

# numkeys: number of KEYS[] arguments (everything after is ARGV[])

# Esempi pratici
EVAL "return redis.call('SET', KEYS[1], ARGV[1])" 1 mykey myvalue
EVAL "return redis.call('GET', KEYS[1])" 1 mykey

# Multiple keys
EVAL "return {redis.call('GET', KEYS[1]), redis.call('GET', KEYS[2])}" 2 key1 key2

# With computation
EVAL "return tonumber(ARGV[1]) + tonumber(ARGV[2])" 0 10 20
-- Returns: 30
```

### 2.2 EVALSHA - Cached Script Execution

Every script sent via `EVAL` is cached on the server by its SHA1 hash. `EVALSHA` executes a cached script without resending the source code, saving bandwidth.

```bash
# Step 1: Load script and get SHA
SCRIPT LOAD "return redis.call('GET', KEYS[1])"
# Returns: "e0e1f9fabfc9d4800c877a703b823ac0578ff831"

# Step 2: Execute via SHA (faster -- no script body in command)
EVALSHA "e0e1f9fabfc9d4800c877a703b823ac0578ff831" 1 mykey

# In production, always try EVALSHA first, fall back to EVAL on NOSCRIPT error
```

### 2.3 SCRIPT Management Commands

```bash
# Check if script is cached
SCRIPT EXISTS "e0e1f9fabfc9d4800c877a703b823ac0578ff831"
# Returns: 1 (cached) or 0 (not cached)

# Check multiple scripts
SCRIPT EXISTS "sha1" "sha2" "sha3"

# Flush all cached scripts
SCRIPT FLUSH

# Flush with sync mode (Redis 6.2+)
SCRIPT FLUSH ASYNC
SCRIPT FLUSH SYNC

# Kill a currently running script
SCRIPT KILL
# Only works if the script has not yet called a write command

# Debug mode (not recommended in production)
SCRIPT DEBUG YES     # Sync debug mode (blocks)
SCRIPT DEBUG NO      # Disable debug
```

### 2.4 Client-Side EVALSHA Pattern

```python
import redis
import hashlib

r = redis.Redis()

SCRIPT = """
local current = redis.call('GET', KEYS[1])
if not current then
    redis.call('SET', KEYS[1], ARGV[1])
    return 1
end
return 0
"""

# Pre-compute SHA
sha = hashlib.sha1(SCRIPT.encode()).hexdigest()

def run_script(key, value):
    try:
        return r.evalsha(sha, 1, key, value)
    except redis.exceptions.NoScriptError:
        # Script not cached on this server, fall back to EVAL
        return r.eval(SCRIPT, 1, key, value)

# Even simpler with redis-py's register_script
set_if_missing = r.register_script(SCRIPT)
result = set_if_missing(keys=['mykey'], args=['myvalue'])
```

---

## 3. Redis Functions (Redis 7+)

### 3.1 Why Functions Replace EVAL

Redis 7.0 introduced Redis Functions as the preferred alternative to `EVAL`/`EVALSHA`. Functions address several limitations of the eval model:

| Feature | EVAL/EVALSHA | Redis Functions |
|---|---|---|
| Persistence | Lost on restart (cache only) | Persisted in RDB/AOF |
| Replication | Script must be on all nodes | Auto-replicated |
| Naming | SHA1 hash (opaque) | Named functions |
| Libraries | None (standalone scripts) | Grouped in libraries |
| Management | SCRIPT LOAD/FLUSH | FUNCTION LOAD/LIST/DELETE |
| Cluster | Manual distribution | Automatic |

### 3.2 Defining a Function Library

```lua
-- mylib.lua
-- A function library is a Lua script that registers one or more functions

#!lua name=mylib

-- Helper (not a registered function, just internal)
local function validate_key(key)
    if not key or key == '' then
        return redis.error_reply('ERR empty key')
    end
    return true
end

-- Register function: set_if_greater
-- Only sets the value if the new value is greater than the current one
redis.register_function('set_if_greater', function(keys, args)
    validate_key(keys[1])
    local current = redis.call('GET', keys[1])
    local new_val = tonumber(args[1])

    if not current or tonumber(current) < new_val then
        redis.call('SET', keys[1], new_val)
        return 1
    end
    return 0
end)

-- Register function: atomic_transfer
-- Atomically transfer amount from one key to another
redis.register_function('atomic_transfer', function(keys, args)
    local from = keys[1]
    local to = keys[2]
    local amount = tonumber(args[1])

    local from_balance = tonumber(redis.call('GET', from) or 0)
    if from_balance < amount then
        return redis.error_reply('ERR insufficient balance')
    end

    redis.call('DECRBY', from, amount)
    redis.call('INCRBY', to, amount)
    return 'OK'
end)
```

### 3.3 Loading and Managing Functions

```bash
# Load a function library from a file
cat mylib.lua | redis-cli -x FUNCTION LOAD REPLACE

# Load with REPLACE flag (overwrites existing library with same name)
FUNCTION LOAD REPLACE "#!lua name=mylib\nredis.register_function('myfunc', function(keys, args) return 'ok' end)"

# List all loaded libraries
FUNCTION LIST

# List functions in a specific library
FUNCTION LIST LIBRARYNAME mylib

# Delete a library
FUNCTION DELETE mylib

# Dump all functions (for backup)
FUNCTION DUMP
# Returns a serialized payload

# Restore functions from dump
FUNCTION RESTORE <serialized_payload>
FUNCTION RESTORE <serialized_payload> REPLACE

# Flush all functions
FUNCTION FLUSH
FUNCTION FLUSH ASYNC
```

### 3.4 Calling Functions

```bash
# FCALL: call a function (equivalent to EVAL for functions)
FCALL set_if_greater 1 mykey 42

# FCALL_RO: call a read-only function (can execute on replicas)
FCALL_RO my_readonly_func 1 mykey

# Python client
result = r.fcall('set_if_greater', 1, 'mykey', '42')

# Node.js
const result = await redis.fcall('set_if_greater', 1, 'mykey', '42');
```

### 3.5 Read-Only Functions

```lua
#!lua name=readonly_lib

-- Flag function as read-only with flags
redis.register_function{
    function_name = 'safe_get',
    callback = function(keys, args)
        return redis.call('GET', keys[1])
    end,
    flags = {'no-writes'}  -- Allows execution on replicas with FCALL_RO
}
```

---

## 4. Redis Lua API

### 4.1 redis.call vs redis.pcall

```lua
-- redis.call: propagates errors (script aborts on error)
local value = redis.call('GET', 'mykey')
-- If GET fails (wrong type, etc.), the entire script fails

-- redis.pcall: catches errors (returns error as table)
local result = redis.pcall('GET', 'mykey')
if type(result) == 'table' and result.err then
    -- Handle error
    return redis.error_reply('Custom error: ' .. result.err)
end
return result
```

### 4.2 Return Types and RESP Mapping

```lua
-- Lua → Redis type conversion:

-- String → Bulk String
return 'hello'                    -- RESP: $5\r\nhello\r\n

-- Number → Integer
return 42                         -- RESP: :42\r\n

-- Table (array) → Multi Bulk
return { 'a', 'b', 'c' }          -- RESP: *3\r\n$1\r\na\r\n...

-- Table (map) → Map (Redis 7+ RESP3 only)
return { key = 'value' }          -- RESP3 map type

-- nil → Null
return nil                        -- RESP: $-1\r\n

-- Boolean → Integer
return true                       -- RESP: :1\r\n
return false                      -- RESP: nil (not 0)

-- IMPORTANT: false and nil are returned as Nil in RESP2
-- In a table, nil terminates the array (Lua behavior)
return {1, 2, nil, 3}             -- Only returns {1, 2} !
```

### 4.3 KEYS and ARGV

```lua
-- KEYS: keys the script operates on (for cluster routing)
-- ARGV: additional parameters (not used for routing)

-- Rule: ALL Redis keys accessed by the script MUST be in KEYS
-- This enables Redis Cluster to route the script to the correct node

-- Correct:
EVAL "return redis.call('GET', KEYS[1])" 1 mykey

-- WRONG (breaks cluster routing):
EVAL "return redis.call('GET', 'mykey')" 0

-- Multiple keys and args:
EVAL "redis.call('SET', KEYS[1], ARGV[1]); redis.call('SET', KEYS[2], ARGV[2]); return 'OK'" 2 key1 key2 val1 val2
```

### 4.4 Status Reply and Error Reply

```lua
-- Return a status reply (simple string)
return redis.status_reply('OK')

-- Return an error reply
return redis.error_reply('ERR custom error message')

-- Return structured error (Redis 7+)
return redis.error_reply('CUSTOM_CODE custom message')
```

### 4.5 redis.log

```lua
-- Log from within a script (appears in Redis server log)
redis.log(redis.LOG_WARNING, 'Something unexpected happened')
redis.log(redis.LOG_NOTICE, 'Processing key: ' .. KEYS[1])
redis.log(redis.LOG_DEBUG, 'Debug info')

-- Log levels: LOG_DEBUG, LOG_VERBOSE, LOG_NOTICE, LOG_WARNING
-- Controlled by the server's loglevel setting
```

### 4.6 cjson Library

```lua
-- Redis includes cjson for JSON encoding/decoding
local data = cjson.decode(redis.call('GET', KEYS[1]))
data.updated_at = ARGV[1]
redis.call('SET', KEYS[1], cjson.encode(data))
return cjson.encode(data)

-- Handle missing/nil values
local raw = redis.call('GET', KEYS[1])
if raw then
    local data = cjson.decode(raw)
    return data.field_name
end
return nil
```

### 4.7 cmsgpack Library

```lua
-- MessagePack encoding/decoding (more compact than JSON)
local packed = cmsgpack.pack({name = 'John', age = 30})
redis.call('SET', KEYS[1], packed)

local data = cmsgpack.unpack(redis.call('GET', KEYS[1]))
return data.name
```

---

## 5. Pattern Comuni

### 5.1 Distributed Lock (Redlock Acquire)

```lua
-- acquire_lock.lua
-- Atomic SET NX PX (set-if-not-exists with millisecond expiry)
local lock_key = KEYS[1]
local lock_value = ARGV[1]
local expire_ms = tonumber(ARGV[2])

if redis.call('SET', lock_key, lock_value, 'PX', expire_ms, 'NX') then
    return 1
else
    return 0
end
```

```lua
-- release_lock.lua
-- Only release if the caller owns the lock (compare-and-delete)
local lock_key = KEYS[1]
local lock_value = ARGV[1]

if redis.call('GET', lock_key) == lock_value then
    redis.call('DEL', lock_key)
    return 1
end
return 0
```

```bash
# Usage
EVALSHA <acquire_sha> 1 lock:resource abc123 10000
# ... do work ...
EVALSHA <release_sha> 1 lock:resource abc123
```

### 5.2 Rate Limiting -- Sliding Window

```lua
-- rate_limit_sliding.lua
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local now = tonumber(ARGV[3])

-- Remove expired entries
redis.call('ZREMRANGEBYSCORE', key, 0, now - window)

-- Count current requests
local count = redis.call('ZCARD', key)

if count >= limit then
    return 0  -- Rate limited
end

-- Add new request with unique member
redis.call('ZADD', key, now, now .. '-' .. math.random(100000))
redis.call('PEXPIRE', key, window)

return 1  -- Allowed
```

### 5.3 Conditional Counter with Threshold

```lua
-- Increment only if under threshold, set TTL on first increment
local key = KEYS[1]
local max = tonumber(ARGV[1])
local ttl = tonumber(ARGV[2])

local current = redis.call('GET', key)
if not current then
    current = 0
else
    current = tonumber(current)
end

if current >= max then
    return -1  -- Threshold exceeded
end

local new_val = redis.call('INCR', key)
if new_val == 1 then
    redis.call('EXPIRE', key, ttl)
end

return new_val
```

### 5.4 Compare-and-Swap (CAS)

```lua
-- CAS: update only if current value matches expected
local key = KEYS[1]
local expected = ARGV[1]
local new_value = ARGV[2]

local current = redis.call('GET', key)
if current == expected then
    redis.call('SET', key, new_value)
    return 1  -- Swapped
end
return 0  -- Value changed since read
```

### 5.5 Batch Multi-Key Operations

```lua
-- Get multiple keys atomically
local result = {}
for i = 1, #KEYS do
    table.insert(result, redis.call('GET', KEYS[i]))
end
return result

-- Execute: EVAL script 3 key1 key2 key3
```

### 5.6 Leaderboard Update with Rank Return

```lua
-- Update score and return new rank atomically
local board = KEYS[1]
local player = ARGV[1]
local score = tonumber(ARGV[2])

redis.call('ZADD', board, score, player)
local rank = redis.call('ZREVRANK', board, player)
local total = redis.call('ZCARD', board)

return {rank, total, score}
-- Returns: [rank (0-based), total players, score]
```

---

## 6. Error Handling

### 6.1 Gestione Errori con pcall

```lua
local function safe_call(cmd, ...)
    local ok, result = pcall(redis.call, cmd, ...)
    if not ok then
        return nil, result
    end
    return result
end

local value, err = safe_call('GET', 'nonexistent')
if err then
    return redis.error_reply('Error: ' .. tostring(err))
end
return value
```

### 6.2 Input Validation

```lua
-- Validate number of keys
if #KEYS ~= 2 then
    return redis.error_reply('ERR expected exactly 2 keys')
end

-- Validate argument types
local amount = tonumber(ARGV[1])
if not amount then
    return redis.error_reply('ERR ARGV[1] must be a number')
end

if amount <= 0 then
    return redis.error_reply('ERR amount must be positive')
end

-- Validate key type
local key_type = redis.call('TYPE', KEYS[1])
if key_type.ok ~= 'string' and key_type.ok ~= 'none' then
    return redis.error_reply('ERR key must be a string type, got ' .. key_type.ok)
end
```

### 6.3 Error Propagation Strategy

```lua
-- Strategy: fail fast with clear messages
-- Do NOT silently swallow errors

-- BAD:
local result = redis.pcall('GET', KEYS[1])
-- ignores result.err

-- GOOD:
local result = redis.pcall('GET', KEYS[1])
if type(result) == 'table' and result.err then
    redis.log(redis.LOG_WARNING, 'Script error: ' .. result.err)
    return redis.error_reply('SCRIPT_ERR ' .. result.err)
end
```

---

## 7. Performance Considerations

### 7.1 Atomicity Implications

```lua
-- The entire script blocks Redis during execution
-- No other client command can interleave
-- This is the KEY benefit: atomic multi-step operations

-- Example: atomic check-and-modify
local current = redis.call('GET', 'counter')
local new_val = (tonumber(current) or 0) + 1
redis.call('SET', 'counter', new_val)
return new_val
-- No race condition possible -- another INCR cannot slip in
```

### 7.2 Execution Time Limits

```bash
# Default script timeout: 5 seconds
# Configurable:
lua-time-limit 5000  # milliseconds

# After timeout:
# - Redis starts accepting SCRIPT KILL commands
# - If script has NOT performed writes: SCRIPT KILL terminates it
# - If script HAS performed writes: only SHUTDOWN NOSAVE can stop it
#   (to prevent partial state)
```

### 7.3 Script Complexity Guidelines

| Complexity | Recommendation |
|---|---|
| < 100 Redis calls | Ideal for Lua scripts |
| 100-1000 calls | Acceptable if unavoidable |
| > 1000 calls | Consider splitting or using different architecture |
| Heavy computation | Offload to application code |
| External I/O | Not possible (no network/file access in Lua) |

### 7.4 EVALSHA vs EVAL Performance

```bash
# EVAL sends the entire script body every time
# EVALSHA sends only the 40-byte SHA1 hash

# For a 1KB script called 10000 times:
# EVAL:    10000 * 1KB = ~10MB of network traffic
# EVALSHA: 10000 * 40B = ~400KB of network traffic

# Always use EVALSHA in production, with EVAL as fallback
```

### 7.5 Script Caching

```bash
# Scripts are cached in a dictionary keyed by SHA1
# Cache survives until:
# - SCRIPT FLUSH is called
# - Server restarts
# - (In cluster) node restarts

# Check if a script is cached
SCRIPT EXISTS "sha1hash"

# Pre-load scripts at application startup
SCRIPT LOAD "return redis.call('GET', KEYS[1])"
```

---

## 8. Atomicity and Concurrency

### 8.1 Script Isolation

While a script runs, no other command from any client can execute. This provides serializable isolation:

```lua
-- This is atomic: no one can modify 'balance' between GET and SET
local balance = tonumber(redis.call('GET', KEYS[1]))
if balance >= tonumber(ARGV[1]) then
    redis.call('DECRBY', KEYS[1], ARGV[1])
    redis.call('INCRBY', KEYS[2], ARGV[1])
    return 1
end
return 0
```

### 8.2 Blocking Impact

Because scripts block all clients, long-running scripts effectively cause downtime. This is the fundamental trade-off: atomicity vs. latency.

```bash
# Monitor blocked clients during script execution
CLIENT LIST
# Look for flags=b (blocked)

# If scripts routinely take > 100ms, redesign:
# 1. Reduce the number of Redis calls in the script
# 2. Pre-compute values in the application
# 3. Use pipelines instead (if atomicity is not required)
```

### 8.3 Replication of Scripts

Scripts are replicated to replicas in one of two ways:

```bash
# Script effects replication (Redis 7+ default for Functions)
# Only the resulting commands are replicated, not the script itself
# This is deterministic and safe

# Script replication (legacy)
# The entire EVAL command is replicated and re-executed on replicas
# This requires scripts to be deterministic (no random(), no TIME)

# Force effects replication in EVAL scripts:
redis.replicate_commands()  -- deprecated in Redis 7+, effects replication is default
```

---

## 9. Debug e Development

### 9.1 Redis Lua Debugger

```bash
# Enable sync debug mode (BLOCKS the server)
redis-cli --ldb --eval /path/to/script.lua key1 key2 , arg1 arg2

# Debugger commands:
# s or step    -- execute next line
# n or next    -- step over function calls
# c or continue -- continue execution
# b <line>     -- set breakpoint at line
# p <var>      -- print variable
# w            -- print call stack
# e <expr>     -- evaluate expression
# a            -- abort script

# Note: the comma separates KEYS from ARGV
# redis-cli --ldb --eval script.lua key1 key2 , arg1 arg2
```

### 9.2 Testing Scripts Locally

```bash
# Quick test with redis-cli
redis-cli EVAL "local a = tonumber(ARGV[1]); local b = tonumber(ARGV[2]); return a + b" 0 10 20
# Returns: 30

# Test with keys
redis-cli SET testkey "hello"
redis-cli EVAL "return redis.call('GET', KEYS[1])" 1 testkey
# Returns: "hello"

# Test error handling
redis-cli EVAL "return redis.error_reply('ERR test error')" 0
# Returns: (error) ERR test error
```

### 9.3 Development Workflow

```python
# Development pattern: load scripts from files

import os

class RedisScripts:
    def __init__(self, redis_client, script_dir):
        self.r = redis_client
        self.scripts = {}
        self._load_scripts(script_dir)

    def _load_scripts(self, script_dir):
        for filename in os.listdir(script_dir):
            if filename.endswith('.lua'):
                name = filename[:-4]  # Remove .lua
                with open(os.path.join(script_dir, filename)) as f:
                    self.scripts[name] = self.r.register_script(f.read())

    def run(self, name, keys=None, args=None):
        return self.scripts[name](keys=keys or [], args=args or [])

# Usage
scripts = RedisScripts(r, './lua_scripts/')
result = scripts.run('rate_limit', keys=['ratelimit:user1'], args=[100, 60000, time.time()])
```

---

## 10. Best Practices

### 10.1 Key Rules

```lua
-- 1. ALWAYS pass Redis keys in KEYS, never hardcode
-- CORRECT:
EVAL "return redis.call('GET', KEYS[1])" 1 mykey

-- WRONG (breaks cluster routing):
EVAL "return redis.call('GET', 'mykey')" 0

-- 2. Keep scripts short and focused
-- One script = one atomic operation

-- 3. Validate inputs at the start of the script

-- 4. Use EVALSHA in production, EVAL as fallback

-- 5. Use redis.pcall for non-critical operations within a script

-- 6. Never use TIME, random(), or other non-deterministic functions
--    in scripts that must replicate correctly (pre-Redis 7)
--    In Redis 7+ with effects replication, this restriction is relaxed
```

### 10.2 Script Organization

```
lua_scripts/
├── locks/
│   ├── acquire.lua
│   └── release.lua
├── rate_limiting/
│   ├── token_bucket.lua
│   └── sliding_window.lua
├── cache/
│   ├── get_or_set.lua
│   └── invalidate_pattern.lua
└── counters/
    ├── increment_bounded.lua
    └── atomic_transfer.lua
```

### 10.3 Version Compatibility

```lua
-- Redis 5.x: tables returned as arrays only
-- Redis 6.x: redis.replicate_commands() added
-- Redis 7.x: Functions (FUNCTION LOAD/FCALL), effects replication by default,
--            map return type support, RESP3 support

-- Write compatible scripts:
-- Return arrays (not maps) for Redis 5/6 compatibility
return { 'a', 'b', 'c' }

-- Redis 7+ only:
-- return { a = 'x', b = 'y' }
```

---

## 11. Configuration Reference

```bash
# Maximum script execution time (milliseconds)
lua-time-limit 5000

# Enable/disable read-only scripts on replicas
# (Relevant for EVALSHA_RO and FCALL_RO)
replica-read-only yes

# Script cache size -- not directly configurable
# Cached scripts use memory tracked under used_memory_scripts

# Redis Functions configuration
# Functions are persisted in RDB/AOF by default (no config needed)

# Busy script protection
# After lua-time-limit, Redis accepts only:
# SCRIPT KILL (if no writes performed)
# SHUTDOWN NOSAVE (if writes performed)
```

---

## 12. Monitoring and Observability

### 12.1 Script Metrics

```bash
# Check cached script memory
INFO memory
# used_memory_scripts: memory used by cached EVAL scripts
# used_memory_scripts_eval: memory by EVAL cache specifically
# number_of_cached_scripts: count of cached scripts

# Command statistics for EVAL/EVALSHA
INFO commandstats
# cmdstat_eval:calls=1000,usec=50000,usec_per_call=50.00
# cmdstat_evalsha:calls=5000,usec=100000,usec_per_call=20.00

# Function statistics
FUNCTION STATS
# Returns running script info (if any) and engine stats
```

### 12.2 Slow Script Detection

```bash
# Scripts that exceed slowlog threshold appear in SLOWLOG
SLOWLOG GET 10

# Example entry for a slow script:
# 1) (integer) 1
# 2) (integer) 1684934400
# 3) (integer) 15000  <-- 15ms execution
# 4) 1) "EVALSHA"
#    2) "abc123sha..."
#    3) "1"
#    4) "mykey"

# Enable latency monitoring
CONFIG SET latency-monitor-threshold 5
LATENCY LATEST
```

### 12.3 Script Performance Profiling

```python
# Client-side timing wrapper
import time

def profiled_eval(script_obj, keys, args, name='unnamed'):
    start = time.monotonic()
    result = script_obj(keys=keys, args=args)
    elapsed = (time.monotonic() - start) * 1000
    if elapsed > 10:  # Log if > 10ms
        logger.warning(f"Slow script '{name}': {elapsed:.2f}ms")
    return result
```

---

## 13. Operational Procedures

### 13.1 Deploying New Scripts

```bash
# Option 1: SCRIPT LOAD at application startup (EVAL/EVALSHA)
redis-cli SCRIPT LOAD "$(cat scripts/rate_limit.lua)"

# Option 2: FUNCTION LOAD for Redis 7+ (preferred)
cat scripts/mylib.lua | redis-cli -x FUNCTION LOAD REPLACE

# Verify deployment
FUNCTION LIST LIBRARYNAME mylib
```

### 13.2 Script Migration (EVAL to Functions)

```bash
# 1. Convert EVAL scripts to Function libraries
# Before (EVAL):
EVAL "return redis.call('GET', KEYS[1])" 1 mykey

# After (Function):
# mylib.lua:
# #!lua name=mylib
# redis.register_function('my_get', function(keys, args)
#     return redis.call('GET', keys[1])
# end)

# 2. Load the library
cat mylib.lua | redis-cli -x FUNCTION LOAD REPLACE

# 3. Update application code
# Before: r.eval(script, 1, 'mykey')
# After:  r.fcall('my_get', 1, 'mykey')
```

### 13.3 Script Rollback

```bash
# For Functions: reload the previous library version
cat mylib_v1.lua | redis-cli -x FUNCTION LOAD REPLACE

# For EVAL: the application code controls which script SHA is used
# Roll back the application deployment
```

### 13.4 Killing a Stuck Script

```bash
# If a script exceeds lua-time-limit:
# Check if script is running
SCRIPT EXISTS <sha>

# Kill it (only if it has not performed writes)
SCRIPT KILL

# If it has performed writes, only SHUTDOWN NOSAVE can stop it
# This is a last resort -- it shuts down Redis without saving
SHUTDOWN NOSAVE
```

---

## 14. Real-World Patterns

### 14.1 Inventory Reservation

```lua
-- Reserve inventory atomically (prevent overselling)
local product_key = KEYS[1]
local reserved_key = KEYS[2]
local quantity = tonumber(ARGV[1])
local reservation_id = ARGV[2]
local ttl = tonumber(ARGV[3])

local available = tonumber(redis.call('GET', product_key) or 0)
if available < quantity then
    return redis.error_reply('ERR insufficient inventory')
end

redis.call('DECRBY', product_key, quantity)
redis.call('HSET', reserved_key, reservation_id, quantity)
redis.call('EXPIRE', reserved_key, ttl)

return available - quantity
```

### 14.2 Deduplication with TTL

```lua
-- Process message only if not seen in the last N seconds
local dedup_key = KEYS[1]
local message_id = ARGV[1]
local ttl = tonumber(ARGV[2])

local exists = redis.call('SISMEMBER', dedup_key, message_id)
if exists == 1 then
    return 0  -- Duplicate
end

redis.call('SADD', dedup_key, message_id)
redis.call('EXPIRE', dedup_key, ttl)
return 1  -- New message
```

### 14.3 Moving Average Calculator

```lua
-- Maintain a moving average over the last N values
local key = KEYS[1]
local value = tonumber(ARGV[1])
local window = tonumber(ARGV[2])

redis.call('RPUSH', key, value)
local len = redis.call('LLEN', key)
if len > window then
    redis.call('LTRIM', key, len - window, -1)
end

local values = redis.call('LRANGE', key, 0, -1)
local sum = 0
for _, v in ipairs(values) do
    sum = sum + tonumber(v)
end

return tostring(sum / #values)
```

### 14.4 Feature Flag Check

```lua
-- Check feature flag with percentage rollout
local flag_key = KEYS[1]
local user_id = ARGV[1]

local flag = redis.call('HGETALL', flag_key)
if #flag == 0 then
    return 0  -- Flag not found, feature disabled
end

local flag_map = {}
for i = 1, #flag, 2 do
    flag_map[flag[i]] = flag[i + 1]
end

if flag_map['enabled'] ~= '1' then
    return 0
end

-- Percentage rollout
local pct = tonumber(flag_map['percentage'] or '100')
local hash = tonumber(redis.call('CRC16', user_id) or '0')  -- Not available, use manual hash
-- Alternative: use string hash
local hash_val = 0
for c in user_id:gmatch('.') do
    hash_val = (hash_val * 31 + string.byte(c)) % 100
end

if hash_val < pct then
    return 1  -- Feature enabled for this user
end
return 0
```

---

## 15. Troubleshooting

### 15.1 NOSCRIPT Error

**Symptoms**: `NOSCRIPT No matching script`

**Cause**: Script cache was flushed (SCRIPT FLUSH, server restart, or cluster failover).

**Resolution**: Fall back to EVAL, or reload scripts at application startup. Use `register_script` in client libraries for automatic fallback.

### 15.2 BUSY Script

**Symptoms**: All commands return `BUSY Redis is busy running a script`.

**Diagnosis**: A script exceeded `lua-time-limit`.

**Resolution**:
```bash
SCRIPT KILL                    # If no writes performed
# OR
SHUTDOWN NOSAVE                # Last resort if writes were performed
```
Fix the script to run faster.

### 15.3 CROSSSLOT Error in Cluster

**Symptoms**: `CROSSSLOT Keys in request don't hash to the same slot`

**Cause**: KEYS passed to the script hash to different cluster slots.

**Resolution**: Use hash tags: `{entity:123}:field1` and `{entity:123}:field2` to ensure same slot.

### 15.4 Wrong Number of Arguments

**Symptoms**: `ERR wrong number of keys` or unexpected nil values in KEYS/ARGV.

**Cause**: `numkeys` parameter is wrong in the EVAL call.

**Resolution**: Ensure the numkeys value matches the actual number of KEYS arguments.

### 15.5 Type Error in Script

**Symptoms**: `WRONGTYPE Operation against a key holding the wrong kind of value`

**Cause**: Script calls a command incompatible with the key's data type (e.g., GET on a Hash).

**Resolution**: Check key type with `redis.call('TYPE', KEYS[1])` before operating.

### 15.6 Nil Values in Returned Table

**Symptoms**: Returned array is shorter than expected.

**Cause**: Lua tables with nil values are truncated (nil terminates array iteration).

**Resolution**: Replace nil with a sentinel value (empty string, `cjson.null`, or `false`).

### 15.7 Script Works Locally but Fails in Cluster

**Symptoms**: Script works on standalone Redis but fails in cluster.

**Cause**: Hardcoded key names, or KEYS spanning multiple slots.

**Resolution**: Pass all keys via KEYS[], use hash tags for multi-key operations.

### 15.8 Non-Deterministic Script Errors

**Symptoms**: `Write commands not allowed after non deterministic commands` (Redis < 7).

**Cause**: Script calls TIME, RANDOMKEY, or other non-deterministic commands before a write.

**Resolution**: In Redis < 7, call `redis.replicate_commands()` at the start. In Redis 7+, this is not needed (effects replication is default).

### 15.9 Memory Leak from Script Cache

**Symptoms**: `used_memory_scripts` grows continuously.

**Cause**: Application generates dynamic scripts (unique script bodies) that fill the cache.

**Resolution**: Never generate unique scripts at runtime. Use ARGV for variable data. Periodically `SCRIPT FLUSH` if needed.

### 15.10 Function Library Load Failure

**Symptoms**: `FUNCTION LOAD` returns error.

**Cause**: Syntax error in Lua, missing `#!lua name=` header, or duplicate function names.

**Resolution**: Validate the Lua script locally. Check for syntax errors. Use `REPLACE` flag for updates.

### 15.11 Script Timeout on Replica

**Symptoms**: Replica blocks during script replication.

**Cause**: In script replication mode, the entire EVAL is re-executed on the replica.

**Resolution**: Use Redis 7+ with effects replication (default). For Redis 6, ensure scripts are fast.

---

## 16. FAQ

### Q1: Should I use EVAL or Redis Functions?

Use Redis Functions for Redis 7+. They are persisted, replicated, named, and grouped into libraries. Use EVAL only for backwards compatibility with Redis 5/6.

### Q2: Can Lua scripts access external services (HTTP, database)?

No. Redis Lua is sandboxed. No network access, file access, or OS calls are available. Data must be in Redis or passed via ARGV.

### Q3: Are Lua scripts faster than pipelines?

For operations requiring atomicity, yes -- scripts execute atomically without round trips. For non-atomic batch operations, pipelines can be faster because they do not block other clients.

### Q4: What happens if a script crashes mid-execution?

If the script raises an unhandled error, Redis rolls back any partial changes to the AOF. The client receives the error. The server state is consistent.

### Q5: Can I use MULTI/EXEC inside a Lua script?

No. Redis scripts are already atomic. Using MULTI/EXEC inside a script is redundant and will cause an error.

### Q6: How many scripts can Redis cache?

There is no hard limit. The cache grows as scripts are loaded. Monitor `used_memory_scripts` and `number_of_cached_scripts`. If memory is a concern, use `SCRIPT FLUSH`.

### Q7: Can I call a Lua script from another Lua script?

No. Nested EVAL calls are not supported. Design scripts to be self-contained. In Redis 7+ Functions, you can call helper functions within the same library, but not functions from other libraries.

### Q8: How do I handle large return values from scripts?

Redis protocol has no hard limit on response size, but large responses consume client output buffer and network bandwidth. For large datasets, paginate within the script or return only summaries.

### Q9: Are Redis Functions persisted across restarts?

Yes. Functions are stored in the RDB and AOF. They survive restarts and are automatically replicated to replicas. This is a key advantage over EVAL scripts.

### Q10: Can I debug Functions the same way as EVAL scripts?

The `--ldb` debugger works with `--eval` (EVAL scripts). For Functions, debugging is more limited -- use `redis.log()` for logging and test in a development environment.

### Q11: What is the maximum script size?

There is no hard limit on script size, but scripts are stored in memory. A 1MB script is unusual and likely indicates a design problem. Keep scripts under 10KB for maintainability.

### Q12: How do I share state between multiple EVAL calls?

You cannot. Each EVAL/EVALSHA call starts with a fresh Lua environment. Shared state must be stored in Redis keys. This is by design -- it prevents hidden dependencies between script invocations.

---

*Questo documento fa parte del modulo 06 "NoSQL Redis" della Data Encyclopedia.*
