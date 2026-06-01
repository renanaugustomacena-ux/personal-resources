---
corso: "Programmazione Python"
fase: "3 — Librerie e Framework"
modulo: "12"
titolo: "Database con Python"
versione: "SQLAlchemy 2.0+ / Alembic 1.x / Pydantic 2.x"
livello: "Intermedio-Avanzato"
prerequisiti:
  - "01-06 — Python Base"
  - "02 — OOP"
  - "07 — Error Handling e Logging"
obiettivi:
  - "Padroneggiare SQLAlchemy 2.0 con il paradigma mapped_column e type-safe queries"
  - "Gestire migrazioni di schema con Alembic in modo sicuro e riproducibile"
  - "Implementare pattern Repository e Unit of Work"
  - "Utilizzare connection pooling, transazioni e gestione degli errori"
  - "Integrare database SQL e NoSQL in applicazioni Python"
  - "Ottimizzare query e prevenire problemi N+1"
tag: [database, SQLAlchemy, Alembic, ORM, PostgreSQL, SQLite, migrations, connection-pooling]
---

# Database con Python — Guida Completa

> **Modulo 12** · **Aggiornamento:** 2026-05-24 · **Versione:** SQLAlchemy 2.0+ / Alembic 1.x / Pydantic 2.x

> ### Obiettivi di apprendimento
>
> **Prerequisiti:** [Python Base](01-fondamenti-linguaggio.md), [OOP](02-oop.md), [Error Handling](07-error-handling-e-logging.md)
>
> Al termine di questo modulo saprai:
> 1. Padroneggiare SQLAlchemy 2.0 con `mapped_column` e query type-safe
> 2. Gestire migrazioni di schema con Alembic in modo sicuro e riproducibile
> 3. Implementare pattern Repository e Unit of Work per disaccoppiare la persistenza
> 4. Utilizzare connection pooling, transazioni e gestione degli errori DB
> 5. Integrare database SQL (PostgreSQL, SQLite) e NoSQL in applicazioni Python
> 6. Ottimizzare query e prevenire problemi N+1 con eager loading
>
> **Tempo stimato:** 8-10 ore · **Livello:** Intermedio-Avanzato

---

### Frontmatter

| Campo | Valore |
|-------|--------|
| **Corso** | Programmazione Python |
| **Fase** | 3 — Persistenza e accesso ai dati |
| **Versione doc** | 2.0 |
| **Livello** | Intermedio → Avanzato |
| **Prerequisiti** | Modulo 05 (classi), Modulo 10 (asyncio), Modulo 11 (web framework) |

**Obiettivi di apprendimento:**

1. Progettare modelli ORM con SQLAlchemy 2.0 (`DeclarativeBase`, `Mapped[T]`, `mapped_column()`) e gestire relazioni one-to-many, many-to-many, one-to-one.
2. Implementare accesso asincrono al database con `create_async_engine`, `AsyncSession` e `async_sessionmaker` per applicazioni FastAPI.
3. Gestire il ciclo di vita dello schema con Alembic: auto-generation, migrazioni dati, downgrade, configurazione async di `env.py`.
4. Applicare il Repository Pattern con dependency injection per separare logica di business e persistenza.
5. Diagnosticare e risolvere il problema N+1, scegliere le strategie di loading (`selectinload`, `joinedload`, `subqueryload`, `raiseload`) e leggere piani di esecuzione con `EXPLAIN ANALYZE`.
6. Integrare Pydantic v2 con SQLAlchemy per validazione, serializzazione e `model_validate` da oggetti ORM.
7. Configurare connection pooling, transaction management, indici e sicurezza delle connessioni per ambienti di produzione.

---

## Idee guida
1. **SQLAlchemy 2.0 syntax: `Mapped`, `mapped_column`.**
2. **Async (`asyncpg` + `SQLAlchemy[asyncio]`) per FastAPI.**
3. **Alembic per migrations.** Single source of truth.
4. **Connection pooling: PgBouncer transaction mode + SQLAlchemy `pool_pre_ping=True`.**

---

## Mappa concettuale — Layer ORM

```
                         ┌─────────────┐
                         │  Applicazione│
                         │  (Repository)│
                         └──────┬──────┘
                                │ model_validate() / to_dict()
                         ┌──────▼──────┐
                         │   Pydantic   │
                         │  Schema v2   │
                         └──────┬──────┘
                                │
                         ┌──────▼──────┐
                         │   Session /  │
                         │ AsyncSession │ ← Unit of Work + Identity Map
                         └──────┬──────┘
                                │ select() / insert() / update()
                         ┌──────▼──────┐
                         │    Query     │
                         │  (select())  │ ← SQL Expression Language
                         └──────┬──────┘
                                │ compila SQL
                         ┌──────▼──────┐
                         │   Engine /   │
                         │ AsyncEngine  │ ← Dialect (psycopg, asyncpg, sqlite)
                         └──────┬──────┘
                                │
                         ┌──────▼──────┐
                         │    Pool      │
                         │ (QueuePool)  │ ← pool_size, max_overflow, pool_pre_ping
                         └──────┬──────┘
                                │ connessione TCP / socket
                         ┌──────▼──────┐
                         │  Database    │
                         │ (PostgreSQL) │
                         └─────────────┘
```

**Flusso di una query ORM:**
1. L'applicazione chiama `session.scalars(select(Utente).where(...))`.
2. La `Session` verifica l'identity map per oggetti gia caricati.
3. Il costrutto `select()` viene compilato in SQL dal dialect appropriato.
4. L'`Engine` richiede una connessione al `Pool`.
5. Il `Pool` restituisce una connessione esistente (o ne crea una nuova fino a `max_overflow`).
6. Il risultato ritorna attraverso gli stessi layer; la `Session` popola l'identity map.

---

## Indice

