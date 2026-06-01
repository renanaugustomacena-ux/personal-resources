# ClickHouse — Join, Subquery e Query Distribuite

## Modello di Join in ClickHouse

ClickHouse supporta i join SQL standard, ma il suo modello di esecuzione differisce dai database OLTP. Essendo un sistema analitico colonnare, i join sono ottimizzati per il caso in cui la tabella destra (right-hand side, RHS) sia significativamente più piccola della sinistra. Capire questa asimmetria è fondamentale per scrivere query performanti.

### Algoritmi di Join

ClickHouse usa principalmente **hash join**: carica la tabella destra in una hash map in memoria, poi scansiona la tabella sinistra e cerca le corrispondenze.

```sql
-- Join semplice: events (grande) JOIN users (piccola)
SELECT
    e.event_date,
    u.country,
    u.plan_type,
    count() as events,
    sum(e.revenue) as revenue
FROM events AS e
JOIN users AS u ON e.user_id = u.user_id
WHERE e.event_date >= today() - 30
GROUP BY e.event_date, u.country, u.plan_type;
```

La tabella `users` viene caricata in RAM come hash map. Regola: la tabella a destra del JOIN deve stare in memoria.

### Tipi di Join Supportati

```sql
-- INNER JOIN (default)
SELECT e.*, u.name FROM events e INNER JOIN users u ON e.user_id = u.user_id;

-- LEFT JOIN (righe della sinistra senza corrispondenza hanno NULL a destra)
SELECT e.event, u.name FROM events e LEFT JOIN users u ON e.user_id = u.user_id;

-- RIGHT JOIN
SELECT e.event, u.name FROM events e RIGHT JOIN users u ON e.user_id = u.user_id;

-- FULL JOIN
SELECT e.event, u.name FROM events e FULL JOIN users u ON e.user_id = u.user_id;

-- CROSS JOIN (prodotto cartesiano - usare con estrema cautela)
SELECT a.date, b.country FROM dates_table a CROSS JOIN countries_table b;

-- ANTI JOIN: righe della sinistra senza corrispondenza
SELECT e.user_id FROM events e
LEFT ANTI JOIN purchases p ON e.user_id = p.user_id
WHERE e.event_date = today();

-- SEMI JOIN: righe della sinistra CON corrispondenza (senza duplicati)
SELECT e.user_id FROM events e
LEFT SEMI JOIN purchases p ON e.user_id = p.user_id;

-- ANY JOIN: per ogni riga della sinistra, prende solo la prima corrispondenza della destra
SELECT e.user_id, u.name
FROM events e ANY LEFT JOIN users u ON e.user_id = u.user_id;
```

---

## Join con Dictionary (Lookup Join)

Per dimension tables piccole che cambiano raramente, i **Dictionary** sono più efficienti degli hash join perché il dizionario rimane in memoria tra le query.

```sql
-- Definizione dizionario
CREATE DICTIONARY user_dict (
    user_id  UInt64,
    name     String,
    country  String,
    plan     String
)
PRIMARY KEY user_id
SOURCE(CLICKHOUSE(TABLE 'users_dim'))
LAYOUT(HASHED())
LIFETIME(MIN 600 MAX 3600);

-- Utilizzo: nessun join, lookup diretto per user_id
SELECT
    event_date,
    dictGet('user_dict', 'country', user_id) as country,
    dictGet('user_dict', 'plan', user_id) as plan,
    count() as events
FROM events
WHERE event_date >= today() - 7
GROUP BY event_date, country, plan;
```

**Tipi di layout per Dictionary**:

| Layout | Struttura | Lookup | Memoria | Adatto per |
|--------|-----------|--------|---------|------------|
| `FLAT` | Array | O(1) | Alta | Chiavi intere 0-N continue |
| `HASHED` | HashMap | O(1) amm. | Media | Chiavi intere sparse |
| `SPARSE_HASHED` | HashMap ottimizzato | O(1) amm. | Bassa | Come HASHED, meno RAM |
| `COMPLEX_KEY_HASHED` | HashMap con chiavi composite | O(1) amm. | Media | Chiavi multi-colonna |
| `RANGE_HASHED` | Range-keyed | O(log n) | Media | Tabelle temporali (SCD Type 2) |
| `IP_TRIE` | Prefix tree | O(n) | Alta | Geolocalizzazione IP |

```sql
-- RANGE_HASHED per SCD Type 2 (versioni valide nel tempo)
CREATE DICTIONARY product_prices_scd (
    product_id  UInt64,
    price       Decimal(10, 2),
    valid_from  Date,
    valid_to    Date
)
PRIMARY KEY product_id
RANGE(MIN valid_from MAX valid_to)
SOURCE(CLICKHOUSE(TABLE 'product_prices_history'))
LAYOUT(RANGE_HASHED())
LIFETIME(3600);

-- Lookup per una data specifica
SELECT
    order_id,
    product_id,
    quantity,
    dictGetOrDefault('product_prices_scd', 'price',
                     (product_id, order_date), 0.0) as historical_price
FROM orders;
```

---

## Subquery e WITH (CTE)

