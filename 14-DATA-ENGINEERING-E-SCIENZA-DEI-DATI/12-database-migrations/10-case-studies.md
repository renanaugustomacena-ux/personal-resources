# Database Migrations — Casi di Studio

## Case Study 1: Rinomina Colonna su Tabella da 50M Righe

**Contesto**: un'applicazione SaaS ha `users.full_name` (VARCHAR 255) che deve diventare `users.display_name` (VARCHAR 512) senza downtime.

**Timeline**:

```
Sprint 1 (Settimana 1):
V30__add_display_name.sql:
  ALTER TABLE users ADD COLUMN display_name VARCHAR(512);

V31__sync_trigger.sql:
  CREATE OR REPLACE FUNCTION sync_display() RETURNS TRIGGER AS $$
  BEGIN
      IF NEW.full_name IS NOT NULL THEN NEW.display_name = NEW.full_name; END IF;
      IF NEW.display_name IS NOT NULL THEN NEW.full_name = NEW.display_name; END IF;
      RETURN NEW;
  END; $$ LANGUAGE plpgsql;
  CREATE TRIGGER tr_sync_display
      BEFORE INSERT OR UPDATE ON users
      FOR EACH ROW EXECUTE FUNCTION sync_display();

Sprint 1 (Settimana 2) - Backfill asincrono:
V32__backfill_display_name.sql:
  DO $$ BEGIN
      LOOP
          UPDATE users SET display_name = full_name
          WHERE id IN (
              SELECT id FROM users WHERE display_name IS NULL LIMIT 10000
          );
          EXIT WHEN NOT FOUND;
          PERFORM pg_sleep(0.1);
      END LOOP;
  END; $$;

Sprint 2: codice v2 legge display_name, scrive su entrambi
Sprint 3: verifica tutte le istanze su v2
Sprint 4 (Settimana 6):
V33__drop_full_name.sql:
  DROP TRIGGER tr_sync_display ON users;
  DROP FUNCTION sync_display();
  ALTER TABLE users DROP COLUMN full_name;
```

**Risultato**: 6 settimane, zero downtime, nessun dato perso.

---

## Case Study 2: Migrazione da MySQL a PostgreSQL

**Contesto**: migrazione dell'intero database da MySQL 5.7 a PostgreSQL 15.

**Fase 1: Schema Translation** (1 settimana)

```python
# Differenze chiave MySQL → PostgreSQL
MYSQL_TO_PG_TYPES = {
    "TINYINT(1)": "BOOLEAN",
    "INT": "INTEGER",
    "BIGINT": "BIGINT",
    "FLOAT": "FLOAT4",
    "DOUBLE": "FLOAT8",
    "DATETIME": "TIMESTAMP",
    "TEXT": "TEXT",
    "LONGTEXT": "TEXT",
    "JSON": "JSONB",     # JSONB invece di JSON per indicizzabilità
    "ENUM(...)": "TEXT",  # o CREATE TYPE ... AS ENUM
}

# AUTO_INCREMENT → SERIAL o GENERATED ALWAYS AS IDENTITY
# UNSIGNED → CHECK constraint o use BIGINT
```

**Fase 2: Dual-Write** (2 settimane)

```python
class DualWriteRepository:
    """Scrive su MySQL (primario) e PostgreSQL (secondario) simultaneamente."""

    def create_order(self, order: dict) -> int:
        with mysql.begin() as m, postgres.begin() as p:
            # Scrivi su MySQL (autoritativo)
            result = m.execute("INSERT INTO orders ...", order)
            order_id = result.lastrowid

            # Scrivi su Postgres (replica write)
            p.execute("INSERT INTO orders ...", {**order, "id": order_id})

        return order_id

    def get_order(self, order_id: int) -> dict:
        # Legge ancora da MySQL durante questa fase
        return mysql.execute("SELECT * FROM orders WHERE id = ?", order_id).fetchone()
```

**Fase 3: Shadow Read** (1 settimana)

```python
import random

def get_order_with_shadow(order_id: int) -> dict:
    mysql_result = mysql.fetchone("SELECT * FROM orders WHERE id = ?", order_id)

    # 1% del traffico fa shadow read da Postgres per confronto
    if random.random() < 0.01:
        pg_result = postgres.fetchone("SELECT * FROM orders WHERE id = ?", order_id)
        if not compare_results(mysql_result, pg_result):
            logger.warning(f"Shadow read mismatch for order {order_id}")

    return mysql_result  # ritorna sempre il risultato MySQL
```

**Fase 4: Switchover** (1 giorno)

