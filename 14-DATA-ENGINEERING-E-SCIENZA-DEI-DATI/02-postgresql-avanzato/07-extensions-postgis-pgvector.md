# PostgreSQL Extensions: PostGIS, pgvector

> Autori: Team Data Encyclopedia  
> Ultimo aggiornamento: 2026-05-04  
> Versione: 1.0.0  
> Stato: draft

## Skip list
- [ ] Bozza iniziale
- [ ] Review tecnica
- [ ] Formattazione
- [ ] Pubblicazione

## Indice
1. Extensions in PostgreSQL
2. PostGIS: GIS Extension
3. PostGIS Data Types
4. PostGIS Spatial Indexes
5. PostGIS Functions
6. pgvector: Vector Similarity Search
7. pgvector Operations
8. pgvector with Embeddings
9. Combining Extensions
10. Extension Management

---

## 1. Extensions in PostgreSQL

### 1.1 Extension System

Le **Estensioni** sono moduli che aggiungono funzionalità a PostgreSQL senza modificare il core. Sono la via principale per estendere le capacità del database.

**Vantaggi delle estensioni**:
- Installazione atomica: una singola instruzione installa tutto (funzioni, tipi, indici, dati)
- Rimozione pulita: DROP EXTENSION rimuove tutto
- Versionamento: le estensioni hanno versioni, facilitano upgrades
- Standardizzazione: le estensioni comuni sono ben testate

**Tipi di estensioni**:
- **Core extensions**: incluse nella distribuzione PostgreSQL
- **Contrib extensions**: nel pacchetto contrib
- **External extensions**: sviluppate dalla comunità

### 1.2 List Extensions

Vedere le estensioni installate:

```sql
-- Lista estensioni installate
SELECT 
    extname,
    extversion,
    extnamespace::regnamespace as schema
FROM pg_extension
ORDER BY extname;

-- Estensioni disponibili nel sistema
SELECT * FROM pg_available_extensions ORDER BY name;
```

### 1.3 Install Extension

Installare un'estensione:

```sql
-- Installazione base
CREATE EXTENSION IF NOT EXISTS extension_name;

-- Con versione specifica
CREATE EXTENSION extension_name VERSION '1.2.3';

-- In uno schema specifico
CREATE EXTENSION extension_name SCHEMA my_extensions;

-- Aggiornare all'ultima versione
ALTER EXTENSION extension_name UPDATE;

-- Rimuovere
DROP EXTENSION extension_name;
```

### 1.4 Common Extensions

Le estensioni più utilizzate includono:

**postgis**: Supporto per dati geografici e GIS. Standard de facto per database spaziali.

**pgvector**: Similarity search per embeddings. Essenziale per applicazioni AI/ML.

**uuid-ossp**: Generazione UUID. Include funzioni per UUID v1, v4, v7.

**hstore**: Chiave-valori. Alternativa NoSQL in PostgreSQL.

**citext**: Case-insensitive text. Per email, username case-insensitive.

**pg_trgm**: Trigram similarity. Per fuzzy search e text matching.

**pg_stat_statements**: Monitoraggio query. Essenziale per performance tuning.

**pgvector**: Ora sono circa 600+ extension nella comunità, coprendo ogni need immaginabile.

---

## 2. PostGIS: GIS Extension

### 2.1 What is PostGIS

PostGIS è l'estensione geospaziale più completa per PostgreSQL. Aggiunge:

**Tipi di dati geografici**:
- POINT: singolo punto
- LINESTRING: linea
- POLYGON: area
- MULTIPOINT, MULTILINESTRING, MULTIPOLYGON: collezioni
- GEOMETRYCOLLECTION: collezione mista

**Funzioni spaziali**: Centinaia di funzioni per:
- Distanza e prossimità
- Intersezioni e overlay
- Transformazioni
- Aggregazione spaziale

**Conformità standard**: Soddisfa le specifiche OGC Simple Features e SQL/MM.

### 2.2 Enable PostGIS

Abilitare PostGIS:

```sql
-- Estensione core (minimo richiesto)
CREATE EXTENSION postgis;

-- Per dati raster
CREATE EXTENSION postgis_raster;

-- Per topologia (strade, confini)
CREATE EXTENSION postgis_topology;

-- Per geocoding
CREATE EXTENSION postgis_tiger_geocoder;

-- Verificare installazione
SELECT postgis_full_version();
```

**Requisiti**: PostGIS deve essere compilato e installato sul server. La maggior parte delle distribuzioni include PostGIS.

### 2.3 Spatial Data Types

Creare tabelle con tipi spaziali:

