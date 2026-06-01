---
corso: "SWE Masterclass"
fase: "7 — AI & ML Integration"
modulo: "07.3"
titolo: "MLOps — Training, Serving, Monitoring"
versione: "PyTorch 2.12, MLflow 3.12, Kubeflow Pipelines 2.16, Feast 0.41, vLLM 0.8, Optuna 4.x"
livello: "Advanced"
prerequisiti:
  - "Container fundamentals (Docker, OCI images)"
  - "Kubernetes concepts (pods, services, CRDs, operators)"
  - "Python 3.11+ and basic NumPy/PyTorch tensor operations"
  - "CI/CD pipeline design (GitHub Actions or GitLab CI)"
  - "Module 07.1 — AI Engineering Patterns"
obiettivi:
  - "Design reproducible ML pipelines with versioned data, code, environment, and hyperparameters linked by lineage"
  - "Implement feature stores (Feast) providing consistent feature definitions across offline training and online serving with point-in-time correctness"
  - "Deploy and manage model registries (MLflow) with promotion gates, evaluation thresholds, and SemVer-style versioning"
  - "Configure distributed training strategies (DDP, FSDP, DeepSpeed ZeRO) and quantization (GPTQ, AWQ) for memory-efficient inference"
  - "Build drift detection and monitoring systems using statistical tests (KS, PSI) integrated with automated retraining triggers"
tag: [mlops, model-serving, feature-store, experiment-tracking, distributed-training, quantization, drift-detection, ci-cd-ml, model-registry, pipeline-orchestration]
---

# Module 7.3: MLOps — Training, Serving, Monitoring

> **Learning Objectives**
>
> After completing this module, you will be able to:
>
> 1. Design end-to-end ML pipelines with full reproducibility: pinned data hashes, code commits, Docker digests, and hyperparameters linked by artifact lineage.
> 2. Implement feature stores (Feast/Tecton) with point-in-time correct joins, online/offline consistency, and feature freshness SLOs.
> 3. Operate model registries (MLflow) with promotion flows (`dev → staging → production`), evaluation gates, and automated CI/CD integration.
> 4. Select and configure distributed training strategies (DDP, FSDP, DeepSpeed ZeRO Stages 1-3) and post-training quantization (GPTQ, AWQ, bitsandbytes).
> 5. Deploy model serving infrastructure (Triton, vLLM, KServe) with drift detection (KS, PSI), prediction logging, and automated retraining triggers.

> **Module 07.3** · **Last updated:** 2026-04-27

## Guiding ideas
1. **Model versioning + reproducibility (MLflow, DVC).**
2. **Feature store: training + serving consistency (Feast, Tecton).**
3. **Drift detection: data + concept drift.**
4. **A/B test deployment for new models.**


**Date:** 2026-04-22
**Status:** Completed

## 1. ML Lifecycle

```
data → feature → train → eval → register → deploy → monitor → retrain
```

Each stage is a versioned artifact with lineage back to the previous stage. Reproducibility = pinned data hash + pinned code commit + pinned env (Docker digest) + pinned hyperparameters.

## 2. Experiment Tracking

*   **MLflow:** OSS, four pillars (Tracking, Projects, Models, Registry). `mlflow.log_param`, `log_metric`, `log_artifact`. Backend store = Postgres; artifact store = S3.
*   **Weights & Biases:** SaaS-first, best-in-class UI for runs/sweeps, system metrics (GPU util) auto-logged.
*   **Neptune:** Lighter, metadata-store oriented.
*   **What to log:** params (hyperparams, dataset hash), metrics (per-step + final), artifacts (model file, confusion matrix, sample predictions), lineage (parent run, dataset version, code SHA), env (`pip freeze`, CUDA version).

## 3. Feature Stores

*   **Why:** Same feature definition for training (offline batch) and inference (online low-latency). Eliminates train-serve skew.
*   **Feast (OSS):** Lightweight, BYO storage. Offline = BigQuery/Snowflake/Parquet; online = Redis/DynamoDB.
*   **Tecton:** Managed, Spark-native, transformation engine included.
*   **Online vs Offline:** Offline store keeps full history for training. Online store keeps latest values for sub-10ms reads at inference.
*   **Point-in-time correctness:** Joining feature values **as they were at event time**, not as they are now. Without it, you leak future information into training labels.
*   **Feature freshness SLO:** Streaming features (e.g. last 5 transactions) need seconds-fresh online store; batch features (e.g. lifetime value) update daily.

