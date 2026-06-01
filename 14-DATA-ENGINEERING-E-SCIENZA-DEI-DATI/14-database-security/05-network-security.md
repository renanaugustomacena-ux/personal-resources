# Sicurezza di Rete per i Database

I database non devono mai essere esposti direttamente su internet. La sicurezza di rete per i database si articola in: isolamento (chi può raggiungerli?), filtraggio del traffico (cosa è permesso?), e monitoraggio (chi sta cercando di accedere?). Un database raggiungibile solo dalla rete interna e attraverso un proxy controllato riduce enormemente la superficie d'attacco.

## Isolamento di Rete

### Architettura di Rete Raccomandata

```
Internet
    │
    ▼
[Load Balancer / WAF]
    │
    ▼
[Application Tier] ─── VPC/Private Network ───┐
  Web Server 1                                  │
  Web Server 2                                  │
    │                                           │
    ▼                                           │
[Proxy Tier]                                   │
  ProxySQL / PgBouncer          Monitoring ────┘
    │                           (read-only)
    ▼
[Database Tier] ─── Isolated Subnet ─────────────
  Primary DB  →  Replica 1  →  Replica 2
  (10.0.30.10)   (10.0.30.11)  (10.0.30.12)

Regole: Database Tier accetta connessioni SOLO dal Proxy Tier
        Nessun accesso diretto da Application Tier
        Nessun accesso da Internet
```

### Configurazione Firewall (iptables / nftables)

```bash
#!/bin/bash
# firewall-db.sh: configurazione firewall per nodo database PostgreSQL

# Pulire le regole esistenti
iptables -F
iptables -X
iptables -Z

# Policy di default: DROP tutto
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# Permettere traffico locale (loopback)
iptables -A INPUT -i lo -j ACCEPT

# Permettere connessioni già stabilite
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# SSH: solo da bastion host (IP del jump server)
iptables -A INPUT -p tcp --dport 22 -s 10.0.0.5 -j ACCEPT

# PostgreSQL: solo dal proxy tier
iptables -A INPUT -p tcp --dport 5432 -s 10.0.20.0/24 -j ACCEPT

# Patroni REST API: solo da altri nodi database e monitoring
iptables -A INPUT -p tcp --dport 8008 -s 10.0.30.0/24 -j ACCEPT  # nodi db
iptables -A INPUT -p tcp --dport 8008 -s 10.0.40.0/24 -j ACCEPT  # monitoring

# etcd: solo tra nodi del cluster
iptables -A INPUT -p tcp --dport 2379 -s 10.0.30.0/24 -j ACCEPT
iptables -A INPUT -p tcp --dport 2380 -s 10.0.30.0/24 -j ACCEPT

# ICMP (ping): limitato per monitoring
iptables -A INPUT -p icmp --icmp-type echo-request -s 10.0.40.0/24 -j ACCEPT

# Log tentativi di accesso negati (per SIEM)
iptables -A INPUT -j LOG --log-prefix "DB_BLOCKED: " --log-level 4
iptables -A INPUT -j DROP

# Salvare le regole
iptables-save > /etc/iptables/rules.v4

# Equivalente con nftables (sistemi moderni)
cat > /etc/nftables.conf << 'NFTEOF'
table inet filter {
    chain input {
        type filter hook input priority 0; policy drop;

        # Connessioni stabilite
        ct state established,related accept
        
        # Loopback
        iif lo accept
        
        # SSH dal bastion
        ip saddr 10.0.0.5 tcp dport 22 accept
        
        # PostgreSQL dal proxy tier
        ip saddr 10.0.20.0/24 tcp dport 5432 accept
        
        # Replica PostgreSQL tra nodi
        ip saddr 10.0.30.0/24 tcp dport 5432 accept
        
        # Log e drop tutto il resto
        log prefix "DB_BLOCKED: " group 0
        drop
    }
}
NFTEOF
nft -f /etc/nftables.conf
```

### Security Groups in Cloud (AWS/Azure/GCP)

```json
// AWS Security Group per il Database Tier
{
  "GroupName": "db-primary-sg",
  "Description": "Security group per nodi database primari",
  "InboundRules": [
    {
      "Type": "PostgreSQL",
      "Protocol": "TCP",
      "Port": 5432,
      "Source": "sg-proxy-tier-id",
      "Description": "Accesso da proxy tier (PgBouncer)"
    },
    {
      "Type": "Custom TCP",
      "Protocol": "TCP",
      "Port": 5432,
      "Source": "sg-db-sg-id",
      "Description": "Replica streaming tra nodi database"
    },
    {
      "Type": "SSH",
      "Protocol": "TCP",
      "Port": 22,
      "Source": "sg-bastion-id",
      "Description": "SSH solo dal bastion host"
    },
    {
      "Type": "Custom TCP",
      "Protocol": "TCP",
      "Port": 8008,
      "Source": "sg-monitoring-id",
      "Description": "Patroni health check"
    }
  ],
  "OutboundRules": [
    {
      "Protocol": "All",
      "Destination": "0.0.0.0/0",
      "Description": "Tutto l'outbound (aggiornamenti, DNS, S3)"
    }
  ]
}
```

