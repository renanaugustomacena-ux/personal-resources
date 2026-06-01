---
corso: "SWE Masterclass"
fase: "2 — Architecture & Design"
modulo: "2.2c"
titolo: "API Design & Evolution"
versione: "2026-05-29"
livello: "Advanced"
prerequisiti:
  - "Solid understanding of HTTP semantics (methods, status codes, headers)"
  - "Familiarity with at least one API technology (REST, GraphQL, or gRPC)"
obiettivi:
  - "Design a REST API that reaches Level 3 of the Richardson Maturity Model"
  - "Implement an API versioning strategy with a deprecation policy and migration path"
  - "Model a GraphQL schema with pagination (Relay Connection spec) and query complexity limiting"
  - "Define a gRPC service using Protocol Buffers with all four communication patterns (unary, server-streaming, client-streaming, bidirectional)"
  - "Author an OpenAPI 3.1+ specification with contract tests that validate backward compatibility"
tag: [api-design, REST, GraphQL, gRPC, OpenAPI, versioning, deprecation, protobuf, HATEOAS]
---

# Module 2.2c: API Design & Evolution

> ### Learning Objectives
>
> By the end of this module you will be able to:
> - Design a REST API that reaches Level 3 of the Richardson Maturity Model
> - Implement an API versioning strategy with a deprecation policy and migration path
> - Model a GraphQL schema with pagination (Relay Connection spec) and query complexity limiting
> - Define a gRPC service using Protocol Buffers with all four communication patterns
> - Author an OpenAPI 3.1+ specification with contract tests that validate backward compatibility

> **Module 02.2.c** · **Last updated:** 2026-05-22

## Guiding ideas
1. **Backwards compatibility: never break, always add.**
2. **Versioning: header > URL.**
3. **Deprecation policy: announce + grace period + retire.**
4. **OpenAPI 3.1+ for spec + codegen.**

---

## Table of Contents

1. REST API Design — Richardson Maturity Model
2. REST Best Practices
3. Pagination Patterns
4. Rate Limiting
5. GraphQL Schema Design
6. GraphQL Performance
7. gRPC & Protocol Buffers
8. API Versioning Strategies
9. Backward Compatibility & Deprecation
10. OpenAPI / Swagger
11. API Security
12. Idempotency in APIs
13. Error Handling
14. Common Pitfalls & Troubleshooting
15. Q&A — Frequently Asked Questions
16. Hands-On Exercises
17. References

---

## 1. REST API Design — Richardson Maturity Model

Leonard Richardson (2008) defined a maturity model for REST APIs, from "HTTP as tunnel" to true HATEOAS.

### 1.1 Level 0 — The Swamp of POX (Plain Old XML/JSON)

HTTP is used as a transport tunnel. Everything goes through one endpoint.

```
POST /api
Content-Type: application/json

{"action": "getUser", "userId": 123}

POST /api
Content-Type: application/json

{"action": "createUser", "name": "Alice", "email": "alice@example.com"}
```

No resource URIs, no HTTP methods, no status codes. Essentially RPC over HTTP. SOAP typically lives here.

### 1.2 Level 1 — Resources

Introduce distinct URIs for different resources, but still use one HTTP method (usually POST).

```
POST /users/123        ← get user
POST /users            ← create user
POST /orders/456       ← get order
POST /orders/456/cancel ← cancel order
```

Better: resources have identity. But HTTP semantics (GET, PUT, DELETE) are not used.

### 1.3 Level 2 — HTTP Verbs

Use HTTP methods correctly. Use status codes. This is where most production APIs land.

```
GET    /users/123          → 200 OK + user body
POST   /users              → 201 Created + Location header
PUT    /users/123          → 200 OK (full replacement)
PATCH  /users/123          → 200 OK (partial update)
DELETE /users/123          → 204 No Content

GET    /orders?status=open → 200 OK + filtered list
```

**HTTP Methods:**

| Method | Idempotent | Safe | Request Body | Use |
|---|---|---|---|---|
| GET | Yes | Yes | No | Read resource |
| POST | No | No | Yes | Create resource, trigger action |
| PUT | Yes | No | Yes | Replace resource completely |
| PATCH | No* | No | Yes | Partial update |
| DELETE | Yes | No | No | Remove resource |
| HEAD | Yes | Yes | No | Headers only (check existence) |
| OPTIONS | Yes | Yes | No | CORS preflight, capabilities |

*PATCH is idempotent only if the patch operation itself is idempotent (e.g., `SET field=value`). It is not idempotent if the operation is relative (e.g., `INCREMENT counter`).

**HTTP Status Codes (Critical Subset):**

| Code | Meaning | When to Use |
|---|---|---|
| 200 | OK | Successful GET, PUT, PATCH |
| 201 | Created | Successful POST that creates a resource |
| 204 | No Content | Successful DELETE (or action with no response body) |
| 400 | Bad Request | Invalid request body, malformed JSON |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Authenticated but not authorized |
| 404 | Not Found | Resource does not exist |
| 409 | Conflict | Concurrent modification conflict |
| 422 | Unprocessable Entity | Valid JSON but fails validation |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Unhandled server exception |
| 502 | Bad Gateway | Upstream service failure |
| 503 | Service Unavailable | Maintenance, overload |
| 504 | Gateway Timeout | Upstream service timeout |

### 1.4 Level 3 — HATEOAS (Hypermedia As The Engine Of Application State)

Responses include links to related actions. The client discovers the API by following links, not by hardcoding URLs.

```json
{
  "id": 123,
  "name": "Alice",
  "email": "alice@example.com",
  "status": "active",
  "_links": {
    "self": {"href": "/users/123"},
    "orders": {"href": "/users/123/orders"},
    "deactivate": {"href": "/users/123/deactivate", "method": "POST"},
    "update": {"href": "/users/123", "method": "PUT"}
  }
}
```

**In theory:** Clients never construct URLs. They follow links from the API root.
**In practice:** Few APIs implement full HATEOAS. The coupling benefit is real but the implementation cost is high. Most APIs stop at Level 2.

