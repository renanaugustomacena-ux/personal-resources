# ClickHouse — Architettura e Principi Fondamentali

## Cos'è ClickHouse e Perché Esiste

ClickHouse è un database colonnare analitico (OLAP) open-source sviluppato da Yandex nel 2009 e rilasciato pubblicamente nel 2016. Nasce per risolvere un problema concreto: Yandex.Metrica, il sistema di web analytics di Yandex, doveva processare decine di miliardi di righe al giorno con query di aggregazione sub-secondo su finestre temporali arbitrarie.

La categoria di appartenenza è **Column-Oriented Database Management System** ottimizzato per workload analitici. Non è un OLTP, non è un data warehouse tradizionale, non è un motore di streaming — è un engine specializzato per query aggregate su volumi enormi di dati storici.

## Architettura del Storage Colonnare

Nel modello row-oriented (PostgreSQL, MySQL, InnoDB), una riga viene scritta e letta come unità atomica:

```
Riga 1: [user_id=1001, event="click", page="/home", ts=2024-01-15, country="IT", revenue=0]
Riga 2: [user_id=1002, event="view",  page="/shop", ts=2024-01-15, country="DE", revenue=50.00]
Riga 3: [user_id=1003, event="buy",   page="/cart", ts=2024-01-15, country="FR", revenue=129.99]
```

Nel modello column-oriented, ogni colonna è salvata in file separati:

```
user_id.bin:  [1001, 1002, 1003, ...]
event.bin:    ["click", "view", "buy", ...]
page.bin:     ["/home", "/shop", "/cart", ...]
ts.bin:       [2024-01-15, 2024-01-15, 2024-01-15, ...]
country.bin:  ["IT", "DE", "FR", ...]
revenue.bin:  [0, 50.00, 129.99, ...]
```

**Vantaggi per le query analitiche**:

```sql
-- Questa query legge SOLO le colonne event e country
SELECT country, count() FROM events WHERE event = 'buy' GROUP BY country
```

Con un row store, il database legge tutte le colonne di tutte le righe candidate. Con un column store, legge solo `event.bin` (per il WHERE) e `country.bin` (per il GROUP BY) — saltando completamente user_id, page, ts, revenue.

Per una tabella con 100 colonne e 1 miliardo di righe, questa query in un row store legge ~800 GB; in ClickHouse legge ~20 GB.

## MergeTree: Il Motore Fondamentale

Quasi tutte le tabelle di produzione usano il motore **MergeTree** o una sua variante. Il nome deriva dall'operazione centrale del sistema: i dati vengono scritti in **parti** (parts) immutabili, poi fusi in background in parti più grandi.

### Struttura di una Parte

```
/var/lib/clickhouse/data/mydb/events/
├── 20240115_1_1_0/          ← part directory (partition_minblock_maxblock_level)
│   ├── data.bin             ← dati colonnari compressi
│   ├── primary.idx          ← indice primario (sparse, non B-tree)
│   ├── count.txt            ← numero di righe nella parte
│   ├── columns.txt          ← lista colonne con tipi
│   ├── checksums.txt        ← checksum per integrità
│   ├── event.bin            ← colonna event compressa
│   ├── event.mrk2           ← marks file per random access
│   ├── user_id.bin
│   ├── user_id.mrk2
│   └── ...
├── 20240115_2_2_0/
├── 20240115_1_2_1/          ← merged part (level=1, copre blocchi 1-2)
└── detached/                ← parti in errore o detached manualmente
```

### Ciclo di Vita Write → Merge

1. **INSERT**: i dati vengono scritti in una nuova parte in memoria (buffer), poi flushed su disco come parte immutabile
2. **Background merge**: il merge tree task in background unisce parti piccole in parti più grandi
3. **Granule**: unità minima di lettura — 8192 righe per default (`index_granularity`). Il primary index punta all'inizio di ogni granule
4. **Compressione**: ogni colonna è compressa con LZ4 (default) o ZSTD. Il coefficiente di compressione tipico è 3-7x per dati reali

### Indice Primario Sparso (Sparse Index)

A differenza di un B-tree, l'indice primario di ClickHouse è **sparso**: memorizza solo il valore della chiave di ordinamento per ogni granule (ogni 8192 righe).

```sql
CREATE TABLE events (
    event_date  Date,
    user_id     UInt64,
    event       LowCardinality(String),
    revenue     Decimal(10, 2)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(event_date)
ORDER BY (event_date, user_id);
```

