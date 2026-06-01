# Penetration Testing dei Database

Il penetration testing dei database è il processo di verifica attiva della sicurezza: invece di verificare che i controlli siano configurati, si verifica che funzionino. Un pen test ben eseguito trova le vulnerabilità prima degli attaccanti.

## Ambito e Metodologia

Il pen test di un database copre:
1. **Ricognizione**: scoperta del servizio, versione, configurazione
2. **Autenticazione**: brute force, credential stuffing, bypass
3. **Autorizzazione**: privilege escalation, accesso a dati non autorizzati
4. **Injection**: SQL injection, stored procedure injection
5. **Configurazione**: hardening, impostazioni default pericolose
6. **Post-exploitation**: cosa può fare un attaccante con l'accesso ottenuto

### Strumenti Standard

```bash
# Ricognizione del servizio
nmap -sV -p 5432,3306,1433,1521 target.example.com
# -sV: versione del servizio

# PostgreSQL: banner grab
psql -h target.example.com -U nonexistent -c "\q" 2>&1
# L'errore rivela la versione di PostgreSQL

# Enumerazione utenti PostgreSQL via timing attack (pre-autenticazione)
# pg_ident permette di testare se uno username esiste prima di autenticarsi
# Questo è mitigato in PostgreSQL moderno con scram-sha-256

# SQLMap: automatic SQL injection detection (con autorizzazione esplicita)
sqlmap -u "http://app.example.com/api/products?category=electronics" \
  --dbms=postgresql \
  --level=3 \
  --risk=2 \
  --technique=BEUST  # Boolean, Error, Union, Stacked, Time-based
```

## Scenari di Test Comuni

### Test 1: Bypass dell'Autenticazione

```python
#!/usr/bin/env python3
"""
Test di autenticazione: verifica che i meccanismi di sicurezza siano efficaci.
SOLO per test autorizzati in ambienti di test/staging.
"""
import psycopg2
import socket
import time

def test_auth_bypass_attempts(host: str, port: int, database: str):
    """
    Testa i meccanismi di protezione brute force.
    Atteso: fail dopo N tentativi e/o lockout.
    """
    results = []
    
    # Test 1: Credenziali comuni
    common_passwords = [
        'password', 'postgres', 'admin', '123456', 'test',
        database, host  # spesso usati come password del database
    ]
    
    for password in common_passwords:
        try:
            conn = psycopg2.connect(
                host=host, port=port, database=database,
                user='postgres', password=password,
                connect_timeout=3
            )
            results.append({'status': 'VULN', 'password': password, 'issue': 'weak_password'})
            conn.close()
        except psycopg2.OperationalError:
            pass
    
    # Test 2: Connessione senza SSL (se possibile)
    try:
        conn = psycopg2.connect(
            host=host, port=port, database=database,
            user='app_user', password='test',
            sslmode='disable'
        )
        results.append({'status': 'VULN', 'issue': 'ssl_not_required'})
        conn.close()
    except psycopg2.OperationalError:
        results.append({'status': 'OK', 'check': 'ssl_required'})
    
    # Test 3: Verifica rate limiting (10 tentativi rapidi)
    start_time = time.time()
    blocked = False
    for i in range(10):
        try:
            psycopg2.connect(
                host=host, port=port, database=database,
                user='app_user', password=f'wrong{i}',
                connect_timeout=1
            )
        except psycopg2.OperationalError as e:
            if 'connection refused' in str(e).lower() or 'too many' in str(e).lower():
                blocked = True
                break
    
    if not blocked:
        results.append({'status': 'WARN', 'issue': 'no_rate_limiting', 'attempts': 10})
    
    return results

def test_ssl_configuration(host: str, port: int):
    """Verifica la configurazione TLS del server database."""
    import ssl
    
    context = ssl.create_default_context()
    
    # Testare versioni TLS deprecate
    for version in ['TLSv1', 'TLSv1.1']:
        try:
            context.minimum_version = getattr(ssl.TLSVersion, version.replace('.', '_'))
            conn = context.wrap_socket(
                socket.socket(socket.AF_INET, socket.SOCK_STREAM),
                server_hostname=host
            )
            conn.connect((host, port))
            print(f"VULNERABILE: {version} accettato")
        except ssl.SSLError:
            print(f"OK: {version} rifiutato")
```