```sql
-- Tabella di punti (negozi)
CREATE TABLE stores (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200),
    location GEOGRAPHY(POINT, 4326)  -- SRID WGS84
);

-- Tabella di poligoni (aree di consegna)
CREATE TABLE delivery_areas (
    id SERIAL PRIMARY KEY,
    zone_name VARCHAR(100),
    area GEOMETRY(POLYGON, 4326)
);

-- Inserire dati
INSERT INTO stores (name, location) VALUES 
    ('Store NYC', ST_GeomFromText('POINT(-74.006 40.7128)', 4326)),
    ('Store LA', ST_GeomFromText('POINT(-118.2437 34.0522)', 4326));
```

### 2.4 Spatial Reference Systems

SRID (Spatial Reference System Identifier) identifica il sistema di coordinate:

```sql
-- 4326: WGS84 (GPS, web maps)
-- 3857: Web Mercator (Google Maps)
-- 32618: UTM Zone 18N (USA est)

-- Cambiare SRID
ALTER TABLE stores ALTER COLUMN location TYPE GEOGRAPHY(POINT, 4326);

-- Verificare SRID
SELECT ST_SRID(location) FROM stores LIMIT 1;
```

### 2.5 Spatial Queries

Query spaziali comuni:

```sql
-- Trovare negozi in un raggio (10km da un punto)
SELECT * FROM stores 
WHERE ST_DWithin(
    location, 
    ST_SetSRID(ST_MakePoint(-74.006, 40.7128), 4326)::geography, 
    10000
);

-- Distanza più vicino
SELECT 
    s.name,
    ST_Distance(s.location, ST_SetSRID(ST_MakePoint(-73.985, 40.758), 4326)::geography) as distance_meters
FROM stores s
ORDER BY distance_meters
LIMIT 1;

-- Intersezione (quali aree contengono un punto)
SELECT zone_name FROM delivery_areas 
WHERE ST_Contains(area, ST_SetSRID(ST_MakePoint(-74.006, 40.7128), 4326));
```

### 2.3 Geometry vs Geography

Due tipi:
- **Geometry**: planar, Cartesian
- **Geography**: spherical, meters

```sql
-- Geometry
CREATE TABLE cities (id int, geom geometry(Point, 4326));

-- Geography
CREATE TABLE cities_geo (id int, geog geography(Point, 4326));
```

---

## 3. PostGIS Data Types

### 3.1 Basic Types

Tipi base:
- POINT
- LINESTRING
- POLYGON
- MULTIPOINT
- MULTILINESTRING
- MULTIPOLYGON
- GEOMETRYCOLLECTION

### 3.2 SRID

Spatial Reference ID:
- 4326: WGS84 (lat/lon)
- 3857: Web Mercator
- Local: Unknown

### 3.3 Creating Geometries

Creare geometrie:
```sql
ST_GeomFromText('POINT(-122.4194 37.7749)', 4326)
ST_GeogFromText('POINT(-122.4194 37.7749)')
ST_MakePoint(lon, lat)
ST_Point(lon, lat)
```

---

## 4. PostGIS Spatial Indexes

### 4.1 GiST Index

Spatial index:
```sql
CREATE INDEX idx_cities_geom ON cities USING gist(geom);
```

### 4.2 Using Index

Usare index con:
- ST_DWithin
- ST_Intersects
- ST_Contains

### 4.3 Index Only Scan

Index only scans con visibility map.

### 4.4 Performance

Index tipicamente >1000x faster than table scan.

---

## 5. PostGIS Functions

### 5.1 Measurements

Misure:
```sql
-- Distance
ST_Distance(geom1, geom2)

-- Area
ST_Area(polygon)

-- Length
ST_Length(line)
```

### 5.2 Relationships

Relazioni:
```sql
-- Intersects
ST_Intersects(geom1, geom2)

-- Contains
ST_Contains(parent, child)

-- Within
ST_Within(child, parent)

-- DWithin (distance based)
ST_DWithin(geom1, geom2, radius)
```

### 5.3 Transformations

Trasformazioni:
```sql
-- Reproject
ST_Transform(geom, new_srid)

-- Simplify
ST_Simplify(geom, tolerance)

-- Buffer
ST_Buffer(geom, distance)
```

---

## 6. pgvector: Vector Similarity Search

### 6.1 What is pgvector

pgvector è un'estensione per **similarity search** su embeddings - rappresentazioni vettoriali di dati (testo, immagini, audio, etc.). È essenziale per applicazioni AI/ML che usano RAG (Retrieval Augmented Generation).

**Funzionalità**:
- Memorizzazione vettori multidimensionali
- Similarity search (cosine, euclidean, inner product)
- Indici per ricerca efficiente
- Approximate Nearest Neighbor (ANN) search

### 6.2 Install pgvector

```sql
CREATE EXTENSION vector;
```

### 6.3 Create Vector Columns

