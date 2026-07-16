---
corso: "Gestione Piattaforme e DevOps"
fase: "7 — Architetture Avanzate"
modulo: 24
titolo: "Site Reliability Engineering (SRE): Error Budget, Toil, Chaos Engineering"
versione: "Prometheus 3.x · OpenSLO 1.0 · LitmusChaos 3.x · Pyrra 0.7 · Sloth 0.11"
livello: "Avanzato"
prerequisiti:
  - "05-kubernetes.md"
  - "08-monitoring-observability.md"
  - "18-troubleshooting-e-guide-pratiche.md"
obiettivi:
  - "Definire SLI/SLO/SLA e calcolare error budget"
  - "Identificare e ridurre il toil con automazione"
  - "Implementare chaos engineering come pratica SRE strutturata"
  - "Costruire un sistema di alerting basato su burn rate degli error budget"
  - "Scrivere post-mortem blameless e action items SMART"
tag: [sre, slo, sli, error-budget, toil, chaos-engineering, blameless-postmortem, burn-rate, reliability]
---

# Site Reliability Engineering (SRE) — Documentazione Completa

> **Modulo 24** · **Aggiornamento:** 2026-07-16

## 1. SRE — Origini e Filosofia

Il Site Reliability Engineering (SRE) è stato inventato da Ben Treynor Sloss in Google
nel 2003 e descritto nel libro "Site Reliability Engineering" (O'Reilly, 2016, ora
disponibile gratuitamente su sre.google). La premessa fondante è questa:

> *"SRE is what you get when you treat operations as a software problem."*
> — Ben Treynor Sloss

### Differenze SRE vs DevOps vs Ops tradizionale

```
OPS TRADIZIONALE:
  Obiettivo: zero cambiamenti = zero incidenti
  Problema: il software deve cambiare per migliorare
  Risultato: release trimestrali, change freeze permanente

DEVOPS:
  Obiettivo: velocità di delivery + stabilità
  Pratica: "you build it, you run it"
  Problema: manca un framework strutturato per la reliability

SRE:
  Obiettivo: bilanciare innovazione (velocity) e reliability
  Strumento chiave: error budget (budget di "errori permessi")
  Regola: se il servizio è oltre la soglia di reliability, si ferma il feature work
  Risultato: incentivi allineati tra dev e ops
```

---

## 2. SLI / SLO / SLA — La Gerarchia della Reliability

### SLI: Service Level Indicator

Un SLI è una misura **quantitativa** di un aspetto del servizio.

```
SLI COMUNI:

AVAILABILITY (disponibilità):
  SLI = (richieste_buone / richieste_totali) * 100
  "Buona" = risposta HTTP non 5xx entro il timeout

LATENZA:
  SLI = percentuale di richieste con latenza < soglia
  Es: percentuale di richieste con p99 < 200ms

FRESHNESS (aggiornamento dati):
  SLI = percentuale di query che restituiscono dati recenti (< X minuti)
  Usato per: sistemi di cache, pipeline dati, report

THROUGHPUT:
  SLI = richieste processate per unità di tempo
  Usato per: sistemi batch, code

DURABILITY (durabilità dati):
  SLI = probabilità che i dati scritti siano recuperabili
  Usato per: sistemi storage, backup

QUALITÀ:
  SLI = percentuale di richieste servite senza degradazione
  Es: modello ML che risponde con confidence > soglia
```

### SLO: Service Level Objective

Un SLO è un **target** per un SLI, per un periodo specifico.

```yaml
# Esempi di SLO ben scritti:

SLO per API REST:
  "Nel 30 giorni scorsi, il 99.9% delle richieste GET /orders
   deve avere un HTTP status 2xx o 3xx
   e una latenza p99 inferiore a 200ms"

SLO per pipeline dati:
  "Nell'ultima settimana, il 99.5% delle query alla tabella orders
   deve restituire dati con freshness < 5 minuti"

SLO per servizio di pagamento:
  "Nel mese corrente, il 99.95% delle transazioni di pagamento
   deve essere completata con successo o rifiutata con un codice di errore
   chiaro entro 30 secondi"

COMPONENTI DI UN SLO:
  1. Indicatore (SLI): cosa si misura
  2. Target: es 99.9%
  3. Window: su quale periodo (rolling 30 giorni è consigliato vs calendar)
  4. Servizio: a quale servizio si applica
  5. User journey: da quale prospettiva (utente, non infrastruttura)
```

