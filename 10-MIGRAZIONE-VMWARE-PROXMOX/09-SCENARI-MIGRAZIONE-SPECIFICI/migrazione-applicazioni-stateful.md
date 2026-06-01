# Migrazione di Applicazioni Stateful da VMware a Proxmox VE

> **Modulo del corso:** Migrazione VMware → Proxmox VE
> **Posizione nel percorso:** Fase 3 — Migrazione · Modulo 09.1 (apre il cluster scenari specifici, vedi `../00-SYLLABUS.md` §5)
> **Prerequisiti:** moduli 06.1, 06.3 (strategie e live cutover); concetti load balancer, sticky sessions, replicazione applicativa; modulo 07.1 (DNS cutover).
> **Obiettivi di apprendimento.** Al termine del modulo lo studente sara in grado di:
> 1. distinguere applicazioni "veramente stateless" (no stato locale, scalano N→N+1 senza coordinamento) da quelle "stateful" (cache locale, sessioni in memoria, queue locali, FS shared) — la differenza e tutto;
> 2. eseguire **drain-and-migrate** per app dietro load balancer: svuotamento del carico (drain), aspetto sessioni esistenti chiudano (drain timeout), spegni nodo old, deploy nuovo, ri-aggiungi al pool;
> 3. eseguire **parallel run** con traffic shift progressivo (10% → 50% → 100%), monitorando metriche su entrambi i lati per detecting regressioni;
> 4. eseguire **cluster-based rolling migration** per cluster di N nodi (Redis, Elasticsearch, RabbitMQ, Kafka), un nodo alla volta, mantenendo quorum/redundancy in ogni momento;
> 5. usare i 3 case study pratici (Redis, Elasticsearch, RabbitMQ) come template adattabili ad altre app stateful;
> 6. configurare e validare session persistence (sticky sessions) durante il cutover, e aggiornare le connection string applicative una volta completata la migrazione.
> **Tempo stimato:** lettura 90-120 min · lab 360-480 min (per simulare un caso pratico)
> **Livello:** competent → proficient (Dreyfus 3 → 4)
> **Ultimo aggiornamento:** 2026-04-26
> **Versioni di riferimento:** Redis 7.x, Elasticsearch 8.x, RabbitMQ 3.13/4.x, HAProxy 2.x/3.x, Nginx 1.24+.

## Mappa concettuale

```
+======================================================+
|  Applicazioni stateful — quattro strategie           |
+======================================================+
|                                                      |
|     [APP DIETRO LB - 1 nodo]                         |
|       Drain-and-migrate                              |
|       1. drain LB (peso 0)                           |
|       2. wait connection drain (5-10 min)            |
|       3. stop VM old                                 |
|       4. clone VM new su Proxmox                     |
|       5. add new VM al LB pool                       |
|       Downtime: 0 nuove richieste; sessioni vecchie  |
|                  chiuse o transferite                |
|                                                      |
|     [APP DIETRO LB - parallel run]                   |
|       Traffic shift gradient                         |
|       1. deploy new VM su Proxmox                    |
|       2. add al LB pool con weight 10%               |
|       3. monitor errori, latency, CPU                |
|       4. shift 10% -> 50% -> 90% -> 100%             |
|       5. remove old VM                               |
|       Downtime: 0; permette rollback granular        |
|                                                      |
|     [CLUSTER N-NODI - rolling migration]             |
|       Replace one at a time                          |
|       Per Redis/Elastic/RabbitMQ/Kafka:              |
|       1. remove node old (drain shards/partitions)   |
|       2. deploy node new su Proxmox                  |
|       3. add to cluster (re-balance)                 |
|       4. wait re-balance done                        |
|       5. repeat per ogni nodo                        |
|       Downtime: 0 (se R >= 1 sempre soddisfatto)     |
|                                                      |
|     [APP NON-CLUSTERED, NO LB]                       |
|       Cold migration con downtime                    |
|       (per app legacy senza HA built-in)             |
|                                                      |
+======================================================+
```

Idee guida del modulo:

1. **Stateful e una quesione di stato del singolo nodo, non di "ha persistenza".** Un'app puo avere DB persistent (in PostgreSQL esterno) ed essere stateless dal punto di vista del nodo applicativo. Capire dove vive lo stato e il primo step.
2. **Drain timeout e fondamentale.** HAProxy `weight 0` non killa connessioni esistenti; aspettare il drain naturale (fino a `timeout client` + `timeout server`, tipicamente 30 s - 2 min). Se l'app ha sessioni long-lived (websocket, SSE, RDP), drain timeout puo essere ore.
3. **Cluster rolling migration richiede quorum.** Per cluster a 3 nodi con replication factor 3, perdere 1 nodo alla volta e safe (quorum 2, R=2). Per cluster a 5 nodi con R=3, ancora ok. Per N=2: NON e safe rolling, serve scaling temporaneo a 3+ prima di iniziare.
4. **Parallel run permette rollback granular.** Se a 50% si vede regressione (errore 5xx +20% sul nuovo), si fa rollback a 0% senza interruzione totale. Drain-and-migrate non offre questa granularita.
5. **Session persistence richiede planning.** Sticky sessions su LB significa che gli utenti restano sullo stesso backend; durante migrate, le sessioni "stick" al nodo vecchio finche non chiudono. Le opzioni: (a) aspettare drain (drain timeout = max session length); (b) implementare session migration (Redis-based session store esterno). Per app legacy senza session migration, drain e l'unica.