### 1.5 Practical Recommendation

Target Level 2 with selective Level 3 elements:
- Use proper HTTP methods and status codes (Level 2).
- Include `self` links and pagination links (Level 3 subset).
- Skip full HATEOAS unless you have a strong client-discovery requirement.

---

## 2. REST Best Practices

### 2.1 Resource Naming

```
GOOD:
  /users                    ← collection
  /users/123                ← specific resource
  /users/123/orders         ← sub-resource
  /users/123/orders/456     ← specific sub-resource

BAD:
  /getUser                  ← verb in URL (use GET method instead)
  /user_list                ← not plural
  /Users/123/Orders         ← inconsistent casing
  /api/v1/users/getById/123 ← over-nested, verb
```

**Rules:**
1. Use plural nouns for collections: `/users`, `/orders`, `/products`.
2. Use lowercase with hyphens: `/order-items` (not `orderItems` or `order_items`).
3. Use resource nesting for true parent-child relationships only.
4. Avoid deep nesting (> 2 levels): `/users/123/orders/456/items/789` → flatten to `/order-items/789`.

### 2.2 Filtering, Sorting, and Field Selection

```
# Filtering
GET /orders?status=open&customer_id=123

# Sorting
GET /orders?sort=-created_at,+total  # - = desc, + = asc

# Field selection (sparse fieldsets)
GET /users/123?fields=name,email

# Combined
GET /orders?status=open&sort=-created_at&fields=id,status,total&page=2&per_page=25
```

### 2.3 Bulk Operations

```
# Create multiple resources
POST /users/bulk
Content-Type: application/json

[
  {"name": "Alice", "email": "alice@example.com"},
  {"name": "Bob", "email": "bob@example.com"}
]

Response: 207 Multi-Status
[
  {"index": 0, "status": 201, "id": "user-1"},
  {"index": 1, "status": 422, "error": "Email already exists"}
]
```

### 2.4 Content Negotiation

```
# Client requests JSON
GET /users/123
Accept: application/json

# Client requests CSV
GET /reports/monthly
Accept: text/csv

# Server cannot produce requested format
406 Not Acceptable
```

### 2.5 Conditional Requests (ETags)

```
# Server returns ETag with response
GET /users/123
→ 200 OK
ETag: "abc123"

# Client sends If-None-Match (for caching)
GET /users/123
If-None-Match: "abc123"
→ 304 Not Modified (no body, client uses cached version)

# Client sends If-Match (for optimistic concurrency)
PUT /users/123
If-Match: "abc123"
Content-Type: application/json
{"name": "Alice Updated"}

→ 200 OK (if ETag matches)
→ 412 Precondition Failed (if someone else modified it)
```

---

## 3. Pagination Patterns

### 3.1 Offset-Based Pagination

```
GET /orders?offset=0&limit=25   → items 1-25
GET /orders?offset=25&limit=25  → items 26-50
GET /orders?offset=50&limit=25  → items 51-75
```

**Response:**

```json
{
  "data": [...],
  "pagination": {
    "offset": 25,
    "limit": 25,
    "total": 1234
  }
}
```

**Pros:** Simple, client can jump to any page.
**Cons:** Slow for deep pages (`OFFSET 100000` scans 100K rows). Inconsistent if data is inserted/deleted between pages (items can be skipped or duplicated).

### 3.2 Cursor-Based Pagination (Keyset)

Use the last item's unique identifier as the cursor.

```
GET /orders?limit=25                        → first page
GET /orders?limit=25&after=ord_abc123       → next page
GET /orders?limit=25&before=ord_xyz789      → previous page
```

**Implementation:**

```sql
-- First page
SELECT * FROM orders
ORDER BY created_at DESC, id DESC
LIMIT 26;  -- fetch 1 extra to know if there's a next page

-- Next page (cursor = last item's created_at + id)
SELECT * FROM orders
WHERE (created_at, id) < ('2026-05-22T10:00:00Z', 'ord_abc123')
ORDER BY created_at DESC, id DESC
LIMIT 26;
```

**Response:**

```json
{
  "data": [...],
  "pagination": {
    "has_next": true,
    "has_prev": true,
    "next_cursor": "eyJjcmVhdGVkX2F0IjoiMjAyNi0wNS0yMiIsImlkIjoib3JkXzEyMyJ9",
    "prev_cursor": "eyJjcmVhdGVkX2F0IjoiMjAyNi0wNS0yMiIsImlkIjoib3JkXzQ1NiJ9"
  }
}
```

**Pros:** Consistent (no skips/duplicates), fast (uses index).
**Cons:** Cannot jump to arbitrary page, requires a stable sort order.

### 3.3 Cursor Encoding

Encode the cursor as base64 of the sort key(s). This hides the implementation and allows changing the underlying column without breaking clients.

```python
import base64
import json

def encode_cursor(created_at: str, id: str) -> str:
    payload = json.dumps({"created_at": created_at, "id": id})
    return base64.urlsafe_b64encode(payload.encode()).decode()

def decode_cursor(cursor: str) -> dict:
    payload = base64.urlsafe_b64decode(cursor.encode())
    return json.loads(payload)
```

### 3.4 Comparison

| Feature | Offset | Cursor | Page Number |
|---|---|---|---|
| Random page access | Yes | No | Yes |
| Consistency | Poor | Good | Poor |
| Performance at depth | O(offset) | O(1) | O(offset) |
| Client complexity | Low | Medium | Low |
| Best for | Small datasets, admin UIs | Feeds, timelines, large datasets | Simple web apps |

**Recommendation:** Use cursor-based for any API that will have > 10K records or real-time data. Use offset for admin dashboards with small datasets.

---

## 4. Rate Limiting

### 4.1 Algorithms

#### Fixed Window

```
Window: 1 minute
Limit: 100 requests per window

10:00:00 - 10:00:59 → count requests
  At 10:00:45: 100 requests → ALLOW
  At 10:00:46: 101st request → REJECT (429)

10:01:00 → counter resets
```

**Problem:** Boundary burst. 100 requests at 10:00:59, 100 more at 10:01:00 = 200 requests in 2 seconds.

