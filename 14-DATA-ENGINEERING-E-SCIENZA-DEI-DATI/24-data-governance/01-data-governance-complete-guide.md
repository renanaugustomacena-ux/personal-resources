# Data Governance — Strategy, Implementation, and Tooling

## Table of Contents

1. [Data Governance Foundations](#1-data-governance-foundations)
2. [Data Catalog and Metadata](#2-data-catalog-and-metadata)
3. [Data Lineage](#3-data-lineage)
4. [Master Data Management (MDM)](#4-master-data-management-mdm)
5. [Data Mesh](#5-data-mesh)
6. [Access Control and Security Governance](#6-access-control-and-security-governance)
7. [Data Lifecycle Management](#7-data-lifecycle-management)
8. [Regulatory Compliance Governance](#8-regulatory-compliance-governance)
9. [Metrics and Measurement](#9-metrics-and-measurement)
10. [Lab Exercises](#10-lab-exercises)

---

## 1. Data Governance Foundations

### 1.1 Definition and Scope

The Data Management Association Body of Knowledge (DAMA-DMBOK) defines data governance as the exercise of authority, control, and shared decision-making over the management of data assets. It is not a technology initiative but an organizational capability that establishes accountability, policies, and standards for data across its entire lifecycle.

Data governance answers the questions: Who can make decisions about data? What decisions need to be made? How are those decisions implemented and enforced?

The scope of data governance encompasses:

- **Policy definition** — rules governing data creation, access, use, quality, and retention
- **Standards** — naming conventions, data models, metadata requirements, classification schemes
- **Processes** — workflows for data issue resolution, change management, access provisioning
- **Organizational structure** — roles, responsibilities, decision rights, escalation paths
- **Technology enablement** — tools that automate policy enforcement, catalog data, track lineage

### 1.2 Governance vs. Management Distinction

A critical distinction separates governance from management:

| Aspect | Data Governance | Data Management |
|--------|----------------|-----------------|
| Focus | Decision rights, policies, accountability | Execution, operations, implementation |
| Question | What should be done? Who decides? | How is it done? Who executes? |
| Scope | Cross-organizational, strategic | Domain-specific, tactical |
| Output | Policies, standards, procedures | Databases, pipelines, reports |
| Actors | Council, owners, stewards | Engineers, analysts, administrators |
| Timeframe | Long-term, evolutionary | Day-to-day operations |

Governance is the legislature; management is the executive branch. Governance sets the rules; management follows them. Without governance, management operates without direction. Without management, governance produces unimplemented policies.

### 1.3 Operating Models

#### Centralized Governance

A single, central team owns all governance decisions, policies, and enforcement. Works well for:

- Small-to-mid organizations with limited data domains
- Highly regulated industries requiring uniform compliance
- Early-stage governance programs establishing foundational controls

**Advantages:** Consistency, clear accountability, simplified compliance reporting.
**Disadvantages:** Bottleneck at scale, slow response to domain-specific needs, perceived as bureaucratic.

```
┌─────────────────────────────────────────────┐
│          Central Governance Office           │
│  (CDO / Data Governance Council)            │
├─────────────────────────────────────────────┤
│  Policy │ Standards │ Enforcement │ Metrics │
└────────────────────┬────────────────────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
   ┌─────────┐ ┌─────────┐ ┌─────────┐
   │ Domain A│ │ Domain B│ │ Domain C│
   │ (executes│ │(executes│ │(executes│
   │  policy) │ │ policy) │ │ policy) │
   └─────────┘ └─────────┘ └─────────┘
```

#### Federated Governance

Domain teams own governance within their boundaries, with lightweight coordination. Suited for:

- Large enterprises with diverse business units
- Organizations adopting data mesh
- Mature data organizations with strong domain expertise

**Advantages:** Domain autonomy, faster decisions, contextual policies.
**Disadvantages:** Inconsistency risk, duplication of effort, interoperability challenges.

```
┌───────────────────────────────────────────────────┐
│        Lightweight Coordination Layer              │
│   (Shared standards, interoperability contracts)   │
└──────────┬──────────────┬──────────────┬──────────┘
           │              │              │
     ┌─────▼─────┐  ┌────▼─────┐  ┌────▼─────┐
     │ Domain A  │  │ Domain B │  │ Domain C │
     │ Own Gov.  │  │ Own Gov. │  │ Own Gov. │
     │ Council   │  │ Council  │  │ Council  │
     │ Policies  │  │ Policies │  │ Policies │
     └───────────┘  └──────────┘  └──────────┘
```

#### Hybrid Governance (Recommended for Most)

Central team sets minimum standards and cross-cutting policies; domains have autonomy within those guardrails.

**Structure:**
- Central team: privacy, security, compliance, cross-domain interoperability
- Domain teams: domain-specific quality rules, naming, stewardship, access within policy
- Collaboration forum: regular sync between central and domain governance leads

### 1.4 Data Governance Council Structure

The governance council is the primary decision-making body. Typical composition:

| Role | Responsibility | Typical Person |
|------|---------------|----------------|
| Executive Sponsor | Budget, organizational authority, tie-breaking | CDO, CIO, or VP Data |
| Council Chair | Agenda, facilitation, progress tracking | Head of Data Governance |
| Domain Representatives | Domain-specific input, policy adoption | Business unit leaders |
| Data Architecture Rep | Technical feasibility, standards alignment | Chief Data Architect |
| Legal/Compliance Rep | Regulatory alignment | Privacy Officer, Legal Counsel |
| IT/Platform Rep | Implementation feasibility, tooling | Platform Engineering Lead |
| Security Rep | Security policy alignment | CISO representative |

**Meeting cadence:**
- Strategic council: monthly (policy decisions, escalations, program direction)
- Working groups: weekly or biweekly (specific initiatives — quality, catalog, access)
- Domain syncs: biweekly (domain-specific governance progress)

### 1.5 Roles and Responsibilities

#### Data Owner

- Senior business leader accountable for a data domain
- Approves access policies, quality thresholds, retention rules
- Makes decisions on data meaning, acceptable use, and classification
- Does NOT do day-to-day management — delegates to stewards

#### Data Steward

- Subject matter expert responsible for day-to-day governance execution
- Maintains metadata, resolves data quality issues, manages business glossary
- Serves as bridge between business context and technical implementation
- Reports to business (functionally) and governance office (for governance tasks)

#### Data Custodian

- Technical role responsible for storage, security, and infrastructure
- Implements access controls, backup/recovery, encryption
- Ensures technical compliance with governance policies
- Typically database administrators, platform engineers, or cloud architects

#### Data Consumer

- End user of data with responsibilities under governance
- Must use data per classification and access policies
- Reports quality issues through defined channels
- Completes required data literacy training

### 1.6 Decision Rights Framework (RACI for Data)

A decision rights framework clarifies who decides what:

| Decision | Data Owner | Steward | Custodian | Governance Office |
|----------|-----------|---------|-----------|-------------------|
| Data classification | Accountable | Responsible | Informed | Consulted |
| Access grant/revoke | Accountable | Responsible | Responsible | Consulted |
| Quality thresholds | Accountable | Responsible | Informed | Consulted |
| Retention period | Consulted | Responsible | Informed | Accountable |
| Schema changes | Consulted | Responsible | Responsible | Informed |
| New data source onboarding | Accountable | Responsible | Responsible | Consulted |
| Policy creation | Consulted | Consulted | Informed | Accountable |

### 1.7 Maturity Assessment

Governance maturity models help organizations assess their current state and plan improvements.

**Level 0 — Undisciplined:** No formal governance, tribal knowledge, ad hoc decisions, no metadata management.

**Level 1 — Reactive:** Governance triggered by incidents or compliance failures. Some documentation exists but is inconsistent.

**Level 2 — Proactive:** Formal governance program established, roles defined, policies documented. Enforcement is manual.

**Level 3 — Managed:** Policies enforced through tooling, metrics tracked, regular reporting to leadership. Catalog and lineage in place.

**Level 4 — Optimized:** Governance embedded in data platform, automated enforcement, continuous improvement through metrics, governance enables (not hinders) data use.

**Assessment dimensions:**
- Organization and roles (0-4)
- Policies and standards (0-4)
- Data quality management (0-4)
- Metadata management (0-4)
- Data security and privacy (0-4)
- Technology and automation (0-4)
- Culture and literacy (0-4)

---

## 2. Data Catalog and Metadata

### 2.1 Why Catalogs Matter

A data catalog is the discovery layer of data governance. Without it, data assets are invisible: users cannot find data, cannot understand its meaning, cannot assess its quality, and cannot determine if they are allowed to use it.

Catalogs transform governance from policy documents into actionable knowledge embedded in the data discovery workflow.

### 2.2 Catalog Platforms

#### Apache Atlas

Open-source catalog originally built for the Hadoop ecosystem. Now used more broadly.

**Architecture:**
```
┌─────────────────────────────────────────┐
│              Apache Atlas               │
├──────────┬──────────┬──────────────────┤
│ Type     │ Search   │ Lineage Engine   │
│ System   │ (Solr/   │ (entity → entity │
│ (entity  │  ES)     │  relationships)  │
│  models) │          │                  │
├──────────┴──────────┴──────────────────┤
│         Graph Store (JanusGraph)        │
├─────────────────────────────────────────┤
│           Kafka (Hooks/Events)          │
└─────────────────────────────────────────┘
```

**Key features:**
- Type-based metadata model with inheritance
- Classification propagation (tag a table, columns inherit)
- REST API and Kafka hooks for automated ingestion
- Lineage stored as process entities connecting inputs to outputs
- Integration with Hadoop ecosystem (Hive, HBase, Storm, Sqoop)

**Configuration example — defining a custom type:**
```json
{
  "enumDefs": [],
  "structDefs": [],
  "classificationDefs": [
    {
      "name": "PII",
      "description": "Personally Identifiable Information",
      "superTypes": ["Confidential"],
      "attributeDefs": [
        {
          "name": "retention_days",
          "typeName": "int",
          "isOptional": true,
          "cardinality": "SINGLE"
        }
      ]
    }
  ],
  "entityDefs": [
    {
      "name": "data_product",
      "superTypes": ["DataSet"],
      "attributeDefs": [
        {
          "name": "domain",
          "typeName": "string",
          "isOptional": false
        },
        {
          "name": "sla_freshness_hours",
          "typeName": "int",
          "isOptional": true
        },
        {
          "name": "owner_email",
          "typeName": "string",
          "isOptional": false
        }
      ]
    }
  ]
}
```

#### DataHub (LinkedIn/Acryl Data)

Modern, API-first metadata platform with strong lineage and governance features.

**Architecture:**
```
┌──────────────────────────────────────────────────────┐
│                    DataHub Frontend                    │
│         (React UI — search, browse, lineage)         │
├──────────────────────────────────────────────────────┤
│                   DataHub GMS                         │
│          (Generalized Metadata Service)              │
│     ┌────────────────────────────────────┐           │
│     │  Metadata Aspects (versioned)      │           │
│     │  Entity Registry                   │           │
│     │  Search Index (Elasticsearch)      │           │
│     │  Graph (Neo4j or Elasticsearch)    │           │
│     └────────────────────────────────────┘           │
├──────────────────────────────────────────────────────┤
│        Metadata Change Log (Kafka/MCPS)              │
├──────────────────────────────────────────────────────┤
│  Ingestion Framework (Python-based, pluggable)       │
│  Sources: dbt, Snowflake, BigQuery, Airflow, etc.   │
└──────────────────────────────────────────────────────┘
```

**Key differentiators:**
- Entity-aspect model: entities (datasets, dashboards, pipelines) with versioned aspects (schema, ownership, tags)
- GraphQL and REST APIs for programmatic access
- Ingestion framework with 50+ connectors
- Column-level lineage support
- Fine-grained access policies
- Glossary terms, domains, and data products as first-class concepts
- Active open-source community (Acryl Data provides managed offering)

**DataHub ingestion recipe (YAML):**
```yaml
source:
  type: postgres
  config:
    host_port: "postgres:5432"
    database: analytics
    username: "${POSTGRES_USER}"
    password: "${POSTGRES_PASSWORD}"
    include_tables: true
    include_views: true
    profiling:
      enabled: true
      profile_table_level_only: false
    stateful_ingestion:
      enabled: true

transformers:
  - type: "simple_add_dataset_ownership"
    config:
      owner_urns:
        - "urn:li:corpuser:data-team"
  - type: "pattern_add_dataset_tags"
    config:
      tag_pattern:
        rules:
          ".*pii.*": ["urn:li:tag:PII"]
          ".*finance.*": ["urn:li:tag:Finance"]

sink:
  type: datahub-rest
  config:
    server: "http://datahub-gms:8080"
    token: "${DATAHUB_TOKEN}"
```

#### Amundsen (LF AI & Data)

Originally from Lyft, focused on data discovery with a lightweight architecture.

**Components:**
- Frontend (Flask app) — search and profile UI
- Search service — Elasticsearch-backed
- Metadata service — Neo4j-backed graph
- Databuilder — ETL framework for metadata ingestion

Best suited for organizations wanting a simple, composable catalog without full governance features.

#### Collibra

Enterprise-grade commercial platform combining catalog, glossary, governance workflows, and policy automation.

**Strengths:** Business glossary, data quality integration, governance workflows with BPMN, regulatory compliance modules, executive reporting. Often chosen by large financial and healthcare organizations.

#### Alation

Commercial catalog emphasizing collaborative data intelligence — behavioral metadata (query patterns), machine learning-driven suggestions, and human curation.

**Strengths:** Query log analysis for popularity signals, Compose (SQL workbench integrated with catalog), stewardship workflows, trust flags.

### 2.3 Metadata Types

#### Technical Metadata

Machine-readable information about data structure and infrastructure:
- Schema (columns, types, constraints, partitions)
- Storage location, format, compression
- Database/warehouse/lake registration
- Data pipeline dependencies
- Freshness timestamps, row counts, file sizes

#### Business Metadata

Human-curated context about meaning and usage:
- Business glossary terms and definitions
- Data domain classification
- Ownership and stewardship assignments
- Use case descriptions
- Data quality expectations and SLAs
- Sensitivity classification (public, internal, confidential, restricted)

#### Operational Metadata

Runtime information about data behavior:
- Query patterns (who queried, how often, which columns)
- Pipeline execution history (last run, duration, success/failure)
- Data quality check results
- Access logs
- Cost attribution (storage cost, compute cost)
- Freshness and staleness signals

### 2.4 Automated Metadata Extraction

Manual metadata management does not scale. Extraction should be automated at multiple layers:

**Schema crawling:** Periodic introspection of databases, warehouses, lakes.
```python
# Example: automated schema extraction pattern
class SchemaExtractor:
    def extract(self, connection_config: ConnectionConfig) -> list[TableMetadata]:
        inspector = sqlalchemy.inspect(engine)
        tables = []
        for table_name in inspector.get_table_names(schema=schema):
            columns = inspector.get_columns(table_name, schema=schema)
            pk = inspector.get_pk_constraint(table_name, schema=schema)
            fks = inspector.get_foreign_keys(table_name, schema=schema)
            tables.append(TableMetadata(
                name=table_name,
                schema=schema,
                columns=[ColumnMetadata(**col) for col in columns],
                primary_key=pk,
                foreign_keys=fks,
                last_crawled=datetime.utcnow()
            ))
        return tables
```

**Query log analysis:** Parse SQL logs to infer column usage, popularity, and join patterns.

**Pipeline metadata:** Extract from orchestrator APIs (Airflow DAG metadata, dbt manifest.json).

**Profiling:** Automated statistical profiling (null rates, cardinality, distributions, patterns).

### 2.5 Search and Discovery

Effective catalogs combine multiple discovery mechanisms:

- **Full-text search** across table names, column names, descriptions, tags
- **Faceted browsing** by domain, owner, classification, platform
- **Popularity ranking** based on query frequency and user interactions
- **Recommendations** based on collaborative filtering (users who used X also used Y)
- **Lineage-based exploration** (upstream/downstream navigation)
- **Column-level search** (find all columns containing email data)

### 2.6 Tagging and Classification

Classification schemes provide consistent data categorization:

**Sensitivity classification:**
```
PUBLIC          → No restrictions on access or sharing
INTERNAL        → Accessible to all employees, not external
CONFIDENTIAL    → Need-to-know basis, requires approval
RESTRICTED      → Strictest controls, regulatory requirements
```

**Domain classification:**
```
CUSTOMER        → Customer-related data
FINANCIAL       → Revenue, billing, accounting
OPERATIONAL     → Internal operations, logistics
PRODUCT         → Product catalog, inventory
EMPLOYEE        → HR, payroll, performance
```

**Automated classification** uses regex patterns, ML classifiers, and named entity recognition to detect PII, PHI, PCI data automatically during ingestion.

### 2.7 Data Lineage Integration

The catalog must integrate lineage to answer: Where did this data come from? What transformations were applied? What downstream systems depend on it?

Lineage in the catalog enables:
- Impact analysis before schema changes
- Root cause analysis when data quality degrades
- Trust assessment (understanding the transformation chain)
- Regulatory compliance (proving data provenance for auditors)

---

## 3. Data Lineage

### 3.1 Column-Level Lineage

Table-level lineage ("Table A feeds Table B") is insufficient for serious governance. Column-level lineage tracks the flow of individual fields through transformations.

```
Source: orders.customer_email
  → Transform: LOWER(customer_email) AS email
    → Target: dim_customers.email
      → Dashboard: Customer Segmentation Report, column "Email"
```

Column-level lineage enables:
- Precise impact analysis (which reports break if I rename `customer_email`?)
- PII tracking (trace every place an email address flows)
- Data quality root cause (which transformation introduced nulls?)
- Regulatory compliance (prove that PII is handled correctly at every hop)

### 3.2 Lineage Capture Methods

#### SQL Parsing

Parse SQL statements to extract source-target column mappings.

**Approach:** Use SQL parsers (sqlglot, sqlparse, JSqlParser) to build ASTs, then resolve column references through CTEs, subqueries, and joins.

```python
import sqlglot
from sqlglot.lineage import lineage

# Extract column lineage from SQL
sql = """
INSERT INTO analytics.dim_customers
SELECT
    c.id AS customer_id,
    LOWER(c.email) AS email,
    o.total_amount AS lifetime_value
FROM raw.customers c
JOIN (
    SELECT customer_id, SUM(amount) AS total_amount
    FROM raw.orders
    GROUP BY customer_id
) o ON c.id = o.customer_id
"""

# sqlglot lineage analysis
node = lineage("email", sql, dialect="postgres")
# Returns: raw.customers.email → LOWER → analytics.dim_customers.email
```

**Limitations:** Cannot capture runtime-dynamic SQL, conditional logic, or UDFs without additional instrumentation.

#### OpenLineage API

OpenLineage is an open standard (Linux Foundation) for lineage metadata emission. Jobs emit events at start, completion, and failure.

**Event structure:**
```json
{
  "eventType": "COMPLETE",
  "eventTime": "2025-01-15T10:30:00.000Z",
  "run": {
    "runId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "facets": {
      "processingEngine": {
        "version": "3.5.0",
        "name": "Apache Spark"
      }
    }
  },
  "job": {
    "namespace": "production",
    "name": "etl.customer_dimensions",
    "facets": {
      "sql": {
        "query": "INSERT INTO dim_customers SELECT ..."
      }
    }
  },
  "inputs": [
    {
      "namespace": "postgres://prod-db:5432",
      "name": "raw.customers",
      "facets": {
        "schema": {
          "fields": [
            {"name": "id", "type": "INTEGER"},
            {"name": "email", "type": "VARCHAR"}
          ]
        },
        "columnLineage": {
          "fields": {
            "email": {
              "inputFields": [
                {
                  "namespace": "postgres://prod-db:5432",
                  "name": "raw.customers",
                  "field": "email",
                  "transformations": [
                    {"type": "DIRECT", "subtype": "TRANSFORMATION", "description": "LOWER()"}
                  ]
                }
              ]
            }
          }
        }
      }
    }
  ],
  "outputs": [
    {
      "namespace": "postgres://analytics-db:5432",
      "name": "analytics.dim_customers",
      "facets": {
        "schema": {
          "fields": [
            {"name": "customer_id", "type": "INTEGER"},
            {"name": "email", "type": "VARCHAR"},
            {"name": "lifetime_value", "type": "DECIMAL"}
          ]
        }
      }
    }
  ]
}
```

#### Runtime Instrumentation

Capture lineage by observing actual data flow at execution time:
- Spark listener plugins intercept query plans
- Airflow extractors capture operator inputs/outputs
- dbt artifacts (manifest.json, catalog.json) provide compile-time lineage
- Flink/Kafka topology introspection

### 3.3 Visualization

Lineage is most useful when visualized as directed acyclic graphs (DAGs):

```
┌──────────────┐     ┌─────────────────┐     ┌──────────────────┐
│ raw.customers│────▶│ etl.customer_dim │────▶│ dim_customers    │
│              │     │                  │     │                  │
│ • id         │     │ SQL Transform:   │     │ • customer_id    │
│ • email      │─┐   │ LOWER(email)     │  ┌──│ • email          │
│ • name       │ │   │ SUM(amount)      │  │  │ • lifetime_value │
└──────────────┘ │   └─────────────────┘  │  └──────────────────┘
                 │                          │           │
┌──────────────┐ │                          │           ▼
│ raw.orders   │─┘                          │  ┌────────────────────┐
│              │                            │  │ Customer Segment   │
│ • order_id   │                            │  │ Dashboard          │
│ • customer_id│                            │  │                    │
│ • amount     │────────────────────────────┘  │ • Email column     │
└──────────────┘                               │ • LTV column       │
                                               └────────────────────┘
```

### 3.4 Impact Analysis

Before making a change (schema modification, column rename, table deprecation), lineage answers:

1. **What downstream assets are affected?** Trace all paths from the changing entity.
2. **Who owns the affected assets?** Look up ownership metadata.
3. **What is the blast radius?** Count affected dashboards, reports, ML models.
4. **What is the SLA risk?** Identify time-critical downstream consumers.

**Impact analysis query pattern:**
```graphql
query ImpactAnalysis($datasetUrn: String!) {
  dataset(urn: $datasetUrn) {
    downstream(depth: 5) {
      entities {
        urn
        type
        ownership {
          owners { owner { username } }
        }
        properties { name }
      }
    }
  }
}
```

### 3.5 Root Cause Analysis

When data quality degrades downstream, lineage enables tracing backward:

1. Identify the affected column/metric
2. Trace upstream through lineage graph
3. At each hop, check data quality metrics
4. First hop where quality degrades is likely the root cause
5. Examine the transformation or source at that hop

### 3.6 Lineage Tools

#### OpenLineage + Marquez

OpenLineage defines the standard; Marquez (also Linux Foundation) provides a reference implementation for lineage storage and API.

**Marquez deployment:**
```yaml
# docker-compose.yml for Marquez
services:
  marquez-api:
    image: marquezproject/marquez:0.41.0
    ports:
      - "5000:5000"  # API
      - "5001:5001"  # Admin
    environment:
      MARQUEZ_CONFIG: /etc/marquez/marquez.yml
    depends_on:
      - marquez-db

  marquez-web:
    image: marquezproject/marquez-web:0.41.0
    ports:
      - "3000:3000"
    environment:
      MARQUEZ_HOST: marquez-api
      MARQUEZ_PORT: 5000

  marquez-db:
    image: postgres:15
    environment:
      POSTGRES_USER: marquez
      POSTGRES_PASSWORD: "${MARQUEZ_DB_PASSWORD}"
      POSTGRES_DB: marquez
    volumes:
      - marquez-data:/var/lib/postgresql/data
```

#### Spline (Apache Spark Lineage)

Captures lineage from Spark jobs automatically via a Spark agent.

```scala
// Enable Spline agent in Spark session
spark.conf.set("spark.sql.queryExecutionListeners", 
  "za.co.absa.spline.harvester.listener.SplineQueryExecutionListener")
spark.conf.set("spark.spline.producer.url", "http://spline-server:8080/producer")
```

#### Cloud-Native Lineage

- **Google Cloud Data Catalog + Dataplex:** Automatic lineage for BigQuery, Dataflow, Dataproc
- **AWS Glue Data Catalog:** Lineage for Glue ETL jobs
- **Azure Purview (Microsoft Purview):** Lineage across Azure Data Factory, Synapse, Databricks

---

## 4. Master Data Management (MDM)

### 4.1 Golden Record Concept

A golden record is the single, authoritative representation of a master data entity (customer, product, location) created by reconciling data from multiple source systems.

The golden record:
- Represents the most accurate, complete, and current view
- Is the system of record for cross-system identification
- Resolves conflicts between sources using survivorship rules
- Is continuously maintained as source data changes

### 4.2 Match/Merge Strategies

#### Matching

Identifying records across systems that represent the same real-world entity:

**Deterministic matching:** Exact match on a unique identifier (SSN, email, product SKU).

**Probabilistic matching:** Weighted scoring across multiple attributes:
```
Match Score Calculation:
  Name similarity (Jaro-Winkler):  0.92 × weight 0.3 = 0.276
  Address similarity:              0.85 × weight 0.25 = 0.213
  Phone exact match:               1.00 × weight 0.2  = 0.200
  DOB exact match:                 1.00 × weight 0.25 = 0.250
  ──────────────────────────────────────────────────────
  Total score:                                          0.939
  Threshold for auto-merge:                             0.90  ✓ MERGE
  Threshold for manual review:                          0.75
```

**ML-based matching:** Train models on labeled match/non-match pairs using feature vectors derived from attribute comparisons.

#### Merging (Survivorship Rules)

When multiple sources provide conflicting values, survivorship rules determine which value wins:

| Rule Type | Example |
|-----------|---------|
| Source priority | CRM email trumps billing system email |
| Recency | Most recently updated address wins |
| Frequency | Value appearing in most sources wins |
| Completeness | Non-null value wins over null |
| Confidence | Value from system with lowest error rate wins |
| Manual | Steward resolves conflicts above threshold |

```
Source A (CRM):     John Smith, john@email.com, 123 Main St
Source B (Billing): J. Smith,   john@email.com, 456 Oak Ave (updated 2025-01-10)
Source C (Support): John Smith, NULL,           123 Main St

Golden Record:      John Smith  (frequency rule: 2 of 3)
                    john@email.com (all agree)
                    456 Oak Ave (recency rule: Source B most recent)
```

### 4.3 Master Data Domains

#### Customer MDM

- Party data (individuals, organizations)
- Relationships (household, corporate hierarchy)
- Contact points (addresses, phones, emails)
- Identifiers (account numbers, loyalty IDs)
- Consent and preferences

#### Product MDM

- Product hierarchy (category → subcategory → SKU)
- Attributes (dimensions, weight, materials)
- Relationships (cross-sell, bundles, alternatives)
- Pricing (list price, cost, promotions)
- Lifecycle (active, discontinued, recalled)

#### Location MDM

- Physical addresses (geocoded, standardized)
- Hierarchy (country → region → city → site → floor)
- Operational attributes (capacity, hours, type)
- Relationships (belongs to business unit, serves region)

#### Reference Data

- Code sets (country codes, currency codes, industry codes)
- Lookups (status values, category types)
- Hierarchies (chart of accounts, organizational structure)
- External standards (ISO codes, NAICS, UNSPSC)

### 4.4 MDM Architecture Styles

#### Registry Style

Sources remain authoritative; MDM layer provides cross-reference and matching only.

```
┌─────────┐  ┌─────────┐  ┌─────────┐
│ Source A │  │ Source B │  │ Source C │
│ (auth.)  │  │ (auth.)  │  │ (auth.)  │
└────┬─────┘  └────┬─────┘  └────┬─────┘
     │              │              │
     ▼              ▼              ▼
┌──────────────────────────────────────┐
│        MDM Registry Hub              │
│  Cross-reference index only          │
│  A.id-123 = B.id-456 = C.id-789     │
│  No master attributes stored         │
└──────────────────────────────────────┘
```

**Best for:** Organizations where sources cannot be changed, and consumers need to query sources directly with a cross-reference key.

#### Consolidation Style

Data copied from sources into MDM hub for analysis; sources remain authoritative for transactions.

**Best for:** Analytics and reporting use cases where a unified view is needed but operational systems cannot be disrupted.

#### Centralized (Transaction Hub) Style

MDM hub is the single authoritative source; all creates/updates go through the hub, then publish to downstream systems.

```
                    ┌────────────────────┐
                    │  MDM Hub (Master)   │
                    │  Golden Records     │
    Create/Update ──▶  Match/Merge       │
                    │  Survivorship       │
                    └────────┬───────────┘
                             │ Publish
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
         ┌─────────┐  ┌─────────┐  ┌─────────┐
         │ System A │  │ System B │  │ System C │
         │(consumer)│  │(consumer)│  │(consumer)│
         └─────────┘  └─────────┘  └─────────┘
```

**Best for:** New deployments or organizations willing to route all master data operations through a central hub.

#### Coexistence Style

Both sources and hub are authoritative; bidirectional sync keeps them aligned.

**Best for:** Phased migration from distributed to centralized, or when multiple systems legitimately own different attributes.

### 4.5 Data Quality in MDM

MDM and data quality are inseparable. Quality rules applied in MDM:

- **Completeness:** Required fields must be populated
- **Validity:** Values must conform to allowed formats/ranges
- **Uniqueness:** No unintended duplicates (post-matching)
- **Consistency:** Related attributes must be logically coherent
- **Timeliness:** Records must be current within SLA

**Quality enforcement points:**
1. At ingestion (reject or quarantine invalid records)
2. During matching (quality of match keys affects match accuracy)
3. During survivorship (quality scores influence which value wins)
4. Post-merge (validate golden record passes all rules)
5. On publication (ensure consumers receive quality data)

### 4.6 MDM Tools

| Tool | Type | Strengths |
|------|------|-----------|
| Informatica MDM | Commercial | Full lifecycle, strong matching, enterprise scale |
| Reltio | Cloud-native | Graph-based relationships, real-time, API-first |
| Tamr | ML-powered | Automated matching using ML, minimal manual rules |
| IBM InfoSphere MDM | Commercial | Deep integration with IBM stack, governance |
| SAP Master Data Governance | Commercial | SAP ecosystem, process-oriented workflows |
| Ataccama ONE | Hybrid | Combined DQ + MDM, strong profiling |

---

## 5. Data Mesh

### 5.1 Domain-Oriented Ownership

Data mesh (Zhamak Dehghani, 2019) rejects the pattern of a central data team owning all pipelines and warehouses. Instead, the domain that generates data owns it end-to-end:

**Traditional (centralized):**
```
Domain Teams → Raw Data → Central Data Team → Warehouse → Consumers
```

**Data Mesh:**
```
Domain Team A → Owns and publishes Data Product A → Consumers
Domain Team B → Owns and publishes Data Product B → Consumers
Domain Team C → Owns and publishes Data Product C → Consumers
```

Domain ownership means the domain:
- Defines the semantic model for its data
- Builds and operates the pipelines that produce analytical data
- Guarantees quality SLAs
- Publishes discoverable, documented data products
- Responds to consumer feedback

### 5.2 Data as a Product

Domain teams treat their analytical data with the same rigor as user-facing products:

**Data product characteristics:**
- **Discoverable:** Registered in a catalog, searchable
- **Addressable:** Standard access mechanism (API, table, event stream)
- **Trustworthy:** Quality guarantees, SLAs, freshness commitments
- **Self-describing:** Schema, documentation, sample data, lineage
- **Interoperable:** Follows organization-wide standards for naming, formatting, identity
- **Secure:** Access policies, classification, audit logging
- **Valuable on its own:** Serves at least one meaningful use case

**Data product specification:**
```yaml
apiVersion: dataproduct/v1
kind: DataProduct
metadata:
  name: customer-360
  domain: customer-success
  owner: customer-platform-team
  tier: tier-1  # critical business data
spec:
  description: |
    Unified customer profile combining CRM, support,
    and product usage data. Updated hourly.
  
  output_ports:
    - name: customer_profiles
      type: table
      platform: snowflake
      schema_ref: ./schemas/customer_profiles.avsc
      freshness_sla: 1h
      quality_sla:
        completeness: 99.5%
        uniqueness: 100%
    
    - name: customer_events
      type: stream
      platform: kafka
      topic: customer-success.customer-events.v2
      schema_ref: ./schemas/customer_event.avsc
  
  input_ports:
    - source: crm-domain/accounts
    - source: support-domain/tickets
    - source: product-domain/usage-events
  
  sla:
    availability: 99.9%
    latency_p99: 5s
    support_channel: "#customer-data-support"
  
  classification: CONFIDENTIAL
  contains_pii: true
  retention: 7y
```

### 5.3 Self-Serve Data Platform

The platform team provides infrastructure that enables domain teams to build data products without needing deep infrastructure expertise:

**Platform capabilities:**
- Storage provisioning (data lake, warehouse accounts)
- Compute provisioning (Spark clusters, SQL engines)
- Pipeline orchestration (managed Airflow, declarative pipelines)
- Data product templates and scaffolding
- Schema registry and contract testing
- Quality monitoring and alerting
- Access control automation
- Catalog registration APIs
- Lineage capture (OpenLineage integration)
- Cost attribution and optimization

```
┌────────────────────────────────────────────────────────┐
│              Self-Serve Data Platform                   │
├────────────────────────────────────────────────────────┤
│  Data Product │ Quality    │ Access     │ Catalog      │
│  Templates    │ Framework  │ Automation │ Integration  │
├────────────────────────────────────────────────────────┤
│  Compute      │ Storage    │ Orchestr.  │ Observability│
│  (Spark, SQL) │ (Lake, WH) │ (Airflow)  │ (Metrics)   │
├────────────────────────────────────────────────────────┤
│           Infrastructure (K8s, Cloud Services)         │
└────────────────────────────────────────────────────────┘
```

### 5.4 Federated Computational Governance

Governance in a mesh is not centralized command-and-control but federated with computational enforcement:

**Principles:**
- Governance decisions made by a federation of domain representatives + central governance team
- Policies encoded as code and enforced automatically by the platform
- Global interoperability standards are mandatory; domain-specific policies are autonomous
- Compliance is continuous and automated, not periodic and manual

**Computational governance examples:**
```python
# Policy-as-code: Every data product must have PII classification
@governance_policy(scope="all_data_products")
def pii_classification_required(data_product: DataProduct) -> PolicyResult:
    if data_product.classification is None:
        return PolicyResult.FAIL(
            "Data products must declare PII classification"
        )
    if data_product.contains_pii and data_product.classification.level < "CONFIDENTIAL":
        return PolicyResult.FAIL(
            "Products containing PII must be CONFIDENTIAL or higher"
        )
    return PolicyResult.PASS()

# Policy-as-code: Schema must use standard naming
@governance_policy(scope="all_output_ports")
def standard_naming(port: OutputPort) -> PolicyResult:
    violations = []
    for field in port.schema.fields:
        if not re.match(r'^[a-z][a-z0-9_]*$', field.name):
            violations.append(f"Field '{field.name}' must be snake_case")
    if violations:
        return PolicyResult.FAIL("\n".join(violations))
    return PolicyResult.PASS()
```

### 5.5 Implementing Data Mesh

#### Organizational Change

Data mesh is fundamentally an organizational transformation:

1. **Identify domains** — bounded contexts from domain-driven design
2. **Assign ownership** — each domain gets data engineering capacity
3. **Define contracts** — inter-domain data sharing agreements
4. **Build platform** — self-serve infrastructure enabling domain autonomy
5. **Establish governance federation** — cross-domain standards body
6. **Migrate incrementally** — start with 2-3 domains, prove value, expand

#### Platform Engineering

The platform team's role shifts from building pipelines to building the platform that enables others:

**Platform team does:**
- Infrastructure provisioning
- Tooling development
- Template creation
- Platform observability
- Cross-cutting concerns (security, lineage)

**Platform team does NOT:**
- Write domain-specific transformations
- Own domain data quality
- Make semantic modeling decisions for domains
- Manage domain access policies

### 5.6 Mesh Governance Policies

**Global policies (enforced by platform):**
- All data products registered in catalog
- Standard schema format (Avro/Protobuf with schema registry)
- Naming conventions for identifiers, timestamps, domains
- Minimum documentation requirements
- PII classification mandatory
- Lineage emission mandatory
- Quality checks must pass before publication

**Domain policies (set by domain, enforced by platform):**
- Domain-specific quality thresholds
- Access approval workflows
- Freshness SLAs
- Retention periods (within global minimums)

---

## 6. Access Control and Security Governance

### 6.1 Role-Based Access Control (RBAC)

RBAC assigns permissions to roles, and roles to users. The simplest and most widely implemented model.

```
Users ──▶ Roles ──▶ Permissions ──▶ Data Assets

Example:
  analyst_finance ──▶ {SELECT on finance.*, SELECT on shared.*}
  engineer_customer ──▶ {SELECT, INSERT, UPDATE on customer.*}
  admin_platform ──▶ {ALL on *.*}
```

**RBAC hierarchy:**
```yaml
roles:
  data_reader:
    permissions: [SELECT]
    scope: assigned_databases
  
  data_analyst:
    inherits: data_reader
    permissions: [CREATE_VIEW, CREATE_TEMP_TABLE]
    scope: assigned_databases
  
  data_engineer:
    inherits: data_analyst
    permissions: [CREATE_TABLE, INSERT, UPDATE, DELETE, CREATE_PIPELINE]
    scope: assigned_databases
  
  domain_admin:
    inherits: data_engineer
    permissions: [GRANT, ALTER, DROP, MANAGE_ACCESS]
    scope: owned_databases
  
  platform_admin:
    permissions: [ALL]
    scope: all_databases
```

**Limitations:** Role explosion in large organizations, coarse-grained (all-or-nothing per role), cannot express contextual conditions.

### 6.2 Attribute-Based Access Control (ABAC)

ABAC evaluates policies based on attributes of the user, resource, action, and environment:

```
Policy: ALLOW access
  IF user.department = resource.domain
  AND user.clearance_level >= resource.sensitivity_level
  AND environment.time BETWEEN "08:00" AND "18:00"
  AND action IN [SELECT]
```

**Attributes:**
- **Subject:** department, role, clearance, location, training_completed
- **Resource:** sensitivity, domain, contains_pii, data_classification
- **Action:** read, write, delete, export, share
- **Environment:** time, network, device_type, mfa_status

ABAC enables fine-grained, context-aware access without role explosion.

### 6.3 Policy-Based Access Control (PBAC)

PBAC centralizes access decisions in a policy engine that evaluates rules in real-time:

```
# Open Policy Agent (OPA) — Rego policy example
package data.access

default allow = false

allow {
    input.action == "read"
    input.resource.classification == "INTERNAL"
    input.user.is_employee == true
}

allow {
    input.action == "read"
    input.resource.classification == "CONFIDENTIAL"
    input.user.department == input.resource.domain
    input.user.completed_training["data_handling"] == true
}

# Column-level masking policy
mask_columns[col] {
    col := input.resource.columns[_]
    col.classification == "PII"
    not input.user.has_role("pii_authorized")
}
```

### 6.4 Apache Ranger Policies

Apache Ranger provides centralized security for Hadoop/cloud ecosystems:

**Policy structure:**
```json
{
  "policyType": 0,
  "name": "finance-analyst-access",
  "resources": {
    "database": {"values": ["finance_warehouse"]},
    "table": {"values": ["*"]},
    "column": {"values": ["*"], "excludes": ["ssn", "credit_card_number"]}
  },
  "policyItems": [
    {
      "accesses": [
        {"type": "select", "isAllowed": true}
      ],
      "users": [],
      "groups": ["finance_analysts"],
      "conditions": [
        {
          "type": "ip-range",
          "values": ["10.0.0.0/8"]
        }
      ]
    }
  ],
  "denyPolicyItems": [
    {
      "accesses": [{"type": "select", "isAllowed": true}],
      "users": [],
      "groups": ["finance_analysts"],
      "resources": {
        "column": {"values": ["ssn", "credit_card_number"]}
      }
    }
  ]
}
```

### 6.5 Column-Level and Row-Level Security

#### Column-Level Security

Restrict access to specific columns based on user attributes:

```sql
-- Snowflake column masking policy
CREATE OR REPLACE MASKING POLICY pii_mask AS (val STRING)
RETURNS STRING ->
  CASE
    WHEN CURRENT_ROLE() IN ('PII_AUTHORIZED', 'SYSADMIN') THEN val
    ELSE SHA2(val, 256)
  END;

ALTER TABLE customers MODIFY COLUMN email
  SET MASKING POLICY pii_mask;
ALTER TABLE customers MODIFY COLUMN phone
  SET MASKING POLICY pii_mask;
```

#### Row-Level Security

Restrict which rows a user can see:

```sql
-- PostgreSQL row-level security
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

CREATE POLICY orders_region_policy ON orders
  FOR SELECT
  USING (region = current_setting('app.user_region'));

-- BigQuery row-level access policy
CREATE ROW ACCESS POLICY region_filter
ON `project.dataset.orders`
GRANT TO ('group:emea-analysts@company.com')
FILTER USING (region = 'EMEA');
```

### 6.6 Dynamic Data Masking

Masking rules applied at query time without modifying stored data:

| Masking Type | Input | Output |
|--------------|-------|--------|
| Full mask | john@email.com | ******* |
| Partial mask | john@email.com | j***@e*****.com |
| Hash | john@email.com | a3f2b8c... |
| Tokenization | 4532-1234-5678-9012 | tok_x7f2k9 |
| Redaction | 555-123-4567 | [REDACTED] |
| Generalization | Age: 34 | Age: 30-40 |
| Noise addition | Salary: 95000 | Salary: 93847 |

**Implementation pattern:**
```yaml
masking_rules:
  - column_pattern: "*.email"
    classification: PII
    rules:
      - role: pii_authorized
        action: SHOW_PLAINTEXT
      - role: analyst
        action: PARTIAL_MASK
        config: {show_first: 1, show_last: 0, mask_domain: true}
      - default:
        action: HASH
        config: {algorithm: sha256}
  
  - column_pattern: "*.credit_card*"
    classification: PCI
    rules:
      - role: payment_admin
        action: SHOW_PLAINTEXT
      - default:
        action: PARTIAL_MASK
        config: {show_last: 4, mask_char: "*"}
```

### 6.7 Purpose-Based Access Control

Access granted based on the declared purpose of data use, aligning with privacy regulations:

```yaml
purposes:
  - name: fraud_detection
    legal_basis: legitimate_interest
    allowed_data: [transaction_history, device_fingerprint, ip_address]
    retention: 90d
    
  - name: marketing_personalization
    legal_basis: consent
    allowed_data: [browsing_history, purchase_history, preferences]
    retention: 365d
    requires_consent: true
    
  - name: regulatory_reporting
    legal_basis: legal_obligation
    allowed_data: [all_financial_records]
    retention: 7y

access_request:
  user: analytics_team
  purpose: marketing_personalization
  decision: |
    ALLOW if user has valid purpose registration
    AND data subject has active consent for this purpose
    AND request accesses only allowed_data for this purpose
```

---

## 7. Data Lifecycle Management

### 7.1 Lifecycle Stages

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│ Creation/│──▶│  Active   │──▶│ Archival │──▶│Retention │──▶│ Disposal │
│Acquisition│   │   Use     │   │          │   │  Hold    │   │          │
└──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
                                                    │
                                              ┌─────▼─────┐
                                              │Legal Hold │
                                              │(suspends  │
                                              │ disposal) │
                                              └───────────┘
```

### 7.2 Data Creation and Acquisition

Governance at creation:
- Schema registration before data lands
- Classification at point of entry (not retroactively)
- Consent capture for personal data
- Lineage initiated (first node in the lineage graph)
- Quality rules activated (validate on ingest)
- Ownership assigned immediately

### 7.3 Active Use

During active use, governance ensures:
- Access controls enforced per policy
- Quality monitored continuously
- Usage tracked (who, when, what, why)
- Changes audited (schema evolution, backfills)
- Freshness SLAs maintained

### 7.4 Archival

When data is no longer actively queried but must be retained:

**Archival triggers:**
- Data age exceeds active retention threshold
- Query frequency drops below threshold (e.g., < 1 query/month)
- Business process completes (project ends, campaign concludes)

**Archival actions:**
- Move to cold/archive storage tier
- Compress and optimize for storage cost
- Maintain catalog entry (marked as archived)
- Preserve access controls and classification
- Document retrieval procedure and SLA

### 7.5 Retention Policies

Define how long data must be kept:

```yaml
retention_policies:
  financial_transactions:
    active: 2y
    archive: 5y
    total: 7y
    legal_basis: "SOX compliance, tax regulations"
    
  customer_pii:
    active: "duration of relationship + 30d"
    archive: 0  # delete after active period
    legal_basis: "GDPR data minimization"
    exception: "legal hold overrides"
    
  application_logs:
    active: 90d
    archive: 275d
    total: 365d
    legal_basis: "security incident investigation"
    
  ml_training_data:
    active: "model lifecycle"
    archive: 2y  # reproducibility
    legal_basis: "model auditability"
    
  anonymized_analytics:
    active: indefinite  # truly anonymized data
    legal_basis: "no personal data; analytics value"
```

### 7.6 Disposal and Deletion

Secure deletion when retention expires:

**Deletion verification:**
- Confirm no active legal holds
- Confirm retention period fully elapsed
- Verify no downstream dependencies (lineage check)
- Execute deletion across all copies (primary, backups, replicas, caches)
- Generate deletion certificate (what, when, who authorized, method)
- Update catalog (mark as deleted, retain deletion metadata)

**Deletion methods by sensitivity:**
- Standard data: logical deletion (mark deleted, overwrite in next compaction)
- Confidential: cryptographic erasure (destroy encryption keys)
- Restricted/regulated: certified destruction with audit trail

### 7.7 Legal Hold

Legal hold suspends normal disposition when litigation or investigation requires data preservation:

```yaml
legal_hold:
  id: LH-2025-0142
  created: 2025-03-15
  created_by: legal_department
  scope:
    - dataset: customer_communications
      date_range: "2023-01-01 to 2024-12-31"
    - dataset: financial_transactions
      filter: "customer_id IN (SELECT id FROM hold_subjects)"
  status: ACTIVE
  review_date: 2025-06-15
  notes: "Preserve per litigation counsel instruction. Do not modify or delete."
```

### 7.8 Storage Tier Management

```
┌─────────────────────────────────────────────────────────────────┐
│ Tier    │ Storage         │ Access   │ Cost      │ Use Case     │
├─────────┼─────────────────┼──────────┼───────────┼──────────────┤
│ HOT     │ SSD/NVMe, in-   │ < 10ms   │ $$$$$     │ Active OLTP, │
│         │ memory cache     │          │           │ real-time    │
├─────────┼─────────────────┼──────────┼───────────┼──────────────┤
│ WARM    │ Standard SSD,   │ < 100ms  │ $$$       │ Recent       │
│         │ columnar WH     │          │           │ analytics    │
├─────────┼─────────────────┼──────────┼───────────┼──────────────┤
│ COLD    │ Object storage  │ seconds  │ $         │ Historical,  │
│         │ (S3, GCS, ADLS) │          │           │ compliance   │
├─────────┼─────────────────┼──────────┼───────────┼──────────────┤
│ ARCHIVE │ Glacier, Archive│ hours    │ ¢         │ Legal hold,  │
│         │ storage class   │          │           │ deep archive │
└─────────┴─────────────────┴──────────┴───────────┴──────────────┘
```

**Automated tier management policy:**
```yaml
lifecycle_rules:
  - name: analytics_tiering
    scope: "analytics/**"
    rules:
      - condition: age > 90d AND access_count_30d < 5
        action: move_to_cold
      - condition: age > 365d AND access_count_90d == 0
        action: move_to_archive
      - condition: age > retention_period AND no_legal_hold
        action: delete_certified
  
  - name: logs_tiering
    scope: "logs/**"
    rules:
      - condition: age > 30d
        action: compress_and_move_cold
      - condition: age > 365d
        action: delete_certified
```

---

## 8. Regulatory Compliance Governance

### 8.1 Privacy by Design

Privacy by design (Ann Cavoukian, later codified in GDPR Article 25) requires privacy protections built into systems from the start, not bolted on after:

**Seven principles applied to data governance:**

1. **Proactive not reactive** — privacy impact assessments before new data collection
2. **Privacy as default** — collect minimum data, restrict access by default
3. **Privacy embedded** — technical controls baked into pipelines
4. **Full functionality** — privacy and utility are not zero-sum
5. **End-to-end lifecycle** — privacy from collection through deletion
6. **Transparency** — clear documentation of processing purposes
7. **User-centric** — data subject rights operationalized

### 8.2 Data Processing Agreements

When data flows between controllers and processors (GDPR) or between business entities:

**DPA governance checklist:**
- Processing purposes explicitly defined
- Sub-processor inventory maintained
- Data transfer mechanisms documented (SCCs, adequacy decisions)
- Security measures specified
- Breach notification timelines agreed
- Data subject request handling responsibilities clear
- Audit rights established
- Data return/deletion on termination specified

### 8.3 Lawful Basis Tracking

For GDPR (and similar regulations), every processing activity requires a lawful basis:

```yaml
processing_register:
  - activity: customer_onboarding
    purpose: account_creation
    lawful_basis: contract
    data_categories: [name, email, address, phone]
    retention: duration_of_contract + 30d
    recipients: [crm_system, email_platform]
    
  - activity: marketing_emails
    purpose: direct_marketing
    lawful_basis: consent
    data_categories: [email, preferences, browsing_history]
    retention: until_consent_withdrawn
    consent_mechanism: double_opt_in
    withdrawal_mechanism: unsubscribe_link
    
  - activity: fraud_scoring
    purpose: fraud_prevention
    lawful_basis: legitimate_interest
    data_categories: [transaction_patterns, device_data, ip_address]
    retention: 90d
    lia_completed: true  # Legitimate Interest Assessment
    lia_date: 2025-01-10
```

### 8.4 Consent Management

Governance over consent:
- Consent must be freely given, specific, informed, unambiguous
- Granular per purpose (not blanket consent)
- Withdrawal as easy as granting
- Consent records immutable and timestamped
- Processing stops when consent withdrawn (propagated to all systems)

**Consent propagation architecture:**
```
┌─────────────┐    ┌───────────────────┐    ┌─────────────────┐
│ User grants │───▶│ Consent Management│───▶│ Event Bus       │
│ / withdraws │    │ Platform (CMP)    │    │ (Kafka topic:   │
│ consent     │    │                   │    │  consent.events) │
└─────────────┘    └───────────────────┘    └────────┬────────┘
                                                      │
                          ┌───────────────────────────┼──────────────┐
                          ▼                           ▼              ▼
                   ┌──────────────┐          ┌──────────────┐ ┌───────────┐
                   │ Marketing    │          │ Analytics    │ │ ML        │
                   │ (stops email │          │ (excludes    │ │ (removes  │
                   │  if revoked) │          │  from agg.)  │ │  from     │
                   └──────────────┘          └──────────────┘ │  training)│
                                                              └───────────┘
```

### 8.5 Data Subject Requests (DSR) Automation

GDPR Articles 15-22 grant rights (access, rectification, erasure, portability, restriction, objection). Governance must operationalize these:

**DSR workflow automation:**
```yaml
dsr_workflow:
  intake:
    channels: [web_form, email, in_app]
    identity_verification: multi_factor
    sla: acknowledge_within_24h
    
  routing:
    - type: access_request
      handler: data_export_pipeline
      sla: 30_days
      
    - type: erasure_request
      handler: deletion_pipeline
      sla: 30_days
      pre_checks:
        - legal_hold_check
        - legitimate_interest_override_check
        - contractual_necessity_check
      
    - type: portability_request
      handler: export_in_machine_readable_format
      format: JSON
      sla: 30_days
  
  execution:
    discovery:
      - scan catalog for all datasets containing subject_id
      - lineage trace to find all derived/copied instances
    action:
      - execute per request type across all discovered locations
      - verify completion across all systems
    certification:
      - generate completion report
      - notify data subject
      - retain DSR log (not the deleted data)
```

### 8.6 Cross-Border Transfer Governance

When data moves across jurisdictions:

**Transfer mechanisms:**
- Adequacy decisions (EU → adequate countries)
- Standard Contractual Clauses (SCCs) — new 2021 modular clauses
- Binding Corporate Rules (intra-group transfers)
- Derogations (explicit consent, contract necessity)

**Governance requirements:**
- Transfer impact assessments (TIAs) for non-adequate destinations
- Technical supplementary measures (encryption in transit and at rest, pseudonymization)
- Sub-processor location tracking
- Data localization compliance (Russia, China, India sector-specific)

### 8.7 Regulatory Change Management

The regulatory landscape changes continuously. Governance must adapt:

**Process:**
1. Monitor regulatory developments (GDPR updates, new state privacy laws, AI Act)
2. Assess impact on current data processing activities
3. Update processing register and policies
4. Implement technical changes (new consent requirements, new rights)
5. Communicate changes to affected teams
6. Verify compliance through audits

**Key regulations to track:**
- GDPR (EU) and UK GDPR
- CCPA/CPRA (California)
- State privacy laws (Virginia, Colorado, Connecticut, Utah, Texas, etc.)
- LGPD (Brazil)
- PIPL (China)
- DPDPA (India)
- AI Act (EU) — governance of training data
- Sector-specific: HIPAA (health), GLBA (finance), PCI-DSS (payments)

---

## 9. Metrics and Measurement

### 9.1 Governance KPIs

#### Data Quality Score

Composite score across quality dimensions:

```
Quality Score = (
  Completeness_weight × Completeness_score +
  Validity_weight × Validity_score +
  Uniqueness_weight × Uniqueness_score +
  Timeliness_weight × Timeliness_score +
  Consistency_weight × Consistency_score
)

Example:
  Completeness (0.25): 98.5% of required fields populated
  Validity (0.25): 99.2% of values within valid ranges
  Uniqueness (0.20): 99.9% no unintended duplicates
  Timeliness (0.15): 95.0% within freshness SLA
  Consistency (0.15): 97.3% cross-system consistency
  ─────────────────────────────────────────────────
  Weighted Score: 98.5×.25 + 99.2×.25 + 99.9×.20 + 95.0×.15 + 97.3×.15
               = 24.63 + 24.80 + 19.98 + 14.25 + 14.60
               = 98.26%
```

#### Catalog Coverage

```
Catalog Coverage = (Assets documented in catalog / Total known data assets) × 100

Target: >95% for production assets

Sub-metrics:
  - Tables cataloged: 97%
  - Columns with descriptions: 82%
  - Business glossary terms linked: 75%
  - Ownership assigned: 91%
  - Classification applied: 88%
```

#### Lineage Completeness

```
Lineage Completeness = (Assets with captured lineage / Total data assets) × 100

Sub-metrics:
  - Table-level lineage coverage: 93%
  - Column-level lineage coverage: 71%
  - Pipeline lineage (Airflow, dbt): 98%
  - Ad-hoc query lineage: 45%
```

#### Policy Compliance Rate

```
Compliance Rate = (Compliant assets / Total assessed assets) × 100

Policy dimensions:
  - Access policy compliance: 96%
  - Retention policy compliance: 89%
  - Classification policy compliance: 92%
  - Naming standard compliance: 85%
  - Documentation standard compliance: 78%
```

#### Issue Resolution Time

```
Mean Time to Resolve (MTTR):
  - Critical data quality issues: < 4 hours
  - High severity issues: < 24 hours
  - Medium issues: < 5 business days
  - Low issues: < 15 business days

Tracking:
  - Issues opened this period: 47
  - Issues resolved this period: 52
  - Issues within SLA: 44 (93.6%)
  - Average resolution time: 2.3 days
```

### 9.2 Executive Dashboards

**Dashboard structure:**
```
┌─────────────────────────────────────────────────────────────┐
│              DATA GOVERNANCE EXECUTIVE DASHBOARD             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Overall Governance Score: 87/100  [████████░░] ↑3 vs Q3   │
│                                                             │
├────────────────────────┬────────────────────────────────────┤
│  DATA QUALITY          │  CATALOG & METADATA                │
│                        │                                    │
│  Quality Score: 98.3%  │  Assets Cataloged: 97%            │
│  Critical Issues: 2    │  Descriptions: 82%                │
│  Trend: ↑ 1.2%        │  Ownership: 91%                   │
│                        │  Glossary Coverage: 75%            │
├────────────────────────┼────────────────────────────────────┤
│  COMPLIANCE            │  ACCESS & SECURITY                 │
│                        │                                    │
│  Policy Compliance: 92%│  Access Reviews Done: 94%         │
│  Overdue Reviews: 3    │  Orphaned Permissions: 12         │
│  DSRs Pending: 7       │  Avg Provision Time: 2.1d         │
│  DSR SLA Met: 100%     │  Policy Violations: 0             │
├────────────────────────┼────────────────────────────────────┤
│  LINEAGE               │  ISSUES & INCIDENTS                │
│                        │                                    │
│  Table Coverage: 93%   │  Open Issues: 23                  │
│  Column Coverage: 71%  │  Resolved (30d): 52               │
│  OpenLineage Jobs: 284 │  MTTR: 2.3 days                   │
│                        │  Within SLA: 93.6%                │
└────────────────────────┴────────────────────────────────────┘
```

### 9.3 ROI of Data Governance

**Cost avoidance:**
- Regulatory fines avoided (GDPR: up to 4% global revenue)
- Breach cost reduction (IBM: $4.45M average breach cost, governance reduces by ~30%)
- Rework reduction (bad data causes 30% of analyst time wasted)

**Value creation:**
- Faster time to insight (catalog reduces data discovery from days to minutes)
- Trusted analytics (quality scores increase stakeholder trust, driving adoption)
- Faster compliance (automated DSRs vs. manual: 80% effort reduction)
- Reduced redundancy (catalog prevents duplicate data asset creation)

**ROI calculation framework:**
```
Annual Governance Cost:
  - Team (5 FTE × $150K): $750K
  - Tooling: $200K
  - Training: $50K
  Total: $1M

Annual Value Delivered:
  - Regulatory fine avoidance (risk-adjusted): $2M
  - Analyst productivity gain (30% of 50 analysts × $120K × 0.3): $1.8M
  - Breach risk reduction (probability × impact reduction): $500K
  - Data quality improvement (fewer pipeline failures): $300K
  - Faster onboarding (new projects start faster): $200K
  Total: $4.8M

ROI = ($4.8M - $1M) / $1M = 380%
```

### 9.4 Business Value Quantification

**Metrics that resonate with business leadership:**

| Metric | Business Translation |
|--------|---------------------|
| Quality Score 98% → 99% | 1% fewer customer complaints from bad data |
| Catalog coverage 80% → 95% | Analysts find data 3x faster |
| DSR automation | From 8 hours/request to 15 minutes/request |
| Access provisioning: 5d → 1d | New team members productive 4 days sooner |
| Lineage coverage 70% → 95% | Change impact known before deployment, fewer incidents |

---

## 10. Lab Exercises

### Lab 1: Deploy DataHub and Catalog a PostgreSQL + S3 Data Ecosystem

**Objective:** Deploy DataHub, ingest metadata from PostgreSQL and S3, configure ownership, tags, and glossary terms.

**Prerequisites:**
- Docker and Docker Compose installed
- PostgreSQL database with sample tables
- S3 bucket (or MinIO for local testing) with Parquet files
- Python 3.9+

**Step 1: Deploy DataHub**

```bash
# Clone DataHub
git clone https://github.com/datahub-project/datahub.git
cd datahub/docker

# Deploy using quickstart
./quickstart.sh

# Verify services
docker compose ps
# Expected: datahub-gms, datahub-frontend, elasticsearch, 
# mysql, kafka, schema-registry, zookeeper
```

**Step 2: Prepare sample data sources**

```sql
-- PostgreSQL: Create sample schema
CREATE SCHEMA raw_data;
CREATE SCHEMA analytics;

CREATE TABLE raw_data.customers (
    customer_id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    address_line1 VARCHAR(255),
    city VARCHAR(100),
    country_code CHAR(2),
    created_at TIMESTAMP DEFAULT NOW(),
    gdpr_consent BOOLEAN DEFAULT FALSE,
    consent_date TIMESTAMP
);

CREATE TABLE raw_data.orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES raw_data.customers(customer_id),
    order_date TIMESTAMP NOT NULL,
    total_amount DECIMAL(10,2),
    currency CHAR(3) DEFAULT 'EUR',
    status VARCHAR(20),
    shipping_address TEXT
);

CREATE TABLE analytics.customer_segments (
    customer_id INTEGER PRIMARY KEY,
    segment VARCHAR(50),
    lifetime_value DECIMAL(12,2),
    churn_risk_score DECIMAL(5,4),
    last_computed TIMESTAMP
);

COMMENT ON TABLE raw_data.customers IS 'Customer master data from CRM system';
COMMENT ON COLUMN raw_data.customers.email IS 'Primary email - PII';
COMMENT ON COLUMN raw_data.customers.phone IS 'Phone number - PII';
```

**Step 3: Configure DataHub ingestion for PostgreSQL**

```yaml
# postgres_recipe.yaml
source:
  type: postgres
  config:
    host_port: "host.docker.internal:5432"
    database: production
    username: "${POSTGRES_USER}"
    password: "${POSTGRES_PASSWORD}"
    include_tables: true
    include_views: true
    schema_pattern:
      allow:
        - "raw_data"
        - "analytics"
    profiling:
      enabled: true
      profile_table_level_only: false
      include_field_null_count: true
      include_field_min_value: true
      include_field_max_value: true

transformers:
  - type: "simple_add_dataset_ownership"
    config:
      owner_urns:
        - "urn:li:corpuser:data-engineering-team"
      ownership_type: "DATAOWNER"
  
  - type: "pattern_add_dataset_tags"
    config:
      tag_pattern:
        rules:
          ".*raw_data\\.customers.*": ["urn:li:tag:PII", "urn:li:tag:GDPR"]
          ".*raw_data\\.orders.*": ["urn:li:tag:Financial"]
          ".*analytics.*": ["urn:li:tag:Derived"]

  - type: "simple_add_dataset_domain"
    config:
      semantics: OVERWRITE
      domain_urn: "urn:li:domain:customer"

sink:
  type: datahub-rest
  config:
    server: "http://localhost:8080"
```

**Step 4: Configure S3/MinIO ingestion**

```yaml
# s3_recipe.yaml
source:
  type: s3
  config:
    path_specs:
      - include: "s3://data-lake/raw/events/{table}/{partition_key[0]}={partition[0]}/*.parquet"
        table_name: "{table}"
      - include: "s3://data-lake/curated/{domain}/{table}/*.parquet"
    aws_config:
      aws_access_key_id: "${AWS_ACCESS_KEY_ID}"
      aws_secret_access_key: "${AWS_SECRET_ACCESS_KEY}"
      aws_region: "eu-west-1"
    env: "PROD"
    platform: "s3"
    profiling:
      enabled: true

sink:
  type: datahub-rest
  config:
    server: "http://localhost:8080"
```

**Step 5: Run ingestion and verify**

```bash
# Install DataHub CLI
pip install acryl-datahub[postgres,s3]

# Run PostgreSQL ingestion
datahub ingest -c postgres_recipe.yaml

# Run S3 ingestion  
datahub ingest -c s3_recipe.yaml

# Verify via CLI
datahub get --urn "urn:li:dataset:(urn:li:dataPlatform:postgres,raw_data.customers,PROD)"
```

**Step 6: Create glossary terms and link**

```bash
# Create business glossary via YAML
cat > glossary.yaml << 'GLOSSARY'
version: 1
source: DataHub
owners:
  users:
    - data-governance-lead
nodes:
  - name: Customer Domain
    description: "Terms related to customer data"
    terms:
      - name: Customer ID
        description: "Unique identifier for a customer across all systems"
        custom_properties:
          source_of_truth: "CRM"
      - name: Lifetime Value
        description: "Total revenue attributed to a customer over their relationship"
        custom_properties:
          calculation: "SUM(order_total) since first_order"
      - name: PII
        description: "Personally Identifiable Information subject to GDPR"
GLOSSARY

datahub ingest -c glossary.yaml
```

---

### Lab 2: Implement Column-Level Lineage with OpenLineage + Airflow

**Objective:** Configure Airflow to emit OpenLineage events with column-level lineage to Marquez, then visualize the lineage.

**Step 1: Deploy Marquez**

```yaml
# docker-compose-marquez.yaml
services:
  marquez-api:
    image: marquezproject/marquez:0.41.0
    ports:
      - "5000:5000"
      - "5001:5001"
    environment:
      - MARQUEZ_PORT=5000
      - MARQUEZ_ADMIN_PORT=5001
      - POSTGRES_HOST=marquez-db
      - POSTGRES_PORT=5432
      - POSTGRES_DB=marquez
      - POSTGRES_USER=marquez
      - POSTGRES_PASSWORD=marquez_secret
    depends_on:
      marquez-db:
        condition: service_healthy

  marquez-web:
    image: marquezproject/marquez-web:0.41.0
    ports:
      - "3000:3000"
    environment:
      - MARQUEZ_HOST=marquez-api
      - MARQUEZ_PORT=5000

  marquez-db:
    image: postgres:15
    environment:
      - POSTGRES_USER=marquez
      - POSTGRES_PASSWORD=marquez_secret
      - POSTGRES_DB=marquez
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U marquez"]
      interval: 5s
      timeout: 5s
      retries: 5
    volumes:
      - marquez-db-data:/var/lib/postgresql/data

volumes:
  marquez-db-data:
```

**Step 2: Configure Airflow with OpenLineage**

```bash
# Install OpenLineage Airflow provider
pip install openlineage-airflow==1.8.0
```

```ini
# airflow.cfg additions
[openlineage]
transport = {"type": "http", "url": "http://marquez-api:5000", "endpoint": "api/v1/lineage"}
namespace = "production"
```

**Step 3: Create an Airflow DAG with lineage-emitting tasks**

```python
# dags/customer_etl_with_lineage.py
from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator

default_args = {
    "owner": "data-engineering",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="customer_dimension_etl",
    default_args=default_args,
    schedule_interval="@hourly",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["customer", "etl", "tier-1"],
) as dag:

    extract_customers = SQLExecuteQueryOperator(
        task_id="extract_customers",
        conn_id="source_postgres",
        sql="""
            CREATE TEMP TABLE staging_customers AS
            SELECT
                customer_id,
                LOWER(email) AS email_normalized,
                full_name,
                country_code,
                created_at,
                gdpr_consent
            FROM raw_data.customers
            WHERE updated_at > '{{ data_interval_start }}'
        """,
        # OpenLineage will parse this SQL to extract column-level lineage
    )

    extract_orders = SQLExecuteQueryOperator(
        task_id="extract_orders",
        conn_id="source_postgres",
        sql="""
            CREATE TEMP TABLE staging_order_agg AS
            SELECT
                customer_id,
                COUNT(*) AS order_count,
                SUM(total_amount) AS lifetime_value,
                MAX(order_date) AS last_order_date
            FROM raw_data.orders
            WHERE order_date > '{{ data_interval_start }}'
            GROUP BY customer_id
        """,
    )

    build_dimension = SQLExecuteQueryOperator(
        task_id="build_customer_dimension",
        conn_id="analytics_postgres",
        sql="""
            INSERT INTO analytics.dim_customers (
                customer_id,
                email,
                full_name,
                country_code,
                order_count,
                lifetime_value,
                last_order_date,
                customer_since,
                has_gdpr_consent,
                etl_updated_at
            )
            SELECT
                c.customer_id,
                c.email_normalized AS email,
                c.full_name,
                c.country_code,
                COALESCE(o.order_count, 0),
                COALESCE(o.lifetime_value, 0),
                o.last_order_date,
                c.created_at AS customer_since,
                c.gdpr_consent AS has_gdpr_consent,
                NOW() AS etl_updated_at
            FROM staging_customers c
            LEFT JOIN staging_order_agg o ON c.customer_id = o.customer_id
            ON CONFLICT (customer_id)
            DO UPDATE SET
                email = EXCLUDED.email,
                order_count = EXCLUDED.order_count,
                lifetime_value = EXCLUDED.lifetime_value,
                last_order_date = EXCLUDED.last_order_date,
                has_gdpr_consent = EXCLUDED.has_gdpr_consent,
                etl_updated_at = EXCLUDED.etl_updated_at
        """,
    )

    extract_customers >> build_dimension
    extract_orders >> build_dimension
```

**Step 4: Verify lineage in Marquez**

```bash
# Query Marquez API for lineage
curl -s http://localhost:5000/api/v1/namespaces/production/jobs/customer_dimension_etl.build_customer_dimension/runs | jq '.runs[0]'

# Get column-level lineage for a specific dataset
curl -s "http://localhost:5000/api/v1/column-lineage?nodeId=dataset:production:analytics.dim_customers" | jq '.'

# Expected response shows column mappings:
# dim_customers.email ← raw_data.customers.email (via LOWER transformation)
# dim_customers.lifetime_value ← raw_data.orders.total_amount (via SUM aggregation)
```

**Step 5: Visualize in Marquez Web UI**

Open `http://localhost:3000` and navigate to the `customer_dimension_etl` job. The lineage graph shows:

```
raw_data.customers ──┐
                     ├──▶ customer_dimension_etl.build_customer_dimension ──▶ analytics.dim_customers
raw_data.orders ─────┘

Column-level detail:
  customers.email → LOWER() → dim_customers.email
  customers.customer_id → PASSTHROUGH → dim_customers.customer_id
  customers.full_name → PASSTHROUGH → dim_customers.full_name
  customers.country_code → PASSTHROUGH → dim_customers.country_code
  customers.created_at → PASSTHROUGH → dim_customers.customer_since
  customers.gdpr_consent → PASSTHROUGH → dim_customers.has_gdpr_consent
  orders.total_amount → SUM() → dim_customers.lifetime_value
  orders.order_date → MAX() → dim_customers.last_order_date
  orders (COUNT) → dim_customers.order_count
```

---

### Lab 3: Create a Data Access Governance Policy with Apache Ranger

**Objective:** Configure Apache Ranger to enforce fine-grained access policies including column masking and row-level filtering.

**Step 1: Deploy Ranger**

```yaml
# docker-compose-ranger.yaml
services:
  ranger-admin:
    image: apache/ranger:2.4.0
    ports:
      - "6080:6080"
    environment:
      - RANGER_ADMIN_DB_HOST=ranger-db
      - RANGER_ADMIN_DB_NAME=ranger
      - RANGER_ADMIN_DB_USER=ranger
      - RANGER_ADMIN_DB_PASSWORD=${RANGER_DB_PASSWORD}
    depends_on:
      - ranger-db
      - solr

  ranger-db:
    image: postgres:15
    environment:
      - POSTGRES_USER=ranger
      - POSTGRES_PASSWORD=${RANGER_DB_PASSWORD}
      - POSTGRES_DB=ranger
    volumes:
      - ranger-db-data:/var/lib/postgresql/data

  solr:
    image: solr:9
    ports:
      - "8983:8983"
    command: solr-precreate ranger_audits

volumes:
  ranger-db-data:
```

**Step 2: Create service definition for Hive/Trino**

```json
{
  "name": "analytics_warehouse",
  "type": "hive",
  "configs": {
    "username": "ranger_admin",
    "password": "ranger_password",
    "jdbc.driverClassName": "org.apache.hive.jdbc.HiveDriver",
    "jdbc.url": "jdbc:hive2://hiveserver:10000"
  }
}
```

**Step 3: Define access policies**

```bash
# Policy 1: Finance team — full access to finance schema, no PII columns
curl -X POST http://localhost:6080/service/public/v2/api/policy \
  -H "Content-Type: application/json" \
  -u admin:rangerAdmin1 \
  -d '{
    "service": "analytics_warehouse",
    "name": "finance-team-access",
    "policyType": 0,
    "resources": {
      "database": {"values": ["finance_warehouse"], "isRecursive": false},
      "table": {"values": ["*"], "isRecursive": false},
      "column": {"values": ["*"], "isRecursive": false}
    },
    "policyItems": [
      {
        "accesses": [{"type": "select", "isAllowed": true}],
        "users": [],
        "groups": ["finance_analysts"],
        "delegateAdmin": false
      }
    ],
    "denyPolicyItems": [
      {
        "accesses": [{"type": "select", "isAllowed": true}],
        "groups": ["finance_analysts"],
        "conditions": [],
        "resources": {
          "database": {"values": ["finance_warehouse"]},
          "table": {"values": ["*"]},
          "column": {"values": ["ssn", "tax_id", "bank_account_number"]}
        }
      }
    ]
  }'

# Policy 2: Column masking for PII
curl -X POST http://localhost:6080/service/public/v2/api/policy \
  -H "Content-Type: application/json" \
  -u admin:rangerAdmin1 \
  -d '{
    "service": "analytics_warehouse",
    "name": "pii-masking-policy",
    "policyType": 1,
    "resources": {
      "database": {"values": ["*"]},
      "table": {"values": ["*"]},
      "column": {"values": ["email", "phone", "ssn"]}
    },
    "dataMaskPolicyItems": [
      {
        "accesses": [{"type": "select", "isAllowed": true}],
        "groups": ["general_analysts"],
        "dataMaskInfo": {
          "dataMaskType": "MASK_HASH",
          "valueExpr": ""
        }
      },
      {
        "accesses": [{"type": "select", "isAllowed": true}],
        "groups": ["pii_authorized"],
        "dataMaskInfo": {
          "dataMaskType": "MASK_NONE"
        }
      }
    ]
  }'

# Policy 3: Row-level security — regional analysts see only their region
curl -X POST http://localhost:6080/service/public/v2/api/policy \
  -H "Content-Type: application/json" \
  -u admin:rangerAdmin1 \
  -d '{
    "service": "analytics_warehouse",
    "name": "regional-row-filter",
    "policyType": 2,
    "resources": {
      "database": {"values": ["analytics"]},
      "table": {"values": ["customer_orders", "customer_profiles"]}
    },
    "rowFilterPolicyItems": [
      {
        "accesses": [{"type": "select", "isAllowed": true}],
        "groups": ["emea_analysts"],
        "rowFilterInfo": {
          "filterExpr": "region = '\''EMEA'\''"
        }
      },
      {
        "accesses": [{"type": "select", "isAllowed": true}],
        "groups": ["apac_analysts"],
        "rowFilterInfo": {
          "filterExpr": "region = '\''APAC'\''"
        }
      },
      {
        "accesses": [{"type": "select", "isAllowed": true}],
        "groups": ["global_analysts"],
        "rowFilterInfo": {
          "filterExpr": "1=1"
        }
      }
    ]
  }'
```

**Step 4: Verify policy enforcement**

```sql
-- As emea_analyst: should only see EMEA rows
SELECT region, COUNT(*) FROM analytics.customer_orders GROUP BY region;
-- Result: EMEA | 15234

-- As global_analyst: sees all regions
SELECT region, COUNT(*) FROM analytics.customer_orders GROUP BY region;
-- Result: EMEA | 15234
--         APAC | 12891
--         AMER | 18456

-- As general_analyst: email column is hashed
SELECT customer_id, email FROM analytics.customer_profiles LIMIT 3;
-- Result: 1001 | a3f2b8c9e1d4...
--         1002 | 7b2e9f4a1c8d...
--         1003 | 5d1c7e3b9a2f...

-- As pii_authorized: email shown in plaintext
SELECT customer_id, email FROM analytics.customer_profiles LIMIT 3;
-- Result: 1001 | alice@example.com
--         1002 | bob@company.org
--         1003 | carol@domain.net
```

**Step 5: Audit trail verification**

```bash
# Query Ranger audit (stored in Solr)
curl -s "http://localhost:8983/solr/ranger_audits/select?q=*:*&rows=5&sort=evtTime+desc&wt=json" | jq '.response.docs[] | {user: .reqUser, resource: .resType, action: .accessType, result: .accessResult, policy: .policyId}'
```

---

### Lab 4: Build a Data Quality Governance Dashboard

**Objective:** Build a governance dashboard that tracks quality scores, catalog coverage, lineage completeness, and policy compliance across domains.

**Step 1: Define metrics schema**

```sql
-- PostgreSQL schema for governance metrics
CREATE SCHEMA governance_metrics;

CREATE TABLE governance_metrics.quality_scores (
    measurement_id SERIAL PRIMARY KEY,
    dataset_urn VARCHAR(500) NOT NULL,
    domain VARCHAR(100) NOT NULL,
    dimension VARCHAR(50) NOT NULL,  -- completeness, validity, etc.
    score DECIMAL(5,4) NOT NULL,     -- 0.0000 to 1.0000
    records_assessed BIGINT,
    records_failed BIGINT,
    measured_at TIMESTAMP NOT NULL DEFAULT NOW(),
    rule_name VARCHAR(200)
);

CREATE TABLE governance_metrics.catalog_coverage (
    measurement_id SERIAL PRIMARY KEY,
    domain VARCHAR(100) NOT NULL,
    total_assets INTEGER NOT NULL,
    cataloged_assets INTEGER NOT NULL,
    assets_with_description INTEGER NOT NULL,
    assets_with_owner INTEGER NOT NULL,
    assets_with_classification INTEGER NOT NULL,
    assets_with_glossary_terms INTEGER NOT NULL,
    measured_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE governance_metrics.lineage_coverage (
    measurement_id SERIAL PRIMARY KEY,
    domain VARCHAR(100) NOT NULL,
    total_datasets INTEGER NOT NULL,
    datasets_with_lineage INTEGER NOT NULL,
    column_lineage_coverage DECIMAL(5,4),
    pipelines_emitting_lineage INTEGER,
    total_pipelines INTEGER,
    measured_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE governance_metrics.policy_compliance (
    measurement_id SERIAL PRIMARY KEY,
    domain VARCHAR(100) NOT NULL,
    policy_name VARCHAR(200) NOT NULL,
    total_assessed INTEGER NOT NULL,
    compliant INTEGER NOT NULL,
    non_compliant INTEGER NOT NULL,
    exceptions_granted INTEGER DEFAULT 0,
    measured_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE governance_metrics.governance_issues (
    issue_id SERIAL PRIMARY KEY,
    domain VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,  -- CRITICAL, HIGH, MEDIUM, LOW
    category VARCHAR(100) NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    dataset_urn VARCHAR(500),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMP,
    assigned_to VARCHAR(200),
    status VARCHAR(20) DEFAULT 'OPEN'
);

-- Indexes for dashboard queries
CREATE INDEX idx_quality_domain_time ON governance_metrics.quality_scores(domain, measured_at DESC);
CREATE INDEX idx_catalog_domain_time ON governance_metrics.catalog_coverage(domain, measured_at DESC);
CREATE INDEX idx_issues_status ON governance_metrics.governance_issues(status, severity);
```

**Step 2: Create metrics collection pipeline**

```python
# governance_metrics_collector.py
"""
Collects governance metrics from DataHub, Marquez, and Ranger
and stores them in the governance metrics database.
"""
import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

import asyncpg
import httpx


@dataclass(frozen=True)
class QualityScore:
    dataset_urn: str
    domain: str
    dimension: str
    score: Decimal
    records_assessed: int
    records_failed: int
    rule_name: Optional[str] = None


class DataHubMetricsCollector:
    """Collects catalog and lineage coverage from DataHub."""

    def __init__(self, datahub_url: str, token: str):
        self._url = datahub_url
        self._headers = {"Authorization": f"Bearer {token}"}

    async def get_catalog_coverage(self, domain: str) -> dict:
        async with httpx.AsyncClient() as client:
            # Query DataHub GraphQL for domain assets
            query = """
            query DomainAssets($domain: String!) {
              search(input: {
                type: DATASET,
                query: "*",
                filters: [{field: "domains", values: [$domain]}]
              }) {
                total
                searchResults {
                  entity {
                    ... on Dataset {
                      urn
                      editableProperties { description }
                      ownership { owners { owner { urn } } }
                      tags { tags { tag { name } } }
                      glossaryTerms { terms { term { name } } }
                    }
                  }
                }
              }
            }
            """
            resp = await client.post(
                f"{self._url}/api/graphql",
                json={"query": query, "variables": {"domain": domain}},
                headers=self._headers,
            )
            data = resp.json()["data"]["search"]
            results = data["searchResults"]

            total = data["total"]
            has_description = sum(
                1 for r in results
                if r["entity"].get("editableProperties", {}).get("description")
            )
            has_owner = sum(
                1 for r in results
                if r["entity"].get("ownership", {}).get("owners")
            )
            has_classification = sum(
                1 for r in results if r["entity"].get("tags", {}).get("tags")
            )
            has_glossary = sum(
                1 for r in results
                if r["entity"].get("glossaryTerms", {}).get("terms")
            )

            return {
                "domain": domain,
                "total_assets": total,
                "cataloged_assets": total,  # all are in catalog by definition
                "assets_with_description": has_description,
                "assets_with_owner": has_owner,
                "assets_with_classification": has_classification,
                "assets_with_glossary_terms": has_glossary,
            }

    async def get_lineage_coverage(self, domain: str) -> dict:
        async with httpx.AsyncClient() as client:
            query = """
            query LineageCoverage($domain: String!) {
              search(input: {
                type: DATASET,
                query: "*",
                filters: [{field: "domains", values: [$domain]}]
              }) {
                total
                searchResults {
                  entity {
                    ... on Dataset {
                      urn
                      upstream: lineage(input: {direction: UPSTREAM, count: 1}) {
                        total
                      }
                    }
                  }
                }
              }
            }
            """
            resp = await client.post(
                f"{self._url}/api/graphql",
                json={"query": query, "variables": {"domain": domain}},
                headers=self._headers,
            )
            data = resp.json()["data"]["search"]
            results = data["searchResults"]

            total = data["total"]
            has_lineage = sum(
                1 for r in results
                if r["entity"].get("upstream", {}).get("total", 0) > 0
            )

            return {
                "domain": domain,
                "total_datasets": total,
                "datasets_with_lineage": has_lineage,
            }


class MetricsStore:
    """Stores governance metrics in PostgreSQL."""

    def __init__(self, dsn: str):
        self._dsn = dsn
        self._pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        self._pool = await asyncpg.create_pool(self._dsn)

    async def store_quality_score(self, score: QualityScore):
        await self._pool.execute(
            """
            INSERT INTO governance_metrics.quality_scores
            (dataset_urn, domain, dimension, score, records_assessed, records_failed, rule_name)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            score.dataset_urn, score.domain, score.dimension,
            score.score, score.records_assessed, score.records_failed,
            score.rule_name,
        )

    async def store_catalog_coverage(self, metrics: dict):
        await self._pool.execute(
            """
            INSERT INTO governance_metrics.catalog_coverage
            (domain, total_assets, cataloged_assets, assets_with_description,
             assets_with_owner, assets_with_classification, assets_with_glossary_terms)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            metrics["domain"], metrics["total_assets"],
            metrics["cataloged_assets"], metrics["assets_with_description"],
            metrics["assets_with_owner"], metrics["assets_with_classification"],
            metrics["assets_with_glossary_terms"],
        )

    async def store_lineage_coverage(self, metrics: dict):
        await self._pool.execute(
            """
            INSERT INTO governance_metrics.lineage_coverage
            (domain, total_datasets, datasets_with_lineage)
            VALUES ($1, $2, $3)
            """,
            metrics["domain"], metrics["total_datasets"],
            metrics["datasets_with_lineage"],
        )

    async def close(self):
        if self._pool:
            await self._pool.close()


async def run_collection():
    store = MetricsStore(dsn="postgresql://governance:secret@localhost:5432/governance")
    await store.connect()

    collector = DataHubMetricsCollector(
        datahub_url="http://localhost:8080",
        token="<datahub-token>",
    )

    domains = ["customer", "finance", "product", "operations"]

    for domain in domains:
        catalog = await collector.get_catalog_coverage(domain)
        await store.store_catalog_coverage(catalog)

        lineage = await collector.get_lineage_coverage(domain)
        await store.store_lineage_coverage(lineage)

    await store.close()


if __name__ == "__main__":
    asyncio.run(run_collection())
```

**Step 3: Dashboard query views**

```sql
-- View: Overall governance score per domain
CREATE OR REPLACE VIEW governance_metrics.v_domain_governance_score AS
WITH latest_quality AS (
    SELECT DISTINCT ON (domain)
        domain,
        AVG(score) OVER (PARTITION BY domain) AS avg_quality_score
    FROM governance_metrics.quality_scores
    WHERE measured_at > NOW() - INTERVAL '24 hours'
    ORDER BY domain, measured_at DESC
),
latest_catalog AS (
    SELECT DISTINCT ON (domain)
        domain,
        assets_with_description::DECIMAL / NULLIF(total_assets, 0) AS description_coverage,
        assets_with_owner::DECIMAL / NULLIF(total_assets, 0) AS ownership_coverage,
        assets_with_classification::DECIMAL / NULLIF(total_assets, 0) AS classification_coverage
    FROM governance_metrics.catalog_coverage
    ORDER BY domain, measured_at DESC
),
latest_lineage AS (
    SELECT DISTINCT ON (domain)
        domain,
        datasets_with_lineage::DECIMAL / NULLIF(total_datasets, 0) AS lineage_coverage
    FROM governance_metrics.lineage_coverage
    ORDER BY domain, measured_at DESC
),
latest_compliance AS (
    SELECT
        domain,
        SUM(compliant)::DECIMAL / NULLIF(SUM(total_assessed), 0) AS compliance_rate
    FROM governance_metrics.policy_compliance
    WHERE measured_at > NOW() - INTERVAL '7 days'
    GROUP BY domain
)
SELECT
    COALESCE(q.domain, c.domain, l.domain, p.domain) AS domain,
    COALESCE(q.avg_quality_score, 0) AS quality_score,
    COALESCE(c.description_coverage, 0) AS catalog_description_pct,
    COALESCE(c.ownership_coverage, 0) AS catalog_ownership_pct,
    COALESCE(c.classification_coverage, 0) AS catalog_classification_pct,
    COALESCE(l.lineage_coverage, 0) AS lineage_coverage_pct,
    COALESCE(p.compliance_rate, 0) AS policy_compliance_pct,
    -- Weighted composite score
    (
        COALESCE(q.avg_quality_score, 0) * 0.30 +
        COALESCE(c.ownership_coverage, 0) * 0.15 +
        COALESCE(c.description_coverage, 0) * 0.15 +
        COALESCE(l.lineage_coverage, 0) * 0.20 +
        COALESCE(p.compliance_rate, 0) * 0.20
    ) AS composite_governance_score
FROM latest_quality q
FULL OUTER JOIN latest_catalog c ON q.domain = c.domain
FULL OUTER JOIN latest_lineage l ON COALESCE(q.domain, c.domain) = l.domain
FULL OUTER JOIN latest_compliance p ON COALESCE(q.domain, c.domain, l.domain) = p.domain;

-- View: Issue summary
CREATE OR REPLACE VIEW governance_metrics.v_issue_summary AS
SELECT
    domain,
    severity,
    COUNT(*) FILTER (WHERE status = 'OPEN') AS open_count,
    COUNT(*) FILTER (WHERE status = 'RESOLVED') AS resolved_count,
    AVG(EXTRACT(EPOCH FROM (COALESCE(resolved_at, NOW()) - created_at)) / 3600)
        FILTER (WHERE status = 'RESOLVED') AS avg_resolution_hours,
    COUNT(*) FILTER (
        WHERE status = 'OPEN'
        AND created_at < NOW() - INTERVAL '5 days'
        AND severity IN ('CRITICAL', 'HIGH')
    ) AS overdue_critical_high
FROM governance_metrics.governance_issues
WHERE created_at > NOW() - INTERVAL '90 days'
GROUP BY domain, severity
ORDER BY domain, 
    CASE severity 
        WHEN 'CRITICAL' THEN 1 
        WHEN 'HIGH' THEN 2 
        WHEN 'MEDIUM' THEN 3 
        WHEN 'LOW' THEN 4 
    END;

-- View: Trend data for time-series charts
CREATE OR REPLACE VIEW governance_metrics.v_quality_trend AS
SELECT
    domain,
    DATE_TRUNC('day', measured_at) AS measurement_date,
    dimension,
    AVG(score) AS avg_score,
    MIN(score) AS min_score,
    MAX(score) AS max_score
FROM governance_metrics.quality_scores
WHERE measured_at > NOW() - INTERVAL '90 days'
GROUP BY domain, DATE_TRUNC('day', measured_at), dimension
ORDER BY domain, measurement_date;
```

**Step 4: Alerting rules**

```yaml
# governance_alerts.yaml
alerts:
  - name: critical_quality_drop
    description: "Data quality score dropped below threshold"
    query: |
      SELECT domain, dimension, score
      FROM governance_metrics.quality_scores
      WHERE measured_at > NOW() - INTERVAL '1 hour'
        AND score < 0.95
        AND dimension IN ('completeness', 'validity')
    severity: CRITICAL
    channel: "#data-governance-alerts"
    
  - name: unowned_assets
    description: "New assets detected without ownership"
    query: |
      SELECT domain, total_assets - assets_with_owner AS unowned
      FROM governance_metrics.catalog_coverage
      WHERE measured_at > NOW() - INTERVAL '24 hours'
        AND (total_assets - assets_with_owner) > 0
    severity: HIGH
    channel: "#data-stewards"
    
  - name: lineage_gap
    description: "Lineage coverage dropped below 80%"
    query: |
      SELECT domain,
             datasets_with_lineage::DECIMAL / NULLIF(total_datasets, 0) AS coverage
      FROM governance_metrics.lineage_coverage
      WHERE measured_at > NOW() - INTERVAL '24 hours'
        AND datasets_with_lineage::DECIMAL / NULLIF(total_datasets, 0) < 0.80
    severity: MEDIUM
    channel: "#data-platform"
    
  - name: overdue_issues
    description: "Governance issues exceeding SLA"
    query: |
      SELECT domain, severity, title, created_at,
             EXTRACT(EPOCH FROM (NOW() - created_at)) / 3600 AS hours_open
      FROM governance_metrics.governance_issues
      WHERE status = 'OPEN'
        AND (
          (severity = 'CRITICAL' AND created_at < NOW() - INTERVAL '4 hours')
          OR (severity = 'HIGH' AND created_at < NOW() - INTERVAL '24 hours')
          OR (severity = 'MEDIUM' AND created_at < NOW() - INTERVAL '5 days')
        )
    severity: HIGH
    channel: "#data-governance-alerts"
```

**Step 5: Grafana dashboard configuration**

```json
{
  "dashboard": {
    "title": "Data Governance Dashboard",
    "panels": [
      {
        "title": "Composite Governance Score by Domain",
        "type": "gauge",
        "targets": [{
          "rawSql": "SELECT domain, composite_governance_score * 100 AS score FROM governance_metrics.v_domain_governance_score",
          "format": "table"
        }],
        "fieldConfig": {
          "defaults": {
            "thresholds": {
              "steps": [
                {"color": "red", "value": 0},
                {"color": "orange", "value": 60},
                {"color": "yellow", "value": 80},
                {"color": "green", "value": 90}
              ]
            },
            "min": 0,
            "max": 100,
            "unit": "percent"
          }
        }
      },
      {
        "title": "Quality Score Trend (90 days)",
        "type": "timeseries",
        "targets": [{
          "rawSql": "SELECT measurement_date AS time, domain, avg_score FROM governance_metrics.v_quality_trend WHERE dimension = 'completeness' ORDER BY measurement_date",
          "format": "time_series"
        }]
      },
      {
        "title": "Open Issues by Severity",
        "type": "barchart",
        "targets": [{
          "rawSql": "SELECT domain, severity, open_count FROM governance_metrics.v_issue_summary WHERE open_count > 0",
          "format": "table"
        }]
      },
      {
        "title": "Catalog Coverage Breakdown",
        "type": "table",
        "targets": [{
          "rawSql": "SELECT domain, ROUND(catalog_description_pct * 100, 1) AS description_pct, ROUND(catalog_ownership_pct * 100, 1) AS ownership_pct, ROUND(catalog_classification_pct * 100, 1) AS classification_pct, ROUND(lineage_coverage_pct * 100, 1) AS lineage_pct FROM governance_metrics.v_domain_governance_score ORDER BY domain",
          "format": "table"
        }]
      }
    ]
  }
}
```

---

## Summary

Data governance is not a one-time project but a continuous organizational discipline. This guide covered:

- **Foundations:** Operating models, roles, decision rights, and maturity assessment provide the organizational backbone.
- **Catalog and metadata:** Discovery, classification, and automated extraction make governance operational.
- **Lineage:** Column-level tracing enables impact analysis, root cause investigation, and regulatory proof.
- **MDM:** Golden records, match/merge, and architecture styles solve the master data fragmentation problem.
- **Data Mesh:** Domain ownership with computational governance scales governance in decentralized organizations.
- **Access control:** RBAC/ABAC/PBAC with column/row-level security and dynamic masking enforce least privilege.
- **Lifecycle:** Retention, archival, disposal, and legal hold manage data from creation to deletion.
- **Compliance:** Privacy by design, consent management, and DSR automation satisfy regulatory requirements.
- **Metrics:** KPIs, dashboards, and ROI quantification justify governance investment.
- **Labs:** Hands-on exercises with DataHub, OpenLineage, Apache Ranger, and governance dashboards provide practical implementation experience.

The key to successful data governance: start with clear organizational accountability, automate everything possible, measure continuously, and iterate based on metrics.
