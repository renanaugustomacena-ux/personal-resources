# Prevenzione delle SQL Injection

Le SQL injection sono la vulnerabilità più sfruttata nelle applicazioni web che usano database relazionali. Sono al primo posto della OWASP Top 10 da oltre un decennio. Un attacco di SQL injection può portare a: lettura di tutti i dati del database, modifica o cancellazione di dati, esecuzione di comandi sul sistema operativo, e escalation dei privilegi.

## Anatomia di una SQL Injection

```python
# Esempio classico di vulnerabilità
# L'applicazione costruisce la query concatenando input utente non validato

def get_user_VULNERABLE(username: str):
    # Se username = "admin' OR '1'='1"
    # Query risultante: SELECT * FROM users WHERE username = 'admin' OR '1'='1'
    # Risultato: TUTTI gli utenti vengono restituiti (perché '1'='1' è sempre vero)
    query = f"SELECT * FROM users WHERE username = '{username}'"
    return db.execute(query).fetchall()

def login_VULNERABLE(username: str, password: str):
    # Se username = "admin'--"
    # Query risultante: SELECT * FROM users WHERE username = 'admin'-- AND password = '...'
    # Il -- commenta il controllo della password: LOGIN SENZA PASSWORD
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    return db.execute(query).fetchone()

def search_products_VULNERABLE(category: str):
    # Se category = "'; DROP TABLE products;--"
    # Query: SELECT * FROM products WHERE category = ''; DROP TABLE products;--'
    # DISTRUZIONE DEI DATI
    query = f"SELECT * FROM products WHERE category = '{category}'"
    return db.execute(query).fetchall()
```

## Parametrizzazione: La Soluzione Fondamentale

La parametrizzazione è la difesa principale e non ha alternative valide. Separa il codice SQL dai dati: i parametri non vengono mai interpretati come SQL.

```python
import psycopg2
from psycopg2.extras import RealDictCursor
import sqlalchemy
from sqlalchemy import text, select
from sqlalchemy.orm import Session

# === Python con psycopg2 ===

# CORRETTO: parametri come secondo argomento
def get_user_safe(conn, username: str):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            "SELECT id, name, email FROM users WHERE username = %s",
            (username,)  # tupla con parametri
        )
        return cur.fetchone()

def login_safe(conn, username: str, password_hash: str):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, role FROM users WHERE username = %s AND password_hash = %s",
            (username, password_hash)
        )
        return cur.fetchone()

def search_products_safe(conn, category: str, min_price: float, max_price: float):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT id, name, price, category
            FROM products
            WHERE category = %s
              AND price BETWEEN %s AND %s
            ORDER BY price
            """,
            (category, min_price, max_price)
        )
        return cur.fetchall()

# Query con parametri multipli di tipo diverso
def create_order(conn, user_id: int, items: list, shipping_address: str):
    with conn.cursor() as cur:
        # Inserimento con RETURNING per recuperare l'ID generato
        cur.execute(
            """
            INSERT INTO orders (user_id, shipping_address, status, created_at)
            VALUES (%s, %s, 'pending', NOW())
            RETURNING id
            """,
            (user_id, shipping_address)
        )
        order_id = cur.fetchone()[0]
        
        # Inserimento batch: usare executemany
        order_items = [(order_id, item['product_id'], item['quantity']) for item in items]
        cur.executemany(
            "INSERT INTO order_items (order_id, product_id, quantity) VALUES (%s, %s, %s)",
            order_items
        )
        
        return order_id


# === SQLAlchemy Core ===

def get_products_by_category(engine, category: str):
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT * FROM products WHERE category = :category"),
            {"category": category}  # parametri come dict con :nome
        )
        return result.fetchall()

# === SQLAlchemy ORM (più sicuro: parametrizza automaticamente) ===

def get_active_users(db: Session, min_age: int = 18):
    return db.query(User).filter(
        User.is_active == True,
        User.age >= min_age  # SQLAlchemy parametrizza automaticamente
    ).all()
```

## Identificatori Dinamici (Table/Column Names)

I driver database non supportano la parametrizzazione per nomi di tabelle, colonne, o altri identificatori SQL. Qui la soluzione è la whitelist.

