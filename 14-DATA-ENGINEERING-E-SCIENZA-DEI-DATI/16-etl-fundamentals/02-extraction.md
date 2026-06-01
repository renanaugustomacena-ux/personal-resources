# Estrazione dei Dati (Data Extraction)

L'estrazione è la prima fase di qualsiasi pipeline ETL/ELT: acquisire dati grezzi da sorgenti eterogenee in modo affidabile, incrementale e scalabile. La qualità dell'intera pipeline dipende dalla robustezza del layer di estrazione.

## Tipologie di Sorgenti

### Sorgenti Strutturate

Database relazionali (PostgreSQL, MySQL, Oracle, SQL Server), file CSV/TSV, fogli Excel, file XML e JSON con schema fisso. L'estrazione da database relazionali è la più comune in ambito enterprise.

### Sorgenti Semi-strutturate

API REST e GraphQL, file JSON/XML senza schema rigido, log applicativi, feed RSS/Atom, webhook. Richiedono parsing adattivo e gestione di campi opzionali.

### Sorgenti Non Strutturate

Documenti PDF, email, immagini, audio, video, pagine web (scraping). Richiedono preprocessing specializzato prima dell'ingestion nel data warehouse.

### Sorgenti Streaming

Apache Kafka, Amazon Kinesis, Azure Event Hubs, Google Pub/Sub. L'estrazione è continua e near-realtime invece che batch periodica.

---

## Full Extraction vs Incremental Extraction

### Full Extraction

Estrae l'intera sorgente ad ogni run. Semplice da implementare ma non scalabile per sorgenti di grandi dimensioni.

```python
import psycopg2
import pandas as pd

def full_extract_postgres(conn_params: dict, table: str) -> pd.DataFrame:
    """Full extraction: scarica tutta la tabella."""
    conn = psycopg2.connect(**conn_params)
    query = f"SELECT * FROM {table}"
    df = pd.read_sql(query, conn)
    conn.close()
    return df
```

Appropriata per:
- Tabelle di dimensioni ridotte (<1M righe)
- Sorgenti senza colonna timestamp affidabile
- Dati che cambiano in modo non tracciabile
- Prima esecuzione (full initial load)

### Incremental Extraction

Estrae solo i dati nuovi o modificati dall'ultima esecuzione. Riduce drasticamente il volume trasferito.

**High-Watermark Pattern** — utilizza una colonna timestamp o sequence per tracciare l'ultima estrazione:

```python
import psycopg2
from datetime import datetime
from typing import Optional
import json
import os

class IncrementalExtractor:
    """Extractor con high-watermark per estrazione incrementale."""

    def __init__(self, conn_params: dict, watermark_file: str = "watermarks.json"):
        self.conn_params = conn_params
        self.watermark_file = watermark_file
        self._watermarks = self._load_watermarks()

    def _load_watermarks(self) -> dict:
        if os.path.exists(self.watermark_file):
            with open(self.watermark_file) as f:
                return json.load(f)
        return {}

    def _save_watermarks(self):
        with open(self.watermark_file, "w") as f:
            json.dump(self._watermarks, f, default=str)

    def get_watermark(self, table: str) -> Optional[datetime]:
        val = self._watermarks.get(table)
        if val:
            return datetime.fromisoformat(val)
        return None

    def update_watermark(self, table: str, value: datetime):
        self._watermarks[table] = value.isoformat()
        self._save_watermarks()

    def extract_incremental(
        self,
        table: str,
        timestamp_col: str,
        batch_size: int = 10_000
    ):
        """Genera batch di righe dall'ultima watermark."""
        last_wm = self.get_watermark(table)
        max_ts = last_wm

        conn = psycopg2.connect(**self.conn_params)
        cur = conn.cursor(name=f"incr_{table}")  # server-side cursor

        if last_wm:
            query = f"""
                SELECT * FROM {table}
                WHERE {timestamp_col} > %s
                ORDER BY {timestamp_col}
            """
            cur.execute(query, (last_wm,))
        else:
            query = f"SELECT * FROM {table} ORDER BY {timestamp_col}"
            cur.execute(query)

        columns = [desc[0] for desc in cur.description]
        rows_extracted = 0

        while True:
            rows = cur.fetchmany(batch_size)
            if not rows:
                break

            batch = [dict(zip(columns, row)) for row in rows]
            rows_extracted += len(batch)

            # Aggiorna watermark con il massimo del batch
            ts_values = [r[timestamp_col] for r in batch if r[timestamp_col]]
            if ts_values:
                batch_max = max(ts_values)
                if max_ts is None or batch_max > max_ts:
                    max_ts = batch_max

            yield batch

        cur.close()
        conn.close()

        if max_ts:
            self.update_watermark(table, max_ts)
        print(f"Estratte {rows_extracted} righe da {table} (wm: {last_wm} → {max_ts})")
```

