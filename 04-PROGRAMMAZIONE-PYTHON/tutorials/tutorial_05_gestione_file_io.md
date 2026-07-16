# Tutorial: Gestione File e I/O — Dal Principiante all'Esperto

> **Companion to:** `05-gestione-file-io.md`
> **Scope:** open() completo con tutte le modalità, encoding e Unicode, pathlib (Path operations), shutil, tempfile, JSON (load/dump/custom encoder), CSV (reader/writer/DictReader), YAML (safe_load), TOML (tomllib), mmap, file lock, filesystem watching.
> **Prerequisiti:** `tutorial_01_fondamenti_linguaggio.md` completato
> **Durata stimata:** 20–25 ore
> **Lingua:** Italiano

---

## Prima di Iniziare: Perché i File sono Fondamentali

### L'Analogia dell'Archivio Fisico

Immagina un ufficio con un archivio fisico: grandi armadi metallici pieni di cassetti. Ogni **cassetto** è un **file**, ogni **armadio** è una **directory** (cartella), e l'**etichetta sul cassetto** è il **path** (percorso).

Quando apri un cassetto, prendi dei fogli, li leggi, magari ne aggiungi altri, poi richiudi il cassetto. Questo è esattamente quello che fa Python con i file:

```
Armadio (directory)   → /home/utente/documenti/
Cassetto (file)       → relazione_2026.txt
Etichetta (path)      → /home/utente/documenti/relazione_2026.txt
Contenuto             → il testo scritto nei fogli
```

### Perché i File sono Indispensabili

Senza file, ogni volta che chiudi il programma **perdi tutto**. I file sono la memoria persistente dei tuoi programmi.

**Esempi reali:**
- **Log di un server:** registra ogni richiesta HTTP — senza file, non potresti debuggare problemi in produzione
- **File di configurazione:** `config.json` dice all'app quale database usare, quale porta aprire
- **Database locali:** SQLite salva l'intero database in un singolo file `.db`
- **Report CSV:** i risultati delle analisi salvati per essere aperti in Excel
- **File `.env`:** contiene le credenziali (API key, password) separate dal codice

### Tipi di File

| Tipo | Descrizione | Esempi |
|------|-------------|--------|
| **Testo** | Leggibile da umani, contiene caratteri | `.txt`, `.py`, `.json`, `.csv`, `.md` |
| **Binario** | Leggibile solo da macchine, contiene byte grezzi | `.png`, `.mp3`, `.pdf`, `.exe`, `.zip` |

La differenza è fondamentale: aprire un'immagine PNG come file di testo produce caratteri incomprensibili — stai leggendo i byte grezzi come se fossero testo.

---

## Parte A: Le Basi Assolute

### A1 — Cos'è un File? Come il Computer Salva i Dati

#### Dal Bit al File

Tutto nel computer è costruito su **bit** (0 o 1). Otto bit formano un **byte**. Un file è semplicemente una sequenza di byte salvata sul disco.

```
Bit:   0  1  0  0  1  0  0  0   = lettera 'H' (ASCII 72)
       0  1  1  0  0  1  0  1   = lettera 'e' (ASCII 101)
       0  1  1  0  1  1  0  0   = lettera 'l' (ASCII 108)
       ...
```

#### File di Testo vs File Binari

**File di testo** (`documento.txt`): la sequenza di byte rappresenta caratteri usando una **codifica** (encoding). Il Blocco Note di Windows può aprirlo e mostrare testo leggibile.

**File binari** (`foto.jpg`): i byte rappresentano dati strutturati secondo un formato specifico. Il Blocco Note lo apre ma mostra caratteri caotici.

**Prova pratica:**

```python
# Leggi un file PNG come testo (output: caratteri incomprensibili)
with open("logo.png", "r", errors="replace") as f:
    print(f.read(20))
# Output: "PNG\r\n\x1a\n\x00\x00\x00\rIHDR..."  (caratteri strani)

# Leggi un file PNG come binario (output: i byte grezzi)
with open("logo.png", "rb") as f:
    print(f.read(8))
# Output: b'\x89PNG\r\n\x1a\n'  (firma PNG — i primi 8 byte identificano il formato)
```

#### Il Problema dell'Encoding: Perché "é" Diventa "Ã©"

Immagina di avere un dizionario che traduce lettere in numeri. ASCII è un dizionario che conosce solo le 128 lettere dell'alfabeto inglese (A=65, B=66...). Ma che succede con "é", "ü", "中", "🎉"?

Serve un dizionario più grande: **UTF-8** è il dizionario universale che conosce oltre un milione di caratteri. È lo standard moderno.

```python
# La lettera "é" in UTF-8 occupa 2 byte
print("é".encode("utf-8"))    # b'\xc3\xa9'  (2 byte)
print("é".encode("latin-1"))  # b'\xe9'      (1 byte — encoding diverso!)

# Se salvi in UTF-8 ma leggi in latin-1: 2 byte letti come 2 caratteri → "Ã©"
# Questo spiega il classico problema dei caratteri storti
```

**Regola d'oro:** usa sempre `encoding='utf-8'` sia in lettura che in scrittura.

#### Concetto di Path (Percorso)

Il **path** è l'indirizzo del file nel filesystem:

```
Linux/macOS (path assoluto):   /home/utente/documenti/report.txt
Windows (path assoluto):       C:\Users\utente\documenti\report.txt
Path relativo:                 documenti/report.txt   (relativo alla directory corrente)
```

- **Path assoluto:** parte dalla radice del filesystem, funziona sempre indipendentemente da dove sei
- **Path relativo:** parte dalla directory corrente — più breve ma dipende da dove lanci il programma

---

### A2 — open() — Aprire File in Modo Sicuro

#### Le Modalità di Apertura

`open()` è la funzione fondamentale per lavorare con i file. Il secondo parametro è la **modalità**:

| Modalità | Nome | Analogia fisica | Comportamento |
|----------|------|-----------------|---------------|
| `"r"` | Read | Apri il cassetto per leggere | Legge. Errore se il file non esiste |
| `"w"` | Write | Svuota il cassetto e riscrivi | Sovrascrive tutto. Crea il file se non esiste |
| `"a"` | Append | Aggiungi fogli in fondo | Aggiunge in coda. Crea il file se non esiste |
| `"x"` | eXclusive | Crea un cassetto nuovo — errore se esiste già | Crea solo se non esiste (safe create) |
| `"r+"` | Read+Write | Leggi e modifica senza svuotare | Lettura e scrittura. Errore se non esiste |
| `"b"` | Binary | (si aggiunge a r/w/a) | Modalità binaria: legge/scrive byte, non testo |

Combinazioni comuni: `"rb"` (lettura binaria), `"wb"` (scrittura binaria), `"ab"` (append binario).

#### Perché SEMPRE usare `with open()`

**Senza `with`:**

```python
# SCONSIGLIATO — cosa succede se read() lancia un'eccezione?
f = open("dati.txt", "r", encoding="utf-8")
contenuto = f.read()   # se qui c'è un errore...
f.close()              # questa riga non viene mai eseguita!
                       # il file rimane aperto → dati persi o corrotti
```

**Il problema:** un file non chiuso può causare:
- Dati non scritti su disco (buffer non svuotato)
- Esaurimento dei file descriptor di sistema (su Linux il limite è ~1024 per processo)
- Su Windows: il file rimane bloccato e altri processi non possono accedervi

**Con `with open()` — il modo corretto:**

```python
# CORRETTO — il file viene SEMPRE chiuso, anche se c'è un'eccezione
with open("dati.txt", "r", encoding="utf-8") as f:
    contenuto = f.read()
# Qui f è già chiuso automaticamente — garanzia assoluta
```

Il `with` implementa il pattern "usa e chiudi": apre il file, esegue il blocco, e chiude il file qualunque cosa succeda.

#### Primo Esempio Completo

```python
# Creiamo un file, scriviamoci, poi leggiamolo
from pathlib import Path

# Passo 1: Scrittura
with open("mio_file.txt", "w", encoding="utf-8") as f:
    f.write("Ciao, mondo!\n")
    f.write("Seconda riga del file.\n")
    f.write("Terza riga con accenti: é, ü, à.\n")

print("File scritto con successo.")

# Passo 2: Lettura
with open("mio_file.txt", "r", encoding="utf-8") as f:
    contenuto = f.read()

print("Contenuto del file:")
print(contenuto)
```

**Output atteso:**
```
File scritto con successo.
Contenuto del file:
Ciao, mondo!
Seconda riga del file.
Terza riga con accenti: é, ü, à.
```

#### Aprire Più File Simultaneamente

```python
# Leggi da un file e scrivi su un altro — syntax moderna (Python 3.10+)
with (
    open("input.txt", "r", encoding="utf-8") as ingresso,
    open("output.txt", "w", encoding="utf-8") as uscita,
):
    for riga in ingresso:
        uscita.write(riga.upper())

# Syntax compatibile con Python 3.x precedenti
with open("input.txt", "r", encoding="utf-8") as ingresso:
    with open("output.txt", "w", encoding="utf-8") as uscita:
        for riga in ingresso:
            uscita.write(riga.upper())
```

#### Problemi Comuni e Soluzioni

**FileNotFoundError:** il file non esiste nel percorso indicato

```python
try:
    with open("file_inesistente.txt", "r", encoding="utf-8") as f:
        contenuto = f.read()
except FileNotFoundError as e:
    print(f"File non trovato: {e}")
    # Output: File non trovato: [Errno 2] No such file or directory: 'file_inesistente.txt'
```

**PermissionError:** non hai i permessi per leggere/scrivere il file

```python
try:
    with open("/etc/shadow", "r", encoding="utf-8") as f:
        contenuto = f.read()
except PermissionError as e:
    print(f"Accesso negato: {e}")
    # Output: Accesso negato: [Errno 13] Permission denied: '/etc/shadow'
```

**IsADirectoryError:** hai indicato una directory invece di un file

```python
try:
    with open("/home/utente/", "r", encoding="utf-8") as f:
        contenuto = f.read()
except IsADirectoryError as e:
    print(f"È una directory, non un file: {e}")
```

**UnicodeDecodeError:** il file non è codificato in UTF-8

```python
try:
    # File salvato con encoding Windows-1252 (comune nei file Excel)
    with open("file_windows.csv", "r", encoding="utf-8") as f:
        contenuto = f.read()
except UnicodeDecodeError as e:
    print(f"Errore di encoding: {e}")
    # Soluzione: prova con encoding="latin-1" o encoding="cp1252"
    with open("file_windows.csv", "r", encoding="cp1252") as f:
        contenuto = f.read()
```

**Pattern robusto con gestione di tutti gli errori comuni:**

```python
from pathlib import Path

def leggi_file_sicuro(percorso: str) -> str | None:
    """Legge un file di testo gestendo tutti gli errori comuni."""
    try:
        with open(percorso, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"ERRORE: File non trovato — {percorso}")
        return None
    except PermissionError:
        print(f"ERRORE: Permessi insufficienti — {percorso}")
        return None
    except IsADirectoryError:
        print(f"ERRORE: Il percorso è una directory — {percorso}")
        return None
    except UnicodeDecodeError:
        print(f"ERRORE: Encoding non UTF-8 — prova con encoding='latin-1'")
        return None
    except OSError as e:
        print(f"ERRORE I/O generico: {e}")
        return None

# Utilizzo
testo = leggi_file_sicuro("documento.txt")
if testo is not None:
    print(f"Letti {len(testo)} caratteri.")
```

---

### A3 — Leggere File — Tutti i Metodi

#### Analogia: Leggere un Libro

Immagina un libro fisico. Puoi:
1. **Leggerlo tutto d'un fiato** (`read()`) — prendi tutte le pagine e leggi
2. **Leggerlo riga per riga** (`readline()`) — leggi una riga, torni, leggi la successiva
3. **Farne fotocopie di tutte le righe** (`readlines()`) — ottieni una lista di tutte le righe
4. **Sfogliarlo automaticamente** (iterazione `for`) — il modo più comodo e moderno

#### Metodo 1: `read()` — Tutto in Memoria

```python
# Crea un file di esempio
with open("esempio.txt", "w", encoding="utf-8") as f:
    f.write("Prima riga\nSeconda riga\nTerza riga\n")

# read() — carica TUTTO il contenuto in una singola stringa
with open("esempio.txt", "r", encoding="utf-8") as f:
    tutto = f.read()

print(type(tutto))   # <class 'str'>
print(repr(tutto))   # 'Prima riga\nSeconda riga\nTerza riga\n'
print(tutto)
```

**Output atteso:**
```
<class 'str'>
'Prima riga\nSeconda riga\nTerza riga\n'
Prima riga
Seconda riga
Terza riga
```

**Leggere N caratteri alla volta:**

```python
with open("esempio.txt", "r", encoding="utf-8") as f:
    chunk1 = f.read(5)   # legge i primi 5 caratteri
    chunk2 = f.read(5)   # legge i successivi 5 caratteri

print(repr(chunk1))  # 'Prima'
print(repr(chunk2))  # ' riga'
```

**ATTENZIONE — File Grandi:** `read()` carica **tutto** in memoria RAM. Un file da 4 GB con `read()` occuperà 4 GB di RAM. Per file grandi usa l'iterazione diretta (vedi sotto).

#### Metodo 2: `readline()` — Una Riga alla Volta

```python
with open("esempio.txt", "r", encoding="utf-8") as f:
    riga1 = f.readline()   # legge la prima riga (include \n finale)
    riga2 = f.readline()   # legge la seconda riga
    riga3 = f.readline()   # legge la terza riga
    riga4 = f.readline()   # fine del file → stringa vuota ''

print(repr(riga1))   # 'Prima riga\n'
print(repr(riga2))   # 'Seconda riga\n'
print(repr(riga3))   # 'Terza riga\n'
print(repr(riga4))   # ''  (fine file)
```

**Output atteso:**
```
'Prima riga\n'
'Seconda riga\n'
'Terza riga\n'
''
```

**Quando usarlo:** quando devi elaborare le righe una alla volta con logica complessa, o quando hai bisogno di tenere traccia della posizione nel file.

#### Metodo 3: `readlines()` — Lista di Tutte le Righe

```python
with open("esempio.txt", "r", encoding="utf-8") as f:
    righe = f.readlines()   # lista di stringhe, ognuna con \n finale

print(type(righe))    # <class 'list'>
print(len(righe))     # 3
print(righe)          # ['Prima riga\n', 'Seconda riga\n', 'Terza riga\n']

# Rimuovere il \n finale
righe_pulite = [r.rstrip("\n") for r in righe]
print(righe_pulite)   # ['Prima riga', 'Seconda riga', 'Terza riga']
```

**Output atteso:**
```
<class 'list'>
3
['Prima riga\n', 'Seconda riga\n', 'Terza riga\n']
['Prima riga', 'Seconda riga', 'Terza riga']
```

**ATTENZIONE:** come `read()`, carica **tutto** in memoria. Per file grandi, usa l'iterazione diretta.

#### Metodo 4: Iterazione Diretta — Il Modo Pythonico

```python
# Il modo più efficiente: non carica tutto in memoria
# Legge una riga alla volta, come sfogliare un libro pagina per pagina
with open("esempio.txt", "r", encoding="utf-8") as f:
    for riga in f:
        riga_pulita = riga.rstrip("\n")   # rimuove \n finale
        print(f"→ {riga_pulita}")
```

**Output atteso:**
```
→ Prima riga
→ Seconda riga
→ Terza riga
```

**Perché è il modo migliore:**
- Legge una riga alla volta → usa pochissima RAM anche per file da GB
- La sintassi è la più leggibile
- È la scelta predefinita per i file di testo

#### Esempio Pratico: Contare le Righe con Errori

```python
# Conta le righe di log con livello ERROR in un file di log
# Simula un file di log reale
with open("server.log", "w", encoding="utf-8") as f:
    f.write("2026-07-15 10:00:01 INFO  Server avviato\n")
    f.write("2026-07-15 10:01:22 ERROR Connessione rifiutata da 192.168.1.5\n")
    f.write("2026-07-15 10:01:45 WARN  Buffer quasi pieno (95%)\n")
    f.write("2026-07-15 10:02:10 ERROR Timeout database dopo 30s\n")
    f.write("2026-07-15 10:03:00 INFO  Health check OK\n")

# Conta gli errori — uno alla volta, memoria minima
contatore_errori = 0
with open("server.log", "r", encoding="utf-8") as f:
    for riga in f:
        if "ERROR" in riga:
            contatore_errori += 1
            print(f"Errore trovato: {riga.strip()}")

print(f"\nTotale errori: {contatore_errori}")
```

