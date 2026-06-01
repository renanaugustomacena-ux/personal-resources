# Trasformazione dei Dati (Data Transformation)

La trasformazione è il cuore dell'ETL: convertire dati grezzi, eterogenei e spesso sporchi in un formato pulito, standardizzato e pronto per l'analisi. Un layer di trasformazione robusto è la differenza tra un data warehouse affidabile e uno strumento di misinformazione.

## Principi della Trasformazione

### Idempotenza

Ogni trasformazione deve produrre lo stesso output se applicata più volte allo stesso input. Questo permette il re-processing sicuro in caso di errore.

### Immutabilità dei Dati Grezzi

I dati raw non vanno mai modificati. La trasformazione produce un nuovo dataset; l'originale rimane inalterato nel bronze layer.

### Tracciabilità

Ogni record trasformato deve mantenere un riferimento al record sorgente (source_id, source_system, extracted_at) per consentire audit e debugging.

### Fail Fast

Un errore di trasformazione non deve essere ingoiato silenziosamente. Loggare, inviare al DLQ, e continuare con i record validi — mai procedere con dati corrotti.

---

## Pulizia dei Dati

### Normalizzazione di Stringhe

```python
import re
import unicodedata
from typing import Optional

def clean_string(value: Optional[str]) -> Optional[str]:
    """Pulizia base: trim, lowercase, rimozione caratteri non printable."""
    if value is None:
        return None
    value = str(value).strip()
    value = unicodedata.normalize("NFKC", value)  # Normalizza unicode
    value = re.sub(r"[\x00-\x1f\x7f]", "", value)  # Rimuovi control chars
    return value if value else None


def normalize_email(email: Optional[str]) -> Optional[str]:
    """Normalizza e valida email address."""
    if not email:
        return None
    email = email.strip().lower()
    pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, email):
        return None  # Email non valida → None, non stringa vuota
    return email


def normalize_phone(phone: Optional[str], default_country: str = "IT") -> Optional[str]:
    """Normalizza numero di telefono in formato E.164."""
    try:
        import phonenumbers
        parsed = phonenumbers.parse(phone, default_country)
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.E164
            )
    except Exception:
        pass
    return None


def normalize_name(name: Optional[str]) -> Optional[str]:
    """Normalizza nome: title case, rimozione spazi multipli."""
    if not name:
        return None
    name = re.sub(r"\s+", " ", name.strip())
    return name.title()


def normalize_currency(value: Optional[str]) -> Optional[float]:
    """Converte stringa valuta in float: '$1,234.56' → 1234.56"""
    if value is None:
        return None
    cleaned = re.sub(r"[^\d.,\-]", "", str(value))
    # Gestisci formati europei (1.234,56) e americani (1,234.56)
    if "," in cleaned and "." in cleaned:
        if cleaned.rindex(",") > cleaned.rindex("."):
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    elif "," in cleaned and "." not in cleaned:
        if len(cleaned.split(",")[-1]) == 2:
            cleaned = cleaned.replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    try:
        return float(cleaned)
    except ValueError:
        return None
```

### Parsing Date e Timestamp

```python
from datetime import datetime, date, timezone
from typing import Optional, Union
import pytz

COMMON_DATE_FORMATS = [
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%m/%d/%Y",
    "%Y%m%d",
    "%d %b %Y",
    "%d %B %Y",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%d %H:%M:%S",
    "%d/%m/%Y %H:%M:%S",
]

def parse_date(value: Optional[str]) -> Optional[date]:
    """Tenta parsing con formati comuni, restituisce None se fallisce."""
    if not value:
        return None
    value = str(value).strip()
    for fmt in COMMON_DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    # Fallback con dateutil
    try:
        from dateutil import parser as dateutil_parser
        return dateutil_parser.parse(value, dayfirst=True).date()
    except Exception:
        return None


def parse_timestamp_to_utc(
    value: Optional[str],
    source_tz: str = "Europe/Rome"
) -> Optional[datetime]:
    """Converte timestamp con timezone locale in UTC consapevole."""
    if not value:
        return None
    dt = None
    for fmt in COMMON_DATE_FORMATS:
        try:
            dt = datetime.strptime(str(value).strip(), fmt)
            break
        except ValueError:
            continue
    if dt is None:
        try:
            from dateutil import parser as dateutil_parser
            dt = dateutil_parser.parse(str(value).strip())
        except Exception:
            return None

    # Se già timezone-aware, converti in UTC
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc)

    # Localizza nella timezone sorgente, poi converti UTC
    local_tz = pytz.timezone(source_tz)
    dt_local = local_tz.localize(dt, is_dst=None)
    return dt_local.astimezone(pytz.utc)
```