### Change Data Capture (CDC)

CDC cattura le modifiche a livello di database log (WAL per PostgreSQL, binlog per MySQL) senza impattare le query applicative. Trattato in dettaglio nel modulo dedicato; qui la struttura di base:

```python
# Struttura evento CDC (Debezium format)
cdc_event = {
    "before": {"id": 1, "name": "Alice", "email": "alice@old.com"},
    "after":  {"id": 1, "name": "Alice", "email": "alice@new.com"},
    "op":     "u",   # c=create, u=update, d=delete, r=read(snapshot)
    "ts_ms":  1700000000000,
    "source": {
        "table": "customers",
        "db":    "production",
        "lsn":   1234567890   # PostgreSQL WAL position
    }
}

def process_cdc_event(event: dict, target_conn) -> None:
    op = event["op"]
    after = event.get("after")
    before = event.get("before")

    with target_conn.cursor() as cur:
        if op == "c":  # CREATE
            cols = list(after.keys())
            vals = list(after.values())
            placeholders = ", ".join(["%s"] * len(cols))
            cur.execute(
                f"INSERT INTO {event['source']['table']} ({', '.join(cols)}) VALUES ({placeholders})",
                vals
            )
        elif op == "u":  # UPDATE
            updates = ", ".join(f"{k} = %s" for k in after.keys())
            vals = list(after.values()) + [before["id"]]
            cur.execute(
                f"UPDATE {event['source']['table']} SET {updates} WHERE id = %s",
                vals
            )
        elif op == "d":  # DELETE
            cur.execute(
                f"DELETE FROM {event['source']['table']} WHERE id = %s",
                [before["id"]]
            )
    target_conn.commit()
```

---

## Estrazione da Database Relazionali

### PostgreSQL con Server-Side Cursor

Per tabelle grandi è essenziale usare cursori server-side per evitare di caricare milioni di righe in memoria:

```python
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Iterator, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class PostgreSQLExtractor:
    """Estrae dati da PostgreSQL con cursore server-side e chunking."""

    def __init__(self, dsn: str):
        self.dsn = dsn

    def extract_table(
        self,
        table: str,
        where_clause: str = "",
        params: tuple = (),
        chunk_size: int = 50_000
    ) -> Iterator[List[Dict[str, Any]]]:
        """Estrae tabella in chunk usando server-side cursor."""

        conn = psycopg2.connect(self.dsn)
        conn.autocommit = False  # Necessario per cursori server-side

        try:
            with conn.cursor(
                name="extract_cursor",
                cursor_factory=RealDictCursor
            ) as cur:
                query = f"SELECT * FROM {table}"
                if where_clause:
                    query += f" WHERE {where_clause}"

                cur.execute(query, params)
                cur.itersize = chunk_size

                while True:
                    rows = cur.fetchmany(chunk_size)
                    if not rows:
                        break
                    yield [dict(row) for row in rows]
                    logger.debug(f"Estratto chunk di {len(rows)} righe da {table}")
        finally:
            conn.close()

    def extract_with_pagination(
        self,
        query: str,
        page_size: int = 10_000
    ) -> Iterator[List[Dict[str, Any]]]:
        """Estrazione con LIMIT/OFFSET per query complesse."""
        conn = psycopg2.connect(self.dsn)
        offset = 0

        try:
            while True:
                paginated = f"{query} LIMIT {page_size} OFFSET {offset}"
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(paginated)
                    rows = cur.fetchall()
                    if not rows:
                        break
                    yield [dict(row) for row in rows]
                    offset += page_size
        finally:
            conn.close()

    def extract_parallel_partitions(
        self,
        table: str,
        partition_col: str,
        n_partitions: int = 4
    ) -> Iterator[List[Dict[str, Any]]]:
        """Estrazione parallela usando modulo aritmetico sul partition_col."""
        import concurrent.futures

        def extract_partition(part_id: int):
            conn = psycopg2.connect(self.dsn)
            results = []
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    f"SELECT * FROM {table} WHERE {partition_col} %% %s = %s",
                    (n_partitions, part_id)
                )
                results = [dict(row) for row in cur.fetchall()]
            conn.close()
            return results

        with concurrent.futures.ThreadPoolExecutor(max_workers=n_partitions) as executor:
            futures = [executor.submit(extract_partition, i) for i in range(n_partitions)]
            for future in concurrent.futures.as_completed(futures):
                yield future.result()
```