Per una tabella con 1 miliardo di righe e `index_granularity=8192`, l'indice primario avrà ~122.000 entry — carica completamente in RAM, sub-millisecondo per binary search.

**Binary search sul primary index**: ClickHouse cerca nell'indice sparso i granule da leggere, poi scansiona solo quei granule. Per una query `WHERE event_date = '2024-01-15' AND user_id = 1001`, con 1B righe e granule da 8192 row, ClickHouse legge ~8192 righe invece di 1B.

## Tipi di Dato Notevoli

```sql
-- Numerici
UInt8, UInt16, UInt32, UInt64, UInt128, UInt256
Int8,  Int16,  Int32,  Int64,  Int128,  Int256
Float32, Float64
Decimal(P, S), Decimal32(S), Decimal64(S), Decimal128(S)

-- Stringa
String              -- lunghezza variabile, nessun limite
FixedString(N)      -- N byte esatti, più efficiente se lunghezza fissa
LowCardinality(T)   -- dizionario su T (tipicamente String), per colonne a bassa cardinalità

-- Data/Tempo
Date                -- giorni dal 1970, 2 byte
Date32              -- range esteso
DateTime            -- timestamp Unix, 4 byte, timezone
DateTime64(3)       -- millisecondi (3 = ms, 6 = μs, 9 = ns)

-- Strutture
Array(T)            -- array tipizzati
Map(K, V)           -- hash map, più efficiente di Array(Tuple)
Tuple(T1, T2, ...)  -- struttura fissa
Nested(col1 T1, col2 T2) -- array paralleli (syntactic sugar)

-- Speciali
UUID                -- 16 byte, rappresentato come stringa nella output
IPv4, IPv6          -- storage compatto per indirizzi IP
Enum8, Enum16       -- stringhe mappate a interi

-- Nullable
Nullable(T)         -- aggiunge flag null a T; evitare dove non necessario (overhead)
```

### LowCardinality: Codifica a Dizionario

`LowCardinality(String)` mantiene un dizionario interno e sostituisce ogni valore con un indice intero (2-4 byte invece di N byte per la stringa). Per colonne come `country`, `event_type`, `status` — con poche centinaia di valori distinti — la compressione migliora 3-5x e le operazioni di filtering accelerano.

```sql
-- Conversione automatica GROUP BY su LowCardinality è ottimizzata
SELECT event, count()
FROM events
WHERE event IN ('click', 'buy', 'view')
GROUP BY event
-- ClickHouse opera direttamente sugli indici del dizionario
```

## Modello di Consistenza e Durabilità

ClickHouse **non è un database transazionale**. Le sue garanzie:

- **Atomicità degli INSERT**: un singolo INSERT è atomico — o tutte le righe sono visibili o nessuna
- **No rollback**: non c'è rollback multi-statement
- **Eventual consistency per le repliche**: con ReplicatedMergeTree, le repliche convergono ma non sono synchronous per default
- **No UPDATE/DELETE transazionali**: `ALTER TABLE UPDATE/DELETE` sono mutazioni asincrone che riscrivono parti su disco

Per workload OLAP puri — dove i dati vengono inseriti e mai modificati — questo modello è perfetto. Per dati che cambiano, si usano pattern come ReplacingMergeTree (deduplication) o CollapsingMergeTree (tombstoning).

## Confronto con Altri Database Analitici

| Caratteristica | ClickHouse | BigQuery | Redshift | DuckDB |
|----------------|-----------|----------|----------|--------|
| Deployment | Self-hosted/Cloud | Managed (GCP) | Managed (AWS) | Embedded |
| Latenza query | Sub-secondo | Secondi | Secondi | Sub-secondo |
| Scalabilità | Orizzontale | Serverless | Cluster | Single-node |
| Aggiornamenti | Limitati | Limitati | Standard SQL | Standard SQL |
| Costo | Server hardware | Pay-per-query | Cluster fisso | Gratis |
| Real-time ingest | Eccellente | Streaming costoso | ETL batch | File-based |

## Installazione e Configurazione Base

```bash
# Ubuntu/Debian
sudo apt-get install -y apt-transport-https ca-certificates curl gnupg
curl -fsSL 'https://packages.clickhouse.com/rpm/lts/repodata/repomd.xml.key' | sudo gpg --dearmor -o /usr/share/keyrings/clickhouse-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/clickhouse-keyring.gpg] https://packages.clickhouse.com/deb stable main" | sudo tee /etc/apt/sources.list.d/clickhouse.list
sudo apt-get update
sudo apt-get install -y clickhouse-server clickhouse-client

# Avvio
sudo service clickhouse-server start
clickhouse-client --password
```

