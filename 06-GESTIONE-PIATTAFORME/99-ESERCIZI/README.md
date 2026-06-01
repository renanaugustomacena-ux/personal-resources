# 99-ESERCIZI — Lab e Scenari

## Lab

### Lab 01 — K8s production cluster

3 control + 5 worker; Pod Security Restricted; ArgoCD GitOps; OTel + Prometheus + Tempo + Loki; Vault rotation; cosign signed images.

### Lab 02 — Multi-tenancy

Setup vCluster su K8s shared; 2 tenant; ResourceQuota + NetworkPolicy isolation.

### Lab 03 — Cost dashboard

Cost Explorer + Grafana visualization per team con tagging strategy.

## Scenari

- `scenario-01-crashloopbackoff.md` — Pod CrashLoopBackOff; troubleshoot.
- `scenario-02-secret-leaked.md` — gitleaks detect AWS key in Git; rotation + RCA.
- `scenario-03-cost-spike.md` — AWS bill +300%; identify e fix root cause.
- `scenario-04-supply-chain-cve.md` — CVE in transitive dep K8s; patch flow.

## Scenario 01 — CrashLoopBackOff

**Sintomi**: pod restart loop, exitcode 137.

**Investigation**: `kubectl describe pod` (events), `kubectl logs --previous` (last run logs); spesso OOM o init container fail.

**Fix**: aumenta memory limit OR fix init dependency.