#### Sliding Window Log

Track the timestamp of each request. Count requests in the last N seconds.

```
Each request: append timestamp to sorted set
Check: count timestamps in [now - window, now]
If count >= limit → reject
Prune: remove timestamps older than window
```

**Pros:** Precise, no boundary burst.
**Cons:** Memory (stores every timestamp).

#### Sliding Window Counter

Approximate sliding window using weighted fixed windows:

```
Current window count: 30 (10:01:00 - 10:01:59)
Previous window count: 80 (10:00:00 - 10:00:59)
Current position in window: 25% (10:01:15)

Weighted count = 30 + 80 * (1 - 0.25) = 30 + 60 = 90
Limit: 100
Result: ALLOW (90 < 100)
```

**Pros:** Low memory (two counters per window).

#### Token Bucket

Already covered in Module 2.2 (Distributed System Patterns). Allows bursts up to bucket capacity.

#### Leaky Bucket

Requests enter a queue that drains at a fixed rate. If the queue is full, new requests are dropped.

```
Queue capacity: 10
Drain rate: 1 request per 100ms (10 req/sec)

Burst of 15 requests:
  First 10 → queued, processed at 100ms intervals
  Next 5 → dropped (queue full)
```

### 4.2 Rate Limit Headers

```http
HTTP/1.1 200 OK
X-RateLimit-Limit: 100          # max requests per window
X-RateLimit-Remaining: 42       # requests left
X-RateLimit-Reset: 1716393600   # Unix timestamp when window resets

# On rate limit exceeded:
HTTP/1.1 429 Too Many Requests
Retry-After: 30                 # seconds until client should retry
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1716393600
```

### 4.3 Distributed Rate Limiting

Single-instance rate limiting fails in a load-balanced environment. Options:

1. **Central store (Redis):** `INCR key`, `EXPIRE key ttl`. All instances share the counter.
2. **Sticky sessions:** Route same client to same instance (limits scope of rate limiting).
3. **Local + sync:** Each instance tracks locally, syncs periodically with central store (approximate but low latency).

```python
# Redis sliding window (sorted set)
import redis
import time

def is_rate_limited(r: redis.Redis, client_id: str,
                    limit: int, window: int) -> bool:
    key = f"rate:{client_id}"
    now = time.time()
    pipe = r.pipeline()
    pipe.zremrangebyscore(key, 0, now - window)  # prune old
    pipe.zadd(key, {str(now): now})              # add current
    pipe.zcard(key)                              # count
    pipe.expire(key, window)                     # TTL safety
    results = pipe.execute()
    count = results[2]
    return count > limit
```

### 4.4 Rate Limiting Strategies

| Strategy | Rate Limit By | Use Case |
|---|---|---|
| Per API key | API key header | SaaS API, partner integrations |
| Per IP | Client IP | Public API, DDoS protection |
| Per user | Authenticated user ID | User-facing API |
| Per endpoint | URL path | Protect expensive endpoints (search, export) |
| Tiered | Plan level (free/pro/enterprise) | SaaS pricing differentiation |

---

## 5. GraphQL Schema Design

### 5.1 Schema-First vs Code-First

**Schema-first:** Write the SDL (Schema Definition Language) first, then implement resolvers.

```graphql
type User {
  id: ID!
  name: String!
  email: String!
  orders(first: Int, after: String): OrderConnection!
}

type Order {
  id: ID!
  total: Money!
  status: OrderStatus!
  createdAt: DateTime!
  items: [OrderItem!]!
}

type OrderItem {
  product: Product!
  quantity: Int!
  unitPrice: Money!
}

scalar Money
scalar DateTime

enum OrderStatus {
  DRAFT
  SUBMITTED
  SHIPPED
  DELIVERED
  CANCELLED
}

type Query {
  user(id: ID!): User
  orders(status: OrderStatus, first: Int, after: String): OrderConnection!
}

type Mutation {
  submitOrder(orderId: ID!): SubmitOrderPayload!
  cancelOrder(orderId: ID!): CancelOrderPayload!
}

type SubmitOrderPayload {
  order: Order
  errors: [UserError!]!
}

type UserError {
  field: String
  message: String!
}
```

**Pros:** Design-first, language-agnostic, reviewable by frontend and backend teams.
**Cons:** Must keep schema and code in sync.

### 5.2 Connection Pattern (Relay Specification)

The standard for paginated lists in GraphQL:

```graphql
type OrderConnection {
  edges: [OrderEdge!]!
  pageInfo: PageInfo!
  totalCount: Int!
}

type OrderEdge {
  node: Order!
  cursor: String!
}

type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}
```

```graphql
query {
  orders(first: 10, after: "cursor_abc") {
    edges {
      node {
        id
        total
        status
      }
      cursor
    }
    pageInfo {
      hasNextPage
      endCursor
    }
    totalCount
  }
}
```

### 5.3 Mutation Design

Use input types and payload types:

```graphql
input SubmitOrderInput {
  orderId: ID!
}

type SubmitOrderPayload {
  order: Order
  errors: [UserError!]!
}

type Mutation {
  submitOrder(input: SubmitOrderInput!): SubmitOrderPayload!
}
```

**Rules:**
1. Every mutation returns a payload type with the modified resource + errors.
2. Use input types (not inline arguments) for mutations.
3. Mutations are named as verbs: `submitOrder`, `cancelOrder`, not `order` or `updateOrder`.
4. Return `UserError` for business rule violations (not HTTP errors).

### 5.4 Schema Evolution Rules

1. **Adding a field:** Always safe. Existing queries do not request it.
2. **Adding an enum value:** Safe if clients use a `default` case. Unsafe if clients exhaustively match.
3. **Deprecating a field:** Mark with `@deprecated(reason: "Use newField instead")`. Clients see warnings.
4. **Removing a field:** Breaking change. Never remove without deprecation period.
5. **Changing a field type:** Breaking. Add a new field instead.
6. **Making a nullable field non-null:** Breaking (clients may pass null).
7. **Making a non-null field nullable:** Safe (broadens contract).

