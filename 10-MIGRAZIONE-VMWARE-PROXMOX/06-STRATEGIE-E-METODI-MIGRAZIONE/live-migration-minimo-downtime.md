# Live Migration — Approcci a Minimo Downtime

> **Modulo del corso:** Migrazione VMware → Proxmox VE
> **Posizione nel percorso:** Fase 3 — Migrazione · Modulo 06.3 (chiude la sequenza strategica, vedi `../00-SYLLABUS.md` §5)
> **Prerequisiti:** moduli 06.1 e 06.2; conoscenza DNS (TTL, A/AAAA records, propagation), database replication concettuale (Postgres streaming, MySQL GTID, MSSQL AG), load balancer (HAProxy, Nginx, F5, AWS ALB), TCP state machine.
> **Obiettivi di apprendimento.** Al termine del modulo lo studente sara in grado di:
> 1. distinguere i 6 approcci di live migration (tool commerciali, replication DB-specific, DNS-based cutover, load balancer switching, hybrid combinato, application-level failover) e scegliere il piu adatto al singolo workload;
> 2. configurare PostgreSQL streaming replication, MySQL GTID-based replication, e MSSQL Always On Availability Group come base per il cutover di un DB con downtime < 30 sec;
> 3. progettare un DNS-based cutover con TTL drop pre-evento + record A change + monitoring del lag dei resolver, calcolando il drain TCP delle sessioni esistenti (FIN_WAIT2, TIME_WAIT);
> 4. configurare un load balancer (HAProxy con `weight 0` graceful drain, AWS ALB con target deregistration, Nginx upstream) per spostare il traffico da VM-VMware a VM-Proxmox in modo blue-green;
> 5. comprendere quando combinare approcci (es. DNS + LB switching + DB replication) per il maximum-resilience cutover di sistemi multi-tier;
> 6. valutare i tool commerciali (Veeam, Zerto, NAKIVO, Carbonite Migrate) confrontandoli con il toolchain open-source per costo, vendor lock-in, capacita di replicare verso target Proxmox.
> **Tempo stimato:** lettura 90-120 min · lab 360-480 min (per implementare almeno 2 approcci end-to-end)
> **Livello:** competent → proficient (Dreyfus 3 → 4); per Approach 5 (Hybrid) → proficient/expert (Dreyfus 4-5)
> **Ultimo aggiornamento:** 2026-04-26
> **Versioni di riferimento:** PostgreSQL 13/14/15/16, MySQL 8.0+/MariaDB 10.6+, MSSQL Server 2019/2022, HAProxy 2.x/3.x, Nginx 1.24+, AWS ALB.

## Mappa concettuale

```
+======================================================+
|  Live migration — i 6 approcci                       |
+======================================================+
|                                                      |
|     [App stateless dietro LB]                        |
|       Approccio 4: Load Balancer Switching           |
|         - clone VM su Proxmox                        |
|         - aggiungi target nel LB pool                |
|         - drain VM-VMware (weight 0)                 |
|         - rimuovi target VMware                      |
|         Downtime: 0 sec (per nuove richieste)        |
|                                                      |
|     [DB stateful con replica nativa]                 |
|       Approccio 2: DB-Specific Replication           |
|         - configura replica Master->Slave            |
|         - sync iniziale (ore)                        |
|         - sync continuo (sec)                        |
|         - cutover: stop master, promote slave        |
|         Downtime: < 30 sec (DB-specific)             |
|                                                      |
|     [VM con IP cambiabile via DNS]                   |
|       Approccio 3: DNS-based Cutover                 |
|         - TTL drop a 60s (T-48h)                     |
|         - clone VM con sync rsync (warm)             |
|         - cutover DNS A record                       |
|         - drain TCP residui (5-10 min)               |
|         Downtime: < 1 min (per nuove sessioni)       |
|                                                      |
|     [Sistema enterprise con tool commerciale]        |
|       Approccio 1: Veeam/Zerto/NAKIVO                |
|         - replica continua VMware -> KVM             |
|         - failover orchestrato                       |
|         Downtime: 1-5 min, costo licenza             |
|                                                      |
|     [Application-aware (Active Directory, Exchange)] |
|       Approccio 6: Application-level Failover        |
|         - aggiungi nodo Proxmox al cluster app       |
|         - sync (DAG, FSMO, AG)                       |
|         - rimuovi nodo VMware                        |
|         Downtime: seamless (cluster app)             |
|                                                      |
|     [Sistema critico complesso]                      |
|       Approccio 5: Hybrid (combina 2-3 sopra)        |
|         - DNS + LB + DB replication                  |
|         Downtime: < 10 sec (con coordinamento)       |
|                                                      |
+======================================================+
```

Idee guida del modulo:

1. **Live ≠ "zero downtime sempre".** Anche le tecniche piu avanzate hanno *qualche* downtime (anche se misurato in millisecondi per le connessioni esistenti). "Live" significa che le *nuove* connessioni continuano ad arrivare senza interruzione percepita. Le sessioni TCP attive devono spesso essere droppate o drained.
2. **Stateful = replication. Stateless = LB switching.** I due assi: (a) lo stato vive nella VM (DB, file system, sessione) → serve replicazione applicativa; (b) lo stato vive altrove (cache, session store, DB esterno) → la VM e fungibile, basta switchare il LB.
3. **DNS TTL: matematica del cutover.** TTL = N → tempo medio di propagazione = N/2 (i resolver re-cachano random nel TTL). Con TTL = 60 s, dopo lo switch DNS, in 30 s metti il 50% dei resolver, in 60 s il 90%, in 120 s il 99%. Non e immediato — pianificare il drain del traffico vecchio per almeno 5-10 min dopo lo switch.
4. **DB replication: i tre fattori di rischio.** (a) Replication lag — verificare con `pg_stat_replication` / `SHOW SLAVE STATUS` / DMV `sys.dm_hadr_database_replica_states`. Cutover solo a lag < 1 sec; (b) Slave promotion atomica — `pg_ctl promote`, `STOP SLAVE; RESET SLAVE ALL`, `ALTER AVAILABILITY GROUP FAILOVER`. Non lasciare il master "promotabile" parallelo (split-brain); (c) Connection redirect — i client devono saper trovare il nuovo master (DNS, connection string, DB-aware proxy come pgbouncer, ProxySQL, MaxScale).
5. **Hybrid e l'unico approccio per multi-tier critici.** Un'app a 3 tier (web, app, db) richiede coordinamento: DB con replication (+ promotion), app con LB switching, web con DNS cutover. La sequenza e *bottom-up*: prima il DB replication ready, poi promote DB, poi switch LB app-tier, poi DNS web-tier. Ogni step ha rollback. Il cutover totale dura 5-15 minuti reali, ma il downtime percepito e < 30 sec.