## Connection Limits e Throttling

```sql
-- Limitare le connessioni per prevenire DoS accidentale o volontario

-- Limite per database
ALTER DATABASE myapp CONNECTION LIMIT 200;
-- 200 connessioni totali al database; le nuove vengono rifiutate con:
-- FATAL: too many connections for database "myapp"

-- Limite per ruolo
ALTER ROLE app_service CONNECTION LIMIT 50;
ALTER ROLE analyst CONNECTION LIMIT 5;
ALTER ROLE monitoring CONNECTION LIMIT 3;

-- Verificare le connessioni correnti per ruolo
SELECT
  usename,
  COUNT(*) AS current_connections,
  rolconnlimit AS max_connections
FROM pg_stat_activity
JOIN pg_roles ON pg_stat_activity.usename = pg_roles.rolname
WHERE usename IS NOT NULL
GROUP BY usename, rolconnlimit
ORDER BY current_connections DESC;

-- Alertare se si avvicina al limite
SELECT
  usename,
  COUNT(*) AS connections,
  rolconnlimit,
  ROUND(COUNT(*) * 100.0 / NULLIF(rolconnlimit, -1), 1) AS pct_used
FROM pg_stat_activity
JOIN pg_roles ON pg_stat_activity.usename = pg_roles.rolname
WHERE rolconnlimit > 0
GROUP BY usename, rolconnlimit
HAVING COUNT(*) > rolconnlimit * 0.8  -- alert all'80% del limite
ORDER BY pct_used DESC;
```

## Prevenzione delle SQL Injection

```python
# SBAGLIATO: query con concatenazione di stringhe (vulnerabile)
def get_user_UNSAFE(username: str):
    query = f"SELECT * FROM users WHERE username = '{username}'"
    # Se username = "'; DROP TABLE users; --"
    # Query risultante: SELECT * FROM users WHERE username = ''; DROP TABLE users; --'
    conn.execute(query)  # DISASTRO

# CORRETTO: parametrizzazione (sempre)
def get_user_safe(username: str):
    conn.execute(
        "SELECT * FROM users WHERE username = %s",
        (username,)
    )

# CORRETTO: ORM (SQLAlchemy)
from sqlalchemy import select
from sqlalchemy.orm import Session

def get_user_orm(db: Session, username: str):
    return db.execute(
        select(User).where(User.username == username)
    ).scalar_one_or_none()
    # SQLAlchemy parametrizza automaticamente

# Query con identificatori dinamici (es. nome tabella/colonna)
# Non si possono parametrizzare; usare whitelist
import re

ALLOWED_SORT_COLUMNS = {'name', 'created_at', 'email', 'status'}

def get_users_sorted(sort_by: str, direction: str = 'ASC'):
    # Validare contro whitelist
    if sort_by not in ALLOWED_SORT_COLUMNS:
        raise ValueError(f"Colonna di ordinamento non valida: {sort_by}")
    if direction.upper() not in ('ASC', 'DESC'):
        raise ValueError(f"Direzione non valida: {direction}")
    
    # Solo ora costruire la query con l'identificatore validato
    query = f"SELECT * FROM users ORDER BY {sort_by} {direction}"
    conn.execute(query)  # sicuro perché sort_by è validato
```

```sql
-- A livello database: limitare le funzioni pericolose

-- Revocare l'accesso alle funzioni di sistema per utenti applicativi
REVOKE EXECUTE ON FUNCTION pg_read_file(text) FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION pg_ls_dir(text) FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION pg_read_binary_file(text) FROM PUBLIC;

-- Disabilitare COPY TO/FROM per utenti non privilegiati
-- (COPY TO FILE può esfiltrare dati, COPY FROM può caricare malware)
REVOKE ALL ON FUNCTION pg_catalog.lo_export(oid, text) FROM PUBLIC;

-- Limitare l'accesso alle viste di sistema sensibili
REVOKE SELECT ON pg_shadow FROM PUBLIC;  -- tabella degli hash delle password
-- pg_authid è già protetta
```

## Monitoraggio delle Connessioni

