# Tutorial 12 — Database in Python: SQLAlchemy 2.0, Alembic e Pattern Avanzati

> **Companion a:** `12-database.md`
> **Scope:** SQLAlchemy 2.0 ORM, sessioni async, Alembic migrations, repository pattern, query avanzate
> **Prerequisiti:** `tutorial_10_programmazione_asincrona.md`, `tutorial_11_web_framework.md`
> **Durata stimata:** 20-25 ore
> **Stack:** Python 3.12+, SQLAlchemy 2.0, asyncpg/aiosqlite, Alembic, PostgreSQL

---

## Mappa concettuale

```
SQLAlchemy 2.0 — Toolkit Database
│
├── Core — SQL Expression Language (basso livello)
│   ├── Engine + Connection
│   ├── Table, Column, MetaData
│   ├── select(), insert(), update(), delete()
│   └── Esecuzione diretta SQL
│
├── ORM — Object Relational Mapper (alto livello)
│   ├── DeclarativeBase — classe base modelli
│   ├── Mapped[T] — colonne con type hint
│   ├── relationship() — relazioni tra modelli
│   ├── Session (sync) / AsyncSession (async)
│   └── Query via select() non Query() (vecchio stile)
│
├── Async — supporto nativo
│   ├── create_async_engine() — engine asincrono
│   ├── async_sessionmaker — factory sessioni
│   ├── AsyncSession — sessione asincrona
│   └── asyncpg (PostgreSQL) / aiosqlite (SQLite)
│
├── Alembic — Migrazioni
│   ├── env.py — configurazione
│   ├── alembic revision --autogenerate
│   ├── alembic upgrade head
│   └── alembic downgrade -1
│
└── Pattern
    ├── Repository — astrazione accesso dati
    ├── Unit of Work — transazione come unità
    └── Query Object — costruzione query sicura
```

---

# Parte A — Fondamenti SQLAlchemy 2.0

---

## A1. Setup: engine e modelli dichiarativi

```python
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from datetime import datetime

# Engine asincrono — PostgreSQL con asyncpg
DATABASE_URL = "postgresql+asyncpg://utente:password@localhost:5432/miodb"

# SQLite per sviluppo/test
# DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,          # connessioni nel pool
    max_overflow=20,       # extra connessioni oltre pool_size
    pool_timeout=30,       # timeout acquisizione connessione
    pool_recycle=1800,     # ricicla connessioni dopo 30 min
    echo=False,            # True per loggare SQL (solo debug)
)

# Factory per sessioni asincrone
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # oggetti accessibili dopo commit
)

# Classe base per tutti i modelli
class Base(DeclarativeBase):
    pass

# Mixin con campi comuni
class TimestampMixin:
    creato_il: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now()
    )
    aggiornato_il: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), server_default=func.now()
    )
```

---

## A2. Definizione modelli con Mapped

```python
from sqlalchemy import String, Integer, Float, ForeignKey, Enum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

class StatoOrdine(str, enum.Enum):
    IN_ATTESA = "in_attesa"
    CONFERMATO = "confermato"
    SPEDITO = "spedito"
    CONSEGNATO = "consegnato"
    ANNULLATO = "annullato"

class Categoria(Base, TimestampMixin):
    __tablename__ = "categorie"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    descrizione: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relazione 1:N — una categoria ha N prodotti
    prodotti: Mapped[list["Prodotto"]] = relationship(back_populates="categoria")

class Prodotto(Base, TimestampMixin):
    __tablename__ = "prodotti"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    prezzo: Mapped[float] = mapped_column(Float, nullable=False)
    stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    categoria_id: Mapped[int | None] = mapped_column(ForeignKey("categorie.id"), nullable=True)

    # Relazione N:1 — molti prodotti a una categoria
    categoria: Mapped["Categoria | None"] = relationship(back_populates="prodotti")
    # Relazione N:N con Ordine tramite association table
    ordini: Mapped[list["ElementoOrdine"]] = relationship(back_populates="prodotto")

    __table_args__ = (
        Index("ix_prodotti_nome", "nome"),
        Index("ix_prodotti_categoria", "categoria_id"),
    )

class Ordine(Base, TimestampMixin):
    __tablename__ = "ordini"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    stato: Mapped[StatoOrdine] = mapped_column(
        Enum(StatoOrdine), default=StatoOrdine.IN_ATTESA, nullable=False
    )
    totale: Mapped[float] = mapped_column(Float, nullable=False)

    elementi: Mapped[list["ElementoOrdine"]] = relationship(back_populates="ordine")

class ElementoOrdine(Base):
    __tablename__ = "elementi_ordine"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ordine_id: Mapped[int] = mapped_column(ForeignKey("ordini.id"))
    prodotto_id: Mapped[int] = mapped_column(ForeignKey("prodotti.id"))
    quantita: Mapped[int] = mapped_column(Integer, nullable=False)
    prezzo_unitario: Mapped[float] = mapped_column(Float, nullable=False)

    ordine: Mapped[Ordine] = relationship(back_populates="elementi")
    prodotto: Mapped[Prodotto] = relationship(back_populates="ordini")
```