**Output atteso:**
```
Errore trovato: 2026-07-15 10:01:22 ERROR Connessione rifiutata da 192.168.1.5
Errore trovato: 2026-07-15 10:02:10 ERROR Timeout database dopo 30s

Totale errori: 2
```

#### Confronto — Quando Usare Quale Metodo

| Metodo | Memoria usata | Caso d'uso ideale |
|--------|---------------|-------------------|
| `read()` | Tutto il file | File piccoli, serve il testo completo come stringa |
| `read(N)` | N byte/char | Parsing di formati binari o a blocchi fissi |
| `readline()` | Una riga | Logica complessa per riga, con controllo esplicito della posizione |
| `readlines()` | Tutto il file | File piccoli, serve una lista di righe |
| `for riga in f` | Una riga | **Default raccomandato** — file di qualsiasi dimensione |

**Regola pratica:** usa sempre l'iterazione diretta (`for riga in f`) a meno che tu non abbia una ragione specifica per fare diversamente.

---

### A4 - Scrivere File: write e writelines

#### Analogia: Il Dattilografo e il Quaderno

Il metodo `write()` e come un dattilografo che batte testo su una macchina da scrivere:
scrive esattamente quello che gli dai, senza aggiungere niente (nemmeno il ritorno a capo).
Il metodo `writelines()` e come dare al dattilografo un pacco di foglietti gia scritti
-- li incolla in sequenza.

#### Il Metodo write()

```python
with open("output.txt", "w", encoding="utf-8") as out:
    n1 = out.write("Prima riga")       # NON aggiunge newline automaticamente
    n2 = out.write("\n")               # devi aggiungere il newline manualmente
    n3 = out.write("Seconda riga\n")
    print(f"Caratteri scritti: {n1}, {n2}, {n3}")
    # Output: Caratteri scritti: 10, 1, 13
```

**Output atteso nel file:**
```
Prima riga
Seconda riga
```

`write()` restituisce il numero di caratteri scritti.
Nota: **non aggiunge il newline automaticamente** -- devi farlo tu.

#### Il Metodo writelines()

```python
righe = [
    "Lunedi: studia Python\n",
    "Martedi: pratica con esercizi\n",
    "Mercoledi: revisione e test\n",
]

with open("agenda.txt", "w", encoding="utf-8") as out:
    out.writelines(righe)   # scrive tutte le righe in sequenza
                            # NON aggiunge separatori tra gli elementi
```

**Output nel file:**
```
Lunedi: studia Python
Martedi: pratica con esercizi
Mercoledi: revisione e test
```

**Attenzione:** `writelines()` non aggiunge separatori tra gli elementi.
Ogni stringa deve gia includere il carattere newline se lo vuoi.

#### Modalita "w" vs "a": Sovrascrittura vs Aggiunta

```python
# Modalita "w" - SOVRASCRIVE sempre
with open("log.txt", "w", encoding="utf-8") as log:
    log.write("Prima esecuzione\n")

with open("log.txt", "w", encoding="utf-8") as log:
    log.write("Seconda esecuzione\n")  # la prima riga e sparita!

# log.txt contiene solo: "Seconda esecuzione"

# Modalita "a" - AGGIUNGE in coda
with open("log.txt", "a", encoding="utf-8") as log:
    log.write("Terza esecuzione\n")

with open("log.txt", "a", encoding="utf-8") as log:
    log.write("Quarta esecuzione\n")

# log.txt contiene ora tutte e tre le ultime righe
```

**Regola:** usa `"w"` quando vuoi ricominciare da capo, `"a"` quando vuoi
accumulare (come un file di log che cresce nel tempo).

#### flush() -- Svuotare il Buffer

Python usa un **buffer interno**: non scrive su disco ogni singolo carattere
(troppo lento), ma accumula in memoria e scrive in blocchi. `flush()` forza
la scrittura immediata su disco.

```python
import time

with open("progresso.txt", "w", encoding="utf-8") as out:
    for i in range(5):
        out.write(f"Passo {i+1} completato\n")
        out.flush()      # forza scrittura su disco ora
        time.sleep(0.1)  # simula lavoro
```

**Quando usare `flush()`:** quando un altro processo deve leggere il file
mentre lo stai scrivendo (es. `tail -f` su un log in tempo reale).

#### print() su File

Una tecnica elegante: `print()` accetta il parametro `file=` per redirigere
l'output su un file anziche su schermo.

```python
fatturato = 89432.50

with open("report.txt", "w", encoding="utf-8") as out:
    print("=" * 50, file=out)
    print("REPORT VENDITE 2026", file=out)
    print("=" * 50, file=out)
    print(f"Totale prodotti: {1247}", file=out)
    print(f"Fatturato: {fatturato:.2f} EUR", file=out)
    print(file=out)   # riga vuota
    print("Generato automaticamente.", file=out)
```

**Output nel file:**
```
==================================================
REPORT VENDITE 2026
==================================================
Totale prodotti: 1247
Fatturato: 89432.50 EUR

Generato automaticamente.
```

Il vantaggio: `print()` aggiunge il newline automaticamente e gestisce la
conversione a stringa (non serve `str()`).

#### Esempio Pratico: Generatore di Log

```python
import datetime

def scrivi_log(percorso: str, n_eventi: int) -> None:
    """Scrive n_eventi righe di log in un file."""
    livelli = ["INFO", "WARN", "ERROR", "DEBUG"]
    messaggi = [
        "Richiesta HTTP ricevuta",
        "Buffer quasi pieno",
        "Connessione scaduta",
        "Cache invalidata",
    ]
    with open(percorso, "w", encoding="utf-8") as out:
        for i in range(n_eventi):
            timestamp = datetime.datetime.now().isoformat()
            livello = livelli[i % len(livelli)]
            messaggio = messaggi[i % len(messaggi)]
            out.write(f"{timestamp} {livello:<6} {messaggio}\n")

scrivi_log("app.log", 100)
print("Log scritto. Prime 3 righe:")

with open("app.log", "r", encoding="utf-8") as log:
    for i, riga in enumerate(log):
        if i >= 3:
            break
        print(riga.strip())
```

**Output atteso:**
```
Log scritto. Prime 3 righe:
2026-07-15T10:30:01.123456 INFO   Richiesta HTTP ricevuta
2026-07-15T10:30:01.124001 WARN   Buffer quasi pieno
2026-07-15T10:30:01.124123 ERROR  Connessione scaduta
```

#### Errori Comuni nella Scrittura

```python
# ERRORE 1: dimenticare il newline
with open("test.txt", "w", encoding="utf-8") as out:
    out.write("Prima")
    out.write("Seconda")   # risultato: "PrimaSeconda" su una riga sola!

# ERRORE 2: scrivere numeri senza conversione
with open("test.txt", "w", encoding="utf-8") as out:
    # out.write(42)         # TypeError: write() argument must be str, not int
    out.write(str(42))      # corretto: converte esplicitamente
    out.write(f"{42}")      # corretto: f-string converte automaticamente
    print(42, file=out)     # corretto: print converte automaticamente
```

---

### A5 - Encoding: Perche i Caratteri Stranieri Vanno Male

#### L'Analogia del Dizionario

Un **encoding** e un dizionario che traduce tra caratteri e numeri (byte).
Il problema: esistono molti dizionari diversi, e se il mittente usa uno e
il destinatario usa un altro, il testo diventa incomprensibile.

```
Dizionario ASCII:    conosce solo A-Z, a-z, 0-9, simboli base (128 caratteri)
Dizionario Latin-1:  aggiunge lettere europee (256 caratteri)
Dizionario UTF-8:    il dizionario universale (oltre 1 milione di caratteri)
```

#### UTF-8 -- Il Dizionario Universale

UTF-8 usa 1 byte per i caratteri ASCII (compatibilita retrograda), 2 byte
per lettere europee, 3 byte per caratteri asiatici, 4 byte per emoji e
simboli rari.

```python
# Verifica quanti byte occupa ogni carattere in UTF-8
esempi_ascii = ["A", "e", "u", "o"]
for c in esempi_ascii:
    byte = c.encode("utf-8")
    print(f"'{c}' -> {len(byte)} byte -> {byte}")

# Output:
# 'A' -> 1 byte -> b'A'
# 'e' -> 1 byte -> b'e'
# 'u' -> 1 byte -> b'u'
# 'o' -> 1 byte -> b'o'

# Caratteri accentati e multibyte
testo_utf8 = "cafe"        # 4 byte ASCII
print(f"'cafe' in ASCII -> {len('cafe'.encode('ascii'))} byte")

# La lettera 'e con accento' occupa 2 byte in UTF-8
# La lettera 'u con dieresi' occupa 2 byte in UTF-8
# Il carattere cinese 'zhong' occupa 3 byte in UTF-8
```

#### Specificare l'Encoding in open()

```python
# SEMPRE specificare l'encoding -- non fare affidamento sul default di sistema
# Il default varia: Linux usa UTF-8, Windows usa spesso cp1252 o cp850

with open("testo.txt", "w", encoding="utf-8") as out:
    out.write("Testo con caratteri speciali\n")
    out.write("Accenti: e a u i o con segni diacritici\n")
    out.write("Simboli: euro, copyright, gradi\n")

with open("testo.txt", "r", encoding="utf-8") as inp:
    print(inp.read())
```

#### Il Parametro errors

Cosa fare quando un carattere non puo essere decodificato?
Il parametro `errors` controlla il comportamento:

```python
# Crea un file con byte non validi in UTF-8 (file "sporco")
with open("sporco.bin", "wb") as out:
    out.write("Testo normale ".encode("utf-8"))
    out.write(b"\xe9\xe0")   # byte Latin-1 -- non validi come UTF-8
    out.write(" fine".encode("utf-8"))

# errors="strict" (default) -- lancia UnicodeDecodeError
try:
    with open("sporco.bin", "r", encoding="utf-8", errors="strict") as inp:
        testo = inp.read()
except UnicodeDecodeError:
    print("strict:    ERRORE -> byte non valido trovato")

# errors="ignore" -- salta i byte non decodificabili (perde dati!)
with open("sporco.bin", "r", encoding="utf-8", errors="ignore") as inp:
    testo = inp.read()
print(f"ignore:    '{testo}'")

# errors="replace" -- sostituisce con il carattere di sostituzione Unicode
with open("sporco.bin", "r", encoding="utf-8", errors="replace") as inp:
    testo = inp.read()
print(f"replace:   '{testo}'")

# errors="backslashreplace" -- mostra l'escape del byte
with open("sporco.bin", "r", encoding="utf-8", errors="backslashreplace") as inp:
    testo = inp.read()
print(f"backslash: '{testo}'")
```

**Output atteso:**
```
strict:    ERRORE -> byte non valido trovato
ignore:    'Testo normale  fine'
replace:   'Testo normale �� fine'
backslash: 'Testo normale \xe9\xe0 fine'
```

**Quando usare quale:**
- `"strict"` (default): in produzione, non vuoi perdere dati silenziosamente
- `"ignore"`: analisi di log sporchi dove qualche carattere mancante e accettabile
- `"replace"`: visualizzazione a schermo, si preferisce segnaposto a un crash
- `"backslashreplace"`: debugging di problemi di encoding

#### Rilevare l'Encoding di un File Sconosciuto

```python
# pip install chardet
import chardet

def rileva_encoding(percorso: str) -> dict:
    """Rileva l'encoding di un file leggendo i primi 10KB."""
    with open(percorso, "rb") as inp:
        campione = inp.read(10_000)
    return chardet.detect(campione)

info = rileva_encoding("file_sconosciuto.txt")
print(info)
# Output: {'encoding': 'UTF-8', 'confidence': 0.99, 'language': ''}

if info["confidence"] > 0.8:
    enc = info["encoding"]
    with open("file_sconosciuto.txt", "r", encoding=enc) as inp:
        contenuto = inp.read()
    print(f"Letto con encoding: {enc}")
else:
    print("Encoding incerto -- usa errors='replace' come fallback")
```

#### Il BOM (Byte Order Mark)

Alcuni file UTF-8 iniziano con una sequenza speciale di 3 byte (BOM)
prodotta da Windows/Excel. Il BOM e invisibile ma puo causare problemi:

```python
# Leggere un file UTF-8 con BOM (prodotto da Notepad/Excel Windows)
with open("file_con_bom.txt", "r", encoding="utf-8-sig") as inp:
    contenuto = inp.read()
# "utf-8-sig" rimuove automaticamente il BOM se presente

# Scrivere senza BOM (raccomandato per compatibilita universale)
with open("senza_bom.txt", "w", encoding="utf-8") as out:
    out.write("Testo senza BOM")

# Scrivere con BOM (solo per sistemi Windows legacy)
with open("con_bom.txt", "w", encoding="utf-8-sig") as out:
    out.write("Testo con BOM")
```

#### Errori Comuni e Soluzioni

```python
# UnicodeDecodeError: encoding sbagliato in lettura
try:
    with open("vecchio_file.txt", "r", encoding="utf-8") as inp:
        testo = inp.read()
except UnicodeDecodeError:
    for enc in ["latin-1", "cp1252", "iso-8859-1"]:
        try:
            with open("vecchio_file.txt", "r", encoding=enc) as inp:
                testo = inp.read()
            print(f"Successo con encoding: {enc}")
            break
        except UnicodeDecodeError:
            continue

# UnicodeEncodeError: caratteri non supportati dall'encoding scelto
try:
    with open("test.txt", "w", encoding="ascii") as out:
        out.write("Caratteri accentati")  # non ASCII -- errore!
except UnicodeEncodeError:
    print("ASCII non supporta caratteri non-ASCII")
    with open("test.txt", "w", encoding="utf-8") as out:
        out.write("Caratteri accentati")  # UTF-8 li supporta
```

---

### A6 - pathlib.Path: Il Modo Moderno per i Percorsi

#### Perche NON Usare os.path (Il Modo Vecchio)

Il modulo `os.path` e il modo legacy di lavorare con i percorsi.
E procedurale, verboso, e soggetto a errori di concatenazione:

```python
# Il VECCHIO modo con os.path
import os

home = "/home/utente"
documento = os.path.join(home, "documenti", "report.txt")
print(os.path.basename(documento))    # report.txt
print(os.path.dirname(documento))     # /home/utente/documenti
print(os.path.splitext(documento))    # ('/home/utente/documenti/report', '.txt')
```

```python
# Il NUOVO modo con pathlib -- orientato agli oggetti
from pathlib import Path

documento = Path("/home/utente") / "documenti" / "report.txt"
print(documento.name)      # report.txt
print(documento.parent)    # /home/utente/documenti
print(documento.suffix)    # .txt
```

`pathlib` e la scelta raccomandata in Python moderno. Pensa a un `Path`
come a un oggetto che **sa dove si trova** e conosce tutto di se.

#### Costruire Path: L'Operatore /

L'operatore `/` e sovrascritto per costruire percorsi in modo elegante:

```python
from pathlib import Path

# Percorso assoluto dalla radice
radice = Path("/home/utente")
config = radice / "config" / "app.toml"
print(config)    # /home/utente/config/app.toml

# Path relativo alla directory corrente
progetto = Path.cwd() / "src" / "main.py"
print(progetto)  # /cartella/corrente/src/main.py

# Path dalla home dell'utente (funziona su tutti i sistemi)
documento = Path.home() / "Documenti" / "nota.txt"
print(documento)
# Linux:   /home/utente/Documenti/nota.txt
# Windows: C:\Users\utente\Documenti\nota.txt
```

**Output atteso (Linux):**
```
/home/utente/config/app.toml
/cartella/corrente/src/main.py
/home/utente/Documenti/nota.txt
```

#### Attributi: Tutto Quello che un Path Sa di Se

```python
from pathlib import Path

p = Path("/home/utente/progetti/app/src/main.py")

print(p.name)     # main.py     -- nome completo con estensione
print(p.stem)     # main        -- nome senza estensione
print(p.suffix)   # .py         -- estensione (con il punto)
print(p.parent)   # /home/utente/progetti/app/src
print(p.parts)    # tuple con tutti i componenti del percorso

# File con estensioni multiple (es. archivi compressi)
archivio = Path("backup.tar.gz")
print(archivio.suffix)    # .gz            -- solo l'ultima estensione
print(archivio.suffixes)  # ['.tar', '.gz'] -- tutte le estensioni
print(archivio.stem)      # backup.tar     -- nome senza l'ultima estensione
```

**Output atteso:**
```
main.py
main
.py
/home/utente/progetti/app/src
('/', 'home', 'utente', 'progetti', 'app', 'src', 'main.py')
.gz
['.tar', '.gz']
backup.tar
```

#### Metodi di Verifica

