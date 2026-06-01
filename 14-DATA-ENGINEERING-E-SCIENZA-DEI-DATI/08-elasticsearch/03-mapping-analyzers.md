# Mapping e Analyzers in Elasticsearch

> Autori: Team Data Encyclopedia  
> Ultimo aggiornamento: 2026-05-22  
> Versione: 2.0.0  
> Stato: expanded

## Indice
1. Mapping: Schema dei Dati
2. Tipi di Campo
3. Analyzers e Pipeline di Analisi
4. Analyzers Custom
5. Index Templates e Component Templates
6. Runtime Fields (ES 7.11+)
7. Mapping Migration Strategies
8. Normalizers for Keyword Fields
9. Mapping Monitoring and Diagnostics
10. Troubleshooting
11. FAQ

---

## 1. Mapping: Schema dei Dati

### 1.1 Dynamic vs Explicit Mapping

Il **dynamic mapping** permette a Elasticsearch di inferire automaticamente il tipo dei campi da ogni documento indicizzato. Un campo con valore stringa che assomiglia a una data diventa `date`; un numero intero diventa `long`; un testo generico diventa `text` con un `keyword` sub-field. Questo è comodo per la prototipazione ma pericoloso in produzione: Elasticsearch può inferire il tipo sbagliato (es. uno ZIP code "01234" diventa `long` perdendo il leading zero), e l'accumulo di campi non previsti può portare al "mapping explosion" (troppi campi causano overhead di memoria).

In produzione si usa **explicit mapping** con `dynamic: "strict"` per rifiutare documenti con campi sconosciuti, oppure `dynamic: false` per ignorarli (indicizzati ma non cercabili).

```http
PUT /articoli
{
  "settings": { "number_of_shards": 3 },
  "mappings": {
    "dynamic": "strict",
    "properties": {
      "titolo":    { "type": "text", "analyzer": "italian",
                     "fields": { "keyword": { "type": "keyword" } } },
      "autore":    { "type": "keyword" },
      "data":      { "type": "date", "format": "yyyy-MM-dd||epoch_millis" },
      "contenuto": { "type": "text", "analyzer": "italian",
                     "index_options": "offsets" },
      "tag":       { "type": "keyword" },
      "metadati":  { "type": "object", "dynamic": true }
    }
  }
}
```

### 1.2 Dynamic Mapping Behavior Reference

| `dynamic` Value | Unknown Field Behavior | Searchable | Stored in `_source` |
|-----------------|----------------------|------------|-------------------|
| `true` (default) | Automatically mapped and indexed | Yes | Yes |
| `false` | Not mapped, not indexed | No | Yes |
| `strict` | Rejects the document with an error | N/A | N/A |
| `runtime` (ES 7.11+) | Added as a runtime field | Yes (computed at query time) | Yes |

### 1.3 Dynamic Templates

Dynamic templates control how Elasticsearch maps fields that match a pattern, even when using dynamic mapping:

```http
PUT /events
{
  "mappings": {
    "dynamic_templates": [
      {
        "strings_as_keywords": {
          "match_mapping_type": "string",
          "match": "*_id",
          "mapping": { "type": "keyword" }
        }
      },
      {
        "long_strings_as_text": {
          "match_mapping_type": "string",
          "match": "*_content",
          "mapping": {
            "type": "text",
            "analyzer": "italian",
            "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } }
          }
        }
      },
      {
        "unmatched_strings_as_keyword": {
          "match_mapping_type": "string",
          "mapping": { "type": "keyword" }
        }
      },
      {
        "dates_with_format": {
          "match": "*_at",
          "mapping": {
            "type": "date",
            "format": "strict_date_optional_time||epoch_millis"
          }
        }
      },
      {
        "disable_norms_on_keywords": {
          "match_mapping_type": "string",
          "match": "tag_*",
          "mapping": {
            "type": "keyword",
            "norms": false,
            "doc_values": true
          }
        }
      }
    ],
    "properties": {
      "@timestamp": { "type": "date" }
    }
  }
}
```

Dynamic templates are evaluated in order; the first matching template wins. This makes the ordering critical.

### 1.4 Mapping Limits

Protect the cluster from mapping explosion with these settings:

```http
PUT /my-index/_settings
{
  "index.mapping.total_fields.limit": 1000,
  "index.mapping.depth.limit": 20,
  "index.mapping.nested_fields.limit": 50,
  "index.mapping.nested_objects.limit": 10000,
  "index.mapping.field_name_length.limit": 300,
  "index.mapping.dimension_fields.limit": 16
}
```

---

## 2. Tipi di Campo

