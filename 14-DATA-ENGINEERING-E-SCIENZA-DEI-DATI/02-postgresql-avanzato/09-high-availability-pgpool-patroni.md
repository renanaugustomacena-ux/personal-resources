# PostgreSQL High Availability: Patroni, pgpool

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
1. HA Concepts per PostgreSQL
2. Patroni Setup
3. Patroni Configuration
4. etcd/Consul Configuration
5. pgpool-II Setup
6. pgpool HA Mode
7. Load Balancing
8. Connection Pooling Advanced
9. Failover Testing
10. HA Best Practices

---

## 1. HA Concepts per PostgreSQL

### 1.1 Availability

L'**alta disponibilità (HA)** in PostgreSQL riguarda la capacità del sistema di rimanere operativo anche quando componenti individuali falliscono. I due parametri chiave sono:

**RTO (Recovery Time Objective)**: Il tempo massimo accettabile per ripristinare il servizio dopo un failure. Tipicamente misurato in minuti o ore.

**RPO (Recovery Point Objective)**: La quantità massima di dati che si può permettere di perdere. Per replica sincrona, RPO=0; per replica asincrona, RPO dipende dal lag.

** SLA comuni**:
- 99.9% (three nines): ~8.7 ore downtime/anno
- 99.99% (four nines): ~52 minuti downtime/anno
- 99.999% (five nines): ~5 minuti downtime/anno

### 1.2 HA Patterns

Diversi pattern per ottenere alta disponibilità:

**Streaming Replication con manual failover**: Setup base con primary e standby. Se il primary fallisce, l'amministratore esegue manualmente il failover. Semplice ma richiede intervento umano.

**Streaming Replication con automatic failover (Patroni)**: Patroni gestisce automaticamente il failover usando un DCS (Distributed Consensus Store) per coordinazione. Fornisce RTO basso senza intervento umano.

**pgpool-II per connection pooling + HA**: pgpool gestisce le connessioni e può rilevare fallimenti, smistando automaticamente le richieste al nodo sano. Offre anche load balancing.

**Cascaded Replication**: Uno standby riceve WAL da un altro standby invece che direttamente dal primary. Riduce il carico sul primary.

**Multi-master (limitato)**: PostgreSQL non supporta nativamente multi-writer. Soluzioni come BDR (Bi-Directional Replication) permettono escritture multiple ma con complessità significativa.

### 1.3 Failover Types

**Automatic Failover**: Patroni o altro sistema rileva il failure del primary e promuove automaticamente uno standby. RTO minimo, ma richiede configurazione corretta.

**Manual/Switchover**: L'amministratore triggers volontariamente un failover per manutenzione. Zero data loss, controllato.

**Cascaded Failover**: Se lo standby che diventa primary ha i propri standby, questi continuano a funzionare e si riconfigurano automaticamente.

**Failback**: Dopo la riparazione del vecchio primary, può essere riconfigurato come standby del nuovo primary. Più complesso e richiede attenzione.

---

## 2. Patroni Setup

### 2.1 What is Patroni

**Patroni** è la soluzione di high availability più utilizzata per PostgreSQL. È un framework Python che gestisce automaticamente PostgreSQL per garantire alta disponibilità.

**Caratteristiche principali**:
- **Distributed Consensus**: Usa un DCS (etcd, Consul, ZooKeeper) per coordinazione tra nodi
- **Automatic Failover**: Rileva fallimenti e promuove automaticamente uno standby
- **PostgreSQL Management**: Gestisce avvio, stop, recovery di PostgreSQL
- **REST API**: Interfaccia per monitoraggio e controllo
- **Watchdog**: Opzionale per failback hardware

**Perché Patroni**:
- Standard de facto per HA PostgreSQL
- Ben testato in produzione
- Supporta multiple backend DCS
- Completo controllo su PostgreSQL

### 2.2 Components

L'architettura Patroni coinvolge multiple componenti:

**Patroni**: Il processo Python su ogni nodo PostgreSQL. Gestisce il PostgreSQL locale, monitora lo stato, comunica con il DCS.

**Distributed Consensus Store (DCS)**: Mantiene lo stato del cluster. Può essere:
- **etcd**: Più utilizzato, semplice
- **Consul**: Più funzionalità, HashiCorp
- **ZooKeeper**: legacy, meno comune

**PostgreSQL**: Il database stesso, configurato per replica.

**HAProxy** (opzionale): Load balancer che indirizza le connessioni al primary corrente. Patroni aggiorna la configurazione HAProxy automaticamente.

