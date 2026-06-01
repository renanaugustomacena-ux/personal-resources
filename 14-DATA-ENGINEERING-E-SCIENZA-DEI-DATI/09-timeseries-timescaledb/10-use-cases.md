# Casi d'Uso e Pattern con TimescaleDB

> Autori: Team Data Encyclopedia  
> Ultimo aggiornamento: 2026-05-06  
> Versione: 1.0.0  
> Stato: draft

## Indice
1. IoT e Telemetria Industriale
2. Dati Finanziari e Tick Data
3. Monitoring DevOps e Infrastruttura
4. Smart Energy e Contatori
5. Pattern di Schema Ricorrenti

---

## 1. IoT e Telemetria Industriale

### 1.1 Architettura di Riferimento

Un sistema IoT industriale tipico ha migliaia di sensori che inviano misurazioni a intervalli regolari (da 100ms a minuti). I requisiti sono: ingestione ad alta frequenza senza perdita di dati, query real-time per monitoraggio dashboard, analisi storica per manutenzione predittiva, e retention differenziata (raw data 3 mesi, aggregati 2 anni).

```sql
-- Schema ottimizzato per IoT multi-sensore multi-metrica
CREATE TABLE iot_telemetria (
    tempo        TIMESTAMPTZ      NOT NULL,
    impianto     TEXT             NOT NULL,
    linea        TEXT             NOT NULL,
    dispositivo  TEXT             NOT NULL,
    metrica      TEXT             NOT NULL,
    valore       DOUBLE PRECISION NOT NULL,
    unita        TEXT,
    qualita      SMALLINT         DEFAULT 100
);

SELECT create_hypertable('iot_telemetria', 'tempo',
    chunk_time_interval => INTERVAL '6 hours');  -- chunk piccoli per alta frequenza

-- Indici per i due pattern di accesso principali
CREATE INDEX ON iot_telemetria (dispositivo, metrica, tempo DESC);
CREATE INDEX ON iot_telemetria (impianto, linea, tempo DESC);

-- Compressione automatica dopo 24 ore
ALTER TABLE iot_telemetria SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'dispositivo,metrica',
    timescaledb.compress_orderby   = 'tempo DESC'
);
SELECT add_compression_policy('iot_telemetria', INTERVAL '24 hours');

-- Retention: 90 giorni per raw
SELECT add_retention_policy('iot_telemetria', INTERVAL '90 days');
```

### 1.2 Manutenzione Predittiva

```sql
-- Rilevamento anomalie: valori fuori dal range storico (z-score)
WITH statistiche AS (
    SELECT
        dispositivo,
        metrica,
        AVG(valore)    AS media,
        STDDEV(valore) AS dev_std
    FROM iot_telemetria
    WHERE tempo >= NOW() - INTERVAL '30 days'
      AND qualita >= 80
    GROUP BY dispositivo, metrica
)
SELECT
    t.tempo,
    t.dispositivo,
    t.metrica,
    t.valore,
    ABS(t.valore - s.media) / NULLIF(s.dev_std, 0) AS z_score
FROM iot_telemetria t
JOIN statistiche s USING (dispositivo, metrica)
WHERE t.tempo >= NOW() - INTERVAL '1 hour'
  AND ABS(t.valore - s.media) / NULLIF(s.dev_std, 0) > 3.0  -- oltre 3 sigma
ORDER BY z_score DESC;
```

---

## 2. Dati Finanziari e Tick Data

### 2.1 Schema Tick Data

```sql
-- Tick data per trading algoritmico
CREATE TABLE tick_data (
    tempo       TIMESTAMPTZ      NOT NULL,
    strumento   TEXT             NOT NULL,
    exchange    TEXT             NOT NULL,
    bid         NUMERIC(18, 8)   NOT NULL,
    ask         NUMERIC(18, 8)   NOT NULL,
    ultimo      NUMERIC(18, 8),
    volume      NUMERIC(18, 4),
    tipo        CHAR(1)          -- 'T' trade, 'Q' quote
);

SELECT create_hypertable('tick_data', 'tempo',
    chunk_time_interval => INTERVAL '1 day');

CREATE INDEX ON tick_data (strumento, tempo DESC);
CREATE INDEX ON tick_data (exchange, strumento, tempo DESC);
```

