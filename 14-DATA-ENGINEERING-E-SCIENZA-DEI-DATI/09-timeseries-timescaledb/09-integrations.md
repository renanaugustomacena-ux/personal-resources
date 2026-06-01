# Integrazioni di TimescaleDB

> Autori: Team Data Encyclopedia  
> Ultimo aggiornamento: 2026-05-06  
> Versione: 1.0.0  
> Stato: draft

## Indice
1. Grafana
2. Prometheus e Remote Write
3. Python: psycopg2, asyncpg, pandas
4. Kafka e Pipeline di Ingestione
5. ORM e Framework

---

## 1. Grafana

### 1.1 Configurazione del Datasource

Grafana supporta TimescaleDB nativamente attraverso il datasource PostgreSQL standard. Non è richiesto alcun plugin aggiuntivo per le funzionalità base. Il parametro `timescaledb: true` nella configurazione attiva ottimizzazioni specifiche come il riconoscimento di `time_bucket` e la generazione corretta degli intervalli.

```json
{
  "type": "postgres",
  "url": "timescaledb:5432",
  "database": "telemetria",
  "user": "grafana_reader",
  "jsonData": {
    "sslmode": "require",
    "postgresVersion": 1600,
    "timescaledb": true
  }
}
```

### 1.2 Query con time_bucket e Variabili Template

```sql
-- Panel time series standard — usa $__interval per risoluzione automatica
SELECT
    time_bucket('$__interval', tempo)  AS "time",
    dispositivo                         AS metric,
    AVG(temperatura)                    AS value
FROM telemetria_sensori
WHERE $__timeFilter(tempo)
  AND dispositivo IN ($dispositivo)
GROUP BY 1, 2
ORDER BY 1;

-- $__interval si adatta al range: 1h → '5 minutes', 30d → '4 hours', 1y → '1 day'
-- $__timeFilter(tempo) espande a: tempo BETWEEN 'start' AND 'end'

-- Template variable — lista dinamica dispositivi
SELECT DISTINCT dispositivo
FROM telemetria_sensori
WHERE tempo >= NOW() - INTERVAL '1 day'
ORDER BY dispositivo;
```

### 1.3 Alert Grafana su TimescaleDB

```sql
-- Query per alert: temperatura critica negli ultimi 5 minuti
SELECT
    MAX(temperatura) AS max_temp
FROM telemetria_sensori
WHERE dispositivo = '$dispositivo'
  AND tempo >= NOW() - INTERVAL '5 minutes';
-- Alert threshold: max_temp > 80
```

---

## 2. Prometheus e Remote Write

### 2.1 prometheus-postgresql-adapter

```yaml
# prometheus.yml
remote_write:
  - url: "http://pg-adapter:9201/write"
    remote_timeout: 30s
    queue_config:
      capacity: 10000
      max_shards: 30
      max_samples_per_send: 5000

remote_read:
  - url: "http://pg-adapter:9201/read"
    read_recent: true
```

### 2.2 Schema per Metriche Prometheus

```sql
-- Schema per metriche Prometheus in TimescaleDB
CREATE TABLE prom_samples (
    time        TIMESTAMPTZ   NOT NULL,
    metric_name TEXT          NOT NULL,
    labels      JSONB,
    value       DOUBLE PRECISION NOT NULL
);

SELECT create_hypertable('prom_samples', 'time',
    chunk_time_interval => INTERVAL '1 day');

CREATE INDEX ON prom_samples (metric_name, time DESC);
CREATE INDEX ON prom_samples USING GIN (labels);

-- Continuous aggregate per dashboard veloci
CREATE MATERIALIZED VIEW prom_samples_5m
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('5 minutes', time) AS bucket,
    metric_name,
    labels,
    AVG(value) AS avg_val,
    MAX(value) AS max_val
FROM prom_samples
GROUP BY 1, 2, 3;
```

---

## 3. Python: psycopg2, asyncpg, pandas

### 3.1 psycopg2 con Bulk Insert

```python
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, timezone

def get_connection():
    return psycopg2.connect(
        host="localhost", database="telemetria",
        user="app_user", password="password",
        options="-c statement_timeout=30000"
    )

def inserisci_batch(misurazioni: list[dict], conn):
    """Inserimento efficiente con execute_values (una singola query SQL)."""
    with conn.cursor() as cur:
        execute_values(
            cur,
            "INSERT INTO telemetria_sensori (tempo, dispositivo, temperatura) VALUES %s",
            [(m['ts'], m['device'], m['temp']) for m in misurazioni],
            page_size=1000
        )
    conn.commit()

def query_trend(dispositivo: str, ore: int = 24):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT time_bucket('1 hour', tempo) AS ora,
                       AVG(temperatura), MIN(temperatura), MAX(temperatura)
                FROM telemetria_sensori
                WHERE dispositivo = %s
                  AND tempo >= NOW() - make_interval(hours => %s)
                GROUP BY 1 ORDER BY 1
            """, (dispositivo, ore))
            return cur.fetchall()
```

### 3.2 asyncpg per Alta Concorrenza