```
1. Blocca tutte le scritture su MySQL (manutenzione 5 minuti)
2. Verifica che Postgres sia allineato (count, checksum)
3. Aggiorna connection string a puntare a Postgres
4. Verifica smoke tests
5. Re-apri le scritture su Postgres
6. Disabilita dual-write
```

**Risultato**: 4 settimane di migrazione con 5 minuti di downtime controllato.

---

## Case Study 3: Aggiunta NOT NULL a Tabella Produttiva

**Problema**: `orders.email` deve diventare NOT NULL ma il 2% delle righe ha email = NULL.

```sql
-- Step 1: Conta righe con NULL
SELECT count(*) FROM orders WHERE email IS NULL;
-- Risultato: 48.203 righe su 2.4M

-- Step 2: Analizza perché sono NULL
SELECT created_at::date, count(*)
FROM orders WHERE email IS NULL
GROUP BY created_at::date
ORDER BY created_at::date;
-- Tutte le righe NULL risalgono a prima del 2021-03-15 (bug del vecchio sistema)

-- Step 3: Popola i NULL con dati recuperabili
UPDATE orders o
SET email = u.email
FROM users u
WHERE o.user_id = u.id
  AND o.email IS NULL;

-- Step 4: Per i rimasti senza email utente (guest orders)
UPDATE orders SET email = 'guest-' || id || '@legacy.internal'
WHERE email IS NULL;

-- Step 5: Verifica
SELECT count(*) FROM orders WHERE email IS NULL;
-- 0

-- Step 6: Aggiungi constraint NOT VALID (non valida storicamente, solo nuovi INSERT)
ALTER TABLE orders ADD CONSTRAINT orders_email_not_null
    CHECK (email IS NOT NULL) NOT VALID;

-- Step 7: Validate in background (non blocca DML)
ALTER TABLE orders VALIDATE CONSTRAINT orders_email_not_null;

-- Step 8: Converti in colonna NOT NULL
ALTER TABLE orders ALTER COLUMN email SET NOT NULL;
ALTER TABLE orders DROP CONSTRAINT orders_email_not_null;
```

---

## Case Study 4: Partizionamento di una Tabella Esistente

**Problema**: `events` da 1.8 miliardi di righe, query sempre più lente.

```sql
-- Step 1: Crea la nuova tabella partizionata
CREATE TABLE events_v2 (
    LIKE events INCLUDING ALL  -- copia schema esatto
) PARTITION BY RANGE (event_date);

-- Step 2: Crea partizioni per gli anni storici
DO $$
DECLARE
    y INT;
BEGIN
    FOR y IN 2020..2024 LOOP
        FOR m IN 1..12 LOOP
            EXECUTE format(
                'CREATE TABLE events_%s_%s PARTITION OF events_v2
                 FOR VALUES FROM (%L) TO (%L)',
                y, lpad(m::text, 2, '0'),
                make_date(y, m, 1),
                make_date(y, m, 1) + interval '1 month'
            );
        END LOOP;
    END LOOP;
END;
$$;

-- Step 3: Copia dati in batch per partizione
-- (eseguito durante ore di bassa attività, settimane di migrazione)
INSERT INTO events_v2
SELECT * FROM events WHERE event_date >= '2020-01-01' AND event_date < '2020-02-01';
-- ... ripeti per ogni mese

-- Step 4: Dual-write mentre il backfill continua
-- triggers su events che copiano su events_v2

-- Step 5: Switchover atomico (30 secondi di manutenzione)
BEGIN;
ALTER TABLE events RENAME TO events_old;
ALTER TABLE events_v2 RENAME TO events;
COMMIT;

-- Step 6: Monitoraggio
-- Le query con WHERE event_date = '...' ora beneficiano del partition pruning

-- Step 7: Drop della tabella vecchia (dopo 30 giorni di verifica)
DROP TABLE events_old;
```

**Risultato**: query da 45 secondi a 200ms dopo il partizionamento su dati del mese corrente.

---

## Lezioni Apprese

1. **Stima il tempo di migrazione PRIMA** — eseguire su un dump di produzione e misurare
2. **I trigger di sync sono costosi** — usarli solo per la durata della transizione
3. **Dual-write aumenta la latenza** — pianificare quanto può durare questa fase
4. **I checksum di riconciliazione salvano le vite** — sempre verificare dopo una migrazione dati
5. **Il rollback deve essere testato, non solo scritto** — un undo script non testato ha il 50% di probabilità di fallire quando serve

Le migrazioni di database sono una delle attività più ad alto rischio nell'ingegneria software — ma con la pianificazione corretta, diventano operazioni di routine prevedibili e sicure.
