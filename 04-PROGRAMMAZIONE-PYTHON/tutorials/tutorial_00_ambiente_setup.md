# Tutorial: Ambiente e Setup su Windows — Dal Principiante all'Esperto

> **Companion to:** `00-ambiente-setup-windows.md`
> **Scope:** Installazione Python su Windows 10/11 con uv, configurazione VS Code e estensioni, uso del terminale PowerShell, struttura di un progetto Python, primo programma funzionante.
> **Prerequisiti:** Nessuno. Solo un PC Windows e connessione internet.
> **Durata stimata:** 6–10 ore
> **Lingua:** Italiano

---

## Prima di Iniziare: Cosa Imparerai e Perché

### Python: la lingua che il computer capisce davvero

Immagina di voler chiedere a qualcuno di fare qualcosa di molto complesso, come "calcola la media di questi mille numeri, poi trovami i dieci più vicini alla media, e stampali in ordine decrescente". Se lo chiedi a un amico, lui capisce il senso generale. Se lo chiedi a un computer, devi essere preciso al millimetro: il computer non "capisce il senso", esegue istruzioni letterali.

Python è la lingua che usi per dare quelle istruzioni. È un linguaggio di programmazione: un modo formale, preciso e non ambiguo per comunicare con il computer. La particolarità di Python rispetto ad altre lingue per computer è che assomiglia molto all'inglese normale, ed è stato progettato apposta per essere letto da esseri umani, non solo dalle macchine.

Confronto visivo — stesso calcolo, tre lingue diverse:

**Python** (quello che imparerai):
```python
numeri = [4, 7, 2, 9, 1, 5]
media = sum(numeri) / len(numeri)
print(f"La media è {media}")
```

**C++** (più vicino al metallo, meno leggibile):
```cpp
#include <iostream>
#include <vector>
int main() {
    std::vector<int> numeri = {4, 7, 2, 9, 1, 5};
    double media = 0;
    for (int n : numeri) media += n;
    media /= numeri.size();
    std::cout << "La media è " << media << std::endl;
}
```

**Assembly** (quello che il processore capisce davvero):
```asm
; ... decine di istruzioni per fare la stessa cosa ...
```

Python è lontano dall'Assembly quanto l'italiano è lontano dal morse. La parola `print` in Python significa effettivamente "stampa questo", come l'italiano. In C++, la stessa operazione richiede `std::cout <<` — un codice molto meno intuitivo.

### Dove viene usato Python nel mondo reale

Python non è un linguaggio "per imparare e poi abbandonare". È attivamente usato in produzione dai sistemi più grandi del mondo:

| Azienda/Progetto | Uso di Python |
|------------------|---------------|
| **Netflix** | Algoritmi di raccomandazione, analisi dei dati di visualizzazione, strumenti CI/CD |
| **Instagram** | Backend completo (Django), gestisce oltre 1 miliardo di utenti |
| **NASA** | Analisi delle missioni spaziali, elaborazione immagini dei telescopi (Hubble, James Webb) |
| **Spotify** | Analisi dati musicali, sistema di raccomandazione delle playlist |
| **CERN** | Analisi dei dati del Grande Collisore di Adroni (LHC) |
| **Dropbox** | Quasi tutto il backend e il client desktop originale |
| **Google** | Molti servizi interni, YouTube (parzialmente), TensorFlow |
| **Medicina** | Analisi genomica, modelli predittivi di diagnosi, ricerca farmacologica |
| **Finanza** | Trading algoritmico, analisi del rischio, modelli attuariali |
| **Intelligenza Artificiale** | PyTorch, TensorFlow, scikit-learn — tutti scritti per Python |

La domanda di sviluppatori Python è costantemente tra le più alte nel mercato del lavoro tecnologico. Secondo Stack Overflow Developer Survey 2024, Python è il linguaggio di programmazione più usato per il quinto anno consecutivo.

### Cosa costruirai alla fine di questo tutorial

Alla fine di questo tutorial avrai:

1. **Un ambiente di sviluppo professionale** funzionante su Windows, identico a quello usato da sviluppatori professionisti in aziende reali.
2. **Python installato e verificato** con il metodo moderno (`uv`), con gestione automatica delle versioni.
3. **VS Code configurato** con tutte le estensioni necessarie per scrivere Python in modo professionale.
4. **Il tuo primo programma** che legge input dall'utente, elabora i dati e produce output — il ciclo fondamentale di qualsiasi programma.
5. **La struttura di un progetto Python reale** con virtual environment, dipendenze gestite e version control con Git.

Non ti verrà insegnato a scrivere programmi complessi qui — quello è il Modulo 01 e oltre. Questo tutorial è il fondamento: senza un ambiente configurato correttamente, qualsiasi altro apprendimento diventa molto più difficile.

> **Consiglio pratico:** Non cercare di capire tutto al primo passaggio. L'obiettivo adesso è che i comandi funzionino. La comprensione profonda arriva con la Parte B di questo stesso tutorial, dopo che hai già visto tutto in pratica.

---

## Parte A: Le Basi Assolute (Livello Principiante)

### A1 — Cos'è un Programma? Cos'è un Linguaggio di Programmazione?

#### La ricetta di cucina

Pensa a una ricetta. Una buona ricetta è una lista di istruzioni precise, in ordine, che chiunque può seguire per ottenere lo stesso risultato:

```
1. Scalda il forno a 180°C
2. Mescola 200g di farina con 100g di burro
3. Aggiungi un uovo e mescola finché l'impasto è omogeneo
4. Stendi l'impasto in una teglia
5. Cuoci per 25 minuti
6. Sforna e lascia raffreddare
```

Un programma informatico è esattamente questo: una ricetta per il computer. Una sequenza di istruzioni precise, nell'ordine giusto, che il computer esegue passo per passo.

```python
# Questo è un "programma" (una ricetta) Python
temperatura = 180                    # Istruzione 1: scalda a 180°C
farina = 200                         # Istruzione 2: prendi la farina
burro = 100                          # Istruzione 3: prendi il burro
impasto = farina + burro             # Istruzione 4: mescola
minuti_cottura = 25                  # Istruzione 5: imposta il timer
print(f"Cuoci a {temperatura}°C per {minuti_cottura} minuti")  # Risultato
```

La differenza fondamentale tra una ricetta per persone e un programma per computer:

- **Persone:** Capiscono "aggiungi sale quanto basta" o "cuoci finché è dorato".
- **Computer:** Hanno bisogno di istruzioni esatte. "Aggiungi 5 grammi di sale fine" invece di "quanto basta".

#### Perché Python in particolare?

Esistono centinaia di linguaggi di programmazione. Ognuno è stato creato con uno scopo specifico. Perché imparare Python?

| Linguaggio | Creato per | Pro | Contro per un principiante |
|------------|------------|-----|---------------------------|
| **Python** | Uso generale, leggibilità | Sintassi quasi-italiana, enorme ecosistema, AI/ML | Più lento di C/C++ (irrilevante per quasi tutti i compiti) |
| **JavaScript** | Web browser | Ovunque sul web, frontend e backend | Molte stranezze storiche, più complicato per principianti |
| **Java** | Enterprise, Android | Molto rigoroso, ottimi errori di tipo | Verboso, richiede molta cerimonia per fare cose semplici |
| **C** | Sistemi operativi, performance | Massima performance, controllo totale | Devi gestire la memoria manualmente — fonte di molti bug |
| **SQL** | Database | Indispensabile per i dati | Solo per interrogare database, non per programmare in generale |

Python vince per chi inizia perché:
1. **La sintassi è minimale.** Non ci sono simboli misteriosi come `{}`, `()`, `;` ovunque. Il codice si legge come pseudo-inglese.
2. **L'errore è comprensibile.** Quando sbagli, Python ti dice cosa hai sbagliato in modo relativamente chiaro.
3. **L'ecosistema è immenso.** Per qualsiasi problema esiste già una libreria Python che lo risolve parzialmente o totalmente.
4. **La domanda è alta.** Le aziende assumono sviluppatori Python più di quasi qualsiasi altro linguaggio.

#### Le parole fondamentali della programmazione

Prima di toccare il terminale, impara questi concetti. Li incontrerai ovunque:

**Istruzione (statement):** Una singola azione che il computer esegue. Come una riga di una ricetta.
```python
print("Ciao")   # Questa è una singola istruzione
```

**Variabile:** Un contenitore con un nome. Come una scatola con un'etichetta. Puoi mettere un valore dentro e richiamarlo usando l'etichetta.
```python
nome = "Marco"   # La scatola si chiama "nome", dentro c'è "Marco"
print(nome)      # Chiedo il contenuto della scatola "nome"
# Output: Marco
```

**Funzione:** Un mini-programma con un nome. Quando la "chiami", il mini-programma si esegue.
```python
print("Ciao")   # "print" è una funzione già pronta in Python
                 # La "chiami" scrivendo il suo nome con le parentesi
```

**Commento:** Testo che Python ignora completamente. Serve per lasciare note a se stessi (o ad altri programmatori). Si inizia con `#`.
```python
# Questo è un commento. Python non lo esegue.
x = 5   # anche qui, tutto dopo # è un commento
```

**Output:** Il risultato che il programma produce. Può essere testo sullo schermo, un file, un dato in una database, ecc.

**Input:** Dati che entrano nel programma dall'esterno. Può essere testo digitato dall'utente, un file, dati da internet, ecc.

---

### A2 — Il Terminale PowerShell: La Tua Nuova Calcolatrice Magica

#### Cos'è un terminale?

Pensa a come interagisci normalmente con Windows: clicchi su icone, trascini file, premi pulsanti nelle finestre. Questa è l'interfaccia grafica (GUI — Graphical User Interface). Funziona bene per operazioni comuni.

Il **terminale** (o **console** o **shell**) è un'alternativa testuale: invece di cliccare su una icona, scrivi un comando. Invece di trascinare un file, scrivi `mv file.txt nuova_posizione\`. Invece di fare clic destro → copia, scrivi `cp file.txt copia.txt`.

All'inizio sembra più difficile. In realtà, per lo sviluppo software il terminale è **molto più potente**:
- Puoi automatizzare sequenze di operazioni.
- Puoi eseguire comandi su centinaia di file con una sola riga.
- Quasi tutta la documentazione tecnica mostra comandi da terminale.
- I server (dove gira il codice in produzione) non hanno interfaccia grafica: solo terminale.

**PowerShell** è il terminale moderno di Microsoft, preinstallato su Windows 10 e 11. È quello che useremo in questo corso.

#### Come aprire PowerShell — 3 metodi

**Metodo 1 — Menu Start (il più semplice):**
1. Clicca sul pulsante Start (il logo Windows in basso a sinistra).
2. Digita `powershell` sulla tastiera (il menu cercherà automaticamente).
3. Clicca su **"Windows PowerShell"** o **"PowerShell 7"** nei risultati.

**Metodo 2 — Tasto Windows + X:**
1. Premi `Win + X` sulla tastiera (il tasto con il logo Windows + la lettera X).
2. Si apre un menu. Seleziona **"Windows PowerShell"** o **"Terminal"**.

