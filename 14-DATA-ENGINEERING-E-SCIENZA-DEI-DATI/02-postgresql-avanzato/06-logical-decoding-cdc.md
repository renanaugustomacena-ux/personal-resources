# PostgreSQL Logical Decoding e CDC

> Autori: Team Data Encyclopedia  
> Ultimo aggiornamento: 2026-05-04  
> Versione: 1.0.0  
> Stato: draft

## Skip list
- [ ] Bozza iniziale
- [ ] Review tecnica
- [ ] Formattazione
- [ ] Pubblicazione

## Indice
1. Logical Decoding Fundamentals
2. Output Plugins
3. Create Publication e Subscription
4. SQL Interface per Decoding
5. Replication Slot Management
6. WAL Decoder Tools
7. Change Data Capture Patterns
8. Debezium Integration
9. Performance Considerations
10. Monitoring e Troubleshooting

---

## 1. Logical Decoding Fundamentals

### 1.1 Cos'è Logical Decoding

Il **Logical Decoding** è il processo che legge il Write-Ahead Log (WAL) e lo converte in un flusso di modifiche comprensibili a livello di singole righe e operazioni DML. A differenza della replica fisica che copia i dati a livello di byte, il logical decoding opera a livello logico, permettendo di estrarre le modifiche in un formato strutturato.

**Come funziona**: Quando le modifiche vengono applicate al database, vengono registrate nel WAL in un formato interno. Il logical decoding legge questo WAL e, usando un output plugin, lo converte in un formato comprensibile - tipicamente JSON, Avro, o un flusso di eventi che può essere consumato da sistemi esterni.

**Componenti chiave**:
- **Replication Slot**: Traccia la posizione nel WAL e mantiene le modifiche non ancora consumate
- **Output Plugin**: Trasforma le modifiche dal formato interno a un formato di output (JSON, etc.)
- **SQL Interface**: Funzioni per leggere e gestire le modifiche

### 1.2 Logical vs Physical Decoding

Le differenze tra i due approcci sono fondamentali:

**Physical Decoding**:
- Replica l'intero cluster a livello di byte
- Copia esattamente tutti i file del database
- Non permette filtraggio o trasformazione
- Utile per disaster recovery e high availability
- Non richiede configurazione a livello di tabella

**Logical Decoding**:
- Opera a livello di singole tabelle e operazioni DML
- Può filtrare quali tabelle includere
- Può trasformare i dati durante la replica
- Permette replica selettiva (solo alcune tabelle)
- Richiede configurazione di pubblicazioni

### 1.3 Use Cases

Il Logical Decoding abilita diversi scenari avanzati:

**Change Data Capture (CDC)**: Estrarre le modifiche alle tabelle in tempo reale per alimentare altri sistemi - data warehouse, cache, sistemi di analytics, altri database.

```sql
-- CDC: le modifiche vengono lette e inviate a Kafka, etc.
SELECT * FROM pg_logical_slot_get_changes('my_slot', NULL, 'include-xids', '1');
```

**Audit Logging**: Tenere traccia di tutte le modifiche ai dati per compliance, sicurezza, o debugging.

```sql
-- Logging completo di tutte le modifiche
CREATE TABLE audit_log AS SELECT * FROM pg_logical_slot_get_changes('audit_slot', NULL, 'include-xids', '1');
```

**Data Synchronization**: Sincronizzare dati tra database - multi-master, operational analytics, caching.

**Event Sourcing**: Trattare le modifiche come eventi per applicazioni event-driven.

**Database Migration**: Estrarre dati da un database PostgreSQL e caricarli in un altro (anche un database diverso).

---

## 2. Output Plugins

### 2.1 Built-in Plugins

PostgreSQL include diversi plugin di output:

**test_decoding**: Plugin di test e debug. Produce output testuale semplice che mostra le modifiche in modo leggibile. Utile per verificare che il decoding funzioni.

```sql
-- Installare test_decoding
-- È incluso in contrib, richiede:
-- CREATE EXTENSION test_decoding;

-- Usare il plugin
SELECT * FROM pg_logical_slot_get_changes('slot_name', NULL, 'pretty-print', '1');
```

**wal2json**: Converte le modifiche in formato JSON. Molto popolare per CDC perché JSON è facile da consumare in applicazioni moderne.

```sql
-- Installare wal2json
-- Richiede: CREATE EXTENSION wal2json;

-- Output JSON delle modifiche
SELECT * FROM pg_logical_slot_get_changes('my_slot', NULL, 'pretty-print', '1');
```