### MySQL con Server-Side Cursor

```python
import mysql.connector
from typing import Iterator, List, Dict, Any

class MySQLExtractor:
    """Estrae dati da MySQL con cursore buffered/unbuffered."""

    def __init__(self, host: str, user: str, password: str, database: str):
        self.config = {
            "host": host, "user": user,
            "password": password, "database": database
        }

    def extract_unbuffered(
        self,
        query: str,
        params: tuple = (),
        chunk_size: int = 50_000
    ) -> Iterator[List[Dict[str, Any]]]:
        """Usa cursore unbuffered per evitare OOM su tabelle grandi."""
        conn = mysql.connector.connect(**self.config)

        # buffered=False → streaming row by row dal server
        cur = conn.cursor(dictionary=True, buffered=False)
        cur.execute(query, params)

        try:
            while True:
                rows = cur.fetchmany(chunk_size)
                if not rows:
                    break
                yield rows
        finally:
            cur.close()
            conn.close()
```

---

## Estrazione da API REST

Le API REST sono sorgenti comuni per dati da servizi SaaS (Salesforce, HubSpot, Stripe, ecc.). Il pattern di paginazione varia per API.

### Paginazione Offset/Limit

```python
import requests
import time
from typing import Iterator, List, Dict, Any, Optional

class RestApiExtractor:
    """Estrae dati da API REST con gestione paginazione e rate limiting."""

    def __init__(
        self,
        base_url: str,
        headers: Optional[dict] = None,
        rate_limit_per_second: float = 10.0
    ):
        self.base_url = base_url
        self.headers = headers or {}
        self._min_interval = 1.0 / rate_limit_per_second
        self._last_call = 0.0

    def _rate_limit(self):
        elapsed = time.monotonic() - self._last_call
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_call = time.monotonic()

    def _get_with_retry(
        self,
        url: str,
        params: dict,
        max_retries: int = 3
    ) -> dict:
        for attempt in range(max_retries):
            self._rate_limit()
            try:
                resp = requests.get(url, params=params, headers=self.headers, timeout=30)

                if resp.status_code == 429:  # Too Many Requests
                    retry_after = int(resp.headers.get("Retry-After", 60))
                    time.sleep(retry_after)
                    continue

                resp.raise_for_status()
                return resp.json()

            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise
                wait = 2 ** attempt
                time.sleep(wait)
        raise RuntimeError("Max retries exceeded")

    def extract_offset_pagination(
        self,
        endpoint: str,
        data_key: str = "data",
        page_size: int = 100
    ) -> Iterator[List[Dict[str, Any]]]:
        """Paginazione classica limit/offset."""
        offset = 0

        while True:
            data = self._get_with_retry(
                f"{self.base_url}/{endpoint}",
                params={"limit": page_size, "offset": offset}
            )

            items = data.get(data_key, [])
            if not items:
                break

            yield items
            offset += len(items)

            # Controlla se ci sono altre pagine
            total = data.get("total") or data.get("count")
            if total and offset >= total:
                break

    def extract_cursor_pagination(
        self,
        endpoint: str,
        data_key: str = "results",
        cursor_key: str = "next_cursor",
        page_size: int = 100
    ) -> Iterator[List[Dict[str, Any]]]:
        """Paginazione con cursore opaco (es. Stripe, Notion)."""
        cursor = None

        while True:
            params = {"limit": page_size}
            if cursor:
                params["cursor"] = cursor

            data = self._get_with_retry(
                f"{self.base_url}/{endpoint}",
                params=params
            )

            items = data.get(data_key, [])
            if items:
                yield items

            cursor = data.get(cursor_key)
            if not cursor:
                break

    def extract_link_header_pagination(
        self,
        endpoint: str,
        page_size: int = 100
    ) -> Iterator[List[Dict[str, Any]]]:
        """Paginazione via Link header (GitHub, Jira, ecc.)."""
        url = f"{self.base_url}/{endpoint}"
        params = {"per_page": page_size}

        while url:
            self._rate_limit()
            resp = requests.get(url, params=params, headers=self.headers, timeout=30)
            resp.raise_for_status()

            yield resp.json()

            # Estrai URL prossima pagina dall'header Link
            link_header = resp.headers.get("Link", "")
            next_url = None
            for part in link_header.split(","):
                if 'rel="next"' in part:
                    next_url = part.split(";")[0].strip().strip("<>")
                    break

            url = next_url
            params = {}  # I parametri sono già nell'URL next
```

