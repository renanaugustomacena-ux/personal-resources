# Glossario — Automazioni e Flussi di Lavoro

> Aggregato dai glossari locali dei moduli 01-25. Aggiornamento 2026-04-27.

## A-C

| Termine | Definizione |
|---|---|
| **ACK manuale** | Worker conferma elaborazione, no auto. |
| **AGID** | Agenzia per l'Italia Digitale. |
| **Ansible Vault** | Strumento per cifrare secrets. |
| **API key** | Stringa autenticazione semplice. |
| **At-least-once** | Garanzia: messaggio consegnato >= 1 volta. |
| **Audit log** | Registro tracciabile delle operazioni. |
| **Auth code flow** | OAuth standard per UI app. |
| **AWX / AAP** | Open-source UI / commercial Ansible. |
| **Backoff exponential** | Delay che cresce esponenzialmente. |
| **Backpressure** | Limitare carico downstream. |
| **Blue-green deploy** | Due ambienti, switch atomico. |
| **Canary deploy** | Rilascio progressivo a % utenti. |
| **CIO/CFO/CTO** | C-level executives. |
| **Circuit breaker** | Stop tentativi quando servizio down. |
| **Client credentials** | OAuth service-to-service. |
| **Code by Zapier** | Step custom JS/Python. |
| **Connector** | Modulo pre-built per integrazione servizio. |
| **Constant-time compare** | Confronto che non leak timing info. |
| **Consumer group** | Insieme consumer che condividono lavoro. |
| **Contract testing** | Test che verifica consumer/producer. |
| **Cosign** | Tool sigstore per firma digitale. |
| **Cron** | Scheduling Linux per task periodici. |
| **Cursor pagination** | Token opaco; pagination robusta. |

## D-G

| Termine | Definizione |
|---|---|
| **Data Store (Make)** | Mini-DB integrato. |
| **DLQ** | Dead Letter Queue. |
| **DLP policy** | Data Loss Prevention. |
| **DLX** | Dead Letter Exchange. |
| **DPO** | Data Protection Officer (GDPR). |
| **Drain** | Periodo in cui un nodo non riceve nuove richieste. |
| **Effective once** | At-least-once + idempotency. |
| **End-to-end workflow** | Workflow completo input → delivery. |
| **Event-driven architecture** | Architettura basata su eventi async. |
| **Exactly-once** | Garanzia matematica impossibile in distributed. |
| **Exponential backoff** | Delay growth esponenziale. |
| **Fail-fast** | Errore esplicito immediato. |
| **Fail-safe** | Errore catturato + retry/fallback. |
| **Fattura elettronica** | XML conforme schema Agenzia Entrate. |
| **Feature flag** | Toggle runtime. |
| **GDPR** | EU regulation 2016/679. |

## H-O

| Termine | Definizione |
|---|---|
| **HMAC** | Hash-based Message Authentication Code. |
| **Idempotency** | Operazione ripetibile senza side effects. |
| **Idempotency key** | UUID per dedup. |
| **InvocationID** | UUID per istanza NTDS di un DC. |
| **iPaaS** | Integration Platform as a Service. |
| **Iterator (Make)** | Loop su array. |
| **Jitter** | Random delay per disperdere retry. |
| **JWT** | JSON Web Token. |
| **LACP** | Link Aggregation Control Protocol. |
| **Lock-in** | Difficolta di switch a vendor alternativo. |
| **Low-code / No-code** | UI visuale per workflow. |
| **MAC verify** | Verifica HMAC del messaggio. |
| **mTLS** | Mutual TLS. |
| **n8n** | Open-source iPaaS. |
| **Nonce** | Number used once; previene replay. |
| **OAuth 2.0/2.1** | Authorization standard. |
| **OIDC** | OpenID Connect. |
| **OpenTelemetry / OTel** | Standard observability. |
| **Operation (Make)** | Unita atomica di esecuzione. |
| **OTLP** | OpenTelemetry Protocol. |

## P-T

| Termine | Definizione |
|---|---|
| **Parking lot** | Coda per messaggi non gestibili. |
| **Path (Zapier)** | Branching condizionale. |
| **PKCE** | Proof Key for Code Exchange. |
| **Polling** | Pull periodico dal client. |
| **Power Automate** | iPaaS Microsoft. |
| **Producer / Consumer** | Componenti messaging. |
| **`private_key_jwt`** | OAuth auth via JWT firmato. |
| **Privsep (`privsep=1`)** | Privilege separation per token API. |
| **Queue / Topic / Partition** | Strutture messaging. |
| **Rate limit** | Limite richieste/secondo. |
| **Receive-Verify-Enqueue** | Pattern webhook. |
| **Refresh token** | Long-lived token per re-auth. |
| **Refresh rotation** | Ogni refresh emette nuovo. |
| **REST** | Representational State Transfer. |
| **Retry** | Riprovare operazione fallita. |
| **Retention policy** | Tempo conservazione. |
| **Right to be forgotten** | GDPR Art. 17. |
| **ROI** | Return on Investment. |
| **Router (Make)** | Branching condizionale. |
| **Rollback** | Tornare a versione precedente. |
| **Saga pattern** | Distributed transaction con compensation. |
| **Sandbox** | Ambiente di test isolato. |
| **Scenario (Make)** | Workflow Make. |
| **SDI** | Sistema di Interscambio. |
| **Secret rotation** | Sostituzione periodica credenziali. |
| **Self-hosted** | Hosting on-prem. |
| **SIEM** | Security Information Event Management. |
| **Smoke test** | Test rapido post-deploy. |
| **Solution (Power Platform)** | Container deploy. |
| **Span** | Operazione singola in un trace. |
| **Stripe-Signature** | Header HMAC Stripe webhook. |
| **structlog** | Python structured logging. |
| **Tamper-evidence** | Capacita rilevare modifiche. |
| **Task (Zapier)** | Unita esecuzione. |
| **Test pyramid** | Unit > integration > e2e. |
| **Throttling** | Limitare rate di esecuzione. |
| **Timing attack** | Estrazione info via misurazione tempi. |
| **Trace** | Albero di span end-to-end. |
| **trace_id** | UUID che identifica una trace. |
| **Trigger / Action** | Evento iniziale / step successivo. |

## U-Z

| Termine | Definizione |
|---|---|
| **uv** | Python package manager Rust-based. |
| **Vault** | Secret manager (HashiCorp). |
| **W3C Trace Context** | Standard trace propagation. |
| **WAL** | Write-Ahead Log. |
| **Webhook** | Push da server a client su evento. |
| **Workflow as code** | Workflow versionato come codice. |
| **WORM** | Write-Once-Read-Many. |
| **YAML** | Markup language per config (Ansible). |
| **Zap** | Workflow Zapier. |
| **Zapier** | iPaaS SaaS leader. |
