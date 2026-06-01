# Best Practice di Sicurezza per i Database

Le best practice di sicurezza per i database sono un insieme consolidato di principi, pattern, e checklist derivati da anni di incident response, pen test, e compliance audit. Non sono teoriche: ogni best practice esiste perché qualcuno ha ignorato quel principio e ha pagato le conseguenze.

## Principi Fondamentali

### Minimo Privilegio

Ogni entità (utente, servizio, processo) deve avere il minimo accesso necessario per svolgere la propria funzione. Questo limita il danno in caso di compromissione.

```sql
-- Audit periodico per trovare violazioni del principio di minimo privilegio

-- Trovare utenti con superuser non necessario
SELECT rolname FROM pg_roles
WHERE rolsuper = true
  AND rolname NOT IN ('postgres')  -- solo il superuser nativo dovrebbe averlo
ORDER BY rolname;

-- Trovare utenti con accesso a più database del necessario
SELECT
  grantee,
  catalog_name,
  privilege_type
FROM information_schema.role_catalog_grants
WHERE grantee NOT IN ('postgres', 'pg_monitor', 'pg_read_all_settings')
ORDER BY grantee;

-- Trovare tabelle senza owner esplicito (ownership implicito = superficie d'attacco)
SELECT tablename, tableowner
FROM pg_tables
WHERE tableowner = 'postgres'  -- il superuser non dovrebbe essere owner di tabelle applicative
  AND schemaname = 'public';

-- Revocare privilegi non necessari
-- Esempio: un servizio di reporting non dovrebbe avere INSERT/UPDATE/DELETE
REVOKE INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public FROM reporting_service;
```

### Defense in Depth (Difesa in Profondità)

Ogni layer di sicurezza è indipendente. Se un layer viene compromesso, gli altri limitano il danno.

```
Layer 1: Rete
  → Firewall, VPC, Security Groups
  → Database non raggiungibile da internet

Layer 2: Autenticazione  
  → scram-sha-256 o mTLS
  → Password forti, rotazione periodica
  → No trust su connessioni di rete

Layer 3: Autorizzazione
  → RBAC granulare
  → RLS per isolamento multi-tenant
  → Column-level security per dati sensibili

Layer 4: Crittografia
  → TLS per dati in transito
  → pgcrypto/Vault per colonne sensibili
  → LUKS per dati a riposo

Layer 5: Auditing
  → pgAudit per operazioni critiche
  → Trigger audit per tabelle sensibili
  → Log immutabili su SIEM

Layer 6: Monitoring
  → Alert su anomalie di accesso
  → Alert su lag replica e backup
  → Penetration testing periodico
```

### Fail Secure

Il sistema deve fallire in modo sicuro: quando un controllo di sicurezza non può essere valutato, deve negare l'accesso per default.

```sql
-- Policy RLS che nega l'accesso se il contesto non è impostato (fail secure)
CREATE POLICY tenant_strict ON orders
  USING (
    -- Se app.tenant_id non è impostato, la query restituisce 0 righe
    -- invece di tutte le righe (che sarebbe fail open)
    organization_id = COALESCE(
      NULLIF(current_setting('app.tenant_id', true), ''),
      '-1'  -- valore impossibile: nessuna riga corrisponde
    )::int
  );

-- NON FARE:
-- USING (organization_id = current_setting('app.tenant_id')::int)
-- Se app.tenant_id non è impostato, questa genera un errore
-- che l'applicazione potrebbe gestire tornando a una query senza filtri
```

## Gestione delle Credenziali

### Mai Hardcodare le Credenziali

```python
# SBAGLIATO: credenziali nel codice
DB_PASSWORD = "super_secret_password"
DATABASE_URL = f"postgresql://app_user:{DB_PASSWORD}@db.example.com/myapp"

# SBAGLIATO: credenziali in variabili d'ambiente leggibili nei log
# os.environ['DB_PASSWORD'] appare nel traceback completo

# CORRETTO: HashiCorp Vault con credenziali dinamiche
import hvac
import os

def get_db_credentials() -> dict:
    """Recupera credenziali dinamiche con TTL breve."""
    client = hvac.Client(
        url=os.environ['VAULT_ADDR'],
        token=os.environ['VAULT_TOKEN']
    )
    
    secret = client.secrets.database.generate_credentials(
        name='myapp-readwrite'  # ruolo configurato in Vault
    )
    
    return {
        'username': secret['data']['username'],
        'password': secret['data']['password'],
        'lease_id': secret['lease_id'],
        'lease_duration': secret['lease_duration']
    }

# CORRETTO: .pgpass file per connessioni locali (mai commitarlo)
# ~/.pgpass (chmod 600):
# hostname:port:database:username:password
# db.example.com:5432:myapp:app_user:secure_password
```

