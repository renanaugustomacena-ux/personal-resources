# Redis: Programming Languages Integration

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
1. Python (redis-py)
2. Node.js (ioredis)
3. Java (Jedis/Lettuce)
4. Go (go-redis)
5. PHP (Predis / phpredis)
6. C# / .NET (StackExchange.Redis)
7. Rust (redis-rs)
8. Connection Pooling Across Languages
9. Error Handling Patterns
10. Async / Await Patterns
11. Serialization Strategies
12. Testing with Redis
13. Monitoring and Observability
14. Operational Best Practices
15. Troubleshooting
16. FAQ

---

## 1. Python (redis-py)

### 1.1 Installation and Basic Usage

```bash
pip install redis    # redis-py 5.x
```

```python
import redis

# Basic connection
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# Strings
r.set('key', 'value')
r.get('key')  # 'value'

# With TTL
r.setex('session:abc', 3600, 'user_data')
r.set('key', 'value', ex=300)  # 5 min expiry

# Hashes
r.hset('user:1', mapping={'name': 'John', 'email': 'john@example.com', 'age': '30'})
r.hgetall('user:1')  # {'name': 'John', 'email': 'john@example.com', 'age': '30'}
r.hget('user:1', 'name')  # 'John'

# Lists
r.lpush('queue', 'task1', 'task2', 'task3')
r.rpop('queue')  # 'task1'
r.lrange('queue', 0, -1)

# Sets
r.sadd('tags:1', 'python', 'redis', 'database')
r.sismember('tags:1', 'redis')  # True
r.smembers('tags:1')

# Sorted Sets
r.zadd('leaderboard', {'player1': 100, 'player2': 200})
r.zrevrange('leaderboard', 0, 9, withscores=True)
```

### 1.2 Connection Pool

```python
# Connection pool (required for production)
pool = redis.ConnectionPool(
    host='localhost',
    port=6379,
    db=0,
    max_connections=50,
    decode_responses=True,
    socket_timeout=5,
    socket_connect_timeout=2,
    retry_on_timeout=True,
    health_check_interval=30
)
r = redis.Redis(connection_pool=pool)

# SSL/TLS connection
pool = redis.ConnectionPool(
    host='redis.example.com',
    port=6380,
    ssl=True,
    ssl_certfile='/path/to/client.crt',
    ssl_keyfile='/path/to/client.key',
    ssl_ca_certs='/path/to/ca.crt'
)
```

### 1.3 Async Support (redis-py 5.x)

```python
import redis.asyncio as aioredis
import asyncio

async def main():
    r = aioredis.Redis(host='localhost', port=6379, decode_responses=True)

    await r.set('async_key', 'async_value')
    value = await r.get('async_key')
    print(value)  # 'async_value'

    # Async pipeline
    async with r.pipeline(transaction=False) as pipe:
        pipe.set('a', 1)
        pipe.set('b', 2)
        pipe.get('a')
        results = await pipe.execute()

    # Async Pub/Sub
    pubsub = r.pubsub()
    await pubsub.subscribe('notifications')
    async for message in pubsub.listen():
        if message['type'] == 'message':
            print(message['data'])

    await r.aclose()

asyncio.run(main())
```

### 1.4 Pipeline and Transaction

```python
# Pipeline (batch commands, reduce round trips)
pipe = r.pipeline(transaction=False)
for i in range(1000):
    pipe.set(f'key:{i}', f'value:{i}')
results = pipe.execute()

# Transaction (MULTI/EXEC -- atomic execution)
pipe = r.pipeline(transaction=True)
pipe.set('balance:A', 900)
pipe.set('balance:B', 100)
pipe.execute()

# Watch (optimistic locking)
with r.pipeline() as pipe:
    while True:
        try:
            pipe.watch('balance:A')
            balance = int(pipe.get('balance:A'))
            pipe.multi()
            pipe.set('balance:A', balance - 50)
            pipe.set('balance:B', balance + 50)
            pipe.execute()
            break
        except redis.WatchError:
            continue  # Retry on concurrent modification
```

### 1.5 Cluster Mode

```python
from redis.cluster import RedisCluster

rc = RedisCluster(
    host='redis-node-1',
    port=6379,
    password='password',
    decode_responses=True,
    read_from_replicas=True
)

rc.set('key', 'value')
rc.get('key')

# Cluster pipeline
pipe = rc.pipeline()
pipe.set('a', 1)
pipe.set('b', 2)
pipe.execute()
```

---

## 2. Node.js (ioredis)

### 2.1 Installation and Basic Usage

```bash
npm install ioredis
```