```python
from typing import Literal

# Whitelist per colonne di ordinamento
ALLOWED_SORT_COLUMNS = {'name', 'created_at', 'price', 'status', 'id'}
ALLOWED_SORT_DIRECTIONS = {'ASC', 'DESC'}

# Whitelist per nomi tabella
ALLOWED_TABLES = {'products', 'users', 'orders', 'categories'}

def get_records_sorted(
    conn,
    table: str,
    sort_by: str,
    direction: str = 'ASC',
    limit: int = 100
):
    # Validare OGNI identificatore contro la whitelist
    if table not in ALLOWED_TABLES:
        raise ValueError(f"Tabella non autorizzata: {table!r}")
    if sort_by not in ALLOWED_SORT_COLUMNS:
        raise ValueError(f"Colonna di ordinamento non autorizzata: {sort_by!r}")
    if direction.upper() not in ALLOWED_SORT_DIRECTIONS:
        raise ValueError(f"Direzione non autorizzata: {direction!r}")
    
    # Ora è sicuro costruire la query (identificatori validati)
    # Il limit è un parametro normale
    query = f"SELECT * FROM {table} ORDER BY {sort_by} {direction} LIMIT %s"
    
    with conn.cursor() as cur:
        cur.execute(query, (limit,))
        return cur.fetchall()

# Per psycopg2: usare sql.Identifier per quotare correttamente
from psycopg2 import sql

def get_column_stats(conn, table_name: str, column_name: str):
    # Validare prima
    if table_name not in ALLOWED_TABLES:
        raise ValueError(f"Tabella non autorizzata: {table_name!r}")
    if column_name not in ALLOWED_SORT_COLUMNS:
        raise ValueError(f"Colonna non autorizzata: {column_name!r}")
    
    # sql.Identifier gestisce il quoting corretto anche per nomi con spazi/caratteri speciali
    query = sql.SQL("SELECT MIN({col}), MAX({col}), AVG({col}) FROM {table}").format(
        col=sql.Identifier(column_name),
        table=sql.Identifier(table_name)
    )
    
    with conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchone()
```

## Stored Procedures: Sicurezza e Limitazioni

Le stored procedure parametrizzate sono sicure contro le SQL injection, ma hanno le proprie vulnerabilità se costruiscono SQL dinamico internamente.

```sql
-- SICURO: stored procedure con parametri
CREATE OR REPLACE FUNCTION get_user_orders(p_user_id INT, p_status TEXT DEFAULT NULL)
RETURNS TABLE(order_id INT, total NUMERIC, created_at TIMESTAMPTZ) AS $$
BEGIN
  RETURN QUERY
    SELECT o.id, o.total_amount, o.created_at
    FROM orders o
    WHERE o.user_id = p_user_id  -- parametro sicuro
      AND (p_status IS NULL OR o.status = p_status);  -- parametro sicuro
END;
$$ LANGUAGE plpgsql;

-- VULNERABILE: stored procedure con EXECUTE e concatenazione
CREATE OR REPLACE FUNCTION search_table_VULNERABLE(p_table TEXT, p_value TEXT)
RETURNS VOID AS $$
BEGIN
  -- PERICOLOSO: p_table e p_value vengono interpolati nella stringa SQL
  EXECUTE 'SELECT * FROM ' || p_table || ' WHERE name = ''' || p_value || '''';
END;
$$ LANGUAGE plpgsql;

-- SICURO: stored procedure con SQL dinamico usa quote_ident e quote_literal
CREATE OR REPLACE FUNCTION search_table_safe(p_table TEXT, p_value TEXT)
RETURNS VOID AS $$
BEGIN
  -- quote_ident: escapa il nome della tabella
  -- quote_literal: escapa il valore stringa
  EXECUTE 'SELECT * FROM ' || quote_ident(p_table) || ' WHERE name = ' || quote_literal(p_value);
END;
$$ LANGUAGE plpgsql;

-- MEGLIO: usare format() con %I (identifier) e %L (literal)
CREATE OR REPLACE FUNCTION search_table_best(p_table TEXT, p_value TEXT)
RETURNS VOID AS $$
BEGIN
  EXECUTE format('SELECT * FROM %I WHERE name = %L', p_table, p_value);
  -- %I: quote_ident automatico
  -- %L: quote_literal automatico
  -- %s: solo per valori numerici o già validati
END;
$$ LANGUAGE plpgsql;
```

## Validazione dell'Input a Livello Applicativo

La parametrizzazione è necessaria ma non sufficiente. La validazione dell'input fornisce un layer aggiuntivo di difesa.

