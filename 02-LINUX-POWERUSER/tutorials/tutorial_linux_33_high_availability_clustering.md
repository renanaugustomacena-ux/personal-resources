# Tutorial Linux 33 — High Availability e Clustering

> **Campo:** 02-LINUX-POWERUSER
> **Scope:** Pacemaker/Corosync, keepalived VRRP, HAProxy, DRBD, Galera cluster MySQL
> **Prerequisiti:** `tutorial_linux_05_networking.md`, `tutorial_linux_18_database.md`
> **Durata stimata:** 14-18 ore

---

## Mappa concettuale

```
High Availability
│
├── Layer networking
│   ├── keepalived (VRRP — Virtual IP failover)
│   └── HAProxy (load balancer + health check)
│
├── Layer cluster
│   ├── Corosync (comunicazione cluster + heartbeat)
│   └── Pacemaker (orchestrazione risorse cluster)
│
├── Storage replicato
│   └── DRBD (Distributed Replicated Block Device)
│
└── Database HA
    ├── Galera Cluster (MySQL/MariaDB multi-primary)
    ├── PostgreSQL Patroni (già in tutorial 29)
    └── Redis Sentinel / Cluster
```

---

# Parte A — keepalived e VRRP

---

## A1. Virtual IP con keepalived

```
MASTER (VIP: 10.0.0.100)    BACKUP
10.0.0.10 ←→ 10.0.0.11

Client contatta sempre 10.0.0.100 (VIP)
Se MASTER cade, BACKUP prende il VIP in 1-2 secondi
```

```bash
# Installa su entrambi i nodi
apt install keepalived

# /etc/keepalived/keepalived.conf (MASTER)
cat > /etc/keepalived/keepalived.conf << 'EOF'
# Health check del servizio locale (es. nginx)
vrrp_script chk_nginx {
    script "/usr/bin/systemctl is-active nginx"
    interval 2     # controlla ogni 2 secondi
    weight -20     # se fallisce, riduce priorità di 20
    fall 2         # fallisce dopo 2 check negativi
    rise 3         # ripristina dopo 3 check positivi
}

vrrp_instance VI_1 {
    state MASTER          # MASTER su nodo primario
    interface eth0
    virtual_router_id 51  # deve essere uguale su tutti i nodi del gruppo
    priority 100          # priorità più alta = MASTER preferito
    advert_int 1          # annuncio VRRP ogni secondo

    authentication {
        auth_type PASS
        auth_pass segreto123
    }

    # IP virtuale
    virtual_ipaddress {
        10.0.0.100/24 dev eth0 label eth0:vip
    }

    # Monitora il servizio
    track_script {
        chk_nginx
    }

    # Notifica cambio stato
    notify_master "/etc/keepalived/notify.sh master"
    notify_backup "/etc/keepalived/notify.sh backup"
    notify_fault  "/etc/keepalived/notify.sh fault"
}
EOF
```

```bash
# /etc/keepalived/keepalived.conf (BACKUP) — uguale ma:
# state BACKUP
# priority 90   (più bassa del MASTER)

# Script notifica
cat > /etc/keepalived/notify.sh << 'EOF'
#!/bin/bash
STATE="$1"
logger "keepalived: entrato in stato $STATE"
# Notifica Slack, email, ecc.
EOF
chmod +x /etc/keepalived/notify.sh

systemctl enable --now keepalived

# Verifica
ip addr show eth0 | grep "10.0.0.100"   # visibile solo su MASTER
systemctl status keepalived
```

> **Analogia:** Il VIP di keepalived è come il numero di telefono fisso di un'azienda: il numero rimane lo stesso (10.0.0.100) anche se l'operatore (server) che risponde cambia. Il VRRP è il meccanismo che decide chi risponde al numero in ogni momento, passando il "centralino" al backup in automatico se il principale è irraggiungibile.

---

## A2. HAProxy con health check attivi