## 4. Pipeline Orchestration

| Tool | Strength |
|---|---|
| **Kubeflow Pipelines** | K8s-native, container-per-step, ML-focused |
| **Airflow** | General DAG, mature, weak ML primitives |
| **Dagster** | Asset-oriented, strong typing, software-defined assets |
| **Metaflow (Netflix)** | Pythonic decorators, S3-backed artifact store |
| **Argo Workflows** | Pure K8s CRDs, Kubeflow's substrate |

Choose based on ops surface: K8s shop → Argo/Kubeflow; analytics shop → Airflow/Dagster.

## 5. Distributed Training

### 5.1 Parallelism Modes
*   **Data Parallel (DDP):** Replicate model on each GPU, split batch. AllReduce gradients each step. Standard for models that fit in one GPU.
*   **Tensor Parallel:** Split a single layer's weight matrix across GPUs (Megatron-style). Intra-node, NVLink-bound.
*   **Pipeline Parallel:** Split layers across GPUs, micro-batch through. GPipe, 1F1B schedules.
*   **3D Parallelism:** DP × TP × PP combined for >100B param models.

### 5.2 Memory-Saving Strategies
*   **FSDP (Fully Sharded Data Parallel):** PyTorch native. Shards params, grads, optimizer states across ranks. Equivalent to DeepSpeed ZeRO-3.
*   **DeepSpeed ZeRO:**
    *   **Stage 1:** shard optimizer states.
    *   **Stage 2:** + shard gradients.
    *   **Stage 3:** + shard parameters. Maximum memory savings, more comms.
*   **NCCL:** NVIDIA's collective comms library — `AllReduce`, `AllGather`, `ReduceScatter`. Topology-aware, ring + tree algorithms.

## 6. Hyperparameter Tuning

*   **Optuna:** Define-by-run, **TPE** (Tree-structured Parzen Estimator) sampler — Bayesian, handles conditional spaces.
*   **Ray Tune:** Distributed, integrates ASHA, PBT, Optuna.
*   **ASHA (Asynchronous Successive Halving):** Aggressive early stopping, prunes underperforming trials at rungs (e.g. epoch 1, 4, 16). 10–100x speedup vs grid search.

## 7. Model Registry

*   **MLflow Registry / SageMaker Model Registry / W&B Artifacts.**
*   **Versioning:** SemVer-ish (`name:version`) plus aliases (`@staging`, `@production`, `@champion`).
*   **Promotion flow:** `dev → staging → production` gated by eval thresholds + sign-off.
*   Store: weights + signature (input/output schema) + dependencies + eval report + dataset hash. Reproducibility lives or dies here.

## 8. Model Serving

### 8.1 General-purpose
*   **Triton Inference Server (NVIDIA):** Multi-framework (TF/PyTorch/ONNX/TensorRT/Python), dynamic batching, model ensembles, gRPC + HTTP.
*   **TorchServe:** PyTorch-native, simple. Maintenance has been thin — check status before adopting.
*   **TF Serving:** TensorFlow SavedModel only.
*   **Ray Serve:** Python-first, request-level autoscaling, FastAPI-style.
*   **KServe (K8s CRD):** Standard K8s `InferenceService` CRD over Triton/TorchServe/etc., adds canary, transformer/predictor split.

### 8.2 LLM-specific
*   **vLLM:** PagedAttention (KV cache as virtual memory pages), continuous batching, top throughput for OSS LLMs.
*   **TGI (HuggingFace Text Generation Inference):** Production-tuned, tensor parallel, FP8 support.
*   **TensorRT-LLM:** NVIDIA-optimized, fused kernels, in-flight batching. Lowest latency, hardest to operate.

## 9. Inference Optimization