```javascript
const Redis = require('ioredis');

// Basic connection
const redis = new Redis({
  host: 'localhost',
  port: 6379,
  password: 'password',
  db: 0,
  retryStrategy(times) {
    const delay = Math.min(times * 50, 2000);
    return delay;
  },
  maxRetriesPerRequest: 3,
  lazyConnect: true
});

// Connect explicitly when using lazyConnect
await redis.connect();

// Strings
await redis.set('key', 'value');
await redis.set('key', 'value', 'EX', 300);  // with TTL
const value = await redis.get('key');

// Hashes
await redis.hset('user:1', 'name', 'John', 'email', 'john@test.com');
const user = await redis.hgetall('user:1');

// Lists
await redis.lpush('queue', 'task1', 'task2');
const task = await redis.rpop('queue');

// Sets
await redis.sadd('tags', 'js', 'redis');
const members = await redis.smembers('tags');

// Sorted Sets
await redis.zadd('scores', 100, 'player1', 200, 'player2');
const top = await redis.zrevrange('scores', 0, 9, 'WITHSCORES');
```

### 2.2 Pipeline and Transaction

```javascript
// Pipeline (batched, non-atomic)
const pipeline = redis.pipeline();
pipeline.set('foo', 'bar');
pipeline.set('baz', 'qux');
pipeline.get('foo');
const results = await pipeline.exec();
// results = [[null, 'OK'], [null, 'OK'], [null, 'bar']]

// Transaction (MULTI/EXEC, atomic)
const multi = redis.multi();
multi.set('balance:A', 900);
multi.set('balance:B', 100);
const txResults = await multi.exec();
```

### 2.3 Pub/Sub

```javascript
// Subscriber (separate connection -- required by Redis protocol)
const subscriber = new Redis();

subscriber.subscribe('notifications', (err, count) => {
  console.log(`Subscribed to ${count} channel(s)`);
});

subscriber.on('message', (channel, message) => {
  console.log(`${channel}: ${message}`);
});

// Pattern subscribe
subscriber.psubscribe('user:*:events');
subscriber.on('pmessage', (pattern, channel, message) => {
  console.log(`${pattern} → ${channel}: ${message}`);
});

// Publisher
await redis.publish('notifications', JSON.stringify({ event: 'new_order' }));
```

### 2.4 Cluster Mode

```javascript
const Redis = require('ioredis');

const cluster = new Redis.Cluster([
  { host: 'node-1', port: 6379 },
  { host: 'node-2', port: 6379 },
  { host: 'node-3', port: 6379 },
], {
  redisOptions: {
    password: 'password'
  },
  scaleReads: 'slave',  // Read from replicas
  natMap: {
    // NAT mapping for Docker/K8s environments
    '10.0.0.1:6379': { host: 'node-1.public', port: 6379 }
  }
});

await cluster.set('key', 'value');
```

### 2.5 Streams

```javascript
// Write to stream
await redis.xadd('events', '*', 'type', 'order', 'data', JSON.stringify({ id: 1 }));

// Read from stream
const entries = await redis.xrange('events', '-', '+', 'COUNT', 10);

// Consumer group
await redis.xgroup('CREATE', 'events', 'processors', '0', 'MKSTREAM');
const messages = await redis.xreadgroup(
  'GROUP', 'processors', 'worker-1',
  'COUNT', 10, 'BLOCK', 5000,
  'STREAMS', 'events', '>'
);
```

---

## 3. Java (Jedis / Lettuce)

### 3.1 Jedis (Synchronous)

```xml
<!-- pom.xml -->
<dependency>
  <groupId>redis.clients</groupId>
  <artifactId>jedis</artifactId>
  <version>5.1.0</version>
</dependency>
```

```java
import redis.clients.jedis.*;

// Connection pool (required for production)
JedisPoolConfig config = new JedisPoolConfig();
config.setMaxTotal(50);
config.setMaxIdle(20);
config.setMinIdle(5);
config.setTestOnBorrow(true);
config.setTestWhileIdle(true);
config.setMinEvictableIdleDuration(Duration.ofSeconds(60));

JedisPool pool = new JedisPool(config, "localhost", 6379, 2000, "password");

try (Jedis jedis = pool.getResource()) {
    // Strings
    jedis.set("key", "value");
    jedis.setex("session", 3600, "data");
    String value = jedis.get("key");

    // Hashes
    Map<String, String> user = new HashMap<>();
    user.put("name", "John");
    user.put("email", "john@test.com");
    jedis.hset("user:1", user);
    Map<String, String> result = jedis.hgetAll("user:1");

    // Pipeline
    Pipeline pipe = jedis.pipelined();
    for (int i = 0; i < 1000; i++) {
        pipe.set("key:" + i, "value:" + i);
    }
    pipe.sync();

    // Transaction
    Transaction tx = jedis.multi();
    tx.set("balance:A", "900");
    tx.set("balance:B", "100");
    tx.exec();
}
```

