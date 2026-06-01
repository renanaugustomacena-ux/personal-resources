# Data Classification, Labeling, and Handling Standards

## Table of Contents

1. [Classification Frameworks](#1-classification-frameworks)
2. [Data Discovery and Inventory](#2-data-discovery-and-inventory)
3. [Labeling Implementation](#3-labeling-implementation)
4. [Handling Procedures by Classification](#4-handling-procedures-by-classification)
5. [Data Loss Prevention (DLP)](#5-data-loss-prevention-dlp)
6. [Database-Specific Classification](#6-database-specific-classification)
7. [Cloud Data Classification](#7-cloud-data-classification)
8. [Data Classification in CI/CD](#8-data-classification-in-cicd)
9. [Compliance Mapping](#9-compliance-mapping)
10. [Lab Exercises](#10-lab-exercises)

---

## 1. Classification Frameworks

Data classification is the disciplined process of categorizing data assets by sensitivity, value, and regulatory requirements to enforce proportional protection controls. Without a rigorous classification scheme, organizations either over-protect low-value data (wasting resources) or under-protect critical assets (inviting breach and regulatory sanction).

### 1.1 Government Classification Frameworks

#### FIPS 199 (Federal Information Processing Standard)

FIPS 199, published by NIST, mandates that federal information systems categorize data based on the potential impact of a security breach across three dimensions:

| Impact Level | Confidentiality | Integrity | Availability |
|---|---|---|---|
| **Low** | Unauthorized disclosure has limited adverse effect | Unauthorized modification has limited adverse effect | Disruption has limited adverse effect |
| **Moderate** | Serious adverse effect on operations, assets, or individuals | Serious adverse effect | Serious adverse effect |
| **High** | Severe or catastrophic adverse effect | Severe or catastrophic adverse effect | Severe or catastrophic adverse effect |

The system's overall security category follows the high-water-mark principle:

```
SC(information_system) = {
  (confidentiality, impact),
  (integrity, impact),
  (availability, impact)
}
```

For example, a system processing federal tax returns:
```
SC(tax_system) = {
  (confidentiality, HIGH),
  (integrity, HIGH),
  (availability, MODERATE)
}
```

This yields an overall HIGH system categorization, driving selection of security controls from NIST 800-53.

#### NATO Classification System

NATO uses a hierarchical classification with strict compartmentalization:

- **COSMIC TOP SECRET (CTS)** — exceptionally grave damage to NATO
- **NATO SECRET (NS)** — serious damage to NATO
- **NATO CONFIDENTIAL (NC)** — damage to NATO interests
- **NATO RESTRICTED (NR)** — disadvantage to NATO interests
- **NATO UNCLASSIFIED (NU)** — no damage

Each level carries specific handling caveats:
- **ATOMAL** — nuclear weapons information
- **BOHEMIA** — SIGINT information
- **BALK** — communications security information

NATO requires personnel security clearances matching or exceeding data classification, need-to-know verification, and physical security controls proportional to classification level.

#### European Union Classification

The EU Council Decision 2013/488/EU establishes four classification levels:

- **TRES SECRET UE/EU TOP SECRET** — exceptionally grave prejudice to essential EU interests
- **SECRET UE/EU SECRET** — serious prejudice
- **CONFIDENTIEL UE/EU CONFIDENTIAL** — prejudice to EU interests
- **RESTREINT UE/EU RESTRICTED** — disadvantageous to EU interests

Member states must implement the EU Information Assurance standards (EUIA) and maintain approved cryptographic products for classified transmission. Cross-border transfer requires bilateral security agreements.

### 1.2 Industry-Specific Frameworks

#### PCI-DSS Data Categories

PCI-DSS defines specific data elements requiring protection:

**Cardholder Data (CHD):**
- Primary Account Number (PAN) — the critical element; its presence defines the CDE
- Cardholder Name (when stored with PAN)
- Service Code
- Expiration Date

**Sensitive Authentication Data (SAD):**
- Full magnetic stripe data (Track 1 / Track 2)
- CAV2/CVC2/CVV2/CID
- PINs and PIN blocks

SAD must NEVER be stored post-authorization, regardless of encryption. CHD can be stored with proper encryption (AES-256 minimum), tokenization, or truncation.

The Cardholder Data Environment (CDE) scope is determined by where CHD flows, is processed, stored, or transmitted. Network segmentation reduces scope but requires validation.

#### HIPAA PHI and ePHI Classification

The Health Insurance Portability and Accountability Act identifies 18 PHI identifiers:

1. Names
2. Geographic data smaller than state
3. Dates (except year) related to an individual
4. Phone numbers
5. Fax numbers
6. Email addresses
7. Social Security Numbers
8. Medical record numbers
9. Health plan beneficiary numbers
10. Account numbers
11. Certificate/license numbers
12. Vehicle identifiers and serial numbers
13. Device identifiers and serial numbers
14. Web URLs
15. IP addresses
16. Biometric identifiers
17. Full-face photos and comparable images
18. Any other unique identifying number

When any of these identifiers is associated with health information and transmitted or maintained in electronic form, it becomes ePHI, triggering the HIPAA Security Rule's administrative, physical, and technical safeguard requirements.

**De-identification methods:**
- **Expert Determination (§164.514(b)(1))** — statistical/scientific expert certifies very small re-identification risk
- **Safe Harbor (§164.514(b)(2))** — remove all 18 identifiers plus verify residual data cannot re-identify individuals

#### FERPA (Family Educational Rights and Privacy Act)

FERPA protects student education records. Classification under FERPA:

- **Directory Information** — name, address, enrollment dates, degrees earned (releasable with opt-out notice)
- **Non-Directory Education Records** — grades, disciplinary records, financial aid records (protected; requires written consent)
- **Treatment Records** — medical/psychological records maintained by professionals (excluded from FERPA, may fall under other statutes)

### 1.3 Enterprise Classification Tiers

Most organizations implement a four-tier model:

| Tier | Label | Description | Example Data |
|---|---|---|---|
| 1 | **Public** | No impact from disclosure | Marketing materials, published financial reports |
| 2 | **Internal** | Minor business impact if disclosed | Internal policies, org charts, non-sensitive emails |
| 3 | **Confidential** | Significant business impact | Customer PII, financial projections, source code |
| 4 | **Restricted** | Severe/existential impact | Trade secrets, M&A plans, cryptographic keys, regulated data |

### 1.4 Sensitivity Levels and Impact Assessment (CIA Triad)

Each classification level maps to specific CIA impact expectations:

```
┌──────────────┬────────────────────────────────────────────────────────────────┐
│  Level       │  Confidentiality      │  Integrity          │  Availability    │
├──────────────┼───────────────────────┼─────────────────────┼──────────────────┤
│  Public      │  None required        │  Low (tamper evident)│  Best effort    │
│  Internal    │  Basic access control │  Moderate            │  Business hours │
│  Confidential│  Encryption at rest   │  High (audit trail)  │  99.9% SLA     │
│              │  & in transit         │                      │                 │
│  Restricted  │  HSM-managed keys,    │  Cryptographic       │  99.99% SLA,   │
│              │  MFA, DLP, RBAC       │  integrity checking  │  HA/DR required│
└──────────────┴───────────────────────┴─────────────────────┴──────────────────┘
```

The classification decision tree:

```
1. Does regulation mandate a specific classification?
   YES → Apply mandated level (cannot downgrade)
   NO  → Continue

2. What is the maximum business impact of unauthorized disclosure?
   Severe/catastrophic → RESTRICTED
   Significant          → CONFIDENTIAL
   Minor               → INTERNAL
   None                → PUBLIC

3. What is the aggregation risk?
   (Multiple INTERNAL items combined may yield CONFIDENTIAL classification)

4. Apply temporal sensitivity:
   - Does classification degrade over time? (e.g., quarterly earnings post-publication)
   - Set review date / declassification trigger
```

---

## 2. Data Discovery and Inventory

You cannot protect what you cannot find. Data discovery is the systematic identification, location, and cataloging of data assets across an organization's infrastructure.

### 2.1 Automated Discovery Tools

#### AWS Macie

Amazon Macie uses machine learning and pattern matching to discover sensitive data in S3:

```python
import boto3

macie_client = boto3.client('macie2')

# Create a classification job
response = macie_client.create_classification_job(
    jobType='ONE_TIME',
    name='pii-discovery-prod-bucket',
    s3JobDefinition={
        'bucketDefinitions': [
            {
                'accountId': '123456789012',
                'buckets': ['production-data-lake']
            }
        ],
        'scoping': {
            'includes': {
                'and': [
                    {
                        'simpleScopeTerm': {
                            'comparator': 'STARTS_WITH',
                            'key': 'OBJECT_KEY',
                            'values': ['customer-data/']
                        }
                    }
                ]
            }
        }
    },
    managedDataIdentifierSelector='ALL',
    customDataIdentifierIds=[
        'custom-employee-id-pattern',
        'custom-internal-account-number'
    ]
)
```

Macie identifies over 100 sensitive data types including:
- Credit card numbers (Luhn validation)
- AWS secret keys
- Passport numbers (country-specific formats)
- National IDs (SSN, SIN, NHS, CPF, etc.)
- Medical terms and ICD codes

#### Google Cloud DLP API

Google's DLP API offers granular inspection capabilities:

```python
from google.cloud import dlp_v2

dlp_client = dlp_v2.DlpServiceClient()

# Configure inspection
inspect_config = {
    "info_types": [
        {"name": "CREDIT_CARD_NUMBER"},
        {"name": "EMAIL_ADDRESS"},
        {"name": "PHONE_NUMBER"},
        {"name": "PERSON_NAME"},
        {"name": "US_SOCIAL_SECURITY_NUMBER"},
    ],
    "min_likelihood": dlp_v2.Likelihood.LIKELY,
    "include_quote": True,
    "limits": {
        "max_findings_per_request": 100
    },
    "custom_info_types": [
        {
            "info_type": {"name": "INTERNAL_EMPLOYEE_ID"},
            "regex": {"pattern": r"EMP-[A-Z]{2}\d{6}"},
            "likelihood": dlp_v2.Likelihood.VERY_LIKELY
        }
    ]
}

# Inspect BigQuery table
job_config = {
    "inspect_config": inspect_config,
    "storage_config": {
        "big_query_options": {
            "table_reference": {
                "project_id": "my-project",
                "dataset_id": "customer_analytics",
                "table_id": "user_profiles"
            },
            "rows_limit": 1000,
            "sample_method": "RANDOM_START"
        }
    },
    "actions": [
        {
            "save_findings": {
                "output_config": {
                    "table": {
                        "project_id": "my-project",
                        "dataset_id": "dlp_results",
                        "table_id": "findings"
                    }
                }
            }
        }
    ]
}

response = dlp_client.create_dlp_job(
    parent="projects/my-project/locations/global",
    inspect_job=job_config
)
```

#### Azure Purview (Microsoft Purview)

Azure Purview provides unified data governance:

```json
{
  "scanRuleSet": {
    "name": "sensitive-data-scan",
    "kind": "AzureSqlDatabase",
    "properties": {
      "classificationRules": [
        {
          "classificationRuleName": "MICROSOFT.FINANCIAL.CREDIT_CARD_NUMBER",
          "enabled": true
        },
        {
          "classificationRuleName": "MICROSOFT.PERSONAL.US.SOCIAL_SECURITY_NUMBER",
          "enabled": true
        },
        {
          "classificationRuleName": "Custom.InternalProjectCode",
          "enabled": true,
          "rulePattern": {
            "kind": "Regex",
            "pattern": "PRJ-\\d{4}-[A-Z]{3}"
          }
        }
      ]
    }
  }
}
```

#### Open-Source Tools

**piicatcher** — scans databases for PII columns:

```bash
# Install
pip install piicatcher

# Scan PostgreSQL database
piicatcher db \
  --connection "postgresql://user:pass@localhost:5432/production" \
  --scan-type metadata \
  --output report.json

# Scan with deep inspection (sample data)
piicatcher db \
  --connection "postgresql://user:pass@localhost:5432/production" \
  --scan-type deep \
  --sample-size 100
```

**Microsoft Presidio** — PII detection and anonymization framework:

```python
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_anonymizer import AnonymizerEngine

# Initialize with default NLP engine
analyzer = AnalyzerEngine()

# Add custom recognizer for internal IDs
internal_id_pattern = Pattern(
    name="internal_id_pattern",
    regex=r"INT-\d{8}-[A-Z]{2}",
    score=0.9
)
internal_id_recognizer = PatternRecognizer(
    supported_entity="INTERNAL_ID",
    patterns=[internal_id_pattern]
)
analyzer.registry.add_recognizer(internal_id_recognizer)

# Analyze text
text = "Customer John Smith (SSN: 123-45-6789) called about account INT-20240115-AB"
results = analyzer.analyze(
    text=text,
    language="en",
    entities=["PERSON", "US_SSN", "INTERNAL_ID", "CREDIT_CARD", "EMAIL_ADDRESS"]
)

# Anonymize
anonymizer = AnonymizerEngine()
anonymized = anonymizer.anonymize(text=text, analyzer_results=results)
# Output: "Customer <PERSON> (SSN: <US_SSN>) called about account <INTERNAL_ID>"
```

### 2.2 Data Catalog Platforms

#### Apache Atlas

Atlas provides metadata management and data governance for Hadoop ecosystems:

```json
{
  "entity": {
    "typeName": "hive_table",
    "attributes": {
      "qualifiedName": "production.customer_profiles@primary",
      "name": "customer_profiles",
      "classifications": [
        {
          "typeName": "PII",
          "attributes": {
            "sensitivity_level": "HIGH",
            "regulation": "GDPR",
            "data_steward": "privacy-team@company.com"
          }
        },
        {
          "typeName": "CONFIDENTIAL",
          "attributes": {
            "review_date": "2025-06-01",
            "justification": "Contains customer contact information"
          }
        }
      ],
      "columns": [
        {
          "name": "email",
          "classifications": ["EMAIL_ADDRESS", "PII"],
          "sensitivity": "CONFIDENTIAL"
        },
        {
          "name": "purchase_total",
          "classifications": ["FINANCIAL"],
          "sensitivity": "INTERNAL"
        }
      ]
    }
  }
}
```

#### LinkedIn DataHub

DataHub offers a modern metadata platform with classification tagging:

```graphql
mutation addClassificationTag {
  addTag(
    input: {
      tagUrn: "urn:li:tag:PII"
      resourceUrn: "urn:li:dataset:(urn:li:dataPlatform:postgres,production.users,PROD)"
    }
  )
}

mutation addGlossaryTerm {
  addTerm(
    input: {
      termUrn: "urn:li:glossaryTerm:Classification.Confidential"
      resourceUrn: "urn:li:schemaField:(urn:li:dataset:(urn:li:dataPlatform:postgres,production.users,PROD),email)"
    }
  )
}
```

#### Amundsen (by Lyft)

Amundsen provides data discovery with classification-aware search. Its architecture separates metadata, search, and frontend services, allowing classification tags to flow through the catalog and appear in data scientist discovery workflows.

#### Collibra

Collibra is an enterprise data governance platform providing:
- Business glossary with classification taxonomies
- Data quality rules tied to classification
- Stewardship workflows for classification review
- Regulatory compliance mapping (GDPR, CCPA, HIPAA)

### 2.3 Metadata-Driven Classification

Metadata-driven classification uses schema information, column names, data patterns, and business context to automatically assign classifications:

```python
class MetadataClassifier:
    """Classify database columns based on metadata heuristics."""

    COLUMN_NAME_PATTERNS = {
        "RESTRICTED": [
            r"(?i)(ssn|social_security|tax_id|national_id)",
            r"(?i)(credit_card|card_number|pan|cvv|cvc)",
            r"(?i)(password|passwd|secret|private_key|api_key)",
        ],
        "CONFIDENTIAL": [
            r"(?i)(email|phone|mobile|address|street|city|zip)",
            r"(?i)(first_name|last_name|full_name|dob|birth)",
            r"(?i)(salary|compensation|bank_account|routing)",
            r"(?i)(medical|diagnosis|prescription|health)",
        ],
        "INTERNAL": [
            r"(?i)(employee_id|department|manager|title)",
            r"(?i)(internal_note|memo|comment)",
            r"(?i)(cost_center|budget|forecast)",
        ],
    }

    DATA_TYPE_SIGNALS = {
        "CONFIDENTIAL": ["jsonb", "bytea", "blob"],  # Often contains unstructured PII
    }

    def classify_column(self, table_name, column_name, data_type, sample_values=None):
        """Return highest applicable classification."""
        classification = "PUBLIC"

        # Check column name patterns
        for level, patterns in self.COLUMN_NAME_PATTERNS.items():
            for pattern in patterns:
                if re.match(pattern, column_name):
                    classification = self._higher(classification, level)
                    break

        # Check data type signals
        for level, types in self.DATA_TYPE_SIGNALS.items():
            if data_type.lower() in types:
                classification = self._higher(classification, level)

        # Check sample values with regex patterns
        if sample_values:
            classification = self._check_sample_values(classification, sample_values)

        return classification

    def _higher(self, current, candidate):
        hierarchy = ["PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"]
        return candidate if hierarchy.index(candidate) > hierarchy.index(current) else current
```

### 2.4 Regex and ML-Based PII Detection Patterns

Common regex patterns for PII detection:

```python
PII_PATTERNS = {
    "US_SSN": r"\b\d{3}-\d{2}-\d{4}\b",
    "US_SSN_NO_DASH": r"\b(?!000|666|9\d{2})\d{3}(?!00)\d{2}(?!0000)\d{4}\b",
    "CREDIT_CARD_VISA": r"\b4\d{3}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
    "CREDIT_CARD_MC": r"\b5[1-5]\d{2}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
    "CREDIT_CARD_AMEX": r"\b3[47]\d{2}[\s-]?\d{6}[\s-]?\d{5}\b",
    "EMAIL": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "PHONE_US": r"\b(?:\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
    "PHONE_INTL": r"\b\+\d{1,3}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}\b",
    "IPV4": r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b",
    "IBAN": r"\b[A-Z]{2}\d{2}[A-Z0-9]{4}\d{7}([A-Z0-9]?){0,16}\b",
    "UK_NHS": r"\b\d{3}[\s-]?\d{3}[\s-]?\d{4}\b",
    "PASSPORT_US": r"\b[A-Z]\d{8}\b",
    "DATE_OF_BIRTH": r"\b(?:0[1-9]|1[0-2])[/-](?:0[1-9]|[12]\d|3[01])[/-](?:19|20)\d{2}\b",
    "AWS_ACCESS_KEY": r"\bAKIA[0-9A-Z]{16}\b",
    "AWS_SECRET_KEY": r"\b[A-Za-z0-9/+=]{40}\b",
    "PRIVATE_KEY_HEADER": r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----",
}
```

ML-based approaches supplement regex when dealing with:
- Names (NER models — spaCy, Flair, Hugging Face NER pipelines)
- Addresses (custom classifiers trained on address corpora)
- Medical terminology (BioBERT, ClinicalBERT)
- Context-dependent classification (email body vs. log entry)

```python
import spacy

nlp = spacy.load("en_core_web_lg")

def extract_pii_entities(text):
    """Use NER to find PII that regex patterns miss."""
    doc = nlp(text)
    pii_findings = []
    
    pii_entity_types = {"PERSON", "GPE", "LOC", "ORG", "DATE", "MONEY"}
    
    for ent in doc.ents:
        if ent.label_ in pii_entity_types:
            pii_findings.append({
                "text": ent.text,
                "type": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char,
                "classification": "CONFIDENTIAL" if ent.label_ == "PERSON" else "INTERNAL"
            })
    
    return pii_findings
```

---

## 3. Labeling Implementation

Labeling translates classification decisions into machine-readable, enforceable metadata attached to data assets at every layer of the stack.

### 3.1 Database Column Tagging

#### PostgreSQL COMMENT and Extensions

```sql
-- Basic column classification with COMMENT
COMMENT ON COLUMN customers.email IS 
  '{"classification": "CONFIDENTIAL", "pii": true, "regulation": ["GDPR", "CCPA"], "retention": "3y"}';

COMMENT ON COLUMN customers.ssn IS 
  '{"classification": "RESTRICTED", "pii": true, "regulation": ["HIPAA", "SOX"], "retention": "7y", "encryption": "AES-256-GCM"}';

COMMENT ON COLUMN orders.total_amount IS 
  '{"classification": "INTERNAL", "pii": false, "regulation": ["SOX"], "retention": "7y"}';

-- Create a dedicated classification schema
CREATE SCHEMA IF NOT EXISTS data_governance;

CREATE TABLE data_governance.column_classifications (
    id SERIAL PRIMARY KEY,
    schema_name TEXT NOT NULL,
    table_name TEXT NOT NULL,
    column_name TEXT NOT NULL,
    classification_level TEXT NOT NULL CHECK (classification_level IN ('PUBLIC', 'INTERNAL', 'CONFIDENTIAL', 'RESTRICTED')),
    pii_flag BOOLEAN DEFAULT FALSE,
    phi_flag BOOLEAN DEFAULT FALSE,
    pci_flag BOOLEAN DEFAULT FALSE,
    regulations TEXT[] DEFAULT '{}',
    data_steward TEXT,
    retention_period INTERVAL,
    encryption_required BOOLEAN DEFAULT FALSE,
    masking_policy TEXT,
    classified_at TIMESTAMPTZ DEFAULT NOW(),
    classified_by TEXT NOT NULL,
    review_date DATE,
    UNIQUE (schema_name, table_name, column_name)
);

-- Index for efficient lookups
CREATE INDEX idx_classification_level ON data_governance.column_classifications(classification_level);
CREATE INDEX idx_pii_flag ON data_governance.column_classifications(pii_flag) WHERE pii_flag = TRUE;

-- Insert classification metadata
INSERT INTO data_governance.column_classifications 
    (schema_name, table_name, column_name, classification_level, pii_flag, regulations, data_steward, retention_period, encryption_required, masking_policy, classified_by, review_date)
VALUES
    ('public', 'customers', 'email', 'CONFIDENTIAL', TRUE, ARRAY['GDPR','CCPA'], 'privacy@company.com', '3 years', TRUE, 'partial_mask', 'auto-scanner', '2025-06-01'),
    ('public', 'customers', 'ssn', 'RESTRICTED', TRUE, ARRAY['HIPAA','SOX'], 'compliance@company.com', '7 years', TRUE, 'full_redact', 'auto-scanner', '2025-06-01'),
    ('public', 'customers', 'name', 'CONFIDENTIAL', TRUE, ARRAY['GDPR'], 'privacy@company.com', '3 years', FALSE, 'tokenize', 'auto-scanner', '2025-06-01');

-- View: query current classifications
CREATE VIEW data_governance.restricted_columns AS
SELECT schema_name, table_name, column_name, regulations, data_steward
FROM data_governance.column_classifications
WHERE classification_level = 'RESTRICTED';
```

#### pg_catalog Extensions for Classification

```sql
-- Using PostgreSQL security labels (built-in feature)
SECURITY LABEL FOR classification ON COLUMN customers.ssn IS 'RESTRICTED';
SECURITY LABEL FOR classification ON COLUMN customers.email IS 'CONFIDENTIAL';
SECURITY LABEL FOR classification ON TABLE customers IS 'CONFIDENTIAL';

-- Query security labels
SELECT objtype, objname, label
FROM pg_seclabels
WHERE provider = 'classification';
```

### 3.2 Schema-Level Metadata

```sql
-- Schema-level classification metadata
COMMENT ON SCHEMA sensitive_pii IS 
  '{"classification": "RESTRICTED", "access_pattern": "need-to-know", "audit": "full", "dlp": "enabled"}';

-- Create classification-segregated schemas
CREATE SCHEMA public_data;        -- PUBLIC tier
CREATE SCHEMA internal_ops;       -- INTERNAL tier
CREATE SCHEMA confidential_pii;   -- CONFIDENTIAL tier
CREATE SCHEMA restricted_secrets; -- RESTRICTED tier

-- Grant access by classification level
GRANT USAGE ON SCHEMA public_data TO PUBLIC;
GRANT USAGE ON SCHEMA internal_ops TO internal_users;
GRANT USAGE ON SCHEMA confidential_pii TO pii_authorized;
GRANT USAGE ON SCHEMA restricted_secrets TO security_team;
```

### 3.3 Data Lineage Integration

Classification must propagate through data transformations. When a RESTRICTED column feeds a derived table, the derived column inherits the classification:

```python
class ClassificationLineageTracker:
    """Track classification inheritance through data transformations."""

    def __init__(self, catalog_client):
        self.catalog = catalog_client

    def propagate_classification(self, source_columns, target_column, transform_type):
        """
        Apply high-water-mark classification to target based on sources.
        
        Args:
            source_columns: List of (schema, table, column) tuples
            target_column: (schema, table, column) tuple
            transform_type: 'direct_copy', 'aggregation', 'derivation', 'anonymization'
        """
        source_classifications = []
        for schema, table, col in source_columns:
            cls = self.catalog.get_classification(schema, table, col)
            source_classifications.append(cls)

        if transform_type == 'anonymization':
            # Proper anonymization can reduce classification level
            target_cls = self._determine_post_anonymization_level(source_classifications)
        elif transform_type == 'aggregation':
            # Aggregation may reduce classification if k-anonymity is met
            target_cls = self._determine_post_aggregation_level(source_classifications)
        else:
            # High-water-mark for direct copy or derivation
            target_cls = max(source_classifications, key=lambda c: c.level)

        self.catalog.set_classification(
            *target_column,
            classification=target_cls,
            lineage_sources=source_columns,
            transform_type=transform_type
        )
```

### 3.4 Automated Labeling in ETL/ELT Pipelines

```python
# dbt example: classification metadata in schema.yml
"""
models:
  - name: dim_customers
    meta:
      classification: CONFIDENTIAL
      data_steward: privacy-team@company.com
      retention: 3y
    columns:
      - name: customer_id
        meta:
          classification: INTERNAL
          pii: false
      - name: email
        meta:
          classification: CONFIDENTIAL
          pii: true
          masking: partial
        tests:
          - not_null
          - unique
      - name: ssn_hash
        meta:
          classification: RESTRICTED
          pii: true
          original_sensitivity: RESTRICTED
          transform: SHA-256 + salt
          masking: full_redact
"""

# Apache Airflow: classification-aware DAG
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable

def classify_and_tag_output(**context):
    """Post-processing: tag output dataset with classification metadata."""
    output_table = context['params']['target_table']
    source_tables = context['params']['source_tables']
    
    # Fetch source classifications from catalog
    max_classification = get_highest_classification(source_tables)
    
    # Tag output in data catalog
    catalog_client.tag_asset(
        asset=output_table,
        tags={
            'classification': max_classification,
            'pipeline': context['dag'].dag_id,
            'run_id': context['run_id'],
            'classified_at': datetime.utcnow().isoformat()
        }
    )
    
    # Apply access controls based on classification
    apply_access_controls(output_table, max_classification)

dag = DAG(
    'customer_etl_classified',
    default_args={'owner': 'data-eng'},
    schedule_interval='@daily',
    tags=['CONFIDENTIAL', 'PII']
)
```

### 3.5 Microsoft Information Protection (MIP) Labels

MIP (formerly Azure Information Protection) provides persistent, document-level classification labels:

```powershell
# PowerShell: Create sensitivity labels
New-Label -DisplayName "Highly Confidential" `
    -Name "HighlyConfidential" `
    -Tooltip "Data requiring strictest handling" `
    -ContentType "File, Email" `
    -EncryptionEnabled $true `
    -EncryptionProtectionType "Template" `
    -EncryptionTemplateId "d4f15b7c-..."

# Auto-labeling policy
New-AutoSensitivityLabelPolicy -Name "AutoLabel-CreditCards" `
    -ApplySensitivityLabel "Confidential" `
    -Mode "TestWithNotifications" `
    -ExchangeLocation "All" `
    -SharePointLocation "All" `
    -Comment "Auto-labels documents containing credit card numbers"

New-AutoSensitivityLabelRule -Policy "AutoLabel-CreditCards" `
    -Name "CreditCardRule" `
    -ContentContainsSensitiveInformation @{
        Name = "Credit Card Number"
        MinCount = 1
        MaxCount = -1
        MinConfidence = 85
    }
```

### 3.6 Apache Ranger Tag-Based Policies

```json
{
  "service": "hive_production",
  "name": "PII_Column_Masking",
  "policyType": 1,
  "policyLabels": ["PII", "GDPR"],
  "resources": {
    "database": {"values": ["*"]},
    "table": {"values": ["*"]},
    "column": {"values": ["*"]}
  },
  "conditions": [
    {
      "type": "tag",
      "values": ["PII_CONFIDENTIAL"]
    }
  ],
  "dataMaskPolicyItems": [
    {
      "accesses": [{"type": "select", "isAllowed": true}],
      "users": ["analyst_*"],
      "dataMaskInfo": {
        "dataMaskType": "MASK_SHOW_LAST_4"
      }
    },
    {
      "accesses": [{"type": "select", "isAllowed": true}],
      "users": ["data_engineer_*"],
      "dataMaskInfo": {
        "dataMaskType": "MASK_NONE"
      }
    }
  ]
}
```

---

## 4. Handling Procedures by Classification

### 4.1 Access Control Matrices

```
┌──────────────────┬───────────────────────────────────────────────────────────────────────┐
│  Control         │  PUBLIC        │  INTERNAL      │  CONFIDENTIAL  │  RESTRICTED        │
├──────────────────┼────────────────┼────────────────┼────────────────┼────────────────────┤
│  Authentication  │  None          │  SSO           │  SSO + MFA     │  SSO + MFA + cert  │
│  Authorization   │  Open          │  RBAC          │  ABAC + RBAC   │  PBAC + need-to-know│
│  Access Review   │  Annual        │  Quarterly     │  Monthly       │  Weekly/Real-time  │
│  Logging         │  None          │  Access logs   │  Full audit    │  SIEM + immutable  │
│  Approval        │  Self-service  │  Manager       │  Data owner    │  CISO + Legal      │
│  Session Timeout │  8h            │  4h            │  1h            │  15min             │
│  Network Access  │  Public        │  Corp network  │  VPN/mTLS      │  Isolated segment  │
└──────────────────┴────────────────┴────────────────┴────────────────┴────────────────────┘
```

**PBAC (Policy-Based Access Control)** for RESTRICTED data:

```python
# OPA (Open Policy Agent) policy for RESTRICTED data access
"""
package data.restricted

default allow = false

allow {
    input.user.clearance_level >= data.asset.classification_level
    input.user.need_to_know[_] == data.asset.compartment
    input.request.time_window.start >= data.asset.access_window.start
    input.request.time_window.end <= data.asset.access_window.end
    not user_under_investigation(input.user.id)
    valid_justification(input.request.justification)
}

user_under_investigation(user_id) {
    data.investigations[_].user_id == user_id
    data.investigations[_].status == "active"
}

valid_justification(justification) {
    count(justification) > 50
    justification != data.previous_justifications[_]
}
"""
```

### 4.2 Encryption Requirements by Level

| Classification | At Rest | In Transit | In Use | Key Management |
|---|---|---|---|---|
| PUBLIC | Optional | TLS 1.2+ recommended | N/A | Standard |
| INTERNAL | AES-128+ | TLS 1.2+ required | N/A | KMS |
| CONFIDENTIAL | AES-256, TDE | TLS 1.3, mTLS | Application-level | HSM-backed KMS |
| RESTRICTED | AES-256-GCM, envelope encryption | TLS 1.3 + mTLS + certificate pinning | Confidential computing / SGX | HSM, BYOK, dual-control key ceremony |

```sql
-- PostgreSQL: Transparent Data Encryption for CONFIDENTIAL+ tables
-- (Using pgcrypto for column-level encryption)

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Encrypt RESTRICTED columns at application layer
CREATE OR REPLACE FUNCTION encrypt_restricted(plaintext TEXT, key_id TEXT)
RETURNS BYTEA AS $$
DECLARE
    encryption_key BYTEA;
BEGIN
    -- Fetch key from vault (never hardcode)
    encryption_key := get_key_from_vault(key_id);
    RETURN pgp_sym_encrypt(plaintext, encode(encryption_key, 'base64'));
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Column-level encryption for SSN
ALTER TABLE customers ADD COLUMN ssn_encrypted BYTEA;
UPDATE customers SET ssn_encrypted = encrypt_restricted(ssn, 'ssn-key-2024');
ALTER TABLE customers DROP COLUMN ssn;
```

### 4.3 Retention Policies by Level

```yaml
# Data retention policy document
retention_policies:
  PUBLIC:
    minimum: none
    maximum: indefinite
    review_cycle: annual
    disposal_method: standard_delete
    legal_hold_override: true

  INTERNAL:
    minimum: 1_year
    maximum: 5_years
    review_cycle: annual
    disposal_method: secure_delete
    legal_hold_override: true
    exceptions:
      - type: financial_records
        minimum: 7_years  # SOX
      - type: employment_records
        minimum: 3_years  # EEOC

  CONFIDENTIAL:
    minimum: varies_by_regulation
    maximum: purpose_fulfilled_plus_buffer
    review_cycle: quarterly
    disposal_method: cryptographic_erasure
    legal_hold_override: true
    regulatory_floors:
      GDPR: purpose_limitation  # No longer than necessary
      HIPAA: 6_years_from_creation_or_last_effective_date
      PCI_DSS: 1_year_transaction_logs
      SOX: 7_years

  RESTRICTED:
    minimum: regulatory_or_contractual_requirement
    maximum: strict_purpose_limitation
    review_cycle: monthly
    disposal_method: nist_800_88_purge_or_destroy
    legal_hold_override: requires_ciso_approval
    key_destruction: concurrent_with_data
```

### 4.4 Transmission Rules

```
┌──────────────────┬────────────────────────────────────────────────────────────────┐
│  Classification  │  Transmission Requirements                                     │
├──────────────────┼────────────────────────────────────────────────────────────────┤
│  PUBLIC          │  No restrictions. Standard HTTP acceptable.                    │
│  INTERNAL        │  TLS 1.2+ required. No clear-text email. VPN for remote.     │
│  CONFIDENTIAL    │  TLS 1.3 + mTLS. Encrypted email (S/MIME or PGP). No USB.    │
│                  │  DLP monitoring active. Watermarked if printed.               │
│  RESTRICTED      │  Dedicated encrypted channel. mTLS + cert pinning.            │
│                  │  No email transmission. Hardware-encrypted media only.         │
│                  │  Courier with chain of custody for physical media.            │
│                  │  Pre-approved recipients list. Transfer logged in SIEM.       │
└──────────────────┴────────────────────────────────────────────────────────────────┘
```

### 4.5 Disposal and Destruction (NIST 800-88)

NIST SP 800-88 Rev. 1 "Guidelines for Media Sanitization" defines three methods:

**Clear** — logical overwrite using standard write commands:
- Appropriate for: PUBLIC and INTERNAL data
- Method: Single-pass overwrite with fixed pattern, then verify
- Limitation: May not address wear-leveled flash or remapped sectors

**Purge** — renders data unrecoverable with state-of-the-art lab techniques:
- Appropriate for: CONFIDENTIAL data
- Methods: Cryptographic erase (for SEDs), block erase (flash), degaussing (magnetic)
- Verification: Sample verification with forensic tools

**Destroy** — physical destruction rendering media unusable:
- Appropriate for: RESTRICTED data
- Methods: Disintegration, pulverization, incineration, shredding (cross-cut ≤2mm for paper)
- Verification: Visual confirmation of particle size compliance
- Documentation: Destruction certificate with witness signatures

```python
# Automated disposal workflow
class DataDisposalWorkflow:
    """Enforce disposal procedures based on classification."""

    DISPOSAL_MAP = {
        "PUBLIC": "standard_delete",
        "INTERNAL": "secure_delete",      # NIST Clear
        "CONFIDENTIAL": "crypto_erase",   # NIST Purge
        "RESTRICTED": "physical_destroy"   # NIST Destroy
    }

    def execute_disposal(self, asset_id, classification):
        method = self.DISPOSAL_MAP[classification]

        # Pre-disposal checks
        self._verify_no_legal_hold(asset_id)
        self._verify_retention_met(asset_id)
        self._log_disposal_intent(asset_id, method)

        if method == "standard_delete":
            self._delete_records(asset_id)
        elif method == "secure_delete":
            self._overwrite_then_delete(asset_id, passes=1)
        elif method == "crypto_erase":
            self._destroy_encryption_key(asset_id)
            self._verify_unreadable(asset_id)
        elif method == "physical_destroy":
            self._create_destruction_ticket(asset_id)
            self._notify_physical_security(asset_id)
            # Physical destruction requires manual execution + certificate

        self._log_disposal_complete(asset_id, method)
        self._update_data_inventory(asset_id, status="DESTROYED")
```

### 4.6 Incident Response Escalation by Data Class

```yaml
incident_response_escalation:
  PUBLIC:
    notification_window: 72h
    escalation_chain: [security_ops]
    external_notification: none
    forensics: optional
    
  INTERNAL:
    notification_window: 48h
    escalation_chain: [security_ops, it_management]
    external_notification: none
    forensics: basic_triage

  CONFIDENTIAL:
    notification_window: 24h
    escalation_chain: [security_ops, ciso, legal, affected_business_unit]
    external_notification: 
      - regulatory_if_required  # GDPR 72h, HIPAA 60d
      - affected_individuals_if_required
    forensics: full_investigation
    containment_sla: 4h

  RESTRICTED:
    notification_window: 1h
    escalation_chain: [security_ops, ciso, ceo, legal, board_if_material]
    external_notification:
      - immediate_regulatory_notification
      - law_enforcement_if_applicable
      - affected_individuals_without_delay
    forensics: external_forensic_firm
    containment_sla: 30min
    war_room: immediate_activation
```

---

## 5. Data Loss Prevention (DLP)

DLP systems detect, monitor, and block unauthorized data exfiltration across network, endpoint, and cloud channels.

### 5.1 Network DLP

Network DLP operates inline on traffic flows:

**Inline Proxy (Forward/Reverse):**
- Inspects HTTPS traffic via TLS interception (MITM with trusted CA)
- Examines email (SMTP), web uploads (HTTP POST/PUT), file transfers (FTP/SFTP)
- Can block, quarantine, or encrypt in real-time

**Email Gateway DLP:**
```yaml
# Email DLP policy example
policy:
  name: "Block PCI Data in Email"
  trigger:
    content_match:
      - type: credit_card_number
        min_count: 1
        confidence: HIGH
      - type: regex
        pattern: '\b4\d{3}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'
    recipient_match:
      - external: true  # Only trigger on external recipients
  actions:
    - block_delivery
    - notify_sender:
        message: "Email blocked: contains credit card data. Use secure portal."
    - notify_dlp_team
    - log_incident:
        severity: HIGH
        include_headers: true
        include_snippet: false  # Don't log the actual PCI data
```

**Network DLP architecture considerations:**
- Placement: after firewall, before internet egress
- Encrypted traffic: requires TLS inspection certificate deployed to endpoints
- Performance: sizing for throughput (hardware appliance for >10Gbps)
- Bypass list: certificate-pinned applications, healthcare portals, banking sites

### 5.2 Endpoint DLP

Agent-based DLP installed on workstations and servers:

```json
{
  "endpoint_dlp_policy": {
    "name": "Restrict Classified Data Movement",
    "rules": [
      {
        "name": "Block USB Copy of Confidential+",
        "trigger": {
          "action": "file_copy",
          "destination": "removable_media",
          "content_classification": ["CONFIDENTIAL", "RESTRICTED"]
        },
        "response": {
          "action": "block",
          "user_notification": "Copying classified data to USB is prohibited.",
          "justification_override": false,
          "log": true
        }
      },
      {
        "name": "Warn on Screen Capture of Confidential",
        "trigger": {
          "action": "screen_capture",
          "window_contains_classification": ["CONFIDENTIAL"]
        },
        "response": {
          "action": "warn",
          "user_notification": "Screen capture of confidential data detected. Proceed?",
          "justification_override": true,
          "log": true
        }
      },
      {
        "name": "Block Print of Restricted",
        "trigger": {
          "action": "print",
          "content_classification": ["RESTRICTED"]
        },
        "response": {
          "action": "block",
          "user_notification": "Printing RESTRICTED data requires CISO approval.",
          "justification_override": false,
          "approval_workflow": "ciso_print_approval",
          "log": true
        }
      },
      {
        "name": "Monitor Cloud Upload of Internal+",
        "trigger": {
          "action": "browser_upload",
          "destination_not_in": ["approved-saas-list"],
          "content_classification": ["INTERNAL", "CONFIDENTIAL", "RESTRICTED"]
        },
        "response": {
          "action": "block",
          "user_notification": "Upload to unapproved cloud service blocked.",
          "log": true
        }
      }
    ]
  }
}
```

### 5.3 Cloud DLP (CASB Integration)

Cloud Access Security Broker integration provides DLP for SaaS:

```python
# CASB DLP policy configuration (conceptual)
casb_policy = {
    "name": "SaaS DLP - Prevent PII Sharing",
    "cloud_apps": ["salesforce", "slack", "google-workspace", "box"],
    "inspection_mode": "api",  # or "proxy" for real-time
    "rules": [
        {
            "name": "Block External Sharing of PII Files",
            "condition": {
                "content_inspection": {
                    "info_types": ["PII", "PHI", "PCI"],
                    "min_confidence": 0.85
                },
                "sharing_scope": "external"
            },
            "action": "revoke_sharing",
            "notification": {
                "user": True,
                "admin": True,
                "incident_ticket": True
            }
        },
        {
            "name": "Quarantine Sensitive Uploads to Unapproved Apps",
            "condition": {
                "app_risk_score": {"operator": ">=", "value": 7},
                "content_classification": ["CONFIDENTIAL", "RESTRICTED"]
            },
            "action": "quarantine",
            "admin_review_required": True
        }
    ]
}
```

### 5.4 API-Based DLP for SaaS

```python
# Custom DLP integration via API for internal SaaS platforms
import hashlib
from typing import Optional

class APIDLPGateway:
    """Intercept and inspect API responses for classified data leakage."""

    def __init__(self, dlp_engine, policy_store):
        self.dlp_engine = dlp_engine
        self.policy_store = policy_store

    def inspect_response(self, endpoint: str, response_body: dict, user_context: dict) -> dict:
        """
        Inspect API response before delivery to client.
        Apply masking/blocking based on user clearance vs data classification.
        """
        policy = self.policy_store.get_policy(endpoint)
        if not policy:
            return response_body

        findings = self.dlp_engine.inspect(response_body)
        
        for finding in findings:
            field_classification = finding['classification']
            user_clearance = user_context.get('clearance_level', 'PUBLIC')
            
            if not self._user_authorized(user_clearance, field_classification):
                response_body = self._apply_masking(
                    response_body, 
                    finding['field_path'],
                    policy.get('masking_strategy', 'redact')
                )
                self._log_dlp_event(finding, user_context, 'masked')

        return response_body

    def _user_authorized(self, user_level: str, data_level: str) -> bool:
        hierarchy = {'PUBLIC': 0, 'INTERNAL': 1, 'CONFIDENTIAL': 2, 'RESTRICTED': 3}
        return hierarchy.get(user_level, 0) >= hierarchy.get(data_level, 3)

    def _apply_masking(self, body: dict, field_path: str, strategy: str) -> dict:
        """Apply masking strategy to a specific field."""
        if strategy == 'redact':
            return self._set_nested(body, field_path, '[REDACTED]')
        elif strategy == 'partial':
            value = self._get_nested(body, field_path)
            masked = value[:2] + '*' * (len(value) - 4) + value[-2:] if len(value) > 4 else '****'
            return self._set_nested(body, field_path, masked)
        elif strategy == 'hash':
            value = self._get_nested(body, field_path)
            hashed = hashlib.sha256(value.encode()).hexdigest()[:12]
            return self._set_nested(body, field_path, f'hash:{hashed}')
        return body
```

### 5.5 DLP Policy Design

**Detection methods:**

1. **Regex patterns** — fast, high-volume, deterministic
   - Best for: structured data (SSN, credit cards, account numbers)
   - Weakness: high false-positive rate without context

2. **Exact Data Match (EDM)** — fingerprint actual sensitive records
   - Process: hash columns from sensitive database, match against egress traffic
   - Best for: customer lists, employee records, proprietary databases
   - Weakness: requires periodic re-indexing as source data changes

3. **Document Fingerprinting (IDM)** — structural hash of document templates
   - Process: compute structural fingerprint of sensitive document forms
   - Best for: contracts, financial statements, design documents
   - Weakness: minor formatting changes can evade detection

4. **Machine Learning classifiers** — trained on labeled sensitive/non-sensitive corpora
   - Best for: unstructured data, nuanced context-dependent classification
   - Weakness: requires training data, periodic retraining, explainability challenges

### 5.6 False Positive Management

False positives erode user trust and cause "alert fatigue." Strategies:

```python
class DLPFalsePositiveManager:
    """Manage and reduce DLP false positives."""

    def __init__(self, incident_store, policy_engine):
        self.incident_store = incident_store
        self.policy_engine = policy_engine

    def analyze_fp_rate(self, policy_id: str, window_days: int = 30) -> dict:
        """Calculate false positive metrics for a policy."""
        incidents = self.incident_store.query(
            policy_id=policy_id,
            start_date=datetime.utcnow() - timedelta(days=window_days)
        )
        
        total = len(incidents)
        confirmed_fp = len([i for i in incidents if i.resolution == 'FALSE_POSITIVE'])
        confirmed_tp = len([i for i in incidents if i.resolution == 'TRUE_POSITIVE'])
        unresolved = total - confirmed_fp - confirmed_tp
        
        fp_rate = confirmed_fp / total if total > 0 else 0
        
        return {
            "policy_id": policy_id,
            "total_incidents": total,
            "false_positives": confirmed_fp,
            "true_positives": confirmed_tp,
            "unresolved": unresolved,
            "fp_rate": fp_rate,
            "recommendation": self._recommend_action(fp_rate, total)
        }

    def _recommend_action(self, fp_rate: float, volume: int) -> str:
        if fp_rate > 0.7 and volume > 100:
            return "CRITICAL: Disable or significantly tune this policy. >70% FP rate."
        elif fp_rate > 0.5:
            return "HIGH: Increase confidence threshold or add exclusion contexts."
        elif fp_rate > 0.3:
            return "MEDIUM: Review regex patterns and add allowlist entries."
        elif fp_rate > 0.1:
            return "LOW: Acceptable FP rate. Monitor quarterly."
        else:
            return "OPTIMAL: Policy performing well."

    def create_allowlist_entry(self, policy_id: str, context: dict):
        """Add verified false-positive context to allowlist."""
        entry = {
            "policy_id": policy_id,
            "exclusion_type": context.get("type"),  # domain, user, file_path, content_hash
            "value": context.get("value"),
            "created_by": context.get("analyst"),
            "justification": context.get("justification"),
            "expiry": context.get("expiry"),  # Allowlist entries should expire
            "review_date": context.get("review_date")
        }
        self.policy_engine.add_exclusion(entry)
```

---

## 6. Database-Specific Classification

### 6.1 SQL Server Data Discovery & Classification

SQL Server 2019+ includes native data discovery and classification:

```sql
-- Add classification labels
ADD SENSITIVITY CLASSIFICATION TO [dbo].[Customers].[SSN]
WITH (LABEL = 'Highly Confidential', LABEL_ID = '7A621345-...',
      INFORMATION_TYPE = 'National ID', INFORMATION_TYPE_ID = 'E7A8F...',
      RANK = CRITICAL);

ADD SENSITIVITY CLASSIFICATION TO [dbo].[Customers].[Email]
WITH (LABEL = 'Confidential', LABEL_ID = '331F0B...',
      INFORMATION_TYPE = 'Contact Info', INFORMATION_TYPE_ID = '5C503...',
      RANK = HIGH);

ADD SENSITIVITY CLASSIFICATION TO [dbo].[Orders].[OrderTotal]
WITH (LABEL = 'General', LABEL_ID = '92F98...',
      INFORMATION_TYPE = 'Financial', INFORMATION_TYPE_ID = 'C64AFA...',
      RANK = MEDIUM);

-- Query all classifications
SELECT 
    schema_name(o.schema_id) AS schema_name,
    o.name AS table_name,
    c.name AS column_name,
    sc.label,
    sc.information_type,
    sc.rank,
    sc.rank_desc
FROM sys.sensitivity_classifications sc
JOIN sys.all_columns c ON sc.major_id = c.object_id AND sc.minor_id = c.column_id
JOIN sys.objects o ON c.object_id = o.object_id
ORDER BY sc.rank DESC;

-- Dynamic Data Masking based on classification
ALTER TABLE Customers
ALTER COLUMN SSN ADD MASKED WITH (FUNCTION = 'partial(0,"XXX-XX-",4)');

ALTER TABLE Customers
ALTER COLUMN Email ADD MASKED WITH (FUNCTION = 'email()');

ALTER TABLE Customers
ALTER COLUMN PhoneNumber ADD MASKED WITH (FUNCTION = 'default()');

-- Grant unmask to specific roles
GRANT UNMASK TO [DataAnalyst_PII_Authorized];
```

**SQL Server Auditing for classified data access:**

```sql
-- Create audit for classified data access
CREATE SERVER AUDIT ClassifiedDataAudit
TO FILE (FILEPATH = 'D:\SQLAudit\', MAXSIZE = 1 GB, MAX_FILES = 10)
WITH (QUEUE_DELAY = 1000, ON_FAILURE = CONTINUE);

CREATE DATABASE AUDIT SPECIFICATION ClassifiedDataSpec
FOR SERVER AUDIT ClassifiedDataAudit
ADD (SELECT ON [dbo].[Customers] BY [public]),
ADD (UPDATE ON [dbo].[Customers] BY [public]),
ADD (INSERT ON [dbo].[Customers] BY [public]),
ADD (DELETE ON [dbo].[Customers] BY [public]);

ALTER SERVER AUDIT ClassifiedDataAudit WITH (STATE = ON);
ALTER DATABASE AUDIT SPECIFICATION ClassifiedDataSpec WITH (STATE = ON);
```

### 6.2 Oracle Data Safe

Oracle Data Safe provides a comprehensive classification engine:

```sql
-- Oracle Data Safe discovers sensitive data and applies classification
-- Configuration via Oracle Cloud Console or REST API

-- Manual classification using Oracle Label Security (OLS)
-- Step 1: Create policy
BEGIN
  SA_SYSDBA.CREATE_POLICY(
    policy_name => 'DATA_CLASS_POLICY',
    column_name => 'OLS_LABEL',
    default_options => 'READ_CONTROL,WRITE_CONTROL,CHECK_CONTROL'
  );
END;
/

-- Step 2: Create levels
BEGIN
  SA_COMPONENTS.CREATE_LEVEL(
    policy_name => 'DATA_CLASS_POLICY',
    level_num   => 100,
    short_name  => 'PUB',
    long_name   => 'PUBLIC'
  );
  SA_COMPONENTS.CREATE_LEVEL(
    policy_name => 'DATA_CLASS_POLICY',
    level_num   => 200,
    short_name  => 'INT',
    long_name   => 'INTERNAL'
  );
  SA_COMPONENTS.CREATE_LEVEL(
    policy_name => 'DATA_CLASS_POLICY',
    level_num   => 300,
    short_name  => 'CONF',
    long_name   => 'CONFIDENTIAL'
  );
  SA_COMPONENTS.CREATE_LEVEL(
    policy_name => 'DATA_CLASS_POLICY',
    level_num   => 400,
    short_name  => 'REST',
    long_name   => 'RESTRICTED'
  );
END;
/

-- Step 3: Apply policy to table
BEGIN
  SA_POLICY_ADMIN.APPLY_TABLE_POLICY(
    policy_name    => 'DATA_CLASS_POLICY',
    schema_name    => 'HR',
    table_name     => 'EMPLOYEES',
    table_options  => 'READ_CONTROL,WRITE_CONTROL'
  );
END;
/

-- Step 4: Set user labels
BEGIN
  SA_USER_ADMIN.SET_USER_LABELS(
    policy_name => 'DATA_CLASS_POLICY',
    user_name   => 'HR_ANALYST',
    max_level   => 'CONF'
  );
  SA_USER_ADMIN.SET_USER_LABELS(
    policy_name => 'DATA_CLASS_POLICY',
    user_name   => 'EXTERNAL_AUDITOR',
    max_level   => 'INT'
  );
END;
/
```

### 6.3 PostgreSQL Row-Level Security by Classification

```sql
-- Enable RLS on classified table
ALTER TABLE customer_records ENABLE ROW LEVEL SECURITY;

-- Add classification column
ALTER TABLE customer_records ADD COLUMN data_classification TEXT 
  DEFAULT 'INTERNAL' CHECK (data_classification IN ('PUBLIC', 'INTERNAL', 'CONFIDENTIAL', 'RESTRICTED'));

-- Create role hierarchy
CREATE ROLE public_reader;
CREATE ROLE internal_reader;
CREATE ROLE confidential_reader;
CREATE ROLE restricted_reader;

GRANT public_reader TO internal_reader;
GRANT internal_reader TO confidential_reader;
GRANT confidential_reader TO restricted_reader;

-- RLS policies based on classification
CREATE POLICY public_access ON customer_records
    FOR SELECT
    TO public_reader
    USING (data_classification = 'PUBLIC');

CREATE POLICY internal_access ON customer_records
    FOR SELECT
    TO internal_reader
    USING (data_classification IN ('PUBLIC', 'INTERNAL'));

CREATE POLICY confidential_access ON customer_records
    FOR SELECT
    TO confidential_reader
    USING (data_classification IN ('PUBLIC', 'INTERNAL', 'CONFIDENTIAL'));

CREATE POLICY restricted_access ON customer_records
    FOR SELECT
    TO restricted_reader
    USING (TRUE);  -- Can see all levels

-- Prevent modification of classification column except by admins
CREATE POLICY classification_immutable ON customer_records
    FOR UPDATE
    USING (TRUE)
    WITH CHECK (
        data_classification = (SELECT data_classification FROM customer_records WHERE id = customer_records.id)
        OR current_user = 'data_governance_admin'
    );

-- Function to classify rows based on content
CREATE OR REPLACE FUNCTION auto_classify_row()
RETURNS TRIGGER AS $$
BEGIN
    -- Auto-classify based on content patterns
    IF NEW.ssn IS NOT NULL OR NEW.medical_record IS NOT NULL THEN
        NEW.data_classification := 'RESTRICTED';
    ELSIF NEW.email IS NOT NULL OR NEW.phone IS NOT NULL OR NEW.address IS NOT NULL THEN
        NEW.data_classification := 'CONFIDENTIAL';
    ELSIF NEW.employee_id IS NOT NULL THEN
        NEW.data_classification := 'INTERNAL';
    ELSE
        NEW.data_classification := 'PUBLIC';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER classify_on_insert
    BEFORE INSERT ON customer_records
    FOR EACH ROW EXECUTE FUNCTION auto_classify_row();
```

### 6.4 MongoDB Field-Level Encryption by Sensitivity

```javascript
// MongoDB Client-Side Field Level Encryption (CSFLE)
// Encrypt fields based on their classification level

const { MongoClient, ClientEncryption } = require('mongodb');

// Key vault configuration
const keyVaultNamespace = 'encryption.__keyVault';
const kmsProviders = {
  aws: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY
  }
};

// Schema map: define encryption per classification
const schemaMap = {
  'production.customers': {
    bsonType: 'object',
    encryptMetadata: {
      keyId: [/* data encryption key UUID */]
    },
    properties: {
      // RESTRICTED fields: deterministic encryption (allows equality queries)
      ssn: {
        encrypt: {
          bsonType: 'string',
          algorithm: 'AEAD_AES_256_CBC_HMAC_SHA_512-Deterministic',
          keyId: [/* restricted-tier DEK */]
        }
      },
      // CONFIDENTIAL fields: random encryption (no queryability)
      medicalHistory: {
        encrypt: {
          bsonType: 'object',
          algorithm: 'AEAD_AES_256_CBC_HMAC_SHA_512-Random',
          keyId: [/* confidential-tier DEK */]
        }
      },
      email: {
        encrypt: {
          bsonType: 'string',
          algorithm: 'AEAD_AES_256_CBC_HMAC_SHA_512-Deterministic',
          keyId: [/* confidential-tier DEK */]
        }
      },
      // INTERNAL and PUBLIC fields: no encryption at field level
      name: { bsonType: 'string' },  // CONFIDENTIAL but needs search — use tokenization instead
      accountType: { bsonType: 'string' }  // PUBLIC
    }
  }
};

// Queryable Encryption (MongoDB 7.0+) for CONFIDENTIAL fields needing search
const encryptedFieldsMap = {
  'production.customers': {
    fields: [
      {
        path: 'email',
        bsonType: 'string',
        keyId: null,  // auto-generated
        queries: { queryType: 'equality' }
      },
      {
        path: 'ssn',
        bsonType: 'string',
        keyId: null,
        queries: { queryType: 'equality' }
      }
    ]
  }
};

async function createClassifiedConnection() {
  const client = new MongoClient(process.env.MONGODB_URI, {
    autoEncryption: {
      keyVaultNamespace,
      kmsProviders,
      schemaMap,
      encryptedFieldsMap
    }
  });
  await client.connect();
  return client;
}
```

### 6.5 Column-Level Access Control Patterns

```sql
-- PostgreSQL: view-based column access control

-- Create views per classification level
CREATE VIEW customers_public AS
SELECT 
    customer_id,
    country,
    account_type,
    created_at
FROM customers;

CREATE VIEW customers_internal AS
SELECT 
    customer_id,
    first_name,
    last_initial,  -- truncated
    country,
    state,
    account_type,
    created_at,
    last_login
FROM customers;

CREATE VIEW customers_confidential AS
SELECT 
    customer_id,
    first_name,
    last_name,
    email,
    phone,
    address_line1,
    city,
    state,
    zip_code,
    country,
    account_type,
    created_at,
    last_login
FROM customers;

-- RESTRICTED: direct table access (with audit)
-- Only granted to restricted_reader role with full audit logging

-- Grant view access by classification tier
GRANT SELECT ON customers_public TO public_reader;
GRANT SELECT ON customers_internal TO internal_reader;
GRANT SELECT ON customers_confidential TO confidential_reader;
GRANT SELECT ON customers TO restricted_reader;

-- Revoke direct table access from lower tiers
REVOKE ALL ON customers FROM public_reader, internal_reader, confidential_reader;
```

---

## 7. Cloud Data Classification

### 7.1 AWS Data Classification

#### Amazon Macie for S3

```python
import boto3

# Configure Macie with custom data identifiers
macie = boto3.client('macie2')

# Create custom data identifier for internal project codes
macie.create_custom_data_identifier(
    name='InternalProjectCode',
    description='Matches internal project identifiers',
    regex='PRJ-[A-Z]{3}-\\d{6}',
    keywords=['project', 'initiative', 'program'],
    maximumMatchDistance=50,
    severityLevels=[
        {'occurrencesThreshold': 1, 'severity': 'MEDIUM'},
        {'occurrencesThreshold': 10, 'severity': 'HIGH'}
    ]
)

# Create classification job
macie.create_classification_job(
    jobType='SCHEDULED',
    name='weekly-pii-scan',
    scheduleFrequency={'monthlySchedule': {'dayOfMonth': 1}},
    s3JobDefinition={
        'bucketDefinitions': [
            {
                'accountId': '123456789012',
                'buckets': ['prod-data-lake', 'analytics-warehouse']
            }
        ],
        'scoping': {
            'includes': {
                'and': [
                    {
                        'simpleScopeTerm': {
                            'comparator': 'STARTS_WITH',
                            'key': 'OBJECT_KEY',
                            'values': ['raw/', 'processed/', 'exports/']
                        }
                    },
                    {
                        'simpleScopeTerm': {
                            'comparator': 'EQ',
                            'key': 'OBJECT_EXTENSION',
                            'values': ['csv', 'json', 'parquet', 'avro']
                        }
                    }
                ]
            }
        }
    },
    managedDataIdentifierSelector='ALL'
)
```

#### AWS Lake Formation Permissions

```python
# Lake Formation: column-level access by classification
lf_client = boto3.client('lakeformation')

# Grant CONFIDENTIAL-tier access to analysts
lf_client.grant_permissions(
    Principal={'DataLakePrincipalIdentifier': 'arn:aws:iam::123456789012:role/DataAnalyst'},
    Resource={
        'TableWithColumns': {
            'DatabaseName': 'customer_analytics',
            'Name': 'user_profiles',
            'ColumnNames': ['user_id', 'signup_date', 'country', 'plan_type'],
            # Excludes: email, phone, address (CONFIDENTIAL columns)
        }
    },
    Permissions=['SELECT']
)

# Grant RESTRICTED-tier access to compliance team
lf_client.grant_permissions(
    Principal={'DataLakePrincipalIdentifier': 'arn:aws:iam::123456789012:role/ComplianceTeam'},
    Resource={
        'Table': {
            'DatabaseName': 'customer_analytics',
            'Name': 'user_profiles'
            # All columns — full access
        }
    },
    Permissions=['SELECT'],
    PermissionsWithGrantOption=[]
)
```

#### S3 Object Tagging for Classification

```python
s3 = boto3.client('s3')

# Tag objects with classification metadata
s3.put_object_tagging(
    Bucket='production-data',
    Key='exports/customer_report_2024.csv',
    Tagging={
        'TagSet': [
            {'Key': 'DataClassification', 'Value': 'CONFIDENTIAL'},
            {'Key': 'ContainsPII', 'Value': 'true'},
            {'Key': 'Regulations', 'Value': 'GDPR,CCPA'},
            {'Key': 'RetentionDays', 'Value': '1095'},
            {'Key': 'DataSteward', 'Value': 'privacy-team'}
        ]
    }
)

# S3 Bucket Policy: enforce classification tagging
bucket_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "RequireClassificationTag",
            "Effect": "Deny",
            "Principal": "*",
            "Action": "s3:PutObject",
            "Resource": "arn:aws:s3:::production-data/*",
            "Condition": {
                "StringNotLike": {
                    "s3:RequestObjectTag/DataClassification": ["PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"]
                }
            }
        }
    ]
}
```

### 7.2 GCP Data Classification

#### Google DLP API with De-identification

```python
from google.cloud import dlp_v2

def deidentify_by_classification(project_id, text, classification_level):
    """Apply de-identification appropriate to classification level."""
    dlp = dlp_v2.DlpServiceClient()
    parent = f"projects/{project_id}"

    # Define transforms per classification requirement
    transforms = {
        "CONFIDENTIAL": {
            "info_types": [
                {"name": "EMAIL_ADDRESS"},
                {"name": "PHONE_NUMBER"},
                {"name": "PERSON_NAME"}
            ],
            "primitive_transformation": {
                "character_mask_config": {
                    "masking_character": "*",
                    "number_to_mask": 0,  # mask all
                    "characters_to_ignore": [
                        {"common_characters_to_ignore": "PUNCTUATION"}
                    ]
                }
            }
        },
        "RESTRICTED": {
            "info_types": [
                {"name": "CREDIT_CARD_NUMBER"},
                {"name": "US_SOCIAL_SECURITY_NUMBER"},
                {"name": "MEDICAL_RECORD_NUMBER"}
            ],
            "primitive_transformation": {
                "crypto_replace_ffpe_fpe_config": {
                    "crypto_key": {
                        "kms_wrapped": {
                            "wrapped_key": "base64-wrapped-key",
                            "crypto_key_name": f"projects/{project_id}/locations/global/keyRings/dlp/cryptoKeys/restricted-tokenization"
                        }
                    },
                    "common_alphabet": "ALPHA_NUMERIC"
                }
            }
        }
    }

    transform_config = transforms.get(classification_level)
    if not transform_config:
        return text  # PUBLIC/INTERNAL: no transform needed in this context

    deidentify_config = {
        "info_type_transformations": {
            "transformations": [
                {
                    "info_types": transform_config["info_types"],
                    "primitive_transformation": transform_config["primitive_transformation"]
                }
            ]
        }
    }

    inspect_config = {
        "info_types": transform_config["info_types"],
        "min_likelihood": dlp_v2.Likelihood.LIKELY
    }

    response = dlp.deidentify_content(
        request={
            "parent": parent,
            "deidentify_config": deidentify_config,
            "inspect_config": inspect_config,
            "item": {"value": text}
        }
    )

    return response.item.value
```

#### BigQuery Column-Level Security

```sql
-- BigQuery: column-level access control using policy tags

-- Step 1: Create taxonomy (via API or Console)
-- taxonomy: "data_classification"
--   policy_tag: "public"
--   policy_tag: "internal"  
--   policy_tag: "confidential"
--   policy_tag: "restricted"

-- Step 2: Apply policy tags to columns (via schema update)
ALTER TABLE `project.dataset.customers`
ALTER COLUMN email SET POLICY TAG `projects/my-project/locations/us/taxonomies/data_classification/policyTags/confidential`;

ALTER TABLE `project.dataset.customers`
ALTER COLUMN ssn SET POLICY TAG `projects/my-project/locations/us/taxonomies/data_classification/policyTags/restricted`;

-- Step 3: Grant fine-grained reader access
-- IAM binding: grant datacatalog.categoryFineGrainedReader on policy tag to specific principals
-- Users without this role see NULL for protected columns (or query fails, depending on config)
```

### 7.3 Azure Data Classification

#### Microsoft Purview Scanning

```json
{
  "name": "sql-database-scan",
  "kind": "AzureSqlDatabaseCredential",
  "properties": {
    "scanRulesetName": "classified-data-ruleset",
    "credential": {
      "referenceName": "purview-scan-credential",
      "credentialType": "ServicePrincipal"
    },
    "collection": {
      "referenceName": "production-databases",
      "type": "CollectionReference"
    },
    "connectedVia": {
      "referenceName": "managed-vnet-runtime"
    }
  },
  "scanResults": [
    {
      "assetsDiscovered": 2847,
      "assetsClassified": 2103,
      "classificationBreakdown": {
        "Government_ID": 45,
        "Financial_Credit_Card": 12,
        "Personal_Email": 234,
        "Personal_Phone": 189,
        "Personal_Name": 567,
        "Healthcare_Medical_Record": 23,
        "Custom_Internal_ID": 1033
      }
    }
  ]
}
```

### 7.4 Multi-Cloud Classification Strategy

```yaml
# Multi-cloud classification governance framework
multi_cloud_strategy:
  principles:
    - classification_labels_are_portable_across_clouds
    - highest_classification_wins_when_clouds_disagree
    - single_source_of_truth_for_classification_catalog
    - enforcement_is_cloud_native_but_policy_is_centralized

  architecture:
    central_catalog: collibra  # or DataHub, Apache Atlas
    policy_engine: open_policy_agent
    
    aws:
      discovery: macie
      enforcement: lake_formation + s3_policies
      labeling: resource_tags + macie_findings
      
    gcp:
      discovery: dlp_api
      enforcement: bigquery_policy_tags + iam
      labeling: data_catalog + dlp_api
      
    azure:
      discovery: purview
      enforcement: purview_policies + sql_classification
      labeling: purview_labels + sensitivity_labels

  sync_workflow:
    # Bidirectional sync between central catalog and cloud-native tools
    - central_catalog_publishes_classification_decisions
    - cloud_scanners_discover_new_assets_and_propose_classifications
    - human_review_for_CONFIDENTIAL_and_RESTRICTED_proposals
    - auto_approve_PUBLIC_and_INTERNAL_with_high_confidence
    - classification_changes_trigger_access_control_updates

  cross_cloud_transfer_rules:
    RESTRICTED:
      - requires_equivalent_controls_at_destination
      - encrypted_in_transit_with_customer_managed_keys
      - transfer_logged_in_central_siem
      - destination_classification_verified_before_transfer
    CONFIDENTIAL:
      - encrypted_in_transit
      - destination_must_have_DLP_enabled
      - transfer_logged
```

---

## 8. Data Classification in CI/CD

### 8.1 Pre-Commit Hooks for PII Detection

```bash
#!/usr/bin/env bash
# .git/hooks/pre-commit — PII detection in staged files

set -euo pipefail

# Patterns that should never appear in code
RESTRICTED_PATTERNS=(
    '\b\d{3}-\d{2}-\d{4}\b'                          # SSN
    '\b4\d{3}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'   # Visa
    '\b5[1-5]\d{14}\b'                                 # Mastercard
    'AKIA[0-9A-Z]{16}'                                 # AWS access key
    '-----BEGIN (RSA |EC )?PRIVATE KEY-----'           # Private key
    '\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'  # Email (in non-test files)
)

VIOLATIONS=0
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM)

for file in $STAGED_FILES; do
    # Skip test files and fixtures for email pattern
    if [[ "$file" =~ (test|spec|fixture|mock|__test__) ]]; then
        continue
    fi
    
    # Skip binary files
    if file "$file" | grep -q "binary"; then
        continue
    fi

    for pattern in "${RESTRICTED_PATTERNS[@]}"; do
        if grep -qP "$pattern" "$file" 2>/dev/null; then
            echo "ERROR: Potential PII/secret detected in $file"
            echo "  Pattern: $pattern"
            grep -nP "$pattern" "$file" | head -3
            VIOLATIONS=$((VIOLATIONS + 1))
        fi
    done
done

if [ $VIOLATIONS -gt 0 ]; then
    echo ""
    echo "BLOCKED: $VIOLATIONS potential PII/secret violation(s) found."
    echo "If these are false positives, add to .pii-allowlist or use test data."
    exit 1
fi

exit 0
```

### 8.2 SAST Rules for Hardcoded Sensitive Data

```yaml
# semgrep rules for classified data leakage
rules:
  - id: hardcoded-secret-in-source
    patterns:
      - pattern-either:
          - pattern: |
              $VAR = "AKIA..."
          - pattern: |
              password = "..."
          - pattern: |
              api_key = "..."
          - pattern: |
              $VAR = "-----BEGIN PRIVATE KEY-----..."
    message: "Hardcoded secret detected. Use environment variables or secret manager."
    severity: ERROR
    metadata:
      classification: RESTRICTED
      cwe: CWE-798
      
  - id: pii-in-log-statement
    patterns:
      - pattern-either:
          - pattern: |
              logger.$METHOD(..., $EMAIL, ...)
          - pattern: |
              console.log(..., $SSN, ...)
          - pattern: |
              log.info(f"...{$USER.email}...")
    message: "Potential PII in log statement. Redact before logging."
    severity: WARNING
    metadata:
      classification: CONFIDENTIAL
      cwe: CWE-532

  - id: sql-query-returns-restricted-column
    pattern: |
      SELECT ... ssn ... FROM ...
    message: "Query returns RESTRICTED column (SSN). Ensure calling context is authorized."
    severity: INFO
    metadata:
      classification: RESTRICTED
```

### 8.3 Secrets Scanning

**gitleaks configuration:**

```toml
# .gitleaks.toml
title = "Custom gitleaks configuration"

[allowlist]
description = "Global allowlist"
paths = [
    '''(.*?)(test|spec|fixture|mock)(.*?)''',
    '''vendor/''',
    '''node_modules/'''
]

[[rules]]
id = "aws-access-key-id"
description = "AWS Access Key ID"
regex = '''(A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}'''
tags = ["key", "AWS"]
severity = "CRITICAL"

[[rules]]
id = "generic-credential"
description = "Generic Credential"
regex = '''(?i)(password|passwd|pwd|secret|token|api[_-]?key)\s*[=:]\s*['"][^\s'"]{8,}['"]'''
tags = ["credential", "generic"]
severity = "HIGH"
[rules.allowlist]
regexes = ['''(?i)(example|placeholder|test|dummy|fake|mock|sample)''']

[[rules]]
id = "private-key"
description = "Private Key"
regex = '''-----BEGIN (RSA |DSA |EC |PGP |OPENSSH )?PRIVATE KEY( BLOCK)?-----'''
tags = ["key", "private"]
severity = "CRITICAL"

[[rules]]
id = "database-url-with-password"
description = "Database connection string with embedded credentials"
regex = '''(?i)(postgres|mysql|mongodb|redis)://[^:]+:[^@]+@[^/]+'''
tags = ["database", "credential"]
severity = "CRITICAL"
```

**truffleHog integration in CI:**

```yaml
# GitHub Actions workflow
name: Secrets Scan
on:
  pull_request:
    branches: [main, develop]
  push:
    branches: [main]

jobs:
  trufflehog:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: TruffleHog Scan
        uses: trufflesecurity/trufflehog@main
        with:
          path: ./
          base: ${{ github.event.pull_request.base.sha || 'HEAD~1' }}
          head: HEAD
          extra_args: --only-verified --results=verified,unverified
```

### 8.4 Test Data Generation (No Production PII)

```python
from faker import Faker
import hashlib
from typing import Any

fake = Faker()
Faker.seed(42)  # Reproducible test data

class ClassifiedTestDataGenerator:
    """Generate synthetic test data that mimics production schema
    without containing real PII."""

    def generate_customer_record(self) -> dict:
        """Generate a fake customer record matching production schema."""
        return {
            "customer_id": f"CUST-{fake.uuid4()[:8].upper()}",
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "email": fake.email(),
            "phone": fake.phone_number(),
            "ssn": fake.ssn(),  # Faker generates structurally valid but fake SSNs
            "address": {
                "street": fake.street_address(),
                "city": fake.city(),
                "state": fake.state_abbr(),
                "zip": fake.zipcode()
            },
            "dob": fake.date_of_birth(minimum_age=18, maximum_age=90).isoformat(),
            "account_type": fake.random_element(["STANDARD", "PREMIUM", "ENTERPRISE"]),
            "created_at": fake.date_time_this_decade().isoformat()
        }

    def generate_test_dataset(self, count: int, classification_level: str) -> list:
        """Generate dataset appropriate for testing at given classification level."""
        records = []
        for _ in range(count):
            record = self.generate_customer_record()
            
            if classification_level == "PUBLIC":
                # Strip all PII for public-tier test scenarios
                record = {
                    "customer_id": record["customer_id"],
                    "account_type": record["account_type"],
                    "created_at": record["created_at"]
                }
            elif classification_level == "INTERNAL":
                # Remove CONFIDENTIAL+ fields
                del record["ssn"]
                del record["dob"]
                record["email"] = f"user-{record['customer_id'][-8:]}@test.internal"
                
            # CONFIDENTIAL and RESTRICTED: full fake data (still synthetic)
            records.append(record)
        
        return records


class ProductionDataAnonymizer:
    """Anonymize production data snapshots for test environments."""

    def __init__(self, salt: str):
        self.salt = salt

    def anonymize_for_test(self, record: dict, schema_classification: dict) -> dict:
        """Transform production record into test-safe version."""
        anonymized = {}
        
        for field, value in record.items():
            field_class = schema_classification.get(field, "PUBLIC")
            
            if field_class == "RESTRICTED":
                # Completely replace with synthetic
                anonymized[field] = self._generate_synthetic(field, value)
            elif field_class == "CONFIDENTIAL":
                # Tokenize: consistent mapping for referential integrity
                anonymized[field] = self._tokenize(field, value)
            elif field_class == "INTERNAL":
                # Generalize
                anonymized[field] = self._generalize(field, value)
            else:
                anonymized[field] = value
        
        return anonymized

    def _tokenize(self, field: str, value: Any) -> str:
        """Consistent one-way mapping preserving referential integrity."""
        token = hashlib.sha256(f"{self.salt}:{field}:{value}".encode()).hexdigest()[:16]
        return f"TOKEN-{token}"

    def _generalize(self, field: str, value: Any) -> Any:
        """Reduce precision while maintaining analytical utility."""
        if field == "age":
            return (int(value) // 10) * 10  # Age bands
        elif field == "zip_code":
            return str(value)[:3] + "00"  # Zip3
        return value

    def _generate_synthetic(self, field: str, value: Any) -> Any:
        """Replace with structurally valid synthetic data."""
        generators = {
            "ssn": lambda: fake.ssn(),
            "credit_card": lambda: fake.credit_card_number(),
            "medical_record": lambda: f"MRN-{fake.random_number(digits=8)}",
        }
        gen = generators.get(field, lambda: f"SYNTHETIC-{fake.uuid4()[:8]}")
        return gen()
```

### 8.5 Synthetic Data Approaches

```python
# Statistical synthetic data generation preserving analytical utility
# without containing any real individual's information

from dataclasses import dataclass
from typing import Optional
import numpy as np

@dataclass
class SyntheticDataConfig:
    """Configuration for synthetic data generation."""
    source_table: str
    target_classification: str  # Maximum classification of output
    preserve_distributions: bool = True
    preserve_correlations: bool = True
    k_anonymity: int = 5
    differential_privacy_epsilon: Optional[float] = 1.0

def generate_differentially_private_statistics(
    real_data,
    epsilon: float = 1.0,
    delta: float = 1e-5
):
    """
    Compute statistics with differential privacy guarantees.
    These statistics can then seed synthetic data generation
    without leaking individual records.
    """
    # Laplace mechanism for counting queries
    sensitivity = 1  # Each person affects count by at most 1
    noise_scale = sensitivity / epsilon
    
    noisy_stats = {}
    for column in real_data.columns:
        if real_data[column].dtype in ['int64', 'float64']:
            # Numeric: noisy mean and std
            true_mean = real_data[column].mean()
            true_std = real_data[column].std()
            noisy_stats[column] = {
                'mean': true_mean + np.random.laplace(0, noise_scale),
                'std': max(0.01, true_std + np.random.laplace(0, noise_scale)),
                'type': 'numeric'
            }
        else:
            # Categorical: noisy frequency distribution
            true_counts = real_data[column].value_counts()
            noisy_counts = true_counts + np.random.laplace(0, noise_scale, size=len(true_counts))
            noisy_counts = np.maximum(noisy_counts, 0)  # Clip negatives
            noisy_stats[column] = {
                'distribution': (noisy_counts / noisy_counts.sum()).to_dict(),
                'type': 'categorical'
            }
    
    return noisy_stats
```

---

## 9. Compliance Mapping

### 9.1 Classification to GDPR Article 9 (Special Categories)

GDPR Article 9 identifies "special categories" of personal data requiring explicit consent or statutory basis:

```yaml
gdpr_article_9_mapping:
  special_categories:
    - racial_or_ethnic_origin:
        classification: RESTRICTED
        lawful_basis: explicit_consent OR employment_law
        examples: [ethnicity_field, nationality, indigenous_status]
        
    - political_opinions:
        classification: RESTRICTED
        lawful_basis: explicit_consent
        examples: [party_membership, voting_records, political_donations]
        
    - religious_or_philosophical_beliefs:
        classification: RESTRICTED
        lawful_basis: explicit_consent
        examples: [religion_field, dietary_preferences_indicating_belief]
        
    - trade_union_membership:
        classification: RESTRICTED
        lawful_basis: explicit_consent OR employment_law
        examples: [union_dues_deduction, union_representative_flag]
        
    - genetic_data:
        classification: RESTRICTED
        lawful_basis: explicit_consent OR healthcare
        examples: [dna_sequences, genetic_test_results, hereditary_conditions]
        
    - biometric_data:
        classification: RESTRICTED
        lawful_basis: explicit_consent OR substantial_public_interest
        examples: [fingerprints, facial_geometry, iris_scans, voiceprints]
        
    - health_data:
        classification: RESTRICTED
        lawful_basis: explicit_consent OR healthcare_provision
        examples: [diagnoses, prescriptions, medical_history, disability_status]
        
    - sex_life_or_sexual_orientation:
        classification: RESTRICTED
        lawful_basis: explicit_consent
        examples: [gender_identity, sexual_orientation, partner_details]

  regular_personal_data:
    - name: { classification: CONFIDENTIAL, lawful_basis: legitimate_interest }
    - email: { classification: CONFIDENTIAL, lawful_basis: contract }
    - phone: { classification: CONFIDENTIAL, lawful_basis: contract }
    - address: { classification: CONFIDENTIAL, lawful_basis: contract }
    - ip_address: { classification: CONFIDENTIAL, lawful_basis: legitimate_interest }
    - cookie_identifier: { classification: INTERNAL, lawful_basis: consent }
```

### 9.2 HIPAA PHI Identification

```python
# HIPAA PHI classification decision engine
class HIPAAClassifier:
    """Classify data elements under HIPAA rules."""

    PHI_IDENTIFIERS = {
        "name", "geographic_subdivision_smaller_than_state",
        "dates_except_year", "phone", "fax", "email",
        "ssn", "medical_record_number", "health_plan_beneficiary_number",
        "account_number", "certificate_license_number",
        "vehicle_identifier", "device_identifier",
        "web_url", "ip_address", "biometric_identifier",
        "face_photo", "unique_identifying_number"
    }

    def classify(self, field_name: str, field_content_type: str, 
                 associated_with_health_info: bool) -> dict:
        """
        Determine HIPAA classification for a data field.
        PHI = health information + identifier that links to individual.
        """
        is_identifier = self._is_phi_identifier(field_name, field_content_type)
        
        if is_identifier and associated_with_health_info:
            return {
                "classification": "RESTRICTED",
                "hipaa_category": "PHI",
                "electronic": True,  # ePHI if stored/transmitted electronically
                "required_safeguards": ["administrative", "physical", "technical"],
                "minimum_necessary_rule": True,
                "breach_notification": "60_days_to_hhs_affected_individuals_media_if_500plus",
                "retention_minimum": "6_years"
            }
        elif is_identifier:
            return {
                "classification": "CONFIDENTIAL",
                "hipaa_category": "PII_not_PHI",
                "note": "Identifier present but not linked to health information"
            }
        elif associated_with_health_info:
            return {
                "classification": "CONFIDENTIAL",
                "hipaa_category": "health_info_deidentified",
                "note": "Health info without identifiers — may still require protection"
            }
        else:
            return {
                "classification": "INTERNAL",
                "hipaa_category": "not_applicable"
            }

    def _is_phi_identifier(self, field_name: str, content_type: str) -> bool:
        normalized = field_name.lower().replace(" ", "_").replace("-", "_")
        return (normalized in self.PHI_IDENTIFIERS or 
                content_type in self.PHI_IDENTIFIERS)
```

### 9.3 PCI-DSS Cardholder Data Environment Scoping

```yaml
pci_dss_scoping:
  # CDE scope determined by where cardholder data flows
  in_scope_systems:
    category_1_cde:
      description: "Systems that store, process, or transmit CHD/SAD"
      classification: RESTRICTED
      examples:
        - payment_processing_servers
        - databases_with_PAN
        - POS_terminals
        - payment_gateway_integration
      controls: "All PCI-DSS requirements apply"

    category_2_connected:
      description: "Systems connected to CDE but don't store/process CHD"
      classification: CONFIDENTIAL
      examples:
        - dns_servers_for_cde
        - log_aggregators_receiving_cde_logs
        - jump_hosts_to_cde
        - monitoring_systems
      controls: "Applicable PCI-DSS requirements"

    category_2a_security_impacting:
      description: "Systems that could impact CDE security"
      classification: CONFIDENTIAL
      examples:
        - firewalls_segmenting_cde
        - ids_ips_monitoring_cde
        - authentication_systems
        - antivirus_management
      controls: "Requirements related to their function"

  out_of_scope:
    description: "Systems with no connectivity to CDE (validated segmentation)"
    classification: INTERNAL_or_below
    validation: "Penetration testing must confirm isolation"

  scope_reduction_techniques:
    - network_segmentation: "Isolate CDE on dedicated VLAN"
    - tokenization: "Replace PAN with non-reversible token outside CDE"
    - p2pe: "Point-to-point encryption removes merchant from scope"
    - outsourcing: "PCI-compliant third party (verify AOC)"
```

### 9.4 SOX Financial Data Classification

```yaml
sox_classification:
  material_financial_data:
    classification: RESTRICTED
    description: "Data that could materially affect financial statements"
    examples:
      - revenue_recognition_data
      - asset_valuations
      - liability_calculations
      - earnings_before_announcement
      - merger_acquisition_financials
    controls:
      - segregation_of_duties
      - change_management_approval
      - immutable_audit_trail
      - access_limited_to_authorized_personnel
    retention: 7_years_minimum

  supporting_financial_data:
    classification: CONFIDENTIAL
    description: "Data supporting financial reporting accuracy"
    examples:
      - general_ledger_entries
      - accounts_payable_receivable
      - inventory_records
      - payroll_data
      - tax_calculations
    controls:
      - role_based_access
      - quarterly_access_review
      - change_logging
    retention: 7_years_minimum

  internal_controls_documentation:
    classification: CONFIDENTIAL
    description: "IT General Controls and application control evidence"
    examples:
      - access_review_reports
      - change_management_tickets
      - backup_verification_logs
      - user_provisioning_records
    retention: 7_years_minimum
```

### 9.5 NIST 800-171 CUI Marking Requirements

Controlled Unclassified Information (CUI) marking under NIST 800-171:

```
CUI Banner Marking Format:
┌─────────────────────────────────────────────────────┐
│  CUI // SP-HLTH / SP-PRIV // NOFORN                │
│                                                      │
│  Category: Controlled Technical Information          │
│  Dissemination: NOFORN (No Foreign Nationals)       │
│  Handling: HIPAA Privacy, Health Information        │
└─────────────────────────────────────────────────────┘

Portion Marking:
(CUI) This paragraph contains controlled unclassified information
regarding the technical specifications of the defense system.

(CUI//SP-HLTH) Patient records indicate treatment history for...
```

```python
# CUI marking implementation for documents
class CUIMarker:
    """Apply CUI markings per NIST 800-171 and 32 CFR Part 2002."""

    CUI_CATEGORIES = {
        "CTI": "Controlled Technical Information",
        "PRVCY": "Privacy Information",
        "HLTH": "Health Information",
        "PROPIN": "Proprietary Business Information",
        "LES": "Law Enforcement Sensitive",
        "FEDCON": "Federal Contract Information",
        "ITAR": "International Traffic in Arms Regulations",
        "EAR": "Export Administration Regulations",
    }

    DISSEMINATION_CONTROLS = {
        "NOFORN": "No Foreign Nationals",
        "FED ONLY": "Federal Employees Only",
        "FEDCON": "Federal Employees and Contractors",
        "DL ONLY": "Dissemination List Only",
    }

    def generate_banner(self, categories: list, dissemination: list = None,
                       specified: bool = False) -> str:
        """Generate CUI banner marking."""
        prefix = "CUI"
        
        # Specified vs. Basic CUI
        cat_prefix = "SP" if specified else ""
        
        cat_marks = []
        for cat in categories:
            if cat_prefix:
                cat_marks.append(f"{cat_prefix}-{cat}")
            else:
                cat_marks.append(cat)
        
        banner = f"CUI // {' / '.join(cat_marks)}"
        
        if dissemination:
            banner += f" // {' / '.join(dissemination)}"
        
        return banner

    def generate_footer(self, controlling_office: str, poc: str) -> str:
        """Generate CUI designation indicator (footer)."""
        return (
            f"Controlled by: {controlling_office}\n"
            f"CUI Category: See banner marking\n"
            f"POC: {poc}\n"
            f"Distribution/Dissemination Control: See banner marking"
        )
```

### 9.6 Cross-Regulation Mapping Matrix

```
┌───────────────────┬────────────┬───────────┬──────────┬──────────┬──────────────┬─────────────┐
│  Data Element     │  GDPR      │  HIPAA    │  PCI-DSS │  SOX     │  NIST CUI    │  Class.     │
├───────────────────┼────────────┼───────────┼──────────┼──────────┼──────────────┼─────────────┤
│  Name             │  Art.4 PD  │  PHI ID   │  CHD     │  —       │  PRVCY       │  CONFID.    │
│  SSN              │  Art.87    │  PHI ID   │  —       │  —       │  SP-PRVCY    │  RESTRICTED │
│  Credit Card PAN  │  Art.4 PD  │  —        │  CHD(*)  │  —       │  —           │  RESTRICTED │
│  Health Diagnosis │  Art.9 SC  │  PHI      │  —       │  —       │  SP-HLTH     │  RESTRICTED │
│  Email            │  Art.4 PD  │  PHI ID   │  —       │  —       │  PRVCY       │  CONFID.    │
│  IP Address       │  Art.4 PD  │  PHI ID   │  —       │  —       │  —           │  CONFID.    │
│  Revenue Figures  │  —         │  —        │  —       │  Material│  PROPIN      │  RESTRICTED │
│  Employee ID      │  Art.4 PD  │  —        │  —       │  ITGC    │  FEDCON      │  INTERNAL   │
│  Biometric        │  Art.9 SC  │  PHI ID   │  —       │  —       │  SP-PRVCY    │  RESTRICTED │
│  Genetic Data     │  Art.9 SC  │  PHI      │  —       │  —       │  SP-HLTH     │  RESTRICTED │
│  Trade Secret     │  —         │  —        │  —       │  —       │  PROPIN      │  RESTRICTED │
│  Public Filing    │  —         │  —        │  —       │  Public  │  —           │  PUBLIC     │
└───────────────────┴────────────┴───────────┴──────────┴──────────┴──────────────┴─────────────┘

Legend:
  PD = Personal Data          SC = Special Category       CHD = Cardholder Data
  (*) = Defines CDE scope     ITGC = IT General Control  CONFID. = CONFIDENTIAL
```

---

## 10. Lab Exercises

### Lab 1: Build Automated PII Scanner with Presidio

**Objective:** Create a database PII scanner that connects to PostgreSQL, scans column samples, and produces a classification report.

```python
#!/usr/bin/env python3
"""
Lab 1: Automated PII Scanner using Microsoft Presidio
Scans PostgreSQL database columns for sensitive data.

Requirements:
    pip install presidio-analyzer presidio-anonymizer psycopg2-binary spacy
    python -m spacy download en_core_web_lg
"""

import json
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Optional

import psycopg2
from psycopg2.extras import RealDictCursor
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern

# --- Configuration ---

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "target_database",
    "user": "scanner_readonly",
    # Password from env: PGPASSWORD
}

SAMPLE_SIZE = 100  # Rows to sample per column
CONFIDENCE_THRESHOLD = 0.7
EXCLUDED_SCHEMAS = {"pg_catalog", "information_schema", "pg_toast"}


@dataclass
class Finding:
    schema_name: str
    table_name: str
    column_name: str
    data_type: str
    entity_type: str
    confidence: float
    sample_count: int
    match_count: int
    match_percentage: float
    proposed_classification: str
    regulations: list


@dataclass
class ScanReport:
    scan_id: str
    database: str
    started_at: str
    completed_at: Optional[str]
    tables_scanned: int
    columns_scanned: int
    findings: list
    summary: dict


class PIIScanner:
    """Scan database for PII using Presidio NER + regex patterns."""

    def __init__(self, db_config: dict):
        self.db_config = db_config
        self.analyzer = self._build_analyzer()
        self.findings = []

    def _build_analyzer(self) -> AnalyzerEngine:
        """Configure Presidio analyzer with custom recognizers."""
        analyzer = AnalyzerEngine()

        # Custom: internal employee ID
        emp_pattern = Pattern(name="employee_id", regex=r"EMP-[A-Z]{2}\d{6}", score=0.9)
        emp_recognizer = PatternRecognizer(
            supported_entity="EMPLOYEE_ID", patterns=[emp_pattern]
        )
        analyzer.registry.add_recognizer(emp_recognizer)

        # Custom: medical record number
        mrn_pattern = Pattern(name="mrn", regex=r"MRN-\d{8,10}", score=0.95)
        mrn_recognizer = PatternRecognizer(
            supported_entity="MEDICAL_RECORD_NUMBER", patterns=[mrn_pattern]
        )
        analyzer.registry.add_recognizer(mrn_recognizer)

        return analyzer

    def scan_database(self) -> ScanReport:
        """Full database scan."""
        scan_start = datetime.now(timezone.utc).isoformat()
        scan_id = f"scan-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"

        conn = psycopg2.connect(**self.db_config)
        conn.set_session(readonly=True)

        try:
            tables = self._get_text_columns(conn)
            tables_scanned = 0
            columns_scanned = 0

            for schema, table, column, data_type in tables:
                if schema in EXCLUDED_SCHEMAS:
                    continue

                samples = self._sample_column(conn, schema, table, column)
                if not samples:
                    continue

                columns_scanned += 1
                self._analyze_samples(schema, table, column, data_type, samples)

            tables_scanned = len(set((s, t) for s, t, _, _ in tables))

        finally:
            conn.close()

        scan_end = datetime.now(timezone.utc).isoformat()

        report = ScanReport(
            scan_id=scan_id,
            database=self.db_config["dbname"],
            started_at=scan_start,
            completed_at=scan_end,
            tables_scanned=tables_scanned,
            columns_scanned=columns_scanned,
            findings=[asdict(f) for f in self.findings],
            summary=self._generate_summary()
        )

        return report

    def _get_text_columns(self, conn) -> list:
        """Get all text-like columns from the database."""
        query = """
        SELECT table_schema, table_name, column_name, data_type
        FROM information_schema.columns
        WHERE data_type IN ('character varying', 'text', 'character', 'varchar', 'json', 'jsonb')
          AND table_schema NOT IN ('pg_catalog', 'information_schema')
        ORDER BY table_schema, table_name, ordinal_position;
        """
        with conn.cursor() as cur:
            cur.execute(query)
            return cur.fetchall()

    def _sample_column(self, conn, schema: str, table: str, column: str) -> list:
        """Sample non-null values from a column."""
        query = f"""
        SELECT {self._quote_ident(column)}::text
        FROM {self._quote_ident(schema)}.{self._quote_ident(table)}
        WHERE {self._quote_ident(column)} IS NOT NULL
          AND {self._quote_ident(column)}::text != ''
        ORDER BY random()
        LIMIT %s;
        """
        try:
            with conn.cursor() as cur:
                cur.execute(query, (SAMPLE_SIZE,))
                return [row[0] for row in cur.fetchall()]
        except psycopg2.Error:
            return []

    def _analyze_samples(self, schema: str, table: str, column: str,
                         data_type: str, samples: list):
        """Run Presidio analysis on sampled values."""
        entity_counts = {}

        for value in samples:
            if not value or len(value) > 5000:
                continue

            results = self.analyzer.analyze(
                text=value,
                language="en",
                score_threshold=CONFIDENCE_THRESHOLD
            )

            for result in results:
                key = result.entity_type
                if key not in entity_counts:
                    entity_counts[key] = {"count": 0, "max_score": 0.0}
                entity_counts[key]["count"] += 1
                entity_counts[key]["max_score"] = max(
                    entity_counts[key]["max_score"], result.score
                )

        # Generate findings for significant detections
        for entity_type, stats in entity_counts.items():
            match_pct = stats["count"] / len(samples)
            if match_pct >= 0.1:  # At least 10% of samples match
                finding = Finding(
                    schema_name=schema,
                    table_name=table,
                    column_name=column,
                    data_type=data_type,
                    entity_type=entity_type,
                    confidence=stats["max_score"],
                    sample_count=len(samples),
                    match_count=stats["count"],
                    match_percentage=round(match_pct * 100, 1),
                    proposed_classification=self._entity_to_classification(entity_type),
                    regulations=self._entity_to_regulations(entity_type)
                )
                self.findings.append(finding)

    def _entity_to_classification(self, entity_type: str) -> str:
        """Map detected entity type to classification level."""
        restricted = {
            "US_SSN", "CREDIT_CARD", "US_BANK_NUMBER",
            "MEDICAL_RECORD_NUMBER", "US_PASSPORT", "UK_NHS",
            "CRYPTO", "IBAN_CODE"
        }
        confidential = {
            "PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER",
            "LOCATION", "DATE_TIME", "IP_ADDRESS",
            "US_DRIVER_LICENSE", "EMPLOYEE_ID"
        }

        if entity_type in restricted:
            return "RESTRICTED"
        elif entity_type in confidential:
            return "CONFIDENTIAL"
        else:
            return "INTERNAL"

    def _entity_to_regulations(self, entity_type: str) -> list:
        """Map entity type to applicable regulations."""
        mapping = {
            "US_SSN": ["HIPAA", "CCPA", "GDPR"],
            "CREDIT_CARD": ["PCI-DSS"],
            "PERSON": ["GDPR", "CCPA"],
            "EMAIL_ADDRESS": ["GDPR", "CCPA", "CAN-SPAM"],
            "PHONE_NUMBER": ["GDPR", "CCPA", "TCPA"],
            "MEDICAL_RECORD_NUMBER": ["HIPAA"],
            "IP_ADDRESS": ["GDPR"],
            "LOCATION": ["GDPR", "CCPA"],
            "US_PASSPORT": ["GDPR", "CCPA"],
        }
        return mapping.get(entity_type, [])

    def _generate_summary(self) -> dict:
        """Generate scan summary statistics."""
        if not self.findings:
            return {"total_findings": 0, "risk_level": "LOW"}

        classifications = [f.proposed_classification for f in self.findings]
        return {
            "total_findings": len(self.findings),
            "restricted_count": classifications.count("RESTRICTED"),
            "confidential_count": classifications.count("CONFIDENTIAL"),
            "internal_count": classifications.count("INTERNAL"),
            "risk_level": "CRITICAL" if "RESTRICTED" in classifications else
                         "HIGH" if "CONFIDENTIAL" in classifications else "MEDIUM",
            "unique_tables_affected": len(set(
                (f.schema_name, f.table_name) for f in self.findings
            )),
            "regulations_implicated": list(set(
                reg for f in self.findings for reg in f.regulations
            ))
        }

    @staticmethod
    def _quote_ident(identifier: str) -> str:
        """Safely quote SQL identifier."""
        return f'"{identifier}"'


if __name__ == "__main__":
    scanner = PIIScanner(DB_CONFIG)
    report = scanner.scan_database()
    print(json.dumps(asdict(report), indent=2))
```

**Expected output structure:**
```json
{
  "scan_id": "scan-20250507-143022",
  "database": "target_database",
  "started_at": "2025-05-07T14:30:22+00:00",
  "completed_at": "2025-05-07T14:32:15+00:00",
  "tables_scanned": 47,
  "columns_scanned": 312,
  "findings": [
    {
      "schema_name": "public",
      "table_name": "customers",
      "column_name": "email_address",
      "data_type": "character varying",
      "entity_type": "EMAIL_ADDRESS",
      "confidence": 0.95,
      "sample_count": 100,
      "match_count": 98,
      "match_percentage": 98.0,
      "proposed_classification": "CONFIDENTIAL",
      "regulations": ["GDPR", "CCPA", "CAN-SPAM"]
    }
  ],
  "summary": {
    "total_findings": 23,
    "restricted_count": 3,
    "confidential_count": 15,
    "internal_count": 5,
    "risk_level": "CRITICAL",
    "unique_tables_affected": 12,
    "regulations_implicated": ["GDPR", "CCPA", "HIPAA", "PCI-DSS"]
  }
}
```

---

### Lab 2: Column-Level Access Control in PostgreSQL Based on Classification Tags

**Objective:** Implement a complete column-level access control system where access is automatically enforced based on classification metadata.

```sql
-- Lab 2: Classification-Driven Column Access Control
-- PostgreSQL 14+ required

-- Step 1: Create governance infrastructure
CREATE SCHEMA IF NOT EXISTS governance;

CREATE TABLE governance.classifications (
    id SERIAL PRIMARY KEY,
    schema_name TEXT NOT NULL,
    table_name TEXT NOT NULL,
    column_name TEXT NOT NULL,
    level TEXT NOT NULL CHECK (level IN ('PUBLIC', 'INTERNAL', 'CONFIDENTIAL', 'RESTRICTED')),
    pii BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (schema_name, table_name, column_name)
);

-- Step 2: Create clearance levels for roles
CREATE TABLE governance.role_clearances (
    role_name TEXT PRIMARY KEY,
    max_level TEXT NOT NULL CHECK (max_level IN ('PUBLIC', 'INTERNAL', 'CONFIDENTIAL', 'RESTRICTED')),
    granted_by TEXT NOT NULL,
    granted_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    justification TEXT
);

-- Step 3: Insert sample classifications
INSERT INTO governance.classifications (schema_name, table_name, column_name, level, pii) VALUES
('public', 'employees', 'id', 'PUBLIC', FALSE),
('public', 'employees', 'first_name', 'CONFIDENTIAL', TRUE),
('public', 'employees', 'last_name', 'CONFIDENTIAL', TRUE),
('public', 'employees', 'email', 'CONFIDENTIAL', TRUE),
('public', 'employees', 'ssn', 'RESTRICTED', TRUE),
('public', 'employees', 'salary', 'RESTRICTED', FALSE),
('public', 'employees', 'department', 'INTERNAL', FALSE),
('public', 'employees', 'hire_date', 'INTERNAL', FALSE),
('public', 'employees', 'title', 'PUBLIC', FALSE);

-- Step 4: Insert role clearances
INSERT INTO governance.role_clearances (role_name, max_level, granted_by, justification) VALUES
('public_api', 'PUBLIC', 'ciso', 'Public API service account'),
('internal_app', 'INTERNAL', 'ciso', 'Internal application service'),
('hr_analyst', 'CONFIDENTIAL', 'hr_director', 'HR reporting needs'),
('payroll_admin', 'RESTRICTED', 'ciso', 'Payroll processing requires full access');

-- Step 5: Create dynamic view generator
CREATE OR REPLACE FUNCTION governance.generate_classified_view(
    p_schema TEXT,
    p_table TEXT,
    p_role TEXT
) RETURNS TEXT AS $$
DECLARE
    role_level TEXT;
    level_rank INT;
    col_list TEXT := '';
    rec RECORD;
    view_name TEXT;
    view_sql TEXT;
BEGIN
    -- Get role clearance
    SELECT max_level INTO role_level
    FROM governance.role_clearances
    WHERE role_name = p_role
      AND (expires_at IS NULL OR expires_at > NOW());

    IF role_level IS NULL THEN
        role_level := 'PUBLIC';  -- Default to minimum
    END IF;

    -- Map level to rank
    level_rank := CASE role_level
        WHEN 'PUBLIC' THEN 1
        WHEN 'INTERNAL' THEN 2
        WHEN 'CONFIDENTIAL' THEN 3
        WHEN 'RESTRICTED' THEN 4
    END;

    -- Build column list based on clearance
    FOR rec IN
        SELECT 
            c.column_name,
            COALESCE(cl.level, 'PUBLIC') AS classification,
            CASE COALESCE(cl.level, 'PUBLIC')
                WHEN 'PUBLIC' THEN 1
                WHEN 'INTERNAL' THEN 2
                WHEN 'CONFIDENTIAL' THEN 3
                WHEN 'RESTRICTED' THEN 4
            END AS col_rank
        FROM information_schema.columns c
        LEFT JOIN governance.classifications cl
            ON cl.schema_name = c.table_schema
            AND cl.table_name = c.table_name
            AND cl.column_name = c.column_name
        WHERE c.table_schema = p_schema
          AND c.table_name = p_table
        ORDER BY c.ordinal_position
    LOOP
        IF rec.col_rank <= level_rank THEN
            -- Include column as-is
            col_list := col_list || format('%I, ', rec.column_name);
        ELSE
            -- Mask or exclude based on policy
            col_list := col_list || format(
                '''[CLASSIFIED-%s]'' AS %I, ',
                rec.classification, rec.column_name
            );
        END IF;
    END LOOP;

    -- Trim trailing comma
    col_list := rtrim(col_list, ', ');

    -- Generate view
    view_name := format('%I.%I_%s_view', p_schema, p_table, p_role);
    view_sql := format(
        'CREATE OR REPLACE VIEW %s AS SELECT %s FROM %I.%I;',
        view_name, col_list, p_schema, p_table
    );

    EXECUTE view_sql;

    -- Grant access
    EXECUTE format('GRANT SELECT ON %s TO %I;', view_name, p_role);

    RETURN view_sql;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Step 6: Generate views for each role
SELECT governance.generate_classified_view('public', 'employees', 'public_api');
SELECT governance.generate_classified_view('public', 'employees', 'internal_app');
SELECT governance.generate_classified_view('public', 'employees', 'hr_analyst');
SELECT governance.generate_classified_view('public', 'employees', 'payroll_admin');

-- Step 7: Audit logging for classified data access
CREATE TABLE governance.access_audit (
    id BIGSERIAL PRIMARY KEY,
    accessed_at TIMESTAMPTZ DEFAULT NOW(),
    role_name TEXT NOT NULL,
    schema_name TEXT NOT NULL,
    table_name TEXT NOT NULL,
    columns_accessed TEXT[],
    highest_classification TEXT,
    query_hash TEXT,
    client_ip INET
);

CREATE OR REPLACE FUNCTION governance.log_classified_access()
RETURNS EVENT_TRIGGER AS $$
DECLARE
    obj RECORD;
BEGIN
    FOR obj IN SELECT * FROM pg_event_trigger_ddl_commands()
    LOOP
        -- Log DDL on classified objects
        INSERT INTO governance.access_audit (role_name, schema_name, table_name, columns_accessed, highest_classification)
        VALUES (current_user, obj.schema_name, obj.object_identity, '{}', 'DDL_EVENT');
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Step 8: Verification queries
-- As public_api role:
-- SELECT * FROM public.employees_public_api_view;
-- Expected: id, title visible; all PII columns show '[CLASSIFIED-...]'

-- As payroll_admin role:
-- SELECT * FROM public.employees_payroll_admin_view;
-- Expected: all columns visible (RESTRICTED clearance)
```

---

### Lab 3: DLP Policy for Database Exports

**Objective:** Build a DLP gateway that intercepts database export operations, inspects content, and enforces classification-based policies.

```python
#!/usr/bin/env python3
"""
Lab 3: DLP Policy Engine for Database Exports
Intercepts pg_dump / CSV exports and enforces classification rules.

This acts as a controlled export gateway — all database exports
must pass through this system.
"""

import csv
import hashlib
import io
import json
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional

from presidio_analyzer import AnalyzerEngine


class ExportAction(Enum):
    ALLOW = "allow"
    MASK = "mask"
    BLOCK = "block"
    ENCRYPT = "encrypt"


@dataclass
class DLPPolicy:
    name: str
    max_classification: str  # Highest classification allowed in export
    allowed_destinations: list = field(default_factory=list)
    require_encryption: bool = False
    require_approval: bool = False
    mask_above_level: Optional[str] = None
    max_rows: Optional[int] = None
    blocked_columns: list = field(default_factory=list)
    audit_all: bool = True


@dataclass  
class ExportRequest:
    requester: str
    source_database: str
    source_schema: str
    source_table: str
    destination: str
    format: str  # csv, json, sql
    columns: list
    where_clause: Optional[str] = None
    justification: Optional[str] = None
    approval_ticket: Optional[str] = None


@dataclass
class DLPDecision:
    action: ExportAction
    reason: str
    modifications: dict = field(default_factory=dict)
    warnings: list = field(default_factory=list)


class DatabaseExportDLP:
    """DLP gateway for controlled database exports."""

    LEVEL_RANK = {"PUBLIC": 1, "INTERNAL": 2, "CONFIDENTIAL": 3, "RESTRICTED": 4}

    def __init__(self, classification_store, policy_store):
        self.classifications = classification_store
        self.policies = policy_store
        self.analyzer = AnalyzerEngine()

    def evaluate_export(self, request: ExportRequest, policy: DLPPolicy) -> DLPDecision:
        """Evaluate an export request against DLP policy."""
        
        # Check 1: Are any requested columns above policy threshold?
        column_classifications = self._get_column_classifications(
            request.source_schema, request.source_table, request.columns
        )
        
        max_col_level = max(
            (self.LEVEL_RANK.get(c, 0) for c in column_classifications.values()),
            default=0
        )
        policy_max = self.LEVEL_RANK.get(policy.max_classification, 0)
        
        if max_col_level > policy_max and policy.mask_above_level is None:
            blocked_cols = [
                col for col, level in column_classifications.items()
                if self.LEVEL_RANK.get(level, 0) > policy_max
            ]
            return DLPDecision(
                action=ExportAction.BLOCK,
                reason=f"Export contains columns above policy threshold: {blocked_cols}",
                warnings=[f"Columns {blocked_cols} are classified above {policy.max_classification}"]
            )

        # Check 2: Explicit blocked columns
        blocked = set(request.columns) & set(policy.blocked_columns)
        if blocked:
            return DLPDecision(
                action=ExportAction.BLOCK,
                reason=f"Policy explicitly blocks columns: {blocked}"
            )

        # Check 3: Destination allowed?
        if policy.allowed_destinations and request.destination not in policy.allowed_destinations:
            return DLPDecision(
                action=ExportAction.BLOCK,
                reason=f"Destination '{request.destination}' not in allowed list"
            )

        # Check 4: Approval required?
        if policy.require_approval and not request.approval_ticket:
            return DLPDecision(
                action=ExportAction.BLOCK,
                reason="Export requires approval ticket. None provided."
            )

        # Check 5: Should we mask?
        if policy.mask_above_level:
            mask_threshold = self.LEVEL_RANK.get(policy.mask_above_level, 0)
            cols_to_mask = [
                col for col, level in column_classifications.items()
                if self.LEVEL_RANK.get(level, 0) > mask_threshold
            ]
            if cols_to_mask:
                return DLPDecision(
                    action=ExportAction.MASK,
                    reason=f"Masking columns above {policy.mask_above_level}",
                    modifications={"masked_columns": cols_to_mask}
                )

        # Check 6: Encryption required?
        if policy.require_encryption:
            return DLPDecision(
                action=ExportAction.ENCRYPT,
                reason="Policy requires encrypted export",
                modifications={"encryption": "AES-256-GCM"}
            )

        # All checks passed
        return DLPDecision(
            action=ExportAction.ALLOW,
            reason="Export meets all policy requirements"
        )

    def execute_export(self, request: ExportRequest, decision: DLPDecision) -> dict:
        """Execute the export with DLP controls applied."""
        
        if decision.action == ExportAction.BLOCK:
            self._log_blocked_export(request, decision)
            return {"status": "blocked", "reason": decision.reason}

        # Build query
        columns = request.columns
        if decision.action == ExportAction.MASK:
            columns = self._build_masked_column_list(
                request.columns, 
                decision.modifications.get("masked_columns", [])
            )

        query = f"SELECT {', '.join(columns)} FROM {request.source_schema}.{request.source_table}"
        if request.where_clause:
            query += f" WHERE {request.where_clause}"

        # Execute and export
        export_path = self._run_export(request, query)
        
        # Post-export content inspection (defense in depth)
        content_findings = self._inspect_exported_content(export_path)
        if content_findings.get("unexpected_pii"):
            self._log_alert(request, content_findings)
            if decision.action != ExportAction.MASK:
                return {"status": "blocked_post_inspection", "findings": content_findings}

        # Encrypt if required
        if decision.action == ExportAction.ENCRYPT:
            export_path = self._encrypt_export(export_path)

        # Compute integrity hash
        file_hash = self._compute_hash(export_path)
        
        # Audit log
        self._log_successful_export(request, decision, export_path, file_hash)

        return {
            "status": "completed",
            "path": str(export_path),
            "hash": file_hash,
            "rows_exported": self._count_rows(export_path),
            "decision": decision.action.value
        }

    def _build_masked_column_list(self, all_columns: list, mask_columns: list) -> list:
        """Replace sensitive columns with masking expressions."""
        result = []
        for col in all_columns:
            if col in mask_columns:
                # PostgreSQL masking expression
                result.append(
                    f"CASE WHEN length({col}::text) > 4 "
                    f"THEN left({col}::text, 2) || repeat('*', length({col}::text) - 4) || right({col}::text, 2) "
                    f"ELSE repeat('*', length({col}::text)) END AS {col}"
                )
            else:
                result.append(col)
        return result

    def _inspect_exported_content(self, export_path: Path) -> dict:
        """Defense-in-depth: scan exported file for unexpected PII."""
        findings = {"unexpected_pii": False, "details": []}
        
        with open(export_path, 'r') as f:
            sample = f.read(100000)  # Inspect first 100KB
        
        results = self.analyzer.analyze(text=sample, language="en", score_threshold=0.8)
        
        high_risk_entities = {"US_SSN", "CREDIT_CARD", "US_BANK_NUMBER"}
        for result in results:
            if result.entity_type in high_risk_entities:
                findings["unexpected_pii"] = True
                findings["details"].append({
                    "entity": result.entity_type,
                    "score": result.score,
                    "position": f"{result.start}-{result.end}"
                })
        
        return findings

    def _get_column_classifications(self, schema: str, table: str, columns: list) -> dict:
        """Fetch classification levels for requested columns."""
        return self.classifications.get_bulk(schema, table, columns)

    def _compute_hash(self, path: Path) -> str:
        """SHA-256 hash for integrity verification."""
        h = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                h.update(chunk)
        return h.hexdigest()

    def _log_blocked_export(self, request, decision):
        """Log blocked export attempt to SIEM."""
        print(json.dumps({
            "event": "dlp_export_blocked",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "requester": request.requester,
            "source": f"{request.source_schema}.{request.source_table}",
            "reason": decision.reason,
            "severity": "HIGH"
        }), file=sys.stderr)

    def _log_successful_export(self, request, decision, path, file_hash):
        """Log successful export with full audit trail."""
        print(json.dumps({
            "event": "dlp_export_completed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "requester": request.requester,
            "source": f"{request.source_schema}.{request.source_table}",
            "destination": request.destination,
            "action": decision.action.value,
            "file_hash": file_hash,
            "justification": request.justification,
            "approval": request.approval_ticket
        }))
```

---

### Lab 4: Design a Complete Data Classification Program

**Objective:** Design an end-to-end data classification program for a fictional mid-size company (500 employees, SaaS product, processing customer PII and payment data).

```yaml
# Lab 4: Data Classification Program Design
# Company: "MedTech SaaS Inc." — 500 employees, healthcare SaaS platform
# Regulations: HIPAA, SOC 2 Type II, GDPR (EU customers), PCI-DSS (payment processing)

program_charter:
  name: "MedTech Data Classification Program"
  version: "1.0"
  effective_date: "2025-06-01"
  owner: "Chief Information Security Officer"
  review_cycle: "Annual (minimum), or upon regulatory change"

governance_structure:
  data_governance_committee:
    chair: CISO
    members: [CTO, DPO, VP_Engineering, Legal_Counsel, Compliance_Officer]
    meeting_cadence: monthly
    responsibilities:
      - approve_classification_policies
      - resolve_classification_disputes
      - approve_exceptions
      - review_incident_reports

  data_stewards:
    per_department: true
    responsibilities:
      - classify_data_in_their_domain
      - review_classifications_quarterly
      - approve_access_requests_for_their_data
      - report_classification_violations
    training: "Annual data classification training + HIPAA awareness"

classification_scheme:
  levels:
    PUBLIC:
      label: "PUBLIC"
      color: green
      description: "Information intended for public disclosure"
      examples: [marketing_content, published_API_docs, press_releases]
      impact_if_breached: none
      
    INTERNAL:
      label: "INTERNAL"
      color: yellow
      description: "Internal business information not intended for public"
      examples: [internal_wikis, org_charts, non-sensitive_emails, meeting_notes]
      impact_if_breached: minor_business_disruption
      
    CONFIDENTIAL:
      label: "CONFIDENTIAL"
      color: orange
      description: "Sensitive business data and personal information"
      examples: [customer_PII, employee_records, financial_projections, source_code]
      impact_if_breached: significant_business_harm_or_regulatory_action
      
    RESTRICTED:
      label: "RESTRICTED"
      color: red
      description: "Highest sensitivity — regulatory, existential risk"
      examples: [PHI, payment_card_data, encryption_keys, M_and_A_plans, trade_secrets]
      impact_if_breached: severe_regulatory_penalties_or_existential_threat

implementation_phases:
  phase_1_foundation:  # Months 1-2
    deliverables:
      - approved_classification_policy_document
      - data_steward_appointments
      - classification_decision_tree
      - training_materials
    tools: none_yet
    focus: governance_and_awareness

  phase_2_discovery:  # Months 3-4
    deliverables:
      - data_inventory_of_all_systems
      - initial_classification_of_critical_systems
      - gap_analysis_vs_HIPAA_and_PCI
    tools:
      - deploy_AWS_Macie_for_S3
      - deploy_piicatcher_for_databases
      - manual_review_for_unstructured_data
    focus: know_what_you_have

  phase_3_labeling:  # Months 5-6
    deliverables:
      - database_column_classifications_in_catalog
      - S3_bucket_tagging_completed
      - schema_documentation_updated
      - data_lineage_mapped_for_RESTRICTED_data
    tools:
      - DataHub_catalog_deployment
      - automated_classification_in_CI
      - pg_column_comments_standardized
    focus: make_classification_machine_readable

  phase_4_enforcement:  # Months 7-9
    deliverables:
      - DLP_policies_active_on_email_and_endpoints
      - RBAC_aligned_to_classification_levels
      - encryption_verified_for_CONFIDENTIAL_plus
      - export_gateway_operational
      - secrets_scanning_in_all_repos
    tools:
      - endpoint_DLP_agent
      - email_DLP_gateway
      - database_access_control_views
      - gitleaks_in_CI
    focus: prevent_unauthorized_disclosure

  phase_5_monitoring:  # Months 10-12
    deliverables:
      - SIEM_correlation_rules_for_classification_violations
      - quarterly_access_review_process
      - incident_response_playbooks_by_classification
      - metrics_dashboard
      - first_annual_classification_review
    tools:
      - SIEM_integration
      - access_certification_platform
      - compliance_dashboard
    focus: detect_and_respond

metrics_and_kpis:
  leading_indicators:
    - percentage_of_data_assets_classified: target_95_percent
    - percentage_of_employees_trained: target_100_percent
    - mean_time_to_classify_new_asset: target_under_48h
    - DLP_policy_coverage: target_100_percent_of_egress_channels
    
  lagging_indicators:
    - classification_related_incidents_per_quarter: target_under_3
    - false_positive_rate_on_DLP: target_under_20_percent
    - audit_findings_related_to_classification: target_zero_critical
    - mean_time_to_remediate_misclassification: target_under_72h

  reporting:
    cadence: monthly_to_governance_committee
    quarterly_board_summary: true
    annual_external_audit: SOC2_and_HIPAA

budget_estimate:
  year_1:
    tools_and_licenses: 150000
    headcount_partial_fte: 1.5  # Split across security and compliance
    training: 25000
    consulting_gap_assessment: 50000
    total: 275000
    
  ongoing_annual:
    tools_and_licenses: 120000
    headcount: 1.0
    training_refresh: 10000
    total: 180000

risk_register:
  - risk: "Shadow IT stores classified data outside governed systems"
    likelihood: HIGH
    impact: HIGH
    mitigation: "CASB discovery + quarterly asset inventory + DLP on all egress"
    
  - risk: "Classification fatigue — users default to lowest level"
    likelihood: MEDIUM
    impact: HIGH
    mitigation: "Auto-classification where possible + spot-check audits + gamification"
    
  - risk: "M&A introduces unclassified data from acquired company"
    likelihood: MEDIUM
    impact: HIGH
    mitigation: "Due diligence checklist includes data classification maturity assessment"
    
  - risk: "Developer copies PHI to local machine for debugging"
    likelihood: HIGH
    impact: CRITICAL
    mitigation: "Synthetic data for dev/test + endpoint DLP + training + production access controls"
```

---

## Security Perspective: Pentester's View

For offensive security professionals, understanding data classification directly impacts engagement value:

**During reconnaissance:**
- Identifying an organization's classification scheme reveals what they consider crown jewels
- Public data classification policies (some organizations publish them) reveal defense priorities
- Job postings mentioning "data steward" or "information governance" signal maturity level

**During exploitation:**
- When you gain access, immediately assess what classification level the compromised data represents
- Finding RESTRICTED data (PHI, PCI, trade secrets) elevates finding severity from informational to critical
- Document the regulatory implications: "Attacker accessed 50,000 ePHI records, triggering HIPAA breach notification to HHS within 60 days and individual notification without delay"

**Impact assessment:**
- CVSS Environmental Score adjusts based on data classification of affected assets
- A SQL injection returning PUBLIC data scores differently than one returning RESTRICTED PCI data
- Aggregation attacks: combining multiple INTERNAL findings may yield CONFIDENTIAL impact

**Report writing:**
- Map findings to classification levels for business impact clarity
- Reference specific regulatory consequences: "This vulnerability exposes PCI CHD, expanding CDE scope to include the compromised web server and potentially failing PCI-DSS Requirement 6"
- Quantify exposure: number of records x classification level x applicable regulations

**DLP evasion (authorized testing):**
- Test DLP effectiveness: can you exfiltrate classified data through approved channels?
- Encoding/obfuscation: Base64, steganography, DNS tunneling — does DLP catch it?
- Slow exfiltration: does DLP detect low-and-slow extraction below volume thresholds?
- Channel switching: if email DLP blocks, does the clipboard or USB get caught?

Understanding classification transforms a technical finding into a business risk statement that executives and regulators act on.

---

## References

- NIST SP 800-60 Vol. 1 & 2 — Guide for Mapping Types of Information to Security Categories
- NIST FIPS 199 — Standards for Security Categorization
- NIST SP 800-88 Rev. 1 — Guidelines for Media Sanitization
- NIST SP 800-171 Rev. 2 — Protecting CUI in Nonfederal Systems
- 32 CFR Part 2002 — Controlled Unclassified Information
- PCI-DSS v4.0 — Requirements 3, 4, 7, 9
- HIPAA Privacy Rule (45 CFR Part 160, 164 Subpart E)
- HIPAA Security Rule (45 CFR Part 160, 164 Subpart C)
- GDPR Articles 4, 5, 9, 32, 35
- EU Council Decision 2013/488/EU — Security Rules for EU Classified Information
- ISO/IEC 27001:2022 Annex A — A.5.12 Classification of Information
- Microsoft Presidio Documentation — https://microsoft.github.io/presidio/
- Apache Ranger Documentation — https://ranger.apache.org/
- AWS Macie User Guide
- Google Cloud DLP API Reference
- Microsoft Purview Documentation
