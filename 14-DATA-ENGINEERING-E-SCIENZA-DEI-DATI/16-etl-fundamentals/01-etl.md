# ETL: Fondamenti di Extract, Transform, Load

ETL (Extract, Transform, Load) è il processo fondamentale con cui i dati vengono spostati da sistemi sorgente verso sistemi di destinazione, tipicamente un data warehouse o un data lake. Ogni fase ha responsabilità precise e sfide specifiche. Comprendere ETL a fondo significa comprendere come funziona la "plomberia" dei dati aziendali.

## Le Tre Fasi

### Extract: Estrazione

La fase di estrazione connette le sorgenti dati e ne recupera i dati. Le sorgenti possono essere estremamente eterogenee: database relazionali, file flat (CSV, JSON, XML), API REST, stream di eventi (Kafka), code di messaggi, file su object storage (S3).

```python
# Estrattori per diverse sorgenti

import psycopg2
import requests
import boto3
import pandas as pd
from kafka import KafkaConsumer
from abc import ABC, abstractmethod
from typing import Iterator, Dict, Any

class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, **kwargs) -> Iterator[Dict[str, Any]]:
        """Genera record uno alla volta (streaming) o in batch."""
        pass

class PostgreSQLExtractor(BaseExtractor):
    """Estrae dati da PostgreSQL con supporto per caricamento incrementale."""
    
    def __init__(self, dsn: str):
        self.dsn = dsn
    
    def extract(self, query: str, params: dict = None, batch_size: int = 10000):
        """Estrae in batch per non saturare la memoria."""
        with psycopg2.connect(self.dsn) as conn:
            with conn.cursor('streaming_cursor') as cur:  # server-side cursor
                cur.execute(query, params)
                
                while True:
                    rows = cur.fetchmany(batch_size)
                    if not rows:
                        break
                    
                    col_names = [desc[0] for desc in cur.description]
                    for row in rows:
                        yield dict(zip(col_names, row))

class RestApiExtractor(BaseExtractor):
    """Estrae dati da una REST API con paginazione automatica."""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {'Authorization': f'Bearer {api_key}'}
    
    def extract(self, endpoint: str, params: dict = None):
        """Gestisce la paginazione cursor-based e offset-based."""
        url = f"{self.base_url}{endpoint}"
        page_params = dict(params or {})
        
        while url:
            response = requests.get(url, headers=self.headers, params=page_params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Supporta diverse strutture di risposta paginate
            records = data.get('data', data.get('results', data if isinstance(data, list) else []))
            
            for record in records:
                yield record
            
            # Paginazione: prova cursor, poi offset, poi link header
            next_cursor = data.get('next_cursor') or data.get('meta', {}).get('next_cursor')
            if next_cursor:
                page_params['cursor'] = next_cursor
            elif 'next' in data.get('links', {}):
                url = data['links']['next']
                page_params = {}
            elif data.get('has_more'):
                page_params['offset'] = page_params.get('offset', 0) + len(records)
            else:
                break

class S3FileExtractor(BaseExtractor):
    """Estrae file da S3/Object Storage."""
    
    def __init__(self, bucket: str, aws_region: str = 'eu-west-1'):
        self.s3 = boto3.client('s3', region_name=aws_region)
        self.bucket = bucket
    
    def extract(self, prefix: str, file_format: str = 'csv', since_date: str = None):
        """Elenca e legge i file S3 con filtro per data."""
        paginator = self.s3.get_paginator('list_objects_v2')
        
        for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
            for obj in page.get('Contents', []):
                key = obj['Key']
                
                # Filtro per data di modifica
                if since_date:
                    import datetime
                    obj_date = obj['LastModified'].strftime('%Y-%m-%d')
                    if obj_date < since_date:
                        continue
                
                # Leggere il file
                response = self.s3.get_object(Bucket=self.bucket, Key=key)
                
                if file_format == 'csv':
                    df = pd.read_csv(response['Body'])
                elif file_format == 'json':
                    df = pd.read_json(response['Body'], lines=True)
                elif file_format == 'parquet':
                    import pyarrow.parquet as pq
                    import io
                    df = pq.read_table(io.BytesIO(response['Body'].read())).to_pandas()
                
                for _, row in df.iterrows():
                    yield row.to_dict()
```

### Transform: Trasformazione

La fase di trasformazione è dove i dati vengono puliti, arricchiti, e modellati per la destinazione. È la fase più complessa e dove si concentra la maggior parte della business logic.

