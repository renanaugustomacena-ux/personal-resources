# Data Protection, GDPR, and Privacy Engineering for Data Systems

## Table of Contents

1. [GDPR Core Principles](#1-gdpr-core-principles)
2. [Data Subject Rights Implementation](#2-data-subject-rights-implementation)
3. [Data Protection by Design and Default](#3-data-protection-by-design-and-default)
4. [Technical Measures for Compliance](#4-technical-measures-for-compliance)
5. [Cross-Border Data Transfers](#5-cross-border-data-transfers)
6. [Data Breach Notification](#6-data-breach-notification)
7. [DPO Role and Compliance Program](#7-dpo-role-and-compliance-program)
8. [Other Privacy Regulations](#8-other-privacy-regulations)
9. [Privacy Engineering in Practice](#9-privacy-engineering-in-practice)
10. [Lab Exercises](#10-lab-exercises)

---

## 1. GDPR Core Principles

The General Data Protection Regulation (Regulation (EU) 2016/679) entered into force on 25 May 2018 and remains the most influential privacy framework globally. Understanding its foundational principles is essential for anyone building, auditing, or securing data systems.

### 1.1 Article 5 — Principles Relating to Processing

Article 5 establishes six principles plus an overarching accountability requirement. Every data processing activity must satisfy ALL of these simultaneously:

**1. Lawfulness, Fairness, and Transparency (Art 5(1)(a))**

Processing must have a valid legal basis (Art 6), must not be deceptive, and must be communicated clearly to data subjects. From a security assessment perspective, check:
- Is there a documented legal basis for each processing activity?
- Are privacy notices actually accessible and comprehensible?
- Does the system process data in ways not disclosed to users?

**2. Purpose Limitation (Art 5(1)(b))**

Data collected for specified, explicit, and legitimate purposes cannot be further processed in a manner incompatible with those purposes. Exception exists for archiving in the public interest, scientific/historical research, or statistical purposes (Art 89(1)).

Technical implication: Data pipelines must enforce purpose boundaries. A customer email collected for order fulfillment cannot feed a marketing pipeline without separate legal basis.

**3. Data Minimization (Art 5(1)(c))**

Data must be adequate, relevant, and limited to what is necessary. This is not merely aspirational — it is a legally enforceable requirement.

In practice:
- Do not collect "just in case" fields
- Review data models for unnecessary attributes
- Implement column-level access controls
- Strip unnecessary fields at ingestion time

**4. Accuracy (Art 5(1)(d))**

Personal data must be accurate and kept up to date. Reasonable steps must be taken to erase or rectify inaccurate data without delay.

Technical requirements:
- Mechanisms for data subjects to update their data
- Validation at point of entry
- Periodic data quality audits
- Propagation of corrections across downstream systems

**5. Storage Limitation (Art 5(1)(e))**

Data kept in identifiable form only as long as necessary for the processing purposes. Longer retention permitted solely for archiving in public interest, scientific/historical research, or statistical purposes under Art 89(1) with appropriate safeguards.

Implementation requires:
- Defined retention periods per data category
- Automated deletion or anonymization workflows
- Retention schedule documentation
- Defensible disposal procedures

**6. Integrity and Confidentiality (Art 5(1)(f))**

Appropriate technical and organizational measures must protect against unauthorized or unlawful processing, accidental loss, destruction, or damage. This is the security principle — and where pentesting directly intersects with GDPR compliance.

Security controls include:
- Encryption at rest and in transit
- Access control enforcement
- Audit logging
- Intrusion detection
- Regular security testing

**7. Accountability (Art 5(2))**

The controller must be able to demonstrate compliance with all principles above. This shifts the burden of proof — you must prove you are compliant, not merely assert it.

Documentation requirements:
- Records of processing activities (Art 30)
- Data protection impact assessments (Art 35)
- Audit trails
- Policy documentation
- Training records

### 1.2 Article 6 — Lawful Basis for Processing

Six mutually exclusive legal bases exist. A controller must identify and document the applicable basis BEFORE processing begins:

| Legal Basis | Article | Use Case | Notes |
|---|---|---|---|
| Consent | 6(1)(a) | Marketing emails, cookies, profiling | Must be freely given, specific, informed, unambiguous. Withdrawable at any time. |
| Contract | 6(1)(b) | Fulfilling purchase orders, SaaS delivery | Only data strictly necessary for the contract |
| Legal Obligation | 6(1)(c) | Tax reporting, AML compliance | Must identify specific legal provision |
| Vital Interests | 6(1)(d) | Emergency medical situations | Narrow — rarely applicable in tech |
| Public Task | 6(1)(e) | Government functions, public authorities | Must have statutory basis |
| Legitimate Interest | 6(1)(f) | Fraud prevention, network security, direct marketing | Requires balancing test (LIA). Not available to public authorities for core tasks |

**Consent Requirements (Art 7)**

Consent under GDPR is substantially more demanding than pre-GDPR regimes:
- Must be affirmative action (no pre-ticked boxes)
- Granular — separate consent per purpose
- Easy to withdraw (as easy as to give)
- Not a condition of service unless genuinely necessary
- Controller must prove consent was obtained
- Children under 16 (or lower age set by Member State, minimum 13) require parental consent (Art 8)

**Special Categories of Data (Art 9)**

Processing of sensitive data (racial/ethnic origin, political opinions, religious beliefs, trade union membership, genetic data, biometric data for identification, health data, sex life/orientation) is prohibited except under specific conditions in Art 9(2):
- Explicit consent
- Employment/social security obligations
- Vital interests where subject incapable of giving consent
- Legitimate activities of foundations/associations with appropriate safeguards
- Data manifestly made public by the subject
- Legal claims
- Substantial public interest
- Health/medical purposes
- Public health
- Archiving/research/statistics

### 1.3 Articles 7-11 — Conditions and Special Processing

**Article 7 — Conditions for Consent:** Controllers must demonstrate consent was given. Consent requests must be clearly distinguishable from other matters, in intelligible and easily accessible form, using clear and plain language.

**Article 8 — Child's Consent:** Information society services directed at children require parental consent verification for children under 16 (adjustable to 13 by Member States). Age verification mechanisms are required but the Regulation does not prescribe specific technology.

**Article 9 — Special Categories:** As detailed above. From a pentest perspective, identifying systems processing special category data immediately elevates the risk profile and regulatory exposure.

**Article 10 — Criminal Conviction Data:** Processing only under control of official authority or when authorized by Union/Member State law with appropriate safeguards.

**Article 11 — Processing Not Requiring Identification:** If purposes do not require identification of data subjects, the controller is not obliged to maintain additional information solely to comply with the Regulation. However, data subject rights still apply if the subject provides additional information enabling identification.

---

## 2. Data Subject Rights Implementation

### 2.1 Right of Access (Article 15)

Data subjects can request confirmation whether their data is being processed and, if so, access to:
- The personal data itself
- Purposes of processing
- Categories of data concerned
- Recipients or categories of recipients
- Retention period or criteria for determining it
- Existence of rights to rectification, erasure, restriction, objection
- Right to lodge a complaint with a supervisory authority
- Source of the data (if not collected from the subject)
- Existence of automated decision-making including profiling
- Safeguards for international transfers

**Technical Implementation:**

```sql
-- Subject Access Request (SAR) query pattern
-- Aggregates all personal data for a given subject across tables

-- Master query for data subject export
SELECT 
    u.user_id,
    u.email,
    u.full_name,
    u.phone_number,
    u.date_of_birth,
    u.registration_date,
    u.last_login,
    a.street_address,
    a.city,
    a.postal_code,
    a.country
FROM users u
LEFT JOIN addresses a ON u.user_id = a.user_id
WHERE u.user_id = :subject_id;

-- Order history
SELECT order_id, order_date, total_amount, status
FROM orders WHERE user_id = :subject_id;

-- Consent records
SELECT purpose, consent_given, consent_date, withdrawal_date
FROM consent_records WHERE user_id = :subject_id;

-- Activity logs (may contain personal data)
SELECT activity_type, timestamp, ip_address, user_agent
FROM activity_logs WHERE user_id = :subject_id;
```

**SAR Response Architecture:**

```
┌─────────────────────────────────────────────┐
│         SAR Processing Pipeline              │
├─────────────────────────────────────────────┤
│ 1. Identity Verification                     │
│    └─ Confirm requester = data subject       │
│ 2. Data Discovery                            │
│    └─ Query all systems holding PII          │
│ 3. Third-Party Data Identification           │
│    └─ Flag data that includes others' PII    │
│ 4. Redaction                                 │
│    └─ Remove third-party data / trade secrets│
│ 5. Format & Deliver                          │
│    └─ Machine-readable format (JSON/CSV)     │
│ 6. Log the Request                           │
│    └─ Audit trail for accountability         │
└─────────────────────────────────────────────┘
```

Response deadline: Without undue delay, maximum one month (extendable by two months for complex/numerous requests with notification to data subject).

### 2.2 Right to Rectification (Article 16)

Data subjects can require correction of inaccurate personal data and completion of incomplete data (considering processing purposes).

**Implementation considerations:**
- Expose self-service profile editing for straightforward fields
- Implement a formal request workflow for data that cannot be self-serviced
- Propagate corrections to all downstream systems and recipients
- Maintain audit trail of corrections (previous value, new value, timestamp, authority)

```sql
-- Rectification audit table
CREATE TABLE rectification_log (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id),
    field_name VARCHAR(100) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    requested_at TIMESTAMP WITH TIME ZONE NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE,
    requested_by VARCHAR(50) NOT NULL, -- 'data_subject', 'dpo', 'system'
    propagated_to JSONB, -- list of downstream systems notified
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

### 2.3 Right to Erasure / Right to Be Forgotten (Article 17)

Data subjects can request deletion when:
- Data no longer necessary for original purpose
- Consent withdrawn (and no other legal basis exists)
- Subject objects under Art 21 and no overriding legitimate grounds
- Data unlawfully processed
- Legal obligation to erase
- Data collected in relation to information society services offered to a child

**Exceptions (Art 17(3)):** Processing is necessary for exercising freedom of expression, legal obligation compliance, public health purposes, archiving/research in public interest, or legal claims.

**Soft Delete vs Hard Delete:**

| Approach | Pros | Cons |
|---|---|---|
| Soft delete (flag + anonymize) | Maintains referential integrity, audit trail preserved, reversible if error | Data remnants in system, must ensure anonymization is irreversible |
| Hard delete (physical removal) | Complete removal, simplest for compliance demonstration | Breaks foreign keys, loses audit context, cascading deletes complex |
| Crypto-shredding | Fast at scale, maintains structure | Key management complexity, must ensure all copies use same key |

**Recommended hybrid approach:**

```sql
-- Step 1: Anonymize PII fields (soft delete with anonymization)
UPDATE users SET
    email = 'deleted_' || user_id || '@anonymized.invalid',
    full_name = 'DELETED',
    phone_number = NULL,
    date_of_birth = NULL,
    ip_addresses = NULL,
    is_deleted = TRUE,
    deleted_at = NOW(),
    deletion_reason = 'GDPR Art 17 request',
    deletion_request_id = :request_id
WHERE user_id = :subject_id;

-- Step 2: Remove from search indices
DELETE FROM user_search_index WHERE user_id = :subject_id;

-- Step 3: Remove from analytics (or anonymize)
UPDATE analytics_events SET
    user_id = NULL,
    ip_address = NULL,
    session_id = NULL
WHERE user_id = :subject_id;

-- Step 4: Notify downstream systems
INSERT INTO erasure_propagation_queue (
    user_id, target_system, status, queued_at
) VALUES
    (:subject_id, 'email_service', 'pending', NOW()),
    (:subject_id, 'analytics_platform', 'pending', NOW()),
    (:subject_id, 'backup_system', 'pending', NOW()),
    (:subject_id, 'cdn_cache', 'pending', NOW());
```

### 2.4 Right to Restriction of Processing (Article 18)

Data subjects can require restriction (storage without processing) when:
- Accuracy contested — restricted for period enabling verification
- Processing unlawful but subject opposes erasure
- Controller no longer needs data but subject needs it for legal claims
- Subject has objected under Art 21 pending verification of legitimate grounds

**Technical implementation:** Add a processing restriction flag:

```sql
ALTER TABLE users ADD COLUMN processing_restricted BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN restriction_reason TEXT;
ALTER TABLE users ADD COLUMN restricted_at TIMESTAMP WITH TIME ZONE;

-- All processing queries must check this flag
-- Example: marketing email query
SELECT email FROM users 
WHERE marketing_consent = TRUE 
AND processing_restricted = FALSE  -- CRITICAL: respect restriction
AND is_deleted = FALSE;
```

### 2.5 Right to Data Portability (Article 20)

Applies when processing is based on consent or contract AND carried out by automated means. Data subjects can receive their data in a structured, commonly used, machine-readable format and transmit it to another controller.

**API Design for Portability:**

```json
// GET /api/v1/data-export/{user_id}
// Response format
{
  "export_metadata": {
    "format_version": "1.0",
    "generated_at": "2025-03-15T14:30:00Z",
    "data_controller": "Example Corp",
    "data_subject_id": "usr_abc123",
    "export_scope": "full"
  },
  "personal_data": {
    "identity": {
      "name": "Jane Doe",
      "email": "jane@example.com",
      "phone": "+1-555-0123"
    },
    "activity": {
      "orders": [...],
      "preferences": {...},
      "communications": [...]
    },
    "consent_history": [
      {
        "purpose": "marketing_emails",
        "given": true,
        "timestamp": "2024-01-15T10:00:00Z"
      }
    ]
  }
}
```

Formats: JSON is preferred for APIs. CSV acceptable for tabular data. XML as fallback. The regulation does not mandate a specific format, only that it be "structured, commonly used, and machine-readable."

### 2.6 Right to Object (Article 21)

Data subjects can object to processing based on legitimate interest (Art 6(1)(f)) or public task (Art 6(1)(e)), including profiling based on those provisions. Controller must cease processing unless demonstrating compelling legitimate grounds overriding the interests of the data subject.

**Special cases:**
- Direct marketing: Absolute right to object, no balancing test. Must cease immediately.
- Research/statistics: Can object unless processing necessary for public interest task.

### 2.7 Automated Decision-Making (Article 22)

Data subjects have the right not to be subject to decisions based solely on automated processing (including profiling) which produce legal effects or similarly significantly affect them.

**Exceptions:**
- Necessary for contract
- Authorized by Union/Member State law
- Based on explicit consent

When exceptions apply, controller must implement:
- Right to obtain human intervention
- Right to express their point of view
- Right to contest the decision

**Implementation pattern:**

```python
class AutomatedDecisionEngine:
    def make_decision(self, user_id: str, input_data: dict) -> DecisionResult:
        # Check if user has opted out of automated decisions
        user_prefs = self.get_user_preferences(user_id)
        if user_prefs.automated_decision_opt_out:
            return DecisionResult(
                decision=None,
                requires_human_review=True,
                reason="User exercised Art 22 rights"
            )
        
        # Process decision
        score = self.model.predict(input_data)
        decision = self.apply_threshold(score)
        
        # Log for transparency and contestability
        self.log_decision(
            user_id=user_id,
            input_features=input_data,
            model_version=self.model.version,
            score=score,
            decision=decision,
            timestamp=datetime.utcnow(),
            explainability_factors=self.model.explain(input_data)
        )
        
        return DecisionResult(
            decision=decision,
            requires_human_review=False,
            explanation=self.generate_plain_language_explanation(score),
            contest_endpoint="/api/v1/decisions/{decision_id}/contest"
        )
```

### 2.8 Consent Management Schema

```sql
CREATE TABLE consent_purposes (
    purpose_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    purpose_code VARCHAR(50) UNIQUE NOT NULL,
    purpose_description TEXT NOT NULL,
    legal_basis VARCHAR(20) NOT NULL CHECK (legal_basis IN (
        'consent', 'contract', 'legal_obligation', 
        'vital_interests', 'public_task', 'legitimate_interest'
    )),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    version INTEGER DEFAULT 1
);

CREATE TABLE user_consents (
    consent_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id),
    purpose_id UUID NOT NULL REFERENCES consent_purposes(purpose_id),
    consent_given BOOLEAN NOT NULL,
    consent_method VARCHAR(50) NOT NULL, -- 'web_form', 'api', 'paper', 'verbal'
    consent_text_version INTEGER NOT NULL, -- version of privacy notice shown
    ip_address INET,
    user_agent TEXT,
    given_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    withdrawn_at TIMESTAMP WITH TIME ZONE,
    withdrawal_method VARCHAR(50),
    CONSTRAINT unique_active_consent UNIQUE (user_id, purpose_id, given_at)
);

CREATE INDEX idx_consent_user ON user_consents(user_id);
CREATE INDEX idx_consent_purpose ON user_consents(purpose_id);
CREATE INDEX idx_consent_active ON user_consents(user_id, purpose_id) 
    WHERE withdrawn_at IS NULL AND consent_given = TRUE;
```

---

## 3. Data Protection by Design and Default

### 3.1 Article 25 Requirements

Article 25 mandates two distinct obligations:

**Data Protection by Design (Art 25(1)):** Taking into account the state of the art, the cost of implementation, the nature/scope/context/purposes of processing, and the risks, the controller shall implement appropriate technical and organizational measures designed to implement data-protection principles effectively and integrate necessary safeguards into the processing.

**Data Protection by Default (Art 25(2)):** By default, only personal data necessary for each specific purpose is processed. This applies to the amount of data collected, extent of processing, period of storage, and accessibility. Specifically, personal data shall not be made accessible to an indefinite number of persons without the individual's intervention.

### 3.2 Privacy-Enhancing Technologies (PETs)

| Technology | Description | Use Case |
|---|---|---|
| Pseudonymization | Replace identifiers with pseudonyms | Analytics, research |
| Anonymization | Irreversibly remove identification ability | Published statistics |
| Differential Privacy | Add calibrated noise to query results | Aggregate analytics |
| Homomorphic Encryption | Compute on encrypted data | Cloud processing |
| Secure Multi-Party Computation | Multiple parties compute without revealing inputs | Collaborative analysis |
| Federated Learning | Train models without centralizing data | ML on sensitive data |
| Zero-Knowledge Proofs | Prove a statement without revealing underlying data | Age verification |
| Synthetic Data | Generate artificial datasets preserving statistical properties | Testing, development |
| Data Masking | Replace sensitive values with fictitious alternatives | Non-production environments |
| Tokenization | Replace data with non-sensitive tokens | Payment processing |

### 3.3 Data Flow Mapping

Every organization processing personal data must maintain a comprehensive understanding of how data flows through their systems. This is foundational for DPIAs, breach response, and SAR fulfillment.

**Data Flow Map Components:**

```
┌──────────────────────────────────────────────────────────────────┐
│                    DATA FLOW MAP TEMPLATE                          │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│  [Collection Point]     [Processing]        [Storage]             │
│  ┌─────────────┐       ┌──────────────┐   ┌──────────────┐      │
│  │ Web Form    │──────▶│ API Gateway  │──▶│ Primary DB   │      │
│  │ Mobile App  │       │ Validation   │   │ (EU-West-1)  │      │
│  │ Third Party │       │ Enrichment   │   └──────┬───────┘      │
│  └─────────────┘       └──────────────┘          │               │
│                                                    │               │
│  [Sharing]              [Analytics]               ▼               │
│  ┌─────────────┐       ┌──────────────┐   ┌──────────────┐      │
│  │ Processor A │◀──────│ Analytics    │◀──│ Data Lake    │      │
│  │ Processor B │       │ Pipeline     │   │ (anonymized) │      │
│  └─────────────┘       └──────────────┘   └──────────────┘      │
│                                                                    │
│  Data Categories: Name, Email, IP, Purchase History               │
│  Legal Basis: Contract (Art 6(1)(b))                              │
│  Retention: 3 years post last transaction                         │
│  Transfer: EU only (no third-country transfers)                   │
│  Recipients: Internal analytics team, shipping processor          │
│                                                                    │
└──────────────────────────────────────────────────────────────────┘
```

### 3.4 Data Protection Impact Assessment (DPIA)

**When Required (Art 35(3)):**
- Systematic and extensive evaluation of personal aspects (profiling with legal/significant effects)
- Large-scale processing of special categories or criminal conviction data
- Systematic monitoring of publicly accessible areas on a large scale
- Any processing appearing on the supervisory authority's mandatory DPIA list

**DPIA Methodology:**

```
Phase 1: Describe the Processing
├── Nature (what you do with data)
├── Scope (scale, categories, geography)
├── Context (internal/external factors)
└── Purpose (intended outcomes)

Phase 2: Assess Necessity and Proportionality
├── Is there a lawful basis?
├── Is the purpose achieved with minimum data?
├── How is data quality ensured?
├── What is the retention period?
└── How are data subject rights facilitated?

Phase 3: Identify and Assess Risks
├── Source of risk (internal/external threat actors)
├── Likelihood (remote, possible, probable)
├── Severity (minimal, significant, severe, maximum)
└── Impact on data subjects (not on the organization)

Phase 4: Identify Measures to Mitigate Risk
├── Technical measures (encryption, access control, etc.)
├── Organizational measures (policies, training, etc.)
├── Residual risk assessment
└── Supervisory authority consultation if residual risk remains high
```

**DPIA Template Structure:**

| Section | Content |
|---|---|
| Project Description | Purpose, scope, data categories, data subjects |
| Data Flows | Collection, storage, processing, sharing, deletion |
| Legal Basis | Identified basis per processing activity |
| Necessity & Proportionality | Justification for each data element |
| Risk Assessment | Threats, likelihood, impact matrix |
| Mitigation Measures | Controls mapped to risks |
| Residual Risk | Remaining risk after controls |
| DPO Opinion | DPO review and recommendation |
| Decision | Proceed / modify / consult supervisory authority |
| Review Schedule | When to reassess |

### 3.5 Legitimate Interest Assessment (LIA)

When relying on Art 6(1)(f), a three-part balancing test is required:

**1. Purpose Test:** Is there a legitimate interest? Is it real and present (not speculative)?

**2. Necessity Test:** Is the processing necessary for that interest? Is there a less intrusive alternative?

**3. Balancing Test:** Do the individual's interests, rights, and freedoms override the legitimate interest?

Factors in the balancing test:
- Nature of the data (sensitive increases weight toward data subject)
- Reasonable expectations of the data subject
- Status of the data subject (child, employee, etc.)
- Relationship between controller and data subject
- Impact on the data subject
- Safeguards the controller can implement

---

## 4. Technical Measures for Compliance

### 4.1 Encryption

**At Rest:**

```sql
-- PostgreSQL Transparent Data Encryption (TDE) via pgcrypto
-- Column-level encryption for sensitive fields

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Encrypt on insert
INSERT INTO users (user_id, email_encrypted, name_encrypted)
VALUES (
    gen_random_uuid(),
    pgp_sym_encrypt('user@example.com', :encryption_key),
    pgp_sym_encrypt('Jane Doe', :encryption_key)
);

-- Decrypt on read (only authorized queries)
SELECT 
    user_id,
    pgp_sym_decrypt(email_encrypted::bytea, :encryption_key) AS email,
    pgp_sym_decrypt(name_encrypted::bytea, :encryption_key) AS name
FROM users
WHERE user_id = :target_user;
```

**Key Management Principles:**
- Keys stored separately from encrypted data (HSM or cloud KMS)
- Key rotation schedule (annually minimum, immediately on compromise)
- Separate keys per data classification level
- Envelope encryption for scalability (DEK encrypted by KEK)
- Key access logging

**In Transit:**
- TLS 1.3 minimum for all connections
- Mutual TLS (mTLS) for service-to-service communication
- Certificate pinning for mobile applications
- HSTS with preload for web applications

### 4.2 Access Controls and RBAC

```sql
-- Role-Based Access Control schema for GDPR compliance

CREATE TABLE roles (
    role_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    max_data_classification VARCHAR(20) NOT NULL 
        CHECK (max_data_classification IN ('public', 'internal', 'confidential', 'restricted')),
    can_export_pii BOOLEAN DEFAULT FALSE,
    can_view_unmasked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE role_permissions (
    role_id UUID REFERENCES roles(role_id),
    resource VARCHAR(100) NOT NULL,  -- 'users.email', 'orders.*', etc.
    action VARCHAR(20) NOT NULL CHECK (action IN ('read', 'write', 'delete', 'export')),
    conditions JSONB, -- row-level security conditions
    PRIMARY KEY (role_id, resource, action)
);

CREATE TABLE user_roles (
    user_id UUID NOT NULL,
    role_id UUID REFERENCES roles(role_id),
    granted_by UUID NOT NULL,
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    justification TEXT NOT NULL,
    PRIMARY KEY (user_id, role_id)
);

-- Row-Level Security (PostgreSQL)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

CREATE POLICY customer_support_policy ON users
    FOR SELECT
    TO customer_support_role
    USING (
        -- Support can only see users in their assigned region
        region = current_setting('app.user_region')
    );

CREATE POLICY marketing_policy ON users
    FOR SELECT
    TO marketing_role
    USING (
        -- Marketing can only see users with active marketing consent
        user_id IN (
            SELECT user_id FROM user_consents 
            WHERE purpose_id = (SELECT purpose_id FROM consent_purposes WHERE purpose_code = 'marketing')
            AND consent_given = TRUE 
            AND withdrawn_at IS NULL
        )
    );
```

### 4.3 Audit Logging

Comprehensive audit logging is both a security control and a GDPR accountability requirement:

```sql
CREATE TABLE audit_log (
    log_id BIGSERIAL PRIMARY KEY,
    event_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    actor_id UUID, -- NULL for system actions
    actor_type VARCHAR(20) NOT NULL CHECK (actor_type IN ('user', 'service', 'system', 'admin')),
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(100),
    data_subject_id UUID, -- whose data was accessed/modified
    details JSONB, -- additional context (fields accessed, old/new values)
    ip_address INET,
    user_agent TEXT,
    request_id UUID, -- correlation ID
    legal_basis VARCHAR(30), -- which legal basis authorized this access
    outcome VARCHAR(10) NOT NULL CHECK (outcome IN ('success', 'failure', 'denied'))
);

-- Index for data subject access queries (SAR support)
CREATE INDEX idx_audit_subject ON audit_log(data_subject_id, event_timestamp);

-- Index for security monitoring
CREATE INDEX idx_audit_actor ON audit_log(actor_id, event_timestamp);

-- Index for compliance reporting
CREATE INDEX idx_audit_action ON audit_log(action, resource_type, event_timestamp);

-- Immutability: use append-only with no UPDATE/DELETE permissions
REVOKE UPDATE, DELETE ON audit_log FROM PUBLIC;
REVOKE UPDATE, DELETE ON audit_log FROM application_role;
```

### 4.4 Data Retention Automation

```sql
-- Retention policy configuration table
CREATE TABLE retention_policies (
    policy_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    data_category VARCHAR(50) NOT NULL,
    table_name VARCHAR(100) NOT NULL,
    retention_period INTERVAL NOT NULL,
    retention_trigger VARCHAR(50) NOT NULL, -- 'creation_date', 'last_activity', 'contract_end'
    action VARCHAR(20) NOT NULL CHECK (action IN ('delete', 'anonymize', 'archive')),
    legal_basis TEXT NOT NULL, -- why this retention period
    approved_by VARCHAR(100) NOT NULL,
    approved_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

-- Example policies
INSERT INTO retention_policies VALUES
(gen_random_uuid(), 'user_activity_logs', 'activity_logs', 
 '90 days', 'creation_date', 'delete', 
 'Data minimization - logs not needed beyond troubleshooting window', 
 'DPO', '2025-01-15'),
 
(gen_random_uuid(), 'customer_accounts', 'users', 
 '3 years', 'last_activity', 'anonymize', 
 'Legitimate interest in service improvement; anonymize after inactivity', 
 'DPO', '2025-01-15'),
 
(gen_random_uuid(), 'financial_records', 'transactions', 
 '7 years', 'creation_date', 'archive', 
 'Legal obligation - tax/accounting requirements', 
 'CFO + DPO', '2025-01-15');

-- Automated retention enforcement (scheduled job)
-- PostgreSQL function for retention processing
CREATE OR REPLACE FUNCTION enforce_retention_policies()
RETURNS TABLE(policy_id UUID, records_processed INTEGER) AS $$
DECLARE
    policy RECORD;
    affected INTEGER;
BEGIN
    FOR policy IN 
        SELECT * FROM retention_policies WHERE is_active = TRUE
    LOOP
        -- Dynamic execution based on policy action
        IF policy.action = 'delete' THEN
            EXECUTE format(
                'DELETE FROM %I WHERE %I < NOW() - $1',
                policy.table_name,
                policy.retention_trigger
            ) USING policy.retention_period;
        ELSIF policy.action = 'anonymize' THEN
            -- Call anonymization function specific to table
            EXECUTE format(
                'SELECT anonymize_%I()', 
                replace(policy.table_name, '.', '_')
            );
        END IF;
        
        GET DIAGNOSTICS affected = ROW_COUNT;
        policy_id := policy.policy_id;
        records_processed := affected;
        RETURN NEXT;
    END LOOP;
END;
$$ LANGUAGE plpgsql;
```

### 4.5 Pseudonymization Techniques

**SQL-based pseudonymization:**

```sql
-- Pseudonymization lookup table (stored separately, ideally different DB)
CREATE TABLE pseudonym_mapping (
    pseudonym_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    original_identifier_hash BYTEA NOT NULL, -- hashed for security
    data_subject_id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(original_identifier_hash)
);

-- Pseudonymized analytics table
CREATE TABLE pseudonymized_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pseudonym_id UUID NOT NULL, -- NOT a FK to avoid joining
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB NOT NULL, -- must not contain direct identifiers
    event_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    session_hash VARCHAR(64), -- hashed session, not raw
    geo_region VARCHAR(20), -- coarsened geography (country level only)
    device_category VARCHAR(20) -- 'mobile', 'desktop', 'tablet' (no fingerprinting)
);
```

**NoSQL (MongoDB) pseudonymization:**

```javascript
// Pseudonymization at write time
const pseudonymize = (userData) => {
  const pseudonymId = crypto.randomUUID();
  
  // Store mapping separately (different collection/database)
  pseudonymMappingDb.collection('mappings').insertOne({
    pseudonymId,
    originalUserId: userData.userId,
    createdAt: new Date()
  });
  
  // Store analytics data with pseudonym only
  analyticsDb.collection('events').insertOne({
    pseudonymId, // no direct identifier
    eventType: userData.eventType,
    eventData: stripPII(userData.eventData),
    timestamp: new Date(),
    geoRegion: coarsenLocation(userData.location), // country only
  });
};

// Re-identification only when legally required (e.g., SAR)
const reidentify = async (pseudonymId, legalBasis) => {
  await auditLog('reidentification_attempt', { pseudonymId, legalBasis });
  
  const mapping = await pseudonymMappingDb
    .collection('mappings')
    .findOne({ pseudonymId });
    
  return mapping?.originalUserId;
};
```

---

## 5. Cross-Border Data Transfers

### 5.1 Transfer Mechanisms (Chapter V)

The GDPR restricts transfers of personal data outside the EEA unless adequate safeguards exist. This is one of the most operationally complex aspects of compliance for global organizations.

**Hierarchy of Transfer Mechanisms:**

```
1. Adequacy Decision (Art 45)
   └─ Country/territory/sector deemed adequate by European Commission
   
2. Appropriate Safeguards (Art 46)
   ├─ Standard Contractual Clauses (SCCs) — most common
   ├─ Binding Corporate Rules (BCRs) — intra-group transfers
   ├─ Codes of Conduct (Art 40) with binding commitments
   ├─ Certification mechanisms (Art 42) with binding commitments
   └─ Ad hoc contractual clauses (requires SA authorization)
   
3. Derogations (Art 49) — ONLY for non-repetitive transfers
   ├─ Explicit consent (informed of risks)
   ├─ Necessary for contract performance
   ├─ Important public interest reasons
   ├─ Legal claims
   ├─ Vital interests
   └─ Public register data
```

### 5.2 Adequacy Decisions (as of 2025)

Countries with full adequacy:
- Andorra, Argentina, Canada (PIPEDA), Faroe Islands, Guernsey, Israel, Isle of Man, Japan, Jersey, New Zealand, Republic of Korea, Switzerland, United Kingdom, Uruguay, United States (EU-US Data Privacy Framework, limited to certified organizations)

Note: Adequacy decisions can be revoked (as happened with US Safe Harbor and Privacy Shield).

### 5.3 Standard Contractual Clauses (SCCs)

The 2021 SCCs (Commission Implementing Decision (EU) 2021/914) replaced all prior versions. Four modules:

| Module | Transfer Scenario |
|---|---|
| Module 1 | Controller to Controller |
| Module 2 | Controller to Processor |
| Module 3 | Processor to Processor |
| Module 4 | Processor to Controller |

**Requirements beyond signing SCCs:**
- Transfer Impact Assessment (TIA) — evaluate third-country law
- Supplementary measures if TIA reveals inadequate protection
- Documentation of the assessment
- Regular reassessment

### 5.4 Schrems II Implications

The CJEU judgment (C-311/18, July 2020) invalidated the EU-US Privacy Shield and imposed additional requirements on SCCs:

**Key holdings:**
1. SCCs alone are insufficient if third-country law undermines their protection
2. Controllers must assess, on a case-by-case basis, whether the third-country legal framework ensures essentially equivalent protection
3. Supplementary measures may be required

**Supplementary Measures (EDPB Recommendations 01/2020):**

Technical:
- End-to-end encryption where the importer does not hold the key
- Pseudonymization where re-identification data stays in the EEA
- Split processing across jurisdictions

Contractual:
- Obligation to challenge government access requests
- Transparency reports on government demands
- Immediate notification of inability to comply with SCCs

Organizational:
- Internal policies on handling access requests
- Adoption of recognized standards (ISO 27001, SOC 2)
- Appointment of qualified DPO in the importing country

### 5.5 EU-US Data Privacy Framework (DPF)

Adopted July 2023 (Commission Implementing Decision (EU) 2023/1795), replacing Privacy Shield. Key features:
- US organizations self-certify with Department of Commerce
- Binding safeguards limiting US intelligence access (Executive Order 14086)
- Data Protection Review Court (DPRC) for EU individuals
- Annual review mechanism by European Commission

**Limitations:**
- Only covers transfers to DPF-certified organizations
- Does not cover all US entities
- Subject to potential future CJEU challenge
- Must verify certification status before relying on DPF

### 5.6 Data Localization Requirements

| Jurisdiction | Requirement |
|---|---|
| Russia | Personal data of Russian citizens must be stored on servers physically located in Russia (Federal Law 242-FZ) |
| China | Critical Information Infrastructure Operators and processors of large volumes must store in China; security assessment for outbound transfers (PIPL Art 38-40) |
| India | Reserve Bank of India mandates payment data localization; broader requirements proposed |
| Vietnam | Certain data must be stored domestically (Cybersecurity Law Art 26) |
| Indonesia | Public electronic systems must have local data centers |
| Turkey | KVKK requires controller registration; transfers subject to adequacy or binding agreements |
| Saudi Arabia | Critical data must remain in-kingdom per PDPL |
| Nigeria | NDPR requires assessment for transfers; government data must be locally hosted |

**Architecture implication:** Multi-region deployment with data residency controls:

```yaml
# Example: Kubernetes data residency configuration
apiVersion: v1
kind: ConfigMap
metadata:
  name: data-residency-config
data:
  EU_REGION: "eu-west-1"
  US_REGION: "us-east-1"
  APAC_REGION: "ap-southeast-1"
  
  # Routing rules
  ROUTING_POLICY: |
    {
      "eu_subjects": {
        "primary_storage": "eu-west-1",
        "allowed_processing": ["eu-west-1", "eu-central-1"],
        "transfer_mechanism": null
      },
      "us_subjects_dpf": {
        "primary_storage": "us-east-1",
        "allowed_processing": ["us-east-1", "eu-west-1"],
        "transfer_mechanism": "dpf_certification"
      },
      "china_subjects": {
        "primary_storage": "cn-north-1",
        "allowed_processing": ["cn-north-1"],
        "transfer_mechanism": "security_assessment_required"
      }
    }
```

---

## 6. Data Breach Notification

### 6.1 Article 33 — Notification to Supervisory Authority

**When:** Upon becoming aware of a personal data breach, unless the breach is unlikely to result in a risk to the rights and freedoms of natural persons.

**Timeline:** Without undue delay, not later than 72 hours after becoming aware. If notification exceeds 72 hours, must include reasons for delay.

**Content of notification:**
1. Nature of the breach (categories and approximate number of data subjects, categories and approximate number of records)
2. Name and contact details of DPO or other contact point
3. Likely consequences of the breach
4. Measures taken or proposed to address the breach, including mitigation

### 6.2 Article 34 — Notification to Data Subjects

**When:** The breach is likely to result in a HIGH risk to the rights and freedoms of natural persons.

**Exceptions (notification not required):**
- Controller implemented appropriate protection measures rendering data unintelligible (e.g., encryption)
- Subsequent measures ensure high risk is no longer likely to materialize
- It would involve disproportionate effort (use public communication instead)

### 6.3 Breach Assessment Criteria

```
┌─────────────────────────────────────────────────────────────┐
│              BREACH RISK ASSESSMENT MATRIX                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Severity Factors:                                            │
│  ┌─────────────────────────────────────────────┐             │
│  │ • Type of breach (C/I/A)                     │             │
│  │ • Nature of data (sensitive = higher)         │             │
│  │ • Volume of records affected                  │             │
│  │ • Ease of identification of subjects          │             │
│  │ • Severity of consequences for subjects       │             │
│  │ • Special characteristics of subjects         │             │
│  │   (children, vulnerable persons)              │             │
│  │ • Number of affected individuals              │             │
│  │ • Special characteristics of controller       │             │
│  │   (medical, financial)                        │             │
│  └─────────────────────────────────────────────┘             │
│                                                               │
│  Risk Level Determination:                                    │
│  ┌──────────┬───────────────┬────────────────────┐          │
│  │ Level    │ SA Notify?    │ Subject Notify?     │          │
│  ├──────────┼───────────────┼────────────────────┤          │
│  │ Unlikely │ No            │ No                  │          │
│  │ Risk     │ Yes (72h)     │ No                  │          │
│  │ High Risk│ Yes (72h)     │ Yes (without delay) │          │
│  └──────────┴───────────────┴────────────────────┘          │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 6.4 Breach Notification Workflow

```python
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional

class BreachSeverity(Enum):
    UNLIKELY_RISK = "unlikely"      # No notification required
    RISK = "risk"                   # SA notification within 72h
    HIGH_RISK = "high_risk"        # SA + data subject notification

class BreachType(Enum):
    CONFIDENTIALITY = "confidentiality"  # Unauthorized disclosure/access
    INTEGRITY = "integrity"              # Unauthorized alteration
    AVAILABILITY = "availability"        # Loss of access/destruction

@dataclass
class BreachRecord:
    breach_id: str
    detected_at: datetime
    breach_type: BreachType
    description: str
    data_categories: list[str]
    estimated_subjects: int
    estimated_records: int
    severity: BreachSeverity
    containment_actions: list[str] = field(default_factory=list)
    root_cause: Optional[str] = None
    sa_notified_at: Optional[datetime] = None
    subjects_notified_at: Optional[datetime] = None
    
    @property
    def notification_deadline(self) -> datetime:
        return self.detected_at + timedelta(hours=72)
    
    @property
    def is_overdue(self) -> bool:
        if self.severity in (BreachSeverity.RISK, BreachSeverity.HIGH_RISK):
            return datetime.utcnow() > self.notification_deadline and self.sa_notified_at is None
        return False

class BreachRegister:
    """Maintained per Art 33(5) — all breaches, regardless of notification."""
    
    def __init__(self, storage_backend):
        self.storage = storage_backend
    
    def record_breach(self, breach: BreachRecord) -> str:
        # Store with full audit trail
        self.storage.insert({
            **vars(breach),
            'recorded_at': datetime.utcnow(),
            'recorded_by': self._get_current_user()
        })
        
        # Trigger alerts based on severity
        if breach.severity == BreachSeverity.HIGH_RISK:
            self._alert_dpo_immediate(breach)
            self._alert_executive_team(breach)
            self._initiate_subject_notification_workflow(breach)
        elif breach.severity == BreachSeverity.RISK:
            self._alert_dpo_immediate(breach)
            self._schedule_sa_notification(breach)
        
        return breach.breach_id
    
    def generate_sa_notification(self, breach_id: str) -> dict:
        """Generate supervisory authority notification per Art 33(3)."""
        breach = self.storage.get(breach_id)
        return {
            "nature_of_breach": {
                "type": breach.breach_type.value,
                "description": breach.description,
                "data_categories": breach.data_categories,
                "approximate_subjects": breach.estimated_subjects,
                "approximate_records": breach.estimated_records
            },
            "dpo_contact": self._get_dpo_details(),
            "likely_consequences": self._assess_consequences(breach),
            "measures_taken": breach.containment_actions,
            "measures_proposed": self._get_remediation_plan(breach)
        }
```

### 6.5 Breach Register Template

Per Art 33(5), controllers must document ALL personal data breaches regardless of whether notification is required:

| Field | Content |
|---|---|
| Breach ID | Unique identifier |
| Date/time of breach | When it occurred (if known) |
| Date/time of detection | When the controller became aware |
| Description | What happened |
| Breach type | Confidentiality / Integrity / Availability |
| Data categories affected | Names, emails, financial, health, etc. |
| Data subject categories | Customers, employees, minors, etc. |
| Approximate number of subjects | Range or exact |
| Approximate number of records | Range or exact |
| Likely consequences | Concrete impact assessment |
| Containment measures | Actions taken to stop the breach |
| Remediation measures | Actions to prevent recurrence |
| Risk assessment | Unlikely risk / Risk / High risk |
| SA notification | Date/time/reference (or justification for not notifying) |
| Data subject notification | Date/method (or justification for not notifying) |
| Root cause | Technical/organizational failure analysis |
| Lessons learned | Improvements identified |

---

## 7. DPO Role and Compliance Program

### 7.1 When a DPO Is Required (Art 37)

Mandatory appointment when:
- Processing carried out by a public authority or body (except courts in judicial capacity)
- Core activities require regular and systematic monitoring of data subjects on a large scale
- Core activities consist of large-scale processing of special categories (Art 9) or criminal conviction data (Art 10)

"Core activities" = primary business activities, not supporting functions like HR/IT (though these may still warrant a DPO given scale).

### 7.2 DPO Position Requirements (Art 38-39)

**Independence guarantees:**
- No instructions regarding exercise of DPO tasks
- Cannot be dismissed or penalized for performing DPO tasks
- Reports directly to highest management level
- No conflict of interest with other tasks (cannot be CISO who makes data processing decisions)

**Minimum tasks (Art 39):**
- Inform and advise controller/processor and employees
- Monitor compliance with GDPR and internal policies
- Provide advice on DPIA and monitor its performance
- Cooperate with and act as contact for supervisory authority
- Have regard to risk associated with processing operations

### 7.3 Records of Processing Activities (Art 30)

**Controller's record must contain:**

| Field | Description |
|---|---|
| Controller identity | Name and contact details of controller, joint controllers, DPO |
| Purposes | Purpose of each processing activity |
| Data subjects | Categories of data subjects |
| Data categories | Categories of personal data |
| Recipients | Categories of recipients (including third countries/international organizations) |
| Transfers | Third-country transfers with safeguard documentation |
| Retention | Envisaged time limits for erasure per category |
| Security | General description of technical/organizational security measures |

**Processor's record must contain:**
- Processor identity and details
- Categories of processing on behalf of each controller
- Transfers to third countries
- General security measures description

```json
// Records of Processing Activities (RoPA) — example entry
{
  "processing_activity": "Customer Relationship Management",
  "controller": {
    "name": "Example Corp",
    "address": "123 Data Street, Berlin, DE",
    "dpo_contact": "dpo@example.com"
  },
  "purposes": [
    "Customer account management",
    "Order fulfillment",
    "Customer support"
  ],
  "legal_basis": "Art 6(1)(b) — contract performance",
  "data_subjects": ["Customers", "Prospective customers"],
  "data_categories": [
    "Name", "Email", "Phone", "Address",
    "Purchase history", "Support tickets"
  ],
  "recipients": [
    {"name": "Shipping Provider X", "role": "processor", "country": "DE"},
    {"name": "Email Service Y", "role": "processor", "country": "US", "transfer_mechanism": "DPF"}
  ],
  "retention": {
    "active_customers": "Duration of relationship + 3 years",
    "inactive_customers": "3 years after last activity, then anonymize"
  },
  "security_measures": [
    "Encryption at rest (AES-256)",
    "TLS 1.3 in transit",
    "Role-based access control",
    "Quarterly access reviews",
    "Annual penetration testing"
  ],
  "dpia_required": false,
  "last_reviewed": "2025-01-15",
  "next_review": "2026-01-15"
}
```

### 7.4 Processor Agreements (Art 28)

Every processor relationship requires a binding contract containing:

1. Subject-matter and duration of processing
2. Nature and purpose of processing
3. Type of personal data and categories of data subjects
4. Obligations and rights of the controller
5. Specific processor obligations:
   - Process only on documented instructions
   - Ensure confidentiality commitments for personnel
   - Implement appropriate security measures (Art 32)
   - Sub-processor restrictions (prior authorization + flow-down of obligations)
   - Assist controller with data subject rights requests
   - Assist with security obligations (Art 32-36)
   - Delete or return all data at end of service
   - Make available all information for audits

### 7.5 Vendor Assessment Framework

```
┌─────────────────────────────────────────────────────────┐
│           VENDOR PRIVACY ASSESSMENT CRITERIA              │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  1. Legal Framework                                       │
│     □ Data processing agreement in place                 │
│     □ Sub-processor list provided and maintained         │
│     □ Transfer mechanisms documented                     │
│     □ Incident notification procedures defined           │
│                                                           │
│  2. Security Controls                                     │
│     □ ISO 27001 / SOC 2 Type II certification           │
│     □ Encryption at rest and in transit                  │
│     □ Access control with least privilege                │
│     □ Regular penetration testing (evidence provided)    │
│     □ Vulnerability management program                   │
│     □ Incident response plan tested                     │
│                                                           │
│  3. Data Handling                                         │
│     □ Data classification implemented                    │
│     □ Retention policies documented and enforced         │
│     □ Deletion/return capabilities demonstrated          │
│     □ Backup encryption confirmed                       │
│     □ No commingling with other customer data           │
│                                                           │
│  4. Operational Maturity                                  │
│     □ Business continuity plan                          │
│     □ Disaster recovery tested annually                 │
│     □ Employee training on data protection              │
│     □ Change management process                         │
│     □ Physical security (if applicable)                 │
│                                                           │
│  5. Rights Fulfillment                                    │
│     □ Can support SAR within timelines                  │
│     □ Can execute erasure requests                      │
│     □ Can restrict processing on request                │
│     □ Provides audit access or reports                  │
│                                                           │
│  Risk Rating: LOW / MEDIUM / HIGH / CRITICAL            │
│  Review Frequency: Annual / Semi-annual / Quarterly     │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

---

## 8. Other Privacy Regulations

### 8.1 Comparison Matrix

| Feature | GDPR (EU) | CCPA/CPRA (CA) | LGPD (Brazil) | PIPEDA (Canada) | POPIA (South Africa) | PDPA (Singapore) | PIPL (China) |
|---|---|---|---|---|---|---|---|
| **Effective** | May 2018 | Jan 2020 / Jan 2023 | Sep 2020 | Apr 2000 | Jul 2021 | Feb 2021 (full) | Nov 2021 |
| **Scope** | EEA + monitoring/offering | CA residents | Brazil processing | Commercial activity (Canada) | SA processing | Singapore processing | China processing |
| **Extraterritorial** | Yes | Yes (CA residents) | Yes | Limited | Yes | Limited | Yes |
| **Legal Basis Req'd** | Yes (6 bases) | No (opt-out model) | Yes (10 bases) | Knowledge + consent | Yes (8 bases) | Consent + exceptions | Yes (7+ bases) |
| **Consent** | Opt-in | Opt-out (sale/share) | Opt-in | Knowledge + consent | Opt-in (with exceptions) | Opt-in | Separate consent for sensitive |
| **Right to Access** | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| **Right to Delete** | Yes (exceptions) | Yes (exceptions) | Yes | Limited | Yes | Withdrawal + deletion | Yes |
| **Right to Port** | Yes | Yes (limited) | Yes | Implied | No | Yes | Yes |
| **Right to Object** | Yes | Opt-out of sale/share | Yes | Withdraw consent | Yes | Withdrawal | Yes |
| **Data Localization** | No (transfer rules) | No | No (adequacy rules) | No (accountability) | No (transfer rules) | No (transfer rules) | Yes (CIIO + volume thresholds) |
| **Breach Notify** | 72h to SA | "Expeditiously" | Reasonable time to SA | ASAP to OPC | ASAP to regulator | 3 days to PDPC | Immediately to authority |
| **DPO Required** | Conditional | No (Privacy agency) | Yes (DPO/encarregado) | Optional | Conditional | Yes (DPO) | Yes (DPO/personal info protection officer) |
| **Max Fine** | €20M / 4% global | $7,500 per intentional violation | 2% revenue (R$50M cap) | C$100K per violation | R10M / imprisonment | S$1M | ¥50M / 5% revenue / criminal |
| **Regulator** | National DPAs | CPPA (CA) | ANPD | OPC | Information Regulator | PDPC | CAC / local authorities |

### 8.2 CCPA/CPRA (California)

The California Consumer Privacy Act (2020) as amended by the California Privacy Rights Act (2023) creates an opt-out framework fundamentally different from GDPR:

**Key differences from GDPR:**
- No requirement for legal basis (processing is permitted by default)
- Focus on "sale" and "sharing" of personal information
- Broader definition of personal information
- "Do Not Sell or Share My Personal Information" link required
- California Privacy Protection Agency (CPPA) enforcement
- Private right of action for data breaches (statutory damages $100-$750 per consumer per incident)
- Sensitive personal information category with right to limit use
- No equivalent of legitimate interest balancing test

**CPRA additions (effective 2023):**
- Right to correct inaccurate information
- Right to limit use of sensitive personal information
- New agency (CPPA) with rulemaking authority
- Automated decision-making opt-out rights
- Annual cybersecurity audits for high-risk businesses
- Risk assessments for processing activities

### 8.3 LGPD (Brazil)

Lei Geral de Proteção de Dados closely mirrors GDPR with some notable differences:

**Ten legal bases (Art 7):**
1. Consent
2. Legal/regulatory obligation
3. Public administration (public policies)
4. Research (anonymized when possible)
5. Contract performance
6. Exercise of rights in judicial/arbitral/administrative proceedings
7. Protection of life/physical safety
8. Health protection
9. Legitimate interest (with balancing test)
10. Credit protection

**Key differences from GDPR:**
- Legitimate interest explicitly includes credit protection
- ANPD (Autoridade Nacional de Proteção de Dados) is the sole regulator
- International transfer requires specific ANPD-approved mechanisms
- No equivalent of the "one-stop-shop" mechanism
- Penalty cap at 2% of revenue (max R$50M per infraction)
- DPO (encarregado) always required for controllers

### 8.4 PIPEDA (Canada)

The Personal Information Protection and Electronic Documents Act is based on the CSA Model Code principles:

**Ten fair information principles:**
1. Accountability
2. Identifying purposes
3. Consent (knowledge and consent)
4. Limiting collection
5. Limiting use, disclosure, retention
6. Accuracy
7. Safeguards
8. Openness
9. Individual access
10. Challenging compliance

**Key features:**
- Adequate under GDPR (for commercial activities)
- Consent framework more flexible than GDPR (implied consent possible)
- Breach notification to OPC and affected individuals when "real risk of significant harm"
- Proposed replacement: Consumer Privacy Protection Act (CPPA) / Digital Charter Implementation Act (still in legislative process)

### 8.5 POPIA (South Africa)

The Protection of Personal Information Act:
- Eight conditions for lawful processing
- Information Regulator as enforcement body
- Criminal liability possible (imprisonment up to 10 years)
- Applies to domiciled and non-domiciled entities processing SA data
- Responsible party (controller equivalent) must register with Information Regulator

### 8.6 PDPA (Singapore and Thailand)

**Singapore PDPA:**
- Personal Data Protection Commission (PDPC) enforcement
- Consent-based with exceptions (business improvement, research, publicly available)
- Data Protection Officer mandatory
- Do Not Call Registry integration
- Mandatory breach notification (3 calendar days to PDPC)
- Data portability framework (in force 2024)

**Thailand PDPA:**
- Closely mirrors GDPR structure
- Six legal bases similar to GDPR
- Sensitive data category with explicit consent requirement
- PDPC as enforcement authority
- Cross-border transfers subject to adequacy or safeguards
- Maximum fine THB 5 million + criminal penalties

### 8.7 China PIPL (Personal Information Protection Law)

The most restrictive major privacy law currently in force:

**Key requirements:**
- Separate consent for: sensitive data, cross-border transfers, public disclosure, third-party provision
- Mandatory security assessment for: CIIO transfers abroad, transfers exceeding volume thresholds (>1M individuals or >100K records/year)
- Personal information protection officer required above thresholds
- Designated representatives required for foreign data handlers
- Government access rights explicitly preserved
- Data localization for Critical Information Infrastructure Operators
- Standard contract filing with provincial-level CAC

**Cross-border transfer mechanisms (Art 38):**
1. Security assessment by CAC (mandatory for CIIOs and high-volume)
2. Personal information protection certification
3. Standard contracts filed with authorities
4. Conditions specified in other laws/regulations

---

## 9. Privacy Engineering in Practice

### 9.1 Consent Management Platforms

**Architecture of a CMP:**

```
┌─────────────────────────────────────────────────────────────────┐
│                    CONSENT MANAGEMENT ARCHITECTURE                │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐   │
│  │ Consent UI   │───▶│ Consent API  │───▶│ Consent Store    │   │
│  │ (Banner/     │    │ (Validation, │    │ (Purpose, User,  │   │
│  │  Preference  │    │  Recording)  │    │  Timestamp, Proof│   │
│  │  Center)     │    │              │    │                  │   │
│  └──────────────┘    └──────┬───────┘    └──────────────────┘   │
│                              │                                    │
│                              ▼                                    │
│                    ┌──────────────────┐                           │
│                    │ Signal Dispatch  │                           │
│                    │ (TCF, GPP, IAB)  │                           │
│                    └────────┬─────────┘                           │
│                             │                                     │
│              ┌──────────────┼──────────────┐                     │
│              ▼              ▼              ▼                      │
│  ┌───────────────┐ ┌──────────────┐ ┌─────────────────┐        │
│  │ Tag Manager   │ │ Analytics    │ │ Ad Platforms     │        │
│  │ (conditional  │ │ (respect     │ │ (signal consent  │        │
│  │  firing)      │ │  consent)    │ │  status)         │        │
│  └───────────────┘ └──────────────┘ └─────────────────┘        │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

**Platform comparison:**

| Platform | Strengths | Considerations |
|---|---|---|
| OneTrust | Enterprise-grade, comprehensive privacy program management, cookie scanning | Cost (enterprise pricing), complexity for simple sites |
| Cookiebot | Easy implementation, automatic scanning, free tier | Limited enterprise features, CMP-focused only |
| Didomi | Strong UI customization, performance-focused | Smaller ecosystem than OneTrust |
| Osano | Simple interface, consent monitoring | Less granular configuration |
| Usercentrics | Strong TCF support, Google-certified | European-focused |
| Custom-built | Full control, no vendor dependency | Development cost, maintenance burden, compliance risk |

### 9.2 Cookie Consent Implementation

**Technical Consent Framework (TCF 2.2 compliant):**

```javascript
// Consent state management (simplified)
const ConsentManager = {
  PURPOSES: {
    STRICTLY_NECESSARY: 1,  // No consent needed
    PERFORMANCE: 2,         // Analytics
    FUNCTIONAL: 3,          // Preferences
    TARGETING: 4,           // Advertising
    SOCIAL_MEDIA: 5         // Social sharing
  },
  
  getConsent() {
    const consentString = this.readConsentCookie();
    if (!consentString) return null;
    return this.parseConsent(consentString);
  },
  
  setConsent(purposes) {
    const consentRecord = {
      version: '2.2',
      created: new Date().toISOString(),
      lastUpdated: new Date().toISOString(),
      purposes: purposes, // {2: true, 3: false, 4: false, 5: false}
      legitimateInterests: {},
      vendorConsents: {},
      tcString: this.encodeTCString(purposes)
    };
    
    // Store consent
    this.writeConsentCookie(consentRecord);
    
    // Server-side record for accountability
    this.recordConsentServer(consentRecord);
    
    // Signal to tag manager / ad tech
    this.dispatchConsentSignal(consentRecord);
  },
  
  // Block scripts until consent obtained
  conditionalLoad(purpose, scriptUrl) {
    const consent = this.getConsent();
    if (consent && consent.purposes[purpose]) {
      const script = document.createElement('script');
      script.src = scriptUrl;
      document.head.appendChild(script);
    }
  }
};
```

### 9.3 Privacy-Preserving Analytics

**Server-side tracking (first-party data collection):**

```
Traditional (third-party):
Browser → Third-party pixel → External analytics server
  ↑ Blocked by: ad blockers, ITP, ETP, consent requirements

Server-side (first-party):
Browser → Your server → Your analytics pipeline
  ↑ Benefits: reliable collection, no third-party cookies,
    reduced consent surface (may fall under legitimate interest)
```

**Implementation considerations:**
- Still requires legal basis (legitimate interest assessment needed)
- IP anonymization/truncation before storage
- Session identifiers rotated frequently
- No cross-site tracking
- Data minimization at collection point
- Respect DNT/GPC signals (legally required in some jurisdictions)

### 9.4 Differential Privacy

Differential privacy provides mathematical guarantees that individual records cannot be identified from aggregate queries:

**Core concept:** Adding calibrated noise to query results such that the presence or absence of any single individual's data does not significantly affect the output.

**Epsilon (ε) — privacy budget:**
- ε → 0: Maximum privacy (more noise, less utility)
- ε → ∞: No privacy (raw data)
- Practical range: 0.1 to 10 (domain-dependent)

```python
import numpy as np

def laplace_mechanism(true_value: float, sensitivity: float, epsilon: float) -> float:
    """
    Add Laplace noise to a query result.
    
    Args:
        true_value: The actual query result
        sensitivity: Maximum change in output from adding/removing one record
        epsilon: Privacy parameter (lower = more private)
    
    Returns:
        Noised result satisfying ε-differential privacy
    """
    scale = sensitivity / epsilon
    noise = np.random.laplace(0, scale)
    return true_value + noise

# Example: Count of users in a city
true_count = 1547
# Sensitivity for count query = 1 (one person changes count by at most 1)
private_count = laplace_mechanism(true_count, sensitivity=1, epsilon=1.0)
# Result: approximately 1547 ± noise

# Example: Average salary (bounded)
true_average = 75000.0
# Sensitivity for bounded average = (max - min) / n
salary_sensitivity = (200000 - 20000) / 1000  # 180
private_average = laplace_mechanism(true_average, sensitivity=salary_sensitivity, epsilon=0.5)
```

**Practical deployments:**
- Apple: Device-level differential privacy for keyboard suggestions, health data
- Google: RAPPOR for Chrome usage statistics
- US Census Bureau: 2020 Census uses differential privacy
- Microsoft: Telemetry collection in Windows

### 9.5 Federated Learning

Train machine learning models without centralizing raw data:

```
┌─────────────────────────────────────────────────────────┐
│              FEDERATED LEARNING ARCHITECTURE              │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  Central Server                                           │
│  ┌────────────────────────────────────────────────┐      │
│  │ 1. Distribute global model                      │      │
│  │ 2. Receive model updates (NOT raw data)         │      │
│  │ 3. Aggregate updates (FedAvg / FedSGD)         │      │
│  │ 4. Update global model                          │      │
│  │ 5. Repeat until convergence                     │      │
│  └──────────┬────────────────────────┬────────────┘      │
│             │                        │                    │
│       ┌─────┘                        └─────┐             │
│       ▼                                    ▼             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ Client A │  │ Client B │  │ Client C │              │
│  │ (local   │  │ (local   │  │ (local   │              │
│  │  data     │  │  data     │  │  data     │              │
│  │  stays    │  │  stays    │  │  stays    │              │
│  │  local)   │  │  local)   │  │  local)   │              │
│  └──────────┘  └──────────┘  └──────────┘              │
│                                                           │
│  Privacy enhancements:                                    │
│  • Secure aggregation (server only sees sum)             │
│  • Differential privacy on updates                       │
│  • Client selection randomization                        │
│  • Gradient clipping to bound individual influence       │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

**GDPR implications:** Federated learning reduces privacy risk but does NOT automatically exempt from GDPR. Model updates can theoretically leak information about training data (membership inference attacks). Combine with differential privacy for stronger guarantees.

### 9.6 Secure Multi-Party Computation (SMPC)

Allows multiple parties to jointly compute a function over their inputs without revealing those inputs to each other:

**Use cases in privacy:**
- Salary benchmarking across companies without revealing individual salaries
- Joint fraud detection across banks without sharing customer data
- Medical research across hospitals without centralizing patient records
- Privacy-preserving advertising measurement

**Protocols:** Secret sharing (Shamir's), garbled circuits (Yao's), oblivious transfer.

**Practical limitations:**
- Computation overhead (orders of magnitude slower than plaintext)
- Communication complexity between parties
- Requires honest majority in some protocols
- Not suitable for all computation types

### 9.7 Homomorphic Encryption Overview

Computation on encrypted data without decryption:

| Scheme Type | Operations | Performance | Use Case |
|---|---|---|---|
| Partially HE (PHE) | Either + or × (not both) | Fast | Aggregation (e.g., Paillier for sum) |
| Somewhat HE (SHE) | Limited + and × | Moderate | Low-depth computations |
| Fully HE (FHE) | Arbitrary + and × | Very slow (>1000x overhead) | General computation (still largely research) |

**Practical today:** PHE for specific operations (encrypted aggregation, encrypted search). FHE remains impractical for general-purpose use but advancing rapidly (Microsoft SEAL, IBM HELib, Zama TFHE).

### 9.8 Global Privacy Control (GPC) and Do Not Track

**GPC (Global Privacy Control):**
- Machine-readable signal (`Sec-GPC: 1` HTTP header)
- Legally recognized under CCPA/CPRA as valid opt-out of sale/sharing
- Browser extensions and some browsers (Brave, Firefox) support natively
- Controllers must respect in California; growing recognition elsewhere

**Implementation requirement:**

```javascript
// Check for GPC signal
if (navigator.globalPrivacyControl) {
  // Must treat as opt-out of sale/share in California
  // Should treat as objection signal under GDPR (debated)
  consentManager.setDefaultOptOut('sale_share');
  consentManager.recordGPCSignal();
}
```

---

## 10. Lab Exercises

### Lab 1: GDPR-Compliant Data Pipeline with Automated Retention

**Objective:** Build a data ingestion pipeline that enforces purpose limitation, data minimization, and automated retention.

**Architecture:**

```
Source Data → Ingestion API → Classification → Storage → Retention Scheduler → Deletion/Anonymization
```

**Step 1: Define schema with privacy metadata**

```sql
-- Data classification labels
CREATE TYPE data_sensitivity AS ENUM ('public', 'internal', 'confidential', 'restricted');
CREATE TYPE legal_basis_type AS ENUM (
    'consent', 'contract', 'legal_obligation', 
    'vital_interests', 'public_task', 'legitimate_interest'
);

-- Master data catalog (privacy-aware)
CREATE TABLE data_catalog (
    catalog_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_name VARCHAR(100) NOT NULL,
    column_name VARCHAR(100) NOT NULL,
    is_personal_data BOOLEAN NOT NULL DEFAULT FALSE,
    is_special_category BOOLEAN NOT NULL DEFAULT FALSE,
    sensitivity data_sensitivity NOT NULL DEFAULT 'internal',
    purpose TEXT NOT NULL,
    legal_basis legal_basis_type NOT NULL,
    retention_days INTEGER NOT NULL,
    anonymization_method VARCHAR(50), -- 'hash', 'generalize', 'suppress', 'noise'
    UNIQUE(table_name, column_name)
);

-- Populate catalog
INSERT INTO data_catalog VALUES
(gen_random_uuid(), 'events', 'user_id', TRUE, FALSE, 'confidential', 
 'Service delivery', 'contract', 365, 'hash'),
(gen_random_uuid(), 'events', 'ip_address', TRUE, FALSE, 'confidential', 
 'Security monitoring', 'legitimate_interest', 90, 'suppress'),
(gen_random_uuid(), 'events', 'event_type', FALSE, FALSE, 'internal', 
 'Analytics', 'legitimate_interest', 730, NULL),
(gen_random_uuid(), 'events', 'timestamp', FALSE, FALSE, 'internal', 
 'Analytics', 'legitimate_interest', 730, NULL);
```

**Step 2: Ingestion API with purpose enforcement**

```python
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Optional
import hashlib

@dataclass
class PrivacyPolicy:
    purpose: str
    legal_basis: str
    retention_days: int
    requires_consent: bool
    anonymization_method: Optional[str]

FIELD_POLICIES: dict[str, PrivacyPolicy] = {
    "user_id": PrivacyPolicy(
        purpose="service_delivery",
        legal_basis="contract",
        retention_days=365,
        requires_consent=False,
        anonymization_method="hash"
    ),
    "email": PrivacyPolicy(
        purpose="communication",
        legal_basis="contract",
        retention_days=365,
        requires_consent=False,
        anonymization_method="suppress"
    ),
    "ip_address": PrivacyPolicy(
        purpose="security",
        legal_basis="legitimate_interest",
        retention_days=90,
        requires_consent=False,
        anonymization_method="truncate"
    ),
    "marketing_preferences": PrivacyPolicy(
        purpose="marketing",
        legal_basis="consent",
        retention_days=730,
        requires_consent=True,
        anonymization_method="suppress"
    ),
}

class PrivacyAwareIngestion:
    def ingest_event(self, raw_event: dict, user_consents: dict) -> dict:
        """
        Ingest event data respecting purpose limitation and data minimization.
        """
        processed_event = {
            "_metadata": {
                "ingested_at": datetime.now(timezone.utc).isoformat(),
                "retention_expires": {},
                "purposes": set()
            }
        }
        
        for field, value in raw_event.items():
            policy = FIELD_POLICIES.get(field)
            
            if policy is None:
                # Unknown field — reject per data minimization
                continue
            
            # Check consent if required
            if policy.requires_consent:
                if not user_consents.get(policy.purpose, False):
                    continue  # No consent — do not process
            
            # Store with retention metadata
            processed_event[field] = value
            processed_event["_metadata"]["retention_expires"][field] = (
                datetime.now(timezone.utc).timestamp() + (policy.retention_days * 86400)
            )
            processed_event["_metadata"]["purposes"].add(policy.purpose)
        
        processed_event["_metadata"]["purposes"] = list(processed_event["_metadata"]["purposes"])
        return processed_event
    
    def apply_retention(self, event: dict) -> dict:
        """Remove fields past their retention period."""
        now = datetime.now(timezone.utc).timestamp()
        expired_fields = []
        
        for field, expiry in event.get("_metadata", {}).get("retention_expires", {}).items():
            if now > expiry:
                expired_fields.append(field)
        
        for field in expired_fields:
            policy = FIELD_POLICIES.get(field)
            if policy and policy.anonymization_method == "hash":
                event[field] = hashlib.sha256(str(event[field]).encode()).hexdigest()[:16]
            elif policy and policy.anonymization_method == "truncate":
                # Truncate IP to /24
                if field == "ip_address" and event.get(field):
                    parts = event[field].split(".")
                    event[field] = f"{parts[0]}.{parts[1]}.{parts[2]}.0"
            else:
                event[field] = None
            
            del event["_metadata"]["retention_expires"][field]
        
        return event
```

**Step 3: Retention scheduler (cron job)**

```python
class RetentionScheduler:
    """Runs daily to enforce retention policies across all data stores."""
    
    def run(self):
        policies = self.db.query("SELECT * FROM data_catalog WHERE retention_days IS NOT NULL")
        
        for policy in policies:
            expired_cutoff = datetime.now(timezone.utc) - timedelta(days=policy.retention_days)
            
            if policy.anonymization_method == 'suppress':
                # Set to NULL
                self.db.execute(f"""
                    UPDATE {policy.table_name} 
                    SET {policy.column_name} = NULL 
                    WHERE created_at < %s AND {policy.column_name} IS NOT NULL
                """, [expired_cutoff])
                
            elif policy.anonymization_method == 'hash':
                # Replace with irreversible hash
                self.db.execute(f"""
                    UPDATE {policy.table_name} 
                    SET {policy.column_name} = encode(
                        sha256({policy.column_name}::bytea), 'hex'
                    )::VARCHAR(16)
                    WHERE created_at < %s 
                    AND {policy.column_name} NOT LIKE 'ANON_%'
                """, [expired_cutoff])
            
            elif policy.anonymization_method == 'generalize':
                # Domain-specific generalization (e.g., age → age range)
                pass
            
            affected = self.db.rowcount
            self.log_retention_action(policy, affected, expired_cutoff)
```

---

### Lab 2: Right-to-Erasure Across Microservices

**Objective:** Implement coordinated erasure across a microservice architecture with eventual consistency guarantees.

**Architecture:**

```
┌─────────────────────────────────────────────────────────────────┐
│                ERASURE ORCHESTRATION SYSTEM                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐         ┌──────────────────────┐              │
│  │ Erasure API  │────────▶│ Erasure Orchestrator │              │
│  │ (receives    │         │ (saga pattern)        │              │
│  │  request)    │         └──────────┬───────────┘              │
│  └──────────────┘                    │                           │
│                                      │ Publish: ErasureRequested │
│                         ┌────────────┼────────────────┐         │
│                         ▼            ▼                ▼         │
│              ┌──────────────┐ ┌──────────┐ ┌──────────────┐    │
│              │ User Service │ │ Order    │ │ Analytics    │    │
│              │ (primary PII)│ │ Service  │ │ Service      │    │
│              └──────┬───────┘ └────┬─────┘ └──────┬───────┘    │
│                     │              │              │              │
│                     ▼              ▼              ▼              │
│              ┌──────────────┐ ┌──────────┐ ┌──────────────┐    │
│              │ ErasureAcked │ │ Erasure  │ │ ErasureAcked │    │
│              │              │ │ Acked    │ │              │    │
│              └──────────────┘ └──────────┘ └──────────────┘    │
│                     │              │              │              │
│                     └──────────────┼──────────────┘              │
│                                    ▼                             │
│                         ┌──────────────────┐                    │
│                         │ Erasure Complete │                    │
│                         │ (all ACKs recv'd)│                    │
│                         └──────────────────┘                    │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

**Implementation:**

```python
import uuid
from datetime import datetime, timezone, timedelta
from enum import Enum

class ErasureStatus(Enum):
    REQUESTED = "requested"
    IN_PROGRESS = "in_progress"
    PARTIALLY_COMPLETE = "partially_complete"
    COMPLETE = "complete"
    FAILED = "failed"
    BLOCKED = "blocked"  # Legal hold or exception applies

class ErasureOrchestrator:
    # All services that hold personal data
    REGISTERED_SERVICES = [
        {"name": "user-service", "queue": "erasure.user-service", "timeout_hours": 24},
        {"name": "order-service", "queue": "erasure.order-service", "timeout_hours": 24},
        {"name": "analytics-service", "queue": "erasure.analytics-service", "timeout_hours": 48},
        {"name": "email-service", "queue": "erasure.email-service", "timeout_hours": 12},
        {"name": "backup-service", "queue": "erasure.backup-service", "timeout_hours": 72},
        {"name": "search-index", "queue": "erasure.search-index", "timeout_hours": 6},
        {"name": "cdn-cache", "queue": "erasure.cdn-cache", "timeout_hours": 6},
    ]
    
    def initiate_erasure(self, user_id: str, request_source: str) -> str:
        """
        Initiate erasure request with saga coordination.
        Returns erasure_request_id for tracking.
        """
        request_id = str(uuid.uuid4())
        
        # Check for legal holds or exceptions (Art 17(3))
        exceptions = self.check_erasure_exceptions(user_id)
        if exceptions:
            self.record_erasure_request(
                request_id=request_id,
                user_id=user_id,
                status=ErasureStatus.BLOCKED,
                reason=f"Exception applies: {exceptions}",
                source=request_source
            )
            return request_id
        
        # Record the request
        self.record_erasure_request(
            request_id=request_id,
            user_id=user_id,
            status=ErasureStatus.IN_PROGRESS,
            source=request_source,
            deadline=datetime.now(timezone.utc) + timedelta(days=30)
        )
        
        # Dispatch to all services
        for service in self.REGISTERED_SERVICES:
            self.message_broker.publish(
                queue=service["queue"],
                message={
                    "request_id": request_id,
                    "user_id": user_id,
                    "action": "erase",
                    "deadline": (datetime.now(timezone.utc) + 
                                timedelta(hours=service["timeout_hours"])).isoformat()
                }
            )
            
            # Track service-level status
            self.record_service_status(
                request_id=request_id,
                service_name=service["name"],
                status="dispatched"
            )
        
        return request_id
    
    def handle_service_acknowledgment(self, request_id: str, service_name: str, 
                                       status: str, details: dict):
        """Handle erasure completion notification from a service."""
        self.record_service_status(
            request_id=request_id,
            service_name=service_name,
            status=status,
            details=details
        )
        
        # Check if all services have acknowledged
        all_statuses = self.get_service_statuses(request_id)
        
        if all(s["status"] == "complete" for s in all_statuses):
            self.mark_erasure_complete(request_id)
            self.notify_data_subject(request_id, "erasure_complete")
        elif any(s["status"] == "failed" for s in all_statuses):
            self.escalate_to_dpo(request_id, all_statuses)
    
    def check_erasure_exceptions(self, user_id: str) -> list[str]:
        """Check Art 17(3) exceptions preventing erasure."""
        exceptions = []
        
        # Legal hold check
        if self.legal_hold_service.has_active_hold(user_id):
            exceptions.append("active_legal_hold")
        
        # Ongoing legal proceedings
        if self.legal_service.has_pending_claims(user_id):
            exceptions.append("pending_legal_claims")
        
        # Regulatory retention requirements
        if self.compliance_service.has_mandatory_retention(user_id):
            exceptions.append("regulatory_retention_requirement")
        
        return exceptions
```

---

### Lab 3: Breach Notification Workflow

**Objective:** Build an automated breach detection, assessment, and notification system meeting the 72-hour requirement.

```python
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from typing import Optional
import json

@dataclass
class BreachEvent:
    event_id: str
    detected_at: datetime
    source: str  # 'siem', 'manual_report', 'vulnerability_scan', 'third_party'
    description: str
    affected_systems: list[str]
    indicators: dict  # IoCs, evidence

class BreachNotificationWorkflow:
    # 72 hours from detection to SA notification
    SA_NOTIFICATION_DEADLINE_HOURS = 72
    
    # Escalation thresholds (hours from detection)
    TRIAGE_DEADLINE_HOURS = 4
    ASSESSMENT_DEADLINE_HOURS = 24
    DPO_REVIEW_DEADLINE_HOURS = 48
    
    def handle_breach_event(self, event: BreachEvent):
        """Entry point: potential breach detected."""
        
        # Step 1: Immediate containment + triage
        breach_record = self.create_breach_record(event)
        self.start_timer(breach_record.breach_id, "triage", self.TRIAGE_DEADLINE_HOURS)
        self.notify_incident_response_team(breach_record)
        
        return breach_record
    
    def triage_breach(self, breach_id: str, triage_result: dict):
        """
        Initial triage determines if personal data is involved.
        Must complete within 4 hours.
        """
        breach = self.get_breach(breach_id)
        
        if not triage_result.get("personal_data_involved"):
            # Not a GDPR breach — continue as security incident only
            breach.status = "security_incident_only"
            self.save_breach(breach)
            return
        
        # Personal data involved — escalate to GDPR assessment
        breach.data_categories = triage_result["data_categories"]
        breach.estimated_subjects = triage_result["estimated_subjects"]
        breach.breach_type = triage_result["breach_type"]
        breach.status = "assessment_in_progress"
        self.save_breach(breach)
        
        self.start_timer(breach_id, "assessment", self.ASSESSMENT_DEADLINE_HOURS)
        self.notify_dpo(breach, "triage_complete")
    
    def assess_risk(self, breach_id: str, assessment: dict) -> str:
        """
        Risk assessment per ENISA/WP29 methodology.
        Returns: 'unlikely_risk', 'risk', 'high_risk'
        """
        breach = self.get_breach(breach_id)
        
        # Scoring factors (simplified ENISA model)
        scores = {
            "data_processing_context": assessment.get("context_score", 0),  # 1-4
            "ease_of_identification": assessment.get("identification_score", 0),  # 1-4
            "circumstances": assessment.get("circumstances_score", 0),  # 1-4
            "severity_of_consequences": assessment.get("severity_score", 0),  # 1-4
        }
        
        # Overall severity = geometric considerations
        total_score = sum(scores.values())
        
        if total_score <= 4:
            risk_level = "unlikely_risk"
        elif total_score <= 8:
            risk_level = "risk"
        else:
            risk_level = "high_risk"
        
        breach.risk_level = risk_level
        breach.assessment_scores = scores
        breach.status = "dpo_review"
        self.save_breach(breach)
        
        # Route based on risk level
        if risk_level == "unlikely_risk":
            # Document in breach register only (Art 33(5))
            self.finalize_breach_register_entry(breach_id)
        elif risk_level == "risk":
            # SA notification required
            self.prepare_sa_notification(breach_id)
        elif risk_level == "high_risk":
            # SA + data subject notification
            self.prepare_sa_notification(breach_id)
            self.prepare_subject_notification(breach_id)
        
        return risk_level
    
    def prepare_sa_notification(self, breach_id: str) -> dict:
        """Generate supervisory authority notification (Art 33(3))."""
        breach = self.get_breach(breach_id)
        
        notification = {
            "notification_type": "initial",  # or 'supplementary'
            "breach_reference": breach_id,
            "date_of_awareness": breach.detected_at.isoformat(),
            "nature_of_breach": {
                "type": breach.breach_type,
                "description": breach.description,
                "categories_of_data_subjects": breach.subject_categories,
                "approximate_number_of_subjects": breach.estimated_subjects,
                "categories_of_records": breach.data_categories,
                "approximate_number_of_records": breach.estimated_records
            },
            "dpo_contact": {
                "name": self.config.dpo_name,
                "email": self.config.dpo_email,
                "phone": self.config.dpo_phone
            },
            "likely_consequences": breach.assessed_consequences,
            "measures_taken_or_proposed": {
                "containment": breach.containment_actions,
                "mitigation": breach.mitigation_actions,
                "prevention": breach.prevention_actions
            },
            "notification_deadline": (
                breach.detected_at + timedelta(hours=72)
            ).isoformat(),
            "submitted_within_72h": (
                datetime.now(timezone.utc) <= breach.detected_at + timedelta(hours=72)
            )
        }
        
        if not notification["submitted_within_72h"]:
            notification["delay_justification"] = breach.delay_reason
        
        return notification
    
    def prepare_subject_notification(self, breach_id: str) -> dict:
        """Generate data subject notification (Art 34)."""
        breach = self.get_breach(breach_id)
        
        # Plain language notification
        return {
            "subject": "Important: Security Incident Affecting Your Data",
            "body": {
                "what_happened": breach.plain_language_description,
                "what_data": breach.data_categories_plain,
                "what_we_did": breach.actions_taken_plain,
                "what_you_can_do": [
                    "Change your password immediately",
                    "Monitor your accounts for unusual activity",
                    "Be cautious of unsolicited communications"
                ],
                "contact": {
                    "dpo_email": self.config.dpo_email,
                    "support_url": self.config.breach_support_url
                }
            },
            "delivery_channels": ["email", "in_app_notification"],
            "affected_subjects_query": breach.affected_subjects_query
        }
```

---

### Lab 4: Consent Management Database Schema

**Objective:** Design a production-grade consent management database that supports granular purposes, versioning, preference centers, and audit trails.

```sql
-- ============================================================
-- CONSENT MANAGEMENT DATABASE SCHEMA
-- Supports: GDPR Art 7, CCPA opt-out, LGPD, multi-jurisdiction
-- ============================================================

-- Jurisdictions and their requirements
CREATE TABLE jurisdictions (
    jurisdiction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(10) UNIQUE NOT NULL, -- 'GDPR', 'CCPA', 'LGPD', etc.
    name VARCHAR(100) NOT NULL,
    default_consent_model VARCHAR(10) NOT NULL CHECK (default_consent_model IN ('opt_in', 'opt_out')),
    min_age_digital_consent INTEGER NOT NULL DEFAULT 16,
    requires_explicit_consent_sensitive BOOLEAN NOT NULL DEFAULT TRUE,
    breach_notification_hours INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

INSERT INTO jurisdictions (code, name, default_consent_model, min_age_digital_consent, breach_notification_hours) VALUES
('GDPR', 'EU General Data Protection Regulation', 'opt_in', 16, 72),
('CCPA', 'California Consumer Privacy Act', 'opt_out', 16, NULL),
('LGPD', 'Brazil Lei Geral de Proteção de Dados', 'opt_in', 12, NULL),
('PIPEDA', 'Canada Personal Information Protection', 'opt_in', 13, NULL),
('PIPL', 'China Personal Information Protection Law', 'opt_in', 14, NULL);

-- Processing purposes (versioned for consent validity)
CREATE TABLE consent_purposes (
    purpose_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    purpose_code VARCHAR(50) NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    title JSONB NOT NULL, -- {"en": "Marketing Emails", "de": "Marketing-E-Mails", ...}
    description JSONB NOT NULL, -- multi-language descriptions
    legal_basis VARCHAR(30) NOT NULL,
    is_essential BOOLEAN NOT NULL DEFAULT FALSE, -- cannot be opted out
    parent_purpose_id UUID REFERENCES consent_purposes(purpose_id),
    data_categories TEXT[] NOT NULL, -- what data this purpose uses
    retention_days INTEGER,
    third_party_sharing BOOLEAN NOT NULL DEFAULT FALSE,
    third_parties JSONB, -- list of third parties if sharing
    applicable_jurisdictions TEXT[] NOT NULL, -- jurisdiction codes
    effective_from TIMESTAMP WITH TIME ZONE NOT NULL,
    effective_until TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(purpose_code, version)
);

-- User consent records (immutable — append-only)
CREATE TABLE consent_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    purpose_id UUID NOT NULL REFERENCES consent_purposes(purpose_id),
    action VARCHAR(20) NOT NULL CHECK (action IN (
        'grant', 'deny', 'withdraw', 'expire', 'invalidate'
    )),
    -- Context for proving valid consent
    consent_context JSONB NOT NULL DEFAULT '{}'::jsonb,
    -- {
    --   "method": "web_banner|preference_center|api|paper",
    --   "interface_version": "2.1",
    --   "privacy_notice_version": "3.0",
    --   "language_shown": "en",
    --   "interaction_type": "affirmative_click|toggle|checkbox",
    --   "bundled_with_service": false,
    --   "freely_given": true
    -- }
    ip_address INET,
    user_agent TEXT,
    geo_country VARCHAR(2), -- for jurisdiction determination
    jurisdiction_applied VARCHAR(10), -- which law governed this consent
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    -- Proof of consent (screenshot hash, form snapshot, etc.)
    evidence_hash VARCHAR(64),
    evidence_storage_ref TEXT
);

-- Materialized current consent state (derived from events)
CREATE MATERIALIZED VIEW current_consent_state AS
SELECT DISTINCT ON (user_id, purpose_id)
    user_id,
    purpose_id,
    action AS current_status,
    recorded_at AS last_updated,
    jurisdiction_applied,
    consent_context
FROM consent_events
ORDER BY user_id, purpose_id, recorded_at DESC;

CREATE UNIQUE INDEX idx_current_consent ON current_consent_state(user_id, purpose_id);

-- Refresh function (call after new events)
CREATE OR REPLACE FUNCTION refresh_consent_state()
RETURNS TRIGGER AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY current_consent_state;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER refresh_consent_after_event
AFTER INSERT ON consent_events
FOR EACH STATEMENT
EXECUTE FUNCTION refresh_consent_state();

-- Preference center configuration
CREATE TABLE preference_center_config (
    config_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    jurisdiction_code VARCHAR(10) NOT NULL,
    purpose_groups JSONB NOT NULL,
    -- [
    --   {
    --     "group_name": {"en": "Marketing", "de": "Marketing"},
    --     "purposes": ["marketing_email", "marketing_sms", "marketing_push"],
    --     "default_state": "off",
    --     "toggleable": true
    --   },
    --   {
    --     "group_name": {"en": "Essential"},
    --     "purposes": ["service_delivery"],
    --     "default_state": "on",
    --     "toggleable": false
    --   }
    -- ]
    show_vendor_list BOOLEAN DEFAULT FALSE,
    allow_granular_vendor_consent BOOLEAN DEFAULT FALSE,
    ui_config JSONB, -- colors, layout, etc.
    version INTEGER NOT NULL DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE
);

-- Consent validity check function
CREATE OR REPLACE FUNCTION is_consent_valid(
    p_user_id UUID,
    p_purpose_code VARCHAR(50)
) RETURNS BOOLEAN AS $$
DECLARE
    v_consent RECORD;
    v_purpose RECORD;
BEGIN
    -- Get current active purpose version
    SELECT * INTO v_purpose 
    FROM consent_purposes 
    WHERE purpose_code = p_purpose_code 
    AND is_active = TRUE 
    ORDER BY version DESC LIMIT 1;
    
    IF NOT FOUND THEN RETURN FALSE; END IF;
    
    -- Essential purposes always valid (no consent needed)
    IF v_purpose.is_essential THEN RETURN TRUE; END IF;
    
    -- Get current consent state
    SELECT * INTO v_consent 
    FROM current_consent_state 
    WHERE user_id = p_user_id AND purpose_id = v_purpose.purpose_id;
    
    IF NOT FOUND THEN RETURN FALSE; END IF;
    
    -- Check if consent was granted (not withdrawn/denied/expired)
    IF v_consent.current_status != 'grant' THEN RETURN FALSE; END IF;
    
    -- Check if consent was given for current purpose version
    -- (major version change may invalidate prior consent)
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql STABLE;

-- Helper: Get all active consents for a user (for SAR response)
CREATE OR REPLACE FUNCTION get_user_consent_summary(p_user_id UUID)
RETURNS TABLE (
    purpose_code VARCHAR(50),
    purpose_title JSONB,
    current_status VARCHAR(20),
    consented_at TIMESTAMP WITH TIME ZONE,
    jurisdiction VARCHAR(10)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        cp.purpose_code,
        cp.title,
        cs.current_status,
        cs.last_updated,
        cs.jurisdiction_applied
    FROM current_consent_state cs
    JOIN consent_purposes cp ON cs.purpose_id = cp.purpose_id
    WHERE cs.user_id = p_user_id
    AND cp.is_active = TRUE
    ORDER BY cp.purpose_code;
END;
$$ LANGUAGE plpgsql STABLE;

-- CCPA-specific: Do Not Sell/Share tracking
CREATE TABLE ccpa_opt_outs (
    opt_out_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    opt_out_type VARCHAR(20) NOT NULL CHECK (opt_out_type IN ('sale', 'share', 'sensitive_use')),
    opted_out BOOLEAN NOT NULL DEFAULT TRUE,
    signal_source VARCHAR(30) NOT NULL, -- 'user_request', 'gpc_signal', 'authorized_agent'
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    gpc_detected BOOLEAN DEFAULT FALSE
);

-- Audit: Who accessed consent data and why
CREATE TABLE consent_access_log (
    log_id BIGSERIAL PRIMARY KEY,
    accessed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    accessor_id UUID NOT NULL,
    accessor_role VARCHAR(50) NOT NULL,
    user_id_accessed UUID NOT NULL,
    access_type VARCHAR(30) NOT NULL, -- 'read_state', 'export', 'modify'
    purpose_of_access TEXT NOT NULL, -- 'sar_fulfillment', 'marketing_check', 'audit'
    ip_address INET
);
```

**Testing the schema:**

```sql
-- Verify consent check works
SELECT is_consent_valid('user-uuid-here', 'marketing_email');

-- Get full consent summary for a SAR
SELECT * FROM get_user_consent_summary('user-uuid-here');

-- Check CCPA opt-out status
SELECT * FROM ccpa_opt_outs 
WHERE user_id = 'user-uuid-here' 
AND opted_out = TRUE;

-- Audit trail for accountability
SELECT * FROM consent_events 
WHERE user_id = 'user-uuid-here' 
ORDER BY recorded_at DESC;
```

---

## Security Assessment Perspective

Throughout this guide, the security-focused reader should recognize the dual nature of GDPR compliance in penetration testing and security assessments:

**What to look for during security assessments:**

1. **Data exposure assessment:** Every vulnerability that exposes personal data carries regulatory consequence. A SQL injection exposing 10,000 customer records is not just a technical finding — it is a reportable breach triggering 72-hour notification obligations.

2. **Access control testing:** RBAC enforcement failures mean unauthorized access to personal data — a processing violation under Art 5(1)(f) independent of any external attack.

3. **Encryption validation:** Test actual implementation, not policy claims. Databases without TDE, unencrypted backups, plaintext in logs — all are Art 32 failures.

4. **Retention policy enforcement:** Verify data actually gets deleted when retention periods expire. Policy documents mean nothing if the cron job is disabled or the retention logic is buggy.

5. **Consent enforcement testing:** Verify that systems actually check consent before processing. Send requests without valid consent tokens and see if processing proceeds regardless.

6. **Cross-border transfer audit:** Map actual data flows (DNS, network traffic, API calls) against documented transfer mechanisms. Cloud auto-scaling into non-adequate regions is a transfer violation.

7. **Breach notification readiness:** Test the 72-hour workflow. Can the organization actually detect, assess, and notify within the deadline? Most cannot.

8. **Right-to-erasure verification:** After an erasure request, attempt to recover the data through API endpoints, cached responses, search indices, backups, and analytics systems. Incomplete erasure is a compliance failure.

**Reporting framework for privacy findings:**

| Element | Standard Security Report | GDPR-Aware Report Addition |
|---|---|---|
| Finding | SQL Injection in /api/users | + Exposes Art 9 health data of ~50K subjects |
| Impact | Database compromise | + Mandatory Art 33/34 notification, potential €20M fine |
| Risk | Critical (CVSS 9.8) | + Regulatory risk: supervisory authority investigation |
| Remediation | Parameterized queries | + Incident response plan review, DPIA update |
| Timeline | 30 days | + 72-hour breach notification may already be triggered |

Understanding GDPR transforms vulnerability findings from purely technical issues into business-critical regulatory risks that demand executive attention and immediate action.

---

## References

- Regulation (EU) 2016/679 (GDPR full text)
- EDPB Guidelines on data breach notification (WP250 rev.01)
- EDPB Recommendations 01/2020 on supplementary measures for transfers
- ENISA methodology for breach severity assessment
- CJEU C-311/18 (Schrems II) judgment
- Commission Implementing Decision (EU) 2021/914 (Standard Contractual Clauses)
- Commission Implementing Decision (EU) 2023/1795 (EU-US Data Privacy Framework adequacy)
- ICO guidance on legitimate interest assessments
- NIST Privacy Framework 1.0
- ISO/IEC 27701:2019 (Privacy Information Management)
