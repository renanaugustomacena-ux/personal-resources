# Aggregazioni in Elasticsearch

> Autori: Team Data Encyclopedia  
> Ultimo aggiornamento: 2026-05-22  
> Versione: 2.0.0  
> Stato: expanded

## Indice
1. Aggregazioni Metriche
2. Aggregazioni Bucket
3. Pipeline Aggregations
4. Aggregazioni Nidificate
5. Composite Aggregation per Scrolling
6. Aggregation Performance Optimization
7. Multi-Terms and Rare Terms
8. Significant Terms and Anomaly Detection
9. Matrix and Geo Aggregations
10. Troubleshooting
11. FAQ

---

## 1. Aggregazioni Metriche

### 1.1 Statistiche di Base

Le aggregazioni metriche calcolano un valore singolo (o un insieme di valori) da un set di documenti. Operano all'interno di un bucket o sull'intero risultato.

```http
POST /vendite/_search
{
  "size": 0,
  "aggs": {
    "fatturato_totale":    { "sum": { "field": "importo" } },
    "fatturato_medio":     { "avg": { "field": "importo" } },
    "ordine_massimo":      { "max": { "field": "importo" } },
    "ordine_minimo":       { "min": { "field": "importo" } },
    "stats_complete": {
      "extended_stats": {
        "field": "importo",
        "sigma": 2
      }
    },
    "clienti_unici": {
      "cardinality": {
        "field": "cliente_id",
        "precision_threshold": 10000
      }
    },
    "percentili_latenza": {
      "percentiles": {
        "field": "latenza_ms",
        "percents": [50, 75, 90, 95, 99, 99.9],
        "tdigest": { "compression": 200 }
      }
    },
    "top_5_ordini": {
      "top_hits": {
        "size": 5,
        "sort": [{ "importo": "desc" }],
        "_source": ["ordine_id", "importo", "data", "cliente"]
      }
    }
  }
}
```

### 1.2 Cardinality Accuracy and HyperLogLog++

The `cardinality` aggregation uses the HyperLogLog++ algorithm, which provides approximate distinct counts. The `precision_threshold` controls accuracy vs memory:

| `precision_threshold` | Memory per shard | Error rate |
|----------------------|-----------------|------------|
| 100 | ~1.6 KB | ~6% |
| 1,000 | ~16 KB | ~2% |
| 10,000 | ~160 KB | ~0.5% |
| 40,000 (max) | ~640 KB | ~0.25% |

Below the threshold, counts are exact. Above the threshold, the error rate applies. For exact counts on low-cardinality fields, the threshold equals the cardinality and results are precise.

```http
// High-precision cardinality (useful for billing/SLA reporting)
{
  "aggs": {
    "unique_users": {
      "cardinality": {
        "field": "user_id",
        "precision_threshold": 40000
      }
    }
  }
}
```

### 1.3 Percentile Ranks

The inverse of percentiles: given a value, what percentile does it fall in?

```http
{
  "aggs": {
    "latency_ranks": {
      "percentile_ranks": {
        "field": "response_time_ms",
        "values": [100, 200, 500, 1000, 5000],
        "keyed": true
      }
    }
  }
}
// Response: "100.0": 45.2, "200.0": 72.1, "500.0": 91.5, ...
// Meaning: 45.2% of requests complete in under 100ms
```

### 1.4 Weighted Average

Compute an average weighted by another field:

```http
{
  "aggs": {
    "weighted_rating": {
      "weighted_avg": {
        "value": { "field": "rating" },
        "weight": { "field": "review_count" }
      }
    }
  }
}
```

### 1.5 Median Absolute Deviation

A robust measure of variability (less sensitive to outliers than standard deviation):

```http
{
  "aggs": {
    "latency_variability": {
      "median_absolute_deviation": {
        "field": "response_time_ms",
        "compression": 1000
      }
    }
  }
}
```

### 1.6 Value Count and Missing Values

