# ClickHouse — Integrazioni con l'Ecosistema

## Driver e Client

### Python: clickhouse-driver e clickhouse-connect

```bash
pip install clickhouse-driver  # driver nativo (protocollo binario TCP)
pip install clickhouse-connect  # driver HTTP/ufficiale ClickHouse Inc.
```

```python
# clickhouse-driver (protocollo nativo, porta 9000)
from clickhouse_driver import Client

client = Client(
    host='ch-node1',
    port=9000,
    user='analytics',
    password='secret',
    database='analytics',
    settings={
        'max_execution_time': 60,
        'max_memory_usage': 5_000_000_000,
    },
    compression=True,  # LZ4 per il trasporto
)

# Query con parametri tipizzati
rows = client.execute(
    'SELECT user_id, sum(revenue) FROM events WHERE event_date = %(date)s GROUP BY user_id',
    {'date': '2024-01-15'}
)

# Insert batch con column-oriented format (più efficiente)
client.execute(
    'INSERT INTO events (event_date, user_id, event, revenue) VALUES',
    [
        ('2024-01-15', 1001, 'buy', 99.99),
        ('2024-01-15', 1002, 'buy', 149.00),
    ]
)

# Insert con colonne separate (molto più veloce per grandi volumi)
client.execute(
    'INSERT INTO events (event_date, user_id, event, revenue) VALUES',
    {
        'event_date': ['2024-01-15', '2024-01-15'],
        'user_id': [1001, 1002],
        'event': ['buy', 'buy'],
        'revenue': [99.99, 149.00],
    },
    columnar=True  # invia in formato colonnare → risparmio serializzazione
)
```

```python
# clickhouse-connect (HTTP, porta 8123, raccomandato per nuovi progetti)
import clickhouse_connect

client = clickhouse_connect.get_client(
    host='ch-node1',
    port=8443,  # HTTPS
    username='analytics',
    password='secret',
    database='analytics',
    secure=True,
    verify=True,
    ca_cert='/etc/ssl/certs/ca.crt',
    settings={'max_execution_time': 60}
)

# Query → DataFrame Pandas direttamente
df = client.query_df(
    'SELECT event_date, country, sum(revenue) as revenue FROM events GROUP BY event_date, country'
)

# Insert da DataFrame
import pandas as pd
df_to_insert = pd.DataFrame({
    'event_date': ['2024-01-15', '2024-01-15'],
    'user_id': [1001, 1002],
    'event': ['buy', 'view'],
    'revenue': [99.99, 0.0]
})
client.insert_df('events', df_to_insert)

# Query parametrica con PyArrow
result = client.query_arrow(
    'SELECT * FROM events WHERE event_date = {date:Date}',
    parameters={'date': '2024-01-15'}
)
```

---

## Apache Kafka → ClickHouse

Il pattern più comune per ingestione real-time: Kafka come buffer, ClickHouse come sink tramite il motore Kafka integrato.

```sql
-- 1. Tabella destinazione (MergeTree)
CREATE TABLE events_store (
    event_time  DateTime,
    user_id     UInt64,
    event_type  LowCardinality(String),
    properties  String,   -- JSON raw
    revenue     Decimal(10, 2)
) ENGINE = ReplicatedMergeTree('/clickhouse/tables/shard1/events_store', 'replica1')
PARTITION BY toYYYYMMDD(event_time)
ORDER BY (event_time, user_id);

-- 2. Tabella Kafka (consumer virtuale)
CREATE TABLE events_kafka (
    event_time  DateTime,
    user_id     UInt64,
    event_type  String,
    properties  String,
    revenue     Float64
) ENGINE = Kafka
SETTINGS
    kafka_broker_list    = 'kafka1:9092,kafka2:9092,kafka3:9092',
    kafka_topic_list     = 'user-events',
    kafka_group_name     = 'clickhouse-ingest',
    kafka_format         = 'JSONEachRow',
    kafka_num_consumers  = 4,
    kafka_skip_broken_messages = 100,
    kafka_max_block_size = 65536;

-- 3. Materialized View: connette Kafka → MergeTree
CREATE MATERIALIZED VIEW events_kafka_mv TO events_store AS
SELECT
    toDateTime(event_time) as event_time,
    user_id,
    event_type,
    properties,
    toDecimal64(revenue, 2) as revenue
FROM events_kafka;

-- Monitoraggio consumer Kafka
SELECT * FROM system.kafka_consumers;
```

**Gestione degli errori Kafka**: i messaggi malformati vengono skippati se `kafka_skip_broken_messages > 0`. Per audit:

```sql
-- Tabella per messaggi falliti
CREATE TABLE events_kafka_dead (
    raw_message String,
    error       String,
    received_at DateTime DEFAULT now()
) ENGINE = MergeTree() ORDER BY received_at;

-- MV alternativa per catturare errori (pattern avanzato con _error virtual column)
```

---

