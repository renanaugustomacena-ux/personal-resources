# Database Replication — Replica Sincrona e Asincrona

## Il Tradeoff Fondamentale

Il parametro più critico di qualsiasi sistema di replica è la **modalità di commit**: la transazione sul primario viene considerata committata prima o dopo che le repliche abbiano confermato la ricezione?

Questa scelta determina il tradeoff tra **consistenza** (le repliche hanno sempre i dati) e **latenza** (quanto velocemente le write vengono confermate all'applicazione).

---

## Replica Asincrona

Il primario committa la transazione localmente e risponde al client **immediatamente**, senza aspettare la conferma delle repliche. Le repliche ricevono i dati in background.

```
T1: Client → Primario: BEGIN; INSERT INTO orders ...; COMMIT;
T2: Primario → Client: "OK, commit confirmed"
T3: (background) Primario → Replica: trasmette i WAL record
T4: Replica: applica la transazione
```

**Gap di durabilità**: nel periodo T2-T4, se il primario crasha, i dati sono persi anche se il client ha ricevuto conferma.

### Configurazione PostgreSQL (Asincrono)

```properties
# postgresql.conf sul primario
wal_level = replica            # Minimum per streaming replication
max_wal_senders = 10           # Max connessioni da repliche
wal_keep_size = 1GB            # Quanti WAL tenere per le repliche in lag

# Asincrono è il DEFAULT in PostgreSQL
# Non specificare synchronous_standby_names → asincrono
```

```bash
# pg_hba.conf sul primario
host replication replication_user 192.168.1.0/24 md5

# recovery.conf (PG < 12) o postgresql.conf (PG >= 12) sulla replica
primary_conninfo = 'host=primary port=5432 user=replication_user password=secret'
primary_slot_name = 'replica1_slot'  # replication slot
```

### Replication Slot

I **replication slot** garantiscono che il primario non elimini i WAL record finché la replica non li ha consumati.

```sql
-- Crea replication slot sul primario
SELECT pg_create_physical_replication_slot('replica1_slot');

-- Lista dei slot e loro lag
SELECT slot_name, active, restart_lsn,
       pg_current_wal_lsn() - restart_lsn AS bytes_retained
FROM pg_replication_slots;

-- ATTENZIONE: se una replica va offline con un slot attivo,
-- il primario accumula WAL indefinitamente → disco pieno!
-- Imposta un limite di sicurezza:
-- max_slot_wal_keep_size = 10GB
```

---

## Replica Sincrona

Il primario **aspetta** che la replica abbia ricevuto (o applicato) i WAL record prima di confermare il commit al client.

```
T1: Client → Primario: COMMIT
T2: Primario → Replica: trasmette WAL
T3: Replica → Primario: "ho ricevuto/applicato fino a LSN X"
T4: Primario → Client: "OK, commit confirmed"
```

**Zero data loss**: se il primario crasha dopo T4, la replica ha già i dati.

**Costo**: latenza aggiuntiva ≈ RTT rete (tipicamente 1-5ms su LAN, 50-200ms su WAN).

### Livelli di Sincronia in PostgreSQL

```properties
# postgresql.conf sul primario

# synchronous_commit determina quando rispondere al client:
# off: commit locale, risposta immediata (asincrono)
# local: commit locale + fsync locale
# remote_write: replica ha scritto in memoria (non su disco)
# on: replica ha eseguito fsync (scritto su disco)    ← DEFAULT sicuro
# remote_apply: replica ha applicato la transazione (disponibile per letture)

synchronous_commit = on  # default

# Quale replica deve confermare?
synchronous_standby_names = 'replica1'
# oppure: 'FIRST 1 (replica1, replica2)' → il più veloce tra i due
# oppure: 'ANY 1 (replica1, replica2)' → almeno uno
# oppure: 'FIRST 2 (r1, r2, r3)' → i due più veloci tra tre
```

```python
# Per transazioni specifiche: override per-query
conn.execute("SET synchronous_commit = off")  # per questa connessione
conn.execute("INSERT INTO audit_logs ...")     # asincrono (ok per audit logs)
conn.execute("SET synchronous_commit = on")
conn.execute("INSERT INTO orders ...")         # sincrono (critico)
```

---

## Semi-Sincrono in MySQL

MySQL offre una modalità **semi-sincrona** che è un compromesso:
- Il primario aspetta che **almeno una** replica abbia ricevuto (non necessariamente applicato) i dati nel suo relay log
- Non aspetta la conferma dell'applicazione (più veloce del sincrono pieno)

```bash
# Installazione plugin
INSTALL PLUGIN rpl_semi_sync_source SONAME 'semisync_source.so';
INSTALL PLUGIN rpl_semi_sync_replica SONAME 'semisync_replica.so';

# Configurazione primario
SET GLOBAL rpl_semi_sync_source_enabled = 1;
SET GLOBAL rpl_semi_sync_source_timeout = 10000;  # ms di attesa prima di fallback asincrono
SET GLOBAL rpl_semi_sync_source_wait_for_replica_count = 1;  # almeno 1 replica

# Configurazione replica
SET GLOBAL rpl_semi_sync_replica_enabled = 1;
```

**Fallback automatico**: se nessuna replica risponde entro il timeout, MySQL passa automaticamente ad asincrono. Il sistema degrada gracefully ma non garantisce più durabilità.

---

## Consistenza delle Letture: Read-Your-Writes

Un'applicazione che scrive sul primario e poi legge da una replica potrebbe vedere dati vecchi (stale read):

```python
# Problema: write sul primario, read sulla replica asincrona
conn_primary = get_primary_connection()
conn_replica = get_replica_connection()

conn_primary.execute("UPDATE users SET balance = 1000 WHERE id = 42")
conn_primary.commit()

# Possibile read stale se la replica non ha ancora ricevuto la write
balance = conn_replica.execute("SELECT balance FROM users WHERE id = 42").scalar()
# Potrebbe restituire il vecchio valore!
```

### Soluzioni

**1. Routing write-aware**:

```python
class SmartConnectionPool:
    def get_connection(self, intent: str = "read"):
        if intent == "write":
            return primary_connection
        if self.recently_wrote(seconds=1):
            # Dopo una write, leggi dal primario per 1 secondo
            return primary_connection
        return replica_connection

    def execute_write(self, query, params):
        conn = self.get_connection("write")
        result = conn.execute(query, params)
        self.mark_recent_write()
        return result
```

**2. Wait for replica con LSN**:

```sql
-- Sul primario, dopo la write
SELECT pg_current_wal_lsn() AS my_lsn;
-- Restituisce: 0/15B3A28C

-- Sulla replica, aspetta che abbia raggiunto quell'LSN
SELECT pg_wal_lsn_diff(pg_last_wal_replay_lsn(), '0/15B3A28C') >= 0;
-- Polling finché non è True, poi esegui la read
```

**3. Synchronous Commit per write critiche**:

```python
# Solo per operazioni dove read-your-writes è essenziale
with conn_primary.begin():
    conn_primary.execute("SET synchronous_commit = remote_apply")
    conn_primary.execute("UPDATE users SET ...")
    conn_primary.execute("SET synchronous_commit = on")
# Dopo il commit, la write è applicata sulla replica
# Possiamo leggere dalla replica immediatamente
```

---

## Confronto Modalità

| Modalità | Data Loss | Latenza Write | Complessità |
|----------|-----------|--------------|-------------|
| Asincrona | Possibile (RPO > 0) | Minima | Bassa |
| Semi-sincrona | Quasi zero | +1 RTT LAN | Media |
| Sincrona (remote_write) | Zero sul crash disk | +1 RTT rete | Media |
| Sincrona (on/fsync) | Zero (crash network ok) | +1 RTT + fsync | Media |
| Sincrona (remote_apply) | Zero + read-your-writes | +1 RTT + apply time | Alta |
| Multi-master (Galera) | Zero | +2 RTT (quorum) | Alta |

**Regola pratica**:
- **OLTP normale**: asincrona + monitoring del lag
- **Dati finanziari/critici**: sincrona a `on` con replica in stesso datacenter
- **Multi-region**: asincrona (latenza WAN troppo alta per sincrona piena)
- **Compliance/no data loss assoluto**: sincrona con due repliche (`FIRST 1 (r1, r2)`)

La scelta del modello di sincronia è una decisione di architettura che impatta ogni transazione dell'applicazione. Va presa consapevolmente, non lasciata al default del database.