** Consul**: Cluster con 3 o più nodi per quorum. Ogni nodo ha un agent Patroni e un'istanza etcd.

### 2.3 Install Patroni

Installare Patroni:

```bash
# Su ogni nodo
pip install patroni[etcd]

# Per systemd
pip install patroni[etcd] systemd

# Verificare installazione
patroni --version
```

### 2.4 Basic Configuration

Configurazione base Patroni (patroni.yml):

```yaml
# Nome del cluster
scope: postgres-cluster

# Nome del nodo (unico per ogni nodo)
name: node1

# REST API per monitoraggio
restapi:
  listen: 0.0.0.0:8008
  connect_address: 10.0.0.1:8008

# DCS configuration (etcd)
etcd:
  hosts: 10.0.0.2:2379,10.0.0.3:2379,10.0.0.4:2379

# PostgreSQL configuration
postgresql:
  data_dir: /data/postgresql
  pgpass: /tmp/pgpass
  parameters:
    listen_addresses: "0.0.0.0"
    port: 5432
    max_connections: 100
    shared_buffers: 256MB
    wal_level: replica
    max_wal_senders: 10
    wal_keep_size: 1GB
    hot_standby: on

# Bootstrap configuration
bootstrap:
  dcs:
    ttl: 30
    loop_wait: 10
    retry_timeout: 10
    maximum_lag_on_failover: 1048576
  method: basebackup
  basebackup:
    host: 10.0.0.1
    user: replicator
    password: mypassword
    checkpoint: fast

# Tags per comportamenti speciali
tags:
  nofailover: false
  noloadbalance: false
  clonefrom: false
```

**Avviare Patroni**:
```bash
# Via systemd
systemctl start patroni
systemctl enable patroni

# Via standalone
patroni patroni.yml
```

### 2.5 Verify Setup

Verificare che Patroni funzioni:

```bash
# Verificare stato del cluster
patroni-ctl show-config

# Verificare membro del cluster
patroni-ctl list

# Verificare status via API
curl http://10.0.0.1:8008/patroni
```

### 2.6 HAProxy Integration

Integrare con HAProxy per connection routing:

```ini
# /etc/haproxy/haproxy.cfg
listen postgres
    bind 10.0.0.100:5432
    option httpchk
    http-check expect status 200
    default-server inter 3s fall 3 rise 2
    server postgresql1 10.0.0.1:5432 check port 8008
    server postgresql2 10.0.0.2:5432 check port 8008
    server postgresql3 10.0.0.3:5432 check port 8008
```

Il backend di HAProxy può essere aggiornato automaticamente da Patroni.

---

## 3. Patroni Configuration

### 3.1 PostgreSQL Parameters

Parametri:
```yaml
postgresql:
  parameters:
    wal_level: replica
    max_wal_senders: 10
    wal_keep_size: 1GB
    hot_standby: on
```

### 3.2 Recovery Configuration

Recovery:
```yaml
postgresql:
  recovery_conf:
    restore_command: ''
    archive_cleanup_command: ''
```

### 3.3 Bootstrap Methods

Bootstrap:
```yaml
bootstrap:
  method: basebackup
  basebackup:
    host: 10.0.0.1
    user: replicator
```

### 3.4 Tags

Tags per controllo:
```yaml
tags:
  nofailover: true  -- disable failover
  noloadbalance: true  -- not for load balancing
```

---

## 4. etcd/Consul Configuration

### 4.1 etcd Setup

etcd per DCS:
```bash
etcd --data-dir=/var/lib/etcd --name=node1 \
  --listen-peer-urls=http://0.0.0.0:2380 \
  --listen-client-urls=http://0.0.0.0:2379 \
  --initial-advertise-peer-urls=http://10.0.0.1:2380
```

### 4.2 etcd Cluster

Cluster etcd:
- Odd number of nodes (3, 5)
- Quorum for consensus

### 4.3 Consul Alternative

Consul:
- Key-value store
- Similar to etcd
- Additional features

---

## 5. pgpool-II Setup

### 5.1 What is pgpool

**pgpool-II** è un middleware che si posiziona tra i client e PostgreSQL. Fornisce funzionalità multiple:

**Connection Pooling**: Riutilizza connessioni invece di crearne una nuova per ogni richiesta client. Riduce overhead di connessione.

**Load Balancing**: Distribuisce le query di sola lettura su multiple repliche. Migliora throughput per query read-heavy.

