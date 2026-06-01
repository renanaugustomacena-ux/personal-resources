# Phase 7: AI/ML for Software Engineers — Syllabus

> **Last updated:** 2026-05-29

You don't need to build models, but you need to know how to use them.

## Module 7.1: AI Engineering Patterns

**Goal:** Build production-grade AI systems with guardrails.

| File | Focus |
|---|---|
| [01_AI_Engineering_Patterns.md](01_AI_Engineering_Patterns.md) | Evaluation harnesses, prompt engineering, agent architectures, structured output, guardrails, cost optimization |

*   **Prompt Engineering:** Zero-Shot, Few-Shot, Chain of Thought, ReAct.
*   **Agent Architectures:** Tool use, planning loops, multi-agent orchestration.
*   **Evaluation:** Offline evals, LLM-as-judge, human-in-the-loop, regression testing.

## Module 7.2: LLM Integration — RAG & Vector Databases

**Goal:** Ground LLM responses in your data.

| File | Focus |
|---|---|
| [02_LLM_Integration_RAG_VectorDB.md](02_LLM_Integration_RAG_VectorDB.md) | RAG pipeline, chunking strategies, HNSW/IVF, reranking, hybrid search, pgvector/Qdrant/Weaviate |

*   **RAG (Retrieval Augmented Generation):** Fetch relevant context → inject into prompt → generate.
*   **Embeddings:** Text/image → float[] vectors. Cosine similarity vs Euclidean.
*   **Vector Search:** HNSW (graph-based), IVF (clustering), hybrid (keyword + semantic).

## Module 7.3: MLOps Pipelines

**Goal:** Ship models to production with reproducibility and monitoring.

| File | Focus |
|---|---|
| [03_MLOps_Pipelines.md](03_MLOps_Pipelines.md) | Feature stores, model registries, training pipelines, drift detection, A/B testing, Kubeflow/MLflow/Feast |

*   **Feature Engineering:** Feature stores (Feast), offline vs online serving.
*   **Training Pipelines:** Kubeflow, MLflow, experiment tracking, hyperparameter tuning.
*   **Model Serving:** vLLM, TensorRT, model monitoring, data/concept drift detection.
