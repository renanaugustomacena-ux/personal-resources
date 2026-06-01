# Best Practice per la Replica Database

Questa sezione distilla i principi operativi per costruire sistemi di replica affidabili, manutenibili e sicuri. Le best practice sono suddivise per area di competenza: design, configurazione, operazioni, e sicurezza.

## Principi di Design

### Scegliere il livello di sincronismo corretto

Il primo e più impattante decisione è il livello di sincronismo: asincrono, semi-sincrono, o sincrono. Non esiste una risposta universale: dipende dal trade-off tra performance e durabilità richiesto dall'applicazione.

```
┌─────────────────────────────────────────────────────────────────────┐
│ DECISION TREE: Scelta del livello di sincronismo                     │
│                                                                      │
│ Posso perdere transazioni?                                           │
│    └─ NO → Sincrono o Semi-sincrono                                  │
│         ├─ Il lag del commit è accettabile (< 10ms)?                 │
│         │    └─ SÌ → Sincrono (synchronous_commit=remote_apply)      │
│         │    └─ NO → Semi-sincrono (remote_write o on)               │
│    └─ SÌ → Asincrono                                                 │
│         ├─ Quanto posso perdere?                                      │
│         │    └─ < 1s → WAL archiving con archive_timeout=60          │
│         │    └─ < 1 binlog file → MySQL semi-sync                    │
│         │    └─ Libero → Puramente asincrono                         │
└─────────────────────────────────────────────────────────────────────┘
```

### Evitare la dipendenza da un singolo punto di failure

La replica non è sufficiente se il percorso di routing ha SPOF (Single Point of Failure). L'architettura completa deve essere ridondante:

```
SBAGLIATO:                    CORRETTO:
                               
App → DB (single node)        App → HAProxy/ProxySQL (pair) → DB Primary
                                                             → DB Replica1
                                                             → DB Replica2

App → HAProxy (single) → DB   App → HAProxy1 ─┐
                               App → HAProxy2 ─┴→ DB Primary + Replicas
```

### Dimensionare i replication slot con attenzione

I replication slot sono la feature più pericolosa di PostgreSQL se usati senza controllo. Un consumer che smette di consumare (es. un Debezium che crashs) può bloccare il sistema trattenendo WAL illimitatamente fino all'esaurimento del disco.

```sql
-- SEMPRE impostare wal_max_replication_slots con un limite ragionevole
-- NON usare slot permanenti per consumer che possono stare offline a lungo

-- Configurare la retention massima dei WAL per slot inattivi
ALTER SYSTEM SET max_slot_wal_keep_size = '10GB';
SELECT pg_reload_conf();

-- Monitorare i slot ogni giorno (alert se WAL_retained > 5GB)
SELECT
  slot_name,
  pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) AS retained_wal,
  active,
  slot_type
FROM pg_replication_slots
WHERE pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn) > 5*1024*1024*1024;

-- Se un consumer è offline da più di X ore, droppare il suo slot
-- meglio perdere la posizione del consumer che perdere tutto il disco
DO $$
DECLARE
  slot RECORD;
BEGIN
  FOR slot IN
    SELECT slot_name, pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn) AS retained_bytes
    FROM pg_replication_slots
    WHERE NOT active
      AND pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn) > 5*1024*1024*1024  -- 5GB
  LOOP
    RAISE WARNING 'Dropping inactive slot % (retained % bytes)', slot.slot_name, slot.retained_bytes;
    PERFORM pg_drop_replication_slot(slot.slot_name);
  END LOOP;
END;
$$;
```

## Configurazione

### Configurare correttamente i parametri WAL

```ini
# postgresql.conf: parametri WAL per replica affidabile

# Livello minimo per la replica streaming
wal_level = replica           # 'minimal' non supporta la replica

# Numero massimo di sender (connessioni replica simultanee)
max_wal_senders = 10          # 2x il numero di repliche previste

# Slot di replica massimi
max_replication_slots = 10    # include slot per logical replication

# Mantenere WAL anche se nessun receiver è connesso
# Evita che il primario elimini WAL prima che la replica si riconnetta
wal_keep_size = 1024          # MB; aumentare per repliche che possono andare offline

# Checkpoint
checkpoint_completion_target = 0.9   # distribuire l'I/O dei checkpoint
checkpoint_timeout = 300             # massimo 5 minuti tra checkpoint
max_wal_size = 4GB                   # dimensione massima WAL prima di forzare checkpoint
min_wal_size = 1GB

# Hints per pg_rewind (necessario per reintegrare vecchi primari come standby)
wal_log_hints = on

# Archiviazione WAL (per PITR e repliche ritardate)
archive_mode = on
archive_command = 'pgbackrest --stanza=main archive-push %p'
archive_timeout = 60         # massimo 60s senza archiviare (limita RPO)
```

