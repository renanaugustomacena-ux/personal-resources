# Elasticsearch — Integrazioni con l'Ecosistema

## La Elastic Stack: Logstash, Beats e Kibana

Elasticsearch non opera mai in isolamento. L'intero valore della piattaforma emerge dall'orchestrazione dei componenti della **Elastic Stack** (ex ELK Stack): Logstash per l'ingestione e trasformazione, i **Beats** come agenti leggeri di raccolta dati, Kibana come interfaccia di visualizzazione e gestione.

### Logstash: Pipeline di Ingestione

Logstash è un processore di eventi orientato alle pipeline, con architettura a tre stadi:

```
Input → Filter → Output
```

Ogni pipeline è definita in un file `.conf`:

```ruby
input {
  kafka {
    bootstrap_servers => "kafka1:9092,kafka2:9092"
    topics            => ["app-logs", "nginx-access"]
    group_id          => "logstash-consumers"
    codec             => "json"
    consumer_threads  => 4
    decorate_events   => true    # aggiunge metadati Kafka all'evento
  }
}

filter {
  # Parsing del log Nginx con grok pattern
  if [kafka][topic] == "nginx-access" {
    grok {
      match => {
        "message" => '%{IPORHOST:client_ip} - %{USER:ident} \[%{HTTPDATE:timestamp}\] "%{WORD:method} %{URIPATHPARAM:path} HTTP/%{NUMBER:http_version}" %{NUMBER:status_code:int} %{NUMBER:bytes_sent:int} "%{URI:referrer}" "%{GREEDYDATA:user_agent}"'
      }
    }
    date {
      match   => ["timestamp", "dd/MMM/yyyy:HH:mm:ss Z"]
      target  => "@timestamp"
      remove_field => ["timestamp"]
    }
    useragent {
      source => "user_agent"
      target => "ua"
    }
    geoip {
      source => "client_ip"
      target => "geo"
      fields => ["country_name", "city_name", "location"]
    }
    mutate {
      remove_field => ["message", "ident"]
      add_field    => { "[@metadata][index_suffix]" => "nginx" }
    }
  }

  # Arricchimento con translate (lookup da file CSV)
  translate {
    field       => "status_code"
    destination => "status_label"
    dictionary  => {
      "200" => "OK"
      "301" => "Moved"
      "400" => "Bad Request"
      "404" => "Not Found"
      "500" => "Internal Server Error"
    }
    fallback => "Unknown"
  }
}

output {
  elasticsearch {
    hosts         => ["https://es-node1:9200", "https://es-node2:9200"]
    index         => "logs-%{[@metadata][index_suffix]}-%{+YYYY.MM.dd}"
    user          => "${ES_USER}"
    password      => "${ES_PASS}"
    ssl           => true
    cacert        => "/etc/logstash/certs/ca.crt"
    # Usa ILM invece di date-based rollover
    ilm_enabled   => true
    ilm_rollover_alias => "logs-nginx"
    ilm_policy    => "logs-policy"
    ilm_pattern   => "{now/d}-000001"
    # Gestione errori con dead letter queue
    action        => "index"
  }
  # Dead Letter Queue per eventi non processabili
  if "_grokparsefailure" in [tags] {
    file {
      path => "/var/log/logstash/dlq/%{+YYYY-MM-dd}-parse-failures.log"
    }
  }
}
```

**Dead Letter Queue (DLQ)**: Logstash supporta una coda separata per eventi che falliscono l'output. Configurazione in `logstash.yml`:

```yaml
dead_letter_queue.enable: true
dead_letter_queue.max_bytes: 1gb
path.dead_letter_queue: /var/lib/logstash/dead_letter_queue
```

Per rielaborare gli eventi dalla DLQ:

```ruby
input {
  dead_letter_queue {
    path            => "/var/lib/logstash/dead_letter_queue"
    commit_offsets  => true
    pipeline_id     => "main"
  }
}
```

### Filebeat: Agente Leggero per Log

Filebeat è il Beat più diffuso — raccoglie log da file e li spedisce a Logstash o direttamente a Elasticsearch.