**Metodo 3 — Dalla barra degli indirizzi di Esplora File:**
1. Apri Esplora File (l'icona della cartella nella barra delle applicazioni).
2. Naviga nella cartella dove vuoi lavorare.
3. Clicca sulla barra degli indirizzi in alto (dove vedi il percorso tipo `C:\Utenti\nome`).
4. Digita `powershell` e premi Invio.
5. Si aprirà PowerShell già posizionato in quella cartella.

#### Capire il prompt di PowerShell

Quando apri PowerShell, vedi qualcosa di simile a questo:

```
Windows PowerShell
Copyright (C) Microsoft Corporation. All rights reserved.

PS C:\Users\Marco>
```

La riga `PS C:\Users\Marco>` si chiama **prompt** (o prompt dei comandi). Ecco cosa significa ogni parte:

```
PS  C:\Users\Marco  >
│   │               │
│   │               └─ Il cursor lampeggia qui: digita il comando
│   └─ Directory corrente: sei in "C:\Users\Marco" (la tua cartella utente)
└─ "PS" = PowerShell (indica che stai usando PowerShell)
```

Quando un virtual environment Python è attivato (lo vedremo più avanti), il prompt cambia aggiungendo il nome dell'ambiente all'inizio:

```
(.venv) PS C:\Users\Marco\mio-progetto>
```

Questo ti dice "stai lavorando all'interno del virtual environment .venv".

#### I comandi fondamentali

Ogni volta che scrivi un comando e premi Invio, PowerShell esegue quell'istruzione e mostra il risultato.

**`pwd` — Print Working Directory (dove sono adesso?):**
```powershell
PS C:\Users\Marco> pwd

Path
----
C:\Users\Marco
```
`pwd` ti dice in quale cartella ti trovi. Come guardare l'indirizzo del luogo dove sei.

**`ls` — List (cosa c'è in questa cartella?):**
```powershell
PS C:\Users\Marco> ls

    Directory: C:\Users\Marco

Mode                 LastWriteTime         Length Name
----                 -------------         ------  ----
d----          15/07/2026    10:23                Desktop
d----          15/07/2026    09:41                Documents
d----          14/07/2026    22:15                Downloads
d----          15/07/2026    11:02                progetti
```
`ls` mostra il contenuto della cartella corrente. Come aprire Esplora File, ma in testo.

**`cd` — Change Directory (spostati in un'altra cartella):**
```powershell
PS C:\Users\Marco> cd Documents
PS C:\Users\Marco\Documents>

# Puoi anche usare un percorso completo:
PS C:\Users\Marco\Documents> cd C:\Users\Marco\Desktop
PS C:\Users\Marco\Desktop>

# Per tornare alla cartella precedente:
PS C:\Users\Marco\Desktop> cd ..
PS C:\Users\Marco>

# Per tornare alla cartella home:
PS C:\qualsiasi\posto> cd ~
PS C:\Users\Marco>
```

**`mkdir` — Make Directory (crea una nuova cartella):**
```powershell
PS C:\Users\Marco> mkdir miei-progetti

    Directory: C:\Users\Marco

Mode                 LastWriteTime         Length Name
----                 -------------         ------  ----
d----          15/07/2026    12:00                miei-progetti
```

**`cls` — Clear Screen (pulisci lo schermo):**
```powershell
PS C:\Users\Marco> cls
# Lo schermo diventa pulito. I comandi precedenti spariscono dalla vista
# (ma la loro esecuzione è già avvenuta: non si "annullano")
```

#### Come copiare e incollare nel terminale

Nel terminale PowerShell, le scorciatoie da tastiera per copia e incolla sono **diverse** da quelle di Windows normale:

- **Copiare testo dal terminale:** Seleziona il testo con il mouse (clic e trascina), poi premi `Ctrl+C`. Oppure, in Windows Terminal moderno, basta selezionare il testo per copiarlo automaticamente.
- **Incollare nel terminale:** Premi `Ctrl+V` oppure clic destro nel terminale.

> **Attenzione:** In terminali più vecchi, `Ctrl+C` nel terminale non copia — **interrompe il programma in esecuzione**. Se copi dall'esterno con `Ctrl+C`, usa clic destro per incollare nel terminale.

#### Ctrl+C — Il tasto di emergenza

Se un programma sta girando nel terminale e non finisce (o si è bloccato), premi `Ctrl+C`. Questo **interrompe immediatamente** l'esecuzione del programma in corso e ti riporta al prompt.

```powershell
PS C:\Users\Marco> python programma-che-non-finisce.py
# Il programma gira... gira... non finisce...
# Premi Ctrl+C
^C                    # PowerShell mostra ^C per indicare che hai interrotto
PS C:\Users\Marco>    # Sei di nuovo al prompt, libero di digitare
```

#### Storico dei comandi — freccia su/giù

Non devi riscrivere i comandi ogni volta. Premi la freccia su (`↑`) per vedere i comandi precedenti, freccia giù (`↓`) per andare avanti nella storia. Premi Invio per rieseguire il comando selezionato.

#### Problemi Comuni con PowerShell

**Problema: PowerShell si apre e si chiude immediatamente**

Sintomo: la finestra appare per un secondo e poi sparisce.

Soluzione: probabilmente stai aprendo un file `.ps1` con doppio clic invece di aprire PowerShell dal menu Start. Apri PowerShell dal menu Start, poi esegui il comando da lì.

**Problema: caratteri strani nell'output (?, ?, ??)**

Sintomo: invece di `à`, `è`, `ù` vedi simboli strani.

Soluzione: esegui questi comandi nella stessa sessione PowerShell:
```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001
```

**Problema: "Accesso negato" o "Permission denied"**

Sintomo: un comando non funziona e dice che non hai i permessi.

Soluzione: devi aprire PowerShell come amministratore. Invece di cliccare semplicemente su PowerShell nel menu Start, fai clic destro → "Esegui come amministratore". Usa questa modalità con cautela: i comandi amministratore possono modificare il sistema in modo irreversibile.

**Problema: il comando non viene trovato ("is not recognized...")**

Sintomo: digiti `python` e ottieni:
```
python : The term 'python' is not recognized as the name of a cmdlet...
```

Questo NON è un errore grave: significa semplicemente che Python non è installato (o non è nel PATH). Lo risolveremo nella sezione A3.

---

### A3 — Installazione Python con uv (Metodo Raccomandato)

#### Cos'è uv e perché è migliore

Tradizionalmente, installare Python su Windows richiedeva:
1. Scaricare il programma di installazione da python.org.
2. Installarlo manualmente.
3. Installare pip separatamente.
4. Imparare a creare virtual environment con `python -m venv`.
5. Imparare a usare pip per installare pacchetti.
6. Gestire manualmente le versioni se avevi più progetti.

`uv` è uno strumento moderno che fa tutto questo in un unico posto. È scritto in Rust (un linguaggio molto veloce) ed è sviluppato da Astral, la stessa azienda che ha creato `ruff` (il formattatore di codice Python più veloce).

Analogia: immagina di dover cucinare. Puoi comprare una padella, poi un fornello, poi un coltello, poi un tagliere — tutto separatamente. Oppure puoi comprare una cucina completa dove tutto funziona insieme. `uv` è la cucina completa.

Cosa fa `uv`:
- Installa Python (qualsiasi versione richiesta).
- Crea e gestisce gli ambienti virtuali (aree isolate per ogni progetto).
- Installa le librerie del progetto (i "pacchetti").
- Genera un file di blocco (lock file) per garantire riproducibilità.
- È 10-100 volte più veloce di pip (il vecchio metodo).

#### Passaggio 1: installare uv

Apri PowerShell (dal menu Start, come visto nella sezione A2) e copia-incolla questo comando:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Premi Invio. Vedrai qualcosa di simile a questo:

```
Downloading uv 0.7.x (x86_64-pc-windows-msvc)
Installing to C:\Users\Marco\.local\bin
uv
uvx
Everything's installed!

To add C:\Users\Marco\.local\bin to your PATH, add the following to your PowerShell profile:

    $env:PATH = "C:\Users\Marco\.local\bin;$env:PATH"

Or run the following command to update your PATH permanently:

    [Environment]::SetEnvironmentVariable("PATH", "C:\Users\Marco\.local\bin;" + [Environment]::GetEnvironmentVariable("PATH", "User"), "User")
```

> **Nota importante:** Se vedi un errore "Cannot be loaded because running scripts is disabled on this system", devi prima eseguire questo comando:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```
> Poi riprova l'installazione di uv.

#### Passaggio 2: aggiornare il PATH nella sessione corrente

Dopo l'installazione, **chiudi e riapri PowerShell**. Questo è necessario perché il PATH (la lista di dove Windows cerca i programmi) viene letto solo all'avvio del terminale.

In alternativa, puoi aggiornare il PATH nella sessione corrente senza chiudere:
```powershell
$env:PATH = "$env:USERPROFILE\.local\bin;$env:PATH"
```

#### Passaggio 3: verifica che uv funziona

```powershell
uv --version
```

Output atteso:
```
uv 0.7.x (qualcosa)
```

Se vedi questo, uv è installato correttamente.

Se vedi `uv : The term 'uv' is not recognized...`, il PATH non è stato aggiornato. Chiudi PowerShell completamente e riaprine uno nuovo, poi riprova.

#### Passaggio 4: installare Python con uv

Con uv installato, non hai più bisogno di scaricare Python da python.org. uv lo gestisce per te:

```powershell
uv python install 3.12
```

Output atteso (potrebbe richiedere 1-2 minuti):
```
Searching for Python versions matching: Python 3.12
Installed Python 3.12.7 in 23.45s
 + cpython-3.12.7-windows-x86_64-none
```

uv scarica e installa Python 3.12 in una directory gestita da lui (`C:\Users\nome\.local\share\uv\python\`).

**Puoi installare più versioni se necessario:**
```powershell
uv python install 3.11   # installa anche Python 3.11
uv python install 3.13   # installa anche Python 3.13
```

**Vedi le versioni installate:**
```powershell
uv python list --only-installed
```

Output atteso:
```
cpython-3.12.7-windows-x86_64-none    C:\Users\Marco\.local\share\uv\python\cpython-3.12.7-...
```

#### Metodo alternativo: installazione da python.org

Se preferisci il metodo classico (ad esempio in un ambiente aziendale dove non puoi eseguire script da internet):

1. Vai su **https://www.python.org/downloads/windows/**
2. Scarica il file **"Windows installer (64-bit)"** della versione 3.12.x
3. Avvia il file scaricato **come amministratore** (tasto destro → "Esegui come amministratore")
4. **IMPORTANTE:** nella prima schermata, spunta la casella **"Add Python to PATH"** prima di cliccare qualsiasi altro pulsante
5. Clicca "Install Now"
6. Attendi il completamento e chiudi l'installer
7. Apri una **nuova** finestra di PowerShell (obbligatorio per aggiornare il PATH)

#### Problemi Comuni — Sezione A3

**Problema: l'output di uv --version mostra una versione molto vecchia**

Aggiorna uv:
```powershell
uv self update
```

**Problema: errore "SSL certificate" durante l'installazione di Python**

In ambienti aziendali, il certificato SSL potrebbe essere intercettato da un proxy aziendale. Contatta il tuo amministratore IT.

**Problema: uv python install 3.12 dice "Already installed"**

Non è un errore. Python 3.12 è già installato. Prosegui alla sezione A4.

**Problema: directory .local\bin non esiste**

```powershell
# Crea la directory manualmente:
New-Item -ItemType Directory -Force "$env:USERPROFILE\.local\bin"
# Poi reinstalla uv
```

---

### A4 — Verifica che Python Funziona

#### Controllare la versione

Apri una nuova finestra di PowerShell (o riusa quella dove hai installato uv) e digita:

```powershell
uv run python --version
```

Output atteso:
```
Python 3.12.7
```

Il comando `uv run python` dice a uv "avvia Python nella sua versione gestita". È diverso da digitare solo `python` (che userebbe il Python del sistema, se presente).

**Alternativa senza uv:**
```powershell
python --version
```

Output atteso:
```
Python 3.12.7
```

Se hai installato Python da python.org con l'opzione "Add to PATH", questo funzionerà direttamente. Con uv, potrebbe non funzionare ancora (dipende dalla configurazione del PATH). Va bene: usiamo sempre `uv run python` per sicurezza.

#### Il REPL Python: la calcolatrice che capisce le parole

**REPL** è l'acronimo di **Read-Eval-Print Loop**:
- **Read:** legge quello che digiti
- **Eval:** lo valuta (lo esegue)
- **Print:** stampa il risultato
- **Loop:** torna al punto 1 e aspetta il prossimo input

Analogia: il REPL è come una calcolatrice avanzata che non capisce solo i numeri, ma anche le parole, le liste, e qualsiasi istruzione Python.

**Come entrare nel REPL:**
```powershell
uv run python
```

Output di avvio (le cifre esatte varieranno):
```
Python 3.12.7 (main, Oct  1 2024, 15:17:31) [MSC v.1941 64 bit (AMD64)] on win32
Type "help", "copyright", "credits" or "license" for more information.
>>>
```

Il simbolo `>>>` è il prompt del REPL. Python è pronto e aspetta che tu scriva qualcosa.

#### Primi comandi nel REPL

**Stampare testo:**
```python
>>> print("Ciao, mondo!")
Ciao, mondo!
>>>
```
Hai appena eseguito il tuo primo programma Python. `print()` è una funzione che stampa il testo sullo schermo.

**Calcoli matematici:**
```python
>>> 2 + 2
4
>>> 10 - 3
7
>>> 5 * 6
30
>>> 10 / 3
3.3333333333333335
>>> 10 // 3
3
>>> 2 ** 10
1024
```

Nel REPL, non hai nemmeno bisogno di `print()`: Python stampa automaticamente il risultato di qualsiasi espressione.

**Operazioni con le stringhe (testo):**
```python
>>> "Python" * 3
'PythonPythonPython'
>>> "Ciao" + " " + "mondo"
'Ciao mondo'
>>> len("Python")
6
```

**Variabili:**
```python
>>> nome = "Marco"
>>> eta = 25
>>> print(f"Mi chiamo {nome} e ho {eta} anni")
Mi chiamo Marco e ho 25 anni
```

**Come uscire dal REPL:**
```python
>>> exit()
```
oppure premi `Ctrl+Z` seguito da Invio su Windows, oppure `Ctrl+D` su Linux/macOS.

> **Nota:** Tutto quello che scrivi nel REPL è temporaneo. Quando esci, tutto sparisce. Per salvare il codice devi scriverlo in un file `.py` — lo faremo nella sezione A5.

---

### A5 — VS Code: Il Tuo Ufficio Digitale

#### Cos'è un editor di codice?

Puoi scrivere codice Python anche con Blocco Note di Windows. Tecnicamente funziona. Ma sarebbe come fare grafica professionale con MS Paint quando esiste Photoshop.

Un **editor di codice** (o IDE — Integrated Development Environment) è un programma specializzato per scrivere codice. Offre:

- **Colorazione della sintassi:** le diverse parti del codice hanno colori diversi, facilitando la lettura.
- **Completamento automatico:** quando inizi a digitare, l'editor suggerisce il completamento.
- **Rilevamento errori in tempo reale:** l'editor evidenzia in rosso gli errori mentre scrivi, prima ancora di eseguire il programma.
- **Navigazione:** puoi fare `Ctrl+clic` su una funzione per andare alla sua definizione.
- **Terminale integrato:** puoi eseguire i comandi PowerShell senza uscire dall'editor.
- **Debug:** puoi fermare l'esecuzione del programma a una riga specifica e esaminare i valori delle variabili.

**VS Code** (Visual Studio Code) di Microsoft è gratuito, open-source, e ha il miglior supporto Python disponibile. È usato da milioni di sviluppatori professionisti in tutto il mondo.

#### Installazione di VS Code

**Metodo 1 — winget (da PowerShell, il più semplice):**
```powershell
winget install -e --id Microsoft.VisualStudioCode
```

Output atteso:
```
Found Visual Studio Code [Microsoft.VisualStudioCode] Version 1.90.x
This application is licensed to you by its owner.
...
Successfully installed
```

**Metodo 2 — Download manuale:**
1. Vai su **https://code.visualstudio.com/**
2. Clicca sul pulsante blu "Download for Windows"
3. Scegli "System Installer 64 bit" se hai Windows 10/11 a 64 bit (è quasi certamente il caso)
4. Avvia il file scaricato (es. `VSCodeSetup-x64-1.90.x.exe`)
5. Accetta la licenza e clicca "Avanti" in tutte le schermate
6. Nella schermata "Seleziona attività aggiuntive", spunta:
   - "Aggiungi azione 'Apri con Code' al menu contestuale di file di Esplora file"
   - "Aggiungi azione 'Apri con Code' al menu contestuale di directory di Esplora file"
   - "Aggiungi a PATH (disponibile dopo il riavvio)" — **IMPORTANTE**
7. Clicca "Installa"

**Verifica:**
Apri una **nuova** finestra di PowerShell e digita:
```powershell
code --version
```

Output atteso:
```
1.90.x
abc123def456...
x64
```

Se vedi questo, VS Code è installato e nel PATH.

#### Tour dell'interfaccia di VS Code

La prima volta che apri VS Code, vedrai questa struttura (da sinistra a destra):

```
╔═══════════════════════════════════════════════════════════════╗
║  BARRA     ║                                                   ║
║  ATTIVITÀ  ║            EDITOR (zona principale)              ║
║            ║                                                   ║
║  [📁]      ║  Qui scrivi il codice                             ║
║  [🔍]      ╠═══════════════════════════════════════════════════╣
║  [🔀]      ║                                                   ║
║  [🐛]      ║            TERMINALE INTEGRATO                    ║
║  [📦]      ║  PowerShell qui dentro!                           ║
╚═══════════════════════════════════════════════════════════════╝
```

- **Barra Attività (sinistra):** icone per passare tra Explorer (file), Search (cerca), Git, Debug, Extensions.
- **Editor (centro):** dove scrivi il codice. Puoi avere più file aperti in tab.
- **Terminale integrato (basso):** un vero PowerShell dentro VS Code. Aprilo con `` Ctrl+` `` (il tasto backtick, solitamente sotto Esc).

#### Installare le estensioni Python

Le **estensioni** sono plugin che aggiungono funzionalità a VS Code. Per Python, ne servono alcune fondamentali.

**Metodo rapido — da PowerShell:**
```powershell
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
code --install-extension ms-python.debugpy
code --install-extension charliermarsh.ruff
code --install-extension tamasfe.even-better-toml
```

Output atteso per ognuno:
```
Installing extensions...
Extension 'ms-python.python' v2024.x.x was successfully installed.
```

**Metodo alternativo — dall'interfaccia di VS Code:**
1. Apri VS Code.
2. Clicca sull'icona delle estensioni nella barra a sinistra (icona a forma di quattro quadrati, `Ctrl+Shift+X`).
3. Nel campo di ricerca in cima, digita `ms-python.python`.
4. Clicca "Installa" accanto all'estensione "Python" di Microsoft.
5. Ripeti per `ms-python.vscode-pylance`, `charliermarsh.ruff`.

**Cosa fa ogni estensione:**

| Estensione | Cosa fa (in parole semplici) |
|------------|------------------------------|
| **Python** (`ms-python.python`) | L'estensione principale. Permette a VS Code di "capire" Python: eseguire file, selezionare la versione Python, integrarsi con i test. |
| **Pylance** (`ms-python.vscode-pylance`) | Il "cervello" dell'editor per Python: analizza il codice e suggerisce completamenti intelligenti, evidenzia errori di tipo, mostra la documentazione delle funzioni. |
| **Python Debugger** (`ms-python.debugpy`) | Permette di fermare il programma a una riga e esaminare le variabili. Indispensabile per trovare i bug. |
| **Ruff** (`charliermarsh.ruff`) | Analizza il codice mentre scrivi e segnala: stile non conforme, import non usati, potenziali bug. Formatta automaticamente il codice quando salvi. |
| **Even Better TOML** (`tamasfe.even-better-toml`) | Aggiunge il supporto per file `.toml` (il formato di configurazione dei progetti Python moderni). |

#### Aprire una cartella di progetto in VS Code

VS Code lavora a livello di **cartella** (workspace), non di singolo file. Quando apri una cartella, VS Code la tratta come il tuo progetto.

```powershell
# Crea una cartella per i tuoi esperimenti
mkdir C:\Users\$env:USERNAME\progetti\esperimento-1
cd C:\Users\$env:USERNAME\progetti\esperimento-1

# Apri VS Code in questa cartella
code .
```

Il punto (`.`) significa "questa cartella". VS Code si aprirà con la cartella `esperimento-1` nell'Explorer a sinistra.

#### Il terminale integrato di VS Code

Uno dei vantaggi principali di VS Code è avere un terminale PowerShell direttamente nell'editor.

- **Aprire il terminale:** premi `` Ctrl+` `` (tasto backtick, sotto Esc).
- Il terminale si apre già posizionato nella cartella del progetto aperto.
- Puoi usarlo esattamente come un PowerShell normale.
- Puoi avere più terminali aperti contemporaneamente (clicca il `+` nel pannello del terminale).

**Creare e eseguire il primo file Python in VS Code:**

Nel terminale integrato di VS Code:
```powershell
# Sei già nella cartella esperimento-1
# Crea il primo file Python
```

Poi, nell'Editor (zona centrale):
1. Clicca su `File` → `New File` (oppure `Ctrl+N`).
2. Clicca su `File` → `Save As` (oppure `Ctrl+Shift+S`).
3. Salva il file con il nome `ciao.py` (l'estensione `.py` è fondamentale — indica che è un file Python).
4. Scrivi nel file:
```python
print("Ciao, sono il mio primo programma Python!")
print("Scritto con VS Code.")
```
5. Salva (`Ctrl+S`).
6. Nel terminale integrato, esegui:
```powershell
uv run python ciao.py
```

Output atteso:
```
Ciao, sono il mio primo programma Python!
Scritto con VS Code.
```

Hai appena scritto, salvato ed eseguito il tuo primo programma Python.

#### Problemi Comuni — Sezione A5

**Problema: VS Code non trova Python (avviso in basso a destra)**

Sintomo: VS Code mostra in basso a destra "Select Python Interpreter" o un avviso che Python non è trovato.

Soluzione:
1. Premi `Ctrl+Shift+P` (apre la "Command Palette").
2. Digita `Python: Select Interpreter`.
3. Seleziona la versione Python che hai installato (dovrebbe mostrare la versione installata con uv).

**Problema: le estensioni non compaiono nella lista**

Soluzione: prova a cercare direttamente l'ID completo nell'Extensions sidebar. Se ancora non appaiono, riavvia VS Code.

**Problema: il codice Python non ha colorazione sintattica**

Soluzione: verifica che il file sia salvato con l'estensione `.py`. In basso a destra di VS Code, il linguaggio rilevato dovrebbe mostrare "Python". Se mostra "Plain Text", clicca su quel testo e seleziona "Python".

**Problema: errore "code is not recognized" in PowerShell**

VS Code non è nel PATH. Soluzioni:
- Reinstalla VS Code scegliendo l'opzione "Add to PATH".
- Oppure aggiungi manualmente al PATH: `C:\Users\<nome>\AppData\Local\Programs\Microsoft VS Code\bin\`

---

*Fine Parte A. Prosegui con la Parte B per la comprensione profonda di come funziona l'ambiente.*


---

## Parte B: Comprensione Profonda (Livello Intermedio)

> Questa sezione spiega il *perché* di quello che hai fatto nella Parte A. Puoi leggerla subito dopo la Parte A, oppure tornare qui dopo aver completato gli esercizi della Parte C. Entrambi gli approcci funzionano.

### B1 — Come Funziona il PATH: La Rubrica del Computer

#### L'analogia della rubrica telefonica

Immagina di voler chiamare il tuo amico Marco. Hai due opzioni:
- **Opzione A:** Conosci il numero a memoria (es. `+39 333 1234567`). Puoi chiamarlo direttamente.
- **Opzione B:** Non conosci il numero. Cerchi "Marco" nella rubrica. La rubrica ti dice il numero. Poi chiami.

Il **PATH** di Windows funziona esattamente come la rubrica — ma per i programmi. Quando nel terminale digiti `python`, Windows non sa dove si trova `python.exe` sul disco. Quindi guarda nella "rubrica" (PATH) e cerca una directory che contenga `python.exe`. Quando la trova, avvia quel programma.

Il PATH e' una lista di percorsi di directory, separati da `;`:

```
C:\Windows\System32;C:\Windows;C:\Users\Marco\.local\bin;C:\Program Files\Git\bin
```

Quando digiti `python` nel terminale, Windows controlla quelle directory nell'ordine:
1. Guarda in `C:\Windows\System32` — c'e' `python.exe`? No.
2. Guarda in `C:\Windows` — c'e' `python.exe`? No.
3. Guarda in `C:\Users\Marco\.local\bin` — c'e' `python.exe`? No.
4. ... e cosi' via finche' non lo trova (o restituisce un errore se non esiste in nessuna directory).

Questo spiega perche', dopo aver installato Python, devi aprire **una nuova finestra** del terminale: la vecchia finestra ha il vecchio PATH in memoria, senza le nuove directory.

#### Vedere il PATH attuale

```powershell
# Visualizza tutto il PATH, una directory per riga
$env:PATH -split ";"
```

Output atteso (molte righe, ne mostro alcune):
```
C:\Windows\system32
C:\Windows
C:\Windows\System32\Wbem
C:\Windows\System32\WindowsPowerShell\v1.0\
C:\Users\Marco\.local\bin
C:\Program Files\Git\bin
C:\Program Files\Git\usr\bin
```

**Filtrare solo le directory Python/uv:**
```powershell
$env:PATH -split ";" | Where-Object { $_ -like "*python*" -or $_ -like "*uv*" -or $_ -like "*Python*" }
```

Output atteso con uv installato:
```
C:\Users\Marco\.local\bin
C:\Users\Marco\.local\share\uv\python\cpython-3.12.7-windows-x86_64-none\bin
```

#### Due livelli di PATH su Windows

Windows ha due livelli di PATH:

1. **PATH di Sistema** — valido per tutti gli utenti, richiede privilegi amministratore per modificarlo.
2. **PATH dell'Utente** — valido solo per te, non richiede privilegi amministratore.

Il PATH effettivo in una sessione e' la combinazione: `PATH Utente + PATH Sistema`. Il PATH Utente ha **priorita'** su quello di Sistema (viene controllato per primo).

**Vedere il PATH utente separatamente:**
```powershell
[Environment]::GetEnvironmentVariable("PATH", "User") -split ";"
```

**Vedere il PATH di sistema separatamente:**
```powershell
[Environment]::GetEnvironmentVariable("PATH", "Machine") -split ";"
```

#### Modificare il PATH (aggiungere una directory)

**Metodo permanente via PowerShell (consigliato per sviluppatori):**
```powershell
# Aggiungi una directory al PATH utente permanentemente
$nuovaDir = "C:\percorso\da\aggiungere"
$pathAttuale = [Environment]::GetEnvironmentVariable("PATH", "User")

if ($pathAttuale -notlike "*$nuovaDir*") {
    [Environment]::SetEnvironmentVariable("PATH", "$nuovaDir;$pathAttuale", "User")
    Write-Host "Directory aggiunta al PATH. Riapri il terminale per applicare."
} else {
    Write-Host "La directory e' gia' nel PATH."
}
```

**Metodo grafico (per chi preferisce i menu):**
1. Premi `Win + R`, digita `sysdm.cpl`, premi Invio.
2. Scheda "Avanzate" → "Variabili d'ambiente".
3. Nella sezione "Variabili utente", seleziona `Path` → "Modifica".
4. Clicca "Nuovo" e inserisci il percorso.
5. OK su tutto. Riapri il terminale.

#### Perche' uv gestisce il PATH automaticamente

Quando installi uv con il comando ufficiale, lo script di installazione aggiunge automaticamente `~\.local\bin` al PATH dell'utente. Non devi fare nulla manualmente.

uv, a sua volta, gestisce le versioni Python internamente. Quando usi `uv run python`, uv trova la versione corretta nel suo store interno senza che tu debba preoccuparti del PATH.

#### Debug: "comando non trovato"

Se digiti un comando e ottieni "is not recognized", segui questa procedura diagnostica:

```powershell
# 1. Controlla il PATH
$env:PATH -split ";" | Where-Object { $_ -ne "" }

# 2. Cerca il file nell'intero sistema (solo nella home)
Get-ChildItem -Recurse -ErrorAction SilentlyContinue "C:\Users\$env:USERNAME" -Filter "python.exe" | Select-Object FullName

# 3. Verifica eseguibili Windows standard
where.exe python
where.exe uv
```

---

### B2 — Virtual Environments: Ogni Progetto nel Suo Universo

#### Il problema che risolvono

Immagina di avere due progetti Python:
- **Progetto Alfa** (un sito web legacy): richiede `requests` versione 2.25 (vecchia, ma il progetto e' stato scritto cosi').
- **Progetto Beta** (un progetto nuovo): richiede `requests` versione 2.32 (l'ultima).

Se installi `requests 2.25` globalmente (nel Python di sistema), il Progetto Beta si rompe. Se installi `requests 2.32`, il Progetto Alfa potrebbe rompersi (se la nuova versione ha breaking changes).

Questo e' il problema fondamentale della gestione delle dipendenze: **conflitti di versione**.

#### La soluzione: l'analogia delle cucine separate

Immagina un ristorante con due chef. Chef Alfa cucina italiana e ha bisogno di parmigiano, basilico fresco, pasta. Chef Beta cucina giapponese e ha bisogno di soia, wasabi, riso a chicco corto.

Se condividono la stessa cucina, i loro ingredienti si mescolano. Caos.

La soluzione: **due cucine separate**. Ognuno ha i propri ingredienti nella propria cucina, non si influenzano mai.

I **virtual environment** (ambienti virtuali) sono le "cucine separate" per i progetti Python:
- Ogni progetto ha il proprio virtual environment.
- Le librerie installate in un environment non "vedono" quelle degli altri.
- Puoi avere `requests 2.25` nel Progetto Alfa e `requests 2.32` nel Progetto Beta senza conflitti.
- Se distruggi un environment, il Python di sistema non viene influenzato.

#### Il virtual environment nella pratica: struttura

Quando crei un virtual environment con uv nella tua cartella di progetto, si crea una sottocartella `.venv`:

```
mio-progetto/
├── .venv/                    <- Il virtual environment (NON toccare mai a mano)
│   ├── Scripts/
│   │   ├── python.exe        <- Il Python di QUESTO progetto
│   │   ├── pip.exe
│   │   └── Activate.ps1      <- Lo script per "entrare" nell'environment
│   └── Lib/
│       └── site-packages/    <- Qui finiscono le librerie installate
├── pyproject.toml            <- La lista delle dipendenze del progetto
├── uv.lock                   <- Il lock file (versioni esatte, riproducibili)
└── main.py                   <- Il tuo codice
```

#### Il flusso moderno con uv

**Creare un nuovo progetto:**
```powershell
uv init mio-progetto
cd mio-progetto
# Output atteso:
# Initialized project `mio-progetto` at `C:\...\mio-progetto`
```

**Vedere cosa ha creato uv:**
```powershell
ls
# Output:
# .python-version    (specifica la versione Python: "3.12")
# main.py            (file di esempio)
# pyproject.toml     (configurazione del progetto)
# README.md          (documentazione)
```

**Creare il virtual environment:**
```powershell
uv venv
# Output:
# Using CPython 3.12.7 interpreter at: C:\...
# Creating virtual environment at: .venv
# Activate with: .venv\Scripts\activate
```

**Aggiungere una dipendenza (es. la libreria requests):**
```powershell
uv add requests
# Output:
# Resolved 5 packages in 234ms
# Installed 5 packages in 87ms
#  + certifi==2024.x.x
#  + charset-normalizer==3.x.x
#  + idna==3.x.x
#  + requests==2.32.x
#  + urllib3==2.x.x
```

uv ha: scaricato `requests` e tutte le sue dipendenze, installato tutto nel `.venv`, aggiornato `pyproject.toml` con la dipendenza, creato/aggiornato `uv.lock` con le versioni esatte.

**Eseguire il codice nel virtual environment:**
```powershell
uv run python main.py
```

Con `uv run`, non devi "attivare" il virtual environment. uv trova automaticamente il `.venv` nella cartella del progetto e usa quello.

**Attivazione manuale (per sessioni interattive):**
```powershell
# Attiva il virtual environment
.\.venv\Scripts\Activate.ps1

# Il prompt cambia:
# (.venv) PS C:\...\mio-progetto>

# Ora puoi usare python direttamente
python main.py
python   # apre il REPL nel venv

# Disattiva quando hai finito
deactivate
```

#### Il file pyproject.toml

Quando uv crea un progetto, genera un file `pyproject.toml`. Questo file e' il "passaporto" del progetto — descrive tutto quello che un nuovo sviluppatore (o una nuova macchina) deve sapere per farlo funzionare.

```toml
[project]
name = "mio-progetto"
version = "0.1.0"
description = "Add your description here"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "requests>=2.32.0",    # uv aggiunge le dipendenze qui automaticamente
]
```

#### Il file uv.lock

Il file `uv.lock` e' diverso da `pyproject.toml`:
- `pyproject.toml` dice "ho bisogno di requests versione 2.32 o superiore".
- `uv.lock` dice "usiamo esattamente requests versione 2.32.3, insieme a certifi 2024.8.30, charset-normalizer 3.3.2, ...".

Il lock file garantisce che quando un collega clona il tuo progetto ed esegue `uv sync`, ottiene **esattamente** le stesse versioni che hai tu. Nessuna sorpresa, nessun "ma sul mio computer funzionava".

```powershell
# Clona un progetto e ripristina le dipendenze esatte
git clone https://github.com/collega/progetto.git
cd progetto
uv sync    # installa tutto esattamente come nel lock file
uv run python -m progetto   # funziona!
```

#### Confronto: vecchio metodo vs uv

| Operazione | Metodo classico | Con uv |
|------------|-----------------|--------|
| Creare venv | `python -m venv .venv` | `uv venv` |
| Attivare venv | `.\.venv\Scripts\Activate.ps1` | Opzionale con `uv run` |
| Installare pacchetto | `pip install requests` | `uv add requests` |
| Salvare dipendenze | `pip freeze > requirements.txt` | Automatico in `pyproject.toml` |
| Ripristinare dipendenze | `pip install -r requirements.txt` | `uv sync` |
| Versioni esatte (lock) | `pip-compile` (tool separato) | Automatico in `uv.lock` |

---

### B3 — Git: Salva il Tuo Lavoro nel Tempo

#### Perche' anche i progetti piccoli hanno bisogno di Git

Hai mai cancellato accidentalmente un file importante? Hai mai modificato del codice e poi voluto tornare alla versione precedente? Hai mai perso ore di lavoro per un crash del computer?

**Git** e' un sistema di version control: tiene traccia di ogni modifica al tuo codice, ti permette di tornare a qualsiasi versione passata, e facilita la collaborazione.

Analogia: Git e' come un sistema di backup infinito, ma intelligente. Non salva solo "copia del file alle 14:32" — salva ogni "stato significativo" del progetto con una descrizione di cosa e' cambiato e perche'.

#### Installazione di Git su Windows

```powershell
winget install -e --id Git.Git
```

Output atteso:
```
Found Git [Git.Git] Version 2.45.x
...
Successfully installed
```

Apri una **nuova** finestra di PowerShell, poi verifica:
```powershell
git --version
# Output: git version 2.45.x.windows.1
```

#### Configurazione iniziale (da fare una sola volta per macchina)

```powershell
# Il tuo nome (apparira' in ogni commit)
git config --global user.name "Il Tuo Nome"

# La tua email
git config --global user.email "tua-email@esempio.com"

# Editor predefinito per i messaggi di commit
git config --global core.editor "code --wait"

# Nome del branch predefinito (convenzione moderna)
git config --global init.defaultBranch main

# Gestione dei fine riga (importante su Windows)
git config --global core.autocrlf true

# Verifica
git config --global --list
```

#### I comandi Git essenziali per cominciare

```powershell
# Inizializzare Git in una cartella esistente
git init

# Vedere lo stato del progetto (cosa e' cambiato?)
git status

# Aggiungere file all'area di staging (preparare per il commit)
git add nome-file.py          # un file specifico
git add .                     # tutti i file modificati

# Creare un commit (salvare lo stato)
git commit -m "feat: aggiunge la funzione di calcolo"

# Vedere la storia dei commit
git log --oneline

# Tornare a un commit precedente (per ispezione)
git checkout abc123def        # usa il codice hash del commit
git checkout -                # torna al branch attuale
```

> **Approfondimento:** Git merita un tutorial dedicato. Trovi `tutorial_00_git_per_pythonisti.md` in questa stessa cartella dei tutorial.

---

### B4 — Come Python Esegue il Codice

#### Dal file .py al risultato sullo schermo

Quando esegui `python mio_programma.py`, cosa succede esattamente? Capire questo processo ti aiutera' a interpretare gli errori e a capire perche' Python si comporta in certi modi.

**Il ciclo di esecuzione:**

```
Tu scrivi:          mio_programma.py (testo leggibile da umani)
                           |
                     [ Python legge ]
                           |
                    Bytecode (.pyc)    <- File intermedio
                     (nella cartella __pycache__)
                           |
                    [ CPython lo esegue ]
                           |
                       Risultato sullo schermo
```

**Passo 1 — Parsing (analisi sintattica):**
Python legge il tuo file `.py` come testo e lo analizza per capire la struttura. Controlla che la sintassi sia corretta (parentesi bilanciate, indentazione corretta, ecc.). Se trova un errore di sintassi, si ferma qui con un `SyntaxError`.

**Passo 2 — Compilazione a Bytecode:**
Python compila il codice sorgente in **bytecode** — istruzioni in un formato intermedio, piu' vicino alla macchina ma non specifico per nessuna CPU in particolare. Il bytecode viene salvato in file `.pyc` nella cartella `__pycache__`. La prossima volta che esegui lo stesso file non modificato, Python salta il passo di compilazione e usa il `.pyc` gia' pronto (piu' veloce).

**Passo 3 — Esecuzione da parte di CPython:**
La **CPython Virtual Machine** (VM) legge il bytecode istruzione per istruzione e le esegue. "CPython" e' l'implementazione standard di Python, scritta in linguaggio C. E' quella che installi da python.org o con uv.

#### Perche' Python e' "interpretato"

La distinzione non e' cosi' netta come sembra, ma l'analogia e' utile:

- **Linguaggio compilato** (es. C, C++, Rust): il codice viene trasformato completamente in istruzioni macchina prima di essere eseguito. Come tradurre un libro dall'italiano al francese: prima traduci tutto, poi il lettore francese legge il libro gia' tradotto.

- **Linguaggio interpretato** (es. Python, JavaScript): il codice viene eseguito "in tempo reale" da un interprete. Come un traduttore simultaneo: sente la frase in italiano e la traduce subito in francese, frase per frase, senza aspettare la fine del libro.

In pratica, Python usa entrambi gli approcci (il bytecode e' una pre-compilazione), ma dal punto di vista del programmatore, Python si comporta come un linguaggio interpretato: puoi eseguire codice riga per riga nel REPL senza compilare nulla.

#### La cartella __pycache__

Quando esegui per la prima volta `python mio_programma.py`, Python crea automaticamente:
```
mio-progetto/
├── mio_programma.py
└── __pycache__/
    └── mio_programma.cpython-312.pyc    <- Bytecode pre-compilato
```

Non devi preoccuparti di questa cartella. Python la gestisce automaticamente. La cartella `__pycache__` **non va committata in Git** — e' per questo che nei `.gitignore` vedi sempre `__pycache__/`.

#### CPython, PyPy, e le altre implementazioni

| Implementazione | Scritto in | Punto di forza | Quando usarla |
|-----------------|-----------|----------------|---------------|
| **CPython** | C | Compatibilita' massima, tutte le librerie C funzionano | Sempre, per default |
| **PyPy** | Python + C | 5-10x piu' veloce per codice Python puro | Applicazioni CPU-intensive senza librerie C |
| **GraalPy** | Java (GraalVM) | Integrazione con ecosistema Java | Ambienti enterprise Java |
| **Jython** | Java | Interoperabilita' con Java (legacy) | Vecchi sistemi Java |

Per il 99% dei casi, userai CPython. Non pensarci per ora.

---

### B5 — Errori Comuni nell'Ambiente di Sviluppo

Questa sezione raccoglie i 10 problemi piu' frequenti incontrati dai principianti nell'ambiente Windows. Per ogni problema: sintomo, causa, soluzione.

#### Errore 1: python non trovato dopo l'installazione

```
python : The term 'python' is not recognized as the name of a cmdlet...
```

**Causa:** La finestra del terminale era aperta prima dell'installazione. Il PATH viene letto solo all'avvio del terminale.

**Soluzione:** Chiudi e riapri il terminale. Se il problema persiste, verifica che l'installazione abbia aggiunto Python al PATH:
```powershell
$env:PATH -split ";" | Where-Object { $_ -like "*Python*" -or $_ -like "*python*" }
```

#### Errore 2: Execution Policy blocca l'attivazione del venv

```
.\.venv\Scripts\Activate.ps1 cannot be loaded because running scripts is disabled
```

**Causa:** PowerShell, per sicurezza, blocca per default l'esecuzione degli script.

**Soluzione:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\.venv\Scripts\Activate.ps1   # riprova
```

#### Errore 3: VS Code non trova l'interprete Python

**Sintomo:** Pylance evidenzia in rosso tutti gli import, con errori come "Import 'requests' could not be resolved".

**Causa:** VS Code non sa quale Python usare, o sta usando il Python di sistema invece del `.venv` del progetto.

**Soluzione:**
```
1. Ctrl+Shift+P -> "Python: Select Interpreter"
2. Seleziona ".venv/Scripts/python.exe" (quello con il percorso del progetto)
3. Riavvia VS Code se il problema persiste
```

#### Errore 4: uv non trovato dopo l'installazione

```
uv : The term 'uv' is not recognized...
```

**Causa:** La directory di uv non e' nel PATH, o il terminale non e' stato riavviato.

**Soluzione:**
```powershell
# Aggiorna il PATH nella sessione corrente
$env:PATH = "$env:USERPROFILE\.local\bin;$env:PATH"
uv --version   # verifica
# Se funziona, riapri il terminale per rendere la modifica permanente
```

#### Errore 5: pip installa nel Python di sistema invece del venv

**Sintomo:** Installi un pacchetto ma non lo vedi nel `.venv` del progetto.

**Causa:** Il venv non e' attivato.

**Soluzione:** Usa sempre `uv add` invece di `pip install`:
```powershell
# SBAGLIATO:
pip install requests

# CORRETTO:
uv add requests

# Oppure verifica se il venv e' attivo:
$env:VIRTUAL_ENV   # se e' vuoto, nessun venv e' attivo
.\.venv\Scripts\Activate.ps1   # attiva
```

#### Errore 6: SyntaxError — "invalid syntax" su codice che sembra corretto

**Sintomo:**
```
  File "mio_programma.py", line 5
    print("ciao"
               ^
SyntaxError: '(' was never closed
```

**Causa:** Parentesi, virgolette o parentesi quadre non bilanciate. Python indica la riga dove ha rilevato il problema, ma l'errore reale potrebbe essere alla riga precedente.

**Soluzione:** Cerca la parentesi o la virgoletta aperta non chiusa. VS Code evidenzia le parentesi bilanciate: clicca vicino a `(` e VS Code evidenzia la corrispondente `)`.

#### Errore 7: ModuleNotFoundError — libreria non trovata

**Sintomo:**
```
ModuleNotFoundError: No module named 'requests'
```

**Causa:** La libreria non e' installata nel venv attivo.

**Soluzione:**
```powershell
uv add requests
uv run python mio_programma.py
```

#### Errore 8: IndentationError — problema di indentazione

**Sintomo:**
```
IndentationError: expected an indented block after 'if' statement on line 3
```

**Causa:** Python usa l'indentazione (gli spazi all'inizio della riga) per definire i blocchi di codice.

```python
# SBAGLIATO (nessuna indentazione dopo if):
if x > 0:
print("positivo")   # IndentationError!

# CORRETTO (4 spazi di indentazione):
if x > 0:
    print("positivo")   # OK
```

**Soluzione:** In VS Code, assicurati che il file usi 4 spazi per ogni livello di indentazione. VS Code mostra in basso a destra "Spaces: 4" se la configurazione e' corretta.

#### Errore 9: caratteri Unicode non visualizzati correttamente

**Sintomo:** I caratteri accentati (a', e', i') appaiono come `?` o sequenze strane nel terminale.

**Causa:** Il terminale Windows usa per default un encoding diverso da UTF-8.

**Soluzione:**
```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001
```

In Python, assicurati che il file `.py` sia salvato in UTF-8 (e' il default in VS Code — controlla in basso a destra: dovrebbe mostrare "UTF-8").

#### Errore 10: FileNotFoundError — file non trovato

**Sintomo:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'dati.csv'
```

**Causa:** Il programma cerca il file nella directory corrente, ma il file non e' li'. Questo accade spesso quando esegui lo script da una directory diversa da quella del file.

**Soluzione:**
```powershell
# Verifica dove sei
pwd
# Vai nella cartella dove si trovano il file .py e dati.csv
cd C:\percorso\al\progetto
uv run python analisi.py
```

In Python, usa sempre `pathlib.Path` per i percorsi file:
```python
from pathlib import Path

# ROBUSTO: funziona indipendentemente da dove esegui lo script
BASE_DIR = Path(__file__).parent
dati = BASE_DIR / "dati.csv"   # percorso assoluto
```

---

*Fine Parte B. Prosegui con la Parte C per gli esercizi pratici guidati.*

---

## Parte C: Esercizi Pratici Guidati

> Gli esercizi di questa sezione devono essere eseguiti in ordine. Ogni esercizio costruisce su quello precedente. Non saltare passaggi — anche se ti sembrano semplici, l'obiettivo e' che le mani imparino i movimenti.

### C1 (Guidato): Installazione Completa da Zero

Questa checklist ti guida attraverso l'installazione completa dell'ambiente. Segui ogni passo nell'ordine indicato e verifica l'output atteso prima di procedere.

**Precondizioni:** PC Windows 10 o Windows 11, connessione internet, circa 30 minuti di tempo.

---

**Passo 1 — Apri PowerShell**

Premi `Win` sulla tastiera, digita `powershell`, premi Invio.

Verifica che il prompt mostri qualcosa del tipo:
```
PS C:\Users\TuoNome>
```

Output atteso: prompt di PowerShell attivo.

---

**Passo 2 — Installa uv**

Copia e incolla questo comando (copia dall'inizio, incluso `powershell`):

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Output atteso (i numeri di versione varieranno):
```
Downloading uv 0.7.x (x86_64-pc-windows-msvc)
Installing to C:\Users\TuoNome\.local\bin
uv
uvx
Everything's installed!
```

Se vedi un errore su "ExecutionPolicy", prova prima:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
poi ripeti il comando di installazione di uv.

---

**Passo 3 — Riapri PowerShell**

Chiudi la finestra di PowerShell attuale. Aprila di nuovo dal menu Start. Questo aggiorna il PATH.

---

**Passo 4 — Verifica uv**

```powershell
uv --version
```

Output atteso:
```
uv 0.7.x (qualcosa)
```

Se vedi questo: ottimo, uv e' installato. Vai al Passo 5.
Se vedi "not recognized": esegui `$env:PATH = "$env:USERPROFILE\.local\bin;$env:PATH"` e riprova.

---

**Passo 5 — Installa Python 3.12**

```powershell
uv python install 3.12
```

Output atteso (richiede 1-3 minuti per il download):
```
Searching for Python versions matching: Python 3.12
Installed Python 3.12.x in XX.XXs
 + cpython-3.12.x-windows-x86_64-none
```

---

**Passo 6 — Verifica Python**

```powershell
uv run python --version
```

Output atteso:
```
Python 3.12.x
```

---

**Passo 7 — Imposta l'Execution Policy**

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Quando chiede conferma, digita `S` o `A` e premi Invio.

Verifica:
```powershell
Get-ExecutionPolicy -Scope CurrentUser
```
Output atteso: `RemoteSigned`

---

**Passo 8 — Installa VS Code**

```powershell
winget install -e --id Microsoft.VisualStudioCode
```

Output atteso:
```
Found Visual Studio Code [Microsoft.VisualStudioCode] Version 1.90.x
...
Successfully installed
```

Se winget non e' disponibile sul tuo sistema, scarica VS Code manualmente da https://code.visualstudio.com/

---

**Passo 9 — Riapri PowerShell e verifica VS Code**

Chiudi e riapri PowerShell, poi:
```powershell
code --version
```

Output atteso:
```
1.90.x
abc123...
x64
```

---

**Passo 10 — Installa le estensioni VS Code**

```powershell
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
code --install-extension ms-python.debugpy
code --install-extension charliermarsh.ruff
code --install-extension tamasfe.even-better-toml
```

Output atteso per ognuno:
```
Installing extensions...
Extension 'ms-python.python' v20xx.x.x was successfully installed.
```

---

**Passo 11 — Installa Git**

```powershell
winget install -e --id Git.Git
```

Riapri PowerShell e verifica:
```powershell
git --version
```
Output atteso: `git version 2.45.x.windows.1`

---

**Passo 12 — Configura Git**

Sostituisci il nome e l'email con i tuoi dati reali:
```powershell
git config --global user.name "Mario Rossi"
git config --global user.email "mario.rossi@esempio.com"
git config --global core.editor "code --wait"
git config --global init.defaultBranch main
git config --global core.autocrlf true
```

Verifica:
```powershell
git config --global --list
```
Output atteso: una lista con user.name, user.email, e le altre impostazioni.

---

**Passo 13 — Crea la cartella dei progetti**

```powershell
mkdir "$HOME\progetti"
Write-Host "Cartella creata in: $HOME\progetti"
```

---

**Passo 14 — Crea un progetto di test**

```powershell
cd "$HOME\progetti"
uv init test-setup
cd test-setup
uv venv
.\.venv\Scripts\Activate.ps1
```

Output atteso dopo l'attivazione: il prompt inizia con `(.venv)`

---

**Passo 15 — Esegui il programma di test**

```powershell
# Stai ancora nella cartella test-setup con .venv attivo
uv run python main.py
```

Output atteso:
```
Hello from test-setup!
```

(uv init crea un `main.py` con un semplice Hello World)

**Verifica finale:**
```powershell
deactivate   # disattiva il venv
cd ..
```

Hai completato l'installazione. Tutti e 15 i passi sono stati eseguiti con successo.

---

### C2 (Guidato): Il Tuo Primo Progetto Python con uv

In questo esercizio crei un progetto Python strutturato da zero, lo apri in VS Code, e scrivi un programma che funziona.

**Obiettivo:** Capire il flusso di lavoro completo: crea → scrivi → esegui.

**Passo 1 — Vai nella cartella progetti:**
```powershell
cd "$HOME\progetti"
```

**Passo 2 — Crea il progetto:**
```powershell
uv init salutatore
```

Output:
```
Initialized project `salutatore` at `C:\Users\...\progetti\salutatore`
```

**Passo 3 — Entra nel progetto:**
```powershell
cd salutatore
ls
```

Output (elenco dei file creati da uv):
```
.python-version
main.py
pyproject.toml
README.md
```

**Passo 4 — Crea il virtual environment:**
```powershell
uv venv
```

Output:
```
Using CPython 3.12.x interpreter at: ...
Creating virtual environment at: .venv
```

**Passo 5 — Apri in VS Code:**
```powershell
code .
```

VS Code si apre con la cartella `salutatore`. In basso a destra dovresti vedere Python selezionato. Se non lo vede automaticamente, premi `Ctrl+Shift+P` → "Python: Select Interpreter" → seleziona `.venv\Scripts\python.exe`.

**Passo 6 — Sostituisci il contenuto di main.py:**

Clicca su `main.py` nell'Explorer di VS Code (a sinistra). Cancella il contenuto esistente e scrivi:

```python
def saluta(nome: str) -> str:
    """Restituisce un messaggio di saluto."""
    return f"Ciao, {nome}! Benvenuto nel mondo di Python."


def main() -> None:
    """Punto di ingresso principale del programma."""
    nomi = ["Alice", "Marco", "Giulia"]
    for nome in nomi:
        messaggio = saluta(nome)
        print(messaggio)


if __name__ == "__main__":
    main()
```

Salva con `Ctrl+S`.

**Passo 7 — Esegui il programma dal terminale di VS Code:**

Apri il terminale integrato di VS Code con `` Ctrl+` ``. Poi:
```powershell
uv run python main.py
```

Output atteso:
```
Ciao, Alice! Benvenuto nel mondo di Python.
Ciao, Marco! Benvenuto nel mondo di Python.
Ciao, Giulia! Benvenuto nel mondo di Python.
```

**Passo 8 — Inizializza Git:**
```powershell
git init
git add .
git commit -m "feat: aggiunge il salutatore"
```

Output del commit:
```
[main (root-commit) abc1234] feat: aggiunge il salutatore
 5 files changed, 20 insertions(+)
 create mode 100644 .python-version
 create mode 100644 .gitignore   (se presente)
 create mode 100644 main.py
 create mode 100644 pyproject.toml
 create mode 100644 README.md
```

Hai completato il tuo primo progetto Python strutturato con uv e Git.

---

### C3 (Guidato): Creare uno Script che Chiede il Nome

In questo esercizio scrivi un programma interattivo che chiede il nome all'utente e risponde in modo personalizzato. Impari a usare `input()` e `print()`.

**Obiettivo:** Capire il ciclo input → elaborazione → output.

**Passo 1 — Crea un nuovo file nel progetto salutatore:**

Nel terminale integrato di VS Code (assicurati di essere nella cartella `salutatore`):
```powershell
pwd   # verifica di essere in C:\Users\...\progetti\salutatore
```

**Passo 2 — Crea il file interattivo:**

In VS Code, crea un nuovo file (`File` → `New File`) e salvalo come `interattivo.py` nella cartella `salutatore`.

**Passo 3 — Scrivi il codice passo per passo:**

```python
# interattivo.py
# Un programma che dialoga con l'utente

# Chiedi il nome
nome = input("Come ti chiami? ")

# Elabora l'input
nome_maiuscolo = nome.strip().title()   # rimuove spazi, mette maiuscole corrette

# Rispondi
print(f"Ciao, {nome_maiuscolo}!")
print(f"Piacere di conoscerti.")

# Chiedi l'eta'
eta_str = input("Quanti anni hai? ")

# Converti da stringa a numero intero
eta = int(eta_str)

# Calcola qualcosa di interessante
anni_alla_pensione = max(0, 67 - eta)

# Mostra il risultato
if eta < 18:
    print(f"Sei giovane! Hai ancora {18 - eta} anni prima di essere maggiorenne.")
elif eta < 30:
    print(f"Sei nel pieno della formazione. Goditi questi anni!")
else:
    print(f"Mancano circa {anni_alla_pensione} anni alla pensione. Niente paura!")

print("\nGrazie per aver usato il mio programma!")
```

**Passo 4 — Esegui e interagisci:**

```powershell
uv run python interattivo.py
```

Il programma si mette in attesa. Digita il tuo nome e premi Invio, poi digita la tua eta' e premi Invio.

Esempio di sessione completa:
```
Come ti chiami? marco
Ciao, Marco!
Piacere di conoscerti.
Quanti anni hai? 25
Sei nel pieno della formazione. Goditi questi anni!

Grazie per aver usato il mio programma!
```

**Analisi del codice riga per riga:**

| Riga | Cosa fa |
|------|---------|
| `nome = input("Come ti chiami? ")` | Mostra il messaggio, aspetta che l'utente digiti qualcosa e prema Invio. Quello che l'utente digita diventa il valore della variabile `nome`. |
| `nome.strip().title()` | `.strip()` rimuove gli spazi all'inizio e alla fine. `.title()` mette la prima lettera di ogni parola in maiuscolo. |
| `int(eta_str)` | `input()` restituisce sempre una stringa. `int()` converte la stringa "25" nel numero intero 25. |
| `if ... elif ... else` | Struttura condizionale: esegue blocchi diversi a seconda del valore di `eta`. |

**Cosa succede se l'utente digita una lettera invece di un numero per l'eta'?**

```
Quanti anni hai? ciao
```

Ottieni un errore:
```
ValueError: invalid literal for int() with base 10: 'ciao'
```

Questo e' il comportamento corretto: il programma segnala esplicitamente che l'input non e' valido. Nel Modulo 01 imparerai a gestire questi errori con `try/except`.

---

### C4 (Semi-autonomo): Configurare VS Code per Python

In questo esercizio configuri VS Code con le impostazioni professionali per Python. Le istruzioni ti guidano, ma devi trovare tu le voci giuste nell'interfaccia.

**Obiettivo:** Imparare a navigare le impostazioni di VS Code e capire cosa fa ogni opzione.

**Passo 1 — Apri le impostazioni JSON:**

Premi `Ctrl+Shift+P`, digita "Open User Settings JSON", premi Invio.

Si apre il file `settings.json`. Se e' vuoto, contiene `{}`. Se ha gia' contenuto, aggiungerai dentro le parentesi graffe esistenti.

**Passo 2 — Aggiungi le impostazioni Python:**

Sostituisci il contenuto di `settings.json` con il seguente (se hai gia' impostazioni, integra le voci Python senza cancellare le altre):

```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/.venv/Scripts/python.exe",
    "python.terminal.activateEnvironment": true,
    "python.terminal.activateEnvInCurrentTerminal": true,
    "python.languageServer": "Pylance",
    "python.analysis.typeCheckingMode": "basic",
    "python.analysis.autoImportCompletions": true,
    "python.analysis.inlayHints.variableTypes": true,
    "python.analysis.inlayHints.functionReturnTypes": true,
    "[python]": {
        "editor.defaultFormatter": "charliermarsh.ruff",
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
            "source.fixAll.ruff": "explicit",
            "source.organizeImports.ruff": "explicit"
        }
    },
    "editor.rulers": [88],
    "editor.tabSize": 4,
    "editor.insertSpaces": true,
    "files.trimTrailingWhitespace": true,
    "files.insertFinalNewline": true,
    "terminal.integrated.defaultProfile.windows": "PowerShell",
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        "**/.pytest_cache": true,
        "**/.ruff_cache": true
    }
}
```

Salva il file (`Ctrl+S`).

**Passo 3 — Verifica formatOnSave:**

Apri `main.py` del progetto `salutatore`. Aggiungi degli spazi in piu' a caso:
```python
def saluta(   nome: str) ->str:
    return f"Ciao,   {nome}!"
```

Salva con `Ctrl+S`. Ruff dovrebbe formattare automaticamente il codice riportandolo alla forma corretta.

Se la formattazione automatica non funziona:
1. Verifica che l'estensione Ruff sia installata (`code --install-extension charliermarsh.ruff`).
2. Riavvia VS Code.
3. Verifica che il file sia salvato con estensione `.py`.

**Passo 4 — Verifica Pylance:**

In `main.py`, aggiungi una riga con un errore di tipo:
```python
risultato = saluta(42)   # saluta si aspetta str, non int
```

Pylance dovrebbe evidenziare `42` con una sottolineatura rossa/gialla e mostrare un messaggio come "Argument of type 'int' is not assignable to parameter 'nome' of type 'str'".

Cancella la riga errata.

**Passo 5 — Impara le scorciatoie essenziali:**

Prova ognuna di queste in `main.py`:

| Scorciatoia | Cosa fa | Provala su |
|-------------|---------|------------|
| `F12` | Vai alla definizione | Clicca su `saluta` nella riga `saluta(nome)` |
| `Ctrl+.` | Quick fix / auto-import | Aggiungi `import json` in cima, poi rimuovilo e aspetta il suggerimento |
| `Ctrl+/` | Commenta/decommenta | Seleziona 3 righe e premi `Ctrl+/` |
| `Shift+Alt+F` | Formatta documento | Premi quando il file e' aperto |
| `Ctrl+Shift+M` | Mostra problemi | Apre il pannello con errori e avvisi |

---

### C5 (Autonomo): Creare un Progetto "calcolatrice"

Questo esercizio e' autonomo: ricevi le specifiche ma devi implementarle tu senza istruzioni passo per passo. E' normale fare errori — usali per imparare.

**Obiettivo:** Creare un progetto Python strutturato e funzionante che simula una calcolatrice semplice.

**Specifiche:**

1. **Struttura del progetto:** Crea un nuovo progetto uv chiamato `calcolatrice` nella cartella `$HOME\progetti`.

2. **File principale (`main.py`):** Il programma deve:
   - Chiedere due numeri all'utente
   - Chiedere quale operazione eseguire (+, -, *, /)
   - Calcolare il risultato
   - Mostrare il risultato in modo leggibile
   - Gestire la divisione per zero (mostrare un messaggio di errore invece di crashare)

3. **Funzioni:** Il codice deve usare funzioni separate per ogni operazione.

4. **Git:** Il progetto deve avere almeno un commit con messaggio significativo.

**Hint per iniziare:**

```python
# Struttura suggerita (non e' l'unica soluzione corretta):

def somma(a: float, b: float) -> float:
    return a + b

def sottrai(a: float, b: float) -> float:
    # ... implementa tu

def moltiplica(a: float, b: float) -> float:
    # ... implementa tu

def dividi(a: float, b: float) -> float | None:
    if b == 0:
        # ... gestisci l'errore
    return a / b

def main() -> None:
    # Chiedi i due numeri
    # Chiedi l'operazione
    # Esegui e mostra il risultato

if __name__ == "__main__":
    main()
```

**Criteri di successo:**
- Il programma esegue senza errori con input validi.
- La divisione per zero mostra un messaggio utile invece di crashare.
- Il codice e' indentato correttamente (Ruff non segnala errori).
- Il progetto ha almeno un commit Git.

**Esempio di output:**
```
--- Calcolatrice Python ---
Inserisci il primo numero: 15
Inserisci il secondo numero: 4
Operazione (+, -, *, /): *
Risultato: 15.0 * 4.0 = 60.0
```

**Soluzione di riferimento (non guardare prima di aver provato!):**

Una possibile implementazione:

```python
def somma(a: float, b: float) -> float:
    return a + b


def sottrai(a: float, b: float) -> float:
    return a - b


def moltiplica(a: float, b: float) -> float:
    return a * b


def dividi(a: float, b: float) -> float | None:
    if b == 0:
        print("Errore: divisione per zero non consentita.")
        return None
    return a / b


OPERAZIONI = {
    "+": somma,
    "-": sottrai,
    "*": moltiplica,
    "/": dividi,
}


def main() -> None:
    print("--- Calcolatrice Python ---")

    try:
        a = float(input("Inserisci il primo numero: "))
        b = float(input("Inserisci il secondo numero: "))
    except ValueError:
        print("Errore: devi inserire numeri validi.")
        return

    operazione = input("Operazione (+, -, *, /): ").strip()

    if operazione not in OPERAZIONI:
        print(f"Errore: operazione '{operazione}' non riconosciuta.")
        return

    funzione = OPERAZIONI[operazione]
    risultato = funzione(a, b)

    if risultato is not None:
        print(f"Risultato: {a} {operazione} {b} = {risultato}")


if __name__ == "__main__":
    main()
```

---

*Fine Parte C. Prosegui con la Parte D per gli approfondimenti per esperti.*

---

## Parte D: Approfondimento per Esperti

> Questa sezione e' pensata per chi vuole capire il funzionamento interno degli strumenti, configurare l'ambiente in modo professionale, e anticipare le domande avanzate. Puoi leggerla dopo aver completato le Parti A, B e C.

### D1 — uv Internals: Come Gestisce le Dipendenze

#### La struttura interna di uv

uv non e' semplicemente "pip piu' veloce". E' un gestore di ambienti e dipendenze con un design radicalmente diverso. Capire la sua architettura ti aiuta a usarlo meglio e a diagnosticare problemi.

**La cache globale di uv:**

uv usa una cache globale condivisa tra tutti i progetti sulla macchina:

```
C:\Users\TuoNome\.cache\uv\
├── archive-v0\         <- Archivi .tar.gz e .whl scaricati
├── builds-v0\          <- Pacchetti costruiti localmente
└── environments-v0\    <- Virtual environment (solo se creati globalmente)
```

Quando esegui `uv add requests`, uv:
1. Controlla se `requests` e' gia' nella cache. Se si', usa quello (nessun download).
2. Se non c'e', scarica il file `.whl` da PyPI e lo mette in cache.
3. Copia (o hard-link, piu' efficiente) i file dalla cache al `.venv` del progetto.

Questo significa che installare la stessa libreria in 10 progetti diversi non scarica 10 volte il file — il download avviene una sola volta. Questo e' uno dei motivi per cui uv e' cosi' veloce.

**Vedere la dimensione della cache:**
```powershell
$cachePath = "$env:USERPROFILE\.cache\uv"
if (Test-Path $cachePath) {
    $size = (Get-ChildItem $cachePath -Recurse -File | Measure-Object -Property Length -Sum).Sum
    Write-Host "Dimensione cache uv: $([Math]::Round($size / 1MB, 1)) MB"
}
```

**Pulire la cache (raramente necessario):**
```powershell
uv cache clean   # rimuove tutta la cache
uv cache prune   # rimuove solo le voci obsolete (piu' sicuro)
```

#### Il processo di risoluzione delle dipendenze

Quando aggiungi una dipendenza con `uv add`, uv esegue un processo chiamato **dependency resolution** (risoluzione delle dipendenze):

1. **Legge** `pyproject.toml` per sapere le dipendenze dirette del progetto.
2. **Scarica** i metadati di ogni pacchetto da PyPI (non i pacchetti interi, solo le informazioni).
3. **Analizza** le dipendenze transitive: se vuoi `requests`, requests dipende da `urllib3`, `certifi`, `idna`, `charset-normalizer`. Anche queste vanno installate.
4. **Risolve i conflitti**: se due pacchetti richiedono versioni diverse della stessa libreria, uv trova una versione compatibile con entrambi (o segnala un conflitto irrisolvibile).
5. **Scrive** il risultato in `uv.lock`.

Il file `uv.lock` e' il risultato di questo processo: una lista completa, con versioni esatte, di tutto quello che deve essere installato.

```toml
# Esempio di contenuto uv.lock (semplificato)
version = 1
requires-python = ">=3.12"

[[package]]
name = "certifi"
version = "2024.8.30"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/...", hash = "sha256:..." }

[[package]]
name = "requests"
version = "2.32.3"
dependencies = [
  { name = "certifi" },
  { name = "charset-normalizer" },
  { name = "idna" },
  { name = "urllib3" },
]
```

#### Workspace e monorepo con uv

Per progetti grandi con piu' sotto-pacchetti (monorepo), uv supporta i **workspace**:

```
mio-monorepo/
├── pyproject.toml       <- Root del workspace
├── packages/
│   ├── core/
│   │   ├── pyproject.toml
│   │   └── src/core/...
│   ├── api/
│   │   ├── pyproject.toml
│   │   └── src/api/...
│   └── cli/
│       ├── pyproject.toml
│       └── src/cli/...
└── uv.lock              <- Lock file unico per tutto il workspace
```

Il `pyproject.toml` root dichiara il workspace:
```toml
[tool.uv.workspace]
members = ["packages/*"]
```

I vantaggi: un solo lock file per tutto il monorepo, dipendenze condivise gestite in un unico posto, build e test coordinati.

#### Confronto con pip, poetry e conda

| Funzionalita' | pip | Poetry | conda | uv |
|---------------|-----|--------|-------|-----|
| Installazione pacchetti | Si' | Si' | Si' | Si' |
| Lock file | No (pip-tools) | Si' | Si' | Si' |
| Gestione venv | No (venv separato) | Si' | Si' | Si' |
| Gestione versioni Python | No (pyenv separato) | No | Si' | Si' |
| Velocita' | Lenta | Media | Lenta | Velocissima (Rust) |
| Workspace/monorepo | No | Limitato | No | Si' |
| Compatibilita' PyPI | Completa | Completa | Parziale | Completa |
| Formato configurazione | requirements.txt | pyproject.toml | environment.yml | pyproject.toml |

---

### D2 — CPython vs PyPy vs GraalPy

#### Quando le alternative a CPython hanno senso

CPython e' l'implementazione standard di Python, ma non e' la piu' veloce. In scenari specifici, implementazioni alternative possono offrire vantaggi significativi.

**CPython:**

- **Implementazione:** il codice Python viene compilato in bytecode, poi il bytecode viene interpretato dalla VM CPython scritta in C.
- **Punto di forza:** compatibilita' massima. Tutte le librerie C (NumPy, Pillow, cryptography) funzionano perche' sono scritte come estensioni CPython.
- **Limite:** il GIL (Global Interpreter Lock) impedisce la vera parallelizzazione di codice Python in piu' thread CPU.
- **Quando usarlo:** sempre, a meno che non hai un caso d'uso molto specifico che giustifica il cambio.

**PyPy:**

- **Implementazione:** usa un compilatore JIT (Just-In-Time). Il codice Python viene compilato in codice macchina nativo durante l'esecuzione, basandosi su quale codice viene eseguito piu' frequentemente.
- **Punto di forza:** 5-10x piu' veloce di CPython per codice Python puro (algoritmi, loop intensivi).
- **Limite:** le librerie C che usano l'API interna di CPython non funzionano direttamente (NumPy, pandas). C'e' compatibilita' parziale tramite cpyext, ma non e' trasparente.
- **Quando usarlo:** applicazioni computazionalmente intensive che non dipendono da librerie C native (simulazioni, elaborazione di testi, parsing, web scraping).

```powershell
# Installare PyPy con uv (se disponibile)
uv python install pypy@3.10

# Eseguire con PyPy
uv run --python pypy3.10 python benchmark.py
```

**Benchmarks tipici (operazione di loop intensivo):**

```python
# Benchmark: calcola numeri di Fibonacci in modo naive
def fib(n):
    if n <= 1:
        return n
    return fib(n-1) + fib(n-2)

# fib(35): CPython ~3.5 secondi, PyPy ~0.4 secondi
```

**GraalPy:**

- **Implementazione:** Python su GraalVM, una VM poliglotta sviluppata da Oracle.
- **Punto di forza:** integrazione con l'ecosistema Java e altri linguaggi JVM. Possibilita' di usare librerie Java da Python e viceversa.
- **Quando usarlo:** ambienti enterprise che devono integrare Python con sistemi Java esistenti.
- **Limitazione:** overhead di avvio significativo, meno compatibile con librerie Python native.

**Riassunto della scelta:**

```
Hai bisogno di NumPy, pandas, Pillow, ecc.? -> Usa CPython
Hai un algoritmo Python puro che e' troppo lento? -> Prova PyPy
Devi integrare con Java? -> Considera GraalPy
```

---

### D3 — Configurazione Avanzata di VS Code

#### settings.json completo per Python professionale

Il file `settings.json` che hai configurato nell'esercizio C4 era una versione base. Ecco la configurazione completa con tutte le opzioni spiegate:

```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/.venv/Scripts/python.exe",
    "python.terminal.activateEnvironment": true,
    "python.terminal.activateEnvInCurrentTerminal": true,

    "python.languageServer": "Pylance",
    "python.analysis.typeCheckingMode": "basic",
    "python.analysis.autoImportCompletions": true,
    "python.analysis.inlayHints.variableTypes": true,
    "python.analysis.inlayHints.functionReturnTypes": true,
    "python.analysis.inlayHints.parameterNames": "All",
    "python.analysis.inlayHints.parameterTypes": true,
    "python.analysis.diagnosticMode": "workspace",
    "python.analysis.autoFormatStrings": true,
    "python.analysis.stubPath": "${workspaceFolder}/.venv/Lib/site-packages",

    "[python]": {
        "editor.defaultFormatter": "charliermarsh.ruff",
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
            "source.fixAll.ruff": "explicit",
            "source.organizeImports.ruff": "explicit"
        }
    },
    "ruff.lint.enable": true,
    "ruff.organizeImports": true,
    "ruff.showNotifications": "onWarning",

    "editor.rulers": [88],
    "editor.renderWhitespace": "trailing",
    "editor.suggestSelection": "first",
    "editor.tabSize": 4,
    "editor.insertSpaces": true,
    "editor.trimAutoWhitespace": true,
    "files.trimTrailingWhitespace": true,
    "files.insertFinalNewline": true,
    "files.trimFinalNewlines": true,
    "files.encoding": "utf8",
    "files.eol": "\n",

    "terminal.integrated.defaultProfile.windows": "PowerShell",
    "terminal.integrated.shellIntegration.enabled": true,
    "terminal.integrated.scrollback": 10000,

    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        "**/.pytest_cache": true,
        "**/.ruff_cache": true,
        "**/.mypy_cache": true,
        "**/.uv": true
    },

    "editor.minimap.enabled": false,
    "breadcrumbs.enabled": true,
    "workbench.editor.enablePreview": false
}
```

**Spiegazione delle opzioni piu' importanti:**

| Opzione | Effetto |
|---------|---------|
| `python.analysis.typeCheckingMode: "basic"` | Abilita il controllo dei tipi di Pylance a livello base. Usa `"strict"` per massimo rigore (solo se hai tutti i type hint). |
| `python.analysis.diagnosticMode: "workspace"` | Pylance analizza tutti i file del progetto, non solo quello aperto. Necessario per rilevare errori tra file diversi. |
| `editor.rulers: [88]` | Mostra una linea verticale a colonna 88 (limite Ruff/Black). |
| `files.eol: "\n"` | Forza i fine riga Unix (LF) nei file salvati. Evita problemi in Git con Windows. |
| `editor.insertSpaces: true` + `editor.tabSize: 4` | Usa spazi (non tab) e 4 spazi per indentazione — convenzione Python. |

#### launch.json: configurare il debugger

Il file `.vscode/launch.json` configura le sessioni di debug. Crea la cartella `.vscode` nel progetto e il file `launch.json`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: File corrente",
            "type": "debugpy",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal",
            "justMyCode": true,
            "cwd": "${workspaceFolder}"
        },
        {
            "name": "Python: main.py",
            "type": "debugpy",
            "request": "launch",
            "program": "${workspaceFolder}/main.py",
            "console": "integratedTerminal",
            "justMyCode": true,
            "cwd": "${workspaceFolder}"
        },
        {
            "name": "Python: pytest",
            "type": "debugpy",
            "request": "launch",
            "module": "pytest",
            "args": ["-v", "${workspaceFolder}/tests/"],
            "console": "integratedTerminal",
            "justMyCode": false,
            "cwd": "${workspaceFolder}"
        },
        {
            "name": "FastAPI: uvicorn (reload)",
            "type": "debugpy",
            "request": "launch",
            "module": "uvicorn",
            "args": [
                "app.main:app",
                "--reload",
                "--port", "8000",
                "--log-level", "debug"
            ],
            "console": "integratedTerminal",
            "justMyCode": false,
            "cwd": "${workspaceFolder}"
        }
    ]
}
```

**Come usare il debugger:**
1. Apri il file che vuoi debuggare.
2. Clicca sul numero di riga dove vuoi fermarti — appare un punto rosso (breakpoint).
3. Premi `F5` per avviare il debugger con la configurazione selezionata.
4. L'esecuzione si ferma al breakpoint. Puoi esaminare i valori delle variabili nel pannello a sinistra.
5. Usa `F10` (passo singolo) o `F5` (continua) per navigare.

#### tasks.json: automatizzare operazioni comuni

Il file `.vscode/tasks.json` permette di eseguire comandi comuni con una scorciatoia:

```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "uv: sync",
            "type": "shell",
            "command": "uv sync",
            "problemMatcher": [],
            "group": "build"
        },
        {
            "label": "ruff: check",
            "type": "shell",
            "command": "uv run ruff check .",
            "problemMatcher": [],
            "group": "test"
        },
        {
            "label": "pytest: all",
            "type": "shell",
            "command": "uv run pytest -v",
            "problemMatcher": [],
            "group": {
                "kind": "test",
                "isDefault": true
            }
        },
        {
            "label": "mypy: check",
            "type": "shell",
            "command": "uv run mypy .",
            "problemMatcher": [],
            "group": "test"
        }
    ]
}
```

Esegui un task con `Ctrl+Shift+P` → "Tasks: Run Task" → scegli il task.

---

### D4 — PowerShell Profile Professionale

#### Cos'e' il profilo PowerShell

Il profilo PowerShell e' uno script `.ps1` che viene eseguito automaticamente ogni volta che apri una nuova sessione PowerShell. E' equivalente al `.bashrc` o `.zshrc` su Linux/macOS.

**Trovare e creare il profilo:**
```powershell
# Mostra il percorso
$PROFILE
# Output tipico: C:\Users\TuoNome\Documents\PowerShell\Microsoft.PowerShell_profile.ps1

