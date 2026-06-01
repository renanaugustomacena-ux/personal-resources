# Continuous Aggregate in TimescaleDB

> Autori: Team Data Encyclopedia  
> Ultimo aggiornamento: 2026-05-06  
> Versione: 1.0.0  
> Stato: draft

## Indice
1. Concetto e Motivazione
2. Creazione di una Continuous Aggregate
3. Policy di Refresh
4. Real-Time Aggregates
5. Aggregazioni Gerarchiche

---

## 1. Concetto e Motivazione

### 1.1 Il Problema del Downsampling Costoso

Una delle query più comuni sulle serie temporali è il downsampling: aggregare dati ad alta frequenza in bucket temporali a granularità minore per produrre trend, medie, o statistiche su periodi prolungati. Un dashboard che mostra la temperatura media oraria dell'ultimo anno deve aggregare 525.600 punti (uno al minuto) in 8.760 bucket orari ogni volta che viene caricato. Senza ottimizzazioni, questa query richiede di scansionare l'intera tabella, e con crescita continua del dataset diventa sempre più lenta.

Le **continuous aggregate** di TimescaleDB risolvono questo problema attraverso la materializzazione incrementale: il risultato dell'aggregazione viene pre-calcolato e memorizzato in una vista materializzata apposita. La caratteristica fondamentale che le distingue dalle `MATERIALIZED VIEW` standard di PostgreSQL è l'aggiornamento **incrementale**: quando arrivano nuovi dati, solo i bucket temporali interessati dai nuovi inserimenti vengono ricalcolati, non l'intera vista. Questo rende il refresh economico e praticabile in modo continuo e automatico.

### 1.2 Architettura Interna

Internamente, ogni continuous aggregate è composta da due elementi: una tabella materiale (`_timescaledb_internal._materialized_hypertable_N`) che memorizza i valori aggregati partizionati temporalmente come un'altra hypertable, e una vista che combina i dati materializzati con i dati "freschi" non ancora materializzati nella hypertable originale.

