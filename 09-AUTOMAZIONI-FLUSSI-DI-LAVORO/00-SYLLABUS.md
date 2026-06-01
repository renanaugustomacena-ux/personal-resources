# Syllabus — Automazioni e Flussi di Lavoro

> **Tipo:** struttura formale del corso
> **Lingua:** italiano
> **Ultimo aggiornamento:** 2026-04-27
> **Versioni di riferimento:** n8n 1.x, Make.com (web), Zapier (web), Power Automate (M365), Python 3.11+, Ansible 9.x, OAuth 2.1, OpenTelemetry 1.x

## 1. Identita del corso

**"Automazione workflow"** — automazione dei processi IT/business attraverso piattaforme low-code, scripting Python, infrastructure-as-code (Ansible), webhook HMAC, OAuth flows, retry/idempotency pattern, e governance produttiva.

**Target competenza finale:** competent → proficient (Dreyfus 3 → 4). Capace di costruire workflow multi-piattaforma con DLQ, OTel logging, audit trail, cost monitoring; risolvere webhook security failures; progettare catene retry-idempotency robuste.

## 2. Prerequisiti

- HTTP/REST/JSON fluency.
- Python intermedio (vedi corso 04).
- Concetti API (auth, rate limit, pagination).
- Linux/CLI base (vedi corso 02).
- Familiarita con almeno un servizio cloud (Google Workspace, M365, Slack o equivalente).

## 3. Obiettivi di apprendimento

1. Scegliere fra low-code (n8n, Make, Zapier, Power Automate) e code-first (Python, Ansible) in base a criteri oggettivi (cost, complessita, scale, lock-in).
2. Implementare HMAC verification per webhook (Stripe, Square, custom) con costant-time compare e replay protection.
3. Disegnare retry policy con idempotency key, exponential backoff, circuit breaker.
4. Configurare OAuth 2.1 + refresh token rotation per integrazioni headless.
5. Implementare event-driven architecture con DLQ (Dead Letter Queue), parking-lot pattern.
6. Audit logging compliant per workflow (GDPR, SOX, HIPAA quando applicabile).
7. Cost monitoring per piattaforme cloud automation (task fees, OAuth API limits).
8. Multi-environment promotion (dev → stage → prod) con secret management.

## 4. Struttura del corso

### Fase 1 — Fondamenti (1-2 settimane)
- Modulo 01: Fondamenti automazione
- Modulo 02: Piattaforme low-code overview
- Modulo 03: Scripting automazione (Python/Bash)

### Fase 2 — API & integrazione (3-5 settimane)
- Modulo 04: Integrazione API
- Modulo 20: OAuth 2.1 flows + refresh token

### Fase 3 — Piattaforme specifiche (settimane 6-9)
- Modulo 09: n8n self-hosted
- Modulo 10: Make.com (Integromat)
- Modulo 11: Power Automate M365
- Modulo 14: Zapier
- Modulo 12: Python automazione avanzata
- Modulo 13: Ansible

### Fase 4 — Pattern di affidabilita (settimane 10-12)
- Modulo 15: Webhook security HMAC
- Modulo 17: Retry/idempotency
- Modulo 16: Event-driven architecture
- Modulo 18: Workflow versioning + rollback

### Fase 5 — Governance (settimane 13-14)
- Modulo 06: Testing qualita
- Modulo 07: Governance best practices
- Modulo 19: Cost monitoring
- Modulo 05: Automazione per dominio (verticali)
- Modulo 21: Ricette PMI Italia
- Modulo 22 (NEW): DLQ + parking-lot pattern
- Modulo 23 (NEW): Osservabilita workflow OTel
- Modulo 24 (NEW): Audit logging compliance
- Modulo 25 (NEW): Multi-environment promotion

### Fase 6 — Capstone (settimane 15-16)
- Modulo 08: Progetti pratici
- `00-CAPSTONE.md`: workflow multi-piattaforma con DLQ, OTel, audit, cost.

## 5. Capstone

Progettare e implementare un workflow di onboarding cliente PMI italiano: ricezione contatto via webform → CRM → calendar invite → email DKIM-verified → fattura elettronica SDI mock → notifica Slack. Requisiti: HMAC webhook, idempotency, DLQ, OTel logs, audit trail GDPR-compliant, cost report.

## 6. Cadenza didattica

| Modalita | Ore/settimana | Settimane |
|---|---|---|
| Full-time intensive | 30-40 | 4-5 |
| Part-time serale | 8-10 | 16-20 |
| Self-paced weekend | 4-6 | 24+ |

## 7. Aggiornamenti rispetto alla `00-panoramica-e-piano-di-studio.md` storica

La panoramica storica e preservata. Questo syllabus aggiunge:
- Mappa formale moduli con ID (M.X numerati).
- Capstone formalizzato.
- Nuovi moduli 22-25 per affidabilita produttiva.
- Riferimenti aggiornati a OAuth 2.1 (RFC 9700), OpenTelemetry GA.
