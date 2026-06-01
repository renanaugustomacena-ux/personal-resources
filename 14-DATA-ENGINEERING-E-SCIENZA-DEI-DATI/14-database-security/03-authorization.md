# Autorizzazione nei Database

L'autorizzazione risponde alla domanda "cosa puoi fare?" dopo che l'autenticazione ha risposto a "chi sei?". Un sistema di autorizzazione ben progettato segue il principio del minimo privilegio: ogni entità (utente, servizio, ruolo) ha esattamente i permessi necessari per la sua funzione e niente di più.

## Modello RBAC in PostgreSQL

PostgreSQL implementa un modello RBAC (Role-Based Access Control) dove i permessi vengono assegnati a ruoli e i ruoli vengono assegnati agli utenti. I ruoli possono essere gerarchici: un ruolo può includere altri ruoli.

### Gerarchia dei Privilegi

```
Superuser (postgres)
    └── DBA role
         ├── DDL role (CREATE/ALTER/DROP)
         │    └── Migration role
         ├── Read-Write role
         │    ├── App service accounts
         │    └── Privileged users
         └── Read-Only role
              ├── Analyst role
              └── Monitoring role
```

```sql
-- Costruire la gerarchia

-- Ruolo DBA: può gestire utenti e oggetti del database
CREATE ROLE dba_role NOLOGIN;
GRANT CONNECT ON DATABASE myapp TO dba_role;
GRANT ALL PRIVILEGES ON DATABASE myapp TO dba_role;

-- Ruolo DDL: solo operazioni di schema
CREATE ROLE ddl_role NOLOGIN;
GRANT CONNECT ON DATABASE myapp TO ddl_role;
GRANT CREATE ON SCHEMA public TO ddl_role;
GRANT USAGE ON SCHEMA public TO ddl_role;

-- Ruolo read-write per l'applicazione
CREATE ROLE rw_role NOLOGIN;
GRANT CONNECT ON DATABASE myapp TO rw_role;
GRANT USAGE ON SCHEMA public TO rw_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO rw_role;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO rw_role;

-- Assicurare che i nuovi oggetti ereditino i permessi del ruolo
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO rw_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT USAGE, SELECT ON SEQUENCES TO rw_role;

-- Ruolo read-only per analytics e monitoring
CREATE ROLE ro_role NOLOGIN;
GRANT CONNECT ON DATABASE myapp TO ro_role;
GRANT USAGE ON SCHEMA public TO ro_role;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO ro_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO ro_role;

-- Ruolo monitoring: accesso solo alle viste di sistema
CREATE ROLE monitoring_role NOLOGIN;
GRANT CONNECT ON DATABASE myapp TO monitoring_role;
GRANT pg_monitor TO monitoring_role;  -- ruolo built-in per monitoring (PG 10+)

-- Utenti concreti
CREATE USER app_service LOGIN ENCRYPTED PASSWORD 'strong_password' CONNECTION LIMIT 50;
GRANT rw_role TO app_service;

CREATE USER analyst LOGIN ENCRYPTED PASSWORD 'strong_password';
GRANT ro_role TO analyst;

CREATE USER prometheus LOGIN ENCRYPTED PASSWORD 'strong_password';
GRANT monitoring_role TO prometheus;

CREATE USER migration_bot LOGIN ENCRYPTED PASSWORD 'strong_password';
GRANT rw_role TO migration_bot;
GRANT ddl_role TO migration_bot;
```

### Privilegi per Schema Multipli

```sql
-- Applicazione con schema separati per moduli diversi
-- Schema: orders, inventory, analytics (separati per sicurezza)

CREATE SCHEMA orders;
CREATE SCHEMA inventory;
CREATE SCHEMA analytics;

-- Ruolo orders_service: solo schema orders
CREATE ROLE orders_service_role NOLOGIN;
GRANT CONNECT ON DATABASE myapp TO orders_service_role;
GRANT USAGE ON SCHEMA orders TO orders_service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA orders TO orders_service_role;
-- Nessun accesso a inventory o analytics

-- Ruolo inventory_service: solo schema inventory
CREATE ROLE inventory_service_role NOLOGIN;
GRANT CONNECT ON DATABASE myapp TO inventory_service_role;
GRANT USAGE ON SCHEMA inventory TO inventory_service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA inventory TO inventory_service_role;

-- Ruolo analytics: accesso in sola lettura a tutto
CREATE ROLE analytics_role NOLOGIN;
GRANT CONNECT ON DATABASE myapp TO analytics_role;
GRANT USAGE ON SCHEMA orders, inventory, analytics TO analytics_role;
GRANT SELECT ON ALL TABLES IN SCHEMA orders TO analytics_role;
GRANT SELECT ON ALL TABLES IN SCHEMA inventory TO analytics_role;
GRANT SELECT ON ALL TABLES IN SCHEMA analytics TO analytics_role;

-- Service account per il microservizio ordini
CREATE USER orders_svc LOGIN ENCRYPTED PASSWORD 'strong_pass';
GRANT orders_service_role TO orders_svc;
```