### Test 2: Privilege Escalation

```sql
-- Test di privilege escalation: verificare che un utente con permessi limitati
-- non possa accedere a dati riservati

-- Come utente 'app_service' (ha solo SELECT, INSERT, UPDATE su tabelle applicative):

-- Tentativo 1: accedere a pg_shadow (hash delle password)
SELECT * FROM pg_shadow;
-- Atteso: permission denied for table pg_shadow

-- Tentativo 2: usare funzioni di sistema per leggere file
SELECT pg_read_file('/etc/passwd');
-- Atteso: permission denied

-- Tentativo 3: accedere ad altri schema
SELECT * FROM pg_catalog.pg_user;
-- Atteso: può vedere i nomi degli utenti (pg_user è pubblica)
-- ma non le password (pg_shadow è protetta)

-- Tentativo 4: COPY TO per esfiltrare dati
COPY users TO '/tmp/users_dump.csv';
-- Atteso: must be superuser or have INSERT privilege on pg_largeobject

-- Tentativo 5: tentare di diventare superuser
ALTER USER app_service SUPERUSER;
-- Atteso: must be superuser to alter superuser roles

-- Tentativo 6: accedere alla funzione execute (execute arbitrary SQL)
CREATE OR REPLACE FUNCTION evil() RETURNS VOID AS $$ 
  -- TENTATIVO di eseguire codice arbitrario
$$ LANGUAGE sql;
-- Questo dovrebbe funzionare se l'utente ha CREATE FUNCTION
-- Rivedere: gli utenti applicativi non dovrebbero avere CREATE FUNCTION
```

### Test 3: SQL Injection Test Suite

```python
"""
Suite di test SQL injection per API che interagiscono con un database.
Da usare in ambiente di staging con dati fittizi.
"""
import requests
from typing import List, Tuple

class SqlInjectionTester:
    """
    Testa endpoint API per vulnerabilità di SQL injection.
    SOLO per test autorizzati.
    """
    
    # Payload per diversi tipi di injection
    BOOLEAN_PAYLOADS = [
        ("' OR '1'='1", "login bypass"),
        ("' OR 1=1 --", "login bypass with comment"),
        ("1 OR 1=1", "numeric injection"),
        ("' OR 'a'='a", "string comparison bypass"),
    ]
    
    ERROR_BASED_PAYLOADS = [
        ("'", "single quote - syntax error expected"),
        ("''", "double quote - should be safe"),
        ("1/0", "division by zero"),
        ("1 AND 1=convert(int,'a')", "type conversion error (MSSQL)"),
        ("' AND EXTRACTVALUE(1,CONCAT(0x7e,version())) --", "MySQL error-based"),
    ]
    
    TIME_BASED_PAYLOADS = [
        ("'; SELECT pg_sleep(5) --", 5, "PostgreSQL time-based"),
        ("1; WAITFOR DELAY '0:0:5' --", 5, "MSSQL time-based"),
        ("1 AND SLEEP(5)", 5, "MySQL time-based"),
    ]
    
    def test_endpoint(self, base_url: str, endpoint: str, param: str) -> List[dict]:
        """Test un singolo endpoint/parametro per SQL injection."""
        findings = []
        
        # Test boolean-based
        for payload, description in self.BOOLEAN_PAYLOADS:
            response = requests.get(
                f"{base_url}{endpoint}",
                params={param: payload},
                timeout=10
            )
            
            # Segnali di vulnerabilità:
            # - Risposta 200 con dati che non dovrebbero essere presenti
            # - Risposta diversa da quella con input normale
            if response.status_code == 200 and len(response.json()) > 0:
                findings.append({
                    'type': 'potential_boolean_sqli',
                    'payload': payload,
                    'description': description,
                    'response_length': len(response.text)
                })
        
        # Test time-based
        for payload, expected_delay, description in self.TIME_BASED_PAYLOADS:
            import time
            start = time.time()
            try:
                response = requests.get(
                    f"{base_url}{endpoint}",
                    params={param: payload},
                    timeout=expected_delay + 3
                )
                elapsed = time.time() - start
                
                if elapsed >= expected_delay * 0.9:  # 90% del delay atteso
                    findings.append({
                        'type': 'confirmed_time_based_sqli',
                        'payload': payload,
                        'description': description,
                        'elapsed_seconds': round(elapsed, 2),
                        'severity': 'CRITICAL'
                    })
            except requests.Timeout:
                findings.append({
                    'type': 'possible_time_based_sqli_timeout',
                    'payload': payload,
                    'severity': 'HIGH'
                })
        
        return findings
```

