# SLO/SLI — Quantificazione e Multi-Burn-Rate Alerting

> **Modulo:** Operations IT · Modulo 22 (NEW)
> **Prerequisiti:** Modulo 07.
> **Obiettivi:** definire SLI misurabili; calcolare SLO realistici; error budget; multi-window/multi-burn-rate alerting.
> **Tempo:** 60 min · lab 180 min · **Livello:** proficient · **Aggiornamento:** 2026-05-22

---

## Mappa concettuale

```
                         ┌──────────────────────────┐
                         │   Esperienza Utente       │
                         └─────────┬────────────────┘
                                   │ misurata da
                                   ▼
                         ┌──────────────────────────┐
                         │   SLI (indicatori)        │
                         │  availability, latency,   │
                         │  throughput, error rate,   │
                         │  freshness, durability     │
                         └─────────┬────────────────┘
                                   │ confrontati con
                                   ▼
                         ┌──────────────────────────┐
                         │   SLO (obiettivi interni) │
                         │  99.9% availability       │
                         │  p99 latency < 300ms      │
                         └─────────┬────────────────┘
                                   │ generano
                    ┌──────────────┼──────────────┐
                    ▼              ▼              ▼
          ┌────────────────┐ ┌──────────┐ ┌──────────────────┐
          │ Error Budget   │ │ Alerting │ │ SLA (contratto)  │
          │ = 1 - SLO      │ │ multi-   │ │ verso clienti    │
          │ policy, freeze │ │ burn-rate│ │ penalità/crediti  │
          └────────────────┘ └──────────┘ └──────────────────┘
```

---

## Idee guida

1. **SLI = misurazione, SLO = target, SLA = contratto.** Distinzione mandatory.
2. **Error budget = 1 - SLO.** "Possiamo permetterci 0.1% di errori questo mese."
3. **Multi-burn-rate: detect tasso veloce + slow.** Standard SRE Google.
4. **Alert quando consumo error budget e > N%/finestra.** Non quando soglia statica passata.

---

## Parte 1 — Fondamenti: SLI, SLO, SLA

### 1.1 Definizioni precise

#### SLI — Service Level Indicator

Un SLI è una **misurazione quantitativa** di un aspetto del servizio percepito dall'utente. Non è un metrico infrastrutturale (CPU, RAM) ma una metrica che riflette l'esperienza reale.

Caratteristiche di un buon SLI:

- **Misurabile**: raccoglibile in modo automatico, senza intervento umano.
- **Correlato all'esperienza utente**: se l'SLI peggiora, l'utente se ne accorge.
- **Aggregabile**: esprimibile come rapporto (buoni/totali) in un intervallo temporale.
- **Comparabile**: confrontabile tra periodi diversi.

Formula standard di un SLI:

```
SLI = (eventi buoni / eventi totali) × 100%
```

Esempio: se in un'ora un'API riceve 10.000 richieste e 9.970 rispondono sotto i 300ms:

```
SLI_latenza = 9970 / 10000 = 99.7%
```

#### SLO — Service Level Objective

Un SLO è un **target interno** per un SLI, definito dal team di engineering. Esprime: "il nostro SLI deve essere almeno X% nel periodo Y".

```
SLO = SLI ≥ target   per   finestra temporale
```

Esempio: "La disponibilità del servizio API deve essere ≥ 99.9% su base mensile (30 giorni rolling)."

L'SLO **non** è un impegno contrattuale verso il cliente — è un obiettivo che il team usa per prendere decisioni operative (deploy, rollback, feature freeze).

#### SLA — Service Level Agreement

Un SLA è un **contratto legale** tra provider e cliente che specifica:

- Le metriche misurate (derivate dagli SLI)
- I target promessi (derivati dagli SLO, ma **sempre meno aggressivi**)
- Le penalità in caso di violazione (crediti, rimborsi, uscita dal contratto)
- Le esclusioni (manutenzione programmata, forza maggiore)
- Il metodo di misurazione e reporting

> **Regola fondamentale:** SLA target < SLO target < 100%.
> Se il tuo SLO è 99.9%, il tuo SLA dovrebbe essere 99.5% o inferiore.
> Questo margine ti dà tempo per reagire prima che scattino le penalità.

### 1.2 Relazione tra SLI, SLO e SLA

```
                SLI                    SLO                    SLA
          ┌─────────────┐        ┌─────────────┐        ┌─────────────┐
          │ Cosa misuro  │───────▶│ Quanto bene  │───────▶│ Cosa prometto│
          │ (fatto)      │        │ (obiettivo)  │        │ (contratto) │
          └─────────────┘        └─────────────┘        └─────────────┘
           disponibilità          ≥ 99.9%/mese           ≥ 99.5%/mese
           latenza p99            < 300ms                 < 500ms
           error rate             ≤ 0.1%                  ≤ 0.5%

          Proprietario:          Proprietario:            Proprietario:
          Eng / SRE              Eng / Product            Legal / Sales
```

Tabella comparativa completa:

| Aspetto | SLI | SLO | SLA |
|---|---|---|---|
| **Natura** | Misurazione | Obiettivo interno | Contratto legale |
| **Audience** | Team SRE/Eng | Team Eng + Product | Cliente + Legal |
| **Vincolo** | Nessuno | Operativo | Legale/finanziario |
| **Violazione** | Segnale diagnostico | Attiva error budget policy | Attiva penalità/crediti |
| **Flessibilità** | Alta (cambio metriche) | Media (revisione trimestrale) | Bassa (rinegoziazione) |
| **Granularità** | Qualsiasi finestra | Rolling window (7/28/30gg) | Mensile/trimestrale/annuale |
| **Chi definisce** | SRE + Dev | SRE + Product Owner | Sales + Legal + SRE |
| **Esempio** | 99.87% uptime oggi | ≥ 99.9% / 30gg | ≥ 99.5% / mese, penalità 10% |

### 1.3 Perché non puntare al 100%

Il 100% di affidabilità è:

1. **Matematicamente impossibile** in sistemi distribuiti (teorema CAP, FLP).
2. **Economicamente irrazionale**: il costo per ogni "nine" aggiuntivo cresce esponenzialmente.
3. **Operativamente controproducente**: se punti al 100%, ogni deploy è un rischio e la velocità di rilascio crolla.

Tabella costi per nine:

| Nines | Percentuale | Downtime/anno | Downtime/mese | Costo relativo |
|---|---|---|---|---|
| 2 nines | 99% | 3.65 giorni | 7.3 ore | 1x |
| 3 nines | 99.9% | 8.76 ore | 43.8 minuti | ~10x |
| 4 nines | 99.99% | 52.6 minuti | 4.38 minuti | ~100x |
| 5 nines | 99.999% | 5.26 minuti | 26.3 secondi | ~1000x |
| 6 nines | 99.9999% | 31.5 secondi | 2.63 secondi | ~10000x |

Il costo non è solo infrastrutturale: include ridondanza, testing, on-call, automazione, rollback capabilities, incident response.

---

## Parte 2 — Scegliere gli SLI giusti

### 2.1 Metodologia Google SRE per la scelta degli SLI

Il libro "Site Reliability Engineering" di Google propone un approccio sistematico:

1. **Identifica i percorsi utente critici** (Critical User Journeys — CUJ).
2. **Per ogni CUJ, scegli SLI dalla categoria appropriata.**
3. **Usa lo specchio SLI**: "se questo SLI degrada, l'utente lo nota?"
4. **Preferisci SLI basati su request/event**, non su infrastruttura.

### 2.2 Categorie di SLI

#### Disponibilità (Availability)

Misura se il servizio risponde alle richieste.

```
SLI_availability = richieste_con_successo / richieste_totali
```

"Successo" = status code 2xx o 3xx (o codici definiti dal servizio). Escludi: 4xx client error (non colpa del servizio), ma includi 429 (rate limit imposto dal servizio).

Prometheus query per availability:

```promql
# Availability su 30 giorni rolling
1 - (
  sum(rate(http_requests_total{job="api-server", code=~"5.."}[30d]))
  /
  sum(rate(http_requests_total{job="api-server"}[30d]))
)
```

#### Latenza (Latency)

Misura il tempo di risposta percepito dall'utente. Usa percentili, non medie.

```
SLI_latency = richieste_sotto_soglia / richieste_totali
```

Perché percentili e non medie:
- La media nasconde outlier (99 richieste a 10ms + 1 a 10s = media 109ms, sembra ok).
- Il p50 (mediana) mostra l'esperienza tipica.
- Il p95 mostra l'esperienza dei "quasi tutti".
- Il p99 mostra l'esperienza del "coda lunga" — spesso power user o utenti paganti.

Prometheus query per latenza:

```promql
# Proporzione di richieste sotto 300ms (SLI latenza)
sum(rate(http_request_duration_seconds_bucket{job="api-server", le="0.3"}[5m]))
/
sum(rate(http_request_duration_seconds_count{job="api-server"}[5m]))
```

```promql
# p99 latenza (per dashboard, non per SLI direttamente)
histogram_quantile(0.99,
  sum(rate(http_request_duration_seconds_bucket{job="api-server"}[5m])) by (le)
)
```

#### Throughput (Capacità)

Misura la quantità di lavoro processato per unità di tempo.

```
SLI_throughput = operazioni_completate_con_successo / secondo
```

Tipicamente non usato come SLI primario perché la domanda è variabile. Utile per:
- Sistemi batch (ETL, pipeline dati).
- Code di messaggi (messaggi/secondo processati).
- Sistemi di streaming (eventi/secondo).

```promql
# Throughput: richieste al secondo riuscite (media su 5 min)
sum(rate(http_requests_total{job="api-server", code=~"2.."}[5m]))
```

#### Error Rate (Tasso di errore)

Complemento dell'availability, ma spesso più granulare.

```
SLI_error_rate = richieste_con_errore / richieste_totali
```

Distinzione importante:

| Tipo errore | Conta per SLI? | Motivo |
|---|---|---|
| 5xx (server error) | Sì | Colpa del servizio |
| 4xx (client error) | No (in generale) | Colpa del client |
| 429 (rate limit) | Dipende | Se causato da capacity planning insufficiente → sì |
| 408 (timeout) | Sì | Il servizio è troppo lento |
| Errori parziali | Sì (pesati) | Risposta degradata |

```promql
# Error rate su finestra 1h
sum(rate(http_requests_total{job="api-server", code=~"5.."}[1h]))
/
sum(rate(http_requests_total{job="api-server"}[1h]))
```

#### Freshness (Freschezza dati)

Misura quanto sono aggiornati i dati presentati all'utente. Critico per:
- Dashboard real-time.
- Sistemi di ricerca (indice aggiornato).
- Cache invalidation.
- Replica database.

```
SLI_freshness = proporzione_dati_aggiornati_entro_soglia
```

```promql
# Età del dato più vecchio nella pipeline (es. replication lag)
max(mysql_slave_seconds_behind_master{job="mysql-replica"})

# Proporzione di record freschi (aggiornati negli ultimi 60s)
sum(data_freshness_within_threshold_total{threshold="60s"})
/
sum(data_freshness_checks_total)
```

#### Durabilità (Durability)

Misura la probabilità che un dato scritto possa essere letto in futuro.

```
SLI_durability = dati_leggibili_con_successo / dati_scritti
```

Tipicamente misurato come:
- Assenza di data loss in un periodo (0 oggetti persi / totale oggetti).
- Successo di read-after-write test periodici.

#### Correttezza (Correctness)

Misura se il servizio produce risultati corretti.

```
SLI_correctness = risposte_corrette / risposte_totali
```

Richiede una definizione di "corretto" (golden dataset, business rules, checksums). Utile per:
- Sistemi di calcolo (fatturazione, pricing).
- Pipeline ML (predizioni entro range atteso).
- Sistemi di pagamento.

### 2.3 Matrice SLI per tipo di servizio

| Tipo servizio | SLI primari | SLI secondari |
|---|---|---|
| **API REST/gRPC** | Availability, Latency (p99) | Error rate, Throughput |
| **Web frontend** | Availability, Latency (LCP/FID) | Error rate JS, CLS |
| **Database** | Availability, Latency (query p99) | Durability, Replication lag |
| **Message queue** | Availability, Freshness (lag) | Throughput, Error rate |
| **Pipeline batch** | Freshness, Correctness | Throughput, Durability |
| **CDN** | Availability, Latency (TTFB) | Cache hit rate, Error rate |
| **Storage (S3-like)** | Availability, Durability | Latency, Throughput |
| **Streaming (video)** | Availability, Latency (buffering) | Bitrate, Error rate |
| **Ricerca** | Availability, Latency, Freshness | Correctness (recall/precision) |
| **Autenticazione** | Availability, Latency | Error rate, Correctness |

### 2.4 Dove misurare gli SLI

La posizione della misurazione determina cosa stai effettivamente misurando:

```
┌───────┐     ┌───────┐     ┌──────────┐     ┌─────────┐     ┌──────┐
│ Utente│────▶│  CDN  │────▶│Load Bal. │────▶│ App Srv │────▶│  DB  │
└───────┘     └───────┘     └──────────┘     └─────────┘     └──────┘
    △              △              △                △              △
    │              │              │                │              │
  (ideale)      (buono)     (accettabile)    (server-side)  (backend)
 client RUM    edge logs   LB access logs    app metrics    DB metrics
```

| Punto di misura | Pro | Contro |
|---|---|---|
| **Client (RUM)** | Esperienza reale utente | Rumoroso, dipende da rete client |
| **Edge/CDN** | Vicino all'utente, logs strutturati | Non cattura errori post-CDN |
| **Load Balancer** | Punto centrale, tutti i request | Non vede errori interni all'app |
| **Application** | Dettagliato, per-endpoint | Non vede errori di rete |
| **Synthetics** | Controllato, baseline stabile | Non rappresenta traffico reale |

**Best practice**: misura al punto più vicino all'utente possibile. Se puoi, combina server-side metrics + client RUM.

---

## Parte 3 — Definire target SLO

### 3.1 Metodologia per il target setting

Non scegliere un numero a caso. Segui questo processo:

#### Passo 1: Misura lo storico

Raccogli almeno 4 settimane di dati SLI reali. Calcola:

```promql
# SLI availability storico su 28 giorni
1 - (
  sum(increase(http_requests_total{job="api-server", code=~"5.."}[28d]))
  /
  sum(increase(http_requests_total{job="api-server"}[28d]))
)
```

#### Passo 2: Identifica il baseline

Se lo storico mostra 99.95% availability su 28 giorni, il tuo SLO non dovrebbe essere 99.99% (non ci sei ancora) né 99.5% (troppo rilassato).

Regola pratica: **SLO = storico - margine ragionevole**.

Se lo storico è 99.95%, un buon SLO iniziale è 99.9%.

#### Passo 3: Allinea con i requisiti di business

| Domanda | Implicazione |
|---|---|
| Quanti utenti impattati da un outage? | Determina la "nine" necessaria |
| C'è un'alternativa (failover, fallback)? | Se sì, SLO meno aggressivo possibile |
| Quanto costa il downtime per l'azienda? | ROI dell'infrastruttura di reliability |
| Qual è la tolleranza del cliente? | Influenza l'SLA (e quindi l'SLO) |
| Quanto spesso rilasciate? | Deploy frequenti = più rischio = SLO meno aggressivo |

#### Passo 4: Definisci la finestra temporale

| Tipo finestra | Descrizione | Quando usare |
|---|---|---|
| **Rolling (28 giorni)** | Ultimi 28 giorni calcolati ad ogni momento | Preferito. Rende visibile l'impatto di incidenti recenti |
| **Calendar month** | Dal 1° all'ultimo giorno del mese | Allineato con billing, ma un incidente a inizio mese "si diluisce" |
| **Rolling (7 giorni)** | Ultimi 7 giorni | Per servizi nuovi o in fase di stabilizzazione |

**Raccomandazione Google SRE**: rolling 28 giorni, perché:
- Evita l'effetto "reset" a inizio mese.
- 4 settimane coprono tutti i pattern settimanali.
- Un incidente grave resta visibile per 28 giorni, motivando prevenzione.

### 3.2 Nines di affidabilità — guida alla scelta

| Target | Downtime 28gg | Tipo servizio | Infrastruttura tipica |
|---|---|---|---|
| 99% (2 nines) | 6.72 ore | Tool interni, batch non critici | Singola istanza, no HA |
| 99.5% | 3.36 ore | Servizi interni, staging | Singola istanza + monitoring |
| 99.9% (3 nines) | 40.3 minuti | API production, web app | Multi-AZ, auto-scaling, LB |
| 99.95% | 20.2 minuti | SaaS business-critical | Multi-AZ, blue-green deploy, CDN |
| 99.99% (4 nines) | 4.03 minuti | Fintech, healthcare, pagamenti | Multi-region, chaos engineering |
| 99.999% (5 nines) | 24.2 secondi | Telecom core, 911, trading | Active-active multi-DC, auto-failover <10s |

> **Attenzione:** Ogni "nine" in più richiede investimenti sproporzionati in ridondanza,
> automazione, testing, e competenze del team. Non scegliere 4 nines "perché suona bene".

### 3.3 SLO compositi

Quando un servizio ha dipendenze, l'SLO effettivo è limitato dalla catena più debole:

```
Servizio A (SLO 99.9%) → Servizio B (SLO 99.9%) → Database (SLO 99.95%)

SLO effettivo ≤ 99.9% × 99.9% × 99.95% = 99.75%
```

Questo è il motivo per cui:
- Ogni dipendenza aggiunta abbassa l'SLO raggiungibile.
- I microservizi richiedono SLO individuali molto alti per comporre un SLO accettabile.
- Fallback e circuit breaker sono essenziali per isolare le dipendenze.

---

## Calcolo error budget

```
SLO = 99.9% (3 nines)
Error budget mensile = (1 - 0.999) * 30 days = 0.001 * 30 = 0.03 days = 43 minuti

Burn rate: consumo error budget / total
- 1x burn rate = consumi tutto in 30 giorni
- 14.4x burn rate = consumi tutto in 1 ora (5%) → page!
- 6x burn rate = 6 ore di consumo (10%) → ticket
```

---

## Parte 4 — Error Budget: calcolo, policy e governance

### 4.1 Calcolo error budget dettagliato

L'error budget è la quantità di "inaffidabilità" tollerata entro la finestra SLO.

```
Error Budget = 1 - SLO target
```

Esempi calcolati per finestra 30 giorni:

| SLO | Error Budget (%) | Error Budget (minuti/30gg) | Error Budget (richieste se 1M/gg) |
|---|---|---|---|
| 99% | 1% | 432 min (7.2 ore) | 300.000 errori |
| 99.5% | 0.5% | 216 min (3.6 ore) | 150.000 errori |
| 99.9% | 0.1% | 43.2 min | 30.000 errori |
| 99.95% | 0.05% | 21.6 min | 15.000 errori |
| 99.99% | 0.01% | 4.32 min | 3.000 errori |

Prometheus query per calcolo error budget rimanente:

```promql
# Error budget consumato (proporzione, 0-1)
# Per availability SLI
(
  sum(increase(http_requests_total{job="api-server", code=~"5.."}[30d]))
  /
  sum(increase(http_requests_total{job="api-server"}[30d]))
)
/
(1 - 0.999)
```

```promql
# Error budget rimanente in percentuale
(
  1 - (
    sum(increase(http_requests_total{job="api-server", code=~"5.."}[30d]))
    /
    sum(increase(http_requests_total{job="api-server"}[30d]))
  )
  /
  (1 - 0.999)
) * 100
```