### Autorizzazione a Livello di Colonna

PostgreSQL supporta il controllo degli accessi a livello di colonna singola.

```sql
-- Tabella con colonne sensibili
CREATE TABLE employees (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  department TEXT NOT NULL,
  salary NUMERIC(10,2),           -- SENSIBILE: solo HR vede stipendi
  ssn TEXT,                       -- MOLTO SENSIBILE: solo payroll
  emergency_contact TEXT,
  job_title TEXT NOT NULL
);

-- Ruolo HR: vede tutto tranne SSN
CREATE ROLE hr_role NOLOGIN;
GRANT SELECT (id, name, department, salary, emergency_contact, job_title)
  ON employees TO hr_role;

-- Ruolo Manager: vede nome, dipartimento, titolo (no stipendio, no SSN)
CREATE ROLE manager_role NOLOGIN;
GRANT SELECT (id, name, department, job_title)
  ON employees TO manager_role;

-- Ruolo Payroll: vede tutto incluso SSN
CREATE ROLE payroll_role NOLOGIN;
GRANT SELECT ON employees TO payroll_role;

-- Nota: la GRANT di colonna può essere a SELECT, INSERT, UPDATE, REFERENCES
-- Non si applica a DELETE (opera sulla riga intera)

-- Tentativo di un manager di vedere gli stipendi → errore
SET ROLE manager_role;
SELECT salary FROM employees WHERE id = 1;
-- ERROR: permission denied for table employees
-- Oppure: permission denied for column salary

-- Il manager può accedere alle colonne permesse
SELECT name, department, job_title FROM employees WHERE id = 1;
-- Funziona
```

## Row Level Security (RLS) Avanzato

RLS permette di filtrare automaticamente le righe in base a policy definite dall'amministratore.

```sql
-- Schema multi-tenant: ogni organizzazione vede solo i propri dati
CREATE TABLE projects (
  id SERIAL PRIMARY KEY,
  organization_id INT NOT NULL,
  name TEXT NOT NULL,
  budget NUMERIC(12,2),
  status TEXT
);

-- Abilitare RLS
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;

-- Policy per utenti normali: vedono solo i progetti della loro organizzazione
CREATE POLICY tenant_isolation ON projects
  AS PERMISSIVE
  FOR ALL
  TO PUBLIC
  USING (
    organization_id = (
      SELECT organization_id
      FROM user_organizations
      WHERE user_id = current_setting('app.user_id', true)::int
    )
  );

-- Policy per admin: vedono tutto
CREATE ROLE admin_role NOLOGIN;
CREATE POLICY admin_full_access ON projects
  AS PERMISSIVE
  FOR ALL
  TO admin_role
  USING (true)
  WITH CHECK (true);

-- Policy per sola lettura
CREATE POLICY readonly_access ON projects
  AS PERMISSIVE
  FOR SELECT
  TO reporting_role
  USING (status = 'active');  -- i report vedono solo progetti attivi

-- Vedere le policy esistenti
SELECT
  tablename,
  policyname,
  permissive,
  roles,
  cmd,
  qual,
  with_check
FROM pg_policies
WHERE tablename = 'projects';
```

```python
# Applicazione: impostare il contesto utente prima di ogni query
import psycopg2
from contextlib import contextmanager

@contextmanager
def get_db_connection(user_id: int):
    """
    Context manager che imposta il contesto utente per RLS.
    """
    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn.cursor() as cur:
            # Impostare la variabile di sessione per RLS
            cur.execute("SET LOCAL app.user_id = %s", (user_id,))
        conn.commit()
        yield conn
    finally:
        conn.close()

# Uso
with get_db_connection(user_id=42) as conn:
    with conn.cursor() as cur:
        # Questa query restituisce automaticamente solo i progetti dell'utente 42
        cur.execute("SELECT id, name FROM projects WHERE status = 'active'")
        projects = cur.fetchall()
```

## Autorizzazione MySQL

