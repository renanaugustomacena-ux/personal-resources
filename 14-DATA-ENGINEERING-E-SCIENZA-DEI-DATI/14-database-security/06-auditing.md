# Auditing dei Database

L'auditing registra chi ha fatto cosa e quando nel database. È indispensabile per la compliance normativa (GDPR, PCI-DSS, HIPAA, SOC2), per le indagini forensi post-incident, e per il rilevamento di comportamenti anomali. Un audit trail efficace deve essere: completo (non perde eventi), immutabile (non può essere modificato da chi è auditato), e ricercabile (le informazioni possono essere estratte rapidamente).

## pgAudit per PostgreSQL

pgAudit è l'extension standard per l'audit in PostgreSQL. Si integra con il sistema di logging di PostgreSQL e aggiunge log strutturati per le operazioni database.

```sql
-- Installazione
-- apt-get install postgresql-15-pgaudit

-- Attivare l'estensione
-- postgresql.conf:
-- shared_preload_libraries = 'pgaudit'

CREATE EXTENSION IF NOT EXISTS pgaudit;

-- Configurazione globale
-- postgresql.conf
SET pgaudit.log = 'write, ddl, role, connection';
-- write: INSERT, UPDATE, DELETE, TRUNCATE, COPY
-- read: SELECT (molto verboso, usare con cautela)
-- ddl: CREATE, ALTER, DROP, COMMENT, GRANT, REVOKE
-- role: CREATE USER, GRANT, REVOKE, ALTER ROLE
-- function: chiamate a funzioni
-- connection: CONNECT, DISCONNECT
-- misc: CHECKPOINT, VACUUM, etc.
-- all: tutto

SET pgaudit.log_catalog = off;    -- non auditare query sulle tabelle di sistema
SET pgaudit.log_parameter = on;   -- includere i valori dei parametri nelle query
SET pgaudit.log_statement_once = off;  -- loggare ogni statement, non una volta per query
SET pgaudit.log_level = log;      -- livello di log PostgreSQL da usare

SELECT pg_reload_conf();
```

```sql
-- Audit a livello di oggetto specifico (più granulare)
-- Auditare solo la tabella payments, non tutte le tabelle

-- Abilitare audit per il ruolo che accede a payments
ALTER ROLE payment_service SET pgaudit.log = 'write';
ALTER ROLE payment_service SET pgaudit.log_relation = on;

-- Audit su ruolo specifico (tutti gli accessi di admin_user)
ALTER ROLE admin_user SET pgaudit.log = 'all';

-- Esempio di output nei log:
-- LOG:  AUDIT: OBJECT,1,1,READ,SELECT,TABLE,public.payments,
--       SELECT amount, currency FROM payments WHERE id = $1,[1234]
-- LOG:  AUDIT: SESSION,1,1,WRITE,INSERT,TABLE,public.payments,
--       INSERT INTO payments(user_id, amount) VALUES($1, $2),[42, 99.99]
```

### Tabella di Audit Personalizzata

Oltre ai log, spesso è utile avere una tabella di audit strutturata per query analitiche.