```python
from typing import Optional, Dict, Any, List
import re
from datetime import datetime, timezone

class DataTransformer:
    """
    Trasformazioni comuni per dati in ingresso.
    Ogni metodo è puro e testabile indipendentemente.
    """
    
    @staticmethod
    def clean_email(email: Optional[str]) -> Optional[str]:
        """Normalizza e valida email."""
        if not email:
            return None
        email = email.strip().lower()
        pattern = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
        return email if re.match(pattern, email) else None
    
    @staticmethod
    def parse_currency(value: Any, currency: str = 'EUR') -> Optional[float]:
        """Converte stringhe di valuta in float."""
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        
        # Rimuovere simboli di valuta, spazi, separatori
        cleaned = re.sub(r'[€$£,\s]', '', str(value))
        cleaned = cleaned.replace(',', '.') if ',' in cleaned and '.' not in cleaned else cleaned
        
        try:
            return float(cleaned)
        except ValueError:
            return None
    
    @staticmethod
    def standardize_phone(phone: Optional[str], country_code: str = '+39') -> Optional[str]:
        """Normalizza numeri di telefono al formato internazionale."""
        if not phone:
            return None
        
        digits = re.sub(r'\D', '', phone)
        
        if digits.startswith('00'):
            digits = '+' + digits[2:]
        elif not digits.startswith('+') and len(digits) == 10:
            digits = country_code + digits
        
        return digits
    
    @staticmethod
    def deduplicate(records: List[Dict], key_fields: List[str], keep: str = 'last') -> List[Dict]:
        """
        Deduplicazione in-memory per batch piccoli.
        Per dataset grandi: usare SQL DISTINCT o ROW_NUMBER().
        """
        seen = {}
        for record in records:
            key = tuple(record.get(f) for f in key_fields)
            if keep == 'last' or key not in seen:
                seen[key] = record
        
        return list(seen.values())
    
    @staticmethod
    def enrich_with_lookup(record: Dict, lookup_table: Dict, key_field: str, target_field: str, 
                           fallback: Any = None) -> Dict:
        """Arricchisce un record con dati da una tabella di lookup."""
        key = record.get(key_field)
        enriched = {**record}
        enriched[target_field] = lookup_table.get(key, fallback)
        return enriched
    
    @staticmethod
    def apply_scd2_logic(existing: Optional[Dict], incoming: Dict, 
                         business_key: str, tracked_fields: List[str]) -> List[Dict]:
        """
        Applica la logica SCD2: restituisce le righe da inserire/aggiornare.
        """
        today = datetime.now(timezone.utc).date().isoformat()
        
        if existing is None:
            # Nuovo record
            return [{
                **incoming,
                'is_current': True,
                'effective_from': today,
                'effective_to': None
            }]
        
        # Verificare se sono cambiati i campi tracciati
        changed = any(existing.get(f) != incoming.get(f) for f in tracked_fields)
        
        if not changed:
            return []  # nessuna modifica necessaria
        
        # SCD2: chiudere il record corrente e aprirne uno nuovo
        closed = {**existing, 'is_current': False, 'effective_to': today}
        new_record = {
            **incoming,
            'is_current': True,
            'effective_from': today,
            'effective_to': None
        }
        
        return [closed, new_record]
```

### Load: Caricamento

La fase di caricamento scrive i dati trasformati nella destinazione. Le strategie di caricamento impattano le performance e la consistenza.

```python
import psycopg2
from psycopg2.extras import execute_values
from typing import List, Dict

class DataLoader:
    """Strategie di caricamento per diversi scenari."""
    
    def __init__(self, dsn: str):
        self.dsn = dsn
    
    def bulk_insert(self, table: str, records: List[Dict], batch_size: int = 10000):
        """
        Inserimento massivo con execute_values (molto più veloce di INSERT singoli).
        """
        if not records:
            return 0
        
        columns = list(records[0].keys())
        
        with psycopg2.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                # execute_values è 10-100x più veloce di executemany
                sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES %s"
                
                total = 0
                for i in range(0, len(records), batch_size):
                    batch = records[i:i + batch_size]
                    values = [[r[col] for col in columns] for r in batch]
                    execute_values(cur, sql, values)
                    total += len(batch)
                
                return total
    
    def upsert(self, table: str, records: List[Dict], conflict_columns: List[str]):
        """
        INSERT ... ON CONFLICT DO UPDATE (upsert).
        Usato per aggiornamento incrementale con deduplicazione.
        """
        if not records:
            return
        
        columns = list(records[0].keys())
        update_columns = [c for c in columns if c not in conflict_columns]
        
        sql = f"""
            INSERT INTO {table} ({', '.join(columns)})
            VALUES %s
            ON CONFLICT ({', '.join(conflict_columns)})
            DO UPDATE SET {', '.join(f"{c} = EXCLUDED.{c}" for c in update_columns)}
        """
        
        with psycopg2.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                values = [[r[col] for col in columns] for r in records]
                execute_values(cur, sql, values)
    
    def staging_and_merge(self, target_table: str, staging_table: str, records: List[Dict],
                           merge_key: str):
        """
        Pattern staging → merge: carica in una tabella temporanea, poi merge.
        Più affidabile dell'upsert diretto per grandi volumi.
        """
        with psycopg2.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                # 1. Creare staging table
                cur.execute(f"CREATE TEMP TABLE {staging_table} AS SELECT * FROM {target_table} LIMIT 0")
                
                # 2. Caricare nello staging
                columns = list(records[0].keys()) if records else []
                if records:
                    values = [[r.get(col) for col in columns] for r in records]
                    execute_values(
                        cur,
                        f"INSERT INTO {staging_table} ({', '.join(columns)}) VALUES %s",
                        values
                    )
                
                # 3. Merge: UPDATE dei record esistenti
                non_key_cols = [c for c in columns if c != merge_key]
                cur.execute(f"""
                    UPDATE {target_table} t
                    SET {', '.join(f"{c} = s.{c}" for c in non_key_cols)}
                    FROM {staging_table} s
                    WHERE t.{merge_key} = s.{merge_key}
                """)
                
                # 4. INSERT dei record nuovi
                cur.execute(f"""
                    INSERT INTO {target_table}
                    SELECT s.*
                    FROM {staging_table} s
                    LEFT JOIN {target_table} t ON t.{merge_key} = s.{merge_key}
                    WHERE t.{merge_key} IS NULL
                """)
                
                conn.commit()
```