### 9.1 Quantization
*   **INT8 / INT4:** Weight precision drop. ~4x memory, ~2x throughput.
*   **GPTQ:** Post-training, layer-by-layer, second-order Hessian-based. Good quality at 4-bit.
*   **AWQ (Activation-aware Weight Quantization):** Preserves salient weights based on activation magnitude. Often beats GPTQ at 4-bit.
*   **bitsandbytes:** On-the-fly NF4/INT8 in HF transformers. Easiest path; quality slightly behind GPTQ/AWQ.

### 9.2 Other Techniques
*   **Distillation:** Train smaller student on teacher logits. Common path for shipping <1B param models from a 70B teacher.
*   **ONNX:** Framework-neutral graph IR. Bridge to TensorRT, OpenVINO, CoreML.
*   **TensorRT:** NVIDIA kernel autotuner, layer fusion, FP16/INT8/FP8.
*   **Batching:**
    *   **Dynamic (static models):** Coalesce in-flight requests up to a max-batch / max-delay window.
    *   **Continuous batching (LLMs):** Add/remove sequences mid-decode at the token boundary. Foundation of vLLM/TGI throughput.

## 10. Monitoring

### 10.1 Drift Detection
*   **Data drift (input distribution shift):**
    *   **KS test (Kolmogorov-Smirnov):** Per-feature CDF comparison. Numeric only.
    *   **PSI (Population Stability Index):** Bins-based, threshold ~0.1 (mild), ~0.25 (significant).
    *   **Chi-squared:** Categorical features.
*   **Concept drift (P(y|x) shift):** Detected via accuracy/AUC degradation against ground-truth labels arriving with delay.

### 10.2 Tooling
*   **Evidently:** OSS, ships dashboards + JSON reports.
*   **WhyLabs / Arize / Fiddler:** Managed observability, profile-based monitoring at scale.
*   **Prediction logs:** Sample (1–10%) — full-rate logging is expensive at high QPS. Always log feature values, prediction, model version, request ID.

## 11. CI/CD for ML

*   **DVC (Data Version Control):** Git-tracked pointers to S3-stored data and models. `dvc.yaml` defines pipeline stages with input/output deps for cache-aware reruns.
*   **CML (Continuous Machine Learning):** GitHub Actions plugin for posting metrics/plots into PR comments.
*   **GitHub Actions / GitLab CI triggers:**
    *   On code push: lint, unit test, smoke train on small sample.
    *   On merge to main: full train, eval gate (e.g. AUC ≥ 0.85), register if pass.
    *   Scheduled: drift check → trigger retrain workflow if PSI > threshold.
*   *Promotion is gated on evaluation, not on CI green.* CI green only proves the code runs.

---

## 12. Exercises

### Exercise 1: Feature Store Implementation

1. Install Feast and define a feature repository with two feature views: a batch feature (customer lifetime value, daily refresh) and a streaming feature (transaction count in last 5 minutes).
2. Configure offline store (Parquet/BigQuery) and online store (Redis/DynamoDB).
3. Materialize features to the online store. Verify point-in-time correctness by querying historical features at a past timestamp and confirming no future data leaks.
4. Write a serving endpoint that fetches online features with < 10ms p99 latency.
5. Add a feature freshness SLO check that alerts when the online store lags behind the offline store by more than the configured threshold.

### Exercise 2: Model Registry and Promotion Pipeline

1. Train three model versions on the same dataset with different hyperparameters. Log each to MLflow with params, metrics, artifacts, and dataset hash.
2. Register the best model in the MLflow Model Registry. Set up aliases: `@dev`, `@staging`, `@production`.
3. Build a promotion script that: (a) evaluates the `@staging` model on a held-out test set, (b) compares metrics against the current `@production` model, (c) promotes only if AUC improves by >= 0.01, (d) logs the promotion event with timestamp and eval report.
4. Integrate the promotion script into a GitHub Actions workflow triggered on merge to `main`.
5. Add a rollback script that demotes `@production` to the previous version and logs the rollback reason.

### Exercise 3: Distributed Training Configuration

