# Compliance Frameworks for Data Systems — PCI-DSS, HIPAA, SOX, and Beyond

## Table of Contents

1. [PCI-DSS v4.0 for Data Systems](#1-pci-dss-v40-for-data-systems)
2. [HIPAA Technical Safeguards](#2-hipaa-technical-safeguards)
3. [SOX Compliance for Data](#3-sox-compliance-for-data)
4. [GDPR Technical Requirements](#4-gdpr-technical-requirements)
5. [NIST Frameworks](#5-nist-frameworks)
6. [Industry-Specific Regulations](#6-industry-specific-regulations)
7. [Control Implementation](#7-control-implementation)
8. [Audit Preparation](#8-audit-preparation)
9. [Continuous Compliance](#9-continuous-compliance)
10. [Lab Exercises](#10-lab-exercises)

---

## 1. PCI-DSS v4.0 for Data Systems

### 1.1 Cardholder Data Environment (CDE) Scoping

PCI-DSS v4.0 (effective March 2024, mandatory March 2025) fundamentally reshapes how organizations scope their cardholder data environments. The scoping exercise determines which systems, networks, and processes fall under PCI-DSS requirements — an incorrect scope either leaves real attack surfaces unaudited or inflates compliance costs by pulling in systems that never touch card data.

**Scoping Categories:**

| Category | Definition | PCI Obligation |
|----------|-----------|----------------|
| CDE Systems | Store, process, or transmit CHD/SAD | Full PCI-DSS requirements |
| Connected-to Systems | Direct connectivity to CDE without segmentation | Most requirements apply |
| Security-Impacting | Could affect CDE security (DNS, AD, SIEM) | Subset of requirements |
| Out-of-Scope | No connectivity, no impact pathway | Documented exclusion only |

**Database Scoping Decision Tree:**

```
Does the database store PAN, track data, CVV, or PIN?
├─ YES → CDE system (full scope)
└─ NO → Does it connect to a CDE-scoped network segment?
    ├─ YES → Connected-to (apply relevant requirements)
    └─ NO → Does it provide security services to the CDE?
        ├─ YES → Security-impacting (subset applies)
        └─ NO → Document as out-of-scope
```

**v4.0 Scoping Changes:**

- Customized Approach: Organizations can now meet objectives through alternative controls with documented justification (replaces compensating controls for Defined Approach)
- Targeted Risk Analysis (TRA): Required for any control where the entity determines frequency (e.g., log review frequency, vulnerability scan cadence)
- Applicability Notes: Each requirement now has explicit guidance on applicability, reducing scope disputes

**Scoping Documentation Requirements:**

```
PCI-DSS v4.0 Requirement 12.5.2:
- Annual scope validation (was implicit, now explicit)
- Document all data flows into/out of CDE
- Identify all system components in CDE
- Confirm segmentation controls function correctly
- Retain evidence of scoping activities
```

### 1.2 Requirement 3 Deep Dive: Protect Stored Account Data

Requirement 3 is the most database-relevant section of PCI-DSS. In v4.0, it underwent significant restructuring.

**3.1 — Storage Minimization:**

```sql
-- Anti-pattern: storing full PAN without business justification
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    pan VARCHAR(19),          -- VIOLATION: stored unmasked PAN
    expiry_date VARCHAR(5),   -- VIOLATION: no retention justification
    cvv VARCHAR(4),           -- VIOLATION: SAD never stored post-auth
    amount DECIMAL(10,2)
);

-- Compliant: tokenized with justified retention
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    token_ref UUID NOT NULL,  -- Reference to token vault
    last_four CHAR(4),        -- Display-only masked value
    amount DECIMAL(10,2),
    retention_expires_at TIMESTAMP NOT NULL  -- Automated purge
);
```

**3.2 — Sensitive Authentication Data (SAD):**

Post-authorization storage of SAD (full track, CVV2/CVC2, PIN/PIN block) is prohibited regardless of encryption. This is non-negotiable — no compensating control, no customized approach. The database must never contain these elements after the authorization response.

**3.3 — PAN Display Restriction:**

Maximum display: first 6 and last 4 digits (BIN + last four). v4.0 clarification: personnel with legitimate business need may view full PAN if access is logged and role-justified.

**3.4 — PAN Rendering Unreadable:**

| Method | Suitability | Key Consideration |
|--------|-------------|-------------------|
| Strong cryptography (AES-256) | Primary method for databases | Key management is the real challenge |
| Truncation | Display/logs only | Cannot reconstruct PAN from truncated value |
| Tokenization | Preferred for reducing scope | Token vault becomes CDE; rest is descoped |
| One-way hash (keyed, e.g., HMAC-SHA256) | Limited use cases | Irreversible — cannot retrieve original |

**3.5 — Key Management:**

```
Key Management Lifecycle (PCI-DSS 3.5/3.6/3.7):
┌─────────────────────────────────────────────────────┐
│ Generation → Storage → Distribution → Usage →       │
│ Rotation → Retirement → Destruction                 │
└─────────────────────────────────────────────────────┘

Requirements:
- KEK (Key Encrypting Key) stored separately from DEK (Data Encrypting Key)
- Split knowledge and dual control for key operations
- Cryptoperiod: rotate DEKs annually minimum (TRA-justified)
- Key custodians: minimum 2, documented acknowledgment
- HSM or equivalent for production key storage
```

### 1.3 Encryption Requirements

**AES-256 Implementation for Databases:**

```sql
-- PostgreSQL: pgcrypto column-level encryption
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Encrypt PAN at insert
INSERT INTO card_vault (token_id, encrypted_pan)
VALUES (
    gen_random_uuid(),
    pgp_sym_encrypt('4111111111111111', current_setting('app.encryption_key'))
);

-- Decrypt with authorized access only
SELECT pgp_sym_decrypt(encrypted_pan, current_setting('app.encryption_key'))
FROM card_vault
WHERE token_id = $1;
```

**Transparent Data Encryption (TDE):**

TDE encrypts at-rest data at the tablespace/file level. It protects against physical theft and unauthorized file access but not against authorized database sessions.

```
TDE Limitations (from PCI perspective):
- Does NOT protect against SQL injection (authenticated session reads cleartext)
- Does NOT protect against privilege escalation within the DBMS
- Does NOT satisfy 3.4 alone if database users can SELECT PAN
- MUST be combined with column-level encryption or tokenization
```

**Key Management Architecture:**

```
┌─────────────────────────────────────────────────────────────┐
│                    HSM (FIPS 140-2 Level 3)                  │
│    ┌─────────────────────────────────────────────┐          │
│    │  Master Key (never leaves HSM)              │          │
│    └─────────────────────────────────────────────┘          │
└───────────────────────────┬─────────────────────────────────┘
                            │ Wraps/Unwraps
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Key Management Server                           │
│    ┌─────────────────────────────────────────────┐          │
│    │  KEK (wrapped by Master Key)                │          │
│    │  DEKs (wrapped by KEK)                      │          │
│    └─────────────────────────────────────────────┘          │
└───────────────────────────┬─────────────────────────────────┘
                            │ DEK delivered per-session
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Database Server                                 │
│    Uses DEK for encrypt/decrypt operations                  │
│    DEK in memory only, never persisted to disk              │
└─────────────────────────────────────────────────────────────┘
```

### 1.4 Tokenization

Tokenization removes PAN from the transactional database entirely, replacing it with a non-reversible token. The token vault (where PAN-to-token mappings live) becomes the CDE, but all systems referencing tokens are descoped.

**Tokenization Architecture:**

```
┌──────────────────┐         ┌──────────────────────────┐
│  Application     │         │  Token Vault (CDE)       │
│  (Out of Scope)  │ ──────► │  PAN ↔ Token mapping     │
│  Uses tokens     │         │  AES-256 encrypted PAN   │
│  only            │         │  HSM-backed keys         │
└──────────────────┘         │  Full PCI-DSS scope      │
                             └──────────────────────────┘
```

**Format-Preserving Tokenization:**

```
Original PAN:  4111 1111 1111 1111
Token:         4111 8392 7461 1111  (preserves BIN + last 4, random middle)

Benefits:
- Passes Luhn check (optional)
- Fits existing VARCHAR(19) columns
- No schema changes required
- Downstream systems unaware of tokenization
```

### 1.5 Requirement 7: Access Control

v4.0 restructured Requirement 7 around least privilege and role-based access.

```sql
-- PostgreSQL RBAC for PCI compliance
-- Principle: no user gets more access than their role demands

-- Read-only role for reporting (masked data only)
CREATE ROLE pci_reporting LOGIN;
GRANT SELECT (token_ref, last_four, amount, transaction_date)
    ON transactions TO pci_reporting;
-- Note: no access to encrypted_pan column

-- Application service account (tokenize/detokenize)
CREATE ROLE pci_app_service LOGIN;
GRANT SELECT, INSERT ON card_vault TO pci_app_service;
GRANT EXECUTE ON FUNCTION tokenize_pan(text) TO pci_app_service;
GRANT EXECUTE ON FUNCTION detokenize(uuid) TO pci_app_service;

-- DBA role (schema management, no data access)
CREATE ROLE pci_dba LOGIN;
GRANT ALL ON SCHEMA payments TO pci_dba;
REVOKE SELECT ON card_vault FROM pci_dba;  -- Cannot read card data
```

### 1.6 Requirement 10: Logging and Monitoring

```sql
-- pgAudit configuration for PCI Requirement 10
-- postgresql.conf
-- pgaudit.log = 'read, write, ddl, role'
-- pgaudit.log_catalog = on
-- pgaudit.log_parameter = on
-- pgaudit.log_statement_once = off

-- What must be logged (Req 10.2):
-- - All individual access to cardholder data
-- - All actions by any individual with root/admin privileges
-- - Access to audit trails
-- - Invalid logical access attempts
-- - Use of identification and authentication mechanisms
-- - Initialization, stopping, or pausing of audit logs
-- - Creation and deletion of system-level objects

-- Log retention: 12 months minimum, 3 months immediately accessible
```

### 1.7 Network Segmentation for Databases

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Corporate Network                           │
│    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐          │
│    │ Workstations │    │   Email     │    │   ERP       │          │
│    └─────────────┘    └─────────────┘    └─────────────┘          │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ DENY ALL (default)
                                │
┌───────────────────────────────┼─────────────────────────────────────┐
│              DMZ              │                                      │
│    ┌─────────────────┐       │                                      │
│    │  Web Servers    │───────┤                                      │
│    │  (tokenized)    │       │                                      │
│    └─────────────────┘       │                                      │
└───────────────────────────────┼─────────────────────────────────────┘
                                │ ALLOW: TCP 5432 from App servers only
                                │
┌───────────────────────────────┼─────────────────────────────────────┐
│           CDE Network Segment │                                      │
│    ┌─────────────────┐    ┌──┴──────────────┐                      │
│    │  App Servers    │    │  Card Database   │                      │
│    │  (PCI scope)    │────│  (PCI scope)     │                      │
│    └─────────────────┘    └─────────────────┘                      │
│                                                                      │
│    Firewall rules: deny all, allow explicit flows only              │
│    IDS/IPS monitoring on segment boundaries                         │
│    No direct internet access from CDE segment                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. HIPAA Technical Safeguards

### 2.1 §164.312 Requirements Overview

The HIPAA Security Rule (45 CFR Part 164) establishes standards for protecting electronic Protected Health Information (ePHI). The Technical Safeguards (§164.312) are the most relevant to data engineering and database systems.

**Technical Safeguard Categories:**

| Section | Safeguard | Standard | Implementation |
|---------|-----------|----------|---------------|
| §164.312(a) | Access Control | Required | Unique user ID, emergency access, auto logoff, encryption/decryption |
| §164.312(b) | Audit Controls | Required | Hardware, software, procedural mechanisms |
| §164.312(c) | Integrity | Addressable | Mechanism to authenticate ePHI |
| §164.312(d) | Authentication | Required | Verify person/entity seeking access |
| §164.312(e) | Transmission Security | Addressable | Integrity controls, encryption |

**Required vs. Addressable:**

A critical distinction that confuses many assessors: "Addressable" does not mean "optional." It means the covered entity must assess whether the implementation specification is reasonable and appropriate. If it is, implement it. If not, document why and implement an equivalent alternative. You cannot simply skip addressable specifications.

### 2.2 Access Control (§164.312(a)(1))

**Unique User Identification (Required):**

```sql
-- Every human and service accessing ePHI must have unique credentials
-- NEVER: shared accounts, generic logins, embedded credentials

-- PostgreSQL: enforce unique identification
CREATE ROLE dr_smith LOGIN PASSWORD 'bcrypt_hashed_initial'
    VALID UNTIL '2025-12-31'
    CONNECTION LIMIT 3;

-- Role-based access aligned with job function
CREATE ROLE clinician;
CREATE ROLE billing_clerk;
CREATE ROLE researcher;

GRANT clinician TO dr_smith;

-- Row-level security for patient assignment
ALTER TABLE patient_records ENABLE ROW LEVEL SECURITY;

CREATE POLICY clinician_assigned_patients ON patient_records
    FOR SELECT
    TO clinician
    USING (
        assigned_clinician_id = current_setting('app.user_id')::int
        OR care_team @> ARRAY[current_setting('app.user_id')::int]
    );
```

**Emergency Access Procedure (Required):**

```sql
-- Break-glass procedure: documented, audited, time-limited
CREATE OR REPLACE FUNCTION emergency_access_grant(
    p_user_id INT,
    p_patient_id INT,
    p_reason TEXT,
    p_authorizer TEXT
) RETURNS VOID AS $$
BEGIN
    -- Log the emergency access event
    INSERT INTO emergency_access_log (
        user_id, patient_id, reason, authorizer,
        granted_at, expires_at, reviewed
    ) VALUES (
        p_user_id, p_patient_id, p_reason, p_authorizer,
        NOW(), NOW() + INTERVAL '4 hours', FALSE
    );

    -- Grant temporary access
    INSERT INTO temporary_access_grants (user_id, patient_id, expires_at)
    VALUES (p_user_id, p_patient_id, NOW() + INTERVAL '4 hours');

    -- Alert privacy officer
    PERFORM pg_notify('emergency_access', json_build_object(
        'user_id', p_user_id,
        'patient_id', p_patient_id,
        'reason', p_reason
    )::text);
END;
$$ LANGUAGE plpgsql;
```

**Automatic Logoff (Addressable):**

```sql
-- PostgreSQL session timeout for ePHI databases
ALTER SYSTEM SET idle_in_transaction_session_timeout = '300000';  -- 5 min
ALTER SYSTEM SET statement_timeout = '60000';  -- 1 min max query

-- Application-level: session expiration
-- Set in connection pooler (PgBouncer):
-- server_idle_timeout = 300
-- client_idle_timeout = 180
```

### 2.3 Audit Controls (§164.312(b))

HIPAA requires audit controls that record and examine activity in systems containing ePHI. Unlike PCI-DSS which prescribes specific events, HIPAA allows the entity to determine what is appropriate — but OCR (Office for Civil Rights) investigations consistently expect comprehensive logging.

```sql
-- Comprehensive audit trigger for ePHI tables
CREATE OR REPLACE FUNCTION audit_ephi_access()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO ephi_audit_log (
        table_name,
        operation,
        user_name,
        user_ip,
        application_name,
        record_id,
        patient_id,
        old_values,
        new_values,
        accessed_at
    ) VALUES (
        TG_TABLE_NAME,
        TG_OP,
        current_user,
        inet_client_addr(),
        current_setting('application_name'),
        COALESCE(NEW.id, OLD.id),
        COALESCE(NEW.patient_id, OLD.patient_id),
        CASE WHEN TG_OP IN ('UPDATE', 'DELETE') THEN row_to_json(OLD) END,
        CASE WHEN TG_OP IN ('INSERT', 'UPDATE') THEN row_to_json(NEW) END,
        clock_timestamp()
    );
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Apply to all ePHI tables
CREATE TRIGGER audit_patient_records
    AFTER INSERT OR UPDATE OR DELETE ON patient_records
    FOR EACH ROW EXECUTE FUNCTION audit_ephi_access();

CREATE TRIGGER audit_diagnoses
    AFTER INSERT OR UPDATE OR DELETE ON diagnoses
    FOR EACH ROW EXECUTE FUNCTION audit_ephi_access();

-- Audit log retention: HIPAA requires 6 years minimum
-- (from date of creation OR last effective date, whichever is later)
```

### 2.4 ePHI at Rest and in Transit

**At Rest:**

```sql
-- Column-level encryption for high-sensitivity ePHI fields
-- (diagnosis, SSN, genetic data, substance abuse records)

CREATE TABLE patient_records (
    id SERIAL PRIMARY KEY,
    mrn VARCHAR(20) NOT NULL,           -- Medical Record Number (encrypted at app layer)
    name_encrypted BYTEA NOT NULL,       -- AES-256-GCM encrypted
    ssn_encrypted BYTEA,                 -- AES-256-GCM encrypted
    dob DATE,                            -- Encryption optional (PHI but lower sensitivity)
    diagnosis_encrypted BYTEA,           -- Always encrypted (42 CFR Part 2 for SUD)
    iv BYTEA NOT NULL,                   -- Initialization vector per row
    key_version INT NOT NULL DEFAULT 1   -- Supports key rotation
);

-- TDE for full-database protection (defense in depth)
-- PostgreSQL doesn't natively support TDE; use:
--   - pg_tde extension (community)
--   - AWS RDS encryption (KMS-managed)
--   - Azure Database for PostgreSQL (service-managed keys or BYOK)
--   - Full-disk encryption (LUKS) for self-managed
```

**In Transit:**

```
-- PostgreSQL TLS Configuration (postgresql.conf)
ssl = on
ssl_cert_file = '/etc/postgresql/server.crt'
ssl_key_file = '/etc/postgresql/server.key'
ssl_ca_file = '/etc/postgresql/ca.crt'
ssl_min_protocol_version = 'TLSv1.2'
ssl_ciphers = 'HIGH:!aNULL:!MD5:!3DES:!RC4'

-- Enforce TLS for all connections (pg_hba.conf)
hostssl all all 0.0.0.0/0 scram-sha-256 clientcert=verify-ca
hostssl all all ::/0       scram-sha-256 clientcert=verify-ca

-- Reject non-TLS connections
hostnossl all all 0.0.0.0/0 reject
```

### 2.5 Business Associate Agreements (BAA) for Cloud Databases

Any cloud provider hosting ePHI must execute a BAA with the covered entity. The BAA is not optional and must include:

- Permitted uses and disclosures of PHI
- Safeguards the BA will implement
- Breach notification obligations (within 60 days)
- Return or destruction of PHI upon termination
- Subcontractor chain requirements (BA must ensure subcontractors also comply)

**Cloud Database BAA Considerations:**

| Provider | BAA Coverage | Key Limitations |
|----------|-------------|-----------------|
| AWS (RDS, Aurora, DynamoDB) | Included in AWS BAA | Must configure encryption, logging, access control yourself |
| Azure (SQL, Cosmos, PostgreSQL) | Microsoft BAA | Some preview services excluded |
| GCP (Cloud SQL, BigQuery, Spanner) | Google Cloud BAA | Certain alpha/beta features excluded |
| MongoDB Atlas | Available on dedicated clusters | Shared clusters NOT covered |

**Critical**: A BAA does not transfer compliance responsibility. The covered entity remains liable for configuring the cloud service correctly. An unencrypted RDS instance with public access is a violation regardless of the BAA.

### 2.6 Minimum Necessary Standard

The Minimum Necessary Standard (§164.502(b)) requires that access to ePHI be limited to the minimum amount needed for the intended purpose. In database terms:

```sql
-- WRONG: Application queries SELECT * and filters in code
SELECT * FROM patient_records WHERE clinic_id = 5;

-- RIGHT: Query only necessary columns for the function
-- Billing clerk needs: MRN, name, insurance, dates of service
SELECT mrn, name_encrypted, insurance_group, date_of_service
FROM patient_records
WHERE clinic_id = 5;

-- BETTER: Views that enforce minimum necessary by role
CREATE VIEW billing_view AS
SELECT mrn, name_encrypted, insurance_group, date_of_service, cpt_codes
FROM patient_records
JOIN billing_records USING (encounter_id);

GRANT SELECT ON billing_view TO billing_clerk;
-- billing_clerk cannot access diagnosis, SSN, notes, etc.
```

### 2.7 De-identification Methods

**Safe Harbor Method (§164.514(b)(2)):**

Remove these 18 identifiers:
1. Names
2. Geographic subdivisions smaller than state (ZIP codes: first 3 digits if population >20k)
3. Dates (except year) related to individual — dates must be shifted or generalized
4. Phone numbers
5. Fax numbers
6. Email addresses
7. SSN
8. MRN (Medical Record Numbers)
9. Health plan beneficiary numbers
10. Account numbers
11. Certificate/license numbers
12. Vehicle identifiers and serial numbers
13. Device identifiers and serial numbers
14. Web URLs
15. IP addresses
16. Biometric identifiers
17. Full-face photographs
18. Any other unique identifying number/code

```sql
-- De-identification function implementing Safe Harbor
CREATE OR REPLACE FUNCTION deidentify_safe_harbor(
    p_patient_id INT,
    p_date_shift_days INT DEFAULT NULL  -- Consistent shift per patient
) RETURNS TABLE (
    age_at_encounter INT,
    gender CHAR(1),
    race VARCHAR(50),
    diagnosis_code VARCHAR(10),
    encounter_year INT,
    zip_3 CHAR(3)
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        LEAST(EXTRACT(YEAR FROM AGE(pr.dob))::INT, 89) AS age_at_encounter,
        pr.gender,
        pr.race,
        d.icd10_code AS diagnosis_code,
        EXTRACT(YEAR FROM e.encounter_date)::INT AS encounter_year,
        CASE
            WHEN zip_population_over_20k(LEFT(pr.zip, 3)) THEN LEFT(pr.zip, 3)
            ELSE '000'  -- Redact low-population ZIP prefixes
        END AS zip_3
    FROM patient_records pr
    JOIN encounters e ON e.patient_id = pr.id
    JOIN diagnoses d ON d.encounter_id = e.id
    WHERE pr.id = p_patient_id;
END;
$$ LANGUAGE plpgsql;
```

**Expert Determination (§164.514(a)):**

Requires a qualified statistical/scientific expert to determine that the risk of identifying any individual is "very small." More flexible than Safe Harbor but requires documentation of the expert's methods and results. Commonly used for research datasets where Safe Harbor would remove too much analytical value.

---

## 3. SOX Compliance for Data

### 3.1 Section 302/404 Requirements

The Sarbanes-Oxley Act (SOX) applies to publicly traded companies in the US and requires internal controls over financial reporting (ICFR). For data systems, this means any database that stores, processes, or produces data feeding into financial statements is subject to SOX controls.

**Section 302 — Corporate Responsibility for Financial Reports:**

CEO and CFO must personally certify that:
- Financial statements are accurate
- Internal controls are effective
- Material weaknesses are disclosed

**Section 404 — Management Assessment of Internal Controls:**

- 404(a): Management must assess effectiveness of ICFR annually
- 404(b): External auditor must attest to management's assessment (accelerated filers)

**Database Impact:**

```
Financial Data Flow Subject to SOX:
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Source   │───►│  ETL/    │───►│  Data    │───►│ Financial│
│  Systems  │    │  Pipeline│    │  Warehouse│    │ Reporting│
│  (ERP,   │    │          │    │          │    │  (10-K,  │
│   CRM)   │    │          │    │          │    │   10-Q)  │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
     │               │               │               │
     └───────────────┴───────────────┴───────────────┘
              ALL subject to SOX ICFR controls
```

### 3.2 Financial Data Integrity Controls

**Data Accuracy Controls:**

```sql
-- Reconciliation controls: source vs. warehouse totals
CREATE OR REPLACE FUNCTION sox_reconciliation_check(
    p_source_table TEXT,
    p_warehouse_table TEXT,
    p_date DATE
) RETURNS TABLE (
    metric TEXT,
    source_value NUMERIC,
    warehouse_value NUMERIC,
    variance NUMERIC,
    variance_pct NUMERIC,
    status TEXT
) AS $$
DECLARE
    v_threshold NUMERIC := 0.001;  -- 0.1% materiality threshold
BEGIN
    RETURN QUERY
    WITH source AS (
        SELECT COUNT(*) as row_count, SUM(amount) as total_amount
        FROM source_table WHERE posting_date = p_date
    ), warehouse AS (
        SELECT COUNT(*) as row_count, SUM(amount) as total_amount
        FROM warehouse_table WHERE posting_date = p_date
    )
    SELECT
        'Row Count'::TEXT,
        s.row_count::NUMERIC,
        w.row_count::NUMERIC,
        (w.row_count - s.row_count)::NUMERIC,
        CASE WHEN s.row_count > 0
            THEN ((w.row_count - s.row_count)::NUMERIC / s.row_count * 100)
            ELSE NULL
        END,
        CASE WHEN s.row_count = w.row_count THEN 'PASS' ELSE 'FAIL' END
    FROM source s, warehouse w
    UNION ALL
    SELECT
        'Total Amount'::TEXT,
        s.total_amount,
        w.total_amount,
        (w.total_amount - s.total_amount),
        CASE WHEN s.total_amount > 0
            THEN ((w.total_amount - s.total_amount) / s.total_amount * 100)
            ELSE NULL
        END,
        CASE WHEN ABS(w.total_amount - s.total_amount) / NULLIF(s.total_amount, 0) < v_threshold
            THEN 'PASS' ELSE 'FAIL'
        END
    FROM source s, warehouse w;
END;
$$ LANGUAGE plpgsql;
```

**Completeness Controls:**

```sql
-- Sequence gap detection for financial transactions
CREATE OR REPLACE FUNCTION detect_sequence_gaps(
    p_table TEXT,
    p_sequence_column TEXT,
    p_start BIGINT,
    p_end BIGINT
) RETURNS TABLE (gap_start BIGINT, gap_end BIGINT) AS $$
BEGIN
    RETURN QUERY EXECUTE format(
        'WITH numbered AS (
            SELECT %I AS seq_val,
                   LEAD(%I) OVER (ORDER BY %I) AS next_val
            FROM %I
            WHERE %I BETWEEN %s AND %s
        )
        SELECT seq_val + 1 AS gap_start, next_val - 1 AS gap_end
        FROM numbered
        WHERE next_val - seq_val > 1',
        p_sequence_column, p_sequence_column, p_sequence_column,
        p_table, p_sequence_column, p_start, p_end
    );
END;
$$ LANGUAGE plpgsql;
```

### 3.3 Change Management for Database Schemas

SOX demands that all changes to systems affecting financial reporting go through a controlled change management process.

```
SOX Change Management Requirements:
┌─────────────────────────────────────────────────────────────┐
│ 1. Change Request                                           │
│    - Business justification documented                      │
│    - Impact assessment (which financial reports affected?)   │
│    - Risk rating (high/medium/low)                          │
│                                                             │
│ 2. Approval                                                 │
│    - Segregated: requestor ≠ approver ≠ implementer         │
│    - CAB (Change Advisory Board) for high-risk              │
│    - Documented approval with timestamps                    │
│                                                             │
│ 3. Testing                                                  │
│    - Test in non-production environment first               │
│    - Regression testing against financial calculations      │
│    - Reconciliation validation post-change                  │
│                                                             │
│ 4. Implementation                                           │
│    - Scheduled maintenance window                           │
│    - Rollback plan documented and tested                    │
│    - Separation of duties enforced                          │
│                                                             │
│ 5. Post-Implementation Review                               │
│    - Verify change produced expected outcome                │
│    - Run reconciliation checks                              │
│    - Close change ticket with evidence                      │
└─────────────────────────────────────────────────────────────┘
```

**Migration Script Template (SOX-Compliant):**

```sql
-- Migration: ADD_REVENUE_RECOGNITION_COLUMN
-- Change Ticket: CHG-2024-1234
-- Approver: CFO / Controller
-- Impact: Revenue reports (10-Q, 10-K)
-- Rollback: DROP COLUMN IF EXISTS recognized_at

BEGIN;

-- Pre-change snapshot for rollback validation
CREATE TEMPORARY TABLE pre_change_snapshot AS
SELECT COUNT(*) as row_count, SUM(amount) as total
FROM revenue_transactions;

-- The change
ALTER TABLE revenue_transactions
    ADD COLUMN recognized_at TIMESTAMP,
    ADD COLUMN recognition_method VARCHAR(50)
        CHECK (recognition_method IN ('point_in_time', 'over_time'));

-- Post-change validation
DO $$
DECLARE
    v_pre_count BIGINT;
    v_post_count BIGINT;
BEGIN
    SELECT row_count INTO v_pre_count FROM pre_change_snapshot;
    SELECT COUNT(*) INTO v_post_count FROM revenue_transactions;

    IF v_pre_count != v_post_count THEN
        RAISE EXCEPTION 'Data integrity violation: row count changed from % to %',
            v_pre_count, v_post_count;
    END IF;
END $$;

-- Log the change
INSERT INTO schema_change_log (
    change_ticket, migration_name, applied_by, applied_at,
    pre_row_count, post_row_count, status
) VALUES (
    'CHG-2024-1234', 'ADD_REVENUE_RECOGNITION_COLUMN',
    current_user, NOW(),
    (SELECT row_count FROM pre_change_snapshot),
    (SELECT COUNT(*) FROM revenue_transactions),
    'SUCCESS'
);

COMMIT;
```

### 3.4 Separation of Duties

SOX requires that no single individual can initiate, authorize, and record a financial transaction — and the same principle applies to data systems.

```
SOX Separation of Duties Matrix (Database):
┌──────────────────────┬───────┬──────────┬─────────┬────────────┐
│ Function             │ DBA   │ Developer│ Analyst │ Auditor    │
├──────────────────────┼───────┼──────────┼─────────┼────────────┤
│ Schema changes       │  X    │  Request │         │  Review    │
│ Data modifications   │       │          │  X      │  Review    │
│ Access provisioning  │  X    │          │         │  Review    │
│ Query production     │       │          │  X      │            │
│ Backup/restore       │  X    │          │         │  Review    │
│ Audit log access     │       │          │         │  X         │
│ Deploy to prod       │  X    │          │         │  Review    │
│ Code development     │       │  X       │         │            │
└──────────────────────┴───────┴──────────┴─────────┴────────────┘

Critical Conflicts:
- Developer CANNOT deploy their own code to production
- DBA CANNOT modify financial data directly
- Nobody can modify audit logs (append-only, separate system)
```

### 3.5 Data Retention for Financial Records

SOX Section 802 mandates 7-year retention for audit workpapers and records relevant to the audit. In practice, financial data systems often retain longer.

```sql
-- Retention policy enforcement
CREATE TABLE data_retention_policy (
    table_name TEXT PRIMARY KEY,
    retention_years INT NOT NULL,
    regulation TEXT NOT NULL,
    purge_method TEXT NOT NULL CHECK (purge_method IN ('delete', 'archive', 'anonymize')),
    last_purge_date DATE,
    next_purge_date DATE GENERATED ALWAYS AS (last_purge_date + (retention_years || ' years')::interval) STORED
);

INSERT INTO data_retention_policy VALUES
('general_ledger',       7, 'SOX §802',     'archive',   NULL, NULL),
('journal_entries',      7, 'SOX §802',     'archive',   NULL, NULL),
('audit_workpapers',     7, 'SOX §802',     'archive',   NULL, NULL),
('tax_records',         7, 'IRS',           'archive',   NULL, NULL),
('employee_payroll',    7, 'IRS/FLSA',      'archive',   NULL, NULL),
('bank_statements',     7, 'SOX/Banking',   'archive',   NULL, NULL),
('email_financial',     7, 'SOX §802',      'archive',   NULL, NULL);

-- Immutable archive function
CREATE OR REPLACE FUNCTION archive_for_retention(
    p_source_table TEXT,
    p_cutoff_date DATE
) RETURNS INT AS $$
DECLARE
    v_archived INT;
BEGIN
    EXECUTE format(
        'WITH moved AS (
            DELETE FROM %I
            WHERE created_at < %L
            RETURNING *
        )
        INSERT INTO %I_archive
        SELECT *, NOW() as archived_at, %L as retention_expires_at
        FROM moved',
        p_source_table, p_cutoff_date,
        p_source_table, (p_cutoff_date + INTERVAL '7 years')
    );
    GET DIAGNOSTICS v_archived = ROW_COUNT;
    RETURN v_archived;
END;
$$ LANGUAGE plpgsql;
```

### 3.6 Automated Testing of Data Controls (SOX 404b)

```python
# Automated SOX control testing framework
# Run daily/weekly to ensure controls remain effective

class SOXControlTest:
    """Base class for automated SOX control tests."""

    def __init__(self, control_id: str, description: str, frequency: str):
        self.control_id = control_id
        self.description = description
        self.frequency = frequency
        self.results = []

    def execute(self) -> dict:
        raise NotImplementedError

    def report(self) -> dict:
        return {
            "control_id": self.control_id,
            "description": self.description,
            "test_date": datetime.utcnow().isoformat(),
            "results": self.results,
            "status": "EFFECTIVE" if all(r["pass"] for r in self.results) else "DEFICIENCY"
        }


class SegregationOfDutiesTest(SOXControlTest):
    """Test that no user has conflicting roles."""

    def execute(self) -> dict:
        conflicting_roles = db.execute("""
            SELECT u.username, array_agg(r.role_name) as roles
            FROM user_roles ur
            JOIN users u ON u.id = ur.user_id
            JOIN roles r ON r.id = ur.role_id
            GROUP BY u.username
            HAVING array_agg(r.role_name) && ARRAY['dba', 'developer']
               OR  array_agg(r.role_name) && ARRAY['approver', 'requestor']
        """)
        self.results.append({
            "test": "No conflicting role assignments",
            "pass": len(conflicting_roles) == 0,
            "findings": conflicting_roles
        })
        return self.report()


class ChangeManagementTest(SOXControlTest):
    """Test that all production changes have approved tickets."""

    def execute(self) -> dict:
        unapproved_changes = db.execute("""
            SELECT scl.migration_name, scl.applied_at, scl.applied_by
            FROM schema_change_log scl
            LEFT JOIN change_tickets ct ON ct.ticket_id = scl.change_ticket
            WHERE scl.applied_at > NOW() - INTERVAL '30 days'
              AND (ct.status IS NULL OR ct.status != 'APPROVED')
        """)
        self.results.append({
            "test": "All schema changes have approved change tickets",
            "pass": len(unapproved_changes) == 0,
            "findings": unapproved_changes
        })
        return self.report()
```

---

## 4. GDPR Technical Requirements

### 4.1 Article 25: Data Protection by Design and by Default (DPbD)

Article 25 mandates that data protection be embedded into system design from inception — not bolted on after deployment. For database architects, this means:

**By Design:**
- Pseudonymization and encryption as default architectural choices
- Data minimization built into schemas (collect only what is necessary)
- Purpose limitation enforced at the query layer
- Storage limitation with automated deletion schedules

**By Default:**
- Most restrictive privacy settings as the default configuration
- No personal data processing beyond the specified purpose without explicit consent
- Data not made accessible to indefinite number of persons without intervention

```sql
-- GDPR-by-Design schema example
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    -- Pseudonymized identifier (not directly identifying)
    pseudonym_id VARCHAR(64) NOT NULL UNIQUE,

    -- Consent-gated personal data
    email_encrypted BYTEA,            -- Only decrypted when consent verified
    name_encrypted BYTEA,
    consent_marketing BOOLEAN DEFAULT FALSE,
    consent_analytics BOOLEAN DEFAULT FALSE,
    consent_profiling BOOLEAN DEFAULT FALSE,

    -- Purpose-bound timestamps
    data_collected_at TIMESTAMP NOT NULL DEFAULT NOW(),
    purpose TEXT NOT NULL,             -- Legal basis reference
    retention_until DATE NOT NULL,     -- Automated deletion trigger

    -- Right to erasure support
    erasure_requested_at TIMESTAMP,
    erasure_completed_at TIMESTAMP,
    is_erased BOOLEAN DEFAULT FALSE
);

-- Automated retention enforcement
CREATE OR REPLACE FUNCTION enforce_retention()
RETURNS void AS $$
BEGIN
    UPDATE users
    SET email_encrypted = NULL,
        name_encrypted = NULL,
        is_erased = TRUE,
        erasure_completed_at = NOW()
    WHERE retention_until < CURRENT_DATE
      AND is_erased = FALSE;
END;
$$ LANGUAGE plpgsql;
```

### 4.2 Article 32: Security of Processing

Article 32 requires "appropriate technical and organisational measures" considering:
- State of the art
- Costs of implementation
- Nature, scope, context, purpose of processing
- Risk of varying likelihood and severity for rights/freedoms

**Required Capabilities:**

```
Article 32(1) measures:
(a) Pseudonymisation and encryption of personal data
(b) Ongoing confidentiality, integrity, availability, resilience
(c) Ability to restore availability and access in timely manner
(d) Process for regularly testing, assessing, evaluating effectiveness

Database Implementation:
┌─────────────────────────────────────────────────────┐
│ (a) Encryption                                       │
│     - TDE for at-rest (full database)               │
│     - Column-level for special categories (Art 9)   │
│     - TLS 1.2+ for in-transit                       │
│     - Key rotation automated                         │
│                                                      │
│ (b) CIA + Resilience                                 │
│     - RBAC with least privilege                     │
│     - Checksums for integrity validation            │
│     - HA cluster (primary + standby)                │
│     - Connection rate limiting                       │
│                                                      │
│ (c) Restore Capability                               │
│     - RPO: 1 hour maximum                           │
│     - RTO: 4 hours maximum                          │
│     - Tested quarterly                              │
│     - Encrypted backups                             │
│                                                      │
│ (d) Effectiveness Testing                            │
│     - Penetration testing annually                  │
│     - Vulnerability scanning weekly                 │
│     - Access review quarterly                       │
│     - Incident response drill semi-annually         │
└─────────────────────────────────────────────────────┘
```

### 4.3 Article 35: Data Protection Impact Assessment (DPIA)

A DPIA is mandatory when processing is "likely to result in a high risk" to individuals. For data systems, triggers include:

- Large-scale processing of special categories (health, biometric, genetic)
- Systematic monitoring of publicly accessible areas
- Automated decision-making with legal/significant effects
- Large-scale profiling
- Innovative technology combined with personal data
- Cross-border data transfers at scale

**DPIA Structure for Database Projects:**

```
DPIA Document Template:
1. Description of Processing
   - What data? (categories, volume, sensitivity)
   - How processed? (collection → storage → use → deletion)
   - What technology? (specific DBMS, cloud services, ETL tools)
   - Who accesses? (roles, third parties, processors)

2. Necessity and Proportionality
   - Is this the minimum data needed? (data minimization)
   - Is there a less invasive alternative?
   - What is the lawful basis? (consent, legitimate interest, contract, etc.)
   - Is retention period justified?

3. Risk Assessment
   - Confidentiality risks (unauthorized access, breach)
   - Integrity risks (unauthorized modification, corruption)
   - Availability risks (loss, destruction)
   - Likelihood × Severity matrix for each risk

4. Mitigation Measures
   - Technical controls (encryption, access control, pseudonymization)
   - Organizational controls (training, policies, DPO oversight)
   - Residual risk assessment after mitigations

5. Consultation
   - DPO opinion
   - Supervisory authority consultation (if high residual risk)
```

### 4.4 Data Processing Records (Article 30)

```sql
-- Article 30 Records of Processing Activities (RoPA)
CREATE TABLE processing_activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    activity_name TEXT NOT NULL,
    controller_name TEXT NOT NULL,
    controller_contact TEXT NOT NULL,
    dpo_contact TEXT NOT NULL,

    -- Purpose
    purposes TEXT[] NOT NULL,
    legal_basis TEXT NOT NULL CHECK (legal_basis IN (
        'consent', 'contract', 'legal_obligation',
        'vital_interests', 'public_task', 'legitimate_interest'
    )),
    legitimate_interest_assessment TEXT,  -- If legal_basis = 'legitimate_interest'

    -- Data subjects and categories
    data_subject_categories TEXT[] NOT NULL,
    personal_data_categories TEXT[] NOT NULL,
    special_categories TEXT[],  -- Art 9 data if applicable

    -- Recipients
    recipient_categories TEXT[],
    third_country_transfers TEXT[],
    transfer_safeguards TEXT,  -- SCCs, BCRs, adequacy decision

    -- Retention
    retention_period TEXT NOT NULL,
    retention_criteria TEXT,

    -- Security
    security_measures TEXT[] NOT NULL,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    last_reviewed DATE NOT NULL,
    next_review_date DATE NOT NULL
);
```

### 4.5 Cross-Border Transfer Mechanisms

Post-Schrems II landscape (2020+):

| Mechanism | Status | Use Case |
|-----------|--------|----------|
| Adequacy Decision | Valid for listed countries | Transfers to UK, Japan, Canada, etc. |
| Standard Contractual Clauses (SCCs) | New 2021 version required | Most common mechanism for US transfers |
| Binding Corporate Rules (BCRs) | Requires DPA approval | Intra-group transfers in multinationals |
| Derogations (Art 49) | Limited, specific situations | Explicit consent, contract necessity |
| EU-US Data Privacy Framework | Active (2023), under review | US companies in DPF list |

**Transfer Impact Assessment (TIA):**

Required alongside SCCs when transferring to non-adequate countries. Must assess:
1. Laws of the destination country (surveillance, government access)
2. Supplementary measures needed (encryption where recipient cannot access keys)
3. Effectiveness of chosen safeguards

### 4.6 Right to Erasure Implementation

```sql
-- GDPR Article 17: Right to erasure ("right to be forgotten")
-- Must handle: main data, backups, logs, derived data, third-party propagation

CREATE OR REPLACE FUNCTION gdpr_erase_subject(
    p_subject_id UUID,
    p_request_id UUID,
    p_verified BOOLEAN DEFAULT FALSE
) RETURNS jsonb AS $$
DECLARE
    v_result jsonb := '{}';
    v_table RECORD;
    v_count INT;
BEGIN
    -- Verify request is authenticated
    IF NOT p_verified THEN
        RAISE EXCEPTION 'Erasure request must be identity-verified';
    END IF;

    -- Check for exceptions (Art 17(3))
    -- (freedom of expression, legal obligation, public health, archiving, legal claims)
    IF EXISTS (SELECT 1 FROM legal_holds WHERE subject_id = p_subject_id AND active) THEN
        RETURN jsonb_build_object(
            'status', 'DENIED',
            'reason', 'Active legal hold (Art 17(3)(e))',
            'request_id', p_request_id
        );
    END IF;

    -- Erase from all personal data tables
    FOR v_table IN
        SELECT table_name, erasure_method
        FROM gdpr_data_inventory
        WHERE contains_personal_data = TRUE
    LOOP
        EXECUTE format(
            'UPDATE %I SET personal_data_fields = NULL, is_erased = TRUE
             WHERE subject_id = %L',
            v_table.table_name, p_subject_id
        );
        GET DIAGNOSTICS v_count = ROW_COUNT;
        v_result := v_result || jsonb_build_object(v_table.table_name, v_count);
    END LOOP;

    -- Log erasure completion
    INSERT INTO erasure_log (request_id, subject_id, tables_affected, completed_at)
    VALUES (p_request_id, p_subject_id, v_result, NOW());

    -- Queue third-party erasure notifications (Art 17(2))
    INSERT INTO erasure_propagation_queue (subject_id, recipients, queued_at)
    SELECT p_subject_id, array_agg(processor_name), NOW()
    FROM data_processors
    WHERE processes_data_for_subject = TRUE;

    RETURN jsonb_build_object(
        'status', 'COMPLETED',
        'tables_erased', v_result,
        'third_party_notifications', 'QUEUED'
    );
END;
$$ LANGUAGE plpgsql;
```

### 4.7 Consent Management Data Model

```sql
-- Granular consent tracking per GDPR requirements
CREATE TABLE consent_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_id UUID NOT NULL REFERENCES users(id),

    -- Consent specifics
    purpose TEXT NOT NULL,
    processing_activity_id UUID REFERENCES processing_activities(id),
    legal_basis TEXT NOT NULL DEFAULT 'consent',

    -- Consent state
    granted BOOLEAN NOT NULL,
    granted_at TIMESTAMP,
    withdrawn_at TIMESTAMP,

    -- Proof of consent (Art 7(1))
    consent_mechanism TEXT NOT NULL,       -- 'web_form', 'api', 'paper', 'verbal'
    consent_text_version VARCHAR(20) NOT NULL,  -- Which version of text was shown
    consent_language VARCHAR(5) NOT NULL,
    ip_address INET,
    user_agent TEXT,

    -- Freely given check (Art 7(4))
    -- Consent must not be bundled with service access
    is_conditional BOOLEAN DEFAULT FALSE,  -- If TRUE, may be invalid

    -- Audit trail
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Consent must be as easy to withdraw as to give (Art 7(3))
CREATE INDEX idx_consent_active ON consent_records(subject_id, purpose)
    WHERE granted = TRUE AND withdrawn_at IS NULL;
```

---

## 5. NIST Frameworks

### 5.1 NIST 800-53: Security and Privacy Controls for Federal Systems

NIST SP 800-53 Rev. 5 defines the control catalog for federal information systems (mandated by FISMA) and increasingly adopted as a baseline by private sector organizations. It contains 20 control families with over 1,000 individual controls.

**Control Families Most Relevant to Data Systems:**

| Family | ID | Name | Database Relevance |
|--------|-----|------|-------------------|
| Access Control | AC | Manage who/what can access | RBAC, row-level security, connection controls |
| Audit & Accountability | AU | Track and review activity | pgAudit, query logging, tamper-evident logs |
| Contingency Planning | CP | Ensure availability | Backup, DR, HA, tested recovery |
| Identification & Auth | IA | Verify identity | Certificate auth, MFA for DBAs, SCRAM-SHA-256 |
| System & Comms Protection | SC | Protect data flows | TLS, encryption at rest, network segmentation |
| System & Info Integrity | SI | Detect/prevent corruption | Input validation, integrity checks, patching |

**Key Controls for Database Systems:**

```
AC-2: Account Management
- Automated account provisioning/deprovisioning
- Account review every 90 days
- Disable inactive accounts after 60 days (AC-2(3))
- Automated audit of role assignments

AC-3: Access Enforcement
- RBAC implementation in DBMS
- Row-level security for multi-tenant
- Column-level access restrictions
- Dynamic access based on attributes (ABAC)

AC-6: Least Privilege
- No standing admin access (just-in-time provisioning)
- Privileged access limited to specific functions
- Audit all privilege escalation

AU-2: Event Logging
- Successful/failed authentication
- Privilege escalation
- Data access (SELECT on sensitive tables)
- Schema modifications (DDL)
- Configuration changes
- Audit log access itself

AU-6: Audit Record Review
- Automated analysis of audit records
- Correlation with other event sources
- Anomaly detection (unusual query patterns)

AU-9: Protection of Audit Information
- Append-only audit stores
- Separate storage from audited systems
- Integrity verification (hash chains)
- Access restricted to auditors only

SC-8: Transmission Confidentiality and Integrity
- TLS 1.2+ for all database connections
- Certificate pinning for service-to-service
- mTLS for high-sensitivity environments

SC-28: Protection of Information at Rest
- Encryption of databases storing CUI/PII
- Key management aligned with SP 800-57
- Verified encryption effectiveness
```

### 5.2 NIST 800-171: Protecting Controlled Unclassified Information (CUI)

NIST 800-171 Rev. 2 (and the upcoming Rev. 3) defines requirements for non-federal organizations handling CUI — commonly encountered in defense contractors, research institutions, and government service providers. It is the basis for CMMC (Cybersecurity Maturity Model Certification).

**110 Security Requirements across 14 Families:**

For database systems, the critical requirements are:

```
3.1 ACCESS CONTROL
3.1.1  Limit system access to authorized users
3.1.2  Limit system access to authorized functions
3.1.3  Control flow of CUI per approved authorizations
3.1.5  Least privilege
3.1.7  Prevent non-privileged users from executing privileged functions

3.3 AUDIT AND ACCOUNTABILITY
3.3.1  Create and retain system audit logs
3.3.2  Ensure actions of individual users can be uniquely traced
3.3.5  Correlate audit records for investigation
3.3.8  Protect audit information from unauthorized access/modification

3.5 IDENTIFICATION AND AUTHENTICATION
3.5.1  Identify information system users and processes
3.5.2  Authenticate users/processes/devices
3.5.3  Use multifactor authentication for network access
3.5.7  Enforce minimum password complexity

3.13 SYSTEM AND COMMUNICATIONS PROTECTION
3.13.1  Monitor/control communications at system boundaries
3.13.8  Implement cryptographic mechanisms for CUI in transit
3.13.11 Employ FIPS-validated cryptography (AES-256, SHA-256+)

3.14 SYSTEM AND INFORMATION INTEGRITY
3.14.1  Identify, report, and correct information system flaws (patching)
3.14.2  Malicious code protection
3.14.6  Monitor communications to detect attacks
3.14.7  Identify unauthorized use of the system
```

### 5.3 NIST Cybersecurity Framework (CSF) 2.0

Released February 2024, CSF 2.0 adds a sixth function (Govern) and expands applicability beyond critical infrastructure.

**Six Functions Applied to Data Systems:**

```
┌─────────────────────────────────────────────────────────────────┐
│                         GOVERN (GV)                              │
│  Organizational context, risk management strategy, roles        │
│  GV.RM: Risk management strategy for data assets                │
│  GV.SC: Supply chain risk for database vendors/cloud providers  │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│IDENTIFY │ │ PROTECT │ │ DETECT  │ │ RESPOND │ │ RECOVER │
│         │ │         │ │         │ │         │ │         │
│Asset    │ │Access   │ │Anomaly  │ │Incident │ │Recovery │
│inventory│ │control  │ │detection│ │response │ │planning │
│Data flow│ │Encrypt  │ │Monitor  │ │Contain  │ │Backup   │
│mapping  │ │Training │ │Alert    │ │Eradicate│ │restore  │
│Risk     │ │Config   │ │Audit    │ │Communi- │ │Lessons  │
│assess   │ │manage   │ │review   │ │cate     │ │learned  │
└─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘
```

**CSF 2.0 Profiles for Database Systems:**

A "profile" is the organization's selection of outcomes aligned to risk tolerance. For a database storing sensitive financial data:

| Category | Target Profile | Current State | Gap |
|----------|---------------|---------------|-----|
| ID.AM (Asset Mgmt) | All databases inventoried, classified | 80% inventoried | Discover shadow DBs |
| PR.AA (Access Auth) | Zero-trust, JIT access | Role-based, standing access | Implement PIM |
| PR.DS (Data Security) | Encrypted at rest + transit | Transit only | Add TDE/column encryption |
| DE.CM (Monitoring) | Real-time anomaly detection | Daily log review | Deploy UEBA |
| RS.AN (Analysis) | Automated triage + correlation | Manual SIEM review | Automate playbooks |
| RC.RP (Recovery) | RPO 1h, RTO 4h, tested quarterly | RPO 24h, RTO unknown | HA + tested DR |

### 5.4 NIST 800-160: Systems Security Engineering

NIST 800-160 provides guidance on building trustworthy secure systems. For data engineering, it introduces the concept of "security-relevant design principles" that should be embedded in database architecture:

```
Key Principles from 800-160 for Data Systems:

1. Least Privilege
   - Service accounts: one per application, minimal grants
   - Human accounts: time-bound privilege escalation
   - Application queries: prepared statements, parameterized

2. Modularity & Layering
   - Separate data stores by sensitivity classification
   - Enforce boundaries between processing tiers
   - Independent failure domains (blast radius reduction)

3. Reduced Complexity
   - Fewer components = fewer attack surfaces
   - Avoid multi-purpose databases (PCI + HIPAA + general in one instance)
   - Simple, auditable access paths

4. Secure Defaults
   - New database instances: deny-all by default
   - Default encryption on, default logging on
   - No public accessibility unless explicitly required

5. Fail Secure
   - Connection failure → deny access (not fail-open)
   - Decryption failure → do not return plaintext or error detail
   - Authorization check failure → default deny
```

### 5.5 Control Implementation Mapping (AC, AU, CP, IA, SC, SI)

```
NIST 800-53 → PostgreSQL Control Mapping:

AC-2 (Account Management):
  → CREATE/ALTER/DROP ROLE with documented process
  → pg_stat_activity monitoring for active sessions
  → Automated scripts to disable accounts after inactivity

AC-3 (Access Enforcement):
  → GRANT/REVOKE at schema/table/column level
  → Row Level Security (RLS) policies
  → pgcrypto for data-level enforcement

AU-2/AU-3 (Audit Events/Content):
  → pgAudit extension (object-level audit)
  → log_statement = 'ddl' minimum, 'all' for sensitive
  → Log: who, what, when, where, outcome

AU-9 (Audit Protection):
  → Ship logs to immutable external store (WORM)
  → Separate log database with restricted access
  → Hash chain for log integrity

CP-9 (Information System Backup):
  → pg_basebackup for physical backups
  → WAL archiving for PITR (Point-In-Time Recovery)
  → Encrypted backup storage
  → Quarterly restore testing

IA-2 (Identification and Authentication):
  → SCRAM-SHA-256 (password)
  → Certificate authentication (mTLS)
  → LDAP/SAML integration for centralized IdP
  → MFA via application layer for DBA access

SC-8 (Transmission Confidentiality):
  → ssl = on in postgresql.conf
  → ssl_min_protocol_version = 'TLSv1.2'
  → hostssl entries only in pg_hba.conf

SC-28 (Protection at Rest):
  → pgcrypto for column-level
  → Full-disk encryption (LUKS/BitLocker)
  → Cloud-managed encryption (AWS KMS, Azure Key Vault)

SI-2 (Flaw Remediation):
  → PostgreSQL minor version updates within 30 days of release
  → Major version upgrades within supported lifecycle
  → Patch management tracked in CMDB
```

---

## 6. Industry-Specific Regulations

### 6.1 GLBA (Gramm-Leach-Bliley Act) — Financial Services

GLBA Safeguards Rule (16 CFR Part 314, updated 2023) requires financial institutions to develop, implement, and maintain a comprehensive information security program.

**Database Requirements:**

```
GLBA Safeguards Rule — Database Controls:

§314.4(c) Risk Assessment:
- Inventory all databases containing NPI (Nonpublic Personal Information)
- Assess threats: insider, external, accidental exposure
- Document risk levels and mitigations

§314.4(d)(1) Access Controls:
- Technical access controls based on least privilege
- Review access rights every 6 months
- Implement MFA for accessing NPI systems

§314.4(d)(2) Data Inventory:
- Know what NPI you have, where it's stored, how it flows
- Periodic audits of data stores for unexpected NPI

§314.4(d)(3) Encryption:
- Encrypt NPI in transit and at rest
- Or: effective alternative compensating controls

§314.4(d)(7) Disposal:
- Secure disposal of NPI within 2 years of last business use
  (unless retention required by law)

§314.4(e) Monitoring:
- Continuous monitoring or annual penetration testing
- Vulnerability assessments every 6 months
```

### 6.2 FERPA (Family Educational Rights and Privacy Act) — Education

FERPA protects student education records. While it predates modern databases, its requirements apply directly to student information systems (SIS), learning management systems (LMS), and analytics platforms.

**Key Database Implications:**

```
FERPA-Protected Education Records:
- Grades and transcripts
- Student financial information
- Disciplinary records
- Enrollment data
- Class schedules
- Student ID numbers
- Parent/guardian information (for minors)

NOT Education Records:
- De-identified aggregate data
- Directory information (if notice given and opt-out available)
- Records kept in sole possession of maker (private notes)

Database Controls for FERPA:
1. Directory information flagging per student opt-out preference
2. Role-based access: faculty see their students only
3. Legitimate educational interest documentation
4. Audit trail of all access to student records
5. Data sharing agreements with third-party EdTech vendors
6. Retention schedules (vary by record type, typically 5-7 years post-enrollment)
```

### 6.3 FedRAMP (Federal Risk and Authorization Management Program) — Government Cloud

FedRAMP provides a standardized approach to security assessment for cloud products serving federal agencies. It maps directly to NIST 800-53 controls but adds cloud-specific implementation guidance.

**Impact Levels:**

| Level | Controls | Data Types | Database Example |
|-------|----------|------------|-----------------|
| Low | 125 controls | Non-sensitive public data | Open data portals |
| Moderate | 325 controls | Most federal data, PII, PHI | Agency databases, HR systems |
| High | 421 controls | National security, law enforcement | Classified-adjacent systems |

**Database-Specific FedRAMP Requirements:**

```
FedRAMP Moderate — Database Controls:

CA-7: Continuous Monitoring
- Automated vulnerability scanning weekly
- Configuration compliance checking daily
- Real-time alert on unauthorized changes

CM-2: Baseline Configuration
- Document approved database configuration
- Detect deviation from baseline (drift)
- Version control all configuration files

CM-6: Configuration Settings
- CIS Benchmark for PostgreSQL/MySQL/etc.
- Disable unused features and default accounts
- Remove sample databases and test data
- Restrict listener to authorized interfaces only

RA-5: Vulnerability Scanning
- Authenticated database vulnerability scans
- CVE tracking and remediation within 30 days (high), 90 days (moderate)
- False positive documentation

SA-10: Developer Configuration Management
- Source-controlled schema migrations
- Code review for stored procedures
- Separation between dev/test/production

SI-4: Information System Monitoring
- Database Activity Monitoring (DAM)
- Anomaly detection on query patterns
- Alert on bulk data extraction
- Alert on schema modification outside change windows
```

### 6.4 CCPA/CPRA (California Consumer Privacy Act / California Privacy Rights Act)

CPRA (effective January 2023) amended CCPA with stronger consumer rights and created the California Privacy Protection Agency (CPPA). Technical requirements for databases:

```sql
-- CCPA/CPRA: Consumer Rights Implementation

-- Right to Know (§1798.110): What personal information is collected
CREATE VIEW consumer_data_inventory AS
SELECT
    category,
    source,
    business_purpose,
    third_party_shared_with,
    retention_period
FROM data_categories
WHERE applies_to_consumers = TRUE;

-- Right to Delete (§1798.105)
-- Similar to GDPR erasure but with different exceptions
-- Exceptions: complete transaction, security, legal obligation,
-- internal use compatible with consumer expectations

-- Right to Opt-Out of Sale/Sharing (§1798.120)
CREATE TABLE consumer_preferences (
    consumer_id UUID PRIMARY KEY,
    opt_out_sale BOOLEAN DEFAULT FALSE,
    opt_out_sharing BOOLEAN DEFAULT FALSE,
    opt_out_automated_decision BOOLEAN DEFAULT FALSE,
    limit_sensitive_use BOOLEAN DEFAULT FALSE,
    preference_set_at TIMESTAMP DEFAULT NOW(),
    -- Must honor GPC (Global Privacy Control) signal
    gpc_detected BOOLEAN DEFAULT FALSE
);

-- Right to Correct (§1798.106) — new in CPRA
-- Must allow consumers to correct inaccurate personal information

-- Sensitive Personal Information (§1798.121)
-- Separate handling for: SSN, financial accounts, geolocation,
-- racial/ethnic origin, religious beliefs, health data, sex life,
-- biometric data, private communications, genetic data
```

### 6.5 NIS2 Directive (EU Network and Information Security)

NIS2 (Directive 2022/2555, applicable October 2024) expands cybersecurity requirements across EU critical infrastructure sectors, including digital infrastructure, healthcare, energy, transport, banking, and digital service providers.

**Database Impact:**

```
NIS2 Article 21 — Cybersecurity Risk Management Measures:

(a) Risk analysis and information system security policies
    → Database risk assessments, security architecture reviews

(b) Incident handling
    → Database breach detection, 24-hour initial notification,
      72-hour detailed report to national CSIRT

(c) Business continuity and crisis management
    → Database HA, DR, backup, tested failover

(d) Supply chain security
    → Database vendor assessment, patch management,
      third-party connector security

(e) Security in network and information systems acquisition
    → Secure database deployment pipelines, hardening standards

(f) Cybersecurity risk assessment effectiveness
    → Regular database penetration testing, vulnerability management

(g) Cybersecurity hygiene and training
    → DBA security training, secure coding for stored procedures

(h) Cryptographic policies
    → Database encryption standards, key management procedures

(i) Human resources security
    → DBA background checks, separation of duties, offboarding

(j) Multi-factor authentication
    → MFA for all administrative database access

Penalties: Up to EUR 10M or 2% of global turnover (essential entities)
```

### 6.6 DORA (Digital Operational Resilience Act) — EU Financial Sector

DORA (Regulation 2022/2554, applicable January 2025) harmonizes ICT risk management for EU financial entities. For database systems in financial services:

```
DORA Requirements for Data Systems:

Chapter II: ICT Risk Management
- Article 6: ICT risk management framework
  → Database in asset inventory with criticality classification
  → Risk assessment per database (threats, vulnerabilities, impact)
  
- Article 7: ICT systems, protocols, tools
  → Database version management, lifecycle policy
  → Documented architecture and data flows
  
- Article 9: Detection
  → Database activity monitoring
  → Anomaly detection on data access patterns
  → Multiple layers of detection (network, application, database)

- Article 11: Response and recovery
  → Database incident response playbooks
  → RPO/RTO per database criticality
  → Annual testing of backup/restore

- Article 12: Backup policies
  → Geographically separated backups
  → Encrypted backup storage
  → Regular restore validation

Chapter III: ICT-Related Incident Management
- 4-hour initial classification for major incidents
- 24-hour initial report to competent authority
- Intermediate report within 72 hours
- Final report within 1 month

Chapter V: ICT Third-Party Risk
- Article 28: Register of ICT third-party service providers
  → Cloud database providers, SaaS analytics, etc.
  → Concentration risk assessment
  → Exit strategies for critical database services
```

### 6.7 State Data Breach Notification Laws

All 50 US states plus DC, Guam, Puerto Rico, and US Virgin Islands have breach notification laws. Key variations affecting database incident response:

| State | Notification Timeline | Encrypted Data Exemption | Private Right of Action |
|-------|----------------------|-------------------------|------------------------|
| California | 72 hours (AG), without unreasonable delay (individuals) | Yes, if key not compromised | Yes (CCPA) |
| New York | Without unreasonable delay, notify AG within 72h if >500 | Yes | Limited |
| Colorado | 30 days | Yes | No |
| Virginia | 60 days | Yes | No |
| Texas | 60 days | Yes | Yes (TDPSA) |
| Florida | 30 days (individuals), 30 days (AG if >500) | Yes | No |
| Illinois | Without unreasonable delay | Yes | Yes (BIPA for biometric) |

---

## 7. Control Implementation

### 7.1 Framework-to-Database Control Mapping

```
┌──────────────────────────────────────────────────────────────────────────┐
│ Framework Requirement    → Database Control Implementation               │
├──────────────────────────────────────────────────────────────────────────┤
│ Access Control (all)     → PostgreSQL RBAC + RLS + column privileges     │
│ Encryption at rest       → TDE (pg_tde) or column-level (pgcrypto)      │
│ Encryption in transit    → TLS 1.2+ with cert auth                      │
│ Audit logging            → pgAudit extension + external SIEM            │
│ Backup/Recovery          → pg_basebackup + WAL archiving + PITR         │
│ Integrity                → Checksums (data_checksums=on) + hash chains  │
│ Authentication           → SCRAM-SHA-256 + LDAP/cert + MFA at app layer │
│ Network segmentation     → pg_hba.conf + firewall rules + VPC/VLAN      │
│ Change management        → Schema migrations in VCS + approval workflow  │
│ Vulnerability mgmt       → CVE tracking + patching within SLA           │
│ Data retention           → Partition-based lifecycle + automated purge   │
│ Incident detection       → Anomaly queries + real-time alerting          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 7.2 PostgreSQL RBAC Implementation (Multi-Framework)

```sql
-- Unified RBAC model satisfying PCI-DSS Req 7, HIPAA §164.312(a),
-- SOX separation of duties, NIST AC-2/AC-3/AC-6

-- 1. Application roles (no login, purely for permission grouping)
CREATE ROLE app_readonly;
CREATE ROLE app_readwrite;
CREATE ROLE app_admin;
CREATE ROLE dba_operations;
CREATE ROLE security_auditor;

-- 2. Schema-level segregation by sensitivity
CREATE SCHEMA pci_data;         -- PCI-DSS scoped
CREATE SCHEMA clinical_data;    -- HIPAA scoped
CREATE SCHEMA financial_data;   -- SOX scoped
CREATE SCHEMA general_data;     -- Standard controls

-- 3. Granular grants
-- PCI schema: only payment service can access
GRANT USAGE ON SCHEMA pci_data TO app_readwrite;
GRANT SELECT, INSERT ON ALL TABLES IN SCHEMA pci_data TO app_readwrite;
REVOKE ALL ON SCHEMA pci_data FROM PUBLIC;

-- Clinical schema: clinician roles only
GRANT USAGE ON SCHEMA clinical_data TO clinician;
GRANT SELECT ON ALL TABLES IN SCHEMA clinical_data TO clinician;

-- Financial schema: finance team + SOX-restricted
GRANT USAGE ON SCHEMA financial_data TO finance_analyst;
GRANT SELECT ON ALL TABLES IN SCHEMA financial_data TO finance_analyst;
-- finance_analyst CANNOT modify data directly (SOX SoD)

-- Auditor: read-only across all schemas, including audit logs
GRANT USAGE ON SCHEMA pci_data, clinical_data, financial_data, general_data
    TO security_auditor;
GRANT SELECT ON ALL TABLES IN SCHEMA pci_data TO security_auditor;
GRANT SELECT ON ALL TABLES IN SCHEMA clinical_data TO security_auditor;
GRANT SELECT ON ALL TABLES IN SCHEMA financial_data TO security_auditor;
-- Auditor CANNOT modify anything

-- 4. Row-Level Security for multi-tenant isolation
ALTER TABLE clinical_data.patient_records ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON clinical_data.patient_records
    USING (tenant_id = current_setting('app.tenant_id')::int);

-- 5. Column-level restrictions
-- Hide SSN column from all roles except specific functions
REVOKE SELECT (ssn_encrypted) ON clinical_data.patient_records FROM PUBLIC;
GRANT SELECT (ssn_encrypted) ON clinical_data.patient_records TO identity_verification;
```

### 7.3 Cloud Shared Responsibility Model

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    SHARED RESPONSIBILITY MODEL                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  CUSTOMER RESPONSIBILITY ("Security IN the Cloud")                      │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ • Data classification and encryption decisions                    │  │
│  │ • Identity and access management (IAM policies)                   │  │
│  │ • Database configuration (pg_hba.conf equivalent)                 │  │
│  │ • Network configuration (security groups, NACLs)                  │  │
│  │ • Application-level security (SQL injection prevention)           │  │
│  │ • Audit log configuration and review                              │  │
│  │ • Backup configuration and restore testing                        │  │
│  │ • Patching (minor versions for self-managed, timely upgrades)     │  │
│  │ • Compliance evidence collection and documentation                │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  SHARED RESPONSIBILITY                                                  │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ • Patch management (managed services: provider applies patches)   │  │
│  │ • Encryption key management (provider infra, customer key policy) │  │
│  │ • Network security (provider VPC, customer security groups)       │  │
│  │ • Monitoring (provider health checks, customer app monitoring)    │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  PROVIDER RESPONSIBILITY ("Security OF the Cloud")                      │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ • Physical security of data centers                               │  │
│  │ • Hardware maintenance and replacement                            │  │
│  │ • Hypervisor security and isolation                               │  │
│  │ • Network infrastructure (backbone, DDoS mitigation)              │  │
│  │ • Storage media destruction/decommissioning                       │  │
│  │ • Compliance certifications (SOC 2, ISO 27001, FedRAMP)           │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Control Inheritance:**

When using a FedRAMP-authorized cloud database (e.g., AWS RDS), certain controls are "inherited" from the provider's authorization:
- PE (Physical and Environmental Protection) — fully inherited
- SC-8 for provider-managed TLS termination — partially inherited
- CP-6 (Alternate Storage Site) — inherited if multi-AZ enabled

But you must still document which controls are inherited vs. customer-implemented in your System Security Plan (SSP).

### 7.4 Compensating Controls Documentation

When a prescribed control cannot be implemented as specified, a compensating control must:
1. Meet the intent and rigor of the original requirement
2. Provide a similar level of defense
3. Be above and beyond other requirements (not already counted)
4. Be commensurate with the additional risk

```
Compensating Control Documentation Template:
═══════════════════════════════════════════════════════════
Requirement: PCI-DSS 3.4 — Render PAN unreadable in storage
Original Control: Encryption of PAN at rest

Constraint: Legacy billing system cannot support encryption
           without complete rewrite (18-month timeline)

Compensating Control:
1. Network isolation: billing DB on dedicated VLAN with
   single-host firewall rules (only billing app server)
2. Enhanced monitoring: all queries logged, real-time
   alerting on any non-application source connection
3. Access restriction: database credentials in HSM,
   rotated weekly, zero human access to credentials
4. Additional control: field-level tokenization in
   reporting layer (tokens never reach billing DB)

Risk Assessment:
- Residual risk: MEDIUM (reduced from HIGH)
- Compensating controls collectively exceed single
  encryption control in defense depth
- Timeline: full encryption by Q3 2025 (project approved)

Review: Annually or upon significant change
═══════════════════════════════════════════════════════════
```

---

## 8. Audit Preparation

### 8.1 Evidence Collection Automation

Manual evidence collection is error-prone, expensive, and unsustainable for continuous compliance. Automating evidence gathering reduces audit fatigue and ensures consistency.

```bash
#!/usr/bin/env bash
# sox_evidence_collector.sh — Automated SOX control evidence collection
# Run monthly, output to compliance evidence repository

set -euo pipefail

EVIDENCE_DIR="/var/compliance/evidence/$(date +%Y-%m)"
DB_HOST="financial-db.internal"
DB_NAME="finance_prod"
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)

mkdir -p "${EVIDENCE_DIR}"/{access-control,change-management,audit-logs,backups}

# --- ACCESS CONTROL EVIDENCE ---

# AC-1: Current role assignments
psql -h "$DB_HOST" -d "$DB_NAME" -c "
    SELECT r.rolname, r.rolsuper, r.rolcreaterole, r.rolcreatedb,
           r.rolcanlogin, r.rolvaliduntil,
           ARRAY(SELECT b.rolname FROM pg_catalog.pg_auth_members m
                 JOIN pg_catalog.pg_roles b ON m.roleid = b.oid
                 WHERE m.member = r.oid) AS member_of
    FROM pg_catalog.pg_roles r
    WHERE r.rolname NOT LIKE 'pg_%'
    ORDER BY r.rolname;
" --csv > "${EVIDENCE_DIR}/access-control/role_assignments_${TIMESTAMP}.csv"

# AC-2: Inactive accounts (no login in 90 days)
psql -h "$DB_HOST" -d "$DB_NAME" -c "
    SELECT usename, last_login, created_at,
           CASE WHEN last_login < NOW() - INTERVAL '90 days'
                THEN 'FINDING: Inactive > 90 days'
                ELSE 'OK'
           END AS status
    FROM user_activity_log
    ORDER BY last_login;
" --csv > "${EVIDENCE_DIR}/access-control/inactive_accounts_${TIMESTAMP}.csv"

# AC-3: Privilege escalation events
psql -h "$DB_HOST" -d "$DB_NAME" -c "
    SELECT * FROM audit_log
    WHERE event_type IN ('GRANT', 'REVOKE', 'ALTER ROLE')
      AND event_time > NOW() - INTERVAL '30 days'
    ORDER BY event_time DESC;
" --csv > "${EVIDENCE_DIR}/access-control/privilege_changes_${TIMESTAMP}.csv"

# --- CHANGE MANAGEMENT EVIDENCE ---

# CM-1: Schema changes with approval status
psql -h "$DB_HOST" -d "$DB_NAME" -c "
    SELECT scl.migration_name, scl.applied_at, scl.applied_by,
           ct.ticket_id, ct.approver, ct.approved_at, ct.status
    FROM schema_change_log scl
    LEFT JOIN change_tickets ct ON ct.ticket_id = scl.change_ticket
    WHERE scl.applied_at > NOW() - INTERVAL '30 days'
    ORDER BY scl.applied_at DESC;
" --csv > "${EVIDENCE_DIR}/change-management/schema_changes_${TIMESTAMP}.csv"

# --- BACKUP EVIDENCE ---

# CP-1: Backup completion status
psql -h "$DB_HOST" -d "$DB_NAME" -c "
    SELECT backup_id, backup_type, started_at, completed_at,
           size_bytes, encrypted, verified, storage_location
    FROM backup_history
    WHERE started_at > NOW() - INTERVAL '30 days'
    ORDER BY started_at DESC;
" --csv > "${EVIDENCE_DIR}/backups/backup_history_${TIMESTAMP}.csv"

# --- GENERATE EVIDENCE MANIFEST ---
find "${EVIDENCE_DIR}" -type f -exec sha256sum {} \; > "${EVIDENCE_DIR}/manifest_${TIMESTAMP}.sha256"

echo "Evidence collection complete: ${EVIDENCE_DIR}"
echo "Files collected: $(find "${EVIDENCE_DIR}" -type f | wc -l)"
echo "Manifest: ${EVIDENCE_DIR}/manifest_${TIMESTAMP}.sha256"
```

```python
# hipaa_evidence_collector.py — HIPAA technical safeguard evidence

import subprocess
import json
from datetime import datetime, timezone
from pathlib import Path

class HIPAAEvidenceCollector:
    """Collect evidence for HIPAA technical safeguard controls."""

    def __init__(self, db_config: dict, evidence_path: str):
        self.db = db_config
        self.evidence_path = Path(evidence_path) / datetime.now(timezone.utc).strftime("%Y-%m")
        self.evidence_path.mkdir(parents=True, exist_ok=True)
        self.findings = []

    def collect_access_controls(self) -> dict:
        """§164.312(a) — Access Control evidence."""
        evidence = {}

        # Unique user identification
        result = self._query("""
            SELECT rolname, rolcanlogin, rolvaliduntil
            FROM pg_roles WHERE rolcanlogin = TRUE
            AND rolname NOT LIKE 'pg_%'
        """)
        evidence["unique_users"] = result

        # Check for shared accounts (finding)
        shared = [r for r in result if "shared" in r["rolname"].lower() or "generic" in r["rolname"].lower()]
        if shared:
            self.findings.append({
                "control": "§164.312(a)(2)(i)",
                "severity": "HIGH",
                "finding": f"Shared/generic accounts detected: {[s['rolname'] for s in shared]}",
                "recommendation": "Replace with individual named accounts"
            })

        # Automatic logoff settings
        evidence["session_timeout"] = self._query("""
            SELECT name, setting, unit
            FROM pg_settings
            WHERE name IN ('idle_in_transaction_session_timeout', 'statement_timeout')
        """)

        return evidence

    def collect_audit_controls(self) -> dict:
        """§164.312(b) — Audit Controls evidence."""
        evidence = {}

        # pgAudit configuration
        evidence["audit_config"] = self._query("""
            SELECT name, setting
            FROM pg_settings
            WHERE name LIKE 'pgaudit%'
        """)

        # Audit log retention verification
        evidence["oldest_audit_record"] = self._query("""
            SELECT MIN(event_time) as oldest_record,
                   COUNT(*) as total_records
            FROM ephi_audit_log
        """)

        return evidence

    def collect_encryption_evidence(self) -> dict:
        """§164.312(a)(2)(iv) and §164.312(e)(2) — Encryption."""
        evidence = {}

        # TLS configuration
        evidence["ssl_config"] = self._query("""
            SELECT name, setting FROM pg_settings
            WHERE name IN ('ssl', 'ssl_min_protocol_version', 'ssl_ciphers')
        """)

        # Active connections using TLS
        evidence["encrypted_connections"] = self._query("""
            SELECT ssl, COUNT(*) as connection_count
            FROM pg_stat_ssl
            JOIN pg_stat_activity USING (pid)
            GROUP BY ssl
        """)

        # Check for unencrypted connections (finding)
        unencrypted = [r for r in evidence["encrypted_connections"] if not r.get("ssl")]
        if unencrypted and unencrypted[0]["connection_count"] > 0:
            self.findings.append({
                "control": "§164.312(e)(2)(ii)",
                "severity": "CRITICAL",
                "finding": f"Unencrypted connections detected: {unencrypted[0]['connection_count']}",
                "recommendation": "Enforce hostssl in pg_hba.conf, reject hostnossl"
            })

        return evidence

    def generate_report(self) -> dict:
        """Generate compliance evidence report."""
        return {
            "report_date": datetime.now(timezone.utc).isoformat(),
            "framework": "HIPAA",
            "findings": self.findings,
            "finding_count": {
                "CRITICAL": len([f for f in self.findings if f["severity"] == "CRITICAL"]),
                "HIGH": len([f for f in self.findings if f["severity"] == "HIGH"]),
                "MEDIUM": len([f for f in self.findings if f["severity"] == "MEDIUM"]),
                "LOW": len([f for f in self.findings if f["severity"] == "LOW"]),
            },
            "overall_status": "FAIL" if any(f["severity"] in ("CRITICAL", "HIGH") for f in self.findings) else "PASS"
        }

    def _query(self, sql: str) -> list:
        """Execute query and return results as list of dicts."""
        # Implementation depends on DB driver (psycopg, asyncpg, etc.)
        pass
```

### 8.2 Common Findings in Database Audits

```
TOP 20 DATABASE AUDIT FINDINGS (by frequency):

CRITICAL:
1. Shared/generic database accounts (violates every framework)
2. Unencrypted sensitive data at rest (PCI 3.4, HIPAA §164.312)
3. Missing or disabled audit logging (SOX, HIPAA, PCI 10)
4. Default credentials on database instances
5. Direct database access from internet-facing networks

HIGH:
6. Excessive privileges (DBA rights to service accounts)
7. No network segmentation between environments
8. Incomplete backup testing (untested restores)
9. Missing TLS enforcement (cleartext database connections)
10. No access review process (stale accounts persist)

MEDIUM:
11. Inconsistent patching (months behind on security patches)
12. No change management for schema modifications
13. Missing column-level encryption for highest-sensitivity fields
14. Audit logs stored on same system being audited
15. No automated retention enforcement (data kept indefinitely)

LOW:
16. Connection pool credentials in plaintext config files
17. Verbose error messages exposing schema information
18. No query timeout configured (DoS risk)
19. Missing index on audit log tables (slow review)
20. Development data containing production PII
```

### 8.3 Pre-Audit Self-Assessment Checklists

```
PCI-DSS v4.0 DATABASE SELF-ASSESSMENT:
═══════════════════════════════════════

[ ] SCOPE (Req 12.5.2)
    [ ] All databases storing/processing/transmitting CHD identified
    [ ] Data flow diagrams current and accurate
    [ ] Segmentation validated (penetration test)
    [ ] Connected-to systems documented

[ ] STORED DATA (Req 3)
    [ ] No prohibited SAD stored post-authorization
    [ ] PAN encrypted or tokenized (AES-256 minimum)
    [ ] Key management documented and followed
    [ ] Cryptographic key inventory current
    [ ] Key rotation within cryptoperiod
    [ ] Data retention policy enforced (automated purge)

[ ] ACCESS CONTROL (Req 7/8)
    [ ] All accounts uniquely assigned
    [ ] Role-based access implemented
    [ ] Quarterly access reviews documented
    [ ] MFA for all administrative access
    [ ] Service accounts have minimum necessary privileges
    [ ] No shared/generic accounts

[ ] LOGGING (Req 10)
    [ ] All access to CHD logged
    [ ] All admin actions logged
    [ ] Logs include: who, what, when, where, success/fail
    [ ] Log integrity protected (tamper-evident)
    [ ] Logs retained 12 months (3 months immediately available)
    [ ] Daily log review process (automated alerts + human review)
    [ ] Time synchronization (NTP) configured

[ ] VULNERABILITY MANAGEMENT (Req 6/11)
    [ ] Database patched within 30 days of critical CVE
    [ ] Internal vulnerability scans quarterly (passing)
    [ ] No high/critical unresolved vulnerabilities
    [ ] Segmentation testing annually (6 months if service provider)

[ ] CONFIGURATION (Req 2)
    [ ] Hardening standard documented and applied
    [ ] Default passwords changed
    [ ] Unnecessary services/features disabled
    [ ] System components inventory accurate
```

### 8.4 Documentation Requirements

Compliance documentation follows a four-tier hierarchy:

```
Documentation Hierarchy:
════════════════════════

TIER 1: POLICIES (Board/Executive level)
- Information Security Policy
- Data Classification Policy
- Acceptable Use Policy
- Incident Response Policy
- Business Continuity Policy

TIER 2: STANDARDS (Technical management level)
- Database Security Standard
- Encryption Standard (algorithms, key lengths, protocols)
- Access Control Standard (authentication, authorization methods)
- Logging and Monitoring Standard
- Patch Management Standard

TIER 3: PROCEDURES (Operational level)
- Database Provisioning Procedure
- Access Request and Approval Procedure
- Backup and Recovery Procedure
- Incident Response Procedure for Database Breach
- Change Management Procedure for Schema Changes
- Key Rotation Procedure
- User Account Review Procedure

TIER 4: GUIDELINES & EVIDENCE (Implementation level)
- Database Hardening Guide (CIS Benchmark implementation)
- SQL Injection Prevention Guide for Developers
- Encryption Implementation Guide
- Audit Log Review Guide
- Evidence artifacts (screenshots, configs, reports)
```

### 8.5 GRC Tools

| Tool | Strengths | Database Compliance Use |
|------|-----------|------------------------|
| ServiceNow GRC | Integrated ITSM + GRC, automated workflows | Control testing linked to change management |
| Archer (RSA) | Risk quantification, regulatory change tracking | Multi-framework mapping, risk scoring |
| LogicGate | Flexible workflow builder, API-first | Custom evidence collection pipelines |
| OneTrust | Privacy-focused, consent management | GDPR/CCPA data mapping, DPIA automation |
| Drata | Automated evidence collection, continuous monitoring | Cloud database compliance monitoring |
| Vanta | Developer-friendly, fast implementation | SOC 2/ISO automated evidence for SaaS databases |
| AuditBoard | Collaboration-focused, SOX expertise | SOX control testing workflows |
| Hyperproof | Evidence management, gap analysis | Multi-framework evidence repository |

---

## 9. Continuous Compliance

### 9.1 Automated Compliance Scanning

**Chef InSpec for Database Compliance:**

```ruby
# inspec/profiles/postgresql-pci/controls/requirement_3.rb
# PCI-DSS Requirement 3: Protect Stored Account Data

control 'pci-3.4-encryption' do
  title 'PAN must be rendered unreadable in storage'
  desc 'Verify that stored PAN is encrypted with AES-256 or stronger'
  impact 1.0  # Critical

  describe sql.query("
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_schema = 'pci_data'
      AND column_name LIKE '%pan%'
      AND data_type != 'bytea'
  ") do
    its('rows') { should be_empty }  # All PAN columns should be bytea (encrypted)
  end
end

control 'pci-3.5-key-management' do
  title 'Encryption keys must be properly managed'
  desc 'Verify key rotation within cryptoperiod'
  impact 0.9

  describe sql.query("
    SELECT key_id, created_at, rotated_at,
           EXTRACT(days FROM NOW() - COALESCE(rotated_at, created_at)) AS days_active
    FROM encryption_key_inventory
    WHERE status = 'ACTIVE'
      AND EXTRACT(days FROM NOW() - COALESCE(rotated_at, created_at)) > 365
  ") do
    its('rows') { should be_empty }  # No keys active > 365 days
  end
end

control 'pci-10.1-audit-logging' do
  title 'Audit logging must be enabled and capturing required events'
  impact 1.0

  describe sql.query("
    SELECT name, setting FROM pg_settings WHERE name = 'pgaudit.log'
  ") do
    its('rows.first.column("setting")') { should include 'read' }
    its('rows.first.column("setting")') { should include 'write' }
    its('rows.first.column("setting")') { should include 'ddl' }
  end
end

control 'pci-8.2-strong-auth' do
  title 'No password-based authentication without strong hashing'
  impact 0.9

  describe sql.query("
    SELECT name, setting FROM pg_settings WHERE name = 'password_encryption'
  ") do
    its('rows.first.column("setting")') { should eq 'scram-sha-256' }
  end

  # Verify no md5 entries in pg_hba.conf
  describe file('/etc/postgresql/16/main/pg_hba.conf') do
    its('content') { should_not match(/\bmd5\b/) }
  end
end
```

**AWS Config Rules for RDS Compliance:**

```json
{
  "ConfigRules": [
    {
      "ConfigRuleName": "rds-storage-encrypted",
      "Source": {
        "Owner": "AWS",
        "SourceIdentifier": "RDS_STORAGE_ENCRYPTED"
      },
      "Scope": {
        "ComplianceResourceTypes": ["AWS::RDS::DBInstance"]
      }
    },
    {
      "ConfigRuleName": "rds-instance-public-access-check",
      "Source": {
        "Owner": "AWS",
        "SourceIdentifier": "RDS_INSTANCE_PUBLIC_ACCESS_CHECK"
      }
    },
    {
      "ConfigRuleName": "rds-logging-enabled",
      "Source": {
        "Owner": "AWS",
        "SourceIdentifier": "RDS_LOGGING_ENABLED"
      }
    },
    {
      "ConfigRuleName": "rds-multi-az-support",
      "Source": {
        "Owner": "AWS",
        "SourceIdentifier": "RDS_MULTI_AZ_SUPPORT"
      }
    },
    {
      "ConfigRuleName": "rds-snapshot-encrypted",
      "Source": {
        "Owner": "CUSTOM_LAMBDA",
        "SourceIdentifier": "arn:aws:lambda:us-east-1:123456789:function:check-rds-snapshot-encryption"
      }
    }
  ]
}
```

**Azure Policy for Database Compliance:**

```json
{
  "policyDefinitions": [
    {
      "displayName": "PostgreSQL servers should use TLS 1.2",
      "policyRule": {
        "if": {
          "allOf": [
            {
              "field": "type",
              "equals": "Microsoft.DBforPostgreSQL/servers"
            },
            {
              "field": "Microsoft.DBforPostgreSQL/servers/minimalTlsVersion",
              "notEquals": "TLS1_2"
            }
          ]
        },
        "then": {
          "effect": "deny"
        }
      }
    },
    {
      "displayName": "PostgreSQL databases must have encryption at rest",
      "policyRule": {
        "if": {
          "allOf": [
            {
              "field": "type",
              "equals": "Microsoft.DBforPostgreSQL/servers"
            },
            {
              "field": "Microsoft.DBforPostgreSQL/servers/infrastructureEncryption",
              "notEquals": "Enabled"
            }
          ]
        },
        "then": {
          "effect": "deny"
        }
      }
    }
  ]
}
```

### 9.2 Drift Detection

Configuration drift occurs when a system's actual state deviates from its approved baseline. For databases, drift can introduce compliance violations silently.

```python
# drift_detector.py — Database configuration drift detection

from dataclasses import dataclass
from typing import Any

@dataclass
class DriftFinding:
    parameter: str
    expected: Any
    actual: Any
    severity: str
    framework_impact: list[str]

class DatabaseDriftDetector:
    """Detect configuration drift from approved baseline."""

    def __init__(self, baseline: dict, current_config: dict):
        self.baseline = baseline
        self.current = current_config
        self.findings: list[DriftFinding] = []

    def detect(self) -> list[DriftFinding]:
        # Security-critical parameters
        critical_params = {
            "ssl": {"expected": "on", "frameworks": ["PCI-DSS", "HIPAA", "NIST"]},
            "ssl_min_protocol_version": {"expected": "TLSv1.2", "frameworks": ["PCI-DSS", "NIST"]},
            "password_encryption": {"expected": "scram-sha-256", "frameworks": ["PCI-DSS", "NIST"]},
            "log_connections": {"expected": "on", "frameworks": ["PCI-DSS", "HIPAA", "SOX"]},
            "log_disconnections": {"expected": "on", "frameworks": ["PCI-DSS", "HIPAA"]},
            "pgaudit.log": {"expected": "read, write, ddl, role", "frameworks": ["PCI-DSS", "HIPAA", "SOX"]},
            "log_statement": {"expected": "ddl", "frameworks": ["SOX", "NIST"]},
            "idle_in_transaction_session_timeout": {"expected": "300000", "frameworks": ["HIPAA"]},
        }

        for param, spec in critical_params.items():
            actual_value = self.current.get(param)
            if actual_value != spec["expected"]:
                self.findings.append(DriftFinding(
                    parameter=param,
                    expected=spec["expected"],
                    actual=actual_value,
                    severity="CRITICAL" if param in ("ssl", "password_encryption") else "HIGH",
                    framework_impact=spec["frameworks"]
                ))

        # pg_hba.conf drift (authentication method changes)
        self._check_hba_drift()

        # Role/permission drift
        self._check_permission_drift()

        return self.findings

    def _check_hba_drift(self):
        """Detect unauthorized changes to authentication configuration."""
        baseline_hba = self.baseline.get("pg_hba_rules", [])
        current_hba = self.current.get("pg_hba_rules", [])

        new_rules = [r for r in current_hba if r not in baseline_hba]
        for rule in new_rules:
            if rule.get("auth_method") in ("trust", "md5", "password"):
                self.findings.append(DriftFinding(
                    parameter="pg_hba.conf",
                    expected="no trust/md5/password methods",
                    actual=f"New rule: {rule}",
                    severity="CRITICAL",
                    framework_impact=["PCI-DSS", "HIPAA", "NIST", "SOX"]
                ))

    def _check_permission_drift(self):
        """Detect unauthorized privilege escalation."""
        baseline_roles = self.baseline.get("role_grants", {})
        current_roles = self.current.get("role_grants", {})

        for role, current_grants in current_roles.items():
            baseline_grants = baseline_roles.get(role, [])
            new_grants = set(current_grants) - set(baseline_grants)
            if new_grants:
                self.findings.append(DriftFinding(
                    parameter=f"role_grants.{role}",
                    expected=baseline_grants,
                    actual=current_grants,
                    severity="HIGH",
                    framework_impact=["PCI-DSS", "HIPAA", "SOX", "NIST"]
                ))
```

### 9.3 Compliance-as-Code with OPA/Rego

Open Policy Agent (OPA) with Rego policies enables declarative compliance rules that can be evaluated against database configurations, Terraform plans, Kubernetes manifests, and API requests.

```rego
# policy/database/pci_dss.rego
package database.pci_dss

# Requirement 2: Do not use vendor-supplied defaults
deny[msg] {
    input.database.port == 5432
    input.database.is_internet_facing == true
    msg := "PCI 2.2.7: Default port on internet-facing database"
}

deny[msg] {
    input.database.admin_username == "postgres"
    msg := "PCI 2.1: Default admin username not changed"
}

# Requirement 3: Protect stored account data
deny[msg] {
    table := input.database.tables[_]
    column := table.columns[_]
    column.contains_pan == true
    column.encrypted == false
    msg := sprintf("PCI 3.4: Unencrypted PAN in %s.%s", [table.name, column.name])
}

# Requirement 7: Restrict access by business need-to-know
deny[msg] {
    role := input.database.roles[_]
    role.has_superuser == true
    role.is_application_account == true
    msg := sprintf("PCI 7.1: Application account '%s' has superuser privileges", [role.name])
}

# Requirement 8: Identify users and authenticate
deny[msg] {
    input.database.password_encryption != "scram-sha-256"
    msg := "PCI 8.3.2: Password hashing must use strong algorithm (scram-sha-256)"
}

deny[msg] {
    hba_rule := input.database.hba_rules[_]
    hba_rule.auth_method == "trust"
    msg := sprintf("PCI 8.2: Trust authentication on %s:%s", [hba_rule.address, hba_rule.database])
}

# Requirement 10: Track and monitor access
deny[msg] {
    input.database.pgaudit_enabled == false
    msg := "PCI 10.1: Audit logging (pgAudit) not enabled"
}

deny[msg] {
    input.database.log_retention_days < 365
    msg := sprintf("PCI 10.7: Log retention %d days, minimum 365 required", [input.database.log_retention_days])
}

# Compile all violations
violations := deny
compliance_score := (count(input.database.controls_assessed) - count(deny)) / count(input.database.controls_assessed) * 100
```

```rego
# policy/database/hipaa.rego
package database.hipaa

# §164.312(a)(2)(i) — Unique User Identification
deny[msg] {
    role := input.database.roles[_]
    contains(lower(role.name), "shared")
    msg := sprintf("HIPAA §164.312(a)(2)(i): Shared account detected: %s", [role.name])
}

# §164.312(a)(2)(iii) — Automatic Logoff
deny[msg] {
    timeout := input.database.settings["idle_in_transaction_session_timeout"]
    to_number(timeout) == 0
    msg := "HIPAA §164.312(a)(2)(iii): No automatic logoff configured"
}

deny[msg] {
    timeout := input.database.settings["idle_in_transaction_session_timeout"]
    to_number(timeout) > 600000  # 10 minutes
    msg := sprintf("HIPAA §164.312(a)(2)(iii): Logoff timeout too long: %sms (max 600000)", [timeout])
}

# §164.312(a)(2)(iv) — Encryption and Decryption
deny[msg] {
    table := input.database.tables[_]
    table.contains_ephi == true
    table.encryption_at_rest == false
    msg := sprintf("HIPAA §164.312(a)(2)(iv): ePHI table '%s' not encrypted at rest", [table.name])
}

# §164.312(e)(2)(ii) — Encryption in Transit
deny[msg] {
    input.database.ssl_enabled == false
    msg := "HIPAA §164.312(e)(2)(ii): TLS not enabled for database connections"
}

# §164.312(b) — Audit Controls
deny[msg] {
    table := input.database.tables[_]
    table.contains_ephi == true
    table.audit_trigger_enabled == false
    msg := sprintf("HIPAA §164.312(b): ePHI table '%s' missing audit trigger", [table.name])
}
```

### 9.4 Real-Time Compliance Dashboards

```sql
-- Compliance dashboard data model
CREATE TABLE compliance_metrics (
    id SERIAL PRIMARY KEY,
    framework TEXT NOT NULL,
    control_id TEXT NOT NULL,
    control_description TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('PASS', 'FAIL', 'EXCEPTION', 'NOT_ASSESSED')),
    last_assessed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    next_assessment_due TIMESTAMP NOT NULL,
    evidence_reference TEXT,
    findings TEXT[],
    risk_score NUMERIC(3,1)  -- 0.0 to 10.0
);

-- Compliance score calculation
CREATE VIEW compliance_scorecard AS
SELECT
    framework,
    COUNT(*) AS total_controls,
    COUNT(*) FILTER (WHERE status = 'PASS') AS passing,
    COUNT(*) FILTER (WHERE status = 'FAIL') AS failing,
    COUNT(*) FILTER (WHERE status = 'EXCEPTION') AS exceptions,
    ROUND(
        COUNT(*) FILTER (WHERE status = 'PASS')::NUMERIC / NULLIF(COUNT(*), 0) * 100, 1
    ) AS compliance_percentage,
    MAX(last_assessed_at) AS last_full_assessment,
    MIN(next_assessment_due) AS next_assessment_due
FROM compliance_metrics
GROUP BY framework;

-- Overdue assessments alert
CREATE VIEW overdue_assessments AS
SELECT framework, control_id, control_description,
       next_assessment_due,
       NOW() - next_assessment_due AS overdue_by
FROM compliance_metrics
WHERE next_assessment_due < NOW()
  AND status != 'NOT_ASSESSED'
ORDER BY overdue_by DESC;

-- Framework overlap analysis (controls satisfying multiple frameworks)
CREATE VIEW control_overlap AS
SELECT
    cm1.control_id AS primary_control,
    cm1.framework AS primary_framework,
    cm2.control_id AS related_control,
    cm2.framework AS related_framework,
    cm.mapping_rationale
FROM compliance_metrics cm1
JOIN control_mappings cm ON cm.source_control = cm1.control_id
JOIN compliance_metrics cm2 ON cm2.control_id = cm.target_control
ORDER BY cm1.framework, cm1.control_id;
```

### 9.5 Exception Management Process

```
COMPLIANCE EXCEPTION LIFECYCLE:
═══════════════════════════════

1. IDENTIFICATION
   - Control test fails OR
   - Known gap identified during assessment OR
   - Business constraint prevents implementation

2. RISK ASSESSMENT
   - Identify affected assets and data
   - Determine threat likelihood (1-5)
   - Determine impact severity (1-5)
   - Calculate risk score = likelihood × severity
   - Document affected frameworks

3. EXCEPTION REQUEST
   - Business justification (why control cannot be met)
   - Duration requested (never indefinite — max 12 months)
   - Compensating controls proposed
   - Remediation timeline (when will exception end)
   - Risk owner acceptance (signature)

4. APPROVAL
   - Risk score 1-8: Manager approval
   - Risk score 9-15: Director approval
   - Risk score 16-25: CISO/CRO approval
   - Any exception affecting PCI CDE: QSA consultation

5. DOCUMENTATION
   - Exception ID, date, expiration
   - Risk rating and owner
   - Compensating controls in place
   - Monitoring plan during exception period
   - Remediation milestones

6. MONITORING
   - Compensating controls tested on regular cadence
   - Risk score reassessed if environment changes
   - Progress toward remediation tracked
   - Alert 60 days before expiration

7. CLOSURE
   - Remediation implemented → close exception
   - OR renewal requested → repeat from step 2
   - Expired without renewal → escalate as finding
```

### 9.6 Risk Acceptance Documentation

```
RISK ACCEPTANCE FORM
════════════════════

Risk ID: RA-2024-047
Date: 2024-11-15
Framework(s) Affected: PCI-DSS 3.4, NIST SC-28

RISK DESCRIPTION:
Legacy payment processing module (v2.3) stores PAN in database
using 3DES encryption. PCI-DSS v4.0 requires migration to AES-128+.
Module scheduled for replacement in Q3 2025.

CURRENT CONTROLS:
- 3DES encryption (168-bit effective key)
- Network isolation (dedicated VLAN, no internet access)
- Application-layer access only (no direct DB queries)
- Enhanced monitoring (all queries logged and alerted)
- Weekly key rotation (exceeds annual requirement)

RISK ASSESSMENT:
- Likelihood: 2/5 (3DES not trivially broken in network-isolated env)
- Impact: 4/5 (PAN exposure if compromised)
- Risk Score: 8/25 (MEDIUM)
- Residual risk with compensating controls: 5/25 (LOW-MEDIUM)

JUSTIFICATION:
- Module replacement in active development (project APEX-2025)
- 3DES migration requires downtime affecting 24/7 processing
- Cost of interim migration: $180k with 6-week implementation
- Risk exposure: 8 months until module replacement

COMPENSATING CONTROLS:
1. Network isolation verified weekly (automated scan)
2. IDS/IPS on VLAN boundaries (signature + anomaly)
3. Enhanced logging: all access attempts alerted real-time
4. Bi-weekly penetration test of isolated segment
5. Key rotation every 7 days (vs 90-day 3DES best practice)

ACCEPTANCE:
Risk Owner: [Name], VP Engineering  Date: 2024-11-15
CISO Review: [Name], CISO           Date: 2024-11-16
QSA Consultation: [Name], QSA       Date: 2024-11-18

Expiration: 2025-07-31 (or module replacement, whichever first)
Review Cadence: Monthly
```

---

## 10. Lab Exercises

### Lab 1: PCI-DSS Assessment Scoping for a Database Environment

**Scenario:** You are conducting a PCI-DSS v4.0 assessment for an e-commerce company. They have the following database infrastructure:

```
Environment:
- PostgreSQL 16 cluster (primary + 2 replicas) — stores tokenized transaction data
- Redis cache — stores session data and temporary cart data
- MongoDB — stores product catalog and user preferences
- Elasticsearch — stores application logs
- Token vault (HashiCorp Vault) — stores PAN-to-token mappings
- Data warehouse (Snowflake) — receives daily financial aggregates
- Analytics database (ClickHouse) — clickstream and behavior data
```

**Exercise Tasks:**

1. **Scope Determination:** For each database system, determine its PCI-DSS scope category (CDE, Connected-to, Security-Impacting, Out-of-Scope). Document your rationale.

2. **Data Flow Mapping:** Create a data flow diagram showing how cardholder data enters the environment, where it is tokenized, and where tokens flow afterward.

3. **Segmentation Validation Plan:** Design penetration test scenarios to validate network segmentation between the CDE (token vault) and connected/out-of-scope systems.

4. **Scoping Documentation:** Complete a scope validation document per Requirement 12.5.2.

**Expected Answers:**

```
Scoping Results:
┌──────────────────────┬──────────────────┬────────────────────────────────┐
│ System               │ Scope Category   │ Rationale                      │
├──────────────────────┼──────────────────┼────────────────────────────────┤
│ Token Vault (Vault)  │ CDE              │ Stores actual PAN data         │
│ PostgreSQL cluster   │ Connected-to     │ Stores tokens, connects to     │
│                      │                  │ token vault for detokenization  │
│ Redis cache          │ Connected-to     │ May cache detokenized data     │
│                      │                  │ temporarily (investigate TTL)  │
│ Data Warehouse       │ Connected-to     │ Receives financial aggregates  │
│                      │                  │ (verify no PAN in aggregates)  │
│ Elasticsearch        │ Security-Impact  │ Stores logs that may contain   │
│                      │                  │ security events for CDE        │
│ MongoDB              │ Out-of-Scope     │ No CHD, no CDE connectivity    │
│                      │                  │ (verify network isolation)     │
│ ClickHouse           │ Out-of-Scope     │ Behavioral data only, no CHD   │
│                      │                  │ (verify no PAN in clickstream) │
└──────────────────────┴──────────────────┴────────────────────────────────┘
```

---

### Lab 2: Implement HIPAA Technical Safeguards for PostgreSQL

**Scenario:** A healthcare startup stores patient records in PostgreSQL 16 on AWS RDS. You need to implement all required HIPAA technical safeguards.

**Exercise Tasks:**

```sql
-- TASK 1: Access Control (§164.312(a))
-- Implement unique user identification, emergency access,
-- automatic logoff, and encryption/decryption mechanisms

-- Step 1: Create role hierarchy
CREATE ROLE hipaa_admin NOLOGIN;
CREATE ROLE clinician NOLOGIN;
CREATE ROLE nurse NOLOGIN;
CREATE ROLE billing NOLOGIN;
CREATE ROLE researcher NOLOGIN;  -- De-identified data only

-- Step 2: Create schema with RLS
CREATE SCHEMA clinical;
ALTER TABLE clinical.patient_records ENABLE ROW LEVEL SECURITY;

-- Step 3: Implement policies per role
-- Clinicians: only their assigned patients
CREATE POLICY clinician_access ON clinical.patient_records
    FOR ALL TO clinician
    USING (
        primary_provider_id = current_setting('app.provider_id')::int
        OR patient_id IN (
            SELECT patient_id FROM clinical.care_team_assignments
            WHERE provider_id = current_setting('app.provider_id')::int
              AND active = TRUE
        )
    );

-- Nurses: read-only for their department patients
CREATE POLICY nurse_access ON clinical.patient_records
    FOR SELECT TO nurse
    USING (
        department_id = current_setting('app.department_id')::int
    );

-- Researchers: only de-identified view
GRANT SELECT ON clinical.deidentified_patients TO researcher;
-- NO access to clinical.patient_records

-- Step 4: Automatic logoff
ALTER SYSTEM SET idle_in_transaction_session_timeout = '300000';  -- 5 min
ALTER SYSTEM SET statement_timeout = '120000';  -- 2 min

-- Step 5: Encryption
-- At rest: RDS encryption enabled (verify via AWS console/CLI)
-- Column-level for high-sensitivity:
ALTER TABLE clinical.patient_records
    ADD COLUMN ssn_encrypted BYTEA,
    ADD COLUMN diagnosis_encrypted BYTEA,
    ADD COLUMN notes_encrypted BYTEA;

-- TASK 2: Audit Controls (§164.312(b))
-- Enable comprehensive auditing

-- Install and configure pgAudit
CREATE EXTENSION IF NOT EXISTS pgaudit;
-- In parameter group: pgaudit.log = 'all'
-- In parameter group: pgaudit.log_catalog = 'on'
-- In parameter group: pgaudit.log_parameter = 'on'

-- Create audit trigger for ePHI tables
-- (See section 2.3 for full implementation)

-- TASK 3: Integrity Controls (§164.312(c)(1))
-- Implement mechanism to authenticate ePHI

-- Checksum-based integrity verification
ALTER TABLE clinical.patient_records
    ADD COLUMN data_hash VARCHAR(64),
    ADD COLUMN last_integrity_check TIMESTAMP;

CREATE OR REPLACE FUNCTION compute_record_hash(p_record clinical.patient_records)
RETURNS VARCHAR(64) AS $$
    SELECT encode(digest(
        p_record.mrn || p_record.dob::text || p_record.ssn_encrypted::text,
        'sha256'
    ), 'hex');
$$ LANGUAGE sql IMMUTABLE;

-- TASK 4: Transmission Security (§164.312(e)(1))
-- Verify TLS enforcement
-- In RDS: force_ssl = 1 (parameter group)
-- Application connection string must include sslmode=verify-full
```

**Validation Steps:**

```bash
# Verify TLS is enforced
psql "host=mydb.rds.amazonaws.com dbname=clinical sslmode=disable" 2>&1 | grep -i "ssl"
# Should fail with: FATAL: no pg_hba.conf entry for host... SSL off

# Verify pgAudit is logging
psql -c "SELECT * FROM clinical.patient_records LIMIT 1;"
# Check CloudWatch logs for pgAudit entry

# Verify RLS is enforced
SET app.provider_id = '999';  -- Non-existent provider
SELECT * FROM clinical.patient_records;
# Should return 0 rows (not an error, just empty due to RLS)
```

---

### Lab 3: SOX-Compliant Change Management for Schema Migrations

**Scenario:** Build a change management system that satisfies SOX Section 404 requirements for database schema changes affecting financial reporting systems.

**Exercise Tasks:**

```sql
-- TASK 1: Change tracking infrastructure

CREATE SCHEMA change_management;

CREATE TABLE change_management.change_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id VARCHAR(20) UNIQUE NOT NULL,  -- e.g., CHG-2024-0001

    -- Request details
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    migration_sql TEXT NOT NULL,
    rollback_sql TEXT NOT NULL,

    -- Impact assessment
    affected_tables TEXT[] NOT NULL,
    affected_reports TEXT[] NOT NULL,  -- Which financial reports impacted
    risk_level TEXT NOT NULL CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    downtime_required BOOLEAN DEFAULT FALSE,

    -- Segregation of duties
    requested_by TEXT NOT NULL,
    requested_at TIMESTAMP DEFAULT NOW(),
    reviewed_by TEXT,
    reviewed_at TIMESTAMP,
    approved_by TEXT,                 -- Must differ from requested_by
    approved_at TIMESTAMP,
    implemented_by TEXT,             -- Must differ from approved_by
    implemented_at TIMESTAMP,

    -- Status tracking
    status TEXT NOT NULL DEFAULT 'DRAFT' CHECK (status IN (
        'DRAFT', 'SUBMITTED', 'UNDER_REVIEW', 'APPROVED',
        'SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'ROLLED_BACK', 'REJECTED'
    )),

    -- Testing evidence
    test_environment TEXT,
    test_results JSONB,
    reconciliation_pre JSONB,
    reconciliation_post JSONB,

    -- Constraints: enforce separation of duties
    CONSTRAINT sod_approval CHECK (approved_by IS NULL OR approved_by != requested_by),
    CONSTRAINT sod_implementation CHECK (implemented_by IS NULL OR implemented_by != approved_by)
);

-- TASK 2: Migration execution with pre/post validation

CREATE OR REPLACE FUNCTION change_management.execute_migration(
    p_ticket_id VARCHAR(20),
    p_implementer TEXT
) RETURNS JSONB AS $$
DECLARE
    v_change RECORD;
    v_pre_snapshot JSONB;
    v_post_snapshot JSONB;
    v_result JSONB;
BEGIN
    -- Fetch and validate change request
    SELECT * INTO v_change
    FROM change_management.change_requests
    WHERE ticket_id = p_ticket_id AND status = 'APPROVED';

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Change % not found or not in APPROVED status', p_ticket_id;
    END IF;

    -- Verify implementer is not the approver (SOX SoD)
    IF v_change.approved_by = p_implementer THEN
        RAISE EXCEPTION 'SOX violation: implementer cannot be approver';
    END IF;

    -- Capture pre-migration snapshot
    v_pre_snapshot := change_management.capture_snapshot(v_change.affected_tables);

    -- Update status
    UPDATE change_management.change_requests
    SET status = 'IN_PROGRESS', implemented_by = p_implementer, implemented_at = NOW()
    WHERE ticket_id = p_ticket_id;

    -- Execute migration
    BEGIN
        EXECUTE v_change.migration_sql;
    EXCEPTION WHEN OTHERS THEN
        -- Rollback and record failure
        UPDATE change_management.change_requests
        SET status = 'ROLLED_BACK',
            reconciliation_pre = v_pre_snapshot,
            test_results = jsonb_build_object('error', SQLERRM)
        WHERE ticket_id = p_ticket_id;
        RAISE;
    END;

    -- Capture post-migration snapshot
    v_post_snapshot := change_management.capture_snapshot(v_change.affected_tables);

    -- Run reconciliation
    v_result := change_management.reconcile_snapshots(v_pre_snapshot, v_post_snapshot);

    -- Update with results
    UPDATE change_management.change_requests
    SET status = 'COMPLETED',
        reconciliation_pre = v_pre_snapshot,
        reconciliation_post = v_post_snapshot,
        test_results = v_result
    WHERE ticket_id = p_ticket_id;

    RETURN v_result;
END;
$$ LANGUAGE plpgsql;

-- TASK 3: Automated reconciliation
CREATE OR REPLACE FUNCTION change_management.capture_snapshot(p_tables TEXT[])
RETURNS JSONB AS $$
DECLARE
    v_snapshot JSONB := '{}';
    v_table TEXT;
    v_count BIGINT;
    v_sum NUMERIC;
BEGIN
    FOREACH v_table IN ARRAY p_tables LOOP
        EXECUTE format('SELECT COUNT(*) FROM %I', v_table) INTO v_count;

        -- Try to get sum of amount columns (financial data)
        BEGIN
            EXECUTE format(
                'SELECT COALESCE(SUM(amount), 0) FROM %I', v_table
            ) INTO v_sum;
        EXCEPTION WHEN undefined_column THEN
            v_sum := NULL;
        END;

        v_snapshot := v_snapshot || jsonb_build_object(
            v_table, jsonb_build_object(
                'row_count', v_count,
                'amount_sum', v_sum,
                'captured_at', NOW()
            )
        );
    END LOOP;
    RETURN v_snapshot;
END;
$$ LANGUAGE plpgsql;
```

**Validation Criteria:**

```
SOX Compliance Verification:
[ ] No single person can request + approve + implement
[ ] All changes have pre/post reconciliation
[ ] Rollback procedure tested before production execution
[ ] Audit trail complete (who, what, when, outcome)
[ ] Financial data integrity maintained (row counts, sums match)
[ ] Change ticket linked to business justification
[ ] High-risk changes reviewed by CAB
```

---

### Lab 4: Automated Compliance Evidence Collection for Multi-Framework

**Scenario:** Build an automated evidence collection system that simultaneously satisfies PCI-DSS, HIPAA, SOX, and NIST 800-53 requirements from a single PostgreSQL database cluster.

**Exercise Tasks:**

```python
# multi_framework_evidence.py
# Automated evidence collection satisfying multiple frameworks simultaneously

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
import json
import hashlib

class Framework(Enum):
    PCI_DSS = "PCI-DSS v4.0"
    HIPAA = "HIPAA"
    SOX = "SOX"
    NIST_800_53 = "NIST 800-53"

@dataclass
class ControlMapping:
    """Maps a single evidence check to multiple framework controls."""
    check_id: str
    description: str
    frameworks: dict[Framework, str]  # Framework → specific control ID
    query: str
    expected_result: str
    severity: str

@dataclass
class EvidenceResult:
    check_id: str
    timestamp: str
    result: dict
    status: str  # PASS, FAIL, ERROR
    frameworks_satisfied: list[str]
    frameworks_violated: list[str]
    hash: str = ""

    def __post_init__(self):
        # Tamper-evident hash of evidence
        content = json.dumps({
            "check_id": self.check_id,
            "timestamp": self.timestamp,
            "result": self.result,
            "status": self.status
        }, sort_keys=True)
        self.hash = hashlib.sha256(content.encode()).hexdigest()


# Multi-framework control mappings
CONTROL_MAPPINGS = [
    ControlMapping(
        check_id="ENC-001",
        description="Database encryption at rest is enabled",
        frameworks={
            Framework.PCI_DSS: "Req 3.4 (render PAN unreadable)",
            Framework.HIPAA: "§164.312(a)(2)(iv) (encryption mechanism)",
            Framework.NIST_800_53: "SC-28 (protection of info at rest)",
        },
        query="""
            SELECT current_setting('data_encryption') as encryption_status,
                   pg_catalog.pg_stat_file('base/1/PG_VERSION') IS NOT NULL as accessible
        """,
        expected_result="encryption_status = on",
        severity="CRITICAL"
    ),
    ControlMapping(
        check_id="TLS-001",
        description="TLS 1.2+ enforced for all connections",
        frameworks={
            Framework.PCI_DSS: "Req 4.2.1 (strong cryptography for transmission)",
            Framework.HIPAA: "§164.312(e)(2)(ii) (encryption in transit)",
            Framework.NIST_800_53: "SC-8 (transmission confidentiality)",
        },
        query="""
            SELECT name, setting FROM pg_settings
            WHERE name IN ('ssl', 'ssl_min_protocol_version')
        """,
        expected_result="ssl=on AND ssl_min_protocol_version>=TLSv1.2",
        severity="CRITICAL"
    ),
    ControlMapping(
        check_id="AUTH-001",
        description="No shared or generic accounts exist",
        frameworks={
            Framework.PCI_DSS: "Req 8.2.1 (unique ID for each user)",
            Framework.HIPAA: "§164.312(a)(2)(i) (unique user identification)",
            Framework.SOX: "Section 404 (individual accountability)",
            Framework.NIST_800_53: "IA-2 (identification and authentication)",
        },
        query="""
            SELECT rolname FROM pg_roles
            WHERE rolcanlogin = TRUE
              AND (rolname LIKE '%shared%'
                   OR rolname LIKE '%generic%'
                   OR rolname LIKE '%common%'
                   OR rolname = 'admin')
        """,
        expected_result="0 rows returned",
        severity="HIGH"
    ),
    ControlMapping(
        check_id="AUDIT-001",
        description="Comprehensive audit logging enabled",
        frameworks={
            Framework.PCI_DSS: "Req 10.2 (audit log content)",
            Framework.HIPAA: "§164.312(b) (audit controls)",
            Framework.SOX: "Section 404 (audit trail)",
            Framework.NIST_800_53: "AU-2/AU-3 (audit events/content)",
        },
        query="""
            SELECT name, setting FROM pg_settings
            WHERE name LIKE 'pgaudit%'
              OR name IN ('log_connections', 'log_disconnections', 'log_statement')
        """,
        expected_result="pgaudit.log includes read,write,ddl",
        severity="CRITICAL"
    ),
    ControlMapping(
        check_id="ACCESS-001",
        description="No superuser application accounts",
        frameworks={
            Framework.PCI_DSS: "Req 7.2 (least privilege)",
            Framework.HIPAA: "§164.312(a)(1) (access control)",
            Framework.SOX: "Section 404 (separation of duties)",
            Framework.NIST_800_53: "AC-6 (least privilege)",
        },
        query="""
            SELECT rolname, rolsuper
            FROM pg_roles
            WHERE rolsuper = TRUE AND rolcanlogin = TRUE
              AND rolname != 'postgres'
        """,
        expected_result="0 rows (no extra superusers beyond postgres)",
        severity="HIGH"
    ),
    ControlMapping(
        check_id="BACKUP-001",
        description="Backups completed within RPO window",
        frameworks={
            Framework.HIPAA: "§164.308(a)(7) (contingency plan)",
            Framework.SOX: "Section 404 (data availability)",
            Framework.NIST_800_53: "CP-9 (information system backup)",
        },
        query="""
            SELECT backup_id, completed_at, encrypted,
                   NOW() - completed_at AS age
            FROM backup_history
            WHERE backup_type = 'full'
            ORDER BY completed_at DESC
            LIMIT 1
        """,
        expected_result="age < 24 hours AND encrypted = true",
        severity="HIGH"
    ),
    ControlMapping(
        check_id="RETENTION-001",
        description="Audit logs retained for required duration",
        frameworks={
            Framework.PCI_DSS: "Req 10.7 (12 months, 3 months accessible)",
            Framework.HIPAA: "§164.530(j) (6 years)",
            Framework.SOX: "Section 802 (7 years)",
            Framework.NIST_800_53: "AU-11 (audit record retention)",
        },
        query="""
            SELECT MIN(event_time) as oldest_log,
                   EXTRACT(days FROM NOW() - MIN(event_time)) as retention_days
            FROM audit_log
        """,
        expected_result="retention_days >= 365 (PCI) or >= 2190 (HIPAA/SOX)",
        severity="HIGH"
    ),
]


class MultiFrameworkCollector:
    """Execute all control checks and generate multi-framework evidence."""

    def __init__(self, db_connection):
        self.db = db_connection
        self.results: list[EvidenceResult] = []

    def collect_all(self) -> dict:
        """Run all control checks and generate evidence package."""
        timestamp = datetime.now(timezone.utc).isoformat()

        for mapping in CONTROL_MAPPINGS:
            try:
                query_result = self.db.execute(mapping.query)
                status = self._evaluate(query_result, mapping.expected_result)

                result = EvidenceResult(
                    check_id=mapping.check_id,
                    timestamp=timestamp,
                    result={"query_output": query_result, "expected": mapping.expected_result},
                    status=status,
                    frameworks_satisfied=[
                        f"{fw.value}: {ctrl}" for fw, ctrl in mapping.frameworks.items()
                    ] if status == "PASS" else [],
                    frameworks_violated=[
                        f"{fw.value}: {ctrl}" for fw, ctrl in mapping.frameworks.items()
                    ] if status == "FAIL" else [],
                )
                self.results.append(result)

            except Exception as e:
                self.results.append(EvidenceResult(
                    check_id=mapping.check_id,
                    timestamp=timestamp,
                    result={"error": str(e)},
                    status="ERROR",
                    frameworks_satisfied=[],
                    frameworks_violated=[
                        f"{fw.value}: {ctrl}" for fw, ctrl in mapping.frameworks.items()
                    ],
                ))

        return self._generate_report()

    def _evaluate(self, result: list, expected: str) -> str:
        """Evaluate query result against expected outcome."""
        # Simplified — real implementation would parse expected conditions
        if "0 rows" in expected:
            return "PASS" if len(result) == 0 else "FAIL"
        return "PASS"  # Placeholder for complex evaluation logic

    def _generate_report(self) -> dict:
        """Generate comprehensive multi-framework compliance report."""
        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "summary": {},
            "details": [vars(r) for r in self.results],
        }

        for framework in Framework:
            fw_results = []
            for r in self.results:
                mapping = next(m for m in CONTROL_MAPPINGS if m.check_id == r.check_id)
                if framework in mapping.frameworks:
                    fw_results.append(r.status)

            total = len(fw_results)
            passing = fw_results.count("PASS")
            report["summary"][framework.value] = {
                "total_controls": total,
                "passing": passing,
                "failing": fw_results.count("FAIL"),
                "errors": fw_results.count("ERROR"),
                "compliance_percentage": round(passing / total * 100, 1) if total > 0 else 0,
            }

        # Chain hash for tamper evidence
        report["evidence_chain_hash"] = hashlib.sha256(
            "".join(r.hash for r in self.results).encode()
        ).hexdigest()

        return report
```

**Running the Lab:**

```bash
# 1. Deploy PostgreSQL with required extensions
# 2. Apply the schema and control configurations
# 3. Run the multi-framework collector
# 4. Review output for:
#    - Which frameworks are passing
#    - Specific control failures
#    - Recommended remediations
# 5. Fix identified issues
# 6. Re-run and verify improvement

# Expected output structure:
# {
#   "summary": {
#     "PCI-DSS v4.0": {"compliance_percentage": 85.7, "failing": 1},
#     "HIPAA": {"compliance_percentage": 100.0, "failing": 0},
#     "SOX": {"compliance_percentage": 80.0, "failing": 1},
#     "NIST 800-53": {"compliance_percentage": 85.7, "failing": 1}
#   }
# }
```

---

## Summary

Compliance is not a checkbox exercise — it is a continuous engineering discipline. For data systems, the core truth is:

1. **Frameworks overlap significantly.** A well-implemented encryption control satisfies PCI-DSS 3.4, HIPAA §164.312(a)(2)(iv), NIST SC-28, and GLBA simultaneously. Map once, satisfy many.

2. **Automation is non-negotiable.** Manual evidence collection does not scale beyond a single framework. Invest in compliance-as-code from day one.

3. **Scope discipline saves millions.** PCI-DSS tokenization can reduce a 500-system CDE to a 5-system token vault. Architect for minimal scope.

4. **Separation of duties is structural.** It cannot be retrofitted. Design database RBAC, deployment pipelines, and approval workflows with SoD from the start.

5. **Audit logs are your insurance policy.** When (not if) a breach occurs, comprehensive, tamper-evident logging is the difference between a manageable incident and an existential one.

6. **Cloud shared responsibility is your responsibility.** A BAA or SOC 2 report from your provider does not make you compliant. You must configure, monitor, and evidence your controls.

For security assessors: understanding these frameworks at the implementation level — not just the checklist level — enables you to identify genuine control weaknesses versus superficial documentation gaps. The most impactful findings come from understanding what the control is supposed to achieve and testing whether it actually does.