### 3.2 Lettuce (Async / Reactive)

```xml
<!-- pom.xml -->
<dependency>
  <groupId>io.lettuce</groupId>
  <artifactId>lettuce-core</artifactId>
  <version>6.3.0.RELEASE</version>
</dependency>
```

```java
import io.lettuce.core.*;
import io.lettuce.core.api.async.*;
import io.lettuce.core.api.sync.*;

// Create client (single multiplexed connection, thread-safe)
RedisClient client = RedisClient.create("redis://password@localhost:6379/0");
StatefulRedisConnection<String, String> connection = client.connect();

// Synchronous API
RedisCommands<String, String> sync = connection.sync();
sync.set("key", "value");
sync.setex("session", 3600, "data");
String value = sync.get("key");

// Asynchronous API
RedisAsyncCommands<String, String> async = connection.async();
RedisFuture<String> future = async.get("key");
future.thenAccept(val -> System.out.println(val));

// Reactive API (Project Reactor)
RedisReactiveCommands<String, String> reactive = connection.reactive();
reactive.get("key")
    .subscribe(val -> System.out.println(val));

// Cluster with Lettuce
RedisClusterClient clusterClient = RedisClusterClient.create(
    RedisURI.create("redis://password@node-1:6379")
);
StatefulRedisClusterConnection<String, String> clusterConn = clusterClient.connect();
clusterConn.sync().set("key", "value");
```

### 3.3 Spring Data Redis

```java
@Configuration
public class RedisConfig {
    @Bean
    public LettuceConnectionFactory connectionFactory() {
        RedisStandaloneConfiguration config = new RedisStandaloneConfiguration();
        config.setHostName("localhost");
        config.setPort(6379);
        config.setPassword("password");
        return new LettuceConnectionFactory(config);
    }

    @Bean
    public RedisTemplate<String, Object> redisTemplate(LettuceConnectionFactory factory) {
        RedisTemplate<String, Object> template = new RedisTemplate<>();
        template.setConnectionFactory(factory);
        template.setKeySerializer(new StringRedisSerializer());
        template.setValueSerializer(new GenericJackson2JsonRedisSerializer());
        return template;
    }
}

// Usage
@Autowired
private RedisTemplate<String, Object> redisTemplate;

redisTemplate.opsForValue().set("key", "value", Duration.ofMinutes(30));
Object value = redisTemplate.opsForValue().get("key");

redisTemplate.opsForHash().putAll("user:1", Map.of("name", "John"));
Map<Object, Object> user = redisTemplate.opsForHash().entries("user:1");
```

---

## 4. Go (go-redis)

### 4.1 Installation and Basic Usage

```bash
go get github.com/redis/go-redis/v9
```

```go
package main

import (
    "context"
    "fmt"
    "time"

    "github.com/redis/go-redis/v9"
)

func main() {
    ctx := context.Background()

    // Connection
    rdb := redis.NewClient(&redis.Options{
        Addr:         "localhost:6379",
        Password:     "password",
        DB:           0,
        DialTimeout:  5 * time.Second,
        ReadTimeout:  3 * time.Second,
        WriteTimeout: 3 * time.Second,
        PoolSize:     50,
        MinIdleConns: 10,
    })
    defer rdb.Close()

    // Ping
    if err := rdb.Ping(ctx).Err(); err != nil {
        panic(err)
    }

    // Strings
    err := rdb.Set(ctx, "key", "value", 5*time.Minute).Err()
    if err != nil {
        panic(err)
    }

    val, err := rdb.Get(ctx, "key").Result()
    if err == redis.Nil {
        fmt.Println("key does not exist")
    } else if err != nil {
        panic(err)
    } else {
        fmt.Println(val)
    }

    // Hashes
    rdb.HSet(ctx, "user:1", "name", "John", "email", "john@test.com")
    user, _ := rdb.HGetAll(ctx, "user:1").Result()
    fmt.Println(user) // map[email:john@test.com name:John]

    // Lists
    rdb.LPush(ctx, "queue", "task1", "task2")
    task, _ := rdb.RPop(ctx, "queue").Result()
    fmt.Println(task)

    // Sorted Sets
    rdb.ZAdd(ctx, "leaderboard", redis.Z{Score: 100, Member: "player1"})
    top, _ := rdb.ZRevRangeWithScores(ctx, "leaderboard", 0, 9).Result()
    fmt.Println(top)
}
```