### Error Budget

```
ERROR BUDGET = 100% - SLO target

Esempio con SLO 99.9% su 30 giorni:
  Error budget = 100% - 99.9% = 0.1%
  
  30 giorni = 30 * 24 * 60 = 43,200 minuti di servizio
  Error budget in minuti = 43,200 * 0.001 = 43.2 minuti
  
  Questo significa: il servizio può essere down/degraded per 43.2 minuti
  al mese PRIMA che violi il proprio SLO.

ERROR BUDGET COME STRUMENTO DECISIONALE:
  Budget pieno (>75%):     team di prodotto può fare release aggressive
  Budget in esaurimento (25-75%): attenzione, rallentare le release
  Budget esaurito (<25%):  STOP feature work → focus su reliability
  Budget a 0%:             nessuna release produzione, solo bug fix
```

---

## 3. Burn Rate — Alert Intelligenti sull'Error Budget

Il burn rate è la velocità con cui si consuma il budget di errore.

```
BURN RATE:

Burn rate = 1x → si consuma il budget esattamente alla velocità "normale"
            (es: 99% availability con SLO 99.9% → burn rate 10x)

Burn rate = 1x → budget esaurito in 30 giorni (normale)
Burn rate = 2x → budget esaurito in 15 giorni
Burn rate = 10x → budget esaurito in 3 giorni!

ALERT BURN RATE (da Google SRE Workbook, Capitolo 5):

Page (PagerDuty immediatamente):
  Burn rate > 14.4x per 1 ora       → budget esaurito in 2 giorni!
  Burn rate > 6x per 6 ore          → budget esaurito in 5 giorni!

Ticket (Jira, no emergenza):
  Burn rate > 3x per 3 giorni
  Burn rate > 1x per 3 giorni (budget sotto il 10%)

VANTAGGIO DEGLI ALERT BURN RATE vs THRESHOLD SEMPLICI:
  Alert semplice: "error rate > 0.1%" → troppi falsi positivi per picchi brevi
  Alert burn rate: "sei sulla strada per esaurire il budget" → solo incidenti reali
```

---

## 4. Toil — Il Nemico della Reliability

Il toil è il lavoro manuale, ripetitivo, che scala linearmente con il traffico e
non produce miglioramenti duraturi.

```
TOIL vs NON-TOIL:

TOIL (da eliminare):
  ✗ Riavviare manualmente un servizio ogni lunedì mattina
  ✗ Approvare manualmente ogni deploy di produzione
  ✗ Rispondere a falsi positivi degli alert
  ✗ Scalare manualmente i pod quando il traffico cresce
  ✗ Copiare log da un sistema all'altro
  ✗ Creare ticket Jira per ogni richiesta di database

NON-TOIL (lavoro SRE valido):
  ✓ Scrivere l'automazione che riavvia il servizio
  ✓ Costruire il sistema di deploy automatico
  ✓ Tuning degli alert per eliminare i falsi positivi
  ✓ Configurare HPA per scaling automatico
  ✓ Costruire pipeline di log aggregation

REGOLA GOOGLE SRE:
  Il toil non deve superare il 50% del tempo di un SRE
  Il resto deve essere: engineering work, capacity planning, post-mortem
  Se il toil supera il 50% → errore sistemico da risolvere con automazione

MISURARE IL TOIL:
  Time tracking settimanale: categorizza ogni attività
  Categories: toil | engineering | on-call | learning | project
  Target: toil < 50%, engineering > 30%
```

---

## 5. Chaos Engineering

