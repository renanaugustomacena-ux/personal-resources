# Query DSL di Elasticsearch

> Autori: Team Data Encyclopedia  
> Ultimo aggiornamento: 2026-05-22  
> Versione: 2.0.0  
> Stato: expanded

## Indice
1. Query Context vs Filter Context
2. Leaf Queries: Term-Level
3. Full-Text Queries
4. Compound Queries
5. Paginazione Efficiente
6. Specialized Queries
7. Sorting and Source Filtering
8. Highlighting
9. Suggesters
10. Rescoring
11. ES|QL (ES 8.11+)
12. Troubleshooting
13. FAQ

---

## 1. Query Context vs Filter Context

### 1.1 La Distinzione Fondamentale

Elasticsearch distingue due contesti di esecuzione: il **query context** (quanto bene corrisponde? → calcola `_score`) e il **filter context** (corrisponde o no? → valutazione binaria, cacheable). Il filter context è più veloce perché non calcola BM25/TF-IDF e i risultati vengono memorizzati in roaring bitset per riuso nelle query successive.

```http
POST /prodotti/_search
{
  "query": {
    "bool": {
      "must":   [{ "match": { "descrizione": "scarpe running" } }],
      "filter": [
        { "term":  { "disponibile": true } },
        { "range": { "prezzo": { "gte": 50, "lte": 200 } } }
      ]
    }
  }
}
```

### 1.2 When to Use Filter vs Query Context

Use **filter context** for:
- Exact value matching (status codes, IDs, booleans)
- Date/numeric ranges where relevance does not matter
- Geo bounding box or distance filters
- Any clause where you need "yes/no" without scoring

Use **query context** for:
- Full-text search where ranking matters
- Fuzzy matching
- Any clause where the quality of the match determines result order

Combining both is the standard pattern: `must` for scoring, `filter` for narrowing:

```http
POST /articles/_search
{
  "query": {
    "bool": {
      "must": [
        { "match": { "content": "distributed systems" } }
      ],
      "filter": [
        { "term": { "status": "published" } },
        { "range": { "date": { "gte": "2025-01-01" } } }
      ],
      "should": [
        { "term": { "featured": { "value": true, "boost": 2.0 } } }
      ]
    }
  }
}
```

### 1.3 Filter Cache Behavior

Filters are cached in the **node query cache** (default 10% of heap). The cache stores roaring bitmaps keyed by (filter, segment). When a segment is merged away, its cache entries are invalidated automatically.

```http
// Check query cache usage per node
GET /_nodes/stats/indices/query_cache?human=true

// Disable caching for a specific filter (useful for high-cardinality rapidly changing data)
POST /my-index/_search
{
  "query": {
    "bool": {
      "filter": [
        {
          "range": {
            "@timestamp": {
              "gte": "now-1h",
              "_cache": false
            }
          }
        }
      ]
    }
  }
}

// Clear the query cache for an index
POST /my-index/_cache/clear?query=true
```

---

## 2. Leaf Queries: Term-Level

### 2.1 term, terms, range, exists

```http
// term: valore esatto su keyword/numeric/boolean
{ "query": { "term": { "stato": { "value": "attivo", "boost": 1.5 } } } }

// terms: match su uno qualsiasi dei valori (SQL IN)
{ "query": { "terms": { "categoria": ["elettronica", "informatica"] } } }

// range su date con timezone
{
  "query": {
    "range": {
      "data_creazione": {
        "gte": "2026-01-01", "lt": "2026-06-01",
        "format": "yyyy-MM-dd", "time_zone": "+01:00"
      }
    }
  }
}

// exists: il campo esiste e non è null
{ "query": { "exists": { "field": "indirizzo_email" } } }

// wildcard: pattern con * e ?
{ "query": { "wildcard": { "nome.keyword": { "value": "Mario*" } } } }

// fuzzy: corrispondenza con distanza di edit Levenshtein
{ "query": { "fuzzy": { "titolo": { "value": "elsticsearch", "fuzziness": "AUTO" } } } }
```

### 2.2 terms_set and ids

