# Caricamento dei Dati (Data Loading)

Il caricamento è la fase finale dell'ETL: scrivere i dati trasformati nel sistema di destinazione in modo efficiente, affidabile e coerente. La strategia di loading determina le performance della pipeline, la consistenza dei dati e la complessità della recovery in caso di errore.

## Strategie di Caricamento

### Full Load (Truncate and Reload)

Svuota completamente la tabella di destinazione e ricarica tutto. Semplice ma distruttivo — non applicabile a tabelle con storia o dipendenze.

```sql
-- Procedura atomica: troncamento + ricaricamento in una transazione
BEGIN;
TRUNCATE TABLE dim_product;
INSERT INTO dim_product SELECT * FROM staging_dim_product;
COMMIT;
```

Appropriato per: dimensioni piccole (<1M righe) che cambiano frequentemente, lookup table, reference data.

### Append-Only

Aggiunge nuovi record senza toccare gli esistenti. Appropriato per fact table con partizioni temporali, log, eventi immutabili.

```python
def append_load(conn, table: str, records: list, batch_size: int = 10_000):
    """Inserisce nuovi record senza controllare duplicati."""
    from psycopg2.extras import execute_values

    if not records:
        return

    columns = list(records[0].keys())
    values = [tuple(r[c] for c in columns) for r in records]
    cols_str = ", ".join(columns)
    
    with conn.cursor() as cur:
        for i in range(0, len(values), batch_size):
            batch = values[i:i + batch_size]
            execute_values(
                cur,
                f"INSERT INTO {table} ({cols_str}) VALUES %s",
                batch,
                page_size=batch_size
            )
    conn.commit()
```

### Upsert (INSERT ... ON CONFLICT)

Inserisce record nuovi e aggiorna quelli esistenti in base a una chiave. Pattern gold standard per dimensioni e tabelle aggiornabili.

```python
from psycopg2.extras import execute_values

def upsert(
    conn,
    table: str,
    records: list,
    key_columns: list,
    update_columns: list = None,
    batch_size: int = 10_000
):
    """
    Upsert: insert se chiave non esiste, update se esiste.
    
    key_columns: colonne che formano la chiave di conflitto
    update_columns: colonne da aggiornare (None = tutte tranne key)
    """
    if not records:
        return

    columns = list(records[0].keys())
    if update_columns is None:
        update_columns = [c for c in columns if c not in key_columns]

    values = [tuple(r[c] for c in columns) for r in records]
    cols_str = ", ".join(columns)
    conflict_cols = ", ".join(key_columns)
    update_str = ", ".join(f"{c} = EXCLUDED.{c}" for c in update_columns)

    query = f"""
        INSERT INTO {table} ({cols_str})
        VALUES %s
        ON CONFLICT ({conflict_cols})
        DO UPDATE SET {update_str}
    """

    with conn.cursor() as cur:
        for i in range(0, len(values), batch_size):
            batch = values[i:i + batch_size]
            execute_values(cur, query, batch, page_size=batch_size)
    conn.commit()
```

### Merge (SCD2 via Staging)

Pattern per SCD Type 2: staging table → MERGE con la tabella dimensionale. Garantisce atomicità e permette gestione delle storie.

```sql
-- Step 1: Carica in staging
INSERT INTO staging_dim_customer (customer_id, name, email, city, loaded_at)
SELECT customer_id, name, email, city, NOW()
FROM temp_customer_batch;

-- Step 2: Chiudi record scaduti
UPDATE dim_customer d
SET valid_to = CURRENT_DATE, is_current = FALSE
FROM staging_dim_customer s
WHERE d.customer_id = s.customer_id
  AND d.is_current = TRUE
  AND (d.name <> s.name OR d.email <> s.email OR d.city <> s.city);

-- Step 3: Inserisci nuove versioni
INSERT INTO dim_customer (customer_id, name, email, city, valid_from, valid_to, is_current)
SELECT s.customer_id, s.name, s.email, s.city, CURRENT_DATE, '9999-12-31', TRUE
FROM staging_dim_customer s
JOIN dim_customer d ON d.customer_id = s.customer_id AND d.is_current = FALSE
                    AND d.valid_to = CURRENT_DATE
UNION ALL
-- Record completamente nuovi
SELECT s.customer_id, s.name, s.email, s.city, CURRENT_DATE, '9999-12-31', TRUE
FROM staging_dim_customer s
WHERE NOT EXISTS (SELECT 1 FROM dim_customer WHERE customer_id = s.customer_id);

-- Step 4: Pulisci staging
TRUNCATE TABLE staging_dim_customer;
```