### Deduplica

```python
from typing import List, Dict, Any, Optional

def deduplicate_records(
    records: List[Dict[str, Any]],
    key_columns: List[str],
    tie_breaker_col: str = "updated_at",
    keep: str = "last"
) -> List[Dict[str, Any]]:
    """
    Deduplica mantenendo il record più recente per ogni chiave.
    
    keep='last' → massimo valore tie_breaker (più recente)
    keep='first' → minimo valore tie_breaker (più vecchio)
    """
    grouped: Dict[tuple, Dict] = {}

    for record in records:
        key = tuple(record.get(col) for col in key_columns)
        existing = grouped.get(key)

        if existing is None:
            grouped[key] = record
        else:
            current_ts = record.get(tie_breaker_col)
            existing_ts = existing.get(tie_breaker_col)

            if current_ts is None:
                continue
            if existing_ts is None or (
                (keep == "last" and current_ts > existing_ts) or
                (keep == "first" and current_ts < existing_ts)
            ):
                grouped[key] = record

    return list(grouped.values())


def find_near_duplicates(
    records: List[Dict[str, Any]],
    compare_col: str,
    threshold: float = 0.85
) -> List[tuple]:
    """Trova record quasi-duplicati usando similarità di stringa."""
    from difflib import SequenceMatcher

    duplicates = []
    values = [(i, str(r.get(compare_col, ""))) for i, r in enumerate(records)]

    for i in range(len(values)):
        for j in range(i + 1, min(i + 100, len(values))):  # Finestra locale
            idx_a, val_a = values[i]
            idx_b, val_b = values[j]
            ratio = SequenceMatcher(None, val_a.lower(), val_b.lower()).ratio()
            if ratio >= threshold:
                duplicates.append((idx_a, idx_b, ratio, val_a, val_b))

    return duplicates
```

---

## Trasformazioni Strutturali

### Flatten di Strutture Annidate

```python
from typing import Dict, Any, Optional

def flatten_dict(
    data: Dict[str, Any],
    parent_key: str = "",
    separator: str = "__"
) -> Dict[str, Any]:
    """
    Appiattisce dizionario annidato.
    
    {"user": {"name": "Alice", "address": {"city": "Roma"}}}
    → {"user__name": "Alice", "user__address__city": "Roma"}
    """
    items = []
    for key, value in data.items():
        new_key = f"{parent_key}{separator}{key}" if parent_key else key
        if isinstance(value, dict):
            items.extend(flatten_dict(value, new_key, separator).items())
        elif isinstance(value, list):
            # Array → converti in JSON string o esplodi
            items.append((new_key, str(value)))
        else:
            items.append((new_key, value))
    return dict(items)


def explode_list_field(
    records: List[Dict[str, Any]],
    list_field: str
) -> List[Dict[str, Any]]:
    """
    Esplode campo array: una riga per elemento.
    
    {"id": 1, "tags": ["python", "etl"]}
    → [{"id": 1, "tag": "python"}, {"id": 1, "tag": "etl"}]
    """
    result = []
    singular = list_field.rstrip("s")  # tags → tag (euristica)
    for record in records:
        items = record.get(list_field, [])
        if not items:
            row = {k: v for k, v in record.items() if k != list_field}
            row[singular] = None
            result.append(row)
        else:
            for item in items:
                row = {k: v for k, v in record.items() if k != list_field}
                row[singular] = item
                result.append(row)
    return result
```

### Pivot e Unpivot