```python
from pathlib import Path

p = Path("/etc/hostname")

print(p.exists())       # True se il percorso esiste sul filesystem
print(p.is_file())      # True se e un file regolare (non dir, non symlink rotto)
print(p.is_dir())       # True se e una directory
print(p.is_symlink())   # True se e un link simbolico

# Informazioni dettagliate sul file
info = p.stat()
print(f"Dimensione: {info.st_size} byte")
print(f"Ultima modifica: {info.st_mtime}")  # timestamp Unix (float)

# Percorso assoluto canonico (risolve ../ e segue symlink)
p_rel = Path("../documenti/file.txt")
print(p_rel.resolve())   # es: /home/utente/documenti/file.txt
```

#### Operazioni: Creare, Rinominare, Eliminare

```python
from pathlib import Path

# Creare un file vuoto (equivalente al comando Unix touch)
nuovo = Path("appunti.txt")
nuovo.touch()
print(nuovo.exists())          # True

# Creare directory (anche intermedie con un'unica chiamata)
cartella = Path("progetto/src/moduli")
cartella.mkdir(parents=True, exist_ok=True)
# parents=True: crea anche le directory intermedie mancanti
# exist_ok=True: nessun errore se la directory esiste gia

# Leggere e scrivere direttamente (scorciatoia per file piccoli)
nota = Path("nota.txt")
nota.write_text("Contenuto della nota", encoding="utf-8")
contenuto = nota.read_text(encoding="utf-8")
print(contenuto)    # Contenuto della nota

# Rinominare (restituisce il nuovo Path)
rinominata = nota.rename("nota_rinominata.txt")

# Eliminare un file
rinominata.unlink()
# Senza errore se il file non esiste (Python 3.8+):
Path("forse_esiste.txt").unlink(missing_ok=True)

# Trasformare il percorso senza toccare il filesystem
p = Path("documento.txt")
print(p.with_suffix(".md"))        # documento.md
print(p.with_suffix(""))           # documento (senza estensione)
print(p.with_stem("relazione"))    # relazione.txt (Python 3.9+)
```

**Output atteso:**
```
True
Contenuto della nota
documento.md
documento
relazione.txt
```

#### glob() e rglob() -- Trovare File con Pattern

```python
from pathlib import Path
import shutil

# Crea una struttura di file di esempio
base = Path("progetto_esempio")
(base / "src").mkdir(parents=True, exist_ok=True)
(base / "test").mkdir(exist_ok=True)
(base / "docs").mkdir(exist_ok=True)

for nome in ["main.py", "utils.py", "config.toml"]:
    (base / "src" / nome).touch()
for nome in ["test_main.py", "test_utils.py"]:
    (base / "test" / nome).touch()
(base / "docs" / "README.md").touch()
(base / "README.md").touch()

# glob() -- cerca nella directory specificata, non ricorsivo per il pattern *
print("=== File .py in src/ ===")
for p in sorted((base / "src").glob("*.py")):
    print(f"  {p.name}")

# rglob() -- ricerca ricorsiva in tutte le sottodirectory
print("\n=== Tutti i file .py nel progetto ===")
for p in sorted(base.rglob("*.py")):
    print(f"  {p.relative_to(base)}")

print("\n=== File di test ===")
for p in sorted(base.rglob("test_*.py")):
    print(f"  {p.relative_to(base)}")

print("\n=== File Markdown ===")
for p in sorted(base.rglob("*.md")):
    print(f"  {p.relative_to(base)}")

shutil.rmtree(base)   # pulizia struttura di esempio
```

**Output atteso:**
```
=== File .py in src/ ===
  main.py
  utils.py

=== Tutti i file .py nel progetto ===
  src/main.py
  src/utils.py
  test/test_main.py
  test/test_utils.py

=== File di test ===
  test/test_main.py
  test/test_utils.py

=== File Markdown ===
  README.md
  docs/README.md
```

#### Esempio Pratico: I File piu Grandi nella Home

```python
from pathlib import Path

def trova_file_grandi(directory: Path, n: int = 5) -> list:
    """Trova gli N file piu grandi in una directory e sottodirectory."""
    file_con_size = []

    for p in directory.rglob("*"):
        if p.is_file():
            try:
                size = p.stat().st_size
                file_con_size.append((p, size))
            except PermissionError:
                continue   # salta i file non accessibili

    file_con_size.sort(key=lambda x: x[1], reverse=True)
    return file_con_size[:n]

home = Path.home()
risultati = trova_file_grandi(home, n=5)

print("I 5 file piu grandi nella home:")
for percorso, dimensione in risultati:
    mb = dimensione / (1024 * 1024)
    print(f"  {mb:8.2f} MB  {percorso.name}")
```

**Output atteso (esempio):**
```
I 5 file piu grandi nella home:
  1024.00 MB  backup.tar.gz
   512.50 MB  video_lezione.mp4
   234.12 MB  database.db
    87.34 MB  immagine_disco.iso
    45.20 MB  archivio.zip
```

#### Errori Comuni con pathlib

```python
from pathlib import Path

# ERRORE 1: confondere Path e stringa con API legacy
p = Path("/home/utente/file.txt")
# Se una libreria accetta solo str, converti esplicitamente:
percorso_str = str(p)

# ERRORE 2: usare / solo con stringhe -- TypeError
# "home" / "utente"       # TypeError: operatore / non supportato tra str e str
Path("home") / "utente"   # corretto: almeno il primo deve essere Path

# ERRORE 3: dimenticare exist_ok e parents per mkdir
# Path("nuova/dir").mkdir()  # FileNotFoundError: "nuova/" non esiste
Path("nuova/dir").mkdir(parents=True, exist_ok=True)  # corretto

# ERRORE 4: confondere is_file() con exists() per i symlink
# Un link simbolico rotto: is_symlink() -> True, exists() -> False
# Verifica sempre entrambi se lavori con link simbolici
```


---

## PARTE B — Strumenti Intermedi per la Gestione File

---

### B1 - shutil: Copiare, Spostare, Archiviare File

#### Analogia: Il Facchino del Trasloco

`shutil` (shell utilities) e il modulo che fa il lavoro pesante con i file:
copia cartelle intere, sposta file, crea archivi ZIP/TAR. Pensa a `shutil`
come al facchino del trasloco -- `pathlib` ti dice dove stai, `shutil` ti
sposta le cose.

#### shutil.copy vs shutil.copy2

```python
import shutil
from pathlib import Path

# Crea un file di esempio
sorgente = Path("originale.txt")
sorgente.write_text("Contenuto originale", encoding="utf-8")

# copy() -- copia contenuto e permessi (ma non metadati tempo)
shutil.copy("originale.txt", "copia_semplice.txt")
shutil.copy("originale.txt", "cartella_dest/")   # copia dentro la cartella

# copy2() -- copia contenuto, permessi E metadati (timestamp, ecc.)
shutil.copy2("originale.txt", "copia_completa.txt")

# Verificare che la copia e avvenuta
print(Path("copia_semplice.txt").exists())   # True
print(Path("copia_completa.txt").read_text("utf-8"))  # Contenuto originale
```

**Output atteso:**
```
True
Contenuto originale
```

**Differenza pratica:** `copy2` e preferibile quando vuoi preservare la data
di modifica originale (utile per backup).

#### shutil.copytree -- Copiare una Directory Intera

```python
import shutil
from pathlib import Path

# Crea struttura di esempio
src = Path("progetto_src")
(src / "src").mkdir(parents=True, exist_ok=True)
(src / "src" / "main.py").write_text("print('hello')", encoding="utf-8")
(src / "src" / "utils.py").write_text("def helper(): pass", encoding="utf-8")
(src / "README.md").write_text("# Progetto", encoding="utf-8")

# Copia l'intera directory
shutil.copytree("progetto_src", "progetto_backup")

# Verifica
for p in Path("progetto_backup").rglob("*"):
    print(f"  {p.relative_to('progetto_backup')}")

# Copia solo certi file (es. solo .py, escludi __pycache__)
shutil.copytree(
    "progetto_src",
    "progetto_solo_python",
    ignore=shutil.ignore_patterns("*.pyc", "__pycache__", "*.log"),
)

# Pulizia
shutil.rmtree("progetto_src")
shutil.rmtree("progetto_backup")
shutil.rmtree("progetto_solo_python")
```

**Output atteso:**
```
  README.md
  src
  src/main.py
  src/utils.py
```

#### shutil.move -- Spostare o Rinominare

```python
import shutil
from pathlib import Path

Path("temp_file.txt").write_text("dati temporanei", encoding="utf-8")

# Spostare in un'altra directory
Path("archivio").mkdir(exist_ok=True)
shutil.move("temp_file.txt", "archivio/temp_file.txt")

# Rinominare (se la destinazione e un percorso diverso nella stessa dir)
shutil.move("archivio/temp_file.txt", "archivio/dati_2026.txt")

print(Path("archivio/dati_2026.txt").exists())   # True
print(Path("temp_file.txt").exists())             # False -- e stato spostato

# Pulizia
shutil.rmtree("archivio")
```

**Output atteso:**
```
True
False
```

#### shutil.rmtree -- Eliminare una Directory con Tutto il Contenuto

```python
import shutil
from pathlib import Path

# Crea struttura
test_dir = Path("da_eliminare")
(test_dir / "subdir").mkdir(parents=True, exist_ok=True)
(test_dir / "subdir" / "file.txt").write_text("testo", encoding="utf-8")

print(f"Prima: {test_dir.exists()}")   # True

# rmtree elimina la directory e TUTTO il suo contenuto
shutil.rmtree("da_eliminare")

print(f"Dopo:  {test_dir.exists()}")   # False
```

**Output atteso:**
```
Prima: True
Dopo:  False
```

**ATTENZIONE:** `rmtree` e irreversibile. Non c'e cestino. Usa con cura
in produzione.

#### shutil.disk_usage e shutil.make_archive

```python
import shutil
from pathlib import Path

# Spazio su disco
utilizzo = shutil.disk_usage("/")
totale_gb = utilizzo.total / (1024 ** 3)
usato_gb  = utilizzo.used  / (1024 ** 3)
libero_gb = utilizzo.free  / (1024 ** 3)
print(f"Totale: {totale_gb:.1f} GB")
print(f"Usato:  {usato_gb:.1f} GB")
print(f"Libero: {libero_gb:.1f} GB")

# Creare un archivio ZIP di una directory
Path("dati").mkdir(exist_ok=True)
Path("dati/file1.txt").write_text("primo", encoding="utf-8")
Path("dati/file2.txt").write_text("secondo", encoding="utf-8")

# Crea backup.zip con il contenuto di "dati/"
shutil.make_archive("backup", "zip", "dati")
print(f"Archivio creato: {Path('backup.zip').exists()}")   # True
print(f"Dimensione: {Path('backup.zip').stat().st_size} byte")

# Estrarre un archivio
shutil.unpack_archive("backup.zip", "dati_estratti")
print("File estratti:")
for p in Path("dati_estratti").rglob("*"):
    if p.is_file():
        print(f"  {p.name}")

# Pulizia
shutil.rmtree("dati")
shutil.rmtree("dati_estratti")
Path("backup.zip").unlink()
```

**Output atteso:**
```
Totale: 500.0 GB
Usato:  120.3 GB
Libero: 379.7 GB
Archivio creato: True
Dimensione: 284 byte
File estratti:
  file1.txt
  file2.txt
```

---

### B2 - tempfile: File e Directory Temporanee

#### Analogia: Il Foglio da Brutta Copia

Un file temporaneo e come la brutta copia che scarti dopo aver finito:
serve durante l'elaborazione, poi sparisce. `tempfile` crea file in posizioni
sicure, con nomi univoci, che vengono eliminati automaticamente.

#### NamedTemporaryFile -- File Temporaneo con Nome

```python
import tempfile
from pathlib import Path

# Crea un file temporaneo che si elimina automaticamente all'uscita del with
with tempfile.NamedTemporaryFile(
    mode="w",
    suffix=".txt",
    prefix="mia_app_",
    encoding="utf-8",
    delete=True,    # True = elimina alla chiusura (default)
) as tmp:
    print(f"Path temporaneo: {tmp.name}")
    tmp.write("Dati temporanei da processare\n")
    tmp.write("Seconda riga di dati\n")
    tmp.flush()   # assicura che i dati siano su disco

    # Leggi il file appena scritto
    contenuto = Path(tmp.name).read_text(encoding="utf-8")
    print(f"Contenuto: {contenuto.strip()}")

# Dopo il with, il file e stato eliminato automaticamente
print(f"File esiste ancora? {Path(tmp.name).exists()}")   # False
```

**Output atteso:**
```
Path temporaneo: /tmp/mia_app_xyz12345.txt
Contenuto: Dati temporanei da processare
Seconda riga di dati
File esiste ancora? False
```

#### NamedTemporaryFile con delete=False

```python
import tempfile
from pathlib import Path

# delete=False: il file persiste dopo la chiusura (lo elimini tu)
with tempfile.NamedTemporaryFile(
    mode="wb",         # modalita binaria
    suffix=".bin",
    delete=False,
) as tmp:
    percorso_tmp = Path(tmp.name)
    tmp.write(b"\x00\x01\x02\x03\x04")
    print(f"Scritti 5 byte in: {percorso_tmp}")

# Il file esiste ancora dopo il with
print(f"File esiste: {percorso_tmp.exists()}")   # True
print(f"Contenuto (hex): {percorso_tmp.read_bytes().hex()}")

# Pulisci manualmente
percorso_tmp.unlink()
print(f"File eliminato: {not percorso_tmp.exists()}")   # True
```

**Output atteso:**
```
Scritti 5 byte in: /tmp/tmpXXXXXX.bin
File esiste: True
Contenuto (hex): 0001020304
File eliminato: True
```

#### TemporaryDirectory -- Directory Temporanea

```python
import tempfile
from pathlib import Path
import shutil

# Crea una directory temporanea (eliminata automaticamente all'uscita del with)
with tempfile.TemporaryDirectory(prefix="mia_app_") as tmpdir:
    base = Path(tmpdir)
    print(f"Directory temporanea: {base}")

    # Lavora nella directory temporanea
    (base / "input").mkdir()
    (base / "output").mkdir()
    (base / "input" / "dati.txt").write_text("input data", encoding="utf-8")

    # Simula elaborazione
    dati = (base / "input" / "dati.txt").read_text(encoding="utf-8")
    risultato = dati.upper()
    (base / "output" / "risultato.txt").write_text(risultato, encoding="utf-8")

    print("File creati:")
    for p in base.rglob("*"):
        if p.is_file():
            print(f"  {p.relative_to(base)}")

# La directory e tutto il contenuto sono stati eliminati
print(f"Dir esiste ancora? {Path(tmpdir).exists()}")   # False
```

**Output atteso:**
```
Directory temporanea: /tmp/mia_app_XXXXXXXX
File creati:
  input/dati.txt
  output/risultato.txt
Dir esiste ancora? False
```

#### SpooledTemporaryFile -- Buffer in Memoria con Overflow su Disco

```python
import tempfile

# Il file rimane in memoria RAM finche non supera max_size
# Poi si riversa automaticamente su disco (senza che tu lo sappia)
with tempfile.SpooledTemporaryFile(
    max_size=1024 * 1024,   # 1 MB in memoria, poi su disco
    mode="w",
    encoding="utf-8",
) as spool:
    spool.write("Dati leggeri\n")   # rimane in RAM
    print(f"In memoria: {not hasattr(spool, 'name')}")

    # Simula dati grandi che superano il limite
    spool.write("X" * (2 * 1024 * 1024))   # 2 MB -- passa su disco

    spool.seek(0)
    prima_riga = spool.readline()
    print(f"Prima riga: {prima_riga.strip()}")
```

**Output atteso:**
```
In memoria: True
Prima riga: Dati leggeri
```

**Quando usare SpooledTemporaryFile:** quando non sai in anticipo se i dati
saranno piccoli (RAM) o grandi (disco). Ideale per upload HTTP, elaborazione
di report variabili.

---

### B3 - JSON: Salvare e Caricare Strutture Dati

#### Analogia: Il Modulo Postale Internazionale

JSON (JavaScript Object Notation) e come il modulo postale internazionale:
un formato standard che tutti capiscono, indipendentemente dal linguaggio o
sistema. Python dict e list vanno e vengono facilmente.

#### json.dump e json.load (File)