```http
// terms_set: requires a minimum number of terms to match (useful for tag-based filtering)
POST /recipes/_search
{
  "query": {
    "terms_set": {
      "ingredients": {
        "terms": ["flour", "sugar", "butter", "eggs"],
        "minimum_should_match_field": "required_match_count"
      }
    }
  }
}

// ids: fetch documents by their _id values directly
{ "query": { "ids": { "values": ["doc-001", "doc-002", "doc-003"] } } }
```

### 2.3 prefix, regexp, and wildcard

These queries operate on the inverted index term dictionary. They can be expensive because they potentially scan many terms:

```http
// prefix: efficient if the field uses a keyword type (binary search on sorted terms)
{ "query": { "prefix": { "sku.keyword": { "value": "PROD-2026" } } } }

// regexp: Lucene regular expressions (NOT PCRE — no backreferences, no lookahead)
{
  "query": {
    "regexp": {
      "product_code": {
        "value": "[A-Z]{2}-[0-9]{4,6}",
        "flags": "COMPLEMENT|INTERVAL",
        "max_determinized_states": 10000
      }
    }
  }
}

// wildcard: * matches zero or more characters, ? matches exactly one
// Avoid leading wildcards (*pattern) — they force a full term scan
{
  "query": {
    "wildcard": {
      "email.keyword": {
        "value": "*@example.com",
        "case_insensitive": true
      }
    }
  }
}
```

**Performance note**: `wildcard` and `regexp` queries with leading wildcards bypass the term dictionary's sorted structure and scan all terms. For frequent prefix-style queries, use `edge_ngram` tokenizer at index time instead.

### 2.4 Range Query on Numeric and Date Types

```http
// Numeric range with relation parameter for range fields
{
  "query": {
    "range": {
      "age": {
        "gte": 18,
        "lt": 65,
        "relation": "WITHIN"
      }
    }
  }
}

// Date math expressions
{
  "query": {
    "range": {
      "@timestamp": {
        "gte": "now-7d/d",
        "lt": "now/d",
        "time_zone": "Europe/Rome"
      }
    }
  }
}
// now-7d/d = 7 days ago, rounded down to the start of the day
// now/d   = today, rounded down to the start of the day

// Date math anchored to a specific date
{
  "query": {
    "range": {
      "date": {
        "gte": "2026-01-01||+1M/d",
        "lt": "2026-01-01||+2M/d"
      }
    }
  }
}
```

---

## 3. Full-Text Queries

### 3.1 match e match_phrase

Le full-text queries analizzano il testo di input con lo stesso analyzer del campo target prima di eseguire la ricerca. `match` è la query full-text standard; `match_phrase` richiede che i termini appaiano nell'ordine dato.

```http
// match: termini in OR di default, operator:and per richiedere tutti
{
  "query": {
    "match": {
      "contenuto": {
        "query": "ricerca full text",
        "operator": "and",
        "fuzziness": "AUTO",
        "minimum_should_match": "75%"
      }
    }
  }
}

// match_phrase con slop (permette N parole tra i termini)
{
  "query": {
    "match_phrase": {
      "titolo": { "query": "machine learning", "slop": 1 }
    }
  }
}

// multi_match su più campi con boost
{
  "query": {
    "multi_match": {
      "query": "database performance",
      "fields": ["titolo^3", "sommario^2", "corpo"],
      "type": "best_fields",
      "tie_breaker": 0.3
    }
  }
}
```

### 3.2 multi_match Types Deep Dive

The `type` parameter in `multi_match` fundamentally changes how scoring works:

```http
// best_fields (default): takes the score from the BEST matching field
// Use when the same concept is in one field at a time (title OR description)
{
  "query": {
    "multi_match": {
      "query": "elasticsearch guide",
      "fields": ["title^3", "description"],
      "type": "best_fields",
      "tie_breaker": 0.3
    }
  }
}

// most_fields: sums the scores from ALL matching fields
// Use with multi-field analysis (same text analyzed differently)
{
  "query": {
    "multi_match": {
      "query": "elasticsearch guide",
      "fields": ["title", "title.english", "title.stemmed"],
      "type": "most_fields"
    }
  }
}

// cross_fields: treats ALL fields as one big field
// Use for data split across fields (first_name + last_name)
{
  "query": {
    "multi_match": {
      "query": "Mario Rossi",
      "fields": ["first_name", "last_name"],
      "type": "cross_fields",
      "operator": "and"
    }
  }
}

// phrase_prefix: match_phrase + prefix on last term (for search-as-you-type)
{
  "query": {
    "multi_match": {
      "query": "elastic sea",
      "fields": ["title", "content"],
      "type": "phrase_prefix",
      "max_expansions": 50
    }
  }
}
```