---

## Bulk Loading Performance

### PostgreSQL COPY

`COPY` è l'operazione di bulk insert più veloce in PostgreSQL — 10-50x più rapida di INSERT singoli:

```python
import psycopg2
import csv
import io
from typing import List, Dict, Any

def bulk_copy_from(
    conn,
    table: str,
    records: List[Dict[str, Any]],
    columns: List[str] = None
) -> int:
    """
    Usa COPY FROM per insert ultra-veloce.
    Bypassa per quanto possibile parsing e WAL a livello di riga.
    """
    if not records:
        return 0

    columns = columns or list(records[0].keys())

    # Serializza in CSV in memoria
    buf = io.StringIO()
    writer = csv.writer(buf, quoting=csv.QUOTE_MINIMAL)
    for record in records:
        row = []
        for col in columns:
            val = record.get(col)
            if val is None:
                row.append("")  # NULL in COPY format
            else:
                row.append(str(val))
        writer.writerow(row)

    buf.seek(0)

    with conn.cursor() as cur:
        cur.copy_expert(
            f"COPY {table} ({', '.join(columns)}) FROM STDIN WITH (FORMAT CSV, NULL '')",
            buf
        )
    conn.commit()
    return len(records)


def bulk_copy_with_staging(
    conn,
    target_table: str,
    records: List[Dict[str, Any]],
    key_columns: List[str],
    update_columns: List[str]
) -> Dict[str, int]:
    """
    Carica via staging per upsert performante:
    1. COPY in temp table
    2. INSERT ... ON CONFLICT dalla temp
    """
    if not records:
        return {"inserted": 0, "updated": 0}

    columns = list(records[0].keys())
    staging_table = f"_staging_{target_table.split('.')[-1]}"

    with conn.cursor() as cur:
        # Crea staging temporanea
        cur.execute(f"""
            CREATE TEMP TABLE {staging_table} (LIKE {target_table})
            ON COMMIT DROP
        """)

        # COPY in staging
        buf = io.StringIO()
        writer = csv.writer(buf)
        for r in records:
            writer.writerow([r.get(c) for c in columns])
        buf.seek(0)
        cur.copy_expert(
            f"COPY {staging_table} ({', '.join(columns)}) FROM STDIN WITH (FORMAT CSV, NULL '')",
            buf
        )

        # Merge dalla staging
        conflict_cols = ", ".join(key_columns)
        update_str = ", ".join(f"{c} = EXCLUDED.{c}" for c in update_columns)
        cur.execute(f"""
            INSERT INTO {target_table} ({', '.join(columns)})
            SELECT {', '.join(columns)} FROM {staging_table}
            ON CONFLICT ({conflict_cols}) DO UPDATE SET {update_str}
        """)

    conn.commit()
    return {"rows_processed": len(records)}
```

### execute_values vs executemany

```python
# LENTO — round trip per ogni riga
for row in records:
    cur.execute("INSERT INTO t (a, b) VALUES (%s, %s)", (row["a"], row["b"]))

# VELOCE — singola query con VALUES multipli
from psycopg2.extras import execute_values
execute_values(
    cur,
    "INSERT INTO t (a, b) VALUES %s",
    [(r["a"], r["b"]) for r in records],
    page_size=1000  # chunk di 1000 VALUES per query
)

# ALTERNATIVA — execute_batch (parametri separati, meno overhead parsing)
from psycopg2.extras import execute_batch
execute_batch(
    cur,
    "INSERT INTO t (a, b) VALUES (%s, %s) ON CONFLICT DO NOTHING",
    [(r["a"], r["b"]) for r in records],
    page_size=1000
)
```

