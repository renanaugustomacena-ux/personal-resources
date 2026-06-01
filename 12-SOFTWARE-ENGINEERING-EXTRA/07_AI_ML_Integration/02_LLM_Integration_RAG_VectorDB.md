---
corso: "SWE Masterclass"
fase: "7 — AI & ML Integration"
modulo: "07.2"
titolo: "LLM Integration — RAG, Vector DBs, Prompt Engineering"
versione: "LangChain 1.3, Qdrant 1.13, pgvector 0.8, Pinecone Serverless, Weaviate 1.28, Cohere Embed v4"
livello: "Advanced"
prerequisiti:
  - "Linear algebra fundamentals (vectors, dot product, cosine similarity)"
  - "REST API design and HTTP streaming (SSE)"
  - "Python 3.11+ with async/await"
  - "SQL and relational database fundamentals (for pgvector)"
  - "Module 07.1 — AI Engineering Patterns"
obiettivi:
  - "Implement end-to-end RAG pipelines: chunking, embedding, hybrid retrieval, reranking, and grounded generation"
  - "Select and configure vector databases (Pinecone, Qdrant, Weaviate, pgvector) based on scale, latency, and operational constraints"
  - "Apply advanced chunking strategies (semantic, document-aware, late chunking) and measure retrieval quality with Recall@K"
  - "Design hybrid search systems combining BM25 keyword search with dense vector retrieval using Reciprocal Rank Fusion"
  - "Evaluate RAG pipelines using RAGAS metrics (faithfulness, answer relevance, context precision/recall) with automated CI integration"
tag: [rag, vector-database, embedding, chunking, hybrid-search, reranking, prompt-engineering, prompt-caching, langchain, llamaindex]
---

# Module 7.2: LLM Integration — RAG, Vector DBs, Prompt Engineering

> **Learning Objectives**
>
> After completing this module, you will be able to:
>
> 1. Build a production RAG pipeline from source documents through chunking, embedding, vector storage, hybrid retrieval, reranking, and grounded generation.
> 2. Compare ANN index strategies (HNSW, IVFFlat, DiskANN) and tune parameters (`m`, `ef_construction`, `ef_search`, `probes`) to meet Recall@10 >= 0.95 SLOs.
> 3. Implement hybrid search (BM25 + dense) with Reciprocal Rank Fusion and cross-encoder reranking to maximize retrieval precision.
> 4. Apply prompt caching, context window budgeting, and model-pinning practices that reduce API costs while preserving deterministic behavior.
> 5. Evaluate retrieval and generation quality using RAGAS metrics and guardrail patterns (PII redaction, output validation, faithfulness checks).

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

---

## 8. Exercises

### Exercise 1: Chunking Strategy Comparison

1. Take a 50-page technical document (e.g., an RFC or product manual).
2. Chunk it with four strategies: fixed 512-token windows, recursive character split, semantic chunking (sentence-embedding + cosine threshold), and document-aware (split by headings).
3. Embed all chunk sets with the same model (e.g., `text-embedding-3-large` at 1024d).
4. Run 20 representative queries against each chunk set. Measure Recall@10 and MRR (Mean Reciprocal Rank).
5. Document which strategy wins and where each fails (tables, code blocks, cross-section references).

### Exercise 2: Vector Database Benchmarking

1. Load 100K embedded chunks into three vector databases: pgvector (HNSW index), Qdrant, and an in-memory FAISS index.
2. Tune HNSW parameters: vary `m` (8, 16, 32) and `ef_search` (64, 128, 256).
3. Measure for each configuration: Recall@10, p50/p99 query latency, index build time, and memory footprint.
4. Plot the recall-vs-latency Pareto frontier. Identify the configuration meeting Recall@10 >= 0.95 with lowest p99 latency.
5. Write a decision matrix recommending which database fits which operational profile (single-node, managed cloud, billion-scale).

### Exercise 3: Hybrid Search with Reranking Pipeline

1. Implement BM25 keyword search using Elasticsearch or a BM25 library alongside dense vector search.
2. Merge results using Reciprocal Rank Fusion (RRF) with `k=60`.
3. Add a cross-encoder reranker (e.g., `BAAI/bge-reranker-v2-m3`) to rescore the top-50 merged results down to top-5.
4. Compare retrieval quality (Recall@5, Precision@5) for: vector-only, BM25-only, hybrid without reranking, hybrid with reranking.
5. Measure end-to-end latency for each configuration. Profile where time is spent (embedding, retrieval, reranking).

### Exercise 4: Prompt Caching Cost Analysis

1. Build a chatbot with a 5000-token system prompt and 10 tool definitions.
2. Implement Anthropic prompt caching with `cache_control` markers on the system prompt and tools.
3. Simulate 100 conversations (5 turns each). Log `cache_creation_input_tokens` and `cache_read_input_tokens` per call.
4. Calculate total cost with and without caching. Compute the break-even point (number of calls before caching pays for the cache-write premium).
5. Experiment with cache TTL strategies: measure cache hit rate under bursty vs. steady traffic patterns.

### Exercise 5: End-to-End RAG Evaluation with RAGAS

1. Build a RAG pipeline over a documentation corpus (at least 200 pages).
2. Create a golden dataset of 50 question-answer pairs with annotated relevant source passages.
3. Evaluate with four RAGAS metrics: faithfulness, answer relevance, context precision, context recall.
4. Identify the weakest metric. Improve it by changing one pipeline parameter (chunk size, top-K, reranker threshold).
5. Re-evaluate and document the before/after scores. Set up the eval as a pytest suite that fails if any metric drops below a threshold.

---

## 9. Readings and References

### Papers