## Pattern ETL Comuni

### Pattern 1: Incremental Load con Timestamp

```python
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def incremental_load(
    extractor: PostgreSQLExtractor,
    transformer: DataTransformer,
    loader: DataLoader,
    watermark_table: str,
    source_table: str,
    target_table: str
):
    """
    Caricamento incrementale con high-water mark.
    Robusto a riavvii: il watermark è aggiornato atomicamente con il caricamento.
    """
    # Recuperare il watermark
    with psycopg2.connect(loader.dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT last_loaded_at FROM etl_watermarks WHERE table_name = %s",
                (source_table,)
            )
            row = cur.fetchone()
            last_loaded = row[0] if row else '2000-01-01'
    
    logger.info(f"Estrazione {source_table} da {last_loaded}")
    
    # Estrarre solo i nuovi record
    records = list(extractor.extract(
        query=f"SELECT * FROM {source_table} WHERE updated_at > %(since)s ORDER BY updated_at",
        params={'since': last_loaded}
    ))
    
    if not records:
        logger.info("Nessun nuovo record")
        return
    
    # Trasformare
    transformed = [DataTransformer.clean_record(r) for r in records]
    
    # Caricare
    loader.upsert(target_table, transformed, conflict_columns=['id'])
    
    # Aggiornare il watermark (atomicamente nella stessa transazione del caricamento)
    new_watermark = max(r['updated_at'] for r in records)
    with psycopg2.connect(loader.dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO etl_watermarks (table_name, last_loaded_at)
                VALUES (%s, %s)
                ON CONFLICT (table_name) DO UPDATE SET last_loaded_at = EXCLUDED.last_loaded_at
            """, (source_table, new_watermark))
    
    logger.info(f"Caricati {len(records)} record. Watermark: {new_watermark}")
```

### Pattern 2: Error Handling e Dead Letter Queue

```python
def etl_with_error_handling(records, transformer, loader, dlq_table: str):
    """
    ETL robusto con dead letter queue per record problematici.
    I record che falliscono vengono salvati separatamente per analisi manuale.
    """
    successful = []
    failed = []
    
    for record in records:
        try:
            transformed = transformer.transform(record)
            successful.append(transformed)
        except Exception as e:
            failed.append({
                'original_record': record,
                'error_message': str(e),
                'error_type': type(e).__name__,
                'failed_at': datetime.utcnow().isoformat()
            })
    
    # Caricare i record buoni
    if successful:
        loader.bulk_insert('target_table', successful)
    
    # Salvare i record falliti nella DLQ
    if failed:
        loader.bulk_insert(dlq_table, failed)
        logger.warning(f"{len(failed)} record in DLQ, {len(successful)} caricati con successo")
    
    return len(successful), len(failed)
```

## Idempotenza

Un processo ETL idempotente può essere eseguito più volte con lo stesso risultato. Questa è la proprietà più importante per la robustezza del pipeline.

```python
# SBAGLIATO: non idempotente
# Se il job riparte dopo un crash, carica i dati due volte
def load_non_idempotent(records):
    cursor.executemany("INSERT INTO orders VALUES (%s, %s, %s)", records)

# CORRETTO: idempotente con ON CONFLICT DO NOTHING
def load_idempotent(records):
    cursor.executemany(
        "INSERT INTO orders VALUES (%s, %s, %s) ON CONFLICT (order_id) DO NOTHING",
        records
    )

# CORRETTO: idempotente con staging + MERGE
def load_with_staging(records, date_partition):
    """
    Usa una data come partizione: il job per una data può essere
    rieseguito N volte con lo stesso risultato.
    """
    cursor.execute(f"DELETE FROM fact_sales WHERE date_key = {date_partition}")
    cursor.executemany("INSERT INTO fact_sales VALUES (%s, %s, %s)", records)
    # La DELETE + INSERT è atomica nella stessa transazione
```

