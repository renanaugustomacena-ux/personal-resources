# Architettura Tecnica SaaS — Guida Completa

## Indice

- [Panoramica](#panoramica)
- [Multi-Tenancy](#multi-tenancy)
- [Architettura Microservizi vs Monolite](#architettura-microservizi-vs-monolite)
- [API Design per SaaS](#api-design-per-saas)
- [API Gateway e Rate Limiting](#api-gateway-e-rate-limiting)
- [Scalabilità e Performance](#scalabilità-e-performance)
- [Database e Data Architecture](#database-e-data-architecture)
- [Strategie di Caching](#strategie-di-caching)
- [Background Job Processing](#background-job-processing)
- [Feature Flags e Rilascio Graduale](#feature-flags-e-rilascio-graduale)
- [CI/CD e DevOps per SaaS](#cicd-e-devops-per-saas)
- [Strategie di Deployment](#strategie-di-deployment)
- [Infrastruttura Cloud](#infrastruttura-cloud)
- [Pattern Infrastrutturali: Kubernetes, Serverless, PaaS](#pattern-infrastrutturali-kubernetes-serverless-paas)
- [Observability: Logging, Metriche, Tracing](#observability-logging-metriche-tracing)
- [Alta Disponibilità e Disaster Recovery](#alta-disponibilità-e-disaster-recovery)
- [Anti-Pattern e Errori Comuni](#anti-pattern-e-errori-comuni)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [FAQ — Domande Frequenti](#faq--domande-frequenti)
- [Matrici Decisionali di Riferimento](#matrici-decisionali-di-riferimento)

---

## Panoramica

L'architettura tecnica di un SaaS deve supportare multi-tenancy (servire centinaia o migliaia di clienti con la stessa infrastruttura), scalabilità (crescere con il business), alta disponibilità (99.9%+ uptime), sicurezza (isolamento dati tra tenant) e velocità di sviluppo (deploy frequenti senza downtime). Le scelte architetturali fatte all'inizio hanno un impatto enorme su costi, scalabilità e velocità di sviluppo per anni a venire.

### I Pilastri dell'Architettura SaaS

```
┌─────────────────────────────────────────────────────────────────┐
│                    ARCHITETTURA SaaS                            │
├─────────────┬─────────────┬──────────────┬─────────────────────┤
│  ISOLATION  │  SCALABILITY│  RELIABILITY │  OPERABILITY        │
│             │             │              │                     │
│ Multi-tenant│ Horizontal  │ HA / DR      │ CI/CD               │
│ Data safety │ Caching     │ Failover     │ Observability       │
│ RLS / ACL   │ Sharding    │ Chaos eng.   │ Feature flags       │
│ Encryption  │ Read replica│ Multi-AZ/reg │ IaC                 │
└─────────────┴─────────────┴──────────────┴─────────────────────┘
```

Ogni decisione architetturale è un trade-off. Non esiste una soluzione universale: la scelta giusta dipende da fase del prodotto, dimensione del team, budget e requisiti di compliance. Questa guida analizza ogni componente in profondità, fornendo framework decisionali concreti per ogni scenario.

### Evoluzione Architetturale Tipica di un SaaS

```
Fase 1 (Pre-PMF, 0-$1M ARR):
  Monolite → PostgreSQL → Heroku/Railway → Team 2-5 dev
  Obiettivo: velocità di iterazione, validare il mercato

Fase 2 (Growth, $1M-$10M ARR):
  Monolite modulare → PostgreSQL + Redis → AWS/GCP → Team 10-30 dev
  Obiettivo: scalabilità iniziale, processi CI/CD maturi

Fase 3 (Scale, $10M-$50M ARR):
  Microservizi selettivi → DB sharding → Kubernetes → Team 30-100 dev
  Obiettivo: scaling indipendente, team autonomi

Fase 4 (Enterprise, $50M+ ARR):
  Platform → Multi-region → Service mesh → Team 100+ dev
  Obiettivo: affidabilità 99.99%, compliance globale
```

---

## Multi-Tenancy

La multi-tenancy è il fondamento del modello SaaS: una singola istanza dell'applicazione serve contemporaneamente più clienti (tenant), ciascuno con i propri dati isolati.

### Architettura Concettuale Multi-Tenant

```
                        ┌──────────────┐
                        │  API Gateway │
                        │  + Auth      │
                        └──────┬───────┘
                               │
                    ┌──────────┼──────────┐
                    │          │          │
              ┌─────▼────┐ ┌──▼───┐ ┌───▼────┐
              │ Tenant A │ │  B   │ │   C    │
              │ context  │ │ ctx  │ │  ctx   │
              └─────┬────┘ └──┬───┘ └───┬────┘
                    │         │         │
              ┌─────▼─────────▼─────────▼────┐
              │     Application Layer         │
              │  (tenant_id propagato in      │
              │   ogni operazione)            │
              └──────────────┬───────────────┘
                             │
              ┌──────────────▼───────────────┐
              │      Data Layer              │
              │  (isolamento per modello     │
              │   scelto)                    │
              └──────────────────────────────┘
```

### Modelli di Multi-Tenancy

**1. Database condiviso, schema condiviso**
Tutti i tenant condividono lo stesso database e le stesse tabelle. Ogni riga ha un `tenant_id` per l'isolamento.

```sql
-- Ogni query include il filtro tenant
SELECT * FROM projects WHERE tenant_id = 'abc123' AND status = 'active';

-- CRITICO: dimenticare il filtro tenant_id espone dati di altri clienti
-- Usare Row Level Security (RLS) in PostgreSQL per prevenire errori
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON projects
  USING (tenant_id = current_setting('app.current_tenant'));
```

Pro: efficiente, facile da mantenere, costo basso. Contro: rischio di data leak se il filtro manca, noisy neighbor (un tenant pesante rallenta tutti), compliance complessa.

#### Implementazione Step-by-Step: Shared Schema con RLS

```sql
-- STEP 1: Creare la tabella con tenant_id come colonna obbligatoria
CREATE TABLE invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    customer_name TEXT NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- STEP 2: Indice composto con tenant_id come primo campo
-- CRITICO: senza questo indice, ogni query fa un full table scan
CREATE INDEX idx_invoices_tenant_status ON invoices(tenant_id, status);
CREATE INDEX idx_invoices_tenant_created ON invoices(tenant_id, created_at DESC);

-- STEP 3: Abilitare RLS sulla tabella
ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;

-- STEP 4: Policy di isolamento — il tenant vede solo i propri dati
CREATE POLICY tenant_isolation_select ON invoices
    FOR SELECT
    USING (tenant_id = current_setting('app.current_tenant')::UUID);

CREATE POLICY tenant_isolation_insert ON invoices
    FOR INSERT
    WITH CHECK (tenant_id = current_setting('app.current_tenant')::UUID);

CREATE POLICY tenant_isolation_update ON invoices
    FOR UPDATE
    USING (tenant_id = current_setting('app.current_tenant')::UUID)
    WITH CHECK (tenant_id = current_setting('app.current_tenant')::UUID);

CREATE POLICY tenant_isolation_delete ON invoices
    FOR DELETE
    USING (tenant_id = current_setting('app.current_tenant')::UUID);

-- STEP 5: L'applicazione imposta il tenant all'inizio di ogni request
-- Nel middleware (es. Express/FastAPI/Spring):
SET app.current_tenant = 'uuid-del-tenant';
-- Dopo questo SET, qualsiasi SELECT/INSERT/UPDATE/DELETE è automaticamente filtrato
```

#### Middleware Tenant Context (Node.js/Express)

```javascript
// middleware/tenantContext.js
// Estratto il tenant_id dal JWT e lo propago a PostgreSQL via RLS
async function tenantContext(req, res, next) {
    const tenantId = req.auth?.tenantId; // dal JWT decodificato
    if (!tenantId) {
        return res.status(403).json({ error: 'Tenant non identificato' });
    }

    // Iniettare tenant_id nel pool di connessioni
    req.db = await pool.connect();
    await req.db.query("SET app.current_tenant = $1", [tenantId]);

    // Cleanup: rilasciare la connessione dopo la response
    res.on('finish', () => {
        req.db.query("RESET app.current_tenant").finally(() => {
            req.db.release();
        });
    });

    next();
}
```

**2. Database condiviso, schema separato**
Ogni tenant ha il proprio schema nello stesso database.

Pro: isolamento migliore, migration per-tenant possibili. Contro: schema proliferation (10.000 tenant = 10.000 schema), backup/restore per-tenant complesso.

```
┌────────────────────────────────────────┐
│         PostgreSQL Instance            │
│                                        │
│  ┌──────────┐ ┌──────────┐ ┌────────┐ │
│  │ schema_  │ │ schema_  │ │schema_ │ │
│  │ tenant_a │ │ tenant_b │ │tenant_c│ │
│  │          │ │          │ │        │ │
│  │ users    │ │ users    │ │ users  │ │
│  │ invoices │ │ invoices │ │invoices│ │
│  │ projects │ │ projects │ │projects│ │
│  └──────────┘ └──────────┘ └────────┘ │
└────────────────────────────────────────┘
```

#### Gestione Schema-per-Tenant

```sql
-- Provisioning di un nuovo tenant
CREATE SCHEMA tenant_acme;

-- Creare le tabelle nello schema del tenant
SET search_path TO tenant_acme;
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL
);
CREATE TABLE invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    amount DECIMAL(12,2) NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft'
);

-- Il middleware imposta lo schema corretto per ogni request
SET search_path TO tenant_acme, public;
-- Ora tutte le query colpiscono automaticamente le tabelle di tenant_acme
```

**Problemi operativi schema-per-tenant:**
- Le migration devono essere eseguite su OGNI schema: `for schema in schemas; do migrate(schema); done`
- Il numero di tabelle nel catalogo di PostgreSQL cresce linearmente: 50 tabelle x 1.000 tenant = 50.000 entries in `pg_class`
- `pg_dump` e `pg_restore` per-tenant richiedono `-n schema_name`
- Connection pooling (PgBouncer) diventa complesso: il `search_path` è per-sessione, non per-transazione in modalità `transaction`

**3. Database separato per tenant**
Ogni tenant ha il proprio database dedicato.

Pro: isolamento completo, performance garantita, compliance semplice (dati fisicamente separati). Contro: costo alto, gestione complessa, migration da eseguire N volte.

```
┌──────────┐    ┌──────────┐    ┌──────────┐
│  DB      │    │  DB      │    │  DB      │
│ tenant_a │    │ tenant_b │    │ tenant_c │
│          │    │          │    │          │
│ (RDS)    │    │ (RDS)    │    │ (RDS)    │
│ $50/mese │    │ $50/mese │    │ $50/mese │
└──────────┘    └──────────┘    └──────────┘

Costo: N tenant × $50/mese = $5.000/mese per 100 tenant (solo DB)
vs schema condiviso: 1 × $200/mese per 100 tenant
```

#### Flusso di Provisioning per DB-per-Tenant

```
1. Tenant si registra → webhook → servizio provisioning
2. Provisioning crea:
   a. Nuovo database RDS (o schema, in base al tier)
   b. Utente DB dedicato con permessi ristretti
   c. Entry nella tabella "tenant_registry" (DB centrale)
   d. DNS record (se tenant ha sottodominio dedicato)
   e. Configurazione cache (namespace Redis)
3. Application router consulta tenant_registry per routing
4. Health check verifica la connessione al nuovo DB
5. Welcome email al tenant
```

### Quale Modello Scegliere

| Criterio | Schema condiviso | Schema separato | DB separato |
|---|---|---|---|
| Costo | Basso | Medio | Alto |
| Isolamento | Logico | Buono | Completo |
| Scalabilità tenant | Illimitata | Migliaia | Centinaia |
| Compliance | Complessa | Media | Semplice |
| Noisy neighbor | Rischio | Rischio ridotto | Nessuno |
| Ideale per | SMB, self-service | Mid-market | Enterprise |
| Complessità migration | Bassa (1 sola) | Alta (N schema) | Alta (N database) |
| Backup per-tenant | Complesso (filtro) | Medio (pg_dump -n) | Semplice (backup DB) |
| Cross-tenant analytics | Facile (stessa tabella) | Medio (UNION su schema) | Difficile (ETL necessario) |
| Connection pooling | Semplice | Complesso | Molto complesso |
| Tempo di provisioning | Millisecondi | Secondi | Minuti |

**Approccio ibrido** (molto comune): schema condiviso per SMB/free tier, database dedicato per enterprise con requisiti compliance. Tiered tenancy.

### Tiered Tenancy — Implementazione Pratica

```
┌────────────────────────────────────────────────────────┐
│                   TENANT ROUTER                        │
│                                                        │
│  tenant_registry:                                      │
│  ┌──────────┬───────────┬──────────────────────┐       │
│  │ tenant_id│ tier      │ db_connection_string  │       │
│  ├──────────┼───────────┼──────────────────────┤       │
│  │ acme     │ free      │ shared_db (RLS)       │       │
│  │ bigcorp  │ pro       │ shared_db (RLS)       │       │
│  │ megacorp │ enterprise│ dedicated_db_megacorp │       │
│  │ govorg   │ regulated │ isolated_db_govorg    │       │
│  └──────────┴───────────┴──────────────────────┘       │
└────────────────────────────────────────────────────────┘

Routing logic:
  1. Estrarre tenant_id dall'header/JWT/sottodominio
  2. Lookup nel registry (cache Redis per performance)
  3. Ottenere connection string per il tier
  4. Propagare il contesto tenant nella request
```

### Tenant Identification Strategies

| Strategia | Esempio | Pro | Contro |
|---|---|---|---|
| Sottodominio | `acme.app.com` | Chiaro, SEO-friendly | Gestione DNS, SSL wildcard |
| Path prefix | `app.com/acme/...` | Semplice, un solo dominio | Rischio di collisione path |
| Header custom | `X-Tenant-Id: acme` | Flessibile, API-friendly | Non funziona nel browser |
| JWT claim | `{ "tenant": "acme" }` | Sicuro, standard | Richiede autenticazione |
| Dominio custom | `app.acme.com` | Brand del cliente | Complessità SSL/DNS estrema |

---

## Architettura Microservizi vs Monolite

### Monolite

Una singola applicazione che gestisce tutte le funzionalità.

**Pro**: semplice da sviluppare, deployare e debuggare. Transazioni ACID naturali. Perfetto per team < 10 sviluppatori e prodotto pre-PMF.

**Contro**: diventa ingestibile oltre una certa dimensione (codice accoppiato, deploy rischiosi, scaling impossibile per singolo componente).

### Microservizi

L'applicazione è composta da servizi indipendenti, ciascuno con il proprio database, comunicanti via API/messaging.

**Pro**: scaling indipendente (scalare solo il servizio sotto pressione), deploy indipendenti (aggiornare un servizio senza toccare gli altri), team autonomi (ogni team possiede il suo servizio), technology diversity.

**Contro**: complessità operativa enorme (networking, service discovery, distributed tracing, eventual consistency), latenza inter-servizio, debugging distribuito difficile.

### Matrice Decisionale: Monolite vs Microservizi

| Fattore | Monolite | Monolite Modulare | Microservizi |
|---|---|---|---|
| Team size | 1-10 dev | 5-30 dev | 20+ dev |
| Velocità iniziale | Massima | Alta | Bassa |
| Costo operativo | Basso | Basso | Alto |
| Deploy indipendente | No | Parziale | Sì |
| Scaling granulare | No | Parziale | Sì |
| Transazioni ACID | Naturale | Naturale | Saga pattern |
| Debugging | Semplice | Medio | Complesso |
| Testing E2E | Semplice | Medio | Complesso |
| Technology diversity | No | No | Sì |
| Tolleranza ai guasti | Tutto o niente | Parziale | Per servizio |

### Quando Migrare

```
REGOLA PRATICA:

  < 10 sviluppatori, < $1M ARR: Monolite
    → La velocità di sviluppo è più importante della scalabilità
    → "Premature optimization is the root of all evil"

  10-30 sviluppatori, $1M-$10M ARR: Monolite modulare
    → Separare il monolite in moduli ben definiti
    → Preparare i confini per una futura estrazione

  30+ sviluppatori, > $10M ARR: Microservizi (graduale)
    → Estrarre servizi uno alla volta, partendo dai più critici
    → Non fare un big-bang rewrite (il progetto fallirà)

  Eccezione: servizi naturalmente indipendenti (email sending,
  image processing, billing) possono essere estratti prima.
```

### Pattern Intermedi

**Modular monolith**: un monolite con confini chiari tra moduli. Ogni modulo ha le sue tabelle, la sua API interna. Facile da estrarre in microservizio quando serve. È il miglior punto di partenza.

```
┌──────────────────────────────────────────────┐
│            MODULAR MONOLITH                  │
│                                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐     │
│  │  Auth    │ │ Billing  │ │ Projects │     │
│  │  Module  │ │  Module  │ │  Module  │     │
│  │          │ │          │ │          │     │
│  │ users    │ │ invoices │ │ projects │     │
│  │ sessions │ │ payments │ │ tasks    │     │
│  │ roles    │ │ plans    │ │ files    │     │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘     │
│       │            │            │            │
│  ┌────▼────────────▼────────────▼─────┐      │
│  │      Internal API / Event Bus      │      │
│  └────────────────────────────────────┘      │
│                                              │
│  ┌────────────────────────────────────┐      │
│  │       Shared Database (PostgreSQL) │      │
│  │  (ogni modulo possiede le proprie  │      │
│  │   tabelle, nessun JOIN cross-modulo│      │
│  │   — solo API interne)             │      │
│  └────────────────────────────────────┘      │
└──────────────────────────────────────────────┘

REGOLA: un modulo non accede MAI direttamente alle tabelle
di un altro modulo. Comunicazione solo via API interna o eventi.
Questa regola prepara l'estrazione futura in microservizio.
```

**Strangler Fig Pattern** — migrazione graduale da monolite a microservizi:

```
FASE 1: Monolite gestisce tutto
  ┌─────────────┐
  │  MONOLITE   │ ←── tutto il traffico
  └─────────────┘

FASE 2: Nuovo servizio affianca il monolite
  ┌────────────┐     ┌─────────────────┐
  │  MONOLITE  │     │ Notification    │
  │  (senza    │     │ Service (nuovo) │
  │  notifiche)│     │                 │
  └──────┬─────┘     └────────┬────────┘
         │                    │
  ┌──────▼────────────────────▼──────┐
  │        API Gateway / Proxy       │
  │  /api/notifications → nuovo     │
  │  /api/* → monolite              │
  └──────────────────────────────────┘

FASE 3: Ripetere per ogni servizio da estrarre
  Regola: estrarre un servizio alla volta
  Priorità di estrazione:
    1. Servizi con scaling diverso (es. media processing)
    2. Servizi con ciclo di rilascio diverso (es. billing)
    3. Servizi con team dedicato
    4. MAI estrarre servizi strettamente accoppiati insieme
```

**Service mesh**: per i microservizi, gestisce networking, load balancing, service discovery, mTLS. Tool: Istio, Linkerd.

### Event-Driven Architecture per Microservizi

```
┌──────────┐    publish     ┌──────────────┐    subscribe    ┌──────────┐
│  Order   │ ──────────────►│  Event Bus   │───────────────► │ Billing  │
│ Service  │  OrderCreated  │ (Kafka/NATS/ │  OrderCreated   │ Service  │
└──────────┘                │  RabbitMQ)   │                 └──────────┘
                            │              │───────────────► ┌──────────┐
                            │              │  OrderCreated   │ Notif.   │
                            └──────────────┘                 │ Service  │
                                                             └──────────┘
Vantaggi:
  - Servizi disaccoppiati (non si conoscono tra loro)
  - Nuovi consumer aggiunti senza modificare il producer
  - Event sourcing possibile (audit trail completo)
  - Resilienza: se Billing è temporaneamente down,
    l'evento resta in coda

Rischi:
  - Eventual consistency (non immediate consistency)
  - Event ordering complesso
  - Debug più difficile (distributed tracing essenziale)
  - Schema evolution degli eventi da gestire (Avro/Protobuf)
```

### Identificare i Service Boundaries

Regola pratica per capire dove tagliare il monolite:

1. **Bounded Context (DDD)**: ogni servizio corrisponde a un bounded context nel dominio
2. **Team ownership**: un servizio = un team proprietario
3. **Data ownership**: un servizio possiede i propri dati, nessun altro servizio accede direttamente al suo DB
4. **Deploy independence**: il servizio può essere deployato senza coordinamento con altri
5. **Scaling independence**: il servizio ha requisiti di scaling diversi

```
SEGNALI che un modulo è pronto per l'estrazione:

  ✓ Ha un team dedicato (o lo avrà presto)
  ✓ Ha requisiti di scaling diversi dal resto
  ✓ Ha un ciclo di rilascio più veloce
  ✓ Ha poche dipendenze verso altri moduli
  ✓ Il suo failure non deve impattare il resto del sistema
  ✗ NON estrarre se ha JOIN cross-module nel DB
  ✗ NON estrarre se le transazioni ACID sono critiche con altri moduli
  ✗ NON estrarre "perché i microservizi sono cool"
```

---

## API Design per SaaS

### REST API

Lo standard per le API SaaS. Principi: risorse come URL, verbi HTTP (GET/POST/PUT/DELETE), stateless, JSON.

```
GET    /api/v1/projects           → lista progetti
POST   /api/v1/projects           → crea progetto
GET    /api/v1/projects/:id       → dettaglio progetto
PUT    /api/v1/projects/:id       → aggiorna progetto
DELETE /api/v1/projects/:id       → elimina progetto
```

### Versioning

Strategia consigliata: URL versioning (`/api/v1/`, `/api/v2/`). Supportare almeno 2 versioni contemporaneamente. Deprecation notice 6-12 mesi prima della rimozione.

#### Strategie di Versioning a Confronto

| Strategia | Esempio | Pro | Contro |
|---|---|---|---|
| URL path | `/api/v1/users` | Esplicito, facile routing | URL diversi per ogni versione |
| Header custom | `X-API-Version: 2` | URL stabili | Meno visibile, debug difficile |
| Accept header | `Accept: application/vnd.api.v2+json` | Standard HTTP | Complesso da implementare |
| Query param | `/api/users?version=2` | Semplice | Caching complicato |

```
STRATEGIA RACCOMANDATA: URL path versioning

  /api/v1/projects   ← versione attuale (stabile)
  /api/v2/projects   ← nuova versione (in beta)

  Regole di lifecycle:
    1. v1 rilasciata → stabile per almeno 12 mesi
    2. v2 rilasciata → v1 entra in "sunset" (deprecation notice)
    3. 6-12 mesi di deprecation con header:
       Sunset: Sat, 01 Mar 2027 00:00:00 GMT
       Deprecation: true
    4. v1 rimossa → 410 Gone con link alla documentazione v2
```

### Contract-First API Design (OpenAPI)

```yaml
# openapi.yaml — definire il contratto PRIMA di scrivere il codice
openapi: 3.1.0
info:
  title: SaaS Platform API
  version: 1.0.0
paths:
  /api/v1/projects:
    get:
      operationId: listProjects
      parameters:
        - name: page
          in: query
          schema: { type: integer, minimum: 1, default: 1 }
        - name: per_page
          in: query
          schema: { type: integer, minimum: 1, maximum: 100, default: 20 }
        - name: status
          in: query
          schema: { type: string, enum: [active, archived, draft] }
      responses:
        '200':
          description: Lista progetti paginata
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ProjectList'
        '429':
          description: Rate limit superato

components:
  schemas:
    ProjectList:
      type: object
      properties:
        data:
          type: array
          items: { $ref: '#/components/schemas/Project' }
        meta:
          $ref: '#/components/schemas/PaginationMeta'
```

### Formato di Risposta Standard

```json
// SUCCESSO
{
  "status": "success",
  "data": {
    "id": "proj_abc123",
    "name": "Progetto Alpha",
    "status": "active"
  },
  "meta": {
    "request_id": "req_xyz789"
  }
}

// ERRORE
{
  "status": "error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Il campo 'name' è obbligatorio",
    "details": [
      {
        "field": "name",
        "rule": "required",
        "message": "Il campo è obbligatorio"
      }
    ]
  },
  "meta": {
    "request_id": "req_xyz790"
  }
}

// LISTA PAGINATA
{
  "status": "success",
  "data": [ ... ],
  "meta": {
    "pagination": {
      "page": 2,
      "per_page": 20,
      "total": 156,
      "total_pages": 8
    },
    "request_id": "req_xyz791"
  }
}
```

### Paginazione: Offset vs Cursor

| Strategia | Pro | Contro | Quando usare |
|---|---|---|---|
| Offset (`?page=3&per_page=20`) | Semplice, navigazione random | Inconsistente con dati mutevoli, lento su tabelle grandi | Dashboard, admin panels |
| Cursor (`?cursor=eyJpZCI6MTAwfQ`) | Consistente, performante | Nessuna navigazione random | Feed, timeline, API pubbliche |

```
Cursor-based pagination (consigliata per API ad alto traffico):

  GET /api/v1/events?limit=20
  → { data: [...], meta: { next_cursor: "abc123", has_more: true } }

  GET /api/v1/events?limit=20&cursor=abc123
  → { data: [...], meta: { next_cursor: "def456", has_more: true } }

  Implementazione DB:
  SELECT * FROM events
  WHERE id > decode_cursor('abc123')
  ORDER BY id ASC
  LIMIT 21;  -- 21 per sapere se esiste la pagina successiva
```

### Rate Limiting

Proteggere l'API da abuso. Implementare per: tenant (1000 req/min), per utente (100 req/min), per endpoint (sensibili: 10 req/min). Header standard: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`. Risposta: `429 Too Many Requests`.

### Webhook

Per eventi asincroni: `project.created`, `invoice.paid`, `subscription.cancelled`. Il SaaS invia una POST al URL configurato dal cliente. Implementare: retry con exponential backoff, firma HMAC per autenticità, logging per debug.

#### Implementazione Webhook Robusta

```
Flusso webhook:

  1. Evento accade (es. invoice.paid)
  2. Payload costruito + firma HMAC-SHA256 calcolata
  3. POST al webhook URL del tenant
  4. Se 2xx → successo, registrare delivery
  5. Se timeout/5xx → retry con exponential backoff:
       Tentativo 1: dopo 1 minuto
       Tentativo 2: dopo 5 minuti
       Tentativo 3: dopo 30 minuti
       Tentativo 4: dopo 2 ore
       Tentativo 5: dopo 12 ore (ultimo tentativo)
  6. Se tutti i tentativi falliscono → marcare webhook come "failing"
  7. Dopo 3 giorni di failure → disabilitare + notificare l'admin del tenant
  8. Tenant può vedere la delivery history nella dashboard

Firma HMAC (il ricevente può verificare l'autenticità):
  signature = HMAC-SHA256(webhook_secret, timestamp + "." + payload_json)
  Header: X-Webhook-Signature: t=1700000000,v1=abc123...
```

### Autenticazione API

| Metodo | Sicurezza | Complessità | Quando usare |
|---|---|---|---|
| API Key | Media | Bassa | Integrazioni server-to-server semplici |
| OAuth 2.0 + JWT | Alta | Alta | Utenti che accedono a dati di terze parti |
| JWT Bearer Token | Alta | Media | API proprie, dashboard, mobile app |
| mTLS | Molto alta | Molto alta | Comunicazione interna tra microservizi |

---

## API Gateway e Rate Limiting

### Ruolo dell'API Gateway

```
┌──────────────────────────────────────────────────────────┐
│                     API GATEWAY                          │
│                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │ Auth &      │  │ Rate        │  │ Request         │  │
│  │ Identity    │  │ Limiting    │  │ Routing         │  │
│  └─────────────┘  └─────────────┘  └─────────────────┘  │
│                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │ Request     │  │ Response    │  │ Logging &       │  │
│  │ Transform   │  │ Transform   │  │ Analytics       │  │
│  └─────────────┘  └─────────────┘  └─────────────────┘  │
│                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │ SSL/TLS     │  │ CORS        │  │ Circuit         │  │
│  │ Termination │  │ Handling    │  │ Breaker         │  │
│  └─────────────┘  └─────────────┘  └─────────────────┘  │
└──────────────┬────────────┬──────────────┬───────────────┘
               │            │              │
         ┌─────▼──┐   ┌────▼───┐   ┌─────▼──┐
         │ Auth   │   │Project │   │Billing │
         │Service │   │Service │   │Service │
         └────────┘   └────────┘   └────────┘
```

### Confronto API Gateway

| Gateway | Tipo | Pro | Contro |
|---|---|---|---|
| Kong | Open source | Plugin ecosystem, Lua scripting | Complessità operativa |
| AWS API Gateway | Managed | Zero ops, integrazione AWS nativa | Vendor lock-in, latenza aggiuntiva |
| Envoy/Istio | Service mesh | L7 proxy, gRPC nativo | Curva di apprendimento ripida |
| Traefik | Open source | Auto-discovery, Docker/K8s nativo | Meno plugin di Kong |
| NGINX | Self-managed | Performante, ben conosciuto | Configurazione manuale |

### Rate Limiting Avanzato

```
STRATEGIE DI RATE LIMITING:

1. Fixed Window (semplice ma bursty)
   Limite: 100 req/min
   Finestra: 12:00:00 - 12:01:00
   Problema: 100 req a 12:00:59 + 100 req a 12:01:00 = 200 req in 2 secondi

2. Sliding Window (bilanciato)
   Conta le request negli ultimi 60 secondi da "adesso"
   Più equo, elimina il burst al confine finestra

3. Token Bucket (flessibile, consigliato)
   Bucket con N token, ricarica R token/secondo
   Ogni request consuma 1 token
   Permette burst controllati (fino a N request immediate)
   Esempio: bucket=50, refill=10/sec → burst di 50, poi 10 req/sec

4. Leaky Bucket (rate costante)
   Coda di dimensione fissa, svuotata a rate costante
   Nessun burst: tutte le request processate alla stessa velocità
```

#### Rate Limiting per Tier SaaS

```
┌──────────────────────────────────────────────────────┐
│                RATE LIMITS PER PIANO                  │
│                                                      │
│  Free:                                               │
│    - 60 req/min per tenant                           │
│    - 10 req/min per endpoint write                   │
│    - 1.000 req/giorno totali                         │
│    - Nessun accesso API bulk                         │
│                                                      │
│  Pro:                                                │
│    - 600 req/min per tenant                          │
│    - 100 req/min per endpoint write                  │
│    - 100.000 req/giorno totali                       │
│    - API bulk disponibile (rate ridotto)             │
│                                                      │
│  Enterprise:                                         │
│    - 6.000 req/min per tenant                        │
│    - 1.000 req/min per endpoint write                │
│    - Nessun limite giornaliero                       │
│    - API bulk completa                               │
│    - SLA su latenza: p99 < 200ms                     │
└──────────────────────────────────────────────────────┘
```

#### Implementazione Rate Limiting con Redis

```python
# Token Bucket implementato con Redis + Lua script atomico
# Lua script per atomicità (no race condition)
RATE_LIMIT_SCRIPT = """
local key = KEYS[1]
local max_tokens = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])   -- token/secondo
local now = tonumber(ARGV[3])

local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
local tokens = tonumber(bucket[1]) or max_tokens
local last_refill = tonumber(bucket[2]) or now

-- Calcolare token da aggiungere dal last refill
local elapsed = now - last_refill
local new_tokens = math.min(max_tokens, tokens + (elapsed * refill_rate))

if new_tokens >= 1 then
    new_tokens = new_tokens - 1
    redis.call('HMSET', key, 'tokens', new_tokens, 'last_refill', now)
    redis.call('EXPIRE', key, math.ceil(max_tokens / refill_rate) * 2)
    return {1, math.floor(new_tokens), 0}  -- allowed, remaining, retry_after
else
    local retry_after = (1 - new_tokens) / refill_rate
    return {0, 0, math.ceil(retry_after)}   -- denied, remaining, retry_after
end
"""
```

---

## Scalabilità e Performance

### Scaling Verticale vs Orizzontale

**Verticale**: server più potente (più CPU, RAM). Semplice, nessun cambio architetturale. Limite fisico: non puoi scalare indefinitamente.

**Orizzontale**: più server. Richiede: applicazione stateless, load balancer, database scalabile. Nessun limite teorico.

```
SCALING VERTICALE:                    SCALING ORIZZONTALE:

  ┌─────────┐                         ┌───┐ ┌───┐ ┌───┐ ┌───┐
  │         │                         │ S │ │ S │ │ S │ │ S │
  │  MEGA   │                         │ 1 │ │ 2 │ │ 3 │ │ 4 │
  │ SERVER  │                         └─┬─┘ └─┬─┘ └─┬─┘ └─┬─┘
  │         │                           │     │     │     │
  │ 96 CPU  │                    ┌──────┴─────┴─────┴─────┴──┐
  │ 768 GB  │                    │      LOAD BALANCER         │
  │  RAM    │                    └────────────────────────────┘
  └─────────┘
  Costo: $$$$$                   Costo: 4 × $$  (spesso meno)
  Limite: hardware               Limite: architettura
  Downtime per upgrade: sì       Downtime per upgrade: no
```

### Pattern di Scalabilità SaaS

**Stateless application**: nessuno stato nella memoria del server. La sessione è in un store esterno (Redis). Qualsiasi server può gestire qualsiasi richiesta → scaling orizzontale facile.

**Caching**: ridurre il carico sul database. Layer: browser cache → CDN → application cache (Redis/Memcached) → database query cache. L'80% delle richieste in un SaaS è lettura → il caching ha impatto enorme.

**Queue-based processing**: operazioni pesanti (report generation, email sending, data import) in coda asincrona. Il server API risponde immediatamente, un worker processa in background. Tool: Redis Queue, RabbitMQ, SQS.

**Read replica**: per database read-heavy, aggiungere repliche in lettura. Il master gestisce le scritture, le repliche le letture. Riduce il carico del master del 60-80%.

**Sharding**: dividere i dati su più database per volume. Shard key tipica nel SaaS: tenant_id (tutti i dati di un tenant sullo stesso shard).

**CDN**: servire asset statici (JS, CSS, immagini) da edge server vicini all'utente. Riduce la latenza del 50-80% per utenti geograficamente distanti. Tool: CloudFront, Cloudflare, Fastly.

### Performance Budget

Target per un SaaS moderno:
- **TTFB** (Time to First Byte): < 200ms
- **Page load**: < 3 secondi
- **API response**: < 200ms per il 95° percentile
- **Uptime**: 99.9% = max 8.7 ore di downtime/anno

### Scaling Checklist

```
□ L'applicazione è stateless? (nessun stato in memoria)
□ Le sessioni sono in un external store (Redis)?
□ Il file upload va a object storage (S3), non a disco locale?
□ I background job sono in una coda (non in-process)?
□ Il database ha connection pooling (PgBouncer)?
□ Le query lente sono identificate e ottimizzate?
□ Gli indici DB coprono le query più frequenti?
□ Il caching è implementato per i dati letti frequentemente?
□ L'auto-scaling è configurato per le ore di punta?
□ Il CDN serve gli asset statici?
□ I log sono centralizzati (non su disco locale)?
□ I health check sono implementati per il load balancer?
```

---

## Database e Data Architecture

### SQL vs NoSQL nel SaaS

**SQL (PostgreSQL, MySQL)**: scelta predefinita per il 90% dei SaaS. ACID compliance, relazioni complesse, query flessibili, ecosistema maturo. PostgreSQL è la scelta standard: supporta JSON, full-text search, partitioning, Row Level Security.

**NoSQL (MongoDB, DynamoDB)**: per dati non strutturati, scalabilità orizzontale nativa, schema flessibile. Utile per: log, eventi analytics, dati IoT, contenuti generati dagli utenti con schema variabile.

**Approccio ibrido**: PostgreSQL per i dati core (utenti, billing, configurazioni) + Redis per caching/sessioni + Elasticsearch per search + time-series DB per analytics.

### Database Sharding per Multi-Tenant

```
SHARDING BY TENANT_ID:

  Shard Router
       │
  ┌────┴────────────────────────────┐
  │  tenant_id hash % N_shards     │
  └────┬──────┬──────┬──────┬──────┘
       │      │      │      │
  ┌────▼─┐┌───▼──┐┌──▼───┐┌▼─────┐
  │Shard ││Shard ││Shard ││Shard │
  │  0   ││  1   ││  2   ││  3   │
  │      ││      ││      ││      │
  │A,E,I ││B,F,J ││C,G,K ││D,H,L │
  └──────┘└──────┘└──────┘└──────┘

Regole di sharding nel SaaS:
  1. Shard key = tenant_id (SEMPRE)
     → Tutti i dati di un tenant sullo stesso shard
     → No cross-shard JOIN (performance killer)
  2. Lo shard non deve essere troppo grande (< 500 GB)
  3. Hot shard: se un tenant enterprise è troppo grande,
     spostarlo su shard dedicato
  4. Resharding è doloroso — pianificare N shards > del necessario
```

### Partitioning in PostgreSQL

```sql
-- Table partitioning per tenant_id (PostgreSQL 11+)
-- Utile per query performance e manutenzione (vacuum per-partizione)

CREATE TABLE events (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    event_type TEXT NOT NULL,
    payload JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
) PARTITION BY HASH (tenant_id);

-- Creare le partizioni (es. 16 partizioni)
CREATE TABLE events_p0 PARTITION OF events
    FOR VALUES WITH (MODULUS 16, REMAINDER 0);
CREATE TABLE events_p1 PARTITION OF events
    FOR VALUES WITH (MODULUS 16, REMAINDER 1);
-- ... fino a p15

-- ALTERNATIVA: Range partitioning per data (utile per audit/compliance)
CREATE TABLE audit_log (
    id BIGSERIAL,
    tenant_id UUID NOT NULL,
    action TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
) PARTITION BY RANGE (created_at);

CREATE TABLE audit_log_2025_q1 PARTITION OF audit_log
    FOR VALUES FROM ('2025-01-01') TO ('2025-04-01');
CREATE TABLE audit_log_2025_q2 PARTITION OF audit_log
    FOR VALUES FROM ('2025-04-01') TO ('2025-07-01');
-- Vantaggio: DROP vecchie partizioni per retention senza DELETE lento
```

### Connection Pooling

```
SENZA POOLING:                    CON PGBOUNCER:

  App (100 request)                App (100 request)
      │                                │
  100 connessioni                 ┌────▼──────┐
  dirette a PostgreSQL            │ PgBouncer │
      │                           │           │
  ┌───▼────────────┐              │ 100 client│
  │ PostgreSQL     │              │  → 20 DB  │
  │ max_conn = 100 │              │ connessioni│
  │ RAM: 100 × 10MB│              └────┬──────┘
  │ = 1 GB solo    │                   │
  │ per connessioni│              ┌────▼────────┐
  └────────────────┘              │ PostgreSQL  │
                                  │ max_conn=20 │
  Problema: PostgreSQL crea       │ RAM: 200 MB │
  un processo per connessione     └─────────────┘
  → 100 conn = 100 processi
  → memory/CPU sprecati           Modalità "transaction":
                                  la connessione DB è usata
                                  solo durante la transazione,
                                  poi restituita al pool
```

### Migration e Schema Evolution

Nel SaaS, il database evolve continuamente (nuove feature = nuove colonne/tabelle). Le migration devono essere:
- **Backward-compatible**: la vecchia versione dell'app funziona con il nuovo schema
- **Zero-downtime**: niente `ALTER TABLE` bloccanti su tabelle grandi
- **Reversibili**: ogni migration ha un rollback

Pattern: expand-and-contract. Fase 1: aggiungi nuova colonna. Fase 2: l'app scrive su entrambe. Fase 3: migra i dati. Fase 4: rimuovi la vecchia colonna.

#### Expand-and-Contract Step-by-Step

```
SCENARIO: rinominare la colonna "name" → "display_name" nella tabella users
(300 milioni di righe, zero downtime)

FASE 1 — EXPAND (deploy 1):
  ALTER TABLE users ADD COLUMN display_name TEXT;
  -- Non bloccante in PostgreSQL (aggiunge solo metadato)
  -- L'app vecchia ignora la nuova colonna → backward compatible

FASE 2 — DUAL WRITE (deploy 2):
  -- L'app scrive su ENTRAMBE le colonne
  INSERT INTO users (name, display_name, ...) VALUES ($1, $1, ...);
  UPDATE users SET name = $1, display_name = $1 WHERE id = $2;
  -- Le letture usano ancora "name"

FASE 3 — BACKFILL (job asincrono):
  -- Migrare i dati esistenti in batch
  UPDATE users SET display_name = name
  WHERE display_name IS NULL
  AND id BETWEEN $start AND $end;
  -- Batch di 10.000 righe con LIMIT per non bloccare il DB

FASE 4 — SWITCH READS (deploy 3):
  -- Le letture passano a "display_name"
  SELECT display_name FROM users WHERE id = $1;
  -- Le scritture continuano su entrambe (compatibilità rollback)

FASE 5 — CONTRACT (deploy 4, dopo conferma stabilità):
  -- Rimuovere la vecchia colonna
  ALTER TABLE users DROP COLUMN name;
  -- Rimuovere il dual write dal codice

Tempo totale: 2-4 settimane (non 2-4 ore!)
```

---

## Strategie di Caching

### Architettura Multi-Layer Cache

```
┌──────────────────────────────────────────────────────────────┐
│                    CACHE LAYERS                              │
│                                                              │
│  Layer 1: BROWSER CACHE                                      │
│  ├─ Cache-Control: max-age=31536000 (asset immutabili)       │
│  ├─ ETag / If-None-Match (contenuto dinamico)                │
│  └─ Service Worker (offline-first PWA)                       │
│                                                              │
│  Layer 2: CDN (CloudFront / Cloudflare)                      │
│  ├─ Edge caching per asset statici                           │
│  ├─ Dynamic content caching (API responses, con Vary header) │
│  └─ Cache invalidation via purge API                         │
│                                                              │
│  Layer 3: APPLICATION CACHE (Redis / Memcached)              │
│  ├─ Session store                                            │
│  ├─ Frequently read data (user profile, tenant config)       │
│  ├─ Computed results (dashboard aggregates)                  │
│  └─ Rate limiting counters                                   │
│                                                              │
│  Layer 4: DATABASE QUERY CACHE                               │
│  ├─ PostgreSQL shared_buffers                                │
│  ├─ Prepared statements                                      │
│  └─ Materialized views per aggregazioni complesse            │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Pattern di Caching con Redis

```
CACHE-ASIDE (Lazy Loading) — pattern più comune:

  1. App riceve richiesta
  2. Cerca in Redis: GET cache:tenant:{tenant_id}:user:{user_id}
  3. Cache HIT → ritorna il dato dalla cache
  4. Cache MISS → query al database → scrivi in cache con TTL → ritorna

  Pro: solo i dati richiesti vanno in cache, resiliente (DB come fallback)
  Contro: primo accesso sempre lento (cold start), dati potenzialmente stale

WRITE-THROUGH — scrivi in cache E database insieme:

  1. App scrive dato
  2. Scrive in Redis E in PostgreSQL (nella stessa operazione)
  3. Le letture successive trovano sempre la cache calda

  Pro: cache sempre aggiornata, nessun dato stale
  Contro: latenza di scrittura aumentata, cache piena di dati mai letti

WRITE-BEHIND (Write-Back) — scrivi in cache, database dopo:

  1. App scrive in Redis
  2. Un worker asincrono propaga a PostgreSQL
  3. Rischio: dati persi se Redis crasha prima della propagazione

  Pro: scritture velocissime
  Contro: rischio perdita dati, complessità di implementazione
  Uso: contatori, analytics, dati non critici
```

### Cache Invalidation Strategies

```
REGOLA D'ORO: "There are only two hard things in computer science:
cache invalidation and naming things." — Phil Karlton

STRATEGIA 1: TTL (Time To Live)
  SET cache:user:123 "{...}" EX 300   -- scade dopo 5 minuti
  Semplice ma i dati possono essere stale per TTL secondi

STRATEGIA 2: Event-Based Invalidation
  Quando un user viene modificato:
    DEL cache:user:123
  Il prossimo accesso fa cache miss → ricarica dal DB
  Preciso ma richiede che ogni write faccia invalidation

STRATEGIA 3: Versioned Keys
  SET cache:user:123:v7 "{...}"
  Quando i dati cambiano, incrementa versione → vecchia key scade via TTL
  Nessun DEL necessario, ma spreco di memoria temporaneo

STRATEGIA 4: Tag-Based Invalidation
  Tag "tenant:acme" → [cache:user:1, cache:user:2, cache:project:5]
  Invalidare tutti i dati di un tenant con un solo comando
  Utile per: tenant data purge, compliance GDPR

MULTI-TENANT CACHE NAMESPACE:
  Pattern: cache:{tenant_id}:{resource}:{id}
  Esempio: cache:acme:user:123
  Vantaggio: isolamento naturale, invalidation per-tenant facile
  CRITICO: MAI dimenticare il tenant_id nel key → data leak cross-tenant
```

### CDN Caching per SaaS

```
CONFIGURAZIONE CDN TIPICA:

  Asset immutabili (JS/CSS con hash nel filename):
    Cache-Control: public, max-age=31536000, immutable
    /static/app.a1b2c3d4.js → cached per 1 anno

  API responses pubbliche (pricing page, docs):
    Cache-Control: public, s-maxage=300, stale-while-revalidate=60
    Vary: Accept-Encoding
    → CDN cache 5 min, serve stale per 1 min durante revalidation

  API responses private (dati utente):
    Cache-Control: private, no-store
    → MAI cacheare in CDN (dati specifici per utente/tenant)

  Immagini uploadate dagli utenti:
    Cache-Control: public, max-age=86400
    → Cache 24 ore, invalidate via CDN purge API quando l'utente cambia foto
```

---

## Background Job Processing

### Architettura Asincrona

```
┌──────────────┐       ┌─────────────┐       ┌──────────────┐
│   API Server │──────►│   Message   │──────►│   Worker     │
│              │ push  │   Queue     │ pull  │   Process    │
│ "Richiesta   │       │             │       │              │
│  accettata"  │       │ ┌─────────┐ │       │ Elaborazione │
│  202 Accepted│       │ │ Job 1   │ │       │ effettiva    │
└──────────────┘       │ │ Job 2   │ │       └──────┬───────┘
                       │ │ Job 3   │ │              │
                       │ │ ...     │ │       ┌──────▼───────┐
                       │ └─────────┘ │       │  Result      │
                       └─────────────┘       │  Store       │
                                             │  (Redis/DB)  │
                                             └──────────────┘
```

### Tipologie di Job nel SaaS

```
JOB CRITICI (perdita = impatto diretto sul revenue):
  - Elaborazione pagamenti (Stripe webhook → conferma abbonamento)
  - Invio fatture
  - Provisioning tenant (creazione DB, schema, configurazione)
  → Coda persistente (RabbitMQ, SQS), retry aggressivo, dead letter queue

JOB IMPORTANTI (perdita = degrado esperienza):
  - Invio email transazionali (welcome, password reset)
  - Generazione report
  - Import/export dati CSV
  - Notifiche push
  → Coda persistente, retry moderato

JOB BEST-EFFORT (perdita = accettabile):
  - Aggiornamento search index
  - Calcolo analytics/aggregazioni
  - Pulizia file temporanei
  - Invio tracking events
  → Coda in-memory (Redis) accettabile, retry limitato

JOB SCHEDULATI (cron):
  - Rinnovo abbonamenti (ogni giorno alle 00:00 UTC)
  - Invio report settimanali (ogni lunedì alle 08:00)
  - Pulizia dati scaduti (ogni ora)
  - Backup incrementale (ogni 6 ore)
  - Health check third-party integrations (ogni 5 minuti)
  → Scheduler (cron job, cloud scheduler), idempotenza obbligatoria
```

### Dead Letter Queue (DLQ)

```
FLUSSO DI RETRY E DLQ:

  Job entra nella coda
       │
       ▼
  Worker prende il job
       │
  ┌────▼────┐
  │ Successo?│
  │         │
  │  SÌ ────┼──► Completato ✓
  │         │
  │  NO ────┼──► Retry? (max 5 tentativi)
  └─────────┘         │
                 ┌────▼────┐
                 │ Retry   │
                 │ < max?  │
                 │         │
                 │  SÌ ────┼──► Riaccodare con delay esponenziale
                 │         │    1min → 5min → 30min → 2h → 12h
                 │  NO ────┼──► Dead Letter Queue (DLQ)
                 └─────────┘         │
                                     ▼
                              ┌──────────────┐
                              │ DLQ          │
                              │              │
                              │ Alert team   │
                              │ Dashboard    │
                              │ Manual retry │
                              │ Investigation│
                              └──────────────┘

CRITICO: i job devono essere IDEMPOTENTI
  Eseguire lo stesso job 2 volte deve avere lo stesso risultato
  Esempio: addebitare un cliente → controllare se già addebitato prima di procedere
  Pattern: unique job ID + check "già processato?" prima di eseguire
```

### Confronto Message Queue

| Queue | Tipo | Persistenza | Throughput | Quando usare |
|---|---|---|---|---|
| Redis (BullMQ) | In-memory + AOF | Opzionale | Alto | Job leggeri, startup/PMF |
| RabbitMQ | Broker | Sì (disk) | Medio-alto | Routing complesso, exchange pattern |
| AWS SQS | Managed | Sì | Alto | AWS ecosystem, zero ops |
| Apache Kafka | Log distribuito | Sì | Molto alto | Event streaming, audit trail |
| NATS | Messaging | Opzionale | Molto alto | Microservizi, bassa latenza |

### Idempotenza dei Job

```python
# Pattern per job idempotente con idempotency key

async def process_payment(job_data):
    idempotency_key = job_data['idempotency_key']

    # Check se già processato
    existing = await db.query(
        "SELECT status FROM payment_jobs WHERE idempotency_key = $1",
        [idempotency_key]
    )

    if existing and existing.status == 'completed':
        return  # Già processato — noop

    if existing and existing.status == 'processing':
        return  # Un altro worker lo sta processando — noop

    # Marcare come "processing" (lock)
    await db.query(
        """INSERT INTO payment_jobs (idempotency_key, status, started_at)
           VALUES ($1, 'processing', now())
           ON CONFLICT (idempotency_key) DO NOTHING""",
        [idempotency_key]
    )

    try:
        # Logica di pagamento effettiva
        result = await stripe.charges.create(...)

        # Marcare come completato
        await db.query(
            "UPDATE payment_jobs SET status='completed', result=$2 WHERE idempotency_key=$1",
            [idempotency_key, json.dumps(result)]
        )
    except Exception as e:
        await db.query(
            "UPDATE payment_jobs SET status='failed', error=$2 WHERE idempotency_key=$1",
            [idempotency_key, str(e)]
        )
        raise  # Rilancia per trigger retry dalla coda
```

---

## Feature Flags e Rilascio Graduale

### Perché i Feature Flags

```
DEPLOY ≠ RELEASE

  Senza feature flags:
    Deploy = Release → tutto o niente, rischio alto

  Con feature flags:
    Deploy → codice in produzione ma SPENTO
    Release → attivazione graduale, controllata, reversibile

  Vantaggi:
    - Rollback istantaneo (spegni il flag, non fare rollback del deploy)
    - A/B testing nativo
    - Beta testing con clienti selezionati
    - Dark launching (testare con traffico reale senza esporre la feature)
    - Kill switch per feature problematiche
    - Trunk-based development (no long-lived feature branches)
```

### Tipologie di Feature Flags

```
1. RELEASE FLAG (temporaneo):
   Scopo: nascondere feature incomplete durante lo sviluppo
   Durata: giorni/settimane, rimuovere dopo il rollout completo
   Esempio: new_dashboard_enabled

2. EXPERIMENT FLAG (temporaneo):
   Scopo: A/B test per validare una variante
   Durata: settimane, rimuovere dopo la decisione
   Esempio: checkout_flow_variant (A/B/C)

3. OPS FLAG (permanente):
   Scopo: circuit breaker, graceful degradation
   Durata: permanente
   Esempio: enable_elasticsearch_search (fallback a DB se ES è down)

4. PERMISSION FLAG (permanente):
   Scopo: feature gating per piano/tier
   Durata: permanente
   Esempio: enable_advanced_analytics (solo piano Enterprise)

5. KILL SWITCH (permanente):
   Scopo: disabilitare feature in emergenza
   Durata: permanente
   Esempio: enable_file_upload (spegnere se storage è pieno)
```

### Rollout Graduale

```
ROLLOUT STRATEGY PER FEATURE RISCHIOSA:

  Giorno 1: 0% → Flag spento, codice deployato
  Giorno 2: 1% → Team interno (dogfooding)
  Giorno 3: 5% → Beta tester selezionati
  Giorno 5: 10% → Monitorare metriche (error rate, latenza, conversion)
  Giorno 7: 25% → Se metriche OK
  Giorno 10: 50% → Attenzione al load
  Giorno 14: 100% → Rollout completo

  CRITICA: ogni step deve avere metriche di successo/failure definite PRIMA
    - Error rate < 0.1% sul nuovo codice path
    - Latenza p95 < 300ms
    - Nessun aumento ticket di supporto
    - Conversion rate non peggiora (A/B test)

  Se una metrica degrada → rollback al % precedente → investigate
```

### Confronto Tool per Feature Flags

| Tool | Tipo | Costo | Pro | Contro |
|---|---|---|---|---|
| LaunchDarkly | SaaS | $$$$ | Best-in-class, SDK ricchi | Caro per startup |
| Unleash | Open source | Gratuito (self-host) | Flessibile, self-hosted | Ops da gestire |
| Flagsmith | Open source + SaaS | $ | Buon bilanciamento | Meno maturo |
| PostHog | Open source + SaaS | $$ | Feature flags + analytics | Più complesso |
| ConfigCat | SaaS | $ | Semplice, economico | Feature set limitato |
| Custom (DB/Redis) | Self-built | Gratuito | Nessuna dipendenza | Tech debt, niente UI |

### Lifecycle di un Feature Flag

```
REGOLA: ogni feature flag ha una DATA DI SCADENZA

  1. Creare il flag con owner e expiration date
  2. Implementare la feature con il flag
  3. Rollout graduale
  4. Rollout completo → flag = ON per tutti
  5. RIMUOVERE il flag dal codice (entro 2 settimane dal 100%)
  6. Rimuovere il dead code path (il ramo "OFF")

  ANTI-PATTERN: migliaia di flag attivi che nessuno sa se servono ancora
  → Tech debt, codice illeggibile, combinazioni imprevedibili
  → Regola: max 50 flag attivi in qualsiasi momento
  → Review mensile: ogni flag senza owner o scaduto → rimuovere
```

---

## CI/CD e DevOps per SaaS

### Pipeline CI/CD

```
Code Push → Build → Test → Deploy Staging → Test E2E → Deploy Production

DETTAGLIO:
  1. Developer push su branch feature
  2. CI automatico: lint + unit test + build
  3. Code review (PR)
  4. Merge su main → deploy automatico su staging
  5. Test E2E automatici su staging
  6. Deploy su production (blue-green o canary)
  7. Monitoring post-deploy (error rate, latency, business metrics)
  8. Rollback automatico se le metriche degradano
```

### Pipeline CI/CD Dettagliata

```
┌────────────────────────────────────────────────────────────────┐
│                    CI PIPELINE (ogni PR)                       │
│                                                                │
│  ┌──────┐  ┌────────┐  ┌──────┐  ┌──────────┐  ┌──────────┐  │
│  │ Lint │→ │ Build  │→ │ Unit │→ │Integrat. │→ │ Security │  │
│  │      │  │        │  │ Test │  │   Test   │  │   Scan   │  │
│  └──────┘  └────────┘  └──────┘  └──────────┘  └──────────┘  │
│                                                                │
│  Durata target: < 10 minuti                                    │
│  Parallelizzare: lint e build in parallelo, test dopo build    │
└────────────────────────────────┬───────────────────────────────┘
                                │ merge su main
                                ▼
┌────────────────────────────────────────────────────────────────┐
│                    CD PIPELINE (dopo merge)                    │
│                                                                │
│  ┌──────────┐  ┌────────┐  ┌──────┐  ┌──────────────────┐     │
│  │ Build    │→ │Deploy  │→ │ E2E  │→ │ Deploy Prod      │     │
│  │ Docker   │  │Staging │  │ Test │  │ (canary/blue-grn) │     │
│  │ Image    │  │        │  │      │  │                   │     │
│  └──────────┘  └────────┘  └──────┘  └────────┬──────────┘     │
│                                               │                │
│                                        ┌──────▼──────┐         │
│                                        │ Post-deploy │         │
│                                        │ monitoring  │         │
│                                        │ (15 min)    │         │
│                                        └─────────────┘         │
└────────────────────────────────────────────────────────────────┘
```

### GitOps per SaaS

```
GITOPS WORKFLOW:

  Repository applicazione:
    app-repo/
    ├── src/
    ├── Dockerfile
    └── .github/workflows/ci.yaml

  Repository infrastruttura:
    infra-repo/
    ├── kubernetes/
    │   ├── base/
    │   │   ├── deployment.yaml
    │   │   ├── service.yaml
    │   │   └── ingress.yaml
    │   ├── overlays/
    │   │   ├── staging/
    │   │   │   └── kustomization.yaml
    │   │   └── production/
    │   │       └── kustomization.yaml
    │   └── kustomization.yaml
    └── terraform/
        ├── modules/
        ├── staging/
        └── production/

  Flusso:
    1. Dev push su app-repo → CI build → Docker image tag v1.2.3
    2. CI aggiorna image tag in infra-repo (PR automatica)
    3. ArgoCD/Flux rileva il cambio → applica a Kubernetes
    4. La "source of truth" è sempre Git
```

### Infrastructure as Code (IaC)

Tutta l'infrastruttura definita in codice, versionata in Git:
- **Terraform**: provisioning cloud (server, database, networking)
- **Ansible/Chef/Puppet**: configurazione server
- **Docker + Kubernetes**: containerizzazione e orchestrazione
- **Helm**: package manager per Kubernetes

---

## Strategie di Deployment

### Blue-Green Deployment

**Blue-Green**: due ambienti identici. Il traffico è su Blue. Deploy su Green. Switch del load balancer. Se qualcosa non va, switch back. Zero downtime, rollback istantaneo.

```
PRIMA DEL DEPLOY:

  Load Balancer ───► Blue (v1.0) ← traffico attivo
                     Green (idle) ← ambiente pronto

DURANTE IL DEPLOY:

  Load Balancer ───► Blue (v1.0) ← traffico ancora qui
                     Green (v1.1) ← deploy nuova versione + smoke test

SWITCH:

  Load Balancer ───► Green (v1.1) ← traffico spostato
                     Blue (v1.0) ← standby per rollback

ROLLBACK (se necessario):

  Load Balancer ───► Blue (v1.0) ← rollback in secondi
                     Green (v1.1) ← investigare il problema

COSTO: 2x risorse (due ambienti identici sempre attivi)
VANTAGGIO: rollback in 10 secondi, zero downtime
```

### Canary Deployment

**Canary**: deploy graduale. 1% del traffico va alla nuova versione. Se le metriche sono ok, 10%, 25%, 50%, 100%. Rileva problemi prima che impattino tutti gli utenti.

```
CANARY PROGRESSIVO:

  Fase 1: 1% traffico → Canary (v1.1)
          99% traffico → Stable (v1.0)
          Monitorare: error rate, latency p99, CPU
          Durata: 15 minuti

  Fase 2: 10% → Canary
          90% → Stable
          Monitorare: + business metrics (conversion, revenue)
          Durata: 30 minuti

  Fase 3: 50% → Canary
          50% → Stable
          Durata: 1 ora

  Fase 4: 100% → Canary (diventa Stable)
          Rollback: rimuovere canary, il 100% torna a Stable

AUTOMATED CANARY ANALYSIS:
  Se error rate canary > 2× error rate stable → auto-rollback
  Se latency p99 canary > 1.5× stable → auto-rollback
  Se crash rate > 0 → auto-rollback immediato
  Tool: Flagger (Kubernetes), AWS AppMesh, Argo Rollouts
```

### Rolling Deployment

```
ROLLING UPDATE (Kubernetes default):

  Prima:  [Pod v1] [Pod v1] [Pod v1] [Pod v1]

  Step 1: [Pod v1] [Pod v1] [Pod v1] [Pod v2] ← nuovo pod creato
  Step 2: [Pod v1] [Pod v1] [Pod v2] [Pod v2] ← vecchio terminato, nuovo creato
  Step 3: [Pod v1] [Pod v2] [Pod v2] [Pod v2]
  Step 4: [Pod v2] [Pod v2] [Pod v2] [Pod v2] ← completato

  Configurazione Kubernetes:
    strategy:
      type: RollingUpdate
      rollingUpdate:
        maxUnavailable: 1    # max 1 pod down alla volta
        maxSurge: 1          # max 1 pod extra durante l'update

  Pro: nessun costo extra, zero downtime, graduale
  Contro: durante il rollout coesistono v1 e v2 (backward compatibility!)
  Rollback: kubectl rollout undo deployment/app
```

### Feature flag per il deploy

La feature è nel codice ma disattivata. Attivazione graduale per percentuale di utenti o per tenant specifici. Tool: LaunchDarkly, Unleash, Flagsmith.

### Matrice Comparativa Strategie di Deploy

| Strategia | Zero downtime | Rollback speed | Costo risorse | Complessità | Rischio |
|---|---|---|---|---|---|
| Blue-Green | Sì | Istantaneo (sec) | 2x | Medio | Basso |
| Canary | Sì | Veloce (min) | 1.1x | Alto | Molto basso |
| Rolling | Sì | Medio (min) | 1.25x | Basso | Medio |
| Recreate | No (downtime) | Lento | 1x | Molto basso | Alto |
| Feature Flag | Sì | Istantaneo | 1x | Medio | Basso |

---

## Infrastruttura Cloud

### Scelta del Cloud Provider

| Provider | Punto di forza | Quando scegliere |
|---|---|---|
| AWS | Servizi più ampi, marketplace | Default per la maggior parte dei SaaS |
| GCP | Data/ML, Kubernetes (GKE) | SaaS data-intensive, team Google-oriented |
| Azure | Enterprise, integrazione Microsoft | Target enterprise con ecosistema Microsoft |

### Architettura Cloud Tipica

```
Internet → CloudFront (CDN) → ALB (Load Balancer)
  → ECS/EKS (Container) → RDS (Database)
                         → ElastiCache (Redis)
                         → S3 (File storage)
                         → SQS (Queue)
                         → CloudWatch (Monitoring)
```

### Architettura Cloud Dettagliata Multi-Environment

```
┌──────────────────────────────────────────────────────────────┐
│                     PRODUCTION (AWS)                         │
│                                                              │
│  ┌────────────┐    ┌─────────────────────────────────┐       │
│  │ Route 53   │    │        VPC (10.0.0.0/16)        │       │
│  │ (DNS)      │    │                                 │       │
│  └──────┬─────┘    │  Public Subnets:                │       │
│         │          │  ┌──────────┐  ┌──────────┐     │       │
│  ┌──────▼─────┐    │  │ ALB      │  │ NAT GW   │     │       │
│  │ CloudFront │    │  │          │  │          │     │       │
│  │ (CDN)      │────│  └────┬─────┘  └──────────┘     │       │
│  └────────────┘    │       │                         │       │
│                    │  Private Subnets:                │       │
│                    │  ┌────▼─────┐  ┌──────────┐     │       │
│                    │  │ EKS      │  │ EKS      │     │       │
│                    │  │ Node AZ-a│  │ Node AZ-b│     │       │
│                    │  └────┬─────┘  └────┬─────┘     │       │
│                    │       │             │            │       │
│                    │  Data Subnets:                   │       │
│                    │  ┌────▼─────┐  ┌────▼─────┐     │       │
│                    │  │RDS Multi-│  │ElastiCache│     │       │
│                    │  │AZ Primary│  │ (Redis)  │     │       │
│                    │  │+ Standby │  │ Cluster  │     │       │
│                    │  └──────────┘  └──────────┘     │       │
│                    │                                 │       │
│                    └─────────────────────────────────┘       │
│                                                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────────┐          │
│  │ S3 Buckets │  │ SQS Queues │  │ Secrets Manager│          │
│  │ (storage)  │  │ (async)    │  │ (credentials)  │          │
│  └────────────┘  └────────────┘  └────────────────┘          │
└──────────────────────────────────────────────────────────────┘
```

### Costi Cloud

Il costo cloud è la voce più grande del COGS SaaS (15-30% del revenue per SaaS maturi). Ottimizzare:
- **Reserved Instances**: 30-60% di sconto per commit 1-3 anni
- **Spot Instances**: 60-90% di sconto per workload interrompibili (batch processing)
- **Right-sizing**: il 50% delle istanze cloud è sovradimensionato
- **Auto-scaling**: scalare dinamicamente con il traffico (meno risorse di notte/weekend)
- **Monitoring costi**: AWS Cost Explorer, CloudHealth, Vantage

### Cost Optimization Checklist

```
AUDIT MENSILE DEI COSTI CLOUD:

  □ Istanze inutilizzate o idle (CPU < 5% media)?
  □ Ambienti di staging/dev accesi 24/7? (spegnere di notte)
  □ Storage (S3, EBS) con lifecycle policy?
  □ Log retention troppo lunga? (90 giorni sono spesso sufficienti)
  □ Reserved Instances che coprono il baseline?
  □ Spot Instances per batch processing?
  □ NAT Gateway: traffico ottimizzato? (costo $0.045/GB!)
  □ Cross-AZ transfer ridotto al minimo?
  □ Container right-sized? (CPU/memory requests/limits)
  □ Database instance class corretta? (non t3.2xlarge per un DB da 10 GB)
```

---

## Pattern Infrastrutturali: Kubernetes, Serverless, PaaS

### Kubernetes per SaaS

```
ARCHITETTURA KUBERNETES PER SAAS:

  ┌──────────────────────────────────────────────┐
  │            KUBERNETES CLUSTER                │
  │                                              │
  │  Namespace: saas-platform                    │
  │  ┌──────────────────────────────────────┐    │
  │  │  Deployment: api-server              │    │
  │  │  Replicas: 3 (HPA: 3-20)            │    │
  │  │  Resources:                          │    │
  │  │    requests: {cpu: 500m, mem: 512Mi} │    │
  │  │    limits:   {cpu: 2,    mem: 2Gi}   │    │
  │  └──────────────────────────────────────┘    │
  │                                              │
  │  ┌──────────────────────────────────────┐    │
  │  │  Deployment: worker                  │    │
  │  │  Replicas: 2 (HPA: 2-10)            │    │
  │  │  Anti-affinity: non stesso node      │    │
  │  └──────────────────────────────────────┘    │
  │                                              │
  │  ┌──────────────────────────────────────┐    │
  │  │  CronJob: daily-billing              │    │
  │  │  Schedule: "0 0 * * *"               │    │
  │  │  concurrencyPolicy: Forbid           │    │
  │  └──────────────────────────────────────┘    │
  │                                              │
  │  ┌──────────────────────────────────────┐    │
  │  │  Ingress: nginx-ingress              │    │
  │  │  TLS: cert-manager (Let's Encrypt)   │    │
  │  │  Rate limit: per-IP, per-tenant      │    │
  │  └──────────────────────────────────────┘    │
  │                                              │
  │  Namespace: monitoring                       │
  │  ┌──────────────────────────────────────┐    │
  │  │  Prometheus + Grafana + Loki         │    │
  │  └──────────────────────────────────────┘    │
  └──────────────────────────────────────────────┘
```

### Serverless per SaaS

```
ARCHITETTURA SERVERLESS (AWS Lambda + API Gateway):

  API Gateway
       │
  ┌────▼──────────────────────────────────────┐
  │  Lambda Functions                         │
  │                                           │
  │  /api/v1/projects → projects-handler      │
  │  /api/v1/users → users-handler            │
  │  /api/v1/billing → billing-handler        │
  │                                           │
  │  Ogni funzione:                           │
  │    - Cold start: 100-500ms (JIT)          │
  │    - Max durata: 15 minuti                │
  │    - Max memoria: 10 GB                   │
  │    - Pricing: pay-per-invocation          │
  └───────────────┬───────────────────────────┘
                  │
  ┌───────────────▼───────────────────────────┐
  │  Managed Services                         │
  │                                           │
  │  DynamoDB (database, pay-per-request)     │
  │  S3 (file storage)                        │
  │  SQS (queues)                             │
  │  EventBridge (event routing)              │
  │  Cognito (auth)                           │
  └───────────────────────────────────────────┘
```

### Matrice Decisionale: Kubernetes vs Serverless vs PaaS

| Criterio | Kubernetes | Serverless | PaaS (Heroku/Railway) |
|---|---|---|---|
| Costo a basso traffico | Alto (cluster always-on) | Molto basso (pay-per-use) | Medio |
| Costo ad alto traffico | Ottimizzato | Potenzialmente alto | Alto |
| Complessità ops | Alta | Bassa | Molto bassa |
| Cold start | No | Sì (100-500ms) | No |
| Scaling | Configurabile | Automatico | Automatico (limitato) |
| Vendor lock-in | Basso | Alto | Medio |
| Team size minimo | 2-3 DevOps | 0 (dev-driven) | 0 (dev-driven) |
| Controllo | Totale | Limitato | Limitato |
| Long-running jobs | Sì | Max 15 min (Lambda) | Sì |
| WebSocket | Sì | Complesso | Sì |
| Ideale per | Scale/Enterprise | Startup/PMF, burst | Startup/PMF, MVP |

```
REGOLA PRATICA:

  Pre-PMF, team < 5: PaaS (Heroku, Railway, Render)
    → Zero ops, focus sul prodotto
    → Migrare quando il costo PaaS > 3× il costo Kubernetes

  PMF confermato, team 5-15: Serverless o Kubernetes managed (EKS/GKE)
    → Serverless se il workload è event-driven e bursty
    → Kubernetes se ci sono long-running jobs e WebSocket

  Scale, team 15+: Kubernetes (EKS/GKE) con team DevOps
    → Costo ottimizzato, controllo totale
    → Service mesh per comunicazione inter-servizio
```

---

## Observability: Logging, Metriche, Tracing

### I Tre Pilastri dell'Observability

```
┌──────────────────────────────────────────────────────────────┐
│                     OBSERVABILITY                            │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   LOGGING    │  │   METRICS    │  │   TRACING    │       │
│  │              │  │              │  │              │       │
│  │ "Cosa è      │  │ "Com'è il    │  │ "Dove è il   │       │
│  │  successo?"  │  │  sistema?"   │  │  bottleneck?"│       │
│  │              │  │              │  │              │       │
│  │ ELK, Loki,  │  │ Prometheus,  │  │ Jaeger,      │       │
│  │ CloudWatch  │  │ Datadog,     │  │ Tempo,       │       │
│  │ Logs        │  │ Grafana      │  │ Zipkin       │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│                                                              │
│  CORRELAZIONE: un request_id lega log, metriche e trace     │
│  dello stesso evento attraverso tutti i servizi              │
└──────────────────────────────────────────────────────────────┘
```

### Structured Logging

```json
// MAI fare questo:
// console.log("User login failed for " + email);

// SEMPRE structured logging:
{
  "timestamp": "2026-05-22T14:30:00.123Z",
  "level": "warn",
  "message": "User login failed",
  "service": "auth-service",
  "request_id": "req_abc123",
  "tenant_id": "tenant_xyz",
  "user_email_hash": "sha256:a1b2c3...",
  "ip": "203.0.113.42",
  "failure_reason": "invalid_password",
  "attempt_count": 3,
  "environment": "production"
}

// REGOLE:
// 1. MAI loggare password, token, API key, PII in chiaro
// 2. SEMPRE includere: timestamp, level, request_id, tenant_id
// 3. Usare log level corretto:
//    ERROR: qualcosa è rotto, azione necessaria
//    WARN: qualcosa di anomalo, potrebbe diventare un problema
//    INFO: eventi di business significativi (login, purchase, signup)
//    DEBUG: dettagli tecnici (solo in staging, MAI in prod di default)
```

### Metriche: RED e USE

```
METODO RED (per servizi request-driven):

  R — Rate:     request/secondo per servizio
  E — Errors:   % di request con errore (4xx, 5xx)
  D — Duration: latenza (p50, p95, p99)

  Dashboard esempio:
  ┌─────────────────────────────────────────┐
  │ API Server — ultimi 30 minuti          │
  │                                         │
  │ Rate:     450 req/sec  [████████░░]     │
  │ Errors:   0.3%         [█░░░░░░░░░]     │
  │ p50:      12ms         [█░░░░░░░░░]     │
  │ p95:      45ms         [██░░░░░░░░]     │
  │ p99:      210ms        [████░░░░░░]     │
  └─────────────────────────────────────────┘

METODO USE (per risorse infrastrutturali):

  U — Utilization: % di utilizzo (CPU, RAM, disco, connessioni DB)
  S — Saturation:  lavoro in coda (queue depth, thread pool exhaustion)
  E — Errors:      errori di risorsa (disk I/O error, OOM kill)

  Alert thresholds:
    CPU > 80% per 5 min → WARNING
    CPU > 95% per 2 min → CRITICAL
    Memory > 85% → WARNING
    Disk > 90% → CRITICAL
    DB connections > 80% pool → WARNING
    Queue depth > 10.000 → WARNING
```

### Distributed Tracing

```
TRACE DI UNA RICHIESTA ATTRAVERSO MICROSERVIZI:

  Trace ID: trace_abc123
  ┌──────────────────────────────────────────────────────────┐
  │                                                          │
  │ [API Gateway]        ████████████████████████  200ms     │
  │   [Auth Service]       ████                    15ms      │
  │   [Project Service]         ████████████████   120ms     │
  │     [DB Query]                ██████           45ms      │
  │     [Cache Lookup]            █                3ms       │
  │     [Billing Check]              ████████      60ms      │
  │       [Stripe API]                ██████       40ms      │
  │   [Audit Logger]                        ████   12ms      │
  │                                                          │
  └──────────────────────────────────────────────────────────┘

  Il trace mostra che:
  - Il bottleneck è nel Billing Check (60ms) → Stripe API (40ms)
  - La DB query impiega 45ms → possibile ottimizzazione indice
  - Cache HIT per 3ms → il caching funziona

  Implementazione: OpenTelemetry SDK → Jaeger/Tempo/Datadog
  Ogni servizio propaga il trace_id via header:
    traceparent: 00-trace_abc123-span_def456-01
```

### Alerting Strategy

```
SEVERITY LEVELS PER ALERT:

  P1 — CRITICAL (pagina on-call, risposta in 5 min):
    - Servizio completamente down (health check failure)
    - Error rate > 10% (di solito < 0.5%)
    - Database non raggiungibile
    - SSL certificato scaduto
    - Data breach detection

  P2 — HIGH (notifica Slack, risposta in 30 min):
    - Error rate > 2%
    - Latenza p99 > 2 secondi (di solito < 200ms)
    - CPU > 90% per 10 minuti
    - Queue depth in crescita continua
    - Disk space > 85%

  P3 — MEDIUM (ticket, risposta entro business hours):
    - Error rate > 0.5%
    - Background job failure rate > 5%
    - Certificate scade tra 14 giorni
    - Reserved Instances in scadenza

  P4 — LOW (review settimanale):
    - Cost anomaly (spesa > 120% della media)
    - Deprecation warning da provider esterni
    - Dependency vulnerability (non exploitable)

  ANTI-PATTERN: troppi alert → alert fatigue → alert ignorati → outage
  REGOLA: ogni alert deve essere actionable. Se non c'è un'azione da fare,
  non è un alert — è una metrica da osservare in dashboard.
```

### Confronto Stack Observability

| Componente | Open Source | SaaS | Quando scegliere |
|---|---|---|---|
| Metriche | Prometheus + Grafana | Datadog, New Relic | OSS se team DevOps dedicato |
| Log | Loki, ELK Stack | Datadog Logs, Papertrail | Loki è più leggero di ELK |
| Tracing | Jaeger, Tempo | Datadog APM, Honeycomb | Jaeger se già Kubernetes |
| Alerting | Alertmanager | PagerDuty, Opsgenie | PagerDuty per on-call serio |
| Uptime | Blackbox Exporter | Better Uptime, Pingdom | SaaS per status page pubblica |

---

## Alta Disponibilità e Disaster Recovery

### SLA e Uptime

| SLA | Downtime/anno | Downtime/mese |
|---|---|---|
| 99% | 3.65 giorni | 7.3 ore |
| 99.9% | 8.7 ore | 43.8 min |
| 99.95% | 4.4 ore | 21.9 min |
| 99.99% | 52.6 min | 4.4 min |

Il 99.9% è lo standard per SaaS B2B. Il 99.99% è necessario per infrastruttura critica.

### Pattern HA

- **Multi-AZ**: risorse distribuite su più Availability Zone nella stessa regione. Protegge da failure di un datacenter.
- **Multi-region**: risorse in più regioni geografiche. Protegge da failure di un'intera regione. Necessario per SLA 99.99% e compliance (data residency).
- **Database HA**: primary + standby con failover automatico. RDS Multi-AZ, Aurora Global Database.
- **Circuit breaker**: se un servizio downstream è down, il circuit breaker interrompe le chiamate e restituisce una risposta di fallback. Previene cascading failure.

### Circuit Breaker Pattern

```
STATI DEL CIRCUIT BREAKER:

  CLOSED (normale):
    Tutte le chiamate passano al servizio downstream
    Contatore failure attivo
        │
        │ failure_count > threshold (es. 5 in 30 sec)
        ▼
  OPEN (protezione attiva):
    Tutte le chiamate → risposta di fallback immediata
    Nessuna chiamata al servizio downstream
    Timer attivo
        │
        │ dopo timeout (es. 30 secondi)
        ▼
  HALF-OPEN (test):
    UNA chiamata passa al servizio
        │
        ├─ successo → torna a CLOSED
        │
        └─ failure → torna a OPEN

  IMPLEMENTAZIONE:
    // Pseudo-codice
    if circuit.state == OPEN:
        return fallback_response()

    try:
        response = call_downstream_service()
        circuit.record_success()
        return response
    except TimeoutError:
        circuit.record_failure()
        if circuit.failure_count > threshold:
            circuit.trip()  // → OPEN
        return fallback_response()
```

### Disaster Recovery

**RPO** (Recovery Point Objective): quanti dati posso permettermi di perdere? (ultimo backup)
**RTO** (Recovery Time Objective): quanto tempo per tornare operativi?

| Strategia | RPO | RTO | Costo |
|---|---|---|---|
| Backup & Restore | Ore | Ore | Basso |
| Pilot Light | Minuti | 30-60 min | Medio |
| Warm Standby | Secondi | Minuti | Alto |
| Multi-site Active | Zero | Zero | Molto alto |

Per la maggior parte dei SaaS: backup automatici ogni ora + warm standby cross-region per il database + infrastruttura IaC (ricostruibile in minuti).

### Disaster Recovery Runbook Template

```
RUNBOOK: Database Failover

  TRIGGER: RDS primary non risponde per > 5 minuti
  SEVERITY: P1
  ON-CALL: Database team lead

  STEPS:
  1. Verificare che il problema è confermato
     → Dashboard: RDS metrics, connection errors
     → AWS Console: RDS instance status
     → Eseguire: pg_isready -h primary-db.internal

  2. Se confermato, iniziare failover:
     → RDS Multi-AZ: failover automatico (2-5 minuti)
     → Aurora: failover automatico (< 30 secondi)
     → Self-managed: promuovere standby manualmente
        pg_ctl promote -D /var/lib/postgresql/data

  3. Aggiornare DNS interno:
     → primary-db.internal → nuovo IP
     → O: usare RDS endpoint (automatico con Multi-AZ)

  4. Verificare applicazione:
     → Health check passa?
     → API risponde? Test: curl https://api.example.com/health
     → Error rate tornato normale?

  5. Comunicare:
     → Slack: #incidents — "DB failover completato"
     → Status page: "Investigating" → "Resolved"
     → Post-mortem entro 48 ore

  6. Post-failover:
     → Creare nuovo standby
     → Verificare backup recente
     → Controllare replication lag
```

### Chaos Engineering

```
PRINCIPI DEL CHAOS ENGINEERING PER SAAS:

  "Introdurre guasti controllati in produzione per scoprire
   debolezze PRIMA che causino outage reali."

  Esperimenti da eseguire periodicamente:

  1. Terminare un'istanza API random
     → Il load balancer la rimuove? Nuova istanza creata?
     → Target: recovery < 60 secondi

  2. Bloccare connessione al database per 30 secondi
     → L'app gestisce il timeout? Circuit breaker scatta?
     → Gli utenti vedono un errore graceful o un crash?

  3. Aumentare latenza di un servizio downstream di 5 secondi
     → Timeout configurati? La richiesta non blocca indefinitamente?
     → Le code si riempiono? Queue back-pressure funziona?

  4. Riempire il disco al 95%
     → Alert scatta? Log rotation funziona?
     → L'app gestisce ENOSPC senza corrompere dati?

  5. Revocare le credenziali di un secret
     → L'app mostra un errore chiaro? Non logga il secret?
     → Il secret rotation funziona senza downtime?

  Tool: Chaos Monkey (Netflix), Litmus (Kubernetes), Gremlin (SaaS)
  ATTENZIONE: solo in ambienti con osservabilità matura e rollback testato
```

---

## Anti-Pattern e Errori Comuni

### 1. Monolith-to-Microservices Big Bang Rewrite

```
ERRORE: "Riscriviamo tutto in microservizi in 6 mesi"
CONSEGUENZA: il progetto dura 18 mesi, il monolite va comunque mantenuto,
  i microservizi sono fragili, il team è esausto.
SOLUZIONE: Strangler Fig Pattern — estrarre un servizio alla volta,
  iniziando dal più indipendente.
```

### 2. Dimenticare il tenant_id nelle Query

```
ERRORE: SELECT * FROM invoices WHERE status = 'overdue';
CONSEGUENZA: espone fatture di TUTTI i tenant → data breach.
SOLUZIONE: RLS in PostgreSQL + test automatici che verificano
  che ogni query includa il filtro tenant.
```

### 3. Shared Mutable State nei Servizi

```
ERRORE: variabili globali, cache in-memory non invalidata, sessioni in RAM.
CONSEGUENZA: inconsistenza tra istanze, bug visibili solo sotto carico.
SOLUZIONE: stato in store esterno (Redis per sessioni, S3 per file),
  servizi stateless.
```

### 4. Over-Engineering Prematuro

```
ERRORE: Kubernetes + Service Mesh + Event Sourcing + CQRS per un MVP
  con 10 utenti.
CONSEGUENZA: 80% del tempo su infrastruttura, 20% sul prodotto.
  Il prodotto fallisce perché non raggiunge il PMF in tempo.
SOLUZIONE: Heroku/Railway + PostgreSQL + monolite.
  Migrare quando la complessità è NECESSARIA, non anticipata.
```

### 5. Ignorare il Noisy Neighbor Problem

```
ERRORE: nessun rate limiting per tenant, nessun resource quota.
CONSEGUENZA: un tenant con un cron job impazzito rallenta tutti gli altri.
  100% dei tenant subiscono la degradation per colpa di 1.
SOLUZIONE: rate limiting per tenant (API + DB), resource quotas,
  monitoring per-tenant, isolamento per tenant enterprise.
```

### 6. Backup Non Testato

```
ERRORE: "Abbiamo backup automatici" → mai testato il restore.
CONSEGUENZA: durante il disaster, il backup è corrotto / incompleto /
  incompatibile con la versione corrente dell'app.
SOLUZIONE: restore test mensile su ambiente isolato.
  Automazione: script che fa restore + smoke test + report.
```

### 7. Secret nel Codice Sorgente

```
ERRORE: API_KEY = "sk_live_abc123..." nel codice versionato in Git.
CONSEGUENZA: chiunque con accesso al repo ha le credenziali.
  Anche dopo la rimozione, il secret è nella Git history.
SOLUZIONE: .env (non versionato) + .env.example (versionato con placeholder),
  secret manager (AWS Secrets Manager, Vault), git-secrets hook pre-commit.
  Se esposto: ruotare IMMEDIATAMENTE.
```

### 8. Zero-Downtime Migration Ignorata

```
ERRORE: ALTER TABLE users ADD COLUMN phone TEXT NOT NULL;
  su una tabella con 50M righe in produzione.
CONSEGUENZA: lock sulla tabella per minuti, tutte le query bloccate,
  timeout, utenti impattati.
SOLUZIONE: expand-and-contract pattern (vedi sezione Database).
  ALTER TABLE ... ADD COLUMN ... senza NOT NULL (non bloccante in PostgreSQL),
  backfill asincrono, poi ADD CONSTRAINT dopo.
```

### 9. Logging Eccessivo o Insufficiente

```
ERRORE 1: loggare ogni request in dettaglio → costi di storage esplodono,
  i log importanti sono sommersi dal rumore.
ERRORE 2: non loggare nulla → durante un incident, nessuna informazione
  per il debug.
SOLUZIONE: log strutturati con livelli (ERROR/WARN/INFO/DEBUG),
  sampling per request ad alto volume (1 su 100),
  log retention policy (30 giorni hot, 90 giorni cold, 1 anno archive).
```

### 10. Feature Flags Mai Rimossi

```
ERRORE: 500 feature flags attivi, nessuno sa quali servono ancora.
CONSEGUENZA: codice illeggibile con if/else nested, combinazioni
  imprevedibili, testing impossibile (2^500 combinazioni).
SOLUZIONE: ogni flag ha owner + expiration date + tag di tipo
  (release/experiment/ops/permission).
  Review mensile: flag scaduti → rimuovere, flag senza owner → rimuovere.
  Max 50 flag attivi contemporaneamente.
```

### 11. Single Point of Failure Nascosto

```
ERRORE: il sistema è "HA" ma c'è un singolo servizio critico
  senza ridondanza (es. un cron job che gira su un solo server).
CONSEGUENZA: quel server va down → niente billing → niente revenue.
SOLUZIONE: audit di tutti i componenti, ogni componente critico
  deve avere almeno 2 istanze + health check + failover.
  Leader election per i cron job (solo un'istanza esegue, le altre sono standby).
```

---

## Best Practices

1. **Iniziare con il monolite**: non partire con microservizi. Modular monolith è il miglior punto di partenza per il 95% dei SaaS
2. **Row Level Security**: in PostgreSQL, usare RLS per garantire l'isolamento tenant a livello di database, non solo di applicazione
3. **Infrastructure as Code**: mai configurare manualmente. Tutto in Terraform/Pulumi, versionato in Git
4. **Feature flag per il deploy**: separare il deploy dalla release. Deployare codice spento, attivare gradualmente
5. **Monitor everything**: non puoi ottimizzare ciò che non misuri. APM (Datadog, New Relic), log aggregation (ELK, Loki), uptime monitoring (Pingdom, Better Uptime)
6. **Database backup testato**: un backup non testato non è un backup. Restore mensile su ambiente di test
7. **Ottimizzare i costi cloud dal giorno 1**: reserved instances, right-sizing, auto-scaling. Il cloud è economico solo se gestito bene
8. **Implementare observability fin dall'inizio**: structured logging + metriche + tracing. Non aspettare il primo outage per instrumentare il codice
9. **Design for failure**: ogni componente esterno FALLIRA'. Circuit breaker, retry con backoff, graceful degradation, fallback responses
10. **Automatizzare il disaster recovery**: runbook documentati, failover testato, chaos engineering periodico. Un piano DR non testato è solo un documento
11. **Rate limiting come cittadino di prima classe**: non aggiungerlo dopo il primo abuso. Implementarlo per tenant, per utente, per endpoint fin dal primo giorno
12. **Immutabilità e statelessness**: servizi senza stato in memoria, configurazione immutabile (container image = l'unico artefatto deployato), nessun snowflake server

---

## Troubleshooting

### Scenario 1: Applicazione Lenta Sotto Carico

**Sintomi**: latenza API sale da 50ms a 2+ secondi durante le ore di punta.

**Diagnosi**: identificare il collo di bottiglia: database (query lente? indici mancanti?), applicazione (CPU-bound? memory leak?), rete (latenza inter-servizio?). Strumenti: APM per trovare le richieste lente, EXPLAIN ANALYZE per le query, load testing (k6, Locust) per riprodurre il problema.

```
PLAYBOOK:
  1. Dashboard APM → quale servizio ha la latenza più alta?
  2. Se database:
     → pg_stat_activity: query attive/bloccate?
     → pg_stat_statements: top 10 query per tempo totale
     → EXPLAIN ANALYZE sulle query lente → indice mancante?
  3. Se applicazione:
     → CPU profiling (flamegraph)
     → Memory profiling → leak?
     → Thread pool exhaustion → connection pool pieno?
  4. Se rete:
     → DNS resolution lenta?
     → Latenza inter-AZ? (2-5ms in più per cross-AZ)
     → TLS handshake ripetuti (keep-alive non configurato)?
```

### Scenario 2: Noisy Neighbor

**Sintomi**: un tenant pesante rallenta tutti gli altri.

**Diagnosi e soluzione**: noisy neighbor problem. Soluzioni: rate limiting per tenant, queue prioritizzata, resource quotas, isolamento per tenant enterprise (dedicated infra). A lungo termine: sharding o database separato per tenant grandi.

```
PLAYBOOK:
  1. Identificare il tenant: query per-tenant metrics
     SELECT tenant_id, COUNT(*), AVG(duration_ms)
     FROM request_logs
     WHERE timestamp > now() - interval '1 hour'
     GROUP BY tenant_id
     ORDER BY COUNT(*) DESC LIMIT 10;
  2. Azione immediata: rate limit temporaneo sul tenant
  3. Azione medio termine: implementare resource quotas per piano
  4. Azione lungo termine: spostare il tenant su infra dedicata
     o implementare sharding
```

### Scenario 3: Deploy Causa Bug in Produzione

**Sintomi**: error rate spike subito dopo un deploy.

**Diagnosi e soluzione**: se si usa canary deploy, il rollback è automatico. Altrimenti: blue-green switch back. Per il futuro: implementare canary + feature flag + automated rollback basato su metriche (error rate spike → rollback).

```
PLAYBOOK:
  1. Confermare: error rate post-deploy > 2× pre-deploy?
  2. Rollback immediato:
     - Blue-green: switch al vecchio ambiente (10 secondi)
     - Canary: rimuovere canary pods (30 secondi)
     - Rolling: kubectl rollout undo deployment/app (2 minuti)
     - Feature flag: spegnere il flag (istantaneo)
  3. Stabilizzare: verificare che error rate torna a baseline
  4. Investigare: diff del deploy, log del periodo anomalo
  5. Fix: correggere il bug, aggiungere test, re-deploy con canary
```

### Scenario 4: Costi Cloud Fuori Controllo

**Sintomi**: la fattura cloud è 3x il mese precedente senza crescita proporzionale del traffico.

**Diagnosi e soluzione**: audit immediato: istanze sovradimensionate? Log/storage non necessario? Ambienti di staging dimenticati accesi? Azioni: reserved instances per il baseline, spot per batch, auto-scaling, tag-based cost allocation per team/servizio.

```
PLAYBOOK:
  1. AWS Cost Explorer: breakdown per servizio, per tag, per account
  2. Top offenders tipici:
     - NAT Gateway: traffico cross-AZ non necessario
     - EBS volumes orfani (non attaccati a nessuna istanza)
     - S3: lifecycle policy mancante, log mai eliminati
     - RDS: istanze dev accese 24/7
     - ECR: immagini Docker mai eliminate
  3. Azioni immediate:
     - Spegnere ambienti non-prod fuori orario
     - Eliminare risorse orfane (EBS, EIP, snapshot vecchi)
  4. Azioni medio termine:
     - Reserved Instances per baseline stabile
     - Spot per batch/worker
     - Auto-scaling corretto (min/max, schedule-based)
```

### Scenario 5: Memory Leak in Produzione

```
SINTOMI: la memoria dell'applicazione cresce lentamente nel tempo,
  fino a OOM kill dopo 24-48 ore. I restart risolvono temporaneamente.

PLAYBOOK:
  1. Confermare il pattern: grafico memoria su 7 giorni → crescita lineare?
  2. Heap dump: catturare un heap dump quando la memoria è alta
     Node.js: --inspect + Chrome DevTools / clinic.js
     JVM: jmap -dump:format=b,file=heap.hprof PID
     Python: tracemalloc + memory_profiler
  3. Analizzare il heap dump:
     - Oggetti che crescono nel tempo?
     - Event listener mai rimossi?
     - Cache senza eviction policy?
     - Connection pool che non rilascia connessioni?
  4. Fix comuni:
     - Aggiungere TTL/LRU alla cache in-memory
     - Chiudere le connessioni DB/HTTP nel finally/defer
     - Rimuovere event listener nel cleanup
     - WeakRef per riferimenti temporanei
  5. Preventivo: alert su memory > 80%, auto-restart se > 90%
```

### Scenario 6: Connection Pool Exhaustion

```
SINTOMI: "Cannot acquire connection from pool" error, l'applicazione
  smette di rispondere mentre il database è idle.

PLAYBOOK:
  1. Verificare: pg_stat_activity → quante connessioni attive?
     SELECT state, COUNT(*) FROM pg_stat_activity GROUP BY state;
  2. Se troppe connessioni "idle in transaction":
     → Qualche query non fa COMMIT/ROLLBACK
     → Transaction leak: il codice non chiude la transazione in caso di errore
  3. Se troppe connessioni "active":
     → Query lente che occupano connessioni troppo a lungo
     → Controllare con pg_stat_statements
  4. Fix:
     - PgBouncer con idle_transaction_timeout = 30s
     - Pool size = (core_count * 2) + effective_spindle_count
       (formula HikariCP, tipicamente 10-20 per nodo app)
     - Statement timeout: SET statement_timeout = '30s';
     - Nel codice: SEMPRE try/finally per rilasciare la connessione
```

### Scenario 7: Certificato SSL Scaduto

```
SINTOMI: tutti gli utenti vedono ERR_CERT_DATE_INVALID,
  l'applicazione sembra funzionare ma nessuno può accedere.

PLAYBOOK:
  1. Verificare: openssl s_client -connect api.example.com:443
     → "verify error:num=10:certificate has expired"
  2. Fix immediato:
     - cert-manager (Kubernetes): kubectl describe certificate
       → verificare che l'issuer è configurato e funzionante
     - ACM (AWS): i certificati ACM si rinnovano automaticamente
       SE il DNS validation record esiste ancora
     - Manual: rinnovare il certificato e applicare al load balancer
  3. Preventivo:
     - Alert quando il certificato scade tra 30 giorni
     - Alert CRITICAL quando scade tra 7 giorni
     - Usare cert-manager o ACM per rinnovo automatico
     - MAI gestire certificati manualmente in produzione
```

### Scenario 8: Split Brain nel Database

```
SINTOMI: dopo un failover, entrambi i nodi DB pensano di essere il primary.
  Dati scritti su entrambi, divergenza irreversibile.

PLAYBOOK:
  1. STOP immediato: spegnere uno dei due nodi (il vecchio primary)
  2. Verificare quale nodo ha i dati più recenti
  3. I dati scritti sul nodo "sbagliato" devono essere recuperati
     manualmente e riconciliati
  4. Ripristinare la replicazione con un solo primary
  5. Post-mortem: perché il fencing (STONITH) non ha funzionato?
  6. Preventivo:
     - Fencing mechanism testato (STONITH: Shoot The Other Node In The Head)
     - Consensus-based failover (Patroni per PostgreSQL)
     - Quorum: almeno 3 nodi per evitare split brain
```

### Scenario 9: Migration Lenta su Tabella Grande

```
SINTOMI: ALTER TABLE con 200M righe bloccata da 45 minuti,
  tutte le query sulla tabella in coda.

PLAYBOOK:
  1. Se possibile, annullare la migration (pg_cancel_backend)
  2. NON fare ALTER TABLE che richiede rewrite su tabelle grandi:
     - ADD COLUMN con DEFAULT: OK in PostgreSQL 11+ (solo metadato)
     - ADD COLUMN NOT NULL: BLOCCANTE → usare expand-and-contract
     - ALTER COLUMN TYPE: BLOCCANTE → creare nuova colonna
     - CREATE INDEX: BLOCCANTE → usare CREATE INDEX CONCURRENTLY
  3. Per il futuro:
     - Testare la migration su un clone del database di produzione
     - Usare pg_repack per operazioni che richiedono rewrite
     - Dividere migration grandi in step piccoli
     - Schedule migration durante le ore di minor traffico
```

### Scenario 10: Tenant Data Corruption

```
SINTOMI: un tenant riporta dati mancanti o inconsistenti.
  Il bug ha corrotto dati per un periodo di tempo.

PLAYBOOK:
  1. Isolare: il problema riguarda solo questo tenant o tutti?
  2. Timeline: quando è iniziata la corruzione?
     → Deploy log, change log, audit trail
  3. Quantificare: quanti record sono corrotti?
     → Query di validazione sui dati del tenant
  4. Recovery:
     a. Se backup point-in-time disponibile:
        → Restore del backup in un DB temporaneo
        → Estrarre i dati corretti del tenant
        → Applicare selettivamente al DB di produzione
     b. Se audit trail disponibile:
        → Ricostruire lo stato corretto dagli eventi
     c. Se nessuno dei precedenti:
        → Lavorare con il cliente per identificare i dati persi
  5. Fix: correggere il bug, aggiungere data validation,
     aggiungere constraint DB, test di integrità automatici
```

### Scenario 11: Third-Party API Down

```
SINTOMI: Stripe/Twilio/SendGrid non risponde, feature dipendenti bloccate.

PLAYBOOK:
  1. Circuit breaker: dovrebbe scattare automaticamente
     → Se non scatta: il timeout è troppo alto, ridurlo
  2. Fallback:
     - Email: accodare per invio successivo
     - Pagamenti: marcare come "pending", retry quando torna
     - SMS: fallback a email
  3. Status page del provider: confermare l'outage
  4. Comunicare agli utenti: "funzionalità X temporaneamente degradata"
  5. NON fare:
     - Retry aggressivo (peggiora il problema del provider)
     - Crash dell'intera applicazione per un singolo provider down
  6. Post-mortem: il circuit breaker ha funzionato?
     Il fallback era implementato? Migliorare per la prossima volta.
```

### Scenario 12: Webhook Delivery Failure

```
SINTOMI: i clienti non ricevono i webhook. I loro sistemi non processano
  gli eventi dal SaaS.

PLAYBOOK:
  1. Dashboard delivery: controllare lo status delle delivery recenti
  2. Cause comuni:
     - Il cliente ha cambiato URL senza aggiornare la configurazione
     - Il firewall del cliente blocca le richieste
     - Il certificato SSL del cliente è scaduto
     - Il server del cliente restituisce 500
     - Il payload è troppo grande (> 1 MB)
  3. Debug:
     - Controllare i retry: quanti tentativi fatti? Quale errore?
     - Verificare il URL: curl -X POST <webhook_url> -d '{"test": true}'
  4. Per il cliente: fornire un webhook test endpoint nella dashboard
     + log delle delivery con response body/status code
```

---

## FAQ — Domande Frequenti

### Q1: Devo partire con microservizi?

**No.** Il 95% dei SaaS dovrebbe iniziare con un monolite (preferibilmente modulare). I microservizi hanno senso quando il team supera le 30 persone e i confini dei domini sono ben compresi. Partire con microservizi pre-PMF è il modo migliore per non raggiungere mai il PMF: la complessità operativa consuma il tempo che dovresti usare per iterare sul prodotto.

### Q2: PostgreSQL o MongoDB per un nuovo SaaS?

**PostgreSQL** nella stragrande maggioranza dei casi. Supporta JSON (per dati semi-strutturati), full-text search, partitioning, RLS, ed è ACID compliant. MongoDB ha senso per use case specifici: schema molto variabile (CMS), documenti nested profondi, o scalabilità orizzontale nativa su dataset enormi. Ma per il 90% dei SaaS, PostgreSQL + Redis è la combinazione ottimale.

### Q3: Come gestire le migration DB con zero-downtime?

Usare il pattern **expand-and-contract**. Mai fare ALTER TABLE distruttive direttamente. Step: (1) aggiungere nuova colonna/tabella, (2) dual-write nel codice, (3) backfill dati esistenti, (4) switch le letture, (5) rimuovere il vecchio dopo stabilizzazione. Testare sempre su un clone del DB di produzione prima.

### Q4: Quante Availability Zone servono?

Minimo **2 AZ** per qualsiasi workload di produzione. 3 AZ è lo standard consigliato da AWS. Multi-region solo se necessario per compliance (data residency), latenza globale (utenti in continenti diversi), o SLA 99.99%.

### Q5: Come implementare il rate limiting multi-tenant?

Usare **Redis con token bucket algorithm**. Chiave per tenant: `ratelimit:{tenant_id}:{window}`. Limiti diversi per piano (Free: 60 req/min, Pro: 600 req/min, Enterprise: custom). Implementare a livello di API Gateway o middleware. Rispondere con `429 Too Many Requests` e header `X-RateLimit-*`.

### Q6: Kubernetes è necessario?

**No**, non per tutti. Kubernetes è necessario quando si hanno 10+ servizi, team DevOps dedicato, e necessità di scaling granulare. Per SaaS in fase iniziale, PaaS (Heroku, Railway, Render) o ECS (AWS) sono scelte migliori: meno complessità operativa, focus sul prodotto. Migrare a Kubernetes quando il costo PaaS supera 3× il costo K8s managed.

### Q7: Come gestire i dati di un tenant che cancella l'account?

**Soft delete** con retention period (30-90 giorni): marcare come `deleted_at = now()`, rendere i dati inaccessibili ma recuperabili. Dopo il retention period: hard delete o anonimizzazione (GDPR). Per compliance: documentare la data retention policy, fornire export dei dati prima della cancellazione, conferma email della richiesta di cancellazione.

### Q8: Feature flags o feature branches?

**Feature flags**. I feature branch di lunga durata (> 2-3 giorni) causano merge conflict, integrazione dolorosa, e ritardano il feedback. Con feature flags: sviluppare su main/trunk, deployare codice spento, attivare gradualmente. I branch restano solo per il ciclo PR (1-2 giorni max).

### Q9: Come scegliere tra REST, GraphQL e gRPC?

| API Style | Quando usare |
|---|---|
| REST | API pubbliche, integrazioni third-party, CRUD standard |
| GraphQL | Frontend con requisiti dati variabili, mobile con bandwidth limitata |
| gRPC | Comunicazione interna tra microservizi, streaming, alta performance |

Per la maggior parte dei SaaS: REST per API pubblica + gRPC (o REST) per comunicazione interna.

### Q10: Qual è la strategia di caching ottimale?

**Cache-aside con Redis** è il pattern più comune e più sicuro. TTL tra 5 e 60 minuti per la maggior parte dei dati. Cache invalidation event-based per dati critici (profilo utente, configurazione tenant). CDN per asset statici con hash nel filename (cache immutabile). Non cacheare mai dati sensibili (token, password hash) in shared cache.

### Q11: Come testare il disaster recovery?

**Game day** trimestrale: simulare un disaster (database failover, servizio down, AZ failure) e verificare che il sistema si ripristina entro il RTO. Documentare il risultato, i problemi trovati, e le azioni correttive. Il chaos engineering (Chaos Monkey, Litmus) può essere eseguito più frequentemente per guasti specifici.

### Q12: Come gestire il database connection pooling in un SaaS multi-tenant?

Usare **PgBouncer** in modalità `transaction` (la connessione DB è usata solo durante la transazione). Pool size = `(core_count * 2) + spindles` per nodo, tipicamente 10-20. Con schema-per-tenant, attenzione: `SET search_path` è per-sessione, non per-transazione. Soluzioni: usare pool separati per tenant, oppure passare lo schema nella query (`schema.table`).

### Q13: Come migrare da monolite a microservizi senza downtime?

Strangler Fig Pattern: (1) identificare il servizio da estrarre, (2) creare il nuovo servizio accanto al monolite, (3) usare un proxy/API gateway per routing graduale, (4) spostare il traffico al nuovo servizio progressivamente, (5) quando il 100% del traffico è sul nuovo servizio, rimuovere il codice dal monolite. Un servizio alla volta, mai big-bang.

### Q14: Quanto budget allocare per l'infrastruttura cloud?

Benchmark: i SaaS maturi spendono il **15-25% del revenue** in infrastruttura. Per startup in crescita, può essere 30-40% (economie di scala non ancora raggiunte). Se la spesa supera il 40% del revenue, serve un audit serio di ottimizzazione. Se è sotto il 10%, probabilmente si sta sotto-investendo in reliability e performance.

### Q15: Come proteggere le API da abusi (DDoS, scraping)?

Strategia a livelli: (1) CDN/WAF come primo scudo (Cloudflare, AWS WAF), (2) rate limiting per IP all'API Gateway, (3) rate limiting per tenant/API key nell'applicazione, (4) CAPTCHA o challenge per endpoint sensibili (login, signup), (5) anomaly detection per pattern di traffico insoliti, (6) blocklist per IP/range noti come malevoli. MAI esporre endpoint senza autenticazione + rate limiting.

### Q16: Quando serve un message queue vs chiamata diretta?

Un message queue serve quando: (1) l'operazione può essere asincrona (l'utente non deve aspettare), (2) l'operazione è pesante (> 5 secondi), (3) il consumer può essere temporaneamente down senza perdere dati, (4) serve decoupling tra producer e consumer (team/servizi diversi), (5) serve retry automatico con backoff. Chiamata diretta quando: la risposta è necessaria immediatamente, la latenza è bassa (< 100ms), il servizio è sempre disponibile.

---

## Matrici Decisionali di Riferimento

### Matrice: Scelta del Database

| Requisito | PostgreSQL | MySQL | MongoDB | DynamoDB |
|---|---|---|---|---|
| ACID compliance | Nativo | Nativo | Parziale | Parziale |
| Multi-tenancy (RLS) | Eccellente | Assente | Assente | IAM-based |
| JSON support | Eccellente (JSONB) | Buono (JSON) | Nativo | Nativo |
| Full-text search | Buono (built-in) | Buono (built-in) | Atlas Search | Assente |
| Horizontal scaling | Limitato (Citus) | Limitato | Nativo | Nativo |
| Cost (managed) | Medio | Basso | Medio | Pay-per-use |
| Ecosistema SaaS | Standard de facto | Comune | Comune per MVP | AWS-only |
| Partitioning | Eccellente (10+) | Buono | Nativo (sharding) | Automatico |

### Matrice: Scelta del Message Queue

| Requisito | Redis (BullMQ) | RabbitMQ | SQS | Kafka |
|---|---|---|---|---|
| Setup | Semplice | Medio | Zero ops | Complesso |
| Persistenza | Opzionale | Sì | Sì | Sì |
| Ordering | FIFO | FIFO | Best-effort* | Per-partition |
| Dead letter queue | Sì | Sì | Sì | Manuale |
| Throughput | Alto | Medio-alto | Alto | Molto alto |
| Latenza | Sub-ms | Ms | Ms-sec | Ms |
| Replay (riprocessare) | No | No | No | Sì |
| Costo | Basso | Medio | Pay-per-use | Alto |
| Ideale per | Startup, job queue | Routing complesso | AWS-native | Event stream |

*SQS FIFO disponibile con throughput ridotto

### Matrice: Scelta dell'API Gateway

| Requisito | Kong | AWS API GW | Traefik | NGINX |
|---|---|---|---|---|
| Costo | OSS gratuito | Pay-per-request | OSS gratuito | OSS gratuito |
| Plugin ecosystem | Ricco | Medio | Medio | Ampio |
| Auto-discovery | Plugin | No | Nativo (K8s) | No |
| Rate limiting | Plugin | Nativo | Plugin | Config |
| Auth integration | Plugin | Cognito/Lambda | Plugin | Config |
| gRPC support | Sì | Sì (HTTP API) | Sì | Sì |
| WebSocket | Sì | Sì | Sì | Sì |
| Managed option | Kong Cloud | Nativo | No | NGINX Plus |
| Ideale per | Multi-cloud | AWS-only | Kubernetes | Self-managed |

### Matrice: Scelta dell'Observability Stack

| Requisito | Datadog | Grafana+Prometheus+Loki | New Relic | ELK Stack |
|---|---|---|---|---|
| Setup | Minuti | Ore/giorni | Minuti | Ore/giorni |
| Costo | $$$$ | Gratuito (+ infra) | $$$ | Gratuito (+ infra) |
| Metriche | Eccellente | Eccellente | Eccellente | Medio |
| Log | Eccellente | Buono (Loki) | Buono | Eccellente |
| Tracing | Eccellente | Buono (Tempo) | Eccellente | Medio |
| Alerting | Eccellente | Buono (AlertMgr) | Eccellente | Buono |
| Dashboard | Eccellente | Eccellente | Buono | Buono (Kibana) |
| Scaling | Automatico | Da gestire | Automatico | Complesso |
| Vendor lock-in | Alto | Zero | Alto | Zero |
| Ideale per | Team senza DevOps | Team con DevOps | Team senza DevOps | Già usano ELK |

### Matrice: Deployment Strategy

```
COME SCEGLIERE LA STRATEGIA DI DEPLOYMENT:

  È la prima versione (MVP)?
    └─ SÌ → Recreate (semplice, downtime accettabile)

  Il downtime è accettabile?
    └─ SÌ → Rolling update (K8s default)
    └─ NO ↓

  Hai budget per 2x risorse?
    └─ SÌ → Blue-Green (rollback istantaneo)
    └─ NO ↓

  Il cambiamento è rischioso?
    └─ SÌ → Canary (validazione graduale)
    └─ NO → Rolling update con feature flag

  È una feature rischiosa ma il deploy è sicuro?
    └─ SÌ → Feature flag (deploy spento, attivare gradualmente)
```

---

*Ultimo aggiornamento: 2026-05-22*