# Verifica se esiste
Test-Path $PROFILE

# Crea se non esiste
if (-not (Test-Path $PROFILE)) {
    New-Item -ItemType File -Path $PROFILE -Force
}

# Apri in VS Code
code $PROFILE
```

#### Profilo professionale completo per sviluppo Python

```powershell
# ====================================================================
# PowerShell Profile — Sviluppo Python Professionale
# ====================================================================

# --- Encoding UTF-8 (fondamentale per Python su Windows) ---
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# --- Prompt con informazioni sul venv attivo ---
function prompt {
    $venv = ""
    if ($env:VIRTUAL_ENV) {
        $venvName = Split-Path $env:VIRTUAL_ENV -Leaf
        $venv = "($venvName) "
    }
    "$venv PS $($PWD.Path.Replace($HOME, '~'))> "
}

# --- Funzione: attiva il venv nella directory corrente ---
function Activate-Venv {
    $venvPaths = @(
        ".venv\Scripts\Activate.ps1",
        "venv\Scripts\Activate.ps1",
        ".env\Scripts\Activate.ps1"
    )
    foreach ($path in $venvPaths) {
        if (Test-Path $path) {
            . $path
            Write-Host "Ambiente virtuale attivato: $env:VIRTUAL_ENV" -ForegroundColor Green
            return
        }
    }
    Write-Warning "Nessun virtual environment trovato nella directory corrente."
}
Set-Alias -Name activate -Value Activate-Venv