## Indice
- [Panoramica](#panoramica)
- [Caratteristiche delle Applicazioni Stateful](#caratteristiche-delle-applicazioni-stateful)
- [Strategie di Migrazione](#strategie-di-migrazione)
- [Drain-and-Migrate: Strategia con Svuotamento del Carico](#drain-and-migrate-strategia-con-svuotamento-del-carico)
- [Parallel Run con Traffic Shift tramite Load Balancer](#parallel-run-con-traffic-shift-tramite-load-balancer)
- [Cluster-Based Rolling Migration](#cluster-based-rolling-migration)
- [Caso Pratico: Redis Replication Cutover](#caso-pratico-redis-replication-cutover)
- [Caso Pratico: Elasticsearch Cluster Rolling Migration](#caso-pratico-elasticsearch-cluster-rolling-migration)
- [Caso Pratico: RabbitMQ Cluster Migration](#caso-pratico-rabbitmq-cluster-migration)
- [Session Persistence e Sticky Sessions](#session-persistence-e-sticky-sessions)
- [Validazione della Sincronizzazione dello Stato](#validazione-della-sincronizzazione-dello-stato)
- [Aggiornamento Configurazioni Applicative](#aggiornamento-configurazioni-applicative)
- [Stress Testing su Proxmox Prima del Cutover](#stress-testing-su-proxmox-prima-del-cutover)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Riferimenti](#riferimenti)

---

## Panoramica

Le applicazioni stateful rappresentano la categoria più complessa da migrare tra hypervisor. A differenza dei servizi stateless, dove ogni istanza è intercambiabile e il load balancer può semplicemente dirottare il traffico su nuove istanze, le applicazioni stateful mantengono dati in memoria, sessioni utente, connessioni persistenti, cache locali, e code di messaggi che non possono essere semplicemente ricreati da zero. La perdita di questo stato durante la migrazione si traduce direttamente in impatto sull'utente finale: sessioni disconnesse, transazioni perse, cache invalidate, e potenzialmente corruzione dei dati.

La sfida della migrazione VMware→Proxmox per queste applicazioni non è solo tecnica ma anche organizzativa. I sistemi come Redis, Elasticsearch, RabbitMQ, e le applicazioni web con sessioni server-side richiedono una coordinazione precisa tra il team infrastruttura (che gestisce la migrazione delle VM), il team applicativo (che deve validare lo stato), e il team operations (che monitora il servizio durante la transizione). Ogni sistema ha le proprie primitive di replica, failover, e recovery che devono essere sfruttate per minimizzare il downtime.

Questo documento presenta tre strategie di migrazione fondamentali — drain-and-migrate, parallel run con traffic shift, e cluster-based rolling — con casi pratici dettagliati per Redis, Elasticsearch, e RabbitMQ. Per ciascun sistema, viene fornita la procedura completa dalla preparazione al cutover, con i comandi specifici per la validazione dello stato e la verifica dell'integrità post-migrazione.

---

## Caratteristiche delle Applicazioni Stateful

### Tipologie di Stato

Le applicazioni stateful mantengono diversi tipi di stato, ciascuno con implicazioni diverse per la migrazione:

| Tipo di Stato | Esempi | Persistenza | Impatto Perdita |
|---|---|---|---|
| Sessioni utente | HTTP sessions, JWT in-memory | Volatile/Semi-persistente | Logout forzato, UX degradata |
| Cache applicativa | Redis cache, Memcached, local cache | Volatile | Performance degradata, cold start |
| Code di messaggi | RabbitMQ queues, Kafka topics | Persistente | Perdita messaggi, transazioni incomplete |
| Indici di ricerca | Elasticsearch indices, Solr cores | Ricostruibile | Downtime ricerca, ricostruzione lenta |
| Connessioni persistenti | WebSocket, database connection pools | Volatile | Disconnessioni, errori applicativi |
| Stato cluster | Cluster membership, leader election | Semi-persistente | Split-brain, dati inconsistenti |

### Matrice di Rischio per Tipo di Applicazione

```
Rischio migrazione:  BASSO ◄──────────────────────► ALTO

Cache pura         ●○○○○   Ricostruibile, nessun dato critico
(Memcached)

Web app con        ●●○○○   Sessioni perse = logout utente
sessioni

Redis con          ●●●○○   Dati applicativi, richiede replica
persistence

Elasticsearch      ●●●●○   Cluster state, shard rebalancing
cluster

RabbitMQ con       ●●●●●   Messaggi in-flight, mirrored queues
mirrored queues

Applicazione       ●●●●●   Stato complesso, connessioni long-lived
custom stateful
```

---

## Strategie di Migrazione

### Confronto delle Strategie

| Criterio | Drain-and-Migrate | Parallel Run + LB | Cluster Rolling |
|---|---|---|---|
| Downtime | Medio (minuti) | Quasi-zero | Zero |
| Complessità | Bassa | Media | Alta |
| Requisiti risorse | 1x (riuso risorse) | 2x (doppia infrastruttura) | 1.3-1.5x (nodi extra) |
| Applicabilità | Qualsiasi app | App dietro LB | Solo app clusterizzate |
| Rischio dati | Basso (stato drenato) | Medio (split state) | Basso (replica nativa) |
| Rollback | Facile | Facile (switch LB) | Medio |

---

## Drain-and-Migrate: Strategia con Svuotamento del Carico

Questa strategia è la più semplice e sicura. Consiste nel rimuovere gradualmente il carico dall'applicazione, attendere che lo stato in-flight sia completamente processato, migrare la VM, e ripristinare il carico.

### Architettura

```
FASE 1: Stato Normale
┌──────────┐     ┌──────────────┐     ┌──────────────┐
│  Client   │────▶│ Load Balancer│────▶│  App Server  │
│           │     │              │     │  (VMware)    │
└──────────┘     └──────────────┘     └──────────────┘

FASE 2: Drain
┌──────────┐     ┌──────────────┐     ┌──────────────┐
│  Client   │────▶│ Load Balancer│──X──│  App Server  │ ← Nessun nuovo traffico
│           │     │  (drain mode)│     │  (VMware)    │ ← Processa richieste in-flight
└──────────┘     └──────────────┘     └──────────────┘

FASE 3: Migrazione
                                      ┌──────────────┐
                                      │  App Server  │ ← Spenta, VMDK convertito
                                      │  (VMware→PVE)│
                                      └──────────────┘

FASE 4: Ripristino
┌──────────┐     ┌──────────────┐     ┌──────────────┐
│  Client   │────▶│ Load Balancer│────▶│  App Server  │
│           │     │              │     │  (Proxmox)   │
└──────────┘     └──────────────┘     └──────────────┘
```

### Implementazione con HAProxy

```haproxy
# haproxy.cfg — Drain del server prima della migrazione

frontend http_front
    bind *:80
    default_backend app_servers

backend app_servers
    balance roundrobin
    option httpchk GET /health
    # Server in fase di drain: accetta solo connessioni esistenti
    server app1-vmware 10.0.1.10:8080 check drain
    # Server Proxmox pronto (aggiunto dopo la migrazione)
    # server app1-proxmox 10.0.1.20:8080 check
```

```bash
# Mettere il server in drain mode via socket HAProxy
echo "set server app_servers/app1-vmware state drain" | socat stdio /var/run/haproxy/admin.sock

# Monitorare le connessioni attive
echo "show stat" | socat stdio /var/run/haproxy/admin.sock | grep app1-vmware | cut -d',' -f5
# Quando il conteggio connessioni attive raggiunge 0, procedere con la migrazione

# Dopo la migrazione, aggiungere il nuovo server
echo "set server app_servers/app1-proxmox state ready" | socat stdio /var/run/haproxy/admin.sock
```

### Implementazione con NGINX

```nginx
# nginx.conf — Drain tramite rimozione dall'upstream

upstream app_backend {
    # Commentare il server VMware e aggiungere il server Proxmox
    # server 10.0.1.10:8080;
    server 10.0.1.20:8080;
}
```

```bash
# Reload senza interruzione delle connessioni attive
nginx -s reload
```

---

## Parallel Run con Traffic Shift tramite Load Balancer

Questa strategia prevede l'esecuzione contemporanea dell'applicazione su VMware e Proxmox, con spostamento graduale del traffico. È particolarmente adatta per applicazioni web stateless o semi-stateful dove lo stato può essere centralizzato.

### Procedura di Traffic Shift Graduale

```
Fase    VMware    Proxmox    Durata       Validazione
─────────────────────────────────────────────────────────
  1     100%      0%         Baseline     Metriche normali
  2     90%       10%        30 min       Error rate, latenza
  3     75%       25%        1 ora        Performance, logs
  4     50%       50%        2 ore        Carico completo
  5     25%       75%        1 ora        Conferma stabilità
  6     0%        100%       Permanente   Monitoraggio 24h
```

### Configurazione HAProxy con Weight Graduale

```haproxy
backend app_servers
    balance roundrobin
    option httpchk GET /health

    # Fase iniziale: tutto su VMware
    server app-vmware 10.0.1.10:8080 check weight 100
    server app-proxmox 10.0.1.20:8080 check weight 0

    # Fase 2: 10% su Proxmox
    # server app-vmware 10.0.1.10:8080 check weight 90
    # server app-proxmox 10.0.1.20:8080 check weight 10
```

```bash
# Shift progressivo via socket
echo "set weight app_servers/app-vmware 90" | socat stdio /var/run/haproxy/admin.sock
echo "set weight app_servers/app-proxmox 10" | socat stdio /var/run/haproxy/admin.sock

# Monitorare il bilanciamento
watch -n 5 'echo "show stat" | socat stdio /var/run/haproxy/admin.sock | cut -d"," -f1,2,5,8,34'
```

---

## Cluster-Based Rolling Migration

Per applicazioni nativamete clusterizzate (Elasticsearch, RabbitMQ, Redis Cluster, Kafka), la migrazione più elegante consiste nell'aggiungere nodi Proxmox al cluster esistente, attendere la sincronizzazione, e rimuovere i nodi VMware uno alla volta.

### Schema Generale

```
FASE 1: Cluster originale (3 nodi VMware)
┌─────────┐   ┌─────────┐   ┌─────────┐
│ Node A  │───│ Node B  │───│ Node C  │
│ VMware  │   │ VMware  │   │ VMware  │
└─────────┘   └─────────┘   └─────────┘

FASE 2: Aggiungere nodi Proxmox al cluster
┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
│ Node A  │───│ Node B  │───│ Node C  │───│ Node D  │───│ Node E  │───│ Node F  │
│ VMware  │   │ VMware  │   │ VMware  │   │ Proxmox │   │ Proxmox │   │ Proxmox │
└─────────┘   └─────────┘   └─────────┘   └─────────┘   └─────────┘   └─────────┘

FASE 3: Drenare e rimuovere nodi VMware
                                          ┌─────────┐   ┌─────────┐   ┌─────────┐
                                          │ Node D  │───│ Node E  │───│ Node F  │
                                          │ Proxmox │   │ Proxmox │   │ Proxmox │
                                          └─────────┘   └─────────┘   └─────────┘
```

---

## Caso Pratico: Redis Replication Cutover

Redis supporta la replica master-replica nativa, rendendo la migrazione relativamente lineare.

### Setup della Replica VMware → Proxmox

```bash
# Sul server Redis Proxmox (nuova istanza vuota)
# redis.conf
port 6379
bind 0.0.0.0
replicaof 10.0.1.10 6379    # IP del Redis master su VMware
replica-read-only yes
# Se il master richiede autenticazione:
masterauth your_redis_password
requirepass your_redis_password
```

```bash
# Avviare Redis sul server Proxmox
systemctl start redis-server

# Verificare lo stato della replica
redis-cli -a your_redis_password INFO replication
# Deve mostrare:
# role:slave
# master_host:10.0.1.10
# master_link_status:up
# master_sync_in_progress:0
```

### Monitoraggio della Sincronizzazione

```bash
# Sul master VMware: verificare la replica connessa
redis-cli -a your_redis_password INFO replication
# connected_slaves:1
# slave0:ip=10.0.1.20,port=6379,state=online,offset=<N>,lag=0

# Verificare il lag
redis-cli -a your_redis_password --latency-history -i 5

# Confrontare il numero di chiavi
redis-cli -a your_redis_password -h 10.0.1.10 DBSIZE
redis-cli -a your_redis_password -h 10.0.1.20 DBSIZE
# I conteggi devono corrispondere
```

### Procedura di Cutover

```bash
# 1. Verificare che la replica sia completamente sincronizzata
redis-cli -a your_redis_password -h 10.0.1.20 INFO replication | grep master_link_status
# Deve essere: master_link_status:up

# 2. (Opzionale) Impostare il master VMware in read-only
redis-cli -a your_redis_password -h 10.0.1.10 CONFIG SET slave-read-only yes
# Nota: non esiste un vero "read-only mode" per il master in Redis
# Alternativa: rinominare il comando WRITE
# O bloccare a livello di firewall

# 3. Attendere la propagazione degli ultimi write (lag = 0)
redis-cli -a your_redis_password -h 10.0.1.20 INFO replication | grep master_repl_offset

# 4. Promuovere la replica Proxmox a master
redis-cli -a your_redis_password -h 10.0.1.20 REPLICAOF NO ONE

# 5. Verificare il nuovo ruolo
redis-cli -a your_redis_password -h 10.0.1.20 INFO replication
# Deve mostrare: role:master

# 6. Aggiornare le applicazioni per puntare al nuovo server
# Aggiornare connection string / Sentinel / DNS

# 7. Se si usa Redis Sentinel, aggiornare la configurazione
redis-cli -h sentinel-host -p 26379 SENTINEL MONITOR mymaster 10.0.1.20 6379 2
```

### Redis Sentinel per Cutover Automatico

Se Redis Sentinel è in uso, la promozione può essere gestita automaticamente:

```bash
# Forzare un failover tramite Sentinel
redis-cli -h sentinel-host -p 26379 SENTINEL FAILOVER mymaster

# Sentinel promuoverà automaticamente la replica Proxmox
# e riconfiguerà il vecchio master come replica
```

---

## Caso Pratico: Elasticsearch Cluster Rolling Migration

Elasticsearch è ideale per la rolling migration grazie alla sua architettura distribuita con shard allocation automatica.

### Fase 1: Preparare i Nodi Proxmox

```bash
# Installare Elasticsearch sulle VM Proxmox con la STESSA versione
# CRITICO: la versione deve essere identica

# elasticsearch.yml sul nodo Proxmox
cluster.name: production-cluster
node.name: es-proxmox-01
node.roles: [master, data, ingest]
network.host: 10.0.2.20
discovery.seed_hosts:
  - 10.0.1.10    # es-vmware-01
  - 10.0.1.11    # es-vmware-02
  - 10.0.1.12    # es-vmware-03
  - 10.0.2.20    # es-proxmox-01 (questo nodo)
  - 10.0.2.21    # es-proxmox-02
  - 10.0.2.22    # es-proxmox-03
cluster.initial_master_nodes:
  - es-vmware-01
  - es-vmware-02
  - es-vmware-03
```

### Fase 2: Aggiungere i Nodi Proxmox al Cluster

```bash
# Avviare Elasticsearch sui nodi Proxmox (uno alla volta)
systemctl start elasticsearch

# Verificare che il nodo si sia unito al cluster
curl -s http://10.0.2.20:9200/_cat/nodes?v
# Deve mostrare sia i nodi VMware che Proxmox

# Verificare la salute del cluster
curl -s http://10.0.2.20:9200/_cluster/health?pretty
# status deve essere "green"
```

### Fase 3: Attendere il Ribilanciamento degli Shard

```bash
# Monitorare lo shard allocation
curl -s http://10.0.2.20:9200/_cat/allocation?v
# I nuovi nodi dovrebbero iniziare a ricevere shard

# Se necessario, forzare il ribilanciamento
curl -X PUT http://10.0.2.20:9200/_cluster/settings -H 'Content-Type: application/json' -d '{
  "persistent": {
    "cluster.routing.rebalance.enable": "all",
    "cluster.routing.allocation.enable": "all"
  }
}'

# Monitorare il progresso
watch -n 10 'curl -s http://10.0.2.20:9200/_cat/shards?v | sort'
```

### Fase 4: Rimuovere i Nodi VMware (Uno alla Volta)

```bash
# Per ogni nodo VMware, nell'ordine:

# 1. Escludere il nodo dall'allocazione shard
curl -X PUT http://10.0.2.20:9200/_cluster/settings -H 'Content-Type: application/json' -d '{
  "transient": {
    "cluster.routing.allocation.exclude._name": "es-vmware-01"
  }
}'

# 2. Attendere che tutti gli shard siano migrati via
watch -n 10 'curl -s http://10.0.2.20:9200/_cat/shards?v | grep es-vmware-01 | wc -l'
# Quando il conteggio raggiunge 0, procedere

# 3. Verificare la salute del cluster (deve essere green)
curl -s http://10.0.2.20:9200/_cluster/health?pretty

# 4. Arrestare il nodo VMware
systemctl stop elasticsearch  # sul nodo VMware

# 5. Rimuovere l'esclusione per preparare il prossimo nodo
curl -X PUT http://10.0.2.20:9200/_cluster/settings -H 'Content-Type: application/json' -d '{
  "transient": {
    "cluster.routing.allocation.exclude._name": ""
  }
}'

# 6. Ripetere per ogni nodo VMware
```

### Pulizia Finale

```bash
# Aggiornare discovery.seed_hosts per rimuovere i nodi VMware
# Su ogni nodo Proxmox:
# elasticsearch.yml
discovery.seed_hosts:
  - 10.0.2.20
  - 10.0.2.21
  - 10.0.2.22

# Aggiornare i voting configuration
curl -X POST http://10.0.2.20:9200/_cluster/voting_config_exclusions?node_names=es-vmware-01,es-vmware-02,es-vmware-03

# Rolling restart dei nodi Proxmox per applicare la configurazione
```

---

## Caso Pratico: RabbitMQ Cluster Migration

RabbitMQ con mirrored queues (o quorum queues in versioni recenti) supporta la rolling migration, ma richiede attenzione particolare per le policy di mirroring e la durabilità dei messaggi.

### Preparazione

```bash
# Verificare lo stato del cluster RabbitMQ attuale
rabbitmqctl cluster_status

# Verificare le policy di mirroring
rabbitmqctl list_policies

# Verificare le quorum queues
rabbitmqctl list_queues name type durable messages
```

### Aggiungere Nodi Proxmox al Cluster

```bash
# Sul nodo Proxmox: installare RabbitMQ (stessa versione!)
# Copiare il cookie Erlang dal cluster esistente
scp root@rmq-vmware-01:/var/lib/rabbitmq/.erlang.cookie /var/lib/rabbitmq/.erlang.cookie
chown rabbitmq:rabbitmq /var/lib/rabbitmq/.erlang.cookie
chmod 400 /var/lib/rabbitmq/.erlang.cookie

# Avviare RabbitMQ
systemctl start rabbitmq-server

# Unirsi al cluster
rabbitmqctl stop_app
rabbitmqctl join_cluster rabbit@rmq-vmware-01
rabbitmqctl start_app

# Verificare
rabbitmqctl cluster_status
```

### Migrare le Mirrored Queues

```bash
# Aggiornare la policy di mirroring per includere i nodi Proxmox
# e mantenere la ridondanza durante la transizione
rabbitmqctl set_policy ha-all ".*" '{
  "ha-mode": "exactly",
  "ha-params": 3,
  "ha-sync-mode": "automatic",
  "ha-promote-on-shutdown": "always"
}' --apply-to queues

# Verificare la sincronizzazione delle code
rabbitmqctl list_queues name slave_pids synchronised_slave_pids
```

### Rimuovere i Nodi VMware

```bash
# Per ogni nodo VMware:

# 1. Verificare che le code siano sincronizzate su almeno 2 nodi Proxmox
rabbitmqctl list_queues name slave_pids synchronised_slave_pids

# 2. Rimuovere il nodo dal cluster
# Sul nodo VMware:
rabbitmqctl stop_app
rabbitmqctl reset

# Su un nodo Proxmox:
rabbitmqctl forget_cluster_node rabbit@rmq-vmware-01

# 3. Verificare la salute del cluster
rabbitmqctl cluster_status
rabbitmqctl list_queues name messages consumers
```

### Per Quorum Queues (RabbitMQ 3.8+)

```bash
# Le quorum queues gestiscono automaticamente la membership
# Verificare i membri di ogni quorum queue
rabbitmqctl list_queues name type members online

# Il leader election avviene automaticamente quando un nodo viene rimosso
# Monitorare il processo
rabbitmqctl list_queues name type leader
```

---

## Session Persistence e Sticky Sessions

### Problema delle Sessioni durante la Migrazione

Se l'applicazione mantiene le sessioni in memoria (in-process), la migrazione della VM causa la perdita di tutte le sessioni attive. Le soluzioni, in ordine di preferenza:

1. **Sessioni esternalizzate** (Redis, database) — nessun impatto sulla migrazione
2. **Session replication** tra i nodi — le sessioni sopravvivono al failover
3. **Sticky sessions** con drain — le sessioni esistenti vengono completate, le nuove vanno al nuovo server

### Configurazione Sticky Sessions con HAProxy

```haproxy
backend app_servers
    balance roundrobin
    cookie SERVERID insert indirect nocache

    # Durante la migrazione: drain del server VMware
    # Le sessioni esistenti (con cookie) continuano sul VMware
    # Le nuove sessioni (senza cookie) vanno al Proxmox
    server app-vmware 10.0.1.10:8080 check cookie vmw drain
    server app-proxmox 10.0.1.20:8080 check cookie pve
```

### Sessioni Esternalizzate su Redis

```python
# Esempio Flask con Redis session store
from flask import Flask
from flask_session import Session
import redis

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = redis.Redis(
    host='redis-vip.internal',  # VIP o DNS che punta al Redis attuale
    port=6379,
    password='secret'
)
Session(app)
```

Quando Redis viene migrato (come descritto nella sezione dedicata), le sessioni vengono automaticamente trasferite. Le applicazioni non richiedono alcuna modifica.

---

## Validazione della Sincronizzazione dello Stato

### Checklist di Validazione per Ogni Sistema

```bash
# Redis: confrontare le chiavi
redis-cli -h vmware-redis DBSIZE
redis-cli -h proxmox-redis DBSIZE
# Confrontare chiavi campione
redis-cli -h vmware-redis --scan --pattern "session:*" | head -20 | while read key; do
  echo "Key: $key"
  echo "VMware: $(redis-cli -h vmware-redis GET $key | md5sum)"
  echo "Proxmox: $(redis-cli -h proxmox-redis GET $key | md5sum)"
done

# Elasticsearch: confrontare i documenti
curl -s http://vmware-es:9200/_cat/count?v
curl -s http://proxmox-es:9200/_cat/count?v

# RabbitMQ: verificare i messaggi
rabbitmqctl -n rabbit@vmware-rmq list_queues name messages
rabbitmqctl -n rabbit@proxmox-rmq list_queues name messages
```

### Script di Validazione Automatizzato

```bash
#!/bin/bash
# validate_state.sh — Eseguire prima e dopo la migrazione

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT="/var/log/migration/state_validation_${TIMESTAMP}.txt"

echo "=== State Validation Report ===" > $REPORT
echo "Timestamp: $(date)" >> $REPORT

# Redis
echo -e "\n--- Redis ---" >> $REPORT
VMWARE_KEYS=$(redis-cli -h $REDIS_VMWARE DBSIZE | awk '{print $2}')
PROXMOX_KEYS=$(redis-cli -h $REDIS_PROXMOX DBSIZE | awk '{print $2}')
echo "VMware keys: $VMWARE_KEYS" >> $REPORT
echo "Proxmox keys: $PROXMOX_KEYS" >> $REPORT
if [ "$VMWARE_KEYS" -eq "$PROXMOX_KEYS" ]; then
  echo "STATUS: OK" >> $REPORT
else
  echo "STATUS: MISMATCH - Delta: $((VMWARE_KEYS - PROXMOX_KEYS))" >> $REPORT
fi

# Elasticsearch
echo -e "\n--- Elasticsearch ---" >> $REPORT
for index in $(curl -s http://$ES_HOST:9200/_cat/indices?h=index | grep -v '^\.' ); do
  COUNT=$(curl -s http://$ES_HOST:9200/$index/_count | jq .count)
  echo "Index $index: $COUNT docs" >> $REPORT
done

# RabbitMQ
echo -e "\n--- RabbitMQ ---" >> $REPORT
rabbitmqctl list_queues name messages consumers >> $REPORT

echo -e "\nValidation complete." >> $REPORT
cat $REPORT
```

---

## Aggiornamento Configurazioni Applicative

Dopo la migrazione, le applicazioni che si connettono ai servizi migrati devono essere aggiornate. Questo include connection string, hostname, e parametri di connessione.

### Strategie per Minimizzare le Modifiche

| Strategia | Complessità | Downtime | Raccomandato per |
|---|---|---|---|
| DNS update (TTL basso) | Bassa | Propagazione DNS | Tutti i casi |
| VIP (Virtual IP) | Bassa | Secondi | Servizi singoli |
| Service discovery (Consul, etcd) | Media | Zero | Microservizi |
| Aggiornamento config file | Media | Restart app | Applicazioni legacy |
| Environment variable update | Bassa | Restart container | Container-based |

### Esempio: Aggiornamento DNS

```bash
# Abbassare il TTL a 60 secondi PRIMA della migrazione (almeno 24h prima)
# Nella zona DNS:
redis.internal.    60    IN    A    10.0.1.10

# Al cutover: aggiornare il record
redis.internal.    60    IN    A    10.0.2.20

# Dopo 48h di stabilità: ripristinare il TTL normale
redis.internal.    3600  IN    A    10.0.2.20
```

### Esempio: Virtual IP con keepalived

```bash
# keepalived.conf sul server Proxmox
vrrp_instance VI_REDIS {
    state MASTER
    interface eth0
    virtual_router_id 51
    priority 100
    advert_int 1
    authentication {
        auth_type PASS
        auth_pass secret123
    }
    virtual_ipaddress {
        10.0.1.10/24    # Stesso IP del vecchio server VMware
    }
}
```

---

## Stress Testing su Proxmox Prima del Cutover

Prima di spostare il traffico di produzione, è essenziale validare le prestazioni sotto carico.

### Redis Benchmark

```bash
# Test di latenza
redis-benchmark -h proxmox-redis -p 6379 -a password \
  -t set,get,incr,lpush,rpush,lpop,rpop,sadd,hset \
  -n 1000000 -c 50 -d 256 --csv > redis_bench_proxmox.csv

# Confrontare con i risultati VMware
diff redis_bench_vmware.csv redis_bench_proxmox.csv
```

### Elasticsearch Benchmark con esrally

```bash
# Installare esrally
pip install esrally

# Eseguire un benchmark standard
esrally race --track=geonames --target-hosts=proxmox-es:9200 \
  --report-file=/tmp/rally_proxmox.txt

# Confrontare con baseline VMware
esrally compare --baseline=<vmware-race-id> --contender=<proxmox-race-id>
```

### RabbitMQ PerfTest

```bash
# Installare rabbitmq-perf-test
# Test di throughput
rabbitmq-perf-test -h amqp://guest:guest@proxmox-rmq:5672 \
  -x 5 -y 5 -z 300 -s 1024 --rate 10000 \
  --metrics-prometheus --metrics-tags "env=proxmox"
```

### Test Applicativo End-to-End

```bash
# Utilizzare k6, locust, o JMeter per simulare il carico reale
# Esempio con k6:
k6 run --vus 100 --duration 30m \
  --env TARGET=http://proxmox-app:8080 \
  load_test.js
```

---

## Best Practices

- **Esternalizzare lo stato** (sessioni, cache) su store dedicati prima della migrazione — questo semplifica enormemente il processo e rende le applicazioni più resilienti in generale
- **Abbassare i TTL DNS** almeno 24-48 ore prima della migrazione per garantire una propagazione rapida al momento del cutover
- **Utilizzare la rolling migration** per sistemi clusterizzati — è la strategia con il minimo impatto sul servizio
- **Non migrare mai tutti i nodi di un cluster contemporaneamente** — mantenere sempre il quorum durante la transizione
- **Validare lo stato con script automatizzati** prima e dopo ogni fase della migrazione, non solo alla fine
- **Eseguire stress test sulla nuova infrastruttura** con carico realistico prima di spostare il traffico di produzione
- **Mantenere i nodi VMware operativi** come fallback per almeno 7 giorni dopo il cutover completo
- **Documentare tutte le connection string e hostname** che devono essere aggiornati — creare una matrice di dipendenze
- **Usare health check attivi** nel load balancer per rilevare automaticamente problemi post-migrazione
- **Pianificare la migrazione durante i periodi di basso traffico** per ridurre il rischio e semplificare il rollback
- **Monitorare attivamente** error rate, latenza, e throughput durante e dopo il cutover — definire soglie di abort chiare
- **Comunicare il piano** a tutti i team coinvolti e stabilire un canale di comunicazione dedicato durante la migrazione

---

## Troubleshooting

### Problema: Split-Brain nel Cluster dopo la Migrazione

**Sintomi**: Il cluster mostra due partizioni indipendenti: i nodi VMware operano separatamente dai nodi Proxmox. Entrambe le partizioni accettano scritture, causando divergenza dei dati.

**Causa**: Perdita di connettività di rete tra i nodi VMware e Proxmox durante la fase in cui entrambi i gruppi sono parte del cluster. Firewall, VLAN errata, o routing non configurato tra le due reti.

**Soluzione**: Identificare quale partizione ha i dati più recenti/completi. Arrestare la partizione con dati stale. Per Elasticsearch, utilizzare `_cluster/reroute` per forzare l'allocazione. Per RabbitMQ, seguire la procedura di partition recovery documentata. Per Redis Cluster, utilizzare `CLUSTER FAILOVER FORCE` sul nodo corretto.

**Prevenzione**: Verificare la connettività di rete bidirezionale tra tutti i nodi (VMware e Proxmox) prima di aggiungere nuovi nodi al cluster. Utilizzare un network overlay o assicurarsi che le VLAN siano correttamente configurate. Testare con `ping`, `telnet`, e test applicativo.

---

### Problema: Perdita di Messaggi RabbitMQ durante la Migrazione

**Sintomi**: Alcuni messaggi pubblicati durante il periodo di migrazione non vengono consegnati ai consumer. I conteggi dei messaggi non corrispondono tra produttore e consumatore.

**Causa**: La coda non è configurata come durabile o i messaggi non sono stati pubblicati con `delivery_mode = 2` (persistent). Durante il failover di un nodo, i messaggi in memoria vengono persi. Le mirrored queues non erano completamente sincronizzate al momento della rimozione del nodo VMware.

**Soluzione**: Verificare lo stato di sincronizzazione delle code prima di rimuovere qualsiasi nodo. Per quorum queues, verificare che tutti i membri siano online. Se messaggi sono stati persi, attivare i meccanismi di retry a livello applicativo (dead letter exchange, republish from source).

**Prevenzione**: Utilizzare quorum queues (RabbitMQ 3.8+) al posto delle mirrored queues. Assicurarsi che tutte le code siano durabili e che i messaggi siano persistent. Verificare la sincronizzazione completa prima di ogni rimozione nodo. Configurare `ha-sync-mode: automatic`.

---

### Problema: Latenza Elevata nelle Connessioni Cross-Hypervisor

**Sintomi**: Durante la fase in cui il cluster è distribuito tra VMware e Proxmox, la latenza delle operazioni aumenta significativamente. Il throughput si riduce.

**Causa**: Il traffico tra nodi VMware e Proxmox attraversa più hop di rete rispetto al traffico intra-hypervisor. Le VM su hypervisor diversi possono trovarsi su segmenti di rete con banda limitata o latenza elevata.

**Soluzione**: Verificare il percorso di rete tra i nodi con `traceroute` e `mtr`. Ottimizzare il routing per minimizzare gli hop. Se possibile, collegare entrambi gli hypervisor allo stesso switch L2 o configurare un bridge dedicato per il traffico inter-cluster.

**Prevenzione**: Pianificare la topologia di rete prima della migrazione. Allocare una rete dedicata per il traffico di replica/cluster tra VMware e Proxmox. Misurare la latenza inter-hypervisor e confrontarla con la latenza intra-cluster prima di iniziare.

---

### Problema: Sessioni Utente Perse durante il Traffic Shift

**Sintomi**: Gli utenti vengono disconnessi o perdono il carrello/stato quando il traffico viene spostato dal server VMware a quello Proxmox. L'error rate applicativo aumenta durante la transizione.

**Causa**: Le sessioni sono memorizzate in-process (memoria del server applicativo) e non sono condivise tra le istanze VMware e Proxmox. Il load balancer invia le richieste dell'utente a un server diverso da quello che detiene la sessione.

**Soluzione**: Implementare sticky sessions nel load balancer per garantire che le sessioni esistenti continuino sul server originale. Utilizzare il drain mode per il server VMware: nessuna nuova sessione, le esistenti vengono completate. Alternativa migliore: esternalizzare le sessioni su Redis prima della migrazione.

**Prevenzione**: Esternalizzare le sessioni su uno store condiviso (Redis, database) come prerequisito della migrazione. Se non è possibile, configurare sticky sessions con drain mode e pianificare un periodo di transizione sufficiente per l'esaurimento naturale delle sessioni attive.

---

### Problema: Elasticsearch Shard Allocation Bloccata

**Sintomi**: Dopo l'aggiunta dei nodi Proxmox, gli shard non vengono ribilanciati. La cluster health rimane "yellow" o "red". I nuovi nodi mostrano 0 shard allocati.

**Causa**: L'allocation è disabilitata (spesso lasciata disabilitata dopo un'operazione di manutenzione precedente), i filtri di allocazione escludono i nuovi nodi, il disco sui nuovi nodi è sopra la watermark, o c'è un mismatch nelle versioni di Elasticsearch.

**Soluzione**: Verificare le impostazioni del cluster:
```bash
curl -s http://es-host:9200/_cluster/settings?pretty | grep -i allocation
```
Riabilitare l'allocation se necessario. Verificare lo spazio disco con `_cat/allocation`. Verificare che la versione sia identica su tutti i nodi.

**Prevenzione**: Verificare le impostazioni del cluster prima di iniziare la migrazione. Assicurarsi che i nodi Proxmox abbiano almeno lo stesso spazio disco dei nodi VMware. Utilizzare la stessa versione esatta di Elasticsearch.

---

### Problema: Redis Replica con Dati Stale Promossa a Master

**Sintomi**: Dopo il cutover, l'applicazione legge dati vecchi o inconsistenti da Redis. Chiavi che dovrebbero esistere sono mancanti. I conteggi non corrispondono.

**Causa**: La replica non era completamente sincronizzata al momento della promozione. La rete tra master VMware e replica Proxmox aveva alta latenza o packet loss, causando un lag di replica non rilevato.

**Soluzione**: Verificare i dati critici confrontandoli con la sorgente. Se i dati sono irrecuperabili da Redis, ricostruire il cache warming dall'applicazione o dal database primario. Se il lag era piccolo, le chiavi mancanti verranno rigenerate naturalmente dall'applicazione.

**Prevenzione**: Monitorare il replication lag in tempo reale durante l'intera fase di migrazione. Non promuovere la replica finché `master_repl_offset` non corrisponde esattamente. Configurare alerting su `master_link_status` e lag.

---

## Riferimenti

- [Redis Documentation — Replication](https://redis.io/docs/management/replication/)
- [Redis Documentation — Sentinel](https://redis.io/docs/management/sentinel/)
- [Elasticsearch Documentation — Cluster Reroute](https://www.elastic.co/guide/en/elasticsearch/reference/current/cluster-reroute.html)
- [Elasticsearch Documentation — Shard Allocation Filtering](https://www.elastic.co/guide/en/elasticsearch/reference/current/shard-allocation-filtering.html)
- [RabbitMQ Documentation — Clustering](https://www.rabbitmq.com/clustering.html)
- [RabbitMQ Documentation — Quorum Queues](https://www.rabbitmq.com/quorum-queues.html)
- [HAProxy Documentation — Server States](https://www.haproxy.com/documentation/hapee/latest/load-balancing/health-checking/active-health-checks/)
- [NGINX Documentation — Upstream](https://nginx.org/en/docs/http/ngx_http_upstream_module.html)
- [keepalived Documentation](https://www.keepalived.org/manpage.html)
- [Proxmox VE Wiki — Migration](https://pve.proxmox.com/wiki/Migration_of_servers_to_Proxmox_VE)

---

## Approfondimenti — note del 2026-04-26

> **Approfondimento — Kafka rolling migration con `under_replicated_partitions`.** Per Apache Kafka cluster, durante rolling migration, monitorare la metrica `kafka.cluster:type=Partition,name=UnderReplicatedPartitions`. Deve restare a 0 durante l'intera operazione: significa che ogni partizione ha la sua replication factor target soddisfatto. Se sale > 0, fermare la migration: un altro nodo offline porterebbe perdita di disponibilita. Per Confluent Kafka, la stessa metrica via JMX o Confluent Control Center.

> **Errore comune — Drain timeout troppo basso per websocket.** Sintomo: dopo migrate di un nodo che gestiva websocket, gli utenti hanno visto "connection reset" massivo. Causa: `timeout client 5min` su HAProxy; websocket session erano > 30min. Soluzione: per backend websocket, usare `timeout client 1h` + `timeout server 1h` + `option http-server-close` per il drain controllato; in alternativa, frontare con un proxy WS-aware (Nginx con `proxy_read_timeout 3600s`).

> **Caso reale — Redis cluster migration con accidental data loss.** Un Redis cluster a 6 nodi (3 master + 3 replica) e stato migrato uno alla volta. Al terzo nodo migrato, alcuni dati sono spariti. Causa: durante il drain del master M1, le scritture sono state inoltrate al replica R1 (che diventava il nuovo master); ma R1 era ancora in fase di iniziale sync verso il nuovo nodo Proxmox. La promotion R1 → master ha perso le scritture in volo. Soluzione: prima di migrare un master, **fare failover esplicito** della partizione al replica gia disponibile (`CLUSTER FAILOVER`), aspettare conferma, *poi* drain del nodo originale. Lezione: comprendere il modello di consistency dell'app prima di rolling migration.

---

## Esercizi

1. **Concettuale — stateless or stateful?** Per ognuno: (a) Spring Boot REST API con DB esterno PostgreSQL; (b) Wordpress con MySQL e file uploads su NFS; (c) Redis cluster come session store; (d) MongoDB cluster con sharding; (e) PHP app con `session.save_path` su filesystem locale. *Risposte:* (a) stateless (stato in DB esterno); (b) parzialmente stateless (uploads sono in NFS shared, sessioni in DB); (c) stateful (Redis e DB primary); (d) stateful (MongoDB e DB); (e) stateful (sessione locale al nodo).

2. **Lab — drain-and-migrate Nginx.** Su 2 nodi Nginx dietro HAProxy con weight uguale, eseguire drain del nodo Nginx-1: (a) cambiare weight a 0 nel config HAProxy + reload; (b) verificare che nuovi traffico vada solo a Nginx-2; (c) attendere 5 min per drain delle connessioni esistenti; (d) shutdown Nginx-1. Misurare con `wrk` o `vegeta` la baseline performance (RPS, latency p99) prima, durante drain, e dopo migrate.

3. **Scenario — rolling migration Elasticsearch 5 nodi.** Hai un cluster Elasticsearch 5 nodi con index replication factor 1 (totale shard primary + 1 replica). Argomenta in 12 righe la procedura di rolling migration: (a) come escludere un nodo dallo scheduling (`cluster.routing.allocation.exclude._name`); (b) come monitorare il rebalance (`_cat/recovery`, `_cat/health`); (c) cosa fare se durante una recovery un altro nodo va offline (rischio di data loss). *Risposta attesa:* (a) `PUT _cluster/settings { "transient": { "cluster.routing.allocation.exclude._name": "node-old-1" } }`; (b) check `_cat/recovery?v` finche STATUS = done; (c) prima di passare al prossimo nodo, verificare `_cat/health = green`; se yellow, aspettare; se red, stop migration.

4. **Stretch — orchestratore parallel run automation.** Scrivere uno script Python che gestisce parallel run con traffic shift su HAProxy: (1) deploy new VM su Proxmox; (2) add con weight 10%; (3) monitor metriche per 15 min (errori, latency, throughput) confrontando old vs new; (4) se metriche OK, shift 50%; (5) ripetere fino a 100%; (6) remove old VM. Bonus: rollback automatico se metriche degradano.

## Auto-valutazione

1. Differenza fra stateful e stateless dal punto di vista del singolo nodo applicativo?
2. HAProxy `weight 0`: cosa fa esattamente alle connessioni esistenti?
3. Drain timeout per websocket: che valore configurare e perche?
4. Quali 3 cluster hanno specifici case study in questo modulo?
5. `cluster.routing.allocation.exclude._name` su Elasticsearch: cosa fa?
6. Redis cluster: comando per failover esplicito di un master partition al replica?
7. Parallel run vs drain-and-migrate: vantaggio principale di parallel run?
8. RabbitMQ rolling migration: a cosa fare attenzione quando si re-aggiunge un nodo al cluster?

## Letture primarie consigliate

- Redis Cluster specification. https://redis.io/docs/reference/cluster-spec/
- Elasticsearch — Cluster Settings. https://www.elastic.co/guide/en/elasticsearch/reference/current/cluster-update-settings.html
- RabbitMQ Clustering Guide. https://www.rabbitmq.com/clustering.html
- Kafka — Replication and ISR. https://kafka.apache.org/documentation/#replication
- HAProxy Documentation. https://docs.haproxy.org/
- Nginx — Upstream Module. https://nginx.org/en/docs/http/ngx_http_upstream_module.html
- keepalived Documentation. https://www.keepalived.org/manpage.html

## Collegamenti incrociati

- Modulo 06.3 — `../06-STRATEGIE-E-METODI-MIGRAZIONE/live-migration-minimo-downtime.md`: live migration general strategies.
- Modulo 07.1 — `../07-MIGRAZIONE-NETWORKING/ip-planning-dns-dhcp-firewall.md`: planning IP/DNS per cutover.
- Modulo 09.2 — `migrazione-database-postgresql-mysql.md`: applicazione stateful per DB SQL specifici.
- Modulo 09.3 — `migrazione-high-io-workloads.md`: workload high-I/O.
- Modulo 09.4 — `migrazione-windows-server-vm.md`: applicazione a Windows AD/Exchange.

## Glossario locale

| Termine | Definizione |
|---|---|
| **Stateful application** | App con stato locale al nodo (sessioni, cache, queue locali, file). |
| **Stateless application** | App senza stato locale; scala N → N+1 senza coordinamento; stato vive in DB/cache esterno. |
| **Drain** | Periodo in cui un nodo non riceve nuove richieste ma completa quelle esistenti. |
| **Drain-and-migrate** | Strategia: drain → wait → stop old → deploy new → re-add. |
| **Parallel run** | Strategia: deploy new in parallelo, traffic shift progressivo, monitor, complete. |
| **Rolling migration** | Strategia per cluster: replace one node at a time, mantenendo quorum. |
| **Sticky sessions** | LB feature che mantiene un client sullo stesso backend durante una sessione. |
| **`weight 0` (HAProxy)** | Backend riceve 0 nuove sessioni, esistenti continuano. |
| **Connection drain** | Tempo per le connessioni TCP esistenti di chiudersi naturalmente. |
| **`under_replicated_partitions` (Kafka)** | Metrica: numero di partizioni con replication factor non soddisfatto. |
| **Elasticsearch shard** | Unita di indice; primary + replica. |
| **Redis hash slot** | Unita di partizione cluster Redis (16384 slot totali). |
| **RabbitMQ queue mirror** | Replica di una queue su nodi diversi del cluster. |
| **`CLUSTER FAILOVER` (Redis)** | Comando per promuovere un replica a master di una partizione. |
| **`_cat/health` (Elasticsearch)** | Endpoint per status cluster: green/yellow/red. |
