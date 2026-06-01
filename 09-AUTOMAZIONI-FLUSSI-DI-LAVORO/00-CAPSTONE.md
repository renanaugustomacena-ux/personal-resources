# Capstone — Automazioni e Flussi di Lavoro

> **Posizione:** progetto pratico finale del corso
> **Prerequisiti:** completamento moduli 01-25, lettura case studies 99-CASE-STUDY/
> **Tempo:** 30-60 ore distribuite in 4-6 settimane
> **Livello:** proficient (Dreyfus 4)
> **Ultimo aggiornamento:** 2026-04-27

## Brief

Progettare e implementare un workflow di onboarding cliente PMI italiana end-to-end, applicando tutti i pattern del corso: HMAC webhook security, idempotency, retry exponential backoff, DLQ, OTel observability, GDPR-compliant audit log, multi-environment promotion.

## Architettura target

```
[Form web Typeform]
       │ webhook (HMAC)
       ▼
[Receive-Verify-Enqueue Gateway (FastAPI)]
       │ HMAC verify, idempotency, enqueue
       ▼
[RabbitMQ main queue]
       │
       ├─► [Worker: validate P.IVA via Agenzia Entrate API]
       │        idempotent, retry 3x, DLQ on fail
       ├─► [Worker: create CRM lead (HubSpot)]
       │        OAuth 2.1 client_credentials
       ├─► [Worker: generate contract via DocuSign]
       ├─► [Worker: send fattura SDI sandbox]
       └─► [Worker: notify Slack + DKIM email]

[OTel Collector] ◄── traces da tutti i worker
[Postgres audit log] ◄── append-only, hash chain
[Grafana dashboard] ◄── burn rate, errori, DLQ size
```

## Deliverables

1. **Architecture document (5-10 pagine)**: scelte di design, alternative considerate, trade-off.
2. **Codice end-to-end** in Git con: gateway FastAPI, worker Python, infrastruttura docker-compose, CI/CD pipeline.
3. **OTel instrumentation completa**: trace cross-service propagato.
4. **Audit log** GDPR-compliant con hash chain.
5. **Test suite**: unit + integration + e2e con coverage ≥ 70%.
6. **Multi-env**: dev + staging + prod con secret separati.
7. **Cost report**: stima monthly cost @ 1K, 10K, 100K onboarding/mese.
8. **Runbook operativo**: procedure failure scenarios.
9. **Final demo (15 min)**: walkthrough end-to-end + Q&A.

## Rubric

| Categoria | Peso | Criteri eccellenza |
|---|---|---|
| Architecture quality | 20% | Trade-off documentati, scalabilita progettata |
| Code quality | 20% | Type hints, structured logging, test coverage |
| Security | 15% | HMAC, idempotency, OAuth 2.1 corretto |
| Observability | 15% | OTel cross-service, dashboard utili |
| Compliance | 10% | Audit log immutable, GDPR data handling |
| CI/CD + multi-env | 10% | Pipeline automatica, rollback testato |
| Documentation | 10% | Runbook readable da terzi |

**Soglia passaggio:** ≥ 70%. **Distinzione:** ≥ 90%.

## Domande di review finale

1. Quale pattern del corso si e rivelato piu critico nel progetto?
2. Quale e stato il rischio piu sottostimato?
3. Cosa cambieresti se rifacessi il progetto?
4. Il tuo runbook e usabile da un terzo? (test pratico)
5. Quale modulo del corso senti meno solido?