```python
from pydantic import BaseModel, validator, constr, confloat, conint
from typing import Optional
import re

class ProductSearchRequest(BaseModel):
    """Schema Pydantic per la ricerca prodotti con validazione rigorosa."""
    
    category: constr(min_length=1, max_length=100, pattern=r'^[a-zA-Z0-9\s\-_]+$')
    # Solo lettere, numeri, spazi, trattini, underscore
    
    min_price: confloat(ge=0.0, le=1_000_000.0)
    max_price: confloat(ge=0.0, le=1_000_000.0)
    
    sort_by: Literal['name', 'price', 'created_at'] = 'name'
    sort_dir: Literal['asc', 'desc'] = 'asc'
    
    limit: conint(ge=1, le=100) = 20
    offset: conint(ge=0) = 0
    
    @validator('max_price')
    def max_price_greater_than_min(cls, v, values):
        if 'min_price' in values and v < values['min_price']:
            raise ValueError('max_price deve essere maggiore di min_price')
        return v

class UserSearchRequest(BaseModel):
    """Ricerca utenti con pattern sicuri."""
    
    # Nomi possono contenere lettere unicode, spazi, apostrofi, trattini
    name: Optional[constr(min_length=1, max_length=100, 
                          pattern=r"^[\w\s\'\-\.àáâãäåæçèéêëìíîïðñòóôõöùúûüýÿ]+$")]
    
    email: Optional[constr(
        min_length=3,
        max_length=254,
        # Regex base per email (non completo ma sufficiente)
        pattern=r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    )]

# FastAPI endpoint con validazione automatica
from fastapi import FastAPI

app = FastAPI()

@app.get("/products/search")
def search_products(params: ProductSearchRequest):
    # params è già validato da Pydantic
    # I valori sono sicuri da passare alla query parametrizzata
    products = db_search_products(
        category=params.category,
        min_price=params.min_price,
        max_price=params.max_price,
        sort_by=params.sort_by,
        limit=params.limit,
        offset=params.offset
    )
    return products
```

## Second-Order SQL Injection

La second-order injection è più insidiosa: i dati vengono prima memorizzati "sicuri" nel database e poi usati in modo non sicuro in una query successiva.

```python
# Scenario: un utente registra il suo username come: admin'--
# La registrazione è sicura (parametrizzata):
def register_user(username: str):
    db.execute("INSERT INTO users (username) VALUES (%s)", (username,))
    # OK: "admin'--" viene memorizzato come stringa letterale

# Il problema emerge quando il username viene riusato in modo non sicuro:
def change_password_VULNERABLE(username: str, new_password: str):
    # Il username viene recuperato dal database... sembra "sicuro"
    user = db.execute("SELECT username FROM users WHERE id = %s", (current_user_id,))
    db_username = user[0]
    
    # MA viene usato senza parametrizzazione nella nuova query!
    # Se db_username = "admin'--"
    # Query: UPDATE users SET password = '...' WHERE username = 'admin'-- AND ...
    # Modifica la password di admin, non dell'utente corrente!
    query = f"UPDATE users SET password = '{new_password}' WHERE username = '{db_username}'"
    db.execute(query)  # VULNERABILE

# SOLUZIONE: parametrizzare SEMPRE, anche quando il valore viene dal database
def change_password_safe(user_id: int, new_password: str):
    # Non riusare mai valori da database in query non parametrizzate
    db.execute(
        "UPDATE users SET password_hash = %s WHERE id = %s",
        (hash_password(new_password), user_id)
    )
```

## Testing per SQL Injection

```python
# Test automatico per vulnerabilità di SQL injection
import pytest
from app.db import get_user

SQLI_PAYLOADS = [
    "' OR '1'='1",
    "'; DROP TABLE users; --",
    "' UNION SELECT username, password FROM users --",
    "admin'--",
    "' AND 1=1 --",
    "1; SELECT pg_sleep(10) --",  # time-based blind injection
    "' OR 1=1 --",
    "1' OR '1'='1",
]

@pytest.mark.parametrize("payload", SQLI_PAYLOADS)
def test_no_sql_injection_in_login(payload):
    """Nessun payload di injection deve restituire risultati o causare errori."""
    result = get_user(username=payload)
    # Con parametrizzazione corretta, nessun payload restituisce dati reali
    assert result is None, f"SQL injection payload {payload!r} ha restituito dati"

@pytest.mark.parametrize("payload", SQLI_PAYLOADS)
def test_search_resilient_to_injection(payload):
    """La ricerca deve essere sicura contro injection."""
    # Non deve sollevare eccezioni (che rivelerebbero la struttura del DB)
    # Non deve restituire più risultati del previsto
    try:
        results = search_products(category=payload)
        assert isinstance(results, list)
        # Verificare che non siano stati restituiti dati di altre categorie
    except ValueError:
        pass  # Validazione bloccata prima della query: OK
```