```python
#!/usr/bin/env python3
"""
Monitor delle connessioni database: rileva pattern anomali.
Da eseguire come servizio o cron job frequente.
"""
import psycopg2
import json
from datetime import datetime, timedelta
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

def detect_anomalies(conn):
    """
    Rileva pattern anomali nelle connessioni:
    - Nuovi IP mai visti prima
    - Picchi di connessioni
    - Connessioni a orari inusuali
    - Tentativi di accesso a oggetti non autorizzati
    """
    results = {}
    
    with conn.cursor() as cur:
        # 1. Connessioni per IP nelle ultime 10 minuti
        cur.execute("""
            SELECT
                client_addr,
                usename,
                COUNT(*) as conn_count,
                ARRAY_AGG(DISTINCT application_name) as apps
            FROM pg_stat_activity
            WHERE client_addr IS NOT NULL
              AND state != 'idle'
            GROUP BY client_addr, usename
            HAVING COUNT(*) > 10  -- più di 10 connessioni attive = anomalia
            ORDER BY conn_count DESC
        """)
        high_conn_users = cur.fetchall()
        if high_conn_users:
            results['high_connections'] = [
                {'ip': str(row[0]), 'user': row[1], 'count': row[2]}
                for row in high_conn_users
            ]
        
        # 2. Query con lock che durano da più di 5 minuti
        cur.execute("""
            SELECT
                pid,
                usename,
                client_addr,
                query_start,
                EXTRACT(EPOCH FROM (NOW() - query_start)) AS duration_seconds,
                LEFT(query, 200) AS query_snippet,
                wait_event_type,
                wait_event
            FROM pg_stat_activity
            WHERE state = 'active'
              AND query_start < NOW() - INTERVAL '5 minutes'
              AND wait_event_type = 'Lock'
            ORDER BY duration_seconds DESC
        """)
        long_locks = cur.fetchall()
        if long_locks:
            results['long_locks'] = [
                {
                    'pid': row[0],
                    'user': row[1],
                    'ip': str(row[2]),
                    'duration_s': row[4]
                }
                for row in long_locks
            ]
        
        # 3. Sessioni aperte da molto tempo (possibile connection leak)
        cur.execute("""
            SELECT
                pid,
                usename,
                client_addr,
                application_name,
                EXTRACT(EPOCH FROM (NOW() - backend_start)) / 3600 AS hours_open,
                state
            FROM pg_stat_activity
            WHERE backend_start < NOW() - INTERVAL '24 hours'
              AND application_name NOT LIKE 'patroni%'  -- escludere patroni
              AND usename != 'replicator'               -- escludere replica
            ORDER BY hours_open DESC
        """)
        old_sessions = cur.fetchall()
        if old_sessions:
            results['old_sessions'] = [
                {'pid': row[0], 'user': row[1], 'hours': row[4], 'state': row[5]}
                for row in old_sessions
            ]
    
    return results

def send_alerts(anomalies: dict):
    """Inviare alert al SIEM o al sistema di notifica."""
    if not anomalies:
        return
    
    alert = {
        'timestamp': datetime.utcnow().isoformat(),
        'source': 'db-security-monitor',
        'anomalies': anomalies
    }
    logger.warning(f"ANOMALIE RILEVATE: {json.dumps(alert)}")
    # Integrare con PagerDuty, Slack, SIEM, ecc.
```

## Protezione contro gli Attacchi di Rete Comuni

### Prevenzione del Port Scanning

```bash
# Configurare fail2ban per bloccare i port scanner
# /etc/fail2ban/jail.local
[postgresql]
enabled = true
port = 5432
filter = postgresql
logpath = /var/log/postgresql/postgresql-*.log
maxretry = 5
bantime = 3600    # 1 ora
findtime = 300    # in 5 minuti

# /etc/fail2ban/filter.d/postgresql.conf
[Definition]
failregex = ^.* FATAL:  password authentication failed for user ".*" \(from client host <HOST>\)$
            ^.* FATAL:  no pg_hba.conf entry for host "<HOST>", user .*, database .*, SSL .*$
ignoreregex =
```

### Protezione contro attacchi temporali

```sql
-- Usare funzioni a tempo costante per confronti di valori sensibili
-- Le funzioni normali di comparazione possono svelare informazioni attraverso
-- differenze nel tempo di risposta (timing attack)

-- PostgreSQL: la funzione pg_crypto.hmac è a tempo costante
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Per token/API key: usare HMAC invece di confronto diretto
CREATE TABLE api_tokens (
  id SERIAL PRIMARY KEY,
  user_id INT NOT NULL,
  token_hash BYTEA NOT NULL,  -- HMAC dell'token, non il token in chiaro
  created_at TIMESTAMPTZ DEFAULT NOW(),
  expires_at TIMESTAMPTZ
);

-- Verificare un token in modo sicuro (tempo costante)
-- In PostgreSQL non esiste una funzione di confronto time-constant nativa
-- Usare la verifica HMAC che è intrinsecamente time-constant

-- Inserire token
INSERT INTO api_tokens (user_id, token_hash)
VALUES (
  42,
  hmac('token_segreto_dell_utente', current_setting('app.hmac_key'), 'sha256')
);

-- Verificare: confrontare HMAC, non il token diretto
SELECT user_id
FROM api_tokens
WHERE token_hash = hmac($1, current_setting('app.hmac_key'), 'sha256')
  AND expires_at > NOW();
-- $1 = token fornito dall'utente
```

## Checklist Sicurezza di Rete

- [ ] Database non raggiungibile dall'internet pubblico
- [ ] Accesso al database solo attraverso proxy/application tier
- [ ] Firewall configurato con regole di default-deny
- [ ] Security groups in cloud configurati con minimo privilegio
- [ ] TLS obbligatorio per tutte le connessioni di rete (hostnossl reject in pg_hba.conf)
- [ ] Connection limits configurati per utente e database
- [ ] fail2ban o equivalente per bloccare brute force
- [ ] Query parametrizzate ovunque nell'applicazione (no SQL injection)
- [ ] Monitoring delle connessioni con alert su anomalie
- [ ] Funzioni di sistema pericolose revocate dagli utenti applicativi