| Paper | Authors | Year | Link | Retrieved |
|---|---|---|---|---|
| Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks | Lewis, P. et al. | 2020 | https://arxiv.org/abs/2005.11401 | 2026-05-29 |
| Attention Is All You Need | Vaswani, A. et al. | 2017 | https://arxiv.org/abs/1706.03762 | 2026-05-29 |
| RAGAS: Automated Evaluation of Retrieval Augmented Generation | Es, S. et al. | 2023 | https://arxiv.org/abs/2309.15217 | 2026-05-29 |
| Efficient and Robust Approximate Nearest Neighbor Search Using HNSW Graphs | Malkov, Y. & Yashunin, D. | 2018 | https://arxiv.org/abs/1603.09320 | 2026-05-29 |
| Matryoshka Representation Learning | Kusupati, A. et al. | 2022 | https://arxiv.org/abs/2205.13147 | 2026-05-29 |

### Books

- Tunstall, L., von Werra, L. & Wolf, T. *Natural Language Processing with Transformers* (Revised Edition). O'Reilly, 2022.
- Auffarth, B. *Generative AI with LangChain*. Packt, 2023.
- Dobilas, A. *RAG-Driven Generative AI*. Packt, 2024.

### Documentation and Guides (retrieved: 2026-05-29)

| Resource | URL |
|---|---|
| Pinecone RAG Guide | https://www.pinecone.io/learn/retrieval-augmented-generation/ |
| Weaviate Chunking Strategies | https://weaviate.io/blog/chunking-strategies-for-rag |
| Qdrant Documentation | https://qdrant.tech/documentation/ |
| pgvector GitHub | https://github.com/pgvector/pgvector |
| LangChain Text Splitters | https://python.langchain.com/docs/how_to/#text-splitters |
| RAGAS Documentation | https://docs.ragas.io/ |
| Anthropic Prompt Caching Guide | https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching |
| Cohere Embed v4 Documentation | https://docs.cohere.com/docs/embed-api |
| Databricks Chunking Strategies Guide | https://community.databricks.com/t5/technical-blog/the-ultimate-guide-to-chunking-strategies-for-rag-applications/ba-p/113089 |

---

## 10. Cross-References

| Module | Relevance to LLM Integration & RAG |
|---|---|
| [01_AI_Engineering_Patterns.md](01_AI_Engineering_Patterns.md) | Foundational AI engineering stack, tool-use loops, evaluation harnesses, and guardrail patterns that frame the RAG pipeline in context |
| [03_MLOps_Pipelines.md](03_MLOps_Pipelines.md) | Model serving infrastructure (Triton, vLLM) for self-hosted embedding and reranker models; pipeline orchestration for batch embedding jobs |
| [../01_Foundations/](../01_Foundations/) | Algorithm fundamentals: graph traversal (HNSW), hashing, sorting, and complexity analysis underpinning ANN index operations |
| [../02_Architecture_Design/](../02_Architecture_Design/) | System design patterns for distributed retrieval: caching layers, load balancing, and eventual consistency in vector store replication |
| [../03_Database_Engineering/](../03_Database_Engineering/) | PostgreSQL internals (indexing, query planning, ACID) directly applicable to pgvector HNSW/IVFFlat index tuning and hybrid SQL+vector queries |
| [../05_DevOps_Cloud_Native/](../05_DevOps_Cloud_Native/) | Kubernetes deployment for self-hosted vector databases (Qdrant, Weaviate, Milvus), GPU node scheduling for embedding model serving |

---

## 11. Glossary

| Term | Definition |
|---|---|
| **RAG** | Retrieval-Augmented Generation — architecture combining document retrieval with LLM generation to produce grounded, factual answers from a knowledge base |
| **HNSW** | Hierarchical Navigable Small World — graph-based approximate nearest neighbor index offering high recall and low latency at the cost of RAM |
| **ANN** | Approximate Nearest Neighbor — family of algorithms trading exact accuracy for orders-of-magnitude speed improvement in high-dimensional similarity search |
| **Embedding** | Dense fixed-dimensional vector representation of text (or other data) produced by a neural encoder, used for similarity search |
| **Matryoshka Representation Learning** | Training technique where leading prefixes of an embedding vector are themselves usable embeddings, enabling post-hoc dimension truncation |
| **BM25** | Best Matching 25 — probabilistic sparse retrieval algorithm based on term frequency and inverse document frequency, effective for exact keyword matching |
| **Reciprocal Rank Fusion (RRF)** | Score-agnostic result merging formula `1/(k + rank)` that combines ranked lists from heterogeneous retrieval systems without score normalization |
| **Cross-Encoder Reranker** | Model that scores a `(query, document)` pair jointly with full cross-attention, providing higher precision than bi-encoder retrieval at O(K) cost |
| **Late Chunking** | Embedding a full document with a long-context model, then mean-pooling over chunk spans so each chunk vector retains global document context |
| **Semantic Chunking** | Splitting text by embedding sentences individually and grouping by cosine similarity threshold, producing semantically coherent chunks |
| **Prompt Caching** | Caching repeated prompt prefixes (system prompt, tools) across API calls; cached tokens cost ~10% of normal input tokens on Anthropic |
| **Context Window** | Maximum number of tokens an LLM can process in a single request, including system prompt, conversation history, retrieved context, and output |
| **Faithfulness** | RAGAS metric measuring whether every claim in the generated answer is grounded in (supported by) the retrieved context passages |
| **HyDE** | Hypothetical Document Embeddings — technique of generating a hypothetical answer and embedding it instead of the raw query for improved retrieval recall |
| **pgvector** | PostgreSQL extension adding vector similarity search with HNSW and IVFFlat indexes, enabling vector search alongside ACID transactions and SQL joins |