### 4.2 Pipeline and Transaction

```go
// Pipeline
pipe := rdb.Pipeline()
for i := 0; i < 1000; i++ {
    pipe.Set(ctx, fmt.Sprintf("key:%d", i), fmt.Sprintf("val:%d", i), 0)
}
_, err := pipe.Exec(ctx)

// Transaction (MULTI/EXEC with WATCH)
err := rdb.Watch(ctx, func(tx *redis.Tx) error {
    balance, err := tx.Get(ctx, "balance:A").Int()
    if err != nil {
        return err
    }

    _, err = tx.TxPipelined(ctx, func(pipe redis.Pipeliner) error {
        pipe.Set(ctx, "balance:A", balance-50, 0)
        pipe.Set(ctx, "balance:B", balance+50, 0)
        return nil
    })
    return err
}, "balance:A")
```

### 4.3 Cluster Mode

```go
rdb := redis.NewClusterClient(&redis.ClusterOptions{
    Addrs:    []string{"node-1:6379", "node-2:6379", "node-3:6379"},
    Password: "password",
    ReadOnly: true,  // Read from replicas
    PoolSize: 50,
})
```

### 4.4 Pub/Sub

```go
// Subscriber
pubsub := rdb.Subscribe(ctx, "notifications")
defer pubsub.Close()

ch := pubsub.Channel()
for msg := range ch {
    fmt.Printf("Channel: %s, Payload: %s\n", msg.Channel, msg.Payload)
}

// Publisher
rdb.Publish(ctx, "notifications", "new event")
```

---

## 5. PHP (Predis / phpredis)

### 5.1 Predis (Pure PHP)

```bash
composer require predis/predis
```

```php
<?php
require 'vendor/autoload.php';

$client = new Predis\Client([
    'scheme' => 'tcp',
    'host'   => '127.0.0.1',
    'port'   => 6379,
    'password' => 'password',
    'timeout' => 5.0,
]);

// Strings
$client->set('key', 'value');
$client->setex('session', 3600, 'data');
$value = $client->get('key');

// Hashes
$client->hset('user:1', 'name', 'John');
$client->hset('user:1', 'email', 'john@test.com');
$user = $client->hgetall('user:1');

// Lists
$client->lpush('queue', 'task1', 'task2');
$task = $client->rpop('queue');

// Sets
$client->sadd('tags', 'php', 'redis');
$members = $client->smembers('tags');

// Pipeline
$responses = $client->pipeline(function ($pipe) {
    for ($i = 0; $i < 1000; $i++) {
        $pipe->set("key:$i", "value:$i");
    }
});

// Transaction
$responses = $client->transaction(function ($tx) {
    $tx->set('balance:A', 900);
    $tx->set('balance:B', 100);
});
```

### 5.2 phpredis (C Extension)

```bash
pecl install redis
```

```php
<?php
$redis = new Redis();
$redis->connect('127.0.0.1', 6379);
$redis->auth('password');

// Same API, but faster (C extension)
$redis->set('key', 'value');
$value = $redis->get('key');

// Serialization (auto serialize PHP objects)
$redis->setOption(Redis::OPT_SERIALIZER, Redis::SERIALIZER_JSON);
$redis->set('user', ['name' => 'John', 'age' => 30]);
$user = $redis->get('user');  // array

// Pub/Sub
$redis->subscribe(['channel'], function ($redis, $channel, $message) {
    echo "$channel: $message\n";
});

// Cluster
$cluster = new RedisCluster(null, ['node-1:6379', 'node-2:6379', 'node-3:6379']);
$cluster->set('key', 'value');
```

---

## 6. C# / .NET (StackExchange.Redis)

### 6.1 Installation and Usage

```bash
dotnet add package StackExchange.Redis
```