---

## 6. GraphQL Performance

### 6.1 The N+1 Problem

```graphql
query {
  authors {
    name
    books {        # N+1: one query per author
      title
    }
  }
}
```

**Execution:**
1. `SELECT * FROM authors` → 10 authors.
2. For each author: `SELECT * FROM books WHERE author_id = ?` → 10 queries.
3. Total: 11 queries.

### 6.2 DataLoader Pattern

Batch and deduplicate database calls within a single request tick.

```python
from aiodataloader import DataLoader

async def batch_load_books(author_ids):
    """Called once per tick with ALL requested author IDs."""
    books = await db.fetch(
        "SELECT * FROM books WHERE author_id = ANY($1)",
        author_ids,
    )
    # Map results back to input order
    books_by_author = defaultdict(list)
    for book in books:
        books_by_author[book["author_id"]].append(book)
    return [books_by_author.get(aid, []) for aid in author_ids]

book_loader = DataLoader(batch_load_books)

# Resolver
async def resolve_books(author, info):
    return await book_loader.load(author.id)
    # All author.books resolvers in the same query batch into ONE SQL query
```

### 6.3 Query Complexity Limiting

Prevent clients from sending extremely expensive queries.

```graphql
# Dangerous query: exponential depth
query {
  users {
    friends {
      friends {
        friends {
          friends {
            name  # 4 levels deep, potentially millions of records
          }
        }
      }
    }
  }
}
```

**Solutions:**

1. **Query depth limiting:** Max depth = 5.
2. **Query complexity scoring:** Assign a cost per field, reject queries exceeding a budget.

```python
# Complexity calculation
# Each field = 1 point
# Each list field = multiplied by estimated size
# users (est. 100) × friends (est. 50) × friends (est. 50)
# = 100 × 50 × 50 = 250,000 points
# Budget: 10,000 points → REJECT
```

3. **Persisted queries:** Client sends a query hash, not the full query text. Only pre-approved queries are accepted.

### 6.4 Response Caching

GraphQL makes HTTP caching hard because all requests are POST to a single endpoint.

**Solutions:**
- Use `@cacheControl` directive to annotate field-level TTLs.
- Use a GraphQL-aware CDN (Apollo, Stellate) or cache at the resolver level.
- For public data: use GET requests with the query in the URL (CDN-friendly).

---

## 7. gRPC & Protocol Buffers

### 7.1 Protocol Buffer Encoding

```protobuf
syntax = "proto3";

message User {
  int32 id = 1;          // field number 1
  string name = 2;       // field number 2
  string email = 3;      // field number 3
  repeated Order orders = 4;
}

message Order {
  string id = 1;
  int64 total_cents = 2;
  OrderStatus status = 3;
}

enum OrderStatus {
  ORDER_STATUS_UNSPECIFIED = 0;
  ORDER_STATUS_DRAFT = 1;
  ORDER_STATUS_SUBMITTED = 2;
}
```

**Wire format:** Each field is encoded as `(field_number << 3 | wire_type)` followed by the value.

```
JSON: {"id": 123, "name": "Alice"}  → 30 bytes
Protobuf: 08 7B 12 05 41 6C 69 63 65  → 9 bytes (3.3x smaller)

08 = field 1, varint type
7B = 123 (varint encoding)
12 = field 2, length-delimited type
05 = length 5
41 6C 69 63 65 = "Alice" (UTF-8)
```

### 7.2 gRPC Communication Patterns

| Pattern | Description | Use Case |
|---|---|---|
| **Unary** | Client sends one message, server responds with one | Standard request/response |
| **Server streaming** | Client sends one message, server streams multiple | Real-time updates, large result sets |
| **Client streaming** | Client streams multiple messages, server responds once | File upload, aggregated data |
| **Bidirectional streaming** | Both sides stream simultaneously | Chat, real-time collaboration |

```protobuf
service OrderService {
  // Unary
  rpc GetOrder(GetOrderRequest) returns (Order);

  // Server streaming
  rpc WatchOrderStatus(WatchRequest) returns (stream OrderStatusUpdate);

  // Client streaming
  rpc UploadOrderBatch(stream Order) returns (BatchUploadResult);

  // Bidirectional streaming
  rpc Chat(stream ChatMessage) returns (stream ChatMessage);
}
```

### 7.3 Protobuf Evolution Rules

1. **Never change field numbers.** The field number is the identity on the wire.
2. **Never reuse field numbers.** If you remove field 5, do not assign 5 to a new field. Use `reserved`.
3. **Adding fields:** Safe. Old code ignores unknown fields.
4. **Removing fields:** Use `reserved` to prevent reuse.
5. **Renaming fields:** Safe (wire format uses numbers, not names).
6. **Changing types:** Unsafe in most cases. `int32 → int64` is safe (widening). `string → int32` is not.

```protobuf
message User {
  reserved 4, 8;              // field numbers that must not be reused
  reserved "old_field_name";  // names that must not be reused

  int32 id = 1;
  string name = 2;
  string email = 3;
  // field 4 was removed (previously "phone")
  string address = 5;
}
```

### 7.4 gRPC vs REST — Decision Matrix

| Factor | REST (JSON) | gRPC (Protobuf) |
|---|---|---|
| Payload size | Larger (text) | 3-10x smaller (binary) |
| Latency | Higher (text parsing) | Lower (binary parsing) |
| Browser support | Native | Requires gRPC-Web proxy |
| Streaming | Workarounds (SSE, WebSocket) | Native (4 patterns) |
| Code generation | Optional (OpenAPI) | Built-in (protoc) |
| Human readability | High (JSON) | Low (binary) |
| Tooling | curl, Postman, browser | grpcurl, Bloom, Evans |
| Best for | Public APIs, web clients | Internal microservice communication |

---

## 8. API Versioning Strategies

### 8.1 URL Path Versioning

```
GET /api/v1/users/123
GET /api/v2/users/123
```

**Pros:** Simple, visible, easy to route.
**Cons:** Multiple API versions in parallel, URL is not a version — it is a resource identity.

