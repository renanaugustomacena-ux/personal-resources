# Tutorial 14 — Data Processing in Python: Pandas, Polars, NumPy

> **Companion a:** `14-data-processing.md`
> **Scope:** pandas 2.x, Polars, NumPy, trasformazioni dati, pipeline ETL, ottimizzazione memoria
> **Prerequisiti:** `tutorial_01_fondamenti_linguaggio.md`, `tutorial_04_decoratori_generatori_context_manager.md`
> **Durata stimata:** 18-22 ore
> **Stack:** Python 3.12+, pandas 2.2+, polars 0.20+, numpy 1.26+

---

## Mappa concettuale

```
Data Processing in Python
│
├── NumPy — Array numerici N-dimensionali
│   ├── ndarray — struttura dati fondamentale
│   ├── Broadcasting — operazioni vettorizzate
│   ├── Ufunc — funzioni universali veloci
│   └── Indexing avanzato (fancy, boolean)
│
├── Pandas — DataFrame e Series
│   ├── DataFrame — tabella 2D tipizzata
│   ├── Series — colonna singola
│   ├── Index — etichette righe
│   ├── IO — CSV, Parquet, JSON, SQL, Excel
│   ├── Trasformazioni — groupby, merge, pivot
│   ├── Missing data — NaN, fillna, dropna
│   └── Dtypes ottimizzati — category, Int64, StringDtype
│
├── Polars — DataFrame moderno (Rust)
│   ├── Lazy API — ottimizzazione query
│   ├── Eager API — esecuzione immediata
│   ├── Expressions — trasformazioni composable
│   ├── Context — select, with_columns, filter, groupby
│   └── Performance — 5-100x più veloce di pandas
│
└── Pipeline ETL
    ├── Extract — lettura dati grezzi
    ├── Transform — pulizia, normalizzazione, aggregazione
    └── Load — salvataggio in formato ottimizzato
```

---

# Parte A — NumPy: basi solide

---

## A1. Array e operazioni fondamentali

```python
import numpy as np

# Creazione array
a = np.array([1, 2, 3, 4, 5], dtype=np.float64)
m = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.int32)

# Array speciali
zeros = np.zeros((3, 4))
ones = np.ones((2, 3))
identita = np.eye(4)
range_arr = np.arange(0, 10, 0.5)     # da 0 a 10 step 0.5
linspace = np.linspace(0, 1, 100)     # 100 punti equidistanti
random = np.random.default_rng(42).standard_normal((100, 10))

# Shape, dtype, dimensioni
print(m.shape)     # (2, 3)
print(m.dtype)     # int32
print(m.ndim)      # 2
print(m.size)      # 6
print(m.nbytes)    # 24 (6 * 4 bytes)

# Operazioni vettorizzate — molto più veloci dei loop Python
a = np.array([1.0, 2.0, 3.0, 4.0])
b = np.array([10.0, 20.0, 30.0, 40.0])

somma = a + b           # [11, 22, 33, 44]
prodotto = a * b        # [10, 40, 90, 160]
quadrato = a ** 2       # [1, 4, 9, 16]
radice = np.sqrt(a)
log_nat = np.log(a)
```

> **Analogia:** NumPy è come un foglio Excel con superpoteri matematici. Invece di calcolare cella per cella, operi su intere colonne simultaneamente. Quando scrivi `a + b`, NumPy esegue l'operazione su tutti gli elementi in C, non in Python — per questo è 100-1000x più veloce di un loop `for`.

---

## A2. Broadcasting e indexing

```python
import numpy as np

# Broadcasting — operazioni tra array di shape diverse
m = np.array([[1, 2, 3], [4, 5, 6]])   # shape (2, 3)
v = np.array([10, 20, 30])              # shape (3,)

# v viene "broadcast" su ogni riga di m
risultato = m + v   # [[11, 22, 33], [14, 25, 36]]

# Scalar broadcasting
normalizzato = (m - m.mean()) / m.std()

# Indexing semplice
arr = np.arange(10)
print(arr[3])       # 3
print(arr[-1])      # 9
print(arr[2:5])     # [2, 3, 4]
print(arr[::2])     # [0, 2, 4, 6, 8]

# Indexing 2D
m = np.arange(12).reshape(3, 4)
print(m[1, 2])      # elemento riga 1, col 2
print(m[:, 1])      # tutta la colonna 1
print(m[0:2, 1:3])  # submatrix

# Boolean indexing
dati = np.array([1.5, -0.3, 2.1, -1.2, 0.8])
positivi = dati[dati > 0]     # [1.5, 2.1, 0.8]
mask = np.abs(dati) > 1.0
dati[mask] = 0   # azzera valori |x| > 1

# Fancy indexing
indici = [0, 2, 4]
selezionati = dati[indici]   # elementi 0, 2, 4
```

---