## Test con pgBadger e Analisi dei Log

```bash
# pgBadger: analisi dei log PostgreSQL per identificare query anomale
# Può rivelare: query con accesso a dati inusuali, picchi di errori, SQL injection attempts

# Installazione
apt-get install pgbadger

# Analizzare i log dell'ultimo giorno
pgbadger \
  /var/log/postgresql/postgresql-2025-01-15.log \
  -o /var/www/html/pgbadger-report.html \
  --format stderr \
  --quiet

# Grep per tentativi di injection nei log
grep -E "(FATAL|ERROR).*(syntax error|operator does not exist|invalid input syntax)" \
  /var/log/postgresql/postgresql-$(date +%Y-%m-%d).log | \
  awk '{print $NF}' | sort | uniq -c | sort -rn | head -20

# Cercare pattern tipici di injection
grep -iE "(union\s+select|or\s+1=1|sleep\(|pg_sleep|;\s*drop|information_schema)" \
  /var/log/postgresql/postgresql-$(date +%Y-%m-%d).log
```

## Report del Penetration Test

```markdown
# Database Penetration Test Report

## Scope
- Host: db.example.com
- Database: PostgreSQL 15.3
- Date: 2025-01-15
- Duration: 8 ore
- Authorization: scritto e firmato da [CTO Name]

## Findings

### CRITICAL: Weak password for 'reporting_user'
- **CVSS Score**: 9.8 (AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H)
- **CWE**: CWE-521 (Weak Password Requirements)
- **Evidence**: Credenziali 'reporting_user:reporting' funzionanti
- **Impact**: Accesso completo alle tabelle di business analytics
- **Remediation**: Cambiare password, implementare politica password forti, fail2ban

### HIGH: SSL non richiesto per connessioni interne
- **CVSS Score**: 7.4 (AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:H/A:N)
- **CWE**: CWE-319 (Cleartext Transmission of Sensitive Information)
- **Evidence**: Connessione senza SSL accettata da 10.0.0.0/8
- **Impact**: Possibile intercettazione credenziali in rete interna
- **Remediation**: hostnossl all all 0.0.0.0/0 reject in pg_hba.conf

### MEDIUM: Versione PostgreSQL esposta nel banner
- **CVSS Score**: 5.3
- **Evidence**: Banner "PostgreSQL 15.3" visibile prima dell'autenticazione
- **Impact**: Facilita targeting di CVE specifiche
- **Remediation**: Limitare l'accesso alla porta 5432 via firewall

### LOW: Utenti senza scadenza password
- **CWE**: CWE-272 (Least Privilege Violation)
- **Evidence**: 8 utenti senza VALID UNTIL impostato
- **Remediation**: ALTER USER x VALID UNTIL 'YYYY-MM-DD' per tutti gli utenti

## Checklist Pre-Rilascio Fix

- [ ] Password deboli cambiate (CRITICAL)
- [ ] SSL obbligatorio attivato (HIGH)
- [ ] Patch di sicurezza future programmate
- [ ] Review completata dal security team
- [ ] Retest pianificato per 2025-02-15
```

## Strumenti di Test Consigliati

| Tool | Tipo | Note |
|------|------|-------|
| SQLMap | SQL Injection | Automatico, molto completo |
| Metasploit (postgres modules) | Post-exploitation | Richiede accesso iniziale |
| nmap scripts (pgsql-*) | Ricognizione | Safe, informativo |
| pgBadger | Log Analysis | Analisi a posteriori |
| pgAudit | Audit trail | Per verificare che il logging funzioni |
| Burp Suite | Web → DB | Per injection via API |

Il penetration testing dei database deve essere ripetuto almeno annualmente, o dopo ogni cambiamento architetturale significativo. I risultati devono essere documentati, tracciati con CVSS scores, e le remediation devono essere verificate con un retest prima di chiudere il finding.