---

## Caricamento su Cloud Data Warehouse

### BigQuery

```python
from google.cloud import bigquery
from google.cloud.bigquery import LoadJobConfig, WriteDisposition
import pandas as pd
from typing import List, Dict, Any

class BigQueryLoader:
    """Carica dati su BigQuery."""

    def __init__(self, project: str, dataset: str):
        self.client = bigquery.Client(project=project)
        self.dataset = dataset
        self.project = project

    def _table_ref(self, table: str) -> str:
        return f"{self.project}.{self.dataset}.{table}"

    def load_dataframe(
        self,
        df: pd.DataFrame,
        table: str,
        write_disposition: str = "WRITE_APPEND",
        schema: list = None
    ) -> int:
        """Carica DataFrame in BigQuery via streaming insert o batch."""
        table_ref = self._table_ref(table)

        job_config = LoadJobConfig(
            write_disposition=write_disposition,
            schema=schema,
            autodetect=(schema is None),
            create_disposition="CREATE_IF_NEEDED"
        )

        job = self.client.load_table_from_dataframe(
            df, table_ref, job_config=job_config
        )
        job.result()  # Attendi completamento

        return job.output_rows

    def streaming_insert(
        self,
        records: List[Dict[str, Any]],
        table: str
    ) -> int:
        """
        Streaming insert (bassa latenza, max 10MB per request, 1MB per riga).
        Non transazionale — duplicati possibili in caso di retry.
        """
        table_ref = self.client.get_table(self._table_ref(table))
        errors = self.client.insert_rows_json(table_ref, records)

        if errors:
            raise RuntimeError(f"BigQuery streaming insert errors: {errors}")
        return len(records)

    def load_from_gcs(
        self,
        gcs_uri: str,
        table: str,
        source_format: str = "PARQUET",
        write_disposition: str = "WRITE_APPEND"
    ) -> int:
        """Carica da GCS — molto più veloce per file grandi."""
        table_ref = self._table_ref(table)
        job_config = LoadJobConfig(
            source_format=source_format,
            write_disposition=write_disposition,
            autodetect=True,
            create_disposition="CREATE_IF_NEEDED"
        )

        job = self.client.load_table_from_uri(
            gcs_uri, table_ref, job_config=job_config
        )
        job.result()
        return job.output_rows

    def run_merge(
        self,
        target_table: str,
        staging_table: str,
        join_keys: List[str],
        update_cols: List[str],
        all_cols: List[str]
    ):
        """MERGE per upsert su BigQuery."""
        join_cond = " AND ".join(
            f"T.{k} = S.{k}" for k in join_keys
        )
        update_set = ", ".join(f"T.{c} = S.{c}" for c in update_cols)
        insert_cols = ", ".join(all_cols)
        insert_vals = ", ".join(f"S.{c}" for c in all_cols)

        sql = f"""
        MERGE `{self._table_ref(target_table)}` AS T
        USING `{self._table_ref(staging_table)}` AS S
        ON {join_cond}
        WHEN MATCHED THEN UPDATE SET {update_set}
        WHEN NOT MATCHED THEN INSERT ({insert_cols}) VALUES ({insert_vals})
        """
        self.client.query(sql).result()
```

### Snowflake