## A3. Operazioni matriciali e aggregazioni

```python
import numpy as np

# Aggregazioni
a = np.array([[1, 2, 3], [4, 5, 6]])
print(a.sum())           # 21 — tutto
print(a.sum(axis=0))     # [5, 7, 9] — per colonna
print(a.sum(axis=1))     # [6, 15] — per riga
print(a.mean())          # 3.5
print(a.std())
print(a.min(), a.max())
print(a.argmin(), a.argmax())   # indici del min/max

# Algebra lineare
A = np.array([[1, 2], [3, 4]])
B = np.array([[5, 6], [7, 8]])
prodotto_matriciale = A @ B      # matrix multiply
trasposta = A.T
determinante = np.linalg.det(A)
inversa = np.linalg.inv(A)
autovalori, autovettori = np.linalg.eig(A)

# Sorting
dati = np.array([3, 1, 4, 1, 5, 9, 2, 6])
ordinati = np.sort(dati)
indici_ord = np.argsort(dati)    # indici che ordinerebbero
```

---

# Parte B — Pandas 2.x: analisi dati pratica

---

## B1. DataFrame e Series

```python
import pandas as pd
import numpy as np

# Creazione DataFrame
df = pd.DataFrame({
    "nome": ["Alice", "Bob", "Carlo", "Diana"],
    "eta": [25, 32, 28, 35],
    "citta": ["Roma", "Milano", "Roma", "Napoli"],
    "stipendio": [35000.0, 52000.0, 41000.0, 48000.0],
})

# Info struttura
print(df.dtypes)     # tipi delle colonne
print(df.shape)      # (4, 4)
print(df.info())     # riepilogo completo
print(df.describe()) # statistiche numeriche

# Selezione colonne
nomi = df["nome"]              # Series
due_col = df[["nome", "eta"]]  # DataFrame

# Selezione righe — loc (label-based) / iloc (position-based)
prima_riga = df.iloc[0]        # prima riga come Series
roma = df.loc[df["citta"] == "Roma"]   # filtro

# Filtri composti
filtro = (df["eta"] > 28) & (df["stipendio"] > 40000)
senior_ben_pagati = df[filtro]

# Aggiunta colonne
df["stipendio_netto"] = df["stipendio"] * 0.78
df["fascia"] = pd.cut(df["eta"], bins=[0, 30, 40, 100], labels=["junior", "mid", "senior"])
```

---

## B2. Groupby e aggregazioni

```python
import pandas as pd

# Groupby — split-apply-combine
df = pd.read_csv("vendite.csv")  # esempio

# Aggregazione semplice
per_citta = df.groupby("citta")["stipendio"].agg(["mean", "median", "count", "std"])

# Aggregazioni multiple per colonna
agg = df.groupby("citta").agg(
    n_impiegati=("nome", "count"),
    stipendio_medio=("stipendio", "mean"),
    eta_media=("eta", "mean"),
    stipendio_max=("stipendio", "max"),
)

# Transform — aggiunge colonna mantenendo l'indice originale
df["media_citta"] = df.groupby("citta")["stipendio"].transform("mean")
df["deviazione"] = df["stipendio"] - df["media_citta"]

# Apply — funzione arbitraria su gruppi
def riassunto_gruppo(gruppo: pd.DataFrame) -> pd.Series:
    return pd.Series({
        "n": len(gruppo),
        "top_earner": gruppo.nlargest(1, "stipendio")["nome"].iloc[0],
        "range_stipendi": gruppo["stipendio"].max() - gruppo["stipendio"].min(),
    })

riassunto = df.groupby("citta").apply(riassunto_gruppo)

# Pivot table
pivot = df.pivot_table(
    values="stipendio",
    index="citta",
    columns="fascia",
    aggfunc="mean",
    fill_value=0,
)
```

---

## B3. Merge e concatenazione

```python
import pandas as pd

ordini = pd.DataFrame({"ordine_id": [1, 2, 3], "cliente_id": [101, 102, 101], "totale": [50, 80, 30]})
clienti = pd.DataFrame({"cliente_id": [101, 102, 103], "nome": ["Alice", "Bob", "Carlo"]})
prodotti = pd.DataFrame({"ordine_id": [1, 1, 2, 3], "prodotto": ["A", "B", "A", "C"]})

# Merge — equivalente JOIN SQL
join_inner = pd.merge(ordini, clienti, on="cliente_id")           # INNER
join_left = pd.merge(ordini, clienti, on="cliente_id", how="left") # LEFT
join_outer = pd.merge(ordini, clienti, on="cliente_id", how="outer") # OUTER

# Join su colonne diverse
join_diverse = pd.merge(
    ordini.rename(columns={"ordine_id": "id"}),
    prodotti,
    left_on="id",
    right_on="ordine_id",
)

# Concatenazione verticale
df1 = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
df2 = pd.DataFrame({"a": [5, 6], "b": [7, 8]})
concatenato = pd.concat([df1, df2], ignore_index=True)

# Concatenazione orizzontale
df_orizzontale = pd.concat([df1, df2], axis=1)
```