### API GraphQL

```python
import requests
from typing import Iterator, List, Dict, Any

class GraphQLExtractor:
    """Estrae dati via GraphQL con paginazione cursor-based."""

    def __init__(self, endpoint: str, headers: dict):
        self.endpoint = endpoint
        self.headers = headers

    def query(self, gql_query: str, variables: dict = None) -> dict:
        payload = {"query": gql_query}
        if variables:
            payload["variables"] = variables
        resp = requests.post(
            self.endpoint,
            json=payload,
            headers=self.headers,
            timeout=30
        )
        resp.raise_for_status()
        result = resp.json()
        if "errors" in result:
            raise ValueError(f"GraphQL errors: {result['errors']}")
        return result["data"]

    def extract_paginated(
        self,
        query_template: str,
        connection_path: str,   # es. "orders.edges"
        page_size: int = 100
    ) -> Iterator[List[Dict[str, Any]]]:
        """Estrae nodi da una connessione GraphQL (Relay-style pagination)."""
        cursor = None

        while True:
            variables = {"first": page_size, "after": cursor}
            data = self.query(query_template, variables)

            # Naviga il path es. "orders.edges"
            obj = data
            for key in connection_path.split("."):
                obj = obj[key]

            edges = obj
            if not edges:
                break

            nodes = [edge["node"] for edge in edges]
            yield nodes

            # Cursor per prossima pagina
            page_info_path = connection_path.replace(".edges", ".pageInfo")
            page_info = data
            for key in page_info_path.split("."):
                page_info = page_info[key]

            if not page_info.get("hasNextPage"):
                break
            cursor = page_info["endCursor"]
```

---

## Estrazione da File

### S3 / Object Storage

```python
import boto3
import csv
import json
import io
from typing import Iterator, List, Dict, Any

class S3Extractor:
    """Estrae file da Amazon S3 o compatibili (MinIO, GCS)."""

    def __init__(self, bucket: str, region: str = "eu-west-1", **kwargs):
        self.bucket = bucket
        self.s3 = boto3.client("s3", region_name=region, **kwargs)

    def list_objects(self, prefix: str, suffix: str = "") -> List[str]:
        """Lista tutti i file con un prefisso dato."""
        paginator = self.s3.get_paginator("list_objects_v2")
        keys = []
        for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                if not suffix or key.endswith(suffix):
                    keys.append(key)
        return keys

    def extract_csv(
        self,
        key: str,
        delimiter: str = ",",
        encoding: str = "utf-8"
    ) -> Iterator[List[Dict[str, Any]]]:
        """Estrae CSV da S3 in streaming."""
        response = self.s3.get_object(Bucket=self.bucket, Key=key)
        body = response["Body"]

        # Decompressione automatica
        if key.endswith(".gz"):
            import gzip
            body = gzip.open(body, mode="rt", encoding=encoding)
        else:
            body = io.TextIOWrapper(body, encoding=encoding)

        reader = csv.DictReader(body, delimiter=delimiter)
        batch = []
        for row in reader:
            batch.append(dict(row))
            if len(batch) >= 10_000:
                yield batch
                batch = []
        if batch:
            yield batch

    def extract_json_lines(
        self,
        key: str,
        encoding: str = "utf-8"
    ) -> Iterator[List[Dict[str, Any]]]:
        """Estrae JSONL (una riga JSON per riga) da S3."""
        response = self.s3.get_object(Bucket=self.bucket, Key=key)
        body = response["Body"]

        if key.endswith(".gz"):
            import gzip
            body = gzip.open(body, mode="rt", encoding=encoding)
        else:
            body = io.TextIOWrapper(body, encoding=encoding)

        batch = []
        for line in body:
            line = line.strip()
            if line:
                batch.append(json.loads(line))
                if len(batch) >= 10_000:
                    yield batch
                    batch = []
        if batch:
            yield batch

    def extract_parquet(self, key: str) -> Iterator[List[Dict[str, Any]]]:
        """Estrae file Parquet da S3 usando PyArrow."""
        import pyarrow.parquet as pq
        import pyarrow as pa

        response = self.s3.get_object(Bucket=self.bucket, Key=key)
        body = response["Body"].read()

        table = pq.read_table(io.BytesIO(body))

        # Converti batch di 50k righe
        for batch in table.to_batches(max_chunksize=50_000):
            yield batch.to_pylist()

    def extract_directory(
        self,
        prefix: str,
        file_extension: str = ".csv"
    ) -> Iterator[List[Dict[str, Any]]]:
        """Estrae tutti i file in una directory S3."""
        keys = self.list_objects(prefix, suffix=file_extension)
        for key in keys:
            print(f"Elaborando: {key}")
            if file_extension == ".csv":
                yield from self.extract_csv(key)
            elif file_extension in (".json", ".jsonl"):
                yield from self.extract_json_lines(key)
            elif file_extension == ".parquet":
                yield from self.extract_parquet(key)
```

