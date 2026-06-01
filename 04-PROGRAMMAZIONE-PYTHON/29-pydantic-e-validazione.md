---
corso: "Programmazione Python"
fase: "3 — Librerie e Framework"
modulo: "29"
titolo: "Pydantic e Validazione Dati"
versione: "Pydantic 2.x"
livello: "Intermedio"
prerequisiti:
  - "02 — OOP"
  - "09 — Type Hints e Mypy"
  - "07 — Error Handling e Logging"
obiettivi:
  - "Padroneggiare BaseModel, Field e validatori custom in Pydantic v2"
  - "Implementare serializzazione/deserializzazione JSON, YAML e TOML"
  - "Utilizzare discriminated union e modelli generici"
  - "Configurare Pydantic Settings per gestione env e configurazioni"
  - "Integrare Pydantic con FastAPI, SQLAlchemy e database"
  - "Validare dati in pipeline ETL e boundary di sistema"
tag: [pydantic, validazione, serializzazione, BaseModel, settings, type-safety, FastAPI]
---

# Pydantic e Validazione Dati — Guida Completa

> **Modulo 29** · **Aggiornamento:** 2026-05-24 · **Versione:** Pydantic 2.x

> ### Obiettivi di apprendimento
>
> **Prerequisiti:** [OOP](02-oop.md), [Type Hints](09-type-hints-e-mypy.md), [Error Handling](07-error-handling-e-logging.md)
>
> Al termine di questo modulo saprai:
> 1. Padroneggiare `BaseModel`, `Field` e validatori custom in Pydantic v2
> 2. Implementare serializzazione/deserializzazione JSON, YAML e TOML
> 3. Utilizzare discriminated union e modelli generici
> 4. Configurare Pydantic Settings per gestione env e configurazioni
> 5. Integrare Pydantic con FastAPI, SQLAlchemy e database
> 6. Validare dati in pipeline ETL e boundary di sistema
>
> **Tempo stimato:** 5-7 ore · **Livello:** Intermedio

## Idee guida
1. **Pydantic v2 ~10x faster di v1 (Rust core).**
2. **`model_validate` (v2) > `parse_obj` (v1 legacy).**
3. **`Field(default_factory=...)` per mutable default.**
4. **`@field_validator` (v2) > `@validator` (v1).**
5. **`ConfigDict` (v2) > `Config` class (v1).**


## Indice

