# Elasticsearch — Casi d'Uso e Pattern Architetturali

## Log Analytics: La Pipeline ELK Classica

Il caso d'uso più consolidato di Elasticsearch è l'analisi di log applicativi e di infrastruttura. L'architettura di riferimento prevede:

1. **Raccolta**: Filebeat/Fluentd sui server di produzione
2. **Buffer**: Kafka come message broker per assorbire picchi di ingestione
3. **Trasformazione**: Logstash o Ingest Pipelines per parsing e arricchimento
4. **Storage**: Elasticsearch con ILM per gestione del ciclo di vita
5. **Visualizzazione**: Kibana Discover + dashboard customizzate

### Schema di Indice per Log

```json
{
  "mappings": {
    "properties": {
      "@timestamp":    { "type": "date" },
      "host":          { "properties": {
                           "name": { "type": "keyword" },
                           "ip":   { "type": "ip" }
                       }},
      "service":       { "type": "keyword" },
      "environment":   { "type": "keyword" },
      "level":         { "type": "keyword" },
      "message":       { "type": "text", "norms": false },
      "error": {
        "properties": {
          "type":       { "type": "keyword" },
          "message":    { "type": "text" },
          "stack_trace":{ "type": "text", "index": false }
        }
      },
      "http": {
        "properties": {
          "method":       { "type": "keyword" },
          "status_code":  { "type": "short" },
          "url":          { "type": "keyword" },
          "response_time":{ "type": "float" }
        }
      },
      "geo": {
        "properties": {
          "country_code": { "type": "keyword" },
          "city":         { "type": "keyword" },
          "location":     { "type": "geo_point" }
        }
      },
      "trace_id":      { "type": "keyword" },
      "span_id":       { "type": "keyword" }
    }
  },
  "settings": {
    "number_of_shards": 2,
    "number_of_replicas": 1,
    "index.codec": "best_compression",
    "index.refresh_interval": "30s"
  }
}
```

### Query Pattern: Analisi Errori

```json
// Top errori nelle ultime 24 ore, raggruppati per tipo
{
  "query": {
    "bool": {
      "filter": [
        { "term": { "level": "ERROR" } },
        { "range": { "@timestamp": { "gte": "now-24h" } } }
      ]
    }
  },
  "aggs": {
    "error_types": {
      "terms": {
        "field": "error.type",
        "size": 20,
        "order": { "_count": "desc" }
      },
      "aggs": {
        "timeline": {
          "date_histogram": {
            "field": "@timestamp",
            "calendar_interval": "1h"
          }
        },
        "sample": {
          "top_hits": {
            "size": 1,
            "_source": ["message", "error.message", "service", "host.name"]
          }
        }
      }
    },
    "services_affected": {
      "cardinality": { "field": "service" }
    }
  },
  "size": 0
}
```

---

## Full-Text Search per E-Commerce

La ricerca prodotti è uno dei casi d'uso più complessi — richiede bilanciamento tra rilevanza testuale, boost per business, filtri strutturati e faceted navigation.

### Mapping Prodotti

```json
{
  "mappings": {
    "properties": {
      "product_id":     { "type": "keyword" },
      "sku":            { "type": "keyword" },
      "name": {
        "type": "text",
        "analyzer": "italian",
        "fields": {
          "keyword":    { "type": "keyword", "ignore_above": 256 },
          "suggest":    { "type": "search_as_you_type" },
          "english":    { "type": "text", "analyzer": "english" }
        }
      },
      "description":    { "type": "text", "analyzer": "italian" },
      "brand":          { "type": "keyword" },
      "category":       { "type": "keyword" },
      "price":          { "type": "scaled_float", "scaling_factor": 100 },
      "discount_pct":   { "type": "float" },
      "rating":         { "type": "float" },
      "reviews_count":  { "type": "integer" },
      "in_stock":       { "type": "boolean" },
      "attributes":     { "type": "nested",
                          "properties": {
                            "name":  { "type": "keyword" },
                            "value": { "type": "keyword" }
                          }},
      "image_url":      { "type": "keyword", "index": false },
      "popularity_score":{ "type": "float" },
      "created_at":     { "type": "date" }
    }
  }
}
```

### Query di Ricerca con Rilevanza Personalizzata

