# Capstone — Software Engineering Masterclass

> 60-100h over 8-12 weeks; level expert (Dreyfus 5).

## Brief

Design, implement, and operate a production-grade microservice ecosystem (5+ services) demonstrating competence across all 8 phases.

## Architecture

```
[API Gateway w/ rate limit]
       ↓
[Order Service] ←→ [Payment Service] ←→ [Inventory Service]
       ↓                                       ↓
[Saga Coordinator (Raft)]              [Notification Service]
       ↓
[Outbox + RabbitMQ]
       ↓
[Audit Service (event-sourced)]

[OTel Collector] ← all services
[Prometheus + Tempo + Loki]
[ArgoCD GitOps]
```

## Deliverables

1. **Architecture document with ADRs** for major decisions.
2. **Source code** for 5+ services in Git.
3. **CAP/PACELC reasoning** documented per service.
4. **Saga pattern** implemented with compensation.
5. **Raft consensus** for ordering (etcd-io/raft or built).
6. **OTel cross-service tracing** end-to-end.
7. **SBOM CycloneDX** per service + cosign signed.
8. **OWASP SAMM L2** for governance + design + verification.
9. **SLI/SLO/SLA** defined + alerting multi-burn-rate.
10. **Incident response runbook** + drill executed.
11. **Postmortem** of one synthetic incident.
12. **Demo video (15 min)** + Q&A.

## Rubric

| Category | Weight |
|---|---|
| Architecture quality + ADRs | 15% |
| Distributed patterns (Saga, consensus) | 15% |
| Database design (CAP/PACELC) | 10% |
| Security (SAMM, SBOM, threat model) | 15% |
| Cloud-native (K8s, IaC, GitOps) | 10% |
| Observability (OTel + SLI/SLO) | 15% |
| Testing (pyramid + chaos) | 10% |
| Documentation + Postmortem | 10% |

**Pass:** ≥ 70%. **Distinction:** ≥ 90%.

## Note

This capstone is genuinely 8-12 weeks of full-time work. Don't underestimate.