```http
{
  "aggs": {
    "total_records": { "value_count": { "field": "order_id" } },
    "missing_email": {
      "missing": { "field": "email" }
    }
  }
}
// missing: counts documents where the field does not exist
```

### 1.7 Scripted Metrics

For complex calculations that built-in metrics cannot express:

```http
{
  "aggs": {
    "profit_margin": {
      "scripted_metric": {
        "init_script": "state.revenues = []; state.costs = []",
        "map_script": """
          state.revenues.add(doc['revenue'].value);
          state.costs.add(doc['cost'].value);
        """,
        "combine_script": """
          double totalRevenue = 0;
          double totalCost = 0;
          for (r in state.revenues) { totalRevenue += r; }
          for (c in state.costs) { totalCost += c; }
          return ['revenue': totalRevenue, 'cost': totalCost];
        """,
        "reduce_script": """
          double totalRevenue = 0;
          double totalCost = 0;
          for (s in states) {
            totalRevenue += s.revenue;
            totalCost += s.cost;
          }
          return (totalRevenue - totalCost) / totalRevenue * 100;
        """
      }
    }
  }
}
```

---

## 2. Aggregazioni Bucket

### 2.1 terms, range, date_histogram

Le aggregazioni bucket partizionano i documenti in gruppi. A differenza delle metriche, producono più valori — uno per bucket.

```http
POST /log/_search
{
  "size": 0,
  "aggs": {
    "per_servizio": {
      "terms": {
        "field": "servizio",
        "size": 20,
        "order": { "_count": "desc" },
        "min_doc_count": 10
      },
      "aggs": {
        "per_livello": {
          "terms": { "field": "level", "size": 5 }
        },
        "errori_nel_tempo": {
          "date_histogram": {
            "field": "@timestamp",
            "calendar_interval": "1h",
            "min_doc_count": 0,
            "extended_bounds": {
              "min": "now-24h",
              "max": "now"
            }
          }
        }
      }
    },

    "fascia_latenza": {
      "range": {
        "field": "latenza_ms",
        "ranges": [
          { "to": 100 },
          { "from": 100, "to": 500 },
          { "from": 500, "to": 1000 },
          { "from": 1000 }
        ]
      }
    },

    "attivita_settimanale": {
      "date_histogram": {
        "field": "@timestamp",
        "fixed_interval": "7d",
        "format": "yyyy-MM-dd",
        "time_zone": "Europe/Rome"
      }
    }
  }
}
```

### 2.2 calendar_interval vs fixed_interval

Understanding the distinction prevents subtle time-bucketing bugs:

| Parameter | Behavior | Values | Example |
|-----------|----------|--------|---------|
| `calendar_interval` | Calendar-aware (varies by month length, DST) | `minute`, `hour`, `day`, `week`, `month`, `quarter`, `year` | "1M" = 28-31 days |
| `fixed_interval` | Exact duration | `Ns`, `Nm`, `Nh`, `Nd` | "30d" = exactly 30*24h |

Use `calendar_interval` for dashboards and human-readable time series. Use `fixed_interval` for SLA reporting where exact durations matter.

```http
// Calendar month buckets (January = 31 days, February = 28/29)
{ "date_histogram": { "field": "@timestamp", "calendar_interval": "1M" } }

// Fixed 30-day buckets (always exactly 2592000 seconds)
{ "date_histogram": { "field": "@timestamp", "fixed_interval": "30d" } }
```

### 2.3 Filter, Filters, Adjacency Matrix

```http
POST /prodotti/_search
{
  "size": 0,
  "aggs": {
    "solo_disponibili": {
      "filter": { "term": { "disponibile": true } },
      "aggs": {
        "prezzo_medio": { "avg": { "field": "prezzo" } }
      }
    },

    "per_fascia_prezzo": {
      "filters": {
        "filters": {
          "economici":   { "range": { "prezzo": { "lte": 50 } } },
          "medi":        { "range": { "prezzo": { "gt": 50, "lte": 200 } } },
          "premium":     { "range": { "prezzo": { "gt": 200 } } }
        }
      }
    },

    "overlap_categorie": {
      "adjacency_matrix": {
        "filters": {
          "sport":   { "term": { "categoria": "sport" } },
          "outdoor": { "term": { "categoria": "outdoor" } },
          "hiking":  { "term": { "categoria": "hiking" } }
        }
      }
    }
  }
}
```

