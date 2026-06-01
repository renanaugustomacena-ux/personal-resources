# Multi-Tenancy — Implementazione Tecnica Approfondita — Guida Approfondita

## Indice
- [Panoramica](#panoramica)
- [Fondamenti della Multi-Tenancy](#fondamenti-della-multi-tenancy)
- [Modelli di Isolamento del Database](#modelli-di-isolamento-del-database)
- [Database-per-Tenant](#database-per-tenant)
- [Schema-per-Tenant](#schema-per-tenant)
- [Shared Schema (Row-Level Isolation)](#shared-schema-row-level-isolation)
- [Confronto Dettagliato dei Modelli](#confronto-dettagliato-dei-modelli)
- [Tenant Isolation Patterns: Silo, Pool e Bridge](#tenant-isolation-patterns-silo-pool-e-bridge)
- [Database Multi-Tenancy Avanzata](#database-multi-tenancy-avanzata)
- [Isolamento Compute](#isolamento-compute)
- [Isolamento di Rete](#isolamento-di-rete)
- [Data Partitioning Strategies](#data-partitioning-strategies)
- [Noisy Neighbor Problem](#noisy-neighbor-problem)
- [Caching Tenant-Aware](#caching-tenant-aware)
- [Tenant Routing e Identificazione](#tenant-routing-e-identificazione)
- [Tenant Provisioning e Lifecycle](#tenant-provisioning-e-lifecycle)
- [Automazione del Provisioning](#automazione-del-provisioning)
- [Billing per Tenant](#billing-per-tenant)
- [Migrazione Dati tra Tenant](#migrazione-dati-tra-tenant)
- [Sicurezza e Isolamento](#sicurezza-e-isolamento)
- [Compliance e Data Residency](#compliance-e-data-residency)
- [Performance e Scalabilità](#performance-e-scalabilità)
- [Performance Benchmarking per Tenant](#performance-benchmarking-per-tenant)
- [Cross-Tenant Analytics](#cross-tenant-analytics)
- [Migrazione tra Modelli](#migrazione-tra-modelli)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [FAQ — Domande Frequenti](#faq--domande-frequenti)
- [Esercizi Pratici](#esercizi-pratici)
- [Riferimenti](#riferimenti)

---

## Panoramica

La multi-tenancy è l'architettura fondamentale che distingue il software SaaS dal software tradizionale on-premises. In un sistema multi-tenant, una singola istanza dell'applicazione serve simultaneamente molteplici clienti (tenant), ciascuno con i propri dati, configurazioni e, potenzialmente, personalizzazioni, mantenendo al contempo un isolamento logico completo tra i tenant. Il tenant non deve mai poter accedere, visualizzare o influenzare i dati o le prestazioni di un altro tenant.

L'implementazione della multi-tenancy è una delle decisioni architetturali più consequenziali nella costruzione di un prodotto SaaS. Influenza direttamente il costo operativo per tenant, la scalabilità del sistema, il profilo di sicurezza, la complessità dello sviluppo, e la capacità di soddisfare requisiti di compliance. Una scelta sbagliata in fase iniziale può richiedere mesi di refactoring per essere corretta, con costi significativi in termini di risorse e opportunità.

Questa guida analizza in profondità i tre modelli principali di isolamento del database nella multi-tenancy — database-per-tenant, schema-per-tenant e shared schema — con esempi concreti di implementazione, analisi dei trade-off, strategie per mitigare il noisy neighbor problem, approcci alla tenant provisioning, e considerazioni di sicurezza e performance. L'obiettivo è fornire al fondatore e all'architetto SaaS le conoscenze necessarie per una decisione informata che sia appropriata per il proprio specifico contesto.

---

## Fondamenti della Multi-Tenancy

### Tenant: Definizione Precisa

Un tenant in un sistema SaaS è l'unità organizzativa che rappresenta un singolo cliente. Un tenant può corrispondere a:
- Un'azienda (il modello più comune in B2B SaaS)
- Un singolo utente (comune in B2C SaaS come Notion o Evernote)
- Un dipartimento all'interno di un'azienda
- Un progetto o workspace

La definizione del tenant è una decisione di design che dipende dal modello di business. In Slack, un tenant è un "workspace" (che può corrispondere a un team, un dipartimento, o un'intera azienda). In Salesforce, un tenant è un'"organization" (un'istanza completa del CRM per un'azienda). In Notion, un tenant può essere un singolo utente (piano personale) o un team (piano team/enterprise).

### Single-Tenant vs Multi-Tenant

**Single-Tenant**: ogni cliente ha la propria istanza dedicata dell'applicazione e del database. È il modello tradizionale del software enterprise on-premises. Offre il massimo isolamento ma i costi operativi scalano linearmente con il numero di clienti.

**Multi-Tenant**: tutti i clienti condividono la stessa istanza dell'applicazione (o un pool di istanze). Il database può essere condiviso o separato a diversi livelli. I costi operativi scalano sub-linearmente con il numero di clienti.

La scelta tra single-tenant e multi-tenant non è binaria: esiste uno spettro di opzioni con diversi gradi di condivisione e isolamento. In pratica, quasi tutti i prodotti SaaS moderni adottano qualche forma di multi-tenancy, con variazioni nel livello di isolamento del database.

### I Livelli della Multi-Tenancy

La multi-tenancy si manifesta a diversi livelli dello stack:

**Application Layer**: l'applicazione stessa è condivisa tra tutti i tenant. Il codice è lo stesso; il comportamento varia in base al contesto del tenant (configurazioni, feature flags, branding).

**Compute Layer**: le risorse computazionali (CPU, memoria) sono condivise tra i tenant. L'applicazione gestisce richieste da diversi tenant sugli stessi server.

**Data Layer**: il livello più critico e dove le decisioni architetturali hanno il maggior impatto. Esistono tre modelli principali che analizziamo in dettaglio nelle sezioni seguenti.

**Network Layer**: la rete è tipicamente condivisa, con isolamento logico attraverso regole di routing e segmentazione. Alcuni prodotti enterprise offrono VPC peering o endpoint privati per isolamento di rete.

---

## Modelli di Isolamento del Database

### Spettro di Isolamento

I tre modelli di isolamento del database rappresentano punti diversi nello spettro tra isolamento completo e condivisione completa:

```
Massimo Isolamento                                    Massima Condivisione
◄──────────────────────────────────────────────────────────────────────►
 Database-per-Tenant    Schema-per-Tenant    Shared Schema (Row-Level)

 - Sicurezza massima    - Buon compromesso   - Efficienza massima
 - Costo massimo        - Complessità media   - Complessità nel codice
 - Scalabilità limitata - Scalabilità media   - Scalabilità massima
```

---

## Database-per-Tenant

### Architettura

Nel modello database-per-tenant, ogni tenant ha un database completamente dedicato. Tutti i dati del tenant — tabelle, indici, stored procedures — risiedono in un database isolato. L'applicazione determina quale database utilizzare basandosi sull'identificazione del tenant nella richiesta (tipicamente dal subdomain, da un header HTTP, o dal token JWT).

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Tenant A    │     │  Tenant B    │     │  Tenant C    │
│  Database    │     │  Database    │     │  Database    │
├──────────────┤     ├──────────────┤     ├──────────────┤
│ users        │     │ users        │     │ users        │
│ projects     │     │ projects     │     │ projects     │
│ invoices     │     │ invoices     │     │ invoices     │
│ ...          │     │ ...          │     │ ...          │
└──────────────┘     └──────────────┘     └──────────────┘
```

### Implementazione

**Connection Routing**: l'applicazione mantiene un registry dei tenant e dei corrispondenti connection parameters (host, porta, database name, credenziali). Quando una richiesta arriva, l'applicazione identifica il tenant e seleziona la connessione appropriata.

```python
# Esempio di connection routing in Python con SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class TenantDatabaseRouter:
    def __init__(self):
        self._engines = {}
        self._session_factories = {}

    def get_session(self, tenant_id: str):
        if tenant_id not in self._engines:
            config = self._get_tenant_config(tenant_id)
            engine = create_engine(
                f"postgresql://{config.user}:{config.password}"
                f"@{config.host}:{config.port}/{config.database}",
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True
            )
            self._engines[tenant_id] = engine
            self._session_factories[tenant_id] = sessionmaker(bind=engine)

        return self._session_factories[tenant_id]()

    def _get_tenant_config(self, tenant_id: str):
        # Recupera la configurazione dal tenant registry
        # (potrebbe essere un database dedicato, un secret manager, etc.)
        return TenantRegistry.get_config(tenant_id)
```

**Schema Migration**: ogni database deve essere migrato indipendentemente. Questo richiede un sistema di migration che iteri su tutti i database dei tenant:

```python
# Migration runner per database-per-tenant
import alembic
from tenant_registry import get_all_tenant_configs

def run_migrations_all_tenants():
    configs = get_all_tenant_configs()
    results = {}

    for tenant_id, config in configs.items():
        try:
            alembic_cfg = create_alembic_config(config.database_url)
            alembic.command.upgrade(alembic_cfg, "head")
            results[tenant_id] = "success"
        except Exception as e:
            results[tenant_id] = f"failed: {str(e)}"
            # Non bloccare le altre migrazioni
            logger.error(f"Migration failed for tenant {tenant_id}: {e}")

    return results
```

### Vantaggi

- **Isolamento completo dei dati**: impossibilità fisica di accedere ai dati di un altro tenant. Il massimo livello di sicurezza.
- **Performance isolate**: un tenant non può influenzare le performance di un altro. Nessun noisy neighbor problem.
- **Backup e restore per tenant**: possibilità di eseguire backup e restore di un singolo tenant senza impattare gli altri.
- **Compliance facilitata**: alcuni requisiti normativi (es. data residency) richiedono che i dati siano fisicamente separati. Questo modello lo soddisfa nativamente.
- **Personalizzazione dello schema**: possibilità di personalizzare lo schema per tenant specifici (custom fields, tabelle aggiuntive), utile per clienti enterprise con requisiti unici.

### Svantaggi

- **Costo operativo elevato**: ogni database richiede risorse dedicate (CPU, memoria, storage). Con 1,000 tenant, si gestiscono 1,000 database.
- **Complessità delle migrazioni**: ogni schema change deve essere applicato a tutti i database. Un errore in una migrazione può lasciare i tenant in stati inconsistenti.
- **Connection pool explosion**: ogni database richiede un connection pool dedicato. Con centinaia di tenant, il numero totale di connessioni può diventare proibitivo.
- **Cross-tenant queries impossibili**: aggregazioni e analytics che richiedono dati da più tenant sono impossibili con query dirette. Richiedono ETL in un data warehouse separato.
- **Scalabilità limitata dal numero di database**: la maggior parte dei database server ha limiti pratici sul numero di database che può gestire efficientemente.

### Quando Usare Database-per-Tenant

- Clienti enterprise con requisiti di isolamento stringenti
- Settori regolamentati (finance, healthcare, governo)
- Numero limitato di tenant (< 100-500)
- Tenant con volumi di dati e carico molto diversi
- Requisiti di data residency per diversi paesi

---

## Schema-per-Tenant

### Architettura

Nel modello schema-per-tenant, tutti i tenant condividono lo stesso server database ma ogni tenant ha il proprio schema (namespace). Lo schema contiene tutte le tabelle del tenant, isolate dagli altri schema nello stesso database. Questo modello è supportato nativamente da PostgreSQL (tramite schema search_path) e da altri database relazionali.

```
┌──────────────────────────────────────────────────────┐
│                    Database Server                     │
│                                                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐│
│  │  Schema:      │  │  Schema:      │  │  Schema:      ││
│  │  tenant_a     │  │  tenant_b     │  │  tenant_c     ││
│  ├──────────────┤  ├──────────────┤  ├──────────────┤│
│  │ users        │  │ users        │  │ users        ││
│  │ projects     │  │ projects     │  │ projects     ││
│  │ invoices     │  │ invoices     │  │ invoices     ││
│  └──────────────┘  └──────────────┘  └──────────────┘│
│                                                        │
│  ┌─────────────────────────────────────────────────┐  │
│  │  Schema: public (shared data - plans, configs)   │  │
│  └─────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘
```

### Implementazione con PostgreSQL

PostgreSQL supporta nativamente il concetto di schema attraverso il `search_path`. La strategia di implementazione tipica è:

```python
# Middleware per impostare lo schema del tenant in PostgreSQL
class TenantSchemaMiddleware:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        tenant_id = self._extract_tenant_id(environ)

        # Impostare lo schema search_path per la connessione
        with db.engine.connect() as conn:
            conn.execute(
                text(f"SET search_path TO tenant_{tenant_id}, public")
            )

        return self.app(environ, start_response)

    def _extract_tenant_id(self, environ):
        # Estrarre il tenant dal subdomain
        host = environ.get('HTTP_HOST', '')
        subdomain = host.split('.')[0]
        return subdomain
```

**Creazione di un nuovo tenant**:

```sql
-- Creare un nuovo schema per il tenant
CREATE SCHEMA tenant_acme;

-- Creare le tabelle nello schema del tenant
SET search_path TO tenant_acme;

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    owner_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Ripristinare il search_path
RESET search_path;
```

**Schema Migration**: le migrazioni sono più semplici rispetto al modello database-per-tenant perché tutti gli schema sono nello stesso database:

```python
# Migrazione per tutti gli schema tenant
def migrate_all_schemas():
    schemas = get_all_tenant_schemas()

    for schema_name in schemas:
        with db.engine.connect() as conn:
            conn.execute(text(f"SET search_path TO {schema_name}"))
            # Applicare le migrazioni
            alembic.command.upgrade(config, "head")
            conn.execute(text("RESET search_path"))
```

### Vantaggi

- **Buon isolamento logico**: gli schema PostgreSQL forniscono isolamento a livello di namespace. Le query di un tenant non possono accidentalmente accedere ai dati di un altro (se il search_path è corretto).
- **Efficienza delle risorse**: un singolo server database serve tutti i tenant, con condivisione efficiente di CPU, memoria e connection pool.
- **Backup unificato**: un singolo backup del database include tutti i tenant.
- **Migrazioni più semplici**: tutte le migrazioni avvengono sullo stesso server, semplificando il processo.
- **Cross-tenant analytics possibile**: queries cross-schema sono possibili quando necessario per analytics interne.

### Svantaggi

- **Limiti di scalabilità dello schema**: PostgreSQL non è progettato per gestire migliaia di schema. Le performance degradano significativamente oltre 500-1,000 schema per database.
- **Connection pooling complesso**: il `search_path` è una proprietà della sessione, il che complica l'uso di connection pooler come PgBouncer in modalità transaction pooling.
- **Noisy neighbor a livello di risorse**: i tenant condividono le risorse del server database. Un tenant con query pesanti impatta le performance di tutti gli altri.
- **Complessità ORM**: la maggior parte degli ORM non supporta nativamente lo switch di schema. Richiede configurazione custom e middleware.

### Quando Usare Schema-per-Tenant

- Numero medio di tenant (50-500)
- Requisiti di isolamento moderati (non regolamentato)
- Team con competenze PostgreSQL avanzate
- Necessità di bilanciare isolamento ed efficienza

---

## Shared Schema (Row-Level Isolation)

### Architettura

Nel modello shared schema, tutti i tenant condividono le stesse tabelle nello stesso database. L'isolamento è implementato a livello di riga attraverso una colonna `tenant_id` presente in ogni tabella. Ogni query include un filtro su `tenant_id` per garantire che un tenant acceda solo ai propri dati.

```
┌──────────────────────────────────────────────────────┐
│                    Database                            │
│                                                        │
│  ┌──────────────────────────────────────────────────┐│
│  │  Tabella: users                                    ││
│  │  ┌───────────┬──────────┬────────────────────┐    ││
│  │  │ tenant_id │ id       │ email              │    ││
│  │  ├───────────┼──────────┼────────────────────┤    ││
│  │  │ acme      │ 1        │ alice@acme.com     │    ││
│  │  │ acme      │ 2        │ bob@acme.com       │    ││
│  │  │ globex    │ 3        │ carol@globex.com   │    ││
│  │  │ initech   │ 4        │ dave@initech.com   │    ││
│  │  └───────────┴──────────┴────────────────────┘    ││
│  └──────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────┘
```

### Implementazione

**Schema del database**:

```sql
-- Ogni tabella include tenant_id come parte della primary key
CREATE TABLE users (
    tenant_id VARCHAR(50) NOT NULL,
    id SERIAL,
    email VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (tenant_id, id),
    UNIQUE (tenant_id, email)
);

CREATE TABLE projects (
    tenant_id VARCHAR(50) NOT NULL,
    id SERIAL,
    name VARCHAR(255) NOT NULL,
    owner_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (tenant_id, id),
    FOREIGN KEY (tenant_id, owner_id)
        REFERENCES users(tenant_id, id)
);

-- Indice per performance delle query filtrate per tenant
CREATE INDEX idx_users_tenant ON users(tenant_id);
CREATE INDEX idx_projects_tenant ON projects(tenant_id);
```

**Row-Level Security (RLS) con PostgreSQL**:

PostgreSQL offre Row-Level Security nativo che può essere utilizzato per implementare l'isolamento a livello di database, aggiungendo una protezione indipendente dal codice applicativo:

```sql
-- Abilitare RLS sulla tabella
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Creare una policy che limita l'accesso al tenant corrente
CREATE POLICY tenant_isolation ON users
    USING (tenant_id = current_setting('app.current_tenant'));

-- Ripetere per ogni tabella
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON projects
    USING (tenant_id = current_setting('app.current_tenant'));
```

```python
# Middleware per impostare il tenant in ogni richiesta
class TenantMiddleware:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        tenant_id = self._extract_tenant_id(environ)

        # Impostare il tenant nella sessione PostgreSQL
        with db.engine.connect() as conn:
            conn.execute(
                text("SET app.current_tenant = :tenant"),
                {"tenant": tenant_id}
            )

        return self.app(environ, start_response)
```

**ORM Integration (SQLAlchemy)**:

```python
from sqlalchemy import event
from sqlalchemy.orm import Session

class TenantMixin:
    """Mixin per aggiungere tenant_id a tutti i modelli"""
    tenant_id = Column(String(50), nullable=False, index=True)

class User(Base, TenantMixin):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)

# Filtro automatico per tenant su tutte le query
@event.listens_for(Session, "do_orm_execute")
def _add_tenant_filter(orm_execute_state):
    if orm_execute_state.is_select:
        tenant_id = get_current_tenant_id()
        if tenant_id:
            orm_execute_state.statement = orm_execute_state.statement.filter(
                orm_execute_state.mapper.class_.tenant_id == tenant_id
            )
```

### Vantaggi

- **Massima efficienza delle risorse**: un singolo database, un singolo schema, condivisione ottimale delle risorse.
- **Scalabilità superiore**: il numero di tenant non è limitato dal numero di database o schema. Migliaia o milioni di tenant sullo stesso database.
- **Migrazioni semplici**: una singola migrazione aggiorna tutte le tabelle per tutti i tenant simultaneamente.
- **Connection pooling semplice**: tutte le connessioni sono allo stesso database, pool standard.
- **Cross-tenant analytics naturale**: queries aggregate su tutti i tenant sono native e performanti.

### Svantaggi

- **Rischio di data leakage**: un bug nel codice (un WHERE mancante, un ORM mal configurato) può esporre dati di un tenant a un altro. Questo è il rischio più critico.
- **Performance condivise**: noisy neighbor problem. Un tenant con molti dati o query pesanti impatta tutti.
- **Backup/restore per tenant complesso**: non è possibile eseguire backup o restore di un singolo tenant con strumenti nativi del database. Richiede logica custom.
- **Complessità nel codice applicativo**: ogni query, ogni endpoint, ogni funzionalità deve includere il filtro `tenant_id`. Un singolo errore può causare un data breach.
- **Indici più complessi**: tutti gli indici devono includere `tenant_id` come primo campo per performance ottimali, aumentando la dimensione degli indici.

### Quando Usare Shared Schema

- Numero elevato di tenant (> 500, potenzialmente milioni)
- Tenant con volumi di dati relativamente piccoli e uniformi
- Costi operativi devono essere minimizzati
- Team con forte disciplina nel testing dell'isolamento
- Non soggetto a requisiti di isolamento fisico dei dati

---

## Confronto Dettagliato dei Modelli

| Caratteristica | Database-per-Tenant | Schema-per-Tenant | Shared Schema |
|---|---|---|---|
| Isolamento dati | Fisico | Logico (namespace) | Logico (row-level) |
| Costo per tenant | Alto | Medio | Basso |
| Max tenant | ~100-500 | ~500-1,000 | Illimitati |
| Complessità migrazioni | Alta | Media | Bassa |
| Noisy neighbor | Nessuno | Medio | Alto |
| Backup per tenant | Nativo | Possibile | Complesso |
| Cross-tenant analytics | Complesso | Possibile | Nativo |
| Rischio data leakage | Minimo | Basso | Medio-Alto |
| Connection pooling | Complesso | Complesso | Semplice |
| Time-to-provision | Secondi-Minuti | Secondi | Millisecondi |
| Personalizzazione schema | Massima | Alta | Limitata |

---

## Tenant Isolation Patterns: Silo, Pool e Bridge

I tre pattern fondamentali di isolamento tenant — Silo, Pool e Bridge — rappresentano le strategie architetturali con cui distribuire risorse infrastrutturali tra i tenant. Ogni pattern ha implicazioni profonde su costi, sicurezza, compliance e complessità operativa.

### Pattern Silo (Full Isolation)

Nel pattern Silo, ogni tenant riceve un set completo di risorse dedicate: database, compute, storage e rete. Non vi è alcuna condivisione di risorse a livello infrastrutturale.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Control Plane                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                │
│  │ Tenant Mgmt │  │  Billing    │  │  Monitoring  │                │
│  └─────────────┘  └─────────────┘  └─────────────┘                │
└─────────────────────────────────────────────────────────────────────┘
         │                    │                    │
    ┌────▼────┐          ┌───▼─────┐         ┌───▼─────┐
    │ SILO A  │          │ SILO B  │         │ SILO C  │
    │┌───────┐│          │┌───────┐│         │┌───────┐│
    ││ App   ││          ││ App   ││         ││ App   ││
    │├───────┤│          │├───────┤│         │├───────┤│
    ││ Cache ││          ││ Cache ││         ││ Cache ││
    │├───────┤│          │├───────┤│         │├───────┤│
    ││  DB   ││          ││  DB   ││         ││  DB   ││
    │├───────┤│          │├───────┤│         │├───────┤│
    ││ Queue ││          ││ Queue ││         ││ Queue ││
    │└───────┘│          │└───────┘│         │└───────┘│
    └─────────┘          └─────────┘         └─────────┘
     Tenant A             Tenant B            Tenant C
```

**Caratteristiche operative**:

| Aspetto | Dettaglio |
|---------|-----------|
| Isolamento | Completo — nessuna risorsa condivisa |
| Blast radius | Limitato al singolo silo |
| Costo unitario | Alto — risorse duplicate per ogni tenant |
| Scaling | Verticale per silo, orizzontale per aggiunta silo |
| Deployment | Indipendente per silo (rolling update o blue-green per tenant) |
| Onboarding | Lento — provisioning infrastruttura completa |
| Adatto a | Finance, healthcare, governo, enterprise con SLA stringenti |

**Pseudocodice — Provisioning di un Silo**:

```python
class SiloProvisioner:
    async def provision_silo(self, tenant: Tenant) -> SiloResources:
        # 1. Provisioning infrastruttura dedicata
        vpc = await self.cloud.create_vpc(
            cidr=self._allocate_cidr(tenant.id),
            name=f"silo-{tenant.slug}"
        )

        db = await self.cloud.create_rds_instance(
            engine="postgres",
            instance_class=tenant.plan.db_instance_class,
            vpc_id=vpc.id,
            db_name=f"db_{tenant.slug}",
            encrypted=True,
            multi_az=tenant.plan.requires_ha
        )

        cluster = await self.cloud.create_ecs_cluster(
            name=f"cluster-{tenant.slug}",
            vpc_id=vpc.id
        )

        cache = await self.cloud.create_elasticache(
            engine="redis",
            node_type=tenant.plan.cache_node_type,
            vpc_id=vpc.id
        )

        # 2. Deploy applicazione nel silo
        await self.deploy_app(cluster, tenant)

        # 3. Configurare DNS
        await self.dns.create_record(
            name=f"{tenant.slug}.app.example.com",
            target=cluster.load_balancer_dns
        )

        # 4. Registrare silo nel control plane
        await self.registry.register_silo(tenant.id, SiloResources(
            vpc=vpc, db=db, cluster=cluster, cache=cache
        ))
```

### Pattern Pool (Full Sharing)

Nel pattern Pool, tutti i tenant condividono lo stesso pool di risorse. L'isolamento è interamente logico, gestito a livello applicativo e di database (RLS, filtri, namespace).

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Control Plane                               │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
              ┌────────────▼────────────┐
              │      POOL CONDIVISO     │
              │                         │
              │  ┌─────────────────┐    │
              │  │   App Cluster   │    │    Tenant A ─┐
              │  │  (N istanze)    │    │    Tenant B ─┤
              │  └────────┬────────┘    │    Tenant C ─┤
              │           │             │    Tenant D ─┤
              │  ┌────────▼────────┐    │    Tenant E ─┤
              │  │   Cache Pool    │    │    ...       │
              │  │  (Redis cluster)│    │    Tenant N ─┘
              │  └────────┬────────┘    │
              │           │             │
              │  ┌────────▼────────┐    │
              │  │   Database      │    │
              │  │  (shared schema)│    │
              │  └─────────────────┘    │
              └─────────────────────────┘
```

**Caratteristiche operative**:

| Aspetto | Dettaglio |
|---------|-----------|
| Isolamento | Logico — RLS, filtri applicativi, namespace |
| Blast radius | Globale — un problema impatta tutti i tenant |
| Costo unitario | Basso — risorse ammortizzate su N tenant |
| Scaling | Orizzontale nativo (aggiungere nodi al pool) |
| Deployment | Unico per tutti i tenant (canary, rolling) |
| Onboarding | Immediato — inserimento record nel pool |
| Adatto a | SaaS self-service, B2C, startup early-stage, alto volume tenant |

### Pattern Bridge (Isolamento Ibrido)

Il pattern Bridge è il più pragmatico e il più adottato nei SaaS maturi. Combina elementi di Silo e Pool, isolando selettivamente le risorse in base al tier del tenant, ai requisiti di compliance o al carico.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Control Plane                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                │
│  │ Tenant Mgmt │  │  Routing    │  │  Monitoring  │                │
│  └─────────────┘  └─────────────┘  └─────────────┘                │
└────────┬─────────────────┬──────────────────┬───────────────────────┘
         │                 │                  │
    ┌────▼────┐     ┌─────▼──────┐     ┌─────▼──────┐
    │ SILO    │     │   POOL     │     │   SILO     │
    │ Premium │     │  Standard  │     │ Compliance │
    │┌───────┐│     │┌──────────┐│     │┌───────┐   │
    ││DB ded.││     ││DB shared ││     ││DB ded.│   │
    ││App ded││     ││App shared││     ││EU only│   │
    │└───────┘│     │└──────────┘│     │└───────┘   │
    └─────────┘     └────────────┘     └────────────┘
    Tenant Ent.     Tenant Free/Pro     Tenant GDPR
```

**Strategie di bridging comuni**:

| Strategia | Risorse Silo | Risorse Pool | Criterio |
|-----------|-------------|-------------|----------|
| Tier-based | DB, compute per enterprise | DB e compute condivisi per free/pro | Piano commerciale |
| Compliance-based | DB per tenant soggetti a regolamentazione | Pool per tenant standard | Requisiti normativi |
| Load-based | Silo per tenant ad alto traffico | Pool per tenant low-traffic | Metriche di carico |
| Geographic | Silo per regioni con data residency | Pool per regioni senza vincoli | Localizzazione dati |

**Pseudocodice — Router Bridge**:

```python
class BridgeRouter:
    """Determina se un tenant deve usare risorse silo o pool."""

    def resolve_resources(self, tenant: Tenant) -> ResourceSet:
        # Regola 1: Enterprise sempre in silo
        if tenant.plan.tier == "enterprise":
            return self.silo_registry.get_resources(tenant.id)

        # Regola 2: Compliance richiede silo dedicato
        if tenant.compliance_requirements:
            region = tenant.data_residency_region
            return self.silo_registry.get_regional_silo(tenant.id, region)

        # Regola 3: Tenant ad alto carico promossi a silo
        if self.metrics.avg_rps(tenant.id, window="7d") > 500:
            if not self.silo_registry.has_silo(tenant.id):
                await self.promote_to_silo(tenant)
            return self.silo_registry.get_resources(tenant.id)

        # Default: pool condiviso
        return self.pool_registry.get_pool_resources(tenant.region)

    async def promote_to_silo(self, tenant: Tenant):
        """Migra un tenant dal pool a un silo dedicato."""
        silo = await self.silo_provisioner.provision_silo(tenant)
        await self.data_migrator.migrate_tenant_data(
            tenant_id=tenant.id,
            source=self.pool_registry.get_pool_db(tenant.region),
            target=silo.db
        )
        await self.routing.update_route(tenant.id, silo)
        await self.pool_registry.remove_tenant_from_pool(tenant.id)
```

### Matrice Decisionale dei Pattern

| Criterio | Silo | Pool | Bridge |
|----------|------|------|--------|
| Costo operativo per 10 tenant | Molto alto | Basso | Medio |
| Costo operativo per 10.000 tenant | Insostenibile | Basso | Medio-basso |
| Sicurezza dei dati | Massima | Dipende dall'implementazione | Configurabile per tenant |
| Velocità di onboarding | Minuti | Millisecondi | Variabile |
| Complessità operativa | Media (N infrastrutture uguali) | Bassa | Alta (gestione ibrida) |
| Flessibilità contrattuale | Massima | Limitata | Alta |
| Upgrade path | Già al massimo isolamento | Migrazione verso silo costosa | Promozione/demozione graduale |

---

## Database Multi-Tenancy Avanzata

### Schema-per-Tenant: Deep Dive PostgreSQL

L'implementazione schema-per-tenant in PostgreSQL merita un approfondimento tecnico perché coinvolge meccanismi specifici del database engine.

**Gestione automatica degli schema con trigger**:

```sql
-- Funzione per creare automaticamente lo schema di un nuovo tenant
CREATE OR REPLACE FUNCTION create_tenant_schema(p_tenant_slug TEXT)
RETURNS VOID AS $$
DECLARE
    v_schema_name TEXT := 'tenant_' || p_tenant_slug;
BEGIN
    -- Creare lo schema
    EXECUTE format('CREATE SCHEMA IF NOT EXISTS %I', v_schema_name);

    -- Creare le tabelle nello schema del tenant
    EXECUTE format('
        CREATE TABLE %I.users (
            id BIGSERIAL PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT ''member'',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )', v_schema_name);

    EXECUTE format('
        CREATE TABLE %I.projects (
            id BIGSERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            owner_id BIGINT NOT NULL REFERENCES %I.users(id),
            status TEXT NOT NULL DEFAULT ''active'',
            settings JSONB NOT NULL DEFAULT ''{}''::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )', v_schema_name, v_schema_name);

    EXECUTE format('
        CREATE TABLE %I.audit_log (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT REFERENCES %I.users(id),
            action TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id BIGINT,
            old_value JSONB,
            new_value JSONB,
            ip_address INET,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )', v_schema_name, v_schema_name);

    -- Indici
    EXECUTE format('CREATE INDEX ON %I.users (email)', v_schema_name);
    EXECUTE format('CREATE INDEX ON %I.projects (owner_id)', v_schema_name);
    EXECUTE format('CREATE INDEX ON %I.audit_log (user_id, created_at DESC)', v_schema_name);

    -- Grant: l'utente applicativo può operare solo nel proprio schema
    EXECUTE format('GRANT USAGE ON SCHEMA %I TO app_user', v_schema_name);
    EXECUTE format('GRANT ALL ON ALL TABLES IN SCHEMA %I TO app_user', v_schema_name);
    EXECUTE format('GRANT ALL ON ALL SEQUENCES IN SCHEMA %I TO app_user', v_schema_name);

    RAISE NOTICE 'Schema % creato con successo', v_schema_name;
END;
$$ LANGUAGE plpgsql;

-- Utilizzo
SELECT create_tenant_schema('acme_corp');
SELECT create_tenant_schema('globex_inc');
```

**Verifica di integrità degli schema**:

```sql
-- Verifica che tutti gli schema tenant abbiano le stesse tabelle
SELECT
    s.schema_name,
    array_agg(t.table_name ORDER BY t.table_name) AS tables
FROM information_schema.schemata s
LEFT JOIN information_schema.tables t
    ON t.table_schema = s.schema_name
WHERE s.schema_name LIKE 'tenant_%'
GROUP BY s.schema_name
ORDER BY s.schema_name;

-- Trovare schema con tabelle mancanti rispetto a un template
WITH template_tables AS (
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'tenant_template'
),
tenant_tables AS (
    SELECT table_schema, array_agg(table_name) AS tables
    FROM information_schema.tables
    WHERE table_schema LIKE 'tenant_%'
      AND table_schema != 'tenant_template'
    GROUP BY table_schema
)
SELECT
    tt.table_schema,
    array(
        SELECT t.table_name FROM template_tables t
        WHERE t.table_name != ALL(tt.tables)
    ) AS missing_tables
FROM tenant_tables tt
WHERE EXISTS (
    SELECT 1 FROM template_tables t
    WHERE t.table_name != ALL(tt.tables)
);
```

### Row-Level Security (RLS): Implementazione Completa

RLS in PostgreSQL merita un trattamento approfondito perché rappresenta la difesa più solida contro il data leakage nel modello shared schema.

**Setup completo con ruoli e policy**:

```sql
-- 1. Creare ruoli dedicati
CREATE ROLE tenant_app_user LOGIN PASSWORD 'strong_password_here';
CREATE ROLE tenant_admin_user LOGIN PASSWORD 'strong_password_here';

-- 2. Tabella tenant per la registrazione
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    plan TEXT NOT NULL DEFAULT 'free',
    status TEXT NOT NULL DEFAULT 'active',
    settings JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 3. Tabelle con tenant_id
CREATE TABLE documents (
    id BIGSERIAL PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    title TEXT NOT NULL,
    content TEXT,
    author_id BIGINT NOT NULL,
    visibility TEXT NOT NULL DEFAULT 'private',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 4. Abilitare RLS
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

-- 5. Policy per operazioni CRUD separate
-- SELECT: il tenant vede solo i propri documenti
CREATE POLICY documents_select ON documents
    FOR SELECT
    USING (tenant_id = current_setting('app.current_tenant')::uuid);

-- INSERT: il tenant può inserire solo nel proprio namespace
CREATE POLICY documents_insert ON documents
    FOR INSERT
    WITH CHECK (tenant_id = current_setting('app.current_tenant')::uuid);

-- UPDATE: il tenant può modificare solo i propri documenti
CREATE POLICY documents_update ON documents
    FOR UPDATE
    USING (tenant_id = current_setting('app.current_tenant')::uuid)
    WITH CHECK (tenant_id = current_setting('app.current_tenant')::uuid);

-- DELETE: il tenant può eliminare solo i propri documenti
CREATE POLICY documents_delete ON documents
    FOR DELETE
    USING (tenant_id = current_setting('app.current_tenant')::uuid);

-- 6. Applicare i grant
GRANT SELECT, INSERT, UPDATE, DELETE ON documents TO tenant_app_user;

-- 7. Policy per admin: accesso cross-tenant (per operazioni interne)
CREATE POLICY documents_admin ON documents
    FOR ALL
    TO tenant_admin_user
    USING (true);
```

**Test di verifica RLS**:

```sql
-- Test 1: Inserire dati per due tenant
SET app.current_tenant = 'uuid-tenant-a';
INSERT INTO documents (tenant_id, title, author_id)
VALUES ('uuid-tenant-a', 'Doc di Tenant A', 1);

SET app.current_tenant = 'uuid-tenant-b';
INSERT INTO documents (tenant_id, title, author_id)
VALUES ('uuid-tenant-b', 'Doc di Tenant B', 2);

-- Test 2: Verificare isolamento
SET app.current_tenant = 'uuid-tenant-a';
SELECT * FROM documents;
-- Risultato atteso: solo "Doc di Tenant A"

-- Test 3: Tentare di inserire per un altro tenant (deve fallire)
SET app.current_tenant = 'uuid-tenant-a';
INSERT INTO documents (tenant_id, title, author_id)
VALUES ('uuid-tenant-b', 'Tentativo di injection', 1);
-- Risultato atteso: ERROR - new row violates row-level security policy

-- Test 4: Verificare che UPDATE cross-tenant fallisca
SET app.current_tenant = 'uuid-tenant-a';
UPDATE documents SET title = 'Hacked!' WHERE tenant_id = 'uuid-tenant-b';
-- Risultato atteso: UPDATE 0 (nessuna riga aggiornata, RLS filtra silenziosamente)
```

**RLS con funzioni di supporto per debugging**:

```sql
-- Funzione helper per impostare il contesto tenant
CREATE OR REPLACE FUNCTION set_tenant_context(p_tenant_id UUID)
RETURNS VOID AS $$
BEGIN
    PERFORM set_config('app.current_tenant', p_tenant_id::text, false);
END;
$$ LANGUAGE plpgsql;

-- Funzione per verificare il contesto attuale
CREATE OR REPLACE FUNCTION current_tenant()
RETURNS UUID AS $$
BEGIN
    RETURN current_setting('app.current_tenant', true)::uuid;
EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION 'Contesto tenant non impostato. Chiamare set_tenant_context() prima.';
END;
$$ LANGUAGE plpgsql;

-- Vista diagnostica: quante righe per tenant in ogni tabella
CREATE OR REPLACE VIEW tenant_data_summary AS
SELECT
    'documents' AS table_name,
    tenant_id,
    count(*) AS row_count,
    pg_size_pretty(sum(pg_column_size(documents.*))) AS estimated_size
FROM documents
GROUP BY tenant_id
UNION ALL
SELECT
    'users' AS table_name,
    tenant_id,
    count(*) AS row_count,
    pg_size_pretty(sum(pg_column_size(users.*))) AS estimated_size
FROM users
GROUP BY tenant_id;
```

### Database-per-Tenant con Connection Pool Management

Il connection pool è il collo di bottiglia più critico nel modello database-per-tenant. Con 200 tenant e 10 connessioni per pool, si hanno 2.000 connessioni attive — un carico significativo.

```python
# Connection pool manager con lazy initialization e eviction
import time
from collections import OrderedDict
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class TenantConnectionPoolManager:
    """
    Gestisce i connection pool per tenant con:
    - Lazy initialization (pool creato al primo accesso)
    - LRU eviction (pool meno usati chiusi per risparmiare risorse)
    - Health check (pool con connessioni morte ricreati)
    """
    def __init__(self, max_pools: int = 100, pool_size: int = 5):
        self._pools: OrderedDict[str, dict] = OrderedDict()
        self._max_pools = max_pools
        self._pool_size = pool_size

    def get_session(self, tenant_id: str):
        # Spostare il pool in cima (LRU)
        if tenant_id in self._pools:
            self._pools.move_to_end(tenant_id)
            pool_entry = self._pools[tenant_id]
            pool_entry["last_accessed"] = time.time()
            return pool_entry["session_factory"]()

        # Eviction se necessario
        if len(self._pools) >= self._max_pools:
            self._evict_least_used()

        # Creare nuovo pool
        config = TenantRegistry.get_config(tenant_id)
        engine = create_engine(
            config.database_url,
            pool_size=self._pool_size,
            max_overflow=2,
            pool_pre_ping=True,
            pool_recycle=3600
        )
        session_factory = sessionmaker(bind=engine)

        self._pools[tenant_id] = {
            "engine": engine,
            "session_factory": session_factory,
            "last_accessed": time.time(),
            "created_at": time.time()
        }
        return session_factory()

    def _evict_least_used(self):
        """Chiude il pool meno recentemente usato."""
        tenant_id, pool_entry = self._pools.popitem(last=False)
        pool_entry["engine"].dispose()

    def close_all(self):
        """Shutdown ordinato di tutti i pool."""
        for tenant_id, pool_entry in self._pools.items():
            pool_entry["engine"].dispose()
        self._pools.clear()

    def stats(self) -> dict:
        """Statistiche per monitoring."""
        return {
            "active_pools": len(self._pools),
            "max_pools": self._max_pools,
            "pools": {
                tid: {
                    "last_accessed": entry["last_accessed"],
                    "pool_status": entry["engine"].pool.status()
                }
                for tid, entry in self._pools.items()
            }
        }
```

---

## Isolamento Compute

L'isolamento compute definisce come le risorse di calcolo (CPU, memoria, processi) vengono distribuite tra i tenant. La scelta dipende dal livello di isolamento richiesto e dal budget operativo.

### Livelli di Isolamento Compute

```
Isolamento massimo ◄──────────────────────────────────────► Condivisione massima

Account cloud       Cluster K8s      Namespace K8s      Pod condiviso
  dedicato          dedicato          dedicato           (filtro logico)
```

### Namespace Kubernetes per Tenant

Il modello più comune per SaaS moderni: ogni tenant ottiene un namespace Kubernetes dedicato con resource quotas.

```yaml
# namespace-tenant-acme.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: tenant-acme
  labels:
    app.kubernetes.io/managed-by: tenant-controller
    tenant-id: acme
    tier: enterprise

---
# Resource quota per tenant
apiVersion: v1
kind: ResourceQuota
metadata:
  name: tenant-quota
  namespace: tenant-acme
spec:
  hard:
    requests.cpu: "4"
    requests.memory: 8Gi
    limits.cpu: "8"
    limits.memory: 16Gi
    pods: "20"
    services: "10"
    persistentvolumeclaims: "5"

---
# Limit range per singolo pod
apiVersion: v1
kind: LimitRange
metadata:
  name: tenant-limits
  namespace: tenant-acme
spec:
  limits:
    - type: Container
      default:
        cpu: "500m"
        memory: 512Mi
      defaultRequest:
        cpu: "250m"
        memory: 256Mi
      max:
        cpu: "2"
        memory: 4Gi

---
# Network policy: isolamento di rete tra namespace
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-cross-tenant
  namespace: tenant-acme
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              tenant-id: acme
    - from:
        - namespaceSelector:
            matchLabels:
              app.kubernetes.io/component: ingress-controller
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              tenant-id: acme
    - to:
        - namespaceSelector:
            matchLabels:
              app.kubernetes.io/component: shared-services
    - to:  # Permettere DNS
        - namespaceSelector: {}
      ports:
        - protocol: UDP
          port: 53
```

### Cluster Dedicato per Tenant

Per clienti enterprise o settori regolamentati, un cluster Kubernetes completo per tenant.

```python
# Provisioning cluster dedicato (pseudocodice con API cloud)
class DedicatedClusterProvisioner:
    async def provision(self, tenant: Tenant) -> ClusterInfo:
        cluster = await self.cloud.create_k8s_cluster(
            name=f"tenant-{tenant.slug}",
            region=tenant.preferred_region,
            node_pools=[
                NodePool(
                    name="app",
                    machine_type=tenant.plan.compute_tier,
                    min_nodes=2,
                    max_nodes=tenant.plan.max_nodes,
                    auto_scaling=True
                ),
                NodePool(
                    name="worker",
                    machine_type="n2-standard-4",
                    min_nodes=1,
                    max_nodes=5,
                    auto_scaling=True,
                    taints=[{"key": "workload", "value": "background"}]
                )
            ],
            network_config=NetworkConfig(
                vpc_id=tenant.vpc_id,
                subnet_cidr=self._allocate_subnet(tenant),
                private_cluster=True,
                master_authorized_networks=[tenant.admin_cidr]
            ),
            encryption_config=EncryptionConfig(
                kms_key=tenant.kms_key_arn
            )
        )

        # Deploy degli operatori e dei servizi comuni
        await self.deploy_base_stack(cluster, tenant)
        return cluster
```

### Account Cloud Dedicato (Massimo Isolamento)

In settori come finance e governo, ogni tenant può richiedere un account cloud separato (AWS Account, GCP Project, Azure Subscription).

| Componente | Account Tenant A | Account Tenant B |
|------------|-----------------|-----------------|
| VPC | Dedicato | Dedicato |
| IAM | Ruoli dedicati | Ruoli dedicati |
| Encryption keys | KMS key dedicata | KMS key dedicata |
| Logging | CloudTrail dedicato | CloudTrail dedicato |
| Billing | Fattura separata | Fattura separata |
| Compliance | Certificazione indipendente | Certificazione indipendente |

---

## Isolamento di Rete

L'isolamento di rete impedisce che il traffico di un tenant possa raggiungere o intercettare le risorse di un altro tenant.

### VPC per Tenant

```
┌─────────────────────────────────────────────────────┐
│                  Account SaaS                        │
│                                                      │
│  ┌──────────────────┐   ┌──────────────────┐        │
│  │  VPC Tenant A     │   │  VPC Tenant B     │        │
│  │  10.1.0.0/16      │   │  10.2.0.0/16      │        │
│  │                    │   │                    │        │
│  │ ┌──────┐ ┌──────┐│   │ ┌──────┐ ┌──────┐│        │
│  │ │App   │ │ DB   ││   │ │App   │ │ DB   ││        │
│  │ │Sub   │ │ Sub  ││   │ │Sub   │ │ Sub  ││        │
│  │ │.1.0  │ │ .1.1 ││   │ │.2.0  │ │ .2.1 ││        │
│  │ └──────┘ └──────┘│   │ └──────┘ └──────┘│        │
│  └──────────────────┘   └──────────────────┘        │
│           │                       │                  │
│  ┌────────▼───────────────────────▼─────────┐       │
│  │          VPC Management / Control Plane   │       │
│  │          10.0.0.0/16                      │       │
│  │  Peering con VPC tenant (read-only mgmt)  │       │
│  └───────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────┘
```

### Security Groups Multi-Tenant

```python
# Configurazione security groups per isolamento tenant
class TenantSecurityGroupManager:
    def create_tenant_security_groups(self, tenant: Tenant, vpc_id: str):
        # SG per l'applicazione del tenant
        app_sg = self.ec2.create_security_group(
            GroupName=f"sg-app-{tenant.slug}",
            Description=f"App security group for tenant {tenant.slug}",
            VpcId=vpc_id,
            TagSpecifications=[{
                "ResourceType": "security-group",
                "Tags": [{"Key": "tenant-id", "Value": tenant.id}]
            }]
        )

        # SG per il database del tenant
        db_sg = self.ec2.create_security_group(
            GroupName=f"sg-db-{tenant.slug}",
            Description=f"DB security group for tenant {tenant.slug}",
            VpcId=vpc_id
        )

        # Regole: solo l'app del tenant può raggiungere il suo DB
        self.ec2.authorize_security_group_ingress(
            GroupId=db_sg["GroupId"],
            IpPermissions=[{
                "IpProtocol": "tcp",
                "FromPort": 5432,
                "ToPort": 5432,
                "UserIdGroupPairs": [{
                    "GroupId": app_sg["GroupId"],
                    "Description": f"App to DB for {tenant.slug}"
                }]
            }]
        )

        # Bloccare qualsiasi altro ingress al DB
        # (il default di un SG vuoto è deny all)

        return {"app_sg": app_sg["GroupId"], "db_sg": db_sg["GroupId"]}
```

### Service Mesh per Isolamento Applicativo

Con un service mesh (Istio, Linkerd), l'isolamento di rete può essere applicato a livello L7 con policy granulari.

```yaml
# Istio AuthorizationPolicy: solo il servizio del tenant A
# può chiamare il suo backend
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: tenant-acme-backend-policy
  namespace: tenant-acme
spec:
  selector:
    matchLabels:
      app: backend
  rules:
    - from:
        - source:
            namespaces: ["tenant-acme"]
            principals: ["cluster.local/ns/tenant-acme/sa/frontend"]
      to:
        - operation:
            methods: ["GET", "POST", "PUT", "DELETE"]
```

---

## Data Partitioning Strategies

### Partitioning Orizzontale (Sharding)

Per il modello shared schema, quando i dati crescono oltre le capacità di un singolo server database, è necessario implementare lo sharding — la distribuzione dei dati su più server basata su una chiave di partizione.

La chiave di partizione naturale per un sistema multi-tenant è `tenant_id`. Ogni tenant viene assegnato a uno shard specifico, e tutte le query per quel tenant vengono dirette allo shard corrispondente.

```python
# Sharding basato su tenant_id
class TenantShardRouter:
    def __init__(self, shard_configs):
        self.shards = {}
        for config in shard_configs:
            engine = create_engine(config.url)
            self.shards[config.shard_id] = engine

    def get_shard(self, tenant_id: str):
        # Consistent hashing per determinare lo shard
        shard_id = self._consistent_hash(tenant_id, len(self.shards))
        return self.shards[shard_id]

    def _consistent_hash(self, key: str, num_shards: int) -> int:
        hash_value = hashlib.md5(key.encode()).hexdigest()
        return int(hash_value, 16) % num_shards
```

### Partitioning per Range di Tenant

Un approccio alternativo al consistent hashing è il range-based partitioning, dove i tenant vengono assegnati a shard in base a un criterio logico:

- **Per dimensione**: tenant piccoli condividono shard, tenant grandi hanno shard dedicati
- **Per regione**: tenant europei su shard EU, tenant americani su shard US (utile per data residency)
- **Per piano**: tenant free su shard condivisi, tenant enterprise su shard premium

### PostgreSQL Table Partitioning

PostgreSQL supporta nativamente il table partitioning, che può essere utilizzato per implementare un partizionamento efficiente per tenant:

```sql
-- Creare una tabella partizionata per tenant
CREATE TABLE events (
    tenant_id VARCHAR(50) NOT NULL,
    id BIGSERIAL,
    event_type VARCHAR(100) NOT NULL,
    payload JSONB,
    created_at TIMESTAMP DEFAULT NOW()
) PARTITION BY LIST (tenant_id);

-- Creare partizioni per tenant specifici
CREATE TABLE events_acme PARTITION OF events
    FOR VALUES IN ('acme');

CREATE TABLE events_globex PARTITION OF events
    FOR VALUES IN ('globex');

-- Partizione default per tutti gli altri tenant
CREATE TABLE events_default PARTITION OF events
    DEFAULT;
```

---

## Noisy Neighbor Problem

### Definizione e Impatto

Il noisy neighbor problem si verifica quando un tenant con utilizzo intensivo delle risorse (CPU, I/O, memoria, bandwidth) degrada le performance per gli altri tenant che condividono le stesse risorse. Questo è intrinseco ai modelli con condivisione di risorse e rappresenta una delle sfide più significative della multi-tenancy.

### Strategie di Mitigazione

**Rate Limiting per Tenant**: implementare limiti sul numero di richieste, query, o operazioni che un tenant può eseguire in un dato intervallo di tempo.

```python
# Rate limiting per tenant con Redis
import redis

class TenantRateLimiter:
    def __init__(self, redis_client):
        self.redis = redis_client

    def check_rate_limit(self, tenant_id: str,
                          limit: int = 100,
                          window_seconds: int = 60) -> bool:
        key = f"ratelimit:{tenant_id}:{int(time.time()) // window_seconds}"

        pipe = self.redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, window_seconds)
        results = pipe.execute()

        current_count = results[0]
        return current_count <= limit
```

**Resource Quotas**: assegnare quote di risorse per tenant (storage, compute, connections) e enforcarle a livello applicativo e database.

**Query Timeout per Tenant**: impostare timeout diversi per le query basati sul piano del tenant.

```sql
-- Impostare un timeout per le query del tenant corrente
SET statement_timeout = '5s';  -- Tenant free
SET statement_timeout = '30s'; -- Tenant enterprise
```

**Connection Pooling per Tenant**: limitare il numero massimo di connessioni database per tenant per prevenire che un tenant monopolizzi il pool.

**Caching aggressivo**: implementare caching a più livelli (application cache, query cache, CDN) per ridurre il carico sul database.

**Throttling adattivo**: monitorare le performance per tenant e ridurre automaticamente i limiti per tenant che stanno causando degradazione.

**Implementazione completa del throttling adattivo**:

```python
class AdaptiveThrottler:
    """
    Monitora le metriche per tenant e applica throttling
    dinamico quando un tenant sta consumando risorse
    in modo anomalo rispetto alla propria baseline.
    """
    def __init__(self, metrics_store, config):
        self.metrics = metrics_store
        self.config = config

    async def evaluate_tenant(self, tenant_id: str) -> ThrottleDecision:
        # Metriche attuali del tenant
        current = await self.metrics.get_current(tenant_id)
        # Baseline storica (media ultimi 7 giorni)
        baseline = await self.metrics.get_baseline(tenant_id, days=7)

        scores = {
            "cpu": current.cpu_percent / max(baseline.cpu_percent, 1),
            "db_queries": current.queries_per_sec / max(baseline.queries_per_sec, 1),
            "bandwidth": current.bandwidth_mbps / max(baseline.bandwidth_mbps, 1),
            "connections": current.active_connections / max(baseline.active_connections, 1),
        }

        # Se qualsiasi metrica supera 3x la baseline → throttle
        max_score = max(scores.values())
        if max_score > 3.0:
            return ThrottleDecision(
                tenant_id=tenant_id,
                action="hard_throttle",
                rate_limit_multiplier=0.3,
                reason=f"Metrica {max(scores, key=scores.get)} a {max_score:.1f}x della baseline"
            )
        elif max_score > 2.0:
            return ThrottleDecision(
                tenant_id=tenant_id,
                action="soft_throttle",
                rate_limit_multiplier=0.6,
                reason=f"Metrica {max(scores, key=scores.get)} a {max_score:.1f}x della baseline"
            )
        return ThrottleDecision(tenant_id=tenant_id, action="none")
```

**Isolamento I/O a livello di database**:

```sql
-- PostgreSQL: limitare le risorse per ruolo tenant
-- (richiede pg_background_worker o cgroup integration)

-- Impostare work_mem per sessione tenant (limita memoria per query)
SET work_mem = '16MB';    -- Tenant free
SET work_mem = '64MB';    -- Tenant pro
SET work_mem = '256MB';   -- Tenant enterprise

-- Limitare il parallelismo per tenant
SET max_parallel_workers_per_gather = 0;  -- Tenant free
SET max_parallel_workers_per_gather = 2;  -- Tenant pro
SET max_parallel_workers_per_gather = 4;  -- Tenant enterprise

-- Timeout query per tier
SET statement_timeout = '5s';   -- Free
SET statement_timeout = '30s';  -- Pro
SET statement_timeout = '120s'; -- Enterprise

-- Monitoraggio: query più costose per tenant
SELECT
    tenant_id,
    count(*) AS total_queries,
    sum(total_exec_time) AS total_time_ms,
    avg(mean_exec_time) AS avg_time_ms,
    max(max_exec_time) AS max_time_ms
FROM pg_stat_statements pss
JOIN (
    SELECT DISTINCT tenant_id, usename
    FROM tenant_db_users
) t ON pss.userid = (SELECT oid FROM pg_roles WHERE rolname = t.usename)
GROUP BY tenant_id
ORDER BY total_time_ms DESC;
```

---

## Caching Tenant-Aware

Il caching in un sistema multi-tenant richiede attenzione speciale per evitare data leakage tramite cache e per garantire che le policy di eviction non penalizzino tenant con basso traffico.

### Strategia di Cache Key

```python
class TenantCacheKeyStrategy:
    """
    Genera cache key con isolamento tenant e supporto
    per invalidazione selettiva.
    """
    PREFIX = "mt"  # multi-tenant
    SEPARATOR = ":"

    @staticmethod
    def build_key(tenant_id: str, domain: str, resource_id: str,
                  version: int = 1) -> str:
        """
        Formato: mt:{tenant_id}:{domain}:{resource_id}:v{version}
        Esempio: mt:acme:project:123:v1
        """
        return f"{TenantCacheKeyStrategy.PREFIX}:{tenant_id}:{domain}:{resource_id}:v{version}"

    @staticmethod
    def build_list_key(tenant_id: str, domain: str,
                       filters_hash: str) -> str:
        """Per cache di risultati di lista filtrati."""
        return f"{TenantCacheKeyStrategy.PREFIX}:{tenant_id}:{domain}:list:{filters_hash}"

    @staticmethod
    def tenant_pattern(tenant_id: str) -> str:
        """Pattern per invalidare tutta la cache di un tenant."""
        return f"{TenantCacheKeyStrategy.PREFIX}:{tenant_id}:*"

    @staticmethod
    def domain_pattern(tenant_id: str, domain: str) -> str:
        """Pattern per invalidare un dominio specifico di un tenant."""
        return f"{TenantCacheKeyStrategy.PREFIX}:{tenant_id}:{domain}:*"
```

### Cache con Quota per Tenant

```python
class TenantAwareCache:
    """
    Cache Redis con:
    - Isolamento per tenant nelle chiavi
    - Quota di memoria per tenant (approssimata)
    - Eviction LRU per tenant (non globale)
    - Invalidazione bulk per tenant
    """
    def __init__(self, redis_client, quota_config: dict):
        self.redis = redis_client
        self.quota_config = quota_config  # {tier: max_keys}

    async def get(self, tenant_id: str, domain: str,
                  resource_id: str) -> dict | None:
        key = TenantCacheKeyStrategy.build_key(tenant_id, domain, resource_id)
        data = await self.redis.get(key)
        if data:
            # Aggiornare il timestamp di accesso per LRU tenant-scoped
            await self.redis.zadd(
                f"mt:{tenant_id}:_lru",
                {key: time.time()}
            )
        return json.loads(data) if data else None

    async def set(self, tenant_id: str, domain: str,
                  resource_id: str, value: dict,
                  ttl_seconds: int = 3600):
        key = TenantCacheKeyStrategy.build_key(tenant_id, domain, resource_id)

        # Verificare quota
        current_count = await self.redis.zcard(f"mt:{tenant_id}:_lru")
        max_keys = self.quota_config.get(
            self._get_tenant_tier(tenant_id), 1000
        )

        if current_count >= max_keys:
            # Evict la chiave meno recente di questo tenant
            oldest = await self.redis.zrange(
                f"mt:{tenant_id}:_lru", 0, 0
            )
            if oldest:
                await self.redis.delete(oldest[0])
                await self.redis.zrem(f"mt:{tenant_id}:_lru", oldest[0])

        await self.redis.setex(key, ttl_seconds, json.dumps(value))
        await self.redis.zadd(f"mt:{tenant_id}:_lru", {key: time.time()})

    async def invalidate_tenant(self, tenant_id: str):
        """Invalida tutta la cache di un tenant."""
        pattern = TenantCacheKeyStrategy.tenant_pattern(tenant_id)
        cursor = 0
        while True:
            cursor, keys = await self.redis.scan(
                cursor=cursor, match=pattern, count=100
            )
            if keys:
                await self.redis.delete(*keys)
            if cursor == 0:
                break
        await self.redis.delete(f"mt:{tenant_id}:_lru")
```

### Multi-Layer Caching per Tenant

| Livello | Tecnologia | TTL | Scope | Uso |
|---------|-----------|-----|-------|-----|
| L1 — In-process | HashMap/LRU locale | 30-60s | Singola istanza | Dati hot-path, configurazioni tenant |
| L2 — Distribuito | Redis/Memcached | 5-60min | Cluster-wide | Oggetti, liste, risultati query |
| L3 — CDN | CloudFront/Fastly | 1-24h | Edge globale | Asset statici, risposte API pubbliche |

```python
# Cache multi-layer con fallback
class MultiLayerTenantCache:
    def __init__(self, l1_cache, l2_cache):
        self.l1 = l1_cache  # In-process LRU
        self.l2 = l2_cache  # Redis

    async def get(self, tenant_id: str, domain: str, resource_id: str):
        # L1: in-process (più veloce, nessun network)
        l1_key = f"{tenant_id}:{domain}:{resource_id}"
        result = self.l1.get(l1_key)
        if result is not None:
            return result

        # L2: Redis
        result = await self.l2.get(tenant_id, domain, resource_id)
        if result is not None:
            # Popolare L1 per accessi futuri
            self.l1.set(l1_key, result, ttl=60)
            return result

        return None

    async def set(self, tenant_id: str, domain: str,
                  resource_id: str, value: dict):
        l1_key = f"{tenant_id}:{domain}:{resource_id}"
        self.l1.set(l1_key, value, ttl=60)
        await self.l2.set(tenant_id, domain, resource_id, value)
```

---

## Tenant Routing e Identificazione

### Strategie di Identificazione Tenant

L'identificazione del tenant nella richiesta è il primo passo di ogni operazione in un sistema multi-tenant. Esistono diverse strategie, ciascuna con i propri trade-off.

| Strategia | Esempio | Pro | Contro |
|-----------|---------|-----|--------|
| Subdomain | `acme.app.example.com` | Chiaro, isolabile per DNS, supporta certificati wildcard | Complessità DNS, CORS cross-subdomain |
| Path prefix | `app.example.com/tenant/acme/` | Semplice, nessuna configurazione DNS | Collision con route applicative, meno elegante |
| Header HTTP | `X-Tenant-ID: acme` | Flessibile, nessun impatto su URL | Non visibile al browser, richiede configurazione client |
| JWT claim | `{ "tenant_id": "acme" }` | Integrato nell'autenticazione | Richiede token per ogni richiesta, tenant fisso nel token |
| Query param | `?tenant=acme` | Semplice per testing | Insicuro per produzione, cache pollution |

### Middleware di Routing Completo

```python
import re
from dataclasses import dataclass

@dataclass
class TenantContext:
    tenant_id: str
    tenant_slug: str
    plan: str
    status: str
    region: str

class TenantRouter:
    """
    Identifica il tenant dalla richiesta usando multiple strategie
    con fallback chain.
    """
    STRATEGIES = ["subdomain", "header", "jwt", "path"]

    def __init__(self, tenant_registry, config):
        self.registry = tenant_registry
        self.config = config
        self.cache = {}  # Cache locale per slug → tenant

    async def resolve_tenant(self, request) -> TenantContext:
        tenant_slug = None

        # Strategia 1: Subdomain
        host = request.headers.get("Host", "")
        match = re.match(r'^([a-z0-9-]+)\.app\.example\.com$', host)
        if match:
            tenant_slug = match.group(1)

        # Strategia 2: Header (fallback per API)
        if not tenant_slug:
            tenant_slug = request.headers.get("X-Tenant-ID")

        # Strategia 3: JWT claim
        if not tenant_slug and hasattr(request, "auth"):
            tenant_slug = getattr(request.auth, "tenant_id", None)

        # Strategia 4: Path prefix
        if not tenant_slug:
            path_match = re.match(r'^/t/([a-z0-9-]+)/', request.path)
            if path_match:
                tenant_slug = path_match.group(1)

        if not tenant_slug:
            raise TenantNotIdentifiedError(
                "Impossibile identificare il tenant dalla richiesta"
            )

        # Risolvere il tenant dal registry
        tenant = await self._resolve_from_registry(tenant_slug)

        if tenant.status != "active":
            raise TenantInactiveError(
                f"Tenant {tenant_slug} è in stato {tenant.status}"
            )

        return tenant

    async def _resolve_from_registry(self, slug: str) -> TenantContext:
        if slug in self.cache:
            return self.cache[slug]

        tenant_data = await self.registry.get_by_slug(slug)
        if not tenant_data:
            raise TenantNotFoundError(f"Tenant '{slug}' non trovato")

        context = TenantContext(
            tenant_id=tenant_data.id,
            tenant_slug=slug,
            plan=tenant_data.plan,
            status=tenant_data.status,
            region=tenant_data.region
        )
        self.cache[slug] = context
        return context
```

### DNS e Certificati per Subdomain Tenant

```
# Configurazione DNS wildcard
*.app.example.com.  A  203.0.113.10

# Certificato wildcard con Let's Encrypt
certbot certonly \
  --dns-cloudflare \
  --dns-cloudflare-credentials /etc/cloudflare.ini \
  -d "*.app.example.com" \
  -d "app.example.com"
```

Per tenant con dominio personalizzato (es. `dashboard.acme.com`):

```python
class CustomDomainManager:
    async def register_custom_domain(self, tenant_id: str, domain: str):
        # 1. Verificare proprietà del dominio
        verification_token = generate_token()
        await self.registry.store_domain_verification(
            tenant_id, domain, verification_token
        )
        # Chiedere al tenant di aggiungere un record TXT:
        # _saas-verification.acme.com TXT "verify=abc123"

    async def verify_domain(self, tenant_id: str, domain: str) -> bool:
        expected = await self.registry.get_verification_token(tenant_id, domain)
        try:
            records = dns.resolver.resolve(
                f"_saas-verification.{domain}", "TXT"
            )
            for record in records:
                if expected in str(record):
                    await self._provision_certificate(domain)
                    await self._configure_routing(tenant_id, domain)
                    return True
        except dns.resolver.NXDOMAIN:
            pass
        return False

    async def _provision_certificate(self, domain: str):
        # Provisioning certificato via ACME/Let's Encrypt
        await self.acme_client.request_certificate(domain)

    async def _configure_routing(self, tenant_id: str, domain: str):
        # Aggiungere mapping dominio → tenant nel reverse proxy
        await self.proxy_config.add_route(domain, tenant_id)
```

---

## Tenant Provisioning e Lifecycle

### Provisioning Automatico

Il provisioning di un nuovo tenant deve essere completamente automatizzato. Il processo tipico include:

1. **Creazione dell'account**: registrazione dell'utente e creazione del record tenant nel registro centrale.
2. **Provisioning del data store**: creazione del database/schema/record per il nuovo tenant.
3. **Seed data**: popolazione dei dati iniziali (template, configurazioni default, dati di esempio).
4. **DNS/Routing**: configurazione del subdomain o del routing per il nuovo tenant.
5. **Notifiche**: invio dell'email di benvenuto e setup delle notifiche.

```python
# Provisioning completo di un nuovo tenant
class TenantProvisioner:
    async def provision(self, tenant_data: TenantCreateRequest) -> Tenant:
        # 1. Creare il record nel tenant registry
        tenant = await self.tenant_repo.create(tenant_data)

        # 2. Provisioning del data store
        if self.isolation_model == "database":
            await self._create_tenant_database(tenant)
        elif self.isolation_model == "schema":
            await self._create_tenant_schema(tenant)
        elif self.isolation_model == "shared":
            pass  # Nessuna azione necessaria per shared schema

        # 3. Seed data
        await self._seed_initial_data(tenant)

        # 4. DNS/Routing
        await self._configure_routing(tenant)

        # 5. Evento di provisioning completato
        await self.event_bus.publish(TenantProvisionedEvent(tenant))

        return tenant
```

### Tenant Lifecycle

Un tenant attraversa diversi stati durante il suo ciclo di vita:

```
Provisioning → Active → Suspended → Terminated → Deleted
                  ↑          ↓
                  └──────────┘ (Reactivation)
```

**Active**: il tenant è operativo e tutti i servizi sono disponibili.
**Suspended**: il tenant è sospeso (pagamento fallito, violazione ToS). I dati sono preservati ma l'accesso è limitato (tipicamente read-only o completamente bloccato).
**Terminated**: il tenant ha richiesto la cancellazione o è stato terminato. I dati vengono mantenuti per un periodo di grazia (tipicamente 30-90 giorni).
**Deleted**: i dati sono permanentemente eliminati. Questa operazione è irreversibile.

### Data Retention e Deletion

La cancellazione dei dati di un tenant deve essere completa e verificabile, specialmente in contesto GDPR:

```python
# Cancellazione completa dei dati di un tenant
class TenantDataPurger:
    async def purge_tenant(self, tenant_id: str):
        # 1. Verificare che il tenant sia in stato "terminated"
        tenant = await self.tenant_repo.get(tenant_id)
        assert tenant.status == TenantStatus.TERMINATED

        # 2. Cancellare i dati dal data store
        if self.isolation_model == "database":
            await self._drop_database(tenant_id)
        elif self.isolation_model == "schema":
            await self._drop_schema(tenant_id)
        elif self.isolation_model == "shared":
            await self._delete_all_rows(tenant_id)

        # 3. Cancellare file dal object storage
        await self._purge_object_storage(tenant_id)

        # 4. Cancellare dai sistemi di caching
        await self._purge_cache(tenant_id)

        # 5. Cancellare dai backup (se richiesto)
        await self._purge_backups(tenant_id)

        # 6. Registrare l'avvenuta cancellazione (audit log)
        await self._log_purge_completion(tenant_id)
```

---

## Sicurezza e Isolamento

### Difesa in Profondità

La sicurezza nella multi-tenancy deve seguire il principio di difesa in profondità — molteplici livelli di protezione indipendenti:

**Livello 1 — Application Layer**: ogni richiesta API deve identificare il tenant e filtrare i dati di conseguenza. Questo è il livello più basilare e il più soggetto a errori.

**Livello 2 — ORM/Query Layer**: filtri automatici a livello di ORM che aggiungono `WHERE tenant_id = ?` a ogni query. Riduce il rischio di errori umani nel codice applicativo.

**Livello 3 — Database Layer**: Row-Level Security (RLS) in PostgreSQL che enforcea l'isolamento a livello di database, indipendentemente dal codice applicativo.

**Livello 4 — Network Layer**: segmentazione di rete per isolare i tenant a livello di networking (rilevante per database-per-tenant).

### Testing dell'Isolamento

Il testing dell'isolamento è critico e deve essere parte integrante della suite di test:

```python
# Test di isolamento multi-tenant
class TestTenantIsolation:
    def test_tenant_cannot_access_other_tenant_data(self):
        # Setup: creare dati per due tenant
        tenant_a_user = create_user(tenant_id="tenant_a", email="a@a.com")
        tenant_b_user = create_user(tenant_id="tenant_b", email="b@b.com")

        # Act: tentare di accedere ai dati del tenant B dal contesto del tenant A
        with set_tenant_context("tenant_a"):
            users = User.query.all()

        # Assert: solo i dati del tenant A sono visibili
        assert len(users) == 1
        assert users[0].email == "a@a.com"

    def test_rls_prevents_cross_tenant_access(self):
        # Verificare che RLS blocca l'accesso anche con query raw
        with set_tenant_context("tenant_a"):
            result = db.execute(
                text("SELECT * FROM users WHERE email = 'b@b.com'")
            )
            assert result.rowcount == 0  # RLS deve bloccare
```

---

## Performance e Scalabilità

### Ottimizzazione degli Indici

Per il modello shared schema, la progettazione degli indici è critica:

```sql
-- Indice composito con tenant_id come primo campo
CREATE INDEX idx_projects_tenant_created
    ON projects(tenant_id, created_at DESC);

-- Per query che filtrano per tenant e poi cercano per nome
CREATE INDEX idx_projects_tenant_name
    ON projects(tenant_id, name);

-- Indice parziale per tenant con molti dati
CREATE INDEX idx_events_acme_recent
    ON events(created_at DESC)
    WHERE tenant_id = 'acme' AND created_at > NOW() - INTERVAL '30 days';
```

### Connection Pooling

Il connection pooling è una sfida significativa nella multi-tenancy, specialmente per i modelli database-per-tenant e schema-per-tenant. PgBouncer è lo strumento standard per PostgreSQL:

Per shared schema, PgBouncer funziona in modalità transaction pooling standard.
Per schema-per-tenant, è necessario configurare PgBouncer per eseguire `SET search_path` a ogni transazione, il che richiede la modalità session pooling (meno efficiente) o configurazioni custom.

### Caching Strategy

Un sistema di caching efficace per la multi-tenancy deve includere il tenant_id nella cache key:

```python
# Cache key con tenant isolation
def get_cache_key(tenant_id: str, resource: str, resource_id: str) -> str:
    return f"t:{tenant_id}:r:{resource}:id:{resource_id}"

# Esempio di utilizzo
cache_key = get_cache_key("acme", "project", "123")
cached_project = redis.get(cache_key)
```

---

## Migrazione tra Modelli

### Da Shared Schema a Schema-per-Tenant

La migrazione dal modello più semplice a uno più isolato è il percorso più comune quando i requisiti di isolamento aumentano (es. primo cliente enterprise con requisiti di compliance):

1. Creare lo schema target per il tenant da migrare
2. Copiare i dati dal shared schema allo schema dedicato
3. Aggiornare il routing per dirigere il tenant al nuovo schema
4. Verificare l'integrità dei dati
5. Eliminare i dati del tenant dallo shared schema

### Approccio Ibrido

L'approccio più pragmatico è un modello ibrido: shared schema per i tenant standard (free, starter, pro) e database/schema dedicato per i tenant enterprise. Questo ottimizza i costi per la maggioranza dei tenant mantenendo la possibilità di offrire isolamento premium ai clienti che lo richiedono.

---

## Best Practices

1. **Iniziare con shared schema**: per la maggior parte delle startup, il modello shared schema è il più appropriato nelle fasi iniziali. È il più semplice da implementare e il più efficiente in termini di costi.
2. **Implementare RLS fin dal primo giorno**: anche con shared schema, Row-Level Security fornisce un livello di protezione indipendente dal codice applicativo.
3. **Testare l'isolamento automaticamente**: includere test di isolamento nella CI/CD pipeline che verifichino che nessun tenant può accedere ai dati di un altro.
4. **Pianificare la migrazione a modelli più isolati**: progettare l'architettura in modo che sia possibile migrare tenant specifici a schema o database dedicati quando necessario.
5. **Monitorare per tenant**: implementare metriche per-tenant (query count, latenza, storage) per identificare noisy neighbors e ottimizzare le risorse.
6. **Includere tenant_id in ogni log entry**: per debugging e audit, ogni log entry deve includere il tenant_id.

---

## Troubleshooting

### Problema: Data Leakage tra Tenant

**Diagnosi**: un utente segnala di vedere dati che non gli appartengono. Questo è un incidente critico di sicurezza.

**Azione immediata**: isolare il tenant affetto, identificare l'endpoint responsabile, analizzare i log per determinare l'estensione del leak.

**Root cause comuni**: query senza filtro tenant_id, ORM che bypassa il filtro automatico (raw queries), bug nel middleware di tenant identification, cache senza tenant isolation nella key.

**Prevenzione**: implementare RLS come difesa in profondità, test automatici di isolamento, code review mandatory per qualsiasi query database.

### Problema: Performance Degradate per un Tenant Specifico

**Diagnosi**: un tenant segnala latenza elevata mentre gli altri tenant funzionano normalmente. Oppure un tenant sta causando degradazione per tutti.

**Soluzione**: verificare le query del tenant con `pg_stat_statements`, identificare query lente o full table scans, verificare gli indici, implementare rate limiting se necessario.

### Problema: Schema Migration Fallita su Alcuni Tenant

**Diagnosi**: in modello database-per-tenant o schema-per-tenant, una migrazione ha fallito su un sottoinsieme di tenant.

**Soluzione**: identificare i tenant in stato inconsistente, analizzare l'errore specifico, applicare la migrazione manualmente o rollback, implementare un sistema di migration tracking per tenant.

---

## Riferimenti

- AWS SaaS Factory: "Multi-Tenant Architecture" — Guida architetturale AWS per multi-tenancy
- Microsoft Azure: "Tenancy Models for SaaS Applications" — Confronto dei modelli su Azure
- PostgreSQL Documentation: "Row Security Policies" — Documentazione RLS nativa
- Tod Golding, "Building Multi-Tenant SaaS Architectures" (O'Reilly) — Testo di riferimento
- Citus Data (Microsoft): "Multi-Tenant SaaS Tutorial" — Implementazione pratica con PostgreSQL e Citus
- "Designing Data-Intensive Applications" — Martin Kleppmann, capitoli su partitioning e multi-tenancy
- OWASP: "Multi-Tenancy Security" — Considerazioni di sicurezza
- PlanetScale Blog: "Multi-Tenancy Strategies" — Approcci pratici con MySQL/Vitess
- Neon Postgres: "Schema-per-Tenant vs Shared Schema" — Analisi comparativa
- AWS re:Invent Talks: "SaaS Multi-Tenancy Deep Dive" — Presentazioni annuali su architetture multi-tenant