# --- Funzione: crea un nuovo progetto Python con uv ---
function New-PythonProject {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Name,
        [string]$Python = "3.12"
    )
    uv init $Name --python $Python
    Set-Location $Name
    uv venv
    Write-Host "Progetto '$Name' creato con Python $Python." -ForegroundColor Green
    Write-Host "Attiva il venv con: activate" -ForegroundColor Cyan
}
Set-Alias -Name newpy -Value New-PythonProject

# --- Funzione: verifica lo stato dell'ambiente Python ---
function Check-PythonEnv {
    Write-Host "`n=== Ambiente Python ===" -ForegroundColor Cyan

    $uvVersion = uv --version 2>$null
    Write-Host "uv:          $uvVersion"

    $pythonVersions = uv python list --only-installed 2>$null
    Write-Host "Python installati:"
    $pythonVersions | ForEach-Object { Write-Host "  $_" }

    if ($env:VIRTUAL_ENV) {
        Write-Host "Venv attivo: $env:VIRTUAL_ENV" -ForegroundColor Green
    } else {
        Write-Host "Venv attivo: nessuno" -ForegroundColor Yellow
    }

    $gitVersion = git --version 2>$null
    Write-Host "Git:         $gitVersion"

    $codeVersion = code --version 2>$null | Select-Object -First 1
    Write-Host "VS Code:     $codeVersion"
}
Set-Alias -Name pycheck -Value Check-PythonEnv