### 8.2 Header Versioning

```
GET /users/123
Accept: application/vnd.myapi.v2+json
```

Or custom header:

```
GET /users/123
X-API-Version: 2
```

**Pros:** Clean URLs, resource identity preserved.
**Cons:** Harder to test (need to set headers), less discoverable.

### 8.3 Query Parameter Versioning

```
GET /users/123?version=2
```

**Pros:** Easy to test in browser.
**Cons:** Pollutes query string, optional parameter can be forgotten.

### 8.4 No Explicit Versioning (Evolutionary)

Instead of versions, evolve the API with additive changes:
- Add new fields (never remove).
- Add new endpoints.
- Use feature flags or capability negotiation.

```json
// V1 response
{"id": 123, "name": "Alice"}

// V2 response (additive)
{"id": 123, "name": "Alice", "email": "alice@example.com"}

// Old clients ignore "email". No version bump needed.
```

**Pros:** No version management, simplest for clients.
**Cons:** Accumulates dead fields, harder to make structural changes.

### 8.5 Recommendation

1. **Internal APIs (microservices):** No explicit versioning. Use protobuf field numbers for evolution.
2. **Public APIs:** URL path versioning (`/v1/`, `/v2/`) for major breaking changes. Additive evolution within a version.
3. **Partner APIs:** Header versioning with long deprecation periods.

---

## 9. Backward Compatibility & Deprecation

### 9.1 What Is a Breaking Change?

| Change | Breaking? | Why |
|---|---|---|
| Add optional field to response | No | Clients ignore unknown fields |
| Add required field to request | **Yes** | Existing clients do not send it |
| Remove field from response | **Yes** | Clients may depend on it |
| Rename field | **Yes** | Clients reference old name |
| Change field type | **Yes** | Deserialization fails |
| Change URL path | **Yes** | Clients have hardcoded URLs |
| Add new endpoint | No | Clients do not call it |
| Add enum value | Maybe | Exhaustive match fails |
| Change error format | **Yes** | Error handling breaks |
| Tighten validation | **Yes** | Previously accepted requests rejected |
| Loosen validation | No | Accepts more inputs |

### 9.2 Robustness Principle (Postel's Law)

> Be conservative in what you send, be liberal in what you accept.

- **Send:** Include only documented fields in the exact documented format.
- **Accept:** Ignore unknown fields. Accept optional fields missing. Be forgiving of minor format variations.

### 9.3 Deprecation Policy Template

```
1. ANNOUNCE (Day 0)
   - Add @deprecated annotation to the field/endpoint.
   - Publish changelog entry.
   - Email affected API consumers.
   - Add Deprecation header to responses.

2. SUNSET HEADER (Day 0+)
   Sunset: Sat, 22 Nov 2026 00:00:00 GMT
   Deprecation: true
   Link: <https://docs.example.com/migration>; rel="deprecation"

3. GRACE PERIOD (6-12 months)
   - Old and new endpoints coexist.
   - Monitor usage of deprecated endpoints.
   - Reach out to consumers still using deprecated API.

4. WARNING LOG (Month 9)
   - Return warning header with each deprecated response.
   - Increase logging verbosity for deprecated calls.

5. RETIRE (Month 12)
   - Return 410 Gone for removed endpoints.
   - Keep documentation archived.
```

### 9.4 Migration Guide Structure

For each breaking change, provide:
1. **What changed:** exact before/after.
2. **Why:** business or technical justification.
3. **How to migrate:** code diff showing old → new.
4. **Timeline:** announcement date, sunset date.
5. **Support:** contact for migration help.

---

## 10. OpenAPI / Swagger

### 10.1 OpenAPI 3.1 Structure

```yaml
openapi: "3.1.0"
info:
  title: Order API
  version: "1.0.0"
  description: API for managing orders

servers:
  - url: https://api.example.com/v1
    description: Production

paths:
  /orders:
    get:
      operationId: listOrders
      summary: List orders with pagination
      parameters:
        - name: status
          in: query
          schema:
            $ref: "#/components/schemas/OrderStatus"
        - name: limit
          in: query
          schema:
            type: integer
            default: 25
            maximum: 100
        - name: after
          in: query
          description: Cursor for pagination
          schema:
            type: string
      responses:
        "200":
          description: Paginated list of orders
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/OrderListResponse"
        "429":
          description: Rate limit exceeded
          headers:
            Retry-After:
              schema:
                type: integer

    post:
      operationId: createOrder
      summary: Create a new order
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/CreateOrderRequest"
      responses:
        "201":
          description: Order created
          headers:
            Location:
              schema:
                type: string
                format: uri
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Order"
        "422":
          description: Validation error
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/ValidationError"

components:
  schemas:
    Order:
      type: object
      required: [id, status, total, createdAt]
      properties:
        id:
          type: string
          format: uuid
        status:
          $ref: "#/components/schemas/OrderStatus"
        total:
          type: number
          format: decimal
        createdAt:
          type: string
          format: date-time

    OrderStatus:
      type: string
      enum: [draft, submitted, shipped, delivered, cancelled]

    CreateOrderRequest:
      type: object
      required: [customerId, items]
      properties:
        customerId:
          type: string
          format: uuid
        items:
          type: array
          minItems: 1
          items:
            $ref: "#/components/schemas/OrderItemInput"

    OrderItemInput:
      type: object
      required: [productId, quantity]
      properties:
        productId:
          type: string
          format: uuid
        quantity:
          type: integer
          minimum: 1

    ValidationError:
      type: object
      properties:
        errors:
          type: array
          items:
            type: object
            properties:
              field:
                type: string
              message:
                type: string

  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

security:
  - bearerAuth: []
```

### 10.2 Code Generation from OpenAPI

```bash
# Generate TypeScript client
npx openapi-typescript-codegen --input openapi.yaml --output ./src/api

# Generate Python client
openapi-generator generate -i openapi.yaml -g python -o ./client

# Generate Go server stubs
oapi-codegen -package api openapi.yaml > api/server.gen.go

# Generate Java server stubs (Spring)
openapi-generator generate -i openapi.yaml -g spring -o ./server
```

