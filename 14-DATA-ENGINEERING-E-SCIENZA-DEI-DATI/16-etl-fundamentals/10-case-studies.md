# Case Study ETL

Casi reali di progettazione e implementazione di pipeline ETL in produzione. Ogni caso affronta uno scenario specifico con soluzioni concrete, trade-off discussi e lezioni apprese.

---

## Case Study 1: ETL E-Commerce — Ordini da PostgreSQL a Snowflake

### Contesto

Un e-commerce con 500k ordini al giorno deve alimentare il data warehouse Snowflake con dati di vendita per analytics e BI. La pipeline deve girare ogni ora con latenza < 30 minuti dalla transazione.

### Sfide

- Tabella `orders` ha 80 milioni di righe e cresce di 500k al giorno
- Il database operativo non può sostenere query pesanti (impatto su produzione)
- I clienti del BI si aspettano dati freschi ogni ora, non solo la sera
- Le trasformazioni dei prezzi richiedono tax computation per 15 paesi

### Soluzione

```python
from datetime import datetime, timedelta
import psycopg2
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class EcommerceOrdersPipeline:
    """Pipeline oraria: PostgreSQL (replica) → Snowflake."""

    def __init__(
        self,
        source_dsn: str,     # Legge dalla replica, non dal primary
        target_conn_params: dict,
        watermark_table: str = "etl_watermarks"
    ):
        self.source_dsn = source_dsn
        self.target_params = target_conn_params
        self.watermark_table = watermark_table

    def get_watermark(self, sf_conn) -> datetime:
        """Recupera l'ultima watermark da Snowflake."""
        cur = sf_conn.cursor()
        cur.execute(f"""
            SELECT MAX(watermark_value)
            FROM {self.watermark_table}
            WHERE pipeline_name = 'ecommerce_orders'
        """)
        row = cur.fetchone()
        if row and row[0]:
            return row[0]
        # Prima esecuzione: backfill da 90 giorni fa
        return datetime.utcnow() - timedelta(days=90)

    def extract(self, from_ts: datetime) -> pd.DataFrame:
        """Estrae ordini modificati dalla watermark in avanti."""
        conn = psycopg2.connect(self.source_dsn)
        # Usa query con index scan su updated_at (colonna indicizzata)
        query = """
            SELECT
                o.id AS order_id,
                o.customer_id,
                c.email AS customer_email,
                o.total_amount,
                o.currency,
                o.country_code,
                o.status,
                o.created_at,
                o.updated_at,
                array_agg(oi.product_id) AS product_ids,
                SUM(oi.quantity) AS total_items,
                SUM(oi.unit_price * oi.quantity) AS items_subtotal
            FROM orders o
            JOIN customers c ON c.id = o.customer_id
            JOIN order_items oi ON oi.order_id = o.id
            WHERE o.updated_at > %s
            GROUP BY o.id, o.customer_id, c.email, o.total_amount,
                     o.currency, o.country_code, o.status, o.created_at, o.updated_at
            ORDER BY o.updated_at
        """
        # Usa pandas con chunksize per evitare OOM
        chunks = pd.read_sql(query, conn, params=(from_ts,), chunksize=50_000)
        df = pd.concat(list(chunks), ignore_index=True)
        conn.close()
        return df

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pulizia, arricchimento e calcoli derivati."""
        if df.empty:
            return df

        # Tipi corretti
        df["total_amount"] = pd.to_numeric(df["total_amount"], errors="coerce")
        df["created_at"] = pd.to_datetime(df["created_at"], utc=True)
        df["updated_at"] = pd.to_datetime(df["updated_at"], utc=True)

        # Rimuovi outlier palesi (refund negativo non è un outlier)
        df = df[df["total_amount"].notna()]

        # Tax calculation per country
        tax_rates = {
            "IT": 0.22, "DE": 0.19, "FR": 0.20,
            "ES": 0.21, "NL": 0.21, "GB": 0.20,
        }
        df["tax_rate"] = df["country_code"].map(tax_rates).fillna(0.0)
        df["tax_amount"] = (df["total_amount"] * df["tax_rate"]).round(2)
        df["gross_amount"] = df["total_amount"] + df["tax_amount"]

        # Segmentazione
        df["order_size"] = pd.cut(
            df["total_amount"],
            bins=[0, 50, 200, 500, float("inf")],
            labels=["small", "medium", "large", "enterprise"]
        )

        # Metadati pipeline
        df["_loaded_at"] = datetime.utcnow()
        df["_pipeline"] = "ecommerce_orders_hourly"

        return df

    def load(self, df: pd.DataFrame, sf_conn) -> int:
        """Carica su Snowflake con MERGE per gestire aggiornamenti."""
        if df.empty:
            return 0

        # Carica in staging table
        staging_table = "STG_ORDERS_TEMP"
        success, _, nrows, _ = write_pandas(
            conn=sf_conn,
            df=df,
            table_name=staging_table,
            auto_create_table=True,
            overwrite=True
        )

        if not success:
            raise RuntimeError("Snowflake staging load fallito")

        # MERGE dalla staging a target
        cur = sf_conn.cursor()
        cur.execute("""
            MERGE INTO ORDERS AS T
            USING STG_ORDERS_TEMP AS S ON T.ORDER_ID = S.ORDER_ID
            WHEN MATCHED THEN UPDATE SET
                T.STATUS = S.STATUS,
                T.TOTAL_AMOUNT = S.TOTAL_AMOUNT,
                T.UPDATED_AT = S.UPDATED_AT,
                T._LOADED_AT = S._LOADED_AT
            WHEN NOT MATCHED THEN INSERT
                (ORDER_ID, CUSTOMER_ID, CUSTOMER_EMAIL, TOTAL_AMOUNT,
                 CURRENCY, COUNTRY_CODE, STATUS, CREATED_AT, UPDATED_AT,
                 TAX_AMOUNT, GROSS_AMOUNT, ORDER_SIZE, _LOADED_AT)
            VALUES
                (S.ORDER_ID, S.CUSTOMER_ID, S.CUSTOMER_EMAIL, S.TOTAL_AMOUNT,
                 S.CURRENCY, S.COUNTRY_CODE, S.STATUS, S.CREATED_AT, S.UPDATED_AT,
                 S.TAX_AMOUNT, S.GROSS_AMOUNT, S.ORDER_SIZE, S._LOADED_AT)
        """)
        return nrows

    def run(self) -> dict:
        sf_conn = snowflake.connector.connect(**self.target_params)
        run_id = f"orders_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        metrics = {"run_id": run_id, "status": "running"}

        try:
            watermark = self.get_watermark(sf_conn)
            logger.info(f"Estrazione da watermark: {watermark}")

            df_raw = self.extract(watermark)
            metrics["rows_extracted"] = len(df_raw)
            logger.info(f"Estratte {len(df_raw)} righe")

            df_clean = self.transform(df_raw)
            metrics["rows_transformed"] = len(df_clean)

            rows_loaded = self.load(df_clean, sf_conn)
            metrics["rows_loaded"] = rows_loaded

            # Aggiorna watermark
            new_wm = df_raw["updated_at"].max()
            sf_conn.cursor().execute(f"""
                MERGE INTO {self.watermark_table} AS T
                USING (SELECT 'ecommerce_orders' AS pipeline_name, %s::TIMESTAMP AS wm) AS S
                ON T.pipeline_name = S.pipeline_name
                WHEN MATCHED THEN UPDATE SET T.watermark_value = S.wm
                WHEN NOT MATCHED THEN INSERT VALUES (S.pipeline_name, S.wm)
            """, (new_wm,))
            sf_conn.commit()

            metrics["status"] = "success"
            metrics["new_watermark"] = str(new_wm)

        except Exception as e:
            metrics["status"] = "failed"
            metrics["error"] = str(e)
            raise
        finally:
            sf_conn.close()

        return metrics
```