### 4.2 Error Budget Policy

L'error budget policy è un documento che definisce **cosa succede** quando il budget si avvicina all'esaurimento o si esaurisce. Senza policy, l'error budget è solo un numero decorativo.

#### Template error budget policy

```yaml
# error-budget-policy.yaml
service: api-gateway
slo_target: 99.9%
window: 30d rolling
owner: team-platform

thresholds:
  - level: green
    budget_remaining: ">50%"
    actions:
      - "Operazioni normali"
      - "Deploy consentiti senza restrizioni"
      - "Esperimenti e chaos testing consentiti"

  - level: yellow
    budget_remaining: "25%-50%"
    actions:
      - "Review obbligatoria pre-deploy"
      - "No chaos testing"
      - "Post-mortem per ogni incidente che consuma >5% budget"
      - "Team SRE in allerta"

  - level: orange
    budget_remaining: "10%-25%"
    actions:
      - "Feature freeze: solo bug fix e reliability work"
      - "Ogni deploy richiede approvazione SRE + Engineering Lead"
      - "Rollback automatico se error rate > 1% post-deploy"
      - "Standup giornaliero sulla reliability"

  - level: red
    budget_remaining: "<10%"
    actions:
      - "Deploy freeze totale (solo hotfix critici)"
      - "Tutto il team su reliability work"
      - "Escalation a VP Engineering"
      - "Incident review entro 24 ore per ogni errore"

  - level: exhausted
    budget_remaining: "0% (SLO violato)"
    actions:
      - "Deploy freeze fino al ripristino del budget"
      - "Post-mortem obbligatorio entro 48 ore"
      - "Action items devono essere completati prima di riprendere feature work"
      - "Review architetturale se SLO violato 2 mesi consecutivi"
      - "Se SLA violato: attivazione processo di incident report per il cliente"

escalation_path:
  - "Team SRE Lead"
  - "Engineering Manager"
  - "VP Engineering"
  - "CTO (solo se SLA violato)"

review_cadence: "Settimanale durante standup, mensile durante SLO review"
```

### 4.3 Burn rate — concetti avanzati

Il burn rate misura **quanto velocemente** il servizio sta consumando l'error budget.

```
Burn rate = tasso_errore_attuale / tasso_errore_consentito_da_SLO
```

Dove:

```
tasso_errore_consentito = (1 - SLO) / finestra_in_ore

Per SLO 99.9% su 30 giorni:
tasso_errore_consentito = 0.001 / 720 ore = 0.00000139 per ora

Se il tasso errore attuale è 0.00002 per ora:
burn_rate = 0.00002 / 0.00000139 = 14.4x
```

Significato pratico del burn rate:

| Burn rate | Tempo per esaurire budget | Impatto |
|---|---|---|
| 0.5x | 60 giorni | Servizio più affidabile del necessario |
| 1x | 30 giorni | Consumo uniforme, ok se transitorio |
| 2x | 15 giorni | Preoccupante se sostenuto |
| 3x | 10 giorni | Richiede azione a breve termine |
| 6x | 5 giorni | Azione urgente necessaria |
| 14.4x | ~2 giorni | Emergenza, intervento immediato |
| 36x | 20 ore | Outage significativo in corso |
| 720x | 1 ora | Servizio completamente down |

---

## Parte 5 — Multi-Burn-Rate Alerting

### 5.1 Perché il multi-burn-rate

Il problema dell'alerting tradizionale (soglie statiche):

| Approccio | Problema |
|---|---|
| "Alert se error rate > 1%" | Troppi falsi positivi per spike brevi. Spike di 30 secondi al 2% = nessun impatto reale su SLO |
| "Alert se availability < 99.9% sull'ora" | Troppo lento per outage totali. Se il servizio è down, aspetti 1 ora? |
| "Alert su ogni errore 5xx" | Noise infinito. Ogni errore diventa un page |

La soluzione del Google SRE Workbook: **multi-window, multi-burn-rate alerting**.

Principio: alert basati su **quanto velocemente stai consumando l'error budget**, con finestre multiple per bilanciare velocità di detection vs falsi positivi.

### Multi-burn-rate alerting (Google SRE)

| Window | Burn rate | Severity |
|---|---|---|
| 5 min + 1h | 14.4x | Page |
| 30 min + 6h | 6x | Page |
| 2h + 1d | 3x | Ticket |
| 6h + 3d | 1x | Ticket |

### 5.2 Come funzionano le due finestre

Ogni regola di alerting ha **due finestre**:

- **Finestra corta** (short window): verifica che il problema sia **attuale** (non storico).
- **Finestra lunga** (long window): verifica che il problema sia **significativo** (non un microscopico spike).

L'alert scatta solo quando **entrambe** le finestre superano il burn rate.

```
ALERT SE:
  burn_rate(finestra_corta) > soglia
  AND
  burn_rate(finestra_lunga) > soglia
```

Questo elimina:
- **Falsi positivi da spike brevi**: lo spike dura 2 minuti, la finestra lunga non lo cattura.
- **Alert stale**: il problema è finito 2 ore fa ma la finestra lunga lo mostra ancora — la finestra corta lo esclude.

### 5.3 Derivazione matematica dei burn rate

Da dove vengono i numeri 14.4x, 6x, 3x, 1x?

Il principio: "quale burn rate consumerebbe X% dell'error budget nella finestra lunga?"

```
burn_rate = (budget_consumato_target / 100) × finestra_SLO / finestra_alert

Per SLO window = 30 giorni = 720 ore:

14.4x: consuma 2% del budget in 1 ora
       = 0.02 × 720 / 1 = 14.4

6x:    consuma 5% del budget in 6 ore
       = 0.05 × 720 / 6 = 6.0

3x:    consuma 10% del budget in 1 giorno (24h)
       = 0.10 × 720 / 24 = 3.0

1x:    consuma 10% del budget in 3 giorni (72h)
       = 0.10 × 720 / 72 = ~1.0 (arrotondato)
```

### 5.4 Implementazione Prometheus completa

#### Recording rules per SLI

```yaml
# prometheus/rules/slo-recording-rules.yaml
groups:
  - name: slo_sli_recording
    interval: 30s
    rules:
      # ---- Tasso di errore per diverse finestre ----
      - record: slo:http_error_rate:rate5m
        expr: |
          sum(rate(http_requests_total{job="api-server", code=~"5.."}[5m]))
          /
          sum(rate(http_requests_total{job="api-server"}[5m]))

      - record: slo:http_error_rate:rate30m
        expr: |
          sum(rate(http_requests_total{job="api-server", code=~"5.."}[30m]))
          /
          sum(rate(http_requests_total{job="api-server"}[30m]))

      - record: slo:http_error_rate:rate1h
        expr: |
          sum(rate(http_requests_total{job="api-server", code=~"5.."}[1h]))
          /
          sum(rate(http_requests_total{job="api-server"}[1h]))

      - record: slo:http_error_rate:rate2h
        expr: |
          sum(rate(http_requests_total{job="api-server", code=~"5.."}[2h]))
          /
          sum(rate(http_requests_total{job="api-server"}[2h]))

      - record: slo:http_error_rate:rate6h
        expr: |
          sum(rate(http_requests_total{job="api-server", code=~"5.."}[6h]))
          /
          sum(rate(http_requests_total{job="api-server"}[6h]))

      - record: slo:http_error_rate:rate1d
        expr: |
          sum(rate(http_requests_total{job="api-server", code=~"5.."}[1d]))
          /
          sum(rate(http_requests_total{job="api-server"}[1d]))

      - record: slo:http_error_rate:rate3d
        expr: |
          sum(rate(http_requests_total{job="api-server", code=~"5.."}[3d]))
          /
          sum(rate(http_requests_total{job="api-server"}[3d]))

      # ---- Latenza SLI (proporzione sotto 300ms) ----
      - record: slo:http_latency_good_rate:rate5m
        expr: |
          sum(rate(http_request_duration_seconds_bucket{
            job="api-server", le="0.3"
          }[5m]))
          /
          sum(rate(http_request_duration_seconds_count{
            job="api-server"
          }[5m]))

      - record: slo:http_latency_good_rate:rate1h
        expr: |
          sum(rate(http_request_duration_seconds_bucket{
            job="api-server", le="0.3"
          }[1h]))
          /
          sum(rate(http_request_duration_seconds_count{
            job="api-server"
          }[1h]))

      - record: slo:http_latency_good_rate:rate6h
        expr: |
          sum(rate(http_request_duration_seconds_bucket{
            job="api-server", le="0.3"
          }[6h]))
          /
          sum(rate(http_request_duration_seconds_count{
            job="api-server"
          }[6h]))

      # ---- Error budget rimanente ----
      - record: slo:error_budget_remaining:ratio
        expr: |
          1 - (
            slo:http_error_rate:rate30d
            /
            (1 - 0.999)
          )
        labels:
          slo: "api-availability-99.9"

      - record: slo:http_error_rate:rate30d
        expr: |
          sum(rate(http_requests_total{job="api-server", code=~"5.."}[30d]))
          /
          sum(rate(http_requests_total{job="api-server"}[30d]))
```

#### Alert rules multi-burn-rate

```yaml
# prometheus/rules/slo-alert-rules.yaml
groups:
  - name: slo_availability_alerts
    rules:
      # ---- PAGE: 14.4x burn rate (5m + 1h) ----
      # Consuma 2% del budget in 1 ora → outage rapido
      - alert: SLOAvailabilityBurnRateCritical
        expr: |
          slo:http_error_rate:rate5m > (14.4 * 0.001)
          and
          slo:http_error_rate:rate1h > (14.4 * 0.001)
        for: 2m
        labels:
          severity: critical
          slo: api-availability
          burn_rate: "14.4x"
        annotations:
          summary: >-
            API availability SLO: burn rate critico (14.4x)
          description: >-
            Il servizio api-server sta consumando l'error budget a 14.4x.
            A questo ritmo, il budget mensile si esaurisce in ~50 ore.
            Error rate attuale (5m): {{ $value | humanizePercentage }}.
          runbook_url: https://wiki.internal/runbooks/slo-availability-critical

      # ---- PAGE: 6x burn rate (30m + 6h) ----
      # Consuma 5% del budget in 6 ore → degradazione significativa
      - alert: SLOAvailabilityBurnRateHigh
        expr: |
          slo:http_error_rate:rate30m > (6 * 0.001)
          and
          slo:http_error_rate:rate6h > (6 * 0.001)
        for: 5m
        labels:
          severity: critical
          slo: api-availability
          burn_rate: "6x"
        annotations:
          summary: >-
            API availability SLO: burn rate alto (6x)
          description: >-
            Il servizio api-server sta consumando l'error budget a 6x.
            A questo ritmo, il budget si esaurisce in ~5 giorni.
            Error rate attuale (30m): {{ $value | humanizePercentage }}.
          runbook_url: https://wiki.internal/runbooks/slo-availability-high

      # ---- TICKET: 3x burn rate (2h + 1d) ----
      # Consuma 10% del budget in 1 giorno → problema lento
      - alert: SLOAvailabilityBurnRateMedium
        expr: |
          slo:http_error_rate:rate2h > (3 * 0.001)
          and
          slo:http_error_rate:rate1d > (3 * 0.001)
        for: 15m
        labels:
          severity: warning
          slo: api-availability
          burn_rate: "3x"
        annotations:
          summary: >-
            API availability SLO: burn rate moderato (3x)
          description: >-
            Il servizio api-server sta consumando l'error budget a 3x.
            Budget si esaurisce in ~10 giorni a questo ritmo.
            Error rate attuale (2h): {{ $value | humanizePercentage }}.
          runbook_url: https://wiki.internal/runbooks/slo-availability-medium

      # ---- TICKET: 1x burn rate (6h + 3d) ----
      # Consumo uniforme → il budget non durerà il mese
      - alert: SLOAvailabilityBurnRateLow
        expr: |
          slo:http_error_rate:rate6h > (1 * 0.001)
          and
          slo:http_error_rate:rate3d > (1 * 0.001)
        for: 30m
        labels:
          severity: warning
          slo: api-availability
          burn_rate: "1x"
        annotations:
          summary: >-
            API availability SLO: burn rate sostenuto (1x)
          description: >-
            Il servizio api-server sta consumando error budget a 1x sostenuto.
            Il budget si esaurirà prima della fine della finestra SLO.
            Error rate attuale (6h): {{ $value | humanizePercentage }}.
          runbook_url: https://wiki.internal/runbooks/slo-availability-low

  - name: slo_latency_alerts
    rules:
      # ---- Latency SLO: p99 < 300ms, target 99.9% ----
      - alert: SLOLatencyBurnRateCritical
        expr: |
          (1 - slo:http_latency_good_rate:rate5m) > (14.4 * 0.001)
          and
          (1 - slo:http_latency_good_rate:rate1h) > (14.4 * 0.001)
        for: 2m
        labels:
          severity: critical
          slo: api-latency
          burn_rate: "14.4x"
        annotations:
          summary: >-
            API latency SLO: burn rate critico (14.4x)
          description: >-
            La proporzione di richieste lente sta consumando
            l'error budget latenza a 14.4x.

      - alert: SLOLatencyBurnRateHigh
        expr: |
          (1 - slo:http_latency_good_rate:rate5m) > (6 * 0.001)
          and
          (1 - slo:http_latency_good_rate:rate6h) > (6 * 0.001)
        for: 5m
        labels:
          severity: critical
          slo: api-latency
          burn_rate: "6x"
        annotations:
          summary: >-
            API latency SLO: burn rate alto (6x)

  - name: slo_error_budget_alerts
    rules:
      # ---- Alert su budget rimanente ----
      - alert: SLOErrorBudgetLow
        expr: slo:error_budget_remaining:ratio < 0.25
        for: 5m
        labels:
          severity: warning
          slo: api-availability
        annotations:
          summary: >-
            Error budget sotto il 25%
          description: >-
            Rimane solo {{ $value | humanizePercentage }} dell'error budget.
            Attivare error budget policy livello orange.

      - alert: SLOErrorBudgetExhausted
        expr: slo:error_budget_remaining:ratio < 0
        for: 1m
        labels:
          severity: critical
          slo: api-availability
        annotations:
          summary: >-
            Error budget esaurito — SLO violato
          description: >-
            L'error budget è esaurito. SLO violato.
            Attivare deploy freeze e incident review.
```

### 5.5 Configurazione Alertmanager

```yaml
# alertmanager/alertmanager.yml
route:
  receiver: default
  group_by: ['slo', 'severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  routes:
    # SLO critical → page on-call
    - match:
        severity: critical
      receiver: slo-page
      group_wait: 10s
      repeat_interval: 1h
      continue: true

    # SLO warning → ticket
    - match:
        severity: warning
      receiver: slo-ticket
      group_wait: 1m
      repeat_interval: 8h

receivers:
  - name: default
    webhook_configs:
      - url: 'http://webhook-handler:9095/default'

  - name: slo-page
    pagerduty_configs:
      - service_key_file: '/etc/alertmanager/secrets/pagerduty-key'
        severity: critical
        description: '{{ .CommonAnnotations.summary }}'
        details:
          slo: '{{ .CommonLabels.slo }}'
          burn_rate: '{{ .CommonLabels.burn_rate }}'
          description: '{{ .CommonAnnotations.description }}'
          runbook: '{{ .CommonAnnotations.runbook_url }}'
    slack_configs:
      - api_url_file: '/etc/alertmanager/secrets/slack-webhook'
        channel: '#sre-alerts'
        title: '[{{ .Status | toUpper }}] {{ .CommonAnnotations.summary }}'
        text: '{{ .CommonAnnotations.description }}'

  - name: slo-ticket
    webhook_configs:
      - url: 'http://jira-webhook:9096/create-ticket'
        send_resolved: true
    slack_configs:
      - api_url_file: '/etc/alertmanager/secrets/slack-webhook'
        channel: '#sre-tickets'
        title: '[TICKET] {{ .CommonAnnotations.summary }}'
        text: '{{ .CommonAnnotations.description }}'

inhibit_rules:
  # Se c'è un alert critical, sopprimi warning per lo stesso SLO
  - source_match:
      severity: critical
    target_match:
      severity: warning
    equal: ['slo']
```

---

## Parte 6 — SLA verso il cliente

### 6.1 Differenze operative SLO vs SLA

| Aspetto | SLO | SLA |
|---|---|---|
| **Se violato** | Team interno agisce (freeze, on-call) | Penalità finanziarie, rischio legale |
| **Chi monitora** | Eng/SRE (Prometheus, Grafana) | Anche il cliente (spesso con strumenti propri) |
| **Come calcolare** | Rolling window, granulare | Calendar month, semplificato |
| **Esclusioni** | Nessuna (ogni errore conta) | Manutenzione programmata, forza maggiore |
| **Modifica** | Decisione interna del team | Rinegoziazione contrattuale |

### 6.2 Progettazione SLA per clienti

#### Principio base

```
SLA target = SLO target - margine di sicurezza (tipicamente 0.1%-0.5%)
```

Se il tuo SLO è 99.9%, il tuo SLA dovrebbe essere 99.5% o massimo 99.7%.

#### Struttura di un SLA documento

```markdown
# Service Level Agreement — [Nome Servizio]

## 1. Definizioni
- "Disponibilità Mensile": percentuale di minuti nel mese in cui il servizio
  risponde alle richieste entro i parametri definiti.
- "Downtime": periodo in cui il servizio non risponde o risponde con errore
  a più del 5% delle richieste in una finestra di 5 minuti.
- "Manutenzione Programmata": interventi comunicati con almeno 72 ore
  di anticipo. Esclusi dal calcolo di disponibilità.

## 2. Metriche di servizio
| Metrica           | Target          | Metodo di misura              |
|-------------------|-----------------|-------------------------------|
| Disponibilità     | ≥ 99.5% / mese  | Probe sintetici ogni 60s      |
| Latenza API       | p95 < 500ms     | Metriche server-side          |
| Error rate        | ≤ 0.5%          | Rapporto risposte 5xx / totale|

## 3. Esclusioni
Non contano come Downtime:
- Manutenzione Programmata (max 4 ore/mese)
- Forza maggiore (disastri naturali, guerre, pandemie)
- Errori causati dal cliente (input invalidi, superamento rate limit)
- Componenti terze parti fuori dal controllo del provider

## 4. Penalità / Service Credits
| Disponibilità mensile | Credito          |
|-----------------------|------------------|
| 99.0% - 99.49%       | 10% della quota  |
| 95.0% - 98.99%       | 25% della quota  |
| < 95.0%              | 50% della quota  |

## 5. Procedura di reclamo
Il cliente deve aprire un ticket entro 30 giorni dalla fine del mese
in cui si è verificata la violazione, allegando evidenze. Il provider
ha 15 giorni lavorativi per verificare e applicare il credito.

## 6. Reporting
Report mensile inviato entro il 5° giorno lavorativo del mese
successivo, contenente: uptime %, incidenti, RCA per incidenti > 15 min.
```

### 6.3 Strutture di penalità

#### Modello a crediti percentuali (più comune)

```
Se SLA violato:
  credito = percentuale_quota × fattore_violazione

Esempio:
  Quota mensile: €10.000
  SLA: 99.5%
  Disponibilità effettiva: 98.7%
  
  Fascia 95%-99.49% → credito 25%
  Credito = €10.000 × 0.25 = €2.500
```