### 2.2 Aggregazioni OHLCV

```sql
-- Candele 5 minuti dal tick data
SELECT
    time_bucket('5 minutes', tempo)    AS candle_time,
    strumento,
    FIRST(ultimo, tempo)               AS open,
    MAX(ultimo)                        AS high,
    MIN(ultimo)                        AS low,
    LAST(ultimo, tempo)                AS close,
    SUM(volume)                        AS volume,
    -- VWAP (Volume Weighted Average Price)
    SUM(ultimo * volume) / NULLIF(SUM(volume), 0) AS vwap
FROM tick_data
WHERE tipo = 'T'  -- solo trade, non quote
  AND strumento = 'BTC-USD'
  AND tempo >= NOW() - INTERVAL '1 day'
GROUP BY 1, 2
ORDER BY 1;

-- Continuous aggregate per candele orarie (pre-calcolate)
CREATE MATERIALIZED VIEW ohlcv_orario
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', tempo)               AS ora,
    strumento,
    FIRST(ultimo, tempo)                       AS open,
    MAX(ultimo)                                AS high,
    MIN(ultimo)                                AS low,
    LAST(ultimo, tempo)                        AS close,
    SUM(volume)                                AS volume
FROM tick_data
WHERE tipo = 'T'
GROUP BY 1, 2;
```

### 2.3 Analisi Statistica

```sql
-- Correlazione tra due strumenti su finestra mobile 30 giorni
SELECT
    time_bucket('1 day', a.tempo) AS giorno,
    CORR(a.rendimento, b.rendimento) AS correlazione
FROM (
    SELECT tempo,
           (LAST(ultimo, tempo) - FIRST(ultimo, tempo)) / FIRST(ultimo, tempo) AS rendimento
    FROM tick_data
    WHERE strumento = 'BTC-USD' AND tipo = 'T'
    GROUP BY time_bucket('1 day', tempo)
) a
JOIN (
    SELECT tempo,
           (LAST(ultimo, tempo) - FIRST(ultimo, tempo)) / FIRST(ultimo, tempo) AS rendimento
    FROM tick_data
    WHERE strumento = 'ETH-USD' AND tipo = 'T'
    GROUP BY time_bucket('1 day', tempo)
) b ON a.tempo = b.tempo
WHERE a.tempo >= NOW() - INTERVAL '30 days'
GROUP BY 1 ORDER BY 1;
```

---

## 3. Monitoring DevOps e Infrastruttura

### 3.1 Schema Metriche Host

```sql
-- Metriche sistema da Telegraf/Node Exporter
CREATE TABLE system_metrics (
    tempo       TIMESTAMPTZ      NOT NULL,
    host        TEXT             NOT NULL,
    environment TEXT             NOT NULL,  -- prod, staging, dev
    metrica     TEXT             NOT NULL,
    valore      DOUBLE PRECISION NOT NULL,
    tags        JSONB
);

SELECT create_hypertable('system_metrics', 'tempo',
    chunk_time_interval => INTERVAL '1 day');

-- Retention: 30 giorni raw, aggregati 1 anno
SELECT add_retention_policy('system_metrics', INTERVAL '30 days');
```

### 3.2 Dashboard SLA e Anomalie

```sql
-- Disponibilità del servizio nell'ultimo mese (uptime %)
WITH stati AS (
    SELECT
        time_bucket('1 hour', tempo) AS ora,
        host,
        AVG(valore) AS cpu_media
    FROM system_metrics
    WHERE metrica = 'cpu_usage_percent'
      AND tempo >= NOW() - INTERVAL '30 days'
    GROUP BY 1, 2
)
SELECT
    host,
    COUNT(*) AS ore_totali,
    COUNT(*) FILTER (WHERE cpu_media < 90) AS ore_normali,
    ROUND(100.0 * COUNT(*) FILTER (WHERE cpu_media < 90) / COUNT(*), 2) AS uptime_pct
FROM stati
GROUP BY host
ORDER BY uptime_pct ASC;
```