### 3.3 match_bool_prefix

A specialized query that combines `match` with prefix matching on the last term. Ideal for autocomplete without the overhead of edge_ngram:

```http
{
  "query": {
    "match_bool_prefix": {
      "product_name": {
        "query": "elastic sear",
        "analyzer": "standard"
      }
    }
  }
}
// Internally becomes: bool(must: [term("elastic"), prefix("sear")])
```

### 3.4 query_string e simple_query_string

```http
// query_string: sintassi Lucene completa (NON usare con input utente non validato)
{
  "query": {
    "query_string": {
      "default_field": "contenuto",
      "query": "titolo:(elastic OR kibana) AND data:[2025-01-01 TO *]"
    }
  }
}

// simple_query_string: sicuro per input utente
{
  "query": {
    "simple_query_string": {
      "fields": ["titolo^2", "corpo"],
      "query": "elastic + kibana - logstash",
      "default_operator": "and"
    }
  }
}
```

### 3.5 combined_fields (ES 8.x)

`combined_fields` is designed for searching across multiple text fields that share the same analyzer. Unlike `cross_fields`, it uses a single BM25 model across all fields, producing more predictable scoring:

```http
{
  "query": {
    "combined_fields": {
      "query": "distributed search engine",
      "fields": ["title", "abstract", "body"],
      "operator": "or",
      "minimum_should_match": "50%"
    }
  }
}
```

---

## 4. Compound Queries

### 4.1 bool Query

```http
POST /documenti/_search
{
  "query": {
    "bool": {
      "must":     [{ "match": { "titolo": "elasticsearch performance" } }],
      "should":   [
        { "term":  { "tag": "tutorial" } },
        { "range": { "visualizzazioni": { "gte": 1000 } } }
      ],
      "must_not": [{ "term": { "stato": "bozza" } }],
      "filter":   [
        { "term":  { "lingua": "it" } },
        { "range": { "data": { "gte": "now-1y" } } }
      ],
      "minimum_should_match": 1
    }
  }
}
```

### 4.2 bool Query Execution Order

Understanding how `bool` executes helps optimize query performance:

1. **filter** and **must_not**: evaluated first in filter context (no scoring). Results cached as bitsets.
2. **must**: evaluated in query context on the filtered document set.
3. **should**: adds optional scoring boosts. With `minimum_should_match`, acts as a soft requirement.

Best practices:
- Move all non-scoring clauses into `filter`. A `must` with a `term` query calculates a useless score.
- Put the most selective filter first. Elasticsearch evaluates filters left to right within the `filter` array, and a selective first filter reduces the candidate set early.
- Use `must_not` for exclusion instead of inverting a filter with a script.

### 4.3 function_score

```http
POST /prodotti/_search
{
  "query": {
    "function_score": {
      "query": { "match": { "nome": "scarpe" } },
      "functions": [
        { "filter": { "term": { "in_offerta": true } }, "weight": 2.0 },
        {
          "field_value_factor": {
            "field": "recensioni_count", "factor": 0.1,
            "modifier": "sqrt", "missing": 1
          }
        },
        {
          "gauss": {
            "data_pubblicazione": {
              "origin": "now", "scale": "30d", "decay": 0.5
            }
          }
        }
      ],
      "score_mode": "sum",
      "boost_mode": "multiply"
    }
  }
}
```

### 4.4 function_score Parameters Reference

| Parameter | Options | Description |
|-----------|---------|-------------|
| `score_mode` | `multiply`, `sum`, `avg`, `first`, `max`, `min` | How function scores are combined with each other |
| `boost_mode` | `multiply`, `replace`, `sum`, `avg`, `max`, `min` | How the combined function score is combined with the query score |
| `max_boost` | float | Upper limit for the function score |
| `min_score` | float | Exclude documents below this total score |

Decay functions (`gauss`, `linear`, `exp`) accept:
- `origin`: the point of maximum score
- `scale`: the distance from origin where the score decays to `decay`
- `offset`: no decay within this distance from origin
- `decay`: the score value at `scale` distance (default 0.5)