```json
{
  "query": {
    "function_score": {
      "query": {
        "bool": {
          "must": [
            {
              "multi_match": {
                "query": "scarpe running uomo",
                "fields": ["name^3", "description^1", "brand^2"],
                "type": "best_fields",
                "tie_breaker": 0.3,
                "fuzziness": "AUTO",
                "prefix_length": 2
              }
            }
          ],
          "filter": [
            { "term": { "in_stock": true } },
            { "range": { "price": { "gte": 50, "lte": 300 } } }
          ],
          "should": [
            { "term": { "category": { "value": "running", "boost": 1.5 } } }
          ]
        }
      },
      "functions": [
        {
          "gauss": {
            "price": {
              "origin": "100",
              "scale": "50",
              "decay": 0.5
            }
          },
          "weight": 1.5
        },
        {
          "field_value_factor": {
            "field": "popularity_score",
            "modifier": "log1p",
            "factor": 0.5
          }
        },
        {
          "filter": { "term": { "brand": "Nike" } },
          "weight": 1.2
        }
      ],
      "score_mode": "sum",
      "boost_mode": "multiply"
    }
  },
  "aggs": {
    "brands": {
      "terms": { "field": "brand", "size": 20 }
    },
    "price_ranges": {
      "range": {
        "field": "price",
        "ranges": [
          { "to": 50 },
          { "from": 50, "to": 100 },
          { "from": 100, "to": 200 },
          { "from": 200 }
        ]
      }
    },
    "colors": {
      "nested": { "path": "attributes" },
      "aggs": {
        "color_filter": {
          "filter": { "term": { "attributes.name": "colore" } },
          "aggs": {
            "values": { "terms": { "field": "attributes.value" } }
          }
        }
      }
    },
    "avg_price": { "avg": { "field": "price" } }
  },
  "highlight": {
    "fields": {
      "name": { "number_of_fragments": 0 },
      "description": { "fragment_size": 100, "number_of_fragments": 2 }
    }
  }
}
```

### Autocomplete e Search-as-you-type

```json
// Mapping con search_as_you_type (già nel mapping sopra per "name.suggest")

// Query autocomplete
{
  "query": {
    "multi_match": {
      "query": "scar",
      "type": "bool_prefix",
      "fields": [
        "name.suggest",
        "name.suggest._2gram",
        "name.suggest._3gram"
      ]
    }
  },
  "size": 10,
  "_source": ["product_id", "name", "price", "image_url"]
}
```

**Suggesters** alternativi per autocomplete:

```json
{
  "suggest": {
    "product-suggest": {
      "prefix": "scar",
      "completion": {
        "field": "name_completion",
        "size": 10,
        "fuzzy": { "fuzziness": 1 },
        "contexts": {
          "in_stock": [{ "context": "true" }]
        }
      }
    }
  }
}
```

---

## APM: Application Performance Monitoring

Elastic APM è integrato nella stack e raccoglie trace, metriche e log con correlazione automatica via `trace_id`.

### Struttura degli Indici APM

- `apm-*-transaction-*`: ogni transazione HTTP/gRPC/custom
- `apm-*-span-*`: span figli della transazione (query DB, chiamate HTTP esterne)
- `apm-*-error-*`: eccezioni e stack trace
- `apm-*-metric-*`: metriche JVM, sistema operativo

### Query: Distribuzione Latenza per Endpoint

```json
{
  "query": {
    "bool": {
      "filter": [
        { "term": { "service.name": "order-service" } },
        { "term": { "transaction.type": "request" } },
        { "range": { "@timestamp": { "gte": "now-1h" } } }
      ]
    }
  },
  "aggs": {
    "endpoints": {
      "terms": {
        "field": "transaction.name",
        "size": 20,
        "order": { "p99_latency.values.99_0": "desc" }
      },
      "aggs": {
        "p99_latency": {
          "percentiles": {
            "field": "transaction.duration.us",
            "percents": [50, 75, 95, 99]
          }
        },
        "error_rate": {
          "filters": {
            "filters": {
              "success": { "term": { "event.outcome": "success" } },
              "failure": { "term": { "event.outcome": "failure" } }
            }
          }
        }
      }
    }
  },
  "size": 0
}
```

---

## SIEM: Security Information and Event Management

Elastic SIEM (parte di Elastic Security) indicizza eventi di sicurezza da Winlogbeat, Auditbeat, e sorgenti esterne in indici dedicati.

### Pattern di Detection: Brute Force SSH

```json
// Rileva tentativi di brute force: >10 fallimenti SSH dallo stesso IP in 5 minuti
{
  "query": {
    "bool": {
      "filter": [
        { "term": { "event.category": "authentication" } },
        { "term": { "event.outcome": "failure" } },
        { "term": { "process.name": "sshd" } },
        { "range": { "@timestamp": { "gte": "now-5m" } } }
      ]
    }
  },
  "aggs": {
    "source_ips": {
      "terms": {
        "field": "source.ip",
        "size": 100,
        "min_doc_count": 10
      },
      "aggs": {
        "target_users": {
          "terms": { "field": "user.name", "size": 10 }
        }
      }
    }
  },
  "size": 0
}
```

