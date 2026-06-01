# Phase 5: DevOps, SRE & Cloud Native — Syllabus

> **Last updated:** 2026-05-29

"It works on my machine" is not a valid excuse.

## Module 5.1: Container Internals (Linux Plumbing)

**Goal:** Understand that "Containers" don't exist; they are just isolated processes.

| File | Focus |
|---|---|
| [01_Container_Internals.md](01_Container_Internals.md) | Namespaces, cgroups v2, OverlayFS, OCI runtime spec, seccomp, runc/gVisor/Kata |

*   **Namespaces (Isolation):** PID, NET, MNT, UTS, IPC, USER.
*   **Cgroups v2 (Limits):** CPU, Memory, I/O. OOM Killer interaction.
*   **Filesystems:** OverlayFS, union mounting, Copy-on-Write.

## Module 5.2: Kubernetes Architecture

**Goal:** Orchestrate containers at scale.

| File | Focus |
|---|---|
| [02_Kubernetes_Architecture.md](02_Kubernetes_Architecture.md) | Control plane, scheduling, Gateway API, RBAC, NetworkPolicy, operators |

*   **Control Plane:** API Server, etcd, Scheduler, Controller Manager.
*   **Worker Node:** Kubelet, Kube-Proxy (iptables/IPVS), CRI.
*   **Networking:** CNI, Service mesh, Gateway API.

## Module 5.3: Site Reliability Engineering (SRE)

**Goal:** Treat operations as a software problem.

| File | Focus |
|---|---|
| [03_Site_Reliability_Engineering.md](03_Site_Reliability_Engineering.md) | SLI/SLO/SLA, error budgets, burn-rate alerting, blameless postmortems, toil |

*   **Metrics:** SLI → SLO → SLA. Error Budgets.
*   **Observability:** Prometheus (metrics), OpenTelemetry (traces), structured logging.

## Module 5.4: Infrastructure as Code

**Goal:** Reproducible, version-controlled infrastructure.

| File | Focus |
|---|---|
| [04_Infrastructure_as_Code.md](04_Infrastructure_as_Code.md) | Terraform/OpenTofu, Pulumi, Ansible, drift detection, policy-as-code |

## Module 5.5: Observability — SLI, SLO, SLA

**Goal:** Understand system behavior from external outputs.

| File | Focus |
|---|---|
| [05_Observability_SLI_SLO_SLA.md](05_Observability_SLI_SLO_SLA.md) | Golden signals, distributed tracing, tail sampling, Prometheus + Grafana |

## Module 5.6: Cloud Architecture — AWS, Azure, GCP

**Goal:** Design for the cloud, not just deploy to it.

| File | Focus |
|---|---|
| [06_Cloud_Architecture_AWS_Azure_GCP.md](06_Cloud_Architecture_AWS_Azure_GCP.md) | Well-Architected frameworks, multi-region, FinOps, landing zones, hybrid connectivity |