```yaml
# filebeat.yml
filebeat.inputs:
  - type: log
    enabled: true
    paths:
      - /var/log/nginx/*.log
      - /var/log/app/*.log
    fields:
      service: myapp
      environment: production
    fields_under_root: true
    multiline.type: pattern
    multiline.pattern: '^\d{4}-\d{2}-\d{2}'  # riga inizia con data
    multiline.negate: true
    multiline.match: after
    close_inactive: 5m
    scan_frequency: 10s

  - type: container
    paths:
      - /var/lib/docker/containers/*/*.log
    processors:
      - add_docker_metadata:
          host: "unix:///var/run/docker.sock"

processors:
  - add_host_metadata: ~
  - add_cloud_metadata: ~
  - drop_event:
      when:
        regexp:
          message: "^health-check"

output.logstash:
  hosts: ["logstash:5044"]
  loadbalance: true
  ssl.certificate_authorities: ["/etc/filebeat/certs/ca.crt"]

monitoring:
  enabled: true
  cluster_uuid: "abc123"
  elasticsearch:
    hosts: ["https://es-monitoring:9200"]
```

**Moduli Filebeat**: configurazioni prebuilt per sorgenti comuni (nginx, apache, postgresql, mysql, aws). Attivazione:

```bash
filebeat modules enable nginx postgresql
filebeat setup --pipelines  # crea ingest pipeline su ES
filebeat setup --index-management  # crea ILM policy e template
```

### Metricbeat, Heartbeat, Packetbeat

- **Metricbeat**: raccoglie metriche di sistema e servizi (CPU, memoria, elasticsearch, redis, kafka). Ogni modulo chiama API native del servizio.
- **Heartbeat**: monitora uptime e latenza di endpoint HTTP/TCP/ICMP, alimenta Uptime in Kibana.
- **Packetbeat**: analisi traffico di rete in tempo reale — ricostruisce transazioni HTTP, MySQL, Redis direttamente dai pacchetti.

---

## Python: elasticsearch-py

Il client ufficiale Python supporta sia l'API sincrona che quella asincrona (`AsyncElasticsearch`).

### Installazione e Connessione

```bash
pip install elasticsearch[async]  # include aiohttp per async
```

```python
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk, async_bulk, streaming_bulk
import certifi

# Connessione con autenticazione e TLS
es = Elasticsearch(
    hosts=["https://es-node1:9200", "https://es-node2:9200"],
    basic_auth=("elastic", "changeme"),
    ca_certs=certifi.where(),
    # oppure percorso custom:
    # ca_certs="/etc/ssl/certs/ca.crt",
    request_timeout=30,
    max_retries=3,
    retry_on_timeout=True,
    sniff_on_start=True,           # autodiscover nodi all'avvio
    sniff_on_node_failure=True,    # re-sniff se un nodo cade
)

info = es.info()
print(f"Cluster: {info['cluster_name']}, ES version: {info['version']['number']}")
```

### CRUD e Operazioni Base

```python
# Indexing
doc = {
    "title": "Introduzione a Elasticsearch",
    "content": "Elasticsearch è un motore di ricerca distribuito...",
    "author": "Mario Rossi",
    "published_at": "2024-01-15T10:30:00Z",
    "tags": ["elasticsearch", "search", "nosql"],
    "view_count": 1234
}

resp = es.index(index="articles", id="art-001", document=doc)
print(resp["result"])  # "created"

# Get
resp = es.get(index="articles", id="art-001")
print(resp["_source"]["title"])

# Update parziale
es.update(index="articles", id="art-001", doc={"view_count": 1235})

# Update con script
es.update(
    index="articles",
    id="art-001",
    script={
        "source": "ctx._source.view_count += params.delta",
        "lang": "painless",
        "params": {"delta": 10}
    }
)

# Delete
es.delete(index="articles", id="art-001")

# Exists
exists = es.exists(index="articles", id="art-001")
```

### Bulk Helpers

L'helper `bulk()` è il modo corretto per ingestione massiva — non usare `es.index()` in un loop.

```python
from elasticsearch.helpers import bulk
import json

def generate_actions(filepath):
    """Generator che legge un JSONL e produce azioni bulk."""
    with open(filepath) as f:
        for line in f:
            doc = json.loads(line)
            yield {
                "_index": "products",
                "_id": doc["sku"],
                "_source": doc,
            }

# bulk sincrono con statistiche
success, errors = bulk(
    es,
    generate_actions("products.jsonl"),
    chunk_size=500,           # documenti per richiesta bulk
    max_chunk_bytes=50*1024*1024,  # 50 MB max per richiesta
    request_timeout=60,
    raise_on_error=False,     # non solleva eccezione, restituisce errori
    raise_on_exception=False,
)
print(f"Indicizzati: {success}, Errori: {len(errors)}")
if errors:
    for err in errors[:5]:
        print(json.dumps(err, indent=2))
```