### ECS (Elastic Common Schema)

Per l'interoperabilità tra sorgenti diverse, Elasticsearch ha standardizzato il formato degli eventi con **ECS**. Campi chiave:

| Campo ECS | Tipo | Descrizione |
|-----------|------|-------------|
| `@timestamp` | date | Momento dell'evento |
| `event.category` | keyword | `authentication`, `network`, `process` |
| `event.type` | keyword | `start`, `end`, `access`, `error` |
| `event.outcome` | keyword | `success`, `failure`, `unknown` |
| `source.ip` | ip | IP sorgente |
| `destination.port` | integer | Porta destinazione |
| `user.name` | keyword | Username |
| `host.name` | keyword | Hostname |
| `process.name` | keyword | Nome processo |
| `network.protocol` | keyword | `tcp`, `udp`, `http` |

---

## Ricerca Vettoriale e Ibrida: BM25 + kNN

Elasticsearch 8.x supporta **dense_vector** e ricerca approssimativa kNN (HNSW algorithm) per semantic search.

### Mapping con Vettori

```json
{
  "mappings": {
    "properties": {
      "doc_id":    { "type": "keyword" },
      "title":     { "type": "text", "analyzer": "italian" },
      "content":   { "type": "text", "analyzer": "italian" },
      "embedding": {
        "type": "dense_vector",
        "dims": 768,
        "index": true,
        "similarity": "cosine"
      }
    }
  }
}
```

### Generazione Embedding e Indicizzazione

```python
from sentence_transformers import SentenceTransformer
from elasticsearch.helpers import bulk
from elasticsearch import Elasticsearch

model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
es = Elasticsearch(hosts=["https://es:9200"], basic_auth=("elastic", "pass"))

def index_documents(documents):
    texts = [d["title"] + " " + d["content"] for d in documents]
    embeddings = model.encode(texts, batch_size=32, show_progress_bar=True)

    def actions():
        for doc, emb in zip(documents, embeddings):
            yield {
                "_index": "knowledge-base",
                "_id": doc["doc_id"],
                "_source": {**doc, "embedding": emb.tolist()}
            }

    bulk(es, actions(), chunk_size=100)
```

### Ricerca Ibrida: Semantica + BM25

```python
def hybrid_search(query_text: str, top_k: int = 10):
    query_embedding = model.encode(query_text).tolist()

    resp = es.search(
        index="knowledge-base",
        body={
            "query": {
                "bool": {
                    "should": [
                        # BM25 lexical
                        {
                            "multi_match": {
                                "query": query_text,
                                "fields": ["title^2", "content"],
                                "boost": 0.5
                            }
                        }
                    ]
                }
            },
            # kNN semantico
            "knn": {
                "field": "embedding",
                "query_vector": query_embedding,
                "k": top_k,
                "num_candidates": top_k * 5,
                "boost": 0.5
            },
            "size": top_k,
            "_source": ["doc_id", "title"],
            "rank": {
                "rrf": {
                    "window_size": 100,
                    "rank_constant": 60
                }
            }
        }
    )
    return resp["hits"]["hits"]
```

**Reciprocal Rank Fusion (RRF)**: algoritmo di fusione che combina i ranking BM25 e kNN senza richiedere normalizzazione manuale degli score. Disponibile da ES 8.9.

---

## Pattern: Multi-Tenancy con Routing e Aliases

Per sistemi SaaS multi-tenant, ci sono tre strategie:

### Strategia 1: Un indice per tenant (small tenants)

```python
def get_tenant_index(tenant_id: str) -> str:
    return f"data-{tenant_id}"

# Alias per operazioni cross-tenant
es.indices.put_alias(
    index="data-tenant-*",
    name="data-all-tenants"
)
```

### Strategia 2: Indice condiviso con routing

```python
# Tutti i tenant nello stesso indice, dati co-localizzati per shard
es.index(
    index="shared-data",
    id=f"{tenant_id}-{doc_id}",
    routing=tenant_id,  # forza stesso shard per tenant
    document={
        "tenant_id": tenant_id,
        "data": payload
    }
)

# Query con routing
es.search(
    index="shared-data",
    routing=tenant_id,
    body={
        "query": {
            "bool": {
                "filter": [{"term": {"tenant_id": tenant_id}}]
            }
        }
    }
)
```

### Strategia 3: ILM + Rollover per volume elevato