```csharp
using StackExchange.Redis;

// Connection (multiplexed, thread-safe, reuse across the app)
var connection = ConnectionMultiplexer.Connect("localhost:6379,password=password");
IDatabase db = connection.GetDatabase();

// Strings
await db.StringSetAsync("key", "value", TimeSpan.FromMinutes(30));
string value = await db.StringGetAsync("key");

// Hashes
await db.HashSetAsync("user:1", new HashEntry[] {
    new("name", "John"),
    new("email", "john@test.com")
});
HashEntry[] user = await db.HashGetAllAsync("user:1");

// Lists
await db.ListLeftPushAsync("queue", "task1");
string task = await db.ListRightPopAsync("queue");

// Sets
await db.SetAddAsync("tags", new RedisValue[] { "csharp", "redis" });
RedisValue[] members = await db.SetMembersAsync("tags");

// Sorted Sets
await db.SortedSetAddAsync("scores", "player1", 100);
var top = await db.SortedSetRangeByRankWithScoresAsync("scores", 0, 9, Order.Descending);

// Transaction
ITransaction tx = db.CreateTransaction();
tx.AddCondition(Condition.StringEqual("balance:A", "1000"));
tx.StringSetAsync("balance:A", "950");
tx.StringSetAsync("balance:B", "1050");
bool committed = await tx.ExecuteAsync();

// Batch (pipeline without MULTI/EXEC)
IBatch batch = db.CreateBatch();
var tasks = new List<Task>();
for (int i = 0; i < 1000; i++)
{
    tasks.Add(batch.StringSetAsync($"key:{i}", $"value:{i}"));
}
batch.Execute();
await Task.WhenAll(tasks);
```

### 6.2 Configuration Options

```csharp
var options = new ConfigurationOptions
{
    EndPoints = { "localhost:6379" },
    Password = "password",
    Ssl = true,
    SslProtocols = System.Security.Authentication.SslProtocols.Tls13,
    AbortOnConnectFail = false,
    ConnectTimeout = 5000,
    SyncTimeout = 5000,
    AsyncTimeout = 5000,
    KeepAlive = 60,
    ConnectRetry = 3
};

var connection = ConnectionMultiplexer.Connect(options);
```

---

## 7. Rust (redis-rs)

### 7.1 Installation and Usage

```toml
# Cargo.toml
[dependencies]
redis = { version = "0.25", features = ["tokio-comp", "connection-manager"] }
tokio = { version = "1", features = ["full"] }
```

```rust
use redis::{Commands, AsyncCommands};

// Synchronous
fn sync_example() -> redis::RedisResult<()> {
    let client = redis::Client::open("redis://password@localhost:6379/")?;
    let mut con = client.get_connection()?;

    con.set("key", "value")?;
    let value: String = con.get("key")?;
    println!("{}", value);

    // Hash
    con.hset_multiple("user:1", &[("name", "John"), ("email", "john@test.com")])?;
    let user: std::collections::HashMap<String, String> = con.hgetall("user:1")?;

    // Pipeline
    let (val1, val2): (String, String) = redis::pipe()
        .cmd("SET").arg("a").arg("1").ignore()
        .cmd("SET").arg("b").arg("2").ignore()
        .cmd("GET").arg("a")
        .cmd("GET").arg("b")
        .query(&mut con)?;

    Ok(())
}

// Async (tokio)
#[tokio::main]
async fn main() -> redis::RedisResult<()> {
    let client = redis::Client::open("redis://password@localhost:6379/")?;
    let mut con = client.get_multiplexed_async_connection().await?;

    con.set("key", "value").await?;
    let value: String = con.get("key").await?;
    println!("{}", value);

    Ok(())
}
```

### 7.2 Connection Manager (Auto-Reconnect)

```rust
use redis::aio::ConnectionManager;

let client = redis::Client::open("redis://localhost/")?;
let mut manager = ConnectionManager::new(client).await?;

// manager auto-reconnects on connection loss
manager.set("key", "value").await?;
```

---

## 8. Connection Pooling Across Languages

### 8.1 Pooling Summary

| Language | Library | Pool Type | Default Pool Size |
|---|---|---|---|
| Python | redis-py | Thread pool | 2^31 (effectively unlimited) |
| Node.js | ioredis | Single multiplexed | 1 connection |
| Java | Jedis | Apache Commons Pool | 8 |
| Java | Lettuce | Single multiplexed | 1 connection |
| Go | go-redis | Built-in pool | 10 * NumCPU |
| PHP | Predis | Per-request | No pooling |
| PHP | phpredis | Persistent connections | Per-worker |
| C# | StackExchange.Redis | Multiplexed | 1 connection |
| Rust | redis-rs | ConnectionManager | 1 connection |

### 8.2 Pool Sizing Guidelines

```
Pooled connections (Jedis, redis-py, go-redis):
  pool_size = max_concurrent_redis_operations * 1.2
  Example: 40 concurrent API handlers needing Redis → pool_size = 50

Multiplexed connections (Lettuce, ioredis, StackExchange.Redis):
  Usually 1 connection is sufficient for up to ~50K ops/sec
  Add more for very high throughput or connection-level operations (SUBSCRIBE, BLPOP)
```