1. [Panoramica](#panoramica)
2. [Fondamenti Pydantic](#fondamenti-pydantic)
3. [Validazione Avanzata](#validazione-avanzata)
4. [Modelli Complessi](#modelli-complessi)
5. [Serializzazione](#serializzazione)
6. [Configurazione con Pydantic](#configurazione-con-pydantic)
7. [Integrazione](#integrazione)
8. [Pattern Pratici](#pattern-pratici)
9. [Best Practices](#best-practices)

---

## Panoramica

### Cos'e Pydantic e Perche e Importante

Pydantic e la libreria di validazione dati piu diffusa nell'ecosistema Python. Il suo scopo principale e garantire che i dati in ingresso a un programma rispettino una struttura e dei vincoli ben definiti, sfruttando le **type annotations** native di Python come unica fonte di verita.

In un mondo dove le applicazioni ricevono dati da sorgenti eterogenee — richieste HTTP, file di configurazione, database, code di messaggi — la validazione manuale diventa rapidamente ingestibile e soggetta a errori. Pydantic risolve questo problema permettendo di dichiarare **modelli** (classi Python) le cui istanze sono sempre valide per costruzione: se i dati non rispettano lo schema, un errore dettagliato viene sollevato automaticamente al momento della creazione.

```python
from pydantic import BaseModel

class Utente(BaseModel):
    nome: str
    eta: int
    email: str

# Validazione automatica
utente = Utente(nome="Marco", eta=30, email="marco@example.com")

# Errore se i dati non sono validi
try:
    utente_invalido = Utente(nome="Marco", eta="non_un_numero", email="marco@example.com")
except Exception as e:
    print(e)
    # 1 validation error for Utente
    # eta
    #   Input should be a valid integer, unable to parse string as an integer
```

### Pydantic v2 — Core basato su Rust

Con il rilascio della **versione 2**, Pydantic ha subito una riscrittura radicale. Il nucleo di validazione e serializzazione e stato riscritto in **Rust** tramite la libreria `pydantic-core`, ottenendo miglioramenti di performance compresi tra 5x e 50x rispetto alla v1. Questa scelta architetturale ha reso Pydantic adatto anche a scenari ad alto throughput, come microservizi che processano migliaia di richieste al secondo, pipeline di data engineering e applicazioni real-time.

L'installazione e immediata:

```bash
pip install pydantic

# Con supporto email validation
pip install pydantic[email]

# Con pydantic-settings per la gestione configurazioni
pip install pydantic-settings
```

Le differenze principali tra v1 e v2 includono:

| Caratteristica | Pydantic v1 | Pydantic v2 |
|---|---|---|
| Core di validazione | Python puro | Rust (`pydantic-core`) |
| Performance | Buona | 5-50x piu veloce |
| Metodo di export | `.dict()`, `.json()` | `.model_dump()`, `.model_dump_json()` |
| Configurazione | classe `Config` interna | `model_config = ConfigDict(...)` |
| Validatori | `@validator`, `@root_validator` | `@field_validator`, `@model_validator` |
| Schema JSON | `.schema()` | `.model_json_schema()` |

```python
# Pydantic v2 — sintassi moderna
from pydantic import BaseModel, ConfigDict

class Prodotto(BaseModel):
    model_config = ConfigDict(strict=False, frozen=False)

    nome: str
    prezzo: float
    disponibile: bool = True
```

### Casi d'Uso Principali

Pydantic trova applicazione in numerosi contesti:

- **Validazione API**: e il motore di validazione predefinito di FastAPI, gestendo automaticamente request body, query parameters e response models.
- **Gestione configurazioni**: tramite `BaseSettings`, Pydantic carica e valida configurazioni da variabili d'ambiente, file `.env`, file JSON e TOML.
- **Data parsing e trasformazione**: converte dati grezzi (dizionari, JSON, dati da database) in oggetti Python fortemente tipizzati.
- **Schema generation**: genera automaticamente JSON Schema compatibili con OpenAPI/Swagger.
- **Validazione form**: valida dati provenienti da form web o interfacce utente.

---

## Fondamenti Pydantic

### BaseModel

`BaseModel` e la classe base da cui derivano tutti i modelli Pydantic. Ogni attributo di classe con type annotation diventa un campo del modello, soggetto a validazione automatica.

#### Definizione e Istanziazione

```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class Articolo(BaseModel):
    titolo: str
    contenuto: str
    autore: str
    pubblicato: bool = False
    data_creazione: datetime = datetime.now()
    tag: list[str] = []
    note: Optional[str] = None

# Istanziazione con keyword arguments
articolo = Articolo(
    titolo="Introduzione a Pydantic",
    contenuto="Pydantic e una libreria...",
    autore="Marco Rossi"
)

print(articolo.titolo)        # "Introduzione a Pydantic"
print(articolo.pubblicato)    # False (valore di default)
print(articolo.tag)           # []

# Istanziazione da dizionario
dati = {
    "titolo": "Secondo Articolo",
    "contenuto": "Contenuto dell'articolo...",
    "autore": "Luca Bianchi",
    "tag": ["python", "pydantic"]
}
articolo2 = Articolo(**dati)
```

#### Metodi Principali del Modello

Pydantic v2 espone una serie di metodi con il prefisso `model_` per operazioni comuni:

```python
from pydantic import BaseModel

class Indirizzo(BaseModel):
    via: str
    citta: str
    cap: str
    provincia: str

indirizzo = Indirizzo(via="Via Roma 1", citta="Milano", cap="20121", provincia="MI")

# model_dump() — converte in dizionario
dizionario = indirizzo.model_dump()
print(dizionario)
# {'via': 'Via Roma 1', 'citta': 'Milano', 'cap': '20121', 'provincia': 'MI'}

# model_dump_json() — serializza in stringa JSON
json_str = indirizzo.model_dump_json()
print(json_str)
# '{"via":"Via Roma 1","citta":"Milano","cap":"20121","provincia":"MI"}'

# model_validate() — crea istanza da dizionario con validazione
nuovo_indirizzo = Indirizzo.model_validate({
    "via": "Corso Italia 5",
    "citta": "Roma",
    "cap": "00185",
    "provincia": "RM"
})

# model_validate_json() — crea istanza da stringa JSON
json_input = '{"via": "Via Napoli 10", "citta": "Torino", "cap": "10100", "provincia": "TO"}'
indirizzo_da_json = Indirizzo.model_validate_json(json_input)

# model_json_schema() — genera lo JSON Schema del modello
schema = Indirizzo.model_json_schema()
print(schema)
# {
#   'properties': {
#     'via': {'title': 'Via', 'type': 'string'},
#     'citta': {'title': 'Citta', 'type': 'string'},
#     'cap': {'title': 'Cap', 'type': 'string'},
#     'provincia': {'title': 'Provincia', 'type': 'string'}
#   },
#   'required': ['via', 'citta', 'cap', 'provincia'],
#   'title': 'Indirizzo',
#   'type': 'object'
# }
```

#### Copia con Modifiche

Per creare una copia di un modello con alcuni campi modificati, si usa `model_copy()`:

```python
articolo_originale = Articolo(
    titolo="Titolo Originale",
    contenuto="Contenuto originale...",
    autore="Marco Rossi"
)

# Crea una copia con titolo modificato
articolo_modificato = articolo_originale.model_copy(update={
    "titolo": "Titolo Modificato",
    "pubblicato": True
})

print(articolo_originale.titolo)   # "Titolo Originale"
print(articolo_modificato.titolo)  # "Titolo Modificato"

# Deep copy — copia anche gli oggetti annidati
articolo_deep = articolo_originale.model_copy(deep=True)
```

#### Immutabilita con `frozen`

Per creare modelli immutabili (i cui campi non possono essere modificati dopo la creazione), si utilizza l'opzione `frozen` nella configurazione:

```python
from pydantic import BaseModel, ConfigDict

class Coordinate(BaseModel):
    model_config = ConfigDict(frozen=True)

    latitudine: float
    longitudine: float

coord = Coordinate(latitudine=45.4642, longitudine=9.1900)

# Tentativo di modifica solleva un errore
try:
    coord.latitudine = 41.9028
except Exception as e:
    print(e)
    # Instance is frozen
```

### Tipi Supportati

Pydantic supporta nativamente un vasto insieme di tipi Python e tipi specializzati.

#### Tipi Standard

```python
from pydantic import BaseModel
from typing import Optional, Union, Literal
from enum import Enum

class TipiBase(BaseModel):
    testo: str                    # stringa
    numero_intero: int            # intero
    numero_decimale: float        # decimale
    flag: bool                    # booleano
    valore_nullo: None            # sempre None
```

#### Tipi Collezione

```python
class Collezioni(BaseModel):
    lista_nomi: list[str]                    # lista di stringhe
    dizionario: dict[str, int]               # dizionario str -> int
    insieme: set[str]                        # insieme di stringhe univoche
    tupla_fissa: tuple[str, int, float]      # tupla con tipi specifici
    tupla_variabile: tuple[int, ...]         # tupla di lunghezza variabile
    lista_annidata: list[list[int]]          # lista di liste di interi
```

#### Optional, Union e Literal

```python
class TipiAvanzati(BaseModel):
    # Optional — puo essere None
    soprannome: Optional[str] = None

    # Union — accetta piu tipi
    identificativo: Union[str, int]

    # Sintassi moderna (Python 3.10+)
    valore: str | int | None = None

    # Literal — solo valori specifici ammessi
    ruolo: Literal["admin", "utente", "ospite"]
    priorita: Literal[1, 2, 3]

# Valido
t = TipiAvanzati(identificativo="ABC123", ruolo="admin", priorita=1)

# Errore: "moderatore" non e tra i valori ammessi
try:
    t2 = TipiAvanzati(identificativo=42, ruolo="moderatore", priorita=1)
except Exception as e:
    print(e)
```

#### Enum

```python
from enum import Enum

class StatoOrdine(str, Enum):
    IN_ATTESA = "in_attesa"
    CONFERMATO = "confermato"
    SPEDITO = "spedito"
    CONSEGNATO = "consegnato"
    ANNULLATO = "annullato"

class Ordine(BaseModel):
    codice: str
    stato: StatoOrdine

ordine = Ordine(codice="ORD-001", stato="confermato")
print(ordine.stato)          # StatoOrdine.CONFERMATO
print(ordine.stato.value)    # "confermato"
```

#### Tipi Data e Ora

```python
from datetime import datetime, date, time, timedelta
from pydantic import BaseModel

class Evento(BaseModel):
    nome: str
    data_ora: datetime
    data: date
    orario: time
    durata: timedelta

evento = Evento(
    nome="Conferenza Python",
    data_ora="2026-06-15T10:00:00",       # parsing automatico da stringa
    data="2026-06-15",                      # parsing automatico
    orario="10:00:00",                      # parsing automatico
    durata=timedelta(hours=2, minutes=30)
)
print(evento.data_ora)  # 2026-06-15 10:00:00
```

#### Tipi Specializzati di Pydantic

```python
from uuid import UUID
from pathlib import Path
from pydantic import BaseModel, EmailStr, SecretStr, HttpUrl, AnyUrl

class Configurazione(BaseModel):
    id_sessione: UUID
    percorso_file: Path
    url_api: HttpUrl
    sito_web: AnyUrl

class Account(BaseModel):
    email: EmailStr          # richiede: pip install pydantic[email]
    password: SecretStr      # nasconde il valore in repr/str

account = Account(email="utente@example.com", password="segreta123")
print(account)
# email='utente@example.com' password=SecretStr('**********')

# Per accedere al valore segreto
print(account.password.get_secret_value())  # "segreta123"
```

#### Tipi Vincolati (Constrained Types)

```python
from pydantic import BaseModel, conint, confloat, constr

class ProdottoVincolato(BaseModel):
    nome: constr(min_length=1, max_length=100)
    prezzo: confloat(gt=0, le=99999.99)
    quantita: conint(ge=0, le=10000)
    codice: constr(pattern=r'^[A-Z]{3}-\d{4}$')

prodotto = ProdottoVincolato(
    nome="Widget",
    prezzo=29.99,
    quantita=100,
    codice="ABC-1234"
)
```

### Field()

La funzione `Field()` permette di aggiungere metadati, vincoli e comportamenti personalizzati ai singoli campi di un modello.

#### Default e Default Factory

```python
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import uuid4

class Documento(BaseModel):
    # Valore di default semplice
    versione: int = Field(default=1)

    # Default factory — funzione chiamata per ogni istanza
    id: str = Field(default_factory=lambda: str(uuid4()))
    creato_il: datetime = Field(default_factory=datetime.now)

    # Campo obbligatorio (nessun default)
    titolo: str = Field(...)  # equivalente a non specificare Field()
```

#### Alias

Gli alias permettono di accettare dati con nomi di campo diversi da quelli del modello Python:

```python
from pydantic import BaseModel, Field, ConfigDict

class RispostaAPI(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    # alias — usato sia per validazione che serializzazione
    nome_utente: str = Field(alias="userName")

    # validation_alias — usato solo per l'input
    indirizzo_email: str = Field(validation_alias="emailAddress")

    # serialization_alias — usato solo per l'output
    codice_fiscale: str = Field(serialization_alias="taxCode")

# Accetta il nome con alias
risposta = RispostaAPI(
    userName="marco_r",
    emailAddress="marco@example.com",
    codice_fiscale="RSSMRC90A01H501Z"
)

# Serializzazione con alias
print(risposta.model_dump(by_alias=True))
# {'userName': 'marco_r', 'indirizzo_email': 'marco@example.com', 'taxCode': 'RSSMRC90A01H501Z'}
```

#### Metadati e Documentazione

```python
class ProdottoCatalogo(BaseModel):
    nome: str = Field(
        title="Nome Prodotto",
        description="Il nome commerciale del prodotto",
        examples=["Laptop Pro 15", "Mouse Wireless X"],
        json_schema_extra={"x-frontend-widget": "text-input"}
    )
    prezzo: float = Field(
        title="Prezzo",
        description="Prezzo in euro, IVA inclusa",
        examples=[999.99, 29.50]
    )
```

#### Vincoli Numerici e su Stringhe

```python
class Registrazione(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=30,
        pattern=r'^[a-zA-Z0-9_]+$'
    )
    eta: int = Field(gt=0, le=150)             # 0 < eta <= 150
    altezza_cm: float = Field(ge=30, lt=300)   # 30 <= altezza < 300
    numero_pari: int = Field(multiple_of=2)    # deve essere multiplo di 2
```

#### Esclusione e Rappresentazione

```python
class UtenteInterno(BaseModel):
    nome: str
    email: str

    # Escluso dalla serializzazione con model_dump()
    password_hash: str = Field(exclude=True)

    # Non mostrato nella rappresentazione repr()
    token_interno: str = Field(repr=False)

utente = UtenteInterno(
    nome="Anna",
    email="anna@example.com",
    password_hash="hashed_pw",
    token_interno="tok_123"
)
print(utente.model_dump())
# {'nome': 'Anna', 'email': 'anna@example.com'}

print(utente)
# UtenteInterno(nome='Anna', email='anna@example.com', password_hash='hashed_pw')
# token_interno non appare nella repr
```

#### Strict Mode vs Lax Mode

Per default, Pydantic opera in **lax mode**: tenta di convertire i dati al tipo corretto (es. la stringa `"42"` viene convertita in intero `42`). In **strict mode**, nessuna conversione automatica viene effettuata e i tipi devono corrispondere esattamente:

```python
from pydantic import BaseModel, ConfigDict

class ModelloLax(BaseModel):
    valore: int

class ModelloStrict(BaseModel):
    model_config = ConfigDict(strict=True)
    valore: int

# Lax mode — conversione automatica
lax = ModelloLax(valore="42")
print(lax.valore)  # 42 (intero)

# Strict mode — errore se il tipo non corrisponde
try:
    strict = ModelloStrict(valore="42")
except Exception as e:
    print(e)  # Input should be a valid integer
```

Si puo anche abilitare lo strict mode su singoli campi usando `Field(strict=True)`, senza renderlo globale per l'intero modello.

#### Gestione Errori di Validazione

Quando la validazione fallisce, Pydantic solleva un `ValidationError` che contiene informazioni dettagliate su tutti gli errori riscontrati:

```python
from pydantic import BaseModel, ValidationError, Field

class Prodotto(BaseModel):
    nome: str = Field(min_length=1)
    prezzo: float = Field(gt=0)
    quantita: int = Field(ge=0)

try:
    p = Prodotto(nome="", prezzo=-10, quantita=-5)
except ValidationError as e:
    # Numero totale di errori
    print(f"Errori trovati: {e.error_count()}")

    # Lista strutturata degli errori
    for errore in e.errors():
        print(f"  Campo: {errore['loc']}")
        print(f"  Tipo:  {errore['type']}")
        print(f"  Msg:   {errore['msg']}")
        print()

    # Rappresentazione JSON degli errori
    print(e.json(indent=2))
```

Ogni errore contiene: `loc` (percorso del campo, inclusi campi annidati), `msg` (messaggio leggibile), `type` (codice errore macchina-leggibile) e `input` (il valore che ha causato l'errore).

---

## Validazione Avanzata

### field_validator

Il decoratore `@field_validator` permette di definire logica di validazione personalizzata per uno o piu campi.

#### Validazione Base

```python
from pydantic import BaseModel, field_validator

class Utente(BaseModel):
    nome: str
    email: str
    eta: int

    @field_validator('nome')
    @classmethod
    def nome_non_vuoto(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Il nome non puo essere vuoto o composto solo da spazi')
        return v.strip().title()

    @field_validator('email')
    @classmethod
    def email_valida(cls, v: str) -> str:
        if '@' not in v:
            raise ValueError('Email deve contenere il carattere @')
        return v.lower()

    @field_validator('eta')
    @classmethod
    def eta_valida(cls, v: int) -> int:
        if v < 0 or v > 150:
            raise ValueError('Eta deve essere compresa tra 0 e 150')
        return v

utente = Utente(nome="  marco rossi  ", email="MARCO@Example.Com", eta=30)
print(utente.nome)   # "Marco Rossi"  (normalizzato)
print(utente.email)  # "marco@example.com" (normalizzato)
```

#### mode='before' vs mode='after'

La modalita `before` esegue il validatore **prima** della validazione di tipo Pydantic, mentre `after` (il default) lo esegue **dopo**:

```python
from pydantic import BaseModel, field_validator

class Prodotto(BaseModel):
    prezzo: float
    codice: str

    # Eseguito PRIMA della validazione di tipo
    # Riceve il dato grezzo (potrebbe essere qualsiasi tipo)
    @field_validator('prezzo', mode='before')
    @classmethod
    def converti_prezzo(cls, v):
        if isinstance(v, str):
            # Gestisce formato italiano "29,99"
            v = v.replace(',', '.')
        return v

    # Eseguito DOPO la validazione di tipo
    # v e gia un float valido
    @field_validator('prezzo', mode='after')
    @classmethod
    def prezzo_positivo(cls, v: float) -> float:
        if v <= 0:
            raise ValueError('Il prezzo deve essere positivo')
        return round(v, 2)

    @field_validator('codice', mode='before')
    @classmethod
    def normalizza_codice(cls, v):
        if isinstance(v, str):
            return v.upper().strip()
        return v

prodotto = Prodotto(prezzo="29,99", codice="  abc-123  ")
print(prodotto.prezzo)  # 29.99
print(prodotto.codice)  # "ABC-123"
```

#### Validazione su Campi Multipli

```python
class Anagrafica(BaseModel):
    nome: str
    cognome: str
    codice_fiscale: str

    # Un singolo validatore applicato a piu campi
    @field_validator('nome', 'cognome')
    @classmethod
    def capitalizza(cls, v: str) -> str:
        return v.strip().title()

    @field_validator('codice_fiscale')
    @classmethod
    def valida_cf(cls, v: str) -> str:
        v = v.upper().strip()
        if len(v) != 16:
            raise ValueError('Il codice fiscale deve avere 16 caratteri')
        return v
```

#### Validatori Riutilizzabili

```python
from pydantic import BaseModel, field_validator

def non_vuoto(v: str) -> str:
    """Validatore riutilizzabile per stringhe non vuote."""
    if not v.strip():
        raise ValueError('Il campo non puo essere vuoto')
    return v.strip()

def in_range(minimo: int, massimo: int):
    """Factory di validatori per range numerici."""
    def validatore(v: int) -> int:
        if v < minimo or v > massimo:
            raise ValueError(f'Il valore deve essere compreso tra {minimo} e {massimo}')
        return v
    return validatore

class ModuloIscrizione(BaseModel):
    nome: str
    cognome: str
    eta: int

    validatore_nome = field_validator('nome', 'cognome')(classmethod(non_vuoto))

    @field_validator('eta')
    @classmethod
    def valida_eta(cls, v: int) -> int:
        return in_range(18, 99)(v)
```

### model_validator

Il decoratore `@model_validator` opera sull'intero modello, consentendo validazioni che coinvolgono piu campi contemporaneamente.

#### mode='before'

In modalita `before`, il validatore riceve i dati grezzi prima di qualsiasi validazione di campo:

```python
from pydantic import BaseModel, model_validator

class Pagamento(BaseModel):
    metodo: str
    numero_carta: str | None = None
    iban: str | None = None

    @model_validator(mode='before')
    @classmethod
    def preprocessa_dati(cls, data):
        """Preprocessa i dati prima della validazione dei campi."""
        if isinstance(data, dict):
            # Normalizza il metodo di pagamento
            metodo = data.get('metodo', '').lower()
            data['metodo'] = metodo
        return data
```

#### mode='after'

In modalita `after`, il validatore riceve il modello gia costruito e validato:

```python
from pydantic import BaseModel, model_validator

class IntervalloDate(BaseModel):
    data_inizio: date
    data_fine: date
    descrizione: str = ""

    @model_validator(mode='after')
    def data_fine_dopo_inizio(self):
        if self.data_fine < self.data_inizio:
            raise ValueError('La data di fine deve essere successiva alla data di inizio')
        return self

class CredenzialiRegistrazione(BaseModel):
    password: str
    conferma_password: str
    email: str

    @model_validator(mode='after')
    def password_corrispondono(self):
        if self.password != self.conferma_password:
            raise ValueError('Le password non corrispondono')
        return self

    @model_validator(mode='after')
    def password_non_contiene_email(self):
        parte_locale = self.email.split('@')[0].lower()
        if parte_locale in self.password.lower():
            raise ValueError('La password non deve contenere il nome utente email')
        return self
```

#### Validazione Condizionale

```python
class Spedizione(BaseModel):
    tipo: Literal["standard", "express", "ritiro_in_sede"]
    indirizzo: str | None = None
    citta: str | None = None
    cap: str | None = None
    punto_ritiro: str | None = None

    @model_validator(mode='after')
    def valida_dati_spedizione(self):
        if self.tipo in ("standard", "express"):
            if not all([self.indirizzo, self.citta, self.cap]):
                raise ValueError(
                    'Per spedizioni standard/express, indirizzo, citta e cap sono obbligatori'
                )
        elif self.tipo == "ritiro_in_sede":
            if not self.punto_ritiro:
                raise ValueError(
                    'Per il ritiro in sede, il punto di ritiro e obbligatorio'
                )
        return self
```

### Custom Types

Pydantic v2 permette di creare tipi personalizzati riutilizzabili tramite `Annotated` e i validatori associati.

#### Annotated con AfterValidator e BeforeValidator

```python
from typing import Annotated
from pydantic import BaseModel, AfterValidator, BeforeValidator

def converti_a_maiuscolo(v: str) -> str:
    return v.upper()

def rimuovi_spazi(v: str) -> str:
    return v.strip()

def valida_partita_iva(v: str) -> str:
    if len(v) != 11 or not v.isdigit():
        raise ValueError('La partita IVA deve essere composta da 11 cifre')
    return v

# Tipi personalizzati riutilizzabili
CodiceMaiuscolo = Annotated[str, BeforeValidator(rimuovi_spazi), AfterValidator(converti_a_maiuscolo)]
PartitaIVA = Annotated[str, BeforeValidator(rimuovi_spazi), AfterValidator(valida_partita_iva)]

class Azienda(BaseModel):
    ragione_sociale: str
    codice: CodiceMaiuscolo
    partita_iva: PartitaIVA

azienda = Azienda(
    ragione_sociale="Esempio S.r.l.",
    codice="  abc-123  ",
    partita_iva="  12345678901  "
)
print(azienda.codice)       # "ABC-123"
print(azienda.partita_iva)  # "12345678901"
```

#### Tipi Annotated Riutilizzabili con Vincoli

```python
from typing import Annotated
from pydantic import BaseModel, Field

# Definizioni di tipo riutilizzabili
NomePersona = Annotated[str, Field(min_length=1, max_length=100)]
Percentuale = Annotated[float, Field(ge=0, le=100)]
CodicePostale = Annotated[str, Field(pattern=r'^\d{5}$')]
Prezzo = Annotated[float, Field(gt=0, le=999999.99)]

class Fattura(BaseModel):
    cliente: NomePersona
    importo: Prezzo
    iva_percentuale: Percentuale
    cap_destinazione: CodicePostale
```

---

## Modelli Complessi

I modelli complessi permettono di rappresentare strutture dati sofisticate, combinando composizione, ereditarieta e polimorfismo in modo type-safe.

### Nested Models (Modelli Annidati)

Pydantic supporta nativamente la composizione di modelli, dove un modello contiene campi il cui tipo e un altro modello. Questo e il meccanismo principale per costruire schemi di dati gerarchici, come un ordine che contiene righe, ciascuna con un prodotto:

```python
from pydantic import BaseModel

class Indirizzo(BaseModel):
    via: str
    civico: str
    citta: str
    cap: str
    provincia: str

class Contatto(BaseModel):
    tipo: Literal["telefono", "email", "pec"]
    valore: str

class Azienda(BaseModel):
    ragione_sociale: str
    partita_iva: str
    sede_legale: Indirizzo                     # modello annidato singolo
    sedi_operative: list[Indirizzo] = []       # lista di modelli annidati
    contatti: list[Contatto] = []

# Istanziazione — i dizionari annidati vengono validati automaticamente
azienda = Azienda(
    ragione_sociale="Tech Solutions S.r.l.",
    partita_iva="12345678901",
    sede_legale={
        "via": "Via Roma",
        "civico": "42",
        "citta": "Milano",
        "cap": "20121",
        "provincia": "MI"
    },
    contatti=[
        {"tipo": "email", "valore": "info@techsolutions.it"},
        {"tipo": "telefono", "valore": "+39 02 1234567"}
    ]
)
```

#### Modelli Auto-referenzianti

```python
from __future__ import annotations
from pydantic import BaseModel

class Categoria(BaseModel):
    nome: str
    descrizione: str = ""
    sotto_categorie: list[Categoria] = []

# Struttura ad albero
catalogo = Categoria(
    nome="Elettronica",
    sotto_categorie=[
        Categoria(
            nome="Computer",
            sotto_categorie=[
                Categoria(nome="Laptop"),
                Categoria(nome="Desktop"),
            ]
        ),
        Categoria(
            nome="Smartphone",
            sotto_categorie=[
                Categoria(nome="Android"),
                Categoria(nome="iOS"),
            ]
        ),
    ]
)

# model_rebuild() necessario in alcuni casi con forward references
Categoria.model_rebuild()
```

### Discriminated Unions

Le Discriminated Unions permettono di distinguere tra piu modelli in un campo `Union` basandosi sul valore di un campo discriminatore:

```python
from pydantic import BaseModel, Discriminator, Tag
from typing import Annotated, Literal, Union

class PagamentoCarta(BaseModel):
    tipo: Literal["carta"]
    numero_carta: str
    scadenza: str
    cvv: str

class PagamentoBonifico(BaseModel):
    tipo: Literal["bonifico"]
    iban: str
    intestatario: str

class PagamentoPayPal(BaseModel):
    tipo: Literal["paypal"]
    email: str

# Union discriminata — Pydantic usa il campo 'tipo' per scegliere il modello
TipoPagamento = Annotated[
    Union[PagamentoCarta, PagamentoBonifico, PagamentoPayPal],
    Discriminator('tipo')
]

class Ordine(BaseModel):
    codice_ordine: str
    importo: float
    pagamento: TipoPagamento

# Pydantic sceglie automaticamente il modello giusto
ordine_carta = Ordine(
    codice_ordine="ORD-001",
    importo=99.99,
    pagamento={"tipo": "carta", "numero_carta": "4111111111111111", "scadenza": "12/28", "cvv": "123"}
)

ordine_paypal = Ordine(
    codice_ordine="ORD-002",
    importo=49.99,
    pagamento={"tipo": "paypal", "email": "utente@example.com"}
)

print(type(ordine_carta.pagamento))   # <class 'PagamentoCarta'>
print(type(ordine_paypal.pagamento))  # <class 'PagamentoPayPal'>
```

### Generics

I modelli generici permettono di parametrizzare i modelli con tipi variabili:

```python
from pydantic import BaseModel
from typing import TypeVar, Generic

T = TypeVar('T')

class RispostaPaginata(BaseModel, Generic[T]):
    dati: list[T]
    pagina: int
    per_pagina: int
    totale: int
    pagine_totali: int

class Utente(BaseModel):
    nome: str
    email: str

class Prodotto(BaseModel):
    nome: str
    prezzo: float

# Riutilizzo del modello generico con tipi diversi
risposta_utenti = RispostaPaginata[Utente](
    dati=[
        Utente(nome="Marco", email="marco@example.com"),
        Utente(nome="Anna", email="anna@example.com"),
    ],
    pagina=1,
    per_pagina=10,
    totale=2,
    pagine_totali=1
)

risposta_prodotti = RispostaPaginata[Prodotto](
    dati=[
        Prodotto(nome="Laptop", prezzo=999.99),
    ],
    pagina=1,
    per_pagina=10,
    totale=1,
    pagine_totali=1
)
```

### Computed Fields

I campi calcolati sono proprieta derivate da altri campi del modello, inclusi automaticamente nella serializzazione:

```python
from pydantic import BaseModel, computed_field

class RigaFattura(BaseModel):
    descrizione: str
    quantita: int
    prezzo_unitario: float
    aliquota_iva: float = 22.0

    @computed_field
    @property
    def imponibile(self) -> float:
        return round(self.quantita * self.prezzo_unitario, 2)

    @computed_field
    @property
    def iva(self) -> float:
        return round(self.imponibile * self.aliquota_iva / 100, 2)

    @computed_field
    @property
    def totale(self) -> float:
        return round(self.imponibile + self.iva, 2)

riga = RigaFattura(descrizione="Servizio consulenza", quantita=10, prezzo_unitario=100.0)
print(riga.model_dump())
# {
#   'descrizione': 'Servizio consulenza',
#   'quantita': 10,
#   'prezzo_unitario': 100.0,
#   'aliquota_iva': 22.0,
#   'imponibile': 1000.0,
#   'iva': 220.0,
#   'totale': 1220.0
# }
```

---

## Serializzazione

### model_dump()

Il metodo `model_dump()` converte un modello in un dizionario Python, con numerose opzioni per controllare l'output:

```python
from pydantic import BaseModel, Field
from datetime import datetime

class EventoLog(BaseModel):
    timestamp: datetime
    livello: str
    messaggio: str
    sorgente: str = "app"
    dettagli: dict | None = None
    id_correlazione: str | None = None

evento = EventoLog(
    timestamp=datetime(2026, 3, 28, 10, 30),
    livello="ERROR",
    messaggio="Connessione al database fallita",
    dettagli={"host": "db.example.com", "porta": 5432}
)

# Serializzazione completa
print(evento.model_dump())

# include — solo i campi specificati
print(evento.model_dump(include={'timestamp', 'livello', 'messaggio'}))
# {'timestamp': datetime(2026, 3, 28, 10, 30), 'livello': 'ERROR', 'messaggio': '...'}

# exclude — esclude i campi specificati
print(evento.model_dump(exclude={'dettagli', 'id_correlazione'}))

# exclude_none — esclude i campi con valore None
print(evento.model_dump(exclude_none=True))
# id_correlazione non appare

# exclude_unset — esclude i campi che non sono stati impostati esplicitamente
print(evento.model_dump(exclude_unset=True))
# sorgente non appare (ha usato il default) ma dettagli si

# exclude_defaults — esclude i campi con il valore uguale al default
print(evento.model_dump(exclude_defaults=True))

# mode='json' — converte tutti i tipi in tipi JSON-compatibili
print(evento.model_dump(mode='json'))
# Il datetime diventa stringa ISO: "2026-03-28T10:30:00"

# by_alias — usa gli alias come chiavi
# (richiede che i campi abbiano alias definiti)
```

### model_dump_json() e Serializzatori Personalizzati

```python
from pydantic import BaseModel, field_serializer
from datetime import datetime
from decimal import Decimal

class Transazione(BaseModel):
    id: int
    importo: Decimal
    valuta: str = "EUR"
    data: datetime
    note: str | None = None

    @field_serializer('importo')
    def serializza_importo(self, v: Decimal) -> str:
        """Serializza il Decimal come stringa con 2 decimali."""
        return f"{v:.2f}"

    @field_serializer('data')
    def serializza_data(self, v: datetime) -> str:
        """Serializza la data in formato italiano."""
        return v.strftime("%d/%m/%Y %H:%M")

transazione = Transazione(
    id=1,
    importo=Decimal("1234.50"),
    data=datetime(2026, 3, 28, 14, 30)
)

print(transazione.model_dump_json(indent=2))
# {
#   "id": 1,
#   "importo": "1234.50",
#   "valuta": "EUR",
#   "data": "28/03/2026 14:30",
#   "note": null
# }

# Escludere None dalla serializzazione JSON
print(transazione.model_dump_json(exclude_none=True, indent=2))
```

#### PlainSerializer e WrapSerializer

```python
from typing import Annotated
from pydantic import BaseModel
from pydantic.functional_serializers import PlainSerializer, WrapSerializer

# PlainSerializer — sostituisce completamente la serializzazione
ImportoFormattato = Annotated[
    float,
    PlainSerializer(lambda v: f"EUR {v:.2f}", return_type=str)
]

# WrapSerializer — avvolge la serializzazione di default
def arrotonda_e_serializza(v, handler):
    """Arrotonda a 2 decimali, poi delega al serializzatore di default."""
    return handler(round(v, 2))

PrezzoArrotondato = Annotated[
    float,
    WrapSerializer(arrotonda_e_serializza)
]

class Preventivo(BaseModel):
    descrizione: str
    importo: ImportoFormattato
    sconto: PrezzoArrotondato

prev = Preventivo(descrizione="Servizio", importo=1500.456, sconto=10.567)
print(prev.model_dump())
# {'descrizione': 'Servizio', 'importo': 'EUR 1500.46', 'sconto': 10.57}
```

### TypeAdapter

`TypeAdapter` permette di validare e serializzare tipi che non sono modelli Pydantic, come liste, dizionari e tipi primitivi:

```python
from pydantic import TypeAdapter, BaseModel

# Validazione di una lista di modelli
class Contatto(BaseModel):
    nome: str
    telefono: str

adapter_lista = TypeAdapter(list[Contatto])

dati_grezzi = [
    {"nome": "Marco", "telefono": "+39 333 1234567"},
    {"nome": "Anna", "telefono": "+39 333 7654321"},
]

# Validazione
contatti = adapter_lista.validate_python(dati_grezzi)
print(contatti)  # [Contatto(nome='Marco', ...), Contatto(nome='Anna', ...)]

# Serializzazione
json_output = adapter_lista.dump_json(contatti, indent=2)
print(json_output)

# Validazione da JSON
json_input = '[{"nome": "Luca", "telefono": "+39 333 0000000"}]'
contatti_da_json = adapter_lista.validate_json(json_input)

# TypeAdapter con dizionari
adapter_dizionario = TypeAdapter(dict[str, list[int]])
dati = adapter_dizionario.validate_python({"numeri": [1, 2, 3], "punteggi": [85, 90, 95]})

# TypeAdapter per generare JSON Schema
schema = adapter_lista.json_schema()
print(schema)
```

---

## Configurazione con Pydantic

### BaseSettings

`pydantic-settings` estende Pydantic con la capacita di caricare configurazioni da variabili d'ambiente, file `.env` e altre sorgenti, con validazione automatica.

```bash
pip install pydantic-settings
```

#### Configurazione Base

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix='DB_',           # prefisso per le variabili d'ambiente
        env_file='.env',            # file .env da caricare
        env_file_encoding='utf-8',
        extra='ignore'              # ignora variabili extra
    )

    host: str = "localhost"
    porta: int = Field(default=5432, alias='DB_PORT')
    nome: str = "mydb"
    utente: str = "postgres"
    password: str
    pool_size: int = 5

# Con variabili d'ambiente:
# DB_HOST=db.production.com
# DB_PORTA=5432
# DB_NOME=produzione_db
# DB_UTENTE=app_user
# DB_PASSWORD=secret_password
# DB_POOL_SIZE=20

# Carica automaticamente dalle variabili d'ambiente
db_settings = DatabaseSettings()
```

#### File .env

```env
# .env
APP_NAME=MiaApplicazione
APP_DEBUG=true
APP_SECRET_KEY=super-secret-key-123
APP_ALLOWED_ORIGINS=["http://localhost:3000","https://miosito.it"]

DB_HOST=localhost
DB_PORT=5432
DB_NAME=myapp
DB_USER=postgres
DB_PASSWORD=password123

REDIS_URL=redis://localhost:6379/0
```

#### Configurazioni Annidate

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel, Field

class DatabaseConfig(BaseModel):
    host: str = "localhost"
    port: int = 5432
    name: str = "mydb"
    user: str = "postgres"
    password: str = ""

class RedisConfig(BaseModel):
    url: str = "redis://localhost:6379/0"
    max_connections: int = 10

class LoggingConfig(BaseModel):
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: str | None = None

class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_nested_delimiter='__',  # DB__HOST diventa database.host
        extra='ignore'
    )

    app_name: str = "MiaApp"
    debug: bool = False
    secret_key: str

    database: DatabaseConfig = DatabaseConfig()
    redis: RedisConfig = RedisConfig()
    logging: LoggingConfig = LoggingConfig()

# Con variabili d'ambiente:
# DATABASE__HOST=db.example.com
# DATABASE__PORT=5432
# DATABASE__PASSWORD=secret
# REDIS__URL=redis://cache.example.com:6379/0
# SECRET_KEY=my-secret
```

#### Sorgenti di Configurazione Multiple

Pydantic Settings supporta diverse sorgenti di configurazione con priorita configurabile:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=('.env', '.env.local'),     # piu file .env (il secondo sovrascrive)
        env_file_encoding='utf-8',
        secrets_dir='/run/secrets',           # directory per Docker secrets
        json_file='config.json',             # file JSON di configurazione
        toml_file='config.toml',             # file TOML di configurazione
    )

    app_name: str
    debug: bool = False
    database_url: str
    api_key: str
```

#### Esempio Completo: Configurazione Applicazione

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, computed_field
from functools import lru_cache

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )

    # Applicazione
    app_name: str = "Studio Lavoro"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = Field(default="development", pattern=r'^(development|staging|production)$')

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4

    # Database
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "app"
    db_user: str = "postgres"
    db_password: str = ""

    # JWT
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    @computed_field
    @property
    def database_url(self) -> str:
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @computed_field
    @property
    def is_production(self) -> bool:
        return self.environment == "production"


# Singleton pattern per le impostazioni
@lru_cache
def get_settings() -> Settings:
    return Settings()


# Utilizzo
settings = get_settings()
print(settings.database_url)
print(settings.is_production)
```

---

## Integrazione

### FastAPI

FastAPI utilizza Pydantic come motore di validazione nativo per request body, query parameters e response models.

#### Validazione Request Body

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime

app = FastAPI()

class CreaUtenteRequest(BaseModel):
    nome: str = Field(min_length=2, max_length=50)
    cognome: str = Field(min_length=2, max_length=50)
    email: EmailStr
    eta: int = Field(ge=18, le=120)

class UtenteResponse(BaseModel):
    id: int
    nome: str
    cognome: str
    email: str
    creato_il: datetime

    model_config = ConfigDict(from_attributes=True)

class ListaUtentiResponse(BaseModel):
    utenti: list[UtenteResponse]
    totale: int

# FastAPI valida automaticamente il body con Pydantic
@app.post("/utenti", response_model=UtenteResponse, status_code=201)
async def crea_utente(utente: CreaUtenteRequest):
    # utente e gia validato da Pydantic
    # ... logica di creazione ...
    return UtenteResponse(
        id=1,
        nome=utente.nome,
        cognome=utente.cognome,
        email=utente.email,
        creato_il=datetime.now()
    )

@app.get("/utenti", response_model=ListaUtentiResponse)
async def lista_utenti(
    pagina: int = Field(default=1, ge=1),
    per_pagina: int = Field(default=10, ge=1, le=100)
):
    # ... logica di recupero ...
    pass
```

#### Query e Path Parameters con Validazione

FastAPI sfrutta Pydantic anche per validare query parameters e path parameters tramite le annotazioni di tipo:

```python
from fastapi import FastAPI, Query, Path

@app.get("/prodotti/{categoria}")
async def cerca_prodotti(
    categoria: str = Path(min_length=2, max_length=50, description="Categoria merceologica"),
    q: str | None = Query(default=None, min_length=2, description="Termine di ricerca"),
    prezzo_min: float = Query(default=0, ge=0, description="Prezzo minimo"),
    prezzo_max: float = Query(default=99999, le=99999, description="Prezzo massimo"),
    ordinamento: Literal["prezzo", "nome", "data"] = Query(default="nome"),
    pagina: int = Query(default=1, ge=1)
):
    # Tutti i parametri sono gia validati
    return {"categoria": categoria, "query": q, "pagina": pagina}
```

#### Dependency Injection con Settings

```python
from fastapi import FastAPI, Depends
from functools import lru_cache

app = FastAPI()

@lru_cache
def get_settings():
    return Settings()

@app.get("/info")
async def info(settings: Settings = Depends(get_settings)):
    return {
        "app_name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment
    }
```

### SQLAlchemy

Pydantic si integra con SQLAlchemy per convertire tra modelli ORM e modelli di validazione:

```python
from sqlalchemy import Column, Integer, String, DateTime, create_engine
from sqlalchemy.orm import declarative_base, Session
from pydantic import BaseModel, ConfigDict
from datetime import datetime

Base = declarative_base()

# Modello SQLAlchemy (ORM)
class UtenteDB(Base):
    __tablename__ = "utenti"
    id = Column(Integer, primary_key=True)
    nome = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    creato_il = Column(DateTime, default=datetime.utcnow)

# Modello Pydantic per la lettura
class UtenteSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    email: str
    creato_il: datetime

# Modello Pydantic per la creazione
class CreaUtenteSchema(BaseModel):
    nome: str
    email: str

# Conversione ORM -> Pydantic
def get_utente(db: Session, utente_id: int) -> UtenteSchema | None:
    utente_db = db.query(UtenteDB).filter(UtenteDB.id == utente_id).first()
    if utente_db is None:
        return None
    # from_attributes=True consente la conversione diretta
    return UtenteSchema.model_validate(utente_db)

# Conversione Pydantic -> ORM
def crea_utente(db: Session, dati: CreaUtenteSchema) -> UtenteSchema:
    utente_db = UtenteDB(**dati.model_dump())
    db.add(utente_db)
    db.commit()
    db.refresh(utente_db)
    return UtenteSchema.model_validate(utente_db)
```

### JSON Schema

Pydantic genera automaticamente JSON Schema conformi allo standard, facilitando l'integrazione con strumenti OpenAPI e documentazione automatica:

```python
from pydantic import BaseModel, Field
from datetime import datetime
import json

class Prodotto(BaseModel):
    """Schema per un prodotto del catalogo."""
    id: int = Field(description="Identificativo univoco del prodotto")
    nome: str = Field(
        min_length=1,
        max_length=200,
        description="Nome commerciale del prodotto"
    )
    prezzo: float = Field(
        gt=0,
        description="Prezzo in euro, IVA inclusa",
        examples=[29.99, 149.00]
    )
    categoria: str = Field(description="Categoria merceologica")
    disponibile: bool = Field(default=True, description="Se il prodotto e disponibile")
    aggiornato_il: datetime = Field(
        default_factory=datetime.now,
        description="Data ultimo aggiornamento"
    )

# Generazione automatica dello schema
schema = Prodotto.model_json_schema()
print(json.dumps(schema, indent=2, ensure_ascii=False))
# {
#   "title": "Prodotto",
#   "description": "Schema per un prodotto del catalogo.",
#   "type": "object",
#   "properties": {
#     "id": {
#       "title": "Id",
#       "description": "Identificativo univoco del prodotto",
#       "type": "integer"
#     },
#     "nome": {
#       "title": "Nome",
#       "description": "Nome commerciale del prodotto",
#       "type": "string",
#       "minLength": 1,
#       "maxLength": 200
#     },
#     ...
#   },
#   "required": ["id", "nome", "prezzo", "categoria"]
# }

# Personalizzazione dello schema
class ProdottoCustom(BaseModel):
    nome: str = Field(
        json_schema_extra={
            "x-frontend-component": "text-input",
            "x-searchable": True
        }
    )
```

---

## Pattern Pratici

### Gestione Configurazione con Gerarchia di Settings

Organizzare le configurazioni in una gerarchia di classi permette di separare le impostazioni per dominio e ambiente:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class BaseAppSettings(BaseSettings):
    """Configurazione base condivisa tra tutti gli ambienti."""
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    app_name: str = "MiaApp"
    app_version: str = "1.0.0"

class DevelopmentSettings(BaseAppSettings):
    """Configurazione per lo sviluppo locale."""
    model_config = SettingsConfigDict(env_file='.env.development', extra='ignore')

    debug: bool = True
    database_url: str = "postgresql://localhost:5432/myapp_dev"
    log_level: str = "DEBUG"

class ProductionSettings(BaseAppSettings):
    """Configurazione per la produzione."""
    model_config = SettingsConfigDict(env_file='.env.production', extra='ignore')

    debug: bool = False
    database_url: str
    log_level: str = "WARNING"
    workers: int = Field(default=4, ge=1)

def get_settings() -> BaseAppSettings:
    import os
    env = os.getenv("ENVIRONMENT", "development")
    if env == "production":
        return ProductionSettings()
    return DevelopmentSettings()
```

### Modelli API Request/Response

Un pattern comune e definire modelli separati per creazione, aggiornamento e lettura:

```python
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

# Base condivisa
class ArticoloBase(BaseModel):
    titolo: str = Field(min_length=5, max_length=200)
    contenuto: str = Field(min_length=10)
    categoria: str
    tag: list[str] = []

# Creazione — campi obbligatori
class ArticoloCreate(ArticoloBase):
    autore_id: int

# Aggiornamento — tutti i campi opzionali
class ArticoloUpdate(BaseModel):
    titolo: str | None = Field(default=None, min_length=5, max_length=200)
    contenuto: str | None = Field(default=None, min_length=10)
    categoria: str | None = None
    tag: list[str] | None = None

# Lettura — include campi generati dal server
class ArticoloRead(ArticoloBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    autore_id: int
    creato_il: datetime
    aggiornato_il: datetime

# Lista con paginazione
class ArticoloList(BaseModel):
    articoli: list[ArticoloRead]
    pagina: int
    per_pagina: int
    totale: int
```

### Pipeline di Trasformazione Dati

Pydantic eccelle nel trasformare dati grezzi in strutture pulite e validate:

```python
from pydantic import BaseModel, field_validator, model_validator
from datetime import datetime

class DatiGrezziCSV(BaseModel):
    """Trasforma una riga CSV grezza in dati strutturati."""
    data: str
    importo: str
    descrizione: str
    categoria: str

    @field_validator('data', mode='before')
    @classmethod
    def parsa_data(cls, v):
        # Supporta piu formati data
        for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y'):
            try:
                return datetime.strptime(v, fmt).date().isoformat()
            except ValueError:
                continue
        raise ValueError(f'Formato data non riconosciuto: {v}')

    @field_validator('importo', mode='before')
    @classmethod
    def parsa_importo(cls, v):
        if isinstance(v, str):
            # Rimuove simbolo valuta e gestisce formato italiano
            v = v.replace('€', '').replace(' ', '').replace('.', '').replace(',', '.')
        return v

    @field_validator('categoria', mode='before')
    @classmethod
    def normalizza_categoria(cls, v):
        mappatura = {
            'alim': 'alimentari',
            'trasp': 'trasporti',
            'svago': 'intrattenimento',
            'casa': 'abitazione',
        }
        return mappatura.get(v.lower().strip(), v.lower().strip())

# Utilizzo in una pipeline
righe_csv = [
    {"data": "28/03/2026", "importo": "€ 1.234,56", "descrizione": "Spesa mensile", "categoria": "alim"},
    {"data": "2026-03-27", "importo": "45,00", "descrizione": "Benzina", "categoria": "trasp"},
]

dati_puliti = [DatiGrezziCSV.model_validate(riga) for riga in righe_csv]
for dato in dati_puliti:
    print(dato.model_dump())
```

### Validazione Form

```python
from pydantic import BaseModel, Field, field_validator, model_validator, EmailStr

class FormContatto(BaseModel):
    nome: str = Field(min_length=2, max_length=100)
    email: EmailStr
    telefono: str | None = None
    oggetto: str = Field(min_length=5, max_length=200)
    messaggio: str = Field(min_length=20, max_length=5000)
    consenso_privacy: bool

    @field_validator('telefono')
    @classmethod
    def valida_telefono(cls, v):
        if v is not None:
            import re
            pulito = re.sub(r'[\s\-\+\(\)]', '', v)
            if not pulito.isdigit() or len(pulito) < 9 or len(pulito) > 15:
                raise ValueError('Numero di telefono non valido')
        return v

    @field_validator('consenso_privacy')
    @classmethod
    def richiedi_consenso(cls, v):
        if not v:
            raise ValueError('Il consenso alla privacy e obbligatorio')
        return v

# Simulazione validazione form
try:
    form = FormContatto(
        nome="Marco",
        email="marco@example.com",
        oggetto="Richiesta informazioni",
        messaggio="Vorrei ricevere maggiori informazioni sui vostri servizi di consulenza.",
        consenso_privacy=True
    )
    print("Form valido:", form.model_dump())
except Exception as e:
    print("Errori di validazione:", e)
```

### Schema per Eventi

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal, Any
from uuid import UUID, uuid4

class EventoBase(BaseModel):
    """Schema base per eventi di dominio."""
    event_id: UUID = Field(default_factory=uuid4)
    event_type: str
    timestamp: datetime = Field(default_factory=datetime.now)
    versione: int = 1
    payload: dict[str, Any] = {}

class UtenteRegistrato(EventoBase):
    event_type: Literal["utente.registrato"] = "utente.registrato"
    payload: dict  # contiene: utente_id, email, nome

class OrdineCreato(EventoBase):
    event_type: Literal["ordine.creato"] = "ordine.creato"
    payload: dict  # contiene: ordine_id, utente_id, importo, prodotti

class PagamentoRicevuto(EventoBase):
    event_type: Literal["pagamento.ricevuto"] = "pagamento.ricevuto"
    payload: dict  # contiene: pagamento_id, ordine_id, importo, metodo

# Deserializzazione con discriminated union
from pydantic import Discriminator
from typing import Annotated, Union

TipoEvento = Annotated[
    Union[UtenteRegistrato, OrdineCreato, PagamentoRicevuto],
    Discriminator('event_type')
]

class BustaEvento(BaseModel):
    evento: TipoEvento

# Deserializzazione automatica dal tipo
busta = BustaEvento.model_validate({
    "evento": {
        "event_type": "ordine.creato",
        "payload": {
            "ordine_id": "ORD-001",
            "utente_id": 42,
            "importo": 199.99,
            "prodotti": ["PROD-1", "PROD-2"]
        }
    }
})
print(type(busta.evento))  # <class 'OrdineCreato'>
```

### Validazione Record Database

```python
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import date
from decimal import Decimal

class RecordDipendente(BaseModel):
    """Validazione per record importati dal database HR."""
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

    matricola: str = Field(pattern=r'^[A-Z]{2}\d{6}$')
    nome: str = Field(min_length=1)
    cognome: str = Field(min_length=1)
    data_assunzione: date
    reparto: str
    ral: Decimal = Field(ge=0, description="Retribuzione Annua Lorda")
    livello: int = Field(ge=1, le=8)
    attivo: bool = True

    @field_validator('data_assunzione')
    @classmethod
    def non_nel_futuro(cls, v: date) -> date:
        if v > date.today():
            raise ValueError('La data di assunzione non puo essere nel futuro')
        return v

    @field_validator('reparto')
    @classmethod
    def normalizza_reparto(cls, v: str) -> str:
        reparti_validi = {
            'IT', 'HR', 'FINANCE', 'SALES', 'MARKETING', 'OPERATIONS', 'LEGAL'
        }
        v_upper = v.upper()
        if v_upper not in reparti_validi:
            raise ValueError(f'Reparto non valido. Ammessi: {", ".join(sorted(reparti_validi))}')
        return v_upper
```

---

## Best Practices

### 1. Usare Pydantic v2 con Sintassi Moderna

Adottare sempre la sintassi v2 nei nuovi progetti. Le API v1 (`.dict()`, `.json()`, `@validator`) sono deprecate e saranno rimosse nelle versioni future. Utilizzare `model_dump()`, `model_dump_json()`, `@field_validator` e `ConfigDict` al posto delle controparti v1.

```python
# Da evitare (v1)
class Vecchio(BaseModel):
    class Config:
        orm_mode = True
    nome: str

# Preferire (v2)
class Moderno(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    nome: str
```

### 2. Separare i Modelli per Responsabilita

Creare modelli distinti per creazione, aggiornamento e lettura. Un modello `Create` contiene solo i campi necessari per la creazione, un modello `Update` rende tutti i campi opzionali, e un modello `Read` include i campi generati dal sistema (id, timestamp). Questo evita che un singolo modello debba gestire troppi casi d'uso diversi.

### 3. Preferire Annotated Types ai Vincoli Inline

Definire tipi personalizzati con `Annotated` e riutilizzarli in piu modelli, invece di ripetere vincoli in ogni campo. Questo migliora la leggibilita e garantisce coerenza.

```python
# Tipi riutilizzabili definiti una volta
NomePersona = Annotated[str, Field(min_length=1, max_length=100, description="Nome di persona")]
Prezzo = Annotated[Decimal, Field(ge=0, decimal_places=2)]
CodicePostale = Annotated[str, Field(pattern=r'^\d{5}$')]

# Riutilizzati in piu modelli senza ripetizioni
class Cliente(BaseModel):
    nome: NomePersona
    cap: CodicePostale

class Fornitore(BaseModel):
    ragione_sociale: NomePersona
    cap: CodicePostale
```

### 4. Usare mode='before' per la Normalizzazione e mode='after' per la Validazione

I validatori `before` sono ideali per normalizzare i dati in ingresso (convertire formati, pulire stringhe, trasformare tipi). I validatori `after` sono ideali per validare la correttezza logica dei dati gia tipizzati. Mantenere questa separazione rende il codice piu prevedibile e facile da debuggare.

### 5. Sfruttare model_validator per Vincoli Cross-Field

Quando una regola di validazione coinvolge piu campi (es. "la data di fine deve essere successiva alla data di inizio", oppure "se il metodo di pagamento e carta, il numero carta e obbligatorio"), usare `@model_validator(mode='after')` invece di inserire logica complessa nei validatori dei singoli campi.

### 6. Gestire gli Errori in Modo Strutturato

Pydantic genera `ValidationError` con una struttura dettagliata che include il percorso del campo, il tipo di errore e il messaggio. Nelle API, catturare questi errori e restituire risposte strutturate al client.

```python
from pydantic import ValidationError

def valida_input(dati: dict) -> Utente | dict:
    try:
        return Utente.model_validate(dati)
    except ValidationError as e:
        errori = []
        for errore in e.errors():
            errori.append({
                "campo": " -> ".join(str(loc) for loc in errore["loc"]),
                "messaggio": errore["msg"],
                "tipo": errore["type"]
            })
        return {"errori": errori, "totale_errori": len(errori)}
```

### 7. Usare ConfigDict con frozen=True per i Value Objects

Gli oggetti che rappresentano valori immutabili (coordinate, importi monetari, codici identificativi) dovrebbero essere definiti con `frozen=True`. Questo previene modifiche accidentali e rende gli oggetti hashable, permettendo il loro uso come chiavi di dizionari e in set.

### 8. Sfruttare TypeAdapter per Validazione Senza Modelli

Non tutto deve essere un `BaseModel`. Per validare liste, dizionari o tipi semplici, `TypeAdapter` e piu leggero e diretto. Usare `BaseModel` solo quando servono metodi di istanza, validatori personalizzati o campi calcolati.

### 9. Centralizzare le Configurazioni con BaseSettings

Evitare di leggere variabili d'ambiente direttamente con `os.getenv()` sparse nel codice. Definire una classe `BaseSettings` che centralizza tutte le configurazioni con validazione, valori di default e documentazione. Utilizzare il pattern singleton con `@lru_cache` per evitare ricaricamenti multipli.

### 10. Documentare i Modelli per la Generazione Automatica di Schema

Aggiungere docstring alle classi e parametri `title`, `description` e `examples` ai campi. Pydantic include queste informazioni nello JSON Schema generato, che a sua volta alimenta la documentazione automatica di FastAPI (Swagger/ReDoc). Questo trasforma i modelli Pydantic in documentazione vivente dell'API.

```python
class Ordine(BaseModel):
    """Rappresenta un ordine nel sistema e-commerce.

    Un ordine contiene i dati del cliente, i prodotti acquistati
    e le informazioni di spedizione e pagamento.
    """
    codice: str = Field(
        description="Codice univoco dell'ordine nel formato ORD-YYYYNNNN",
        examples=["ORD-20260001", "ORD-20260042"],
        pattern=r'^ORD-\d{8}$'
    )
    importo_totale: float = Field(
        gt=0,
        description="Importo totale dell'ordine in euro, IVA inclusa",
        examples=[99.99, 1250.00]
    )
```

---

Questa guida copre le funzionalita fondamentali e avanzate di Pydantic v2 per la validazione dei dati in Python. Per approfondimenti, consultare la documentazione ufficiale su [docs.pydantic.dev](https://docs.pydantic.dev/) e il repository GitHub [pydantic/pydantic](https://github.com/pydantic/pydantic).

---

## Pydantic v2 Core — Il Motore di Validazione Rust

### Architettura di pydantic-core

Il cambiamento architetturale piu significativo introdotto da Pydantic v2 e la riscrittura del motore di validazione e serializzazione in **Rust**, pubblicato come pacchetto separato chiamato `pydantic-core`. Questo motore e responsabile di tutta la validazione a basso livello: parsing di tipi primitivi, coercion, validazione di vincoli, attraversamento di strutture annidate e generazione di errori. Il layer Python di Pydantic v2 si limita a orchestrare la costruzione degli schemi e a esporre l'API pubblica (`BaseModel`, decoratori, `Field`), delegando l'esecuzione pesante al codice compilato.

La scelta di Rust non e casuale: il linguaggio offre sicurezza di memoria senza garbage collector, performance paragonabili al C, e un sistema di tipi che previene intere classi di bug a compile-time. Per Pydantic, questo si traduce in una validazione che opera a velocita nativa, eliminando il collo di bottiglia che in v1 era rappresentato dalle migliaia di chiamate a funzioni Python pure durante la validazione di strutture complesse.

### SchemaValidator e SchemaSerializer

Internamente, `pydantic-core` espone due classi principali: `SchemaValidator` e `SchemaSerializer`. Quando si definisce un `BaseModel`, Pydantic costruisce uno **schema core** — una rappresentazione intermedia della struttura del modello — e lo passa a `SchemaValidator` per creare un validatore compilato. Lo stesso avviene per `SchemaSerializer`, che gestisce la conversione in dizionario e JSON.

```python
from pydantic_core import SchemaValidator, core_schema

# Esempio di schema core a basso livello
# (normalmente generato automaticamente da BaseModel)
schema = core_schema.model_schema(
    cls=dict,  # tipo target
    schema=core_schema.model_fields_schema(
        fields={
            'nome': core_schema.model_field(
                schema=core_schema.str_schema(min_length=1, max_length=100)
            ),
            'eta': core_schema.model_field(
                schema=core_schema.int_schema(ge=0, le=150)
            ),
        }
    )
)

validatore = SchemaValidator(schema)

# Validazione diretta tramite il core Rust
risultato = validatore.validate_python({'nome': 'Marco', 'eta': 30})
print(risultato)  # {'nome': 'Marco', 'eta': 30}
```

Nella pratica quotidiana non si interagisce direttamente con `pydantic-core`: `BaseModel` e `TypeAdapter` costruiscono e gestiscono gli schemi automaticamente. Tuttavia, comprendere questa architettura a due livelli e utile per:

- **Debugging performance**: capire dove si verifica il costo computazionale.
- **Custom types avanzati**: quando si implementano tipi personalizzati con `__get_pydantic_core_schema__`, si lavora direttamente con gli schemi core.
- **Contributi al progetto**: il repository `pydantic/pydantic-core` su GitHub contiene il codice Rust e accetta contributi.

### Impatto sulle Performance

Il passaggio a Rust ha portato miglioramenti misurabili in diversi scenari:

| Operazione | v1 (Python puro) | v2 (Rust core) | Speedup |
|---|---|---|---|
| Validazione modello semplice (5 campi) | ~15 µs | ~1.5 µs | ~10x |
| Validazione modello complesso (20+ campi, nested) | ~120 µs | ~8 µs | ~15x |
| Serializzazione JSON di lista (1000 modelli) | ~25 ms | ~1.2 ms | ~20x |
| Validazione da JSON string | ~30 µs | ~2 µs | ~15x |

Questi numeri variano in base alla complessita del modello, alla quantita di validatori custom (che rimangono in Python) e alla presenza di coercion. Il guadagno e massimo quando la validazione coinvolge prevalentemente tipi primitivi e vincoli standard.

### __get_pydantic_core_schema__ — Estensione del Core

Per creare tipi completamente personalizzati che si integrano con il motore Rust, si implementa il metodo `__get_pydantic_core_schema__` nella classe del tipo. Questo metodo restituisce uno schema core che indica a `pydantic-core` come validare e serializzare il tipo.

```python
from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema
from typing import Any

class CodiceFiscale:
    """Tipo personalizzato per il codice fiscale italiano."""

    def __init__(self, valore: str):
        self.valore = valore.upper()

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_plain_validator_function(
            cls._valida,
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda v: v.valore,
                info_arg=False,
            ),
        )

    @classmethod
    def _valida(cls, v: Any) -> 'CodiceFiscale':
        if isinstance(v, cls):
            return v
        if not isinstance(v, str):
            raise ValueError('Il codice fiscale deve essere una stringa')
        v = v.upper().strip()
        if len(v) != 16:
            raise ValueError('Il codice fiscale deve avere 16 caratteri')
        return cls(v)

    def __repr__(self) -> str:
        return f'CodiceFiscale({self.valore!r})'


from pydantic import BaseModel

class Contribuente(BaseModel):
    nome: str
    cf: CodiceFiscale

contrib = Contribuente(nome="Marco Rossi", cf="RSSMRC90A01H501Z")
print(contrib.cf)                    # CodiceFiscale('RSSMRC90A01H501Z')
print(contrib.model_dump())          # {'nome': 'Marco Rossi', 'cf': 'RSSMRC90A01H501Z'}
print(contrib.model_dump_json())     # '{"nome":"Marco Rossi","cf":"RSSMRC90A01H501Z"}'
```

---

## model_validator vs field_validator — Confronto Approfondito

### Differenze Fondamentali

I due decoratori principali per la validazione personalizzata in Pydantic v2 — `@field_validator` e `@model_validator` — operano a livelli diversi della pipeline di validazione e hanno semantiche distinte.

| Caratteristica | `@field_validator` | `@model_validator` |
|---|---|---|
| Ambito | Singolo campo (o piu campi esplicitamente elencati) | Intero modello |
| Accesso ad altri campi | No (solo il valore del campo corrente) | Si (tutti i campi) |
| Decoratore `@classmethod` | Obbligatorio | Obbligatorio con `mode='before'`, non richiesto con `mode='after'` |
| Tipo di input (`mode='before'`) | Valore grezzo del singolo campo | Dizionario completo dei dati grezzi |
| Tipo di input (`mode='after'`) | Valore gia validato e tipizzato | Istanza completa del modello |
| Valore di ritorno | Il valore del campo (potenzialmente trasformato) | I dati (before) o il modello (after) |
| Ordine di esecuzione | Dopo la validazione di tipo del campo | Prima (before) o dopo (after) tutti i field validators |

### Ordine di Esecuzione Completo

Comprendere l'ordine di esecuzione e fondamentale per evitare bug sottili. Quando Pydantic valida un modello, la sequenza e la seguente:

1. **model_validator(mode='before')** — riceve i dati grezzi prima di qualsiasi validazione
2. **Per ogni campo, nell'ordine di definizione:**
   a. **field_validator(mode='before')** — pre-processing del valore grezzo
   b. **Validazione di tipo Pydantic** — coercion e type checking
   c. **field_validator(mode='after')** — post-validazione del valore tipizzato
3. **model_validator(mode='after')** — riceve il modello completamente costruito

```python
from pydantic import BaseModel, field_validator, model_validator

class DimostrazioneOrdine(BaseModel):
    valore: int

    @model_validator(mode='before')
    @classmethod
    def step_1_model_before(cls, data):
        print("1. model_validator mode='before' — dati grezzi:", data)
        return data

    @field_validator('valore', mode='before')
    @classmethod
    def step_2_field_before(cls, v):
        print("2. field_validator mode='before' — valore grezzo:", v)
        return v

    @field_validator('valore', mode='after')
    @classmethod
    def step_3_field_after(cls, v: int) -> int:
        print("3. field_validator mode='after' — valore tipizzato:", v)
        return v

    @model_validator(mode='after')
    def step_4_model_after(self):
        print("4. model_validator mode='after' — modello completo:", self)
        return self

# Output:
# 1. model_validator mode='before' — dati grezzi: {'valore': '42'}
# 2. field_validator mode='before' — valore grezzo: '42'
# 3. field_validator mode='after' — valore tipizzato: 42
# 4. model_validator mode='after' — modello completo: valore=42
demo = DimostrazioneOrdine(valore='42')
```

### Errori Comuni e Come Evitarli

**Errore 1: Accedere ad altri campi in un field_validator.** Un `field_validator` non ha accesso ai valori di altri campi. Se si tenta di accedervi tramite `info.data`, i campi definiti dopo quello corrente non saranno ancora disponibili. Se serve un vincolo che dipende da piu campi, usare `model_validator(mode='after')`.

```python
# SBAGLIATO: accesso a campo che potrebbe non esistere ancora
class Sbagliato(BaseModel):
    prezzo: float
    sconto: float

    @field_validator('sconto')
    @classmethod
    def sconto_non_supera_prezzo(cls, v, info):
        # info.data['prezzo'] potrebbe non essere disponibile
        # se l'ordine di definizione cambia
        prezzo = info.data.get('prezzo')
        if prezzo is not None and v > prezzo:
            raise ValueError('Lo sconto non puo superare il prezzo')
        return v

# CORRETTO: usare model_validator per vincoli cross-field
class Corretto(BaseModel):
    prezzo: float
    sconto: float

    @model_validator(mode='after')
    def sconto_non_supera_prezzo(self):
        if self.sconto > self.prezzo:
            raise ValueError('Lo sconto non puo superare il prezzo')
        return self
```

**Errore 2: Dimenticare il `return` nel model_validator.** Sia `mode='before'` che `mode='after'` richiedono un valore di ritorno. Con `mode='before'` si deve restituire il dizionario (potenzialmente modificato), con `mode='after'` si deve restituire `self`. Dimenticare il return causa un `None` implicito che corrompe la validazione.

**Errore 3: Sollevare `ValueError` generico in mode='before'.** In `mode='before'`, i dati grezzi possono avere qualsiasi forma. Il validatore deve gestire tipi inattesi (ad esempio ricevere un intero quando si aspetta un dizionario) senza assumere la struttura dei dati.

### Linee Guida Pratiche

- **Usare `field_validator`** per: normalizzazione di stringhe (trim, lowercase), conversione di formati (date, valute), validazione di singoli valori (range, pattern, lunghezza).
- **Usare `model_validator(mode='before')`** per: preprocessing dell'intero payload (rinominare chiavi, aggiungere campi calcolati prima della validazione, gestire formati di input alternativi).
- **Usare `model_validator(mode='after')`** per: vincoli cross-field (date inizio/fine, password/conferma, importo/sconto), calcolo di valori derivati che dipendono da piu campi validati, invarianti di business logic.

---

## Computed Fields Avanzati

### cached_property e Performance

Quando un campo calcolato richiede un'operazione costosa (chiamata API, calcolo crittografico, query), si puo combinare `@computed_field` con `@cached_property` per calcolare il valore una sola volta e memorizzarlo:

```python
from pydantic import BaseModel, computed_field
from functools import cached_property
import hashlib

class Documento(BaseModel):
    model_config = ConfigDict(frozen=False)  # cached_property richiede mutabilita

    contenuto: str
    autore: str

    @computed_field
    @cached_property
    def hash_contenuto(self) -> str:
        """Calcola l'hash SHA-256 del contenuto (costoso, calcolato una volta)."""
        return hashlib.sha256(self.contenuto.encode()).hexdigest()

    @computed_field
    @cached_property
    def conteggio_parole(self) -> int:
        """Conta le parole nel contenuto."""
        return len(self.contenuto.split())

doc = Documento(contenuto="Lorem ipsum dolor sit amet", autore="Marco")
# La prima volta calcola l'hash
print(doc.hash_contenuto)
# La seconda volta restituisce il valore cached
print(doc.hash_contenuto)  # stesso risultato, nessun ricalcolo
```

**Attenzione**: `cached_property` richiede che il modello NON sia `frozen`. Se il modello e frozen, l'assegnazione del valore cached fallira. Per modelli frozen con campi calcolati costosi, usare `@property` standard (ricalcolo a ogni accesso) oppure pre-calcolare il valore nel `model_validator(mode='after')`.

### Esclusione Condizionale con exclude

A partire da Pydantic v2.9+, i computed fields supportano il parametro `repr` per controllare la loro apparizione nella rappresentazione del modello, e si possono escludere dalla serializzazione usando le opzioni di `model_dump()`:

```python
from pydantic import BaseModel, computed_field

class Fattura(BaseModel):
    imponibile: float
    aliquota_iva: float = 22.0

    @computed_field(repr=False)
    @property
    def iva(self) -> float:
        return round(self.imponibile * self.aliquota_iva / 100, 2)

    @computed_field(repr=True)
    @property
    def totale(self) -> float:
        return round(self.imponibile + self.iva, 2)

fattura = Fattura(imponibile=1000.0)
print(fattura)  # Fattura(imponibile=1000.0, aliquota_iva=22.0, totale=1220.0)
# 'iva' non appare nella repr ma e presente nella serializzazione

# Escludere computed fields specifici dalla serializzazione
print(fattura.model_dump(exclude={'iva'}))
# {'imponibile': 1000.0, 'aliquota_iva': 22.0, 'totale': 1220.0}
```

### Computed Fields nel JSON Schema

I computed fields vengono automaticamente inclusi nel JSON Schema generato da Pydantic, con il tipo di ritorno della property come tipo dello schema. Questo e utile per la documentazione OpenAPI: il client dell'API sa che la risposta conterra il campo calcolato, anche se non deve fornirlo in input.

```python
import json

schema = Fattura.model_json_schema()
print(json.dumps(schema, indent=2, ensure_ascii=False))
# I computed fields 'iva' e 'totale' appaiono nelle properties dello schema
# ma NON nella lista dei 'required' (non sono campi di input)
```

### Computed Fields con Alias

I computed fields supportano alias di serializzazione, utili quando l'API esterna richiede nomi diversi da quelli interni:

```python
from pydantic import BaseModel, computed_field, Field

class Riepilogo(BaseModel):
    quantita: int
    prezzo_unitario: float

    @computed_field(alias='total_amount')
    @property
    def importo_totale(self) -> float:
        return round(self.quantita * self.prezzo_unitario, 2)

riepilogo = Riepilogo(quantita=5, prezzo_unitario=19.99)
print(riepilogo.model_dump(by_alias=True))
# {'quantita': 5, 'prezzo_unitario': 19.99, 'total_amount': 99.95}
```

---

## Discriminated Unions Avanzate

### Discriminatore con Funzione Personalizzata

Oltre all'uso di un campo stringa come discriminatore, Pydantic v2 supporta l'uso di funzioni callable come discriminatori. Questo e utile quando la logica di discriminazione non si basa su un singolo campo ma su una combinazione di valori o sulla struttura stessa dei dati:

```python
from pydantic import BaseModel, Discriminator, Tag
from typing import Annotated, Union

class EventoClick(BaseModel):
    x: int
    y: int
    elemento: str

class EventoTastiera(BaseModel):
    tasto: str
    modificatori: list[str] = []

class EventoScroll(BaseModel):
    delta_x: float
    delta_y: float

def discrimina_evento(dati: dict) -> str:
    """Discrimina il tipo di evento in base ai campi presenti."""
    if 'x' in dati and 'y' in dati:
        return 'click'
    elif 'tasto' in dati:
        return 'tastiera'
    elif 'delta_x' in dati or 'delta_y' in dati:
        return 'scroll'
    raise ValueError('Tipo di evento non riconosciuto')

TipoEvento = Annotated[
    Union[
        Annotated[EventoClick, Tag('click')],
        Annotated[EventoTastiera, Tag('tastiera')],
        Annotated[EventoScroll, Tag('scroll')],
    ],
    Discriminator(discrimina_evento)
]

class StreamEventi(BaseModel):
    eventi: list[TipoEvento]

stream = StreamEventi(eventi=[
    {'x': 100, 'y': 200, 'elemento': 'bottone'},
    {'tasto': 'Enter', 'modificatori': ['Ctrl']},
    {'delta_x': 0, 'delta_y': -120.0},
])

for evento in stream.eventi:
    print(type(evento).__name__, evento.model_dump())
# EventoClick {'x': 100, 'y': 200, 'elemento': 'bottone'}
# EventoTastiera {'tasto': 'Enter', 'modificatori': ['Ctrl']}
# EventoScroll {'delta_x': 0.0, 'delta_y': -120.0}
```

### Discriminated Unions Annidate

Le discriminated unions possono essere annidate per gestire gerarchie di tipi complesse. Questo pattern e comune nei sistemi di notifica, nei motori di regole e nelle pipeline di processing:

```python
from pydantic import BaseModel, Discriminator
from typing import Annotated, Literal, Union

# Livello 2: tipi specifici di notifica email
class EmailTestuale(BaseModel):
    formato: Literal["testo"]
    corpo: str

class EmailHTML(BaseModel):
    formato: Literal["html"]
    corpo_html: str
    corpo_testo: str  # fallback

# Livello 1: canali di notifica
class NotificaEmail(BaseModel):
    canale: Literal["email"]
    destinatario: str
    oggetto: str
    contenuto: Annotated[
        Union[EmailTestuale, EmailHTML],
        Discriminator('formato')
    ]

class NotificaSMS(BaseModel):
    canale: Literal["sms"]
    numero: str
    testo: str

class NotificaPush(BaseModel):
    canale: Literal["push"]
    device_token: str
    titolo: str
    corpo: str

# Union principale discriminata per canale
TipoNotifica = Annotated[
    Union[NotificaEmail, NotificaSMS, NotificaPush],
    Discriminator('canale')
]

class InvioNotifica(BaseModel):
    notifica: TipoNotifica

# Validazione con discriminazione a due livelli
invio = InvioNotifica(notifica={
    'canale': 'email',
    'destinatario': 'utente@example.com',
    'oggetto': 'Benvenuto',
    'contenuto': {
        'formato': 'html',
        'corpo_html': '<h1>Benvenuto!</h1>',
        'corpo_testo': 'Benvenuto!'
    }
})
print(type(invio.notifica))             # NotificaEmail
print(type(invio.notifica.contenuto))   # EmailHTML
```

### Performance: Discriminated vs Untagged Unions

Le discriminated unions sono significativamente piu performanti delle union non discriminate. In una union non discriminata, Pydantic prova ogni tipo in ordine fino a trovarne uno che valida con successo — un processo O(n) nel numero di tipi. Con un discriminatore, Pydantic effettua un lookup diretto O(1) basato sul valore del campo discriminatore.

Per union con piu di 3-4 membri, la differenza di performance diventa sostanziale. In benchmark tipici:

| Numero di tipi nella union | Untagged | Discriminated | Speedup |
|---|---|---|---|
| 3 tipi | ~8 µs | ~2 µs | ~4x |
| 10 tipi | ~25 µs | ~2 µs | ~12x |
| 20 tipi | ~50 µs | ~2 µs | ~25x |

Oltre alla performance, le discriminated unions producono anche messaggi di errore piu chiari: invece di elencare tutti i tentativi falliti per ogni tipo, Pydantic indica immediatamente quale tipo era atteso e perche la validazione e fallita.

### Serializzazione Polimorfica

A partire da Pydantic v2.13, la serializzazione delle discriminated unions e stata migliorata. I modelli vengono serializzati con tutti i campi specifici del tipo concreto, non solo quelli della classe base. Questo garantisce che la serializzazione e deserializzazione siano round-trip safe:

```python
ordine_carta = Ordine(
    codice_ordine="ORD-001",
    importo=99.99,
    pagamento={"tipo": "carta", "numero_carta": "4111111111111111",
               "scadenza": "12/28", "cvv": "123"}
)

# Serializzazione preserva tutti i campi del tipo concreto
json_str = ordine_carta.model_dump_json()
# {"codice_ordine":"ORD-001","importo":99.99,
#  "pagamento":{"tipo":"carta","numero_carta":"4111...","scadenza":"12/28","cvv":"123"}}

# Round-trip: deserializzazione preserva il tipo
ordine_ricostruito = Ordine.model_validate_json(json_str)
assert type(ordine_ricostruito.pagamento) is PagamentoCarta
```

---

## Modelli Generici Avanzati

### TypeVar Multipli e Bounded Generics

I modelli generici possono utilizzare piu TypeVar per parametrizzare diversi aspetti della struttura. Si possono anche vincolare i TypeVar con bound per limitare i tipi accettati:

```python
from pydantic import BaseModel
from typing import TypeVar, Generic

# TypeVar vincolato: accetta solo sottoclassi di BaseModel
M = TypeVar('M', bound=BaseModel)
K = TypeVar('K', str, int)  # accetta solo str o int come chiave

class Registro(BaseModel, Generic[K, M]):
    """Registro generico con chiave tipizzata e valore modello."""
    elementi: dict[K, M]
    ultimo_aggiornamento: datetime | None = None

    def cerca(self, chiave: K) -> M | None:
        return self.elementi.get(chiave)

class Prodotto(BaseModel):
    nome: str
    prezzo: float

class Utente(BaseModel):
    nome: str
    email: str

# Registro con chiave stringa e valori Prodotto
catalogo = Registro[str, Prodotto](
    elementi={
        'PROD-001': Prodotto(nome='Laptop', prezzo=999.99),
        'PROD-002': Prodotto(nome='Mouse', prezzo=29.99),
    }
)

# Registro con chiave intera e valori Utente
rubrica = Registro[int, Utente](
    elementi={
        1: Utente(nome='Marco', email='marco@example.com'),
        2: Utente(nome='Anna', email='anna@example.com'),
    }
)
```

### Generics con Validazione Tipizzata

I validatori all'interno di modelli generici possono operare sul tipo parametrizzato, mantenendo la type safety:

```python
from pydantic import BaseModel, model_validator
from typing import TypeVar, Generic

T = TypeVar('T')

class CollezioneLimitata(BaseModel, Generic[T]):
    """Collezione con limite massimo di elementi."""
    elementi: list[T]
    limite: int = 100

    @model_validator(mode='after')
    def verifica_limite(self):
        if len(self.elementi) > self.limite:
            raise ValueError(
                f'La collezione contiene {len(self.elementi)} elementi, '
                f'il limite e {self.limite}'
            )
        return self

class Punteggio(BaseModel):
    giocatore: str
    punti: int

# Collezione limitata di punteggi
classifica = CollezioneLimitata[Punteggio](
    elementi=[
        Punteggio(giocatore='Alice', punti=100),
        Punteggio(giocatore='Bob', punti=85),
    ],
    limite=50
)
```

### Pattern Envelope Generico per API

Un pattern molto diffuso nelle API e l'envelope generico che avvolge risposte di diversi tipi con metadati comuni:

```python
from pydantic import BaseModel, computed_field
from typing import TypeVar, Generic
from datetime import datetime

T = TypeVar('T')

class RispostaAPI(BaseModel, Generic[T]):
    """Envelope generico per risposte API."""
    successo: bool
    dati: T | None = None
    errore: str | None = None
    timestamp: datetime = Field(default_factory=datetime.now)
    versione_api: str = "2.0"

    @computed_field
    @property
    def ha_errore(self) -> bool:
        return self.errore is not None

class MetadatiPaginazione(BaseModel):
    pagina: int
    per_pagina: int
    totale: int
    pagine_totali: int

class RispostaPaginataAPI(BaseModel, Generic[T]):
    """Risposta API con paginazione."""
    successo: bool = True
    dati: list[T]
    paginazione: MetadatiPaginazione

# Uso concreto
class ArticoloDTO(BaseModel):
    id: int
    titolo: str

risposta = RispostaPaginataAPI[ArticoloDTO](
    dati=[
        ArticoloDTO(id=1, titolo="Primo articolo"),
        ArticoloDTO(id=2, titolo="Secondo articolo"),
    ],
    paginazione=MetadatiPaginazione(pagina=1, per_pagina=10, totale=2, pagine_totali=1)
)

# Lo schema JSON riflette il tipo concreto
schema = RispostaPaginataAPI[ArticoloDTO].model_json_schema()
```

---

## Generazione JSON Schema Avanzata

### Modalita validation vs serialization

Pydantic puo generare due varianti di JSON Schema: una per la **validazione** (cosa accetta in input) e una per la **serializzazione** (cosa produce in output). La differenza e significativa quando ci sono computed fields, alias o campi con `exclude=True`:

```python
from pydantic import BaseModel, computed_field, Field
import json

class Prodotto(BaseModel):
    codice: str = Field(alias='product_code')
    nome: str
    prezzo: float
    password_hash: str = Field(exclude=True)

    @computed_field
    @property
    def prezzo_formattato(self) -> str:
        return f"EUR {self.prezzo:.2f}"

# Schema per la validazione (input)
schema_validazione = Prodotto.model_json_schema(mode='validation')
print("Validazione:", json.dumps(schema_validazione, indent=2, ensure_ascii=False))
# Include: product_code (alias), nome, prezzo, password_hash
# NON include: prezzo_formattato (computed, non accettato in input)

# Schema per la serializzazione (output)
schema_serializzazione = Prodotto.model_json_schema(mode='serialization')
print("Serializzazione:", json.dumps(schema_serializzazione, indent=2, ensure_ascii=False))
# Include: product_code, nome, prezzo, prezzo_formattato
# NON include: password_hash (exclude=True)
```

### Personalizzazione dello Schema con json_schema_extra

Per aggiungere metadati custom allo schema JSON (utili per generatori di UI, documentazione o integrazioni esterne), si usa `json_schema_extra` sia a livello di campo che di modello:

```python
from pydantic import BaseModel, Field, ConfigDict

class FormRegistrazione(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            'x-form-title': 'Registrazione Utente',
            'x-form-description': 'Form di registrazione per nuovi utenti',
            'x-submit-label': 'Registrati',
        }
    )

    nome: str = Field(
        min_length=2,
        json_schema_extra={
            'x-widget': 'text-input',
            'x-placeholder': 'Inserisci il tuo nome',
            'x-order': 1,
        }
    )
    email: str = Field(
        json_schema_extra={
            'x-widget': 'email-input',
            'x-autocomplete': 'email',
            'x-order': 2,
        }
    )
    ruolo: str = Field(
        json_schema_extra={
            'x-widget': 'select',
            'x-options': ['utente', 'admin', 'moderatore'],
            'x-order': 3,
        }
    )
```

### Riferimenti e $defs

Per modelli complessi con sotto-modelli condivisi, Pydantic genera automaticamente un sezione `$defs` nello schema JSON, evitando duplicazioni. Questo segue lo standard JSON Schema e produce schemi piu compatti e manutenibili:

```python
from pydantic import BaseModel

class Indirizzo(BaseModel):
    via: str
    citta: str
    cap: str

class Persona(BaseModel):
    nome: str
    residenza: Indirizzo
    domicilio: Indirizzo | None = None  # riutilizza lo stesso schema

schema = Persona.model_json_schema()
# Lo schema contiene '$defs' con la definizione di Indirizzo una sola volta
# I campi 'residenza' e 'domicilio' referenziano '$ref': '#/$defs/Indirizzo'
```

### Generazione Schema con TypeAdapter

`TypeAdapter` permette di generare JSON Schema anche per tipi che non sono `BaseModel`, utile per documentare strutture dati intermedie o formati di scambio:

```python
from pydantic import TypeAdapter

# Schema per un tipo semplice vincolato
from typing import Annotated
from pydantic import Field

PunteggioLimitato = Annotated[int, Field(ge=0, le=100, description="Punteggio da 0 a 100")]
adapter = TypeAdapter(PunteggioLimitato)
print(adapter.json_schema())
# {'type': 'integer', 'minimum': 0, 'maximum': 100, 'description': 'Punteggio da 0 a 100'}

# Schema per una struttura complessa senza BaseModel
from typing import TypedDict

class MetricheDict(TypedDict):
    cpu_percent: float
    memoria_mb: int
    disco_libero_gb: float

adapter_metriche = TypeAdapter(list[MetricheDict])
print(adapter_metriche.json_schema())
```

---

## Pydantic Settings v2 — Configurazione Multi-Sorgente Avanzata

### settings_customise_sources — Priorita Personalizzata

Per default, `BaseSettings` legge i valori nell'ordine: argomenti del costruttore > variabili d'ambiente > file .env > valori default. Questo ordine puo essere completamente personalizzato sovrascrivendo il metodo `settings_customise_sources`:

```python
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
    PydanticBaseSettingsSource,
)

class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        toml_file='config.toml',
    )

    nome_app: str = "MiaApp"
    porta: int = 8000
    debug: bool = False
    database_url: str = "sqlite:///local.db"

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Personalizza l'ordine di priorita delle sorgenti.

        Priorita (dalla piu alta alla piu bassa):
        1. Argomenti del costruttore
        2. Variabili d'ambiente
        3. File .env
        4. Docker secrets
        """
        return (
            init_settings,          # priorita massima
            env_settings,           # variabili d'ambiente
            dotenv_settings,        # file .env
            file_secret_settings,   # directory secrets
        )
```

### Sorgenti Custom

Pydantic Settings permette di creare sorgenti di configurazione completamente personalizzate. Questo e utile per leggere configurazioni da API remote, database, vault di secrets o formati di file proprietari:

```python
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource
from pydantic.fields import FieldInfo
from typing import Any

class JSONFileSettingsSource(PydanticBaseSettingsSource):
    """Sorgente di configurazione che legge da un file JSON."""

    def __init__(self, settings_cls: type[BaseSettings], json_path: str):
        super().__init__(settings_cls)
        self.json_path = json_path

    def get_field_value(
        self, field: FieldInfo, field_name: str
    ) -> tuple[Any, str, bool]:
        import json
        from pathlib import Path

        file_path = Path(self.json_path)
        if not file_path.exists():
            return None, field_name, False

        dati = json.loads(file_path.read_text())
        valore = dati.get(field_name)
        return valore, field_name, valore is not None

    def __call__(self) -> dict[str, Any]:
        import json
        from pathlib import Path

        file_path = Path(self.json_path)
        if not file_path.exists():
            return {}
        return json.loads(file_path.read_text())


class ConfigConJSON(BaseSettings):
    nome_app: str = "MiaApp"
    porta: int = 8000
    debug: bool = False

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,
            JSONFileSettingsSource(settings_cls, 'config.json'),
            dotenv_settings,
            file_secret_settings,
        )
```

### Docker Secrets e Kubernetes

Per ambienti containerizzati, Pydantic Settings supporta nativamente la lettura di secrets da directory montate (tipico pattern Docker Swarm e Kubernetes):

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class DockerSecrets(BaseSettings):
    model_config = SettingsConfigDict(
        secrets_dir='/run/secrets',   # directory montata da Docker/K8s
        env_prefix='APP_',
    )

    # Docker crea un file per ogni secret:
    # /run/secrets/db_password contiene il valore
    # /run/secrets/jwt_secret contiene il valore
    db_password: str
    jwt_secret: str
    api_key: str

# I secrets vengono letti dai file nella directory specificata
# Il nome del file corrisponde al nome del campo (senza prefisso)
config = DockerSecrets()
```

### Configurazione Multi-Ambiente

Pattern completo per gestire configurazioni per development, staging e production con override progressivo:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Literal

class Ambiente(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=('.env', '.env.local'),  # .env.local sovrascrive .env
        env_file_encoding='utf-8',
        extra='ignore',
    )

    # Il nome dell'ambiente determina il file .env aggiuntivo
    ambiente: Literal['development', 'staging', 'production'] = 'development'

    # Impostazioni comuni
    app_nome: str = "StudioLavoro"
    log_level: str = "INFO"

    # Database
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "app_dev"
    db_password: str = ""

    # Cache
    redis_url: str = "redis://localhost:6379/0"

    # Sicurezza
    cors_origins: list[str] = ["http://localhost:3000"]
    rate_limit_per_minuto: int = 60

    def e_produzione(self) -> bool:
        return self.ambiente == 'production'

    def e_debug(self) -> bool:
        return self.ambiente == 'development'
```

---

## Serializzazione Avanzata

### model_serializer — Serializzazione Globale del Modello

Mentre `@field_serializer` opera su singoli campi, `@model_serializer` permette di controllare la serializzazione dell'intero modello. Questo e utile per produrre formati di output radicalmente diversi dalla struttura interna del modello:

```python
from pydantic import BaseModel, model_serializer
from datetime import datetime

class LogEntry(BaseModel):
    timestamp: datetime
    livello: str
    messaggio: str
    sorgente: str
    metadati: dict | None = None

    @model_serializer
    def serializza_come_riga_log(self) -> str:
        """Serializza il modello come riga di log testuale."""
        ts = self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        meta = f" | {self.metadati}" if self.metadati else ""
        return f"[{ts}] {self.livello.upper():8s} | {self.sorgente}: {self.messaggio}{meta}"

log = LogEntry(
    timestamp=datetime(2026, 5, 24, 10, 30),
    livello="error",
    messaggio="Connessione persa",
    sorgente="db_client"
)
print(log.model_dump())
# '[2026-05-24 10:30:00] ERROR    | db_client: Connessione persa'
```

### Parametro when_used nei Serializzatori

I serializzatori supportano il parametro `when_used` per controllare quando la logica di serializzazione personalizzata viene applicata. Le opzioni sono: `'always'` (default), `'unless-none'`, `'json'` (solo per output JSON), `'json-unless-none'`:

```python
from pydantic import BaseModel, field_serializer
from datetime import datetime

class Evento(BaseModel):
    nome: str
    data: datetime | None = None

    @field_serializer('data', when_used='json')
    def serializza_data_json(self, v: datetime | None) -> str | None:
        """Formatta la data solo nella serializzazione JSON."""
        if v is None:
            return None
        return v.strftime('%d/%m/%Y')

evento = Evento(nome="Conferenza", data=datetime(2026, 6, 15))

# model_dump() NON usa il serializzatore custom (when_used='json')
print(evento.model_dump())
# {'nome': 'Conferenza', 'data': datetime(2026, 6, 15, 0, 0)}

# model_dump_json() USA il serializzatore custom
print(evento.model_dump_json())
# '{"nome":"Conferenza","data":"15/06/2026"}'
```

### Round-Trip Fidelity

Per garantire che la serializzazione e deserializzazione siano biunivoche (round-trip safe), e fondamentale che il formato di output sia anche un formato di input valido. Questo e particolarmente importante per tipi personalizzati e enum:

```python
from pydantic import BaseModel, field_serializer, field_validator
from enum import Enum

class Stato(str, Enum):
    ATTIVO = "attivo"
    SOSPESO = "sospeso"
    CHIUSO = "chiuso"

class Account(BaseModel):
    id: int
    stato: Stato
    saldo: float

    @field_serializer('saldo')
    def serializza_saldo(self, v: float) -> str:
        return f"{v:.2f}"

    @field_validator('saldo', mode='before')
    @classmethod
    def deserializza_saldo(cls, v):
        if isinstance(v, str):
            return float(v)
        return v

# Round-trip
account = Account(id=1, stato="attivo", saldo=1234.567)
json_str = account.model_dump_json()
account_ricostruito = Account.model_validate_json(json_str)
assert account_ricostruito.id == account.id
assert account_ricostruito.stato == account.stato
# Il saldo e stato arrotondato dal serializzatore, quindi il round-trip non e bit-identical
# ma la struttura e preservata
```

### Serializzazione su Annotated Types

I serializzatori possono essere applicati come parte di un tipo `Annotated`, rendendoli riutilizzabili in piu modelli senza ripetere la logica:

```python
from typing import Annotated
from pydantic import BaseModel
from pydantic.functional_serializers import PlainSerializer
from datetime import datetime
from decimal import Decimal

# Tipi riutilizzabili con serializzazione incorporata
DataItaliana = Annotated[
    datetime,
    PlainSerializer(
        lambda v: v.strftime('%d/%m/%Y %H:%M'),
        return_type=str,
    )
]

ImportoEuro = Annotated[
    Decimal,
    PlainSerializer(
        lambda v: f"{v:,.2f} EUR".replace(',', 'X').replace('.', ',').replace('X', '.'),
        return_type=str,
    )
]

class Movimento(BaseModel):
    data: DataItaliana
    importo: ImportoEuro
    descrizione: str

movimento = Movimento(
    data=datetime(2026, 5, 24, 14, 30),
    importo=Decimal("12345.67"),
    descrizione="Bonifico in uscita"
)
print(movimento.model_dump())
# {'data': '24/05/2026 14:30', 'importo': '12.345,67 EUR', 'descrizione': 'Bonifico in uscita'}
```

---

## Strict Mode vs Lax Mode — Approfondimento

### Strict Mode per Campo Singolo

Oltre alla configurazione globale `ConfigDict(strict=True)`, lo strict mode puo essere abilitato selettivamente su singoli campi. Questo e utile quando la maggior parte dei campi beneficia della coercion automatica, ma alcuni campi richiedono tipi esatti:

```python
from pydantic import BaseModel, Field

class ConfigurazioneMista(BaseModel):
    # Lax: accetta stringhe convertibili a intero
    porta: int = 8000

    # Strict: richiede esattamente un booleano
    debug: bool = Field(default=False, strict=True)

    # Strict: richiede esattamente una stringa
    api_key: str = Field(strict=True)

    # Lax: accetta stringhe convertibili a float
    timeout: float = 30.0

# Funziona: porta accetta stringa, debug richiede bool
config = ConfigurazioneMista(porta="8080", debug=True, api_key="abc-123")

# Errore: debug riceve una stringa invece di un bool
try:
    config_err = ConfigurazioneMista(porta="8080", debug="true", api_key="abc-123")
except Exception as e:
    print(e)  # Input should be a valid boolean
```

### Strict Mode con TypeAdapter

`TypeAdapter` supporta il parametro `strict` sia nella configurazione che nelle singole chiamate di validazione:

```python
from pydantic import TypeAdapter

adapter = TypeAdapter(int)

# Lax mode (default): converte stringhe
risultato = adapter.validate_python("42")
print(risultato)  # 42

# Strict mode: rifiuta stringhe
try:
    adapter.validate_python("42", strict=True)
except Exception as e:
    print(e)  # Input should be a valid integer

# TypeAdapter con strict mode globale
adapter_strict = TypeAdapter(int, config={'strict': True})
try:
    adapter_strict.validate_python("42")
except Exception as e:
    print(e)  # Input should be a valid integer
```

### Strict Mode con Union Types

Lo strict mode interagisce in modo significativo con le union. In lax mode, `Union[int, str]` accetta `"42"` e lo converte a `int` (perche int e il primo tipo nella union). In strict mode, `"42"` viene validato come `str` perche e gia una stringa valida:

```python
from pydantic import BaseModel, ConfigDict

class LaxUnion(BaseModel):
    valore: int | str

class StrictUnion(BaseModel):
    model_config = ConfigDict(strict=True)
    valore: int | str

# Lax: "42" viene convertito a int (primo tipo nella union)
lax = LaxUnion(valore="42")
print(type(lax.valore))  # <class 'int'>

# Strict: "42" resta str (tipo esatto)
strict = StrictUnion(valore="42")
print(type(strict.valore))  # <class 'str'>
```

### Linee Guida per la Scelta

| Scenario | Modalita consigliata | Motivazione |
|---|---|---|
| API pubblica con input utente | Lax | Gli utenti inviano spesso stringhe per numeri |
| API interna tra servizi | Strict | Garante di correttezza, cattura errori di serializzazione |
| Parsing di CSV/Excel | Lax | I dati da file sono spesso tutti stringhe |
| Validazione di config interne | Strict | Previene errori di configurazione silenziosi |
| Pipeline di dati tipizzati | Strict | Garantisce che i tipi siano coerenti attraverso la pipeline |
| Prototipi e MVP | Lax | Meno rigido, piu produttivo |

---

## TypeAdapter — Uso Avanzato

### Validazione Senza BaseModel

`TypeAdapter` e la soluzione ideale quando si vuole validare dati senza creare una classe `BaseModel`. Questo e utile per funzioni standalone, validazione di parametri e preprocessing di dati:

```python
from pydantic import TypeAdapter, ValidationError
from typing import Annotated
from pydantic import Field

# Validazione di una lista di email
EmailList = TypeAdapter(list[Annotated[str, Field(pattern=r'^[\w.+-]+@[\w-]+\.[\w.]+$')]])

try:
    email_valide = EmailList.validate_python([
        "utente@example.com",
        "admin@test.it",
        "non-una-email",  # fallisce
    ])
except ValidationError as e:
    print(e)

# Validazione di dizionari con struttura specifica
from typing import TypedDict

class MetrichePerformance(TypedDict):
    latenza_ms: float
    richieste_al_secondo: int
    errori_percentuale: float

MetricheAdapter = TypeAdapter(MetrichePerformance)
metriche = MetricheAdapter.validate_python({
    'latenza_ms': 45.2,
    'richieste_al_secondo': 1500,
    'errori_percentuale': 0.5,
})
```

### TypeAdapter per la Validazione di Argomenti di Funzione

Un pattern utile e l'uso di `TypeAdapter` come decoratore per validare gli argomenti di funzioni senza Pydantic `BaseModel`:

```python
from pydantic import TypeAdapter, Field
from typing import Annotated
from functools import wraps

Eta = Annotated[int, Field(ge=0, le=150)]
Nome = Annotated[str, Field(min_length=1, max_length=100)]

eta_adapter = TypeAdapter(Eta)
nome_adapter = TypeAdapter(Nome)

def valida_persona(nome: str, eta: int) -> dict:
    """Funzione con validazione tramite TypeAdapter."""
    nome_validato = nome_adapter.validate_python(nome)
    eta_validata = eta_adapter.validate_python(eta)
    return {'nome': nome_validato, 'eta': eta_validata}

# Validazione automatica
risultato = valida_persona("Marco", 30)
print(risultato)  # {'nome': 'Marco', 'eta': 30}

# Errore se i parametri non sono validi
try:
    valida_persona("", 200)
except Exception as e:
    print(e)
```

### Performance di TypeAdapter vs BaseModel

`TypeAdapter` e piu leggero di `BaseModel` perche non crea una classe con tutti i metodi di modello. Per validazioni semplici e ripetute, puo essere significativamente piu veloce:

```python
from pydantic import TypeAdapter, BaseModel
from typing import Annotated
from pydantic import Field

# Approccio BaseModel
class NumeroValidato(BaseModel):
    valore: int = Field(ge=0, le=100)

# Approccio TypeAdapter
NumeroAdapter = TypeAdapter(Annotated[int, Field(ge=0, le=100)])

# TypeAdapter: ~0.5 µs per validazione
# BaseModel: ~1.5 µs per validazione (include costruzione oggetto)

# Per validare migliaia di valori semplici, TypeAdapter e preferibile
valori = [42, 85, 100, 0, 55]
validati = [NumeroAdapter.validate_python(v) for v in valori]
```

---

## Dataclasses vs BaseModel

### Pydantic Dataclasses

Pydantic offre un decoratore `@pydantic.dataclasses.dataclass` che combina l'ergonomia delle dataclass standard con la validazione di Pydantic. Questo e un punto intermedio tra `dataclasses.dataclass` (nessuna validazione) e `BaseModel` (validazione completa con tutti i metodi di modello):

```python
from pydantic.dataclasses import dataclass
from pydantic import Field

@dataclass
class Coordinate:
    latitudine: float = Field(ge=-90, le=90)
    longitudine: float = Field(ge=-180, le=180)

# Validazione automatica come BaseModel
coord = Coordinate(latitudine=45.46, longitudine=9.19)

# Errore se fuori range
try:
    coord_err = Coordinate(latitudine=100, longitudine=0)
except Exception as e:
    print(e)  # Input should be less than or equal to 90
```

### Confronto Dettagliato

| Caratteristica | `dataclasses.dataclass` | `pydantic.dataclasses.dataclass` | `BaseModel` |
|---|---|---|---|
| Validazione automatica | No | Si | Si |
| Coercion di tipo | No | Si | Si |
| `model_dump()` | No | No (usa `asdict()`) | Si |
| `model_dump_json()` | No | No | Si |
| `model_validate()` | No | No | Si |
| JSON Schema | No | Si (tramite `TypeAdapter`) | Si |
| `@field_validator` | No | Si | Si |
| `@model_validator` | No | Si | Si |
| `computed_field` | No | No | Si |
| `model_config` | No | Si (tramite decoratore) | Si |
| Performance istanziazione | Massima | Media | Media |
| Compatibilita con librerie standard | Massima | Parziale | Limitata |
| `__init__` generato | Si | Si | Si |
| `__eq__` generato | Si | Si | Si |
| `__hash__` generato | Opzionale | Opzionale | No (default) |

### Quando Usare Quale

**Usare `dataclasses.dataclass`** quando:
- La struttura dati e interna al programma e non riceve input esterno
- La performance di istanziazione e critica (migliaia di oggetti al secondo)
- Si vuole massima compatibilita con librerie standard (es. `json.dumps` con encoder custom)
- Non serve validazione — i dati sono gia noti come corretti

**Usare `pydantic.dataclasses.dataclass`** quando:
- Si vuole validazione senza la complessita completa di `BaseModel`
- Si devono integrare dati con librerie che si aspettano dataclass standard
- Si vuole un graduale migrazione da dataclass a Pydantic

**Usare `BaseModel`** quando:
- Serve serializzazione completa (`model_dump()`, `model_dump_json()`)
- Serve generazione di JSON Schema
- Serve integrazione con FastAPI (response model)
- Servono computed fields
- Serve `model_validate()` per creare istanze da dizionari
- Il modello rappresenta un boundary di sistema (API, database, file)

```python
# Esempio: stessa struttura, tre approcci
from dataclasses import dataclass as std_dataclass
from pydantic.dataclasses import dataclass as pyd_dataclass
from pydantic import BaseModel

# 1. Dataclass standard — nessuna validazione
@std_dataclass
class PuntoStd:
    x: float
    y: float

# 2. Pydantic dataclass — validazione, ma API dataclass
@pyd_dataclass
class PuntoPyd:
    x: float
    y: float

# 3. BaseModel — validazione + serializzazione completa
class PuntoModel(BaseModel):
    x: float
    y: float

# std: accetta qualsiasi cosa senza errori
p1 = PuntoStd(x="non_un_numero", y=[1, 2])  # nessun errore!

# pydantic dataclass: valida
p2 = PuntoPyd(x=1.5, y=2.5)  # ok
# p2_err = PuntoPyd(x="non_un_numero", y=[1, 2])  # errore!

# BaseModel: valida + serializza
p3 = PuntoModel(x=1.5, y=2.5)
print(p3.model_dump_json())  # '{"x":1.5,"y":2.5}'
```

---

## Migrazione da Pydantic v1 a v2

### Panoramica delle Breaking Changes

La migrazione da v1 a v2 e un cambiamento significativo che tocca API, comportamenti di validazione e configurazione. Le principali aree di rottura sono:

**API rinominate:**

| v1 | v2 | Note |
|---|---|---|
| `.dict()` | `.model_dump()` | v1 API deprecata ma ancora funzionante |
| `.json()` | `.model_dump_json()` | |
| `.parse_obj()` | `.model_validate()` | |
| `.parse_raw()` | `.model_validate_json()` | |
| `.schema()` | `.model_json_schema()` | |
| `.copy(update={})` | `.model_copy(update={})` | |
| `@validator` | `@field_validator` | Firma diversa: `@classmethod` esplicito |
| `@root_validator` | `@model_validator` | |
| `class Config:` | `model_config = ConfigDict(...)` | |
| `Config.orm_mode` | `ConfigDict(from_attributes=True)` | |
| `Config.schema_extra` | `ConfigDict(json_schema_extra={})` | |
| `__fields__` | `model_fields` | Struttura cambiata |
| `update_forward_refs()` | `model_rebuild()` | |

**Cambamenti di comportamento:**

- I validatori `@field_validator` richiedono il decoratore `@classmethod` esplicito (v1 lo applicava implicitamente).
- `mode='before'` sostituisce `pre=True` in `@validator`.
- I validatori `@model_validator(mode='after')` ricevono `self` (l'istanza del modello), non un dizionario come `@root_validator(pre=False)` in v1.
- La coercion di default e piu restrittiva in v2: ad esempio, `bool` non accetta piu stringhe arbitrarie come `"yes"` o `"no"`.

### Strumento Automatico: bump-pydantic

Il progetto `bump-pydantic` fornisce un tool CLI che automatizza gran parte della migrazione. Non copre tutti i casi, ma gestisce le rinominazioni piu comuni:

```bash
# Installazione
pip install bump-pydantic

# Esecuzione sulla codebase
bump-pydantic --diff .

# Applicazione delle modifiche
bump-pydantic .
```

`bump-pydantic` gestisce automaticamente:
- Rinominazione di `.dict()` → `.model_dump()`
- Rinominazione di `.json()` → `.model_dump_json()`
- Conversione di `class Config:` → `model_config = ConfigDict(...)`
- Conversione di `@validator` → `@field_validator` (parziale)
- Conversione di `orm_mode = True` → `from_attributes=True`

**Non gestisce** (richiedono intervento manuale):
- Conversione di `@root_validator` → `@model_validator` (la firma e completamente diversa)
- Logica nei validatori che dipende dalla firma v1
- Custom validators che usano `values` (il dizionario dei campi precedenti)
- Tipi personalizzati con `__get_validators__()` (v2 usa `__get_pydantic_core_schema__()`)

### Procedura di Migrazione Step-by-Step

**Step 1: Installare entrambe le versioni in parallelo.**

```bash
pip install pydantic>=2.0
pip install bump-pydantic
```

**Step 2: Eseguire bump-pydantic in modalita diff per valutare le modifiche.**

```bash
bump-pydantic --diff src/
```

**Step 3: Applicare le modifiche automatiche.**

```bash
bump-pydantic src/
```

**Step 4: Correggere manualmente i root_validator.**

```python
# v1 — root_validator
from pydantic import root_validator

class ModelloV1(BaseModel):
    inizio: date
    fine: date

    @root_validator
    def controlla_date(cls, values):
        if values.get('fine') and values.get('inizio'):
            if values['fine'] < values['inizio']:
                raise ValueError('Fine deve essere dopo inizio')
        return values

# v2 — model_validator
from pydantic import model_validator

class ModelloV2(BaseModel):
    inizio: date
    fine: date

    @model_validator(mode='after')
    def controlla_date(self):
        if self.fine < self.inizio:
            raise ValueError('Fine deve essere dopo inizio')
        return self
```

**Step 5: Migrare i validatori con `values`.**

```python
# v1 — accesso ai campi precedenti tramite 'values'
class V1(BaseModel):
    password: str
    conferma: str

    @validator('conferma')
    def password_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Le password non corrispondono')
        return v

# v2 — accesso tramite info.data
class V2(BaseModel):
    password: str
    conferma: str

    @field_validator('conferma')
    @classmethod
    def password_match(cls, v: str, info) -> str:
        if 'password' in info.data and v != info.data['password']:
            raise ValueError('Le password non corrispondono')
        return v
```

**Step 6: Eseguire i test e verificare la copertura.** La maggior parte dei bug di migrazione si manifesta come `ValidationError` inattesi o come cambiamenti nel comportamento di coercion.

**Step 7: Rimuovere i warning di deprecation.** Pydantic v2 emette warning quando si usano le API v1. Cercare e sostituire tutte le occorrenze rimanenti.

---

## Pydantic con SQLModel

### SQLModel: Il Ponte tra SQLAlchemy e Pydantic

SQLModel e una libreria creata dal creatore di FastAPI (Sebastian Ramirez) che unifica SQLAlchemy e Pydantic in un'unica classe. Un modello SQLModel e simultaneamente un modello Pydantic (con validazione) e un modello SQLAlchemy (con ORM e query):

```python
from sqlmodel import SQLModel, Field, Session, create_engine, select
from datetime import datetime
from typing import Optional

class Utente(SQLModel, table=True):
    """Modello che e sia tabella SQL che modello Pydantic."""
    id: int | None = Field(default=None, primary_key=True)
    nome: str = Field(min_length=2, max_length=50, index=True)
    email: str = Field(unique=True, index=True)
    attivo: bool = Field(default=True)
    creato_il: datetime = Field(default_factory=datetime.now)

# Crea la tabella
engine = create_engine("sqlite:///database.db")
SQLModel.metadata.create_all(engine)

# Inserimento con validazione Pydantic automatica
with Session(engine) as sessione:
    utente = Utente(nome="Marco Rossi", email="marco@example.com")
    sessione.add(utente)
    sessione.commit()
    sessione.refresh(utente)
    print(utente.id)  # ID generato dal database

# Query con risultati come modelli Pydantic
with Session(engine) as sessione:
    risultati = sessione.exec(select(Utente).where(Utente.attivo == True)).all()
    for u in risultati:
        # u e un modello Pydantic con tutti i metodi
        print(u.model_dump())
```

### Pattern: Modelli Separati per Input e Database

Seguendo le best practice, e consigliabile separare i modelli per input API (senza `table=True`) dai modelli per database:

```python
from sqlmodel import SQLModel, Field

# Modello base condiviso (campi comuni)
class UtenteBase(SQLModel):
    nome: str = Field(min_length=2, max_length=50)
    email: str
    reparto: str | None = None

# Modello per la creazione (input API — non e una tabella)
class UtenteCreate(UtenteBase):
    password: str = Field(min_length=8)

# Modello per l'aggiornamento (tutti i campi opzionali)
class UtenteUpdate(SQLModel):
    nome: str | None = None
    email: str | None = None
    reparto: str | None = None

# Modello per il database (e una tabella)
class Utente(UtenteBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    password_hash: str  # mai esposto all'API
    attivo: bool = True

# Modello per la risposta API (senza password)
class UtenteRead(UtenteBase):
    id: int
    attivo: bool
```

### Relazioni con SQLModel

SQLModel supporta relazioni tra modelli, combinando la potenza dell'ORM di SQLAlchemy con la validazione di Pydantic:

```python
from sqlmodel import SQLModel, Field, Relationship

class Team(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    nome: str = Field(min_length=1, unique=True)
    descrizione: str = ""

    # Relazione one-to-many
    membri: list["Membro"] = Relationship(back_populates="team")

class Membro(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    nome: str = Field(min_length=2)
    ruolo: str
    team_id: int | None = Field(default=None, foreign_key="team.id")

    # Relazione many-to-one
    team: Team | None = Relationship(back_populates="membri")
```

### Vantaggi e Limitazioni di SQLModel

**Vantaggi:**
- Un'unica definizione per schema dati, validazione e ORM
- Integrazione nativa con FastAPI (response model e request body)
- Meno boilerplate rispetto a SQLAlchemy + Pydantic separati
- Query type-safe con il supporto degli editor

**Limitazioni:**
- Non supporta tutte le feature avanzate di SQLAlchemy (es. composite keys complesse)
- La maturita del progetto e inferiore a SQLAlchemy
- Per query molto complesse, potrebbe essere necessario ricadere sull'API SQLAlchemy diretta
- Non supporta tutti i database supportati da SQLAlchemy

---

## Benchmark di Performance: Pydantic vs attrs vs dataclasses

### Contesto e Metodologia

La scelta tra Pydantic, attrs e dataclasses standard dipende fortemente dal caso d'uso. I benchmark seguenti misurano tre operazioni fondamentali: **istanziazione** (creazione di un oggetto), **validazione** (verifica dei vincoli) e **serializzazione** (conversione in dizionario/JSON).

Tutti i benchmark sono stati eseguiti con Python 3.12, Pydantic 2.9+, attrs 24.x e dataclasses standard, su un modello con 8 campi tipizzati.

### Risultati Comparativi

| Operazione | `dataclasses` | `attrs` | `attrs + cattrs` | `Pydantic v2` |
|---|---|---|---|---|
| Istanziazione semplice (no validazione) | ~0.3 µs | ~0.4 µs | ~0.4 µs | ~1.5 µs |
| Istanziazione con validazione | N/A (manuale) | ~0.8 µs (con validators) | ~1.2 µs | ~1.5 µs |
| Serializzazione a dict | ~0.6 µs (`asdict()`) | ~0.7 µs | ~0.9 µs | ~0.8 µs |
| Serializzazione JSON | ~2.5 µs (manuale) | ~2.0 µs | ~1.8 µs | ~0.9 µs |
| Validazione da dict esterno | N/A | N/A (manuale) | ~2.0 µs | ~1.5 µs |
| Validazione da JSON string | N/A | N/A | ~3.0 µs | ~1.2 µs |

### Analisi dei Risultati

**Istanziazione:** Le dataclass standard sono le piu veloci perche non eseguono nessuna validazione. Pydantic v2 e ~5x piu lento delle dataclass per la sola istanziazione, ma il costo include la validazione completa. In v1, il gap era ~15x.

**Serializzazione JSON:** Qui Pydantic v2 eccelle grazie al motore Rust, superando sia dataclass (che richiedono `json.dumps(asdict(obj))`) sia attrs con cattrs. La serializzazione JSON e uno dei punti di forza piu evidenti di pydantic-core.

**Validazione da input esterno:** Questo e lo scenario dove Pydantic non ha rivali. Ne dataclass ne attrs offrono validazione integrata da dizionari o JSON. Per replicare lo stesso livello di validazione, serve codice custom o cattrs configurato ad hoc, che in genere e piu lento di Pydantic v2.

### Linee Guida per la Scelta

```
                 Input esterno?
                 (API, JSON, utente)
                    /       \
                  Si          No
                  |            |
             Pydantic      Performance
             BaseModel      critica?
                            /     \
                          Si       No
                          |        |
                     dataclass   attrs
                                  o
                                dataclass
```

**Regola pratica:** in applicazioni I/O-bound (la maggior parte delle web app e dei servizi), la differenza di performance tra Pydantic e dataclasses e irrilevante. Il collo di bottiglia e la rete, il database o il filesystem, non la validazione in-memory. Scegliere in base alle feature necessarie, non ai microsecondi.

Per contesti ad alta frequenza (elaborazione di milioni di record in-memory, hot loops di calcolo), le dataclasses standard o attrs sono scelte migliori per le strutture dati interne, con Pydantic usato solo ai boundary del sistema.

### Benchmark di Memoria

Oltre alla velocita, il consumo di memoria e un fattore critico per applicazioni che gestiscono molte istanze contemporaneamente:

| Struttura | Memoria per istanza (8 campi) | Note |
|---|---|---|
| `dict` | ~400 bytes | Nessuna validazione, nessun tipo |
| `dataclass` | ~200 bytes | Con `__slots__` scende a ~150 bytes |
| `attrs` (slotted) | ~150 bytes | Default con `__slots__` |
| `Pydantic v2 BaseModel` | ~300 bytes | Include metadati di validazione |
| `Pydantic v2 dataclass` | ~180 bytes | Piu leggero di BaseModel |

La differenza diventa significativa con centinaia di migliaia di istanze in memoria. Per modelli che fungono solo da contenitori dati interni (senza necessita di validazione runtime), le Pydantic dataclass con `__slots__` offrono un buon compromesso tra validazione e footprint di memoria.

### Ottimizzazione delle Performance in Pydantic v2

Alcune tecniche per massimizzare le performance di Pydantic v2:

```python
from pydantic import TypeAdapter

# 1. Pre-compilare il validatore per tipi usati ripetutamente
adapter_lista_utenti = TypeAdapter(list[Utente])

# Il validatore e gia compilato, ogni chiamata successiva e veloce
utenti = adapter_lista_utenti.validate_python(dati_raw)

# 2. Usare model_validate invece di __init__ per input da dict
# Evita la doppia conversione dict -> kwargs -> validazione
utente = Utente.model_validate(dati_dict)  # piu veloce di Utente(**dati_dict)

# 3. Disabilitare la validazione quando i dati sono gia validati
utente = Utente.model_construct(**dati_gia_validati)

# 4. Usare model_dump_json() invece di json.dumps(model_dump())
# Il motore Rust serializza direttamente, bypassando Python
json_bytes = utente.model_dump_json()  # ~2x piu veloce

# 5. Evitare computed_field in modelli ad alta frequenza
# Se il valore cambia raramente, pre-calcolarlo nel model_validator
```

### Profiling e Misurazione

Per misurare le performance nel proprio contesto specifico, usare `timeit` con cautela:

```python
import timeit

# Misurare creazione con validazione
tempo_pydantic = timeit.timeit(
    lambda: Utente(nome="Mario", email="mario@example.com", eta=30),
    number=100_000
)

# Misurare serializzazione JSON
utente = Utente(nome="Mario", email="mario@example.com", eta=30)
tempo_json = timeit.timeit(
    lambda: utente.model_dump_json(),
    number=100_000
)

print(f"Creazione: {tempo_pydantic / 100_000 * 1_000_000:.2f} µs/op")
print(f"JSON: {tempo_json / 100_000 * 1_000_000:.2f} µs/op")
```

I risultati variano significativamente in base alla complessita del modello: modelli con validatori custom, computed fields e nested models saranno naturalmente piu lenti di modelli con soli campi tipizzati. Profilare sempre il caso d'uso reale, non un benchmark sintetico generico.

---

## Pydantic AI — Output Strutturato per LLM

### Cos'e Pydantic AI

Pydantic AI e un framework Python sviluppato dal team Pydantic per costruire agenti LLM che producono **output strutturati e validati**. Invece di ricevere stringhe di testo libero dai modelli di linguaggio e parsarle manualmente, Pydantic AI garantisce che l'output sia conforme a un modello Pydantic, con validazione automatica e retry in caso di errore.

```python
from pydantic_ai import Agent
from pydantic import BaseModel

class AnalisiSentimento(BaseModel):
    """Risultato dell'analisi del sentimento."""
    testo_originale: str
    sentimento: str  # "positivo", "negativo", "neutro"
    punteggio: float  # da -1.0 a 1.0
    parole_chiave: list[str]

# Definizione dell'agente con output strutturato
agente = Agent(
    'anthropic:claude-opus-4-7',
    result_type=AnalisiSentimento,
    system_prompt='Analizza il sentimento del testo fornito. Rispondi in italiano.',
)

# L'output e un modello Pydantic validato, non una stringa
risultato = agente.run_sync('Il servizio clienti e stato eccellente, molto soddisfatto!')
print(risultato.data)
# AnalisiSentimento(
#   testo_originale='Il servizio clienti...',
#   sentimento='positivo',
#   punteggio=0.9,
#   parole_chiave=['servizio', 'eccellente', 'soddisfatto']
# )
```

### Structured Output con OpenAI e Anthropic

Anche senza Pydantic AI, i modelli Pydantic possono essere usati direttamente con le API di OpenAI e Anthropic per generare output strutturato. Il JSON Schema generato da Pydantic viene passato al modello come vincolo di formato:

```python
from pydantic import BaseModel, Field
from typing import Literal
import json

class EntitaEstratta(BaseModel):
    """Schema per l'estrazione di entita da testo."""
    nome: str = Field(description="Nome dell'entita")
    tipo: Literal["persona", "organizzazione", "luogo", "data", "importo"]
    contesto: str = Field(description="Frase o contesto in cui appare l'entita")
    confidenza: float = Field(ge=0, le=1, description="Livello di confidenza 0-1")

class RisultatoEstrazione(BaseModel):
    """Risultato dell'estrazione di entita dal testo."""
    testo_analizzato: str
    entita: list[EntitaEstratta]
    lingua: str

# Lo schema JSON viene passato all'API come vincolo
schema = RisultatoEstrazione.model_json_schema()

# Con OpenAI (response_format structured output)
# client.chat.completions.create(
#     model="gpt-4o",
#     response_format={
#         "type": "json_schema",
#         "json_schema": {
#             "name": "estrazione_entita",
#             "schema": schema,
#             "strict": True
#         }
#     },
#     messages=[...]
# )

# Il JSON ricevuto viene validato con Pydantic
# risultato = RisultatoEstrazione.model_validate_json(risposta_json)
```

### Dependency Injection e Testing

Pydantic AI supporta dependency injection (ispirata a FastAPI) e un modello di test (`TestModel`) che permette di testare gli agenti senza chiamare API esterne:

```python
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel
from pydantic import BaseModel

class Riassunto(BaseModel):
    titolo: str
    punti_chiave: list[str]
    lunghezza_originale: int

agente = Agent(
    'anthropic:claude-opus-4-7',
    result_type=Riassunto,
)

# Testing senza API calls
with agente.override(model=TestModel()):
    risultato = agente.run_sync('Testo lungo da riassumere...')
    # TestModel genera output strutturato di esempio
    assert isinstance(risultato.data, Riassunto)
    assert isinstance(risultato.data.punti_chiave, list)
```

### Validazione e Retry Automatico

Quando l'output del modello non supera la validazione Pydantic, Pydantic AI puo automaticamente riprovare con un prompt correttivo che include gli errori di validazione:

```python
from pydantic_ai import Agent
from pydantic import BaseModel, Field, field_validator

class CodiceStrutturato(BaseModel):
    linguaggio: str
    codice: str = Field(min_length=10)
    spiegazione: str = Field(min_length=20)

    @field_validator('linguaggio')
    @classmethod
    def linguaggio_supportato(cls, v: str) -> str:
        supportati = {'python', 'javascript', 'typescript', 'rust', 'go'}
        if v.lower() not in supportati:
            raise ValueError(f'Linguaggio non supportato. Ammessi: {supportati}')
        return v.lower()

agente = Agent(
    'anthropic:claude-opus-4-7',
    result_type=CodiceStrutturato,
    retries=3,  # massimo 3 tentativi se la validazione fallisce
)
```

Se il primo tentativo del modello produce un linguaggio non supportato (es. "Java"), Pydantic AI rinvia al modello con l'errore specifico, permettendogli di correggere l'output nel tentativo successivo.

### Tool e Function Calling con Pydantic

Pydantic AI integra il concetto di tool (funzioni che l'agente puo invocare) con validazione Pydantic su input e output:

```python
from pydantic_ai import Agent, RunContext
from pydantic import BaseModel, Field

class InfoMeteo(BaseModel):
    citta: str
    temperatura: float = Field(description="Temperatura in Celsius")
    condizioni: str
    umidita: int = Field(ge=0, le=100)

class DipendenzaDB:
    """Simulazione di un database per le citta."""
    async def cerca_meteo(self, citta: str) -> dict:
        # In produzione: chiamata a un servizio meteo reale
        return {"citta": citta, "temperatura": 22.5,
                "condizioni": "soleggiato", "umidita": 45}

agente_meteo = Agent(
    'anthropic:claude-opus-4-7',
    result_type=InfoMeteo,
    deps_type=DipendenzaDB,
)

@agente_meteo.tool
async def ottieni_meteo(ctx: RunContext[DipendenzaDB], citta: str) -> dict:
    """Ottieni le informazioni meteo per una citta."""
    return await ctx.deps.cerca_meteo(citta)
```

Il decoratore `@agente_meteo.tool` registra la funzione come tool disponibile per l'agente. Pydantic valida automaticamente sia i parametri passati dall'LLM al tool, sia il risultato finale restituito dall'agente. Questo garantisce che anche le interazioni intermedie siano type-safe.

### Confronto con Instructor e Outlines

Pydantic AI non e l'unico framework per output strutturato. Un confronto rapido:

| Feature | Pydantic AI | Instructor | Outlines |
|---|---|---|---|
| Validazione output | Pydantic nativa | Pydantic nativa | JSON Schema |
| Agenti multi-step | Si | No (solo singola chiamata) | No |
| Tool calling | Si, con DI | No | No |
| Streaming strutturato | Si (parziale) | Si | Si |
| Testing senza API | TestModel integrato | Mock manuale | Mock manuale |
| Modelli supportati | OpenAI, Anthropic, Gemini, Groq, Ollama | OpenAI, Anthropic, Gemini, Cohere | Locale (transformers, llama.cpp) |

Per applicazioni semplici di "LLM -> output strutturato" senza agenti, **Instructor** e piu leggero. Per pipeline agentiche con tool calling e dependency injection, **Pydantic AI** offre un framework piu completo. **Outlines** eccelle nel constrained decoding locale, dove il token sampling stesso viene guidato dalla grammatica del JSON Schema.

---

## Strategie di Testing per Modelli Pydantic

### Testing Unitario dei Modelli

Il testing dei modelli Pydantic si concentra su tre aspetti: validazione corretta (i dati validi vengono accettati), rifiuto dei dati invalidi (errori appropriati), e trasformazioni (i validatori producono i valori attesi).

```python
import pytest
from pydantic import ValidationError
from datetime import date

# Assumendo il modello RecordDipendente definito precedentemente

class TestRecordDipendente:
    """Test suite per il modello RecordDipendente."""

    def test_creazione_valida(self):
        """Verifica che dati validi creino un'istanza corretta."""
        record = RecordDipendente(
            matricola="AB123456",
            nome="Marco",
            cognome="Rossi",
            data_assunzione=date(2020, 1, 15),
            reparto="IT",
            ral=45000,
            livello=5,
        )
        assert record.matricola == "AB123456"
        assert record.reparto == "IT"  # normalizzato a uppercase

    def test_matricola_invalida(self):
        """Verifica che matricole con formato errato vengano rifiutate."""
        with pytest.raises(ValidationError) as exc_info:
            RecordDipendente(
                matricola="INVALIDA",
                nome="Marco",
                cognome="Rossi",
                data_assunzione=date(2020, 1, 15),
                reparto="IT",
                ral=45000,
                livello=5,
            )
        errori = exc_info.value.errors()
        assert len(errori) == 1
        assert errori[0]['loc'] == ('matricola',)
        assert errori[0]['type'] == 'string_pattern_mismatch'

    def test_data_futura_rifiutata(self):
        """Verifica che date di assunzione future vengano rifiutate."""
        from datetime import timedelta
        with pytest.raises(ValidationError) as exc_info:
            RecordDipendente(
                matricola="AB123456",
                nome="Marco",
                cognome="Rossi",
                data_assunzione=date.today() + timedelta(days=1),
                reparto="IT",
                ral=45000,
                livello=5,
            )
        assert 'futuro' in str(exc_info.value).lower()

    def test_normalizzazione_reparto(self):
        """Verifica che il reparto venga normalizzato a uppercase."""
        record = RecordDipendente(
            matricola="AB123456",
            nome="Marco",
            cognome="Rossi",
            data_assunzione=date(2020, 1, 15),
            reparto="it",  # minuscolo
            ral=45000,
            livello=5,
        )
        assert record.reparto == "IT"

    def test_errori_multipli(self):
        """Verifica che tutti gli errori vengano riportati in una volta."""
        with pytest.raises(ValidationError) as exc_info:
            RecordDipendente(
                matricola="INVALIDA",
                nome="",
                cognome="Rossi",
                data_assunzione=date(2020, 1, 15),
                reparto="INVALIDO",
                ral=-1000,
                livello=10,
            )
        errori = exc_info.value.errors()
        assert len(errori) >= 3  # almeno matricola, nome, reparto
```

### Fixture e Factory per i Test

Per modelli con molti campi, le factory facilitano la creazione di istanze di test con valori di default ragionevoli:

```python
import pytest
from datetime import date
from decimal import Decimal

@pytest.fixture
def dati_dipendente_validi() -> dict:
    """Factory per dati validi di un dipendente."""
    return {
        "matricola": "AB123456",
        "nome": "Marco",
        "cognome": "Rossi",
        "data_assunzione": date(2020, 1, 15),
        "reparto": "IT",
        "ral": Decimal("45000.00"),
        "livello": 5,
        "attivo": True,
    }

def crea_dipendente(**overrides) -> dict:
    """Factory function per creare dati dipendente con override."""
    dati = {
        "matricola": "AB123456",
        "nome": "Marco",
        "cognome": "Rossi",
        "data_assunzione": date(2020, 1, 15),
        "reparto": "IT",
        "ral": Decimal("45000.00"),
        "livello": 5,
        "attivo": True,
    }
    dati.update(overrides)
    return dati


class TestConFactory:
    def test_livello_minimo(self):
        dati = crea_dipendente(livello=1)
        record = RecordDipendente(**dati)
        assert record.livello == 1

    def test_livello_zero_rifiutato(self):
        dati = crea_dipendente(livello=0)
        with pytest.raises(ValidationError):
            RecordDipendente(**dati)

    def test_ral_negativa_rifiutata(self):
        dati = crea_dipendente(ral=Decimal("-1"))
        with pytest.raises(ValidationError):
            RecordDipendente(**dati)
```

### Testing della Serializzazione

Verificare che la serializzazione produca l'output atteso e fondamentale, specialmente quando si usano serializzatori custom o alias:

```python
from pydantic import BaseModel, field_serializer
from datetime import datetime
import json

class TestSerialization:
    def test_model_dump_include(self):
        """Verifica che include filtri i campi correttamente."""
        evento = EventoLog(
            timestamp=datetime(2026, 1, 1),
            livello="INFO",
            messaggio="Test",
        )
        dump = evento.model_dump(include={'livello', 'messaggio'})
        assert 'timestamp' not in dump
        assert dump['livello'] == 'INFO'

    def test_model_dump_exclude_none(self):
        """Verifica che exclude_none rimuova i campi None."""
        evento = EventoLog(
            timestamp=datetime(2026, 1, 1),
            livello="INFO",
            messaggio="Test",
        )
        dump = evento.model_dump(exclude_none=True)
        assert 'dettagli' not in dump
        assert 'id_correlazione' not in dump

    def test_json_round_trip(self):
        """Verifica che la serializzazione/deserializzazione sia round-trip safe."""
        evento = EventoLog(
            timestamp=datetime(2026, 1, 1, 12, 0),
            livello="ERROR",
            messaggio="Errore critico",
            sorgente="api",
        )
        json_str = evento.model_dump_json()
        ricostruito = EventoLog.model_validate_json(json_str)
        assert ricostruito.livello == evento.livello
        assert ricostruito.messaggio == evento.messaggio
```

### Testing di model_validator e Vincoli Cross-Field

```python
class TestValidazioneIncrociata:
    def test_date_ordinate(self):
        """La data di fine deve essere dopo la data di inizio."""
        intervallo = IntervalloDate(
            data_inizio=date(2026, 1, 1),
            data_fine=date(2026, 12, 31),
        )
        assert intervallo.data_fine > intervallo.data_inizio

    def test_date_invertite_rifiutate(self):
        """Date invertite devono sollevare ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            IntervalloDate(
                data_inizio=date(2026, 12, 31),
                data_fine=date(2026, 1, 1),
            )
        assert 'successiva' in str(exc_info.value).lower()

    def test_stesse_date_accettate(self):
        """Date uguali devono essere accettate (non e un errore)."""
        intervallo = IntervalloDate(
            data_inizio=date(2026, 6, 15),
            data_fine=date(2026, 6, 15),
        )
        assert intervallo.data_inizio == intervallo.data_fine
```

### Parametrized Testing per Validazione di Range

Pytest `@parametrize` e ideale per testare i boundary dei vincoli:

```python
import pytest

class TestVincoliNumerici:
    @pytest.mark.parametrize("eta,valido", [
        (0, True),
        (1, True),
        (150, True),
        (-1, False),
        (151, False),
        (None, False),
    ])
    def test_range_eta(self, eta, valido):
        if valido:
            utente = Utente(nome="Test", email="test@example.com", eta=eta)
            assert utente.eta == eta
        else:
            with pytest.raises(ValidationError):
                Utente(nome="Test", email="test@example.com", eta=eta)

    @pytest.mark.parametrize("prezzo,atteso", [
        ("29,99", 29.99),     # formato italiano
        ("29.99", 29.99),     # formato internazionale
        (29.99, 29.99),       # gia float
        ("100", 100.0),       # intero come stringa
    ])
    def test_conversione_prezzo(self, prezzo, atteso):
        prodotto = Prodotto(prezzo=prezzo, codice="ABC")
        assert prodotto.prezzo == atteso
```

### Testing delle Discriminated Unions

```python
class TestDiscriminatedUnion:
    def test_tipo_carta(self):
        ordine = Ordine(
            codice_ordine="ORD-001",
            importo=99.99,
            pagamento={
                "tipo": "carta",
                "numero_carta": "4111111111111111",
                "scadenza": "12/28",
                "cvv": "123"
            }
        )
        assert isinstance(ordine.pagamento, PagamentoCarta)

    def test_tipo_non_riconosciuto(self):
        with pytest.raises(ValidationError):
            Ordine(
                codice_ordine="ORD-001",
                importo=99.99,
                pagamento={"tipo": "bitcoin", "indirizzo": "abc"}
            )

    def test_round_trip_union(self):
        """Verifica round-trip per ogni tipo nella union."""
        for dati_pagamento in [
            {"tipo": "carta", "numero_carta": "4111111111111111",
             "scadenza": "12/28", "cvv": "123"},
            {"tipo": "bonifico", "iban": "IT60X0542811101000000123456",
             "intestatario": "Mario Rossi"},
            {"tipo": "paypal", "email": "utente@example.com"},
        ]:
            ordine = Ordine(
                codice_ordine="ORD-001",
                importo=99.99,
                pagamento=dati_pagamento
            )
            json_str = ordine.model_dump_json()
            ricostruito = Ordine.model_validate_json(json_str)
            assert type(ricostruito.pagamento) == type(ordine.pagamento)
```

---

## Esercizi

1. **Modelli Pydantic per e-commerce** — Definisci modelli Pydantic per un sistema e-commerce: `Prodotto`, `Ordine`, `Cliente`, `Indirizzo`. Implementa: validatori custom per codice fiscale/partita IVA, discriminated union per tipi di pagamento (carta, bonifico, PayPal), `model_validator` per verificare che la data di spedizione sia successiva alla data di ordine. Scrivi test per ogni validazione.

2. **BaseSettings per configurazione** — Crea una classe `AppSettings(BaseSettings)` che carichi configurazione da: variabili d'ambiente, file `.env`, file TOML, e valori di default. Includi validazione per URL, porte, secret con lunghezza minima, e enum per l'ambiente (dev/staging/prod). Usa `@lru_cache` per il singleton e scrivi test che verifichino la precedenza delle fonti.

3. **Serializzazione custom** — Implementa modelli Pydantic con `model_serializer` e `field_serializer` per produrre output JSON personalizzato: date in formato ISO 8601, enum come valori human-readable, campi sensibili mascherati, e nested model come flat JSON. Verifica che `model_dump()` e `model_dump_json()` producano l'output atteso.

4. **Integrazione FastAPI + Pydantic** — Costruisci una mini-API FastAPI con almeno 3 endpoint che utilizzino modelli Pydantic per: request body validation, response model con `model_config`, query parameter validation con `Field`, e error handling con `RequestValidationError`. Verifica che la documentazione OpenAPI generata sia corretta e completa.

5. **Migration da Pydantic v1 a v2** — Prendi un modulo con almeno 5 modelli Pydantic v1 (con `validator`, `Config` class, `schema_extra`) e migralo a v2 (con `field_validator`, `model_config`, `json_schema_extra`). Usa `bump-pydantic` come punto di partenza e documenta le modifiche manuali necessarie. Verifica che tutti i test passino dopo la migrazione.

---

## Letture e Riferimenti

### Fonti primarie

- Pydantic Documentation — https://docs.pydantic.dev/ (consultato: 2026-05-24)
- Pydantic Settings Documentation — https://docs.pydantic.dev/latest/concepts/pydantic_settings/ (consultato: 2026-05-24)
- Pydantic Migration Guide v1 → v2 — https://docs.pydantic.dev/latest/migration/ (consultato: 2026-05-24)
- Python Documentation — *`typing` module* — https://docs.python.org/3/library/typing.html (consultato: 2026-05-24)
- FastAPI Documentation — *Request Body* — https://fastapi.tiangolo.com/tutorial/body/ (consultato: 2026-05-24)
- bump-pydantic — https://github.com/pydantic/bump-pydantic (consultato: 2026-05-24)

### Libri consigliati

- *Robust Python* — Patrick Viafore — O'Reilly, 2021

---

## Riferimenti Incrociati

| Modulo | Relazione |
|---|---|
| [09 — Type Hints e Mypy](09-type-hints-e-mypy.md) | Type hints fondamentali per i modelli Pydantic |
| [13 — REST API](13-rest-api.md) | Validazione request/response in FastAPI con Pydantic |
| [14 — Data Processing](14-data-processing.md) | Validazione dati in pipeline ETL con pandera e Pydantic |
| [12 — Database](12-database.md) | Integrazione Pydantic con SQLAlchemy per ORM type-safe |
| [07 — Error Handling](07-error-handling-e-logging.md) | Gestione ValidationError e error reporting strutturato |
| [22 — Clean Code](22-clean-code.md) | Modelli come documentazione vivente, naming e design |

---

## Glossario

| Termine | Definizione |
|---|---|
| **BaseModel** | Classe base Pydantic per definire modelli dati con validazione automatica basata su type hints |
| **Field** | Funzione Pydantic per configurare metadati, vincoli e validazione di singoli campi del modello |
| **Validatore** | Funzione decorata con `@field_validator` o `@model_validator` che aggiunge logica di validazione custom |
| **Discriminated Union** | Pattern che usa un campo discriminatore per selezionare automaticamente il tipo corretto in una union |
| **BaseSettings** | Sottoclasse di BaseModel specializzata per la gestione di configurazioni da env, file e secrets |
| **Serializzazione** | Processo di conversione di un modello Pydantic in dict (`model_dump()`) o JSON (`model_dump_json()`) |
| **JSON Schema** | Schema generato automaticamente da Pydantic che descrive la struttura e i vincoli del modello |
| **model_config** | Attributo di classe che configura il comportamento del modello (strict mode, alias, extra fields) |
| **Coercion** | Conversione automatica di tipi durante la validazione (es. stringa `"42"` → intero `42`) |
| **Strict Mode** | Modalita Pydantic che disabilita la coercion, richiedendo tipi esatti |
| **ValidationError** | Eccezione sollevata quando i dati non superano la validazione, con dettagli strutturati sugli errori |
