# Compliance e Normative per i Database

La compliance normativa impone requisiti specifici su come i dati vengono protetti, conservati, e trattati. Le principali normative che impattano i database sono: GDPR (Europa), PCI-DSS (dati di pagamento), HIPAA (dati sanitari USA), e SOC2 (cloud service providers). Ogni normativa ha requisiti diversi ma condivide principi comuni: riservatezza, integrità, disponibilità, e accountability.

## GDPR: General Data Protection Regulation

Il GDPR si applica a qualsiasi organizzazione che tratta dati personali di residenti EU. Per i database, i requisiti principali riguardano: minimizzazione dei dati, diritto all'oblio, portabilità, e trasparenza.

### Catasto dei Dati Personali

Il primo passo per la compliance GDPR è sapere dove si trovano i dati personali nel database.

```sql
-- Inventario automatico delle colonne potenzialmente PII
-- (da completare con conoscenza del dominio)
SELECT
  t.table_schema,
  t.table_name,
  c.column_name,
  c.data_type,
  -- Classificazione automatica basata sul nome della colonna
  CASE
    WHEN c.column_name ~* '(email|mail)' THEN 'email'
    WHEN c.column_name ~* '(phone|telefono|cellulare|mobile)' THEN 'phone'
    WHEN c.column_name ~* '(name|nome|cognome|first_name|last_name|surname)' THEN 'name'
    WHEN c.column_name ~* '(address|indirizzo|via|street|city|citta|cap|zip|postal)' THEN 'address'
    WHEN c.column_name ~* '(birth|nascita|dob|date_of_birth)' THEN 'birth_date'
    WHEN c.column_name ~* '(ssn|fiscal_code|codice_fiscale|tax_id|passport)' THEN 'national_id'
    WHEN c.column_name ~* '(ip_address|ip_addr|user_agent|device)' THEN 'technical_id'
    WHEN c.column_name ~* '(credit_card|card_number|iban|account)' THEN 'financial'
    ELSE 'review_needed'
  END AS pii_category
FROM information_schema.tables t
JOIN information_schema.columns c
  ON c.table_schema = t.table_schema AND c.table_name = t.table_name
WHERE t.table_schema NOT IN ('pg_catalog', 'information_schema', 'audit')
  AND t.table_type = 'BASE TABLE'
ORDER BY t.table_schema, t.table_name, c.column_name;
```

### Diritto all'Oblio (Right to Erasure)

```sql
-- Implementare il diritto all'oblio in modo sicuro

-- Strategia 1: Pseudonymization (preferita rispetto alla cancellazione completa)
-- I dati vengono anonimizzati, ma le statistiche aggregate sono preservate
CREATE OR REPLACE FUNCTION gdpr_erase_user(p_user_id INT)
RETURNS VOID AS $$
DECLARE
  pseudonym TEXT;
BEGIN
  -- Generare un pseudonimo deterministico ma non reversibile
  pseudonym := 'DELETED-' || encode(
    hmac(p_user_id::TEXT, current_setting('app.gdpr_key'), 'sha256'),
    'hex'
  );
  
  -- Pseudonymizzare i dati personali
  UPDATE users
  SET
    name = pseudonym,
    email = pseudonym || '@deleted.invalid',
    phone = NULL,
    address = NULL,
    date_of_birth = NULL,
    deleted_at = NOW(),
    deletion_reason = 'GDPR Art. 17 - Right to Erasure'
  WHERE id = p_user_id;
  
  -- Cancellare dati strettamente personali non aggregabili
  DELETE FROM user_documents WHERE user_id = p_user_id;
  DELETE FROM user_sessions WHERE user_id = p_user_id;
  
  -- NON cancellare: ordini, transazioni (necessari per obblighi contabili)
  -- Ma anonimizzare i riferimenti
  UPDATE orders
  SET customer_name = pseudonym, customer_email = pseudonym || '@deleted.invalid'
  WHERE user_id = p_user_id;
  
  -- Registrare l'azione nell'audit log
  INSERT INTO gdpr_erasure_log (user_id, erased_at, pseudonym)
  VALUES (p_user_id, NOW(), pseudonym);
  
  RAISE NOTICE 'Utente % anonimizzato con pseudonimo %', p_user_id, pseudonym;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

### Diritto alla Portabilità

```sql
-- Esportare tutti i dati di un utente in formato strutturato
CREATE OR REPLACE FUNCTION gdpr_export_user_data(p_user_id INT)
RETURNS JSONB AS $$
DECLARE
  result JSONB;
