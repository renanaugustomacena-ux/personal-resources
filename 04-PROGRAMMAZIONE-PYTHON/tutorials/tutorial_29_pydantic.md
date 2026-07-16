# Tutorial 29 — Pydantic v2: Validazione, Serializzazione, Settings

> **Companion a:** `29-pydantic.md`
> **Scope:** BaseModel, Field, validator, serializzazione, pydantic-settings, custom types
> **Prerequisiti:** `tutorial_09_type_hints_mypy.md`
> **Durata stimata:** 12-16 ore
> **Stack:** Python 3.12+, Pydantic v2.7+, pydantic-settings 2.x

---

## Mappa concettuale

```
Pydantic v2
│
├── BaseModel — schema + validazione
│   ├── Mapped Python types — str, int, float, bool
│   ├── Tipi complessi — list, dict, set, tuple
│   ├── Annotated types — UUID, datetime, HttpUrl, EmailStr
│   ├── Optional / Union (|) — nullable
│   └── Nested models — composizione
│
├── Field() — metadati e constraint
│   ├── default, default_factory
│   ├── description — OpenAPI docs
│   ├── min_length, max_length (str)
│   ├── ge, le, gt, lt (numeri)
│   ├── pattern (regex)
│   └── alias, validation_alias
│
├── Validator decoratori
│   ├── @field_validator — singolo campo
│   ├── @model_validator(mode="before") — prima di parse
│   ├── @model_validator(mode="after") — post-costruzione
│   └── @computed_field — campo calcolato
│
├── Serializzazione
│   ├── model_dump() — dict Python
│   ├── model_dump_json() — JSON string
│   ├── model_json_schema() — JSON Schema
│   └── include/exclude/by_alias
│
├── Custom Types
│   ├── Annotated[T, Validator]
│   ├── RootModel — tipo singolo validato
│   └── Generic models — Model[T]
│
└── pydantic-settings
    ├── BaseSettings — config da env
    ├── .env file
    └── Nested settings
```

---

# Parte A — BaseModel e Field

---

## A1. Modelli base con vincoli

```python
from pydantic import BaseModel, Field, EmailStr, HttpUrl
from pydantic import field_validator, model_validator, computed_field
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID, uuid4
from typing import Annotated

# Tipo personalizzato per nome
NomeStr = Annotated[str, Field(min_length=1, max_length=100, strip_whitespace=True)]

class IndirizzoSpedizione(BaseModel):
    via: str = Field(min_length=5, max_length=200)
    numero_civico: str = Field(min_length=1, max_length=10)
    citta: str = Field(min_length=2, max_length=100)
    cap: str = Field(pattern=r"^\d{5}$")
    paese: str = Field(default="IT", min_length=2, max_length=2)

class Utente(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    nome: NomeStr
    cognome: NomeStr
    email: EmailStr
    eta: int = Field(ge=0, le=150)
    bio: str | None = Field(default=None, max_length=1000)
    sito: HttpUrl | None = None
    tag: list[str] = Field(default_factory=list, max_length=10)
    indirizzo: IndirizzoSpedizione | None = None
    creato_il: datetime = Field(default_factory=datetime.now)

    # Computed field — calcolato da altri campi
    @computed_field
    @property
    def nome_completo(self) -> str:
        return f"{self.nome} {self.cognome}"

# Parsing da dict
dati = {
    "nome": "  Mario  ",   # strip_whitespace lo pulisce
    "cognome": "Rossi",
    "email": "mario.rossi@example.com",
    "eta": 30,
}
u = Utente(**dati)
print(u.nome)            # "Mario" (strip applicato)
print(u.nome_completo)   # "Mario Rossi"
print(u.id)              # UUID generato automaticamente

# Parsing da JSON
u2 = Utente.model_validate_json('{"nome": "Alice", "cognome": "B", "email": "a@b.com", "eta": 25}')
print(u2)
```

---

## A2. Validatori