```http
// Decay function with offset
{
  "gauss": {
    "location": {
      "origin": { "lat": 45.46, "lon": 9.19 },
      "offset": "2km",
      "scale": "10km",
      "decay": 0.33
    }
  }
}
```

### 4.5 Nested Query

```http
// Per campi nested: mantiene la correlazione tra campi dell'oggetto annidato
POST /ordini/_search
{
  "query": {
    "nested": {
      "path": "prodotti",
      "query": {
        "bool": {
          "must": [
            { "match": { "prodotti.nome": "scarpe rosse" } },
            { "range": { "prodotti.prezzo": { "lt": 50 } } }
          ]
        }
      },
      "score_mode": "max"
    }
  }
}
```

### 4.6 dis_max Query

`dis_max` returns documents that match any of its sub-queries, using the highest score from any matching sub-query (plus a `tie_breaker` fraction of other matching queries):

```http
{
  "query": {
    "dis_max": {
      "queries": [
        { "match": { "title": "elasticsearch" } },
        { "match": { "body": "elasticsearch" } }
      ],
      "tie_breaker": 0.7
    }
  }
}
```

This is what `multi_match` with `type: best_fields` uses internally.

### 4.7 boosting Query

Demotes documents matching a negative query without excluding them:

```http
{
  "query": {
    "boosting": {
      "positive": { "match": { "content": "elasticsearch" } },
      "negative": { "term":  { "category": "deprecated" } },
      "negative_boost": 0.2
    }
  }
}
```

### 4.8 constant_score Query

Wraps a filter and assigns a fixed score to all matching documents:

```http
{
  "query": {
    "constant_score": {
      "filter": { "term": { "status": "active" } },
      "boost": 1.2
    }
  }
}
```

---

## 5. Paginazione Efficiente

### 5.1 from/size vs search_after vs PIT

`from + size` è semplice ma costoso per pagine profonde: recupera `from + size` documenti da ogni shard. Limite: `max_result_window = 10000`.

```http
// Paginazione base — OK solo per prime N pagine
POST /documenti/_search
{
  "from": 0, "size": 20,
  "sort": [{ "data": "desc" }, { "_score": "desc" }],
  "query": { "match": { "titolo": "elasticsearch" } }
}
```

`search_after` è la soluzione per paginazione profonda. Niente offset: si passa il sort value dell'ultimo documento ricevuto.

```http
// Prima pagina
POST /log/_search
{
  "size": 100,
  "sort": [{ "timestamp": "desc" }, { "_id": "asc" }],
  "query": { "range": { "timestamp": { "gte": "now-1d" } } }
}

// Pagina successiva con search_after
POST /log/_search
{
  "size": 100,
  "sort": [{ "timestamp": "desc" }, { "_id": "asc" }],
  "search_after": ["2026-05-06T14:23:45.000Z", "abc123"],
  "query": { "range": { "timestamp": { "gte": "now-1d" } } }
}
```

Point-in-Time (PIT) garantisce paginazione consistente su dati che cambiano:

```http
// Apri PIT
POST /log/_pit?keep_alive=1m
// → { "id": "46ToAwMDaWR..." }

// Pagina con PIT (i dati non cambiano tra pagine)
POST /_search
{
  "size": 100,
  "pit": { "id": "46ToAwMDaWR...", "keep_alive": "1m" },
  "sort": [{ "@timestamp": "desc" }],
  "search_after": [1716998625000],
  "query": { "match_all": {} }
}

// Chiudi PIT
DELETE /_pit
{ "id": "46ToAwMDaWR..." }
```

### 5.2 Pagination Strategy Decision Matrix

| Method | Max Documents | Consistency | Cost | Use Case |
|--------|--------------|-------------|------|----------|
| `from/size` | 10,000 (configurable) | None (real-time) | O(from+size) per shard | UI pagination (first few pages) |
| `search_after` | Unlimited | None (real-time) | O(size) per shard | Deep pagination, infinite scroll |
| `search_after + PIT` | Unlimited | Snapshot | O(size) per shard + PIT memory | Export, batch processing |
| `scroll` (deprecated for search) | Unlimited | Snapshot | Holds search context in memory | Legacy bulk export only |

