# Syllabus — Piattaforme Cloud-Native (DevOps/SRE)

> **Lingua:** italiano · **Aggiornamento:** 2026-04-27
> **Versioni:** Kubernetes 1.30+, Docker 27+, Terraform 1.9+, Prometheus 2.x, OpenTelemetry 1.x, Vault 1.16+, Istio 1.22+, Ceph Squid 19.

## 1. Identita

**"Piattaforme cloud-native — DevOps/SRE"** — costruire e operare cluster Kubernetes con Pod Security Standards, OTel observability, supply chain SLSA, IaC Terraform, secret management Vault.

**Target:** competent → expert (Dreyfus 3 → 5). Capable of designing prod-ready K8s + CI/CD + monitoring + secrets stack.

## 2. Prerequisiti

- Linux admin (corso 02), networking (corso 04), Docker basics, Git fluent.

## 3. Obiettivi

1. Provider cloud principali (AWS, Azure, GCP) — strengths/weaknesses.
2. IaC con Terraform/OpenTofu (drift, state management, modules).
3. Kubernetes hardened: Pod Security Standards Restricted, NetworkPolicy, RBAC least-privilege, Kyverno/OPA.
4. CI/CD GitOps (ArgoCD, Flux); SHA-pinning; OIDC cloud creds.
5. Observability: OTel Collector + Prometheus + Tempo + Loki.
6. Secrets: Vault rotation per type; gitleaks scanning.
7. Supply-chain: SLSA, cosign, syft SBOM.
8. Multi-tenancy isolation (namespace, network, control plane).

## 4. Struttura

### Fase 1 — Fondamenti (1-2 settimane)
- 01-03: AWS, Azure, GCP overview
- 04: Infrastructure as Code

### Fase 2 — Container e orchestrazione (3-5 settimane)
- 06: Docker avanzato
- 05: Kubernetes

### Fase 3 — Pipeline e observability (settimane 6-7)
- 07: CI/CD
- 08: Monitoring + observability

### Fase 4 — Servizi piattaforma (settimane 8-10)
- 09: Service mesh
- 10: Load balancer + reverse proxy
- 11: Database management
- 12: Message queues
- 16: API gateway
- 17: Storage distribuito

### Fase 5 — Sicurezza (settimane 11-12)
- 13: Sicurezza piattaforme
- 14: Compliance
- 15: Secrets management
- 20 (NEW): Supply-chain SLSA + cosign
- 22 (NEW): Multi-tenancy isolation

### Fase 6 — Operations + governance
- 18: Troubleshooting
- 21 (NEW): FinOps + cost governance

### Fase 7 — Capstone
- `00-CAPSTONE.md`: K8s cluster con SLSA, Pod Security, OTel, secret rotation.

## 5. Capstone

K8s cluster a 3 control + 5 worker su Hetzner; Pod Security Restricted; ArgoCD + GitOps; OTel + Prometheus + Tempo + Loki; Vault rotation; cosign signed images; SLSA Level 2 minimum.