**pgoutput**: Il plugin standard usato dalla replica logica di PostgreSQL. Produce un formato binario che PostgreSQL sa consumare per le subscriptions.

### 2.2 pgoutput

pgoutput è il plugin usato internamente da PostgreSQL per la replica logica:

```sql
-- Quando si crea una SUBSCRIPTION, usa automaticamente pg_output
CREATE SUBSCRIPTION my_sub 
CONNECTION 'host=primary dbname=mydb user=replicator'
PUBLICATION my_publication;
```

Non viene tipicamente usato direttamente - le subscriptions gestiscono tutto automaticamente.

### 2.3 wal2json

wal2json è il plugin più usato per CDC:

```sql
-- Output base
SELECT * FROM pg_logical_slot_get_changes('slot', NULL, NULL, NULL);

-- Opzioni
-- pretty-print: formato più leggibile
-- include-xids: include transaction ID
-- include-schemas: include schema name
-- include-types: include tipo di operazione

SELECT * FROM pg_logical_slot_get_changes(
    'slot', 
    NULL, 
    'pretty-print', 
    'include-xids', 
    '1'
);
```

**Esempio output**:
```json
{
  "change": [
    {
      "kind": "insert",
      "schema": "public",
      "table": "users",
      "columnnames": ["id", "name", "email"],
      "columntypes": ["integer", "varchar", "varchar"],
      "columnvalues": [1, "John", "john@example.com"]
    }
  ]
}
```

### 2.4 Custom Plugins

È possibile creare plugin personalizzati:

```c
// Struttura base di un plugin (esempio concettuale)
typedef struct OutputPluginCallbacks {
    void (*startup_cb)(OutputPluginOptions *options, bool is_truncate);
    void (*begin_cb)(TransactionId xid, TimestampTz ts);
    void (*change_cb)(LogicalDecodingChange *ctx);
    void (*commit_cb(TransactionId xid, XLogRecPtr commit_lsn);
} OutputPluginCallbacks;
```

**Tipi di plugin custom**:
- Formati specifici (Avro, Protobuf, CSV)
- Filtraggio avanzato
- Transformazioni
- Integrazione con sistemi specifici

---

## 3. Create Publication e Subscription

### 3.1 Publications

Le **Publications** definiscono quali modifiche sono disponibili per la replica logica:

```sql
-- Publication per tabelle specifiche
CREATE PUBLICATION sales_publication FOR TABLE 
    orders, 
    order_items, 
    customers;

-- Publication per tutte le tabelle
CREATE PUBLICATION all_tables FOR ALL TABLES;

-- Publication con opzioni
CREATE PUBLICATION selective_pub FOR TABLE 
    users, 
    products
WITH (publish = 'insert, update, delete');

-- Publication per tabelle con filtri
CREATE PUBLICATION active_users FOR TABLE users 
    WHERE status = 'active';
```

**Opzioni disponibili**:
- publish: quali operazioni includere (insert, update, delete, truncate)
- publish_via_partition_root: come gestire tabelle partizionate

### 3.2 Subscriptions

Le **Subscriptions** configurano il receiver della replica logica:

```sql
-- Creare subscription
CREATE SUBSCRIPTION sales_sub
CONNECTION 'host=10.0.0.1 port=5432 dbname=sales user=replicator password=secret'
PUBLICATION sales_publication;

-- Subscription con opzioni
CREATE SUBSCRIPTION my_sub
CONNECTION 'host=primary dbname=mydb user=replicator'
PUBLICATION my_pub
WITH (create_slot = true, slot_name = 'my_slot', synchronous_commit = off);
```

**Gestione subscription**:
```sql
-- Disabilitare temporaneamente
ALTER SUBSCRIPTION my_sub DISABLE;

-- Abilitare
ALTER SUBSCRIPTION my_sub ENABLE;

-- Rimuovere
DROP SUBSCRIPTION my_sub;

-- Sincronizzare dati iniziali
ALTER SUBSCRIPTION my_sub REFRESH PUBLICATION;
```

Creare subscription:
```sql
CREATE SUBSCRIPTION mysub 
CONNECTION 'host=remote port=5432 dbname=db user=rep password=pass'
PUBLICATION mypub;
```

### 3.3 Refresh

Refresh subscription:
```sql
ALTER SUBSCRIPTION mysub REFRESH PUBLICATION;
```

### 3.4 Drop

Rimuovere:
```sql
DROP SUBSCRIPTION mysub;
DROP PUBLICATION mypub;
```

---

## 4. SQL Interface per Decoding

### 4.1 pg_logical_slot_get_changes