---

## A3. CRUD con AsyncSession

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Creazione tabelle (solo sviluppo — in produzione usare Alembic)
async def crea_tabelle():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# CREATE
async def crea_prodotto(
    session: AsyncSession,
    nome: str,
    prezzo: float,
    stock: int = 0,
) -> Prodotto:
    prodotto = Prodotto(nome=nome, prezzo=prezzo, stock=stock)
    session.add(prodotto)
    await session.flush()   # assegna id senza commit
    await session.refresh(prodotto)   # ricarica da db
    return prodotto

# READ — singolo per id
async def leggi_prodotto(session: AsyncSession, prodotto_id: int) -> Prodotto | None:
    stmt = select(Prodotto).where(Prodotto.id == prodotto_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

# READ — lista con filtri
async def lista_prodotti(
    session: AsyncSession,
    categoria_id: int | None = None,
    prezzo_max: float | None = None,
    skip: int = 0,
    limit: int = 20,
) -> list[Prodotto]:
    stmt = select(Prodotto).offset(skip).limit(limit)
    if categoria_id is not None:
        stmt = stmt.where(Prodotto.categoria_id == categoria_id)
    if prezzo_max is not None:
        stmt = stmt.where(Prodotto.prezzo <= prezzo_max)
    stmt = stmt.order_by(Prodotto.nome)

    result = await session.execute(stmt)
    return list(result.scalars().all())

# UPDATE
async def aggiorna_stock(
    session: AsyncSession,
    prodotto_id: int,
    nuovo_stock: int,
) -> Prodotto | None:
    prodotto = await leggi_prodotto(session, prodotto_id)
    if prodotto is None:
        return None
    prodotto.stock = nuovo_stock
    await session.flush()
    return prodotto

# DELETE
async def elimina_prodotto(session: AsyncSession, prodotto_id: int) -> bool:
    prodotto = await leggi_prodotto(session, prodotto_id)
    if prodotto is None:
        return False
    await session.delete(prodotto)
    return True

# Uso con transazione
async def esempio_transazione():
    async with AsyncSessionLocal() as session:
        async with session.begin():   # commit/rollback automatici
            p = await crea_prodotto(session, "Laptop", 999.99, stock=10)
            await aggiorna_stock(session, p.id, 8)
        # commit avvenuto uscendo dal blocco begin
    # sessione chiusa uscendo dal blocco outer with
```

---

# Parte B — Query avanzate

---

## B1. Join, aggregazioni, subquery

```python
from sqlalchemy import select, func, and_, or_, case
from sqlalchemy.orm import joinedload, selectinload

# JOIN esplicito
async def prodotti_con_categoria(session: AsyncSession) -> list:
    stmt = (
        select(Prodotto, Categoria.nome.label("categoria_nome"))
        .join(Categoria, Prodotto.categoria_id == Categoria.id, isouter=True)
        .order_by(Prodotto.nome)
    )
    result = await session.execute(stmt)
    return [(p, cat_nome) for p, cat_nome in result]

# Aggregazioni — GROUP BY
async def totale_per_categoria(session: AsyncSession) -> list:
    stmt = (
        select(
            Categoria.nome,
            func.count(Prodotto.id).label("n_prodotti"),
            func.avg(Prodotto.prezzo).label("prezzo_medio"),
            func.sum(Prodotto.stock).label("stock_totale"),
        )
        .join(Prodotto, isouter=True)
        .group_by(Categoria.nome)
        .having(func.count(Prodotto.id) > 0)
        .order_by(func.avg(Prodotto.prezzo).desc())
    )
    result = await session.execute(stmt)
    return result.all()

# Caricamento relazioni — eager loading
async def ordini_con_dettagli(session: AsyncSession) -> list[Ordine]:
    stmt = (
        select(Ordine)
        .options(
            selectinload(Ordine.elementi).selectinload(ElementoOrdine.prodotto)
        )
        .order_by(Ordine.creato_il.desc())
        .limit(50)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())

# CASE expression
async def prodotti_per_fascia(session: AsyncSession) -> list:
    fascia = case(
        (Prodotto.prezzo < 50, "economico"),
        (Prodotto.prezzo < 200, "medio"),
        else_="premium",
    ).label("fascia_prezzo")

    stmt = select(Prodotto.nome, Prodotto.prezzo, fascia)
    result = await session.execute(stmt)
    return result.all()
```

---

## B2. Alembic — Migrazioni

```bash
# Setup iniziale
pip install alembic
alembic init migrations

# Struttura creata:
# migrations/
#   env.py          — configurazione migrazioni
#   versions/       — file di migrazione
# alembic.ini       — configurazione principale
```

```python
# migrations/env.py — configurazione per async
import asyncio
from logging.config import fileConfig
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context
from app.models import Base  # importa i modelli

config = context.config
fileConfig(config.config_file_name)
target_metadata = Base.metadata

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online():
    engine = create_async_engine(config.get_main_option("sqlalchemy.url"))
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
```

```python
# Migrazione generata automaticamente: alembic revision --autogenerate -m "aggiungi_tabella_utenti"
# migrations/versions/20240101_aggiungi_tabella_utenti.py

from alembic import op
import sqlalchemy as sa

revision = "abc123"
down_revision = None   # prima migrazione
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "utenti",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("nome", sa.String(100), nullable=False),
        sa.Column("email", sa.String(200), unique=True, nullable=False),
        sa.Column("creato_il", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_utenti_email", "utenti", ["email"], unique=True)

def downgrade() -> None:
    op.drop_index("ix_utenti_email", "utenti")
    op.drop_table("utenti")
```

```bash
# Comandi comuni
alembic upgrade head       # applica tutte le migrazioni
alembic upgrade +1         # applica una migrazione
alembic downgrade -1       # annulla ultima migrazione
alembic current            # migrazione corrente
alembic history            # storico migrazioni
alembic stamp head         # marca come applicata senza eseguire
```

---

## B3. Repository Pattern

```python
from abc import ABC, abstractmethod
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

class ProdottoRepository(ABC):
    @abstractmethod
    async def trova_per_id(self, id: int) -> Prodotto | None: ...
    @abstractmethod
    async def trova_tutti(self, skip: int, limit: int) -> list[Prodotto]: ...
    @abstractmethod
    async def crea(self, dati: dict) -> Prodotto: ...
    @abstractmethod
    async def aggiorna(self, id: int, dati: dict) -> Prodotto | None: ...
    @abstractmethod
    async def elimina(self, id: int) -> bool: ...

class SqlAlchemyProdottoRepository(ProdottoRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def trova_per_id(self, id: int) -> Prodotto | None:
        stmt = select(Prodotto).where(Prodotto.id == id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def trova_tutti(self, skip: int = 0, limit: int = 20) -> list[Prodotto]:
        stmt = select(Prodotto).offset(skip).limit(limit).order_by(Prodotto.id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def crea(self, dati: dict) -> Prodotto:
        p = Prodotto(**dati)
        self._session.add(p)
        await self._session.flush()
        await self._session.refresh(p)
        return p

    async def aggiorna(self, id: int, dati: dict) -> Prodotto | None:
        p = await self.trova_per_id(id)
        if p is None:
            return None
        for chiave, valore in dati.items():
            setattr(p, chiave, valore)
        await self._session.flush()
        return p

    async def elimina(self, id: int) -> bool:
        p = await self.trova_per_id(id)
        if p is None:
            return False
        await self._session.delete(p)
        return True

# Repository in-memory per test
class InMemoryProdottoRepository(ProdottoRepository):
    def __init__(self) -> None:
        self._store: dict[int, Prodotto] = {}
        self._counter = 0

    async def trova_per_id(self, id: int) -> Prodotto | None:
        return self._store.get(id)

    async def trova_tutti(self, skip: int = 0, limit: int = 20) -> list[Prodotto]:
        items = list(self._store.values())
        return items[skip:skip+limit]

    async def crea(self, dati: dict) -> Prodotto:
        self._counter += 1
        p = Prodotto(id=self._counter, **dati)
        self._store[p.id] = p
        return p

    async def aggiorna(self, id: int, dati: dict) -> Prodotto | None:
        p = self._store.get(id)
        if p is None:
            return None
        for k, v in dati.items():
            setattr(p, k, v)
        return p

    async def elimina(self, id: int) -> bool:
        return self._store.pop(id, None) is not None
```

---

# Parte C — Integrazione con FastAPI

---

## C1. Dependency injection sessione

```python
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession

app = FastAPI()

async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

@app.get("/prodotti/{id}")
async def leggi_prodotto_endpoint(
    id: int,
    session: AsyncSession = Depends(get_session),
) -> dict:
    p = await leggi_prodotto(session, id)
    if p is None:
        from fastapi import HTTPException
        raise HTTPException(404, f"Prodotto {id} non trovato")
    return {"id": p.id, "nome": p.nome, "prezzo": p.prezzo}

@app.post("/prodotti", status_code=201)
async def crea_prodotto_endpoint(
    dati: dict,
    session: AsyncSession = Depends(get_session),
) -> dict:
    async with session.begin():
        p = await crea_prodotto(session, dati["nome"], dati["prezzo"])
    return {"id": p.id, "nome": p.nome}
```

---

## C2. Service layer con Unit of Work

```python
class OrdineService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def crea_ordine(
        self,
        prodotti: list[tuple[int, int]],   # (prodotto_id, quantita)
    ) -> Ordine:
        """Crea ordine, scala stock, valida disponibilità."""
        async with self._session.begin():
            totale = 0.0
            elementi = []

            for prod_id, qty in prodotti:
                stmt = select(Prodotto).where(Prodotto.id == prod_id)
                result = await self._session.execute(stmt)
                p = result.scalar_one_or_none()

                if p is None:
                    raise ValueError(f"Prodotto {prod_id} non trovato")
                if p.stock < qty:
                    raise ValueError(f"Stock insufficiente per {p.nome}: {p.stock} < {qty}")

                p.stock -= qty
                totale += p.prezzo * qty
                elementi.append(ElementoOrdine(
                    prodotto_id=prod_id,
                    quantita=qty,
                    prezzo_unitario=p.prezzo,
                ))

            ordine = Ordine(totale=round(totale, 2))
            self._session.add(ordine)
            await self._session.flush()

            for el in elementi:
                el.ordine_id = ordine.id
            self._session.add_all(elementi)

        return ordine
```

---

# Parte D — Test del database

---

## D1. Test con database SQLite in memoria

```python
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.models import Base

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="function")
async def engine_test():
    engine = create_async_engine(TEST_DB_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture
async def session_test(engine_test):
    factory = async_sessionmaker(engine_test, expire_on_commit=False)
    async with factory() as session:
        yield session

@pytest.mark.anyio
async def test_crea_e_leggi_prodotto(session_test: AsyncSession):
    p = await crea_prodotto(session_test, "Mouse", 29.99, stock=5)
    await session_test.commit()

    trovato = await leggi_prodotto(session_test, p.id)
    assert trovato is not None
    assert trovato.nome == "Mouse"
    assert trovato.prezzo == 29.99
    assert trovato.stock == 5

@pytest.mark.anyio
async def test_aggiorna_stock(session_test: AsyncSession):
    p = await crea_prodotto(session_test, "Tastiera", 79.99, stock=10)
    await session_test.commit()

    aggiornato = await aggiorna_stock(session_test, p.id, 7)
    await session_test.commit()

    assert aggiornato is not None
    assert aggiornato.stock == 7

@pytest.mark.anyio
async def test_elimina_prodotto(session_test: AsyncSession):
    p = await crea_prodotto(session_test, "Monitor", 299.99)
    await session_test.commit()

    ok = await elimina_prodotto(session_test, p.id)
    await session_test.commit()

    assert ok is True
    assert await leggi_prodotto(session_test, p.id) is None
```

---

# Parte E — Riepilogo

## Tabella quick reference

| Operazione | SQLAlchemy 2.0 |
|---|---|
| Select singolo | `select(Model).where(Model.id == id)` → `scalar_one_or_none()` |
| Select lista | `select(Model).offset(n).limit(k)` → `scalars().all()` |
| Insert | `session.add(obj)` + `flush()` |
| Update | `setattr(obj, "campo", valore)` + `flush()` |
| Delete | `session.delete(obj)` |
| Commit | `await session.commit()` |
| Rollback | `await session.rollback()` |
| Transazione | `async with session.begin():` |
| Join | `.join(AltroModel, cond)` |
| Aggregate | `func.count()`, `func.avg()`, `func.sum()` |
| Eager load | `.options(selectinload(rel))` |

## Anti-pattern

- **N+1 query** — caricare relazioni in loop invece di usare `selectinload`/`joinedload`
- **Sessione condivisa tra richieste** — ogni request deve avere la propria sessione
- **Dimenticare commit** — `flush()` non è `commit()`; senza commit le modifiche vengono perse
- **Query non limitate** — sempre usare `.limit()` o paginazione su query che ritornano liste
- **DDL manuale in produzione** — usare sempre Alembic per modifiche schema

## Prossimi passi

- `tutorial_27_ci_cd.md` — pipeline che esegue migrazioni Alembic automaticamente
- `tutorial_31_otel.md` — tracing delle query SQL con SQLAlchemy instrumentor OTel