## Panoramica

La **live migration** con downtime minimo (o quasi zero) rappresenta il Santo Graal delle migrazioni da VMware a Proxmox VE. A differenza della cold e warm migration, qui l'obiettivo è ridurre il downtime percepito a **pochi secondi** — idealmente sotto la soglia di timeout delle connessioni di rete e delle applicazioni.

Non esiste una singola tecnologia che consenta una migrazione "live" trasparente tra hypervisor diversi (VMware -> Proxmox/KVM). Tuttavia, combinando **replicazione dati continua**, **failover applicativo**, **gestione DNS intelligente** e **load balancer switching**, è possibile ottenere risultati paragonabili a una vera live migration.

### Classificazione degli Approcci per Downtime

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SPETTRO DEL DOWNTIME                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Cold Migration    Warm Migration    Near-Zero         Zero*        │
│  ██████████████    ██████████        ████              █            │
│  Ore               Minuti            Secondi           ~0           │
│  (2-16 ore)        (5-30 min)        (5-60 sec)        (<5 sec)    │
│                                                                     │
│  qemu-img          rsync+cutover     Replicazione      Cluster     │
│  convert           block-sync        continua +        nativo +    │
│                                      failover          failover    │
│                                      automatico        automatico  │
│                                                                     │
│  * Zero downtime reale è possibile solo con replicazione           │
│    applicativa e load balancer, non con migrazione VM pura          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Approccio 1: Replicazione con Tool Commerciali (Veeam, Zerto, NAKIVO)

### Veeam Backup & Replication — Instant VM Recovery

Veeam offre una funzionalità chiamata **Instant VM Recovery** che consente di avviare una VM direttamente dal backup, riducendo il downtime al tempo di switch.

#### Architettura

```
┌──────────────┐     Backup Continuo     ┌──────────────────┐
│  VM VMware   │ ─────────────────────► │  Veeam Repository  │
│  (Sorgente)  │     (ogni 15 min)      │  (Backup recente) │
└──────────────┘                         └────────┬─────────┘
                                                  │
                                         Instant VM Recovery
                                                  │
                                         ┌────────▼─────────┐
                                         │  VM Proxmox      │
                                         │  (Destinazione)  │
                                         │  Avviata dal     │
                                         │  backup Veeam    │
                                         └──────────────────┘
```

#### Procedura con Veeam

```powershell
# === FASE 1: Configurare il Backup Job Continuo ===

# 1. In Veeam Backup & Replication Console:
#    - Backup Job > New > Virtual Machine
#    - Selezionare la VM VMware da migrare
#    - Schedule: ogni 15 minuti (o il minimo consentito dalla licenza)
#    - Repository: storage locale ad alta velocità (SSD consigliato)

# 2. Eseguire il primo full backup
# 3. Verificare che i backup incrementali funzionino correttamente
# 4. Mantenere il job attivo per almeno 24 ore prima della migrazione

# === FASE 2: Preparare l'Ambiente Proxmox ===

# Su Proxmox, preparare lo storage e la rete
# Assicurarsi che il Veeam Proxy/Repository abbia accesso alla rete Proxmox

# === FASE 3: Cutover ===

# 1. Eseguire l'ultimo backup incrementale
# 2. Spegnere la VM su VMware
# 3. In Veeam: Restore > Instant VM Recovery
#    - Selezionare il backup più recente
#    - Target: Proxmox host (via Veeam Proxy)
#    - Network mapping: configurare il bridge di rete corretto
# 4. La VM si avvia direttamente dal repository Veeam
#    (latenza I/O iniziale più alta, ma downtime minimo)
# 5. In background, Veeam migra i dati verso lo storage definitivo di Proxmox
#    (Storage vMotion in background)

# Downtime effettivo: 2-5 minuti (tempo di spegnimento + avvio)
```

### Zerto — Continuous Data Protection

Zerto offre replicazione continua con **RPO di pochi secondi** e failover automatizzato.

```
Architettura Zerto per Migrazione VMware -> Proxmox:

┌──────────────────┐          ┌──────────────────┐
│  VMware vCenter  │          │  Proxmox VE      │
│  ┌────────────┐  │  Journal │  ┌────────────┐  │
│  │  VM Prod   │──┼──Based──►│  │  VM Replica │  │
│  │            │  │  Replic. │  │  (standby)  │  │
│  └────────────┘  │          │  └────────────┘  │
│  ┌────────────┐  │          │  ┌────────────┐  │
│  │  Zerto VRA │  │          │  │  Zerto VRA │  │
│  │  (Virtual  │  │◄────────►│  │  (Virtual  │  │
│  │  Repl.     │  │          │  │  Repl.     │  │
│  │  Appliance)│  │          │  │  Appliance)│  │
│  └────────────┘  │          │  └────────────┘  │
└──────────────────┘          └──────────────────┘
```

#### Procedura Zerto

