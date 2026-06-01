# Hyperfunctions di TimescaleDB

> Autori: Team Data Encyclopedia  
> Ultimo aggiornamento: 2026-05-06  
> Versione: 1.0.0  
> Stato: draft

## Indice
1. time_bucket e Varianti
2. Funzioni di Gap-Filling
3. Hyperfunctions Statistiche e Finanziarie
4. Funzioni di Stato e Aggregazione Avanzata
5. Toolkit Hyperfunctions: Pattern di Utilizzo

---

## 1. time_bucket e Varianti

### 1.1 La Funzione time_bucket

`time_bucket()` è la funzione centrale di TimescaleDB per il downsampling e la segmentazione temporale. A differenza del `date_trunc()` di PostgreSQL che tronca al limite naturale del calendario (ora piena, giorno, settimana), `time_bucket()` divide il tempo in bucket di dimensione fissa allineati a un'origine configurabile. Questa distinzione è fondamentale: `date_trunc('hour', '2026-01-01 14:37:22')` restituisce `14:00:00`, mentre `time_bucket('15 minutes', '14:37:22')` restituisce `14:30:00` — il bucket di 15 minuti che contiene il timestamp.

La firma di base della funzione è `time_bucket(bucket_width, ts [, origin] [, timezone] [, offset])`. Il parametro `bucket_width` può essere qualsiasi `INTERVAL` di PostgreSQL: `'5 minutes'`, `'1 hour'`, `'1 day'`, `'1 week'`, `'30 days'`. Tuttavia, per intervalli superiori al giorno conviene usare valori come `'7 days'` anziché `'1 week'` per evitare ambiguità con le convenzioni del calendario.

```sql
-- Aggregazione oraria con time_bucket
SELECT
    time_bucket('1 hour', tempo)    AS ora,
    dispositivo,
    AVG(temperatura)                AS temp_media,
    MIN(temperatura)                AS temp_min,
    MAX(temperatura)                AS temp_max,
    COUNT(*)                        AS campioni
FROM telemetria_sensori
WHERE tempo >= NOW() - INTERVAL '24 hours'
GROUP BY 1, 2
ORDER BY 1 DESC, 2;
```

### 1.2 Origine e Offset

Per default, `time_bucket()` usa l'epoch Unix (1970-01-01 00:00:00 UTC) come punto di riferimento per l'allineamento dei bucket. Questo significa che i bucket di 7 giorni partono da giovedì (perché 1970-01-01 era un giovedì). Se si vuole che la settimana parta da lunedì, bisogna specificare un'origine esplicita.

```sql
-- Bucket settimanali con inizio lunedì
SELECT
    time_bucket('7 days', tempo, TIMESTAMPTZ '2023-01-02') AS settimana, -- 2023-01-02 era lunedì
    COUNT(*) AS eventi
FROM log_eventi
GROUP BY 1
ORDER BY 1;

-- Bucket con offset personalizzato (per fusi orari non standard)
SELECT time_bucket('1 day', tempo, 
    timezone => 'Europe/Rome',
    origin   => '2000-01-01'
) AS giorno_locale,
    AVG(valore)
FROM metriche
GROUP BY 1;
```

Il parametro `timezone` è particolarmente importante per applicazioni che mostrano dati aggregati per giorno/ora locale: senza di esso, i bucket di un giorno corrispondono a giorni UTC, non ai giorni locali degli utenti. Un dashboard che mostra "vendite giornaliere" in italiano deve usare il bucket nel timezone `Europe/Rome` per ottenere giornate che vanno dalla mezzanotte locale alla mezzanotte locale successiva.

---

## 2. Funzioni di Gap-Filling

### 2.1 time_bucket_gapfill

Quando si aggregano serie temporali con bucket fissi, si ottengono naturalmente solo i bucket che contengono dati. Se un sensore non trasmette dati per un'ora, quella riga semplicemente manca nel risultato. Per molte applicazioni (dashboard, grafici) questo è problematico: la linea nel grafico salta, creando visualizzazioni fuorvianti. `time_bucket_gapfill()` risolve questo problema generando una riga per ogni bucket nell'intervallo specificato, anche quelli senza dati.