```python
import pandas as pd

def pivot_metrics(
    df: pd.DataFrame,
    index_cols: List[str],
    column_col: str,
    value_col: str
) -> pd.DataFrame:
    """
    Trasforma formato long in wide.
    
    | customer_id | metric_name  | value |
    |-------------|--------------|-------|
    | 1           | revenue      | 1000  |
    | 1           | orders       | 5     |
    
    → | customer_id | revenue | orders |
      |-------------|---------|--------|
      | 1           | 1000    | 5      |
    """
    return df.pivot_table(
        index=index_cols,
        columns=column_col,
        values=value_col,
        aggfunc="first"
    ).reset_index().rename_axis(None, axis=1)


def unpivot_wide_to_long(
    df: pd.DataFrame,
    id_vars: List[str],
    value_vars: List[str],
    var_name: str = "metric",
    value_name: str = "value"
) -> pd.DataFrame:
    """
    Trasforma formato wide in long (melt).
    
    | id | jan_sales | feb_sales |
    |----|-----------|-----------|
    | 1  | 100       | 150       |
    
    → | id | month     | sales |
      |----|-----------|-------|
      | 1  | jan_sales | 100   |
      | 1  | feb_sales | 150   |
    """
    return df.melt(
        id_vars=id_vars,
        value_vars=value_vars,
        var_name=var_name,
        value_name=value_name
    )
```

---

## Business Logic Transformation

### Calcoli Derivati

```python
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any

def apply_tax(
    amount: Optional[float],
    tax_rate: float = 0.22,
    country: str = "IT"
) -> Optional[Dict[str, float]]:
    """Calcola importo tasse e totale lordo."""
    if amount is None:
        return None
    net = Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    tax = (net * Decimal(str(tax_rate))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    gross = net + tax
    return {
        "net_amount": float(net),
        "tax_amount": float(tax),
        "gross_amount": float(gross),
        "tax_rate": tax_rate,
        "tax_country": country
    }


def categorize_customer(
    lifetime_value: Optional[float],
    order_count: Optional[int]
) -> str:
    """Segmentazione clienti basata su LTV e frequenza."""
    if lifetime_value is None or order_count is None:
        return "unknown"
    if lifetime_value >= 10_000 or order_count >= 50:
        return "vip"
    elif lifetime_value >= 1_000 or order_count >= 10:
        return "regular"
    elif order_count >= 2:
        return "returning"
    else:
        return "new"


def calculate_age_bucket(birth_date: Optional[date]) -> Optional[str]:
    """Classifica età in fasce standard."""
    if birth_date is None:
        return None
    today = date.today()
    age = (today - birth_date).days // 365
    if age < 18:
        return "under_18"
    elif age < 25:
        return "18_24"
    elif age < 35:
        return "25_34"
    elif age < 45:
        return "35_44"
    elif age < 55:
        return "45_54"
    elif age < 65:
        return "55_64"
    else:
        return "65_plus"
```

### Lookup ed Enrichment

```python
from typing import Dict, Any, Optional

class LookupEnricher:
    """Arricchisce record con dati da tabelle di lookup."""

    def __init__(self, conn_params: dict):
        self.conn_params = conn_params
        self._cache: Dict[str, Dict] = {}

    def load_lookup(
        self,
        lookup_name: str,
        query: str,
        key_col: str
    ) -> Dict[str, Dict]:
        """Carica lookup in memoria per join efficiente."""
        import psycopg2
        from psycopg2.extras import RealDictCursor

        conn = psycopg2.connect(**self.conn_params)
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            rows = cur.fetchall()

        self._cache[lookup_name] = {str(row[key_col]): dict(row) for row in rows}
        conn.close()
        print(f"Lookup '{lookup_name}' caricato: {len(self._cache[lookup_name])} voci")
        return self._cache[lookup_name]

    def enrich_record(
        self,
        record: Dict[str, Any],
        lookup_name: str,
        join_key: str,
        prefix: str = "",
        columns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Arricchisce record con campi dal lookup."""
        lookup = self._cache.get(lookup_name, {})
        join_value = str(record.get(join_key, ""))
        lookup_row = lookup.get(join_value)

        result = dict(record)
        if lookup_row:
            cols = columns or list(lookup_row.keys())
            for col in cols:
                result[f"{prefix}{col}" if prefix else col] = lookup_row.get(col)
        return result

    def enrich_batch(
        self,
        records: List[Dict[str, Any]],
        lookup_name: str,
        join_key: str,
        prefix: str = "",
        columns: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Arricchisce un batch di record."""
        return [
            self.enrich_record(r, lookup_name, join_key, prefix, columns)
            for r in records
        ]
```