### File System Locale / SFTP

```python
import paramiko
import csv
import io
from pathlib import Path
from typing import Iterator, List, Dict, Any

class SFTPExtractor:
    """Estrae file da server SFTP."""

    def __init__(self, host: str, port: int, username: str, key_path: str):
        self.host = host
        self.port = port
        self.username = username
        self.key_path = key_path
        self._client: paramiko.SFTPClient = None

    def __enter__(self):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.RejectPolicy())  # NO AutoAdd
        key = paramiko.RSAKey.from_private_key_file(self.key_path)
        ssh.connect(self.host, port=self.port, username=self.username, pkey=key)
        self._client = ssh.open_sftp()
        return self

    def __exit__(self, *args):
        if self._client:
            self._client.close()

    def list_files(self, remote_dir: str, pattern: str = "*") -> List[str]:
        """Lista file in una directory remota."""
        import fnmatch
        files = self._client.listdir(remote_dir)
        return [
            f"{remote_dir}/{f}" for f in files
            if fnmatch.fnmatch(f, pattern)
        ]

    def extract_csv(
        self,
        remote_path: str,
        delimiter: str = ","
    ) -> Iterator[List[Dict[str, Any]]]:
        """Estrae CSV remoto in batch."""
        with self._client.open(remote_path, "r") as f:
            reader = csv.DictReader(
                io.TextIOWrapper(f, encoding="utf-8"),
                delimiter=delimiter
            )
            batch = []
            for row in reader:
                batch.append(dict(row))
                if len(batch) >= 10_000:
                    yield batch
                    batch = []
            if batch:
                yield batch
```

---

## Estrazione da Stream

### Apache Kafka Consumer