```
PRINCIPI DEL CHAOS ENGINEERING (Principles of Chaos.org, 2019):

1. HYPOTHESIS: formulare un'ipotesi sul comportamento del sistema in condizioni normali
2. VARY REAL-WORLD EVENTS: iniettare eventi reali (pod failure, latenza, errori rete)
3. RUN IN PRODUCTION: il chaos deve essere eseguito in produzione (o staging realistico)
4. MINIMIZE BLAST RADIUS: inizia piccolo, limita l'impatto potenziale
5. AUTOMATE: il chaos deve essere automatizzato e schedulato

TIPI DI ESPERIMENTI CHAOS:
  Pod failure:        termina un pod → verifica recovery automatico
  CPU stress:         satura CPU → verifica HPA e latenza
  Memory pressure:    riempie memoria → verifica OOMKilled recovery
  Network latency:    aggiunge latenza di rete → verifica timeout e retry
  Network partition:  disconnette un servizio → verifica circuit breaker
  Disk pressure:      riempie disco → verifica gestione storage
  Clock skew:         sfasa l'orologio del pod → verifica JWT expiry, TOTP

DIFFERENZA: CHAOS vs DISASTRO:
  Chaos Engineering: esperimento controllato, ipotesi formulata, blast radius limitato
  Disastro:          evento non controllato, nessuna preparazione, panico
  
  L'obiettivo del chaos è trovare le debolezze PRIMA che le trovino gli utenti.
```

---

## 6. Post-Mortem Blameless

```
PRINCIPI DEL POST-MORTEM BLAMELESS:

1. NESSUNA COLPA: gli incidenti sono fallimenti del sistema, non delle persone
2. TIMELINE: ricostruire cosa è successo, in ordine cronologico, con fatti
3. ROOT CAUSE: 5 Why per trovare la causa radice (non la causa immediata)
4. ACTION ITEMS SMART: Specific, Measurable, Assignable, Relevant, Time-bound
5. CONDIVISIONE: il post-mortem è condiviso con tutta l'azienda (cultura dell'apprendimento)

TEMPLATE POST-MORTEM:

  Titolo: [SERVIZIO] Degradazione [DATA]
  Severity: SEV-1 (down) | SEV-2 (degraded) | SEV-3 (minor)
  
  Impatto: X utenti colpiti per Y minuti, Z% error rate
  
  Timeline:
    HH:MM  Evento (chi, cosa, dove)
    HH:MM  Alert Prometheus: error rate > 5%
    HH:MM  On-call notificato
    HH:MM  Root cause identificata
    HH:MM  Fix deployato
    HH:MM  Servizio ripristinato
  
  5 Why:
    Perché l'API era down? → Database non raggiungibile
    Perché il database non era raggiungibile? → Connessioni esaurite
    Perché le connessioni erano esaurite? → Memory leak nel connection pool
    Perché c'era il memory leak? → Aggiornamento ORM senza test regression
    Perché l'aggiornamento non aveva test regression? → Coverage insufficiente
  
  Action Items:
    1. [Mario Rossi] Aggiungere test regression per connection pool — entro 2026-07-30
    2. [Platform Team] Configurare alert connection pool exhaustion — entro 2026-07-23
    3. [Marco Bianchi] Review policy aggiornamenti dipendenze — entro 2026-08-07

ERRORI COMUNI NEL POST-MORTEM:
  ✗ "L'errore umano è la root cause" — le persone fanno errori, il sistema deve tollerarli
  ✗ Action items vaghi: "migliorare monitoring" — non è misurabile
  ✗ Post-mortem non condivisi — nessun apprendimento organizzativo
  ✗ Root cause alla prima risposta (causa immediata != causa radice)
```

---

## 7. SLO con OpenSLO e Pyrra

### OpenSLO — Standard Aperto per SLO

```yaml
# OpenSLO: definizione standardizzata di SLO (v1.0, 2023)
apiVersion: openslo/v1
kind: SLO
metadata:
  name: order-service-availability
  displayName: "Order Service Availability"
spec:
  service: order-service
  description: "Availability SLO per il servizio ordini"
  
  indicator:
    ratio:
      counter:
        metric:
          metricSource:
            type: Prometheus
          spec:
            query: |
              sum(rate(http_requests_total{
                job="order-service",
                status!~"5.."
              }[5m]))
        isGood: true
      total:
        metric:
          metricSource:
            type: Prometheus
          spec:
            query: |
              sum(rate(http_requests_total{
                job="order-service"
              }[5m]))
  
  objectives:
    - displayName: "99.9% Availability"
      target: 0.999
      window:
        rolling:
          count: 30
          unit: Day

---
# SLO per latenza
apiVersion: openslo/v1
kind: SLO
metadata:
  name: order-service-latency
spec:
  service: order-service
  indicator:
    ratio:
      counter:
        metric:
          metricSource:
            type: Prometheus
          spec:
            query: |
              sum(rate(http_request_duration_seconds_bucket{
                job="order-service",
                le="0.2"
              }[5m]))
        isGood: true
      total:
        metric:
          metricSource:
            type: Prometheus
          spec:
            query: |
              sum(rate(http_request_duration_seconds_count{
                job="order-service"
              }[5m]))
  objectives:
    - displayName: "99% richieste < 200ms"
      target: 0.99
      window:
        rolling:
          count: 30
          unit: Day
```