#### Modello a crediti per minuto

```
Costo per minuto di downtime = quota_mensile / minuti_mese / (1 - SLA_target)

Esempio:
  Quota: €10.000/mese
  SLA: 99.5% → budget downtime = 0.5% × 43.200 min = 216 min
  
  Costo per minuto eccedente: €10.000 / 216 = €46.30/min
  
  Se downtime = 300 min:
  Eccedenza = 300 - 216 = 84 min
  Credito = 84 × €46.30 = €3.889
```

#### Cap sulle penalità

Tutte le strutture SLA includono un cap:

```
Credito massimo = X% della quota mensile (tipicamente 30-50%)
```

Il cap protegge il provider da penalità catastrofiche. Il cliente che vuole protezione oltre il cap necessita di una polizza assicurativa o clausole contrattuali specifiche.

### 6.4 Metriche SLA che evitano ambiguità

Regole per definire metriche SLA non ambigue:

1. **Definire cosa conta come "errore"**: solo 5xx? Anche timeout? Anche risposte parziali?
2. **Definire la granularità temporale**: controllare ogni minuto? Ogni 5 minuti?
3. **Definire il punto di misura**: probe sintetico? Metriche server? Log load balancer?
4. **Definire le esclusioni**: manutenzione? Failover? Degradazione pianificata?
5. **Definire chi misura**: il provider? Il cliente? Un terzo?

---

## Parte 7 — OpenSLO Specification

### 7.1 Cos'è OpenSLO

OpenSLO è una specifica vendor-neutral per definire SLO come codice (SLO-as-Code). Permette di:

- Definire SLI e SLO in formato YAML dichiarativo.
- Versionare gli SLO in Git insieme al codice del servizio.
- Generare automaticamente recording rules Prometheus, dashboard Grafana, alert rules.
- Audit trail delle modifiche agli SLO.

Specifica: https://openslo.com/

### 7.2 Struttura OpenSLO

```yaml
# openslo/api-availability.yaml
apiVersion: openslo/v1
kind: SLO
metadata:
  name: api-gateway-availability
  displayName: "API Gateway — Disponibilità"
  labels:
    team: platform
    tier: "1"
spec:
  description: >-
    L'API Gateway deve rispondere con successo al 99.9%
    delle richieste su una finestra rolling di 28 giorni.
  service: api-gateway
  indicator:
    metadata:
      name: api-gateway-availability-sli
    spec:
      ratioMetric:
        counter: true
        good:
          metricSource:
            type: Prometheus
            spec:
              query: >-
                sum(rate(http_requests_total{
                  job="api-gateway",
                  code!~"5.."
                }[{{.window}}]))
        total:
          metricSource:
            type: Prometheus
            spec:
              query: >-
                sum(rate(http_requests_total{
                  job="api-gateway"
                }[{{.window}}]))
  objectives:
    - displayName: "99.9% availability"
      target: 0.999
      op: gte
  timeWindow:
    - duration: 28d
      isRolling: true
  budgetingMethod: Occurrences
  alertPolicies:
    - kind: AlertPolicy
      metadata:
        name: api-availability-burn-rate
      spec:
        conditions:
          - kind: AlertCondition
            metadata:
              name: fast-burn
            spec:
              severity: critical
              condition:
                kind: Burnrate
                op: gt
                threshold: 14.4
                lookbackWindow: 1h
                alertAfter: 5m
          - kind: AlertCondition
            metadata:
              name: slow-burn
            spec:
              severity: warning
              condition:
                kind: Burnrate
                op: gt
                threshold: 6
                lookbackWindow: 6h
                alertAfter: 30m
```

```yaml
# openslo/api-latency.yaml
apiVersion: openslo/v1
kind: SLO
metadata:
  name: api-gateway-latency
  displayName: "API Gateway — Latenza p99"
spec:
  description: >-
    Il 99.9% delle richieste all'API Gateway deve completarsi
    entro 300ms.
  service: api-gateway
  indicator:
    metadata:
      name: api-gateway-latency-sli
    spec:
      ratioMetric:
        counter: true
        good:
          metricSource:
            type: Prometheus
            spec:
              query: >-
                sum(rate(http_request_duration_seconds_bucket{
                  job="api-gateway",
                  le="0.3"
                }[{{.window}}]))
        total:
          metricSource:
            type: Prometheus
            spec:
              query: >-
                sum(rate(http_request_duration_seconds_count{
                  job="api-gateway"
                }[{{.window}}]))
  objectives:
    - displayName: "99.9% sotto 300ms"
      target: 0.999
  timeWindow:
    - duration: 28d
      isRolling: true
  budgetingMethod: Occurrences
```

```yaml
# openslo/service-definition.yaml
apiVersion: openslo/v1
kind: Service
metadata:
  name: api-gateway
  displayName: "API Gateway"
  labels:
    team: platform
    environment: production
    tier: "1"
spec:
  description: >-
    Gateway API principale. Gestisce autenticazione,
    rate limiting e routing verso i microservizi backend.
```

---

## Parte 8 — Sloth: generatore SLO per Prometheus

### 8.1 Cos'è Sloth