### 10.3 Contract Testing

Use the OpenAPI spec as the contract between frontend and backend:

```python
# Validate response against OpenAPI schema
from openapi_core import validate_response

result = validate_response(
    request=request,
    response=response,
    spec=openapi_spec,
)
assert not result.errors, f"API response violates spec: {result.errors}"
```

---

## 11. API Security

### 11.1 Authentication Mechanisms

| Mechanism | Use Case | Pros | Cons |
|---|---|---|---|
| **API Key** | Simple M2M, public APIs | Easy to implement | No user identity, hard to rotate |
| **OAuth 2.0 + JWT** | User-facing APIs, delegated access | Standard, fine-grained scopes | Complex implementation |
| **mTLS** | Service-to-service | Strong identity, no secrets in headers | Certificate management overhead |
| **HMAC Signature** | Webhook verification, high-security | Tamper-proof | Clock sync, replay window |

### 11.2 JWT Best Practices

1. **Short-lived access tokens** (5-15 minutes). Refresh tokens for renewal.
2. **Validate signature** on every request. Never trust a JWT without verification.
3. **Check `exp`, `iss`, `aud` claims** — do not just validate the signature.
4. **Use asymmetric keys (RS256, ES256)** for public APIs. Symmetric (HS256) only for single-service scenarios.
5. **Never store sensitive data in the JWT payload** — it is base64 encoded, not encrypted.

### 11.3 API Key Rotation

```
1. Generate new key (key_v2)
2. Accept both key_v1 and key_v2
3. Notify consumers to switch to key_v2
4. Monitor: wait until key_v1 usage drops to 0
5. Revoke key_v1
```

---

## 12. Idempotency in APIs

Covered in depth in Module 2.2 (Distributed System Patterns, Section 8). Key API-specific points:

### 12.1 Which Endpoints Need Idempotency Keys?

| Method | Needs Key? | Why |
|---|---|---|
| GET | No | Already idempotent (safe, read-only) |
| PUT | No | Already idempotent (replaces resource) |
| DELETE | No | Already idempotent (deleting twice = 404 or 204) |
| POST | **Yes** | Creates new resource or triggers action |
| PATCH (relative) | **Yes** | `increment counter` is not idempotent |
| PATCH (absolute) | No | `set counter = 5` is idempotent |

### 12.2 Idempotency-Key Header Convention

```http
POST /payments
Idempotency-Key: pay_req_abc123
Content-Type: application/json

{"amount": 50.00, "currency": "USD", "customer_id": "cust_123"}
```

Server behavior:
- First call: execute, store result with key.
- Subsequent calls with same key: return stored result without re-executing.
- TTL: 24-48 hours (after which the key can be reused).

---

## 13. Error Handling

### 13.1 Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request contains invalid fields",
    "details": [
      {
        "field": "email",
        "message": "Must be a valid email address",
        "value": "not-an-email"
      },
      {
        "field": "quantity",
        "message": "Must be greater than 0",
        "value": -1
      }
    ],
    "request_id": "req_abc123",
    "documentation_url": "https://docs.example.com/errors/VALIDATION_ERROR"
  }
}
```

### 13.2 Error Code Strategy

Use machine-readable error codes, not just HTTP status codes:

```
HTTP 400 + code: INVALID_JSON         → malformed request body
HTTP 400 + code: MISSING_FIELD        → required field missing
HTTP 422 + code: VALIDATION_ERROR     → valid JSON, business rule violation
HTTP 409 + code: CONCURRENT_MODIFY    → optimistic locking conflict
HTTP 409 + code: DUPLICATE_RESOURCE   → resource already exists
HTTP 429 + code: RATE_LIMITED         → too many requests
HTTP 500 + code: INTERNAL_ERROR       → unhandled server error
```

### 13.3 Error Message Rules

1. **Never expose stack traces** in production responses.
2. **Never expose internal identifiers** (database table names, internal service names).
3. **Include `request_id`** for support ticket correlation.
4. **Provide actionable messages** — tell the client what to fix, not just what is wrong.
5. **Localize messages** if serving multiple locales (or use codes + client-side translation).

---

## 14. Common Pitfalls & Troubleshooting

### Pitfall 1: Chatty APIs

**Symptom:** Client makes 15 API calls to render one page.
**Fix:** Design aggregate endpoints. Use GraphQL. Use `?include=related_resource` for REST.

### Pitfall 2: Unbounded Lists

**Symptom:** `GET /orders` returns 10 million rows. Server OOM.
**Fix:** Always paginate. Set a default and maximum page size. Never allow `limit=0` (meaning "all").

### Pitfall 3: Breaking Changes Without Warning

**Symptom:** Client app crashes after a deploy. No deprecation notice was given.
**Fix:** Implement the deprecation policy (Section 9.3). Use contract tests in CI.

### Pitfall 4: GraphQL N+1

**Symptom:** A single query generates 100+ database queries.
**Fix:** Use DataLoader for every relationship resolver. Monitor query count per request.

### Pitfall 5: Rate Limiting Without Headers

**Symptom:** Clients cannot tell why they are getting 429 or when to retry.
**Fix:** Always return `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `Retry-After`.

### Pitfall 6: Inconsistent Error Formats

**Symptom:** Some endpoints return `{"error": "..."}`, others return `{"message": "..."}`, others return plain text.
**Fix:** Standardize on one error envelope. Enforce with middleware.

---

## 15. Q&A — Frequently Asked Questions

**Q1: REST or GraphQL?**
A: REST for simple CRUD, public APIs, CDN-cached content. GraphQL for complex client-driven queries, mobile apps with bandwidth constraints, rapid frontend iteration. gRPC for internal microservice communication.

**Q2: Should I use HATEOAS?**
A: Probably not fully. Include `self` links and pagination links. Full HATEOAS is rarely worth the investment for APIs consumed by known clients.

**Q3: How do I handle file uploads in REST?**
A: Use `multipart/form-data` for direct upload. For large files, use presigned URLs (upload directly to S3/GCS, then notify the API).