### Configurare il pg_hba.conf in modo sicuro

```
# pg_hba.conf: autenticazione replica sicura

# SBAGLIATO: permettere la replica da qualsiasi host
host replication all 0.0.0.0/0 trust

# CORRETTO: IP specifici, utente dedicato, autenticazione forte
hostssl replication replicator 192.168.1.11/32 scram-sha-256
hostssl replication replicator 192.168.1.12/32 scram-sha-256

# Utente dedicato solo per la replica (senza accesso ai dati)
# Creare in PostgreSQL:
-- CREATE USER replicator REPLICATION LOGIN ENCRYPTED PASSWORD 'strong_password';
```

### Impostare i timeout appropriati

```ini
# Evitare che connessioni zombie blocchino il failover

# postgresql.conf
wal_receiver_timeout = 60000          # ms; terminare se il sender non risponde
wal_sender_timeout = 60000            # ms; terminare se il receiver non risponde
tcp_keepalives_idle = 60              # secondi di idle prima di keepalive
tcp_keepalives_interval = 10          # intervallo tra keepalive
tcp_keepalives_count = 5              # numero di keepalive prima di drop

# recovery.conf (o postgresql.conf in PG 12+)
recovery_min_apply_delay = 0          # 0 = applica subito; aumentare per replica ritardata
```

## Operazioni

### Runbook per la manutenzione della replica

```bash
#!/bin/bash
# maintenance-checklist.sh: pre-manutenzione replica

echo "=== Pre-manutenzione replica: $(date -u '+%Y-%m-%dT%H:%M:%SZ') ==="

# 1. Stato corrente del cluster
echo "--- Stato cluster ---"
patronictl -c /etc/patroni/patroni.yml list

# 2. Lag di replica corrente
echo "--- Lag replica ---"
psql -U postgres -c "
SELECT
  client_addr,
  state,
  sent_lsn,
  write_lsn,
  flush_lsn,
  replay_lsn,
  pg_wal_lsn_diff(sent_lsn, replay_lsn) AS lag_bytes,
  write_lag,
  flush_lag,
  replay_lag
FROM pg_stat_replication;
"

# 3. Slot di replica e WAL trattenuto
echo "--- Slot di replica ---"
psql -U postgres -c "
SELECT
  slot_name,
  slot_type,
  active,
  pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) AS wal_retained
FROM pg_replication_slots;
"

# 4. Spazio disco
echo "--- Spazio disco ---"
df -h /var/lib/postgresql/data
du -sh /var/lib/postgresql/data/pg_wal

# 5. Connessioni attive (evitare manutenzione durante picchi)
echo "--- Connessioni attive ---"
psql -U postgres -c "
SELECT COUNT(*), state
FROM pg_stat_activity
GROUP BY state
ORDER BY count DESC;
"

echo "=== Check completato - procedere con la manutenzione ==="
```

### Promuovere una replica in modo sicuro

```bash
# Prima di promuovere: verificare che il lag sia zero
LAG=$(psql -h replica -U postgres -t -c "
SELECT EXTRACT(EPOCH FROM (NOW() - pg_last_xact_replay_timestamp()))::integer;
")

if [ "$LAG" -gt 5 ]; then
    echo "ATTENZIONE: Lag di ${LAG}s. Attendere prima di promuovere."
    exit 1
fi

echo "Lag: ${LAG}s - OK per promozione"

# Verificare che nessuna transazione sia in attesa di replica
psql -h primary -U postgres -c "
SELECT COUNT(*)
FROM pg_stat_replication
WHERE replay_lsn < sent_lsn;
"

# Solo se il lag è accettabile, procedere con la promozione
# (via Patroni per ambienti gestiti, pg_ctl promote per emergenze)
```