```sql
-- Schema per audit trail strutturato
CREATE SCHEMA IF NOT EXISTS audit;

CREATE TABLE audit.audit_log (
  id BIGSERIAL PRIMARY KEY,
  event_time TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  table_schema TEXT NOT NULL,
  table_name TEXT NOT NULL,
  operation TEXT NOT NULL,          -- INSERT, UPDATE, DELETE
  old_data JSONB,                   -- dati prima della modifica
  new_data JSONB,                   -- dati dopo la modifica
  changed_fields TEXT[],            -- solo i campi modificati
  performed_by TEXT DEFAULT current_user NOT NULL,
  application_user TEXT,            -- utente applicativo (da current_setting)
  client_addr INET DEFAULT inet_client_addr(),
  transaction_id BIGINT DEFAULT txid_current(),
  query_text TEXT
);

-- Indici per query di audit efficienti
CREATE INDEX idx_audit_time ON audit.audit_log(event_time DESC);
CREATE INDEX idx_audit_table ON audit.audit_log(table_schema, table_name);
CREATE INDEX idx_audit_user ON audit.audit_log(performed_by);
CREATE INDEX idx_audit_operation ON audit.audit_log(operation);

-- Partitionare per mese (audit log crescono rapidamente)
-- Usare pg_partman o partitioning nativo

-- Trigger per popolate l'audit log
CREATE OR REPLACE FUNCTION audit.log_changes()
RETURNS TRIGGER AS $$
DECLARE
  old_data JSONB;
  new_data JSONB;
  changed_fields TEXT[];
BEGIN
  IF TG_OP = 'DELETE' THEN
    old_data := row_to_json(OLD)::JSONB;
    new_data := NULL;
  ELSIF TG_OP = 'INSERT' THEN
    old_data := NULL;
    new_data := row_to_json(NEW)::JSONB;
  ELSIF TG_OP = 'UPDATE' THEN
    old_data := row_to_json(OLD)::JSONB;
    new_data := row_to_json(NEW)::JSONB;
    -- Calcolare quali campi sono cambiati
    SELECT ARRAY_AGG(key)
    INTO changed_fields
    FROM jsonb_each(old_data) old_row
    WHERE NOT (new_data ? old_row.key AND new_data->old_row.key = old_row.value);
  END IF;

  INSERT INTO audit.audit_log (
    table_schema,
    table_name,
    operation,
    old_data,
    new_data,
    changed_fields,
    application_user,
    query_text
  ) VALUES (
    TG_TABLE_SCHEMA,
    TG_TABLE_NAME,
    TG_OP,
    old_data,
    new_data,
    changed_fields,
    current_setting('app.user_id', true),
    current_query()
  );

  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Applicare il trigger alle tabelle critiche
CREATE TRIGGER audit_payments
  AFTER INSERT OR UPDATE OR DELETE ON payments
  FOR EACH ROW EXECUTE FUNCTION audit.log_changes();

CREATE TRIGGER audit_users
  AFTER INSERT OR UPDATE OR DELETE ON users
  FOR EACH ROW EXECUTE FUNCTION audit.log_changes();

CREATE TRIGGER audit_orders
  AFTER INSERT OR UPDATE OR DELETE ON orders
  FOR EACH ROW EXECUTE FUNCTION audit.log_changes();
```

### Query di Audit

```sql
-- Chi ha modificato un record specifico?
SELECT
  event_time,
  operation,
  performed_by,
  application_user,
  client_addr,
  old_data,
  new_data
FROM audit.audit_log
WHERE table_name = 'payments'
  AND new_data->>'id' = '12345'
ORDER BY event_time DESC;

-- Tutte le operazioni DELETE nelle ultime 24 ore
SELECT
  event_time,
  table_schema || '.' || table_name AS table_path,
  performed_by,
  application_user,
  old_data
FROM audit.audit_log
WHERE operation = 'DELETE'
  AND event_time > NOW() - INTERVAL '24 hours'
ORDER BY event_time DESC;

-- Attività sospetta: molte DELETE da un singolo utente in un'ora
SELECT
  DATE_TRUNC('hour', event_time) AS hour,
  performed_by,
  COUNT(*) AS delete_count
FROM audit.audit_log
WHERE operation = 'DELETE'
  AND event_time > NOW() - INTERVAL '7 days'
GROUP BY hour, performed_by
HAVING COUNT(*) > 100  -- più di 100 delete/ora = sospetto
ORDER BY delete_count DESC;

-- Storia completa di un record specifico (ricostruzione point-in-time)
SELECT
  event_time,
  operation,
  performed_by,
  changed_fields,
  old_data,
  new_data
FROM audit.audit_log
WHERE table_name = 'orders'
  AND (
    new_data->>'id' = '999'
    OR old_data->>'id' = '999'
  )
ORDER BY event_time;
```

## Audit MySQL con Percona Audit Plugin