---

## SCD Type 2 Logic

Il calcolo delle dimensioni slowly-changing di tipo 2 è una delle trasformazioni più critiche in un data warehouse:

```python
from datetime import datetime, date
from typing import List, Dict, Any, Optional

def apply_scd2_logic(
    new_records: List[Dict[str, Any]],
    existing_records: List[Dict[str, Any]],
    business_key: str,
    tracked_columns: List[str],
    effective_date_col: str = "valid_from",
    expiry_date_col: str = "valid_to",
    current_flag_col: str = "is_current",
    surrogate_key_prefix: str = "sk"
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Applica logica SCD2:
    - record invariati → nessuna azione
    - record modificati → chiudi vecchio, inserisci nuovo
    - record nuovi → inserisci
    - record cancellati → chiudi (soft delete)
    
    Restituisce {inserts: [...], updates: [...]}
    """
    today = date.today().isoformat()
    FAR_FUTURE = "9999-12-31"
    
    # Indicizza esistenti per business key
    existing_index = {
        str(r[business_key]): r
        for r in existing_records
        if r.get(current_flag_col)
    }

    inserts = []
    updates = []

    new_keys = set()
    for new_rec in new_records:
        bk = str(new_rec[business_key])
        new_keys.add(bk)
        existing = existing_index.get(bk)

        if existing is None:
            # Nuovo record
            row = dict(new_rec)
            row[effective_date_col] = today
            row[expiry_date_col] = FAR_FUTURE
            row[current_flag_col] = True
            inserts.append(row)
        else:
            # Controlla se qualche colonna tracciata è cambiata
            changed = any(
                str(new_rec.get(col)) != str(existing.get(col))
                for col in tracked_columns
            )
            if changed:
                # Chiudi il vecchio record
                close_update = {
                    "id": existing.get("id"),
                    business_key: bk,
                    expiry_date_col: today,
                    current_flag_col: False
                }
                updates.append(close_update)

                # Inserisci il nuovo record
                row = dict(new_rec)
                row[effective_date_col] = today
                row[expiry_date_col] = FAR_FUTURE
                row[current_flag_col] = True
                inserts.append(row)

    # Record cancellati dalla sorgente (soft delete)
    for bk, existing in existing_index.items():
        if bk not in new_keys and existing.get(current_flag_col):
            close_update = {
                "id": existing.get("id"),
                business_key: bk,
                expiry_date_col: today,
                current_flag_col: False,
                "_deleted": True
            }
            updates.append(close_update)

    return {"inserts": inserts, "updates": updates}
```

---

## Pipeline di Trasformazione con Composizione

### Transformer Chain

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Callable
import logging

logger = logging.getLogger(__name__)

