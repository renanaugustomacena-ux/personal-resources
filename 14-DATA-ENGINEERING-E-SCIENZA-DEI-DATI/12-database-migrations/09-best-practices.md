# Database Migrations — Best Practices

## Principi Fondamentali

### 1. Un Commit per Migrazione

Ogni migrazione deve essere un commit atomico e separato nel repository. Non mescolare modifiche al codice applicativo con le migrazioni nello stesso commit se possono essere deployate indipendentemente.

```
git log --oneline migrations/
abc123 V20__add_customer_segments_table
def456 V19__add_email_verified_column
ghi789 V18__backfill_display_name
jkl012 V17__add_display_name_column
```

### 2. Mai Modificare Script già Applicati

Una volta che una migrazione è stata applicata (anche solo in sviluppo o staging), **non modificarla mai**. Flyway e Liquibase verificano il checksum — una modifica causerà un fallimento al prossimo `migrate`.

Se hai commesso un errore:
1. Crea una **nuova migrazione** che corregge l'errore
2. Usa `flyway repair` o `liquibase clearCheckSums` solo come ultima risorsa

### 3. Idempotenza dove Possibile

```sql
-- Sì: CREATE IF NOT EXISTS, ADD COLUMN IF NOT EXISTS
CREATE TABLE IF NOT EXISTS events (...);
ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_url TEXT;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email ON users(email);

-- No: statement che fallisce se rieseguito
CREATE TABLE events (...);           -- fallisce se esiste
ALTER TABLE users ADD COLUMN url TEXT;  -- fallisce se esiste
```

### 4. Lock Timeout Esplicito

```sql
-- Imposta sempre un lock_timeout per evitare deadlock che bloccano l'applicazione
SET lock_timeout = '5s';
SET statement_timeout = '300s';

ALTER TABLE orders ADD COLUMN notes TEXT;
-- Se qualcuno tiene un lock aperto su orders, la migrazione aborterà dopo 5s
-- invece di aspettare indefinitamente
```

### 5. Separare Schema Changes da Data Changes

```sql
-- SBAGLIATO: schema + data in una migrazione
ALTER TABLE users ADD COLUMN tier VARCHAR(20);
UPDATE users SET tier = 'free';  -- può durare ore su tabelle grandi

-- CORRETTO: due migrazioni separate
-- V10__add_tier_column.sql (rapida)
ALTER TABLE users ADD COLUMN tier VARCHAR(20);

-- V11__backfill_tier.sql (lenta, ma isolata)
UPDATE users SET tier = 'free' WHERE tier IS NULL;
```

---

## Anti-Pattern da Evitare

### Anti-Pattern 1: DROP senza Fase di Transizione

```sql
-- SBAGLIATO: droppare immediatamente una colonna usata dal codice
ALTER TABLE users DROP COLUMN legacy_field;
-- Il codice ancora usa legacy_field → crash immediato in produzione

-- CORRETTO: seguire il processo expand-contract
-- 1. Rimuovi l'uso della colonna dal codice
-- 2. Deploya
-- 3. Poi droppa la colonna in una migrazione successiva
```

### Anti-Pattern 2: Constraint NOT NULL su Colonne Esistenti Senza Backfill

```sql
-- SBAGLIATO: constraint immediato
ALTER TABLE orders ADD COLUMN notes TEXT NOT NULL;
-- Fallisce se ci sono righe senza notes (default = NULL)

-- CORRETTO
ALTER TABLE orders ADD COLUMN notes TEXT;      -- step 1: nullable
UPDATE orders SET notes = '' WHERE notes IS NULL;  -- step 2: backfill
ALTER TABLE orders ALTER COLUMN notes SET NOT NULL; -- step 3: constraint
ALTER TABLE orders ALTER COLUMN notes SET DEFAULT '';  -- step 4: default per nuove righe
```

### Anti-Pattern 3: Migration con Logica Applicativa

```sql
-- SBAGLIATO: calcola prezzi nella migrazione con logica di business
UPDATE orders SET total = subtotal + (subtotal * tax_rate / 100);
-- Cambio della logica fiscale = devi modificare la migrazione (impossibile)

-- CORRETTO: la migrazione aggiunge struttura, l'applicazione calcola
-- la migrazione aggiunge la colonna senza default
-- il codice applicativo la popola al momento corretto
```

### Anti-Pattern 4: Migrazioni Giganti

```sql
-- SBAGLIATO: una migrazione con 50 ALTER TABLE
-- Se fallisce a metà, rollback complicato e stato inconsistente

-- CORRETTO: migrazioni piccole e atomiche
-- V10: aggiunge una tabella
-- V11: aggiunge indice alla tabella
-- V12: aggiunge FK
-- Ogni migrazione ha un singolo scopo
```

---

## Workflow per Ambienti Multipli

```
local dev:
  flyway migrate        (applica manualmente dopo ogni pull)
  
staging:
  CI/CD applica migrazioni automaticamente prima del deploy
  
production:
  Pipeline applica migrazioni in finestra di deployment
  Health check post-migrazione
  Rollback automatico se smoke test falliscono
```

```yaml
# Configurazione per ambiente
flyway.conf:
  flyway.placeholderPrefix=$[
  flyway.placeholders.environment=production

V5__add_index.sql:
  -- Solo in produzione, saltato in ambienti con pochi dati
  -- flyway: conditionalOn="$[environment] == 'production'"
  CREATE INDEX CONCURRENTLY idx_orders_user ON orders(user_id);
```

---

## Checklist per Ogni Migrazione

**Progettazione**:
- [ ] La migrazione fa una sola cosa (principio di single responsibility)
- [ ] Lo script undo è definito e testato
- [ ] I dati critici sono preservati o backuppati prima di DELETE/UPDATE
- [ ] Tabelle grandi usano batch per DML, CONCURRENTLY per indici

**Review**:
- [ ] Lock timeout impostato esplicitamente
- [ ] Nessuna dipendenza dal codice applicativo (la migrazione è autonoma)
- [ ] Compatibile backward con la versione precedente del codice

**Testing**:
- [ ] Eseguita su DB di staging con dati simili alla produzione in volume
- [ ] Schema post-migrazione corrisponde all'atteso
- [ ] Undo testato e funzionante
- [ ] Durata misurata e accettabile

**Post-Deploy**:
- [ ] `flyway info` mostra tutte le migrazioni come SUCCESS
- [ ] Smoke test applicativi passano
- [ ] Nessun aumento anomalo di error rate nei log
- [ ] Replication lag rientrato nella norma

Le migrazioni sono il contrato tra il codice e il database. Trattarle con la stessa attenzione del codice di produzione — review, test, versionamento, documentazione — è la differenza tra un sistema che evolve con fiducia e uno che cambia con paura.