```python
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas
import pandas as pd
from typing import List, Dict, Any

class SnowflakeLoader:
    """Carica dati su Snowflake."""

    def __init__(self, account: str, user: str, password: str,
                 warehouse: str, database: str, schema: str):
        self.conn = snowflake.connector.connect(
            account=account, user=user, password=password,
            warehouse=warehouse, database=database, schema=schema
        )

    def load_dataframe(
        self,
        df: pd.DataFrame,
        table: str,
        auto_create_table: bool = False,
        overwrite: bool = False
    ) -> int:
        """Carica DataFrame con write_pandas (usa PUT + COPY internamente)."""
        success, nchunks, nrows, output = write_pandas(
            conn=self.conn,
            df=df,
            table_name=table.upper(),
            auto_create_table=auto_create_table,
            overwrite=overwrite,
            quote_identifiers=False
        )
        if not success:
            raise RuntimeError(f"Snowflake load fallito: {output}")
        return nrows

    def copy_from_stage(
        self,
        stage_path: str,
        table: str,
        file_format: str = "PARQUET"
    ):
        """COPY INTO dalla stage Snowflake interna o esterna (S3/GCS)."""
        cur = self.conn.cursor()
        cur.execute(f"""
            COPY INTO {table}
            FROM '{stage_path}'
            FILE_FORMAT = (TYPE = {file_format})
            ON_ERROR = 'CONTINUE'
            PURGE = FALSE
        """)
        result = cur.fetchone()
        cur.close()
        return result

    def merge(
        self,
        target: str,
        source: str,
        join_keys: List[str],
        update_cols: List[str],
        insert_cols: List[str]
    ):
        """MERGE per upsert su Snowflake."""
        join_cond = " AND ".join(f"t.{k} = s.{k}" for k in join_keys)
        update_set = ", ".join(f"t.{c} = s.{c}" for c in update_cols)
        all_cols = insert_cols
        insert_vals = ", ".join(f"s.{c}" for c in all_cols)

        sql = f"""
        MERGE INTO {target} AS t
        USING {source} AS s
        ON {join_cond}
        WHEN MATCHED THEN UPDATE SET {update_set}
        WHEN NOT MATCHED THEN INSERT ({', '.join(all_cols)})
                          VALUES ({insert_vals})
        """
        cur = self.conn.cursor()
        cur.execute(sql)
        cur.close()
```

---

## Transazionalità e Atomicità

### Caricamento Multi-Tabella Atomico

Quando più tabelle devono essere aggiornate insieme (es. dim + fact), usare una singola transazione:

```python
import psycopg2
from contextlib import contextmanager

@contextmanager
def transaction(conn):
    """Context manager per transazione esplicita con rollback automatico."""
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise

def load_sales_batch(
    conn,
    customers: list,
    products: list,
    sales: list
):
    """Carica dimensioni e fatti in modo atomico."""
    with transaction(conn):
        # Prima carica le dimensioni
        upsert(conn, "dim_customer", customers, ["customer_id"])
        upsert(conn, "dim_product", products, ["product_id"])

        # Poi la fact table (foreign key integrità garantita)
        upsert(conn, "fact_sales", sales, ["sale_id"])
```

### Two-Phase Commit Pattern

Per pipeline che caricano su più database eterogenei simultaneamente:

```python
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class TwoPhaseLoader:
    """
    Coordina il caricamento su più destinazioni con two-phase commit simulato.
    Non è un vero 2PC (richiederebbe XA transactions), ma gestisce il rollback
    compensatorio in caso di fallimento parziale.
    """

    def __init__(self, loaders: Dict[str, any]):
        """loaders: {"postgres": pg_loader, "bigquery": bq_loader}"""
        self.loaders = loaders
        self._loaded: Dict[str, bool] = {}

    def load_all(
        self,
        data: Dict[str, list],
        table: str
    ) -> Dict[str, int]:
        """
        Tenta il caricamento su tutti i loader.
        Se uno fallisce dopo che altri hanno già caricato, compensa
        con delete dei record appena inseriti (rollback compensatorio).
        """
        results = {}
        self._loaded = {}

        for name, loader in self.loaders.items():
            try:
                rows = loader.load(data[name], table)
                results[name] = rows
                self._loaded[name] = True
                logger.info(f"Load su {name}: {rows} righe")
            except Exception as e:
                logger.error(f"Load su {name} fallito: {e}")
                self._compensate(data, table)
                raise RuntimeError(f"Load fallito su {name}, rollback completato") from e

        return results

    def _compensate(self, data: Dict, table: str):
        """Elimina i record già caricati nei loader che hanno avuto successo."""
        for name, success in self._loaded.items():
            if success:
                try:
                    self.loaders[name].delete_batch(data[name], table)
                    logger.info(f"Rollback compensatorio completato su {name}")
                except Exception as e:
                    logger.critical(f"ROLLBACK COMPENSATORIO FALLITO su {name}: {e}")
```

