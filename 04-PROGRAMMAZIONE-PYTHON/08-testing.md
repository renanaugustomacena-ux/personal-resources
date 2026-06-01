---
corso: "Programmazione Python"
fase: "5 — Qualità e Manutenzione"
modulo: "08"
titolo: "Testing in Python"
versione: "pytest 8.x / Python 3.12+"
livello: "Intermedio"
prerequisiti:
  - "01-06 — Python Base"
  - "07 — OOP"
  - "03 — Funzioni e Scope"
obiettivi:
  - "Padroneggiare pytest per unit, integration e E2E testing"
  - "Utilizzare fixture, parametrize, marker e plugin"
  - "Implementare TDD con il ciclo Red-Green-Refactor"
  - "Applicare mocking e patching con unittest.mock"
  - "Misurare e interpretare la coverage del codice"
  - "Configurare testing nella pipeline CI/CD"
tag: [testing, pytest, TDD, coverage, mocking, fixture, CI, hypothesis]
---

# Testing in Python — Guida Completa

> **Modulo 08** · **Aggiornamento:** 2026-05-24 · **Versione:** pytest 8.x / Python 3.12+

> ### Obiettivi di apprendimento
>
> **Prerequisiti:** [Python Base](01-fondamenti-linguaggio.md), [OOP](02-oop.md), [Funzioni e Scope](03-funzioni-scope.md)
>
> Al termine di questo modulo saprai:
> 1. Padroneggiare pytest per unit, integration e E2E testing
> 2. Utilizzare fixture, parametrize, marker e plugin per test organizzati
> 3. Implementare TDD con il ciclo Red-Green-Refactor
> 4. Applicare mocking e patching con `unittest.mock` e `pytest-mock`
> 5. Misurare e interpretare la coverage con `pytest-cov`
> 6. Configurare testing automatizzato nella pipeline CI/CD
>
> **Tempo stimato:** 6-8 ore · **Livello:** Intermedio

## Idee guida
1. **pytest > unittest. Period.**
2. **Fixture > setUp/tearDown.**
3. **parametrize per data-driven tests.**
4. **Coverage 80%+ minimum; pytest-cov.**


## Mappa concettuale

```
                ┌─────────────────────────┐
                │   TESTING IN PYTHON     │
                └────────────┬────────────┘
                             │
        ┌────────────────────┼─────────────────────┐
        │                    │                      │
  ┌─────▼─────┐      ┌──────▼──────┐      ┌───────▼───────┐
  │  pytest    │      │  Mocking    │      │  Patterns &   │
  │ Framework  │      │  & Fakes    │      │  Methodology  │
  └─────┬─────┘      └──────┬──────┘      └───────┬───────┘
        │                    │                      │
  ┌─────┴──────┐     ┌──────┴──────┐      ┌───────┴───────┐
  │fixtures    │     │Mock/Magic   │      │TDD Red-Green  │
  │parametrize │     │AsyncMock    │      │AAA / GWT      │
  │markers     │     │patch        │      │Property-based │
  │conftest.py │     │spec/side_fx │      │Snapshot       │
  │plugins     │     │responses    │      │Mutation       │
  └─────┬──────┘     └──────┬──────┘      └───────┬───────┘
        │                    │                      │
        └──────────┬─────────┴──────────┬───────────┘
                   │                    │
          ┌────────▼──────┐    ┌───────▼───────┐
          │  Coverage &   │    │ Integration & │
          │  Quality      │    │ Infra         │
          │  (branch,     │    │ (testcontain. │
          │   threshold)  │    │  factory_boy, │
          └───────────────┘    │  faker)       │
                               └───────────────┘
```

## Indice