---

## 9. Error Handling Patterns

### 9.1 Python

```python
from redis.exceptions import (
    ConnectionError, TimeoutError, ReadOnlyError,
    ResponseError, AuthenticationError
)

def safe_get(key):
    try:
        return r.get(key)
    except ConnectionError:
        # Redis server unreachable
        log.error("Redis connection failed")
        return None
    except TimeoutError:
        # Operation timed out
        log.warning("Redis operation timed out")
        return None
    except ReadOnlyError:
        # Writing to a read-only replica (failover in progress)
        log.warning("Redis instance is read-only, failover may be in progress")
        return None
    except ResponseError as e:
        # Command error (wrong type, NOPERM, etc.)
        log.error(f"Redis command error: {e}")
        raise
```

### 9.2 Go

```go
val, err := rdb.Get(ctx, "key").Result()
switch {
case err == redis.Nil:
    // Key does not exist
    log.Println("Key not found")
case err != nil:
    // Connection/timeout/other error
    log.Printf("Redis error: %v", err)
default:
    log.Printf("Value: %s", val)
}
```

### 9.3 Node.js

```javascript
redis.on('error', (err) => {
  console.error('Redis connection error:', err);
});

redis.on('reconnecting', (delay) => {
  console.log(`Reconnecting in ${delay}ms`);
});

// Per-command error handling
try {
  const value = await redis.get('key');
} catch (err) {
  if (err.message.includes('READONLY')) {
    // Failover in progress
  }
  console.error('Redis error:', err);
}
```

---

## 10. Async / Await Patterns

### 10.1 Python Async with FastAPI

```python
from fastapi import FastAPI
import redis.asyncio as aioredis

app = FastAPI()
redis_pool = None

@app.on_event("startup")
async def startup():
    global redis_pool
    redis_pool = aioredis.Redis(
        host='localhost', port=6379,
        decode_responses=True, max_connections=50
    )

@app.on_event("shutdown")
async def shutdown():
    await redis_pool.aclose()

@app.get("/user/{user_id}")
async def get_user(user_id: int):
    cached = await redis_pool.get(f"user:{user_id}")
    if cached:
        return json.loads(cached)
    user = await db.fetch_user(user_id)
    await redis_pool.setex(f"user:{user_id}", 3600, json.dumps(user))
    return user
```

### 10.2 Node.js with Express

```javascript
const express = require('express');
const Redis = require('ioredis');

const app = express();
const redis = new Redis({ host: 'localhost', port: 6379 });

app.get('/user/:id', async (req, res) => {
  const cacheKey = `user:${req.params.id}`;
  const cached = await redis.get(cacheKey);

  if (cached) {
    return res.json(JSON.parse(cached));
  }

  const user = await db.getUser(req.params.id);
  await redis.setex(cacheKey, 3600, JSON.stringify(user));
  res.json(user);
});
```

---

## 11. Serialization Strategies

### 11.1 JSON (Most Common)

```python
# Python
import json
r.set('user:1', json.dumps({'name': 'John', 'age': 30}))
user = json.loads(r.get('user:1'))
```

### 11.2 MessagePack (Faster, More Compact)

```python
# Python
import msgpack
r.set('user:1', msgpack.packb({'name': 'John', 'age': 30}))
user = msgpack.unpackb(r.get('user:1'))
```

### 11.3 Protocol Buffers (Schema-Enforced)

```python
# Serialize with protobuf
user = User(name='John', age=30)
r.set('user:1', user.SerializeToString())

# Deserialize
user = User()
user.ParseFromString(r.get('user:1'))
```

### 11.4 Comparison

| Format | Speed | Size | Schema | Human-Readable |
|---|---|---|---|---|
| JSON | Baseline | Largest | No | Yes |
| MessagePack | ~2-5x faster | ~30% smaller | No | No |
| Protocol Buffers | ~3-10x faster | ~50% smaller | Yes (enforced) | No |
| Pickle (Python) | Fast | Variable | No | No (insecure) |

**Security note**: Never use Python `pickle` for Redis values if untrusted clients can write to the same Redis instance. Pickle deserialization can execute arbitrary code.

---

## 12. Testing with Redis

### 12.1 Real Redis (Integration Tests)

```python
# pytest with real Redis
import pytest
import redis

@pytest.fixture
def redis_client():
    r = redis.Redis(host='localhost', port=6379, db=15)  # Use separate DB for tests
    r.flushdb()  # Clean before each test
    yield r
    r.flushdb()  # Clean after each test

def test_cache_hit(redis_client):
    redis_client.set('key', 'value')
    assert redis_client.get('key') == b'value'
```

