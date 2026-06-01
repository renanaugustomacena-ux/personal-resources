# Connections e Variables in Airflow

La gestione sicura delle credenziali e dei parametri di configurazione è fondamentale in un sistema di orchestrazione che accede a decine di sorgenti dati diverse.

## Connections

Le Connection in Airflow sono oggetti che centralizzano i parametri di connessione per database, API, servizi cloud e qualsiasi risorsa esterna.

### Struttura di una Connection

```
conn_id:      identificatore univoco (es. "postgres_dwh")
conn_type:    tipo (postgres, mysql, http, aws, google_cloud, ...)
host:         hostname o URL base
schema:       nome database o path
login:        username
password:     password (crittografata con Fernet key)
port:         porta
extra:        JSON con parametri aggiuntivi specifici al conn_type
```

### Creazione via UI

```
Admin → Connections → + Add Connection
```

### Creazione via CLI

```bash
# Connessione PostgreSQL
airflow connections add postgres_dwh \
    --conn-type postgres \
    --conn-host dwh.company.internal \
    --conn-schema datawarehouse \
    --conn-login etl_user \
    --conn-password "$(vault read -field=password secret/etl/pg)" \
    --conn-port 5432

# Connessione Snowflake
airflow connections add snowflake_prod \
    --conn-type snowflake \
    --conn-host company.eu-west-1.snowflakecomputing.com \
    --conn-schema DWH \
    --conn-login ETL_USER \
    --conn-password "$(vault read -field=password secret/etl/snowflake)" \
    --conn-extra '{"account": "company", "warehouse": "TRANSFORM_WH", "role": "TRANSFORMER", "region": "eu-west-1"}'

# Connessione AWS
airflow connections add aws_default \
    --conn-type aws \
    --conn-extra '{"aws_access_key_id": "...", "aws_secret_access_key": "...", "region_name": "eu-west-1"}'

# Connessione HTTP (API REST)
airflow connections add stripe_api \
    --conn-type http \
    --conn-host https://api.stripe.com \
    --conn-extra '{"Authorization": "Bearer sk_live_..."}'
```

### Creazione via Environment Variables

In Kubernetes o Docker, le connessioni possono essere definite come variabili d'ambiente senza passare dal metadata DB:

```bash
# Formato: AIRFLOW_CONN_{CONN_ID} = URI
export AIRFLOW_CONN_POSTGRES_DWH="postgresql://etl_user:password@dwh.internal:5432/datawarehouse"
export AIRFLOW_CONN_SNOWFLAKE_PROD="snowflake://ETL_USER:password@company.eu-west-1/DWH?warehouse=TRANSFORM_WH&role=TRANSFORMER"
export AIRFLOW_CONN_AWS_DEFAULT="aws://?aws_access_key_id=AKIA...&aws_secret_access_key=...&region_name=eu-west-1"
```

### Accesso nel Codice

```python
from airflow.hooks.base import BaseHook
import psycopg2
import snowflake.connector

def get_postgres_conn(conn_id: str = "postgres_dwh"):
    """Ottieni connessione psycopg2 da Airflow connection."""
    conn = BaseHook.get_connection(conn_id)
    return psycopg2.connect(
        host=conn.host,
        port=conn.port,
        dbname=conn.schema,
        user=conn.login,
        password=conn.password,
        sslmode="require"
    )


def get_snowflake_conn(conn_id: str = "snowflake_prod"):
    """Ottieni connessione Snowflake da Airflow connection."""
    conn = BaseHook.get_connection(conn_id)
    extra = conn.extra_dejson
    return snowflake.connector.connect(
        account=extra.get("account"),
        user=conn.login,
        password=conn.password,
        warehouse=extra.get("warehouse"),
        database=conn.schema,
        role=extra.get("role"),
        region=extra.get("region")
    )


def get_api_headers(conn_id: str) -> dict:
    """Ottieni headers HTTP da Airflow connection."""
    conn = BaseHook.get_connection(conn_id)
    return conn.extra_dejson  # Contiene {"Authorization": "Bearer ..."}
```

---

## Variables

Le Variables sono coppie chiave-valore globali accessibili da qualsiasi DAG. Utili per parametri di configurazione che cambiano senza richiedere un deploy del codice.

### Creazione via UI

```
Admin → Variables → + Add Variable
```

### Creazione via CLI

```bash
# Singola variabile
airflow variables set batch_size 50000

# Variabile JSON (serializzata come stringa)
airflow variables set pipeline_config '{"max_retries": 3, "timeout_hours": 2}'

# Da file
airflow variables import variables.json
```

```json
// variables.json
{
  "batch_size": "50000",
  "dbt_target": "prod",
  "alert_email": "data-team@company.com",
  "pipeline_config": "{\"max_retries\": 3, \"timeout\": 7200}",
  "feature_flags": "{\"enable_new_transform\": false, \"use_v2_api\": true}"
}
```

### Accesso nel Codice

```python
from airflow.models import Variable

# Stringa semplice
batch_size = int(Variable.get("batch_size", default_var="50000"))

# JSON automaticamente deserializzato
config = Variable.get("pipeline_config", deserialize_json=True)
max_retries = config["max_retries"]
timeout = config["timeout"]

# Feature flag
flags = Variable.get("feature_flags", deserialize_json=True)
if flags.get("enable_new_transform"):
    result = new_transform(records)
else:
    result = old_transform(records)

# Come template Jinja (non richiede importazione)
# {{ var.value.batch_size }}           → stringa
# {{ var.json.pipeline_config.timeout }} → navigazione JSON
```

### Variables come Template