Sloth (https://github.com/slok/sloth) è un tool open-source che genera automaticamente:

- **Recording rules** Prometheus per calcolare SLI a diverse finestre temporali.
- **Alert rules** multi-burn-rate secondo la metodologia Google SRE.
- **Dashboard** Grafana per visualizzare error budget e SLI.

Vantaggi rispetto a scrivere le regole manualmente:

- Elimina errori di calcolo nei burn rate.
- Genera tutte le finestre necessarie in modo consistente.
- Formato YAML dichiarativo e versionabile.
- Supporta plugin per sorgenti SLI custom.

### 8.2 Installazione

```bash
# Via Go
go install github.com/slok/sloth/cmd/sloth@latest

# Via container
docker pull ghcr.io/slok/sloth:latest

# Via Kubernetes (Helm)
helm repo add sloth https://slok.github.io/sloth
helm install sloth sloth/sloth
```

### 8.3 Definizione SLO con Sloth

```yaml
# sloth/api-gateway-slos.yaml
version: "prometheus/v1"
service: "api-gateway"
labels:
  team: platform
  tier: "1"

slos:
  # ---- Availability SLO ----
  - name: "api-availability"
    objective: 99.9
    description: "API Gateway disponibilità: 99.9% richieste senza errori 5xx."
    labels:
      category: availability
    sli:
      events:
        error_query: >-
          sum(rate(http_requests_total{
            job="api-gateway",
            code=~"5.."
          }[{{.window}}]))
        total_query: >-
          sum(rate(http_requests_total{
            job="api-gateway"
          }[{{.window}}]))
    alerting:
      name: ApiGatewayAvailability
      labels:
        team: platform
      annotations:
        runbook: "https://wiki.internal/runbooks/api-availability"
      page_alert:
        labels:
          severity: critical
          routing_key: sre-oncall
      ticket_alert:
        labels:
          severity: warning
          routing_key: sre-ticket

  # ---- Latency SLO ----
  - name: "api-latency"
    objective: 99.9
    description: "API Gateway latenza: 99.9% richieste sotto 300ms."
    labels:
      category: latency
    sli:
      events:
        error_query: >-
          (
            sum(rate(http_request_duration_seconds_count{
              job="api-gateway"
            }[{{.window}}]))
            -
            sum(rate(http_request_duration_seconds_bucket{
              job="api-gateway",
              le="0.3"
            }[{{.window}}]))
          )
        total_query: >-
          sum(rate(http_request_duration_seconds_count{
            job="api-gateway"
          }[{{.window}}]))
    alerting:
      name: ApiGatewayLatency
      labels:
        team: platform
      annotations:
        runbook: "https://wiki.internal/runbooks/api-latency"
      page_alert:
        labels:
          severity: critical
      ticket_alert:
        labels:
          severity: warning

  # ---- Throughput SLO (pipeline batch) ----
  - name: "etl-throughput"
    objective: 99.5
    description: "Pipeline ETL: 99.5% dei batch completati entro la finestra prevista."
    labels:
      category: throughput
    sli:
      events:
        error_query: >-
          sum(rate(etl_batch_failures_total{
            job="etl-pipeline"
          }[{{.window}}]))
        total_query: >-
          sum(rate(etl_batch_runs_total{
            job="etl-pipeline"
          }[{{.window}}]))
    alerting:
      name: EtlThroughput
      page_alert:
        labels:
          severity: critical
      ticket_alert:
        labels:
          severity: warning
```

### 8.4 Generazione regole

```bash
# Genera recording + alert rules Prometheus
sloth generate \
  -i sloth/api-gateway-slos.yaml \
  -o prometheus/rules/generated-slo-rules.yaml

# Verifica regole generate (dry run)
sloth validate -i sloth/api-gateway-slos.yaml

# Genera per tutti i file in una directory
sloth generate \
  -i sloth/ \
  -o prometheus/rules/

# Formato output Kubernetes (PrometheusRule CRD)
sloth generate \
  -i sloth/api-gateway-slos.yaml \
  --slo-period 28d \
  -o prometheus/rules/generated-slo-rules.yaml \
  --extra-labels "cluster=prod-eu-west-1"
```

Output generato (esempio semplificato):

```yaml
# prometheus/rules/generated-slo-rules.yaml (generato da Sloth)
groups:
  - name: sloth-slo-sli-recordings-api-gateway-api-availability
    rules:
      - record: slo:sli_error:ratio_rate5m
        expr: |
          (sum(rate(http_requests_total{job="api-gateway",code=~"5.."}[5m])))
          /
          (sum(rate(http_requests_total{job="api-gateway"}[5m])))
        labels:
          sloth_id: api-gateway-api-availability
          sloth_service: api-gateway
          sloth_slo: api-availability
      # ... record per ogni finestra: 30m, 1h, 2h, 6h, 1d, 3d, 30d

  - name: sloth-slo-meta-recordings-api-gateway-api-availability
    rules:
      - record: slo:objective:ratio
        expr: vector(0.999)
        labels:
          sloth_id: api-gateway-api-availability
      - record: slo:error_budget:ratio
        expr: vector(1 - 0.999)
        labels:
          sloth_id: api-gateway-api-availability
      - record: slo:time_period:days
        expr: vector(30)
        labels:
          sloth_id: api-gateway-api-availability
      - record: slo:current_burn_rate:ratio
        expr: |
          slo:sli_error:ratio_rate5m{sloth_id="api-gateway-api-availability"}
          /
          on() group_left
          slo:error_budget:ratio{sloth_id="api-gateway-api-availability"}
        labels:
          sloth_id: api-gateway-api-availability

  - name: sloth-slo-alerts-api-gateway-api-availability
    rules:
      # Le 4 regole multi-burn-rate generate automaticamente
      - alert: ApiGatewayAvailabilityPageBurnRate
        # ... (regole come quelle della Parte 5.4)
```

---

## Parte 9 — Dashboard Grafana per SLO

### 9.1 Pannelli essenziali

Una dashboard SLO efficace deve contenere:

1. **SLI attuale** (gauge): valore corrente dell'SLI.
2. **SLO target** (linea di riferimento): il target sovrapposto al grafico SLI.
3. **Error budget rimanente** (gauge %): quanto budget resta.
4. **Error budget consumo nel tempo** (time series): trend del consumo.
5. **Burn rate attuale** (stat panel): il burn rate corrente.
6. **Storico incidenti** (annotations): overlay degli incidenti sul grafico.

### 9.2 Query Grafana per pannelli SLO

```promql
# Pannello 1: SLI attuale (availability) — Gauge
1 - slo:http_error_rate:rate30d{job="api-server"}

# Pannello 2: Error budget rimanente — Gauge
slo:error_budget_remaining:ratio{slo="api-availability-99.9"} * 100

# Pannello 3: Burn rate attuale — Stat
slo:http_error_rate:rate1h{job="api-server"}
/
(1 - 0.999)

# Pannello 4: Error budget consumo nel tempo — Time series
1 - slo:error_budget_remaining:ratio{slo="api-availability-99.9"}

# Pannello 5: SLI su diverse finestre — Multi-line
slo:http_error_rate:rate5m{job="api-server"}
slo:http_error_rate:rate1h{job="api-server"}
slo:http_error_rate:rate1d{job="api-server"}
slo:http_error_rate:rate30d{job="api-server"}

# Pannello 6: Latenza p50/p95/p99 — Multi-line
histogram_quantile(0.50, sum(rate(http_request_duration_seconds_bucket{job="api-server"}[5m])) by (le))
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{job="api-server"}[5m])) by (le))
histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket{job="api-server"}[5m])) by (le))
```

### 9.3 Dashboard JSON provisioning (estratto)

```json
{
  "dashboard": {
    "title": "SLO — API Gateway",
    "uid": "slo-api-gateway",
    "tags": ["slo", "sre", "api-gateway"],
    "templating": {
      "list": [
        {
          "name": "job",
          "type": "query",
          "query": "label_values(http_requests_total, job)",
          "current": { "text": "api-gateway", "value": "api-gateway" }
        }
      ]
    },
    "panels": [
      {
        "title": "Availability SLI (30d rolling)",
        "type": "gauge",
        "targets": [
          {
            "expr": "1 - slo:http_error_rate:rate30d{job=\"$job\"}",
            "legendFormat": "Availability"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "min": 0.99,
            "max": 1,
            "thresholds": {
              "steps": [
                { "color": "red", "value": 0 },
                { "color": "orange", "value": 0.995 },
                { "color": "yellow", "value": 0.999 },
                { "color": "green", "value": 0.9995 }
              ]
            },
            "unit": "percentunit",
            "decimals": 4
          }
        },
        "gridPos": { "h": 8, "w": 6, "x": 0, "y": 0 }
      },
      {
        "title": "Error Budget Rimanente",
        "type": "gauge",
        "targets": [
          {
            "expr": "slo:error_budget_remaining:ratio{slo=\"api-availability-99.9\"} * 100",
            "legendFormat": "Budget %"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "min": 0,
            "max": 100,
            "thresholds": {
              "steps": [
                { "color": "red", "value": 0 },
                { "color": "orange", "value": 10 },
                { "color": "yellow", "value": 25 },
                { "color": "green", "value": 50 }
              ]
            },
            "unit": "percent"
          }
        },
        "gridPos": { "h": 8, "w": 6, "x": 6, "y": 0 }
      },
      {
        "title": "Burn Rate Attuale (1h)",
        "type": "stat",
        "targets": [
          {
            "expr": "slo:http_error_rate:rate1h{job=\"$job\"} / (1 - 0.999)",
            "legendFormat": "Burn Rate"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "thresholds": {
              "steps": [
                { "color": "green", "value": 0 },
                { "color": "yellow", "value": 1 },
                { "color": "orange", "value": 3 },
                { "color": "red", "value": 6 }
              ]
            },
            "unit": "short",
            "decimals": 1
          }
        },
        "gridPos": { "h": 8, "w": 6, "x": 12, "y": 0 }
      }
    ]
  }
}
```

---

## Parte 10 — Template documentazione SLO

### 10.1 SLO Document Template

Ogni servizio dovrebbe avere un documento SLO che segue questo template:

```markdown
# SLO Document — [Nome Servizio]

## Metadata
| Campo              | Valore                         |
|--------------------|--------------------------------|
| Servizio           | [nome]                         |
| Owner              | [team]                         |
| Tier               | [1/2/3]                        |
| Ultima revisione   | [data YYYY-MM-DD]              |
| Prossima revisione | [data YYYY-MM-DD]              |
| Approvato da       | [Product Owner + Eng Lead]     |
| SLO dashboard      | [link Grafana]                 |
| Runbook            | [link wiki]                    |

## Descrizione servizio
[2-3 frasi: cosa fa, chi lo usa, quanto è critico]

## Critical User Journeys (CUJ)
1. [CUJ 1: es. "Utente effettua login"]
2. [CUJ 2: es. "Utente visualizza dashboard"]
3. [CUJ 3: es. "Sistema processa pagamento"]

## SLI e SLO

### Availability
- **SLI**: proporzione di richieste non-5xx su totale richieste
- **Target SLO**: ≥ 99.9% su 28 giorni rolling
- **Metodo misura**: metriche Prometheus http_requests_total
- **Punto misura**: load balancer access logs
- **Query**: `1 - (sum(rate(http_requests_total{code=~"5.."}[28d])) / sum(rate(http_requests_total[28d])))`

### Latency
- **SLI**: proporzione di richieste completate sotto 300ms
- **Target SLO**: ≥ 99.9% su 28 giorni rolling
- **Metodo misura**: histogram Prometheus http_request_duration_seconds
- **Query**: vedi recording rule `slo:http_latency_good_rate:rate28d`

## Error Budget
- **Budget**: 0.1% = 40.3 minuti / 28 giorni
- **Policy link**: [link a error budget policy]

## Dipendenze
| Servizio     | SLO atteso | Impatto se down |
|--------------|------------|-----------------|
| Database     | 99.95%     | Servizio down   |
| Auth Service | 99.9%     | Login fallisce  |
| CDN          | 99.99%    | Asset lenti     |

## Alerting
- **14.4x burn rate**: page SRE on-call
- **6x burn rate**: page SRE on-call
- **3x burn rate**: ticket Jira con priorità alta
- **1x burn rate**: ticket Jira con priorità media

## Storico SLO
| Mese        | SLI Availability | SLI Latency | Budget usato |
|-------------|-----------------|-------------|--------------|
| 2026-04     | 99.93%          | 99.95%      | 30%          |
| 2026-03     | 99.87%          | 99.91%      | 130% (MISS)  |
| 2026-02     | 99.95%          | 99.97%      | 50%          |
```

### 10.2 SLO Review Process

La revisione SLO è un processo periodico (consigliato: mensile, minimo trimestrale):

#### Agenda SLO Review Meeting

```
1. Performance report (10 min)
   - SLI attuale vs target per ogni SLO
   - Error budget consumato nel periodo
   - Trend: miglioramento o peggioramento?

2. Incidenti impattanti (15 min)
   - Quali incidenti hanno consumato error budget?
   - RCA completate? Action items aperti?
   - Pattern ricorrenti?

3. SLO appropriateness (10 min)
   - L'SLO è troppo rilassato? (budget mai consumato > 50%)
   - L'SLO è troppo aggressivo? (budget consumato ogni mese)
   - Nuovi CUJ da coprire?
   - SLI da aggiungere/rimuovere?

4. Decisioni (10 min)
   - Modifiche agli SLO per il prossimo periodo
   - Nuovi SLO da definire
   - Investimenti reliability necessari
   - Aggiornamento error budget policy

5. Action items (5 min)
   - Chi fa cosa entro quando
```

#### Criteri per modificare un SLO

| Segnale | Azione suggerita |
|---|---|
| Budget mai consumato > 20% in 6 mesi | Stringi l'SLO (alza il target) |
| SLO violato > 3 mesi su 6 | Rilassa l'SLO o investi in reliability |
| Nuovo CUJ critico non coperto | Aggiungi SLO |
| SLI non correlato con esperienza utente | Cambia l'SLI |
| Dipendenza cambiata (nuova/rimossa) | Ricalcola SLO composito |

---

## Parte 11 — Esempi SLO per tipo di servizio

### 11.1 API REST (e-commerce)

```yaml
service: ecommerce-api
slos:
  - name: checkout-availability
    description: "Il checkout deve essere disponibile al 99.95%"
    objective: 99.95
    sli:
      type: availability
      good: "richieste POST /api/checkout con status 2xx o 3xx"
      total: "tutte le richieste POST /api/checkout"
    window: 28d rolling
    rationale: >
      Il checkout genera revenue diretta. Ogni errore = vendita persa.
      99.95% = max 8.6 minuti di downtime in 28 giorni.

  - name: checkout-latency
    description: "Il checkout deve rispondere sotto 1s al p99"
    objective: 99.5
    sli:
      type: latency
      threshold: 1000ms
      good: "richieste completate sotto 1s"
      total: "tutte le richieste POST /api/checkout"
    window: 28d rolling

  - name: catalog-availability
    description: "Il catalogo prodotti deve essere disponibile al 99.9%"
    objective: 99.9
    sli:
      type: availability
      good: "richieste GET /api/products/* con status 2xx"
      total: "tutte le richieste GET /api/products/*"
    window: 28d rolling
    rationale: >
      Il catalogo è importante ma ha CDN come fallback.
      99.9% è sufficiente con cache davanti.
```

### 11.2 Database PostgreSQL

```yaml
service: postgres-primary
slos:
  - name: db-availability
    objective: 99.95
    sli:
      type: availability
      good: "query completate senza errore di connessione"
      total: "tutte le query inviate"

  - name: db-latency-read
    objective: 99.9
    sli:
      type: latency
      threshold: 50ms
      description: "p99 query SELECT sotto 50ms"

  - name: db-latency-write
    objective: 99.5
    sli:
      type: latency
      threshold: 100ms
      description: "p99 query INSERT/UPDATE sotto 100ms"

  - name: db-replication-freshness
    objective: 99.9
    sli:
      type: freshness
      threshold: 10s
      description: "Replication lag sotto 10 secondi"
      query_prometheus: >
        mysql_slave_seconds_behind_master < 10
```

### 11.3 Pipeline ETL / Batch

```yaml
service: etl-daily-pipeline
slos:
  - name: etl-completeness
    objective: 99.5
    sli:
      type: correctness
      good: "batch completati con successo e dati validati"
      total: "batch schedulati"
    window: 7d rolling
    rationale: >
      Pipeline giornaliera. SLO su 7 giorni perché
      un batch fallito = 1 giorno di dati mancanti.

  - name: etl-freshness
    objective: 99.0
    sli:
      type: freshness
      threshold: 6h
      description: "Dati disponibili entro 6 ore dalla generazione"
```

### 11.4 Message Queue (Kafka)

```yaml
service: kafka-cluster-prod
slos:
  - name: kafka-availability
    objective: 99.99
    sli:
      type: availability
      good: "messaggi prodotti con successo (ack ricevuto)"
      total: "tutti i tentativi di produzione"
    rationale: >
      Kafka è infrastruttura critica condivisa. Il downtime
      impatta a cascata tutti i consumer.

  - name: kafka-consumer-lag
    objective: 99.9
    sli:
      type: freshness
      threshold: 30s
      description: "Consumer lag sotto 30 secondi per tutti i consumer group critici"
      query_prometheus: >
        kafka_consumergroup_lag_seconds < 30
```

### 11.5 CDN / Static Assets

```yaml
service: cdn-static-assets
slos:
  - name: cdn-availability
    objective: 99.99
    sli:
      type: availability
      good: "richieste con status 2xx o 304"
      total: "tutte le richieste (escluse 4xx client error)"

  - name: cdn-latency-ttfb
    objective: 99.5
    sli:
      type: latency
      threshold: 100ms
      description: "Time to First Byte sotto 100ms"

  - name: cdn-cache-hit
    objective: 95.0
    sli:
      type: throughput
      description: "Cache hit rate sopra il 95%"
      query_prometheus: >
        sum(rate(cdn_cache_hits_total[5m]))
        /
        sum(rate(cdn_requests_total[5m]))
```

---

## Parte 12 — Cultura SLO: adozione organizzativa

### 12.1 Maturità SLO nelle organizzazioni

| Livello | Caratteristiche | Segnali |
|---|---|---|
| **0 — Assente** | Nessun SLO definito. Alert solo su infrastruttura (CPU, disco) | On-call reagisce a tutto. Burnout |
| **1 — Iniziale** | SLO esistono su carta, non monitorati. SLA copiati dai vendor | "Abbiamo un SLO ma nessuno lo guarda" |
| **2 — Definito** | SLO monitorati. Error budget calcolato. Alert multi-burn-rate | Team sa quando è sopra/sotto SLO |
| **3 — Gestito** | Error budget policy attiva. Deploy freeze quando necessario | Decisioni basate su dati, non su paura |
| **4 — Ottimizzato** | SLO review regolari. SLO-as-Code. SLO influenzano roadmap | Product Owner usa SLO per prioritizzare |

### 12.2 Percorso di adozione

#### Fase 1: Fondamenta (settimane 1-4)

1. Scegli **un** servizio critico (non tutti).
2. Definisci 1-2 SLI (availability + latency).
3. Misura lo storico per 2-4 settimane.
4. Imposta un SLO realistico (basato sullo storico).
5. Crea una dashboard Grafana con SLI e error budget.

#### Fase 2: Operazionalizzazione (settimane 5-8)

1. Implementa multi-burn-rate alerting.
2. Scrivi una error budget policy.
3. Configura routing alert (page vs ticket).
4. Crea un runbook per ogni alert SLO.
5. Prima SLO review meeting.

#### Fase 3: Scala (settimane 9-16)

1. Estendi a 3-5 servizi.
2. Adotta SLO-as-Code (Sloth o OpenSLO).
3. Automatizza generazione recording/alert rules.
4. Integra SLO nel processo di deploy (gating).
5. Training per dev team su error budget.

#### Fase 4: Cultura (mesi 4-6)

1. SLO review diventa parte dello standup/sprint.
2. Product Owner usa error budget per prioritizzare reliability vs feature.
3. SLO influenzano architettura (quando aggiungere ridondanza).
4. Post-mortem collegano sempre l'impatto all'error budget.
5. Nuovi servizi nascono con SLO definiti dal giorno 1.

### 12.3 Errori comuni nell'adozione

| Errore | Perché è un problema | Soluzione |
|---|---|---|
| Troppi SLO al primo tentativo | Overwhelm, nessuno viene monitorato | Inizia con 1 servizio, 2 SLI |
| SLO copiati da Google/AWS | Non riflettono la tua realtà | Misura storico prima |
| SLO mai revisionati | Diventano irrilevanti | Review mensile nel calendario |
| Error budget policy senza enforcement | Policy su carta, nessuno la rispetta | VP Engineering approva e applica |
| SLO definiti solo dall'engineering | Non allineati al business | Product Owner co-firma |
| Alert troppo rumorosi | Alert fatigue, SLO ignorati | Multi-burn-rate, tuning soglie |
| SLO = 100% | Nessun error budget, zero rischio possibile | Spiega il costo del 100% |
| Confondere SLO con SLA | Target interni troppo rilassati o troppo aggressivi | Documenta la distinzione |

### 12.4 SLO e processo di deploy

L'error budget può fungere da gate per i deploy:

```yaml
# Esempio: pipeline CI/CD con SLO gating
deploy_production:
  stage: deploy
  before_script:
    # Controlla error budget prima del deploy
    - |
      BUDGET=$(curl -s "http://prometheus:9090/api/v1/query" \
        --data-urlencode "query=slo:error_budget_remaining:ratio{slo='api-availability-99.9'}" \
        | jq -r '.data.result[0].value[1]')
      
      if (( $(echo "$BUDGET < 0.10" | bc -l) )); then
        echo "ERROR: Error budget sotto 10% ($BUDGET). Deploy bloccato."
        echo "Contatta SRE Lead per override."
        exit 1
      elif (( $(echo "$BUDGET < 0.25" | bc -l) )); then
        echo "WARNING: Error budget sotto 25% ($BUDGET)."
        echo "Deploy consentito ma richiede approvazione manuale."
        # trigger manual approval gate
      else
        echo "OK: Error budget sufficiente ($BUDGET)."
      fi
  script:
    - kubectl apply -f k8s/deployment.yaml
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
```

---

## Parte 13 — Implementazione end-to-end: caso pratico

### 13.1 Scenario

Un team gestisce un servizio API (`order-service`) con i seguenti requisiti:

- Serve ~5 milioni di richieste al giorno.
- Il servizio è un microservizio Go dietro un Envoy proxy.
- Espone metriche Prometheus via `/metrics`.
- Il team vuole definire SLO e implementare alerting.

### 13.2 Passo 1 — Strumentazione

```go
// metrics.go — metriche Prometheus per SLI
package main

import (
    "github.com/prometheus/client_golang/prometheus"
    "github.com/prometheus/client_golang/prometheus/promauto"
)

var (
    httpRequestsTotal = promauto.NewCounterVec(
        prometheus.CounterOpts{
            Name: "http_requests_total",
            Help: "Total HTTP requests by status code and method",
        },
        []string{"code", "method", "handler"},
    )

    httpRequestDuration = promauto.NewHistogramVec(
        prometheus.HistogramOpts{
            Name:    "http_request_duration_seconds",
            Help:    "HTTP request duration in seconds",
            Buckets: []float64{
                0.005, 0.01, 0.025, 0.05, 0.1,
                0.25, 0.3, 0.5, 1, 2.5, 5, 10,
            },
        },
        []string{"method", "handler"},
    )
)
```

### 13.3 Passo 2 — Definizione SLO con Sloth

```yaml
# sloth/order-service.yaml
version: "prometheus/v1"
service: "order-service"
labels:
  team: commerce
  tier: "1"

slos:
  - name: "order-availability"
    objective: 99.9
    description: "Order service: 99.9% richieste completate senza errore server."
    sli:
      events:
        error_query: >-
          sum(rate(http_requests_total{
            job="order-service",
            code=~"5.."
          }[{{.window}}]))
        total_query: >-
          sum(rate(http_requests_total{
            job="order-service"
          }[{{.window}}]))
    alerting:
      name: OrderServiceAvailability
      labels:
        team: commerce
      annotations:
        runbook: "https://wiki.internal/runbooks/order-availability"
      page_alert:
        labels:
          severity: critical
      ticket_alert:
        labels:
          severity: warning

  - name: "order-latency"
    objective: 99.9
    description: "Order service: 99.9% richieste completate sotto 300ms."
    sli:
      events:
        error_query: >-
          (
            sum(rate(http_request_duration_seconds_count{
              job="order-service"
            }[{{.window}}]))
            -
            sum(rate(http_request_duration_seconds_bucket{
              job="order-service",
              le="0.3"
            }[{{.window}}]))
          )
        total_query: >-
          sum(rate(http_request_duration_seconds_count{
            job="order-service"
          }[{{.window}}]))
    alerting:
      name: OrderServiceLatency
      labels:
        team: commerce
      page_alert:
        labels:
          severity: critical
      ticket_alert:
        labels:
          severity: warning
```

### 13.4 Passo 3 — Genera e applica le regole

```bash
# Genera regole
sloth generate -i sloth/order-service.yaml \
  -o prometheus/rules/order-service-slo.yaml

# Applica regole a Prometheus
cp prometheus/rules/order-service-slo.yaml \
   /etc/prometheus/rules.d/

# Ricarica Prometheus
curl -X POST http://localhost:9090/-/reload

# Verifica che le regole siano caricate
curl -s http://localhost:9090/api/v1/rules \
  | jq '.data.groups[] | select(.name | contains("order"))'
```

### 13.5 Passo 4 — Verifica

```promql
# Verifica SLI availability attuale
1 - slo:sli_error:ratio_rate5m{sloth_service="order-service", sloth_slo="order-availability"}

# Verifica error budget rimanente
slo:error_budget:ratio{sloth_service="order-service"} - slo:sli_error:ratio_rate30d{sloth_service="order-service"}

# Verifica burn rate
slo:current_burn_rate:ratio{sloth_service="order-service"}
```

---

## Parte 14 — Casi avanzati

### 14.1 SLO per servizi asincroni

Per sistemi event-driven (Kafka consumer, worker queue), l'SLI non è basato su HTTP ma su:

```promql
# SLI: proporzione di messaggi processati con successo
sum(rate(messages_processed_total{status="success"}[5m]))
/
sum(rate(messages_processed_total[5m]))

# SLI: freshness — consumer lag sotto soglia
count(kafka_consumergroup_lag_seconds{group="order-processor"} < 30)
/
count(kafka_consumergroup_lag_seconds{group="order-processor"})
```

### 14.2 SLO per frontend (Web Vitals)

Per applicazioni web, gli SLI derivano dai Core Web Vitals:

```promql
# SLI: proporzione di page load con LCP sotto 2.5s
sum(rate(web_vital_lcp_bucket{le="2.5"}[1h]))
/
sum(rate(web_vital_lcp_count[1h]))

# SLI: proporzione di interazioni con INP sotto 200ms
sum(rate(web_vital_inp_bucket{le="0.2"}[1h]))
/
sum(rate(web_vital_inp_count[1h]))
```

> Richiede strumentazione client-side (browser SDK che invia metriche a un collector).

### 14.3 SLO per servizi multi-tier

Quando un servizio ha frontend, backend, e database:

```
Frontend SLO:   99.5% (dipende da backend + CDN)
Backend SLO:    99.9% (dipende da database + cache)
Database SLO:   99.95% (componente più critica)

SLO effettivo end-to-end:
  = 99.5% × 99.9% × 99.95%
  ≈ 99.35%
```

Per misurare l'SLI end-to-end, usa synthetic monitoring:

```yaml
# blackbox-exporter/config.yml
modules:
  http_2xx_300ms:
    prober: http
    timeout: 5s
    http:
      valid_http_versions: ["HTTP/1.1", "HTTP/2.0"]
      valid_status_codes: [200, 201, 301, 302]
      method: GET
      fail_if_body_not_matches_regexp:
        - '"status":"ok"'
      fail_if_ssl_cert_expires_in_less_than: 720h
```

```promql
# SLI sintetico end-to-end
avg_over_time(probe_success{job="blackbox", instance="https://api.example.com/health"}[30d])
```

### 14.4 SLO con degradazione graceful

Alcuni servizi hanno modalità degradate (fallback a cache, risposta parziale). Come contarle nell'SLI?

Approccio: **SLI pesato**.

```
# Definisci pesi per tipo di risposta
  Risposta completa e corretta:      peso 1.0 (successo pieno)
  Risposta da cache (stale < 5 min): peso 0.8 (successo parziale)
  Risposta da cache (stale > 5 min): peso 0.3 (degradata)
  Errore 5xx:                        peso 0.0 (fallimento)

SLI = somma(peso × conteggio) / totale_richieste
```

```promql
# SLI pesato (esempio con label "response_quality")
(
  sum(rate(requests_total{quality="full"}[5m])) * 1.0
  +
  sum(rate(requests_total{quality="cached_fresh"}[5m])) * 0.8
  +
  sum(rate(requests_total{quality="cached_stale"}[5m])) * 0.3
  +
  sum(rate(requests_total{quality="error"}[5m])) * 0.0
)
/
sum(rate(requests_total[5m]))
```

---

## Parte 15 — SLODLC: Service Level Objective Development Lifecycle

### 15.1 Cos'è il SLODLC

Il SLODLC (Service Level Objective Development Lifecycle) è un framework metodologico open-source creato dalla comunità SRE per guidare le organizzazioni nell'adozione strutturata degli SLO. A differenza dell'approccio "definisci un numero e monitora", il SLODLC fornisce un processo iterativo con fasi distinte, worksheet strutturati e punti di decisione chiari.

Il framework è composto da quattro fasi principali:

```
┌───────────────┐     ┌──────────────┐     ┌────────────────┐     ┌──────────────┐
│  1. DISCOVERY │────▶│  2. DESIGN   │────▶│ 3. IMPLEMENT   │────▶│  4. ITERATE  │
│               │     │              │     │                │     │              │
│ Comprendere   │     │ Progettare   │     │ Distribuire    │     │ Rivedere e   │
│ il servizio,  │     │ SLI, SLO,    │     │ in produzione, │     │ migliorare   │
│ gli utenti,   │     │ error budget,│     │ configurare    │     │ ciclicamente │
│ i percorsi    │     │ policy       │     │ monitoring     │     │              │
│ critici       │     │              │     │ e alerting     │     │              │
└───────────────┘     └──────────────┘     └────────────────┘     └──────────────┘
       △                                                                  │
       └──────────────────────────────────────────────────────────────────┘
                              feedback loop continuo
```

### 15.2 Fase 1 — Discovery Worksheet

Il Discovery Worksheet è il primo artefatto da compilare. Il suo scopo è raccogliere tutte le informazioni necessarie prima di definire qualsiasi SLI o SLO.

#### Template Discovery Worksheet

```markdown
# SLODLC Discovery Worksheet — [Nome Servizio]

## 1. Informazioni sul servizio
| Campo                  | Valore                                |
|------------------------|---------------------------------------|
| Nome servizio          |                                       |
| Team proprietario      |                                       |
| Tier (1/2/3)           |                                       |
| Architettura           | [monolite/microservizi/serverless]     |
| Stack tecnologico      |                                       |
| Dipendenze critiche    |                                       |
| Numero utenti stimati  |                                       |
| Traffico medio (req/s) |                                       |

## 2. Contesto di business
- Qual è il valore di business del servizio?
- Chi sono gli utenti principali? (interni/esterni/entrambi)
- Qual è l'impatto finanziario del downtime?
  - Per minuto: €___
  - Per ora: €___
- Esistono requisiti normativi? (GDPR, PCI-DSS, SOC2)
- Esistono SLA esistenti con i clienti?

## 3. Critical User Journeys (CUJ)
Per ogni percorso utente critico, documentare:

### CUJ 1: [Nome]
- **Descrizione:** [cosa fa l'utente]
- **Frequenza:** [quante volte al giorno/settimana]
- **Impatto se fallisce:** [alto/medio/basso] — [descrizione]
- **Dipendenze:** [quali servizi/sistemi coinvolge]
- **Metriche esistenti:** [quali metriche già raccogli per questo percorso]

### CUJ 2: [Nome]
- (stessa struttura)

## 4. Pain points attuali
- Quali sono i problemi di affidabilità più frequenti?
- Quanti incidenti negli ultimi 3 mesi?
- Qual è il MTTR (Mean Time to Recovery) tipico?
- Ci sono alert esistenti? Sono efficaci o rumorosi?
- Il team soffre di alert fatigue?

## 5. Aspettative e vincoli
- Qual è il livello di affidabilità atteso dagli utenti?
- Ci sono finestre di manutenzione concordate?
- Il servizio ha una modalità di degradazione graceful?
- Budget disponibile per miglioramenti di reliability?

## 6. Dati storici
- Disponibilità misurata negli ultimi 30/60/90 giorni: ___%
- Latenza p99 misurata: ___ms
- Numero di incidenti per mese: ___
- Error budget policy esistente: [sì/no]
```

### 15.3 Fase 2 — Design Worksheet

Dopo la discovery, si passa alla progettazione di SLI e SLO concreti.

#### Template Design Worksheet

```markdown
# SLODLC Design Worksheet — [Nome Servizio]

## SLI/SLO Specification #1

### SLI Definition
| Campo                 | Valore                                     |
|-----------------------|--------------------------------------------|
| Nome SLI              | [es. api-availability]                     |
| Categoria             | [availability/latency/freshness/etc.]      |
| Descrizione           | [cosa misura, in linguaggio non tecnico]   |
| Formula               | [eventi buoni / eventi totali]             |
| Definizione "buono"   | [status 2xx/3xx]                           |
| Definizione "totale"  | [tutte le richieste, escluse health check] |
| Punto di misura       | [LB / app / client RUM]                   |
| Filtri                | [escludi endpoint interni, health check]   |
| Sorgente dati         | [Prometheus / Datadog / altro]             |

### SLO Target
| Campo                 | Valore                     |
|-----------------------|----------------------------|
| Target                | [es. 99.9%]                |
| Finestra temporale    | [28 giorni rolling]        |
| Giustificazione       | [perché questo target]     |
| Baseline storico      | [valore misurato]          |
| SLA collegato         | [se esiste, quale target]  |

### Error Budget
| Campo                   | Valore                          |
|-------------------------|---------------------------------|
| Budget (%)              | [es. 0.1%]                      |
| Budget (minuti/28gg)    | [es. 40.3 minuti]              |
| Budget (richieste/gg)   | [calcolato su traffico medio]  |
| Policy level green      | [>50% rimanente: ops normali]  |
| Policy level yellow     | [25-50%: review pre-deploy]    |
| Policy level orange     | [10-25%: feature freeze]       |
| Policy level red        | [<10%: deploy freeze]          |

### Alerting
| Burn rate | Finestra    | Severity | Azione              |
|-----------|-------------|----------|----------------------|
| 14.4x     | 5m + 1h     | critical | Page on-call         |
| 6x        | 30m + 6h    | critical | Page on-call         |
| 3x        | 2h + 1d     | warning  | Ticket priorità alta |
| 1x        | 6h + 3d     | warning  | Ticket priorità media|
```

### 15.4 Fase 3 — Implementation Checklist

```markdown
# SLODLC Implementation Checklist — [Nome Servizio]

## Pre-implementazione
- [ ] Discovery worksheet completato e approvato
- [ ] Design worksheet completato e approvato
- [ ] SLI/SLO specification firmata da Product Owner + Eng Lead
- [ ] Metriche sorgente verificate in produzione (non vuote)
- [ ] Strumentazione aggiunta dove mancante

## Monitoring
- [ ] Recording rules Prometheus create (manuale o via Sloth/Pyrra)
- [ ] Recording rules validate con `promtool check rules`
- [ ] Recording rules caricate in Prometheus (verify via API)
- [ ] Valori SLI verificati non-zero su tutte le finestre

## Alerting
- [ ] Alert rules multi-burn-rate create
- [ ] Alert rules validate con `promtool check rules`
- [ ] Routing Alertmanager configurato (page → PagerDuty, ticket → Jira)
- [ ] Inhibit rules configurate (critical sopprime warning)
- [ ] Test di fire degli alert (simulazione)

## Dashboard
- [ ] Dashboard Grafana creata con pannelli obbligatori
- [ ] Gauge SLI attuale funzionante
- [ ] Gauge error budget rimanente funzionante
- [ ] Time series burn rate funzionante
- [ ] Annotations incidenti configurate

## Documentazione
- [ ] SLO Document creato (template Parte 10.1)
- [ ] Error budget policy scritta e approvata
- [ ] Runbook per ogni alert SLO creato
- [ ] Data prossima SLO review fissata nel calendario

## Go-live
- [ ] Prima SLO review meeting schedulata (dopo 2 settimane)
- [ ] Stakeholder notificati
- [ ] Baseline storico registrato
```

### 15.5 Fase 4 — Iterate: revisione periodica

La fase di iterazione è un ciclo continuo. Ogni revisione periodica produce tre possibili outcome:

1. **Conferma**: l'SLO è appropriato, nessuna modifica.
2. **Aggiustamento**: il target viene modificato (stretto o rilassato).
3. **Sostituzione**: l'SLI viene cambiato perché non correla più con l'esperienza utente.

Template per il report di iterazione:

```markdown
# SLO Iteration Report — [Servizio] — [Data]

## Performance nel periodo
| SLO             | Target | Raggiunto | Budget usato |
|-----------------|--------|-----------|--------------|
| Availability    | 99.9%  | 99.93%    | 30%          |
| Latency p99     | 99.9%  | 99.85%    | 150% (MISS)  |

## Incidenti impattanti
| Data       | Durata | Budget consumato | RCA completata |
|------------|--------|------------------|----------------|
| 2026-05-03 | 12 min | 30%              | Sì             |
| 2026-05-11 | 22 min | 55%              | In corso       |

## Raccomandazioni
1. [ ] Latency SLO violato: investigare p99 spikes
2. [ ] Considerare l'aggiunta di caching per ridurre latenza
3. [ ] Aggiornare runbook con procedura per [caso specifico]

## Decisione
- Availability SLO: **confermato** (performance entro target)
- Latency SLO: **rilassato** a 99.5% fino al completamento
  delle ottimizzazioni di performance
```

---

## Parte 16 — Pyrra: SLO nativi per Kubernetes

### 16.1 Architettura Pyrra

Pyrra è un tool open-source che rende gli SLO con Prometheus gestibili, accessibili e facili da usare. A differenza di Sloth (che genera file YAML statici), Pyrra opera come controller Kubernetes con una UI web integrata.

```
┌──────────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                             │
│                                                                  │
│  ┌─────────────────────┐    ┌──────────────────────────────────┐ │
│  │ ServiceLevelObjective│    │        Pyrra Controller          │ │
│  │  (Custom Resource)   │───▶│                                  │ │
│  │                      │    │  Watches CRDs → Generates:       │ │
│  └─────────────────────┘    │  • PrometheusRule (recording)    │ │
│                              │  • PrometheusRule (alerting)     │ │
│                              └──────────┬───────────────────────┘ │
│                                         │                         │
│  ┌─────────────────────┐    ┌──────────▼───────────────────────┐ │
│  │   Prometheus         │◀───│     PrometheusRule CRDs          │ │
│  │   (Operator-managed) │    │  (auto-generated by Pyrra)       │ │
│  └──────────┬──────────┘    └──────────────────────────────────┘ │
│             │                                                     │
│  ┌──────────▼──────────┐                                         │
│  │    Pyrra API/UI      │    ← Dashboard web per SLO status      │
│  │    (port 9099)       │                                         │
│  └─────────────────────┘                                         │
└──────────────────────────────────────────────────────────────────┘
```

### 16.2 Tipi di SLO supportati

Pyrra supporta quattro tipi di indicatori SLI:

| Tipo | Descrizione | Uso tipico |
|---|---|---|
| **ratio** | Rapporto tra counter buoni e totali | Availability, error rate |
| **latency** | Basato su histogram bucket (classic) | Latenza con histogram tradizionali |
| **latencyNative** | Basato su native histogram | Latenza con histogram esponenziali |
| **bool_gauge** | Gauge booleano (0 o 1) | Stato up/down, health check |

### 16.3 Installazione Pyrra

```bash
# Installazione via Helm
helm repo add pyrra https://pyrra-dev.github.io/pyrra
helm repo update

helm install pyrra pyrra/pyrra \
  --namespace monitoring \
  --create-namespace \
  --set image.tag=v0.8.0 \
  --set prometheusUrl=http://prometheus-operated:9090 \
  --set prometheusExternalUrl=https://prometheus.internal

# Installazione manuale (kubectl)
kubectl apply -f https://raw.githubusercontent.com/pyrra-dev/pyrra/main/config/crd/bases/pyrra.dev_servicelevelobjectives.yaml
kubectl apply -f https://raw.githubusercontent.com/pyrra-dev/pyrra/main/config/default/
```

### 16.4 Definizione SLO con CRD Pyrra

```yaml
# pyrra/api-gateway-availability.yaml
apiVersion: pyrra.dev/v1alpha1
kind: ServiceLevelObjective
metadata:
  name: api-gateway-availability
  namespace: monitoring
  labels:
    pyrra.dev/team: platform
    pyrra.dev/tier: "1"
spec:
  target: "99.9"
  window: 4w
  description: >-
    L'API Gateway deve rispondere con successo al 99.9%
    delle richieste su una finestra rolling di 28 giorni.
  indicator:
    ratio:
      errors:
        metric: http_requests_total{job="api-gateway",code=~"5.."}
      total:
        metric: http_requests_total{job="api-gateway"}
  alerting:
    name: ApiGatewayAvailability
    disabled: false
    burnrates: true
```

```yaml
# pyrra/api-gateway-latency.yaml
apiVersion: pyrra.dev/v1alpha1
kind: ServiceLevelObjective
metadata:
  name: api-gateway-latency
  namespace: monitoring
spec:
  target: "99.9"
  window: 4w
  description: >-
    Il 99.9% delle richieste all'API Gateway deve completarsi
    entro 300ms.
  indicator:
    latency:
      success:
        metric: http_request_duration_seconds_bucket{job="api-gateway",le="0.3"}
      total:
        metric: http_request_duration_seconds_count{job="api-gateway"}
  alerting:
    name: ApiGatewayLatency
```

```yaml
# pyrra/database-health.yaml
apiVersion: pyrra.dev/v1alpha1
kind: ServiceLevelObjective
metadata:
  name: database-primary-health
  namespace: monitoring
spec:
  target: "99.95"
  window: 4w
  description: "Il database primario deve essere raggiungibile al 99.95%."
  indicator:
    bool_gauge:
      metric: pg_up{job="postgres-primary"}
  alerting:
    name: DatabasePrimaryHealth
```

### 16.5 Pyrra con native histograms

A partire dalla versione 0.8+, Pyrra supporta native histograms di Prometheus, che offrono vantaggi significativi per gli SLI di latenza:

```yaml
# pyrra/api-latency-native-histogram.yaml
apiVersion: pyrra.dev/v1alpha1
kind: ServiceLevelObjective
metadata:
  name: api-latency-native
  namespace: monitoring
spec:
  target: "99.9"
  window: 4w
  description: "Latenza API sotto 300ms usando native histograms."
  indicator:
    latencyNative:
      latency: "0.3"
      total:
        metric: http_request_duration_seconds{job="api-gateway"}
```

Vantaggi dei native histograms per SLO:

- **Risoluzione dinamica**: i bucket si adattano automaticamente alla distribuzione dei dati.
- **Nessuna riconfigurazione**: se la soglia SLO cambia (es. da 300ms a 200ms), non serve modificare la strumentazione.
- **Riduzione cardinalità**: ~10x meno serie temporali rispetto agli histogram classici.
- **Precisione superiore**: i bucket esponenziali forniscono una risoluzione più fine vicino alla soglia SLO.

### 16.6 Confronto Sloth vs Pyrra

| Aspetto | Sloth | Pyrra |
|---|---|---|
| **Architettura** | CLI, generazione statica | Controller Kubernetes + UI web |
| **Input** | File YAML | CRD Kubernetes |
| **Output** | File YAML (rules) | PrometheusRule CRD (auto-applicati) |
| **UI** | Nessuna (solo CLI) | Dashboard web integrata |
| **Native histograms** | Non supportati | Supportati (latencyNative) |
| **SLI plugins** | Sì (Go plugins) | No |
| **Grouping per label** | Manuale (duplicare SLO spec) | Automatico (group by label) |
| **Dipendenze** | Nessuna (binary standalone) | Kubernetes + Prometheus Operator |
| **Ideale per** | CI/CD pipeline, GitOps | Cluster Kubernetes con Operator |
| **Maturità** | Stabile, ampia adozione | Stabile, community in crescita |

**Raccomandazione**: usa Sloth per ambienti non-Kubernetes o quando preferisci il workflow GitOps (commit YAML → pipeline genera regole). Usa Pyrra quando hai Prometheus Operator e vuoi una UI web per gestire gli SLO visivamente.

---

## Parte 17 — Prometheus Native Histograms per SLO

### 17.1 Il problema degli histogram classici

Gli histogram classici di Prometheus richiedono la definizione statica dei bucket al momento della strumentazione:

```go
// Histogram classico: bucket definiti staticamente
httpRequestDuration = promauto.NewHistogramVec(
    prometheus.HistogramOpts{
        Name:    "http_request_duration_seconds",
        Buckets: []float64{0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10},
    },
    []string{"method", "handler"},
)
```

Problemi:

1. **Bucket mal configurati**: se la soglia SLO è 300ms ma non c'è un bucket a 0.3s, la misurazione è imprecisa.
2. **Alta cardinalità**: ogni bucket è una serie temporale separata. 11 bucket × 50 handler = 550 serie per questa sola metrica.
3. **Rigidità**: cambiare i bucket richiede modificare il codice sorgente, fare il deploy, e perdere la continuità storica.

### 17.2 Native histograms: soluzione

I native histograms (stabili da PromCon EU 2025) usano bucket esponenziali calcolati automaticamente:

```go
// Native histogram: bucket calcolati automaticamente
httpRequestDuration = promauto.NewHistogramVec(
    prometheus.HistogramOpts{
        Name:                            "http_request_duration_seconds",
        NativeHistogramBucketFactor:     1.1,  // fattore di crescita bucket
        NativeHistogramMaxBucketNumber:  100,  // max bucket per limitare cardinalità
        NativeHistogramMinResetDuration: 1 * time.Hour,
    },
    []string{"method", "handler"},
)
```

Vantaggi per SLO:

- **Qualsiasi soglia SLO** è calcolabile con precisione, senza preconfigurazione dei bucket.
- **~10x riduzione** nel conteggio delle serie temporali.
- **Adattamento dinamico**: la risoluzione si concentra dove i dati sono più densi.

### 17.3 Query PromQL per SLI con native histograms

```promql
# SLI latenza con native histogram: proporzione sotto 300ms
histogram_fraction(0, 0.3,
  sum(rate(http_request_duration_seconds{job="api-gateway"}[5m]))
)

# p99 con native histogram (più preciso degli histogram classici)
histogram_quantile(0.99,
  sum(rate(http_request_duration_seconds{job="api-gateway"}[5m]))
)

# Recording rule per SLI latenza con native histogram
- record: slo:http_latency_native_good:rate5m
  expr: |
    histogram_fraction(0, 0.3,
      sum(rate(http_request_duration_seconds{job="api-gateway"}[5m]))
    )
```

### 17.4 Migrazione da histogram classici a nativi

Strategia di migrazione raccomandata senza perdita di dati:

```go
// Fase 1: dual-write (classico + nativo simultanei)
httpRequestDuration = promauto.NewHistogramVec(
    prometheus.HistogramOpts{
        Name:    "http_request_duration_seconds",
        // Bucket classici mantenuti per compatibilità
        Buckets: []float64{0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10},
        // Native histogram abilitato in parallelo
        NativeHistogramBucketFactor:    1.1,
        NativeHistogramMaxBucketNumber: 100,
    },
    []string{"method", "handler"},
)
```

```yaml
# Fase 2: recording rules parallele per confronto
- record: slo:http_latency_classic:rate5m
  expr: |
    sum(rate(http_request_duration_seconds_bucket{
      job="api-gateway", le="0.3"
    }[5m]))
    /
    sum(rate(http_request_duration_seconds_count{
      job="api-gateway"
    }[5m]))

- record: slo:http_latency_native:rate5m
  expr: |
    histogram_fraction(0, 0.3,
      sum(rate(http_request_duration_seconds{job="api-gateway"}[5m]))
    )

# Fase 3: confronta i valori per 2-4 settimane
# Fase 4: migra gli alert alla versione native
# Fase 5: rimuovi i bucket classici (riduce cardinalità)
```

### 17.5 Costi e considerazioni

A partire da maggio 2025, Grafana Cloud applica un modello di pricing differenziato per i native histograms:

```
serie_native_histogram = numero_bucket_attivi × 0.25

Esempio:
  Histogram classico con 11 bucket: conta come 11 serie
  Native histogram con 40 bucket: conta come 40 × 0.25 = 10 serie

  Risparmio anche con più bucket (e maggiore precisione)
```

Regola pratica: se il numero medio di bucket nativi attivi è inferiore a 4× il numero di bucket classici, il native histogram è più economico.

---

## Parte 18 — SLO con Service Mesh (Istio / Linkerd)

### 18.1 Perché il service mesh è rilevante per gli SLO

Un service mesh (Istio, Linkerd, Cilium) fornisce metriche uniformi per tutti i servizi nel cluster senza modificare il codice applicativo. Questo risolve un problema fondamentale degli SLO nei microservizi: la strumentazione inconsistente.

```
Senza service mesh:
  Servizio A → metriche custom Go
  Servizio B → metriche custom Java
  Servizio C → nessuna metrica (legacy)
  Risultato: SLI incoerenti, gap di copertura

Con service mesh:
  Tutti i servizi → metriche uniformi dal sidecar proxy
  Risultato: SLI consistenti per availability e latenza
             su tutti i servizi, indipendentemente dal linguaggio
```

### 18.2 SLI da Istio

Istio (con Envoy proxy) espone automaticamente metriche standardizzate:

```promql
# SLI availability da metriche Istio
1 - (
  sum(rate(istio_requests_total{
    destination_service="api-gateway.production.svc.cluster.local",
    response_code=~"5..",
    reporter="destination"
  }[5m]))
  /
  sum(rate(istio_requests_total{
    destination_service="api-gateway.production.svc.cluster.local",
    reporter="destination"
  }[5m]))
)

# SLI latenza da metriche Istio (proporzione sotto 300ms)
sum(rate(istio_request_duration_milliseconds_bucket{
  destination_service="api-gateway.production.svc.cluster.local",
  reporter="destination",
  le="300"
}[5m]))
/
sum(rate(istio_request_duration_milliseconds_count{
  destination_service="api-gateway.production.svc.cluster.local",
  reporter="destination"
}[5m]))
```

### 18.3 SLI da Linkerd

Linkerd espone metriche simili con naming diverso:

```promql
# SLI availability da metriche Linkerd
1 - (
  sum(rate(response_total{
    deployment="api-gateway",
    classification="failure",
    direction="inbound"
  }[5m]))
  /
  sum(rate(response_total{
    deployment="api-gateway",
    direction="inbound"
  }[5m]))
)

# SLI latenza da metriche Linkerd
sum(rate(response_latency_ms_bucket{
  deployment="api-gateway",
  direction="inbound",
  le="300"
}[5m]))
/
sum(rate(response_latency_ms_count{
  deployment="api-gateway",
  direction="inbound"
}[5m]))
```

### 18.4 SLO per service-to-service communication

Un vantaggio unico del service mesh è la capacità di definire SLO per la comunicazione tra servizi (non solo client-to-service):

```yaml
# Sloth SLO per traffico inter-service
version: "prometheus/v1"
service: "order-service-to-payment-service"
labels:
  team: commerce
  tier: "1"
  mesh: istio

slos:
  - name: "order-to-payment-availability"
    objective: 99.95
    description: >-
      La comunicazione tra order-service e payment-service
      deve avere successo al 99.95%.
    sli:
      events:
        error_query: >-
          sum(rate(istio_requests_total{
            source_workload="order-service",
            destination_service="payment-service.production.svc.cluster.local",
            response_code=~"5..",
            reporter="source"
          }[{{.window}}]))
        total_query: >-
          sum(rate(istio_requests_total{
            source_workload="order-service",
            destination_service="payment-service.production.svc.cluster.local",
            reporter="source"
          }[{{.window}}]))
    alerting:
      name: OrderToPaymentAvailability
      page_alert:
        labels:
          severity: critical
      ticket_alert:
        labels:
          severity: warning
```

### 18.5 SLO e retry budget nel service mesh

Il service mesh può applicare retry automatici, ma questo interagisce con gli SLO in modo non ovvio:

```
Scenario: order-service chiama payment-service
  - payment-service fallisce il 2% delle richieste
  - Istio retry automatico rende il failure rate visibile all'utente 0.04%
  - SLI misurato lato client (order-service): 99.96%
  - SLI misurato lato server (payment-service): 98%

Problema: quale SLI usare per l'SLO?
```

Raccomandazione:

- **SLO end-to-end** (lato client/utente): misura dopo i retry. Riflette l'esperienza utente reale.
- **SLO per-service** (lato server): misura prima dei retry. Riflette la salute del servizio.
- **Entrambi** sono utili: l'SLO end-to-end per il business, l'SLO per-service per il debugging.

Attenzione al **retry budget**: troppi retry mascherano problemi e amplificano il traffico. Definisci un limite:

```yaml
# Istio: retry con budget limitato
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: payment-service
spec:
  hosts:
    - payment-service
  http:
    - route:
        - destination:
            host: payment-service
      retries:
        attempts: 2
        perTryTimeout: 500ms
        retryOn: "5xx,reset,connect-failure"
      timeout: 2s
```

---

## Parte 19 — SLO e Incident Management

### 19.1 Post-mortem con impatto su error budget

Ogni post-mortem dovrebbe includere una sezione dedicata all'impatto sull'error budget. Questo collega l'analisi tecnica alle conseguenze operative.

#### Template sezione error budget nel post-mortem

```markdown
## Impatto su Error Budget

### SLO impattati
| SLO                | Target | Periodo    | Budget prima | Budget dopo | Consumato |
|--------------------|--------|------------|--------------|-------------|-----------|
| api-availability   | 99.9%  | 28d rolling| 72%          | 38%         | 34%       |
| api-latency-p99    | 99.9%  | 28d rolling| 85%          | 82%         | 3%        |

### Dettaglio impatto
- **Durata incidente:** 18 minuti (13:42–14:00 UTC 2026-05-03)
- **Richieste impattate:** 45.230 su 1.800.000 (2.5%)
- **Error budget consumato (availability):** 34% (14.7 minuti equivalenti)
- **Stato error budget policy:** passato da GREEN a YELLOW

### Conseguenze operative
- Review obbligatoria pre-deploy attivata (policy level yellow)
- Chaos testing sospeso fino a ritorno sopra 50%
- Prossima SLO review anticipata a [data]
```

### 19.2 Classificazione incidenti per impatto su SLO

Non tutti gli incidenti hanno lo stesso impatto sull'error budget. La classificazione per impatto SLO fornisce un framework più utile della severità tradizionale (P1/P2/P3):

| Impatto SLO | Budget consumato | Azione richiesta | Equivalente severità |
|---|---|---|---|
| **Catastrofico** | >50% in un evento | Deploy freeze immediato, escalation VP, post-mortem entro 24h | P1 |
| **Maggiore** | 20-50% in un evento | Feature freeze, post-mortem entro 48h, SLO review | P2 |
| **Significativo** | 5-20% in un evento | Review pre-deploy, post-mortem entro 1 settimana | P2/P3 |
| **Minore** | 1-5% in un evento | Ticket con priorità alta, azione nella sprint corrente | P3 |
| **Trascurabile** | <1% in un evento | Documentare, azione nel backlog | P4 |

### 19.3 SLO-driven incident response

L'incidente viene gestito in funzione dell'impatto sull'error budget, non della sensazione soggettiva di gravità:

```
Flusso di incident response SLO-driven:

1. Alert SLO scatta (burn rate > soglia)
2. On-call verifica:
   a. Quale SLO è impattato?
   b. Qual è il burn rate attuale?
   c. Quanto error budget rimane?
3. Decisioni basate sul budget:
   - Budget > 50%: investiga, fix in orario lavorativo
   - Budget 25-50%: fix prioritario, coinvolgi team
   - Budget 10-25%: escalation, tutte le risorse sul fix
   - Budget < 10%: war room, VP informato, deploy freeze
4. Risoluzione + post-mortem con impatto budget
5. Action items per prevenire ricorrenza
```

### 19.4 Integrazione SLO con tool di incident management

```yaml
# PagerDuty: routing basato su burn rate
# alertmanager.yml
routes:
  - match:
      burn_rate: "14.4x"
    receiver: pagerduty-critical
    group_wait: 0s       # notifica immediata per 14.4x

  - match:
      burn_rate: "6x"
    receiver: pagerduty-high
    group_wait: 30s

  - match_re:
      burn_rate: "(3x|1x)"
    receiver: jira-ticket
    group_wait: 5m

receivers:
  - name: pagerduty-critical
    pagerduty_configs:
      - service_key_file: /etc/secrets/pd-critical
        severity: critical
        description: >-
          SLO {{ .CommonLabels.slo }} burn rate
          {{ .CommonLabels.burn_rate }}.
          Error budget rimanente:
          {{ .CommonAnnotations.budget_remaining }}.
        details:
          runbook: "{{ .CommonAnnotations.runbook_url }}"
          team: "{{ .CommonLabels.team }}"
          impatto: >-
            A questo ritmo il budget si esaurisce in
            {{ .CommonAnnotations.time_to_exhaustion }}.
```

### 19.5 Prevenzione: error budget forecast

Un approccio proattivo prevede il consumo futuro dell'error budget per anticipare violazioni SLO:

```promql
# Stima giorni rimanenti prima di esaurire il budget
# Basata sul burn rate medio degli ultimi 7 giorni
(
  slo:error_budget_remaining:ratio{slo="api-availability-99.9"}
  /
  (
    slo:http_error_rate:rate7d{job="api-server"}
    /
    (1 - 0.999)
  )
) * 30

# Alert se il budget si esaurirà entro 7 giorni al ritmo attuale
- alert: SLOErrorBudgetForecastExhaustion
  expr: |
    (
      slo:error_budget_remaining:ratio{slo="api-availability-99.9"}
      /
      (
        slo:http_error_rate:rate7d{job="api-server"}
        / (1 - 0.999)
      )
    ) * 30 < 7
  for: 1h
  labels:
    severity: warning
  annotations:
    summary: >-
      Error budget previsto esaurito entro 7 giorni
    description: >-
      Al ritmo di consumo attuale, l'error budget per
      {{ $labels.slo }} si esaurirà in {{ $value | humanize }}
      giorni. Intervenire proattivamente.
```

---

## Parte 20 — Dashboard Grafana avanzate per SLO

### 20.1 Pannelli avanzati oltre la base

Oltre ai pannelli essenziali (Parte 9), una dashboard SLO matura include pannelli per analisi avanzata e comunicazione con il management.

#### Pannello: Error Budget Forecast (previsione esaurimento)

```promql
# Giorni stimati prima dell'esaurimento del budget
clamp_min(
  (
    slo:error_budget_remaining:ratio{slo="api-availability-99.9"}
    /
    clamp_min(
      slo:http_error_rate:rate7d{job="api-server"} / (1 - 0.999),
      0.001
    )
  ) * 30,
  0
)
```

Visualizzazione: **Stat panel** con soglie colorate (rosso < 7gg, arancio < 14gg, verde > 14gg).

#### Pannello: Error Budget consumato per incidente

```promql
# Richiede annotations Grafana per gli incidenti
# Mostra il consumo di budget durante ogni finestra di incidente
(
  slo:http_error_rate:rate1h{job="api-server"} - avg_over_time(slo:http_error_rate:rate30d{job="api-server"}[1h])
)
/ (1 - 0.999) * 100
```

Visualizzazione: **Time series** con annotation layer per gli incidenti.

#### Pannello: SLO compliance heatmap

```promql
# Per dashboard multi-servizio: compliance di ogni servizio
# 1 = SLO rispettato, 0 = SLO violato
slo:error_budget_remaining:ratio > 0
```

Visualizzazione: **Status history** o **Table** con semaforo per servizio.

#### Pannello: Burn rate multi-finestra overlay

```promql
# Overlay di burn rate su diverse finestre per pattern recognition
slo:http_error_rate:rate5m{job="api-server"} / (1 - 0.999)   # 5m burn
slo:http_error_rate:rate1h{job="api-server"} / (1 - 0.999)   # 1h burn
slo:http_error_rate:rate6h{job="api-server"} / (1 - 0.999)   # 6h burn
slo:http_error_rate:rate1d{job="api-server"} / (1 - 0.999)   # 1d burn
```

Visualizzazione: **Time series** con 4 linee sovrapposte e threshold a 1x, 3x, 6x, 14.4x.

### 20.2 Dashboard per il management

Una dashboard separata per stakeholder non tecnici deve mostrare lo stato senza complessità PromQL:

```
┌─────────────────────────────────────────────────────────┐
│  SLO Executive Dashboard — Maggio 2026                  │
│                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │ SERVIZI OK  │  │ SERVIZI     │  │ SLO VIOLATI     │ │
│  │     12      │  │ A RISCHIO   │  │      1           │ │
│  │   (verde)   │  │     3       │  │    (rosso)       │ │
│  │             │  │  (giallo)   │  │                  │ │
│  └─────────────┘  └─────────────┘  └─────────────────┘ │
│                                                         │
│  Dettaglio servizi a rischio:                           │
│  ┌─────────────────────────────────────────────────────┐│
│  │ Servizio     │ SLO Target │ Attuale │ Budget │ Trend││
│  ├──────────────┼────────────┼─────────┼────────┼──────┤│
│  │ payment-api  │ 99.95%     │ 99.91%  │ 18% ▼  │ ↓    ││
│  │ search-svc   │ 99.9%      │ 99.88%  │ 32% ▼  │ ↓    ││
│  │ auth-svc     │ 99.9%      │ 99.92%  │ 45%    │ →    ││
│  └─────────────────────────────────────────────────────┘│
│                                                         │
│  SLO violato:                                           │
│  • etl-pipeline: target 99.5%, attuale 98.7%            │
│    Causa: 3 batch falliti la scorsa settimana            │
│    Azione: team data engineering sta indagando           │
└─────────────────────────────────────────────────────────┘
```

Query per il conteggio dei servizi per stato:

```promql
# Conteggio servizi con budget > 50% (OK)
count(slo:error_budget_remaining:ratio > 0.5)

# Conteggio servizi con budget 0-50% (a rischio)
count(slo:error_budget_remaining:ratio > 0 and slo:error_budget_remaining:ratio <= 0.5)

# Conteggio servizi con budget esaurito (violato)
count(slo:error_budget_remaining:ratio <= 0)
```

### 20.3 Grafana SLO App (Grafana Cloud)

Per gli utenti di Grafana Cloud, l'SLO App nativa offre funzionalità avanzate senza configurazione manuale:

- **Creazione SLO via UI**: definisci SLI e target visualmente.
- **Auto-generazione dashboard**: pannelli standard generati automaticamente.
- **Forecast ML**: previsione dell'esaurimento del budget basata su 90 giorni di dati storici.
- **Multidimensional SLO**: SLO che preservano dimensioni (es. SLO per-region, per-customer-tier).
- **Label management**: etichette condivise tra alert, incidenti e SLO.

Esempio di SLO multidimensionale:

```
SLO: api-availability con dimensione "region"
  → Genera automaticamente SLI per eu-west-1, us-east-1, ap-southeast-1
  → Dashboard con breakdown per region
  → Alert indipendenti per region
```

---

## Parte 21 — Piattaforme SLO commerciali

### 21.1 Panoramica del mercato

Il mercato delle piattaforme SLO è cresciuto significativamente tra il 2024 e il 2026, con soluzioni che vanno dall'open-source al full enterprise:

| Piattaforma | Tipo | Target | Caratteristica distintiva |
|---|---|---|---|
| **Sloth** | Open-source | Team SRE con Prometheus | Generazione statica, SLI plugins |
| **Pyrra** | Open-source | Kubernetes-native | CRD + UI, native histograms |
| **OpenSLO** | Specifica | Standard interoperabilità | Vendor-neutral, YAML spec |
| **Nobl9** | Commerciale | Enterprise | Reliability Center, composite SLO 2.0 |
| **Grafana Cloud SLO** | SaaS | Utenti Grafana | Forecast ML, multidimensional |
| **Datadog SLO** | SaaS | Utenti Datadog | SLO widget integrato |
| **Dynatrace SLO** | SaaS | Enterprise | AI-driven, auto-detection |
| **New Relic SLO** | SaaS | Utenti New Relic | NRQL-based, service maps |
| **Honeycomb SLO** | SaaS | Utenti Honeycomb | Burn alerts, high-cardinality |

### 21.2 Nobl9: Reliability Center

Nobl9 è la piattaforma commerciale SLO più specializzata. Le funzionalità chiave includono:

**Composite SLO 2.0**: combina multipli SLO con SLI da qualsiasi sorgente dati in un indicatore unificato di salute del sistema. Supporta pesi differenziati per dare priorità ai componenti critici.

```
Composite SLO: "Customer Experience"
  ├── api-availability (peso 0.4) — da Prometheus
  ├── checkout-latency  (peso 0.3) — da Datadog
  ├── cdn-availability  (peso 0.2) — da CloudWatch
  └── search-freshness  (peso 0.1) — da Elasticsearch
  = Indicatore unico di esperienza cliente pesato
```

**Reliability Score**: punteggio aggregato calcolato da tutti gli SLO gestiti, progettato per comunicare la reliability a livello esecutivo.

**Multi-data-source**: integra SLI da Prometheus, Datadog, New Relic, Splunk, CloudWatch, BigQuery, Dynatrace, Elasticsearch, e altri — in un'unica piattaforma.

### 21.3 Criteri di scelta

| Criterio | Open-source (Sloth/Pyrra) | SaaS integrato | Enterprise (Nobl9) |
|---|---|---|---|
| **Costo** | Gratuito | Incluso nel SaaS monitoring | Licenza dedicata |
| **Complessità setup** | Media (richiede expertise) | Bassa (nativo) | Bassa (managed) |
| **Flessibilità** | Alta | Media (locked-in al vendor) | Alta (multi-source) |
| **Multi-data-source** | Solo Prometheus | Solo il vendor | Sì, qualsiasi |
| **Governance enterprise** | Limitata | Variabile | Completa (audit, RBAC) |
| **Composite SLO** | Manuale | Alcuni vendor | Nativo, pesato |
| **Scalabilità** | Limitata dalla cardinalità Prometheus | Scalabilità del vendor | Scalabilità enterprise |
| **Ideale per** | Team SRE con Prometheus | Organizzazioni single-vendor | Enterprise multi-vendor |

---

## Parte 22 — SLO per servizi AI/ML

### 22.1 Sfide specifiche

I servizi AI/ML presentano sfide uniche per la definizione di SLO:

1. **Latenza altamente variabile**: l'inferenza di un modello LLM può richiedere da 100ms a 60s a seconda dell'input.
2. **Correttezza soggettiva**: la "correttezza" di una predizione ML non è binaria come un HTTP 200.
3. **Risorse GPU**: la disponibilità dipende da hardware specializzato con failure rate diverso.
4. **Degradazione per model drift**: la qualità del modello può degradare nel tempo senza errori tecnici.
5. **Batch vs real-time**: i pipeline di training hanno requisiti SLO diversi dall'inferenza.

### 22.2 SLI per servizi di inferenza

```yaml
service: ml-inference-api
slos:
  # Availability standard
  - name: inference-availability
    objective: 99.9
    sli:
      type: availability
      good: "richieste con status 2xx e predizione valida"
      total: "tutte le richieste"

  # Latenza con soglie differenziate per tipo di modello
  - name: inference-latency-classification
    objective: 99.5
    sli:
      type: latency
      threshold: 200ms
      filter: 'model_type="classification"'
      description: "Modelli di classificazione sotto 200ms"

  - name: inference-latency-generative
    objective: 95.0
    sli:
      type: latency
      threshold: 5000ms
      filter: 'model_type="generative"'
      description: "Modelli generativi sotto 5s (p95)"

  # Correttezza/qualità del modello
  - name: inference-quality
    objective: 99.0
    sli:
      type: correctness
      description: "Predizioni con confidence score > 0.7"
      query_prometheus: >
        sum(rate(predictions_total{confidence="high"}[1h]))
        /
        sum(rate(predictions_total[1h]))

  # Freshness del modello
  - name: model-freshness
    objective: 99.0
    sli:
      type: freshness
      threshold: 24h
      description: "Il modello in produzione non deve essere più vecchio di 24 ore dall'ultimo training"
      query_prometheus: >
        (time() - model_last_updated_timestamp_seconds) < 86400
```

### 22.3 SLO per pipeline di training

```yaml
service: ml-training-pipeline
slos:
  - name: training-completion
    objective: 99.0
    sli:
      type: correctness
      good: "job di training completati con successo e metriche di qualità sopra soglia"
      total: "job di training schedulati"
    window: 7d rolling

  - name: training-freshness
    objective: 95.0
    sli:
      type: freshness
      threshold: 6h
      description: "Training giornaliero completato entro 6 ore dall'inizio schedulato"

  - name: training-data-quality
    objective: 99.5
    sli:
      type: correctness
      description: "Dataset di training supera tutti i data quality check"
      query_prometheus: >
        sum(rate(data_quality_checks_passed_total[1h]))
        /
        sum(rate(data_quality_checks_total[1h]))
```

---

## Parte 23 — Worksheet di calcolo SLO

### 23.1 Foglio di calcolo: da requisiti di business a SLO target

Usa questo worksheet per derivare il target SLO corretto partendo dai requisiti di business:

```
╔══════════════════════════════════════════════════════════════════╗
║  WORKSHEET: Calcolo SLO target da requisiti di business         ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  1. IMPATTO FINANZIARIO DEL DOWNTIME                            ║
║     Revenue annuale del servizio:        €____________           ║
║     Revenue per ora:                     €____________           ║
║     Costo reputazionale per incidente:   €____________           ║
║                                                                  ║
║  2. UTENTI IMPATTATI                                            ║
║     Utenti totali del servizio:          ____________            ║
║     Utenti concorrenti al picco:         ____________            ║
║     % utenti paganti:                   ____________%            ║
║                                                                  ║
║  3. TOLLERANZA AL DOWNTIME                                      ║
║     Quanto downtime al mese è accettabile per il business?      ║
║     □ 7 ore    (99%)    — tool interni non critici              ║
║     □ 3.5 ore  (99.5%)  — servizi interni, staging             ║
║     □ 43 min   (99.9%)  — API production standard              ║
║     □ 21 min   (99.95%) — SaaS business-critical               ║
║     □ 4.3 min  (99.99%) — fintech, healthcare                  ║
║     □ 26 sec   (99.999%)— telecom core, emergency              ║
║                                                                  ║
║  4. COSTO DELL'AFFIDABILITÀ                                    ║
║     Budget infrastruttura attuale:       €____________/mese      ║
║     Stima per +1 nine:                   €____________/mese      ║
║     Personale SRE/on-call:               __ persone              ║
║                                                                  ║
║  5. STORICO                                                     ║
║     Availability media ultimi 90 giorni: ____________%           ║
║     Numero incidenti ultimi 90 giorni:   ____________            ║
║     MTTR medio:                          ____________ min        ║
║     Incidente più lungo:                 ____________ min        ║
║                                                                  ║
║  6. CALCOLO                                                     ║
║     SLO target = min(storico - margine, tolleranza_business)    ║
║                                                                  ║
║     Storico availability:                ____________%           ║
║     Margine sicurezza (-0.05%):          ____________%           ║
║     Tolleranza business (passo 3):       ____________%           ║
║                                                                  ║
║     ┌─────────────────────────────────────────────┐             ║
║     │  SLO TARGET RACCOMANDATO: ____________%     │             ║
║     └─────────────────────────────────────────────┘             ║
║                                                                  ║
║  7. ERROR BUDGET RISULTANTE                                     ║
║     Error budget (%):                    ____________%           ║
║     Error budget (minuti/30gg):          ____________ min       ║
║     Error budget (richieste/gg):         ____________ errori    ║
║                                                                  ║
║  8. SLA DERIVATO (se necessario)                                ║
║     SLA target = SLO target - margine (0.1-0.5%)               ║
║     SLA target raccomandato:             ____________%           ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

### 23.2 Foglio di calcolo: Error Budget per sprint

Utile per team Agile che vogliono allocare l'error budget tra feature work e reliability:

```
╔══════════════════════════════════════════════════════════════════╗
║  WORKSHEET: Allocazione Error Budget per Sprint                  ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  Sprint: ____________  Durata: __ giorni  Date: _____ — _____   ║
║                                                                  ║
║  1. STATO ERROR BUDGET ALL'INIZIO DELLO SPRINT                  ║
║     SLO: ____________%     Budget totale 30gg: _______ min      ║
║     Budget rimanente: _______%  = _______ minuti                ║
║     Policy level attuale: [GREEN/YELLOW/ORANGE/RED]             ║
║                                                                  ║
║  2. ALLOCAZIONE LAVORO (basata su policy level)                 ║
║                                                                  ║
║     GREEN (>50%):                                               ║
║       Feature work:     ___%  = ___ story points                ║
║       Reliability:      ___%  = ___ story points                ║
║       Toil reduction:   ___%  = ___ story points                ║
║       Chaos engineering: consentito □ sì  □ no                  ║
║                                                                  ║
║     YELLOW (25-50%):                                            ║
║       Feature work:     ___%  = ___ story points                ║
║       Reliability:      ___%  = ___ story points                ║
║       Toil reduction:   ___%  = ___ story points                ║
║       Chaos engineering: □ sospeso                              ║
║                                                                  ║
║     ORANGE (10-25%):                                            ║
║       Feature work:     0%                                      ║
║       Reliability:      ___%  = ___ story points                ║
║       Toil reduction:   ___%  = ___ story points                ║
║       Deploy: solo con approvazione SRE                         ║
║                                                                  ║
║     RED (<10%):                                                 ║
║       Feature work:     0%                                      ║
║       Reliability:      100%  = ___ story points                ║
║       Deploy: freeze totale                                     ║
║                                                                  ║
║  3. DEPLOY PIANIFICATI IN QUESTO SPRINT                         ║
║     | Deploy    | Rischio | Budget stimato | Approvazione |     ║
║     |-----------|---------|----------------|--------------|     ║
║     |           |         |                |              |     ║
║     |           |         |                |              |     ║
║                                                                  ║
║  4. OBIETTIVI RELIABILITY DELLO SPRINT                          ║
║     □ _____________________________________________             ║
║     □ _____________________________________________             ║
║     □ _____________________________________________             ║
║                                                                  ║
║  5. STATO ERROR BUDGET ALLA FINE DELLO SPRINT                   ║
║     Budget rimanente: _______%  = _______ minuti                ║
║     Incidenti durante lo sprint: ___                            ║
║     Budget consumato da incidenti: _______ minuti               ║
║     Note: _______________________________________________       ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

### 23.3 Foglio di calcolo: SLO composito con dipendenze

```
╔══════════════════════════════════════════════════════════════════╗
║  WORKSHEET: Calcolo SLO Composito                                ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  Servizio principale: _________________________                  ║
║                                                                  ║
║  DIPENDENZE E LORO SLO:                                         ║
║  | # | Servizio        | SLO individuale | Critica? | Fallback? ║
║  |---|-----------------|-----------------|----------|-----------|║
║  | 1 |                 |        %        | □ sì □ no| □ sì □ no|║
║  | 2 |                 |        %        | □ sì □ no| □ sì □ no|║
║  | 3 |                 |        %        | □ sì □ no| □ sì □ no|║
║  | 4 |                 |        %        | □ sì □ no| □ sì □ no|║
║  | 5 |                 |        %        | □ sì □ no| □ sì □ no|║
║                                                                  ║
║  CALCOLO SLO COMPOSITO:                                         ║
║                                                                  ║
║  Scenario A — Dipendenze in serie (tutte necessarie):           ║
║    SLO_composito = SLO_1 × SLO_2 × ... × SLO_N                 ║
║    = ______% × ______% × ______% × ______% × ______%           ║
║    = ____________%                                               ║
║                                                                  ║
║  Scenario B — Con fallback (una dipendenza ha backup):          ║
║    SLO_con_fallback = 1 - ((1-SLO_primario) × (1-SLO_fallback))║
║    Dipendenza ___: SLO_effettivo = 1-(1-____%)×(1-____%)       ║
║    = ____________%                                               ║
║    SLO_composito_corretto = ____________%                        ║
║                                                                  ║
║  Scenario C — Con circuit breaker:                              ║
║    La dipendenza non critica ___ ha circuit breaker              ║
║    Se breaker aperto: servizio funziona in modalità degradata   ║
║    SLO availability non impattato dal circuit breaker           ║
║    SLO composito senza la dipendenza non critica:               ║
║    = ____________%                                               ║
║                                                                  ║
║  RISULTATO:                                                     ║
║  ┌─────────────────────────────────────────────────┐            ║
║  │  SLO Composito finale: ____________%            │            ║
║  │  SLO Composito target desiderato: ____________% │            ║
║  │  GAP: ____________%                             │            ║
║  └─────────────────────────────────────────────────┘            ║
║                                                                  ║
║  AZIONI PER COLMARE IL GAP:                                    ║
║  □ Aumentare SLO di ________________ a _______%                 ║
║  □ Aggiungere fallback per _________________                    ║
║  □ Implementare circuit breaker per _________________           ║
║  □ Ridurre il numero di dipendenze sincrone                     ║
║  □ Accettare SLO composito attuale e adeguare SLA              ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## Parte 24 — Canary Deployment e SLO-Gated Release

### 24.1 Canary deployment con verifica SLO

Il canary deployment integrato con la verifica SLO automatizza la decisione di procedere o fare rollback basandosi su metriche oggettive:

```
┌─────────────────────────────────────────────────────────────┐
│                  Canary Deployment con SLO Gate              │
│                                                              │
│  1. Deploy canary (5% traffico)                             │
│     ↓                                                        │
│  2. Attendi periodo di osservazione (10-30 min)             │
│     ↓                                                        │
│  3. Verifica SLI del canary vs baseline:                    │
│     • availability canary ≥ SLO target?                     │
│     • latency p99 canary ≤ soglia SLO?                      │
│     • error rate canary ≤ (1 - SLO)?                        │
│     ↓                                                        │
│  4a. SLI OK → Incrementa traffico (25%, 50%, 100%)         │
│  4b. SLI FAIL → Rollback automatico                        │
│     ↓                                                        │
│  5. Verifica SLI dopo full rollout (30 min)                 │
│     ↓                                                        │
│  6a. SLI OK → Release completata                            │
│  6b. SLI FAIL → Rollback automatico                        │
└─────────────────────────────────────────────────────────────┘
```

### 24.2 Implementazione con Argo Rollouts e Prometheus

```yaml
# argo-rollouts/api-gateway-rollout.yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: api-gateway
spec:
  replicas: 10
  strategy:
    canary:
      canaryService: api-gateway-canary
      stableService: api-gateway-stable
      trafficRouting:
        istio:
          virtualService:
            name: api-gateway-vsvc
      steps:
        # Fase 1: 5% traffico al canary
        - setWeight: 5
        - pause: { duration: 10m }
        # Verifica SLO dopo 10 minuti
        - analysis:
            templates:
              - templateName: slo-verification
            args:
              - name: canary-service
                value: api-gateway-canary
              - name: stable-service
                value: api-gateway-stable

        # Fase 2: 25% traffico se SLO ok
        - setWeight: 25
        - pause: { duration: 15m }
        - analysis:
            templates:
              - templateName: slo-verification

        # Fase 3: 50% traffico
        - setWeight: 50
        - pause: { duration: 15m }
        - analysis:
            templates:
              - templateName: slo-verification

        # Fase 4: 100% traffico
        - setWeight: 100
        - pause: { duration: 30m }
        - analysis:
            templates:
              - templateName: slo-final-verification

---
# argo-rollouts/slo-verification-template.yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: slo-verification
spec:
  args:
    - name: canary-service
    - name: stable-service
  metrics:
    # Verifica 1: availability del canary ≥ SLO
    - name: canary-availability
      interval: 2m
      count: 5
      successCondition: result[0] >= 0.999
      failureLimit: 2
      provider:
        prometheus:
          address: http://prometheus:9090
          query: |
            1 - (
              sum(rate(http_requests_total{
                job="{{args.canary-service}}",
                code=~"5.."
              }[5m]))
              /
              sum(rate(http_requests_total{
                job="{{args.canary-service}}"
              }[5m]))
            )

    # Verifica 2: latenza p99 del canary ≤ 300ms
    - name: canary-latency-p99
      interval: 2m
      count: 5
      successCondition: result[0] <= 0.3
      failureLimit: 2
      provider:
        prometheus:
          address: http://prometheus:9090
          query: |
            histogram_quantile(0.99,
              sum(rate(http_request_duration_seconds_bucket{
                job="{{args.canary-service}}"
              }[5m])) by (le)
            )

    # Verifica 3: canary non peggiore dello stable
    - name: canary-vs-stable-error-rate
      interval: 2m
      count: 5
      successCondition: result[0] <= 1.1
      failureLimit: 2
      provider:
        prometheus:
          address: http://prometheus:9090
          query: |
            (
              sum(rate(http_requests_total{
                job="{{args.canary-service}}",code=~"5.."}[5m]))
              /
              sum(rate(http_requests_total{
                job="{{args.canary-service}}"}[5m]))
            )
            /
            (
              sum(rate(http_requests_total{
                job="{{args.stable-service}}",code=~"5.."}[5m]))
              /
              sum(rate(http_requests_total{
                job="{{args.stable-service}}"}[5m]))
            )
```

### 24.3 GitLab CI/CD con SLO gate

```yaml
# .gitlab-ci.yml
stages:
  - build
  - test
  - slo-check
  - deploy-canary
  - slo-verify-canary
  - deploy-production

slo_pre_deploy_check:
  stage: slo-check
  script:
    - |
      echo "=== SLO Pre-Deploy Check ==="
      
      # Query error budget rimanente
      BUDGET=$(curl -s "${PROMETHEUS_URL}/api/v1/query" \
        --data-urlencode "query=slo:error_budget_remaining:ratio{slo='api-availability-99.9'}" \
        | jq -r '.data.result[0].value[1]')
      
      echo "Error budget rimanente: ${BUDGET}"
      
      # Query burn rate attuale
      BURN_RATE=$(curl -s "${PROMETHEUS_URL}/api/v1/query" \
        --data-urlencode "query=slo:current_burn_rate:ratio{sloth_service='api-gateway'}" \
        | jq -r '.data.result[0].value[1]')
      
      echo "Burn rate attuale: ${BURN_RATE}"
      
      # Decisione
      if (( $(echo "$BUDGET < 0.10" | bc -l) )); then
        echo "BLOCCATO: Error budget sotto 10% (${BUDGET})"
        echo "Policy level: RED — deploy freeze in vigore"
        echo "Contatta SRE Lead per override: ${SRE_LEAD_EMAIL}"
        exit 1
      elif (( $(echo "$BUDGET < 0.25" | bc -l) )); then
        echo "ATTENZIONE: Error budget sotto 25% (${BUDGET})"
        echo "Policy level: ORANGE — richiesta approvazione manuale"
        # Crea merge request comment per approvazione
        curl -s --request POST \
          --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
          "${CI_API_V4_URL}/projects/${CI_PROJECT_ID}/merge_requests/${CI_MERGE_REQUEST_IID}/notes" \
          --data "body=SLO Gate: Error budget al ${BUDGET}%. Approvazione manuale richiesta per procedere con il deploy."
        exit 1
      elif (( $(echo "$BURN_RATE > 3" | bc -l) )); then
        echo "ATTENZIONE: Burn rate elevato (${BURN_RATE}x)"
        echo "Il servizio sta consumando error budget rapidamente"
        echo "Deploy consentito ma richiede monitoring attento"
      else
        echo "OK: Error budget sufficiente (${BUDGET}), burn rate normale (${BURN_RATE}x)"
        echo "Deploy consentito"
      fi
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
```

### 24.4 Error budget come gate per feature flags

```yaml
# feature-flags/slo-gated-features.yaml
# Configurazione per feature flag system (es. LaunchDarkly, Unleash)
features:
  - name: new-checkout-flow
    description: "Nuovo flusso checkout con pagamento one-click"
    slo_gate:
      # Feature attiva solo se error budget > 50%
      condition: "slo:error_budget_remaining:ratio{slo='checkout-availability'} > 0.5"
      check_interval: 5m
      on_budget_low:
        action: disable_feature
        notification: "#team-commerce"
        message: >-
          Feature 'new-checkout-flow' disabilitata automaticamente:
          error budget checkout sotto 50%.

  - name: experimental-search-algorithm
    description: "Nuovo algoritmo di ricerca ML-based"
    slo_gate:
      condition: "slo:error_budget_remaining:ratio{slo='search-availability'} > 0.30"
      check_interval: 10m
      on_budget_low:
        action: reduce_rollout_percentage
        target_percentage: 5
        notification: "#team-search"
```

---

## Esercizi

1. **Lab — definisci SLO per servizio web.** Latency p95 < 500ms, availability 99.9%, error rate < 0.1%.
2. **Lab — Prometheus alert multi-burn-rate.** Implementa 4 regole come tabella sopra.
3. **Stretch — error budget policy.** Quando consumi > 75%, blocco deploys non critici. Documenta.
4. **Lab — SLO-as-Code con Sloth.** Definisci 2 SLO per un servizio a scelta. Genera le regole e importale in Prometheus. Verifica che le recording rules producano valori validi.
5. **Lab — Dashboard SLO Grafana.** Crea una dashboard con: gauge SLI, gauge error budget, time series burn rate, tabella incidenti. Usa le query di questa guida.
6. **Lab — OpenSLO spec.** Scrivi una specifica OpenSLO per un servizio con 3 SLI (availability, latency, freshness). Valida il YAML con un parser OpenSLO.
7. **Lab — Calcolo SLO composito.** Dato un sistema con 4 microservizi (SLO: 99.95%, 99.9%, 99.9%, 99.99%), calcola l'SLO end-to-end. Discuti strategie per migliorarlo (circuit breaker, fallback, retry budget).
8. **Stretch — Error budget gating CI/CD.** Implementa uno script che controlla l'error budget prima del deploy e blocca se sotto il 10%. Testalo con un mock Prometheus API.
9. **Lab — SLO review simulata.** Usando dati fittizi di 3 mesi, conduci un SLO review meeting. Prepara il report, identifica pattern, proponi modifiche agli SLO.
10. **Stretch — SLA design.** Progetta un SLA per un servizio SaaS B2B. Includi: metriche, target, esclusioni, struttura penalità, procedura reclamo. Confrontalo con un SLA reale (AWS, GCP, Azure).

---

## Auto-valutazione

1. SLI vs SLO vs SLA.
2. Error budget: come calcolare?
3. Burn rate 14.4x: cosa significa?
4. Multi-burn-rate: vantaggio vs single?
5. Perché misurare l'SLI al punto più vicino all'utente?
6. Spiega la formula: SLI = eventi buoni / eventi totali.
7. Perché usare percentili (p95, p99) per la latenza e non la media?
8. Cosa succede quando l'error budget si esaurisce?
9. Perché l'SLA target dovrebbe essere meno aggressivo dell'SLO?
10. Come scegliere il numero di "nines" appropriato?
11. Spiega il concetto di SLO composito.
12. Cos'è una recording rule Prometheus e perché è necessaria per gli SLO?
13. Come funziona l'alerting a due finestre (short + long)?
14. Cosa è OpenSLO e perché è utile?
15. Descrivi il processo di SLO review.

---

## Troubleshooting

### T01 — Alert troppo rumorosi (falsi positivi)

**Sintomo:** ricevi page per spike brevi che non impattano l'error budget.

**Causa:** finestra troppo corta o burn rate soglia troppo bassa.

**Soluzione:**
- Verifica che stai usando la doppia finestra (short + long).
- Aumenta il valore `for:` nelle alert rules (es. da 1m a 2m per il 14.4x).
- Controlla che le recording rules siano calcolate correttamente.

```promql
# Debug: confronta error rate su diverse finestre
slo:http_error_rate:rate5m{job="api-server"}
slo:http_error_rate:rate1h{job="api-server"}
slo:http_error_rate:rate1d{job="api-server"}
```

### T02 — Alert non scattano durante un outage

**Sintomo:** servizio down ma nessun alert SLO.

**Causa probabile:**
- Recording rules non caricate.
- Le query usano label errate (job name sbagliato).
- Prometheus non ha abbastanza dati (finestra 1h, Prometheus riavviato 30 min fa).

**Soluzione:**
```bash
# Verifica che le regole siano caricate
curl -s http://localhost:9090/api/v1/rules | jq '.data.groups[].rules[] | select(.name | contains("slo"))'

# Verifica che le recording rules producano valori
curl -s 'http://localhost:9090/api/v1/query?query=slo:http_error_rate:rate5m'

# Verifica i label disponibili
curl -s 'http://localhost:9090/api/v1/label/job/values'
```

### T03 — Error budget mostra valori negativi

**Sintomo:** il gauge error budget è sotto zero.

**Causa:** SLO violato — l'error rate ha superato il budget nella finestra.

**Soluzione:** Non è un bug. Attiva l'error budget policy (deploy freeze). Verifica con:

```promql
# Quanto siamo sotto
slo:error_budget_remaining:ratio{slo="api-availability-99.9"}
# Se il valore è -0.05, abbiamo consumato 105% del budget
```

### T04 — SLI availability sembra troppo alto (> 99.99% costantemente)

**Sintomo:** availability sempre al 99.99%+ ma gli utenti si lamentano.

**Cause probabili:**
- La metrica non cattura tutti gli errori (errori a livello applicazione restituiti come 200).
- Misuri al punto sbagliato (server-side, ma gli errori sono nella rete).
- Health check domina il traffico (1000 health check OK + 10 user request con errori).

**Soluzione:**
- Escludi health check dal calcolo SLI.
- Aggiungi un SLI di latenza (cattura lentezza che l'availability non vede).
- Considera RUM (Real User Monitoring) per catturare errori client-side.

```promql
# Escludi health check
sum(rate(http_requests_total{job="api-server", handler!="/healthz", code=~"5.."}[5m]))
/
sum(rate(http_requests_total{job="api-server", handler!="/healthz"}[5m]))
```

### T05 — Latenza SLI mostra sempre 100% (tutti sotto soglia)

**Sintomo:** l'SLI latenza è sempre al 100%.

**Causa:** soglia troppo alta o bucket histogram troppo grossolani.

**Soluzione:**
- Controlla la distribuzione effettiva della latenza.
- Abbassa la soglia SLI.
- Aggiungi bucket più granulari vicino alla soglia.

```promql
# Vedi distribuzione effettiva
histogram_quantile(0.5, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))
histogram_quantile(0.9, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))
histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))
```

### T06 — Recording rule restituisce "no data"

**Sintomo:** la recording rule non produce dati, le alert rules non funzionano.

**Cause:**
- La metrica sorgente non esiste (il servizio non espone quella metrica).
- I label nella query non corrispondono.
- L'intervallo di valutazione della regola è troppo breve per i dati disponibili.

**Soluzione:**
```promql
# Verifica che la metrica sorgente esiste
http_requests_total{job="api-server"}