### 12.2 fakeredis (Unit Tests)

```python
# pip install fakeredis
import fakeredis

def test_rate_limiter():
    r = fakeredis.FakeRedis()
    for i in range(100):
        r.incr('ratelimit:user1')
    assert int(r.get('ratelimit:user1')) == 100
```

### 12.3 Testcontainers

```python
# pip install testcontainers
from testcontainers.redis import RedisContainer

def test_with_container():
    with RedisContainer() as redis_container:
        r = redis.Redis(
            host=redis_container.get_container_host_ip(),
            port=redis_container.get_exposed_port(6379)
        )
        r.set('key', 'value')
        assert r.get('key') == b'value'
```

```java
// Java Testcontainers
@Testcontainers
class RedisTest {
    @Container
    private GenericContainer<?> redis = new GenericContainer<>("redis:7-alpine")
        .withExposedPorts(6379);

    @Test
    void testBasicOperations() {
        Jedis jedis = new Jedis(redis.getHost(), redis.getFirstMappedPort());
        jedis.set("key", "value");
        assertEquals("value", jedis.get("key"));
    }
}
```

---

## 13. Monitoring and Observability

### 13.1 Client-Side Metrics

```python
# redis-py provides connection pool stats
pool = r.connection_pool
print(f"Created connections: {pool._created_connections}")
print(f"Available connections: {len(pool._available_connections)}")
print(f"In-use connections: {len(pool._in_use_connections)}")
```

### 13.2 Latency Tracking

```python
import time

class InstrumentedRedis:
    def __init__(self, redis_client, metrics_client):
        self.r = redis_client
        self.metrics = metrics_client

    def get(self, key):
        start = time.monotonic()
        try:
            result = self.r.get(key)
            self.metrics.observe('redis_command_duration_seconds', time.monotonic() - start,
                                labels={'command': 'GET', 'status': 'ok'})
            return result
        except Exception as e:
            self.metrics.observe('redis_command_duration_seconds', time.monotonic() - start,
                                labels={'command': 'GET', 'status': 'error'})
            raise
```

---

## 14. Operational Best Practices

### 14.1 Connection Management Checklist

- Always use connection pools or multiplexed connections in production
- Set `socket_timeout` and `socket_connect_timeout` to prevent hanging
- Implement retry logic with exponential backoff
- Handle `ReadOnlyError` for Sentinel/Cluster failover scenarios
- Close connections/pools on application shutdown

### 14.2 Serialization Checklist

- Use JSON for debugging ease and interoperability
- Use MessagePack for performance-critical paths with large payloads
- Never serialize language-specific objects (pickle, Java serialization) if other languages may read the data
- Always handle deserialization errors (corrupted data, schema changes)

### 14.3 Key Naming Convention

```
{service}:{entity}:{id}:{field}

Examples:
webapp:user:123:profile
api:cache:products:page:1
worker:lock:process_orders
```

---

## 15. Troubleshooting

### 15.1 Connection Pool Exhaustion

**Symptoms**: `redis.exceptions.ConnectionError: Too many connections` or application hangs waiting for connection.

**Diagnosis**: Check `CLIENT LIST` for total connections. Check pool stats in the client library.

**Resolution**: Increase pool size, reduce connection hold time, ensure connections are returned to pool (use context managers/try-finally).

### 15.2 Serialization Errors

**Symptoms**: `json.decoder.JSONDecodeError` or garbled data on GET.

**Cause**: Mixed serialization formats in same keyspace, or `decode_responses=True` on binary data.

**Resolution**: Use consistent serialization per key prefix. Disable `decode_responses` when storing binary data.

### 15.3 MOVED / ASK Errors in Cluster

**Symptoms**: `redis.exceptions.ResponseError: MOVED 12345 10.0.0.2:6379`

**Cause**: Using a non-cluster-aware client for a Redis Cluster.

**Resolution**: Use `RedisCluster` client instead of `Redis` client.

### 15.4 Timeout on BRPOP / BLPOP

**Symptoms**: Client timeout exception during blocking pop.

**Cause**: `socket_timeout` is shorter than the `BLOCK` timeout.

**Resolution**: Set `socket_timeout` greater than the block timeout, or use `0` block with a socket timeout check loop.

### 15.5 ReadOnlyError After Failover

**Symptoms**: Write commands return `READONLY You can't write against a read only replica`.

**Cause**: Client is still connected to the old master which is now a replica.

**Resolution**: Use Sentinel-aware or Cluster-aware client that auto-discovers the new master.