```python
from pydantic import BaseModel, Field, field_validator, model_validator
import re

class RegistrazioneUtente(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: str
    password: str = Field(min_length=8)
    conferma_password: str
    data_nascita: date | None = None

    @field_validator("username")
    @classmethod
    def username_alfanumerico(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_\-]+$", v):
            raise ValueError("Username: solo lettere, numeri, _ e -")
        return v.lower()

    @field_validator("email")
    @classmethod
    def email_valida(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Email non valida")
        return v

    @field_validator("password")
    @classmethod
    def password_sicura(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Almeno una maiuscola")
        if not re.search(r"\d", v):
            raise ValueError("Almeno un numero")
        if not re.search(r"[!@#$%^&*]", v):
            raise ValueError("Almeno un carattere speciale (!@#$%^&*)")
        return v

    @model_validator(mode="after")
    def password_uguale(self) -> "RegistrazioneUtente":
        if self.password != self.conferma_password:
            raise ValueError("Le password non coincidono")
        return self

    @model_validator(mode="after")
    def eta_minima(self) -> "RegistrazioneUtente":
        if self.data_nascita:
            from datetime import date
            eta = (date.today() - self.data_nascita).days // 365
            if eta < 18:
                raise ValueError("Devi avere almeno 18 anni")
        return self

# Gestione errori di validazione
from pydantic import ValidationError

try:
    reg = RegistrazioneUtente(
        username="mario!!",
        email="non-email",
        password="semplice",
        conferma_password="diversa",
    )
except ValidationError as e:
    print(f"Errori ({e.error_count()}):")
    for errore in e.errors():
        print(f"  [{errore['loc']}] {errore['msg']}")
```

---

# Parte B — Serializzazione avanzata

---

## B1. model_dump e configurazione

```python
from pydantic import BaseModel, Field, AliasGenerator, ConfigDict
from pydantic.alias_generators import to_camel

class ProdottoAPI(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,          # accetta sia alias che nome Python
        from_attributes=True,           # crea da ORM/SQLAlchemy object
        str_strip_whitespace=True,      # strip automatico stringhe
        str_min_length=1,               # no stringhe vuote
        alias_generator=to_camel,       # nome_python → nomePython (JSON camelCase)
    )

    id: int
    nome_prodotto: str
    prezzo_unitario: float
    disponibile: bool = True
    tag_prodotto: list[str] = Field(default_factory=list)

p = ProdottoAPI(id=1, nomeProdotto="Mouse", prezzoUnitario=29.99)

# Serializzazione
print(p.model_dump())           # nomi Python: nome_prodotto
print(p.model_dump(by_alias=True))   # camelCase: nomeProdotto
print(p.model_dump(exclude={"id"}))
print(p.model_dump(include={"nome_prodotto", "prezzo_unitario"}))
print(p.model_dump(exclude_none=True, exclude_defaults=True))

json_str = p.model_dump_json(by_alias=True)   # JSON diretto

# JSON Schema per OpenAPI
schema = ProdottoAPI.model_json_schema()
print(schema)
```

---

## B2. Custom types e RootModel