class Transformer(ABC):
    """Interfaccia base per trasformatori componibili."""

    @abstractmethod
    def transform(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        pass

    def __call__(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return self.transform(records)


class FunctionTransformer(Transformer):
    """Wrappa una funzione Python in un Transformer."""
    def __init__(self, func: Callable, name: str = ""):
        self.func = func
        self.name = name or func.__name__

    def transform(self, records):
        return [self.func(r) for r in records]


class FilterTransformer(Transformer):
    """Filtra record che non soddisfano una condizione."""
    def __init__(self, predicate: Callable[[Dict], bool], name: str = ""):
        self.predicate = predicate
        self.name = name

    def transform(self, records):
        valid = [r for r in records if self.predicate(r)]
        dropped = len(records) - len(valid)
        if dropped:
            logger.warning(f"Filter '{self.name}': scartati {dropped}/{len(records)} record")
        return valid


class TransformationPipeline:
    """Catena di trasformatori applicati in sequenza."""

    def __init__(self, transformers: List[Transformer] = None):
        self.transformers = transformers or []

    def add(self, transformer: Transformer) -> "TransformationPipeline":
        self.transformers.append(transformer)
        return self

    def execute(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        result = records
        for t in self.transformers:
            name = getattr(t, "name", t.__class__.__name__)
            before = len(result)
            result = t.transform(result)
            after = len(result)
            if before != after:
                logger.info(f"Dopo '{name}': {before} → {after} record")
        return result


# Esempio di utilizzo
def build_customer_pipeline(enricher: LookupEnricher) -> TransformationPipeline:
    return (
        TransformationPipeline()
        .add(FunctionTransformer(
            lambda r: {**r, "email": normalize_email(r.get("email"))},
            name="normalize_email"
        ))
        .add(FunctionTransformer(
            lambda r: {**r, "phone": normalize_phone(r.get("phone"))},
            name="normalize_phone"
        ))
        .add(FilterTransformer(
            lambda r: r.get("email") is not None,
            name="require_email"
        ))
        .add(FunctionTransformer(
            lambda r: {**r, "name": normalize_name(r.get("name"))},
            name="normalize_name"
        ))
        .add(FunctionTransformer(
            lambda r: enricher.enrich_record(r, "countries", "country_code", "country_"),
            name="enrich_country"
        ))
        .add(FunctionTransformer(
            lambda r: {**r, "segment": categorize_customer(
                r.get("lifetime_value"), r.get("order_count")
            )},
            name="segment_customer"
        ))
    )
```

---

## Trasformazioni con Pandas e PySpark

### Pandas per Batch di Medie Dimensioni

```python
import pandas as pd
import numpy as np

def transform_sales_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Trasformazione di un batch vendite con Pandas."""
    
    # Copia difensiva — no mutazioni in-place
    result = df.copy()

    # Pulizia tipo
    result["amount"] = pd.to_numeric(result["amount"], errors="coerce")
    result["sale_date"] = pd.to_datetime(result["sale_date"], errors="coerce")

    # Rimuovi righe con dati critici mancanti
    result = result.dropna(subset=["customer_id", "product_id", "amount"])

    # Derived columns
    result["year_month"] = result["sale_date"].dt.to_period("M").astype(str)
    result["quarter"] = "Q" + result["sale_date"].dt.quarter.astype(str)
    result["tax_amount"] = (result["amount"] * 0.22).round(2)
    result["gross_amount"] = result["amount"] + result["tax_amount"]

    # Normalizza stringa
    result["customer_email"] = result["customer_email"].str.strip().str.lower()

    # Outlier handling: clippa amount a 99° percentile
    p99 = result["amount"].quantile(0.99)
    result["amount_capped"] = result["amount"].clip(upper=p99)
    result["is_outlier"] = result["amount"] > p99

    return result
```

### PySpark per Dataset di Grandi Dimensioni

```python
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType, TimestampType

def transform_sales_spark(df: DataFrame) -> DataFrame:
    """Trasformazione batch vendite con PySpark."""

    return (
        df
        # Cast dei tipi
        .withColumn("amount", F.col("amount").cast(DoubleType()))
        .withColumn("sale_date", F.to_timestamp("sale_date"))
        
        # Filtra null su colonne critiche
        .filter(
            F.col("customer_id").isNotNull() &
            F.col("product_id").isNotNull() &
            F.col("amount").isNotNull()
        )
        
        # Colonne derivate
        .withColumn("year_month", F.date_format("sale_date", "yyyy-MM"))
        .withColumn("quarter", F.concat(F.lit("Q"), F.quarter("sale_date")))
        .withColumn("tax_amount", F.round(F.col("amount") * 0.22, 2))
        .withColumn("gross_amount", F.col("amount") + F.col("tax_amount"))
        
        # Normalizza email
        .withColumn("customer_email",
                    F.trim(F.lower(F.col("customer_email"))))
        
        # Outlier flag con percentile approssimato
        .withColumn("is_outlier",
                    F.col("amount") > F.lit(
                        df.approxQuantile("amount", [0.99], 0.01)[0]
                    ))
    )
```

---

## Gestione degli Errori di Trasformazione

### Dead Letter Queue Pattern

```python
import json
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple
from datetime import datetime

@dataclass
class TransformationError:
    record: Dict[str, Any]
    error_type: str
    error_message: str
    transformer_name: str
    occurred_at: str = None

    def __post_init__(self):
        if self.occurred_at is None:
            self.occurred_at = datetime.utcnow().isoformat()

    def to_dict(self) -> dict:
        return {
            "original_record": self.record,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "transformer": self.transformer_name,
            "occurred_at": self.occurred_at
        }


class FaultTolerantPipeline:
    """Pipeline che isola gli errori senza fermare il processing."""

    def __init__(self, transformers: List[Transformer]):
        self.transformers = transformers
        self.dead_letter_queue: List[TransformationError] = []

    def execute(
        self,
        records: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[TransformationError]]:
        """
        Ritorna (record_validi, errori).
        Record che falliscono vanno in DLQ, non bloccano la pipeline.
        """
        valid = []
        errors = []

        for record in records:
            current = record
            record_failed = False

            for transformer in self.transformers:
                name = getattr(transformer, "name", transformer.__class__.__name__)
                try:
                    result = transformer.transform([current])
                    if not result:
                        err = TransformationError(
                            record=current,
                            error_type="FilteredOut",
                            error_message=f"Record filtrato da '{name}'",
                            transformer_name=name
                        )
                        errors.append(err)
                        record_failed = True
                        break
                    current = result[0]
                except Exception as e:
                    err = TransformationError(
                        record=current,
                        error_type=type(e).__name__,
                        error_message=str(e),
                        transformer_name=name
                    )
                    errors.append(err)
                    record_failed = True
                    break

            if not record_failed:
                valid.append(current)

        return valid, errors

    def flush_dlq_to_file(self, path: str):
        """Persiste DLQ su file JSONL per re-processing manuale."""
        with open(path, "a") as f:
            for err in self.dead_letter_queue:
                f.write(json.dumps(err.to_dict()) + "\n")
        self.dead_letter_queue.clear()
```

---

## Testing delle Trasformazioni

Le trasformazioni sono funzioni pure (input → output) e quindi facilmente testabili con unit test senza dipendenze esterne:

```python
import pytest

class TestNormalizeEmail:
    def test_valid_email_lowercase(self):
        assert normalize_email("ALICE@EXAMPLE.COM") == "alice@example.com"

    def test_strips_whitespace(self):
        assert normalize_email("  alice@example.com  ") == "alice@example.com"

    def test_invalid_email_returns_none(self):
        assert normalize_email("not-an-email") is None

    def test_none_returns_none(self):
        assert normalize_email(None) is None

    def test_empty_string_returns_none(self):
        assert normalize_email("") is None


class TestNormalizeCurrency:
    @pytest.mark.parametrize("input_val,expected", [
        ("$1,234.56", 1234.56),
        ("€1.234,56", 1234.56),
        ("1000", 1000.0),
        ("  -500.25  ", -500.25),
        (None, None),
        ("abc", None),
    ])
    def test_currency_formats(self, input_val, expected):
        assert normalize_currency(input_val) == expected


class TestDeduplication:
    def test_keeps_most_recent(self):
        records = [
            {"id": 1, "name": "Alice", "updated_at": "2024-01-01"},
            {"id": 1, "name": "Alice Updated", "updated_at": "2024-06-01"},
        ]
        result = deduplicate_records(records, ["id"], "updated_at")
        assert len(result) == 1
        assert result[0]["name"] == "Alice Updated"

    def test_different_keys_both_kept(self):
        records = [
            {"id": 1, "name": "Alice", "updated_at": "2024-01-01"},
            {"id": 2, "name": "Bob", "updated_at": "2024-01-01"},
        ]
        result = deduplicate_records(records, ["id"], "updated_at")
        assert len(result) == 2
```

---

## Best Practice

**Non trasformare nella query di estrazione** — separa estrazione e trasformazione. Rende il debugging più semplice e permette di riprocessare i raw senza riestrarre dalla sorgente.

**Usa Pandas per < 10M righe**, PySpark o DuckDB per dataset più grandi. Non overengineer con Spark per batch piccoli.

**Ogni trasformazione deve essere testata singolarmente** con input noti prima di integrarla nella pipeline.

**Loggare il numero di record prima e dopo ogni step** di filtraggio. Un drop imprevisto è il primo segnale di un bug.

**Mantieni i dati raw inalterati** nel bronze layer S3/GCS. Ogni trasformazione produce nuovi file/tabelle — non sovrascrive quelli originali.

**Gestisci i null esplicitamente** — non lasciare che i null si propaghino silenziosamente attraverso calcoli che restituiscono null anziché errori.