# --- Funzione: aggiorna uv e gli strumenti globali ---
function Update-PythonTools {
    Write-Host "Aggiornamento uv..." -ForegroundColor Cyan
    uv self update
    Write-Host "Aggiornamento strumenti globali..." -ForegroundColor Cyan
    uv tool upgrade --all
    Write-Host "Completato." -ForegroundColor Green
}
Set-Alias -Name pyupdate -Value Update-PythonTools

# --- Alias generali ---
Set-Alias -Name py -Value python -ErrorAction SilentlyContinue

# --- Messaggio di avvio (opzionale) ---
Write-Host "Python dev profile caricato. Comandi: activate, newpy, pycheck, pyupdate" -ForegroundColor DarkGray
```

**Come applicare il profilo:**

Dopo aver modificato e salvato il file `$PROFILE`, puoi:
- Chiudere e riaprire PowerShell (il profilo viene caricato automaticamente).
- Oppure eseguire nella sessione corrente: `. $PROFILE` (il punto all'inizio e' importante).

**Verifica che funzioni:**
```powershell
pycheck   # deve mostrare le informazioni sull'ambiente
newpy mio-nuovo-progetto   # deve creare un progetto Python
```

---

### D5 — WSL2 come Alternativa

#### Cos'e' WSL2 e quando conviene

**WSL2** (Windows Subsystem for Linux versione 2) e' un ambiente Linux completo che gira all'interno di Windows tramite un kernel Linux reale. Non e' una macchina virtuale tradizionale: e' piu' integrato e leggero.

Perche' alcuni sviluppatori Python preferiscono WSL2 a Windows nativo:

1. **Parita' con la produzione:** la maggior parte dei server dove gira il codice in produzione sono Linux. Con WSL2, il comportamento e' identico.
2. **Strumenti nativi Linux:** `make`, `gcc`, librerie di sistema Unix che su Windows richiedono configurazione complessa.
3. **Docker:** Docker Desktop su Windows usa WSL2 internamente. Lavorare direttamente in WSL2 elimina un livello di indirezione.
4. **Performance I/O:** le operazioni sui file nel filesystem WSL2 sono piu' veloci di quelle sul filesystem Windows montato.

Quando WSL2 **non** e' necessario (e questo tutorial e' sufficiente):
- Apprendimento di Python base e intermedio.
- Sviluppo web con FastAPI/Flask/Django.
- Data science con pandas, NumPy, scikit-learn.
- Scripting e automazione.

#### Installazione di WSL2

```powershell
# Da PowerShell con privilegi amministratore:
wsl --install