```python
import json
from pathlib import Path

# Struttura dati Python
configurazione = {
    "versione": "2.0",
    "database": {
        "host": "localhost",
        "porta": 5432,
        "nome": "app_db",
    },
    "funzionalita": ["autenticazione", "notifiche", "report"],
    "debug": False,
    "timeout_secondi": 30,
}

# Scrivi su file (dump = dizionario -> file)
with open("config.json", "w", encoding="utf-8") as out:
    json.dump(
        configurazione,
        out,
        indent=2,           # indentazione per leggibilita
        ensure_ascii=False, # permette caratteri non-ASCII (es. accenti)
    )

print("config.json scritto:")
print(Path("config.json").read_text(encoding="utf-8"))

# Leggi dal file (load = file -> dizionario)
with open("config.json", "r", encoding="utf-8") as inp:
    dati_letti = json.load(inp)

print(f"Versione: {dati_letti['versione']}")
print(f"Host DB:  {dati_letti['database']['host']}")
print(f"Funzioni: {dati_letti['funzionalita']}")
```

**Output atteso:**
```json
{
  "versione": "2.0",
  "database": {
    "host": "localhost",
    "porta": 5432,
    "nome": "app_db"
  },
  "funzionalita": ["autenticazione", "notifiche", "report"],
  "debug": false,
  "timeout_secondi": 30
}
Versione: 2.0
Host DB:  localhost
Funzioni: ['autenticazione', 'notifiche', 'report']
```

#### json.dumps e json.loads (Stringa)

```python
import json

dati = {"nome": "Alice", "punteggio": 98.5, "superato": True}

# dumps = dizionario -> stringa JSON
json_str = json.dumps(dati, ensure_ascii=False)
print(f"JSON stringa: {json_str}")
# Output: {"nome": "Alice", "punteggio": 98.5, "superato": true}

# loads = stringa JSON -> dizionario
ripristinato = json.loads(json_str)
print(f"Tipo: {type(ripristinato)}")     # dict
print(f"Nome: {ripristinato['nome']}")   # Alice
```

**Output atteso:**
```
JSON stringa: {"nome": "Alice", "punteggio": 98.5, "superato": true}
Tipo: <class 'dict'>
Nome: Alice
```

#### JSONEncoder Personalizzato per Tipi Non Standard

```python
import json
import datetime
from pathlib import Path

class EncoderEsteso(json.JSONEncoder):
    """Gestisce datetime, Path e set che il JSON standard non supporta."""

    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return {"__tipo__": "datetime", "valore": obj.isoformat()}
        if isinstance(obj, datetime.date):
            return {"__tipo__": "date", "valore": obj.isoformat()}
        if isinstance(obj, Path):
            return {"__tipo__": "path", "valore": str(obj)}
        if isinstance(obj, set):
            return {"__tipo__": "set", "valore": sorted(obj)}
        return super().default(obj)

# Dati che JSON standard non sa serializzare
evento = {
    "nome": "Riunione",
    "data": datetime.datetime(2026, 7, 15, 10, 30),
    "cartella": Path("/home/utente/riunioni"),
    "partecipanti": {"Alice", "Bob", "Carlo"},
}

json_str = json.dumps(evento, cls=EncoderEsteso, indent=2, ensure_ascii=False)
print(json_str)
```

**Output atteso:**
```json
{
  "nome": "Riunione",
  "data": {
    "__tipo__": "datetime",
    "valore": "2026-07-15T10:30:00"
  },
  "cartella": {
    "__tipo__": "path",
    "valore": "/home/utente/riunioni"
  },
  "partecipanti": {
    "__tipo__": "set",
    "valore": ["Alice", "Bob", "Carlo"]
  }
}
```

#### Decoder Personalizzato con object_hook

```python
import json
import datetime
from pathlib import Path

def decodifica_tipi(diz: dict):
    """Ricostruisce i tipi speciali dal JSON."""
    if "__tipo__" not in diz:
        return diz
    tipo = diz["__tipo__"]
    valore = diz["valore"]
    if tipo == "datetime":
        return datetime.datetime.fromisoformat(valore)
    if tipo == "date":
        return datetime.date.fromisoformat(valore)
    if tipo == "path":
        return Path(valore)
    if tipo == "set":
        return set(valore)
    return diz

json_input = '''
{
  "nome": "Riunione",
  "data": {"__tipo__": "datetime", "valore": "2026-07-15T10:30:00"},
  "cartella": {"__tipo__": "path", "valore": "/home/utente/riunioni"},
  "partecipanti": {"__tipo__": "set", "valore": ["Alice", "Bob", "Carlo"]}
}
'''

evento = json.loads(json_input, object_hook=decodifica_tipi)
print(f"Nome: {evento['nome']}")
print(f"Data: {evento['data']} (tipo: {type(evento['data']).__name__})")
print(f"Cartella: {evento['cartella']} (tipo: {type(evento['cartella']).__name__})")
print(f"Partecipanti: {evento['partecipanti']} (tipo: {type(evento['partecipanti']).__name__})")
```

**Output atteso:**
```
Nome: Riunione
Data: 2026-07-15 10:30:00 (tipo: datetime)
Cartella: /home/utente/riunioni (tipo: PosixPath)
Partecipanti: {'Alice', 'Bob', 'Carlo'} (tipo: set)
```

#### Errori Comuni con JSON

```python
import json

# TypeError: tipo non serializzabile
dati = {"data": set([1, 2, 3])}   # set non supportato
try:
    json.dumps(dati)
except TypeError as e:
    print(f"Errore: {e}")
    # Soluzione: converti a list
    dati["data"] = list(dati["data"])
    print(json.dumps(dati))

# JSONDecodeError: JSON malformato
json_rotto = '{"nome": "Alice", "eta": }'   # valore mancante
try:
    json.loads(json_rotto)
except json.JSONDecodeError as e:
    print(f"JSON malformato: {e}")
```

---

### B4 - CSV: File di Testo Tabulari

#### Analogia: Il Foglio Excel in Formato Testo

CSV (Comma-Separated Values) e un foglio di calcolo salvato come testo puro:
ogni riga e una riga della tabella, le colonne sono separate da virgola (o
punto e virgola). Tutti i programmi lo capiscono: Excel, Google Sheets, database.

#### Leggere CSV con csv.reader

```python
import csv
from pathlib import Path

# Crea un CSV di esempio
Path("vendite.csv").write_text(
    "prodotto,quantita,prezzo,categoria\n"
    "Laptop,5,899.99,Elettronica\n"
    "Mouse,20,29.99,Elettronica\n"
    "Scrivania,3,249.00,Arredamento\n"
    "Sedia,8,149.50,Arredamento\n",
    encoding="utf-8",
)

# Leggi con csv.reader
# IMPORTANTE: newline="" obbligatorio su Windows per evitare righe vuote extra
with open("vendite.csv", "r", encoding="utf-8", newline="") as inp:
    reader = csv.reader(inp)
    intestazione = next(reader)   # leggi la prima riga come intestazione
    print(f"Colonne: {intestazione}")

    totale_vendite = 0.0
    for riga in reader:
        prodotto, quantita, prezzo, categoria = riga
        subtotale = int(quantita) * float(prezzo)
        totale_vendite += subtotale
        print(f"  {prodotto}: {int(quantita)} x {float(prezzo):.2f} = {subtotale:.2f} EUR")

    print(f"Totale: {totale_vendite:.2f} EUR")
```

**Output atteso:**
```
Colonne: ['prodotto', 'quantita', 'prezzo', 'categoria']
  Laptop: 5 x 899.99 = 4499.95 EUR
  Mouse: 20 x 29.99 = 599.80 EUR
  Scrivania: 3 x 249.00 = 747.00 EUR
  Sedia: 8 x 149.50 = 1196.00 EUR
Totale: 7042.75 EUR
```

#### Scrivere CSV con csv.writer

```python
import csv

dati = [
    ["nome", "cognome", "citta", "punteggio"],
    ["Alice", "Rossi", "Milano", 98],
    ["Bob", "Verdi", "Roma", 87],
    ["Carlo", "Bianchi", "Torino", 92],
]

with open("studenti.csv", "w", encoding="utf-8", newline="") as out:
    writer = csv.writer(out)
    writer.writerows(dati)   # scrive tutte le righe in una chiamata

# Verifica
with open("studenti.csv", "r", encoding="utf-8") as inp:
    print(inp.read())
```

**Output atteso:**
```
nome,cognome,citta,punteggio
Alice,Rossi,Milano,98
Bob,Verdi,Roma,87
Carlo,Bianchi,Torino,92
```

#### DictReader e DictWriter -- Lavora con Dizionari

```python
import csv

# DictReader: ogni riga e un dizionario (chiave = intestazione)
with open("vendite.csv", "r", encoding="utf-8", newline="") as inp:
    reader = csv.DictReader(inp)
    print(f"Campi: {reader.fieldnames}")

    per_categoria = {}
    for riga in reader:
        cat = riga["categoria"]
        prezzo = float(riga["prezzo"])
        qtà = int(riga["quantita"])
        per_categoria[cat] = per_categoria.get(cat, 0) + prezzo * qtà

print("Vendite per categoria:")
for cat, totale in per_categoria.items():
    print(f"  {cat}: {totale:.2f} EUR")
```

**Output atteso:**
```
Campi: ['prodotto', 'quantita', 'prezzo', 'categoria']
Vendite per categoria:
  Elettronica: 5099.75 EUR
  Arredamento: 1943.00 EUR
```

```python
import csv

# DictWriter: scrivi dizionari su CSV
prodotti = [
    {"codice": "P001", "nome": "Laptop Pro", "stock": 5, "prezzo": 1299.00},
    {"codice": "P002", "nome": "Mouse Wireless", "stock": 50, "prezzo": 39.99},
    {"codice": "P003", "nome": "Tastiera Meccanica", "stock": 15, "prezzo": 129.90},
]

campi = ["codice", "nome", "stock", "prezzo"]

with open("inventario.csv", "w", encoding="utf-8", newline="") as out:
    writer = csv.DictWriter(out, fieldnames=campi)
    writer.writeheader()    # scrive la riga di intestazione
    writer.writerows(prodotti)

print("inventario.csv:")
with open("inventario.csv", "r", encoding="utf-8") as inp:
    print(inp.read())
```

**Output atteso:**
```
inventario.csv:
codice,nome,stock,prezzo
P001,Laptop Pro,5,1299.0
P002,Mouse Wireless,50,39.99
P003,Tastiera Meccanica,15,129.9
```

#### Gestire CSV con Separatori Diversi (Dialetti)

```python
import csv

# CSV europeo: separatore ; (non ,), decimale con virgola
dati_europei = [
    ["Prodotto", "Quantita", "Prezzo EUR"],
    ["Laptop", "5", "899,99"],
    ["Mouse", "20", "29,99"],
]

with open("europeo.csv", "w", encoding="utf-8", newline="") as out:
    writer = csv.writer(out, delimiter=";")
    writer.writerows(dati_europei)

# Lettura con separatore personalizzato
with open("europeo.csv", "r", encoding="utf-8", newline="") as inp:
    reader = csv.reader(inp, delimiter=";")
    for riga in reader:
        print(riga)
```

**Output atteso:**
```
['Prodotto', 'Quantita', 'Prezzo EUR']
['Laptop', '5', '899,99']
['Mouse', '20', '29,99']
```

#### Perche newline="" e Obbligatorio

```python
# Su Windows, senza newline="", csv.writer aggiunge \r\r\n invece di \r\n
# risultando in righe vuote extra nel file

# SBAGLIATO (su Windows):
# with open("file.csv", "w", encoding="utf-8") as out:    # manca newline=""
#     writer = csv.writer(out)

# CORRETTO:
with open("file.csv", "w", encoding="utf-8", newline="") as out:
    writer = csv.writer(out)
    writer.writerow(["a", "b", "c"])
```

---

### B5 - YAML: File di Configurazione Leggibili

#### Analogia: Il Modulo di Configurazione a Parole

YAML e come un modulo di configurazione scritto in linguaggio quasi naturale:
piu leggibile di JSON (niente virgolette, commenti permessi), ideale per
file di configurazione come `docker-compose.yml` o `config.yaml`.

**ATTENZIONE DI SICUREZZA:** Non usare MAI `yaml.load()` su dati non fidati
-- e vulnerabile a esecuzione di codice arbitrario (RCE). Usa SEMPRE
`yaml.safe_load()`.

#### Installazione

```bash
pip install pyyaml
```

#### yaml.safe_load -- Leggere YAML

```python
import yaml
from pathlib import Path

# Crea un file YAML di configurazione
config_yaml = """
# Configurazione applicazione (i commenti sono permessi in YAML!)
versione: "2.0"
ambiente: produzione

database:
  host: localhost
  porta: 5432
  nome: app_db
  pool_size: 10

server:
  host: 0.0.0.0
  porta: 8080
  debug: false
  workers: 4

funzionalita:
  - autenticazione
  - notifiche
  - report
  - audit_log

limiti:
  max_upload_mb: 50
  timeout_secondi: 30
  retry_tentativi: 3
"""

Path("config.yaml").write_text(config_yaml, encoding="utf-8")

# Leggi con safe_load (MAI yaml.load senza Loader -- RCE!)
with open("config.yaml", "r", encoding="utf-8") as inp:
    config = yaml.safe_load(inp)

print(f"Versione: {config['versione']}")
print(f"Ambiente: {config['ambiente']}")
print(f"DB host:  {config['database']['host']}")
print(f"Workers:  {config['server']['workers']}")
print(f"Features: {config['funzionalita']}")
print(f"Timeout:  {config['limiti']['timeout_secondi']} s")
```

**Output atteso:**
```
Versione: 2.0
Ambiente: produzione
DB host:  localhost
Workers:  4
Features: ['autenticazione', 'notifiche', 'report', 'audit_log']
Timeout:  30 s
```

#### yaml.safe_dump -- Scrivere YAML

```python
import yaml

dati = {
    "nome": "Alice Rossi",
    "ruolo": "admin",
    "permessi": ["lettura", "scrittura", "amministrazione"],
    "attivo": True,
    "sessioni_max": 3,
}

# Scrivi su file
with open("utente.yaml", "w", encoding="utf-8") as out:
    yaml.safe_dump(
        dati,
        out,
        default_flow_style=False,   # stile blocco (piu leggibile)
        allow_unicode=True,          # permetti caratteri non-ASCII
        sort_keys=True,              # ordina le chiavi alfabeticamente
    )

# Mostra il risultato
with open("utente.yaml", "r", encoding="utf-8") as inp:
    print(inp.read())
```

**Output atteso:**
```yaml
attivo: true
nome: Alice Rossi
permessi:
- lettura
- scrittura
- amministrazione
ruolo: admin
sessioni_max: 3
```

#### YAML vs JSON vs TOML: Confronto

| Caratteristica       | JSON              | YAML              | TOML              |
|----------------------|-------------------|-------------------|-------------------|
| Commenti             | No                | Si                | Si                |
| Leggibilita          | Media             | Alta              | Alta              |
| Tipi supportati      | 6 base            | Ricchi            | Ricchi            |
| Standard Python      | Si (json)         | No (pyyaml)       | Si (tomllib 3.11) |
| Uso principale       | API, scambio dati | Config, DevOps    | Config Python     |
| Rischio sicurezza    | Basso             | Alto (load())     | Basso             |

#### Errori Comuni con YAML

```python
import yaml

# ERRORE GRAVE: yaml.load senza Loader -- rischio RCE!
# yaml.load(file)                     # SBAGLIATO e pericoloso
# yaml.load(file, Loader=yaml.Loader) # SBAGLIATO -- Loader pieno e insicuro
yaml.safe_load(file)                   # CORRETTO -- solo tipi sicuri

# ERRORE: indentazione inconsistente (YAML e indentazione-sensitivo)
yaml_rotto = """
chiave1: valore1
 chiave2: valore2  # indentazione sbagliata
"""
try:
    yaml.safe_load(yaml_rotto)
except yaml.YAMLError as e:
    print(f"Errore YAML: {e}")

# NOTA: YAML interpreta certi valori in modo sorprendente
# on, off, yes, no, true, false -> bool (NON string!)
# 1.0 -> float
# 2026-07-15 -> datetime.date (attenzione!)
dati = yaml.safe_load("valore: on")
print(type(dati["valore"]))   # bool, non str!
```


---

### B6 - TOML: Il Formato di Configurazione di Python

#### Analogia: La Scheda Tecnica Standardizzata