```bash
# /etc/haproxy/haproxy.cfg
cat > /etc/haproxy/haproxy.cfg << 'EOF'
global
    log /dev/log local0
    maxconn 50000
    user haproxy
    group haproxy
    daemon
    stats socket /run/haproxy/admin.sock mode 660 level admin

defaults
    log global
    mode http
    option httplog
    option dontlognull
    timeout connect 5s
    timeout client  30s
    timeout server  30s
    errorfile 503 /etc/haproxy/errors/503.http

# Stats UI
frontend stats
    bind *:8404
    stats enable
    stats uri /stats
    stats refresh 30s
    stats auth admin:password_sicura
    stats show-legends
    stats show-node

# Frontend HTTP — redirect a HTTPS
frontend http_in
    bind *:80
    default_backend redirect_https

backend redirect_https
    http-request redirect scheme https code 301

# Frontend HTTPS
frontend https_in
    bind *:443 ssl crt /etc/haproxy/certs/fullchain.pem
    
    # HSTS
    http-response set-header Strict-Transport-Security "max-age=31536000; includeSubDomains"
    
    # ACL per routing
    acl is_api path_beg /api/
    acl is_static path_beg /static/
    
    use_backend api_servers if is_api
    use_backend static_servers if is_static
    default_backend web_servers

# Backend app servers
backend web_servers
    balance leastconn
    option httpchk GET /health HTTP/1.1\r\nHost:\ localhost
    
    server web1 10.0.0.10:8000 check inter 5s fall 3 rise 2 weight 1
    server web2 10.0.0.11:8000 check inter 5s fall 3 rise 2 weight 1
    server web3 10.0.0.12:8000 check inter 5s fall 3 rise 2 backup

# Backend API
backend api_servers
    balance roundrobin
    option httpchk GET /api/health
    http-check expect status 200
    
    server api1 10.0.0.20:8001 check inter 3s
    server api2 10.0.0.21:8001 check inter 3s

# Backend TCP (es. PostgreSQL)
frontend pg_in
    bind *:5432
    mode tcp
    default_backend pg_servers

backend pg_servers
    mode tcp
    option tcp-check
    tcp-check connect port 5432
    
    server pg-primary 10.0.0.30:5432 check
    server pg-standby 10.0.0.31:5432 check backup

EOF

systemctl enable --now haproxy

# Runtime API
echo "show stat" | socat /run/haproxy/admin.sock stdio | column -t -s,
echo "disable server web_servers/web3" | socat /run/haproxy/admin.sock stdio
echo "enable server web_servers/web3" | socat /run/haproxy/admin.sock stdio
```

---

# Parte B — Pacemaker e Corosync

---

## B1. Setup cluster 2 nodi

```bash
# Installa su entrambi i nodi
apt install pacemaker corosync pcs

# Abilita pcsd
systemctl enable --now pcsd

# Imposta password per utente hacluster
passwd hacluster  # stessa password su entrambi i nodi

# Su nodo 1: autenticazione
pcs host auth node1.esempio.it node2.esempio.it \
    -u hacluster -p PASSWORD

# Setup cluster
pcs cluster setup mio-cluster \
    node1.esempio.it addr=10.0.0.10 \
    node2.esempio.it addr=10.0.0.11

pcs cluster start --all
pcs cluster enable --all

# Verifica stato
pcs status
pcs cluster status
```

---

## B2. Configurare risorse cluster

```bash
# Disabilita STONITH (per lab — in produzione configurarlo!)
pcs property set stonith-enabled=false

# Configura Virtual IP come risorsa
pcs resource create virtual_ip ocf:heartbeat:IPaddr2 \
    ip=10.0.0.100 \
    cidr_netmask=24 \
    nic=eth0 \
    op monitor interval=30s

# Configura nginx come risorsa
pcs resource create nginx ocf:heartbeat:nginx \
    configfile=/etc/nginx/nginx.conf \
    statusurl="http://localhost/nginx_status" \
    op monitor interval=30s

# Collega le risorse (VIP e nginx vanno sullo stesso nodo)
pcs resource group add web-group virtual_ip nginx

# Colocation constraint
pcs constraint colocation add nginx with virtual_ip INFINITY

# Order constraint
pcs constraint order virtual_ip then nginx

# Verifica
pcs status resources
pcs constraint show --full
```

---

# Parte C — DRBD (Storage Replicato)

---

## C1. DRBD setup