### 2.4 Histogram Aggregation

```http
// Numeric histogram with regular intervals
{
  "aggs": {
    "price_distribution": {
      "histogram": {
        "field": "price",
        "interval": 25,
        "min_doc_count": 1,
        "extended_bounds": {
          "min": 0,
          "max": 500
        },
        "offset": 5,
        "keyed": true,
        "order": { "_key": "asc" }
      }
    }
  }
}

// Variable-width histogram (auto-determined bucket widths for even distribution)
{
  "aggs": {
    "auto_distribution": {
      "variable_width_histogram": {
        "field": "price",
        "buckets": 10
      }
    }
  }
}

// Auto-date histogram: automatically selects the best interval for N buckets
{
  "aggs": {
    "timeline": {
      "auto_date_histogram": {
        "field": "@timestamp",
        "buckets": 20,
        "minimum_interval": "hour"
      }
    }
  }
}
```

### 2.5 Sampler and Diversified Sampler

Limit the document set for sub-aggregations to improve performance and relevance:

```http
// Sampler: take top N documents per shard by relevance
{
  "aggs": {
    "top_sample": {
      "sampler": {
        "shard_size": 200
      },
      "aggs": {
        "keywords": {
          "significant_terms": { "field": "content", "size": 10 }
        }
      }
    }
  }
}

// Diversified sampler: limits overrepresentation of any single value
{
  "aggs": {
    "diverse_sample": {
      "diversified_sampler": {
        "shard_size": 200,
        "field": "author"
      },
      "aggs": {
        "common_terms": {
          "significant_terms": { "field": "tags", "size": 10 }
        }
      }
    }
  }
}
```

---

## 3. Pipeline Aggregations

### 3.1 avg_bucket, derivative, cumulative_sum

Le pipeline aggregations operano sui risultati di altre aggregazioni, non direttamente sui documenti.

```http
POST /metriche/_search
{
  "size": 0,
  "aggs": {
    "per_ora": {
      "date_histogram": {
        "field": "@timestamp",
        "fixed_interval": "1h"
      },
      "aggs": {
        "richieste_ora": { "sum": { "field": "richieste" } },
        "latenza_media": { "avg": { "field": "latenza_ms" } }
      }
    },

    "media_delle_medie": {
      "avg_bucket": {
        "buckets_path": "per_ora>latenza_media"
      }
    },

    "derivata_richieste": {
      "derivative": {
        "buckets_path": "per_ora>richieste_ora"
      }
    },

    "totale_cumulativo": {
      "cumulative_sum": {
        "buckets_path": "per_ora>richieste_ora"
      }
    },

    "moving_average_7d": {
      "moving_avg": {
        "buckets_path": "per_ora>latenza_media",
        "window": 168,
        "model": "ewma",
        "settings": { "alpha": 0.3 }
      }
    }
  }
}
```

### 3.2 Pipeline Aggregation Reference

| Pipeline Agg | Type | Description |
|-------------|------|-------------|
| `avg_bucket` | Sibling | Average of values in sibling buckets |
| `max_bucket` | Sibling | Max value across sibling buckets |
| `min_bucket` | Sibling | Min value across sibling buckets |
| `sum_bucket` | Sibling | Sum of values in sibling buckets |
| `stats_bucket` | Sibling | Stats (avg, min, max, sum, count) across buckets |
| `percentiles_bucket` | Sibling | Percentiles across bucket values |
| `derivative` | Parent | Rate of change between consecutive buckets |
| `cumulative_sum` | Parent | Running total across buckets |
| `cumulative_cardinality` | Parent | Running distinct count |
| `moving_avg` | Parent | Moving average with model selection |
| `moving_fn` | Parent | Custom moving window function |
| `serial_diff` | Parent | Difference between current and N-lagged value |
| `bucket_script` | Parent | Custom script across multiple metrics per bucket |
| `bucket_sort` | Parent | Sort buckets by a metric or truncate |
| `bucket_selector` | Parent | Filter buckets based on metric conditions |