# Riavvia il computer quando richiesto.
# Al riavvio, Ubuntu viene installato automaticamente.

# Verifica la versione WSL:
wsl --version
```

Output atteso dopo il riavvio:
```
WSL version: 2.x.x
Kernel version: 5.x.x
```

**Installare la distribuzione Ubuntu (se non e' stata installata automaticamente):**
```powershell
wsl --install -d Ubuntu-24.04
```

**Avviare WSL2:**
```powershell
wsl   # apre la shell Ubuntu
# oppure
ubuntu   # se hai Ubuntu installato
```

#### Python in WSL2

All'interno di WSL2 si usa la sintassi Linux. Il flusso con uv e' identico a Windows, ma i comandi di sistema sono diversi:

```bash
# All'interno della shell WSL2 (bash/zsh — NON PowerShell)

# Installare uv (versione Linux, non Windows)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Ricaricare la shell
source ~/.bashrc   # o source ~/.zshrc

# Installare Python
uv python install 3.12

# Creare un progetto
uv init mio-progetto
cd mio-progetto
uv venv

# Attivare il venv (sintassi Linux, diversa da Windows)
source .venv/bin/activate   # NON .\.venv\Scripts\Activate.ps1

# Eseguire
python main.py
```

#### Integrazione VS Code con WSL2

VS Code supporta WSL2 nativamente tramite l'estensione Remote WSL:

```powershell
# Installa l'estensione Remote WSL (dalla PowerShell di Windows)
code --install-extension ms-vscode-remote.remote-wsl
```

**Aprire un progetto WSL2 in VS Code da Windows:**
```bash
# Da dentro WSL2:
cd /home/tuonome/mio-progetto
code .   # apre VS Code su Windows, connesso a WSL2
```

VS Code mostra in basso a sinistra `[WSL: Ubuntu]` per indicare che sta lavorando nel filesystem WSL2.

#### Accesso incrociato tra Windows e WSL2

```powershell
# Da PowerShell Windows: esegui un comando in WSL2
wsl python3 --version
wsl ls -la /home/tuonome