TOML (Tom's Obvious, Minimal Language) e come una scheda tecnica standardizzata:
chiaro, non ambiguo, progettato specificamente per file di configurazione.
E il formato usato da `pyproject.toml`, `Cargo.toml` (Rust), e altri strumenti
moderni. Da Python 3.11, `tomllib` fa parte della libreria standard.

**Limitazione:** `tomllib` supporta solo la lettura. Per scrivere TOML,
usa `tomli-w` (pip install tomli-w).

#### Leggere TOML con tomllib (Python 3.11+)

```python
import tomllib   # stdlib da Python 3.11
from pathlib import Path

# Crea un file TOML di configurazione
config_toml = """
# Configurazione progetto

[progetto]
nome = "mia-app"
versione = "1.2.0"
autori = ["Alice Rossi <alice@example.com>", "Bob Verdi <bob@example.com>"]
python_richiesto = ">=3.11"

[dipendenze]
richieste = ["requests>=2.28", "pydantic>=2.0"]
dev = ["pytest>=7.0", "mypy>=1.0", "black"]

[database]
host = "localhost"
porta = 5432
nome = "app_db"
ssl = true

[[server]]
nome = "primario"
host = "10.0.0.1"
porta = 8080

[[server]]
nome = "secondario"
host = "10.0.0.2"
porta = 8081
"""

Path("config.toml").write_text(config_toml, encoding="utf-8")

# TOML deve essere letto in modalita binaria
with open("config.toml", "rb") as inp:
    config = tomllib.load(inp)

print(f"Progetto: {config['progetto']['nome']} v{config['progetto']['versione']}")
print(f"Autori: {config['progetto']['autori']}")
print(f"DB host: {config['database']['host']}")
print(f"Server: {[s['nome'] for s in config['server']]}")
```

**Output atteso:**
```
Progetto: mia-app v1.2.0
Autori: ['Alice Rossi <alice@example.com>', 'Bob Verdi <bob@example.com>']
DB host: localhost
Server: ['primario', 'secondario']
```

#### Scrivere TOML con tomli-w

```python
# pip install tomli-w
import tomli_w

config = {
    "progetto": {
        "nome": "nuovo-progetto",
        "versione": "0.1.0",
    },
    "database": {
        "host": "localhost",
        "porta": 5432,
        "ssl": False,
    },
    "funzionalita": ["auth", "logging", "metrics"],
}

# Scrivi in modalita binaria
with open("nuovo.toml", "wb") as out:
    tomli_w.dump(config, out)

# Verifica
with open("nuovo.toml", "r", encoding="utf-8") as inp:
    print(inp.read())
```

**Output atteso:**
```toml
[progetto]
nome = "nuovo-progetto"
versione = "0.1.0"

[database]
host = "localhost"
porta = 5432
ssl = false

funzionalita = ["auth", "logging", "metrics"]
```

---

### B7 - mmap: File Mappati in Memoria

#### Analogia: La Finestra sul File

`mmap` (memory-mapped file) e come aprire una finestra direttamente sul file:
invece di caricare tutto in memoria, il sistema operativo mappa il file nello
spazio degli indirizzi del processo. Puoi leggere e modificare il file come se
fosse un array di byte in memoria, ma il SO gestisce il caricamento lazily.

#### Lettura con mmap.ACCESS_READ

```python
import mmap
import re
from pathlib import Path

# Crea un file di testo di esempio (grande)
contenuto = "ERRORE: connessione rifiutata\n" * 1000
contenuto += "INFO: server avviato\n" * 500
contenuto += "WARN: memoria al 90%\n" * 200
Path("server.log").write_text(contenuto, encoding="utf-8")

# Conta le occorrenze di "ERRORE" senza caricare tutto in memoria
with open("server.log", "rb") as fp:
    with mmap.mmap(fp.fileno(), length=0, access=mmap.ACCESS_READ) as mm:
        print(f"Dimensione file: {mm.size()} byte")

        # Cerca con find() -- come su una stringa ma su file
        pos = mm.find(b"ERRORE")
        print(f"Prima occorrenza 'ERRORE' a: byte {pos}")

        # Cerca tutte le occorrenze con regex
        pattern = re.compile(b"ERRORE")
        conteggio = len(pattern.findall(mm))
        print(f"Totale occorrenze 'ERRORE': {conteggio}")

        # Leggi una sezione specifica senza caricare tutto
        mm.seek(0)
        prima_riga = mm.readline()
        print(f"Prima riga: {prima_riga.decode('utf-8').strip()}")

Path("server.log").unlink()
```

**Output atteso:**
```
Dimensione file: 43700 byte
Prima occorrenza 'ERRORE' a: byte 0
Totale occorrenze 'ERRORE': 1000
Prima riga: ERRORE: connessione rifiutata
```

#### Modifica con mmap.ACCESS_WRITE

```python
import mmap
from pathlib import Path

# Crea un file con dati da modificare
Path("config.bin").write_bytes(b"versione=1.0 stato=attivo  ")

with open("config.bin", "r+b") as fp:
    with mmap.mmap(fp.fileno(), length=0) as mm:
        print(f"Prima: {bytes(mm[:]).decode('ascii')}")

        # Modifica "1.0" -> "2.0" in posizione
        pos = mm.find(b"1.0")
        if pos != -1:
            mm[pos:pos+3] = b"2.0"

        print(f"Dopo:  {bytes(mm[:]).decode('ascii')}")

Path("config.bin").unlink()
```

**Output atteso:**
```
Prima: versione=1.0 stato=attivo  
Dopo:  versione=2.0 stato=attivo  
```

**Quando usare mmap:**
- File molto grandi (> 100 MB) dove non vuoi caricare tutto in RAM
- Ricerca di pattern su file binari o log enormi
- Elaborazione di file in finestre scorrevoli
- Accesso random a sezioni di file (database semplici, indici)

---

### B8 - File Locking: Accesso Esclusivo ai File

#### Analogia: Il Semaforo sulla Porta del Bagno

Quando piu processi accedono allo stesso file, puo succedere il caos: due
scritture simultanee corrompono il file. Un lock e come il semaforo sul bagno:
solo uno entra alla volta.

#### filelock -- Cross-Platform e Semplice

```python
# pip install filelock
import filelock
from pathlib import Path
import time

def aggiorna_contatore(percorso_lock: str, percorso_file: str) -> int:
    """Aggiorna un contatore in modo sicuro da piu processi."""
    lock = filelock.FileLock(percorso_lock, timeout=10)

    with lock:   # acquisisce il lock -- altri processi aspettano
        # Leggi il valore attuale
        if Path(percorso_file).exists():
            valore = int(Path(percorso_file).read_text(encoding="utf-8").strip())
        else:
            valore = 0

        # Aggiorna
        valore += 1
        Path(percorso_file).write_text(str(valore), encoding="utf-8")
        return valore
    # Il lock viene rilasciato automaticamente all'uscita del with

# Simula 5 aggiornamenti sequenziali
for i in range(5):
    nuovo_valore = aggiorna_contatore("contatore.lock", "contatore.txt")
    print(f"Aggiornamento {i+1}: valore = {nuovo_valore}")

# Pulizia
Path("contatore.txt").unlink(missing_ok=True)
Path("contatore.lock").unlink(missing_ok=True)
```

**Output atteso:**
```
Aggiornamento 1: valore = 1
Aggiornamento 2: valore = 2
Aggiornamento 3: valore = 3
Aggiornamento 4: valore = 4
Aggiornamento 5: valore = 5
```

#### Timeout e Lock Non Bloccante

```python
import filelock

lock = filelock.FileLock("risorsa.lock", timeout=5)  # aspetta max 5 secondi

try:
    with lock:
        print("Lock acquisito -- elaboro la risorsa")
        # ... lavoro ...
except filelock.Timeout:
    print("Impossibile acquisire il lock entro 5 secondi")
    # Gestisci il caso: riprova piu tardi, salta, o segnala errore

finally:
    # Pulizia garantita anche in caso di eccezione
    import os
    for nome in ["risorsa.lock"]:
        if os.path.exists(nome):
            os.unlink(nome)
```

---

### B9 - watchdog: Monitorare i Cambiamenti del Filesystem

#### Analogia: Il Guardiano del Castello

`watchdog` e come un guardiano che sorveglia un castello (directory) e ti
avvisa di ogni movimento: qualcuno ha creato un file, modificato un documento,
cancellato una cartella. Utile per hot-reload, sincronizzazione, automazione.

```bash
pip install watchdog
```

#### Gestore Base degli Eventi

```python
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class MioGestore(FileSystemEventHandler):
    """Gestisce gli eventi del filesystem."""

    def on_created(self, event):
        if not event.is_directory:
            print(f"CREATO:    {event.src_path}")

    def on_modified(self, event):
        if not event.is_directory:
            print(f"MODIFICATO: {event.src_path}")

    def on_deleted(self, event):
        print(f"ELIMINATO: {event.src_path}")

    def on_moved(self, event):
        print(f"SPOSTATO:  {event.src_path} -> {event.dest_path}")

# Avvia il monitor su una directory
cartella_da_monitorare = Path("monitora_questa")
cartella_da_monitorare.mkdir(exist_ok=True)

gestore = MioGestore()
observer = Observer()
observer.schedule(gestore, str(cartella_da_monitorare), recursive=True)
observer.start()

print(f"Monitoraggio avviato su: {cartella_da_monitorare}")

try:
    # Simula attivita sulla directory (in un'app reale, questo sarebbe un loop)
    time.sleep(0.1)
    (cartella_da_monitorare / "test.txt").write_text("primo", encoding="utf-8")
    time.sleep(0.1)
    (cartella_da_monitorare / "test.txt").write_text("secondo", encoding="utf-8")
    time.sleep(0.1)
    (cartella_da_monitorare / "test.txt").unlink()
    time.sleep(0.2)   # aspetta l'elaborazione degli eventi
finally:
    observer.stop()
    observer.join()
    import shutil
    shutil.rmtree(cartella_da_monitorare)
```

**Output atteso:**
```
Monitoraggio avviato su: monitora_questa
CREATO:    monitora_questa/test.txt
MODIFICATO: monitora_questa/test.txt
ELIMINATO: monitora_questa/test.txt
```

#### PatternMatchingEventHandler -- Filtra per Pattern

```python
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
import time, shutil
from pathlib import Path

# Monitora solo file Python e JSON, ignora i file temporanei
gestore = PatternMatchingEventHandler(
    patterns=["*.py", "*.json"],
    ignore_patterns=["*.tmp", "*.pyc", "*/__pycache__/*"],
    ignore_directories=True,
    case_sensitive=False,
)

def on_any_event(event):
    print(f"Evento: {event.event_type:12} {Path(event.src_path).name}")

gestore.on_any_event = on_any_event

cartella = Path("progetto")
cartella.mkdir(exist_ok=True)

observer = Observer()
observer.schedule(gestore, str(cartella), recursive=True)
observer.start()

try:
    time.sleep(0.1)
    (cartella / "main.py").write_text("print('hello')", encoding="utf-8")
    (cartella / "config.json").write_text('{}', encoding="utf-8")
    (cartella / "temp.tmp").write_text("ignorato", encoding="utf-8")
    time.sleep(0.3)
finally:
    observer.stop()
    observer.join()
    shutil.rmtree(cartella)
```

**Output atteso:**
```
Evento: created      main.py
Evento: created      config.json
```
(temp.tmp e ignorato perche non corrisponde ai pattern)

---

### B10 - aiofiles: I/O Asincrono con asyncio

#### Analogia: Il Cameriere che Serve Piu Tavoli

Nella ristorazione tradizionale (I/O sincrono), il cameriere porta l'ordine
in cucina e aspetta che sia pronto prima di servire il tavolo successivo.
Con l'I/O asincrono, il cameriere lascia l'ordine in cucina e nel frattempo
serve altri tavoli: quando il piatto e pronto, torna a ritirarlo.

```bash
pip install aiofiles
```

#### Lettura e Scrittura Asincrone

```python
import asyncio
import aiofiles
from pathlib import Path

async def leggi_file(percorso: str) -> str:
    """Legge un file in modo asincrono."""
    async with aiofiles.open(percorso, "r", encoding="utf-8") as inp:
        contenuto = await inp.read()
    return contenuto

async def scrivi_file(percorso: str, contenuto: str) -> None:
    """Scrive un file in modo asincrono."""
    async with aiofiles.open(percorso, "w", encoding="utf-8") as out:
        await out.write(contenuto)

async def main():
    # Scrittura asincrona
    await scrivi_file("async_test.txt", "Contenuto scritto in modo asincrono\n")
    print("Scritto.")

    # Lettura asincrona
    testo = await leggi_file("async_test.txt")
    print(f"Letto: {testo.strip()}")

    # Leggi piu file in parallelo!
    for i in range(3):
        await scrivi_file(f"parallelo_{i}.txt", f"File numero {i}\n")

    # Leggi tutti e 3 contemporaneamente
    tasks = [leggi_file(f"parallelo_{i}.txt") for i in range(3)]
    risultati = await asyncio.gather(*tasks)
    for i, r in enumerate(risultati):
        print(f"parallelo_{i}.txt: {r.strip()}")

    # Pulizia
    for nome in ["async_test.txt", "parallelo_0.txt", "parallelo_1.txt", "parallelo_2.txt"]:
        Path(nome).unlink(missing_ok=True)

asyncio.run(main())
```

**Output atteso:**
```
Scritto.
Letto: Contenuto scritto in modo asincrono
parallelo_0.txt: File numero 0
parallelo_1.txt: File numero 1
parallelo_2.txt: File numero 2
```

#### Leggere un File Riga per Riga in Modo Asincrono

```python
import asyncio
import aiofiles

async def processa_log(percorso: str) -> dict:
    """Conta le occorrenze di ogni livello di log."""
    conteggi = {"INFO": 0, "WARN": 0, "ERROR": 0, "DEBUG": 0}

    async with aiofiles.open(percorso, "r", encoding="utf-8") as log:
        async for riga in log:
            for livello in conteggi:
                if livello in riga:
                    conteggi[livello] += 1

    return conteggi

async def main():
    # Crea log di esempio
    import aiofiles
    async with aiofiles.open("test.log", "w", encoding="utf-8") as out:
        for i in range(10):
            await out.write(f"INFO:  operazione {i}\n")
        for i in range(3):
            await out.write(f"ERROR: fallimento {i}\n")
        for i in range(5):
            await out.write(f"WARN:  attenzione {i}\n")

    risultato = await processa_log("test.log")
    for livello, count in risultato.items():
        print(f"  {livello}: {count}")

    import os
    os.unlink("test.log")

asyncio.run(main())
```

**Output atteso:**
```
  INFO: 10
  WARN: 5
  ERROR: 3
  DEBUG: 0
```

#### asyncio.Semaphore -- Limitare le Operazioni Concorrenti

```python
import asyncio
import aiofiles
from pathlib import Path

async def processa_file(sem: asyncio.Semaphore, nome: str) -> str:
    """Elabora un file con limite di concorrenza."""
    async with sem:   # max N operazioni contemporanee
        async with aiofiles.open(nome, "r", encoding="utf-8") as inp:
            contenuto = await inp.read()
        await asyncio.sleep(0.01)   # simula elaborazione
        return f"{nome}: {len(contenuto)} caratteri"

async def elabora_molti_file(percorsi: list, max_concurrent: int = 5) -> list:
    """Elabora file in parallelo con limite di concorrenza."""
    sem = asyncio.Semaphore(max_concurrent)
    tasks = [processa_file(sem, p) for p in percorsi]
    return await asyncio.gather(*tasks)

async def main():
    # Crea file di esempio
    nomi = [f"file_{i:02d}.txt" for i in range(10)]
    for nome in nomi:
        async with aiofiles.open(nome, "w", encoding="utf-8") as out:
            await out.write(f"Contenuto del file {nome}\n")

    # Elabora max 3 file alla volta
    risultati = await elabora_molti_file(nomi, max_concurrent=3)
    for r in risultati:
        print(r)

    # Pulizia
    for nome in nomi:
        Path(nome).unlink(missing_ok=True)

asyncio.run(main())
```

**Output atteso:**
```
file_00.txt: 25 caratteri
file_01.txt: 25 caratteri
file_02.txt: 25 caratteri
...
file_09.txt: 25 caratteri
```

---

## PARTE C — Esercizi Pratici

Questi esercizi sono ordinati dal piu guidato (C1) al piu autonomo (C10).
Ogni esercizio ha uno scheletro iniziale e i requisiti chiari.

---

### C1 - Contatore di Parole (Guidato)

**Obiettivo:** Leggere un file di testo e contare quante volte appare ogni parola.

**Requisiti:**
- Ignora maiuscole/minuscole (normalizza tutto in minuscolo)
- Ignora la punteggiatura
- Mostra le 10 parole piu frequenti in ordine decrescente

**Scheletro:**
```python
import re
from collections import Counter
from pathlib import Path

def conta_parole(percorso: str) -> Counter:
    """Conta le parole in un file di testo."""
    with open(percorso, "r", encoding="utf-8") as inp:
        testo = inp.read()

    # Normalizza: minuscolo + solo lettere e spazi
    testo_norm = testo.lower()
    parole = re.findall(r"[a-zA-Z]+", testo_norm)
    return Counter(parole)

# Crea un testo di esempio
Path("testo.txt").write_text("""
Python e un linguaggio di programmazione potente e versatile.
Python viene usato per web, data science, automazione e molto altro.
Imparare Python e la scelta giusta per iniziare a programmare.
""", encoding="utf-8")

contatore = conta_parole("testo.txt")

print("Le 10 parole piu frequenti:")
for parola, freq in contatore.most_common(10):
    print(f"  {parola:<20} {freq}x")

Path("testo.txt").unlink()
```

**Output atteso:**
```
Le 10 parole piu frequenti:
  python               3x
  e                    3x
  per                  2x
  un                   1x
  linguaggio           1x
  di                   1x
  programmazione       1x
  potente              1x
  versatile            1x
  viene                1x
```

---

### C2 - Backup con Timestamp

**Obiettivo:** Creare una funzione che faccia backup di un file aggiungendo
timestamp al nome.

**Requisiti:**
- Il backup deve avere formato: `nome_originale_20260715_103045.ext`
- Se la directory di backup non esiste, crearla
- Restituire il percorso del file di backup creato

**Soluzione:**
```python
import shutil
import datetime
from pathlib import Path

def crea_backup(percorso_file: str, dir_backup: str = "backups") -> Path:
    """Crea una copia di backup con timestamp nel nome."""
    sorgente = Path(percorso_file)
    if not sorgente.exists():
        raise FileNotFoundError(f"File non trovato: {sorgente}")

    dest_dir = Path(dir_backup)
    dest_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_backup = f"{sorgente.stem}_{timestamp}{sorgente.suffix}"
    dest = dest_dir / nome_backup

    shutil.copy2(str(sorgente), str(dest))
    return dest

# Test
Path("documento.txt").write_text("Testo importante", encoding="utf-8")
backup = crea_backup("documento.txt")
print(f"Backup creato: {backup.name}")
print(f"Esiste: {backup.exists()}")

# Pulizia
Path("documento.txt").unlink()
import shutil; shutil.rmtree("backups")
```

**Output atteso (esempio):**
```
Backup creato: documento_20260715_103045.txt
Esiste: True
```

---

### C3 - Log Rotante

**Obiettivo:** Implementare un logger che ruota il file quando supera una
dimensione massima, mantenendo un numero configurabile di backup.

**Requisiti:**
- Quando il file supera `max_bytes`, rinominalo in `.1`, `.2`, etc.
- Mantieni al massimo `max_backup` copie
- Scrivi sempre nel file principale

**Soluzione:**
```python
from pathlib import Path

class LogRotante:
    """Logger che ruota automaticamente il file quando supera max_bytes."""

    def __init__(self, percorso: str, max_bytes: int = 1024, max_backup: int = 3):
        self.percorso = Path(percorso)
        self.max_bytes = max_bytes
        self.max_backup = max_backup

    def _ruota(self) -> None:
        """Ruota i file di log."""
        # Elimina il backup piu vecchio se esiste
        vecchio = Path(f"{self.percorso}.{self.max_backup}")
        vecchio.unlink(missing_ok=True)

        # Scala i backup: .2 -> .3, .1 -> .2, ecc.
        for i in range(self.max_backup - 1, 0, -1):
            src = Path(f"{self.percorso}.{i}")
            dst = Path(f"{self.percorso}.{i+1}")
            if src.exists():
                src.rename(dst)

        # Il log corrente diventa .1
        if self.percorso.exists():
            self.percorso.rename(f"{self.percorso}.1")

    def scrivi(self, messaggio: str) -> None:
        """Scrive un messaggio, ruotando se necessario."""
        if self.percorso.exists() and self.percorso.stat().st_size >= self.max_bytes:
            self._ruota()

        with open(self.percorso, "a", encoding="utf-8") as log:
            log.write(messaggio + "\n")

# Test
logger = LogRotante("app.log", max_bytes=200, max_backup=3)

for i in range(30):
    logger.scrivi(f"INFO: evento numero {i:03d} - dati elaborati correttamente")

# Elenca i file di log creati
import os
log_files = sorted([f for f in os.listdir(".") if f.startswith("app.log")])
for nome in log_files:
    size = Path(nome).stat().st_size
    print(f"  {nome}: {size} byte")

# Pulizia
for nome in log_files:
    Path(nome).unlink()
```

**Output atteso:**
```
  app.log: 87 byte
  app.log.1: 174 byte
  app.log.2: 174 byte
  app.log.3: 174 byte
```

---

### C4 - Analizzatore CSV

**Obiettivo:** Leggere un CSV di vendite e produrre statistiche.

**Requisiti:**
- Calcola totale, media, minimo e massimo delle vendite per categoria
- Genera un CSV di riepilogo
- Gestisci righe con dati mancanti o malformati

**Soluzione:**
```python
import csv
from pathlib import Path
from collections import defaultdict

# Crea CSV di input
Path("vendite.csv").write_text(
    "data,prodotto,categoria,quantita,prezzo\n"
    "2026-01-15,Laptop,Elettronica,3,899.99\n"
    "2026-01-16,Mouse,Elettronica,15,29.99\n"
    "2026-01-16,Scrivania,Arredamento,2,349.00\n"
    "2026-01-17,,Elettronica,5,\n"  # riga con dati mancanti
    "2026-01-18,Sedia,Arredamento,8,149.50\n"
    "2026-01-18,Tastiera,Elettronica,10,79.99\n",
    encoding="utf-8"
)

# Analisi
vendite_per_cat = defaultdict(list)
righe_saltate = 0

with open("vendite.csv", "r", encoding="utf-8", newline="") as inp:
    reader = csv.DictReader(inp)
    for riga in reader:
        try:
            if not riga["prodotto"] or not riga["prezzo"]:
                righe_saltate += 1
                continue
            subtotale = int(riga["quantita"]) * float(riga["prezzo"])
            vendite_per_cat[riga["categoria"]].append(subtotale)
        except (ValueError, KeyError):
            righe_saltate += 1

print(f"Righe saltate (dati mancanti): {righe_saltate}")
print()

# Genera CSV di riepilogo
with open("riepilogo.csv", "w", encoding="utf-8", newline="") as out:
    writer = csv.writer(out)
    writer.writerow(["categoria", "totale", "media", "min", "max", "n_vendite"])

    for cat, valori in sorted(vendite_per_cat.items()):
        row = [
            cat,
            f"{sum(valori):.2f}",
            f"{sum(valori)/len(valori):.2f}",
            f"{min(valori):.2f}",
            f"{max(valori):.2f}",
            len(valori),
        ]
        writer.writerow(row)
        print(f"  {cat}: totale={row[1]}, media={row[2]}")

# Pulizia
Path("vendite.csv").unlink()
Path("riepilogo.csv").unlink()
```

**Output atteso:**
```
Righe saltate (dati mancanti): 1

  Arredamento: totale=1895.00, media=947.50
  Elettronica: totale=3498.87, media=1166.29
```

---

### C5 - Convertitore di Formati

**Obiettivo:** Convertire un file JSON in YAML e viceversa.

**Requisiti:**
- Rileva automaticamente il formato in input dall'estensione
- Supporta JSON -> YAML e YAML -> JSON
- Preserva tutti i dati (tipi, annidamento)

**Soluzione:**
```python
import json
import yaml
from pathlib import Path

def converti_formato(input_path: str, output_path: str) -> None:
    """Converte un file tra JSON e YAML."""
    src = Path(input_path)
    dst = Path(output_path)

    # Leggi input
    if src.suffix.lower() == ".json":
        with open(src, "r", encoding="utf-8") as inp:
            dati = json.load(inp)
    elif src.suffix.lower() in (".yaml", ".yml"):
        with open(src, "r", encoding="utf-8") as inp:
            dati = yaml.safe_load(inp)
    else:
        raise ValueError(f"Formato non supportato: {src.suffix}")

    # Scrivi output
    if dst.suffix.lower() == ".json":
        with open(dst, "w", encoding="utf-8") as out:
            json.dump(dati, out, indent=2, ensure_ascii=False)
    elif dst.suffix.lower() in (".yaml", ".yml"):
        with open(dst, "w", encoding="utf-8") as out:
            yaml.safe_dump(dati, out, default_flow_style=False, allow_unicode=True)
    else:
        raise ValueError(f"Formato non supportato: {dst.suffix}")

    print(f"Convertito: {src.name} -> {dst.name}")

# Test JSON -> YAML
Path("config.json").write_text(
    '{"app": "test", "versione": 1, "debug": false, "lista": [1, 2, 3]}',
    encoding="utf-8"
)
converti_formato("config.json", "config.yaml")
print(Path("config.yaml").read_text(encoding="utf-8"))

# Test YAML -> JSON
converti_formato("config.yaml", "config_back.json")
print(Path("config_back.json").read_text(encoding="utf-8"))

# Pulizia
for nome in ["config.json", "config.yaml", "config_back.json"]:
    Path(nome).unlink(missing_ok=True)
```

**Output atteso:**
```
Convertito: config.json -> config.yaml
app: test
debug: false
lista:
- 1
- 2
- 3
versione: 1

Convertito: config.yaml -> config_back.json
{
  "app": "test",
  "debug": false,
  "lista": [1, 2, 3],
  "versione": 1
}
```

---

### C6 - Organizzatore di File per Estensione (Semi-Autonomo)

**Obiettivo:** Organizzare automaticamente i file di una directory in
sottocartelle per tipo.

**Requisiti:**
- Mappa le estensioni alle categorie (es. .jpg, .png -> "Immagini")
- Crea le sottocartelle se non esistono
- Non spostare file gia nelle sottocartelle
- Genera un report di cosa e stato spostato

**Scheletro da completare:**
```python
import shutil
from pathlib import Path

CATEGORIE = {
    "Immagini":    [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg"],
    "Documenti":   [".pdf", ".doc", ".docx", ".txt", ".odt", ".rtf"],
    "Video":       [".mp4", ".mkv", ".avi", ".mov", ".wmv"],
    "Audio":       [".mp3", ".wav", ".flac", ".aac", ".ogg"],
    "Archivi":     [".zip", ".tar", ".gz", ".bz2", ".7z", ".rar"],
    "Codice":      [".py", ".js", ".ts", ".html", ".css", ".java", ".go"],
    "Dati":        [".csv", ".json", ".yaml", ".toml", ".xml", ".db"],
    "Altro":       [],   # categoria di fallback
}

def costruisci_mappa_estensioni(categorie: dict) -> dict:
    """Crea dizionario estensione -> categoria."""
    mappa = {}
    for categoria, estensioni in categorie.items():
        for ext in estensioni:
            mappa[ext.lower()] = categoria
    return mappa

def organizza_directory(directory: str) -> dict:
    """Organizza i file della directory in sottocartelle."""
    base = Path(directory)
    mappa = costruisci_mappa_estensioni(CATEGORIE)
    spostati = {}   # categoria -> [file spostati]

    for file in base.iterdir():
        if not file.is_file():
            continue   # salta le directory

        categoria = mappa.get(file.suffix.lower(), "Altro")
        dest_dir = base / categoria
        dest_dir.mkdir(exist_ok=True)

        dest = dest_dir / file.name
        shutil.move(str(file), str(dest))
        spostati.setdefault(categoria, []).append(file.name)

    return spostati

# Test
base = Path("da_organizzare")
base.mkdir(exist_ok=True)

# Crea file di esempio
for nome in ["foto.jpg", "video.mp4", "report.pdf", "dati.csv",
             "script.py", "archivio.zip", "documento.txt"]:
    (base / nome).touch()

report = organizza_directory(str(base))
print("File organizzati:")
for categoria, file_list in sorted(report.items()):
    print(f"  {categoria}/")
    for nome in sorted(file_list):
        print(f"    - {nome}")

# Pulizia
import shutil
shutil.rmtree(base)
```

**Output atteso:**
```
File organizzati:
  Archivi/
    - archivio.zip
  Audio/
  Codice/
    - script.py
  Dati/
    - dati.csv
  Documenti/
    - documento.txt
    - report.pdf
  Immagini/
    - foto.jpg
  Video/
    - video.mp4
```

---

### C7 - Ricerca Ricorsiva con Filtri

**Obiettivo:** Implementare una funzione di ricerca file avanzata con
filtri per nome, dimensione, data di modifica.

**Soluzione:**
```python
import datetime
from pathlib import Path
from typing import Optional

def cerca_file(
    directory: str,
    pattern: str = "*",
    min_size_kb: Optional[float] = None,
    max_size_kb: Optional[float] = None,
    modificato_dopo: Optional[datetime.datetime] = None,
) -> list[Path]:
    """Cerca file con filtri multipli."""
    base = Path(directory)
    risultati = []

    for p in base.rglob(pattern):
        if not p.is_file():
            continue

        try:
            info = p.stat()
        except PermissionError:
            continue

        # Filtro dimensione
        size_kb = info.st_size / 1024
        if min_size_kb is not None and size_kb < min_size_kb:
            continue
        if max_size_kb is not None and size_kb > max_size_kb:
            continue

        # Filtro data modifica
        if modificato_dopo is not None:
            mod_time = datetime.datetime.fromtimestamp(info.st_mtime)
            if mod_time < modificato_dopo:
                continue

        risultati.append(p)

    return sorted(risultati)

# Test con struttura di esempio
import shutil

base = Path("ricerca_test")
(base / "src").mkdir(parents=True, exist_ok=True)
(base / "docs").mkdir(exist_ok=True)

(base / "src" / "main.py").write_text("x" * 500, encoding="utf-8")
(base / "src" / "utils.py").write_text("x" * 100, encoding="utf-8")
(base / "docs" / "README.md").write_text("x" * 200, encoding="utf-8")
(base / "config.json").write_text("x" * 50, encoding="utf-8")

# Cerca file .py piu grandi di 0.2 KB
trovati = cerca_file(str(base), "*.py", min_size_kb=0.2)
print("File .py > 0.2 KB:")
for p in trovati:
    kb = p.stat().st_size / 1024
    print(f"  {p.relative_to(base)} ({kb:.2f} KB)")

# Cerca tutti i file tra 0.1 e 0.3 KB
trovati2 = cerca_file(str(base), min_size_kb=0.1, max_size_kb=0.3)
print("\nFile tra 0.1 e 0.3 KB:")
for p in trovati2:
    kb = p.stat().st_size / 1024
    print(f"  {p.relative_to(base)} ({kb:.2f} KB)")

shutil.rmtree(base)
```

**Output atteso:**
```
File .py > 0.2 KB:
  src/main.py (0.49 KB)

File tra 0.1 e 0.3 KB:
  docs/README.md (0.20 KB)
  src/utils.py (0.10 KB)
```

---

### C8 - Merge di File CSV

**Obiettivo:** Unire piu file CSV con la stessa struttura in un unico file,
rimuovendo duplicati basati su una colonna chiave.

**Soluzione:**
```python
import csv
from pathlib import Path

def merge_csv(
    file_input: list[str],
    file_output: str,
    colonna_chiave: str,
) -> int:
    """Unisce piu CSV rimuovendo duplicati per colonna_chiave."""
    visti = set()
    righe_uniche = []
    intestazione = None

    for percorso in file_input:
        with open(percorso, "r", encoding="utf-8", newline="") as inp:
            reader = csv.DictReader(inp)
            if intestazione is None:
                intestazione = reader.fieldnames

            for riga in reader:
                chiave = riga[colonna_chiave]
                if chiave not in visti:
                    visti.add(chiave)
                    righe_uniche.append(riga)

    with open(file_output, "w", encoding="utf-8", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=intestazione)
        writer.writeheader()
        writer.writerows(righe_uniche)

    return len(righe_uniche)

# Crea CSV di esempio con duplicati
Path("lista_a.csv").write_text(
    "id,nome,citta\n1,Alice,Milano\n2,Bob,Roma\n3,Carlo,Torino\n",
    encoding="utf-8"
)
Path("lista_b.csv").write_text(
    "id,nome,citta\n2,Bob,Roma\n4,Diana,Napoli\n5,Ettore,Firenze\n",
    encoding="utf-8"
)

n = merge_csv(["lista_a.csv", "lista_b.csv"], "merged.csv", "id")
print(f"Righe uniche: {n}")
print(Path("merged.csv").read_text(encoding="utf-8"))

for nome in ["lista_a.csv", "lista_b.csv", "merged.csv"]:
    Path(nome).unlink()
```

**Output atteso:**
```
Righe uniche: 5
id,nome,citta
1,Alice,Milano
2,Bob,Roma
3,Carlo,Torino
4,Diana,Napoli
5,Ettore,Firenze
```

---

### C9 - Scrivi Atomicamente (Autonomo)

**Obiettivo:** Implementare una funzione di scrittura atomica che garantisce
che il file di destinazione non venga mai corrotto, nemmeno in caso di crash
del programma durante la scrittura.

**Requisiti:**
- Scrivi in un file temporaneo nella stessa directory della destinazione
- Usa `os.fsync()` per garantire la scrittura su disco
- Usa `os.replace()` (atomico su POSIX) per sostituire il file finale
- Gestisci gli errori: se la scrittura fallisce, la destinazione non cambia

**Soluzione:**
```python
import os
import tempfile
from pathlib import Path

def scrivi_atomicamente(percorso: str, contenuto: str, encoding: str = "utf-8") -> None:
    """
    Scrive il contenuto nel file in modo atomico.
    La destinazione non viene mai vista in stato parziale.
    """
    dest = Path(percorso)
    parent = dest.parent

    # Crea il file temporaneo nella STESSA directory della destinazione
    # (fondamentale: os.replace() atomico funziona solo sullo stesso filesystem)
    fd, tmp_path = tempfile.mkstemp(dir=parent, prefix=".tmp_", suffix=dest.suffix)
    try:
        with os.fdopen(fd, "w", encoding=encoding) as tmp:
            tmp.write(contenuto)
            tmp.flush()
            os.fsync(tmp.fileno())   # forza scrittura su disco (anche su crash)

        # os.replace() e atomico su POSIX: o la destinazione ha il nuovo
        # contenuto, o ha quello vecchio -- mai uno stato intermedio
        os.replace(tmp_path, percorso)

    except Exception:
        # Se qualcosa va storto, elimina il temporaneo e rilancia
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise

# Test
scrivi_atomicamente("importante.txt", "Dati critici che non devono corrompersi\n")
print("Scritto:")
print(Path("importante.txt").read_text(encoding="utf-8"))

# Simula aggiornamento
scrivi_atomicamente("importante.txt", "Dati aggiornati - versione 2\n")
print("Aggiornato:")
print(Path("importante.txt").read_text(encoding="utf-8"))

Path("importante.txt").unlink()
```

**Output atteso:**
```
Scritto:
Dati critici che non devono corrompersi

Aggiornato:
Dati aggiornati - versione 2
```

---

### C10 - Pipeline di Elaborazione File (Completamente Autonomo)

**Obiettivo:** Implementare una pipeline di elaborazione per file di log grandi
usando generatori (niente caricamento in memoria).

**Requisiti:**
- Leggi righe dal file senza caricare tutto in memoria (generatore)
- Filtra righe che contengono un livello di log specificato
- Trasforma: aggiungi un prefisso e parsifica il timestamp
- Raggruppa per ora: conta gli eventi per ogni ora
- Genera un report CSV con i risultati

**Soluzione:**
```python
import csv
import datetime
import re
from collections import defaultdict
from pathlib import Path

def genera_righe(percorso: str):
    """Generatore: produce righe una alla volta senza caricare il file."""
    with open(percorso, "r", encoding="utf-8") as inp:
        for riga in inp:
            yield riga.rstrip()

def filtra_livello(righe, livello: str):
    """Filtra solo le righe con il livello specificato."""
    for riga in righe:
        if livello in riga:
            yield riga

PATTERN_LOG = re.compile(
    r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\s+(\w+)\s+(.*)"
)

def parsifica_riga(righe):
    """Estrae timestamp, livello e messaggio da ogni riga."""
    for riga in righe:
        m = PATTERN_LOG.match(riga)
        if m:
            ts_str, livello, messaggio = m.groups()
            yield {
                "timestamp": datetime.datetime.fromisoformat(ts_str),
                "livello": livello,
                "messaggio": messaggio,
            }

def raggruppa_per_ora(eventi) -> dict:
    """Conta gli eventi per ogni ora."""
    per_ora = defaultdict(int)
    for evento in eventi:
        ora = evento["timestamp"].strftime("%Y-%m-%d %H:00")
        per_ora[ora] += 1
    return dict(sorted(per_ora.items()))

# Crea log di esempio
import datetime
with open("grandi.log", "w", encoding="utf-8") as out:
    base = datetime.datetime(2026, 7, 15, 8, 0, 0)
    for i in range(200):
        ts = base + datetime.timedelta(minutes=i * 3)
        livello = ["INFO", "ERROR", "INFO", "WARN", "INFO"][i % 5]
        out.write(f"{ts.isoformat()} {livello} Evento numero {i:04d}\n")

# Pipeline: leggi -> filtra ERROR -> parsifica -> raggruppa per ora
pipeline = genera_righe("grandi.log")
pipeline = filtra_livello(pipeline, "ERROR")
pipeline = parsifica_riga(pipeline)
per_ora = raggruppa_per_ora(pipeline)

print("Errori per ora:")
for ora, count in per_ora.items():
    print(f"  {ora}: {count} errori")

# Genera report CSV
with open("report_errori.csv", "w", encoding="utf-8", newline="") as out:
    writer = csv.writer(out)
    writer.writerow(["ora", "n_errori"])
    for ora, count in per_ora.items():
        writer.writerow([ora, count])

print("\nReport CSV generato: report_errori.csv")

# Pulizia
Path("grandi.log").unlink()
Path("report_errori.csv").unlink()
```

**Output atteso:**
```
Errori per ora:
  2026-07-15 08:00: 5
  2026-07-15 09:00: 5
  2026-07-15 10:00: 5
  2026-07-15 11:00: 5
  2026-07-15 12:00: 5
  2026-07-15 13:00: 5
  2026-07-15 14:00: 5
  2026-07-15 15:00: 5
  2026-07-15 16:00: 4

Report CSV generato: report_errori.csv
```


---

## PARTE D — Argomenti Avanzati

---

### D1 - Il Modulo io: Flussi di Dati in Memoria

#### Analogia: La Lavagna Temporanea

`io.StringIO` e `io.BytesIO` sono come lavagne in memoria: puoi scriverci
sopra, leggere quello che hai scritto, spostarti avanti e indietro -- senza
mai toccare il disco. Utili per testare codice che lavora con file, o per
costruire dati da inviare via rete.

#### io.StringIO -- Testo in Memoria

```python
import io

# StringIO si comporta esattamente come un file di testo
buffer = io.StringIO()
buffer.write("Prima riga\n")
buffer.write("Seconda riga\n")
buffer.write("Terza riga\n")

# Leggi tutto dall'inizio
buffer.seek(0)
print("Tutto il contenuto:")
print(buffer.read())

# Leggi riga per riga
buffer.seek(0)
print("Riga per riga:")
for riga in buffer:
    print(f"  >> {riga.strip()}")

# Ottieni il valore come stringa
valore = buffer.getvalue()   # tutto il contenuto senza seek
print(f"Lunghezza: {len(valore)} caratteri")

buffer.close()
```

**Output atteso:**
```
Tutto il contenuto:
Prima riga
Seconda riga
Terza riga

Riga per riga:
  >> Prima riga
  >> Seconda riga
  >> Terza riga
Lunghezza: 36 caratteri
```

#### io.BytesIO -- Byte in Memoria

```python
import io

# Costruisci un file binario in memoria (es. un'immagine mini)
buf = io.BytesIO()
buf.write(b"\x89PNG\r\n\x1a\n")   # header PNG (simulato)
buf.write(b"\x00" * 100)           # dati fittizi

print(f"Dimensione buffer: {buf.tell()} byte")

# Torna all'inizio e leggi
buf.seek(0)
intestazione = buf.read(8)
print(f"Intestazione: {intestazione.hex()}")

# Passa a una funzione che si aspetta un file
buf.seek(0)
dati = buf.read()
print(f"Totale byte: {len(dati)}")
```

**Output atteso:**
```
Dimensione buffer: 108 byte
Intestazione: 89504e470d0a1a0a
Totale byte: 108
```

#### Uso Pratico: Test di Funzioni che Scrivono su File

```python
import io
import csv

def scrivi_report_csv(dati: list, file_out) -> int:
    """Scrive dati su qualsiasi oggetto file (disco o memoria)."""
    writer = csv.writer(file_out)
    writer.writerow(["nome", "valore"])
    for riga in dati:
        writer.writerow(riga)
    return len(dati)

dati_test = [["Alpha", 10], ["Beta", 20], ["Gamma", 30]]

# Test senza toccare il disco
buffer = io.StringIO()
n = scrivi_report_csv(dati_test, buffer)

output = buffer.getvalue()
print(f"Scritte {n} righe:")
print(output)

# Verifica con csv.reader
buffer.seek(0)
reader = csv.reader(buffer)
righe = list(reader)
print(f"Righe verificate: {len(righe)}")   # intestazione + 3 dati = 4
```

**Output atteso:**
```
Scritte 3 righe:
nome,valore
Alpha,10
Beta,20
Gamma,30

Righe verificate: 4
```

---

### D2 - Compressione: gzip, bz2, lzma, zipfile, tarfile

#### Analogia: Il Compattatore e il Contenitore

La compressione e come un compattatore: riduce la dimensione del contenuto.
L'archiviazione (zip, tar) e come un contenitore: raggruppa piu file in uno.
Spesso si fa entrambe: tar.gz = prima raggruppa (tar), poi comprime (gz).

#### gzip -- Compressione Semplice

```python
import gzip
from pathlib import Path

# Testo da comprimere
testo_originale = ("Python e un linguaggio eccellente per la gestione file. " * 50)
print(f"Originale: {len(testo_originale)} byte")

# Comprimi
with gzip.open("testo.txt.gz", "wt", encoding="utf-8") as out:
    out.write(testo_originale)

dimensione_gz = Path("testo.txt.gz").stat().st_size
print(f"Compresso: {dimensione_gz} byte")
print(f"Rapporto:  {dimensione_gz/len(testo_originale.encode('utf-8')):.1%}")

# Decomprimi
with gzip.open("testo.txt.gz", "rt", encoding="utf-8") as inp:
    testo_decompresso = inp.read()

print(f"Decompresso: {len(testo_decompresso)} byte")
print(f"Uguali: {testo_originale == testo_decompresso}")

Path("testo.txt.gz").unlink()
```

**Output atteso:**
```
Originale: 2800 byte
Compresso: 75 byte
Rapporto:  2.7%
Decompresso: 2800 byte
Uguali: True
```

#### zipfile -- Archivio con Piu File

```python
import zipfile
from pathlib import Path

# Crea file di esempio
for nome in ["a.txt", "b.txt", "c.py"]:
    Path(nome).write_text(f"Contenuto di {nome}\n" * 10, encoding="utf-8")

# Crea archivio ZIP
with zipfile.ZipFile("archivio.zip", "w", compression=zipfile.ZIP_DEFLATED) as zf:
    for nome in ["a.txt", "b.txt", "c.py"]:
        zf.write(nome)
        print(f"  Aggiunto: {nome} ({Path(nome).stat().st_size} byte)")

print(f"Archivio: {Path('archivio.zip').stat().st_size} byte")

# Elenca il contenuto
with zipfile.ZipFile("archivio.zip", "r") as zf:
    print("\nContenuto archivio:")
    for info in zf.infolist():
        print(f"  {info.filename}: {info.file_size} byte -> {info.compress_size} byte")

# Estrai tutti i file
with zipfile.ZipFile("archivio.zip", "r") as zf:
    zf.extractall("estratti")

print("\nEstrazione completata:")
for p in Path("estratti").rglob("*"):
    if p.is_file():
        print(f"  {p}")

# Pulizia
import shutil
for nome in ["a.txt", "b.txt", "c.py", "archivio.zip"]:
    Path(nome).unlink(missing_ok=True)
shutil.rmtree("estratti", ignore_errors=True)
```

**Output atteso:**
```
  Aggiunto: a.txt (210 byte)
  Aggiunto: b.txt (210 byte)
  Aggiunto: c.py (210 byte)
Archivio: 234 byte

Contenuto archivio:
  a.txt: 210 byte -> 22 byte
  b.txt: 210 byte -> 22 byte
  c.py: 210 byte -> 22 byte

Estrazione completata:
  estratti/a.txt
  estratti/b.txt
  estratti/c.py
```

#### Confronto Algoritmi di Compressione

| Algoritmo | Modulo   | Velocita | Compressione | Uso tipico          |
|-----------|----------|----------|--------------|---------------------|
| gzip      | gzip     | Veloce   | Buona        | Log, backup rapidi  |
| bz2       | bz2      | Media    | Migliore     | Distribuzioni       |
| lzma/xz   | lzma     | Lenta    | Ottima       | Archivi finali      |
| zstd      | zstandard| Veloce   | Ottima       | Sistemi moderni     |

```python
import gzip, bz2, lzma
from pathlib import Path

dati = b"Python " * 10000   # 70 KB di dati ripetuti

# gzip
with gzip.open("test.gz", "wb") as out:
    out.write(dati)

# bz2
with bz2.open("test.bz2", "wb") as out:
    out.write(dati)

# lzma
with lzma.open("test.xz", "wb") as out:
    out.write(dati)

print(f"Originale: {len(dati)} byte")
for nome in ["test.gz", "test.bz2", "test.xz"]:
    size = Path(nome).stat().st_size
    print(f"  {nome}: {size} byte ({size/len(dati):.1%})")
    Path(nome).unlink()
```

**Output atteso:**
```
Originale: 70000 byte
  test.gz: 237 byte (0.3%)
  test.bz2: 43 byte (0.1%)
  test.xz: 188 byte (0.3%)
```

---

### D3 - struct: Leggere e Scrivere Dati Binari

#### Analogia: La Chiave per il Cassetto Cifrato

Il modulo `struct` e come la chiave per aprire un cassetto con dati in
formato fisso: sai che i primi 4 byte sono un intero, i successivi 8 byte
sono un float, e cosi via. Utile per protocol binary, formati di file
proprietari, comunicazione con hardware.

#### Formato di struct

Il carattere di formato descrive il tipo e la dimensione di ogni campo:

```
Prefisso byte order:
  > = big-endian (rete, file portabili)
  < = little-endian (x86 nativo)
  = = nativo del sistema

Tipi:
  b = signed byte (1 byte)
  B = unsigned byte (1 byte)
  h = short (2 byte)
  i = int (4 byte)
  f = float (4 byte)
  d = double (8 byte)
  s = char (1 byte per carattere: "10s" = stringa da 10 byte)
```

#### pack e unpack -- Serializzazione Binaria

```python
import struct

# Definisci la struttura: 4 campi
# - ID utente (unsigned int, 4 byte)
# - Punteggio (float, 4 byte)
# - Livello (unsigned short, 2 byte)
# - Flag (unsigned byte, 1 byte)
FORMATO = ">IHBf"   # big-endian: uint32, uint16, uint8, float32

# pack: Python -> bytes
dati_binari = struct.pack(FORMATO, 12345, 99, 1, 87.5)
print(f"Dimensione: {len(dati_binari)} byte")
print(f"Bytes: {dati_binari.hex()}")

# unpack: bytes -> Python
id_utente, livello, flag, punteggio = struct.unpack(FORMATO, dati_binari)
print(f"ID: {id_utente}, Livello: {livello}, Flag: {flag}, Punteggio: {punteggio:.1f}")
```

**Output atteso:**
```
Dimensione: 11 byte
Bytes: 000030392063015842f000
ID: 12345, Livello: 99, Flag: 1, Punteggio: 87.5
```

#### Scrivere e Leggere un File Binario con struct

```python
import struct
from pathlib import Path

# Formato record: timestamp (8 byte double) + valore (4 byte float) + flag (1 byte)
FORMATO_RECORD = ">df"
DIMENSIONE_RECORD = struct.calcsize(FORMATO_RECORD)

# Scrivi record binari
import time
with open("sensori.bin", "wb") as out:
    for i in range(5):
        ts = time.time() + i
        valore = 20.0 + i * 0.5
        out.write(struct.pack(FORMATO_RECORD, ts, valore))

print(f"File: {Path('sensori.bin').stat().st_size} byte")
print(f"Dimensione per record: {DIMENSIONE_RECORD} byte")
print(f"Numero record: {Path('sensori.bin').stat().st_size // DIMENSIONE_RECORD}")

# Leggi i record
print("\nRecords letti:")
with open("sensori.bin", "rb") as inp:
    while True:
        chunk = inp.read(DIMENSIONE_RECORD)
        if len(chunk) < DIMENSIONE_RECORD:
            break
        ts, valore = struct.unpack(FORMATO_RECORD, chunk)
        print(f"  ts={ts:.2f} valore={valore:.1f}")

Path("sensori.bin").unlink()
```

**Output atteso:**
```
File: 60 byte
Dimensione per record: 12 byte
Numero record: 5

Records letti:
  ts=1752571234.56 valore=20.0
  ts=1752571235.56 valore=20.5
  ts=1752571236.56 valore=21.0
  ts=1752571237.56 valore=21.5
  ts=1752571238.56 valore=22.0
```

---

### D4 - sqlite3: Il Database come File

#### Analogia: Il Raccoglitore con Schede Ordinate

SQLite e come un raccoglitore con schede ben ordinate: tutti i dati sono in
un singolo file `.db`, senza server, senza configurazione. Python include
sqlite3 nella libreria standard.

#### Operazioni Base

```python
import sqlite3
from pathlib import Path

# Connetti (crea il file se non esiste)
conn = sqlite3.connect("magazzino.db")
conn.row_factory = sqlite3.Row   # abilita accesso per nome colonna

try:
    cur = conn.cursor()

    # Crea tabella
    cur.execute("""
        CREATE TABLE IF NOT EXISTS prodotti (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            nome    TEXT    NOT NULL,
            prezzo  REAL    NOT NULL,
            stock   INTEGER DEFAULT 0
        )
    """)

    # Inserisci dati
    prodotti = [
        ("Laptop Pro", 1299.00, 5),
        ("Mouse Wireless", 39.99, 50),
        ("Tastiera Meccanica", 129.90, 15),
        ("Monitor 4K", 699.00, 8),
    ]
    cur.executemany(
        "INSERT INTO prodotti (nome, prezzo, stock) VALUES (?, ?, ?)",
        prodotti
    )
    conn.commit()
    print(f"Inseriti {cur.rowcount} prodotti")

    # Leggi tutti
    print("\nProdotti in magazzino:")
    for row in cur.execute("SELECT * FROM prodotti ORDER BY prezzo DESC"):
        print(f"  [{row['id']}] {row['nome']:<22} {row['prezzo']:>8.2f} EUR  stock={row['stock']}")

    # Query filtrata
    print("\nProdotti economici (< 100 EUR):")
    cur.execute("SELECT nome, prezzo FROM prodotti WHERE prezzo < 100 ORDER BY prezzo")
    for row in cur.fetchall():
        print(f"  {row['nome']}: {row['prezzo']:.2f} EUR")

    # Aggiorna
    cur.execute("UPDATE prodotti SET stock = stock - 1 WHERE nome = ?", ("Laptop Pro",))
    conn.commit()

    nuovo_stock = cur.execute(
        "SELECT stock FROM prodotti WHERE nome = ?", ("Laptop Pro",)
    ).fetchone()[0]
    print(f"\nNuovo stock Laptop Pro: {nuovo_stock}")

finally:
    conn.close()
    Path("magazzino.db").unlink(missing_ok=True)
```

**Output atteso:**
```
Inseriti 4 prodotti

Prodotti in magazzino:
  [1] Laptop Pro             1299.00 EUR  stock=5
  [4] Monitor 4K              699.00 EUR  stock=8
  [3] Tastiera Meccanica      129.90 EUR  stock=15
  [2] Mouse Wireless           39.99 EUR  stock=50

Prodotti economici (< 100 EUR):
  Mouse Wireless: 39.99 EUR

Nuovo stock Laptop Pro: 4
```

#### Context Manager per Transazioni

```python
import sqlite3

# sqlite3 supporta "with" per le transazioni
with sqlite3.connect("test.db") as conn:
    conn.execute("CREATE TABLE IF NOT EXISTS log (ts TEXT, msg TEXT)")
    conn.execute("INSERT INTO log VALUES (datetime('now'), ?)", ("avvio",))
    conn.execute("INSERT INTO log VALUES (datetime('now'), ?)", ("operazione",))
    # conn.commit() e chiamato automaticamente all'uscita del with
    # in caso di eccezione, viene fatto rollback automatico

import os
os.unlink("test.db")
```

---

### D5 - Pattern Avanzati: Generatori per File Enormi

#### Il Pattern Pipeline con Generatori

Quando elabori file enormi (GB di dati), non puoi caricare tutto in memoria.
I generatori Python permettono di costruire pipeline che processano una riga
alla volta, con consumo di memoria costante:

```python
from pathlib import Path
import random, datetime

# Crea un file di log grande (simulato)
def genera_log_grande(percorso: str, n_righe: int) -> None:
    livelli = ["INFO", "WARN", "ERROR", "DEBUG"]
    with open(percorso, "w", encoding="utf-8") as out:
        base = datetime.datetime(2026, 7, 1)
        for i in range(n_righe):
            ts = base + datetime.timedelta(seconds=i * 10)
            livello = livelli[i % len(livelli)]
            out.write(f"{ts.isoformat()} {livello} Messaggio numero {i:06d}\n")

genera_log_grande("grande.log", 100_000)
print(f"File creato: {Path('grande.log').stat().st_size / 1024 / 1024:.1f} MB")

# ---- PIPELINE CON GENERATORI ----

def leggi_righe(percorso: str):
    """Generatore: legge una riga alla volta (O(1) memoria)."""
    with open(percorso, "r", encoding="utf-8") as inp:
        for riga in inp:
            yield riga.rstrip()

def filtra_livello_gen(righe, livello: str):
    """Generatore: filtra per livello senza buffering."""
    for riga in righe:
        if livello in riga:
            yield riga

def campiona_reservoir(righe, n: int) -> list:
    """Reservoir sampling: campiona N righe casuali senza caricare tutto."""
    import random
    campione = []
    for i, riga in enumerate(righe):
        if i < n:
            campione.append(riga)
        else:
            j = random.randint(0, i)
            if j < n:
                campione[j] = riga
    return campione

# Conta gli ERROR con consumo di memoria O(1)
pipeline = leggi_righe("grande.log")
pipeline = filtra_livello_gen(pipeline, "ERROR")
n_errori = sum(1 for _ in pipeline)
print(f"Totale errori: {n_errori}")

# Campiona 5 righe di errore casuali
pipeline = leggi_righe("grande.log")
pipeline = filtra_livello_gen(pipeline, "ERROR")
campione = campiona_reservoir(pipeline, 5)
print("\n5 righe di errore casuali:")
for riga in campione:
    print(f"  {riga[:80]}")

Path("grande.log").unlink()
```

**Output atteso:**
```
File creato: 6.1 MB
Totale errori: 25000

5 righe di errore casuali:
  2026-07-01T00:00:20 ERROR Messaggio numero 000002
  2026-07-01T05:15:40 ERROR Messaggio numero 001894
  2026-07-01T12:30:10 ERROR Messaggio numero 004503
  2026-07-01T18:45:50 ERROR Messaggio numero 006755
  2026-07-02T01:00:00 ERROR Messaggio numero 008640
```

---

## PARTE E — Riepilogo, Tabelle e Glossario

---

### Checklist: Prima di Lavorare con i File

Usa questa checklist ogni volta che scrivi codice di I/O:

```
APERTURA FILE:
  [ ] Uso sempre "with open()" (non open() senza with)
  [ ] Specifico sempre encoding="utf-8" per file di testo
  [ ] Scelgo la modalita giusta: "r", "w", "a", "x", "rb", "wb"
  [ ] Gestisco FileNotFoundError, PermissionError, IsADirectoryError

ENCODING:
  [ ] Uso UTF-8 per tutti i file nuovi
  [ ] Uso "utf-8-sig" per file che potrebbero avere BOM
  [ ] Specifico errors="strict" in produzione
  [ ] Uso chardet per file di origine sconosciuta

PATHLIB:
  [ ] Uso Path() invece di os.path per codice nuovo
  [ ] Uso / per costruire percorsi (non os.path.join)
  [ ] Verifico con .exists() prima di operare
  [ ] Uso .mkdir(parents=True, exist_ok=True) per creare directory

SCRITTURA SICURA:
  [ ] Per file critici, uso il pattern temp -> fsync -> os.replace()
  [ ] Uso filelock per accesso da processi multipli
  [ ] Faccio flush() se altri processi devono vedere i dati in tempo reale

CSV:
  [ ] Uso sempre newline="" in open() per file CSV
  [ ] Preferisco DictReader/DictWriter a reader/writer per leggibilita
  [ ] Gestisco righe con dati mancanti o malformati

JSON/YAML/TOML:
  [ ] Uso json.dump() con indent=2 e ensure_ascii=False
  [ ] Per YAML, uso SEMPRE yaml.safe_load(), MAI yaml.load()
  [ ] Per TOML in lettura, apro in modalita "rb"
  [ ] Per tipi non standard (datetime, Path, set), uso JSONEncoder custom

FILE GRANDI:
  [ ] Uso generatori invece di .read() per file > 100 MB
  [ ] Considero mmap per ricerca su file molto grandi
  [ ] Uso reservoir sampling per campionare senza caricare tutto

COMPRESSIONE:
  [ ] gzip per compatibilita e velocita
  [ ] lzma per massima compressione (distribuzioni)
  [ ] zipfile per archivi multi-file con Windows
  [ ] tarfile per archivi Unix

PULIZIA:
  [ ] Uso tempfile per file temporanei (eliminazione automatica)
  [ ] Uso shutil.rmtree() con cautela (irreversibile)
  [ ] Uso Path.unlink(missing_ok=True) per evitare errori se il file non esiste
```

---

### Tabella: Quando Usare Quale Formato

| Scenario                          | Formato    | Modulo          | Note                              |
|-----------------------------------|------------|-----------------|-----------------------------------|
| Configurazione leggibile          | TOML       | tomllib/tomli-w | Standard Python moderno           |
| Configurazione con commenti       | YAML       | pyyaml          | Attenzione a safe_load!           |
| Scambio dati tra sistemi          | JSON       | json (stdlib)   | Universale, senza dipendenze      |
| Dati tabulari/Excel               | CSV        | csv (stdlib)    | newline="" obbligatorio           |
| Database locale                   | SQLite     | sqlite3 (stdlib)| File unico, nessun server         |
| Dati binari compatti              | struct     | struct (stdlib) | Protocolli, sensori, hardware     |
| Archive multi-file                | ZIP        | zipfile (stdlib)| Compatibile con Windows           |
| Archive Unix                      | TAR.GZ     | tarfile (stdlib)| Standard Linux                    |
| File enormi (> 1 GB)             | Streaming  | generatori      | Memoria O(1)                      |
| Cache rapida Python-only          | pickle     | pickle          | Non condividere tra versioni!     |
| File testo non strutturato        | TXT        | open() base     | Semplice e universale             |

---

### Tabella: Modalita di Apertura File

| Modalita | Descrizione                       | Crea | Tronca | Deve Esistere |
|----------|-----------------------------------|------|--------|---------------|
| "r"      | Leggi testo                       | No   | No     | Si            |
| "w"      | Scrivi testo (sovrascrive)        | Si   | Si     | No            |
| "a"      | Aggiungi testo (in coda)          | Si   | No     | No            |
| "x"      | Crea testo (errore se esiste)     | Si   | No     | No (errore si)|
| "r+"     | Leggi e scrivi testo              | No   | No     | Si            |
| "rb"     | Leggi binario                     | No   | No     | Si            |
| "wb"     | Scrivi binario (sovrascrive)      | Si   | Si     | No            |
| "ab"     | Aggiungi binario                  | Si   | No     | No            |
| "xb"     | Crea binario (errore se esiste)   | Si   | No     | No (errore si)|

---

### Gerarchia degli Errori di I/O

```
OSError
  FileNotFoundError     -- il file/directory non esiste
  PermissionError       -- permessi insufficienti
  IsADirectoryError     -- aspettavi un file, hai trovato una dir
  FileExistsError       -- il file esiste (con modalita "x")
  NotADirectoryError    -- aspettavi una dir, hai trovato un file

UnicodeError
  UnicodeDecodeError    -- impossibile decodificare (encoding sbagliato)
  UnicodeEncodeError    -- impossibile codificare (carattere non supportato)

json.JSONDecodeError    -- JSON malformato
yaml.YAMLError          -- YAML malformato o non sicuro
csv.Error               -- errore nel parsing CSV
```

---

### Glossario

**Buffer:** Area di memoria temporanea tra il tuo programma e il disco fisico.
Python scrive prima nel buffer e poi sul disco in blocchi per efficienza.

**BOM (Byte Order Mark):** Sequenza di 3 byte all'inizio di file UTF-8 prodotta
da Windows. Invisible ma puo causare problemi. Usa "utf-8-sig" per gestirlo.

**Codec:** Il software che implementa un encoding (codifica/decodifica).
Python cerca il codec per nome (es. "utf-8", "latin-1", "cp1252").

**Encoding:** Dizionario che mappa caratteri a sequenze di byte.
UTF-8 e lo standard moderno raccomandato.

**File lock:** Meccanismo che garantisce accesso esclusivo a un file da
parte di un solo processo alla volta. filelock e la libreria cross-platform.

**File mapping (mmap):** Tecnica dove il SO mappa un file nello spazio
degli indirizzi del processo. Consente accesso casuale rapido senza caricare
tutto in memoria.

**Flush:** Operazione che forza il contenuto del buffer in memoria a essere
scritto su disco. Necessario quando altri processi devono vedere i dati subito.

**Generator (generatore):** Funzione che produce valori uno alla volta con
yield. Essenziale per elaborare file enormi senza occupare memoria.

**glob:** Pattern di ricerca per file (es. "*.py", "test_*.txt").
pathlib.glob() e rglob() lo implementano.

**JSON:** JavaScript Object Notation. Formato di testo per scambio dati.
Supporta: string, number, bool, null, array, object.

**mmap:** Memory-mapped file. Vedi "File mapping".

**newline="":** Parametro obbligatorio per open() quando si usa csv.
Senza di esso, Windows aggiunge righe vuote extra.

**os.replace():** Funzione atomica che sostituisce un file con un altro.
Su POSIX garantisce che la sostituzione sia atomica (no stati intermedi).

**pathlib.Path:** Classe Python per rappresentare percorsi del filesystem
in modo orientato agli oggetti. Preferita a os.path in codice moderno.

**Pickle:** Formato di serializzazione Python-specifico. Non sicuro con
dati non fidati. Non condividere tra versioni diverse di Python.

**Pipeline:** Serie di elaborazioni concatenate dove l'output di una e
l'input della successiva. Con generatori, permette I/O con memoria O(1).

**rglob():** Ricerca ricorsiva di file con pattern. Equivalente a
`find` su Unix. Piu efficiente di listdir() + os.walk() per pattern semplici.

**shutil:** Shell utilities. Modulo per operazioni di alto livello su file
e directory: copy, copytree, move, rmtree, make_archive.

**SQLite:** Database embedded salvato in un file .db. Nessun server richiesto.
Incluso nella stdlib Python tramite sqlite3.

**struct:** Modulo per serializzazione binaria con formato fisso.
Usato per protocolli, formati di file binari, comunicazione hardware.

**tempfile:** Modulo per file e directory temporanei. NamedTemporaryFile,
TemporaryDirectory, SpooledTemporaryFile.

**TOML:** Tom's Obvious, Minimal Language. Formato di configurazione leggibile.
Usato da pyproject.toml. Incluso in stdlib da Python 3.11 (tomllib).

**UnicodeDecodeError:** Errore che si verifica quando Python non riesce a
decodificare byte con l'encoding specificato. Spesso: file Latin-1 letto come UTF-8.

**UTF-8:** Encoding Unicode a larghezza variabile. Lo standard moderno per
testo. Compatibile con ASCII. Supporta tutti i caratteri Unicode.

**watchdog:** Libreria per monitorare i cambiamenti del filesystem in tempo
reale. Observer + FileSystemEventHandler.

**with open():** Context manager per file. Garantisce la chiusura del file
anche in caso di eccezione. Sempre preferito a open() senza with.

**YAML:** YAML Ain't Markup Language. Formato di configurazione leggibile,
con commenti. Attenzione: yaml.load() e vulnerabile a RCE -- usa yaml.safe_load().

---

### Prossimi Passi

Dopo aver padroneggiato la gestione file e I/O:

1. **Tutorial 06 — Espressioni Regolari:** Pattern matching avanzato per
   parsing di file di testo, log, dati strutturati.

2. **Tutorial 07 — Gestione Errori e Logging:** Logging strutturato con
   il modulo `logging`, rotazione dei log, handler multipli.

3. **Tutorial 08 — Testing con pytest:** Come testare funzioni di I/O
   usando `tmp_path` (fixture pytest), monkeypatch, e file temporanei.

4. **Tutorial 10 — Programmazione Asincrona:** asyncio e aiofiles per
   I/O ad alta concorrenza, elaborazione parallela di file.

5. **Tutorial 12 — Database con SQLAlchemy:** ORM per SQLite, PostgreSQL,
   MySQL -- il livello successivo a sqlite3 diretto.

---

*Fine Tutorial 05 — Gestione File e I/O*

*Companion: `05-gestione-file-io.md` | Livello: Principiante -> Intermedio*
*Tempo stimato: 4-6 ore | Esercizi: C1-C10 (dal guidato all'autonomo)*