### Async Elasticsearch

```python
import asyncio
from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk

async def main():
    es = AsyncElasticsearch(
        hosts=["https://es-node1:9200"],
        basic_auth=("elastic", "changeme"),
    )

    async def generate():
        for i in range(100_000):
            yield {
                "_index": "events",
                "_source": {
                    "event_id": i,
                    "timestamp": "2024-01-15T10:00:00Z",
                    "message": f"Event {i}",
                }
            }

    success, errors = await async_bulk(
        es,
        generate(),
        chunk_size=1000,
    )
    print(f"Async bulk: {success} successi, {errors} errori")
    await es.close()

asyncio.run(main())
```

### Search con Python

```python
# Query complessa
resp = es.search(
    index="articles",
    body={
        "query": {
            "bool": {
                "must": [
                    {"match": {"content": "elasticsearch performance"}}
                ],
                "filter": [
                    {"range": {"published_at": {"gte": "2024-01-01"}}},
                    {"terms": {"tags": ["elasticsearch"]}}
                ]
            }
        },
        "sort": [{"published_at": "desc"}, "_score"],
        "highlight": {
            "fields": {"content": {"fragment_size": 150, "number_of_fragments": 3}}
        },
        "aggs": {
            "tags_count": {"terms": {"field": "tags.keyword", "size": 20}}
        },
        "_source": ["title", "author", "published_at", "tags"],
        "size": 10
    }
)

for hit in resp["hits"]["hits"]:
    print(f"{hit['_source']['title']} — score: {hit['_score']}")
    if "highlight" in hit:
        for fragment in hit["highlight"].get("content", []):
            print(f"  ... {fragment} ...")
```

---

## Apache Kafka → Elasticsearch

### Kafka Connect: Elasticsearch Sink Connector

Il connettore ufficiale Confluent (o il community connector) consuma topic Kafka e indicizza documenti in Elasticsearch.

```json
{
  "name": "elasticsearch-sink-events",
  "config": {
    "connector.class": "io.confluent.connect.elasticsearch.ElasticsearchSinkConnector",
    "tasks.max": "4",
    "topics": "user-events,purchase-events",
    "connection.url": "https://es-node1:9200,https://es-node2:9200",
    "connection.username": "${file:/etc/kafka/secrets.properties:es.username}",
    "connection.password": "${file:/etc/kafka/secrets.properties:es.password}",
    "elastic.security.protocol": "SSL",
    "elastic.https.ssl.keystore.location": "/etc/kafka/certs/kafka.client.keystore.jks",

    "type.name": "_doc",
    "key.ignore": "false",
    "schema.ignore": "true",

    "behavior.on.malformed.documents": "warn",
    "behavior.on.null.values": "delete",      # null value → delete del documento
    "drop.invalid.message": "true",

    "batch.size": "2000",
    "linger.ms": "100",
    "max.buffered.records": "20000",
    "max.in.flight.requests": "5",
    "flush.timeout.ms": "10000",
    "read.timeout.ms": "30000",

    "transforms": "unwrap,addTimestamp",
    "transforms.unwrap.type": "io.debezium.transforms.ExtractNewRecordState",
    "transforms.addTimestamp.type": "org.apache.kafka.connect.transforms.InsertField$Value",
    "transforms.addTimestamp.timestamp.field": "kafka_ingest_time"
  }
}
```

### Consumer Python Custom

```python
from kafka import KafkaConsumer
from elasticsearch.helpers import bulk
from elasticsearch import Elasticsearch
import json, time

es = Elasticsearch(hosts=["https://es:9200"], basic_auth=("elastic", "pass"))

consumer = KafkaConsumer(
    "user-events",
    bootstrap_servers=["kafka1:9092"],
    group_id="es-indexer",
    value_deserializer=lambda v: json.loads(v.decode()),
    auto_offset_reset="earliest",
    enable_auto_commit=False,
    max_poll_records=500,
)

BATCH_SIZE = 500
FLUSH_INTERVAL = 5.0  # secondi

buffer = []
last_flush = time.time()

def flush_buffer(buf):
    if not buf:
        return
    actions = [
        {"_index": "user-events", "_id": doc.get("event_id"), "_source": doc}
        for doc in buf
    ]
    success, errors = bulk(es, actions, raise_on_error=False)
    print(f"Flushed {success} docs, {len(errors)} errors")
    return success

for message in consumer:
    buffer.append(message.value)
    now = time.time()
    if len(buffer) >= BATCH_SIZE or (now - last_flush) >= FLUSH_INTERVAL:
        flush_buffer(buffer)
        consumer.commit()
        buffer.clear()
        last_flush = now
```