### 5.3 Scroll API (Legacy)

The scroll API is still available but deprecated for search use cases. Use `search_after` + PIT instead. The scroll API is retained for compatibility with bulk processing tools:

```http
// Open scroll
POST /logs-*/_search?scroll=5m
{
  "size": 1000,
  "query": { "match_all": {} }
}

// Subsequent pages
POST /_search/scroll
{
  "scroll": "5m",
  "scroll_id": "DXF1ZXJ5QW5kRmV0..."
}

// ALWAYS close the scroll when done (frees memory on all nodes)
DELETE /_search/scroll
{ "scroll_id": "DXF1ZXJ5QW5kRmV0..." }

// Clear all scrolls (emergency cleanup)
DELETE /_search/scroll/_all
```

---

## 6. Specialized Queries

### 6.1 Geo Queries

```http
// Geo bounding box: documents within a rectangular area
{
  "query": {
    "geo_bounding_box": {
      "location": {
        "top_left":     { "lat": 45.50, "lon": 9.10 },
        "bottom_right": { "lat": 45.40, "lon": 9.30 }
      }
    }
  }
}

// Geo distance: documents within a radius
{
  "query": {
    "geo_distance": {
      "distance": "10km",
      "location": { "lat": 45.46, "lon": 9.19 }
    }
  },
  "sort": [
    {
      "_geo_distance": {
        "location": { "lat": 45.46, "lon": 9.19 },
        "order": "asc",
        "unit": "km"
      }
    }
  ]
}

// Geo polygon: documents within an arbitrary polygon
{
  "query": {
    "geo_shape": {
      "area": {
        "shape": {
          "type": "polygon",
          "coordinates": [
            [[9.1, 45.5], [9.3, 45.5], [9.3, 45.4], [9.1, 45.4], [9.1, 45.5]]
          ]
        },
        "relation": "WITHIN"
      }
    }
  }
}
```

### 6.2 kNN (Approximate Nearest Neighbor) Search

ES 8.x supports vector search via HNSW (Hierarchical Navigable Small World) algorithm:

```http
// kNN search with pre-filter
POST /knowledge-base/_search
{
  "knn": {
    "field": "embedding",
    "query_vector": [0.1, -0.2, 0.3, ...],
    "k": 10,
    "num_candidates": 100,
    "filter": {
      "term": { "category": "technical" }
    }
  },
  "_source": ["title", "content"]
}

// Hybrid search: combine kNN with BM25 using RRF (ES 8.9+)
POST /knowledge-base/_search
{
  "query": {
    "match": { "content": "distributed consensus algorithms" }
  },
  "knn": {
    "field": "embedding",
    "query_vector": [0.1, -0.2, 0.3, ...],
    "k": 10,
    "num_candidates": 100
  },
  "rank": {
    "rrf": {
      "window_size": 100,
      "rank_constant": 60
    }
  }
}
```

### 6.3 Percolate Query (Reverse Search)

A percolate query matches documents against stored queries (the reverse of normal search):

```http
// Step 1: Create an index with a percolator field
PUT /alerts
{
  "mappings": {
    "properties": {
      "query":    { "type": "percolator" },
      "message":  { "type": "text" },
      "severity": { "type": "keyword" }
    }
  }
}

// Step 2: Store queries (alert rules)
PUT /alerts/_doc/rule-1
{
  "query": {
    "bool": {
      "must": [
        { "match": { "message": "OutOfMemoryError" } },
        { "term":  { "severity": "critical" } }
      ]
    }
  }
}

// Step 3: Check which stored queries match a new document
POST /alerts/_search
{
  "query": {
    "percolate": {
      "field": "query",
      "document": {
        "message": "Java OutOfMemoryError: Heap space at com.example.Service",
        "severity": "critical"
      }
    }
  }
}
```

### 6.4 more_like_this Query

Finds documents similar to a given document or text:

```http
{
  "query": {
    "more_like_this": {
      "fields": ["title", "content"],
      "like": [
        { "_index": "articles", "_id": "art-123" },
        "Elasticsearch is a distributed search engine"
      ],
      "min_term_freq": 1,
      "max_query_terms": 25,
      "min_doc_freq": 2,
      "minimum_should_match": "30%"
    }
  }
}
```

---