# Verifica i label disponibili
count by (code) (http_requests_total{job="api-server"})

# Test manuale della query della recording rule
sum(rate(http_requests_total{job="api-server", code=~"5.."}[5m]))
/
sum(rate(http_requests_total{job="api-server"}[5m]))
```

### T07 — Error budget si resetta a inizio mese

**Sintomo:** l'error budget torna a 100% ogni primo del mese.

**Causa:** stai usando finestra calendar month anziché rolling.

**Soluzione:** passa a rolling 28 giorni. Le query Prometheus con `[28d]` calcolano automaticamente su finestra rolling.

### T08 — SLO composito troppo basso

**Sintomo:** il tuo SLO end-to-end è inaccettabilmente basso perché hai troppe dipendenze.

**Soluzione:**
- Implementa circuit breaker per isolare dipendenze non critiche.
- Aggiungi fallback (cache, default values, graceful degradation).
- Riduci il numero di dipendenze sincrone (usa pattern asincroni).
- Aumenta l'SLO individuale dei componenti più deboli.

### T09 — Alertmanager non invia notifiche SLO

**Sintomo:** gli alert scattano in Prometheus ma non arrivano al canale di notifica.

**Cause:**
- Route non configurata per i label SLO.
- Inhibit rule sopprime l'alert.
- Receiver mal configurato.

**Soluzione:**
```bash
# Verifica gli alert attivi
curl -s http://localhost:9093/api/v2/alerts | jq '.[].labels'