```bash
# DRBD: Distributed Replicated Block Device
# Sincronizza un block device tra 2 nodi (RAID-1 via rete)

apt install drbd-utils

# /etc/drbd.d/dati.res
cat > /etc/drbd.d/dati.res << 'EOF'
resource dati {
    protocol C;  # C = sincrono (scrittura confermata da entrambi)
                 # A = asincrono, B = semi-sincrono

    meta-disk internal;

    device /dev/drbd0;

    disk /dev/sdb;   # device fisico

    net {
        allow-two-primaries no;
        cram-hmac-alg sha256;
        shared-secret "segreto-drbd";
        verify-alg sha256;
    }

    on node1.esempio.it {
        address 10.0.0.10:7789;
    }

    on node2.esempio.it {
        address 10.0.0.11:7789;
    }
}
EOF

# Su entrambi i nodi
drbdadm create-md dati
systemctl start drbd

# Solo su nodo PRIMARY: inizializza
drbdadm -- --overwrite-data-of-peer primary dati
watch drbdadm status dati   # attendi sincronizzazione completa

# Formatta e monta (solo su primary)
mkfs.ext4 /dev/drbd0
mount /dev/drbd0 /mnt/dati

# Failover manuale
drbdadm secondary dati     # su nodo corrente primary
drbdadm primary dati       # su nodo backup
```

---

# Parte D — Galera Cluster (MariaDB)

---

## D1. Multi-primary MySQL cluster

```bash
# Galera: tutti i nodi accettano scritture (multi-primary)
# Replica sincrona basata su wsrep (write-set replication)

# Installa MariaDB con Galera su tutti i nodi (3 minimo)
apt install mariadb-server galera-4

# /etc/mysql/mariadb.conf.d/60-galera.cnf
cat > /etc/mysql/mariadb.conf.d/60-galera.cnf << 'EOF'
[mysqld]
binlog_format=ROW
innodb_autoinc_lock_mode=2

# Galera Provider
wsrep_on=ON
wsrep_provider=/usr/lib/galera/libgalera_smm.so

# Cluster configuration
wsrep_cluster_name="mio-galera-cluster"
wsrep_cluster_address="gcomm://10.0.0.30,10.0.0.31,10.0.0.32"

# Node-specific (cambia per ogni nodo)
wsrep_node_name="node1"
wsrep_node_address="10.0.0.30"

# SST (State Snapshot Transfer) — copia stato a nuovi nodi
wsrep_sst_method=mariabackup

# Performance
wsrep_sync_wait=0
innodb_flush_log_at_trx_commit=0
EOF

# Solo su primo nodo: bootstrap del cluster
galera_new_cluster

# Su nodi 2 e 3: join al cluster
systemctl start mariadb

# Verifica stato cluster
mysql -u root -e "SHOW STATUS LIKE 'wsrep_%';" | grep -E "wsrep_cluster_size|wsrep_local_state_comment|wsrep_ready"
# wsrep_cluster_size   3    (tutti i nodi)
# wsrep_local_state_comment  Synced
# wsrep_ready    ON
```

---

# Parte E — Riepilogo

## Pattern HA stack completo

```
Client
  ↓
[DNS Round-Robin / anycast]
  ↓
keepalived VIP (10.0.0.100)
  ↓
HAProxy (health-check, SSL termination, routing)
  ├── /api/ → API servers (3x)
  └── /    → Web servers (3x)
  ↓                           ↓
Pacemaker/Corosync      Galera Cluster
 ├── nginx resource       ├── node1 (R/W)
 └── VIP resource         ├── node2 (R/W)
                          └── node3 (R/W)
        DRBD (storage condiviso)
```

## Checklist HA

```bash
# Test failover VIP
systemctl stop keepalived   # su MASTER
ip addr show eth0           # VIP sparisce dal MASTER
# Su BACKUP: VIP compare automaticamente

# Test HAProxy
echo "disable server web_servers/web1" | socat /run/haproxy/admin.sock stdio
# Traffico va a web2 e web3

# Test cluster
pcs node standby node1
pcs status   # risorse migrate a node2

# Test DRBD failover
drbdadm secondary dati   # su node1
drbdadm primary dati     # su node2
mount /dev/drbd0 /mnt/dati  # accesso da node2
```

## RTO/RPO obiettivi tipici

| Componente | RTO (Recovery Time) | RPO (Recovery Point) |
|---|---|---|
| keepalived VRRP | < 2 secondi | 0 (stateless) |
| HAProxy backend fail | < 5 secondi | 0 |
| Pacemaker risorsa | 30-60 secondi | 0 |
| DRBD sync | < 1 secondo | 0 (protocollo C) |
| Galera Cluster | < 1 secondo | 0 (sincrono) |

## Prossimi passi

- `tutorial_linux_34_hardening.md` — hardening avanzato
- `tutorial_linux_29_postgresql.md` — Patroni HA PostgreSQL