### 2.1 Tipi Testuali

`text` è per il full-text search: il valore viene analizzato (tokenizzato, normalizzato) prima dell'indicizzazione. Non può essere usato per sorting, aggregazioni esatte, o term queries — per questi usi si aggiunge un sub-field `keyword`. `keyword` non viene analizzato: il valore viene indicizzato as-is. Ideale per identificatori, categorie, stati, tag.

```http
// Multi-field: titolo cercabile full-text E aggregabile come keyword
"titolo": {
  "type": "text",
  "analyzer": "italian",
  "fields": {
    "keyword": { "type": "keyword", "ignore_above": 256 },
    "english": { "type": "text", "analyzer": "english" }
  }
}
```

### 2.2 Wildcard Field Type (ES 7.9+)

The `wildcard` type is optimized for grep-like wildcard and regexp queries on keyword-like data. It uses an n-gram sub-index to speed up pattern matching:

```http
"log_message": {
  "type": "wildcard"
}

// Queries like these are fast on wildcard fields:
{ "query": { "wildcard": { "log_message": "*NullPointerException*" } } }
{ "query": { "regexp": { "log_message": ".*ERROR.*timeout.*" } } }
```

Use `wildcard` type when you need frequent leading wildcard or regexp searches. For simple prefix queries, `keyword` with `prefix` query is sufficient and more storage-efficient.

### 2.3 search_as_you_type Field Type

Purpose-built for autocomplete. Internally creates sub-fields with edge_ngram and shingle analyzers:

```http
"product_name": {
  "type": "search_as_you_type",
  "max_shingle_size": 3
}

// This creates internal sub-fields:
// product_name           (standard analyzed)
// product_name._2gram    (shingles of 2)
// product_name._3gram    (shingles of 3)
// product_name._index_prefix (edge_ngram of each term)

// Search query:
{
  "query": {
    "multi_match": {
      "query": "elast",
      "type": "bool_prefix",
      "fields": [
        "product_name",
        "product_name._2gram",
        "product_name._3gram"
      ]
    }
  }
}
```

### 2.4 Tipi Numerici e Speciali

```http
"properties": {
  "prezzo":       { "type": "scaled_float", "scaling_factor": 100 },  // 19.99 → 1999
  "quantita":     { "type": "integer" },
  "id_prodotto":  { "type": "long" },
  "attivo":       { "type": "boolean" },
  "coordinate":   { "type": "geo_point" },
  "area":         { "type": "geo_shape" },
  "vettore":      { "type": "dense_vector", "dims": 384,
                    "index": true, "similarity": "cosine" },  // kNN search
  "attributi":    { "type": "flattened" },   // JSON arbitrario come keyword nested
  "embedding":    { "type": "dense_vector", "dims": 1536 }
}
```

### 2.5 Numeric Type Selection Guide

| Type | Range | Bytes | Use When |
|------|-------|-------|----------|
| `byte` | -128 to 127 | 1 | Age, small counts |
| `short` | -32768 to 32767 | 2 | HTTP status codes, small enums |
| `integer` | -2^31 to 2^31-1 | 4 | Counts, IDs (if numeric) |
| `long` | -2^63 to 2^63-1 | 8 | Timestamps (epoch_millis), large IDs |
| `float` | IEEE 754 single precision | 4 | Approximate decimals where precision is not critical |
| `double` | IEEE 754 double precision | 8 | High-precision decimals |
| `half_float` | IEEE 754 half precision | 2 | ML features, normalized scores |
| `scaled_float` | long internally | 8 | Currency (scaling_factor: 100 stores cents) |
| `unsigned_long` | 0 to 2^64-1 | 8 | Very large positive IDs, hashes |

**Performance note**: for range queries on integers, Elasticsearch uses BKD trees (not the inverted index). For exact-value lookups on low-cardinality numeric fields (e.g., status codes), `keyword` can be faster than `short` because it uses the inverted index.

### 2.6 Nested vs Object vs Flattened

Understanding the differences between these structured types is critical:

```http
// OBJECT: fields are flattened. Cross-field correlation is LOST.
// { "items": [{"color":"red","size":"L"}, {"color":"blue","size":"S"}] }
// becomes: items.color: ["red","blue"], items.size: ["L","S"]
// A query for color=red AND size=S matches — WRONG (cross-object match)

// NESTED: each object is indexed as a separate hidden Lucene document.
// Cross-field correlation is PRESERVED. Requires nested query.
"items": {
  "type": "nested",
  "properties": {
    "color": { "type": "keyword" },
    "size":  { "type": "keyword" }
  }
}

// FLATTENED: entire JSON subtree is stored as keyword key-value pairs.
// No per-field analysis, no numeric range queries.
// Good for arbitrary metadata where field names are unpredictable.
"metadata": {
  "type": "flattened"
}
```