```python
from confluent_kafka import Consumer, KafkaError, KafkaException
import json
from typing import Iterator, List, Dict, Any
import time

class KafkaExtractor:
    """Consuma messaggi da Kafka topic in batch."""

    def __init__(
        self,
        bootstrap_servers: str,
        group_id: str,
        topics: List[str],
        auto_offset_reset: str = "earliest"
    ):
        self.consumer = Consumer({
            "bootstrap.servers": bootstrap_servers,
            "group.id": group_id,
            "auto.offset.reset": auto_offset_reset,
            "enable.auto.commit": False,  # Commit manuale dopo processing
            "max.poll.interval.ms": 300_000,
        })
        self.consumer.subscribe(topics)

    def extract_batches(
        self,
        batch_size: int = 1_000,
        batch_timeout_sec: float = 5.0
    ) -> Iterator[List[Dict[str, Any]]]:
        """Yield batch di messaggi, committando dopo ogni batch elaborato."""

        batch = []
        batch_start = time.monotonic()

        try:
            while True:
                msg = self.consumer.poll(timeout=1.0)

                if msg is None:
                    # Timeout poll: flush batch parziale se scaduto il timeout
                    if batch and (time.monotonic() - batch_start) >= batch_timeout_sec:
                        yield batch
                        self.consumer.commit(asynchronous=False)
                        batch = []
                        batch_start = time.monotonic()
                    continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    raise KafkaException(msg.error())

                try:
                    value = json.loads(msg.value().decode("utf-8"))
                    batch.append({
                        "topic": msg.topic(),
                        "partition": msg.partition(),
                        "offset": msg.offset(),
                        "timestamp": msg.timestamp()[1],
                        "key": msg.key().decode("utf-8") if msg.key() else None,
                        "value": value
                    })
                except json.JSONDecodeError:
                    # Messaggio malformato: metti in DLQ
                    batch.append({
                        "topic": msg.topic(),
                        "partition": msg.partition(),
                        "offset": msg.offset(),
                        "value": None,
                        "_parse_error": str(msg.value()[:100])
                    })

                if len(batch) >= batch_size:
                    yield batch
                    self.consumer.commit(asynchronous=False)
                    batch = []
                    batch_start = time.monotonic()

        except KeyboardInterrupt:
            if batch:
                yield batch
                self.consumer.commit(asynchronous=False)
        finally:
            self.consumer.close()
```

---

## Web Scraping

Per sorgenti senza API ufficiale, il web scraping è l'ultima risorsa. Da usare con cautela rispettando robots.txt e termini di servizio.

```python
import httpx
import asyncio
from bs4 import BeautifulSoup
from typing import Iterator, List, Dict, Any
import time
import random

class WebScraper:
    """Scraper rispettoso con rate limiting e retry."""

    def __init__(
        self,
        base_url: str,
        delay_range: tuple = (1.0, 3.0),
        headers: dict = None
    ):
        self.base_url = base_url
        self.delay_range = delay_range
        self.headers = headers or {
            "User-Agent": "DataPipelineBot/1.0 (research purposes)"
        }

    def _polite_delay(self):
        """Delay randomizzato tra richieste."""
        delay = random.uniform(*self.delay_range)
        time.sleep(delay)

    def scrape_listing_pages(
        self,
        url_pattern: str,
        total_pages: int,
        item_selector: str,
        field_selectors: Dict[str, str]
    ) -> Iterator[List[Dict[str, Any]]]:
        """Scrapa pagine di lista con paginazione numerica."""
        for page in range(1, total_pages + 1):
            url = url_pattern.format(page=page)
            self._polite_delay()

            resp = httpx.get(url, headers=self.headers, timeout=30, follow_redirects=True)
            if resp.status_code != 200:
                print(f"Skip pagina {page}: HTTP {resp.status_code}")
                continue

            soup = BeautifulSoup(resp.text, "lxml")
            items = soup.select(item_selector)

            batch = []
            for item in items:
                record = {}
                for field, selector in field_selectors.items():
                    el = item.select_one(selector)
                    record[field] = el.get_text(strip=True) if el else None
                batch.append(record)

            if batch:
                yield batch
```

---

## Schema Inference e Validazione

Prima di caricare in un data warehouse, è essenziale inferire e validare lo schema dei dati estratti:

```python
import pandas as pd
from typing import Dict, Any

def infer_schema(samples: List[Dict[str, Any]]) -> Dict[str, str]:
    """Inferisce tipi di colonna da un campione di record."""
    if not samples:
        return {}

    df = pd.DataFrame(samples[:1000])  # Campiona max 1000 record

    schema = {}
    for col in df.columns:
        # Tenta conversione a numerici
        numeric = pd.to_numeric(df[col], errors="coerce")
        if numeric.notna().sum() / df[col].notna().sum() > 0.95:
            if (numeric % 1 == 0).all():
                schema[col] = "integer"
            else:
                schema[col] = "float"
            continue

        # Tenta conversione a datetime
        try:
            pd.to_datetime(df[col].dropna().head(50), infer_datetime_format=True)
            schema[col] = "timestamp"
            continue
        except (ValueError, TypeError):
            pass

        # Booleani
        bool_values = {"true", "false", "1", "0", "yes", "no", "t", "f"}
        if df[col].str.lower().dropna().isin(bool_values).all():
            schema[col] = "boolean"
            continue

        schema[col] = "text"

    return schema


def validate_extracted_data(
    records: List[Dict[str, Any]],
    expected_columns: List[str],
    required_columns: List[str]
) -> Dict[str, Any]:
    """Valida record estratti contro schema atteso."""
    issues = []

    if not records:
        return {"valid": False, "issues": ["Nessun record estratto"]}

    actual_cols = set(records[0].keys())
    expected_set = set(expected_columns)
    required_set = set(required_columns)

    missing_required = required_set - actual_cols
    if missing_required:
        issues.append(f"Colonne obbligatorie mancanti: {missing_required}")

    extra_cols = actual_cols - expected_set
    if extra_cols:
        issues.append(f"Colonne extra non attese: {extra_cols} (warning)")

    # Controlla null in required columns
    for col in required_columns:
        if col in actual_cols:
            null_count = sum(1 for r in records if r.get(col) is None)
            if null_count > 0:
                issues.append(f"Colonna {col}: {null_count} valori null")

    return {
        "valid": len([i for i in issues if "mancanti" in i]) == 0,
        "record_count": len(records),
        "column_count": len(actual_cols),
        "issues": issues
    }
```