# Verifica il routing
# In alertmanager.yml, assicurati che i label delle regole SLO
# matchino le route configurate (severity: critical → slo-page)

# Verifica inibizioni
curl -s http://localhost:9093/api/v2/silences | jq '.'
```

### T10 — SLI diverso tra Prometheus e il monitoraggio del cliente

**Sintomo:** il tuo SLI dice 99.95%, il cliente misura 99.5%.

**Cause:**
- Punto di misura diverso (tu: server-side; cliente: client-side).
- Esclusioni diverse (tu: escludi manutenzione; cliente: no).
- Finestra temporale diversa.
- Il cliente include errori DNS, TLS, timeout di rete che tu non vedi server-side.

**Soluzione:**
- Allinea la definizione di "errore" con il cliente.
- Aggiungi probe sintetici che simulano la prospettiva del cliente.
- Documenta le differenze di misurazione nell'SLA.

### T11 — Sloth genera regole con errori di sintassi

**Sintomo:** dopo `sloth generate`, Prometheus rifiuta le regole.

**Cause:**
- Template query con sintassi PromQL invalida.
- Caratteri speciali non escapati.
- Versione Sloth incompatibile con il formato Prometheus.

**Soluzione:**
```bash
# Valida il file Sloth prima della generazione
sloth validate -i sloth/my-slos.yaml