### 3.3 bucket_script and bucket_selector

```http
POST /sales/_search
{
  "size": 0,
  "aggs": {
    "monthly": {
      "date_histogram": {
        "field": "@timestamp",
        "calendar_interval": "1M"
      },
      "aggs": {
        "revenue": { "sum": { "field": "revenue" } },
        "cost":    { "sum": { "field": "cost" } },
        "profit_margin": {
          "bucket_script": {
            "buckets_path": {
              "totalRevenue": "revenue",
              "totalCost": "cost"
            },
            "script": "(params.totalRevenue - params.totalCost) / params.totalRevenue * 100"
          }
        },
        "only_profitable": {
          "bucket_selector": {
            "buckets_path": {
              "margin": "profit_margin"
            },
            "script": "params.margin > 10"
          }
        },
        "sort_by_margin": {
          "bucket_sort": {
            "sort": [{ "profit_margin": { "order": "desc" } }],
            "size": 6
          }
        }
      }
    }
  }
}
```

### 3.4 Moving Function (Custom Window Calculations)

```http
{
  "aggs": {
    "hourly": {
      "date_histogram": {
        "field": "@timestamp",
        "fixed_interval": "1h"
      },
      "aggs": {
        "avg_latency": { "avg": { "field": "latency_ms" } },
        "anomaly_score": {
          "moving_fn": {
            "buckets_path": "avg_latency",
            "window": 24,
            "script": """
              if (values.length < 10) return 0;
              double mean = MovingFunctions.unweightedAvg(values);
              double std = MovingFunctions.stdDev(values, mean);
              if (std == 0) return 0;
              return Math.abs(values[values.length - 1] - mean) / std;
            """
          }
        }
      }
    }
  }
}
```

---

## 4. Aggregazioni Nidificate

### 4.1 Nested Aggregation

Per aggregare su campi di tipo `nested`, è necessario usare la `nested` aggregation per "scendere" nel contesto dell'oggetto annidato.

```http
POST /ordini/_search
{
  "size": 0,
  "aggs": {
    "prodotti_nested": {
      "nested": { "path": "prodotti" },
      "aggs": {
        "per_categoria": {
          "terms": { "field": "prodotti.categoria", "size": 10 },
          "aggs": {
            "fatturato": {
              "sum": { "script": "doc['prodotti.prezzo'].value * doc['prodotti.quantita'].value" }
            }
          }
        },
        "back_to_order": {
          "reverse_nested": {},
          "aggs": {
            "avg_order_value": { "avg": { "field": "totale_ordine" } }
          }
        }
      }
    }
  }
}
```

### 4.2 Multi-Level Nested Aggregation

For deeply nested structures, chain nested aggregations:

```http
// Mapping: orders → items (nested) → reviews (nested within items)
POST /orders/_search
{
  "size": 0,
  "aggs": {
    "items": {
      "nested": { "path": "items" },
      "aggs": {
        "reviews": {
          "nested": { "path": "items.reviews" },
          "aggs": {
            "avg_rating": { "avg": { "field": "items.reviews.rating" } },
            "back_to_items": {
              "reverse_nested": { "path": "items" },
              "aggs": {
                "category_rating": {
                  "terms": { "field": "items.category" },
                  "aggs": {
                    "back_to_reviews": {
                      "nested": { "path": "items.reviews" },
                      "aggs": {
                        "avg_review": { "avg": { "field": "items.reviews.rating" } }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

---

## 5. Composite Aggregation per Scrolling

### 5.1 Paginazione sulle Aggregazioni

La `composite` aggregation permette di paginare sui bucket quando il numero di combinazioni uniche è troppo elevato per un'aggregazione `terms` standard. È l'equivalente di `search_after` per le aggregazioni.

```http
POST /eventi/_search
{
  "size": 0,
  "aggs": {
    "combo_servizio_data": {
      "composite": {
        "size": 1000,
        "sources": [
          { "servizio": { "terms": { "field": "servizio" } } },
          {
            "data": {
              "date_histogram": {
                "field": "@timestamp",
                "calendar_interval": "1d",
                "format": "yyyy-MM-dd"
              }
            }
          }
        ]
      },
      "aggs": {
        "errori":   { "filter": { "term": { "level": "error" } } },
        "latenza":  { "avg": { "field": "latenza_ms" } }
      }
    }
  }
}