---

## Monitoring dell'Estrazione

Ogni estrazione deve tracciare metriche operative per diagnostica e SLA monitoring:

```python
import time
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class ExtractionMetrics:
    source: str
    started_at: float = field(default_factory=time.monotonic)
    rows_extracted: int = 0
    bytes_extracted: int = 0
    batches: int = 0
    errors: int = 0
    finished_at: Optional[float] = None

    @property
    def duration_sec(self) -> float:
        end = self.finished_at or time.monotonic()
        return end - self.started_at

    @property
    def rows_per_second(self) -> float:
        return self.rows_extracted / max(self.duration_sec, 0.001)

    def finish(self):
        self.finished_at = time.monotonic()

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "rows_extracted": self.rows_extracted,
            "bytes_extracted": self.bytes_extracted,
            "batches": self.batches,
            "errors": self.errors,
            "duration_sec": round(self.duration_sec, 2),
            "rows_per_second": round(self.rows_per_second, 0),
        }


def extract_with_metrics(extractor, source_name: str, **kwargs):
    """Wrapper che raccoglie metriche durante l'estrazione."""
    metrics = ExtractionMetrics(source=source_name)
    all_batches = []

    for batch in extractor.extract(**kwargs):
        metrics.rows_extracted += len(batch)
        metrics.batches += 1
        all_batches.append(batch)

    metrics.finish()
    print(f"Estrazione completata: {metrics.to_dict()}")
    return all_batches, metrics
```

---

## Best Practice

**Usa sempre server-side cursor** per tabelle > 100k righe. Un cursore client-side carica tutto in RAM.

**Imposta timeout espliciti** su ogni connessione e query di estrazione. Un'estrazione bloccata può stoppare l'intera pipeline.

**Registra l'high-watermark prima del commit** nel target, non dopo. Se il load fallisce, riparti dall'ultima watermark sicura.

**Non fidarti mai del conteggio totale** restituito dall'API (`total: 1234`). Paginazione over può restituire record duplicati o saltarne.

**Gestisci gli schemi in evoluzione**: nuovi campi possono apparire in qualsiasi momento da API. Usa `*` o raccogli tutti i campi dinamicamente invece di hardcodare colonne.

**Compressione in transito**: usa GZIP sulla rete dove possibile. Per Parquet, il formato stesso è già compresso; per CSV, wrappa in `.gz`.

---

## Riepilogo Pattern di Paginazione

| Pattern | Esempio API | Meccanismo | Pro | Contro |
|---------|-------------|-----------|-----|--------|
| Offset/Limit | REST generico | `?limit=100&offset=200` | Semplice | Inconsistente se insert durante estrazione |
| Cursor | Stripe, Notion | `?after=cur_xxx` | Stabile | Cursor non navigabile |
| Link Header | GitHub, Jira | Header `Link: <url>; rel="next"` | Standard HTTP | Parse complesso |
| Page Number | Legacy | `?page=3&per_page=100` | Familiare | Stessa instabilità di offset |
| GraphQL Relay | Shopify, GitHub v4 | `edges{node}`, `pageInfo` | Standard | Verboso |
| Keyset | Postgres custom | `WHERE id > last_id` | Performante | Richiede PK monotono |