---

## Apache Spark → Elasticsearch

Il connettore ufficiale **elasticsearch-hadoop** espone sia un DataSource che RDD API.

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("ES-Spark-Integration") \
    .config("spark.jars.packages",
            "org.elasticsearch:elasticsearch-spark-30_2.12:8.11.0") \
    .config("es.nodes", "es-node1,es-node2") \
    .config("es.port", "9200") \
    .config("es.net.ssl", "true") \
    .config("es.net.ssl.cert.allow.self.signed", "false") \
    .config("es.net.http.auth.user", "elastic") \
    .config("es.net.http.auth.pass", "changeme") \
    .getOrCreate()

# Lettura da Elasticsearch
df_es = spark.read \
    .format("org.elasticsearch.spark.sql") \
    .option("es.resource", "products/_doc") \
    .option("es.query", '{"query": {"range": {"price": {"gte": 100}}}}') \
    .option("es.read.field.include", "sku,name,price,category") \
    .load()

df_es.show(5)
df_es.createOrReplaceTempView("products")

# Trasformazione
df_enriched = spark.sql("""
    SELECT sku, name, price, category,
           price * 0.22 as vat_amount,
           CASE WHEN price > 1000 THEN 'premium' ELSE 'standard' END as tier
    FROM products
""")

# Scrittura su Elasticsearch
df_enriched.write \
    .format("org.elasticsearch.spark.sql") \
    .option("es.resource", "products-enriched/_doc") \
    .option("es.mapping.id", "sku") \
    .option("es.write.operation", "upsert") \
    .option("es.batch.size.bytes", "20mb") \
    .option("es.batch.size.entries", "5000") \
    .option("es.batch.write.refresh", "false") \
    .mode("append") \
    .save()
```

---

## Kibana: Pattern di Utilizzo Programmatico

### Saved Objects API

Kibana espone le Saved Objects API per creare dashboard, index patterns e visualizzazioni via codice — utile per deployment automatizzati.

```bash
# Creare un index pattern
curl -X POST "https://kibana:5601/api/saved_objects/index-pattern/logs-*" \
  -H "kbn-xsrf: true" \
  -H "Content-Type: application/json" \
  -u elastic:changeme \
  -d '{
    "attributes": {
      "title": "logs-*",
      "timeFieldName": "@timestamp"
    }
  }'

# Export dashboard (per backup/migration)
curl -X POST "https://kibana:5601/api/saved_objects/_export" \
  -H "kbn-xsrf: true" \
  -H "Content-Type: application/json" \
  -u elastic:changeme \
  -d '{
    "type": "dashboard",
    "includeReferencesDeep": true
  }' > dashboard-export.ndjson

# Import dashboard
curl -X POST "https://kibana:5601/api/saved_objects/_import" \
  -H "kbn-xsrf: true" \
  -u elastic:changeme \
  -F "file=@dashboard-export.ndjson"
```

### Kibana Alerting API

```python
import requests

kibana_url = "https://kibana:5601"
headers = {"kbn-xsrf": "true", "Content-Type": "application/json"}
auth = ("elastic", "changeme")

# Creare un rule per alerting su ES query
rule = {
    "name": "High Error Rate Alert",
    "rule_type_id": "es_query",
    "schedule": {"interval": "5m"},
    "params": {
        "index": ["logs-*"],
        "timeField": "@timestamp",
        "esQuery": '{"query":{"term":{"level":"ERROR"}}}',
        "timeWindowSize": 5,
        "timeWindowUnit": "m",
        "thresholdComparator": ">",
        "threshold": [100]
    },
    "actions": [
        {
            "id": "slack-connector-id",
            "group": "threshold met",
            "params": {
                "message": "Alert: {{context.title}} - {{context.value}} errors in 5m"
            }
        }
    ]
}