```
1. Installare Zerto Virtual Manager (ZVM) nel vCenter
2. Installare Zerto VRA su ogni ESXi host
3. Installare Zerto Linux ZVM su Proxmox (se supportato)
   OPPURE usare un proxy Zerto compatibile con KVM/Proxmox
4. Creare un Virtual Protection Group (VPG):
   - Selezionare le VM da proteggere/migrare
   - Configurare il target (Proxmox)
   - Impostare RPO target (es. 5 secondi)
   - Configurare network mapping
5. Attendere la sincronizzazione iniziale
6. Monitorare il Journal (mantiene N ore di punti di recovery)
7. Al momento del cutover:
   a. Iniziare il "Move" (non "Failover")
   b. Zerto esegue l'ultimo sync
   c. Spegne la VM sorgente
   d. Avvia la VM di destinazione
   e. Downtime: 10-30 secondi
```

### NAKIVO Backup & Replication

NAKIVO supporta nativamente sia VMware che Proxmox VE come piattaforme di origine e destinazione.

```bash
# === Configurazione NAKIVO per Cross-Platform Replication ===

# 1. Installare NAKIVO Backup & Replication
# Download da: https://www.nakivo.com/

# 2. Aggiungere l'inventario VMware
# Settings > Inventory > Add VMware vCenter/ESXi
# Inserire credenziali vCenter

# 3. Aggiungere l'inventario Proxmox
# Settings > Inventory > Add Proxmox VE
# Inserire IP e credenziali Proxmox

# 4. Creare un Replication Job
# Jobs > Create > Replication Job
# Source: VMware VM
# Destination: Proxmox storage
# Schedule: ogni 15 minuti (RPO)
# Network mapping: configurare bridge mapping

# 5. Eseguire il job e monitorare la replicazione
# Dashboard > Replication Jobs > Status

# 6. Al momento del cutover:
# Jobs > Replication Job > Failover
# Tipo: Planned Failover (spegne sorgente prima di avviare destinazione)
# Downtime stimato: 2-5 minuti
```

---

## Approccio 2: Replicazione Database-Specific

Per molte applicazioni, il componente più critico è il **database**. Migrando prima il database con replicazione nativa e poi l'applicazione separatamente, si può ottenere un downtime quasi nullo.

### MySQL / MariaDB — Replicazione Master-Slave

```bash
# === VM SORGENTE (VMware) - MASTER ===

# 1. Configurare il master per la replicazione
cat >> /etc/mysql/mariadb.conf.d/50-server.cnf << 'EOF'
[mysqld]
server-id = 1
log-bin = mysql-bin
binlog-format = ROW
binlog-do-db = production_db
# Opzionale: escludere database di sistema
binlog-ignore-db = information_schema
binlog-ignore-db = performance_schema
binlog-ignore-db = mysql
EOF

systemctl restart mariadb

# 2. Creare l'utente di replicazione
mysql -e "
CREATE USER 'repl_user'@'%' IDENTIFIED BY 'StrongPassword123!';
GRANT REPLICATION SLAVE ON *.* TO 'repl_user'@'%';
FLUSH PRIVILEGES;
"

# 3. Ottenere la posizione del binary log
mysql -e "SHOW MASTER STATUS\G"
# Annotare File e Position (es: mysql-bin.000003, 785)

# 4. Esportare il dump iniziale con lock minimo
mysqldump --all-databases --master-data=2 --single-transaction \
  --routines --triggers --events \
  -u root -p > /tmp/full_dump.sql

# Trasferire il dump sulla VM di destinazione
scp /tmp/full_dump.sql root@proxmox-vm:/tmp/

# === VM DESTINAZIONE (Proxmox) - SLAVE ===

# 5. Configurare lo slave
cat >> /etc/mysql/mariadb.conf.d/50-server.cnf << 'EOF'
[mysqld]
server-id = 2
relay-log = relay-bin
read-only = 1
EOF

systemctl restart mariadb

# 6. Importare il dump
mysql -u root -p < /tmp/full_dump.sql

# 7. Configurare e avviare la replicazione
mysql -e "
CHANGE MASTER TO
  MASTER_HOST='192.168.1.50',
  MASTER_USER='repl_user',
  MASTER_PASSWORD='StrongPassword123!',
  MASTER_LOG_FILE='mysql-bin.000003',
  MASTER_LOG_POS=785;
START SLAVE;
"

# 8. Verificare lo stato della replicazione
mysql -e "SHOW SLAVE STATUS\G" | grep -E "Slave_IO_Running|Slave_SQL_Running|Seconds_Behind_Master"
# Atteso:
# Slave_IO_Running: Yes
# Slave_SQL_Running: Yes
# Seconds_Behind_Master: 0

# === CUTOVER (Downtime Minimo) ===

# 9. Sul MASTER (sorgente): fermare le scritture
mysql -e "SET GLOBAL read_only = ON;"
mysql -e "FLUSH TABLES WITH READ LOCK;"

# 10. Sullo SLAVE: verificare che sia completamente allineato
mysql -e "SHOW SLAVE STATUS\G" | grep "Seconds_Behind_Master"
# Deve essere 0

# 11. Sullo SLAVE: promuovere a master
mysql -e "
STOP SLAVE;
RESET SLAVE ALL;
SET GLOBAL read_only = OFF;
"

# 12. Aggiornare la configurazione dell'applicazione per puntare al nuovo DB
# 13. Sbloccare il vecchio master
mysql -e "UNLOCK TABLES;"

# Downtime DB effettivo: 5-15 secondi
```

### PostgreSQL — Streaming Replication