```python
from pydantic import BaseModel, GetCoreSchemaHandler
from pydantic_core import core_schema
from typing import Annotated, Any

# Custom type con validatore
class CodiceFiscale(str):
    """Stringa validata come codice fiscale italiano."""

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_after_validator_function(
            cls._valida,
            core_schema.str_schema(to_upper=True),
            serialization=core_schema.plain_serializer_function_ser_schema(str),
        )

    @classmethod
    def _valida(cls, v: str) -> "CodiceFiscale":
        v = v.upper().strip()
        if len(v) != 16:
            raise ValueError("Il codice fiscale deve essere di 16 caratteri")
        import re
        if not re.match(r"^[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]$", v):
            raise ValueError("Formato codice fiscale non valido")
        return cls(v)

class Cittadino(BaseModel):
    nome: str
    codice_fiscale: CodiceFiscale

# RootModel — modello con tipo radice singolo
from pydantic import RootModel

class ListaId(RootModel[list[int]]):
    """Lista di ID validata."""

    def __iter__(self):
        return iter(self.root)

    def __len__(self) -> int:
        return len(self.root)

lista = ListaId.model_validate([1, 2, 3])
print(len(lista))   # 3

# Generic Model
from typing import TypeVar, Generic

T = TypeVar("T")

class RisultatoPaginato(BaseModel, Generic[T]):
    dati: list[T]
    totale: int
    pagina: int = 1
    per_pagina: int = 20

    @computed_field
    @property
    def n_pagine(self) -> int:
        return (self.totale + self.per_pagina - 1) // self.per_pagina

class ProdottoSemplice(BaseModel):
    id: int
    nome: str

prodotti_paginati = RisultatoPaginato[ProdottoSemplice](
    dati=[ProdottoSemplice(id=1, nome="Mouse")],
    totale=100,
)
```

---

# Parte C — pydantic-settings

---

## C1. Configurazione applicazione

```python
# pip install pydantic-settings
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, PostgresDsn, RedisDsn
from functools import lru_cache

class ImpostazioniDatabase(BaseSettings):
    host: str = "localhost"
    porta: int = 5432
    nome: str = "appdb"
    utente: str = "app"
    password: str = Field(min_length=8)
    pool_size: int = Field(default=10, ge=1, le=100)

    model_config = SettingsConfigDict(env_prefix="DB_")
    # Legge: DB_HOST, DB_PORTA, DB_NOME, DB_UTENTE, DB_PASSWORD

    @property
    def url(self) -> str:
        return f"postgresql+asyncpg://{self.utente}:{self.password}@{self.host}:{self.porta}/{self.nome}"

class ImpostazioniApp(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_nested_delimiter="__",   # APP__DB__HOST → app.db.host
    )

    app_nome: str = "MiaApp"
    debug: bool = False
    secret_key: str = Field(min_length=32)
    cors_origins: list[str] = ["http://localhost:3000"]
    log_level: str = Field(default="info", pattern="^(debug|info|warning|error|critical)$")

    # Sezione database
    db: ImpostazioniDatabase = Field(default_factory=ImpostazioniDatabase)

    # Sezione Redis
    redis_url: str = "redis://localhost:6379/0"

# Singleton delle impostazioni (caricate una volta)
@lru_cache(maxsize=1)
def get_settings() -> ImpostazioniApp:
    return ImpostazioniApp()

settings = get_settings()

# In FastAPI
from fastapi import Depends
def get_app_settings(s: ImpostazioniApp = Depends(get_settings)) -> ImpostazioniApp:
    return s
```

---

# Parte D — Riepilogo

## Pydantic v2 cheatsheet

```python
# Creazione
m = MioModello(**dati_dict)
m = MioModello.model_validate(dati_dict)      # con alias
m = MioModello.model_validate_json(json_str)  # da JSON

# Serializzazione
m.model_dump()
m.model_dump(by_alias=True, exclude_none=True)
m.model_dump_json()
m.model_json_schema()

# Copia con modifiche
m2 = m.model_copy(update={"campo": "nuovo_valore"})

# Configurazione BaseModel
class Mio(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,       # ORM
        populate_by_name=True,      # alias + nome originale
        str_strip_whitespace=True,  # strip automatico
        alias_generator=to_camel,   # CamelCase automatico
    )
```

## Anti-pattern

- **Validazione manuale** — se hai già Pydantic, usalo
- **model.dict()** — deprecato in v2, usare `model_dump()`
- **Validator che modifica il tipo** — restituire sempre il tipo annotato nel validator
- **Settings senza env_prefix** — variabili ambiente ambigue in container

## Prossimi passi

- `tutorial_11_web_framework.md` — FastAPI usa Pydantic nativamente
- `tutorial_12_database.md` — ORM models con `from_attributes=True`