resp = requests.post(
    f"{kibana_url}/api/alerting/rule",
    json=rule,
    headers=headers,
    auth=auth
)
print(resp.json()["id"])
```

---

## Ingest Pipelines: Processamento Lato Elasticsearch

Le **Ingest Pipelines** permettono di trasformare i documenti prima dell'indicizzazione, eliminando Logstash per casi semplici.

```python
# Creare una pipeline via Python
pipeline = {
    "description": "Parsa log Nginx e arricchisce con GeoIP",
    "processors": [
        {
            "grok": {
                "field": "message",
                "patterns": [
                    '%{IPORHOST:client_ip} - - \\[%{HTTPDATE:timestamp}\\] "%{WORD:method} %{URIPATHPARAM:path} HTTP/%{NUMBER:http_version}" %{NUMBER:status:int} %{NUMBER:bytes:int}'
                ]
            }
        },
        {
            "date": {
                "field": "timestamp",
                "formats": ["dd/MMM/yyyy:HH:mm:ss Z"],
                "target_field": "@timestamp"
            }
        },
        {
            "geoip": {
                "field": "client_ip",
                "target_field": "geo",
                "properties": ["country_name", "city_name", "location"]
            }
        },
        {
            "user_agent": {
                "field": "user_agent_string",
                "target_field": "ua"
            }
        },
        {
            "remove": {
                "field": ["message", "timestamp"],
                "ignore_missing": True
            }
        },
        {
            "set": {
                "field": "ingest_timestamp",
                "value": "{{_ingest.timestamp}}"
            }
        }
    ],
    "on_failure": [
        {
            "set": {
                "field": "_index",
                "value": "failed-{{ _index }}"
            }
        }
    ]
}

es.ingest.put_pipeline(id="nginx-pipeline", body=pipeline)

# Indicizza usando la pipeline
es.index(
    index="logs-nginx",
    document={"message": '192.168.1.1 - - [15/Jan/2024:10:00:00 +0000] "GET /api/health HTTP/1.1" 200 42'},
    pipeline="nginx-pipeline"
)

# Imposta pipeline di default su un indice (tramite index settings)
es.indices.put_settings(
    index="logs-nginx-*",
    settings={"index.default_pipeline": "nginx-pipeline"}
)
```

---

## Integrazione con sistemi di Caching e CDN

### Elasticsearch + Redis (Cache a due livelli)

Pattern comune: Redis come cache L1 (query frequenti con TTL breve), Elasticsearch come backend autoritativo.

```python
import redis
import json
import hashlib
from elasticsearch import Elasticsearch

r = redis.Redis(host="redis", port=6379, db=0, decode_responses=True)
es = Elasticsearch(hosts=["https://es:9200"], basic_auth=("elastic", "pass"))

CACHE_TTL = 300  # 5 minuti

def cached_search(index: str, query: dict) -> dict:
    # Chiave cache basata su hash della query
    cache_key = f"es:search:{index}:{hashlib.md5(json.dumps(query, sort_keys=True).encode()).hexdigest()}"

    cached = r.get(cache_key)
    if cached:
        return json.loads(cached)

    result = es.search(index=index, body=query)
    serializable = {
        "hits": result["hits"]["hits"],
        "total": result["hits"]["total"]["value"],
        "aggregations": result.get("aggregations", {}),
    }
    r.setex(cache_key, CACHE_TTL, json.dumps(serializable))
    return serializable
```

---

## Monitoraggio dell'Integrazione

### Metriche chiave da esporre per il bulk indexing

```python
from prometheus_client import Counter, Histogram, start_http_server
import time

docs_indexed = Counter("es_docs_indexed_total", "Documenti indicizzati", ["index", "status"])
bulk_duration = Histogram("es_bulk_duration_seconds", "Durata bulk request", buckets=[0.1, 0.5, 1, 5, 10])

def instrumented_bulk(es_client, actions, **kwargs):
    start = time.time()
    success, errors = bulk(es_client, actions, raise_on_error=False, **kwargs)
    duration = time.time() - start

    bulk_duration.observe(duration)
    docs_indexed.labels(index="default", status="success").inc(success)
    docs_indexed.labels(index="default", status="error").inc(len(errors))
    return success, errors
```

Le integrazioni di Elasticsearch coprono l'intero ciclo dei dati: raccolta con i Beats, trasformazione con Logstash o Ingest Pipelines, analisi con Spark, visualizzazione con Kibana. La scelta del layer di ingestione dipende dalla complessità delle trasformazioni richieste e dalla latenza accettabile.