## 7. Sorting and Source Filtering

### 7.1 Sort Options

```http
POST /products/_search
{
  "sort": [
    { "price": { "order": "asc", "missing": "_last" } },
    { "rating": { "order": "desc", "mode": "avg" } },
    {
      "_geo_distance": {
        "location": { "lat": 45.46, "lon": 9.19 },
        "order": "asc",
        "unit": "km",
        "mode": "min"
      }
    },
    {
      "_script": {
        "type": "number",
        "script": {
          "source": "doc['price'].value * (1 - doc['discount_pct'].value / 100.0)"
        },
        "order": "asc"
      }
    },
    "_score"
  ]
}
```

### 7.2 Source Filtering

Reduce response payload by selecting only needed fields:

```http
POST /articles/_search
{
  "_source": {
    "includes": ["title", "author", "published_at"],
    "excludes": ["content", "embedding"]
  },
  "query": { "match_all": {} }
}

// Disable _source entirely (only return _id and _score)
POST /articles/_search
{
  "_source": false,
  "fields": ["title", "author"],
  "query": { "match_all": {} }
}

// Use the fields parameter (ES 7.x+) for formatted/runtime field values
POST /articles/_search
{
  "fields": [
    "title",
    { "field": "date", "format": "yyyy-MM-dd" }
  ],
  "_source": false,
  "query": { "match_all": {} }
}
```

---

## 8. Highlighting

Highlighting returns text fragments with matching terms wrapped in HTML tags:

```http
POST /articles/_search
{
  "query": { "match": { "content": "elasticsearch performance tuning" } },
  "highlight": {
    "pre_tags": ["<mark>"],
    "post_tags": ["</mark>"],
    "fields": {
      "content": {
        "type": "unified",
        "fragment_size": 150,
        "number_of_fragments": 3,
        "no_match_size": 150
      },
      "title": {
        "type": "unified",
        "number_of_fragments": 0
      }
    }
  }
}
```

Highlighter types:
- **unified** (default, recommended): works with all query types, supports `index_options: offsets` for fast highlighting.
- **plain**: simple, slow for large fields. Uses re-analysis of the stored text.
- **fvh** (fast vector highlighter): requires `term_vector: with_positions_offsets`. Fast for large fields but uses more disk space.

---

## 9. Suggesters

### 9.1 Term and Phrase Suggesters (Did-you-mean)

```http
POST /articles/_search
{
  "suggest": {
    "spell-check": {
      "text": "elasticsearh distrbuted",
      "term": {
        "field": "content",
        "suggest_mode": "popular",
        "min_word_length": 4,
        "max_edits": 2
      }
    },
    "phrase-suggest": {
      "text": "elasticsearh distrbuted system",
      "phrase": {
        "field": "content",
        "gram_size": 3,
        "confidence": 1.0,
        "max_errors": 2.0,
        "highlight": {
          "pre_tag": "<em>",
          "post_tag": "</em>"
        }
      }
    }
  }
}
```

### 9.2 Completion Suggester (Autocomplete)

The completion suggester uses an in-memory FST data structure for extremely fast prefix completions:

```http
// Mapping
PUT /products
{
  "mappings": {
    "properties": {
      "suggest": {
        "type": "completion",
        "contexts": [
          { "name": "category", "type": "category" }
        ]
      }
    }
  }
}

// Index with completion field
PUT /products/_doc/1
{
  "suggest": {
    "input": ["Scarpe Running Nike Air Max", "Nike Air Max", "Air Max"],
    "weight": 42,
    "contexts": { "category": "running" }
  }
}

// Query
POST /products/_search
{
  "suggest": {
    "product-suggest": {
      "prefix": "nik",
      "completion": {
        "field": "suggest",
        "size": 5,
        "fuzzy": { "fuzziness": 1 },
        "contexts": {
          "category": [{ "context": "running", "boost": 2 }]
        }
      }
    }
  }
}
```

---

## 10. Rescoring

Rescoring applies a more expensive query to only the top-N results from the initial query, improving relevance without the cost of running the expensive query on all documents:

```http
POST /articles/_search
{
  "query": {
    "match": { "content": "elasticsearch performance" }
  },
  "rescore": {
    "window_size": 100,
    "query": {
      "rescore_query": {
        "match_phrase": {
          "content": {
            "query": "elasticsearch performance",
            "slop": 2
          }
        }
      },
      "query_weight": 0.7,
      "rescore_query_weight": 1.2,
      "score_mode": "total"
    }
  }
}
```

---

## 11. ES|QL (ES 8.11+)

ES|QL is a pipe-based query language that provides an alternative to Query DSL for data exploration:

```http
POST /_query
{
  "query": """
    FROM logs-*
    | WHERE level == "ERROR" AND @timestamp > NOW() - 24 HOURS
    | STATS error_count = COUNT(*), services = COUNT_DISTINCT(service) BY error.type
    | SORT error_count DESC
    | LIMIT 20
  """
}

// ES|QL with filtering and aggregation
POST /_query
{
  "query": """
    FROM metrics-*
    | WHERE service == "order-api" AND @timestamp > NOW() - 1 HOUR
    | EVAL latency_seconds = latency_ms / 1000.0
    | STATS p50 = PERCENTILE(latency_seconds, 50),
            p99 = PERCENTILE(latency_seconds, 99),
            total = COUNT(*)
      BY endpoint
    | WHERE total > 100
    | SORT p99 DESC
  """
}
```

ES|QL supports: `FROM`, `WHERE`, `EVAL`, `STATS`, `SORT`, `LIMIT`, `KEEP`, `DROP`, `RENAME`, `DISSECT`, `GROK`, `ENRICH`, `MV_EXPAND`.

---

## 12. Troubleshooting

### 12.1 Query returns zero results when matches are expected

- Check that the analyzer used at search time matches the analyzer used at index time. Run `POST /_analyze` with the same analyzer and text to see the generated tokens.
- For term-level queries (`term`, `terms`), verify the field is of type `keyword` or that you are querying the `.keyword` sub-field. `term` queries do not analyze the input.
- Check `dynamic` mapping: if set to `false`, new fields are stored but not indexed (not searchable).

### 12.2 Unexpected scoring or ranking

```http
// Use explain to understand why a document got its score
POST /my-index/_search
{
  "explain": true,
  "query": { "match": { "content": "elasticsearch" } }
}

// Or explain a specific document
GET /my-index/_explain/doc-123
{
  "query": { "match": { "content": "elasticsearch" } }
}
```

### 12.3 "Data too large" on aggregations

The `search.max_buckets` setting (default 65535) limits the number of buckets returned. For high-cardinality terms aggregations, use `composite` aggregation with pagination instead of increasing this limit.

### 12.4 query_string throws parsing exceptions

`query_string` uses Lucene syntax and will throw exceptions on unbalanced quotes, unrecognized operators, or invalid field names. For user-facing search bars, always use `simple_query_string` which silently ignores syntax errors.

### 12.5 Slow queries with leading wildcard

Leading wildcards (`*pattern`) bypass the term index and scan all terms in the segment. Solutions:
- Use `reverse` token filter to enable suffix search as prefix search on the reversed tokens.
- Use `ngram` tokenizer to pre-compute substrings at index time.
- Use `wildcard` field type (ES 7.9+) which uses an n-gram index optimized for wildcard and regexp queries.

### 12.6 Nested query returns parent documents unexpectedly

Nested queries return the **parent** document, not the nested objects themselves. To get the matching nested objects, use `inner_hits`:

```http
{
  "query": {
    "nested": {
      "path": "items",
      "query": { "term": { "items.color": "red" } },
      "inner_hits": {
        "size": 3,
        "_source": ["items.name", "items.color"]
      }
    }
  }
}
```

### 12.7 PIT expires during pagination

If a PIT expires mid-pagination (`search_context_missing_exception`), you must open a new PIT and restart from the beginning. Set `keep_alive` long enough for the full pagination cycle, and extend it on each search request.

### 12.8 match_phrase returns no results for long phrases

Long phrases may not have all terms in the exact order within the analyzer's token stream. Increase `slop` to allow term reordering, or switch to `match` with `operator: and` if exact phrase order is not required.

### 12.9 fuzziness produces too many irrelevant results

`fuzziness: AUTO` maps to edit distance 0 for 1-2 char terms, 1 for 3-5 char terms, and 2 for 6+ char terms. For better control, set `fuzziness` to a fixed value (0, 1, or 2) and use `prefix_length: 2` to require the first 2 characters to match exactly.

