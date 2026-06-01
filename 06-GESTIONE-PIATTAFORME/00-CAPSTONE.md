# Capstone — Piattaforme Cloud-Native

> Progetto pratico finale; 40-80h in 4-8 settimane; livello proficient → expert.

## Brief

Costruire e operare un cluster Kubernetes production-ready su provider cloud con: SLSA Level 2, Pod Security Restricted, OTel observability stack, secret rotation Vault, ArgoCD GitOps, multi-tenancy isolation per 2 team simulati.

## Architettura target

```
[GitHub repo] → [GitHub Actions OIDC]
                  ↓ (cosign sign)
            [Container Registry]
                  ↓ (ArgoCD pull)
[K8s cluster: 3 ctl + 5 worker]
  ├─ Pod Security: Restricted
  ├─ NetworkPolicy: default-DENY
  ├─ Vault sidecar (secret injection)
  ├─ Tenant-A namespace
  ├─ Tenant-B namespace
  └─ shared infrastructure ns
[OTel Collector] → Prometheus + Tempo + Loki + Grafana
```

## Deliverables

1. Terraform/OpenTofu IaC per cluster.
2. ArgoCD applications per tutto il workload.
3. cosign signed images + SLSA L2 attestation.
4. Pod Security Standards Restricted in tutti i namespace.
5. NetworkPolicy default-DENY + esplicite.
6. Vault setup + rotation policy.
7. Observability stack OTel-compliant.
8. Multi-tenancy 2 team con quota + iso.
9. Runbook DR con drill effettuato.
10. Final demo (30 min) + Q&A.

## Rubric: 70% pass, 90% distinction.
