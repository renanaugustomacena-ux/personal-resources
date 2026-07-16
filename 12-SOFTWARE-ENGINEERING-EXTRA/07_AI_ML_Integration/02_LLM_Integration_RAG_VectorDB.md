# Module 7.2: LLM Integration — RAG, Vector DBs, Prompt Engineering

> **Module 07.2** · **Last updated:** 2026-04-27

## Guiding ideas
1. **HNSW (Hierarchical Navigable Small World) standard ANN index.**
2. **Quantization: PQ, scalar, binary; balance accuracy/memory.**
3. **Vector DB: Pinecone, Weaviate, Qdrant, pgvector.**
4. **RAG: retrieval + generation; chunk strategy critical.**
5. **LangChain / LlamaIndex frameworks; mature 2024+.**


**Date:** 2026-04-22
**Status:** Completed

## 1. LLM API Call Patterns

### 1.1 Chat Completion
*   Stateless: client resends entire `messages[]` each call. Server has no session memory.
*   Roles: `system` (instructions), `user`, `assistant`, `tool`.
*   **Streaming:** SSE (`text/event-stream`). Reduces TTFT (time-to-first-token) from seconds to ~200ms. Mandatory for chat UX.

### 1.2 Function / Tool Calling
*   Pass `tools=[{name, description, parameters: JSONSchema}]`.
*   Model returns `tool_use` block with structured args. Client executes, returns `tool_result` with same `tool_use_id`. Loop until `stop_reason="end_turn"`.
*   **Parallel tool use:** Modern models emit multiple tool calls in one assistant turn — execute concurrently.

### 1.3 Structured Output
*   **JSON mode:** Model constrained to emit valid JSON.
*   **JSON Schema mode (constrained decoding):** Logits masked at sample time so only schema-conforming tokens are valid. Zero parse failures, enforced by the sampler not the prompt.
*   Anthropic uses tool-call coercion; OpenAI uses `response_format={type:"json_schema", strict:true}`.

## 2. Prompt Engineering

### 2.1 Message Hierarchy
*   **System:** Role, constraints, output format, refusal policy. Stable across the session.
*   **User:** Per-turn input.
*   **Few-shot:** Pairs of `(user, assistant)` exemplars before the real query. ~3-5 shots is the sweet spot.
*   **Chain-of-thought (CoT):** "Think step by step before answering." Forces reasoning tokens. Modern reasoning models (o3, Claude extended thinking) do this internally.
*   **ReAct loop:** Thought → Action (tool call) → Observation → Thought → ... → Answer. Standard agentic pattern.

### 2.2 Prompt Caching
*   Anthropic: `cache_control: {type:"ephemeral"}` markers, 5-min default TTL, 1-hour beta. Cached tokens cost ~10% of normal input.
*   OpenAI: automatic for prompts ≥1024 tokens, prefix-matched.
*   **Pin exact model IDs** (e.g. `claude-opus-4-7`, `claude-sonnet-4-6`) in production code — bare aliases like `claude-opus-latest` invalidate cache and break determinism.

### 2.3 Context Window Budgets
| Model | Context |
|---|---|
| Anthropic Claude Opus 4.x | 200k |
| Anthropic Claude Sonnet 4.6 (1M beta) | 1M |
| OpenAI GPT-4o / 4.1 | 128k–1M |
| Google Gemini 2.5 Pro | 2M |

*   Token counting: `tiktoken` (OpenAI), `anthropic.count_tokens()`. Budget = system + tools + history + retrieved docs + headroom for output.

## 3. RAG Architecture

### 3.1 Pipeline
1.  **Chunk:** Split source docs.
2.  **Embed:** Encode chunks → dense vectors.
3.  **Store:** Upsert to vector DB with metadata (doc_id, page, ACL).
4.  **Retrieve:** Embed query, top-K nearest neighbors. Add **hybrid** keyword search.
5.  **Rerank:** Cross-encoder rescoring of top-N candidates.
6.  **Prompt:** Inject reranked context into the system/user message, generate.