### Rotazione delle Credenziali

```bash
#!/bin/bash
# rotate-db-password.sh: rotazione sicura della password
# Da eseguire come cron job mensile

DB_HOST="db.example.com"
DB_PORT=5432
DB_NAME="myapp"
DB_USER="app_service"
VAULT_ADDR="https://vault.example.com"

# 1. Generare nuova password
NEW_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)

# 2. Aggiornare in PostgreSQL (usando la password corrente da Vault)
CURRENT_PASSWORD=$(vault kv get -field=password secret/database/app_service)

PGPASSWORD="$CURRENT_PASSWORD" psql \
  -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -U "$DB_USER" \
  -c "ALTER USER ${DB_USER} ENCRYPTED PASSWORD '${NEW_PASSWORD}'"

if [ $? -ne 0 ]; then
    echo "ERRORE: modifica password fallita"
    exit 1
fi

# 3. Verificare che la nuova password funzioni
PGPASSWORD="$NEW_PASSWORD" psql \
  -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -U "$DB_USER" \
  -c "SELECT 1" > /dev/null

if [ $? -ne 0 ]; then
    echo "ERRORE: verifica nuova password fallita. Ripristino..."
    PGPASSWORD="$CURRENT_PASSWORD" psql \
      -h "$DB_HOST" -c "ALTER USER ${DB_USER} ENCRYPTED PASSWORD '${CURRENT_PASSWORD}'"
    exit 1
fi

# 4. Aggiornare in Vault
vault kv put secret/database/app_service \
  password="$NEW_PASSWORD" \
  rotated_at="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"

echo "Password rotata con successo per ${DB_USER}"
```

## Hardening del Database

### Configurazione Sicura PostgreSQL

```ini
# postgresql.conf: hardening di sicurezza

# Connessioni
listen_addresses = 'localhost,10.0.30.10'  # NON '0.0.0.0' se non necessario
max_connections = 200
superuser_reserved_connections = 5  # sempre slots per il DBA in emergenza

# Autenticazione
password_encryption = scram-sha-256   # NON md5

# Logging sicurezza
log_connections = on                  # loggare ogni connessione
log_disconnections = on
log_failed_authentications = on
log_hostname = off                    # NON fare reverse DNS (rallenta e può ingannare)

# Non rivelare informazioni di errore agli utenti non privilegiati
# (le query non dovrebbero esporre dettagli interni)
# Ma PostgreSQL per default non nasconde i messaggi di errore:
# configurare l'applicazione per non mostrare pg errors raw agli utenti finali

# Lock timeout: evita che una query blocchi il sistema per sempre
lock_timeout = '30s'
statement_timeout = '300s'             # 5 minuti max per query
idle_in_transaction_session_timeout = '60s'

# Logging query (per audit e debugging, NON in produzione ad alta frequenza)
log_min_duration_statement = 1000     # loggare query > 1 secondo
log_statement = 'ddl'                 # loggare tutte le DDL
```

### Disabilitare Funzioni Non Necessarie

```sql
-- Revocare funzioni pericolose dagli utenti applicativi

-- Lettura di file dal filesystem del server
REVOKE EXECUTE ON FUNCTION pg_read_file(text) FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION pg_read_file(text, bigint, bigint) FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION pg_read_binary_file(text) FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION pg_ls_dir(text) FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION pg_stat_file(text) FROM PUBLIC;

-- Large Object export (può esfiltrare dati)
REVOKE EXECUTE ON FUNCTION lo_export(oid, text) FROM PUBLIC;

-- Eseguire comandi OS (disponibile solo con superuser, ma revocare esplicitamente)
-- pg_execute_server_program è disponibile solo con superuser: non revocare PUBLIC
-- ma verificare che nessun utente non-superuser lo abbia

-- Verificare le funzioni con accesso PUBLIC
SELECT
  p.proname AS function_name,
  n.nspname AS schema_name
FROM pg_proc p
JOIN pg_namespace n ON n.oid = p.pronamespace
WHERE has_function_privilege('PUBLIC', p.oid, 'EXECUTE')
  AND p.proname IN ('pg_read_file', 'pg_read_binary_file', 'pg_ls_dir', 'lo_export')
ORDER BY schema_name, function_name;
```

## Monitoraggio della Sicurezza