---

## 4. Smart Energy e Contatori

### 4.1 Schema Smart Meter

```sql
CREATE TABLE letture_contatori (
    tempo         TIMESTAMPTZ    NOT NULL,
    contatore_id  TEXT           NOT NULL,
    zona          TEXT           NOT NULL,
    energia_kwh   NUMERIC(10,3)  NOT NULL,  -- lettura cumulativa
    potenza_kw    NUMERIC(8,3),
    tensione_v    NUMERIC(6,2),
    corrente_a    NUMERIC(6,2),
    fattore_pot   NUMERIC(4,3)
);

SELECT create_hypertable('letture_contatori', 'tempo',
    chunk_time_interval => INTERVAL '1 week');

ALTER TABLE letture_contatori SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'contatore_id',
    timescaledb.compress_orderby   = 'tempo DESC'
);
SELECT add_compression_policy('letture_contatori', INTERVAL '7 days');
```

### 4.2 Calcolo Consumo

```sql
-- Consumo orario per contatore (differenza tra letture cumulative)
SELECT
    time_bucket('1 hour', tempo) AS ora,
    contatore_id,
    -- Differenza tra ultima e prima lettura nell'ora
    LAST(energia_kwh, tempo) - FIRST(energia_kwh, tempo) AS consumo_kwh
FROM letture_contatori
WHERE tempo >= NOW() - INTERVAL '24 hours'
GROUP BY 1, 2
ORDER BY contatore_id, ora;

-- Peak demand per zona (fascia oraria di punta)
SELECT
    zona,
    EXTRACT(HOUR FROM tempo) AS ora_del_giorno,
    AVG(potenza_kw) AS potenza_media_kw,
    MAX(potenza_kw) AS potenza_picco_kw
FROM letture_contatori
WHERE tempo >= NOW() - INTERVAL '30 days'
  AND EXTRACT(DOW FROM tempo) BETWEEN 1 AND 5  -- lunedì-venerdì
GROUP BY 1, 2
ORDER BY 1, potenza_media_kw DESC;
```

---

## 5. Pattern di Schema Ricorrenti

### 5.1 Pattern EAV (Entity-Attribute-Value) vs Schema Fisso

Lo schema EAV (una riga per ogni (dispositivo, metrica, valore)) è flessibile ma introduce overhead di query. Lo schema fisso (una colonna per ogni metrica) è rigido ma efficiente per query che accedono a molte metriche insieme.

```sql
-- EAV: flessibile, ottimo per metriche eterogenee
CREATE TABLE metriche_eav (
    tempo       TIMESTAMPTZ      NOT NULL,
    entita      TEXT             NOT NULL,
    attributo   TEXT             NOT NULL,
    valore      DOUBLE PRECISION NOT NULL
);

-- Schema fisso: efficiente per set fisso di metriche
CREATE TABLE metriche_host (
    tempo         TIMESTAMPTZ      NOT NULL,
    host          TEXT             NOT NULL,
    cpu_pct       DOUBLE PRECISION,
    mem_pct       DOUBLE PRECISION,
    disk_io_read  BIGINT,
    disk_io_write BIGINT,
    net_rx_bytes  BIGINT,
    net_tx_bytes  BIGINT
);
```

### 5.2 Gestione dei Timestamp con Fusi Orari

```sql
-- Sempre TIMESTAMPTZ (con timezone), mai TIMESTAMP
-- TimescaleDB memorizza UTC internamente, restituisce nel timezone della sessione

-- Impostare timezone di sessione per query locali
SET TIME ZONE 'Europe/Rome';

-- Bucket per ora locale italiana
SELECT
    time_bucket('1 day', tempo AT TIME ZONE 'Europe/Rome') AS giorno_locale,
    COUNT(*) AS eventi
FROM log_applicazione
WHERE tempo >= NOW() - INTERVAL '30 days'
GROUP BY 1 ORDER BY 1;
```

---

*Questo documento fa parte del modulo 09 "Time Series & TimescaleDB" della Data Encyclopedia.*