### Pyrra — Dashboard SLO da Kubernetes CRD

```yaml
# Pyrra: CRD K8s per definire SLO (genera Prometheus rules automaticamente)
apiVersion: pyrra.dev/v1alpha1
kind: ServiceLevelObjective
metadata:
  name: order-service-availability
  namespace: monitoring
  labels:
    pyrra.dev/team: backend
spec:
  target: "99.9"
  window: 30d
  
  indicator:
    ratio:
      errors:
        metric: http_requests_total{job="order-service",status=~"5.."}
      total:
        metric: http_requests_total{job="order-service"}
```

---

## 8. Strumenti SRE nel 2024-2026

```
TOOL LANDSCAPE SRE (2026):

SLO MANAGEMENT:
  Pyrra 0.7:       CRD K8s → Prometheus rules + dashboard Grafana
  Sloth 0.11:      genera Prometheus recording rules da spec SLO
  OpenSLO CLI:     validazione spec OpenSLO
  Nobl9:           SaaS SLO management
  Datadog SLOs:    integrato in Datadog

CHAOS ENGINEERING:
  LitmusChaos 3.x:  CNCF project, K8s native, 100+ fault injectors
  Chaos Monkey:     Netflix, termina istanze random
  Gremlin:          SaaS enterprise chaos platform
  AWS FIS:          AWS Fault Injection Simulator (managed)
  Chaos Toolkit:    open source, Python-based

ERROR BUDGET TRACKING:
  Prometheus:       recording rules per burn rate
  Grafana:          dashboard con error budget consumption
  Alertmanager:     routing alert per burn rate
  PagerDuty:        incident management + SLO integration
  StatusPage:       comunicazione pubblica degli incidenti

POST-MORTEM:
  Firehydrant:      incident management + post-mortem automation
  PagerDuty:        incident timeline + retrospective
  Blameless.io:     SaaS per post-mortem strutturati
  Google Docs:      template condiviso (semplice ed efficace)
```

---

## 9. SRE Team Structure e Career Path

```
MODELLI DI TEAM SRE:

EMBEDDED SRE:
  Un SRE embedded in ogni team di prodotto
  Pro: ownership chiara, context profondo
  Contro: isolamento, nessuna comunità SRE

CENTRALIZED SRE:
  Un team SRE centrale che serve tutti
  Pro: standardizzazione, community
  Contro: collo di bottiglia, superficiale per ogni servizio

HYBRID (Google model):
  Team SRE centrale per servizi critici (Tier 1)
  SRE come "consulenti" per altri team
  Pro: bilanciamento tra specializzazione e scalabilità

CRITERI DI ACCETTAZIONE DI UN SERVIZIO IN SRE:
  (Google pratica: il servizio deve soddisfare requisiti prima che SRE lo gestisca)
  ✓ Documentazione di architettura completa
  ✓ SLI/SLO definiti e misurati in Prometheus
  ✓ Runbook per i 5 incidenti più comuni
  ✓ Capacity planning documentato
  ✓ Test di carico eseguiti
  ✓ Coverage CI/CD > 80%
  
  Se non soddisfatti: il team di prodotto deve correggere prima che SRE prenda ownership
```

---

> **Versioni di riferimento:** OpenSLO v1.0 (2023, CNCF working group),
> Pyrra 0.7 (2024), LitmusChaos 3.x (CNCF sandbox → incubating 2024),
> Sloth 0.11.0.
> Libro fondante: "Site Reliability Engineering" (Google, O'Reilly, 2016) — free su sre.google
> "The SRE Workbook" (Google, O'Reilly, 2018) — free su sre.google
> Chaos Engineering: "Chaos Engineering" (Casey Rosenthal, O'Reilly, 2020)