### Reinserire un vecchio primario come standby

```bash
# Dopo un failover, il vecchio primario ha WAL divergenti
# pg_rewind riconcilia le differenze in modo efficiente

# Verificare che pg_rewind sia applicabile
# Prerequisiti: wal_log_hints=on O data_checksums abilitato

# Fermare il vecchio primario (se ancora in esecuzione)
pg_ctl stop -D /var/lib/postgresql/data

# Eseguire pg_rewind
pg_rewind \
  --target-pgdata=/var/lib/postgresql/data \
  --source-server="host=nuovo-primario port=5432 user=postgres" \
  --progress

# Configurare come standby
cat > /var/lib/postgresql/data/postgresql.auto.conf << 'EOF'
primary_conninfo = 'host=nuovo-primario port=5432 user=replicator password=password'
EOF

touch /var/lib/postgresql/data/standby.signal

# Avviare come standby
pg_ctl start -D /var/lib/postgresql/data
```

## Sicurezza

### Crittografia della replica in transito

```bash
# PostgreSQL: replica con SSL/TLS

# 1. Generare i certificati (CA auto-firmata per ambiente interno)
# In produzione: usare una CA aziendale o Let's Encrypt
openssl req -new -x509 -days 365 -nodes \
  -subj "/CN=PostgreSQL CA" \
  -keyout /etc/postgresql/ssl/ca-key.pem \
  -out /etc/postgresql/ssl/ca-cert.pem

# Certificato per il server (primario)
openssl req -new -nodes \
  -subj "/CN=primary.example.com" \
  -keyout /etc/postgresql/ssl/server-key.pem \
  -out /etc/postgresql/ssl/server-csr.pem

openssl x509 -req -days 365 \
  -in /etc/postgresql/ssl/server-csr.pem \
  -CA /etc/postgresql/ssl/ca-cert.pem \
  -CAkey /etc/postgresql/ssl/ca-key.pem \
  -CAcreateserial \
  -out /etc/postgresql/ssl/server-cert.pem

# Certificato per il client (replicatore)
openssl req -new -nodes \
  -subj "/CN=replicator" \
  -keyout /etc/postgresql/ssl/client-key.pem \
  -out /etc/postgresql/ssl/client-csr.pem

openssl x509 -req -days 365 \
  -in /etc/postgresql/ssl/client-csr.pem \
  -CA /etc/postgresql/ssl/ca-cert.pem \
  -CAkey /etc/postgresql/ssl/ca-key.pem \
  -CAcreateserial \
  -out /etc/postgresql/ssl/client-cert.pem

# 2. Configurare PostgreSQL per richiedere SSL
# postgresql.conf
ssl = on
ssl_cert_file = '/etc/postgresql/ssl/server-cert.pem'
ssl_key_file = '/etc/postgresql/ssl/server-key.pem'
ssl_ca_file = '/etc/postgresql/ssl/ca-cert.pem'

# pg_hba.conf: richiedere SSL per la replica
hostssl replication replicator 192.168.1.11/32 scram-sha-256 clientcert=verify-full

# 3. Configurare il receiver (standby)
# postgresql.conf o recovery.conf
primary_conninfo = 'host=primary port=5432 user=replicator password=secret
  sslmode=verify-full
  sslcert=/etc/postgresql/ssl/client-cert.pem
  sslkey=/etc/postgresql/ssl/client-key.pem
  sslrootcert=/etc/postgresql/ssl/ca-cert.pem'
```

### Principio del minimo privilegio per la replica

```sql
-- Utente dedicato con solo i permessi necessari
-- NON usare l'utente superuser per la replica

-- PostgreSQL
CREATE USER replicator
  REPLICATION
  LOGIN
  ENCRYPTED PASSWORD 'strong_random_password_here'
  CONNECTION LIMIT 5;  -- limitare il numero di connessioni simultanee
-- Non concedere accesso ad alcun database: l'utente REPLICATION
-- ha già i permessi necessari per la streaming replication

-- Per la logical replication (Debezium, etc.)
CREATE USER debezium_user
  LOGIN
  ENCRYPTED PASSWORD 'strong_random_password_here'
  REPLICATION;  -- necessario per creare slot di replica logica

GRANT CONNECT ON DATABASE mydb TO debezium_user;
GRANT USAGE ON SCHEMA public TO debezium_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO debezium_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT ON TABLES TO debezium_user;
-- NON concedere INSERT/UPDATE/DELETE: l'utente deve solo leggere
```