**Replication**: Può gestire replica interna (non necessario con streaming replication).

**HA**: Watchdog fornisce failover automatico.

**Query Caching**: Cache risultati (opzionale).

** Quando usare pgpool**:
- Applicazioni che aprono molte connessioni (ORM, connection pooling lato app debole)
- Query read-heavy dove load balancing aiuta
- HA con switchover automatico
- Caching risultati

### 5.2 Install pgpool

Installare pgpool-II:

```bash
# Debian/Ubuntu
apt-get install pgpool2

# RHEL/CentOS
yum install pgpool-II

# Verificare installazione
pgpool --version
```

### 5.3 Backend Configuration

Configurare i backend PostgreSQL:

```ini
# /etc/pgpool2/pgpool.conf

# Backend connections
backend_hostname0 = '10.0.0.1'
backend_port0 = 5432
backend_weight0 = 1
backend_data_directory0 = '/data/postgresql'
backend_flag0 = 'ALLOW_TO_FAILOVER'

backend_hostname1 = '10.0.0.2'
backend_port1 = 5432
backend_weight1 = 1
backend_data_directory1 = '/data/postgresql'
backend_flag1 = 'ALLOW_TO_FAILOVER'

# Connection pool
pool_mode = 'transaction'
num_init_children = 32
max_connections = 100

# Authentication
pool_passwd = 'pool_passwd'

# Listen addresses
listen_addresses = '*'
port = 9999
```

### 5.4 Connection Pool

Configurare il connection pooling:

```ini
# Modalità di pooling
pool_mode = transaction  # release at commit
# pool_mode = session   # release at disconnect
# pool_mode = statement  # release at statement (per autocommit)

# Numero di connessioni child
num_init_children = 32  # max 1000, default 32
max_connections = 100  # deve essere > num_init_children

# Tempo di vita
child_life_time = 300  # secondi
connection_life_time = 600
connection_max_age = 3600
```

### 5.5 Authentication Setup

Configurare autenticazione:

```bash
# Generare pool_passwd
pg_md5 --md5auth --username=myuser --password

# In pgpool.conf
pool_passwd = 'pool_passwd'
```

### 5.6 Start pgpool

Avviare pgpool:

```bash
# Avviare
systemctl start pgpool

# Verificare status
systemctl status pgpool

# Test connessione
psql -h localhost -p 9999 -U myuser -d mydb
```

---

## 6. pgpool HA Mode

### 6.1 Watchdog

pgpool-II include **Watchdog** per alta disponibilità tra nodi pgpool. Senza Watchdog, un failure di pgpool lascia le applicazioni senza accesso al database.

**Watchdog Functions**:
- Monitora lo stato degli altri nodi pgpool
- Eleige un leader per gestire il VIP
- Trigger failover se il pgpool primario fallisce
- Coordina switchover tra nodi pgpool

**Configurazione base Watchdog**:
```ini
# Enable watchdog
use_watchdog = on

# Nodi watchdog (almeno 3 per quorum)
wd_hostname1 = '10.0.0.10'
wd_port1 = 9000

wd_hostname2 = '10.0.0.11'
wd_port2 = 9000

wd_hostname3 = '10.0.0.12'
wd_port3 = 9000

# Interfaccia di rete per VIP
ifconfig_up = 'ens160'

# Heartbeat
heartbeat_destination0 = '10.0.0.10'
heartbeat_destination1 = '10.0.0.11'
heartbeat_destination2 = '10.0.0.12'

# Tempo di risposta
wd_heartbeat_deadline = 30
wd_interval = 5
```

### 6.2 Virtual IP

Il **delegate IP (Virtual IP)** permette alle applicazioni di connettersi a un IP fisso che pointing automaticamente al pgpool attivo.

**Configurazione VIP**:
```ini
# Virtual IP
delegate_ip = '10.0.0.100'

# Comando per rilevare VIP (opzionale)
validate_command = '/usr/local/bin/pgpool_valid.sh'

# Life check
lifecheck_method = 'heartbeat'
```

**Comportamento**:
- All'avvio, un nodo pgpool diventa leader e alza il VIP
- Se il leader fallisce, Watchdog elegge un nuovo leader che alza il VIP
- Le applicazioni usano `10.0.0.100:9999` e non devono sapere quale nodo è attivo

### 6.3 Failover Command

Il comando di failover viene eseguito quando pgpool rileva un failure del backend PostgreSQL.