// Pagina successiva: usa after_key dall'ultima risposta
POST /eventi/_search
{
  "size": 0,
  "aggs": {
    "combo_servizio_data": {
      "composite": {
        "size": 1000,
        "after": { "servizio": "api-gateway", "data": "2026-05-05" },
        "sources": [
          { "servizio": { "terms": { "field": "servizio" } } },
          {
            "data": {
              "date_histogram": {
                "field": "@timestamp",
                "calendar_interval": "1d",
                "format": "yyyy-MM-dd"
              }
            }
          }
        ]
      }
    }
  }
}
```

### 5.2 Composite Aggregation Source Types

The composite aggregation supports multiple source types:

```http
{
  "composite": {
    "size": 500,
    "sources": [
      // Terms source (keyword)
      { "product": { "terms": { "field": "product_id" } } },

      // Histogram source (numeric)
      { "price_bucket": { "histogram": { "field": "price", "interval": 50 } } },

      // Date histogram source
      { "month": { "date_histogram": { "field": "@timestamp", "calendar_interval": "1M" } } },

      // GeoTile grid source (ES 7.9+)
      { "tile": { "geotile_grid": { "field": "location", "precision": 8 } } }
    ]
  }
}
```

### 5.3 Full Composite Pagination Pattern (Python)

```python
def iterate_composite(es, index, agg_body):
    """Iterate through all composite aggregation pages."""
    all_buckets = []
    after_key = None

    while True:
        body = {"size": 0, "aggs": {"comp": agg_body.copy()}}
        if after_key:
            body["aggs"]["comp"]["composite"]["after"] = after_key

        resp = es.search(index=index, body=body)
        buckets = resp["aggregations"]["comp"]["buckets"]

        if not buckets:
            break

        all_buckets.extend(buckets)
        after_key = resp["aggregations"]["comp"]["after_key"]

    return all_buckets
```

---

## 6. Aggregation Performance Optimization

### 6.1 Reducing Aggregation Cost

Aggregations are often the most expensive part of a query. Optimization strategies:

```http
// 1. Use filter context to narrow the document set BEFORE aggregating
POST /logs/_search
{
  "size": 0,
  "query": {
    "bool": {
      "filter": [
        { "range": { "@timestamp": { "gte": "now-24h" } } },
        { "term": { "environment": "production" } }
      ]
    }
  },
  "aggs": {
    "by_service": { "terms": { "field": "service", "size": 20 } }
  }
}

// 2. Use shard_size to control per-shard term collection
// Default shard_size = size * 1.5 + 10
// Increase for more accurate results on high-cardinality fields
{
  "aggs": {
    "top_categories": {
      "terms": {
        "field": "category",
        "size": 10,
        "shard_size": 100
      }
    }
  }
}

// 3. Use execution_hint for terms aggregations
{
  "aggs": {
    "by_status": {
      "terms": {
        "field": "status",
        "execution_hint": "map"
      }
    }
  }
}
// "map": uses a per-segment map (good for low-cardinality, many segments)
// "global_ordinals" (default): uses global ordinals (good for high-cardinality)
```

### 6.2 Eager Global Ordinals

For keyword fields used in frequent aggregations, pre-build global ordinals at refresh time:

```http
PUT /my-index/_mapping
{
  "properties": {
    "category": {
      "type": "keyword",
      "eager_global_ordinals": true
    }
  }
}
```

This trades index-time CPU (ordinals built during refresh) for faster aggregation queries. Enable only for fields that are aggregated frequently.

### 6.3 Request Cache for Aggregations

The request cache caches the full response of requests with `size: 0` (aggregation-only queries). Cache entries are invalidated when a shard refreshes.

```http
// Explicitly enable request cache
POST /my-index/_search?request_cache=true
{
  "size": 0,
  "aggs": { "total": { "sum": { "field": "revenue" } } }
}

