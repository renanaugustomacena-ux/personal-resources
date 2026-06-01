# ClickHouse — Partizionamento, Chiavi di Ordinamento e Indici

## Partizionamento: Pruning delle Parti

Il partizionamento in ClickHouse è un meccanismo di **physical pruning**: le parti sono organizzate in directory separate per partizione, e le query che filtrano sulla chiave di partizione saltano completamente le partizioni non rilevanti — senza leggere nemmeno il primary index di quelle partizioni.

### Definizione della Chiave di Partizione

```sql
CREATE TABLE events (
    event_date  Date,
    event_time  DateTime,
    user_id     UInt64,
    event       LowCardinality(String),
    country     LowCardinality(FixedString(2)),
    revenue     Decimal(10, 2)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(event_date)  -- partition key
ORDER BY (event_date, user_id, event_time);
```

Con `PARTITION BY toYYYYMM(event_date)`, ogni mese crea una partizione separata. Una query `WHERE event_date = '2024-01-15'` legge solo la partizione `202401`.

### Granularità del Partizionamento

Scegliere la granularità corretta è critico:

| Granularità | Espressione | Pro | Contro |
|-------------|------------|-----|--------|
| Giornaliera | `toYYYYMMDD(ts)` | Pruning preciso | Molte partizioni (365/anno) |
| Settimanale | `toYYYYWeek(ts)` | Bilanciamento | Meno comune |
| Mensile | `toYYYYMM(ts)` | Standard | Partizioni più grandi |
| Annuale | `toYear(ts)` | Poche partizioni | Pruning grossolano |
| Per categoria | `(country, toYYYYMM(ts))` | Pruning per categoria | Molte partizioni |

**Regola pratica**: evitare più di 1000-2000 partizioni per tabella. Ogni partizione ha overhead di gestione. Partizionare per mese è il punto di partenza standard per dati time-series.

### Partizioni Multi-Dimensionali

```sql
-- Partizionamento su più colonne
CREATE TABLE events_multi (
    event_date Date,
    region     LowCardinality(String),
    event_type LowCardinality(String),
    value      Float64
) ENGINE = MergeTree()
PARTITION BY (region, toYYYYMM(event_date))
ORDER BY (event_date, event_type);
```

Query che filtrano su `region = 'EU'` beneficiano del partition pruning.

### Operazioni sulle Partizioni

```sql
-- Visualizzare le partizioni
SELECT
    partition,
    count() as parts,
    sum(rows) as rows,
    formatReadableSize(sum(bytes_on_disk)) as size_on_disk
FROM system.parts
WHERE table = 'events' AND database = 'analytics' AND active = 1
GROUP BY partition
ORDER BY partition;

-- Detach di una partizione (rimozione logica, dati ancora su disco in /detached)
ALTER TABLE events DETACH PARTITION '202312';

-- Drop di una partizione (rimozione fisica, irreversibile)
ALTER TABLE events DROP PARTITION '202312';

-- Attach di una partizione detached
ALTER TABLE events ATTACH PARTITION '202312';

-- Move di una partizione a un'altra tabella (stesso schema)
ALTER TABLE events MOVE PARTITION '202312' TO TABLE events_archive;

-- Replace (atomico): sostituisce partizione in dest con quella da source
ALTER TABLE events_new REPLACE PARTITION '202401' FROM events_old;

-- Freeze (backup immutabile)
ALTER TABLE events FREEZE PARTITION '202401';
-- I dati vengono linkati in /var/lib/clickhouse/shadow/
```

---

## La Chiave di Ordinamento (ORDER BY)

`ORDER BY` è la chiave di sort delle parti su disco. È la struttura dati più importante per le performance — determina l'efficacia dell'indice primario sparso.

### Come Funziona l'Indice Sparso

Con `ORDER BY (event_date, user_id)` e `index_granularity = 8192`:

```
Granule 0:  rows 0-8191    → primary index entry: (2024-01-01, 1001)
Granule 1:  rows 8192-16383 → primary index entry: (2024-01-01, 98432)
Granule 2:  rows 16384-24575 → primary index entry: (2024-01-01, 201567)
...
```