**Configurazione failover**:
```ini
failover_command = '/usr/local/etc/pgpool_failover.sh %h %p %D %m %M %H'
```

**Parametri disponibili**:
- `%h`: hostname del nuovo primary
- `%p`: port del nuovo primary
- `%D`: database directory del nuovo primary
- `%m`: ID del nuovo primary
- `%M`: ID del vecchio primary
- `%H`: hostname del nuovo standby

**Esempio script failover**:
```bash
#!/bin/bash
# /usr/local/etc/pgpool_failover.sh
NEW_PRIMARY=$1
NEW_PRIMARY_PORT=$2

# Notificare Patroni (se usato)
curl -X POST http://patroni:8008/failover

echo "$(date): Failover to $NEW_PRIMARY:$NEW_PRIMARY_PORT" >> /var/log/pgpool/failover.log
```

### 6.4 Integration with Patroni

L'integrazione **Patroni + pgpool** è la configurazione consigliata per ambienti production:

**Architettura**:
```
[App] --> [pgpool + Watchdog] --> [Patroni + PostgreSQL]
```

**Configurazione**:
```ini
# pgpool.conf
backend_hostname0 = '10.0.0.1'
backend_port0 = 5432
backend_flag0 = 'ALLOW_TO_FAILOVER'

backend_hostname1 = '10.0.0.2'
backend_port1 = 5432
backend_flag1 = 'ALLOW_TO_FAILOVER'

# Point to HAProxy controlled by Patroni instead
# Or use Patroni's REST API as health check
```

**Patroni gestisce**:
- Failover PostgreSQL
- Aggiornamento DCS
- Replica setup

**pgpool gestisce**:
- Connection pooling
- Load balancing per read
- Failover a livello middleware

**Pattern raccomandato**:
1. pgpool usa i nodi PostgreSQL direttamente
2. Patroni comunica con pgpool via `pgpool_adaptor` per aggiornare lo stato
3. Opgionalmente, pgpool controlla lo stato via REST API di Patroni

### 6.5 Health Check

pgpool può controllare la salute dei backend:

```ini
health_check_period = 5
health_check_timeout = 30
health_check_user = 'postgres'
health_check_password = 'mypassword'
health_check_database = 'postgres'

# Retry prima di failover
health_check_max_retries = 3
health_check_retry_delay = 3
```

**Parametri importante**:
- `health_check_period`: secondi tra check
- `health_check_timeout`: timeout per singolo check
- `health_check_max_retries`: tentativi prima di dichiarare fallito

---

## 7. Load Balancing

### 7.1 Load Balance Mode

Load balance:
```ini
load_balance_mode = on
```

### 7.2 Weight Configuration

Weights:
```ini
backend_weight0 = 1
backend_weight1 = 3  -- send more to node 1
```

### 7.3 SQL Functions

Controllare balance:
```sql
SELECT pgpool_set_random();  -- switch query destination
```

### 7.4 Statement-Level Load Balance

Statement level:
- INSERT/SELECT balancing
- Per-session balancing

---

## 8. Connection Pooling Advanced

### 8.1 Pool Mode

Modes:
- **Session**: release at disconn
- **Transaction**: release at commit
- **Statement**: release at statement

### 8.2 Pool Size

Pool size:
```ini
num_init_children = 32
max_connections = 100
```

### 8.3 Connection Pool Config

Configuration:
```ini
child_life_time = 300
connection_life_time = 600
child_max_connections = 0
```

---

## 9. Failover Testing

### 9.1 Simulate Failure

Test failover:
```bash
# Kill primary
systemctl kill patroni

# Check new primary
pg_isready -h 10.0.0.2
```

### 9.2 Verify Applications

Verify:
- Applications reconnect
- No data loss
- Functionality

### 9.3 Switchover Test

Switchover:
```bash
# Trigger switchover
patroni-ctl switchover
```

### 9.4 Regular Testing

Test regolari:
- Schedule downtime for testing
- Document procedures

---

## 10. HA Best Practices

### 10.1 Design Principles

Principi:
- Simplicity
- Automation
- Monitoring

### 10.2 Monitoring

Monitorare:
- pgpool stats
- replication lag
- connection pool

### 10.3 Alerts

Alerts per:
- Replication lag
- Node down
- Failover events

### 10.4 Documentation

Documentare:
- Procedures
- Contact info
- Testing schedule

---

*Questo documento fa parte del modulo 02 "PostgreSQL Avanzato" della Data Encyclopedia.*