---

## B4. Missing data e ottimizzazione dtype

```python
import pandas as pd
import numpy as np

df = pd.DataFrame({
    "a": [1, np.nan, 3, np.nan, 5],
    "b": ["X", None, "Y", None, "Z"],
    "c": [1.5, 2.5, np.nan, 4.5, 5.5],
})

# Rilevamento valori mancanti
print(df.isnull().sum())        # quanti NaN per colonna
print(df.isnull().any())        # colonne con almeno un NaN
print(df.isnull().sum() / len(df))   # percentuale

# Rimozione
df_senza_nan = df.dropna()                  # elimina righe con qualsiasi NaN
df_senza_nan_col = df.dropna(axis=1)        # elimina colonne
df_soglia = df.dropna(thresh=2)             # mantieni righe con almeno 2 valori

# Riempimento
df_zero = df.fillna(0)
df_forward = df.fillna(method="ffill")   # forward fill
df_back = df.fillna(method="bfill")      # backward fill
df["a"] = df["a"].fillna(df["a"].median())

# Ottimizzazione dtype — ridurre memoria
df_ottimizzato = df.copy()
df_ottimizzato["id"] = df_ottimizzato.get("id", range(len(df))).astype("int32")

# Category — per colonne con pochi valori unici
df["b"] = df["b"].astype("category")

# nullable integer (supporta NaN)
df["a"] = df["a"].astype("Int64")  # maiuscola = nullable

# String dtype efficiente
df["b"] = df["b"].astype("string")

# Verifica uso memoria
print(df.memory_usage(deep=True))
print(f"Totale: {df.memory_usage(deep=True).sum() / 1024:.1f} KB")
```

---

# Parte C — Polars: performance moderna

---

## C1. Polars vs Pandas: filosofia diversa

```python
import polars as pl
import pandas as pd
import time

# Polars — Lazy API (query ottimizzata)
risultato_polars = (
    pl.scan_csv("grandi_dati.csv")          # lazy: non legge subito
    .filter(pl.col("prezzo") > 100)
    .with_columns(pl.col("prezzo") * 1.22).alias("prezzo_iva")
    .group_by("categoria")
    .agg([
        pl.col("prezzo_iva").mean().alias("prezzo_medio"),
        pl.len().alias("n"),
    ])
    .sort("prezzo_medio", descending=True)
    .collect()   # <-- esegue tutto qui, ottimizzato
)

# Polars — Eager API
df = pl.DataFrame({
    "nome": ["Alice", "Bob", "Carlo"],
    "eta": [25, 32, 28],
    "stipendio": [35000, 52000, 41000],
})

# Selezione e filtro
giovani = df.filter(pl.col("eta") < 30)
nomi_stipendi = df.select(["nome", "stipendio"])

# Nuove colonne con expressions
df_con_bonus = df.with_columns([
    (pl.col("stipendio") * 1.1).alias("stipendio_con_bonus"),
    (pl.col("stipendio") / pl.col("stipendio").mean()).alias("ratio_media"),
])

# Groupby
per_fascia = (
    df.with_columns(
        pl.when(pl.col("eta") < 30).then(pl.lit("junior")).otherwise(pl.lit("senior")).alias("fascia")
    )
    .group_by("fascia")
    .agg([
        pl.col("stipendio").mean().alias("stipendio_medio"),
        pl.len().alias("n"),
    ])
)
```

---

## C2. Polars Lazy API — ottimizzazioni automatiche

```python
import polars as pl

# Polars ottimizza automaticamente:
# - Predicate pushdown: filtri applicati prima del join
# - Projection pushdown: legge solo le colonne necessarie
# - Parallelismo: esegue su tutti i core disponibili

lazy_query = (
    pl.scan_parquet("dati/*.parquet")   # legge solo file necessari
    .filter(pl.col("anno") == 2024)     # filtro pushdown al file scan
    .select(["id", "valore", "categoria"])  # projection pushdown
    .with_columns(
        pl.col("valore").log1p().alias("log_valore")
    )
    .group_by("categoria")
    .agg(pl.col("log_valore").mean())
    # Vedi il piano di query ottimizzato:
    # .explain()
)

# Visualizza piano prima di eseguire
print(lazy_query.explain())

# Esegui (con streaming per dati grandi)
risultato = lazy_query.collect(streaming=True)

# Conversione tra Pandas e Polars
df_pandas = pd.DataFrame({"a": [1, 2, 3]})
df_polars = pl.from_pandas(df_pandas)
df_pandas_back = df_polars.to_pandas()
```

---

# Parte D — Pipeline ETL completa