```sql
-- Senza gap-fill: mancano le ore senza dati
SELECT time_bucket('1 hour', tempo) AS ora,
       AVG(temperatura) AS temp
FROM sensori
WHERE tempo BETWEEN '2026-01-01' AND '2026-01-02'
GROUP BY 1;

-- Con gap-fill: una riga per ogni ora, NULL dove mancano dati
SELECT time_bucket_gapfill('1 hour', tempo,
           start => '2026-01-01 00:00:00+01',
           finish => '2026-01-02 00:00:00+01') AS ora,
       AVG(temperatura) AS temp
FROM sensori
WHERE tempo BETWEEN '2026-01-01' AND '2026-01-02'
GROUP BY 1
ORDER BY 1;
```

### 2.2 locf — Last Observation Carried Forward

`locf()` è una funzione di interpolazione che compila i NULL nei bucket vuoti con l'ultimo valore osservato prima di quel bucket. Il nome deriva dalla tecnica statistica "Last Observation Carried Forward", ampiamente usata nell'analisi di serie temporali discontinue. È appropriata quando si vuole rappresentare che il valore misurato rimane invariato fino alla prossima misurazione.

```sql
SELECT
    time_bucket_gapfill('1 hour', tempo,
        start  => '2026-01-01 00:00:00+01',
        finish => '2026-01-02 00:00:00+01') AS ora,
    dispositivo,
    locf(AVG(temperatura))  AS temp_locf,   -- ultimo valore portato avanti
    locf(AVG(umidita),
         treat_null_as_missing => TRUE)       -- ignora NULL espliciti come dati mancanti
FROM sensori
WHERE tempo BETWEEN '2026-01-01 -01:00' AND '2026-01-02 +01:00'
GROUP BY 1, 2
ORDER BY 2, 1;
```

### 2.3 interpolate — Interpolazione Lineare

`interpolate()` compila i bucket vuoti con valori calcolati per interpolazione lineare tra il valore precedente e quello successivo. È appropriata per sensori fisici dove si assume che i valori varino in modo continuo (temperatura, pressione, umidità) e che i dati mancanti siano dovuti a problemi di comunicazione, non a cambiamenti reali nel sistema misurato.

```sql
SELECT
    time_bucket_gapfill('15 minutes', tempo,
        start  => '2026-01-01 08:00+01',
        finish => '2026-01-01 18:00+01') AS quarto_ora,
    locf(AVG(temperatura))              AS temp_locf,
    interpolate(AVG(temperatura))       AS temp_interpolata,
    AVG(temperatura)                    AS temp_reale
FROM sensori_temperatura
WHERE dispositivo = 'termostato-nord'
  AND tempo BETWEEN '2026-01-01' AND '2026-01-02'
GROUP BY 1
ORDER BY 1;
```

La differenza tra `locf` e `interpolate` è visivamente evidente: `locf` produce una curva a scalini (il valore rimane costante tra due misurazioni), mentre `interpolate` produce una curva lineare a tratti. La scelta dipende dalla natura fisica della grandezza misurata e dal contesto applicativo.

---

## 3. Hyperfunctions Statistiche e Finanziarie

### 3.1 Percentile Approximation

TimescaleDB toolkit fornisce `percentile_agg()` e `approx_percentile()` per il calcolo approssimato dei percentili su grandi dataset. L'algoritmo sottostante è il T-Digest, che mantiene una struttura dati compatta (a diferenza di `percentile_cont` che richiede di materializzare tutti i valori) permettendo aggregazioni incremental e parallelizzabili.

```sql
-- Calcolo del 95° e 99° percentile di latenza
SELECT
    time_bucket('1 hour', tempo)    AS ora,
    servizio,
    approx_percentile(0.50, percentile_agg(latenza_ms)) AS p50,
    approx_percentile(0.95, percentile_agg(latenza_ms)) AS p95,
    approx_percentile(0.99, percentile_agg(latenza_ms)) AS p99,
    approx_percentile(0.999, percentile_agg(latenza_ms)) AS p999
FROM log_latenze
WHERE tempo >= NOW() - INTERVAL '24 hours'
GROUP BY 1, 2;

-- Rollup di percentile_agg da aggregati pre-calcolati
-- (fondamentale per continuous aggregate su percentili)
SELECT
    time_bucket('1 day', ora) AS giorno,
    approx_percentile(0.99, rollup(pct_agg)) AS p99_giornaliero
FROM (
    SELECT time_bucket('1 hour', tempo) AS ora,
           percentile_agg(latenza_ms)   AS pct_agg
    FROM log_latenze
    GROUP BY 1
) hourly
GROUP BY 1;
```