1. Take a model that fits on a single GPU and train it with DDP across 2 GPUs. Verify identical convergence to single-GPU training (compare loss curves).
2. Switch to FSDP (ZeRO-3 equivalent). Measure peak GPU memory per rank vs. DDP. Document the memory savings.
3. Configure mixed-precision training (FP16 with gradient scaling). Measure throughput (samples/sec) improvement over FP32.
4. Apply GPTQ 4-bit quantization to the trained model. Compare inference latency and model quality (accuracy/perplexity) against the FP32 original.
5. Profile the training run with PyTorch Profiler. Identify the top-3 bottlenecks (data loading, gradient sync, compute) and propose mitigations.

### Exercise 4: Drift Detection and Automated Retraining

1. Deploy a trained model with prediction logging (sample 10% of requests, log features + prediction + model version + request ID).
2. Implement data drift detection: run KS tests on numeric features and chi-squared tests on categorical features against the training distribution. Set thresholds (KS > 0.1, PSI > 0.25).
3. Simulate drift by gradually shifting the input distribution. Verify the drift detector fires when thresholds are crossed.
4. Build an automated retraining workflow: drift detection triggers data collection → retrain → evaluate against champion model → promote if better.
5. Set up an Evidently dashboard showing feature distributions, drift scores, and model performance over time.

### Exercise 5: CI/CD for ML Pipeline

1. Define a DVC pipeline (`dvc.yaml`) with stages: data prep, feature engineering, train, evaluate.
2. Configure cache-aware reruns: changing only the training code should skip data prep and feature engineering.
3. Set up GitHub Actions CI: on push, run lint + unit tests + smoke training (100 samples, 1 epoch). On merge to `main`, run full training.
4. Add CML integration: post training metrics and a confusion matrix plot as a PR comment.
5. Gate model registration on evaluation: the CI job registers the model in MLflow only if the eval metric (e.g., AUC >= 0.85) passes. Document the full pipeline as a DAG diagram.

---

## 13. Readings and References

### Papers

| Paper | Authors | Year | Link | Retrieved |
|---|---|---|---|---|
| Attention Is All You Need | Vaswani, A. et al. | 2017 | https://arxiv.org/abs/1706.03762 | 2026-05-29 |
| PyTorch: An Imperative Style, High-Performance Deep Learning Library | Paszke, A. et al. | 2019 | https://arxiv.org/abs/1912.01703 | 2026-05-29 |
| ZeRO: Memory Optimizations Toward Training Trillion Parameter Models | Rajbhandari, S. et al. | 2019 | https://arxiv.org/abs/1910.02054 | 2026-05-29 |
| GPTQ: Accurate Post-Training Quantization for Generative Pre-Trained Transformers | Frantar, E. et al. | 2022 | https://arxiv.org/abs/2210.17323 | 2026-05-29 |
| AWQ: Activation-aware Weight Quantization for LLM Compression and Acceleration | Lin, J. et al. | 2023 | https://arxiv.org/abs/2306.00978 | 2026-05-29 |
| Efficient Memory Management for Large Language Model Serving with PagedAttention (vLLM) | Kwon, W. et al. | 2023 | https://arxiv.org/abs/2309.06180 | 2026-05-29 |

### Books

- Gift, N. et al. *Practical MLOps*. O'Reilly, 2021.
- Huyen, C. *Designing Machine Learning Systems*. O'Reilly, 2022.
- Treveil, M. et al. *Introducing MLOps*. O'Reilly, 2020.

### Documentation and Guides (retrieved: 2026-05-29)

| Resource | URL |
|---|---|
| MLflow Documentation | https://mlflow.org/docs/latest/ |
| Feast Documentation | https://docs.feast.dev/ |
| Kubeflow Pipelines Documentation | https://www.kubeflow.org/docs/components/pipelines/ |
| PyTorch FSDP Tutorial | https://pytorch.org/tutorials/intermediate/FSDP_tutorial.html |
| DeepSpeed Documentation | https://www.deepspeed.ai/docs/ |
| vLLM Documentation | https://docs.vllm.ai/ |
| Triton Inference Server Documentation | https://docs.nvidia.com/deeplearning/triton-inference-server/user-guide/ |
| KServe Documentation | https://kserve.github.io/website/ |
| DVC Documentation | https://dvc.org/doc |
| Evidently AI Documentation | https://docs.evidentlyai.com/ |
| Optuna Documentation | https://optuna.readthedocs.io/ |
| MLOps Definitive Guide 2026 | https://rahulkolekar.com/mlops-in-2026-the-definitive-guide-tools-cloud-platforms-architectures-and-a-practical-playbook/ |