### Lezioni Apprese

**Leggi sempre dalla replica** — la query con `GROUP BY` e `array_agg` su 80M righe avrebbe degradato il primary in produzione.

**Il MERGE di Snowflake è costoso** — per ordini che raramente cambiano status, è più efficiente controllare solo ordini con `updated_at` recente invece di fare MERGE su tutto.

**La tax computation va nel transform**, non nel DWH — se la legge fiscale cambia, riprocessi con la logica corretta senza dover scrivere SQL complesso.

---

## Case Study 2: Real-Time Events da Kafka a BigQuery

### Contesto

Una piattaforma SaaS raccoglie eventi comportamentali (click, view, conversion) da 2 milioni di utenti. Volume: 50 milioni di eventi al giorno. Latenza target: 5 minuti dal browser al DWH.

### Architettura

```
Browser/App → Kafka (eventi raw) → Consumer Python → BigQuery
                                         ↓
                                   DLQ (bad events)
                                   Monitoring
```

### Implementazione

```python
from confluent_kafka import Consumer, KafkaError
import json
import time
from datetime import datetime
from google.cloud import bigquery
from typing import List, Dict

class EventsPipeline:
    """Consumer Kafka → BigQuery per eventi comportamentali."""

    BATCH_SIZE = 5_000
    BATCH_TIMEOUT_SEC = 30.0  # Flush ogni 30s anche se batch non pieno

    def __init__(
        self,
        kafka_config: dict,
        bq_project: str,
        bq_dataset: str,
        bq_table: str
    ):
        self.consumer = Consumer({
            **kafka_config,
            "enable.auto.commit": False,
            "max.poll.interval.ms": 300_000,
        })
        self.bq = bigquery.Client(project=bq_project)
        self.table_ref = f"{bq_project}.{bq_dataset}.{bq_table}"

    def parse_event(self, raw_bytes: bytes) -> Dict:
        """Parsa e valida un evento raw."""
        try:
            event = json.loads(raw_bytes.decode("utf-8"))
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON non valido: {e}")

        required = ["event_type", "user_id", "timestamp"]
        missing = [f for f in required if f not in event]
        if missing:
            raise ValueError(f"Campi obbligatori mancanti: {missing}")

        # Normalizzazione
        return {
            "event_id":     event.get("event_id") or str(uuid.uuid4()),
            "event_type":   str(event["event_type"])[:50],
            "user_id":      str(event["user_id"])[:100],
            "session_id":   event.get("session_id", ""),
            "page_url":     event.get("page_url", "")[:2000],
            "properties":   json.dumps(event.get("properties", {})),
            "event_ts":     datetime.fromtimestamp(
                                event["timestamp"] / 1000
                            ).isoformat() + "Z",
            "ingested_at":  datetime.utcnow().isoformat() + "Z",
        }

    def flush_batch(self, batch: List[Dict]) -> int:
        """Invia batch a BigQuery via streaming insert."""
        if not batch:
            return 0
        errors = self.bq.insert_rows_json(
            self.table_ref,
            batch,
            skip_invalid_rows=False
        )
        if errors:
            # BigQuery streaming ha errori parziali
            valid = [r for i, r in enumerate(batch)
                     if i not in {e["index"] for e in errors}]
            logger.error(f"BigQuery: {len(errors)} errori su {len(batch)} eventi")
            # Re-invia i validi
            if valid:
                self.bq.insert_rows_json(self.table_ref, valid)
        return len(batch) - len(errors)

    def run(self, topics: List[str]):
        self.consumer.subscribe(topics)
        batch = []
        dlq = []
        batch_start = time.monotonic()

        try:
            while True:
                msg = self.consumer.poll(timeout=1.0)
                deadline_exceeded = (
                    time.monotonic() - batch_start >= self.BATCH_TIMEOUT_SEC
                )

                if msg is None:
                    if batch and deadline_exceeded:
                        self.flush_batch(batch)
                        self.consumer.commit(asynchronous=False)
                        batch = []
                        batch_start = time.monotonic()
                    continue

                if msg.error():
                    if msg.error().code() != KafkaError._PARTITION_EOF:
                        logger.error(f"Kafka error: {msg.error()}")
                    continue

                try:
                    event = self.parse_event(msg.value())
                    batch.append(event)
                except (ValueError, KeyError) as e:
                    dlq.append({
                        "raw": msg.value().decode("utf-8", errors="replace")[:1000],
                        "error": str(e),
                        "offset": msg.offset(),
                        "partition": msg.partition()
                    })

                if len(batch) >= self.BATCH_SIZE or deadline_exceeded:
                    loaded = self.flush_batch(batch)
                    self.consumer.commit(asynchronous=False)
                    logger.info(f"Flushed {loaded} eventi (DLQ: {len(dlq)})")
                    batch = []
                    batch_start = time.monotonic()

        except KeyboardInterrupt:
            if batch:
                self.flush_batch(batch)
            logger.info("Pipeline fermata gracefully")
        finally:
            self.consumer.close()
```