1. [Panoramica](#panoramica)
2. [pytest](#pytest)
3. [conftest.py Deep Dive](#conftest-deep-dive)
4. [unittest](#unittest)
5. [Mocking](#mocking)
6. [Testing Patterns](#testing-patterns)
7. [Coverage](#coverage)
8. [Integration Testing](#integration-testing)
9. [Test Data: factory_boy e Faker](#test-data-factory_boy-e-faker)
10. [Testcontainers Deep Dive](#testcontainers-deep-dive)
11. [Testing Asincrono con pytest-asyncio](#testing-asincrono-con-pytest-asyncio)
12. [Snapshot Testing](#snapshot-testing)
13. [Mutation Testing con mutmut](#mutation-testing-con-mutmut)
14. [Property-Based Testing](#property-based-testing)
15. [TDD Workflow Deep Dive](#tdd-workflow-deep-dive)
16. [Performance Testing](#performance-testing)
17. [Ecosistema Plugin pytest](#ecosistema-plugin-pytest)
18. [CI/CD Integration](#cicd-integration)
19. [Best Practices](#best-practices)
20. [Esercizi](#esercizi)
21. [Letture](#letture)
22. [Glossario](#glossario)

---

## Panoramica

Il testing del software rappresenta una delle discipline fondamentali nello sviluppo professionale. Scrivere test non significa semplicemente verificare che il codice funzioni oggi, ma costruire una rete di sicurezza che protegge il progetto nel tempo, durante refactoring, aggiornamenti di dipendenze e aggiunta di nuove funzionalita.

### La Piramide del Testing

La piramide del testing e un modello concettuale che descrive la distribuzione ideale dei test in un progetto software. Alla base si trovano i test piu numerosi e veloci, mentre al vertice quelli piu costosi e lenti.

**Unit Test** — costituiscono la base della piramide. Testano singole funzioni, metodi o classi in completo isolamento. Sono estremamente rapidi (millisecondi), facili da scrivere e da mantenere. Un progetto maturo dovrebbe avere centinaia o migliaia di unit test.

```python
# Esempio di unit test
def calcola_sconto(prezzo, percentuale):
    if percentuale < 0 or percentuale > 100:
        raise ValueError("Percentuale non valida")
    return prezzo * (1 - percentuale / 100)

def test_calcola_sconto():
    assert calcola_sconto(100, 20) == 80.0

def test_calcola_sconto_zero():
    assert calcola_sconto(100, 0) == 100.0

def test_calcola_sconto_invalido():
    with pytest.raises(ValueError):
        calcola_sconto(100, -5)
```

**Integration Test** — occupano la fascia intermedia. Verificano che diversi componenti del sistema funzionino correttamente quando interagiscono tra loro: accesso al database, chiamate API, interazione tra moduli. Sono piu lenti degli unit test e richiedono piu setup, ma catturano errori che gli unit test non possono individuare.

**End-to-End Test (E2E)** — si trovano al vertice della piramide. Simulano il comportamento completo dell'utente attraverso l'intera applicazione. Sono i piu lenti, fragili e costosi da mantenere, ma verificano che il sistema funzioni nel suo complesso. Strumenti come Selenium, Playwright o Cypress vengono utilizzati per i test E2E di applicazioni web.

La distribuzione ideale suggerisce circa il 70% di unit test, il 20% di integration test e il 10% di E2E test, anche se queste proporzioni variano in base alla natura del progetto.

### TDD vs BDD

**Test-Driven Development (TDD)** e una metodologia che inverte il flusso tradizionale di sviluppo. Il ciclo si articola in tre fasi note come Red-Green-Refactor:

1. **Red** — scrivi un test che fallisce perche la funzionalita non esiste ancora
2. **Green** — scrivi il codice minimo necessario per far passare il test
3. **Refactor** — migliora il codice mantenendo tutti i test verdi

Il TDD forza il programmatore a pensare all'interfaccia e al comportamento atteso prima dell'implementazione, producendo codice piu modulare e testabile.

**Behavior-Driven Development (BDD)** estende il TDD concentrandosi sul comportamento del sistema dal punto di vista dell'utente. I test BDD vengono scritti in un linguaggio semi-naturale (spesso con sintassi Given-When-Then) che facilita la comunicazione tra sviluppatori, tester e stakeholder non tecnici.

### Obiettivi di Test Coverage

La test coverage misura quale percentuale del codice sorgente viene eseguita durante i test. E un indicatore utile ma non sufficiente: una coverage del 100% non garantisce l'assenza di bug, ma una coverage bassa e certamente un segnale di rischio.

Obiettivi ragionevoli:
- **80%** — soglia minima per progetti professionali
- **90%+** — consigliato per librerie e componenti critici
- **100%** — realistico solo per moduli piccoli e ben definiti

E fondamentale distinguere tra line coverage e branch coverage. La branch coverage e piu rigorosa perche verifica che ogni ramo condizionale (if/else, try/except) venga attraversato.

---

## pytest

pytest e il framework di testing piu utilizzato nell'ecosistema Python moderno. Offre una sintassi concisa, un sistema di plugin estensibile e funzionalita avanzate come fixtures parametrizzate e autodiscovery dei test.

### Fondamenti

#### Test Discovery

pytest segue convenzioni precise per individuare automaticamente i file e le funzioni di test:

- I file devono chiamarsi `test_*.py` oppure `*_test.py`
- Le funzioni di test devono iniziare con `test_`
- Le classi di test devono iniziare con `Test` (senza metodo `__init__`)
- I metodi nelle classi di test devono iniziare con `test_`

```
progetto/
    src/
        calcolatrice.py
    tests/
        __init__.py
        test_calcolatrice.py
        test_validazione.py
        conftest.py
```

#### Assert Statements

Una delle caratteristiche piu apprezzate di pytest e l'uso diretto delle istruzioni `assert` di Python, senza la necessita di metodi specifici come `assertEqual` o `assertTrue`. pytest riscrive internamente le assert per fornire messaggi di errore estremamente dettagliati in caso di fallimento.

```python
def test_confronto_liste():
    risultato = [1, 2, 3, 4]
    atteso = [1, 2, 3, 5]
    assert risultato == atteso
    # Output dettagliato:
    # AssertionError: assert [1, 2, 3, 4] == [1, 2, 3, 5]
    #   At index 3 diff: 4 != 5

def test_stringa_contenuta():
    messaggio = "Benvenuto nello studio"
    assert "studio" in messaggio

def test_approssimazione():
    # Per confronti con numeri floating-point
    assert 0.1 + 0.2 == pytest.approx(0.3)

def test_tipo():
    risultato = {"chiave": "valore"}
    assert isinstance(risultato, dict)
```

#### Esecuzione dei Test

```bash
# Esegui tutti i test nella directory corrente
pytest

# Output verboso con dettagli su ogni test
pytest -v

# Esegui solo i test che contengono "sconto" nel nome
pytest -k "sconto"

# Ferma all'esecuzione al primo fallimento
pytest -x

# Ferma dopo N fallimenti
pytest --maxfail=3

# Esegui un file specifico
pytest tests/test_calcolatrice.py

# Esegui un test specifico
pytest tests/test_calcolatrice.py::test_addizione

# Esegui una classe specifica
pytest tests/test_calcolatrice.py::TestOperazioni

# Esegui un metodo specifico di una classe
pytest tests/test_calcolatrice.py::TestOperazioni::test_moltiplicazione

# Mostra l'output di print() durante i test
pytest -s

# Mostra i test piu lenti
pytest --durations=10
```

#### Interpretazione dell'Output

L'output di pytest usa simboli compatti:
- `.` (punto) — test passato
- `F` — test fallito (assertion error)
- `E` — errore durante l'esecuzione (eccezione inattesa)
- `s` — test saltato (skip)
- `x` — test che ci si aspettava fallisse ed effettivamente fallisce (xfail)
- `X` — test che ci si aspettava fallisse ma e passato (xpass)

```
tests/test_calcolo.py ..F.s.x    [100%]
```

### Fixtures

Le fixtures sono il meccanismo di pytest per gestire il setup e il teardown dei test. Forniscono dati, oggetti o risorse necessari ai test, eliminando la duplicazione del codice di inizializzazione.

#### @pytest.fixture Base

```python
import pytest

@pytest.fixture
def database_utenti():
    """Fornisce un dizionario simulato di utenti."""
    return {
        "mario": {"eta": 30, "ruolo": "admin"},
        "luigi": {"eta": 25, "ruolo": "utente"},
        "peach": {"eta": 28, "ruolo": "moderatore"},
    }

def test_conteggio_utenti(database_utenti):
    assert len(database_utenti) == 3

def test_ruolo_admin(database_utenti):
    assert database_utenti["mario"]["ruolo"] == "admin"
```

Il nome del parametro della funzione di test deve corrispondere esattamente al nome della fixture. pytest risolve automaticamente le dipendenze tramite dependency injection.

#### Scope delle Fixtures

Lo scope determina la frequenza con cui una fixture viene creata e distrutta:

```python
@pytest.fixture(scope="function")  # Default: ricreata per ogni test
def connessione_leggera():
    return crea_connessione()

@pytest.fixture(scope="class")  # Una per classe di test
def client_api():
    return APIClient()

@pytest.fixture(scope="module")  # Una per modulo (file .py)
def configurazione():
    return carica_config("test.toml")

@pytest.fixture(scope="session")  # Una per l'intera sessione di test
def connessione_database():
    conn = crea_connessione_db()
    yield conn
    conn.close()
```

- **function** — la fixture viene eseguita prima di ogni funzione di test e distrutta dopo. E il comportamento predefinito.
- **class** — la fixture viene condivisa tra tutti i metodi di una classe di test.
- **module** — la fixture viene condivisa tra tutti i test di un file.
- **session** — la fixture viene creata una sola volta per l'intera sessione di test.

#### Yield Fixtures (Setup/Teardown)

Le yield fixtures permettono di separare chiaramente la fase di setup da quella di teardown:

```python
@pytest.fixture
def file_temporaneo():
    # Setup: crea il file
    percorso = Path("/tmp/test_data.txt")
    percorso.write_text("dati di test")

    yield percorso  # Valore fornito al test

    # Teardown: pulisci dopo il test
    percorso.unlink(missing_ok=True)

@pytest.fixture
def transazione_db(connessione_database):
    # Setup: inizia una transazione
    trans = connessione_database.begin()

    yield connessione_database

    # Teardown: rollback per isolamento
    trans.rollback()
```

Il codice dopo `yield` viene eseguito sempre, anche se il test fallisce, garantendo una pulizia affidabile delle risorse.

#### conftest.py

Il file `conftest.py` e un file speciale riconosciuto automaticamente da pytest. Le fixtures definite in `conftest.py` sono disponibili per tutti i test nella stessa directory e nelle sottodirectory, senza bisogno di import espliciti.

```
tests/
    conftest.py          # Fixtures globali per tutti i test
    test_auth.py
    api/
        conftest.py      # Fixtures specifiche per i test API
        test_endpoints.py
    database/
        conftest.py      # Fixtures specifiche per i test database
        test_modelli.py
```

```python
# tests/conftest.py
import pytest

@pytest.fixture(scope="session")
def app():
    """Crea un'istanza dell'applicazione per i test."""
    from mia_app import crea_app
    app = crea_app(config="testing")
    return app

@pytest.fixture
def client(app):
    """Crea un test client HTTP."""
    return app.test_client()
```

#### Fixtures Built-in

pytest fornisce diverse fixtures integrate estremamente utili:

```python
def test_output_console(capsys):
    """capsys cattura stdout e stderr."""
    print("Elaborazione completata")
    catturato = capsys.readouterr()
    assert "completata" in catturato.out

def test_file_temporaneo(tmp_path):
    """tmp_path fornisce una directory temporanea unica per ogni test."""
    file_dati = tmp_path / "dati.json"
    file_dati.write_text('{"chiave": "valore"}')
    assert file_dati.exists()
    contenuto = file_dati.read_text()
    assert '"chiave"' in contenuto

def test_variabile_ambiente(monkeypatch):
    """monkeypatch modifica temporaneamente attributi, dizionari, variabili d'ambiente."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///test.db")
    monkeypatch.setattr("mio_modulo.CONFIGURAZIONE", {"debug": True})
    monkeypatch.delenv("API_KEY", raising=False)

    import os
    assert os.environ["DATABASE_URL"] == "sqlite:///test.db"

def test_con_request(request):
    """request fornisce informazioni sul test corrente."""
    nome_test = request.node.name
    print(f"Esecuzione di: {nome_test}")
```

#### Fixture Factories

Quando serve creare oggetti con parametri variabili, le fixture factory sono la soluzione:

```python
@pytest.fixture
def crea_utente():
    """Factory che crea utenti con parametri personalizzabili."""
    utenti_creati = []

    def _crea_utente(nome="Test", email=None, ruolo="utente"):
        email = email or f"{nome.lower()}@test.it"
        utente = Utente(nome=nome, email=email, ruolo=ruolo)
        utenti_creati.append(utente)
        return utente

    yield _crea_utente

    # Pulizia: rimuovi tutti gli utenti creati
    for utente in utenti_creati:
        utente.elimina()

def test_utente_admin(crea_utente):
    admin = crea_utente(nome="Admin", ruolo="admin")
    assert admin.ruolo == "admin"

def test_utenti_multipli(crea_utente):
    u1 = crea_utente(nome="Primo")
    u2 = crea_utente(nome="Secondo")
    assert u1.email != u2.email
```

#### Fixtures Parametrizzate

```python
@pytest.fixture(params=["sqlite", "postgresql", "mysql"])
def database(request):
    """Esegue i test con diversi backend di database."""
    db = crea_database(tipo=request.param)
    yield db
    db.disconnetti()

def test_inserimento(database):
    # Questo test viene eseguito tre volte, una per ciascun database
    database.inserisci({"id": 1, "nome": "Test"})
    risultato = database.cerca(id=1)
    assert risultato["nome"] == "Test"
```

#### Autouse Fixtures

Le fixtures con `autouse=True` vengono applicate automaticamente a tutti i test nel loro scope, senza bisogno di richiederle esplicitamente come parametro:

```python
import pytest
import logging

@pytest.fixture(autouse=True)
def pulisci_cache():
    """Applicata automaticamente a OGNI test in questo modulo."""
    yield
    # Teardown: pulisci la cache dopo ogni test
    from mia_app.cache import cache
    cache.clear()

@pytest.fixture(autouse=True, scope="session")
def configura_logging():
    """Configura il logging una volta per l'intera sessione di test."""
    logging.basicConfig(level=logging.WARNING)
    yield

@pytest.fixture(autouse=True)
def isola_database(db_session):
    """Ogni test opera in una transazione isolata con rollback."""
    db_session.begin_nested()
    yield
    db_session.rollback()
```

Linee guida per `autouse`:
- Usare per **setup/teardown trasversale** che riguarda tutti i test (pulizia cache, isolamento DB, configurazione logging)
- **Non abusare**: se una fixture autouse e rilevante solo per alcuni test, usare un marker + `request.config` o posizionarla in un conftest.py di sotto-directory
- Mai usare `autouse` per fornire dati di test — rende le dipendenze implicite e il codice difficile da seguire

### Fixture Avanzate: Pattern di Composizione

#### Composizione e Catene di Fixture

Le fixture di pytest supportano naturalmente la composizione: una fixture puo dipendere da altre fixture, creando catene di dipendenze che pytest risolve automaticamente tramite il suo meccanismo di dependency injection. Questo permette di costruire setup complessi partendo da componenti semplici e riutilizzabili.

```python
@pytest.fixture(scope="session")
def engine():
    """Crea il motore del database una volta per sessione."""
    from sqlalchemy import create_engine
    eng = create_engine("sqlite:///:memory:")
    yield eng
    eng.dispose()

@pytest.fixture(scope="session")
def tabelle(engine):
    """Crea le tabelle del database. Dipende da engine."""
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)

@pytest.fixture
def sessione(engine, tabelle):
    """Fornisce una sessione con transazione isolata. Dipende da engine e tabelle."""
    from sqlalchemy.orm import Session
    conn = engine.connect()
    trans = conn.begin()
    session = Session(bind=conn)
    yield session
    session.close()
    trans.rollback()
    conn.close()
```

La catena `engine → tabelle → sessione` viene risolta automaticamente. Ogni fixture viene creata una sola volta per il suo scope e riutilizzata per tutte le dipendenze downstream.

#### addfinalizer vs yield

Oltre al pattern `yield`, pytest offre `request.addfinalizer()` per registrare funzioni di teardown. La differenza principale e che `addfinalizer` permette di registrare piu funzioni di cleanup, utile quando il setup e condizionale o iterativo:

```python
@pytest.fixture
def risorse_multiple(request):
    """Crea risorse con cleanup condizionale tramite addfinalizer."""
    risorse = []

    def crea_risorsa(tipo):
        risorsa = Risorsa(tipo=tipo)
        risorsa.inizializza()
        risorse.append(risorsa)
        # Registra il cleanup per ogni risorsa creata
        request.addfinalizer(risorsa.chiudi)
        return risorsa

    return crea_risorsa

def test_risorse_diverse(risorse_multiple):
    db = risorse_multiple("database")
    cache = risorse_multiple("cache")
    # Entrambe le risorse verranno chiuse al termine del test,
    # in ordine inverso di registrazione (LIFO)
    assert db.stato == "attivo"
    assert cache.stato == "attivo"
```

Il vantaggio di `addfinalizer` rispetto a `yield` e che il finalizer viene eseguito anche se il setup fallisce dopo la registrazione. Con `yield`, se il codice prima di `yield` solleva un'eccezione, il teardown non viene eseguito.

#### Selezione Dinamica di Fixture

In scenari avanzati, puo essere necessario selezionare una fixture in modo dinamico basandosi su condizioni runtime. L'hook `pytest_generate_tests` permette di generare parametri per i test a livello programmatico:

```python
# conftest.py
def pytest_generate_tests(metafunc):
    """Genera parametri per fixture in base a variabili d'ambiente."""
    if "backend_db" in metafunc.fixturenames:
        import os
        backends = os.environ.get("TEST_DB_BACKENDS", "sqlite").split(",")
        metafunc.parametrize("backend_db", backends, indirect=True)

@pytest.fixture
def backend_db(request):
    """Fixture che crea connessioni a database diversi dinamicamente."""
    tipo = request.param
    if tipo == "sqlite":
        conn = crea_connessione_sqlite()
    elif tipo == "postgres":
        conn = crea_connessione_postgres()
    elif tipo == "mysql":
        conn = crea_connessione_mysql()
    else:
        pytest.skip(f"Backend {tipo} non supportato")
    yield conn
    conn.close()
```

#### Lazy Fixtures e Valutazione Differita

In alcuni casi, le fixture devono essere valutate solo quando effettivamente necessarie. Il plugin `pytest-lazy-fixtures` (successore di `pytest-lazy-fixture`) supporta la valutazione differita:

```python
# pip install pytest-lazy-fixtures
from pytest_lazy_fixtures import lf

@pytest.mark.parametrize("utente, atteso", [
    (lf("utente_admin"), True),      # La fixture utente_admin viene valutata solo qui
    (lf("utente_base"), False),       # La fixture utente_base viene valutata solo qui
    (lf("utente_sospeso"), False),
])
def test_permesso_cancellazione(utente, atteso):
    assert utente.puo_cancellare() == atteso
```

Senza lazy fixtures, non sarebbe possibile usare i valori di fixture direttamente nei parametri di `parametrize`, poiche le fixture non sono ancora state risolte al momento della raccolta dei test.

#### Fixture con Contesto Personalizzato

Le fixture possono utilizzare context manager personalizzati per gestire risorse complesse con garanzia di cleanup:

```python
from contextlib import contextmanager

@contextmanager
def server_temporaneo(porta):
    """Context manager che avvia e ferma un server HTTP di test."""
    import http.server
    import threading
    handler = http.server.SimpleHTTPRequestHandler
    server = http.server.HTTPServer(("localhost", porta), handler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    yield f"http://localhost:{porta}"
    server.shutdown()

@pytest.fixture
def server_test():
    """Fixture che usa un context manager per il lifecycle del server."""
    with server_temporaneo(porta=9876) as url:
        yield url
    # Il server viene fermato automaticamente all'uscita dal context manager

def test_richiesta_al_server(server_test):
    import urllib.request
    risposta = urllib.request.urlopen(f"{server_test}/index.html")
    assert risposta.status == 200
```

---

## conftest Deep Dive

Il file `conftest.py` e il meccanismo di pytest per la condivisione di fixtures, hook e configurazione tra test. La sua semantica di scoping lo rende uno strumento potente ma che richiede comprensione.

### Gerarchia e Scoping

```
progetto/
├── conftest.py              # [A] Fixtures disponibili per TUTTI i test
├── tests/
│   ├── conftest.py          # [B] Fixtures per tutti i test in tests/
│   ├── test_utils.py        # Vede [A] + [B]
│   ├── unit/
│   │   ├── conftest.py      # [C] Fixtures solo per test in unit/
│   │   ├── test_calcoli.py  # Vede [A] + [B] + [C]
│   │   └── test_validazione.py
│   ├── integration/
│   │   ├── conftest.py      # [D] Fixtures solo per test in integration/
│   │   ├── test_api.py      # Vede [A] + [B] + [D]
│   │   └── test_database.py
│   └── e2e/
│       ├── conftest.py      # [E] Fixtures solo per test in e2e/
│       └── test_flusso.py   # Vede [A] + [B] + [E]
```

La regola e semplice: un test vede le fixtures definite nel proprio conftest.py e in tutti i conftest.py delle directory antenate, fino alla root.

### Pattern Avanzati in conftest.py

```python
# tests/conftest.py — fixtures globali per tutti i test

import pytest
from pathlib import Path

# --- Fixtures per l'applicazione ---
@pytest.fixture(scope="session")
def app():
    """Crea l'applicazione una volta per l'intera sessione."""
    from mia_app import crea_app
    app = crea_app(config="testing")
    yield app

# --- Fixture condizionale basata su marker ---
@pytest.fixture(autouse=True)
def salta_se_lento(request):
    """Salta i test marcati @pytest.mark.slow se --runslow non e specificato."""
    if request.node.get_closest_marker("slow"):
        if not request.config.getoption("--runslow", default=False):
            pytest.skip("Test lento: usa --runslow per eseguirlo")

# --- Registrazione opzioni CLI personalizzate ---
def pytest_addoption(parser):
    parser.addoption(
        "--runslow",
        action="store_true",
        default=False,
        help="Esegui i test marcati come slow",
    )
    parser.addoption(
        "--db-url",
        action="store",
        default="sqlite:///:memory:",
        help="URL del database per i test di integrazione",
    )

# --- Hook per modificare la raccolta dei test ---
def pytest_collection_modifyitems(config, items):
    """Aggiunge automaticamente il marker 'slow' ai test di integrazione."""
    for item in items:
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.slow)

# --- Fixtures per dati di test da file ---
@pytest.fixture(scope="session")
def fixtures_dir():
    """Directory contenente i file di fixture."""
    return Path(__file__).parent / "fixtures"

@pytest.fixture
def dati_esempio(fixtures_dir):
    """Carica dati di esempio da un file JSON."""
    import json
    file_dati = fixtures_dir / "dati_esempio.json"
    return json.loads(file_dati.read_text())
```

```python
# tests/integration/conftest.py — fixtures specifiche per integrazione

import pytest

@pytest.fixture(scope="session")
def db_engine(request):
    """Crea il database engine per i test di integrazione."""
    from sqlalchemy import create_engine
    url = request.config.getoption("--db-url")
    engine = create_engine(url)
    yield engine
    engine.dispose()

@pytest.fixture(scope="function")
def db_session(db_engine):
    """Fornisce una sessione DB con rollback automatico."""
    from sqlalchemy.orm import Session
    with Session(db_engine) as session:
        session.begin()
        yield session
        session.rollback()
```

### Overriding di Fixtures

Una fixture definita in un conftest.py di sotto-directory puo **sovrascrivere** una fixture con lo stesso nome definita in un conftest.py padre:

```python
# tests/conftest.py
@pytest.fixture
def client(app):
    return app.test_client()

# tests/integration/conftest.py
@pytest.fixture
def client(app):
    """Override: client con autenticazione per i test di integrazione."""
    client = app.test_client()
    client.headers["Authorization"] = "Bearer test-token"
    return client
```

---

### Parametrize

Il decoratore `@pytest.mark.parametrize` permette di eseguire lo stesso test con combinazioni diverse di input e output attesi, evitando la duplicazione di codice.

#### Parametro Singolo e Multiplo

```python
# Parametro singolo
@pytest.mark.parametrize("input_val", [1, 2, 3, 4, 5])
def test_numero_positivo(input_val):
    assert input_val > 0

# Parametri multipli
@pytest.mark.parametrize("a, b, atteso", [
    (1, 2, 3),
    (0, 0, 0),
    (-1, 1, 0),
    (100, 200, 300),
    (1.5, 2.5, 4.0),
])
def test_addizione(a, b, atteso):
    assert a + b == atteso

# Con oggetti complessi
@pytest.mark.parametrize("input_dict, chiave, atteso", [
    ({"a": 1, "b": 2}, "a", 1),
    ({"x": "ciao"}, "x", "ciao"),
    ({}, "chiave", None),
])
def test_accesso_dizionario(input_dict, chiave, atteso):
    assert input_dict.get(chiave) == atteso
```

#### Parametrizzazione Indiretta

La parametrizzazione indiretta passa i valori attraverso una fixture prima di fornirli al test:

```python
@pytest.fixture
def connessione_db(request):
    """Crea connessioni a database diversi in base al parametro."""
    tipo_db = request.param
    conn = crea_connessione(tipo_db)
    yield conn
    conn.close()

@pytest.mark.parametrize("connessione_db", ["sqlite", "postgres"], indirect=True)
def test_query(connessione_db):
    risultato = connessione_db.esegui("SELECT 1")
    assert risultato is not None
```

#### ID per Leggibilita

Gli ID rendono l'output dei test piu comprensibile:

```python
@pytest.mark.parametrize("email, valido", [
    ("utente@dominio.it", True),
    ("invalido", False),
    ("@dominio.it", False),
    ("utente@", False),
    ("utente@dominio.co.uk", True),
], ids=[
    "email_standard",
    "senza_chiocciola",
    "senza_nome_utente",
    "senza_dominio",
    "dominio_secondo_livello",
])
def test_validazione_email(email, valido):
    assert valida_email(email) == valido
```

Con gli ID, l'output diventa: `test_validazione_email[email_standard] PASSED` invece di `test_validazione_email[utente@dominio.it-True] PASSED`.

#### Combinazione di Parametrize

Quando si applicano piu decoratori `parametrize`, pytest genera il prodotto cartesiano di tutte le combinazioni:

```python
@pytest.mark.parametrize("x", [1, 2])
@pytest.mark.parametrize("y", [10, 20, 30])
def test_moltiplicazione(x, y):
    risultato = x * y
    assert risultato == x * y
# Genera 6 test: (1,10), (1,20), (1,30), (2,10), (2,20), (2,30)
```

#### Parametrize con Marker Condizionali

E possibile associare marker a singoli parametri all'interno di `parametrize`, permettendo di marcare specifiche combinazioni come `xfail`, `skip` o con marker personalizzati:

```python
@pytest.mark.parametrize("input_val, atteso", [
    (10, 20),
    (0, 0),
    pytest.param(-1, -2, marks=pytest.mark.xfail(reason="Bug #567: negativi non gestiti")),
    pytest.param(None, 0, marks=pytest.mark.skip(reason="Supporto None non ancora implementato")),
    pytest.param(1_000_000, 2_000_000, marks=pytest.mark.slow),
])
def test_raddoppia(input_val, atteso):
    assert raddoppia(input_val) == atteso
```

Questa tecnica e particolarmente utile per documentare bug noti o funzionalita in sviluppo direttamente nella matrice dei test, senza separare i casi in funzioni diverse.

#### Generazione Dinamica con pytest_generate_tests

L'hook `pytest_generate_tests` offre un controllo programmatico completo sulla generazione dei parametri. A differenza di `parametrize`, che richiede valori statici definiti nel decoratore, `pytest_generate_tests` puo calcolare i parametri a runtime:

```python
# conftest.py
import json
from pathlib import Path

def pytest_generate_tests(metafunc):
    """Genera test cases da file JSON esterni."""
    if "caso_test" in metafunc.fixturenames:
        file_casi = Path(__file__).parent / "fixtures" / "casi_test.json"
        if file_casi.exists():
            casi = json.loads(file_casi.read_text())
            ids = [c["id"] for c in casi]
            metafunc.parametrize("caso_test", casi, ids=ids)

def test_elaborazione(caso_test):
    risultato = elabora(caso_test["input"])
    assert risultato == caso_test["output_atteso"]
```

Casi d'uso tipici di `pytest_generate_tests`:
- Caricare casi di test da file esterni (JSON, CSV, YAML)
- Generare parametri in base a variabili d'ambiente o configurazione
- Creare combinazioni condizionali che non possono essere espresse con il prodotto cartesiano di piu `parametrize`
- Filtrare parametri in base alla piattaforma o alla versione Python

#### Parametrize con Fixture Indirette Multiple

La parametrizzazione indiretta puo essere applicata a piu fixture contemporaneamente, utile per testare combinazioni di servizi:

```python
@pytest.fixture
def database(request):
    tipo = request.param
    db = crea_database(tipo)
    yield db
    db.chiudi()

@pytest.fixture
def cache(request):
    tipo = request.param
    c = crea_cache(tipo)
    yield c
    c.svuota()

@pytest.mark.parametrize(
    "database, cache",
    [
        ("sqlite", "memory"),
        ("postgres", "redis"),
        ("sqlite", "redis"),
    ],
    indirect=True,
)
def test_servizio_completo(database, cache):
    servizio = Servizio(db=database, cache=cache)
    servizio.salva("chiave", "valore")
    assert servizio.recupera("chiave") == "valore"
```

### Markers

I marker sono annotazioni che aggiungono metadati ai test, permettendo di controllarli in modo granulare.

#### Skip e Skipif

```python
import sys
import pytest

@pytest.mark.skip(reason="Funzionalita non ancora implementata")
def test_funzione_futura():
    pass

@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Non supportato su Windows"
)
def test_permessi_unix():
    import os
    assert os.getuid() >= 0

@pytest.mark.skipif(
    sys.version_info < (3, 11),
    reason="Richiede Python 3.11+ per ExceptionGroup"
)
def test_exception_group():
    pass
```

Si puo anche saltare un test dinamicamente all'interno del corpo:

```python
def test_connessione_esterna():
    if not rete_disponibile():
        pytest.skip("Rete non disponibile")
    risposta = richiedi_api_esterna()
    assert risposta.status == 200
```

#### Xfail

`xfail` marca un test che ci si aspetta fallisca. E utile per documentare bug noti o funzionalita non ancora implementate senza che il test blocchi la suite:

```python
@pytest.mark.xfail(reason="Bug #1234 — divisione per zero non gestita")
def test_divisione_zero():
    assert dividi(10, 0) == float("inf")

@pytest.mark.xfail(strict=True)
def test_strettamente_atteso_fallire():
    # Se questo test PASSA, viene segnalato come XPASS (errore)
    assert funzione_rotta() == "risultato"
```

#### Marker Personalizzati

```python
# Definisci marker personalizzati
@pytest.mark.slow
def test_elaborazione_pesante():
    """Test che richiede molto tempo."""
    risultato = elabora_dataset_grande()
    assert risultato.completato

@pytest.mark.integrazione
def test_connessione_database():
    """Test che richiede un database attivo."""
    pass
```

Per evitare warning, registra i marker nella configurazione:

```toml
# pyproject.toml
[tool.pytest.ini_options]
markers = [
    "slow: test che richiedono molto tempo",
    "integrazione: test che richiedono servizi esterni",
    "notturno: test da eseguire solo durante la build notturna",
]
```

```bash
# Esegui solo i test lenti
pytest -m slow

# Escludi i test lenti
pytest -m "not slow"

# Combinazioni logiche
pytest -m "integrazione and not slow"
```

### Plugin Essenziali

L'ecosistema di plugin di pytest e uno dei suoi punti di forza principali. Ecco i plugin fondamentali per un setup professionale.

#### pytest-cov

Integra la misurazione della coverage direttamente nell'esecuzione dei test:

```bash
pip install pytest-cov

# Report in terminale
pytest --cov=src tests/

# Report HTML interattivo
pytest --cov=src --cov-report=html tests/

# Fallisci se la coverage e sotto la soglia
pytest --cov=src --cov-fail-under=80 tests/
```

#### pytest-xdist

Permette l'esecuzione parallela dei test su piu core della CPU:

```bash
pip install pytest-xdist

# Usa tutti i core disponibili
pytest -n auto

# Usa un numero specifico di worker
pytest -n 4

# Distribuisci i test per file
pytest -n auto --dist loadfile
```

#### pytest-mock

Fornisce la fixture `mocker` che semplifica l'uso di `unittest.mock`:

```python
def test_invio_email(mocker):
    mock_smtp = mocker.patch("mio_modulo.smtplib.SMTP")
    invia_notifica("utente@test.it", "Messaggio")
    mock_smtp.return_value.sendmail.assert_called_once()
```

#### pytest-asyncio

Supporto per il testing di codice asincrono:

```python
import pytest

@pytest.mark.asyncio
async def test_richiesta_asincrona():
    risultato = await recupera_dati_async("https://api.esempio.it/dati")
    assert risultato["status"] == "ok"

@pytest.mark.asyncio
async def test_operazioni_concorrenti():
    import asyncio
    risultati = await asyncio.gather(
        operazione_a(),
        operazione_b(),
        operazione_c(),
    )
    assert all(r.successo for r in risultati)
```

#### pytest-timeout

Impone limiti temporali ai test per evitare blocchi:

```bash
pip install pytest-timeout

# Timeout globale di 10 secondi per test
pytest --timeout=10
```

```python
@pytest.mark.timeout(5)
def test_operazione_veloce():
    """Deve completarsi entro 5 secondi."""
    risultato = calcola_velocemente()
    assert risultato is not None
```

#### pytest-html

Genera report HTML dettagliati e visivamente chiari:

```bash
pip install pytest-html

pytest --html=report.html --self-contained-html
```

---

## unittest

unittest e il framework di testing incluso nella libreria standard di Python, ispirato a JUnit di Java. Pur essendo meno moderno di pytest, rimane rilevante per la sua presenza garantita in ogni installazione Python e per la sua integrazione con molti strumenti legacy.

### Fondamenti

#### TestCase

Tutti i test in unittest ereditano dalla classe `TestCase`:

```python
import unittest

class TestCalcolatrice(unittest.TestCase):

    def test_addizione(self):
        self.assertEqual(2 + 3, 5)

    def test_sottrazione(self):
        self.assertEqual(10 - 4, 6)

    def test_divisione_per_zero(self):
        with self.assertRaises(ZeroDivisionError):
            1 / 0

if __name__ == "__main__":
    unittest.main()
```

#### setUp e tearDown

```python
class TestGestioneFile(unittest.TestCase):

    def setUp(self):
        """Eseguito PRIMA di ogni test."""
        self.percorso_temp = Path("/tmp/test_file.txt")
        self.percorso_temp.write_text("contenuto iniziale")

    def tearDown(self):
        """Eseguito DOPO ogni test."""
        self.percorso_temp.unlink(missing_ok=True)

    @classmethod
    def setUpClass(cls):
        """Eseguito una volta prima di tutti i test della classe."""
        cls.connessione = crea_connessione_db()

    @classmethod
    def tearDownClass(cls):
        """Eseguito una volta dopo tutti i test della classe."""
        cls.connessione.close()

    def test_lettura(self):
        contenuto = self.percorso_temp.read_text()
        self.assertEqual(contenuto, "contenuto iniziale")

    def test_scrittura(self):
        self.percorso_temp.write_text("nuovo contenuto")
        self.assertEqual(self.percorso_temp.read_text(), "nuovo contenuto")
```

#### Metodi Assert

unittest offre un ricco insieme di metodi di asserzione:

```python
class TestAsserzioni(unittest.TestCase):

    def test_uguaglianza(self):
        self.assertEqual(1 + 1, 2)
        self.assertNotEqual(1 + 1, 3)

    def test_verita(self):
        self.assertTrue(10 > 5)
        self.assertFalse(10 < 5)

    def test_identita(self):
        a = [1, 2, 3]
        b = a
        self.assertIs(a, b)
        self.assertIsNot(a, [1, 2, 3])

    def test_none(self):
        self.assertIsNone(None)
        self.assertIsNotNone("valore")

    def test_appartenenza(self):
        self.assertIn(3, [1, 2, 3, 4])
        self.assertNotIn(5, [1, 2, 3, 4])

    def test_tipo(self):
        self.assertIsInstance("ciao", str)
        self.assertNotIsInstance("ciao", int)

    def test_eccezioni(self):
        with self.assertRaises(ValueError):
            int("non_un_numero")

        with self.assertRaises(KeyError) as contesto:
            {"a": 1}["b"]
        self.assertEqual(str(contesto.exception), "'b'")

    def test_approssimazione(self):
        self.assertAlmostEqual(0.1 + 0.2, 0.3, places=10)

    def test_regex(self):
        self.assertRegex("Errore: file non trovato", r"Errore:.*")

    def test_conteggio_elementi(self):
        self.assertCountEqual([1, 2, 3], [3, 1, 2])  # Ordine irrilevante
```

#### Test Runner

```bash
# Esecuzione standard
python -m unittest tests/test_modulo.py

# Discovery automatica
python -m unittest discover -s tests -p "test_*.py"

# Verboso
python -m unittest -v tests/test_modulo.py
```

#### Quando Usare unittest vs pytest

**Scegli pytest quando:**
- Inizi un nuovo progetto
- Vuoi una sintassi piu concisa e leggibile
- Hai bisogno di fixtures avanzate e parametrizzazione
- Vuoi accedere a un ecosistema di plugin ricco

**Scegli unittest quando:**
- Lavori su un progetto che lo usa gia estensivamente
- Non puoi installare dipendenze esterne
- Il team ha familiarita con xUnit-style frameworks
- Ti serve la compatibilita con strumenti legacy

Nota importante: pytest puo eseguire test scritti in stile unittest senza modifiche. Questa compatibilita permette una migrazione graduale.

---

## Mocking

Il mocking e la tecnica che permette di sostituire componenti reali con oggetti simulati durante i test. E fondamentale per isolare l'unita sotto test dalle sue dipendenze esterne.

### unittest.mock

Il modulo `unittest.mock` della libreria standard fornisce tutti gli strumenti necessari per il mocking in Python.

#### Mock, MagicMock e AsyncMock

```python
from unittest.mock import Mock, MagicMock, AsyncMock

# Mock base — oggetto che accetta qualsiasi attributo e chiamata
mock = Mock()
mock.metodo(42)
mock.metodo.assert_called_with(42)

# MagicMock — Mock con implementazione dei magic methods
mock_lista = MagicMock()
mock_lista.__len__.return_value = 5
len(mock_lista)  # Restituisce 5
mock_lista.__getitem__.return_value = "elemento"
mock_lista[0]  # Restituisce "elemento"

# AsyncMock — per funzioni e metodi asincroni
mock_async = AsyncMock(return_value={"dati": [1, 2, 3]})
# In un contesto async:
# risultato = await mock_async()
```

#### patch() — Decoratore e Context Manager

`patch()` sostituisce temporaneamente un oggetto con un mock nel contesto dove viene utilizzato:

```python
from unittest.mock import patch

# Come decoratore
@patch("mio_modulo.requests.get")
def test_richiesta_api(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"risultato": "ok"}

    risposta = mio_modulo.chiama_api("/endpoint")
    assert risposta["risultato"] == "ok"
    mock_get.assert_called_once_with("https://api.esempio.it/endpoint")

# Come context manager
def test_richiesta_fallita():
    with patch("mio_modulo.requests.get") as mock_get:
        mock_get.return_value.status_code = 500
        with pytest.raises(ErroreAPI):
            mio_modulo.chiama_api("/endpoint")
```

Regola fondamentale: **si fa patch dove l'oggetto viene usato, non dove viene definito**. Se `mio_modulo.py` importa `requests`, il patch corretto e `"mio_modulo.requests"`, non `"requests"`.

#### patch.object e patch.dict

```python
# patch.object — patch di un attributo specifico di un oggetto
class ServizioEsterno:
    def invia(self, messaggio):
        # Logica reale di invio
        pass

def test_invio_messaggio():
    servizio = ServizioEsterno()
    with patch.object(servizio, "invia", return_value=True) as mock_invia:
        risultato = servizio.invia("test")
        assert risultato is True
        mock_invia.assert_called_once_with("test")

# patch.dict — modifica temporanea di un dizionario
import os

@patch.dict(os.environ, {"API_KEY": "chiave_test", "DEBUG": "1"})
def test_configurazione_da_ambiente():
    assert os.environ["API_KEY"] == "chiave_test"
    assert os.environ["DEBUG"] == "1"

# Con clear=True per svuotare prima il dizionario
@patch.dict(os.environ, {"SOLO_QUESTA": "variabile"}, clear=True)
def test_ambiente_pulito():
    assert "HOME" not in os.environ  # Tutte le variabili rimosse
    assert os.environ["SOLO_QUESTA"] == "variabile"
```

#### spec e spec_set

`spec` garantisce che il mock abbia la stessa interfaccia dell'oggetto reale, prevenendo errori come il mock di metodi inesistenti:

```python
class Database:
    def connetti(self): ...
    def query(self, sql): ...
    def disconnetti(self): ...

# Con spec, il mock permette solo attributi di Database
mock_db = Mock(spec=Database)
mock_db.query("SELECT 1")  # OK
mock_db.metodo_inesistente()  # AttributeError!

# spec_set e ancora piu restrittivo: impedisce anche l'assegnazione
mock_db_strict = Mock(spec_set=Database)
mock_db_strict.nuovo_attributo = "valore"  # AttributeError!
```

#### side_effect

`side_effect` permette comportamenti complessi nei mock:

```python
# Sollevare un'eccezione
mock = Mock()
mock.side_effect = ConnectionError("Connessione rifiutata")
# mock()  -> solleva ConnectionError

# Restituire valori diversi ad ogni chiamata
mock = Mock()
mock.side_effect = [10, 20, 30]
mock()  # 10
mock()  # 20
mock()  # 30

# Funzione personalizzata
def effetto_laterale(x):
    if x < 0:
        raise ValueError("Valore negativo")
    return x * 2

mock = Mock(side_effect=effetto_laterale)
mock(5)   # 10
mock(-1)  # ValueError
```

#### Ispezione delle Chiamate

```python
mock = Mock()
mock("primo", chiave="valore")
mock("secondo")

# Verifica chiamate specifiche
mock.assert_called_with("secondo")  # Ultima chiamata
mock.assert_any_call("primo", chiave="valore")  # Qualsiasi chiamata

# Conteggio chiamate
assert mock.call_count == 2

# Argomenti dell'ultima chiamata
args, kwargs = mock.call_args
assert args == ("secondo",)

# Lista completa di tutte le chiamate
from unittest.mock import call
assert mock.call_args_list == [
    call("primo", chiave="valore"),
    call("secondo"),
]

# Verifica chiamata singola
mock_singolo = Mock()
mock_singolo("unica")
mock_singolo.assert_called_once_with("unica")
```

### Strategie di Mocking

#### Mocking di API Esterne

```python
# Con la libreria 'responses'
import responses

@responses.activate
def test_chiamata_api():
    responses.add(
        responses.GET,
        "https://api.meteo.it/oggi",
        json={"temperatura": 22, "citta": "Roma"},
        status=200,
    )

    risultato = servizio_meteo.ottieni_temperatura("Roma")
    assert risultato == 22

# Con 'requests-mock' (plugin pytest)
def test_api_con_errore(requests_mock):
    requests_mock.get(
        "https://api.esempio.it/dati",
        status_code=503,
        json={"errore": "Servizio non disponibile"},
    )

    with pytest.raises(ErroreServizio):
        client.recupera_dati()
```

#### Mocking del Database

```python
# Uso di SQLite in-memory come sostituto del database di produzione
import sqlite3

@pytest.fixture
def db_in_memoria():
    conn = sqlite3.connect(":memory:")
    conn.execute("""
        CREATE TABLE utenti (
            id INTEGER PRIMARY KEY,
            nome TEXT NOT NULL,
            email TEXT UNIQUE
        )
    """)
    conn.execute(
        "INSERT INTO utenti (nome, email) VALUES (?, ?)",
        ("Mario", "mario@test.it")
    )
    conn.commit()
    yield conn
    conn.close()

def test_ricerca_utente(db_in_memoria):
    cursore = db_in_memoria.execute(
        "SELECT nome FROM utenti WHERE email = ?",
        ("mario@test.it",)
    )
    riga = cursore.fetchone()
    assert riga[0] == "Mario"
```

#### Mocking del File System

```python
def test_lettura_configurazione(tmp_path):
    # tmp_path crea una directory temporanea reale
    config_file = tmp_path / "config.json"
    config_file.write_text('{"debug": true, "porta": 8080}')

    config = carica_configurazione(str(config_file))
    assert config["debug"] is True
    assert config["porta"] == 8080

# Oppure con mock per evitare I/O reale
@patch("builtins.open", mock_open(read_data='{"chiave": "valore"}'))
def test_lettura_file():
    import json
    with open("qualsiasi_file.json") as f:
        dati = json.load(f)
    assert dati["chiave"] == "valore"
```

#### Mocking di datetime e time

```python
from unittest.mock import patch
from datetime import datetime

@patch("mio_modulo.datetime")
def test_scadenza(mock_datetime):
    # Fissiamo il tempo a una data specifica
    mock_datetime.now.return_value = datetime(2026, 6, 15, 10, 30)
    mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

    risultato = mio_modulo.verifica_scadenza("2026-06-14")
    assert risultato is True  # La data e passata

# Con la libreria freezegun (piu elegante)
from freezegun import freeze_time

@freeze_time("2026-03-27")
def test_data_corrente():
    assert datetime.now().day == 27
    assert datetime.now().month == 3
```

#### Quando NON Fare Mock (Over-Mocking)

L'over-mocking e un errore comune che rende i test fragili e poco significativi. Evita il mock quando:

- **Stai testando logica pura senza dipendenze esterne**: funzioni che trasformano dati non hanno bisogno di mock.
- **Il mock replica fedelmente il codice reale**: se il mock diventa complesso quanto l'implementazione, il test non verifica nulla di utile.
- **Il componente reale e veloce e deterministico**: non serve mockare un dizionario, una lista o una semplice classe di dati.
- **Stai mockando dettagli implementativi interni**: i test dovrebbero verificare il comportamento, non l'implementazione. Mockare ogni dettaglio interno rende il refactoring doloroso.

Regola pratica: se un test ha piu codice di mock che di asserzioni, probabilmente stai facendo over-mocking.

### Mocking Avanzato

#### create_autospec

`create_autospec` crea un mock che replica fedelmente la firma del metodo originale. A differenza di `spec`, `create_autospec` e ricorsivo: anche i metodi del mock avranno le firme corrette, e chiamare un metodo con argomenti sbagliati solleva `TypeError`:

```python
from unittest.mock import create_autospec

class ServizioEmail:
    def invia(self, destinatario: str, oggetto: str, corpo: str) -> bool:
        # Implementazione reale
        ...

    def invia_batch(self, destinatari: list[str], oggetto: str, corpo: str) -> int:
        ...

# create_autospec garantisce firma corretta ricorsivamente
mock_email = create_autospec(ServizioEmail)

mock_email.invia("utente@test.it", "Oggetto", "Corpo")  # OK
mock_email.invia("solo_destinatario")  # TypeError! Firma non rispettata
mock_email.metodo_inesistente()  # AttributeError! Non esiste nella classe reale
```

La differenza chiave rispetto a `Mock(spec=ServizioEmail)` e che `create_autospec` controlla anche il numero e il tipo degli argomenti, non solo l'esistenza del metodo.

#### PropertyMock

Per mockare proprieta (`@property`) di una classe, `Mock` standard non funziona perche le proprieta sono descriptor a livello di classe. `PropertyMock` risolve questo problema:

```python
from unittest.mock import PropertyMock, patch

class Configurazione:
    @property
    def ambiente(self) -> str:
        # Legge da un file o variabile d'ambiente
        return os.environ.get("AMBIENTE", "produzione")

    @property
    def debug(self) -> bool:
        return self.ambiente == "sviluppo"

def test_modalita_debug():
    with patch.object(
        Configurazione, "ambiente",
        new_callable=PropertyMock,
        return_value="sviluppo"
    ):
        config = Configurazione()
        assert config.ambiente == "sviluppo"
        assert config.debug is True
```

#### patch.multiple

`patch.multiple` permette di applicare piu patch contemporaneamente su un singolo target, riducendo l'annidamento di decoratori e context manager:

```python
from unittest.mock import patch, MagicMock, DEFAULT

@patch.multiple(
    "mio_modulo",
    servizio_email=DEFAULT,
    servizio_sms=DEFAULT,
    logger=DEFAULT,
)
def test_notifica_multipla(servizio_email, servizio_sms, logger):
    servizio_email.invia.return_value = True
    servizio_sms.invia.return_value = True

    notifica_utente("utente@test.it", "+39123456789", "Messaggio")

    servizio_email.invia.assert_called_once()
    servizio_sms.invia.assert_called_once()
    logger.info.assert_called()
```

Il valore `DEFAULT` indica a `patch.multiple` di creare automaticamente un `MagicMock` per ogni attributo specificato. E possibile fornire valori specifici per alcuni attributi e usare `DEFAULT` per gli altri.

#### Mocking di Context Manager

Per mockare oggetti usati come context manager (`with` statement), `MagicMock` implementa automaticamente `__enter__` e `__exit__`:

```python
def test_connessione_come_context_manager():
    mock_conn = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.__exit__.return_value = False

    with patch("mio_modulo.crea_connessione", return_value=mock_conn):
        from mio_modulo import esegui_query
        risultato = esegui_query("SELECT 1")
        # Verifica che la connessione sia stata usata come context manager
        mock_conn.__enter__.assert_called_once()
        mock_conn.__exit__.assert_called_once()
```

#### Mocking di Generatori e Iteratori

Per mockare funzioni che restituiscono generatori o iteratori, `side_effect` con un iterabile e l'approccio piu pulito:

```python
def test_lettura_a_blocchi():
    mock_file = MagicMock()
    # Simula un generatore che produce blocchi di dati
    mock_file.leggi_blocchi.return_value = iter([
        b"blocco_1_dati",
        b"blocco_2_dati",
        b"blocco_3_fine",
    ])

    with patch("mio_modulo.apri_file", return_value=mock_file):
        blocchi = list(mio_modulo.processa_file("grande_file.bin"))
        assert len(blocchi) == 3

# Per generatori asincroni
async def mock_stream_async():
    for evento in ["inizio", "dati", "fine"]:
        yield evento

@pytest.mark.asyncio
async def test_stream_eventi():
    with patch("mio_modulo.stream_eventi", side_effect=mock_stream_async):
        eventi = []
        async for evento in mio_modulo.stream_eventi():
            eventi.append(evento)
        assert eventi == ["inizio", "dati", "fine"]
```

#### sentinel

`unittest.mock.sentinel` fornisce oggetti unici e non ambigui per verificare che un valore specifico venga propagato correttamente attraverso il codice, senza rischio di collisione con valori reali:

```python
from unittest.mock import sentinel, Mock

def test_propagazione_valore():
    repository = Mock()
    repository.trova.return_value = sentinel.utente_trovato

    servizio = ServizioUtenti(repository=repository)
    risultato = servizio.cerca_utente(id=42)

    # Verifica che il valore restituito dal repository sia esattamente
    # lo stesso oggetto propagato dal servizio, senza trasformazioni
    assert risultato is sentinel.utente_trovato
```

`sentinel` e preferibile a stringhe o numeri come valori di ritorno dei mock quando si vuole verificare l'identita (usando `is`) piuttosto che l'uguaglianza (usando `==`).

---

## Testing Patterns

### Test Doubles

I test doubles sono oggetti che sostituiscono componenti reali durante i test. Ne esistono diversi tipi, ciascuno con uno scopo specifico:

**Dummy** — oggetto passato come parametro ma mai realmente utilizzato. Serve solo a soddisfare la firma di un metodo.

```python
def test_registrazione():
    logger_dummy = object()  # Non verra mai chiamato
    servizio = ServizioRegistrazione(logger=logger_dummy)
    servizio.registra("utente@test.it", "password123")
```

**Stub** — fornisce risposte predeterminate alle chiamate. Non verifica come viene usato, si limita a restituire valori fissi.

```python
class StubMeteo:
    def temperatura(self, citta):
        return 20  # Sempre 20 gradi, indipendentemente dalla citta

def test_consiglio_abbigliamento():
    meteo = StubMeteo()
    consiglio = consiglia_abbigliamento(meteo, "Milano")
    assert consiglio == "Giacca leggera"
```

**Mock** — oggetto che registra le chiamate ricevute e permette di verificare che le interazioni avvengano come previsto.

```python
def test_notifica_inviata():
    mock_notificatore = Mock()
    servizio = ServizioOrdini(notificatore=mock_notificatore)
    servizio.completa_ordine(ordine_id=42)
    mock_notificatore.invia.assert_called_once_with(
        destinatario="cliente@test.it",
        messaggio="Ordine 42 completato"
    )
```

**Spy** — avvolge l'oggetto reale, delegando le chiamate ma registrandole per la verifica successiva.

```python
from unittest.mock import patch

def test_con_spy():
    with patch.object(servizio_reale, "elabora", wraps=servizio_reale.elabora) as spy:
        servizio_reale.elabora(dati)
        spy.assert_called_once()
        # L'implementazione reale viene comunque eseguita
```

**Fake** — implementazione funzionante ma semplificata, non adatta alla produzione. Esempio classico: un database in-memory al posto di PostgreSQL.

```python
class FakeRepository:
    def __init__(self):
        self._dati = {}

    def salva(self, id, entita):
        self._dati[id] = entita

    def trova(self, id):
        return self._dati.get(id)
```

### Arrange-Act-Assert (AAA)

Il pattern AAA e lo standard de facto per la struttura dei test unitari. Divide ogni test in tre sezioni distinte:

```python
def test_applicazione_sconto_fedelta():
    # Arrange — prepara i dati e le condizioni iniziali
    cliente = Cliente(nome="Mario", punti_fedelta=1500)
    carrello = Carrello()
    carrello.aggiungi(Prodotto("Scarpe", prezzo=100.00))
    carrello.aggiungi(Prodotto("Maglietta", prezzo=30.00))
    calcolatore = CalcolatoreSconto()

    # Act — esegui l'operazione sotto test
    totale = calcolatore.calcola_totale(carrello, cliente)

    # Assert — verifica il risultato atteso
    assert totale == 117.00  # 10% di sconto per fedelta (>1000 punti)
```

La separazione chiara tra le tre fasi rende il test leggibile e immediatamente comprensibile. Ogni sezione risponde a una domanda precisa:
- **Arrange**: "Quali sono le precondizioni?"
- **Act**: "Cosa sto testando?"
- **Assert**: "Qual e il risultato atteso?"

### Given-When-Then (BDD)

Il pattern Given-When-Then e l'equivalente BDD del pattern AAA, con enfasi sul comportamento:

```python
def test_ritiro_contante_sufficiente():
    # Given — dato un conto con saldo di 1000 euro
    conto = ContoBancario(saldo=1000)

    # When — quando si ritira 200 euro
    conto.ritira(200)

    # Then — allora il saldo e 800 euro
    assert conto.saldo == 800
```

#### pytest-bdd

Il plugin `pytest-bdd` permette di scrivere test in formato Gherkin, collegando feature files a step implementations:

```gherkin
# features/login.feature
Feature: Login Utente
  Scenario: Login con credenziali valide
    Given un utente registrato con email "mario@test.it"
    And la password e "sicura123"
    When l'utente effettua il login
    Then il login ha successo
    And viene generato un token JWT
```

```python
# tests/test_login.py
from pytest_bdd import scenario, given, when, then

@scenario("../features/login.feature", "Login con credenziali valide")
def test_login_valido():
    pass

@given('un utente registrato con email "mario@test.it"')
def utente_registrato():
    return crea_utente(email="mario@test.it")

@when("l'utente effettua il login")
def effettua_login(utente_registrato):
    return login(utente_registrato.email, "sicura123")

@then("il login ha successo")
def login_successo(effettua_login):
    assert effettua_login.successo is True
```

### BDD Avanzato con pytest-bdd

#### Scenario Outline (Parametrizzazione Gherkin)

Lo Scenario Outline e l'equivalente Gherkin di `@pytest.mark.parametrize`. Permette di definire la logica una sola volta e eseguirla con combinazioni diverse di dati, specificati nella tabella `Examples`:

```gherkin
# features/conversione_valuta.feature
Feature: Conversione Valuta

  Scenario Outline: Converti tra valute
    Given un importo di <importo> <valuta_origine>
    When converto in <valuta_destinazione>
    Then il risultato e circa <atteso> <valuta_destinazione>

    Examples:
      | importo | valuta_origine | valuta_destinazione | atteso  |
      | 100     | EUR            | USD                 | 108.50  |
      | 100     | EUR            | GBP                 | 85.30   |
      | 50      | USD            | EUR                 | 46.08   |
      | 1000    | GBP            | EUR                 | 1172.41 |
```

```python
# tests/test_conversione.py
from pytest_bdd import scenarios, given, when, then, parsers

# Carica TUTTI gli scenari dal feature file
scenarios("../features/conversione_valuta.feature")

@given(parsers.cfparse('un importo di {importo:d} {valuta_origine}'))
def importo_iniziale(importo, valuta_origine):
    return {"importo": importo, "valuta": valuta_origine}

@when(parsers.cfparse('converto in {valuta_destinazione}'))
def converti(importo_iniziale, valuta_destinazione):
    risultato = converti_valuta(
        importo_iniziale["importo"],
        importo_iniziale["valuta"],
        valuta_destinazione,
    )
    return {"risultato": risultato, "valuta": valuta_destinazione}

@then(parsers.cfparse('il risultato e circa {atteso:f} {valuta_destinazione}'))
def verifica_risultato(converti, atteso):
    assert abs(converti["risultato"] - atteso) < 0.01
```

#### Parser di Step: cfparse vs re

pytest-bdd offre tre parser per estrarre valori dagli step:

- **string** (default) — matching letterale, nessuna estrazione
- **cfparse** — usa la sintassi `{nome:tipo}` con supporto per tipi come `d` (intero), `f` (float), `g` (generale)
- **re** — regex Python complete per pattern complessi

```python
from pytest_bdd import parsers

# cfparse: semplice e leggibile
@given(parsers.cfparse('un utente con {punti:d} punti fedelta'))
def utente_con_punti(punti):
    return Utente(punti_fedelta=punti)

# re: per pattern complessi
@given(parsers.re(r'un utente "(?P<nome>\w+)" con email "(?P<email>[^"]+)"'))
def utente_con_dettagli(nome, email):
    return Utente(nome=nome, email=email)
```

#### Background

La sezione `Background` in Gherkin definisce step comuni eseguiti prima di ogni scenario nel feature file, evitando la ripetizione:

```gherkin
Feature: Gestione Carrello

  Background:
    Given un catalogo con i seguenti prodotti:
      | nome      | prezzo | disponibile |
      | Laptop    | 999.99 | true        |
      | Mouse     | 29.99  | true        |
      | Tastiera  | 79.99  | false       |
    And un carrello vuoto

  Scenario: Aggiungi prodotto disponibile
    When aggiungo "Laptop" al carrello
    Then il carrello contiene 1 prodotto
    And il totale e 999.99

  Scenario: Tentativo di aggiungere prodotto non disponibile
    When provo ad aggiungere "Tastiera" al carrello
    Then ricevo un errore "Prodotto non disponibile"
    And il carrello e vuoto
```

#### Data Tables negli Step

Le data tables permettono di passare dati tabulari direttamente negli step, utili per setup complessi o verifiche con insiemi di dati:

```python
@given("un catalogo con i seguenti prodotti:")
def catalogo_prodotti(datatable):
    catalogo = Catalogo()
    for riga in datatable:
        catalogo.aggiungi(Prodotto(
            nome=riga["nome"],
            prezzo=float(riga["prezzo"]),
            disponibile=riga["disponibile"] == "true",
        ))
    return catalogo
```

#### Integrazione con Fixture pytest

Uno dei vantaggi principali di pytest-bdd rispetto ad altri framework BDD e la piena integrazione con le fixture di pytest. Gli step possono ricevere fixture per dependency injection, e le fixture definite in `conftest.py` sono disponibili automaticamente:

```python
# conftest.py
@pytest.fixture
def servizio_pagamento():
    return MockServizioPagamento()

# test_pagamento.py
@when("l'utente paga con carta di credito")
def paga_con_carta(servizio_pagamento, carrello):
    # servizio_pagamento viene iniettato automaticamente da pytest
    return servizio_pagamento.processa(carrello.totale)
```

#### Mapping Tag → Marker

I tag Gherkin (`@tag`) vengono automaticamente convertiti in marker pytest, permettendo di filtrare gli scenari BDD con la stessa sintassi dei test normali:

```gherkin
@critico @regressione
Scenario: Verifica pagamento doppio
  Given un ordine gia pagato
  When si tenta un secondo pagamento
  Then il pagamento viene rifiutato
```

```bash
# Esegui solo gli scenari critici
pytest -m critico

# Esegui i test di regressione escludendo quelli lenti
pytest -m "regressione and not slow"
```

### Testing delle Eccezioni

```python
def test_divisione_per_zero():
    with pytest.raises(ZeroDivisionError):
        1 / 0

def test_messaggio_eccezione():
    with pytest.raises(ValueError, match=r"non valido.*negativo"):
        valida_eta(-5)  # Dovrebbe sollevare "Valore non valido: negativo"

def test_eccezione_dettagliata():
    with pytest.raises(PermessoNegato) as exc_info:
        accedi_risorsa_protetta(utente_non_autorizzato)

    assert exc_info.value.codice == 403
    assert "non autorizzato" in str(exc_info.value)
```

### Testing del Logging

```python
import logging

def test_log_avvertimento(caplog):
    """caplog cattura i messaggi di log durante il test."""
    with caplog.at_level(logging.WARNING):
        elabora_dati_incompleti({"nome": "Test"})

    assert "campo 'email' mancante" in caplog.text
    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == "WARNING"

def test_log_multipli(caplog):
    with caplog.at_level(logging.DEBUG):
        esegui_pipeline(dati)

    messaggi_errore = [r for r in caplog.records if r.levelno >= logging.ERROR]
    assert len(messaggi_errore) == 0, "Nessun errore dovrebbe essere registrato"
```

---

## Coverage

La coverage misura la percentuale di codice sorgente effettivamente eseguita durante i test. E uno strumento diagnostico fondamentale per identificare aree del codice non testate.

### Configurazione di pytest-cov

```bash
pip install pytest-cov

# Report base in terminale
pytest --cov=src tests/

# Report combinato: terminale + HTML
pytest --cov=src --cov-report=term-missing --cov-report=html tests/

# Solo il report di sintesi
pytest --cov=src --cov-report=term:skip-covered tests/
```

### Report in Terminale e HTML

L'output in terminale mostra una tabella con la coverage per ogni file:

```
----------- coverage: platform linux, python 3.12 -----------
Name                    Stmts   Miss  Cover   Missing
-----------------------------------------------------
src/calcolatrice.py        45      3    93%   67-69
src/validazione.py         32      0   100%
src/database.py            78     15    81%   34-40, 55, 89-95
-----------------------------------------------------
TOTAL                     155     18    88%
```

Il report HTML (generato nella directory `htmlcov/`) permette di navigare il codice sorgente con le righe coperte evidenziate in verde e quelle non coperte in rosso.

### Branch Coverage

La line coverage verifica solo se una riga e stata eseguita, ma la branch coverage e piu rigorosa: verifica che ogni ramo di ogni decisione condizionale sia stato percorso.

```python
def classifica_eta(eta):
    if eta < 0:         # Branch 1: True / False
        raise ValueError("Eta negativa")
    elif eta < 18:      # Branch 2: True / False
        return "minore"
    else:               # Branch 3
        return "adulto"
```

Con la sola line coverage, due test (eta=10 e eta=25) darebbero il 100% delle righe, ma non verificherebbero il ramo dell'errore. La branch coverage evidenzia questa lacuna.

```bash
pytest --cov=src --cov-branch tests/
```

### Configurazione in pyproject.toml

```toml
# pyproject.toml
[tool.coverage.run]
source = ["src"]
branch = true
omit = [
    "*/migrations/*",
    "*/test_*",
    "*/__pycache__/*",
]

[tool.coverage.report]
fail_under = 85
show_missing = true
skip_covered = true
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if TYPE_CHECKING:",
    "if __name__ == .__main__.",
    "raise NotImplementedError",
    "@abstractmethod",
]

[tool.coverage.html]
directory = "htmlcov"
```

### Soglie Minime di Coverage

Impostare una soglia minima impedisce che la coverage degradi nel tempo:

```bash
# Fallisce se la coverage scende sotto l'85%
pytest --cov=src --cov-fail-under=85 tests/
```

E consigliabile integrare questa soglia nella pipeline CI/CD per bloccare le pull request che riducono la coverage.

### Analisi della Coverage: Interpretazione e Trabocchetti

La coverage e un indicatore necessario ma non sufficiente. Comprendere le sue sfumature evita falsi sensi di sicurezza.

#### Line Coverage vs Branch Coverage vs Path Coverage

- **Line Coverage**: la metrica piu semplice. Una riga e coperta se viene eseguita almeno una volta. Problema: non distingue tra i rami di un `if/else` se sono sulla stessa riga.

- **Branch Coverage**: verifica che ogni ramo di ogni punto di decisione sia stato attraversato. Con un `if/else`, servono almeno due test: uno per il ramo `True` e uno per il ramo `False`. E significativamente piu rigorosa della line coverage.

- **Path Coverage**: la metrica piu completa ma anche la piu costosa. Verifica ogni possibile percorso di esecuzione attraverso una funzione. Con `n` punti di decisione indipendenti, i percorsi possibili sono `2^n`. In pratica, la path coverage completa e raggiungibile solo per funzioni molto semplici.

```python
def elabora_ordine(ordine):
    if ordine.valido:              # Decisione 1
        if ordine.importo > 100:   # Decisione 2
            applica_sconto(ordine)
        if ordine.prioritario:     # Decisione 3
            spedisci_express(ordine)
        return "completato"
    return "rifiutato"

# Line coverage 100% con soli 2 test:
# - ordine valido, importo 200, prioritario
# - ordine non valido

# Branch coverage 100% richiede almeno 4 test:
# - valido + importo > 100
# - valido + importo <= 100
# - valido + prioritario
# - non valido

# Path coverage 100% richiede 5 percorsi:
# - non valido
# - valido, importo <= 100, non prioritario
# - valido, importo > 100, non prioritario
# - valido, importo <= 100, prioritario
# - valido, importo > 100, prioritario
```

#### Coverage Come Strumento Diagnostico, Non Come Obiettivo

Un errore comune e perseguire la coverage come obiettivo numerico fine a se stesso. Test scritti solo per raggiungere una soglia numerica, senza asserzioni significative, producono una coverage ingannevole:

```python
# Test che raggiunge coverage ma NON verifica nulla
def test_inutile():
    risultato = funzione_complessa(dati)
    assert True  # 100% coverage, 0% utilita

# Test che verifica realmente il comportamento
def test_significativo():
    risultato = funzione_complessa(dati)
    assert risultato.stato == "completato"
    assert risultato.errori == []
    assert risultato.tempo_esecuzione < 5.0
```

La regola e: la coverage rivela le aree **non testate**, ma non dice nulla sulla **qualita** dei test nelle aree coperte. Usa la coverage per trovare lacune, non per misurare la qualita.

### Cosa Escludere dalla Coverage

Non tutto il codice merita di essere coperto dai test. Escludi ragionevolmente:

- Codice di configurazione (`if __name__ == "__main__"`)
- Metodi `__repr__` e `__str__` puramente cosmetici
- Codice protetto da `TYPE_CHECKING` (usato solo per type hints)
- Metodi astratti (sono solo dichiarazioni di interfaccia)
- Blocchi di codice legacy in via di rimozione
- File di migrazione del database generati automaticamente

---

## Integration Testing

I test di integrazione verificano che componenti diversi del sistema funzionino correttamente insieme. Sono piu lenti e complessi degli unit test, ma catturano errori che emergono solo dall'interazione tra moduli.

### Testing di Operazioni Database

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture(scope="function")
def sessione_db():
    """Crea un database SQLite in-memory per ogni test."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    sessione = Session()

    yield sessione

    sessione.rollback()
    sessione.close()

def test_creazione_utente(sessione_db):
    utente = Utente(nome="Mario", email="mario@test.it")
    sessione_db.add(utente)
    sessione_db.commit()

    trovato = sessione_db.query(Utente).filter_by(email="mario@test.it").first()
    assert trovato is not None
    assert trovato.nome == "Mario"

def test_vincolo_unicita_email(sessione_db):
    u1 = Utente(nome="Mario", email="duplicato@test.it")
    u2 = Utente(nome="Luigi", email="duplicato@test.it")
    sessione_db.add(u1)
    sessione_db.commit()

    sessione_db.add(u2)
    with pytest.raises(IntegrityError):
        sessione_db.commit()
```

### Testing di Endpoint API

```python
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    from mia_app.main import app
    return TestClient(app)

def test_lista_utenti(client):
    risposta = client.get("/api/utenti")
    assert risposta.status_code == 200
    dati = risposta.json()
    assert isinstance(dati, list)

def test_creazione_utente_valido(client):
    payload = {"nome": "Mario", "email": "mario@test.it"}
    risposta = client.post("/api/utenti", json=payload)
    assert risposta.status_code == 201
    assert risposta.json()["nome"] == "Mario"

def test_creazione_utente_invalido(client):
    payload = {"nome": ""}  # Nome vuoto, email mancante
    risposta = client.post("/api/utenti", json=payload)
    assert risposta.status_code == 422  # Validation error

def test_autenticazione_richiesta(client):
    risposta = client.get("/api/admin/dashboard")
    assert risposta.status_code == 401
```

### Infrastruttura di Test con Docker

Per test di integrazione che richiedono servizi reali (database, cache, message broker), Docker e la soluzione ideale:

```python
# conftest.py con testcontainers
import pytest
from testcontainers.postgres import PostgresContainer

@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:16") as postgres:
        yield postgres

@pytest.fixture(scope="function")
def connessione_postgres(postgres_container):
    import psycopg2
    conn = psycopg2.connect(postgres_container.get_connection_url())
    yield conn
    conn.rollback()
    conn.close()
```

In alternativa, si puo usare `docker-compose` per orchestrare l'ambiente di test:

```yaml
# docker-compose.test.yml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: test_db
      POSTGRES_PASSWORD: test_password
    ports:
      - "5433:5432"

  redis:
    image: redis:7
    ports:
      - "6380:6379"
```

### Strategie di Isolamento

L'isolamento dei test e cruciale per evitare che un test influenzi il risultato di un altro:

- **Transazione con rollback**: ogni test opera all'interno di una transazione che viene annullata al termine. E il metodo piu veloce e affidabile.
- **Database separato per test**: crea un database dedicato per ogni sessione di test.
- **Fixture con pulizia esplicita**: cancella i dati inseriti nel teardown.
- **Factory per dati unici**: usa identificatori unici (UUID) per evitare collisioni tra test paralleli.

```python
import uuid

@pytest.fixture
def email_unica():
    """Genera un'email unica per ogni test, evitando conflitti."""
    return f"test-{uuid.uuid4().hex[:8]}@test.it"
```

---

## Property-Based Testing

Il testing tradizionale verifica il codice con esempi specifici scelti dallo sviluppatore. Il property-based testing adotta un approccio diverso: definisce proprieta che devono valere per qualsiasi input e lascia al framework la generazione automatica di casi di test.

### La Libreria Hypothesis

Hypothesis e la libreria di riferimento per il property-based testing in Python:

```bash
pip install hypothesis
```

```python
from hypothesis import given
from hypothesis import strategies as st

@given(st.integers(), st.integers())
def test_addizione_commutativa(a, b):
    """L'addizione e commutativa per qualsiasi coppia di interi."""
    assert a + b == b + a

@given(st.lists(st.integers()))
def test_ordinamento_preserva_lunghezza(lista):
    """Ordinare una lista non ne cambia la lunghezza."""
    ordinata = sorted(lista)
    assert len(ordinata) == len(lista)

@given(st.lists(st.integers(), min_size=1))
def test_ordinamento_primo_minore_uguale_ultimo(lista):
    """Il primo elemento della lista ordinata e il minimo."""
    ordinata = sorted(lista)
    assert ordinata[0] == min(lista)
    assert ordinata[-1] == max(lista)
```

### Strategies

Le strategies definiscono il tipo di dati che Hypothesis genera:

```python
from hypothesis import strategies as st

# Tipi base
st.integers()                        # Qualsiasi intero
st.integers(min_value=0, max_value=100)  # Intero nell'intervallo
st.floats(allow_nan=False)           # Float senza NaN
st.text(min_size=1, max_size=100)    # Stringhe non vuote
st.booleans()                        # True o False

# Collezioni
st.lists(st.integers(), min_size=0, max_size=50)
st.dictionaries(st.text(min_size=1), st.integers())
st.tuples(st.integers(), st.text())

# Composizione
st.one_of(st.integers(), st.text())  # Intero OPPURE stringa

# Dati strutturati
@st.composite
def strategia_utente(draw):
    nome = draw(st.text(min_size=2, max_size=50, alphabet=st.characters(
        whitelist_categories=("L",)
    )))
    eta = draw(st.integers(min_value=0, max_value=150))
    return {"nome": nome, "eta": eta}

@given(strategia_utente())
def test_validazione_utente(utente):
    risultato = valida_utente(utente)
    assert isinstance(risultato, bool)
```

### Individuazione Automatica di Edge Case

Hypothesis e particolarmente efficace nel trovare edge case che lo sviluppatore potrebbe non considerare:

```python
@given(st.text())
def test_codifica_decodifica(testo):
    """Codificare e decodificare deve restituire il testo originale."""
    codificato = codifica_base64(testo)
    decodificato = decodifica_base64(codificato)
    assert decodificato == testo
    # Hypothesis potrebbe scoprire problemi con:
    # - Stringhe vuote
    # - Caratteri Unicode esotici
    # - Stringhe molto lunghe
    # - Caratteri null
```

### Shrinking

Quando Hypothesis trova un input che fa fallire il test, applica automaticamente lo shrinking: riduce progressivamente l'input al caso minimo che ancora causa il fallimento. Questo rende il debugging molto piu semplice.

```python
@given(st.lists(st.integers()))
def test_somma_positiva(numeri):
    """Esempio: supponi un bug quando la lista contiene numeri negativi."""
    assert sum(numeri) >= 0
    # Hypothesis potrebbe trovare [1, -3, 2] come caso fallimentare
    # ma lo ridurra a [-1], il caso minimo che causa il fallimento
```

### Hypothesis Avanzato

#### Stateful Testing con RuleBasedStateMachine

Il testing stateful e il punto di forza piu avanzato di Hypothesis. Mentre `@given` testa singole operazioni in isolamento, `RuleBasedStateMachine` genera sequenze di operazioni per testare il comportamento di sistemi con stato nel tempo, scoprendo bug che emergono solo da interazioni specifiche tra operazioni successive:

```python
from hypothesis.stateful import RuleBasedStateMachine, rule, precondition, Bundle
from hypothesis import strategies as st

class TestCarrelloStateful(RuleBasedStateMachine):
    """Verifica che il carrello si comporti correttamente
    con qualsiasi sequenza di operazioni."""

    def __init__(self):
        super().__init__()
        self.carrello = Carrello()
        self.prodotti_attesi = []

    prodotti_aggiunti = Bundle("prodotti_aggiunti")

    @rule(target=prodotti_aggiunti, nome=st.text(min_size=1, max_size=20),
          prezzo=st.floats(min_value=0.01, max_value=9999.99))
    def aggiungi_prodotto(self, nome, prezzo):
        """Regola: aggiungi un prodotto al carrello."""
        self.carrello.aggiungi(nome, prezzo)
        self.prodotti_attesi.append({"nome": nome, "prezzo": prezzo})
        assert self.carrello.numero_prodotti == len(self.prodotti_attesi)
        return nome

    @rule(nome=prodotti_aggiunti)
    def rimuovi_prodotto(self, nome):
        """Regola: rimuovi un prodotto precedentemente aggiunto."""
        self.carrello.rimuovi(nome)
        self.prodotti_attesi = [p for p in self.prodotti_attesi if p["nome"] != nome]
        assert self.carrello.numero_prodotti == len(self.prodotti_attesi)

    @precondition(lambda self: len(self.prodotti_attesi) > 0)
    @rule()
    def verifica_totale(self):
        """Invariante: il totale deve sempre corrispondere alla somma dei prezzi."""
        totale_atteso = sum(p["prezzo"] for p in self.prodotti_attesi)
        assert abs(self.carrello.totale - totale_atteso) < 0.01

    @rule()
    def svuota(self):
        """Regola: svuota il carrello."""
        self.carrello.svuota()
        self.prodotti_attesi.clear()
        assert self.carrello.numero_prodotti == 0
        assert self.carrello.totale == 0.0

# Esegui il test stateful
TestCarrello = TestCarrelloStateful.TestCase
```

Hypothesis genera centinaia di sequenze di operazioni diverse (aggiungi, rimuovi, svuota, verifica) in ordini casuali, cercando sequenze che violano le invarianti.

#### @settings e Profili

Il decoratore `@settings` permette di configurare il comportamento di Hypothesis per singolo test, controllando il numero di esempi, il tempo massimo, la verbosita e altre opzioni:

```python
from hypothesis import given, settings, HealthCheck, Phase, Verbosity
from hypothesis import strategies as st

@settings(
    max_examples=500,               # Genera 500 casi di test (default: 100)
    deadline=5000,                   # Timeout di 5 secondi per caso (ms)
    suppress_health_check=[          # Disabilita specifici health check
        HealthCheck.too_slow,
        HealthCheck.filter_too_much,
    ],
    derandomize=True,                # Risultati riproducibili (disabilita randomizzazione)
)
@given(st.lists(st.integers(), min_size=1, max_size=10000))
def test_ordinamento_grande(lista):
    ordinata = sorted(lista)
    assert all(ordinata[i] <= ordinata[i+1] for i in range(len(ordinata)-1))
```

I profili permettono di definire configurazioni riutilizzabili per ambienti diversi:

```python
# conftest.py
from hypothesis import settings

# Profilo CI: piu esempi, piu tempo
settings.register_profile("ci", max_examples=1000, deadline=10000)

# Profilo sviluppo: meno esempi, piu veloce
settings.register_profile("dev", max_examples=50, deadline=2000)

# Profilo debug: massima verbosita
settings.register_profile("debug", max_examples=10, verbosity=Verbosity.verbose)

# Seleziona il profilo tramite variabile d'ambiente
import os
settings.load_profile(os.environ.get("HYPOTHESIS_PROFILE", "dev"))
```

```bash
# Usa il profilo CI nella pipeline
HYPOTHESIS_PROFILE=ci pytest tests/
```

#### @example per Casi Specifici

Il decoratore `@example` forza l'inclusione di casi specifici che devono sempre essere testati, indipendentemente dalla generazione casuale. E utile per regressioni e boundary cases noti:

```python
from hypothesis import given, example
from hypothesis import strategies as st

@given(st.text())
@example("")           # Stringa vuota — sempre testata
@example("  ")         # Solo spazi
@example("a" * 10000)  # Stringa molto lunga
@example("\x00\n\r")   # Caratteri di controllo
def test_normalizza_testo(testo):
    risultato = normalizza(testo)
    assert isinstance(risultato, str)
    # La normalizzazione non deve mai restituire None
    assert risultato is not None
```

#### assume() per Filtrare Input Non Validi

`assume()` permette di scartare input generati che non soddisfano le precondizioni del test, senza contarli come fallimenti:

```python
from hypothesis import given, assume
from hypothesis import strategies as st

@given(st.integers(), st.integers())
def test_divisione_sicura(numeratore, denominatore):
    assume(denominatore != 0)  # Scarta i casi con denominatore zero
    risultato = numeratore / denominatore
    assert risultato * denominatore == pytest.approx(numeratore)
```

Attenzione: se `assume()` filtra troppi valori (>50% dei generati), Hypothesis segnala un health check warning. In quel caso, e meglio restringere la strategia di generazione piuttosto che filtrare eccessivamente.

#### Database di Hypothesis

Hypothesis salva automaticamente gli esempi che causano fallimenti in un database locale (`.hypothesis/` nella directory del progetto). Quando il test viene rieseguito, Hypothesis tenta prima gli esempi falliti salvati. Questo garantisce che un bug, una volta trovato, non venga mai "dimenticato" anche se la generazione casuale non lo riprodurrebbe:

```python
# Per condividere il database tra sviluppatori, aggiungere .hypothesis/ al repository
# oppure configurare un database condiviso:
from hypothesis import settings
from hypothesis.database import DirectoryBasedExampleDatabase

settings.register_profile(
    "condiviso",
    database=DirectoryBasedExampleDatabase("/percorso/condiviso/.hypothesis"),
)
```

---

## Test Data: factory_boy e Faker

### factory_boy

`factory_boy` genera oggetti di test complessi con valori realistici, eliminando la necessita di costruire manualmente ogni oggetto nelle fixtures.

```python
# pip install factory-boy faker
import factory
from factory import Faker, SubFactory, LazyAttribute
from mia_app.modelli import Utente, Ordine, Indirizzo

class IndirizzoFactory(factory.Factory):
    class Meta:
        model = Indirizzo

    via = Faker("street_address", locale="it_IT")
    citta = Faker("city", locale="it_IT")
    cap = Faker("postcode", locale="it_IT")
    provincia = Faker("state_abbr", locale="it_IT")

class UtenteFactory(factory.Factory):
    class Meta:
        model = Utente

    nome = Faker("first_name", locale="it_IT")
    cognome = Faker("last_name", locale="it_IT")
    email = LazyAttribute(lambda o: f"{o.nome.lower()}.{o.cognome.lower()}@test.it")
    eta = Faker("random_int", min=18, max=80)
    indirizzo = SubFactory(IndirizzoFactory)
    attivo = True

class OrdineFactory(factory.Factory):
    class Meta:
        model = Ordine

    codice = factory.Sequence(lambda n: f"ORD-{n:06d}")
    utente = SubFactory(UtenteFactory)
    importo = Faker("pydecimal", left_digits=4, right_digits=2, positive=True)

# Uso nei test
def test_sconto_cliente_attivo():
    utente = UtenteFactory(attivo=True, eta=65)
    ordine = OrdineFactory(utente=utente, importo=100.00)
    assert calcola_sconto(ordine) == 10.0  # sconto senior

def test_batch_utenti():
    utenti = UtenteFactory.create_batch(50)
    assert len(utenti) == 50
    assert all(u.eta >= 18 for u in utenti)

# Traits per varianti comuni
class UtenteFactory(factory.Factory):
    class Meta:
        model = Utente

    nome = Faker("first_name", locale="it_IT")
    email = LazyAttribute(lambda o: f"{o.nome.lower()}@test.it")
    attivo = True
    ruolo = "utente"

    class Params:
        admin = factory.Trait(ruolo="admin", email="admin@test.it")
        inattivo = factory.Trait(attivo=False)

# Uso dei traits
admin = UtenteFactory(admin=True)
utente_disattivato = UtenteFactory(inattivo=True)
```

### Faker Standalone

`Faker` puo essere usato indipendentemente da factory_boy per generare dati di test realistici:

```python
from faker import Faker

fake = Faker("it_IT")

def test_con_dati_realistici():
    nome = fake.name()
    email = fake.email()
    cf = fake.ssn()  # Codice fiscale italiano
    iban = fake.iban()
    telefono = fake.phone_number()
    indirizzo = fake.address()

    assert "@" in email
    assert len(cf) == 16

# Seed per riproducibilita
Faker.seed(42)
fake_riproducibile = Faker("it_IT")
```

---

## Testcontainers Deep Dive

Testcontainers avvia container Docker come infrastruttura di test, garantendo isolamento e riproducibilita per database, cache, message broker e altri servizi.

```python
# pip install testcontainers
import pytest
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer
from testcontainers.mongodb import MongoDbContainer

# --- PostgreSQL ---
@pytest.fixture(scope="session")
def postgres():
    with PostgresContainer("postgres:16-alpine") as pg:
        yield pg

@pytest.fixture
def pg_conn(postgres):
    import psycopg2
    conn = psycopg2.connect(
        host=postgres.get_container_host_ip(),
        port=postgres.get_exposed_port(5432),
        user=postgres.username,
        password=postgres.password,
        dbname=postgres.dbname,
    )
    yield conn
    conn.rollback()
    conn.close()

def test_inserimento_postgres(pg_conn):
    cur = pg_conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS test (id SERIAL, nome TEXT)")
    cur.execute("INSERT INTO test (nome) VALUES (%s) RETURNING id", ("Mario",))
    id_inserito = cur.fetchone()[0]
    assert id_inserito > 0

# --- Redis ---
@pytest.fixture(scope="session")
def redis_container():
    with RedisContainer("redis:7-alpine") as redis:
        yield redis

@pytest.fixture
def redis_client(redis_container):
    import redis as redis_lib
    client = redis_lib.Redis(
        host=redis_container.get_container_host_ip(),
        port=redis_container.get_exposed_port(6379),
    )
    yield client
    client.flushdb()

def test_cache_redis(redis_client):
    redis_client.set("chiave", "valore")
    assert redis_client.get("chiave") == b"valore"
```

### Pattern Avanzati con Testcontainers

#### Orchestrazione Multi-Container

Scenari reali richiedono spesso piu servizi che interagiscono tra loro. Testcontainers permette di orchestrare piu container coordinando il loro ciclo di vita:

```python
import pytest
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

@pytest.fixture(scope="session")
def infrastruttura_test():
    """Avvia PostgreSQL e Redis insieme per i test di integrazione."""
    postgres = PostgresContainer("postgres:16-alpine")
    redis = RedisContainer("redis:7-alpine")

    postgres.start()
    redis.start()

    yield {
        "postgres_url": postgres.get_connection_url(),
        "redis_host": redis.get_container_host_ip(),
        "redis_port": redis.get_exposed_port(6379),
    }

    redis.stop()
    postgres.stop()

def test_cache_invalidation(infrastruttura_test):
    """Verifica che la cache Redis si invalidi quando il DB cambia."""
    import psycopg2
    import redis as redis_lib

    conn = psycopg2.connect(infrastruttura_test["postgres_url"])
    cache = redis_lib.Redis(
        host=infrastruttura_test["redis_host"],
        port=int(infrastruttura_test["redis_port"]),
    )

    # Inserisci dati nel DB e nella cache
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS prodotti (id SERIAL, nome TEXT, prezzo NUMERIC)")
    cur.execute("INSERT INTO prodotti (nome, prezzo) VALUES (%s, %s)", ("Laptop", 999.99))
    conn.commit()

    cache.set("prodotto:1", "Laptop:999.99")
    assert cache.get("prodotto:1") is not None

    # Aggiorna il DB e invalida la cache
    cur.execute("UPDATE prodotti SET prezzo = %s WHERE nome = %s", (899.99, "Laptop"))
    conn.commit()
    cache.delete("prodotto:1")

    assert cache.get("prodotto:1") is None
    cur.close()
    conn.close()
```

#### Container Personalizzati

Per servizi non supportati nativamente, e possibile creare container personalizzati partendo da `DockerContainer`:

```python
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs

class MinioContainer(DockerContainer):
    """Container personalizzato per MinIO (S3-compatible object storage)."""

    def __init__(self, image="minio/minio:latest"):
        super().__init__(image)
        self.with_exposed_ports(9000, 9001)
        self.with_env("MINIO_ROOT_USER", "minioadmin")
        self.with_env("MINIO_ROOT_PASSWORD", "minioadmin")
        self.with_command("server /data --console-address ':9001'")

    def start(self):
        super().start()
        wait_for_logs(self, "API:")
        return self

    def get_endpoint_url(self) -> str:
        host = self.get_container_host_ip()
        port = self.get_exposed_port(9000)
        return f"http://{host}:{port}"

@pytest.fixture(scope="session")
def minio():
    with MinioContainer() as container:
        yield container

def test_upload_oggetto(minio):
    import boto3
    s3 = boto3.client(
        "s3",
        endpoint_url=minio.get_endpoint_url(),
        aws_access_key_id="minioadmin",
        aws_secret_access_key="minioadmin",
    )
    s3.create_bucket(Bucket="test-bucket")
    s3.put_object(Bucket="test-bucket", Key="file.txt", Body=b"contenuto")

    risposta = s3.get_object(Bucket="test-bucket", Key="file.txt")
    assert risposta["Body"].read() == b"contenuto"
```

#### Riutilizzo dei Container

Per velocizzare l'esecuzione durante lo sviluppo locale, e possibile riutilizzare container tra sessioni di test successive con il flag `reuse`:

```python
@pytest.fixture(scope="session")
def postgres_riutilizzabile():
    container = PostgresContainer("postgres:16-alpine")
    container.with_kwargs(reuse=True)  # Riutilizza il container se esiste
    container.start()
    yield container
    # Non fermare il container — verra riutilizzato alla prossima esecuzione
```

Questa tecnica riduce drasticamente il tempo di avvio dei test di integrazione durante lo sviluppo iterativo, ma deve essere disabilitata nella pipeline CI dove l'isolamento e prioritario.

#### Integrazione factory_boy + Testcontainers + SQLAlchemy

Il pattern piu potente per i test di integrazione combina Testcontainers per l'infrastruttura, SQLAlchemy per l'ORM e factory_boy per la generazione dei dati:

```python
import pytest
import factory
from testcontainers.postgres import PostgresContainer
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

@pytest.fixture(scope="session")
def pg_engine():
    with PostgresContainer("postgres:16-alpine") as pg:
        engine = create_engine(pg.get_connection_url())
        Base.metadata.create_all(engine)
        yield engine

@pytest.fixture
def db_session(pg_engine):
    connection = pg_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

class UtenteFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Utente
        sqlalchemy_session = None  # Impostata dinamicamente
        sqlalchemy_session_persistence = "commit"

    nome = factory.Faker("first_name", locale="it_IT")
    email = factory.LazyAttribute(lambda o: f"{o.nome.lower()}@test.it")

@pytest.fixture(autouse=True)
def imposta_sessione_factory(db_session):
    """Collega factory_boy alla sessione di test corrente."""
    UtenteFactory._meta.sqlalchemy_session = db_session
    yield

def test_ricerca_utenti(db_session):
    UtenteFactory.create_batch(10)
    utenti = db_session.query(Utente).all()
    assert len(utenti) == 10
```

---

## Testing Asincrono con pytest-asyncio

```python
# pip install pytest-asyncio
import pytest
import asyncio
from unittest.mock import AsyncMock, patch

# Configurazione in pyproject.toml:
# [tool.pytest.ini_options]
# asyncio_mode = "auto"  # tutte le funzioni async sono test automaticamente

@pytest.mark.asyncio
async def test_operazione_asincrona():
    risultato = await recupera_dati_async("/api/utenti")
    assert isinstance(risultato, list)

@pytest.mark.asyncio
async def test_concorrenza():
    """Verifica che operazioni concorrenti non causino race condition."""
    contatore = {"valore": 0}

    async def incrementa():
        val = contatore["valore"]
        await asyncio.sleep(0.01)
        contatore["valore"] = val + 1

    tasks = [asyncio.create_task(incrementa()) for _ in range(10)]
    await asyncio.gather(*tasks)
    # Se c'e una race condition, il valore sara < 10

# Fixture asincrona
@pytest.fixture
async def client_async():
    from httpx import AsyncClient
    from mia_app import app
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
async def test_endpoint_async(client_async):
    risposta = await client_async.get("/api/stato")
    assert risposta.status_code == 200

# Mock asincrono
@pytest.mark.asyncio
async def test_con_mock_async():
    mock_servizio = AsyncMock(return_value={"stato": "ok"})
    risultato = await mock_servizio()
    assert risultato["stato"] == "ok"
    mock_servizio.assert_awaited_once()

# Timeout per test asincroni
@pytest.mark.asyncio
@pytest.mark.timeout(5)
async def test_non_deve_bloccarsi():
    await asyncio.sleep(0.1)
    assert True
```

### Testing Asincrono Avanzato

#### Configurazione Event Loop e Scope

A partire da pytest-asyncio 0.23+, la gestione dell'event loop e stata significativamente migliorata. La modalita `auto` marca automaticamente tutte le funzioni `async` come test asincroni, eliminando la necessita di `@pytest.mark.asyncio` su ogni test:

```toml
# pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"

# Scope dell'event loop: controlla la durata del loop
# "function" (default), "class", "module", "package", "session"
```

Per condividere un event loop tra test (utile per fixture session-scoped asincrone), configurare lo scope del loop:

```python
# conftest.py
import pytest

@pytest.fixture(scope="session")
def event_loop_policy():
    """Usa la policy di default per l'event loop di sessione."""
    import asyncio
    return asyncio.DefaultEventLoopPolicy()

# Alternativa con il marker per scope module
pytestmark = pytest.mark.asyncio(loop_scope="module")
```

#### Fixture Asincrone con Scope

Le fixture asincrone seguono le stesse regole di scope delle fixture sincrone, ma richiedono attenzione alla compatibilita con lo scope dell'event loop:

```python
@pytest.fixture(scope="session")
async def pool_connessioni():
    """Pool di connessioni condiviso per l'intera sessione."""
    import asyncpg
    pool = await asyncpg.create_pool(
        "postgresql://test:test@localhost:5432/test_db",
        min_size=2,
        max_size=10,
    )
    yield pool
    await pool.close()

@pytest.fixture
async def connessione(pool_connessioni):
    """Connessione singola con transazione isolata per ogni test."""
    async with pool_connessioni.acquire() as conn:
        trans = conn.transaction()
        await trans.start()
        yield conn
        await trans.rollback()

async def test_inserimento_async(connessione):
    await connessione.execute(
        "INSERT INTO utenti (nome) VALUES ($1)", "Mario"
    )
    riga = await connessione.fetchrow("SELECT nome FROM utenti WHERE nome = $1", "Mario")
    assert riga["nome"] == "Mario"
```

#### Testing di WebSocket

Il testing di connessioni WebSocket richiede gestione asincrona bidirezionale. Con framework come FastAPI, il test client integrato supporta WebSocket:

```python
import pytest
from httpx import AsyncClient
from httpx_ws import aconnect_ws
from mia_app import app

async def test_websocket_chat():
    async with AsyncClient(app=app, base_url="http://test") as client:
        async with aconnect_ws("/ws/chat/stanza-1", client) as ws:
            # Invia un messaggio
            await ws.send_text("Ciao dalla stanza 1")

            # Ricevi la risposta
            risposta = await ws.receive_text()
            assert "Ciao" in risposta

async def test_websocket_broadcast():
    """Verifica che i messaggi vengano distribuiti a tutti i client connessi."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        async with aconnect_ws("/ws/chat/stanza-1", client) as ws1, \
                   aconnect_ws("/ws/chat/stanza-1", client) as ws2:

            await ws1.send_text("Messaggio broadcast")
            # ws2 dovrebbe ricevere il messaggio inviato da ws1
            risposta = await ws2.receive_text()
            assert risposta == "Messaggio broadcast"
```

#### Testing di Generatori Asincroni

I generatori asincroni (`async for`) richiedono un approccio specifico per il testing:

```python
async def stream_eventi(sorgente):
    """Generatore asincrono che emette eventi da una sorgente."""
    async for evento in sorgente:
        if evento["tipo"] != "heartbeat":
            yield evento

async def test_stream_filtra_heartbeat():
    """Verifica che lo stream filtri gli eventi heartbeat."""
    eventi_mock = [
        {"tipo": "dati", "payload": "a"},
        {"tipo": "heartbeat"},
        {"tipo": "dati", "payload": "b"},
        {"tipo": "heartbeat"},
        {"tipo": "dati", "payload": "c"},
    ]

    async def sorgente_mock():
        for evento in eventi_mock:
            yield evento

    risultati = []
    async for evento in stream_eventi(sorgente_mock()):
        risultati.append(evento)

    assert len(risultati) == 3
    assert all(e["tipo"] == "dati" for e in risultati)
```

#### Gestione dei Timeout nei Test Asincroni

I test asincroni sono particolarmente vulnerabili a blocchi (deadlock, attese infinite). Combinare `pytest-timeout` con `asyncio.wait_for` fornisce protezione a due livelli:

```python
import asyncio

async def test_con_timeout_esplicito():
    """Timeout a livello applicativo per operazioni specifiche."""
    try:
        risultato = await asyncio.wait_for(
            operazione_potenzialmente_lenta(),
            timeout=3.0,
        )
        assert risultato is not None
    except asyncio.TimeoutError:
        pytest.fail("L'operazione ha superato il timeout di 3 secondi")

@pytest.mark.timeout(10)  # Timeout a livello di test
async def test_pipeline_asincrona():
    """Pipeline con timeout sia per il singolo step che per il test intero."""
    dati = await asyncio.wait_for(recupera_dati(), timeout=2.0)
    elaborati = await asyncio.wait_for(elabora(dati), timeout=5.0)
    assert len(elaborati) > 0
```

---

## Snapshot Testing

Lo snapshot testing cattura l'output di una funzione e lo confronta con un riferimento salvato su disco. Se l'output cambia, il test fallisce — e lo sviluppatore decide se la modifica e intenzionale (aggiorna lo snapshot) o un bug.

```python
# pip install syrupy  (o pytest-snapshot)

# Con syrupy (raccomandato)
def test_schema_json(snapshot):
    from mia_app.modelli import Utente
    schema = Utente.model_json_schema()
    assert schema == snapshot

def test_output_formattato(snapshot):
    report = genera_report(dati_esempio)
    assert report == snapshot

# Alla prima esecuzione, syrupy crea il file __snapshots__/test_modulo.ambr
# Le esecuzioni successive confrontano con lo snapshot salvato

# Per aggiornare gli snapshot (dopo una modifica intenzionale):
# pytest --snapshot-update

# Con pytest-snapshot (alternativa)
def test_risposta_api(snapshot):
    risposta = client.get("/api/prodotti/1")
    snapshot.assert_match(risposta.json())
```

Quando usare snapshot testing:
- **JSON Schema**: verifica che lo schema generato non cambi accidentalmente
- **Output di rendering**: HTML, template renderizzati, report formattati
- **Risposte API**: struttura delle risposte
- **Serializzazione**: output di `model_dump()`, `to_dict()`, ecc.

Quando NON usare:
- Output con componenti non deterministici (timestamp, UUID) — prima normalizza
- Test dove il valore atteso e semplice e noto — usa un assert diretto

### Snapshot Testing Avanzato

#### Serializzatori Personalizzati

Il comportamento predefinito di syrupy serializza gli snapshot in formato `ambr` (AmberSnapshotSerializer). Per output specifici, e possibile definire serializzatori personalizzati che normalizzano componenti non deterministici prima del confronto:

```python
from syrupy.extensions.single_file import SingleFileSnapshotExtension
from syrupy.extensions.json import JSONSnapshotExtension

# Usa snapshot JSON per risposte API (piu leggibili nei diff)
class MioSerializzatoreJSON(JSONSnapshotExtension):
    pass

@pytest.fixture
def snapshot_json(snapshot):
    return snapshot.use_extension(JSONSnapshotExtension)

def test_risposta_api(snapshot_json, client):
    risposta = client.get("/api/utenti/1")
    # Lo snapshot viene salvato come file .json separato
    assert risposta.json() == snapshot_json
```

#### Normalizzazione di Valori Dinamici

Per gestire timestamp, UUID e altri valori dinamici negli snapshot, normalizzare i dati prima del confronto:

```python
import re

def normalizza_snapshot(dati: dict) -> dict:
    """Sostituisce valori dinamici con placeholder deterministici."""
    normalizzati = dati.copy()
    if "id" in normalizzati:
        normalizzati["id"] = "<UUID>"
    if "creato_il" in normalizzati:
        normalizzati["creato_il"] = "<TIMESTAMP>"
    if "token" in normalizzati:
        normalizzati["token"] = "<TOKEN>"
    return normalizzati

def test_creazione_utente_snapshot(snapshot, client):
    risposta = client.post("/api/utenti", json={"nome": "Mario"})
    dati = normalizza_snapshot(risposta.json())
    assert dati == snapshot
```

#### Workflow di Aggiornamento Snapshot in CI

In una pipeline CI, gli snapshot devono essere trattati come parte del codice sorgente. La strategia consigliata prevede:

1. **Sviluppo locale**: eseguire `pytest --snapshot-update` per aggiornare gli snapshot dopo modifiche intenzionali
2. **Commit**: includere i file snapshot aggiornati nel commit
3. **CI**: eseguire `pytest` senza `--snapshot-update` — il test fallisce se lo snapshot non corrisponde, indicando che lo sviluppatore ha dimenticato di aggiornare

```yaml
# Nel workflow CI - MAI usare --snapshot-update
- name: Verifica snapshot
  run: pytest tests/ -x  # Fallisce se snapshot non aggiornati

# Script per lo sviluppatore
# make update-snapshots
# pytest --snapshot-update && git add __snapshots__/
```

#### Snapshot Multi-Formato

Per componenti che producono output in formati diversi (JSON, HTML, testo), e possibile usare snapshot multipli nello stesso test:

```python
def test_generazione_report(snapshot):
    report = genera_report(dati_vendite)
    # Ogni invocazione di == snapshot crea uno snapshot separato
    assert report.to_json() == snapshot
    assert report.to_html() == snapshot
    assert report.to_text() == snapshot
    # syrupy gestisce automaticamente snapshot multipli con indici
```

---

## Mutation Testing con mutmut

Il mutation testing misura la **qualita** dei test, non solo la copertura. Il principio: se si modifica (muta) il codice sorgente e nessun test fallisce, i test non stanno verificando adeguatamente quel codice.

```bash
# Installazione
pip install mutmut

# Esecuzione
mutmut run --paths-to-mutate=src/

# Visualizza i risultati
mutmut results

# Mostra una mutazione specifica
mutmut show 42

# Output HTML
mutmut html
```

### Come Funziona

mutmut genera **mutanti** — versioni del codice con piccole modifiche:

| Tipo di Mutazione | Originale | Mutante |
|---|---|---|
| Operatore aritmetico | `a + b` | `a - b` |
| Operatore di confronto | `a > b` | `a >= b` |
| Valore di ritorno | `return True` | `return False` |
| Costante | `timeout = 30` | `timeout = 31` |
| Operatore logico | `a and b` | `a or b` |
| Rimozione decoratore | `@cache` | (rimosso) |

Per ogni mutante, mutmut esegue la suite di test. Se tutti i test passano (il mutante **sopravvive**), significa che i test non rilevano la modifica.

```python
# Esempio: la funzione ha una mutazione non rilevata
def classifica_eta(eta: int) -> str:
    if eta < 18:      # mutmut potrebbe cambiare < in <=
        return "minore"
    return "adulto"

# Questo test NON rileva la mutazione < → <=
def test_classifica_base():
    assert classifica_eta(10) == "minore"
    assert classifica_eta(30) == "adulto"

# Questo test RILEVA la mutazione (il boundary case)
def test_classifica_boundary():
    assert classifica_eta(17) == "minore"
    assert classifica_eta(18) == "adulto"  # Questa asserzione cattura la mutazione
```

### Configurazione in pyproject.toml

```toml
[tool.mutmut]
paths_to_mutate = "src/"
tests_dir = "tests/"
runner = "python -m pytest -x --tb=no -q"
dict_synonyms = "Struct, NamedStruct"
```

### Mutation Testing Avanzato

#### Analisi dei Mutanti Sopravvissuti

Quando mutmut completa l'esecuzione, il passo cruciale e analizzare i mutanti sopravvissuti. Non tutti i mutanti sopravvissuti indicano test carenti — alcuni rappresentano mutazioni equivalenti (il codice mutato produce lo stesso risultato) o mutazioni in codice non critico:

```bash
# Visualizza tutti i mutanti sopravvissuti
mutmut results

# Ispeziona un mutante specifico
mutmut show 42
# Output:
# --- src/calcolatrice.py
# +++ src/calcolatrice.py (mutant 42)
# @@ -15,1 +15,1 @@
# -    if prezzo > 100:
# +    if prezzo >= 100:

# Applica il mutante al codice sorgente per testarlo manualmente
mutmut apply 42
```

Strategie per gestire i mutanti sopravvissuti:

1. **Mutante significativo** — scrivi un test aggiuntivo che lo uccida. Tipicamente un boundary test mancante
2. **Mutazione equivalente** — il codice mutato produce lo stesso risultato per tutti gli input possibili. Segna come falso positivo
3. **Codice non critico** — metodi `__repr__`, logging, commenti. Escludi dalla mutazione

#### Integrazione con Coverage per Mutazione Mirata

mutmut puo essere configurato per mutare solo le righe effettivamente coperte dai test, riducendo drasticamente il tempo di esecuzione:

```toml
# pyproject.toml
[tool.mutmut]
paths_to_mutate = "src/"
tests_dir = "tests/"
runner = "python -m pytest -x --tb=no -q"
# Muta solo le righe coperte dai test
use_coverage = true
```

```bash
# Prima genera il report di coverage
pytest --cov=src --cov-report=xml tests/

# Poi esegui mutmut con la coverage
mutmut run --use-coverage
```

#### Integrazione CI per Mutation Testing

Il mutation testing e computazionalmente costoso — eseguirlo su ogni commit non e pratico. Una strategia pragmatica prevede:

```yaml
# .github/workflows/mutation.yml
name: Mutation Testing
on:
  schedule:
    - cron: '0 2 * * 1'  # Ogni lunedi alle 2:00 AM
  workflow_dispatch:       # Esecuzione manuale su richiesta

jobs:
  mutation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e ".[dev]" mutmut
      - run: pytest --cov=src --cov-report=xml tests/
      - run: mutmut run --use-coverage --CI
      - run: mutmut results
      - name: Verifica mutation score
        run: |
          SCORE=$(mutmut results | grep -oP '\d+\.\d+%' | head -1)
          echo "Mutation score: $SCORE"
```

#### Confronto: mutmut vs cosmic-ray

| Caratteristica | mutmut | cosmic-ray |
|---|---|---|
| Facilita d'uso | Molto semplice, zero configurazione | Richiede piu setup |
| Velocita | Piu lento (esegue l'intera suite per mutante) | Piu veloce (usa celery per distribuzione) |
| Tasso di rilevamento | ~88.5% | ~82.7% |
| Mutazioni Python-specifiche | Ottime (dict, f-string, decorator) | Buone |
| Integrazione CI | Supporto nativo | Richiede configurazione aggiuntiva |
| Distribuzione parallela | Limitata | Nativa con celery |

Per progetti di piccole-medie dimensioni, mutmut e la scelta migliore per la sua semplicita. Per progetti grandi con suite di test lente, cosmic-ray con distribuzione celery puo essere piu pratico.

---

## TDD Workflow Deep Dive

### Il Ciclo Red-Green-Refactor in Pratica

```
    ┌──────────────┐
    │    RED       │ ← Scrivi un test che FALLISCE
    │ (test fails) │   (verifica che il test rilevi l'assenza della funzionalita)
    └──────┬───────┘
           │
    ┌──────▼───────┐
    │   GREEN      │ ← Scrivi il codice MINIMO per far passare il test
    │ (test passes)│   (niente di piu, niente generalizzazione prematura)
    └──────┬───────┘
           │
    ┌──────▼───────┐
    │  REFACTOR    │ ← Migliora il codice mantenendo tutti i test verdi
    │ (improve)    │   (elimina duplicazione, migliora nomi, semplifica)
    └──────┬───────┘
           │
           └──→ Torna a RED per la prossima funzionalita
```

### Esempio Completo: Carrello della Spesa

```python
# PASSO 1 — RED: il test descrive il comportamento desiderato
# test_carrello.py

def test_carrello_vuoto_ha_zero_prodotti():
    carrello = Carrello()
    assert carrello.numero_prodotti == 0

# ESEGUI: pytest → FALLISCE (Carrello non esiste ancora)

# PASSO 2 — GREEN: implementazione minima
# carrello.py
class Carrello:
    @property
    def numero_prodotti(self) -> int:
        return 0

# ESEGUI: pytest → PASSA

# PASSO 3 — RED: prossimo test
def test_aggiungi_prodotto():
    carrello = Carrello()
    carrello.aggiungi("Mela", prezzo=1.50)
    assert carrello.numero_prodotti == 1

# ESEGUI: pytest → FALLISCE

# PASSO 4 — GREEN
class Carrello:
    def __init__(self):
        self._prodotti = []

    @property
    def numero_prodotti(self) -> int:
        return len(self._prodotti)

    def aggiungi(self, nome: str, prezzo: float) -> None:
        self._prodotti.append({"nome": nome, "prezzo": prezzo})

# PASSO 5 — RED: calcolo totale
def test_totale_carrello():
    carrello = Carrello()
    carrello.aggiungi("Mela", prezzo=1.50)
    carrello.aggiungi("Pane", prezzo=2.00)
    assert carrello.totale == 3.50

# PASSO 6 — GREEN
class Carrello:
    # ... metodi precedenti ...

    @property
    def totale(self) -> float:
        return sum(p["prezzo"] for p in self._prodotti)

# PASSO 7 — REFACTOR: estrarre un dataclass per il prodotto
from dataclasses import dataclass

@dataclass(frozen=True)
class Prodotto:
    nome: str
    prezzo: float
    quantita: int = 1

class Carrello:
    def __init__(self):
        self._prodotti: list[Prodotto] = []

    @property
    def numero_prodotti(self) -> int:
        return sum(p.quantita for p in self._prodotti)

    @property
    def totale(self) -> float:
        return sum(p.prezzo * p.quantita for p in self._prodotti)

    def aggiungi(self, nome: str, prezzo: float, quantita: int = 1) -> None:
        self._prodotti.append(Prodotto(nome=nome, prezzo=prezzo, quantita=quantita))

# Tutti i test precedenti DEVONO ancora passare dopo il refactoring
```

### Regole del TDD

1. **Non scrivere codice di produzione senza un test che fallisce** — Il test e la specifica eseguibile del comportamento.
2. **Scrivere il test minimo che fallisce** — Un solo assert per volta. Non anticipare funzionalita future.
3. **Scrivere il codice minimo che fa passare il test** — Niente generalizzazione, niente ottimizzazione. Fai passare il test e basta.
4. **Refactoring solo con tutti i test verdi** — Mai refactorizzare con test rossi. I test sono la rete di sicurezza per il refactoring.
5. **Triangolazione** — Se il codice minimo e una costante hardcoded, scrivi un secondo test con un valore diverso per forzare l'implementazione reale.

---

## Performance Testing

Misurare le prestazioni del codice durante i test aiuta a prevenire regressioni e a identificare colli di bottiglia.

### pytest-benchmark

```bash
pip install pytest-benchmark
```

```python
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

def fibonacci_iterativo(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a

def test_fibonacci_benchmark(benchmark):
    """Misura il tempo di esecuzione di fibonacci."""
    risultato = benchmark(fibonacci_iterativo, 100)
    assert risultato == 354224848179261915075

def test_confronto_implementazioni(benchmark):
    """Confronta diverse implementazioni."""
    benchmark.pedantic(
        fibonacci_iterativo,
        args=(50,),
        rounds=1000,
        warmup_rounds=10,
    )
```

L'output mostra statistiche dettagliate: media, mediana, deviazione standard, min, max e numero di iterazioni.

### Il Modulo timeit

Per misurazioni rapide senza pytest-benchmark:

```python
import timeit

def test_prestazioni_ordinamento():
    tempo = timeit.timeit(
        stmt="sorted(dati)",
        setup="import random; dati = [random.randint(0, 10000) for _ in range(1000)]",
        number=100,
    )
    # Verifica che 100 ordinamenti richiedano meno di 1 secondo
    assert tempo < 1.0

def test_confronto_approcci():
    tempo_lista = timeit.timeit(
        "[x**2 for x in range(1000)]",
        number=1000,
    )
    tempo_map = timeit.timeit(
        "list(map(lambda x: x**2, range(1000)))",
        number=1000,
    )
    # Registra i risultati (non asserire, le prestazioni variano)
    print(f"List comprehension: {tempo_lista:.4f}s")
    print(f"map+lambda: {tempo_map:.4f}s")
```

### Profiling dei Test

Per identificare i test piu lenti e ottimizzarli:

```bash
# Mostra i 20 test piu lenti
pytest --durations=20

# Mostra tutti i test con durata > 0
pytest --durations=0

# Profiling dettagliato con cProfile
python -m cProfile -o profilo.prof -m pytest tests/
python -m pstats profilo.prof
```

```python
# Profiling all'interno di un test
import cProfile
import pstats

def test_profiling_elaborazione():
    profiler = cProfile.Profile()
    profiler.enable()

    risultato = elaborazione_complessa(dati_grandi)

    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats("cumulative")
    stats.print_stats(20)  # Top 20 funzioni per tempo cumulativo

    assert risultato.completato
```

---

## Ecosistema Plugin pytest

L'ecosistema di plugin di pytest e uno dei motivi principali della sua adozione universale. Con oltre 1500 plugin disponibili su PyPI, esiste un plugin per praticamente ogni esigenza di testing. Questa sezione approfondisce i plugin piu utili oltre quelli gia trattati.

### pytest-randomly

`pytest-randomly` randomizza l'ordine di esecuzione dei test ad ogni run, rivelando dipendenze nascoste tra test. Un test che passa solo perche un altro test ha lasciato uno stato residuo viene immediatamente scoperto:

```bash
pip install pytest-randomly

# L'ordine viene randomizzato automaticamente
pytest tests/

# Riproduci un ordine specifico con il seed
pytest tests/ -p randomly -p no:randomly  # Disabilita
pytest tests/ --randomly-seed=12345       # Seed specifico
pytest tests/ --randomly-seed=last        # Ripeti l'ultimo ordine
```

```
# Output tipico
Using --randomly-seed=1716547200
tests/test_auth.py::test_login PASSED
tests/test_cache.py::test_invalidazione PASSED
tests/test_auth.py::test_logout FAILED  ← dipendenza da test_login scoperta!
```

Se un test fallisce con ordine casuale ma passa con ordine fisso, quel test ha una dipendenza implicita che deve essere risolta. La fixture `autouse` con scope appropriato o l'isolamento tramite rollback DB sono le soluzioni tipiche.

### pytest-repeat

Per identificare test flaky (instabili), `pytest-repeat` esegue ogni test un numero configurabile di volte:

```bash
pip install pytest-repeat

# Esegui ogni test 10 volte
pytest --count=10 tests/

# Ferma alla prima ripetizione fallita
pytest --count=100 -x tests/test_operazione_flaky.py
```

```python
# Oppure, per test specifici:
@pytest.mark.repeat(50)
def test_operazione_concorrente():
    """Esegui 50 volte per verificare l'assenza di race condition."""
    risultato = operazione_thread_safe()
    assert risultato.consistente
```

### pytest-deadfixtures

Con il tempo, i progetti accumulano fixture inutilizzate nei file `conftest.py`. `pytest-deadfixtures` individua fixture non referenziate da nessun test:

```bash
pip install pytest-deadfixtures

# Trova fixture non utilizzate
pytest --dead-fixtures tests/

# Output:
# tests/conftest.py::vecchia_connessione_db (non utilizzata)
# tests/api/conftest.py::mock_servizio_legacy (non utilizzata)
```

### pytest-sugar

Migliora l'output visivo di pytest con barre di progresso, output colorato piu leggibile e report degli errori immediato:

```bash
pip install pytest-sugar
# Nessuna configurazione necessaria — si attiva automaticamente

# Per disabilitare temporaneamente
pytest -p no:sugar tests/
```

### Scrivere Plugin Personalizzati

pytest supporta la creazione di plugin personalizzati tramite gli hook del framework. Un plugin personalizzato nel `conftest.py` puo estendere il comportamento di pytest senza installare pacchetti aggiuntivi:

```python
# conftest.py — plugin personalizzato per misurare la durata dei setup

import time
import pytest

class TimingPlugin:
    """Plugin che registra il tempo di setup di ogni fixture."""

    def __init__(self):
        self.tempi_fixture = {}

    @pytest.hookimpl(hookwrapper=True)
    def pytest_fixture_setup(self, fixturedef, request):
        inizio = time.perf_counter()
        yield
        durata = time.perf_counter() - inizio
        nome = fixturedef.argname
        if durata > 0.1:  # Registra solo fixture lente (>100ms)
            self.tempi_fixture[nome] = durata

    def pytest_terminal_summary(self, terminalreporter):
        if self.tempi_fixture:
            terminalreporter.write_sep("=", "Fixture lente")
            for nome, durata in sorted(
                self.tempi_fixture.items(), key=lambda x: -x[1]
            ):
                terminalreporter.write_line(f"  {nome}: {durata:.3f}s")

def pytest_configure(config):
    config.pluginmanager.register(TimingPlugin(), "timing-plugin")
```

### Configurazione Ottimale dei Plugin

Una configurazione di progetto professionale combina diversi plugin per massimizzare efficienza e qualita:

```toml
# pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
addopts = [
    "--strict-markers",       # Errore su marker non registrati
    "--strict-config",        # Errore su opzioni di configurazione sconosciute
    "-ra",                    # Mostra sommario per test non passati
    "--tb=short",             # Traceback conciso
    "--cov=src",              # Coverage automatica
    "--cov-branch",           # Branch coverage
    "--cov-report=term-missing:skip-covered",  # Report solo file non coperti
    "--randomly-seed=last",   # Riproduci l'ultimo ordine casuale
]
markers = [
    "slow: test che richiedono molto tempo",
    "integrazione: test che richiedono servizi esterni",
    "e2e: test end-to-end",
    "notturno: test da eseguire solo nella build notturna",
]
filterwarnings = [
    "error",                  # Tratta i warning come errori
    "ignore::DeprecationWarning:modulo_legacy",  # Ignora warning da moduli legacy
]
```

---

## CI/CD Integration

L'integrazione dei test nella pipeline CI/CD garantisce che ogni modifica al codice venga verificata automaticamente prima del merge.

### Esecuzione di pytest in GitHub Actions

```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12", "3.13"]

    steps:
      - uses: actions/checkout@v4

      - name: Configura Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Installa dipendenze
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"

      - name: Esegui linting
        run: |
          ruff check src/ tests/

      - name: Esegui test con coverage
        run: |
          pytest --cov=src --cov-report=xml --cov-report=term-missing --cov-fail-under=85 tests/

      - name: Carica report coverage
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml
          fail_ci_if_error: true
```

### Test Reporting

Per generare report leggibili nei workflow CI:

```bash
# Report JUnit XML (compatibile con la maggior parte dei sistemi CI)
pytest --junitxml=report.xml tests/

# Report HTML
pytest --html=report.html --self-contained-html tests/
```

```yaml
# Nella GitHub Action, pubblica il report come artifact
      - name: Carica report test
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: test-report
          path: report.html
```

### Coverage Badges

Per mostrare il badge di coverage nel README del progetto:

```yaml
      - name: Genera badge coverage
        uses: codecov/codecov-action@v4
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
```

Dopo la configurazione su Codecov, il badge puo essere incluso nel README:

```markdown
[![codecov](https://codecov.io/gh/utente/progetto/branch/main/graph/badge.svg)](https://codecov.io/gh/utente/progetto)
```

### Fallimento su Diminuzione della Coverage

Per impedire che nuove modifiche riducano la coverage complessiva:

```toml
# pyproject.toml
[tool.coverage.report]
fail_under = 85
```

```yaml
# Nel workflow CI
      - name: Verifica soglia coverage
        run: |
          pytest --cov=src --cov-fail-under=85 tests/
```

Servizi come Codecov possono essere configurati per commentare automaticamente le pull request con il delta di coverage e bloccare il merge se la coverage diminuisce.

### Strategie CI/CD Avanzate

#### Test Splitting e Parallelizzazione in CI

Per progetti con suite di test grandi, eseguire tutti i test sequenzialmente in CI puo richiedere decine di minuti. Il test splitting distribuisce i test su piu job paralleli:

```yaml
# .github/workflows/test-parallel.yml
name: Test Paralleli

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        # Dividi i test in 4 shard
        shard: [1, 2, 3, 4]

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e ".[dev]"
      - name: Esegui shard ${{ matrix.shard }}
        run: |
          # Usa pytest-split per bilanciare il carico
          pytest --splits 4 --group ${{ matrix.shard }} \
                 --splitting-algorithm least_duration \
                 --cov=src --cov-report=xml tests/
      - name: Carica coverage parziale
        uses: actions/upload-artifact@v4
        with:
          name: coverage-${{ matrix.shard }}
          path: coverage.xml

  merge-coverage:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/download-artifact@v4
      - run: pip install coverage
      - run: coverage combine coverage-*/coverage.xml
      - run: coverage report --fail-under=85
```

#### Selezione Test Basata sul Diff

Eseguire solo i test rilevanti per i file modificati riduce drasticamente i tempi di CI per le pull request. Il plugin `pytest-testmon` traccia le dipendenze tra codice sorgente e test:

```bash
pip install pytest-testmon

# Prima esecuzione: crea il database delle dipendenze
pytest --testmon tests/

# Esecuzioni successive: esegue solo i test impattati dalle modifiche
pytest --testmon tests/
# Output: collected 450 items / 430 deselected / 20 selected
```

```yaml
# Nel workflow CI per le pull request
- name: Test basati sul diff
  run: |
    # Installa testmon
    pip install pytest-testmon

    # Fetch del branch base per il diff
    git fetch origin ${{ github.base_ref }}

    # Esegui solo i test impattati
    pytest --testmon --tb=short tests/
```

#### Strategy Matrix Avanzata

Per testare combinazioni di Python, sistema operativo e dipendenze:

```yaml
jobs:
  test:
    strategy:
      fail-fast: false  # Non fermare gli altri job se uno fallisce
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ["3.11", "3.12", "3.13"]
        exclude:
          # Escludi combinazioni non supportate
          - os: windows-latest
            python-version: "3.11"
        include:
          # Aggiungi combinazioni specifiche con variabili extra
          - os: ubuntu-latest
            python-version: "3.12"
            database: postgres
            coverage: true

    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -e ".[dev]"
      - name: Test con coverage
        if: matrix.coverage == true
        run: pytest --cov=src --cov-fail-under=85 tests/
      - name: Test senza coverage
        if: matrix.coverage != true
        run: pytest tests/
```

#### Pre-commit Hooks per Testing

Integrare test leggeri nel flusso pre-commit garantisce che ogni commit sia almeno minimamente verificato:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: test-unitari-veloci
        name: Test unitari rapidi
        entry: pytest tests/unit/ -x --timeout=30 -q
        language: system
        pass_filenames: false
        always_run: true
        stages: [pre-commit]

      - id: type-check
        name: Type check
        entry: mypy src/
        language: system
        pass_filenames: false
        types: [python]
```

#### Coverage Differenziale con Codecov

Codecov e SonarQube supportano la coverage differenziale, che misura la coverage solo sul codice nuovo o modificato nella pull request, indipendentemente dalla coverage complessiva del progetto:

```yaml
# codecov.yml
coverage:
  status:
    project:
      default:
        target: 85%          # Coverage minima del progetto
    patch:
      default:
        target: 90%          # Coverage minima del codice NUOVO (nella PR)
        threshold: 2%        # Tolleranza

comment:
  layout: "reach,diff,flags,files"
  behavior: default
  require_changes: true       # Commenta solo se la coverage cambia
```

Questa configurazione blocca le PR che aggiungono codice non testato, anche se la coverage complessiva rimane sopra la soglia.

#### Pipeline Completa per Progetto Python

Una pipeline CI/CD matura per un progetto Python professionale include diverse fasi orchestrate:

```yaml
# .github/workflows/ci.yml
name: CI Completa

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  # Fase 1: Qualita del codice (veloce, feedback immediato)
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install ruff mypy
      - run: ruff check src/ tests/
      - run: mypy src/ --strict

  # Fase 2: Test unitari (veloce, massima copertura)
  unit-tests:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e ".[dev]"
      - run: pytest tests/unit/ -n auto --cov=src --cov-fail-under=85 --junitxml=results.xml
      - uses: codecov/codecov-action@v4

  # Fase 3: Test di integrazione (piu lenti, richiedono servizi)
  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432
      redis:
        image: redis:7
        ports:
          - 6379:6379
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e ".[dev]"
      - run: pytest tests/integration/ -m integrazione --timeout=60

  # Fase 4: Mutation testing (settimanale, non bloccante)
  mutation:
    if: github.event_name == 'schedule'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install -e ".[dev]" mutmut
      - run: mutmut run --use-coverage --CI
```

---

## Best Practices

Le seguenti dieci best practices rappresentano principi consolidati per scrivere test efficaci e mantenibili.

**1. Ogni test deve verificare un solo comportamento.**
Un test che verifica piu cose contemporaneamente e difficile da diagnosticare quando fallisce. Se il test si chiama `test_creazione_e_modifica_e_cancellazione_utente`, quasi certamente sta facendo troppo. Separalo in tre test distinti, ciascuno con una singola asserzione o un gruppo di asserzioni strettamente correlate.

**2. I test devono essere indipendenti e isolati.**
L'ordine di esecuzione dei test non deve mai influenzare il risultato. Ogni test deve preparare il proprio stato (Arrange), eseguire l'operazione (Act) e verificare il risultato (Assert) senza dipendere da effetti collaterali di test precedenti. Le fixtures con scope appropriato e il pattern di rollback delle transazioni sono gli strumenti principali per garantire l'isolamento.

**3. Usa nomi descrittivi per i test.**
Il nome del test deve comunicare chiaramente cosa viene verificato. `test_calcola_sconto_applica_dieci_percento_per_clienti_gold` e infinitamente piu utile di `test_sconto_1`. Quando un test fallisce nella pipeline CI, il nome deve bastare per capire cosa si e rotto, senza dover leggere il codice.

**4. Segui il pattern AAA (Arrange-Act-Assert).**
Struttura ogni test con tre sezioni ben definite, separate visivamente da righe vuote o commenti. Questa convenzione rende i test uniformi e immediatamente leggibili per qualsiasi membro del team. Un test ben strutturato non richiede commenti aggiuntivi per essere compreso.

**5. Testa i casi limite e gli errori, non solo il percorso felice.**
I bug si annidano nelle condizioni limite: liste vuote, stringhe vuote, valori None, numeri negativi, overflow, caratteri Unicode. Per ogni funzione, chiediti: "Cosa succede con input inatteso?". Il property-based testing con Hypothesis e un alleato prezioso per scoprire automaticamente questi casi.

**6. Mantieni i test veloci.**
Una suite di test lenta viene eseguita meno frequentemente, riducendo il feedback loop. Gli unit test dovrebbero completarsi in millisecondi. Se un test richiede piu di un secondo, probabilmente sta facendo I/O reale e dovrebbe essere mockato oppure spostato nella categoria dei test di integrazione. Usa `pytest-xdist` per parallelizzare l'esecuzione e marcatori personalizzati per separare test lenti e veloci.

**7. Non testare i dettagli implementativi.**
I test dovrebbero verificare il *cosa* (comportamento esterno), non il *come* (implementazione interna). Se cambi l'algoritmo di ordinamento interno ma il risultato resta corretto, nessun test dovrebbe rompersi. L'over-mocking di metodi privati e il sintomo piu comune di test troppo accoppiati all'implementazione. Testa le interfacce pubbliche.

**8. Automatizza l'esecuzione nella pipeline CI/CD.**
I test che non vengono eseguiti automaticamente ad ogni commit perdono gran parte del loro valore. Configura GitHub Actions (o il sistema CI preferito) per eseguire la suite completa su ogni push e pull request. Includi la verifica della soglia di coverage e blocca il merge se i test falliscono. Un progetto senza CI e un progetto dove "funziona sulla mia macchina" e l'unica garanzia.

**9. Tratta il codice dei test con la stessa cura del codice di produzione.**
I test sono codice a tutti gli effetti: meritano refactoring, nomi chiari, assenza di duplicazione e una struttura coerente. Evita la tentazione di copiare e incollare test simili: usa `parametrize` per le varianti e le fixtures per il codice condiviso. Un test illeggibile e un test che verra ignorato quando fallisce.

**10. Misura la coverage ma non farne un feticcio.**
La coverage e un indicatore utile per individuare zone scoperte, ma una coverage del 100% non garantisce la qualita dei test. Un test che esegue una riga senza verificarne il risultato e un falso positivo nella coverage. Concentrati sulla qualita delle asserzioni e sulla significativita dei casi testati. Una coverage dell'85% con test ben scritti e molto piu preziosa di una coverage del 100% con test superficiali.

---

> **Nota finale**: il testing non e un costo aggiuntivo, ma un investimento. Ogni ora spesa a scrivere test ne risparmia molte in debugging, regressioni e incidenti in produzione. Un progetto con una suite di test solida e un progetto su cui si puo lavorare con fiducia, oggi e in futuro.

---

## Esercizi

1. **TDD per un modulo di utilita** — Implementa un modulo `string_utils` con le funzioni `slugify()`, `truncate()`, `camel_to_snake()` e `extract_emails()` seguendo rigorosamente il ciclo TDD (Red-Green-Refactor). Scrivi ogni test PRIMA dell'implementazione, esegui il test per verificare che fallisca, implementa il minimo codice necessario, poi refactorizza. Target: 100% coverage.

2. **Fixture avanzate con scope e teardown** — Crea una suite di test per un'applicazione CRUD che utilizzi: fixture con scope `session` per la connessione DB (SQLite in-memory), fixture con scope `function` per il rollback delle transazioni, fixture parametrizzate per testare con dataset diversi, e una fixture `tmp_path` per file temporanei. Verifica che i test siano completamente isolati tra loro.

3. **Property-based testing con Hypothesis** — Prendi 3 funzioni di una libreria (es. sort, encode/decode, serialize/deserialize) e scrivi property-based test con `hypothesis`. Definisci strategie custom per generare dati di dominio. Confronta i bug trovati con Hypothesis vs quelli trovati con test tradizionali parametrizzati.

4. **Mocking e patching** — Scrivi test per un modulo che interagisce con un'API esterna (es. weather API) utilizzando `unittest.mock.patch`, `MagicMock` e `pytest-mock`. Testa: risposta di successo, timeout, errore HTTP 500, JSON malformato, e rate limiting. Verifica che i mock non mascherino bug reali testando anche con un integration test contro un server mock locale (`responses` o `httpretty`).

5. **CI/CD testing pipeline** — Configura una GitHub Action che: (a) esegua `pytest` con coverage report, (b) imponga una soglia minima dell'80% con `--cov-fail-under`, (c) esegua i test in parallelo con `pytest-xdist`, (d) separi test unitari e di integrazione con marker, (e) carichi il report di coverage come artifact. Documenta la configurazione e spiega ogni scelta.

---

## Letture e Riferimenti

### Fonti primarie

- pytest Documentation — https://docs.pytest.org/ (consultato: 2026-05-24)
- Python Documentation — *`unittest`* — https://docs.python.org/3/library/unittest.html (consultato: 2026-05-24)
- Python Documentation — *`unittest.mock`* — https://docs.python.org/3/library/unittest.mock.html (consultato: 2026-05-24)
- pytest-cov Documentation — https://pytest-cov.readthedocs.io/ (consultato: 2026-05-24)
- pytest-xdist Documentation — https://pytest-xdist.readthedocs.io/ (consultato: 2026-05-24)
- Hypothesis Documentation — https://hypothesis.readthedocs.io/ (consultato: 2026-05-24)
- Coverage.py Documentation — https://coverage.readthedocs.io/ (consultato: 2026-05-24)
- pytest-mock Documentation — https://pytest-mock.readthedocs.io/ (consultato: 2026-05-24)
- pytest-bdd Documentation — https://pytest-bdd.readthedocs.io/ (consultato: 2026-05-24)
- pytest-asyncio Documentation — https://pytest-asyncio.readthedocs.io/ (consultato: 2026-05-24)
- Testcontainers Python — https://testcontainers-python.readthedocs.io/ (consultato: 2026-05-24)
- mutmut Documentation — https://mutmut.readthedocs.io/ (consultato: 2026-05-24)
- syrupy Documentation — https://github.com/syrupy-project/syrupy (consultato: 2026-05-24)
- factory_boy Documentation — https://factoryboy.readthedocs.io/ (consultato: 2026-05-24)

### Libri consigliati

- *Python Testing with pytest, 2nd Edition* — Brian Okken — Pragmatic Bookshelf, 2022
- *Architecture Patterns with Python* — Harry Percival, Bob Gregory — O'Reilly, 2020 (Capitoli su TDD)

---

## Riferimenti Incrociati

| Modulo | Relazione |
|---|---|
| [22 — Clean Code](22-clean-code.md) | Test come documentazione, naming, qualita del codice di test |
| [27 — CI/CD](27-ci-cd-per-python.md) | Automazione dei test nella pipeline CI/CD |
| [02 — OOP](02-oop.md) | Mock di classi, dependency injection per testabilita |
| [07 — Error Handling](07-error-handling-e-logging.md) | Testing delle eccezioni, logging nei test |
| [21 — Design Patterns](21-design-patterns.md) | Pattern testabili, Strategy per test doubles |
| [13 — REST API](13-rest-api.md) | Testing di endpoint API con client di test |

---

## Glossario

| Termine | Definizione |
|---|---|
| **pytest** | Framework di testing Python de facto standard, con fixture, parametrize, marker e ricco ecosistema di plugin |
| **Fixture** | Funzione pytest che prepara lo stato necessario per i test (setup) e opzionalmente lo ripulisce (teardown) |
| **Parametrize** | Decoratore pytest che esegue lo stesso test con set di dati diversi, riducendo la duplicazione |
| **Marker** | Etichetta assegnata a test per classificarli (es. `@pytest.mark.slow`, `@pytest.mark.integration`) |
| **TDD** | Test-Driven Development — metodologia in cui i test vengono scritti prima dell'implementazione (Red-Green-Refactor) |
| **Coverage** | Percentuale di codice sorgente eseguita durante l'esecuzione dei test; misurata con `coverage.py` o `pytest-cov` |
| **Mock** | Oggetto simulato che sostituisce una dipendenza reale nei test, permettendo di controllare input/output e verificare interazioni |
| **Patch** | Tecnica di `unittest.mock` che sostituisce temporaneamente un oggetto nel namespace specificato durante un test |
| **AAA** | Arrange-Act-Assert — pattern di strutturazione dei test: preparazione, esecuzione, verifica |
| **Property-based Testing** | Approccio in cui si definiscono proprieta invarianti e il framework (Hypothesis) genera automaticamente casi di test |
| **Hypothesis** | Libreria Python per property-based testing che genera automaticamente input di test secondo strategie definite |
| **Integration Test** | Test che verifica l'interazione tra componenti reali (database, API, filesystem) senza mock |
| **E2E Test** | End-to-End test che verifica un flusso utente completo dall'interfaccia al database |
| **pytest-xdist** | Plugin pytest per l'esecuzione parallela dei test su piu CPU o nodi remoti |
| **conftest.py** | File speciale pytest che definisce fixture e hook condivisi, visibili a tutti i test nella stessa directory e sottodirectory |
| **create_autospec** | Funzione di `unittest.mock` che crea un mock con firma dei metodi validata ricorsivamente — errore se chiamato con argomenti sbagliati |
| **PropertyMock** | Mock specializzato per sostituire proprieta (`@property`) di una classe durante i test |
| **RuleBasedStateMachine** | Classe Hypothesis per il testing stateful: genera sequenze casuali di operazioni verificando invarianti a ogni passo |
| **pytest-randomly** | Plugin pytest che randomizza l'ordine di esecuzione dei test per scoprire dipendenze nascoste tra test |
| **pytest-bdd** | Plugin che integra il Behavior-Driven Development in pytest, collegando feature file Gherkin a step Python |
| **Scenario Outline** | Costrutto Gherkin che parametrizza uno scenario con una tabella `Examples`, equivalente a `@pytest.mark.parametrize` |
| **Lazy Fixture** | Meccanismo per valutare una fixture solo al momento dell'uso effettivo, necessario per usare fixture nei parametri di `parametrize` |
| **Testcontainers** | Libreria che avvia container Docker come infrastruttura di test, garantendo isolamento e riproducibilita |
| **Snapshot Testing** | Approccio che cattura l'output e lo confronta con un riferimento salvato su disco; usato per verificare che output complessi non cambino accidentalmente |
| **Branch Coverage** | Metrica di coverage che verifica che ogni ramo di ogni punto di decisione sia stato attraversato, piu rigorosa della line coverage |