```sql
-- MySQL: modello di autorizzazione basato su privilege tables

-- Privilegi globali (tutti i database)
GRANT PROCESS, REPLICATION CLIENT ON *.* TO 'monitor'@'%';

-- Privilegi per database specifico
GRANT SELECT, INSERT, UPDATE, DELETE ON myapp.* TO 'app_service'@'%';

-- Privilegi per tabella specifica
GRANT SELECT ON myapp.products TO 'readonly_service'@'%';
GRANT SELECT, INSERT ON myapp.orders TO 'orders_service'@'%';

-- Privilegi per colonna specifica
GRANT SELECT (id, name, email) ON myapp.users TO 'limited_access'@'%';

-- Ruoli MySQL (disponibili da MySQL 8.0)
CREATE ROLE 'app_readonly', 'app_readwrite', 'app_admin';

GRANT SELECT ON myapp.* TO 'app_readonly';
GRANT SELECT, INSERT, UPDATE, DELETE ON myapp.* TO 'app_readwrite';
GRANT ALL PRIVILEGES ON myapp.* TO 'app_admin';

-- Assegnare ruoli a utenti
GRANT 'app_readwrite' TO 'web_service'@'%';
GRANT 'app_readonly' TO 'analyst'@'%';

-- Il ruolo non è attivo automaticamente in MySQL
-- L'utente deve attivarlo
-- SET DEFAULT ROLE 'app_readwrite' TO 'web_service'@'%';
-- O a livello di sessione:
-- SET ROLE 'app_readwrite';

-- Vedere i privilegi di un utente
SHOW GRANTS FOR 'web_service'@'%';

-- Revocare un privilegio
REVOKE DELETE ON myapp.* FROM 'web_service'@'%';
```

## Principio del Minimo Privilegio: Applicazione Pratica

### Inventario dei Permessi

Prima di implementare l'autorizzazione, creare un inventario di chi ha bisogno di cosa:

```sql
-- Script per auditare i permessi correnti in PostgreSQL
SELECT
  grantee,
  table_schema,
  table_name,
  STRING_AGG(privilege_type, ', ' ORDER BY privilege_type) AS privileges
FROM information_schema.role_table_grants
WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
GROUP BY grantee, table_schema, table_name
ORDER BY grantee, table_schema, table_name;

-- Trovare utenti con troppi privilegi (superuser o con CREATEROLE)
SELECT
  rolname,
  rolsuper,
  rolinherit,
  rolcreaterole,
  rolcreatedb,
  rolcanlogin,
  rolreplication,
  rolconnlimit
FROM pg_roles
WHERE rolsuper OR rolcreaterole
ORDER BY rolname;

-- Trovare utenti inattivi da più di 90 giorni
SELECT
  usename,
  usesuper,
  usecreatedb,
  valuntil,
  -- Attenzione: query_start_time non è disponibile su pg_user; usare pg_stat_activity
  (SELECT MAX(query_start)
   FROM pg_stat_activity
   WHERE pg_stat_activity.usename = pg_user.usename) AS last_active
FROM pg_user
ORDER BY last_active NULLS FIRST;
```

### Revoca Sicura

```sql
-- Revoca completa per un utente da disabilitare
-- Non cancellare l'utente (potrebbe avere oggetti): disabilitarlo

-- 1. Terminare tutte le sessioni attive
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE usename = 'ex_employee'
  AND pid <> pg_backend_pid();

-- 2. Revocare tutti i privilegi
REVOKE ALL PRIVILEGES ON DATABASE myapp FROM ex_employee;
REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM ex_employee;
REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public FROM ex_employee;
REVOKE ALL PRIVILEGES ON SCHEMA public FROM ex_employee;

-- 3. Revocare i ruoli
REVOKE rw_role FROM ex_employee;
REVOKE ro_role FROM ex_employee;

-- 4. Bloccare il login (senza cancellare: mantiene la storia di audit)
ALTER USER ex_employee NOLOGIN;

-- 5. Documentare la disabilitazione
COMMENT ON ROLE ex_employee IS 'Disabilitato il 2025-01-15 - Mario Rossi lasciato azienda';
```

## Separation of Duties

Per i sistemi critici, applicare la separazione dei compiti impedisce che un singolo utente compromesso possa causare danni massivi:

```sql
-- Nessun singolo utente può sia scrivere dati che cancellare audit log

-- Utente applicazione: può scrivere dati ma non toccare l'audit schema
CREATE USER app_service LOGIN ENCRYPTED PASSWORD 'password';
GRANT rw_role TO app_service;
-- app_service non ha accesso ad audit schema

-- Utente audit: può solo scrivere nell'audit schema (via security definer function)
CREATE USER audit_writer LOGIN ENCRYPTED PASSWORD 'password';
GRANT EXECUTE ON FUNCTION write_audit_log(text, text, jsonb) TO audit_writer;
-- Non può leggere o cancellare audit_log direttamente

-- Utente compliance: può leggere l'audit log ma non i dati di produzione
CREATE USER compliance_reader LOGIN ENCRYPTED PASSWORD 'password';
GRANT USAGE ON SCHEMA audit TO compliance_reader;
GRANT SELECT ON audit.audit_log TO compliance_reader;
-- Non ha accesso agli schema di produzione
```