### 2.7 Mapping Parameters Importanti

```http
"campo": {
  "type": "text",
  "index": false,          // indicizza ma non rende cercabile (solo store)
  "store": true,           // memorizza separatamente dal _source (per campi grandi)
  "doc_values": false,     // disabilita doc values (risparmio disco per campi non-aggregati)
  "norms": false,          // disabilita norms (risparmio memoria per short fields)
  "index_options": "docs", // docs|freqs|positions|offsets (meno info = meno storage)
  "eager_global_ordinals": true  // pre-calcola ordinali per aggregazioni su keyword ad alta frequenza
}
```

### 2.8 Mapping Parameter Decision Matrix

| Parameter | Default | Disable When | Disk Savings |
|-----------|---------|--------------|-------------|
| `doc_values` | true (numeric, keyword) | Field is never sorted or aggregated | 10-30% per field |
| `norms` | true (text) | Field is never used for scoring (e.g., filter-only) | ~1 byte per doc per field |
| `index` | true | Field is stored only for display, never searched | Significant |
| `store` | false | Enable when you need to retrieve a field without loading full `_source` | Adds storage |
| `index_options` | positions (text) | `docs`: only need boolean match. `freqs`: need TF but no phrase queries. `offsets`: need fast highlighting | Varies |
| `coerce` | true (numeric) | Set to false to reject malformed numbers (e.g., "5" string for integer field) | None |

---

## 3. Analyzers e Pipeline di Analisi

### 3.1 Componenti di un Analyzer

Un analyzer è composto da tre fasi in sequenza: **character filters** (pre-processano il testo grezzo: rimuovono HTML, sostituiscono pattern), **tokenizer** (divide il testo in token), **token filters** (trasformano i token: lowercase, stemming, sinonimi, stopwords, n-gram).

```http
// Visualizzare come un analyzer processa un testo
POST /_analyze
{
  "analyzer": "italian",
  "text": "Gli elefanti correvano velocemente nella savana africana"
}
// Output: ["elefant", "correv", "velocement", "savan", "afric"]
// Lo stemmer italiano riduce le parole alla radice

// Analyzer custom inline
POST /_analyze
{
  "tokenizer": "standard",
  "filter": ["lowercase", "stop", { "type": "stemmer", "language": "italian" }],
  "text": "Elasticsearch è un motore di ricerca distribuito"
}
```

### 3.2 Analyzers Built-in

Elasticsearch include analyzers predefiniti per le principali lingue, incluso l'italiano. Ogni language analyzer include un tokenizer standard, rimozione delle stopwords nella lingua target, e uno stemmer specifico.

```http
// Confronto: standard vs italian
POST /_analyze
{ "analyzer": "standard", "text": "correvano velocemente" }
// → ["correvano", "velocemente"]   (nessuna riduzione)

POST /_analyze
{ "analyzer": "italian", "text": "correvano velocemente" }
// → ["correv", "velocement"]   (stemmed)
```

### 3.3 Complete Analyzer Reference

| Analyzer | Tokenizer | Token Filters | Use Case |
|----------|-----------|---------------|----------|
| `standard` | `standard` | `lowercase` | General purpose, language-agnostic |
| `simple` | `lowercase` (tokenizer) | None | Split on non-letter chars, lowercase |
| `whitespace` | `whitespace` | None | Split on whitespace only, case-sensitive |
| `stop` | `lowercase` | `stop` (English) | Standard + English stopword removal |
| `keyword` | `keyword` | None | No-op: the entire input is one token |
| `pattern` | `pattern` (regex split) | `lowercase` | Custom delimiter splitting |
| `fingerprint` | `standard` | `lowercase`, `asciifolding`, `stop`, dedup, sort | Deduplication, normalization |
| `italian` | `standard` | `italian_elision`, `lowercase`, `italian_stop`, `italian_keywords`, `italian_stemmer` | Italian full-text search |
| `english` | `standard` | `english_possessive_stemmer`, `lowercase`, `english_stop`, `english_keywords`, `english_stemmer` | English full-text search |

### 3.4 Tokenizer Types