**Q4: How long should a deprecation period be?**
A: For public APIs: 6-12 months minimum. For internal APIs: 1-3 months. For partner APIs: negotiate with each partner.

**Q5: Should I use JSON:API, HAL, or plain JSON?**
A: Plain JSON with consistent conventions is usually sufficient. JSON:API and HAL add complexity that is rarely justified unless you are building a generic client.

**Q6: How do I version GraphQL?**
A: You do not. GraphQL is designed for evolution: add new fields, deprecate old fields. If you need a breaking change, add a new type or field.

**Q7: What is the maximum acceptable API response time?**
A: Depends on the client. Interactive web: < 200ms. Mobile: < 500ms. Batch/async: < 30s. Document these SLOs in your API documentation.

**Q8: How do I test API backward compatibility?**
A: Contract tests. Record the old response schema. After changes, validate that the old schema still matches (new fields are ignored, existing fields are unchanged).

---

## 16. Hands-On Exercises

### Exercise 1: Design a REST API (Beginner)

Design a REST API for a library management system.

**Requirements:**
- Resources: Books, Authors, Members, Loans.
- Implement CRUD for each resource.
- Implement cursor-based pagination for listing endpoints.
- Implement filtering: `GET /books?author_id=123&available=true`.
- Return proper status codes and error format.
- Write an OpenAPI 3.1 spec.

### Exercise 2: GraphQL Schema Design (Intermediate)

Design a GraphQL schema for an e-commerce storefront.

**Requirements:**
- Types: Product, Category, Cart, CartItem, User, Order.
- Implement the Connection pattern for paginated lists.
- Implement mutations: addToCart, removeFromCart, checkout.
- Use DataLoader for all relationship resolvers.
- Implement query complexity limiting (max cost: 1000 points).

### Exercise 3: API Versioning Strategy (Intermediate)

You have a public REST API at v1. You need to make a breaking change to the `/users` response (splitting `name` into `firstName` and `lastName`).

**Requirements:**
- Design the migration path: v1 (old) → v2 (new).
- Both versions must work simultaneously for 6 months.
- Write the deprecation headers for v1 responses.
- Write a migration guide for consumers.
- Implement contract tests that verify v1 still works.

### Exercise 4: Rate Limiter Implementation (Intermediate)

Build a distributed rate limiter using Redis.

**Requirements:**
- Implement sliding window counter algorithm.
- Support per-API-key rate limits.
- Return proper rate limit headers.
- Handle Redis unavailability (fail open or fail closed?).
- Write tests for: under limit, at limit, over limit, Redis down.

### Exercise 5: gRPC Service (Advanced)

Build a gRPC service with all four communication patterns.

**Requirements:**
- Define a `.proto` file for an order management service.
- Implement unary: `GetOrder`, `CreateOrder`.
- Implement server streaming: `WatchOrderStatus` (client subscribes to status changes).
- Implement client streaming: `UploadOrders` (batch upload).
- Implement bidirectional streaming: `OrderChat` (support chat attached to an order).
- Write integration tests using grpcurl.

---

## 17. References

1. Richardson, L. "Richardson Maturity Model" (2008). https://martinfowler.com/articles/richardsonMaturityModel.html
2. Fielding, R. "Architectural Styles and the Design of Network-based Software Architectures" (2000). — REST dissertation.
3. GraphQL Foundation. "GraphQL Specification." https://spec.graphql.org/
4. gRPC Project. "gRPC Documentation." https://grpc.io/docs/
5. OpenAPI Initiative. "OpenAPI Specification 3.1." https://spec.openapis.org/oas/v3.1.0
6. Stripe API Reference. https://stripe.com/docs/api — Best-in-class API design example.
7. RFC 6585: Additional HTTP Status Codes (429 Too Many Requests).
8. RFC 7807: Problem Details for HTTP APIs.
9. RFC 8288: Web Linking (Link header for deprecation).
10. Relay GraphQL Cursor Connections Specification. https://relay.dev/graphql/connections.htm
11. Google. "API Design Guide." https://cloud.google.com/apis/design

---

## Exercises

### Exercise 1: Design a RESTful Resource API with Versioning (Intermediate)

Design a public REST API for a task management system that supports two concurrent versions.

**Requirements:**
- Resources: Project, Task, User, Comment.
- Version 1 returns `name` as a single string on User; version 2 splits it into `firstName` and `lastName`.
- Both versions must be served simultaneously from the same codebase.
- Choose a versioning strategy (URL path, header, or media type) and justify your decision.
- Write deprecation headers (`Deprecation`, `Sunset`, `Link`) for v1 responses per RFC 8594.
- Provide an OpenAPI 3.1 spec for both versions and a consumer migration guide.

### Exercise 2: GraphQL Schema with Relay Pagination (Intermediate)

Design a GraphQL schema for an e-commerce catalog with efficient pagination and cost control.

**Requirements:**
- Types: Product, Category, Review, User.
- Implement the Relay Connection specification for paginated lists (`edges`, `node`, `cursor`, `pageInfo`).
- Implement mutations: `addReview`, `updateProduct`, `deleteProduct`.
- Add query complexity analysis: assign costs to each field and enforce a maximum query cost of 1000 points.
- Use DataLoader for all relationship resolvers to prevent N+1 queries.
- Write 3 example queries with their expected complexity scores.

### Exercise 3: gRPC Service with All Four Patterns (Advanced)

Build a gRPC order-tracking service that uses all four communication patterns.

**Requirements:**
- Define a `.proto` file for an `OrderTrackingService`.
- Unary: `GetOrderStatus(OrderId) -> OrderStatus`.
- Server streaming: `SubscribeToUpdates(OrderId) -> stream StatusUpdate` (push updates as the order progresses).
- Client streaming: `BulkCreateOrders(stream CreateOrderRequest) -> BulkCreateResponse`.
- Bidirectional streaming: `LiveSupport(stream ChatMessage) -> stream ChatMessage` (real-time support chat).
- Implement deadline propagation and proper error codes (`NOT_FOUND`, `DEADLINE_EXCEEDED`, `RESOURCE_EXHAUSTED`).
- Write integration tests using `grpcurl` or a generated client.