### 3.2 Aggregazioni Finanziarie (candlestick)

Il TimescaleDB Toolkit include funzioni native per l'analisi finanziaria, in particolare le aggregazioni candlestick (OHLCV: Open, High, Low, Close, Volume). Queste funzioni sono ottimizzate per calcoli incrementali e si integrano perfettamente con le continuous aggregate.

```sql
-- Dati OHLCV da tick data
SELECT
    time_bucket('5 minutes', tempo) AS candle,
    strumento,
    toolkit_experimental.open(candlestick_agg(tempo, prezzo, volume))  AS open,
    toolkit_experimental.high(candlestick_agg(tempo, prezzo, volume))  AS high,
    toolkit_experimental.low(candlestick_agg(tempo, prezzo, volume))   AS low,
    toolkit_experimental.close(candlestick_agg(tempo, prezzo, volume)) AS close,
    toolkit_experimental.volume(candlestick_agg(tempo, prezzo, volume)) AS volume,
    toolkit_experimental.vwap(candlestick_agg(tempo, prezzo, volume))  AS vwap
FROM tick_data
WHERE tempo >= NOW() - INTERVAL '1 day'
  AND strumento = 'BTC-USD'
GROUP BY 1, 2
ORDER BY 1;
```

---

## 4. Funzioni di Stato e Aggregazione Avanzata

### 4.1 state_agg e heartbeat_agg

`state_agg()` è progettata per tracciare transizioni di stato nel tempo: un dispositivo che passa da "online" a "offline", un servizio che cambia da "healthy" a "degraded". Permette di calcolare la durata in ogni stato, il numero di transizioni, e lo stato corrente.

```sql
-- Tracking dello stato di un servizio
SELECT
    time_bucket('1 hour', tempo) AS ora,
    servizio,
    state_agg(tempo, stato) AS stato_agg
FROM eventi_stato
GROUP BY 1, 2;

-- Estrazione delle metriche dallo state_agg
SELECT
    ora,
    servizio,
    duration_in(stato_agg, 'degraded')  AS durata_degraded,
    duration_in(stato_agg, 'offline')   AS durata_offline,
    num_changes(stato_agg)              AS num_transizioni
FROM (
    SELECT time_bucket('1 day', tempo) AS ora,
           servizio,
           state_agg(tempo, stato) AS stato_agg
    FROM eventi_stato
    GROUP BY 1, 2
) daily
ORDER BY durata_degraded DESC;
```

### 4.2 counter_agg per Contatori Monotoni