Il meccanismo di refresh usa un **watermark** (linea d'acqua): un puntatore che indica fino a quale punto temporale i dati sono stati materializzati. Ogni nuovo inserimento nella hypertable originale viene registrato in una tabella di invalidazione. Al refresh successivo, TimescaleDB ricalcola solo i bucket che contengono dati modificati dopo l'ultimo watermark.

---

## 2. Creazione di una Continuous Aggregate

### 2.1 Sintassi Base

```sql
-- Continuous aggregate: temperatura media oraria per dispositivo
CREATE MATERIALIZED VIEW telemetria_oraria
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', tempo)  AS ora,
    dispositivo,
    AVG(temperatura)              AS temp_media,
    MIN(temperatura)              AS temp_min,
    MAX(temperatura)              AS temp_max,
    COUNT(*)                      AS campioni
FROM telemetria_sensori
GROUP BY 1, 2
WITH NO DATA;  -- non materializzare subito: aspetta il primo refresh

-- Refresh iniziale (può richiedere tempo su dati storici)
CALL refresh_continuous_aggregate('telemetria_oraria',
    NULL,  -- from: NULL = dall'inizio dei dati
    NULL   -- to: NULL = fino al watermark corrente
);
```

### 2.2 Vincoli e Limitazioni

Le continuous aggregate hanno alcune limitazioni rispetto alle viste standard. Non supportano:
- Subquery nella SELECT list
- Window functions
- Funzioni che non sono aggregate
- Self-join sulla stessa hypertable
- `DISTINCT` (usare `COUNT(DISTINCT col)` invece)
- ORDER BY nella definizione (si usa nell'interrogazione)

Supportano invece tutte le funzioni aggregate di PostgreSQL, le hyperfunctions del toolkit (percentile_agg, state_agg), i JOIN con tabelle ordinarie (non con altre hypertable), e le espressioni nelle colonne SELECT.

```sql
-- Esempio con JOIN verso tabella anagrafica
CREATE MATERIALIZED VIEW metriche_arricchite
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', m.tempo) AS ora,
    m.dispositivo,
    d.location,
    d.tipo,
    AVG(m.temperatura)             AS temp_media
FROM telemetria_sensori m
JOIN dispositivi_anagrafica d ON m.dispositivo = d.id  -- JOIN con tabella ordinaria OK
GROUP BY 1, 2, 3, 4;
```

---

## 3. Policy di Refresh

### 3.1 add_continuous_aggregate_policy

La policy di refresh automatico determina con quale frequenza e su quale finestra temporale la continuous aggregate viene aggiornata. I parametri chiave sono `start_offset` (quanto indietro nel tempo ricalcolare, per gestire l'arrivo di dati in ritardo), `end_offset` (quanto vicino al tempo corrente materializzare, per evitare race condition con inserimenti in corso), e `schedule_interval` (frequenza del refresh).

```sql
-- Refresh ogni ora, ricalcola le ultime 3 ore, non materializzare l'ultima ora
SELECT add_continuous_aggregate_policy('telemetria_oraria',
    start_offset    => INTERVAL '3 hours',
    end_offset      => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour'
);

-- Per aggregazioni giornaliere: refresh ogni giorno, lag di 1 giorno
SELECT add_continuous_aggregate_policy('telemetria_giornaliera',
    start_offset    => INTERVAL '3 days',
    end_offset      => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 day'
);

-- Verifica delle policy configurate
SELECT ca.view_name,
       j.config,
       j.schedule_interval,
       j.next_start
FROM timescaledb_information.continuous_aggregates ca
JOIN timescaledb_information.jobs j 
    ON j.config->>'mat_hypertable_id' = 
       (SELECT id::text FROM _timescaledb_catalog.hypertable 
        WHERE table_name = ca.materialization_hypertable_name)
ORDER BY ca.view_name;
```

### 3.2 Refresh Manuale

In alcuni scenari è necessario forzare il refresh di una continuous aggregate su un intervallo specifico: dopo il caricamento di dati storici, dopo la correzione di errori, o prima di un report critico.

```sql
-- Refresh manuale su un intervallo specifico
CALL refresh_continuous_aggregate('telemetria_oraria',
    '2026-01-01 00:00:00+01',
    '2026-01-08 00:00:00+01'
);

-- Refresh dell'intero storico (operazione costosa!)
CALL refresh_continuous_aggregate('telemetria_oraria', NULL, NULL);
```

---

## 4. Real-Time Aggregates

### 4.1 timescaledb.materialized_only

Per default, le continuous aggregate combinano i dati materializzati con quelli non ancora materializzati (il periodo tra `end_offset` e NOW()). Questo comportamento è controllato dall'opzione `timescaledb.materialized_only`:

```sql
-- Visualizza solo dati materializzati (più veloce, ma può essere stale)
ALTER MATERIALIZED VIEW telemetria_oraria
SET (timescaledb.materialized_only = TRUE);

-- Combina dati materializzati + dati recenti non ancora materializzati (default)
ALTER MATERIALIZED VIEW telemetria_oraria
SET (timescaledb.materialized_only = FALSE);
```

Con `materialized_only = FALSE` (default), una query sulla continuous aggregate produce risultati "real-time": i bucket materializzati vengono letti dalla vista materializzata, mentre i bucket dell'ultimo periodo (entro `end_offset` dal presente) vengono calcolati al volo sulla hypertable originale. Questo garantisce che la continuous aggregate mostri sempre dati aggiornati anche tra un refresh e l'altro.

---

## 5. Aggregazioni Gerarchiche

### 5.1 Continuous Aggregate su Continuous Aggregate

TimescaleDB 2.x supporta le aggregazioni gerarchiche (hierarchical continuous aggregates): una continuous aggregate che aggrega un'altra continuous aggregate invece della hypertable raw. Questo è fondamentale per scalare le dashboard su storici molto lunghi.

```sql
-- Livello 1: aggregazione minuto → ora (sul raw data)
CREATE MATERIALIZED VIEW sensori_orari
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', tempo) AS ora,
    dispositivo,
    AVG(valore)                  AS media,
    percentile_agg(valore)       AS pct_agg,
    COUNT(*)                     AS campioni
FROM telemetria_raw
GROUP BY 1, 2;

-- Livello 2: aggregazione ora → giorno (sulla continuous aggregate oraria)
CREATE MATERIALIZED VIEW sensori_giornalieri
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', ora)          AS giorno,
    dispositivo,
    rollup(pct_agg)                    AS pct_agg,  -- rollup di percentile_agg
    SUM(campioni)                      AS campioni
FROM sensori_orari  -- nota: aggrega la continuous aggregate, non il raw
GROUP BY 1, 2;

-- Livello 3: aggregazione giorno → settimana
CREATE MATERIALIZED VIEW sensori_settimanali
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('7 days', giorno) AS settimana,
    dispositivo,
    rollup(pct_agg)               AS pct_agg,
    SUM(campioni)                 AS campioni
FROM sensori_giornalieri
GROUP BY 1, 2;

-- Query sul livello settimanale: opera su pochissimi dati
SELECT settimana,
       dispositivo,
       approx_percentile(0.99, pct_agg) AS p99
FROM sensori_settimanali
WHERE settimana >= NOW() - INTERVAL '1 year'
GROUP BY 1, 2
ORDER BY 1, p99 DESC;
```

Questo schema gerarchico garantisce che le query sui trend a lungo termine (settimane, mesi) siano sempre sub-secondo, indipendentemente dal volume di dati raw, perché operano su aggregati pre-calcolati a più livelli.

---

*Questo documento fa parte del modulo 09 "Time Series & TimescaleDB" della Data Encyclopedia.*