```bash
# === VM SORGENTE (VMware) - PRIMARY ===

# 1. Configurare postgresql.conf
cat >> /etc/postgresql/15/main/postgresql.conf << 'EOF'
wal_level = replica
max_wal_senders = 5
wal_keep_size = 1GB
hot_standby = on
EOF

# 2. Configurare pg_hba.conf per permettere la replicazione
echo "host replication repl_user 192.168.1.0/24 md5" >> /etc/postgresql/15/main/pg_hba.conf

# 3. Creare l'utente di replicazione
sudo -u postgres psql -c "CREATE ROLE repl_user WITH REPLICATION LOGIN PASSWORD 'StrongPassword123!';"

systemctl restart postgresql

# === VM DESTINAZIONE (Proxmox) - STANDBY ===

# 4. Fermare PostgreSQL sulla destinazione
systemctl stop postgresql

# 5. Rimuovere i dati esistenti
rm -rf /var/lib/postgresql/15/main/*

# 6. Eseguire il base backup dalla sorgente
sudo -u postgres pg_basebackup \
  -h 192.168.1.50 \
  -U repl_user \
  -D /var/lib/postgresql/15/main \
  -Fp -Xs -P -R

# Il flag -R crea automaticamente standby.signal e configura
# primary_conninfo in postgresql.auto.conf

# 7. Avviare PostgreSQL in modalità standby
systemctl start postgresql

# 8. Verificare la replicazione
sudo -u postgres psql -c "SELECT * FROM pg_stat_replication;" # Sul primary
sudo -u postgres psql -c "SELECT * FROM pg_stat_wal_receiver;" # Sullo standby

# === CUTOVER ===

# 9. Promuovere lo standby a primary
sudo -u postgres pg_ctl promote -D /var/lib/postgresql/15/main
# OPPURE:
sudo -u postgres psql -c "SELECT pg_promote();"

# 10. Verificare che sia diventato primary
sudo -u postgres psql -c "SELECT pg_is_in_recovery();"
# Deve restituire: f (false = è primary)

# Downtime DB: 2-5 secondi (tempo di promozione)
```

### Microsoft SQL Server — Log Shipping

```sql
-- === VM SORGENTE (VMware) - PRIMARY ===

-- 1. Configurare il database per full recovery model
ALTER DATABASE [ProductionDB] SET RECOVERY FULL;

-- 2. Eseguire il full backup
BACKUP DATABASE [ProductionDB]
TO DISK = '\\share\backups\ProductionDB_full.bak'
WITH INIT, COMPRESSION;

-- 3. Configurare Log Shipping tramite SSMS:
-- Database > Properties > Transaction Log Shipping
-- Enable this as a primary database in a log shipping configuration
-- Backup Settings:
--   Network path: \\share\backups\
--   Backup schedule: ogni 5 minuti
-- Secondary Databases:
--   Add secondary server (Proxmox VM con MSSQL)
--   Copy settings: copia dalla share
--   Restore settings: restore con STANDBY mode

-- OPPURE via T-SQL:
-- Configurare il backup job
EXEC sp_add_log_shipping_primary_database
  @database = N'ProductionDB',
  @backup_directory = N'\\share\backups',
  @backup_share = N'\\share\backups',
  @backup_job_name = N'LSBackup_ProductionDB',
  @backup_compression = 1;

-- === VM DESTINAZIONE (Proxmox) ===

-- 4. Restore del full backup con NORECOVERY
RESTORE DATABASE [ProductionDB]
FROM DISK = '\\share\backups\ProductionDB_full.bak'
WITH NORECOVERY, MOVE 'ProductionDB' TO 'D:\Data\ProductionDB.mdf',
MOVE 'ProductionDB_log' TO 'D:\Logs\ProductionDB_log.ldf';

-- 5. Configurare il restore automatico dei transaction log
-- (tramite SQL Server Agent Job o script PowerShell)

-- === CUTOVER ===

-- 6. Sul PRIMARY: eseguire l'ultimo log backup
BACKUP LOG [ProductionDB]
TO DISK = '\\share\backups\ProductionDB_final.trn'
WITH NORECOVERY;
-- NORECOVERY qui impedisce ulteriori transazioni

-- 7. Sullo SECONDARY: applicare l'ultimo log e portare online
RESTORE LOG [ProductionDB]
FROM DISK = '\\share\backups\ProductionDB_final.trn'
WITH RECOVERY;
-- WITH RECOVERY porta il database online

-- Downtime DB: 30 secondi - 2 minuti (dipende dal log size)
```

---

## Approccio 3: DNS-Based Cutover con Low TTL

Il DNS-based cutover è un approccio semplice e universale che non richiede tool commerciali. Funziona cambiando la risoluzione DNS per puntare i client dalla vecchia alla nuova VM.

### Setup Pre-Migrazione (24-48 ore prima)

```bash
# === Sul DNS Server (es. BIND9) ===

# 1. Ridurre il TTL dei record che verranno modificati
# Modificare il file di zona

# PRIMA (TTL alto):
# webserver.example.com.  3600  IN  A  192.168.1.50

# DOPO (TTL ridotto a 60 secondi):
# webserver.example.com.  60    IN  A  192.168.1.50

# 2. Ricaricare la zona
rndc reload example.com

# 3. Verificare che il nuovo TTL sia propagato
dig +nocmd +noall +answer webserver.example.com
# Verificare che il TTL sia 60

# 4. Attendere che il vecchio TTL scada completamente
# Se il vecchio TTL era 3600, attendere almeno 1 ora
# In pratica, attendere 2x il vecchio TTL per sicurezza
```

### Procedura di Cutover DNS