# Da PowerShell Windows: accedi ai file WSL2
dir "\\wsl.localhost\Ubuntu\home\tuonome"
```

```bash
# Da WSL2: accedi ai file Windows
ls /mnt/c/Users/TuoNome/progetti
```

> **Importante:** Non lavorare su file Windows (`/mnt/c/`) da WSL2. Le performance sono molto peggiori rispetto a lavorare nel filesystem WSL2 nativo. Tieni i progetti in `/home/tuonome/` dentro WSL2, o in `C:\Users\TuoNome\` dentro Windows — ma non usarli dall'altro ambiente.

#### Riepilogo: Windows nativo vs WSL2

| Scenario | Windows nativo (questo tutorial) | WSL2 |
|----------|----------------------------------|------|
| Apprendimento Python | Ottimo | Ottimo |
| Sviluppo web FastAPI/Django | Ottimo | Ottimo |
| Data science | Ottimo | Ottimo |
| DevOps (Ansible, Terraform) | Possibile ma piu' complesso | Raccomandato |
| Docker-first development | Funziona | Piu' naturale |
| Contribuire a progetti open source Linux | Va bene | Preferibile |
| Librerie con dipendenze native problematiche | A volte complesso | Semplificato |

La scelta non e' permanente: puoi usare Windows nativo adesso e passare a WSL2 piu' avanti se ne senti la necessita'.

---

*Fine Parte D. Prosegui con la Parte E per il riepilogo, la checklist finale e i prossimi passi.*

---

## Parte E: Riepilogo, Checklist e Prossimi Passi

### Checklist Verifica Setup Completo

Esegui questa checklist alla fine del tutorial. Ogni voce deve risultare verificata prima di considerare il setup completato. I comandi sono nell'ordine consigliato di verifica.

**Apri PowerShell ed esegui ogni comando. Confronta l'output con quello atteso.**

---

#### Sezione 1: Strumenti di base installati

- [ ] **uv installato:**
```powershell
uv --version
# Atteso: uv 0.7.x o superiore
```

- [ ] **Python installato tramite uv:**
```powershell
uv python list --only-installed
# Atteso: almeno una riga con cpython-3.12.x
```

- [ ] **Python raggiungibile direttamente:**
```powershell
uv run python --version
# Atteso: Python 3.12.x
```

- [ ] **pip funzionante nel contesto uv:**
```powershell
uv run python -m pip --version
# Atteso: pip 24.x from ... (python 3.12)
```

- [ ] **Git installato:**
```powershell
git --version
# Atteso: git version 2.39.x o superiore (qualsiasi versione 2.39+)
```

- [ ] **VS Code installato e nel PATH:**
```powershell
code --version
# Atteso: versione 1.90.x o superiore, poi commit hash, poi "x64"
```

---

#### Sezione 2: Configurazione PowerShell

- [ ] **Execution Policy configurata correttamente:**
```powershell
Get-ExecutionPolicy -Scope CurrentUser
# Atteso: RemoteSigned
```

- [ ] **Il profilo PowerShell esiste (facoltativo ma consigliato):**
```powershell
Test-Path $PROFILE
# Atteso: True
```

- [ ] **Encoding UTF-8 attivo (verifica nel profilo o nella sessione):**
```powershell
[Console]::OutputEncoding.EncodingName
# Atteso: Unicode (UTF-8) o simile
```

---

#### Sezione 3: Configurazione PATH

- [ ] **uv trovato nel PATH:**
```powershell
where.exe uv
# Atteso: C:\Users\TuoNome\.local\bin\uv.exe
```

- [ ] **Nessun conflitto con stub Windows Store:**
```powershell
where.exe python
# Se mostra C:\Users\...\AppData\Local\Microsoft\WindowsApps\python.exe
# significa che lo stub e' ancora attivo. Vedi sezione A3.
```

---

#### Sezione 4: Virtual Environment

- [ ] **Crea e attiva un venv di test:**
```powershell
cd $HOME
uv init test-checklist-venv
cd test-checklist-venv
uv venv
.\.venv\Scripts\Activate.ps1
# Atteso: il prompt cambia in (.venv) PS C:\...\test-checklist-venv>
```

- [ ] **Python nel venv usa la versione corretta:**
```powershell
python --version
# Atteso: Python 3.12.x (DENTRO il venv attivo)
```

- [ ] **Installa una dipendenza di test:**
```powershell
uv add requests
# Atteso: Installed requests==2.32.x e le sue dipendenze
```

- [ ] **La dipendenza e' importabile:**
```powershell
python -c "import requests; print(requests.__version__)"
# Atteso: 2.32.x o simile (un numero di versione)
```

- [ ] **Disattiva e pulisci:**
```powershell
deactivate
cd $HOME
Remove-Item -Recurse -Force test-checklist-venv
# Atteso: nessun errore
```

---

#### Sezione 5: Git configurato

- [ ] **Nome utente configurato:**
```powershell
git config --global user.name
# Atteso: il tuo nome (non deve essere vuoto)
```

- [ ] **Email configurata:**
```powershell
git config --global user.email
# Atteso: la tua email (non deve essere vuota)
```

- [ ] **Branch predefinito impostato a main:**
```powershell
git config --global init.defaultBranch
# Atteso: main
```

- [ ] **Core editor impostato:**
```powershell
git config --global core.editor
# Atteso: code --wait
```

- [ ] **Git crea un repository funzionante:**
```powershell
cd $HOME
mkdir test-git-repo
cd test-git-repo
git init
git status
# Atteso: "On branch main, No commits yet, nothing to commit"
cd $HOME
Remove-Item -Recurse -Force test-git-repo
```

---

#### Sezione 6: VS Code con estensioni Python

- [ ] **Estensione Python installata:**
```powershell
code --list-extensions | Select-String "ms-python.python"
# Atteso: ms-python.python
```

- [ ] **Pylance installato:**
```powershell
code --list-extensions | Select-String "pylance"
# Atteso: ms-python.vscode-pylance
```

- [ ] **Ruff installato:**
```powershell
code --list-extensions | Select-String "ruff"
# Atteso: charliermarsh.ruff
```

- [ ] **VS Code apre una cartella Python senza errori:**

Crea un file di test, aprilo in VS Code e verifica che non ci siano errori:
```powershell
cd $HOME
mkdir test-vscode-py
cd test-vscode-py
uv init . --name test-vscode
uv venv
"print('VS Code funziona!')" | Out-File -Encoding utf8 main.py
code .
# In VS Code: apri main.py, verifica che Python sia selezionato,
# poi esegui con Ctrl+F5. Atteso: "VS Code funziona!" nel terminale.
```

---

#### Sezione 7: Progetto end-to-end completo

Questo e' il test finale che verifica che tutto il flusso funzioni insieme:

- [ ] **Crea il progetto hello-world finale:**
```powershell
cd "$HOME\progetti"
uv init hello-world-finale --python 3.12
cd hello-world-finale
```

- [ ] **Crea il virtual environment:**
```powershell
uv venv
.\.venv\Scripts\Activate.ps1
# Atteso: prompt con (.venv)
```

- [ ] **Scrivi un programma con input e output:**
```powershell
@"
def somma(a: float, b: float) -> float:
    return a + b