```python
# Creare alias di scrittura con rollover
es.indices.create(
    index=f"tenant-{tenant_id}-000001",
    body={
        "aliases": {
            f"tenant-{tenant_id}": {"is_write_index": True}
        }
    }
)

# Il rollover avviene automaticamente quando:
# - index age > soglia (es. 7d)
# - doc count > soglia (es. 50M)
# - size > soglia (es. 50GB)
```

---

## Pattern: Scroll API vs Search After vs PIT

Per paginare grandi result set, ci sono tre approcci con caratteristiche diverse.

### Scroll (deprecato per deep pagination)

```python
# NON usare per UI pagination — snapshot costoso in RAM
resp = es.search(index="logs-*", scroll="5m", body={"query": {"match_all": {}}, "size": 1000})
scroll_id = resp["_scroll_id"]

all_hits = resp["hits"]["hits"]
while True:
    resp = es.scroll(scroll_id=scroll_id, scroll="5m")
    if not resp["hits"]["hits"]:
        break
    all_hits.extend(resp["hits"]["hits"])

es.clear_scroll(scroll_id=scroll_id)  # SEMPRE liberare
```

### Search After + PIT (raccomandato)

```python
# Creare un Point in Time (snapshot consistente)
pit = es.open_point_in_time(index="logs-*", keep_alive="5m")
pit_id = pit["id"]

try:
    last_sort = None
    while True:
        body = {
            "query": {"range": {"@timestamp": {"gte": "now-7d"}}},
            "sort": [{"@timestamp": "asc"}, {"_id": "asc"}],
            "size": 1000,
            "pit": {"id": pit_id, "keep_alive": "5m"}
        }
        if last_sort:
            body["search_after"] = last_sort

        resp = es.search(body=body)
        hits = resp["hits"]["hits"]
        if not hits:
            break

        process_batch(hits)
        last_sort = hits[-1]["sort"]
        pit_id = resp["pit_id"]  # il PIT può cambiare, aggiorna
finally:
    es.close_point_in_time(id=pit_id)
```

---

## Indici di Sistema e Diagnostica

### Pattern di Healthcheck Operativo

```python
def elasticsearch_healthcheck(es: Elasticsearch) -> dict:
    health = es.cluster.health(timeout="5s")
    stats = es.cluster.stats()

    return {
        "status": health["status"],           # green/yellow/red
        "nodes": health["number_of_nodes"],
        "shards": {
            "active": health["active_shards"],
            "unassigned": health["unassigned_shards"],
            "relocating": health["relocating_shards"],
        },
        "indices_count": stats["indices"]["count"],
        "docs_count": stats["indices"]["docs"]["count"],
        "store_size_gb": stats["indices"]["store"]["size_in_bytes"] / 1e9,
        "jvm_heap_used_pct": max(
            n["jvm"]["mem"]["heap_used_percent"]
            for n in es.nodes.stats()["nodes"].values()
        )
    }
```

### Indici ad Alta Scrittura: Configurazione Ottimale

Per indici che ricevono milioni di documenti al giorno:

```json
{
  "settings": {
    "index.refresh_interval": "30s",
    "index.translog.durability": "async",
    "index.translog.flush_threshold_size": "1gb",
    "index.translog.sync_interval": "30s",
    "index.merge.policy.max_merged_segment": "5gb",
    "index.merge.scheduler.max_thread_count": 1,
    "index.number_of_replicas": 0
  }
}
```

Dopo il caricamento massivo, riabilitare le repliche:

```bash
PUT /my-bulk-index/_settings
{
  "index.number_of_replicas": 1,
  "index.refresh_interval": "1s"
}
```

---

## Considerazioni Architetturali per la Scelta del Pattern

| Caso d'Uso | Pattern Raccomandato | Motivazione |
|------------|---------------------|-------------|
| Log analytics (<1TB/giorno) | ELK + ILM | Maturità, integrazione Kibana |
| Full-text search prodotti | Query DSL + function_score | Controllo fine sulla rilevanza |
| Ricerca semantica | kNN + RRF | Comprensione semantica della query |
| SIEM / Security | ECS + detection rules | Standard di interoperabilità |
| APM / Tracing | Elastic APM agent | Correlazione automatica |
| Multi-tenant SaaS | Routing + alias per scrittura | Isolamento dati, performance |
| Export massivo dati | PIT + search_after | Consistenza snapshot, efficienza memoria |
| Dashboard real-time | Aggregazioni + refresh breve | Latenza accettabile per analytics |

La scelta del pattern architetturale deve considerare non solo le esigenze funzionali ma anche il volume dei dati, i requisiti di latenza e i vincoli di manutenzione operativa del cluster.