```bash
# === CUTOVER ===

# Fase 1: La nuova VM su Proxmox è pronta con IP diverso (192.168.1.60)
# Verificare che sia funzionante
curl -I http://192.168.1.60/healthcheck
# Deve restituire 200 OK

# Fase 2: Aggiornare il record DNS
# Metodo 1: nsupdate (dynamic DNS)
nsupdate -k /etc/bind/rndc.key << EOF
server 127.0.0.1
zone example.com
update delete webserver.example.com. A
update add webserver.example.com. 60 A 192.168.1.60
send
EOF

# Metodo 2: Modifica manuale del file di zona
# Modificare la zona, incrementare il serial, ricaricare
rndc reload example.com

# Metodo 3: Per Windows DNS (PowerShell)
# Remove-DnsServerResourceRecord -ZoneName "example.com" -RRType "A" -Name "webserver" -Force
# Add-DnsServerResourceRecord -ZoneName "example.com" -A -Name "webserver" -IPv4Address "192.168.1.60" -TimeToLive 00:01:00

# Fase 3: Monitorare la transizione
# Script di monitoraggio
cat > /root/monitor-dns-transition.sh << 'SCRIPT'
#!/bin/bash
echo "Monitoraggio transizione DNS - $(date)"
echo "============================================"
while true; do
    RESOLVED_IP=$(dig +short webserver.example.com @8.8.8.8)
    LOCAL_IP=$(dig +short webserver.example.com @localhost)

    # Contare connessioni attive sulle due VM
    OLD_CONNS=$(ssh root@192.168.1.50 "ss -s" 2>/dev/null | grep "estab" | awk '{print $2}')
    NEW_CONNS=$(ssh root@192.168.1.60 "ss -s" 2>/dev/null | grep "estab" | awk '{print $2}')

    echo "[$(date '+%H:%M:%S')] DNS Google: $RESOLVED_IP | DNS Local: $LOCAL_IP | Old VM conns: $OLD_CONNS | New VM conns: $NEW_CONNS"

    sleep 10
done
SCRIPT
chmod +x /root/monitor-dns-transition.sh

# Fase 4: Dopo la stabilizzazione (30-60 minuti)
# Riportare il TTL al valore normale
# webserver.example.com.  3600  IN  A  192.168.1.60
rndc reload example.com

# Fase 5: Spegnere la vecchia VM (dopo verifica completa)
# Mantenere la vecchia VM spenta per almeno 7 giorni come rollback
```

### Limitazioni del DNS-Based Cutover

```
┌────────────────────────────────────────────────────────────────┐
│                LIMITAZIONI DNS CUTOVER                         │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  1. Client con DNS cache aggressivo                            │
│     - Java (default: cache infinito per lookup positivi)       │
│       Fix: -Dnetworkaddress.cache.ttl=60                      │
│     - Browser (cache DNS interno)                              │
│       Fix: non controllabile dall'esterno                      │
│     - nscd/systemd-resolved (cache OS)                         │
│       Fix: ridurre cache TTL o fare flush                      │
│                                                                │
│  2. Connessioni TCP long-lived                                 │
│     - WebSocket, gRPC streams, database connections            │
│     - Queste connessioni non verranno migrate                  │
│     - Fix: riavviare i client o attendere timeout              │
│                                                                │
│  3. Hardcoded IPs                                              │
│     - Applicazioni che usano IP invece di hostname             │
│     - Fix: impossibile con DNS, serve cambio IP               │
│                                                                │
│  4. Split-brain temporaneo                                     │
│     - Per la durata del TTL, alcuni client puntano al vecchio  │
│       IP e altri al nuovo                                      │
│     - Fix: mantenere entrambe le VM attive durante la          │
│       transizione                                              │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## Approccio 4: Load Balancer Switching

Quando le applicazioni sono posizionate dietro un load balancer, il cutover può essere gestito interamente a livello di bilanciamento del traffico.

### HAProxy — Blue/Green Deployment

```bash
# === Configurazione HAProxy per Migrazione ===

# haproxy.cfg — PRIMA della migrazione
cat > /etc/haproxy/haproxy.cfg << 'EOF'
global
    log /dev/log local0
    maxconn 4096

defaults
    log     global
    mode    http
    option  httplog
    timeout connect 5000ms
    timeout client  50000ms
    timeout server  50000ms

frontend http_front
    bind *:80
    bind *:443 ssl crt /etc/ssl/certs/server.pem
    default_backend webservers

backend webservers
    balance roundrobin
    option httpchk GET /healthcheck

    # VM VMware (blue) — attualmente attiva
    server web-vmware 192.168.1.50:80 check inter 5s fall 3 rise 2

    # VM Proxmox (green) — in preparazione, disabilitata
    server web-proxmox 192.168.1.60:80 check inter 5s fall 3 rise 2 disabled
EOF

systemctl reload haproxy
```

#### Procedura di Cutover con HAProxy

```bash
# STEP 1: Abilitare la VM Proxmox nel pool (traffico su entrambe)
# Tramite HAProxy Runtime API (socket)
echo "enable server webservers/web-proxmox" | socat stdio /var/run/haproxy/admin.sock

# STEP 2: Verificare che la VM Proxmox risponda correttamente
echo "show stat" | socat stdio /var/run/haproxy/admin.sock | grep web-proxmox
# Status deve essere "UP"

# STEP 3: Attendere qualche minuto e verificare i log
tail -f /var/log/haproxy.log | grep web-proxmox
# Verificare che non ci siano errori

# STEP 4: Spostare tutto il traffico sulla VM Proxmox
# Mettere la VM VMware in maintenance (drain connections)
echo "set server webservers/web-vmware state drain" | socat stdio /var/run/haproxy/admin.sock

# STEP 5: Attendere che le connessioni attive sulla VM VMware si chiudano
echo "show stat" | socat stdio /var/run/haproxy/admin.sock | grep web-vmware
# Monitorare "scur" (current sessions) — deve arrivare a 0

# STEP 6: Disabilitare completamente la VM VMware
echo "disable server webservers/web-vmware" | socat stdio /var/run/haproxy/admin.sock

# STEP 7: Se tutto funziona, aggiornare la configurazione permanente
# Modificare haproxy.cfg per riflettere lo stato finale
# Rimuovere la VM VMware dal backend

# ROLLBACK (se necessario):
echo "enable server webservers/web-vmware" | socat stdio /var/run/haproxy/admin.sock
echo "disable server webservers/web-proxmox" | socat stdio /var/run/haproxy/admin.sock
```

### NGINX — Upstream Switching

```nginx
# nginx.conf — Configurazione per migrazione

upstream backend {
    # VM VMware (attiva)
    server 192.168.1.50:80 weight=100;

    # VM Proxmox (pronta, peso zero = no traffico)
    server 192.168.1.60:80 weight=0 backup;
}

server {
    listen 80;
    server_name webserver.example.com;

    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_next_upstream error timeout invalid_header http_500 http_502 http_503;
    }

    location /healthcheck {
        proxy_pass http://backend;
        access_log off;
    }
}

# === CUTOVER ===
# Modificare i pesi per spostare il traffico gradualmente