## Anti-pattern da Evitare

### Anti-pattern 1: Leggere dalla replica senza awareness del lag

```python
# SBAGLIATO: assumere che la replica sia aggiornata
def get_user_after_update(user_id):
    update_user(user_id, new_data)  # scrive sul primario
    return get_user(user_id)        # legge dalla replica (potrebbe avere dati vecchi!)

# CORRETTO: opzione A - leggi-la-tua-scrittura con hint di LSN
def get_user_after_update(user_id):
    update_user(user_id, new_data)  # scrive sul primario
    lsn = get_current_lsn()         # recupera il LSN corrente dal primario
    
    # Attendere che la replica abbia raggiunto questo LSN
    wait_for_replica_catchup(lsn, timeout=5)
    return get_user_from_replica(user_id)

# CORRETTO: opzione B - sempre dal primario per questo utente
def get_user_after_update(user_id):
    update_user(user_id, new_data)  # scrive sul primario
    return get_user_from_primary(user_id)  # leggi sempre dal primario per consistenza
```

### Anti-pattern 2: Replication slot senza monitoraggio

```sql
-- SBAGLIATO: creare slot e dimenticarli
SELECT pg_create_logical_replication_slot('consumer_slot', 'pgoutput');
-- Se il consumer si rompe, il disco si riempie silenziosamente

-- CORRETTO: alert su slot inattivi o con troppo WAL
-- (da eseguire ogni 5 minuti in produzione)
SELECT
  slot_name,
  active,
  pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn) / 1024 / 1024 AS wal_mb
FROM pg_replication_slots
WHERE NOT active
   OR pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn) > 1024 * 1024 * 1024; -- 1GB
```

### Anti-pattern 3: Usare la replica come sostituto del backup

La replica protegge dalla failure hardware ma non dalla corruzione logica. Un `DROP TABLE` o `UPDATE WHERE 1=1` si propaga immediatamente a tutte le repliche. Il backup è obbligatorio e complementare alla replica.

### Anti-pattern 4: Failover senza fencing

Eseguire il failover senza fencing (isolare il vecchio primario prima che il nuovo inizi a scrivere) porta allo split-brain. Anche se il vecchio primario sembra morto, potrebbe essere solo irraggiungibile dal punto di vista della rete ma ancora in esecuzione localmente, continuando ad accettare scritture.

Soluzioni di fencing:
- STONITH via IPMI/iDRAC (spegnimento fisico del nodo)
- Revoca del lease etcd (Patroni: il vecchio primario non può scrivere senza lease)
- Network fencing (isolare l'IP del vecchio primario)

## Checklist di Produzione

**Infrastruttura:**
- [ ] Almeno 2 repliche streaming (non un singolo standby)
- [ ] WAL archiving configurato per PITR
- [ ] Backup base regolare (almeno settimanale)
- [ ] Test di recovery mensile su ambiente separato
- [ ] Replication slot monitorati con alert su WAL retained > 5GB
- [ ] SSL/TLS sulla connessione di replica

**Monitoraggio:**
- [ ] Alert su replication lag > 30s
- [ ] Alert su replication lag > 5 minuti (critical)
- [ ] Alert su replica disconnessa
- [ ] Alert su spazio disco < 20% in pg_wal directory
- [ ] Dashboard di lag in tempo reale (Grafana)

**Alta Disponibilità:**
- [ ] Patroni (o equivalente) configurato con DCS ridondante
- [ ] HAProxy o ProxySQL per il routing
- [ ] Test di failover eseguito entro l'ultimo mese
- [ ] RTO e RPO documentati e verificati
- [ ] Runbook di failover aggiornato e accessibile

**Sicurezza:**
- [ ] Utente dedicato per la replica (non superuser)
- [ ] Connessioni SSL/TLS per la replica
- [ ] Nessuna password in chiaro nei file di configurazione (usare .pgpass o variabili)
- [ ] Accesso alla replica protetto da firewall (solo IP autorizzati)

