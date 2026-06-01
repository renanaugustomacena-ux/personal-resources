# Case Study — Zapier 2022 Incidents

> **Tipo:** vari incident postmortem 2022 pubblicati su status.zapier.com
> **Aggiornamento:** 2026-04-27 (sintesi storica)

## Cronologia high-level

Zapier ha avuto multiple incident significativi nel 2022, che hanno evidenziato:
- **Database load spikes**: durante migrazioni interne, latency Zap execution salita 10x.
- **Webhook delivery delays**: backlog di webhook fino a 2-4 ore in periodi di traffic spike.
- **Auth provider outages**: Google OAuth + Slack OAuth periodicamente irraggiungibili.

## Lezioni operative per architetti

1. **SaaS automation e single-vendor SPOF.** Zapier down = tutti i tuoi Zap fermi. Pianificare alternative warm.
2. **Webhook delivery non garantita real-time su SaaS.** SLA Zapier non promette delivery < 5 min.
3. **OAuth provider outages sono cross-platform.** Quando Google OAuth e down, Zapier + n8n + Make tutti faticano.
4. **Backlog management richiede idempotency.** Quando 4 ore di webhook arrivano insieme, idempotency salva da side effect duplicate.

## Per organizzazioni mission-critical

- Self-host n8n come backup di Zapier prod.
- Health-check webhook esterni ogni 60s; alarm se delivery > 10 min latency.
- Idempotency mandatory in tutti i workflow downstream.
- Documentare runbook "Zapier down" con failover manuale.

## Riferimenti

- status.zapier.com — postmortem pubblici.
- Zapier engineering blog (2022).
- Hacker News + r/programming discussions sul tema.

## Collegamenti incrociati

- Modulo 14 — `../14-zapier-guida-operativa.md`.
- Modulo 17 — `../17-retry-idempotency-pattern.md`.
- Modulo 22 — `../22-dlq-parking-lot-pattern.md`.