Leggere changes:
```sql
SELECT * FROM pg_logical_slot_get_changes(
    'slot_name',
    NULL, -- start LSN
    NULL  -- end LSN
);
```

### 4.2 pg_logical_slot_peek_changes

Peek without consuming:
```sql
SELECT * FROM pg_logical_slot_peek_changes(
    'slot_name',
    NULL,
    'include-xids', '1'
);
```

### 4.3 Options

Opzioni disponibili:
- pretty-print
- include-xids
- include-timestamp
- force-binary

### 4.4 Consuming

Consuming:
```sql
-- Dopo lettura, slot avanzato
SELECT * FROM pg_logical_slot_get_changes('slot', NULL, 'include-xids', '1');
```

---

## 5. Replication Slot Management

### 5.1 Create Slot

Creare slot:
```sql
SELECT pg_create_logical_replication_slot('slot_name', 'wal2json');
```

### 5.2 List Slots

Vedere slot:
```sql
SELECT * FROM pg_replication_slots;
```

### 5.3 Drop Slot

Rimuovere slot:
```sql
SELECT pg_drop_replication_slot('slot_name');
```

### 5.4 Advance Slot

Avanzare slot manualmente:
```sql
SELECT pg_replication_slot_advance('slot_name', '0/12345678');
```

---

## 6. WAL Decoder Tools

### 6.1 test_decoding

Test decoding:
```sql
-- Abilitare
wal_level = logical
-- Usare slot con test_decoding
```

### 6.2 wal2json

JSON output:
```sql
SELECT data FROM pg_logical_slot_peek_changes('slot', NULL, 'format', 'json');
```

### 6.3 Decodable Operations

Operazioni tracciabili:
- INSERT
- UPDATE (old and new values)
- DELETE (old values)
- TRUNCATE

### 6.4 Non-Decodable

Non tracciato:
- DDL (non di default)
- Sequences
- System tables

---

## 7. Change Data Capture Patterns

### 7.1 Event-Driven Architecture

CDC pattern:
- Source DB -> WAL -> Decoder -> Kafka
- Consumers processano events

### 7.2 Outbox Pattern

Outbox pattern:
- Write to table + outbox table
- Transactional outbox
- Process outbox -> publish

### 7.3 Dual Write Problem

Evitare dual write:
- Single source of truth
- Transactional boundaries
- Idempotent consumers

### 7.4 Schema Evolution

Evoluzione schema:
- Schema compatibility
- Backward/forward compatibility
- Schema registry

---

## 8. Debezium Integration

### 8.1 Debezium

Debezium per CDC:
- Open source
- Multiple connectors
- Kafka Connect integration

### 8.2 PostgreSQL Connector

Connector PostgreSQL:
- Logical decoding
- Snapshot mode
- WAL position tracking

### 8.3 Configuration

Configurazione connector:
```json
{
  "name": "postgres-connector",
  "config": {
    "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
    "database.hostname": "localhost",
    "database.port": "5432",
    "database.user": "debezium",
    "database.password": "dbz123",
    "database.dbname": "inventory",
    "publication.name": "dbz_publication",
    "plugin.name": "pgoutput"
  }
}
```

### 8.4 Topics

Topics per tabella:
- Multiple topics (default)
- Single topic per prefix
- Transactional boundaries

---

## 9. Performance Considerations

### 9.1 Slot Lag

Monitorare lag:
```sql
SELECT slot_name, restart_lsn, confirmed_flush_lsn
FROM pg_replication_slots;
```

### 9.2 Impact on Primary

Impatto su primary:
- WAL generation increase
- Memory per slot
- I/O for consumption

### 9.3 Optimization

Ottimizzare:
- Consume frequently
- Appropriate slot retention
- Filter unwanted changes

### 9.4 Best Practices

Best practices:
- Multiple slots per app
- Monitor lag
- Test failure scenarios

---

## 10. Monitoring e Troubleshooting

### 10.1 pg_stat_replication

Monitor:
```sql
SELECT * FROM pg_stat_replication;
```

### 10.2 Slot Monitoring

Slot lag:
```sql
SELECT 
    slot_name,
    pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) as retained_wal,
    pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), confirmed_flush_lsn)) as lag
FROM pg_replication_slots;
```

### 10.3 Common Issues

Problemi comuni:
- Slot not consumed
- WAL accumulation
- Consumer errors

### 10.4 Troubleshooting Steps

Risoluzione:
1. Check slot lag
2. Restart consumer
3. Recreate slot if needed

---

*Questo documento fa parte del modulo 02 "PostgreSQL Avanzato" della Data Encyclopedia.*