### 15.6 High Latency from Large Pipelines

**Symptoms**: Pipeline `execute()` takes seconds despite fast individual commands.

**Cause**: Pipeline is too large (millions of commands), causing memory pressure on both client and server.

**Resolution**: Batch pipelines in chunks of 5,000-10,000 commands.

### 15.7 Memory Leak from Unclosed Pub/Sub

**Symptoms**: Connection count grows over time, eventually hitting `maxclients`.

**Cause**: Pub/Sub subscribers are created but never closed (each requires a dedicated connection).

**Resolution**: Always call `pubsub.close()` or `pubsub.unsubscribe()` when done. Use context managers.

### 15.8 Go Context Cancellation Not Working

**Symptoms**: Redis operations do not respect context timeout/cancellation in Go.

**Cause**: Using an older version of go-redis that ignores context.

**Resolution**: Use go-redis v9+, which respects context cancellation and deadlines.

### 15.9 Cluster Pipeline Returning Partial Results

**Symptoms**: Some commands in a cluster pipeline fail with `CROSSSLOT` error.

**Cause**: Multi-key commands (MGET, MSET) in pipeline target different hash slots.

**Resolution**: Use hash tags `{tag}:key` to ensure multi-key commands target the same slot, or split into single-key commands.

### 15.10 Authentication Failure After ACL Change

**Symptoms**: Existing connections get `NOAUTH` or `NOPERM` errors after ACL update.

**Cause**: ACL changes apply to new authentications. Existing connections retain old permissions until re-authenticated.

**Resolution**: After ACL changes, applications must re-authenticate or reconnect. Some client libraries handle this automatically on reconnect.

---

## 16. FAQ

### Q1: Which Java client should I use -- Jedis or Lettuce?

Use Lettuce for: async/reactive applications, Spring Boot (default), multiplexed connections. Use Jedis for: synchronous code, when you prefer a simpler API, or when you need explicit connection management.

### Q2: Is ioredis still maintained after the Valkey fork?

Yes. ioredis works with both Redis and Valkey. The wire protocol is the same. No code changes are needed to switch between Redis and Valkey server implementations.

### Q3: Should I use connection pooling with ioredis?

No. ioredis uses a single multiplexed connection by default, which is sufficient for most workloads. Only create additional connections for blocking operations (BLPOP, SUBSCRIBE).

### Q4: How do I handle Redis being unavailable?

Implement circuit breaker pattern: after N consecutive failures, stop attempting Redis for a cooldown period and fall back to database or defaults. Resume Redis after cooldown.

### Q5: Can I use Redis Cluster with all client libraries?

All major libraries support Cluster mode. Use the cluster-specific client class (e.g., `RedisCluster` in Python, `Redis.Cluster` in ioredis, `RedisClusterClient` in Lettuce).

### Q6: What serialization format should I use for cross-language interoperability?

JSON. It is universally supported, human-readable, and debuggable. Use MessagePack if you need better performance and all consumers can deserialize it.

### Q7: How do I run Redis commands not exposed by the client library?

Most libraries provide a raw command method:
```python
# Python
r.execute_command('CLIENT', 'TRACKINGINFO')

# Go
rdb.Do(ctx, "CLIENT", "TRACKINGINFO").Result()

# Node.js
redis.call('CLIENT', 'TRACKINGINFO')
```

### Q8: Does decode_responses affect performance?

Slightly. With `decode_responses=True`, every response is decoded from bytes to UTF-8 string. For binary data (images, serialized protobufs), disable it to avoid encoding overhead and errors.

### Q9: How do I profile slow Redis calls from the application?

1. Wrap client methods with timing instrumentation
2. Check `SLOWLOG GET` on the server side
3. Use APM tools (Datadog, New Relic) with Redis integration
4. Enable `latency-monitor-threshold` on the Redis server

### Q10: Can I use the same Redis connection for Pub/Sub and regular commands?

No. When a connection enters subscriber mode (`SUBSCRIBE`), it can only execute subscription-related commands. Use a separate connection (or a second client instance) for Pub/Sub.

### Q11: How do I handle schema changes in cached values?

Use versioned keys (`cache:user:v2:123`) or include a version field in the serialized data. On schema change, increment the version and let old keys expire naturally.

### Q12: Is redis-py thread-safe?

Yes. The `Redis` client with connection pooling is thread-safe. Each thread borrows a connection from the pool, uses it, and returns it. Do not share a single connection across threads without a pool.

---

*Questo documento fa parte del modulo 06 "NoSQL Redis" della Data Encyclopedia.*