# Step 1: 50/50
# server 192.168.1.50:80 weight=50;
# server 192.168.1.60:80 weight=50;
# nginx -s reload

# Step 2: 10/90 (quasi tutto su Proxmox)
# server 192.168.1.50:80 weight=10;
# server 192.168.1.60:80 weight=90;
# nginx -s reload

# Step 3: 0/100 (tutto su Proxmox)
# server 192.168.1.50:80 down;
# server 192.168.1.60:80 weight=100;
# nginx -s reload
```

---

## Approccio 5: Hybrid — Combinazione di Più Tecniche

L'approccio più efficace per sistemi complessi è combinare più tecniche per minimizzare il downtime di ciascun componente.

### Scenario: Migrazione di un'Applicazione Web a 3 Livelli

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ARCHITETTURA A 3 LIVELLI                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│    [Load Balancer]  ◄── DNS-based cutover (zero downtime)          │
│         │                                                           │
│    [Web Server]     ◄── LB switching (zero downtime)               │
│         │                                                           │
│    [App Server]     ◄── Blue/green deploy (< 5 sec downtime)      │
│         │                                                           │
│    [Database]       ◄── Replicazione nativa (< 5 sec downtime)    │
│         │                                                           │
│    [File Storage]   ◄── rsync continuo + NFS switch               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Procedura Ibrida Passo per Passo

```bash
# === FASE 1: PREPARAZIONE (2-4 settimane prima) ===

# 1. Ridurre TTL DNS
# 2. Configurare la replicazione database (MySQL replica)
# 3. Configurare rsync continuo per i file di dati
# 4. Creare le VM di destinazione su Proxmox
# 5. Installare e configurare le applicazioni sulle VM Proxmox

# === FASE 2: REPLICAZIONE ATTIVA (1-2 settimane prima) ===

# Database: Replicazione MySQL attiva e verificata
mysql -e "SHOW SLAVE STATUS\G" | grep Seconds_Behind_Master
# Output: Seconds_Behind_Master: 0

# File storage: rsync continuo ogni 15 minuti
*/15 * * * * rsync -aHAXz --delete /data/ root@proxmox-fileserver:/data/

# Web/App server: configurazione identica già applicata
# Test funzionale completato sulla destinazione

# === FASE 3: CUTOVER (Piano di esecuzione minuto per minuto) ===

# T-60min: Comunicazione agli stakeholder
# T-30min: Verifica finale stato replicazione
# T-15min: Team pronti alle posizioni

echo "=== T-00:00 INIZIO CUTOVER ==="

# T+00:00 — Step 1: Mettere web server VMware in drain sul LB
echo "set server webservers/web-vmware state drain" | \
  socat stdio /var/run/haproxy/admin.sock

# T+00:30 — Step 2: Abilitare web server Proxmox sul LB
echo "enable server webservers/web-proxmox" | \
  socat stdio /var/run/haproxy/admin.sock
# (traffico inizia a fluire sulla nuova VM)

# T+01:00 — Step 3: Verificare health check della nuova VM
curl -s http://192.168.1.60/healthcheck
echo "show stat" | socat stdio /var/run/haproxy/admin.sock

# T+02:00 — Step 4: Attendere drain delle connessioni sulla vecchia VM
# Monitorare fino a 0 sessioni attive

# T+03:00 — Step 5: Fermare scritture sul database sorgente
mysql -h 192.168.1.50 -e "SET GLOBAL read_only = ON; FLUSH TABLES WITH READ LOCK;"

# T+03:10 — Step 6: Verificare allineamento replica
mysql -h 192.168.1.60 -e "SHOW SLAVE STATUS\G" | grep Seconds_Behind_Master
# DEVE essere 0

# T+03:15 — Step 7: Promuovere database replica
mysql -h 192.168.1.60 -e "STOP SLAVE; RESET SLAVE ALL; SET GLOBAL read_only = OFF;"

# T+03:20 — Step 8: Aggiornare connection string applicativa
# (già configurata per puntare al nuovo IP, serve solo restart)
ssh root@proxmox-appserver "systemctl restart application"

# T+03:30 — Step 9: Ultima sync file storage
rsync -aHAXz --delete /data/ root@proxmox-fileserver:/data/

# T+03:45 — Step 10: Switch NFS mount sull'app server
ssh root@proxmox-appserver "umount /mnt/data; mount proxmox-fileserver:/data /mnt/data"

# T+04:00 — Step 11: Disabilitare completamente vecchio web server
echo "disable server webservers/web-vmware" | \
  socat stdio /var/run/haproxy/admin.sock

# T+05:00 — Step 12: Verifiche finali
curl -I https://webserver.example.com
mysql -h 192.168.1.60 -e "SELECT COUNT(*) FROM production_table;"

echo "=== T+05:00 CUTOVER COMPLETATO ==="
echo "Downtime percepito: < 30 secondi (solo switch DB)"

# === FASE 4: POST-CUTOVER ===

# Monitorare per 2 ore
# Mantenere VM VMware spente per 7 giorni (rollback)
# Aggiornare documentazione
# Ripristinare TTL DNS a valori normali
```

---

## Approccio 6: Application-Level Failover

Alcune applicazioni hanno meccanismi di failover integrati che possono essere sfruttati per la migrazione.

### Redis — Replicazione e Failover con Sentinel

```bash
# === VM Sorgente (VMware) — Redis Master ===
# redis.conf:
# bind 0.0.0.0
# protected-mode no

# === VM Destinazione (Proxmox) — Redis Slave ===
# redis.conf:
# replicaof 192.168.1.50 6379

# === Redis Sentinel (3 istanze) ===
# sentinel.conf:
# sentinel monitor mymaster 192.168.1.50 6379 2
# sentinel down-after-milliseconds mymaster 5000
# sentinel failover-timeout mymaster 60000

# CUTOVER:
# 1. Fermare il Redis master su VMware
redis-cli -h 192.168.1.50 shutdown