1. [Panoramica](#panoramica)
2. [SQLite](#sqlite)
3. [PostgreSQL](#postgresql)
4. [MySQL](#mysql)
5. [SQLAlchemy](#sqlalchemy)
6. [Alembic (Migrazioni)](#alembic-migrazioni)
7. [Redis](#redis)
8. [MongoDB](#mongodb)
9. [Pattern e Best Practices](#pattern-e-best-practices)
10. [Best Practices](#best-practices)
11. [SQLAlchemy 2.0 — Approfondimento](#sqlalchemy-20--approfondimento)
12. [Async SQLAlchemy — Approfondimento](#async-sqlalchemy--approfondimento)
13. [Alembic — Approfondimento](#alembic--approfondimento)
14. [Repository Pattern — Approfondimento](#repository-pattern--approfondimento)
15. [Query Avanzate — CTE, Window Functions, Subquery](#query-avanzate--cte-window-functions-subquery)
16. [Loading Strategies — Approfondimento](#loading-strategies--approfondimento)
17. [Connection Pooling — Approfondimento](#connection-pooling--approfondimento)
18. [Transaction Management — Approfondimento](#transaction-management--approfondimento)
19. [Pydantic v2 e SQLAlchemy — Integrazione](#pydantic-v2-e-sqlalchemy--integrazione)
20. [SQLite vs PostgreSQL — Strategia di Migrazione](#sqlite-vs-postgresql--strategia-di-migrazione)
21. [Database Testing](#database-testing)
22. [Migrazioni — Best Practices Avanzate](#migrazioni--best-practices-avanzate)
23. [Performance — EXPLAIN ANALYZE e Indici](#performance--explain-analyze-e-indici)
24. [Sicurezza Database](#sicurezza-database)
25. [Troubleshooting](#troubleshooting)
26. [FAQ](#faq)
27. [Esercizi](#esercizi)
28. [Letture e Riferimenti](#letture-e-riferimenti)
29. [Cross-link](#cross-link)
30. [Glossario](#glossario)

---

## Panoramica

La programmazione con database rappresenta una competenza fondamentale per qualsiasi sviluppatore Python. Che si tratti di un'applicazione web, di un servizio backend o di uno script di analisi dati, la capacità di interagire con sistemi di persistenza è indispensabile.

### Tipologie di Database

I database si dividono principalmente in due grandi famiglie:

**Database relazionali (SQL):** organizzano i dati in tabelle con righe e colonne, rispettando uno schema rigido. Supportano transazioni ACID (Atomicità, Consistenza, Isolamento, Durabilità) e utilizzano il linguaggio SQL per le interrogazioni. Esempi principali sono SQLite, PostgreSQL e MySQL.

**Database NoSQL:** adottano modelli di dati flessibili e non impongono uno schema fisso. Si suddividono ulteriormente in:

- **Document store** (MongoDB): memorizzano documenti JSON/BSON
- **Key-value store** (Redis): associano chiavi a valori arbitrari
- **Column-family** (Cassandra): organizzano i dati in colonne anziché righe
- **Graph database** (Neo4j): modellano relazioni tra entità come grafi

### DB-API 2.0 (PEP 249)

Python definisce uno standard per l'interfacciamento con i database relazionali attraverso la PEP 249 (DB-API 2.0). Questa specifica garantisce un'interfaccia coerente tra i vari driver, stabilendo concetti comuni come `Connection`, `Cursor`, metodi `execute()`, `fetchone()`, `fetchall()` e la gestione delle transazioni. Ciò significa che una volta appreso il pattern di base con un database, il passaggio a un altro risulta agevole.

### ORM vs Raw SQL

Esistono due approcci principali per interagire con i database:

- **Raw SQL:** si scrivono direttamente le query SQL, ottenendo pieno controllo sulle interrogazioni e sulle prestazioni. È l'approccio ideale per query complesse o quando si necessita di ottimizzazione fine. Lo sviluppatore ha piena visibilità su ciò che viene eseguito e può sfruttare funzionalità specifiche del database in uso.
- **ORM (Object-Relational Mapping):** mappa le tabelle del database su classi Python, consentendo di operare con oggetti anziché con stringhe SQL. Offre produttività maggiore e astrazione dal database sottostante, al costo di una minore flessibilità in scenari avanzati.

La scelta tra i due approcci non è necessariamente esclusiva: molti progetti adottano un approccio ibrido, utilizzando l'ORM per le operazioni CRUD standard e le query SQL dirette per le interrogazioni complesse o le ottimizzazioni critiche. SQLAlchemy, ad esempio, supporta entrambi gli approcci all'interno dello stesso progetto, permettendo di passare dall'uno all'altro in modo trasparente.

---

## SQLite

SQLite è un database relazionale leggero, serverless e self-contained, integrato direttamente nella libreria standard di Python tramite il modulo `sqlite3`. Non richiede alcuna installazione aggiuntiva ed è perfetto per prototipi, applicazioni embedded, test e piccoli progetti.

### Installazione e Caratteristiche

SQLite non necessita di installazione separata poiché il modulo `sqlite3` è incluso nella libreria standard di Python. Il database risiede in un singolo file su disco (o in memoria), il che lo rende estremamente portabile. Supporta la maggior parte dello standard SQL-92, include il supporto per le transazioni ACID e gestisce accessi concorrenti multipli in lettura (la scrittura è serializzata tramite lock). La dimensione massima di un database SQLite è di 281 terabyte, rendendolo adatto anche a dataset di medie dimensioni.

### Connessione e Operazioni di Base

```python
import sqlite3

# Connessione al database (crea il file se non esiste)
conn = sqlite3.connect("mio_database.db")

# Creazione del cursore per eseguire le query
cursor = conn.cursor()

# Creazione di una tabella
cursor.execute("""
    CREATE TABLE IF NOT EXISTS utenti (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        eta INTEGER,
        data_registrazione TEXT DEFAULT CURRENT_TIMESTAMP
    )
""")

# Inserimento di un record
cursor.execute(
    "INSERT INTO utenti (nome, email, eta) VALUES (?, ?, ?)",
    ("Mario Rossi", "mario@esempio.it", 30)
)

# Conferma delle modifiche
conn.commit()

# Lettura dei dati con fetchall
cursor.execute("SELECT * FROM utenti")
tutti_gli_utenti = cursor.fetchall()
for utente in tutti_gli_utenti:
    print(utente)  # Tuple: (1, 'Mario Rossi', 'mario@esempio.it', 30, '2026-03-27 ...')

# Lettura di un singolo record con fetchone
cursor.execute("SELECT * FROM utenti WHERE id = ?", (1,))
singolo_utente = cursor.fetchone()
print(singolo_utente)

# Chiusura della connessione
conn.close()
```

### Query Parametrizzate (Prevenzione SQL Injection)

Non concatenare mai stringhe direttamente nelle query SQL. L'uso di parametri è fondamentale per la sicurezza.

```python
# SBAGLIATO — vulnerabile a SQL injection
nome_utente = "Mario'; DROP TABLE utenti; --"
cursor.execute(f"SELECT * FROM utenti WHERE nome = '{nome_utente}'")

# CORRETTO — query parametrizzata con segnaposto ?
cursor.execute("SELECT * FROM utenti WHERE nome = ?", (nome_utente,))

# CORRETTO — parametri nominali
cursor.execute(
    "SELECT * FROM utenti WHERE nome = :nome AND eta > :eta",
    {"nome": "Mario Rossi", "eta": 25}
)

# Inserimento multiplo con executemany
utenti_nuovi = [
    ("Lucia Bianchi", "lucia@esempio.it", 28),
    ("Paolo Verdi", "paolo@esempio.it", 35),
    ("Anna Neri", "anna@esempio.it", 42),
]
cursor.executemany(
    "INSERT INTO utenti (nome, email, eta) VALUES (?, ?, ?)",
    utenti_nuovi
)
conn.commit()
```

### Transazioni (commit, rollback)

SQLite supporta le transazioni per garantire l'integrità dei dati. Per impostazione predefinita, `sqlite3` opera in modalità auto-commit disattivata, raggruppando le operazioni in transazioni implicite.

```python
conn = sqlite3.connect("mio_database.db")
cursor = conn.cursor()

try:
    cursor.execute("UPDATE conti SET saldo = saldo - 100 WHERE id = ?", (1,))
    cursor.execute("UPDATE conti SET saldo = saldo + 100 WHERE id = ?", (2,))

    # Se entrambe le operazioni riescono, conferma la transazione
    conn.commit()
    print("Trasferimento completato con successo")
except sqlite3.Error as e:
    # In caso di errore, annulla tutte le modifiche
    conn.rollback()
    print(f"Errore durante il trasferimento: {e}")
finally:
    conn.close()
```

### Context Manager

Il modo più sicuro e pulito per gestire le connessioni è tramite il context manager, che garantisce la chiusura automatica delle risorse e la gestione delle transazioni.

```python
import sqlite3

# Il context manager gestisce commit/rollback automaticamente
with sqlite3.connect("mio_database.db") as conn:
    cursor = conn.cursor()
    cursor.execute("INSERT INTO utenti (nome, email, eta) VALUES (?, ?, ?)",
                   ("Giulia Ferrara", "giulia@esempio.it", 26))
    # conn.commit() viene chiamato automaticamente se non ci sono eccezioni
    # conn.rollback() viene chiamato in caso di eccezione

# NOTA: il context manager di sqlite3 NON chiude la connessione
# Per chiuderla esplicitamente:
conn.close()

# Pattern completo con chiusura della connessione
def esegui_query(database: str, query: str, parametri: tuple = ()):
    """Esegue una query con gestione completa delle risorse."""
    with sqlite3.connect(database) as conn:
        cursor = conn.cursor()
        cursor.execute(query, parametri)
        return cursor.fetchall()
```

### Database In-Memory

SQLite consente di creare database interamente in memoria, ideali per i test e per operazioni temporanee ad alte prestazioni.

```python
# Database in memoria — esiste solo durante la connessione
conn = sqlite3.connect(":memory:")
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE prodotti (
        id INTEGER PRIMARY KEY,
        nome TEXT,
        prezzo REAL
    )
""")

cursor.executemany(
    "INSERT INTO prodotti (nome, prezzo) VALUES (?, ?)",
    [("Laptop", 999.99), ("Mouse", 29.99), ("Tastiera", 79.99)]
)

cursor.execute("SELECT * FROM prodotti WHERE prezzo > ?", (50.0,))
print(cursor.fetchall())

conn.close()  # Il database viene distrutto
```

### Row Factory (sqlite3.Row)

Per impostazione predefinita, `fetchall()` restituisce tuple. Utilizzando `sqlite3.Row` si ottiene un accesso ai dati simile a un dizionario, molto più leggibile.

```python
conn = sqlite3.connect("mio_database.db")
conn.row_factory = sqlite3.Row  # Imposta la factory per righe

cursor = conn.cursor()
cursor.execute("SELECT * FROM utenti")

for riga in cursor.fetchall():
    # Accesso per nome della colonna
    print(f"Nome: {riga['nome']}, Email: {riga['email']}, Età: {riga['eta']}")

    # Accesso anche per indice
    print(f"ID: {riga[0]}")

    # Conversione a dizionario
    dizionario = dict(riga)
    print(dizionario)

conn.close()
```

---

## PostgreSQL

PostgreSQL è il database relazionale open-source più avanzato, ampiamente utilizzato in applicazioni di produzione per la sua robustezza, scalabilità e ricchezza di funzionalità (tipi JSON, full-text search, estensioni come PostGIS).

### psycopg2 e psycopg3

Esistono due librerie principali per interfacciarsi con PostgreSQL da Python:

- **psycopg2:** la libreria storica, stabile e matura, basata su `libpq` in C
- **psycopg3 (psycopg):** la nuova generazione, completamente riscritta in Python con supporto nativo per async

#### Installazione

```bash
# psycopg2
pip install psycopg2-binary  # versione precompilata

# psycopg3
pip install psycopg[binary]
pip install psycopg[pool]     # per il connection pooling
```

#### Connessione e Query con psycopg2

```python
import psycopg2
from psycopg2.extras import RealDictCursor

# Connessione al database
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    dbname="mio_db",
    user="utente",
    password="password"
)

# Cursore con risultati come dizionari
cursor = conn.cursor(cursor_factory=RealDictCursor)

# Creazione tabella
cursor.execute("""
    CREATE TABLE IF NOT EXISTS articoli (
        id SERIAL PRIMARY KEY,
        titolo VARCHAR(200) NOT NULL,
        contenuto TEXT,
        autore_id INTEGER REFERENCES utenti(id),
        pubblicato BOOLEAN DEFAULT FALSE,
        creato_il TIMESTAMP DEFAULT NOW()
    )
""")

# Query parametrizzate (usa %s come segnaposto, NON i ? di SQLite)
cursor.execute(
    "INSERT INTO articoli (titolo, contenuto, autore_id) VALUES (%s, %s, %s) RETURNING id",
    ("Il mio primo articolo", "Contenuto dell'articolo...", 1)
)
nuovo_id = cursor.fetchone()["id"]
print(f"Articolo creato con ID: {nuovo_id}")

conn.commit()

# Lettura
cursor.execute("SELECT * FROM articoli WHERE pubblicato = %s", (True,))
articoli = cursor.fetchall()
for art in articoli:
    print(f"{art['titolo']} — {art['creato_il']}")

cursor.close()
conn.close()
```

#### Connessione e Query con psycopg3

```python
import psycopg
from psycopg.rows import dict_row

# Context manager per la connessione
with psycopg.connect(
    "host=localhost port=5432 dbname=mio_db user=utente password=password",
    row_factory=dict_row
) as conn:
    # Autocommit disattivato per impostazione predefinita
    with conn.cursor() as cur:
        cur.execute(
            "SELECT * FROM articoli WHERE autore_id = %s ORDER BY creato_il DESC",
            (1,)
        )
        for riga in cur:
            print(riga["titolo"])

    # Il commit è automatico all'uscita dal context manager se non ci sono errori
```

### Connection Pooling (psycopg_pool)

Il connection pooling è essenziale in produzione per evitare il costo di apertura/chiusura delle connessioni ad ogni richiesta.

```python
from psycopg_pool import ConnectionPool

# Creazione del pool con un minimo e un massimo di connessioni
pool = ConnectionPool(
    conninfo="host=localhost dbname=mio_db user=utente password=password",
    min_size=5,
    max_size=20,
    max_idle=300,  # secondi prima di chiudere connessioni inattive
)

# Utilizzo di una connessione dal pool
with pool.connection() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM articoli")
        conteggio = cur.fetchone()[0]
        print(f"Totale articoli: {conteggio}")
# La connessione viene restituita al pool automaticamente

# Chiusura del pool (alla fine dell'applicazione)
pool.close()
```

### COPY per Operazioni Bulk

Il comando `COPY` di PostgreSQL è il metodo più efficiente per caricare grandi quantità di dati.

```python
import psycopg

with psycopg.connect("host=localhost dbname=mio_db user=utente") as conn:
    with conn.cursor() as cur:
        # COPY IN — caricamento dati da Python a PostgreSQL
        with cur.copy("COPY prodotti (nome, prezzo, categoria) FROM STDIN") as copy:
            for nome, prezzo, categoria in dati_prodotti:
                copy.write_row((nome, prezzo, categoria))

        # COPY OUT — scaricamento dati da PostgreSQL a Python
        with cur.copy("COPY prodotti TO STDOUT") as copy:
            for riga in copy.rows():
                print(riga)

    conn.commit()
```

### NOTIFY/LISTEN

PostgreSQL offre un meccanismo di notifiche asincrone tra connessioni tramite `NOTIFY` e `LISTEN`, utile per implementare sistemi di eventi in tempo reale.

```python
import psycopg

# Listener — attende notifiche
with psycopg.connect("host=localhost dbname=mio_db", autocommit=True) as conn:
    conn.execute("LISTEN canale_ordini")

    print("In attesa di notifiche...")
    for notifica in conn.notifies():
        print(f"Canale: {notifica.channel}")
        print(f"Payload: {notifica.payload}")
        if notifica.payload == "stop":
            break

# Da un'altra connessione — invio notifica
with psycopg.connect("host=localhost dbname=mio_db", autocommit=True) as conn:
    conn.execute("NOTIFY canale_ordini, 'nuovo_ordine:12345'")
```

### Async con psycopg3

psycopg3 offre supporto nativo per la programmazione asincrona, fondamentale per applicazioni ad alta concorrenza.

```python
import asyncio
import psycopg
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

async def main():
    # Pool di connessioni asincrono
    async with AsyncConnectionPool(
        conninfo="host=localhost dbname=mio_db user=utente",
        min_size=2,
        max_size=10,
    ) as pool:
        async with pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute("SELECT * FROM articoli LIMIT 10")
                articoli = await cur.fetchall()
                for art in articoli:
                    print(art["titolo"])

asyncio.run(main())
```

---

## MySQL

MySQL è uno dei database relazionali più diffusi, particolarmente utilizzato nel mondo web (stack LAMP). Python offre diversi driver per l'interfacciamento.

### mysql-connector-python e PyMySQL

```bash
# Driver ufficiale Oracle
pip install mysql-connector-python

# Driver puro Python (alternativa popolare)
pip install PyMySQL
```

#### Connessione e Query con mysql-connector-python

```python
import mysql.connector
from mysql.connector import pooling

# Connessione semplice
config = {
    "host": "localhost",
    "port": 3306,
    "user": "utente",
    "password": "password",
    "database": "mio_db",
    "charset": "utf8mb4",
}

conn = mysql.connector.connect(**config)
cursor = conn.cursor(dictionary=True)  # Risultati come dizionari

# Creazione tabella
cursor.execute("""
    CREATE TABLE IF NOT EXISTS clienti (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nome VARCHAR(100) NOT NULL,
        email VARCHAR(150) UNIQUE,
        citta VARCHAR(100),
        creato_il DATETIME DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
""")

# Inserimento con parametri (usa %s come PostgreSQL)
cursor.execute(
    "INSERT INTO clienti (nome, email, citta) VALUES (%s, %s, %s)",
    ("Franco Colombo", "franco@esempio.it", "Milano")
)
conn.commit()

# Lettura
cursor.execute("SELECT * FROM clienti WHERE citta = %s", ("Milano",))
for cliente in cursor.fetchall():
    print(f"{cliente['nome']} — {cliente['email']}")

cursor.close()
conn.close()
```

#### Connection Pooling con MySQL

```python
from mysql.connector import pooling

# Creazione del pool
pool = pooling.MySQLConnectionPool(
    pool_name="mio_pool",
    pool_size=10,
    pool_reset_session=True,
    **config
)

# Ottenere una connessione dal pool
conn = pool.get_connection()
cursor = conn.cursor(dictionary=True)

cursor.execute("SELECT * FROM clienti")
clienti = cursor.fetchall()

cursor.close()
conn.close()  # Restituisce la connessione al pool
```

#### PyMySQL

```python
import pymysql

conn = pymysql.connect(
    host="localhost",
    user="utente",
    password="password",
    database="mio_db",
    charset="utf8mb4",
    cursorclass=pymysql.cursors.DictCursor,
)

with conn:
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM clienti WHERE citta = %s", ("Roma",))
        risultati = cursor.fetchall()
        for riga in risultati:
            print(riga)
    conn.commit()
```

---

## SQLAlchemy

SQLAlchemy è la libreria Python di riferimento per l'interazione con database relazionali. Offre due livelli di astrazione: **Core** (SQL Expression Language) e **ORM** (Object-Relational Mapping). Dalla versione 2.0, l'API è stata significativamente modernizzata con supporto completo per i type hints.

```bash
pip install sqlalchemy
pip install sqlalchemy[asyncio]  # per il supporto async
```

### Core

Il layer Core di SQLAlchemy fornisce un'astrazione SQL che consente di costruire query in modo programmatico, senza scrivere stringhe SQL, mantenendo il pieno controllo sulla generazione delle interrogazioni.

#### Engine, Connection e MetaData

```python
from sqlalchemy import create_engine, MetaData, text

# Creazione dell'engine — punto di accesso al database
engine = create_engine(
    "sqlite:///mio_database.db",
    echo=True,   # Stampa le query SQL generate (utile per il debug)
    pool_size=5,  # Dimensione del connection pool (non applicabile a SQLite)
    max_overflow=10,
)

# Stringhe di connessione per altri database:
# PostgreSQL: "postgresql+psycopg://utente:password@localhost:5432/mio_db"
# MySQL:      "mysql+pymysql://utente:password@localhost:3306/mio_db"

# MetaData — contenitore per le definizioni delle tabelle
metadata = MetaData()

# Esecuzione di una query raw con l'engine
with engine.connect() as conn:
    risultato = conn.execute(text("SELECT 1"))
    print(risultato.scalar())
    conn.commit()
```

#### Definizione delle Tabelle e Tipi di Colonna

```python
from sqlalchemy import (
    Table, Column, Integer, String, Float, Boolean,
    DateTime, Text, ForeignKey, UniqueConstraint, Index
)
from datetime import datetime

metadata = MetaData()

utenti = Table(
    "utenti", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("nome", String(100), nullable=False),
    Column("email", String(150), nullable=False, unique=True),
    Column("eta", Integer),
    Column("attivo", Boolean, default=True),
    Column("creato_il", DateTime, default=datetime.utcnow),
)

articoli = Table(
    "articoli", metadata,
    Column("id", Integer, primary_key=True),
    Column("titolo", String(200), nullable=False),
    Column("contenuto", Text),
    Column("autore_id", Integer, ForeignKey("utenti.id"), nullable=False),
    Column("pubblicato", Boolean, default=False),
    Column("creato_il", DateTime, default=datetime.utcnow),
    # Indice composto
    Index("idx_autore_pubblicato", "autore_id", "pubblicato"),
)

# Creazione di tutte le tabelle nel database
metadata.create_all(engine)
```

#### Select, Insert, Update, Delete (SQL Expression Language)

```python
from sqlalchemy import select, insert, update, delete, func

with engine.connect() as conn:
    # INSERT
    stmt = insert(utenti).values(nome="Elena Ricci", email="elena@esempio.it", eta=29)
    risultato = conn.execute(stmt)
    print(f"ID inserito: {risultato.inserted_primary_key[0]}")

    # INSERT multiplo
    conn.execute(
        insert(utenti),
        [
            {"nome": "Luca Bianchi", "email": "luca@esempio.it", "eta": 34},
            {"nome": "Sara Verdi", "email": "sara@esempio.it", "eta": 27},
        ]
    )

    # SELECT
    stmt = select(utenti).where(utenti.c.eta > 25).order_by(utenti.c.nome)
    risultato = conn.execute(stmt)
    for riga in risultato:
        print(f"{riga.nome} — {riga.email}")

    # UPDATE
    stmt = update(utenti).where(utenti.c.id == 1).values(eta=31)
    conn.execute(stmt)

    # DELETE
    stmt = delete(utenti).where(utenti.c.attivo == False)
    risultato = conn.execute(stmt)
    print(f"Righe eliminate: {risultato.rowcount}")

    conn.commit()
```

#### Joins, Aggregazioni e Subquery

```python
from sqlalchemy import select, func, and_, or_

with engine.connect() as conn:
    # JOIN
    stmt = (
        select(utenti.c.nome, articoli.c.titolo, articoli.c.creato_il)
        .join(articoli, utenti.c.id == articoli.c.autore_id)
        .where(articoli.c.pubblicato == True)
        .order_by(articoli.c.creato_il.desc())
    )
    for riga in conn.execute(stmt):
        print(f"{riga.nome}: {riga.titolo}")

    # Aggregazioni
    stmt = (
        select(
            utenti.c.nome,
            func.count(articoli.c.id).label("totale_articoli"),
            func.max(articoli.c.creato_il).label("ultimo_articolo"),
        )
        .join(articoli, utenti.c.id == articoli.c.autore_id)
        .group_by(utenti.c.nome)
        .having(func.count(articoli.c.id) > 2)
    )

    # Subquery
    subq = (
        select(articoli.c.autore_id, func.count().label("num_articoli"))
        .group_by(articoli.c.autore_id)
        .subquery()
    )

    stmt = (
        select(utenti.c.nome, subq.c.num_articoli)
        .join(subq, utenti.c.id == subq.c.autore_id)
        .where(subq.c.num_articoli > 5)
    )
    for riga in conn.execute(stmt):
        print(f"{riga.nome}: {riga.num_articoli} articoli")
```

### ORM

L'ORM di SQLAlchemy mappa le tabelle del database su classi Python, rendendo le operazioni sui dati naturali e orientate agli oggetti.

#### Declarative Mapping (SQLAlchemy 2.0+)

```python
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, ForeignKey, func
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, mapped_column, relationship
)

# Classe base per tutti i modelli
class Base(DeclarativeBase):
    pass

class Utente(Base):
    __tablename__ = "utenti"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(150), unique=True)
    eta: Mapped[Optional[int]] = mapped_column(default=None)
    attivo: Mapped[bool] = mapped_column(default=True)
    creato_il: Mapped[datetime] = mapped_column(server_default=func.now())

    # Relazione one-to-many: un utente ha molti articoli
    articoli: Mapped[List["Articolo"]] = relationship(
        back_populates="autore",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Utente(id={self.id}, nome='{self.nome}')>"

class Articolo(Base):
    __tablename__ = "articoli"

    id: Mapped[int] = mapped_column(primary_key=True)
    titolo: Mapped[str] = mapped_column(String(200))
    contenuto: Mapped[Optional[str]] = mapped_column(Text, default=None)
    autore_id: Mapped[int] = mapped_column(ForeignKey("utenti.id"))
    pubblicato: Mapped[bool] = mapped_column(default=False)
    creato_il: Mapped[datetime] = mapped_column(server_default=func.now())

    # Lato inverso della relazione
    autore: Mapped["Utente"] = relationship(back_populates="articoli")

    # Relazione many-to-many con i tag
    tags: Mapped[List["Tag"]] = relationship(
        secondary="articoli_tags",
        back_populates="articoli"
    )

# Tabella di associazione per many-to-many
from sqlalchemy import Table, Column, Integer
articoli_tags = Table(
    "articoli_tags", Base.metadata,
    Column("articolo_id", Integer, ForeignKey("articoli.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
)

class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(50), unique=True)

    articoli: Mapped[List["Articolo"]] = relationship(
        secondary="articoli_tags",
        back_populates="tags"
    )
```

#### Relazioni: one-to-many, many-to-many, one-to-one

```python
# ONE-TO-ONE — un utente ha un solo profilo
class Profilo(Base):
    __tablename__ = "profili"

    id: Mapped[int] = mapped_column(primary_key=True)
    bio: Mapped[Optional[str]] = mapped_column(Text)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(300))
    utente_id: Mapped[int] = mapped_column(ForeignKey("utenti.id"), unique=True)

    utente: Mapped["Utente"] = relationship(back_populates="profilo")

# Aggiungere al modello Utente:
# profilo: Mapped[Optional["Profilo"]] = relationship(
#     back_populates="utente", uselist=False
# )
```

#### Session (add, commit, rollback, flush)

La `Session` è il punto di interfaccia principale dell'ORM per le operazioni sul database. Gestisce le transazioni e il ciclo di vita degli oggetti.

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

engine = create_engine("sqlite:///mio_database.db")
Base.metadata.create_all(engine)

# Creazione e utilizzo della sessione
with Session(engine) as session:
    # Creazione di un nuovo utente
    nuovo_utente = Utente(nome="Marco Polo", email="marco@esempio.it", eta=33)
    session.add(nuovo_utente)

    # flush() invia le modifiche al database ma NON conferma la transazione
    session.flush()
    print(f"ID assegnato (prima del commit): {nuovo_utente.id}")

    # Aggiunta di un articolo collegato all'utente
    articolo = Articolo(
        titolo="Viaggio in Oriente",
        contenuto="Resoconto del viaggio...",
        autore=nuovo_utente,  # assegna la relazione
    )
    session.add(articolo)

    try:
        session.commit()
        print("Transazione confermata")
    except Exception as e:
        session.rollback()
        print(f"Errore, rollback eseguito: {e}")
```

#### Querying (select, where, join, order_by, group_by, limit)

```python
from sqlalchemy import select, func

with Session(engine) as session:
    # Select semplice
    stmt = select(Utente).where(Utente.attivo == True)
    utenti = session.scalars(stmt).all()

    # Filtri combinati
    stmt = (
        select(Utente)
        .where(Utente.eta >= 25, Utente.eta <= 40)
        .order_by(Utente.nome.asc())
        .limit(10)
        .offset(0)
    )
    utenti_paginati = session.scalars(stmt).all()

    # Join e aggregazione
    stmt = (
        select(Utente.nome, func.count(Articolo.id).label("num_articoli"))
        .join(Articolo, Utente.id == Articolo.autore_id)
        .group_by(Utente.nome)
        .having(func.count(Articolo.id) > 0)
        .order_by(func.count(Articolo.id).desc())
    )
    for nome, num in session.execute(stmt):
        print(f"{nome}: {num} articoli")

    # Ricerca per chiave primaria
    utente = session.get(Utente, 1)

    # Primo risultato o None
    stmt = select(Utente).where(Utente.email == "marco@esempio.it")
    utente = session.scalars(stmt).first()
```

#### Eager vs Lazy Loading

Il caricamento delle relazioni è un aspetto cruciale per le prestazioni. SQLAlchemy offre diverse strategie.

```python
from sqlalchemy.orm import joinedload, selectinload, subqueryload

with Session(engine) as session:
    # LAZY LOADING (predefinito) — carica la relazione al primo accesso
    # Può causare il problema N+1 se si accede alla relazione in un ciclo
    utente = session.get(Utente, 1)
    # Qui viene eseguita una seconda query per caricare gli articoli
    for art in utente.articoli:
        print(art.titolo)

    # JOINED LOAD — carica tutto con una singola JOIN
    stmt = (
        select(Utente)
        .options(joinedload(Utente.articoli))
        .where(Utente.id == 1)
    )
    utente = session.scalars(stmt).unique().first()
    # Nessuna query aggiuntiva necessaria
    for art in utente.articoli:
        print(art.titolo)

    # SELECT IN LOAD — una seconda query con clausola IN
    # Efficiente per caricare relazioni su molti oggetti
    stmt = (
        select(Utente)
        .options(selectinload(Utente.articoli))
        .where(Utente.attivo == True)
    )
    utenti = session.scalars(stmt).all()

    # SUBQUERY LOAD — una seconda query con subquery
    stmt = (
        select(Utente)
        .options(subqueryload(Utente.articoli))
    )
    utenti = session.scalars(stmt).all()
```

#### Eventi e Hooks

SQLAlchemy fornisce un sistema di eventi per intercettare operazioni specifiche.

```python
from sqlalchemy import event

# Evento prima dell'inserimento
@event.listens_for(Utente, "before_insert")
def prima_di_inserire_utente(mapper, connection, target):
    """Normalizza il nome prima dell'inserimento."""
    target.nome = target.nome.strip().title()

# Evento dopo l'aggiornamento
@event.listens_for(Utente, "after_update")
def dopo_aggiornamento_utente(mapper, connection, target):
    """Log delle modifiche all'utente."""
    print(f"Utente {target.id} aggiornato")

# Evento a livello di sessione
@event.listens_for(Session, "before_commit")
def prima_del_commit(session):
    """Validazione globale prima del commit."""
    for obj in session.new:
        if isinstance(obj, Articolo) and not obj.titolo:
            raise ValueError("L'articolo deve avere un titolo")
```

### Async SQLAlchemy (2.0+)

SQLAlchemy 2.0 offre supporto nativo per le operazioni asincrone, essenziale per framework come FastAPI e applicazioni ad alta concorrenza.

```python
import asyncio
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy import select

# Engine asincrono — richiede un driver async
async_engine = create_async_engine(
    "postgresql+asyncpg://utente:password@localhost/mio_db",
    echo=True,
)

# Session factory asincrona
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def crea_utente(nome: str, email: str) -> Utente:
    """Crea un nuovo utente in modo asincrono."""
    async with AsyncSessionLocal() as session:
        async with session.begin():
            utente = Utente(nome=nome, email=email)
            session.add(utente)
        # Il commit è automatico all'uscita da session.begin()
        return utente

async def ottieni_utenti_attivi() -> list[Utente]:
    """Recupera tutti gli utenti attivi."""
    async with AsyncSessionLocal() as session:
        stmt = (
            select(Utente)
            .where(Utente.attivo == True)
            .order_by(Utente.nome)
        )
        risultato = await session.scalars(stmt)
        return risultato.all()

async def main():
    # Creazione delle tabelle
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Operazioni
    utente = await crea_utente("Async User", "async@esempio.it")
    utenti = await ottieni_utenti_attivi()
    for u in utenti:
        print(u.nome)

    # Chiusura dell'engine
    await async_engine.dispose()

asyncio.run(main())
```

---

## Alembic (Migrazioni)

Alembic è lo strumento ufficiale per le migrazioni del database in progetti che utilizzano SQLAlchemy. Consente di versionare lo schema del database e applicare modifiche incrementali in modo controllato e reversibile.

### Installazione e Setup

```bash
pip install alembic

# Inizializzazione nella directory del progetto
alembic init alembic
```

Questo crea la seguente struttura:

```
progetto/
├── alembic/
│   ├── versions/          # Directory per i file di migrazione
│   ├── env.py             # Configurazione dell'ambiente
│   ├── script.py.mako     # Template per le migrazioni
│   └── README
└── alembic.ini            # File di configurazione principale
```

### Configurazione di env.py

Il file `env.py` va configurato per puntare ai modelli SQLAlchemy e alla connessione del database.

```python
# alembic/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Importa i modelli per l'autogenerate
from app.models import Base  # Importa la Base dei tuoi modelli

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# MetaData dei modelli per l'autogenerate
target_metadata = Base.metadata

def run_migrations_online() -> None:
    """Esegue le migrazioni in modalità online."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # Rileva cambiamenti nei tipi di colonna
        )

        with context.begin_transaction():
            context.run_migrations()

run_migrations_online()
```

Configurazione della stringa di connessione in `alembic.ini`:

```ini
# alembic.ini
[alembic]
script_location = alembic
sqlalchemy.url = postgresql+psycopg://utente:password@localhost/mio_db
```

### Creazione delle Migrazioni

```bash
# Generazione automatica basata sulle differenze tra modelli e database
alembic revision --autogenerate -m "creazione tabelle utenti e articoli"

# Migrazione manuale (file vuoto da compilare)
alembic revision -m "aggiunta colonna telefono a utenti"
```

Il file di migrazione generato automaticamente avrà un aspetto simile a:

```python
"""creazione tabelle utenti e articoli

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-03-27 10:30:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        "utenti",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("nome", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=150), nullable=False),
        sa.Column("eta", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

def downgrade() -> None:
    op.drop_table("utenti")
```

### Esecuzione delle Migrazioni

```bash
# Applica tutte le migrazioni pendenti
alembic upgrade head

# Applica fino a una revisione specifica
alembic upgrade a1b2c3d4e5f6

# Applica le prossime N migrazioni
alembic upgrade +2

# Visualizza lo stato corrente
alembic current

# Cronologia delle migrazioni
alembic history --verbose
```

### Downgrade

```bash
# Torna indietro di una migrazione
alembic downgrade -1

# Torna a una revisione specifica
alembic downgrade a1b2c3d4e5f6

# Annulla tutte le migrazioni
alembic downgrade base
```

### Best Practices per le Migrazioni

Quando si lavora con Alembic, è importante seguire alcune regole per mantenere le migrazioni affidabili e manutenibili. Ogni migrazione deve essere atomica e focalizzata su un singolo cambiamento logico. È fondamentale testare sia la funzione `upgrade()` che la funzione `downgrade()` per garantire la reversibilità completa. In ambienti con più sviluppatori, i conflitti tra migrazioni concorrenti vanno risolti con attenzione, utilizzando `alembic merge` per unire branch divergenti. Si raccomanda inoltre di non eliminare mai i file di migrazione già applicati in produzione, poiché la cronologia completa è necessaria per ricostruire lo schema da zero.

```python
# Migrazione con gestione dei dati esistenti
def upgrade() -> None:
    # Aggiunta di una nuova colonna con valore predefinito
    op.add_column("utenti", sa.Column("ruolo", sa.String(50), nullable=True))

    # Aggiornamento dei dati esistenti prima di rendere la colonna NOT NULL
    op.execute("UPDATE utenti SET ruolo = 'utente' WHERE ruolo IS NULL")

    # Ora rendi la colonna obbligatoria
    op.alter_column("utenti", "ruolo", nullable=False, server_default="utente")

def downgrade() -> None:
    op.drop_column("utenti", "ruolo")
```

---

## Redis

Redis è un database in-memory key-value estremamente veloce, utilizzato principalmente come cache, message broker e per la gestione di sessioni. Supporta strutture dati avanzate come liste, hash, set e sorted set.

```bash
pip install redis
```

### Connessione e Operazioni di Base

```python
import redis

# Connessione al server Redis
r = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=True,  # Restituisce stringhe invece di bytes
)

# Verifica della connessione
print(r.ping())  # True

# --- Stringhe ---
r.set("nome", "Mario Rossi")
r.set("contatore", 0)
print(r.get("nome"))       # "Mario Rossi"
r.incr("contatore")        # 1
r.incrby("contatore", 10)  # 11

# --- Liste ---
r.rpush("coda_lavori", "lavoro_1", "lavoro_2", "lavoro_3")
r.lpush("coda_lavori", "lavoro_urgente")
print(r.lrange("coda_lavori", 0, -1))  # Tutti gli elementi
lavoro = r.lpop("coda_lavori")          # Rimuove e restituisce il primo
print(r.llen("coda_lavori"))            # Lunghezza della lista

# --- Hash ---
r.hset("utente:1", mapping={
    "nome": "Elena Ricci",
    "email": "elena@esempio.it",
    "eta": "29",
})
print(r.hget("utente:1", "nome"))       # "Elena Ricci"
print(r.hgetall("utente:1"))            # Tutto l'hash come dizionario
r.hincrby("utente:1", "eta", 1)         # Incrementa l'età

# --- Set ---
r.sadd("tags:python", "web", "database", "async", "testing")
r.sadd("tags:javascript", "web", "frontend", "node")
print(r.smembers("tags:python"))                # Tutti i membri del set
print(r.sinter("tags:python", "tags:javascript"))  # Intersezione: {"web"}
print(r.sunion("tags:python", "tags:javascript"))   # Unione

# --- Sorted Set ---
r.zadd("classifica", {"alice": 100, "bob": 85, "charlie": 92})
r.zincrby("classifica", 15, "bob")         # bob ora ha 100
print(r.zrange("classifica", 0, -1, withscores=True))  # Ordinato per punteggio
print(r.zrevrange("classifica", 0, 2))     # Top 3 in ordine decrescente
```

### Expiry (TTL)

La possibilità di impostare una scadenza sulle chiavi è fondamentale per la gestione della cache.

```python
# Imposta una chiave con scadenza
r.setex("sessione:abc123", 3600, "dati_sessione")  # Scade dopo 1 ora
r.set("token_temp", "valore", ex=300)                # Scade dopo 5 minuti

# Controlla il tempo rimanente
print(r.ttl("sessione:abc123"))  # Secondi rimanenti

# Imposta scadenza su una chiave esistente
r.set("chiave_persistente", "valore")
r.expire("chiave_persistente", 600)  # Scade tra 10 minuti

# Rimuovi la scadenza (rendi la chiave persistente)
r.persist("chiave_persistente")
```

### Pub/Sub

Redis offre un sistema di messaggistica publish/subscribe per la comunicazione tra processi.

```python
import redis
import threading

r = redis.Redis(host="localhost", decode_responses=True)

# Subscriber (in un thread o processo separato)
def ascolta_messaggi():
    pubsub = r.pubsub()
    pubsub.subscribe("notifiche", "aggiornamenti")

    for messaggio in pubsub.listen():
        if messaggio["type"] == "message":
            print(f"Canale: {messaggio['channel']}, Dati: {messaggio['data']}")

thread = threading.Thread(target=ascolta_messaggi, daemon=True)
thread.start()

# Publisher
r.publish("notifiche", "Nuovo ordine ricevuto!")
r.publish("aggiornamenti", "Prezzo aggiornato per prodotto #42")
```

### Pipeline (Operazioni Batch)

Le pipeline raggruppano più comandi in una singola comunicazione con il server Redis, migliorando notevolmente le prestazioni.

```python
# Senza pipeline — ogni comando è una chiamata di rete separata
for i in range(1000):
    r.set(f"chiave:{i}", f"valore:{i}")

# Con pipeline — tutti i comandi in un'unica comunicazione
with r.pipeline() as pipe:
    for i in range(1000):
        pipe.set(f"chiave:{i}", f"valore:{i}")
    risultati = pipe.execute()  # Invia tutti i comandi insieme

# Pipeline con transazione atomica
with r.pipeline(transaction=True) as pipe:
    pipe.multi()
    pipe.set("saldo:1", 900)
    pipe.set("saldo:2", 1100)
    pipe.execute()
```

### Pattern di Caching

```python
import json
from functools import wraps

def cache_redis(ttl: int = 300):
    """Decoratore per il caching con Redis."""
    def decoratore(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Genera una chiave unica basata su funzione e argomenti
            chiave = f"cache:{func.__name__}:{hash((args, tuple(sorted(kwargs.items()))))}"

            # Prova a leggere dalla cache
            risultato_cache = r.get(chiave)
            if risultato_cache is not None:
                return json.loads(risultato_cache)

            # Esegui la funzione e salva il risultato in cache
            risultato = func(*args, **kwargs)
            r.setex(chiave, ttl, json.dumps(risultato))
            return risultato
        return wrapper
    return decoratore

@cache_redis(ttl=600)
def ottieni_dati_costosi(utente_id: int) -> dict:
    """Funzione con risultato cacheable."""
    # Simulazione di una query lenta
    return {"id": utente_id, "dati": "risultato costoso"}

# Pattern cache-aside
def ottieni_utente(utente_id: int) -> dict:
    chiave = f"utente:{utente_id}"

    # 1. Prova dalla cache
    dati = r.get(chiave)
    if dati:
        return json.loads(dati)

    # 2. Query al database
    utente = database.query_utente(utente_id)

    # 3. Salva in cache
    r.setex(chiave, 3600, json.dumps(utente))

    return utente
```

---

## MongoDB

MongoDB è il database NoSQL document-oriented più diffuso. Memorizza i dati come documenti BSON (una versione binaria di JSON), offrendo flessibilità nello schema e scalabilità orizzontale.

```bash
pip install pymongo
pip install motor  # driver asincrono
```

### pymongo — Operazioni di Base

```python
from pymongo import MongoClient
from bson import ObjectId

# Connessione
client = MongoClient("mongodb://localhost:27017/")

# Selezione del database e della collezione
db = client["mio_database"]
collezione_utenti = db["utenti"]
```

### CRUD Operations

```python
# --- CREATE ---
# Inserimento singolo
risultato = collezione_utenti.insert_one({
    "nome": "Roberto Mancini",
    "email": "roberto@esempio.it",
    "eta": 38,
    "interessi": ["calcio", "cucina", "viaggi"],
    "indirizzo": {
        "citta": "Roma",
        "cap": "00100",
    }
})
print(f"ID inserito: {risultato.inserted_id}")

# Inserimento multiplo
utenti_nuovi = [
    {"nome": "Laura Pausini", "email": "laura@esempio.it", "eta": 30},
    {"nome": "Andrea Bocelli", "email": "andrea@esempio.it", "eta": 45},
]
risultato = collezione_utenti.insert_many(utenti_nuovi)
print(f"ID inseriti: {risultato.inserted_ids}")

# --- READ ---
# Trova un documento
utente = collezione_utenti.find_one({"email": "roberto@esempio.it"})
print(utente)

# Trova per ID
utente = collezione_utenti.find_one({"_id": ObjectId("66a1b2c3d4e5f6a7b8c9d0e1")})

# Trova con filtri e proiezione
cursore = collezione_utenti.find(
    {"eta": {"$gte": 25, "$lte": 40}},      # Filtro
    {"nome": 1, "email": 1, "_id": 0}        # Proiezione (campi da includere)
).sort("nome", 1).limit(10)

for utente in cursore:
    print(utente)

# Operatori di query
# $gt, $gte, $lt, $lte, $ne, $in, $nin, $exists, $regex
collezione_utenti.find({"interessi": {"$in": ["calcio", "musica"]}})
collezione_utenti.find({"indirizzo.citta": "Roma"})  # Query su documenti annidati

# --- UPDATE ---
# Aggiorna un documento
collezione_utenti.update_one(
    {"email": "roberto@esempio.it"},
    {
        "$set": {"eta": 39, "verificato": True},
        "$push": {"interessi": "musica"},
    }
)

# Aggiorna più documenti
collezione_utenti.update_many(
    {"eta": {"$lt": 18}},
    {"$set": {"minorenne": True}}
)

# Upsert — inserisci se non esiste, aggiorna altrimenti
collezione_utenti.update_one(
    {"email": "nuovo@esempio.it"},
    {"$set": {"nome": "Nuovo Utente", "eta": 25}},
    upsert=True
)

# --- DELETE ---
collezione_utenti.delete_one({"email": "laura@esempio.it"})
risultato = collezione_utenti.delete_many({"attivo": False})
print(f"Documenti eliminati: {risultato.deleted_count}")
```

### Aggregation Pipeline

La pipeline di aggregazione è lo strumento più potente di MongoDB per l'analisi dei dati, simile alle query GROUP BY e JOIN in SQL.

```python
# Conteggio utenti per città
pipeline = [
    {"$match": {"eta": {"$gte": 18}}},          # Filtra
    {"$group": {                                   # Raggruppa
        "_id": "$indirizzo.citta",
        "totale": {"$sum": 1},
        "eta_media": {"$avg": "$eta"},
    }},
    {"$sort": {"totale": -1}},                    # Ordina
    {"$limit": 10},                                # Limita
]

risultati = collezione_utenti.aggregate(pipeline)
for r in risultati:
    print(f"Città: {r['_id']}, Utenti: {r['totale']}, Età media: {r['eta_media']:.1f}")

# Pipeline con $lookup (equivalente di una JOIN)
pipeline_con_join = [
    {"$lookup": {
        "from": "ordini",
        "localField": "_id",
        "foreignField": "utente_id",
        "as": "ordini_utente",
    }},
    {"$project": {
        "nome": 1,
        "totale_ordini": {"$size": "$ordini_utente"},
        "spesa_totale": {"$sum": "$ordini_utente.totale"},
    }},
    {"$match": {"totale_ordini": {"$gt": 0}}},
]
```

### Motor (Driver Asincrono)

Motor è il driver asincrono ufficiale per MongoDB, costruito sopra pymongo, essenziale per applicazioni async come quelle basate su FastAPI o asyncio.

```python
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    # Connessione asincrona
    client = AsyncIOMotorClient("mongodb://localhost:27017/")
    db = client["mio_database"]
    collezione = db["utenti"]

    # Inserimento
    risultato = await collezione.insert_one({
        "nome": "Async User",
        "email": "async@esempio.it",
    })
    print(f"ID: {risultato.inserted_id}")

    # Query
    async for utente in collezione.find({"eta": {"$gte": 25}}).limit(10):
        print(utente["nome"])

    # Aggregazione
    pipeline = [
        {"$group": {"_id": "$indirizzo.citta", "totale": {"$sum": 1}}},
    ]
    async for risultato in collezione.aggregate(pipeline):
        print(risultato)

    # Conteggio
    totale = await collezione.count_documents({"attivo": True})
    print(f"Utenti attivi: {totale}")

asyncio.run(main())
```

---

## Pattern e Best Practices

### Repository Pattern

Il Repository Pattern astrae l'accesso ai dati dietro un'interfaccia, separando la logica di business dalla logica di persistenza. Questo rende il codice più testabile e flessibile.

```python
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional

T = TypeVar("T")

class RepositoryAstratto(ABC, Generic[T]):
    """Interfaccia astratta per il repository."""

    @abstractmethod
    def ottieni_per_id(self, id: int) -> Optional[T]:
        ...

    @abstractmethod
    def ottieni_tutti(self, limite: int = 100, offset: int = 0) -> list[T]:
        ...

    @abstractmethod
    def aggiungi(self, entita: T) -> T:
        ...

    @abstractmethod
    def aggiorna(self, entita: T) -> T:
        ...

    @abstractmethod
    def elimina(self, id: int) -> bool:
        ...

class RepositoryUtentiSQLAlchemy(RepositoryAstratto[Utente]):
    """Implementazione concreta con SQLAlchemy."""

    def __init__(self, session: Session):
        self.session = session

    def ottieni_per_id(self, id: int) -> Optional[Utente]:
        return self.session.get(Utente, id)

    def ottieni_tutti(self, limite: int = 100, offset: int = 0) -> list[Utente]:
        stmt = select(Utente).limit(limite).offset(offset)
        return list(self.session.scalars(stmt).all())

    def aggiungi(self, entita: Utente) -> Utente:
        self.session.add(entita)
        self.session.flush()  # Ottieni l'ID senza fare commit
        return entita

    def aggiorna(self, entita: Utente) -> Utente:
        self.session.merge(entita)
        self.session.flush()
        return entita

    def elimina(self, id: int) -> bool:
        utente = self.ottieni_per_id(id)
        if utente:
            self.session.delete(utente)
            return True
        return False

class RepositoryUtentiMongo(RepositoryAstratto[dict]):
    """Implementazione concreta con MongoDB."""

    def __init__(self, collezione):
        self.collezione = collezione

    def ottieni_per_id(self, id: int) -> Optional[dict]:
        return self.collezione.find_one({"_id": id})

    def ottieni_tutti(self, limite: int = 100, offset: int = 0) -> list[dict]:
        return list(self.collezione.find().skip(offset).limit(limite))

    def aggiungi(self, entita: dict) -> dict:
        risultato = self.collezione.insert_one(entita)
        entita["_id"] = risultato.inserted_id
        return entita

    def aggiorna(self, entita: dict) -> dict:
        self.collezione.replace_one({"_id": entita["_id"]}, entita)
        return entita

    def elimina(self, id: int) -> bool:
        risultato = self.collezione.delete_one({"_id": id})
        return risultato.deleted_count > 0
```

### Unit of Work

Il pattern Unit of Work gestisce le transazioni raggruppando le operazioni in un'unità atomica. In SQLAlchemy, la `Session` funge già da Unit of Work.

```python
from contextlib import contextmanager

class UnitOfWork:
    """Gestisce il ciclo di vita della sessione e delle transazioni."""

    def __init__(self, session_factory):
        self.session_factory = session_factory

    def __enter__(self):
        self.session = self.session_factory()
        self.utenti = RepositoryUtentiSQLAlchemy(self.session)
        # Aggiungere altri repository secondo necessità
        # self.articoli = RepositoryArticoliSQLAlchemy(self.session)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
        self.session.close()

    def commit(self):
        """Conferma tutte le modifiche."""
        self.session.commit()

    def rollback(self):
        """Annulla tutte le modifiche."""
        self.session.rollback()

# Utilizzo del pattern Unit of Work
from sqlalchemy.orm import sessionmaker

SessionFactory = sessionmaker(bind=engine)

def trasferisci_articolo(articolo_id: int, nuovo_autore_id: int):
    """Trasferisce un articolo a un nuovo autore."""
    with UnitOfWork(SessionFactory) as uow:
        utente = uow.utenti.ottieni_per_id(nuovo_autore_id)
        if not utente:
            raise ValueError("Utente non trovato")

        # Operazioni multiple nella stessa transazione
        # ...

        uow.commit()
```

### Connection Pooling

Il connection pooling è una tecnica fondamentale per le prestazioni delle applicazioni in produzione. Mantenere un pool di connessioni riutilizzabili elimina il costo di apertura e chiusura ripetuta delle connessioni. Senza un pool, ogni richiesta deve negoziare una nuova connessione TCP, eseguire l'autenticazione e inizializzare la sessione con il database, operazioni che possono richiedere decine di millisecondi ciascuna. Con un pool, le connessioni vengono create una sola volta e riutilizzate per tutta la durata dell'applicazione, riducendo drasticamente la latenza e il consumo di risorse sul server di database.

```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

# Configurazione del pool con SQLAlchemy
engine = create_engine(
    "postgresql+psycopg://utente:password@localhost/mio_db",
    poolclass=QueuePool,
    pool_size=10,           # Numero di connessioni permanenti
    max_overflow=20,        # Connessioni aggiuntive in caso di carico
    pool_timeout=30,        # Secondi di attesa per una connessione libera
    pool_recycle=1800,      # Ricicla connessioni ogni 30 minuti
    pool_pre_ping=True,     # Verifica che la connessione sia valida prima dell'uso
)

# Monitoraggio del pool
print(f"Dimensione pool: {engine.pool.size()}")
print(f"Connessioni in uso: {engine.pool.checkedin()}")
print(f"Connessioni checked out: {engine.pool.checkedout()}")
```

### Query Optimization

#### Problema N+1 e Soluzioni

Il problema N+1 si verifica quando si caricano N entità e poi si esegue una query aggiuntiva per ciascuna per caricare le relazioni, risultando in N+1 query totali.

```python
from sqlalchemy.orm import joinedload, selectinload

# PROBLEMA N+1 — 1 query per gli utenti + N query per gli articoli
with Session(engine) as session:
    utenti = session.scalars(select(Utente)).all()
    for utente in utenti:
        # Ogni accesso a utente.articoli genera una nuova query
        print(f"{utente.nome}: {len(utente.articoli)} articoli")

# SOLUZIONE con joinedload — una singola query con JOIN
with Session(engine) as session:
    stmt = select(Utente).options(joinedload(Utente.articoli))
    utenti = session.scalars(stmt).unique().all()
    for utente in utenti:
        print(f"{utente.nome}: {len(utente.articoli)} articoli")

# SOLUZIONE con selectinload — due query (più efficiente per grandi dataset)
with Session(engine) as session:
    stmt = select(Utente).options(selectinload(Utente.articoli))
    utenti = session.scalars(stmt).all()
```

#### Strategie di Indicizzazione

Gli indici sono strutture dati che velocizzano le operazioni di lettura sul database, al costo di un leggero rallentamento delle operazioni di scrittura e di spazio aggiuntivo su disco. La scelta degli indici corretti è una delle attività più importanti per l'ottimizzazione delle prestazioni. Come regola generale, si dovrebbero creare indici sulle colonne utilizzate frequentemente nelle clausole `WHERE`, `JOIN`, `ORDER BY` e `GROUP BY`. Gli indici composti (su più colonne) sono particolarmente efficaci quando le query filtrano su più colonne contemporaneamente, ma l'ordine delle colonne nell'indice è determinante per la sua efficacia.

```python
from sqlalchemy import Index

class Articolo(Base):
    __tablename__ = "articoli"

    # ... colonne ...

    # Indici per ottimizzare le query più comuni
    __table_args__ = (
        Index("idx_articoli_autore", "autore_id"),
        Index("idx_articoli_pubblicato_data", "pubblicato", "creato_il"),
        Index("idx_articoli_titolo_tsvector", "titolo",
              postgresql_using="gin",
              postgresql_ops={"titolo": "gin_trgm_ops"}),
    )
```

#### Analisi con EXPLAIN

L'istruzione `EXPLAIN` (e la sua variante `EXPLAIN ANALYZE` in PostgreSQL) è lo strumento diagnostico principale per comprendere come il database esegue una query. Mostra il piano di esecuzione scelto dal query planner, inclusi i metodi di scansione delle tabelle (sequential scan, index scan, bitmap scan), le strategie di join (nested loop, hash join, merge join) e le stime sui costi. Analizzare regolarmente i piani di esecuzione delle query più frequenti permette di identificare scansioni sequenziali non necessarie, indici mancanti e strategie di join inefficienti.

```python
from sqlalchemy import text

with engine.connect() as conn:
    # Analizza il piano di esecuzione della query
    risultato = conn.execute(text("""
        EXPLAIN ANALYZE
        SELECT u.nome, COUNT(a.id) as num_articoli
        FROM utenti u
        JOIN articoli a ON u.id = a.autore_id
        WHERE a.pubblicato = true
        GROUP BY u.nome
        ORDER BY num_articoli DESC
    """))

    for riga in risultato:
        print(riga[0])
```

#### Operazioni Batch

Le operazioni batch (o bulk) consentono di eseguire inserimenti, aggiornamenti ed eliminazioni su grandi quantità di dati in modo efficiente. Anziché inviare ogni operazione singolarmente al database (con il relativo overhead di rete e di parsing), le operazioni batch raggruppano centinaia o migliaia di righe in un'unica comunicazione. SQLAlchemy offre diversi livelli di ottimizzazione per le operazioni batch, dal metodo `add_all()` dell'ORM fino all'uso diretto del Core con `insert().values()` per le massime prestazioni.

```python
from sqlalchemy import insert

# Inserimento batch efficiente
with Session(engine) as session:
    # Invece di aggiungere uno per uno
    dati = [
        {"nome": f"Utente {i}", "email": f"utente{i}@esempio.it", "eta": 20 + i}
        for i in range(10000)
    ]

    # Inserimento bulk con Core (più veloce)
    session.execute(insert(Utente), dati)
    session.commit()

# Aggiornamento batch
with Session(engine) as session:
    session.execute(
        update(Utente)
        .where(Utente.eta < 18)
        .values(attivo=False)
    )
    session.commit()
```

---

## Best Practices

Di seguito le dieci pratiche fondamentali per una corretta programmazione con database in Python:

1. **Utilizzare sempre query parametrizzate.** Non concatenare mai valori utente direttamente nelle stringhe SQL. Utilizzare i segnaposto forniti dal driver (`?` per SQLite, `%s` per PostgreSQL e MySQL) per prevenire attacchi di SQL injection. Questa è la regola più importante per la sicurezza delle applicazioni.

2. **Implementare il connection pooling in produzione.** L'apertura e la chiusura di connessioni ad ogni richiesta rappresenta un collo di bottiglia significativo. Utilizzare i pool di connessioni offerti da SQLAlchemy, psycopg_pool o i meccanismi nativi del driver per riutilizzare le connessioni in modo efficiente, configurando dimensione minima, massima e timeout in base al carico previsto.

3. **Gestire le migrazioni con Alembic.** Non modificare mai lo schema del database manualmente in produzione. Utilizzare Alembic per versionare ogni modifica allo schema, garantendo che le migrazioni siano reversibili, testate e applicate in modo coerente su tutti gli ambienti (sviluppo, staging, produzione).

4. **Chiudere sempre le connessioni e le risorse.** Utilizzare i context manager (`with`) per garantire la chiusura automatica di connessioni, cursori e sessioni. Le risorse non rilasciate possono causare memory leak, esaurimento del pool di connessioni e problemi di prestazioni.

5. **Gestire le transazioni in modo esplicito.** Raggruppare le operazioni correlate in transazioni atomiche, utilizzando `commit()` per confermare e `rollback()` per annullare in caso di errore. Comprendere i livelli di isolamento del database utilizzato e scegliere quello appropriato per il caso d'uso.

6. **Risolvere il problema N+1 con il caricamento anticipato.** Quando si lavora con l'ORM, utilizzare `joinedload()`, `selectinload()` o `subqueryload()` per caricare le relazioni in modo efficiente. Monitorare le query generate abilitando il logging SQL (`echo=True` in SQLAlchemy) durante lo sviluppo.

7. **Creare indici appropriati.** Analizzare le query più frequenti e creare indici sulle colonne utilizzate nelle clausole `WHERE`, `JOIN` e `ORDER BY`. Utilizzare `EXPLAIN ANALYZE` per verificare che gli indici siano effettivamente utilizzati dal pianificatore di query. Non creare indici in eccesso, poiché rallentano le operazioni di scrittura.

8. **Separare la logica di accesso ai dati dalla logica di business.** Adottare il Repository Pattern per isolare le operazioni sul database. Ciò rende il codice più testabile (si possono facilmente creare mock dei repository), manutenibile e permette di cambiare il database sottostante senza modificare la logica applicativa.

9. **Configurare correttamente le credenziali del database.** Non scrivere mai le credenziali direttamente nel codice sorgente. Utilizzare variabili d'ambiente, file `.env` (con librerie come `python-dotenv`) o sistemi di gestione dei segreti. Applicare il principio del minimo privilegio: ogni servizio dovrebbe avere un utente database con i soli permessi necessari.

10. **Implementare una strategia di backup e monitoraggio.** Configurare backup regolari e automatizzati del database. Monitorare le prestazioni delle query, il tempo di risposta, l'utilizzo delle connessioni e lo spazio su disco. Implementare health check per verificare la raggiungibilità del database e impostare alert per situazioni anomale.

---

## SQLAlchemy 2.0 — Approfondimento

> Rif. SQLAlchemy docs: *What's New in SQLAlchemy 2.0* · *Mapped Column Attributes*

SQLAlchemy 2.0 rappresenta un cambiamento architetturale rispetto alla serie 1.x. L'API precedente basata su `Column()` e `declarative_base()` rimane funzionante ma e deprecata. L'API 2.0 si basa su annotazioni Python native e offre supporto completo per type checkers come mypy e pyright.

### DeclarativeBase vs declarative_base()

Il vecchio `declarative_base()` era una funzione factory che restituiva una classe base. La nuova `DeclarativeBase` e una classe che si sottoclassa direttamente, con pieno supporto per l'ereditarieta e i type hints.

```python
# --- VECCHIO STILE (1.x / legacy) — deprecato ---
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String

Base = declarative_base()

class UtenteVecchio(Base):
    __tablename__ = "utenti"
    id = Column(Integer, primary_key=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)


# --- NUOVO STILE (2.0) — raccomandato ---
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String

class Base(DeclarativeBase):
    pass

class UtenteNuovo(Base):
    __tablename__ = "utenti"
    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(150), unique=True)
```

La differenza principale: con `Mapped[T]`, il tipo Python e il tipo colonna sono dichiarati in un unico punto. Un `Mapped[str]` genera automaticamente una colonna `NOT NULL`; un `Mapped[Optional[str]]` genera una colonna `nullable=True`. Il type checker puo verificare staticamente la correttezza dei tipi senza esecuzione.

### Mapped[T] — Inferenza dei tipi

`Mapped[T]` accetta qualsiasi tipo Python supportato dal type map di SQLAlchemy. Il mapping predefinito tra tipi Python e tipi SQL e il seguente:

| Python type | SQL type |
|---|---|
| `int` | `Integer` |
| `str` | `String` (richiede length per la maggior parte dei backend) |
| `float` | `Float` |
| `bool` | `Boolean` |
| `bytes` | `LargeBinary` |
| `datetime.datetime` | `DateTime` |
| `datetime.date` | `Date` |
| `datetime.time` | `Time` |
| `decimal.Decimal` | `Numeric` |
| `uuid.UUID` | `Uuid` |

```python
from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Text, Numeric

class Prodotto(Base):
    __tablename__ = "prodotti"

    id: Mapped[int] = mapped_column(primary_key=True)
    codice: Mapped[UUID] = mapped_column(default=None)
    nome: Mapped[str] = mapped_column(String(200))
    descrizione: Mapped[Optional[str]] = mapped_column(Text, default=None)
    prezzo: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    disponibile: Mapped[bool] = mapped_column(default=True)
    data_inserimento: Mapped[date] = mapped_column(default=date.today)
    ultimo_aggiornamento: Mapped[Optional[datetime]] = mapped_column(default=None)
```

### mapped_column() — Parametri avanzati

`mapped_column()` accetta tutti i parametri di `Column()` piu alcuni specifici per il mapping ORM.

```python
from sqlalchemy import String, func, text
from sqlalchemy.orm import Mapped, mapped_column

class Ordine(Base):
    __tablename__ = "ordini"

    id: Mapped[int] = mapped_column(primary_key=True)

    # server_default: il database genera il valore (visibile anche fuori dall'ORM)
    codice: Mapped[str] = mapped_column(
        String(20),
        server_default=text("'ORD-' || nextval('ordini_seq')"),
    )

    # default: Python genera il valore prima dell'INSERT
    stato: Mapped[str] = mapped_column(String(20), default="nuovo")

    # insert_default: come default, ma esplicito per l'INSERT
    # init=False: escluso dal __init__ generato (utile con dataclass mapping)
    creato_il: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        init=False,
    )

    # index=True: crea un indice sulla colonna
    cliente_email: Mapped[str] = mapped_column(String(150), index=True)

    # unique + nullable
    codice_fiscale: Mapped[Optional[str]] = mapped_column(
        String(16), unique=True, default=None
    )
```

### relationship() nel contesto 2.0

Le relazioni in 2.0 sfruttano `Mapped` per dichiarare il tipo atteso (singolo oggetto o lista). Cio consente al type checker di segnalare accessi errati.

```python
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional

class Dipartimento(Base):
    __tablename__ = "dipartimenti"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100), unique=True)

    # one-to-many: un dipartimento ha molti impiegati
    impiegati: Mapped[List["Impiegato"]] = relationship(
        back_populates="dipartimento",
        cascade="all, delete-orphan",
        order_by="Impiegato.cognome",
    )

class Impiegato(Base):
    __tablename__ = "impiegati"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100))
    cognome: Mapped[str] = mapped_column(String(100))
    dipartimento_id: Mapped[int] = mapped_column(
        ForeignKey("dipartimenti.id")
    )

    # many-to-one
    dipartimento: Mapped["Dipartimento"] = relationship(
        back_populates="impiegati"
    )

    # one-to-one (uselist=False)
    badge: Mapped[Optional["Badge"]] = relationship(
        back_populates="impiegato", uselist=False
    )

class Badge(Base):
    __tablename__ = "badge"

    id: Mapped[int] = mapped_column(primary_key=True)
    codice: Mapped[str] = mapped_column(String(20), unique=True)
    impiegato_id: Mapped[int] = mapped_column(
        ForeignKey("impiegati.id"), unique=True
    )

    impiegato: Mapped["Impiegato"] = relationship(back_populates="badge")
```

### Mixin e classi base riutilizzabili

Un pattern comune e definire colonne condivise (timestamps, soft delete) in un mixin.

```python
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column, declared_attr

class TimestampMixin:
    """Mixin per colonne di timestamp automatiche."""
    creato_il: Mapped[datetime] = mapped_column(server_default=func.now())
    aggiornato_il: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )

class SoftDeleteMixin:
    """Mixin per soft delete."""
    eliminato: Mapped[bool] = mapped_column(default=False)
    eliminato_il: Mapped[Optional[datetime]] = mapped_column(default=None)

class Progetto(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "progetti"

    id: Mapped[int] = mapped_column(primary_key=True)
    titolo: Mapped[str] = mapped_column(String(200))
    # creato_il, aggiornato_il, eliminato, eliminato_il sono ereditati
```

---

## Async SQLAlchemy — Approfondimento

> Rif. SQLAlchemy docs: *Asynchronous I/O (asyncio)* · asyncpg docs: *API Reference*

### Architettura async: cosa succede dietro le quinte

`create_async_engine` crea un wrapper attorno a un engine sincrono. Le operazioni vengono eseguite in un thread executor (di default `asyncio.get_event_loop().run_in_executor()`), eccetto per i driver nativamente asincroni come `asyncpg` e `aiosqlite`, che non richiedono il thread executor.

```python
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncAttrs,
)
from sqlalchemy import select

# asyncpg per PostgreSQL (nativo async, nessun thread executor)
async_engine = create_async_engine(
    "postgresql+asyncpg://utente:password@localhost:5432/mio_db",
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

# aiosqlite per SQLite (wrapper async su sqlite3)
# async_engine_sqlite = create_async_engine("sqlite+aiosqlite:///test.db")
```

### async_sessionmaker — Factory pattern

`async_sessionmaker` e la controparte asincrona di `sessionmaker`. La best practice e crearla una sola volta a livello di modulo e riutilizzarla in tutta l'applicazione.

```python
AsyncSessionFactory = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,  # gli attributi restano accessibili dopo il commit
)


async def ottieni_utente_per_email(email: str) -> Utente | None:
    """Ricerca un utente per email."""
    async with AsyncSessionFactory() as session:
        stmt = select(Utente).where(Utente.email == email)
        return await session.scalar(stmt)


async def crea_utente_con_articoli(
    nome: str, email: str, titoli_articoli: list[str]
) -> Utente:
    """Crea un utente con i suoi articoli in una singola transazione."""
    async with AsyncSessionFactory() as session:
        async with session.begin():
            utente = Utente(nome=nome, email=email)
            session.add(utente)
            await session.flush()  # ottieni l'ID prima di creare gli articoli

            for titolo in titoli_articoli:
                session.add(Articolo(titolo=titolo, autore_id=utente.id))

        # begin() fa il commit automaticamente; se si solleva un'eccezione, rollback
        return utente
```

### Relazioni lazy in contesto async

In contesto asincrono, le relazioni lazy non possono essere caricate con un accesso diretto all'attributo (causerebbe I/O sincrono in un event loop). Le opzioni sono:

1. **Eager loading** con `selectinload`/`joinedload` nella query.
2. **`AsyncAttrs`** mixin che rende le relazioni awaitable.
3. **`awaitable_attrs`** (SQLAlchemy 2.0.20+): `await session.run_sync()`.

```python
# Opzione 1: eager loading nella query (raccomandato)
async with AsyncSessionFactory() as session:
    stmt = (
        select(Utente)
        .options(selectinload(Utente.articoli))
        .where(Utente.id == 1)
    )
    utente = await session.scalar(stmt)
    # utente.articoli e gia caricato, nessun await necessario
    for art in utente.articoli:
        print(art.titolo)


# Opzione 2: AsyncAttrs mixin (utile per accessi one-off)
class UtenteAsync(AsyncAttrs, Base):
    __tablename__ = "utenti_async"
    id: Mapped[int] = mapped_column(primary_key=True)
    articoli: Mapped[List["ArticoloAsync"]] = relationship()

# Utilizzo:
# articoli = await utente.awaitable_attrs.articoli
```

### Integrazione con FastAPI

```python
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession

app = FastAPI()

async def get_session() -> AsyncSession:
    """Dependency injection per la sessione asincrona."""
    async with AsyncSessionFactory() as session:
        yield session

@app.get("/utenti/{utente_id}")
async def leggi_utente(
    utente_id: int,
    session: AsyncSession = Depends(get_session),
):
    utente = await session.get(Utente, utente_id)
    if not utente:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    return {"id": utente.id, "nome": utente.nome}
```

---

## Alembic — Approfondimento

> Rif. Alembic docs: *Auto Generating Migrations* · *Running Alembic in an asyncio application*

### Configurazione async di env.py

Per progetti che utilizzano `create_async_engine`, il file `env.py` deve essere adattato. Alembic supporta nativamente l'esecuzione asincrona dalla versione 1.7.

```python
# alembic/env.py — versione async
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.models import Base  # i modelli con DeclarativeBase

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Genera SQL senza connettersi al database."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    """Callback sincrono eseguito dentro run_sync()."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        render_as_batch=True,  # necessario per SQLite (non supporta ALTER TABLE)
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Esegue le migrazioni con un engine asincrono."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Entry point per le migrazioni online."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### Auto-generation: cosa rileva e cosa no

L'opzione `--autogenerate` confronta lo stato dei modelli Python con lo schema corrente del database e genera le operazioni necessarie. Ecco cosa rileva automaticamente e cosa richiede intervento manuale:

**Rileva automaticamente:**
- Tabelle aggiunte o rimosse
- Colonne aggiunte o rimosse
- Cambiamenti di nullable (con `compare_type=True`)
- Foreign key aggiunte o rimosse
- Indici e vincoli unique aggiunti o rimossi

**NON rileva (richiede migrazione manuale):**
- Rinomina di tabelle o colonne (vengono interpretati come drop + create)
- Cambiamenti ai constraint CHECK
- Cambiamenti a `server_default` (a meno di `compare_server_default=True`)
- Cambiamenti nei dati (data migrations)
- Stored procedures, trigger, viste

```bash
# Genera una migrazione e poi RIVEDI il file prima di applicarla
alembic revision --autogenerate -m "aggiunta tabella ordini"

# Rivedi il contenuto
cat alembic/versions/xxxx_aggiunta_tabella_ordini.py
```

### Migrazione con rinomina di colonna

```python
"""rinomina colonna nome in nome_completo

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
"""
from alembic import op

revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"

def upgrade() -> None:
    op.alter_column(
        "utenti",
        "nome",
        new_column_name="nome_completo",
    )

def downgrade() -> None:
    op.alter_column(
        "utenti",
        "nome_completo",
        new_column_name="nome",
    )
```

### Merge di branch divergenti

Quando piu sviluppatori creano migrazioni in parallelo, si formano branch divergenti. Alembic offre il comando `merge` per unirli.

```bash
# Visualizza i branch
alembic heads

# Se ci sono piu head, uniscili
alembic merge -m "merge branch feature_ordini e feature_notifiche" head1 head2
```

### Stamping: sincronizzare un database esistente

```bash
# Segna il database come aggiornato alla revisione corrente
# (utile quando si inizializza Alembic su un database gia esistente)
alembic stamp head

# Segna una revisione specifica
alembic stamp a1b2c3d4e5f6
```

---

## Repository Pattern — Approfondimento

### Repository asincrono con generics

```python
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, Sequence
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

ModelType = TypeVar("ModelType", bound=Base)


class RepositoryAsincrono(ABC, Generic[ModelType]):
    """Repository base asincrono con operazioni CRUD generiche."""

    def __init__(self, session: AsyncSession, model: type[ModelType]):
        self.session = session
        self.model = model

    async def ottieni_per_id(self, id: int) -> Optional[ModelType]:
        return await self.session.get(self.model, id)

    async def ottieni_tutti(
        self, *, limite: int = 100, offset: int = 0
    ) -> Sequence[ModelType]:
        stmt = select(self.model).limit(limite).offset(offset)
        risultato = await self.session.scalars(stmt)
        return risultato.all()

    async def conta(self) -> int:
        stmt = select(func.count()).select_from(self.model)
        return await self.session.scalar(stmt) or 0

    async def aggiungi(self, entita: ModelType) -> ModelType:
        self.session.add(entita)
        await self.session.flush()
        return entita

    async def aggiungi_multipli(self, entita: list[ModelType]) -> list[ModelType]:
        self.session.add_all(entita)
        await self.session.flush()
        return entita

    async def elimina(self, entita: ModelType) -> None:
        await self.session.delete(entita)


class RepositoryUtentiAsync(RepositoryAsincrono[Utente]):
    """Repository specializzato per gli utenti."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Utente)

    async def cerca_per_email(self, email: str) -> Optional[Utente]:
        stmt = select(Utente).where(Utente.email == email)
        return await self.session.scalar(stmt)

    async def ottieni_attivi(self) -> Sequence[Utente]:
        stmt = (
            select(Utente)
            .where(Utente.attivo == True)
            .order_by(Utente.nome)
        )
        risultato = await self.session.scalars(stmt)
        return risultato.all()
```

### Dependency injection con FastAPI

```python
from fastapi import Depends

async def get_session() -> AsyncSession:
    async with AsyncSessionFactory() as session:
        yield session

async def get_repo_utenti(
    session: AsyncSession = Depends(get_session),
) -> RepositoryUtentiAsync:
    return RepositoryUtentiAsync(session)

@app.post("/utenti/")
async def crea_utente_endpoint(
    nome: str,
    email: str,
    repo: RepositoryUtentiAsync = Depends(get_repo_utenti),
    session: AsyncSession = Depends(get_session),
):
    utente = Utente(nome=nome, email=email)
    await repo.aggiungi(utente)
    await session.commit()
    return {"id": utente.id, "nome": utente.nome}
```

---

## Query Avanzate — CTE, Window Functions, Subquery

> Rif. SQLAlchemy docs: *Common Table Expressions* · *Window Functions* · PostgreSQL docs: *WITH Queries*

### Common Table Expressions (CTE)

Le CTE migliorano la leggibilita delle query complesse e consentono query ricorsive.

```python
from sqlalchemy import select, func, literal

# CTE per calcolare statistiche intermedie
with Session(engine) as session:
    # CTE: conteggio articoli per autore
    articoli_per_autore = (
        select(
            Articolo.autore_id,
            func.count(Articolo.id).label("num_articoli"),
            func.avg(func.length(Articolo.contenuto)).label("lunghezza_media"),
        )
        .where(Articolo.pubblicato == True)
        .group_by(Articolo.autore_id)
        .cte("articoli_per_autore")
    )

    # Query principale che usa la CTE
    stmt = (
        select(
            Utente.nome,
            articoli_per_autore.c.num_articoli,
            articoli_per_autore.c.lunghezza_media,
        )
        .join(articoli_per_autore, Utente.id == articoli_per_autore.c.autore_id)
        .where(articoli_per_autore.c.num_articoli > 3)
        .order_by(articoli_per_autore.c.num_articoli.desc())
    )

    for riga in session.execute(stmt):
        print(f"{riga.nome}: {riga.num_articoli} articoli")
```

### CTE ricorsiva

```python
# CTE ricorsiva per strutture gerarchiche (es. categorie annidate)
class Categoria(Base):
    __tablename__ = "categorie"
    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100))
    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("categorie.id"), default=None
    )

# Trova tutti i discendenti di una categoria
with Session(engine) as session:
    # Parte non ricorsiva: la categoria radice
    gerarchia = (
        select(
            Categoria.id,
            Categoria.nome,
            Categoria.parent_id,
            literal(0).label("livello"),
        )
        .where(Categoria.id == 1)  # categoria radice
        .cte("gerarchia", recursive=True)
    )

    # Parte ricorsiva: i figli
    cat_alias = Categoria.__table__.alias()
    gerarchia = gerarchia.union_all(
        select(
            cat_alias.c.id,
            cat_alias.c.nome,
            cat_alias.c.parent_id,
            (gerarchia.c.livello + 1).label("livello"),
        )
        .where(cat_alias.c.parent_id == gerarchia.c.id)
    )

    stmt = select(gerarchia).order_by(gerarchia.c.livello, gerarchia.c.nome)
    for riga in session.execute(stmt):
        indentazione = "  " * riga.livello
        print(f"{indentazione}{riga.nome} (livello {riga.livello})")
```

### Window Functions

Le window functions calcolano valori su un set di righe correlate senza raggrupparle, mantenendo tutte le righe nel risultato.

```python
from sqlalchemy import select, func, over

with Session(engine) as session:
    # Classifica degli autori per numero di articoli
    stmt = select(
        Utente.nome,
        func.count(Articolo.id).label("num_articoli"),
        func.rank().over(
            order_by=func.count(Articolo.id).desc()
        ).label("posizione"),
    ).join(Articolo).group_by(Utente.id, Utente.nome)

    for riga in session.execute(stmt):
        print(f"#{riga.posizione} {riga.nome}: {riga.num_articoli}")

    # Running total con window function
    stmt = select(
        Articolo.titolo,
        Articolo.creato_il,
        func.count().over(
            partition_by=Articolo.autore_id,
            order_by=Articolo.creato_il,
        ).label("articolo_progressivo"),
        func.row_number().over(
            partition_by=Articolo.autore_id,
            order_by=Articolo.creato_il.desc(),
        ).label("riga"),
    ).where(Articolo.pubblicato == True)

    for riga in session.execute(stmt):
        print(f"{riga.titolo} — progressivo: {riga.articolo_progressivo}")
```

---

## Loading Strategies — Approfondimento

> Rif. SQLAlchemy docs: *Relationship Loading Techniques*

### Confronto delle strategie

| Strategia | N. query | Quando usare | Attenzione |
|---|---|---|---|
| `lazy="select"` (default) | 1 + N | Relazioni raramente accedute | Problema N+1 in cicli |
| `joinedload()` | 1 | Relazione singola, pochi risultati | Duplicazione righe nel risultato |
| `selectinload()` | 2 | Liste di oggetti con relazioni | Clausola IN puo crescere |
| `subqueryload()` | 2 | Simile a selectinload, query complesse | Subquery puo essere costosa |
| `raiseload()` | 0 (errore) | Prevenzione accessi lazy accidentali | Solleva `InvalidRequestError` |
| `lazy="write_only"` | 0 | Collezioni grandi, solo scrittura | Nessuna lettura automatica |

### raiseload — Prevenzione N+1 in produzione

`raiseload` e una strategia difensiva: se il codice tenta di accedere a una relazione non caricata, SQLAlchemy solleva un'eccezione anziché eseguire una query lazy. Questo forza lo sviluppatore a dichiarare esplicitamente le relazioni necessarie nella query, eliminando le query N+1 accidentali.

```python
from sqlalchemy.orm import raiseload

# Carica SOLO i dati dell'utente — qualsiasi accesso a relazioni solleva errore
with Session(engine) as session:
    stmt = (
        select(Utente)
        .options(raiseload(Utente.articoli))
        .where(Utente.id == 1)
    )
    utente = session.scalars(stmt).first()
    # utente.articoli  # <-- InvalidRequestError!

# Combinare raiseload con caricamenti selettivi
with Session(engine) as session:
    stmt = (
        select(Utente)
        .options(
            selectinload(Utente.articoli),  # carica articoli
            raiseload(Utente.profilo),       # blocca accesso al profilo
        )
    )
```

### lazy="write_only" — Collezioni grandi

Per relazioni con migliaia di elementi dove non si vuole mai caricare l'intera collezione in memoria.

```python
from sqlalchemy.orm import WriteOnlyMapped, relationship

class AutoreProlifico(Base):
    __tablename__ = "autori_prolifici"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100))

    # WriteOnlyMapped: la collezione non viene mai caricata interamente
    articoli: WriteOnlyMapped[List["Articolo"]] = relationship(
        lazy="write_only"
    )

# Utilizzo
with Session(engine) as session:
    autore = session.get(AutoreProlifico, 1)

    # Aggiungere elementi senza caricare la collezione
    autore.articoli.add(Articolo(titolo="Nuovo articolo"))

    # Per leggere, usare una query esplicita
    stmt = autore.articoli.select().where(Articolo.pubblicato == True).limit(10)
    articoli = session.scalars(stmt).all()
```

---

## Connection Pooling — Approfondimento

> Rif. SQLAlchemy docs: *Connection Pooling*

### Tipi di pool disponibili

SQLAlchemy offre diversi pool, ciascuno con un caso d'uso specifico.

| Pool | Descrizione | Caso d'uso |
|---|---|---|
| `QueuePool` | Pool con coda FIFO (default) | Applicazioni web, servizi in produzione |
| `NullPool` | Nessun pooling, connessione nuova ad ogni richiesta | Alembic, script singoli, ambienti serverless |
| `StaticPool` | Una singola connessione condivisa | Test con SQLite in-memory |
| `SingletonThreadPool` | Una connessione per thread | SQLite multi-thread |
| `AsyncAdaptedQueuePool` | QueuePool per engine async | Applicazioni async |

```python
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool, StaticPool, QueuePool

# Produzione — QueuePool con tuning
engine_produzione = create_engine(
    "postgresql+psycopg://utente:password@localhost/mio_db",
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True,
)

# Alembic / script — NullPool
engine_migrazione = create_engine(
    "postgresql+psycopg://utente:password@localhost/mio_db",
    poolclass=NullPool,
)

# Test con SQLite in-memory — StaticPool
engine_test = create_engine(
    "sqlite://",
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
)
```

### pool_pre_ping: come funziona

`pool_pre_ping=True` esegue un `SELECT 1` (o equivalente) prima di restituire una connessione dal pool. Se la connessione e morta (timeout del database, restart del server), viene scartata e ne viene creata una nuova. Il costo e trascurabile (~1ms) rispetto al rischio di un `OperationalError` in produzione.

### PgBouncer e SQLAlchemy

PgBouncer e un connection pooler esterno per PostgreSQL. Quando si usa PgBouncer in modalita `transaction`, ogni transazione puo utilizzare una connessione diversa. Questo richiede attenzione nella configurazione di SQLAlchemy:

```python
# Con PgBouncer in transaction mode
engine_pgbouncer = create_engine(
    "postgresql+psycopg://utente:password@pgbouncer:6432/mio_db",
    pool_size=5,          # il pool e gestito da PgBouncer, non serve grande
    pool_pre_ping=True,
    pool_reset_on_return="rollback",  # assicura stato pulito
    # DISABILITARE prepared statements con PgBouncer transaction mode
    # (le prepared statements sono per-connessione, ma PgBouncer riassegna le connessioni)
)
```

---

## Transaction Management — Approfondimento

> Rif. SQLAlchemy docs: *Session Basics — Framing out a begin / commit / rollback block*

### Pattern begin/commit/rollback

```python
from sqlalchemy.orm import Session

# Pattern esplicito con begin()
with Session(engine) as session:
    with session.begin():
        # Tutto in questo blocco e una singola transazione
        utente = Utente(nome="Test", email="test@esempio.it")
        session.add(utente)
        session.flush()

        articolo = Articolo(titolo="Test", autore_id=utente.id)
        session.add(articolo)
        # commit automatico all'uscita; rollback se eccezione

# Pattern con gestione manuale (quando serve logica condizionale)
with Session(engine) as session:
    try:
        session.add(Utente(nome="Manuale", email="manuale@esempio.it"))
        session.commit()
    except Exception:
        session.rollback()
        raise
```

### Nested transactions (savepoint)

I savepoint consentono di annullare parzialmente una transazione senza perdere le modifiche precedenti.

```python
with Session(engine) as session:
    with session.begin():
        # Operazione 1 — sara confermata
        utente = Utente(nome="Utente A", email="a@esempio.it")
        session.add(utente)
        session.flush()

        # Savepoint — tenta un'operazione rischiosa
        savepoint = session.begin_nested()
        try:
            utente_duplicato = Utente(nome="Dup", email="a@esempio.it")  # violazione UNIQUE
            session.add(utente_duplicato)
            session.flush()
            savepoint.commit()
        except Exception:
            savepoint.rollback()
            # L'utente A e ancora valido; il duplicato e annullato

        # Operazione 3 — procede nonostante l'errore nel savepoint
        session.add(Utente(nome="Utente B", email="b@esempio.it"))
    # commit della transazione esterna
```

### Livelli di isolamento

```python
from sqlalchemy import create_engine

# Imposta il livello di isolamento a livello di engine
engine = create_engine(
    "postgresql+psycopg://utente:password@localhost/mio_db",
    isolation_level="REPEATABLE READ",
    # Valori possibili per PostgreSQL:
    # "READ UNCOMMITTED", "READ COMMITTED" (default),
    # "REPEATABLE READ", "SERIALIZABLE"
)

# Oppure per singola connessione/transazione
with engine.connect().execution_options(
    isolation_level="SERIALIZABLE"
) as conn:
    # Questa connessione usa SERIALIZABLE
    conn.execute(text("..."))
    conn.commit()
```

---

## Pydantic v2 e SQLAlchemy — Integrazione

> Rif. Pydantic docs: *model_validate* · *ConfigDict* · *Field*

### Definizione degli schemi Pydantic

Pydantic v2 introduce `model_validate()` al posto di `from_orm()`, `ConfigDict` al posto di `class Config`, e `Field()` con parametri aggiornati.

```python
from pydantic import BaseModel, ConfigDict, Field, EmailStr
from datetime import datetime
from typing import Optional


class UtenteBase(BaseModel):
    """Schema base condiviso tra creazione e lettura."""
    nome: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    eta: Optional[int] = Field(None, ge=0, le=150)


class UtenteCrea(UtenteBase):
    """Schema per la creazione — niente id, niente timestamp."""
    pass


class UtenteRisposta(UtenteBase):
    """Schema per le risposte API — include id e timestamp."""
    id: int
    attivo: bool
    creato_il: datetime

    # ConfigDict sostituisce class Config in Pydantic v2
    model_config = ConfigDict(
        from_attributes=True,  # sostituisce orm_mode = True
        json_schema_extra={
            "example": {
                "id": 1,
                "nome": "Mario Rossi",
                "email": "mario@esempio.it",
                "eta": 30,
                "attivo": True,
                "creato_il": "2026-05-23T10:30:00",
            }
        },
    )


class ArticoloRisposta(BaseModel):
    id: int
    titolo: str
    pubblicato: bool
    creato_il: datetime
    autore: UtenteRisposta  # relazione annidata

    model_config = ConfigDict(from_attributes=True)
```

### model_validate da oggetti ORM

`model_validate()` converte un oggetto ORM in uno schema Pydantic, validando i dati nel processo. Richiede `from_attributes=True` nel `ConfigDict`.

```python
with Session(engine) as session:
    # Carica un utente dal database
    utente_orm = session.get(Utente, 1)

    # Converte in schema Pydantic
    utente_schema = UtenteRisposta.model_validate(utente_orm)
    print(utente_schema.model_dump())
    # {"id": 1, "nome": "Mario Rossi", "email": "mario@esempio.it", ...}

    # Serializzazione JSON diretta
    json_str = utente_schema.model_dump_json()

    # Con relazioni annidate (richiede eager loading)
    stmt = (
        select(Articolo)
        .options(joinedload(Articolo.autore))
        .where(Articolo.id == 1)
    )
    articolo_orm = session.scalars(stmt).first()
    articolo_schema = ArticoloRisposta.model_validate(articolo_orm)
    print(articolo_schema.autore.nome)  # accesso tipizzato alla relazione
```

### Pattern completo: FastAPI + Pydantic v2 + SQLAlchemy

```python
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

app = FastAPI()

@app.post("/utenti/", response_model=UtenteRisposta, status_code=201)
async def crea_utente(
    dati: UtenteCrea,
    session: AsyncSession = Depends(get_session),
):
    # Validazione automatica di Pydantic all'ingresso
    utente = Utente(**dati.model_dump())
    session.add(utente)
    await session.commit()
    await session.refresh(utente)
    # model_validate all'uscita (fatto implicitamente da response_model)
    return utente

@app.get("/utenti/", response_model=list[UtenteRisposta])
async def lista_utenti(
    limite: int = 10,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
):
    stmt = select(Utente).limit(limite).offset(offset)
    risultato = await session.scalars(stmt)
    return risultato.all()
```

### Field() — Validazioni avanzate

```python
from pydantic import BaseModel, Field
from typing import Annotated

class ProdottoSchema(BaseModel):
    nome: str = Field(..., min_length=2, max_length=200)
    prezzo: float = Field(..., gt=0, description="Prezzo in EUR")
    quantita: int = Field(default=0, ge=0)
    codice_sku: str = Field(
        ...,
        pattern=r"^[A-Z]{3}-\d{4}$",
        examples=["ABC-1234"],
    )
    tags: list[str] = Field(default_factory=list, max_length=10)

    model_config = ConfigDict(from_attributes=True)
```

---

## SQLite vs PostgreSQL — Strategia di Migrazione

### Differenze operative rilevanti

| Aspetto | SQLite | PostgreSQL |
|---|---|---|
| Concorrenza | Lock a livello di file (un solo writer) | MVCC, migliaia di writer concorrenti |
| ALTER TABLE | Limitato (no DROP COLUMN prima di 3.35.0) | Completo |
| Tipi | Tipizzazione debole (type affinity) | Tipizzazione forte |
| JSON | `json_extract()` | `jsonb`, operatori `->>`, `@>`, indici GIN |
| Full-text search | FTS5 (modulo esterno) | `tsvector` + `tsquery` nativi |
| Array | Non supportato | `ARRAY[]` nativo |
| ENUM | Non supportato | `CREATE TYPE ... AS ENUM` |
| Schema | Singolo schema | Multi-schema (`public`, custom) |

### Strategia per lo sviluppo locale con SQLite

```python
import os

def ottieni_engine():
    """Crea l'engine basato sull'ambiente."""
    database_url = os.environ.get("DATABASE_URL")

    if database_url:
        # Produzione: PostgreSQL
        return create_engine(database_url, pool_pre_ping=True, pool_size=10)

    # Sviluppo locale: SQLite
    return create_engine(
        "sqlite:///sviluppo.db",
        connect_args={"check_same_thread": False},
        echo=True,
    )
```

> **Attenzione:** usare SQLite in sviluppo e PostgreSQL in produzione puo mascherare bug legati a differenze di comportamento (tipizzazione, concorrenza, vincoli). Per test di integrazione, utilizzare sempre PostgreSQL (via Docker o testcontainers).

---

## Pattern Avanzati

### Unit of Work Esplicito

Il pattern Unit of Work è implementato nativamente dalla `Session` di SQLAlchemy, ma in applicazioni complesse può essere utile renderlo esplicito per separare il dominio dalla persistenza.

```python
from contextlib import contextmanager
from sqlalchemy.orm import Session

class UnitOfWork:
    """Unit of Work esplicito che gestisce il ciclo di vita della sessione."""
    
    def __init__(self, session_factory):
        self._session_factory = session_factory
    
    def __enter__(self):
        self.session: Session = self._session_factory()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
        self.session.close()
    
    def commit(self):
        try:
            self.session.commit()
        except Exception:
            self.rollback()
            raise
    
    def rollback(self):
        self.session.rollback()

# Uso nel service layer
class OrdineService:
    def __init__(self, uow_factory):
        self._uow_factory = uow_factory
    
    def crea_ordine(self, utente_id: int, prodotti: list[dict]) -> int:
        with self._uow_factory() as uow:
            utente = uow.session.get(Utente, utente_id)
            if not utente:
                raise ValueError(f"Utente {utente_id} non trovato")
            
            ordine = Ordine(utente_id=utente_id)
            for p in prodotti:
                riga = RigaOrdine(prodotto_id=p["id"], quantita=p["qty"])
                ordine.righe.append(riga)
            
            uow.session.add(ordine)
            uow.commit()
            return ordine.id
```

### Multi-tenancy con Schema Separation

Per applicazioni multi-tenant, SQLAlchemy supporta la separazione per schema PostgreSQL. Ogni tenant ha il proprio schema con le stesse tabelle, isolando completamente i dati.

```python
from sqlalchemy import event
from sqlalchemy.orm import Session

def set_tenant_schema(session: Session, tenant_id: str):
    """Imposta lo schema corrente per la sessione."""
    schema = f"tenant_{tenant_id}"
    session.execute(text(f"SET search_path TO {schema}, public"))

# Event listener per impostare lo schema automaticamente
@event.listens_for(Session, "after_begin")
def set_schema_on_begin(session, transaction, connection):
    tenant_id = get_current_tenant()  # da contesto (thread-local, context var)
    if tenant_id:
        connection.execute(text(f"SET search_path TO tenant_{tenant_id}, public"))

# Creare uno schema per un nuovo tenant
def provision_tenant(engine, tenant_id: str):
    schema = f"tenant_{tenant_id}"
    with engine.connect() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
        conn.execute(text(f"SET search_path TO {schema}"))
        # Creare le tabelle nello schema del tenant
        Base.metadata.create_all(conn)
        conn.commit()
```

### Event Sourcing con SQLAlchemy

Event sourcing memorizza ogni cambiamento di stato come un evento immutabile. SQLAlchemy può servire sia come storage per gli eventi che per le proiezioni (viste materializzate dello stato corrente).

```python
from datetime import datetime, UTC
from sqlalchemy import JSON

class DomainEvent(Base):
    __tablename__ = "domain_events"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    aggregate_type: Mapped[str] = mapped_column(String(100), index=True)
    aggregate_id: Mapped[str] = mapped_column(String(100), index=True)
    event_type: Mapped[str] = mapped_column(String(100))
    event_data: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    version: Mapped[int] = mapped_column(default=1)
    
    __table_args__ = (
        # Vincolo di unicità per optimistic concurrency
        UniqueConstraint("aggregate_type", "aggregate_id", "version"),
    )

class EventStore:
    def __init__(self, session: Session):
        self._session = session
    
    def append(self, aggregate_type: str, aggregate_id: str,
               event_type: str, data: dict, expected_version: int):
        event = DomainEvent(
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            event_type=event_type,
            event_data=data,
            version=expected_version + 1,
        )
        self._session.add(event)
        # IntegrityError se la versione è già stata usata (concurrent write)
    
    def get_events(self, aggregate_type: str, aggregate_id: str) -> list[DomainEvent]:
        stmt = (
            select(DomainEvent)
            .where(DomainEvent.aggregate_type == aggregate_type)
            .where(DomainEvent.aggregate_id == aggregate_id)
            .order_by(DomainEvent.version)
        )
        return list(self._session.execute(stmt).scalars())
```

---

## Database Testing

> Rif. testcontainers-python docs · factory_boy docs · faker docs

### Setup con testcontainers

Testcontainers avvia un container Docker con il database reale per i test, eliminando differenze tra test e produzione.

```python
# pip install testcontainers[postgres]
import pytest
from testcontainers.postgres import PostgresContainer
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

@pytest.fixture(scope="session")
def postgres_engine():
    """Engine PostgreSQL effimero per i test."""
    with PostgresContainer("postgres:16-alpine") as pg:
        engine = create_engine(pg.get_connection_url())
        Base.metadata.create_all(engine)
        yield engine
        engine.dispose()

@pytest.fixture
def session(postgres_engine):
    """Sessione con rollback automatico dopo ogni test."""
    with Session(postgres_engine) as session:
        with session.begin():
            yield session
            session.rollback()  # annulla tutto dopo il test
```

### Factory con factory_boy e faker

```python
# pip install factory-boy faker
import factory
from factory.alchemy import SQLAlchemyModelFactory

class UtenteFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Utente
        sqlalchemy_session = None  # iniettata dal fixture

    nome = factory.Faker("name", locale="it_IT")
    email = factory.LazyAttribute(
        lambda obj: f"{obj.nome.lower().replace(' ', '.')}@esempio.it"
    )
    eta = factory.Faker("random_int", min=18, max=80)
    attivo = True

class ArticoloFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Articolo
        sqlalchemy_session = None

    titolo = factory.Faker("sentence", nb_words=6, locale="it_IT")
    contenuto = factory.Faker("text", max_nb_chars=500, locale="it_IT")
    autore = factory.SubFactory(UtenteFactory)
    pubblicato = factory.Faker("boolean")

# Utilizzo nei test
def test_utente_con_articoli(session):
    UtenteFactory._meta.sqlalchemy_session = session
    ArticoloFactory._meta.sqlalchemy_session = session

    utente = UtenteFactory()
    articoli = ArticoloFactory.create_batch(5, autore=utente)

    assert len(utente.articoli) == 5
    assert all(a.autore_id == utente.id for a in articoli)
```

### Test asincroni

```python
# pip install pytest-asyncio
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

@pytest.fixture
async def async_session():
    engine = create_async_engine("sqlite+aiosqlite://", echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session

    await engine.dispose()

@pytest.mark.asyncio
async def test_crea_utente_async(async_session):
    utente = Utente(nome="Test Async", email="async@test.it")
    async_session.add(utente)
    await async_session.flush()

    assert utente.id is not None

    caricato = await async_session.get(Utente, utente.id)
    assert caricato.nome == "Test Async"
```

---

## Migrazioni — Best Practices Avanzate

### Convenzioni di naming

Alembic genera nomi per vincoli e indici basati sulle convenzioni configurate. Definire una naming convention esplicita garantisce nomi prevedibili e coerenti, necessari per i downgrade.

```python
from sqlalchemy import MetaData

# Naming convention globale
convenzione = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=convenzione)
```

### Data migration (migrazione dei dati)

Le data migration modificano i dati esistenti, non lo schema. Vanno separate dalle schema migration per chiarezza e reversibilita.

```python
"""migrazione dati: normalizza email a lowercase

Revision ID: c3d4e5f6a7b8
"""
from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    # Tabella temporanea per la migrazione
    utenti = sa.table("utenti", sa.column("id", sa.Integer), sa.column("email", sa.String))

    conn = op.get_bind()
    risultato = conn.execute(sa.select(utenti.c.id, utenti.c.email))

    for row in risultato:
        if row.email != row.email.lower():
            conn.execute(
                utenti.update()
                .where(utenti.c.id == row.id)
                .values(email=row.email.lower())
            )

def downgrade() -> None:
    # Le data migration spesso non sono reversibili
    pass
```

### Zero-downtime migrations

Per evitare downtime durante le migrazioni in produzione, seguire il pattern expand-and-contract:

1. **Expand:** aggiungere la nuova colonna come nullable, senza rimuovere la vecchia.
2. **Migrate data:** popolare la nuova colonna con i dati dalla vecchia.
3. **Switch code:** aggiornare il codice per leggere/scrivere dalla nuova colonna.
4. **Contract:** rimuovere la vecchia colonna (in una migrazione successiva).

```python
# Fase 1 — Expand: aggiungi nuova colonna
def upgrade_fase_1() -> None:
    op.add_column("utenti", sa.Column("email_nuovo", sa.String(150), nullable=True))

# Fase 2 — Migrate data
def upgrade_fase_2() -> None:
    op.execute("UPDATE utenti SET email_nuovo = LOWER(email)")

# Fase 3 — (deploy del codice che usa email_nuovo)

# Fase 4 — Contract: rimuovi vecchia colonna
def upgrade_fase_4() -> None:
    op.alter_column("utenti", "email_nuovo", nullable=False)
    op.create_unique_constraint("uq_utenti_email_nuovo", "utenti", ["email_nuovo"])
    op.drop_column("utenti", "email")
    op.alter_column("utenti", "email_nuovo", new_column_name="email")
```

---

## Performance — EXPLAIN ANALYZE e Indici

> Rif. PostgreSQL docs: *EXPLAIN* · *Index Types*

### Leggere un piano di esecuzione

```
                                                    QUERY PLAN
------------------------------------------------------------------------------------------------------------------
 Sort  (cost=156.34..158.84 rows=1000 width=72) (actual time=2.456..2.512 rows=1000 loops=1)
   Sort Key: count DESC
   Sort Method: quicksort  Memory: 100kB
   ->  HashAggregate  (cost=96.34..106.34 rows=1000 width=72) (actual time=1.234..1.890 rows=1000 loops=1)
         Group Key: u.nome
         ->  Hash Join  (cost=28.50..71.34 rows=5000 width=68) (actual time=0.123..0.890 rows=5000 loops=1)
               Hash Cond: (a.autore_id = u.id)
               ->  Seq Scan on articoli a  (cost=0.00..32.00 rows=5000 width=8) (actual time=0.005..0.234 rows=5000 loops=1)
                     Filter: (pubblicato = true)
               ->  Hash  (cost=16.00..16.00 rows=1000 width=68) (actual time=0.100..0.100 rows=1000 loops=1)
                     ->  Seq Scan on utenti u  (cost=0.00..16.00 rows=1000 width=68) (actual time=0.003..0.050 rows=1000 loops=1)
 Planning Time: 0.150 ms
 Execution Time: 2.600 ms
```

**Come leggere il piano:**
- **cost=X..Y**: X = costo di avvio, Y = costo totale (unita arbitrarie del planner).
- **rows**: numero stimato di righe (il planner stima, `actual` mostra il reale).
- **Seq Scan**: scansione sequenziale — l'intera tabella viene letta. Accettabile per tabelle piccole, problematico per tabelle grandi.
- **Index Scan / Index Only Scan**: usa un indice — molto piu efficiente per tabelle grandi con filtri selettivi.
- **Hash Join / Nested Loop / Merge Join**: strategia di join scelta dal planner.

### Tipi di indice in PostgreSQL

| Tipo | Uso principale | Esempio |
|---|---|---|
| **B-tree** (default) | Uguaglianza, range, ORDER BY | `WHERE eta > 25` |
| **Hash** | Solo uguaglianza esatta | `WHERE codice = 'ABC'` |
| **GIN** | Array, JSONB, full-text search | `WHERE tags @> '{"python"}'` |
| **GiST** | Geometria, range types, full-text | PostGIS, `tsquery` |
| **BRIN** | Dati fisicamente ordinati (timestamp) | `WHERE creato_il > '2026-01-01'` |

```python
from sqlalchemy import Index, text

class EventoLog(Base):
    __tablename__ = "eventi_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(index=True)
    tipo: Mapped[str] = mapped_column(String(50))
    payload: Mapped[dict] = mapped_column(type_=sa.JSON)

    __table_args__ = (
        # Indice B-tree composto
        Index("idx_tipo_timestamp", "tipo", "timestamp"),
        # Indice GIN su colonna JSONB (solo PostgreSQL)
        Index("idx_payload_gin", "payload", postgresql_using="gin"),
        # Indice parziale (solo righe con tipo = 'errore')
        Index(
            "idx_errori_recenti",
            "timestamp",
            postgresql_where=text("tipo = 'errore'"),
        ),
    )
```

### Monitoraggio query lente

```python
# Abilitare il logging delle query lente in SQLAlchemy
import logging

logging.basicConfig()
logger = logging.getLogger("sqlalchemy.engine")
logger.setLevel(logging.INFO)  # INFO mostra tutte le query, WARNING solo gli errori

# Evento per misurare il tempo delle query
from sqlalchemy import event
import time

@event.listens_for(engine, "before_cursor_execute")
def prima_esecuzione(conn, cursor, statement, parameters, context, executemany):
    conn.info["query_start_time"] = time.monotonic()

@event.listens_for(engine, "after_cursor_execute")
def dopo_esecuzione(conn, cursor, statement, parameters, context, executemany):
    durata = time.monotonic() - conn.info["query_start_time"]
    if durata > 0.5:  # soglia: 500ms
        logger.warning(f"Query lenta ({durata:.3f}s): {statement[:200]}")
```

---

## Sicurezza Database

### Query parametrizzate — sempre

La regola piu importante: non concatenare mai valori utente nelle query SQL. Questo vale per tutti i layer: raw SQL, Core e ORM.

```python
# SBAGLIATO a ogni livello
conn.execute(text(f"SELECT * FROM utenti WHERE nome = '{nome}'"))

# CORRETTO — raw SQL con bind parameters
conn.execute(text("SELECT * FROM utenti WHERE nome = :nome"), {"nome": nome})

# CORRETTO — Core
stmt = select(utenti).where(utenti.c.nome == nome)

# CORRETTO — ORM
stmt = select(Utente).where(Utente.nome == nome)
```

### Gestione sicura della stringa di connessione

```python
import os
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

# MAI hardcodare credenziali nel codice
# CORRETTO: variabili d'ambiente
database_url = os.environ["DATABASE_URL"]  # fallisce esplicitamente se manca

# Alternativa: costruire l'URL in modo sicuro
url = URL.create(
    drivername="postgresql+psycopg",
    username=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
    host=os.environ.get("DB_HOST", "localhost"),
    port=int(os.environ.get("DB_PORT", "5432")),
    database=os.environ["DB_NAME"],
)
engine = create_engine(url)
```

### SSL/TLS per connessioni al database

```python
# PostgreSQL con SSL
engine = create_engine(
    "postgresql+psycopg://utente:password@db.esempio.com/mio_db",
    connect_args={
        "sslmode": "verify-full",
        "sslrootcert": "/path/to/ca.crt",
        "sslcert": "/path/to/client.crt",
        "sslkey": "/path/to/client.key",
    },
)
```

### Principio del minimo privilegio

```sql
-- Utente per l'applicazione: solo CRUD sulle tabelle necessarie
CREATE USER app_user WITH PASSWORD '...';
GRANT CONNECT ON DATABASE mio_db TO app_user;
GRANT USAGE ON SCHEMA public TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO app_user;

-- Utente per le migrazioni: DDL completo
CREATE USER migration_user WITH PASSWORD '...';
GRANT ALL PRIVILEGES ON DATABASE mio_db TO migration_user;

-- Utente per i report: solo lettura
CREATE USER report_user WITH PASSWORD '...';
GRANT CONNECT ON DATABASE mio_db TO report_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO report_user;
```

---

## Troubleshooting

### Errori comuni e soluzioni

| Errore | Causa | Soluzione |
|---|---|---|
| `DetachedInstanceError` | Accesso a un attributo dopo la chiusura della sessione | Usare `expire_on_commit=False` o caricare i dati prima di chiudere |
| `MissingGreenlet` | Accesso lazy a relazione in contesto async | Usare `selectinload`/`joinedload` o `AsyncAttrs` |
| `TimeoutError` (pool) | Tutte le connessioni del pool sono in uso | Aumentare `pool_size`/`max_overflow` o verificare connessioni non rilasciate |
| `OperationalError: server closed the connection` | Connessione scaduta lato server | Abilitare `pool_pre_ping=True` e `pool_recycle` |
| `IntegrityError: duplicate key` | Violazione vincolo UNIQUE | Gestire con try/except o usare `ON CONFLICT` |
| `ProgrammingError: relation does not exist` | Tabella non creata o migrazione non applicata | Eseguire `alembic upgrade head` |
| `SAWarning: relationship expects a class or mapper argument` | Import circolare tra modelli | Usare stringhe per i riferimenti: `relationship("NomeClasse")` |
| N+1 queries (lentezza) | Lazy loading in un ciclo | Usare `selectinload`/`joinedload` nella query |

### Debug delle query generate

```python
# Abilitare echo sull'engine
engine = create_engine("...", echo=True)

# Oppure: compilare la query senza eseguirla
from sqlalchemy.dialects import postgresql

stmt = select(Utente).where(Utente.attivo == True)
print(stmt.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))
# SELECT utenti.id, utenti.nome, ... FROM utenti WHERE utenti.attivo = true
```

---

## FAQ

**D: Quando usare `session.flush()` vs `session.commit()`?**
R: `flush()` invia le modifiche al database (esegue INSERT/UPDATE/DELETE) ma non chiude la transazione. Utile per ottenere l'ID auto-generato prima del commit. `commit()` chiama `flush()` e poi conferma la transazione. Se qualcosa va storto dopo il flush ma prima del commit, il rollback annulla tutto.

**D: `expire_on_commit=False` e sicuro?**
R: Si, nella maggior parte dei casi. Senza questo flag, dopo il commit tutti gli attributi degli oggetti vengono invalidati e il prossimo accesso causa una nuova query (o un `DetachedInstanceError` se la sessione e chiusa). Con `expire_on_commit=False`, gli attributi restano accessibili ma potrebbero non riflettere modifiche fatte da altre sessioni o trigger. Per applicazioni web stateless (ogni request ha la sua sessione), e generalmente sicuro.

**D: Quando preferire `selectinload` a `joinedload`?**
R: `joinedload` genera un singolo JOIN SQL ed e ideale quando si carica un singolo oggetto con le sue relazioni. `selectinload` genera una seconda query con `WHERE id IN (...)` ed e preferibile quando si caricano molti oggetti, perche evita la duplicazione di righe che il JOIN causerebbe.

**D: Come gestire gli import circolari tra modelli?**
R: Usare stringhe per i riferimenti nelle relazioni (`relationship("Articolo")` anziché `relationship(Articolo)`) e importare i modelli in modo lazy. In alternativa, definire tutti i modelli nello stesso modulo o usare un modulo `models/__init__.py` che importa tutti i modelli.

**D: Come gestire le transazioni distribuite tra più database?**
R: SQLAlchemy non supporta nativamente le transazioni XA distribuite. Per operazioni cross-database, usare il pattern Saga: ogni operazione ha una compensazione definita. In alternativa, usare `Session.begin_nested()` per savepoint all'interno di una singola transazione. Per scenari complessi, considerare un orchestratore esterno (Temporal, Celery con task idempotenti) che coordina le scritture su database diversi con compensazione in caso di fallimento parziale.

**D: Qual è la differenza tra `Session.merge()` e `Session.add()`?**
R: `add()` inserisce un nuovo oggetto nella sessione; se un oggetto con la stessa chiave primaria esiste già nella identity map, solleva un errore. `merge()` prende un oggetto (anche detached o proveniente da un'altra sessione) e lo riconcilia con lo stato della sessione corrente: se un oggetto con la stessa PK esiste, ne aggiorna gli attributi; se non esiste, crea una nuova entry. `merge()` è utile per sincronizzare oggetti tra sessioni diverse o per reattaccare oggetti detached.

```python
# merge() per reattaccare un oggetto detached
utente_detached = Utente(id=42, nome="Mario Aggiornato")
utente_merged = session.merge(utente_detached)
# utente_merged è ora tracked dalla sessione
# Se id=42 esisteva, i suoi attributi sono aggiornati
# Se non esisteva, verrà inserito al commit
session.commit()
```

**D: Come implementare soft delete con SQLAlchemy 2.0?**
R: Aggiungere una colonna `deleted_at` (nullable `datetime`) e sovrascrivere le query di default con un filtro automatico. In SQLAlchemy 2.0, usare `do_orm_execute` event per iniettare il filtro.

```python
from sqlalchemy import event, DateTime
from sqlalchemy.orm import Session

class SoftDeleteMixin:
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, index=True
    )

    def soft_delete(self) -> None:
        self.deleted_at = datetime.now(UTC)

@event.listens_for(Session, "do_orm_execute")
def _apply_soft_delete_filter(execute_state):
    if execute_state.is_select and not execute_state.execution_options.get("include_deleted"):
        execute_state.statement = execute_state.statement.options(
            # Aggiunge WHERE deleted_at IS NULL automaticamente
        ).where(
            execute_state.bind_arguments.get("mapper").class_.deleted_at.is_(None)
        )
```

**D: Come ottimizzare le bulk insert con SQLAlchemy?**
R: Per inserimenti massivi (>10k righe), evitare `session.add_all()` che crea oggetti ORM per ogni riga. Preferire `session.execute(insert(Model), lista_dizionari)` che usa l'inserimento bulk a livello Core, bypassando l'overhead dell'ORM. Per PostgreSQL, `executemany_mode="values_plus_batch"` nel `create_engine()` genera un singolo INSERT con VALUES multipli, drasticamente più veloce.

```python
# LENTO: ORM per ogni riga (~300 righe/sec)
for data in dataset:
    session.add(Prodotto(**data))

# VELOCE: Core bulk insert (~50.000 righe/sec)
session.execute(
    insert(Prodotto),
    [{"nome": d["nome"], "prezzo": d["prezzo"]} for d in dataset]
)
session.commit()
```

**D: Come gestire i tipi PostgreSQL-specifici (ARRAY, JSONB, ENUM) in SQLAlchemy?**
R: SQLAlchemy fornisce tipi specifici nel modulo `sqlalchemy.dialects.postgresql`. Per JSONB, usare `JSONB` con indici GIN per query performanti. Per ARRAY, definire il tipo dell'elemento. Per ENUM, preferire `Enum` Python nativo con `native_enum=True`.

```python
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy import Enum as SAEnum
import enum

class StatoOrdine(enum.Enum):
    NUOVO = "nuovo"
    CONFERMATO = "confermato"
    SPEDITO = "spedito"

class Prodotto(Base):
    __tablename__ = "prodotti"
    id: Mapped[int] = mapped_column(primary_key=True)
    tags: Mapped[list[str]] = mapped_column(ARRAY(String), default=[])
    metadati: Mapped[dict] = mapped_column(JSONB, default={})
    stato: Mapped[StatoOrdine] = mapped_column(SAEnum(StatoOrdine), default=StatoOrdine.NUOVO)
```

**D: Come gestire i connection pool in ambienti con fork (Gunicorn, uWSGI)?**
R: Dopo un `fork()`, le connessioni del processo padre diventano inutilizzabili nel processo figlio. Usare l'evento `pool_events.connect` non è sufficiente. La soluzione è chiamare `engine.dispose()` dopo il fork, oppure configurare `pool_pre_ping=True` e `pool_recycle=300`. Con Gunicorn, usare il hook `post_fork` per disporre l'engine.

```python
# Gunicorn config (gunicorn.conf.py)
def post_fork(server, worker):
    from myapp.database import engine
    engine.dispose()

# Alternativa: NullPool (nessun pooling, una connessione per query)
# Utile in ambienti serverless (Lambda, Cloud Functions)
engine = create_engine("...", poolclass=NullPool)
```

**D: Quando usare `with_for_update()` e quali sono le alternative?**
R: `with_for_update()` aggiunge `SELECT ... FOR UPDATE` alla query, acquisendo un lock a livello di riga per prevenire letture concorrenti dirty. Utile per operazioni read-modify-write dove la consistenza è critica (es. aggiornamento saldo). L'alternativa è l'optimistic locking con una colonna `version_id`: SQLAlchemy verifica che la versione non sia cambiata al momento del commit, e solleva `StaleDataError` se un'altra sessione ha modificato la riga.

```python
# Pessimistic locking
stmt = select(Conto).where(Conto.id == conto_id).with_for_update()
conto = session.execute(stmt).scalar_one()
conto.saldo -= importo
session.commit()  # lock rilasciato al commit

# Optimistic locking (preferibile per bassa contention)
class Conto(Base):
    __tablename__ = "conti"
    id: Mapped[int] = mapped_column(primary_key=True)
    saldo: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    versione: Mapped[int] = mapped_column(default=0)
    __mapper_args__ = {"version_id_col": versione}
```

---

## Troubleshooting Avanzato

### Scenario 1: Memory leak con sessioni non chiuse

**Sintomi**: l'uso di memoria dell'applicazione cresce costantemente. Il garbage collector non riesce a liberare gli oggetti ORM.

**Causa**: sessioni che non vengono chiuse o che accumulano oggetti nella identity map. Ogni `session.add()` o query mantiene un riferimento all'oggetto nella sessione. Se la sessione vive troppo a lungo (es. sessione globale usata per tutta la vita dell'applicazione), la identity map cresce indefinitamente.

**Diagnosi**:
```python
# Verificare quanti oggetti sono nella sessione
print(f"Oggetti in sessione: {len(session.identity_map)}")
print(f"Oggetti nuovi: {len(session.new)}")
print(f"Oggetti modificati: {len(session.dirty)}")

# Con objgraph per analisi dettagliata
import objgraph
objgraph.show_most_common_types(limit=20)
```

**Soluzione**: usare sessioni scoped con lifecycle chiaro (una per request in web, una per task in batch). Chiamare `session.close()` o usare context manager. Per batch processing su grandi dataset, chiamare `session.expire_all()` periodicamente per liberare la identity map.

### Scenario 2: Deadlock tra transazioni concorrenti

**Sintomi**: `OperationalError: deadlock detected` in ambiente multi-thread o multi-processo.

**Causa**: due transazioni acquisiscono lock su righe in ordine inverso. Transazione A blocca riga 1 e attende riga 2; transazione B blocca riga 2 e attende riga 1.

**Soluzione**: (1) Ordinare le operazioni per chiave primaria all'interno di una transazione, in modo che tutte le transazioni acquisiscano i lock nello stesso ordine. (2) Ridurre la durata delle transazioni. (3) Usare `NOWAIT` o `SKIP LOCKED` per evitare attese.

```python
# Ordinare le update per ID per prevenire deadlock
ids_da_aggiornare = sorted([42, 17, 99])
for pid in ids_da_aggiornare:
    stmt = select(Prodotto).where(Prodotto.id == pid).with_for_update()
    prodotto = session.execute(stmt).scalar_one()
    prodotto.prezzo *= 1.1

# SKIP LOCKED per code di lavoro (job queue pattern)
stmt = (
    select(Task)
    .where(Task.stato == "pendente")
    .with_for_update(skip_locked=True)
    .limit(10)
)
tasks = session.execute(stmt).scalars().all()
```

### Scenario 3: Migrazione Alembic fallisce a metà

**Sintomi**: `alembic upgrade head` fallisce a metà di una migrazione. Il database è in uno stato parzialmente migrato. Rieseguire la migrazione fallisce perché alcune operazioni sono già state applicate.

**Soluzione**: (1) Mai fare DDL e DML nella stessa migrazione — PostgreSQL fa rollback del DDL, ma non tutti i database lo supportano. (2) Usare `op.execute()` con controlli condizionali. (3) Per recovery: identificare fino a quale punto la migrazione è arrivata, creare una migrazione correttiva che completa le operazioni mancanti o annulla quelle parziali.

```python
# Migrazione resiliente con check condizionali
def upgrade():
    conn = op.get_bind()
    # Verifica se la colonna esiste già (idempotente)
    result = conn.execute(text(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = 'prodotti' AND column_name = 'codice_sku'"
    ))
    if not result.fetchone():
        op.add_column("prodotti", sa.Column("codice_sku", sa.String(50)))
    
    # Data migration con batch per tabelle grandi
    conn.execute(text(
        "UPDATE prodotti SET codice_sku = 'SKU-' || id::text "
        "WHERE codice_sku IS NULL"
    ))
```

---

## Esercizi

### Esercizio 1 — Modelli ORM 2.0 (livello base)

Definire i seguenti modelli usando la sintassi SQLAlchemy 2.0 (`DeclarativeBase`, `Mapped`, `mapped_column`):
- `Categoria` (id, nome, descrizione, parent_id autoref)
- `Prodotto` (id, nome, prezzo Decimal, categoria_id FK, disponibile bool)
- `Recensione` (id, prodotto_id FK, autore str, voto int 1-5, testo, creato_il)

Configurare le relazioni bidirezionali e la naming convention. Creare le tabelle su un database SQLite e verificare lo schema con `.tables` e `.schema`.

### Esercizio 2 — Repository asincrono (livello intermedio)

Implementare un `RepositoryProdottiAsync` con i metodi:
- `cerca_per_categoria(categoria_id)` con `selectinload` delle recensioni
- `top_prodotti(n)` che restituisce gli N prodotti con voto medio piu alto (CTE o subquery)
- `aggiorna_prezzo(prodotto_id, nuovo_prezzo)` con validazione (prezzo > 0)

Scrivere test con `pytest-asyncio` e `aiosqlite`.

### Esercizio 3 — Migrazione Alembic (livello intermedio)

Partendo dai modelli dell'esercizio 1:
1. Inizializzare Alembic con `env.py` asincrono.
2. Generare la migrazione iniziale con `--autogenerate`.
3. Aggiungere una colonna `codice_sku` a `Prodotto` con data migration (generare codici per i prodotti esistenti).
4. Rinominare `Recensione.testo` in `Recensione.contenuto` (migrazione manuale).
5. Verificare che `upgrade` e `downgrade` funzionino in entrambe le direzioni.

### Esercizio 4 — Pydantic + SQLAlchemy (livello avanzato)

Creare un micro-servizio FastAPI con:
- Endpoint CRUD per `Prodotto` con schemi Pydantic v2 separati (Create, Update, Response).
- Validazioni con `Field()`: prezzo > 0, nome 2-200 caratteri, codice_sku con regex.
- `model_validate()` per la conversione ORM → Pydantic.
- Paginazione con parametri `limit` e `offset`.
- Test con `httpx.AsyncClient` e testcontainers PostgreSQL.

### Esercizio 5 — Performance analysis (livello avanzato)

Dato un database PostgreSQL con 100k prodotti e 500k recensioni:
1. Identificare il problema N+1 nella query "tutti i prodotti con le loro recensioni".
2. Risolvere con la strategia di loading appropriata.
3. Aggiungere indici per le query piu frequenti.
4. Usare `EXPLAIN ANALYZE` per confrontare i piani prima e dopo gli indici.
5. Documentare il miglioramento in termini di tempo di esecuzione.

---

## Checklist di Produzione per Database Python

Prima di mandare in produzione un'applicazione Python con database, verificare:

```
═══════════════════════════════════════════════════════════════
          PYTHON DATABASE PRODUCTION CHECKLIST
═══════════════════════════════════════════════════════════════

▸ CONNESSIONE E POOLING
  [ ] pool_pre_ping = True (verifica connessioni stale)
  [ ] pool_recycle = 1800 (ricrea connessioni ogni 30 min)
  [ ] pool_size adeguato al carico (non > max_connections/N_istanze)
  [ ] max_overflow configurato (burst temporanei)
  [ ] connect_args con timeout esplicito
  [ ] Stringa di connessione da variabile d'ambiente (mai hardcoded)
  [ ] SSL/TLS per connessioni remote (sslmode=verify-full)

▸ ORM E QUERY
  [ ] Nessun N+1: tutte le relazioni in loop usano eager loading
  [ ] Paginazione su tutte le query che restituiscono liste
  [ ] Indici creati per le colonne più filtrate/ordinate
  [ ] EXPLAIN ANALYZE verificato per le query critiche
  [ ] Nessuna query raw con concatenazione di stringhe (SQL injection)
  [ ] expire_on_commit=False se gli oggetti vengono usati dopo commit

▸ MIGRAZIONI
  [ ] Alembic configurato con env.py asincrono (se async)
  [ ] Naming convention per vincoli definita nel metadata
  [ ] Ogni migrazione testata con upgrade E downgrade
  [ ] Data migration separate da schema migration
  [ ] Migrazioni non distruttive (no DROP COLUMN senza deprecation)

▸ TESTING
  [ ] Test con PostgreSQL reale (testcontainers), non SQLite
  [ ] Factory per generazione dati di test (factory_boy)
  [ ] Test di concorrenza per operazioni critiche
  [ ] Test di migrazione su database con dati reali

▸ MONITORING
  [ ] Logging delle query lente (event listener o echo selettivo)
  [ ] Metriche del connection pool esportate (pool_size, overflow)
  [ ] OpenTelemetry tracing sulle query SQL
  [ ] Alert su errori di connessione e timeout

═══════════════════════════════════════════════════════════════
```

---

## Letture e Riferimenti

### Documentazione ufficiale

- SQLAlchemy 2.0 Documentation — *What's New in SQLAlchemy 2.0* · *ORM Mapped Class Configuration* · *Relationship Loading Techniques* · *Connection Pooling* — <https://docs.sqlalchemy.org/en/20/>
- Alembic Documentation — *Auto Generating Migrations* · *Running Alembic in an asyncio application* · *Operation Reference* — <https://alembic.sqlalchemy.org/en/latest/>
- Pydantic v2 Documentation — *model_validate* · *ConfigDict* · *Field* · *Types* — <https://docs.pydantic.dev/latest/>
- PostgreSQL Documentation — *EXPLAIN* · *Index Types* · *Transaction Isolation* — <https://www.postgresql.org/docs/current/>
- asyncpg Documentation — <https://magicstack.github.io/asyncpg/>
- testcontainers-python — <https://testcontainers-python.readthedocs.io/>
- factory_boy Documentation — <https://factoryboy.readthedocs.io/>

### PEP e standard

- PEP 249 — Python Database API Specification v2.0
- PEP 484 — Type Hints (fondamento per `Mapped[T]`)

### Libri

- *Architecture Patterns with Python* — Harry Percival, Bob Gregory (O'Reilly, 2020) — Repository pattern, Unit of Work, dependency injection con SQLAlchemy.
- *SQLAlchemy: Database Access Using Python* — Mark Ramm-Christensen, Michael Bayer — Dalla documentazione ufficiale.
- *High Performance PostgreSQL for Rails* — Andrew Atkinson (2024) — Indici, EXPLAIN, query optimization (applicabile anche a Python).

---

## Cross-link

| Modulo | Collegamento |
|---|---|
| Modulo 05 — Classi e OOP | Ereditarieta e mixin per i modelli ORM |
| Modulo 10 — Programmazione asincrona | `asyncio`, `TaskGroup`, event loop per Async SQLAlchemy |
| Modulo 11 — Web Framework | FastAPI dependency injection, endpoint con SQLAlchemy |
| Modulo 13 — REST API | Serializzazione Pydantic, validazione input, paginazione |
| Modulo 18 — Sicurezza | Gestione segreti, SQL injection prevention |
| Modulo 31 — Osservabilita | Tracing delle query SQL con OpenTelemetry |

---

## Glossario

| Termine | Definizione |
|---|---|
| **ACID** | Atomicita, Consistenza, Isolamento, Durabilita — proprieta delle transazioni in database relazionali |
| **Alembic** | Strumento di migrazione per SQLAlchemy; versiona lo schema del database |
| **AsyncSession** | Versione asincrona della `Session` SQLAlchemy, per contesti `async/await` |
| **Connection pooling** | Tecnica che mantiene un pool di connessioni riutilizzabili per evitare il costo di apertura/chiusura ripetuta |
| **CTE** | Common Table Expression — espressione tabellare temporanea definita con `WITH`, migliora la leggibilita delle query complesse |
| **DB-API 2.0** | Specifica Python (PEP 249) per l'interfacciamento con database relazionali |
| **DeclarativeBase** | Classe base SQLAlchemy 2.0 per il mapping dichiarativo dei modelli ORM |
| **Eager loading** | Caricamento delle relazioni nella stessa query (o in una query immediatamente successiva), opposto di lazy loading |
| **EXPLAIN ANALYZE** | Comando SQL che mostra il piano di esecuzione effettivo di una query con tempi reali |
| **Identity map** | Cache a livello di sessione che garantisce un'unica istanza Python per ogni riga del database |
| **Lazy loading** | Caricamento delle relazioni solo al momento del primo accesso all'attributo |
| **Mapped[T]** | Annotazione SQLAlchemy 2.0 che dichiara il tipo Python di un attributo ORM |
| **mapped_column()** | Funzione SQLAlchemy 2.0 che sostituisce `Column()` per la configurazione delle colonne ORM |
| **model_validate()** | Metodo Pydantic v2 che crea un'istanza validata da un oggetto Python (inclusi oggetti ORM con `from_attributes=True`) |
| **N+1 problem** | Antipattern dove si eseguono 1 query per la lista + N query per le relazioni di ogni elemento |
| **NullPool** | Pool SQLAlchemy che non mantiene connessioni; ogni operazione apre e chiude una connessione |
| **ORM** | Object-Relational Mapping — tecnica che mappa tabelle del database su classi Python |
| **pool_pre_ping** | Opzione SQLAlchemy che verifica la validita di una connessione prima di restituirla dal pool |
| **QueuePool** | Pool SQLAlchemy predefinito; mantiene connessioni in una coda FIFO con dimensione configurabile |
| **raiseload** | Strategia di loading che solleva un'eccezione se si accede a una relazione non caricata |
| **Repository pattern** | Pattern architetturale che astrae l'accesso ai dati dietro un'interfaccia, separando logica di business e persistenza |
| **Savepoint** | Punto di salvataggio all'interno di una transazione; consente rollback parziali senza annullare l'intera transazione |
| **selectinload** | Strategia di eager loading che esegue una seconda query con `WHERE id IN (...)` per caricare le relazioni |
| **Session** | Interfaccia principale dell'ORM SQLAlchemy per le operazioni sul database; implementa Unit of Work e Identity Map |
| **Unit of Work** | Pattern che raggruppa le operazioni in un'unita transazionale atomica |
| **Window function** | Funzione SQL che calcola valori su un set di righe correlate senza raggrupparle (`ROW_NUMBER()`, `RANK()`, `LAG()`) |
| **Bulk insert** | Inserimento massivo di righe usando operazioni Core (non ORM) per performance ottimali; bypassa la identity map |
| **Soft delete** | Cancellazione logica che marca un record come eliminato (colonna `deleted_at`) senza rimuoverlo fisicamente dal database |
| **Optimistic locking** | Controllo di concorrenza che usa una colonna `version` per rilevare modifiche concorrenti al momento del commit |
| **Pessimistic locking** | Controllo di concorrenza che acquisisce un lock esplicito sulla riga (`SELECT FOR UPDATE`) per prevenire accessi concorrenti |
| **Event sourcing** | Pattern architetturale che memorizza ogni cambiamento di stato come evento immutabile, ricostruendo lo stato corrente dalla sequenza di eventi |
| **Multi-tenancy** | Architettura che serve più clienti (tenant) dalla stessa applicazione, isolando i dati per schema, database o filtro a livello di riga |
| **Canonical Data Model** | Modello di dati standard interno a cui tutti i sistemi si mappano, disaccoppiando la logica di business dalla logica di integrazione |
| **UPSERT** | Operazione che inserisce una riga se non esiste o la aggiorna se esiste; in PostgreSQL implementata con `INSERT ... ON CONFLICT DO UPDATE` |
| **Savepoint nested** | Punto di salvataggio annidato all'interno di una transazione; in SQLAlchemy implementato con `session.begin_nested()` che crea un `SAVEPOINT` SQL |
| **Type annotation** | Annotazione di tipo Python (`Mapped[int]`, `Mapped[str | None]`) usata in SQLAlchemy 2.0 per definire il tipo delle colonne ORM in modo type-safe e verificabile da mypy |

---

> **Nota finale:** la scelta del database e dell'approccio di interazione dipende dalle esigenze specifiche del progetto. SQLite è perfetto per prototipi e applicazioni embedded, PostgreSQL è la scelta principale per applicazioni di produzione che richiedono robustezza e funzionalità avanzate, Redis eccelle come layer di caching, e MongoDB è ideale quando si necessita di flessibilità nello schema. SQLAlchemy, con il suo ORM e il layer Core, rimane la libreria di riferimento per l'ecosistema Python, offrendo un'astrazione potente senza sacrificare le prestazioni.