```sql
-- Tabella con embeddings
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    content TEXT,
    embedding VECTOR(1536)  -- dimensione (es. OpenAI ada-002)
);

-- Inserire embeddings
INSERT INTO documents (content, embedding) VALUES 
    ('PostgreSQL is powerful', '[0.1, 0.2, ...]'),
    ('Vector similarity search', '[0.3, 0.4, ...]');
```

### 6.4 Vector Operations

```sql
-- Similarity search (cosine distance)
SELECT id, content, 1 - (embedding <=> query_embedding) as similarity
FROM documents
ORDER BY embedding <=> query_embedding
LIMIT 5;

-- Con filtro
SELECT * FROM documents
WHERE category = 'tech'
ORDER BY embedding <=> query_embedding
LIMIT 5;
```

**Operatori**:
- `<=>`: cosine distance
- `<->`: euclidean distance
- `<#>`: inner product

### 6.5 Vector Indexes

Per ricerche efficienti su grandi dataset:

```sql
-- Index per approximate nearest neighbor
CREATE INDEX ON documents USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Per dataset molto grandi: HNSW
CREATE INDEX ON documents USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

**IVFFLAT**: Più veloce da costruire, buono per dataset medi. Lists determina bilanciamento speed/accuracy.

**HNSW**: Più accurato, migliore per query di qualità. M e ef_construction controllano qualità.

### 6.6 Combining with pgvector and AI

pgvector si integra perfettamente con applicazioni AI:

```sql
-- Pipeline RAG tipico
-- 1. Generare embedding da user query
-- 2. Cercare documenti simili
-- 3. Estrarre contesto per LLM

SELECT 
    d.content,
    1 - (d.embedding <=> $user_query_embedding) as relevance
FROM documents d
WHERE d.embedding <=> $user_query_embedding < 0.3  -- threshold
ORDER BY relevance
LIMIT 5;
```

### 6.3 Vector Type

Tipo vector:
```sql
CREATE TABLE embeddings (
    id INT,
    embedding vector(1536)  -- dimension based on model
);
```

### 6.4 Dimensions

Dimensioni comuni:
- OpenAI ada-002: 1536
- OpenAI text-embedding-3: 1536, 3072
- BERT: 768

---

## 7. pgvector Operations

### 7.1 Similarity Search

Ricerche similarità:
```sql
-- Cosine distance (default)
SELECT * FROM embeddings 
ORDER BY embedding <=> query_embedding;

-- L2 distance
SELECT * FROM embeddings 
ORDER BY embedding <-> query_embedding;

-- Inner product
SELECT * FROM embeddings 
ORDER BY embedding <#> query_embedding;
```

### 7.2 Indexes

Indici per similarity:
```sql
-- HNSW index
CREATE INDEX ON embeddings USING hnsw (embedding vector_cosine_ops);

-- IVFFlat index
CREATE INDEX ON embeddings USING ivfflat (embedding vector_cosine_ops);
```

### 7.3 Exact vs Approximate

Trade-off:
- Exact: no index, slow
- Approximate: index, fast but approximate

---

## 8. pgvector with Embeddings

### 8.1 Storing Embeddings

Integrare embeddings:
- Generate con AI model
- Store in PostgreSQL
- Query similar

### 8.2 Use Cases

Use cases:
- Semantic search
- Recommendation
- Anomaly detection
- Classification

### 8.3 Performance

Performance:
- HNSW: fast, memory
- IVFFlat: faster build, slower query

### 8.4 Combining with Metadata

Combinare:
```sql
SELECT d.*, e.embedding
FROM documents d
JOIN embeddings e ON d.id = e.document_id
WHERE e.embedding <=> $query_embedding < 0.5;
```

---

## 9. Combining Extensions

### 9.1 PostGIS + pgvector

Combinare:
```sql
CREATE TABLE locations (
    id INT,
    geom geometry(Point, 4326),
    description TEXT,
    embedding vector(768)
);
```

### 9.2 Spatial + Semantic Search

Ricerca ibrida:
```sql
SELECT * FROM locations
WHERE ST_DWithin(geom, ST_MakePoint($lon, $lat)::geography, $radius)
ORDER BY embedding <=> $query_embedding
LIMIT 10;
```

### 9.3 Use Cases

Applicazioni:
- Location-based AI
- Semantic geolocation
- Combined search

---

## 10. Extension Management

### 10.1 List Extensions

Vedere installate:
```sql
SELECT extname, extversion FROM pg_extension ORDER BY extname;
```

### 10.2 Update Extension

Aggiornare:
```sql
ALTER EXTENSION postgis UPDATE;
ALTER EXTENSION vector UPDATE;
```

### 10.3 Extensions Versions

Versioni specifiche:
```sql
CREATE EXTENSION postgis VERSION '3.4.0';
```

### 10.4 Security

Security:
- Only superuser can install
- Review extension code
- Keep updated

---

*Questo documento fa parte del modulo 02 "PostgreSQL Avanzato" della Data Encyclopedia.*