```xml
<!-- /etc/clickhouse-server/config.d/custom.xml -->
<clickhouse>
    <max_server_memory_usage_to_ram_ratio>0.8</max_server_memory_usage_to_ram_ratio>
    <max_concurrent_queries>200</max_concurrent_queries>
    <max_connections>4096</max_connections>

    <!-- Storage paths per tabelle separate su dischi diversi -->
    <storage_configuration>
        <disks>
            <default>
                <path>/var/lib/clickhouse/</path>
            </default>
            <cold_storage>
                <type>s3</type>
                <endpoint>https://my-bucket.s3.amazonaws.com/clickhouse/</endpoint>
                <access_key_id>AKIAIOSFODNN7EXAMPLE</access_key_id>
                <secret_access_key>wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY</secret_access_key>
            </cold_storage>
        </disks>
        <policies>
            <tiered>
                <volumes>
                    <hot>
                        <disk>default</disk>
                        <max_data_part_size_bytes>1073741824</max_data_part_size_bytes>
                    </hot>
                    <cold>
                        <disk>cold_storage</disk>
                    </cold>
                </volumes>
                <move_factor>0.2</move_factor>
            </tiered>
        </policies>
    </storage_configuration>
</clickhouse>
```

```xml
<!-- /etc/clickhouse-server/users.d/users.xml -->
<clickhouse>
    <users>
        <analytics_user>
            <password_sha256_hex><!-- echo -n "password" | sha256sum --></password_sha256_hex>
            <profile>analytics</profile>
            <quota>default</quota>
            <allow_databases>
                <database>analytics</database>
            </allow_databases>
        </analytics_user>
    </users>
    <profiles>
        <analytics>
            <max_memory_usage>10000000000</max_memory_usage>
            <use_uncompressed_cache>1</use_uncompressed_cache>
            <load_balancing>random</load_balancing>
            <max_execution_time>60</max_execution_time>
        </analytics>
    </profiles>
    <quotas>
        <default>
            <interval>
                <duration>3600</duration>
                <queries>1000</queries>
                <read_rows>10000000000</read_rows>
            </interval>
        </default>
    </quotas>
</clickhouse>
```

## Prima Tabella e Query

```sql
-- Crea database
CREATE DATABASE IF NOT EXISTS analytics;
USE analytics;

-- Tabella eventi web
CREATE TABLE web_events (
    event_date    Date,
    event_time    DateTime,
    user_id       UInt64,
    session_id    String,
    event         LowCardinality(String),
    page          String,
    country       LowCardinality(FixedString(2)),
    device        LowCardinality(String),
    revenue       Decimal(10, 2) DEFAULT 0
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(event_date)
ORDER BY (event_date, user_id, event_time)
SETTINGS index_granularity = 8192;

-- Insert batch
INSERT INTO web_events (event_date, event_time, user_id, session_id, event, page, country, device, revenue)
SELECT
    today() - toUInt32(rand() % 30) as event_date,
    now() - toUInt32(rand() % 2592000) as event_time,
    rand() % 1000000 as user_id,
    toString(rand()) as session_id,
    arrayElement(['click','view','buy','add_cart'], rand() % 4 + 1) as event,
    arrayElement(['/home','/shop','/product','/cart','/checkout'], rand() % 5 + 1) as page,
    arrayElement(['IT','DE','FR','ES','PL'], rand() % 5 + 1) as country,
    arrayElement(['mobile','desktop','tablet'], rand() % 3 + 1) as device,
    if(event = 'buy', round(rand() % 500 + 10, 2), 0) as revenue
FROM numbers(10000000);

-- Query tipica OLAP
SELECT
    country,
    device,
    count() as events,
    uniq(user_id) as unique_users,
    countIf(event = 'buy') as purchases,
    sum(revenue) as total_revenue,
    avg(revenue) as avg_revenue
FROM web_events
WHERE event_date BETWEEN today() - 7 AND today()
GROUP BY country, device
ORDER BY total_revenue DESC;
```

Il risultato di questa query su 10 milioni di righe in ClickHouse è tipicamente sotto i 50ms su hardware commodity.

ClickHouse non è lo strumento per ogni problema, ma per il suo caso d'uso specifico — query aggregate su dati immutabili ad alto volume — è lo stato dell'arte tra i sistemi open-source.
