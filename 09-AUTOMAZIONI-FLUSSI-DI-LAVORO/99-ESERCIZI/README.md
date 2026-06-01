# 99-ESERCIZI — Lab e Scenari Avanzati

Esercizi cross-module per consolidare il corso.

## Lab guidati

- `lab-01-onboarding-pmi.md` — Workflow onboarding cliente PMI italiana end-to-end.
- `lab-02-multi-platform-comparison.md` — Stesso scenario su 4 piattaforme; report comparison.
- `lab-03-webhook-receiver-production.md` — HMAC + idempotency + DLQ + OTel completo.

## Scenari di troubleshooting

- `scenario-01-zapier-throughput-cliff.md` — Zapier throughput drop causa rate limit downstream.
- `scenario-02-n8n-credential-loss.md` — n8n encryption key perso, recovery procedure.
- `scenario-03-webhook-replay-flood.md` — Attaccante replay 10K webhook validi; mitigation.
- `scenario-04-oauth-rotation-broken.md` — Refresh token expired, downstream silenzioso.

## Lab 01 — Onboarding PMI

**Obiettivo**: workflow completo per onboarding cliente PMI italiana.

**Componenti**:
1. Form web (Typeform/Tally) raccoglie anagrafica + P.IVA.
2. Validazione P.IVA con API Agenzia Entrate (mock se sandbox).
3. Creazione lead in CRM (HubSpot/Pipedrive).
4. Generazione contratto via DocuSign.
5. Fattura prima rata via SDI sandbox.
6. Notifica Slack al team commerciale.
7. Welcome email DKIM-verified.

**Vincoli**: HMAC verifica per webhook Typeform; idempotency lato form-to-CRM; OTel tracing end-to-end.

## Lab 02 — Multi-platform comparison

Implementa "form → enrich → CRM → Slack" su:
- n8n self-hosted
- Make.com
- Zapier
- Power Automate

Misura: tempo build, costo monthly @ 10K task/mese, manutenibilita, lock-in.

## Lab 03 — Webhook receiver production

FastAPI endpoint che riceve webhook Stripe production-grade:
- HMAC verification con `Stripe-Signature`.
- Replay protection: timestamp tolerance 5 min + nonce.
- Idempotency: Redis dedup con TTL 24h.
- DLQ: Postgres table `failed_webhooks` con retry counter.
- OTel: trace ogni richiesta con span per validazione, processing, downstream call.
- Health check + Prometheus metrics.

## Scenario 01 — Zapier throughput cliff

**Sintomi**: Zap che funziona normalmente, all'improvviso 80% errori 429 su downstream API.

**Da diagnosticare**: rate limit downstream (Slack 100 msg/min per workspace? Salesforce API limits?), Zapier che non sa propagare backpressure → tutti i Zap saturano la API.

**Soluzione**: Code by Zapier con `time.sleep` adattivo; oppure pre-aggregazione (digest invece di N msg singoli); oppure migrazione a n8n con rate-limit node.

## Scenario 02 — n8n encryption key persa

**Sintomi**: dopo rebuild server, `N8N_ENCRYPTION_KEY` cambiata; tutti i workflow runnano ma le credentials sono "corrotte" (decryption fail).

**Da risolvere**: ricerca backup `.env`; se non c'e, ri-creare ogni connessione manualmente. **Lezione**: backup encryption key insieme a backup DB, in vault separato.

## Scenario 03 — Webhook replay flood

**Sintomi**: log vede 10K webhook in 5 minuti, tutti con HMAC valido.

**Da risolvere**: replay protection mancante. Implementare: timestamp tolerance 5min + nonce store in Redis con TTL.

## Scenario 04 — OAuth rotation broken

**Sintomi**: workflow che funzionava silently smette di sincronizzare. Nessun errore visibile.

**Da diagnosticare**: refresh token expired; downstream client non gestisce `invalid_grant` come errore loud.

**Soluzione**: alert su qualsiasi `invalid_grant` HTTP response; metric counter token refresh failures; dashboard monitoring expiration.