---

## 14. Cross-References

| Module | Relevance to MLOps Pipelines |
|---|---|
| [01_AI_Engineering_Patterns.md](01_AI_Engineering_Patterns.md) | Production deployment patterns, cost optimization strategies, and observability practices that apply to model serving endpoints |
| [02_LLM_Integration_RAG_VectorDB.md](02_LLM_Integration_RAG_VectorDB.md) | Embedding model serving (for RAG pipelines) uses the same Triton/vLLM/TGI infrastructure; batch embedding jobs fit the pipeline orchestration patterns |
| [../01_Foundations/](../01_Foundations/) | Algorithm complexity analysis for understanding training convergence, distributed communication patterns (AllReduce, ring topology), and numerical stability |
| [../02_Architecture_Design/](../02_Architecture_Design/) | System design for ML serving: load balancing, canary deployments, circuit breakers, and A/B testing infrastructure patterns |
| [../03_Database_Engineering/](../03_Database_Engineering/) | Feature store backend storage (PostgreSQL, Redis, DynamoDB), data pipeline design, and point-in-time query semantics |
| [../05_DevOps_Cloud_Native/](../05_DevOps_Cloud_Native/) | Kubernetes orchestration (pods, CRDs, operators) underpinning Kubeflow, KServe, and Argo Workflows; CI/CD pipeline design for ML; GPU node scheduling and resource quotas |

---

## 15. Glossary

| Term | Definition |
|---|---|
| **MLOps** | Set of practices combining ML, DevOps, and data engineering to deploy and maintain ML systems in production reliably and efficiently |
| **Feature Store** | Infrastructure component providing consistent feature definitions and values for both offline training (batch) and online inference (low-latency), eliminating train-serve skew |
| **Point-in-Time Correctness** | Joining feature values as they existed at the event timestamp, preventing future information leakage into training labels |
| **Model Registry** | Versioned catalog of trained models storing weights, input/output signatures, dependencies, evaluation reports, and dataset hashes with promotion aliases |
| **DDP (Distributed Data Parallel)** | PyTorch strategy replicating the full model on each GPU, splitting batches, and synchronizing gradients via AllReduce each step |
| **FSDP (Fully Sharded Data Parallel)** | PyTorch native strategy sharding parameters, gradients, and optimizer states across ranks, equivalent to DeepSpeed ZeRO Stage 3 |
| **DeepSpeed ZeRO** | Memory optimization framework with three stages: Stage 1 shards optimizer states, Stage 2 adds gradient sharding, Stage 3 adds parameter sharding |
| **GPTQ** | Post-training quantization method using second-order Hessian information to quantize weights layer-by-layer to 4-bit with minimal quality loss |
| **AWQ** | Activation-aware Weight Quantization — preserves salient weights based on activation magnitude, often outperforming GPTQ at 4-bit precision |
| **PagedAttention** | KV cache management technique (vLLM) treating attention cache as virtual memory pages, enabling continuous batching and efficient memory utilization |
| **Data Drift** | Statistical shift in the input feature distribution between training and production data, detected via KS test, PSI, or chi-squared tests |
| **Concept Drift** | Change in the relationship P(y|x) between inputs and outputs, detected via model performance degradation against delayed ground-truth labels |
| **PSI (Population Stability Index)** | Bin-based metric comparing two distributions; PSI < 0.1 indicates stability, 0.1-0.25 mild drift, > 0.25 significant drift requiring investigation |
| **DVC (Data Version Control)** | Git-like version control for data and ML pipelines; stores pointers in Git while actual data lives in remote storage (S3, GCS) |
| **Continuous Batching** | LLM serving technique adding and removing sequences mid-decode at token boundaries, maximizing GPU utilization; foundation of vLLM and TGI throughput |
