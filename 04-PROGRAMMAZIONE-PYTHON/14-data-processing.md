---
corso: "Programmazione Python"
fase: "3 — Librerie e Framework"
modulo: "14"
titolo: "Data Processing"
versione: "pandas 2.2+ / NumPy 2.x / Polars 1.x / openpyxl 3.x / Pillow 10.x"
livello: "Intermedio"
prerequisiti:
  - "01-06 — Python Base"
  - "05 — Gestione File e I/O"
  - "03 — Funzioni e Scope"
obiettivi:
  - "Padroneggiare pandas per manipolazione, aggregazione e merge di dati tabulari"
  - "Utilizzare NumPy per operazioni numeriche vettorizzate"
  - "Costruire pipeline ETL modulari e testabili"
  - "Validare dati con Pydantic e pandera"
  - "Elaborare file Excel, PDF e immagini con librerie specializzate"
  - "Valutare e adottare Polars per dataset ad alte prestazioni"
tag: [pandas, numpy, data-processing, ETL, polars, openpyxl, pillow, pydantic, pandera]
---

# Data Processing — Guida Completa

> **Modulo 14** · **Aggiornamento:** 2026-05-24

> ### Obiettivi di apprendimento
>
> **Prerequisiti:** [Python Base](01-introduzione.md), [Gestione File e I/O](05-gestione-file-io.md), [Funzioni e Scope](03-funzioni-scope.md)
>
> Al termine di questo modulo saprai:
> 1. Padroneggiare pandas per manipolazione, aggregazione e merge di dati tabulari
> 2. Utilizzare NumPy per operazioni numeriche vettorizzate ad alte prestazioni
> 3. Costruire pipeline ETL modulari, testabili e monitorate
> 4. Validare dati in ingresso con Pydantic e pandera
> 5. Elaborare file Excel, PDF e immagini con openpyxl, pdfplumber e Pillow
> 6. Valutare e adottare Polars come alternativa ad alte prestazioni per dataset grandi
>
> **Tempo stimato:** 8-10 ore · **Livello:** Intermedio

## Idee guida
1. **Polars > Pandas per perf su large data.** Rust-core, lazy.
2. **Pandas 2.x: PyArrow backend, faster.**
3. **DuckDB per SQL analytics in-process.**
4. **`numpy` per numerical; `numba` JIT per hotspot.**


Python si e affermato come il linguaggio di riferimento per l'elaborazione dei dati grazie a un ecosistema di librerie mature, performanti e ben documentate. Dalla semplice lettura di un file CSV alla costruzione di pipeline ETL complesse, Python offre strumenti per ogni fase del ciclo di vita dei dati. Questa guida esplora in profondita le librerie fondamentali — pandas, NumPy, openpyxl, Pillow — e le tecniche essenziali per costruire pipeline di elaborazione robuste, efficienti e manutenibili.

---

## Indice