---

## Idempotenza del Caricamento

Un caricamento idempotente produce lo stesso risultato se eseguito una, due o cento volte. Fondamentale per pipeline che possono essere re-eseguite in caso di errore.

```python
def idempotent_load(
    conn,
    table: str,
    records: list,
    run_id: str,
    batch_date: str
):
    """
    Idempotenza via DELETE + INSERT per batch identificati da run_id.
    Se il batch è già presente, lo sovrascrive.
    """
    if not records:
        return

    with conn.cursor() as cur:
        # Elimina eventuale run precedente con stesso ID
        cur.execute(
            f"DELETE FROM {table} WHERE _run_id = %s AND _batch_date = %s",
            (run_id, batch_date)
        )
        deleted = cur.rowcount

        # Aggiungi metadati di tracking
        augmented = [
            {**r, "_run_id": run_id, "_batch_date": batch_date}
            for r in records
        ]

        columns = list(augmented[0].keys())
        from psycopg2.extras import execute_values
        execute_values(
            cur,
            f"INSERT INTO {table} ({', '.join(columns)}) VALUES %s",
            [tuple(r[c] for c in columns) for r in augmented]
        )

    conn.commit()
    return {"deleted_prev": deleted, "inserted": len(records)}
```

---

## Type 1 vs Type 2 Load Strategy

```python
from typing import Dict, Any, List

def load_dimension_type1(
    conn,
    table: str,
    records: List[Dict[str, Any]],
    business_key: str
):
    """SCD Type 1: sovrascrive senza storia."""
    upsert(conn, table, records, [business_key])


def load_dimension_type2(
    conn,
    table: str,
    records: List[Dict[str, Any]],
    business_key: str,
    tracked_cols: List[str]
):
    """SCD Type 2: mantiene storia completa con valid_from/valid_to."""
    from psycopg2.extras import RealDictCursor

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            f"SELECT * FROM {table} WHERE is_current = TRUE"
        )
        existing = cur.fetchall()

    scd_result = apply_scd2_logic(
        new_records=records,
        existing_records=[dict(r) for r in existing],
        business_key=business_key,
        tracked_columns=tracked_cols
    )

    with conn.cursor() as cur:
        # Chiudi record scaduti
        for upd in scd_result["updates"]:
            cur.execute(
                f"""UPDATE {table}
                    SET valid_to = %s, is_current = FALSE
                    WHERE id = %s""",
                (upd["valid_to"], upd["id"])
            )

        # Inserisci nuove versioni
        if scd_result["inserts"]:
            from psycopg2.extras import execute_values
            ins = scd_result["inserts"]
            cols = list(ins[0].keys())
            execute_values(
                cur,
                f"INSERT INTO {table} ({', '.join(cols)}) VALUES %s",
                [tuple(r[c] for c in cols) for r in ins]
            )

    conn.commit()
    return {
        "inserted": len(scd_result["inserts"]),
        "closed": len(scd_result["updates"])
    }
```

---

## Partitioning e Partition Pruning

Per fact table di grandi dimensioni, il caricamento partizionato riduce il lock e aumenta le performance di query:

```sql
-- Crea fact table con partition by range sul mese
CREATE TABLE fact_sales (
    sale_id     BIGINT,
    sale_date   DATE NOT NULL,
    customer_sk INT,
    product_sk  INT,
    amount      NUMERIC(12,2)
) PARTITION BY RANGE (sale_date);

-- Crea partizioni mensili automaticamente
CREATE OR REPLACE PROCEDURE create_monthly_partition(p_year INT, p_month INT)
LANGUAGE plpgsql AS $$
DECLARE
    partition_name TEXT;
    start_date DATE;
    end_date DATE;
BEGIN
    start_date := make_date(p_year, p_month, 1);
    end_date := start_date + INTERVAL '1 month';
    partition_name := format('fact_sales_%s_%s', p_year, lpad(p_month::text, 2, '0'));

    EXECUTE format(
        'CREATE TABLE IF NOT EXISTS %I
         PARTITION OF fact_sales
         FOR VALUES FROM (%L) TO (%L)',
        partition_name, start_date, end_date
    );
END;
$$;
```