BEGIN
  SELECT jsonb_build_object(
    'export_date', NOW(),
    'user_id', p_user_id,
    'profile', (
      SELECT row_to_json(u)
      FROM (
        SELECT id, name, email, phone, date_of_birth, created_at
        FROM users
        WHERE id = p_user_id
      ) u
    ),
    'orders', (
      SELECT jsonb_agg(
        jsonb_build_object(
          'order_id', o.id,
          'date', o.created_at,
          'items', (
            SELECT jsonb_agg(oi.*)
            FROM order_items oi WHERE oi.order_id = o.id
          ),
          'total', o.total_amount
        )
      )
      FROM orders o WHERE o.user_id = p_user_id
    ),
    'preferences', (
      SELECT row_to_json(p)
      FROM user_preferences p WHERE p.user_id = p_user_id
    )
  ) INTO result;
  
  RETURN result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Uso:
-- SELECT gdpr_export_user_data(42);
-- Il risultato è JSON scaricabile in formato leggibile
```

### Data Retention Policy

```sql
-- Implementare le retention policy del GDPR
-- I dati non devono essere mantenuti oltre il necessario

-- Tabella di configurazione delle retention
CREATE TABLE gdpr_retention_policies (
  table_name TEXT PRIMARY KEY,
  retention_days INT NOT NULL,
  deletion_strategy TEXT NOT NULL,  -- 'delete', 'anonymize', 'archive'
  legal_basis TEXT,                 -- motivo della retention
  last_reviewed DATE NOT NULL
);

INSERT INTO gdpr_retention_policies VALUES
  ('user_sessions', 90, 'delete', 'security', '2025-01-01'),
  ('user_activity_logs', 365, 'anonymize', 'analytics', '2025-01-01'),
  ('orders', 2555, 'archive', 'fiscal_obligations', '2025-01-01'),  -- 7 anni
  ('marketing_consents', 1825, 'delete', 'consent_expires', '2025-01-01');  -- 5 anni

-- Job periodico per applicare le retention policy
CREATE OR REPLACE PROCEDURE apply_retention_policies()
LANGUAGE plpgsql AS $$
DECLARE
  policy RECORD;
  rows_affected INT;
BEGIN
  FOR policy IN SELECT * FROM gdpr_retention_policies LOOP
    IF policy.deletion_strategy = 'delete' THEN
      EXECUTE format(
        'DELETE FROM %I WHERE created_at < NOW() - INTERVAL ''%s days''',
        policy.table_name,
        policy.retention_days
      );
      GET DIAGNOSTICS rows_affected = ROW_COUNT;
      RAISE NOTICE 'Tabella %: cancellate % righe (policy: % giorni)',
        policy.table_name, rows_affected, policy.retention_days;
    END IF;
  END LOOP;
END;
$$;
```

## PCI-DSS: Payment Card Industry Data Security Standard

PCI-DSS si applica a qualsiasi organizzazione che elabora, memorizza, o trasmette dati di carte di pagamento. Per i database, i requisiti principali sono: crittografia dei dati sensibili, controllo accessi, e logging.

### Protezione dei Dati del Titolare di Carta

```sql
-- PCI-DSS richiede che i dati sensibili della carta siano protetti

-- Dati PROIBITI da memorizzare (mai, nemmeno cifrati):
-- - Full Magnetic Stripe data
-- - CAV2/CVC2/CVV2/CID (codice di sicurezza)
-- - PIN e PIN block

-- Dati PERMESSI con protezione adeguata:
-- - PAN (Primary Account Number): crittografato e tronca
-- - Nome del titolare
-- - Data di scadenza