```sql
-- Installazione
INSTALL PLUGIN audit_log SONAME 'audit_log.so';

-- Configurazione
-- my.cnf:
-- audit_log_file=/var/log/mysql/audit.log
-- audit_log_format=JSON
-- audit_log_policy=ALL
-- audit_log_rotate_on_size=100M
-- audit_log_flush=ON

-- Verificare lo stato del plugin
SELECT PLUGIN_NAME, PLUGIN_STATUS FROM information_schema.PLUGINS
WHERE PLUGIN_NAME = 'audit_log';

-- Filtrare per utente specifico (ridurre il volume di log)
-- Auditare solo gli utenti privilegiati, non i service account normali
SET GLOBAL audit_log_include_accounts = 'admin@%,dba@%';
SET GLOBAL audit_log_exclude_accounts = 'monitor@localhost,replicator@%';

-- Formato del log JSON (esempio):
-- {"audit_record":{"name":"Query","record":"2_2025-01-15T10:30:00","timestamp":"2025-01-15T10:30:00","command_class":"select","connection_id":42,"host":"app-server.example.com","user":"app_user","os_login":"","priv_user":"app_user","ip":"10.0.1.50","db":"myapp","sqltext":"SELECT * FROM payments WHERE id = 123"}}
```

## Protezione del Log di Audit

Il log di audit deve essere protetto dall'utente auditato: un attaccante che ha compromesso il database non deve poter cancellare le sue tracce.

```sql
-- In PostgreSQL: rendere la tabella di audit append-only

-- 1. Revocare DELETE e UPDATE dalla tabella audit
REVOKE DELETE, UPDATE, TRUNCATE ON audit.audit_log FROM PUBLIC;
REVOKE DELETE, UPDATE, TRUNCATE ON audit.audit_log FROM app_service;

-- 2. Policy RLS che nega anche DELETE dal proprietario della tabella
ALTER TABLE audit.audit_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit.audit_log FORCE ROW LEVEL SECURITY;

-- Solo un ruolo di compliance specifico può leggere il log
CREATE POLICY audit_readonly ON audit.audit_log
  FOR SELECT
  TO compliance_role
  USING (true);

-- Nessuna policy per DELETE/UPDATE = nessuno può cancellare
-- (con FORCE ROW LEVEL SECURITY si applica anche ai superuser delle tabelle)

-- 3. Aggiungere un trigger che impedisce modifiche
CREATE OR REPLACE FUNCTION audit.prevent_modifications()
RETURNS TRIGGER AS $$
BEGIN
  RAISE EXCEPTION 'Il log di audit è immutabile. Operazione negata.';
  RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER no_audit_modifications
  BEFORE UPDATE OR DELETE ON audit.audit_log
  FOR EACH ROW EXECUTE FUNCTION audit.prevent_modifications();

-- 4. Inviare i log anche a un sistema esterno (SIEM)
-- Usare un consumer Debezium/logical replication per sincronizzare
-- audit.audit_log verso Elasticsearch o Splunk
-- Un attaccante che compromette PostgreSQL non può toccare il SIEM
```

### Archiviazione e Retention

```sql
-- Policy di retention: mantenere audit log per 2 anni (requisito GDPR/PCI-DSS)
-- Archiviare i log più vecchi su cold storage prima di cancellarli

-- Funzione per archiviare su S3 e poi cancellare
CREATE OR REPLACE PROCEDURE audit.archive_old_logs(retention_months INT DEFAULT 24)
LANGUAGE plpgsql AS $$
DECLARE
  cutoff_date TIMESTAMPTZ;
BEGIN
  cutoff_date := NOW() - (retention_months || ' months')::INTERVAL;
  
  -- Esportare in CSV su S3 tramite COPY (se disponibile)
  PERFORM pg_catalog.pg_file_write(
    '/tmp/audit_export_' || to_char(NOW(), 'YYYYMM') || '.csv',
    (SELECT STRING_AGG(row_to_json(t)::TEXT, E'\n')
     FROM audit.audit_log t
     WHERE event_time < cutoff_date)::TEXT,
    false
  );
  
  -- Upload su S3 (tramite shell command o FDW)
  -- Poi cancellare dopo conferma upload
  -- DELETE FROM audit.audit_log WHERE event_time < cutoff_date;
  -- (da eseguire solo dopo conferma archiviazione)
END;
$$;
```

