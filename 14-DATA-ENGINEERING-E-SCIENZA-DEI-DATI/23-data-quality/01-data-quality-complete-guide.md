# Data Quality: Frameworks, Measurement, and Enforcement

## Table of Contents

1. [Data Quality Dimensions](#1-data-quality-dimensions)
2. [Data Quality Frameworks](#2-data-quality-frameworks)
3. [Great Expectations](#3-great-expectations)
4. [dbt Testing](#4-dbt-testing)
5. [Data Contracts](#5-data-contracts)
6. [Data Observability](#6-data-observability)
7. [Data Validation Patterns](#7-data-validation-patterns)
8. [Data Profiling](#8-data-profiling)
9. [Remediation and Root Cause](#9-remediation-and-root-cause)
10. [Lab Exercises](#10-lab-exercises)

---

## 1. Data Quality Dimensions

Data quality is not a binary attribute. It is a multidimensional construct requiring distinct measurement approaches for each facet. A datum can be accurate but stale, complete but inconsistent, or timely but invalid. Understanding each dimension independently enables targeted measurement and improvement.

### 1.1 Accuracy

Accuracy measures how closely data values correspond to the true real-world values they represent.

**Measurement Metrics:**

| Metric | Formula | Target |
|--------|---------|--------|
| Error Rate | `incorrect_records / total_records` | < 0.1% |
| Deviation Score | `mean(abs(measured - actual))` | Context-dependent |
| Source Agreement | `matching_values / compared_values` | > 99.5% |
| Cross-Reference Match | `confirmed_records / sampled_records` | > 99% |

**SLA Definition:**

```yaml
accuracy_sla:
  dimension: accuracy
  measurement_frequency: daily
  targets:
    critical_fields:
      - field: customer_email
        threshold: 99.9%
        measurement: regex_validation + deliverability_check
      - field: transaction_amount
        threshold: 99.99%
        measurement: source_system_reconciliation
    standard_fields:
      threshold: 99.0%
      measurement: cross_reference_sampling
  escalation:
    breach_notification: 15_minutes
    resolution_target: 4_hours
```

**Validation Approaches:**

- Cross-reference with authoritative sources (government databases, master data)
- Statistical sampling and manual verification
- Pattern matching against known formats
- Business rule validation (e.g., birth date cannot be in the future)

### 1.2 Completeness

Completeness measures the degree to which all required data is present.

**Measurement Metrics:**

| Metric | Formula | Target |
|--------|---------|--------|
| Null Rate | `null_values / total_values` per column | Field-specific |
| Record Completeness | `non_null_fields / required_fields` per row | > 95% |
| Schema Completeness | `populated_columns / expected_columns` | 100% |
| Population Completeness | `actual_entities / expected_entities` | > 99% |

**SLA Definition:**

```yaml
completeness_sla:
  dimension: completeness
  targets:
    mandatory_fields:
      null_rate: 0%
      fields: [customer_id, transaction_date, amount]
    important_fields:
      null_rate: < 5%
      fields: [email, phone, address_line_1]
    optional_fields:
      null_rate: < 30%
      fields: [middle_name, secondary_phone]
  measurement:
    method: column_null_count_vs_total_rows
    frequency: per_batch_load
```

### 1.3 Consistency

Consistency measures whether the same data agrees across different systems, tables, or time periods.

**Measurement Metrics:**

| Metric | Formula | Target |
|--------|---------|--------|
| Cross-System Match Rate | `matching_records / total_compared` | > 99.9% |
| Intra-Record Consistency | `valid_combinations / total_records` | 100% |
| Referential Integrity | `matched_fk / total_fk` | 100% |
| Temporal Consistency | `monotonic_sequences / total_sequences` | 100% |

**Validation SQL Example:**

```sql
-- Cross-system consistency check
WITH source_totals AS (
    SELECT DATE(created_at) AS dt, COUNT(*) AS src_count, SUM(amount) AS src_sum
    FROM source_system.transactions
    GROUP BY DATE(created_at)
),
warehouse_totals AS (
    SELECT transaction_date AS dt, COUNT(*) AS wh_count, SUM(amount) AS wh_sum
    FROM warehouse.fact_transactions
    GROUP BY transaction_date
)
SELECT
    COALESCE(s.dt, w.dt) AS check_date,
    s.src_count,
    w.wh_count,
    ABS(s.src_count - w.wh_count) AS count_diff,
    ABS(s.src_sum - w.wh_sum) AS sum_diff,
    CASE
        WHEN ABS(s.src_count - w.wh_count) > 0 THEN 'FAIL'
        WHEN ABS(s.src_sum - w.wh_sum) > 0.01 THEN 'FAIL'
        ELSE 'PASS'
    END AS consistency_status
FROM source_totals s
FULL OUTER JOIN warehouse_totals w ON s.dt = w.dt
WHERE s.dt >= CURRENT_DATE - INTERVAL '7 days';
```

### 1.4 Timeliness and Freshness

Timeliness measures whether data is available when needed. Freshness measures how current the data is relative to the real-world state it represents.

**Measurement Metrics:**

| Metric | Formula | Target |
|--------|---------|--------|
| Data Age | `current_time - max(updated_at)` | < SLA threshold |
| Arrival Latency | `arrival_time - event_time` | < pipeline SLA |
| Processing Lag | `available_time - arrival_time` | < processing SLA |
| Freshness Score | `1 - (age / max_acceptable_age)` | > 0.9 |

**SLA Definition:**

```yaml
freshness_sla:
  dimension: timeliness
  tables:
    - name: fact_transactions
      max_age: 1_hour
      measurement: max(event_timestamp) vs current_timestamp
      alert_threshold: 45_minutes
    - name: dim_customers
      max_age: 24_hours
      measurement: max(updated_at) vs current_timestamp
      alert_threshold: 20_hours
    - name: fact_page_views
      max_age: 15_minutes
      measurement: max(event_time) vs current_timestamp
      alert_threshold: 10_minutes
```

### 1.5 Validity

Validity measures whether data conforms to defined rules, formats, and business constraints.

**Measurement Metrics:**

| Metric | Formula | Target |
|--------|---------|--------|
| Format Compliance | `valid_format / total_values` | > 99.9% |
| Domain Compliance | `in_domain_values / total_values` | 100% for enums |
| Range Compliance | `in_range_values / total_values` | > 99.9% |
| Business Rule Compliance | `passing_rules / total_rules` | 100% for critical |

**Validation Examples:**

```python
from dataclasses import dataclass
from typing import Optional
import re
from datetime import date


@dataclass(frozen=True)
class ValidationRule:
    field: str
    rule_type: str
    parameters: dict
    severity: str  # "error" | "warning"


VALIDATION_RULES = [
    ValidationRule(
        field="email",
        rule_type="regex",
        parameters={"pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"},
        severity="error",
    ),
    ValidationRule(
        field="age",
        rule_type="range",
        parameters={"min": 0, "max": 150},
        severity="error",
    ),
    ValidationRule(
        field="country_code",
        rule_type="enum",
        parameters={"allowed": ["US", "GB", "DE", "FR", "IT", "ES", "BR", "JP"]},
        severity="error",
    ),
    ValidationRule(
        field="transaction_date",
        rule_type="temporal",
        parameters={"not_future": True, "not_before": "2000-01-01"},
        severity="error",
    ),
]
```

### 1.6 Uniqueness

Uniqueness measures whether data records are free from unintended duplicates.

**Measurement Metrics:**

| Metric | Formula | Target |
|--------|---------|--------|
| Duplicate Rate | `duplicate_records / total_records` | 0% for PKs |
| Near-Duplicate Rate | `fuzzy_matches / total_records` | < 0.1% |
| Key Uniqueness | `distinct_keys / total_keys` | 100% |
| Entity Resolution Ambiguity | `ambiguous_matches / total_entities` | < 1% |

**Detection SQL:**

```sql
-- Exact duplicate detection
WITH duplicates AS (
    SELECT
        customer_id,
        email,
        COUNT(*) AS occurrence_count,
        MIN(created_at) AS first_seen,
        MAX(created_at) AS last_seen
    FROM dim_customers
    GROUP BY customer_id, email
    HAVING COUNT(*) > 1
)
SELECT
    COUNT(*) AS duplicate_groups,
    SUM(occurrence_count - 1) AS excess_records,
    SUM(occurrence_count - 1)::FLOAT / (SELECT COUNT(*) FROM dim_customers) AS duplicate_rate
FROM duplicates;

-- Near-duplicate detection using similarity
SELECT
    a.customer_id AS id_a,
    b.customer_id AS id_b,
    a.email AS email_a,
    b.email AS email_b,
    similarity(a.full_name, b.full_name) AS name_similarity
FROM dim_customers a
JOIN dim_customers b
    ON a.customer_id < b.customer_id
    AND a.email = b.email
    AND similarity(a.full_name, b.full_name) > 0.8;
```

### 1.7 Integrity

Integrity measures whether relationships between data elements are maintained correctly.

**Measurement Metrics:**

| Metric | Formula | Target |
|--------|---------|--------|
| Referential Integrity | `matched_fk / total_fk_values` | 100% |
| Cardinality Compliance | `valid_cardinality / total_relationships` | 100% |
| Cascade Integrity | `properly_cascaded / total_cascades` | 100% |
| Aggregate Integrity | `matching_aggregates / total_aggregates` | 100% |

### 1.8 Data Quality Scoring Models

**Composite Score Calculation:**

```python
from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class DimensionScore:
    dimension: str
    score: float  # 0.0 to 1.0
    weight: float
    threshold: float


def calculate_dq_score(scores: list[DimensionScore]) -> Dict[str, float]:
    """Calculate weighted composite data quality score."""
    total_weight = sum(s.weight for s in scores)
    weighted_sum = sum(s.score * s.weight for s in scores)
    composite = weighted_sum / total_weight if total_weight > 0 else 0.0

    breaches = [s for s in scores if s.score < s.threshold]

    return {
        "composite_score": round(composite, 4),
        "dimensions_passing": len(scores) - len(breaches),
        "dimensions_total": len(scores),
        "critical_breaches": [s.dimension for s in breaches],
        "grade": _score_to_grade(composite),
    }


def _score_to_grade(score: float) -> str:
    if score >= 0.98:
        return "A"
    elif score >= 0.95:
        return "B"
    elif score >= 0.90:
        return "C"
    elif score >= 0.80:
        return "D"
    return "F"


# Usage
dimension_scores = [
    DimensionScore("accuracy", 0.997, weight=0.25, threshold=0.99),
    DimensionScore("completeness", 0.985, weight=0.20, threshold=0.95),
    DimensionScore("consistency", 0.999, weight=0.20, threshold=0.99),
    DimensionScore("timeliness", 0.950, weight=0.15, threshold=0.90),
    DimensionScore("validity", 0.998, weight=0.10, threshold=0.99),
    DimensionScore("uniqueness", 1.000, weight=0.05, threshold=0.999),
    DimensionScore("integrity", 1.000, weight=0.05, threshold=0.999),
]

result = calculate_dq_score(dimension_scores)
```

---

## 2. Data Quality Frameworks

### 2.1 DAMA-DMBOK Data Quality Model

The Data Management Association's Body of Knowledge (DAMA-DMBOK) provides a comprehensive framework treating data quality as one of eleven knowledge areas in data management. The model integrates quality into the broader data governance lifecycle.

**Core Activities in DAMA-DMBOK DQ:**

1. **Define Data Quality Requirements** — Establish business-driven quality expectations per data domain
2. **Define a Data Quality Strategy** — Create organizational approach to DQ improvement
3. **Identify and Assess Data Quality Issues** — Profile, measure, root-cause analysis
4. **Define Metrics and Business Rules** — Translate requirements into measurable thresholds
5. **Develop and Deploy DQ Operations** — Implement monitoring, cleansing, enrichment
6. **Implement Governance and Stewardship** — Assign ownership and accountability

**DAMA DQ Operating Model:**

```
┌─────────────────────────────────────────────────┐
│              DATA GOVERNANCE COUNCIL             │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │  Data    │  │  Data    │  │  Data    │     │
│  │  Owner   │  │  Steward │  │  Custodian│     │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘     │
│       │              │              │           │
│       ▼              ▼              ▼           │
│  ┌──────────────────────────────────────┐      │
│  │        DATA QUALITY PROGRAM          │      │
│  ├──────────────────────────────────────┤      │
│  │ • Assessment & Profiling             │      │
│  │ • Rules & Metrics Definition         │      │
│  │ • Monitoring & Alerting              │      │
│  │ • Issue Management & Remediation     │      │
│  │ • Reporting & Communication          │      │
│  └──────────────────────────────────────┘      │
│                                                 │
└─────────────────────────────────────────────────┘
```

### 2.2 ISO 8000

ISO 8000 is the international standard for data quality. It provides a formal specification for master data quality and defines requirements for data exchange.

**Key Parts:**

| Part | Title | Focus |
|------|-------|-------|
| ISO 8000-1 | Overview | Concepts and vocabulary |
| ISO 8000-2 | Vocabulary | Formal definitions |
| ISO 8000-8 | Information and data quality | General requirements |
| ISO 8000-61 | Data quality management | Process approach |
| ISO 8000-100 | Master data: Exchange | Quality of exchanged master data |
| ISO 8000-110 | Master data: Syntax | Syntax encoding |
| ISO 8000-120 | Master data: Provenance | Data origin tracking |
| ISO 8000-130 | Master data: Accuracy | Accuracy requirements |
| ISO 8000-140 | Master data: Completeness | Completeness criteria |
| ISO 8000-150 | Master data: Currency/timeliness | Freshness standards |

**ISO 8000 Compliance Checklist:**

```yaml
iso_8000_compliance:
  part_61_process:
    - define_quality_policy: true
    - establish_objectives: true
    - assign_responsibilities: true
    - monitor_and_measure: true
    - continuous_improvement: true
  part_100_exchange:
    - syntactic_accuracy: validated
    - semantic_accuracy: verified
    - provenance_documented: true
    - authorization_confirmed: true
  part_120_provenance:
    - data_originator_identified: true
    - creation_timestamp_recorded: true
    - transformation_chain_documented: true
    - authorization_chain_intact: true
```

### 2.3 Total Data Quality Management (TDQM)

TDQM, developed at MIT by Richard Wang and colleagues, treats data quality management as a continuous improvement cycle analogous to Total Quality Management (TQM) for manufacturing.

**TDQM Cycle:**

```
        ┌──────────┐
        │  DEFINE  │ ← Identify DQ dimensions relevant to stakeholders
        └────┬─────┘
             │
             ▼
        ┌──────────┐
        │ MEASURE  │ ← Quantify current quality levels
        └────┬─────┘
             │
             ▼
        ┌──────────┐
        │ ANALYZE  │ ← Root-cause analysis of deficiencies
        └────┬─────┘
             │
             ▼
        ┌──────────┐
        │ IMPROVE  │ ← Implement corrective actions
        └────┬─────┘
             │
             └──────────→ (back to DEFINE)
```

**Key Principles:**

1. **Data as Product** — Treat data with the same quality discipline as physical products
2. **Data Consumer Focus** — Quality is defined by fitness for use, not absolute perfection
3. **Process Orientation** — Quality results from well-managed processes
4. **Continuous Improvement** — Quality is never "done"; iterate perpetually

### 2.4 Data Quality Maturity Models

**Five-Level Maturity Model:**

| Level | Name | Characteristics |
|-------|------|-----------------|
| 1 | Initial | Ad-hoc, reactive, no formal DQ processes |
| 2 | Repeatable | Basic DQ checks exist, manual, per-project |
| 3 | Defined | Organization-wide DQ standards, automated monitoring |
| 4 | Managed | Quantitative DQ management, SLAs enforced, root-cause analysis |
| 5 | Optimizing | Predictive DQ, self-healing pipelines, continuous improvement culture |

**Maturity Assessment Framework:**

```python
MATURITY_ASSESSMENT = {
    "governance": {
        "level_1": "No formal data ownership",
        "level_2": "Some data owners identified informally",
        "level_3": "Formal data ownership and stewardship roles defined",
        "level_4": "Data governance council active, policies enforced",
        "level_5": "Self-service governance, automated policy enforcement",
    },
    "measurement": {
        "level_1": "No DQ metrics defined",
        "level_2": "Basic null checks and row counts",
        "level_3": "Multi-dimensional DQ scoring, dashboards",
        "level_4": "SLA-driven alerting, trend analysis",
        "level_5": "Predictive anomaly detection, auto-remediation",
    },
    "tooling": {
        "level_1": "Manual SQL queries for ad-hoc checks",
        "level_2": "Scripts and notebooks for periodic validation",
        "level_3": "DQ framework deployed (GX, dbt tests)",
        "level_4": "Full observability platform, data contracts",
        "level_5": "ML-driven anomaly detection, self-healing pipelines",
    },
    "culture": {
        "level_1": "DQ is someone else's problem",
        "level_2": "Engineers add checks when things break",
        "level_3": "DQ is part of definition of done",
        "level_4": "DQ metrics in team OKRs, producer accountability",
        "level_5": "DQ excellence as competitive advantage",
    },
}
```

### 2.5 Building a Data Quality Program

**Governance Structure:**

```
Data Quality Program Structure:

Executive Sponsor
    └── Data Quality Council
            ├── Data Domain Owners (Business)
            │       └── Define requirements and SLAs
            ├── Data Stewards (Business + Tech)
            │       └── Day-to-day quality oversight
            ├── Data Engineers (Tech)
            │       └── Implement checks and remediation
            └── Data Quality Analysts (Tech)
                    └── Measure, report, investigate

Communication Cadence:
  - Weekly: Steward sync (operational issues)
  - Bi-weekly: DQ Council meeting (metrics review)
  - Monthly: Executive report (trends, ROI)
  - Quarterly: Maturity assessment and roadmap update
```

**Issue Management Workflow:**

```yaml
dq_issue_lifecycle:
  states:
    - detected: "Automated check or user report identifies issue"
    - triaged: "Severity assessed, owner assigned"
    - investigating: "Root cause analysis in progress"
    - remediation_planned: "Fix identified, implementation scheduled"
    - remediation_in_progress: "Fix being implemented"
    - validation: "Fix deployed, verifying resolution"
    - resolved: "Issue confirmed fixed, monitoring"
    - closed: "Post-mortem complete, preventive measures in place"
  severity_levels:
    critical:
      response_time: 15_minutes
      resolution_target: 4_hours
      criteria: "Revenue-impacting, regulatory, customer-facing corruption"
    high:
      response_time: 1_hour
      resolution_target: 24_hours
      criteria: "Analytics incorrect, operational decisions affected"
    medium:
      response_time: 4_hours
      resolution_target: 1_week
      criteria: "Non-critical field quality degradation"
    low:
      response_time: 1_business_day
      resolution_target: 1_month
      criteria: "Cosmetic, optional field, edge case"
```

---

## 3. Great Expectations

Great Expectations (GX) is the dominant open-source framework for data validation, documentation, and profiling. It enables declarative definition of data quality expectations that can be executed against any data source.

### 3.1 Core Concepts

**Architecture:**

```
┌─────────────────────────────────────────────────────────┐
│                    GX ECOSYSTEM                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Data Context                                           │
│  ├── Data Sources (Pandas, Spark, SQL)                  │
│  │   └── Data Assets                                    │
│  │       └── Batch Definitions                          │
│  ├── Expectation Suites                                 │
│  │   └── Individual Expectations                        │
│  ├── Checkpoints                                        │
│  │   └── Validation Definitions                         │
│  │       ├── Batch + Suite binding                      │
│  │       └── Actions (notify, store, render)            │
│  └── Data Docs (auto-generated documentation)           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Key Components:**

- **Data Context** — The primary GX API entry point managing all configuration
- **Expectations** — Declarative assertions about data (e.g., "this column should not be null")
- **Expectation Suites** — Named collections of expectations applied to a data asset
- **Checkpoints** — Orchestration units that run validations and trigger actions
- **Data Docs** — Auto-generated HTML documentation of expectations and results
- **Validation Results** — Structured output of pass/fail per expectation with diagnostics

### 3.2 Setup and Configuration

```python
import great_expectations as gx

# Initialize context (file-based)
context = gx.get_context()

# Add a data source
datasource = context.data_sources.add_pandas("my_pandas_source")

# Define a data asset
data_asset = datasource.add_csv_asset(
    name="transactions",
    filepath_or_buffer="data/transactions.csv",
)

# Create a batch definition
batch_definition = data_asset.add_batch_definition_whole_dataframe("full_batch")
```

### 3.3 Built-in Expectations (100+ Types)

GX ships with over 100 built-in expectations organized by category:

**Column Value Expectations:**

```python
# Null checks
suite.add_expectation(
    gx.expectations.ExpectColumnValuesToNotBeNull(column="customer_id")
)

# Type checks
suite.add_expectation(
    gx.expectations.ExpectColumnValuesToBeOfType(
        column="amount", type_="float64"
    )
)

# Range checks
suite.add_expectation(
    gx.expectations.ExpectColumnValuesToBeBetween(
        column="age", min_value=0, max_value=150
    )
)

# Set membership
suite.add_expectation(
    gx.expectations.ExpectColumnValuesToBeInSet(
        column="status", value_set=["active", "inactive", "pending", "closed"]
    )
)

# Pattern matching
suite.add_expectation(
    gx.expectations.ExpectColumnValuesToMatchRegex(
        column="email",
        regex=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
    )
)

# Uniqueness
suite.add_expectation(
    gx.expectations.ExpectColumnValuesToBeUnique(column="transaction_id")
)
```

**Column Aggregate Expectations:**

```python
# Statistical bounds
suite.add_expectation(
    gx.expectations.ExpectColumnMeanToBeBetween(
        column="order_value", min_value=50.0, max_value=500.0
    )
)

suite.add_expectation(
    gx.expectations.ExpectColumnMedianToBeBetween(
        column="delivery_days", min_value=1, max_value=14
    )
)

suite.add_expectation(
    gx.expectations.ExpectColumnStdevToBeBetween(
        column="temperature", min_value=0.5, max_value=5.0
    )
)

# Cardinality
suite.add_expectation(
    gx.expectations.ExpectColumnDistinctValuesToBeInSet(
        column="country_code",
        value_set=["US", "GB", "DE", "FR", "IT", "ES", "BR", "JP", "IN", "AU"],
    )
)

suite.add_expectation(
    gx.expectations.ExpectColumnUniqueValueCountToBeBetween(
        column="product_category", min_value=5, max_value=50
    )
)
```

**Table-Level Expectations:**

```python
# Row count
suite.add_expectation(
    gx.expectations.ExpectTableRowCountToBeBetween(
        min_value=1000, max_value=10000000
    )
)

# Column presence
suite.add_expectation(
    gx.expectations.ExpectTableColumnsToMatchOrderedList(
        column_list=["id", "customer_id", "amount", "currency", "created_at"]
    )
)

# Multi-column
suite.add_expectation(
    gx.expectations.ExpectMulticolumnSumToEqual(
        column_list=["subtotal", "tax", "shipping"],
        sum_total_column="total",
    )
)

suite.add_expectation(
    gx.expectations.ExpectCompoundColumnsToBeUnique(
        column_list=["customer_id", "order_date", "product_id"]
    )
)
```

### 3.4 Custom Expectations Development

```python
from great_expectations.expectations import ExpectColumnValuesToMatchCondition
from great_expectations.core import ExpectationConfiguration
import great_expectations as gx


class ExpectColumnValuesToBeValidIBAN(gx.expectations.ExpectColumnValuesToMatchRegex):
    """Custom expectation: validates IBAN format with country-specific length."""

    description = "Expect column values to be valid IBAN numbers"

    # IBAN lengths per country (subset)
    IBAN_LENGTHS = {
        "DE": 22, "GB": 22, "FR": 27, "IT": 27, "ES": 24,
        "NL": 18, "BE": 16, "AT": 20, "CH": 21, "PT": 25,
    }

    regex = r"^[A-Z]{2}\d{2}[A-Z0-9]{4,30}$"

    @classmethod
    def _validate(cls, value):
        if not isinstance(value, str):
            return False
        if len(value) < 5:
            return False
        country_code = value[:2]
        expected_length = cls.IBAN_LENGTHS.get(country_code)
        if expected_length and len(value) != expected_length:
            return False
        return bool(__import__("re").match(cls.regex, value))
```

### 3.5 Integration with Airflow

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime


def run_gx_checkpoint(checkpoint_name: str, **kwargs):
    """Execute a Great Expectations checkpoint within Airflow."""
    import great_expectations as gx

    context = gx.get_context(
        project_root_dir="/opt/airflow/gx"
    )
    result = context.checkpoints.get(checkpoint_name).run()

    if not result.success:
        failed = [
            r.expectation_config.type
            for r in result.run_results.values()
            for vr in r.results
            if not vr.success
        ]
        raise ValueError(
            f"Data quality checkpoint '{checkpoint_name}' failed. "
            f"Failed expectations: {failed}"
        )


with DAG(
    "data_quality_pipeline",
    schedule_interval="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
) as dag:

    validate_raw = PythonOperator(
        task_id="validate_raw_transactions",
        python_callable=run_gx_checkpoint,
        op_kwargs={"checkpoint_name": "raw_transactions_checkpoint"},
    )

    transform = PythonOperator(
        task_id="transform_transactions",
        python_callable=lambda: ...,  # transformation logic
    )

    validate_transformed = PythonOperator(
        task_id="validate_transformed",
        python_callable=run_gx_checkpoint,
        op_kwargs={"checkpoint_name": "transformed_transactions_checkpoint"},
    )

    validate_raw >> transform >> validate_transformed
```

### 3.6 Integration with dbt

```yaml
# dbt_project.yml - GX integration via dbt artifacts
# Use dbt run-results to feed GX validation

# great_expectations/checkpoints/dbt_checkpoint.yml
name: dbt_models_checkpoint
validations:
  - expectation_suite_name: dbt_staging_suite
    batch_request:
      datasource_name: warehouse
      data_asset_name: stg_transactions
      options:
        schema: analytics
        table: stg_transactions
  - expectation_suite_name: dbt_mart_suite
    batch_request:
      datasource_name: warehouse
      data_asset_name: fct_orders
      options:
        schema: analytics
        table: fct_orders
```

### 3.7 Integration with Spark

```python
import great_expectations as gx
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("gx_validation").getOrCreate()

context = gx.get_context()

# Add Spark datasource
spark_datasource = context.data_sources.add_spark("spark_source")

# Add asset from existing DataFrame
df = spark.read.parquet("s3://bucket/transactions/")
data_asset = spark_datasource.add_dataframe_asset(name="spark_transactions")
batch_definition = data_asset.add_batch_definition_whole_dataframe("spark_batch")

# Get batch and validate
batch = batch_definition.get_batch(batch_parameters={"dataframe": df})
results = batch.validate(suite)
```

### 3.8 Deployment Patterns

**In-Process (Embedded):**
- GX runs within the existing pipeline process
- Lowest latency, no additional infrastructure
- Best for: Airflow tasks, dbt post-hooks, Spark jobs

**Standalone Service:**
- GX runs as a separate microservice with API
- Decoupled from pipeline code
- Best for: multi-team environments, centralized DQ platform

**GX Cloud:**
- Managed SaaS offering
- Collaborative suite management via UI
- Best for: organizations wanting minimal infrastructure overhead

---

## 4. dbt Testing

dbt (data build tool) provides native testing capabilities that integrate quality checks directly into the transformation layer. Tests run as SQL queries that assert zero rows returned equals success.

### 4.1 Generic Tests (Built-in)

```yaml
# models/staging/stg_transactions.yml
version: 2

models:
  - name: stg_transactions
    description: "Staged transaction data from source system"
    columns:
      - name: transaction_id
        description: "Unique transaction identifier"
        data_tests:
          - unique
          - not_null

      - name: customer_id
        description: "Foreign key to customers"
        data_tests:
          - not_null
          - relationships:
              to: ref('stg_customers')
              field: customer_id

      - name: status
        description: "Transaction status"
        data_tests:
          - accepted_values:
              values: ['pending', 'completed', 'failed', 'refunded', 'cancelled']

      - name: amount
        description: "Transaction amount in base currency"
        data_tests:
          - not_null

      - name: currency_code
        description: "ISO 4217 currency code"
        data_tests:
          - not_null
          - accepted_values:
              values: ['USD', 'EUR', 'GBP', 'JPY', 'BRL', 'CAD', 'AUD']
```

### 4.2 Custom Singular Tests

Singular tests are standalone SQL files in the `tests/` directory:

```sql
-- tests/assert_transaction_amounts_positive.sql
-- Ensures all completed transactions have positive amounts

SELECT
    transaction_id,
    amount,
    status
FROM {{ ref('stg_transactions') }}
WHERE status = 'completed'
  AND amount <= 0
```

```sql
-- tests/assert_daily_transaction_count_reasonable.sql
-- Ensures we don't have suspiciously low or high daily counts

WITH daily_counts AS (
    SELECT
        DATE(transaction_date) AS dt,
        COUNT(*) AS txn_count
    FROM {{ ref('fct_transactions') }}
    WHERE transaction_date >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY DATE(transaction_date)
),
stats AS (
    SELECT
        AVG(txn_count) AS avg_count,
        STDDEV(txn_count) AS stddev_count
    FROM daily_counts
)
SELECT
    dc.dt,
    dc.txn_count,
    s.avg_count,
    s.stddev_count
FROM daily_counts dc
CROSS JOIN stats s
WHERE dc.txn_count < s.avg_count - (3 * s.stddev_count)
   OR dc.txn_count > s.avg_count + (3 * s.stddev_count)
```

```sql
-- tests/assert_revenue_reconciliation.sql
-- Cross-validates revenue between fact table and source

WITH fact_revenue AS (
    SELECT
        DATE_TRUNC('day', order_date) AS dt,
        SUM(total_amount) AS fact_total
    FROM {{ ref('fct_orders') }}
    WHERE order_date >= CURRENT_DATE - INTERVAL '7 days'
    GROUP BY 1
),
source_revenue AS (
    SELECT
        DATE_TRUNC('day', created_at) AS dt,
        SUM(amount) AS source_total
    FROM {{ source('payments', 'transactions') }}
    WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
      AND status = 'completed'
    GROUP BY 1
)
SELECT
    COALESCE(f.dt, s.dt) AS dt,
    f.fact_total,
    s.source_total,
    ABS(f.fact_total - s.source_total) AS discrepancy
FROM fact_revenue f
FULL OUTER JOIN source_revenue s ON f.dt = s.dt
WHERE ABS(COALESCE(f.fact_total, 0) - COALESCE(s.source_total, 0)) > 1.00
```

### 4.3 dbt_utils Package Tests

```yaml
# packages.yml
packages:
  - package: dbt-labs/dbt_utils
    version: [">=1.0.0", "<2.0.0"]
```

```yaml
# models/marts/fct_orders.yml
version: 2

models:
  - name: fct_orders
    data_tests:
      # Ensure no duplicate rows across compound key
      - dbt_utils.unique_combination_of_columns:
          combination_of_columns:
            - order_id
            - line_item_id

      # Ensure referential integrity with multiple tables
      - dbt_utils.relationships_where:
          to: ref('dim_products')
          field: product_id
          from_condition: "product_id IS NOT NULL"
          to_condition: "is_active = true"

      # Expression validation
      - dbt_utils.expression_is_true:
          expression: "quantity > 0"
          config:
            where: "status != 'cancelled'"

      # Recency check
      - dbt_utils.recency:
          datepart: hour
          field: created_at
          interval: 24

      # Row count delta
      - dbt_utils.equal_rowcount:
          compare_model: ref('stg_orders')

    columns:
      - name: order_date
        data_tests:
          - dbt_utils.not_null_proportion:
              at_least: 0.99
          - dbt_utils.accepted_range:
              min_value: "'2020-01-01'"
              max_value: "CURRENT_DATE"

      - name: total_amount
        data_tests:
          - dbt_utils.accepted_range:
              min_value: 0
              max_value: 1000000
              inclusive: true
```

### 4.4 dbt_expectations Package

```yaml
# packages.yml
packages:
  - package: calogica/dbt_expectations
    version: [">=0.10.0", "<0.11.0"]
```

```yaml
# models/marts/fct_transactions.yml
version: 2

models:
  - name: fct_transactions
    data_tests:
      # Table shape expectations
      - dbt_expectations.expect_table_row_count_to_be_between:
          min_value: 1000
          max_value: 10000000

      - dbt_expectations.expect_table_row_count_to_equal_other_table:
          compare_model: ref('stg_transactions')

      - dbt_expectations.expect_table_columns_to_contain_set:
          column_list:
            - transaction_id
            - customer_id
            - amount
            - created_at

    columns:
      - name: amount
        data_tests:
          - dbt_expectations.expect_column_values_to_be_between:
              min_value: 0
              max_value: 999999.99
              row_condition: "status = 'completed'"

          - dbt_expectations.expect_column_mean_to_be_between:
              min_value: 10
              max_value: 1000

          - dbt_expectations.expect_column_stdev_to_be_between:
              min_value: 5
              max_value: 500

          - dbt_expectations.expect_column_quantile_values_to_be_between:
              quantile: 0.95
              min_value: 10
              max_value: 5000

      - name: email
        data_tests:
          - dbt_expectations.expect_column_values_to_match_regex:
              regex: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
              row_condition: "email IS NOT NULL"

      - name: created_at
        data_tests:
          - dbt_expectations.expect_row_values_to_have_recent_data:
              datepart: hour
              interval: 24

          - dbt_expectations.expect_column_values_to_be_increasing:
              sort_column: transaction_id
              strictly: false
```

### 4.5 Custom Generic Tests

```sql
-- tests/generic/test_column_values_within_n_stdev.sql
{% test column_values_within_n_stdev(model, column_name, n_stdev=3) %}

WITH stats AS (
    SELECT
        AVG({{ column_name }}) AS col_mean,
        STDDEV({{ column_name }}) AS col_stdev
    FROM {{ model }}
    WHERE {{ column_name }} IS NOT NULL
)
SELECT
    t.{{ column_name }},
    s.col_mean,
    s.col_stdev
FROM {{ model }} t
CROSS JOIN stats s
WHERE t.{{ column_name }} IS NOT NULL
  AND (
      t.{{ column_name }} < s.col_mean - ({{ n_stdev }} * s.col_stdev)
      OR t.{{ column_name }} > s.col_mean + ({{ n_stdev }} * s.col_stdev)
  )

{% endtest %}
```

```sql
-- tests/generic/test_freshness_within_threshold.sql
{% test freshness_within_threshold(model, column_name, max_hours=24) %}

SELECT
    MAX({{ column_name }}) AS latest_record,
    CURRENT_TIMESTAMP AS check_time,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - MAX({{ column_name }}))) / 3600 AS hours_since_latest
FROM {{ model }}
HAVING EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - MAX({{ column_name }}))) / 3600 > {{ max_hours }}

{% endtest %}
```

```sql
-- tests/generic/test_referential_integrity_percentage.sql
{% test referential_integrity_percentage(model, column_name, to, field, min_percentage=99.0) %}

WITH integrity_check AS (
    SELECT
        COUNT(*) AS total_records,
        COUNT(CASE WHEN t.{{ field }} IS NOT NULL THEN 1 END) AS matched_records
    FROM {{ model }} s
    LEFT JOIN {{ to }} t ON s.{{ column_name }} = t.{{ field }}
    WHERE s.{{ column_name }} IS NOT NULL
)
SELECT
    total_records,
    matched_records,
    (matched_records::FLOAT / NULLIF(total_records, 0)) * 100 AS match_percentage
FROM integrity_check
WHERE (matched_records::FLOAT / NULLIF(total_records, 0)) * 100 < {{ min_percentage }}

{% endtest %}
```

**Usage in schema YAML:**

```yaml
columns:
  - name: revenue
    data_tests:
      - column_values_within_n_stdev:
          n_stdev: 3

  - name: updated_at
    data_tests:
      - freshness_within_threshold:
          max_hours: 6

  - name: product_id
    data_tests:
      - referential_integrity_percentage:
          to: ref('dim_products')
          field: product_id
          min_percentage: 99.5
```

### 4.6 Test Severity and Configuration

```yaml
# models/staging/stg_customers.yml
version: 2

models:
  - name: stg_customers
    columns:
      - name: customer_id
        data_tests:
          - unique:
              severity: error  # Blocks pipeline
          - not_null:
              severity: error  # Blocks pipeline

      - name: email
        data_tests:
          - not_null:
              severity: warn  # Logs warning, continues
          - unique:
              severity: warn
              config:
                where: "email IS NOT NULL"

      - name: phone_number
        data_tests:
          - not_null:
              severity: warn
              config:
                error_if: ">10%"   # Error if more than 10% null
                warn_if: ">5%"     # Warn if more than 5% null

      - name: created_at
        data_tests:
          - not_null:
              severity: error
              tags: ['critical', 'freshness']
          - freshness_within_threshold:
              max_hours: 24
              severity: error
              tags: ['critical', 'freshness']
```

### 4.7 Test Selection and Tagging

```bash
# Run only critical tests
dbt test --select tag:critical

# Run tests for a specific model
dbt test --select stg_transactions

# Run tests for a model and all downstream
dbt test --select stg_transactions+

# Run only freshness tests
dbt test --select tag:freshness

# Run tests excluding slow ones
dbt test --exclude tag:slow

# Run specific test types
dbt test --select test_type:singular
dbt test --select test_type:generic
```

---

## 5. Data Contracts

Data contracts formalize the agreement between data producers and consumers, specifying schema, quality expectations, SLAs, and change management procedures.

### 5.1 Schema-First Development

The schema-first approach inverts the traditional pattern: instead of inferring schema from data, the schema is defined first and data must conform to it.

**Principles:**

1. Schema is the source of truth, not the data
2. Breaking changes require explicit versioning and consumer notification
3. Producers are accountable for contract compliance
4. Contracts are tested in CI/CD before deployment

### 5.2 Contract Specification Formats

**JSON Schema:**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://company.com/schemas/transactions/v2.0.0",
  "title": "Transaction Event",
  "description": "Contract for transaction events from payments service",
  "type": "object",
  "required": ["transaction_id", "customer_id", "amount", "currency", "timestamp", "status"],
  "properties": {
    "transaction_id": {
      "type": "string",
      "format": "uuid",
      "description": "Unique transaction identifier"
    },
    "customer_id": {
      "type": "string",
      "format": "uuid",
      "description": "Customer who initiated the transaction"
    },
    "amount": {
      "type": "number",
      "minimum": 0,
      "maximum": 999999.99,
      "description": "Transaction amount in minor units"
    },
    "currency": {
      "type": "string",
      "enum": ["USD", "EUR", "GBP", "JPY", "BRL"],
      "description": "ISO 4217 currency code"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 timestamp of transaction creation"
    },
    "status": {
      "type": "string",
      "enum": ["pending", "processing", "completed", "failed", "refunded"],
      "description": "Current transaction status"
    },
    "metadata": {
      "type": "object",
      "additionalProperties": true,
      "description": "Optional key-value metadata"
    }
  },
  "additionalProperties": false
}
```

**Protobuf:**

```protobuf
syntax = "proto3";

package company.payments.v2;

option java_package = "com.company.payments.v2";

import "google/protobuf/timestamp.proto";

message TransactionEvent {
  // Unique transaction identifier (UUID format)
  string transaction_id = 1;

  // Customer who initiated the transaction
  string customer_id = 2;

  // Transaction amount in minor currency units (cents)
  int64 amount_minor_units = 3;

  // ISO 4217 currency code
  Currency currency = 4;

  // Timestamp of transaction creation
  google.protobuf.Timestamp created_at = 5;

  // Current transaction status
  TransactionStatus status = 6;

  // Optional metadata
  map<string, string> metadata = 7;
}

enum Currency {
  CURRENCY_UNSPECIFIED = 0;
  USD = 1;
  EUR = 2;
  GBP = 3;
  JPY = 4;
  BRL = 5;
}

enum TransactionStatus {
  STATUS_UNSPECIFIED = 0;
  PENDING = 1;
  PROCESSING = 2;
  COMPLETED = 3;
  FAILED = 4;
  REFUNDED = 5;
}
```

**Avro:**

```json
{
  "type": "record",
  "name": "TransactionEvent",
  "namespace": "com.company.payments.v2",
  "doc": "Contract for transaction events from payments service",
  "fields": [
    {
      "name": "transaction_id",
      "type": "string",
      "doc": "UUID - unique transaction identifier"
    },
    {
      "name": "customer_id",
      "type": "string",
      "doc": "UUID - customer who initiated the transaction"
    },
    {
      "name": "amount_minor_units",
      "type": "long",
      "doc": "Transaction amount in minor currency units"
    },
    {
      "name": "currency",
      "type": {
        "type": "enum",
        "name": "Currency",
        "symbols": ["USD", "EUR", "GBP", "JPY", "BRL"]
      }
    },
    {
      "name": "created_at",
      "type": {
        "type": "long",
        "logicalType": "timestamp-millis"
      }
    },
    {
      "name": "status",
      "type": {
        "type": "enum",
        "name": "TransactionStatus",
        "symbols": ["PENDING", "PROCESSING", "COMPLETED", "FAILED", "REFUNDED"]
      }
    },
    {
      "name": "metadata",
      "type": ["null", {"type": "map", "values": "string"}],
      "default": null
    }
  ]
}
```

### 5.3 Contract Testing in CI/CD

```python
# tests/test_data_contracts.py
"""Data contract validation tests for CI/CD pipeline."""

import json
import pytest
from pathlib import Path
from jsonschema import validate, ValidationError, Draft202012Validator


CONTRACTS_DIR = Path("contracts/")
SAMPLE_DATA_DIR = Path("tests/fixtures/")


def load_contract(name: str) -> dict:
    """Load a contract schema by name."""
    path = CONTRACTS_DIR / f"{name}.json"
    return json.loads(path.read_text())


def load_samples(name: str) -> list[dict]:
    """Load sample data for contract testing."""
    path = SAMPLE_DATA_DIR / f"{name}_samples.json"
    return json.loads(path.read_text())


class TestTransactionContract:
    """Validate transaction events against their contract."""

    @pytest.fixture
    def schema(self):
        return load_contract("transaction_event_v2")

    @pytest.fixture
    def valid_samples(self):
        return load_samples("transaction_valid")

    @pytest.fixture
    def invalid_samples(self):
        return load_samples("transaction_invalid")

    def test_valid_events_pass(self, schema, valid_samples):
        """All valid sample events should pass contract validation."""
        for sample in valid_samples:
            validate(instance=sample, schema=schema)

    def test_invalid_events_fail(self, schema, invalid_samples):
        """All invalid sample events should fail contract validation."""
        for sample in invalid_samples:
            with pytest.raises(ValidationError):
                validate(instance=sample, schema=schema)

    def test_required_fields_enforced(self, schema):
        """Contract should reject events missing required fields."""
        incomplete = {"transaction_id": "abc-123"}
        with pytest.raises(ValidationError) as exc_info:
            validate(instance=incomplete, schema=schema)
        assert "required" in str(exc_info.value.message).lower()

    def test_no_additional_properties(self, schema):
        """Contract should reject unknown fields."""
        with_extra = {
            "transaction_id": "550e8400-e29b-41d4-a716-446655440000",
            "customer_id": "660e8400-e29b-41d4-a716-446655440000",
            "amount": 100.00,
            "currency": "USD",
            "timestamp": "2024-01-15T10:30:00Z",
            "status": "completed",
            "unknown_field": "should_fail",
        }
        with pytest.raises(ValidationError):
            validate(instance=with_extra, schema=schema)

    def test_schema_is_valid_json_schema(self, schema):
        """The contract itself should be a valid JSON Schema."""
        Draft202012Validator.check_schema(schema)
```

### 5.4 Breaking Change Detection

```python
# tools/contract_diff.py
"""Detect breaking changes between contract versions."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ChangeType(Enum):
    BREAKING = "breaking"
    COMPATIBLE = "compatible"
    WARNING = "warning"


@dataclass(frozen=True)
class ContractChange:
    path: str
    change_type: ChangeType
    description: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None


def detect_breaking_changes(old_schema: dict, new_schema: dict) -> list[ContractChange]:
    """Compare two JSON Schema versions and identify breaking changes."""
    changes = []

    # Check for removed required fields (BREAKING)
    old_required = set(old_schema.get("required", []))
    new_required = set(new_schema.get("required", []))

    removed_required = old_required - new_required
    # Removing a required field is compatible (consumers won't break)
    # Adding a required field is BREAKING (existing producers may not send it)
    added_required = new_required - old_required

    for field in added_required:
        changes.append(ContractChange(
            path=f"$.required.{field}",
            change_type=ChangeType.BREAKING,
            description=f"New required field '{field}' added - existing producers may not provide it",
            new_value=field,
        ))

    # Check for removed properties (BREAKING)
    old_props = set(old_schema.get("properties", {}).keys())
    new_props = set(new_schema.get("properties", {}).keys())

    removed_props = old_props - new_props
    for prop in removed_props:
        changes.append(ContractChange(
            path=f"$.properties.{prop}",
            change_type=ChangeType.BREAKING,
            description=f"Property '{prop}' removed - consumers relying on it will break",
            old_value=prop,
        ))

    # Check for type changes (BREAKING)
    for prop in old_props & new_props:
        old_type = old_schema["properties"][prop].get("type")
        new_type = new_schema["properties"][prop].get("type")
        if old_type != new_type:
            changes.append(ContractChange(
                path=f"$.properties.{prop}.type",
                change_type=ChangeType.BREAKING,
                description=f"Type of '{prop}' changed from '{old_type}' to '{new_type}'",
                old_value=old_type,
                new_value=new_type,
            ))

        # Check for enum value removal (BREAKING)
        old_enum = set(old_schema["properties"][prop].get("enum", []))
        new_enum = set(new_schema["properties"][prop].get("enum", []))
        removed_values = old_enum - new_enum
        if removed_values:
            changes.append(ContractChange(
                path=f"$.properties.{prop}.enum",
                change_type=ChangeType.BREAKING,
                description=f"Enum values removed from '{prop}': {removed_values}",
                old_value=str(old_enum),
                new_value=str(new_enum),
            ))

    # Check for narrowed constraints (BREAKING)
    for prop in old_props & new_props:
        old_min = old_schema["properties"][prop].get("minimum")
        new_min = new_schema["properties"][prop].get("minimum")
        if old_min is not None and new_min is not None and new_min > old_min:
            changes.append(ContractChange(
                path=f"$.properties.{prop}.minimum",
                change_type=ChangeType.BREAKING,
                description=f"Minimum for '{prop}' increased from {old_min} to {new_min}",
                old_value=str(old_min),
                new_value=str(new_min),
            ))

    return changes
```

### 5.5 Versioning Strategies

```yaml
# contract_registry.yml
contracts:
  - name: transaction_event
    owner: payments-team
    consumers: [analytics, fraud-detection, reporting]
    versions:
      - version: "1.0.0"
        status: deprecated
        sunset_date: "2024-06-01"
        schema: contracts/transaction_event_v1.json

      - version: "2.0.0"
        status: active
        published_date: "2024-01-15"
        schema: contracts/transaction_event_v2.json
        changelog:
          - "Added metadata field (optional)"
          - "Changed amount from integer to decimal"
          - "Added REFUNDED to status enum"

      - version: "2.1.0"
        status: draft
        schema: contracts/transaction_event_v2.1.json
        changelog:
          - "Added payment_method field (optional)"
          - "Added idempotency_key field (optional)"

    versioning_policy:
      strategy: semantic  # major.minor.patch
      breaking_changes: major_version_bump
      additive_changes: minor_version_bump
      deprecation_notice: 90_days
      max_supported_versions: 2
      migration_guide_required: true
```

### 5.6 Producer/Consumer Contract Negotiation

```yaml
# contract_negotiation.yml
negotiation_process:
  1_proposal:
    initiator: producer | consumer
    artifact: RFC document with proposed schema changes
    review_period: 5_business_days

  2_impact_assessment:
    actions:
      - producer: Run breaking change detection
      - consumers: Assess impact on downstream systems
      - platform_team: Review infrastructure implications

  3_agreement:
    criteria:
      - All affected consumers acknowledge the change
      - Migration path documented
      - Timeline agreed for deprecated version sunset
      - Rollback plan defined

  4_implementation:
    sequence:
      - producer publishes new version alongside old
      - consumers migrate at own pace within window
      - old version sunset after grace period

  5_verification:
    checks:
      - Contract tests pass in CI for both versions
      - No consumer still using deprecated version after sunset
      - Monitoring confirms new version stable
```

---

## 6. Data Observability

Data observability extends traditional application monitoring to data systems, providing visibility into data health without requiring predefined rules for every failure mode.

### 6.1 Key Pillars

| Pillar | What It Measures | Detection Method |
|--------|-----------------|-----------------|
| Freshness | Is data arriving on time? | Timestamp monitoring |
| Volume | Are row counts within expected ranges? | Statistical bounds |
| Schema | Has the structure changed unexpectedly? | DDL monitoring |
| Distribution | Have value patterns shifted? | Statistical tests |
| Lineage | Where did the data come from and go? | Graph analysis |

### 6.2 Commercial Platforms

**Monte Carlo:**
- Automated anomaly detection across all five pillars
- ML-based thresholds (no manual rule setting needed)
- Root cause analysis with lineage integration
- Circuit breaker pattern (stop pipelines on critical anomalies)
- Integrates with Snowflake, BigQuery, Databricks, Redshift

**Elementary:**
- Open-source, dbt-native observability
- Anomaly detection models built into dbt tests
- Schema change tracking
- Lineage visualization
- Self-hosted or Elementary Cloud

**Bigeye:**
- Automated metric collection across warehouse tables
- Freshness, volume, and distribution monitoring
- Data diff for comparing environments
- Custom metric definitions

**Datafold:**
- Data diff as primary differentiator (column-level comparison)
- CI/CD integration for PR-level data impact analysis
- Cross-environment regression testing
- Lineage-aware impact analysis

### 6.3 Open-Source Alternatives

```python
# Elementary dbt integration example
# packages.yml
# packages:
#   - package: elementary-data/elementary
#     version: ">=0.13.0"

# models/staging/_schema.yml (Elementary anomaly tests)
"""
version: 2

models:
  - name: stg_orders
    data_tests:
      - elementary.volume_anomalies:
          timestamp_column: created_at
          where: "status != 'test'"
          time_bucket:
            period: hour
            count: 1
          training_period:
            period: day
            count: 30
          severity: warn

      - elementary.freshness_anomalies:
          timestamp_column: updated_at
          severity: error

      - elementary.all_columns_anomalies:
          timestamp_column: created_at
          where: "status = 'completed'"
          severity: warn

    columns:
      - name: amount
        data_tests:
          - elementary.column_anomalies:
              timestamp_column: created_at
              column_anomalies:
                - null_count
                - null_percent
                - zero_count
                - zero_percent
                - average
                - standard_deviation
                - min
                - max
"""
```

### 6.4 Anomaly Detection Algorithms

```python
"""Data observability anomaly detection implementations."""

import numpy as np
from dataclasses import dataclass
from typing import Optional
from scipy import stats


@dataclass(frozen=True)
class AnomalyResult:
    metric_name: str
    current_value: float
    expected_range: tuple[float, float]
    is_anomaly: bool
    severity: str
    z_score: Optional[float] = None


def z_score_detection(
    values: list[float],
    current: float,
    threshold: float = 3.0,
) -> AnomalyResult:
    """Simple z-score based anomaly detection."""
    arr = np.array(values)
    mean = np.mean(arr)
    std = np.std(arr)

    if std == 0:
        return AnomalyResult(
            metric_name="z_score",
            current_value=current,
            expected_range=(mean, mean),
            is_anomaly=current != mean,
            severity="low",
            z_score=0.0,
        )

    z = (current - mean) / std
    lower = mean - threshold * std
    upper = mean + threshold * std

    is_anomaly = abs(z) > threshold
    severity = "critical" if abs(z) > 5 else "high" if abs(z) > 4 else "medium"

    return AnomalyResult(
        metric_name="z_score",
        current_value=current,
        expected_range=(lower, upper),
        is_anomaly=is_anomaly,
        severity=severity if is_anomaly else "none",
        z_score=z,
    )


def mad_detection(
    values: list[float],
    current: float,
    threshold: float = 3.5,
) -> AnomalyResult:
    """Median Absolute Deviation - robust to outliers in training data."""
    arr = np.array(values)
    median = np.median(arr)
    mad = np.median(np.abs(arr - median))

    # Modified z-score using MAD
    modified_z = 0.6745 * (current - median) / mad if mad > 0 else 0.0
    lower = median - threshold * mad / 0.6745
    upper = median + threshold * mad / 0.6745

    is_anomaly = abs(modified_z) > threshold

    return AnomalyResult(
        metric_name="mad",
        current_value=current,
        expected_range=(lower, upper),
        is_anomaly=is_anomaly,
        severity="high" if is_anomaly else "none",
        z_score=modified_z,
    )


def seasonal_detection(
    values: list[float],
    current: float,
    period: int = 7,
    threshold: float = 3.0,
) -> AnomalyResult:
    """Seasonal decomposition for time-series with weekly patterns."""
    arr = np.array(values)

    if len(arr) < period * 3:
        return z_score_detection(values, current, threshold)

    # Simple seasonal decomposition
    n_periods = len(arr) // period
    seasonal_means = []
    for i in range(period):
        indices = [i + j * period for j in range(n_periods) if i + j * period < len(arr)]
        seasonal_means.append(np.mean(arr[indices]))

    # Current position in season
    current_position = len(arr) % period
    expected = seasonal_means[current_position]
    residuals = []
    for i in range(len(arr)):
        pos = i % period
        residuals.append(arr[i] - seasonal_means[pos])

    residual_std = np.std(residuals)
    current_residual = current - expected
    z = current_residual / residual_std if residual_std > 0 else 0

    lower = expected - threshold * residual_std
    upper = expected + threshold * residual_std
    is_anomaly = abs(z) > threshold

    return AnomalyResult(
        metric_name="seasonal",
        current_value=current,
        expected_range=(lower, upper),
        is_anomaly=is_anomaly,
        severity="high" if is_anomaly else "none",
        z_score=z,
    )


def ks_distribution_drift(
    reference: list[float],
    current: list[float],
    p_threshold: float = 0.01,
) -> dict:
    """Kolmogorov-Smirnov test for distribution drift detection."""
    statistic, p_value = stats.ks_2samp(reference, current)

    return {
        "test": "kolmogorov_smirnov",
        "statistic": statistic,
        "p_value": p_value,
        "is_drift": p_value < p_threshold,
        "severity": (
            "critical" if p_value < 0.001
            else "high" if p_value < 0.01
            else "medium" if p_value < 0.05
            else "none"
        ),
    }
```

### 6.5 Incident Management for Data

```yaml
data_incident_management:
  detection:
    automated:
      - anomaly_detection_alerts
      - dbt_test_failures
      - freshness_sla_breaches
      - pipeline_failures
    manual:
      - user_reported_issues
      - stakeholder_escalation

  severity_classification:
    sev1_critical:
      criteria: "Revenue impacting, regulatory, or customer-facing data corruption"
      response_time: 15_minutes
      notification: pagerduty + slack_critical + email_leadership
      war_room: immediate
    sev2_high:
      criteria: "Analytics/reporting incorrect, operational decisions affected"
      response_time: 1_hour
      notification: slack_data_alerts + email_team
    sev3_medium:
      criteria: "Non-critical degradation, single downstream affected"
      response_time: 4_hours
      notification: slack_data_alerts
    sev4_low:
      criteria: "Cosmetic, optional fields, edge cases"
      response_time: next_business_day
      notification: ticket_created

  response_workflow:
    1_detect: "Alert fires or issue reported"
    2_acknowledge: "On-call engineer acknowledges within response_time"
    3_triage: "Classify severity, identify blast radius via lineage"
    4_communicate: "Notify affected consumers with ETA"
    5_mitigate: "Quarantine bad data, switch to fallback, or pause pipeline"
    6_resolve: "Fix root cause, validate fix, restore normal operation"
    7_postmortem: "Document timeline, root cause, action items within 48h"

  communication_templates:
    incident_start: |
      DATA INCIDENT - {severity}
      Affected: {tables/pipelines}
      Impact: {description}
      Status: Investigating
      ETA: {estimate}
      Point of Contact: {oncall}
    
    incident_update: |
      UPDATE - {incident_id}
      Status: {status}
      Progress: {description}
      Revised ETA: {estimate}
    
    incident_resolved: |
      RESOLVED - {incident_id}
      Duration: {duration}
      Root Cause: {brief_rca}
      Postmortem: {link}
```

---

## 7. Data Validation Patterns

### 7.1 Input Validation

**Schema Enforcement:**

```python
"""Input validation layer for data pipelines."""

from dataclasses import dataclass
from typing import Any, Callable
import json
from datetime import datetime, date


@dataclass(frozen=True)
class ValidationError:
    field: str
    value: Any
    rule: str
    message: str


@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool
    errors: tuple[ValidationError, ...]
    record: dict


def validate_record(record: dict, schema: dict) -> ValidationResult:
    """Validate a single record against a schema definition."""
    errors = []

    # Check required fields
    for field in schema.get("required", []):
        if field not in record or record[field] is None:
            errors.append(ValidationError(
                field=field,
                value=None,
                rule="required",
                message=f"Required field '{field}' is missing or null",
            ))

    # Check field types and constraints
    for field, constraints in schema.get("properties", {}).items():
        if field not in record or record[field] is None:
            continue

        value = record[field]

        # Type validation
        expected_type = constraints.get("type")
        if expected_type and not _check_type(value, expected_type):
            errors.append(ValidationError(
                field=field,
                value=value,
                rule="type",
                message=f"Expected type '{expected_type}', got '{type(value).__name__}'",
            ))
            continue

        # Range validation
        if "minimum" in constraints and value < constraints["minimum"]:
            errors.append(ValidationError(
                field=field,
                value=value,
                rule="minimum",
                message=f"Value {value} below minimum {constraints['minimum']}",
            ))

        if "maximum" in constraints and value > constraints["maximum"]:
            errors.append(ValidationError(
                field=field,
                value=value,
                rule="maximum",
                message=f"Value {value} above maximum {constraints['maximum']}",
            ))

        # Enum validation
        if "enum" in constraints and value not in constraints["enum"]:
            errors.append(ValidationError(
                field=field,
                value=value,
                rule="enum",
                message=f"Value '{value}' not in allowed set: {constraints['enum']}",
            ))

        # Pattern validation
        if "pattern" in constraints:
            import re
            if not re.match(constraints["pattern"], str(value)):
                errors.append(ValidationError(
                    field=field,
                    value=value,
                    rule="pattern",
                    message=f"Value does not match pattern: {constraints['pattern']}",
                ))

    # Check additionalProperties
    if not schema.get("additionalProperties", True):
        known_fields = set(schema.get("properties", {}).keys())
        extra_fields = set(record.keys()) - known_fields
        for field in extra_fields:
            errors.append(ValidationError(
                field=field,
                value=record[field],
                rule="additionalProperties",
                message=f"Unexpected field '{field}' not allowed by schema",
            ))

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=tuple(errors),
        record=record,
    )


def _check_type(value: Any, expected: str) -> bool:
    """Check if value matches expected JSON Schema type."""
    type_map = {
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
        "array": list,
        "object": dict,
    }
    expected_types = type_map.get(expected)
    if expected_types is None:
        return True
    return isinstance(value, expected_types)
```

### 7.2 Cross-Dataset Validation

```sql
-- Referential integrity validation across datasets
-- Check that all foreign keys in fact table resolve

WITH unresolved_customers AS (
    SELECT DISTINCT f.customer_id
    FROM fact_orders f
    LEFT JOIN dim_customers d ON f.customer_id = d.customer_id
    WHERE d.customer_id IS NULL
      AND f.customer_id IS NOT NULL
),
unresolved_products AS (
    SELECT DISTINCT f.product_id
    FROM fact_order_lines f
    LEFT JOIN dim_products d ON f.product_id = d.product_id
    WHERE d.product_id IS NULL
      AND f.product_id IS NOT NULL
),
reconciliation AS (
    -- Reconcile totals between source and warehouse
    SELECT
        'orders' AS entity,
        (SELECT COUNT(*) FROM source.orders WHERE created_at >= CURRENT_DATE - 1) AS source_count,
        (SELECT COUNT(*) FROM fact_orders WHERE order_date >= CURRENT_DATE - 1) AS warehouse_count,
        (SELECT SUM(total) FROM source.orders WHERE created_at >= CURRENT_DATE - 1) AS source_total,
        (SELECT SUM(order_total) FROM fact_orders WHERE order_date >= CURRENT_DATE - 1) AS warehouse_total
)
SELECT
    'unresolved_customers' AS check_name,
    COUNT(*) AS violation_count,
    CASE WHEN COUNT(*) > 0 THEN 'FAIL' ELSE 'PASS' END AS status
FROM unresolved_customers
UNION ALL
SELECT
    'unresolved_products',
    COUNT(*),
    CASE WHEN COUNT(*) > 0 THEN 'FAIL' ELSE 'PASS' END
FROM unresolved_products
UNION ALL
SELECT
    'count_reconciliation',
    ABS(source_count - warehouse_count),
    CASE WHEN ABS(source_count - warehouse_count) > 0 THEN 'FAIL' ELSE 'PASS' END
FROM reconciliation
UNION ALL
SELECT
    'total_reconciliation',
    CASE WHEN ABS(source_total - warehouse_total) > 0.01 THEN 1 ELSE 0 END,
    CASE WHEN ABS(source_total - warehouse_total) > 0.01 THEN 'FAIL' ELSE 'PASS' END
FROM reconciliation;
```

### 7.3 Temporal Validation

```sql
-- Monotonicity check: timestamps should never go backwards
WITH ordered_events AS (
    SELECT
        event_id,
        event_timestamp,
        LAG(event_timestamp) OVER (PARTITION BY session_id ORDER BY sequence_number) AS prev_timestamp,
        sequence_number
    FROM event_stream
)
SELECT
    event_id,
    event_timestamp,
    prev_timestamp,
    sequence_number
FROM ordered_events
WHERE event_timestamp < prev_timestamp;

-- Gap detection: identify missing time periods
WITH time_series AS (
    SELECT
        DATE_TRUNC('hour', event_timestamp) AS hour_bucket,
        COUNT(*) AS event_count
    FROM events
    WHERE event_timestamp >= CURRENT_TIMESTAMP - INTERVAL '7 days'
    GROUP BY 1
),
expected_hours AS (
    SELECT generate_series(
        DATE_TRUNC('hour', CURRENT_TIMESTAMP - INTERVAL '7 days'),
        DATE_TRUNC('hour', CURRENT_TIMESTAMP),
        INTERVAL '1 hour'
    ) AS expected_hour
)
SELECT
    e.expected_hour,
    COALESCE(t.event_count, 0) AS actual_count,
    CASE WHEN t.event_count IS NULL THEN 'GAP' ELSE 'OK' END AS status
FROM expected_hours e
LEFT JOIN time_series t ON e.expected_hour = t.hour_bucket
WHERE t.event_count IS NULL
   OR t.event_count = 0
ORDER BY e.expected_hour;

-- Late-arriving data detection
SELECT
    DATE(event_timestamp) AS event_date,
    DATE(ingested_at) AS ingestion_date,
    EXTRACT(EPOCH FROM (ingested_at - event_timestamp)) / 3600 AS hours_late,
    COUNT(*) AS late_records
FROM events
WHERE ingested_at - event_timestamp > INTERVAL '24 hours'
GROUP BY 1, 2
ORDER BY hours_late DESC;
```

### 7.4 Statistical Validation

```python
"""Statistical validation for distribution drift and outlier detection."""

import numpy as np
from scipy import stats
from typing import NamedTuple


class DriftResult(NamedTuple):
    test_name: str
    statistic: float
    p_value: float
    is_drift: bool
    threshold: float


def chi_squared_categorical_drift(
    reference_counts: dict[str, int],
    current_counts: dict[str, int],
    p_threshold: float = 0.01,
) -> DriftResult:
    """Chi-squared test for categorical distribution drift."""
    all_categories = sorted(set(reference_counts.keys()) | set(current_counts.keys()))

    observed = np.array([current_counts.get(c, 0) for c in all_categories])
    expected_raw = np.array([reference_counts.get(c, 0) for c in all_categories])

    # Normalize expected to match observed total
    total_observed = observed.sum()
    total_expected = expected_raw.sum()
    expected = expected_raw * (total_observed / total_expected) if total_expected > 0 else expected_raw

    # Filter out zero-expected categories to avoid division by zero
    mask = expected > 0
    if mask.sum() < 2:
        return DriftResult("chi_squared", 0.0, 1.0, False, p_threshold)

    stat, p_value = stats.chisquare(observed[mask], expected[mask])

    return DriftResult(
        test_name="chi_squared",
        statistic=stat,
        p_value=p_value,
        is_drift=p_value < p_threshold,
        threshold=p_threshold,
    )


def population_stability_index(
    reference: np.ndarray,
    current: np.ndarray,
    n_bins: int = 10,
) -> dict:
    """
    Calculate Population Stability Index (PSI).
    PSI < 0.1: no significant change
    PSI 0.1-0.25: moderate change, investigation recommended
    PSI > 0.25: significant change, action required
    """
    # Create bins from reference distribution
    bin_edges = np.percentile(reference, np.linspace(0, 100, n_bins + 1))
    bin_edges[0] = -np.inf
    bin_edges[-1] = np.inf

    ref_counts, _ = np.histogram(reference, bins=bin_edges)
    cur_counts, _ = np.histogram(current, bins=bin_edges)

    # Convert to proportions (avoid zeros)
    ref_pct = np.clip(ref_counts / ref_counts.sum(), 1e-6, None)
    cur_pct = np.clip(cur_counts / cur_counts.sum(), 1e-6, None)

    # PSI formula
    psi_values = (cur_pct - ref_pct) * np.log(cur_pct / ref_pct)
    psi_total = np.sum(psi_values)

    return {
        "psi": psi_total,
        "interpretation": (
            "no_change" if psi_total < 0.1
            else "moderate_change" if psi_total < 0.25
            else "significant_change"
        ),
        "bin_psi": psi_values.tolist(),
        "action_required": psi_total >= 0.25,
    }


def isolation_forest_outliers(
    data: np.ndarray,
    contamination: float = 0.01,
) -> dict:
    """Detect outliers using Isolation Forest."""
    from sklearn.ensemble import IsolationForest

    model = IsolationForest(
        contamination=contamination,
        random_state=42,
        n_estimators=100,
    )

    # Reshape for sklearn if 1D
    if data.ndim == 1:
        data = data.reshape(-1, 1)

    predictions = model.fit_predict(data)
    scores = model.decision_function(data)

    outlier_mask = predictions == -1
    outlier_indices = np.where(outlier_mask)[0]

    return {
        "n_outliers": int(outlier_mask.sum()),
        "outlier_rate": float(outlier_mask.mean()),
        "outlier_indices": outlier_indices.tolist(),
        "anomaly_scores": scores[outlier_mask].tolist(),
    }
```

---

## 8. Data Profiling

### 8.1 Automated Profiling Tools

**ydata-profiling (formerly pandas-profiling):**

```python
"""Data profiling with ydata-profiling for initial data understanding."""

import pandas as pd
from ydata_profiling import ProfileReport


def profile_dataset(
    df: pd.DataFrame,
    title: str = "Data Profile Report",
    output_path: str = "profile_report.html",
    minimal: bool = False,
) -> ProfileReport:
    """Generate a comprehensive data profile report."""
    profile = ProfileReport(
        df,
        title=title,
        minimal=minimal,
        explorative=True,
        correlations={
            "auto": {"calculate": True},
            "pearson": {"calculate": True},
            "spearman": {"calculate": True},
        },
        missing_diagrams={
            "bar": True,
            "matrix": True,
            "heatmap": True,
        },
    )
    profile.to_file(output_path)
    return profile


def profile_to_expectations(profile: ProfileReport) -> list[dict]:
    """Convert profiling results to Great Expectations expectations."""
    description = profile.get_description()
    expectations = []

    for col_name, col_stats in description.variables.items():
        col_type = col_stats.get("type")

        # Not null expectation based on observed null rate
        null_pct = col_stats.get("p_missing", 0)
        if null_pct == 0:
            expectations.append({
                "expectation_type": "expect_column_values_to_not_be_null",
                "kwargs": {"column": col_name},
            })

        # Uniqueness
        if col_stats.get("is_unique", False):
            expectations.append({
                "expectation_type": "expect_column_values_to_be_unique",
                "kwargs": {"column": col_name},
            })

        # Numeric range
        if col_type in ("Numeric", "Real"):
            expectations.append({
                "expectation_type": "expect_column_values_to_be_between",
                "kwargs": {
                    "column": col_name,
                    "min_value": col_stats.get("min"),
                    "max_value": col_stats.get("max"),
                },
            })

            # Mean stability
            mean_val = col_stats.get("mean")
            std_val = col_stats.get("std")
            if mean_val is not None and std_val is not None:
                expectations.append({
                    "expectation_type": "expect_column_mean_to_be_between",
                    "kwargs": {
                        "column": col_name,
                        "min_value": mean_val - 2 * std_val,
                        "max_value": mean_val + 2 * std_val,
                    },
                })

        # Categorical
        if col_type == "Categorical":
            n_distinct = col_stats.get("n_distinct", 0)
            if n_distinct <= 20:
                value_counts = col_stats.get("value_counts_index_sorted")
                if value_counts:
                    expectations.append({
                        "expectation_type": "expect_column_values_to_be_in_set",
                        "kwargs": {
                            "column": col_name,
                            "value_set": list(value_counts.keys()),
                        },
                    })

    return expectations
```

**whylogs:**

```python
"""Lightweight data profiling with whylogs for production monitoring."""

import whylogs as why
from whylogs.core import DatasetProfileView
from whylogs.core.constraints import ConstraintsBuilder
from whylogs.core.constraints.factories import (
    greater_than_number,
    smaller_than_number,
    no_missing_values,
    is_in_range,
    null_percentage_below,
)
import pandas as pd


def create_whylogs_profile(df: pd.DataFrame, dataset_name: str) -> DatasetProfileView:
    """Create a whylogs profile for a DataFrame."""
    results = why.log(df)
    profile = results.profile()
    view = profile.view()
    return view


def build_constraints_from_profile(
    reference_profile: DatasetProfileView,
    columns_config: dict,
) -> ConstraintsBuilder:
    """Build validation constraints from a reference profile."""
    builder = ConstraintsBuilder(dataset_profile_view=reference_profile)

    for col_name, config in columns_config.items():
        if config.get("not_null"):
            builder.add_constraint(no_missing_values(col_name))

        if "null_pct_max" in config:
            builder.add_constraint(
                null_percentage_below(col_name, config["null_pct_max"])
            )

        if "min" in config and "max" in config:
            builder.add_constraint(
                is_in_range(col_name, config["min"], config["max"])
            )

    return builder


def compare_profiles(
    reference: DatasetProfileView,
    current: DatasetProfileView,
) -> dict:
    """Compare two profiles for drift detection."""
    ref_columns = reference.get_columns()
    cur_columns = current.get_columns()

    drift_report = {}
    for col_name in ref_columns:
        if col_name not in cur_columns:
            drift_report[col_name] = {"status": "MISSING_IN_CURRENT"}
            continue

        ref_summary = ref_columns[col_name].to_summary_dict()
        cur_summary = cur_columns[col_name].to_summary_dict()

        # Compare key metrics
        comparisons = {}
        for metric in ["distribution/mean", "distribution/stddev", "counts/null"]:
            ref_val = ref_summary.get(metric)
            cur_val = cur_summary.get(metric)
            if ref_val is not None and cur_val is not None and ref_val != 0:
                pct_change = abs(cur_val - ref_val) / abs(ref_val) * 100
                comparisons[metric] = {
                    "reference": ref_val,
                    "current": cur_val,
                    "pct_change": pct_change,
                    "drift": pct_change > 20,  # 20% threshold
                }

        drift_report[col_name] = comparisons

    return drift_report
```

### 8.2 Profiling at Scale (Spark-Based)

```python
"""Spark-based data profiling for large datasets."""

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import StructType
from typing import Dict, Any


def spark_profile_table(
    spark: SparkSession,
    df: DataFrame,
    sample_fraction: float = 1.0,
) -> Dict[str, Any]:
    """Profile a Spark DataFrame with key statistics."""

    if sample_fraction < 1.0:
        df = df.sample(fraction=sample_fraction, seed=42)

    # Cache for multiple passes
    df.cache()

    row_count = df.count()
    col_count = len(df.columns)

    profile = {
        "table_stats": {
            "row_count": row_count,
            "column_count": col_count,
            "size_bytes": df.rdd.map(lambda r: len(str(r))).sum(),
        },
        "columns": {},
    }

    for col_name in df.columns:
        col_type = str(df.schema[col_name].dataType)

        # Basic stats available for all types
        null_count = df.filter(F.col(col_name).isNull()).count()
        distinct_count = df.select(col_name).distinct().count()

        col_profile = {
            "type": col_type,
            "null_count": null_count,
            "null_rate": null_count / row_count if row_count > 0 else 0,
            "distinct_count": distinct_count,
            "uniqueness": distinct_count / row_count if row_count > 0 else 0,
        }

        # Numeric-specific stats
        if col_type in ("IntegerType", "LongType", "DoubleType", "FloatType", "DecimalType"):
            numeric_stats = df.select(
                F.min(col_name).alias("min"),
                F.max(col_name).alias("max"),
                F.mean(col_name).alias("mean"),
                F.stddev(col_name).alias("stddev"),
                F.expr(f"percentile({col_name}, 0.25)").alias("p25"),
                F.expr(f"percentile({col_name}, 0.50)").alias("p50"),
                F.expr(f"percentile({col_name}, 0.75)").alias("p75"),
                F.expr(f"percentile({col_name}, 0.95)").alias("p95"),
                F.expr(f"percentile({col_name}, 0.99)").alias("p99"),
            ).collect()[0]

            col_profile.update({
                "min": numeric_stats["min"],
                "max": numeric_stats["max"],
                "mean": numeric_stats["mean"],
                "stddev": numeric_stats["stddev"],
                "percentiles": {
                    "p25": numeric_stats["p25"],
                    "p50": numeric_stats["p50"],
                    "p75": numeric_stats["p75"],
                    "p95": numeric_stats["p95"],
                    "p99": numeric_stats["p99"],
                },
                "zero_count": df.filter(F.col(col_name) == 0).count(),
                "negative_count": df.filter(F.col(col_name) < 0).count(),
            })

        # String-specific stats
        elif col_type == "StringType":
            string_stats = df.filter(F.col(col_name).isNotNull()).select(
                F.min(F.length(col_name)).alias("min_length"),
                F.max(F.length(col_name)).alias("max_length"),
                F.mean(F.length(col_name)).alias("avg_length"),
            ).collect()[0]

            col_profile.update({
                "min_length": string_stats["min_length"],
                "max_length": string_stats["max_length"],
                "avg_length": string_stats["avg_length"],
                "empty_count": df.filter(
                    (F.col(col_name) == "") | (F.col(col_name).isNull())
                ).count(),
            })

            # Top values for low-cardinality columns
            if distinct_count <= 100:
                top_values = (
                    df.filter(F.col(col_name).isNotNull())
                    .groupBy(col_name)
                    .count()
                    .orderBy(F.desc("count"))
                    .limit(20)
                    .collect()
                )
                col_profile["top_values"] = {
                    row[col_name]: row["count"] for row in top_values
                }

        profile["columns"][col_name] = col_profile

    df.unpersist()
    return profile
```

### 8.3 Profiling Metrics Summary

| Category | Metric | Purpose |
|----------|--------|---------|
| Cardinality | distinct_count, uniqueness_ratio | Identify keys, flags, categories |
| Distribution | mean, stddev, percentiles, skewness, kurtosis | Understand value spread |
| Null Analysis | null_count, null_rate, null_pattern | Assess completeness |
| Pattern Matching | regex_match_rate, format_distribution | Detect format issues |
| Temporal | min_date, max_date, gaps, frequency | Validate time coverage |
| Correlation | pearson, spearman, cramers_v | Find relationships |
| Outliers | iqr_outliers, zscore_outliers | Identify extreme values |

### 8.4 Auto-Generating Expectations from Profiles

```python
"""Generate GX expectations automatically from profiling results."""

from typing import Any


def auto_generate_suite(
    profile: dict[str, Any],
    strictness: str = "moderate",
) -> list[dict]:
    """
    Generate expectations from a profiling result.

    strictness levels:
      - strict: tight bounds, low tolerance
      - moderate: reasonable margins
      - loose: wide bounds, only catch extreme deviations
    """
    margin_map = {"strict": 0.05, "moderate": 0.20, "loose": 0.50}
    margin = margin_map.get(strictness, 0.20)

    expectations = []

    # Table-level expectations
    row_count = profile["table_stats"]["row_count"]
    expectations.append({
        "expectation_type": "expect_table_row_count_to_be_between",
        "kwargs": {
            "min_value": int(row_count * (1 - margin)),
            "max_value": int(row_count * (1 + margin)),
        },
    })

    # Column-level expectations
    for col_name, col_stats in profile["columns"].items():
        # Null rate expectations
        null_rate = col_stats.get("null_rate", 0)
        if null_rate == 0:
            expectations.append({
                "expectation_type": "expect_column_values_to_not_be_null",
                "kwargs": {"column": col_name},
            })
        elif null_rate < 0.01:
            expectations.append({
                "expectation_type": "expect_column_values_to_not_be_null",
                "kwargs": {"column": col_name, "mostly": 0.99},
            })

        # Uniqueness expectations
        uniqueness = col_stats.get("uniqueness", 0)
        if uniqueness == 1.0:
            expectations.append({
                "expectation_type": "expect_column_values_to_be_unique",
                "kwargs": {"column": col_name},
            })

        # Numeric column expectations
        if "mean" in col_stats:
            mean_val = col_stats["mean"]
            std_val = col_stats.get("stddev", 0)
            min_val = col_stats.get("min")
            max_val = col_stats.get("max")

            # Value range
            if min_val is not None and max_val is not None:
                range_margin = (max_val - min_val) * margin
                expectations.append({
                    "expectation_type": "expect_column_values_to_be_between",
                    "kwargs": {
                        "column": col_name,
                        "min_value": min_val - range_margin,
                        "max_value": max_val + range_margin,
                    },
                })

            # Mean stability
            if mean_val is not None and std_val is not None and std_val > 0:
                expectations.append({
                    "expectation_type": "expect_column_mean_to_be_between",
                    "kwargs": {
                        "column": col_name,
                        "min_value": mean_val - (2 + margin) * std_val,
                        "max_value": mean_val + (2 + margin) * std_val,
                    },
                })

        # Categorical column expectations
        if "top_values" in col_stats:
            distinct = col_stats.get("distinct_count", 0)
            if distinct <= 50:
                expectations.append({
                    "expectation_type": "expect_column_values_to_be_in_set",
                    "kwargs": {
                        "column": col_name,
                        "value_set": list(col_stats["top_values"].keys()),
                    },
                })

    return expectations
```

---

## 9. Remediation and Root Cause

### 9.1 Data Quality Issue Classification

```yaml
issue_classification:
  categories:
    schema_change:
      description: "Source system altered schema without notice"
      indicators:
        - new_columns_appeared
        - columns_removed
        - type_changed
      typical_impact: pipeline_failure
      typical_rca: source_system_deployment

    data_drift:
      description: "Statistical distribution shifted beyond normal variation"
      indicators:
        - mean_shift
        - variance_change
        - new_category_values
      typical_impact: model_accuracy_degradation
      typical_rca: business_change_or_upstream_logic

    completeness_degradation:
      description: "Increase in null/missing values"
      indicators:
        - null_rate_spike
        - row_count_drop
        - missing_partitions
      typical_impact: partial_data_downstream
      typical_rca: source_system_issue_or_extraction_bug

    timeliness_violation:
      description: "Data arriving late or not at all"
      indicators:
        - freshness_sla_breach
        - pipeline_timeout
        - no_new_partitions
      typical_impact: stale_analytics_and_reports
      typical_rca: infrastructure_or_dependency_failure

    duplicate_injection:
      description: "Unexpected duplicate records appearing"
      indicators:
        - uniqueness_violation
        - row_count_spike
        - key_collision
      typical_impact: inflated_metrics
      typical_rca: retry_logic_or_idempotency_failure

    referential_integrity_break:
      description: "Foreign key relationships violated"
      indicators:
        - orphaned_records
        - unresolvable_references
        - cascade_failures
      typical_impact: join_failures_and_null_enrichment
      typical_rca: load_ordering_or_partial_source_sync
```

### 9.2 Impact Assessment

```python
"""Data quality impact assessment framework."""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass(frozen=True)
class ImpactAssessment:
    issue_id: str
    detected_at: datetime
    affected_tables: tuple[str, ...]
    downstream_consumers: tuple[str, ...]
    estimated_records_affected: int
    revenue_impact: Optional[float]
    regulatory_exposure: bool
    customer_facing: bool
    severity: str
    blast_radius: str


def assess_impact(
    issue_type: str,
    affected_table: str,
    lineage_graph: dict,
    table_metadata: dict,
) -> ImpactAssessment:
    """Assess the downstream impact of a data quality issue."""

    # Traverse lineage to find all downstream tables
    downstream = _get_downstream_tables(affected_table, lineage_graph)

    # Identify consumers (dashboards, ML models, APIs, reports)
    consumers = _get_consumers(downstream, table_metadata)

    # Check for regulatory tables
    regulatory = any(
        table_metadata.get(t, {}).get("contains_pii", False) or
        table_metadata.get(t, {}).get("regulatory_scope", False)
        for t in [affected_table] + downstream
    )

    # Check for customer-facing exposure
    customer_facing = any(
        table_metadata.get(t, {}).get("serves_api", False) or
        table_metadata.get(t, {}).get("customer_dashboard", False)
        for t in [affected_table] + downstream
    )

    # Determine severity
    severity = _calculate_severity(
        n_downstream=len(downstream),
        regulatory=regulatory,
        customer_facing=customer_facing,
        issue_type=issue_type,
    )

    # Determine blast radius
    blast_radius = (
        "critical" if len(downstream) > 20 or regulatory
        else "high" if len(downstream) > 10 or customer_facing
        else "medium" if len(downstream) > 3
        else "low"
    )

    return ImpactAssessment(
        issue_id=f"DQ-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        detected_at=datetime.utcnow(),
        affected_tables=tuple([affected_table] + downstream),
        downstream_consumers=tuple(consumers),
        estimated_records_affected=0,  # populated by caller
        revenue_impact=None,
        regulatory_exposure=regulatory,
        customer_facing=customer_facing,
        severity=severity,
        blast_radius=blast_radius,
    )


def _get_downstream_tables(table: str, lineage: dict) -> list[str]:
    """BFS traversal of lineage graph to find all downstream."""
    visited = set()
    queue = lineage.get(table, {}).get("downstream", [])
    result = []

    while queue:
        current = queue.pop(0)
        if current not in visited:
            visited.add(current)
            result.append(current)
            queue.extend(lineage.get(current, {}).get("downstream", []))

    return result


def _get_consumers(tables: list[str], metadata: dict) -> list[str]:
    """Identify end consumers of affected tables."""
    consumers = []
    for table in tables:
        meta = metadata.get(table, {})
        consumers.extend(meta.get("dashboards", []))
        consumers.extend(meta.get("ml_models", []))
        consumers.extend(meta.get("api_endpoints", []))
        consumers.extend(meta.get("reports", []))
    return list(set(consumers))


def _calculate_severity(
    n_downstream: int,
    regulatory: bool,
    customer_facing: bool,
    issue_type: str,
) -> str:
    """Calculate issue severity based on impact factors."""
    if regulatory:
        return "critical"
    if customer_facing and issue_type in ("completeness_degradation", "data_drift"):
        return "critical"
    if n_downstream > 10:
        return "high"
    if customer_facing:
        return "high"
    if n_downstream > 3:
        return "medium"
    return "low"
```

### 9.3 Root Cause Analysis

```yaml
root_cause_analysis:
  investigation_framework:
    step_1_timeline:
      action: "Establish when the issue started"
      tools:
        - query_monitoring_metrics_history
        - check_pipeline_run_logs
        - compare_profile_snapshots
      output: "timestamp range of issue onset"

    step_2_scope:
      action: "Determine what is affected"
      tools:
        - run_lineage_traversal
        - check_dependent_pipelines
        - query_consumer_error_rates
      output: "blast radius and affected consumers"

    step_3_correlation:
      action: "Correlate with system events"
      tools:
        - check_source_system_deployments
        - check_infrastructure_incidents
        - check_schema_registry_changes
        - check_pipeline_configuration_changes
      output: "candidate root causes"

    step_4_verification:
      action: "Verify root cause hypothesis"
      tools:
        - reproduce_with_specific_data
        - check_source_system_logs
        - compare_before_after_data
      output: "confirmed root cause"

  common_root_causes:
    source_system_changes:
      patterns:
        - "New column added but not propagated"
        - "Enum value added to source"
        - "Date format changed"
        - "API response structure modified"
        - "Source system timezone change"
      detection:
        - schema_diff_monitoring
        - contract_validation_in_ingestion
      prevention:
        - data_contracts_with_producer
        - schema_registry_enforcement
        - change_notification_subscription

    pipeline_bugs:
      patterns:
        - "Incorrect join condition introduced"
        - "Filter predicate wrong after refactor"
        - "Type casting loses precision"
        - "Null handling edge case"
        - "Timezone conversion error"
      detection:
        - dbt_test_failures
        - reconciliation_checks
        - row_count_anomalies
      prevention:
        - comprehensive_dbt_tests
        - pr_review_with_data_diff
        - staging_environment_validation

    infrastructure_issues:
      patterns:
        - "Disk full causing partial writes"
        - "Network timeout during extraction"
        - "Memory OOM killing Spark executor"
        - "Clock skew between systems"
        - "Connection pool exhaustion"
      detection:
        - infrastructure_monitoring
        - pipeline_error_classification
        - partial_load_detection
      prevention:
        - resource_monitoring_and_alerting
        - retry_with_idempotency
        - infrastructure_capacity_planning
```

### 9.4 Automated Remediation

```python
"""Automated data quality remediation patterns."""

from dataclasses import dataclass
from typing import Optional, Callable
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class RemediationAction(Enum):
    QUARANTINE = "quarantine"
    DEFAULT_FILL = "default_fill"
    REPROCESS = "reprocess"
    NOTIFY_AND_SKIP = "notify_and_skip"
    CIRCUIT_BREAK = "circuit_break"
    FALLBACK_SOURCE = "fallback_source"


@dataclass(frozen=True)
class RemediationRule:
    issue_type: str
    severity: str
    action: RemediationAction
    config: dict


REMEDIATION_RULES = [
    RemediationRule(
        issue_type="null_rate_spike",
        severity="high",
        action=RemediationAction.QUARANTINE,
        config={
            "quarantine_table": "dq_quarantine.null_violations",
            "max_quarantine_pct": 5.0,
            "escalate_if_exceeds": True,
        },
    ),
    RemediationRule(
        issue_type="duplicate_injection",
        severity="medium",
        action=RemediationAction.REPROCESS,
        config={
            "dedup_strategy": "keep_latest",
            "dedup_keys": ["transaction_id"],
            "max_retries": 3,
        },
    ),
    RemediationRule(
        issue_type="freshness_breach",
        severity="critical",
        action=RemediationAction.CIRCUIT_BREAK,
        config={
            "pause_downstream_pipelines": True,
            "notification_channels": ["pagerduty", "slack_critical"],
            "fallback_to_cache": True,
        },
    ),
    RemediationRule(
        issue_type="schema_change",
        severity="critical",
        action=RemediationAction.CIRCUIT_BREAK,
        config={
            "pause_ingestion": True,
            "notification_channels": ["slack_data_eng", "email_data_owner"],
            "require_manual_approval": True,
        },
    ),
]


class DataQualityRemediator:
    """Executes automated remediation based on configured rules."""

    def __init__(self, rules: list[RemediationRule]):
        self._rules = {(r.issue_type, r.severity): r for r in rules}

    def remediate(self, issue_type: str, severity: str, context: dict) -> dict:
        """Execute appropriate remediation for a given issue."""
        rule = self._rules.get((issue_type, severity))

        if rule is None:
            logger.warning(f"No remediation rule for {issue_type}/{severity}")
            return {"action": "manual_intervention_required", "reason": "no_matching_rule"}

        handler = self._get_handler(rule.action)
        result = handler(rule, context)

        logger.info(
            f"Remediation executed: issue={issue_type}, "
            f"severity={severity}, action={rule.action.value}, "
            f"result={result.get('status')}"
        )

        return result

    def _get_handler(self, action: RemediationAction) -> Callable:
        handlers = {
            RemediationAction.QUARANTINE: self._handle_quarantine,
            RemediationAction.DEFAULT_FILL: self._handle_default_fill,
            RemediationAction.REPROCESS: self._handle_reprocess,
            RemediationAction.NOTIFY_AND_SKIP: self._handle_notify_skip,
            RemediationAction.CIRCUIT_BREAK: self._handle_circuit_break,
            RemediationAction.FALLBACK_SOURCE: self._handle_fallback,
        }
        return handlers[action]

    def _handle_quarantine(self, rule: RemediationRule, context: dict) -> dict:
        """Move bad records to quarantine table for manual review."""
        bad_records = context.get("bad_records", [])
        total_records = context.get("total_records", 0)
        quarantine_pct = (len(bad_records) / total_records * 100) if total_records > 0 else 0

        if quarantine_pct > rule.config["max_quarantine_pct"]:
            return {
                "status": "escalated",
                "reason": f"Quarantine rate {quarantine_pct:.1f}% exceeds max {rule.config['max_quarantine_pct']}%",
                "action": "circuit_break",
            }

        return {
            "status": "quarantined",
            "records_quarantined": len(bad_records),
            "quarantine_table": rule.config["quarantine_table"],
            "quarantine_rate_pct": quarantine_pct,
        }

    def _handle_default_fill(self, rule: RemediationRule, context: dict) -> dict:
        """Fill missing values with configured defaults."""
        return {
            "status": "filled",
            "records_filled": context.get("null_count", 0),
            "fill_strategy": rule.config.get("strategy", "static_default"),
        }

    def _handle_reprocess(self, rule: RemediationRule, context: dict) -> dict:
        """Trigger reprocessing of affected partition/batch."""
        return {
            "status": "reprocessing",
            "partition": context.get("partition"),
            "dedup_strategy": rule.config.get("dedup_strategy"),
        }

    def _handle_notify_skip(self, rule: RemediationRule, context: dict) -> dict:
        """Notify stakeholders and skip bad records."""
        return {
            "status": "skipped_with_notification",
            "records_skipped": context.get("bad_record_count", 0),
            "notified": rule.config.get("notification_channels", []),
        }

    def _handle_circuit_break(self, rule: RemediationRule, context: dict) -> dict:
        """Stop pipeline and alert on-call."""
        return {
            "status": "circuit_broken",
            "pipelines_paused": rule.config.get("pause_downstream_pipelines", False),
            "requires_manual_approval": rule.config.get("require_manual_approval", False),
            "notified": rule.config.get("notification_channels", []),
        }

    def _handle_fallback(self, rule: RemediationRule, context: dict) -> dict:
        """Switch to fallback data source."""
        return {
            "status": "fallback_activated",
            "fallback_source": rule.config.get("fallback_source"),
            "cache_ttl": rule.config.get("cache_ttl_minutes"),
        }
```

### 9.5 Feedback Loops to Source Systems

```yaml
feedback_loop_architecture:
  automated_notifications:
    trigger: dq_issue_detected_with_source_attribution
    channels:
      - source_team_slack_channel
      - source_team_jira_board
      - shared_dq_dashboard
    content:
      - issue_type_and_severity
      - affected_records_sample
      - detection_timestamp
      - downstream_impact_summary
      - suggested_fix

  escalation_path:
    level_1: "Automated notification to source team"
    level_2: "Follow-up if no acknowledgment in 4h"
    level_3: "Escalate to source team manager"
    level_4: "Data governance council intervention"

  contract_enforcement:
    on_breach:
      - log_violation_to_contract_registry
      - increment_producer_reliability_score
      - trigger_automated_notification
    on_repeated_breach:
      - flag_for_governance_review
      - propose_contract_tightening
      - recommend_additional_validation_at_source
    metrics_tracked:
      - breach_count_per_producer_per_month
      - mean_time_to_acknowledge
      - mean_time_to_resolve
      - recurring_issue_rate
```

---

## 10. Lab Exercises

### Lab 1: Complete Data Quality Framework (Great Expectations + dbt + Elementary)

**Objective:** Implement end-to-end data quality monitoring for a data warehouse with three layers: raw ingestion validation, transformation testing, and ongoing observability.

**Architecture:**

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Raw Data   │───▶│  dbt Models  │───▶│  Data Marts  │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │
       ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│     GX       │    │  dbt Tests   │    │  Elementary  │
│  Validation  │    │  (generic +  │    │  Anomaly     │
│  (ingestion) │    │   custom)    │    │  Detection   │
└──────────────┘    └──────────────┘    └──────────────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           ▼
                  ┌──────────────────┐
                  │   DQ Dashboard   │
                  │  (Elementary UI  │
                  │   + custom)      │
                  └──────────────────┘
```

**Step 1: Project Setup**

```yaml
# dbt_project.yml
name: dq_warehouse
version: '1.0.0'
profile: warehouse

vars:
  dq_schema: 'data_quality'
  elementary_schema: 'elementary'

models:
  dq_warehouse:
    staging:
      +schema: staging
      +materialized: view
    marts:
      +schema: analytics
      +materialized: table

# packages.yml
packages:
  - package: dbt-labs/dbt_utils
    version: [">=1.0.0", "<2.0.0"]
  - package: calogica/dbt_expectations
    version: [">=0.10.0", "<0.11.0"]
  - package: elementary-data/elementary
    version: [">=0.13.0", "<0.14.0"]
```

**Step 2: Great Expectations for Raw Data Validation**

```python
# gx/validate_raw_ingestion.py
"""Validate raw data on ingestion before loading to warehouse."""

import great_expectations as gx
import pandas as pd
from pathlib import Path


def validate_raw_transactions(file_path: str) -> dict:
    """Validate a raw transactions file before warehouse ingestion."""
    context = gx.get_context(project_root_dir=Path(__file__).parent)

    # Load data
    df = pd.read_csv(file_path)

    # Get datasource and create batch
    datasource = context.data_sources.get("raw_files")
    asset = datasource.get_asset("transactions_csv")
    batch_def = asset.get_batch_definition("ingestion_batch")
    batch = batch_def.get_batch(batch_parameters={"dataframe": df})

    # Get suite
    suite = context.suites.get("raw_transactions_suite")

    # Run validation
    result = batch.validate(suite)

    # Generate data docs
    context.build_data_docs()

    return {
        "success": result.success,
        "statistics": result.statistics,
        "file_path": file_path,
        "row_count": len(df),
        "failed_expectations": [
            {
                "type": r.expectation_config.type,
                "kwargs": r.expectation_config.kwargs,
                "result": r.result,
            }
            for r in result.results
            if not r.success
        ],
    }


# gx/expectations/raw_transactions_suite.json
RAW_TRANSACTIONS_SUITE = {
    "name": "raw_transactions_suite",
    "expectations": [
        {
            "type": "expect_table_row_count_to_be_between",
            "kwargs": {"min_value": 100, "max_value": 10000000},
        },
        {
            "type": "expect_table_columns_to_match_set",
            "kwargs": {
                "column_set": [
                    "transaction_id", "customer_id", "amount",
                    "currency", "status", "created_at",
                ],
                "exact_match": False,
            },
        },
        {
            "type": "expect_column_values_to_not_be_null",
            "kwargs": {"column": "transaction_id"},
        },
        {
            "type": "expect_column_values_to_be_unique",
            "kwargs": {"column": "transaction_id"},
        },
        {
            "type": "expect_column_values_to_not_be_null",
            "kwargs": {"column": "customer_id"},
        },
        {
            "type": "expect_column_values_to_not_be_null",
            "kwargs": {"column": "amount"},
        },
        {
            "type": "expect_column_values_to_be_between",
            "kwargs": {"column": "amount", "min_value": 0, "max_value": 999999.99},
        },
        {
            "type": "expect_column_values_to_be_in_set",
            "kwargs": {
                "column": "currency",
                "value_set": ["USD", "EUR", "GBP", "JPY", "BRL"],
            },
        },
        {
            "type": "expect_column_values_to_be_in_set",
            "kwargs": {
                "column": "status",
                "value_set": ["pending", "completed", "failed", "refunded"],
            },
        },
        {
            "type": "expect_column_values_to_match_regex",
            "kwargs": {
                "column": "created_at",
                "regex": r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}",
            },
        },
    ],
}
```

**Step 3: dbt Tests for Transformation Layer**

```yaml
# models/staging/stg_transactions.yml
version: 2

models:
  - name: stg_transactions
    description: "Cleaned and standardized transactions from raw source"
    columns:
      - name: transaction_id
        data_tests:
          - unique
          - not_null

      - name: customer_id
        data_tests:
          - not_null
          - relationships:
              to: ref('stg_customers')
              field: customer_id
              severity: warn

      - name: amount_usd
        description: "Amount normalized to USD"
        data_tests:
          - not_null
          - dbt_expectations.expect_column_values_to_be_between:
              min_value: 0
              max_value: 999999.99
          - column_values_within_n_stdev:
              n_stdev: 4

      - name: transaction_date
        data_tests:
          - not_null
          - dbt_utils.accepted_range:
              min_value: "'2020-01-01'"
              max_value: "CURRENT_DATE"
          - freshness_within_threshold:
              max_hours: 24
              severity: error
              tags: ['critical']

      - name: status
        data_tests:
          - accepted_values:
              values: ['pending', 'completed', 'failed', 'refunded']
              severity: error

    data_tests:
      - dbt_expectations.expect_table_row_count_to_be_between:
          min_value: 1000
          tags: ['volume']

      - dbt_utils.recency:
          datepart: hour
          field: transaction_date
          interval: 24
          tags: ['freshness']


# models/marts/fct_daily_revenue.yml
version: 2

models:
  - name: fct_daily_revenue
    description: "Daily revenue aggregation"
    data_tests:
      - elementary.volume_anomalies:
          timestamp_column: revenue_date
          time_bucket:
            period: day
            count: 1
          severity: warn
          tags: ['observability']

      - elementary.freshness_anomalies:
          timestamp_column: revenue_date
          severity: error
          tags: ['observability']

    columns:
      - name: revenue_date
        data_tests:
          - unique
          - not_null

      - name: total_revenue
        data_tests:
          - not_null
          - elementary.column_anomalies:
              timestamp_column: revenue_date
              column_anomalies:
                - average
                - standard_deviation
                - min
                - max
              tags: ['observability']
```

**Step 4: Elementary Monitoring Configuration**

```yaml
# models/elementary_config.yml
# Elementary anomaly detection models

version: 2

models:
  - name: stg_transactions
    meta:
      owner: "data-engineering@company.com"
      tags: ["critical", "revenue"]
    data_tests:
      - elementary.all_columns_anomalies:
          timestamp_column: transaction_date
          where: "status = 'completed'"
          time_bucket:
            period: hour
            count: 1
          training_period:
            period: day
            count: 14
          severity: warn
          tags: ['anomaly_detection']

      - elementary.schema_changes:
          severity: error
          tags: ['schema_monitoring']
```

**Step 5: Orchestration (Airflow DAG)**

```python
# dags/data_quality_pipeline.py
"""Complete DQ pipeline: validate → transform → monitor."""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.trigger_rule import TriggerRule
from datetime import datetime, timedelta


default_args = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


def run_gx_validation(**kwargs):
    """Execute Great Expectations validation on raw data."""
    from gx.validate_raw_ingestion import validate_raw_transactions
    result = validate_raw_transactions(kwargs["params"]["file_path"])
    if not result["success"]:
        raise ValueError(f"GX validation failed: {result['failed_expectations']}")
    return result


def check_elementary_alerts(**kwargs):
    """Check Elementary for anomaly alerts after dbt run."""
    # Query Elementary results table
    pass


with DAG(
    "data_quality_pipeline",
    default_args=default_args,
    description="End-to-end data quality pipeline",
    schedule_interval="@hourly",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["data-quality"],
) as dag:

    # Phase 1: Raw data validation with GX
    validate_raw = PythonOperator(
        task_id="validate_raw_data",
        python_callable=run_gx_validation,
        params={"file_path": "/data/incoming/transactions_{{ ds }}.csv"},
    )

    # Phase 2: dbt transformations
    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command="cd /opt/dbt && dbt run --select staging+ --target prod",
    )

    # Phase 3: dbt tests (includes Elementary anomaly tests)
    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command="cd /opt/dbt && dbt test --target prod",
    )

    # Phase 4: Generate Elementary report
    elementary_report = BashOperator(
        task_id="elementary_report",
        bash_command="cd /opt/dbt && edr report --days-back 7",
    )

    # Phase 5: Check for critical alerts
    check_alerts = PythonOperator(
        task_id="check_alerts",
        python_callable=check_elementary_alerts,
        trigger_rule=TriggerRule.ALL_DONE,
    )

    validate_raw >> dbt_run >> dbt_test >> elementary_report >> check_alerts
```

---

### Lab 2: Data Contract System with Schema Evolution

**Objective:** Build a data contract registry that enforces schema contracts, detects breaking changes in CI/CD, and manages schema evolution across producer/consumer teams.

**Step 1: Contract Registry**

```python
# contracts/registry.py
"""Data contract registry with versioning and evolution tracking."""

import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass(frozen=True)
class ContractVersion:
    version: str
    schema: dict
    published_at: str
    status: str  # draft | active | deprecated | sunset
    changelog: tuple[str, ...]
    sunset_date: Optional[str] = None


@dataclass(frozen=True)
class Contract:
    name: str
    owner: str
    consumers: tuple[str, ...]
    versions: tuple[ContractVersion, ...]
    current_version: str


class ContractRegistry:
    """Manages data contracts with versioning."""

    def __init__(self, registry_path: Path):
        self._path = registry_path
        self._contracts: dict[str, Contract] = {}
        self._load()

    def _load(self):
        """Load all contracts from the registry directory."""
        for contract_file in self._path.glob("*/contract.json"):
            data = json.loads(contract_file.read_text())
            versions = tuple(
                ContractVersion(
                    version=v["version"],
                    schema=v["schema"],
                    published_at=v["published_at"],
                    status=v["status"],
                    changelog=tuple(v.get("changelog", [])),
                    sunset_date=v.get("sunset_date"),
                )
                for v in data["versions"]
            )
            contract = Contract(
                name=data["name"],
                owner=data["owner"],
                consumers=tuple(data["consumers"]),
                versions=versions,
                current_version=data["current_version"],
            )
            self._contracts[contract.name] = contract

    def get_contract(self, name: str) -> Optional[Contract]:
        return self._contracts.get(name)

    def get_active_schema(self, name: str) -> Optional[dict]:
        """Get the currently active schema for a contract."""
        contract = self._contracts.get(name)
        if not contract:
            return None
        for version in contract.versions:
            if version.version == contract.current_version:
                return version.schema
        return None

    def validate_evolution(self, name: str, proposed_schema: dict) -> dict:
        """Check if a proposed schema change is backwards compatible."""
        from tools.contract_diff import detect_breaking_changes, ChangeType

        current_schema = self.get_active_schema(name)
        if not current_schema:
            return {"compatible": True, "changes": [], "recommendation": "new_contract"}

        changes = detect_breaking_changes(current_schema, proposed_schema)
        breaking = [c for c in changes if c.change_type == ChangeType.BREAKING]

        return {
            "compatible": len(breaking) == 0,
            "breaking_changes": [
                {"path": c.path, "description": c.description}
                for c in breaking
            ],
            "all_changes": [
                {"path": c.path, "type": c.change_type.value, "description": c.description}
                for c in changes
            ],
            "recommendation": (
                "minor_version_bump" if len(breaking) == 0
                else "major_version_bump_required"
            ),
        }
```

**Step 2: CI/CD Integration**

```yaml
# .github/workflows/contract-check.yml
name: Data Contract Validation

on:
  pull_request:
    paths:
      - 'contracts/**'

jobs:
  validate-contracts:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: pip install jsonschema pytest

      - name: Validate contract schemas
        run: python -m pytest tests/test_data_contracts.py -v

      - name: Check for breaking changes
        run: |
          python tools/check_breaking_changes.py \
            --base-ref ${{ github.event.pull_request.base.sha }} \
            --head-ref ${{ github.event.pull_request.head.sha }}

      - name: Notify affected consumers
        if: failure()
        run: |
          python tools/notify_consumers.py \
            --contract-changes contracts/changed.json
```

```python
# tools/check_breaking_changes.py
"""CI script to detect breaking changes in data contracts."""

import sys
import json
import subprocess
from pathlib import Path


def get_changed_contracts(base_ref: str, head_ref: str) -> list[Path]:
    """Find contract files modified between two git refs."""
    result = subprocess.run(
        ["git", "diff", "--name-only", base_ref, head_ref, "--", "contracts/"],
        capture_output=True,
        text=True,
    )
    return [Path(f) for f in result.stdout.strip().split("\n") if f.endswith(".json")]


def get_file_at_ref(path: str, ref: str) -> str:
    """Get file content at a specific git ref."""
    result = subprocess.run(
        ["git", "show", f"{ref}:{path}"],
        capture_output=True,
        text=True,
    )
    return result.stdout


def main(base_ref: str, head_ref: str):
    from tools.contract_diff import detect_breaking_changes, ChangeType

    changed_files = get_changed_contracts(base_ref, head_ref)
    all_breaking = []

    for contract_file in changed_files:
        try:
            old_content = get_file_at_ref(str(contract_file), base_ref)
            old_schema = json.loads(old_content)
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            continue  # New file, no breaking change possible

        new_schema = json.loads(contract_file.read_text())
        changes = detect_breaking_changes(old_schema, new_schema)
        breaking = [c for c in changes if c.change_type == ChangeType.BREAKING]

        if breaking:
            all_breaking.append({
                "contract": str(contract_file),
                "breaking_changes": [
                    {"path": c.path, "description": c.description}
                    for c in breaking
                ],
            })

    if all_breaking:
        print("BREAKING CHANGES DETECTED:")
        print(json.dumps(all_breaking, indent=2))
        sys.exit(1)
    else:
        print("No breaking changes detected.")
        sys.exit(0)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-ref", required=True)
    parser.add_argument("--head-ref", required=True)
    args = parser.parse_args()
    main(args.base_ref, args.head_ref)
```

---

### Lab 3: Automated Data Profiling and Anomaly Detection Pipeline

**Objective:** Build an automated system that profiles data daily, compares against historical baselines, detects anomalies, and generates alerts with context.

**Step 1: Profiling Pipeline**

```python
# profiling/daily_profiler.py
"""Daily data profiling pipeline with drift detection."""

import json
from datetime import datetime, date
from pathlib import Path
from typing import Optional
import pandas as pd
import numpy as np


class DailyProfiler:
    """Runs daily profiling and stores results for trend analysis."""

    def __init__(self, storage_path: Path, lookback_days: int = 30):
        self._storage = storage_path
        self._lookback = lookback_days
        self._storage.mkdir(parents=True, exist_ok=True)

    def profile_and_compare(
        self,
        df: pd.DataFrame,
        dataset_name: str,
        profile_date: Optional[date] = None,
    ) -> dict:
        """Profile current data and compare to historical baseline."""
        if profile_date is None:
            profile_date = date.today()

        # Generate current profile
        current_profile = self._generate_profile(df)

        # Store current profile
        self._store_profile(dataset_name, profile_date, current_profile)

        # Load historical profiles for comparison
        historical = self._load_historical(dataset_name, profile_date)

        # Detect anomalies
        anomalies = self._detect_anomalies(current_profile, historical)

        return {
            "dataset": dataset_name,
            "profile_date": profile_date.isoformat(),
            "profile": current_profile,
            "anomalies": anomalies,
            "has_critical_anomalies": any(a["severity"] == "critical" for a in anomalies),
        }

    def _generate_profile(self, df: pd.DataFrame) -> dict:
        """Generate statistical profile for a DataFrame."""
        profile = {
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": {},
        }

        for col in df.columns:
            col_profile = {
                "dtype": str(df[col].dtype),
                "null_count": int(df[col].isnull().sum()),
                "null_rate": float(df[col].isnull().mean()),
                "distinct_count": int(df[col].nunique()),
            }

            if pd.api.types.is_numeric_dtype(df[col]):
                desc = df[col].describe()
                col_profile.update({
                    "mean": float(desc["mean"]),
                    "std": float(desc["std"]),
                    "min": float(desc["min"]),
                    "max": float(desc["max"]),
                    "p25": float(desc["25%"]),
                    "p50": float(desc["50%"]),
                    "p75": float(desc["75%"]),
                    "zero_count": int((df[col] == 0).sum()),
                    "negative_count": int((df[col] < 0).sum()),
                })

            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                non_null = df[col].dropna()
                if len(non_null) > 0:
                    col_profile.update({
                        "min_date": str(non_null.min()),
                        "max_date": str(non_null.max()),
                    })

            elif df[col].dtype == "object":
                col_profile.update({
                    "avg_length": float(df[col].dropna().str.len().mean()) if len(df[col].dropna()) > 0 else 0,
                    "max_length": int(df[col].dropna().str.len().max()) if len(df[col].dropna()) > 0 else 0,
                    "empty_count": int((df[col] == "").sum()),
                })

                if col_profile["distinct_count"] <= 50:
                    top_values = df[col].value_counts().head(20).to_dict()
                    col_profile["top_values"] = {str(k): int(v) for k, v in top_values.items()}

            profile["columns"][col] = col_profile

        return profile

    def _detect_anomalies(self, current: dict, historical: list[dict]) -> list[dict]:
        """Compare current profile against historical baseline."""
        if len(historical) < 7:
            return []  # Not enough history for meaningful detection

        anomalies = []

        # Row count anomaly
        hist_counts = [h["row_count"] for h in historical]
        count_anomaly = self._check_numeric_anomaly(
            "row_count", current["row_count"], hist_counts
        )
        if count_anomaly:
            anomalies.append(count_anomaly)

        # Column-level anomalies
        for col_name, col_stats in current["columns"].items():
            hist_col_stats = [
                h["columns"].get(col_name, {})
                for h in historical
                if col_name in h.get("columns", {})
            ]

            if not hist_col_stats:
                continue

            # Null rate anomaly
            hist_null_rates = [h.get("null_rate", 0) for h in hist_col_stats]
            null_anomaly = self._check_numeric_anomaly(
                f"{col_name}.null_rate", col_stats["null_rate"], hist_null_rates,
                threshold=3.0,
            )
            if null_anomaly:
                anomalies.append(null_anomaly)

            # Numeric column anomalies
            if "mean" in col_stats:
                hist_means = [h.get("mean") for h in hist_col_stats if "mean" in h]
                if hist_means:
                    mean_anomaly = self._check_numeric_anomaly(
                        f"{col_name}.mean", col_stats["mean"], hist_means
                    )
                    if mean_anomaly:
                        anomalies.append(mean_anomaly)

                hist_stds = [h.get("std") for h in hist_col_stats if "std" in h]
                if hist_stds:
                    std_anomaly = self._check_numeric_anomaly(
                        f"{col_name}.std", col_stats["std"], hist_stds
                    )
                    if std_anomaly:
                        anomalies.append(std_anomaly)

            # Distinct count anomaly (detect new categories)
            hist_distinct = [h.get("distinct_count", 0) for h in hist_col_stats]
            distinct_anomaly = self._check_numeric_anomaly(
                f"{col_name}.distinct_count", col_stats["distinct_count"], hist_distinct,
                threshold=2.5,
            )
            if distinct_anomaly:
                anomalies.append(distinct_anomaly)

        return anomalies

    def _check_numeric_anomaly(
        self,
        metric_name: str,
        current_value: float,
        historical_values: list[float],
        threshold: float = 3.0,
    ) -> Optional[dict]:
        """Check if current value is anomalous vs historical."""
        arr = np.array([v for v in historical_values if v is not None])
        if len(arr) < 5:
            return None

        mean = np.mean(arr)
        std = np.std(arr)

        if std == 0:
            is_anomaly = current_value != mean
            z_score = float("inf") if is_anomaly else 0.0
        else:
            z_score = (current_value - mean) / std
            is_anomaly = abs(z_score) > threshold

        if not is_anomaly:
            return None

        severity = "critical" if abs(z_score) > 5 else "high" if abs(z_score) > 4 else "medium"

        return {
            "metric": metric_name,
            "current_value": current_value,
            "historical_mean": float(mean),
            "historical_std": float(std),
            "z_score": float(z_score),
            "severity": severity,
            "message": f"{metric_name}: current={current_value:.4f}, expected={mean:.4f}+/-{std:.4f} (z={z_score:.2f})",
        }

    def _store_profile(self, dataset_name: str, profile_date: date, profile: dict):
        """Persist profile to storage."""
        dir_path = self._storage / dataset_name
        dir_path.mkdir(parents=True, exist_ok=True)
        file_path = dir_path / f"{profile_date.isoformat()}.json"
        file_path.write_text(json.dumps(profile, indent=2, default=str))

    def _load_historical(self, dataset_name: str, before_date: date) -> list[dict]:
        """Load historical profiles for comparison."""
        dir_path = self._storage / dataset_name
        if not dir_path.exists():
            return []

        profiles = []
        for file_path in sorted(dir_path.glob("*.json"), reverse=True):
            file_date = date.fromisoformat(file_path.stem)
            if file_date < before_date:
                profiles.append(json.loads(file_path.read_text()))
                if len(profiles) >= self._lookback:
                    break

        return profiles
```

**Step 2: Alert Generation**

```python
# profiling/alerting.py
"""Alert generation and routing for data quality anomalies."""

from dataclasses import dataclass
from typing import Optional
import json


@dataclass(frozen=True)
class Alert:
    dataset: str
    severity: str
    metric: str
    message: str
    context: dict
    timestamp: str
    runbook_link: Optional[str] = None


def generate_alerts(profiling_result: dict) -> list[Alert]:
    """Generate structured alerts from profiling anomalies."""
    alerts = []
    for anomaly in profiling_result.get("anomalies", []):
        alert = Alert(
            dataset=profiling_result["dataset"],
            severity=anomaly["severity"],
            metric=anomaly["metric"],
            message=anomaly["message"],
            context={
                "current_value": anomaly["current_value"],
                "expected_mean": anomaly["historical_mean"],
                "z_score": anomaly["z_score"],
            },
            timestamp=profiling_result["profile_date"],
            runbook_link=_get_runbook(anomaly["metric"]),
        )
        alerts.append(alert)
    return alerts


def format_slack_alert(alert: Alert) -> dict:
    """Format alert as Slack message payload."""
    severity_emoji = {
        "critical": ":rotating_light:",
        "high": ":warning:",
        "medium": ":information_source:",
    }
    emoji = severity_emoji.get(alert.severity, ":grey_question:")

    return {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} Data Quality Alert - {alert.severity.upper()}",
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Dataset:*\n{alert.dataset}"},
                    {"type": "mrkdwn", "text": f"*Metric:*\n{alert.metric}"},
                    {"type": "mrkdwn", "text": f"*Severity:*\n{alert.severity}"},
                    {"type": "mrkdwn", "text": f"*Detected:*\n{alert.timestamp}"},
                ],
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Details:*\n{alert.message}",
                },
            },
        ],
    }


def _get_runbook(metric: str) -> Optional[str]:
    """Map metric to relevant runbook URL."""
    runbook_map = {
        "row_count": "https://wiki.internal/runbooks/data-quality/row-count-anomaly",
        "null_rate": "https://wiki.internal/runbooks/data-quality/null-rate-spike",
        "mean": "https://wiki.internal/runbooks/data-quality/distribution-drift",
        "distinct_count": "https://wiki.internal/runbooks/data-quality/cardinality-change",
    }
    for key, url in runbook_map.items():
        if key in metric:
            return url
    return None
```

---

### Lab 4: Data Quality Dashboard Design

**Objective:** Design and implement a data quality monitoring dashboard that provides visibility into DQ health across the entire data platform.

**Dashboard Specification:**

```yaml
data_quality_dashboard:
  pages:
    executive_summary:
      widgets:
        - overall_dq_score:
            type: gauge
            metric: composite_dq_score
            thresholds: { red: 90, yellow: 95, green: 98 }
        - trend_chart:
            type: line_chart
            metrics: [accuracy, completeness, freshness, consistency]
            period: 90_days
        - active_incidents:
            type: count
            filter: status IN ('open', 'investigating')
        - sla_compliance:
            type: percentage
            metric: sla_met / total_slas

    table_health:
      widgets:
        - table_scorecard:
            type: table
            columns: [table_name, owner, freshness, completeness, test_pass_rate, last_issue]
            sortable: true
            filterable: true
        - freshness_heatmap:
            type: heatmap
            x_axis: hour_of_day
            y_axis: table_name
            value: freshness_minutes
        - test_results_timeline:
            type: timeline
            events: dbt_test_results
            period: 7_days

    incidents:
      widgets:
        - incident_timeline:
            type: timeline
            events: dq_incidents
            grouped_by: severity
        - mttr_chart:
            type: bar_chart
            metric: mean_time_to_resolve
            grouped_by: issue_category
        - recurring_issues:
            type: table
            filter: occurrence_count > 2
            columns: [issue_type, table, count, last_seen, owner]

    pipeline_health:
      widgets:
        - pipeline_success_rate:
            type: line_chart
            metric: successful_runs / total_runs
            period: 30_days
        - test_coverage:
            type: bar_chart
            metric: tested_columns / total_columns
            grouped_by: schema
        - validation_results:
            type: stacked_bar
            categories: [pass, warn, fail]
            grouped_by: date
```

**Dashboard Query Examples:**

```sql
-- Overall DQ Score (last 24 hours)
WITH dimension_scores AS (
    SELECT
        'accuracy' AS dimension,
        1.0 - (failed_accuracy_checks::FLOAT / total_accuracy_checks) AS score,
        0.25 AS weight
    FROM dq_metrics.daily_scores
    WHERE metric_date = CURRENT_DATE
    UNION ALL
    SELECT
        'completeness',
        1.0 - AVG(null_rate),
        0.20
    FROM dq_metrics.column_completeness
    WHERE measured_at >= CURRENT_DATE
    UNION ALL
    SELECT
        'freshness',
        CASE
            WHEN MAX(hours_since_update) <= 24 THEN 1.0
            WHEN MAX(hours_since_update) <= 48 THEN 0.8
            ELSE 0.5
        END,
        0.20
    FROM dq_metrics.table_freshness
    WHERE measured_at >= CURRENT_DATE
    UNION ALL
    SELECT
        'consistency',
        1.0 - (inconsistent_records::FLOAT / total_records),
        0.15
    FROM dq_metrics.consistency_checks
    WHERE check_date = CURRENT_DATE
    UNION ALL
    SELECT
        'test_pass_rate',
        passed_tests::FLOAT / total_tests,
        0.20
    FROM dq_metrics.dbt_test_results
    WHERE run_date = CURRENT_DATE
)
SELECT
    ROUND(SUM(score * weight) / SUM(weight) * 100, 1) AS overall_dq_score,
    ARRAY_AGG(
        JSON_BUILD_OBJECT('dimension', dimension, 'score', ROUND(score * 100, 1))
    ) AS dimension_breakdown
FROM dimension_scores;

-- Table Health Scorecard
SELECT
    t.table_name,
    t.owner,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - f.last_updated)) / 3600 AS hours_since_update,
    CASE
        WHEN EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - f.last_updated)) / 3600 <= f.freshness_sla_hours
        THEN 'ON_TIME'
        ELSE 'LATE'
    END AS freshness_status,
    c.completeness_pct,
    tr.pass_rate,
    i.last_incident_date,
    i.open_incident_count
FROM dq_catalog.tables t
LEFT JOIN dq_metrics.table_freshness f ON t.table_name = f.table_name
LEFT JOIN dq_metrics.table_completeness c ON t.table_name = c.table_name AND c.measured_date = CURRENT_DATE
LEFT JOIN (
    SELECT
        table_name,
        SUM(CASE WHEN status = 'pass' THEN 1 ELSE 0 END)::FLOAT / COUNT(*) AS pass_rate
    FROM dq_metrics.dbt_test_results
    WHERE run_date >= CURRENT_DATE - INTERVAL '7 days'
    GROUP BY table_name
) tr ON t.table_name = tr.table_name
LEFT JOIN (
    SELECT
        affected_table,
        MAX(detected_at) AS last_incident_date,
        COUNT(*) FILTER (WHERE status = 'open') AS open_incident_count
    FROM dq_incidents.incidents
    GROUP BY affected_table
) i ON t.table_name = i.affected_table
ORDER BY COALESCE(tr.pass_rate, 0) ASC, hours_since_update DESC;

-- Incident MTTR by Category (last 90 days)
SELECT
    issue_category,
    COUNT(*) AS incident_count,
    AVG(EXTRACT(EPOCH FROM (resolved_at - detected_at)) / 3600) AS avg_hours_to_resolve,
    PERCENTILE_CONT(0.50) WITHIN GROUP (
        ORDER BY EXTRACT(EPOCH FROM (resolved_at - detected_at)) / 3600
    ) AS median_hours_to_resolve,
    PERCENTILE_CONT(0.95) WITHIN GROUP (
        ORDER BY EXTRACT(EPOCH FROM (resolved_at - detected_at)) / 3600
    ) AS p95_hours_to_resolve
FROM dq_incidents.incidents
WHERE detected_at >= CURRENT_DATE - INTERVAL '90 days'
  AND resolved_at IS NOT NULL
GROUP BY issue_category
ORDER BY avg_hours_to_resolve DESC;
```

---

## Summary

Data quality is not a one-time project but a continuous discipline requiring:

1. **Clear dimensions and metrics** — Know what to measure and define explicit thresholds
2. **Layered validation** — Input validation (GX), transformation testing (dbt), ongoing monitoring (Elementary)
3. **Contracts between teams** — Formalize expectations between producers and consumers
4. **Automated detection** — Use statistical methods to catch issues human-written rules miss
5. **Rapid response** — Incident management with clear severity levels and escalation paths
6. **Root cause elimination** — Fix the source, not just the symptom
7. **Cultural accountability** — Data quality owned by producers, measured continuously, visible to all

The tooling ecosystem (Great Expectations, dbt tests, Elementary, data contract registries) provides the building blocks. The organizational commitment to use them consistently, respond to failures promptly, and continuously improve is what separates mature data platforms from fragile ones.
