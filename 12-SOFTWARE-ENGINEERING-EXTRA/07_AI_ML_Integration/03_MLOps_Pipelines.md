# Module 7.3: MLOps — Training, Serving, Monitoring

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