CREATE TABLE payment_cards (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id INT NOT NULL,
  
  -- PAN: memorizzare solo i primi 6 e gli ultimi 4 cifre (IIN + last4)
  -- I 6 cifre iniziali identificano l'emittente (BIN)
  pan_first6 CHAR(6),         -- primi 6 cifre (visibili)
  pan_last4 CHAR(4),          -- ultimi 4 cifre (visibili)
  pan_token TEXT NOT NULL,    -- token da payment processor (Stripe, Braintree)
  -- MAI memorizzare il PAN completo nel proprio database
  -- Usare tokenization di terze parti
  
  cardholder_name TEXT NOT NULL,
  expiry_month SMALLINT NOT NULL,
  expiry_year SMALLINT NOT NULL,
  -- NEVER: cvv TEXT → PCI-DSS vieta esplicitamente la memorizzazione del CVV
  
  is_default BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Masking del PAN per visualizzazione
CREATE OR REPLACE FUNCTION mask_pan(first6 CHAR(6), last4 CHAR(4))
RETURNS TEXT AS $$
BEGIN
  RETURN first6 || '******' || last4;
  -- Risultato: 411111******1111 (formato tipico per display UI)
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Verifica compliance: assicurarsi che nessun PAN completo sia presente
-- Questa è una query di audit periodica
SELECT table_name, column_name
FROM information_schema.columns
WHERE (
  column_name ILIKE '%card_number%' OR
  column_name ILIKE '%pan%' OR
  column_name ILIKE '%cvv%' OR
  column_name ILIKE '%cvc%'
)
AND data_type NOT IN ('bytea')  -- bytea indica crittografia (controllare manualmente)
AND table_schema NOT IN ('pg_catalog', 'information_schema');
```

### Separazione dell'Ambiente CDE

```sql
-- CDE (Cardholder Data Environment): isolamento del database che gestisce i dati di carta

-- Schema separato per il CDE
CREATE SCHEMA payment_cde;

-- Accesso al CDE: solo per utenti specifici
REVOKE ALL ON SCHEMA payment_cde FROM PUBLIC;
GRANT USAGE ON SCHEMA payment_cde TO payment_service_role;

-- Log di tutti gli accessi al CDE (PCI-DSS Req 10)
ALTER ROLE payment_service_role SET pgaudit.log = 'all';
ALTER ROLE payment_service_role SET pgaudit.log_relation = on;
```

## HIPAA: Health Insurance Portability and Accountability Act

HIPAA si applica alle organizzazioni sanitarie USA che trattano PHI (Protected Health Information).

```sql
-- PHI: informazioni sanitarie protette
-- Include: nome, indirizzo, data di nascita, diagnosi, prescrizioni, ecc.

-- Schema per dati HIPAA
CREATE SCHEMA phi;  -- Protected Health Information

-- Tabella diagnosi crittografata
CREATE TABLE phi.diagnoses (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  patient_id INT NOT NULL,
  icd10_code TEXT NOT NULL,         -- codice ICD-10 (es. "I10" per ipertensione)
  description_encrypted BYTEA,     -- descrizione in chiaro crittografata
  provider_id INT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  
  -- HIPAA richiede che sappiamo CHI ha acceduto ai dati
  -- Non memorizzare il motivo dell'accesso: non è richiesto da HIPAA
  FOREIGN KEY (patient_id) REFERENCES patients(id),
  FOREIGN KEY (provider_id) REFERENCES healthcare_providers(id)
);

-- Audit mandatory per HIPAA (Access Report)
-- HIPAA Req: pazienti hanno diritto di sapere chi ha acceduto ai loro dati
CREATE TABLE phi.access_log (
  id BIGSERIAL PRIMARY KEY,
  access_time TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  patient_id INT NOT NULL,
  accessed_by_user_id INT NOT NULL,
  access_type TEXT NOT NULL,  -- 'read', 'write', 'delete'
  access_reason TEXT,         -- opzionale ma raccomandato
  data_accessed TEXT[],       -- nomi delle tabelle/record acceduti
  client_app TEXT
);

-- Vista per il paziente: "chi ha visto le mie informazioni?"
CREATE OR REPLACE VIEW phi.my_access_report AS
SELECT
  al.access_time,
  hp.name AS accessed_by,
  hp.role AS accessor_role,
  al.access_type,
  al.access_reason,
  al.data_accessed
FROM phi.access_log al
JOIN healthcare_providers hp ON hp.user_id = al.accessed_by_user_id
WHERE al.patient_id = current_setting('app.patient_id', true)::int
ORDER BY al.access_time DESC;
```

## SOC2: Trust Service Criteria

SOC2 valuta i controlli di sicurezza di un service provider. I cinque Trust Service Criteria sono: Security, Availability, Processing Integrity, Confidentiality, Privacy.

```sql
-- SOC2 CC6: Logical and Physical Access Controls

-- Verifica che tutti gli utenti abbiano solo i privilegi necessari
-- Questo script genera un report per i revisori SOC2
CREATE OR REPLACE VIEW soc2_access_review AS
SELECT
  r.rolname AS username,
  r.rolsuper AS is_superuser,
  r.rolcreaterole AS can_create_roles,
  r.rolcreatedb AS can_create_databases,
  r.rolcanlogin AS can_login,
  r.rolconnlimit AS connection_limit,
  r.rolvaliduntil AS password_expires,
  STRING_AGG(m.rolname, ', ') AS granted_roles
FROM pg_roles r
LEFT JOIN pg_auth_members am ON am.member = r.oid
LEFT JOIN pg_roles m ON m.oid = am.roleid
WHERE r.rolcanlogin = true
GROUP BY r.rolname, r.rolsuper, r.rolcreaterole, r.rolcreatedb,
         r.rolcanlogin, r.rolconnlimit, r.rolvaliduntil
ORDER BY r.rolname;

-- CC7: System Operations - monitoraggio continuo
-- Verificare che i backup siano stati eseguiti
CREATE TABLE infrastructure.backup_log (
  id SERIAL PRIMARY KEY,
  backup_time TIMESTAMPTZ DEFAULT NOW(),
  backup_type TEXT,    -- 'full', 'incremental', 'wal'
  size_bytes BIGINT,
  duration_seconds INT,
  status TEXT,         -- 'success', 'failed'
  destination TEXT,    -- 's3://...', '/backup/...'
  verified BOOLEAN DEFAULT FALSE  -- il backup è stato testato con restore?
);

-- Report SOC2: tutti i backup degli ultimi 30 giorni
SELECT
  DATE_TRUNC('day', backup_time) AS day,
  backup_type,
  status,
  COUNT(*) AS count,
  SUM(size_bytes) / 1024 / 1024 / 1024 AS total_gb
FROM infrastructure.backup_log
WHERE backup_time > NOW() - INTERVAL '30 days'
GROUP BY day, backup_type, status
ORDER BY day DESC;
```

## Matrice di Compliance

| Controllo | GDPR | PCI-DSS | HIPAA | SOC2 |
|-----------|------|---------|-------|------|
| Crittografia a riposo | Raccomandato | Richiesto (PAN) | Richiesto (PHI) | CC6 |
| Crittografia in transito | Richiesto | Richiesto | Richiesto | CC6 |
| Controllo accessi RBAC | Richiesto | Req 7-8 | Richiesto | CC6 |
| Audit logging | Richiesto | Req 10 | Richiesto | CC7 |
| Backup e recovery | Art. 32 | Req 12 | Richiesto | A1 |
| Retention policy | Art. 5 | - | Req 164.530(j) | P5 |
| Right to erasure | Art. 17 | - | - | P4 |
| Penetration testing | Art. 32 | Req 11 | - | CC4 |
| Incident response | Art. 33-34 | Req 12 | Req 164.308 | CC7 |

La compliance non è un progetto con una fine: è un processo continuo di valutazione, implementazione, e verifica. Un'organizzazione tipicamente inizia con i controlli tecnici (crittografia, accessi, audit) e poi matura verso controlli procedurali (training, policy, risk assessment).