// Check cache hit rates
GET /_nodes/stats/indices/request_cache?human=true

// Clear request cache
POST /my-index/_cache/clear?request=true
```

### 6.4 Collecting Mode

For deeply nested aggregations, the `collect_mode` parameter controls when child aggregations are computed:

```http
{
  "aggs": {
    "by_country": {
      "terms": {
        "field": "country",
        "size": 5,
        "collect_mode": "breadth_first"
      },
      "aggs": {
        "by_city": {
          "terms": { "field": "city", "size": 10 }
        }
      }
    }
  }
}
// "depth_first" (default): builds full sub-aggregation tree for every bucket
// "breadth_first": prunes top-level buckets first, then computes sub-aggs
//                  (faster when size << total unique values)
```

---

## 7. Multi-Terms and Rare Terms

### 7.1 multi_terms Aggregation (ES 7.12+)

Groups documents by multiple fields simultaneously (like SQL `GROUP BY field1, field2`):

```http
{
  "aggs": {
    "by_service_and_status": {
      "multi_terms": {
        "terms": [
          { "field": "service" },
          { "field": "http_status" }
        ],
        "size": 50,
        "order": { "_count": "desc" }
      },
      "aggs": {
        "avg_latency": { "avg": { "field": "latency_ms" } }
      }
    }
  }
}
```

Note: `multi_terms` is less efficient than `composite` for large result sets. Use `composite` for pagination; use `multi_terms` for small, sorted top-N groups.

### 7.2 rare_terms Aggregation

Finds terms that appear in very few documents (the opposite of `terms` which finds the most common):

```http
{
  "aggs": {
    "rare_errors": {
      "rare_terms": {
        "field": "error.type",
        "max_doc_count": 5
      }
    }
  }
}
```

This is useful for anomaly detection: new error types, unusual user agents, or rare status codes.

---

## 8. Significant Terms and Anomaly Detection

### 8.1 significant_terms

Identifies terms that are statistically overrepresented in the query results compared to the full index. Used for content recommendation, root cause analysis, and trend detection:

```http
// What terms are unusually common in ERROR logs compared to all logs?
POST /logs/_search
{
  "size": 0,
  "query": { "term": { "level": "ERROR" } },
  "aggs": {
    "unusual_terms": {
      "significant_terms": {
        "field": "message.keyword",
        "size": 10,
        "min_doc_count": 5,
        "shard_min_doc_count": 2,
        "background_filter": {
          "range": { "@timestamp": { "gte": "now-7d" } }
        }
      }
    }
  }
}
```

### 8.2 significant_text

Like `significant_terms` but operates on analyzed text fields (no need for `.keyword`):

```http
{
  "aggs": {
    "trending_topics": {
      "significant_text": {
        "field": "message",
        "filter_duplicate_text": true,
        "min_doc_count": 3
      }
    }
  }
}
```

### 8.3 Anomaly Detection Pattern with Aggregations

Combine pipeline aggregations to detect anomalies without ML:

```http
POST /metrics/_search
{
  "size": 0,
  "aggs": {
    "hourly": {
      "date_histogram": {
        "field": "@timestamp",
        "fixed_interval": "1h"
      },
      "aggs": {
        "error_rate": {
          "filter": { "term": { "level": "ERROR" } }
        },
        "total": { "value_count": { "field": "_id" } },
        "error_pct": {
          "bucket_script": {
            "buckets_path": {
              "errors": "error_rate._count",
              "total": "total"
            },
            "script": "params.total > 0 ? params.errors / params.total * 100 : 0"
          }
        },
        "z_score": {
          "moving_fn": {
            "buckets_path": "error_pct",
            "window": 168,
            "script": """
              if (values.length < 24) return 0;
              double mean = MovingFunctions.unweightedAvg(values);
              double std = MovingFunctions.stdDev(values, mean);
              if (std == 0) return 0;
              return Math.abs(values[values.length - 1] - mean) / std;
            """
          }
        },
        "flag_anomaly": {
          "bucket_selector": {
            "buckets_path": { "score": "z_score" },
            "script": "params.score > 3"
          }
        }
      }
    }
  }
}
```

---

## 9. Matrix and Geo Aggregations

### 9.1 Matrix Stats

Computes correlations and covariance between numeric fields:

```http
{
  "aggs": {
    "field_correlations": {
      "matrix_stats": {
        "fields": ["price", "rating", "reviews_count", "days_on_market"]
      }
    }
  }
}
// Returns: count, mean, variance, skewness, kurtosis, covariance matrix, correlation matrix
```

### 9.2 Geo Aggregations

```http
// geo_distance: concentric rings around a point
{
  "aggs": {
    "rings_around_milan": {
      "geo_distance": {
        "field": "location",
        "origin": { "lat": 45.46, "lon": 9.19 },
        "unit": "km",
        "ranges": [
          { "to": 5 },
          { "from": 5, "to": 20 },
          { "from": 20, "to": 50 },
          { "from": 50 }
        ]
      }
    }
  }
}