```http
// standard: splits on word boundaries (Unicode Text Segmentation)
POST /_analyze
{ "tokenizer": "standard", "text": "Hello-World test123 email@test.com" }
// → ["Hello", "World", "test123", "email", "test.com"]

// letter: splits on non-letter characters
POST /_analyze
{ "tokenizer": "letter", "text": "Hello-World test123" }
// → ["Hello", "World", "test"]

// whitespace: splits on whitespace only
POST /_analyze
{ "tokenizer": "whitespace", "text": "Hello-World test123" }
// → ["Hello-World", "test123"]

// UAX URL email: preserves URLs and email addresses as single tokens
POST /_analyze
{ "tokenizer": "uax_url_email", "text": "Visit https://elastic.co or email info@elastic.co" }
// → ["Visit", "https://elastic.co", "or", "email", "info@elastic.co"]

// path_hierarchy: generates tokens for each path component
POST /_analyze
{ "tokenizer": "path_hierarchy", "text": "/var/log/elasticsearch/cluster.log" }
// → ["/var", "/var/log", "/var/log/elasticsearch", "/var/log/elasticsearch/cluster.log"]

// pattern: splits on regex
POST /_analyze
{
  "tokenizer": { "type": "pattern", "pattern": "[,;|]" },
  "text": "red,green;blue|yellow"
}
// → ["red", "green", "blue", "yellow"]
```

### 3.5 Token Filter Types

```http
// Edge n-gram: generates prefixes of each token (for autocomplete)
POST /_analyze
{
  "tokenizer": "standard",
  "filter": [
    "lowercase",
    { "type": "edge_ngram", "min_gram": 2, "max_gram": 10 }
  ],
  "text": "elasticsearch"
}
// → ["el", "ela", "elas", "elast", "elasti", "elastic", "elastics", "elasticse", "elasticsea"]

// n-gram: generates all substrings of each token (for substring matching)
POST /_analyze
{
  "tokenizer": "standard",
  "filter": [
    "lowercase",
    { "type": "ngram", "min_gram": 3, "max_gram": 4 }
  ],
  "text": "search"
}
// → ["sea", "sear", "ear", "earc", "arc", "arch", "rch"]

// synonym: expand or replace terms
POST /_analyze
{
  "tokenizer": "standard",
  "filter": [
    "lowercase",
    {
      "type": "synonym",
      "synonyms": ["laptop, notebook, portatile", "tv => televisore"]
    }
  ],
  "text": "laptop screen"
}
// → ["laptop", "notebook", "portatile", "screen"]

// asciifolding: converts Unicode characters to ASCII equivalents
POST /_analyze
{
  "tokenizer": "standard",
  "filter": ["lowercase", "asciifolding"],
  "text": "Straße caffè résumé naïve"
}
// → ["strasse", "caffe", "resume", "naive"]
```

### 3.6 Character Filters

```http
// html_strip: removes HTML tags and decodes entities
POST /_analyze
{
  "char_filter": ["html_strip"],
  "tokenizer": "standard",
  "text": "<p>Search &amp; <strong>analytics</strong></p>"
}
// → ["Search", "analytics"]

// mapping: custom character replacement
POST /_analyze
{
  "char_filter": [
    {
      "type": "mapping",
      "mappings": [
        ":) => _happy_",
        ":( => _sad_",
        "<3 => _love_"
      ]
    }
  ],
  "tokenizer": "standard",
  "text": "I love ES :) <3"
}
// → ["I", "love", "ES", "_happy_", "_love_"]

// pattern_replace: regex-based replacement
POST /_analyze
{
  "char_filter": [
    {
      "type": "pattern_replace",
      "pattern": "(\\d{3})(\\d{3})(\\d{4})",
      "replacement": "$1-$2-$3"
    }
  ],
  "tokenizer": "keyword",
  "text": "5551234567"
}
// → ["555-123-4567"]
```

---

## 4. Analyzers Custom

### 4.1 Definizione nell'Index Settings