# Controlla la sintassi delle regole generate
promtool check rules prometheus/rules/generated-slo-rules.yaml

# Se il problema è nella query, testala manualmente nell'UI Prometheus
```

### T12 — Error budget consumato interamente da un singolo incidente

**Sintomo:** un outage di 45 minuti ha consumato il 100% dell'error budget mensile (SLO 99.9%).

**Analisi:** con SLO 99.9% su 30 giorni, il budget è 43.2 minuti. Un singolo outage di 45 minuti lo esaurisce.

**Soluzioni a lungo termine:**
- Implementa auto-rollback (riduce la durata degli incidenti).
- Aggiungi canary deployment (limita il blast radius).
- Valuta se l'SLO è appropriato (forse 99.5% è sufficiente per il servizio).
- Implementa redundanza per ridurre la probabilità di outage totale.

### T13 — Team non rispetta l'error budget policy

**Sintomo:** l'error budget è esaurito ma i deploy continuano.

**Cause:**
- Policy non ha enforcement tecnico (solo documento).
- Management non la sostiene.
- Dev team non capisce l'error budget.

**Soluzione:**
- Implementa enforcement tecnico (CI/CD gating, vedi Parte 12.4).
- VP Engineering firma la policy e la applica.
- Training team su SLO e error budget.
- Includi la compliance error budget nelle metriche del team.

### T14 — Troppe recording rules, Prometheus rallenta

**Sintomo:** Prometheus diventa lento dopo aver aggiunto recording rules SLO per molti servizi.

**Cause:**
- Troppe serie temporali generate (N servizi × M SLI × K finestre).
- Query delle recording rules troppo pesanti (join su molte label).

**Soluzione:**
- Aggrega le metriche nelle recording rules (usa `without(instance)` per ridurre la cardinalità).
- Riduci il numero di finestre (se non usi l'alert 1x/3d, non generare la recording rule per 3d).
- Usa Thanos/Cortex/Mimir per la retention a lungo termine e tieni Prometheus leggero.
- Verifica la cardinalità:

```promql
# Conteggio serie per regola
count({__name__=~"slo:.*"}) by (__name__)
```

### T15 — SLO inadeguato dopo cambio architettura

**Sintomo:** dopo una migrazione (monolite → microservizi, on-prem → cloud), gli SLO precedenti non funzionano.

**Soluzione:**
- Tratta la migrazione come "nuovo servizio" per gli SLO.
- Misura 2-4 settimane di storico nella nuova architettura.
- Ridefinisci SLI (nuove metriche, nuovi punti di misura).
- Imposta SLO provvisori e fai review dopo 1 mese.
- Aggiorna le dipendenze nel documento SLO.

### T16 — Error budget burn rate spikes durante i deploy

**Sintomo:** ogni deploy causa un breve spike nel burn rate.

**Cause:**
- Pod rolling restart causa connessioni dropped.
- Health check non protegge adeguatamente le richieste in-flight.
- Readiness probe troppo aggressiva.

**Soluzione:**
- Implementa graceful shutdown (drain connections, SIGTERM handling).
- Configura preStop hook in Kubernetes (sleep 5-10s prima di SIGTERM).
- Usa PodDisruptionBudget per limitare il numero di pod riavviati contemporaneamente.
- Configura readiness probe con initialDelaySeconds adeguato.

```yaml
# kubernetes/deployment.yaml — graceful shutdown per SLO
spec:
  template:
    spec:
      terminationGracePeriodSeconds: 30
      containers:
        - name: api-server
          lifecycle:
            preStop:
              exec:
                command: ["/bin/sh", "-c", "sleep 5"]
          readinessProbe:
            httpGet:
              path: /healthz
              port: 8080
            initialDelaySeconds: 10
            periodSeconds: 5
            failureThreshold: 3
          livenessProbe:
            httpGet:
              path: /livez
              port: 8080
            initialDelaySeconds: 15
            periodSeconds: 10
  strategy:
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
```

---

## FAQ

### F01 — Quanti SLO dovrebbe avere un servizio?

Da **2 a 5**. Tipicamente: 1 availability + 1 latency + 1 specifico del dominio (freshness per pipeline, correctness per calcoli).

Più di 5 SLO significa che stai misurando troppo e niente verrà davvero monitorato. Meno di 2 significa che probabilmente ti manca qualcosa di importante.

### F02 — Chi è responsabile degli SLO?

Il **team che possiede il servizio** (dev + SRE). Il Product Owner co-firma la scelta dei target. L'SRE implementa il monitoring. Il dev scrive il codice che rispetta gli SLO.

Non delegare gli SLO a un "team SLO" separato — diventa burocrazia.

### F03 — Quanto spesso devo fare SLO review?

**Mensile** per servizi con SLO attivi. **Trimestrale** per servizi stabili con SLO mai violato. **Immediatamente** dopo un SLO miss o un cambio architetturale.

### F04 — Posso avere SLO diversi per clienti diversi?

Sì. È comune avere **tier di servizio**:

| Tier | SLO Availability | SLO Latency | SLA |
|---|---|---|---|
| Enterprise | 99.99% | p99 < 100ms | Sì, con penalità |
| Business | 99.9% | p99 < 300ms | Sì, crediti |
| Free | 99.5% | p99 < 1s | No SLA |

Richiede routing e misurazione separati per tier.

### F05 — Come gestire le dipendenze esterne (cloud provider, CDN, API terze)?

- Includi il loro SLA nel calcolo SLO composito.
- Non contare sulle loro promesse — misura tu.
- Implementa fallback per dipendenze con SLO < tuo target.
- Documenta le dipendenze nel documento SLO.

### F06 — L'SLO deve essere uguale per tutti gli endpoint?

No. Endpoint critici (checkout, pagamento) possono avere SLO più aggressivi di endpoint secondari (preferenze, avatar).

```yaml
# SLO differenziati per endpoint
slos:
  - name: checkout-availability
    objective: 99.95
    sli:
      filter: 'handler=~"/api/v1/checkout.*"'

  - name: catalog-availability
    objective: 99.9
    sli:
      filter: 'handler=~"/api/v1/catalog.*"'
