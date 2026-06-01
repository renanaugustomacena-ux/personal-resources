# Programmazione Python — Guida allo Studio

## Indice

1. [Panoramica del Campo](#panoramica-del-campo)
2. [Piano di Studio](#piano-di-studio)
   - [Fase 1: Fondamenti (settimane 1-3)](#fase-1-fondamenti-settimane-1-3)
   - [Fase 2: Tecniche Avanzate (settimane 4-5)](#fase-2-tecniche-avanzate-settimane-4-5)
   - [Fase 3: Qualità del Codice (settimane 6-7)](#fase-3-qualità-del-codice-settimane-6-7)
   - [Fase 4: Programmazione Specializzata (settimane 8-11)](#fase-4-programmazione-specializzata-settimane-8-11)
   - [Fase 5: Applicazioni Pratiche (settimane 12-14)](#fase-5-applicazioni-pratiche-settimane-12-14)
   - [Fase 6: Produzione e Deploy (settimane 15-16)](#fase-6-produzione-e-deploy-settimane-15-16)
3. [Ambiente di Laboratorio](#ambiente-di-laboratorio)
4. [Glossario](#glossario)
5. [Certificazioni Rilevanti](#certificazioni-rilevanti)
6. [Risorse Consigliate](#risorse-consigliate)

---

## Panoramica del Campo

Python è uno dei linguaggi di programmazione più influenti e diffusi al mondo. Nato nel 1991 dalla mente di Guido van Rossum, si è evoluto fino a diventare il linguaggio di riferimento in ambiti che spaziano dallo scripting di sistema allo sviluppo web, dall'automazione all'analisi dei dati, dal Machine Learning all'Internet of Things. La sua filosofia, racchiusa nel celebre *Zen of Python* (accessibile digitando `import this` nell'interprete), pone al centro la leggibilità del codice, la semplicità e l'esplicitezza: principi che lo rendono ideale sia come primo linguaggio sia come strumento professionale avanzato.

### Perché Python per il professionista IT

Per chi lavora nel settore IT — che si tratti di amministrazione di sistemi, sviluppo software, analisi dei dati o DevOps — Python rappresenta un investimento strategico di altissimo valore. Le ragioni sono molteplici:

- **Versatilità trasversale**: Python non è confinato a un singolo dominio. Un sistemista può usarlo per automatizzare task ripetitivi con script di poche righe; un sviluppatore web può costruire API RESTful complete con Django o FastAPI; un data engineer può orchestrare pipeline di dati con pandas e Apache Airflow; un ricercatore può implementare modelli di Machine Learning con scikit-learn, TensorFlow o PyTorch. Questa trasversalità significa che le competenze acquisite sono immediatamente spendibili in contesti diversi.

- **Ecosistema sterminato**: Il Python Package Index (PyPI) ospita oltre 500.000 pacchetti, coprendo praticamente ogni necessità immaginabile. Dalla crittografia alla generazione di PDF, dalla manipolazione di immagini alla comunicazione con servizi cloud, esiste quasi certamente una libreria matura e ben documentata pronta all'uso.

- **Curva di apprendimento favorevole**: La sintassi di Python è pulita, intuitiva e priva del rumore sintattico che caratterizza molti altri linguaggi. L'indentazione obbligatoria forza una struttura visiva coerente. Questo non significa che Python sia un linguaggio "semplice" in senso riduttivo: sotto la superficie accessibile si celano meccanismi sofisticati come metaclassi, descriptor, protocolli asincroni e un sistema di tipi sempre più espressivo.

- **Domanda di mercato**: Python si colloca stabilmente tra i primi tre linguaggi negli indici TIOBE e Stack Overflow Developer Survey. La domanda di sviluppatori Python è particolarmente forte nei settori del cloud computing, dell'automazione infrastrutturale, della data science e dello sviluppo backend.

- **Comunità e supporto**: La comunità Python è tra le più attive e accoglienti nel panorama della programmazione. La documentazione ufficiale è un modello di chiarezza, e risorse come Real Python, Python Weekly e innumerevoli conferenze (PyCon, EuroPython) garantiscono un aggiornamento costante.

### Focus su Python 3.x (3.10+)

Questo percorso di studio si concentra esclusivamente su Python 3, con particolare attenzione alle funzionalità introdotte nelle versioni 3.10 e successive. Tra le novità più significative delle versioni recenti:

- **Structural Pattern Matching** (`match`/`case`) introdotto in Python 3.10, che porta nel linguaggio un potente meccanismo di pattern matching simile a quello di linguaggi funzionali.
- **Miglioramenti ai messaggi di errore** (3.10+), con traceback più descrittivi e suggerimenti contestuali.
- **Union types con la sintassi `X | Y`** (3.10) nei type hint, più leggibile rispetto a `Union[X, Y]`.
- **`ExceptionGroup` e `except*`** (3.11) per la gestione di eccezioni multiple concorrenti.
- **Miglioramenti significativi alle prestazioni** (3.11 e 3.12), con il progetto Faster CPython che ha portato accelerazioni misurabili.
- **Sintassi migliorata per i type parameter** (3.12), con la nuova sintassi `type` statement e i generics semplificati.
- **Rimozione progressiva del GIL** (sperimentale da 3.13), che apre scenari di vero parallelismo multi-thread.

Consigliamo di installare Python 3.12 o superiore per sfruttare tutte le funzionalità trattate in questo percorso.

---

## Piano di Studio

Il percorso è organizzato in 6 fasi progressive, distribuite su circa 16 settimane. Ogni fase fa riferimento alle cartelle numerate (01-30) presenti in questo repository, ciascuna contenente materiale didattico, esercizi ed esempi pratici. Le tempistiche sono indicative e vanno adattate al proprio ritmo di apprendimento e alle conoscenze pregresse.

### Fase 1: Fondamenti (settimane 1-3)

Questa fase costruisce le basi solide su cui poggia tutto il resto del percorso. Anche chi ha esperienza con altri linguaggi dovrebbe dedicare tempo sufficiente per assimilare le peculiarità e le convenzioni proprie di Python.

**`01-FONDAMENTI-LINGUAGGIO`** — Si parte dalla sintassi di base: variabili e tipi primitivi (`int`, `float`, `str`, `bool`, `None`), operatori, strutture di controllo (`if`/`elif`/`else`, cicli `for` e `while`), funzioni con argomenti posizionali, keyword, default e variabili (`*args`, `**kwargs`). Si affrontano le strutture dati fondamentali — liste, tuple, dizionari, set — con le relative operazioni e i metodi più usati. Si introduce il concetto di *comprehension* (list, dict, set comprehension) e le f-string per la formattazione. Vengono trattati moduli, pacchetti e il sistema di import. Si esplora il flusso di esecuzione, lo scope delle variabili (regola LEGB) e la gestione di base delle eccezioni con `try`/`except`.

**`02-OOP`** — Programmazione orientata agli oggetti in Python: classi e istanze, attributi di classe e di istanza, metodi (`self`), ereditarietà singola e multipla, Method Resolution Order (MRO), polimorfismo e incapsulamento. Si studiano le classi astratte (ABC), le property, i metodi `classmethod` e `staticmethod`, i metodi speciali (dunder methods come `__init__`, `__repr__`, `__str__`, `__eq__`, `__hash__`, `__lt__`), il protocollo iteratore (`__iter__`, `__next__`), l'overloading degli operatori e la composizione vs ereditarietà. Attenzione particolare va dedicata alle `dataclass`, introdotte in Python 3.7 e diventate uno strumento imprescindibile per la creazione di classi che contengono principalmente dati.

**`03-STRUTTURE-DATI-AVANZATE`** — Si va oltre le strutture dati di base per esplorare `collections` (`namedtuple`, `defaultdict`, `Counter`, `OrderedDict`, `deque`, `ChainMap`), il modulo `itertools` (prodotti cartesiani, combinazioni, permutazioni, catene, accumulate), `functools` (`lru_cache`, `partial`, `reduce`, `wraps`, `total_ordering`) e le strutture dati del modulo `heapq` e `bisect`. Si affrontano le complessità algoritmiche delle operazioni sulle strutture dati Python e si impara a scegliere la struttura più appropriata per ogni caso d'uso.

### Fase 2: Tecniche Avanzate (settimane 4-5)

Con le basi consolidate, si esplorano i meccanismi avanzati che distinguono il codice Python professionale da quello amatoriale.

**`04-DECORATORI-GENERATORI-CONTEXT-MANAGER`** — I decoratori: funzioni come oggetti di prima classe, closure, decoratori semplici e parametrici, decoratori di classe, `functools.wraps`. I generatori: la keyword `yield`, espressioni generatrici, `yield from`, generatori come coroutine leggere, pipeline di generatori per l'elaborazione lazy di grandi volumi di dati. I context manager: il protocollo `__enter__`/`__exit__`, `contextlib.contextmanager`, context manager asincroni, uso idiomatico con il costrutto `with`.

**`05-GESTIONE-FILE-IO`** — Lettura e scrittura di file di testo e binari, encoding (UTF-8 e oltre), il modulo `pathlib` come alternativa moderna a `os.path`, gestione di file CSV con il modulo `csv`, parsing e generazione di JSON (`json`), manipolazione di file XML (`xml.etree.ElementTree`), file YAML (`PyYAML`), file TOML (supporto nativo da Python 3.11), operazioni sul filesystem (`shutil`, `tempfile`, `glob`), e serializzazione con `pickle` (con le relative considerazioni di sicurezza).

**`06-REGEX-E-TEXT-PROCESSING`** — Il modulo `re`: sintassi delle espressioni regolari, gruppi di cattura, lookahead e lookbehind, flag (`re.IGNORECASE`, `re.MULTILINE`, `re.DOTALL`), metodi `search`, `match`, `findall`, `finditer`, `sub`, `split`. Pattern comuni per la validazione (email, URL, codice fiscale). Elaborazione di testo: il modulo `string`, manipolazione avanzata di stringhe, parsing di formati strutturati, tokenizzazione, normalizzazione Unicode.

**`07-ERROR-HANDLING-E-LOGGING`** — Filosofia EAFP (Easier to Ask Forgiveness than Permission) vs LBYL (Look Before You Leap). Gerarchia delle eccezioni built-in, eccezioni personalizzate, chaining di eccezioni (`raise ... from ...`), `ExceptionGroup` (Python 3.11+). Il modulo `logging`: livelli di log, handler, formatter, configurazione avanzata tramite `dictConfig`, rotating file handler, logging strutturato. Best practice per la gestione degli errori in applicazioni di produzione, uso di `warnings` e strategie di monitoraggio.

### Fase 3: Qualità del Codice (settimane 6-7)

Il codice che funziona non è sufficiente: deve essere testabile, manutenibile, leggibile e robusto. Questa fase è dedicata agli strumenti e alle pratiche che elevano la qualità del software.

**`08-TESTING`** — Il framework `pytest`: test function, fixture, parametrize, marker, plugin. Il modulo `unittest` della libreria standard. Mocking con `unittest.mock` (`patch`, `MagicMock`, `side_effect`). Coverage con `pytest-cov`. Test-Driven Development (TDD): ciclo red-green-refactor. Test di integrazione e test end-to-end. Property-based testing con Hypothesis. Organizzazione dei test nel progetto, strategie di naming, test di regressione.

**`09-TYPE-HINTS-E-MYPY`** — Il sistema di type hint di Python (PEP 484, PEP 526, PEP 544, PEP 612, PEP 695): annotazioni di base, tipi generici, `Optional`, `Union`, `Literal`, `TypeAlias`, `TypeVar`, `ParamSpec`, `Protocol` per lo structural typing. Uso di `mypy` come type checker statico: configurazione, modalità strict, integrazione con l'IDE. Alternative come `pyright` (usato da Pylance in VS Code). Vantaggi dei type hint: documentazione vivente, autocompletamento potenziato, intercettazione di bug prima dell'esecuzione.

**`21-DESIGN-PATTERNS`** — Pattern di progettazione implementati in modo pythonico: Singleton (e perché spesso in Python si usa il modulo come singleton), Factory, Strategy, Observer, Decorator (il pattern, distinto dal decoratore sintattico di Python), Iterator (già integrato nel linguaggio), Context Manager come pattern, Adapter, Facade, Repository. Anti-pattern da evitare. Come Python rende inutili o trasparenti alcuni pattern classici grazie a funzionalità native come duck typing, first-class function e il protocollo descriptor.

**`22-CLEAN-CODE`** — Principi di codice pulito applicati a Python: PEP 8 come guida di stile, strumenti di formattazione automatica (`black`, `isort`, `autopep8`), linter (`flake8`, `pylint`, `ruff`), principi SOLID adattati a Python, DRY (Don't Repeat Yourself), KISS (Keep It Simple, Stupid). Naming convention in Python (snake_case, UPPER_CASE, PascalCase). Documentazione con docstring (stili Google, NumPy, Sphinx), generazione automatica della documentazione. Refactoring: code smell comuni e come risolverli.

### Fase 4: Programmazione Specializzata (settimane 8-11)

Si entra nei domini applicativi specifici, costruendo competenze verticali in aree ad alta domanda professionale.

**`10-PROGRAMMAZIONE-ASINCRONA`** — Il modello asincrono di Python: event loop, coroutine (`async`/`await`), `asyncio.gather`, `asyncio.create_task`, semafori e lock asincroni. Differenza tra concorrenza e parallelismo. `threading` per operazioni I/O-bound, `multiprocessing` per operazioni CPU-bound, `concurrent.futures` come astrazione unificata. Librerie asincrone: `aiohttp`, `aiofiles`, `asyncpg`. Quando usare (e quando non usare) la programmazione asincrona.

**`11-WEB-FRAMEWORK`** — Panoramica dei principali framework web Python. **Flask**: routing, template Jinja2, blueprint, estensioni. **Django**: architettura MTV, ORM, admin, sistema di autenticazione, middleware, management command. **FastAPI**: type hint come contratto API, validazione automatica con Pydantic, documentazione OpenAPI/Swagger generata automaticamente, supporto nativo async, dependency injection. Confronto tra i framework e criteri di scelta.

**`12-DATABASE`** — Interazione con database relazionali: il DB-API 2.0 (PEP 249), `sqlite3` della libreria standard, driver per PostgreSQL (`psycopg2`/`psycopg3`) e MySQL (`mysql-connector-python`). ORM con **SQLAlchemy** 2.0: Core vs ORM, sessioni, query, relazioni, migrazioni con Alembic. Database NoSQL: `pymongo` per MongoDB, `redis-py` per Redis. Connessioni pool, transazioni, pattern Repository, best practice per la sicurezza (SQL injection prevention).

**`13-REST-API`** — Progettazione e implementazione di API RESTful: principi REST, codici di stato HTTP, verbi HTTP, versionamento delle API. Implementazione con FastAPI e Flask-RESTful. Autenticazione e autorizzazione: API key, JWT (JSON Web Tokens), OAuth 2.0. Serializzazione e validazione dei dati. Documentazione con OpenAPI/Swagger. Rate limiting, paginazione, HATEOAS. Consumo di API esterne con `requests` e `httpx`. Testing delle API con `pytest` e client di test.

**`14-DATA-PROCESSING`** — Elaborazione dati con Python: **pandas** per la manipolazione tabellare (DataFrame, Series, operazioni di merge/join/groupby, pivot table, gestione dei valori mancanti). **NumPy** per il calcolo numerico (array n-dimensionali, broadcasting, operazioni vettorizzate). Visualizzazione con **matplotlib** e **seaborn**. Lettura di dati da fonti eterogenee (CSV, Excel, SQL, API, Parquet). Pipeline di data cleaning e trasformazione. Introduzione a **Polars** come alternativa ad alte prestazioni a pandas.

### Fase 5: Applicazioni Pratiche (settimane 12-14)

Questa fase traduce le conoscenze teoriche in applicazioni concrete, affrontando scenari reali che un professionista IT incontra quotidianamente.

**`15-WEB-SCRAPING`** — Estrazione di dati dal web: `requests` per il download di pagine, **Beautiful Soup** per il parsing HTML, `lxml` per il parsing XML/HTML ad alte prestazioni. **Selenium** e **Playwright** per lo scraping di contenuti generati dinamicamente via JavaScript. Framework completi come **Scrapy** per il crawling su larga scala. Gestione di sessioni, cookie, header personalizzati, proxy, rate limiting e rispetto del `robots.txt`. Aspetti legali ed etici del web scraping.

**`16-AUTOMAZIONE`** — Automazione di task di sistema e flussi di lavoro: il modulo `subprocess` per l'esecuzione di comandi esterni, `os` e `shutil` per operazioni sul filesystem, `schedule` e `APScheduler` per la pianificazione di task, automazione di fogli Excel con `openpyxl`, generazione di PDF con `reportlab` e `WeasyPrint`, invio di email con `smtplib` e `email`, interazione con servizi cloud (AWS con `boto3`, Google Cloud con le relative librerie client). Script di automazione per il provisioning e la configurazione di server.

**`17-NETWORK-PROGRAMMING`** — Programmazione di rete: socket TCP e UDP, il modulo `socket`, client e server di base, protocolli applicativi. Librerie di alto livello: `paramiko` per SSH, `ftplib` per FTP, `smtplib`/`imaplib` per email. Network scanning e monitoring con `scapy`. SNMP con `pysnmp`. Programmazione di rete asincrona con `asyncio`. Serializzazione efficiente per la comunicazione di rete: Protocol Buffers, MessagePack.

**`18-SICUREZZA`** — Sicurezza nelle applicazioni Python: il modulo `hashlib` per hashing (SHA-256, bcrypt per le password), `secrets` per la generazione di valori casuali crittograficamente sicuri, crittografia simmetrica e asimmetrica con `cryptography`. Vulnerabilità comuni (injection, XSS, CSRF) e contromisure. Gestione sicura delle credenziali (variabili d'ambiente, vault). Auditing delle dipendenze con `pip-audit` e `safety`. OWASP Top 10 applicato a Python.

**`19-CLI-TOOLS`** — Creazione di strumenti a riga di comando professionali: `argparse` della libreria standard, **Click** per CLI dichiarative ed eleganti, **Typer** (basato su Click e type hint) per CLI con minimo boilerplate. Output formattato con **Rich** (tabelle, progress bar, syntax highlighting, markdown nel terminale). Gestione della configurazione con file `.ini`, `.yaml`, `.toml`, variabili d'ambiente. Distribuzione degli strumenti CLI come pacchetti installabili.

**`20-GUI`** — Interfacce grafiche desktop con Python: **tkinter** come libreria standard (widget, layout manager, eventi, dialog), **PyQt6**/**PySide6** per applicazioni desktop professionali (signal/slot, Qt Designer, widget personalizzati), **Kivy** per applicazioni multi-piattaforma e touch. Pattern Model-View-Controller (MVC) nelle applicazioni GUI. Threading e operazioni asincrone nell'interfaccia grafica per mantenere la reattività.

### Fase 6: Produzione e Deploy (settimane 15-16)

L'ultima fase porta il codice dal laptop alla produzione, coprendo packaging, deploy, ottimizzazione e argomenti specialistici.

**`23-PACKAGING-DISTRIBUZIONE`** — Preparazione del progetto per la distribuzione: struttura standard di un progetto Python, `pyproject.toml` come file di configurazione unificato (PEP 621), `setup.cfg` e `setup.py` (legacy), build backend (`setuptools`, `hatchling`, `flit`). Creazione di wheel e sdist. Pubblicazione su PyPI e su repository privati. Versionamento semantico (SemVer). Entry point per script e plugin.

**`24-VIRTUAL-ENVIRONMENTS`** — Isolamento degli ambienti: `venv` (libreria standard), `virtualenv`, **pipenv** (Pipfile/Pipfile.lock), **Poetry** (pyproject.toml, lock file, gestione delle dipendenze basata su risolutore). Gestione di versioni multiple di Python con **pyenv**. Confronto tra gli strumenti e guida alla scelta. `pip freeze` vs lock file. Strategie per la riproducibilità degli ambienti. Introduzione a **uv** come tool moderno e veloce per la gestione di ambienti e pacchetti.

**`25-PERFORMANCE`** — Ottimizzazione delle prestazioni: profiling con `cProfile`, `line_profiler` e `memory_profiler`. Identificazione dei colli di bottiglia. Strategie di ottimizzazione: algoritmi e strutture dati appropriati, caching (`functools.lru_cache`, `functools.cache`), lazy evaluation, generatori per dati grandi, operazioni vettorizzate con NumPy. Accelerazione con **Cython**, **Numba** (compilazione JIT), `ctypes` e `cffi` per l'interfacciamento con librerie C. Benchmarking con `timeit`.

**`26-DOCKER-PER-PYTHON`** — Containerizzazione delle applicazioni Python: scrittura di Dockerfile ottimizzati (multi-stage build, immagini slim, layer caching, utente non-root). Docker Compose per ambienti multi-servizio (applicazione + database + cache). Gestione delle dipendenze nel container. Volume per dati persistenti e codice in sviluppo. Variabili d'ambiente e configurazione. Healthcheck. Ottimizzazione della dimensione dell'immagine. Integrazione con registri container (Docker Hub, GitHub Container Registry, AWS ECR).

**`27-CI-CD-PER-PYTHON`** — Pipeline di Continuous Integration e Continuous Delivery: **GitHub Actions** (workflow, job, step, matrix strategy per test su versioni Python multiple), **GitLab CI/CD** (`.gitlab-ci.yml`, stage, runner). Automazione di linting, testing, type checking, security audit e deploy. Pubblicazione automatica su PyPI. Deploy su piattaforme cloud (Heroku, AWS Lambda, Google Cloud Run). Semantic release e changelog automatico.

**`28-MACHINE-LEARNING-INTRO`** — Introduzione al Machine Learning con Python: concetti fondamentali (supervised vs unsupervised learning, training/test split, overfitting/underfitting, cross-validation). **scikit-learn**: preprocessing, modelli di classificazione e regressione, metriche di valutazione, pipeline. Visualizzazione dei risultati. Cenni su deep learning con **TensorFlow**/**Keras** e **PyTorch**. L'ecosistema ML: Jupyter notebook, MLflow per il tracking degli esperimenti, concetti di MLOps.

**`29-PYDANTIC-E-VALIDAZIONE`** — Validazione e serializzazione dei dati con **Pydantic** v2: modelli (`BaseModel`), validatori (`field_validator`, `model_validator`), serializzazione JSON, integrazione con FastAPI, configurazione dei modelli, tipi personalizzati. Confronto con alternative: `attrs`, `marshmallow`, `cerberus`. Settings management con `pydantic-settings`. Pattern per la validazione dei dati in ingresso e in uscita nelle applicazioni di produzione.

**`30-TROUBLESHOOTING-E-GUIDE-PRATICHE`** — Strategie di debugging e risoluzione dei problemi: `pdb` e `breakpoint()`, debugging nell'IDE, logging strategico, traceback analysis. Errori comuni in Python e come risolverli. Post-mortem debugging. Analisi dei memory leak con `tracemalloc` e `objgraph`. Performance troubleshooting. Guide pratiche per scenari reali: deployment su server Linux, gestione di processi long-running con `supervisord` e `systemd`, monitoraggio con Prometheus e Grafana.

---

## Ambiente di Laboratorio

La configurazione dell'ambiente di sviluppo è un prerequisito fondamentale per un percorso di studio efficace. Un ambiente ben configurato riduce le frizioni, permette di concentrarsi sul codice e introduce fin da subito pratiche professionali.

### Installazione di Python 3.12+

Si consiglia di utilizzare **pyenv** per la gestione di versioni multiple di Python. pyenv permette di installare, disinstallare e passare tra versioni diverse senza interferire con il Python di sistema.

```bash
# Installazione di pyenv su Linux/macOS
curl https://pyenv.run | bash

# Installazione di Python 3.12
pyenv install 3.12.7
pyenv global 3.12.7

# Verifica
python --version
```

Su Windows, è possibile usare **pyenv-win** oppure scaricare l'installer ufficiale dal sito python.org, assicurandosi di selezionare "Add Python to PATH" durante l'installazione.

### Configurazione dell'IDE

**Visual Studio Code** è l'editor consigliato per la sua leggerezza, estensibilità e supporto eccellente per Python. Estensioni fondamentali:

- **Python** (Microsoft) — IntelliSense, debugging, linting, formattazione
- **Pylance** — Language server avanzato con type checking (basato su pyright)
- **Python Debugger** — Debugging integrato con supporto per breakpoint condizionali
- **Ruff** — Linter e formatter ultraveloce, scritto in Rust, che sostituisce flake8 + isort + black
- **autoDocstring** — Generazione automatica di docstring
- **Jupyter** — Supporto per notebook interattivi direttamente nell'editor
- **GitLens** — Visualizzazione avanzata della cronologia Git

Configurazione consigliata per `settings.json`:

```json
{
  "python.defaultInterpreterPath": "~/.pyenv/versions/3.12.7/bin/python",
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": "explicit"
    }
  },
  "python.analysis.typeCheckingMode": "basic"
}
```

**PyCharm** (JetBrains) è un'alternativa potente, particolarmente apprezzata per progetti di grandi dimensioni. La Community Edition (gratuita) include refactoring avanzato, debugger grafico, test runner integrato e supporto nativo per venv. La Professional Edition aggiunge supporto per framework web, database, Docker e profiling.

### Virtual Environment

L'uso di ambienti virtuali è una pratica non negoziabile nello sviluppo Python professionale. Ogni progetto deve avere il proprio ambiente isolato.

```bash
# Creazione con venv (libreria standard)
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Con Poetry (consigliato per progetti complessi)
pip install poetry
poetry init
poetry add requests pandas

# Con uv (alternativa moderna e velocissima)
pip install uv
uv venv
uv pip install requests pandas
```

### Gestione dei Pacchetti con pip

```bash
# Installazione di pacchetti
pip install nome-pacchetto
pip install nome-pacchetto==1.2.3  # versione specifica
pip install -r requirements.txt    # da file di requisiti

# Generazione del requirements.txt
pip freeze > requirements.txt

# Aggiornamento
pip install --upgrade nome-pacchetto
pip list --outdated
```

### Jupyter Notebook

Jupyter è uno strumento fondamentale per la sperimentazione interattiva, l'esplorazione di dati, la prototipazione rapida e la documentazione del processo di analisi.

```bash
pip install jupyterlab
jupyter lab
```

Si può anche utilizzare Jupyter direttamente in VS Code tramite l'estensione dedicata, che offre un'esperienza integrata con IntelliSense e debugging disponibili anche nelle celle del notebook.

### Integrazione con Git

Git è indispensabile per il versionamento del codice. Si consiglia di configurare un file `.gitignore` appropriato per Python fin dall'inizio di ogni progetto (escludendo `.venv/`, `__pycache__/`, `*.pyc`, `.mypy_cache/`, `.pytest_cache/`, `dist/`, `*.egg-info/`). L'uso di **pre-commit** permette di eseguire automaticamente linting, formattazione e type checking prima di ogni commit:

```bash
pip install pre-commit
# Configurare .pre-commit-config.yaml con hook per ruff, mypy, ecc.
pre-commit install
```

---

## Glossario

| Termine | Definizione |
|---------|------------|
| **Interpreter** | Il programma che esegue il codice Python. L'interprete legge il sorgente, lo compila in bytecode e lo esegue sulla Python Virtual Machine (PVM). |
| **CPython** | L'implementazione di riferimento dell'interprete Python, scritta in C. È quella scaricata dal sito ufficiale python.org. |
| **PyPy** | Implementazione alternativa di Python con un compilatore JIT (Just-In-Time) che può offrire prestazioni significativamente superiori a CPython per codice CPU-bound. |
| **PEP** | Python Enhancement Proposal. Documento di design che descrive nuove funzionalità, processi o linee guida per Python. Ogni PEP ha un numero identificativo univoco. |
| **PEP 8** | La guida di stile ufficiale per il codice Python. Definisce convenzioni su indentazione, naming, spaziatura, lunghezza delle righe e organizzazione del codice. |
| **PEP 484** | Il PEP che ha introdotto i type hint in Python 3.5, definendo la sintassi per le annotazioni di tipo delle funzioni e delle variabili. |
| **GIL** | Global Interpreter Lock. Meccanismo di CPython che garantisce che un solo thread alla volta esegua bytecode Python, limitando il parallelismo reale nei programmi multi-thread CPU-bound. |
| **Bytecode** | Il codice intermedio (file `.pyc`) generato dalla compilazione del sorgente Python. Viene eseguito dalla Python Virtual Machine. |
| **`__init__`** | Metodo speciale (dunder) che funge da inizializzatore di un'istanza di classe. Viene invocato automaticamente dopo la creazione dell'oggetto. |
| **`__main__`** | Nome speciale assegnato al modulo di livello superiore (entry point) di un programma Python. Il costrutto `if __name__ == "__main__":` permette di distinguere tra esecuzione diretta e import. |
| **Dunder** | Abbreviazione di "double underscore". Si riferisce ai metodi e attributi speciali delimitati da doppio underscore (es. `__init__`, `__repr__`, `__len__`). |
| **Decorator** | Funzione che prende un'altra funzione (o classe) come argomento e ne restituisce una versione modificata o arricchita, usando la sintassi `@decorator`. |
| **Generator** | Funzione che usa `yield` per produrre una sequenza di valori in modo lazy, un elemento alla volta, senza caricare l'intera sequenza in memoria. |
| **Iterator** | Oggetto che implementa il protocollo iteratore (`__iter__` e `__next__`), permettendo di attraversare una sequenza di elementi uno alla volta. |
| **Context Manager** | Oggetto che definisce un contesto di esecuzione tramite i metodi `__enter__` e `__exit__`, usato con il costrutto `with` per gestire risorse in modo sicuro. |
| **Comprehension** | Sintassi concisa per creare liste (`[x for x in ...]`), dizionari (`{k: v for ...}`), set (`{x for x in ...}`) e generatori (`(x for x in ...)`) da iterabili. |
| **f-string** | Formatted string literal (da Python 3.6). Stringa prefissata con `f` che permette di incorporare espressioni Python direttamente tra parentesi graffe: `f"Valore: {x}"`. |
| **Walrus Operator** | L'operatore `:=` (Python 3.8+) che permette di assegnare un valore a una variabile all'interno di un'espressione: `if (n := len(a)) > 10:`. |
| **Type Hint** | Annotazione di tipo opzionale che documenta il tipo atteso di variabili, parametri e valori di ritorno, usata da tool di analisi statica come mypy e pyright. |
| **Duck Typing** | Filosofia per cui il tipo di un oggetto è meno importante dei metodi e degli attributi che espone: "Se cammina come un'anatra e starnazza come un'anatra, allora è un'anatra". |
| **EAFP** | Easier to Ask Forgiveness than Permission. Stile pythonico che preferisce tentare un'operazione e gestire eventuali eccezioni, piuttosto che verificare preventivamente le condizioni. |
| **LBYL** | Look Before You Leap. Stile opposto all'EAFP, che prevede la verifica esplicita delle precondizioni prima di eseguire un'operazione. |
| **Metaclass** | La "classe di una classe". Controlla la creazione delle classi stesse, permettendo di personalizzare il comportamento della definizione di classe (es. `type` è la metaclasse predefinita). |
| **Mixin** | Classe progettata per fornire funzionalità aggiuntive ad altre classi tramite ereditarietà multipla, senza essere istanziata direttamente. |
| **ABC** | Abstract Base Class. Classe astratta (dal modulo `abc`) che definisce un'interfaccia che le sottoclassi devono implementare, impedendo l'istanziazione diretta della classe astratta. |
| **Dataclass** | Decoratore `@dataclass` (modulo `dataclasses`) che genera automaticamente metodi speciali (`__init__`, `__repr__`, `__eq__`, ecc.) per classi che contengono principalmente dati. |
| **Enum** | Classe base (modulo `enum`) per creare insiemi di costanti simboliche con nome. Supporta `IntEnum`, `StrEnum`, `Flag` e `auto()`. |
| **Slot** | L'attributo `__slots__` di una classe che limita gli attributi consentiti, eliminando il `__dict__` dell'istanza con conseguente risparmio di memoria e accesso più veloce. |
| **Descriptor** | Oggetto che definisce uno o più dei metodi `__get__`, `__set__`, `__delete__`, permettendo di personalizzare l'accesso agli attributi. Le property sono un esempio di descriptor. |
| **Property** | Decoratore `@property` che permette di definire metodi accessibili come attributi, fornendo getter, setter e deleter con sintassi pulita. |
| **classmethod** | Decoratore `@classmethod` che definisce un metodo che riceve la classe (non l'istanza) come primo argomento (`cls`), utile per factory method e operazioni a livello di classe. |
| **staticmethod** | Decoratore `@staticmethod` che definisce un metodo che non riceve né l'istanza né la classe come argomento, funzionando come una funzione regolare nel namespace della classe. |
| **Lambda** | Funzione anonima definita con la keyword `lambda`, limitata a una singola espressione: `lambda x, y: x + y`. Utile come argomento di funzioni di ordine superiore. |
| **Closure** | Funzione che "cattura" e ricorda le variabili dall'ambiente in cui è stata definita, anche dopo che tale ambiente non è più attivo. Meccanismo alla base dei decoratori. |
| **Coroutine** | Funzione definita con `async def` che può sospendere la propria esecuzione con `await`, permettendo ad altre coroutine di procedere. Fondamento della programmazione asincrona. |
| **asyncio** | Modulo della libreria standard per la programmazione asincrona, che fornisce l'event loop, primitive di sincronizzazione, API per I/O di rete e subprocess asincroni. |
| **Event Loop** | Il ciclo degli eventi: componente centrale di asyncio che orchestra l'esecuzione delle coroutine, gestisce i callback e coordina le operazioni di I/O asincrone. |
| **pip** | Il package installer di Python. Strumento da riga di comando per installare, aggiornare e rimuovere pacchetti dal Python Package Index (PyPI) e da altre sorgenti. |
| **venv** | Modulo della libreria standard per la creazione di ambienti virtuali Python isolati, ciascuno con il proprio interprete e insieme di pacchetti installati. |
| **Wheel** | Formato di distribuzione binaria precompilata (file `.whl`) per pacchetti Python. Più veloce da installare rispetto a sdist perché non richiede compilazione. |
| **sdist** | Source distribution. Archivio contenente il codice sorgente di un pacchetto Python, che potrebbe richiedere compilazione durante l'installazione. |
| **pyproject.toml** | File di configurazione unificato (PEP 518, PEP 621) per i progetti Python. Sostituisce `setup.py`, `setup.cfg`, e centralizza la configurazione di build system, metadati e strumenti. |

---

## Certificazioni Rilevanti

Le certificazioni Python, rilasciate dal Python Institute (OpenEDG), rappresentano un percorso strutturato per validare le proprie competenze e sono riconosciute a livello internazionale.

### PCEP — Certified Entry-Level Python Programmer

- **Livello**: Base
- **Destinatari**: Principianti e studenti che vogliono dimostrare la conoscenza dei fondamenti di Python
- **Argomenti principali**: Tipi di dato fondamentali, operatori, strutture di controllo, strutture dati di base (liste, tuple, dizionari), funzioni, gestione delle eccezioni di base, concetti elementari di OOP
- **Formato**: 30 domande, 45 minuti, soglia di superamento al 70%
- **Costo**: Circa 59 USD
- **Preparazione**: La Fase 1 del nostro piano di studio copre ampiamente il syllabus di questa certificazione

### PCAP — Certified Associate in Python Programming

- **Livello**: Intermedio
- **Destinatari**: Programmatori che vogliono certificare competenze professionali in Python
- **Argomenti principali**: OOP avanzata (ereditarietà, polimorfismo, incapsulamento, metodi speciali), moduli e pacchetti, gestione delle eccezioni avanzata, generatori, iteratori, list comprehension, lambda, closure, operazioni su file, il modulo `os`
- **Formato**: 40 domande, 65 minuti, soglia di superamento al 70%
- **Costo**: Circa 295 USD
- **Preparazione**: Le Fasi 1-2 del nostro piano di studio forniscono una copertura completa

### PCPP1 e PCPP2 — Certified Professional in Python Programming

- **Livello**: Avanzato (Livello 1 e Livello 2)
- **Destinatari**: Sviluppatori professionisti che vogliono certificare competenze esperte
- **PCPP1 — Argomenti principali**: OOP avanzata (metaclassi, decoratori avanzati, ABC), best practice di codifica e design pattern, programmazione di rete (socket), accesso ai database (DB-API 2.0, SQLite), operazioni su file avanzate (XML, CSV, JSON, logging), programmazione GUI con tkinter
- **PCPP2 — Argomenti principali**: Creazione e distribuzione di pacchetti, design pattern avanzati, comunicazione interprocesso, programmazione di rete avanzata, standard e best practice Python, testing
- **Formato**: 45 domande, 65 minuti ciascuno, soglia di superamento al 70%
- **Costo**: Circa 195 USD ciascuno
- **Preparazione**: L'intero percorso di studio (Fasi 1-6) prepara adeguatamente per entrambe le certificazioni

### Suggerimento strategico

Si consiglia di affrontare le certificazioni in ordine progressivo: PCEP come primo traguardo per consolidare la fiducia, PCAP come obiettivo intermedio, e PCPP1/PCPP2 come validazione delle competenze professionali avanzate. Per ogni certificazione, è fondamentale esercitarsi con domande pratiche in stile esame, disponibili sul sito del Python Institute e su piattaforme dedicate.

---

## Risorse Consigliate

### Libri

- **"Fluent Python" (2a edizione) — Luciano Ramalho**: Il testo di riferimento per comprendere le meccaniche profonde di Python. Copre data model, funzioni come oggetti, decoratori, closure, generatori, coroutine, metaclassi e molto altro. Essenziale per chiunque voglia padroneggiare il linguaggio.
- **"Python Crash Course" (3a edizione) — Eric Matthes**: Eccellente per chi inizia. Copre i fondamenti e include tre progetti pratici (gioco, visualizzazione dati, applicazione web).
- **"Effective Python" (2a edizione) — Brett Slatkin**: 90 consigli pratici per scrivere codice Python migliore. Ogni suggerimento è autocontenuto e immediatamente applicabile.
- **"Architecture Patterns with Python" — Harry Percival e Bob Gregory**: Patterns per applicazioni Python scalabili e manutenibili: Repository, Unit of Work, CQRS, Event-Driven Architecture.
- **"Robust Python" — Patrick Viafore**: Dedicato alla creazione di codice Python robusto attraverso type hint, dataclass, enum e strumenti di analisi statica.
- **"Python Distilled" — David Beazley**: Guida concisa e autorevole al linguaggio, scritta da uno dei maggiori esperti mondiali di Python.
- **"Test-Driven Development with Python" — Harry Percival**: Guida pratica al TDD con Python, usando Django come framework di riferimento.

### Siti Web e Documentazione

- **docs.python.org**: La documentazione ufficiale è un modello di chiarezza e completezza. Il tutorial ufficiale, la libreria standard e il Language Reference sono risorse imprescindibili.
- **Real Python** (realpython.com): Tutorial approfonditi, articoli e corsi video di alta qualità, curati da professionisti Python.
- **Python Weekly** (pythonweekly.com): Newsletter settimanale con le ultime notizie, articoli, tutorial e librerie dall'ecosistema Python.
- **PyPI** (pypi.org): Il Python Package Index, repository ufficiale dei pacchetti Python.
- **Awesome Python** (github.com/vinta/awesome-python): Lista curata di framework, librerie, software e risorse Python, organizzata per categoria.
- **PEP Index** (peps.python.org): L'elenco completo delle Python Enhancement Proposal, fondamentale per comprendere l'evoluzione del linguaggio.

### Canali YouTube

- **Corey Schafer**: Tutorial Python chiari e ben strutturati, dai fondamenti ai concetti avanzati. Serie eccellenti su OOP, decoratori, generatori e strumenti di sviluppo.
- **ArjanCodes**: Contenuti focalizzati su design pattern, architettura software e best practice in Python. Ideale per chi vuole scrivere codice professionale.
- **mCoding (James Murphy)**: Approfondimenti tecnici su aspetti sottili e avanzati di Python, con spiegazioni precise e dettagliate.
- **Tech With Tim**: Tutorial pratici su progetti Python, GUI, web development e game development.
- **Sebastiaan Mathot**: Video eccellenti su aspetti specifici e spesso trascurati del linguaggio Python.

### Piattaforme di Pratica

- **LeetCode** (leetcode.com): Problemi di algoritmica e strutture dati, fondamentali per i colloqui tecnici e per affinare il pensiero algoritmico.
- **HackerRank** (hackerrank.com): Sfide di programmazione organizzate per dominio (Python, algoritmi, SQL, regex). Ha un track dedicato specificamente a Python.
- **Exercism** (exercism.org): Esercizi con mentoring. Il track Python offre esercizi progressivi con feedback da mentor volontari.
- **Codewars** (codewars.com): Kata di programmazione con livelli di difficoltà crescente e soluzioni della community per confrontare i propri approcci.
- **Project Euler** (projecteuler.net): Problemi matematico-computazionali che richiedono soluzioni algoritmiche efficienti. Eccellente per sviluppare il pensiero analitico.
- **Advent of Code** (adventofcode.com): Sfide di programmazione annuali (dicembre), con problemi giornalieri di difficoltà crescente. Comunità attivissima e problemi creativi.

### Conferenze e Community

- **PyCon US / PyCon Italia**: Le conferenze Python di riferimento, con talk registrati disponibili gratuitamente su YouTube.
- **EuroPython**: La conferenza Python europea, con contenuti tecnici di alto livello.
- **Python Italia** (python.it): La community italiana di Python, con eventi, meetup e risorse in lingua italiana.
- **Python Discord**: Server Discord con canali dedicati a ogni livello e argomento, ottimo per chiedere aiuto e confrontarsi.

---

*Questo documento serve come mappa di orientamento per l'intero percorso di studio sulla programmazione Python. Ogni cartella numerata (01-30) contiene materiale specifico con approfondimenti, esempi di codice ed esercizi pratici. Si consiglia di seguire l'ordine proposto, adattando i tempi al proprio ritmo, e di affiancare sempre lo studio teorico con la pratica costante al terminale.*