```python
import asyncpg, asyncio
from datetime import datetime, timezone

async def setup_pool():
    return await asyncpg.create_pool(
        "postgresql://user:password@localhost/telemetria",
        min_size=5, max_size=20,
        command_timeout=30
    )

async def ingest_worker(pool, queue: asyncio.Queue):
    """Worker che preleva batch dalla queue e li inserisce."""
    while True:
        batch = await queue.get()
        async with pool.acquire() as conn:
            await conn.executemany(
                "INSERT INTO telemetria_sensori(tempo,dispositivo,temperatura)"
                " VALUES($1,$2,$3)",
                batch
            )
        queue.task_done()
```

### 3.3 pandas per Analisi

```python
import pandas as pd
from sqlalchemy import create_engine, text

engine = create_engine("postgresql+psycopg2://user:password@localhost/telemetria",
                       pool_size=5, max_overflow=10)

def carica_serie(dispositivo: str, giorni: int = 30) -> pd.DataFrame:
    query = text("""
        SELECT time_bucket('15 minutes', tempo) AS ts,
               AVG(temperatura) AS temp
        FROM telemetria_sensori
        WHERE dispositivo = :dev
          AND tempo >= NOW() - make_interval(days => :days)
        GROUP BY 1 ORDER BY 1
    """)
    df = pd.read_sql(query, engine,
                     params={"dev": dispositivo, "days": giorni},
                     index_col="ts", parse_dates=["ts"])
    return df

def salva_df(df: pd.DataFrame, table: str = "telemetria_sensori"):
    """Scrittura ottimizzata di un DataFrame."""
    df.to_sql(table, engine, if_exists="append",
              index=True, method="multi", chunksize=5000)
```

---

## 4. Kafka e Pipeline di Ingestione

### 4.1 Consumer Python con Batch Write

```python
from kafka import KafkaConsumer
from psycopg2.extras import execute_values
import json, psycopg2, time

consumer = KafkaConsumer(
    'telemetria.raw',
    bootstrap_servers=['kafka:9092'],
    value_deserializer=lambda m: json.loads(m.decode()),
    group_id='ts-writer',
    max_poll_records=2000
)

conn = psycopg2.connect("postgresql://writer:pw@timescaledb/telemetria")

BATCH_SIZE = 2000
FLUSH_INTERVAL = 5  # secondi

batch, last_flush = [], time.time()

for msg in consumer:
    v = msg.value
    batch.append((v['ts'], v['device'], v['temperature']))
    
    if len(batch) >= BATCH_SIZE or (time.time() - last_flush) > FLUSH_INTERVAL:
        with conn.cursor() as cur:
            execute_values(cur,
                "INSERT INTO telemetria_sensori(tempo,dispositivo,temperatura) "
                "VALUES %s ON CONFLICT DO NOTHING",
                batch, page_size=1000)
        conn.commit()
        batch.clear()
        last_flush = time.time()
```

### 4.2 Kafka Connect JDBC Sink

```json
{
  "name": "timescaledb-telemetria-sink",
  "config": {
    "connector.class": "io.confluent.connect.jdbc.JdbcSinkConnector",
    "tasks.max": "4",
    "connection.url": "jdbc:postgresql://timescaledb:5432/telemetria",
    "connection.user": "kafka_writer",
    "topics": "telemetria.raw",
    "table.name.format": "telemetria_sensori",
    "insert.mode": "insert",
    "batch.size": "3000",
    "pk.mode": "none",
    "transforms": "TimestampConverter",
    "transforms.TimestampConverter.type": "org.apache.kafka.connect.transforms.TimestampConverter$Value",
    "transforms.TimestampConverter.field": "tempo",
    "transforms.TimestampConverter.target.type": "Timestamp"
  }
}
```

---

## 5. ORM e Framework

### 5.1 SQLAlchemy

```python
from sqlalchemy import Column, String, Float, Index, text
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import Session, declarative_base

Base = declarative_base()

class TelemetriaSensore(Base):
    __tablename__ = 'telemetria_sensori'
    tempo       = Column(TIMESTAMP(timezone=True), primary_key=True)
    dispositivo = Column(String, primary_key=True)
    temperatura = Column(Float)

    __table_args__ = (
        Index('ix_tel_dev_tempo', 'dispositivo', tempo.desc()),
    )

# Query raw con time_bucket (SQLAlchemy ORM non wrappa direttamente)
with Session(engine) as session:
    rows = session.execute(text("""
        SELECT time_bucket('1 hour', tempo) AS ora, AVG(temperatura)
        FROM telemetria_sensori
        WHERE dispositivo = :dev AND tempo >= NOW() - INTERVAL '24 hours'
        GROUP BY 1 ORDER BY 1
    """), {"dev": "sensore-42"}).fetchall()
```

### 5.2 Django + django-timescaledb

```python
# models.py
from timescale.db.models.models import TimescaleModel
from timescale.db.models.fields import TimescaleDateTimeField
from django.db import models

class TelemetriaSensore(TimescaleModel):
    time        = TimescaleDateTimeField(interval="1 day")
    dispositivo = models.CharField(max_length=100, db_index=True)
    temperatura = models.FloatField()

    class Meta:
        indexes = [models.Index(fields=['dispositivo', '-time'])]
        ordering = ['-time']

# Query manager
ultime_24h = TelemetriaSensore.timescale.filter(
    time__gte=timezone.now() - timedelta(hours=24),
    dispositivo='sensore-42'
).order_by('-time')
```

---

*Questo documento fa parte del modulo 09 "Time Series & TimescaleDB" della Data Encyclopedia.*