// geohash_grid: tile the world into geohash cells
{
  "aggs": {
    "heatmap": {
      "geohash_grid": {
        "field": "location",
        "precision": 5,
        "size": 10000
      },
      "aggs": {
        "center": { "geo_centroid": { "field": "location" } }
      }
    }
  }
}

// geotile_grid: tile the world into map tile cells (for Kibana Maps)
{
  "aggs": {
    "map_tiles": {
      "geotile_grid": {
        "field": "location",
        "precision": 8
      }
    }
  }
}

// geo_bounds: bounding box of all geo_points in the result
{
  "aggs": {
    "viewport": {
      "geo_bounds": { "field": "location", "wrap_longitude": true }
    }
  }
}
```

---

## 10. Troubleshooting

### 10.1 "Too many buckets" error

Default `search.max_buckets` is 65,535. Solutions:
- Increase the limit: `PUT /_cluster/settings {"persistent": {"search.max_buckets": 100000}}`
- Better: use `composite` aggregation with pagination instead of collecting all buckets in one request.
- Reduce the number of date_histogram buckets by using a larger interval.

### 10.2 Inaccurate terms aggregation counts

`terms` aggregation collects `shard_size` terms per shard and merges them. If a term is in the top-N globally but not in the top-N on every shard, it may be missed or have inaccurate counts. Increase `shard_size` for better accuracy at the cost of more memory:

```http
{ "terms": { "field": "tag", "size": 10, "shard_size": 200 } }
```

### 10.3 date_histogram missing empty buckets

By default, date_histogram omits buckets with zero documents. Use `min_doc_count: 0` and `extended_bounds` to include empty intervals:

```http
{
  "date_histogram": {
    "field": "@timestamp",
    "fixed_interval": "1h",
    "min_doc_count": 0,
    "extended_bounds": {
      "min": "2026-05-22T00:00:00Z",
      "max": "2026-05-22T23:59:59Z"
    }
  }
}
```

### 10.4 Aggregation on text field fails

Text fields do not have doc_values. Use the `.keyword` sub-field. Never enable `fielddata: true` on text fields for aggregations — it loads the entire inverted index into heap.

### 10.5 Nested aggregation returns wrong counts

Nested aggregation operates on nested documents (separate Lucene documents). The `doc_count` in nested aggregation reflects nested object count, not parent document count. Use `reverse_nested` to get back to parent document metrics.

### 10.6 Pipeline aggregation returns null for first bucket

Derivative and moving_fn aggregations need previous buckets to compute their values. The first bucket (and the first `window` buckets for moving functions) will have null or zero values. This is expected behavior; use `gap_policy: "skip"` to handle gaps.

### 10.7 Composite aggregation is slow

- Reduce `size` per page (1000 instead of 10000).
- Add a query filter to reduce the document set.
- Ensure all source fields have doc_values enabled.
- Avoid using runtime fields as composite sources.

### 10.8 High memory usage from aggregations

Check the `indices.breaker.request.limit` circuit breaker. Large cardinality aggregations on high-cardinality fields can exceed memory limits. Use `sampler` to limit the input set, or switch to `composite` for pagination.

### 10.9 Aggregation results differ between requests

If the index is receiving concurrent writes, aggregation results change between requests because new documents are visible after each refresh. Use a PIT (Point in Time) for consistent aggregation results across multiple requests.

### 10.10 sum aggregation returns 0 for non-zero data

Check that the field type supports numeric aggregations (integer, long, float, double, scaled_float). If the field is mapped as `text` or `keyword`, the sum returns 0 or errors. Also check for `null` values: use the `missing` parameter to supply a default.

```http
{ "sum": { "field": "price", "missing": 0 } }
```

---

## 11. FAQ

### Q1: What is the difference between terms and composite aggregation?

`terms` collects the top-N terms in a single request but is limited to 65,535 buckets and may have accuracy issues on distributed clusters. `composite` paginates through ALL unique combinations and is accurate, but requires multiple requests. Use `terms` for dashboards (top-N); use `composite` for data export or full enumeration.

### Q2: How accurate is the cardinality aggregation?

It uses HyperLogLog++ and is approximate. Set `precision_threshold` to control the trade-off. Below the threshold, counts are exact. Above it, the error rate is typically under 1% for `precision_threshold: 10000`.

### Q3: Can I sort aggregation buckets by a sub-aggregation value?

Yes. Use `order` with the sub-aggregation name:

```http
{ "terms": { "field": "product", "size": 10, "order": { "avg_price": "desc" } },
  "aggs": { "avg_price": { "avg": { "field": "price" } } }
}
```

### Q4: How do I compute a ratio across two aggregation results?

Use `bucket_script` pipeline aggregation to combine metrics within each bucket.

### Q5: What is the performance impact of deeply nested aggregations?

Each nesting level multiplies the number of buckets. A terms(100) → terms(50) → date_histogram(24) produces up to 120,000 buckets. Keep nesting shallow and use `size` constraints. Use `breadth_first` collect mode when the top-level `size` is much smaller than the total number of unique values.

### Q6: How do I export all aggregation results for offline analysis?

Use `composite` aggregation with pagination. Process each page and write results to a file or database. This is the only aggregation that supports exhaustive enumeration.

### Q7: Can aggregations work with runtime fields?

Yes, but runtime fields are computed at query time, so aggregations on runtime fields are slower than on indexed fields. Acceptable for ad-hoc analysis; promote to indexed fields for production dashboards.

### Q8: How does the request cache interact with aggregations?

Requests with `size: 0` (aggregation-only) are cached by default. The cache is invalidated when any shard in the index refreshes. For time-series data with frequent writes, the cache hit rate may be low. For static indices, the cache is highly effective.

### Q9: What is the max_buckets setting and when should I change it?

`search.max_buckets` (default 65,535) limits the total number of buckets across all aggregations in a single request. It exists to prevent accidental OOM from unbounded aggregations. Increase it only for batch analytics; use `composite` pagination instead.

### Q10: How do I aggregate on IP addresses?

IP fields support all standard aggregations. Use `ip_range` for IP-specific bucketing:

```http
{
  "aggs": {
    "ip_ranges": {
      "ip_range": {
        "field": "client_ip",
        "ranges": [
          { "from": "10.0.0.0", "to": "10.255.255.255" },
          { "from": "172.16.0.0", "to": "172.31.255.255" },
          { "from": "192.168.0.0", "to": "192.168.255.255" }
        ]
      }
    }
  }
}
```

---

*Questo documento fa parte del modulo 08 "Elasticsearch" della Data Encyclopedia.*