I contatori monotoni (come i bytes inviati su un'interfaccia di rete, o il numero totale di richieste) presentano una sfida nelle serie temporali: il valore non è mai negativo e può resettarsi a zero (quando il dispositivo si riavvia o il contatore va in overflow). `counter_agg()` gestisce questi reset automaticamente e permette di calcolare il delta (incremento) tra due punti nel tempo.

```sql
-- Calcolo del rate di un contatore con gestione dei reset
SELECT
    time_bucket('1 minute', tempo) AS minuto,
    interfaccia,
    delta(counter_agg(tempo, bytes_inviati)) AS bytes_nel_minuto,
    irate_left(counter_agg(tempo, bytes_inviati)) AS rate_istantaneo
FROM metriche_rete
WHERE tempo >= NOW() - INTERVAL '1 hour'
GROUP BY 1, 2
ORDER BY 1;
```

---

## 5. Toolkit Hyperfunctions: Pattern di Utilizzo

### 5.1 Installazione del Toolkit

Le hyperfunctions avanzate (T-Digest, state_agg, counter_agg, candlestick) richiedono l'estensione `timescaledb_toolkit` separata.

```sql
CREATE EXTENSION IF NOT EXISTS timescaledb_toolkit;

-- Verifica delle funzioni disponibili
SELECT proname
FROM pg_proc
WHERE pronamespace = 'toolkit_experimental'::regnamespace
ORDER BY proname;
```

### 5.2 Composizione con Continuous Aggregate

Il vero potere delle hyperfunctions emerge nella combinazione con le continuous aggregate. Le funzioni come `percentile_agg()` e `candlestick_agg()` producono tipi di dati intermedi (partial aggregates) che possono essere materializzati nella continuous aggregate e poi combinati con `rollup()` per ottenere aggregazioni a granularità più bassa senza rielaborare i dati grezzi.

```sql
-- Continuous aggregate con percentile_agg (granularità oraria)
CREATE MATERIALIZED VIEW latenze_orarie
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', tempo) AS ora,
    servizio,
    percentile_agg(latenza_ms)   AS pct_agg,  -- tipo intermedio
    COUNT(*)                     AS richieste
FROM log_latenze
GROUP BY 1, 2;

-- Rollup giornaliero dalla continuous aggregate oraria
SELECT
    time_bucket('1 day', ora) AS giorno,
    servizio,
    approx_percentile(0.99, rollup(pct_agg)) AS p99,
    SUM(richieste) AS richieste_totali
FROM latenze_orarie
WHERE ora >= NOW() - INTERVAL '30 days'
GROUP BY 1, 2
ORDER BY 1, p99 DESC;
```

Questo pattern di "hierarchical rollup" è fondamentale per scalare dashboard su storici lunghi: invece di rielaborare miliardi di righe raw, si lavora su milioni di righe aggregate orarie, le quali sono già pre-calcolate e materializzate su disco.

---

*Questo documento fa parte del modulo 09 "Time Series & TimescaleDB" della Data Encyclopedia.*

---

## 6. Statistical Hyperfunctions

### 6.1 stats_agg — Running Statistics

`stats_agg()` computes streaming statistics (count, sum, mean, variance, standard deviation, skewness, kurtosis) in a single pass. It supports `rollup()` for hierarchical aggregation:

```sql
-- One-pass statistics computation
SELECT
    time_bucket('1 hour', tempo) AS hour,
    dispositivo,
    average(stats_agg(valore))    AS mean,
    stddev(stats_agg(valore))     AS std_dev,
    variance(stats_agg(valore))   AS variance,
    num_vals(stats_agg(valore))   AS sample_count,
    skewness(stats_agg(valore))   AS skew,
    kurtosis(stats_agg(valore))   AS kurt
FROM telemetria_iot
WHERE tempo >= NOW() - INTERVAL '24 hours'
GROUP BY 1, 2;

-- Rollup from hourly to daily stats without re-reading raw data
SELECT
    time_bucket('1 day', hour) AS day,
    dispositivo,
    average(rollup(hourly_stats)) AS daily_mean,
    stddev(rollup(hourly_stats))  AS daily_stddev
FROM (
    SELECT time_bucket('1 hour', tempo) AS hour,
           dispositivo,
           stats_agg(valore) AS hourly_stats
    FROM telemetria_iot
    GROUP BY 1, 2
) hourly
GROUP BY 1, 2;
```

### 6.2 Regression Analysis

```sql
-- Two-variable statistical aggregate for correlation analysis
SELECT
    time_bucket('1 day', tempo) AS day,
    corr(stats_agg(temperatura, umidita)) AS temp_humidity_correlation,
    slope(stats_agg(temperatura, umidita)) AS regression_slope,
    intercept(stats_agg(temperatura, umidita)) AS regression_intercept,
    r_squared(stats_agg(temperatura, umidita)) AS r_squared
FROM sensori
WHERE tempo >= NOW() - INTERVAL '30 days'
GROUP BY 1
ORDER BY 1;
```

---

## 7. Heartbeat Monitoring

### 7.1 heartbeat_agg

Detect devices that have gone silent by tracking expected heartbeat intervals:

```sql
-- Track device heartbeats
SELECT
    dispositivo,
    num_live_ranges(
        heartbeat_agg(tempo, 
            NOW() - INTERVAL '24 hours',
            NOW(),
            INTERVAL '5 minutes')  -- expected heartbeat interval
    ) AS live_periods,
    num_gaps(
        heartbeat_agg(tempo,
            NOW() - INTERVAL '24 hours',
            NOW(),
            INTERVAL '5 minutes')
    ) AS gap_count,
    live_at(
        heartbeat_agg(tempo,
            NOW() - INTERVAL '24 hours',
            NOW(),
            INTERVAL '5 minutes'),
        NOW()
    ) AS currently_alive
FROM telemetria_iot
WHERE tempo >= NOW() - INTERVAL '24 hours'
GROUP BY 1;
```

---

## 8. Delta and Rate Calculations

### 8.1 Rate from Counter Data

```sql
-- Calculate rate of change (per second) for monotonic counters
SELECT
    time_bucket('5 minutes', tempo) AS interval,
    host,
    -- Rate: change per second
    delta(counter_agg(tempo, bytes_sent)) / 
        EXTRACT(EPOCH FROM '5 minutes'::interval) AS bytes_per_second,
    -- Percent change
    (delta(counter_agg(tempo, cpu_ticks)) * 100.0) / 
        GREATEST(1, first(cpu_ticks, tempo)) AS cpu_percent_change
FROM host_metrics
WHERE tempo >= NOW() - INTERVAL '1 hour'
GROUP BY 1, 2
ORDER BY 1, 2;
```

### 8.2 Handling Counter Resets

```sql
-- counter_agg automatically detects and handles resets
-- (when the counter value decreases, it assumes a reset occurred)
SELECT
    time_bucket('1 minute', tempo) AS minute,
    interface_name,
    delta(counter_agg(tempo, packets_total)) AS packets_in_minute,
    num_resets(counter_agg(tempo, packets_total)) AS reset_count
FROM network_counters
WHERE tempo >= NOW() - INTERVAL '1 hour'
GROUP BY 1, 2
ORDER BY 1, 2;
```

---

## 9. Continuous Aggregate Integration Patterns

### 9.1 Multi-Level Aggregation Hierarchy

```sql
-- Level 1: Minute granularity continuous aggregate
CREATE MATERIALIZED VIEW metrics_1m
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 minute', tempo) AS bucket,
    dispositivo,
    AVG(valore) AS avg_val,
    MIN(valore) AS min_val,
    MAX(valore) AS max_val,
    COUNT(*) AS samples,
    percentile_agg(valore) AS pct_agg,
    stats_agg(valore) AS stat_agg
FROM telemetria_iot
GROUP BY 1, 2
WITH NO DATA;

SELECT add_continuous_aggregate_policy('metrics_1m',
    start_offset => INTERVAL '1 hour',
    end_offset => INTERVAL '1 minute',
    schedule_interval => INTERVAL '1 minute');

-- Level 2: Hourly from minute aggregate (cagg-on-cagg, TimescaleDB 2.9+)
CREATE MATERIALIZED VIEW metrics_1h
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', bucket) AS bucket,
    dispositivo,
    AVG(avg_val) AS avg_val,
    MIN(min_val) AS min_val,
    MAX(max_val) AS max_val,
    SUM(samples) AS samples,
    rollup(pct_agg) AS pct_agg,
    rollup(stat_agg) AS stat_agg
FROM metrics_1m
GROUP BY 1, 2
WITH NO DATA;

SELECT add_continuous_aggregate_policy('metrics_1h',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');

-- Level 3: Daily from hourly
CREATE MATERIALIZED VIEW metrics_1d
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', bucket) AS bucket,
    dispositivo,
    AVG(avg_val) AS avg_val,
    MIN(min_val) AS min_val,
    MAX(max_val) AS max_val,
    SUM(samples) AS samples,
    rollup(pct_agg) AS pct_agg,
    rollup(stat_agg) AS stat_agg
FROM metrics_1h
GROUP BY 1, 2
WITH NO DATA;
```

### 9.2 Querying the Right Level

```sql
-- Dashboard query: pick the appropriate level based on time range
-- Last hour → 1-minute aggregate
SELECT bucket, avg_val, approx_percentile(0.99, pct_agg) AS p99
FROM metrics_1m
WHERE dispositivo = 'sensor-42' AND bucket >= NOW() - INTERVAL '1 hour'
ORDER BY bucket;

-- Last 7 days → 1-hour aggregate  
SELECT bucket, avg_val, approx_percentile(0.99, pct_agg) AS p99
FROM metrics_1h
WHERE dispositivo = 'sensor-42' AND bucket >= NOW() - INTERVAL '7 days'
ORDER BY bucket;

-- Last 90 days → 1-day aggregate
SELECT bucket, avg_val, approx_percentile(0.99, pct_agg) AS p99
FROM metrics_1d
WHERE dispositivo = 'sensor-42' AND bucket >= NOW() - INTERVAL '90 days'
ORDER BY bucket;
```

---

## 10. Anomaly Detection with Hyperfunctions

```sql
-- Z-score based anomaly detection using stats_agg
WITH baseline AS (
    SELECT
        dispositivo,
        average(stats_agg(valore)) AS mean,
        stddev(stats_agg(valore)) AS stddev
    FROM telemetria_iot
    WHERE tempo BETWEEN NOW() - INTERVAL '7 days' AND NOW() - INTERVAL '1 hour'
    GROUP BY 1
),
recent AS (
    SELECT tempo, dispositivo, valore
    FROM telemetria_iot
    WHERE tempo >= NOW() - INTERVAL '1 hour'
)
SELECT
    r.tempo, r.dispositivo, r.valore,
    b.mean, b.stddev,
    ABS(r.valore - b.mean) / NULLIF(b.stddev, 0) AS z_score,
    CASE WHEN ABS(r.valore - b.mean) / NULLIF(b.stddev, 0) > 3 
         THEN 'ANOMALY' ELSE 'NORMAL' END AS status
FROM recent r
JOIN baseline b ON r.dispositivo = b.dispositivo
WHERE ABS(r.valore - b.mean) / NULLIF(b.stddev, 0) > 2
ORDER BY z_score DESC;

-- Moving average for trend detection
SELECT
    tempo,
    valore,
    AVG(valore) OVER (ORDER BY tempo ROWS BETWEEN 60 PRECEDING AND CURRENT ROW) AS ma_60,
    valore - AVG(valore) OVER (ORDER BY tempo ROWS BETWEEN 60 PRECEDING AND CURRENT ROW) AS deviation
FROM telemetria_iot
WHERE dispositivo = 'sensor-42'
  AND tempo >= NOW() - INTERVAL '1 hour'
ORDER BY tempo;
```

---

## Troubleshooting

### 1. percentile_agg Returns Unexpected Values

**Symptom**: p99 is lower than p95.

**Root cause**: T-Digest approximation can have error margins, especially with very few data points.

**Fix**: For small datasets, use exact `percentile_cont()`. T-Digest works best with 1000+ values per aggregate.

### 2. time_bucket_gapfill Missing Rows

**Symptom**: Gap-fill does not generate rows at the boundaries.

**Fix**: The `start` and `finish` parameters must be explicitly set, and the WHERE clause must cover at least the same range:
```sql
SELECT time_bucket_gapfill('1 hour', tempo,
    start => '2026-01-01'::timestamptz,
    finish => '2026-01-02'::timestamptz)
FROM table
WHERE tempo >= '2026-01-01' AND tempo < '2026-01-02'  -- MUST match
GROUP BY 1;
```

### 3. candlestick_agg Function Not Found

**Symptom**: `ERROR: function candlestick_agg does not exist`.

**Fix**: Install the toolkit extension:
```sql
CREATE EXTENSION IF NOT EXISTS timescaledb_toolkit;
-- Candlestick functions are in the toolkit_experimental schema
SET search_path TO public, toolkit_experimental;
```

### 4. counter_agg Delta Returns Negative Value

**Symptom**: Delta calculation shows negative values.

**Root cause**: Counter is not actually monotonic, or data has incorrect timestamps.

**Fix**: Verify data ordering and counter behavior. For non-monotonic counters, use `delta(stats_agg(...))` instead.

### 5. Rollup Produces Different Results Than Direct Aggregation

**Symptom**: `rollup(pct_agg)` over hourly data gives different p99 than computing p99 directly from raw data.

**Root cause**: T-Digest rollup introduces approximation error. This is expected behavior — the error is typically <1%.

**Fix**: Accept the approximation for scalability, or use exact percentiles for small datasets.

### 6. locf Returns NULL Despite Previous Data Existing

**Symptom**: `locf(AVG(value))` still shows NULL for some gaps.

**Root cause**: No previous non-NULL bucket exists in the query result set.

**Fix**: Provide a `prev` value:
```sql
locf(AVG(valore), prev => 0.0)  -- use 0 if no previous value exists
```

### 7. Gap-Fill Query Very Slow

**Symptom**: `time_bucket_gapfill` query takes minutes.

**Root cause**: Time range too wide with too-fine granularity generates millions of rows.

**Fix**: Narrow the range or increase bucket size. Generating 1M gap-fill rows is computationally expensive.

### 8. stats_agg Overflow on Large Values

**Symptom**: Variance or kurtosis returns infinity.

**Root cause**: Numerical overflow when squaring very large values.

**Fix**: Normalize input values before aggregation, or use `stats_agg(valore::double precision)`.

### 9. Continuous Aggregate with Hyperfunctions Fails to Refresh

**Symptom**: Refresh policy errors on aggregates using toolkit functions.

**Fix**: Ensure `timescaledb_toolkit` is loaded in `shared_preload_libraries`:
```properties
shared_preload_libraries = 'timescaledb, timescaledb_toolkit'
```

### 10. interpolate Returns Step Function Instead of Linear

**Symptom**: `interpolate()` produces same value for all gap-filled rows.

**Root cause**: Only one non-NULL data point exists — interpolation requires at least two points (before and after the gap).

**Fix**: Ensure the query covers enough range to have data points on both sides of every gap. If only forward data exists, use `locf()` instead.

---

## FAQ

### 1. What is the difference between time_bucket and date_trunc?

`date_trunc` rounds to calendar boundaries (hour, day, week). `time_bucket` divides time into fixed-width intervals from a configurable origin. Use `time_bucket` for arbitrary intervals (15 min, 4 hours, 7 days) and `date_trunc` for calendar-aligned boundaries.

### 2. Can I use hyperfunctions in regular SQL queries?

Yes. Hyperfunctions are PostgreSQL aggregate functions. They work in SELECT, GROUP BY, window functions, subqueries, and CTEs. No special syntax required beyond installing the extension.

### 3. What is the accuracy of approx_percentile?

T-Digest provides sub-1% relative error for typical distributions. Accuracy is highest at the extreme percentiles (p99, p99.9) which is where precision matters most. For datasets under 1000 points, use exact `percentile_cont()`.

### 4. Can I combine gap-fill with continuous aggregates?

No, `time_bucket_gapfill` cannot be used inside continuous aggregate definitions. Compute the aggregate without gap-fill, then apply gap-fill when querying the aggregate:
```sql
-- Continuous aggregate (no gap-fill)
CREATE MATERIALIZED VIEW hourly_temps WITH (timescaledb.continuous) AS
SELECT time_bucket('1 hour', tempo), AVG(temp) FROM sensors GROUP BY 1;

-- Query with gap-fill
SELECT time_bucket_gapfill('1 hour', time_bucket, ...) FROM hourly_temps ...
```

### 5. How does rollup work for aggregates?

`rollup()` combines multiple partial aggregate objects into one. For example, hourly `stats_agg` objects can be rolled up into a daily aggregate without re-reading raw data. This works because the aggregate types store sufficient internal state (e.g., T-Digest centroids, count+sum+sum-of-squares).

### 6. What is the overhead of storing partial aggregates?

A `percentile_agg` stores a T-Digest structure (~1-10 KB per aggregate depending on compression). A `stats_agg` stores ~100 bytes per aggregate. This is much smaller than storing raw data and enables efficient hierarchical rollups.

### 7. Can hyperfunctions work with non-numeric data?

`stats_agg` and `percentile_agg` work with numeric types only. `state_agg` works with text values (categorical states). `counter_agg` works with numeric counters. For string data, use standard PostgreSQL aggregates.

### 8. Are hyperfunctions compatible with PostgreSQL parallel query?

Yes. Most hyperfunctions support parallel aggregation. The partial aggregate types (T-Digest, counter_agg internal) are designed for parallel combine operations.

### 9. How do I create a moving average with hyperfunctions?

Use window functions with `time_bucket`:
```sql
SELECT bucket, avg_val,
    AVG(avg_val) OVER (ORDER BY bucket ROWS BETWEEN 23 PRECEDING AND CURRENT ROW) AS ma_24h
FROM metrics_1h;
```

### 10. What is the difference between counter_agg and stats_agg for rate calculation?

`counter_agg` handles monotonic counters with reset detection — it knows the counter can only go up and interprets decreases as resets. `stats_agg` treats values independently with no counter semantics. Use `counter_agg` for network counters, request totals, uptime counters. Use `stats_agg` for gauge measurements like temperature.

Hyperfunctions transform TimescaleDB from a time-series storage engine into an analytical platform. The combination of approximate algorithms (T-Digest), state tracking (state_agg, counter_agg), gap handling (locf, interpolate), and hierarchical rollup creates a computational layer that eliminates the need for external analytics pipelines for most time-series workloads.

---

## 11. UDDSKETCH — Distribution Approximation

```sql
-- UDDSKETCH provides approximate distribution with error guarantees
SELECT
    time_bucket('1 hour', tempo) AS hour,
    dispositivo,
    approx_percentile(0.5, uddsketch(200, 0.001, valore)) AS median,
    approx_percentile(0.95, uddsketch(200, 0.001, valore)) AS p95,
    approx_percentile(0.99, uddsketch(200, 0.001, valore)) AS p99,
    mean(uddsketch(200, 0.001, valore)) AS mean_val,
    num_vals(uddsketch(200, 0.001, valore)) AS count
FROM telemetria_iot
WHERE tempo >= NOW() - INTERVAL '24 hours'
GROUP BY 1, 2;
```

---

## 12. Compact Utility Functions

### first() and last()

```sql
-- Get first and last value in a time window per device
SELECT
    time_bucket('1 hour', tempo) AS hour,
    dispositivo,
    first(valore, tempo) AS first_reading,
    last(valore, tempo) AS last_reading,
    last(valore, tempo) - first(valore, tempo) AS change
FROM telemetria_iot
WHERE tempo >= NOW() - INTERVAL '24 hours'
GROUP BY 1, 2
ORDER BY 1, 2;

-- Get most recent reading per device (last-value query)
SELECT DISTINCT ON (dispositivo)
    dispositivo, tempo, valore
FROM telemetria_iot
ORDER BY dispositivo, tempo DESC;
```

### Histogram

```sql
-- Compute histogram buckets
SELECT
    time_bucket('1 day', tempo) AS day,
    histogram(valore, 0.0, 100.0, 10) AS temp_distribution
FROM telemetria_iot
WHERE metrica = 'temperature'
  AND tempo >= NOW() - INTERVAL '7 days'
GROUP BY 1
ORDER BY 1;
-- Returns array of counts per bucket: [count_0_10, count_10_20, ..., count_90_100]
```

---

## Additional Troubleshooting

### 11. first/last Returns Wrong Value

**Symptom**: `first(value, time)` does not return the chronologically first value.

**Root cause**: Duplicate timestamps. `first` picks arbitrarily among rows with the same timestamp.

**Fix**: Ensure timestamp precision is sufficient for your sampling rate. Use microsecond precision if needed:
```sql
ALTER TABLE telemetria_iot ALTER COLUMN tempo TYPE TIMESTAMPTZ USING tempo::timestamptz;
```

### 12. Continuous Aggregate with Toolkit Functions Fails to Create

**Symptom**: `ERROR: aggregate function not allowed in continuous aggregate`.

**Fix**: Not all toolkit functions are supported in continuous aggregates. Supported: `stats_agg`, `percentile_agg`, `counter_agg`, `state_agg`, `candlestick_agg`. Unsupported: `histogram`, `uddsketch` in some versions. Check TimescaleDB release notes for your version.

---

## Additional FAQ

### 11. Can I use hyperfunctions with Grafana?

Yes. Write SQL queries using `time_bucket`, `percentile_agg`, and other functions directly in Grafana's PostgreSQL data source. Grafana treats the results as regular time-series data.

### 12. What is the maximum number of values stats_agg can handle?

`stats_agg` uses streaming computation — it processes one value at a time and stores only ~100 bytes of state. There is no practical limit on the number of values.

### 13. How do I compute exponential moving average (EMA)?

Use window functions:
```sql
SELECT tempo, valore,
    AVG(valore) OVER (ORDER BY tempo 
        ROWS BETWEEN 11 PRECEDING AND CURRENT ROW) AS sma_12,
    -- For true EMA, use a recursive CTE or toolkit_experimental.exponential_moving_average
    toolkit_experimental.exponential_moving_average(valore, 12)
        OVER (ORDER BY tempo) AS ema_12
FROM telemetria_iot
WHERE dispositivo = 'sensor-42';
```

### 14. Are there performance differences between percentile_agg and uddsketch?

`percentile_agg` (T-Digest) is slightly faster for most use cases and has better accuracy at extreme percentiles. `uddsketch` provides relative error guarantees across the entire distribution. For most applications, `percentile_agg` is the default choice.