### 3.2 Embedding Models
*   **OpenAI text-embedding-3-large:** 3072d, supports Matryoshka truncation (256/512/1024d) with graceful quality degradation.
*   **Cohere embed-v3 / embed-v4:** Multilingual, document/query-aware (`input_type` flag).
*   **Open weights:** BAAI/bge-m3 (dense+sparse+colbert in one), intfloat/e5-mistral-7b (decoder-based, top-of-MTEB), nomic-embed-text-v2.
*   **Matryoshka Representation Learning (MRL):** Train so leading prefix of vector is itself a usable embedding. Enables storage/latency tuning post-hoc.

### 3.3 Chunking Strategies
*   **Fixed:** Naive token windows (e.g. 512 tokens, 50 overlap). Cheap, brittle on structured docs.
*   **Recursive character split:** Split on `\n\n` → `\n` → ` ` → char until under size. LangChain default.
*   **Semantic:** Embed sentence-by-sentence, group by cosine similarity threshold. Higher quality, ~10x slower.
*   **Late chunking (Jina, 2024):** Embed the full document with long-context model, then mean-pool over chunk spans. Each chunk vector retains global context.

## 4. Vector Databases

| DB | Hosting | Index | Notes |
|---|---|---|---|
| Pinecone | Managed only | proprietary | Serverless, pay-per-read |
| Weaviate | OSS + cloud | HNSW | Built-in modules, hybrid native |
| Qdrant | OSS + cloud | HNSW | Rust, strong filtering, payload index |
| Milvus / Zilliz | OSS + cloud | HNSW, IVF, DiskANN | Billion-scale, GPU index |
| pgvector | Postgres ext | HNSW, IVFFlat | Single-DB ops, ACID, joins |

### 4.1 Index Trade-offs
*   **HNSW:** Graph-based. High recall, low latency, large RAM footprint. Tune `m`, `ef_construction`, `ef_search`.
*   **IVFFlat:** Cluster + flat search inside cluster. Lower memory, lower recall. Tune `lists` (clusters) and `probes`.
*   **DiskANN / Vamana:** Disk-resident graph for billion-scale on commodity hardware.
*   *Recall vs latency:* Always measure. Recall@10 ≥ 0.95 is a typical SLO; trade `ef_search` higher for recall at the cost of p99 latency.

## 5. Hybrid Search & Reranking

### 5.1 Hybrid (BM25 + Dense)
*   BM25 catches exact tokens (product codes, names). Dense catches paraphrase.
*   **Reciprocal Rank Fusion (RRF):** `score(d) = Σ 1/(k + rank_i(d))`, `k=60` typical. Rank-only, no score normalization needed. Robust default.

### 5.2 Reranking
*   Top-K (50–100) from retrieval → cross-encoder scoring → top-N (5–10) into prompt.
*   **Cohere Rerank 3:** Hosted, multilingual, 4096-token windows.
*   **BAAI/bge-reranker-v2-m3:** Open, GPU-served via TEI/Triton.
*   Cross-encoders see (query, doc) jointly → much higher precision than bi-encoder retrieval, but O(K) forward passes per query — that's why you rerank only top-K.

## 6. Frameworks

*   **LangChain:** Broad ecosystem, fast iteration, but abstraction churn and leaky interfaces. Fine for prototypes; many teams rip it out for production.
*   **LlamaIndex:** RAG-first, strong ingestion connectors and query engines.
*   **Haystack (deepset):** Pipeline DAG, mature for enterprise search.
*   **No framework:** Direct SDK + ~300 lines is often more maintainable. Pick based on team familiarity, not hype.

## 7. Evaluation & Guardrails

### 7.1 RAGAS Metrics
*   **Faithfulness:** Are answer claims grounded in retrieved context?
*   **Answer Relevance:** Does the answer address the query?
*   **Context Precision / Recall:** Are retrieved chunks relevant / sufficient?
*   LLM-as-judge backs these — pin the judge model and version, otherwise scores drift.

### 7.2 Guardrails
*   **Output validation:** JSON schema, regex, allow-list of values, refusal classifier.
*   **PII redaction before logging:** Run Presidio / regex over prompts and completions before any log sink. Never persist tokens, secrets, or raw PII alongside traces.
*   **Treat model output as untrusted:** Sandbox tool calls, validate every argument the model passes — same threat model as user input.