### Lezioni Apprese

**Lo streaming insert di BigQuery non è transazionale** — duplicati possono verificarsi in caso di retry. Usa `event_id` come chiave di deduplicazione nelle query downstream.

**Il batch timeout è critico** — senza un timeout, un topic con traffico basso potrebbe non fare flush per ore.

**Il `max.poll.interval.ms`** deve essere maggiore del tempo di processing di un batch + tempo di commit. Se la pipeline impiega 25s per flushare 5k eventi su BigQuery in condizioni di rete lenta, `max.poll.interval.ms = 300000` (5 minuti) è ragionevole.

---

## Case Study 3: Migration da Data Lake a Delta Lake

### Contesto

Una media company ha 5 anni di log di accesso (50TB) in CSV compressi su S3. La struttura è caotica: schemi cambiati 3 volte, alcuni file corrotti, nomi di colonne inconsistenti. Obiettivo: migrare tutto a Delta Lake con schema unificato e ACID.

### Piano di Migrazione

```python
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import *
from delta.tables import DeltaTable

spark = SparkSession.builder \
    .appName("LegacyMigration") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .getOrCreate()

# Schema target unificato (ignora differenze storiche di naming)
UNIFIED_SCHEMA = StructType([
    StructField("event_id",    StringType(),     nullable=False),
    StructField("user_id",     StringType(),     nullable=True),
    StructField("page_url",    StringType(),     nullable=True),
    StructField("ip_address",  StringType(),     nullable=True),
    StructField("user_agent",  StringType(),     nullable=True),
    StructField("event_ts",    TimestampType(),  nullable=False),
    StructField("_year",       IntegerType(),    nullable=False),
    StructField("_month",      IntegerType(),    nullable=False),
    StructField("_source_file",StringType(),     nullable=True),
])

def normalize_column_names(df):
    """Normalizza nomi colonne tra le versioni storiche dello schema."""
    rename_map = {
        # Vecchi nomi → nomi standard
        "userid":       "user_id",
        "uid":          "user_id",
        "url":          "page_url",
        "request_url":  "page_url",
        "ip":           "ip_address",
        "client_ip":    "ip_address",
        "ua":           "user_agent",
        "ts":           "event_ts",
        "timestamp":    "event_ts",
        "request_time": "event_ts",
    }
    for old, new in rename_map.items():
        if old in df.columns:
            df = df.withColumnRenamed(old, new)
    return df


def migrate_year_month(year: int, month: int, source_prefix: str, target_path: str):
    """Migra un mese di dati storici in Delta Lake."""
    source_path = f"s3a://legacy-lake/{source_prefix}/{year}/{month:02d}/*.csv.gz"

    # Leggi con mode permissiva: le righe corrotte vanno in _corrupt_record
    df = spark.read \
        .option("header", "true") \
        .option("mode", "PERMISSIVE") \
        .option("columnNameOfCorruptRecord", "_corrupt_record") \
        .option("encoding", "UTF-8") \
        .csv(source_path)

    # Traccia righe corrotte
    corrupt = df.filter(F.col("_corrupt_record").isNotNull())
    if corrupt.count() > 0:
        logger.warning(f"{year}-{month:02d}: {corrupt.count()} righe corrotte")
        corrupt.write.mode("append").json(f"s3a://data-lake/quarantine/{year}/{month:02d}/")

    df = df.filter(F.col("_corrupt_record").isNull()).drop("_corrupt_record")

    # Normalizza colonne
    df = normalize_column_names(df)

    # Aggiungi colonne mancanti come NULL
    for field in UNIFIED_SCHEMA.fields:
        if field.name not in df.columns and not field.name.startswith("_"):
            df = df.withColumn(field.name, F.lit(None).cast(field.dataType))

    # Cast timestamp (gestisce formati diversi per anno)
    df = df.withColumn("event_ts", F.coalesce(
        F.to_timestamp("event_ts", "yyyy-MM-dd HH:mm:ss"),
        F.to_timestamp("event_ts", "yyyy-MM-dd'T'HH:mm:ss'Z'"),
        F.to_timestamp("event_ts", "dd/MM/yyyy HH:mm:ss")
    ))

    df = df.filter(F.col("event_ts").isNotNull())

    # Aggiungi metadati
    df = df \
        .withColumn("_year", F.year("event_ts")) \
        .withColumn("_month", F.month("event_ts")) \
        .withColumn("_source_file", F.input_file_name())

    # Seleziona solo colonne dello schema unificato
    df = df.select([f.name for f in UNIFIED_SCHEMA.fields])

    # Scrivi in Delta Lake
    df.write \
        .format("delta") \
        .mode("append") \
        .partitionBy("_year", "_month") \
        .save(target_path)

    return df.count()


# Esegui migrazione in ordine cronologico
for year in range(2019, 2024):
    for month in range(1, 13):
        try:
            rows = migrate_year_month(year, month, "access_logs", "s3a://delta-lake/access_logs")
            logger.info(f"Migrato {year}-{month:02d}: {rows} righe")
        except Exception as e:
            logger.error(f"FALLITO {year}-{month:02d}: {e}")

# Optimize e Z-Order dopo la migrazione completa
spark.sql("""
    OPTIMIZE delta.`s3a://delta-lake/access_logs`
    ZORDER BY (user_id, page_url)