```

### F07 — Come misurare la disponibilità di un servizio che riceve poco traffico?

Per servizi con poco traffico (< 100 richieste/giorno), l'SLI basato su richieste è statisticamente instabile. Soluzioni:

1. **Synthetic monitoring**: probe sintetici a intervalli regolari (es. ogni 60s).
2. **Finestra più lunga**: usa 28 o 90 giorni per avere un campione più significativo.
3. **Conta minuti di uptime** anziché proporzione di richieste.

### F08 — Error budget e manutenzione programmata?

La manutenzione programmata **non** dovrebbe consumare error budget, ma solo se:

- È comunicata in anticipo.
- Avviene nella finestra di manutenzione definita.
- Non supera la durata prevista.

Tecnica: escludi la finestra di manutenzione dal calcolo SLI con un'annotazione Prometheus o un recording rule che filtra il periodo.

```promql
# SLI che esclude manutenzione programmata
# Usa una metrica booleana che indica se siamo in manutenzione
sum(rate(http_requests_total{code=~"5.."}[5m]) unless on() maintenance_window == 1)
/
sum(rate(http_requests_total[5m]) unless on() maintenance_window == 1)
```

### F09 — Qual è la differenza tra "nines" di disponibilità e uptime?

- **Uptime** = tempo in cui il servizio è "acceso" (binary: on/off).
- **Availability (nines)** = proporzione di richieste servite con successo.

Un servizio può avere 100% uptime ma 99% availability se il 1% delle richieste fallisce anche quando il servizio è attivo (bug, timeout, resource exhaustion).

L'availability è una metrica migliore perché riflette l'esperienza utente reale.

### F10 — Posso usare SLO senza Prometheus?

Sì. I concetti SLO sono agnostici rispetto allo stack di monitoring. Puoi implementarli con:

- **Datadog**: SLO nativi con Datadog SLO widget.
- **New Relic**: SLI/SLO con NRQL queries.
- **Elastic**: SLO con Elastic Observability.
- **CloudWatch**: metriche custom + CloudWatch alarms.
- **Honeycomb**: SLO con burn alerts.

Il vantaggio di Prometheus è l'ecosistema open-source (Sloth, OpenSLO, Grafana).

### F11 — Come gestire SLO in ambienti multi-region?

Opzioni:

1. **SLO globale**: unico SLO calcolato su tutte le region aggregate. Semplice ma può nascondere problemi regionali.
2. **SLO per region**: SLO separato per ogni region. Più preciso ma più SLO da gestire.
3. **SLO ibrido**: SLO globale + alert per region con soglie locali.

```promql
# SLO globale (tutte le region)
1 - sum(rate(http_requests_total{code=~"5.."}[30d]))
    / sum(rate(http_requests_total[30d]))

# SLO per region
1 - sum(rate(http_requests_total{code=~"5..", region="eu-west-1"}[30d]))
    / sum(rate(http_requests_total{region="eu-west-1"}[30d]))
```

### F12 — Error budget e chaos engineering?

L'error budget è il **permesso** per fare chaos engineering. Se hai budget:

- Puoi iniettare fault e misurare la resilienza.
- Se il chaos test consuma budget, è informazione preziosa (il sistema non è abbastanza resiliente).

Se non hai budget:
- **Non** fare chaos testing (rischi di violare l'SLO).
- Concentrati prima sulla reliability.

### F13 — Che strumenti esistono oltre a Sloth per SLO-as-Code?

| Tool | Descrizione | Licenza |
|---|---|---|
| **Sloth** | Genera Prometheus rules da YAML | Apache 2.0 |
| **Pyrra** | SLO per Kubernetes con UI web | Apache 2.0 |
| **OpenSLO** | Specifica vendor-neutral (non un tool) | Apache 2.0 |
| **Google SLO Generator** | Genera SLO per Cloud Monitoring | Apache 2.0 |
| **Nobl9** | Piattaforma SLO commerciale | Proprietario |
| **Dynatrace SLO** | SLO integrati in Dynatrace | Proprietario |

### F14 — Come comunicare lo stato degli SLO al management?

Report mensile con:

1. **Semaforo**: verde (>50% budget), giallo (25-50%), rosso (<25%), nero (esaurito).
2. **Trend**: miglioramento o peggioramento rispetto al mese precedente.
3. **Impatto business**: "3 incidenti hanno impattato X utenti per Y minuti totali".
4. **Action items**: investimenti necessari per mantenere/migliorare l'SLO.

Non mostrare query PromQL al management. Mostra dashboard Grafana con gauge e semafori.

### F15 — Qual è la relazione tra SLO e toil?

Il toil (lavoro ripetitivo manuale) è l'opposto dell'error budget. Se il team spende troppo tempo in toil:

- Non investe in automazione.
- I sistemi non migliorano.
- L'SLO tende a peggiorare nel tempo.

L'error budget policy dovrebbe allocare tempo per ridurre il toil:

```
Se error budget > 50%:
  50% feature work, 30% reliability, 20% toil reduction

Se error budget 25-50%:
  30% feature work, 50% reliability, 20% toil reduction

Se error budget < 25%:
  0% feature work, 70% reliability, 30% toil reduction
```

### F16 — Posso avere SLO per servizi interni (non customer-facing)?

Sì, e dovresti. I servizi interni che supportano i servizi customer-facing devono avere SLO per:

- Garantire che il servizio esterno possa raggiungere il suo SLO.
- Dare visibilità sulla salute dei componenti interni.
- Permettere ai team interni di gestire il loro error budget.

La regola: se il servizio interno ha un'SLO, il suo target deve essere **uguale o superiore** all'SLO del servizio esterno che ne dipende.

### F17 — Come gestire SLO durante una migrazione?

Durante le migrazioni (es. on-prem → cloud, monolite → microservizi):

1. **Prima della migrazione**: documenta l'SLO attuale come baseline.
2. **Durante la migrazione**: rilassa temporaneamente l'SLO (es. da 99.9% a 99.5%), comunicalo agli stakeholder.
3. **Dopo la migrazione**: misura 2-4 settimane, poi imposta il nuovo SLO.
4. **Documenta** la transizione nel documento SLO.

---

## Letture primarie

- Google SRE Book — Implementing SLOs. https://sre.google/sre-book/service-level-objectives/
- Google SRE Workbook — Alerting on SLOs. https://sre.google/workbook/alerting-on-slos/
- Google SRE Workbook — SLO Engineering Case Studies. https://sre.google/workbook/slo-engineering-case-studies/
- OpenSLO Specification. https://openslo.com/
- Sloth — SLO generator per Prometheus. https://github.com/slok/sloth
- Pyrra — SLO con UI per Kubernetes. https://github.com/pyrra-dev/pyrra
- Alex Hidalgo — "Implementing Service Level Objectives" (O'Reilly, 2020). ISBN: 978-1492076803
- Prometheus documentation — Recording rules. https://prometheus.io/docs/prometheus/latest/configuration/recording_rules/
- Prometheus documentation — Alerting rules. https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/

---

## Collegamenti incrociati

- Modulo 07 — `07-monitoraggio-incidenti.md`.
- Modulo 24 — `24-vulnerability-management.md` (SLO per tempi di remediation vulnerabilità).
- Modulo 33 — `33-security-automation-ansible-soar.md` (automazione alerting).

---

## Glossario locale

| Termine | Definizione |
|---|---|
| **SLI** | Service Level Indicator — misurazione quantitativa di un aspetto del servizio percepito dall'utente. Espresso come rapporto: eventi buoni / eventi totali. |
| **SLO** | Service Level Objective — target interno per un SLI. Definisce "quanto bene" il servizio deve performare in una finestra temporale. |
| **SLA** | Service Level Agreement — contratto legale tra provider e cliente che specifica metriche, target e penalità. |
| **Error budget** | Quantità di inaffidabilità tollerata: 1 - SLO target. Rappresenta il "budget" di errori che il team può spendere. |
| **Burn rate** | Velocità di consumo dell'error budget. 1x = consumo uniforme sulla finestra. 14.4x = emergenza. |
| **Multi-burn-rate** | Tecnica di alerting che usa multiple finestre temporali e soglie di burn rate per bilanciare velocità di detection e falsi positivi. |
| **Nines** | Modo di esprimere l'affidabilità: 99.9% = "3 nines", 99.99% = "4 nines". Ogni nine aggiuntiva riduce il downtime ammesso di 10x. |
| **Rolling window** | Finestra temporale calcolata continuamente dagli ultimi N giorni, anziché allineata al calendario. Preferita per SLO. |
| **Recording rule** | Regola Prometheus che pre-calcola e salva il risultato di una query complessa come nuova serie temporale. Essenziale per performance con SLO. |
| **CUJ** | Critical User Journey — percorso utente critico. Ogni SLO dovrebbe essere collegato a uno o più CUJ. |
| **OpenSLO** | Specifica open-source vendor-neutral per definire SLI e SLO in formato YAML dichiarativo. |
| **Sloth** | Tool open-source che genera recording rules e alert rules Prometheus da definizioni SLO YAML. |
| **Toil** | Lavoro operativo ripetitivo, manuale, automabile, reattivo e privo di valore durevole. L'error budget policy dovrebbe allocare tempo per ridurlo. |
| **Synthetic monitoring** | Monitoraggio basato su probe sintetici che simulano il comportamento dell'utente a intervalli regolari. Utile per servizi a basso traffico. |
| **Graceful degradation** | Capacità di un servizio di fornire risposte parziali o da cache anziché errori completi quando una dipendenza fallisce. |
| **SLO composito** | SLO calcolato moltiplicando gli SLO delle dipendenze. Sempre inferiore al singolo SLO più debole della catena. |
| **Error budget policy** | Documento che definisce le azioni da intraprendere quando l'error budget raggiunge determinate soglie (deploy freeze, feature freeze, escalation). |
| **Burn rate alerting** | Tecnica di alerting che misura la velocità di consumo dell'error budget anziché soglie statiche su metriche. |
| **Probe sintetico** | Richiesta HTTP (o altro protocollo) generata automaticamente a intervalli regolari per verificare la disponibilità e latenza di un servizio. |
| **Blackbox exporter** | Componente Prometheus che esegue probe sintetici (HTTP, DNS, TCP, ICMP) verso endpoint esterni, misurando disponibilità e latenza. |