---

## D1. ETL con validazione e logging

```python
import logging
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class RapportoETL:
    sorgente: str
    righe_lette: int = 0
    righe_valide: int = 0
    righe_scartate: int = 0
    errori: list[str] = field(default_factory=list)
    inizio: datetime = field(default_factory=datetime.now)
    fine: datetime | None = None

    @property
    def durata_sec(self) -> float:
        if self.fine:
            return (self.fine - self.inizio).total_seconds()
        return 0.0

def estrai_csv(percorso: Path, encoding: str = "utf-8") -> tuple[pd.DataFrame, RapportoETL]:
    rapporto = RapportoETL(sorgente=str(percorso))
    try:
        df = pd.read_csv(percorso, encoding=encoding, low_memory=False)
        rapporto.righe_lette = len(df)
        logger.info(f"Letto {len(df)} righe da {percorso}")
        return df, rapporto
    except FileNotFoundError:
        rapporto.errori.append(f"File non trovato: {percorso}")
        return pd.DataFrame(), rapporto

def trasforma_vendite(df: pd.DataFrame, rapporto: RapportoETL) -> pd.DataFrame:
    """Pulizia e normalizzazione dati vendite."""
    n_inizio = len(df)

    # Rimuovi duplicati
    df = df.drop_duplicates(subset=["ordine_id"])
    n_dopo_dedup = len(df)
    if n_inizio > n_dopo_dedup:
        logger.warning(f"Rimossi {n_inizio - n_dopo_dedup} duplicati")

    # Rimuovi righe senza dati critici
    df = df.dropna(subset=["ordine_id", "importo", "data"])
    n_dopo_dropna = len(df)

    # Normalizza tipi
    df["importo"] = pd.to_numeric(df["importo"], errors="coerce")
    df = df.dropna(subset=["importo"])

    df["data"] = pd.to_datetime(df["data"], errors="coerce")
    df = df.dropna(subset=["data"])

    # Validazione range
    mask_validi = (df["importo"] > 0) & (df["importo"] < 1_000_000)
    df = df[mask_validi]

    # Feature engineering
    df["anno"] = df["data"].dt.year
    df["mese"] = df["data"].dt.month
    df["giorno_settimana"] = df["data"].dt.dayofweek
    df["importo_arrotondato"] = df["importo"].round(2)

    rapporto.righe_valide = len(df)
    rapporto.righe_scartate = n_inizio - len(df)

    return df

def carica_parquet(df: pd.DataFrame, percorso: Path, rapporto: RapportoETL) -> None:
    """Salva in Parquet — compresso e veloce da leggere."""
    percorso.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(percorso, index=False, compression="snappy")
    rapporto.fine = datetime.now()
    logger.info(
        f"Salvate {len(df)} righe in {percorso} ({percorso.stat().st_size / 1024:.1f} KB)"
        f" in {rapporto.durata_sec:.1f}s"
    )

def esegui_pipeline(sorgente: Path, destinazione: Path) -> RapportoETL:
    """Pipeline ETL completa."""
    df, rapporto = estrai_csv(sorgente)
    if df.empty:
        logger.error("Nessun dato estratto, pipeline interrotta")
        return rapporto

    df = trasforma_vendite(df, rapporto)
    carica_parquet(df, destinazione, rapporto)

    logger.info(
        f"Pipeline completata: {rapporto.righe_lette} lette, "
        f"{rapporto.righe_valide} valide, {rapporto.righe_scartate} scartate"
    )
    return rapporto
```

---

# Parte E — Riepilogo

## Quando usare cosa

| Libreria | Caso d'uso | Vantaggi |
|---|---|---|
| **NumPy** | Calcolo numerico, array matematici | Velocità C, broadcasting, algebra lineare |
| **Pandas** | Analisi esplorativa, small-medium data (<5GB) | Ecosystem maturo, ampia documentazione, SQL-like |
| **Polars** | Performance, large data, pipeline produzione | 5-100x più veloce, lazy eval, parallelismo automatico |
| **Polars Lazy** | ETL su file grandi, query complesse | Query ottimizzate, streaming per dati >RAM |

## Checklist ottimizzazione memoria Pandas

- Usa `dtype="category"` per colonne con <50 valori unici
- Usa `Int8/Int16/Int32` invece di `Int64` quando il range lo permette
- Usa `Float32` invece di `Float64` per dati non finanziari
- Leggi solo le colonne necessarie con `usecols=["a", "b"]`
- Usa `chunksize` per CSV grandi: `pd.read_csv(f, chunksize=10_000)`
- Preferisci Parquet a CSV per file persistenti (10x più veloce in lettura)

## Prossimi passi

- `tutorial_28_ml_intro.md` — scikit-learn, predizione su DataFrame
- `tutorial_25_performance.md` — profilazione e ottimizzazione codice Python