```http
PUT /catalogo_prodotti
{
  "settings": {
    "analysis": {
      "char_filter": {
        "html_strip": { "type": "html_strip" },
        "normalizza_apostrofo": {
          "type": "mapping",
          "mappings": ["' => '", "' => '", "` => '"]
        }
      },
      "tokenizer": {
        "italian_tokenizer": {
          "type": "standard",
          "max_token_length": 255
        }
      },
      "filter": {
        "italian_stop": {
          "type": "stop",
          "stopwords": "_italian_"
        },
        "italian_stemmer": {
          "type": "stemmer",
          "language": "light_italian"
        },
        "italian_elision": {
          "type": "elision",
          "articles_case": true,
          "articles": ["c", "l", "all", "dall", "dell", "nell", "sull",
                       "coll", "pell", "gl", "agl", "dagl", "degl",
                       "negl", "sugl", "un", "m", "t", "s", "v", "d"]
        },
        "autocomplete_filter": {
          "type": "edge_ngram",
          "min_gram": 2,
          "max_gram": 20
        },
        "sinonimi_prodotti": {
          "type": "synonym_graph",
          "synonyms": [
            "laptop, notebook, portatile",
            "smartphone, cellulare, telefono"
          ]
        }
      },
      "analyzer": {
        "italian_custom": {
          "type": "custom",
          "char_filter": ["html_strip", "normalizza_apostrofo"],
          "tokenizer": "italian_tokenizer",
          "filter": ["lowercase", "italian_elision", "italian_stop", "italian_stemmer"]
        },
        "autocomplete": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": ["lowercase", "autocomplete_filter"]
        },
        "autocomplete_search": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": ["lowercase"]
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "nome": {
        "type": "text",
        "analyzer": "italian_custom",
        "fields": {
          "autocomplete": {
            "type": "text",
            "analyzer": "autocomplete",
            "search_analyzer": "autocomplete_search"
          }
        }
      }
    }
  }
}
```

### 4.2 Synonym Files

For large synonym lists, use external files instead of inline arrays:

```http
PUT /my-index
{
  "settings": {
    "analysis": {
      "filter": {
        "synonym_filter": {
          "type": "synonym_graph",
          "synonyms_path": "analysis/synonyms.txt",
          "updateable": true,
          "lenient": true
        }
      },
      "analyzer": {
        "synonym_analyzer": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": ["lowercase", "synonym_filter"]
        }
      }
    }
  }
}
```

Synonym file format (`config/analysis/synonyms.txt`):

```
# Explicit mapping (one-way)
tv => television
usa => united states of america

# Equivalent synonyms (bidirectional)
laptop, notebook, portatile

# Single-word expansion
pc, personal computer, desktop computer
```

To update synonyms without reindexing (ES 7.3+ with `updateable: true`):

```http
// Reload search analyzers (updates synonym file in memory)
POST /my-index/_reload_search_analyzers
```

### 4.3 Index Time vs Search Time Analysis

A common pattern is to use different analyzers at index time and search time:

```http
"product_name": {
  "type": "text",
  "analyzer": "index_analyzer",          // used at index time
  "search_analyzer": "search_analyzer"   // used at search time
}
```

When to use asymmetric analysis:
- **Autocomplete**: index with `edge_ngram`, search with `standard` (avoid double n-gramming the query).
- **Synonyms**: apply at search time only (`synonym_graph` with `search_analyzer`) so you can add synonyms without reindexing. Apply at index time if synonym expansion must affect scoring.
- **Stemming**: heavier stemming at index time (catches more variants), lighter at search time (preserves precision).

---

## 5. Index Templates e Component Templates

### 5.1 Component Templates

```http
// Component template riusabile per campi comuni
PUT /_component_template/timestamp_fields
{
  "template": {
    "mappings": {
      "properties": {
        "@timestamp":   { "type": "date" },
        "created_at":   { "type": "date" },
        "updated_at":   { "type": "date" }
      }
    }
  }
}

PUT /_component_template/italian_text_settings
{
  "template": {
    "settings": {
      "analysis": {
        "analyzer": {
          "default": { "type": "italian" }
        }
      }
    }
  }
}
```

### 5.2 Index Template Composito

```http
// Index template che combina component templates
PUT /_index_template/log_template
{
  "index_patterns": ["log-*", "events-*"],
  "composed_of": ["timestamp_fields", "italian_text_settings"],
  "priority": 200,
  "template": {
    "settings": {
      "number_of_shards":   1,
      "number_of_replicas": 1,
      "index.refresh_interval": "5s",
      "index.lifecycle.name": "log_policy"
    },
    "mappings": {
      "dynamic": "false",
      "properties": {
        "level":   { "type": "keyword" },
        "service": { "type": "keyword" },
        "message": { "type": "text" },
        "host":    { "type": "keyword" }
      }
    },
    "aliases": {
      "logs-all": {}
    }
  }
}
```

### 5.3 Template Priority and Composition

When multiple templates match an index pattern, the one with the highest `priority` wins. Component templates are applied in the order listed in `composed_of`, with later templates overriding earlier ones. The index template's own `template` section overrides all component templates.

```http
// Low priority: base settings
PUT /_index_template/base_template
{
  "index_patterns": ["*"],
  "priority": 0,
  "template": {
    "settings": {
      "number_of_replicas": 1,
      "refresh_interval": "5s"
    }
  }
}

