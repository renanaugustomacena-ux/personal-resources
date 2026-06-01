---
corso: Programmazione Python
fase: 1 — Fondamenti
modulo: "05"
versione: Python 3.12+
livello: intermedio
prerequisiti:
  - completamento modulo 01 (fondamenti-linguaggio)
  - conoscenza base dei tipi built-in (str, bytes, list, dict)
  - familiarità con i context manager (with statement)
obiettivi:
  - padroneggiare pathlib.Path per la manipolazione idiomatica dei percorsi
  - leggere e scrivere file di testo e binari con gestione corretta dell'encoding
  - elaborare formati strutturati (JSON, CSV, TOML, YAML, XML) con la libreria standard
  - implementare pattern di scrittura atomica con file temporanei
  - gestire compressione e archiviazione (gzip, zip, tar) in modo sicuro
  - applicare la serializzazione consapevole dei rischi (pickle vs JSON vs msgpack)
  - monitorare il filesystem con watchdog e inotify
tag:
  - file-io
  - pathlib
  - json
  - csv
  - toml
  - serializzazione
  - filesystem
---

# Gestione File e I/O — Guida Completa

> **Modulo 05** · **Aggiornamento:** 2026-05-24

> **Modulo del corso:** Programmazione Python
> **Prerequisiti:** [01-fondamenti-linguaggio.md](01-fondamenti-linguaggio.md)
> **Obiettivi di apprendimento:**
> 1. Padroneggiare pathlib.Path per manipolazione idiomatica dei percorsi
> 2. Leggere e scrivere file di testo e binari con gestione corretta dell'encoding
> 3. Elaborare formati strutturati (JSON, CSV, TOML, YAML, XML) con la libreria standard
> 4. Implementare pattern di scrittura atomica con file temporanei
> 5. Gestire compressione e archiviazione (gzip, zip, tar) in modo sicuro
> 6. Applicare serializzazione consapevole dei rischi (pickle vs JSON vs msgpack)
> 7. Monitorare il filesystem con watchdog e inotify
> **Tempo stimato:** lettura 50 min · lab 90 min
> **Livello:** intermedio
> **Ultimo aggiornamento:** 2026-05-24

## Idee guida
1. **`pathlib.Path` > `os.path` per modern code.**
2. **`with open(...)` always; auto-close.**
3. **`encoding='utf-8'` explicit; default platform-dependent.**
4. **`tempfile.NamedTemporaryFile` per atomic write pattern.**


## Indice