```sql
-- Subquery scalare
SELECT user_id, revenue,
    revenue / (SELECT avg(revenue) FROM events WHERE event = 'buy') as relative_to_avg
FROM events
WHERE event = 'buy' AND event_date = today();

-- CTE con WITH
WITH
    active_buyers AS (
        SELECT DISTINCT user_id
        FROM events
        WHERE event = 'buy' AND event_date >= today() - 30
    ),
    user_stats AS (
        SELECT
            user_id,
            count() as total_events,
            sum(revenue) as total_revenue,
            max(event_time) as last_activity
        FROM events
        WHERE event_date >= today() - 30
        GROUP BY user_id
    )
SELECT
    u.user_id,
    u.total_events,
    u.total_revenue,
    u.last_activity
FROM user_stats u
WHERE u.user_id IN (SELECT user_id FROM active_buyers)
ORDER BY u.total_revenue DESC
LIMIT 1000;

-- CTE ricorsiva (disponibile da ClickHouse 22.6)
WITH RECURSIVE category_tree AS (
    SELECT id, name, parent_id, 1 as depth
    FROM categories
    WHERE parent_id IS NULL
    UNION ALL
    SELECT c.id, c.name, c.parent_id, ct.depth + 1
    FROM categories c
    JOIN category_tree ct ON c.parent_id = ct.id
    WHERE ct.depth < 10
)
SELECT * FROM category_tree ORDER BY depth, name;
```

---

## Tabelle Distribuite

Per cluster multi-nodo, ClickHouse usa il motore **Distributed** come layer di federazione.

### Architettura Cluster

```xml
<!-- /etc/clickhouse-server/config.d/remote_servers.xml -->
<clickhouse>
    <remote_servers>
        <analytics_cluster>
            <shard>
                <weight>1</weight>
                <internal_replication>true</internal_replication>
                <replica>
                    <host>ch-node1</host>
                    <port>9000</port>
                    <user>interserver_user</user>
                    <password>secret</password>
                </replica>
                <replica>
                    <host>ch-node2</host>
                    <port>9000</port>
                </replica>
            </shard>
            <shard>
                <weight>1</weight>
                <internal_replication>true</internal_replication>
                <replica>
                    <host>ch-node3</host>
                    <port>9000</port>
                </replica>
                <replica>
                    <host>ch-node4</host>
                    <port>9000</port>
                </replica>
            </shard>
        </analytics_cluster>
    </remote_servers>
</clickhouse>
```

### Tabelle Distribuite

```sql
-- Su ogni nodo: tabella locale (ReplicatedMergeTree per HA)
CREATE TABLE events_local ON CLUSTER analytics_cluster (
    event_date Date,
    user_id    UInt64,
    event      LowCardinality(String),
    revenue    Decimal(10, 2)
) ENGINE = ReplicatedMergeTree('/clickhouse/tables/{layer}-{shard}/events', '{replica}')
PARTITION BY toYYYYMM(event_date)
ORDER BY (event_date, user_id);

-- Tabella Distributed: layer di federazione (non contiene dati)
CREATE TABLE events ON CLUSTER analytics_cluster (
    event_date Date,
    user_id    UInt64,
    event      LowCardinality(String),
    revenue    Decimal(10, 2)
) ENGINE = Distributed('analytics_cluster', currentDatabase(), 'events_local', rand());
-- rand() = hash per shard selection; alternativa: intHash64(user_id) per co-locality

-- INSERT su tabella Distributed → routing automatico ai shard
INSERT INTO events SELECT * FROM events_import;

-- SELECT su tabella Distributed → parallel query su tutti i shard + aggregazione
SELECT country, sum(revenue) FROM events GROUP BY country;
```

### Distributed Join: Problemi e Soluzioni

I join su tabelle distribuite sono il problema più complesso. Se entrambe le tabelle sono distribuite, ClickHouse deve o:

1. **Broadcast join**: inviare l'intera tabella piccola a ogni shard
2. **Shuffle join**: ridistribuire i dati per chiave di join (molto costoso)

```sql
-- Soluzione raccomandata: tabella locale + global subquery
SELECT e.user_id, u.country, count()
FROM events_local AS e
GLOBAL JOIN (
    SELECT user_id, country FROM users
) AS u ON e.user_id = u.user_id
GROUP BY e.user_id, u.country;
-- GLOBAL: la subquery viene eseguita sul nodo coordinatore,
-- poi il risultato viene inviato a tutti i shard come broadcast
```

**`IN` distribuito**:

```sql
-- GLOBAL IN: subquery eseguita sul coordinatore, risultato broadcast
SELECT * FROM events_local
WHERE user_id GLOBAL IN (
    SELECT user_id FROM premium_users
);

-- vs IN senza GLOBAL: subquery eseguita su ogni shard separatamente
-- (corretto solo se la tabella inner è distribuita ugualmente)
```

---

## Query su File Remoti

```sql
-- Unione di query su file S3 e tabelle locali
SELECT
    local.user_id,
    local.total_events,
    s3_data.external_score
FROM (
    SELECT user_id, count() as total_events
    FROM events_local
    GROUP BY user_id
) AS local
JOIN (
    SELECT user_id, score as external_score
    FROM s3('s3://my-bucket/scores/2024/*.parquet', 'key', 'secret', 'Parquet')
) AS s3_data ON local.user_id = s3_data.user_id;

-- remote() e remoteSecure() per query cross-cluster
SELECT count() FROM remote('ch-other-cluster:9000', 'analytics.events', 'user', 'pass')
WHERE event_date = today();
```

I join in ClickHouse richiedono una comprensione del data locality per essere performanti. La regola fondamentale è: tenere a sinistra la tabella grande, a destra quella piccola; usare Dictionary per i lookup ripetuti; evitare shuffle join su tabelle distribuite usando GLOBAL IN e GLOBAL JOIN dove necessario.