# 2. Sentinel rileva il master down e promuove automaticamente lo slave
# Il failover avviene in 5-10 secondi

# 3. Verificare il nuovo master
redis-cli -h 192.168.1.60 info replication
# role:master
```

### Elasticsearch — Cluster Cross-Platform

```bash
# Aggiungere il nodo Proxmox al cluster Elasticsearch esistente

# elasticsearch.yml sul nodo Proxmox:
# cluster.name: production-cluster
# node.name: es-proxmox-01
# discovery.seed_hosts: ["192.168.1.50", "192.168.1.60"]

# 1. Avviare il nodo Proxmox e attendere che si unisca al cluster
curl -s http://192.168.1.60:9200/_cluster/health?pretty

# 2. Attendere che le shard si ribilancino
curl -s http://192.168.1.60:9200/_cat/shards?v

# 3. Escludere il nodo VMware dal cluster
curl -X PUT "http://192.168.1.50:9200/_cluster/settings" -H 'Content-Type: application/json' -d'
{
  "transient": {
    "cluster.routing.allocation.exclude._ip": "192.168.1.50"
  }
}'

# 4. Attendere che tutte le shard siano migrate
# 5. Rimuovere il nodo VMware dal cluster
```

---

## Tabella Riassuntiva degli Approcci

| Approccio | Downtime | Complessità | Costo | Adatto per |
|-----------|:--------:|:-----------:|:-----:|------------|
| Veeam Instant Recovery | 2-5 min | Media | $$$ | Grandi aziende con licenze Veeam |
| Zerto CDP | 10-30 sec | Alta | $$$$ | Ambienti mission-critical |
| NAKIVO Replication | 2-5 min | Media | $$ | PMI con budget moderato |
| DB Replication + App Switch | < 30 sec | Alta | Gratuito | Applicazioni database-centric |
| DNS-Based Cutover | 1-5 min * | Bassa | Gratuito | Web server, API stateless |
| Load Balancer Switching | < 5 sec | Media | Gratuito/$ | Applicazioni dietro LB |
| Hybrid Multi-Technique | < 30 sec | Molto Alta | Variabile | Architetture multi-tier |
| App-Level Failover | < 10 sec | Media | Gratuito | App con failover nativo |

\* DNS downtime percepito varia in base al client cache behavior

---

## Best Practice per Migrazione a Minimo Downtime

1. **Non esiste un approccio universale** — scegliere la tecnica in base all'applicazione specifica
2. **Testare il cutover** almeno 2 volte su un ambiente di test prima della produzione
3. **Preparare un runbook dettagliato** con timestamp e responsabili per ogni step
4. **Avere un piano di rollback** documentato e testato per ogni fase
5. **Ridurre il TTL DNS almeno 48 ore prima** del cutover pianificato
6. **Monitorare attivamente** durante e dopo il cutover con dashboard in tempo reale
7. **Comunicare chiaramente** tempi e impatti a tutti gli stakeholder
8. **La replicazione database nativa** è SEMPRE preferibile alla copia file
9. **Pianificare il cutover nelle ore di minor traffico** anche con downtime minimo
10. **Documentare ogni migrazione** per migliorare il processo iterativamente

---

## Approfondimenti — note del 2026-04-26

> **Approfondimento — DNS-aware proxy "splitter" per cutover progressivo.** Per cutover graduali (es. 10% → 50% → 100% del traffico verso il nuovo target), invece di cambiare il record DNS in un solo step, usare un "DNS-aware proxy" come Cloudflare Workers, Fastly Compute, o un HAProxy con `random` di routing. Questo permette di osservare il comportamento sul nuovo backend prima di completare il cutover. Vantaggio: rollback granulare. Svantaggio: setup complesso, costo extra.

> **Errore comune — Promote DB slave senza fence del master.** Sintomo: dopo aver promosso lo slave su Proxmox, alcune scritture continuano sul master VMware (perche il client cached la connection o il DNS). Risultato: split-brain con dati divergenti. Soluzione: prima di promote, **disabilitare scritture sul master** (es. PostgreSQL: `pg_ctl stop` o `ALTER SYSTEM SET default_transaction_read_only = on`); per MSSQL AG, `ALTER AVAILABILITY GROUP FAILOVER` con automatic seeding fa il lock automaticamente. Per MySQL, `SET GLOBAL read_only = 1` sul master prima di promote slave.

> **Caso reale — Connection drain insufficient su LB switching.** Un'app con sessioni TCP long-lived (websocket, SSE) ha visto chiusure forzate quando il LB ha drained la VM-VMware. Causa: `weight 0` in HAProxy non termina connessioni esistenti, ma con `option httpclose` o `option forceclose` si: e sono state forzate. Soluzione: configurare `option http-server-close` (gentile) e aspettare il completamento naturale (con `--max-conn` per evitare overload). Per websocket: `tcp-check connect` per verificare il backend, ma drain manuale con timeout esplicito (`stick-table store conn_cur`).

---

## Esercizi

1. **Concettuale — scelta approccio.** Per ognuno: (a) e-commerce con DB Postgres 200 GB; (b) gateway API stateless; (c) Active Directory Domain Controller; (d) sistema legacy con applicazione monolitica e SQL Server. *Risposte:* (a) hybrid (Approach 5: DB replication + LB switching); (b) Approach 4 (LB switching); (c) Approach 6 (AD replication, FSMO transfer); (d) Approach 1 (Veeam con replica continua) o hybrid se si puo separare DB da app.
2. **Lab — Postgres streaming replication cutover.** Su due VM: (a) `pg_basebackup` dalla VM-VMware verso VM-Proxmox; (b) configurare `standby.signal` e `primary_conninfo`; (c) avviare lo slave; (d) verificare lag con `pg_stat_replication`; (e) eseguire cutover: `ALTER SYSTEM SET default_transaction_read_only = on` sul master, attendere lag = 0, `pg_ctl promote` sul slave, aggiornare connection string client. Misurare downtime totale dal client perspective.
3. **Scenario — DNS TTL = 86400 s residuo.** Hai bisogno di cutover urgente ma il TTL del record A e 86400 s (24 h). Spiega in 8 righe: perche non puoi semplicemente cambiare DNS adesso e aspettare; quale workaround applicare (LB intermedio, NAT routing); rischi del workaround. *Risposta:* il TTL alto significa che molti resolver hanno cached il vecchio IP per fino a 24 h; cambiarlo adesso si vede solo dopo. Workaround: deploy un reverse proxy temporaneo sul vecchio IP che inoltra al nuovo backend; oppure NAT sull'edge router. Rischi: doppia latenza, single point of failure aggiuntivo, complessita rollback.
4. **Stretch — hybrid 3-tier cutover automation.** Scrivere uno script orchestrator (Bash o Python) che, per un'app 3-tier (web nginx, app java, db postgres), esegue: (1) drain LB web-tier; (2) drain LB app-tier; (3) verify DB replication lag; (4) promote DB slave; (5) re-route LB app-tier al nuovo DB; (6) re-enable LB web-tier verso new app-tier; (7) update DNS web-tier. Includere step di rollback ad ogni fase. Riferimento: book "Designing Data-Intensive Applications" di Martin Kleppmann (O'Reilly, ISBN 978-1449373320).

## Auto-valutazione

1. Quanti tipi/approcci di live migration sono trattati nel modulo, e quale e il piu indicato per stateless app?
2. Quale e il TTL DNS raccomandato per cutover (in secondi) e quanto prima del cutover va abbassato?
3. Comando PostgreSQL per verificare lag di replica streaming?
4. Comando MySQL/MariaDB per fermare lo slave e disconnetterlo permanentemente?
5. Cosa fa `weight 0` su HAProxy backend e come si differenzia da `disabled`?
6. AD: quali ruoli FSMO vanno trasferiti per cambio DC e con quale comando PowerShell?
7. Quale tool commerciale offre replica VMware → KVM nativa con orchestratore di failover?
8. In un cutover hybrid 3-tier, qual e l'ordine corretto: web-app-db oppure db-app-web?

## Letture primarie consigliate

- [`PG-REPL`] PostgreSQL Streaming Replication. https://www.postgresql.org/docs/current/warm-standby.html#STREAMING-REPLICATION
- [`MYSQL-REPL`] MySQL Replication. https://dev.mysql.com/doc/refman/8.0/en/replication.html
- [`MSSQL-AG`] SQL Server Always On Availability Groups. https://learn.microsoft.com/en-us/sql/database-engine/availability-groups/windows/overview-of-always-on-availability-groups-sql-server
- HAProxy Documentation. https://docs.haproxy.org/
- Nginx upstream module. https://nginx.org/en/docs/http/ngx_http_upstream_module.html
- AWS ALB Target Group Connection Draining. https://docs.aws.amazon.com/elasticloadbalancing/latest/application/target-group-connection-termination.html
- Veeam Backup & Replication Documentation. https://www.veeam.com/documentation-guides-datasheets.html
- Cloudflare DNS — TTL best practices. https://developers.cloudflare.com/dns/manage-dns-records/reference/ttl/

## Collegamenti incrociati

- Modulo 06.1 — `strategie-metodi-migrazione.md`: il quadro generale.
- Modulo 06.2 — `migrazione-con-virt-v2v.md`: tool per la fase di clone iniziale.
- Modulo 07.1 — `../07-MIGRAZIONE-NETWORKING/ip-planning-dns-dhcp-firewall.md`: planning IP e DNS dettagliato.
- Modulo 09.1 — `../09-SCENARI-MIGRAZIONE-SPECIFICI/migrazione-applicazioni-stateful.md`: applicazioni stateful con replicazione.
- Modulo 09.2 — `../09-SCENARI-MIGRAZIONE-SPECIFICI/migrazione-database-postgresql-mysql.md`: deep dive PostgreSQL/MySQL replication.
- Modulo 09.4 — `../09-SCENARI-MIGRAZIONE-SPECIFICI/migrazione-windows-server-vm.md`: Windows AD/Exchange replication.

## Glossario locale

| Termine | Definizione |
|---|---|
| **Live migration** | Migrazione con downtime ridotto a secondi o meno per il client. |
| **Stateful / Stateless** | VM/app con stato locale (DB, file) vs senza stato locale (cache esterna, sessioni in DB). |
| **Replication lag** | Ritardo fra la scrittura sul master e la sua applicazione sullo slave. |
| **Promotion** | Operazione che converte uno slave in master di replica. |
| **Split-brain** | Stato in cui due nodi pensano entrambi di essere master e accettano scritture divergenti. |
| **TTL DNS** | Time To Live; secondi durante i quali un resolver tiene cached la risposta. |
| **Drain** | Periodo in cui non si accettano nuove richieste su un backend, lasciando completare le esistenti. |
| **`weight 0` (HAProxy)** | Backend riceve 0 nuove sessioni ma le esistenti continuano. |
| **AG (Always On AG)** | Availability Group di SQL Server: replica sincrona/asincrona di DB con failover. |
| **DAG (Database Availability Group)** | Equivalente Exchange di un AG. |
| **FSMO** | Flexible Single-Master Operations — ruoli speciali in Active Directory (Schema, Domain Naming, RID, PDC, Infrastructure). |
| **`pg_basebackup`** | Tool PostgreSQL per fare un backup fisico iniziale per costituire uno slave. |
| **`SHOW SLAVE STATUS`** | MySQL: comando per vedere stato della replica e seconds_behind_master. |
| **GTID** | Global Transaction ID — identificatore univoco di transazione MySQL/MariaDB usato per replication. |
| **HSRP / VRRP** | Hot Standby Router Protocol / Virtual Router Redundancy — failover di IP virtuali a livello di rete. |
| **Active-Active** | Modello in cui entrambi i nodi accettano scritture (richiede risoluzione conflitti). |
| **Active-Passive** | Solo il master accetta scritture; lo slave e in attesa di promote. |