1. [Panoramica](#panoramica)
2. [pathlib — Il Modulo Moderno](#pathlib--il-modulo-moderno)
3. [Lettura e Scrittura File](#lettura-e-scrittura-file)
4. [Formati Strutturati](#formati-strutturati)
5. [File Temporanei](#file-temporanei)
6. [Compressione e Archivi](#compressione-e-archivi)
7. [Operazioni su Filesystem](#operazioni-su-filesystem)
8. [Serializzazione](#serializzazione)
9. [Watch e Monitoring](#watch-e-monitoring)
10. [File Locking — Accesso Concorrente ai File](#file-locking--accesso-concorrente-ai-file)
11. [Scrittura Atomica dei File](#scrittura-atomica-dei-file)
12. [Permessi e Sicurezza dei File](#permessi-e-sicurezza-dei-file)
13. [Async File I/O](#async-file-io)
14. [Monitoring Avanzato del Filesystem](#monitoring-avanzato-del-filesystem)
15. [Compressione Avanzata](#compressione-avanzata)
16. [shutil Avanzato](#shutil-avanzato)
17. [os.scandir — Performance nella Scansione di Directory](#osscandir--performance-nella-scansione-di-directory)
18. [configparser Avanzato](#configparser-avanzato)
19. [Elaborazione File di Grandi Dimensioni — Pattern Avanzati](#elaborazione-file-di-grandi-dimensioni--pattern-avanzati)
20. [Gestione degli Errori di I/O](#gestione-degli-errori-di-io)
21. [Best Practices](#best-practices)

---

## Panoramica

La gestione dei file e delle operazioni di input/output rappresenta una delle competenze fondamentali per qualsiasi programmatore Python. Ogni applicazione non banale interagisce con il filesystem: legge configurazioni, scrive log, elabora dati strutturati, gestisce risorse temporanee. Python offre un ecosistema ricco e stratificato per queste operazioni, dal modulo legacy `os.path` fino al moderno `pathlib`, dai formati di testo semplice ai formati strutturati come JSON, CSV, YAML, TOML e XML.

Storicamente, le operazioni su file in Python si basavano sui moduli `os` e `os.path`, che esponevano un'interfaccia procedurale ispirata alle system call POSIX. Con Python 3.4 e stato introdotto `pathlib` (PEP 428), che offre un'astrazione orientata agli oggetti per la manipolazione dei percorsi. Oggi `pathlib` rappresenta l'approccio raccomandato e idiomatico: rende il codice piu leggibile, piu portabile tra sistemi operativi e meno soggetto a errori legati alla concatenazione manuale delle stringhe.

Questa guida copre l'intero spettro delle operazioni su file: dalla costruzione dei percorsi alla lettura e scrittura, dalla gestione dei formati strutturati alla compressione, dalla serializzazione al monitoring in tempo reale. Ogni sezione include esempi pratici pronti per l'uso in contesti professionali.

Il modello di I/O di Python si basa su alcuni principi fondamentali. Primo, i file sono trattati come **stream** (flussi): sequenze di byte (modalita binaria) o caratteri (modalita testo) che possono essere letti o scritti in modo sequenziale o con accesso casuale. Secondo, Python adotta il paradigma **RAII** (Resource Acquisition Is Initialization) attraverso i context manager, garantendo che le risorse vengano rilasciate in modo deterministico. Terzo, la libreria standard offre un'astrazione stratificata: operazioni di basso livello nel modulo `os`, manipolazione dei percorsi in `pathlib`, e formati strutturati in moduli dedicati come `json`, `csv`, `xml`. Questa stratificazione permette di scegliere il livello di astrazione appropriato per ogni caso d'uso, dalla manipolazione diretta dei file descriptor fino alla serializzazione automatica di strutture dati complesse.

---

## pathlib — Il Modulo Moderno

Il modulo `pathlib`, introdotto in Python 3.4 e progressivamente arricchito nelle versioni successive, rappresenta il modo idiomatico per lavorare con i percorsi del filesystem in Python moderno. Offre una gerarchia di classi che incapsulano le operazioni sui percorsi in un'interfaccia orientata agli oggetti, eliminando la necessita di manipolare stringhe grezze.

### Path Objects

La classe principale e `Path`, che costruisce automaticamente l'oggetto appropriato in base al sistema operativo corrente:

```python
from pathlib import Path

# Su Linux/macOS crea un PosixPath, su Windows un WindowsPath
p = Path("/home/utente/documenti/report.txt")
print(type(p))  # <class 'pathlib.PosixPath'> (su Linux)
```

La gerarchia delle classi e la seguente:

- **PurePath** — classe base astratta per la manipolazione pura dei percorsi (senza accesso al filesystem)
  - **PurePosixPath** — percorsi in stile POSIX (separatore `/`)
  - **PureWindowsPath** — percorsi in stile Windows (separatore `\`)
- **Path** — sottoclasse concreta di PurePath con accesso reale al filesystem
  - **PosixPath** — operazioni concrete su sistemi POSIX
  - **WindowsPath** — operazioni concrete su sistemi Windows

Le classi `Pure*` sono utili quando si devono manipolare percorsi di un sistema diverso da quello corrente, ad esempio per elaborare percorsi Windows su una macchina Linux:

```python
from pathlib import PurePosixPath, PureWindowsPath

# Manipolazione di percorsi Windows su Linux
wp = PureWindowsPath(r"C:\Users\renan\Documents\file.txt")
print(wp.name)    # file.txt
print(wp.parent)  # C:\Users\renan\Documents

# Manipolazione di percorsi POSIX
pp = PurePosixPath("/var/log/syslog")
print(pp.parts)   # ('/', 'var', 'log', 'syslog')
```

#### Costruzione e Concatenazione

`Path` accetta segmenti multipli e li unisce automaticamente con il separatore corretto. L'operatore `/` (overloading di `__truediv__`) permette una sintassi elegante per la concatenazione:

```python
from pathlib import Path

# Costruzione diretta
base = Path("/home/utente")

# Concatenazione con l'operatore /
config = base / "config" / "app.toml"
print(config)  # /home/utente/config/app.toml

# Equivalente con argomenti multipli
config2 = Path("/home", "utente", "config", "app.toml")
print(config2)  # /home/utente/config/app.toml

# Percorso relativo alla directory corrente
progetto = Path.cwd() / "src" / "main.py"

# Percorso dalla home dell'utente
documento = Path.home() / "Documenti" / "nota.txt"
```

#### Proprieta del Percorso

Ogni oggetto `Path` espone proprieta utili per accedere ai componenti del percorso senza parsing manuale delle stringhe:

```python
from pathlib import Path

p = Path("/home/utente/progetti/app/src/main.py")

p.name       # 'main.py'        — nome completo del file
p.stem       # 'main'           — nome senza estensione
p.suffix     # '.py'            — estensione (con il punto)
p.suffixes   # ['.py']          — lista di tutte le estensioni
p.parent     # Path('/home/utente/progetti/app/src')
p.parents    # sequenza di tutti i genitori fino alla root
p.parts      # ('/', 'home', 'utente', 'progetti', 'app', 'src', 'main.py')
p.anchor     # '/'              — radice del percorso
p.root       # '/'              — componente root

# Iterare sui genitori
for genitore in p.parents:
    print(genitore)
# /home/utente/progetti/app/src
# /home/utente/progetti/app
# /home/utente/progetti
# /home/utente
# /home
# /

# File con estensioni multiple
archivio = Path("dati.tar.gz")
archivio.suffix    # '.gz'
archivio.suffixes  # ['.tar', '.gz']
archivio.stem      # 'dati.tar'
```

#### Metodi di Verifica

`Path` offre metodi per interrogare lo stato effettivo del filesystem:

```python
from pathlib import Path

p = Path("/etc/hostname")

p.exists()      # True se il percorso esiste
p.is_file()     # True se e un file regolare
p.is_dir()      # True se e una directory
p.is_symlink()  # True se e un link simbolico
p.is_mount()    # True se e un mount point
p.is_socket()   # True se e un socket Unix
p.is_fifo()     # True se e una named pipe
p.is_block_device()  # True se e un dispositivo a blocchi
p.is_char_device()   # True se e un dispositivo a caratteri

# Risoluzione del percorso
p.resolve()     # percorso assoluto canonico (risolve symlink e ..)
p.absolute()    # percorso assoluto (non risolve symlink)

# Informazioni sul file
stat = p.stat()
stat.st_size     # dimensione in byte
stat.st_mtime    # timestamp ultima modifica
stat.st_mode     # permessi

# Proprietario (solo POSIX)
p.owner()        # nome utente proprietario
p.group()        # nome gruppo proprietario
```

### Operazioni su File

`pathlib` integra direttamente le operazioni di lettura e scrittura piu comuni, eliminando la necessita di aprire e chiudere esplicitamente i file per operazioni semplici:

```python
from pathlib import Path

file = Path("esempio.txt")

# Scrittura e lettura di testo
file.write_text("Contenuto del file\nSeconda riga", encoding="utf-8")
contenuto = file.read_text(encoding="utf-8")

# Scrittura e lettura di byte
file_bin = Path("dati.bin")
file_bin.write_bytes(b"\x00\x01\x02\x03")
dati = file_bin.read_bytes()

# Apertura con context manager (per operazioni piu complesse)
with file.open("r", encoding="utf-8") as f:
    for riga in f:
        print(riga.strip())

# Apertura in modalita append
with file.open("a", encoding="utf-8") as f:
    f.write("\nTerza riga aggiunta")
```

Metodi per la gestione del ciclo di vita dei file:

```python
from pathlib import Path

file = Path("nuovo_file.txt")

# Creazione di un file vuoto (come il comando touch)
file.touch()                # crea se non esiste, aggiorna timestamp se esiste
file.touch(exist_ok=False)  # solleva FileExistsError se il file esiste gia

# Rinominare
nuovo = file.rename("rinominato.txt")  # restituisce il nuovo Path

# Sostituire (sovrascrive la destinazione se esiste)
altro = Path("altro.txt")
altro.write_text("contenuto")
file2 = Path("rinominato.txt")
file2.replace("altro.txt")  # sovrascrive altro.txt

# Eliminare
Path("altro.txt").unlink()               # elimina il file
Path("inesistente.txt").unlink(missing_ok=True)  # non solleva errore se manca

# Creare un link simbolico
link = Path("collegamento.txt")
link.symlink_to("/percorso/originale.txt")

# Creare un hard link
hard = Path("hard_link.txt")
hard.hardlink_to("/percorso/originale.txt")  # Python 3.10+
```

### Operazioni su Directory

Le operazioni sulle directory sono altrettanto intuitive:

```python
from pathlib import Path

cartella = Path("progetto/src/moduli")

# Creazione directory
cartella.mkdir()                        # crea la directory (il genitore deve esistere)
cartella.mkdir(parents=True)            # crea anche le directory intermedie
cartella.mkdir(parents=True, exist_ok=True)  # nessun errore se esiste gia

# Rimozione directory (deve essere vuota)
Path("progetto/src/moduli").rmdir()

# Elenco contenuti
for elemento in Path("/etc").iterdir():
    if elemento.is_file():
        print(f"File: {elemento.name}")
    elif elemento.is_dir():
        print(f"Dir:  {elemento.name}")
```

#### glob() e rglob()

I metodi `glob()` e `rglob()` permettono di cercare file con pattern matching, utilizzando la sintassi glob standard:

```python
from pathlib import Path

progetto = Path("/home/utente/progetto")

# Tutti i file Python nella directory corrente
for py in progetto.glob("*.py"):
    print(py)

# Tutti i file Python ricorsivamente (sottodirectory incluse)
for py in progetto.rglob("*.py"):
    print(py)

# Pattern piu complessi
progetto.glob("src/**/*.py")     # file .py in src e sottodirectory
progetto.glob("test_*.py")       # file che iniziano con test_
progetto.glob("**/config.*")     # file config.* a qualsiasi profondita
progetto.glob("[a-z]*.txt")      # file .txt che iniziano con lettera minuscola

# Combinazione con list comprehension
file_grandi = [
    f for f in progetto.rglob("*.log")
    if f.stat().st_size > 1_000_000  # file piu grandi di 1 MB
]
```

### pathlib Avanzato — PurePath, Symlink e Glob Patterns

#### PurePath in Profondita

Le classi `PurePath`, `PurePosixPath` e `PureWindowsPath` sono fondamentali quando si devono manipolare percorsi senza accedere al filesystem sottostante. Questo e particolarmente utile in scenari di cross-platform development, strumenti di build, sistemi di CI/CD e test unitari:

```python
from pathlib import PurePosixPath, PureWindowsPath, PurePath

# Conversione tra stili di percorso
win_path = PureWindowsPath(r"C:\Users\renan\Documents\progetto\src\main.py")
posix_equivalent = PurePosixPath(*win_path.parts[1:])  # rimuove il drive
print(posix_equivalent)  # Users/renan/Documents/progetto/src/main.py

# Operatori di confronto — PurePath supporta confronti lessicografici
p1 = PurePosixPath("/home/a")
p2 = PurePosixPath("/home/b")
print(p1 < p2)  # True

# match() — verifica se il percorso corrisponde a un pattern glob
p = PurePosixPath("/home/utente/progetti/app/src/main.py")
p.match("*.py")           # True — match sul nome del file
p.match("src/*.py")       # True — match sugli ultimi due componenti
p.match("progetti/**/*.py")  # True — match ricorsivo (Python 3.12+)

# PurePath e immutabile e hashabile — puo essere usato come chiave di dizionario
percorsi_visti = {}
p = PurePosixPath("/var/log/app.log")
percorsi_visti[p] = "ultimo accesso: 2026-05-24"

# Parsing di URI e URL in percorsi
from urllib.parse import urlparse
url = "file:///home/utente/documenti/report.pdf"
parsed = urlparse(url)
percorso = PurePosixPath(parsed.path)
print(percorso.name)  # report.pdf

# Costruzione cross-platform di percorsi per configurazione
import sys
if sys.platform == "win32":
    base = PureWindowsPath("C:/ProgramData/MyApp")
else:
    base = PurePosixPath("/etc/myapp")
config_path = base / "config.toml"
```

#### Risoluzione dei Symlink

La distinzione tra `resolve()`, `absolute()` e `readlink()` e critica per la sicurezza e la correttezza del codice:

```python
from pathlib import Path

# Scenario: /tmp/link -> /home/utente/dati/file.txt
link = Path("/tmp/link")

# resolve() — percorso canonico assoluto, risolve TUTTI i symlink e i '..'
canonico = link.resolve()  # /home/utente/dati/file.txt
# resolve(strict=True) — solleva FileNotFoundError se il percorso non esiste
try:
    inesistente = Path("/tmp/non_esiste").resolve(strict=True)
except FileNotFoundError:
    print("Il percorso non esiste")

# absolute() — percorso assoluto senza risolvere i symlink
assoluto = link.absolute()  # /tmp/link (il symlink resta)

# readlink() — legge il target del symlink (Python 3.9+)
target = link.readlink()  # /home/utente/dati/file.txt

# Catena di symlink: link1 -> link2 -> file.txt
# resolve() segue l'intera catena fino al file reale
# readlink() legge solo il primo livello

# SICUREZZA: verificare che un percorso non esca da una directory consentita
def percorso_sicuro(percorso: Path, directory_base: Path) -> bool:
    """Verifica che il percorso risolto sia all'interno della directory base."""
    try:
        risolto = percorso.resolve(strict=True)
        base_risolta = directory_base.resolve(strict=True)
        risolto.relative_to(base_risolta)
        return True
    except (FileNotFoundError, ValueError):
        return False

# Esempio: prevenzione path traversal
upload_dir = Path("/var/app/uploads")
file_utente = upload_dir / "../../etc/passwd"  # tentativo di path traversal
print(percorso_sicuro(file_utente, upload_dir))  # False

# is_symlink() vs exists() — comportamento con symlink rotti
link_rotto = Path("/tmp/link_rotto")  # punta a un file che non esiste piu
# link_rotto.exists()     -> False (il target non esiste)
# link_rotto.is_symlink() -> True  (il link stesso esiste)
# link_rotto.lstat()      -> funziona (stat del link, non del target)
```

#### Glob Patterns Avanzati

I metodi `glob()` e `rglob()` supportano pattern piu sofisticati rispetto al semplice wildcard:

```python
from pathlib import Path

progetto = Path("/home/utente/progetto")

# Pattern con classi di caratteri
progetto.glob("[A-Z]*.py")         # file Python che iniziano con maiuscola
progetto.glob("test_[0-9]*.py")    # test numerati: test_01.py, test_123.py
progetto.glob("[!_]*.py")          # file che NON iniziano con underscore

# Pattern con alternative (Python 3.13+)
# Prima di 3.13, usare fnmatch per pattern piu complessi
progetto.glob("*.{py,pyi}")       # file .py e .pyi (Python 3.13+)

# Combinazione con filtri programmatici per versioni precedenti
import fnmatch
tutti_i_file = list(progetto.rglob("*"))
sorgenti = [
    f for f in tutti_i_file
    if fnmatch.fnmatch(f.name, "*.py") or fnmatch.fnmatch(f.name, "*.pyi")
]

# walk() — Python 3.12+ alternativa a os.walk basata su Path
for dirpath, dirnames, filenames in progetto.walk():
    # dirpath e un oggetto Path
    # dirnames e filenames sono liste di stringhe
    print(f"Directory: {dirpath}")
    for nome in filenames:
        file_path = dirpath / nome
        print(f"  File: {file_path} ({file_path.stat().st_size} byte)")

    # Esclusione di directory dalla ricorsione (modifica in-place)
    dirnames[:] = [d for d in dirnames if d not in {".git", "__pycache__", ".venv"}]

# Performance: glob() restituisce un generatore — e lazy
# Ma per directory molto grandi, os.scandir() puo essere piu veloce
# (vedi sezione dedicata a os.scandir)

# Contare file per estensione in un progetto
from collections import Counter
estensioni = Counter(
    f.suffix.lower()
    for f in progetto.rglob("*")
    if f.is_file() and f.suffix
)
for ext, count in estensioni.most_common(10):
    print(f"{ext}: {count} file")
```

### Path Manipulation

Metodi per trasformare un percorso creandone di nuovi basati su quello esistente:

```python
from pathlib import Path

p = Path("/home/utente/report.txt")

# Cambiare il nome del file
p.with_name("analisi.txt")      # /home/utente/analisi.txt

# Cambiare l'estensione
p.with_suffix(".md")            # /home/utente/report.md
p.with_suffix("")               # /home/utente/report (rimuove estensione)

# Cambiare lo stem (Python 3.9+)
p.with_stem("riepilogo")        # /home/utente/riepilogo.txt

# Percorso relativo
assoluto = Path("/home/utente/progetti/app/main.py")
relativo = assoluto.relative_to("/home/utente")
print(relativo)                 # progetti/app/main.py

# Verifica se un percorso e relativo a un altro (Python 3.9+)
assoluto.is_relative_to("/home/utente")     # True
assoluto.is_relative_to("/var")             # False
```

---

## Lettura e Scrittura File

Oltre ai metodi rapidi di `pathlib`, Python offre la funzione built-in `open()` per un controllo completo sulle operazioni di I/O. La combinazione di `open()` con il costrutto `with` (context manager) garantisce la corretta chiusura del file anche in caso di eccezioni.

### File di Testo

#### Apertura e Encoding

L'encoding corretto e cruciale per evitare errori di decodifica. A partire da Python 3.15 l'encoding predefinito diventa UTF-8 (PEP 686), ma e buona pratica specificarlo esplicitamente per compatibilita con versioni precedenti:

```python
# Apertura in lettura con encoding esplicito
with open("documento.txt", "r", encoding="utf-8") as f:
    contenuto = f.read()

# Le modalita principali:
# "r"  — lettura testo (default)
# "w"  — scrittura testo (sovrascrive)
# "a"  — append testo (aggiunge in coda)
# "x"  — creazione esclusiva (errore se il file esiste)
# "r+" — lettura e scrittura
```

#### Metodi di Lettura

```python
with open("dati.txt", "r", encoding="utf-8") as f:
    # Leggere tutto il contenuto in una stringa
    tutto = f.read()

with open("dati.txt", "r", encoding="utf-8") as f:
    # Leggere al massimo N caratteri
    chunk = f.read(1024)

with open("dati.txt", "r", encoding="utf-8") as f:
    # Leggere una singola riga (include il newline)
    prima_riga = f.readline()
    seconda_riga = f.readline()

with open("dati.txt", "r", encoding="utf-8") as f:
    # Leggere tutte le righe in una lista
    righe = f.readlines()
    # ['Prima riga\n', 'Seconda riga\n', 'Terza riga\n']

with open("dati.txt", "r", encoding="utf-8") as f:
    # Iterazione riga per riga (il modo piu efficiente in memoria)
    for riga in f:
        riga_pulita = riga.rstrip("\n")
        print(riga_pulita)
```

#### Metodi di Scrittura

```python
# Scrittura — sovrascrive il contenuto esistente
with open("output.txt", "w", encoding="utf-8") as f:
    f.write("Prima riga\n")
    f.write("Seconda riga\n")

# writelines() — scrive un iterabile di stringhe (NON aggiunge newline)
righe = ["Riga 1\n", "Riga 2\n", "Riga 3\n"]
with open("output.txt", "w", encoding="utf-8") as f:
    f.writelines(righe)

# Append — aggiunge alla fine del file
with open("log.txt", "a", encoding="utf-8") as f:
    f.write("Nuovo evento registrato\n")

# print() verso file
with open("report.txt", "w", encoding="utf-8") as f:
    print("Titolo del Report", file=f)
    print("=" * 40, file=f)
    print(f"Risultato: {42}", file=f)
```

#### Gestione degli Errori di Encoding

Il parametro `errors` di `open()` controlla il comportamento in caso di caratteri non decodificabili:

```python
# strict (default) — solleva UnicodeDecodeError
with open("file.txt", "r", encoding="utf-8", errors="strict") as f:
    contenuto = f.read()

# ignore — ignora i caratteri non decodificabili
with open("file.txt", "r", encoding="utf-8", errors="ignore") as f:
    contenuto = f.read()

# replace — sostituisce con il carattere di sostituzione Unicode
with open("file.txt", "r", encoding="utf-8", errors="replace") as f:
    contenuto = f.read()

# surrogateescape — utile per gestire nomi di file con encoding misto
with open("file.txt", "r", encoding="utf-8", errors="surrogateescape") as f:
    contenuto = f.read()

# backslashreplace — sostituisce con escape sequences Python
with open("file.txt", "r", encoding="utf-8", errors="backslashreplace") as f:
    contenuto = f.read()
```

#### Il Context Manager (with statement)

Il costrutto `with` assicura che il file venga chiuso automaticamente, anche se si verifica un'eccezione all'interno del blocco. Senza `with`, un'eccezione potrebbe lasciare il file aperto, causando perdita di dati o esaurimento dei file descriptor:

```python
# CORRETTO — il file viene sempre chiuso
with open("file.txt", "r", encoding="utf-8") as f:
    contenuto = f.read()
# Qui f e gia chiuso

# SCONSIGLIATO — richiede gestione manuale della chiusura
f = open("file.txt", "r", encoding="utf-8")
try:
    contenuto = f.read()
finally:
    f.close()

# Apertura multipla simultanea
with (
    open("input.txt", "r", encoding="utf-8") as ingresso,
    open("output.txt", "w", encoding="utf-8") as uscita,
):
    for riga in ingresso:
        uscita.write(riga.upper())
```

### File Binari

Le modalita binarie (`rb`, `wb`, `ab`) lavorano con oggetti `bytes` anziche stringhe, senza alcuna trasformazione di encoding o newline:

```python
# Lettura binaria
with open("immagine.png", "rb") as f:
    intestazione = f.read(8)  # primi 8 byte (signature PNG)
    print(intestazione)       # b'\x89PNG\r\n\x1a\n'

# Scrittura binaria
dati = bytes(range(256))
with open("dati.bin", "wb") as f:
    f.write(dati)

# Navigazione nel file (seek/tell)
with open("dati.bin", "rb") as f:
    f.seek(100)           # posiziona il cursore al byte 100
    posizione = f.tell()  # restituisce la posizione corrente (100)
    chunk = f.read(10)    # legge 10 byte dalla posizione corrente
```

#### Il Modulo struct

Il modulo `struct` permette di leggere e scrivere dati binari strutturati, interpretando sequenze di byte secondo formati specifici:

```python
import struct

# Scrivere dati binari strutturati
# 'I' = unsigned int (4 byte), 'f' = float (4 byte), '10s' = stringa 10 byte
record = struct.pack("If10s", 42, 3.14, b"ciao      ")
with open("record.bin", "wb") as f:
    f.write(record)

# Leggere dati binari strutturati
with open("record.bin", "rb") as f:
    dati = f.read(struct.calcsize("If10s"))
    numero, decimale, testo = struct.unpack("If10s", dati)
    print(f"{numero}, {decimale:.2f}, {testo.strip()}")
    # 42, 3.14, b'ciao'
```

#### Formati di Stringa struct e Byte Order

Il modulo `struct` utilizza stringhe di formato che specificano il layout dei dati binari. Il primo carattere della stringa controlla il byte order e l'allineamento:

```python
import struct

# Byte order e allineamento
# '@' — nativo (byte order e allineamento del sistema)
# '=' — nativo byte order, nessun allineamento
# '<' — little-endian
# '>' — big-endian (network byte order)
# '!' — network byte order (= big-endian)

# Esempio: protocollo di rete con header fisso
# Header: magic (4 byte), versione (2 byte), lunghezza payload (4 byte)
HEADER_FORMAT = "!4sHI"  # network byte order: 4s + unsigned short + unsigned int
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)  # 10 byte

def crea_pacchetto(versione: int, payload: bytes) -> bytes:
    header = struct.pack(HEADER_FORMAT, b"PROT", versione, len(payload))
    return header + payload

def leggi_pacchetto(dati: bytes) -> tuple:
    magic, versione, lunghezza = struct.unpack(HEADER_FORMAT, dati[:HEADER_SIZE])
    payload = dati[HEADER_SIZE:HEADER_SIZE + lunghezza]
    return magic, versione, payload

pacchetto = crea_pacchetto(1, b"Hello World")
magic, ver, payload = leggi_pacchetto(pacchetto)
print(f"Versione {ver}, Payload: {payload}")  # Versione 1, Payload: b'Hello World'

# iter_unpack — deserializzazione iterativa di record ripetuti
# Utile per file con record a lunghezza fissa
RECORD_FMT = "<Iff"  # little-endian: uint32 + float + float
record_size = struct.calcsize(RECORD_FMT)

with open("sensori.bin", "rb") as f:
    dati = f.read()

for timestamp, temperatura, umidita in struct.iter_unpack(RECORD_FMT, dati):
    print(f"t={timestamp}: {temperatura:.1f}°C, {umidita:.1f}%")
```

#### io.BytesIO e io.StringIO — Stream in Memoria

I moduli `io.BytesIO` e `io.StringIO` forniscono buffer in memoria con la stessa interfaccia degli oggetti file. Sono fondamentali per il testing, la costruzione di dati binari in memoria e l'interazione con API che accettano oggetti file-like:

```python
import io

# BytesIO — buffer binario in memoria
buffer = io.BytesIO()
buffer.write(b"Prima parte dei dati\n")
buffer.write(b"Seconda parte dei dati\n")

# Ottenere tutto il contenuto
contenuto = buffer.getvalue()  # non modifica la posizione del cursore
print(len(contenuto))  # 42

# Riposizionare e leggere
buffer.seek(0)
prima_riga = buffer.readline()  # b'Prima parte dei dati\n'

# Inizializzare con dati esistenti
buffer_inizializzato = io.BytesIO(b"\x00\x01\x02\x03\x04")
buffer_inizializzato.seek(2)
print(buffer_inizializzato.read(2))  # b'\x02\x03'

# StringIO — buffer di testo in memoria
testo_buffer = io.StringIO()
testo_buffer.write("Riga 1\n")
testo_buffer.write("Riga 2\n")
print(testo_buffer.getvalue())

# Uso con librerie che accettano file-like objects
import csv
csv_output = io.StringIO()
writer = csv.writer(csv_output)
writer.writerow(["nome", "valore"])
writer.writerow(["test", "42"])
csv_string = csv_output.getvalue()

# Costruzione progressiva di dati binari complessi
import struct
pacchetto = io.BytesIO()
# Header
pacchetto.write(struct.pack("!4sH", b"HDR\x00", 1))
# Payload variabile
dati_payload = b"contenuto variabile del messaggio"
pacchetto.write(struct.pack("!I", len(dati_payload)))
pacchetto.write(dati_payload)
# Checksum
import hashlib
pacchetto_bytes = pacchetto.getvalue()
checksum = hashlib.md5(pacchetto_bytes).digest()[:4]
pacchetto.write(checksum)

risultato_finale = pacchetto.getvalue()
print(f"Pacchetto: {len(risultato_finale)} byte")

# BytesIO come sostituto di file per il testing
def processa_file(file_obj):
    """Funzione che accetta un file-like object."""
    return file_obj.read().decode("utf-8").upper()

# In produzione: open("dati.txt", "rb")
# In test:
file_finto = io.BytesIO(b"dati di test")
risultato = processa_file(file_finto)
assert risultato == "DATI DI TEST"
```

### File Grandi

Quando si lavora con file di dimensioni elevate (centinaia di megabyte o gigabyte), caricare l'intero contenuto in memoria con `read()` non e praticabile. Python offre diverse strategie per l'elaborazione efficiente.

#### Lettura Riga per Riga

L'iterazione diretta sull'oggetto file e il modo piu semplice e memory-efficient per elaborare file di testo grandi:

```python
contatore = 0
with open("enorme.log", "r", encoding="utf-8") as f:
    for riga in f:
        if "ERROR" in riga:
            contatore += 1
print(f"Trovati {contatore} errori")
```

#### Lettura a Chunk

Per file binari o quando si necessita di un controllo preciso sulla dimensione dei blocchi letti:

```python
DIMENSIONE_CHUNK = 8192  # 8 KB

def leggi_a_blocchi(percorso, dimensione=DIMENSIONE_CHUNK):
    with open(percorso, "rb") as f:
        while True:
            chunk = f.read(dimensione)
            if not chunk:
                break
            yield chunk

# Calcolo hash di un file grande
import hashlib

def hash_file(percorso):
    h = hashlib.sha256()
    for blocco in leggi_a_blocchi(percorso):
        h.update(blocco)
    return h.hexdigest()
```

#### Elaborazione con Generator

I generator permettono di costruire pipeline di elaborazione memory-efficient:

```python
from pathlib import Path

def leggi_righe(percorso):
    """Generator che produce righe pulite."""
    with open(percorso, "r", encoding="utf-8") as f:
        for riga in f:
            yield riga.strip()

def filtra_non_vuote(righe):
    """Filtra le righe vuote."""
    for riga in righe:
        if riga:
            yield riga

def cerca_pattern(righe, pattern):
    """Filtra le righe che contengono il pattern."""
    for riga in righe:
        if pattern in riga:
            yield riga

# Pipeline di elaborazione — mai piu di una riga in memoria
righe = leggi_righe("server.log")
non_vuote = filtra_non_vuote(righe)
errori = cerca_pattern(non_vuote, "CRITICAL")

for errore in errori:
    print(errore)
```

#### Memory-Mapped Files (mmap)

Il modulo `mmap` permette di mappare un file direttamente nello spazio di indirizzamento del processo, consentendo accesso casuale efficiente a file grandi senza caricarli interamente in memoria:

```python
import mmap

with open("grande.bin", "r+b") as f:
    # Mappa l'intero file in memoria
    with mmap.mmap(f.fileno(), 0) as mm:
        # Accesso casuale come a una sequenza di byte
        primi_100 = mm[:100]

        # Ricerca nel file (molto veloce)
        posizione = mm.find(b"MARKER")
        if posizione != -1:
            mm.seek(posizione)
            dati = mm.read(50)

        # Scrittura diretta nella mappa (modifica il file)
        mm[0:5] = b"NUOVO"
```

#### mmap Avanzato — Pattern e Tecniche

Il modulo `mmap` offre funzionalita ben oltre la semplice lettura sequenziale. Le operazioni di memory-mapping sfruttano il meccanismo di paginazione del sistema operativo: le pagine del file vengono caricate in memoria fisica solo quando effettivamente accedute (lazy loading), e le pagine non usate possono essere scaricate dal kernel per liberare RAM.

```python
import mmap
import re
import struct

# Ricerca con regex su file memory-mapped
# mmap supporta il modulo re direttamente — molto efficiente per file grandi
with open("log_grande.txt", "r+b") as f:
    with mmap.mmap(f.fileno(), 0) as mm:
        # Cerca tutti gli indirizzi IP nel file
        pattern = rb"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"
        for match in re.finditer(pattern, mm):
            print(f"IP trovato a posizione {match.start()}: {match.group().decode()}")

# Mappatura parziale — solo una porzione del file
with open("enorme.bin", "r+b") as f:
    # Mappa solo 1 MB a partire dall'offset 100 MB
    offset = 100 * 1024 * 1024
    lunghezza = 1 * 1024 * 1024
    with mmap.mmap(f.fileno(), lunghezza, offset=offset) as mm:
        dati = mm[:100]  # primi 100 byte della regione mappata

# Mappatura di sola lettura
with open("dati_protetti.bin", "rb") as f:
    with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
        # mm[0] = 65  # -> TypeError: mmap object doesn't support assignment
        contenuto = mm[:]

# Mappatura copy-on-write — modifiche locali che non alterano il file
with open("template.bin", "rb") as f:
    with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_COPY) as mm:
        mm[0:5] = b"MODIF"  # modifica solo la copia in memoria
        # il file originale resta invariato

# Comunicazione inter-processo tramite mmap anonimo (senza file)
# Utile per condividere dati tra processo padre e figlio
import os

dimensione = 1024
mm = mmap.mmap(-1, dimensione)  # -1 = mmap anonimo (non legato a file)
mm.write(b"Messaggio dal processo padre")
mm.seek(0)

pid = os.fork()
if pid == 0:
    # Processo figlio
    messaggio = mm.readline()
    print(f"Figlio ha letto: {messaggio}")
    mm.close()
    os._exit(0)
else:
    os.wait()
    mm.close()

# Lettura di record binari con mmap e struct
RECORD_FMT = "<I32sf"  # id (uint32), nome (32 byte), valore (float)
RECORD_SIZE = struct.calcsize(RECORD_FMT)

with open("database.bin", "r+b") as f:
    with mmap.mmap(f.fileno(), 0) as mm:
        num_record = len(mm) // RECORD_SIZE
        for i in range(num_record):
            offset = i * RECORD_SIZE
            id_rec, nome, valore = struct.unpack_from(RECORD_FMT, mm, offset)
            nome_pulito = nome.rstrip(b"\x00").decode("utf-8")
            print(f"Record {id_rec}: {nome_pulito} = {valore:.2f}")

        # Aggiornamento in-place di un singolo record (molto veloce)
        struct.pack_into("f", mm, 2 * RECORD_SIZE + 36, 99.99)
```

I vantaggi di `mmap` rispetto alla lettura tradizionale: accesso casuale O(1) senza seek espliciti, il kernel gestisce automaticamente la cache delle pagine, possibilita di condividere mappature tra processi, e le modifiche vengono propagate al file in modo efficiente dal sistema operativo. Lo svantaggio principale e che `mmap` non e adatto per file che cambiano dimensione frequentemente, e su sistemi a 32 bit la dimensione della mappatura e limitata dallo spazio di indirizzamento virtuale (~2-3 GB).

---

## Formati Strutturati

Python offre supporto nativo o tramite librerie esterne per tutti i principali formati di dati strutturati.

### JSON

JSON (JavaScript Object Notation) e il formato di scambio dati piu diffuso. Il modulo `json` della libreria standard gestisce serializzazione e deserializzazione:

```python
import json
from pathlib import Path

# Serializzazione (Python -> JSON)
dati = {
    "nome": "Mario Rossi",
    "eta": 35,
    "citta": "Roma",
    "competenze": ["Python", "SQL", "Docker"],
    "attivo": True,
    "indirizzo": None
}

# Scrittura su file
with open("utente.json", "w", encoding="utf-8") as f:
    json.dump(dati, f, indent=2, ensure_ascii=False)

# Serializzazione a stringa
json_str = json.dumps(dati, indent=2, ensure_ascii=False, sort_keys=True)

# Deserializzazione (JSON -> Python)
with open("utente.json", "r", encoding="utf-8") as f:
    dati_letti = json.load(f)

# Deserializzazione da stringa
dati_da_str = json.loads('{"chiave": "valore"}')
```

#### Serializzazione Personalizzata

Tipi come `datetime`, `Decimal` e `set` non sono serializzabili nativamente in JSON. Si possono gestire con un encoder personalizzato:

```python
import json
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path

class EncoderAvanzato(json.JSONEncoder):
    """Encoder che gestisce tipi Python non standard."""
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, set):
            return sorted(list(obj))
        if isinstance(obj, Path):
            return str(obj)
        if isinstance(obj, bytes):
            return obj.decode("utf-8", errors="replace")
        return super().default(obj)

dati = {
    "timestamp": datetime.now(),
    "prezzo": Decimal("19.99"),
    "tag": {"python", "tutorial", "io"},
    "percorso": Path("/home/utente/file.txt"),
}

output = json.dumps(dati, cls=EncoderAvanzato, indent=2, ensure_ascii=False)
print(output)

# Alternativa con il parametro default (piu semplice)
def serializza(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Tipo non serializzabile: {type(obj)}")

json.dumps(dati, default=serializza)
```

### CSV

Il modulo `csv` gestisce file in formato Comma-Separated Values, gestendo correttamente quoting, escaping e diversi dialetti:

```python
import csv

# Scrittura con csv.writer
with open("dipendenti.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Nome", "Ruolo", "Stipendio"])  # intestazione
    writer.writerow(["Anna Bianchi", "Developer", 45000])
    writer.writerow(["Marco Verdi", "Designer", 38000])
    writer.writerows([
        ["Laura Neri", "Manager", 55000],
        ["Paolo Rossi", "DevOps", 48000],
    ])

# Lettura con csv.reader
with open("dipendenti.csv", "r", newline="", encoding="utf-8") as f:
    reader = csv.reader(f)
    intestazione = next(reader)  # salta l'intestazione
    for riga in reader:
        nome, ruolo, stipendio = riga
        print(f"{nome}: {ruolo} ({stipendio} EUR)")
```

#### DictReader e DictWriter

Le varianti basate su dizionari offrono un accesso piu leggibile ai dati:

```python
import csv

# Scrittura con DictWriter
campi = ["nome", "email", "dipartimento"]
dipendenti = [
    {"nome": "Anna", "email": "anna@example.com", "dipartimento": "IT"},
    {"nome": "Marco", "email": "marco@example.com", "dipartimento": "HR"},
]

with open("team.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=campi)
    writer.writeheader()
    writer.writerows(dipendenti)

# Lettura con DictReader
with open("team.csv", "r", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for riga in reader:
        print(f"{riga['nome']} lavora nel dipartimento {riga['dipartimento']}")
```

#### Dialetti e Opzioni di Formattazione

```python
import csv

# Registrare un dialetto personalizzato
csv.register_dialect("europeo",
    delimiter=";",
    quotechar='"',
    quoting=csv.QUOTE_MINIMAL,
    lineterminator="\n"
)

with open("dati_eu.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f, dialect="europeo")
    writer.writerow(["Prodotto", "Prezzo", "Quantita"])
    writer.writerow(["Laptop", "999,99", 15])

# Gestione di file CSV grandi — iterazione lazy
with open("enorme.csv", "r", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for i, riga in enumerate(reader):
        if i >= 1_000_000:
            break
        # elaborazione riga per riga senza caricare tutto in memoria
```

Una nota importante: il parametro `newline=""` nella chiamata a `open()` e obbligatorio quando si usa il modulo `csv`. Senza di esso, Python potrebbe trasformare i caratteri di fine riga in modo incoerente con le aspettative del modulo `csv`, causando righe vuote indesiderate nei file scritti o errori di parsing nella lettura. Su Windows questa precauzione e particolarmente critica a causa della differenza tra `\r\n` e `\n`.

### YAML

YAML (YAML Ain't Markup Language) e un formato leggibile dall'uomo, molto usato per file di configurazione. Richiede la libreria esterna `PyYAML`:

```python
# pip install pyyaml
import yaml

# Lettura sicura (raccomandato — non esegue codice arbitrario)
with open("config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# Scrittura
config = {
    "database": {
        "host": "localhost",
        "porta": 5432,
        "nome": "myapp",
    },
    "logging": {
        "livello": "INFO",
        "file": "/var/log/app.log",
    },
    "features": ["auth", "api", "dashboard"],
}

with open("config.yaml", "w", encoding="utf-8") as f:
    yaml.safe_dump(config, f, default_flow_style=False, allow_unicode=True)

# Documenti YAML multipli (separati da ---)
documenti_yaml = """
---
nome: primo
valore: 1
---
nome: secondo
valore: 2
"""

for doc in yaml.safe_load_all(documenti_yaml):
    print(doc)
# {'nome': 'primo', 'valore': 1}
# {'nome': 'secondo', 'valore': 2}
```

**Attenzione alla sicurezza**: non utilizzare mai `yaml.load()` con il `Loader` predefinito (`FullLoader` o `UnsafeLoader`) su dati provenienti da fonti non fidate. `yaml.safe_load()` e l'unica funzione che dovrebbe essere usata nella stragrande maggioranza dei casi, poiche supporta solo tipi Python nativi e non permette l'esecuzione di costruttori arbitrari. La funzione `yaml.load()` senza specificare `Loader=yaml.SafeLoader` puo portare all'esecuzione di codice malevolo attraverso tag YAML personalizzati come `!!python/object/apply:os.system`.

### TOML

TOML (Tom's Obvious Minimal Language) e il formato scelto per `pyproject.toml` e sta diventando sempre piu popolare per la configurazione. Python 3.11 ha introdotto il modulo `tomllib` nella libreria standard per la lettura:

```python
# Lettura (Python 3.11+ — modulo built-in)
import tomllib

with open("pyproject.toml", "rb") as f:  # NOTA: modalita binaria obbligatoria
    config = tomllib.load(f)

# Lettura da stringa
toml_str = """
[project]
name = "mio-progetto"
version = "1.0.0"
description = "Un progetto Python"

[project.dependencies]
requests = ">=2.28"
"""
config = tomllib.loads(toml_str)
print(config["project"]["name"])  # mio-progetto

# Scrittura (richiede libreria esterna)
# pip install tomli-w
import tomli_w

config = {
    "tool": {
        "mypy": {
            "strict": True,
            "python_version": "3.12",
        }
    }
}

with open("config.toml", "wb") as f:  # modalita binaria
    tomli_w.dump(config, f)
```

### XML

XML rimane importante per integrazioni enterprise, feed RSS/Atom e formati come SVG. Il modulo `xml.etree.ElementTree` della libreria standard copre la maggior parte dei casi d'uso:

```python
import xml.etree.ElementTree as ET

# Parsing di un file XML
tree = ET.parse("catalogo.xml")
root = tree.getroot()

# Parsing da stringa
xml_str = """<?xml version="1.0" encoding="UTF-8"?>
<catalogo>
    <libro isbn="978-0-13-468599-1">
        <titolo>The Pragmatic Programmer</titolo>
        <autore>David Thomas</autore>
        <prezzo valuta="EUR">35.90</prezzo>
    </libro>
    <libro isbn="978-0-596-00712-6">
        <titolo>Head First Design Patterns</titolo>
        <autore>Eric Freeman</autore>
        <prezzo valuta="EUR">42.50</prezzo>
    </libro>
</catalogo>
"""
root = ET.fromstring(xml_str)

# Navigazione con XPath
for libro in root.findall("libro"):
    titolo = libro.find("titolo").text
    autore = libro.find("autore").text
    prezzo = libro.find("prezzo")
    print(f"{titolo} di {autore} — {prezzo.text} {prezzo.get('valuta')}")

# Query XPath piu avanzate
libri_cari = root.findall(".//libro[prezzo]")  # tutti i libri con prezzo
tutti_i_titoli = [e.text for e in root.iter("titolo")]

# Creazione di XML da zero
nuovo_root = ET.Element("persone")
persona = ET.SubElement(nuovo_root, "persona", attrib={"id": "1"})
ET.SubElement(persona, "nome").text = "Giulia"
ET.SubElement(persona, "eta").text = "28"

tree = ET.ElementTree(nuovo_root)
ET.indent(tree, space="  ")  # Python 3.9+ — indentazione leggibile
tree.write("persone.xml", encoding="unicode", xml_declaration=True)
```

Per esigenze avanzate (validazione XSD, XSLT, XPath completo), la libreria `lxml` offre funzionalita molto superiori:

```python
# pip install lxml
from lxml import etree

# Parsing con validazione
parser = etree.XMLParser(remove_blank_text=True)
tree = etree.parse("documento.xml", parser)

# XPath completo
risultati = tree.xpath("//libro[@isbn='978-0-13-468599-1']/titolo/text()")

# Validazione con schema XSD
schema_doc = etree.parse("schema.xsd")
schema = etree.XMLSchema(schema_doc)
documento = etree.parse("documento.xml")
if schema.validate(documento):
    print("Documento valido")
else:
    for errore in schema.error_log:
        print(f"Errore: {errore}")
```

Una considerazione importante sulla sicurezza: il parsing XML e potenzialmente vulnerabile ad attacchi come XML External Entity (XXE) injection e Billion Laughs (espansione esponenziale di entita). Quando si elaborano documenti XML provenienti da fonti non fidate, e consigliabile utilizzare `defusedxml`, una libreria che disabilita le funzionalita pericolose dei parser XML standard:

```python
# pip install defusedxml
import defusedxml.ElementTree as ET

# Parsing sicuro — blocca entita esterne e espansione di entita
tree = ET.parse("documento_non_fidato.xml")
```

### INI/Config

Il modulo `configparser` gestisce file di configurazione in formato INI, ancora utilizzati da molti strumenti e applicazioni:

```python
import configparser

# Creazione e scrittura
config = configparser.ConfigParser()

config["DEFAULT"] = {
    "debug": "false",
    "log_level": "WARNING",
}

config["database"] = {
    "host": "localhost",
    "porta": "5432",
    "nome": "produzione",
    "debug": "true",  # sovrascrive il DEFAULT
}

config["server"] = {
    "host": "0.0.0.0",
    "porta": "8080",
}

with open("app.ini", "w") as f:
    config.write(f)

# Lettura
config = configparser.ConfigParser()
config.read("app.ini")

host_db = config["database"]["host"]           # "localhost"
porta_db = config["database"].getint("porta")  # 5432 (int)
debug = config["database"].getboolean("debug") # True (bool)

# Interpolazione — riferimenti a valori di altre chiavi
config = configparser.ConfigParser(
    interpolation=configparser.BasicInterpolation()
)
config.read_string("""
[paths]
base = /home/utente
data = %(base)s/data
logs = %(base)s/logs
""")
print(config["paths"]["data"])  # /home/utente/data
```

---

## File Temporanei

Il modulo `tempfile` crea file e directory temporanei in modo sicuro, evitando conflitti di nomi e problemi di sicurezza legati alla prevedibilita dei percorsi. I file temporanei vengono creati nella directory temporanea del sistema (`/tmp` su Linux, `%TEMP%` su Windows):

```python
import tempfile
from pathlib import Path

# File temporaneo con nome (accessibile da altri processi)
with tempfile.NamedTemporaryFile(
    mode="w",
    suffix=".json",
    prefix="app_",
    encoding="utf-8",
    delete=True,           # eliminato automaticamente alla chiusura
    delete_on_close=False  # Python 3.12+: non eliminare alla chiusura del file
) as tmp:
    tmp.write('{"chiave": "valore"}')
    tmp.flush()
    print(f"File temporaneo: {tmp.name}")
    # /tmp/app_abc123.json — accessibile durante il blocco with

# Directory temporanea (eliminata automaticamente)
with tempfile.TemporaryDirectory(prefix="progetto_") as tmpdir:
    cartella = Path(tmpdir)
    file_temp = cartella / "dati.txt"
    file_temp.write_text("contenuto temporaneo", encoding="utf-8")
    print(f"Directory: {tmpdir}")
    # tutti i file nella directory vengono eliminati all'uscita dal blocco

# Funzioni di basso livello
fd, percorso = tempfile.mkstemp(suffix=".txt")  # crea file, restituisce descriptor
import os
os.write(fd, b"dati")
os.close(fd)
os.unlink(percorso)  # pulizia manuale necessaria

tmpdir = tempfile.mkdtemp()  # crea directory, restituisce percorso
# pulizia manuale necessaria: shutil.rmtree(tmpdir)

# Ottenere la directory temporanea di sistema
print(tempfile.gettempdir())  # /tmp (Linux) o equivalente
```

### SpooledTemporaryFile

`SpooledTemporaryFile` e un ibrido intelligente: mantiene i dati in memoria (come `BytesIO`/`StringIO`) finche non superano una soglia configurabile, poi trasferisce automaticamente su disco. Ideale per operazioni dove la dimensione dei dati e imprevedibile:

```python
import tempfile

# SpooledTemporaryFile con soglia di 5 MB
with tempfile.SpooledTemporaryFile(
    max_size=5 * 1024 * 1024,  # 5 MB: sotto questa soglia resta in memoria
    mode="w+",
    encoding="utf-8",
    suffix=".csv",
    prefix="elaborazione_",
) as spool:
    # Scrittura — resta in memoria finche < 5 MB
    for i in range(100):
        spool.write(f"riga,{i},dati,esempio\n")

    # Verifica se e in memoria o su disco
    # _rolled e un attributo interno (non documentato ma comunemente usato)

    # rollover() — forza il trasferimento su disco
    spool.rollover()

    # Dopo il rollover, si comporta come un NamedTemporaryFile
    spool.seek(0)
    contenuto = spool.read()
    print(f"Letti {len(contenuto)} caratteri")

# Caso d'uso: upload di file via HTTP con dimensione sconosciuta
import tempfile

def gestisci_upload(stream, max_memoria=10 * 1024 * 1024):
    """Salva un upload in memoria se piccolo, su disco se grande."""
    spool = tempfile.SpooledTemporaryFile(max_size=max_memoria, mode="w+b")
    while True:
        chunk = stream.read(8192)
        if not chunk:
            break
        spool.write(chunk)
    spool.seek(0)
    return spool

# Caso d'uso: elaborazione CSV intermedia
import csv

with tempfile.SpooledTemporaryFile(
    max_size=2 * 1024 * 1024, mode="w+", encoding="utf-8", newline=""
) as tmp:
    writer = csv.writer(tmp)
    writer.writerow(["id", "nome", "valore"])
    for i in range(10000):
        writer.writerow([i, f"item_{i}", i * 1.5])

    tmp.seek(0)
    reader = csv.DictReader(tmp)
    totale = sum(float(r["valore"]) for r in reader)
    print(f"Totale: {totale:.2f}")
```

### Pattern Avanzati con File Temporanei

```python
import tempfile
import os
from pathlib import Path

# Pattern: file temporaneo che sopravvive al context manager
# Utile quando il file deve essere passato a un processo esterno
tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".sql")
try:
    tmp.write(b"SELECT * FROM utenti WHERE attivo = true;\n")
    tmp.flush()
    percorso = tmp.name
    tmp.close()  # chiude il file ma non lo elimina

    # Il file e ora accessibile da altri processi
    print(f"Query salvata in: {percorso}")
    # ... esegui il processo esterno che legge il file ...
finally:
    os.unlink(percorso)  # pulizia manuale obbligatoria

# Pattern: directory temporanea con struttura predefinita
with tempfile.TemporaryDirectory(prefix="workspace_") as workspace:
    ws = Path(workspace)
    (ws / "input").mkdir()
    (ws / "output").mkdir()
    (ws / "logs").mkdir()

    # Popola la struttura
    (ws / "input" / "dati.csv").write_text("a,b,c\n1,2,3\n", encoding="utf-8")

    # Elaborazione nel workspace isolato
    dati = (ws / "input" / "dati.csv").read_text(encoding="utf-8")
    risultato = dati.upper()
    (ws / "output" / "risultato.csv").write_text(risultato, encoding="utf-8")

    # Tutto viene eliminato automaticamente all'uscita dal blocco

# Pattern: personalizzazione della directory temporanea
# Per default usa tempfile.gettempdir(), ma si puo specificare una directory diversa
with tempfile.NamedTemporaryFile(
    dir="/var/app/tmp",     # directory personalizzata
    prefix="sessione_",
    suffix=".dat",
    delete=True
) as tmp:
    tmp.write(b"dati di sessione")
    print(f"File in: {tmp.name}")
    # /var/app/tmp/sessione_xxxx.dat
```

---

## Compressione e Archivi

Python offre supporto completo per i formati di compressione e archiviazione piu diffusi.

### zipfile

Il modulo `zipfile` gestisce file ZIP in modo completo:

```python
import zipfile
from pathlib import Path

# Creazione di un archivio ZIP
with zipfile.ZipFile("archivio.zip", "w", zipfile.ZIP_DEFLATED) as zf:
    # Aggiungere file
    zf.write("documento.txt")
    zf.write("report.pdf", arcname="documenti/report.pdf")  # rinominare dentro l'archivio

    # Aggiungere contenuto direttamente dalla memoria
    zf.writestr("note.txt", "Questo contenuto viene scritto direttamente")

    # Compressione con livello specifico
    zf.write("grande.log", compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)

# Lettura e ispezione
with zipfile.ZipFile("archivio.zip", "r") as zf:
    # Elenco dei contenuti
    zf.printdir()
    nomi = zf.namelist()
    info_lista = zf.infolist()

    for info in info_lista:
        print(f"{info.filename}: {info.file_size} -> {info.compress_size} byte")

    # Leggere un file senza estrarlo
    contenuto = zf.read("note.txt")

    # Estrarre tutto
    zf.extractall("cartella_destinazione")

    # Estrarre un singolo file
    zf.extract("documento.txt", "destinazione/")

# Verifica integrita
with zipfile.ZipFile("archivio.zip", "r") as zf:
    risultato = zf.testzip()  # None se tutto OK, altrimenti nome del primo file corrotto
```

### tarfile

Il modulo `tarfile` gestisce archivi tar, con o senza compressione:

```python
import tarfile

# Creazione di un archivio tar.gz
with tarfile.open("archivio.tar.gz", "w:gz") as tar:
    tar.add("src/", arcname="progetto/src")
    tar.add("README.md", arcname="progetto/README.md")

# Modi di apertura:
# "w"    — tar senza compressione
# "w:gz" — tar con compressione gzip
# "w:bz2"— tar con compressione bzip2
# "w:xz" — tar con compressione lzma/xz

# Lettura e estrazione
with tarfile.open("archivio.tar.gz", "r:gz") as tar:
    # Elenco contenuti
    tar.list()
    nomi = tar.getnames()

    # Estrazione sicura (Python 3.12+ — filtro predefinito)
    tar.extractall("destinazione/", filter="data")

    # Estrarre un singolo membro
    membro = tar.getmember("progetto/README.md")
    tar.extract(membro, "destinazione/", filter="data")

    # Leggere senza estrarre
    f = tar.extractfile("progetto/README.md")
    if f is not None:
        contenuto = f.read()
```

**Nota sulla sicurezza**: a partire da Python 3.12, `extractall()` richiede un filtro per prevenire attacchi di path traversal. Utilizzare sempre `filter="data"` o `filter="tar"` per estrazioni sicure. Il filtro `"data"` e il piu restrittivo: rifiuta percorsi assoluti, componenti `..`, link simbolici che puntano fuori dalla directory di destinazione, e file speciali (dispositivi, pipe). Il filtro `"tar"` e meno restrittivo e permette link simbolici, utile quando si devono preservare le strutture di link dell'archivio originale.

### gzip, bz2, lzma

Questi moduli gestiscono la compressione di singoli file (a differenza di zip/tar che sono formati archivio):

```python
import gzip
import bz2
import lzma

# gzip — compressione/decompressione
with gzip.open("dati.txt.gz", "wt", encoding="utf-8") as f:
    f.write("Dati compressi con gzip\n" * 1000)

with gzip.open("dati.txt.gz", "rt", encoding="utf-8") as f:
    contenuto = f.read()

# bz2 — compressione piu lenta ma rapporto migliore
with bz2.open("dati.txt.bz2", "wt", encoding="utf-8") as f:
    f.write("Dati compressi con bzip2\n" * 1000)

# lzma/xz — compressione massima
with lzma.open("dati.txt.xz", "wt", encoding="utf-8") as f:
    f.write("Dati compressi con lzma\n" * 1000)

# Compressione in memoria (streaming)
dati_originali = b"x" * 100_000
compressi_gz = gzip.compress(dati_originali, compresslevel=9)
decompressi = gzip.decompress(compressi_gz)
print(f"Originale: {len(dati_originali)}, Compresso: {len(compressi_gz)}")
```

La scelta del formato di compressione dipende dal caso d'uso. `gzip` offre il miglior compromesso tra velocita e compressione ed e lo standard de facto per la compressione di dati su web (HTTP Content-Encoding) e per i file `.tar.gz`. `bz2` offre un rapporto di compressione migliore di gzip ma e significativamente piu lento, utile per archiviazione a lungo termine dove la velocita di compressione non e critica. `lzma` (formato `.xz`) offre il rapporto di compressione piu alto tra i tre, ma richiede piu memoria e CPU sia in compressione che in decompressione; e la scelta ideale per la distribuzione di pacchetti software dove la dimensione del download e importante.

---

## Operazioni su Filesystem

### shutil

Il modulo `shutil` (shell utilities) fornisce operazioni di alto livello su file e directory, complementando `pathlib` e `os`:

```python
import shutil
from pathlib import Path

# Copia di file
shutil.copy("sorgente.txt", "destinazione.txt")       # copia contenuto + permessi
shutil.copy2("sorgente.txt", "destinazione.txt")      # copia anche i metadati (timestamp)
shutil.copyfile("sorgente.txt", "destinazione.txt")   # copia solo il contenuto

# Copia di directory (ricorsiva)
shutil.copytree("progetto/", "progetto_backup/")
shutil.copytree(
    "src/",
    "backup_src/",
    ignore=shutil.ignore_patterns("*.pyc", "__pycache__", ".git"),
    dirs_exist_ok=True  # Python 3.8+: non errore se la destinazione esiste
)

# Spostamento (funziona anche tra filesystem diversi)
shutil.move("vecchio_percorso/file.txt", "nuovo_percorso/file.txt")
shutil.move("cartella/", "nuova_posizione/cartella/")

# Eliminazione ricorsiva di directory
shutil.rmtree("directory_da_eliminare/")
shutil.rmtree("forse_non_esiste/", ignore_errors=True)

# Informazioni sul disco
uso = shutil.disk_usage("/")
print(f"Totale: {uso.total / (1024**3):.1f} GB")
print(f"Usato:  {uso.used / (1024**3):.1f} GB")
print(f"Libero: {uso.free / (1024**3):.1f} GB")

# Creazione di archivi compressi
shutil.make_archive(
    "backup",           # nome base dell'archivio (senza estensione)
    "gztar",            # formato: "zip", "tar", "gztar", "bztar", "xztar"
    root_dir="progetto" # directory da archiviare
)
# Crea: backup.tar.gz

# Estrazione di archivi
shutil.unpack_archive("backup.tar.gz", "destinazione/")

# Trovare eseguibili nel PATH
python = shutil.which("python3")
print(python)  # /usr/bin/python3 (o None se non trovato)
```

### Modulo os (Legacy ma Ancora Utile)

Sebbene `pathlib` sia raccomandato per la manipolazione dei percorsi, il modulo `os` rimane indispensabile per alcune operazioni:

```python
import os

# Funzioni su percorsi (prefer pathlib per queste)
os.path.join("home", "utente", "file.txt")  # home/utente/file.txt
os.path.exists("/tmp/file.txt")
os.path.isfile("/tmp/file.txt")
os.path.isdir("/tmp/")
os.path.basename("/home/utente/file.txt")   # file.txt
os.path.dirname("/home/utente/file.txt")    # /home/utente
os.path.splitext("file.tar.gz")             # ('file.tar', '.gz')
os.path.getsize("/tmp/file.txt")            # dimensione in byte
os.path.abspath("relativo.txt")             # percorso assoluto

# os.walk — attraversamento ricorsivo delle directory
for dirpath, dirnames, filenames in os.walk("/home/utente/progetto"):
    # dirpath:  percorso della directory corrente
    # dirnames: lista delle sottodirectory
    # filenames: lista dei file nella directory corrente
    for filename in filenames:
        percorso_completo = os.path.join(dirpath, filename)
        print(percorso_completo)

    # Escludere directory specifiche dalla ricorsione
    dirnames[:] = [d for d in dirnames if d not in (".git", "__pycache__", "node_modules")]

# Variabili d'ambiente
home = os.environ.get("HOME", "/home/default")
os.environ["MIA_VARIABILE"] = "valore"  # imposta per il processo corrente

# Informazioni sul file
stat_info = os.stat("/tmp/file.txt")
print(f"Dimensione: {stat_info.st_size}")
print(f"Ultima modifica: {stat_info.st_mtime}")
print(f"Permessi: {oct(stat_info.st_mode)}")

# Permessi e proprietario
os.chmod("/tmp/file.txt", 0o644)     # cambia permessi
os.chown("/tmp/file.txt", 1000, 1000)  # cambia proprietario/gruppo (richiede root)

# Creazione e rimozione di directory
os.makedirs("a/b/c", exist_ok=True)  # equivalente a mkdir -p
os.removedirs("a/b/c")               # rimuove directory vuote dal basso verso l'alto

# Link simbolici
os.symlink("/percorso/originale", "/percorso/link")
os.readlink("/percorso/link")  # legge il target del link

# Operazioni sulla directory corrente
cwd = os.getcwd()             # directory corrente
os.chdir("/tmp")              # cambia directory (sconsigliato in librerie)
os.listdir("/tmp")            # lista contenuti (preferire Path.iterdir())
```

Un caso d'uso in cui `os.walk` resta superiore a `pathlib.rglob()` e quando si necessita di modificare l'elenco delle sottodirectory durante la traversata. Modificando `dirnames[:]` in-place, si possono escludere intere directory dalla ricorsione, risparmiando tempo su alberi di directory molto grandi con molte sottodirectory da ignorare (come `.git`, `node_modules` o `__pycache__`). Con `pathlib.rglob()` questo tipo di filtraggio deve avvenire dopo l'enumerazione, quando i percorsi sono gia stati visitati.

---

## Serializzazione

La serializzazione e il processo di conversione di oggetti Python in un formato che puo essere salvato su disco o trasmesso in rete, e successivamente ricostruito.

### pickle

Il modulo `pickle` serializza oggetti Python arbitrari in formato binario. E specifico di Python e non interoperabile con altri linguaggi:

```python
import pickle

# Serializzazione su file
dati = {
    "modello": [1.5, 2.3, 0.8, -1.2],
    "parametri": {"learning_rate": 0.001, "epochs": 100},
    "etichette": ["gatto", "cane", "uccello"],
}

with open("modello.pkl", "wb") as f:
    pickle.dump(dati, f, protocol=pickle.HIGHEST_PROTOCOL)

# Deserializzazione
with open("modello.pkl", "rb") as f:
    dati_caricati = pickle.load(f)

# Serializzazione in memoria (bytes)
serializzato = pickle.dumps(dati)
ricostruito = pickle.loads(serializzato)

# Serializzazione di oggetti personalizzati
class Configurazione:
    def __init__(self, nome, valori):
        self.nome = nome
        self.valori = valori

    def __repr__(self):
        return f"Configurazione({self.nome!r}, {self.valori!r})"

config = Configurazione("test", [1, 2, 3])
with open("config.pkl", "wb") as f:
    pickle.dump(config, f)
```

**Avvertenza di sicurezza**: `pickle.load()` puo eseguire codice arbitrario. Non deserializzare mai dati provenienti da fonti non attendibili. Per lo scambio di dati tra sistemi diversi, utilizzare JSON o un altro formato testuale. Un payload pickle malevolo puo eseguire comandi di sistema, eliminare file o installare malware.

I protocolli pickle vengono aggiornati con le nuove versioni di Python. Il protocollo 5 (Python 3.8+) supporta l'out-of-band data per una serializzazione efficiente di grandi buffer di memoria.

### shelve

Il modulo `shelve` offre un dizionario persistente, salvato su disco tramite pickle:

```python
import shelve

# Scrittura (crea file come database.db, database.dir, database.bak)
with shelve.open("database") as db:
    db["utente_1"] = {"nome": "Anna", "eta": 30}
    db["utente_2"] = {"nome": "Marco", "eta": 25}
    db["contatore"] = 0

# Lettura
with shelve.open("database", flag="r") as db:  # "r" = sola lettura
    print(db["utente_1"])
    print(list(db.keys()))

# Aggiornamento — attenzione: i valori mutabili richiedono writeback
with shelve.open("database", writeback=True) as db:
    db["utente_1"]["eta"] = 31  # con writeback=True questo viene salvato
    db["contatore"] += 1
```

`shelve` e comodo per prototipi e piccole applicazioni, ma presenta limitazioni significative: non e thread-safe, il formato del database sottostante varia tra piattaforme (puo usare `dbm.gnu`, `dbm.ndbm` o `dbm.dumb`), e i file creati non sono portabili tra sistemi operativi diversi. Per dati strutturati di una certa complessita e preferibile un database come SQLite, che offre transazioni ACID, query SQL e portabilita completa.

### marshal

Il modulo `marshal` e un formato di serializzazione interno usato da Python per i file `.pyc` (bytecode compilato). Non e destinato all'uso applicativo e ha garanzie di compatibilita limitate tra versioni di Python:

```python
import marshal

# Uso basilare (sconsigliato per dati applicativi)
dati = {"chiave": [1, 2, 3], "flag": True}
serializzato = marshal.dumps(dati)
ricostruito = marshal.loads(serializzato)

# marshal supporta solo tipi primitivi: None, bool, int, float,
# complex, str, bytes, tuple, list, dict, set, frozenset, code objects
# NON supporta classi personalizzate, a differenza di pickle
```

---

## Watch e Monitoring

La libreria `watchdog` permette di monitorare il filesystem in tempo reale, reagendo a creazione, modifica, cancellazione e spostamento di file e directory. Questo e utile per build system, sincronizzazione, hot-reload di configurazioni e pipeline di elaborazione automatica.

```python
# pip install watchdog
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

class GestoreEventi(FileSystemEventHandler):
    """Gestisce gli eventi del filesystem."""

    def on_created(self, event):
        if not event.is_directory:
            print(f"Creato: {event.src_path}")

    def on_modified(self, event):
        if not event.is_directory:
            print(f"Modificato: {event.src_path}")

    def on_deleted(self, event):
        if not event.is_directory:
            print(f"Eliminato: {event.src_path}")

    def on_moved(self, event):
        print(f"Spostato: {event.src_path} -> {event.dest_path}")

# Avvio del monitoraggio
gestore = GestoreEventi()
osservatore = Observer()
osservatore.schedule(gestore, path="/home/utente/progetto", recursive=True)
osservatore.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    osservatore.stop()

osservatore.join()
```

Un esempio piu sofisticato con filtro per tipo di file e debouncing:

```python
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class MonitorPython(FileSystemEventHandler):
    """Monitora solo file Python con debouncing."""

    def __init__(self, callback, intervallo=1.0):
        self.callback = callback
        self.intervallo = intervallo
        self._ultimo_evento = {}

    def on_modified(self, event):
        if event.is_directory:
            return

        percorso = Path(event.src_path)
        if percorso.suffix != ".py":
            return

        # Debouncing: ignora eventi troppo ravvicinati
        ora = time.time()
        ultimo = self._ultimo_evento.get(event.src_path, 0)
        if ora - ultimo < self.intervallo:
            return

        self._ultimo_evento[event.src_path] = ora
        self.callback(percorso)

def on_file_cambiato(percorso):
    print(f"File Python modificato: {percorso}")
    # Esegui test, linting, rebuild...

gestore = MonitorPython(on_file_cambiato, intervallo=2.0)
osservatore = Observer()
osservatore.schedule(gestore, path="src/", recursive=True)
osservatore.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    osservatore.stop()
osservatore.join()
```

Per script piu semplici, `watchdog` offre anche un'interfaccia a linea di comando tramite il tool `watchmedo`:

```bash
# Esegui un comando quando i file Python cambiano
watchmedo shell-command \
    --patterns="*.py" \
    --recursive \
    --command='echo "Modificato: ${watch_src_path}"' \
    src/
```

---

## File Locking — Accesso Concorrente ai File

Quando piu processi o thread accedono allo stesso file simultaneamente, e necessario un meccanismo di locking per prevenire corruzione dei dati e race condition. Python offre diverse soluzioni, con diversi livelli di portabilita.

### fcntl — Locking POSIX (Linux/macOS)

Il modulo `fcntl` fornisce accesso diretto alle system call POSIX per il file locking. Funziona solo su sistemi Unix-like:

```python
import fcntl
import os

def scrivi_con_lock(percorso: str, dati: str) -> None:
    """Scrive su un file con lock esclusivo POSIX."""
    with open(percorso, "a", encoding="utf-8") as f:
        try:
            # LOCK_EX = lock esclusivo (blocca altri scrittori e lettori)
            # LOCK_NB = non-blocking (solleva IOError se il lock non e disponibile)
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            f.write(dati + "\n")
            f.flush()
            os.fsync(f.fileno())  # forza la scrittura su disco
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)  # rilascia il lock

def leggi_con_lock(percorso: str) -> str:
    """Legge un file con lock condiviso POSIX."""
    with open(percorso, "r", encoding="utf-8") as f:
        try:
            # LOCK_SH = lock condiviso (permette altri lettori, blocca scrittori)
            fcntl.flock(f.fileno(), fcntl.LOCK_SH)
            return f.read()
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)

# Lock non-blocking — utile per evitare deadlock
import errno

def tenta_lock(percorso: str) -> bool:
    """Tenta di acquisire un lock senza bloccarsi."""
    with open(percorso, "a") as f:
        try:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except OSError as e:
            if e.errno in (errno.EACCES, errno.EAGAIN):
                return False  # un altro processo detiene il lock
            raise

# Lock advisory vs mandatory
# IMPORTANTE: su Linux, flock() implementa lock ADVISORY.
# Cio significa che il lock e rispettato solo dai processi che lo richiedono
# esplicitamente. Un processo che apre il file senza richiedere il lock
# puo leggere e scrivere liberamente. Non e un meccanismo di sicurezza,
# ma un meccanismo di coordinamento tra processi cooperanti.
```

### portalocker — Locking Cross-Platform

Per applicazioni che devono funzionare sia su Linux/macOS che su Windows, la libreria `portalocker` fornisce un'API unificata:

```python
# pip install portalocker
import portalocker

# Lock con context manager — il modo piu semplice e sicuro
with portalocker.Lock("dati.json", mode="r+", timeout=10) as f:
    contenuto = f.read()
    # ... elaborazione ...
    f.seek(0)
    f.write(contenuto_modificato)
    f.truncate()

# Lock con timeout — evita blocchi indefiniti
try:
    with portalocker.Lock("risorsa.lock", timeout=5) as lock_file:
        # Operazione critica
        pass
except portalocker.LockException:
    print("Impossibile acquisire il lock entro 5 secondi")

# Lock esplicito per controllo granulare
f = open("condiviso.txt", "r+")
try:
    portalocker.lock(f, portalocker.LOCK_EX)  # lock esclusivo
    # ... operazione critica ...
finally:
    portalocker.unlock(f)
    f.close()

# Pattern: file di lock separato (lock file)
# Utile quando non si vuole/puo fare lock sul file dati stesso
import portalocker
import json

LOCK_FILE = "/var/run/myapp.lock"
DATA_FILE = "/var/app/config.json"

def aggiorna_config(chiave: str, valore) -> None:
    """Aggiorna la configurazione in modo atomico con lock."""
    with portalocker.Lock(LOCK_FILE, timeout=30):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
        config[chiave] = valore
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
```

### filelock — Alternativa Leggera

La libreria `filelock` offre un'interfaccia ancora piu minimale per il file locking cross-platform:

```python
# pip install filelock
from filelock import FileLock, Timeout

lock = FileLock("app.lock", timeout=10)

# Context manager
with lock:
    # Sezione critica — il lock viene rilasciato automaticamente
    pass

# Gestione del timeout
try:
    with lock.acquire(timeout=5):
        pass
except Timeout:
    print("Lock non disponibile")

# Lock rientrante — lo stesso thread puo acquisirlo piu volte
with lock:
    with lock:  # non causa deadlock
        pass
```

**Considerazioni importanti sul file locking**: i lock su file sono per loro natura *advisory* su tutti i sistemi operativi supportati da Python. Questo significa che funzionano correttamente solo quando tutti i processi che accedono al file cooperano utilizzando lo stesso meccanismo di locking. Inoltre, i lock non sopravvivono a crash del processo: se un processo termina inaspettatamente, il sistema operativo rilascia automaticamente i suoi lock. Per casi d'uso che richiedono garanzie piu forti, valutare l'uso di un database (SQLite supporta transazioni ACID) o di un sistema di locking distribuito (Redis, ZooKeeper).

---

## Scrittura Atomica dei File

La scrittura atomica garantisce che un file non venga mai lasciato in uno stato parziale o corrotto. Il pattern fondamentale e "write to temp, then rename": si scrive su un file temporaneo nella stessa directory e poi si esegue un rename atomico che sostituisce il file originale.

### Pattern Write-Temp-Rename

```python
import os
import tempfile
from pathlib import Path

def scrittura_atomica(percorso: str | Path, contenuto: str, encoding: str = "utf-8") -> None:
    """Scrive un file in modo atomico usando temp + rename.

    Garanzia: il file di destinazione non sara mai in uno stato parziale.
    Se il processo crasha durante la scrittura, il file originale resta intatto.
    """
    percorso = Path(percorso)
    directory = percorso.parent

    # Il file temporaneo DEVE essere nella stessa directory del target
    # per garantire che os.replace() sia atomico (stesso filesystem)
    fd, tmp_percorso = tempfile.mkstemp(
        dir=directory,
        prefix=f".{percorso.name}.",
        suffix=".tmp",
    )

    try:
        with os.fdopen(fd, "w", encoding=encoding) as f:
            f.write(contenuto)
            f.flush()
            os.fsync(f.fileno())  # forza la scrittura su disco

        # os.replace() e atomico su POSIX (singola system call rename)
        # Su Windows e atomico per file sullo stesso volume
        os.replace(tmp_percorso, percorso)

        # fsync sulla directory padre per garantire che il rename sia durevole
        # (necessario su Linux per durability completa)
        dir_fd = os.open(str(directory), os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)

    except BaseException:
        # Pulizia in caso di errore
        try:
            os.unlink(tmp_percorso)
        except OSError:
            pass
        raise

# Uso
scrittura_atomica("/etc/myapp/config.json", '{"version": 2}')
```

### Scrittura Atomica con Preservazione dei Permessi

```python
import os
import stat
import tempfile
from pathlib import Path

def scrittura_atomica_con_permessi(
    percorso: str | Path,
    contenuto: bytes | str,
    encoding: str = "utf-8",
) -> None:
    """Scrittura atomica che preserva permessi e proprietario del file originale."""
    percorso = Path(percorso)

    # Salva i metadati del file esistente (se presente)
    permessi_originali = None
    uid_originale = None
    gid_originale = None
    if percorso.exists():
        stat_info = percorso.stat()
        permessi_originali = stat.S_IMODE(stat_info.st_mode)
        uid_originale = stat_info.st_uid
        gid_originale = stat_info.st_gid

    modalita = "w" if isinstance(contenuto, str) else "wb"
    kwargs = {"encoding": encoding} if isinstance(contenuto, str) else {}

    fd, tmp_percorso = tempfile.mkstemp(dir=percorso.parent)
    try:
        with os.fdopen(fd, modalita, **kwargs) as f:
            f.write(contenuto)
            f.flush()
            os.fsync(f.fileno())

        # Ripristina i permessi originali
        if permessi_originali is not None:
            os.chmod(tmp_percorso, permessi_originali)
        if uid_originale is not None:
            try:
                os.chown(tmp_percorso, uid_originale, gid_originale)
            except PermissionError:
                pass  # richiede privilegi root

        os.replace(tmp_percorso, percorso)
    except BaseException:
        try:
            os.unlink(tmp_percorso)
        except OSError:
            pass
        raise

# Context manager per scrittura atomica
import contextlib

@contextlib.contextmanager
def apri_atomico(percorso: str | Path, mode: str = "w", **kwargs):
    """Context manager per scrittura atomica."""
    percorso = Path(percorso)
    fd, tmp_percorso = tempfile.mkstemp(dir=percorso.parent)
    tmp_file = None
    try:
        tmp_file = os.fdopen(fd, mode, **kwargs)
        yield tmp_file
        tmp_file.flush()
        os.fsync(tmp_file.fileno())
        tmp_file.close()
        tmp_file = None
        os.replace(tmp_percorso, percorso)
    except BaseException:
        if tmp_file is not None:
            tmp_file.close()
        try:
            os.unlink(tmp_percorso)
        except OSError:
            pass
        raise

# Uso del context manager
with apri_atomico("config.toml", mode="w", encoding="utf-8") as f:
    f.write('[server]\nhost = "0.0.0.0"\nport = 8080\n')
```

La distinzione tra `os.rename()` e `os.replace()` e importante: `os.replace()` sovrascrive atomicamente il file di destinazione se esiste, mentre `os.rename()` su Windows solleva un errore se la destinazione esiste gia. Per la scrittura atomica, usare sempre `os.replace()`.

---

## Permessi e Sicurezza dei File

La gestione corretta dei permessi e cruciale per la sicurezza delle applicazioni che operano su file. Python espone le operazioni sui permessi attraverso i moduli `os` e `pathlib`, con il modulo `stat` che fornisce le costanti per i flag di permesso.

### Lettura e Modifica dei Permessi

```python
import os
import stat
from pathlib import Path

percorso = Path("/home/utente/dati/segreto.key")

# Lettura dei permessi
info = percorso.stat()
mode = info.st_mode

# Decodifica dei permessi con il modulo stat
print(f"Permessi ottali: {oct(stat.S_IMODE(mode))}")
print(f"Leggibile dal proprietario: {bool(mode & stat.S_IRUSR)}")
print(f"Scrivibile dal proprietario: {bool(mode & stat.S_IWUSR)}")
print(f"Eseguibile dal proprietario: {bool(mode & stat.S_IXUSR)}")
print(f"Leggibile dal gruppo: {bool(mode & stat.S_IRGRP)}")
print(f"Leggibile da altri: {bool(mode & stat.S_IROTH)}")
print(f"Tipo di file: {'file' if stat.S_ISREG(mode) else 'directory' if stat.S_ISDIR(mode) else 'altro'}")

# Modifica dei permessi
# 0o600 = rw------- (solo proprietario puo leggere/scrivere)
os.chmod(percorso, 0o600)

# Modifica con Path (Python 3.10+)
percorso.chmod(0o644)  # rw-r--r--

# Creazione di file con permessi restrittivi fin dall'inizio
# Importante per file sensibili (chiavi, credenziali)
fd = os.open(
    "credenziali.json",
    os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
    0o600  # rw------- — solo il proprietario puo accedere
)
with os.fdopen(fd, "w", encoding="utf-8") as f:
    f.write('{"api_key": "secret"}')

# umask — maschera di creazione predefinita
vecchia_umask = os.umask(0o077)  # nuovi file: rw-------, nuove dir: rwx------
try:
    Path("file_sicuro.txt").touch()
finally:
    os.umask(vecchia_umask)  # ripristina la umask precedente
```

### Verifica dei Permessi e Accesso

```python
import os
from pathlib import Path

percorso = Path("/var/app/dati.db")

# Verifica se il processo corrente ha accesso
os.access(percorso, os.R_OK)  # leggibile?
os.access(percorso, os.W_OK)  # scrivibile?
os.access(percorso, os.X_OK)  # eseguibile?
os.access(percorso, os.F_OK)  # esiste?

# ATTENZIONE: os.access() ha una race condition intrinseca (TOCTOU)
# Tra la verifica e l'operazione, i permessi potrebbero cambiare.
# Meglio tentare l'operazione e gestire l'eccezione:
try:
    with open(percorso, "r") as f:
        dati = f.read()
except PermissionError:
    print("Accesso negato al file")
except FileNotFoundError:
    print("File non trovato")

# Proprietario e gruppo
print(f"Proprietario: {percorso.owner()}")  # nome utente
print(f"Gruppo: {percorso.group()}")        # nome gruppo

# Modifica proprietario (richiede root)
try:
    os.chown(percorso, uid=1000, gid=1000)
except PermissionError:
    print("Serve root per cambiare proprietario")

# shutil.chown accetta nomi di utente/gruppo come stringhe
import shutil
try:
    shutil.chown(percorso, user="appuser", group="appgroup")
except PermissionError:
    pass
```

### Sicurezza nella Creazione di File e Directory

```python
import os
import tempfile
from pathlib import Path

# Creazione sicura di directory con permessi restrittivi
def crea_directory_sicura(percorso: Path) -> None:
    """Crea una directory con permessi 0o700 (solo proprietario)."""
    percorso.mkdir(parents=True, exist_ok=True)
    percorso.chmod(0o700)

# Verifica che un percorso non sia un symlink prima di scrivere
def scrivi_sicuro(percorso: Path, contenuto: str) -> None:
    """Scrive su un file verificando che non sia un symlink."""
    if percorso.is_symlink():
        raise SecurityError(f"Rifiuto di scrivere su un symlink: {percorso}")
    percorso.write_text(contenuto, encoding="utf-8")

# Prevenzione di race condition TOCTOU con O_NOFOLLOW
def apri_senza_seguire_symlink(percorso: str, flags: int) -> int:
    """Apre un file rifiutando di seguire symlink."""
    return os.open(percorso, flags | os.O_NOFOLLOW)

# Pattern: directory temporanea con permessi ristretti per elaborazione sicura
with tempfile.TemporaryDirectory() as tmpdir:
    os.chmod(tmpdir, 0o700)  # solo il proprietario puo accedere
    file_sensibile = Path(tmpdir) / "decrypted.txt"
    file_sensibile.write_text("dati decifrati", encoding="utf-8")
    os.chmod(file_sensibile, 0o600)
    # Elaborazione...
    # Il file viene eliminato automaticamente all'uscita dal blocco
```

---

## Async File I/O

Le operazioni su file sono intrinsecamente bloccanti: quando un thread esegue una chiamata `read()` o `write()`, resta in attesa fino al completamento dell'operazione da parte del sistema operativo. In applicazioni asincrone basate su `asyncio`, questo comportamento blocca l'event loop, impedendo l'esecuzione concorrente di altre coroutine. Esistono due approcci principali per risolvere questo problema.

### aiofiles — File I/O Asincrono Dedicato

La libreria `aiofiles` e la soluzione piu matura e adottata per il file I/O asincrono in Python. Delega le operazioni di I/O a un thread pool, esponendo un'interfaccia async/await compatibile:

```python
# pip install aiofiles
import aiofiles
import asyncio

async def leggi_file_async(percorso: str) -> str:
    """Legge un file in modo asincrono."""
    async with aiofiles.open(percorso, mode="r", encoding="utf-8") as f:
        contenuto = await f.read()
    return contenuto

async def scrivi_file_async(percorso: str, contenuto: str) -> None:
    """Scrive su un file in modo asincrono."""
    async with aiofiles.open(percorso, mode="w", encoding="utf-8") as f:
        await f.write(contenuto)

# Lettura riga per riga — asincrona
async def elabora_log_async(percorso: str) -> int:
    """Conta gli errori in un file di log in modo asincrono."""
    contatore = 0
    async with aiofiles.open(percorso, mode="r", encoding="utf-8") as f:
        async for riga in f:
            if "ERROR" in riga:
                contatore += 1
    return contatore

# Elaborazione concorrente di piu file
async def elabora_multipli(percorsi: list[str]) -> list[str]:
    """Legge piu file in parallelo."""
    tasks = [leggi_file_async(p) for p in percorsi]
    return await asyncio.gather(*tasks)

# File binari asincroni
async def copia_file_async(sorgente: str, destinazione: str) -> None:
    """Copia un file in modo asincrono con chunked reading."""
    async with aiofiles.open(sorgente, mode="rb") as src:
        async with aiofiles.open(destinazione, mode="wb") as dst:
            while True:
                chunk = await src.read(65536)  # 64 KB
                if not chunk:
                    break
                await dst.write(chunk)

# Operazioni su filesystem asincrone
import aiofiles.os

async def operazioni_filesystem():
    """Operazioni asincrone sul filesystem."""
    # stat asincrono
    info = await aiofiles.os.stat("file.txt")
    print(f"Dimensione: {info.st_size}")

    # rename asincrono
    await aiofiles.os.rename("vecchio.txt", "nuovo.txt")

    # remove asincrono
    await aiofiles.os.remove("temporaneo.txt")

    # mkdir asincrono
    await aiofiles.os.makedirs("nuova/struttura/dir", exist_ok=True)

# Esempio: server di elaborazione file con aiofiles
async def processa_upload(file_paths: list[str]) -> dict[str, int]:
    """Elabora upload in modo concorrente, restituisce dimensioni."""
    risultati = {}

    async def processa_singolo(percorso: str) -> tuple[str, int]:
        async with aiofiles.open(percorso, mode="rb") as f:
            contenuto = await f.read()
        return percorso, len(contenuto)

    tasks = [processa_singolo(p) for p in file_paths]
    for risultato in await asyncio.gather(*tasks):
        percorso, dimensione = risultato
        risultati[percorso] = dimensione

    return risultati
```

### asyncio.to_thread — Alternativa Stdlib

A partire da Python 3.9, `asyncio.to_thread()` permette di eseguire funzioni bloccanti in un thread separato senza dipendenze esterne:

```python
import asyncio
from pathlib import Path

async def leggi_con_to_thread(percorso: str) -> str:
    """Legge un file usando asyncio.to_thread() — nessuna dipendenza esterna."""
    return await asyncio.to_thread(Path(percorso).read_text, encoding="utf-8")

async def scrivi_con_to_thread(percorso: str, contenuto: str) -> None:
    """Scrive su un file usando asyncio.to_thread()."""
    await asyncio.to_thread(Path(percorso).write_text, contenuto, encoding="utf-8")

# Elaborazione concorrente con to_thread
async def elabora_file_multipli(directory: str) -> dict[str, int]:
    """Conta le righe di tutti i file .txt in una directory."""
    cartella = Path(directory)
    file_txt = list(cartella.glob("*.txt"))

    async def conta_righe(percorso: Path) -> tuple[str, int]:
        contenuto = await asyncio.to_thread(percorso.read_text, encoding="utf-8")
        return str(percorso), contenuto.count("\n")

    tasks = [conta_righe(f) for f in file_txt]
    risultati = await asyncio.gather(*tasks)
    return dict(risultati)

# Combinazione con operazioni di rete
async def scarica_e_salva(url: str, percorso: str) -> None:
    """Esempio di combinazione I/O rete + file asincroni."""
    import aiohttp
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as risposta:
            dati = await risposta.read()
    # Scrittura su file senza bloccare l'event loop
    await asyncio.to_thread(Path(percorso).write_bytes, dati)
```

### Limitazione della Concorrenza con Semafori

Quando si elaborano molti file in parallelo, e fondamentale limitare il numero di file aperti simultaneamente per evitare l'esaurimento dei file descriptor del sistema operativo:

```python
import asyncio
import aiofiles
from pathlib import Path

async def elabora_con_limite(
    percorsi: list[Path],
    max_concorrente: int = 50,
) -> dict[str, int]:
    """Elabora file in parallelo con limite di concorrenza."""
    semaforo = asyncio.Semaphore(max_concorrente)
    risultati: dict[str, int] = {}

    async def elabora_singolo(percorso: Path) -> tuple[str, int]:
        async with semaforo:
            async with aiofiles.open(percorso, mode="r", encoding="utf-8") as f:
                contenuto = await f.read()
            return str(percorso), len(contenuto.split())

    tasks = [elabora_singolo(p) for p in percorsi]
    for nome, parole in await asyncio.gather(*tasks):
        risultati[nome] = parole

    return risultati

# Uso: elabora fino a 50 file alla volta
# asyncio.run(elabora_con_limite(list(Path("docs/").rglob("*.md")), max_concorrente=50))
```

**Quando usare quale approccio**: `aiofiles` e preferibile quando si hanno molte operazioni su file all'interno di un'applicazione asincrona (server web, pipeline di dati), perche gestisce internamente il thread pool e offre un'API coerente. `asyncio.to_thread()` e sufficiente per casi semplici dove non si vuole aggiungere una dipendenza esterna, ma richiede di gestire manualmente l'apertura e chiusura dei file. In entrambi i casi, le operazioni vengono eseguite in thread separati — il vantaggio non e il parallelismo dell'I/O in se, ma il fatto che l'event loop non viene bloccato e puo servire altre coroutine nel frattempo.

Un errore comune e aprire migliaia di file contemporaneamente con `asyncio.gather()` senza semaforo: questo porta a un `OSError: [Errno 24] Too many open files`. Il limite predefinito su Linux e tipicamente 1024 file descriptor per processo (verificabile con `ulimit -n`). Il pattern con `asyncio.Semaphore` mostrato sopra e il modo idiomatico per gestire questa limitazione.

---

## Monitoring Avanzato del Filesystem

### watchdog — Pattern Matching e RegexMatchingEventHandler

Oltre al `FileSystemEventHandler` base, `watchdog` fornisce handler specializzati per il filtraggio avanzato degli eventi:

```python
from watchdog.events import PatternMatchingEventHandler, RegexMatchingEventHandler

# PatternMatchingEventHandler — filtro con pattern glob
class MonitorSorgenti(PatternMatchingEventHandler):
    """Monitora solo file sorgente, ignorando build artifacts."""

    def __init__(self):
        super().__init__(
            patterns=["*.py", "*.pyi", "*.toml", "*.yaml"],
            ignore_patterns=["*.pyc", "*__pycache__*", "*.egg-info*"],
            ignore_directories=True,
            case_sensitive=True,
        )

    def on_modified(self, event):
        print(f"Sorgente modificato: {event.src_path}")

    def on_created(self, event):
        print(f"Nuovo file sorgente: {event.src_path}")

# RegexMatchingEventHandler — filtro con espressioni regolari
class MonitorLog(RegexMatchingEventHandler):
    """Monitora file di log con pattern regex."""

    def __init__(self):
        super().__init__(
            regexes=[r".*\.log$", r".*\.log\.\d+$"],  # app.log, app.log.1, ...
            ignore_regexes=[r".*\.log\.gz$"],           # ignora log compressi
            ignore_directories=True,
        )

    def on_modified(self, event):
        print(f"Log aggiornato: {event.src_path}")
```

### watchdog con Coda di Eventi

Per elaborazione asincrona degli eventi, `watchdog` si integra con le code di Python:

```python
import time
import queue
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class AccodaEventi(FileSystemEventHandler):
    """Accoda gli eventi per elaborazione asincrona."""

    def __init__(self, coda: queue.Queue):
        self.coda = coda

    def on_any_event(self, event):
        if not event.is_directory:
            self.coda.put(event)

def elabora_eventi(coda: queue.Queue) -> None:
    """Elabora gli eventi dalla coda in un thread separato."""
    while True:
        try:
            evento = coda.get(timeout=1.0)
            tipo = evento.event_type  # created, modified, deleted, moved
            percorso = evento.src_path
            print(f"[{tipo.upper()}] {percorso}")
            coda.task_done()
        except queue.Empty:
            continue

# Setup
coda_eventi = queue.Queue()
gestore = AccodaEventi(coda_eventi)
osservatore = Observer()
osservatore.schedule(gestore, path="src/", recursive=True)

import threading
thread_elaborazione = threading.Thread(
    target=elabora_eventi, args=(coda_eventi,), daemon=True
)
thread_elaborazione.start()
osservatore.start()
```

### inotify Nativo (Solo Linux)

Per applicazioni Linux-only che richiedono il massimo delle prestazioni e il controllo granulare degli eventi, si puo usare l'interfaccia `inotify` direttamente tramite `inotify_simple`:

```python
# pip install inotify_simple
from inotify_simple import INotify, flags

inotify = INotify()
watch_flags = flags.CREATE | flags.MODIFY | flags.DELETE | flags.MOVED_FROM | flags.MOVED_TO

# Aggiungere una directory al monitoring
wd = inotify.add_watch("/home/utente/progetto/src", watch_flags)

# Loop di lettura eventi — molto efficiente, usa epoll internamente
while True:
    for evento in inotify.read():
        nome_flags = flags.from_mask(evento.mask)
        print(f"Evento: {nome_flags}, File: {evento.name}")

        # Flags specifici di inotify non disponibili in watchdog:
        # IN_CLOSE_WRITE  — file chiuso dopo scrittura
        # IN_CLOSE_NOWRITE — file chiuso senza scrittura
        # IN_ATTRIB — attributi del file cambiati (permessi, owner)
        # IN_ACCESS — file letto
```

I vantaggi di `inotify` nativo rispetto a `watchdog` su Linux: overhead minimo (nessun polling, nessun thread di background per il polling), eventi piu granulari (close_write, attrib, access), e latenza inferiore. Lo svantaggio e la non portabilita: `inotify` esiste solo su Linux, mentre `watchdog` funziona su Linux (usa inotify internamente), macOS (usa FSEvents) e Windows (usa ReadDirectoryChangesW).

### Confronto tra Approcci di Monitoring

| Caratteristica | watchdog | inotify_simple | pyinotify |
|---------------|----------|----------------|-----------|
| **Piattaforma** | Cross-platform | Solo Linux | Solo Linux |
| **Overhead** | Basso (usa inotify su Linux) | Minimo | Medio |
| **API** | OOP con event handler | Low-level, iteratore | OOP con callback |
| **Ricorsione** | Automatica | Manuale (watch per dir) | Automatica |
| **Pattern matching** | Built-in (glob, regex) | Manuale | Manuale |
| **Manutenzione** | Attiva, aggiornato | Stabile, leggera | Legacy, poco attiva |
| **Uso consigliato** | Applicazioni generiche | Performance critica su Linux | Sconsigliato per nuovi progetti |

Per la maggior parte dei casi d'uso, `watchdog` e la scelta raccomandata: offre un'API pulita, e cross-platform e gestisce automaticamente la ricorsione nelle sottodirectory. L'uso diretto di `inotify` ha senso solo in scenari ad alta frequenza di eventi su Linux dove ogni microsecondo di latenza conta, come sistemi di trading, pipeline di dati real-time o strumenti di build altamente ottimizzati.

---

## Compressione Avanzata

### Compressione Streaming e Pipeline

Per file molto grandi, la compressione in streaming evita di caricare l'intero file in memoria:

```python
import gzip
import bz2
import lzma
import shutil

# Pipeline di compressione: file grande -> gzip senza caricare in memoria
def comprimi_file(sorgente: str, destinazione: str, algoritmo: str = "gzip") -> None:
    """Comprime un file in streaming, senza caricarlo interamente in memoria."""
    openers = {
        "gzip": lambda p: gzip.open(p, "wb", compresslevel=6),
        "bz2": lambda p: bz2.open(p, "wb", compresslevel=9),
        "xz": lambda p: lzma.open(p, "wb", preset=6),
    }
    open_compressed = openers[algoritmo]

    with open(sorgente, "rb") as src, open_compressed(destinazione) as dst:
        shutil.copyfileobj(src, dst, length=1024 * 1024)  # 1 MB chunks

# Decompressione trasparente — determina il formato automaticamente
import magic  # pip install python-magic (opzionale)

def apri_auto_decomprimi(percorso: str, mode: str = "rt", encoding: str = "utf-8"):
    """Apre un file, decomprimendo automaticamente se necessario."""
    openers = {
        ".gz": gzip.open,
        ".bz2": bz2.open,
        ".xz": lzma.open,
    }
    from pathlib import Path
    suffisso = Path(percorso).suffix.lower()
    opener = openers.get(suffisso, open)

    kwargs = {"encoding": encoding} if "t" in mode else {}
    return opener(percorso, mode, **kwargs)

# Uso trasparente
with apri_auto_decomprimi("log.txt.gz") as f:
    for riga in f:
        print(riga.strip())

with apri_auto_decomprimi("dati.csv") as f:  # file non compresso — open() normale
    for riga in f:
        print(riga.strip())

# Compressione incrementale con GzipFile per controllo granulare
with gzip.GzipFile("output.gz", "wb", compresslevel=9) as gz:
    gz.write(b"Primo blocco di dati\n")
    gz.write(b"Secondo blocco di dati\n")
    # Ogni write() viene compresso incrementalmente
```

### zipfile Avanzato

```python
import zipfile
from pathlib import Path

# Creazione di archivi ZIP con password (solo lettura in stdlib)
# Per la creazione di ZIP cifrati, usare pyzipper
# pip install pyzipper
import pyzipper

with pyzipper.AESZipFile(
    "archivio_cifrato.zip", "w",
    compression=pyzipper.ZIP_LZMA,
    encryption=pyzipper.WZ_AES
) as zf:
    zf.setpassword(b"password_sicura")
    zf.writestr("segreto.txt", "Dati riservati")

# ZIP64 per archivi > 4 GB
with zipfile.ZipFile("enorme.zip", "w", allowZip64=True) as zf:
    zf.write("file_enorme.db")

# Aggiungere file a un archivio esistente
with zipfile.ZipFile("archivio.zip", "a") as zf:
    zf.write("nuovo_file.txt")

# Leggere file dall'archivio senza estrarre (in memoria)
with zipfile.ZipFile("archivio.zip", "r") as zf:
    with zf.open("documento.txt") as f:
        # f e un file-like object — puo essere passato a csv.reader, json.load, etc.
        import csv
        reader = csv.reader(
            (riga.decode("utf-8") for riga in f),
            delimiter=","
        )
        for riga in reader:
            print(riga)

# Verifica di sicurezza prima dell'estrazione
def estrai_sicuro_zip(archivio: str, destinazione: str) -> None:
    """Estrae un ZIP con verifiche di sicurezza."""
    dest = Path(destinazione).resolve()
    with zipfile.ZipFile(archivio, "r") as zf:
        for info in zf.infolist():
            # Rifiuta percorsi assoluti
            if info.filename.startswith("/") or info.filename.startswith("\\"):
                raise ValueError(f"Percorso assoluto rifiutato: {info.filename}")
            # Rifiuta path traversal
            estratto = (dest / info.filename).resolve()
            if not str(estratto).startswith(str(dest)):
                raise ValueError(f"Path traversal rilevato: {info.filename}")
            # Rifiuta file troppo grandi (zip bomb)
            if info.file_size > 500 * 1024 * 1024:  # 500 MB
                raise ValueError(f"File troppo grande: {info.filename} ({info.file_size} byte)")
        zf.extractall(destinazione)
```

---

## shutil Avanzato

### copytree con Funzioni Personalizzate

```python
import shutil
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# copytree con funzione di copia personalizzata
def copia_con_log(src: str, dst: str, *, follow_symlinks: bool = True) -> str:
    """Funzione di copia che logga ogni file copiato."""
    logger.info("Copiando: %s -> %s", src, dst)
    return shutil.copy2(src, dst, follow_symlinks=follow_symlinks)

shutil.copytree(
    "progetto/",
    "backup/",
    copy_function=copia_con_log,
    dirs_exist_ok=True,
)

# copytree con filtro callable avanzato
def ignora_grandi(directory: str, contenuti: list[str]) -> set[str]:
    """Ignora file piu grandi di 10 MB e directory nascoste."""
    da_ignorare = set()
    for nome in contenuti:
        percorso = Path(directory) / nome
        if nome.startswith("."):
            da_ignorare.add(nome)
        elif percorso.is_file() and percorso.stat().st_size > 10 * 1024 * 1024:
            da_ignorare.add(nome)
    return da_ignorare

shutil.copytree("sorgente/", "destinazione/", ignore=ignora_grandi)

# copytree con gestione errori personalizzata
def gestisci_errori_copia(errori):
    """Handler per errori non fatali durante copytree."""
    for src, dst, errore in errori:
        logger.warning("Errore copiando %s -> %s: %s", src, dst, errore)

try:
    shutil.copytree("sorgente/", "destinazione/")
except shutil.Error as e:
    gestisci_errori_copia(e.args[0])

# rmtree con handler per file read-only (comune su Windows con .git)
import os
import stat

def rimuovi_readonly(func, percorso, exc_info):
    """Handler per rmtree che rimuove il flag read-only."""
    os.chmod(percorso, stat.S_IWRITE)
    func(percorso)

shutil.rmtree("cartella_con_readonly/", onerror=rimuovi_readonly)

# Copia efficiente con copyfileobj e buffer personalizzato
with open("grande.iso", "rb") as src, open("copia.iso", "wb") as dst:
    shutil.copyfileobj(src, dst, length=16 * 1024 * 1024)  # buffer da 16 MB

# Spazio su disco con formattazione leggibile
def spazio_disco_formattato(percorso: str = "/") -> str:
    """Restituisce informazioni sullo spazio disco in formato leggibile."""
    uso = shutil.disk_usage(percorso)
    def formatta(byte_val: int) -> str:
        for unita in ["B", "KB", "MB", "GB", "TB"]:
            if byte_val < 1024:
                return f"{byte_val:.1f} {unita}"
            byte_val /= 1024
        return f"{byte_val:.1f} PB"

    return (
        f"Totale: {formatta(uso.total)}, "
        f"Usato: {formatta(uso.used)} ({uso.used/uso.total*100:.1f}%), "
        f"Libero: {formatta(uso.free)}"
    )

print(spazio_disco_formattato("/"))
print(spazio_disco_formattato("/home"))
```

---

## os.scandir — Performance nella Scansione di Directory

`os.scandir()`, introdotto in Python 3.5 con PEP 471, e significativamente piu veloce di `os.listdir()` per la scansione di directory. La ragione e che `os.scandir()` restituisce oggetti `DirEntry` che contengono informazioni di tipo file e attributi gia ottenute dalla system call di lettura della directory, evitando chiamate `stat()` aggiuntive.

```python
import os
from pathlib import Path

# os.scandir restituisce un iteratore di DirEntry — lazy e efficiente
def trova_file_grandi(directory: str, soglia_mb: float = 100) -> list[tuple[str, float]]:
    """Trova file piu grandi della soglia usando os.scandir.

    Piu veloce di pathlib.iterdir() + stat() separato perche DirEntry
    memorizza il tipo di file ottenuto dalla readdir() del sistema operativo.
    """
    grandi = []
    soglia_byte = soglia_mb * 1024 * 1024

    with os.scandir(directory) as entries:
        for entry in entries:
            # is_file() e is_dir() NON richiedono una system call stat aggiuntiva
            # su Linux (usano d_type da readdir)
            if entry.is_file(follow_symlinks=False):
                # stat() viene chiamata solo quando serve la dimensione
                info = entry.stat(follow_symlinks=False)
                if info.st_size > soglia_byte:
                    dim_mb = info.st_size / (1024 * 1024)
                    grandi.append((entry.path, dim_mb))

    return sorted(grandi, key=lambda x: x[1], reverse=True)

# Scansione ricorsiva efficiente con os.scandir
def scandir_ricorsivo(directory: str, profondita_max: int = -1):
    """os.walk implementato con os.scandir — gia il default in Python 3.5+.

    os.walk() usa internamente os.scandir() a partire da Python 3.5.
    Questa implementazione esplicita mostra il meccanismo sottostante.
    """
    with os.scandir(directory) as entries:
        dirs = []
        files = []
        for entry in entries:
            if entry.is_dir(follow_symlinks=False):
                dirs.append(entry.name)
            elif entry.is_file(follow_symlinks=False):
                files.append(entry.name)

        yield directory, dirs, files

        if profondita_max != 0:
            for d in dirs:
                percorso = os.path.join(directory, d)
                yield from scandir_ricorsivo(percorso, profondita_max - 1)

# Confronto prestazionale con listdir
import time

def benchmark_listdir(directory: str) -> float:
    inizio = time.perf_counter()
    for nome in os.listdir(directory):
        percorso = os.path.join(directory, nome)
        os.stat(percorso)  # stat separato per ogni file
    return time.perf_counter() - inizio

def benchmark_scandir(directory: str) -> float:
    inizio = time.perf_counter()
    with os.scandir(directory) as entries:
        for entry in entries:
            entry.stat()  # stat incluso o cached da DirEntry
    return time.perf_counter() - inizio

# Su directory con migliaia di file, scandir e 2-20x piu veloce

# DirEntry espone: name, path, inode(), is_dir(), is_file(), is_symlink(), stat()
with os.scandir(".") as entries:
    for entry in entries:
        tipo = "DIR " if entry.is_dir() else "FILE"
        print(f"[{tipo}] {entry.name} (inode: {entry.inode()})")
```

La ragione per cui `os.scandir()` e cosi piu veloce risiede nel funzionamento delle system call sottostanti. Su Linux, la system call `readdir()` restituisce il tipo di file (`d_type`) insieme al nome, quindi `DirEntry.is_file()` e `DirEntry.is_dir()` sono operazioni gratuite che non richiedono una `stat()` aggiuntiva. Su Windows, `FindNextFile()` restituisce gia dimensione, timestamp e attributi. Con `os.listdir()` + `os.stat()`, si eseguono N+1 system call (una listdir + N stat), mentre con `os.scandir()` spesso basta una sola system call per tutta la directory.

### Confronto tra Metodi di Iterazione sulle Directory

| Metodo | Tipo di ritorno | Lazy | Metadata inclusa | Uso raccomandato |
|--------|----------------|------|------------------|------------------|
| `os.listdir()` | `list[str]` | No | No (solo nomi) | Raramente — solo per compatibilita |
| `os.scandir()` | `Iterator[DirEntry]` | Si | Si (tipo file, stat cached) | Performance critica, directory grandi |
| `Path.iterdir()` | `Iterator[Path]` | Si | No (stat separato) | Codice idiomatico moderno |
| `os.walk()` | `Iterator[tuple]` | Si | Parziale (usa scandir) | Ricorsione con filtraggio |
| `Path.walk()` | `Iterator[tuple]` | Si | No | Ricorsione con Path objects (3.12+) |
| `Path.glob()` | `Iterator[Path]` | Si | No | Pattern matching su nomi |
| `Path.rglob()` | `Iterator[Path]` | Si | No | Pattern matching ricorsivo |

Come regola generale: per nuovo codice dove la performance non e critica, `pathlib` e il default idiomatico. Per directory con migliaia di file dove si devono controllare attributi, `os.scandir()` offre vantaggi misurabili. Per ricorsione con esclusione di sottodirectory, `os.walk()` resta il piu flessibile grazie alla modifica in-place di `dirnames`.

---

## configparser Avanzato

Il modulo `configparser` offre funzionalita avanzate oltre la semplice lettura/scrittura di file INI:

```python
import configparser

# Interpolazione avanzata con ExtendedInterpolation
# Supporta la sintassi ${section:key} per riferimenti tra sezioni
config = configparser.ConfigParser(
    interpolation=configparser.ExtendedInterpolation()
)

config.read_string("""
[DEFAULT]
app_name = MyApp

[paths]
base_dir = /opt/${DEFAULT:app_name}
data_dir = ${paths:base_dir}/data
log_dir = ${paths:base_dir}/logs
config_file = ${paths:base_dir}/config.ini

[database]
host = localhost
port = 5432
name = ${DEFAULT:app_name}_db
url = postgresql://${database:host}:${database:port}/${database:name}
""")

print(config["paths"]["data_dir"])    # /opt/MyApp/data
print(config["database"]["url"])      # postgresql://localhost:5432/MyApp_db

# Sezioni come namespace — iterazione e accesso dinamico
for sezione in config.sections():
    print(f"\n[{sezione}]")
    for chiave, valore in config[sezione].items():
        print(f"  {chiave} = {valore}")

# Conversione di tipi con metodi dedicati
config.read_string("""
[server]
host = 0.0.0.0
port = 8080
debug = yes
timeout = 30.5
workers = 4
allowed_origins = http://localhost:3000, https://example.com
""")

host = config["server"].get("host")                    # str
porta = config["server"].getint("port")                # int
debug = config["server"].getboolean("debug")           # bool (yes/no, true/false, 1/0)
timeout = config["server"].getfloat("timeout")         # float

# Valori di fallback
max_conn = config["server"].getint("max_connections", fallback=100)

# Parsing di liste da valori separati da virgola
origini = [o.strip() for o in config["server"]["allowed_origins"].split(",")]

# Scrittura con commenti e ordine preservato
config_output = configparser.ConfigParser()
config_output["app"] = {
    "nome": "Server Produzione",
    "versione": "2.1.0",
}
config_output["logging"] = {
    "livello": "INFO",
    "formato": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
}

with open("app_output.ini", "w", encoding="utf-8") as f:
    f.write("# Configurazione dell'applicazione\n")
    f.write("# Generata automaticamente\n\n")
    config_output.write(f)

# configparser con valori multilinea
config.read_string("""
[template]
email_body =
    Gentile {nome},
    
    La informiamo che il suo ordine {ordine_id}
    e stato spedito.
    
    Cordiali saluti,
    Il Team
""")
corpo = config["template"]["email_body"]
```

---

## Elaborazione File di Grandi Dimensioni — Pattern Avanzati

### Generatori e Pipeline Composibili

```python
from pathlib import Path
from typing import Iterator
import csv
import io

# Pipeline composibile per elaborazione di file CSV grandi
def leggi_csv_lazy(percorso: str | Path) -> Iterator[dict]:
    """Legge un CSV riga per riga come dizionari."""
    with open(percorso, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        yield from reader

def filtra_per_campo(righe: Iterator[dict], campo: str, valore: str) -> Iterator[dict]:
    """Filtra righe dove campo == valore."""
    for riga in righe:
        if riga.get(campo) == valore:
            yield riga

def trasforma_campi(righe: Iterator[dict], trasformazioni: dict) -> Iterator[dict]:
    """Applica trasformazioni ai campi specificati."""
    for riga in righe:
        nuova_riga = dict(riga)
        for campo, fn in trasformazioni.items():
            if campo in nuova_riga:
                nuova_riga[campo] = fn(nuova_riga[campo])
        yield nuova_riga

def scrivi_csv_lazy(percorso: str | Path, righe: Iterator[dict], campi: list[str]) -> int:
    """Scrive un CSV riga per riga, restituisce il numero di righe scritte."""
    contatore = 0
    with open(percorso, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campi)
        writer.writeheader()
        for riga in righe:
            writer.writerow({k: riga.get(k, "") for k in campi})
            contatore += 1
    return contatore

# Composizione della pipeline
pipeline = leggi_csv_lazy("vendite_2025.csv")
pipeline = filtra_per_campo(pipeline, "regione", "Europa")
pipeline = trasforma_campi(pipeline, {
    "prezzo": lambda x: f"{float(x) * 1.22:.2f}",  # aggiungi IVA
    "nome": str.upper,
})

scritte = scrivi_csv_lazy(
    "vendite_europa_iva.csv",
    pipeline,
    campi=["id", "nome", "prezzo", "regione", "data"],
)
print(f"Scritte {scritte} righe")

# Lettura di file con delimitatori di record personalizzati
def leggi_record(percorso: str, delimitatore: str = "\n---\n") -> Iterator[str]:
    """Legge un file dividendolo per un delimitatore multi-carattere."""
    buffer = []
    with open(percorso, "r", encoding="utf-8") as f:
        for riga in f:
            buffer.append(riga)
            testo = "".join(buffer)
            while delimitatore in testo:
                record, testo = testo.split(delimitatore, 1)
                yield record.strip()
                buffer = [testo]
        # Ultimo record (senza delimitatore finale)
        finale = "".join(buffer).strip()
        if finale:
            yield finale

# Conteggio efficiente di righe senza caricare il file
def conta_righe_veloce(percorso: str) -> int:
    """Conta le righe di un file in modo efficiente usando buffer binario."""
    contatore = 0
    with open(percorso, "rb") as f:
        while True:
            buf = f.read(1024 * 1024)  # 1 MB
            if not buf:
                break
            contatore += buf.count(b"\n")
    return contatore

# Campionamento casuale da file grandi senza caricare tutto
import random

def campiona_righe(percorso: str, n: int) -> list[str]:
    """Campiona n righe casuali da un file grande (algoritmo reservoir sampling)."""
    campione: list[str] = []
    with open(percorso, "r", encoding="utf-8") as f:
        for i, riga in enumerate(f):
            if i < n:
                campione.append(riga.rstrip("\n"))
            else:
                j = random.randint(0, i)
                if j < n:
                    campione[j] = riga.rstrip("\n")
    return campione
```

---

## Gestione degli Errori di I/O

La corretta gestione degli errori nelle operazioni su file e una delle aree piu sottovalutate della programmazione Python. Le operazioni di I/O sono intrinsecamente soggette a fallimenti per ragioni esterne al controllo del programma: disco pieno, permessi insufficienti, file bloccati da altri processi, connessioni di rete interrotte per filesystem remoti, filesystem corrotti.

### Gerarchia delle Eccezioni di I/O

```python
# La gerarchia delle eccezioni rilevanti per il file I/O:
#
# BaseException
# └── Exception
#     └── OSError (alias: IOError, EnvironmentError)
#         ├── FileNotFoundError      (errno ENOENT)
#         ├── FileExistsError        (errno EEXIST)
#         ├── PermissionError        (errno EACCES, EPERM)
#         ├── IsADirectoryError      (errno EISDIR)
#         ├── NotADirectoryError     (errno ENOTDIR)
#         ├── InterruptedError       (errno EINTR)
#         ├── BlockingIOError        (errno EAGAIN, EWOULDBLOCK)
#         ├── ConnectionError        (NFS/CIFS)
#         └── TimeoutError
#
# Altre eccezioni rilevanti:
# - UnicodeDecodeError  (encoding errato)
# - UnicodeEncodeError  (caratteri non rappresentabili)
# - ValueError          (modalita di apertura invalida)
# - struct.error        (dati binari malformati)

from pathlib import Path
import json

def leggi_config_sicura(percorso: Path) -> dict:
    """Legge un file di configurazione JSON con gestione completa degli errori."""
    try:
        contenuto = percorso.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise SystemExit(f"File di configurazione non trovato: {percorso}")
    except PermissionError:
        raise SystemExit(f"Permessi insufficienti per leggere: {percorso}")
    except IsADirectoryError:
        raise SystemExit(f"Il percorso e una directory, non un file: {percorso}")
    except UnicodeDecodeError as e:
        raise SystemExit(f"Encoding non valido in {percorso}: {e}")
    except OSError as e:
        raise SystemExit(f"Errore di I/O leggendo {percorso}: {e}")

    try:
        return json.loads(contenuto)
    except json.JSONDecodeError as e:
        raise SystemExit(f"JSON non valido in {percorso}: {e}")

# Pattern: retry con backoff esponenziale per filesystem di rete
import time
import errno

def leggi_con_retry(
    percorso: str,
    tentativi: int = 3,
    ritardo_base: float = 0.5,
) -> str:
    """Legge un file con retry per gestire errori transitori (NFS, CIFS)."""
    ultimo_errore = None
    for tentativo in range(tentativi):
        try:
            with open(percorso, "r", encoding="utf-8") as f:
                return f.read()
        except OSError as e:
            ultimo_errore = e
            if e.errno in (errno.ESTALE, errno.EIO, errno.EAGAIN):
                # Errori transitori — vale la pena riprovare
                ritardo = ritardo_base * (2 ** tentativo)
                time.sleep(ritardo)
            else:
                raise  # Errore non transitori — non riprovare
    raise ultimo_errore  # type: ignore[misc]

# Pattern: scrittura con verifica dello spazio disco
import shutil

def scrivi_con_verifica_spazio(
    percorso: Path,
    contenuto: str,
    margine_mb: float = 100,
) -> None:
    """Scrive su file solo se c'e spazio sufficiente sul disco."""
    dimensione_stimata = len(contenuto.encode("utf-8"))
    spazio_libero = shutil.disk_usage(percorso.parent).free

    if spazio_libero < dimensione_stimata + margine_mb * 1024 * 1024:
        spazio_mb = spazio_libero / (1024 * 1024)
        raise OSError(
            f"Spazio disco insufficiente: {spazio_mb:.1f} MB disponibili, "
            f"necessari almeno {dimensione_stimata / (1024*1024):.1f} MB + {margine_mb} MB di margine"
        )

    percorso.write_text(contenuto, encoding="utf-8")
```

### Pattern di Cleanup Sicuro

```python
import os
import logging
from pathlib import Path
from contextlib import contextmanager

logger = logging.getLogger(__name__)

@contextmanager
def file_temporaneo_sicuro(percorso: Path):
    """Context manager che garantisce la pulizia del file temporaneo."""
    try:
        yield percorso
    finally:
        try:
            if percorso.exists():
                percorso.unlink()
        except OSError as e:
            logger.warning("Impossibile eliminare %s: %s", percorso, e)

# Pattern: operazione con rollback
def aggiorna_file_con_backup(
    percorso: Path,
    nuovo_contenuto: str,
) -> None:
    """Aggiorna un file creando un backup automatico con rollback in caso di errore."""
    backup = percorso.with_suffix(percorso.suffix + ".bak")

    # Crea backup dell'originale
    if percorso.exists():
        import shutil
        shutil.copy2(percorso, backup)

    try:
        percorso.write_text(nuovo_contenuto, encoding="utf-8")
    except Exception:
        # Rollback: ripristina il backup
        if backup.exists():
            import shutil
            shutil.move(str(backup), str(percorso))
        raise
    else:
        # Successo: elimina il backup
        if backup.exists():
            backup.unlink()
```

---

## Best Practices

1. **Usare `pathlib` invece di `os.path`**. Il modulo `pathlib` offre un'interfaccia orientata agli oggetti piu leggibile e meno soggetta a errori rispetto alla manipolazione di stringhe con `os.path`. L'operatore `/` per la concatenazione dei percorsi elimina una classe intera di bug legati ai separatori. Adottare `pathlib` come scelta predefinita per tutte le nuove basi di codice.

2. **Specificare sempre l'encoding**. Anche se Python 3.15 rendera UTF-8 il default, specificare `encoding="utf-8"` esplicitamente garantisce compatibilita con tutte le versioni di Python 3 e rende chiara l'intenzione del codice. Non fare mai affidamento sull'encoding di sistema, che varia tra piattaforme e configurazioni locali.

3. **Usare il context manager (`with`) per ogni operazione su file**. Il costrutto `with` garantisce la chiusura del file anche in caso di eccezioni. Non chiudere un file puo portare a perdita di dati (i buffer non vengono scritti su disco), esaurimento dei file descriptor o blocchi su sistemi Windows dove i file aperti non possono essere rinominati o eliminati.

4. **Elaborare file grandi in modo incrementale**. Non caricare mai l'intero contenuto di un file grande in memoria con `read()`. Iterare riga per riga per i file di testo, leggere a chunk per i file binari e usare generator per costruire pipeline di elaborazione memory-efficient. Per accesso casuale a file molto grandi, valutare `mmap`.

5. **Usare `json` per lo scambio dati e mai `pickle` con fonti esterne**. JSON e il formato standard per lo scambio dati tra sistemi. `pickle` e specifico di Python, non e interoperabile e, soprattutto, puo eseguire codice arbitrario durante la deserializzazione. Usare `pickle` solo per dati interni di cui si ha il controllo completo, come cache locali o salvataggi di stato.

6. **Gestire sempre le eccezioni di I/O**. Le operazioni su file possono fallire per molteplici ragioni: permessi insufficienti, disco pieno, file bloccato, percorso inesistente. Gestire `FileNotFoundError`, `PermissionError`, `IsADirectoryError` e `OSError` con messaggi utili per la diagnosi. Non catturare mai `Exception` generica per mascherare errori di I/O.

7. **Usare `tempfile` per i file temporanei**. Non creare mai file temporanei con nomi prevedibili in directory condivise. Il modulo `tempfile` genera nomi unici in modo crittograficamente sicuro e gestisce la pulizia automatica. `TemporaryDirectory` con context manager e la soluzione piu sicura per file temporanei che devono esistere per la durata di un'operazione.

8. **Applicare il filtro di sicurezza nell'estrazione di archivi**. A partire da Python 3.12, `tarfile.extractall()` supporta il parametro `filter` per prevenire attacchi di path traversal. Usare sempre `filter="data"` per estrazioni sicure. Per `zipfile`, verificare che i percorsi estratti non contengano `..` o percorsi assoluti. Non estrarre mai archivi provenienti da fonti non attendibili senza validazione.

9. **Preferire formati testuali per la configurazione**. TOML (`pyproject.toml`), YAML e JSON sono formati leggibili, versionabili con git e modificabili con qualsiasi editor. Evitare `pickle` o `shelve` per le configurazioni. Per Python moderno, TOML e la scelta idiomatica grazie al supporto nativo con `tomllib` (Python 3.11+) e alla sua adozione nel packaging Python.

10. **Chiudere le risorse al livello giusto di astrazione**. Quando si costruiscono librerie o API che gestiscono file, esporre i context manager ai chiamanti anziche nascondere l'apertura e chiusura dei file internamente. Implementare `__enter__` e `__exit__` nelle proprie classi che incapsulano risorse di I/O, o utilizzare `contextlib.contextmanager` per creare context manager da generator. Questo rende esplicito il ciclo di vita delle risorse e previene leak.

11. **Usare `os.scandir()` per directory con molti file**. Quando si scansionano directory contenenti migliaia di file e si necessita di informazioni come il tipo (file o directory) o la dimensione, `os.scandir()` e significativamente piu veloce di `os.listdir()` + `os.stat()` perche le informazioni sul tipo di file vengono restituite direttamente dalla system call di lettura della directory, senza richiedere chiamate `stat()` aggiuntive. Il guadagno in prestazioni e tipicamente 2-20x, con i benefici maggiori su filesystem di rete.

12. **Limitare la concorrenza nelle operazioni asincrone su file**. Quando si usa `aiofiles` o `asyncio.to_thread()` per elaborare molti file in parallelo, usare sempre un `asyncio.Semaphore` per limitare il numero di file aperti simultaneamente. Senza questa precauzione, l'apertura simultanea di migliaia di file porta rapidamente all'esaurimento dei file descriptor del sistema operativo (tipicamente limitati a 1024 per processo su Linux). Un valore ragionevole per il semaforo e 50-100 file concorrenti.

13. **Usare la scrittura atomica per file critici**. Per file di configurazione, database, stato persistente e qualsiasi file la cui corruzione causerebbe problemi, adottare il pattern "write to temp + fsync + rename": scrivere i dati su un file temporaneo nella stessa directory, chiamare `os.fsync()` per garantire la scrittura su disco, e poi usare `os.replace()` per sostituire atomicamente il file originale. Questo garantisce che il file non sia mai in uno stato parziale, anche in caso di crash del processo o del sistema.

14. **Implementare il file locking per accesso concorrente**. Quando piu processi accedono allo stesso file, usare `portalocker` o `filelock` per il locking cross-platform. Ricordare che i lock su file in Python sono *advisory*: funzionano solo quando tutti i processi cooperano. Per garanzie piu forti di consistenza, valutare l'uso di SQLite o un database relazionale.
---

## Esercizi di Consolidamento

**Esercizio 1 — Pathlib explorer:**
Scrivi una funzione `tree(directory: Path, indent: int = 0) -> None` che stampa l'albero delle directory in formato simile al comando `tree` di Unix. Usa `Path.iterdir()` e ricorsione. Gestisci `PermissionError` per le directory non leggibili.

**Esercizio 2 — Merge CSV con validazione:**
Dati N file CSV nella stessa directory con colonne identiche, scrivi uno script che li unisca in un unico file CSV ordinato per una colonna specificata dall'utente. Valida che tutti i file abbiano le stesse intestazioni prima di procedere. Usa `csv.DictReader` e `csv.DictWriter`.

**Esercizio 3 — Atomic config writer:**
Implementa una classe `AtomicConfigWriter` che scrive file TOML in modo atomico (write to temp + rename). Il metodo `save()` deve garantire che il file di configurazione non venga mai lasciato in uno stato parziale, anche in caso di crash durante la scrittura. Scrivi test con pytest che verifichino il comportamento atomico.

**Esercizio 4 — Log file analyzer:**
Scrivi un generatore `parse_log(path: Path)` che legge un file di log riga per riga (anche file da diversi GB), estrae timestamp, livello e messaggio, e yield `LogEntry` namedtuple. Implementa filtri per livello e intervallo temporale. Misura il consumo di memoria con `tracemalloc`.

**Esercizio 5 — Secure archive extractor:**
Implementa una funzione `safe_extract(archive_path: Path, dest: Path)` che supporti `.zip` e `.tar.gz`. Deve: validare che nessun file estratto esca dalla directory di destinazione (path traversal), rifiutare archivi con file > 100 MB (zip bomb), e loggare ogni file estratto. Usa `tarfile` con `filter="data"` per Python 3.12+.

**Esercizio 6 — File locking con contatore condiviso:**
Implementa un contatore persistente salvato in un file JSON, accessibile da piu processi in modo concorrente. Usa `portalocker` o `filelock` per il locking e scrittura atomica per gli aggiornamenti. Scrivi un test che lancia N processi simultanei (con `multiprocessing`) e verifica che il contatore finale sia corretto (nessuna race condition). Verifica che il file non venga mai corrotto anche se un processo crasha durante la scrittura.

**Esercizio 7 — Async file processor:**
Scrivi una pipeline asincrona con `aiofiles` che: legge tutti i file `.txt` da una directory, conta le parole in ciascuno in modo concorrente (con `asyncio.gather`), e scrive un report JSON con i risultati. Misura il tempo di esecuzione e confrontalo con l'equivalente sincrono su una directory con almeno 100 file di testo.

**Esercizio 8 — Directory watcher con hot-reload:**
Implementa un sistema di hot-reload per file di configurazione TOML usando `watchdog`. Il sistema deve: monitorare un file `config.toml` per modifiche, ricaricare la configurazione in modo thread-safe quando il file cambia, applicare debouncing per evitare ricaricamenti multipli per un singolo salvataggio, e validare la nuova configurazione prima di applicarla (se invalida, mantenere quella precedente).

**Esercizio 9 — Compressione streaming multi-formato:**
Implementa una utility da riga di comando che comprime file grandi in streaming usando il formato specificato dall'utente (gzip, bz2, xz). Deve mostrare una barra di progresso, gestire file > 1 GB senza esaurire la memoria, e preservare i permessi del file originale. Aggiungi un'opzione per il livello di compressione e un benchmark che confronta i tre formati su un file di test.

**Esercizio 10 — os.scandir-based du:**
Implementa una versione Python del comando `du -sh` (disk usage) usando `os.scandir()` per la massima performance. La funzione deve calcolare la dimensione totale di una directory e di tutte le sue sottodirectory, gestire permessi insufficienti senza bloccarsi, supportare l'opzione di escludere directory specifiche (come `.git`), e restituire i risultati sia come dimensione grezza in byte sia in formato leggibile (KB/MB/GB).

---

## Letture e Riferimenti

### Fonti Primarie

- **pathlib — Object-oriented filesystem paths** — https://docs.python.org/3/library/pathlib.html (consultato: 2026-05-24). Reference completo per `Path`, `PurePath`, metodi di filesystem, pattern glob.

- **io — Core tools for working with streams** — https://docs.python.org/3/library/io.html (consultato: 2026-05-24). Gerarchia degli stream: `TextIOWrapper`, `BufferedReader`, `RawIOBase`, encoding.

- **json — JSON encoder and decoder** — https://docs.python.org/3/library/json.html (consultato: 2026-05-24). `json.dump/load`, custom encoder/decoder, `default` parameter.

- **csv — CSV File Reading and Writing** — https://docs.python.org/3/library/csv.html (consultato: 2026-05-24). `DictReader`, `DictWriter`, dialetti, quoting.

- **tomllib — Parse TOML files** — https://docs.python.org/3/library/tomllib.html (consultato: 2026-05-24). Parsing TOML nativo in Python 3.11+ (sola lettura).

- **PEP 428 — The pathlib module** — https://peps.python.org/pep-0428/ (consultato: 2026-05-24). Design rationale e motivazioni per l'introduzione di pathlib.

- **PEP 686 — Make UTF-8 mode default** — https://peps.python.org/pep-0686/ (consultato: 2026-05-24). Transizione verso UTF-8 come encoding default in Python 3.15+.

- **mmap — Memory-mapped file support** — https://docs.python.org/3/library/mmap.html (consultato: 2026-05-24). Memory mapping, accesso casuale, condivisione inter-processo.

- **struct — Interpret bytes as packed binary data** — https://docs.python.org/3/library/struct.html (consultato: 2026-05-24). Packing/unpacking di dati binari, formati di byte order.

- **tempfile — Generate temporary files and directories** — https://docs.python.org/3/library/tempfile.html (consultato: 2026-05-24). NamedTemporaryFile, SpooledTemporaryFile, TemporaryDirectory.

- **shutil — High-level file operations** — https://docs.python.org/3/library/shutil.html (consultato: 2026-05-24). copytree, copy2, disk_usage, make_archive, rmtree.

- **PEP 471 — os.scandir() function** — https://peps.python.org/pep-0471/ (consultato: 2026-05-24). Motivazioni e benchmark per os.scandir, 2-20x piu veloce di os.listdir.

- **aiofiles — PyPI** — https://pypi.org/project/aiofiles/ (consultato: 2026-05-24). File I/O asincrono per applicazioni asyncio.

- **portalocker — GitHub** — https://github.com/wolph/portalocker (consultato: 2026-05-24). File locking cross-platform con supporto context manager.

- **watchdog — GitHub** — https://github.com/gorakhargosh/watchdog (consultato: 2026-05-24). Monitoring del filesystem cross-platform con PatternMatching.

### Testi Consigliati

- **"Fluent Python" di Luciano Ramalho (2a ed., O'Reilly)** — Capitolo su data model, protocollo dei context manager, I/O pattern.

- **"Python Cookbook" di David Beazley e Brian K. Jones (3a ed., O'Reilly)** — Ricette pratiche per file I/O, parsing, serializzazione.

---

## Riferimenti Incrociati

| Argomento | Modulo | File |
|-----------|--------|------|
| Fondamenti: tipi, stringhe, bytes, encoding | 01 | [01-fondamenti-linguaggio.md](01-fondamenti-linguaggio.md) |
| Decoratori, generatori, context manager | 04 | [04-decoratori-generatori-context-manager.md](04-decoratori-generatori-context-manager.md) |
| Regex e text processing | 06 | [06-regex-e-text-processing.md](06-regex-e-text-processing.md) |
| Error handling e logging | 07 | [07-error-handling-e-logging.md](07-error-handling-e-logging.md) |
| Data processing (pandas, polars) | 14 | [14-data-processing.md](14-data-processing.md) |
| Sicurezza: pickle deserialization, path traversal | 18 | [18-sicurezza.md](18-sicurezza.md) |

---

## Glossario

| Termine | Definizione |
|---------|-------------|
| **buffer** | Area di memoria intermedia che accumula dati prima di scriverli su disco, migliorando le performance di I/O. |
| **context manager** | Oggetto che implementa `__enter__` e `__exit__`, usato con `with` per gestire risorse (file, connessioni). |
| **encoding** | Schema di conversione tra caratteri e sequenze di byte. UTF-8 e lo standard moderno; ASCII ne e un sottoinsieme. |
| **file descriptor** | Intero assegnato dal sistema operativo a ogni file aperto. Risorsa limitata; file non chiusi li esauriscono. |
| **glob** | Pattern di matching per nomi di file (`*.py`, `**/*.md`). Supportato nativamente da `Path.glob()`. |
| **mmap** | Memory-mapped file: il contenuto del file viene mappato direttamente nello spazio di indirizzamento del processo. |
| **path traversal** | Attacco che usa `..` nei percorsi per accedere a file fuori dalla directory prevista. Prevenuto con `resolve()`. |
| **PurePath** | Classe pathlib per manipolazione pura dei percorsi (senza accesso al filesystem). |
| **serializzazione** | Conversione di strutture dati Python in formato persistente (JSON, pickle, msgpack). |
| **stream** | Flusso sequenziale di dati (byte o caratteri) leggibile/scrivibile. Base del modello I/O Python. |
| **TOML** | Tom's Obvious Minimal Language — formato di configurazione leggibile, nativo in Python 3.11+ via `tomllib`. |
| **UTF-8** | Encoding Unicode a lunghezza variabile (1-4 byte). Standard de facto per testo su web e in Python moderno. |
| **advisory lock** | Lock che funziona solo tra processi cooperanti che lo richiedono esplicitamente. Non impedisce l'accesso da parte di processi che non usano il locking. |
| **aiofiles** | Libreria per file I/O asincrono in Python. Delega le operazioni a un thread pool con interfaccia async/await. |
| **atomic write** | Pattern di scrittura che garantisce che un file non sia mai in uno stato parziale: write to temp + rename. |
| **BytesIO** | Buffer binario in memoria con interfaccia identica a un file object. Utile per costruire dati binari o per testing. |
| **copy-on-write** | Strategia mmap dove le modifiche alla mappatura non vengono propagate al file originale. |
| **DirEntry** | Oggetto restituito da `os.scandir()` con informazioni cached sul tipo di file, evitando chiamate stat aggiuntive. |
| **fcntl** | Modulo POSIX per il controllo dei file descriptor, include funzioni di file locking (`flock`, `lockf`). |
| **fsync** | System call che forza la scrittura dei buffer del sistema operativo su disco fisico, garantendo la durabilita dei dati. |
| **inotify** | Sottosistema del kernel Linux per il monitoring efficiente degli eventi del filesystem. |
| **os.replace** | Funzione che sostituisce atomicamente un file con un altro. Preferibile a `os.rename()` per la scrittura atomica cross-platform. |
| **portalocker** | Libreria cross-platform per file locking che astrae le differenze tra fcntl (Unix) e Win32 API (Windows). |
| **reservoir sampling** | Algoritmo per campionare k elementi da un flusso di dimensione sconosciuta con probabilita uniforme. |
| **SpooledTemporaryFile** | File temporaneo che resta in memoria finche non supera una soglia configurabile, poi trasferisce su disco. |
| **struct** | Modulo per la conversione tra valori Python e strutture dati binarie C, usato per protocolli e formati binari. |
| **TOCTOU** | Time Of Check Time Of Use: race condition dove lo stato verificato cambia prima dell'operazione effettiva. |
| **umask** | Maschera di creazione predefinita che sottrae permessi ai file e directory appena creati. |
| **watchdog** | Libreria cross-platform per il monitoring del filesystem. Usa inotify (Linux), FSEvents (macOS), ReadDirectoryChangesW (Windows). |