```python
def load_to_partitioned_table(
    conn,
    table: str,
    records: list,
    partition_col: str = "sale_date"
):
    """Carica su tabella partizionata: PostgreSQL fa routing automatico."""
    # PostgreSQL gestisce il routing alla partizione corretta via INSERT
    # Non serve logica speciale nel load — il partizionamento è trasparente
    upsert(conn, table, records, key_columns=["sale_id"])
```

---

## Monitoring del Caricamento

```python
import time
from dataclasses import dataclass
from typing import Optional

@dataclass
class LoadMetrics:
    table: str
    strategy: str  # "upsert", "copy", "append"
    rows_inserted: int = 0
    rows_updated: int = 0
    rows_deleted: int = 0
    rows_rejected: int = 0
    duration_sec: float = 0.0
    batch_count: int = 0

    @property
    def total_rows(self) -> int:
        return self.rows_inserted + self.rows_updated

    @property
    def rows_per_second(self) -> float:
        return self.total_rows / max(self.duration_sec, 0.001)

    def to_dict(self) -> dict:
        return {
            "table": self.table,
            "strategy": self.strategy,
            "rows_inserted": self.rows_inserted,
            "rows_updated": self.rows_updated,
            "rows_deleted": self.rows_deleted,
            "rows_rejected": self.rows_rejected,
            "duration_sec": round(self.duration_sec, 2),
            "rows_per_second": round(self.rows_per_second, 0),
            "batch_count": self.batch_count,
        }


def load_fact_table(
    conn,
    table: str,
    records: list,
    batch_size: int = 50_000
) -> LoadMetrics:
    """Carica fact table in batch con metriche."""
    metrics = LoadMetrics(table=table, strategy="copy_batched")
    start = time.monotonic()

    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        try:
            inserted = bulk_copy_from(conn, table, batch)
            metrics.rows_inserted += inserted
            metrics.batch_count += 1
        except Exception as e:
            metrics.rows_rejected += len(batch)
            raise

    metrics.duration_sec = time.monotonic() - start
    return metrics
```

---

## Confronto Strategie di Caricamento

| Strategia | Velocità | Consistenza | Idempotente | Use Case |
|-----------|----------|-------------|-------------|----------|
| Full Load | Media | Alta | Sì | Dimension piccole, reference |
| Append Only | Alta | Alta | No (by default) | Fact immutabili, eventi |
| Upsert ON CONFLICT | Media | Alta | Sì | Dimension, CDC |
| COPY + Staging | Alta | Alta | Sì (con run_id) | Bulk ingestion |
| MERGE | Media | Alta | Sì | SCD2, history |
| Streaming Insert | Alta | Bassa | No | Realtime, low latency |

---

## Best Practice

**Mai caricare direttamente in produzione** — usa sempre una staging table per validare i dati prima del merge nella tabella finale.

**Monitora le dimensioni dei batch** — batch troppo grandi causano lock lunghi; troppo piccoli aumentano l'overhead di round trip. 10k–50k righe è il range ottimale per la maggior parte dei casi.

**Usa `INSERT ... ON CONFLICT DO NOTHING`** per append idempotente invece di verificare l'esistenza del record prima dell'insert — la versione atomica è sempre più sicura e performante.

**Traccia `_loaded_at`, `_run_id`, `_source`** in ogni tabella di destinazione. Questi metadati sono essenziali per debugging e audit.

**Verifica post-load**: dopo ogni caricamento, esegui una query di riconciliazione (count, sum su colonne chiave) contro la sorgente per garantire che i dati siano coerenti.

**Non disabilitare i constraint durante il load** in produzione senza un piano di validazione post-load. Le foreign key violations scoperte dopo il commit sono molto più costose da correggere.