if __name__ == '__main__':
    a = float(input('Primo numero: '))
    b = float(input('Secondo numero: '))
    risultato = somma(a, b)
    print(f'Risultato: {a} + {b} = {risultato}')
    assert risultato == a + b, 'Test fallito!'
    print('Test superato.')
"@ | Out-File -Encoding utf8 main.py
```

- [ ] **Esegui e verifica:**
```powershell
uv run python main.py
# Inserisci: 10 e 5
# Atteso:
# Primo numero: 10
# Secondo numero: 5
# Risultato: 10.0 + 5.0 = 15.0
# Test superato.
```

- [ ] **Inizializza Git e crea il primo commit:**
```powershell
git init
git add .
git commit -m "feat: hello-world finale con somma"
# Atteso: [main (root-commit) hash] feat: hello-world finale con somma
```

- [ ] **Apri in VS Code e verifica:**
```powershell
code .
# Atteso: VS Code apre il progetto, Pylance analizza main.py senza errori rossi
```

**Se tutti i punti sono verificati: il setup e' completo e professionale.**

---

### Glossario dei Termini del Tutorial

Questo glossario definisce tutti i termini tecnici usati nel tutorial. I termini sono in ordine alfabetico.

---

**Ambiente virtuale (virtual environment):** Un ambiente Python isolato per un singolo progetto. Contiene la propria copia di Python e le proprie librerie installate, separate da tutti gli altri progetti. Creato da `uv venv` o `python -m venv`. Vedi: Parte B2.

**Bytecode:** Forma intermedia del codice Python, generata dal compilatore CPython e salvata in file `.pyc` nella cartella `__pycache__`. Non e' codice macchina nativo, ma e' piu' efficiente da eseguire rispetto al codice sorgente testuale. Vedi: Parte B4.

**Cartella (directory):** Un contenitore nel filesystem che puo' contenere file e altre cartelle. In PowerShell, la cartella corrente si vede con `pwd`, i contenuti con `ls`, ci si sposta con `cd`. Analogo al "cassetto" in un archivio fisico.

**Commit:** Uno "snapshot" (istantanea) del tuo progetto salvato in Git. Ogni commit ha un messaggio che descrive cosa e' cambiato. I commit formano la storia del progetto a cui puoi tornare in qualsiasi momento. Vedi: Parte B3.

**CPython:** L'implementazione standard e piu' comune di Python, scritta in linguaggio C. E' quella che installi da python.org o con `uv python install`. Quasi tutto quello che leggi su Python si riferisce a CPython. Vedi: Parte D2.

**Dipendenza:** Una libreria Python esterna che il tuo progetto richiede per funzionare. Ad esempio, un progetto che usa `requests` per fare chiamate HTTP ha `requests` come dipendenza. Le dipendenze sono gestite da uv e dichiarate in `pyproject.toml`. Vedi: Parte B2.

**Editor di codice (IDE):** Un programma specializzato per scrivere codice. VS Code e' l'editor usato in questo tutorial. Offre colorazione della sintassi, completamento automatico, rilevamento errori in tempo reale e debug integrato. Vedi: Parte A5.

**Encoding (codifica dei caratteri):** Il sistema che determina come i caratteri (lettere, simboli) vengono rappresentati come byte nel computer. UTF-8 e' lo standard moderno che supporta tutti i caratteri internazionali. Su Windows, problemi di encoding causano la visualizzazione di caratteri strani. Vedi: Parte B5, Errore 9.

**Estensione (VS Code):** Un plugin che aggiunge funzionalita' a VS Code. Le estensioni fondamentali per Python sono: `ms-python.python`, `ms-python.vscode-pylance`, `charliermarsh.ruff`. Vedi: Parte A5.

**Execution Policy:** Un meccanismo di sicurezza di PowerShell che controlla quali script `.ps1` possono essere eseguiti. Il valore `RemoteSigned` permette script locali e blocca quelli non firmati scaricati da internet. Vedi: Parte A3, B5.

**File .gitignore:** Un file che dice a Git quali file e cartelle ignorare (non includere nel version control). File comuni da ignorare in Python: `.venv/`, `__pycache__/`, `.env`. Vedi: Parte B3.

**Git:** Il sistema di version control piu' usato al mondo. Tiene traccia di ogni modifica al codice, permette di tornare a versioni precedenti e di collaborare con altri sviluppatori. Vedi: Parte B3.

**GIL (Global Interpreter Lock):** Un meccanismo interno di CPython che impedisce l'esecuzione simultanea di piu' thread Python sulla stessa CPU. Questo limita il parallelismo nel codice Python puro. Python 3.13 introduce il GIL opzionale sperimentale. Vedi: Parte D2.

**Indentazione:** Gli spazi all'inizio di una riga di codice Python. A differenza di altri linguaggi che usano `{}` per delimitare i blocchi, Python usa l'indentazione. La convenzione e' 4 spazi per livello. Un'indentazione errata causa `IndentationError`. Vedi: Parte B5, Errore 8.

**Interprete:** Il programma che legge ed esegue il tuo codice Python. Quando dici "Python", di solito intendi l'interprete CPython. VS Code deve sapere quale interprete usare per ogni progetto. Vedi: Parte B4.

**JIT (Just-In-Time compilation):** Tecnica usata da PyPy: il codice Python viene compilato in codice macchina nativo durante l'esecuzione, rendendo i loop ripetuti molto piu' veloci. Vedi: Parte D2.

**Linguaggio di programmazione:** Un sistema formale di istruzioni per comunicare con il computer. Python e' un linguaggio di programmazione ad alto livello, leggibile, general-purpose. Vedi: Parte A1.

**Lock file (uv.lock):** Un file generato automaticamente da uv che registra le versioni esatte di tutte le dipendenze del progetto (dirette e transitive). Garantisce che tutti ottengano esattamente le stesse versioni quando eseguono `uv sync`. Vedi: Parte B2.

**Modulo:** Un file Python (`.py`) che contiene definizioni di funzioni, classi e variabili. Un modulo puo' essere importato da altri file con `import`. Esempi di moduli della libreria standard: `os`, `sys`, `json`, `datetime`. Vedi: Parte A4.

**PATH:** Una variabile d'ambiente del sistema operativo che elenca le directory in cui Windows cerca gli eseguibili quando digiti un comando. Se Python non e' nel PATH, Windows non sa dove trovarlo e restituisce "command not recognized". Vedi: Parte B1.

**Prompt (dei comandi):** Il testo che appare nel terminale prima del cursore, indicando che il sistema e' pronto per ricevere un comando. In PowerShell: `PS C:\Users\nome>`. In Python REPL: `>>>`. Vedi: Parte A2.

**pyproject.toml:** Il file di configurazione standard per i progetti Python moderni (definito da PEP 518, 517, 621). Contiene il nome del progetto, la versione, le dipendenze, e la configurazione degli strumenti (ruff, mypy, pytest). E' il sostituto moderno di `setup.py`, `setup.cfg`, `requirements.txt`. Vedi: Parte B2.

**PyPy:** Un'implementazione alternativa di Python che usa la compilazione JIT per essere 5-10x piu' veloce di CPython per codice Python puro. Non compatibile con tutte le librerie C native. Vedi: Parte D2.

**Python:** Linguaggio di programmazione ad alto livello, interpretato, general-purpose. Creato da Guido van Rossum nel 1991. Filosofia: leggibilita' e produttivita' del programmatore prima di tutto. Vedi: Parte A1, Prima di Iniziare.

**Pylance:** Un language server avanzato per Python sviluppato da Microsoft, basato su Pyright. Offre analisi dei tipi, completamento automatico intelligente, import automatici, navigazione tra simboli. Estensione VS Code: `ms-python.vscode-pylance`. Vedi: Parte A5.

**REPL (Read-Eval-Print Loop):** L'ambiente interattivo di Python. Puoi digitare espressioni Python e vedere immediatamente il risultato. Si avvia con `python` o `uv run python`. Uscire con `exit()` o `Ctrl+Z + Invio`. Vedi: Parte A4.

**Repository (Git):** Una cartella tracciata da Git, con tutta la storia dei commit. Si crea con `git init` o si clona con `git clone`. Vedi: Parte B3.

**Ruff:** Un linter e formatter per Python scritto in Rust, molto veloce. Sostituisce `flake8`, `isort` e `black` con un unico strumento. Formato automatico al salvataggio con l'estensione VS Code. Estensione: `charliermarsh.ruff`. Vedi: Parte A5.

**Script:** Un file Python (`.py`) che contiene un programma da eseguire. Si esegue con `python nome_file.py` o `uv run python nome_file.py`. Vedi: Parte A4, A5.

**Terminale (PowerShell):** Un'interfaccia testuale per interagire con il sistema operativo tramite comandi scritti. PowerShell e' il terminale moderno di Microsoft, preinstallato su Windows 10 e 11. Vedi: Parte A2.

**Type hint (annotazione di tipo):** Una notazione facoltativa in Python per indicare il tipo di una variabile o il tipo di ritorno di una funzione. Esempio: `def saluta(nome: str) -> str:`. Non obbligatori, ma aiutano Pylance a trovare errori di tipo. Vedi: Parte C2.

**uv:** Un gestore di progetti e ambienti Python moderno scritto in Rust, sviluppato da Astral. Sostituisce pip, virtualenv, pyenv e poetry con un unico strumento velocissimo. Metodo raccomandato per questo corso. Vedi: Parte A3, B2, D1.

**Variabile:** Un nome che si riferisce a un valore in memoria. In Python: `nome = "Marco"`. Il valore puo' cambiare durante l'esecuzione. Vedi: Parte A1.

**Version control:** Un sistema che traccia le modifiche ai file nel tempo. Git e' il sistema di version control piu' usato. Permette di tornare a versioni precedenti, collaborare con altri, e capire chi ha modificato cosa e quando. Vedi: Parte B3.

**Virtual environment:** Vedi: Ambiente virtuale.

**WSL2 (Windows Subsystem for Linux 2):** Un ambiente Linux completo che gira all'interno di Windows. Permette di usare comandi Linux, strumenti DevOps, e garantisce la parita' con ambienti di produzione Linux. Non necessario per questo corso base. Vedi: Parte D5.

---

### Problemi Risolti durante il Tutorial

Questa sezione raccoglie tutti gli errori e le soluzioni descritte nel tutorial, in formato di ricerca rapida.

| Errore | Sezione | Soluzione rapida |
|--------|---------|------------------|
| `python : The term 'python' is not recognized` | A3, B5 | Chiudi e riapri PowerShell. Se persiste, verifica PATH. |
| `uv : The term 'uv' is not recognized` | A3, B5 | `$env:PATH = "$env:USERPROFILE\.local\bin;$env:PATH"`, poi riapri terminale. |
| `Activate.ps1 cannot be loaded because running scripts is disabled` | A3, B5 | `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| VS Code non trova Python / Pylance mostra errori su tutti gli import | A5, B5 | `Ctrl+Shift+P` → "Python: Select Interpreter" → seleziona `.venv\Scripts\python.exe` |
| `SyntaxError: '(' was never closed` | B5 | Cerca la parentesi non chiusa alla riga segnalata o in quella precedente |
| `ModuleNotFoundError: No module named 'X'` | B5 | `uv add X` poi riesegui |
| `IndentationError: expected an indented block` | B5 | Usa 4 spazi dopo `if:`, `for:`, `def:`, ecc. Non mescolare spazi e tab |
| Caratteri accentati mostrati come `?` | B5 | `[Console]::OutputEncoding = [System.Text.Encoding]::UTF8` |
| `FileNotFoundError: No such file or directory` | B5 | `cd` nella cartella corretta prima di eseguire, o usa `Path(__file__).parent` |
| `ValueError: invalid literal for int() with base 10: 'X'` | C3 | L'utente ha inserito testo dove si aspettava un numero. Usa `try/except ValueError`. |
| `code --version` non trovato dopo installazione | A5 | Riapri terminale. Se persiste, aggiungi VS Code al PATH manualmente. |
| `git --version` non trovato dopo installazione | B3 | Riapri terminale. Reinstalla con `winget install Git.Git`. |
| python punta alla versione sbagliata (ex. 2.7 invece di 3.12) | B1 | Controlla `where.exe python`. Metti la directory corretta prima nel PATH. |
| pip installa nel Python di sistema, non nel venv | B5 | Verifica `$env:VIRTUAL_ENV`. Attiva il venv o usa `uv add`. |
| Il venv si attiva ma `python --version` mostra versione sbagliata | B2 | Il file `.python-version` del progetto specifica la versione. Controlla il suo contenuto. |
| uv.lock ha conflitti tra dipendenze | D1 | `uv lock --upgrade` per aggiornare il lock file |

---

### Prossimo Passo

Hai completato il tutorial `tutorial_00_ambiente_setup.md`. L'ambiente e' configurato, Python funziona, VS Code e' pronto, Git e' configurato.

Ora sei pronto per i prossimi tutorial:

**Tutorial successivo (prossimo da leggere):**

```
tutorial_00_git_per_pythonisti.md
```

Impara Git in modo specifico per il flusso di lavoro Python: branch, merge, pull request, come integrare Git con uv e VS Code.

---

**Dopo Git:**

```
tutorial_01_fondamenti_linguaggio.md
```

Inizia a imparare Python vero e proprio: variabili e tipi, operatori, strutture di controllo (`if`, `for`, `while`), funzioni, e la libreria standard di base.

---

**Riferimento permanente per questo modulo:**

Il documento di riferimento `00-ambiente-setup-windows.md` e' la versione concisa di questo tutorial — contiene tutti i comandi senza le spiegazioni dettagliate. Usalo come "cheat sheet" una volta che hai interiorizzato i concetti.

---

**Checklist finale prima di procedere:**

Prima di aprire `tutorial_01_fondamenti_linguaggio.md`, verifica di avere:

- [ ] uv funzionante (`uv --version` risponde)
- [ ] Python 3.12 installato (`uv run python --version` mostra 3.12.x)
- [ ] VS Code aperto e configurato con Pylance e Ruff
- [ ] Git configurato con nome ed email (`git config --global --list`)
- [ ] Almeno un progetto uv creato e funzionante
- [ ] L'Execution Policy impostata a `RemoteSigned`
- [ ] Hai letto (o scorso) la Parte B per capire il perche' di ogni strumento

Buon apprendimento.

---

*Tutorial parte del corso "Programmazione Python Professionale" — Modulo 00*
*Companion a: `00-ambiente-setup-windows.md`*
*Versione: 2026-07-15 · Piattaforma: Windows 10/11 · Python: 3.12+*