```python
from airflow.operators.python import PythonOperator

task = PythonOperator(
    task_id="process",
    python_callable=process_fn,
    op_kwargs={
        "batch_size": "{{ var.value.batch_size }}",
        "target_schema": "{{ var.value.dbt_target }}",
    }
)

# Op SQL con variable
from airflow.providers.postgres.operators.postgres import PostgresOperator
query = PostgresOperator(
    task_id="run_query",
    postgres_conn_id="postgres_dwh",
    sql="""
        INSERT INTO {{ var.value.target_schema }}.daily_summary
        SELECT * FROM orders WHERE DATE(created_at) = '{{ ds }}'
    """
)
```

---

## Backend dei Segreti

In produzione, le credenziali non dovrebbero essere nel metadata DB di Airflow. I backend dei segreti delegano la risoluzione a sistemi dedicati come HashiCorp Vault o AWS Secrets Manager.

### AWS Secrets Manager

```bash
# In airflow.cfg
[secrets]
backend = airflow.providers.amazon.aws.secrets.secrets_manager.SecretsManagerBackend
backend_kwargs = {
    "connections_prefix": "airflow/connections",
    "variables_prefix": "airflow/variables",
    "profile_name": null
}
```

```bash
# Crea segreto in AWS Secrets Manager
aws secretsmanager create-secret \
    --name "airflow/connections/postgres_dwh" \
    --secret-string '{
        "conn_type": "postgres",
        "host": "dwh.company.internal",
        "schema": "datawarehouse",
        "login": "etl_user",
        "password": "s3cr3t",
        "port": 5432
    }'

# Crea variabile in AWS Secrets Manager
aws secretsmanager create-secret \
    --name "airflow/variables/slack_webhook" \
    --secret-string "https://hooks.slack.com/services/..."
```

### HashiCorp Vault

```bash
# airflow.cfg
[secrets]
backend = airflow.providers.hashicorp.secrets.vault.VaultBackend
backend_kwargs = {
    "connections_path": "connections",
    "variables_path": "variables",
    "url": "http://vault.company.internal:8200",
    "mount_point": "airflow",
    "auth_type": "kubernetes",
    "kubernetes_role": "airflow"
}
```

```bash
# Crea segreto in Vault
vault kv put airflow/connections/postgres_dwh \
    conn_type=postgres \
    host=dwh.company.internal \
    schema=datawarehouse \
    login=etl_user \
    password=s3cr3t \
    port=5432

vault kv put airflow/variables/slack_webhook \
    value="https://hooks.slack.com/services/..."
```

### Rotazione Automatica delle Credenziali

```python
from airflow.decorators import dag, task
from datetime import datetime, timedelta

@dag(
    schedule_interval="@weekly",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["security", "credentials"]
)
def rotate_credentials():
    """DAG per la rotazione periodica delle credenziali ETL."""

    @task
    def generate_new_password(service: str) -> str:
        """Genera nuova password sicura."""
        import secrets
        import string
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return "".join(secrets.choice(alphabet) for _ in range(32))

    @task
    def update_database_password(service: str, new_password: str):
        """Aggiorna la password nel database."""
        conn = get_admin_conn(service)
        with conn.cursor() as cur:
            cur.execute(
                f"ALTER USER etl_{service}_user PASSWORD %s",
                (new_password,)
            )
        conn.commit()

    @task
    def update_vault_secret(service: str, new_password: str):
        """Aggiorna il segreto in Vault."""
        import hvac
        client = hvac.Client(url="http://vault:8200", token=get_vault_token())
        client.secrets.kv.v2.create_or_update_secret(
            path=f"connections/{service}_db",
            secret={"password": new_password}
        )

    @task
    def verify_connection(service: str):
        """Verifica che la nuova password funzioni."""
        from airflow.hooks.base import BaseHook
        conn = BaseHook.get_connection(f"{service}_db")
        # Forza refresh dal vault (non dalla cache locale)
        test_connection(conn)

    for svc in ["orders", "customers", "products"]:
        pwd = generate_new_password(svc)
        update_database_password(svc, pwd)
        update_vault_secret(svc, pwd)
        verify_connection(svc)


dag = rotate_credentials()
```

---

## Fernet Key

La Fernet key crittografa le password delle Connection nel metadata DB. Senza di essa, le password sono in chiaro.

```python
# Genera Fernet key
from cryptography.fernet import Fernet
key = Fernet.generate_key()
print(key.decode())  # Salva questo nel config!

# airflow.cfg
# [core]
# fernet_key = la_key_generata_sopra

# O come environment variable
# AIRFLOW__CORE__FERNET_KEY=la_key_generata
```

**Rotazione della Fernet key**:

```bash
# 1. Genera nuova key
NEW_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

# 2. Aggiungi ENTRAMBE le key (old + new) durante la migrazione
# AIRFLOW__CORE__FERNET_KEY=new_key,old_key

# 3. Esegui la rotazione
airflow db rotate-fernet-key

# 4. Rimuovi la vecchia key dalla configurazione
# AIRFLOW__CORE__FERNET_KEY=new_key
```

---

## Best Practice

**Non hardcodare conn_id** nelle funzioni Python — passali come parametri o recuperali da Variable, così sono modificabili senza deploy.

**Usa environment variables** per conn in ambienti K8s — è più sicuro del metadata DB ed è compatibile con i secret manager nativi.

**Rotazione regolare delle credenziali** — automatizza con un DAG settimanale. Un'API key compromessa mai ruotata è una backdoor permanente.

**Non passare segreti via DAG conf o XCom** — usa sempre il sistema di connection/secret. Il conf del DAG è visibile nella UI e nei log.

**Segrega le connection per ambiente** — `postgres_dwh_dev`, `postgres_dwh_prod`. Mai condividere la stessa connection tra dev e prod.