### Exercise 4: API Contract Testing with OpenAPI (Intermediate)

Set up a contract testing pipeline that prevents backward-incompatible changes.

**Requirements:**
- Start with an OpenAPI 3.1 spec for a payments API (`POST /payments`, `GET /payments/{id}`, `GET /payments?status=`).
- Introduce a breaking change (e.g., rename a required field) and a non-breaking change (add an optional field).
- Use a schema diff tool (e.g., `oasdiff`, `openapi-diff`) to detect the breaking change automatically.
- Configure the diff tool as a CI gate that fails the build on breaking changes.
- Document the full deprecation lifecycle: announce → grace period (with `Sunset` header) → removal.

### Exercise 5: Rate Limiter Design and Implementation (Intermediate)

Design and implement a distributed rate limiter for a public API.

**Requirements:**
- Implement the sliding window counter algorithm using Redis.
- Support per-API-key limits with configurable tiers (free: 100 req/min, pro: 1000 req/min).
- Return standard rate-limit headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`, `Retry-After`.
- Handle Redis unavailability gracefully (decide and justify: fail-open or fail-closed).
- Write tests covering: under limit, at limit, over limit, window rollover, Redis down.

---

## Readings and References

### Official Documentation (retrieved: 2026-05-29)

- OpenAPI Specification 3.1.0 — https://spec.openapis.org/oas/v3.1.0.html
- OpenAPI Specification 3.2.0 — https://spec.openapis.org/oas/v3.2.0.html
- GraphQL Specification — https://spec.graphql.org/
- Relay Cursor Connections Specification — https://relay.dev/graphql/connections.htm
- gRPC Documentation — https://grpc.io/docs/
- Google API Design Guide — https://cloud.google.com/apis/design
- Stripe API Reference (best-in-class design example) — https://stripe.com/docs/api
- Fern API Design Best Practices Guide (2026) — https://buildwithfern.com/post/api-design-best-practices-guide

### Books

- Kleppmann, M. *Designing Data-Intensive Applications* (O'Reilly, 2017). Chapters on encoding, evolution, and data integration.
- Richardson, C. *Microservices Patterns* (Manning, 2018). Chapter 3 (inter-process communication).
- Lauret, A. *The Design of Web APIs* (Manning, 2019). End-to-end API design methodology.
- Sturgeon, P. *Build APIs You Won't Hate*, 2nd edition (Leanpub, 2024). Practical REST design.

### RFCs and Standards

- Fielding, R. "Architectural Styles and the Design of Network-based Software Architectures." Doctoral dissertation, UC Irvine (2000). https://ics.uci.edu/~fielding/pubs/dissertation/top.htm
- RFC 6585 — Additional HTTP Status Codes (429 Too Many Requests).
- RFC 7807 / RFC 9457 — Problem Details for HTTP APIs.
- RFC 8288 — Web Linking (Link header for deprecation and pagination).
- RFC 8594 — The Sunset HTTP Header Field.
- Richardson, L. "Richardson Maturity Model" (2008). https://martinfowler.com/articles/richardsonMaturityModel.html

---

## Cross-References

| Topic | Module | File |
|---|---|---|
| Distributed system patterns (saga, outbox) for service integration | 2.2 | `02_Distributed_System_Patterns.md` |
| High-performance system design (latency budgets for API calls) | 2.2b | `02_b_High_Performance_System_Design.md` |
| Code-level architecture (ports & adapters for API layers) | 2.1 | `01_Code_Level_Architecture.md` |
| SOLID principles applied to API controller design | 2.3 | `03_Design_Principles_SOLID_etc.md` |
| CAP / PACELC trade-offs affecting API consistency guarantees | 2.4 | `04_System_Design_CAP_PACELC.md` |
| Database query patterns underlying API pagination and filtering | — | `03_Database_Engineering/` |

---

## Glossary

| Term | Definition |
|---|---|
| **REST** | Representational State Transfer — an architectural style for networked applications defined by Fielding (2000), emphasizing stateless interactions, uniform interfaces, and resource identification via URIs. |
| **Richardson Maturity Model** | A four-level classification (0-3) for REST API maturity, from plain RPC tunneling through resource URIs, HTTP verbs, and finally HATEOAS. |
| **HATEOAS** | Hypermedia As The Engine Of Application State — the principle that API responses include links (hypermedia controls) that tell the client what actions are available next. |
| **GraphQL** | A query language and runtime for APIs that lets clients request exactly the data they need, defined by a strongly-typed schema. |
| **gRPC** | A high-performance RPC framework built on HTTP/2 and Protocol Buffers, supporting unary, server-streaming, client-streaming, and bidirectional-streaming communication. |
| **Protocol Buffers (Protobuf)** | A language-neutral binary serialization format used by gRPC; `.proto` files define the schema and generate typed client/server code. |
| **OpenAPI** | A specification standard (formerly Swagger) for describing RESTful APIs in a machine-readable format (YAML/JSON), enabling codegen, documentation, and contract testing. |
| **Idempotency Key** | A client-generated unique token sent with a request so the server can detect retries and return the original response instead of processing the request again. |
| **Rate Limiting** | A technique that restricts the number of API requests a client can make within a time window, protecting the server from abuse and ensuring fair usage. |
| **Backward Compatibility** | The property of an API change that allows existing clients to continue functioning without modification (e.g., adding optional fields, new endpoints). |
| **Deprecation** | The process of marking an API version or field as scheduled for removal, with advance notice, a grace period, and a sunset date. |
| **Sunset Header** | An HTTP response header (RFC 8594) that communicates the date after which an API version or endpoint will no longer be available. |
| **Contract Testing** | Automated tests that verify an API implementation conforms to its published specification (e.g., OpenAPI schema), catching breaking changes before deployment. |
| **Content Negotiation** | The HTTP mechanism (via `Accept` and `Content-Type` headers) by which client and server agree on the representation format and version of a resource. |

---

*End of Module 2.2c*