""")
```

### Lezioni Apprese

**Non aspettarti schema consistency su 5 anni di CSV** — le colonne cambiano nome, vengono aggiunte, rimosse. Il rename_map è essenziale.

**Quarantina le righe corrotte** invece di perderle — magari contengono dati recuperabili manualmente in un secondo momento.

**OPTIMIZE + ZORDER dopo la migrazione iniziale** riduce enormemente il costo delle query analitiche sui dati storici.

---

## Case Study 4: Gestione di una Pipeline Rotta in Produzione

### Scenario

La pipeline degli ordini non gira da 36 ore. Il DWH mostra dati fermi. Il team BI chiama. È domenica mattina.

### Procedura di Recovery

```bash
#!/bin/bash
# Runbook: recovery pipeline ordini

echo "=== DIAGNOSI ==="

# 1. Controlla lo stato dell'ultimo run
psql $DWH_URL -c "
    SELECT pipeline_name, status, started_at, error_message
    FROM etl_run_log
    WHERE pipeline_name = 'orders_etl'
    ORDER BY started_at DESC
    LIMIT 5;
"

# 2. Controlla i job Airflow
airflow dags state orders_etl 2024-01-14
airflow tasks logs orders_etl extract_orders 2024-01-14

# 3. Controlla la connettività alla sorgente
pg_isready -h $SOURCE_HOST -p 5432 -U etl_user

# 4. Controlla lo spazio disco sul DWH
df -h /var/lib/postgresql/

echo "=== RECOVERY ==="

# 5. Se il run è in stato "running" da > 2 ore: è zombi, resetta
psql $DWH_URL -c "
    UPDATE etl_run_log
    SET status = 'failed', error_message = 'reset manuale dopo timeout',
        finished_at = NOW()
    WHERE pipeline_name = 'orders_etl'
      AND status = 'running'
      AND started_at < NOW() - INTERVAL '2 hours';
"

# 6. Backfill le date mancanti
python etl/backfill.py \
    --pipeline orders_etl \
    --start-date 2024-01-13 \
    --end-date 2024-01-14 \
    --parallelism 2

echo "=== VERIFICA ==="

# 7. Controlla i dati caricati
psql $DWH_URL -c "
    SELECT DATE(created_at) AS day, COUNT(*) AS orders
    FROM fact_orders
    WHERE created_at > NOW() - INTERVAL '3 days'
    GROUP BY 1
    ORDER BY 1;
"

# 8. Controlla il DLQ per anomalie
psql $DWH_URL -c "
    SELECT error_type, COUNT(*) AS cnt, MAX(last_failed_at) AS latest
    FROM etl_dead_letter_queue
    WHERE pipeline_name = 'orders_etl' AND resolved = FALSE
    GROUP BY error_type
    ORDER BY cnt DESC;
"
```

### Lezioni Apprese

**Il runbook salva le domeniche mattina** — documentare le procedure di recovery durante l'orario di lavoro, non quando si è già in crisi.

**I run "running" zombi sono comuni** — un processo ETL killato senza cleanup lascia il run in stato "running" per sempre. Aggiungi sempre un timeout di guardia.

**Il DLQ non è solo per errori di dati** — durante la recovery, controllare il DLQ rivela spesso il root cause originale del problema.

---

## Riepilogo Pattern e Trade-off

| Scenario | Pattern Consigliato | Trade-off |
|----------|-------------------|-----------|
| Volume basso, latenza alta | Micro-batch (5-30 min) | Semplice ma non real-time |
| Volume alto, latenza bassa | Streaming (Kafka) | Complessità infrastruttura |
| Storico massivo una tantum | Spark batch partizionato | Costoso ma parallelo |
| Schema instabile | Schema-on-read + flessibilità | Più codice di adattamento |
| Multi-sorgente etero | Staging unificato | Latenza aggiuntiva |
| Recovery rapida post-errore | Idempotenza + checkpoint | Overhead storage |
