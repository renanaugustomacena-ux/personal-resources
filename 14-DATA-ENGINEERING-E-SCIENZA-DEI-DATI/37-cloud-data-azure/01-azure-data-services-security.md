# Azure Data Services — Architecture, Implementation, and Security

## Table of Contents

1. [Azure Data Architecture Overview](#1-azure-data-architecture-overview)
2. [Azure Data Lake Storage Gen2](#2-azure-data-lake-storage-gen2)
3. [Azure Synapse Analytics](#3-azure-synapse-analytics)
4. [Azure Data Factory](#4-azure-data-factory)
5. [Azure Databricks](#5-azure-databricks)
6. [Streaming and Events](#6-streaming-and-events)
7. [Security Architecture](#7-security-architecture)
8. [Security Assessment](#8-security-assessment)
9. [Monitoring and Compliance](#9-monitoring-and-compliance)
10. [Lab Exercises](#10-lab-exercises)

---

## 1. Azure Data Architecture Overview

### Core Data Services Taxonomy

Azure's data platform is a composable set of PaaS/SaaS services designed to handle ingestion, storage, processing, serving, and governance across batch, streaming, and interactive workloads. Understanding the interplay between these services is foundational to both implementation and security assessment.

### Azure Data Lake Storage Gen2 (ADLS Gen2)

ADLS Gen2 combines Azure Blob Storage scalability with a hierarchical namespace (HNS), providing POSIX-like directory semantics, fine-grained ACLs, and atomic directory operations. It is the canonical landing zone for raw, curated, and enriched data in Azure lakehouses.

Key differentiators from standard Blob Storage:
- Hierarchical namespace enables true directory operations (rename, delete are O(1) metadata ops)
- POSIX ACLs (rwx) on directories and files coexist with Azure RBAC
- Integration with ABFS driver for Hadoop-compatible workloads
- Storage account endpoint: `https://<account>.dfs.core.windows.net`

### Azure Synapse Analytics

A unified analytics platform merging:
- **Dedicated SQL pools** (formerly SQL DW): MPP distributed query engine with columnar storage
- **Serverless SQL pools**: On-demand query over external data (Parquet, Delta, CSV in ADLS)
- **Apache Spark pools**: Managed Spark with auto-scaling, notebook collaboration
- **Data integration**: Built-in pipeline orchestration (ADF-compatible)
- **Synapse Link**: No-ETL operational analytics bridging Cosmos DB, Dataverse, SQL Server

### Azure Data Factory (ADF)

Cloud-native ETL/ELT orchestration service. ADF pipelines move and transform data across 100+ connectors. Key primitives:
- **Pipelines**: Logical grouping of activities
- **Activities**: Copy, Data Flow, Stored Procedure, Databricks, Custom, Web
- **Integration Runtimes**: Compute infrastructure (Azure IR, Self-hosted IR, SSIS IR)
- **Triggers**: Schedule, tumbling window, event-based, custom event

### Azure Databricks

Jointly operated by Microsoft and Databricks Inc. Provides managed Apache Spark with collaborative notebooks, MLflow, Delta Lake, and Unity Catalog for unified governance.

### Azure Stream Analytics (ASA)

Fully managed real-time analytics engine using T-SQL-like query language over streaming data from Event Hubs, IoT Hub, and Blob Storage.

### Azure Event Hubs

Distributed streaming platform (Kafka-compatible) handling millions of events/second with partitioned consumer model, capture to ADLS/Blob, and Schema Registry.

### Azure Cosmos DB

Globally distributed, multi-model database with turnkey replication, single-digit-millisecond latency, and five consistency models. Relevant to data engineering as operational store feeding analytics via Synapse Link or Change Feed.

### Reference Architectures

#### Modern Data Warehouse

```
Sources → ADF Ingestion → ADLS Gen2 (Bronze/Silver/Gold)
                                    ↓
                          Synapse Dedicated SQL Pool (Gold serving)
                                    ↓
                              Power BI / APIs
```

Characteristics:
- Medallion architecture (Bronze: raw, Silver: validated, Gold: business-ready)
- ADF orchestrates ingestion from on-premises, SaaS, APIs
- Synapse provides distributed query over structured Gold layer
- Purview provides lineage and governance

#### Real-Time Analytics

```
IoT Devices / Apps → Event Hubs → Stream Analytics → Power BI (real-time)
                                        ↓
                                   ADLS Gen2 (archive)
                                        ↓
                                   Synapse (batch analytics)
```

Characteristics:
- Event Hubs provides partitioned ingestion at millions of events/sec
- ASA windowing functions (tumbling, hopping, sliding, session) for aggregation
- Dual output: real-time dashboards + cold storage for batch reprocessing

#### IoT Reference Architecture

```
IoT Devices → IoT Hub → ASA (hot path) → Cosmos DB → Power BI
                  ↓
          Azure Functions (warm path)
                  ↓
          ADLS Gen2 (cold path) → Databricks ML → Model Serving
```

Characteristics:
- Three-path processing (hot/warm/cold) separates latency requirements
- IoT Hub provides device identity, twin management, C2D messaging
- ML models trained on historical cold-path data, served on warm/hot path

#### Lakehouse Architecture

```
Sources → ADF / Event Hubs → ADLS Gen2 (Delta Lake format)
                                       ↓
                           Databricks (unified compute)
                                       ↓
                      Unity Catalog (governance) + Purview (lineage)
                                       ↓
                           Synapse Serverless (SQL access)
                                       ↓
                               Power BI / Apps
```

Characteristics:
- Delta Lake provides ACID transactions on object storage
- Unity Catalog centralizes access control, audit, lineage
- Synapse Serverless enables SQL over Delta without data movement
- Eliminates traditional warehouse as separate copy

---

## 2. Azure Data Lake Storage Gen2

### Hierarchical Namespace (HNS)

The hierarchical namespace transforms flat blob storage into a true filesystem. When HNS is enabled:

- Directory rename/delete operations are atomic metadata operations (O(1))
- File paths become first-class objects with permission inheritance
- POSIX ACLs (access + default) are enforceable on every node
- Blob API and DFS API both remain available, but DFS is primary for analytics

```bash
# Enable HNS at account creation (cannot be enabled post-creation on existing accounts)
az storage account create \
  --name mystorageaccount \
  --resource-group rg-data-platform \
  --location westeurope \
  --sku Standard_ZRS \
  --kind StorageV2 \
  --hns true \
  --min-tls-version TLS1_2 \
  --allow-blob-public-access false \
  --require-infrastructure-encryption true
```

### ACLs (POSIX-Style)

ADLS Gen2 supports two authorization layers that coexist:

1. **Azure RBAC** (coarse-grained): Storage Blob Data Owner/Contributor/Reader roles
2. **POSIX ACLs** (fine-grained): rwx permissions on files/directories with named users, named groups, owning user, owning group, other, mask

ACL types:
- **Access ACLs**: Control access to the object itself
- **Default ACLs**: Template applied to new child objects (directories only)

```bash
# Set ACL on a directory — grant read+execute to a security group
az storage fs access set \
  --account-name mystorageaccount \
  --file-system bronze \
  --path raw/sales/ \
  --acl "group:data-engineers-sg:r-x,default:group:data-engineers-sg:r-x"

# Recursive ACL update
az storage fs access set-recursive \
  --account-name mystorageaccount \
  --file-system silver \
  --path curated/ \
  --acl "group:data-scientists-sg:r-x"
```

Permission evaluation order:
1. If caller has RBAC role (Storage Blob Data Owner/Contributor/Reader), ACLs are bypassed
2. If no RBAC role, ACLs are evaluated: owning user → named users → owning group/named groups → other
3. Mask entry limits effective permissions for named users, named groups, and owning group

### Integration with Entra ID (Azure Active Directory)

ADLS Gen2 authenticates via Entra ID OAuth 2.0 tokens. Service principals, managed identities, and user principals all authenticate the same way:

```python
from azure.identity import DefaultAzureCredential
from azure.storage.filedatalake import DataLakeServiceClient

credential = DefaultAzureCredential()
service_client = DataLakeServiceClient(
    account_url="https://mystorageaccount.dfs.core.windows.net",
    credential=credential
)

file_system_client = service_client.get_file_system_client("bronze")
directory_client = file_system_client.get_directory_client("raw/events")
```

### Storage Account Security

#### Firewall and Network Rules

```bicep
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  kind: 'StorageV2'
  sku: { name: 'Standard_ZRS' }
  properties: {
    isHnsEnabled: true
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    supportsHttpsTrafficOnly: true
    networkAcls: {
      defaultAction: 'Deny'
      bypass: 'AzureServices'
      virtualNetworkRules: [
        { id: subnetId, action: 'Allow' }
      ]
      ipRules: [
        { value: '203.0.113.0/24', action: 'Allow' }
      ]
    }
    encryption: {
      services: {
        blob: { enabled: true, keyType: 'Account' }
        file: { enabled: true, keyType: 'Account' }
      }
      keySource: 'Microsoft.Keyvault'
      keyvaultproperties: {
        keyname: encryptionKeyName
        keyvaulturi: keyVaultUri
      }
      requireInfrastructureEncryption: true
    }
  }
}
```

#### Private Endpoints

```terraform
resource "azurerm_private_endpoint" "adls_pe" {
  name                = "pe-adls-${var.environment}"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  subnet_id           = azurerm_subnet.private_endpoints.id

  private_service_connection {
    name                           = "psc-adls"
    private_connection_resource_id = azurerm_storage_account.datalake.id
    subresource_names              = ["dfs"]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name                 = "adls-dns-zone-group"
    private_dns_zone_ids = [azurerm_private_dns_zone.dfs.id]
  }
}

resource "azurerm_private_dns_zone" "dfs" {
  name                = "privatelink.dfs.core.windows.net"
  resource_group_name = azurerm_resource_group.rg.name
}
```

#### Managed Identity Access

```bash
# Assign Storage Blob Data Contributor to a managed identity
az role assignment create \
  --assignee-object-id $MANAGED_IDENTITY_OBJECT_ID \
  --role "Storage Blob Data Contributor" \
  --scope "/subscriptions/$SUB_ID/resourceGroups/rg-data/providers/Microsoft.Storage/storageAccounts/mystorageaccount"
```

### Lifecycle Management

```json
{
  "rules": [
    {
      "enabled": true,
      "name": "move-to-cool-after-30-days",
      "type": "Lifecycle",
      "definition": {
        "actions": {
          "baseBlob": {
            "tierToCool": { "daysAfterModificationGreaterThan": 30 },
            "tierToArchive": { "daysAfterModificationGreaterThan": 180 },
            "delete": { "daysAfterModificationGreaterThan": 365 }
          }
        },
        "filters": {
          "blobTypes": ["blockBlob"],
          "prefixMatch": ["bronze/raw/"]
        }
      }
    }
  ]
}
```

### Redundancy Options

| Option | Description | RPO | Use Case |
|--------|-------------|-----|----------|
| LRS | 3 copies in single datacenter | ~0 | Dev/test, non-critical |
| ZRS | 3 copies across 3 AZs | ~0 | Production, regional HA |
| GRS | LRS + async copy to paired region | ~15 min | DR requirement |
| GZRS | ZRS + async copy to paired region | ~15 min | Maximum durability + HA |

For data lake workloads, **ZRS** is the recommended baseline for production — it balances durability (3 AZ copies) with cost and provides synchronous writes across zones.

---

## 3. Azure Synapse Analytics

### Dedicated SQL Pools

Dedicated SQL pools implement massively parallel processing (MPP) with a control node distributing queries to 60 distributions across compute nodes.

#### Distribution Strategies

| Strategy | Mechanism | Best For |
|----------|-----------|----------|
| Hash | Rows distributed by hash of a column | Large fact tables (>60M rows), join key distribution |
| Round-robin | Rows distributed evenly, no key | Staging tables, no clear distribution key |
| Replicated | Full copy on each compute node | Small dimension tables (<2GB) |

```sql
-- Hash-distributed fact table
CREATE TABLE dbo.FactSales
(
    SalesKey BIGINT NOT NULL,
    OrderDate DATE NOT NULL,
    CustomerKey INT NOT NULL,
    ProductKey INT NOT NULL,
    Amount DECIMAL(18,2) NOT NULL
)
WITH (
    DISTRIBUTION = HASH(CustomerKey),
    CLUSTERED COLUMNSTORE INDEX,
    PARTITION (OrderDate RANGE RIGHT FOR VALUES
        ('2024-01-01','2024-04-01','2024-07-01','2024-10-01'))
);

-- Replicated dimension table
CREATE TABLE dbo.DimProduct
(
    ProductKey INT NOT NULL,
    ProductName NVARCHAR(200) NOT NULL,
    Category NVARCHAR(100) NOT NULL
)
WITH (
    DISTRIBUTION = REPLICATE,
    CLUSTERED COLUMNSTORE INDEX
);
```

#### Indexing

- **Clustered Columnstore Index (CCI)**: Default for analytics. Columnar compression, batch mode execution. Optimal for scans over millions of rows.
- **Heap**: No index. Used for staging/temp tables with frequent inserts.
- **Clustered Rowstore Index**: B-tree. Rare in analytics; useful for lookup patterns.
- **Nonclustered Index**: Additional B-tree on CCI or rowstore for point lookups.

#### Workload Management

```sql
-- Create workload group for data engineering ETL
CREATE WORKLOAD GROUP wg_etl
WITH (
    MIN_PERCENTAGE_RESOURCE = 25,
    MAX_PERCENTAGE_RESOURCE = 50,
    CAP_PERCENTAGE_RESOURCE = 75,
    REQUEST_MIN_RESOURCE_GRANT_PERCENT = 10,
    REQUEST_MAX_RESOURCE_GRANT_PERCENT = 25
);

-- Create classifier to route ETL service principal
CREATE WORKLOAD CLASSIFIER wc_etl
WITH (
    WORKLOAD_GROUP = 'wg_etl',
    MEMBERNAME = 'svc_etl_principal',
    IMPORTANCE = ABOVE_NORMAL
);
```

### Serverless SQL Pools

Serverless pools query external data in-place without loading it. Pay per TB scanned.

```sql
-- Query Parquet files in ADLS Gen2
CREATE EXTERNAL DATA SOURCE adls_bronze
WITH (
    LOCATION = 'abfss://bronze@mystorageaccount.dfs.core.windows.net'
);

SELECT
    customer_id,
    SUM(amount) as total_spend,
    COUNT(*) as transaction_count
FROM OPENROWSET(
    BULK 'raw/transactions/year=2024/month=*/*.parquet',
    DATA_SOURCE = 'adls_bronze',
    FORMAT = 'PARQUET'
) AS txn
GROUP BY customer_id
HAVING SUM(amount) > 10000;

-- Create logical view over Delta Lake
CREATE OR ALTER VIEW dbo.vw_customers AS
SELECT *
FROM OPENROWSET(
    BULK 'curated/customers/',
    DATA_SOURCE = 'adls_bronze',
    FORMAT = 'DELTA'
) AS c;
```

### Spark Pools

Managed Apache Spark with auto-scale, session-level isolation, and notebook collaboration.

```python
# PySpark in Synapse Spark pool
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, sum, window

spark = SparkSession.builder.getOrCreate()

# Read Delta Lake table from ADLS Gen2
df = spark.read.format("delta").load(
    "abfss://silver@mystorageaccount.dfs.core.windows.net/curated/events/"
)

# Windowed aggregation
result = (
    df.filter(col("event_date") >= "2024-01-01")
    .groupBy(window("event_timestamp", "1 hour"), "event_type")
    .agg(sum("event_value").alias("hourly_total"))
    .orderBy("window.start")
)

# Write to Gold layer as Delta
result.write.format("delta").mode("overwrite").save(
    "abfss://gold@mystorageaccount.dfs.core.windows.net/aggregated/hourly_events/"
)
```

### Synapse Link

Synapse Link provides near-real-time analytical access to operational data without impacting the source system:

- **Cosmos DB Synapse Link**: Auto-syncs Cosmos DB analytical store to Synapse (columnar format)
- **SQL Server / Azure SQL Synapse Link**: CDC-based replication to Synapse dedicated pools
- **Dataverse Synapse Link**: Dynamics 365 / Power Platform data to ADLS Gen2

```sql
-- Query Cosmos DB analytical store via Synapse Link
SELECT TOP 100 *
FROM OPENROWSET(
    'CosmosDB',
    'Account=mycosmosaccount;Database=ecommerce;Key=<read-only-key>',
    orders
) AS orders
WHERE orders.order_date > '2024-06-01';
```

### Workspace Security Model

#### Managed VNet

When workspace-managed VNet is enabled:
- All Spark pool and pipeline compute runs in an isolated VNet
- Outbound traffic restricted to approved destinations via managed private endpoints
- No public IP addresses assigned to compute
- Data exfiltration protection prevents writing to unauthorized storage accounts

```bicep
resource synapseWorkspace 'Microsoft.Synapse/workspaces@2021-06-01' = {
  name: workspaceName
  location: location
  identity: { type: 'SystemAssigned' }
  properties: {
    defaultDataLakeStorage: {
      accountUrl: 'https://${storageAccountName}.dfs.core.windows.net'
      filesystem: 'synapse'
    }
    managedVirtualNetwork: 'default'
    managedVirtualNetworkSettings: {
      preventDataExfiltration: true
      allowedAadTenantIdsForLinking: [subscription().tenantId]
    }
    publicNetworkAccess: 'Disabled'
  }
}
```

#### Role-Based Access

| Role | Scope | Permissions |
|------|-------|-------------|
| Synapse Administrator | Workspace | Full control over all artifacts |
| Synapse SQL Administrator | SQL pools | DDL/DML on dedicated/serverless pools |
| Synapse Spark Administrator | Spark pools | Manage Spark pools and sessions |
| Synapse Contributor | Workspace | Create/edit artifacts, cannot publish |
| Synapse Artifact Publisher | Workspace | Publish artifacts (deploy) |
| Synapse Artifact User | Workspace | Read/execute published artifacts |

---

## 4. Azure Data Factory

### Pipelines and Activities

ADF pipelines are DAGs of activities. Activities fall into three categories:

1. **Data movement**: Copy activity (100+ connectors)
2. **Data transformation**: Data Flow, Databricks, HDInsight, Stored Procedure, Custom
3. **Control flow**: If Condition, ForEach, Until, Switch, Wait, Web, Set Variable, Execute Pipeline

```json
{
  "name": "IngestSalesData",
  "properties": {
    "activities": [
      {
        "name": "CopyFromSQLToADLS",
        "type": "Copy",
        "inputs": [{ "referenceName": "SqlServerSource", "type": "DatasetReference" }],
        "outputs": [{ "referenceName": "AdlsParquetSink", "type": "DatasetReference" }],
        "typeProperties": {
          "source": {
            "type": "SqlServerSource",
            "sqlReaderQuery": "SELECT * FROM sales.orders WHERE modified_at > @{pipeline().parameters.lastWatermark}"
          },
          "sink": {
            "type": "ParquetSink",
            "storeSettings": { "type": "AzureBlobFSWriteSettings" }
          },
          "enableStaging": true,
          "stagingSettings": {
            "linkedServiceName": { "referenceName": "StagingBlobStorage", "type": "LinkedServiceReference" }
          }
        }
      }
    ],
    "parameters": {
      "lastWatermark": { "type": "String", "defaultValue": "1900-01-01" }
    }
  }
}
```

### Integration Runtimes

| Type | Location | Use Case |
|------|----------|----------|
| Azure IR | Azure regions (auto-resolve or fixed) | Cloud-to-cloud movement and data flows |
| Self-Hosted IR | Customer network (VM/container) | On-premises, private network sources |
| Azure-SSIS IR | Azure (managed SSIS cluster) | Lift-and-shift SSIS packages |

Self-hosted IR security considerations:
- Runs as a Windows service under a dedicated service account
- Communicates outbound via HTTPS (port 443) — no inbound ports required
- Credential encryption uses DPAPI tied to the IR node
- HA mode: 2-4 nodes sharing a single logical IR registration

```powershell
# Register self-hosted IR node
$key = Get-AzDataFactoryV2IntegrationRuntimeKey `
  -ResourceGroupName "rg-data" `
  -DataFactoryName "adf-production" `
  -Name "ir-onprem-sales"

# On the on-premises server:
.\IntegrationRuntime.exe -key $key.AuthKey1
```

### Data Flows

#### Mapping Data Flows
Visual, code-free transformations compiled to Spark. Support:
- Source/Sink, Filter, Select, Derived Column, Aggregate, Join, Lookup, Union, Conditional Split, Alter Row, Window, Rank, Pivot/Unpivot, Flatten, Parse, Stringify

#### Wrangling Data Flows
Power Query Online (M language) for self-service prep. Limited to simpler transformations.

### Triggers

| Trigger Type | Mechanism | Example |
|--------------|-----------|---------|
| Schedule | Cron-like (wall clock) | Daily at 02:00 UTC |
| Tumbling Window | Fixed-size, non-overlapping intervals | Every 1 hour, backfill capable |
| Event (Blob) | Blob created/deleted in storage account | New file in `/raw/sales/` |
| Custom Event | Event Grid custom topic | Application-emitted event |

```json
{
  "name": "TriggerOnNewSalesFile",
  "properties": {
    "type": "BlobEventsTrigger",
    "typeProperties": {
      "blobPathBeginsWith": "/bronze/raw/sales/",
      "blobPathEndsWith": ".parquet",
      "ignoreEmptyBlobs": true,
      "scope": "/subscriptions/.../storageAccounts/mystorageaccount",
      "events": ["Microsoft.Storage.BlobCreated"]
    },
    "pipelines": [
      { "pipelineReference": { "referenceName": "ProcessSalesFile", "type": "PipelineReference" } }
    ]
  }
}
```

### Credential Management

ADF supports multiple credential types:

1. **Managed Identity** (recommended): System-assigned or user-assigned
2. **Azure Key Vault linked service**: Secrets stored in Key Vault, referenced dynamically
3. **Credential stored in ADF**: Encrypted at rest, but less auditable

```json
{
  "name": "LinkedService_ADLS",
  "properties": {
    "type": "AzureBlobFS",
    "typeProperties": {
      "url": "https://mystorageaccount.dfs.core.windows.net"
    },
    "connectVia": { "referenceName": "AutoResolveIR", "type": "IntegrationRuntimeReference" },
    "credential": {
      "referenceName": "ManagedIdentityCredential",
      "type": "CredentialReference"
    }
  }
}
```

### Managed VNet and Data Exfiltration Protection

```bash
# Create ADF with managed VNet
az datafactory create \
  --resource-group rg-data \
  --factory-name adf-secure \
  --location westeurope \
  --global-parameter-type "String" \
  --global-parameter-value "prod"

# Create managed private endpoint to ADLS
az datafactory managed-private-endpoint create \
  --resource-group rg-data \
  --factory-name adf-secure \
  --managed-private-endpoint-name mpe-adls \
  --group-id dfs \
  --private-link-resource-id "/subscriptions/.../storageAccounts/mystorageaccount"
```

---

## 5. Azure Databricks

### Unity Catalog

Unity Catalog is Databricks' unified governance layer providing:
- Three-level namespace: `catalog.schema.table`
- Centralized access control (grants, row-level security, column masking)
- Cross-workspace governance
- Automated lineage tracking
- Data sharing via Delta Sharing protocol

Hierarchy:
```
Metastore (account-level)
  └── Catalog (logical grouping, e.g., "production", "staging")
       └── Schema (database equivalent)
            └── Table / View / Function / Volume / Model
```

```sql
-- Create catalog and schema
CREATE CATALOG IF NOT EXISTS production;
CREATE SCHEMA IF NOT EXISTS production.sales;

-- Create managed table (data stored in metastore root)
CREATE TABLE production.sales.transactions (
  transaction_id BIGINT GENERATED ALWAYS AS IDENTITY,
  customer_id BIGINT NOT NULL,
  amount DECIMAL(18,2) NOT NULL,
  transaction_date TIMESTAMP NOT NULL,
  region STRING NOT NULL
)
USING DELTA
PARTITIONED BY (region)
COMMENT 'Production sales transactions';

-- Grant access
GRANT USE CATALOG ON CATALOG production TO `data-analysts@company.com`;
GRANT USE SCHEMA ON SCHEMA production.sales TO `data-analysts@company.com`;
GRANT SELECT ON TABLE production.sales.transactions TO `data-analysts@company.com`;

-- Column masking for PII
CREATE FUNCTION production.sales.mask_customer_id(customer_id BIGINT)
RETURNS BIGINT
RETURN CASE
  WHEN is_account_group_member('data-engineers') THEN customer_id
  ELSE 0
END;

ALTER TABLE production.sales.transactions
ALTER COLUMN customer_id SET MASK production.sales.mask_customer_id;
```

### Delta Lake on Azure

Delta Lake provides ACID transactions, schema enforcement, time travel, and Z-ordering on top of ADLS Gen2:

```python
from delta.tables import DeltaTable
from pyspark.sql.functions import col, current_timestamp

# Upsert (MERGE) pattern
source_df = spark.read.format("parquet").load(
    "abfss://bronze@account.dfs.core.windows.net/raw/customers_incremental/"
)

target_table = DeltaTable.forPath(
    spark, "abfss://silver@account.dfs.core.windows.net/curated/customers/"
)

(target_table.alias("target")
    .merge(source_df.alias("source"), "target.customer_id = source.customer_id")
    .whenMatchedUpdate(set={
        "name": "source.name",
        "email": "source.email",
        "updated_at": current_timestamp()
    })
    .whenNotMatchedInsertAll()
    .execute()
)

# Optimize and Z-Order for query performance
spark.sql("""
    OPTIMIZE production.sales.transactions
    ZORDER BY (customer_id, transaction_date)
""")

# Time travel
df_yesterday = spark.read.format("delta").option("timestampAsOf", "2024-06-01").load(
    "abfss://silver@account.dfs.core.windows.net/curated/customers/"
)
```

### Cluster Policies

Cluster policies enforce governance on compute resources:

```json
{
  "name": "DataEngineeringPolicy",
  "definition": {
    "spark_version": { "type": "fixed", "value": "14.3.x-scala2.12" },
    "node_type_id": { "type": "allowlist", "values": ["Standard_D4ds_v5", "Standard_D8ds_v5"] },
    "num_workers": { "type": "range", "minValue": 1, "maxValue": 10 },
    "autotermination_minutes": { "type": "fixed", "value": 30 },
    "custom_tags.team": { "type": "fixed", "value": "data-engineering" },
    "spark_conf.spark.databricks.cluster.profile": { "type": "fixed", "value": "serverless" },
    "azure_attributes.availability": { "type": "fixed", "value": "ON_DEMAND_AZURE" }
  }
}
```

### Access Control

#### Table ACLs (Legacy)
Table ACLs provide SQL-level GRANT/REVOKE on tables within a workspace. Superseded by Unity Catalog but still present in legacy deployments.

#### Unity Catalog Permissions

| Privilege | Object | Effect |
|-----------|--------|--------|
| USE CATALOG | Catalog | Can access the catalog |
| USE SCHEMA | Schema | Can access the schema |
| SELECT | Table/View | Read data |
| MODIFY | Table | Insert, Update, Delete |
| CREATE TABLE | Schema | Create new tables |
| ALL PRIVILEGES | Any | Full control |
| EXECUTE | Function | Run function |

### Secret Scopes

Two backends:

1. **Databricks-backed**: Secrets stored in Databricks control plane (AES-256)
2. **Azure Key Vault-backed**: Secrets stored in Key Vault, Databricks proxies access

```python
# Create Key Vault-backed secret scope
import requests

databricks_host = "https://adb-123456789.10.azuredatabricks.net"
token = dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiToken().get()

payload = {
    "scope": "kv-production",
    "scope_backend_type": "AZURE_KEYVAULT",
    "backend_azure_keyvault": {
        "resource_id": "/subscriptions/.../resourceGroups/rg-data/providers/Microsoft.KeyVault/vaults/kv-prod",
        "dns_name": "https://kv-prod.vault.azure.net/"
    }
}

response = requests.post(
    f"{databricks_host}/api/2.0/secrets/scopes/create",
    headers={"Authorization": f"Bearer {token}"},
    json=payload
)

# Use secret in notebook
storage_key = dbutils.secrets.get(scope="kv-production", key="adls-access-key")
```

### Network Security

#### Private Link (No Public IP)

```terraform
resource "azurerm_databricks_workspace" "secure" {
  name                        = "dbw-secure-prod"
  resource_group_name         = azurerm_resource_group.rg.name
  location                    = azurerm_resource_group.rg.location
  sku                         = "premium"
  managed_resource_group_name = "rg-dbw-managed-prod"

  public_network_access_enabled         = false
  network_security_group_rules_required = "NoAzureDatabricksRules"

  custom_parameters {
    no_public_ip                                         = true
    virtual_network_id                                   = azurerm_virtual_network.vnet.id
    private_subnet_name                                  = azurerm_subnet.private.name
    public_subnet_name                                   = azurerm_subnet.public.name
    private_subnet_network_security_group_association_id = azurerm_subnet_network_security_group_association.private.id
    public_subnet_network_security_group_association_id  = azurerm_subnet_network_security_group_association.public.id
  }
}

resource "azurerm_private_endpoint" "dbw_ui" {
  name                = "pe-dbw-ui"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  subnet_id           = azurerm_subnet.private_endpoints.id

  private_service_connection {
    name                           = "psc-dbw-ui"
    private_connection_resource_id = azurerm_databricks_workspace.secure.id
    subresource_names              = ["databricks_ui_api"]
    is_manual_connection           = false
  }
}
```

#### IP Access Lists

```bash
# Restrict workspace access to corporate IPs
curl -X POST "https://adb-123456789.10.azuredatabricks.net/api/2.0/ip-access-lists" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "label": "Corporate VPN",
    "list_type": "ALLOW",
    "ip_addresses": ["198.51.100.0/24", "203.0.113.0/24"]
  }'
```

---

## 6. Streaming and Events

### Azure Event Hubs

Event Hubs is a fully managed, partitioned streaming platform designed for high-throughput event ingestion.

#### Core Concepts

| Concept | Description |
|---------|-------------|
| Namespace | Container for one or more Event Hubs (TLS endpoint) |
| Event Hub | Analogous to a Kafka topic |
| Partition | Ordered sequence of events within a hub (1-32 default, up to 1024 premium) |
| Consumer Group | Independent view of the event stream (max 5 in Standard, 100 in Premium) |
| Partition Key | Determines partition assignment for ordering guarantees |
| Capture | Auto-archive to ADLS Gen2 or Blob in Avro format |

#### Provisioning

```bicep
resource eventHubNamespace 'Microsoft.EventHub/namespaces@2023-01-01-preview' = {
  name: namespaceName
  location: location
  sku: { name: 'Premium', tier: 'Premium', capacity: 1 }
  properties: {
    minimumTlsVersion: '1.2'
    publicNetworkAccess: 'Disabled'
    disableLocalAuth: true  // Force Entra ID auth only
    kafkaEnabled: true
    zoneRedundant: true
  }
}

resource eventHub 'Microsoft.EventHub/namespaces/eventhubs@2023-01-01-preview' = {
  parent: eventHubNamespace
  name: 'telemetry-events'
  properties: {
    partitionCount: 8
    messageRetentionInDays: 7
    captureDescription: {
      enabled: true
      encoding: 'Avro'
      intervalInSeconds: 300
      sizeLimitInBytes: 314572800
      destination: {
        name: 'EventHubArchive.AzureBlockBlob'
        properties: {
          storageAccountResourceId: storageAccountId
          blobContainer: 'eventhub-capture'
          archiveNameFormat: '{Namespace}/{EventHub}/{PartitionId}/{Year}/{Month}/{Day}/{Hour}/{Minute}/{Second}'
        }
      }
    }
  }
}
```

#### Schema Registry

Event Hubs Schema Registry provides centralized schema management with Avro serialization:

```python
from azure.schemaregistry import SchemaRegistryClient
from azure.schemaregistry.serializer.avroserializer import AvroSerializer
from azure.identity import DefaultAzureCredential
from azure.eventhub import EventHubProducerClient, EventData

credential = DefaultAzureCredential()

schema_registry_client = SchemaRegistryClient(
    fully_qualified_namespace="ehns-prod.servicebus.windows.net",
    credential=credential
)

avro_serializer = AvroSerializer(
    client=schema_registry_client,
    group_name="telemetry-schemas",
    auto_register=False  # Enforce schema governance
)

# Serialize event with schema validation
event_data = {
    "device_id": "sensor-42",
    "temperature": 23.5,
    "timestamp": "2024-06-01T12:00:00Z"
}

schema = """
{
  "type": "record",
  "name": "TelemetryEvent",
  "namespace": "com.company.telemetry",
  "fields": [
    {"name": "device_id", "type": "string"},
    {"name": "temperature", "type": "double"},
    {"name": "timestamp", "type": "string"}
  ]
}
"""

serialized = avro_serializer.serialize(event_data, schema=schema)

# Send to Event Hub
producer = EventHubProducerClient(
    fully_qualified_namespace="ehns-prod.servicebus.windows.net",
    eventhub_name="telemetry-events",
    credential=credential
)

with producer:
    batch = producer.create_batch()
    batch.add(EventData(body=serialized))
    producer.send_batch(batch)
```

### Azure Stream Analytics

ASA provides real-time event processing with a SQL-like declarative language.

#### Windowing Functions

```sql
-- Tumbling window: non-overlapping, fixed-size
SELECT
    device_id,
    AVG(temperature) AS avg_temp,
    MAX(temperature) AS max_temp,
    COUNT(*) AS reading_count,
    System.Timestamp() AS window_end
INTO [output-anomalies]
FROM [input-telemetry] TIMESTAMP BY event_time
GROUP BY device_id, TumblingWindow(minute, 5)
HAVING AVG(temperature) > 80;

-- Hopping window: overlapping windows
SELECT
    region,
    SUM(order_amount) AS rolling_revenue,
    System.Timestamp() AS window_end
INTO [output-revenue]
FROM [input-orders] TIMESTAMP BY order_time
GROUP BY region, HoppingWindow(minute, 60, 5);

-- Session window: groups events by activity period
SELECT
    user_id,
    COUNT(*) AS click_count,
    DATEDIFF(second, MIN(event_time), MAX(event_time)) AS session_duration_sec
INTO [output-sessions]
FROM [input-clickstream] TIMESTAMP BY event_time
GROUP BY user_id, SessionWindow(minute, 5, 30);

-- Sliding window: fires on every event within the window
SELECT
    sensor_id,
    AVG(pressure) AS avg_pressure
INTO [output-alerts]
FROM [input-sensors] TIMESTAMP BY reading_time
GROUP BY sensor_id, SlidingWindow(second, 30)
HAVING AVG(pressure) > 150;
```

#### Reference Data Join

```sql
-- Enrich streaming data with static reference
SELECT
    s.device_id,
    s.temperature,
    r.location_name,
    r.threshold_celsius,
    CASE WHEN s.temperature > r.threshold_celsius THEN 'ALERT' ELSE 'NORMAL' END AS status
INTO [output-enriched]
FROM [input-telemetry] s TIMESTAMP BY event_time
JOIN [reference-devices] r ON s.device_id = r.device_id;
```

#### Output Sinks

ASA can write to: Event Hub, ADLS Gen2, Blob Storage, Azure SQL Database, Cosmos DB, Power BI, Synapse Analytics, Azure Table Storage, Service Bus, Azure Functions.

### Kafka on Event Hubs

Event Hubs Premium/Dedicated exposes a Kafka-compatible endpoint (protocol 0.10+):

```properties
# Kafka producer configuration for Event Hubs
bootstrap.servers=ehns-prod.servicebus.windows.net:9093
security.protocol=SASL_SSL
sasl.mechanism=OAUTHBEARER
sasl.jaas.config=org.apache.kafka.common.security.oauthbearer.OAuthBearerLoginModule required;
sasl.login.callback.handler.class=com.azure.identity.extensions.kafka.AzureIdentityLoginCallbackHandler
```

```python
from confluent_kafka import Producer
from azure.identity import DefaultAzureCredential

def get_oauth_token(config):
    credential = DefaultAzureCredential()
    token = credential.get_token("https://ehns-prod.servicebus.windows.net/.default")
    return token.token, token.expires_on

producer_conf = {
    'bootstrap.servers': 'ehns-prod.servicebus.windows.net:9093',
    'security.protocol': 'SASL_SSL',
    'sasl.mechanism': 'OAUTHBEARER',
    'oauth_cb': get_oauth_token,
    'client.id': 'data-pipeline-producer'
}

producer = Producer(producer_conf)
producer.produce('telemetry-events', key='sensor-42', value=b'{"temp": 23.5}')
producer.flush()
```

### Real-Time Dashboards with Power BI

ASA streaming datasets in Power BI enable sub-second refresh dashboards:

```sql
-- ASA query outputting to Power BI
SELECT
    region,
    COUNT(*) AS order_count,
    SUM(amount) AS total_revenue,
    System.Timestamp() AS event_time
INTO [powerbi-realtime]
FROM [input-orders] TIMESTAMP BY order_time
GROUP BY region, TumblingWindow(second, 10);
```

Power BI streaming dataset configuration:
- Dataset refresh: Push/Streaming
- Historical data analysis: Enabled (hybrid mode)
- Tile refresh rate: 1 second for streaming datasets

---

## 7. Security Architecture

### Entra ID Authentication

All Azure data services authenticate through Entra ID (formerly Azure AD). Authentication flows:

1. **User principals**: Interactive login, MFA-enforced, conditional access policies
2. **Service principals**: App registrations with certificates (preferred) or secrets
3. **Managed identities**: Azure-managed credentials with automatic rotation

```python
from azure.identity import (
    DefaultAzureCredential,
    ManagedIdentityCredential,
    ClientCertificateCredential
)

# Production: system-assigned managed identity
credential = ManagedIdentityCredential()

# Production: user-assigned managed identity
credential = ManagedIdentityCredential(
    client_id="12345678-abcd-efgh-ijkl-123456789012"
)

# CI/CD: service principal with certificate (preferred over secret)
credential = ClientCertificateCredential(
    tenant_id="<tenant-id>",
    client_id="<app-id>",
    certificate_path="/var/run/secrets/sp-cert.pem"
)

# Development only: DefaultAzureCredential chain
credential = DefaultAzureCredential()
```

### Managed Identities

| Type | Lifecycle | Use Case |
|------|-----------|----------|
| System-assigned | Tied to Azure resource; created/deleted with resource | Single-resource identity; Synapse workspace, ADF, Databricks |
| User-assigned | Independent resource; explicit lifecycle | Shared across multiple resources; consistent identity for cross-service access |

```terraform
# User-assigned managed identity for data platform
resource "azurerm_user_assigned_identity" "data_platform" {
  name                = "id-data-platform-prod"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
}

# Assign to multiple services
resource "azurerm_role_assignment" "adls_access" {
  scope                = azurerm_storage_account.datalake.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_user_assigned_identity.data_platform.principal_id
}

resource "azurerm_role_assignment" "keyvault_access" {
  scope                = azurerm_key_vault.platform.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_user_assigned_identity.data_platform.principal_id
}
```

### Azure Key Vault Integration

Key Vault serves as the central secrets, keys, and certificate store for all data services:

```bicep
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  properties: {
    sku: { family: 'A', name: 'premium' }  // HSM-backed keys
    tenantId: subscription().tenantId
    enableRbacAuthorization: true  // Prefer RBAC over access policies
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
    enablePurgeProtection: true  // Prevent accidental permanent deletion
    publicNetworkAccess: 'Disabled'
    networkAcls: {
      defaultAction: 'Deny'
      bypass: 'AzureServices'
    }
  }
}
```

### Private Endpoints and Private Link

Private Link eliminates public internet exposure for data services:

```terraform
# Central Private DNS Zone structure
locals {
  private_dns_zones = {
    "blob"       = "privatelink.blob.core.windows.net"
    "dfs"        = "privatelink.dfs.core.windows.net"
    "sql"        = "privatelink.sql.azuresynapse.net"
    "dev"        = "privatelink.dev.azuresynapse.net"
    "vault"      = "privatelink.vaultcore.azure.net"
    "databricks" = "privatelink.azuredatabricks.net"
    "eventhub"   = "privatelink.servicebus.windows.net"
    "cosmos"     = "privatelink.documents.azure.com"
  }
}

resource "azurerm_private_dns_zone" "zones" {
  for_each            = local.private_dns_zones
  name                = each.value
  resource_group_name = azurerm_resource_group.networking.name
}

resource "azurerm_private_dns_zone_virtual_network_link" "links" {
  for_each              = local.private_dns_zones
  name                  = "link-${each.key}"
  resource_group_name   = azurerm_resource_group.networking.name
  private_dns_zone_name = azurerm_private_dns_zone.zones[each.key].name
  virtual_network_id    = azurerm_virtual_network.hub.id
}
```

### Network Security Groups

```terraform
resource "azurerm_network_security_group" "data_subnet" {
  name                = "nsg-data-subnet"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name

  security_rule {
    name                       = "DenyInternetOutbound"
    priority                   = 4000
    direction                  = "Outbound"
    access                     = "Deny"
    protocol                   = "*"
    source_port_range          = "*"
    destination_port_range     = "*"
    source_address_prefix      = "*"
    destination_address_prefix = "Internet"
  }

  security_rule {
    name                       = "AllowPrivateEndpoints"
    priority                   = 100
    direction                  = "Outbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "443"
    source_address_prefix      = "VirtualNetwork"
    destination_address_prefix = "VirtualNetwork"
  }
}
```

### Microsoft Defender for Data Services

```bash
# Enable Defender for Storage
az security pricing create \
  --name StorageAccounts \
  --tier Standard \
  --subplan PerStorageAccount

# Enable Defender for SQL
az security pricing create \
  --name SqlServers \
  --tier Standard

# Enable Defender for Cosmos DB
az security pricing create \
  --name CosmosDbs \
  --tier Standard

# Enable Defender for Key Vault
az security pricing create \
  --name KeyVaults \
  --tier Standard
```

Defender detects:
- Anomalous access patterns (unusual geo, time, volume)
- Potential data exfiltration
- Brute-force attacks on storage accounts
- SQL injection attempts
- Suspicious Key Vault access
- Malware uploads to storage

### Azure Policy for Data Governance

```json
{
  "mode": "All",
  "policyRule": {
    "if": {
      "allOf": [
        {
          "field": "type",
          "equals": "Microsoft.Storage/storageAccounts"
        },
        {
          "field": "Microsoft.Storage/storageAccounts/allowBlobPublicAccess",
          "notEquals": false
        }
      ]
    },
    "then": {
      "effect": "deny"
    }
  },
  "parameters": {}
}
```

Common data platform policies:
- Deny storage accounts with public blob access
- Require minimum TLS 1.2
- Require private endpoints for all data services
- Deny unencrypted storage accounts
- Require diagnostic settings on all data resources
- Deny Synapse workspaces without managed VNet
- Require Unity Catalog on Databricks workspaces

---

## 8. Security Assessment

### Storage Account Misconfigurations

#### Public Blob Access

The most common misconfiguration. When `allowBlobPublicAccess` is `true` and a container's access level is set to `Blob` or `Container`, data is exposed to the internet.

```bash
# Enumerate storage accounts with public access enabled
az storage account list --query "[?allowBlobPublicAccess==true].{name:name,rg:resourceGroup}" -o table

# Check container-level access
az storage container list \
  --account-name $STORAGE_ACCOUNT \
  --query "[?properties.publicAccess!='None'].{name:name,access:properties.publicAccess}" -o table

# Verify from external perspective (no auth)
curl -s "https://$STORAGE_ACCOUNT.blob.core.windows.net/$CONTAINER?restype=container&comp=list" | head -50
```

#### Shared Access Signature (SAS) Abuse

SAS tokens grant delegated access but are frequently over-privileged:

```python
# Security assessment: check for overly permissive SAS tokens
# Common issues:
# 1. No IP restriction
# 2. No HTTPS-only restriction
# 3. Excessive permissions (rwdlac vs needed read-only)
# 4. Excessive validity period (years vs hours)
# 5. Account-level SAS (full account access)
# 6. No signed identifier (cannot be revoked individually)

from datetime import datetime, timedelta
from azure.storage.blob import (
    generate_account_sas, ResourceTypes, AccountSasPermissions
)

# INSECURE: overly broad SAS (anti-pattern for documentation)
insecure_sas = generate_account_sas(
    account_name="target",
    account_key="<key>",
    resource_types=ResourceTypes(container=True, object=True, service=True),
    permission=AccountSasPermissions(
        read=True, write=True, delete=True, list=True,
        add=True, create=True, update=True, process=True
    ),
    expiry=datetime.utcnow() + timedelta(days=365),  # 1 year validity
    # No ip= restriction
    # No protocol='https'
)

# SECURE: minimal-privilege SAS
secure_sas = generate_account_sas(
    account_name="target",
    account_key="<key>",
    resource_types=ResourceTypes(object=True),
    permission=AccountSasPermissions(read=True),
    expiry=datetime.utcnow() + timedelta(hours=1),
    ip="198.51.100.0-198.51.100.255",
    protocol="https"
)
```

#### Account Key Exposure

Storage account keys provide full administrative access. If exposed:

```bash
# Rotate keys immediately
az storage account keys renew --account-name $ACCOUNT --key primary
az storage account keys renew --account-name $ACCOUNT --key secondary

# Disable shared key access entirely (force Entra ID)
az storage account update \
  --name $ACCOUNT \
  --resource-group $RG \
  --allow-shared-key-access false
```

### Synapse Credential Theft

#### Attack Vectors

1. **Linked service credential extraction**: Synapse stores credentials for linked services; SQL injection or notebook code execution can extract them
2. **Managed identity token theft**: Spark notebooks can request tokens for the workspace managed identity
3. **Credential passthrough abuse**: User identity delegation may grant broader access than intended

```python
# Demonstrating managed identity token acquisition from Spark notebook
# (authorized pentest scenario)
import requests

# Azure IMDS endpoint available within Synapse Spark
token_url = "http://169.254.169.254/metadata/identity/oauth2/token"
params = {
    "api-version": "2019-08-01",
    "resource": "https://storage.azure.com/"
}
headers = {"Metadata": "true"}

response = requests.get(token_url, params=params, headers=headers)
token = response.json()["access_token"]

# This token can access any storage account the managed identity has permissions on
# Mitigation: principle of least privilege on managed identity RBAC assignments
```

#### Mitigations

- Enable managed VNet with data exfiltration protection
- Use workspace-managed private endpoints exclusively
- Restrict notebook execution to approved users via Synapse RBAC
- Monitor credential access via diagnostic logs
- Implement conditional access policies for Synapse workspace access

### Data Factory Pipeline Injection

#### Attack Surface

1. **Expression injection**: Dynamic content expressions (`@pipeline().parameters.x`) that construct SQL queries or file paths without sanitization
2. **Self-hosted IR compromise**: The on-premises IR machine is a high-value target; compromising it yields access to all connected sources
3. **Linked service secrets**: Stored in ADF configuration; extractable via ARM API with Contributor role

```json
// VULNERABLE: SQL injection via unsanitized parameter
{
  "source": {
    "type": "SqlServerSource",
    "sqlReaderQuery": "SELECT * FROM orders WHERE region = '@{pipeline().parameters.region}'"
  }
}

// SECURE: parameterized query
{
  "source": {
    "type": "SqlServerSource",
    "sqlReaderQuery": "SELECT * FROM orders WHERE region = @region",
    "queryParameters": {
      "region": { "value": "@pipeline().parameters.region", "type": "String" }
    }
  }
}
```

#### Self-Hosted IR Hardening

```powershell
# Assess self-hosted IR security
# Check: runs as dedicated service account (not LocalSystem)
Get-WmiObject Win32_Service | Where-Object { $_.Name -like "*IntegrationRuntime*" } | 
  Select-Object Name, StartName, State

# Check: DPAPI credential protection scope
# IR stores credentials encrypted via DPAPI tied to the machine
# If the machine is compromised, credentials can be decrypted

# Hardening checklist:
# 1. Dedicated VM, no other workloads
# 2. No internet access except Azure relay (ServiceBus)
# 3. Windows Defender Application Control (WDAC)
# 4. Credential Guard enabled
# 5. Network segmentation (separate VLAN)
# 6. Regular patching cadence
# 7. Azure Arc monitoring
```

### Databricks Notebook Credential Extraction

#### Attack Vectors

1. **Secret scope enumeration**: Users with `READ` on a secret scope can list secret keys (not values)
2. **Credential leakage via output**: Notebook outputs may display credentials in cell results
3. **Cluster log exposure**: Spark driver/executor logs may contain credentials passed as Spark conf
4. **init script injection**: Cluster init scripts execute as root; can install keyloggers or exfiltrate secrets

```python
# Pentest: enumerate accessible secret scopes and keys
import requests

host = "https://adb-123456789.10.azuredatabricks.net"
token = "<compromised-token>"

# List all secret scopes
scopes = requests.get(
    f"{host}/api/2.0/secrets/scopes/list",
    headers={"Authorization": f"Bearer {token}"}
).json()

for scope in scopes.get("scopes", []):
    # List keys within each scope
    keys = requests.get(
        f"{host}/api/2.0/secrets/list",
        headers={"Authorization": f"Bearer {token}"},
        params={"scope": scope["name"]}
    ).json()
    print(f"Scope: {scope['name']}, Keys: {[k['key'] for k in keys.get('secrets', [])]}")
```

#### Mitigations

- Use Unity Catalog for all data access (eliminates direct storage credential need)
- Restrict secret scope permissions (only grant to service principals, not users)
- Enable cluster log delivery to locked-down storage (immutable)
- Disable init script execution on production clusters
- Enable IP access lists to restrict workspace access
- Monitor via Azure Databricks audit logs

### Event Hub SAS Key Exposure

```bash
# Check: are SAS keys rotated recently?
az eventhubs namespace authorization-rule keys list \
  --resource-group $RG \
  --namespace-name $NAMESPACE \
  --name RootManageSharedAccessKey

# Mitigation: disable local auth (force Entra ID)
az eventhubs namespace update \
  --resource-group $RG \
  --name $NAMESPACE \
  --disable-local-auth true

# Rotate keys if compromised
az eventhubs namespace authorization-rule keys renew \
  --resource-group $RG \
  --namespace-name $NAMESPACE \
  --name RootManageSharedAccessKey \
  --key PrimaryKey
```

### Managed Identity Abuse

If an attacker gains code execution on an Azure resource with a managed identity:

```python
# From compromised Azure VM/container/function with managed identity
import requests

# Acquire token for any resource the identity has access to
targets = [
    "https://storage.azure.com/",
    "https://vault.azure.net",
    "https://database.windows.net/",
    "https://management.azure.com/",
    "https://graph.microsoft.com/"
]

for resource in targets:
    try:
        resp = requests.get(
            "http://169.254.169.254/metadata/identity/oauth2/token",
            params={"api-version": "2019-08-01", "resource": resource},
            headers={"Metadata": "true"},
            timeout=2
        )
        if resp.status_code == 200:
            token_data = resp.json()
            print(f"[+] Token acquired for: {resource}")
            print(f"    Expires: {token_data.get('expires_on')}")
            # Attacker can now use this token to access the resource
    except Exception:
        pass
```

#### Defense

- Apply strict least-privilege RBAC to managed identities
- Use Conditional Access for workload identities (Preview/GA depending on timing)
- Monitor token acquisition patterns via Entra ID sign-in logs
- Implement JIT (Just-In-Time) access for sensitive resources
- Network isolation: ensure managed identity can only reach intended targets

### Azure AD Privilege Escalation via Data Services

Attack chains leveraging data services for privilege escalation:

1. **ADF Contributor → Storage access**: ADF Contributor can create pipelines using the ADF managed identity, which often has broad storage access
2. **Synapse Contributor → SQL Admin**: Can create SQL scripts executing as the workspace managed identity
3. **Databricks workspace admin → Subscription-level access**: If workspace managed identity has over-privileged RBAC, workspace admin can leverage it
4. **Key Vault access via data service**: Compromising a data service with Key Vault access yields all secrets in that vault

```bash
# Enumerate role assignments for data service managed identities
az role assignment list \
  --assignee $SYNAPSE_MI_OBJECT_ID \
  --all \
  --output table

az role assignment list \
  --assignee $ADF_MI_OBJECT_ID \
  --all \
  --output table

az role assignment list \
  --assignee $DATABRICKS_MI_OBJECT_ID \
  --all \
  --output table
```

---

## 9. Monitoring and Compliance

### Azure Monitor

#### Diagnostic Settings

Every data service must have diagnostic settings configured to capture:
- **Metrics**: Performance counters (latency, throughput, errors)
- **Logs**: Activity logs, resource logs (audit, data plane operations)
- **Destination**: Log Analytics workspace (primary), Storage account (archive), Event Hub (SIEM forwarding)

```terraform
resource "azurerm_monitor_diagnostic_setting" "adls_diagnostics" {
  name                       = "diag-adls-to-law"
  target_resource_id         = azurerm_storage_account.datalake.id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.platform.id

  enabled_log {
    category = "StorageRead"
  }
  enabled_log {
    category = "StorageWrite"
  }
  enabled_log {
    category = "StorageDelete"
  }
  metric {
    category = "Transaction"
  }
  metric {
    category = "Capacity"
  }
}

resource "azurerm_monitor_diagnostic_setting" "synapse_diagnostics" {
  name                       = "diag-synapse-to-law"
  target_resource_id         = azurerm_synapse_workspace.main.id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.platform.id

  enabled_log {
    category = "SynapseRbacOperations"
  }
  enabled_log {
    category = "GatewayApiRequests"
  }
  enabled_log {
    category = "SQLSecurityAuditEvents"
  }
  enabled_log {
    category = "BuiltinSqlReqsEnded"
  }
  metric {
    category = "AllMetrics"
  }
}
```

#### Alert Rules

```bicep
resource alertDataExfiltration 'Microsoft.Insights/metricAlerts@2018-03-01' = {
  name: 'alert-adls-high-egress'
  location: 'global'
  properties: {
    severity: 2
    enabled: true
    scopes: [storageAccount.id]
    evaluationFrequency: 'PT5M'
    windowSize: 'PT1H'
    criteria: {
      'odata.type': 'Microsoft.Azure.Monitor.SingleResourceMultipleMetricCriteria'
      allOf: [
        {
          name: 'high_egress'
          metricName: 'Egress'
          operator: 'GreaterThan'
          threshold: 10737418240  // 10 GB in 1 hour
          timeAggregation: 'Total'
        }
      ]
    }
    actions: [
      { actionGroupId: securityActionGroup.id }
    ]
  }
}
```

### Log Analytics Workspace

```kusto
// Query: identify unusual storage access patterns
StorageBlobLogs
| where TimeGenerated > ago(24h)
| where OperationName == "GetBlob"
| where StatusCode == 200
| summarize 
    TotalBytes = sum(ResponseBodySize),
    RequestCount = count(),
    DistinctFiles = dcount(ObjectKey)
    by CallerIpAddress, AccountName, bin(TimeGenerated, 1h)
| where TotalBytes > 1073741824  // > 1GB in 1 hour
| order by TotalBytes desc

// Query: failed authentication attempts to data services
SigninLogs
| where TimeGenerated > ago(7d)
| where ResourceDisplayName has_any ("Storage", "Synapse", "Databricks", "Data Factory")
| where ResultType != "0"
| summarize FailedAttempts = count() by UserPrincipalName, AppDisplayName, ResourceDisplayName, IPAddress
| where FailedAttempts > 10
| order by FailedAttempts desc

// Query: Key Vault secret access audit
AzureDiagnostics
| where ResourceProvider == "MICROSOFT.KEYVAULT"
| where OperationName == "SecretGet"
| where TimeGenerated > ago(24h)
| summarize AccessCount = count() by CallerIPAddress, identity_claim_upn_s, id_s
| where AccessCount > 50
| order by AccessCount desc
```

### Microsoft Sentinel for Data Services

Sentinel provides SIEM+SOAR capabilities built on Log Analytics. Custom analytics rules for data platform security:

```kusto
// Sentinel Analytics Rule: Mass data download from ADLS
// Frequency: Every 5 minutes
// Lookback: 1 hour
let threshold_bytes = 5368709120;  // 5 GB
StorageBlobLogs
| where TimeGenerated > ago(1h)
| where OperationName in ("GetBlob", "GetBlobProperties")
| where StatusCode == 200
| summarize 
    TotalEgress = sum(ResponseBodySize),
    FileCount = dcount(ObjectKey),
    Operations = count()
    by CallerIpAddress, AccountName, UserAgentHeader
| where TotalEgress > threshold_bytes
| extend AlertSeverity = case(
    TotalEgress > 53687091200, "High",    // > 50 GB
    TotalEgress > 10737418240, "Medium",  // > 10 GB
    "Low"
)

// Sentinel Analytics Rule: Synapse SQL suspicious queries
SynapseSqlAuditEvents
| where TimeGenerated > ago(1h)
| where Statement has_any (
    "OPENROWSET", "BULK", "EXTERNAL",
    "xp_cmdshell", "sp_execute_external_script"
)
| where ClientIp !in (known_good_ips)
| project TimeGenerated, ClientIp, LoginName, Statement, DatabaseName
```

#### Sentinel Automation (SOAR)

```json
{
  "definition": {
    "triggers": {
      "Microsoft_Sentinel_incident": {
        "type": "ApiConnectionWebhook",
        "inputs": {
          "body": { "incidentId": "@triggerBody()?['object']?['id']" }
        }
      }
    },
    "actions": {
      "Block_storage_access": {
        "type": "ApiConnection",
        "inputs": {
          "method": "PUT",
          "path": "/subscriptions/@{variables('subscriptionId')}/resourceGroups/@{variables('rgName')}/providers/Microsoft.Storage/storageAccounts/@{variables('accountName')}/networkAcls",
          "body": {
            "defaultAction": "Deny",
            "ipRules": []
          }
        }
      },
      "Notify_security_team": {
        "type": "ApiConnection",
        "inputs": {
          "method": "POST",
          "path": "/v2/teams/@{variables('teamsChannelId')}/messages",
          "body": {
            "content": "ALERT: Data exfiltration detected on @{variables('accountName')}"
          }
        }
      }
    }
  }
}
```

### Azure Activity Log

Activity Log captures control-plane operations (resource creation, modification, deletion, role assignments):

```kusto
// Monitor for dangerous role assignments on data resources
AzureActivity
| where TimeGenerated > ago(24h)
| where OperationNameValue == "MICROSOFT.AUTHORIZATION/ROLEASSIGNMENTS/WRITE"
| where ActivityStatusValue == "Success"
| extend Props = parse_json(Properties)
| extend RoleId = tostring(Props.requestbody.properties.roleDefinitionId)
| where RoleId has_any (
    "b7e6dc6d-f1e8-4753-8033-0f276bb0955b",  // Storage Blob Data Owner
    "ba92f5b4-2d11-453d-a403-e96b0029c9fe",  // Storage Blob Data Contributor
    "6e591065-9bad-43ed-90f3-e9424366d2f0"   // Synapse Administrator
)
| project TimeGenerated, Caller, ResourceId, RoleId
```

### Microsoft Purview

Purview provides unified data governance: discovery, classification, lineage, and access control.

#### Data Map and Scanning

```python
from azure.identity import DefaultAzureCredential
from azure.purview.scanning import PurviewScanningClient
from azure.purview.catalog import PurviewCatalogClient

credential = DefaultAzureCredential()

# Register a data source
scanning_client = PurviewScanningClient(
    endpoint="https://purview-prod.purview.azure.com",
    credential=credential
)

# Create ADLS Gen2 data source
data_source = {
    "kind": "AdlsGen2",
    "properties": {
        "endpoint": "https://mystorageaccount.dfs.core.windows.net/",
        "resourceGroup": "rg-data",
        "subscriptionId": "<subscription-id>",
        "location": "westeurope",
        "resourceName": "mystorageaccount"
    }
}

scanning_client.data_sources.create_or_update(
    data_source_name="adls-production",
    body=data_source
)
```

#### Classification Rules

Purview includes 200+ built-in classification rules (PII, financial, healthcare). Custom classifiers:

```json
{
  "name": "InternalProjectCode",
  "kind": "Custom",
  "properties": {
    "classificationName": "INTERNAL_PROJECT_CODE",
    "description": "Internal project identifiers (PRJ-XXXXX format)",
    "classificationAction": "Keep",
    "ruleStatus": "Enabled",
    "dataPatterns": [
      { "pattern": "PRJ-[0-9]{5}" }
    ],
    "columnPatterns": [
      { "pattern": "(?i)(project.?code|project.?id)" }
    ],
    "minimumPercentageMatch": 60
  }
}
```

#### Lineage

Purview automatically captures lineage from:
- ADF pipeline copy and data flow activities
- Synapse Spark notebooks (via OpenLineage)
- Databricks Unity Catalog (bi-directional integration)
- Power BI datasets and reports

### Compliance Certifications

Azure data services maintain compliance with:
- **SOC 1/2/3** (all services)
- **ISO 27001/27017/27018** (all services)
- **HIPAA BAA** (storage, Synapse, Databricks, Cosmos DB)
- **PCI DSS** (storage, SQL, Key Vault)
- **FedRAMP High** (select regions)
- **GDPR** (data residency, right to erasure)
- **CCPA** (data discovery via Purview)

#### Azure Blueprints for Data Platforms

```json
{
  "identity": { "type": "SystemAssigned" },
  "properties": {
    "displayName": "Secure Data Platform Blueprint",
    "description": "Enforce security baseline for data analytics workloads",
    "targetScope": "subscription",
    "parameters": {},
    "resourceGroups": {
      "rg-data-platform": {
        "location": "westeurope"
      }
    },
    "artifacts": [
      {
        "kind": "policyAssignment",
        "properties": {
          "policyDefinitionId": "/providers/Microsoft.Authorization/policySetDefinitions/1f3afdf9-d0c9-4c3d-847f-89da613e70a8",
          "displayName": "Azure Security Benchmark"
        }
      },
      {
        "kind": "policyAssignment",
        "properties": {
          "policyDefinitionId": "/providers/Microsoft.Authorization/policyDefinitions/34c877ad-507e-4c82-993e-3452a6e0ad3c",
          "displayName": "Storage accounts should restrict network access"
        }
      }
    ]
  }
}
```

---

## 10. Lab Exercises

### Lab 1: Build a Secure Lakehouse

**Objective**: Deploy ADLS Gen2 + Synapse + Purview with private endpoints, no public access.

#### Infrastructure (Terraform)

```terraform
terraform {
  required_providers {
    azurerm = { source = "hashicorp/azurerm", version = "~> 3.80" }
  }
}

provider "azurerm" {
  features {}
}

variable "location" { default = "westeurope" }
variable "prefix" { default = "lab-lakehouse" }

resource "azurerm_resource_group" "rg" {
  name     = "rg-${var.prefix}"
  location = var.location
}

# Virtual Network
resource "azurerm_virtual_network" "vnet" {
  name                = "vnet-${var.prefix}"
  location            = var.location
  resource_group_name = azurerm_resource_group.rg.name
  address_space       = ["10.0.0.0/16"]
}

resource "azurerm_subnet" "private_endpoints" {
  name                                      = "snet-private-endpoints"
  resource_group_name                       = azurerm_resource_group.rg.name
  virtual_network_name                      = azurerm_virtual_network.vnet.name
  address_prefixes                          = ["10.0.1.0/24"]
  private_endpoint_network_policies_enabled = true
}

resource "azurerm_subnet" "synapse" {
  name                 = "snet-synapse"
  resource_group_name  = azurerm_resource_group.rg.name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = ["10.0.2.0/24"]
}

# ADLS Gen2
resource "azurerm_storage_account" "datalake" {
  name                            = "stadlslakehouse01"
  resource_group_name             = azurerm_resource_group.rg.name
  location                        = var.location
  account_tier                    = "Standard"
  account_replication_type        = "ZRS"
  account_kind                    = "StorageV2"
  is_hns_enabled                  = true
  min_tls_version                 = "TLS1_2"
  allow_nested_items_to_be_public = false
  shared_access_key_enabled       = false  # Force Entra ID auth

  network_rules {
    default_action = "Deny"
    bypass         = ["AzureServices"]
  }

  identity {
    type = "SystemAssigned"
  }
}

resource "azurerm_storage_data_lake_gen2_filesystem" "bronze" {
  name               = "bronze"
  storage_account_id = azurerm_storage_account.datalake.id
}

resource "azurerm_storage_data_lake_gen2_filesystem" "silver" {
  name               = "silver"
  storage_account_id = azurerm_storage_account.datalake.id
}

resource "azurerm_storage_data_lake_gen2_filesystem" "gold" {
  name               = "gold"
  storage_account_id = azurerm_storage_account.datalake.id
}

# Private Endpoint for ADLS Gen2 (DFS)
resource "azurerm_private_dns_zone" "dfs" {
  name                = "privatelink.dfs.core.windows.net"
  resource_group_name = azurerm_resource_group.rg.name
}

resource "azurerm_private_dns_zone_virtual_network_link" "dfs_link" {
  name                  = "link-dfs"
  resource_group_name   = azurerm_resource_group.rg.name
  private_dns_zone_name = azurerm_private_dns_zone.dfs.name
  virtual_network_id    = azurerm_virtual_network.vnet.id
}

resource "azurerm_private_endpoint" "adls_dfs" {
  name                = "pe-adls-dfs"
  location            = var.location
  resource_group_name = azurerm_resource_group.rg.name
  subnet_id           = azurerm_subnet.private_endpoints.id

  private_service_connection {
    name                           = "psc-adls-dfs"
    private_connection_resource_id = azurerm_storage_account.datalake.id
    subresource_names              = ["dfs"]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name                 = "dns-zone-group-dfs"
    private_dns_zone_ids = [azurerm_private_dns_zone.dfs.id]
  }
}

# Synapse Workspace
resource "azurerm_synapse_workspace" "synapse" {
  name                                 = "syn-${var.prefix}"
  resource_group_name                  = azurerm_resource_group.rg.name
  location                             = var.location
  storage_data_lake_gen2_filesystem_id = azurerm_storage_data_lake_gen2_filesystem.bronze.id

  identity {
    type = "SystemAssigned"
  }

  managed_virtual_network_enabled      = true
  data_exfiltration_protection_enabled = true
  public_network_access_enabled        = false

  aad_admin {
    login     = "synapse-admins@company.com"
    object_id = "<admin-group-object-id>"
    tenant_id = data.azurerm_client_config.current.tenant_id
  }
}

# Private Endpoint for Synapse (Dev)
resource "azurerm_private_dns_zone" "synapse_dev" {
  name                = "privatelink.dev.azuresynapse.net"
  resource_group_name = azurerm_resource_group.rg.name
}

resource "azurerm_private_endpoint" "synapse_dev" {
  name                = "pe-synapse-dev"
  location            = var.location
  resource_group_name = azurerm_resource_group.rg.name
  subnet_id           = azurerm_subnet.private_endpoints.id

  private_service_connection {
    name                           = "psc-synapse-dev"
    private_connection_resource_id = azurerm_synapse_workspace.synapse.id
    subresource_names              = ["Dev"]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name                 = "dns-zone-group-syn-dev"
    private_dns_zone_ids = [azurerm_private_dns_zone.synapse_dev.id]
  }
}

# Grant Synapse workspace access to ADLS
resource "azurerm_role_assignment" "synapse_to_adls" {
  scope                = azurerm_storage_account.datalake.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_synapse_workspace.synapse.identity[0].principal_id
}

# Purview Account
resource "azurerm_purview_account" "purview" {
  name                = "pview-${var.prefix}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = var.location

  identity {
    type = "SystemAssigned"
  }

  managed_resource_group_name = "rg-${var.prefix}-purview-managed"
  public_network_enabled      = false
}

# Grant Purview access to scan ADLS
resource "azurerm_role_assignment" "purview_to_adls" {
  scope                = azurerm_storage_account.datalake.id
  role_definition_name = "Storage Blob Data Reader"
  principal_id         = azurerm_purview_account.purview.identity[0].principal_id
}

data "azurerm_client_config" "current" {}

output "adls_endpoint" {
  value = azurerm_storage_account.datalake.primary_dfs_endpoint
}

output "synapse_endpoint" {
  value = azurerm_synapse_workspace.synapse.connectivity_endpoints
}
```

#### Validation Steps

```bash
# Verify no public access
az storage account show --name stadlslakehouse01 --query "networkRuleSet.defaultAction" -o tsv
# Expected: Deny

az storage account show --name stadlslakehouse01 --query "allowBlobPublicAccess" -o tsv
# Expected: false

# Verify Synapse managed VNet
az synapse workspace show --name syn-lab-lakehouse --resource-group rg-lab-lakehouse \
  --query "{managedVNet:managedVirtualNetwork,exfilProtection:managedVirtualNetworkSettings.preventDataExfiltration}" -o json

# Test connectivity from within VNet (must be on a VM in the VNet)
nslookup stadlslakehouse01.dfs.core.windows.net
# Expected: resolves to private IP (10.0.1.x)
```

### Lab 2: End-to-End Encryption Strategy

**Objective**: Implement encryption at rest (CMK), in transit (TLS 1.2+), and in use (confidential computing).

#### Customer-Managed Key Setup

```bash
# Create Key Vault with RBAC and purge protection
az keyvault create \
  --name kv-encryption-prod \
  --resource-group rg-data \
  --location westeurope \
  --sku premium \
  --enable-rbac-authorization true \
  --enable-purge-protection true \
  --enable-soft-delete true \
  --retention-days 90 \
  --public-network-access Disabled

# Create RSA-HSM key for storage encryption
az keyvault key create \
  --vault-name kv-encryption-prod \
  --name key-adls-encryption \
  --kty RSA-HSM \
  --size 3072 \
  --ops wrapKey unwrapKey

# Grant storage account access to the key
az role assignment create \
  --role "Key Vault Crypto Service Encryption User" \
  --assignee-object-id $STORAGE_MI_OBJECT_ID \
  --scope "/subscriptions/$SUB/resourceGroups/rg-data/providers/Microsoft.KeyVault/vaults/kv-encryption-prod"

# Configure CMK on storage account
az storage account update \
  --name mystorageaccount \
  --resource-group rg-data \
  --encryption-key-source Microsoft.Keyvault \
  --encryption-key-vault "https://kv-encryption-prod.vault.azure.net" \
  --encryption-key-name key-adls-encryption \
  --encryption-key-version "" \
  --key-vault-user-identity-id $USER_ASSIGNED_MI_RESOURCE_ID
```

#### Double Encryption (Infrastructure + Service)

```bicep
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: 'stadlsencrypted'
  location: location
  kind: 'StorageV2'
  sku: { name: 'Standard_ZRS' }
  properties: {
    isHnsEnabled: true
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    encryption: {
      requireInfrastructureEncryption: true  // Double encryption
      services: {
        blob: { enabled: true, keyType: 'Account' }
      }
      keySource: 'Microsoft.Keyvault'
      keyvaultproperties: {
        keyname: 'key-adls-encryption'
        keyvaulturi: keyVaultUri
      }
    }
  }
}
```

#### TLS 1.2 Enforcement Validation

```python
import ssl
import socket

def check_tls_version(hostname: str, port: int = 443) -> dict:
    """Verify minimum TLS version on Azure service endpoints."""
    results = {}
    
    for protocol_name, protocol_const in [
        ("TLSv1.0", ssl.PROTOCOL_TLSv1),
        ("TLSv1.1", ssl.PROTOCOL_TLSv1_1),
        ("TLSv1.2", ssl.PROTOCOL_TLSv1_2),
    ]:
        try:
            context = ssl.SSLContext(protocol_const)
            with socket.create_connection((hostname, port), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    results[protocol_name] = f"CONNECTED ({ssock.version()})"
        except (ssl.SSLError, ConnectionRefusedError, OSError) as e:
            results[protocol_name] = f"REJECTED ({type(e).__name__})"
    
    return results

# Test Azure endpoints
endpoints = [
    "mystorageaccount.dfs.core.windows.net",
    "syn-prod.dev.azuresynapse.net",
    "kv-prod.vault.azure.net",
]

for endpoint in endpoints:
    print(f"\n{endpoint}:")
    for version, status in check_tls_version(endpoint).items():
        print(f"  {version}: {status}")
    # Expected: TLSv1.0 REJECTED, TLSv1.1 REJECTED, TLSv1.2 CONNECTED
```

### Lab 3: Azure Data Platform Security Assessment

**Objective**: Conduct an authorized security assessment of an Azure data platform deployment.

#### Scope Definition

```markdown
## Authorized Assessment Scope
- Target: Azure data platform (subscription: xxx-xxx-xxx)
- Services: ADLS Gen2, Synapse, Databricks, ADF, Event Hubs, Key Vault
- Methodology: OWASP Cloud Security, CIS Azure Benchmark, Azure Well-Architected
- Duration: 2024-07-01 to 2024-07-14
- Authorization: Written authorization from subscription Owner (ref: AUTH-2024-042)
```

#### Automated Assessment Script

```python
#!/usr/bin/env python3
"""Azure Data Platform Security Assessment Tool.

Requires: azure-identity, azure-mgmt-storage, azure-mgmt-synapse,
          azure-mgmt-resource, azure-mgmt-network
"""

import json
from dataclasses import dataclass, field
from enum import Enum
from azure.identity import DefaultAzureCredential
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.synapse import SynapseManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.resource import ResourceManagementClient

class Severity(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"

@dataclass
class Finding:
    severity: Severity
    resource_id: str
    title: str
    description: str
    remediation: str
    cwe: str = ""
    cvss: float = 0.0

@dataclass
class AssessmentReport:
    findings: list = field(default_factory=list)
    
    def add(self, finding: Finding):
        self.findings.append(finding)
    
    def summary(self) -> dict:
        return {
            sev.value: len([f for f in self.findings if f.severity == sev])
            for sev in Severity
        }

def assess_storage_accounts(
    storage_client: StorageManagementClient,
    report: AssessmentReport
):
    """Assess all storage accounts for security misconfigurations."""
    
    for account in storage_client.storage_accounts.list():
        resource_id = account.id
        
        # Check: public blob access
        if account.allow_blob_public_access:
            report.add(Finding(
                severity=Severity.CRITICAL,
                resource_id=resource_id,
                title="Public blob access enabled",
                description=f"Storage account {account.name} allows public blob access",
                remediation="Set allowBlobPublicAccess to false",
                cwe="CWE-284",
                cvss=9.1
            ))
        
        # Check: minimum TLS version
        if account.minimum_tls_version != "TLS1_2":
            report.add(Finding(
                severity=Severity.HIGH,
                resource_id=resource_id,
                title=f"TLS version below 1.2: {account.minimum_tls_version}",
                description="Allows connections with deprecated TLS versions",
                remediation="Set minimumTlsVersion to TLS1_2",
                cwe="CWE-326",
                cvss=7.5
            ))
        
        # Check: shared key access
        if account.allow_shared_key_access is not False:
            report.add(Finding(
                severity=Severity.MEDIUM,
                resource_id=resource_id,
                title="Shared key access not disabled",
                description="Account keys provide full administrative access; prefer Entra ID",
                remediation="Set allowSharedKeyAccess to false",
                cwe="CWE-798",
                cvss=6.5
            ))
        
        # Check: network rules
        if account.network_rule_set and account.network_rule_set.default_action == "Allow":
            report.add(Finding(
                severity=Severity.HIGH,
                resource_id=resource_id,
                title="Network default action is Allow",
                description="Storage account accessible from all networks",
                remediation="Set defaultAction to Deny, use private endpoints",
                cwe="CWE-284",
                cvss=7.8
            ))
        
        # Check: infrastructure encryption (double encryption)
        if not account.encryption.require_infrastructure_encryption:
            report.add(Finding(
                severity=Severity.LOW,
                resource_id=resource_id,
                title="Infrastructure encryption not enabled",
                description="Single layer encryption only (service-level)",
                remediation="Enable requireInfrastructureEncryption for double encryption",
                cwe="CWE-311",
                cvss=3.1
            ))
        
        # Check: HTTPS only
        if not account.enable_https_traffic_only:
            report.add(Finding(
                severity=Severity.HIGH,
                resource_id=resource_id,
                title="HTTP traffic allowed",
                description="Unencrypted traffic permitted to storage account",
                remediation="Set supportsHttpsTrafficOnly to true",
                cwe="CWE-319",
                cvss=7.5
            ))

def assess_synapse_workspaces(
    synapse_client: SynapseManagementClient,
    report: AssessmentReport
):
    """Assess Synapse workspaces for security misconfigurations."""
    
    for workspace in synapse_client.workspaces.list():
        resource_id = workspace.id
        
        # Check: managed VNet
        if not workspace.managed_virtual_network:
            report.add(Finding(
                severity=Severity.HIGH,
                resource_id=resource_id,
                title="Managed VNet not enabled",
                description=f"Synapse workspace {workspace.name} lacks network isolation",
                remediation="Enable managed virtual network (requires workspace recreation)",
                cwe="CWE-284",
                cvss=7.5
            ))
        
        # Check: data exfiltration protection
        mvn_settings = workspace.managed_virtual_network_settings
        if mvn_settings and not mvn_settings.prevent_data_exfiltration:
            report.add(Finding(
                severity=Severity.HIGH,
                resource_id=resource_id,
                title="Data exfiltration protection disabled",
                description="Workspace can write data to unauthorized destinations",
                remediation="Enable preventDataExfiltration in managed VNet settings",
                cwe="CWE-200",
                cvss=8.0
            ))
        
        # Check: public network access
        if workspace.public_network_access == "Enabled":
            report.add(Finding(
                severity=Severity.MEDIUM,
                resource_id=resource_id,
                title="Public network access enabled",
                description="Workspace accessible from public internet",
                remediation="Disable public network access, use private endpoints",
                cwe="CWE-284",
                cvss=6.5
            ))

def main():
    credential = DefaultAzureCredential()
    subscription_id = "<subscription-id>"
    
    storage_client = StorageManagementClient(credential, subscription_id)
    synapse_client = SynapseManagementClient(credential, subscription_id)
    
    report = AssessmentReport()
    
    assess_storage_accounts(storage_client, report)
    assess_synapse_workspaces(synapse_client, report)
    
    # Output report
    print(json.dumps({
        "summary": report.summary(),
        "findings": [
            {
                "severity": f.severity.value,
                "resource": f.resource_id,
                "title": f.title,
                "cwe": f.cwe,
                "cvss": f.cvss,
                "remediation": f.remediation
            }
            for f in sorted(report.findings, key=lambda x: x.cvss, reverse=True)
        ]
    }, indent=2))

if __name__ == "__main__":
    main()
```

### Lab 4: Sentinel Detection Rules for Data Exfiltration

**Objective**: Create custom Sentinel analytics rules to detect data exfiltration patterns from Azure data services.

#### Rule 1: Large Volume Data Download

```kusto
// Scheduled rule: runs every 5 minutes, looks back 1 hour
// Detects: single identity downloading > 5 GB from ADLS in 1 hour

let ExfiltrationThresholdBytes = 5368709120;  // 5 GB
let TimeWindow = 1h;

StorageBlobLogs
| where TimeGenerated > ago(TimeWindow)
| where OperationName in ("GetBlob", "ReadFile")
| where StatusCode == 200
| extend AccountName = split(Uri, ".")[0]
| summarize 
    TotalBytesDownloaded = sum(ResponseBodySize),
    UniqueFiles = dcount(ObjectKey),
    Operations = count(),
    FirstSeen = min(TimeGenerated),
    LastSeen = max(TimeGenerated)
    by CallerIpAddress, RequesterUpn = tostring(AuthenticationHash), AccountName = tostring(AccountName)
| where TotalBytesDownloaded > ExfiltrationThresholdBytes
| extend 
    DataExfiltratedGB = round(TotalBytesDownloaded / 1073741824.0, 2),
    DurationMinutes = datetime_diff('minute', LastSeen, FirstSeen)
| project 
    FirstSeen, LastSeen, CallerIpAddress, RequesterUpn,
    AccountName, DataExfiltratedGB, UniqueFiles, Operations, DurationMinutes
```

#### Rule 2: Unusual Cross-Tenant Data Access

```kusto
// Detects: access from service principals in unexpected tenants

let KnownTenants = dynamic(["<primary-tenant-id>", "<partner-tenant-id>"]);

StorageBlobLogs
| where TimeGenerated > ago(1h)
| where StatusCode == 200
| where AuthenticationType == "OAuth"
| extend TokenClaims = parse_json(AuthorizationDetails)
| extend CallerTenantId = tostring(TokenClaims.tenantId)
| where CallerTenantId !in (KnownTenants)
| where isnotempty(CallerTenantId)
| summarize 
    AccessCount = count(),
    DataAccessed = sum(ResponseBodySize),
    Resources = make_set(ObjectKey, 10)
    by CallerTenantId, CallerIpAddress, AccountName
| extend AlertSeverity = "High"
| project TimeGenerated = now(), CallerTenantId, CallerIpAddress, AccountName, AccessCount, DataAccessed, Resources
```

#### Rule 3: Synapse Data Export to Unauthorized Destinations

```kusto
// Detects: CETAS (CREATE EXTERNAL TABLE AS SELECT) or COPY INTO targeting unknown storage

SynapseSqlAuditEvents
| where TimeGenerated > ago(1h)
| where Statement has_any ("CREATE EXTERNAL TABLE", "COPY INTO", "OPENROWSET")
| extend 
    TargetStorage = extract(@"https://([^.]+)\.(?:blob|dfs)\.core\.windows\.net", 1, Statement)
| where isnotempty(TargetStorage)
| where TargetStorage !in (dynamic(["approvedstorage1", "approvedstorage2", "approvedstorage3"]))
| project 
    TimeGenerated, 
    LoginName = UserName, 
    ClientIp, 
    DatabaseName, 
    TargetStorage,
    StatementSnippet = substring(Statement, 0, 500)
| extend AlertSeverity = "High"
```

#### Rule 4: Databricks Bulk Data Export

```kusto
// Detects: Databricks cluster writing large volumes to external storage
// Requires: Databricks audit logs forwarded to Log Analytics

DatabricksAudit
| where TimeGenerated > ago(1h)
| where ActionName in ("databricksSQLWrite", "mountDirectory", "writeExternalData")
| extend 
    TargetPath = tostring(parse_json(RequestParams).path),
    BytesWritten = tolong(parse_json(Response).bytesWritten),
    UserIdentity = tostring(parse_json(Identity).email)
| where BytesWritten > 1073741824  // > 1 GB
| where TargetPath has_any ("wasb://", "abfss://", "s3://", "gs://")
| where TargetPath !has_any ("approvedaccount1", "approvedaccount2")
| summarize 
    TotalExported = sum(BytesWritten),
    Destinations = make_set(TargetPath, 5)
    by UserIdentity, ClusterName = tostring(parse_json(RequestParams).clusterId)
| extend DataExportedGB = round(TotalExported / 1073741824.0, 2)
| where DataExportedGB > 1
```

#### Rule 5: Event Hub Consumer Group Enumeration

```kusto
// Detects: rapid enumeration of consumer groups (reconnaissance)

AzureActivity
| where TimeGenerated > ago(1h)
| where ResourceProvider == "MICROSOFT.EVENTHUB"
| where OperationNameValue has_any ("consumergroups/read", "eventhubs/read", "authorizationrules/listkeys")
| summarize 
    OperationCount = count(),
    UniqueOperations = dcount(OperationNameValue),
    Resources = make_set(Resource, 20)
    by Caller, CallerIpAddress
| where OperationCount > 50 or UniqueOperations > 5
| extend AlertSeverity = case(
    OperationCount > 200, "High",
    OperationCount > 100, "Medium",
    "Low"
)
```

#### Deploying Rules via ARM Template

```json
{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "workspaceName": { "type": "string" },
    "location": { "type": "string", "defaultValue": "[resourceGroup().location]" }
  },
  "resources": [
    {
      "type": "Microsoft.OperationalInsights/workspaces/providers/alertRules",
      "apiVersion": "2022-11-01-preview",
      "name": "[concat(parameters('workspaceName'), '/Microsoft.SecurityInsights/data-exfiltration-adls')]",
      "kind": "Scheduled",
      "location": "[parameters('location')]",
      "properties": {
        "displayName": "Data Exfiltration - Large ADLS Download",
        "description": "Detects single identity downloading > 5 GB from ADLS in 1 hour",
        "severity": "High",
        "enabled": true,
        "query": "StorageBlobLogs | where TimeGenerated > ago(1h) | where OperationName in ('GetBlob', 'ReadFile') | where StatusCode == 200 | summarize TotalBytes = sum(ResponseBodySize), Files = dcount(ObjectKey) by CallerIpAddress, tostring(split(Uri, '.')[0]) | where TotalBytes > 5368709120",
        "queryFrequency": "PT5M",
        "queryPeriod": "PT1H",
        "triggerOperator": "GreaterThan",
        "triggerThreshold": 0,
        "suppressionDuration": "PT1H",
        "suppressionEnabled": true,
        "tactics": ["Exfiltration"],
        "techniques": ["T1567"],
        "incidentConfiguration": {
          "createIncident": true,
          "groupingConfiguration": {
            "enabled": true,
            "reopenClosedIncident": false,
            "lookbackDuration": "PT5H",
            "matchingMethod": "AllEntities"
          }
        },
        "entityMappings": [
          {
            "entityType": "IP",
            "fieldMappings": [
              { "identifier": "Address", "columnName": "CallerIpAddress" }
            ]
          }
        ]
      }
    }
  ]
}
```

#### Incident Response Playbook

```powershell
# Automated response when data exfiltration is detected

param(
    [string]$StorageAccountName,
    [string]$SuspiciousIP,
    [string]$IncidentId
)

# Step 1: Block the IP immediately
$networkRules = Get-AzStorageAccountNetworkRuleSet -ResourceGroupName "rg-data" -Name $StorageAccountName

# Add deny rule (by removing from allow list if present)
$updatedIpRules = $networkRules.IpRules | Where-Object { $_.IPAddressOrRange -ne $SuspiciousIP }
Update-AzStorageAccountNetworkRuleSet `
    -ResourceGroupName "rg-data" `
    -Name $StorageAccountName `
    -DefaultAction Deny `
    -IPRule $updatedIpRules

# Step 2: Revoke active sessions (rotate keys if shared key was used)
$keyType = "kerb1"  # Rotate Kerberos key to invalidate tokens
New-AzStorageAccountKey -ResourceGroupName "rg-data" -Name $StorageAccountName -KeyName $keyType

# Step 3: Capture forensic snapshot
$context = New-AzStorageContext -StorageAccountName $StorageAccountName -StorageAccountKey (Get-AzStorageAccountKey -ResourceGroupName "rg-data" -Name $StorageAccountName)[0].Value

# Get access logs for the suspicious IP in the last 24h
$logs = Get-AzStorageBlob -Container '$logs' -Context $context |
    Where-Object { $_.LastModified -gt (Get-Date).AddHours(-24) }

# Step 4: Update Sentinel incident
$incident = Get-AzSentinelIncident -ResourceGroupName "rg-security" -WorkspaceName "law-security" -Id $IncidentId
Update-AzSentinelIncident `
    -ResourceGroupName "rg-security" `
    -WorkspaceName "law-security" `
    -Id $IncidentId `
    -Status Active `
    -Severity High `
    -Title "CONFIRMED: Data Exfiltration from $StorageAccountName" `
    -Description "IP $SuspiciousIP blocked. Keys rotated. Forensic capture in progress."

Write-Output "[$(Get-Date -Format 'o')] Response completed for incident $IncidentId"
```

---

## Summary of Key Security Principles

1. **Zero Trust Network**: All data services behind private endpoints; no public internet exposure in production
2. **Least Privilege Identity**: Managed identities with minimal RBAC; no shared keys; no SAS tokens in production
3. **Defense in Depth**: NSGs + Private Endpoints + Firewall Rules + Conditional Access + Defender
4. **Encryption Everywhere**: CMK + infrastructure encryption + TLS 1.2+ + HTTPS-only
5. **Continuous Monitoring**: Diagnostic settings on every resource; Sentinel analytics rules; automated response
6. **Governance**: Azure Policy enforcement; Purview classification and lineage; Unity Catalog access control
7. **Assume Breach**: Monitor for lateral movement between data services; detect credential abuse; automated key rotation
8. **Data Exfiltration Prevention**: Managed VNet with exfiltration protection; Sentinel detection rules; egress monitoring

---

## References

- Microsoft Learn: Azure Data Architecture Guide
- Microsoft Learn: Azure Well-Architected Framework — Data Analytics
- CIS Microsoft Azure Foundations Benchmark v2.0
- OWASP Cloud Security Testing Guide
- MITRE ATT&CK Cloud Matrix — Azure
- Azure Security Benchmark v3
- Databricks Security Best Practices
- Azure Synapse Analytics Security Whitepaper