1. [Panoramica](#panoramica)
2. [pandas](#pandas)
   - [Fondamenti](#fondamenti)
   - [Manipolazione Dati](#manipolazione-dati)
   - [Dati Mancanti](#dati-mancanti)
   - [Aggregazione](#aggregazione)
   - [Merge e Join](#merge-e-join)
   - [Export](#export)
3. [NumPy](#numpy)
   - [Fondamenti NumPy](#fondamenti-numpy)
   - [Operazioni](#operazioni)
4. [Elaborazione File](#elaborazione-file)
   - [Excel avanzato (openpyxl)](#excel-avanzato-openpyxl)
   - [PDF (PyPDF2/pdfplumber)](#pdf-pypdf2pdfplumber)
   - [Immagini (Pillow)](#immagini-pillow)
5. [Data Validation](#data-validation)
6. [Pipeline di Dati](#pipeline-di-dati)
   - [Design Pattern](#design-pattern)
   - [Esempio Completo](#esempio-completo)
7. [Performance](#performance)
8. [Best Practices](#best-practices)

---

## Panoramica

Il termine **data processing** indica l'insieme delle operazioni attraverso le quali dati grezzi vengono trasformati in informazioni utili, strutturate e pronte per l'analisi o l'archiviazione. In un contesto professionale, raramente i dati arrivano nel formato desiderato: contengono valori mancanti, formati incoerenti, duplicati e strutture inadeguate. Il ruolo dello sviluppatore Python e quello di costruire pipeline che automatizzino la pulizia, la trasformazione e il caricamento di questi dati.

### Il Concetto di Data Processing Pipeline

Una pipeline di elaborazione dati e una sequenza ordinata di trasformazioni che i dati attraversano dalla sorgente alla destinazione. Ogni fase della pipeline riceve un input, lo elabora e produce un output che diventa l'input della fase successiva. Questo approccio modulare consente di testare, debuggare e sostituire singole fasi senza alterare il resto del flusso.

```
Sorgente → Estrazione → Validazione → Trasformazione → Aggregazione → Caricamento → Destinazione
```

### ETL (Extract, Transform, Load)

Il paradigma **ETL** e il modello architetturale piu diffuso per le pipeline di dati:

- **Extract (Estrazione)**: acquisizione dei dati dalle sorgenti originali — file CSV, database, API REST, fogli Excel, pagine web. Questa fase si occupa anche della gestione degli errori di connessione e della lettura incrementale.
- **Transform (Trasformazione)**: pulizia, normalizzazione, arricchimento e ristrutturazione dei dati. Include la gestione dei valori mancanti, la conversione dei tipi, il calcolo di campi derivati e l'applicazione di regole di business.
- **Load (Caricamento)**: scrittura dei dati trasformati nella destinazione finale — un database, un data warehouse, un file Parquet, un report Excel.

```python
# Schema concettuale di una pipeline ETL
def extract(source_path: str) -> pd.DataFrame:
    """Estrae i dati dalla sorgente."""
    return pd.read_csv(source_path)

def transform(df: pd.DataFrame) -> pd.DataFrame:
    """Applica le trasformazioni necessarie."""
    df = df.dropna(subset=["id"])
    df["nome"] = df["nome"].str.strip().str.title()
    df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y")
    return df

def load(df: pd.DataFrame, dest_path: str) -> None:
    """Carica i dati nella destinazione."""
    df.to_parquet(dest_path, index=False)

# Esecuzione della pipeline
dati = extract("vendite_raw.csv")
dati = transform(dati)
load(dati, "vendite_clean.parquet")
```

---

## pandas

pandas e la libreria di riferimento per la manipolazione e l'analisi di dati tabulari in Python. Costruita su NumPy, offre strutture dati ad alte prestazioni — `Series` e `DataFrame` — e un'ampia gamma di funzioni per leggere, trasformare, aggregare e scrivere dati in molteplici formati.

### Fondamenti

#### Series e DataFrame

Le due strutture dati principali di pandas sono `Series` (vettore monodimensionale etichettato) e `DataFrame` (tabella bidimensionale con righe e colonne etichettate).

```python
import pandas as pd
import numpy as np

# --- Series ---
# Creazione da lista
serie = pd.Series([10, 20, 30, 40], name="valori")
print(serie)
# 0    10
# 1    20
# 2    30
# 3    40
# Name: valori, dtype: int64

# Creazione con indice personalizzato
temperature = pd.Series(
    [22.5, 18.3, 25.1, 20.0],
    index=["Milano", "Torino", "Roma", "Napoli"],
    name="temperatura_media"
)
print(temperature["Roma"])  # 25.1

# --- DataFrame ---
# Creazione da dizionario
df = pd.DataFrame({
    "nome": ["Alice", "Bob", "Carlo", "Diana"],
    "eta": [30, 25, 35, 28],
    "citta": ["Milano", "Roma", "Napoli", "Torino"],
    "stipendio": [45000, 38000, 52000, 41000]
})
print(df)
#     nome  eta   citta  stipendio
# 0  Alice   30  Milano      45000
# 1    Bob   25    Roma      38000
# 2  Carlo   35  Napoli      52000
# 3  Diana   28  Torino      41000
```

#### Lettura dei Dati

pandas supporta la lettura da numerosi formati. Ogni funzione `read_*` accetta parametri specifici per controllare il parsing.

```python
# CSV — il formato piu comune
df_csv = pd.read_csv("dati.csv", sep=";", encoding="utf-8", parse_dates=["data"])

# Parametri utili di read_csv
df_csv = pd.read_csv(
    "dati.csv",
    sep=",",                    # separatore di campo
    header=0,                   # riga dell'intestazione (None se assente)
    names=["col1", "col2"],     # nomi colonne personalizzati
    usecols=["col1", "col2"],   # legge solo colonne specifiche
    dtype={"col1": str},        # forza il tipo di una colonna
    na_values=["N/A", "n.d."],  # valori da interpretare come NaN
    nrows=1000,                 # legge solo le prime N righe
    skiprows=5,                 # salta le prime N righe
    encoding="latin-1"          # encoding del file
)

# Excel
df_excel = pd.read_excel("report.xlsx", sheet_name="Vendite", engine="openpyxl")

# JSON
df_json = pd.read_json("api_response.json", orient="records")

# SQL (richiede una connessione al database)
import sqlite3
conn = sqlite3.connect("database.db")
df_sql = pd.read_sql("SELECT * FROM clienti WHERE attivo = 1", conn)
conn.close()

# Parquet (formato colonnare ad alte prestazioni)
df_parquet = pd.read_parquet("dati.parquet", columns=["id", "nome", "valore"])
```

#### Esplorazione dei Dati

Dopo aver caricato i dati, il primo passo e sempre l'esplorazione per comprenderne struttura, tipi e qualita.

```python
# Prime e ultime righe
print(df.head(10))       # prime 10 righe
print(df.tail(5))        # ultime 5 righe

# Informazioni sulla struttura
print(df.shape)          # (num_righe, num_colonne)
print(df.dtypes)         # tipo di ciascuna colonna
print(df.columns.tolist())  # lista dei nomi delle colonne
df.info()                # riepilogo completo: tipo, conteggio non-null, memoria

# Statistiche descrittive
print(df.describe())                    # statistiche per colonne numeriche
print(df.describe(include="object"))    # statistiche per colonne testuali
print(df["citta"].value_counts())       # frequenze per valore

# Valori unici
print(df["citta"].nunique())     # numero di valori unici
print(df["citta"].unique())      # array dei valori unici
```

#### Selezione dei Dati

pandas offre diversi meccanismi di selezione, ciascuno con caratteristiche specifiche.

```python
# Selezione per etichetta con loc
df.loc[0]                          # riga con indice 0 (restituisce Series)
df.loc[0:2]                        # righe con indice da 0 a 2 incluso
df.loc[0:2, ["nome", "eta"]]       # righe 0-2, solo colonne nome e eta

# Selezione per posizione con iloc
df.iloc[0]                         # prima riga
df.iloc[0:3]                       # prime 3 righe (0, 1, 2)
df.iloc[0:3, 0:2]                  # prime 3 righe, prime 2 colonne

# Boolean indexing (filtri condizionali)
adulti = df[df["eta"] >= 30]
milanesi_ricchi = df[(df["citta"] == "Milano") & (df["stipendio"] > 40000)]

# query() — sintassi piu leggibile per filtri complessi
risultato = df.query("eta >= 30 and citta == 'Milano'")
risultato = df.query("citta in ['Milano', 'Roma'] and stipendio > 40000")

# Selezione singola colonna
nomi = df["nome"]               # restituisce Series
nomi = df.nome                  # equivalente (ma sconsigliato per nomi con spazi)

# Selezione di piu colonne
subset = df[["nome", "citta"]]  # restituisce DataFrame
```

---

### Manipolazione Dati

#### Aggiunta e Rimozione di Colonne

```python
# Aggiungere una colonna calcolata
df["stipendio_mensile"] = df["stipendio"] / 12
df["bonus"] = df["stipendio"] * 0.10

# Aggiungere una colonna con valore condizionale
df["fascia_eta"] = np.where(df["eta"] >= 30, "senior", "junior")

# Aggiungere con assign() — restituisce una copia, non modifica l'originale
df_nuovo = df.assign(
    tasse=df["stipendio"] * 0.23,
    netto=lambda x: x["stipendio"] - x["stipendio"] * 0.23
)

# Rimuovere colonne
df = df.drop(columns=["bonus"])
df = df.drop(columns=["stipendio_mensile", "fascia_eta"])
```

#### Rinominare Colonne

```python
# Rinominare colonne specifiche
df = df.rename(columns={"nome": "nome_completo", "eta": "anni"})

# Rinominare tutte le colonne con una funzione
df.columns = df.columns.str.lower().str.replace(" ", "_")

# Applicare una trasformazione ai nomi
df = df.rename(columns=str.upper)
```

#### Ordinamento

```python
# Ordinare per una colonna
df_ordinato = df.sort_values("stipendio", ascending=False)

# Ordinare per piu colonne
df_ordinato = df.sort_values(["citta", "stipendio"], ascending=[True, False])

# Ordinare per indice
df_ordinato = df.sort_index(ascending=True)

# Ripristinare l'indice dopo l'ordinamento
df_ordinato = df_ordinato.reset_index(drop=True)
```

#### Filtraggio

```python
# Filtro con isin()
citta_target = ["Milano", "Roma", "Napoli"]
df_filtrato = df[df["citta"].isin(citta_target)]

# Filtro con between()
df_filtrato = df[df["stipendio"].between(35000, 50000)]

# Filtro con str.contains()
df_filtrato = df[df["nome"].str.contains("ar", case=False, na=False)]

# Negazione del filtro con ~
df_non_milano = df[~(df["citta"] == "Milano")]
```

#### apply(), map() e applymap()

Queste funzioni permettono di applicare trasformazioni personalizzate ai dati.

```python
# apply() su una colonna — opera su ciascun valore
def classifica_stipendio(valore):
    if valore < 35000:
        return "basso"
    elif valore < 45000:
        return "medio"
    return "alto"

df["classe_stipendio"] = df["stipendio"].apply(classifica_stipendio)

# apply() su un DataFrame — opera su righe o colonne
# axis=1 applica la funzione a ciascuna riga
df["descrizione"] = df.apply(
    lambda riga: f"{riga['nome']} ({riga['eta']} anni) - {riga['citta']}",
    axis=1
)

# map() su una Series — mappatura di valori
mappa_citta = {"Milano": "Nord", "Roma": "Centro", "Napoli": "Sud", "Torino": "Nord"}
df["area"] = df["citta"].map(mappa_citta)

# map() restituisce NaN per valori non trovati nella mappa
# replace() e un'alternativa che mantiene il valore originale
df["area"] = df["citta"].replace(mappa_citta)
```

#### String Methods (accessor .str)

L'accessor `.str` espone metodi per la manipolazione di stringhe su intere colonne.

```python
# Trasformazioni di base
df["nome_upper"] = df["nome"].str.upper()
df["nome_lower"] = df["nome"].str.lower()
df["nome_title"] = df["nome"].str.title()
df["nome_strip"] = df["nome"].str.strip()

# Estrazione e sostituzione
df["iniziale"] = df["nome"].str[0]
df["nome_pulito"] = df["nome"].str.replace(r"[^\w\s]", "", regex=True)

# Split e join
df[["cognome", "nome_proprio"]] = df["nome_completo"].str.split(", ", expand=True)
df["nome_unito"] = df[["nome", "cognome"]].apply(lambda x: " ".join(x), axis=1)

# Padding e lunghezza
df["codice_pad"] = df["codice"].str.zfill(6)     # pad con zeri a sinistra
df["lunghezza_nome"] = df["nome"].str.len()

# Verifica contenuto
mask_email = df["email"].str.contains("@gmail", na=False)
mask_inizio = df["codice"].str.startswith("IT")
mask_fine = df["file"].str.endswith(".csv")
```

#### DateTime Methods (accessor .dt)

L'accessor `.dt` fornisce metodi per lavorare con colonne di tipo datetime.

```python
# Conversione a datetime
df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y")
df["timestamp"] = pd.to_datetime(df["timestamp"], format="%Y-%m-%d %H:%M:%S")

# Estrazione di componenti
df["anno"] = df["data"].dt.year
df["mese"] = df["data"].dt.month
df["giorno"] = df["data"].dt.day
df["giorno_settimana"] = df["data"].dt.day_name()    # es. "Monday"
df["trimestre"] = df["data"].dt.quarter
df["settimana_anno"] = df["data"].dt.isocalendar().week

# Operazioni con date
df["giorni_da_oggi"] = (pd.Timestamp.now() - df["data"]).dt.days
df["mese_successivo"] = df["data"] + pd.DateOffset(months=1)

# Filtro per intervallo temporale
df_2024 = df[df["data"].dt.year == 2024]
df_q1 = df[df["data"].between("2024-01-01", "2024-03-31")]

# Resampling (per serie temporali con indice datetime)
df.set_index("data", inplace=True)
df_mensile = df.resample("ME").sum()        # aggregazione mensile
df_settimanale = df.resample("W").mean()    # media settimanale
```

---

### Dati Mancanti

La gestione dei valori mancanti e una delle attivita piu importanti nel data processing. pandas rappresenta i valori mancanti come `NaN` (Not a Number) per i dati numerici e `NaT` (Not a Time) per le date.

```python
# Rilevamento dei valori mancanti
print(df.isna().sum())         # conteggio NaN per colonna
print(df.notna().sum())        # conteggio valori validi per colonna
print(df.isna().mean() * 100)  # percentuale di NaN per colonna

# Verifica se esistono valori mancanti
print(df.isna().any().any())   # True se esiste almeno un NaN nel DataFrame

# Visualizzazione delle righe con valori mancanti
righe_con_nan = df[df.isna().any(axis=1)]
print(righe_con_nan)
```

#### fillna() — Riempimento dei Valori Mancanti

```python
# Riempimento con un valore costante
df["citta"] = df["citta"].fillna("Sconosciuta")
df["stipendio"] = df["stipendio"].fillna(0)

# Riempimento con la media o la mediana
df["eta"] = df["eta"].fillna(df["eta"].mean())
df["stipendio"] = df["stipendio"].fillna(df["stipendio"].median())

# Riempimento con il valore piu frequente (moda)
df["citta"] = df["citta"].fillna(df["citta"].mode()[0])

# Forward fill e backward fill
df["valore"] = df["valore"].ffill()   # propaga l'ultimo valore valido in avanti
df["valore"] = df["valore"].bfill()   # propaga il prossimo valore valido all'indietro
```

#### dropna() — Rimozione delle Righe o Colonne con NaN

```python
# Rimuovere righe con almeno un NaN
df_pulito = df.dropna()

# Rimuovere righe dove tutte le colonne sono NaN
df_pulito = df.dropna(how="all")

# Rimuovere righe con NaN solo in colonne specifiche
df_pulito = df.dropna(subset=["nome", "email"])

# Rimuovere colonne con troppi NaN (soglia: almeno 50% di valori validi)
soglia = len(df) * 0.50
df_pulito = df.dropna(axis=1, thresh=int(soglia))
```

#### Strategie di Interpolazione

```python
# Interpolazione lineare (utile per serie temporali)
df["temperatura"] = df["temperatura"].interpolate(method="linear")

# Interpolazione temporale (richiede indice datetime)
df["valore"] = df["valore"].interpolate(method="time")

# Interpolazione polinomiale
df["misura"] = df["misura"].interpolate(method="polynomial", order=2)

# Limitare il numero di NaN consecutivi da interpolare
df["sensore"] = df["sensore"].interpolate(method="linear", limit=3)
```

---

### Aggregazione

#### groupby()

L'operazione `groupby()` divide il DataFrame in gruppi basati sui valori di una o piu colonne, applica una funzione di aggregazione a ciascun gruppo e combina i risultati.

```python
# Aggregazione di base
vendite_per_citta = df.groupby("citta")["stipendio"].mean()
print(vendite_per_citta)

# Raggruppamento per piu colonne
df.groupby(["citta", "reparto"])["stipendio"].sum()

# Aggregazioni multiple su una colonna
df.groupby("citta")["stipendio"].agg(["mean", "median", "std", "count"])

# Iterazione sui gruppi
for nome_gruppo, gruppo_df in df.groupby("citta"):
    print(f"\n--- {nome_gruppo} ---")
    print(gruppo_df)
```

#### agg() con Funzioni Multiple

```python
# Funzioni diverse per colonne diverse
risultato = df.groupby("citta").agg(
    stipendio_medio=("stipendio", "mean"),
    stipendio_max=("stipendio", "max"),
    eta_media=("eta", "mean"),
    conteggio=("nome", "count")
)

# Funzioni personalizzate
def intervallo(serie):
    return serie.max() - serie.min()

risultato = df.groupby("citta").agg(
    range_stipendio=("stipendio", intervallo),
    stipendio_medio=("stipendio", "mean")
)

# Aggregazione con lambda
risultato = df.groupby("citta").agg(
    sopra_media=("stipendio", lambda x: (x > x.mean()).sum())
)
```

#### Pivot Tables

Le pivot table sono una forma avanzata di aggregazione che riorganizza i dati in formato tabellare bidimensionale.

```python
# Creazione di dati di esempio
vendite = pd.DataFrame({
    "data": pd.date_range("2024-01-01", periods=12, freq="ME"),
    "prodotto": ["A", "B", "C"] * 4,
    "regione": ["Nord", "Sud"] * 6,
    "quantita": [100, 150, 200, 120, 180, 90, 130, 160, 210, 110, 170, 140],
    "ricavo": [1000, 2250, 3000, 1440, 2700, 1350, 1560, 2400, 3150, 1320, 2550, 2100]
})

# Pivot table di base
pivot = pd.pivot_table(
    vendite,
    values="ricavo",
    index="prodotto",
    columns="regione",
    aggfunc="sum"
)

# Pivot table con aggregazioni multiple e totali marginali
pivot = pd.pivot_table(
    vendite,
    values=["quantita", "ricavo"],
    index="prodotto",
    columns="regione",
    aggfunc={"quantita": "sum", "ricavo": ["sum", "mean"]},
    margins=True,           # aggiunge riga e colonna "All" con i totali
    margins_name="Totale"
)

# Crosstab — tabella di frequenza incrociata
ct = pd.crosstab(vendite["prodotto"], vendite["regione"], margins=True)
print(ct)
```

---

### Merge e Join

L'unione di DataFrame provenienti da sorgenti diverse e un'operazione fondamentale nel data processing.

#### merge()

```python
clienti = pd.DataFrame({
    "id_cliente": [1, 2, 3, 4],
    "nome": ["Alice", "Bob", "Carlo", "Diana"],
    "citta": ["Milano", "Roma", "Napoli", "Torino"]
})

ordini = pd.DataFrame({
    "id_ordine": [101, 102, 103, 104, 105],
    "id_cliente": [1, 2, 2, 5, 3],
    "importo": [250.0, 180.0, 320.0, 150.0, 420.0]
})

# Inner join — solo le righe con corrispondenza in entrambi i DataFrame
inner = pd.merge(clienti, ordini, on="id_cliente", how="inner")

# Left join — tutte le righe del DataFrame sinistro
left = pd.merge(clienti, ordini, on="id_cliente", how="left")

# Right join — tutte le righe del DataFrame destro
right = pd.merge(clienti, ordini, on="id_cliente", how="right")

# Outer join — tutte le righe di entrambi i DataFrame
outer = pd.merge(clienti, ordini, on="id_cliente", how="outer")

# Merge con colonne di nome diverso
risultato = pd.merge(
    clienti, ordini,
    left_on="id_cliente",
    right_on="id_cliente",
    how="inner",
    suffixes=("_cliente", "_ordine")  # suffissi per colonne duplicate
)

# Merge su piu colonne
risultato = pd.merge(df1, df2, on=["anno", "mese", "codice"], how="inner")
```

#### concat()

```python
# Concatenazione verticale (impilare DataFrames)
df_q1 = pd.DataFrame({"mese": ["Gen", "Feb", "Mar"], "vendite": [100, 120, 110]})
df_q2 = pd.DataFrame({"mese": ["Apr", "Mag", "Giu"], "vendite": [130, 150, 140]})
df_anno = pd.concat([df_q1, df_q2], ignore_index=True)

# Concatenazione orizzontale (aggiungere colonne)
info = pd.DataFrame({"target": [100, 120, 110, 130, 150, 140]})
df_completo = pd.concat([df_anno, info], axis=1)

# Concatenazione con chiavi per identificare la sorgente
df_totale = pd.concat(
    [df_q1, df_q2],
    keys=["Q1", "Q2"],
    names=["trimestre", "indice"]
)
```

#### join()

```python
# join() usa l'indice per l'unione — utile per DataFrames con indice significativo
df1 = pd.DataFrame({"A": [1, 2, 3]}, index=["x", "y", "z"])
df2 = pd.DataFrame({"B": [4, 5, 6]}, index=["x", "y", "w"])

risultato = df1.join(df2, how="inner")    # solo x, y
risultato = df1.join(df2, how="outer")    # x, y, z, w
```

---

### Export

pandas supporta l'export in numerosi formati. Ogni metodo `to_*` offre parametri per controllare la formattazione dell'output.

```python
# CSV
df.to_csv("output.csv", index=False, sep=";", encoding="utf-8")

# Excel — con foglio specifico
df.to_excel("report.xlsx", sheet_name="Dati", index=False, engine="openpyxl")

# Piu fogli nello stesso file Excel
with pd.ExcelWriter("report_completo.xlsx", engine="openpyxl") as writer:
    df_vendite.to_excel(writer, sheet_name="Vendite", index=False)
    df_clienti.to_excel(writer, sheet_name="Clienti", index=False)
    df_riepilogo.to_excel(writer, sheet_name="Riepilogo", index=False)

# JSON
df.to_json("dati.json", orient="records", indent=2, force_ascii=False)

# SQL
import sqlite3
conn = sqlite3.connect("database.db")
df.to_sql("tabella_vendite", conn, if_exists="replace", index=False)
conn.close()

# Parquet — formato colonnare, compresso, efficiente
df.to_parquet("dati.parquet", index=False, compression="snappy")
```

---

## NumPy

NumPy (Numerical Python) e la libreria fondamentale per il calcolo numerico in Python. Fornisce l'oggetto `ndarray`, un array multidimensionale omogeneo ad alte prestazioni, insieme a un vasto insieme di funzioni matematiche ottimizzate. pandas stesso si basa su NumPy per le operazioni interne.

### Fondamenti NumPy

#### Creazione di Array

```python
import numpy as np

# Da lista Python
arr = np.array([1, 2, 3, 4, 5])
matrice = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])

# Array speciali
zeri = np.zeros((3, 4))            # matrice 3x4 di zeri
uni = np.ones((2, 3))              # matrice 2x3 di uni
vuoto = np.empty((2, 2))           # matrice 2x2 non inizializzata
identita = np.eye(4)               # matrice identita 4x4
pieno = np.full((3, 3), 7.5)       # matrice 3x3 riempita con 7.5

# Sequenze
seq = np.arange(0, 10, 2)          # [0, 2, 4, 6, 8]
lin = np.linspace(0, 1, 5)         # [0.0, 0.25, 0.5, 0.75, 1.0]
log_space = np.logspace(0, 3, 4)   # [1, 10, 100, 1000]

# Informazioni sull'array
print(arr.shape)      # (5,)
print(matrice.shape)   # (3, 3)
print(arr.dtype)       # int64
print(matrice.ndim)    # 2
print(matrice.size)    # 9
```

#### Indicizzazione e Slicing Multidimensionale

```python
matrice = np.array([[1, 2, 3, 4],
                    [5, 6, 7, 8],
                    [9, 10, 11, 12]])

# Accesso a un singolo elemento
print(matrice[1, 2])         # 7

# Slicing di righe e colonne
print(matrice[0, :])         # riga 0: [1, 2, 3, 4]
print(matrice[:, 1])         # colonna 1: [2, 6, 10]
print(matrice[0:2, 1:3])     # sotto-matrice: [[2, 3], [6, 7]]

# Indicizzazione avanzata (fancy indexing)
righe = [0, 2]
colonne = [1, 3]
print(matrice[righe, colonne])    # [2, 12]

# Boolean indexing
mask = matrice > 5
print(matrice[mask])              # [6, 7, 8, 9, 10, 11, 12]
matrice[mask] = 0                 # imposta a 0 tutti i valori > 5
```

#### Broadcasting

Il broadcasting e il meccanismo con cui NumPy gestisce operazioni tra array di forme diverse, estendendo automaticamente l'array piu piccolo.

```python
# Scalare e array
arr = np.array([1, 2, 3, 4])
risultato = arr * 10              # [10, 20, 30, 40]

# Array 1D e matrice 2D
matrice = np.array([[1, 2, 3],
                    [4, 5, 6]])
vettore = np.array([10, 20, 30])
risultato = matrice + vettore
# [[11, 22, 33],
#  [14, 25, 36]]

# Array colonna e array riga
colonna = np.array([[1], [2], [3]])
riga = np.array([10, 20, 30])
risultato = colonna + riga
# [[11, 21, 31],
#  [12, 22, 32],
#  [13, 23, 33]]
```

#### Universal Functions (ufunc)

Le ufunc sono funzioni ottimizzate che operano elemento per elemento sugli array.

```python
arr = np.array([1, 4, 9, 16, 25])

# Funzioni matematiche
print(np.sqrt(arr))          # [1, 2, 3, 4, 5]
print(np.exp(arr))           # esponenziale di ciascun elemento
print(np.log(arr))           # logaritmo naturale
print(np.log10(arr))         # logaritmo in base 10
print(np.abs(np.array([-1, -2, 3])))  # [1, 2, 3]

# Funzioni trigonometriche
angoli = np.array([0, np.pi/6, np.pi/4, np.pi/3, np.pi/2])
print(np.sin(angoli))
print(np.cos(angoli))

# Arrotondamento
valori = np.array([1.234, 2.567, 3.891])
print(np.round(valori, 1))   # [1.2, 2.6, 3.9]
print(np.floor(valori))      # [1., 2., 3.]
print(np.ceil(valori))       # [2., 3., 4.]
```

#### Aggregazioni

```python
arr = np.array([[1, 2, 3],
                [4, 5, 6],
                [7, 8, 9]])

# Aggregazioni globali
print(np.sum(arr))        # 45
print(np.mean(arr))       # 5.0
print(np.std(arr))        # 2.581...
print(np.min(arr))        # 1
print(np.max(arr))        # 9

# Aggregazioni per asse
print(np.sum(arr, axis=0))    # somma per colonna: [12, 15, 18]
print(np.sum(arr, axis=1))    # somma per riga: [6, 15, 24]
print(np.mean(arr, axis=0))   # media per colonna: [4., 5., 6.]

# Indice del minimo e massimo
print(np.argmin(arr))          # 0 (indice flat del minimo)
print(np.argmax(arr, axis=1))  # [2, 2, 2] (indice del max per ogni riga)

# Aggregazioni cumulative
print(np.cumsum(arr, axis=1))  # somma cumulativa per riga
```

#### Reshaping

```python
arr = np.arange(12)   # [0, 1, 2, ..., 11]

# Reshape
matrice = arr.reshape(3, 4)     # matrice 3x4
matrice = arr.reshape(3, -1)    # -1 calcola automaticamente la dimensione

# Appiattire
piatto = matrice.ravel()         # vista monodimensionale (condivide la memoria)
copia_piatta = matrice.flatten() # copia monodimensionale

# Trasporre
trasposta = matrice.T
trasposta = np.transpose(matrice)

# Aggiungere una dimensione
arr_1d = np.array([1, 2, 3])
riga = arr_1d[np.newaxis, :]     # shape: (1, 3)
colonna = arr_1d[:, np.newaxis]  # shape: (3, 1)

# Impilare array
a = np.array([1, 2, 3])
b = np.array([4, 5, 6])
verticale = np.vstack([a, b])     # [[1,2,3], [4,5,6]]
orizzontale = np.hstack([a, b])   # [1,2,3,4,5,6]
```

---

### Operazioni

#### Operazioni Elemento per Elemento

```python
a = np.array([1, 2, 3, 4])
b = np.array([10, 20, 30, 40])

# Aritmetica
print(a + b)     # [11, 22, 33, 44]
print(a * b)     # [10, 40, 90, 160]
print(b / a)     # [10., 10., 10., 10.]
print(a ** 2)    # [1, 4, 9, 16]

# Confronto (restituisce array booleano)
print(a > 2)     # [False, False, True, True]
print(a == b)    # [False, False, False, False]

# Operazioni logiche
x = np.array([True, True, False, False])
y = np.array([True, False, True, False])
print(np.logical_and(x, y))  # [True, False, False, False]
print(np.logical_or(x, y))   # [True, True, True, False]
```

#### Operazioni Matriciali

```python
A = np.array([[1, 2], [3, 4]])
B = np.array([[5, 6], [7, 8]])

# Prodotto matriciale
C = np.dot(A, B)           # oppure A @ B
C = np.matmul(A, B)        # equivalente

# Determinante
det = np.linalg.det(A)

# Inversa
inv_A = np.linalg.inv(A)

# Autovalori e autovettori
autovalori, autovettori = np.linalg.eig(A)

# Sistema di equazioni lineari: Ax = b
b = np.array([5, 11])
x = np.linalg.solve(A, b)

# Norma
norma = np.linalg.norm(A)             # norma di Frobenius
norma_vettore = np.linalg.norm(b)     # norma euclidea
```

#### Generazione di Numeri Random

```python
rng = np.random.default_rng(seed=42)   # generatore con seed per riproducibilita

# Distribuzioni comuni
uniformi = rng.uniform(0, 1, size=10)            # distribuzione uniforme [0, 1)
normali = rng.normal(loc=0, scale=1, size=1000)   # distribuzione normale
interi = rng.integers(0, 100, size=20)             # interi casuali [0, 100)

# Permutazioni
arr = np.arange(10)
rng.shuffle(arr)                    # mescola in-place
permutato = rng.permutation(arr)    # restituisce copia mescolata

# Campionamento
scelta = rng.choice(arr, size=5, replace=False)  # 5 elementi senza ripetizione

# Matrice random
matrice_random = rng.standard_normal((3, 4))  # matrice 3x4 da distribuzione normale
```

---

## Elaborazione File

Oltre ai formati tabulari standard, Python offre librerie specializzate per lavorare con file Excel avanzati, documenti PDF e immagini.

### Excel avanzato (openpyxl)

La libreria `openpyxl` consente di leggere e scrivere file Excel `.xlsx` con pieno controllo su formattazione, grafici e formule.

```python
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.chart import BarChart, Reference

# --- Creazione di un file Excel con formattazione ---
wb = Workbook()
ws = wb.active
ws.title = "Report Vendite"

# Intestazioni con stile
intestazioni = ["Prodotto", "Q1", "Q2", "Q3", "Q4", "Totale"]
ws.append(intestazioni)

# Stile per l'intestazione
font_intestazione = Font(name="Calibri", size=12, bold=True, color="FFFFFF")
sfondo_intestazione = PatternFill(start_color="2F5496", end_color="2F5496", fill_type="solid")
allineamento_centro = Alignment(horizontal="center", vertical="center")

for cella in ws[1]:
    cella.font = font_intestazione
    cella.fill = sfondo_intestazione
    cella.alignment = allineamento_centro

# Dati con formule
dati = [
    ["Widget A", 1500, 1800, 2100, 1900],
    ["Widget B", 2200, 2500, 2300, 2800],
    ["Widget C", 800, 950, 1100, 1050],
]

for riga in dati:
    numero_riga = ws.max_row + 1
    ws.append(riga + [None])
    # Formula per il totale
    ws.cell(row=numero_riga, column=6).value = (
        f"=SUM(B{numero_riga}:E{numero_riga})"
    )

# --- Creazione di un grafico ---
grafico = BarChart()
grafico.type = "col"
grafico.title = "Vendite Trimestrali"
grafico.x_axis.title = "Prodotto"
grafico.y_axis.title = "Quantita"

dati_grafico = Reference(ws, min_col=2, max_col=5, min_row=1, max_row=4)
categorie = Reference(ws, min_col=1, min_row=2, max_row=4)
grafico.add_data(dati_grafico, titles_from_data=True)
grafico.set_categories(categorie)
ws.add_chart(grafico, "H2")

# --- Aggiunta di un secondo foglio ---
ws2 = wb.create_sheet("Dettaglio")
ws2.append(["ID", "Descrizione", "Prezzo"])
ws2.append([1, "Componente A", 25.50])
ws2.append([2, "Componente B", 18.90])

# Larghezza colonne automatica
for colonna in ws.columns:
    max_lunghezza = max(len(str(cella.value or "")) for cella in colonna)
    lettera = colonna[0].column_letter
    ws.column_dimensions[lettera].width = max_lunghezza + 4

wb.save("report_formattato.xlsx")
```

#### Lettura avanzata con openpyxl

```python
from openpyxl import load_workbook

wb = load_workbook("report_formattato.xlsx", data_only=True)
ws = wb["Report Vendite"]

# Iterare sulle righe
for riga in ws.iter_rows(min_row=2, values_only=True):
    prodotto, q1, q2, q3, q4, totale = riga
    print(f"{prodotto}: totale = {totale}")

# Accesso a celle specifiche
valore = ws["B2"].value
print(f"Q1 di Widget A: {valore}")

# Elenco dei fogli
print(wb.sheetnames)   # ['Report Vendite', 'Dettaglio']
```

---

### PDF (PyPDF2/pdfplumber)

L'elaborazione di file PDF e un'esigenza comune nel data processing aziendale — estrazione di testo, manipolazione di pagine e recupero di tabelle.

```python
# --- Estrazione di testo con pdfplumber ---
import pdfplumber

with pdfplumber.open("documento.pdf") as pdf:
    # Informazioni sul documento
    print(f"Numero di pagine: {len(pdf.pages)}")

    # Estrazione del testo da tutte le pagine
    testo_completo = ""
    for pagina in pdf.pages:
        testo = pagina.extract_text()
        if testo:
            testo_completo += testo + "\n"

    print(testo_completo)

    # Estrazione di tabelle
    prima_pagina = pdf.pages[0]
    tabelle = prima_pagina.extract_tables()
    for tabella in tabelle:
        df = pd.DataFrame(tabella[1:], columns=tabella[0])
        print(df)
```

```python
# --- Manipolazione di pagine con PyPDF2 ---
from PyPDF2 import PdfReader, PdfWriter

# Estrazione del testo
reader = PdfReader("input.pdf")
for pagina in reader.pages:
    print(pagina.extract_text())

# Unione di piu PDF
writer = PdfWriter()
for file_pdf in ["parte1.pdf", "parte2.pdf", "parte3.pdf"]:
    reader = PdfReader(file_pdf)
    for pagina in reader.pages:
        writer.add_page(pagina)
writer.write("documento_unito.pdf")

# Estrazione di pagine specifiche
reader = PdfReader("documento_lungo.pdf")
writer = PdfWriter()
for i in [0, 2, 4]:  # pagine 1, 3, 5 (indice zero-based)
    writer.add_page(reader.pages[i])
writer.write("pagine_selezionate.pdf")

# Rotazione di pagine
reader = PdfReader("input.pdf")
writer = PdfWriter()
for pagina in reader.pages:
    pagina.rotate(90)  # rotazione di 90 gradi in senso orario
    writer.add_page(pagina)
writer.write("ruotato.pdf")
```

---

### Immagini (Pillow)

Pillow (fork di PIL) e la libreria standard per l'elaborazione di immagini in Python.

```python
from PIL import Image, ImageFilter, ImageEnhance

# --- Operazioni di base ---
img = Image.open("foto.jpg")
print(f"Dimensioni: {img.size}")      # (larghezza, altezza)
print(f"Formato: {img.format}")        # JPEG
print(f"Modalita: {img.mode}")         # RGB

# Ridimensionamento
img_piccola = img.resize((800, 600))
img_thumbnail = img.copy()
img_thumbnail.thumbnail((200, 200))    # mantiene le proporzioni

# Ritaglio (left, upper, right, lower)
ritaglio = img.crop((100, 50, 500, 400))

# Rotazione
ruotata = img.rotate(45, expand=True, fillcolor="white")

# Ribaltamento
specchio_h = img.transpose(Image.FLIP_LEFT_RIGHT)
specchio_v = img.transpose(Image.FLIP_TOP_BOTTOM)

# --- Conversione di formato ---
img.save("foto.png")                    # da JPEG a PNG
img.save("foto.webp", quality=85)       # a WebP con qualita specifica
img_gray = img.convert("L")             # scala di grigi
img_gray.save("foto_grigia.jpg")

# --- Filtri ---
sfocata = img.filter(ImageFilter.GaussianBlur(radius=5))
nitida = img.filter(ImageFilter.SHARPEN)
contorni = img.filter(ImageFilter.FIND_EDGES)

# --- Miglioramenti ---
enhancer = ImageEnhance.Contrast(img)
img_contrasto = enhancer.enhance(1.5)   # 1.0 = originale, >1.0 = piu contrasto

enhancer = ImageEnhance.Brightness(img)
img_luminosa = enhancer.enhance(1.2)
```

#### Elaborazione Batch di Immagini

```python
from pathlib import Path
from PIL import Image

def elabora_batch_immagini(
    cartella_input: str,
    cartella_output: str,
    dimensione_max: tuple[int, int] = (1920, 1080),
    qualita: int = 85,
    formato_output: str = "WEBP"
) -> dict[str, int]:
    """Elabora un batch di immagini: ridimensiona, ottimizza e converte."""
    input_path = Path(cartella_input)
    output_path = Path(cartella_output)
    output_path.mkdir(parents=True, exist_ok=True)

    statistiche = {"elaborate": 0, "errori": 0, "saltate": 0}
    estensioni = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}

    for file in input_path.iterdir():
        if file.suffix.lower() not in estensioni:
            statistiche["saltate"] += 1
            continue

        try:
            with Image.open(file) as img:
                # Converti in RGB se necessario (per JPEG/WebP)
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")

                # Ridimensiona mantenendo le proporzioni
                img.thumbnail(dimensione_max, Image.LANCZOS)

                # Salva nel formato di output
                nome_output = file.stem + f".{formato_output.lower()}"
                percorso_output = output_path / nome_output
                img.save(percorso_output, formato_output, quality=qualita)

                statistiche["elaborate"] += 1
        except Exception as e:
            print(f"Errore con {file.name}: {e}")
            statistiche["errori"] += 1

    return statistiche

# Utilizzo
stats = elabora_batch_immagini("foto_originali/", "foto_ottimizzate/")
print(f"Elaborate: {stats['elaborate']}, Errori: {stats['errori']}")
```

---

## Data Validation

La validazione dei dati e una fase critica che previene errori a valle nella pipeline. Python offre diversi strumenti per garantire che i dati rispettino vincoli di tipo, formato e coerenza.

### Pydantic per Validazione Dati

Pydantic utilizza i type hints di Python per definire modelli di dati con validazione automatica.

```python
from pydantic import BaseModel, Field, field_validator, EmailStr
from datetime import date
from typing import Optional

class Cliente(BaseModel):
    id: int = Field(gt=0, description="ID univoco del cliente")
    nome: str = Field(min_length=2, max_length=100)
    email: EmailStr
    data_registrazione: date
    eta: int = Field(ge=18, le=120)
    saldo: float = Field(ge=0, default=0.0)
    note: Optional[str] = None

    @field_validator("nome")
    @classmethod
    def nome_deve_essere_capitalizzato(cls, v: str) -> str:
        return v.strip().title()

# Validazione riuscita
cliente = Cliente(
    id=1,
    nome="mario rossi",
    email="mario.rossi@example.com",
    data_registrazione="2024-01-15",
    eta=35,
    saldo=1500.50
)
print(cliente.nome)  # "Mario Rossi" (capitalizzato dal validator)

# Validazione fallita — solleva ValidationError
try:
    cliente_invalido = Cliente(
        id=-1,              # errore: deve essere > 0
        nome="A",           # errore: troppo corto
        email="non-valida", # errore: formato email
        data_registrazione="2024-01-15",
        eta=15              # errore: deve essere >= 18
    )
except Exception as e:
    print(f"Errori di validazione:\n{e}")
```

### pandera per Validazione DataFrame

pandera estende la validazione al livello del DataFrame, definendo schemi per colonne, tipi e vincoli.

```python
import pandera as pa
from pandera import Column, Check, DataFrameSchema

# Definizione dello schema
schema_vendite = DataFrameSchema({
    "id_ordine": Column(int, Check.greater_than(0), unique=True),
    "prodotto": Column(str, Check.isin(["Widget A", "Widget B", "Widget C"])),
    "quantita": Column(int, Check.in_range(1, 10000)),
    "prezzo_unitario": Column(float, Check.greater_than(0)),
    "data_ordine": Column("datetime64[ns]"),
    "regione": Column(str, Check.str_length(min_value=2, max_value=50)),
})

# Validazione del DataFrame
df_vendite = pd.DataFrame({
    "id_ordine": [1, 2, 3],
    "prodotto": ["Widget A", "Widget B", "Widget C"],
    "quantita": [10, 25, 5],
    "prezzo_unitario": [9.99, 14.50, 22.00],
    "data_ordine": pd.to_datetime(["2024-01-10", "2024-01-11", "2024-01-12"]),
    "regione": ["Nord", "Sud", "Centro"]
})

try:
    df_validato = schema_vendite.validate(df_vendite)
    print("Validazione superata")
except pa.errors.SchemaError as e:
    print(f"Errore di validazione:\n{e}")
```

### Great Expectations — Panoramica

Great Expectations e un framework enterprise per la validazione dei dati che produce documentazione automatica e report di qualita.

```python
import great_expectations as gx

# Creazione del contesto e del datasource
context = gx.get_context()

# Definizione delle aspettative
validator = context.sources.pandas_default.read_dataframe(df_vendite)
validator.expect_column_values_to_not_be_null("id_ordine")
validator.expect_column_values_to_be_unique("id_ordine")
validator.expect_column_values_to_be_between("quantita", min_value=1, max_value=10000)
validator.expect_column_values_to_be_in_set("regione", ["Nord", "Sud", "Centro", "Isole"])

# Esecuzione della validazione
risultati = validator.validate()
print(f"Successo: {risultati.success}")
print(f"Risultati: {risultati.statistics}")
```

---

## Pipeline di Dati

### Design Pattern

#### Pipeline Funzionale (Chain of Transformations)

L'approccio funzionale consiste nel concatenare funzioni pure, ciascuna delle quali riceve un DataFrame e ne restituisce uno trasformato.

```python
from typing import Callable
import pandas as pd

# Definizione delle funzioni di trasformazione
def rimuovi_duplicati(df: pd.DataFrame) -> pd.DataFrame:
    return df.drop_duplicates()

def pulisci_stringhe(df: pd.DataFrame) -> pd.DataFrame:
    colonne_testo = df.select_dtypes(include="object").columns
    for col in colonne_testo:
        df[col] = df[col].str.strip().str.lower()
    return df

def converti_date(df: pd.DataFrame) -> pd.DataFrame:
    if "data" in df.columns:
        df["data"] = pd.to_datetime(df["data"], errors="coerce")
    return df

def filtra_righe_valide(df: pd.DataFrame) -> pd.DataFrame:
    return df.dropna(subset=["id", "nome"])

# Funzione pipeline che concatena le trasformazioni
def esegui_pipeline(
    df: pd.DataFrame,
    *trasformazioni: Callable[[pd.DataFrame], pd.DataFrame]
) -> pd.DataFrame:
    for trasformazione in trasformazioni:
        df = trasformazione(df)
    return df

# Esecuzione
df_risultato = esegui_pipeline(
    df_raw,
    rimuovi_duplicati,
    pulisci_stringhe,
    converti_date,
    filtra_righe_valide
)
```

Un'alternativa elegante sfrutta il metodo `pipe()` di pandas.

```python
risultato = (
    df_raw
    .pipe(rimuovi_duplicati)
    .pipe(pulisci_stringhe)
    .pipe(converti_date)
    .pipe(filtra_righe_valide)
)
```

#### Pipeline Basata su Classi

L'approccio a classi offre maggiore struttura, configurabilita e possibilita di mantenere stato interno.

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)

class Step(ABC):
    """Classe base per un singolo passo della pipeline."""

    @property
    def nome(self) -> str:
        return self.__class__.__name__

    @abstractmethod
    def esegui(self, df: pd.DataFrame) -> pd.DataFrame:
        ...

class RimuoviDuplicati(Step):
    def esegui(self, df: pd.DataFrame) -> pd.DataFrame:
        n_prima = len(df)
        df = df.drop_duplicates()
        logger.info(f"Rimossi {n_prima - len(df)} duplicati")
        return df

class FiltraPerData(Step):
    def __init__(self, colonna: str, data_inizio: str, data_fine: str):
        self.colonna = colonna
        self.data_inizio = data_inizio
        self.data_fine = data_fine

    def esegui(self, df: pd.DataFrame) -> pd.DataFrame:
        df[self.colonna] = pd.to_datetime(df[self.colonna])
        mask = df[self.colonna].between(self.data_inizio, self.data_fine)
        n_filtrate = (~mask).sum()
        df = df[mask]
        logger.info(f"Filtrate {n_filtrate} righe fuori dall'intervallo")
        return df

class NormalizzaColonne(Step):
    def __init__(self, colonne: list[str]):
        self.colonne = colonne

    def esegui(self, df: pd.DataFrame) -> pd.DataFrame:
        for col in self.colonne:
            if col in df.columns:
                df[col] = df[col].str.strip().str.title()
        return df

@dataclass
class Pipeline:
    """Esecutore della pipeline con logging e gestione errori."""
    nome: str
    steps: list[Step] = field(default_factory=list)

    def aggiungi_step(self, step: Step) -> "Pipeline":
        self.steps.append(step)
        return self  # consente il chaining

    def esegui(self, df: pd.DataFrame) -> pd.DataFrame:
        logger.info(f"Avvio pipeline '{self.nome}' con {len(df)} righe")
        for i, step in enumerate(self.steps, 1):
            logger.info(f"Step {i}/{len(self.steps)}: {step.nome}")
            try:
                df = step.esegui(df)
                logger.info(f"  -> {len(df)} righe dopo {step.nome}")
            except Exception as e:
                logger.error(f"Errore nello step {step.nome}: {e}")
                raise
        logger.info(f"Pipeline '{self.nome}' completata: {len(df)} righe finali")
        return df

# Costruzione e esecuzione della pipeline
pipeline = Pipeline(nome="Pulizia Vendite")
pipeline.aggiungi_step(RimuoviDuplicati())
pipeline.aggiungi_step(FiltraPerData("data_ordine", "2024-01-01", "2024-12-31"))
pipeline.aggiungi_step(NormalizzaColonne(["nome_cliente", "citta"]))

df_pulito = pipeline.esegui(df_raw)
```

#### Error Handling nelle Pipeline

```python
import logging
from dataclasses import dataclass, field

@dataclass
class RisultatoPipeline:
    """Contiene il risultato della pipeline e le informazioni sugli errori."""
    successo: bool
    dataframe: pd.DataFrame | None
    errori: list[str] = field(default_factory=list)
    avvisi: list[str] = field(default_factory=list)
    statistiche: dict = field(default_factory=dict)

def pipeline_con_gestione_errori(
    df: pd.DataFrame,
    steps: list[Callable],
    continua_su_errore: bool = False
) -> RisultatoPipeline:
    """Esegue una pipeline con gestione errori robusta."""
    risultato = RisultatoPipeline(successo=True, dataframe=df)
    risultato.statistiche["righe_iniziali"] = len(df)

    for step in steps:
        nome_step = step.__name__
        try:
            n_prima = len(df)
            df = step(df)
            n_dopo = len(df)

            if n_dopo < n_prima * 0.5:
                risultato.avvisi.append(
                    f"{nome_step}: rimosso piu del 50% delle righe "
                    f"({n_prima} -> {n_dopo})"
                )

        except Exception as e:
            messaggio = f"Errore in {nome_step}: {e}"
            risultato.errori.append(messaggio)
            logging.error(messaggio)

            if not continua_su_errore:
                risultato.successo = False
                risultato.dataframe = None
                return risultato

    risultato.dataframe = df
    risultato.statistiche["righe_finali"] = len(df)
    return risultato
```

#### Logging del Progresso della Pipeline

```python
import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler("pipeline.log"),
        logging.StreamHandler()
    ]
)

def step_con_logging(nome: str):
    """Decoratore che aggiunge logging automatico a uno step della pipeline."""
    def decorator(func):
        def wrapper(df: pd.DataFrame) -> pd.DataFrame:
            logger = logging.getLogger("pipeline")
            logger.info(f"[INIZIO] {nome} — {len(df)} righe in input")
            inizio = time.perf_counter()

            risultato = func(df)

            durata = time.perf_counter() - inizio
            logger.info(
                f"[FINE]   {nome} — {len(risultato)} righe in output "
                f"({durata:.2f}s)"
            )
            return risultato
        wrapper.__name__ = nome
        return wrapper
    return decorator

# Utilizzo del decoratore
@step_con_logging("Pulizia dati")
def pulisci_dati(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop_duplicates()
    df = df.dropna(subset=["id"])
    return df

@step_con_logging("Trasformazione")
def trasforma_dati(df: pd.DataFrame) -> pd.DataFrame:
    df["nome"] = df["nome"].str.title()
    df["anno"] = df["data"].dt.year
    return df
```

---

### Esempio Completo

Questa sezione presenta una pipeline ETL completa e realistica: lettura di un file CSV, validazione, trasformazione, aggregazione e export.

```python
"""
Pipeline ETL completa: elaborazione delle vendite mensili.

Flusso:
    CSV grezzo → Validazione → Pulizia → Arricchimento → Aggregazione → Export
"""
import pandas as pd
import numpy as np
import logging
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
logger = logging.getLogger("etl_vendite")


@dataclass
class ConfigPipeline:
    """Configurazione centralizzata della pipeline."""
    input_path: str = "dati/vendite_raw.csv"
    output_dir: str = "output/"
    anno_corrente: int = 2024
    colonne_richieste: list = field(default_factory=lambda: [
        "id_ordine", "data_ordine", "prodotto", "categoria",
        "quantita", "prezzo_unitario", "id_cliente", "regione"
    ])


def extract(config: ConfigPipeline) -> pd.DataFrame:
    """Fase di estrazione: legge il CSV e verifica la struttura."""
    logger.info(f"Lettura file: {config.input_path}")
    df = pd.read_csv(
        config.input_path,
        sep=",",
        encoding="utf-8",
        parse_dates=["data_ordine"],
        dtype={"id_ordine": str, "id_cliente": str}
    )
    logger.info(f"Lette {len(df)} righe e {len(df.columns)} colonne")

    # Verifica colonne richieste
    mancanti = set(config.colonne_richieste) - set(df.columns)
    if mancanti:
        raise ValueError(f"Colonne mancanti nel file sorgente: {mancanti}")

    return df


def validate(df: pd.DataFrame) -> pd.DataFrame:
    """Fase di validazione: identifica e gestisce anomalie."""
    n_iniziali = len(df)

    # Rimozione duplicati
    df = df.drop_duplicates(subset=["id_ordine"])
    n_duplicati = n_iniziali - len(df)
    if n_duplicati > 0:
        logger.warning(f"Rimossi {n_duplicati} duplicati")

    # Verifica valori mancanti critici
    colonne_critiche = ["id_ordine", "prodotto", "quantita", "prezzo_unitario"]
    n_nan = df[colonne_critiche].isna().sum().sum()
    if n_nan > 0:
        logger.warning(f"Trovati {n_nan} valori mancanti in colonne critiche")
        df = df.dropna(subset=colonne_critiche)

    # Verifica vincoli di business
    mask_quantita_valida = df["quantita"] > 0
    mask_prezzo_valido = df["prezzo_unitario"] > 0
    mask_valida = mask_quantita_valida & mask_prezzo_valido

    n_invalide = (~mask_valida).sum()
    if n_invalide > 0:
        logger.warning(f"Rimosse {n_invalide} righe con valori non validi")
        df = df[mask_valida]

    logger.info(f"Validazione completata: {len(df)}/{n_iniziali} righe valide")
    return df


def transform(df: pd.DataFrame) -> pd.DataFrame:
    """Fase di trasformazione: pulizia, arricchimento, calcoli."""
    # Pulizia stringhe
    df["prodotto"] = df["prodotto"].str.strip().str.title()
    df["categoria"] = df["categoria"].str.strip().str.lower()
    df["regione"] = df["regione"].str.strip().str.title()

    # Calcoli derivati
    df["ricavo_totale"] = df["quantita"] * df["prezzo_unitario"]
    df["anno"] = df["data_ordine"].dt.year
    df["mese"] = df["data_ordine"].dt.month
    df["trimestre"] = df["data_ordine"].dt.quarter
    df["nome_mese"] = df["data_ordine"].dt.strftime("%B")

    # Classificazione per fascia di ricavo
    df["fascia_ricavo"] = pd.cut(
        df["ricavo_totale"],
        bins=[0, 50, 200, 1000, float("inf")],
        labels=["micro", "piccolo", "medio", "grande"]
    )

    logger.info(f"Trasformazione completata: {len(df.columns)} colonne")
    return df


def aggregate(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Fase di aggregazione: produce tabelle riassuntive."""
    risultati = {}

    # Riepilogo per regione
    risultati["per_regione"] = (
        df.groupby("regione")
        .agg(
            ordini=("id_ordine", "count"),
            ricavo_totale=("ricavo_totale", "sum"),
            ricavo_medio=("ricavo_totale", "mean"),
            clienti_unici=("id_cliente", "nunique")
        )
        .sort_values("ricavo_totale", ascending=False)
        .reset_index()
    )

    # Riepilogo per categoria e trimestre
    risultati["per_categoria_trimestre"] = pd.pivot_table(
        df,
        values="ricavo_totale",
        index="categoria",
        columns="trimestre",
        aggfunc="sum",
        margins=True,
        margins_name="Totale"
    )

    # Top 10 prodotti per ricavo
    risultati["top_prodotti"] = (
        df.groupby("prodotto")["ricavo_totale"]
        .sum()
        .nlargest(10)
        .reset_index()
    )

    # Andamento mensile
    risultati["trend_mensile"] = (
        df.groupby(["anno", "mese"])
        .agg(
            ricavo=("ricavo_totale", "sum"),
            ordini=("id_ordine", "count")
        )
        .reset_index()
    )

    logger.info(f"Aggregazione completata: {len(risultati)} tabelle prodotte")
    return risultati


def load(
    df: pd.DataFrame,
    aggregazioni: dict[str, pd.DataFrame],
    config: ConfigPipeline
) -> None:
    """Fase di caricamento: scrive i risultati su file."""
    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Dati puliti in Parquet
    path_parquet = output_dir / "vendite_pulite.parquet"
    df.to_parquet(path_parquet, index=False)
    logger.info(f"Dati puliti salvati in: {path_parquet}")

    # Report Excel con piu fogli
    path_excel = output_dir / "report_vendite.xlsx"
    with pd.ExcelWriter(path_excel, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Dati Completi", index=False)
        for nome, tabella in aggregazioni.items():
            tabella.to_excel(writer, sheet_name=nome[:31], index=True)

    logger.info(f"Report Excel salvato in: {path_excel}")

    # CSV delle aggregazioni
    for nome, tabella in aggregazioni.items():
        path_csv = output_dir / f"{nome}.csv"
        tabella.to_csv(path_csv, index=False)

    logger.info("Export completato")


def main():
    """Punto di ingresso della pipeline ETL."""
    config = ConfigPipeline()
    logger.info("=" * 60)
    logger.info("AVVIO PIPELINE ETL VENDITE")
    logger.info("=" * 60)

    try:
        df = extract(config)
        df = validate(df)
        df = transform(df)
        aggregazioni = aggregate(df)
        load(df, aggregazioni, config)
        logger.info("PIPELINE COMPLETATA CON SUCCESSO")
    except Exception as e:
        logger.error(f"PIPELINE FALLITA: {e}")
        raise


if __name__ == "__main__":
    main()
```

---

## Performance

Quando si lavora con grandi volumi di dati, le prestazioni diventano critiche. Questa sezione illustra le tecniche principali per ottimizzare il data processing in Python.

### Vettorizzazione vs Loop

La vettorizzazione e la tecnica piu importante per le prestazioni con pandas e NumPy. Le operazioni vettorizzate sfruttano codice C ottimizzato internamente, evitando il costo dell'iterazione Python.

```python
import numpy as np
import pandas as pd

n = 1_000_000
df = pd.DataFrame({
    "a": np.random.randn(n),
    "b": np.random.randn(n)
})

# --- SBAGLIATO: loop Python (lento) ---
# risultato = []
# for i in range(len(df)):
#     risultato.append(df.iloc[i]["a"] ** 2 + df.iloc[i]["b"] ** 2)
# df["c"] = risultato

# --- CORRETTO: operazione vettorizzata (veloce) ---
df["c"] = df["a"] ** 2 + df["b"] ** 2

# --- SBAGLIATO: apply con funzione Python (lento per operazioni semplici) ---
# df["c"] = df.apply(lambda row: row["a"] ** 2 + row["b"] ** 2, axis=1)

# --- CORRETTO: NumPy per operazioni complesse ---
df["c"] = np.where(df["a"] > 0, df["a"] * df["b"], df["a"] + df["b"])
```

### Ottimizzazione dei dtypes

La scelta del tipo di dato corretto riduce drasticamente il consumo di memoria.

```python
# Analisi della memoria
print(df.memory_usage(deep=True))

# Downcast dei tipi numerici
df["quantita"] = pd.to_numeric(df["quantita"], downcast="integer")
df["prezzo"] = pd.to_numeric(df["prezzo"], downcast="float")

# Conversione a category per colonne con pochi valori unici
df["regione"] = df["regione"].astype("category")
df["prodotto"] = df["prodotto"].astype("category")

# Confronto memoria prima e dopo
def mostra_memoria(df: pd.DataFrame) -> None:
    mem_mb = df.memory_usage(deep=True).sum() / 1024**2
    print(f"Memoria totale: {mem_mb:.2f} MB")

# Funzione di ottimizzazione automatica
def ottimizza_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """Riduce il consumo di memoria ottimizzando i tipi di dato."""
    for col in df.columns:
        col_type = df[col].dtype

        if col_type == "object":
            n_unici = df[col].nunique()
            n_totali = len(df)
            if n_unici / n_totali < 0.5:
                df[col] = df[col].astype("category")
        elif col_type in ["int64", "int32"]:
            df[col] = pd.to_numeric(df[col], downcast="integer")
        elif col_type in ["float64", "float32"]:
            df[col] = pd.to_numeric(df[col], downcast="float")

    return df
```

### Elaborazione a Blocchi (Chunked Processing)

Per file troppo grandi per la memoria, pandas consente la lettura a blocchi.

```python
# Lettura a blocchi (chunk)
risultati = []
for chunk in pd.read_csv("dati_enormi.csv", chunksize=100_000):
    # Elabora ogni blocco
    chunk_filtrato = chunk[chunk["valore"] > 0]
    chunk_aggregato = chunk_filtrato.groupby("categoria")["valore"].sum()
    risultati.append(chunk_aggregato)

# Combina i risultati parziali
risultato_finale = pd.concat(risultati).groupby(level=0).sum()

# Funzione generica per elaborazione a blocchi
def processa_a_blocchi(
    file_path: str,
    funzione_trasformazione: Callable[[pd.DataFrame], pd.DataFrame],
    chunksize: int = 50_000,
    output_path: str = "output.parquet"
) -> None:
    """Elabora un file CSV di grandi dimensioni a blocchi."""
    blocchi_elaborati = []

    for i, chunk in enumerate(pd.read_csv(file_path, chunksize=chunksize)):
        logger.info(f"Elaborazione blocco {i + 1}...")
        chunk_elaborato = funzione_trasformazione(chunk)
        blocchi_elaborati.append(chunk_elaborato)

    df_finale = pd.concat(blocchi_elaborati, ignore_index=True)
    df_finale.to_parquet(output_path, index=False)
    logger.info(f"Risultato salvato in: {output_path}")
```

### Dask — Panoramica (Parallel pandas)

Dask estende l'API di pandas per l'elaborazione parallela e distribuita. E particolarmente utile quando i dati superano la capacita della RAM.

```python
import dask.dataframe as dd

# Lettura — Dask crea un grafo di computazione, non carica tutto in memoria
ddf = dd.read_csv("dati_enormi/*.csv")    # supporta glob patterns
ddf = dd.read_parquet("dati_enormi/")

# Le operazioni hanno la stessa sintassi di pandas
ddf_filtrato = ddf[ddf["valore"] > 100]
risultato = ddf_filtrato.groupby("categoria")["valore"].mean()

# compute() esegue effettivamente le operazioni
df_risultato = risultato.compute()  # restituisce un DataFrame pandas

# Parallelismo: Dask distribuisce le operazioni su piu core
ddf_trasformato = ddf.map_partitions(
    lambda df: df.assign(nuovo_campo=df["a"] * df["b"])
)

# Salvataggio in Parquet partizionato
ddf_trasformato.to_parquet(
    "output_partizionato/",
    partition_on=["anno", "mese"]
)
```

### Polars — Panoramica (Alternativa basata su Rust)

Polars e una libreria emergente per il data processing, scritta in Rust, che offre prestazioni superiori a pandas nella maggior parte degli scenari grazie all'esecuzione lazy, al parallelismo automatico e all'ottimizzazione delle query.

```python
import polars as pl

# Lettura
df = pl.read_csv("dati.csv")
df = pl.read_parquet("dati.parquet")

# API espressiva con chaining
risultato = (
    df
    .filter(pl.col("valore") > 100)
    .with_columns([
        (pl.col("prezzo") * pl.col("quantita")).alias("ricavo"),
        pl.col("nome").str.to_uppercase().alias("nome_upper")
    ])
    .group_by("categoria")
    .agg([
        pl.col("ricavo").sum().alias("ricavo_totale"),
        pl.col("ricavo").mean().alias("ricavo_medio"),
        pl.col("id").count().alias("n_ordini")
    ])
    .sort("ricavo_totale", descending=True)
)

# Modalita lazy — ottimizzazione automatica delle query
risultato_lazy = (
    pl.scan_csv("dati_enormi.csv")    # non carica nulla in memoria
    .filter(pl.col("anno") == 2024)
    .group_by("regione")
    .agg(pl.col("vendite").sum())
    .collect()                         # esegue la query ottimizzata
)

# Conversione da/a pandas
df_polars = pl.from_pandas(df_pandas)
df_pandas = df_polars.to_pandas()
```

---

## Best Practices

1. **Preferire sempre le operazioni vettorizzate ai loop Python.** Le operazioni vettorizzate di pandas e NumPy sono ordini di grandezza piu veloci dei loop `for`. Usare `apply()` con `axis=1` solo quando la logica non e esprimibile con operazioni vettoriali native; in quel caso, valutare se NumPy `np.where()` o `np.select()` possano sostituirlo.

2. **Validare i dati il prima possibile nella pipeline.** Inserire una fase di validazione esplicita subito dopo l'estrazione consente di individuare e gestire le anomalie prima che si propaghino nelle fasi successive. Utilizzare pandera o Pydantic per definire schemi formali e riproducibili.

3. **Ottimizzare i tipi di dato per ridurre il consumo di memoria.** Convertire le colonne con pochi valori unici al tipo `category`, eseguire il downcast dei tipi numerici (`int64` → `int32` o `int16`) e utilizzare formati colonnari come Parquet per lo storage. Questa pratica puo ridurre l'uso di memoria del 50-80%.

4. **Costruire pipeline modulari e testabili.** Ogni fase della pipeline deve essere una funzione (o classe) indipendente con input e output ben definiti. Questo approccio consente di scrivere unit test per ciascuna fase, sostituire o riordinare i passi senza effetti collaterali e debuggare problemi in isolamento.

5. **Gestire esplicitamente i valori mancanti.** Non ignorare mai i `NaN`. Documentare la strategia adottata per ogni colonna — rimozione, imputazione con media/mediana/moda, forward fill, interpolazione — e giustificare la scelta nel contesto del dominio applicativo.

6. **Utilizzare logging strutturato nelle pipeline.** Registrare il numero di righe in ingresso e in uscita da ogni fase, i tempi di esecuzione, il numero di record scartati e le anomalie riscontrate. Questi log sono essenziali per il monitoraggio in produzione e per il debugging.

7. **Lavorare con Parquet invece che CSV per lo storage intermedio.** Il formato Parquet e colonnare, compresso e tipizzato, il che lo rende enormemente piu efficiente del CSV per la lettura parziale (solo colonne necessarie), lo storage su disco e la conservazione dei tipi di dato senza ambiguita.

8. **Utilizzare metodi method chaining per trasformazioni leggibili.** L'uso di `pipe()`, `assign()` e il chaining dei metodi pandas producono codice piu leggibile e manutenibile rispetto alla modifica in-place del DataFrame. Evitare l'uso eccessivo di variabili intermedie.

9. **Profilare prima di ottimizzare.** Non assumere mai dove si trova il collo di bottiglia: misurare con `%timeit`, `cProfile` o `line_profiler`. Spesso il problema non e dove ci si aspetta. Per file molto grandi, valutare Dask o Polars solo dopo aver verificato che le ottimizzazioni locali non siano sufficienti.

10. **Documentare le assunzioni sui dati.** Ogni pipeline fa assunzioni implicite sulla struttura e la qualita dei dati in ingresso — formato delle date, encoding del file, intervallo dei valori numerici, presenza o assenza di intestazioni. Rendere esplicite queste assunzioni nel codice (tramite assert, validazioni o commenti) previene errori silenziosi quando la sorgente cambia.

---

## Polars — Deep Dive

La sezione precedente ha introdotto Polars con un esempio essenziale. Qui approfondiamo i concetti che rendono Polars una scelta superiore per workload ad alte prestazioni: lazy evaluation, Expression API, contesti e un confronto sistematico con pandas.

### Architettura e Modello di Esecuzione

Polars e scritto in Rust e sfrutta Apache Arrow come formato di memoria colonnare. A differenza di pandas, che utilizza un modello di esecuzione *eager* (ogni operazione viene eseguita immediatamente e materializza un DataFrame intermedio), Polars offre due modalita:

- **Eager mode**: simile a pandas — le operazioni vengono eseguite subito. Utile per esplorazione interattiva e prototyping.
- **Lazy mode**: le operazioni vengono registrate in un piano di query logico. L'esecuzione avviene solo alla chiamata di `.collect()`. Il query optimizer di Polars applica automaticamente ottimizzazioni come predicate pushdown, projection pushdown, fusione di operazioni e riordino delle fasi.

```python
import polars as pl

# --- Eager mode ---
df = pl.read_csv("vendite.csv")
risultato_eager = (
    df
    .filter(pl.col("regione") == "Nord")
    .select(["prodotto", "ricavo"])
    .sort("ricavo", descending=True)
)

# --- Lazy mode ---
# scan_csv non carica nulla in memoria — costruisce un LazyFrame
risultato_lazy = (
    pl.scan_csv("vendite.csv")
    .filter(pl.col("regione") == "Nord")
    .select(["prodotto", "ricavo"])
    .sort("ricavo", descending=True)
    .collect()  # solo qui avviene la lettura e l'esecuzione
)
```

### Lazy Evaluation — Ottimizzazioni Automatiche

Il lazy mode e il cuore delle prestazioni di Polars. Quando si costruisce una pipeline lazy, Polars registra ogni operazione in un grafo logico. Prima dell'esecuzione, il query planner applica diverse ottimizzazioni:

- **Predicate Pushdown**: i filtri vengono spostati il piu vicino possibile alla sorgente dati. Se si filtra per `anno == 2024` dopo un `group_by`, Polars sposta il filtro prima del raggruppamento, riducendo il volume dei dati elaborati.
- **Projection Pushdown**: se la pipeline finale utilizza solo 3 colonne su 50, Polars legge solo quelle 3 dal file sorgente (particolarmente efficace con Parquet).
- **Slice Pushdown**: operazioni come `.head(100)` vengono propagate alla sorgente.
- **Common Subexpression Elimination (CSE)**: espressioni duplicate vengono calcolate una sola volta.

```python
# Esempio di ottimizzazione automatica
piano = (
    pl.scan_parquet("dati_grandi.parquet")  # 50 colonne nel file
    .filter(pl.col("anno") >= 2023)          # predicate pushdown → letto solo anno >= 2023
    .select(["prodotto", "ricavo", "anno"])   # projection pushdown → lette solo 3 colonne
    .group_by("prodotto")
    .agg(pl.col("ricavo").sum().alias("ricavo_totale"))
    .sort("ricavo_totale", descending=True)
    .head(10)                                # slice pushdown
)

# Visualizzare il piano di query ottimizzato
print(piano.explain(optimized=True))

# Eseguire
top_10 = piano.collect()
```

### Expression API — Il Linguaggio di Polars

Le *expressions* sono il mattone fondamentale di Polars. Ogni trasformazione viene espressa come una composizione di espressioni, che sono valutate in modo vettorizzato e parallelizzato. Le espressioni vengono eseguite all'interno di *contesti* specifici.

#### Contesti di Esecuzione

Polars definisce tre contesti principali in cui le espressioni vengono valutate:

```python
import polars as pl

df = pl.DataFrame({
    "nome": ["Alice", "Bob", "Carlo", "Diana", "Elena"],
    "reparto": ["IT", "IT", "HR", "HR", "IT"],
    "stipendio": [45000, 38000, 52000, 41000, 47000],
    "anni_esperienza": [5, 3, 10, 6, 7],
})

# 1. CONTESTO SELECT — seleziona e trasforma colonne
risultato = df.select(
    pl.col("nome"),
    pl.col("stipendio").mean().alias("stipendio_medio_globale"),
    (pl.col("stipendio") / 12).round(2).alias("stipendio_mensile"),
)

# 2. CONTESTO WITH_COLUMNS — aggiunge/modifica colonne mantenendo le esistenti
risultato = df.with_columns(
    (pl.col("stipendio") * 1.10).alias("stipendio_con_aumento"),
    pl.col("nome").str.to_uppercase().alias("nome_maiuscolo"),
    pl.when(pl.col("anni_esperienza") >= 5)
      .then(pl.lit("senior"))
      .otherwise(pl.lit("junior"))
      .alias("livello"),
)

# 3. CONTESTO GROUP_BY + AGG — aggregazione per gruppo
risultato = df.group_by("reparto").agg(
    pl.col("stipendio").mean().alias("stipendio_medio"),
    pl.col("stipendio").max().alias("stipendio_max"),
    pl.col("nome").count().alias("n_dipendenti"),
    (pl.col("stipendio").max() - pl.col("stipendio").min()).alias("range_stipendio"),
    pl.col("anni_esperienza").sort(descending=True).first().alias("max_esperienza"),
)
```

#### Composizione di Espressioni

Le espressioni Polars sono composte con il method chaining, producendo pipeline dichiarative:

```python
# Espressione complessa composta
risultato = df.select(
    # Operazione stringa → filtro → aggregazione, in una sola espressione
    pl.col("nome")
      .str.to_lowercase()
      .str.contains("a")
      .sum()
      .alias("nomi_con_a"),

    # Condizionale + aritmetica
    pl.when(pl.col("anni_esperienza") > 5)
      .then(pl.col("stipendio") * 1.15)
      .otherwise(pl.col("stipendio") * 1.05)
      .mean()
      .alias("stipendio_medio_proiettato"),
)

# Window functions (operazioni all'interno di gruppi senza collassare le righe)
risultato = df.with_columns(
    pl.col("stipendio")
      .mean()
      .over("reparto")
      .alias("media_reparto"),

    pl.col("stipendio")
      .rank()
      .over("reparto")
      .alias("rank_nel_reparto"),

    (pl.col("stipendio") - pl.col("stipendio").mean().over("reparto"))
      .alias("delta_dalla_media"),
)
```

### Polars vs pandas — Confronto Sistematico

| Caratteristica | pandas | Polars |
|---|---|---|
| Linguaggio core | C / Cython | Rust |
| Formato memoria | NumPy-backed (row-oriented per default) | Apache Arrow (colonnare) |
| Esecuzione | Eager (ogni operazione materializza) | Eager + Lazy (query optimizer) |
| Threading | Single-thread (GIL) | Multi-thread nativo (Rayon) |
| Indice | Si — indice per righe, spesso implicito | No — nessun indice, solo colonne |
| Mutabilita | DataFrame mutabile (in-place ops) | DataFrame immutabile per design |
| Memoria (1M righe, 10 col) | ~120 MB tipici | ~40-60 MB tipici |
| Velocita filtro (1M righe) | ~50ms | ~5ms (10x piu veloce) |
| Velocita group_by (10M righe) | ~800ms | ~80ms (10x piu veloce) |
| Velocita join (10M righe) | ~1.2s | ~100ms (12x piu veloce) |
| Ecosistema | Vastissimo, maturo | In crescita rapida, compatibile Arrow |
| Curva di apprendimento | Bassa (standard de facto) | Media (API diversa, ma coerente) |
| Casi d'uso ottimali | Prototyping, dataset < 1GB, interoperabilita | ETL ad alte prestazioni, dataset grandi, pipeline produzione |

### Interoperabilita Polars-pandas

```python
import polars as pl
import pandas as pd

# pandas → Polars (zero-copy quando possibile con Arrow backend)
df_pandas = pd.DataFrame({"a": [1, 2, 3], "b": [4.0, 5.0, 6.0]})
df_polars = pl.from_pandas(df_pandas)

# Polars → pandas
df_pandas_ritorno = df_polars.to_pandas()

# Polars → Arrow Table (zero-copy)
arrow_table = df_polars.to_arrow()

# Arrow Table → Polars (zero-copy)
df_da_arrow = pl.from_arrow(arrow_table)
```

---

## Apache Arrow e PyArrow

Apache Arrow e uno standard aperto per dati colonnari in memoria, progettato per l'interscambio ad alte prestazioni tra sistemi e linguaggi di programmazione. Definisce un formato di memoria colonnare indipendente dal linguaggio e un protocollo IPC (Inter-Process Communication) per lo scambio di dati senza serializzazione.

### Formato Colonnare in Memoria

A differenza dei formati row-oriented (come i record di un database tradizionale), Arrow organizza i dati per colonne contigue in memoria. Questo layout e ottimale per le operazioni analitiche, che tipicamente accedono a poche colonne ma a molte righe.

```python
import pyarrow as pa

# Creazione di un Array Arrow
arr_int = pa.array([1, 2, 3, 4, 5])
arr_str = pa.array(["Alice", "Bob", "Carlo", None, "Elena"])
arr_float = pa.array([45.5, 38.0, 52.1, 41.0, 47.3], type=pa.float64())

# Creazione di una Arrow Table (equivalente di un DataFrame)
tabella = pa.table({
    "nome": arr_str,
    "eta": arr_int,
    "stipendio_k": arr_float,
})

print(tabella)
print(f"Schema: {tabella.schema}")
print(f"Righe: {tabella.num_rows}, Colonne: {tabella.num_columns}")

# Accesso a una colonna (zero-copy — nessuna allocazione)
colonna_nomi = tabella.column("nome")
print(colonna_nomi)

# Filtraggio con compute functions Arrow
import pyarrow.compute as pc
mask = pc.greater(tabella.column("stipendio_k"), 40.0)
tabella_filtrata = tabella.filter(mask)
print(tabella_filtrata)
```

### Zero-Copy e Interoperabilita

Il vantaggio principale di Arrow e la capacita di scambiare dati tra librerie e processi senza copiarli. Quando pandas, Polars, DuckDB e PyArrow condividono dati tramite Arrow, non avviene alcuna serializzazione o copia in memoria:

```python
import pyarrow as pa
import pandas as pd
import polars as pl

# Creazione di una tabella Arrow
tabella = pa.table({
    "id": pa.array(range(1_000_000)),
    "valore": pa.array([float(i) * 1.5 for i in range(1_000_000)]),
})

# Arrow → pandas (zero-copy con types_mapper)
df_pandas = tabella.to_pandas(types_mapper=pd.ArrowDtype)
print(df_pandas.dtypes)  # usa i tipi Arrow-backed di pandas

# Arrow → Polars (zero-copy)
df_polars = pl.from_arrow(tabella)

# pandas con backend PyArrow (pandas 2.x)
df_arrow_backend = pd.DataFrame({
    "id": pd.array(range(100), dtype="int64[pyarrow]"),
    "nome": pd.array(["test"] * 100, dtype="string[pyarrow]"),
})
print(df_arrow_backend.dtypes)
```

### Pandas 2.x con Backend PyArrow

Pandas 2.x ha introdotto il backend PyArrow come alternativa al tradizionale backend NumPy. Questo offre diversi vantaggi: migliore gestione dei tipi nullable, supporto nativo per stringhe (senza il tipo `object`), riduzione del consumo di memoria e interoperabilita zero-copy con il resto dell'ecosistema Arrow.

```python
import pandas as pd

# Lettura CSV con engine PyArrow (parser C++ piu veloce)
df = pd.read_csv(
    "dati_grandi.csv",
    engine="pyarrow",                    # parser PyArrow
    dtype_backend="pyarrow",             # tipi Arrow-backed
)
print(df.dtypes)
# id            int64[pyarrow]
# nome          large_string[pyarrow]
# valore        double[pyarrow]
# data          timestamp[ns][pyarrow]

# Lettura Parquet con backend PyArrow
df = pd.read_parquet("dati.parquet", dtype_backend="pyarrow")

# Confronto memoria: backend NumPy vs PyArrow
import numpy as np
n = 1_000_000
df_numpy = pd.DataFrame({
    "testo": np.random.choice(["alfa", "beta", "gamma"], n),
    "intero": np.random.randint(0, 1000, n),
})
df_arrow = pd.DataFrame({
    "testo": pd.array(np.random.choice(["alfa", "beta", "gamma"], n),
                       dtype="string[pyarrow]"),
    "intero": pd.array(np.random.randint(0, 1000, n),
                        dtype="int64[pyarrow]"),
})
print(f"NumPy backend: {df_numpy.memory_usage(deep=True).sum() / 1024**2:.1f} MB")
print(f"Arrow backend: {df_arrow.memory_usage(deep=True).sum() / 1024**2:.1f} MB")
# Arrow backend tipicamente usa 30-50% meno memoria per stringhe
```

### Arrow IPC — Scambio Dati Inter-Processo

Arrow definisce due formati binari per lo scambio di dati:

- **IPC Streaming Format**: per lo scambio sequenziale di record batch, ideale per comunicazione tra processi.
- **IPC File Format (Feather v2)**: per accesso random ai record batch, ottimale per file su disco.

```python
import pyarrow as pa
import pyarrow.ipc as ipc

tabella = pa.table({
    "id": range(10000),
    "valore": [float(i) * 0.5 for i in range(10000)],
})

# --- IPC Streaming Format ---
# Scrittura
sink = pa.BufferOutputStream()
writer = ipc.new_stream(sink, tabella.schema)
writer.write_table(tabella)
writer.close()
buffer = sink.getvalue()
print(f"Dimensione stream: {len(buffer)} bytes")

# Lettura (zero-copy da buffer)
reader = ipc.open_stream(buffer)
tabella_letta = reader.read_all()

# --- IPC File Format (Feather v2) ---
import pyarrow.feather as feather

# Scrittura su file Feather
feather.write_feather(tabella, "dati.feather", compression="zstd")

# Lettura (supporta memory-mapping per zero-copy)
tabella_feather = feather.read_table("dati.feather")

# Lettura con memory-mapping per zero-copy reale
source = pa.memory_map("dati.feather", "r")
tabella_mmap = ipc.open_file(source).read_all()
```

---

## DuckDB per Query Analitiche

DuckDB e un database analitico embedded (in-process) progettato per eseguire query OLAP direttamente all'interno di un processo Python, senza bisogno di un server separato. Si integra nativamente con pandas, Polars e PyArrow tramite *replacement scans* — la capacita di trattare DataFrame e tabelle Arrow come tabelle SQL senza copia dei dati.

### Fondamenti

```python
import duckdb
import pandas as pd

# DuckDB opera in-memory per default
con = duckdb.connect()

# Query su dati in memoria
df = pd.DataFrame({
    "prodotto": ["Widget A", "Widget B", "Widget A", "Widget C", "Widget B"],
    "regione": ["Nord", "Sud", "Nord", "Centro", "Nord"],
    "quantita": [100, 200, 150, 80, 300],
    "prezzo": [10.0, 15.0, 10.0, 20.0, 15.0],
})

# DuckDB legge direttamente il DataFrame pandas — zero-copy
risultato = con.sql("""
    SELECT
        prodotto,
        SUM(quantita) AS quantita_totale,
        SUM(quantita * prezzo) AS ricavo_totale,
        AVG(prezzo) AS prezzo_medio,
        COUNT(*) AS n_transazioni
    FROM df
    GROUP BY prodotto
    ORDER BY ricavo_totale DESC
""").fetchdf()  # restituisce un DataFrame pandas

print(risultato)
```

### Query su File Parquet senza Caricamento in Memoria

Una delle funzionalita piu potenti di DuckDB e la capacita di eseguire query SQL direttamente su file Parquet, CSV e JSON senza doverli caricare interamente in memoria:

```python
import duckdb

# Query diretta su file Parquet — DuckDB legge solo le colonne necessarie
risultato = duckdb.sql("""
    SELECT
        regione,
        COUNT(*) AS ordini,
        SUM(ricavo) AS ricavo_totale
    FROM 'vendite/*.parquet'
    WHERE anno >= 2024
    GROUP BY regione
    HAVING ricavo_totale > 100000
    ORDER BY ricavo_totale DESC
    LIMIT 20
""").fetchdf()

# Query su file CSV con inferenza automatica dello schema
risultato = duckdb.sql("""
    SELECT *
    FROM read_csv_auto('dati_legacy.csv', header=true, sep=';')
    WHERE importo > 0
    LIMIT 1000
""").fetchdf()

# Glob pattern per file multipli
risultato = duckdb.sql("""
    SELECT
        filename AS file_sorgente,
        COUNT(*) AS righe
    FROM 'dati/2024/**/*.parquet'
    GROUP BY filename
""").fetchdf()
```

### Integrazione con Polars e Arrow

```python
import duckdb
import polars as pl
import pyarrow as pa

# DuckDB + Polars
df_polars = pl.DataFrame({
    "id": range(1000),
    "categoria": ["A", "B", "C"] * 333 + ["A"],
    "valore": [float(i) * 1.5 for i in range(1000)],
})

# Query su DataFrame Polars
risultato = duckdb.sql("""
    SELECT categoria, AVG(valore) AS media
    FROM df_polars
    GROUP BY categoria
""").pl()  # .pl() restituisce un Polars DataFrame

# DuckDB + Arrow Table
tabella_arrow = pa.table({"x": range(100), "y": [i**2 for i in range(100)]})
risultato_arrow = duckdb.sql("""
    SELECT * FROM tabella_arrow WHERE y > 1000
""").arrow()  # .arrow() restituisce un Arrow Table

# Conversione di risultati DuckDB
query = "SELECT * FROM 'file.parquet' LIMIT 100"
df_pandas = duckdb.sql(query).fetchdf()     # → pandas DataFrame
df_polars = duckdb.sql(query).pl()          # → Polars DataFrame
tbl_arrow = duckdb.sql(query).arrow()       # → Arrow Table
```

### Casi d'uso Ideali per DuckDB

- **Analisi esplorativa su file Parquet** senza caricarli in memoria.
- **Query SQL complesse** che sarebbero verbose con l'API pandas (subquery, window functions, CTE).
- **Join tra DataFrame e file su disco**: DuckDB consente di unire un DataFrame in memoria con un file Parquet da 10 GB senza caricare tutto.
- **Sostituzione di Spark per dataset medi** (fino a ~100 GB su una singola macchina con SSD).

```python
# Esempio avanzato: CTE, window functions, subquery
risultato = duckdb.sql("""
    WITH vendite_mensili AS (
        SELECT
            prodotto,
            DATE_TRUNC('month', data_ordine) AS mese,
            SUM(ricavo) AS ricavo_mensile
        FROM 'vendite.parquet'
        GROUP BY prodotto, DATE_TRUNC('month', data_ordine)
    )
    SELECT
        prodotto,
        mese,
        ricavo_mensile,
        LAG(ricavo_mensile) OVER (
            PARTITION BY prodotto ORDER BY mese
        ) AS ricavo_mese_precedente,
        ricavo_mensile - LAG(ricavo_mensile) OVER (
            PARTITION BY prodotto ORDER BY mese
        ) AS variazione
    FROM vendite_mensili
    ORDER BY prodotto, mese
""").fetchdf()
```

---

## Serializzazione dei Dati

La scelta del formato di serializzazione influisce su prestazioni di lettura/scrittura, dimensione su disco, compatibilita tra sistemi e capacita di evoluzione dello schema. Questa sezione confronta i formati principali per il data processing in Python.

### Parquet — Deep Dive

Apache Parquet e un formato colonnare binario, compresso e tipizzato, progettato per workload analitici. E diventato lo standard de facto per lo storage di dati tabulari nell'ecosistema Python.

```python
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# --- Scrittura Parquet con opzioni avanzate ---
df = pd.DataFrame({
    "id": range(1_000_000),
    "categoria": ["A", "B", "C", "D"] * 250_000,
    "valore": [float(i) * 0.1 for i in range(1_000_000)],
    "data": pd.date_range("2024-01-01", periods=1_000_000, freq="s"),
})

# Scrittura con compressione e partizionamento
tabella = pa.Table.from_pandas(df)

# File singolo con compressione
pq.write_table(tabella, "dati.parquet", compression="zstd")

# Partizionamento Hive-style (un file per partizione)
pq.write_to_dataset(
    tabella,
    root_path="dati_partizionati/",
    partition_cols=["categoria"],
    compression="snappy",
)

# --- Lettura selettiva ---
# Solo colonne necessarie (projection pushdown)
df_parziale = pd.read_parquet("dati.parquet", columns=["id", "valore"])

# Con filtro (predicate pushdown — il filtro viene spinto al livello di row group)
filtri = [("categoria", "==", "A"), ("valore", ">", 50000)]
df_filtrato = pd.read_parquet(
    "dati_partizionati/",
    filters=filtri,
)

# --- Metadati Parquet ---
meta = pq.read_metadata("dati.parquet")
print(f"Righe: {meta.num_rows}")
print(f"Row groups: {meta.num_row_groups}")
print(f"Dimensione: {meta.serialized_size} bytes")
print(f"Schema: {meta.schema}")
```

### Apache Avro

Avro e un formato row-oriented con schema embedded, ottimale per lo streaming e l'evoluzione dello schema. E lo standard in ecosistemi come Apache Kafka per la serializzazione dei messaggi.

```python
import avro.schema
from avro.datafile import DataFileWriter, DataFileReader
from avro.io import DatumWriter, DatumReader
import json

# Definizione dello schema Avro
schema_json = {
    "type": "record",
    "name": "Ordine",
    "fields": [
        {"name": "id", "type": "int"},
        {"name": "prodotto", "type": "string"},
        {"name": "quantita", "type": "int"},
        {"name": "prezzo", "type": "double"},
        {"name": "note", "type": ["null", "string"], "default": None},
    ]
}
schema = avro.schema.parse(json.dumps(schema_json))

# Scrittura
with DataFileWriter(open("ordini.avro", "wb"), DatumWriter(), schema) as writer:
    writer.append({"id": 1, "prodotto": "Widget A", "quantita": 10, "prezzo": 9.99, "note": None})
    writer.append({"id": 2, "prodotto": "Widget B", "quantita": 5, "prezzo": 14.50, "note": "urgente"})

# Lettura
with DataFileReader(open("ordini.avro", "rb"), DatumReader()) as reader:
    for record in reader:
        print(record)

# Alternativa piu veloce: fastavro
import fastavro

records = [
    {"id": 1, "prodotto": "Widget A", "quantita": 10, "prezzo": 9.99, "note": None},
    {"id": 2, "prodotto": "Widget B", "quantita": 5, "prezzo": 14.50, "note": "urgente"},
]
with open("ordini_fast.avro", "wb") as f:
    fastavro.writer(f, fastavro.parse_schema(schema_json), records)
```

### Confronto Formati di Serializzazione

| Caratteristica | Parquet | Avro | Arrow IPC / Feather | CSV | JSON |
|---|---|---|---|---|---|
| Orientamento | Colonnare | Riga | Colonnare | Riga | Riga |
| Compressione | Eccellente (snappy, zstd, gzip) | Buona (deflate, snappy) | Opzionale (zstd, lz4) | Nessuna | Nessuna |
| Schema | Embedded, tipizzato | Embedded, evoluzione nativa | Embedded, Arrow types | Nessuno | Nessuno |
| Lettura parziale | Si (column/row group pruning) | No (sequenziale) | Si (column selection) | No | No |
| Velocita lettura | Veloce (per query analitiche) | Media | Molto veloce (zero-copy) | Lenta | Lenta |
| Velocita scrittura | Media | Veloce | Molto veloce | Veloce | Veloce |
| Uso tipico | Data lake, analytics, ML | Kafka, streaming, schema evolution | IPC, cache intermedia, notebook | Interscambio legacy | API, config |
| Supporto Python | pyarrow, pandas, polars | fastavro, avro-python3 | pyarrow, polars | stdlib csv, pandas | stdlib json, pandas |
| Dimensione su disco (1M righe) | ~15 MB | ~40 MB | ~25 MB | ~80 MB | ~120 MB |

### Quando Usare Quale Formato

- **Parquet**: storage a lungo termine, data lake, pipeline analitiche, ML feature store. Formato predefinito per lo storage intermedio nelle pipeline ETL.
- **Avro**: streaming (Kafka), sistemi che richiedono evoluzione dello schema (aggiunta/rimozione di campi senza breaking change), log di eventi.
- **Arrow IPC / Feather**: scambio rapido tra processi sulla stessa macchina, cache intermedie, file temporanei durante la pipeline, notebook interattivi.
- **CSV**: interoperabilita con sistemi legacy, import/export manuale, file di configurazione semplici.
- **JSON / JSONL**: API REST, log strutturati, configurazione, dati semi-strutturati.

---

## Dask per Elaborazione Distribuita — Approfondimento

La sezione precedente ha introdotto Dask con un esempio essenziale. Qui approfondiamo i pattern avanzati per l'elaborazione parallela e distribuita di dataset che superano la capacita della RAM.

### Architettura di Dask

Dask opera costruendo un *task graph* — un grafo aciclico diretto (DAG) di operazioni — che viene eseguito da uno scheduler. Dask offre tre scheduler:

- **Synchronous**: esecuzione sequenziale, utile per debugging.
- **Threaded**: parallelismo su thread (default per dask.dataframe, soggetto al GIL per operazioni Python pure).
- **Distributed**: scheduler completo con dashboard web, adatto a cluster multi-macchina.

```python
import dask.dataframe as dd
from dask.distributed import Client

# Avvio dello scheduler distribuito (anche su singola macchina)
client = Client(n_workers=4, threads_per_worker=2, memory_limit="4GB")
print(client.dashboard_link)  # dashboard web per monitorare l'esecuzione

# Lettura di un dataset partizionato — Dask crea una partizione per file
ddf = dd.read_parquet(
    "dati_grandi/anno=*/mese=*/*.parquet",
    columns=["prodotto", "regione", "ricavo", "data_ordine"],
)
print(f"Partizioni: {ddf.npartitions}")
print(f"Righe stimate: {len(ddf)}")  # calcolo lazy — potrebbe richiedere compute

# Operazioni lazy (non vengono eseguite fino a .compute())
risultato = (
    ddf
    .loc[ddf["ricavo"] > 100]
    .groupby("regione")
    .agg({"ricavo": ["sum", "mean", "count"]})
)

# Esecuzione e materializzazione
df_risultato = risultato.compute()  # restituisce un pandas DataFrame
```

### Pattern Avanzati con Dask

```python
import dask.dataframe as dd
import pandas as pd

# --- Map Partitions: applicare una funzione pandas a ciascuna partizione ---
def arricchisci_partizione(df: pd.DataFrame) -> pd.DataFrame:
    """Funzione pandas pura applicata a ciascuna partizione."""
    df = df.copy()
    df["ricavo_log"] = df["ricavo"].apply(lambda x: max(0, x).__log10__() if x > 0 else 0)
    df["trimestre"] = df["data_ordine"].dt.quarter
    return df

# map_partitions applica la funzione a ciascuna partizione in parallelo
ddf_arricchito = ddf.map_partitions(
    arricchisci_partizione,
    meta={"prodotto": "str", "regione": "str", "ricavo": "float64",
           "data_ordine": "datetime64[ns]", "ricavo_log": "float64", "trimestre": "int64"},
)

# --- Repartition: ottimizzare il numero di partizioni ---
# Troppe partizioni piccole = overhead di scheduling
# Poche partizioni grandi = meno parallelismo
ddf_ottimizzato = ddf.repartition(npartitions=8)

# --- Persist: mantenere in memoria per riutilizzo ---
ddf_cache = ddf_ottimizzato.persist()  # mantiene le partizioni in memoria dei worker

# --- Salvataggio in Parquet partizionato ---
ddf_arricchito.to_parquet(
    "output_dask/",
    partition_on=["regione"],
    compression="snappy",
    write_index=False,
)
```

### Quando Scegliere Dask vs Polars vs pandas

| Scenario | Scelta consigliata | Motivazione |
|---|---|---|
| Dataset < 1 GB, esplorazione | pandas | API matura, ecosistema vastissimo |
| Dataset 1-10 GB, singola macchina | Polars | Velocita superiore, lazy evaluation |
| Dataset 10-100 GB, singola macchina | DuckDB + Polars | DuckDB per query SQL, Polars per trasformazioni |
| Dataset > 100 GB, cluster | Dask / Spark | Distribuzione reale su piu macchine |
| Pipeline ETL ad alte prestazioni | Polars (lazy mode) | Ottimizzatore di query, parallelismo nativo |
| Analisi SQL interattiva su file | DuckDB | SQL nativo, pushdown su Parquet |

---

## Pattern di Pulizia Dati Avanzati

La sezione precedente ha trattato la gestione dei valori mancanti con pandas (`fillna`, `dropna`, interpolazione). Qui approfondiamo strategie avanzate per la pulizia dei dati, inclusa la rilevazione degli outlier e pattern di normalizzazione.

### Strategie Avanzate per Dati Mancanti

La scelta della strategia di imputazione dipende dalla natura dei dati e dal dominio applicativo:

```python
import pandas as pd
import numpy as np

df = pd.DataFrame({
    "id_sensore": [1, 1, 1, 1, 2, 2, 2, 2],
    "timestamp": pd.date_range("2024-01-01", periods=8, freq="h"),
    "temperatura": [22.5, np.nan, 23.1, np.nan, 18.0, 18.5, np.nan, 19.0],
    "umidita": [45, 46, np.nan, 48, np.nan, np.nan, 60, 62],
    "stato": ["ok", None, "ok", "ok", None, "ok", "errore", "ok"],
})

# --- Strategia 1: Imputazione per gruppo ---
# Usare la media del sensore, non la media globale
df["temperatura_imp"] = df.groupby("id_sensore")["temperatura"].transform(
    lambda x: x.fillna(x.mean())
)

# --- Strategia 2: Interpolazione temporale all'interno del gruppo ---
df["umidita_imp"] = df.groupby("id_sensore")["umidita"].transform(
    lambda x: x.interpolate(method="linear")
)

# --- Strategia 3: KNN Imputation (richiede scikit-learn) ---
from sklearn.impute import KNNImputer

imputer = KNNImputer(n_neighbors=3, weights="distance")
colonne_numeriche = ["temperatura", "umidita"]
df[colonne_numeriche] = imputer.fit_transform(df[colonne_numeriche])

# --- Strategia 4: Flag per dati imputati ---
# Creare colonne indicatore prima dell'imputazione per tracciabilita
df["temperatura_was_nan"] = df["temperatura"].isna().astype(int)
df["temperatura"] = df["temperatura"].fillna(df["temperatura"].median())

# --- Strategia 5: Soglia di completezza per colonne ---
def rimuovi_colonne_sparse(df: pd.DataFrame, soglia: float = 0.3) -> pd.DataFrame:
    """Rimuove colonne con percentuale di NaN superiore alla soglia."""
    percentuali_nan = df.isna().mean()
    colonne_da_tenere = percentuali_nan[percentuali_nan <= soglia].index.tolist()
    rimosse = set(df.columns) - set(colonne_da_tenere)
    if rimosse:
        print(f"Colonne rimosse (>{soglia*100}% NaN): {rimosse}")
    return df[colonne_da_tenere]
```

### Rilevazione degli Outlier

Gli outlier possono distorcere analisi statistiche, modelli di ML e aggregazioni. Esistono diverse tecniche per identificarli:

```python
import pandas as pd
import numpy as np

df = pd.DataFrame({
    "prodotto": ["A"] * 100 + ["B"] * 100,
    "prezzo": np.concatenate([
        np.random.normal(50, 5, 98).tolist() + [200, 5],      # A: due outlier
        np.random.normal(30, 3, 99).tolist() + [150],          # B: un outlier
    ]),
})

# --- Metodo 1: IQR (Interquartile Range) ---
def rileva_outlier_iqr(
    df: pd.DataFrame,
    colonna: str,
    fattore: float = 1.5
) -> pd.Series:
    """Restituisce una maschera booleana: True = outlier."""
    q1 = df[colonna].quantile(0.25)
    q3 = df[colonna].quantile(0.75)
    iqr = q3 - q1
    limite_inf = q1 - fattore * iqr
    limite_sup = q3 + fattore * iqr
    return (df[colonna] < limite_inf) | (df[colonna] > limite_sup)

# Per gruppo (outlier diversi per prodotto A e B)
df["is_outlier_iqr"] = df.groupby("prodotto")["prezzo"].transform(
    lambda x: rileva_outlier_iqr(pd.DataFrame({"prezzo": x}), "prezzo")
)

# --- Metodo 2: Z-Score ---
def rileva_outlier_zscore(
    df: pd.DataFrame,
    colonna: str,
    soglia: float = 3.0
) -> pd.Series:
    """Outlier = valori con z-score > soglia."""
    media = df[colonna].mean()
    std = df[colonna].std()
    z_scores = (df[colonna] - media).abs() / std
    return z_scores > soglia

df["is_outlier_zscore"] = rileva_outlier_zscore(df, "prezzo", soglia=3.0)

# --- Metodo 3: Modified Z-Score (robusto con la mediana) ---
def rileva_outlier_modified_zscore(
    df: pd.DataFrame,
    colonna: str,
    soglia: float = 3.5
) -> pd.Series:
    """Usa la mediana e il MAD — piu robusto del z-score classico."""
    mediana = df[colonna].median()
    mad = np.median(np.abs(df[colonna] - mediana))
    modified_z = 0.6745 * (df[colonna] - mediana) / mad if mad != 0 else pd.Series(0, index=df.index)
    return modified_z.abs() > soglia

# --- Strategie di gestione degli outlier ---
# Opzione A: Rimozione
df_senza_outlier = df[~df["is_outlier_iqr"]]

# Opzione B: Capping (winsorization) — limita i valori estremi
def cap_outlier(serie: pd.Series, percentile_inf: float = 0.01, percentile_sup: float = 0.99) -> pd.Series:
    """Limita i valori al range [percentile_inf, percentile_sup]."""
    lower = serie.quantile(percentile_inf)
    upper = serie.quantile(percentile_sup)
    return serie.clip(lower=lower, upper=upper)

df["prezzo_capped"] = cap_outlier(df["prezzo"])

# Opzione C: Sostituzione con la mediana
df.loc[df["is_outlier_iqr"], "prezzo"] = df.loc[~df["is_outlier_iqr"], "prezzo"].median()
```

### Normalizzazione e Standardizzazione dei Dati

```python
import pandas as pd
import numpy as np

# --- Normalizzazione di stringhe ---
def normalizza_testo(df: pd.DataFrame, colonne: list[str]) -> pd.DataFrame:
    """Normalizzazione completa di colonne testuali."""
    df = df.copy()
    for col in colonne:
        df[col] = (
            df[col]
            .str.strip()                           # rimuove spazi iniziali/finali
            .str.lower()                           # minuscolo
            .str.replace(r"\s+", " ", regex=True)  # spazi multipli → singolo
            .str.replace(r"[^\w\s]", "", regex=True)  # rimuove punteggiatura
        )
    return df

# --- Normalizzazione di date in formati misti ---
def normalizza_date(serie: pd.Series) -> pd.Series:
    """Gestisce formati data misti: DD/MM/YYYY, YYYY-MM-DD, DD-MM-YYYY, etc."""
    return pd.to_datetime(serie, dayfirst=True, errors="coerce")

# --- Deduplicazione fuzzy (per nomi con typo) ---
def deduplica_fuzzy(
    df: pd.DataFrame,
    colonna: str,
    soglia_somiglianza: float = 0.85
) -> pd.DataFrame:
    """Deduplicazione basata su similarita di stringhe.
    Richiede: pip install thefuzz python-Levenshtein
    """
    from thefuzz import fuzz
    valori_unici = df[colonna].unique()
    mappatura = {}

    for i, val1 in enumerate(valori_unici):
        if val1 in mappatura:
            continue
        for val2 in valori_unici[i+1:]:
            if val2 not in mappatura:
                if fuzz.ratio(str(val1), str(val2)) >= soglia_somiglianza * 100:
                    mappatura[val2] = val1  # val2 viene mappato a val1

    df = df.copy()
    df[colonna] = df[colonna].replace(mappatura)
    return df
```

---

## Tecniche Avanzate di Performance pandas

Oltre alla vettorizzazione e all'ottimizzazione dei dtype trattate nella sezione Performance, pandas offre strumenti piu sofisticati per accelerare le operazioni su grandi DataFrame.

### pandas.eval() e pandas.query()

`eval()` compila espressioni in codice C tramite numexpr, bypassando la creazione di array temporanei intermedi. E efficace su DataFrame con piu di 10.000 righe.

```python
import pandas as pd
import numpy as np

n = 5_000_000
df = pd.DataFrame({
    "a": np.random.randn(n),
    "b": np.random.randn(n),
    "c": np.random.randn(n),
    "d": np.random.randn(n),
})

# --- eval() per espressioni aritmetiche ---
# Metodo standard: crea 3 array temporanei
# risultato = df["a"] + df["b"] * df["c"] - df["d"]

# eval() usa numexpr — un solo passaggio, meno memoria
df["risultato"] = df.eval("a + b * c - d")

# Espressioni multiple in un solo eval()
df = df.eval("""
    rapporto = a / (b + 1)
    prodotto = c * d
    flag = (a > 0) & (b < 0)
""")

# --- query() per filtri complessi ---
# Metodo standard: crea array booleano intermedio
# filtrato = df[(df["a"] > 0) & (df["b"] < 0.5) & (df["c"].between(-1, 1))]

# query() — piu leggibile e leggermente piu veloce su grandi DataFrame
filtrato = df.query("a > 0 and b < 0.5 and -1 <= c <= 1")

# Variabili esterne con @
soglia_min = 0.0
soglia_max = 1.5
filtrato = df.query("@soglia_min < a < @soglia_max")
```

### Categorical dtype — Approfondimento

Il tipo `category` e uno degli strumenti piu sottovalutati per la performance di pandas. Oltre al risparmio di memoria, accelera significativamente `groupby`, `merge`, `sort` e `value_counts` su colonne con cardinalita limitata.

```python
import pandas as pd
import numpy as np

n = 2_000_000
regioni = ["Nord", "Sud", "Centro", "Isole", "Nord-Est", "Nord-Ovest"]
prodotti = [f"Prodotto_{i}" for i in range(50)]

df = pd.DataFrame({
    "regione": np.random.choice(regioni, n),
    "prodotto": np.random.choice(prodotti, n),
    "valore": np.random.randn(n) * 100 + 500,
})

# --- Conversione a category ---
df["regione"] = df["regione"].astype("category")
df["prodotto"] = df["prodotto"].astype("category")

# Confronto memoria
print(df.memory_usage(deep=True))
# regione (category): ~2 MB vs ~120 MB (object)
# prodotto (category): ~4 MB vs ~140 MB (object)

# --- Category ordinale (con ordine specifico) ---
from pandas.api.types import CategoricalDtype

livelli_tipo = CategoricalDtype(
    categories=["junior", "mid", "senior", "lead", "principal"],
    ordered=True
)
df_emp = pd.DataFrame({
    "nome": ["Alice", "Bob", "Carlo"],
    "livello": pd.Categorical(["senior", "junior", "mid"], dtype=livelli_tipo),
})

# Operazioni di confronto su categorie ordinate
print(df_emp[df_emp["livello"] >= "mid"])  # senior e mid

# --- Velocita groupby con category ---
# groupby su colonne category e significativamente piu veloce
# perche pandas usa indici interi interni invece di confrontare stringhe
risultato = df.groupby("regione")["valore"].mean()
```

### Numba JIT per Funzioni Personalizzate

Quando una trasformazione personalizzata non e esprimibile con operazioni vettorizzate native, Numba consente di compilare funzioni Python in codice macchina nativo tramite JIT (Just-In-Time) compilation.

```python
import pandas as pd
import numpy as np
from numba import jit

# --- Funzione personalizzata compilata con Numba ---
@jit(nopython=True)
def calcola_media_mobile_esponenziale(valori: np.ndarray, alpha: float) -> np.ndarray:
    """EMA (Exponential Moving Average) implementata con Numba."""
    n = len(valori)
    risultato = np.empty(n)
    risultato[0] = valori[0]
    for i in range(1, n):
        risultato[i] = alpha * valori[i] + (1 - alpha) * risultato[i - 1]
    return risultato

# Applicazione alla colonna
df = pd.DataFrame({"prezzo": np.random.randn(1_000_000).cumsum() + 100})
df["ema_numba"] = calcola_media_mobile_esponenziale(df["prezzo"].values, alpha=0.1)

# --- Confronto con apply() Python puro ---
# apply() su 1M righe: ~10 secondi
# Numba su 1M righe: ~0.05 secondi (200x piu veloce)

# --- Numba con pandas .apply() (engine="numba") ---
# pandas supporta engine="numba" in alcune aggregazioni
risultato = df.groupby("gruppo")["valore"].transform("mean", engine="numba")

# --- Cython in pandas ---
# Alcune operazioni pandas utilizzano gia Cython internamente
# Per ottimizzazioni custom, usare Numba e generalmente piu semplice
```

---

## Elaborazione Dati in Streaming

Per dataset che superano la RAM disponibile o per flussi di dati continui, l'elaborazione in streaming consente di processare i dati incrementalmente con complessita di memoria O(1).

### Generator-Based Pipelines

I generatori Python sono lo strumento nativo per costruire pipeline di streaming. Ogni generatore produce elementi uno alla volta, senza caricare l'intero dataset in memoria.

```python
from typing import Iterator, Generator
import csv
from pathlib import Path

# --- Pipeline di generatori concatenati ---
def leggi_righe(file_path: str) -> Generator[dict, None, None]:
    """Legge un CSV riga per riga come dizionari."""
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for riga in reader:
            yield riga

def filtra_validi(righe: Iterator[dict]) -> Generator[dict, None, None]:
    """Filtra righe con campi obbligatori presenti."""
    for riga in righe:
        if riga.get("id") and riga.get("valore"):
            yield riga

def trasforma(righe: Iterator[dict]) -> Generator[dict, None, None]:
    """Trasforma ciascuna riga."""
    for riga in righe:
        riga["valore"] = float(riga["valore"])
        riga["nome"] = riga.get("nome", "").strip().title()
        yield riga

def scrivi_output(righe: Iterator[dict], output_path: str) -> int:
    """Scrive le righe trasformate su file. Restituisce il conteggio."""
    conteggio = 0
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = None
        for riga in righe:
            if writer is None:
                writer = csv.DictWriter(f, fieldnames=riga.keys())
                writer.writeheader()
            writer.writerow(riga)
            conteggio += 1
    return conteggio

# Composizione della pipeline — nessun dato in memoria
pipeline = trasforma(filtra_validi(leggi_righe("input_grande.csv")))
n = scrivi_output(pipeline, "output_pulito.csv")
print(f"Elaborate {n} righe con memoria costante")
```

### itertools per Streaming Avanzato

```python
import itertools
from typing import Iterator, TypeVar

T = TypeVar("T")

# --- Chunking con itertools ---
def chunked(iterable: Iterator[T], size: int) -> Iterator[list[T]]:
    """Divide un iteratore in blocchi di dimensione fissa."""
    it = iter(iterable)
    while True:
        chunk = list(itertools.islice(it, size))
        if not chunk:
            break
        yield chunk

# Elaborazione a blocchi con pandas
import pandas as pd

def processa_csv_streaming(
    file_path: str,
    chunk_size: int = 50_000,
) -> pd.DataFrame:
    """Processa un CSV enorme a blocchi, aggregando i risultati."""
    aggregati = []
    for i, chunk_df in enumerate(pd.read_csv(file_path, chunksize=chunk_size)):
        # Ogni chunk e un DataFrame pandas di dimensione controllata
        agg = chunk_df.groupby("categoria")["valore"].agg(["sum", "count"])
        aggregati.append(agg)
        print(f"Blocco {i}: {len(chunk_df)} righe elaborate")

    # Combinazione dei risultati parziali
    risultato = pd.concat(aggregati).groupby(level=0).sum()
    risultato["media"] = risultato["sum"] / risultato["count"]
    return risultato

# Python 3.12+: itertools.batched()
# from itertools import batched
# for batch in batched(range(100), 10):
#     print(batch)  # tuple di 10 elementi
```

### Async Generators per I/O Concorrente

Quando la pipeline include operazioni di I/O (lettura da API, database, file di rete), i generatori asincroni combinano streaming e concorrenza:

```python
import asyncio
import aiohttp
from typing import AsyncGenerator

async def fetch_pagine(
    url_base: str,
    n_pagine: int
) -> AsyncGenerator[list[dict], None]:
    """Scarica pagine da un'API in modo asincrono e le produce in streaming."""
    async with aiohttp.ClientSession() as session:
        for pagina in range(1, n_pagine + 1):
            async with session.get(f"{url_base}?page={pagina}") as resp:
                dati = await resp.json()
                yield dati.get("results", [])

async def pipeline_async():
    """Pipeline asincrona: fetch → filtra → accumula."""
    risultati = []
    async for batch in fetch_pagine("https://api.example.com/dati", n_pagine=50):
        # Filtra e trasforma ciascun batch
        validi = [r for r in batch if r.get("attivo")]
        risultati.extend(validi)
    return risultati

# Esecuzione
# dati = asyncio.run(pipeline_async())
```

---

## Elaborazione Memory-Efficient

Quando le risorse di memoria sono limitate, diverse tecniche permettono di elaborare dataset di grandi dimensioni senza saturare la RAM.

### Memory-Mapped Files

I file mappati in memoria (mmap) consentono al sistema operativo di gestire automaticamente quali porzioni del file risiedono in RAM, permettendo di accedere a file piu grandi della memoria disponibile:

```python
import numpy as np

# --- NumPy memory-mapped arrays ---
# Creazione di un file memory-mapped
arr_mmap = np.memmap(
    "dati_grandi.dat",
    dtype="float64",
    mode="w+",          # lettura/scrittura
    shape=(10_000_000, 5)
)

# Scrittura dei dati (il sistema operativo gestisce il flush su disco)
arr_mmap[:1000] = np.random.randn(1000, 5)
arr_mmap.flush()

# Lettura parziale — solo le righe necessarie risiedono in RAM
arr_lettura = np.memmap("dati_grandi.dat", dtype="float64", mode="r", shape=(10_000_000, 5))
subset = arr_lettura[5000:6000]  # accede solo a 1000 righe
print(f"Media: {subset.mean():.4f}")

# --- PyArrow con memory mapping ---
import pyarrow.parquet as pq

# Lettura Parquet con memory mapping (zero-copy)
tabella = pq.read_table("dati.parquet", memory_map=True)
```

### Gestione della Memoria con gc e tracemalloc

```python
import gc
import tracemalloc
import pandas as pd

# --- Monitorare l'uso della memoria ---
tracemalloc.start()

df = pd.read_csv("dati.csv")
snapshot1 = tracemalloc.take_snapshot()

df_trasformato = df.groupby("categoria").agg({"valore": "sum"})
snapshot2 = tracemalloc.take_snapshot()

# Confronto tra snapshot
stats = snapshot2.compare_to(snapshot1, "lineno")
for stat in stats[:5]:
    print(stat)

tracemalloc.stop()

# --- Rilascio esplicito della memoria ---
def processa_e_rilascia(file_path: str) -> pd.DataFrame:
    """Carica, elabora e rilascia la memoria del DataFrame intermedio."""
    df_raw = pd.read_csv(file_path)
    risultato = df_raw.groupby("categoria")["valore"].sum().reset_index()

    # Rilascia esplicitamente il DataFrame grande
    del df_raw
    gc.collect()  # forza il garbage collector

    return risultato

# --- Pattern: elaborazione sequenziale con rilascio ---
def processa_file_multipli(file_paths: list[str]) -> pd.DataFrame:
    """Elabora file uno alla volta, rilasciando la memoria dopo ciascuno."""
    risultati = []
    for path in file_paths:
        df = pd.read_csv(path)
        agg = df.groupby("regione")["ricavo"].sum()
        risultati.append(agg)
        del df
        gc.collect()

    return pd.concat(risultati).groupby(level=0).sum().reset_index()
```

### Generatori come Pipeline ETL Memory-Efficient

```python
from typing import Generator
import json

def leggi_jsonl_streaming(file_path: str) -> Generator[dict, None, None]:
    """Legge un file JSONL (una riga JSON per linea) in streaming."""
    with open(file_path, "r", encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            if linea:
                yield json.loads(linea)

def batch_to_dataframe(
    records: Generator[dict, None, None],
    batch_size: int = 10_000
) -> Generator["pd.DataFrame", None, None]:
    """Converte un flusso di record in DataFrame a batch."""
    import pandas as pd

    batch = []
    for record in records:
        batch.append(record)
        if len(batch) >= batch_size:
            yield pd.DataFrame(batch)
            batch = []
    if batch:
        yield pd.DataFrame(batch)

# Pipeline: file JSONL → batch DataFrame → trasformazione → output Parquet
import pandas as pd

records = leggi_jsonl_streaming("eventi.jsonl")
for i, df_batch in enumerate(batch_to_dataframe(records, batch_size=50_000)):
    # Trasforma ogni batch
    df_batch["timestamp"] = pd.to_datetime(df_batch["timestamp"])
    df_batch = df_batch[df_batch["tipo_evento"] != "debug"]

    # Salva ogni batch come file Parquet separato
    df_batch.to_parquet(f"output/batch_{i:04d}.parquet", index=False)
    print(f"Batch {i}: {len(df_batch)} righe salvate")
```

---

## Validazione Dati Avanzata

La sezione precedente ha introdotto Pydantic, pandera e Great Expectations con esempi base. Qui approfondiamo pattern avanzati di validazione per pipeline di produzione.

### pandera SchemaModel (Class-Based API)

La class-based API di pandera sfrutta i type hints di Python per definire schemi di validazione in modo piu idiomatico e compatibile con gli IDE:

```python
import pandera as pa
from pandera.typing import Series, DataFrame
import pandas as pd

class SchemaVendite(pa.DataFrameModel):
    """Schema di validazione per il DataFrame vendite."""

    id_ordine: Series[int] = pa.Field(gt=0, unique=True)
    prodotto: Series[str] = pa.Field(isin=["Widget A", "Widget B", "Widget C"])
    quantita: Series[int] = pa.Field(ge=1, le=10000)
    prezzo_unitario: Series[float] = pa.Field(gt=0, le=99999.99)
    data_ordine: Series[pa.DateTime]
    regione: Series[str] = pa.Field(str_length={"min_value": 2, "max_value": 50})
    sconto: Series[float] = pa.Field(ge=0, le=1.0, nullable=True, coerce=True)

    class Config:
        strict = True           # rifiuta colonne extra non definite nello schema
        coerce = True           # converti automaticamente i tipi
        ordered = False         # l'ordine delle colonne non conta

    # Check cross-colonna
    @pa.check("prezzo_unitario", name="prezzo_coerente_con_prodotto")
    def prezzo_nel_range_prodotto(cls, prezzo: Series[float]) -> Series[bool]:
        return prezzo < 1000  # nessun prodotto puo costare piu di 1000

    # Check a livello di DataFrame
    @pa.dataframe_check
    def ricavo_positivo(cls, df: pd.DataFrame) -> Series[bool]:
        return (df["quantita"] * df["prezzo_unitario"]) > 0

# Utilizzo
@pa.check_types
def processa_vendite(df: DataFrame[SchemaVendite]) -> pd.DataFrame:
    """La validazione avviene automaticamente all'ingresso della funzione."""
    return df.assign(
        ricavo_totale=df["quantita"] * df["prezzo_unitario"]
    )

# Il decorator @check_types valida il DataFrame prima di eseguire la funzione
# Se la validazione fallisce, solleva pa.errors.SchemaError
```

### pandera con Polars

A partire dalla versione 0.19, pandera supporta nativamente i DataFrame Polars:

```python
import pandera.polars as pa
import polars as pl

class SchemaOrdini(pa.DataFrameModel):
    """Schema pandera per DataFrame Polars."""

    id: int = pa.Field(gt=0)
    prodotto: str = pa.Field()
    valore: float = pa.Field(ge=0)

    class Config:
        strict = True

# Validazione di un DataFrame Polars
df = pl.DataFrame({
    "id": [1, 2, 3],
    "prodotto": ["A", "B", "C"],
    "valore": [10.0, 20.0, 30.0],
})

try:
    df_validato = SchemaOrdini.validate(df)
    print("Validazione Polars superata")
except pa.errors.SchemaError as e:
    print(f"Errore: {e}")
```

### Great Expectations — Pattern Avanzati

Great Expectations opera con il concetto di *Expectation Suite*: una collezione di aspettative (regole di validazione) applicate a un *Batch* di dati. In produzione, le suite vengono salvate come file JSON e riutilizzate nei checkpoint della pipeline.

```python
import great_expectations as gx
import pandas as pd

# --- Creazione di un contesto GE ---
context = gx.get_context()

# --- Definizione di una Expectation Suite ---
suite = context.add_expectation_suite("suite_vendite")

# Aspettative strutturali
suite.add_expectation(
    gx.expectations.ExpectColumnToExist(column="id_ordine")
)
suite.add_expectation(
    gx.expectations.ExpectTableRowCountToBeBetween(min_value=100, max_value=10_000_000)
)

# Aspettative sui valori
suite.add_expectation(
    gx.expectations.ExpectColumnValuesToBeUnique(column="id_ordine")
)
suite.add_expectation(
    gx.expectations.ExpectColumnValuesToNotBeNull(column="id_ordine")
)
suite.add_expectation(
    gx.expectations.ExpectColumnValuesToBeBetween(
        column="quantita", min_value=1, max_value=100000
    )
)
suite.add_expectation(
    gx.expectations.ExpectColumnValuesToBeInSet(
        column="regione",
        value_set=["Nord", "Sud", "Centro", "Isole", "Nord-Est", "Nord-Ovest"]
    )
)

# Aspettative statistiche
suite.add_expectation(
    gx.expectations.ExpectColumnMeanToBeBetween(
        column="prezzo_unitario", min_value=1.0, max_value=500.0
    )
)
```

### Pattern: Validazione a Strati nella Pipeline

```python
import pandera as pa
import pandas as pd
from typing import Callable

# Schema per ciascuna fase della pipeline
schema_raw = pa.DataFrameSchema({
    "id": pa.Column(int, pa.Check.gt(0)),
    "nome": pa.Column(str),
    "valore": pa.Column(float),
})

schema_pulito = pa.DataFrameSchema({
    "id": pa.Column(int, pa.Check.gt(0), unique=True),
    "nome": pa.Column(str, pa.Check.str_length(min_value=1)),
    "valore": pa.Column(float, pa.Check.gt(0)),
    "nome_normalizzato": pa.Column(str),
})

schema_finale = pa.DataFrameSchema({
    "id": pa.Column(int, pa.Check.gt(0), unique=True),
    "nome_normalizzato": pa.Column(str),
    "valore": pa.Column(float, pa.Check.gt(0)),
    "categoria_valore": pa.Column(str, pa.Check.isin(["basso", "medio", "alto"])),
})

def con_validazione(
    schema_input: pa.DataFrameSchema,
    schema_output: pa.DataFrameSchema,
) -> Callable:
    """Decoratore che valida input e output di una funzione di trasformazione."""
    def decorator(func: Callable) -> Callable:
        def wrapper(df: pd.DataFrame) -> pd.DataFrame:
            schema_input.validate(df)         # validazione input
            risultato = func(df)
            schema_output.validate(risultato)  # validazione output
            return risultato
        return wrapper
    return decorator

@con_validazione(schema_raw, schema_pulito)
def pulisci(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop_duplicates(subset=["id"])
    df = df[df["valore"] > 0]
    df["nome_normalizzato"] = df["nome"].str.strip().str.title()
    return df
```

---

## Pattern ETL Avanzati

Oltre al pattern ETL base illustrato nelle sezioni precedenti, le pipeline di produzione richiedono pattern piu sofisticati per gestire idempotenza, caricamenti incrementali e quarantena degli errori.

### Idempotenza

Una pipeline idempotente produce lo stesso risultato indipendentemente dal numero di esecuzioni. Questo e critico per pipeline schedulate che possono fallire e necessitano di ri-esecuzione.

```python
import pandas as pd
from pathlib import Path
import hashlib
import json

def calcola_hash_file(file_path: str) -> str:
    """Calcola l'hash SHA-256 di un file per verificare se e cambiato."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def pipeline_idempotente(
    input_path: str,
    output_path: str,
    state_file: str = ".pipeline_state.json",
) -> bool:
    """Pipeline che non ri-elabora file gia processati."""
    # Carica lo stato precedente
    state_path = Path(state_file)
    stato = json.loads(state_path.read_text()) if state_path.exists() else {}

    # Verifica se il file e cambiato
    hash_corrente = calcola_hash_file(input_path)
    if stato.get(input_path) == hash_corrente:
        print(f"File {input_path} gia elaborato — skip")
        return False

    # Elaborazione
    df = pd.read_csv(input_path)
    df = df.drop_duplicates()
    df.to_parquet(output_path, index=False)

    # Salva lo stato
    stato[input_path] = hash_corrente
    state_path.write_text(json.dumps(stato, indent=2))
    print(f"Elaborato {input_path} → {output_path}")
    return True
```

### Caricamento Incrementale

Il caricamento incrementale elabora solo i dati nuovi o modificati dall'ultima esecuzione, riducendo drasticamente tempi di elaborazione e costi:

```python
import pandas as pd
from datetime import datetime

def caricamento_incrementale(
    sorgente_path: str,
    destinazione_path: str,
    colonna_timestamp: str = "updated_at",
    last_run_file: str = ".last_run",
) -> pd.DataFrame:
    """Carica solo i record modificati dopo l'ultima esecuzione."""
    from pathlib import Path

    # Determina il timestamp dell'ultima esecuzione
    last_run_path = Path(last_run_file)
    if last_run_path.exists():
        last_run = pd.Timestamp(last_run_path.read_text().strip())
    else:
        last_run = pd.Timestamp("1970-01-01")

    now = pd.Timestamp.now()

    # Legge solo i record nuovi/modificati
    df = pd.read_parquet(sorgente_path)
    df[colonna_timestamp] = pd.to_datetime(df[colonna_timestamp])
    df_nuovi = df[df[colonna_timestamp] > last_run]

    if df_nuovi.empty:
        print("Nessun nuovo dato da caricare")
        return df_nuovi

    # Merge con i dati esistenti (upsert)
    dest_path = Path(destinazione_path)
    if dest_path.exists():
        df_esistente = pd.read_parquet(destinazione_path)
        # Upsert: rimuove vecchi record con lo stesso ID, aggiunge i nuovi
        id_nuovi = set(df_nuovi["id"])
        df_esistente = df_esistente[~df_esistente["id"].isin(id_nuovi)]
        df_finale = pd.concat([df_esistente, df_nuovi], ignore_index=True)
    else:
        df_finale = df_nuovi

    df_finale.to_parquet(destinazione_path, index=False)

    # Aggiorna il timestamp dell'ultima esecuzione
    last_run_path.write_text(now.isoformat())
    print(f"Caricati {len(df_nuovi)} nuovi record")
    return df_nuovi
```

### Quarantena degli Errori

In pipeline di produzione, le righe con errori non devono bloccare l'elaborazione delle righe valide. Il pattern *quarantena* separa i dati validi dai dati problematici per analisi successiva:

```python
import pandas as pd
from dataclasses import dataclass, field
from typing import Callable

@dataclass
class RisultatoValidazione:
    """Risultato della validazione con dati validi e in quarantena."""
    validi: pd.DataFrame
    quarantena: pd.DataFrame
    statistiche: dict = field(default_factory=dict)

def valida_con_quarantena(
    df: pd.DataFrame,
    regole: list[tuple[str, Callable[[pd.DataFrame], pd.Series]]],
) -> RisultatoValidazione:
    """Applica regole di validazione e separa righe valide da invalide."""
    mask_valida = pd.Series(True, index=df.index)
    motivi_errore = pd.Series("", index=df.index)

    for nome_regola, check_fn in regole:
        risultato_check = check_fn(df)
        invalide = ~risultato_check
        mask_valida &= risultato_check

        # Registra il motivo dell'errore
        motivi_errore[invalide] += f"{nome_regola}; "

    df_quarantena = df[~mask_valida].copy()
    df_quarantena["motivo_quarantena"] = motivi_errore[~mask_valida].str.rstrip("; ")

    return RisultatoValidazione(
        validi=df[mask_valida].copy(),
        quarantena=df_quarantena,
        statistiche={
            "totali": len(df),
            "validi": mask_valida.sum(),
            "quarantena": (~mask_valida).sum(),
            "tasso_errore": f"{(~mask_valida).mean() * 100:.1f}%",
        },
    )

# Utilizzo
regole = [
    ("id_positivo", lambda df: df["id"] > 0),
    ("prezzo_valido", lambda df: df["prezzo"].between(0.01, 99999)),
    ("nome_presente", lambda df: df["nome"].str.len() > 0),
    ("email_valida", lambda df: df["email"].str.contains("@", na=False)),
]

risultato = valida_con_quarantena(df_input, regole)
print(f"Statistiche: {risultato.statistiche}")

# Salva dati validi per la pipeline
risultato.validi.to_parquet("dati_validi.parquet")

# Salva quarantena per analisi manuale
risultato.quarantena.to_csv("quarantena.csv", index=False)
```

---

## Orchestrazione di Pipeline — Fondamenti

Per pipeline di produzione che devono essere schedulate, monitorate e gestite, gli orchestratori forniscono infrastruttura per scheduling, retry, logging, lineage e alerting. I due orchestratori Python piu diffusi sono Prefect e Dagster.

### Prefect — Panoramica

Prefect trasforma funzioni Python ordinarie in task osservabili con decoratori. Il focus e sulla resilienza: retry automatici, gestione dei fallimenti, caching dei risultati.

```python
from prefect import flow, task
from prefect.tasks import task_input_hash
import pandas as pd

@task(retries=3, retry_delay_seconds=60, log_prints=True)
def estrai_dati(percorso: str) -> pd.DataFrame:
    """Task di estrazione con retry automatico."""
    print(f"Lettura da {percorso}")
    return pd.read_csv(percorso)

@task(log_prints=True)
def trasforma_dati(df: pd.DataFrame) -> pd.DataFrame:
    """Task di trasformazione."""
    df = df.drop_duplicates()
    df["nome"] = df["nome"].str.strip().str.title()
    print(f"Trasformate {len(df)} righe")
    return df

@task(
    cache_key_fn=task_input_hash,
    cache_expiration=pd.Timedelta(hours=1),
    log_prints=True,
)
def carica_dati(df: pd.DataFrame, destinazione: str) -> None:
    """Task di caricamento con caching (non ri-esegue se input invariato)."""
    df.to_parquet(destinazione, index=False)
    print(f"Salvate {len(df)} righe in {destinazione}")

@flow(name="ETL Vendite", log_prints=True)
def pipeline_vendite(input_path: str, output_path: str):
    """Flow principale: orchestrazione dei task."""
    dati = estrai_dati(input_path)
    dati_trasformati = trasforma_dati(dati)
    carica_dati(dati_trasformati, output_path)

# Esecuzione locale
# pipeline_vendite("vendite_raw.csv", "vendite_clean.parquet")

# Esecuzione schedulata (richiede Prefect server)
# from prefect.deployments import Deployment
# deployment = Deployment.build_from_flow(
#     flow=pipeline_vendite,
#     name="vendite-giornaliero",
#     schedule={"cron": "0 6 * * *"},  # ogni giorno alle 06:00
# )
```

### Dagster — Panoramica

Dagster adotta un approccio *asset-centric*: invece di definire task, si definiscono *asset* (materializazioni di dati) con le loro dipendenze, lineage e metadati.

```python
from dagster import asset, Definitions, MaterializeResult, MetadataValue
import pandas as pd

@asset(description="Dati grezzi delle vendite dal CSV sorgente")
def vendite_raw() -> pd.DataFrame:
    """Asset: dati grezzi estratti dalla sorgente."""
    df = pd.read_csv("dati/vendite.csv")
    return df

@asset(description="Vendite pulite e validate")
def vendite_pulite(vendite_raw: pd.DataFrame) -> pd.DataFrame:
    """Asset: dati puliti (dipende da vendite_raw)."""
    df = vendite_raw.drop_duplicates()
    df = df.dropna(subset=["id_ordine", "prodotto"])
    df["nome_prodotto"] = df["prodotto"].str.strip().str.title()
    return df

@asset(description="Report aggregato per regione")
def report_regionale(vendite_pulite: pd.DataFrame) -> MaterializeResult:
    """Asset: report aggregato con metadati."""
    report = (
        vendite_pulite
        .groupby("regione")
        .agg(
            ordini=("id_ordine", "count"),
            ricavo_totale=("ricavo", "sum"),
        )
        .reset_index()
    )
    report.to_parquet("output/report_regionale.parquet")

    return MaterializeResult(
        metadata={
            "n_regioni": MetadataValue.int(len(report)),
            "ricavo_totale": MetadataValue.float(report["ricavo_totale"].sum()),
            "preview": MetadataValue.md(report.head().to_markdown()),
        }
    )

# Registrazione degli asset
defs = Definitions(assets=[vendite_raw, vendite_pulite, report_regionale])

# Esecuzione: dagster dev (avvia la UI web)
# oppure: dagster asset materialize --select vendite_raw vendite_pulite report_regionale
```

### Confronto Orchestratori

| Caratteristica | Prefect | Dagster | Airflow |
|---|---|---|---|
| Paradigma | Task-centric (imperative) | Asset-centric (dichiarativo) | DAG di task (imperative) |
| Modello mentale | "esegui questi step in ordine" | "materializza questi dati" | "esegui questo DAG" |
| Retry/resilienza | Eccellente (built-in) | Buono | Buono |
| Lineage dati | Basico | Nativo (data lineage completo) | Plugin-based |
| UI web | Si (Prefect Cloud/Server) | Si (Dagit, molto informativa) | Si (Airflow UI) |
| Testing | Facile (funzioni Python) | Eccellente (test unitari nativi) | Complesso |
| Curva di apprendimento | Bassa | Media | Alta |
| Scheduling | Cron, intervalli, eventi | Cron, sensori, schedule | Cron, trigger |
| Casi d'uso ideali | Workflow dinamici, ML ops | Data platform, analytics, governance | Infrastruttura legacy, team grandi |

---

## Metriche di Qualita dei Dati

La qualita dei dati non e un concetto binario: va misurata, monitorata e tracciata nel tempo. Un framework di metriche strutturato consente di rilevare degradazioni prima che impattino i consumatori a valle.

### Le Sei Dimensioni della Qualita

Le sei dimensioni standard (definite da DAMA International) sono:

| Dimensione | Definizione | Metrica esempio |
|---|---|---|
| **Completezza** | % di valori non nulli | `df.notna().mean()` per colonna |
| **Unicita** | assenza di duplicati | `1 - df.duplicated().mean()` |
| **Validita** | conformita a regole di business | righe che superano pandera / totale |
| **Accuratezza** | corrispondenza con il mondo reale | richiede ground truth esterna |
| **Consistenza** | uniformita tra sorgenti | confronto hash tra sistemi |
| **Tempestivita** | freschezza dei dati | `now() - max(timestamp_aggiornamento)` |

### Implementazione di un Profiler di Qualita

```python
import pandas as pd
from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass
class ReportQualita:
    """Report strutturato sulla qualita di un DataFrame."""
    nome_dataset: str
    timestamp: str
    n_righe: int
    n_colonne: int
    completezza: dict[str, float]
    unicita: float
    tipi_mismatch: dict[str, str]
    statistiche_numeriche: dict[str, dict]

def profila_qualita(
    df: pd.DataFrame,
    nome: str,
    colonne_chiave: list[str] | None = None,
) -> ReportQualita:
    """Genera un profilo di qualita completo per il DataFrame."""
    # Completezza per colonna (0.0 = tutto nullo, 1.0 = tutto presente)
    completezza = {
        col: round(df[col].notna().mean(), 4)
        for col in df.columns
    }

    # Unicita basata sulle colonne chiave
    if colonne_chiave:
        duplicati = df.duplicated(subset=colonne_chiave).mean()
    else:
        duplicati = df.duplicated().mean()

    # Rileva colonne dove il dtype inferito differisce dal contenuto
    tipi_mismatch = {}
    for col in df.select_dtypes(include=["object"]).columns:
        campione = df[col].dropna().head(100)
        if campione.str.isnumeric().all():
            tipi_mismatch[col] = "contiene numeri ma dtype=object"

    # Statistiche numeriche
    stat_num = {}
    for col in df.select_dtypes(include=["number"]).columns:
        serie = df[col].dropna()
        stat_num[col] = {
            "media": round(serie.mean(), 4),
            "mediana": round(serie.median(), 4),
            "std": round(serie.std(), 4),
            "min": serie.min(),
            "max": serie.max(),
            "skewness": round(serie.skew(), 4),
            "pct_zero": round((serie == 0).mean(), 4),
        }

    return ReportQualita(
        nome_dataset=nome,
        timestamp=datetime.now(timezone.utc).isoformat(),
        n_righe=len(df),
        n_colonne=len(df.columns),
        completezza=completezza,
        unicita=round(1 - duplicati, 4),
        tipi_mismatch=tipi_mismatch,
        statistiche_numeriche=stat_num,
    )

# Utilizzo
report = profila_qualita(df, "vendite_q1", colonne_chiave=["id_ordine"])
print(f"Completezza colonna 'email': {report.completezza.get('email', 'N/A')}")
print(f"Unicita: {report.unicita * 100:.1f}%")
```

### Monitoraggio della Qualita nel Tempo

Per rilevare *data drift* e degradazioni progressive, il pattern consigliato e salvare le metriche storicamente:

```python
import json
from pathlib import Path

def salva_metrica_qualita(
    report: ReportQualita,
    percorso_storico: str = "qualita_storico.jsonl",
) -> None:
    """Appende il report come riga JSONL per analisi storica."""
    record = {
        "dataset": report.nome_dataset,
        "timestamp": report.timestamp,
        "n_righe": report.n_righe,
        "completezza_media": round(
            sum(report.completezza.values()) / len(report.completezza), 4
        ),
        "unicita": report.unicita,
        "n_tipi_mismatch": len(report.tipi_mismatch),
    }
    with open(percorso_storico, "a") as f:
        f.write(json.dumps(record) + "\n")

def rileva_anomalie_qualita(
    percorso_storico: str = "qualita_storico.jsonl",
    soglia_completezza: float = 0.05,
) -> list[str]:
    """Confronta l'ultimo report con la media storica e segnala anomalie."""
    records = []
    with open(percorso_storico) as f:
        for riga in f:
            records.append(json.loads(riga))

    if len(records) < 2:
        return []

    ultimo = records[-1]
    storici = records[:-1]
    media_completezza = sum(r["completezza_media"] for r in storici) / len(storici)

    avvisi = []
    if ultimo["completezza_media"] < media_completezza - soglia_completezza:
        avvisi.append(
            f"WARN: completezza {ultimo['completezza_media']:.3f} "
            f"sotto media storica {media_completezza:.3f}"
        )
    if ultimo["n_righe"] < min(r["n_righe"] for r in storici) * 0.5:
        avvisi.append(
            f"WARN: n_righe {ultimo['n_righe']} sotto il 50% del minimo storico"
        )
    return avvisi
```

---

## Logging e Osservabilita nelle Pipeline

Pipeline di produzione richiedono logging strutturato per debugging, audit e monitoraggio. Il modulo `logging` della libreria standard, configurato con formato strutturato, e la base.

### Logging Strutturato per Pipeline

```python
import logging
import json
import sys
from datetime import datetime, timezone
from functools import wraps
from typing import Callable

class StructuredFormatter(logging.Formatter):
    """Formatter che emette log in formato JSON strutturato."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Aggiungi campi extra se presenti
        if hasattr(record, "pipeline"):
            log_entry["pipeline"] = record.pipeline
        if hasattr(record, "fase"):
            log_entry["fase"] = record.fase
        if hasattr(record, "righe"):
            log_entry["righe"] = record.righe
        return json.dumps(log_entry, ensure_ascii=False)

def configura_logging_pipeline(nome_pipeline: str) -> logging.Logger:
    """Configura un logger strutturato per la pipeline."""
    logger = logging.getLogger(nome_pipeline)
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredFormatter())
    logger.addHandler(handler)
    return logger

def log_fase(fase: str) -> Callable:
    """Decoratore che logga ingresso/uscita di ogni fase della pipeline."""
    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger("pipeline")
            logger.info(
                f"Inizio fase: {fase}",
                extra={"fase": fase, "pipeline": "etl"},
            )
            try:
                risultato = fn(*args, **kwargs)
                n_righe = len(risultato) if hasattr(risultato, "__len__") else "N/A"
                logger.info(
                    f"Fine fase: {fase}",
                    extra={"fase": fase, "righe": n_righe, "pipeline": "etl"},
                )
                return risultato
            except Exception as e:
                logger.error(
                    f"Errore in fase {fase}: {type(e).__name__}",
                    extra={"fase": fase, "pipeline": "etl"},
                )
                raise
        return wrapper
    return decorator

# Utilizzo
@log_fase("pulizia")
def pulisci_dati(df):
    df = df.drop_duplicates()
    df = df.dropna(subset=["id"])
    return df

@log_fase("trasformazione")
def trasforma_dati(df):
    df = df.assign(importo_eur=df["importo"] * 0.92)
    return df
```

### Metriche di Esecuzione della Pipeline

```python
import time
import tracemalloc
from contextlib import contextmanager
from dataclasses import dataclass

@dataclass
class MetricaFase:
    """Metriche di esecuzione di una singola fase."""
    nome: str
    durata_secondi: float
    memoria_picco_mb: float
    righe_ingresso: int
    righe_uscita: int

    @property
    def tasso_filtro(self) -> float:
        """Percentuale di righe rimosse."""
        if self.righe_ingresso == 0:
            return 0.0
        return 1 - (self.righe_uscita / self.righe_ingresso)

@contextmanager
def misura_fase(nome: str, righe_ingresso: int = 0):
    """Context manager che misura tempo e memoria di una fase."""
    tracemalloc.start()
    inizio = time.perf_counter()

    risultato = {"righe_uscita": 0}
    yield risultato

    durata = time.perf_counter() - inizio
    _, picco = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    metrica = MetricaFase(
        nome=nome,
        durata_secondi=round(durata, 3),
        memoria_picco_mb=round(picco / 1024 / 1024, 2),
        righe_ingresso=righe_ingresso,
        righe_uscita=risultato["righe_uscita"],
    )
    print(
        f"[{metrica.nome}] "
        f"durata={metrica.durata_secondi}s "
        f"memoria_picco={metrica.memoria_picco_mb}MB "
        f"righe={metrica.righe_ingresso}->{metrica.righe_uscita} "
        f"filtro={metrica.tasso_filtro:.1%}"
    )

# Utilizzo
import pandas as pd

df = pd.read_csv("dati.csv")
with misura_fase("pulizia", righe_ingresso=len(df)) as m:
    df = df.drop_duplicates().dropna(subset=["id"])
    m["righe_uscita"] = len(df)
```

---

## DataFrame Tipizzati e Type Safety

Python 3.11+ e le type stub di pandas consentono di migliorare la type safety nel data processing, riducendo errori a runtime.

### pandas-stubs e Tipizzazione Statica

```python
# pyproject.toml — aggiungere pandas-stubs per mypy/pyright
# [tool.mypy]
# plugins = ["pandera.mypy"]

import pandas as pd

def processa_vendite(df: pd.DataFrame) -> pd.DataFrame:
    """Funzione con tipo di ritorno esplicito.

    Con pandas-stubs installato, mypy/pyright verificano
    che i metodi invocati esistano sul tipo DataFrame.
    """
    # Specifica i tipi al momento del caricamento
    dtypes = {
        "id": "int64",
        "prezzo": "float64",
        "categoria": "category",
        "data": "string",
    }
    df = df.astype(dtypes)
    return df.query("prezzo > 0")
```

### Pattern: Schema come Contratto tra Fasi

Un pattern comune nelle pipeline di produzione e definire lo schema atteso come un "contratto" tra fasi. Se una fase modifica lo schema, il contratto aggiornato documenta il cambiamento:

```python
from typing import TypedDict

class SchemaVenditeRaw(TypedDict):
    """Schema dei dati grezzi in ingresso."""
    id: int
    prodotto: str
    prezzo: float
    quantita: int
    data_ordine: str

class SchemaVenditePulite(TypedDict):
    """Schema dopo la fase di pulizia."""
    id: int
    prodotto: str
    prezzo: float
    quantita: int
    data_ordine: str  # ISO 8601 verificato
    importo_totale: float  # calcolato: prezzo * quantita

class SchemaVenditeArricchite(TypedDict):
    """Schema dopo arricchimento con dati esterni."""
    id: int
    prodotto: str
    prezzo: float
    quantita: int
    data_ordine: str
    importo_totale: float
    categoria: str  # da lookup esterno
    regione: str    # da geocoding

def verifica_schema(
    df: pd.DataFrame,
    colonne_attese: list[str],
    nome_fase: str,
) -> None:
    """Verifica che il DataFrame abbia le colonne attese."""
    mancanti = set(colonne_attese) - set(df.columns)
    extra = set(df.columns) - set(colonne_attese)
    if mancanti:
        raise ValueError(
            f"Fase '{nome_fase}': colonne mancanti: {mancanti}"
        )
    if extra:
        import logging
        logging.warning(
            f"Fase '{nome_fase}': colonne non previste: {extra}"
        )
```

Questo pattern e particolarmente utile quando la pipeline attraversa confini di team: lo schema serve come documentazione eseguibile delle aspettative di ciascuna fase.

---

## Confronto Sintetico degli Strumenti

Per orientare la scelta tecnologica in base al caso d'uso, questa tabella riassume le caratteristiche principali degli strumenti trattati in questo capitolo:

| Scenario | Strumento consigliato | Motivazione |
|---|---|---|
| Analisi esplorativa < 1GB | pandas | Ecosistema maturo, ricchissimo di funzionalita |
| Dataset 1-10GB, single machine | Polars | Lazy evaluation, performance nativa, basso consumo memoria |
| Query SQL su file locali | DuckDB | SQL standard, zero infrastruttura, lettura diretta Parquet |
| Elaborazione distribuita > 10GB | Dask / PySpark | Scalabilita orizzontale su cluster |
| Scambio dati tra sistemi | Apache Arrow / Parquet | Zero-copy, formato colonnare standard |
| Validazione dati in pipeline | pandera | Schema dichiarativo, integrato con pandas e Polars |
| Validazione con aspettative di business | Great Expectations | Suite di aspettative, checkpoint, data docs |
| Orchestrazione semplice | Prefect | Decoratori Python, retry nativi, bassa curva di apprendimento |
| Piattaforma dati con lineage | Dagster | Asset-centric, lineage completo, ottimo testing |
| Pipeline legacy enterprise | Airflow | Standard de facto, ampio ecosistema di operatori |

---

> **Nota finale:** il data processing e una disciplina che richiede tanto rigore tecnico quanto comprensione del dominio applicativo. Le librerie presentate in questa guida — pandas, NumPy, openpyxl, Pillow, Pydantic, pandera — costituiscono il toolkit fondamentale dello sviluppatore Python. La padronanza di questi strumenti, unita alla capacita di costruire pipeline modulari, validate e monitorate, e la base per affrontare qualsiasi sfida di elaborazione dati in ambito professionale.

---

## Esercizi

1. **Pipeline ETL completa** — Costruisci una pipeline ETL che: (a) estragga dati da 3 fonti diverse (CSV, JSON, Excel), (b) pulisca e normalizzi i dati (gestione NaN, conversione tipi, rimozione duplicati), (c) validi i dati con pandera o Pydantic, (d) trasformi e aggreghi per produrre un report, (e) esporti in formato Parquet e CSV. Ogni fase deve essere una funzione indipendente con logging del numero di righe in ingresso/uscita.

2. **Benchmark pandas vs Polars** — Genera un dataset sintetico di almeno 1 milione di righe con 10 colonne (mix di tipi: int, float, string, date). Implementa le stesse 5 operazioni (filtro, group_by, join, sort, aggregazione) sia in pandas che in Polars. Misura tempo e memoria con `time.perf_counter()` e `tracemalloc`. Presenta i risultati in una tabella comparativa e commenta quando preferire ciascuna libreria.

3. **Elaborazione batch di file Excel** — Scrivi uno script che processi una directory di file Excel (almeno 10 file): legga ogni file con openpyxl, estragga dati da sheet specifici, validi la struttura (colonne attese, tipi), consolidi tutto in un unico DataFrame pandas, e generi un report riassuntivo. Gestisci esplicitamente file corrotti o con struttura inattesa senza interrompere il batch.

4. **Data validation con pandera** — Definisci un `DataFrameSchema` pandera per un dataset reale (es. dati di vendita) che includa: vincoli su tipi di colonna, range di valori numerici, pattern regex per stringhe, check di unicita e check cross-colonna (es. data_fine > data_inizio). Scrivi test che verifichino sia la validazione corretta che il rilevamento di dati invalidi.

5. **Image processing pipeline con Pillow** — Costruisci una pipeline di elaborazione immagini che: (a) legga tutte le immagini da una directory, (b) ridimensioni mantenendo l'aspect ratio, (c) applichi watermark con testo configurabile, (d) ottimizzi per il web (compressione, conversione a WebP), (e) generi thumbnail. Usa `concurrent.futures.ThreadPoolExecutor` per parallelizzare l'elaborazione e misura lo speedup rispetto all'esecuzione sequenziale.

---

## Letture e Riferimenti

### Fonti primarie

- pandas Documentation — https://pandas.pydata.org/docs/ (consultato: 2026-05-24)
- NumPy Documentation — https://numpy.org/doc/stable/ (consultato: 2026-05-24)
- Polars Documentation — https://docs.pola.rs/ (consultato: 2026-05-24)
- openpyxl Documentation — https://openpyxl.readthedocs.io/ (consultato: 2026-05-24)
- Pillow (PIL Fork) Documentation — https://pillow.readthedocs.io/ (consultato: 2026-05-24)
- Pydantic Documentation — https://docs.pydantic.dev/ (consultato: 2026-05-24)
- pandera Documentation — https://pandera.readthedocs.io/ (consultato: 2026-05-24)
- DuckDB Documentation — https://duckdb.org/docs/ (consultato: 2026-05-24)
- pdfplumber Documentation — https://github.com/jsvine/pdfplumber (consultato: 2026-05-24)

### Libri consigliati

- *Python for Data Analysis, 3rd Edition* — Wes McKinney — O'Reilly, 2022
- *Effective Pandas* — Matt Harrison — 2021

---

## Riferimenti Incrociati

| Modulo | Relazione |
|---|---|
| [05 — Gestione File e I/O](05-gestione-file-io.md) | Lettura/scrittura file CSV, JSON, binari — input delle pipeline dati |
| [25 — Performance](25-performance.md) | Profiling e ottimizzazione di operazioni su dati (vectorization, Numba) |
| [08 — Concorrenza e Parallelismo](08-concorrenza.md) | Parallelizzazione di pipeline con ThreadPool/ProcessPool |
| [03 — Funzioni e Scope](03-funzioni-scope.md) | Funzioni pure per trasformazioni dati, composizione di pipeline |
| [22 — Clean Code](22-clean-code.md) | Codice modulare, naming, type hints nelle pipeline dati |
| [26 — Docker](26-docker-per-python.md) | Containerizzazione di pipeline dati per riproducibilita |

---

## Glossario

| Termine | Definizione |
|---|---|
| **DataFrame** | Struttura dati tabellare bidimensionale con righe e colonne etichettate, tipo fondamentale in pandas e Polars |
| **Series** | Struttura dati monodimensionale etichettata in pandas, equivalente a una singola colonna di un DataFrame |
| **Vectorization** | Tecnica che applica operazioni a interi array/colonne senza loop Python espliciti, sfruttando codice C/Rust sottostante |
| **ETL** | Extract, Transform, Load — pattern per pipeline di elaborazione dati che estrae da fonti, trasforma e carica in destinazione |
| **Parquet** | Formato di file colonnare, compresso e tipizzato, ottimale per storage e query analitiche su grandi dataset |
| **pandas** | Libreria Python per analisi e manipolazione di dati tabulari, basata su NumPy con supporto PyArrow |
| **Polars** | Libreria DataFrame ad alte prestazioni scritta in Rust con API Python, supporto lazy evaluation e parallelismo nativo |
| **NumPy** | Libreria fondamentale per calcolo numerico in Python, fornisce array N-dimensionali e operazioni vettorizzate |
| **pandera** | Libreria per la validazione di DataFrame tramite schemi dichiarativi con vincoli su tipi, range e relazioni |
| **DuckDB** | Database analitico in-process (embedded) ottimizzato per query OLAP, con integrazione nativa pandas/Polars |
| **Lazy Evaluation** | Strategia di esecuzione in cui le operazioni vengono registrate ma non eseguite fino alla chiamata esplicita di `.collect()` |
| **Method Chaining** | Stile di programmazione in cui metodi successivi vengono concatenati (`df.filter().groupby().agg()`) per leggibilita |
| **NaN** | Not a Number — valore speciale IEEE 754 usato per rappresentare dati mancanti in pandas e NumPy |
| **Downcast** | Conversione di un tipo numerico a una rappresentazione piu compatta (es. `int64` → `int32`) per ridurre la memoria |