// Higher priority: overrides for logs
PUT /_index_template/logs_template
{
  "index_patterns": ["logs-*"],
  "priority": 100,
  "composed_of": ["timestamp_fields", "italian_text_settings"],
  "template": {
    "settings": {
      "number_of_replicas": 0,
      "refresh_interval": "30s"
    }
  }
}

// Check which template applies to a given index name
POST /_index_template/_simulate_index/logs-myapp-2026.05.22
```

### 5.4 Legacy vs Composable Templates

ES 7.8+ introduced **composable index templates** (the `_index_template` API) which replaced **legacy templates** (the `_template` API). Key differences:

| Feature | Legacy (`_template`) | Composable (`_index_template`) |
|---------|---------------------|-------------------------------|
| Component reuse | None | `composed_of` references |
| Priority resolution | `order` field | `priority` field |
| Overlap | Multiple templates can apply (merged) | Only highest-priority single template applies |
| Simulation | None | `_simulate` and `_simulate_index` APIs |
| Data streams | Not supported | Supported via `data_stream: {}` |

Migrate to composable templates. Legacy templates are deprecated.

---

## 6. Runtime Fields (ES 7.11+)

### 6.1 Schema-on-Read with Runtime Fields

Runtime fields are computed at query time, not at index time. They are defined in the mapping but do not consume disk space or indexing CPU. Use them for ad-hoc analysis, prototyping new fields, and extracting values from `_source` without reindexing:

```http
PUT /logs
{
  "mappings": {
    "runtime": {
      "day_of_week": {
        "type": "keyword",
        "script": {
          "source": "emit(doc['@timestamp'].value.dayOfWeekEnum.getDisplayName(TextStyle.FULL, Locale.ROOT))"
        }
      },
      "response_time_seconds": {
        "type": "double",
        "script": {
          "source": "emit(doc['response_time_ms'].value / 1000.0)"
        }
      },
      "full_url": {
        "type": "keyword",
        "script": {
          "source": """
            String host = doc['host.keyword'].value;
            String path = doc['path.keyword'].value;
            emit('https://' + host + path);
          """
        }
      }
    },
    "properties": {
      "@timestamp":      { "type": "date" },
      "response_time_ms": { "type": "integer" },
      "host":            { "type": "keyword" },
      "path":            { "type": "keyword" }
    }
  }
}
```

### 6.2 Runtime Fields in Search Requests

You can also define runtime fields per-query without adding them to the mapping:

```http
POST /logs/_search
{
  "runtime_mappings": {
    "is_slow": {
      "type": "boolean",
      "script": {
        "source": "emit(doc['response_time_ms'].value > 5000)"
      }
    }
  },
  "query": {
    "bool": {
      "filter": [
        { "term": { "is_slow": true } }
      ]
    }
  },
  "aggs": {
    "slow_by_service": {
      "terms": { "field": "service" }
    }
  }
}
```

### 6.3 When to Use Runtime Fields vs Indexed Fields

| Criteria | Runtime Field | Indexed Field |
|----------|--------------|---------------|
| Query frequency | Rare, ad-hoc | Frequent |
| Performance | Slower (computed per query) | Faster (pre-computed) |
| Disk usage | Zero | Proportional to data size |
| Reindex required | No | Yes (for new fields) |
| Aggregation performance | Acceptable for small cardinalities | Fast for all cardinalities |
| Ideal use | Prototyping, derived values, one-off analysis | Production search and aggregation |

When a runtime field proves valuable, promote it to an indexed field and reindex for better performance.

---

## 7. Mapping Migration Strategies

### 7.1 Adding New Fields

Adding new fields to an existing mapping is always safe and does not require reindexing:

```http
PUT /my-index/_mapping
{
  "properties": {
    "new_field": { "type": "keyword" },
    "nested_obj": {
      "properties": {
        "sub_field": { "type": "text" }
      }
    }
  }
}
```

### 7.2 Changing Field Types (Requires Reindex)

Once a field is mapped, its type cannot be changed. The only way is to reindex into a new index with the correct mapping:

```http
// Step 1: Create destination index with new mapping
PUT /my-index-v2
{
  "mappings": {
    "properties": {
      "price": { "type": "scaled_float", "scaling_factor": 100 }
    }
  }
}

// Step 2: Reindex
POST /_reindex
{
  "source": { "index": "my-index-v1" },
  "dest":   { "index": "my-index-v2" }
}

// Step 3: Switch alias
POST /_aliases
{
  "actions": [
    { "remove": { "index": "my-index-v1", "alias": "my-index" } },
    { "add":    { "index": "my-index-v2", "alias": "my-index" } }
  ]
}
```

### 7.3 Zero-Downtime Reindex Pattern

For production systems, use the alias pattern to switch atomically:

```http
// Application always reads/writes through the alias "products"
// Never reference concrete index names in application code