## Apache Spark → ClickHouse

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .config("spark.jars",
            "/opt/jars/clickhouse-spark-runtime-3.4_2.12-0.7.3.jar,"
            "/opt/jars/clickhouse-jdbc-0.6.0-all.jar") \
    .getOrCreate()

# Lettura da ClickHouse
df = spark.read \
    .format("clickhouse") \
    .option("host", "ch-node1") \
    .option("port", "8443") \
    .option("protocol", "https") \
    .option("user", "spark_user") \
    .option("password", "secret") \
    .option("database", "analytics") \
    .option("table", "events") \
    .option("query",
            "SELECT user_id, sum(revenue) as rev FROM events "
            "WHERE event_date >= '2024-01-01' GROUP BY user_id") \
    .load()

# Scrittura su ClickHouse
df_result.write \
    .format("clickhouse") \
    .option("host", "ch-node1") \
    .option("port", "8443") \
    .option("protocol", "https") \
    .option("user", "spark_user") \
    .option("password", "secret") \
    .option("database", "analytics") \
    .option("table", "spark_results") \
    .option("batchSize", "100000") \
    .mode("append") \
    .save()
```

---

## dbt con ClickHouse

```bash
pip install dbt-clickhouse
```

```yaml
# profiles.yml
my_project:
  target: dev
  outputs:
    dev:
      type: clickhouse
      schema: analytics_dbt
      host: ch-node1
      port: 8443
      user: dbt_user
      password: "{{ env_var('CLICKHOUSE_PASSWORD') }}"
      secure: True
      verify: True

    prod:
      type: clickhouse
      schema: analytics
      host: ch-node1
      port: 8443
      cluster: analytics_cluster
      distributed_ddl_to_local: False
```

```sql
-- models/events_daily.sql
{{ config(
    materialized='incremental',
    engine='ReplicatedMergeTree()',
    order_by='(event_date, country)',
    partition_by='toYYYYMM(event_date)',
    unique_key='(event_date, country)',
    incremental_strategy='delete+insert'
) }}

SELECT
    event_date,
    country,
    count() as events,
    uniq(user_id) as unique_users,
    countIf(event = 'buy') as purchases,
    sum(revenue) as revenue
FROM {{ source('raw', 'events') }}
{% if is_incremental() %}
WHERE event_date >= {{ var('start_date', "today() - 3") }}
{% endif %}
GROUP BY event_date, country
```

---

## Grafana

Il plugin ufficiale Grafana ClickHouse supporta query SQL con macro temporali:

```sql
-- Dashboard: eventi per ora nelle ultime 24 ore
SELECT
    toStartOfHour(event_time) as time,
    count() as events
FROM analytics.events
WHERE $__timeFilter(event_time)  -- macro Grafana: sostituisce con range temporale
GROUP BY time
ORDER BY time;

-- Con variabili Grafana
SELECT country, sum(revenue)
FROM analytics.events
WHERE event_date >= toDate($__from/1000)
  AND event_date <= toDate($__to/1000)
  AND country IN ($country_var)  -- variabile multi-select Grafana
GROUP BY country;
```

```yaml
# Provisioning datasource Grafana
apiVersion: 1
datasources:
  - name: ClickHouse
    type: grafana-clickhouse-datasource
    access: proxy
    url: https://ch-node1:8443
    jsonData:
      defaultDatabase: analytics
      username: grafana_ro
      tlsAuthWithCACert: true
    secureJsonData:
      password: "secret"
      tlsCACert: |
        -----BEGIN CERTIFICATE-----
        ...
```

---

## Airflow → ClickHouse

```python
from airflow import DAG
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.providers.clickhouse.hooks.clickhouse import ClickHouseHook
from datetime import datetime, timedelta

with DAG('clickhouse_etl', schedule_interval='0 * * * *', ...) as dag:

    # Operatore SQL generico
    aggregate_hourly = SQLExecuteQueryOperator(
        task_id='aggregate_hourly',
        conn_id='clickhouse_analytics',
        sql="""
            INSERT INTO events_hourly
            SELECT
                toStartOfHour(event_time) as hour,
                country,
                count() as events,
                sum(revenue) as revenue
            FROM events_raw
            WHERE event_time >= toStartOfHour(now()) - INTERVAL 1 HOUR
              AND event_time < toStartOfHour(now())
            GROUP BY hour, country
        """
    )

    # Hook diretto per operazioni più complesse
    @task
    def check_data_quality():
        hook = ClickHouseHook(clickhouse_conn_id='clickhouse_analytics')
        result = hook.get_first(
            "SELECT count() FROM events_raw WHERE event_time >= today() AND revenue < 0"
        )
        if result[0] > 0:
            raise ValueError(f"Found {result[0]} rows with negative revenue")
```

Le integrazioni ClickHouse coprono l'intero ciclo dei dati: ingestione real-time da Kafka, trasformazioni batch con Spark e dbt, visualizzazione con Grafana, orchestrazione con Airflow. Il punto di forza è l'interfaccia SQL standard che rende ClickHouse compatibile con qualunque strumento che supporti JDBC/HTTP.