Per una query `WHERE event_date = '2024-01-15' AND user_id = 500000`:
1. Binary search sull'indice primario → identifica i granule rilevanti
2. Legge solo quei granule (non l'intera colonna)
3. Filtra le righe esatte all'interno del granule

**Effetto dell'ordine nella chiave**: il primo campo nella chiave ha il massimo potere di pruning. Il secondo campo filtra solo all'interno dei granule selezionati dal primo. Il terzo filtra all'interno dei granule selezionati dai primi due. E così via.

```sql
-- Se le query filtrano principalmente su (host, metric_name, ts):
ORDER BY (host, metric_name, ts)
-- Una query WHERE host='server1' AND metric_name='cpu' legge pochi granule

-- Se si invertisse:
ORDER BY (ts, host, metric_name)
-- Una query WHERE host='server1' legge TUTTI i granule (ts varia su tutta la tabella)
```

### Scelta della Chiave di Ordinamento

Regole pratiche per definire `ORDER BY`:

1. **Priorità ai filtri più selettivi** nella posizione più a sinistra
2. **Cardinalità crescente** da sinistra a destra è l'anti-pattern comune da evitare — ma dipende dalle query
3. **Timestamp** tipicamente all'ultimo posto: permette range scan efficienti senza impattare il pruning per altre colonne
4. **LowCardinality prima** di String ad alta cardinalità

```sql
-- Schema per metriche di monitoraggio
-- Query tipiche: WHERE host='srv1' AND metric='cpu', WHERE ts BETWEEN ...
ORDER BY (host, metric, ts)

-- Schema per eventi e-commerce
-- Query tipiche: WHERE event_date=... AND user_id=..., WHERE product_id=...
ORDER BY (event_date, user_id, event_time)

-- Schema per log applicativi
-- Query tipiche: WHERE service='api' AND level='ERROR', range su @timestamp
ORDER BY (service, level, timestamp)
```

---

## Indici Secondari (Skip Indexes / Data Skipping Indexes)

L'indice sparso primario funziona solo con la chiave di ordinamento. Gli **skip indexes** (o data skipping indexes) permettono di saltare granule basandosi su colonne non nella chiave di ordinamento.

### Tipi di Skip Index

```sql
-- minmax: memorizza min e max del valore per ogni granule
-- Utile per colonne numeriche con range query
ALTER TABLE events ADD INDEX idx_revenue revenue TYPE minmax GRANULARITY 4;

-- set: memorizza l'insieme dei valori unici per ogni granule
-- Utile per colonne a bassa cardinalità con equality/IN query
ALTER TABLE events ADD INDEX idx_event event TYPE set(10) GRANULARITY 4;
-- set(10) = massimo 10 valori unici per granule; se >10, non si costruisce per quel granule

-- bloom_filter: filtro probabilistico per equality/IN su alta cardinalità
ALTER TABLE events ADD INDEX idx_session session_id TYPE bloom_filter(0.01) GRANULARITY 4;
-- 0.01 = 1% false positive rate; più basso = più grande l'indice

-- tokenbf_v1: bloom filter su token di una stringa (full-text search base)
ALTER TABLE events ADD INDEX idx_page page TYPE tokenbf_v1(32768, 3, 0) GRANULARITY 4;
-- 32768 bytes, 3 hash functions, 0 seed

-- ngrambf_v1: N-gram bloom filter per substring search
ALTER TABLE search_logs ADD INDEX idx_query query TYPE ngrambf_v1(4, 32768, 3, 0) GRANULARITY 4;
```

**GRANULARITY N**: l'indice copre N granule (non singole righe). Un granule è 8192 righe di default. `GRANULARITY 4` → un entry dell'indice copre 32768 righe.

### Esempio Pratico con Skip Index

```sql
CREATE TABLE events (
    event_date  Date,
    event_time  DateTime,
    user_id     UInt64,
    session_id  String,
    event       LowCardinality(String),
    url         String,
    revenue     Decimal(10, 2),
    INDEX idx_revenue revenue TYPE minmax GRANULARITY 4,
    INDEX idx_event   event   TYPE set(50) GRANULARITY 4,
    INDEX idx_url     url     TYPE tokenbf_v1(65536, 3, 0) GRANULARITY 4
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(event_date)
ORDER BY (event_date, user_id);

-- Questa query beneficia di idx_revenue: salta granule dove max(revenue)=0
SELECT user_id, sum(revenue) FROM events
WHERE event_date >= '2024-01-01' AND revenue > 100
GROUP BY user_id;

-- Questa query beneficia di idx_event
SELECT count() FROM events WHERE event = 'buy';

-- EXPLAIN per vedere se gli indici vengono usati
EXPLAIN indexes = 1 SELECT ...;
```

---

## Proiezioni (Projections)

Le proiezioni sono sottotabelle materializzate con un diverso ordinamento, mantenute automaticamente sincronizzate con la tabella principale. Eliminano la necessità di tabelle di appoggio separate.

```sql
CREATE TABLE events (
    event_date  Date,
    user_id     UInt64,
    event       LowCardinality(String),
    country     LowCardinality(FixedString(2)),
    revenue     Decimal(10, 2),
    PROJECTION proj_by_country
    (
        SELECT country, toYYYYMM(event_date), sum(revenue), count()
        GROUP BY country, toYYYYMM(event_date)
    ),
    PROJECTION proj_by_event
    (
        SELECT event, event_date, count()
        ORDER BY event, event_date
    )
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(event_date)
ORDER BY (event_date, user_id);
```

ClickHouse sceglie automaticamente la proiezione più efficiente in base alla query. Le proiezioni aumentano lo spazio su disco ma eliminano la necessità di tabelle aggregate separate.

---

## Materialized Views come Indici Alternativi

Un pattern comune per query frequenti su pattern di accesso diversi dalla chiave principale:

```sql
-- Tabella principale ordinata per (event_date, user_id)
CREATE TABLE events (
    event_date Date,
    user_id    UInt64,
    event      LowCardinality(String),
    revenue    Decimal(10, 2)
) ENGINE = MergeTree()
ORDER BY (event_date, user_id);

-- MV che pre-aggrega per country, utile per query analitiche geografiche
CREATE TABLE events_by_country (
    event_date Date,
    country    LowCardinality(FixedString(2)),
    events     AggregateFunction(count),
    revenue    AggregateFunction(sum, Decimal(10, 2))
) ENGINE = AggregatingMergeTree()
ORDER BY (event_date, country);

CREATE MATERIALIZED VIEW mv_events_by_country TO events_by_country AS
SELECT
    event_date,
    country,
    countState() as events,
    sumState(revenue) as revenue
FROM events
GROUP BY event_date, country;
```

La MV viene aggiornata ad ogni INSERT nella tabella `events`, senza overhead di query time.