### 12.10 Timeout on aggregation queries

Use the `timeout` parameter to set a hard limit on query execution:

```http
POST /large-index/_search?timeout=10s
{
  "size": 0,
  "aggs": { "big_agg": { "terms": { "field": "category", "size": 10000 } } }
}
// If the timeout is reached, partial results are returned with "timed_out": true
```

---

## 13. FAQ

### Q1: Should I use query_string or simple_query_string for a search bar?

Use `simple_query_string` for user-facing search. It handles malformed input gracefully (no exceptions), supports common operators (+, -, |, "", ~N, *), and is safe against injection. Use `query_string` only for internal/admin tools where the operator knows Lucene syntax.

### Q2: How does minimum_should_match work?

In a `bool` query with no `must` clauses, at least one `should` clause must match by default. `minimum_should_match` overrides this. It accepts absolute numbers (2), percentages (75%), negative numbers (-2 = all except 2), or combinations (3<90% = if 3 or more clauses, require 90%). When a `must` clause exists, `should` clauses are purely optional scoring boosters unless `minimum_should_match` is set.

### Q3: What is the difference between term and match queries?

`term` does not analyze the input: it searches the inverted index for the exact value you provide. `match` analyzes the input with the field's search analyzer before searching. For `text` fields, always use `match`. For `keyword` fields, use `term`.

### Q4: How do I search across multiple indices?

Specify a comma-separated list or a wildcard pattern in the URL:

```http
POST /logs-2026.05.*,metrics-*/_search
{ "query": { "match_all": {} } }
```

### Q5: What is the maximum number of results I can retrieve?

`from + size` is limited to `index.max_result_window` (default 10,000). For deeper pagination, use `search_after` with a PIT. For bulk export of all documents, use `search_after` with `match_all` and a PIT.

### Q6: How can I boost recent documents in search results?

Use a `gauss` decay function in `function_score` on the date field, or a `field_value_factor` on a recency score computed at index time. A decay function is more flexible because it does not require reindexing.

### Q7: Can I do JOINs in Elasticsearch?

Not in the SQL sense. Options for related data: (1) denormalize at index time (fastest queries, requires reindex on updates), (2) nested objects (correlated fields within a document, stored in the same Lucene block), (3) parent-child (has_child/has_parent queries, slower but allows independent updates), (4) application-side join (two queries, combine in code).

### Q8: How do I debug a slow query?

Enable the profile API (`"profile": true`), check slow logs, and use `_explain` on specific documents. Common causes: leading wildcards, high-cardinality terms aggregations, deep pagination with `from`, scripts in sort or scoring, and missing filter context (scoring where only filtering is needed).

### Q9: What is the difference between match_phrase and match with operator:and?

`match` with `operator: and` requires all terms to be present but in any order. `match_phrase` requires all terms in the exact order (with optional `slop` for flexibility). `match_phrase` is stricter and produces fewer but more precise results.

### Q10: Can I use SQL with Elasticsearch?

Yes. Elasticsearch supports SQL via the `_sql` endpoint (X-Pack feature):

```http
POST /_sql?format=txt
{
  "query": "SELECT service, COUNT(*) as cnt FROM \"logs-*\" WHERE level='ERROR' GROUP BY service ORDER BY cnt DESC LIMIT 10"
}
```

For more complex analytics, ES|QL (ES 8.11+) provides a pipe-based language with richer statistical functions.

### Q11: How do I handle multilingual search?

Use multi-fields with language-specific analyzers on the same field:

```json
"title": {
  "type": "text",
  "analyzer": "italian",
  "fields": {
    "english": { "type": "text", "analyzer": "english" },
    "german":  { "type": "text", "analyzer": "german" }
  }
}
```

Then use `multi_match` across `title`, `title.english`, and `title.german` with `type: most_fields`.

### Q12: What happens if I query a field that does not exist in the mapping?

For `term` and `match` queries, the query returns zero results without error. For `strict` dynamic mapping, the query fails if you try to search a field not in the mapping. This is why explicit mappings with `dynamic: strict` are recommended for production.

---

*Questo documento fa parte del modulo 08 "Elasticsearch" della Data Encyclopedia.*