```python
#!/usr/bin/env python3
"""
Security monitor: rileva eventi di sicurezza nel database.
Da eseguire ogni 5 minuti come cron job.
"""
import psycopg2
import json
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta

SECURITY_CHECKS = {
    'new_superusers': """
        SELECT rolname
        FROM pg_roles
        WHERE rolsuper = true
          AND rolname != 'postgres'
    """,
    
    'users_no_expiry': """
        SELECT rolname
        FROM pg_roles
        WHERE rolcanlogin = true
          AND rolvaliduntil IS NULL
          AND rolname NOT IN ('postgres', 'replicator', 'prometheus')
    """,
    
    'too_many_connections': """
        SELECT usename, COUNT(*) as count
        FROM pg_stat_activity
        WHERE state != 'idle'
        GROUP BY usename
        HAVING COUNT(*) > 20
    """,
    
    'long_running_queries': """
        SELECT pid, usename, client_addr,
               EXTRACT(EPOCH FROM (NOW() - query_start)) AS duration_s,
               LEFT(query, 100) AS query_snippet
        FROM pg_stat_activity
        WHERE state = 'active'
          AND query_start < NOW() - INTERVAL '10 minutes'
          AND query NOT LIKE 'autovacuum%'
    """,
    
    'failed_logins_from_log': """
        -- Richiederebbe accesso al file di log; alternativa: usare fail2ban
        -- o pg_audit con analisi esterna
        SELECT 1 WHERE false  -- placeholder
    """,
    
    'slot_retention_alert': """
        SELECT slot_name,
               pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) AS retained
        FROM pg_replication_slots
        WHERE NOT active
           OR pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn) > 5*1024*1024*1024
    """
}

def run_security_checks(conn_str: str) -> dict:
    """Esegui tutti i check di sicurezza e restituisci i risultati."""
    findings = {}
    
    with psycopg2.connect(conn_str) as conn:
        with conn.cursor() as cur:
            for check_name, query in SECURITY_CHECKS.items():
                cur.execute(query)
                results = cur.fetchall()
                if results:
                    findings[check_name] = [list(row) for row in results]
    
    return findings

def send_security_alert(findings: dict, recipient: str):
    """Invia alert di sicurezza via email."""
    if not findings:
        return
    
    body = f"Security Alert - {datetime.utcnow().isoformat()}\n\n"
    for check, results in findings.items():
        body += f"=== {check} ===\n"
        for row in results:
            body += f"  {row}\n"
        body += "\n"
    
    msg = MIMEText(body)
    msg['Subject'] = f'[DB SECURITY] Alert trovati: {", ".join(findings.keys())}'
    msg['From'] = 'db-monitor@example.com'
    msg['To'] = recipient
    
    with smtplib.SMTP('smtp.example.com') as server:
        server.sendmail(msg['From'], [recipient], msg.as_string())
```

## Checklist di Sicurezza Completa

**Autenticazione:**
- [ ] scram-sha-256 o mTLS per tutte le connessioni
- [ ] Nessun utente con metodo `trust` su connessioni di rete
- [ ] Password forti (almeno 20 caratteri, generate)
- [ ] Scadenza password impostata per utenti umani
- [ ] Rotazione password ogni 90 giorni
- [ ] Account disabilitati per ex-dipendenti

**Autorizzazione:**
- [ ] Principio di minimo privilegio applicato
- [ ] Nessun utente superuser non necessario
- [ ] Ruoli separati per lettura/scrittura/DDL
- [ ] RLS abilitato per tabelle multi-tenant
- [ ] Column-level security per PII e dati finanziari

**Crittografia:**
- [ ] TLS obbligatorio (hostnossl reject)
- [ ] TLS 1.2 come minimo (preferito TLS 1.3)
- [ ] Colonne PII crittografate con pgcrypto o Vault Transit
- [ ] Chiavi gestite da Vault, non hardcodate

**Rete:**
- [ ] Database non raggiungibile da internet
- [ ] Firewall con default-deny
- [ ] Accesso solo attraverso proxy/application tier
- [ ] fail2ban per protezione brute force

**Auditing:**
- [ ] pgAudit abilitato per DDL, role, connection
- [ ] Trigger di audit su tabelle con PII
- [ ] Log immutabili (RLS + trigger anti-delete)
- [ ] Log inviati a SIEM esterno

**Operazioni:**
- [ ] Backup testato (restore verificato ogni mese)
- [ ] Patch di sicurezza applicate entro 30 giorni
- [ ] Penetration test annuale
- [ ] Incident response plan documentato
- [ ] Rotazione chiavi crittografiche annuale