// Initial setup
PUT /products-v1
{ "mappings": { ... }, "aliases": { "products": { "is_write_index": true } } }

// Migration: create v2, reindex, switch alias atomically
PUT /products-v2
{ "mappings": { ... } }

POST /_reindex
{ "source": { "index": "products-v1" }, "dest": { "index": "products-v2" } }

// Atomic alias swap
POST /_aliases
{
  "actions": [
    { "remove": { "index": "products-v1", "alias": "products" } },
    { "add":    { "index": "products-v2", "alias": "products" } }
  ]
}

// After verification, delete old index
DELETE /products-v1
```

---

## 8. Normalizers for Keyword Fields

Normalizers apply analysis to keyword fields without tokenization. The entire value is treated as a single token but can be lowercased, accent-folded, etc.:

```http
PUT /users
{
  "settings": {
    "analysis": {
      "normalizer": {
        "lowercase_normalizer": {
          "type": "custom",
          "filter": ["lowercase", "asciifolding"]
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "email": {
        "type": "keyword",
        "normalizer": "lowercase_normalizer"
      },
      "username": {
        "type": "keyword",
        "normalizer": "lowercase_normalizer"
      }
    }
  }
}

// Now these are equivalent:
// term query for "Mario@Example.COM" matches "mario@example.com"
// Aggregations group "ADMIN", "Admin", "admin" together
```

---

## 9. Mapping Monitoring and Diagnostics

### 9.1 Viewing Current Mappings

```http
// View full mapping for an index
GET /my-index/_mapping

// View mapping for a specific field
GET /my-index/_mapping/field/title

// View which template was applied
GET /my-index/_settings?filter_path=*.settings.index.provided_name

// Count fields in an index mapping
GET /my-index/_mapping?filter_path=*.mappings.properties
// Count the keys in the response to know field count

// Check field capabilities across multiple indices
GET /logs-*/_field_caps?fields=message,level,service
```

### 9.2 Analyzing Field Usage

```http
// Field usage stats (ES 7.15+)
GET /my-index/_field_usage_stats

// Identify unused fields for cleanup
// Fields with zero searches or aggregations are candidates for
// disabling index/doc_values to save disk
```

---

## 10. Troubleshooting

### 10.1 "mapper_parsing_exception: failed to parse field"

The document value does not match the field's mapped type. For example, sending `"price": "not_a_number"` to an `integer` field. Solutions:
- Fix the source data.
- Use `coerce: true` (default) to auto-convert strings like "5" to integer 5.
- Use `ignore_malformed: true` to silently skip malformed values instead of rejecting the document.

```http
PUT /tolerant-index
{
  "mappings": {
    "properties": {
      "price": { "type": "float", "ignore_malformed": true }
    }
  }
}
```

### 10.2 "illegal_argument_exception: Limit of total fields exceeded"

Too many fields in the mapping. Increase the limit or restructure:

```http
PUT /my-index/_settings
{ "index.mapping.total_fields.limit": 2000 }
```

Better solution: use `flattened` type for arbitrary JSON or restructure the data to use nested arrays instead of dynamic field names.

### 10.3 Field mapped as wrong type

Common scenario: first document had `"status": 200` (mapped as `long`), but later documents send `"status": "OK"` (rejected). Solution: use explicit mapping from the start. If already in production, reindex.

### 10.4 Text field not aggregatable

`text` fields cannot be used for aggregations, sorting, or scripting by default. Use the `.keyword` sub-field instead. Never enable `fielddata` on text fields unless you understand the heap implications.

### 10.5 Analyzer produces unexpected tokens

Use the `_analyze` API to debug:

```http
// Test with the analyzer applied to a specific field
POST /my-index/_analyze
{
  "field": "title",
  "text": "Your test input here"
}

// Test with a custom analyzer definition
POST /_analyze
{
  "tokenizer": "standard",
  "filter": ["lowercase", { "type": "stemmer", "language": "italian" }],
  "text": "Your test input here"
}
```

### 10.6 Synonym expansion not working

- Ensure synonyms are applied in the correct analyzer (index-time or search-time).
- `synonym_graph` is recommended over `synonym` for multi-word synonyms.
- Synonym filters must come AFTER `lowercase` in the filter chain (synonyms are case-sensitive).
- Use `lenient: true` to skip malformed synonym rules instead of failing.

### 10.7 Multi-field mapping not reflecting in queries

Multi-fields (`.keyword`, `.english`, etc.) are only populated for documents indexed AFTER the multi-field was added. Previously indexed documents need to be reindexed via `_update_by_query`:

```http
POST /my-index/_update_by_query?conflicts=proceed
```

### 10.8 Nested fields causing high heap usage

Each nested object is stored as a separate Lucene document. An index with 10 million documents, each containing 50 nested objects, effectively has 500 million Lucene documents. Monitor with:

```http
GET /my-index/_stats?filter_path=_all.primaries.docs
// "docs.count" includes nested docs
// Compare with actual document count to see the nested inflation factor
```

### 10.9 Runtime field script errors

Runtime fields fail silently for documents where the script encounters an error. Enable debug logging or test the script on specific documents:

```http
POST /my-index/_search
{
  "runtime_mappings": {
    "test_field": {
      "type": "keyword",
      "script": "emit(doc['maybe_missing_field'].value)"
    }
  },
  "fields": ["test_field"],
  "size": 5
}
```

### 10.10 Index template not applying to new indices

Check template priority and pattern matching:

```http
// Simulate which template would apply
POST /_index_template/_simulate_index/my-new-index-name

// List all templates sorted by priority
GET /_index_template?filter_path=index_templates.name,index_templates.index_template.priority
```

---

## 11. FAQ

### Q1: Can I change an existing field's type without reindexing?

No. Once a field is mapped to a type, it cannot be changed. You must create a new index with the correct mapping and reindex. Use the alias swap pattern for zero-downtime migrations.

### Q2: What is the difference between object and nested types?

`object` flattens arrays of objects, losing cross-field correlation within each object. `nested` stores each object as a separate Lucene document, preserving correlation but requiring `nested` queries and costing more in storage and heap.

### Q3: Should I use dynamic mapping in production?

No. Use `dynamic: "strict"` to reject unknown fields, or `dynamic: false` to store them in `_source` without indexing. Dynamic mapping leads to mapping explosion and type conflicts.

### Q4: How do I handle fields that might have different types across indices?

Use `_field_caps` API to check field types across indices. If types conflict (e.g., `text` in one index and `keyword` in another), fix the mapping in one index and reindex. For cross-index searches, Elasticsearch handles type conflicts gracefully but with reduced functionality.

### Q5: When should I use scaled_float vs float for currency?

Always use `scaled_float` with `scaling_factor: 100` for currency. It stores the value as a long integer internally (avoiding floating-point precision issues) and is more space-efficient than `double`.

### Q6: How do synonyms interact with stemming?

Apply synonyms BEFORE stemming in the filter chain. If synonyms come after stemming, the stemmed form might not match the synonym list. For search-time synonyms with `synonym_graph`, the synonym expansion happens before the rest of the search analyzer's filters.

### Q7: What is the maximum number of fields per index?

The default limit is 1,000 fields (`index.mapping.total_fields.limit`). This can be increased but large mappings slow down cluster state updates and increase memory usage. If you need more than 1,000 fields, reconsider your data model (use `flattened` or structured nested arrays).

### Q8: How do I search for exact phrases in keyword fields?

`keyword` fields store the entire value as a single token. A `term` query matches the entire value exactly. For partial matching on keyword fields, use `wildcard` or `regexp` queries, or switch to a `text` field with `match_phrase`.

### Q9: What is the difference between analyzer and normalizer?

An analyzer tokenizes text into multiple tokens. A normalizer treats the entire input as a single token but can apply transformations (lowercase, asciifolding). Use analyzers for `text` fields, normalizers for `keyword` fields.

### Q10: How do I test an analyzer without creating an index?

Use the cluster-level `_analyze` API with an inline analyzer definition:

```http
POST /_analyze
{
  "tokenizer": "standard",
  "filter": ["lowercase", { "type": "stop", "stopwords": "_english_" }],
  "char_filter": ["html_strip"],
  "text": "<p>Testing the analyzer</p>"
}
```

### Q11: Can I add a search_analyzer to a field after creation?

Yes. Unlike changing the field type, adding or changing a `search_analyzer` is allowed on existing fields because it only affects query-time analysis, not the indexed data:

```http
PUT /my-index/_mapping
{
  "properties": {
    "content": {
      "type": "text",
      "analyzer": "standard",
      "search_analyzer": "english"
    }
  }
}
```

### Q12: How do I handle multilingual content in a single field?

Options: (1) multi-fields with language-specific analyzers, searched via `multi_match` with `type: most_fields`, (2) language detection at index time with routing to language-specific sub-fields, (3) ICU analysis plugin for Unicode-aware tokenization across scripts.

---

*Questo documento fa parte del modulo 08 "Elasticsearch" della Data Encyclopedia.*