## Integrazione con SIEM

```python
#!/usr/bin/env python3
"""
Forwarder del log di audit PostgreSQL verso un SIEM (es. Splunk o Elasticsearch).
Usa logical replication per catturare i cambiamenti in tempo reale.
"""
import psycopg2
from psycopg2.extras import LogicalReplicationConnection
import json
import logging
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

class AuditLogForwarder:
    """
    Consuma le modifiche alla tabella audit.audit_log via logical replication
    e le invia a un SIEM esterno.
    """
    
    def __init__(self, db_dsn: str, siem_url: str, slot_name: str = 'audit_siem_slot'):
        self.db_dsn = db_dsn
        self.siem_url = siem_url
        self.slot_name = slot_name
    
    def create_slot(self):
        """Creare il slot di replica logica se non esiste."""
        conn = psycopg2.connect(self.db_dsn, connection_factory=LogicalReplicationConnection)
        try:
            conn.cursor().create_replication_slot(
                self.slot_name,
                output_plugin='pgoutput'
            )
        except psycopg2.errors.DuplicateObject:
            pass  # slot già esistente
        finally:
            conn.close()
    
    def start_forwarding(self):
        """Avviare il forwarding continuo."""
        conn = psycopg2.connect(self.db_dsn, connection_factory=LogicalReplicationConnection)
        cur = conn.cursor()
        
        cur.start_replication(
            slot_name=self.slot_name,
            options={
                'publication_names': 'audit_publication',
                'proto_version': '1'
            }
        )
        
        def process_message(msg):
            payload = json.loads(msg.payload)
            
            # Inviare al SIEM
            siem_event = {
                '@timestamp': datetime.utcnow().isoformat(),
                'source': 'postgresql-audit',
                'event': payload,
                'host': 'db-primary.example.com'
            }
            
            try:
                response = requests.post(
                    self.siem_url,
                    json=siem_event,
                    timeout=5
                )
                response.raise_for_status()
                msg.cursor.send_feedback(flush_lsn=msg.data_start)
            except requests.RequestException as e:
                logger.error(f"Errore invio a SIEM: {e}")
                # Non avanzare il LSN: riproveremo al prossimo giro
        
        logger.info("Avvio forwarding audit log verso SIEM")
        cur.consume_stream(process_message)
```

## Compliance Check Automatico

```sql
-- Query per verificare i requisiti PCI-DSS relativi al database

-- PCI-DSS Req 7: Limitare l'accesso ai dati del titolare di carta
-- Verificare che solo i ruoli autorizzati accedano alle tabelle payment*
SELECT
  grantee,
  table_name,
  privilege_type
FROM information_schema.role_table_grants
WHERE table_name LIKE '%payment%'
  OR table_name LIKE '%card%'
  OR table_name LIKE '%credit%'
ORDER BY table_name, grantee;

-- PCI-DSS Req 8: Identificare e autenticare l'accesso ai componenti di sistema
-- Verificare che nessun utente usi autenticazione trust o md5 legacy
SELECT
  rolname,
  rolsuper,
  rolconnlimit
FROM pg_roles
WHERE rolcanlogin = true
ORDER BY rolname;

-- Verificare in pg_hba.conf (non interrogabile via SQL direttamente)
-- Usare uno script esterno per analizzare pg_hba.conf

-- GDPR: Verificare la presenza di dati personali senza crittografia
-- (questo è un audit manuale: verificare le colonne note)
SELECT
  column_name,
  table_name,
  data_type
FROM information_schema.columns
WHERE (
  column_name ILIKE '%ssn%' OR
  column_name ILIKE '%social_security%' OR
  column_name ILIKE '%credit_card%' OR
  column_name ILIKE '%passport%' OR
  column_name ILIKE '%tax_id%'
)
AND data_type != 'bytea'  -- non crittografato (bytea indica storage binario, tipicamente cifrato)
AND table_schema NOT IN ('pg_catalog', 'information_schema')
ORDER BY table_name, column_name;
```

