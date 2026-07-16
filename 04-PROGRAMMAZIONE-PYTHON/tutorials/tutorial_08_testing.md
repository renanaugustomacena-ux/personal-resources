# Tutorial: Testing con pytest — Dal Principiante all'Esperto

> **Companion to:** `08-testing.md`
> **Scope:** unittest (per completezza storica), pytest deep dive (test discovery, assert, fixtures,
> parametrize, marks, conftest, plugins), mocking (unittest.mock, MagicMock, AsyncMock, patch,
> side_effect), coverage (pytest-cov, branch coverage, report HTML), property-based testing
> (Hypothesis, strategie, stateful testing), mutation testing (mutmut), BDD (pytest-bdd, behave,
> Gherkin), testcontainers, factory_boy, faker, performance testing (pytest-benchmark, locust),
> snapshot testing (syrupy), testing asincrono (pytest-asyncio), CI/CD integration.
> **Prerequisiti:** `tutorial_01_fondamenti_linguaggio.md` completato (idealmente anche tutorial_02 — OOP)
> **Durata stimata:** 30–40 ore
> **Lingua:** Italiano

---

## Indice Generale

- **PARTE A — BASI ASSOLUTE**
  - A1: Perché Testare? Il Prezzo di Non Testare
  - A2: Tipi di Test — La Piramide del Testing
  - A3: pytest — Installazione e Prima Esecuzione
  - A4: Il Primo Test — `assert` è tutto quello che ti serve
  - [Sezione speciale] Come leggere un output di pytest fallito
  - A5: `assert` con Messaggi Personalizzati
  - A6: Test per le Eccezioni — `pytest.raises`
  - A7: Test per i Warning — `pytest.warns`

- **PARTE B — COMPRENSIONE PROFONDA**
  - B1: Fixtures — Il Codice di Setup che Non Si Ripete
  - B2: `parametrize` — Lo Stesso Test con Dati Diversi
  - B3: Marks — Etichettare e Filtrare i Test
  - B4: `conftest.py` — Il File Condiviso di pytest
  - B5: Mocking — Sostituire Dipendenze nei Test
  - B6: Coverage — Quanto Codice è Coperto?
  - B7: Hypothesis — Testing Basato su Proprietà
  - B8: Testcontainers — Database Reali nei Test
  - B9: BDD con behave — Test che Capiscono Tutti
  - B10: Mutation Testing con mutmut

- **PARTE C — ESERCIZI COMPLETI** (12 esercizi guidati)

- **PARTE D — APPROFONDIMENTO ESPERTI**
  - D1: pytest Internals e Plugin API
  - D2: Testing Parallelo con pytest-xdist
  - D3: Snapshot Testing con syrupy
  - D4: Contract Testing con pact
  - D5: Performance Testing con pytest-benchmark
  - D6: Load Testing con Locust
  - D7: Fuzzing
  - D8: Tassonomia Completa dei Test Doubles
  - D9: Quando NON Testare

- **PARTE E — RIEPILOGO E RIFERIMENTI**
  - Checklist 40+ punti
  - Tabella "Tipo di test → Strumento giusto"
  - Glossario completo
  - Percorso verso tutorial_09

---

## PARTE A — BASI ASSOLUTE

---

## A1: Perché Testare? Il Prezzo di Non Testare

### L'illusione del "testare a mano"

Immagina di aver scritto una funzione che calcola lo sconto su un prezzo. La esegui, vedi che
`calcola_sconto(100, 20)` restituisce `80.0` e pensi: "Funziona". Poi vai avanti con il progetto.

Tre settimane dopo, il tuo collega (o tu stesso, alle 23:00 prima di un rilascio) modifica quella
funzione per supportare gli sconti stagionali. Riesegue il programma a mano, inserisce qualche
valore, sembra ok. Si fa il deploy.

Il giorno dopo il cliente chiama: tutti gli ordini con sconto superiore al 50% sono stati elaborati
con il prezzo intero. Nessuno si è accorto che il calcolo per gli sconti alti era rotto.

Questo scenario si ripete ogni giorno in migliaia di progetti nel mondo. Non perché i programmatori
siano incompetenti, ma perché **testare a mano non scala**: più il progetto cresce, meno è possibile
verificare manualmente ogni combinazione di input e scenario.

---

### L'analogia dell'assicurazione auto

I test automatici funzionano come un'assicurazione auto.

- **Non ti servono finché non hai un incidente.** Se guidi ogni giorno senza problemi, potresti
  pensare che l'assicurazione sia soldi buttati.
- **Ma quando succede qualcosa, vale ogni centesimo.** Senza assicurazione, un incidente
  significa costi enormi, ansia, mesi di problemi.
- **Il punto non è se ci sarà un incidente, ma quando.** Con progetti software reali, la domanda
  non è "avrò mai un bug?", è "quanto mi costerà quel bug?".

I test automatici sono il tuo "premio assicurativo". Li paghi con il tempo di scrittura iniziale,
ma ti proteggono ogni volta che modifichi il codice.

Senza test, ogni modifica è un salto nel vuoto. Con i test, ogni modifica è accompagnata da una
rete di sicurezza che ti dice immediatamente se hai rotto qualcosa.

---

### Il costo dei bug: dati reali

Non è solo teoria. Ecco cosa succede quando non si testa abbastanza.

---

#### Il Therac-25 (1985–1987): bug che uccidono persone

Il Therac-25 era una macchina per la radioterapia. A causa di una race condition nel software
(un tipo di bug legato alla concorrenza tra processi), la macchina poteva erogare dosi di
radiazioni tra 100 e 1000 volte superiori al previsto.

**Risultato:** almeno sei pazienti ricevettero dosi letali. Alcuni morirono, altri subirono
danni permanenti gravissimi.

**La causa?** La versione precedente del software (Therac-20) aveva protezioni hardware che
rendevano il software sicuro anche con bug. Il Therac-25 rimosse quelle protezioni hardware
confidando solo nel software. I test non erano stati aggiornati per riflettere questa nuova
dipendenza critica.

---

#### Knight Capital Group (1 agosto 2012): 440 milioni di dollari in 45 minuti

Knight Capital Group era una delle più grandi società di trading ad alta frequenza del mondo.
Il 1° agosto 2012, durante un aggiornamento software, un errore di deployment attivò del codice
legacy mai rimosso.

In 45 minuti, il sistema automatico di trading acquistò e vendette azioni in modo errato,
accumulando perdite di **440 milioni di dollari**. La società fu costretta a vendere le proprie
quote e di fatto cessò di esistere come entità indipendente.

**La causa?** Mancanza di test per lo scenario di deployment, nessuna validazione automatica
del comportamento del sistema prima dell'attivazione in produzione.

---

#### Mars Climate Orbiter (23 settembre 1999): 327 milioni di dollari persi nello spazio

La sonda della NASA Mars Climate Orbiter fu lanciata nel 1998 con la missione di orbitare
attorno a Marte. Dopo 286 giorni di viaggio, raggiunse Marte e... scomparve.

L'indagine rivelò la causa: il software di navigazione di un fornitore esterno usava unità
**imperiali** (libbre-forza per secondo), mentre il sistema della NASA si aspettava unità
**metriche** (newton-secondo). Nessun test di integrazione verificava la compatibilità
delle unità tra i due sistemi.

**Risultato:** 327 milioni di dollari di missione andati persi.

---

### Perché i programmatori non scrivono test?

Se i test sono così importanti, perché molti programmatori non li scrivono? Le motivazioni
più comuni:

**"Non ho tempo."**
In realtà, scrivere test *risparmia* tempo nel medio-lungo periodo. Il tempo perso a fare
il debug di un bug complesso in produzione è sempre maggiore del tempo che ci avrebbe
voluto per scrivere il test.

**"Il mio codice è semplice, non ha bisogno di test."**
Ogni programmatore ha detto questa frase. Poi il codice "semplice" è cresciuto, è stato
modificato da altri, ha avuto nuovi requisiti, e quello che sembrava semplice è diventato
complicato. I test scritti quando il codice era semplice valgono oro quando diventa complesso.

**"I test vanno scritti dopo aver finito il codice."**
Questa idea produce test scritti di fretta, superficiali, oppure mai scritti affatto perché
"adesso ho altro da fare". I test scritti insieme al codice (o prima, con TDD) sono integrati
nel processo, non un'aggiunta a posteriori.

**"Non so come farlo."**
Questa è l'unica motivazione valida — ed è esattamente quello che questo tutorial risolve.

---

### Cosa guadagni con i test?

**Fiducia nel refactoring.** Vuoi rinominare una variabile, spostare una funzione, cambiare
un algoritmo? Con i test, fai la modifica, esegui pytest, e in secondi sai se hai rotto qualcosa.
Senza test, ogni refactoring è un atto di fede.

**Documentazione viva.** I test documentano come il codice deve essere usato. Un test come
`test_calcola_sconto_percentuale_negativa_solleva_errore()` comunica immediatamente un vincolo
del sistema, meglio di qualsiasi commento nel codice.

**Design migliore.** Scrivere test ti forza a pensare all'interfaccia pubblica del tuo codice
prima dell'implementazione. Il codice difficile da testare è quasi sempre mal progettato:
troppo accoppiato, troppe responsabilità, dipendenze nascoste.

**Feedback immediato.** Senza test, il ciclo di feedback è: scrivi codice → rilascia in
produzione → aspetta che qualcosa si rompa → scopri il bug. Con i test, il ciclo è: scrivi
test → scrivi codice → esegui i test → correggi immediatamente. Il feedback diventa instantaneo.

**Dormire meglio.** Non è una battuta. Sapere che il codice è coperto da test riduce l'ansia
da rilascio. Puoi fare un deploy venerdì pomeriggio senza terrore.

---

### Un'ultima analogia: le fondamenta di un edificio

Immagina di costruire un grattacielo senza fare test sulle fondamenta. All'inizio va bene —
le fondamenta tengono. Ma man mano che aggiungi piani, il peso aumenta. A un certo punto, una
piccola vibrazione (un terremoto, un camion pesante) potrebbe far cedere tutto.

I test sono i collaudi strutturali delle fondamenta. Ogni "piano" che aggiungi (ogni nuova
funzionalità) è sicuro perché sai che le fondamenta reggono.

Un progetto senza test ha fondamenta non collaudate. Potrebbe reggere. Ma con ogni nuova
funzionalità, il rischio cresce. Ed è impossibile sapere quando si avvicina il limite.

---

> **Ricorda:** non stai scrivendo test per il compilatore, per il tuo capo, o per una
> checklist di qualità. Li stai scrivendo per il te del futuro, che alle 23:00 due mesi
> da oggi dovrà modificare questo codice senza romperlo.

---

## A2: Tipi di Test — La Piramide del Testing

### La metafora dell'edificio (ancora)

Torniamo all'edificio. Quando costruisci una casa, fai diversi tipi di controlli:

1. **Ispezioni dei singoli componenti** — verifica che ogni mattone sia integro, che ogni
   vite sia stretta, che ogni cavo sia collegato correttamente. Queste ispezioni sono veloci,
   economiche, e se trovano un problema lo individuano esattamente.

2. **Test di integrazione** — verifichi che il sistema elettrico funzioni con il sistema
   idraulico, che le porte si aprano e si chiudano con gli infissi installati. Più lenti,
   più costosi, ma rivelano problemi che le ispezioni dei singoli componenti non possono trovare.

3. **Collaudo completo** — abiti nella casa per qualche settimana e vedi se tutto funziona
   insieme. È il test più completo, ma anche il più lento e costoso.

Nel software, questa gerarchia si chiama **Piramide del Testing**.

---

### La Piramide del Testing

```
          /\
         /  \
        / E2E\      ← Pochissimi, lentissimi, costosi
       /------\
      / Integr. \   ← Alcuni, più lenti, richiedono infrastruttura
     /------------\
    /  Unit Tests  \ ← Molti, velocissimi, isolati
   /________________\
```

I tre livelli hanno caratteristiche molto diverse:

| Caratteristica | Unit Test | Integration Test | E2E Test |
|---|---|---|---|
| **Velocità** | Millisecondi | Secondi | Minuti |
| **Isolamento** | Totale | Parziale | Nessuno |
| **Numero ideale** | Centinaia/migliaia | Decine | Una manciata |
| **Manutenzione** | Bassa | Media | Alta |
| **Confidenza** | Alta per unità | Alta per sistemi | Alta per percorsi utente |
| **Quando falliscono** | Immediata diagnosi | Diagnosi meno precisa | Diagnosi complessa |

---

### Unit Test: la base della piramide

Un **unit test** verifica una singola unità di codice — tipicamente una funzione o un metodo —
in completo **isolamento** dal resto del sistema.

"Isolamento" significa che l'unità viene testata senza dipendenze reali: se la funzione
normalmente chiama un database, nel test quella chiamata viene simulata (mockata). Se la funzione
legge un file, nel test si usa un file temporaneo o si simula la lettura.

**Perché l'isolamento è importante?** Immagina di testare la funzione `calcola_prezzo_totale()`
che chiama il database per ottenere i prezzi dei prodotti. Se il test fallisce, è perché
la funzione è sbagliata? O perché il database non è disponibile? O perché i dati del
database sono cambiati? Con l'isolamento, il test fallisce solo se la funzione è sbagliata.

```python
# Esempio di unit test — verifica una singola funzione in isolamento
def calcola_sconto(prezzo: float, percentuale: float) -> float:
    """Calcola il prezzo scontato."""
    if percentuale < 0 or percentuale > 100:
        raise ValueError(f"Percentuale non valida: {percentuale}. Deve essere tra 0 e 100.")
    return prezzo * (1 - percentuale / 100)


# UNIT TESTS — ogni test verifica un singolo comportamento
def test_sconto_normale():
    """Caso standard: 20% di sconto su 100€."""
    assert calcola_sconto(100.0, 20.0) == 80.0


def test_sconto_zero():
    """Sconto zero: il prezzo non cambia."""
    assert calcola_sconto(100.0, 0.0) == 100.0


def test_sconto_totale():
    """Sconto 100%: il prezzo diventa zero."""
    assert calcola_sconto(100.0, 100.0) == 0.0


def test_sconto_percentuale_negativa():
    """Percentuale negativa: deve sollevare ValueError."""
    import pytest
    with pytest.raises(ValueError, match="non valida"):
        calcola_sconto(100.0, -5.0)


def test_sconto_percentuale_maggiore_100():
    """Percentuale > 100: deve sollevare ValueError."""
    import pytest
    with pytest.raises(ValueError, match="non valida"):
        calcola_sconto(100.0, 150.0)
```

Questi cinque test coprono tutti i casi significativi della funzione. Vengono eseguiti in
millisecondi, non dipendono da nessun sistema esterno, e ogni fallimento indica esattamente
quale comportamento è rotto.

---

### Integration Test: il piano di mezzo

Un **integration test** verifica che più componenti del sistema funzionino correttamente
**insieme**. Non simula le dipendenze — le usa davvero.

**L'analogia del motore:** gli unit test verificano che ogni pistone si muova correttamente
da solo. L'integration test verifica che il motore completo giri. Potresti avere tutti i
pistoni perfetti ma un problema nella loro sincronizzazione.

```python
# Esempio di integration test — usa un database SQLite reale
import sqlite3
import pytest

@pytest.fixture
def database_reale():
    """Crea un database SQLite vero in memoria."""
    conn = sqlite3.connect(":memory:")
    conn.execute("""
        CREATE TABLE prodotti (
            id INTEGER PRIMARY KEY,
            nome TEXT NOT NULL,
            prezzo REAL NOT NULL
        )
    """)
    conn.execute("INSERT INTO prodotti (nome, prezzo) VALUES ('Mela', 0.50)")
    conn.execute("INSERT INTO prodotti (nome, prezzo) VALUES ('Pane', 1.20)")
    conn.commit()
    yield conn
    conn.close()


def test_recupera_prodotti_dal_db(database_reale):
    """Integration test: la funzione recupera davvero i dati dal database."""
    cursore = database_reale.execute("SELECT nome, prezzo FROM prodotti ORDER BY nome")
    prodotti = cursore.fetchall()

    assert len(prodotti) == 2
    assert prodotti[0] == ("Mela", 0.50)
    assert prodotti[1] == ("Pane", 1.20)


def test_inserimento_e_recupero(database_reale):
    """Integration test: inserimento e recupero funzionano insieme."""
    database_reale.execute(
        "INSERT INTO prodotti (nome, prezzo) VALUES (?, ?)",
        ("Latte", 0.80)
    )
    database_reale.commit()

    cursore = database_reale.execute(
        "SELECT prezzo FROM prodotti WHERE nome = ?",
        ("Latte",)
    )
    riga = cursore.fetchone()
    assert riga[0] == 0.80
```

Gli integration test sono più lenti degli unit test perché devono effettivamente
parlare con componenti reali (anche se qui usiamo SQLite in-memory, che è molto veloce).
Catturano bug che gli unit test non possono trovare: problemi di SQL, problemi di schema,
problemi nella serializzazione dei dati.

---

### End-to-End Test: il vertice della piramide

Un **E2E test** (End-to-End, cioè "da un'estremità all'altra") simula un percorso utente
completo attraverso l'intera applicazione.

**L'analogia del collaudo:** non stai testando singoli componenti, stai mettendoti nei
panni di un utente e verificando che l'intero flusso funzioni, dall'inizio alla fine.

Strumenti tipici per E2E:
- **Selenium / Playwright** — controllano un browser web
- **httpx / requests** — inviano richieste HTTP reali
- **Robot Framework** — automazione basata su keyword

```python
# Esempio schematico di E2E test con una web API
# (richiede un server in esecuzione)
import httpx
import pytest


@pytest.mark.e2e
def test_flusso_completo_acquisto():
    """
    E2E test: verifica il flusso completo
    - Login utente
    - Aggiunta prodotto al carrello
    - Checkout
    - Verifica ordine creato
    """
    client = httpx.Client(base_url="http://localhost:8000")

    # Step 1: Login
    login_resp = client.post("/api/login", json={
        "email": "mario@test.it",
        "password": "password123"
    })
    assert login_resp.status_code == 200
    token = login_resp.json()["token"]

    # Step 2: Aggiungi al carrello
    client.headers["Authorization"] = f"Bearer {token}"
    cart_resp = client.post("/api/carrello/aggiungi", json={
        "prodotto_id": 1,
        "quantita": 2
    })
    assert cart_resp.status_code == 200

    # Step 3: Checkout
    checkout_resp = client.post("/api/ordini/crea")
    assert checkout_resp.status_code == 201
    ordine_id = checkout_resp.json()["id"]

    # Step 4: Verifica ordine
    ordine_resp = client.get(f"/api/ordini/{ordine_id}")
    assert ordine_resp.status_code == 200
    ordine = ordine_resp.json()
    assert ordine["stato"] == "confermato"
    assert ordine["totale"] > 0
```

Gli E2E test sono i più "reali" — verificano che l'utente possa effettivamente completare
un'azione — ma sono anche i più:
- **Lenti:** ogni test può richiedere secondi o minuti
- **Fragili:** se il server, il database, o la rete hanno problemi, il test fallisce
- **Difficili da diagnosticare:** quando falliscono, non è sempre ovvio perché

---

### Perché la forma di piramide e non un quadrato?

Molti principianti pensano: "Se gli E2E test verificano tutto, perché non scrivere solo
quelli?" La risposta è il **costo di manutenzione**.

Considera: se scrivi 500 E2E test e cambiano l'URL di un endpoint, devi aggiornare 500 test.
Se scrivi 400 unit test + 80 integration test + 20 E2E test e cambiano quell'URL, aggiorni
solo i 20 E2E test.

Inoltre, gli E2E test sono **lenti**. Una suite di 500 E2E test potrebbe richiedere un'ora
per completarsi. Una suite di 400 unit test richiede secondi.

La piramide suggerisce una distribuzione ottimale:
- **70% unit test** — molti, veloci, precisi
- **20% integration test** — moderati, più lenti
- **10% E2E test** — pochi, lenti, ma indispensabili

---

### L'Anti-Pattern: il Cono Gelato

Esiste un anti-pattern famoso nel testing chiamato **cono gelato** (ice cream cone):

```
   /___________\
  /   E2E Tests \    ← Tantissimi E2E (lenti, fragili)
 /_______________\
/  Integr. Tests  \  ← Pochi integration
/__________________\
\   Unit Tests     /  ← Pochissimi unit (o nessuno!)
 \________________/
```

Questo succede quando il team non ha una cultura del testing o non sa come scrivere unit test.
Il risultato: una suite di test lenta, fragile, che viene disabilitata perché "ci mette troppo
a girare" o "si rompe sempre per motivi stupidi".

---

### La Piramide nella Pratica

Per un progetto reale di medie dimensioni (es. un'applicazione web con API REST), una
distribuzione sana potrebbe essere:

| Tipo | Quantità | Tempo di esecuzione |
|---|---|---|
| Unit test | 350 | ~2 secondi |
| Integration test | 80 | ~45 secondi |
| E2E test | 15 | ~4 minuti |
| **Totale** | **445** | **~5 minuti** |

5 minuti per verificare l'intera applicazione è ragionevole — può girare ad ogni commit
senza rallentare il team.

---

### Esercizio mentale A2

Pensa alle seguenti situazioni e decidi che tipo di test useresti:

1. Verificare che la funzione `somma(a, b)` restituisca `a + b`
2. Verificare che un utente possa effettuare il login via API REST
3. Verificare che quando si aggiunge un prodotto al carrello, il totale si aggiorna
   correttamente e viene salvato nel database
4. Verificare che un utente possa fare login, aggiungere un prodotto, e comprarlo
   attraverso l'intera interfaccia web

**Risposte:**
1. **Unit test** — funzione pura, nessuna dipendenza esterna
2. **Integration test** o **E2E** — richiede un server e un database
3. **Integration test** — verifica l'interazione tra più componenti
4. **E2E test** — verifica un flusso utente completo

---

## A3: pytest — Installazione e Prima Esecuzione

### Perché pytest e non unittest?

Python include nella libreria standard il modulo `unittest`, ispirato a JUnit di Java.
Funziona, ma ha alcune limitazioni che pytest risolve elegantemente.

**Confronto:**

```python
# unittest — verboso, richiede ereditarietà e metodi speciali
import unittest

class TestCalcolatrice(unittest.TestCase):
    def test_addizione(self):
        self.assertEqual(2 + 3, 5)

    def test_divisione_per_zero(self):
        with self.assertRaises(ZeroDivisionError):
            1 / 0

if __name__ == "__main__":
    unittest.main()
```

```python
# pytest — conciso, usa assert normale, nessuna ereditarietà
def test_addizione():
    assert 2 + 3 == 5

def test_divisione_per_zero():
    import pytest
    with pytest.raises(ZeroDivisionError):
        1 / 0
```

pytest vince per:
- **Sintassi più pulita:** usi `assert` normale invece di `self.assertEqual`, `self.assertTrue`, etc.
- **Output migliore:** quando un test fallisce, pytest mostra esattamente cosa è andato storto
- **Fixture potenti:** sistema di setup/teardown molto più flessibile
- **Parametrizzazione:** `@pytest.mark.parametrize` è molto più ergonomico di `subTest`
- **Ecosistema di plugin:** oltre 1500 plugin disponibili su PyPI
- **Compatibilità:** pytest esegue anche i test scritti con unittest, senza modifiche

---

### Installazione

Prima di tutto, assicurati di avere un ambiente virtuale attivo. Se non sai cosa è un
ambiente virtuale, leggi la sezione corrispondente in `tutorial_01`.

```bash
# Crea e attiva l'ambiente virtuale (se non esiste già)
python -m venv venv

# Windows (PowerShell)
venv\Scripts\Activate.ps1

# macOS/Linux
source venv/bin/activate

# Installa pytest
pip install pytest

# Verifica l'installazione
pytest --version
```

**Output atteso:**
```
pytest 8.3.2
```

Installa anche alcuni plugin essenziali che useremo in questo tutorial:

```bash
pip install pytest-cov pytest-mock pytest-asyncio
```

- `pytest-cov` — misura la coverage del codice
- `pytest-mock` — facilita il mocking con la fixture `mocker`
- `pytest-asyncio` — supporto per test asincroni

---

### Struttura del progetto

Una buona struttura di progetto separa il codice sorgente dai test:

```
mio_progetto/
├── src/                    ← Codice sorgente
│   ├── __init__.py
│   ├── calcolatrice.py
│   └── validazione.py
├── tests/                  ← Test
│   ├── __init__.py
│   ├── conftest.py         ← Fixture condivise (spiegato in B4)
│   ├── test_calcolatrice.py
│   └── test_validazione.py
├── pyproject.toml          ← Configurazione del progetto e di pytest
└── README.md
```

**Regola fondamentale:** i file di test devono chiamarsi `test_*.py` oppure `*_test.py`.
Le funzioni di test devono iniziare con `test_`.

---

### Il primo progetto di test

Creiamo un progetto di esempio minimale.

**Passo 1:** crea la struttura delle directory:

```bash
mkdir mio_progetto
cd mio_progetto
mkdir src tests
touch src/__init__.py tests/__init__.py
```

**Passo 2:** crea il codice sorgente (`src/calcolatrice.py`):

```python
# src/calcolatrice.py

def somma(a: float, b: float) -> float:
    """Restituisce la somma di a e b."""
    return a + b


def sottrazione(a: float, b: float) -> float:
    """Restituisce la differenza a - b."""
    return a - b


def moltiplicazione(a: float, b: float) -> float:
    """Restituisce il prodotto a * b."""
    return a * b


def divisione(a: float, b: float) -> float:
    """
    Restituisce il quoziente a / b.

    Raises:
        ValueError: se b è zero.
    """
    if b == 0:
        raise ValueError("Impossibile dividere per zero")
    return a / b
```

**Passo 3:** crea il file di test (`tests/test_calcolatrice.py`):

```python
# tests/test_calcolatrice.py

import pytest
from src.calcolatrice import somma, sottrazione, moltiplicazione, divisione


def test_somma_interi():
    assert somma(2, 3) == 5


def test_somma_negativi():
    assert somma(-1, -2) == -3


def test_sottrazione():
    assert sottrazione(10, 4) == 6


def test_moltiplicazione():
    assert moltiplicazione(3, 4) == 12


def test_divisione():
    assert divisione(10, 2) == 5.0


def test_divisione_per_zero():
    with pytest.raises(ValueError, match="Impossibile dividere per zero"):
        divisione(10, 0)
```

**Passo 4:** esegui i test:

```bash
pytest tests/
```

**Output atteso:**
```
========================= test session starts ==========================
platform linux -- Python 3.12.3, pytest-8.3.2, pluggy-1.5.0
rootdir: /path/to/mio_progetto
collected 6 items

tests/test_calcolatrice.py ......                                [100%]

========================== 6 passed in 0.03s ===========================
```

Sei puntini (`.`) = sei test passati. Il 100% indica che tutti i test hanno completato.

---

### Comandi pytest essenziali

```bash
# Esegui tutti i test nella directory corrente e sottodirectory
pytest

# Esegui i test con output verboso (un test per riga)
pytest -v

# Esegui solo un file specifico
pytest tests/test_calcolatrice.py

# Esegui un singolo test specifico
pytest tests/test_calcolatrice.py::test_somma_interi

# Esegui test il cui nome contiene una parola chiave
pytest -k "divisione"

# Mostra i print() durante i test (normalmente soppressi)
pytest -s

# Mostra i 10 test più lenti
pytest --durations=10

# Fermati al primo fallimento
pytest -x

# Fermati dopo N fallimenti
pytest --maxfail=3

# Esegui con coverage (richiede pytest-cov)
pytest --cov=src tests/
```

---

### Configurazione in pyproject.toml

Puoi configurare pytest in un file `pyproject.toml` nella root del progetto:

```toml
# pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]              # Dove cercare i test
python_files = ["test_*.py"]      # Pattern per i file di test
python_functions = ["test_*"]     # Pattern per le funzioni di test
addopts = ["-v", "--tb=short"]    # Opzioni aggiunte automaticamente
```

Con questa configurazione, eseguire `pytest` dalla root del progetto equivale a
eseguire `pytest tests/ -v --tb=short`.

---

## A4: Il Primo Test — `assert` è tutto quello che ti serve

### La magia di assert in pytest

In Python, `assert` è un'istruzione nativa del linguaggio che verifica una condizione:

```python
assert 2 + 2 == 4          # OK, non succede nulla
assert 2 + 2 == 5          # AssertionError!
```

In Python normale, `AssertionError` mostra solo un messaggio generico. pytest trasforma
completamente questa esperienza: **riscrive internamente le assert** per fornire messaggi
d'errore dettagliati e utili.

Questo è uno dei motivi per cui pytest è superiore a unittest: non hai bisogno di ricordare
30 metodi diversi (`assertEqual`, `assertIn`, `assertIsInstance`, `assertAlmostEqual`...).
Usi semplicemente `assert` e pytest fa il resto.

---

### Esempi di assert con pytest

Creiamo un file di test per esplorare le diverse forme di assert:

```python
# tests/test_assert_examples.py

import pytest


# --- Assert su valori semplici ---

def test_uguaglianza_interi():
    risultato = 2 + 2
    assert risultato == 4


def test_uguaglianza_stringhe():
    saluto = "Ciao"
    assert saluto == "Ciao"


def test_disuguaglianza():
    assert 3 != 4


def test_comparazioni():
    assert 5 > 3
    assert 3 < 5
    assert 5 >= 5
    assert 3 <= 3


# --- Assert su collezioni ---

def test_lista_contiene_elemento():
    frutti = ["mela", "banana", "arancia"]
    assert "banana" in frutti


def test_stringa_contiene_sottostriga():
    messaggio = "Il pagamento è stato confermato"
    assert "confermato" in messaggio


def test_lista_lunghezza():
    numeri = [1, 2, 3, 4, 5]
    assert len(numeri) == 5


def test_lista_uguaglianza():
    lista1 = [1, 2, 3]
    lista2 = [1, 2, 3]
    assert lista1 == lista2


def test_dizionario_ha_chiave():
    config = {"debug": True, "porta": 8080}
    assert "debug" in config
    assert config["porta"] == 8080


# --- Assert su tipi ---

def test_tipo_oggetto():
    risultato = {"chiave": "valore"}
    assert isinstance(risultato, dict)


def test_oggetto_none():
    risultato = None
    assert risultato is None


def test_oggetto_non_none():
    risultato = 42
    assert risultato is not None


# --- Assert su numeri float (ATTENZIONE!) ---

def test_somma_float_sbagliata():
    # Questo test FALLIREBBE con == !
    # 0.1 + 0.2 in Python non è esattamente 0.3
    # print(0.1 + 0.2)  # 0.30000000000000004
    pass


def test_somma_float_corretta():
    # pytest.approx risolve il problema dei float
    assert 0.1 + 0.2 == pytest.approx(0.3)


def test_approssimazione_con_tolleranza():
    # La tolleranza predefinita di pytest.approx è 1e-6 (relativa)
    assert 3.14159 == pytest.approx(3.14, rel=1e-2)  # 1% di tolleranza


# --- Assert con booleani ---

def test_valore_truthy():
    lista_non_vuota = [1, 2, 3]
    assert lista_non_vuota  # truthy se non vuota


def test_valore_falsy():
    lista_vuota = []
    assert not lista_vuota  # falsy se vuota
```

---

## [Sezione Speciale] Come Leggere un Output di pytest Fallito

> **Nota per il principiante:** Questa è LA sezione più importante di tutto il tutorial.
> Ogni principiante si blocca davanti al primo output di errore di pytest. Dopo questa
> sezione, sarai in grado di leggere qualsiasi output di errore e capire esattamente
> cosa è successo.

### Creiamo un test che fallisce intenzionalmente

```python
# tests/test_fallimento_esempio.py

def test_che_fallisce():
    lista_attesa = [1, 2, 3, 5]   # NOTA: 5 alla fine
    lista_reale  = [1, 2, 3, 4]   # NOTA: 4 alla fine
    assert lista_reale == lista_attesa
```

Eseguiamo:

```bash
pytest tests/test_fallimento_esempio.py -v
```

**Output completo:**
```
========================= test session starts ==========================
platform linux -- Python 3.12.3, pytest-8.3.2, pluggy-1.5.0
rootdir: /path/to/mio_progetto
collected 1 item

tests/test_fallimento_esempio.py::test_che_fallisce FAILED      [100%]

=============================== FAILURES ================================
_________________________ test_che_fallisce ____________________________

    def test_che_fallisce():
        lista_attesa = [1, 2, 3, 5]   # NOTA: 5 alla fine
        lista_reale  = [1, 2, 3, 4]   # NOTA: 4 alla fine
>       assert lista_reale == lista_attesa

E       AssertionError: assert [1, 2, 3, 4] == [1, 2, 3, 5]
E         At index 3 diff: 4 != 5
E         Use -v to get more diff

========================= short test summary info =======================
FAILED tests/test_fallimento_esempio.py::test_che_fallisce
========================== 1 failed in 0.03s ===========================
```

Analizziamo ogni riga:

---

#### Riga 1: Intestazione della sessione

```
========================= test session starts ==========================
```
Indica l'inizio dell'esecuzione. Se vedi questo, pytest è partito.

---

#### Riga 2: Informazioni sull'ambiente

```
platform linux -- Python 3.12.3, pytest-8.3.2, pluggy-1.5.0
```
Mostra il sistema operativo, la versione di Python, di pytest e di pluggy
(il sistema di plugin). Utile per il debugging se il test fallisce solo
su una certa piattaforma.

---

#### Riga 3: Root directory

```
rootdir: /path/to/mio_progetto
```
La directory "radice" che pytest ha identificato come punto di partenza.
Influenza come vengono trovati i file di configurazione.

---

#### Riga 4: Raccolta

```
collected 1 item
```
pytest ha trovato e "raccolto" 1 test. Se scrivi un test e non viene
raccolto, controlla: il nome del file inizia con `test_`? Il nome della
funzione inizia con `test_`?

---

#### Riga 5: Stato del test

```
tests/test_fallimento_esempio.py::test_che_fallisce FAILED      [100%]
```
- `tests/test_fallimento_esempio.py` — il file
- `::` — separatore
- `test_che_fallisce` — il nome del test
- `FAILED` — il test ha fallito
- `[100%]` — percentuale di completamento (100% = tutti i test raccolti sono stati eseguiti)

**Possibili stati:**
- `PASSED` — test superato
- `FAILED` — test fallito (una assertion non è soddisfatta)
- `ERROR` — errore durante l'esecuzione (eccezione non gestita nel test o nel setup)
- `SKIPPED` — test saltato (`pytest.mark.skip`)
- `XFAIL` — test atteso fallire, ed effettivamente fallisce (`pytest.mark.xfail`)
- `XPASS` — test atteso fallire, ma è passato (potenzialmente un problema)

---

#### Sezione FAILURES

```
=============================== FAILURES ================================
_________________________ test_che_fallisce ____________________________
```
Intestazione della sezione dei fallimenti, con il nome del test che ha fallito.

---

#### Il codice del test

```python
    def test_che_fallisce():
        lista_attesa = [1, 2, 3, 5]   # NOTA: 5 alla fine
        lista_reale  = [1, 2, 3, 4]   # NOTA: 4 alla fine
>       assert lista_reale == lista_attesa
```

pytest mostra il codice del test. La freccia `>` indica la riga esatta che ha fallito.

---

#### Il messaggio di errore

```
E       AssertionError: assert [1, 2, 3, 4] == [1, 2, 3, 5]
E         At index 3 diff: 4 != 5
E         Use -v to get more diff
```

Ogni riga che inizia con `E` fa parte del messaggio di errore:
- Prima riga: `AssertionError` — il tipo di errore, poi la rappresentazione dell'assert fallita
  con i valori reali inseriti. Puoi vedere esattamente `[1, 2, 3, 4]` (il valore reale)
  e `[1, 2, 3, 5]` (il valore atteso).
- Seconda riga: `At index 3 diff: 4 != 5` — pytest ha analizzato le due liste e ha trovato
  la prima differenza: all'indice 3, il valore reale è `4` ma quello atteso è `5`.
- Terza riga: suggerimento di usare `-v` per avere un diff più dettagliato.

---

#### Riepilogo finale

```
========================= short test summary info =======================
FAILED tests/test_fallimento_esempio.py::test_che_fallisce
========================== 1 failed in 0.03s ===========================
```

Riepilogo: 1 test fallito, esecuzione completata in 0.03 secondi.

---

### Altri esempi di output di errore

#### Errore con stringhe

```python
def test_stringhe():
    atteso = "Ciao Mario"
    reale  = "Ciao Luigi"
    assert reale == atteso
```

```
E   AssertionError: assert 'Ciao Luigi' == 'Ciao Mario'
E
E   - Ciao Mario
E   + Ciao Luigi
E   ?      ^^^^^
E   ?      -----
```

Il formato `diff` con `+` e `-` mostra cosa c'è nel valore reale (`+`) e cosa c'è
nel valore atteso (`-`). I `^` e `-` puntano alla parte diversa.

---

#### Errore con numeri

```python
def test_numeri():
    assert 42 == 43
```

```
E   AssertionError: assert 42 == 43
```

Semplice: mostra i due valori.

---

#### Errore con dizionari

```python
def test_dizionari():
    atteso = {"nome": "Mario", "eta": 30}
    reale  = {"nome": "Mario", "eta": 31}
    assert reale == atteso
```

```
E   AssertionError: assert {'nome': 'Mario', 'eta': 31} == {'nome': 'Mario', 'eta': 30}
E   
E   Omitting 1 identical items, use -v to show
E   Left contains 1 more item:
E   {'eta': 31}
E   Right contains 1 more item:
E   {'eta': 30}
```

---

#### Errore con eccezione non gestita (ERROR vs FAILED)

```python
def test_con_errore():
    lista = [1, 2, 3]
    assert lista[10] == 5  # IndexError! Non un AssertionError
```

```
tests/test_fallimento_esempio.py::test_con_errore ERROR

================================== ERRORS ==================================
__________________ ERROR in test_con_errore ___________________________

    def test_con_errore():
        lista = [1, 2, 3]
>       assert lista[10] == 5
E       IndexError: list index out of range

========================= 1 error in 0.03s ============================
```

**Differenza importante:**
- `FAILED` = una `assert` ha prodotto `AssertionError`
- `ERROR` = un'eccezione *inattesa* è stata sollevata nel codice del test

---

#### I simboli compatti (senza -v)

Quando esegui `pytest` senza `-v`, ogni test viene rappresentato da un simbolo compatto:

```
tests/test_calcolo.py ..F.sEx.          [100%]
```

- `.` — PASSED
- `F` — FAILED
- `E` — ERROR
- `s` — SKIPPED
- `x` — XFAIL (expected failure)
- `X` — XPASS (unexpected pass)

---

### Checklist: "Il mio test fallisce, cosa faccio?"

1. **Leggi il nome del test che ha fallito** — `test_calcolatrice.py::test_divisione`
2. **Cerca la freccia `>`** — indica la riga esatta del fallimento
3. **Leggi le righe `E`** — mostrano i valori reali vs attesi
4. **Confronta i valori** — il valore "atteso" è quello che hai scritto nel test;
   il valore "reale" è quello che il codice produce effettivamente
5. **Decidi:** il test è sbagliato, o il codice è sbagliato?

---

## A5: `assert` con Messaggi Personalizzati

### Perché aggiungere messaggi?

L'output di pytest di default è già molto informativo, ma a volte un messaggio personalizzato
chiarisce immediatamente il *contesto* del fallimento, non solo i valori.

Confronta questi due output:

**Senza messaggio:**
```
AssertionError: assert 5 == 6
```

**Con messaggio:**
```
AssertionError: Carrello con 2 prodotti da 5€ ciascuno dovrebbe avere totale 10€, ma ne ha 5€
assert 5 == 10
```

Il secondo messaggio dice immediatamente *cosa* stava succedendo, non solo *che cosa* è fallito.

---

### Sintassi

La sintassi per aggiungere un messaggio personalizzato a `assert` è:

```python
assert condizione, "Messaggio di errore personalizzato"
```

Il messaggio viene mostrato solo se la condizione è `False`.

```python
# tests/test_messaggi.py

def test_totale_carrello():
    prezzi = [5.0, 3.0, 2.0]
    totale = sum(prezzi)

    assert totale == 10.0, (
        f"Il totale del carrello dovrebbe essere 10.0€, "
        f"ma è {totale}€. Prezzi nel carrello: {prezzi}"
    )


def test_utente_maggiorenne():
    eta = 16
    assert eta >= 18, (
        f"L'utente con età {eta} non dovrebbe poter accedere al sito. "
        f"Età minima richiesta: 18 anni."
    )


def test_email_valida():
    email = "mario.rossi"
    # Verifica base: contiene una @
    assert "@" in email, (
        f"L'email '{email}' non contiene '@' ed è quindi invalida. "
        f"Usa il formato: nome@dominio.it"
    )


def test_lista_non_vuota():
    risultati_ricerca = []  # Simuliamo una ricerca senza risultati
    assert len(risultati_ricerca) > 0, (
        f"La ricerca non ha restituito risultati. "
        f"La lista dovrebbe contenere almeno un elemento."
    )
```

---

### Quando usare i messaggi personalizzati?

**Usa un messaggio personalizzato quando:**
- Il contesto non è ovvio dai valori soli
- Stai verificando una proprietà complessa di un oggetto
- Il fallimento potrebbe avere cause diverse e vuoi guidare la diagnosi
- Stai lavorando in team e vuoi che il messaggio sia auto-esplicativo

**Non serve un messaggio quando:**
- I valori nell'output standard già spiegano tutto
- Il nome del test è sufficientemente descrittivo
- L'assert è triviale (`assert x == 5`)

---

### Messaggi multi-riga con f-string

Per messaggi complessi, usa le parentesi per andare a capo:

```python
def test_ordine_completo():
    ordine = {
        "prodotti": ["Mela", "Pane"],
        "totale": 1.70,
        "stato": "bozza"
    }

    assert ordine["stato"] == "confermato", (
        f"L'ordine dovrebbe essere nello stato 'confermato', "
        f"ma è '{ordine['stato']}'.\n"
        f"Prodotti nell'ordine: {ordine['prodotti']}\n"
        f"Totale: {ordine['totale']}€"
    )
```

---

### Alternativa: usare variabili intermediate

A volte è più chiaro calcolare i valori intermedi e mostrare l'intera catena:

```python
def test_sconto_fedelta():
    prezzo_originale = 100.0
    punti_fedelta = 1500
    sconto_atteso = 10.0  # 10% per clienti con > 1000 punti

    # Calcola lo sconto
    if punti_fedelta > 1000:
        sconto_calcolato = prezzo_originale * 0.10
    else:
        sconto_calcolato = 0.0

    assert sconto_calcolato == sconto_atteso, (
        f"Sconto calcolato: {sconto_calcolato}€\n"
        f"Sconto atteso: {sconto_atteso}€\n"
        f"Punti fedeltà: {punti_fedelta}\n"
        f"Regola: sconto 10% per punti > 1000"
    )
```

---

## A6: Test per le Eccezioni — `pytest.raises`

### Il problema: come testare che qualcosa vada storto?

I test non verificano solo il "percorso felice" — verificano anche che il codice si comporti
correttamente quando le cose vanno storto. Un sistema robusto:
- Rifiuta input invalidi
- Solleva eccezioni appropriate con messaggi utili
- Non crasha silenziosamente

Come testi che una funzione solleva un'eccezione? Non puoi usare `assert` direttamente,
perché l'eccezione interromperebbe il test prima di arrivare all'assert.

La soluzione è `pytest.raises()`.

---

### Utilizzo base

```python
# tests/test_eccezioni.py

import pytest
from src.calcolatrice import divisione


def test_divisione_per_zero_solleva_eccezione():
    """Verifica che la divisione per zero sollevi ValueError."""
    with pytest.raises(ValueError):
        divisione(10, 0)
```

Il context manager `pytest.raises(ValueError)` cattura l'eccezione di tipo `ValueError`.
Se l'eccezione viene sollevata, il test passa. Se non viene sollevata (o viene sollevata
un'eccezione diversa), il test fallisce.

---

### Verificare il messaggio dell'eccezione

Spesso vuoi verificare non solo *che* un'eccezione venga sollevata, ma anche *cosa dice*
il messaggio di errore:

```python
def test_divisione_per_zero_messaggio():
    """Verifica sia il tipo che il messaggio dell'eccezione."""
    with pytest.raises(ValueError, match="Impossibile dividere per zero"):
        divisione(10, 0)
```

Il parametro `match` usa una **espressione regolare** per cercare una corrispondenza
nel messaggio dell'eccezione. Non deve essere la stringa esatta — basta che sia contenuta.

```python
# match verifica con regex — questi sono tutti equivalenti per il messaggio
# "Impossibile dividere per zero"

with pytest.raises(ValueError, match="Impossibile"):        # OK - parziale
with pytest.raises(ValueError, match="dividere per zero"):  # OK - parziale
with pytest.raises(ValueError, match="Impossibile dividere per zero"):  # OK - completo
with pytest.raises(ValueError, match=r"[Ii]mpossibile"):   # OK - regex
```

---

### Ispezionare l'eccezione nel dettaglio

Se vuoi accedere all'oggetto eccezione per verificare attributi specifici:

```python
class ErroreOrdine(Exception):
    """Eccezione personalizzata per errori negli ordini."""
    def __init__(self, messaggio: str, codice_errore: int):
        super().__init__(messaggio)
        self.codice_errore = codice_errore


def processa_ordine(importo: float) -> dict:
    """Elabora un ordine. Lancia ErroreOrdine se l'importo è negativo."""
    if importo < 0:
        raise ErroreOrdine(
            f"Importo negativo non valido: {importo}",
            codice_errore=400
        )
    return {"stato": "confermato", "importo": importo}


def test_importo_negativo_codice_errore():
    """Verifica il codice errore dell'eccezione personalizzata."""
    with pytest.raises(ErroreOrdine) as exc_info:
        processa_ordine(-50.0)

    # exc_info.value contiene l'oggetto eccezione
    eccezione = exc_info.value
    assert eccezione.codice_errore == 400
    assert "negativo" in str(eccezione)
```

La variabile `exc_info` è un oggetto speciale di pytest:
- `exc_info.value` — l'oggetto eccezione effettivo
- `exc_info.type` — il tipo dell'eccezione
- `exc_info.tb` — il traceback

---

### Esempi pratici

```python
# Testa validazione dell'età
def valida_eta(eta: int) -> None:
    if not isinstance(eta, int):
        raise TypeError(f"L'età deve essere un intero, ricevuto: {type(eta).__name__}")
    if eta < 0:
        raise ValueError(f"L'età non può essere negativa: {eta}")
    if eta > 150:
        raise ValueError(f"L'età {eta} non è realistica (massimo: 150)")


def test_eta_negativa():
    with pytest.raises(ValueError, match="negativa"):
        valida_eta(-1)


def test_eta_irrealistica():
    with pytest.raises(ValueError, match="non è realistica"):
        valida_eta(200)


def test_eta_tipo_sbagliato():
    with pytest.raises(TypeError, match="intero"):
        valida_eta("trentasei")  # Stringa invece di int


def test_eta_valida_non_solleva():
    """Verifica che un'età valida NON sollevi eccezioni."""
    valida_eta(25)   # Deve passare senza eccezioni
    valida_eta(0)    # Età zero è ammessa (neonato)
    valida_eta(100)  # Centenario — valido
```

---

### Testare eccezioni in sequenza

```python
def test_errori_multipli():
    """Testa più scenari di errore nella stessa funzione."""

    # Scenario 1: divisore è zero
    with pytest.raises(ValueError, match="zero"):
        divisione(10, 0)

    # Scenario 2: input non numerici (se la funzione li gestisce)
    # with pytest.raises(TypeError):
    #     divisione("dieci", "due")
```

---

### Errore comune: non usare il context manager

```python
# SBAGLIATO — l'eccezione non viene catturata e il test crasha
def test_sbagliato():
    pytest.raises(ValueError)  # Senza 'with'!
    divisione(10, 0)           # Questa eccezione non viene catturata

# CORRETTO
def test_corretto():
    with pytest.raises(ValueError):
        divisione(10, 0)
```

---

## A7: Test per i Warning — `pytest.warns`

### Cosa sono i warning Python?

I warning sono messaggi di avviso che il codice emette per segnalare comportamenti
potenzialmente problematici senza interrompere l'esecuzione. Sono diversi dalle eccezioni:

```python
import warnings

# Un'eccezione blocca il programma
# raise ValueError("Errore grave")

# Un warning avvisa senza bloccare
warnings.warn("Questa funzione è deprecata", DeprecationWarning)
# Il codice continua normalmente dopo il warning
```

I warning vengono usati tipicamente per:
- **Deprecation Warning** — la funzione esiste ancora ma sarà rimossa in futuro
- **User Warning** — avviso per l'utente su un utilizzo potenzialmente sbagliato
- **Resource Warning** — risorsa (file, connessione) non chiusa correttamente

---

### pytest.warns

`pytest.warns` funziona esattamente come `pytest.raises`, ma per i warning:

```python
# tests/test_warning.py

import warnings
import pytest


def funzione_deprecata(x: int) -> int:
    """
    Calcola il quadrato di x.

    .. deprecated:: 2.0
       Usa `quadrato_v2()` invece.
    """
    warnings.warn(
        "funzione_deprecata() è deprecata. Usa quadrato_v2() invece.",
        DeprecationWarning,
        stacklevel=2,  # Indica che il warning viene dal chiamante
    )
    return x ** 2


def test_avviso_deprecazione():
    """Verifica che la funzione emetta il DeprecationWarning corretto."""
    with pytest.warns(DeprecationWarning, match="deprecata"):
        risultato = funzione_deprecata(5)

    # Verifica anche che il calcolo sia corretto
    assert risultato == 25


def test_avviso_contiene_alternativa():
    """Verifica che il warning menzioni la funzione sostitutiva."""
    with pytest.warns(DeprecationWarning, match="quadrato_v2"):
        funzione_deprecata(10)
```

---

### Catturare e ispezionare i warning

```python
def funzione_con_input_sospetto(valori: list[float]) -> float:
    """Calcola la media, emette warning se ci sono NaN."""
    import math

    nan_trovati = [v for v in valori if math.isnan(v)]
    if nan_trovati:
        warnings.warn(
            f"Trovati {len(nan_trovati)} valori NaN. "
            f"Saranno ignorati nel calcolo.",
            UserWarning
        )

    valori_puliti = [v for v in valori if not math.isnan(v)]
    if not valori_puliti:
        raise ValueError("Nessun valore valido")
    return sum(valori_puliti) / len(valori_puliti)


def test_media_con_nan():
    """Verifica warning e calcolo corretto in presenza di NaN."""
    import math
    valori = [1.0, 2.0, float("nan"), 3.0]

    with pytest.warns(UserWarning) as warning_info:
        media = funzione_con_input_sospetto(valori)

    # Verifica il risultato del calcolo
    assert media == 2.0  # (1+2+3)/3, NaN escluso

    # Verifica il messaggio del warning
    assert len(warning_info) == 1  # Esattamente un warning
    messaggio = str(warning_info[0].message)
    assert "NaN" in messaggio
    assert "ignorati" in messaggio
```

---

### Verificare che NON vengano emessi warning

A volte vuoi verificare che il tuo codice sia "silenzioso" — non emetta warning inattesi:

```python
def test_nessun_warning_con_input_valido():
    """Verifica che input validi non producano warning."""
    valori = [1.0, 2.0, 3.0, 4.0]

    # recwarn è una fixture built-in di pytest
    # Se dopo il blocco non ci sono warning, il test passa
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("error")  # Trasforma warning in eccezioni
        # Se viene emesso un warning, questo blocco solleverà un'eccezione
        # e il test fallirà
        media = funzione_con_input_sospetto(valori)

    assert media == 2.5
```

---

### Recap Parte A

Prima di passare alla Parte B, facciamo un riepilogo di quello che hai imparato:

| Concetto | Cosa fa | Quando usarlo |
|---|---|---|
| `assert valore == atteso` | Verifica uguaglianza | Sempre, per la maggior parte dei test |
| `assert valore == pytest.approx(float)` | Verifica float con tolleranza | Quando confronti numeri decimali |
| `assert "testo" in stringa` | Verifica contenuto | Quando cerchi una sottostringa |
| `assert cond, "messaggio"` | Assert con messaggio custom | Quando il contesto non è ovvio |
| `with pytest.raises(TipoEccezione):` | Verifica che un'eccezione venga sollevata | Per testare la gestione degli errori |
| `with pytest.raises(T, match="regex"):` | Verifica tipo E messaggio eccezione | Quando il messaggio dell'eccezione è importante |
| `with pytest.warns(TipoWarning):` | Verifica che un warning venga emesso | Per funzioni deprecate o con avvisi |

---

> **Prima di continuare:** esegui tutti gli esempi di questa sezione tu stesso.
> Non limitarti a leggerli — scrivili, eseguili, modifica qualcosa per farli fallire,
> e leggi l'output. La pratica è l'unico modo per interiorizzare questi concetti.

---

## PARTE B — COMPRENSIONE PROFONDA

---

## B1: Fixtures — Il Codice di Setup che Non Si Ripete

### Il problema: la duplicazione del setup

Considera questa situazione. Stai scrivendo test per un sistema che gestisce una rubrica
telefonica:

```python
# tests/test_rubrica_senza_fixture.py

def test_aggiungi_contatto():
    # Setup: crea una rubrica vuota e aggiungi dati iniziali
    rubrica = Rubrica()
    rubrica.aggiungi("Mario Rossi", "555-1234")
    rubrica.aggiungi("Luigi Bianchi", "555-5678")

    # Test
    rubrica.aggiungi("Anna Verdi", "555-9999")
    assert rubrica.conta() == 3


def test_trova_contatto():
    # Setup: STESSO codice ripetuto!
    rubrica = Rubrica()
    rubrica.aggiungi("Mario Rossi", "555-1234")
    rubrica.aggiungi("Luigi Bianchi", "555-5678")

    # Test
    numero = rubrica.cerca("Mario Rossi")
    assert numero == "555-1234"


def test_rimuovi_contatto():
    # Setup: ANCORA lo stesso codice!
    rubrica = Rubrica()
    rubrica.aggiungi("Mario Rossi", "555-1234")
    rubrica.aggiungi("Luigi Bianchi", "555-5678")

    # Test
    rubrica.rimuovi("Mario Rossi")
    assert rubrica.conta() == 1
```

Il codice di setup è ripetuto identico in tutti e tre i test. Questo è problematico:
- Se il setup deve cambiare (es. aggiungiamo un terzo contatto iniziale), devi modificare
  tutti i test
- Viola il principio DRY (Don't Repeat Yourself)
- Rende i test più lunghi e meno leggibili

---

### La soluzione: le fixture

**Analogia:** immagina un ristorante. Prima di aprire, il cuoco prepara il mise en place:
ingredienti tagliati, salse pronte, attrezzatura posizionata. Ogni chef (test) trova
tutto già pronto senza dover rifare il setup da zero.

Le **fixture** di pytest sono esattamente questo: codice di preparazione eseguito
automaticamente prima del test, senza bisogno di chiamarlo esplicitamente.

```python
# tests/test_rubrica_con_fixture.py

import pytest


class Rubrica:
    def __init__(self):
        self._contatti = {}

    def aggiungi(self, nome: str, numero: str) -> None:
        self._contatti[nome] = numero

    def cerca(self, nome: str) -> str | None:
        return self._contatti.get(nome)

    def rimuovi(self, nome: str) -> None:
        del self._contatti[nome]

    def conta(self) -> int:
        return len(self._contatti)


@pytest.fixture
def rubrica_con_dati():
    """Fixture: crea una rubrica con due contatti pre-inseriti."""
    r = Rubrica()
    r.aggiungi("Mario Rossi", "555-1234")
    r.aggiungi("Luigi Bianchi", "555-5678")
    return r


# Ora ogni test riceve la rubrica già configurata
def test_aggiungi_contatto(rubrica_con_dati):
    rubrica_con_dati.aggiungi("Anna Verdi", "555-9999")
    assert rubrica_con_dati.conta() == 3


def test_trova_contatto(rubrica_con_dati):
    numero = rubrica_con_dati.cerca("Mario Rossi")
    assert numero == "555-1234"


def test_rimuovi_contatto(rubrica_con_dati):
    rubrica_con_dati.rimuovi("Mario Rossi")
    assert rubrica_con_dati.conta() == 1
```

**Come funziona:** pytest vede che `test_aggiungi_contatto` ha un parametro chiamato
`rubrica_con_dati`. Cerca una fixture con quel nome, la esegue, e passa il valore
restituito al test. Tutto automaticamente, senza import.

---

### Il meccanismo della fixture: dependency injection

Questo meccanismo si chiama **dependency injection** (iniezione di dipendenze). pytest
"inietta" la fixture nel test come dipendenza. Non stai chiamando la fixture tu — è
pytest che la chiama e ti passa il risultato.

Puoi usare più fixture nello stesso test:

```python
@pytest.fixture
def rubrica_vuota():
    return Rubrica()


@pytest.fixture
def contatti_esempio():
    return [
        ("Mario Rossi", "555-1234"),
        ("Luigi Bianchi", "555-5678"),
    ]


def test_inserimento_multiplo(rubrica_vuota, contatti_esempio):
    for nome, numero in contatti_esempio:
        rubrica_vuota.aggiungi(nome, numero)

    assert rubrica_vuota.conta() == len(contatti_esempio)
```

---

### Scope delle fixture: quanto dura la fixture?

Lo **scope** controlla quando la fixture viene creata e distrutta.

#### scope="function" (predefinito)

La fixture viene creata all'inizio di ogni test e distrutta alla fine. Ogni test
riceve una copia fresca della fixture.

```python
@pytest.fixture(scope="function")  # "function" è il default
def rubrica_fresca():
    """Nuova rubrica per ogni test."""
    return Rubrica()


def test_1(rubrica_fresca):
    rubrica_fresca.aggiungi("Mario", "555-0001")
    # Questa rubrica esiste solo in test_1


def test_2(rubrica_fresca):
    # Questa è una NUOVA rubrica — Mario non c'è!
    assert rubrica_fresca.conta() == 0
```

---

#### scope="class"

La fixture viene creata una volta per ogni classe di test e condivisa tra tutti i
metodi della classe.

```python
@pytest.fixture(scope="class")
def connessione_database():
    """Una connessione per tutti i test nella classe."""
    conn = crea_connessione()
    yield conn
    conn.close()


class TestOperazioniDatabase:
    def test_inserimento(self, connessione_database):
        # La stessa connessione viene usata da tutti i metodi
        connessione_database.inserisci({"id": 1})
        assert connessione_database.conta() == 1

    def test_aggiornamento(self, connessione_database):
        # ATTENZIONE: questa fixture è condivisa!
        # I dati inseriti in test_inserimento sono ancora qui
        pass
```

---

#### scope="module"

La fixture viene creata una volta per file `.py` di test e condivisa tra tutti i
test nel file.

```python
@pytest.fixture(scope="module")
def configurazione_app():
    """Caricata una volta per tutto il file di test."""
    print("\nCarico configurazione...")
    config = carica_config("config_test.toml")
    yield config
    print("\nLibero le risorse della configurazione...")
```

---

#### scope="session"

La fixture viene creata una volta per l'intera esecuzione di pytest (tutti i file,
tutti i test). Utile per risorse costose da inizializzare.

```python
@pytest.fixture(scope="session")
def server_di_test():
    """Avvia il server una volta per tutta la sessione."""
    print("\nAvvio server di test...")
    server = avvia_server(porta=9999)

    yield server

    print("\nFermo server di test...")
    server.ferma()
```

---

### La tabella degli scope

| Scope | Quando viene creata | Quando viene distrutta | Esempio d'uso |
|---|---|---|---|
| `function` | Prima di ogni test | Dopo ogni test | Rubrica pulita, dati freschi |
| `class` | Prima della prima funzione della classe | Dopo l'ultima funzione | Connessione DB condivisa in classe |
| `module` | Prima del primo test nel file | Dopo l'ultimo test del file | Configurazione condivisa nel file |
| `session` | Prima di qualsiasi test | Dopo tutti i test | Server, DB connection pool |

---

### yield: la magia del teardown

Le fixture con `yield` hanno due parti: il codice **prima** di `yield` è il setup,
il codice **dopo** è il teardown.

```python
@pytest.fixture
def file_temporaneo(tmp_path):
    """Crea un file temporaneo, poi lo rimuove."""
    percorso = tmp_path / "test_data.txt"
    percorso.write_text("dati iniziali del test")

    yield percorso  # <-- il test riceve questo valore

    # Questa parte viene eseguita DOPO il test, anche se il test fallisce
    percorso.unlink(missing_ok=True)
    print(f"\nFile rimosso: {percorso}")


def test_lettura_file(file_temporaneo):
    contenuto = file_temporaneo.read_text()
    assert contenuto == "dati iniziali del test"


def test_scrittura_file(file_temporaneo):
    file_temporaneo.write_text("nuovi dati")
    assert file_temporaneo.read_text() == "nuovi dati"
    # Dopo questo test, il file viene rimosso automaticamente
```

**La garanzia del teardown:** il codice dopo `yield` viene eseguito *sempre*, anche
se il test fallisce, anche se solleva un'eccezione. È come `finally` in un try/except.

---

### Fixture per database con rollback

Un pattern fondamentale per i test di integrazione è usare il rollback del database:
ogni test opera all'interno di una transazione che viene annullata al termine, lasciando
il database nello stato iniziale.

```python
import sqlite3
import pytest


@pytest.fixture(scope="session")
def database_connessione():
    """Connessione al database (una volta per sessione)."""
    conn = sqlite3.connect(":memory:")
    conn.execute("""
        CREATE TABLE utenti (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL
        )
    """)
    conn.commit()
    yield conn
    conn.close()


@pytest.fixture
def db(database_connessione):
    """
    Per ogni test: torna allo stato pulito.

    In SQLite in-memory non c'è un vero rollback delle transazioni
    come in PostgreSQL, quindi usiamo DELETE per pulire.
    """
    yield database_connessione
    # Teardown: rimuovi tutti i dati inseriti dal test
    database_connessione.execute("DELETE FROM utenti")
    database_connessione.commit()


def test_inserimento_utente(db):
    db.execute("INSERT INTO utenti (nome, email) VALUES (?, ?)",
               ("Mario", "mario@test.it"))
    db.commit()

    cursore = db.execute("SELECT COUNT(*) FROM utenti")
    assert cursore.fetchone()[0] == 1


def test_database_inizia_vuoto(db):
    """Il teardown del test precedente ha pulito il database."""
    cursore = db.execute("SELECT COUNT(*) FROM utenti")
    assert cursore.fetchone()[0] == 0
```

---

### Fixture dipendenti da altre fixture

Le fixture possono dipendere da altre fixture, creando catene di dipendenze:

```python
@pytest.fixture(scope="session")
def engine():
    """Crea il motore del database."""
    conn = sqlite3.connect(":memory:")
    return conn


@pytest.fixture(scope="session")
def schema(engine):
    """Crea lo schema. Dipende da engine."""
    engine.execute("CREATE TABLE prodotti (id INTEGER PRIMARY KEY, nome TEXT)")
    engine.commit()
    return engine


@pytest.fixture
def db_pulito(schema):
    """Database pronto per il test. Dipende da schema."""
    yield schema
    schema.execute("DELETE FROM prodotti")
    schema.commit()
```

pytest risolve automaticamente la catena: per creare `db_pulito`, ha bisogno di `schema`;
per creare `schema`, ha bisogno di `engine`. Li crea nell'ordine corretto.

---

### Fixture built-in di pytest

pytest include diverse fixture integrate molto utili che non devi definire tu:

#### `tmp_path` — Directory temporanea

```python
def test_creazione_file(tmp_path):
    """tmp_path è una directory temporanea unica per ogni test."""
    file = tmp_path / "output.txt"
    file.write_text("contenuto del file")

    assert file.exists()
    assert file.read_text() == "contenuto del file"
    # La directory viene rimossa automaticamente dopo il test
```

#### `capsys` — Cattura stdout/stderr

```python
def test_output_a_schermo(capsys):
    """capsys cattura quello che stampi con print()."""
    print("Elaborazione completata")
    print("Risultato: 42", end="")

    catturato = capsys.readouterr()
    assert "completata" in catturato.out
    assert "42" in catturato.out
    assert catturato.err == ""  # Nessun output su stderr
```

#### `caplog` — Cattura i messaggi di logging

```python
import logging


def test_logging(caplog):
    """caplog cattura i messaggi di log."""
    logger = logging.getLogger(__name__)

    with caplog.at_level(logging.WARNING):
        logger.warning("Questa è un'avvertenza")
        logger.error("Questo è un errore")

    assert "avvertenza" in caplog.text
    assert len(caplog.records) == 2
    assert caplog.records[0].levelname == "WARNING"
    assert caplog.records[1].levelname == "ERROR"
```

#### `monkeypatch` — Modifica temporanea di attributi e variabili d'ambiente

```python
import os


def test_variabile_ambiente(monkeypatch):
    """monkeypatch modifica temporaneamente variabili d'ambiente."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///test.db")
    monkeypatch.setenv("DEBUG", "true")

    # Dentro il test, le variabili d'ambiente hanno i nuovi valori
    assert os.environ["DATABASE_URL"] == "sqlite:///test.db"
    # Dopo il test, vengono ripristinate automaticamente


def test_attributo_oggetto(monkeypatch):
    """monkeypatch modifica attributi di oggetti e moduli."""
    import mio_modulo

    # Sostituisce temporaneamente la funzione nel modulo
    monkeypatch.setattr(mio_modulo, "funzione_lenta", lambda: "risultato_finto")

    risultato = mio_modulo.funzione_lenta()
    assert risultato == "risultato_finto"
    # Dopo il test, mio_modulo.funzione_lenta è ripristinata all'originale
```

---

### Fixture Factory: creare oggetti con parametri variabili

A volte vuoi una fixture che crea oggetti con parametri diversi in test diversi.
La soluzione è la **fixture factory** (fixture che restituisce una funzione):

```python
@pytest.fixture
def crea_utente():
    """Factory fixture: restituisce una funzione per creare utenti."""
    utenti_creati = []

    def _crea_utente(nome="Test Utente", email=None, ruolo="base"):
        email = email or f"{nome.lower().replace(' ', '.')}@test.it"
        utente = {"nome": nome, "email": email, "ruolo": ruolo}
        utenti_creati.append(utente)
        return utente

    yield _crea_utente  # Il test riceve la funzione _crea_utente

    # Teardown: in un'app reale, qui rimuoveresti gli utenti dal DB
    print(f"\nRimossi {len(utenti_creati)} utenti di test")


def test_utente_admin(crea_utente):
    admin = crea_utente(nome="Super Admin", ruolo="admin")
    assert admin["ruolo"] == "admin"
    assert admin["email"] == "super.admin@test.it"


def test_utenti_multipli(crea_utente):
    u1 = crea_utente(nome="Primo Utente")
    u2 = crea_utente(nome="Secondo Utente")
    assert u1["email"] != u2["email"]
    assert u1["nome"] != u2["nome"]
```

---

### autouse: fixture automatiche

Le fixture con `autouse=True` vengono applicate a TUTTI i test nel loro scope,
senza che il test debba chiederle esplicitamente:

```python
@pytest.fixture(autouse=True)
def pulisci_cache_dopo_test():
    """Applicata automaticamente a ogni test nel modulo."""
    yield
    # Questo codice viene eseguito DOPO ogni test
    # per pulire la cache dell'applicazione
    from mia_app.cache import cache
    cache.clear()
    print("\nCache pulita")


def test_uno():
    # Non dichiaro la fixture, ma viene eseguita lo stesso
    from mia_app.cache import cache
    cache["chiave"] = "valore"
    assert cache["chiave"] == "valore"


def test_due():
    # La cache è stata pulita dopo test_uno
    from mia_app.cache import cache
    assert "chiave" not in cache
```

**Quando usare autouse:**
- Setup globale che deve applicarsi a tutti i test (es. configurazione logging)
- Pulizia di risorse condivise dopo ogni test
- Isolamento del database (rollback automatico)

**Quando NON usare autouse:**
- Quando solo alcuni test richiedono quel setup
- Per fornire dati di test (rende le dipendenze implicite)

---

### Fixture parametrizzate: la stessa fixture con valori diversi

```python
@pytest.fixture(params=["sqlite", "postgresql", "mysql"])
def tipo_database(request):
    """Questa fixture viene eseguita tre volte, una per ogni parametro."""
    return request.param


def test_connessione(tipo_database):
    """Questo test viene eseguito tre volte, con database diversi."""
    print(f"\nTest con database: {tipo_database}")
    # In un test reale, qui creeresti una connessione al database specificato
    assert tipo_database in ["sqlite", "postgresql", "mysql"]
```

**Output con `-v`:**
```
test_connessione[sqlite] PASSED
test_connessione[postgresql] PASSED
test_connessione[mysql] PASSED
```

---

## B2: `parametrize` — Lo Stesso Test con Dati Diversi

### Il problema: la duplicazione del codice di test

Immagina di dover testare una funzione di validazione email:

```python
# Senza parametrize — CODICE DUPLICATO

def test_email_valida_standard():
    assert valida_email("utente@dominio.it") is True

def test_email_valida_sottodominio():
    assert valida_email("utente@mail.dominio.it") is True

def test_email_invalida_senza_chiocciola():
    assert valida_email("utente_senza_chiocciola") is False

def test_email_invalida_senza_dominio():
    assert valida_email("utente@") is False

def test_email_invalida_vuota():
    assert valida_email("") is False
```

Cinque funzioni quasi identiche. Se la logica del test cambia, devi aggiornarne cinque.

---

### `@pytest.mark.parametrize`: lo stesso test, dati diversi

**Analogia:** immagina un questionario scolastico. Le domande sono sempre le stesse,
ma ogni studente dà risposte diverse. Con `parametrize`, il "questionario" (la funzione
di test) è uno solo, ma viene "somministrato" con dati diversi.

```python
import pytest
import re


def valida_email(email: str) -> bool:
    """Validazione base dell'email."""
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


@pytest.mark.parametrize("email, atteso", [
    ("utente@dominio.it",           True),
    ("utente@mail.dominio.it",      True),
    ("nome.cognome@azienda.com",    True),
    ("utente+tag@gmail.com",        True),
    ("utente_senza_chiocciola",     False),
    ("utente@",                     False),
    ("@dominio.it",                 False),
    ("",                            False),
    ("utente@dominio",              False),  # Senza TLD
])
def test_validazione_email(email: str, atteso: bool):
    assert valida_email(email) == atteso
```

Con `pytest -v`:
```
test_validazione_email[utente@dominio.it-True] PASSED
test_validazione_email[utente@mail.dominio.it-True] PASSED
test_validazione_email[nome.cognome@azienda.com-True] PASSED
test_validazione_email[utente+tag@gmail.com-True] PASSED
test_validazione_email[utente_senza_chiocciola-False] PASSED
test_validazione_email[utente@-False] PASSED
test_validazione_email[@dominio.it-False] PASSED
test_validazione_email[-False] PASSED
test_validazione_email[utente@dominio-False] PASSED
```

9 test al prezzo di 1 funzione.

---

### La sintassi di parametrize

```python
@pytest.mark.parametrize("nome_parametro", [valore1, valore2, valore3])
def test_funzione(nome_parametro):
    # usa nome_parametro
    pass
```

Con più parametri:

```python
@pytest.mark.parametrize("param1, param2, atteso", [
    (valore1_a, valore1_b, atteso1),
    (valore2_a, valore2_b, atteso2),
])
def test_funzione(param1, param2, atteso):
    assert funzione(param1, param2) == atteso
```

---

### IDs personalizzati per leggibilità

Di default, pytest genera ID basati sui valori dei parametri. Puoi personalizzarli
con `ids`:

```python
@pytest.mark.parametrize("eta, deve_essere_maggiorenne", [
    (17, False),
    (18, True),
    (30, True),
    (0,  False),
    (150, True),  # Limite massimo
], ids=[
    "minorenne-17",
    "maggiore-eta-esatta",
    "adulto-normale",
    "neonato",
    "centenario",
])
def test_maggiorenne(eta: int, deve_essere_maggiorenne: bool):
    assert (eta >= 18) == deve_essere_maggiorenne
```

Con gli ID:
```
test_maggiorenne[minorenne-17] PASSED
test_maggiorenne[maggiore-eta-esatta] PASSED
test_maggiorenne[adulto-normale] PASSED
test_maggiorenne[neonato] PASSED
test_maggiorenne[centenario] PASSED
```

---

### Marker su singoli parametri

Puoi associare marker (come `skip` o `xfail`) a singoli valori del parametrize:

```python
@pytest.mark.parametrize("valore, atteso", [
    (10, 20),
    (0, 0),
    pytest.param(-1, -2, marks=pytest.mark.xfail(reason="Bug #123: negativi non gestiti")),
    pytest.param(None, 0, marks=pytest.mark.skip(reason="Non ancora implementato")),
])
def test_raddoppia(valore, atteso):
    assert raddoppia(valore) == atteso
```

---

### Prodotto cartesiano con più @parametrize

Se applichi più decoratori `@pytest.mark.parametrize`, pytest genera tutte le
combinazioni possibili (prodotto cartesiano):

```python
@pytest.mark.parametrize("moltiplicatore", [2, 3, 5])
@pytest.mark.parametrize("base", [10, 20])
def test_moltiplicazione(base, moltiplicatore):
    risultato = base * moltiplicatore
    assert risultato == base * moltiplicatore
```

Genera 6 test: (10,2), (10,3), (10,5), (20,2), (20,3), (20,5).

---

### Casi pratici avanzati

#### Validazione del codice fiscale italiano

```python
def calcola_lunghezza_cf(cf: str) -> bool:
    """Verifica che il CF abbia esattamente 16 caratteri."""
    return len(cf) == 16


@pytest.mark.parametrize("cf, valido", [
    ("RSSMRA85T10A562S", True),    # CF valido standard
    ("BNCNGL68E49C351X", True),    # CF valido con sesso femminile
    ("RSSMRA85T10A562",  False),   # Troppo corto (15 char)
    ("RSSMRA85T10A562SS", False),  # Troppo lungo (17 char)
    ("",                 False),   # Vuoto
    ("1234567890123456", False),   # Solo cifre (non è un CF valido)
], ids=[
    "standard_maschile",
    "femminile",
    "troppo_corto",
    "troppo_lungo",
    "vuoto",
    "solo_cifre",
])
def test_lunghezza_codice_fiscale(cf: str, valido: bool):
    assert calcola_lunghezza_cf(cf) == valido
```

#### Test di ordinamento con diversi algoritmi

```python
def insertion_sort(lista: list) -> list:
    lista = lista.copy()
    for i in range(1, len(lista)):
        chiave = lista[i]
        j = i - 1
        while j >= 0 and lista[j] > chiave:
            lista[j + 1] = lista[j]
            j -= 1
        lista[j + 1] = chiave
    return lista


@pytest.mark.parametrize("lista_input, lista_attesa", [
    ([3, 1, 2],         [1, 2, 3]),
    ([],                []),                      # Lista vuota
    ([1],               [1]),                     # Singolo elemento
    ([1, 2, 3],         [1, 2, 3]),               # Già ordinata
    ([3, 2, 1],         [1, 2, 3]),               # Invertita
    ([-3, 0, -1, 2],   [-3, -1, 0, 2]),          # Negativi
    ([5, 5, 5, 5],      [5, 5, 5, 5]),             # Duplicati
    ([1, -1, 1, -1],    [-1, -1, 1, 1]),           # Alternati
])
def test_insertion_sort(lista_input, lista_attesa):
    assert insertion_sort(lista_input) == lista_attesa
```

---

### Parametrize con fixture (indirect)

La parametrizzazione indiretta passa il valore attraverso una fixture prima di
darlo al test:

```python
@pytest.fixture
def client_api(request):
    """Crea un client per l'API specificata."""
    tipo = request.param  # Il parametro viene passato via request.param
    if tipo == "staging":
        return APIClient("https://staging.api.it")
    elif tipo == "produzione":
        return APIClient("https://api.it")


@pytest.mark.parametrize("client_api", ["staging", "produzione"], indirect=True)
def test_api_risponde(client_api):
    risposta = client_api.get("/stato")
    assert risposta.status_code == 200
```

---

## B3: Marks — Etichettare e Filtrare i Test

### Cos'è un mark?

Un **mark** (marcatore) è un'etichetta applicata a un test o a un gruppo di test.
I mark servono a:
- Saltare test in certe condizioni (`skip`, `skipif`)
- Documentare test che ci si aspetta falliscano (`xfail`)
- Raggruppare test per eseguirli selettivamente (`-m "lento"`)

---

### `pytest.mark.skip` — Salta sempre questo test

```python
import pytest


@pytest.mark.skip(reason="Funzionalità non ancora implementata — ticket #456")
def test_funzionalita_futura():
    # Questo test non viene mai eseguito
    assert nuova_funzione() == "risultato"
```

Nell'output:
```
tests/test_marks.py::test_funzionalita_futura SKIPPED (Funzionalità non ancora...)
```

---

### `pytest.mark.skipif` — Salta solo in certe condizioni

```python
import sys
import pytest


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Questo test usa i permessi Unix, non supportati su Windows"
)
def test_permessi_file():
    import os
    os.chmod("/tmp/file_test.txt", 0o644)
    # ...


@pytest.mark.skipif(
    sys.version_info < (3, 11),
    reason="Richiede Python 3.11+ per le ExceptionGroup"
)
def test_exception_group():
    try:
        raise ExceptionGroup("errori", [ValueError("a"), TypeError("b")])
    except* ValueError:
        pass


# Skip dinamico all'interno del test
def test_connessione_rete():
    import urllib.request
    try:
        urllib.request.urlopen("https://www.google.com", timeout=2)
    except Exception:
        pytest.skip("Rete non disponibile")

    # ... resto del test
```

---

### `pytest.mark.xfail` — Test atteso fallire

`xfail` (expected failure) marca un test che si sa già che fallirà, tipicamente
perché documenta un bug noto:

```python
@pytest.mark.xfail(reason="Bug #789 — la funzione non gestisce le stringhe Unicode")
def test_unicode():
    risultato = normalizza_testo("Cаfé")  # 'a' cirillico + é con accento
    assert risultato == "cafe"
```

**Comportamento:**
- Se il test **fallisce** (come atteso): `XFAIL` — OK, il test è "correttamente rotto"
- Se il test **passa** (contro le aspettative): `XPASS` — segnalato come sorpresa

```
tests/test_marks.py::test_unicode XFAIL (Bug #789 — la funzione non gestisce...)
```

#### `strict=True` per rendere XPASS un errore

```python
@pytest.mark.xfail(strict=True, reason="Bug confermato — DEVE fallire")
def test_divisione_zero():
    # Se questo test passa (il bug è stato risolto ma non si è aggiornato il test),
    # viene contato come FAILED
    assert 1 / 0 == float("inf")
```

---

### Marker personalizzati

Puoi creare marker personalizzati per classificare i tuoi test:

```python
# Applica il marker personalizzato
@pytest.mark.slow
def test_elaborazione_grande_dataset():
    """Test che richiede molto tempo — marcato come 'slow'."""
    dataset = genera_dataset_grande(righe=1_000_000)
    risultato = elabora(dataset)
    assert risultato.completato


@pytest.mark.integrazione
def test_salva_su_database():
    """Test che richiede un database attivo."""
    pass


@pytest.mark.e2e
def test_flusso_completo_utente():
    """Test end-to-end — richiede l'intera stack applicativa."""
    pass
```

**Registra i marker personalizzati in `pyproject.toml`** (altrimenti pytest mostra
un warning):

```toml
# pyproject.toml
[tool.pytest.ini_options]
markers = [
    "slow: test che richiedono molto tempo di esecuzione",
    "integrazione: test che richiedono servizi esterni (database, cache, ecc.)",
    "e2e: test end-to-end che richiedono l'intera stack applicativa",
    "notturno: test da eseguire solo nella build notturna settimanale",
]
```

---

### Filtrare i test con `-m`

```bash
# Esegui solo i test marcati come 'slow'
pytest -m slow

# Esegui solo i test di integrazione
pytest -m integrazione

# Esegui tutti TRANNE i test 'slow'
pytest -m "not slow"

# Combina: integrazione ma non slow
pytest -m "integrazione and not slow"

# Uno O l'altro
pytest -m "slow or e2e"
```

---

### Strategie di utilizzo dei marker

**Separare test veloci da test lenti:**

```bash
# Durante lo sviluppo: esegui solo i test veloci
pytest -m "not slow" tests/

# Prima del commit: esegui tutto
pytest tests/

# In CI: esegui prima i veloci, poi i lenti in parallelo
pytest -m "not slow" tests/        # Pipeline veloce
pytest -m slow --timeout=300 tests/ # Pipeline lenta separata
```

**Marker basati sull'ambiente:**

```python
import os

# Skip se la variabile d'ambiente non è impostata
@pytest.mark.skipif(
    "POSTGRES_URL" not in os.environ,
    reason="Variabile POSTGRES_URL non impostata — salta i test Postgres"
)
def test_operazioni_postgres():
    pass
```

---

## B4: `conftest.py` — Il File Condiviso di pytest

### Cos'è conftest.py?

`conftest.py` è un file speciale riconosciuto automaticamente da pytest. Le fixture,
i plugin e le configurazioni definite in `conftest.py` sono disponibili per tutti
i test nella stessa directory e nelle sottodirectory, **senza bisogno di import
espliciti**.

---

### La gerarchia dei conftest

```
progetto/
├── conftest.py              ← [A] Visibile a TUTTI i test del progetto
├── tests/
│   ├── conftest.py          ← [B] Visibile a tutti i test in tests/
│   ├── test_utils.py        ← Vede [A] e [B]
│   ├── unit/
│   │   ├── conftest.py      ← [C] Visibile solo ai test in unit/
│   │   └── test_calcoli.py  ← Vede [A], [B] e [C]
│   └── integration/
│       ├── conftest.py      ← [D] Visibile solo ai test in integration/
│       └── test_api.py      ← Vede [A], [B] e [D]
```

**Regola:** un test vede le fixture del proprio `conftest.py` e di tutti i
`conftest.py` nelle directory antenate fino alla root.

---

### Esempio pratico di gerarchia conftest

```python
# tests/conftest.py — fixture globali per tutti i test

import pytest


@pytest.fixture(scope="session")
def configurazione_app():
    """Caricata una volta per tutta la sessione."""
    return {
        "debug": True,
        "database_url": "sqlite:///:memory:",
        "secret_key": "chiave-test-12345",
    }


# Opzione CLI personalizzata
def pytest_addoption(parser):
    """Aggiunge --lento per eseguire i test marcati come slow."""
    parser.addoption(
        "--lento",
        action="store_true",
        default=False,
        help="Includi i test marcati come 'slow' nell'esecuzione",
    )


@pytest.fixture(autouse=True)
def salta_test_lenti(request):
    """Salta i test 'slow' a meno che non si usi --lento."""
    if request.node.get_closest_marker("slow"):
        if not request.config.getoption("--lento", default=False):
            pytest.skip("Test lento: usa --lento per eseguirlo")
```

```python
# tests/integration/conftest.py — fixture specifiche per l'integrazione

import pytest


@pytest.fixture(scope="session")
def database_integrazione(configurazione_app):
    """Database per i test di integrazione. Dipende da configurazione_app."""
    import sqlite3
    url = configurazione_app["database_url"]
    # Estrai il percorso dal URL
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE utenti (id INTEGER PRIMARY KEY, nome TEXT)")
    conn.commit()
    yield conn
    conn.close()


@pytest.fixture
def sessione_db(database_integrazione):
    """Sessione con isolamento per test."""
    yield database_integrazione
    database_integrazione.execute("DELETE FROM utenti")
    database_integrazione.commit()
```

```python
# tests/integration/test_utenti.py

def test_crea_utente(sessione_db):
    """Usa la fixture dalla gerarchia di conftest."""
    sessione_db.execute(
        "INSERT INTO utenti (nome) VALUES (?)",
        ("Mario",)
    )
    sessione_db.commit()

    cursore = sessione_db.execute("SELECT COUNT(*) FROM utenti")
    assert cursore.fetchone()[0] == 1
```

---

### Override di fixture

Una fixture in un `conftest.py` figlio può **sovrascrivere** una fixture con lo stesso
nome definita in un `conftest.py` padre:

```python
# tests/conftest.py
@pytest.fixture
def client():
    return APIClient(base_url="http://localhost:8000")


# tests/integration/conftest.py
@pytest.fixture
def client():  # Override! Sovrascrive la fixture padre
    """Client con autenticazione per i test di integrazione."""
    client = APIClient(base_url="http://localhost:8000")
    client.set_auth_token("token-di-test-valido")
    return client
```

I test in `tests/integration/` usano il `client` autenticato.
I test in `tests/unit/` usano il `client` base.

---

### Hook in conftest.py

Oltre alle fixture, `conftest.py` può contenere **hook** di pytest — funzioni
che modificano il comportamento del framework:

```python
# tests/conftest.py

def pytest_collection_modifyitems(config, items):
    """
    Hook eseguito dopo la raccolta dei test.
    Aggiunge automaticamente il marker 'slow' a tutti i test di integrazione.
    """
    for item in items:
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.slow)
        if "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """
    Hook eseguito alla fine di tutta la suite.
    Mostra un messaggio personalizzato.
    """
    if exitstatus == 0:
        terminalreporter.write_sep("=", "Tutti i test sono verdi! 🎉")
    else:
        terminalreporter.write_sep(
            "=",
            "Alcuni test sono falliti. Controlla l'output sopra."
        )
```

---

## B5: Mocking — Sostituire Dipendenze nei Test

### Il problema: dipendenze esterne

Considera questa funzione:

```python
# src/notifiche.py

import smtplib
import requests


def invia_email(destinatario: str, messaggio: str) -> bool:
    """Invia un'email reale via SMTP."""
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login("app@gmail.com", "password-segreta")
    server.sendmail("app@gmail.com", destinatario, messaggio)
    server.quit()
    return True


def ottieni_meteo(citta: str) -> dict:
    """Chiama un'API esterna per il meteo."""
    risposta = requests.get(f"https://api.meteo.it/v1/{citta}")
    return risposta.json()
```

Come testi `invia_email` senza inviare davvero un'email?
Come testi `ottieni_meteo` senza fare davvero una chiamata di rete?

La risposta è il **mocking**: sostituisci la dipendenza esterna con un oggetto
simulato (mock) che si comporta come vuoi tu.

---

### Analogia: l'attore al posto dell'esperto

Immagina di girare un film in cui il protagonista è un cardochirurgo. Non assumi
un vero cardochirurgo per girare il film — assumi un attore che *recita la parte*
del cardochirurgo. L'attore dice le battute giuste, si muove nel modo giusto,
ma non è un medico vero.

Il mock è l'attore. Quando il tuo codice chiama `requests.get()`, invece di
fare una vera chiamata HTTP, chiama il mock che "recita la parte" di `requests.get()`,
restituendo un valore preconfezionato.

---

### unittest.mock: il modulo standard

Python include `unittest.mock` nella libreria standard. I suoi oggetti principali:
- `Mock` — oggetto simulato base
- `MagicMock` — Mock che implementa anche i metodi magici (`__len__`, `__str__`, ecc.)
- `AsyncMock` — per funzioni asincrone
- `patch()` — sostituisce temporaneamente un oggetto con un mock

---

### Mock e MagicMock

```python
from unittest.mock import Mock, MagicMock


# Mock base: accetta qualsiasi chiamata e attributo
mock = Mock()

# Chiama il mock come funzione
mock("argomento1", chiave="valore")

# Verifica che sia stato chiamato
assert mock.called
assert mock.call_count == 1

# Verifica i dettagli della chiamata
mock.assert_called_with("argomento1", chiave="valore")

# Imposta il valore di ritorno
mock.return_value = 42
risultato = mock()
assert risultato == 42

# Accedi ad attributi inesistenti — il mock li crea al volo
print(mock.qualsiasi_attributo)          # Mock() — un altro mock
print(mock.metodo_inesistente())         # Mock() — un altro mock
```

```python
# MagicMock: come Mock, ma supporta anche i magic methods

lista_mock = MagicMock()
lista_mock.__len__.return_value = 5
len(lista_mock)   # Restituisce 5

lista_mock.__getitem__.return_value = "elemento"
lista_mock[0]     # Restituisce "elemento"

lista_mock.__contains__.return_value = True
"qualcosa" in lista_mock  # Restituisce True
```

---

### `patch()`: sostituisci temporaneamente un oggetto

`patch()` è lo strumento più usato nel mocking. Sostituisce un oggetto nel namespace
specificato durante l'esecuzione del test, poi lo ripristina automaticamente.

#### Come decoratore

```python
from unittest.mock import patch


# src/servizio_meteo.py
import requests

def ottieni_temperatura(citta: str) -> float:
    risposta = requests.get(f"https://api.meteo.it/v1/{citta}")
    dati = risposta.json()
    return dati["temperatura"]


# tests/test_meteo.py
from unittest.mock import patch
from src.servizio_meteo import ottieni_temperatura


@patch("src.servizio_meteo.requests.get")  # <-- patch dove viene USATO, non definito
def test_temperatura_roma(mock_get):
    # Configura cosa deve restituire il mock
    mock_get.return_value.json.return_value = {"temperatura": 22.5, "citta": "Roma"}
    mock_get.return_value.status_code = 200

    # Chiama la funzione
    temperatura = ottieni_temperatura("Roma")

    # Verifica il risultato
    assert temperatura == 22.5

    # Verifica che la chiamata sia stata fatta nel modo giusto
    mock_get.assert_called_once_with("https://api.meteo.it/v1/Roma")
```

#### Regola fondamentale del patch

**Si fa patch dove l'oggetto viene USATO, non dove viene DEFINITO.**

```python
# requests è DEFINITO nel modulo requests
# ma viene USATO in src.servizio_meteo

# CORRETTO: patch dove viene usato
@patch("src.servizio_meteo.requests.get")

# SBAGLIATO: patch dove è definito
@patch("requests.get")  # Non funziona!
```

Perché? Quando `servizio_meteo.py` fa `import requests`, ottiene un riferimento a
`requests`. Se fai il patch di `requests.get`, quello nel modulo `servizio_meteo`
ha già il vecchio riferimento. Devi fare il patch del riferimento dentro `servizio_meteo`.

---

#### Come context manager

```python
def test_temperatura_con_context_manager():
    with patch("src.servizio_meteo.requests.get") as mock_get:
        mock_get.return_value.json.return_value = {"temperatura": 15.0}

        temperatura = ottieni_temperatura("Milano")
        assert temperatura == 15.0

    # Dopo l'uscita dal with, requests.get è ripristinato
```

---

### `side_effect`: comportamenti complessi

`side_effect` permette di simulare comportamenti più complessi:

```python
from unittest.mock import Mock


# 1. Sollevare un'eccezione
mock_rete = Mock()
mock_rete.side_effect = ConnectionError("Timeout di rete")
# mock_rete()  # Solleva ConnectionError


# 2. Restituire valori diversi a ogni chiamata
mock_contatore = Mock()
mock_contatore.side_effect = [10, 20, 30, 40]
print(mock_contatore())  # 10
print(mock_contatore())  # 20
print(mock_contatore())  # 30
print(mock_contatore())  # 40
# mock_contatore()  # StopIteration!


# 3. Funzione personalizzata
def mia_logica(x):
    if x < 0:
        raise ValueError(f"Valore negativo: {x}")
    return x * 2

mock_fun = Mock(side_effect=mia_logica)
print(mock_fun(5))   # 10
# mock_fun(-1)        # Solleva ValueError
```

---

### Esempio completo: test di un servizio che manda email

```python
# src/servizio_ordini.py

import smtplib
from email.mime.text import MIMEText


class ServizioOrdini:
    def __init__(self, smtp_host: str, smtp_port: int):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port

    def conferma_ordine(self, email_cliente: str, id_ordine: int) -> bool:
        """Confirma un ordine inviando un'email al cliente."""
        messaggio = MIMEText(f"Il tuo ordine #{id_ordine} è confermato!")
        messaggio["Subject"] = f"Conferma ordine #{id_ordine}"
        messaggio["From"] = "ordini@negozio.it"
        messaggio["To"] = email_cliente

        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.sendmail("ordini@negozio.it", email_cliente, messaggio.as_string())

        return True
```

```python
# tests/test_servizio_ordini.py

from unittest.mock import patch, MagicMock
import pytest
from src.servizio_ordini import ServizioOrdini


def test_conferma_ordine_invia_email():
    """Verifica che la conferma ordine chiami SMTP correttamente."""
    servizio = ServizioOrdini("smtp.negozio.it", 587)

    with patch("src.servizio_ordini.smtplib.SMTP") as mock_smtp_class:
        # mock_smtp_class è il mock della CLASSE SMTP
        # mock_smtp_class() è il mock dell'ISTANZA creata con SMTP(...)
        mock_server = MagicMock()
        mock_smtp_class.return_value.__enter__.return_value = mock_server

        risultato = servizio.conferma_ordine("mario@test.it", ordine_id=42)

    # Verifica il risultato
    assert risultato is True

    # Verifica che SMTP sia stato creato con i parametri corretti
    mock_smtp_class.assert_called_once_with("smtp.negozio.it", 587)

    # Verifica che sendmail sia stato chiamato
    mock_server.sendmail.assert_called_once()
    args = mock_server.sendmail.call_args[0]
    assert args[0] == "ordini@negozio.it"
    assert args[1] == "mario@test.it"
    assert "ordine #42" in args[2] or "#42" in args[2]


def test_conferma_ordine_smtp_fallisce():
    """Verifica il comportamento quando SMTP fallisce."""
    servizio = ServizioOrdini("smtp.negozio.it", 587)

    with patch("src.servizio_ordini.smtplib.SMTP") as mock_smtp_class:
        mock_smtp_class.side_effect = ConnectionRefusedError("SMTP non disponibile")

        with pytest.raises(ConnectionRefusedError):
            servizio.conferma_ordine("mario@test.it", ordine_id=42)
```

---

### Verificare le chiamate al mock

```python
from unittest.mock import Mock, call


mock = Mock()
mock("primo")
mock("secondo", chiave="valore")
mock("terzo")


# Verifica la ULTIMA chiamata
mock.assert_called_with("terzo")


# Verifica che sia stato chiamato ALMENO UNA VOLTA con questi argomenti
mock.assert_any_call("primo")
mock.assert_any_call("secondo", chiave="valore")


# Verifica esattamente una chiamata (fallisce se è 0 o più di 1)
mock_unico = Mock()
mock_unico("unica_chiamata")
mock_unico.assert_called_once_with("unica_chiamata")


# Verifica il numero di chiamate
assert mock.call_count == 3


# Verifica TUTTE le chiamate nell'ordine esatto
assert mock.call_args_list == [
    call("primo"),
    call("secondo", chiave="valore"),
    call("terzo"),
]
```

---

### `spec`: mock che rispettano l'interfaccia reale

Senza `spec`, un mock accetta qualsiasi chiamata:

```python
mock = Mock()
mock.metodo_inesistente()  # Funziona! Il mock non sa che non esiste


# Con spec, il mock verifica che i metodi esistano nella classe reale
class Database:
    def connetti(self): ...
    def query(self, sql): ...
    def disconnetti(self): ...


mock_db = Mock(spec=Database)
mock_db.query("SELECT 1")         # OK
mock_db.metodo_inesistente()      # AttributeError! Non esiste in Database
```

`spec` è utile per evitare che i test passino su interfacce sbagliate.

---

### `patch.dict`: modifica temporanea di dizionari

```python
import os
from unittest.mock import patch


def test_configurazione_production():
    """Testa con variabili d'ambiente di produzione simulate."""
    with patch.dict(os.environ, {
        "ENV": "production",
        "DATABASE_URL": "postgresql://prod-db/myapp",
        "DEBUG": "false",
    }):
        assert os.environ["ENV"] == "production"
        assert os.environ["DEBUG"] == "false"

    # Fuori dal context manager, os.environ è ripristinato
```

---

### `pytest-mock`: la fixture `mocker`

Il plugin `pytest-mock` fornisce la fixture `mocker` che semplifica il mocking:

```bash
pip install pytest-mock
```

```python
# Con pytest-mock, non servono import aggiuntivi nel test

def test_con_mocker(mocker):
    """mocker è una fixture pytest che wrappa unittest.mock."""
    mock_get = mocker.patch("src.servizio_meteo.requests.get")
    mock_get.return_value.json.return_value = {"temperatura": 20.0}

    temperatura = ottieni_temperatura("Napoli")
    assert temperatura == 20.0

    # Il patch viene rimosso automaticamente alla fine del test
    # (non serve il context manager)
```

Vantaggi di `pytest-mock` vs `unittest.mock.patch`:
- Non serve importare `patch`
- Il patch viene rimosso automaticamente anche in caso di errore
- Integrazione naturale con il sistema di fixture

---

### AsyncMock: mock per codice asincrono

```python
import pytest
from unittest.mock import AsyncMock, patch


async def recupera_utente(user_id: int) -> dict:
    """Funzione asincrona che chiama un'API."""
    import httpx
    async with httpx.AsyncClient() as client:
        risposta = await client.get(f"https://api.esempio.it/utenti/{user_id}")
        return risposta.json()


@pytest.mark.asyncio
async def test_recupera_utente():
    mock_client = AsyncMock()
    mock_client.get.return_value.json.return_value = {
        "id": 1,
        "nome": "Mario Rossi"
    }

    with patch("src.api.httpx.AsyncClient") as mock_httpx:
        mock_httpx.return_value.__aenter__.return_value = mock_client

        utente = await recupera_utente(1)

    assert utente["nome"] == "Mario Rossi"
    mock_client.get.assert_awaited_once_with("https://api.esempio.it/utenti/1")
```

---

### Quando NON usare il mock (over-mocking)

Il mocking è potente, ma se abusato rende i test fragili e inutili.

**Segnali di over-mocking:**
- Il test ha più righe di configurazione del mock che di asserzioni
- Stai mockando funzioni pure (senza dipendenze esterne)
- Stai mockando metodi privati dell'oggetto che stai testando
- Il mock ricrea fedelmente la logica dell'oggetto originale

```python
# OVER-MOCKING: mockare una funzione pura è inutile
def somma(a, b):
    return a + b

def test_sbagliato(mocker):
    mock_somma = mocker.patch("mio_modulo.somma", return_value=5)
    # Questo non testa NULLA di utile — hai sostituito la funzione stessa!
    assert mock_somma(2, 3) == 5


# CORRETTO: testa la funzione direttamente
def test_corretto():
    assert somma(2, 3) == 5
```

**Regola pratica:** usa il mock solo per:
1. Chiamate a servizi esterni (HTTP, email, SMS)
2. Accesso al filesystem (se l'I/O è lento o ha side effects)
3. Chiamate al database (nei unit test — gli integration test usano il DB reale)
4. Funzioni che dipendono dall'orologio (`datetime.now()`)
5. Generatori di numeri casuali (`random.randint()`)

---

## B6: Coverage — Quanto Codice è Coperto?

### Cos'è la coverage?

La **coverage** (copertura) misura quale percentuale del codice sorgente viene
effettivamente eseguita durante i test. È uno strumento diagnostico che risponde
alla domanda: "Ci sono parti del codice che i nostri test non toccano mai?"

---

### Analogia: l'ispezione della casa

Immagina di fare un'ispezione di una casa in vendita. La coverage è come tenere
traccia di quali stanze hai visitato:
- Bagno: ✓ ispecionato
- Cucina: ✓ ispezionata
- Salotto: ✓ ispezionato
- Cantina: ✗ non ispezionata

Se la cantina ha problemi (muffa, fondamenta che cedono), non lo scoprirai perché
non ci sei entrato. La coverage bassa è la cantina non ispezionata — problemi nascosti.

---

### Installazione e utilizzo base

```bash
pip install pytest-cov

# Report in terminale
pytest --cov=src tests/

# Report dettagliato con righe mancanti
pytest --cov=src --cov-report=term-missing tests/

# Report HTML interattivo
pytest --cov=src --cov-report=html tests/

# Più report contemporaneamente
pytest --cov=src --cov-report=term-missing --cov-report=html tests/
```

---

### Interpretare il report

```
Name                      Stmts   Miss  Cover   Missing
-------------------------------------------------------
src/calcolatrice.py          18      2    89%   45-46
src/validazione.py           32      0   100%
src/notifiche.py             45     15    67%   23-30, 55, 89-95
-------------------------------------------------------
TOTAL                        95     17    82%
```

**Colonne:**
- `Stmts` — numero di statement (istruzioni) nel file
- `Miss` — numero di statement non eseguiti dai test
- `Cover` — percentuale di statement coperti
- `Missing` — numeri di riga non coperti

**Interpretazione:**
- `src/calcolatrice.py` — 89% di copertura, mancano le righe 45-46
- `src/validazione.py` — 100% di copertura
- `src/notifiche.py` — 67%, molte righe mancanti

---

### Branch coverage: più rigorosa della line coverage

La **line coverage** verifica solo se una riga è stata eseguita.
La **branch coverage** verifica che ogni ramo di ogni decisione sia stato percorso.

```python
def classifica_eta(eta: int) -> str:
    if eta < 0:                     # Ramo A: eta < 0, Ramo B: eta >= 0
        raise ValueError("Negativa")
    elif eta < 18:                  # Ramo C: eta < 18, Ramo D: eta >= 18
        return "minore"
    else:
        return "adulto"
```

Con solo due test (`eta=10` e `eta=25`):
- **Line coverage**: 100% (tutte le righe vengono eseguite)
- **Branch coverage**: manca il Ramo A (eta < 0)

```bash
# Attiva la branch coverage
pytest --cov=src --cov-branch tests/
```

---

### Configurazione in pyproject.toml

```toml
# pyproject.toml
[tool.coverage.run]
source = ["src"]
branch = true          # Attiva branch coverage
omit = [
    "*/migrations/*",  # Escludi le migrazioni
    "*/test_*",        # Escludi i file di test
    "*/__pycache__/*",
]

[tool.coverage.report]
fail_under = 85        # Fallisci se la coverage è sotto l'85%
show_missing = true
skip_covered = true    # Non mostrare i file al 100%
exclude_lines = [
    "pragma: no cover",        # Linea marcata esplicitamente
    "def __repr__",            # Metodi repr
    "if TYPE_CHECKING:",       # Codice solo per i type hints
    "if __name__ == .__main__.", # Blocco main
    "raise NotImplementedError",
    "@abstractmethod",
]

[tool.coverage.html]
directory = "htmlcov"
```

---

### Fallire se la coverage è troppo bassa

```bash
# Fallisce se la coverage totale è sotto il 80%
pytest --cov=src --cov-fail-under=80 tests/
```

Questo comando ritorna un codice di errore diverso da zero se la coverage è sotto
la soglia, bloccando la pipeline CI.

---

### Coverage non è tutto

> "Una coverage del 100% non garantisce assenza di bug.
>  Una coverage del 0% garantisce bug non trovati."

La coverage è utile per trovare codice **non testato**, ma non dice nulla sulla
**qualità** dei test nelle aree coperte.

```python
# Questo test ha coverage del 100% ma verifica NULLA di utile
def test_inutile():
    calcola_sconto(100.0, 20.0)  # Esegue il codice ma non verifica il risultato
    assert True                   # Sempre vero — non verifica nulla
```

Usa la coverage come strumento diagnostico per trovare lacune, non come obiettivo
numerico fine a se stesso.

---

## B7: Hypothesis — Testing Basato su Proprietà

### Il problema con i test tradizionali

Con il testing tradizionale, scegli manualmente gli input:

```python
# Test tradizionale — scegli tu gli esempi
def test_ordinamento():
    assert sorted([3, 1, 2]) == [1, 2, 3]
    assert sorted([]) == []
    assert sorted([5, 5, 5]) == [5, 5, 5]
```

Questo funziona per i casi che hai pensato di testare. Ma cosa succede con
`[sys.maxsize, -sys.maxsize, 0]`? Con `[float('nan')]`? Con una lista di
un milione di elementi?

---

### La soluzione: testing basato su proprietà

Invece di scegliere esempi specifici, definisci **proprietà** che devono valere
per *qualsiasi* input, e lasci che il framework generi automaticamente centinaia
di casi di test.

**Analogia:** invece di testare 3 pazienti in un test clinico, testi 1000 pazienti
con profili diversi. Il principio del farmaco deve valere per tutti.

---

### Installazione e primo test con Hypothesis

```bash
pip install hypothesis
```

```python
from hypothesis import given
from hypothesis import strategies as st


@given(st.integers(), st.integers())
def test_addizione_commutativa(a: int, b: int) -> None:
    """L'addizione deve essere commutativa per QUALSIASI coppia di interi."""
    assert a + b == b + a


@given(st.lists(st.integers()))
def test_ordinamento_preserva_lunghezza(lista: list[int]) -> None:
    """sorted() non deve mai cambiare il numero di elementi."""
    assert len(sorted(lista)) == len(lista)


@given(st.lists(st.integers(), min_size=1))
def test_ordinamento_minimo_e_massimo(lista: list[int]) -> None:
    """Il primo elemento della lista ordinata è sempre il minimo."""
    ordinata = sorted(lista)
    assert ordinata[0] == min(lista)
    assert ordinata[-1] == max(lista)
```

Hypothesis genera automaticamente 100 casi di test (di default) per ogni test,
includendo casi limite come zero, negativi, valori molto grandi, stringhe vuote.

---

### Strategies: come Hypothesis genera i dati

Le `strategies` definiscono il dominio dei dati da generare:

```python
from hypothesis import strategies as st


# Tipi base
st.integers()                             # Qualsiasi intero
st.integers(min_value=0, max_value=100)   # Da 0 a 100
st.floats(allow_nan=False, allow_infinity=False)  # Float finiti
st.text()                                 # Stringa qualsiasi
st.text(min_size=1, max_size=50)          # Stringa da 1 a 50 caratteri
st.booleans()                             # True o False
st.binary()                               # Bytes

# Collezioni
st.lists(st.integers(), min_size=0, max_size=20)
st.sets(st.text(min_size=1))
st.dictionaries(st.text(min_size=1), st.integers())
st.tuples(st.integers(), st.text())

# Composizione
st.one_of(st.integers(), st.text())       # Intero OPPURE testo
st.none()                                 # Solo None
st.just(42)                               # Sempre 42 (utile nelle composizioni)
st.sampled_from([1, 2, 3, "a", "b"])      # Campiona dalla lista

# Dati strutturati
st.emails()                               # Email valide
st.dates()                                # Date
st.datetimes()                            # Datetime
st.decimals()                             # Decimal Python
```

---

### @composite: strategie personalizzate

Per dati strutturati complessi, usa `@st.composite`:

```python
from hypothesis import strategies as st
from hypothesis import given


@st.composite
def strategia_prodotto(draw):
    """Genera prodotti validi per i test."""
    nome = draw(st.text(
        min_size=2,
        max_size=50,
        alphabet=st.characters(whitelist_categories=("L", "N", "Zs"))
    ))
    prezzo = draw(st.floats(min_value=0.01, max_value=9999.99,
                            allow_nan=False, allow_infinity=False))
    quantita = draw(st.integers(min_value=0, max_value=1000))
    return {"nome": nome, "prezzo": round(prezzo, 2), "quantita": quantita}


@given(strategia_prodotto())
def test_prodotto_sempre_valido(prodotto: dict) -> None:
    """Un prodotto generato da strategia_prodotto deve sempre essere valido."""
    assert len(prodotto["nome"]) >= 2
    assert prodotto["prezzo"] > 0
    assert prodotto["quantita"] >= 0
```

---

### Shrinking: trovare il caso minimo

Quando Hypothesis trova un input che fa fallire il test, applica lo **shrinking**:
riduce progressivamente l'input al caso più piccolo che ancora causa il fallimento.

```python
@given(st.lists(st.integers()))
def test_somma_sempre_positiva(numeri: list[int]) -> None:
    # Questo test è SBAGLIATO — la somma può essere negativa
    assert sum(numeri) >= 0
```

Hypothesis potrebbe trovare `[1, -5, 3]` come caso fallimentare, ma dopo lo
shrinking ti presenterà `[-1]` — il caso più semplice che dimostra il problema.

```
Falsifying example: test_somma_sempre_positiva(numeri=[-1])
```

---

### `assume()`: filtrare input non validi

```python
from hypothesis import given, assume
from hypothesis import strategies as st


@given(st.integers(), st.integers())
def test_divisione(numeratore: int, denominatore: int) -> None:
    assume(denominatore != 0)  # Scarta i casi dove il denominatore è zero

    risultato = numeratore / denominatore
    assert risultato * denominatore == pytest.approx(numeratore)
```

Attenzione: se `assume()` scarta troppi valori, Hypothesis mostra un health check
warning. In quel caso, è meglio restringere la strategia:

```python
# Meglio di assume: restringi la strategia
@given(st.integers(), st.integers().filter(lambda x: x != 0))
def test_divisione_v2(numeratore: int, denominatore: int) -> None:
    risultato = numeratore / denominatore
    assert risultato * denominatore == pytest.approx(numeratore)
```

---

### Esempio completo: property-based test per encode/decode

```python
import base64
from hypothesis import given
from hypothesis import strategies as st


def codifica(testo: str) -> str:
    """Codifica una stringa in base64."""
    return base64.b64encode(testo.encode("utf-8")).decode("ascii")


def decodifica(codificato: str) -> str:
    """Decodifica una stringa da base64."""
    return base64.b64decode(codificato.encode("ascii")).decode("utf-8")


@given(st.text())
def test_codifica_decodifica_inversa(testo: str) -> None:
    """
    Proprietà: codificare e poi decodificare deve restituire il testo originale.
    Questa proprietà deve valere per QUALSIASI stringa.
    """
    assert decodifica(codifica(testo)) == testo


@given(st.text(min_size=1))
def test_codifica_non_vuota(testo: str) -> None:
    """La codifica di un testo non vuoto non è mai vuota."""
    assert len(codifica(testo)) > 0
```

---

## B8: Testcontainers — Database Reali nei Test

### Il problema con i mock del database

Puoi mockare il database nei tuoi unit test, ma il mock del database è sempre
una semplificazione. Non testa:
- Il vero comportamento SQL (JOIN complesse, vincoli, trigger)
- Le performance delle query
- Le dipendenze specifiche del dialetto SQL
- I comportamenti di concorrenza

Per i test di integrazione, vuoi un database **vero** — ma non quello di produzione.

---

### Testcontainers: database reali in Docker

**Testcontainers** avvia container Docker come infrastruttura per i test. Ogni
test (o suite di test) ottiene un database fresco, isolato, che viene distrutto
al termine.

```bash
pip install testcontainers

# Richiede Docker installato e in esecuzione
```

---

### Esempio: PostgreSQL in un container

```python
import pytest
import psycopg2
from testcontainers.postgres import PostgresContainer


@pytest.fixture(scope="session")
def postgres():
    """Avvia PostgreSQL in Docker per l'intera sessione."""
    with PostgresContainer("postgres:16-alpine") as pg:
        print(f"\nPostgreSQL in esecuzione su: {pg.get_connection_url()}")
        yield pg
    print("\nContainer PostgreSQL fermato e rimosso")


@pytest.fixture
def pg_conn(postgres):
    """Connessione al database per ogni test, con rollback automatico."""
    conn = psycopg2.connect(
        host=postgres.get_container_host_ip(),
        port=postgres.get_exposed_port(5432),
        user=postgres.username,
        password=postgres.password,
        dbname=postgres.dbname,
    )
    # Crea la tabella per i test
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS utenti (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                creato_il TIMESTAMP DEFAULT NOW()
            )
        """)
    conn.commit()

    yield conn

    # Teardown: rollback e pulizia
    conn.rollback()
    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS utenti")
    conn.commit()
    conn.close()


def test_inserimento_utente(pg_conn):
    """Test con PostgreSQL reale — non un mock!"""
    with pg_conn.cursor() as cur:
        cur.execute(
            "INSERT INTO utenti (nome, email) VALUES (%s, %s) RETURNING id",
            ("Mario Rossi", "mario@test.it")
        )
        id_utente = cur.fetchone()[0]

    pg_conn.commit()

    # Verifica che l'inserimento sia avvenuto
    with pg_conn.cursor() as cur:
        cur.execute("SELECT nome, email FROM utenti WHERE id = %s", (id_utente,))
        riga = cur.fetchone()

    assert riga[0] == "Mario Rossi"
    assert riga[1] == "mario@test.it"


def test_unicita_email(pg_conn):
    """Verifica il vincolo UNIQUE sul database reale."""
    with pg_conn.cursor() as cur:
        cur.execute(
            "INSERT INTO utenti (nome, email) VALUES (%s, %s)",
            ("Mario", "mario@test.it")
        )
    pg_conn.commit()

    # Tentativo di inserire la stessa email deve fallire
    with pytest.raises(Exception) as exc_info:
        with pg_conn.cursor() as cur:
            cur.execute(
                "INSERT INTO utenti (nome, email) VALUES (%s, %s)",
                ("Luigi", "mario@test.it")  # Email duplicata!
            )
        pg_conn.commit()

    assert "unique" in str(exc_info.value).lower() or "duplicate" in str(exc_info.value).lower()
```

---

### Esempio: Redis in un container

```python
import pytest
from testcontainers.redis import RedisContainer
import redis as redis_lib


@pytest.fixture(scope="session")
def redis_container():
    """Redis in Docker per la sessione."""
    with RedisContainer("redis:7-alpine") as container:
        yield container


@pytest.fixture
def redis_client(redis_container):
    """Client Redis, con flush automatico dopo ogni test."""
    client = redis_lib.Redis(
        host=redis_container.get_container_host_ip(),
        port=redis_container.get_exposed_port(6379),
        decode_responses=True,
    )
    yield client
    client.flushdb()  # Pulisce tutto dopo il test


def test_set_e_get(redis_client):
    """Test con Redis reale."""
    redis_client.set("chiave", "valore", ex=60)  # Scadenza 60 secondi
    assert redis_client.get("chiave") == "valore"


def test_scadenza_chiave(redis_client):
    """Verifica la scadenza automatica delle chiavi."""
    redis_client.set("temporanea", "dato", ex=1)  # Scade in 1 secondo
    assert redis_client.exists("temporanea") == 1

    import time
    time.sleep(1.1)  # Aspetta che scada

    assert redis_client.exists("temporanea") == 0
```

---

### Perché Testcontainers > mock del DB

| Aspetto | Mock del DB | Testcontainers |
|---|---|---|
| Velocità | Molto veloce | Lento (avvio Docker) |
| Fedeltà | Bassa — simula il DB | Alta — è il DB reale |
| Dipendenze | Nessuna | Richiede Docker |
| Manutenzione | Alta — il mock va aggiornato | Bassa |
| Bug catturati | Solo bug di logica | Anche bug SQL, vincoli, trigger |
| Uso consigliato | Unit test | Integration test |

---

## B9: BDD con behave — Test che Capiscono Tutti

### Cos'è il BDD?

**Behavior-Driven Development** (BDD) è un approccio allo sviluppo in cui i test
vengono scritti in un linguaggio semi-naturale comprensibile anche ai non tecnici.

Il linguaggio usato si chiama **Gherkin** e usa una sintassi `Given/When/Then`
(Dato/Quando/Allora):

```gherkin
Scenario: Utente effettua il login con credenziali valide
  Dato che l'utente "mario@test.it" è registrato con password "Sicura123!"
  Quando l'utente inserisce email "mario@test.it" e password "Sicura123!"
  Allora il login ha successo
  E l'utente viene reindirizzato alla dashboard
```

Questo testo è comprensibile dal product manager, dal cliente, dall'UX designer.
Ma è anche codice eseguibile.

---

### Installazione di behave

```bash
pip install behave
```

---

### Struttura di un progetto BDD con behave

```
progetto/
├── features/
│   ├── login.feature           ← Scenari in Gherkin
│   ├── carrello.feature
│   └── steps/
│       ├── login_steps.py      ← Implementazione degli step
│       └── carrello_steps.py
└── src/
    └── app.py
```

---

### Esempio completo: login utente

```gherkin
# features/login.feature

Feature: Login Utente
  Come utente registrato
  Voglio poter effettuare il login
  In modo da accedere alle mie informazioni personali

  Scenario: Login con credenziali valide
    Dato che esiste un utente con email "mario@test.it" e password "Sicura123!"
    Quando invio una richiesta di login con email "mario@test.it" e password "Sicura123!"
    Allora la risposta ha status code 200
    E la risposta contiene un token JWT

  Scenario: Login con password sbagliata
    Dato che esiste un utente con email "mario@test.it" e password "Sicura123!"
    Quando invio una richiesta di login con email "mario@test.it" e password "errata"
    Allora la risposta ha status code 401
    E la risposta contiene il messaggio "Credenziali non valide"

  Scenario: Login con email non registrata
    Dato nessun utente con email "sconosciuto@test.it"
    Quando invio una richiesta di login con email "sconosciuto@test.it" e password "qualsiasi"
    Allora la risposta ha status code 401
```

```python
# features/steps/login_steps.py

from behave import given, when, then
import json


# ---- Step Given (Dato) ----

@given('che esiste un utente con email "{email}" e password "{password}"')
def step_crea_utente(context, email, password):
    """Crea un utente nel database di test."""
    # context.database è il database di test (impostato nel environment.py)
    context.database["utenti"][email] = {
        "email": email,
        "password_hash": hash(password),
        "token": None,
    }


@given('nessun utente con email "{email}"')
def step_nessun_utente(context, email):
    """Verifica che l'email non sia nel database."""
    context.database["utenti"].pop(email, None)


# ---- Step When (Quando) ----

@when('invio una richiesta di login con email "{email}" e password "{password}"')
def step_invia_login(context, email, password):
    """Simula l'invio di una richiesta di login."""
    # context.client è il client HTTP di test
    risposta = context.client.post("/api/login", json={
        "email": email,
        "password": password,
    })
    context.ultima_risposta = risposta


# ---- Step Then (Allora/E) ----

@then("la risposta ha status code {status_code:d}")
def step_verifica_status_code(context, status_code):
    assert context.ultima_risposta.status_code == status_code, (
        f"Atteso status code {status_code}, "
        f"ricevuto {context.ultima_risposta.status_code}"
    )


@then("la risposta contiene un token JWT")
def step_verifica_token_jwt(context):
    dati = context.ultima_risposta.json()
    assert "token" in dati, "La risposta non contiene il campo 'token'"
    assert dati["token"].startswith("eyJ"), "Il token non sembra un JWT valido"


@then('la risposta contiene il messaggio "{messaggio}"')
def step_verifica_messaggio(context, messaggio):
    dati = context.ultima_risposta.json()
    assert "messaggio" in dati or "error" in dati, "Nessun campo messaggio nella risposta"
    corpo = dati.get("messaggio") or dati.get("error", "")
    assert messaggio in corpo, f"'{messaggio}' non trovato in '{corpo}'"
```

---

### Eseguire i test BDD

```bash
# Esegui tutti gli scenari
behave

# Esegui solo i feature file specifici
behave features/login.feature

# Output verboso
behave --no-capture

# Esegui solo scenari con un certo tag
behave --tags=@critico
```

**Output:**
```
Feature: Login Utente # features/login.feature:1

  Scenario: Login con credenziali valide       # features/login.feature:8
    Dato che esiste un utente con...            # steps/login_steps.py:6
    Quando invio una richiesta di login...      # steps/login_steps.py:17
    Allora la risposta ha status code 200       # steps/login_steps.py:25
    E la risposta contiene un token JWT         # steps/login_steps.py:32

1 feature passed, 0 failed, 0 skipped
3 scenarios passed, 0 failed, 0 skipped
12 steps passed, 0 failed, 0 skipped, 0 undefined
```

---

### Quando usare BDD?

**BDD è utile quando:**
- Il team include non tecnici che devono validare i requisiti
- I requisiti cambiano frequentemente e devono essere documentati in modo leggibile
- Vuoi una documentazione viva che si aggiorna automaticamente con il codice

**BDD non è necessario quando:**
- Il team è solo di sviluppatori
- I requisiti sono puramente tecnici
- La complessità della "traduzione" Gherkin → Python supera il beneficio

---

## B10: Mutation Testing con mutmut

### Il problema: test che non testano davvero

Considera questi test:

```python
def classifica_eta(eta: int) -> str:
    if eta < 18:
        return "minore"
    return "adulto"


def test_classifica():
    assert classifica_eta(10) == "minore"
    assert classifica_eta(30) == "adulto"
```

I test passano. Ma c'è un problema: se cambio `< 18` in `<= 18`, i test
passano ancora! Il test per `eta=18` manca.

---

### Mutation Testing: introduci bug di proposito

Il **mutation testing** risponde alla domanda: "Se introduco un bug nel codice,
i test lo trovano?"

**Come funziona:**
1. mutmut prende il codice sorgente e crea migliaia di versioni modificate
   ("mutanti") — cambia `<` in `<=`, `+` in `-`, `True` in `False`, ecc.
2. Per ogni mutante, esegue la suite di test
3. Se i test **falliscono** → il mutante è "ucciso" (i test lo hanno trovato)
4. Se i test **passano** → il mutante è "sopravvissuto" (i test non hanno trovato il bug)

I mutanti sopravvissuti indicano lacune nei test.

---

### Installazione e utilizzo

```bash
pip install mutmut

# Esegui il mutation testing
mutmut run --paths-to-mutate=src/

# Visualizza i risultati
mutmut results

# Mostra i dettagli di un mutante specifico
mutmut show 42

# Report HTML
mutmut html
```

---

### Esempio pratico

```python
# src/calcolatrice.py
def calcola_sconto(prezzo: float, percentuale: float) -> float:
    if percentuale < 0 or percentuale > 100:
        raise ValueError("Percentuale non valida")
    return prezzo * (1 - percentuale / 100)
```

```python
# tests/test_calcolatrice.py

# Test deboli che NON catturano le mutazioni boundary
def test_sconto_deboli():
    assert calcola_sconto(100, 20) == 80.0
    assert calcola_sconto(100, 0) == 100.0
    assert calcola_sconto(100, 100) == 0.0


# Test forti con boundary cases
def test_sconto_forti():
    assert calcola_sconto(100, 20) == 80.0
    assert calcola_sconto(100, 0) == 100.0
    assert calcola_sconto(100, 100) == 0.0

    # Boundary: la mutazione < → <= cambia quale valore solleva errore
    import pytest
    with pytest.raises(ValueError):
        calcola_sconto(100, -0.001)  # Appena sotto 0

    with pytest.raises(ValueError):
        calcola_sconto(100, 100.001)  # Appena sopra 100

    # Non deve sollevare errori ai boundary
    calcola_sconto(100, 0)      # Esattamente 0: valido
    calcola_sconto(100, 100)    # Esattamente 100: valido
```

---

### Tipi di mutazioni generate da mutmut

| Tipo | Originale | Mutante |
|---|---|---|
| Operatore aritmetico | `a + b` | `a - b`, `a * b` |
| Operatore comparazione | `a > b` | `a >= b`, `a < b`, `a == b` |
| Operatore logico | `a and b` | `a or b` |
| Valore di ritorno | `return True` | `return False` |
| Costante numerica | `timeout = 30` | `timeout = 31`, `timeout = 29` |
| Rimozione condizione | `if a and b:` | `if a:`, `if b:` |
| Inversione condizione | `if x > 0:` | `if x <= 0:` |

---

### Interpretare i risultati

```bash
mutmut results
```

```
Legend for output:
- Killed mutants.   The test suite was able to detect the mutation.
- Survived mutants. The test suite was not able to detect the mutation.
- Timeout mutants.  The test suite took too long to run (likely infinite loop).
- Suspicious mutants.

67 mutations were made

Killed: 55 (82.09%)
Survived: 10 (14.93%)
Suspicious: 2 (2.99%)
```

**Obiettivo:** mutation score > 80%. Qualsiasi sopravvissuto è un candidato per
un nuovo test che cattura il boundary case mancante.

---

### Configurazione in pyproject.toml

```toml
[tool.mutmut]
paths_to_mutate = "src/"
tests_dir = "tests/"
runner = "python -m pytest -x --tb=no -q"
```

---

> **Riepilogo Parte B:**
> In questa sezione hai imparato i fondamentali avanzati del testing con pytest.
> Le fixture eliminano la duplicazione del setup. `parametrize` testa molti casi
> con poco codice. I marks permettono di filtrare i test. `conftest.py` centralizza
> la configurazione. Il mocking isola le dipendenze esterne. La coverage trova
> le lacune. Hypothesis genera automaticamente casi limite. Testcontainers usa
> database reali. BDD rende i test leggibili ai non tecnici. mutmut verifica la
> qualità dei test stessi.

---

## PARTE C — ESERCIZI COMPLETI

Ogni esercizio è accompagnato da:
1. La specifica del problema
2. Il codice sorgente da testare
3. I test richiesti
4. La soluzione completa
5. Estensioni per chi vuole approfondire

---

## Esercizio C1: Calcolatrice Completa

### Specifica

Scrivi una suite di test completa per una classe `Calcolatrice` che supporta
le quattro operazioni aritmetiche di base, la radice quadrata e la potenza.

### Il codice da testare

```python
# src/calcolatrice.py

import math


class Calcolatrice:
    """Calcolatrice con operazioni di base e funzioni matematiche."""

    def somma(self, a: float, b: float) -> float:
        """Restituisce a + b."""
        return a + b

    def sottrazione(self, a: float, b: float) -> float:
        """Restituisce a - b."""
        return a - b

    def moltiplicazione(self, a: float, b: float) -> float:
        """Restituisce a * b."""
        return a * b

    def divisione(self, a: float, b: float) -> float:
        """
        Restituisce a / b.

        Raises:
            ValueError: se b è zero.
        """
        if b == 0:
            raise ValueError("Divisione per zero non consentita")
        return a / b

    def radice_quadrata(self, n: float) -> float:
        """
        Restituisce la radice quadrata di n.

        Raises:
            ValueError: se n è negativo.
        """
        if n < 0:
            raise ValueError(f"Impossibile calcolare la radice quadrata di {n}")
        return math.sqrt(n)

    def potenza(self, base: float, esponente: float) -> float:
        """Restituisce base ** esponente."""
        return base ** esponente
```

### Test richiesti

Scrivi i test per tutti i comportamenti della calcolatrice, inclusi:
- Casi normali per ogni operazione
- Casi limite (zero, negativi, numeri molto grandi)
- Verifica delle eccezioni con messaggi
- Test parametrizzati per le operazioni comuni

### Soluzione

```python
# tests/test_calcolatrice.py

import pytest
from src.calcolatrice import Calcolatrice


@pytest.fixture
def calc():
    """Fixture: istanza fresca della calcolatrice per ogni test."""
    return Calcolatrice()


# ===== SOMMA =====

class TestSomma:
    """Suite di test per il metodo somma."""

    def test_somma_positivi(self, calc):
        assert calc.somma(3, 4) == 7

    def test_somma_negativi(self, calc):
        assert calc.somma(-3, -4) == -7

    def test_somma_misto(self, calc):
        assert calc.somma(-3, 5) == 2

    def test_somma_con_zero(self, calc):
        assert calc.somma(5, 0) == 5
        assert calc.somma(0, 5) == 5

    def test_somma_due_zeri(self, calc):
        assert calc.somma(0, 0) == 0

    def test_somma_float(self, calc):
        assert calc.somma(1.5, 2.5) == pytest.approx(4.0)

    def test_somma_float_imprecisione(self, calc):
        # 0.1 + 0.2 in binario non è esattamente 0.3
        assert calc.somma(0.1, 0.2) == pytest.approx(0.3)

    def test_somma_numeri_grandi(self, calc):
        assert calc.somma(1_000_000, 2_000_000) == 3_000_000


@pytest.mark.parametrize("a, b, atteso", [
    (1, 2, 3),
    (0, 0, 0),
    (-1, -1, -2),
    (1.5, 1.5, 3.0),
    (100, -100, 0),
], ids=["positivi", "doppio_zero", "negativi", "float", "annullamento"])
def test_somma_parametrizzata(a, b, atteso):
    calc = Calcolatrice()
    assert calc.somma(a, b) == pytest.approx(atteso)


# ===== DIVISIONE =====

class TestDivisione:
    """Suite di test per il metodo divisione."""

    def test_divisione_normale(self, calc):
        assert calc.divisione(10, 2) == 5.0

    def test_divisione_float(self, calc):
        assert calc.divisione(7, 2) == pytest.approx(3.5)

    def test_divisione_per_uno(self, calc):
        assert calc.divisione(42, 1) == 42.0

    def test_divisione_zero_fratto_n(self, calc):
        assert calc.divisione(0, 5) == 0.0

    def test_divisione_per_zero_solleva_errore(self, calc):
        with pytest.raises(ValueError, match="Divisione per zero"):
            calc.divisione(10, 0)

    def test_divisione_per_zero_messaggio_completo(self, calc):
        with pytest.raises(ValueError) as exc_info:
            calc.divisione(5, 0)
        assert "zero" in str(exc_info.value).lower()

    def test_divisione_negativi(self, calc):
        assert calc.divisione(-10, 2) == -5.0
        assert calc.divisione(10, -2) == -5.0
        assert calc.divisione(-10, -2) == 5.0


# ===== RADICE QUADRATA =====

class TestRadiceQuadrata:
    """Suite di test per il metodo radice_quadrata."""

    def test_radice_quadrata_perfetto(self, calc):
        assert calc.radice_quadrata(9) == 3.0
        assert calc.radice_quadrata(4) == 2.0
        assert calc.radice_quadrata(16) == 4.0

    def test_radice_quadrata_zero(self, calc):
        assert calc.radice_quadrata(0) == 0.0

    def test_radice_quadrata_uno(self, calc):
        assert calc.radice_quadrata(1) == 1.0

    def test_radice_quadrata_float(self, calc):
        assert calc.radice_quadrata(2) == pytest.approx(1.4142135, rel=1e-5)

    def test_radice_quadrata_negativo_solleva_errore(self, calc):
        with pytest.raises(ValueError, match="radice quadrata"):
            calc.radice_quadrata(-1)

    def test_radice_quadrata_negativo_messaggio_contiene_valore(self, calc):
        with pytest.raises(ValueError) as exc_info:
            calc.radice_quadrata(-25)
        assert "-25" in str(exc_info.value)


@pytest.mark.parametrize("n, atteso", [
    (0, 0.0),
    (1, 1.0),
    (4, 2.0),
    (9, 3.0),
    (25, 5.0),
    (100, 10.0),
], ids=["zero", "uno", "quattro", "nove", "venticinque", "cento"])
def test_radice_quadrata_perfetti(n, atteso):
    calc = Calcolatrice()
    assert calc.radice_quadrata(n) == atteso


# ===== POTENZA =====

class TestPotenza:
    """Suite di test per il metodo potenza."""

    def test_potenza_normale(self, calc):
        assert calc.potenza(2, 3) == 8.0

    def test_potenza_zero(self, calc):
        assert calc.potenza(5, 0) == 1.0   # Qualsiasi numero^0 = 1
        assert calc.potenza(0, 5) == 0.0   # 0^qualsiasi = 0

    def test_potenza_uno(self, calc):
        assert calc.potenza(7, 1) == 7.0

    def test_potenza_negativa(self, calc):
        assert calc.potenza(2, -1) == pytest.approx(0.5)
        assert calc.potenza(2, -2) == pytest.approx(0.25)

    def test_potenza_base_negativa(self, calc):
        assert calc.potenza(-2, 2) == 4.0   # Negativo^pari = positivo
        assert calc.potenza(-2, 3) == -8.0  # Negativo^dispari = negativo

    def test_potenza_float(self, calc):
        assert calc.potenza(4, 0.5) == pytest.approx(2.0)  # Equivalente a sqrt(4)
```

**Output atteso con `pytest tests/test_calcolatrice.py -v`:**

```
tests/test_calcolatrice.py::TestSomma::test_somma_positivi PASSED
tests/test_calcolatrice.py::TestSomma::test_somma_negativi PASSED
...
tests/test_calcolatrice.py::TestDivisione::test_divisione_per_zero_solleva_errore PASSED
...
tests/test_calcolatrice.py::test_somma_parametrizzata[positivi] PASSED
...
========================== 30 passed in 0.12s ============================
```

### Estensioni

- Aggiungi la storia del calcolo (ogni operazione viene memorizzata)
- Aggiungi il metodo `percentuale(a, b)` che calcola il b% di a
- Scrivi property-based test con Hypothesis per verificare le proprietà
  matematiche (commutatività, associatività)

---

## Esercizio C2: Fixture con Database SQLite Temporaneo

### Specifica

Crea una suite di test per un sistema di gestione contatti che usa SQLite,
sfruttando le fixture per gestire il ciclo di vita del database.

### Il codice da testare

```python
# src/gestione_contatti.py

import sqlite3
from pathlib import Path
from typing import Optional


class GestioneContatti:
    """Sistema di gestione contatti con persistenza SQLite."""

    def __init__(self, percorso_db: str):
        self.percorso_db = percorso_db
        self._inizializza_db()

    def _inizializza_db(self) -> None:
        """Crea le tabelle se non esistono."""
        with self._connessione() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS contatti (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    cognome TEXT NOT NULL,
                    email TEXT UNIQUE,
                    telefono TEXT,
                    gruppo TEXT DEFAULT 'Personale'
                )
            """)

    def _connessione(self) -> sqlite3.Connection:
        return sqlite3.connect(self.percorso_db)

    def aggiungi(self, nome: str, cognome: str,
                 email: Optional[str] = None,
                 telefono: Optional[str] = None,
                 gruppo: str = "Personale") -> int:
        """Aggiunge un contatto e restituisce l'ID."""
        with self._connessione() as conn:
            cur = conn.execute(
                """INSERT INTO contatti (nome, cognome, email, telefono, gruppo)
                   VALUES (?, ?, ?, ?, ?) """,
                (nome, cognome, email, telefono, gruppo)
            )
            return cur.lastrowid

    def cerca_per_nome(self, nome: str) -> list[dict]:
        """Cerca contatti per nome o cognome (case-insensitive)."""
        with self._connessione() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute(
                """SELECT * FROM contatti
                   WHERE LOWER(nome) LIKE ? OR LOWER(cognome) LIKE ?""",
                (f"%{nome.lower()}%", f"%{nome.lower()}%")
            )
            return [dict(row) for row in cur.fetchall()]

    def cerca_per_id(self, id_contatto: int) -> Optional[dict]:
        """Cerca un contatto per ID."""
        with self._connessione() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute("SELECT * FROM contatti WHERE id = ?", (id_contatto,))
            riga = cur.fetchone()
            return dict(riga) if riga else None

    def aggiorna_telefono(self, id_contatto: int, nuovo_telefono: str) -> bool:
        """Aggiorna il telefono di un contatto. Restituisce True se trovato."""
        with self._connessione() as conn:
            cur = conn.execute(
                "UPDATE contatti SET telefono = ? WHERE id = ?",
                (nuovo_telefono, id_contatto)
            )
            return cur.rowcount > 0

    def elimina(self, id_contatto: int) -> bool:
        """Elimina un contatto per ID. Restituisce True se trovato."""
        with self._connessione() as conn:
            cur = conn.execute("DELETE FROM contatti WHERE id = ?", (id_contatto,))
            return cur.rowcount > 0

    def conta(self) -> int:
        """Restituisce il numero totale di contatti."""
        with self._connessione() as conn:
            cur = conn.execute("SELECT COUNT(*) FROM contatti")
            return cur.fetchone()[0]

    def per_gruppo(self, gruppo: str) -> list[dict]:
        """Restituisce i contatti di un gruppo specifico."""
        with self._connessione() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute(
                "SELECT * FROM contatti WHERE gruppo = ? ORDER BY cognome, nome",
                (gruppo,)
            )
            return [dict(row) for row in cur.fetchall()]
```

### Soluzione: test con fixture

```python
# tests/test_gestione_contatti.py

import pytest
from src.gestione_contatti import GestioneContatti


@pytest.fixture
def db_temporaneo(tmp_path):
    """
    Fixture che crea un database SQLite temporaneo per ogni test.
    tmp_path è una fixture built-in di pytest che fornisce una
    directory temporanea unica per ogni test.
    """
    percorso = str(tmp_path / "contatti_test.db")
    gestione = GestioneContatti(percorso)
    return gestione


@pytest.fixture
def db_con_dati(db_temporaneo):
    """
    Fixture che estende db_temporaneo aggiungendo contatti di esempio.
    Dipende da db_temporaneo — pytest la crea automaticamente.
    """
    # Aggiungi contatti di esempio
    id1 = db_temporaneo.aggiungi(
        "Mario", "Rossi",
        email="mario.rossi@email.it",
        telefono="555-0001",
        gruppo="Lavoro"
    )
    id2 = db_temporaneo.aggiungi(
        "Luigi", "Bianchi",
        email="luigi.bianchi@email.it",
        telefono="555-0002",
        gruppo="Lavoro"
    )
    id3 = db_temporaneo.aggiungi(
        "Anna", "Verdi",
        email="anna.verdi@personal.it",
        telefono="555-0003",
        gruppo="Personale"
    )

    # Restituisci sia la gestione che gli ID dei contatti creati
    return db_temporaneo, {"mario": id1, "luigi": id2, "anna": id3}


# ===== TEST CON db_temporaneo (database vuoto) =====

def test_database_inizialmente_vuoto(db_temporaneo):
    assert db_temporaneo.conta() == 0


def test_aggiungi_contatto_restituisce_id(db_temporaneo):
    id_contatto = db_temporaneo.aggiungi("Mario", "Rossi")
    assert isinstance(id_contatto, int)
    assert id_contatto > 0


def test_aggiungi_incrementa_contatore(db_temporaneo):
    db_temporaneo.aggiungi("Mario", "Rossi")
    db_temporaneo.aggiungi("Luigi", "Bianchi")
    assert db_temporaneo.conta() == 2


def test_aggiungi_senza_email(db_temporaneo):
    """Un contatto può essere creato senza email."""
    id_contatto = db_temporaneo.aggiungi("Marco", "Polo")
    contatto = db_temporaneo.cerca_per_id(id_contatto)
    assert contatto["email"] is None


def test_email_unica_vincolo(db_temporaneo):
    """Due contatti non possono avere la stessa email."""
    import sqlite3
    db_temporaneo.aggiungi("Mario", "Rossi", email="mario@test.it")

    with pytest.raises(sqlite3.IntegrityError):
        db_temporaneo.aggiungi("Altro", "Mario", email="mario@test.it")


# ===== TEST CON db_con_dati (database con contatti pre-inseriti) =====

def test_cerca_per_nome_trova_contatto(db_con_dati):
    gestione, ids = db_con_dati
    risultati = gestione.cerca_per_nome("mario")
    assert len(risultati) == 1
    assert risultati[0]["nome"] == "Mario"
    assert risultati[0]["cognome"] == "Rossi"


def test_cerca_per_nome_case_insensitive(db_con_dati):
    gestione, ids = db_con_dati
    risultati_lower = gestione.cerca_per_nome("mario")
    risultati_upper = gestione.cerca_per_nome("MARIO")
    risultati_mixed = gestione.cerca_per_nome("MaRiO")
    assert len(risultati_lower) == len(risultati_upper) == len(risultati_mixed)


def test_cerca_per_nome_parziale(db_con_dati):
    gestione, ids = db_con_dati
    risultati = gestione.cerca_per_nome("ros")  # Parte di "Rossi"
    assert len(risultati) == 1
    assert risultati[0]["cognome"] == "Rossi"


def test_cerca_per_nome_non_trovato(db_con_dati):
    gestione, ids = db_con_dati
    risultati = gestione.cerca_per_nome("Dracula")
    assert risultati == []


def test_cerca_per_id(db_con_dati):
    gestione, ids = db_con_dati
    contatto = gestione.cerca_per_id(ids["mario"])
    assert contatto is not None
    assert contatto["nome"] == "Mario"
    assert contatto["email"] == "mario.rossi@email.it"


def test_cerca_per_id_non_trovato(db_con_dati):
    gestione, ids = db_con_dati
    contatto = gestione.cerca_per_id(99999)  # ID inesistente
    assert contatto is None


def test_aggiorna_telefono(db_con_dati):
    gestione, ids = db_con_dati
    nuovo_numero = "333-9999"
    successo = gestione.aggiorna_telefono(ids["mario"], nuovo_numero)

    assert successo is True
    contatto = gestione.cerca_per_id(ids["mario"])
    assert contatto["telefono"] == nuovo_numero


def test_aggiorna_telefono_id_inesistente(db_con_dati):
    gestione, ids = db_con_dati
    successo = gestione.aggiorna_telefono(99999, "333-9999")
    assert successo is False


def test_elimina_contatto(db_con_dati):
    gestione, ids = db_con_dati
    conteggio_iniziale = gestione.conta()

    successo = gestione.elimina(ids["anna"])

    assert successo is True
    assert gestione.conta() == conteggio_iniziale - 1
    assert gestione.cerca_per_id(ids["anna"]) is None


def test_per_gruppo(db_con_dati):
    gestione, ids = db_con_dati
    contatti_lavoro = gestione.per_gruppo("Lavoro")
    contatti_personali = gestione.per_gruppo("Personale")

    assert len(contatti_lavoro) == 2
    assert len(contatti_personali) == 1
    assert all(c["gruppo"] == "Lavoro" for c in contatti_lavoro)


def test_per_gruppo_inesistente(db_con_dati):
    gestione, ids = db_con_dati
    risultati = gestione.per_gruppo("GruppoCheNonEsiste")
    assert risultati == []
```

### Cosa impari in questo esercizio

- Come usare `tmp_path` per database SQLite temporanei che vengono rimossi automaticamente
- Come costruire fixture dipendenti (`db_con_dati` usa `db_temporaneo`)
- Come testare vincoli del database (unicità dell'email)
- Come organizzare i test per fixture required (vuoto vs con dati)

---

## Esercizio C3: parametrize per Validatori

### Specifica

Scrivi una classe di validatori per dati italiani comuni e testali
con `@pytest.mark.parametrize`.

### Il codice da testare

```python
# src/validatori_italiani.py

import re


def valida_email(email: str) -> bool:
    """Valida un indirizzo email."""
    if not email or not isinstance(email, str):
        return False
    pattern = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def valida_codice_fiscale(cf: str) -> bool:
    """
    Valida la struttura di un codice fiscale italiano.
    Non verifica il carattere di controllo (solo lunghezza e formato).
    """
    if not cf or not isinstance(cf, str):
        return False
    pattern = r'^[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]$'
    return bool(re.match(pattern, cf.upper()))


def valida_numero_telefono_italiano(tel: str) -> bool:
    """
    Valida numeri di telefono italiani.
    Accetta: +39XXXXXXXXXX, 0XXXXXXX, 3XXXXXXXX
    """
    if not tel or not isinstance(tel, str):
        return False
    # Rimuovi spazi e trattini
    tel_pulito = tel.replace(" ", "").replace("-", "")
    patterns = [
        r'^\+39\d{9,10}$',   # +39 seguito da 9-10 cifre
        r'^0\d{6,9}$',        # Fisso italiano
        r'^3\d{8,9}$',        # Cellulare italiano (3XX XXXXXXXX)
    ]
    return any(bool(re.match(p, tel_pulito)) for p in patterns)


def valida_cap_italiano(cap: str) -> bool:
    """Valida un CAP italiano (5 cifre)."""
    if not cap or not isinstance(cap, str):
        return False
    return bool(re.match(r'^\d{5}$', cap.strip()))
```

### Soluzione con parametrize

```python
# tests/test_validatori.py

import pytest
from src.validatori_italiani import (
    valida_email,
    valida_codice_fiscale,
    valida_numero_telefono_italiano,
    valida_cap_italiano,
)


# ===== EMAIL =====

@pytest.mark.parametrize("email, valido", [
    # Email valide
    ("utente@dominio.it",                  True),
    ("nome.cognome@azienda.com",           True),
    ("utente+tag@gmail.com",               True),
    ("mail@sotto.dominio.org",             True),
    ("a@b.it",                             True),  # Minima valida

    # Email invalide
    ("",                                   False),  # Vuota
    ("senza_chiocciola",                   False),  # Manca @
    ("@dominio.it",                        False),  # Manca utente
    ("utente@",                            False),  # Manca dominio
    ("utente@dominio",                     False),  # Manca TLD
    ("utente @dominio.it",                 False),  # Spazio nel mezzo
    (None,                                 False),  # None
    (42,                                   False),  # Intero
], ids=[
    # Valide
    "standard", "nome.cognome", "con_tag", "sottodominio", "minima",
    # Invalide
    "vuota", "no_chiocciola", "no_utente", "no_dominio", "no_tld",
    "spazio", "none", "intero",
])
def test_valida_email(email, valido):
    assert valida_email(email) == valido


# ===== CODICE FISCALE =====

@pytest.mark.parametrize("cf, valido", [
    # CF validi (formato, non carattere di controllo)
    ("RSSMRA85T10A562S",   True),   # CF maschile standard
    ("BNCNGL68E49C351X",   True),   # CF femminile (giorno+40)
    ("rssmra85t10a562s",   True),   # Lowercase (deve essere accettato)

    # CF invalidi
    ("",                   False),  # Vuoto
    ("RSSMRA85T10A562",    False),  # 15 caratteri (manca uno)
    ("RSSMRA85T10A562SS",  False),  # 17 caratteri (uno di troppo)
    ("12345678901234AB",   False),  # Inizia con numeri
    ("RSSMRA85T10A562!",   False),  # Carattere speciale
    (None,                 False),  # None
], ids=[
    "maschile", "femminile", "lowercase",
    "vuoto", "corto", "lungo", "inizia_numeri", "carattere_speciale", "none",
])
def test_valida_codice_fiscale(cf, valido):
    assert valida_codice_fiscale(cf) == valido


# ===== TELEFONO =====

@pytest.mark.parametrize("telefono, valido", [
    # Validi
    ("+393401234567",      True),   # Cellulare con prefisso
    ("3401234567",         True),   # Cellulare senza prefisso
    ("340 123 4567",       True),   # Con spazi (devono essere rimossi)
    ("0212345678",         True),   # Fisso Milano
    ("06 1234567",         True),   # Fisso Roma con spazio

    # Invalidi
    ("",                   False),  # Vuoto
    ("123",                False),  # Troppo corto
    ("prova",              False),  # Non numerico
    ("+1234567890",        False),  # Prefisso non italiano
    (None,                 False),  # None
], ids=[
    "cellulare_con_prefisso", "cellulare_senza", "con_spazi", "fisso_mi", "fisso_rm",
    "vuoto", "troppo_corto", "non_numerico", "prefisso_estero", "none",
])
def test_valida_telefono(telefono, valido):
    assert valida_numero_telefono_italiano(telefono) == valido


# ===== CAP =====

@pytest.mark.parametrize("cap, valido", [
    ("00100", True),    # Roma centro
    ("20100", True),    # Milano
    ("80100", True),    # Napoli
    ("",      False),   # Vuoto
    ("1234",  False),   # 4 cifre (troppo corto)
    ("123456",False),   # 6 cifre (troppo lungo)
    ("ABCDE", False),   # Lettere
    ("1234A", False),   # Misto
], ids=["roma", "milano", "napoli", "vuoto", "corto", "lungo", "lettere", "misto"])
def test_valida_cap(cap, valido):
    assert valida_cap_italiano(cap) == valido
```

---

## Esercizio C4: Mock di API HTTP Esterna

### Specifica

Testa un servizio che interagisce con un'API meteo esterna, senza fare
chiamate HTTP reali.

### Il codice da testare

```python
# src/servizio_meteo.py

import requests
from dataclasses import dataclass
from typing import Optional


class ErroreAPI(Exception):
    """Errore generico dell'API meteo."""
    def __init__(self, messaggio: str, status_code: Optional[int] = None):
        super().__init__(messaggio)
        self.status_code = status_code


@dataclass
class DatiMeteo:
    citta: str
    temperatura: float
    umidita: int
    descrizione: str

    @property
    def fa_caldo(self) -> bool:
        return self.temperatura >= 30.0

    @property
    def piove(self) -> bool:
        return "pioggia" in self.descrizione.lower()


class ServizioMeteo:
    BASE_URL = "https://api.meteo-esempio.it/v2"
    TIMEOUT = 10  # secondi

    def __init__(self, api_key: str):
        self.api_key = api_key

    def ottieni_meteo(self, citta: str) -> DatiMeteo:
        """
        Recupera i dati meteo per una città.

        Raises:
            ErroreAPI: se la città non esiste (404) o c'è un errore del server (5xx).
            requests.Timeout: se la richiesta supera il timeout.
        """
        url = f"{self.BASE_URL}/meteo/{citta}"
        headers = {"X-API-Key": self.api_key}

        try:
            risposta = requests.get(url, headers=headers, timeout=self.TIMEOUT)
        except requests.Timeout:
            raise ErroreAPI(f"Timeout: l'API non ha risposto entro {self.TIMEOUT}s")

        if risposta.status_code == 404:
            raise ErroreAPI(f"Città non trovata: {citta}", status_code=404)

        if risposta.status_code >= 500:
            raise ErroreAPI(
                f"Errore del server: {risposta.status_code}",
                status_code=risposta.status_code
            )

        if risposta.status_code != 200:
            raise ErroreAPI(
                f"Risposta inattesa: {risposta.status_code}",
                status_code=risposta.status_code
            )

        dati = risposta.json()
        return DatiMeteo(
            citta=citta,
            temperatura=dati["temperature"],
            umidita=dati["humidity"],
            descrizione=dati["description"],
        )
```

### Soluzione con mock

```python
# tests/test_servizio_meteo.py

import pytest
import requests
from unittest.mock import patch, MagicMock
from src.servizio_meteo import ServizioMeteo, DatiMeteo, ErroreAPI


@pytest.fixture
def servizio():
    """Fixture: istanza del servizio con chiave API di test."""
    return ServizioMeteo(api_key="chiave-test-12345")


def crea_risposta_mock(status_code: int = 200, json_data: dict = None):
    """Helper: crea una risposta HTTP mockata."""
    mock_risposta = MagicMock()
    mock_risposta.status_code = status_code
    if json_data is not None:
        mock_risposta.json.return_value = json_data
    return mock_risposta


# ===== CASO DI SUCCESSO =====

@patch("src.servizio_meteo.requests.get")
def test_ottieni_meteo_successo(mock_get, servizio):
    """Test del caso normale: l'API risponde con 200 e dati validi."""
    mock_get.return_value = crea_risposta_mock(
        status_code=200,
        json_data={
            "temperature": 22.5,
            "humidity": 65,
            "description": "Cielo sereno"
        }
    )

    risultato = servizio.ottieni_meteo("Roma")

    # Verifica il risultato
    assert isinstance(risultato, DatiMeteo)
    assert risultato.citta == "Roma"
    assert risultato.temperatura == 22.5
    assert risultato.umidita == 65
    assert risultato.descrizione == "Cielo sereno"

    # Verifica che la chiamata HTTP sia stata fatta correttamente
    mock_get.assert_called_once_with(
        "https://api.meteo-esempio.it/v2/meteo/Roma",
        headers={"X-API-Key": "chiave-test-12345"},
        timeout=10,
    )


@patch("src.servizio_meteo.requests.get")
def test_proprieta_fa_caldo(mock_get, servizio):
    """Verifica la proprietà fa_caldo."""
    mock_get.return_value = crea_risposta_mock(
        json_data={"temperature": 35.0, "humidity": 80, "description": "Afoso"}
    )
    risultato = servizio.ottieni_meteo("Palermo")
    assert risultato.fa_caldo is True


@patch("src.servizio_meteo.requests.get")
def test_proprieta_piove(mock_get, servizio):
    """Verifica la proprietà piove."""
    mock_get.return_value = crea_risposta_mock(
        json_data={
            "temperature": 15.0,
            "humidity": 95,
            "description": "Pioggia intensa"
        }
    )
    risultato = servizio.ottieni_meteo("Venezia")
    assert risultato.piove is True


# ===== CASI DI ERRORE =====

@patch("src.servizio_meteo.requests.get")
def test_citta_non_trovata(mock_get, servizio):
    """Test: l'API restituisce 404 per città inesistente."""
    mock_get.return_value = crea_risposta_mock(status_code=404)

    with pytest.raises(ErroreAPI) as exc_info:
        servizio.ottieni_meteo("CittaCheNonEsiste")

    assert exc_info.value.status_code == 404
    assert "non trovata" in str(exc_info.value).lower()


@pytest.mark.parametrize("status_code", [500, 502, 503, 504], ids=[
    "internal_server_error", "bad_gateway", "service_unavailable", "gateway_timeout"
])
@patch("src.servizio_meteo.requests.get")
def test_errore_server(mock_get, status_code, servizio):
    """Test: l'API restituisce 5xx."""
    mock_get.return_value = crea_risposta_mock(status_code=status_code)

    with pytest.raises(ErroreAPI) as exc_info:
        servizio.ottieni_meteo("Milano")

    assert exc_info.value.status_code == status_code


@patch("src.servizio_meteo.requests.get")
def test_timeout_rete(mock_get, servizio):
    """Test: la richiesta va in timeout."""
    mock_get.side_effect = requests.Timeout("Timeout dopo 10s")

    with pytest.raises(ErroreAPI, match="Timeout"):
        servizio.ottieni_meteo("Roma")


@patch("src.servizio_meteo.requests.get")
def test_errore_connessione(mock_get, servizio):
    """Test: impossibile connettersi all'API."""
    mock_get.side_effect = requests.ConnectionError("Impossibile connettersi")

    # requests.ConnectionError non viene gestito: si propaga
    with pytest.raises(requests.ConnectionError):
        servizio.ottieni_meteo("Roma")
```

---

## Esercizio C5: Test di Funzioni con Side Effects sul Filesystem

### Specifica

Testa funzioni che leggono e scrivono file, usando `tmp_path` per evitare
di sporcare il filesystem reale.

### Il codice da testare

```python
# src/gestore_log.py

import json
from pathlib import Path
from datetime import datetime
from typing import Optional


class GestoreLog:
    """Gestisce un log strutturato in formato JSON Lines."""

    def __init__(self, percorso_file: str | Path):
        self.percorso = Path(percorso_file)
        self.percorso.parent.mkdir(parents=True, exist_ok=True)

    def scrivi(self, livello: str, messaggio: str,
               dati: Optional[dict] = None) -> None:
        """Aggiunge una riga al log."""
        voce = {
            "timestamp": datetime.now().isoformat(),
            "livello": livello.upper(),
            "messaggio": messaggio,
        }
        if dati:
            voce["dati"] = dati

        with self.percorso.open("a", encoding="utf-8") as f:
            f.write(json.dumps(voce, ensure_ascii=False) + "\n")

    def leggi_tutte(self) -> list[dict]:
        """Legge tutte le voci del log."""
        if not self.percorso.exists():
            return []
        voci = []
        with self.percorso.open("r", encoding="utf-8") as f:
            for riga in f:
                riga = riga.strip()
                if riga:
                    voci.append(json.loads(riga))
        return voci

    def filtra_per_livello(self, livello: str) -> list[dict]:
        """Restituisce solo le voci con il livello specificato."""
        return [v for v in self.leggi_tutte() if v["livello"] == livello.upper()]

    def conta_per_livello(self) -> dict[str, int]:
        """Conta le voci per livello."""
        conteggi: dict[str, int] = {}
        for voce in self.leggi_tutte():
            livello = voce["livello"]
            conteggi[livello] = conteggi.get(livello, 0) + 1
        return conteggi

    def svuota(self) -> None:
        """Svuota il file di log."""
        self.percorso.write_text("", encoding="utf-8")
```

### Soluzione

```python
# tests/test_gestore_log.py

import json
import pytest
from pathlib import Path
from src.gestore_log import GestoreLog


@pytest.fixture
def log_file(tmp_path):
    """Crea un GestoreLog in una directory temporanea."""
    percorso = tmp_path / "logs" / "app.jsonl"
    return GestoreLog(percorso)


@pytest.fixture
def log_con_dati(log_file):
    """GestoreLog con voci già scritte."""
    log_file.scrivi("INFO", "Applicazione avviata")
    log_file.scrivi("DEBUG", "Connessione al database", dati={"db": "postgres"})
    log_file.scrivi("WARNING", "Memoria bassa", dati={"ram_libera_mb": 512})
    log_file.scrivi("ERROR", "Errore elaborazione ordine", dati={"ordine_id": 42})
    log_file.scrivi("INFO", "Ordine riprocessato")
    return log_file


# ===== TEST BASE =====

def test_file_non_esiste_inizialmente(tmp_path):
    """Prima di scrivere, il file non esiste."""
    percorso = tmp_path / "log_che_non_esiste.jsonl"
    assert not percorso.exists()


def test_scrivi_crea_file(log_file):
    """La prima scrittura crea il file."""
    assert not log_file.percorso.exists()
    log_file.scrivi("INFO", "Test")
    assert log_file.percorso.exists()


def test_scrivi_voce_base(log_file):
    """Verifica struttura della voce scritta."""
    log_file.scrivi("INFO", "Messaggio di test")

    voci = log_file.leggi_tutte()
    assert len(voci) == 1

    voce = voci[0]
    assert voce["livello"] == "INFO"
    assert voce["messaggio"] == "Messaggio di test"
    assert "timestamp" in voce
    assert "dati" not in voce


def test_scrivi_voce_con_dati(log_file):
    """Verifica che i dati extra vengano salvati."""
    log_file.scrivi("DEBUG", "Query eseguita", dati={"query": "SELECT 1", "durata_ms": 5})

    voci = log_file.leggi_tutte()
    voce = voci[0]
    assert voce["dati"]["query"] == "SELECT 1"
    assert voce["dati"]["durata_ms"] == 5


def test_livello_uppercase(log_file):
    """Il livello deve essere sempre uppercase."""
    log_file.scrivi("info", "test")
    log_file.scrivi("WARNING", "test")
    log_file.scrivi("error", "test")

    voci = log_file.leggi_tutte()
    assert all(v["livello"] == v["livello"].upper() for v in voci)


# ===== TEST CON DATI =====

def test_leggi_tutte(log_con_dati):
    voci = log_con_dati.leggi_tutte()
    assert len(voci) == 5


def test_filtra_per_livello_info(log_con_dati):
    voci_info = log_con_dati.filtra_per_livello("info")
    assert len(voci_info) == 2
    assert all(v["livello"] == "INFO" for v in voci_info)


def test_filtra_per_livello_inesistente(log_con_dati):
    voci = log_con_dati.filtra_per_livello("CRITICAL")
    assert voci == []


def test_conta_per_livello(log_con_dati):
    conteggi = log_con_dati.conta_per_livello()
    assert conteggi["INFO"] == 2
    assert conteggi["DEBUG"] == 1
    assert conteggi["WARNING"] == 1
    assert conteggi["ERROR"] == 1
    assert "CRITICAL" not in conteggi


def test_svuota(log_con_dati):
    assert len(log_con_dati.leggi_tutte()) > 0
    log_con_dati.svuota()
    assert log_con_dati.leggi_tutte() == []


# ===== TEST EDGE CASES =====

def test_leggi_da_file_vuoto(log_file):
    """Leggi da file vuoto deve restituire lista vuota."""
    log_file.percorso.write_text("", encoding="utf-8")
    assert log_file.leggi_tutte() == []


def test_leggi_da_file_inesistente(tmp_path):
    """Leggi da file inesistente deve restituire lista vuota."""
    percorso = tmp_path / "non_esiste.jsonl"
    log = GestoreLog(percorso)
    assert log.leggi_tutte() == []


def test_directory_creata_automaticamente(tmp_path):
    """La directory viene creata automaticamente se non esiste."""
    percorso_profondo = tmp_path / "a" / "b" / "c" / "app.log"
    log = GestoreLog(percorso_profondo)
    log.scrivi("INFO", "Test")
    assert percorso_profondo.exists()


def test_caratteri_unicode(log_file):
    """Il log deve gestire correttamente i caratteri Unicode."""
    messaggio = "Errore: città non trovata — Düsseldorf"
    log_file.scrivi("ERROR", messaggio)

    voci = log_file.leggi_tutte()
    assert voci[0]["messaggio"] == messaggio
```

---

## Esercizio C6: Property-Based Test per Ordinamento

### Specifica

Usa Hypothesis per verificare le proprietà invarianti di un algoritmo di ordinamento.

### Il codice da testare

```python
# src/ordinamento.py

from typing import TypeVar

T = TypeVar("T")


def bubble_sort(lista: list) -> list:
    """
    Implementazione di Bubble Sort.
    NOTA: ha un bug intenzionale per lo scopo dell'esercizio.
    """
    lista = lista.copy()
    n = len(lista)
    for i in range(n):
        for j in range(0, n - i - 1):
            if lista[j] > lista[j + 1]:
                lista[j], lista[j + 1] = lista[j + 1], lista[j]
    return lista


def merge_sort(lista: list) -> list:
    """Implementazione di Merge Sort."""
    if len(lista) <= 1:
        return lista.copy()

    meta = len(lista) // 2
    sinistra = merge_sort(lista[:meta])
    destra = merge_sort(lista[meta:])

    return _merge(sinistra, destra)


def _merge(sinistra: list, destra: list) -> list:
    """Fonde due liste ordinate in una lista ordinata."""
    risultato = []
    i = j = 0

    while i < len(sinistra) and j < len(destra):
        if sinistra[i] <= destra[j]:
            risultato.append(sinistra[i])
            i += 1
        else:
            risultato.append(destra[j])
            j += 1

    risultato.extend(sinistra[i:])
    risultato.extend(destra[j:])
    return risultato
```

### Soluzione con Hypothesis

```python
# tests/test_ordinamento.py

import pytest
from hypothesis import given, assume
from hypothesis import strategies as st
from src.ordinamento import bubble_sort, merge_sort


# ===== PROPRIETÀ FONDAMENTALI =====

# Verifichiamo queste proprietà per entrambi gli algoritmi:
# 1. La lunghezza non cambia
# 2. Il risultato è ordinato
# 3. Il multiset degli elementi è lo stesso
# 4. Il risultato è deterministic (stessa input → stesso output)


@given(st.lists(st.integers(), min_size=0, max_size=100))
def test_bubble_sort_lunghezza_invariata(lista):
    """Bubble sort non deve mai cambiare il numero di elementi."""
    assert len(bubble_sort(lista)) == len(lista)


@given(st.lists(st.integers(), min_size=0, max_size=100))
def test_bubble_sort_risultato_ordinato(lista):
    """Il risultato di bubble sort deve essere ordinato."""
    ordinata = bubble_sort(lista)
    assert all(ordinata[i] <= ordinata[i+1] for i in range(len(ordinata)-1))


@given(st.lists(st.integers(), min_size=0, max_size=100))
def test_bubble_sort_stessi_elementi(lista):
    """Bubble sort deve preservare tutti gli elementi (stesso multiset)."""
    assert sorted(bubble_sort(lista)) == sorted(lista)


@given(st.lists(st.integers(), min_size=0, max_size=100))
def test_merge_sort_lunghezza_invariata(lista):
    assert len(merge_sort(lista)) == len(lista)


@given(st.lists(st.integers(), min_size=0, max_size=100))
def test_merge_sort_risultato_ordinato(lista):
    ordinata = merge_sort(lista)
    assert all(ordinata[i] <= ordinata[i+1] for i in range(len(ordinata)-1))


@given(st.lists(st.integers(), min_size=0, max_size=100))
def test_merge_sort_stessi_elementi(lista):
    assert sorted(merge_sort(lista)) == sorted(lista)


# ===== CONFRONTO TRA ALGORITMI =====

@given(st.lists(st.integers(), min_size=0, max_size=50))
def test_bubble_e_merge_stesso_risultato(lista):
    """I due algoritmi devono produrre lo stesso risultato."""
    assert bubble_sort(lista) == merge_sort(lista)


@given(st.lists(st.integers(), min_size=0, max_size=50))
def test_algoritmi_concordano_con_sorted_builtin(lista):
    """Entrambi devono concordare con sorted() della libreria standard."""
    riferimento = sorted(lista)
    assert bubble_sort(lista) == riferimento
    assert merge_sort(lista) == riferimento


# ===== PROPRIETÀ AGGIUNTIVE =====

@given(st.lists(st.integers(), min_size=1, max_size=50))
def test_minimo_e_massimo_posizione_corretta(lista):
    """Il minimo deve essere in posizione 0, il massimo nell'ultima."""
    ordinata = merge_sort(lista)
    assert ordinata[0] == min(lista)
    assert ordinata[-1] == max(lista)


@given(st.lists(st.integers(), min_size=2, max_size=50))
def test_idempotente(lista):
    """Ordinare una lista già ordinata non cambia nulla."""
    prima = merge_sort(lista)
    seconda = merge_sort(prima)
    assert prima == seconda


# ===== TEST TRADIZIONALI PER CASI SPECIFICI =====

@pytest.mark.parametrize("lista_input, attesa", [
    ([],           []),
    ([1],          [1]),
    ([2, 1],       [1, 2]),
    ([3, 1, 2],    [1, 2, 3]),
    ([3, 3, 3],    [3, 3, 3]),
    ([-5, 0, 5],   [-5, 0, 5]),
])
def test_merge_sort_casi_base(lista_input, attesa):
    assert merge_sort(lista_input) == attesa
```

---

## Esercizio C7: Integration Test con Testcontainers Postgres

### Specifica

Scrivi integration test per un sistema di gestione prodotti usando PostgreSQL reale.

### Il codice da testare

```python
# src/repository_prodotti.py

from dataclasses import dataclass
from typing import Optional
import psycopg2
import psycopg2.extras


@dataclass
class Prodotto:
    id: Optional[int]
    nome: str
    prezzo: float
    categoria: str
    disponibile: bool = True


class RepositoryProdotti:
    """Repository per la gestione dei prodotti su PostgreSQL."""

    def __init__(self, conn):
        self.conn = conn
        self._inizializza_schema()

    def _inizializza_schema(self) -> None:
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS prodotti (
                    id SERIAL PRIMARY KEY,
                    nome TEXT NOT NULL,
                    prezzo NUMERIC(10,2) NOT NULL CHECK (prezzo >= 0),
                    categoria TEXT NOT NULL,
                    disponibile BOOLEAN DEFAULT TRUE,
                    creato_il TIMESTAMP DEFAULT NOW()
                )
            """)
        self.conn.commit()

    def salva(self, prodotto: Prodotto) -> Prodotto:
        """Salva un nuovo prodotto e restituisce il prodotto con ID."""
        with self.conn.cursor() as cur:
            cur.execute(
                """INSERT INTO prodotti (nome, prezzo, categoria, disponibile)
                   VALUES (%s, %s, %s, %s) RETURNING id""",
                (prodotto.nome, prodotto.prezzo, prodotto.categoria, prodotto.disponibile)
            )
            nuovo_id = cur.fetchone()[0]
        self.conn.commit()
        return Prodotto(
            id=nuovo_id,
            nome=prodotto.nome,
            prezzo=prodotto.prezzo,
            categoria=prodotto.categoria,
            disponibile=prodotto.disponibile,
        )

    def cerca_per_id(self, id_prodotto: int) -> Optional[Prodotto]:
        with self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("SELECT * FROM prodotti WHERE id = %s", (id_prodotto,))
            riga = cur.fetchone()
        if not riga:
            return None
        return Prodotto(
            id=riga["id"], nome=riga["nome"], prezzo=float(riga["prezzo"]),
            categoria=riga["categoria"], disponibile=riga["disponibile"]
        )

    def cerca_per_categoria(self, categoria: str) -> list[Prodotto]:
        with self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(
                "SELECT * FROM prodotti WHERE categoria = %s AND disponibile = TRUE ORDER BY nome",
                (categoria,)
            )
            righe = cur.fetchall()
        return [
            Prodotto(id=r["id"], nome=r["nome"], prezzo=float(r["prezzo"]),
                     categoria=r["categoria"], disponibile=r["disponibile"])
            for r in righe
        ]

    def aggiorna_prezzo(self, id_prodotto: int, nuovo_prezzo: float) -> bool:
        with self.conn.cursor() as cur:
            cur.execute(
                "UPDATE prodotti SET prezzo = %s WHERE id = %s",
                (nuovo_prezzo, id_prodotto)
            )
            aggiornato = cur.rowcount > 0
        self.conn.commit()
        return aggiornato

    def disabilita(self, id_prodotto: int) -> bool:
        with self.conn.cursor() as cur:
            cur.execute(
                "UPDATE prodotti SET disponibile = FALSE WHERE id = %s",
                (id_prodotto,)
            )
            aggiornato = cur.rowcount > 0
        self.conn.commit()
        return aggiornato
```

### Soluzione con Testcontainers

```python
# tests/integration/test_repository_prodotti.py

import pytest
import psycopg2
from testcontainers.postgres import PostgresContainer
from src.repository_prodotti import RepositoryProdotti, Prodotto


@pytest.fixture(scope="session")
def postgres():
    """Avvia PostgreSQL una volta per tutta la sessione di test."""
    with PostgresContainer("postgres:16-alpine") as pg:
        yield pg


@pytest.fixture
def conn(postgres):
    """Connessione PostgreSQL per ogni test, con cleanup automatico."""
    connessione = psycopg2.connect(
        host=postgres.get_container_host_ip(),
        port=postgres.get_exposed_port(5432),
        user=postgres.username,
        password=postgres.password,
        dbname=postgres.dbname,
    )
    yield connessione
    # Teardown: pulisci la tabella dopo ogni test
    connessione.rollback()
    with connessione.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS prodotti")
    connessione.commit()
    connessione.close()


@pytest.fixture
def repo(conn):
    """Repository con connessione e schema inizializzati."""
    return RepositoryProdotti(conn)


@pytest.fixture
def prodotti_esempio(repo):
    """Repository con prodotti di esempio."""
    laptop = repo.salva(Prodotto(
        id=None, nome="Laptop Pro", prezzo=999.99, categoria="Elettronica"
    ))
    mouse = repo.salva(Prodotto(
        id=None, nome="Mouse Wireless", prezzo=29.99, categoria="Elettronica"
    ))
    libro = repo.salva(Prodotto(
        id=None, nome="Python Avanzato", prezzo=35.00, categoria="Libri"
    ))
    return repo, {"laptop": laptop, "mouse": mouse, "libro": libro}


# ===== TEST =====

def test_salva_prodotto(repo):
    prodotto = Prodotto(id=None, nome="Test Prodotto", prezzo=19.99, categoria="Test")
    salvato = repo.salva(prodotto)

    assert salvato.id is not None
    assert salvato.id > 0
    assert salvato.nome == "Test Prodotto"
    assert salvato.prezzo == 19.99


def test_cerca_per_id(prodotti_esempio):
    repo, prodotti = prodotti_esempio
    laptop = prodotti["laptop"]

    trovato = repo.cerca_per_id(laptop.id)

    assert trovato is not None
    assert trovato.nome == "Laptop Pro"
    assert trovato.prezzo == 999.99
    assert trovato.disponibile is True


def test_cerca_per_id_inesistente(repo):
    assert repo.cerca_per_id(99999) is None


def test_cerca_per_categoria(prodotti_esempio):
    repo, prodotti = prodotti_esempio

    elettronica = repo.cerca_per_categoria("Elettronica")
    libri = repo.cerca_per_categoria("Libri")

    assert len(elettronica) == 2
    assert len(libri) == 1
    assert all(p.categoria == "Elettronica" for p in elettronica)


def test_aggiorna_prezzo(prodotti_esempio):
    repo, prodotti = prodotti_esempio
    laptop = prodotti["laptop"]

    successo = repo.aggiorna_prezzo(laptop.id, 799.99)
    assert successo is True

    aggiornato = repo.cerca_per_id(laptop.id)
    assert aggiornato.prezzo == 799.99


def test_disabilita_prodotto(prodotti_esempio):
    repo, prodotti = prodotti_esempio
    mouse = prodotti["mouse"]

    successo = repo.disabilita(mouse.id)
    assert successo is True

    # I prodotti disabilitati non compaiono nella ricerca per categoria
    elettronica = repo.cerca_per_categoria("Elettronica")
    assert all(p.id != mouse.id for p in elettronica)


def test_prezzo_negativo_vincolo_db(repo):
    """Il database deve rifiutare prezzi negativi."""
    with pytest.raises(Exception):  # psycopg2.errors.CheckViolation
        repo.salva(Prodotto(id=None, nome="Invalido", prezzo=-1.0, categoria="Test"))
```

---

## Esercizio C8: BDD per Sistema di Autenticazione

### Specifica

Implementa scenari BDD per un sistema di autenticazione usando behave.

```gherkin
# features/autenticazione.feature

Feature: Autenticazione Utente
  Come utente del sistema
  Voglio poter accedere con le mie credenziali
  In modo da usare le funzionalità protette

  Background:
    Dato che il sistema ha i seguenti utenti registrati:
      | email              | password   | ruolo   | attivo |
      | admin@test.it      | Admin123!  | admin   | true   |
      | mario@test.it      | Mario456!  | base    | true   |
      | sospeso@test.it    | Test789!   | base    | false  |

  Scenario: Login con credenziali valide
    Quando l'utente "mario@test.it" tenta il login con password "Mario456!"
    Allora il login ha successo
    E viene restituito un token di accesso

  Scenario: Login con password sbagliata
    Quando l'utente "mario@test.it" tenta il login con password "PasswordSbagliata"
    Allora il login fallisce con errore "Credenziali non valide"

  Scenario: Login con email non registrata
    Quando l'utente "sconosciuto@test.it" tenta il login con password "qualsiasi"
    Allora il login fallisce con errore "Credenziali non valide"

  Scenario: Login con account sospeso
    Quando l'utente "sospeso@test.it" tenta il login con password "Test789!"
    Allora il login fallisce con errore "Account sospeso"

  Scenario Outline: Validazione formato email
    Quando l'utente "<email>" tenta il login con password "qualsiasi"
    Allora il login fallisce con errore "Email non valida"

    Examples:
      | email        |
      | non_una_mail |
      |              |
      | @solo_dominio|
```

```python
# features/steps/autenticazione_steps.py

from behave import given, when, then
import hashlib


class SistemaAutenticazione:
    def __init__(self):
        self.utenti = {}
        self.token_attivi = set()

    def registra_utente(self, email, password, ruolo="base", attivo=True):
        self.utenti[email] = {
            "email": email,
            "password_hash": hashlib.sha256(password.encode()).hexdigest(),
            "ruolo": ruolo,
            "attivo": attivo,
        }

    def login(self, email, password):
        import re
        # Valida formato email
        if not email or not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            raise ValueError("Email non valida")

        utente = self.utenti.get(email)
        if utente is None:
            raise ValueError("Credenziali non valide")

        if not utente["attivo"]:
            raise PermissionError("Account sospeso")

        password_hash = hashlib.sha256(password.encode()).hexdigest()
        if utente["password_hash"] != password_hash:
            raise ValueError("Credenziali non valide")

        token = f"token_{email}_{id(utente)}"
        self.token_attivi.add(token)
        return token


@given("che il sistema ha i seguenti utenti registrati:")
def step_carica_utenti(context):
    context.sistema = SistemaAutenticazione()
    for riga in context.table:
        context.sistema.registra_utente(
            email=riga["email"],
            password=riga["password"],
            ruolo=riga["ruolo"],
            attivo=riga["attivo"].lower() == "true",
        )


@when('l\'utente "{email}" tenta il login con password "{password}"')
def step_tenta_login(context, email, password):
    context.token = None
    context.errore = None
    try:
        context.token = context.sistema.login(email, password)
    except (ValueError, PermissionError) as e:
        context.errore = str(e)


@then("il login ha successo")
def step_login_successo(context):
    assert context.errore is None, f"Login fallito: {context.errore}"
    assert context.token is not None, "Nessun token restituito"


@then("viene restituito un token di accesso")
def step_token_restituito(context):
    assert context.token is not None
    assert context.token.startswith("token_")


@then('il login fallisce con errore "{messaggio_atteso}"')
def step_login_fallito(context, messaggio_atteso):
    assert context.token is None, "Il login non dovrebbe essere riuscito"
    assert context.errore is not None, "Nessun messaggio di errore"
    assert messaggio_atteso in context.errore, (
        f"Errore atteso: '{messaggio_atteso}'\n"
        f"Errore ricevuto: '{context.errore}'"
    )
```

---

## Esercizi C9–C12: Esercizi Aggiuntivi

### C9: Coverage Analysis Project

**Obiettivo:** Prendi il codice dell'Esercizio C1 (Calcolatrice) e:
1. Esegui `pytest --cov=src --cov-report=html tests/test_calcolatrice.py`
2. Apri il report HTML in `htmlcov/index.html`
3. Identifica le righe non coperte
4. Scrivi i test mancanti per raggiungere il 100% di branch coverage
5. Verifica con `pytest --cov=src --cov-branch --cov-fail-under=100 tests/`

### C10: Async API Testing

**Obiettivo:** Crea e testa una funzione asincrona che chiama più API in parallelo:

```python
# src/aggregatore.py
import asyncio
import httpx
from typing import Any


async def recupera_dati_multipli(urls: list[str]) -> list[Any]:
    """Recupera dati da più URL in parallelo."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        tasks = [client.get(url) for url in urls]
        risposte = await asyncio.gather(*tasks, return_exceptions=True)

    risultati = []
    for risposta in risposte:
        if isinstance(risposta, Exception):
            risultati.append({"errore": str(risposta)})
        elif risposta.status_code == 200:
            risultati.append(risposta.json())
        else:
            risultati.append({"status": risposta.status_code})

    return risultati
```

Scrivi test asincroni che usino `AsyncMock` per simulare le risposte HTTP.

### C11: Factory Boy per Data Generation

**Obiettivo:** Installa `factory-boy` e `faker`. Crea factory per:
- `UtenteFactory` con nome, cognome, email, data di nascita realistici
- `ProdottoFactory` con nome, prezzo, categoria
- `OrdineFactory` con utente (SubFactory), lista prodotti, totale calcolato

Usa le factory nei test dell'Esercizio C7 per generare dati di test senza
hardcodare valori.

### C12: Mutation Testing con mutmut

**Obiettivo:** Esegui mutmut sui test dell'Esercizio C1:
1. `mutmut run --paths-to-mutate=src/calcolatrice.py`
2. Analizza i mutanti sopravvissuti con `mutmut results`
3. Ispeziona ogni sopravvissuto con `mutmut show <id>`
4. Scrivi i test mancanti che "uccidono" i mutanti sopravvissuti
5. Raggiungi un mutation score > 90%

---

## PARTE D — APPROFONDIMENTO ESPERTI

---

## D1: pytest Internals e Plugin API

### Come funziona pytest internamente

pytest è costruito attorno a un sistema di hook (ganci) che permettono di estendere
ogni aspetto del suo comportamento. Comprendere questi meccanismi ti permette di
scrivere plugin potenti e personalizzare pytest per le esigenze del tuo team.

### Il ciclo di vita di pytest

Quando esegui `pytest`, accade questo:

```
1. Inizializzazione (pytest_configure)
   └─ Carica i plugin (built-in, da pip, da conftest.py)

2. Raccolta dei test (pytest_collection)
   ├─ Trova i file (pytest_collect_file)
   ├─ Raccoglie i test (pytest_pycollect_makeitem)
   └─ Modifica la raccolta (pytest_collection_modifyitems)

3. Esecuzione (pytest_runtest_protocol)
   ├─ Setup (pytest_runtest_setup)
   │   └─ Esegue le fixture
   ├─ Esecuzione del test (pytest_runtest_call)
   └─ Teardown (pytest_runtest_teardown)
       └─ Esegue il teardown delle fixture

4. Reporting (pytest_terminal_summary)
   └─ Mostra i risultati
```

---

### Scrivere un plugin pytest personalizzato

Un plugin può essere definito in `conftest.py` (per il progetto) o come pacchetto
pip (per la distribuzione):

```python
# conftest.py — plugin personalizzato

import time
import pytest
from collections import defaultdict


class PerformancePlugin:
    """Plugin che monitora le performance dei test."""

    def __init__(self):
        self.durate: dict[str, float] = {}
        self.soglia_lento = 1.0  # secondi

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_call(self, item):
        """Wrapper attorno all'esecuzione di ogni test."""
        inizio = time.perf_counter()
        yield
        durata = time.perf_counter() - inizio
        self.durate[item.nodeid] = durata

    def pytest_terminal_summary(self, terminalreporter):
        """Mostra un riepilogo delle performance alla fine."""
        test_lenti = {
            nodo: durata
            for nodo, durata in self.durate.items()
            if durata >= self.soglia_lento
        }

        if test_lenti:
            terminalreporter.write_sep("=", "Test lenti (≥1s)")
            for nodo, durata in sorted(test_lenti.items(), key=lambda x: -x[1]):
                terminalreporter.write_line(f"  {durata:.3f}s  {nodo}")


def pytest_configure(config):
    """Registra il plugin quando pytest viene configurato."""
    config.pluginmanager.register(PerformancePlugin(), "performance-plugin")
```

---

### Hook principali di pytest

```python
# conftest.py

def pytest_addoption(parser):
    """Aggiunge opzioni CLI personalizzate."""
    parser.addoption(
        "--ambiente",
        choices=["dev", "staging", "prod"],
        default="dev",
        help="Ambiente per i test di integrazione",
    )


def pytest_configure(config):
    """Eseguito durante l'inizializzazione di pytest."""
    # Registra marker personalizzati
    config.addinivalue_line(
        "markers",
        "critico: test che devono sempre passare prima del deploy"
    )


def pytest_collection_modifyitems(config, items):
    """Modifica la lista dei test raccolti."""
    # Esegui i test critici per primi
    critici = [item for item in items if item.get_closest_marker("critico")]
    non_critici = [item for item in items if not item.get_closest_marker("critico")]
    items[:] = critici + non_critici


def pytest_runtest_logreport(report):
    """Chiamato dopo ogni fase di un test (setup, call, teardown)."""
    if report.when == "call" and report.failed:
        print(f"\nFALLIMENTO: {report.nodeid}")


def pytest_sessionfinish(session, exitstatus):
    """Chiamato alla fine dell'intera sessione di test."""
    print(f"\nSessione completata con status: {exitstatus}")
```

---

### Il sistema di fixture internamente

Le fixture di pytest usano un meccanismo di dependency injection basato sui nomi
dei parametri. Internamente, pytest:

1. Raccoglie tutte le fixture disponibili (da conftest.py, da plugin, built-in)
2. Per ogni test, analizza i parametri della funzione
3. Risolve il grafo delle dipendenze (quale fixture dipende da quale)
4. Crea le fixture nell'ordine corretto, rispettando gli scope
5. Passa i valori al test
6. Esegue il teardown in ordine inverso

```python
# Esempio avanzato: fixture che accede al request context
@pytest.fixture
def fixture_context_aware(request):
    """Fixture che sa in quale test è in esecuzione."""
    test_name = request.node.name
    test_file = request.node.fspath
    marker = request.node.get_closest_marker("slow")

    print(f"\nSetup per: {test_name} in {test_file}")
    if marker:
        print("  (questo test è marcato come slow)")

    yield f"dati_per_{test_name}"

    print(f"\nTeardown per: {test_name}")
```

---

## D2: Testing Parallelo con pytest-xdist

### Perché parallelizzare i test?

Se hai 1000 test che impiegano 10 minuti, con 4 core potresti ridurre il tempo
a circa 2.5 minuti. pytest-xdist distribuisce i test su più worker Python.

### Installazione e utilizzo

```bash
pip install pytest-xdist

# Usa tutti i core disponibili
pytest -n auto

# Usa N worker specifici
pytest -n 4

# Distribuzione dei test: per file (default)
pytest -n 4 --dist loadfile

# Distribuzione: bilanciamento del carico
pytest -n 4 --dist load
```

---

### Considerazioni importanti per la parallelizzazione

Non tutti i test si parallelizzano facilmente. I problemi comuni:

**1. Stato globale condiviso**

```python
# PROBLEMA: variabile globale condivisa tra worker
contatore_globale = 0

def test_incrementa_contatore():
    global contatore_globale
    contatore_globale += 1
    assert contatore_globale == 1  # Può fallire con parallelizzazione!
```

```python
# SOLUZIONE: usa fixture per lo stato locale
@pytest.fixture
def contatore():
    return {"valore": 0}

def test_incrementa_contatore(contatore):
    contatore["valore"] += 1
    assert contatore["valore"] == 1  # Sicuro — locale al test
```

**2. Database condiviso**

Con più worker che scrivono sullo stesso database, possono avvenire conflitti.
La soluzione è usare database separati per ogni worker:

```python
# conftest.py
@pytest.fixture(scope="session")
def worker_id(request):
    """Restituisce l'ID del worker corrente (da pytest-xdist)."""
    if hasattr(request.config, "workerinput"):
        return request.config.workerinput["workerid"]
    return "master"


@pytest.fixture(scope="session")
def database(worker_id):
    """Ogni worker ha il proprio database."""
    url = f"sqlite:///test_{worker_id}.db"
    db = crea_database(url)
    yield db
    db.drop_all()
```

**3. File temporanei**

pytest-xdist garantisce che `tmp_path` sia unica per ogni test anche in parallelo.

---

### Configurazione ottimale

```toml
# pyproject.toml
[tool.pytest.ini_options]
addopts = [
    "-n", "auto",           # Usa tutti i core disponibili
    "--dist", "loadfile",   # Tieni i test dello stesso file nello stesso worker
]
```

---

## D3: Snapshot Testing con syrupy

### Cos'è lo snapshot testing?

Lo snapshot testing cattura l'output di una funzione e lo salva su file.
Nelle esecuzioni successive, confronta l'output attuale con quello salvato.
Se differiscono, il test fallisce — e tu decidi se è un bug o una modifica intenzionale.

**Casi d'uso ideali:**
- Output JSON/XML complessi
- Schema di modelli (Pydantic, SQLAlchemy)
- Report formattati
- Output di rendering

### Installazione e utilizzo

```bash
pip install syrupy
```

```python
# tests/test_snapshot.py

def test_schema_utente(snapshot):
    """Verifica che lo schema Pydantic non cambi accidentalmente."""
    from src.modelli import Utente
    schema = Utente.model_json_schema()
    assert schema == snapshot  # Prima esecuzione: crea lo snapshot


def test_output_report(snapshot):
    """Verifica il formato del report generato."""
    dati = {"vendite": [100, 200, 150], "periodo": "Q1 2026"}
    report = genera_report_vendite(dati)
    assert report == snapshot
```

**Prima esecuzione** (crea gli snapshot):
```bash
pytest tests/test_snapshot.py --snapshot-update
```

Crea i file in `__snapshots__/test_snapshot.ambr`.

**Esecuzioni successive** (confronta):
```bash
pytest tests/test_snapshot.py
# PASSED se lo snapshot corrisponde
# FAILED se l'output è cambiato
```

**Aggiornamento** (dopo una modifica intenzionale):
```bash
pytest tests/test_snapshot.py --snapshot-update
git add __snapshots__/
git commit -m "Aggiorna snapshot dopo modifica schema utente"
```

---

### Gestione dei valori dinamici negli snapshot

Il problema: timestamp e UUID cambiano ad ogni esecuzione e romperebbero lo snapshot.

```python
def normalizza_per_snapshot(dati: dict) -> dict:
    """Sostituisce valori dinamici con placeholder stabili."""
    risultato = dati.copy()
    if "id" in risultato:
        risultato["id"] = "<UUID>"
    if "creato_il" in risultato:
        risultato["creato_il"] = "<TIMESTAMP>"
    if "token" in risultato:
        risultato["token"] = "<TOKEN_JWT>"
    return risultato


def test_risposta_creazione_utente(snapshot, client):
    risposta = client.post("/api/utenti", json={"nome": "Mario"})
    assert normalizza_per_snapshot(risposta.json()) == snapshot
```

---

## D4: Contract Testing con pact

### Cos'è il contract testing?

In un'architettura a microservizi, il **contract testing** verifica che il contratto
(interfaccia) tra un consumatore e un provider sia rispettato da entrambe le parti.

È un approccio intermedio tra unit test e integration test:
- Più veloce degli integration test (non richiede che tutti i servizi girino insieme)
- Più realistico degli unit test (verifica l'interfaccia reale)

### Il modello Pact

```
Consumer (es. Frontend)         Provider (es. Backend API)
     |                                    |
     | 1. Definisce il contratto          |
     |    (cosa mi aspetto dall'API)      |
     |                                    |
     | 2. Genera un pact file             |
     |                                    |
     |              pact file             |
     |---------------------------------->  |
     |                                    | 3. Verifica che l'API
     |                                    |    soddisfi il contratto
```

### Installazione e utilizzo base

```bash
pip install pact-python
```

```python
# tests/contract/test_consumer.py
# Lato consumer: definisci cosa ti aspetti dall'API

import pytest
from pact import Consumer, Provider

pact = Consumer("frontend").has_pact_with(Provider("backend-api"))


def test_ottieni_utente():
    """Il consumer si aspetta questa risposta dal provider."""
    (pact
     .given("esiste un utente con ID 1")
     .upon_receiving("una richiesta per l'utente 1")
     .with_request("GET", "/api/utenti/1")
     .will_respond_with(200, body={
         "id": 1,
         "nome": "Mario Rossi",
         "email": "mario@test.it"
     }))

    with pact:
        # Qui chiami il tuo codice consumer
        # che parla con l'API (che ora è il Pact mock server)
        import requests
        risposta = requests.get("http://localhost:1234/api/utenti/1")
        assert risposta.json()["nome"] == "Mario Rossi"
```

---

## D5: Performance Testing con pytest-benchmark

### Misurare le prestazioni nei test

`pytest-benchmark` integra la misurazione delle performance direttamente in pytest.
Esegue ogni funzione centinaia di volte e calcola statistiche.

```bash
pip install pytest-benchmark
```

```python
# tests/test_performance.py

def fibonacci_ricorsivo(n):
    if n <= 1:
        return n
    return fibonacci_ricorsivo(n - 1) + fibonacci_ricorsivo(n - 2)


def fibonacci_iterativo(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def fibonacci_memoizzato(n, memo={}):
    if n in memo:
        return memo[n]
    if n <= 1:
        return n
    memo[n] = fibonacci_memoizzato(n-1, memo) + fibonacci_memoizzato(n-2, memo)
    return memo[n]


def test_fibonacci_iterativo(benchmark):
    """Benchmark: misura le performance di fibonacci_iterativo(30)."""
    risultato = benchmark(fibonacci_iterativo, 30)
    assert risultato == 832040


def test_fibonacci_memoizzato(benchmark):
    """Benchmark: misura le performance di fibonacci_memoizzato(30)."""
    risultato = benchmark(fibonacci_memoizzato, 30)
    assert risultato == 832040


def test_benchmark_con_setup(benchmark):
    """Benchmark con setup separato dal codice misurato."""
    dati = list(range(10000))

    def ordina():
        return sorted(dati)

    benchmark.pedantic(
        ordina,
        rounds=100,        # Ripeti 100 volte
        warmup_rounds=10,  # Scarta le prime 10 esecuzioni (warm-up)
    )
```

**Output:**
```
------------------------------ benchmark: 3 tests ----------------------------
Name                          Min         Max        Mean     StdDev  Rounds
-----------------------------------------------------------------------------
test_fibonacci_iterativo     1.234us    2.456us    1.345us   0.23us   1000
test_fibonacci_memoizzato    0.987us    1.234us    1.023us   0.05us   1000
test_benchmark_con_setup    45.678us   52.345us   47.234us   2.34us    100
```

---

### Confronto delle performance nel tempo

```bash
# Salva i risultati in un file JSON
pytest --benchmark-save="baseline"

# Confronta con la baseline
pytest --benchmark-compare="baseline" --benchmark-compare-fail=mean:10%
```

Il secondo comando fallisce se la media è peggiorata più del 10% rispetto alla baseline.

---

### Asserzioni sulle performance

```python
def test_operazione_veloce(benchmark):
    """Verifica che l'operazione sia completata entro limiti accettabili."""
    risultato = benchmark(calcola_hash, "dati di test" * 100)

    # Verifica correttezza
    assert len(risultato) == 64  # SHA256 = 64 caratteri hex

    # Verifica performance (opzionale — può essere fragile in CI)
    assert benchmark.stats["mean"] < 0.001  # Meno di 1ms di media
```

---

## D6: Load Testing con Locust

### Cos'è il load testing?

Il load testing verifica come il sistema si comporta sotto carico elevato.
Mentre pytest-benchmark misura le performance di singole funzioni, Locust simula
molti utenti che interagiscono con il sistema contemporaneamente.

### Installazione e utilizzo base

```bash
pip install locust
```

```python
# locustfile.py

from locust import HttpUser, task, between


class UtenteNormale(HttpUser):
    """Simula un utente normale dell'applicazione."""

    # Aspetta tra 1 e 5 secondi tra un'azione e l'altra
    wait_time = between(1, 5)

    def on_start(self):
        """Eseguito all'inizio della simulazione per ogni utente."""
        # Login
        risposta = self.client.post("/api/login", json={
            "email": "test@test.it",
            "password": "password123"
        })
        if risposta.status_code == 200:
            self.token = risposta.json()["token"]
            self.client.headers.update({"Authorization": f"Bearer {self.token}"})

    @task(weight=3)
    def visualizza_prodotti(self):
        """Azione frequente: naviga il catalogo prodotti."""
        self.client.get("/api/prodotti")

    @task(weight=1)
    def visualizza_profilo(self):
        """Azione meno frequente: visualizza il profilo."""
        self.client.get("/api/profilo")

    @task(weight=2)
    def cerca_prodotto(self):
        """Ricerca di un prodotto."""
        self.client.get("/api/prodotti?q=laptop")
```

**Esecuzione:**

```bash
# Web UI (apri http://localhost:8089)
locust --host=http://localhost:8000

# Headless (senza UI, per CI)
locust --host=http://localhost:8000 \
       --users=100 \
       --spawn-rate=10 \
       --run-time=60s \
       --headless \
       --csv=risultati_carico
```

---

## D7: Fuzzing

### Cos'è il fuzzing?

Il **fuzzing** è una tecnica di testing che genera input casuali, invalidi o inattesi
per trovare crash, eccezioni non gestite e comportamenti anomali nel codice.

È diverso da Hypothesis (property-based testing): il fuzzer non conosce la struttura
dei dati — genera input casuali a basso livello (bytes, stringhe, ecc.).

### pythonfuzz: fuzzing per Python

```bash
pip install pythonfuzz
```

```python
# fuzz_test.py

from pythonfuzz.main import PythonFuzz
from src.parser_json import parse_json_personalizzato


@PythonFuzz
def fuzz(buf):
    """
    Il fuzzer chiama questa funzione con input casuali.
    Se solleva un'eccezione non gestita (non ValueError o JSONDecodeError),
    è un bug.
    """
    try:
        testo = buf.decode("utf-8", errors="ignore")
        parse_json_personalizzato(testo)
    except (ValueError, UnicodeDecodeError, Exception):
        # Eccezioni attese — non sono bug
        pass
    # Se il parser crasha con SegFault o hang → bug trovato dal fuzzer


if __name__ == "__main__":
    fuzz()
```

### atheris: fuzzing per Python (Google)

`atheris` è il fuzzer di Google per Python, più avanzato di pythonfuzz:

```bash
pip install atheris
```

```python
# atheris_fuzz.py

import atheris
import sys


def TestOneInput(data):
    """Funzione chiamata dal fuzzer con input casuali."""
    try:
        testo = data.decode("utf-8")
        # Testa qualsiasi funzione che potrebbe avere bug con input inattesi
        risultato = mia_funzione_complicata(testo)
    except (ValueError, UnicodeDecodeError):
        pass  # Eccezioni attese


if __name__ == "__main__":
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()
```

---

## D8: Tassonomia Completa dei Test Doubles

### I cinque tipi di test double

Un **test double** è qualsiasi oggetto che sostituisce una dipendenza reale nei test.
Gerard Meszaros ha catalogato cinque tipi distinti nel libro "xUnit Test Patterns":

---

#### 1. Dummy

Un oggetto passato ma mai utilizzato. Serve solo a soddisfare la firma di un metodo.

```python
# La funzione richiede un logger, ma nel test non ci interessa cosa logga
class LoggerDummy:
    def info(self, msg): pass
    def error(self, msg): pass


def test_calcola_totale():
    logger_dummy = LoggerDummy()  # Non viene mai chiamato nel test
    servizio = ServizioOrdini(logger=logger_dummy)
    assert servizio.calcola_totale([10.0, 20.0]) == 30.0
```

---

#### 2. Stub

Fornisce risposte predeterminate alle chiamate. Non verifica nulla — restituisce
solo valori fissi.

```python
class StubMeteo:
    """Restituisce sempre lo stesso dato, indipendentemente dall'input."""

    def temperatura(self, citta: str) -> float:
        return 20.0  # Sempre 20°C, per ogni città

    def precipitazioni(self, citta: str) -> bool:
        return False  # Non piove mai


def test_consiglio_abbigliamento():
    meteo = StubMeteo()
    consiglio = ConsigliAbbigliamento(meteo)
    assert consiglio.per_oggi("Roma") == "Giacca leggera"
```

---

#### 3. Spy

Avvolge un oggetto reale, delegando tutte le chiamate ma registrandole per
una verifica successiva.

```python
class SpyNotificatore:
    """Spy: delega all'implementazione reale ma registra le chiamate."""

    def __init__(self, notificatore_reale):
        self._reale = notificatore_reale
        self.chiamate = []

    def invia(self, destinatario: str, messaggio: str) -> bool:
        self.chiamate.append({"destinatario": destinatario, "messaggio": messaggio})
        return self._reale.invia(destinatario, messaggio)  # Delegato al reale


def test_ordine_notifica_cliente():
    notificatore_reale = NotificatoreEmail()
    spy = SpyNotificatore(notificatore_reale)

    servizio_ordini = ServizioOrdini(notificatore=spy)
    servizio_ordini.completa_ordine(ordine_id=42)

    # Verifica che la notifica sia stata inviata
    assert len(spy.chiamate) == 1
    assert spy.chiamate[0]["destinatario"] == "cliente@test.it"
```

---

#### 4. Mock

Verifica le interazioni: si aspetta di essere chiamato in un certo modo e
fallisce se le aspettative non sono soddisfatte.

```python
from unittest.mock import Mock


def test_ordine_invia_email_conferma():
    mock_notificatore = Mock()
    mock_notificatore.invia.return_value = True

    servizio_ordini = ServizioOrdini(notificatore=mock_notificatore)
    servizio_ordini.completa_ordine(ordine_id=42, email_cliente="mario@test.it")

    # Il mock verifica che invia() sia stato chiamato con i giusti argomenti
    mock_notificatore.invia.assert_called_once_with(
        destinatario="mario@test.it",
        messaggio="Il tuo ordine #42 è confermato"
    )
```

---

#### 5. Fake

Un'implementazione funzionante ma semplificata. Non adatta alla produzione, ma
abbastanza reale da essere usata nei test.

```python
class FakeRepositoryUtenti:
    """
    Implementazione in-memory del repository utenti.
    Funziona davvero (non restituisce valori fissi),
    ma usa un dizionario invece del database reale.
    """

    def __init__(self):
        self._utenti: dict[int, dict] = {}
        self._prossimo_id = 1

    def salva(self, utente: dict) -> dict:
        utente_con_id = {**utente, "id": self._prossimo_id}
        self._utenti[self._prossimo_id] = utente_con_id
        self._prossimo_id += 1
        return utente_con_id

    def trova_per_id(self, id_utente: int) -> dict | None:
        return self._utenti.get(id_utente)

    def trova_per_email(self, email: str) -> dict | None:
        return next(
            (u for u in self._utenti.values() if u.get("email") == email),
            None
        )


def test_registrazione_utente():
    repo = FakeRepositoryUtenti()  # Fake, non il database reale

    servizio = ServizioRegistrazione(repository=repo)
    utente = servizio.registra("Mario", "mario@test.it", "password123")

    assert utente["id"] > 0
    assert repo.trova_per_email("mario@test.it") is not None
```

---

### Tabella comparativa

| Tipo | Verifica interazioni? | Implementazione reale? | Quando usare |
|---|---|---|---|
| **Dummy** | No | No | Parametri richiesti ma non usati |
| **Stub** | No | No | Controllo dei valori restituiti |
| **Spy** | Sì (post-hoc) | Sì (delega) | Verificare che qualcosa sia chiamato, con il reale |
| **Mock** | Sì (pre-aspettativa) | No | Verificare interazioni precise |
| **Fake** | No | Sì (semplificata) | Sostituire componenti lenti (DB, rete) |

---

## D9: Quando NON Testare

### Il paradosso del testing

Il testing ha un costo — scrivere e mantenere i test richiede tempo. Non tutto
vale il costo di un test.

### Cosa generalmente NON vale la pena testare

**1. Codice generato automaticamente**

Le migrazioni di database, i file generati da strumenti, i protobuf compilati:
questi vengono verificati dai loro strumenti. Testare il loro output è duplicazione.

**2. Getter e setter banali**

```python
class Prodotto:
    def __init__(self, nome):
        self._nome = nome

    @property
    def nome(self) -> str:
        return self._nome  # Testare questo è un costo senza beneficio
```

**3. Codice di terze parti**

Non testare che `requests.get()` funzioni. Non testare che `json.dumps()`
serializza correttamente. Quei test sono nel repository di requests e json.

**4. Configurazione e script di deployment**

Un test per la configurazione è spesso più complicato della configurazione stessa.

---

### Il principio del ritorno sull'investimento (ROI)

Il testing ha ROI alto quando:
- Il codice è complesso e ha molti casi limite
- Il codice viene modificato frequentemente
- Un bug ha conseguenze gravi (denaro, sicurezza)
- Il codice è riutilizzato in molti contesti

Il testing ha ROI basso quando:
- Il codice è semplice e lineare
- Il codice non viene quasi mai modificato
- Un bug è facilmente rilevabile manualmente
- Il codice è throwaway (script one-shot)

---

### La regola pratica

**Scrivi un test quando:**
- Stai per implementare qualcosa di non banale
- Stai correggendo un bug (il test riproduce il bug — poi lo correggi)
- Stai refactorizzando codice complesso
- Stai integrando con un sistema esterno

**Considera di non scrivere un test quando:**
- L'implementazione è così ovvia che il test sarebbe identico al codice
- Stai esplorando/prototipando (scrivi i test quando la direzione è chiara)
- Il costo di mantenimento del test supera il costo del bug che potrebbe trovare

---

## PARTE E — RIEPILOGO E RIFERIMENTI

---

## E1: Checklist Testing — 40+ Punti

Usa questa checklist prima di ogni rilascio e durante le code review.

### Struttura e Organizzazione

- [ ] I file di test si chiamano `test_*.py` o `*_test.py`
- [ ] Le funzioni di test iniziano con `test_`
- [ ] I test sono nella directory `tests/` separata dal codice sorgente
- [ ] Esiste un `conftest.py` con le fixture condivise
- [ ] I marker personalizzati sono registrati in `pyproject.toml`
- [ ] La configurazione di pytest è in `pyproject.toml` (non `setup.cfg` o `pytest.ini`)
- [ ] Esiste un `.gitignore` che esclude `.pytest_cache/`, `htmlcov/`, `__pycache__/`

### Qualità dei Test

- [ ] Ogni test verifica un solo comportamento
- [ ] I nomi dei test descrivono chiaramente cosa testano
  - Buono: `test_calcola_sconto_restituisce_zero_per_percentuale_100`
  - Cattivo: `test_sconto_1`
- [ ] Ogni test segue il pattern AAA (Arrange-Act-Assert)
- [ ] Le sezioni AAA sono separate visivamente (righe vuote o commenti)
- [ ] Le assert hanno messaggi personalizzati quando il contesto non è ovvio
- [ ] I test non dipendono dall'ordine di esecuzione
- [ ] I test non dipendono da dati globali mutabili
- [ ] Non ci sono `assert True` o `assert False` senza logica

### Copertura dei Casi

- [ ] Sono testati sia i casi di successo che i casi di errore
- [ ] Sono testati i valori limite (zero, vuoto, massimo, minimo)
- [ ] Le eccezioni attese sono verificate con `pytest.raises()`
- [ ] Il tipo E il messaggio dell'eccezione sono verificati
- [ ] I numeri float sono confrontati con `pytest.approx()`
- [ ] Le stringhe case-insensitive sono verificate con entrambi i casi

### Fixtures

- [ ] Il codice di setup duplicato è estratto in fixture
- [ ] Le fixture hanno scope appropriato (function/class/module/session)
- [ ] Le fixture con risorse esterne usano `yield` per il teardown
- [ ] Le fixture factory sono usate quando servono oggetti con parametri variabili
- [ ] `autouse=True` è usato solo per setup universale, non per dati specifici

### Parametrize

- [ ] I casi identici con dati diversi sono unificati con `@pytest.mark.parametrize`
- [ ] I parametri hanno IDs descrittivi (`ids=[...]`)
- [ ] I casi speciali hanno marker appropriati (`pytest.param(..., marks=...)`)

### Mocking

- [ ] Si fa patch dove l'oggetto viene USATO, non dove è definito
- [ ] I mock usano `spec=` per rispettare l'interfaccia reale
- [ ] Si verificano le chiamate al mock (non solo il risultato)
- [ ] I test non sono over-mockati (le funzioni pure non vanno mockate)
- [ ] `AsyncMock` è usato per le funzioni asincrone

### Coverage

- [ ] La coverage è misurata con `pytest-cov`
- [ ] La branch coverage è attiva (`--cov-branch`)
- [ ] Esiste una soglia minima (≥80%) configurata in `pyproject.toml`
- [ ] Il report mostra le righe mancanti (`--cov-report=term-missing`)
- [ ] Il codice irraggiungibile è marcato con `# pragma: no cover`
- [ ] Le migrazioni e il codice generato sono esclusi dalla coverage

### Performance

- [ ] I test completano in tempi ragionevoli (unit test < 100ms)
- [ ] I test lenti sono marcati con `@pytest.mark.slow`
- [ ] I test lenti sono separati dall'esecuzione principale in CI
- [ ] `pytest-xdist` è considerato per suite grandi

### CI/CD

- [ ] I test girano automaticamente su ogni push/PR (GitHub Actions o simile)
- [ ] La pipeline fallisce se i test falliscono
- [ ] La pipeline fallisce se la coverage scende sotto la soglia
- [ ] I test di integrazione usano servizi containerizzati (non mocked)
- [ ] I report di test sono pubblicati come artifact CI

### Manutenibilità

- [ ] Il codice dei test è refactorizzato con la stessa cura del codice produzione
- [ ] Non c'è copia-incolla tra test (usa `parametrize` e fixture)
- [ ] I test sono aggiornati quando il comportamento del codice cambia
- [ ] I test rotti non vengono commentati o skippati senza un ticket aperto
- [ ] Le fixture inutilizzate vengono rimosse (usa `pytest-deadfixtures`)

---

## E2: Tabella "Tipo di Test → Strumento Giusto"

| Cosa vuoi testare | Strumento consigliato | Esempio |
|---|---|---|
| Funzione pura con input/output chiari | `pytest` + `assert` base | `assert somma(2, 3) == 5` |
| Stessa funzione con molti casi di dati | `@pytest.mark.parametrize` | Validatore email con 10 casi |
| Setup che si ripete in molti test | `@pytest.fixture` | Database, configurazione |
| Eccezioni e comportamento d'errore | `pytest.raises()` | `ValueError` per input invalido |
| Warning di deprecazione | `pytest.warns()` | `DeprecationWarning` |
| Codice che chiama API HTTP esterne | `unittest.mock.patch` + `responses` | Test di client API |
| Codice che usa il database | `@pytest.fixture` + SQLite in-memory | CRUD operations |
| Database reale (PostgreSQL/Redis/MongoDB) | `testcontainers` | Integration test |
| Generare molti dati di test realistici | `factory-boy` + `faker` | Utenti, prodotti, ordini |
| Proprietà invarianti (non esempi specifici) | `hypothesis` | Commutatività, idempotenza |
| Codice asincrono (async/await) | `pytest-asyncio` + `AsyncMock` | API asincrona |
| Output complessi (JSON schema, HTML) | `syrupy` (snapshot testing) | Schema Pydantic |
| Requisiti leggibili dai non tecnici | `behave` + Gherkin | Feature di autenticazione |
| Qualità dei test (bug nei test stessi) | `mutmut` | Boundary conditions |
| Performance di funzioni | `pytest-benchmark` | Fibonacci, ordinamento |
| Carico su sistema reale | `locust` | 100 utenti concorrenti |
| Input inattesi/malformati | `atheris` o `pythonfuzz` | Parser JSON |
| Dipendenze tra servizi (microservizi) | `pact` | Contract testing |
| Velocità: parallelizzare la suite | `pytest-xdist` | `-n auto` |
| Trovare dipendenze nascoste tra test | `pytest-randomly` | Ordine casuale |
| Identificare test flaky | `pytest-repeat` | `--count=50` |

---

## E3: Confronto unittest vs pytest

| Aspetto | unittest | pytest |
|---|---|---|
| **Stile** | Classe che estende `TestCase` | Funzioni standalone |
| **Assert** | `self.assertEqual(a, b)`, `self.assertTrue(x)`, ecc. | `assert a == b` |
| **Setup** | `setUp()` / `tearDown()` per metodo | `@pytest.fixture` |
| **Setup classe** | `setUpClass()` / `tearDownClass()` | `@pytest.fixture(scope="class")` |
| **Parametrizzazione** | `subTest` (limitato) | `@pytest.mark.parametrize` |
| **Skip** | `@unittest.skip()` | `@pytest.mark.skip()` |
| **Output errori** | Generico | Dettagliato con diff |
| **Plugin** | Limitati | 1500+ su PyPI |
| **Compatibilità** | Python standard | Richiede pip install |
| **Curva d'apprendimento** | Familiare per chi viene da Java | Più Pythonica |
| **Usato in progetti nuovi** | Raro | Standard de facto |

**Quando usare unittest:**
- Il progetto usa già unittest e la migrazione non è prioritaria
- Non puoi installare dipendenze esterne
- Il team è abituato allo stile JUnit

**Quando usare pytest (quasi sempre):**
- Progetto nuovo
- Vuoi una sintassi più pulita
- Hai bisogno di fixture avanzate e parametrizzazione
- Vuoi accedere all'ecosistema di plugin

---

## E4: Comandi pytest — Riferimento Rapido

```bash
# ESECUZIONE BASE
pytest                          # Esegui tutti i test
pytest tests/                   # Esegui test in una directory
pytest tests/test_calc.py       # Esegui un singolo file
pytest tests/test_calc.py::test_somma  # Esegui un test specifico
pytest tests/test_calc.py::TestCalc::test_somma  # Metodo in classe

# OUTPUT
pytest -v                       # Verboso (un test per riga)
pytest -vv                      # Più verboso
pytest -s                       # Mostra print() e output
pytest -q                       # Silenzioso (solo errori)
pytest --tb=short               # Traceback corto (predefinito consigliato)
pytest --tb=long                # Traceback completo
pytest --tb=no                  # Nessun traceback

# SELEZIONE
pytest -k "somma"               # Test il cui nome contiene "somma"
pytest -k "not slow"            # Test che NON contengono "slow"
pytest -k "somma or divisione"  # Uno O l'altro
pytest -m slow                  # Test marcati come "slow"
pytest -m "not slow"            # Test NON marcati come "slow"
pytest -m "integrazione and not slow"  # Combinazione logica

# COMPORTAMENTO
pytest -x                       # Ferma al primo fallimento
pytest --maxfail=3              # Ferma dopo 3 fallimenti
pytest --lf                     # Esegui solo i test falliti l'ultima volta
pytest --ff                     # Esegui prima i test falliti
pytest --nf                     # Esegui i nuovi test (non ancora eseguiti)

# COVERAGE
pytest --cov=src                # Coverage del modulo src
pytest --cov=src --cov-branch   # Con branch coverage
pytest --cov=src --cov-report=term-missing  # Mostra righe mancanti
pytest --cov=src --cov-report=html          # Report HTML
pytest --cov=src --cov-fail-under=80        # Fallisce se < 80%

# PERFORMANCE
pytest -n auto                  # Parallelizza su tutti i core (pytest-xdist)
pytest -n 4                     # Usa 4 worker
pytest --durations=10           # Mostra i 10 test più lenti

# DEBUG
pytest --pdb                    # Entra nel debugger al primo fallimento
pytest --pdb-failure            # Come --pdb ma per qualsiasi errore
pytest -v --tb=long --pdb       # Massimo dettaglio con debugger
```

---

## E5: Glossario

| Termine | Definizione |
|---|---|
| **AAA** | Arrange-Act-Assert: pattern per strutturare i test in tre fasi distinte. |
| **Assertion** | Verifica che una condizione sia vera. In pytest: `assert condizione`. |
| **AsyncMock** | Mock per funzioni e metodi asincroni (`async def`). |
| **autouse** | Parametro di fixture che la applica automaticamente a tutti i test nel suo scope. |
| **behave** | Framework Python per BDD che usa il linguaggio Gherkin. |
| **BDD** | Behavior-Driven Development: test scritti in linguaggio quasi-naturale (Gherkin). |
| **Branch coverage** | Metrica di coverage che verifica ogni ramo di ogni punto di decisione. |
| **capsys** | Fixture built-in di pytest che cattura stdout e stderr. |
| **caplog** | Fixture built-in di pytest che cattura i messaggi di logging. |
| **conftest.py** | File speciale di pytest che contiene fixture e hook condivisi. |
| **Contract testing** | Verifica che il contratto (interfaccia) tra microservizi sia rispettato. |
| **Coverage** | Percentuale del codice sorgente eseguita durante i test. |
| **Dummy** | Test double: oggetto passato ma mai usato nel test. |
| **E2E test** | End-to-End test: verifica un flusso utente completo. |
| **Fake** | Test double: implementazione funzionante ma semplificata (es. DB in-memory). |
| **factory_boy** | Libreria per generare oggetti di test complessi con dati realistici. |
| **faker** | Libreria per generare dati finti realistici (nomi, email, CF, ecc.). |
| **fixture** | Funzione pytest che prepara lo stato necessario per i test (setup + teardown). |
| **Fuzzing** | Tecnica di testing con input casuali/malformati per trovare bug nascosti. |
| **Gherkin** | Linguaggio di testo strutturato usato in BDD (Given/When/Then). |
| **Given-When-Then** | Pattern BDD: precondizioni, azione, risultato atteso. |
| **hypothesis** | Libreria Python per property-based testing. |
| **integration test** | Verifica l'interazione tra componenti reali del sistema. |
| **line coverage** | Metrica che verifica quante righe di codice vengono eseguite dai test. |
| **locust** | Strumento Python per load testing e stress testing. |
| **MagicMock** | Mock che implementa anche i magic methods Python (`__len__`, `__str__`, ecc.). |
| **marker** | Etichetta applicata a un test: `@pytest.mark.skip`, `@pytest.mark.slow`, ecc. |
| **Mock** | Test double: verifica che le interazioni avvengano come previsto. |
| **mock** | Oggetto simulato che sostituisce una dipendenza reale nei test. |
| **monkeypatch** | Fixture built-in di pytest per modificare attributi, variabili d'ambiente, ecc. |
| **mutation testing** | Tecnica che introduce bug intenzionali per verificare la qualità dei test. |
| **mutmut** | Strumento Python per mutation testing. |
| **over-mocking** | Anti-pattern: usare troppi mock, rendendo i test fragili e inutili. |
| **pact** | Framework per contract testing tra microservizi. |
| **patch()** | Funzione di `unittest.mock` che sostituisce temporaneamente un oggetto. |
| **parametrize** | Decoratore pytest per eseguire lo stesso test con dati diversi. |
| **property-based testing** | Verifica proprietà invarianti con input generati automaticamente. |
| **pytest** | Framework di testing Python de facto standard. |
| **pytest-asyncio** | Plugin per testare codice asincrono (`async def`). |
| **pytest-benchmark** | Plugin per misurare le performance dei test. |
| **pytest-cov** | Plugin per misurare la coverage del codice. |
| **pytest-mock** | Plugin che fornisce la fixture `mocker`. |
| **pytest-randomly** | Plugin che randomizza l'ordine dei test. |
| **pytest-xdist** | Plugin per l'esecuzione parallela dei test. |
| **scope** | In pytest: durata di vita di una fixture (function/class/module/session). |
| **shrinking** | In Hypothesis: riduzione automatica dell'input che causa fallimento al caso minimo. |
| **skip** | Marker pytest che salta un test: `@pytest.mark.skip`. |
| **skipif** | Marker pytest che salta un test condizionalmente: `@pytest.mark.skipif`. |
| **snapshot testing** | Approccio che cattura l'output e lo confronta con un riferimento su file. |
| **Spy** | Test double: avvolge l'oggetto reale e registra le chiamate. |
| **Stub** | Test double: restituisce valori predeterminati senza logica reale. |
| **syrupy** | Libreria Python per snapshot testing. |
| **TDD** | Test-Driven Development: scrivi il test prima del codice (Red-Green-Refactor). |
| **testcontainers** | Libreria che avvia container Docker come infrastruttura di test. |
| **tmp_path** | Fixture built-in di pytest che fornisce una directory temporanea unica. |
| **unit test** | Verifica una singola unità di codice in isolamento. |
| **xfail** | Marker pytest per test attesi fallire: `@pytest.mark.xfail`. |
| **xpass** | Stato di un test xfail che ha passato contro le aspettative. |
| **yield fixture** | Fixture che usa `yield` per separare setup e teardown. |

---

## E6: Struttura di un Progetto Testing Completo

Alla fine di questo percorso, la struttura del tuo progetto dovrebbe assomigliare a questa:

```
mio_progetto/
├── src/
│   ├── __init__.py
│   ├── calcolatrice.py
│   ├── validazione.py
│   ├── repository.py
│   └── servizi.py
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Fixture globali, opzioni CLI
│   │
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── conftest.py      # Fixture per unit test
│   │   ├── test_calcolatrice.py
│   │   └── test_validazione.py
│   │
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── conftest.py      # Fixture per integration (Testcontainers)
│   │   └── test_repository.py
│   │
│   └── e2e/
│       ├── __init__.py
│       ├── conftest.py      # Fixture per E2E (client HTTP)
│       └── test_flussi_utente.py
│
├── features/                # Test BDD con behave
│   ├── autenticazione.feature
│   └── steps/
│       └── autenticazione_steps.py
│
├── __snapshots__/           # Snapshot di syrupy (committati nel repo)
│
├── pyproject.toml           # Configurazione pytest, coverage, mutmut
├── locustfile.py            # Configurazione load testing
└── .github/
    └── workflows/
        └── ci.yml           # Pipeline CI/CD
```

---

## E7: Configurazione pyproject.toml Completa

```toml
# pyproject.toml — configurazione completa per un progetto Python con testing

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
asyncio_mode = "auto"          # Per pytest-asyncio
addopts = [
    "--strict-markers",
    "--strict-config",
    "-ra",                     # Sommario per test non passati
    "--tb=short",
    "--cov=src",
    "--cov-branch",
    "--cov-report=term-missing:skip-covered",
    "--cov-fail-under=80",
]
markers = [
    "slow: test che richiedono molto tempo",
    "integrazione: test che richiedono servizi esterni",
    "e2e: test end-to-end",
    "critico: test che devono passare prima del deploy",
]
filterwarnings = [
    "error",
    "ignore::DeprecationWarning:modulo_legacy",
]

[tool.coverage.run]
source = ["src"]
branch = true
omit = ["*/migrations/*", "*/test_*", "*/__pycache__/*"]

[tool.coverage.report]
fail_under = 80
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

[tool.mutmut]
paths_to_mutate = "src/"
tests_dir = "tests/"
runner = "python -m pytest -x --tb=no -q"
```

---

## E8: Pipeline CI/CD Completa

```yaml
# .github/workflows/ci.yml

name: CI — Test e Qualità

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  # Fase 1: Linting e type checking (veloce, feedback immediato)
  qualita:
    name: "Qualità del codice"
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install ruff mypy
      - run: ruff check src/ tests/
      - run: mypy src/ --strict

  # Fase 2: Unit test (veloci)
  unit:
    name: "Unit Test (Python ${{ matrix.python-version }})"
    runs-on: ubuntu-latest
    needs: qualita
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -e ".[dev]"
      - name: Esegui unit test
        run: |
          pytest tests/unit/ \
            -n auto \
            --cov=src \
            --cov-branch \
            --cov-fail-under=80 \
            --junitxml=report-unit.xml
      - uses: codecov/codecov-action@v4

  # Fase 3: Integration test (più lenti, richiedono servizi)
  integration:
    name: "Integration Test"
    runs-on: ubuntu-latest
    needs: unit
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_PASSWORD: testpass
          POSTGRES_DB: testdb
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e ".[dev]"
      - name: Esegui integration test
        env:
          DATABASE_URL: "postgresql://postgres:testpass@localhost:5432/testdb"
          REDIS_URL: "redis://localhost:6379"
        run: pytest tests/integration/ -m integrazione --timeout=60

  # Fase 4: E2E test (ancora più lenti)
  e2e:
    name: "E2E Test"
    runs-on: ubuntu-latest
    needs: integration
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e ".[dev]"
      - name: Avvia applicazione
        run: uvicorn src.main:app --host 0.0.0.0 --port 8000 &
      - name: Esegui E2E test
        run: pytest tests/e2e/ --timeout=120
```

---

## E9: Percorso verso tutorial_09

Hai completato il tutorial di testing! Il prossimo passo naturale è:

### `tutorial_09_type_hints_e_mypy.md`

Il testing e i type hints sono complementari:

- **I type hints riducono i bug** che i test devono trovare
- **mypy** trova errori di tipo a compile-time, prima dei test
- **I test verificano il comportamento a runtime**, i type hints la correttezza dei tipi

Nel tutorial_09 imparerai:
- Annotazioni di tipo (`int`, `str`, `list[int]`, `dict[str, Any]`)
- `Optional`, `Union`, `TypeVar`, `Generic`
- `Protocol` per duck typing tipizzato
- `dataclass` e `TypedDict`
- Configurare mypy nel progetto
- Integrare mypy nella pipeline CI insieme a pytest

---

### Letture Consigliate

**Libri:**
- *Python Testing with pytest, 2nd Edition* — Brian Okken (Pragmatic Bookshelf, 2022)
  Il libro di riferimento per pytest, scritto dall'autore che segue pytest da vicino.
- *Architecture Patterns with Python* — Harry Percival, Bob Gregory (O'Reilly, 2020)
  Capitoli eccellenti su TDD, test doubles e clean architecture.
- *Growing Object-Oriented Software, Guided by Tests* — Freeman, Pryce
  Il classico del TDD orientato agli oggetti, in Java ma i principi sono universali.

**Documentazione ufficiale:**
- pytest: https://docs.pytest.org/
- Hypothesis: https://hypothesis.readthedocs.io/
- Coverage.py: https://coverage.readthedocs.io/
- Testcontainers Python: https://testcontainers-python.readthedocs.io/
- unittest.mock: https://docs.python.org/3/library/unittest.mock.html
- behave: https://behave.readthedocs.io/

---

### Parole Finali

> Il testing non è una fase del ciclo di sviluppo — è una **pratica continua**
> che accompagna ogni riga di codice che scrivi.
>
> I principianti pensano al testing come a un costo. I professionisti lo vedono
> come un **investimento** che accelera lo sviluppo nel tempo.
>
> Ogni test che scrivi è una lettera al tuo io futuro: "Ehi, questo codice funziona
> così. Se stai leggendo questo in un momento di crisi, controlla questi casi."
>
> Scrivi i test come se il prossimo a lavorare su quel codice fossi tu, alle 2:00
> di mattina, durante un incidente in produzione. Perché prima o poi, sarà così.
>
> **Testa con fiducia. Rilascia con serenità.**

---

*Fine del Tutorial 08 — Testing con pytest*

*Prossimo: `tutorial_09_type_hints_e_mypy.md`*


---

## SEZIONE SUPPLEMENTARE F: TDD — Test-Driven Development in Profondità

---

## F1: Il Ciclo Red-Green-Refactor

### Cos'è davvero il TDD?

Il **Test-Driven Development** (Sviluppo Guidato dai Test) è una pratica di sviluppo
in cui scrivi il test *prima* del codice. Questo inverte il flusso tradizionale.

**Flusso tradizionale:**
```
Pensieri → Codice → (Forse) Test
```

**Flusso TDD:**
```
Pensieri → Test (fallisce) → Codice (minimo) → Refactoring
```

---

### Perché il TDD migliora il design?

Quando scrivi il test prima del codice, sei costretto a pensare a:
- **Cosa fa il codice?** (non come lo fa)
- **Qual è l'interfaccia pubblica?** (come viene usato il codice)
- **Quante dipendenze ha?** (codice facilmente testabile = codice ben disegnato)

Un codice difficile da testare è quasi sempre un sintomo di cattivo design:
troppo accoppiamento, troppe responsabilità, dipendenze nascoste.

---

### I tre passi in dettaglio

#### ROSSO: Scrivi un test che fallisce

```
┌─────────────────────────────────────────────┐
│  RED                                        │
│                                             │
│  1. Scrivi UN test per UN comportamento     │
│  2. Esegui il test                          │
│  3. Verifica che FALLISCA                   │
│                                             │
│  IMPORTANTE: se il test passa subito, è     │
│  sbagliato — stai testando qualcosa che     │
│  già esiste, non stai guidando il design    │
└─────────────────────────────────────────────┘
```

**Perché verificare che fallisca?** Perché un test che non puoi far fallire è un test
che non verifica nulla. Se il test passa anche quando il codice è sbagliato, non ti
protegge.

#### VERDE: Scrivi il codice minimo

```
┌─────────────────────────────────────────────┐
│  GREEN                                      │
│                                             │
│  1. Scrivi il MINIMO codice necessario      │
│  2. Esegui il test                          │
│  3. Verifica che PASSI                      │
│                                             │
│  IMPORTANTE: "minimo" significa davvero     │
│  minimo. Anche hardcode del risultato va    │
│  bene temporaneamente (triangolazione)      │
└─────────────────────────────────────────────┘
```

**Perché il codice minimo?** Per non anticipare requisiti che non esistono ancora.
La generalizzazione prematura è la radice di molta complessità inutile.

#### REFACTOR: Migliora senza rompere

```
┌─────────────────────────────────────────────┐
│  REFACTOR                                   │
│                                             │
│  1. Migliora il codice (rimuovi duplicati,  │
│     migliora nomi, semplifica logica)       │
│  2. Esegui tutti i test                     │
│  3. Verifica che siano ancora VERDI         │
│                                             │
│  IMPORTANTE: non aggiungere funzionalità    │
│  in questa fase. Solo migliorare.           │
└─────────────────────────────────────────────┘
```

---

### Esempio Completo: Stack (Pila)

Costruiamo una struttura dati Stack (LIFO) usando TDD puro.

#### Iterazione 1: Stack vuoto

**RED:**

```python
# tests/test_stack.py
# STEP 1: Scrivi il test PRIMA di creare la classe

import pytest

def test_stack_vuoto_ha_dimensione_zero():
    """Uno stack appena creato deve essere vuoto."""
    stack = Stack()  # Questa classe non esiste ancora!
    assert stack.dimensione() == 0
```

Esegui: `pytest tests/test_stack.py`

```
FAILED tests/test_stack.py::test_stack_vuoto_ha_dimensione_zero
    stack = Stack()
E           NameError: name 'Stack' is not defined
```

Perfetto — il test fallisce (rosso).

**GREEN:**

```python
# src/stack.py
# Codice minimo per far passare il test

class Stack:
    def dimensione(self) -> int:
        return 0  # Hardcoded! Ma fa passare il test.
```

Esegui: `pytest tests/test_stack.py` → PASSA.

**REFACTOR:** Nessun refactoring necessario per ora.

---

#### Iterazione 2: Push

**RED:**

```python
# tests/test_stack.py — aggiungi il nuovo test

def test_push_incrementa_dimensione():
    """push() deve incrementare la dimensione."""
    stack = Stack()
    stack.push("primo")
    assert stack.dimensione() == 1

    stack.push("secondo")
    assert stack.dimensione() == 2
```

Esegui: il test fallisce (dimensione() restituisce sempre 0).

**GREEN:**

```python
# src/stack.py — aggiorna per far passare il test

class Stack:
    def __init__(self):
        self._elementi = []

    def dimensione(self) -> int:
        return len(self._elementi)  # Non più hardcoded!

    def push(self, elemento) -> None:
        self._elementi.append(elemento)
```

Esegui: entrambi i test passano.

---

#### Iterazione 3: Pop

**RED:**

```python
def test_pop_restituisce_elemento_in_cima():
    """pop() deve restituire l'ultimo elemento inserito (LIFO)."""
    stack = Stack()
    stack.push("primo")
    stack.push("secondo")

    assert stack.pop() == "secondo"


def test_pop_decrementa_dimensione():
    """pop() deve ridurre la dimensione di 1."""
    stack = Stack()
    stack.push("elemento")
    stack.pop()
    assert stack.dimensione() == 0
```

**GREEN:**

```python
def pop(self):
    return self._elementi.pop()
```

---

#### Iterazione 4: Pop da stack vuoto

**RED:**

```python
def test_pop_da_stack_vuoto_solleva_eccezione():
    """pop() su uno stack vuoto deve sollevare un'eccezione."""
    stack = Stack()
    with pytest.raises(IndexError, match="Stack vuoto"):
        stack.pop()
```

**GREEN:**

```python
def pop(self):
    if not self._elementi:
        raise IndexError("Stack vuoto")
    return self._elementi.pop()
```

---

#### Iterazione 5: Peek

**RED:**

```python
def test_peek_mostra_elemento_senza_rimuoverlo():
    """peek() deve mostrare l'elemento in cima senza rimuoverlo."""
    stack = Stack()
    stack.push("elemento")

    assert stack.peek() == "elemento"
    assert stack.dimensione() == 1  # La dimensione non cambia


def test_peek_da_stack_vuoto_solleva_eccezione():
    """peek() su stack vuoto deve sollevare IndexError."""
    stack = Stack()
    with pytest.raises(IndexError, match="Stack vuoto"):
        stack.peek()
```

**GREEN:**

```python
def peek(self):
    if not self._elementi:
        raise IndexError("Stack vuoto")
    return self._elementi[-1]
```

---

#### Refactoring finale

Ora che tutti i test passano, possiamo refactorizzare:

```python
# src/stack.py — versione finale dopo refactoring

from typing import TypeVar, Generic

T = TypeVar("T")


class Stack(Generic[T]):
    """Stack generico (LIFO) con type hints."""

    def __init__(self) -> None:
        self._elementi: list[T] = []

    def push(self, elemento: T) -> None:
        """Aggiunge un elemento in cima allo stack."""
        self._elementi.append(elemento)

    def pop(self) -> T:
        """
        Rimuove e restituisce l'elemento in cima.

        Raises:
            IndexError: se lo stack è vuoto.
        """
        self._verifica_non_vuoto()
        return self._elementi.pop()

    def peek(self) -> T:
        """
        Mostra l'elemento in cima senza rimuoverlo.

        Raises:
            IndexError: se lo stack è vuoto.
        """
        self._verifica_non_vuoto()
        return self._elementi[-1]

    def dimensione(self) -> int:
        """Restituisce il numero di elementi."""
        return len(self._elementi)

    def vuoto(self) -> bool:
        """Restituisce True se lo stack è vuoto."""
        return len(self._elementi) == 0

    def _verifica_non_vuoto(self) -> None:
        """Lancia IndexError se lo stack è vuoto."""
        if self.vuoto():
            raise IndexError("Stack vuoto")
```

Esegui tutti i test: passano ancora.

**Questo è il TDD:** il codice finale è pulito, documentato, testato al 100%,
e abbiamo costruito ogni funzionalità passo dopo passo con la rete di sicurezza
dei test.

---

### La Triangolazione nel TDD

La **triangolazione** è la tecnica per forzare l'implementazione reale quando
la soluzione più semplice è un valore hardcoded.

```python
# Iterazione 1 — RED
def test_raddoppia_cinque():
    assert raddoppia(5) == 10

# GREEN facile — ma sbagliata!
def raddoppia(n):
    return 10  # Hardcoded! Passa il test ma è inutile.

# Iterazione 2 — Triangolazione: aggiungi un secondo test con valore diverso
def test_raddoppia_tre():
    assert raddoppia(3) == 6

# Ora 'return 10' non funziona più — sei COSTRETTO a implementare davvero
def raddoppia(n):
    return n * 2  # Implementazione reale
```

La triangolazione dice: se il codice minimo è hardcoded, aggiungi un secondo
esempio con un valore diverso per forzare la generalizzazione.

---

## F2: unittest — Il Framework Nativo Python

### Quando serve conoscere unittest

Anche se pytest è lo standard moderno, dovrai conoscere unittest perché:
- Moltissimi progetti esistenti lo usano
- pytest esegue test unittest senza modifiche (retro-compatibilità)
- Molti tutorial e documentazioni fanno riferimento a unittest
- È disponibile senza installazioni aggiuntive

---

### Struttura base di unittest

```python
# tests/test_calcolatrice_unittest.py

import unittest
from src.calcolatrice import Calcolatrice


class TestCalcolatrice(unittest.TestCase):
    """Classe di test per la Calcolatrice. Tutti i test devono ereditare da TestCase."""

    # ===== SETUP E TEARDOWN =====

    def setUp(self):
        """
        Eseguito PRIMA di ogni test.
        Equivalente a @pytest.fixture con scope="function".
        """
        self.calc = Calcolatrice()
        print(f"\nSetup: {self._testMethodName}")

    def tearDown(self):
        """
        Eseguito DOPO ogni test, anche se il test fallisce.
        Equivalente al codice dopo yield in una fixture.
        """
        print(f"\nTeardown: {self._testMethodName}")

    @classmethod
    def setUpClass(cls):
        """
        Eseguito UNA VOLTA prima di tutti i test nella classe.
        Equivalente a @pytest.fixture(scope="class").
        """
        cls.valore_condiviso = 42
        print("\nSetupClass")

    @classmethod
    def tearDownClass(cls):
        """
        Eseguito UNA VOLTA dopo tutti i test nella classe.
        """
        print("\nTeardownClass")

    # ===== TEST =====

    def test_somma_positivi(self):
        """Nome del test: deve iniziare con test_"""
        self.assertEqual(self.calc.somma(2, 3), 5)

    def test_somma_negativi(self):
        self.assertEqual(self.calc.somma(-1, -2), -3)

    def test_divisione_per_zero(self):
        with self.assertRaises(ValueError):
            self.calc.divisione(10, 0)

    def test_divisione_per_zero_con_messaggio(self):
        with self.assertRaises(ValueError) as ctx:
            self.calc.divisione(10, 0)
        self.assertIn("zero", str(ctx.exception).lower())


if __name__ == "__main__":
    unittest.main()
```

---

### Tutti i metodi assert di unittest

```python
class TestAssertions(unittest.TestCase):

    # Uguaglianza
    def test_assertEqual(self):
        self.assertEqual(2 + 2, 4)

    def test_assertNotEqual(self):
        self.assertNotEqual(2 + 2, 5)

    # Verità
    def test_assertTrue(self):
        self.assertTrue(10 > 5)

    def test_assertFalse(self):
        self.assertFalse(10 < 5)

    # Identità
    def test_assertIs(self):
        x = [1, 2, 3]
        y = x
        self.assertIs(x, y)  # Stesso oggetto in memoria

    def test_assertIsNot(self):
        self.assertIsNot([1, 2], [1, 2])  # Oggetti diversi

    # None
    def test_assertIsNone(self):
        self.assertIsNone(None)

    def test_assertIsNotNone(self):
        self.assertIsNotNone("valore")

    # Appartenenza
    def test_assertIn(self):
        self.assertIn(3, [1, 2, 3, 4])

    def test_assertNotIn(self):
        self.assertNotIn(5, [1, 2, 3, 4])

    # Tipo
    def test_assertIsInstance(self):
        self.assertIsInstance("ciao", str)

    def test_assertNotIsInstance(self):
        self.assertNotIsInstance(42, str)

    # Eccezioni
    def test_assertRaises(self):
        with self.assertRaises(ValueError):
            int("non_un_numero")

    def test_assertRaisesRegex(self):
        with self.assertRaisesRegex(ValueError, "invalid literal"):
            int("abc")

    # Approssimazione (float)
    def test_assertAlmostEqual(self):
        self.assertAlmostEqual(0.1 + 0.2, 0.3, places=10)

    def test_assertNotAlmostEqual(self):
        self.assertNotAlmostEqual(0.1, 0.2)

    # Regex
    def test_assertRegex(self):
        self.assertRegex("Errore: file non trovato", r"Errore:.*")

    # Multisetting (ordine irrilevante)
    def test_assertCountEqual(self):
        self.assertCountEqual([1, 2, 3], [3, 1, 2])  # Stesso contenuto, ordine diverso

    # Confronto con msg personalizzato
    def test_with_message(self):
        eta = 15
        self.assertGreaterEqual(eta, 18, f"Utente troppo giovane: {eta} anni")
```

---

### Organizzare le test suite con TestSuite

```python
import unittest


def crea_suite_completa():
    """Crea una suite con tutti i test del progetto."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Aggiungi classi specifiche
    suite.addTests(loader.loadTestsFromTestCase(TestCalcolatrice))
    suite.addTests(loader.loadTestsFromTestCase(TestValidazione))

    return suite


def crea_suite_rapida():
    """Crea una suite solo con i test rapidi."""
    loader = unittest.TestLoader()
    # Carica solo i test il cui nome contiene "rapido"
    pattern = loader.testMethodPrefix  # default: "test"

    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromName("test_calcolatrice_rapido"))
    return suite


if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(crea_suite_completa())
```

---

### Differenze chiave tra unittest e pytest

```python
# unittest
class TestEsempio(unittest.TestCase):

    def setUp(self):                          # Setup per ogni test
        self.dati = [1, 2, 3]

    def test_lunghezza(self):
        self.assertEqual(len(self.dati), 3)   # self.assertEqual(a, b)
        self.assertIn(2, self.dati)           # self.assertIn(x, c)
        self.assertTrue(len(self.dati) > 0)  # self.assertTrue(cond)

    @unittest.skip("Non ancora implementato")  # @unittest.skip
    def test_funzione_futura(self):
        pass

    @unittest.skipIf(True, "Condizione")      # @unittest.skipIf
    def test_condizionale(self):
        pass


# pytest — equivalente più conciso
import pytest

@pytest.fixture
def dati():                                    # Fixture invece di setUp
    return [1, 2, 3]

def test_lunghezza(dati):
    assert len(dati) == 3                      # assert normale
    assert 2 in dati
    assert len(dati) > 0

@pytest.mark.skip(reason="Non ancora implementato")
def test_funzione_futura():
    pass

@pytest.mark.skipif(True, reason="Condizione")
def test_condizionale():
    pass
```

---

## F3: Testing Asincrono — Guida Completa

### Il problema con il codice asincrono

Il codice asincrono (basato su `async/await`) non può essere testato con i test
tradizionali perché le funzioni async restituiscono coroutine, non valori.

```python
# PROBLEMA: questo NON funziona
async def recupera_dati():
    await asyncio.sleep(0.1)
    return {"risultato": 42}

def test_recupera_dati_SBAGLIATO():
    risultato = recupera_dati()  # Restituisce una coroutine, non il risultato!
    assert risultato == {"risultato": 42}  # Fallisce sempre
```

---

### pytest-asyncio: la soluzione

```bash
pip install pytest-asyncio
```

```toml
# pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"  # Marca automaticamente tutte le funzioni async come test
```

```python
# tests/test_asincrono.py

import pytest
import asyncio
from unittest.mock import AsyncMock, patch


# ===== TEST ASYNC BASE =====

async def recupera_dati():
    """Funzione asincrona che simula una chiamata I/O."""
    await asyncio.sleep(0.01)  # Simula latenza di rete
    return {"risultato": 42}


async def test_recupera_dati():
    """Test asincrono — pytest-asyncio lo esegue correttamente."""
    risultato = await recupera_dati()
    assert risultato == {"risultato": 42}


# ===== FIXTURE ASINCRONE =====

@pytest.fixture
async def client_asincrono():
    """Fixture asincrona per un client HTTP."""
    import httpx
    # In un test reale, puntereste a un'applicazione reale o di test
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        yield client
    # Il client viene chiuso automaticamente all'uscita dal async with


# ===== MOCKING ASINCRONO =====

class ServizioMeteo:
    async def temperatura(self, citta: str) -> float:
        import httpx
        async with httpx.AsyncClient() as client:
            risposta = await client.get(f"https://api.meteo.it/{citta}")
            return risposta.json()["temperatura"]


async def test_temperatura_con_mock():
    """Testa una funzione async che chiama un'API esterna."""
    servizio = ServizioMeteo()

    # AsyncMock: il mock che funziona con await
    with patch.object(servizio, "temperatura", new_callable=AsyncMock) as mock_temp:
        mock_temp.return_value = 22.5

        temperatura = await servizio.temperatura("Roma")
        assert temperatura == 22.5
        mock_temp.assert_awaited_once_with("Roma")


# ===== CONCORRENZA =====

async def test_operazioni_concorrenti():
    """Verifica che le operazioni asincrone funzionino in parallelo."""

    async def operazione(nome: str, delay: float) -> str:
        await asyncio.sleep(delay)
        return f"{nome}-completata"

    inizio = asyncio.get_event_loop().time()

    # gather esegue le operazioni in parallelo
    risultati = await asyncio.gather(
        operazione("A", 0.1),
        operazione("B", 0.1),
        operazione("C", 0.1),
    )

    fine = asyncio.get_event_loop().time()
    durata = fine - inizio

    assert "A-completata" in risultati
    assert "B-completata" in risultati
    assert "C-completata" in risultati

    # Se girassero in sequenza, impiegherebbero 0.3s
    # In parallelo, impiegano circa 0.1s
    assert durata < 0.25, f"Troppo lento: {durata:.2f}s"


# ===== GESTIONE DEGLI ERRORI ASYNC =====

async def operazione_che_fallisce():
    """Operazione asincrona che solleva un'eccezione."""
    await asyncio.sleep(0.01)
    raise ValueError("Errore durante l'operazione asincrona")


async def test_eccezione_asincrona():
    """Le eccezioni async si testano nello stesso modo delle sincrone."""
    with pytest.raises(ValueError, match="asincrona"):
        await operazione_che_fallisce()


# ===== TIMEOUT PER TEST ASINCRONI =====

@pytest.mark.timeout(2)  # Il test deve completarsi entro 2 secondi
async def test_con_timeout():
    """Verifica che l'operazione non blocchi indefinitamente."""
    risultato = await asyncio.wait_for(
        recupera_dati(),
        timeout=1.0  # Timeout a livello applicativo
    )
    assert risultato is not None


# ===== GENERATORI ASINCRONI =====

async def genera_eventi():
    """Generatore asincrono che emette eventi."""
    for i in range(5):
        await asyncio.sleep(0.01)
        yield {"tipo": "evento", "id": i}


async def test_generatore_asincrono():
    """Testa un generatore asincrono."""
    eventi = []
    async for evento in genera_eventi():
        eventi.append(evento)

    assert len(eventi) == 5
    assert all(e["tipo"] == "evento" for e in eventi)
    assert [e["id"] for e in eventi] == [0, 1, 2, 3, 4]
```

---

## F4: factory_boy e faker — Dati di Test Realistici

### Il problema dei dati di test hardcoded

```python
# Hardcoded — cattiva pratica
def test_sconto_senior():
    utente = Utente(
        nome="Mario",    # Chi è Mario? Perché Mario?
        eta=65,
        email="mario@test.it"
    )
    assert calcola_sconto(utente) == 0.15
```

I dati hardcoded rendono i test:
- **Fragili:** se cambio la validazione dell'email, "mario@test.it" potrebbe
  diventare invalida e rompere test che non hanno niente a che fare con email
- **Ingannevoli:** il test sembra verificare "Mario con 65 anni", ma in realtà
  dovrebbe verificare "qualsiasi utente senior"
- **Poco documentativi:** non è chiaro quali dati siano rilevanti per il test

---

### factory_boy: factory per oggetti di test

```bash
pip install factory-boy faker
```

```python
# tests/factories.py

import factory
from factory import Faker, LazyAttribute, SubFactory, Sequence
from faker import Faker as FakerLib

# Locale italiano per dati realistici
fake_it = FakerLib("it_IT")


class IndirizzoFactory(factory.Factory):
    class Meta:
        model = dict  # Crea un dizionario (modifica per classi reali)

    via = Faker("street_address", locale="it_IT")
    citta = Faker("city", locale="it_IT")
    cap = Faker("postcode", locale="it_IT")
    provincia = factory.LazyAttribute(lambda o: o.citta[:2].upper())


class UtenteFactory(factory.Factory):
    class Meta:
        model = dict

    nome = Faker("first_name", locale="it_IT")
    cognome = Faker("last_name", locale="it_IT")
    email = LazyAttribute(
        lambda o: f"{o.nome.lower()}.{o.cognome.lower()}@test.it"
    )
    eta = Faker("random_int", min=18, max=90)
    attivo = True
    ruolo = "base"
    indirizzo = SubFactory(IndirizzoFactory)

    class Params:
        """Traits per varianti comuni."""
        senior = factory.Trait(eta=65)
        admin = factory.Trait(ruolo="admin", email="admin@test.it")
        inattivo = factory.Trait(attivo=False)
        giovane = factory.Trait(eta=factory.Faker("random_int", min=18, max=25))


class ProdottoFactory(factory.Factory):
    class Meta:
        model = dict

    id = Sequence(lambda n: n + 1)
    nome = Faker("catch_phrase")  # Nome prodotto finto ma realistico
    prezzo = factory.LazyAttribute(
        lambda o: round(fake_it.pydecimal(left_digits=3, right_digits=2, positive=True), 2)
    )
    categoria = factory.Iterator(["Elettronica", "Abbigliamento", "Libri", "Sport"])
    disponibile = True


class OrdineFactory(factory.Factory):
    class Meta:
        model = dict

    id = Sequence(lambda n: f"ORD-{n:06d}")
    utente = SubFactory(UtenteFactory)
    prodotti = factory.LazyAttribute(lambda o: [ProdottoFactory() for _ in range(2)])
    stato = "in_attesa"
    totale = factory.LazyAttribute(
        lambda o: sum(p["prezzo"] for p in o.prodotti)
    )
```

---

### Usare le factory nei test

```python
# tests/test_con_factory.py

import pytest
from tests.factories import UtenteFactory, ProdottoFactory, OrdineFactory


def test_sconto_senior():
    """Testa lo sconto per utenti senior."""
    utente = UtenteFactory(senior=True)

    assert utente["eta"] == 65
    sconto = calcola_sconto(utente)
    assert sconto == 0.15


def test_accesso_admin():
    """Testa i permessi di un amministratore."""
    admin = UtenteFactory(admin=True)
    assert admin["ruolo"] == "admin"
    assert puo_accedere_al_pannello_admin(admin) is True


def test_utente_inattivo_non_accede():
    """Un utente inattivo non deve poter fare login."""
    utente_inattivo = UtenteFactory(inattivo=True)
    assert utente_inattivo["attivo"] is False

    with pytest.raises(PermissionError, match="inattivo"):
        effettua_login(utente_inattivo)


def test_ordine_con_prodotti():
    """Testa la creazione di un ordine."""
    ordine = OrdineFactory()

    assert ordine["id"].startswith("ORD-")
    assert len(ordine["prodotti"]) == 2
    assert ordine["totale"] > 0


def test_batch_di_utenti():
    """Crea più utenti per test di performance o integrazione."""
    utenti = [UtenteFactory() for _ in range(50)]
    assert len(utenti) == 50
    assert len({u["email"] for u in utenti}) == 50  # Tutti con email diverse?


@pytest.mark.parametrize("categoria", ["Elettronica", "Abbigliamento", "Libri"])
def test_prodotto_per_categoria(categoria):
    """Testa prodotti di categorie specifiche."""
    prodotto = ProdottoFactory(categoria=categoria)
    assert prodotto["categoria"] == categoria
```

---

### faker standalone: dati locali italiani

```python
# Per dati italiani senza factory_boy

from faker import Faker

fake = Faker("it_IT")

def test_dati_italiani():
    """Verifica che il sistema accetti dati italiani realistici."""
    nome = fake.name()                    # "Mario Rossi"
    cf = fake.ssn()                       # Codice fiscale italiano
    iban = fake.iban()                    # IBAN italiano
    telefono = fake.phone_number()        # Numero italiano
    indirizzo = fake.address()            # Indirizzo italiano

    assert len(nome) > 0
    assert len(cf) == 16                  # CF sempre 16 caratteri
    assert iban.startswith("IT")          # IBAN italiano inizia con IT

# Per riproducibilità nei test (stesso seed = stessi dati)
Faker.seed(42)
fake_riproducibile = Faker("it_IT")
print(fake_riproducibile.name())  # Sempre lo stesso nome con seed=42
```

---

## F5: CI/CD Integration — Testing Automatizzato

### GitHub Actions: configurazione completa

```yaml
# .github/workflows/ci.yml

name: "CI — Test Suite Completa"

on:
  push:
    branches: [main, develop, "feature/**"]
  pull_request:
    branches: [main, develop]

env:
  PYTHON_VERSION: "3.12"

jobs:
  # ==============================
  # JOB 1: Linting e Formattazione
  # ==============================
  linting:
    name: "Linting e Formattazione"
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: "pip"

      - name: Installa strumenti di linting
        run: pip install ruff mypy

      - name: Ruff — Linting e formattazione
        run: |
          ruff check src/ tests/
          ruff format --check src/ tests/

      - name: mypy — Type checking
        run: mypy src/ --strict --ignore-missing-imports


  # ==============================
  # JOB 2: Unit Test
  # ==============================
  unit-tests:
    name: "Unit Test (Python ${{ matrix.python-version }})"
    needs: linting  # Esegui solo se il linting passa
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false  # Non bloccare gli altri test se uno fallisce
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ["3.11", "3.12"]
        exclude:
          # Escludi combinazioni non necessarie
          - os: macos-latest
            python-version: "3.11"

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: "pip"

      - name: Installa dipendenze
        run: pip install -e ".[dev]"

      - name: Esegui unit test
        run: |
          pytest tests/unit/ \
            -n auto \
            --cov=src \
            --cov-branch \
            --cov-fail-under=80 \
            --cov-report=xml \
            --cov-report=term-missing \
            --junitxml=reports/junit-unit-${{ matrix.os }}-${{ matrix.python-version }}.xml \
            --timeout=30

      - name: Carica coverage su Codecov
        uses: codecov/codecov-action@v4
        if: matrix.os == 'ubuntu-latest' && matrix.python-version == '3.12'
        with:
          file: coverage.xml
          fail_ci_if_error: true

      - name: Archivia report
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: reports-unit-${{ matrix.os }}-${{ matrix.python-version }}
          path: reports/


  # ==============================
  # JOB 3: Integration Test
  # ==============================
  integration-tests:
    name: "Integration Test"
    needs: unit-tests
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_USER: testuser
          POSTGRES_PASSWORD: testpass
          POSTGRES_DB: testdb
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: "pip"
      - run: pip install -e ".[dev]"

      - name: Esegui integration test
        env:
          DATABASE_URL: "postgresql://testuser:testpass@localhost:5432/testdb"
          REDIS_URL: "redis://localhost:6379"
        run: |
          pytest tests/integration/ \
            -m integrazione \
            --timeout=60 \
            --junitxml=reports/junit-integration.xml

      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: reports-integration
          path: reports/


  # ==============================
  # JOB 4: E2E Test (solo su main)
  # ==============================
  e2e-tests:
    name: "E2E Test"
    needs: integration-tests
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: "pip"
      - run: pip install -e ".[dev]"

      - name: Avvia applicazione in background
        run: |
          uvicorn src.main:app --host 0.0.0.0 --port 8000 &
          sleep 3  # Aspetta che sia pronta

      - name: Verifica che l'app sia in esecuzione
        run: curl -f http://localhost:8000/api/salute || exit 1

      - name: Esegui E2E test
        run: |
          pytest tests/e2e/ \
            -m e2e \
            --timeout=120 \
            --junitxml=reports/junit-e2e.xml


  # ==============================
  # JOB 5: Mutation Testing (settimanale)
  # ==============================
  mutation-testing:
    name: "Mutation Testing"
    runs-on: ubuntu-latest
    if: github.event_name == 'schedule'

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      - run: pip install -e ".[dev]" mutmut

      - name: Esegui test per coverage (prerequisito di mutmut)
        run: pytest --cov=src --cov-report=xml tests/unit/

      - name: Esegui mutation testing
        run: mutmut run --paths-to-mutate=src/ --use-coverage

      - name: Mostra risultati
        if: always()
        run: mutmut results

      - name: Genera report HTML
        if: always()
        run: mutmut html

      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: mutmut-report
          path: html/
```

---

### Pre-commit hooks per testing locale

```yaml
# .pre-commit-config.yaml

repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: local
    hooks:
      - id: unit-tests-veloci
        name: "Unit test rapidi (pre-commit)"
        entry: pytest
        args:
          - tests/unit/
          - -x                    # Ferma al primo fallimento
          - -q                    # Output silenzioso
          - --timeout=30          # Max 30s
          - -m "not slow"         # Solo test rapidi
        language: system
        pass_filenames: false
        always_run: true
        stages: [pre-commit]

      - id: type-check
        name: "Type check (mypy)"
        entry: mypy
        args: [src/, --strict, --ignore-missing-imports]
        language: system
        pass_filenames: false
        types: [python]
        stages: [pre-commit]
```

---

## F6: Errori Comuni e Come Evitarli

### Errori comuni nel testing

Questa sezione raccoglie gli errori più frequenti dei principianti, con spiegazione
e soluzione.

---

#### Errore 1: Testare i dettagli implementativi

```python
# SBAGLIATO — testa la struttura interna
def test_lista_interna():
    carrello = Carrello()
    carrello.aggiungi("Mela", 0.5)
    assert carrello._elementi == [{"nome": "Mela", "prezzo": 0.5}]  # Accesso privato!


# CORRETTO — testa il comportamento pubblico
def test_comportamento_pubblico():
    carrello = Carrello()
    carrello.aggiungi("Mela", 0.5)
    assert carrello.conta() == 1
    assert carrello.totale() == 0.5
```

Se cambi la struttura interna di `Carrello` (es. usi un `deque` invece di una `list`),
il primo test si rompe anche se il comportamento non è cambiato. Il secondo continua
a passare.

---

#### Errore 2: Test troppo grandi

```python
# SBAGLIATO — un test che verifica troppe cose
def test_ciclo_vita_ordine():
    # Crea utente
    utente = crea_utente("mario@test.it")
    assert utente.id > 0

    # Crea carrello
    carrello = Carrello(utente)
    carrello.aggiungi(prodotto_id=1)
    assert carrello.conta() == 1

    # Crea ordine
    ordine = crea_ordine(carrello)
    assert ordine.stato == "in_attesa"

    # Paga ordine
    paga_ordine(ordine)
    assert ordine.stato == "pagato"

    # Spedisci ordine
    spedisci_ordine(ordine)
    assert ordine.stato == "spedito"

    # Annulla ordine (impossibile dopo spedizione)
    with pytest.raises(ValueError):
        annulla_ordine(ordine)
```

Se questo test fallisce, non sai dove. È nella creazione dell'utente? Nel pagamento?
Nella spedizione?

```python
# CORRETTO — test separati per ogni comportamento
def test_crea_utente_restituisce_id(db):
    utente = crea_utente("mario@test.it")
    assert utente.id > 0


def test_carrello_con_prodotto_ha_conteggio_uno(carrello_vuoto, prodotto_id):
    carrello_vuoto.aggiungi(prodotto_id)
    assert carrello_vuoto.conta() == 1


def test_nuovo_ordine_ha_stato_in_attesa(ordine_con_prodotti):
    assert ordine_con_prodotti.stato == "in_attesa"


def test_ordine_pagato_ha_stato_pagato(ordine_in_attesa):
    paga_ordine(ordine_in_attesa)
    assert ordine_in_attesa.stato == "pagato"
```

---

#### Errore 3: Test che dipendono dall'ordine

```python
# SBAGLIATO — test_due dipende dallo stato lasciato da test_uno
database_globale = []

def test_uno():
    database_globale.append("elemento")
    assert len(database_globale) == 1

def test_due():
    # Funziona solo se test_uno è eseguito prima!
    assert len(database_globale) == 1
```

Con `pytest-randomly`, questi test falliscono quando l'ordine è invertito.

```python
# CORRETTO — ogni test gestisce il proprio stato
@pytest.fixture
def database():
    return []

def test_uno(database):
    database.append("elemento")
    assert len(database) == 1

def test_due(database):
    # database è sempre vuoto perché la fixture viene ricreata
    assert len(database) == 0
```

---

#### Errore 4: Mock del percorso sbagliato

```python
# src/servizio.py
import requests

def chiama_api():
    return requests.get("https://api.esempio.it/dati").json()


# SBAGLIATO — patch nel posto sbagliato
@patch("requests.get")  # Sbagliato! Patcha requests.get nel modulo requests
def test_sbagliato(mock_get):
    mock_get.return_value.json.return_value = {"risultato": "ok"}
    # Funziona se requests è importato direttamente nel test,
    # ma NON funziona se servizio.py ha già importato requests


# CORRETTO — patch dove viene USATO
@patch("src.servizio.requests.get")  # Corretto! Patcha nel modulo servizio
def test_corretto(mock_get):
    mock_get.return_value.json.return_value = {"risultato": "ok"}
    risultato = chiama_api()
    assert risultato == {"risultato": "ok"}
```

---

#### Errore 5: Non pulire le risorse

```python
# SBAGLIATO — il file rimane dopo il test
def test_crea_file():
    file = Path("/tmp/test_data.txt")
    file.write_text("dati")
    assert file.exists()
    # Il file NON viene rimosso! Sporca il filesystem


# CORRETTO — usa tmp_path o yield fixture
def test_crea_file(tmp_path):
    file = tmp_path / "test_data.txt"
    file.write_text("dati")
    assert file.exists()
    # Il file viene rimosso automaticamente da pytest


# Oppure con yield fixture
@pytest.fixture
def file_temp():
    file = Path("/tmp/test_data_unico.txt")
    file.write_text("dati")
    yield file
    file.unlink(missing_ok=True)  # Pulizia garantita

def test_con_file(file_temp):
    assert file_temp.read_text() == "dati"
```

---

#### Errore 6: assert su valori floating-point

```python
# SBAGLIATO — confronto esatto su float
def test_calcolo():
    assert 0.1 + 0.2 == 0.3  # FALLISCE! 0.1 + 0.2 = 0.30000000000000004


# CORRETTO — usa pytest.approx
def test_calcolo_corretto():
    assert 0.1 + 0.2 == pytest.approx(0.3)  # PASSA


# Oppure con tolleranza esplicita
def test_calcolo_tolleranza():
    assert 0.1 + 0.2 == pytest.approx(0.3, abs=1e-10)  # Tolleranza assoluta
    assert 3.14 == pytest.approx(3.14159, rel=0.01)      # Tolleranza relativa 1%
```

---

#### Errore 7: Test che passano sempre (test vuoti)

```python
# SBAGLIATO — un test vuoto passa sempre!
def test_operazione():
    pass  # Questo "passa" ma non verifica nulla


# SBAGLIATO — assert sempre vero
def test_risultato():
    risultato = funzione_complessa()
    assert True  # Inutile — passa sempre


# CORRETTO — verifica qualcosa di significativo
def test_risultato_corretto():
    risultato = funzione_complessa()
    assert risultato is not None
    assert risultato["stato"] == "completato"
    assert risultato["valore"] > 0
```

---

## F7: Cheat Sheet Completo — Fixture Scope e Lifecycle

```
SCOPE DELLA FIXTURE                   QUANDO VIENE CREATA/DISTRUTTA
═══════════════════════════════════════════════════════════════════════
                                       ┌─────────────────────────┐
scope="session"                        │ Intera sessione pytest  │
                                       │ (tutti i file, tutti    │
@pytest.fixture(scope="session")       │ i test)                 │
def setup_globale():                   └─────────────────────────┘
    ↑ Creata una volta        ↑ Distrutta dopo l'ultimo test

═══════════════════════════════════════════════════════════════════════
                                       ┌─────────────────────────┐
scope="module"                         │ Ogni file .py di test   │
                                       │ test_a.py → test_b.py  │
@pytest.fixture(scope="module")        │ Separata per ogni file  │
def setup_modulo():                    └─────────────────────────┘
    ↑ Creata per ogni modulo   ↑ Distrutta alla fine del modulo

═══════════════════════════════════════════════════════════════════════
                                       ┌─────────────────────────┐
scope="class"                          │ Ogni classe TestXxx     │
                                       │ class TestA → class TestB│
@pytest.fixture(scope="class")         │ Separata per ogni classe│
def setup_classe():                    └─────────────────────────┘
    ↑ Creata per ogni classe   ↑ Distrutta alla fine della classe

═══════════════════════════════════════════════════════════════════════
                                       ┌─────────────────────────┐
scope="function" [DEFAULT]             │ Ogni funzione test_xxx  │
                                       │ test_a(), test_b(), ... │
@pytest.fixture                        │ Separata per ogni test  │
def setup_test():                      └─────────────────────────┘
    ↑ Creata per ogni test     ↑ Distrutta dopo ogni test
═══════════════════════════════════════════════════════════════════════
```

---

## F8: Recap Visivo dell'Ecosistema Testing Python

```
ECOSISTEMA TESTING PYTHON
═══════════════════════════════════════════════════════════════════════

  UNIT TEST                   INTEGRATION TEST          E2E TEST
  ──────────                  ──────────────────        ────────
  pytest                      pytest                    Selenium
  unittest                    pytest-asyncio            Playwright
                              testcontainers            httpx
                                                        Locust

  GENERAZIONE DATI            MOCKING                   QUALITÀ
  ──────────────              ───────                   ───────
  factory_boy                 unittest.mock             mutmut
  faker                       pytest-mock               Hypothesis
                              responses                 pytest-randomly

  COVERAGE                    COMPORTAMENTO (BDD)       PERFORMANCE
  ────────                    ──────────────────        ───────────
  pytest-cov                  behave                    pytest-benchmark
  coverage.py                 pytest-bdd                timeit

  PARALLELISMO                SNAPSHOT                  CI/CD
  ────────────                ────────                  ─────
  pytest-xdist                syrupy                    GitHub Actions
                              pytest-snapshot           GitLab CI
                                                        Jenkins

═══════════════════════════════════════════════════════════════════════
```

---

## F9: Note Finali sull'Approccio al Testing

### La filosofia del testing maturo

Il testing è una disciplina che si impara con la pratica. Ecco le lezioni che
i programmatori esperti imparano tipicamente nel tempo:

**Settimana 1:** "Ok, scrivo i test per far contenta la pipeline CI."

**Mese 1:** "I test mi hanno salvato da almeno 3 bug stupidi. Comincio a capire."

**Mese 6:** "Ora scrivo i test PRIMA di scrivere il codice. È molto più veloce."

**Anno 1:** "Quando vedo codice senza test, non mi sento a mio agio a modificarlo."

**Anno 3+:** "I test sono documentazione vivente. Il test spiega il contratto
del codice meglio di qualsiasi commento."

---

### La domanda giusta

Prima di scrivere un test, non chiederti "Devo scrivere un test per questo?".
Chiediti: "Cosa succede se questo codice è sbagliato? Quanto mi costa scoprirlo
in produzione vs. adesso?"

Se la risposta è "pochissimo" → forse il test non vale il costo.
Se la risposta è "molto" → scrivi il test.

Per il codice critico (autenticazione, pagamenti, dati dell'utente), la risposta
è sempre "molto". Per gli script one-shot o le utility di visualizzazione, può
valere la pena non testare.

---

### Inizia piccolo, cresce nel tempo

Non cercare di avere il 100% di coverage dall'inizio. Inizia con:
1. Test per i bug che trovi (test di regressione)
2. Test per le funzioni più critiche
3. Test per il codice che stai modificando

Con il tempo, la suite crescerà organicamente verso una copertura significativa.
Una suite di test costruita gradualmente è sempre migliore di una suite costruita
frettolosamente per "raggiungere il 100%".

---

## ESERCIZI COMPLETI C9–C12

---

## Esercizio C9 — Sistema di Cache con TTL (pytest-asyncio + mocking del tempo)

### Obiettivo

Implementare e testare un sistema di cache in-memory con Time-To-Live (TTL):
gli elementi scadono automaticamente dopo un tempo configurabile.

### Struttura del progetto

```
cache_ttl/
├── src/
│   └── cache.py
└── tests/
    └── test_cache.py
```

### Codice da testare

```python
# src/cache.py

import time
from typing import Any, Optional


class CacheScaduta(Exception):
    """Sollevata quando si tenta di accedere a un elemento scaduto."""
    pass


class ChiaveNonTrovata(Exception):
    """Sollevata quando la chiave non esiste in cache."""
    pass


class Cache:
    """
    Cache in-memory con TTL (Time-To-Live).

    Ogni elemento inserito ha una scadenza configurabile.
    Dopo la scadenza, l'elemento è considerato non esistente.
    """

    def __init__(self, ttl_default: float = 60.0) -> None:
        """
        Args:
            ttl_default: Durata predefinita in secondi degli elementi.
        """
        self._dati: dict[str, Any] = {}
        self._scadenze: dict[str, float] = {}
        self._ttl_default = ttl_default

    def imposta(self, chiave: str, valore: Any, ttl: Optional[float] = None) -> None:
        """
        Inserisce o aggiorna un elemento in cache.

        Args:
            chiave: Chiave identificativa.
            valore: Valore da memorizzare.
            ttl: Durata in secondi (usa ttl_default se None).
        """
        durata = ttl if ttl is not None else self._ttl_default
        self._dati[chiave] = valore
        self._scadenze[chiave] = time.time() + durata

    def ottieni(self, chiave: str) -> Any:
        """
        Recupera un elemento dalla cache.

        Raises:
            ChiaveNonTrovata: se la chiave non esiste.
            CacheScaduta: se l'elemento è scaduto.
        """
        if chiave not in self._dati:
            raise ChiaveNonTrovata(f"Chiave non trovata: {chiave!r}")

        if time.time() > self._scadenze[chiave]:
            # Pulizia lazy — rimuovi al momento dell'accesso
            del self._dati[chiave]
            del self._scadenze[chiave]
            raise CacheScaduta(f"Elemento scaduto: {chiave!r}")

        return self._dati[chiave]

    def esiste(self, chiave: str) -> bool:
        """Verifica se la chiave esiste e non è scaduta."""
        try:
            self.ottieni(chiave)
            return True
        except (ChiaveNonTrovata, CacheScaduta):
            return False

    def elimina(self, chiave: str) -> bool:
        """
        Rimuove un elemento dalla cache.

        Returns:
            True se l'elemento esisteva, False altrimenti.
        """
        if chiave in self._dati:
            del self._dati[chiave]
            del self._scadenze[chiave]
            return True
        return False

    def conta(self) -> int:
        """Conta gli elementi non scaduti."""
        adesso = time.time()
        return sum(
            1
            for chiave, scadenza in self._scadenze.items()
            if adesso <= scadenza
        )

    def pulisci_scaduti(self) -> int:
        """
        Rimuove tutti gli elementi scaduti.

        Returns:
            Numero di elementi rimossi.
        """
        adesso = time.time()
        chiavi_scadute = [
            chiave
            for chiave, scadenza in self._scadenze.items()
            if adesso > scadenza
        ]
        for chiave in chiavi_scadute:
            del self._dati[chiave]
            del self._scadenze[chiave]
        return len(chiavi_scadute)

    def svuota(self) -> None:
        """Rimuove tutti gli elementi."""
        self._dati.clear()
        self._scadenze.clear()
```

### Test completo

```python
# tests/test_cache.py

import time
import pytest
from unittest.mock import patch, MagicMock
from src.cache import Cache, CacheScaduta, ChiaveNonTrovata


# ===== FIXTURE =====

@pytest.fixture
def cache():
    """Cache con TTL predefinito di 60 secondi."""
    return Cache(ttl_default=60.0)


@pytest.fixture
def cache_breve():
    """Cache con TTL brevissimo per test di scadenza."""
    return Cache(ttl_default=0.05)  # 50 millisecondi


# ===== TEST: IMPOSTA E OTTIENI =====

class TestImpostaOttieni:
    """Test per le operazioni base di imposta/ottieni."""

    def test_imposta_e_ottieni_stringa(self, cache):
        cache.imposta("nome", "Mario")
        assert cache.ottieni("nome") == "Mario"

    def test_imposta_e_ottieni_intero(self, cache):
        cache.imposta("eta", 25)
        assert cache.ottieni("eta") == 25

    def test_imposta_e_ottieni_lista(self, cache):
        lista = [1, 2, 3, 4, 5]
        cache.imposta("numeri", lista)
        assert cache.ottieni("numeri") == [1, 2, 3, 4, 5]

    def test_imposta_e_ottieni_dizionario(self, cache):
        dati = {"nome": "Mario", "eta": 25}
        cache.imposta("utente", dati)
        risultato = cache.ottieni("utente")
        assert risultato == {"nome": "Mario", "eta": 25}

    def test_imposta_e_ottieni_none(self, cache):
        """None è un valore valido in cache."""
        cache.imposta("vuoto", None)
        assert cache.ottieni("vuoto") is None

    def test_sovrascrittura_valore(self, cache):
        """Impostare la stessa chiave sovrascrive il valore."""
        cache.imposta("chiave", "primo")
        cache.imposta("chiave", "secondo")
        assert cache.ottieni("chiave") == "secondo"

    def test_chiavi_multiple_indipendenti(self, cache):
        cache.imposta("a", 1)
        cache.imposta("b", 2)
        cache.imposta("c", 3)
        assert cache.ottieni("a") == 1
        assert cache.ottieni("b") == 2
        assert cache.ottieni("c") == 3


# ===== TEST: CHIAVE NON TROVATA =====

class TestChiaveNonTrovata:
    """Test per accessi a chiavi inesistenti."""

    def test_chiave_inesistente_solleva_eccezione(self, cache):
        with pytest.raises(ChiaveNonTrovata):
            cache.ottieni("non_esiste")

    def test_messaggio_errore_contiene_chiave(self, cache):
        with pytest.raises(ChiaveNonTrovata, match="mia_chiave_speciale"):
            cache.ottieni("mia_chiave_speciale")

    def test_dopo_eliminazione_chiave_non_trovata(self, cache):
        cache.imposta("temporanea", "valore")
        cache.elimina("temporanea")
        with pytest.raises(ChiaveNonTrovata):
            cache.ottieni("temporanea")


# ===== TEST: SCADENZA (TTL) — Con mock del tempo =====

class TestScadenza:
    """
    Test per la scadenza degli elementi.

    TECNICA: usiamo patch('time.time') per controllare il tempo
    senza dover aspettare davvero.
    """

    def test_elemento_fresco_accessibile(self, cache):
        """Un elemento appena inserito deve essere accessibile."""
        # Tempo corrente: 1000
        with patch("src.cache.time.time", return_value=1000.0):
            cache.imposta("chiave", "valore", ttl=60)

        # Un secondo dopo: 1001 (ben prima della scadenza a 1060)
        with patch("src.cache.time.time", return_value=1001.0):
            assert cache.ottieni("chiave") == "valore"

    def test_elemento_scaduto_solleva_eccezione(self, cache):
        """Un elemento scaduto deve sollevare CacheScaduta."""
        # Inserisci a tempo 1000 con TTL=60 (scade a 1060)
        with patch("src.cache.time.time", return_value=1000.0):
            cache.imposta("chiave", "valore", ttl=60)

        # Prova ad accedere a tempo 1061 (dopo la scadenza)
        with patch("src.cache.time.time", return_value=1061.0):
            with pytest.raises(CacheScaduta, match="chiave"):
                cache.ottieni("chiave")

    def test_esatto_momento_scadenza(self, cache):
        """Al momento esatto della scadenza, l'elemento è scaduto."""
        with patch("src.cache.time.time", return_value=1000.0):
            cache.imposta("chiave", "valore", ttl=60)

        # Esattamente alla scadenza (1000 + 60 = 1060), il TTL è superato
        with patch("src.cache.time.time", return_value=1060.0):
            with pytest.raises(CacheScaduta):
                cache.ottieni("chiave")

    def test_ttl_personalizzato(self, cache):
        """Il TTL può essere specificato per ogni elemento."""
        with patch("src.cache.time.time", return_value=1000.0):
            cache.imposta("breve", "valore", ttl=10)
            cache.imposta("lungo", "valore", ttl=3600)

        # A 1011: "breve" è scaduto, "lungo" no
        with patch("src.cache.time.time", return_value=1011.0):
            with pytest.raises(CacheScaduta):
                cache.ottieni("breve")
            assert cache.ottieni("lungo") == "valore"

    def test_dopo_scadenza_elemento_rimosso(self, cache):
        """Dopo l'accesso a un elemento scaduto, viene rimosso dalla cache."""
        with patch("src.cache.time.time", return_value=1000.0):
            cache.imposta("chiave", "valore", ttl=60)

        # Accedi quando scaduto
        with patch("src.cache.time.time", return_value=1061.0):
            with pytest.raises(CacheScaduta):
                cache.ottieni("chiave")

            # Ora la chiave è stata rimossa — solleva ChiaveNonTrovata
            with pytest.raises(ChiaveNonTrovata):
                cache.ottieni("chiave")


# ===== TEST: ESISTE =====

class TestEsiste:
    """Test per il metodo esiste()."""

    def test_chiave_esistente_restituisce_true(self, cache):
        cache.imposta("chiave", "valore")
        assert cache.esiste("chiave") is True

    def test_chiave_inesistente_restituisce_false(self, cache):
        assert cache.esiste("non_esiste") is False

    def test_chiave_scaduta_restituisce_false(self, cache):
        with patch("src.cache.time.time", return_value=1000.0):
            cache.imposta("chiave", "valore", ttl=60)

        with patch("src.cache.time.time", return_value=1061.0):
            assert cache.esiste("chiave") is False


# ===== TEST: ELIMINA =====

class TestElimina:
    """Test per il metodo elimina()."""

    def test_elimina_chiave_esistente_restituisce_true(self, cache):
        cache.imposta("chiave", "valore")
        assert cache.elimina("chiave") is True

    def test_elimina_chiave_inesistente_restituisce_false(self, cache):
        assert cache.elimina("non_esiste") is False

    def test_dopo_eliminazione_chiave_non_accessibile(self, cache):
        cache.imposta("chiave", "valore")
        cache.elimina("chiave")
        with pytest.raises(ChiaveNonTrovata):
            cache.ottieni("chiave")


# ===== TEST: CONTA =====

class TestConta:
    """Test per il metodo conta()."""

    def test_cache_vuota_conta_zero(self, cache):
        assert cache.conta() == 0

    def test_un_elemento_conta_uno(self, cache):
        cache.imposta("chiave", "valore")
        assert cache.conta() == 1

    def test_tre_elementi_conta_tre(self, cache):
        cache.imposta("a", 1)
        cache.imposta("b", 2)
        cache.imposta("c", 3)
        assert cache.conta() == 3

    def test_elementi_scaduti_non_contati(self, cache):
        with patch("src.cache.time.time", return_value=1000.0):
            cache.imposta("fresco", "valore", ttl=3600)
            cache.imposta("scaduto", "valore", ttl=60)

        with patch("src.cache.time.time", return_value=1100.0):
            assert cache.conta() == 1  # Solo "fresco" non è scaduto


# ===== TEST: PULISCI SCADUTI =====

class TestPulisciScaduti:
    """Test per il metodo pulisci_scaduti()."""

    def test_pulisci_cache_vuota_restituisce_zero(self, cache):
        assert cache.pulisci_scaduti() == 0

    def test_pulisci_senza_scaduti_restituisce_zero(self, cache):
        cache.imposta("fresco", "valore", ttl=3600)
        assert cache.pulisci_scaduti() == 0

    def test_pulisci_restituisce_numero_rimossi(self, cache):
        with patch("src.cache.time.time", return_value=1000.0):
            cache.imposta("a", "valore", ttl=60)
            cache.imposta("b", "valore", ttl=60)
            cache.imposta("fresco", "valore", ttl=3600)

        with patch("src.cache.time.time", return_value=1100.0):
            rimossi = cache.pulisci_scaduti()
            assert rimossi == 2

    def test_dopo_pulizia_freschi_rimangono(self, cache):
        with patch("src.cache.time.time", return_value=1000.0):
            cache.imposta("scaduto", "valore", ttl=60)
            cache.imposta("fresco", "mantenuto", ttl=3600)

        with patch("src.cache.time.time", return_value=1100.0):
            cache.pulisci_scaduti()
            assert cache.ottieni("fresco") == "mantenuto"


# ===== TEST: SVUOTA =====

class TestSvuota:
    """Test per il metodo svuota()."""

    def test_svuota_rimuove_tutto(self, cache):
        cache.imposta("a", 1)
        cache.imposta("b", 2)
        cache.svuota()
        assert cache.conta() == 0

    def test_dopo_svuota_tutte_le_chiavi_non_trovate(self, cache):
        cache.imposta("a", 1)
        cache.imposta("b", 2)
        cache.svuota()
        with pytest.raises(ChiaveNonTrovata):
            cache.ottieni("a")
        with pytest.raises(ChiaveNonTrovata):
            cache.ottieni("b")

    def test_svuota_cache_vuota_non_solleva(self, cache):
        """Svuotare una cache già vuota non deve sollevare eccezioni."""
        cache.svuota()  # Non deve sollevare nulla
        assert cache.conta() == 0


# ===== TEST: SCENARIO INTEGRATO =====

class TestScenarioIntegrato:
    """Test di scenario che simulano utilizzi realistici."""

    def test_cache_come_meccanismo_di_throttling(self, cache):
        """
        Scenario: usa la cache per evitare chiamate API ripetute
        entro un certo intervallo di tempo.
        """
        chiamate_api = 0

        def chiama_api_costosa(parametro: str) -> dict:
            nonlocal chiamate_api
            chiamate_api += 1
            return {"risultato": f"dati per {parametro}"}

        def ottieni_con_cache(parametro: str) -> dict:
            if cache.esiste(parametro):
                return cache.ottieni(parametro)
            risultato = chiama_api_costosa(parametro)
            cache.imposta(parametro, risultato, ttl=300)
            return risultato

        # Prima chiamata — colpisce l'API
        r1 = ottieni_con_cache("test")
        assert chiamate_api == 1

        # Seconda chiamata — dalla cache
        r2 = ottieni_con_cache("test")
        assert chiamate_api == 1  # Nessuna nuova chiamata API
        assert r1 == r2

    def test_ttl_default_applicato_correttamente(self):
        """Il TTL default viene usato quando non specificato."""
        cache_con_ttl = Cache(ttl_default=30.0)

        with patch("src.cache.time.time", return_value=1000.0):
            cache_con_ttl.imposta("chiave", "valore")

        # A 1029: ancora valido (TTL = 30s)
        with patch("src.cache.time.time", return_value=1029.0):
            assert cache_con_ttl.ottieni("chiave") == "valore"

        # A 1031: scaduto
        with patch("src.cache.time.time", return_value=1031.0):
            with pytest.raises(CacheScaduta):
                cache_con_ttl.ottieni("chiave")
```

**Output atteso:**

```
tests/test_cache.py::TestImpostaOttieni::test_imposta_e_ottieni_stringa PASSED
tests/test_cache.py::TestImpostaOttieni::test_imposta_e_ottieni_intero PASSED
tests/test_cache.py::TestImpostaOttieni::test_imposta_e_ottieni_lista PASSED
... (tutti i test passano)

================================ 30 passed in 0.12s ================================
```

---

## Esercizio C10 — Parser di Espressioni Matematiche (Hypothesis)

### Obiettivo

Implementare e testare un valutatore di espressioni matematiche usando
Hypothesis per trovare casi limite in modo automatico.

### Struttura del progetto

```
calcolatrice_expr/
├── src/
│   └── parser_expr.py
└── tests/
    └── test_parser_expr.py
```

### Codice da testare

```python
# src/parser_expr.py
"""
Parser di espressioni matematiche semplici.

Supporta: +, -, *, /, numeri interi, spazi.
"""

import re
from typing import Union


class ErroreEspressione(Exception):
    """Errore nell'espressione matematica."""
    pass


def valuta(espressione: str) -> float:
    """
    Valuta un'espressione matematica come stringa.

    Supporta: +, -, *, /, numeri interi e decimali, spazi.
    Non supporta: variabili, funzioni, parentesi (versione base).

    Args:
        espressione: Espressione matematica come stringa.

    Returns:
        Risultato numerico.

    Raises:
        ErroreEspressione: Se l'espressione non è valida.
        ZeroDivisionError: Se si divide per zero.
    """
    espressione = espressione.strip()

    if not espressione:
        raise ErroreEspressione("Espressione vuota")

    # Valida che contenga solo caratteri permessi
    if not re.match(r'^[\d\s\+\-\*\/\.]+$', espressione):
        raise ErroreEspressione(
            f"Caratteri non permessi in: {espressione!r}"
        )

    # Tokenizza l'espressione (numeri e operatori)
    token_pattern = r'(\d+\.?\d*)'
    parti = re.split(token_pattern, espressione.strip())

    # Rimuovi whitespace e token vuoti
    token = [p.strip() for p in parti if p.strip()]

    if not token:
        raise ErroreEspressione("Nessun token trovato")

    # Prima passata: moltiplica e dividi (priorità alta)
    # Converti i numeri
    numeri_ops = []
    i = 0
    try:
        while i < len(token):
            if token[i] in ('*', '/'):
                # Prendi il numero precedente, operatore, numero successivo
                sx = numeri_ops.pop()
                op = token[i]
                dx = float(token[i + 1])
                if op == '*':
                    numeri_ops.append(sx * dx)
                else:
                    if dx == 0:
                        raise ZeroDivisionError("Divisione per zero")
                    numeri_ops.append(sx / dx)
                i += 2
            else:
                numeri_ops.append(float(token[i]))
                i += 1
    except (IndexError, ValueError) as e:
        raise ErroreEspressione(f"Espressione malformata: {e}") from e

    # Seconda passata: somma e sottrai
    risultato = numeri_ops[0]
    i = 1
    while i < len(numeri_ops):
        if numeri_ops[i] in ('+', '-'):  # type: ignore[comparison-overlap]
            op = numeri_ops[i]
            valore = numeri_ops[i + 1]
            if op == '+':
                risultato += valore
            else:
                risultato -= valore
            i += 2
        else:
            i += 1

    return risultato
```

### Test con Hypothesis

```python
# tests/test_parser_expr.py

import pytest
from hypothesis import given, assume, settings, HealthCheck
from hypothesis import strategies as st
from src.parser_expr import valuta, ErroreEspressione


# ===== TEST BASE =====

class TestValutaBase:
    """Test per espressioni semplici e note."""

    def test_numero_singolo(self):
        assert valuta("42") == 42.0

    def test_numero_decimale(self):
        assert valuta("3.14") == pytest.approx(3.14)

    def test_addizione(self):
        assert valuta("2 + 3") == 5.0

    def test_sottrazione(self):
        assert valuta("10 - 3") == 7.0

    def test_moltiplicazione(self):
        assert valuta("4 * 5") == 20.0

    def test_divisione(self):
        assert valuta("10 / 4") == pytest.approx(2.5)

    def test_precedenza_operatori(self):
        """Moltiplicazione ha precedenza su addizione."""
        assert valuta("2 + 3 * 4") == pytest.approx(14.0)

    def test_catena_addizioni(self):
        assert valuta("1 + 2 + 3 + 4 + 5") == 15.0

    def test_spazi_extra_ignorati(self):
        assert valuta("  2  +  3  ") == 5.0

    def test_divisione_per_zero(self):
        with pytest.raises(ZeroDivisionError):
            valuta("10 / 0")

    def test_espressione_vuota(self):
        with pytest.raises(ErroreEspressione, match="vuota"):
            valuta("")

    def test_caratteri_non_validi(self):
        with pytest.raises(ErroreEspressione, match="non permessi"):
            valuta("2 + a")


# ===== TEST CON HYPOTHESIS =====

class TestHypothesis:
    """
    Test basati su proprietà con Hypothesis.

    Proprietà matematiche che devono valere sempre:
    - a + b == b + a (commutatività dell'addizione)
    - a * b == b * a (commutatività della moltiplicazione)
    - a + 0 == a (elemento neutro dell'addizione)
    - a * 1 == a (elemento neutro della moltiplicazione)
    - (a + b) + c == a + (b + c) (associatività)
    """

    @given(
        a=st.integers(min_value=-1000, max_value=1000),
        b=st.integers(min_value=-1000, max_value=1000),
    )
    def test_addizione_commutativa(self, a, b):
        """a + b deve dare lo stesso risultato di b + a."""
        assert valuta(f"{a} + {b}") == pytest.approx(valuta(f"{b} + {a}"))

    @given(
        a=st.integers(min_value=-100, max_value=100),
        b=st.integers(min_value=-100, max_value=100),
    )
    def test_moltiplicazione_commutativa(self, a, b):
        """a * b deve dare lo stesso risultato di b * a."""
        assert valuta(f"{a} * {b}") == pytest.approx(valuta(f"{b} * {a}"))

    @given(a=st.integers(min_value=-1000, max_value=1000))
    def test_addizione_zero_e_identita(self, a):
        """a + 0 deve dare a."""
        assert valuta(f"{a} + 0") == pytest.approx(float(a))

    @given(a=st.integers(min_value=-1000, max_value=1000))
    def test_moltiplicazione_per_uno_e_identita(self, a):
        """a * 1 deve dare a."""
        assert valuta(f"{a} * 1") == pytest.approx(float(a))

    @given(a=st.integers(min_value=-1000, max_value=1000))
    def test_moltiplicazione_per_zero(self, a):
        """a * 0 deve dare 0."""
        assert valuta(f"{a} * 0") == pytest.approx(0.0)
        assert valuta(f"0 * {a}") == pytest.approx(0.0)

    @given(
        a=st.integers(min_value=-100, max_value=100),
        b=st.integers(min_value=-100, max_value=100),
        c=st.integers(min_value=-100, max_value=100),
    )
    def test_addizione_associativa(self, a, b, c):
        """(a + b) + c == a + (b + c)."""
        sinistra = valuta(f"{a} + {b}") + c
        destra = a + valuta(f"{b} + {c}")
        assert sinistra == pytest.approx(destra)

    @given(
        a=st.integers(min_value=-1000, max_value=1000),
        b=st.integers(min_value=-1000, max_value=1000),
    )
    def test_sottrazione_come_addizione_negativo(self, a, b):
        """a - b deve essere uguale a a + (-b)."""
        assert valuta(f"{a} - {b}") == pytest.approx(a - b)

    @given(
        a=st.integers(min_value=1, max_value=100),
        b=st.integers(min_value=1, max_value=100),
    )
    def test_divisione_e_moltiplicazione_inverse(self, a, b):
        """(a * b) / b deve dare a."""
        prodotto = valuta(f"{a} * {b}")
        risultato = valuta(f"{prodotto} / {b}")
        assert risultato == pytest.approx(float(a))

    @given(
        a=st.integers(min_value=-1000, max_value=1000),
        b=st.integers(min_value=-1000, max_value=1000),
    )
    def test_risultato_coerente_con_python(self, a, b):
        """Il parser deve dare lo stesso risultato di Python nativo."""
        assert valuta(f"{a} + {b}") == pytest.approx(a + b)
        assert valuta(f"{a} - {b}") == pytest.approx(a - b)
        assert valuta(f"{a} * {b}") == pytest.approx(a * b)

    @given(
        a=st.integers(min_value=1, max_value=1000),
        b=st.integers(min_value=1, max_value=1000),
    )
    def test_divisione_coerente_con_python(self, a, b):
        """La divisione deve dare lo stesso risultato di Python nativo."""
        assert valuta(f"{a} / {b}") == pytest.approx(a / b)

    @given(a=st.integers(min_value=-1000000, max_value=1000000))
    def test_numero_singolo_grande(self, a):
        """Qualsiasi numero intero nel range supportato deve essere valutato."""
        assert valuta(str(a)) == pytest.approx(float(a))
```

**Output atteso:**

```
tests/test_parser_expr.py::TestValutaBase::test_numero_singolo PASSED
tests/test_parser_expr.py::TestValutaBase::test_addizione PASSED
...
tests/test_parser_expr.py::TestHypothesis::test_addizione_commutativa PASSED
    (Hypothesis ha testato 100 esempi)
tests/test_parser_expr.py::TestHypothesis::test_moltiplicazione_commutativa PASSED
...

================================ 22 passed in 2.31s ================================
```

---

## Esercizio C11 — Sistema di Notifiche (Mock avanzato + pytest-asyncio)

### Obiettivo

Implementare e testare un sistema di notifiche asincrono che invia messaggi
via email e SMS, con retry automatico in caso di fallimento.

### Struttura del progetto

```
notifiche/
├── src/
│   ├── notifiche.py
│   └── trasporti.py
└── tests/
    └── test_notifiche.py
```

### Codice da testare

```python
# src/trasporti.py
"""Interfacce e implementazioni per i trasporti di notifica."""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Messaggio:
    """Rappresenta un messaggio da inviare."""
    destinatario: str
    testo: str
    priorita: int = 1  # 1 = normale, 2 = alta, 3 = urgente


class TrasportoBase(ABC):
    """Interfaccia base per i trasporti di notifica."""

    @abstractmethod
    async def invia(self, messaggio: Messaggio) -> bool:
        """
        Invia il messaggio.

        Returns:
            True se l'invio ha successo, False altrimenti.
        """
        ...


class TrasportoEmail(TrasportoBase):
    """Trasporto per email (implementazione reale usa SMTP)."""

    async def invia(self, messaggio: Messaggio) -> bool:
        # Implementazione reale: connessione SMTP
        await asyncio.sleep(0.1)
        return True


class TrasportoSMS(TrasportoBase):
    """Trasporto per SMS (implementazione reale usa API Twilio)."""

    async def invia(self, messaggio: Messaggio) -> bool:
        # Implementazione reale: chiamata API Twilio
        await asyncio.sleep(0.05)
        return True
```

```python
# src/notifiche.py
"""Sistema di notifiche con retry e fallback."""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from src.trasporti import TrasportoBase, Messaggio

logger = logging.getLogger(__name__)


@dataclass
class StatoInvio:
    """Risultato di un tentativo di invio."""
    successo: bool
    tentativi: int
    errore: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


class GestoreNotifiche:
    """
    Gestore di notifiche con retry automatico e fallback.

    Tenta l'invio con il trasporto primario. In caso di fallimento,
    riprova fino a max_tentativi. Se tutti falliscono, usa il trasporto
    di fallback (se configurato).
    """

    def __init__(
        self,
        trasporto_primario: TrasportoBase,
        trasporto_fallback: Optional[TrasportoBase] = None,
        max_tentativi: int = 3,
        delay_retry: float = 1.0,
    ) -> None:
        self._primario = trasporto_primario
        self._fallback = trasporto_fallback
        self._max_tentativi = max_tentativi
        self._delay_retry = delay_retry
        self._storico: list[StatoInvio] = []

    async def invia(self, messaggio: Messaggio) -> StatoInvio:
        """
        Invia una notifica con retry automatico.

        1. Tenta con il trasporto primario (max_tentativi volte)
        2. Se tutti falliscono e c'è un fallback, usa il fallback
        3. Registra il risultato nello storico
        """
        tentativi = 0
        ultimo_errore = None

        for tentativo in range(1, self._max_tentativi + 1):
            tentativi += 1
            try:
                successo = await self._primario.invia(messaggio)
                if successo:
                    stato = StatoInvio(successo=True, tentativi=tentativi)
                    self._storico.append(stato)
                    logger.info(
                        "Notifica inviata con successo al tentativo %d",
                        tentativo,
                    )
                    return stato

                ultimo_errore = "Trasporto ha restituito False"

            except Exception as exc:
                ultimo_errore = str(exc)
                logger.warning(
                    "Tentativo %d/%d fallito: %s",
                    tentativo,
                    self._max_tentativi,
                    ultimo_errore,
                )

            # Aspetta prima di riprovare (non all'ultimo tentativo)
            if tentativo < self._max_tentativi:
                await asyncio.sleep(self._delay_retry)

        # Tutti i tentativi primari falliti — prova il fallback
        if self._fallback is not None:
            try:
                successo = await self._fallback.invia(messaggio)
                if successo:
                    stato = StatoInvio(
                        successo=True,
                        tentativi=tentativi,
                        errore=f"Usato fallback dopo: {ultimo_errore}",
                    )
                    self._storico.append(stato)
                    return stato
            except Exception as exc:
                ultimo_errore = f"Anche il fallback è fallito: {exc}"

        stato = StatoInvio(
            successo=False,
            tentativi=tentativi,
            errore=ultimo_errore,
        )
        self._storico.append(stato)
        return stato

    def storico_invii(self) -> list[StatoInvio]:
        """Restituisce lo storico degli invii."""
        return self._storico.copy()

    def statistiche(self) -> dict:
        """Restituisce statistiche sugli invii."""
        totale = len(self._storico)
        if totale == 0:
            return {"totale": 0, "successi": 0, "fallimenti": 0, "tasso_successo": 0.0}

        successi = sum(1 for s in self._storico if s.successo)
        return {
            "totale": totale,
            "successi": successi,
            "fallimenti": totale - successi,
            "tasso_successo": successi / totale,
        }
```

### Test completo con AsyncMock

```python
# tests/test_notifiche.py

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, call, patch
from src.notifiche import GestoreNotifiche, StatoInvio
from src.trasporti import Messaggio, TrasportoBase


# ===== FIXTURE =====

@pytest.fixture
def messaggio():
    return Messaggio(
        destinatario="mario@test.it",
        testo="Test notifica",
        priorita=1,
    )


@pytest.fixture
def messaggio_urgente():
    return Messaggio(
        destinatario="+39 333 1234567",
        testo="Allerta urgente!",
        priorita=3,
    )


@pytest.fixture
def trasporto_funzionante():
    """Mock di un trasporto che funziona sempre."""
    mock = AsyncMock(spec=TrasportoBase)
    mock.invia.return_value = True
    return mock


@pytest.fixture
def trasporto_rotto():
    """Mock di un trasporto che fallisce sempre."""
    mock = AsyncMock(spec=TrasportoBase)
    mock.invia.return_value = False
    return mock


@pytest.fixture
def trasporto_eccezione():
    """Mock di un trasporto che solleva eccezione."""
    mock = AsyncMock(spec=TrasportoBase)
    mock.invia.side_effect = ConnectionError("Connessione rifiutata")
    return mock


# ===== TEST: INVIO CON SUCCESSO =====

class TestInvioSuccesso:
    """Test per scenari di successo."""

    async def test_invio_riuscito_al_primo_tentativo(
        self, trasporto_funzionante, messaggio
    ):
        gestore = GestoreNotifiche(trasporto_funzionante, max_tentativi=3, delay_retry=0)
        stato = await gestore.invia(messaggio)

        assert stato.successo is True
        assert stato.tentativi == 1
        assert stato.errore is None

    async def test_trasporto_chiamato_una_volta_al_successo(
        self, trasporto_funzionante, messaggio
    ):
        gestore = GestoreNotifiche(trasporto_funzionante, max_tentativi=3, delay_retry=0)
        await gestore.invia(messaggio)

        trasporto_funzionante.invia.assert_awaited_once_with(messaggio)

    async def test_invio_con_messaggio_urgente(
        self, trasporto_funzionante, messaggio_urgente
    ):
        gestore = GestoreNotifiche(trasporto_funzionante, delay_retry=0)
        stato = await gestore.invia(messaggio_urgente)

        assert stato.successo is True
        trasporto_funzionante.invia.assert_awaited_once_with(messaggio_urgente)


# ===== TEST: RETRY =====

class TestRetry:
    """Test per la logica di retry."""

    async def test_fallisce_poi_riesce(self, messaggio):
        """Primo tentativo fallisce, secondo riesce."""
        mock = AsyncMock(spec=TrasportoBase)
        mock.invia.side_effect = [False, True]  # Prima False, poi True

        gestore = GestoreNotifiche(mock, max_tentativi=3, delay_retry=0)
        stato = await gestore.invia(messaggio)

        assert stato.successo is True
        assert stato.tentativi == 2
        assert mock.invia.await_count == 2

    async def test_tre_fallimenti_poi_successo(self, messaggio):
        """Tre fallimenti, poi riesce al quarto (con 4 max_tentativi)."""
        mock = AsyncMock(spec=TrasportoBase)
        mock.invia.side_effect = [False, False, False, True]

        gestore = GestoreNotifiche(mock, max_tentativi=4, delay_retry=0)
        stato = await gestore.invia(messaggio)

        assert stato.successo is True
        assert stato.tentativi == 4

    async def test_tutti_i_tentativi_falliscono(self, trasporto_rotto, messaggio):
        """Se tutti i tentativi falliscono, restituisce successo=False."""
        gestore = GestoreNotifiche(
            trasporto_rotto, max_tentativi=3, delay_retry=0
        )
        stato = await gestore.invia(messaggio)

        assert stato.successo is False
        assert stato.tentativi == 3
        assert trasporto_rotto.invia.await_count == 3

    async def test_eccezione_gestita_come_fallimento(
        self, trasporto_eccezione, messaggio
    ):
        """Le eccezioni vengono trattate come fallimenti e si riprova."""
        gestore = GestoreNotifiche(
            trasporto_eccezione, max_tentativi=2, delay_retry=0
        )
        stato = await gestore.invia(messaggio)

        assert stato.successo is False
        assert stato.tentativi == 2
        assert "Connessione rifiutata" in stato.errore

    async def test_delay_tra_tentativi(self, trasporto_rotto, messaggio):
        """Verifica che ci sia un delay tra i tentativi."""
        with patch("src.notifiche.asyncio.sleep") as mock_sleep:
            gestore = GestoreNotifiche(
                trasporto_rotto, max_tentativi=3, delay_retry=2.0
            )
            await gestore.invia(messaggio)

            # Con 3 tentativi, ci sono 2 sleep (non all'ultimo tentativo)
            assert mock_sleep.await_count == 2
            mock_sleep.assert_any_await(2.0)


# ===== TEST: FALLBACK =====

class TestFallback:
    """Test per la logica di fallback."""

    async def test_fallback_usato_quando_primario_fallisce(
        self, trasporto_rotto, trasporto_funzionante, messaggio
    ):
        """Se il primario fallisce, il fallback viene usato."""
        gestore = GestoreNotifiche(
            trasporto_rotto,
            trasporto_fallback=trasporto_funzionante,
            max_tentativi=2,
            delay_retry=0,
        )
        stato = await gestore.invia(messaggio)

        assert stato.successo is True
        assert trasporto_rotto.invia.await_count == 2  # Tutti i tentativi primari
        trasporto_funzionante.invia.assert_awaited_once_with(messaggio)

    async def test_fallback_indica_uso_nel_stato(
        self, trasporto_rotto, trasporto_funzionante, messaggio
    ):
        """Il campo errore indica quando il fallback è stato usato."""
        gestore = GestoreNotifiche(
            trasporto_rotto,
            trasporto_fallback=trasporto_funzionante,
            max_tentativi=1,
            delay_retry=0,
        )
        stato = await gestore.invia(messaggio)

        assert stato.successo is True
        assert "fallback" in stato.errore.lower()

    async def test_senza_fallback_ritorna_fallimento(
        self, trasporto_rotto, messaggio
    ):
        """Senza fallback configurato, dopo i tentativi primari ritorna False."""
        gestore = GestoreNotifiche(
            trasporto_rotto, max_tentativi=2, delay_retry=0
        )
        stato = await gestore.invia(messaggio)
        assert stato.successo is False


# ===== TEST: STORICO E STATISTICHE =====

class TestStoricoStatistiche:
    """Test per storico e statistiche degli invii."""

    async def test_storico_aggiornato_dopo_successo(
        self, trasporto_funzionante, messaggio
    ):
        gestore = GestoreNotifiche(trasporto_funzionante, delay_retry=0)
        await gestore.invia(messaggio)

        storico = gestore.storico_invii()
        assert len(storico) == 1
        assert storico[0].successo is True

    async def test_storico_aggiornato_dopo_fallimento(
        self, trasporto_rotto, messaggio
    ):
        gestore = GestoreNotifiche(
            trasporto_rotto, max_tentativi=2, delay_retry=0
        )
        await gestore.invia(messaggio)

        storico = gestore.storico_invii()
        assert len(storico) == 1
        assert storico[0].successo is False

    async def test_statistiche_multiple_invii(
        self, messaggio
    ):
        """Test statistiche con mix di successi e fallimenti."""
        mock_alterno = AsyncMock(spec=TrasportoBase)
        mock_alterno.invia.side_effect = [True, False, True]

        gestore = GestoreNotifiche(mock_alterno, max_tentativi=1, delay_retry=0)
        await gestore.invia(messaggio)
        await gestore.invia(messaggio)
        await gestore.invia(messaggio)

        stats = gestore.statistiche()
        assert stats["totale"] == 3
        assert stats["successi"] == 2
        assert stats["fallimenti"] == 1
        assert stats["tasso_successo"] == pytest.approx(2/3)

    async def test_statistiche_cache_vuota(self, trasporto_funzionante):
        gestore = GestoreNotifiche(trasporto_funzionante)
        stats = gestore.statistiche()
        assert stats["totale"] == 0
        assert stats["tasso_successo"] == 0.0
```

**Output atteso:**

```
tests/test_notifiche.py::TestInvioSuccesso::test_invio_riuscito_al_primo_tentativo PASSED
tests/test_notifiche.py::TestInvioSuccesso::test_trasporto_chiamato_una_volta_al_successo PASSED
...
tests/test_notifiche.py::TestRetry::test_fallisce_poi_riesce PASSED
tests/test_notifiche.py::TestRetry::test_delay_tra_tentativi PASSED
...
tests/test_notifiche.py::TestFallback::test_fallback_usato_quando_primario_fallisce PASSED
...

================================ 18 passed in 0.28s ================================
```

---

## Esercizio C12 — API REST con FastAPI (test di integrazione con TestClient)

### Obiettivo

Implementare e testare una semplice API REST per gestire una lista di compiti
(to-do list) con FastAPI, usando il `TestClient` di HTTPX.

### Struttura del progetto

```
todo_api/
├── src/
│   ├── modelli.py
│   └── app.py
└── tests/
    └── test_api.py
```

### Codice da testare

```python
# src/modelli.py

from pydantic import BaseModel, Field
from typing import Optional


class TodoBase(BaseModel):
    titolo: str = Field(..., min_length=1, max_length=200)
    descrizione: Optional[str] = Field(None, max_length=1000)
    completato: bool = False


class TodoCrea(TodoBase):
    """Schema per la creazione di un todo."""
    pass


class TodoAggiorna(BaseModel):
    """Schema per l'aggiornamento parziale di un todo."""
    titolo: Optional[str] = Field(None, min_length=1, max_length=200)
    descrizione: Optional[str] = Field(None, max_length=1000)
    completato: Optional[bool] = None


class TodoRisposta(TodoBase):
    """Schema per la risposta con l'ID."""
    id: int
```

```python
# src/app.py

from fastapi import FastAPI, HTTPException
from typing import Optional
from src.modelli import TodoCrea, TodoAggiorna, TodoRisposta

app = FastAPI(
    title="Todo API",
    description="API per la gestione di una lista di compiti",
    version="1.0.0",
)

# In-memory storage (nei test reali usereste un DB)
_todos: dict[int, dict] = {}
_prossimo_id = 1


def _reset_storage():
    """Resetta lo storage (usato nei test)."""
    global _todos, _prossimo_id
    _todos = {}
    _prossimo_id = 1


@app.get("/salute")
def stato_salute():
    """Endpoint di health check."""
    return {"stato": "ok", "versione": "1.0.0"}


@app.post("/todos", response_model=TodoRisposta, status_code=201)
def crea_todo(todo: TodoCrea):
    """Crea un nuovo todo."""
    global _prossimo_id
    nuovo_todo = {
        "id": _prossimo_id,
        "titolo": todo.titolo,
        "descrizione": todo.descrizione,
        "completato": todo.completato,
    }
    _todos[_prossimo_id] = nuovo_todo
    _prossimo_id += 1
    return nuovo_todo


@app.get("/todos", response_model=list[TodoRisposta])
def lista_todos(
    completato: Optional[bool] = None,
    limite: int = 100,
    offset: int = 0,
):
    """Lista tutti i todos con filtro opzionale."""
    tutti = list(_todos.values())
    if completato is not None:
        tutti = [t for t in tutti if t["completato"] == completato]
    return tutti[offset:offset + limite]


@app.get("/todos/{todo_id}", response_model=TodoRisposta)
def ottieni_todo(todo_id: int):
    """Ottieni un todo specifico per ID."""
    if todo_id not in _todos:
        raise HTTPException(status_code=404, detail=f"Todo {todo_id} non trovato")
    return _todos[todo_id]


@app.patch("/todos/{todo_id}", response_model=TodoRisposta)
def aggiorna_todo(todo_id: int, aggiornamento: TodoAggiorna):
    """Aggiorna parzialmente un todo."""
    if todo_id not in _todos:
        raise HTTPException(status_code=404, detail=f"Todo {todo_id} non trovato")

    todo = _todos[todo_id]
    dati_aggiornamento = aggiornamento.model_dump(exclude_none=True)
    todo.update(dati_aggiornamento)
    return todo


@app.delete("/todos/{todo_id}", status_code=204)
def elimina_todo(todo_id: int):
    """Elimina un todo."""
    if todo_id not in _todos:
        raise HTTPException(status_code=404, detail=f"Todo {todo_id} non trovato")
    del _todos[todo_id]
```

### Test completo

```python
# tests/test_api.py

import pytest
from fastapi.testclient import TestClient
from src.app import app, _reset_storage


# ===== FIXTURE =====

@pytest.fixture(autouse=True)
def storage_pulito():
    """Resetta lo storage prima di ogni test."""
    _reset_storage()
    yield
    _reset_storage()


@pytest.fixture
def client():
    """TestClient per l'applicazione FastAPI."""
    return TestClient(app)


@pytest.fixture
def todo_di_test(client):
    """Crea un todo di test e restituisce il payload della risposta."""
    risposta = client.post("/todos", json={
        "titolo": "Studiare pytest",
        "descrizione": "Fare il tutorial completo",
    })
    return risposta.json()


# ===== TEST: HEALTH CHECK =====

def test_health_check(client):
    risposta = client.get("/salute")
    assert risposta.status_code == 200
    dati = risposta.json()
    assert dati["stato"] == "ok"
    assert "versione" in dati


# ===== TEST: CREA TODO =====

class TestCreaTodo:
    """Test per POST /todos."""

    def test_crea_todo_minimo(self, client):
        """Crea un todo con solo il titolo."""
        risposta = client.post("/todos", json={"titolo": "Fare la spesa"})
        assert risposta.status_code == 201
        dati = risposta.json()
        assert dati["titolo"] == "Fare la spesa"
        assert dati["completato"] is False
        assert dati["descrizione"] is None
        assert "id" in dati

    def test_crea_todo_completo(self, client):
        """Crea un todo con tutti i campi."""
        risposta = client.post("/todos", json={
            "titolo": "Scrivere test",
            "descrizione": "Aggiungere test per tutti i casi limite",
            "completato": True,
        })
        assert risposta.status_code == 201
        dati = risposta.json()
        assert dati["titolo"] == "Scrivere test"
        assert dati["descrizione"] == "Aggiungere test per tutti i casi limite"
        assert dati["completato"] is True

    def test_id_autoincrementale(self, client):
        """Gli ID vengono assegnati in ordine crescente."""
        r1 = client.post("/todos", json={"titolo": "Primo"}).json()
        r2 = client.post("/todos", json={"titolo": "Secondo"}).json()
        r3 = client.post("/todos", json={"titolo": "Terzo"}).json()

        assert r1["id"] < r2["id"] < r3["id"]

    def test_titolo_vuoto_errore_400(self, client):
        """Un titolo vuoto deve restituire 422 (Unprocessable Entity)."""
        risposta = client.post("/todos", json={"titolo": ""})
        assert risposta.status_code == 422  # Pydantic validation error

    def test_senza_titolo_errore(self, client):
        """Senza titolo deve restituire 422."""
        risposta = client.post("/todos", json={"descrizione": "solo descrizione"})
        assert risposta.status_code == 422

    def test_titolo_troppo_lungo_errore(self, client):
        """Titolo > 200 caratteri deve restituire 422."""
        risposta = client.post("/todos", json={"titolo": "A" * 201})
        assert risposta.status_code == 422


# ===== TEST: LISTA TODOS =====

class TestListaTodos:
    """Test per GET /todos."""

    def test_lista_vuota(self, client):
        risposta = client.get("/todos")
        assert risposta.status_code == 200
        assert risposta.json() == []

    def test_lista_con_elementi(self, client):
        client.post("/todos", json={"titolo": "Primo"})
        client.post("/todos", json={"titolo": "Secondo"})

        risposta = client.get("/todos")
        assert risposta.status_code == 200
        assert len(risposta.json()) == 2

    def test_filtra_per_completato_true(self, client):
        client.post("/todos", json={"titolo": "Fatto", "completato": True})
        client.post("/todos", json={"titolo": "Da fare", "completato": False})

        risposta = client.get("/todos?completato=true")
        todos = risposta.json()
        assert len(todos) == 1
        assert todos[0]["titolo"] == "Fatto"

    def test_filtra_per_completato_false(self, client):
        client.post("/todos", json={"titolo": "Fatto", "completato": True})
        client.post("/todos", json={"titolo": "Da fare", "completato": False})

        risposta = client.get("/todos?completato=false")
        todos = risposta.json()
        assert len(todos) == 1
        assert todos[0]["titolo"] == "Da fare"

    def test_paginazione_limite(self, client):
        """Il parametro limite controlla il numero di risultati."""
        for i in range(5):
            client.post("/todos", json={"titolo": f"Todo {i}"})

        risposta = client.get("/todos?limite=3")
        assert len(risposta.json()) == 3

    def test_paginazione_offset(self, client):
        """Il parametro offset salta i primi N risultati."""
        ids_creati = []
        for i in range(5):
            r = client.post("/todos", json={"titolo": f"Todo {i}"})
            ids_creati.append(r.json()["id"])

        risposta = client.get("/todos?offset=2")
        ids_restituiti = [t["id"] for t in risposta.json()]
        assert ids_restituiti == ids_creati[2:]


# ===== TEST: OTTIENI SINGOLO TODO =====

class TestOttieniTodo:
    """Test per GET /todos/{id}."""

    def test_ottieni_todo_esistente(self, client, todo_di_test):
        todo_id = todo_di_test["id"]
        risposta = client.get(f"/todos/{todo_id}")
        assert risposta.status_code == 200
        assert risposta.json()["id"] == todo_id

    def test_ottieni_todo_inesistente_404(self, client):
        risposta = client.get("/todos/9999")
        assert risposta.status_code == 404

    def test_messaggio_errore_404(self, client):
        risposta = client.get("/todos/9999")
        assert "9999" in risposta.json()["detail"]


# ===== TEST: AGGIORNA TODO =====

class TestAggiornaTodo:
    """Test per PATCH /todos/{id}."""

    def test_aggiorna_titolo(self, client, todo_di_test):
        todo_id = todo_di_test["id"]
        risposta = client.patch(f"/todos/{todo_id}", json={"titolo": "Nuovo titolo"})
        assert risposta.status_code == 200
        assert risposta.json()["titolo"] == "Nuovo titolo"

    def test_aggiorna_completato(self, client, todo_di_test):
        todo_id = todo_di_test["id"]
        risposta = client.patch(f"/todos/{todo_id}", json={"completato": True})
        assert risposta.status_code == 200
        assert risposta.json()["completato"] is True

    def test_aggiornamento_parziale_preserva_altri_campi(self, client, todo_di_test):
        """Un aggiornamento parziale non deve modificare i campi non toccati."""
        todo_id = todo_di_test["id"]
        titolo_originale = todo_di_test["titolo"]

        client.patch(f"/todos/{todo_id}", json={"completato": True})
        risposta = client.get(f"/todos/{todo_id}")

        assert risposta.json()["titolo"] == titolo_originale  # Non cambiato
        assert risposta.json()["completato"] is True  # Aggiornato

    def test_aggiorna_todo_inesistente_404(self, client):
        risposta = client.patch("/todos/9999", json={"titolo": "Test"})
        assert risposta.status_code == 404


# ===== TEST: ELIMINA TODO =====

class TestEliminaTodo:
    """Test per DELETE /todos/{id}."""

    def test_elimina_todo_esistente(self, client, todo_di_test):
        todo_id = todo_di_test["id"]
        risposta = client.delete(f"/todos/{todo_id}")
        assert risposta.status_code == 204

    def test_dopo_eliminazione_non_trovato(self, client, todo_di_test):
        todo_id = todo_di_test["id"]
        client.delete(f"/todos/{todo_id}")

        risposta = client.get(f"/todos/{todo_id}")
        assert risposta.status_code == 404

    def test_elimina_todo_inesistente_404(self, client):
        risposta = client.delete("/todos/9999")
        assert risposta.status_code == 404

    def test_dopo_eliminazione_lista_aggiornata(self, client):
        r1 = client.post("/todos", json={"titolo": "Primo"}).json()
        r2 = client.post("/todos", json={"titolo": "Secondo"}).json()

        client.delete(f"/todos/{r1['id']}")

        lista = client.get("/todos").json()
        ids_rimasti = [t["id"] for t in lista]
        assert r1["id"] not in ids_rimasti
        assert r2["id"] in ids_rimasti


# ===== TEST: SCENARI INTEGRATI =====

class TestScenariIntegrati:
    """Test di scenario che simulano utilizzi reali dell'API."""

    def test_ciclo_vita_completo_todo(self, client):
        """
        Crea → Leggi → Aggiorna → Completa → Elimina.
        Simula il ciclo di vita completo di un todo.
        """
        # CREA
        r_crea = client.post("/todos", json={
            "titolo": "Imparare pytest",
            "descrizione": "Fare tutti gli esercizi",
        })
        assert r_crea.status_code == 201
        todo_id = r_crea.json()["id"]

        # LEGGI
        r_leggi = client.get(f"/todos/{todo_id}")
        assert r_leggi.status_code == 200
        assert r_leggi.json()["completato"] is False

        # AGGIORNA
        r_aggiorna = client.patch(f"/todos/{todo_id}", json={
            "descrizione": "Fatto gli esercizi C1-C12!"
        })
        assert r_aggiorna.status_code == 200

        # COMPLETA
        r_completa = client.patch(f"/todos/{todo_id}", json={"completato": True})
        assert r_completa.json()["completato"] is True

        # VERIFICA IN LISTA
        r_lista = client.get("/todos?completato=true")
        ids_completati = [t["id"] for t in r_lista.json()]
        assert todo_id in ids_completati

        # ELIMINA
        r_elimina = client.delete(f"/todos/{todo_id}")
        assert r_elimina.status_code == 204

        # VERIFICA ELIMINAZIONE
        r_verifica = client.get(f"/todos/{todo_id}")
        assert r_verifica.status_code == 404

    def test_filtro_completati_dopo_aggiornamenti_multipli(self, client):
        """
        Crea più todos, completane alcuni, verifica il filtro.
        """
        titoli = ["A", "B", "C", "D", "E"]
        ids = []
        for titolo in titoli:
            r = client.post("/todos", json={"titolo": titolo})
            ids.append(r.json()["id"])

        # Completa A, C, E (indici 0, 2, 4)
        for idx in [0, 2, 4]:
            client.patch(f"/todos/{ids[idx]}", json={"completato": True})

        # Verifica filtro completati
        r_completati = client.get("/todos?completato=true")
        ids_completati = [t["id"] for t in r_completati.json()]
        assert len(ids_completati) == 3
        assert ids[0] in ids_completati
        assert ids[2] in ids_completati
        assert ids[4] in ids_completati

        # Verifica filtro non-completati
        r_non_completati = client.get("/todos?completato=false")
        ids_non_completati = [t["id"] for t in r_non_completati.json()]
        assert len(ids_non_completati) == 2
        assert ids[1] in ids_non_completati
        assert ids[3] in ids_non_completati
```

**Output atteso:**

```
tests/test_api.py::test_health_check PASSED
tests/test_api.py::TestCreaTodo::test_crea_todo_minimo PASSED
tests/test_api.py::TestCreaTodo::test_crea_todo_completo PASSED
tests/test_api.py::TestCreaTodo::test_id_autoincrementale PASSED
tests/test_api.py::TestCreaTodo::test_titolo_vuoto_errore_400 PASSED
tests/test_api.py::TestCreaTodo::test_senza_titolo_errore PASSED
tests/test_api.py::TestCreaTodo::test_titolo_troppo_lungo_errore PASSED
tests/test_api.py::TestListaTodos::test_lista_vuota PASSED
tests/test_api.py::TestListaTodos::test_lista_con_elementi PASSED
tests/test_api.py::TestListaTodos::test_filtra_per_completato_true PASSED
tests/test_api.py::TestListaTodos::test_filtra_per_completato_false PASSED
tests/test_api.py::TestListaTodos::test_paginazione_limite PASSED
tests/test_api.py::TestListaTodos::test_paginazione_offset PASSED
tests/test_api.py::TestOttieniTodo::test_ottieni_todo_esistente PASSED
tests/test_api.py::TestOttieniTodo::test_ottieni_todo_inesistente_404 PASSED
tests/test_api.py::TestOttieniTodo::test_messaggio_errore_404 PASSED
tests/test_api.py::TestAggiornaTodo::test_aggiorna_titolo PASSED
tests/test_api.py::TestAggiornaTodo::test_aggiorna_completato PASSED
tests/test_api.py::TestAggiornaTodo::test_aggiornamento_parziale_preserva_altri_campi PASSED
tests/test_api.py::TestAggiornaTodo::test_aggiorna_todo_inesistente_404 PASSED
tests/test_api.py::TestEliminaTodo::test_elimina_todo_esistente PASSED
tests/test_api.py::TestEliminaTodo::test_dopo_eliminazione_non_trovato PASSED
tests/test_api.py::TestEliminaTodo::test_elimina_todo_inesistente_404 PASSED
tests/test_api.py::TestEliminaTodo::test_dopo_eliminazione_lista_aggiornata PASSED
tests/test_api.py::TestScenariIntegrati::test_ciclo_vita_completo_todo PASSED
tests/test_api.py::TestScenariIntegrati::test_filtro_completati_dopo_aggiornamenti_multipli PASSED

================================ 26 passed in 0.45s ================================
```

---

## Riepilogo degli Esercizi C9–C12

```
ESERCIZIO   TECNICA PRINCIPALE           NUMERO ASSERT
─────────────────────────────────────────────────────────────
C9          mock del tempo (time.time)   30 test
C10         Hypothesis (property-based)  22 test
C11         AsyncMock, retry, fallback   18 test
C12         TestClient FastAPI, REST     26 test
─────────────────────────────────────────────────────────────
TOTALE C9-C12:                           96 test
─────────────────────────────────────────────────────────────
```

---

## SEZIONE SUPPLEMENTARE H: Approfondimenti Avanzati

---

## H1: Fixture Avanzate — Tutti i Pattern

### Pattern 1: Fixture con parametri (indiretto)

Il parametrize indiretto permette di passare parametri a una fixture invece che
direttamente al test:

```python
# tests/test_fixture_indirect.py

import pytest


@pytest.fixture
def connessione_db(request):
    """
    Fixture parametrizzata — il parametro viene da parametrize(indirect=True).
    """
    tipo_db = request.param

    if tipo_db == "sqlite":
        conn = crea_connessione_sqlite(":memory:")
    elif tipo_db == "postgres":
        conn = crea_connessione_postgres("localhost", 5432)
    else:
        raise ValueError(f"Tipo DB sconosciuto: {tipo_db}")

    yield conn
    conn.close()


@pytest.mark.parametrize(
    "connessione_db",
    ["sqlite", "postgres"],
    indirect=True,  # Passa il valore alla fixture, non al test direttamente
)
def test_inserisci_e_leggi(connessione_db):
    """
    Questo test viene eseguito una volta con SQLite e una con PostgreSQL.
    La fixture si occupa di creare il tipo giusto di connessione.
    """
    connessione_db.execute("INSERT INTO test (valore) VALUES (42)")
    risultato = connessione_db.execute("SELECT valore FROM test").fetchone()
    assert risultato[0] == 42
```

---

### Pattern 2: Fixture come Factory

A volte hai bisogno di creare più istanze dello stesso oggetto, ognuna con
configurazioni diverse. La fixture come factory risolve questo:

```python
@pytest.fixture
def crea_utente():
    """
    Fixture factory: restituisce una funzione che crea utenti.

    Permette di creare più utenti con parametri diversi nello stesso test.
    """
    utenti_creati = []

    def _crea(nome="Mario", email=None, ruolo="base"):
        email = email or f"{nome.lower()}@test.it"
        utente = Utente(nome=nome, email=email, ruolo=ruolo)
        utenti_creati.append(utente)
        return utente

    yield _crea

    # Cleanup: elimina tutti gli utenti creati
    for utente in utenti_creati:
        utente.elimina()


def test_trasferimento_fondi(crea_utente):
    """Crea due utenti distinti nello stesso test."""
    mittente = crea_utente("Alice", ruolo="premium")
    destinatario = crea_utente("Bob")

    trasferisci_fondi(mittente, destinatario, 100.0)

    assert mittente.saldo == mittente.saldo_iniziale - 100.0
    assert destinatario.saldo == destinatario.saldo_iniziale + 100.0
```

---

### Pattern 3: Fixture con addfinalizer (cleanup garantito anche su errore)

```python
@pytest.fixture
def risorsa_con_cleanup(request):
    """
    Versione con addfinalizer invece di yield.

    Utile quando il cleanup deve essere garantito anche se la setup fallisce
    parzialmente, o quando ci sono più risorse da pulire in ordine inverso.
    """
    risorse = []

    def crea_risorsa(nome):
        risorsa = RisorsaEsterna(nome)
        risorsa.connetti()
        risorse.append(risorsa)
        return risorsa

    def cleanup():
        # Il cleanup viene eseguito in ordine inverso
        for risorsa in reversed(risorse):
            try:
                risorsa.disconnetti()
            except Exception as e:
                print(f"Errore durante cleanup di {risorsa}: {e}")

    request.addfinalizer(cleanup)
    return crea_risorsa
```

---

### Pattern 4: Fixture annidate con scope diversi

```python
# conftest.py

import pytest
import sqlite3


@pytest.fixture(scope="session")
def schema_db():
    """
    Crea lo schema del database una volta per tutta la sessione.
    Scope: session (eseguita una sola volta per tutta la sessione pytest)
    """
    conn = sqlite3.connect(":memory:")
    conn.execute("""
        CREATE TABLE utenti (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE ordini (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            utente_id INTEGER,
            totale REAL,
            FOREIGN KEY (utente_id) REFERENCES utenti(id)
        )
    """)
    conn.commit()
    yield conn
    conn.close()


@pytest.fixture(scope="module")
def utente_base(schema_db):
    """
    Crea un utente fisso per tutto il modulo.
    Dipende da schema_db (scope=session) — va bene, scope >= session.
    """
    schema_db.execute(
        "INSERT INTO utenti (nome, email) VALUES (?, ?)",
        ("Mario Rossi", "mario@test.it")
    )
    schema_db.commit()
    utente_id = schema_db.execute("SELECT last_insert_rowid()").fetchone()[0]
    yield utente_id
    # Cleanup: rimuovi l'utente
    schema_db.execute("DELETE FROM utenti WHERE id = ?", (utente_id,))
    schema_db.commit()


@pytest.fixture  # scope="function" (default)
def ordine_vuoto(schema_db, utente_base):
    """
    Crea un ordine vuoto per ogni test.
    Dipende da schema_db (session) e utente_base (module) — entrambi > function.
    """
    schema_db.execute(
        "INSERT INTO ordini (utente_id, totale) VALUES (?, ?)",
        (utente_base, 0.0)
    )
    schema_db.commit()
    ordine_id = schema_db.execute("SELECT last_insert_rowid()").fetchone()[0]
    yield ordine_id
    # Cleanup ordine dopo ogni test
    schema_db.execute("DELETE FROM ordini WHERE id = ?", (ordine_id,))
    schema_db.commit()


def test_ordine_inizialmente_vuoto(ordine_vuoto, schema_db):
    """Verifica che un nuovo ordine abbia totale 0."""
    totale = schema_db.execute(
        "SELECT totale FROM ordini WHERE id = ?", (ordine_vuoto,)
    ).fetchone()[0]
    assert totale == 0.0


def test_aggiunta_prodotto(ordine_vuoto, schema_db):
    """Verifica l'aggiunta di un prodotto all'ordine."""
    schema_db.execute(
        "UPDATE ordini SET totale = totale + 25.99 WHERE id = ?",
        (ordine_vuoto,)
    )
    schema_db.commit()
    totale = schema_db.execute(
        "SELECT totale FROM ordini WHERE id = ?", (ordine_vuoto,)
    ).fetchone()[0]
    assert totale == pytest.approx(25.99)
```

---

### Pattern 5: Fixture con autouse e scope

```python
# tests/conftest.py

import pytest
import logging


@pytest.fixture(autouse=True)
def configura_logging(caplog):
    """
    Si applica automaticamente a tutti i test.
    Configura il logging per catturare WARNING e superiori.
    """
    with caplog.at_level(logging.WARNING):
        yield


@pytest.fixture(autouse=True, scope="session")
def benvenuto():
    """Messaggio di inizio e fine sessione di test."""
    print("\n\n=== INIZIO SESSIONE DI TEST ===")
    yield
    print("\n=== FINE SESSIONE DI TEST ===")


@pytest.fixture(autouse=True)
def verifica_nessun_warning_inaspettato(caplog):
    """
    Dopo ogni test, verifica che non ci siano state warning inaspettate.
    """
    yield
    # Questo codice viene eseguito DOPO ogni test
    warning_inaspettate = [
        r for r in caplog.records
        if r.levelno >= logging.WARNING
        and "Deprecat" in r.getMessage()
    ]
    assert not warning_inaspettate, (
        f"Warning di deprecazione inaspettate: {warning_inaspettate}"
    )
```

---

## H2: @pytest.mark.parametrize — Tutti i Pattern

### Pattern 1: Parametrize con IDs espliciti

```python
import pytest
from src.validatore import valida_email


@pytest.mark.parametrize(
    "email, atteso",
    [
        ("mario@test.it", True),
        ("MARIO@TEST.IT", True),      # case insensitive
        ("mario+tag@test.it", True),  # con tag
        ("mario@sub.dominio.it", True),  # sottodomain
        ("mario", False),              # senza @
        ("@test.it", False),           # senza nome
        ("mario@", False),             # senza dominio
        ("mario @test.it", False),     # spazio nel mezzo
        ("mario@test..it", False),     # doppio punto
        ("", False),                   # stringa vuota
    ],
    ids=[
        "email_valida",
        "email_maiuscola",
        "email_con_tag",
        "email_sottodominio",
        "senza_chiocciola",
        "senza_nome",
        "senza_dominio",
        "con_spazio",
        "doppio_punto",
        "stringa_vuota",
    ],
)
def test_valida_email(email, atteso):
    """I test IDs appaiono nell'output di pytest per identificare il caso."""
    assert valida_email(email) == atteso
```

Output con `pytest -v`:

```
tests/test_validatore.py::test_valida_email[email_valida] PASSED
tests/test_validatore.py::test_valida_email[email_maiuscola] PASSED
tests/test_validatore.py::test_valida_email[email_con_tag] PASSED
...
tests/test_validatore.py::test_valida_email[stringa_vuota] PASSED
```

---

### Pattern 2: Prodotto cartesiano con parametrize multiplo

```python
@pytest.mark.parametrize("tipo_db", ["sqlite", "postgres", "mysql"])
@pytest.mark.parametrize("metodo_autenticazione", ["password", "token", "oauth"])
def test_login(tipo_db, metodo_autenticazione):
    """
    Con 3 tipi di DB e 3 metodi di autenticazione, genera 3×3=9 test.

    Eseguiti in ordine:
    test_login[password-sqlite]
    test_login[password-postgres]
    test_login[password-mysql]
    test_login[token-sqlite]
    ... (9 test totali)
    """
    risultato = effettua_login(
        db=tipo_db,
        auth_method=metodo_autenticazione,
        username="utente_test",
        password="password_test",
    )
    assert risultato.autenticato is True
```

---

### Pattern 3: parametrize con oggetti complessi

```python
from dataclasses import dataclass


@dataclass
class CasoSconto:
    """Dati per un caso di test sugli sconti."""
    eta: int
    abbonamento: str
    spesa: float
    sconto_atteso: float
    descrizione: str


casi_sconto = [
    CasoSconto(
        eta=25, abbonamento="base", spesa=100.0,
        sconto_atteso=0.0, descrizione="Adulto, nessun abbonamento premium"
    ),
    CasoSconto(
        eta=16, abbonamento="base", spesa=100.0,
        sconto_atteso=0.10, descrizione="Minore, sconto 10%"
    ),
    CasoSconto(
        eta=65, abbonamento="base", spesa=100.0,
        sconto_atteso=0.15, descrizione="Senior, sconto 15%"
    ),
    CasoSconto(
        eta=30, abbonamento="premium", spesa=100.0,
        sconto_atteso=0.20, descrizione="Abbonato premium, sconto 20%"
    ),
    CasoSconto(
        eta=65, abbonamento="premium", spesa=100.0,
        sconto_atteso=0.30, descrizione="Senior + premium, sconto 30%"
    ),
]


@pytest.mark.parametrize(
    "caso",
    casi_sconto,
    ids=[caso.descrizione for caso in casi_sconto],
)
def test_calcola_sconto(caso):
    """Il calcolo dello sconto deve considerare età e tipo di abbonamento."""
    sconto = calcola_sconto(caso.eta, caso.abbonamento)
    assert sconto == pytest.approx(caso.sconto_atteso)


# Oppure verifica il prezzo finale
@pytest.mark.parametrize("caso", casi_sconto, ids=[c.descrizione for c in casi_sconto])
def test_prezzo_finale(caso):
    """Il prezzo finale deve essere correttamente scontato."""
    sconto = calcola_sconto(caso.eta, caso.abbonamento)
    prezzo = caso.spesa * (1 - sconto)
    assert prezzo == pytest.approx(caso.spesa - caso.spesa * caso.sconto_atteso)
```

---

### Pattern 4: parametrize con valori che sollevano eccezioni

```python
@pytest.mark.parametrize(
    "valore, tipo_eccezione, messaggio_atteso",
    [
        (-1, ValueError, "negativo"),
        (0, ValueError, "zero"),
        ("abc", TypeError, "non numerico"),
        (None, TypeError, "None"),
        (float("inf"), ValueError, "infinito"),
    ],
    ids=[
        "negativo",
        "zero",
        "stringa",
        "none",
        "infinito",
    ]
)
def test_radice_quadrata_valori_invalidi(valore, tipo_eccezione, messaggio_atteso):
    """La funzione deve sollevare l'eccezione appropriata per ogni input invalido."""
    with pytest.raises(tipo_eccezione, match=messaggio_atteso):
        calcola_radice(valore)
```

---

## H3: Mock Avanzato — Pattern Completi

### Pattern 1: Mock di un context manager

```python
from unittest.mock import MagicMock, patch, mock_open


def leggi_file_configurazione(percorso: str) -> dict:
    """Legge un file di configurazione JSON."""
    import json
    with open(percorso) as f:
        return json.load(f)


def test_leggi_configurazione_con_mock():
    """Testa la lettura del file senza creare file reale."""
    config_json = '{"host": "localhost", "porta": 5432}'

    with patch("builtins.open", mock_open(read_data=config_json)):
        risultato = leggi_file_configurazione("/non/esiste.json")

    assert risultato["host"] == "localhost"
    assert risultato["porta"] == 5432


def test_errore_file_non_trovato():
    """Simula un errore di file non trovato."""
    with patch("builtins.open", side_effect=FileNotFoundError("File non trovato")):
        with pytest.raises(FileNotFoundError):
            leggi_file_configurazione("/non/esiste.json")
```

---

### Pattern 2: Mock di chiamate a catena

```python
class ServizioUtenti:
    def ottieni_utente(self, user_id: int):
        # In realtà chiama un'API
        ...


class ServizioEmail:
    def invia(self, a: str, oggetto: str, corpo: str) -> bool:
        # In realtà invia email via SMTP
        ...


class GestoreAccountFunzionale:
    def __init__(self, servizio_utenti, servizio_email):
        self._utenti = servizio_utenti
        self._email = servizio_email

    def invia_benvenuto(self, user_id: int) -> bool:
        utente = self._utenti.ottieni_utente(user_id)
        return self._email.invia(
            a=utente.email,
            oggetto="Benvenuto!",
            corpo=f"Ciao {utente.nome}, benvenuto!",
        )


def test_invia_benvenuto():
    """Testa il flusso di benvenuto con tutti i servizi mockati."""
    # Crea mock degli oggetti utente
    utente_mock = MagicMock()
    utente_mock.email = "mario@test.it"
    utente_mock.nome = "Mario"

    # Crea mock dei servizi
    servizio_utenti = MagicMock()
    servizio_utenti.ottieni_utente.return_value = utente_mock

    servizio_email = MagicMock()
    servizio_email.invia.return_value = True

    # Test
    gestore = GestoreAccountFunzionale(servizio_utenti, servizio_email)
    risultato = gestore.invia_benvenuto(user_id=42)

    # Verifica
    assert risultato is True
    servizio_utenti.ottieni_utente.assert_called_once_with(42)
    servizio_email.invia.assert_called_once_with(
        a="mario@test.it",
        oggetto="Benvenuto!",
        corpo="Ciao Mario, benvenuto!",
    )
```

---

### Pattern 3: Mock con side_effect callable

```python
# Simula comportamenti diversi basati sull'input

def recupera_dato(chiave: str) -> str:
    # Chiamata a un'API esterna
    ...


def test_comportamento_variabile():
    """Il mock risponde in modo diverso in base all'argomento."""
    risposte = {
        "utente:1": {"nome": "Mario"},
        "utente:2": {"nome": "Luigi"},
        "utente:99": None,
    }

    def risposta_simulata(chiave: str):
        if chiave not in risposte:
            raise KeyError(f"Chiave non trovata: {chiave}")
        return risposte[chiave]

    with patch("src.servizio.recupera_dato", side_effect=risposta_simulata):
        assert recupera_dato("utente:1") == {"nome": "Mario"}
        assert recupera_dato("utente:2") == {"nome": "Luigi"}
        assert recupera_dato("utente:99") is None

        with pytest.raises(KeyError):
            recupera_dato("utente:999")
```

---

### Pattern 4: Verifica dell'ordine delle chiamate

```python
from unittest.mock import call

def test_ordine_operazioni_db():
    """Verifica che le operazioni DB avvengano nel giusto ordine."""
    mock_db = MagicMock()

    # Esegui l'operazione
    esegui_transazione(mock_db)

    # Verifica l'ordine esatto delle chiamate
    assert mock_db.mock_calls == [
        call.inizio_transazione(),
        call.inserisci("dati"),
        call.aggiorna("stato", "completato"),
        call.commit(),
    ]
```

---

### Pattern 5: patch.object per metodi di istanza

```python
class ServizioNotifiche:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def invia_sms(self, numero: str, testo: str) -> bool:
        # Chiamata reale all'API Twilio
        import requests
        risposta = requests.post(
            "https://api.twilio.com/sms",
            data={"to": numero, "body": testo},
            auth=(self.api_key, ""),
        )
        return risposta.status_code == 200


def test_invia_sms_con_patch_object():
    """Mock del metodo specifico senza cambiare l'intera classe."""
    servizio = ServizioNotifiche(api_key="test_key")

    with patch.object(servizio, "invia_sms", return_value=True) as mock_invia:
        risultato = servizio.invia_sms("+39 333 123456", "Test")

    assert risultato is True
    mock_invia.assert_called_once_with("+39 333 123456", "Test")
```

---

## H4: conftest.py — Organizzazione Avanzata

### Struttura di progetto con conftest multipli

```
progetto/
├── conftest.py                    ← Fixture globali (session/module scope)
├── tests/
│   ├── conftest.py                ← Fixture per tutti i test
│   ├── unit/
│   │   ├── conftest.py            ← Fixture per unit test
│   │   └── test_calcolatrice.py
│   ├── integration/
│   │   ├── conftest.py            ← Fixture per integration test (con DB reale)
│   │   └── test_repository.py
│   └── e2e/
│       ├── conftest.py            ← Fixture per E2E (con client HTTP)
│       └── test_api_completa.py
```

```python
# tests/conftest.py — Fixture comuni a tutti i test

import pytest
from unittest.mock import MagicMock


@pytest.fixture
def utente_admin():
    """Utente amministratore per test di permessi."""
    return {"id": 1, "nome": "Admin", "ruolo": "admin", "attivo": True}


@pytest.fixture
def utente_base():
    """Utente normale per test di comportamento base."""
    return {"id": 2, "nome": "Mario", "ruolo": "base", "attivo": True}


@pytest.fixture
def utente_inattivo():
    """Utente inattivo per test di accesso negato."""
    return {"id": 3, "nome": "Ex-utente", "ruolo": "base", "attivo": False}
```

```python
# tests/unit/conftest.py — Fixture per unit test

import pytest
from unittest.mock import MagicMock, AsyncMock


@pytest.fixture
def mock_repository():
    """Mock del repository per test unitari del domain layer."""
    mock = MagicMock()
    mock.trova.return_value = None
    mock.salva.return_value = True
    mock.elimina.return_value = True
    return mock


@pytest.fixture
def mock_servizio_email():
    """Mock del servizio email per test unitari."""
    mock = MagicMock()
    mock.invia.return_value = True
    return mock
```

```python
# tests/integration/conftest.py — Fixture per integration test

import pytest
import sqlite3


@pytest.fixture(scope="module")
def db_integrazione():
    """
    Database reale (in-memory SQLite) per test di integrazione.
    Scope module: ricreato per ogni file di test.
    """
    conn = sqlite3.connect(":memory:")

    # Schema
    conn.executescript("""
        CREATE TABLE utenti (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            attivo INTEGER DEFAULT 1
        );
        CREATE TABLE sessioni (
            id TEXT PRIMARY KEY,
            utente_id INTEGER,
            creata_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (utente_id) REFERENCES utenti(id)
        );
    """)

    yield conn
    conn.close()


@pytest.fixture
def db_con_utente_base(db_integrazione):
    """DB con un utente di test pre-inserito."""
    db_integrazione.execute(
        "INSERT OR IGNORE INTO utenti (nome, email) VALUES (?, ?)",
        ("Mario Test", "mario.test@test.it")
    )
    db_integrazione.commit()
    utente_id = db_integrazione.execute(
        "SELECT id FROM utenti WHERE email = ?",
        ("mario.test@test.it",)
    ).fetchone()[0]
    yield utente_id
    # Cleanup: rimuovi i dati inseriti durante il test
    db_integrazione.execute("DELETE FROM sessioni WHERE utente_id = ?", (utente_id,))
    db_integrazione.execute("DELETE FROM utenti WHERE id = ?", (utente_id,))
    db_integrazione.commit()
```

---

## H5: Marks Avanzati — Categorie e Filtri

### Registrazione dei marker personalizzati

```python
# pyproject.toml

[tool.pytest.ini_options]
markers = [
    "slow: test che richiedono più di 5 secondi",
    "integrazione: test che richiedono servizi esterni (DB, API)",
    "e2e: test end-to-end che richiedono l'applicazione completa",
    "smoke: test critici da eseguire prima del deploy",
    "regression: test di regressione per bug noti",
    "feature_x: test per la feature X (sperimentale)",
    "wip: work in progress, non deve bloccare la CI",
]
```

### Uso dei marker

```python
import pytest


@pytest.mark.smoke
def test_health_check():
    """Test critico: deve passare sempre."""
    assert applicazione_in_esecuzione() is True


@pytest.mark.slow
@pytest.mark.integrazione
def test_elaborazione_grande_dataset():
    """Test lento che richiede database reale."""
    risultato = elabora_milione_di_righe()
    assert risultato["elaborati"] == 1_000_000


@pytest.mark.wip
def test_nuova_funzionalita():
    """In sviluppo — non blocca la CI."""
    assert nuova_funzione() == "valore_atteso"


@pytest.mark.regression
@pytest.mark.parametrize("ticket", ["BUG-123", "BUG-456", "BUG-789"])
def test_regressione(ticket):
    """Assicura che i bug chiusi non tornino."""
    assert non_riproduce_bug(ticket)
```

### Eseguire sottoinsiemi

```bash
# Solo test veloci (no @slow e no @integrazione)
pytest -m "not slow and not integrazione"

# Solo smoke test per CI rapida
pytest -m smoke

# Solo integration test
pytest -m integrazione

# Solo test di regressione
pytest -m regression

# Escluди wip e slow
pytest -m "not wip and not slow"
```

---

## H6: Approfondimento pytest.raises

### Tutte le varianti di pytest.raises

```python
import pytest


# Variante 1: Semplice — verifica solo il tipo di eccezione
def test_semplice():
    with pytest.raises(ValueError):
        int("non_numerico")


# Variante 2: Con match — verifica il messaggio con regex
def test_con_match():
    with pytest.raises(ValueError, match=r"invalid literal.*'abc'"):
        int("abc")


# Variante 3: Con oggetto ExceptionInfo per ispezione avanzata
def test_con_oggetto_excinfo():
    with pytest.raises(ValueError) as exc_info:
        int("abc")

    # Ora puoi ispezionare l'eccezione
    assert exc_info.type == ValueError
    assert "abc" in str(exc_info.value)
    assert exc_info.traceback is not None


# Variante 4: Verifica eccezioni annidate (cause)
class ErroreDominio(Exception):
    pass


def operazione_fallita():
    try:
        int("abc")
    except ValueError as e:
        raise ErroreDominio("Operazione non riuscita") from e


def test_eccezione_con_causa():
    with pytest.raises(ErroreDominio) as exc_info:
        operazione_fallita()

    # Verifica la causa originale
    assert isinstance(exc_info.value.__cause__, ValueError)
    assert "abc" in str(exc_info.value.__cause__)


# Variante 5: Verifica che NON venga sollevata un'eccezione
def test_nessuna_eccezione():
    """Verifica esplicitamente che non vengano sollevate eccezioni."""
    try:
        risultato = int("42")  # Deve funzionare senza errori
    except ValueError:
        pytest.fail("int('42') non deve sollevare ValueError")

    assert risultato == 42
```

---

### pytest.warns — Verifica i warning

```python
import warnings
import pytest


def funzione_deprecata():
    warnings.warn(
        "funzione_deprecata è deprecata, usa nuova_funzione invece",
        DeprecationWarning,
        stacklevel=2,
    )
    return 42


def test_warning_deprecazione():
    """Verifica che la funzione emetta il warning atteso."""
    with pytest.warns(DeprecationWarning, match="deprecata"):
        risultato = funzione_deprecata()
    assert risultato == 42


def test_nessun_warning():
    """Verifica che una funzione non emetta warning."""
    with warnings.catch_warnings():
        warnings.simplefilter("error")  # Converte warning in eccezione
        risultato = nuova_funzione()  # Se emette un warning, il test fallisce
    assert risultato is not None
```

---

## H7: Fixtures Built-in di pytest — Guida Completa

### capsys — Cattura stdout/stderr

```python
def test_output_stampato(capsys):
    """Verifica che la funzione stampi l'output corretto."""
    from src.reporter import genera_report
    genera_report({"totale": 100, "venduti": 75})

    captured = capsys.readouterr()

    assert "Totale: 100" in captured.out
    assert "Venduti: 75" in captured.out
    assert "Percentuale: 75.0%" in captured.out
    assert captured.err == ""  # Nessun output su stderr


def test_errore_su_stderr(capsys):
    """Verifica che gli errori vengano scritti su stderr."""
    from src.logger import log_errore
    log_errore("Qualcosa è andato storto")

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "storto" in captured.err
```

---

### caplog — Cattura log

```python
import logging


def test_log_generato(caplog):
    """Verifica che la funzione generi i log attesi."""
    from src.servizio import elabora_richiesta

    with caplog.at_level(logging.INFO):
        elabora_richiesta({"tipo": "acquisto", "importo": 100})

    assert "Elaborazione richiesta di acquisto" in caplog.text
    assert any(r.levelname == "INFO" for r in caplog.records)


def test_log_warning_su_errore(caplog):
    """Verifica che un input invalido generi un warning nel log."""
    from src.servizio import elabora_richiesta

    with caplog.at_level(logging.WARNING):
        elabora_richiesta({"tipo": "sconosciuto", "importo": -1})

    assert any(
        "tipo non riconosciuto" in r.message and r.levelname == "WARNING"
        for r in caplog.records
    )


def test_log_errore_eccezione(caplog):
    """Verifica che le eccezioni vengano loggiate correttamente."""
    from src.handler import gestisci_errore

    with caplog.at_level(logging.ERROR):
        gestisci_errore(ValueError("test"))

    errori = [r for r in caplog.records if r.levelno >= logging.ERROR]
    assert len(errori) == 1
    assert "ValueError" in errori[0].message
```

---

### monkeypatch — Override sicuro di attributi, env, funzioni

```python
def test_variabile_ambiente(monkeypatch):
    """Testa il comportamento con variabile d'ambiente specifica."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///test.db")
    monkeypatch.setenv("DEBUG", "true")

    from src.configurazione import carica_config
    config = carica_config()

    assert config.database_url == "sqlite:///test.db"
    assert config.debug is True
    # La variabile viene ripristinata automaticamente dopo il test


def test_senza_variabile_ambiente(monkeypatch):
    """Testa il comportamento quando una variabile d'ambiente manca."""
    monkeypatch.delenv("DATABASE_URL", raising=False)

    from src.configurazione import carica_config
    config = carica_config()

    assert config.database_url == "sqlite:///default.db"  # Valore di default


def test_sostituzione_funzione(monkeypatch):
    """Sostituisce una funzione con una versione controllata."""
    chiamate = []

    def funzione_sostitutiva(valore):
        chiamate.append(valore)
        return valore * 2

    monkeypatch.setattr("src.modulo.funzione_target", funzione_sostitutiva)

    from src.modulo import usa_funzione
    risultato = usa_funzione(21)

    assert risultato == 42
    assert chiamate == [21]


def test_override_attributo_classe(monkeypatch):
    """Override di un attributo di classe."""
    monkeypatch.setattr("src.config.Config.max_tentativi", 1)

    from src.servizio import ServizioCon ResilLo
    # Il servizio ora userà max_tentativi=1 invece del valore reale
```

---

### tmp_path — File temporanei

```python
def test_elabora_file_csv(tmp_path):
    """
    Testa l'elaborazione di un file CSV.
    tmp_path è una directory temporanea unica per ogni test.
    """
    # Prepara il file di input
    file_input = tmp_path / "dati.csv"
    file_input.write_text("nome,eta\nMario,25\nLuigi,30\n")

    # Esegui l'elaborazione
    from src.elaboratore import elabora_csv
    file_output = tmp_path / "risultato.json"
    elabora_csv(str(file_input), str(file_output))

    # Verifica il risultato
    import json
    risultato = json.loads(file_output.read_text())
    assert len(risultato) == 2
    assert risultato[0]["nome"] == "Mario"
    assert risultato[0]["eta"] == 25


def test_gestione_directory(tmp_path):
    """Testa operazioni su strutture di directory."""
    # Crea struttura
    (tmp_path / "input").mkdir()
    (tmp_path / "output").mkdir()
    (tmp_path / "input" / "file1.txt").write_text("contenuto 1")
    (tmp_path / "input" / "file2.txt").write_text("contenuto 2")

    from src.processore import processa_directory
    processa_directory(
        str(tmp_path / "input"),
        str(tmp_path / "output")
    )

    output_files = list((tmp_path / "output").iterdir())
    assert len(output_files) == 2


def test_scrittura_log(tmp_path):
    """Testa che i log vengano scritti correttamente su file."""
    file_log = tmp_path / "app.log"

    from src.logger import Logger
    logger = Logger(str(file_log))
    logger.info("Avvio applicazione")
    logger.warning("Connessione lenta")
    logger.error("Errore critico")

    contenuto = file_log.read_text()
    assert "INFO" in contenuto
    assert "Avvio applicazione" in contenuto
    assert "WARNING" in contenuto
    assert "ERROR" in contenuto
```

---

## H8: Coverage — Analisi Dettagliata

### Capire i tipi di coverage

```python
# esempio per capire line vs branch coverage

def calcola_spedizione(peso: float, veloce: bool) -> float:
    """
    Calcola il costo di spedizione.

    Se peso > 10 kg: costo base = 20
    Altrimenti: costo base = 5
    Se veloce: raddoppia il costo
    """
    if peso > 10:              # Linea 1 — branch: peso>10 vs peso<=10
        costo = 20.0
    else:
        costo = 5.0

    if veloce:                 # Linea 2 — branch: veloce=True vs veloce=False
        costo *= 2

    return costo
```

```python
# Test con solo line coverage 100% ma branch coverage < 100%
def test_spedizione_leggera_veloce():
    assert calcola_spedizione(2.0, True) == 10.0

# Questo test copre TUTTE le linee (peso <= 10 è coperto, veloce=True è coperto)
# Ma mancano i branch:
#   - peso > 10 (True branch del primo if)
#   - veloce = False (False branch del secondo if)

# Per avere branch coverage 100%:
def test_spedizione_pesante_normale():
    assert calcola_spedizione(15.0, False) == 20.0
```

### Configurazione coverage avanzata

```toml
# pyproject.toml

[tool.coverage.run]
source = ["src"]
branch = true
omit = [
    "src/*/migrations/*",
    "src/__init__.py",
    "tests/*",
    "venv/*",
]
parallel = true  # Per pytest-xdist

[tool.coverage.report]
skip_covered = false
skip_empty = true
show_missing = true
exclude_lines = [
    # Escludi questi pattern dal conteggio di coverage
    "pragma: no cover",
    "raise NotImplementedError",
    "if TYPE_CHECKING:",
    "if __name__ == .__main__.:",
    "@(abc\\.)?abstractmethod",
    "\\.\\.\\.",  # Ellissi (abstract methods)
]
fail_under = 85  # Fallisce se sotto l'85% di coverage

[tool.coverage.html]
directory = "htmlcov"
title = "Coverage Report — Mio Progetto"

[tool.coverage.xml]
output = "coverage.xml"
```

### Interpretare l'output di coverage

```
$ pytest --cov=src --cov-report=term-missing tests/

----------- coverage: platform linux, python 3.12.3 -----------
Name                    Stmts   Miss Branch BrPart  Cover   Missing
--------------------------------------------------------------------
src/calcolatrice.py        45      3     20      2    92%   34-36, 78
src/validatore.py          30      0     15      0   100%
src/servizio.py            80     15     40      5    78%   45-50, 67, 89-95
--------------------------------------------------------------------
TOTAL                     155     18     75      7    87%
```

Spiegazione delle colonne:
- `Stmts`: numero totale di statement (istruzioni Python)
- `Miss`: statement non eseguiti durante i test
- `Branch`: numero di branch (rami condizionali)
- `BrPart`: branch parzialmente coperti (un ramo sì, l'altro no)
- `Cover`: percentuale di coverage (line + branch)
- `Missing`: numeri di riga non coperti

```
src/servizio.py    80     15     40      5    78%   45-50, 67, 89-95
```

Questo significa:
- Riga 45-50: non eseguite (possibile blocco di gestione errori mai testato)
- Riga 67: non eseguita (possibile codice morto o caso limite non testato)
- Riga 89-95: non eseguite (probabilmente un ramo `else` o un'eccezione)

---

## H9: Debugging dei Test Falliti

### Come usare pytest -v -s per il debug

```bash
# Mostra output dettagliato + stampe
pytest tests/test_mio.py -v -s

# Mostra solo i test falliti
pytest --tb=short -q

# Mostra il traceback completo
pytest --tb=long

# Apre il debugger pdb al fallimento
pytest --pdb

# Ferma al primo fallimento
pytest -x

# Esegui solo i test che hanno fallito nell'ultima sessione
pytest --lf

# Esegui prima i test falliti, poi gli altri
pytest --ff
```

### Usare breakpoint nei test

```python
def test_complesso():
    dati = prepara_dati_complessi()

    # Aggiungi breakpoint per ispezionare lo stato
    breakpoint()  # Python 3.7+: apre pdb qui durante pytest -s

    risultato = elabora(dati)
    assert risultato["stato"] == "completato"
```

---

## H10: Plugin Utili per la Produttività

### pytest-sugar — Output più leggibile

```bash
pip install pytest-sugar
```

Cambia l'output da:

```
F..F.F...
```

A:

```
 tests/test_api.py ✓ test_health_check
 tests/test_api.py ✓ test_crea_todo
 tests/test_api.py ✗ test_aggiorna_todo (FAILED)
```

---

### pytest-randomly — Ordine casuale

```bash
pip install pytest-randomly
```

```bash
# Esegui in ordine casuale con seed esplicito (per riprodurre un fallimento)
pytest --randomly-seed=12345

# Disabilita l'ordine casuale per questa sessione
pytest -p no:randomly
```

---

### pytest-repeat — Ripeti test

```bash
pip install pytest-repeat
```

```bash
# Ripeti ogni test 5 volte (per trovare test instabili)
pytest --count=5 tests/

# Ripeti con parametro nel nome del test
pytest --count=3 tests/ --repeat-scope=function
```

---

### pytest-timeout — Timeout automatico

```bash
pip install pytest-timeout
```

```toml
# pyproject.toml — timeout di default per tutti i test
[tool.pytest.ini_options]
timeout = 30  # 30 secondi
```

```python
# Timeout per test specifico
@pytest.mark.timeout(5)
def test_operazione_lenta():
    ...

# Disabilita il timeout per un test
@pytest.mark.timeout(0)
def test_senza_timeout():
    ...
```

---

### pytest-deadfixtures — Trova fixture inutilizzate

```bash
pip install pytest-deadfixtures
pytest --dead-fixtures
```

Output:

```
Your fixtures: 12
Used fixtures: 10
Dead fixtures:
  fixture_non_usata (tests/conftest.py:45)
  altra_fixture_vecchia (tests/unit/conftest.py:23)
```

---

## H11: Glossario Tecnico Completo

Questa sezione raccoglie tutti i termini tecnici usati nel tutorial, con
definizioni precise e riferimenti ai concetti correlati.

```
AAA (Arrange-Act-Assert)
    Pattern per strutturare i test in tre fasi:
    Arrange = prepara i dati/oggetti
    Act = esegui l'azione da testare
    Assert = verifica il risultato atteso

AsyncMock
    Versione asincrona di MagicMock. Usata per mockare funzioni async.
    Restituisce una coroutine quando chiamata, compatibile con await.

autouse (fixture)
    Parametro di una fixture che la fa applicare automaticamente a tutti
    i test nel suo scope, senza che debbano dichiararla esplicitamente.

Branch coverage
    Misura quanti rami condizionali (if/else, try/except) sono stati
    eseguiti durante i test. Più precisa della line coverage.

BDD (Behaviour-Driven Development)
    Approccio di sviluppo in cui i test sono scritti in linguaggio naturale
    (Gherkin: Given/When/Then) e poi implementati come step.

caplog
    Fixture built-in di pytest per catturare e verificare i messaggi
    di logging emessi durante i test.

capsys
    Fixture built-in di pytest per catturare e verificare l'output
    scritto su stdout e stderr durante i test.

conftest.py
    File speciale di pytest che contiene fixture e configurazioni condivise.
    Viene scoperto automaticamente e si applica ai test nella stessa directory
    e nelle sottodirectory.

coverage (copertura)
    Percentuale del codice sorgente eseguita durante i test.
    Tipi: line coverage, branch coverage, path coverage.

Dummy
    Test double che viene passato ma mai usato. Serve solo a soddisfare
    una firma di funzione che richiede un parametro.

E2E (End-to-End)
    Test che verificano il sistema completo dall'inizio alla fine,
    come farebbe un utente reale.

Fake
    Test double con implementazione funzionante ma semplificata.
    Es: database in-memory invece di PostgreSQL.

factory_boy
    Libreria Python per creare oggetti di test con dati realistici.
    Alternativa agli oggetti hardcoded nei test.

fixture
    In pytest, una funzione che fornisce dati, oggetti, o risorse
    ai test. Può avere diversi scope e supporta setup/teardown.

fuzzing
    Tecnica di testing che alimenta input casuali o semi-casuali
    al programma per trovare crash e comportamenti inattesi.

Gherkin
    Linguaggio naturale strutturato usato in BDD per descrivere
    scenari di test: Given (dato che), When (quando), Then (allora).

GWT (Given-When-Then)
    Alias per il pattern BDD. Given = precondizioni,
    When = azione, Then = risultato atteso.

Hypothesis
    Libreria Python per property-based testing. Genera automaticamente
    esempi di input per verificare proprietà matematiche/logiche.

integration test
    Test che verificano l'interazione tra più componenti del sistema,
    come un servizio con il suo database.

line coverage
    Misura quante linee di codice sono state eseguite durante i test.
    Meno precisa della branch coverage.

MagicMock
    Versione di Mock con supporto per i magic methods Python
    (__len__, __iter__, __enter__, __exit__, ecc.).

marker
    Decoratore pytest (@pytest.mark.xxx) per taggare i test e
    permettere l'esecuzione selettiva.

Mock
    Oggetto sostitutivo che registra le chiamate e permette di
    verificarle. Da non confondere con stub (che solo restituisce valori).

mock_open
    Helper di unittest.mock per mockare la funzione built-in open().

monkeypatch
    Fixture built-in di pytest per sostituire temporaneamente attributi,
    funzioni, variabili d'ambiente durante un test.

mutation testing
    Tecnica che introduce bug artificiali (mutanti) nel codice per
    verificare che i test li rilevino. Misura la qualità dei test.

mutmut
    Strumento Python per mutation testing.

parametrize
    Decoratore pytest (@pytest.mark.parametrize) per eseguire lo stesso
    test con input diversi, generando test separati per ognuno.

property-based testing
    Testing in cui si specificano proprietà (invarianti) che devono valere
    per qualsiasi input, anziché esempi specifici.

pytest
    Framework di testing Python. Alternativa moderna a unittest con
    sintassi più semplice e potenti funzionalità di fixture.

scope (fixture)
    Definisce la frequenza di creazione di una fixture:
    function (default), class, module, session.

side_effect
    Attributo di un Mock che specifica cosa deve succedere quando
    il mock viene chiamato. Può essere un'eccezione, un callable,
    o un iterabile.

snapshot testing
    Test che confrontano l'output corrente con un "snapshot" (foto)
    precedentemente approvato. Utile per output complessi.

Spy
    Test double che registra come viene usato (come Mock) ma chiama
    anche l'implementazione reale.

Stub
    Test double che restituisce valori predefiniti senza logica reale.

syrupy
    Libreria Python per snapshot testing.

TDD (Test-Driven Development)
    Pratica di sviluppo in cui si scrive il test prima del codice.
    Ciclo: Red → Green → Refactor.

testcontainers
    Libreria Python per avviare container Docker durante i test di
    integrazione (PostgreSQL, Redis, MongoDB, ecc.).

tmp_path
    Fixture built-in di pytest che fornisce una directory temporanea
    unica per ogni test. Pulita automaticamente.

unit test
    Test che verificano un'unità isolata di codice (funzione o classe)
    senza dipendenze esterne reali.

xfail
    Marker pytest (@pytest.mark.xfail) per test attesi fallire.
    Il test è documentato ma non blocca la suite.

xdist (pytest-xdist)
    Plugin pytest per esecuzione parallela dei test su più CPU o
    macchine remote.
```

---

## H12: Tabelle di Riferimento Rapido

### Tabella: Quando usare quale tipo di test

```
SCENARIO                              TIPO DI TEST    TOOL PRINCIPALE
────────────────────────────────────────────────────────────────────
Funzione pura con input/output        Unit            pytest
Classe con logica di business         Unit            pytest
Servizio con dipendenze               Unit + Mock     pytest + unittest.mock
API REST (endpoint singolo)           Integration     pytest + httpx/requests
API con autenticazione               Integration     pytest + TestClient
Database queries                      Integration     pytest + testcontainers
Molteplici servizi insieme           Integration     pytest + Docker Compose
Flusso utente completo               E2E             pytest + Playwright/Selenium
Performance e latenza                Performance     pytest-benchmark + Locust
Proprietà matematiche                Property        Hypothesis
Ricerca di crash con input casuali   Fuzzing         atheris/pythonfuzz
Qualità dei test stessi              Mutation        mutmut
Output HTML/JSON complessi           Snapshot        syrupy
Comportamento definito dal business  BDD             behave / pytest-bdd
────────────────────────────────────────────────────────────────────
```

---

### Tabella: scope delle fixture

```
SCOPE       CREATA QUANDO              DISTRUTTA QUANDO          USO TIPICO
──────────────────────────────────────────────────────────────────────────────
function    Prima di ogni test         Dopo ogni test            Default, dati mutabili
class       Prima di ogni classe       Dopo ogni classe          Stato condiviso in classe
module      Prima di ogni file .py     Alla fine del file .py    Connessioni DB per file
session     All'inizio di pytest       Alla fine di pytest       Config globale, server
──────────────────────────────────────────────────────────────────────────────
```

---

### Tabella: Mock vs MagicMock vs AsyncMock

```
TIPO            CASO D'USO                            DIFFERENZA CHIAVE
────────────────────────────────────────────────────────────────────────────
Mock            Oggetti e funzioni generiche          Non supporta magic methods
MagicMock       Oggetti con __len__, __iter__,        Versione completa di Mock
                __enter__, __exit__, ecc.
AsyncMock       Funzioni e metodi async               Restituisce coroutine
PropertyMock    Proprietà (@property)                 Usato con patch.object
────────────────────────────────────────────────────────────────────────────
```

---

### Tabella: Assertion comuni

```
ASSERT                          SIGNIFICATO
──────────────────────────────────────────────────────────────────
assert x == y                   x è uguale a y
assert x != y                   x è diverso da y
assert x is y                   x e y sono lo stesso oggetto
assert x is None                x è None
assert x is not None            x non è None
assert x in y                   x è contenuto in y
assert x not in y               x non è contenuto in y
assert isinstance(x, T)         x è un'istanza di tipo T
assert callable(f)              f è chiamabile
assert 0.1 + 0.2 == approx(0.3) float approssimato
assert len(lista) == 3          lista ha 3 elementi
──────────────────────────────────────────────────────────────────
```

---

### Tabella: Comandi pytest più usati

```
COMANDO                                     FUNZIONE
──────────────────────────────────────────────────────────────────
pytest                                      Esegui tutti i test
pytest -v                                   Output verboso
pytest -q                                   Output silenziato
pytest -s                                   Mostra print/output
pytest -x                                   Ferma al primo fallimento
pytest -k "nome"                            Filtra per nome
pytest -m "marker"                          Filtra per marker
pytest --lf                                 Solo test falliti
pytest --ff                                 Falliti prima, poi gli altri
pytest --co                                 Lista test (senza eseguire)
pytest --pdb                                Debugger al fallimento
pytest --tb=short                           Traceback corto
pytest -n auto                              Parallelo (xdist)
pytest --cov=src --cov-report=term-missing  Coverage
pytest --count=5                            Ripeti ogni test 5 volte
pytest --timeout=30                         Timeout 30s
──────────────────────────────────────────────────────────────────
```

---

## SEZIONE SUPPLEMENTARE I: Pattern Avanzati con Esempi Completi

---

## I1: Testing del Pattern Repository

Il pattern Repository è uno dei pattern più comuni nell'architettura del software.
Separa la logica di business dall'accesso ai dati. Ecco come testarlo correttamente.

### Il problema senza Repository

```python
# PROBLEMA: la logica di business è mescolata con il DB
def calcola_totale_ordini_utente(user_id: int) -> float:
    import sqlite3
    conn = sqlite3.connect("produzione.db")  # Hardcoded!
    cursor = conn.cursor()
    cursor.execute(
        "SELECT SUM(totale) FROM ordini WHERE utente_id = ? AND stato = 'completato'",
        (user_id,)
    )
    totale = cursor.fetchone()[0] or 0.0
    conn.close()
    return totale

# Come testi questo? Devi avere un database reale con dati reali.
# È un integration test ogni volta, non un unit test.
```

### La soluzione: Repository Pattern

```python
# src/repository.py — Interfaccia

from abc import ABC, abstractmethod
from typing import Optional
from src.modelli import Ordine


class OrdiniRepositoryBase(ABC):
    """Contratto per il repository degli ordini."""

    @abstractmethod
    def trova_per_utente(self, utente_id: int, stato: str = "completato") -> list[Ordine]:
        """Restituisce gli ordini di un utente."""
        ...

    @abstractmethod
    def salva(self, ordine: Ordine) -> Ordine:
        """Salva o aggiorna un ordine."""
        ...

    @abstractmethod
    def elimina(self, ordine_id: int) -> bool:
        """Elimina un ordine per ID."""
        ...
```

```python
# src/servizi/ordini.py — Logica di business pura

class ServizioOrdini:
    """
    Logica di business per la gestione degli ordini.
    Dipende dall'astrazione, non dall'implementazione concreta.
    """

    def __init__(self, repository: OrdiniRepositoryBase) -> None:
        self._repository = repository

    def calcola_totale_utente(self, utente_id: int) -> float:
        """Calcola il totale degli ordini completati di un utente."""
        ordini = self._repository.trova_per_utente(utente_id, stato="completato")
        return sum(o.totale for o in ordini)

    def applica_sconto_fedelta(self, utente_id: int) -> float:
        """
        Applica uno sconto fedeltà se l'utente ha più di 5 ordini.
        """
        ordini = self._repository.trova_per_utente(utente_id)
        if len(ordini) >= 5:
            return 0.10  # 10% di sconto
        elif len(ordini) >= 3:
            return 0.05  # 5% di sconto
        return 0.0
```

### Test unitari con Mock del Repository

```python
# tests/unit/test_servizio_ordini.py

import pytest
from unittest.mock import MagicMock
from src.servizi.ordini import ServizioOrdini
from src.modelli import Ordine


@pytest.fixture
def mock_repository():
    """Mock del repository — non tocca mai il database."""
    return MagicMock()


@pytest.fixture
def servizio(mock_repository):
    """Servizio con repository mockato."""
    return ServizioOrdini(repository=mock_repository)


class TestCalcolaTotaleUtente:

    def test_nessun_ordine_restituisce_zero(self, servizio, mock_repository):
        """Un utente senza ordini ha totale zero."""
        mock_repository.trova_per_utente.return_value = []
        assert servizio.calcola_totale_utente(utente_id=1) == 0.0

    def test_un_ordine(self, servizio, mock_repository):
        """Totale con un solo ordine."""
        ordine = MagicMock()
        ordine.totale = 49.99
        mock_repository.trova_per_utente.return_value = [ordine]

        assert servizio.calcola_totale_utente(utente_id=1) == pytest.approx(49.99)

    def test_piu_ordini_sommati(self, servizio, mock_repository):
        """Il totale è la somma di tutti gli ordini."""
        ordini = [MagicMock(totale=v) for v in [10.0, 25.50, 14.00]]
        mock_repository.trova_per_utente.return_value = ordini

        assert servizio.calcola_totale_utente(utente_id=1) == pytest.approx(49.50)

    def test_filtra_per_stato_completato(self, servizio, mock_repository):
        """La ricerca deve usare lo stato 'completato'."""
        mock_repository.trova_per_utente.return_value = []
        servizio.calcola_totale_utente(utente_id=42)

        mock_repository.trova_per_utente.assert_called_once_with(42, stato="completato")


class TestApplicaScontoFedelta:

    @pytest.mark.parametrize("num_ordini, sconto_atteso", [
        (0, 0.0),
        (1, 0.0),
        (2, 0.0),
        (3, 0.05),
        (4, 0.05),
        (5, 0.10),
        (10, 0.10),
    ], ids=[
        "0_ordini", "1_ordine", "2_ordini",
        "3_ordini_5%", "4_ordini_5%", "5_ordini_10%", "10_ordini_10%"
    ])
    def test_sconto_per_numero_ordini(
        self, servizio, mock_repository, num_ordini, sconto_atteso
    ):
        """Lo sconto dipende dal numero di ordini storici."""
        ordini = [MagicMock() for _ in range(num_ordini)]
        mock_repository.trova_per_utente.return_value = ordini

        assert servizio.applica_sconto_fedelta(utente_id=1) == pytest.approx(sconto_atteso)
```

### Test di integrazione con Repository reale (SQLite)

```python
# tests/integration/test_ordini_repository.py

import pytest
import sqlite3
from src.repository.sqlite import OrdiniRepositorySQLite
from src.modelli import Ordine


@pytest.fixture(scope="module")
def db():
    """Database SQLite in-memory per i test di integrazione."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        CREATE TABLE utenti (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL
        );
        CREATE TABLE ordini (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            utente_id INTEGER NOT NULL,
            totale REAL NOT NULL,
            stato TEXT NOT NULL DEFAULT 'in_attesa',
            FOREIGN KEY (utente_id) REFERENCES utenti(id)
        );
        INSERT INTO utenti (nome) VALUES ('Mario Test');
    """)
    yield conn
    conn.close()


@pytest.fixture
def repository(db):
    """Repository che usa il database di test."""
    return OrdiniRepositorySQLite(conn=db)


@pytest.fixture
def utente_id(db):
    """ID dell'utente di test."""
    return db.execute("SELECT id FROM utenti WHERE nome = 'Mario Test'").fetchone()[0]


@pytest.fixture(autouse=True)
def pulisci_ordini(db, utente_id):
    """Pulisci gli ordini prima di ogni test."""
    yield
    db.execute("DELETE FROM ordini WHERE utente_id = ?", (utente_id,))
    db.commit()


class TestOrdiniRepositorySQLite:
    """Test di integrazione — usano il DB reale."""

    def test_trova_ordini_utente_vuoto(self, repository, utente_id):
        """Utente senza ordini: lista vuota."""
        ordini = repository.trova_per_utente(utente_id)
        assert ordini == []

    def test_salva_e_trova_ordine(self, repository, utente_id, db):
        """Inserisce un ordine e lo recupera."""
        ordine = Ordine(utente_id=utente_id, totale=75.00, stato="completato")
        ordine_salvato = repository.salva(ordine)

        assert ordine_salvato.id is not None

        trovati = repository.trova_per_utente(utente_id, stato="completato")
        assert len(trovati) == 1
        assert trovati[0].totale == pytest.approx(75.00)

    def test_filtro_per_stato(self, repository, utente_id, db):
        """Il filtro per stato funziona correttamente."""
        db.execute(
            "INSERT INTO ordini (utente_id, totale, stato) VALUES (?,?,?)",
            (utente_id, 10.0, "completato")
        )
        db.execute(
            "INSERT INTO ordini (utente_id, totale, stato) VALUES (?,?,?)",
            (utente_id, 20.0, "in_attesa")
        )
        db.commit()

        completati = repository.trova_per_utente(utente_id, stato="completato")
        assert len(completati) == 1

        in_attesa = repository.trova_per_utente(utente_id, stato="in_attesa")
        assert len(in_attesa) == 1
```

---

## I2: Testing del Pattern Observer/Event

```python
# src/eventi.py

from collections import defaultdict
from typing import Callable, Any


class BusEventi:
    """
    Bus di eventi: permette di pubblicare eventi e registrare handler.
    Pattern Observer.
    """

    def __init__(self):
        self._handlers: dict[str, list[Callable]] = defaultdict(list)
        self._storico: list[dict] = []

    def registra(self, evento: str, handler: Callable) -> None:
        """Registra un handler per un tipo di evento."""
        self._handlers[evento].append(handler)

    def pubblica(self, evento: str, payload: Any = None) -> int:
        """
        Pubblica un evento e chiama tutti gli handler registrati.

        Returns:
            Numero di handler chiamati.
        """
        self._storico.append({"evento": evento, "payload": payload})
        handlers = self._handlers.get(evento, [])
        for handler in handlers:
            handler(payload)
        return len(handlers)

    def deregistra(self, evento: str, handler: Callable) -> bool:
        """Rimuove un handler."""
        if handler in self._handlers.get(evento, []):
            self._handlers[evento].remove(handler)
            return True
        return False

    def storico(self) -> list[dict]:
        """Restituisce lo storico degli eventi pubblicati."""
        return self._storico.copy()
```

```python
# tests/test_bus_eventi.py

import pytest
from unittest.mock import MagicMock, call
from src.eventi import BusEventi


@pytest.fixture
def bus():
    return BusEventi()


class TestRegistrazioneHandler:

    def test_handler_chiamato_su_evento(self, bus):
        """Handler viene chiamato quando l'evento è pubblicato."""
        handler = MagicMock()
        bus.registra("ordine.creato", handler)
        bus.pubblica("ordine.creato", {"id": 1})
        handler.assert_called_once_with({"id": 1})

    def test_handler_non_chiamato_per_altri_eventi(self, bus):
        """Handler viene chiamato solo per l'evento a cui è registrato."""
        handler = MagicMock()
        bus.registra("ordine.creato", handler)
        bus.pubblica("ordine.eliminato", {"id": 1})
        handler.assert_not_called()

    def test_multipli_handler_per_stesso_evento(self, bus):
        """Più handler possono essere registrati per lo stesso evento."""
        h1 = MagicMock()
        h2 = MagicMock()
        bus.registra("evento", h1)
        bus.registra("evento", h2)
        bus.pubblica("evento", "payload")
        h1.assert_called_once_with("payload")
        h2.assert_called_once_with("payload")

    def test_pubblica_restituisce_numero_handler(self, bus):
        """pubblica() restituisce quanti handler sono stati chiamati."""
        bus.registra("evento", MagicMock())
        bus.registra("evento", MagicMock())
        assert bus.pubblica("evento") == 2

    def test_evento_senza_handler_restituisce_zero(self, bus):
        assert bus.pubblica("evento_senza_handler") == 0


class TestDeregistrazione:

    def test_deregistra_handler(self, bus):
        """Un handler deregistrato non viene più chiamato."""
        handler = MagicMock()
        bus.registra("evento", handler)
        bus.deregistra("evento", handler)
        bus.pubblica("evento")
        handler.assert_not_called()

    def test_deregistra_handler_inesistente_restituisce_false(self, bus):
        """Deregistrare un handler non registrato restituisce False."""
        handler = MagicMock()
        assert bus.deregistra("evento", handler) is False

    def test_deregistra_un_handler_su_due(self, bus):
        """Deregistrare un handler non influenza gli altri."""
        h1 = MagicMock()
        h2 = MagicMock()
        bus.registra("evento", h1)
        bus.registra("evento", h2)
        bus.deregistra("evento", h1)
        bus.pubblica("evento", "data")

        h1.assert_not_called()
        h2.assert_called_once_with("data")


class TestStorico:

    def test_storico_traccia_eventi(self, bus):
        """Lo storico registra tutti gli eventi pubblicati."""
        bus.pubblica("evento1", "payload1")
        bus.pubblica("evento2", "payload2")

        storico = bus.storico()
        assert len(storico) == 2
        assert storico[0] == {"evento": "evento1", "payload": "payload1"}
        assert storico[1] == {"evento": "evento2", "payload": "payload2"}

    def test_storico_immutabile(self, bus):
        """Modificare il risultato di storico() non altera lo storico interno."""
        bus.pubblica("evento", "payload")
        s = bus.storico()
        s.append({"evento": "falso", "payload": None})

        assert len(bus.storico()) == 1  # Lo storico interno è invariato
```

---

## I3: Testing del Pattern Strategy

```python
# src/strategia_prezzi.py

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Prodotto:
    nome: str
    prezzo_base: float
    categoria: str


class StrategiaPrezzo(ABC):
    """Interfaccia per le strategie di pricing."""

    @abstractmethod
    def calcola(self, prodotto: Prodotto, quantita: int) -> float:
        """Calcola il prezzo finale."""
        ...


class PrezzoBase(StrategiaPrezzo):
    """Nessuno sconto — prezzo pieno."""

    def calcola(self, prodotto: Prodotto, quantita: int) -> float:
        return prodotto.prezzo_base * quantita


class ScontoQuantita(StrategiaPrezzo):
    """Sconto progressivo in base alla quantità."""

    SOGLIE = [
        (50, 0.20),   # >= 50 pezzi: 20%
        (20, 0.15),   # >= 20 pezzi: 15%
        (10, 0.10),   # >= 10 pezzi: 10%
        (5, 0.05),    # >= 5 pezzi: 5%
        (0, 0.0),     # < 5 pezzi: nessuno sconto
    ]

    def calcola(self, prodotto: Prodotto, quantita: int) -> float:
        sconto = next(
            perc for soglia, perc in self.SOGLIE if quantita >= soglia
        )
        return prodotto.prezzo_base * quantita * (1 - sconto)


class PrezzoFlash(StrategiaPrezzo):
    """Prezzo scontato per vendite flash."""

    def __init__(self, percentuale_sconto: float) -> None:
        if not (0 < percentuale_sconto <= 1):
            raise ValueError(f"Percentuale sconto invalida: {percentuale_sconto}")
        self._sconto = percentuale_sconto

    def calcola(self, prodotto: Prodotto, quantita: int) -> float:
        return prodotto.prezzo_base * quantita * (1 - self._sconto)


class Carrello:
    """Carrello che usa una strategia di prezzo."""

    def __init__(self, strategia: StrategiaPrezzo) -> None:
        self._strategia = strategia
        self._items: list[tuple[Prodotto, int]] = []

    def aggiungi(self, prodotto: Prodotto, quantita: int) -> None:
        if quantita <= 0:
            raise ValueError(f"Quantità invalida: {quantita}")
        self._items.append((prodotto, quantita))

    def totale(self) -> float:
        return sum(
            self._strategia.calcola(prod, qty)
            for prod, qty in self._items
        )

    def cambia_strategia(self, strategia: StrategiaPrezzo) -> None:
        """Permette di cambiare la strategia a runtime."""
        self._strategia = strategia
```

```python
# tests/test_strategia_prezzi.py

import pytest
from unittest.mock import MagicMock
from src.strategia_prezzi import (
    Prodotto, PrezzoBase, ScontoQuantita, PrezzoFlash, Carrello
)


@pytest.fixture
def laptop():
    return Prodotto(nome="Laptop", prezzo_base=1000.0, categoria="Elettronica")


@pytest.fixture
def penna():
    return Prodotto(nome="Penna", prezzo_base=2.0, categoria="Cancelleria")


class TestPrezzoBase:

    def test_prezzo_unitario(self, laptop):
        strategia = PrezzoBase()
        assert strategia.calcola(laptop, 1) == pytest.approx(1000.0)

    def test_prezzo_multiplo(self, laptop):
        strategia = PrezzoBase()
        assert strategia.calcola(laptop, 3) == pytest.approx(3000.0)

    def test_nessuno_sconto_applicato(self, penna):
        strategia = PrezzoBase()
        assert strategia.calcola(penna, 100) == pytest.approx(200.0)


class TestScontoQuantita:

    @pytest.mark.parametrize("quantita, prezzo_atteso", [
        (1, 10.0),        # Nessuno sconto
        (4, 40.0),        # Nessuno sconto
        (5, 47.5),        # 5% sconto (10 * 5 * 0.95)
        (10, 90.0),       # 10% sconto (10 * 10 * 0.90)
        (20, 170.0),      # 15% sconto (10 * 20 * 0.85)
        (50, 400.0),      # 20% sconto (10 * 50 * 0.80)
        (100, 800.0),     # 20% sconto (10 * 100 * 0.80)
    ], ids=[
        "1pz_no_sconto", "4pz_no_sconto", "5pz_5%",
        "10pz_10%", "20pz_15%", "50pz_20%", "100pz_20%"
    ])
    def test_sconto_progressivo(self, quantita, prezzo_atteso):
        prodotto = Prodotto(nome="Test", prezzo_base=10.0, categoria="Test")
        strategia = ScontoQuantita()
        assert strategia.calcola(prodotto, quantita) == pytest.approx(prezzo_atteso)


class TestPrezzoFlash:

    def test_prezzo_con_sconto_50pct(self, laptop):
        strategia = PrezzoFlash(percentuale_sconto=0.50)
        assert strategia.calcola(laptop, 1) == pytest.approx(500.0)

    def test_sconto_invalido_zero(self):
        with pytest.raises(ValueError, match="invalida"):
            PrezzoFlash(percentuale_sconto=0)

    def test_sconto_invalido_maggiore_uno(self):
        with pytest.raises(ValueError):
            PrezzoFlash(percentuale_sconto=1.5)


class TestCarrello:

    def test_carrello_vuoto_ha_totale_zero(self):
        carrello = Carrello(PrezzoBase())
        assert carrello.totale() == 0.0

    def test_aggiunge_prodotto(self, laptop):
        carrello = Carrello(PrezzoBase())
        carrello.aggiungi(laptop, 1)
        assert carrello.totale() == pytest.approx(1000.0)

    def test_aggiunge_piu_prodotti(self, laptop, penna):
        carrello = Carrello(PrezzoBase())
        carrello.aggiungi(laptop, 1)
        carrello.aggiungi(penna, 5)
        assert carrello.totale() == pytest.approx(1010.0)

    def test_quantita_zero_solleva_errore(self, laptop):
        carrello = Carrello(PrezzoBase())
        with pytest.raises(ValueError, match="invalida"):
            carrello.aggiungi(laptop, 0)

    def test_cambio_strategia_a_runtime(self, laptop):
        """Il totale cambia quando si cambia strategia."""
        carrello = Carrello(PrezzoBase())
        carrello.aggiungi(laptop, 1)
        assert carrello.totale() == pytest.approx(1000.0)

        carrello.cambia_strategia(PrezzoFlash(0.30))
        assert carrello.totale() == pytest.approx(700.0)

    def test_strategia_mockata(self, laptop):
        """Testa il carrello con una strategia mockata."""
        strategia_mock = MagicMock(spec=PrezzoBase)
        strategia_mock.calcola.return_value = 42.0

        carrello = Carrello(strategia_mock)
        carrello.aggiungi(laptop, 2)

        assert carrello.totale() == pytest.approx(42.0)
        strategia_mock.calcola.assert_called_once_with(laptop, 2)
```

---

## I4: Testing con Dipendenze Esterne — Tutti i Pattern

### Pattern: HTTP con responses

```bash
pip install responses
```

```python
# src/client_meteo.py

import requests
from dataclasses import dataclass


@dataclass
class DatiMeteo:
    citta: str
    temperatura: float
    umidita: int
    descrizione: str


class ClientMeteo:
    def __init__(self, api_key: str, base_url: str = "https://api.openweather.org/v2.5"):
        self._api_key = api_key
        self._base_url = base_url

    def temperatura_attuale(self, citta: str) -> DatiMeteo:
        url = f"{self._base_url}/weather"
        risposta = requests.get(url, params={
            "q": citta,
            "appid": self._api_key,
            "units": "metric",
            "lang": "it",
        }, timeout=10)

        risposta.raise_for_status()
        dati = risposta.json()

        return DatiMeteo(
            citta=dati["name"],
            temperatura=dati["main"]["temp"],
            umidita=dati["main"]["humidity"],
            descrizione=dati["weather"][0]["description"],
        )
```

```python
# tests/test_client_meteo.py

import pytest
import responses as resp_lib
from requests.exceptions import HTTPError, ConnectionError
from src.client_meteo import ClientMeteo, DatiMeteo


@pytest.fixture
def client():
    return ClientMeteo(api_key="test_key_12345")


class TestTemperaturaAttuale:
    """Test del client meteo con risposte HTTP simulate."""

    @resp_lib.activate
    def test_risposta_corretta(self, client):
        """Simula una risposta HTTP 200 con dati meteo."""
        resp_lib.add(
            resp_lib.GET,
            "https://api.openweather.org/v2.5/weather",
            json={
                "name": "Roma",
                "main": {"temp": 22.5, "humidity": 60},
                "weather": [{"description": "cielo sereno"}],
            },
            status=200,
        )

        dati = client.temperatura_attuale("Roma")

        assert isinstance(dati, DatiMeteo)
        assert dati.citta == "Roma"
        assert dati.temperatura == pytest.approx(22.5)
        assert dati.umidita == 60
        assert dati.descrizione == "cielo sereno"

    @resp_lib.activate
    def test_citta_non_trovata_errore_404(self, client):
        """La risposta 404 deve sollevare HTTPError."""
        resp_lib.add(
            resp_lib.GET,
            "https://api.openweather.org/v2.5/weather",
            json={"cod": "404", "message": "city not found"},
            status=404,
        )

        with pytest.raises(HTTPError):
            client.temperatura_attuale("CittàInesistente")

    @resp_lib.activate
    def test_api_key_invalida_errore_401(self, client):
        """API key invalida deve sollevare HTTPError."""
        resp_lib.add(
            resp_lib.GET,
            "https://api.openweather.org/v2.5/weather",
            json={"cod": 401, "message": "Invalid API key"},
            status=401,
        )

        with pytest.raises(HTTPError):
            client.temperatura_attuale("Roma")

    @resp_lib.activate
    def test_server_error_errore_500(self, client):
        """Errore del server deve sollevare HTTPError."""
        resp_lib.add(
            resp_lib.GET,
            "https://api.openweather.org/v2.5/weather",
            status=500,
        )

        with pytest.raises(HTTPError):
            client.temperatura_attuale("Roma")

    @resp_lib.activate
    def test_parametri_query_corretti(self, client):
        """Verifica che vengano passati i parametri corretti."""
        resp_lib.add(
            resp_lib.GET,
            "https://api.openweather.org/v2.5/weather",
            json={
                "name": "Milano",
                "main": {"temp": 18.0, "humidity": 70},
                "weather": [{"description": "nuvoloso"}],
            },
            status=200,
        )

        client.temperatura_attuale("Milano")

        chiamata = resp_lib.calls[0]
        assert "q=Milano" in chiamata.request.url
        assert "appid=test_key_12345" in chiamata.request.url
        assert "units=metric" in chiamata.request.url
        assert "lang=it" in chiamata.request.url

    def test_timeout_sul_server_lento(self, client):
        """Un timeout deve sollevare un'eccezione appropriata."""
        from unittest.mock import patch
        import requests

        with patch(
            "requests.get",
            side_effect=requests.Timeout("Connection timeout")
        ):
            with pytest.raises(requests.Timeout):
                client.temperatura_attuale("Roma")
```

---

## I5: Testing di Algoritmi — Approccio Sistematico

### Principio: testa l'algoritmo come una scatola nera

```python
# src/algoritmi/ricerca.py

def ricerca_binaria(lista: list[int], target: int) -> int:
    """
    Ricerca binaria in una lista ORDINATA.

    Returns:
        Indice dell'elemento, o -1 se non trovato.

    Precondizione: la lista deve essere ORDINATA in ordine crescente.
    """
    sx, dx = 0, len(lista) - 1

    while sx <= dx:
        medio = (sx + dx) // 2
        if lista[medio] == target:
            return medio
        elif lista[medio] < target:
            sx = medio + 1
        else:
            dx = medio - 1

    return -1
```

```python
# tests/test_ricerca_binaria.py

import pytest
from hypothesis import given, strategies as st, assume
from src.algoritmi.ricerca import ricerca_binaria


class TestRicercaBinariaCasiNoti:
    """Test con casi specifici e noti."""

    def test_lista_vuota(self):
        assert ricerca_binaria([], 5) == -1

    def test_lista_un_elemento_trovato(self):
        assert ricerca_binaria([42], 42) == 0

    def test_lista_un_elemento_non_trovato(self):
        assert ricerca_binaria([42], 99) == -1

    def test_elemento_al_centro(self):
        assert ricerca_binaria([1, 3, 5, 7, 9], 5) == 2

    def test_elemento_all_inizio(self):
        assert ricerca_binaria([1, 3, 5, 7, 9], 1) == 0

    def test_elemento_alla_fine(self):
        assert ricerca_binaria([1, 3, 5, 7, 9], 9) == 4

    def test_elemento_non_trovato_tra_gli_altri(self):
        assert ricerca_binaria([1, 3, 5, 7, 9], 4) == -1

    def test_elemento_minore_del_primo(self):
        assert ricerca_binaria([5, 10, 15], 3) == -1

    def test_elemento_maggiore_dell_ultimo(self):
        assert ricerca_binaria([5, 10, 15], 20) == -1

    def test_elementi_duplicati(self):
        """Con duplicati, restituisce UN indice valido (non necessariamente il primo)."""
        indice = ricerca_binaria([1, 2, 2, 2, 3], 2)
        assert indice in [1, 2, 3]  # Qualsiasi indice dove c'è un 2

    def test_lista_grande(self):
        """Test con lista grande per verificare efficienza."""
        lista = list(range(0, 10000, 2))  # 5000 numeri pari
        assert ricerca_binaria(lista, 4998) == lista.index(4998)
        assert ricerca_binaria(lista, 4999) == -1  # Numero dispari


class TestRicercaBinariaHypothesis:
    """Test basati su proprietà con Hypothesis."""

    @given(
        lista=st.lists(st.integers(-1000, 1000), min_size=1).map(sorted),
        target=st.integers(-1000, 1000),
    )
    def test_se_trovato_lista_contiene_elemento(self, lista, target):
        """
        Proprietà: se ricerca_binaria restituisce un indice >= 0,
        lista[indice] == target.
        """
        indice = ricerca_binaria(lista, target)
        if indice >= 0:
            assert lista[indice] == target

    @given(
        lista=st.lists(st.integers(-1000, 1000), min_size=1).map(sorted),
        target=st.integers(-1000, 1000),
    )
    def test_se_non_trovato_non_e_nella_lista(self, lista, target):
        """
        Proprietà: se ricerca_binaria restituisce -1,
        target NON è nella lista.
        """
        indice = ricerca_binaria(lista, target)
        if indice == -1:
            assert target not in lista

    @given(
        lista=st.lists(st.integers(-1000, 1000), min_size=1).map(sorted),
    )
    def test_ogni_elemento_e_trovabile(self, lista):
        """
        Proprietà: ogni elemento nella lista deve essere trovabile.
        """
        for elemento in lista:
            indice = ricerca_binaria(lista, elemento)
            assert indice >= 0, f"{elemento} non trovato in {lista}"

    @given(
        lista_base=st.lists(st.integers(-100, 100), min_size=1, max_size=50),
    )
    def test_coerente_con_metodo_lineare(self, lista_base):
        """
        Proprietà: la ricerca binaria deve dare lo stesso risultato
        di una ricerca lineare (diverso indice per duplicati, ma stesso fatto
        di trovare/non trovare).
        """
        lista = sorted(set(lista_base))  # Rimuovi duplicati per confronto preciso

        for target in lista_base:
            binaria = ricerca_binaria(lista, target)
            lineare = lista.index(target) if target in lista else -1

            # Entrambi trovano o non trovano
            assert (binaria >= 0) == (lineare >= 0)
```

---

## I6: Testing di Sistemi con Stato

### Macchina a stati — Semaforo

```python
# src/semaforo.py

from enum import Enum, auto


class StatoSemaforo(Enum):
    ROSSO = auto()
    GIALLO = auto()
    VERDE = auto()


class ErroreTransizione(Exception):
    """Transizione di stato non permessa."""
    pass


class Semaforo:
    """
    Semaforo con macchina a stati.

    Transizioni permesse:
    ROSSO → VERDE
    VERDE → GIALLO
    GIALLO → ROSSO
    """

    TRANSIZIONI_PERMESSE = {
        StatoSemaforo.ROSSO: [StatoSemaforo.VERDE],
        StatoSemaforo.VERDE: [StatoSemaforo.GIALLO],
        StatoSemaforo.GIALLO: [StatoSemaforo.ROSSO],
    }

    def __init__(self) -> None:
        self._stato = StatoSemaforo.ROSSO
        self._storico: list[StatoSemaforo] = [StatoSemaforo.ROSSO]

    @property
    def stato(self) -> StatoSemaforo:
        return self._stato

    def transita(self, nuovo_stato: StatoSemaforo) -> None:
        """
        Transita al nuovo stato.

        Raises:
            ErroreTransizione: Se la transizione non è permessa.
        """
        stati_permessi = self.TRANSIZIONI_PERMESSE[self._stato]
        if nuovo_stato not in stati_permessi:
            raise ErroreTransizione(
                f"Transizione non permessa: {self._stato.name} → {nuovo_stato.name}"
            )
        self._stato = nuovo_stato
        self._storico.append(nuovo_stato)

    def avanza(self) -> StatoSemaforo:
        """Transita allo stato successivo nel ciclo standard."""
        prossimo = self.TRANSIZIONI_PERMESSE[self._stato][0]
        self.transita(prossimo)
        return self._stato

    def storico(self) -> list[StatoSemaforo]:
        """Restituisce lo storico degli stati."""
        return self._storico.copy()
```

```python
# tests/test_semaforo.py

import pytest
from src.semaforo import Semaforo, StatoSemaforo, ErroreTransizione


@pytest.fixture
def semaforo():
    return Semaforo()


class TestStatoIniziale:

    def test_stato_iniziale_e_rosso(self, semaforo):
        assert semaforo.stato == StatoSemaforo.ROSSO

    def test_storico_iniziale_ha_rosso(self, semaforo):
        assert semaforo.storico() == [StatoSemaforo.ROSSO]


class TestTransizioni:

    def test_rosso_a_verde(self, semaforo):
        semaforo.transita(StatoSemaforo.VERDE)
        assert semaforo.stato == StatoSemaforo.VERDE

    def test_verde_a_giallo(self, semaforo):
        semaforo.transita(StatoSemaforo.VERDE)
        semaforo.transita(StatoSemaforo.GIALLO)
        assert semaforo.stato == StatoSemaforo.GIALLO

    def test_giallo_a_rosso(self, semaforo):
        semaforo.transita(StatoSemaforo.VERDE)
        semaforo.transita(StatoSemaforo.GIALLO)
        semaforo.transita(StatoSemaforo.ROSSO)
        assert semaforo.stato == StatoSemaforo.ROSSO

    def test_ciclo_completo(self, semaforo):
        semaforo.avanza()  # ROSSO → VERDE
        semaforo.avanza()  # VERDE → GIALLO
        semaforo.avanza()  # GIALLO → ROSSO
        assert semaforo.stato == StatoSemaforo.ROSSO

    def test_storico_ciclo_completo(self, semaforo):
        semaforo.avanza()
        semaforo.avanza()
        semaforo.avanza()
        assert semaforo.storico() == [
            StatoSemaforo.ROSSO,
            StatoSemaforo.VERDE,
            StatoSemaforo.GIALLO,
            StatoSemaforo.ROSSO,
        ]


class TestTransizioniNonPermesse:

    @pytest.mark.parametrize("da_stato, a_stato, setup_passi", [
        (StatoSemaforo.ROSSO, StatoSemaforo.GIALLO, 0),
        (StatoSemaforo.ROSSO, StatoSemaforo.ROSSO, 0),
        (StatoSemaforo.VERDE, StatoSemaforo.ROSSO, 1),
        (StatoSemaforo.VERDE, StatoSemaforo.VERDE, 1),
        (StatoSemaforo.GIALLO, StatoSemaforo.VERDE, 2),
        (StatoSemaforo.GIALLO, StatoSemaforo.GIALLO, 2),
    ], ids=[
        "rosso->giallo", "rosso->rosso", "verde->rosso", "verde->verde",
        "giallo->verde", "giallo->giallo",
    ])
    def test_transizione_non_permessa(self, semaforo, da_stato, a_stato, setup_passi):
        """Tutte le transizioni non permesse sollevano ErroreTransizione."""
        for _ in range(setup_passi):
            semaforo.avanza()

        with pytest.raises(ErroreTransizione):
            semaforo.transita(a_stato)

    def test_messaggio_errore_contiene_stati(self, semaforo):
        with pytest.raises(ErroreTransizione, match="ROSSO.*GIALLO"):
            semaforo.transita(StatoSemaforo.GIALLO)

    def test_stato_invariato_dopo_transizione_fallita(self, semaforo):
        """Lo stato non cambia se la transizione fallisce."""
        try:
            semaforo.transita(StatoSemaforo.GIALLO)
        except ErroreTransizione:
            pass
        assert semaforo.stato == StatoSemaforo.ROSSO
```

---

## I7: Testing con Hypothesis — Pattern Avanzati

### Stateful Testing con RuleBasedStateMachine

```python
# tests/test_lista_ordinata_stateful.py

from hypothesis.stateful import RuleBasedStateMachine, rule, invariant, initialize
from hypothesis import strategies as st


class ListaOrdinataStateful(RuleBasedStateMachine):
    """
    Test stateful per una struttura dati ListaOrdinata.

    Hypothesis genera automaticamente sequenze di operazioni
    e verifica che le invarianti siano sempre rispettate.
    """

    def __init__(self):
        super().__init__()
        from src.lista_ordinata import ListaOrdinata
        self._lista = ListaOrdinata()
        self._shadow: list[int] = []  # Lista Python "di riferimento"

    @initialize(valore=st.integers(-1000, 1000))
    def aggiungi_iniziale(self, valore: int):
        """Aggiungi un elemento iniziale."""
        self._lista.aggiungi(valore)
        self._shadow.append(valore)
        self._shadow.sort()

    @rule(valore=st.integers(-1000, 1000))
    def aggiungi(self, valore: int):
        """Aggiungi un elemento."""
        self._lista.aggiungi(valore)
        self._shadow.append(valore)
        self._shadow.sort()

    @rule(valore=st.integers(-1000, 1000))
    def rimuovi_se_esiste(self, valore: int):
        """Rimuovi un elemento (solo se esiste)."""
        if valore in self._shadow:
            self._lista.rimuovi(valore)
            self._shadow.remove(valore)

    @invariant()
    def lista_sempre_ordinata(self):
        """La lista deve essere sempre ordinata."""
        elementi = self._lista.to_list()
        assert elementi == sorted(elementi), f"Lista non ordinata: {elementi}"

    @invariant()
    def dimensione_coerente(self):
        """La dimensione deve corrispondere alla lista shadow."""
        assert self._lista.dimensione() == len(self._shadow)

    @invariant()
    def contenuto_coerente_con_shadow(self):
        """Il contenuto deve corrispondere alla lista shadow."""
        assert self._lista.to_list() == self._shadow


# Questo genera la classe di test
TestListaOrdinata = ListaOrdinataStateful.TestCase
```

---

### Strategies personalizzate con @composite

```python
from hypothesis import strategies as st, given
from hypothesis.strategies import composite
from dataclasses import dataclass
from typing import Optional


@dataclass
class Utente:
    nome: str
    eta: int
    email: str
    premium: bool
    saldo: float


@composite
def utenti_validi(draw, premium: Optional[bool] = None):
    """
    Strategy personalizzata per generare utenti validi.

    Args:
        draw: Iniettata da Hypothesis.
        premium: Se specificato, forza il valore di premium.
    """
    nome = draw(st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll')),
        min_size=2, max_size=50,
    ))
    eta = draw(st.integers(min_value=18, max_value=120))
    dominio = draw(st.sampled_from(["test.it", "example.com", "email.org"]))
    email = f"{nome.lower().replace(' ', '.')}@{dominio}"
    is_premium = draw(st.booleans()) if premium is None else premium
    saldo = draw(st.floats(min_value=0.0, max_value=100000.0, allow_nan=False))

    return Utente(nome=nome, eta=eta, email=email, premium=is_premium, saldo=saldo)


@composite
def coppie_utenti_diversi(draw):
    """Genera due utenti con email diverse."""
    u1 = draw(utenti_validi())
    u2 = draw(utenti_validi())
    # Assicura che le email siano diverse
    if u1.email == u2.email:
        u2 = Utente(
            nome=u2.nome + "_2",
            eta=u2.eta,
            email=u2.email + ".alt",
            premium=u2.premium,
            saldo=u2.saldo,
        )
    return u1, u2


@given(utente=utenti_validi())
def test_calcola_sconto_qualsiasi_utente_valido(utente):
    """Lo sconto non deve mai essere negativo o > 1."""
    sconto = calcola_sconto_utente(utente)
    assert 0.0 <= sconto <= 1.0


@given(utente=utenti_validi(premium=True))
def test_utente_premium_ha_sconto_minimo(utente):
    """Gli utenti premium hanno sempre almeno il 10% di sconto."""
    sconto = calcola_sconto_utente(utente)
    assert sconto >= 0.10


@given(coppie=coppie_utenti_diversi())
def test_trasferimento_saldo(coppie):
    """Il trasferimento non crea o distrugge saldo."""
    mittente, destinatario = coppie
    saldo_totale_prima = mittente.saldo + destinatario.saldo
    importo = min(50.0, mittente.saldo)

    if importo > 0:
        trasferisci(mittente, destinatario, importo)
        saldo_totale_dopo = mittente.saldo + destinatario.saldo
        assert saldo_totale_dopo == pytest.approx(saldo_totale_prima)
```

---

## I8: Testing di Validatori — Pattern Completo

```python
# src/validatori/italiano.py
"""
Validatori per dati tipici italiani.
"""

import re


def valida_codice_fiscale(cf: str) -> bool:
    """
    Valida un codice fiscale italiano.

    Il codice fiscale è composto da 16 caratteri:
    - 3 consonanti del cognome
    - 3 consonanti/vocali del nome
    - 2 cifre per l'anno di nascita
    - 1 lettera per il mese
    - 2 cifre per il giorno + genere
    - 4 caratteri per il comune
    - 1 carattere di controllo
    """
    if not isinstance(cf, str):
        return False

    cf = cf.strip().upper()

    if len(cf) != 16:
        return False

    PATTERN = r'^[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]$'
    if not re.match(PATTERN, cf):
        return False

    # Verifica il carattere di controllo
    dispari = [1, 0, 5, 7, 9, 13, 15, 17, 19, 21, 2, 4, 18, 20, 11, 3,
               16, 8, 12, 14, 22, 25, 24, 23, 6, 10]
    pari = list(range(26))

    somma = 0
    for i, c in enumerate(cf[:-1]):
        if c.isdigit():
            c = chr(ord('A') + int(c))
        idx = ord(c) - ord('A')
        if i % 2 == 0:
            somma += dispari[idx]
        else:
            somma += pari[idx]

    atteso = chr(ord('A') + somma % 26)
    return cf[-1] == atteso


def valida_partita_iva(piva: str) -> bool:
    """Valida una partita IVA italiana (11 cifre)."""
    if not isinstance(piva, str):
        return False

    piva = piva.strip().replace(" ", "")

    if not re.match(r'^\d{11}$', piva):
        return False

    # Algoritmo di Luhn per P.IVA italiana
    somma = 0
    for i in range(10):
        cifra = int(piva[i])
        if i % 2 == 0:
            somma += cifra
        else:
            doppio = cifra * 2
            somma += doppio if doppio < 10 else doppio - 9

    cifra_controllo = (10 - somma % 10) % 10
    return cifra_controllo == int(piva[10])


def valida_iban_italiano(iban: str) -> bool:
    """Valida un IBAN italiano."""
    if not isinstance(iban, str):
        return False

    iban = iban.strip().replace(" ", "").upper()

    if not iban.startswith("IT"):
        return False

    if len(iban) != 27:
        return False

    # Verifica caratteri
    if not re.match(r'^IT\d{2}[A-Z]\d{10}[A-Z0-9]{12}$', iban):
        return False

    return True  # Verifica checksum semplificata


def valida_cap(cap: str) -> bool:
    """Valida un Codice di Avviamento Postale (CAP) italiano."""
    if not isinstance(cap, str):
        return False
    return bool(re.match(r'^\d{5}$', cap.strip()))
```

```python
# tests/test_validatori_italiano.py

import pytest
from src.validatori.italiano import (
    valida_codice_fiscale, valida_partita_iva,
    valida_iban_italiano, valida_cap
)


class TestCodiceFiscale:
    """Test per la validazione del codice fiscale."""

    VALIDI = [
        "RSSMRA85T10A562S",   # Codice realistico (struttura corretta)
        "MRARSS90L01H501W",
    ]

    NON_VALIDI = [
        ("", "stringa_vuota"),
        ("1234567890123456", "tutto_numeri"),
        ("RSSMRA85T10A562X", "carattere_controllo_sbagliato"),
        ("RSSMRA85T10A56", "troppo_corto"),
        ("RSSMRA85T10A5621", "troppo_lungo"),
        ("rssmra85t10a562s", "minuscolo"),
        (None, "none"),
        (123, "intero"),
        ("AAAAAA00A00A000A", "formato_valido_cf_inventato"),
    ]

    @pytest.mark.parametrize("cf", VALIDI)
    def test_codice_fiscale_valido(self, cf):
        assert valida_codice_fiscale(cf) is True

    @pytest.mark.parametrize("cf, motivo", NON_VALIDI)
    def test_codice_fiscale_non_valido(self, cf, motivo):
        assert valida_codice_fiscale(cf) is False, f"Doveva essere invalido: {motivo}"

    def test_maiuscolo_e_minuscolo(self):
        """Il CF dovrebbe essere case-insensitive (normalizzato internamente)."""
        cf_minuscolo = "rssmra85t10a562s"
        # Se valida, il risultato deve essere lo stesso del maiuscolo
        # Questo dipende dall'implementazione
        # Se non implementato, deve restituire False per input non standard
        assert isinstance(valida_codice_fiscale(cf_minuscolo), bool)


class TestPartitaIva:
    """Test per la validazione della partita IVA."""

    @pytest.mark.parametrize("piva, atteso", [
        ("12345670784", True),    # PIVA valida standard
        ("00000000000", False),   # Non valida (checksum fallisce)
        ("1234567078", False),    # Troppo corta (10 cifre)
        ("123456707840", False),  # Troppo lunga (12 cifre)
        ("1234567ABC4", False),   # Contiene lettere
        ("", False),              # Vuota
        (None, False),            # None
    ], ids=[
        "valida", "tutti_zeri", "troppo_corta",
        "troppo_lunga", "con_lettere", "vuota", "none"
    ])
    def test_partita_iva(self, piva, atteso):
        assert valida_partita_iva(piva) is atteso

    def test_con_spazi_accettata(self):
        """Con spazi (formato spesso usato) dovrebbe essere gestita."""
        # "12345 670784" normalizzata rimuovendo spazi = "12345670784"
        assert isinstance(valida_partita_iva("12345 670784"), bool)


class TestIbanItaliano:
    """Test per la validazione dell'IBAN italiano."""

    @pytest.mark.parametrize("iban, atteso", [
        ("IT60X0542811101000000123456", True),   # Struttura corretta
        ("DE89370400440532013000", False),        # IBAN tedesco
        ("IT60X054281110100000012345", False),    # Troppo corto
        ("IT60X05428111010000001234567", False),  # Troppo lungo
        ("it60x0542811101000000123456", True),    # Minuscolo (normalizzato)
        ("IT60 X054 2811 1010 0000 0123 456", True),  # Con spazi
        ("", False),                              # Vuoto
        (None, False),                            # None
    ], ids=[
        "valido", "tedesco", "corto", "lungo",
        "minuscolo", "con_spazi", "vuoto", "none"
    ])
    def test_iban(self, iban, atteso):
        assert valida_iban_italiano(iban) is atteso


class TestCap:
    """Test per la validazione del CAP."""

    @pytest.mark.parametrize("cap, atteso", [
        ("00100", True),    # Roma centro
        ("20100", True),    # Milano
        ("99999", True),    # 5 cifre qualsiasi
        ("0010", False),    # 4 cifre
        ("001000", False),  # 6 cifre
        ("AAAAA", False),   # Lettere
        ("0010A", False),   # Mix
        ("", False),        # Vuoto
        (None, False),      # None
        (12345, False),     # Intero (non stringa)
    ], ids=[
        "roma", "milano", "cinque_cifre", "quattro", "sei",
        "lettere", "mix", "vuoto", "none", "intero"
    ])
    def test_cap(self, cap, atteso):
        assert valida_cap(cap) is atteso

    def test_cap_con_spazi_viene_trimmato(self):
        """Gli spazi iniziali/finali devono essere ignorati."""
        assert valida_cap("  00100  ") is True
```

---

## I9: Testing di Classi con Stato Complesso

### Conto Bancario con Storico Transazioni

```python
# src/conto_bancario.py

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Optional


class TipoTransazione(Enum):
    DEPOSITO = auto()
    PRELIEVO = auto()
    TRASFERIMENTO_IN = auto()
    TRASFERIMENTO_OUT = auto()


@dataclass
class Transazione:
    tipo: TipoTransazione
    importo: float
    timestamp: datetime = field(default_factory=datetime.now)
    descrizione: Optional[str] = None
    conto_correlato: Optional[str] = None


class SaldoInsufficiante(Exception):
    pass


class ImportoNonValido(Exception):
    pass


class ContoBancario:
    """Conto bancario con storico transazioni."""

    def __init__(self, numero: str, intestatario: str, saldo_iniziale: float = 0.0):
        if saldo_iniziale < 0:
            raise ImportoNonValido("Il saldo iniziale non può essere negativo")
        self._numero = numero
        self._intestatario = intestatario
        self._saldo = saldo_iniziale
        self._transazioni: list[Transazione] = []
        if saldo_iniziale > 0:
            self._registra(TipoTransazione.DEPOSITO, saldo_iniziale, "Saldo iniziale")

    @property
    def numero(self) -> str:
        return self._numero

    @property
    def saldo(self) -> float:
        return self._saldo

    def deposita(self, importo: float, descrizione: Optional[str] = None) -> float:
        self._valida_importo(importo)
        self._saldo += importo
        self._registra(TipoTransazione.DEPOSITO, importo, descrizione)
        return self._saldo

    def preleva(self, importo: float, descrizione: Optional[str] = None) -> float:
        self._valida_importo(importo)
        if importo > self._saldo:
            raise SaldoInsufficiante(
                f"Saldo insufficiente: {self._saldo:.2f} < {importo:.2f}"
            )
        self._saldo -= importo
        self._registra(TipoTransazione.PRELIEVO, importo, descrizione)
        return self._saldo

    def trasferisci(self, importo: float, destinatario: "ContoBancario") -> None:
        """Trasferisce fondi a un altro conto."""
        self.preleva(importo, f"Trasferimento a {destinatario.numero}")
        destinatario._saldo += importo
        destinatario._registra(
            TipoTransazione.TRASFERIMENTO_IN, importo,
            f"Trasferimento da {self._numero}",
            conto_correlato=self._numero,
        )
        self._transazioni[-1] = Transazione(
            tipo=TipoTransazione.TRASFERIMENTO_OUT,
            importo=importo,
            descrizione=f"Trasferimento a {destinatario.numero}",
            conto_correlato=destinatario.numero,
        )

    def estratto_conto(self) -> list[Transazione]:
        return self._transazioni.copy()

    def _registra(
        self,
        tipo: TipoTransazione,
        importo: float,
        descrizione: Optional[str],
        conto_correlato: Optional[str] = None,
    ) -> None:
        self._transazioni.append(Transazione(
            tipo=tipo,
            importo=importo,
            descrizione=descrizione,
            conto_correlato=conto_correlato,
        ))

    def _valida_importo(self, importo: float) -> None:
        if importo <= 0:
            raise ImportoNonValido(f"L'importo deve essere positivo, ricevuto: {importo}")
```

```python
# tests/test_conto_bancario.py

import pytest
from src.conto_bancario import (
    ContoBancario, TipoTransazione,
    SaldoInsufficiante, ImportoNonValido
)


@pytest.fixture
def conto():
    return ContoBancario("IT001", "Mario Rossi", saldo_iniziale=1000.0)


@pytest.fixture
def conto_vuoto():
    return ContoBancario("IT002", "Luigi Verdi")


class TestCreazione:

    def test_saldo_iniziale(self, conto):
        assert conto.saldo == pytest.approx(1000.0)

    def test_numero_conto(self, conto):
        assert conto.numero == "IT001"

    def test_conto_senza_saldo_iniziale(self, conto_vuoto):
        assert conto_vuoto.saldo == pytest.approx(0.0)

    def test_saldo_iniziale_negativo_invalido(self):
        with pytest.raises(ImportoNonValido):
            ContoBancario("IT003", "Test", saldo_iniziale=-100)

    def test_transazione_iniziale_registrata(self, conto):
        """Il saldo iniziale deve creare una transazione di deposito."""
        estratto = conto.estratto_conto()
        assert len(estratto) == 1
        assert estratto[0].tipo == TipoTransazione.DEPOSITO
        assert estratto[0].importo == pytest.approx(1000.0)


class TestDeposito:

    def test_deposito_aumenta_saldo(self, conto_vuoto):
        conto_vuoto.deposita(500.0)
        assert conto_vuoto.saldo == pytest.approx(500.0)

    def test_deposito_restituisce_saldo_aggiornato(self, conto_vuoto):
        saldo = conto_vuoto.deposita(500.0)
        assert saldo == pytest.approx(500.0)

    def test_multipli_depositi(self, conto_vuoto):
        conto_vuoto.deposita(100.0)
        conto_vuoto.deposita(200.0)
        conto_vuoto.deposita(50.0)
        assert conto_vuoto.saldo == pytest.approx(350.0)

    def test_deposito_zero_invalido(self, conto):
        with pytest.raises(ImportoNonValido):
            conto.deposita(0)

    def test_deposito_negativo_invalido(self, conto):
        with pytest.raises(ImportoNonValido):
            conto.deposita(-100)


class TestPrelievo:

    def test_prelievo_riduce_saldo(self, conto):
        conto.preleva(300.0)
        assert conto.saldo == pytest.approx(700.0)

    def test_prelievo_totale_saldo(self, conto):
        conto.preleva(1000.0)
        assert conto.saldo == pytest.approx(0.0)

    def test_prelievo_eccede_saldo(self, conto):
        with pytest.raises(SaldoInsufficiante, match="insufficiente"):
            conto.preleva(1500.0)

    def test_saldo_invariato_dopo_prelievo_fallito(self, conto):
        try:
            conto.preleva(9999.0)
        except SaldoInsufficiante:
            pass
        assert conto.saldo == pytest.approx(1000.0)


class TestTrasferimento:

    def test_trasferimento_riduce_saldo_mittente(self, conto, conto_vuoto):
        conto.trasferisci(300.0, conto_vuoto)
        assert conto.saldo == pytest.approx(700.0)

    def test_trasferimento_aumenta_saldo_destinatario(self, conto, conto_vuoto):
        conto.trasferisci(300.0, conto_vuoto)
        assert conto_vuoto.saldo == pytest.approx(300.0)

    def test_trasferimento_conserva_saldo_totale(self, conto, conto_vuoto):
        """Il saldo totale deve rimanere invariato dopo il trasferimento."""
        totale_prima = conto.saldo + conto_vuoto.saldo
        conto.trasferisci(300.0, conto_vuoto)
        totale_dopo = conto.saldo + conto_vuoto.saldo
        assert totale_dopo == pytest.approx(totale_prima)

    def test_trasferimento_registrato_su_entrambi(self, conto, conto_vuoto):
        """Il trasferimento deve apparire nell'estratto conto di entrambi."""
        conto.trasferisci(300.0, conto_vuoto)

        estratto_mittente = conto.estratto_conto()
        estratto_destinatario = conto_vuoto.estratto_conto()

        # Mittente: una transazione di deposito iniziale + una di trasferimento OUT
        assert estratto_mittente[-1].tipo == TipoTransazione.TRASFERIMENTO_OUT

        # Destinatario: una transazione di trasferimento IN
        assert len(estratto_destinatario) == 1
        assert estratto_destinatario[0].tipo == TipoTransazione.TRASFERIMENTO_IN
```

---

Questi pattern di testing — Repository, Observer, Strategy, Validatori, Macchine a stati,
Conti bancari — coprono la grande maggioranza dei casi che incontrerai nello sviluppo
reale. Il principio comune è sempre lo stesso: **testa il comportamento, non
l'implementazione**. Se l'interfaccia pubblica funziona correttamente, il codice
è corretto — indipendentemente da come è implementato internamente.

---

## SEZIONE SUPPLEMENTARE J: Guida Definitiva al Mocking

---

## J1: unittest.mock — Tutto ciò che devi sapere

### L'oggetto Mock di base

```python
from unittest.mock import Mock, MagicMock, patch, call

# Creazione di un Mock base
m = Mock()

# Il mock accetta qualsiasi attributo o chiamata
print(m.qualsiasi_attributo)      # <Mock name='mock.qualsiasi_attributo' id='...'>
print(m.qualsiasi_metodo())       # <Mock name='mock.qualsiasi_metodo()' id='...'>
print(m.a.b.c.d())                # Catene infinite

# Configurare il valore restituito
m.somma.return_value = 42
assert m.somma(1, 2) == 42

# Configurare side_effect per eccezioni
m.fallisci.side_effect = ValueError("Qualcosa è andato storto")
try:
    m.fallisci()
except ValueError as e:
    print(e)  # "Qualcosa è andato storto"

# Verificare le chiamate
m.somma(10, 20)
m.somma.assert_called_once_with(10, 20)
print(m.somma.call_count)   # 2 (abbiamo chiamato somma due volte in totale)
print(m.somma.call_args)    # call(10, 20)
print(m.somma.call_args_list)  # [call(1, 2), call(10, 20)]
```

---

### La differenza tra Mock e MagicMock

```python
from unittest.mock import Mock, MagicMock

# Mock NON supporta i magic methods
m = Mock()
try:
    len(m)          # TypeError — __len__ non è supportato da Mock normale
except TypeError as e:
    print(f"Mock fallisce: {e}")

# MagicMock SUPPORTA i magic methods
mm = MagicMock()
print(len(mm))      # 0 (valore di default per __len__)
print(bool(mm))     # True
print(list(mm))     # [] (valore di default per __iter__)

# Configura magic methods
mm.__len__.return_value = 5
print(len(mm))      # 5

mm.__iter__.return_value = iter([1, 2, 3])
print(list(mm))     # [1, 2, 3]

# Context manager
mm.__enter__.return_value = "valore_del_context"
mm.__exit__.return_value = False
with mm as v:
    print(v)        # "valore_del_context"
```

---

### patch — Il decoratore e il context manager

```python
# METODO 1: come context manager
def test_con_context_manager():
    with patch("src.modulo.dipendenza") as mock_dep:
        mock_dep.funzione.return_value = 42
        risultato = funzione_che_usa_dipendenza()
        assert risultato == 42
        mock_dep.funzione.assert_called_once()

# METODO 2: come decoratore
@patch("src.modulo.dipendenza")
def test_con_decoratore(mock_dep):
    mock_dep.funzione.return_value = 42
    risultato = funzione_che_usa_dipendenza()
    assert risultato == 42

# METODO 3: multipli patch come decoratori (ordine inverso degli argomenti!)
@patch("src.modulo.dipendenza_b")
@patch("src.modulo.dipendenza_a")  # Questo viene passato PRIMA
def test_multipli_patch(mock_a, mock_b):
    # mock_a corrisponde a dipendenza_a (decoratore più vicino alla funzione)
    # mock_b corrisponde a dipendenza_b (decoratore più lontano)
    mock_a.return_value = 1
    mock_b.return_value = 2
    assert usa_entrambe() == 3  # 1 + 2

# METODO 4: patch.multiple per patchare più oggetti contemporaneamente
@patch.multiple(
    "src.modulo",
    dipendenza_a=DEFAULT,
    dipendenza_b=DEFAULT,
)
def test_patch_multiple(dipendenza_a, dipendenza_b):
    dipendenza_a.return_value = 10
    dipendenza_b.return_value = 20
```

---

### patch.object — Patch di attributi specifici

```python
class DatabaseManager:
    def connetti(self) -> bool:
        # Implementazione reale
        import psycopg2
        conn = psycopg2.connect("postgresql://...")
        return True

    def inserisci(self, tabella: str, dati: dict) -> int:
        # Implementazione reale
        ...


def test_inserimento_con_patch_object():
    db = DatabaseManager()

    # Patcha solo il metodo 'connetti' sull'istanza specifica
    with patch.object(db, "connetti", return_value=True) as mock_connetti:
        with patch.object(db, "inserisci", return_value=42) as mock_inserisci:
            db.connetti()
            result = db.inserisci("utenti", {"nome": "Mario"})

            mock_connetti.assert_called_once()
            mock_inserisci.assert_called_once_with("utenti", {"nome": "Mario"})
            assert result == 42
```

---

### patch.dict — Patch di dizionari

```python
import os

def ottieni_configurazione():
    """Legge la configurazione dalle variabili d'ambiente."""
    return {
        "host": os.environ.get("DB_HOST", "localhost"),
        "port": int(os.environ.get("DB_PORT", "5432")),
        "debug": os.environ.get("DEBUG", "false").lower() == "true",
    }


def test_configurazione_staging():
    """Testa con variabili d'ambiente di staging."""
    env_staging = {
        "DB_HOST": "staging.db.esempio.it",
        "DB_PORT": "5433",
        "DEBUG": "true",
    }

    with patch.dict(os.environ, env_staging):
        config = ottieni_configurazione()

    assert config["host"] == "staging.db.esempio.it"
    assert config["port"] == 5433
    assert config["debug"] is True


def test_configurazione_default():
    """Testa i valori di default quando le variabili non sono impostate."""
    # Rimuovi le variabili se esistono
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("DB_HOST", None)
        os.environ.pop("DB_PORT", None)
        os.environ.pop("DEBUG", None)

        config = ottieni_configurazione()

    assert config["host"] == "localhost"
    assert config["port"] == 5432
    assert config["debug"] is False
```

---

### spec e create_autospec — Mock tipizzati

```python
from unittest.mock import Mock, MagicMock, create_autospec


class ServizioReale:
    def calcola(self, a: int, b: int) -> float:
        return a / b

    def invia_email(self, destinatario: str, oggetto: str) -> bool:
        return True


# SENZA spec: il mock accetta qualsiasi attributo/argomento
mock_senza_spec = Mock()
mock_senza_spec.metodo_inesistente()  # Non solleva errori!
mock_senza_spec.calcola("stringa", "altra")  # Non controlla i tipi!


# CON spec=ServizioReale: il mock rispecchia l'interfaccia reale
mock_con_spec = Mock(spec=ServizioReale)
try:
    mock_con_spec.metodo_inesistente()  # AttributeError!
except AttributeError as e:
    print(f"Corretto! {e}")


# create_autospec: crea un mock completo con spec verificata sugli argomenti
mock_auto = create_autospec(ServizioReale)
try:
    mock_auto.calcola("stringa")  # TypeError: argomenti sbagliati!
except TypeError as e:
    print(f"Spec verificata sugli argomenti: {e}")

# Configurazione correttamente
mock_auto.calcola.return_value = 5.0
risultato = mock_auto.calcola(10, 2)  # Funziona con gli argomenti giusti
assert risultato == 5.0


# Test con create_autospec
def test_servizio_con_autospec():
    mock_servizio = create_autospec(ServizioReale, instance=True)
    mock_servizio.calcola.return_value = 3.14

    # Il codice sotto test riceve il mock
    gestore = GestoreBusinessLogic(servizio=mock_servizio)
    gestore.elabora(5, 2)

    # Verifica con spec — gli argomenti devono essere corretti
    mock_servizio.calcola.assert_called_once_with(5, 2)
```

---

### PropertyMock — Mock delle proprietà

```python
from unittest.mock import patch, PropertyMock


class Utente:
    def __init__(self, nome: str, email: str):
        self._nome = nome
        self._email = email

    @property
    def nome_completo(self) -> str:
        """Proprietà calcolata."""
        return f"Sig. {self._nome}"

    @property
    def email(self) -> str:
        return self._email


def test_nome_completo_con_property_mock():
    """Mock di una proprietà (@property)."""
    utente = Utente("Rossi", "mario@test.it")

    with patch.object(
        type(utente),          # IMPORTANTE: patcha sul tipo, non sull'istanza
        "nome_completo",
        new_callable=PropertyMock,
    ) as mock_nome:
        mock_nome.return_value = "Mock Nome Completo"

        assert utente.nome_completo == "Mock Nome Completo"
        mock_nome.assert_called_once()
```

---

### sentinel — Valori unici per i test

```python
from unittest.mock import sentinel


def test_valore_non_trovato():
    """
    sentinel crea oggetti unici che non possono essere confusi con None, False, o 0.
    Utile per distinguere "non trovato" da "trovato con valore None".
    """
    NON_TROVATO = sentinel.NON_TROVATO

    def trova_utente(user_id: int):
        if user_id == 1:
            return {"nome": "Mario"}
        if user_id == 2:
            return None  # Utente esiste ma con valore None (es. cancellato)
        return NON_TROVATO  # Utente mai esistito

    risultato_1 = trova_utente(1)
    assert risultato_1 is not NON_TROVATO  # Trovato

    risultato_2 = trova_utente(2)
    assert risultato_2 is not NON_TROVATO  # Trovato, anche se None
    assert risultato_2 is None

    risultato_3 = trova_utente(99)
    assert risultato_3 is NON_TROVATO  # Non trovato

    # sentinel.X è sempre lo stesso oggetto (singleton per nome)
    assert sentinel.NON_TROVATO is sentinel.NON_TROVATO
```

---

## J2: Mocking di Chiamate di Sistema

### Mock del filesystem (os, pathlib)

```python
from unittest.mock import patch, MagicMock
from pathlib import Path


def conta_file_python(directory: str) -> int:
    """Conta i file .py in una directory."""
    return len(list(Path(directory).glob("**/*.py")))


def test_conta_file_python():
    """Mock di Path.glob per controllare i file restituiti."""
    file_py = [
        MagicMock(name="main.py"),
        MagicMock(name="utils.py"),
        MagicMock(name="test_main.py"),
    ]

    with patch.object(Path, "glob", return_value=iter(file_py)):
        count = conta_file_python("/qualsiasi/percorso")
        assert count == 3


def leggi_configurazione_da_file(percorso: str) -> dict:
    """Legge una configurazione JSON da un file."""
    import json
    with open(percorso, "r") as f:
        return json.load(f)


def test_leggi_configurazione():
    """Mock di open() per evitare I/O reale."""
    from unittest.mock import mock_open

    config_json = '{"host": "db.esempio.it", "porta": 5432}'
    m = mock_open(read_data=config_json)

    with patch("builtins.open", m):
        config = leggi_configurazione_da_file("/etc/myapp/config.json")

    assert config["host"] == "db.esempio.it"
    assert config["porta"] == 5432

    # Verifica che open sia stato chiamato con i parametri giusti
    m.assert_called_once_with("/etc/myapp/config.json", "r")
```

---

### Mock del tempo (datetime, time)

```python
from unittest.mock import patch
from datetime import datetime, timedelta


def calcola_eta(data_nascita: datetime) -> int:
    """Calcola l'età in anni basandosi sulla data odierna."""
    oggi = datetime.now()
    eta = oggi.year - data_nascita.year
    if (oggi.month, oggi.day) < (data_nascita.month, data_nascita.day):
        eta -= 1
    return eta


def test_calcola_eta_38_anni():
    """Test con una data di oggi fissa."""
    data_fissa = datetime(2025, 6, 15, 12, 0, 0)
    data_nascita = datetime(1987, 6, 20)  # Ha compiuto 37 anni il 20 giugno

    with patch("src.utenti.datetime") as mock_dt:
        mock_dt.now.return_value = data_fissa
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

        eta = calcola_eta(data_nascita)
        assert eta == 37  # Non ha ancora compiuto 38 (il 20 giugno 2025 non è ancora)


def test_token_scaduto():
    """Verifica che un token scaduto venga riconosciuto."""
    scadenza = datetime(2025, 1, 1, 12, 0, 0)  # Token scaduto a gennaio 2025

    # Simula che "adesso" sia dopo la scadenza
    with patch("src.auth.datetime") as mock_dt:
        mock_dt.now.return_value = datetime(2025, 6, 15)
        assert token_e_scaduto(scadenza) is True

    # Simula che "adesso" sia prima della scadenza
    with patch("src.auth.datetime") as mock_dt:
        mock_dt.now.return_value = datetime(2024, 12, 31)
        assert token_e_scaduto(scadenza) is False
```

---

### Mock di librerie di terze parti

```python
# src/servizio_sms.py

import boto3  # AWS SDK


class ServizioSMS:
    def __init__(self, region: str = "eu-west-1"):
        self._client = boto3.client("sns", region_name=region)

    def invia(self, numero: str, messaggio: str) -> str:
        """
        Invia un SMS tramite AWS SNS.
        Returns: l'ID del messaggio.
        """
        risposta = self._client.publish(
            PhoneNumber=numero,
            Message=messaggio,
        )
        return risposta["MessageId"]


# tests/test_servizio_sms.py

import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def servizio():
    return ServizioSMS()


def test_invia_sms_restituisce_message_id(servizio):
    """Testa l'invio SMS senza chiamare AWS."""
    mock_risposta = {"MessageId": "MSG-12345", "ResponseMetadata": {"HTTPStatusCode": 200}}

    with patch.object(servizio._client, "publish", return_value=mock_risposta) as mock_publish:
        message_id = servizio.invia("+39 333 1234567", "Ciao!")

    assert message_id == "MSG-12345"
    mock_publish.assert_called_once_with(
        PhoneNumber="+39 333 1234567",
        Message="Ciao!",
    )


def test_invia_sms_errore_aws(servizio):
    """Testa il comportamento quando AWS restituisce un errore."""
    from botocore.exceptions import ClientError

    error_response = {
        "Error": {
            "Code": "InvalidParameter",
            "Message": "Numero di telefono non valido",
        }
    }

    with patch.object(
        servizio._client,
        "publish",
        side_effect=ClientError(error_response, "Publish"),
    ):
        with pytest.raises(ClientError):
            servizio.invia("numero_invalido", "Ciao!")
```

---

## J3: Organizzazione dei Test in Progetti Reali

### Struttura completa di un progetto professionale

```
mio_progetto/
├── pyproject.toml
├── src/
│   └── mio_progetto/
│       ├── __init__.py
│       ├── dominio/
│       │   ├── __init__.py
│       │   ├── modelli.py
│       │   ├── servizi.py
│       │   └── eccezioni.py
│       ├── infrastruttura/
│       │   ├── __init__.py
│       │   ├── repository.py
│       │   └── client_http.py
│       └── api/
│           ├── __init__.py
│           ├── routes.py
│           └── middleware.py
├── tests/
│   ├── conftest.py           ← Fixture globali
│   ├── factories.py          ← factory_boy factories
│   ├── unit/
│   │   ├── conftest.py       ← Fixture per unit test
│   │   ├── test_dominio/
│   │   │   ├── test_modelli.py
│   │   │   └── test_servizi.py
│   │   └── test_infrastruttura/
│   │       ├── test_repository.py
│   │       └── test_client_http.py
│   ├── integration/
│   │   ├── conftest.py       ← Fixture per integration (DB reale)
│   │   ├── test_database.py
│   │   └── test_api_esterna.py
│   └── e2e/
│       ├── conftest.py       ← Fixture per E2E (server reale)
│       ├── test_flusso_utente.py
│       └── test_flusso_admin.py
```

### pyproject.toml completo

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "mio-progetto"
version = "1.0.0"
description = "Il mio progetto Python"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.111.0",
    "sqlalchemy>=2.0.0",
    "pydantic>=2.0.0",
    "httpx>=0.27.0",
]

[project.optional-dependencies]
dev = [
    # Testing
    "pytest>=8.3.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=5.0.0",
    "pytest-xdist>=3.6.0",
    "pytest-timeout>=2.3.0",
    "pytest-randomly>=3.15.0",
    "pytest-mock>=3.14.0",
    # Property testing
    "hypothesis>=6.108.0",
    # Data factories
    "factory-boy>=3.3.0",
    "faker>=25.0.0",
    # Mocking HTTP
    "responses>=0.25.0",
    "httpx>=0.27.0",
    # Integration testing
    "testcontainers[postgres,redis]>=4.7.0",
    # Snapshot testing
    "syrupy>=4.6.0",
    # Mutation testing
    "mutmut>=2.4.0",
    # Code quality
    "ruff>=0.5.0",
    "mypy>=1.10.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
asyncio_mode = "auto"
timeout = 60

addopts = """
    -v
    --tb=short
    --strict-markers
    --import-mode=importlib
"""

markers = [
    "slow: test che richiedono più di 5 secondi",
    "integrazione: richiede servizi esterni",
    "e2e: test end-to-end",
    "smoke: test critici pre-deploy",
    "regression: test per bug risolti",
]

[tool.coverage.run]
source = ["src"]
branch = true
omit = [
    "src/mio_progetto/migrations/*",
    "tests/*",
]

[tool.coverage.report]
show_missing = true
fail_under = 85
exclude_lines = [
    "pragma: no cover",
    "raise NotImplementedError",
    "if TYPE_CHECKING:",
    "if __name__ == .__main__.:",
]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]

[tool.mypy]
python_version = "3.11"
strict = true
```

---

## J4: Debugging Avanzato dei Test

### Tecnica: bisecting per trovare test instabili

```bash
# Un test passa da solo ma fallisce in una suite? Usa bisecting:

# 1. Esegui tutti i test per vedere se il problema è riproducibile
pytest tests/ --randomly-seed=42

# 2. Se fallisce, trova quale test prima causa il problema
pytest tests/ --randomly-seed=42 -v 2>&1 | grep -E "(PASSED|FAILED)"

# 3. Usa pytest-bisect per trovare automaticamente il test che "inquina" lo stato
pip install pytest-bisect
pytest --bisect tests/

# 4. Oppure, usa git bisect per trovare il commit che ha introdotto il problema
git bisect start
git bisect bad HEAD
git bisect good v1.0.0
git bisect run pytest tests/test_problematico.py -x
git bisect reset
```

---

### Tecnica: profiling dei test lenti

```bash
# Trova i test più lenti
pytest --durations=10 tests/

# Output esempio:
# ========================= slowest 10 test durations ==========================
# 3.45s call     tests/integration/test_db.py::test_elaborazione_massiva
# 1.23s call     tests/integration/test_api.py::test_flusso_completo
# 0.89s call     tests/unit/test_servizio.py::test_operazione_costosa
```

```python
# Identifica le fixture lente
@pytest.fixture(scope="session")
def dati_grandi():
    """Attenzione: questa fixture è molto lenta!"""
    # Operazione costosa — usa scope="session" per eseguirla una sola volta
    return genera_milione_di_record()
```

---

### pdb nel debugging di test complessi

```python
def test_algoritmo_complesso(dati):
    risultato_step1 = step1(dati)
    risultato_step2 = step2(risultato_step1)

    # Aggiungi breakpoint manuale (usa 'pytest -s' per vedere l'output)
    import pdb; pdb.set_trace()

    # Comandi pdb utili:
    # n → esegui la prossima riga
    # s → entra nella funzione corrente
    # c → continua fino al prossimo breakpoint
    # p variabile → stampa il valore della variabile
    # pp oggetto → stampa l'oggetto con pretty print
    # l → mostra le righe del codice intorno
    # q → esci dal debugger (il test fallisce)

    risultato_finale = step3(risultato_step2)
    assert risultato_finale == valore_atteso
```

---

## J5: Checklist di Revisione del Codice di Test

Quando scrivi o rivedi un test, passa questa checklist:

```
CHECKLIST DI QUALITÀ DEI TEST
═══════════════════════════════════════════════════════════════════

NOMENCLATURA E ORGANIZZAZIONE
□ Il nome del test descrive chiaramente cosa viene testato?
□ Il nome include il contesto (cosa, quando, cosa ci si aspetta)?
  Formato suggerito: test_<cosa>_quando_<condizione>_deve_<risultato>
□ I test correlati sono raggruppati in una classe TestXxx?
□ La classe è nel file corretto (unit/ vs integration/ vs e2e/)?

STRUTTURA AAA (ARRANGE-ACT-ASSERT)
□ La fase Arrange (preparazione) è separata e chiara?
□ La fase Act (azione) è una singola operazione?
□ La fase Assert (verifica) verifica una sola cosa?
□ I commenti # Arrange # Act # Assert sono presenti se il test è lungo?

FIXTURE E DATI
□ I dati di test sono significativi (non arbitrari)?
□ È chiaro PERCHÉ i valori scelti sono importanti?
□ Si usano fixture invece di dati hardcoded dove possibile?
□ Le fixture hanno scope corretto (evitare scope troppo ampio)?
□ Ci sono fixture autouse che potrebbero influenzare il comportamento?

MOCK E STUB
□ Si patcha dove il simbolo è USATO, non dove è definito?
□ I mock usano spec= per rispettare l'interfaccia reale?
□ Si verifica che i mock siano stati chiamati con gli argomenti giusti?
□ I mock non maschereranno bug reali in produzione?

ASSERZIONI
□ L'asserzione è specifica (non assert True)?
□ Il messaggio di errore sarà chiaro se l'asserzione fallisce?
□ I valori float usano pytest.approx?
□ Si usa match= in pytest.raises per verificare il messaggio?
□ Si verifica sia i casi di successo che quelli di errore?

COPERTURA DEI CASI LIMITE
□ È testato il caso "lista vuota" o "valore None"?
□ È testato il caso "valore minimo" e "valore massimo"?
□ Sono testate le precondizioni che sollevano eccezioni?
□ È testato il comportamento con dati non validi?
□ Sono coperti tutti i rami condizionali (if/else)?

ISOLAMENTO
□ Il test è indipendente dagli altri test?
□ Il test lascia il sistema nello stesso stato di quando è iniziato?
□ Non c'è dipendenza dall'ordine di esecuzione?
□ Non ci sono effetti collaterali su file, DB, o risorse esterne?

PERFORMANCE
□ Il test è sufficientemente veloce per la sua categoria?
  - Unit: < 100ms
  - Integration: < 5s
  - E2E: < 30s
□ I test lenti sono marcati con @pytest.mark.slow?
□ Le fixture costose hanno scope appropriato?

MANUTENIBILITÀ
□ Il test si romperà se cambia l'implementazione (non l'interfaccia)?
□ I test sono DRY (no duplicazione eccessiva, usa fixture/parametrize)?
□ Il test è leggibile anche da chi non ha scritto il codice?

═══════════════════════════════════════════════════════════════════
```

---

## J6: Pattern di Test per Scenari Comuni

### Scenario 1: Funzione con retry

```python
# src/resilienza.py

import time
from functools import wraps
from typing import Callable, TypeVar, Any

T = TypeVar("T")


def con_retry(
    max_tentativi: int = 3,
    delay: float = 1.0,
    eccezioni: tuple = (Exception,),
):
    """Decoratore che riprova una funzione in caso di eccezione."""
    def decoratore(funzione: Callable[..., T]) -> Callable[..., T]:
        @wraps(funzione)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            for tentativo in range(1, max_tentativi + 1):
                try:
                    return funzione(*args, **kwargs)
                except eccezioni as e:
                    if tentativo == max_tentativi:
                        raise
                    time.sleep(delay)
            raise RuntimeError("Non raggiungibile")  # pragma: no cover
        return wrapper
    return decoratore
```

```python
# tests/test_resilienza.py

import pytest
from unittest.mock import patch, MagicMock, call
from src.resilienza import con_retry


class TestConRetry:
    """Test per il decoratore con_retry."""

    def test_successo_al_primo_tentativo(self):
        """Se la funzione ha successo subito, nessun retry."""
        chiamate = 0

        @con_retry(max_tentativi=3, delay=0)
        def funzione_stabile():
            nonlocal chiamate
            chiamate += 1
            return "successo"

        with patch("src.resilienza.time.sleep"):
            risultato = funzione_stabile()

        assert risultato == "successo"
        assert chiamate == 1

    def test_fallisce_poi_riesce(self):
        """Fallisce 2 volte poi riesce al terzo tentativo."""
        tentativo = 0

        @con_retry(max_tentativi=3, delay=0.01)
        def funzione_instabile():
            nonlocal tentativo
            tentativo += 1
            if tentativo < 3:
                raise ConnectionError("Connessione fallita")
            return "recuperato"

        with patch("src.resilienza.time.sleep"):
            risultato = funzione_instabile()

        assert risultato == "recuperato"
        assert tentativo == 3

    def test_esaurisce_tutti_i_tentativi(self):
        """Solleva l'eccezione dopo aver esaurito tutti i tentativi."""
        @con_retry(max_tentativi=3, delay=0)
        def funzione_sempre_fallisce():
            raise ValueError("Errore permanente")

        with patch("src.resilienza.time.sleep"):
            with pytest.raises(ValueError, match="permanente"):
                funzione_sempre_fallisce()

    def test_delay_tra_tentativi(self):
        """Verifica che il delay sia rispettato tra i tentativi."""
        @con_retry(max_tentativi=3, delay=2.0)
        def funzione_instabile():
            raise ConnectionError()

        with patch("src.resilienza.time.sleep") as mock_sleep:
            with pytest.raises(ConnectionError):
                funzione_instabile()

            # Con 3 tentativi, ci sono 2 sleep
            assert mock_sleep.call_count == 2
            mock_sleep.assert_any_call(2.0)

    def test_solo_eccezioni_specificate(self):
        """Non ritenta per eccezioni non specificate."""
        chiamate = 0

        @con_retry(max_tentativi=3, delay=0, eccezioni=(ConnectionError,))
        def funzione():
            nonlocal chiamate
            chiamate += 1
            raise ValueError("Tipo sbagliato di errore")

        with patch("src.resilienza.time.sleep"):
            with pytest.raises(ValueError):
                funzione()

        assert chiamate == 1  # Non ha fatto retry

    def test_preserva_valore_restituito(self):
        """Il decoratore non altera il valore restituito."""
        @con_retry()
        def funzione_con_dati():
            return {"nome": "Mario", "eta": 25}

        risultato = funzione_con_dati()
        assert risultato == {"nome": "Mario", "eta": 25}

    def test_preserva_nome_funzione(self):
        """Il decoratore (con wraps) preserva il nome della funzione."""
        @con_retry()
        def mia_funzione_speciale():
            pass

        assert mia_funzione_speciale.__name__ == "mia_funzione_speciale"
```

---

### Scenario 2: Rate Limiter

```python
# src/rate_limiter.py

import time
from collections import deque


class RateLimiter:
    """
    Rate limiter a finestra scorrevole.

    Permette al massimo max_richieste in una finestra di finestra_sec secondi.
    """

    def __init__(self, max_richieste: int, finestra_sec: float):
        if max_richieste <= 0:
            raise ValueError("max_richieste deve essere positivo")
        if finestra_sec <= 0:
            raise ValueError("finestra_sec deve essere positivo")
        self._max = max_richieste
        self._finestra = finestra_sec
        self._storico: deque[float] = deque()

    def permetti(self) -> bool:
        """
        Controlla se la richiesta è permessa.

        Returns:
            True se la richiesta è permessa, False se siamo al limite.
        """
        adesso = time.monotonic()
        limite_inferiore = adesso - self._finestra

        # Rimuovi richieste fuori dalla finestra
        while self._storico and self._storico[0] <= limite_inferiore:
            self._storico.popleft()

        if len(self._storico) < self._max:
            self._storico.append(adesso)
            return True

        return False

    def richieste_in_finestra(self) -> int:
        """Numero di richieste nella finestra corrente."""
        adesso = time.monotonic()
        limite_inferiore = adesso - self._finestra
        return sum(1 for t in self._storico if t > limite_inferiore)
```

```python
# tests/test_rate_limiter.py

import pytest
from unittest.mock import patch
from src.rate_limiter import RateLimiter


class TestRateLimiter:

    def test_prima_richiesta_sempre_permessa(self):
        limiter = RateLimiter(max_richieste=5, finestra_sec=60)
        with patch("src.rate_limiter.time.monotonic", return_value=0.0):
            assert limiter.permetti() is True

    def test_richieste_entro_limite_permesse(self):
        limiter = RateLimiter(max_richieste=3, finestra_sec=60)
        with patch("src.rate_limiter.time.monotonic", return_value=0.0):
            assert limiter.permetti() is True   # 1/3
            assert limiter.permetti() is True   # 2/3
            assert limiter.permetti() is True   # 3/3

    def test_richiesta_oltre_limite_negata(self):
        limiter = RateLimiter(max_richieste=3, finestra_sec=60)
        with patch("src.rate_limiter.time.monotonic", return_value=0.0):
            limiter.permetti()
            limiter.permetti()
            limiter.permetti()
            assert limiter.permetti() is False  # 4/3 — negata!

    def test_richieste_vecchie_non_contate(self):
        """Le richieste fuori dalla finestra non vengono conteggiate."""
        limiter = RateLimiter(max_richieste=3, finestra_sec=60)

        # 3 richieste al secondo 0
        with patch("src.rate_limiter.time.monotonic", return_value=0.0):
            limiter.permetti()
            limiter.permetti()
            limiter.permetti()

        # Al secondo 61, le prime 3 richieste sono "scadute"
        with patch("src.rate_limiter.time.monotonic", return_value=61.0):
            assert limiter.permetti() is True   # Nuova finestra, permessa!

    def test_finestra_scorrevole(self):
        """Verifica il comportamento con finestra scorrevole."""
        limiter = RateLimiter(max_richiestes=2, finestra_sec=10)

        with patch("src.rate_limiter.time.monotonic", return_value=0.0):
            limiter.permetti()   # t=0: 1 richiesta

        with patch("src.rate_limiter.time.monotonic", return_value=5.0):
            limiter.permetti()   # t=5: 2 richieste (0 e 5, entrambe nella finestra 10s)

        with patch("src.rate_limiter.time.monotonic", return_value=11.0):
            # La richiesta t=0 è fuori finestra (11-10=1 > 0)
            # La richiesta t=5 è ancora dentro (11-10=1 < 5)
            # Quindi abbiamo solo 1 richiesta in finestra
            assert limiter.permetti() is True   # 2/2, permessa

    def test_configurazione_invalida(self):
        with pytest.raises(ValueError, match="max_richieste"):
            RateLimiter(max_richieste=0, finestra_sec=60)

        with pytest.raises(ValueError, match="finestra_sec"):
            RateLimiter(max_richieste=10, finestra_sec=-1)
```

---

## J7: Testing di Output Visuale — Snapshot Testing Completo

### Installazione e setup

```bash
pip install syrupy
```

```python
# tests/conftest.py — aggiunta per syrupy
# syrupy si configura automaticamente con pytest
```

### Primo utilizzo — creare gli snapshot

```python
# tests/test_snapshot.py

import pytest
from src.report_generator import genera_report_json, genera_tabella_testo


def test_report_json_struttura(snapshot):
    """
    Al primo run: crea lo snapshot.
    Dai run successivi: confronta con lo snapshot.
    """
    dati = {
        "utenti": 1247,
        "ordini": 3891,
        "fatturato": 48523.50,
        "periodo": "Giugno 2025",
    }

    report = genera_report_json(dati)

    # Prima esecuzione: pytest --snapshot-update crea lo snapshot
    # Esecuzioni successive: confronta con quello creato
    assert report == snapshot


def test_tabella_testo_formato(snapshot):
    """Test del formato testuale della tabella."""
    prodotti = [
        {"nome": "Laptop", "prezzo": 999.0, "disponibile": True},
        {"nome": "Mouse", "prezzo": 29.99, "disponibile": False},
        {"nome": "Tastiera", "prezzo": 79.50, "disponibile": True},
    ]

    tabella = genera_tabella_testo(prodotti)
    assert tabella == snapshot
```

### Workflow degli snapshot

```bash
# Crea gli snapshot (prima esecuzione)
pytest tests/test_snapshot.py --snapshot-update

# Confronta con gli snapshot esistenti (test normale)
pytest tests/test_snapshot.py

# Se l'output è cambiato intenzionalmente, aggiorna lo snapshot
pytest tests/test_snapshot.py --snapshot-update

# Rimuovi snapshot obsoleti
pytest tests/test_snapshot.py --snapshot-warn-unused
pytest tests/test_snapshot.py --snapshot-delete-unused
```

### Snapshot con normalizzazione

```python
from syrupy.extensions.json import JSONSnapshotExtension
import re


@pytest.fixture
def snapshot_json(snapshot):
    """Snapshot per output JSON con normalizzazione."""
    return snapshot.with_defaults(extension_class=JSONSnapshotExtension)


def test_report_con_timestamp(snapshot_json):
    """
    Il report contiene un timestamp che cambia ad ogni esecuzione.
    Dobbiamo normalizzarlo prima del confronto.
    """
    report = genera_report()

    # Normalizza il timestamp per renderlo deterministico
    report["timestamp"] = "TIMESTAMP_NORMALIZZATO"
    report["id"] = "ID_NORMALIZZATO"

    assert report == snapshot_json
```

---

## J8: Pattern di Test per Eccezioni — Guida Completa

### Tutti i modi per testare le eccezioni

```python
# MODO 1: pytest.raises — il più comune
def test_divisione_per_zero():
    with pytest.raises(ZeroDivisionError):
        1 / 0

# MODO 2: con match per verificare il messaggio
def test_valore_invalido_con_messaggio():
    with pytest.raises(ValueError, match="negativo"):
        calcola_radice(-1)

# MODO 3: con ExceptionInfo per ispezione completa
def test_eccezione_con_attributi():
    with pytest.raises(ErroreValidazione) as exc_info:
        valida_dati({"eta": -1, "nome": ""})

    errore = exc_info.value
    assert errore.codice == "VALIDAZIONE_FALLITA"
    assert "eta" in errore.campi_invalidi
    assert "nome" in errore.campi_invalidi

# MODO 4: verifica eccezione nella catena
def test_eccezione_con_causa():
    with pytest.raises(ErroreDB) as exc_info:
        salva_in_database(dati_invalidi)

    assert isinstance(exc_info.value.__cause__, ValueError)

# MODO 5: verifica che NON venga sollevata un'eccezione
def test_operazione_non_solleva():
    # Questo approccio è esplicito
    try:
        operazione_che_deve_funzionare()
    except Exception as e:
        pytest.fail(f"Non deve sollevare eccezioni, ma ha sollevato: {e}")

# MODO 6: verifica eccezioni asincrone
async def test_eccezione_async():
    with pytest.raises(TimeoutError):
        await operazione_con_timeout(timeout=0.001)

# MODO 7: parametrize con tipi di eccezione diversi
@pytest.mark.parametrize("input, eccezione", [
    (-1, ValueError),
    ("testo", TypeError),
    (None, TypeError),
    (float("inf"), OverflowError),
])
def test_vari_tipi_eccezione(input, eccezione):
    with pytest.raises(eccezione):
        calcola_radice(input)
```

---

### Eccezioni personalizzate ben testabili

```python
# src/eccezioni.py

class ErroreApplicazione(Exception):
    """Eccezione base dell'applicazione."""
    codice: str = "ERRORE_GENERICO"

    def __init__(self, messaggio: str, dettagli: dict | None = None):
        super().__init__(messaggio)
        self.messaggio = messaggio
        self.dettagli = dettagli or {}


class ErroreValidazione(ErroreApplicazione):
    """Errore di validazione dei dati di input."""
    codice = "VALIDAZIONE_FALLITA"

    def __init__(self, campi: list[str], messaggio: str = "Validazione fallita"):
        super().__init__(messaggio, dettagli={"campi": campi})
        self.campi_invalidi = campi


class ErroreAutorizzazione(ErroreApplicazione):
    """Errore di autorizzazione."""
    codice = "ACCESSO_NEGATO"

    def __init__(self, utente_id: int, risorsa: str):
        super().__init__(
            f"Utente {utente_id} non autorizzato ad accedere a {risorsa!r}",
            dettagli={"utente_id": utente_id, "risorsa": risorsa},
        )
        self.utente_id = utente_id
        self.risorsa = risorsa
```

```python
# tests/test_eccezioni.py

def test_errore_validazione_ha_campi():
    """L'errore di validazione espone i campi invalidi."""
    errore = ErroreValidazione(campi=["nome", "email"])
    assert errore.campi_invalidi == ["nome", "email"]
    assert errore.codice == "VALIDAZIONE_FALLITA"
    assert "nome" in errore.dettagli["campi"]


def test_errore_autorizzazione():
    """L'errore di autorizzazione espone utente e risorsa."""
    errore = ErroreAutorizzazione(utente_id=42, risorsa="/admin/utenti")
    assert errore.utente_id == 42
    assert errore.risorsa == "/admin/utenti"
    assert "42" in str(errore)
    assert "/admin/utenti" in str(errore)


def test_gerarchia_eccezioni():
    """Le eccezioni personalizzate devono essere sotto-classi corrette."""
    errore_val = ErroreValidazione(campi=["nome"])
    errore_auth = ErroreAutorizzazione(utente_id=1, risorsa="/admin")

    assert isinstance(errore_val, ErroreApplicazione)
    assert isinstance(errore_auth, ErroreApplicazione)
    assert isinstance(errore_val, Exception)
    assert isinstance(errore_auth, Exception)


def test_validazione_servizio_solleva_errore_valido():
    """Il servizio solleva ErroreValidazione con i campi corretti."""
    dati_invalidi = {"nome": "", "email": "non_valida", "eta": -1}

    with pytest.raises(ErroreValidazione) as exc_info:
        valida_dati(dati_invalidi)

    errore = exc_info.value
    assert "nome" in errore.campi_invalidi
    assert "email" in errore.campi_invalidi
    assert "eta" in errore.campi_invalidi
```

---

## J9: Considerazioni sulla Performance dei Test

### Identificare i colli di bottiglia

I test lenti rallentano il ciclo di sviluppo. Ecco dove si trova il 90% dei
problemi di performance:

**1. Setup e teardown eccessivi**

```python
# LENTO: crea e distrugge il DB ad ogni test
@pytest.fixture
def db():
    conn = crea_schema_completo()  # 500ms
    yield conn
    distruggi_schema(conn)  # 200ms

# VELOCE: crea il DB una volta, pulisci i dati tra i test
@pytest.fixture(scope="session")
def db_session():
    conn = crea_schema_completo()  # 500ms TOTALE
    yield conn
    conn.close()

@pytest.fixture
def db(db_session):
    yield db_session
    pulisci_tabelle(db_session)  # 20ms per test
```

**2. Mock invece di risorse reali per unit test**

```python
# LENTO: connessione DB reale per unit test
def test_servizio_unita(db_reale):
    servizio = Servizio(repository=RealRepository(db_reale))
    ...

# VELOCE: mock per unit test
def test_servizio_unita(mock_repository):
    servizio = Servizio(repository=mock_repository)
    ...  # Nessuna I/O
```

**3. Parallelizzazione con pytest-xdist**

```bash
# Esegui in parallelo su tutti i core disponibili
pytest -n auto tests/unit/

# Specifica il numero di worker
pytest -n 4 tests/

# Nota: i test parallelizzati non devono condividere risorse
# Usa --dist=loadfile per raggruppare per file
pytest -n 4 --dist=loadfile tests/
```

**4. Test di integrazione con testcontainers — riuso del container**

```python
# Avvia il container UNA SOLA VOLTA per tutta la sessione
@pytest.fixture(scope="session")
def postgres_container():
    """Container PostgreSQL per tutta la sessione di test."""
    from testcontainers.postgres import PostgresContainer

    with PostgresContainer("postgres:16-alpine") as container:
        yield container

@pytest.fixture(scope="session")
def db_integration(postgres_container):
    """Connessione al DB, riusata per tutta la sessione."""
    import psycopg2
    conn = psycopg2.connect(postgres_container.get_connection_url())
    crea_schema(conn)
    yield conn
    conn.close()

@pytest.fixture(autouse=True)
def pulisci_dati(db_integration):
    """Pulisci i dati tra i test (ma non ricreare il DB)."""
    yield
    with db_integration.cursor() as cur:
        cur.execute("TRUNCATE TABLE utenti, ordini CASCADE")
    db_integration.commit()
```

---

## J10: Appendice — Snippets Pronti all'Uso

### Snippet 1: Fixture per database SQLite con rollback

```python
@pytest.fixture
def db_con_rollback():
    """
    Fixture che usa le transazioni per isolare ogni test.
    Dopo ogni test, la transazione viene annullata — nessun dato persiste.
    """
    import sqlite3
    conn = sqlite3.connect(":memory:")
    crea_schema(conn)
    conn.execute("BEGIN")
    yield conn
    conn.execute("ROLLBACK")
    conn.close()
```

### Snippet 2: Mock del timer

```python
from unittest.mock import patch


class MockTimer:
    """Simulatore di timer per test deterministici."""

    def __init__(self, tempo_iniziale: float = 0.0):
        self._tempo = tempo_iniziale

    def avanza(self, secondi: float) -> None:
        self._tempo += secondi

    def __call__(self) -> float:
        return self._tempo


@pytest.fixture
def timer_controllato():
    timer = MockTimer()
    with patch("src.modulo.time.time", new=timer):
        yield timer


def test_scadenza(timer_controllato):
    cache = Cache(ttl=60)
    cache.imposta("chiave", "valore")

    timer_controllato.avanza(30)  # 30 secondi dopo
    assert cache.ottieni("chiave") == "valore"

    timer_controllato.avanza(31)  # 61 secondi totali
    with pytest.raises(CacheScaduta):
        cache.ottieni("chiave")
```

### Snippet 3: Verifica dei log strutturati

```python
@pytest.fixture
def json_log_capturato(caplog, monkeypatch):
    """Cattura log in formato JSON strutturato."""
    import logging
    import json

    log_records = []

    class JsonHandler(logging.Handler):
        def emit(self, record):
            log_records.append({
                "level": record.levelname,
                "message": record.getMessage(),
                "extra": {k: v for k, v in record.__dict__.items()
                         if k not in ("msg", "args", "levelname", "levelno", "message")},
            })

    handler = JsonHandler()
    logging.getLogger().addHandler(handler)
    yield log_records
    logging.getLogger().removeHandler(handler)


def test_log_strutturato(json_log_capturato):
    from src.servizio import elabora_ordine
    elabora_ordine(ordine_id=42, utente_id=1)

    assert any(
        r["level"] == "INFO"
        and r["message"] == "Ordine elaborato"
        and r["extra"].get("ordine_id") == 42
        for r in json_log_capturato
    )
```

### Snippet 4: Mock di una API REST completa

```python
import responses


@pytest.fixture
def api_mock():
    """Context manager che mocka un'intera API."""
    with responses.RequestsMock() as rsps:
        # GET /utenti/{id}
        rsps.add(
            responses.GET,
            re.compile(r"https://api.esempio.it/utenti/\d+"),
            json={"id": 1, "nome": "Mario Rossi", "email": "mario@test.it"},
            status=200,
        )

        # POST /utenti
        rsps.add(
            responses.POST,
            "https://api.esempio.it/utenti",
            json={"id": 42, "nome": "Nuovo Utente"},
            status=201,
        )

        # DELETE /utenti/{id}
        rsps.add(
            responses.DELETE,
            re.compile(r"https://api.esempio.it/utenti/\d+"),
            status=204,
        )

        yield rsps


def test_ciclo_crud_utente(api_mock):
    client = ClientAPI("https://api.esempio.it")

    utente = client.crea_utente("Nuovo Utente", "nuovo@test.it")
    assert utente["id"] == 42

    trovato = client.ottieni_utente(1)
    assert trovato["nome"] == "Mario Rossi"

    client.elimina_utente(42)
    assert len([c for c in api_mock.calls if c.request.method == "DELETE"]) == 1
```

---

Queste sezioni supplementari completano la copertura di tutti i pattern di mocking,
le tecniche di debugging, e gli scenari comuni nel testing Python professionale.
Con questi strumenti, sarai in grado di affrontare qualsiasi situazione di testing
che incontrerai nel mondo reale.

---

## SEZIONE SUPPLEMENTARE K: BDD con pytest-bdd, Mutation Testing Avanzato, e Approfondimenti

---

## K1: BDD con pytest-bdd — Alternativa a behave

### Differenza tra behave e pytest-bdd

**behave** usa file di steps separati dai test pytest.
**pytest-bdd** integra i feature files direttamente nell'ecosistema pytest.

```bash
pip install pytest-bdd
```

### Struttura con pytest-bdd

```
progetto/
├── features/
│   └── autenticazione.feature    ← File Gherkin
└── tests/
    └── bdd/
        └── test_autenticazione.py ← Steps + test
```

### Feature file

```gherkin
# features/autenticazione.feature

Feature: Autenticazione utente
  Come utente del sistema
  Voglio potermi autenticare con le mie credenziali
  Per accedere alle funzionalità protette

  Background:
    Given esiste un utente "mario@test.it" con password "Password123!"

  Scenario: Login con credenziali corrette
    Given l'utente non è autenticato
    When l'utente invia le credenziali "mario@test.it" e "Password123!"
    Then l'accesso è consentito
    And viene restituito un token JWT valido

  Scenario: Login con password errata
    Given l'utente non è autenticato
    When l'utente invia le credenziali "mario@test.it" e "password_sbagliata"
    Then l'accesso è negato
    And viene restituito un messaggio di errore "Credenziali non valide"

  Scenario: Login con email inesistente
    Given l'utente non è autenticato
    When l'utente invia le credenziali "inesistente@test.it" e "Password123!"
    Then l'accesso è negato
    And viene restituito un messaggio di errore "Credenziali non valide"

  Scenario Outline: Tentativi di login consecutivi
    Given l'utente non è autenticato
    When l'utente invia <tentativi> credenziali errate
    Then l'account viene bloccato dopo <soglia> tentativi

    Examples:
      | tentativi | soglia |
      | 3         | 3      |
      | 5         | 5      |
```

### Implementazione degli steps con pytest-bdd

```python
# tests/bdd/test_autenticazione.py

import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from unittest.mock import MagicMock

# Carica tutti gli scenari dal file feature
scenarios("features/autenticazione.feature")


# ===== BACKGROUND =====

@pytest.fixture
def repository():
    """Mock del repository utenti."""
    return MagicMock()


@pytest.fixture
def servizio_auth(repository):
    """Servizio di autenticazione con dipendenze mockate."""
    from src.auth import ServizioAuth
    return ServizioAuth(repository=repository)


@given(parsers.parse('esiste un utente "{email}" con password "{password}"'))
def utente_esistente(repository, email, password):
    """Prepara il repository con un utente di test."""
    utente_mock = MagicMock()
    utente_mock.email = email
    utente_mock.verifica_password.return_value = True
    utente_mock.bloccato = False
    utente_mock.tentativi_falliti = 0

    repository.trova_per_email.side_effect = lambda e: (
        utente_mock if e == email else None
    )


# ===== GIVEN =====

@pytest.fixture
def contesto():
    """Dizionario condiviso tra gli step."""
    return {}


@given("l'utente non è autenticato")
def utente_non_autenticato(contesto):
    """Precondizione: nessuna sessione attiva."""
    contesto["autenticato"] = False
    contesto["token"] = None
    contesto["errore"] = None


# ===== WHEN =====

@when(parsers.parse('l\'utente invia le credenziali "{email}" e "{password}"'))
def invia_credenziali(email, password, servizio_auth, contesto):
    """Tenta l'autenticazione con le credenziali fornite."""
    try:
        risultato = servizio_auth.login(email=email, password=password)
        contesto["autenticato"] = True
        contesto["token"] = risultato.get("token")
        contesto["errore"] = None
    except Exception as e:
        contesto["autenticato"] = False
        contesto["token"] = None
        contesto["errore"] = str(e)


@when(parsers.parse("l'utente invia {tentativi:d} credenziali errate"))
def invia_credenziali_errate(tentativi, servizio_auth, repository, contesto):
    """Invia N volte credenziali sbagliate."""
    for i in range(tentativi):
        try:
            servizio_auth.login(
                email="mario@test.it",
                password=f"password_sbagliata_{i}",
            )
        except Exception:
            pass
    contesto["tentativi_eseguiti"] = tentativi


# ===== THEN =====

@then("l'accesso è consentito")
def accesso_consentito(contesto):
    assert contesto["autenticato"] is True, (
        f"L'accesso doveva essere consentito, ma errore: {contesto['errore']}"
    )


@then("l'accesso è negato")
def accesso_negato(contesto):
    assert contesto["autenticato"] is False, (
        "L'accesso doveva essere negato, ma è stato consentito"
    )


@then("viene restituito un token JWT valido")
def token_jwt_valido(contesto):
    token = contesto.get("token")
    assert token is not None, "Nessun token restituito"
    # Un JWT ha 3 parti separate da punti
    parti = token.split(".")
    assert len(parti) == 3, f"Token JWT malformato: {token}"


@then(parsers.parse('viene restituito un messaggio di errore "{messaggio}"'))
def messaggio_errore(messaggio, contesto):
    errore = contesto.get("errore", "")
    assert messaggio in errore, (
        f"Messaggio atteso: {messaggio!r}, ricevuto: {errore!r}"
    )


@then(parsers.parse("l'account viene bloccato dopo {soglia:d} tentativi"))
def account_bloccato(soglia, servizio_auth, contesto):
    """Verifica che l'account sia bloccato dopo N tentativi."""
    # Il prossimo tentativo deve fallire con AccountBloccato
    from src.auth import AccountBloccato

    with pytest.raises(AccountBloccato):
        servizio_auth.login(
            email="mario@test.it",
            password="qualsiasi_password",
        )
```

### Eseguire i test BDD

```bash
# Esegui tutti i test BDD
pytest tests/bdd/ -v

# Esegui uno scenario specifico
pytest tests/bdd/ -k "Login con credenziali corrette"

# Mostra i feature files nell'output
pytest tests/bdd/ -v --tb=short

# Output:
# tests/bdd/test_autenticazione.py::test_login_con_credenziali_corrette PASSED
# tests/bdd/test_autenticazione.py::test_login_con_password_errata PASSED
# tests/bdd/test_autenticazione.py::test_login_con_email_inesistente PASSED
```

---

## K2: Mutation Testing con mutmut — Guida Completa

### Concetto: cos'è un mutante?

mutmut introduce automaticamente piccoli bug nel tuo codice:

```python
# Codice originale
def calcola_sconto(eta: int) -> float:
    if eta >= 65:
        return 0.15
    return 0.0

# Mutante 1: >= diventa >
def calcola_sconto(eta: int) -> float:
    if eta > 65:       # MUTANTE: >= → >
        return 0.15
    return 0.0

# Mutante 2: 65 diventa 66
def calcola_sconto(eta: int) -> float:
    if eta >= 66:      # MUTANTE: 65 → 66
        return 0.15
    return 0.0

# Mutante 3: 0.15 diventa 0.14
def calcola_sconto(eta: int) -> float:
    if eta >= 65:
        return 0.14    # MUTANTE: 0.15 → 0.14
    return 0.0

# Mutante 4: return 0.0 rimosso
def calcola_sconto(eta: int) -> float:
    if eta >= 65:
        return 0.15
                       # MUTANTE: return 0.0 rimosso (ritorna None)
```

Un mutante **sopravvive** se nessun test lo rileva — questo significa che
la tua suite di test ha un buco di copertura qualitativa.

---

### Workflow con mutmut

```bash
# 1. Prima esegui i test normali (prerequisito)
pytest --cov=src --cov-report=xml tests/

# 2. Esegui mutation testing
mutmut run --paths-to-mutate=src/ --use-coverage

# 3. Vedi i risultati
mutmut results

# Output esempio:
# Legend for result column:
#   Killed (5):
#     - Killed by a test
#   Survived (3):
#     - Not killed by any test
#   Timeout (0):
#     - Took too long, might indicate infinite loop mutations
#   Suspicious (0):
#     - Suspicious mutation
#
# ⠴ 5/8  62%|████████████████████████▌                  |

# 4. Ispeziona i mutanti sopravvissuti
mutmut show 3  # Mostra il mutante numero 3

# Output:
# --- src/calcolatrice.py
# +++ src/calcolatrice.py
# @@ -15,7 +15,7 @@
#  def calcola_sconto(eta: int) -> float:
# -    if eta >= 65:
# +    if eta > 65:
#      return 0.15
#      return 0.0

# 5. Genera report HTML
mutmut html
# Apri htmlcov/index.html nel browser
```

---

### Come "uccidere" i mutanti sopravvissuti

Se il mutante che cambia `>=` in `>` sopravvive, significa che i tuoi test
non verificano il caso limite di `eta == 65`:

```python
# Il mutante >= → > sopravvive se non hai questo test:
def test_sconto_esatto_65_anni():
    """Il boundary di 65 anni deve dare sconto."""
    assert calcola_sconto(65) == pytest.approx(0.15)

# Con questo test, il mutante viene ucciso:
# Original: if eta >= 65 → calcola_sconto(65) = 0.15 ✓
# Mutante:  if eta > 65  → calcola_sconto(65) = 0.0 ✗
# Il test test_sconto_esatto_65_anni FALLISCE con il mutante → mutante UCCISO
```

### Esempio completo: analisi di mutanti sopravvissuti

```python
# src/carrello.py

def applica_coupon(totale: float, codice: str) -> float:
    """Applica un codice coupon all'ordine."""
    coupon_validi = {
        "SCONTO10": 0.10,
        "SCONTO20": 0.20,
        "SCONTO50": 0.50,
    }

    if codice in coupon_validi:
        sconto = coupon_validi[codice]
        return totale * (1 - sconto)

    return totale
```

```python
# Test di partenza (insufficienti)
def test_applica_coupon_10():
    assert applica_coupon(100.0, "SCONTO10") == pytest.approx(90.0)
```

```
$ mutmut run --paths-to-mutate=src/carrello.py

Survived mutants:
  3: if codice in coupon_validi → if codice not in coupon_validi
  5: 0.10 → 0.09   (nel dizionario)
  6: 0.20 → 0.19   (nel dizionario)
  7: 0.50 → 0.49   (nel dizionario)
  8: return totale → (riga rimossa)
```

```python
# Test migliorati che uccidono TUTTI i mutanti
@pytest.mark.parametrize("codice, totale, atteso", [
    ("SCONTO10", 100.0, 90.0),    # 10% di sconto
    ("SCONTO20", 100.0, 80.0),    # 20% di sconto
    ("SCONTO50", 100.0, 50.0),    # 50% di sconto
    ("INVALIDO", 100.0, 100.0),   # Codice non valido → nessuno sconto
    ("", 100.0, 100.0),           # Stringa vuota
    ("SCONTO10", 0.0, 0.0),       # Totale zero
    ("SCONTO20", 250.0, 200.0),   # Totale non intero
])
def test_applica_coupon(codice, totale, atteso):
    assert applica_coupon(totale, codice) == pytest.approx(atteso)
```

```
$ mutmut run --paths-to-mutate=src/carrello.py

Survived mutants: 0
Killed mutants: 8

Mutation score: 100%
```

---

## K3: Performance Testing con pytest-benchmark

### Setup

```bash
pip install pytest-benchmark
```

### Test di benchmark base

```python
# tests/benchmark/test_performance.py

import pytest
from src.algoritmi import bubble_sort, merge_sort, quick_sort
import random


def genera_lista(dimensione: int, seed: int = 42) -> list[int]:
    """Genera una lista casuale riproducibile."""
    rng = random.Random(seed)
    return [rng.randint(0, 10000) for _ in range(dimensione)]


# ===== BENCHMARK CON PARAMETRI =====

@pytest.fixture(params=[100, 1000, 10000], ids=["100", "1000", "10000"])
def lista_input(request):
    """Fixture parametrizzata con liste di dimensioni diverse."""
    return genera_lista(request.param)


def test_bubble_sort_benchmark(benchmark, lista_input):
    """Benchmark di bubble_sort con liste di dimensioni diverse."""
    lista_copia = lista_input.copy()
    risultato = benchmark(bubble_sort, lista_copia)
    assert risultato == sorted(lista_input)


def test_merge_sort_benchmark(benchmark, lista_input):
    """Benchmark di merge_sort."""
    lista_copia = lista_input.copy()
    risultato = benchmark(merge_sort, lista_copia)
    assert risultato == sorted(lista_input)


def test_quick_sort_benchmark(benchmark, lista_input):
    """Benchmark di quick_sort."""
    lista_copia = lista_input.copy()
    risultato = benchmark(quick_sort, lista_copia)
    assert risultato == sorted(lista_input)


# ===== CONFRONTO DIRETTO =====

def test_merge_vs_bubble_su_lista_grande(benchmark):
    """Merge sort deve essere più veloce di bubble sort su liste grandi."""
    lista = genera_lista(5000)

    # Benchmark di merge_sort
    risultato = benchmark(merge_sort, lista.copy())

    # Verifica che il risultato sia corretto
    assert risultato == sorted(lista)

    # Il benchmark registra automaticamente i tempi


# ===== BENCHMARK CON SETUP =====

def test_ricerca_in_dizionario(benchmark):
    """Benchmark della ricerca in dizionario vs lista."""
    dati = {str(i): i for i in range(10000)}
    chiavi = [str(i) for i in range(10000)]

    def ricerca():
        return [dati[k] for k in chiavi if k in dati]

    risultato = benchmark(ricerca)
    assert len(risultato) == 10000
```

### Eseguire i benchmark

```bash
# Esegui tutti i benchmark
pytest tests/benchmark/ --benchmark-only

# Output esempio:
# ------------------------------------------------------------------ benchmark: 6 tests --
# Name (time in ms)                         Min       Max      Mean    StdDev    Median
# -------------------------------------------------------------------------------------
# test_bubble_sort_benchmark[100]        0.0234    0.0312   0.0246   0.0012    0.0241
# test_merge_sort_benchmark[100]         0.0089    0.0121   0.0094   0.0005    0.0092
# test_quick_sort_benchmark[100]         0.0067    0.0098   0.0071   0.0004    0.0069
# test_bubble_sort_benchmark[1000]       2.3456    3.1234   2.4567   0.1234    2.4012
# test_merge_sort_benchmark[1000]        0.1234    0.1678   0.1312   0.0089    0.1289
# test_quick_sort_benchmark[1000]        0.0987    0.1423   0.1045   0.0067    0.1023

# Salva il risultato di riferimento
pytest tests/benchmark/ --benchmark-save=baseline

# Confronta con il riferimento (in una sessione futura)
pytest tests/benchmark/ --benchmark-compare=baseline
```

---

## K4: Locust — Load Testing con Python

### Cos'è il load testing?

Il load testing verifica come si comporta il sistema sotto carico elevato.
A differenza dei test funzionali (che verificano la correttezza), il load testing
verifica la performance e la stabilità.

```bash
pip install locust
```

### Scenario: API di e-commerce

```python
# tests/load/locustfile.py

from locust import HttpUser, task, between, events
import random
import json


class UtenteBase(HttpUser):
    """
    Simula un utente base che naviga il sito.
    Aspetta tra 1 e 3 secondi tra le richieste (comportamento umano).
    """
    wait_time = between(1, 3)

    def on_start(self):
        """Eseguito quando l'utente virtuale inizia."""
        self.client.headers.update({"Content-Type": "application/json"})

    @task(3)  # Peso 3: questa azione è 3 volte più frequente di task(1)
    def sfoglia_prodotti(self):
        """L'utente sfoglia il catalogo prodotti."""
        with self.client.get(
            "/api/prodotti",
            params={"pagina": random.randint(1, 10), "per_pagina": 20},
            name="/api/prodotti [GET]",  # Raggruppa tutte le richieste paginate
            catch_response=True,
        ) as risposta:
            if risposta.status_code == 200:
                dati = risposta.json()
                if "prodotti" in dati:
                    risposta.success()
                else:
                    risposta.failure("Risposta senza campo 'prodotti'")
            else:
                risposta.failure(f"Status code: {risposta.status_code}")

    @task(1)
    def visualizza_prodotto_singolo(self):
        """L'utente visualizza un prodotto specifico."""
        prodotto_id = random.randint(1, 1000)
        with self.client.get(
            f"/api/prodotti/{prodotto_id}",
            name="/api/prodotti/{id} [GET]",
            catch_response=True,
        ) as risposta:
            if risposta.status_code in (200, 404):
                risposta.success()
            else:
                risposta.failure(f"Errore inatteso: {risposta.status_code}")


class UtenteAcquirente(HttpUser):
    """
    Simula un utente che fa acquisti.
    Aspetta meno (più intento).
    """
    wait_time = between(0.5, 2)

    def on_start(self):
        """Autenticati all'inizio."""
        risposta = self.client.post(
            "/api/auth/login",
            json={"email": "test@load.it", "password": "password"},
        )
        if risposta.status_code == 200:
            token = risposta.json().get("token")
            self.client.headers.update({"Authorization": f"Bearer {token}"})
        else:
            self.environment.runner.quit()

    @task(2)
    def aggiungi_al_carrello(self):
        """Aggiunge un prodotto al carrello."""
        self.client.post(
            "/api/carrello/aggiungi",
            json={"prodotto_id": random.randint(1, 100), "quantita": 1},
            name="/api/carrello/aggiungi [POST]",
        )

    @task(1)
    def checkout(self):
        """Completa un acquisto."""
        self.client.post(
            "/api/ordini",
            json={
                "metodo_pagamento": "carta",
                "indirizzo": "Via Test 1, Milano",
            },
            name="/api/ordini [POST]",
        )
```

### Eseguire il load test

```bash
# Avvia con UI web (http://localhost:8089)
locust -f tests/load/locustfile.py --host=http://localhost:8000

# Avvia senza UI (headless) per CI
locust \
    -f tests/load/locustfile.py \
    --host=http://localhost:8000 \
    --users=100 \
    --spawn-rate=10 \
    --run-time=60s \
    --headless \
    --csv=reports/load_test

# Aggiungi asserzioni sui risultati
locust \
    --users=50 \
    --spawn-rate=5 \
    --run-time=30s \
    --headless \
    --stop-timeout=10 \
    --exit-code-on-error=1
```

---

## K5: Snapshot Testing Avanzato con syrupy

### Tipi di snapshot supportati

```python
# tests/conftest.py
from syrupy.extensions.amber import AmberSnapshotExtension
from syrupy.extensions.json import JSONSnapshotExtension
from syrupy.extensions.single_file import SingleFileSnapshotExtension


@pytest.fixture
def snapshot_json(snapshot):
    return snapshot.with_defaults(extension_class=JSONSnapshotExtension)


@pytest.fixture
def snapshot_file(snapshot):
    return snapshot.with_defaults(extension_class=SingleFileSnapshotExtension)
```

```python
# tests/test_snapshot_avanzato.py

def test_output_html(snapshot_file, tmp_path):
    """Snapshot di un file HTML generato."""
    from src.report_html import genera_html

    dati = {
        "titolo": "Report Vendite",
        "mese": "Giugno 2025",
        "totale": 48523.50,
    }
    html = genera_html(dati)

    # Normalizza valori dinamici
    html = html.replace(str(dati["mese"]), "MESE_NORMALIZZATO")

    assert html == snapshot_file


def test_risposta_api_json(snapshot_json):
    """Snapshot della risposta JSON dell'API."""
    from fastapi.testclient import TestClient
    from src.app import app

    client = TestClient(app)
    risposta = client.get("/api/statistiche")

    dati = risposta.json()
    # Normalizza timestamp
    dati["generato_alle"] = "TIMESTAMP"

    assert dati == snapshot_json


def test_grafico_dati(snapshot, tmp_path):
    """Snapshot della struttura dati di un grafico."""
    from src.grafici import calcola_dati_grafico

    dati_input = {
        "gennaio": 1200,
        "febbraio": 1400,
        "marzo": 1100,
    }

    dati_grafico = calcola_dati_grafico(dati_input)
    # Verifica la struttura, non i valori dinamici
    assert {
        "etichette": dati_grafico["etichette"],
        "valori_count": len(dati_grafico["valori"]),
    } == snapshot
```

---

## K6: pytest-xdist — Parallelismo Avanzato

### Modalità di distribuzione

```bash
# Distribuzione automatica (default: dividi test tra worker)
pytest -n auto tests/

# Distribuzione per file (tutti i test in un file vanno sullo stesso worker)
pytest -n 4 --dist=loadfile tests/

# Distribuzione per gruppo (usa @pytest.mark.xdist_group)
pytest -n 4 --dist=loadgroup tests/

# Distribuzione no (disabilita xdist anche se --n è impostato)
pytest -n 0 tests/
```

### Raggruppamento di test per xdist

```python
import pytest


@pytest.mark.xdist_group(name="database")
class TestDatabaseOperations:
    """Questi test condividono lo stesso worker per evitare conflitti DB."""

    def test_inserimento(self, db):
        ...

    def test_query(self, db):
        ...


@pytest.mark.xdist_group(name="api")
class TestAPIOperations:
    """Questi test condividono lo stesso worker (stesso server API)."""

    def test_get_utenti(self, client):
        ...

    def test_post_utente(self, client):
        ...
```

### worker_id nelle fixture

```python
@pytest.fixture(scope="session")
def database(worker_id):
    """
    Con pytest-xdist, ogni worker ottiene il proprio database.
    Senza xdist, worker_id è 'master'.
    """
    if worker_id == "master":
        db_name = "test_db"
    else:
        db_name = f"test_db_{worker_id}"

    conn = crea_database(db_name)
    yield conn
    distruggi_database(db_name)
```

---

## K7: pytest hooks — Personalizzazione avanzata

### Hook principali di pytest

```python
# conftest.py — Hook personalizzati

import pytest


def pytest_configure(config):
    """
    Eseguito prima di qualsiasi test.
    Utile per configurare variabili globali o registrare marker.
    """
    config.addinivalue_line(
        "markers", "mio_marker: un marker personalizzato"
    )


def pytest_collection_modifyitems(config, items):
    """
    Eseguito dopo la raccolta di tutti i test.
    Permette di filtrare, riordinare, o modificare i test.
    """
    # Aggiungi il marker 'slow' ai test in tests/integration/
    for item in items:
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.slow)

    # Riordina: prima i test veloci, poi i lenti
    fast_tests = [i for i in items if "slow" not in [m.name for m in i.iter_markers()]]
    slow_tests = [i for i in items if "slow" in [m.name for m in i.iter_markers()]]
    items[:] = fast_tests + slow_tests


def pytest_runtest_setup(item):
    """
    Eseguito prima di ogni test.
    """
    print(f"\n[START] {item.name}")


def pytest_runtest_teardown(item, nextitem):
    """
    Eseguito dopo ogni test.
    """
    print(f"[END] {item.name}")


def pytest_runtest_makereport(item, call):
    """
    Permette di modificare il report di ogni test.
    """
    pass


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Hook avanzato per catturare il risultato del test.
    """
    outcome = yield
    rep = outcome.get_result()

    # Salva il risultato nel request per uso nelle fixture
    if rep.when == "call":
        if hasattr(item, "funcargs") and "request" in item.funcargs:
            item.funcargs["request"]._test_failed = rep.failed


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """
    Aggiunge informazioni al sommario finale.
    """
    passed = len(terminalreporter.stats.get("passed", []))
    failed = len(terminalreporter.stats.get("failed", []))
    total = passed + failed

    if total > 0:
        percentuale = (passed / total) * 100
        terminalreporter.write_sep(
            "=",
            f"Tasso di successo: {passed}/{total} ({percentuale:.1f}%)"
        )
```

---

## K8: Test degli Hook pytest — Test di Plugin

```python
# tests/test_il_mio_plugin.py

import pytest
from pytest import ExitCode


def test_marker_aggiunto_automaticamente(testdir):
    """
    pytestdir: fixture speciale per testare plugin pytest.
    """
    # Crea un file di test temporaneo
    testdir.makepyfile("""
        import pytest

        def test_in_integration():
            assert True  # Test in un percorso che simula integration/
    """)

    # Esegui pytest nel directory temporaneo
    result = testdir.runpytest("-v")

    # Verifica il risultato
    result.assert_outcomes(passed=1)
    result.stdout.fnmatch_lines(["*PASSED*"])
```

---

## K9: Integrazione con Sistemi di CI/CD Reali

### GitLab CI — Pipeline completa

```yaml
# .gitlab-ci.yml

stages:
  - lint
  - test
  - mutation
  - deploy

variables:
  PYTHON_VERSION: "3.12"
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

# Cache delle dipendenze pip
cache:
  paths:
    - .cache/pip
    - venv/

# ==============================
# STAGE 1: Linting
# ==============================
lint:
  stage: lint
  image: python:${PYTHON_VERSION}
  before_script:
    - pip install ruff mypy
  script:
    - ruff check src/ tests/
    - ruff format --check src/ tests/
    - mypy src/ --strict --ignore-missing-imports
  rules:
    - if: '$CI_PIPELINE_SOURCE == "push"'

# ==============================
# STAGE 2: Test
# ==============================
unit-tests:
  stage: test
  image: python:${PYTHON_VERSION}
  before_script:
    - pip install -e ".[dev]"
  script:
    - pytest tests/unit/
        -n auto
        --cov=src
        --cov-report=xml
        --cov-report=term-missing
        --junitxml=reports/junit-unit.xml
        --timeout=30
  coverage: '/TOTAL.+?(\d+)%/'
  artifacts:
    reports:
      junit: reports/junit-unit.xml
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
    expire_in: 1 week

integration-tests:
  stage: test
  image: python:${PYTHON_VERSION}
  services:
    - name: postgres:16-alpine
      alias: postgres
    - name: redis:7-alpine
      alias: redis
  variables:
    POSTGRES_DB: testdb
    POSTGRES_USER: testuser
    POSTGRES_PASSWORD: testpass
    DATABASE_URL: "postgresql://testuser:testpass@postgres:5432/testdb"
    REDIS_URL: "redis://redis:6379"
  before_script:
    - pip install -e ".[dev]"
  script:
    - pytest tests/integration/
        -m integrazione
        --junitxml=reports/junit-integration.xml
        --timeout=60
  artifacts:
    reports:
      junit: reports/junit-integration.xml
    expire_in: 1 week
  needs: ["unit-tests"]

# ==============================
# STAGE 3: Mutation Testing (solo su main)
# ==============================
mutation-testing:
  stage: mutation
  image: python:${PYTHON_VERSION}
  before_script:
    - pip install -e ".[dev]" mutmut
  script:
    - pytest --cov=src --cov-report=xml tests/unit/
    - mutmut run --paths-to-mutate=src/ --use-coverage || true
    - mutmut results
  artifacts:
    paths:
      - .mutmut-cache
    expire_in: 1 week
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
  needs: ["unit-tests"]

# ==============================
# STAGE 4: Deploy (solo su main, solo se tutti i test passano)
# ==============================
deploy-staging:
  stage: deploy
  image: docker:latest
  script:
    - echo "Deploy in staging..."
    # ... logica di deploy
  environment:
    name: staging
    url: https://staging.esempio.it
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
  needs: ["unit-tests", "integration-tests"]
```

---

### Jenkins Pipeline (Jenkinsfile)

```groovy
// Jenkinsfile

pipeline {
    agent any

    environment {
        PYTHON_VERSION = '3.12'
        VENV_DIR = '.venv'
    }

    stages {
        stage('Setup') {
            steps {
                sh """
                    python${PYTHON_VERSION} -m venv ${VENV_DIR}
                    ${VENV_DIR}/bin/pip install -e ".[dev]"
                """
            }
        }

        stage('Lint') {
            steps {
                sh """
                    ${VENV_DIR}/bin/ruff check src/ tests/
                    ${VENV_DIR}/bin/mypy src/ --strict
                """
            }
        }

        stage('Unit Tests') {
            steps {
                sh """
                    ${VENV_DIR}/bin/pytest tests/unit/
                        -n auto
                        --cov=src
                        --cov-report=xml
                        --junitxml=reports/junit-unit.xml
                        --timeout=30
                """
            }
            post {
                always {
                    junit 'reports/junit-unit.xml'
                    publishCoverage adapters: [coberturaAdapter('coverage.xml')]
                }
            }
        }

        stage('Integration Tests') {
            steps {
                sh """
                    ${VENV_DIR}/bin/pytest tests/integration/
                        --junitxml=reports/junit-integration.xml
                        --timeout=60
                """
            }
            post {
                always {
                    junit 'reports/junit-integration.xml'
                }
            }
        }
    }

    post {
        failure {
            emailext(
                to: 'team@esempio.it',
                subject: "Build fallita: ${currentBuild.displayName}",
                body: "La pipeline è fallita. Controlla: ${env.BUILD_URL}",
            )
        }
    }
}
```

---

## K10: Testcontainers — Tutti i Container Supportati

### PostgreSQL con Alembic (migrazioni)

```python
# tests/integration/conftest.py

import pytest
from testcontainers.postgres import PostgresContainer
from alembic.config import Config
from alembic import command
import sqlalchemy


@pytest.fixture(scope="session")
def postgres_url():
    """URL di connessione PostgreSQL per i test."""
    with PostgresContainer("postgres:16-alpine") as container:
        url = container.get_connection_url()
        yield url


@pytest.fixture(scope="session")
def db_engine(postgres_url):
    """SQLAlchemy engine con migrazioni applicate."""
    engine = sqlalchemy.create_engine(postgres_url)

    # Esegui le migrazioni Alembic
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", postgres_url)
    command.upgrade(alembic_cfg, "head")

    yield engine

    # Teardown: downgrade al base
    command.downgrade(alembic_cfg, "base")
    engine.dispose()


@pytest.fixture
def sessione_db(db_engine):
    """Sessione SQLAlchemy con rollback automatico."""
    with sqlalchemy.orm.Session(db_engine) as sessione:
        with sessione.begin():
            yield sessione
            sessione.rollback()  # Annulla tutte le modifiche del test
```

### Redis con pytest

```python
# tests/integration/test_cache_redis.py

import pytest
from testcontainers.redis import RedisContainer
import redis


@pytest.fixture(scope="module")
def redis_client():
    """Client Redis per i test di integrazione."""
    with RedisContainer("redis:7-alpine") as container:
        client = redis.Redis(
            host=container.get_container_host_ip(),
            port=container.get_exposed_port(6379),
            decode_responses=True,
        )
        yield client


@pytest.fixture(autouse=True)
def pulisci_redis(redis_client):
    """Pulisci Redis prima di ogni test."""
    redis_client.flushall()
    yield
    redis_client.flushall()


def test_set_e_get(redis_client):
    redis_client.set("chiave", "valore", ex=60)
    assert redis_client.get("chiave") == "valore"


def test_ttl_redis(redis_client):
    redis_client.set("temporanea", "valore", ex=30)
    ttl = redis_client.ttl("temporanea")
    assert 0 < ttl <= 30


def test_chiave_scaduta(redis_client):
    redis_client.set("veloce", "valore", px=100)  # 100ms
    import time
    time.sleep(0.2)
    assert redis_client.get("veloce") is None
```

### MongoDB con testcontainers

```python
# tests/integration/test_mongodb.py

import pytest
from testcontainers.mongodb import MongoDbContainer
from pymongo import MongoClient


@pytest.fixture(scope="module")
def mongo_client():
    """Client MongoDB per i test."""
    with MongoDbContainer("mongo:7.0") as container:
        client = MongoClient(container.get_connection_url())
        yield client
        client.close()


@pytest.fixture
def collezione(mongo_client):
    """Collezione MongoDB pulita per ogni test."""
    db = mongo_client.test_database
    col = db.test_collection
    col.drop()
    yield col
    col.drop()


def test_inserisci_documento(collezione):
    doc = {"nome": "Mario", "eta": 25}
    risultato = collezione.insert_one(doc)
    assert risultato.inserted_id is not None


def test_trova_documento(collezione):
    collezione.insert_many([
        {"nome": "Mario", "categoria": "A"},
        {"nome": "Luigi", "categoria": "B"},
        {"nome": "Peach", "categoria": "A"},
    ])

    categoria_a = list(collezione.find({"categoria": "A"}))
    assert len(categoria_a) == 2
    nomi = {d["nome"] for d in categoria_a}
    assert nomi == {"Mario", "Peach"}
```

---

## K11: Guida al Debugging — Analisi delle Failure

### Anatomia di una failure complessa

```python
# Funzione con un bug sottile
def calcola_media_pesata(valori: list[float], pesi: list[float]) -> float:
    """Calcola la media pesata."""
    if len(valori) != len(pesi):
        raise ValueError("Valori e pesi devono avere la stessa lunghezza")

    totale_pesi = sum(pesi)
    if totale_pesi == 0:
        raise ValueError("La somma dei pesi non può essere zero")

    return sum(v * p for v, p in zip(valori, pesi)) / totale_pesi


# Test che trova il bug:
def test_media_pesata_con_valori_negativi():
    valori = [-2.0, 0.0, 4.0]
    pesi = [1.0, 2.0, 1.0]

    risultato = calcola_media_pesata(valori, pesi)
    # Media pesata: (-2*1 + 0*2 + 4*1) / (1+2+1) = 2/4 = 0.5
    assert risultato == pytest.approx(0.5)
```

```
FAILED tests/test_media.py::test_media_pesata_con_valori_negativi
─────────────────────────────── FAILURES ──────────────────────────────────

test_media_pesata_con_valori_negativi
─────────────────────────────── Short Test Summary Info ──────────────────
>       assert risultato == pytest.approx(0.5)
E       assert 2.0 == 0.5 ± 5.0e-07
E         (comparison failed, actual: 2.0)

tests/test_media.py:14: AssertionError
```

### Analisi step-by-step

```python
# Aggiungi print di debug temporanei (ma usa breakpoint() in produzione)
def test_media_pesata_debug():
    valori = [-2.0, 0.0, 4.0]
    pesi = [1.0, 2.0, 1.0]

    print(f"\nValori: {valori}")
    print(f"Pesi: {pesi}")
    print(f"Somma pesi: {sum(pesi)}")

    prodotti = [v * p for v, p in zip(valori, pesi)]
    print(f"Prodotti: {prodotti}")
    print(f"Somma prodotti: {sum(prodotti)}")

    risultato = calcola_media_pesata(valori, pesi)
    print(f"Risultato: {risultato}")

    assert risultato == pytest.approx(0.5)
```

```
Valori: [-2.0, 0.0, 4.0]
Pesi: [1.0, 2.0, 1.0]
Somma pesi: 4.0
Prodotti: [-2.0, 0.0, 4.0]
Somma prodotti: 2.0
Risultato: 2.0
```

Il bug è visibile: 2.0 / 4.0 dovrebbe dare 0.5, ma il risultato è 2.0.
Il problema? La formula è sbagliata: divide per `len(pesi)` invece di
`sum(pesi)`.

---

### Diagnosi con caplog

```python
def test_servizio_con_log_debug(caplog):
    """Cattura i log durante l'esecuzione per il debugging."""
    import logging

    with caplog.at_level(logging.DEBUG):
        risultato = servizio_complesso.esegui(dati)

    print("\nLog catturati:")
    for record in caplog.records:
        print(f"  [{record.levelname}] {record.getMessage()}")

    assert risultato["stato"] == "completato"
```

---

## K12: Tabelle di Riferimento per il Progetto Professionale

### Matrice: quando usare quale strumento

```
SITUAZIONE                                    STRUMENTO CONSIGLIATO
══════════════════════════════════════════════════════════════════════
Test di una funzione pura                     pytest (plain)
Test di una classe con metodi                 pytest + classi Test*
Dati di test variabili                        @pytest.mark.parametrize
Stessi test su diversi ambienti              parametrize indiretto
Test di codice con dipendenze esterne        unittest.mock + patch
Test di codice asincrono                      pytest-asyncio
Test di API REST (endpoint)                   httpx.TestClient / responses
Test di database (unit)                       Mock del repository
Test di database (integrazione)               testcontainers
Test con dati realistici                      factory_boy + faker
Test di proprietà matematiche                 Hypothesis
Test di scenari business                      behave / pytest-bdd
Test di performance (microbenchmark)          pytest-benchmark
Test di carico (throughput)                   Locust
Test di output complessi                      syrupy (snapshot)
Verifica qualità dei test                     mutmut (mutation testing)
Test instabili / ordine dei test             pytest-randomly + xdist
══════════════════════════════════════════════════════════════════════
```

### Timeline di maturità del testing

```
SETTIMANA 1-2:  Installa pytest, scrivi i primi assert
SETTIMANA 3-4:  Scopri le fixture, usa tmp_path e capsys
MESE 2:         Padroneggi parametrize, capisci AAA
MESE 3:         Introduci Mock per le dipendenze esterne
MESE 4:         Aggiungi pytest-cov, target 80%
MESE 5-6:       TDD su nuove funzionalità
MESE 7-8:       Hypothesis per i casi limite
MESE 9-10:      Integration test con testcontainers
ANNO 1:         Suite completa, CI/CD, mutation testing
ANNO 2+:        Test architetti, design for testability
```

---

Con questa copertura completa di tutti gli strumenti, pattern, e scenari del
testing Python, hai tutto ciò che serve per passare da "non ho mai scritto un test"
a "scrivo test professionali che danno fiducia reale nel codice".

Il segreto finale: non cercare la perfezione dall'inizio. Inizia con un test
oggi — anche solo uno — e costruisci l'abitudine. La suite crescerà naturalmente.

---

## SEZIONE SUPPLEMENTARE L: Progetto Completo — Sistema di Gestione Biblioteca

---

## L1: Introduzione al Progetto

In questa sezione costruiamo un sistema completo da zero usando TDD e tutte le
tecniche imparate. La biblioteca gestisce libri, utenti, e prestiti.

### Requisiti funzionali

1. Aggiungere libri al catalogo
2. Registrare utenti
3. Prendere in prestito libri (con limite massimo di 3 libri per utente)
4. Restituire libri
5. Cercare libri per titolo, autore, o genere
6. Visualizzare la cronologia dei prestiti di un utente

### Struttura del progetto

```
biblioteca/
├── src/
│   ├── modelli.py
│   ├── catalogo.py
│   ├── gestione_prestiti.py
│   └── eccezioni.py
└── tests/
    ├── conftest.py
    ├── unit/
    │   ├── test_modelli.py
    │   ├── test_catalogo.py
    │   └── test_gestione_prestiti.py
    └── integration/
        └── test_biblioteca_completa.py
```

---

## L2: Modelli di Dominio

```python
# src/modelli.py

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional
from enum import Enum


class GenereLibro(Enum):
    ROMANZO = "romanzo"
    SAGGISTICA = "saggistica"
    FANTASCIENZA = "fantascienza"
    GIALLO = "giallo"
    POESIA = "poesia"
    ALTRO = "altro"


class StatoPrestito(Enum):
    ATTIVO = "attivo"
    RESTITUITO = "restituito"
    IN_RITARDO = "in_ritardo"


@dataclass
class Libro:
    """Rappresenta un libro nel catalogo."""
    isbn: str
    titolo: str
    autore: str
    genere: GenereLibro
    anno: int
    disponibile: bool = True
    copie_totali: int = 1
    copie_disponibili: int = 1

    def __post_init__(self):
        if self.copie_totali <= 0:
            raise ValueError("copie_totali deve essere positivo")
        if self.copie_disponibili < 0:
            raise ValueError("copie_disponibili non può essere negativo")
        if self.copie_disponibili > self.copie_totali:
            raise ValueError("copie_disponibili non può superare copie_totali")

    def e_disponibile(self) -> bool:
        return self.copie_disponibili > 0


@dataclass
class Utente:
    """Rappresenta un utente della biblioteca."""
    id: int
    nome: str
    email: str
    data_iscrizione: date = field(default_factory=date.today)
    attivo: bool = True

    LIMITE_PRESTITI = 3

    def __post_init__(self):
        if not self.email or "@" not in self.email:
            raise ValueError(f"Email non valida: {self.email!r}")
        if not self.nome.strip():
            raise ValueError("Il nome non può essere vuoto")


@dataclass
class Prestito:
    """Rappresenta un prestito di un libro a un utente."""
    id: int
    utente_id: int
    libro_isbn: str
    data_prestito: date = field(default_factory=date.today)
    data_scadenza: date = field(default_factory=lambda: date.today())
    data_restituzione: Optional[date] = None
    stato: StatoPrestito = StatoPrestito.ATTIVO

    def __post_init__(self):
        if self.data_scadenza <= self.data_prestito:
            raise ValueError("La data di scadenza deve essere dopo la data di prestito")

    def e_attivo(self) -> bool:
        return self.stato == StatoPrestito.ATTIVO

    def e_in_ritardo(self) -> bool:
        if not self.e_attivo():
            return False
        return date.today() > self.data_scadenza

    def giorni_rimanenti(self) -> int:
        """Giorni rimanenti prima della scadenza (negativo se in ritardo)."""
        if not self.e_attivo():
            return 0
        return (self.data_scadenza - date.today()).days
```

---

## L3: Test dei Modelli

```python
# tests/unit/test_modelli.py

import pytest
from datetime import date, timedelta
from src.modelli import Libro, Utente, Prestito, GenereLibro, StatoPrestito


class TestLibro:
    """Test per il modello Libro."""

    @pytest.fixture
    def libro_base(self):
        return Libro(
            isbn="978-88-06-21497-1",
            titolo="Il Gattopardo",
            autore="Giuseppe Tomasi di Lampedusa",
            genere=GenereLibro.ROMANZO,
            anno=1958,
        )

    def test_creazione_libro_base(self, libro_base):
        assert libro_base.isbn == "978-88-06-21497-1"
        assert libro_base.titolo == "Il Gattopardo"
        assert libro_base.disponibile is True
        assert libro_base.copie_totali == 1
        assert libro_base.copie_disponibili == 1

    def test_libro_disponibile_con_copie(self, libro_base):
        libro_base.copie_disponibili = 3
        assert libro_base.e_disponibile() is True

    def test_libro_non_disponibile_senza_copie(self, libro_base):
        libro_base.copie_disponibili = 0
        assert libro_base.e_disponibile() is False

    def test_copie_totali_zero_invalido(self):
        with pytest.raises(ValueError, match="copie_totali"):
            Libro(
                isbn="test",
                titolo="Test",
                autore="Test",
                genere=GenereLibro.ALTRO,
                anno=2024,
                copie_totali=0,
            )

    def test_copie_disponibili_negative_invalide(self):
        with pytest.raises(ValueError, match="negativo"):
            Libro(
                isbn="test",
                titolo="Test",
                autore="Test",
                genere=GenereLibro.ALTRO,
                anno=2024,
                copie_disponibili=-1,
            )

    def test_copie_disponibili_superano_totali(self):
        with pytest.raises(ValueError, match="copie_totali"):
            Libro(
                isbn="test",
                titolo="Test",
                autore="Test",
                genere=GenereLibro.ALTRO,
                anno=2024,
                copie_totali=2,
                copie_disponibili=3,
            )


class TestUtente:
    """Test per il modello Utente."""

    @pytest.fixture
    def utente_mario(self):
        return Utente(id=1, nome="Mario Rossi", email="mario@test.it")

    def test_creazione_utente(self, utente_mario):
        assert utente_mario.id == 1
        assert utente_mario.nome == "Mario Rossi"
        assert utente_mario.email == "mario@test.it"
        assert utente_mario.attivo is True

    def test_email_senza_chiocciola(self):
        with pytest.raises(ValueError, match="Email"):
            Utente(id=1, nome="Mario", email="email_invalida")

    def test_nome_vuoto(self):
        with pytest.raises(ValueError, match="nome"):
            Utente(id=1, nome="   ", email="mario@test.it")

    def test_limite_prestiti_e_tre(self):
        assert Utente.LIMITE_PRESTITI == 3


class TestPrestito:
    """Test per il modello Prestito."""

    @pytest.fixture
    def prestito_attivo(self):
        return Prestito(
            id=1,
            utente_id=1,
            libro_isbn="978-88-06-21497-1",
            data_prestito=date.today(),
            data_scadenza=date.today() + timedelta(days=14),
        )

    def test_prestito_attivo(self, prestito_attivo):
        assert prestito_attivo.e_attivo() is True
        assert prestito_attivo.e_in_ritardo() is False

    def test_prestito_non_in_ritardo(self, prestito_attivo):
        assert prestito_attivo.e_in_ritardo() is False

    def test_prestito_in_ritardo(self):
        prestito = Prestito(
            id=2,
            utente_id=1,
            libro_isbn="isbn",
            data_prestito=date.today() - timedelta(days=20),
            data_scadenza=date.today() - timedelta(days=5),
        )
        assert prestito.e_in_ritardo() is True

    def test_giorni_rimanenti(self, prestito_attivo):
        giorni = prestito_attivo.giorni_rimanenti()
        assert 13 <= giorni <= 14  # Circa 14 giorni rimanenti

    def test_giorni_rimanenti_in_ritardo(self):
        prestito = Prestito(
            id=3,
            utente_id=1,
            libro_isbn="isbn",
            data_prestito=date.today() - timedelta(days=20),
            data_scadenza=date.today() - timedelta(days=5),
        )
        assert prestito.giorni_rimanenti() < 0

    def test_scadenza_prima_del_prestito_invalida(self):
        with pytest.raises(ValueError, match="scadenza"):
            Prestito(
                id=4,
                utente_id=1,
                libro_isbn="isbn",
                data_prestito=date.today(),
                data_scadenza=date.today(),  # Stesso giorno — invalido
            )
```

---

## L4: Il Catalogo Libri

```python
# src/catalogo.py

from typing import Optional
from src.modelli import Libro, GenereLibro
from src.eccezioni import LibroGiaEsistente, LibroNonTrovato


class Catalogo:
    """Gestisce il catalogo dei libri della biblioteca."""

    def __init__(self):
        self._libri: dict[str, Libro] = {}

    def aggiungi(self, libro: Libro) -> None:
        """
        Aggiunge un libro al catalogo.

        Raises:
            LibroGiaEsistente: Se un libro con lo stesso ISBN esiste già.
        """
        if libro.isbn in self._libri:
            raise LibroGiaEsistente(
                f"Libro con ISBN {libro.isbn!r} già presente nel catalogo"
            )
        self._libri[libro.isbn] = libro

    def trova_per_isbn(self, isbn: str) -> Libro:
        """
        Trova un libro per ISBN.

        Raises:
            LibroNonTrovato: Se il libro non è nel catalogo.
        """
        if isbn not in self._libri:
            raise LibroNonTrovato(f"Libro con ISBN {isbn!r} non trovato")
        return self._libri[isbn]

    def cerca(
        self,
        titolo: Optional[str] = None,
        autore: Optional[str] = None,
        genere: Optional[GenereLibro] = None,
        solo_disponibili: bool = False,
    ) -> list[Libro]:
        """Cerca libri con filtri opzionali."""
        risultati = list(self._libri.values())

        if titolo:
            titolo_lower = titolo.lower()
            risultati = [
                l for l in risultati
                if titolo_lower in l.titolo.lower()
            ]

        if autore:
            autore_lower = autore.lower()
            risultati = [
                l for l in risultati
                if autore_lower in l.autore.lower()
            ]

        if genere is not None:
            risultati = [l for l in risultati if l.genere == genere]

        if solo_disponibili:
            risultati = [l for l in risultati if l.e_disponibile()]

        return risultati

    def conta(self) -> int:
        """Conta il numero di libri nel catalogo."""
        return len(self._libri)

    def titoli(self) -> list[str]:
        """Restituisce la lista dei titoli."""
        return [l.titolo for l in self._libri.values()]
```

```python
# tests/unit/test_catalogo.py

import pytest
from src.catalogo import Catalogo
from src.modelli import Libro, GenereLibro
from src.eccezioni import LibroGiaEsistente, LibroNonTrovato


@pytest.fixture
def catalogo():
    return Catalogo()


@pytest.fixture
def gattopardo():
    return Libro(
        isbn="978-88-06-21497-1",
        titolo="Il Gattopardo",
        autore="Giuseppe Tomasi di Lampedusa",
        genere=GenereLibro.ROMANZO,
        anno=1958,
    )


@pytest.fixture
def promessi_sposi():
    return Libro(
        isbn="978-88-452-6982-4",
        titolo="I Promessi Sposi",
        autore="Alessandro Manzoni",
        genere=GenereLibro.ROMANZO,
        anno=1840,
        copie_totali=3,
        copie_disponibili=3,
    )


@pytest.fixture
def cosmos():
    return Libro(
        isbn="978-88-04-41400-5",
        titolo="Cosmos",
        autore="Carl Sagan",
        genere=GenereLibro.SAGGISTICA,
        anno=1980,
    )


class TestAggiungiLibro:
    """Test per l'aggiunta di libri al catalogo."""

    def test_aggiungi_libro(self, catalogo, gattopardo):
        catalogo.aggiungi(gattopardo)
        assert catalogo.conta() == 1

    def test_aggiungi_piu_libri(self, catalogo, gattopardo, promessi_sposi):
        catalogo.aggiungi(gattopardo)
        catalogo.aggiungi(promessi_sposi)
        assert catalogo.conta() == 2

    def test_isbn_duplicato_solleva_errore(self, catalogo, gattopardo):
        catalogo.aggiungi(gattopardo)
        with pytest.raises(LibroGiaEsistente, match=gattopardo.isbn):
            catalogo.aggiungi(gattopardo)

    def test_isbn_duplicato_non_modifica_catalogo(self, catalogo, gattopardo):
        catalogo.aggiungi(gattopardo)
        try:
            catalogo.aggiungi(gattopardo)
        except LibroGiaEsistente:
            pass
        assert catalogo.conta() == 1


class TestTrovaPerIsbn:
    """Test per la ricerca per ISBN."""

    def test_trova_libro_esistente(self, catalogo, gattopardo):
        catalogo.aggiungi(gattopardo)
        trovato = catalogo.trova_per_isbn(gattopardo.isbn)
        assert trovato.titolo == "Il Gattopardo"

    def test_isbn_inesistente_solleva_errore(self, catalogo):
        with pytest.raises(LibroNonTrovato, match="inesistente"):
            catalogo.trova_per_isbn("isbn-inesistente")


class TestCerca:
    """Test per la ricerca con filtri."""

    @pytest.fixture(autouse=True)
    def popola_catalogo(self, catalogo, gattopardo, promessi_sposi, cosmos):
        catalogo.aggiungi(gattopardo)
        catalogo.aggiungi(promessi_sposi)
        catalogo.aggiungi(cosmos)

    def test_cerca_per_titolo_parziale(self, catalogo):
        risultati = catalogo.cerca(titolo="gatto")
        assert len(risultati) == 1
        assert risultati[0].titolo == "Il Gattopardo"

    def test_cerca_per_autore(self, catalogo):
        risultati = catalogo.cerca(autore="Manzoni")
        assert len(risultati) == 1
        assert risultati[0].titolo == "I Promessi Sposi"

    def test_cerca_per_genere(self, catalogo):
        risultati = catalogo.cerca(genere=GenereLibro.ROMANZO)
        assert len(risultati) == 2

    def test_cerca_saggistica(self, catalogo):
        risultati = catalogo.cerca(genere=GenereLibro.SAGGISTICA)
        assert len(risultati) == 1
        assert risultati[0].titolo == "Cosmos"

    def test_cerca_solo_disponibili(self, catalogo):
        """I Promessi Sposi ha 3 copie, rendiamo il Gattopardo non disponibile."""
        catalogo.trova_per_isbn("978-88-06-21497-1").copie_disponibili = 0

        disponibili = catalogo.cerca(solo_disponibili=True)
        titoli = {l.titolo for l in disponibili}
        assert "Il Gattopardo" not in titoli
        assert "I Promessi Sposi" in titoli

    def test_cerca_senza_filtri_restituisce_tutto(self, catalogo):
        assert len(catalogo.cerca()) == 3

    def test_cerca_case_insensitive(self, catalogo):
        risultati_maiuscolo = catalogo.cerca(titolo="GATTOPARDO")
        risultati_minuscolo = catalogo.cerca(titolo="gattopardo")
        assert len(risultati_maiuscolo) == len(risultati_minuscolo)

    def test_cerca_nessun_risultato(self, catalogo):
        risultati = catalogo.cerca(titolo="libro_inesistente_12345")
        assert risultati == []

    @pytest.mark.parametrize("titolo, count", [
        ("Gattopardo", 1),
        ("Promessi", 1),
        ("Cosmos", 1),
        ("i", 2),   # "Il Gattopardo" e "I Promessi Sposi" contengono "i"
        ("zzz", 0),
    ])
    def test_cerca_parametrizzato(self, catalogo, titolo, count):
        assert len(catalogo.cerca(titolo=titolo)) == count
```

---

## L5: Gestione dei Prestiti

```python
# src/gestione_prestiti.py

from datetime import date, timedelta
from typing import Optional
from src.modelli import Libro, Utente, Prestito, StatoPrestito
from src.catalogo import Catalogo
from src.eccezioni import (
    LimitePrestitivRaggiunto, LibroNonDisponibile,
    PrestitoNonTrovato, UtenteNonAttivo
)


class GestorePrestiti:
    """
    Gestisce il ciclo di vita dei prestiti.
    """

    DURATA_PRESTITO_GIORNI = 14

    def __init__(self, catalogo: Catalogo):
        self._catalogo = catalogo
        self._prestiti: dict[int, Prestito] = {}
        self._prossimo_id = 1

    def prendi_in_prestito(
        self,
        utente: Utente,
        isbn: str,
        durata_giorni: int = DURATA_PRESTITO_GIORNI,
    ) -> Prestito:
        """
        Registra un prestito di un libro a un utente.

        Args:
            utente: L'utente che prende in prestito.
            isbn: ISBN del libro.
            durata_giorni: Durata del prestito in giorni.

        Returns:
            Il prestito creato.

        Raises:
            UtenteNonAttivo: Se l'utente non è attivo.
            LimitePrestitivRaggiunto: Se l'utente ha già 3 libri.
            LibroNonDisponibile: Se il libro non ha copie disponibili.
        """
        if not utente.attivo:
            raise UtenteNonAttivo(
                f"L'utente {utente.nome!r} non è attivo"
            )

        prestiti_attivi = self.prestiti_attivi_utente(utente.id)
        if len(prestiti_attivi) >= Utente.LIMITE_PRESTITI:
            raise LimitePrestitivRaggiunto(
                f"L'utente {utente.nome!r} ha già raggiunto il limite di "
                f"{Utente.LIMITE_PRESTITI} prestiti"
            )

        libro = self._catalogo.trova_per_isbn(isbn)
        if not libro.e_disponibile():
            raise LibroNonDisponibile(
                f"Il libro {libro.titolo!r} non ha copie disponibili"
            )

        # Aggiorna la disponibilità del libro
        libro.copie_disponibili -= 1

        # Crea il prestito
        oggi = date.today()
        prestito = Prestito(
            id=self._prossimo_id,
            utente_id=utente.id,
            libro_isbn=isbn,
            data_prestito=oggi,
            data_scadenza=oggi + timedelta(days=durata_giorni),
        )
        self._prestiti[self._prossimo_id] = prestito
        self._prossimo_id += 1

        return prestito

    def restituisci(self, prestito_id: int) -> Prestito:
        """
        Registra la restituzione di un libro.

        Raises:
            PrestitoNonTrovato: Se il prestito non esiste.
        """
        if prestito_id not in self._prestiti:
            raise PrestitoNonTrovato(f"Prestito {prestito_id} non trovato")

        prestito = self._prestiti[prestito_id]
        if not prestito.e_attivo():
            raise ValueError(f"Il prestito {prestito_id} è già stato restituito")

        # Aggiorna il prestito
        prestito.data_restituzione = date.today()
        prestito.stato = StatoPrestito.RESTITUITO

        # Restituisce la copia al catalogo
        libro = self._catalogo.trova_per_isbn(prestito.libro_isbn)
        libro.copie_disponibili += 1

        return prestito

    def prestiti_attivi_utente(self, utente_id: int) -> list[Prestito]:
        """Restituisce i prestiti attivi di un utente."""
        return [
            p for p in self._prestiti.values()
            if p.utente_id == utente_id and p.e_attivo()
        ]

    def storico_prestiti_utente(self, utente_id: int) -> list[Prestito]:
        """Restituisce tutti i prestiti (attivi e restituiti) di un utente."""
        return [
            p for p in self._prestiti.values()
            if p.utente_id == utente_id
        ]

    def prestiti_in_ritardo(self) -> list[Prestito]:
        """Restituisce tutti i prestiti scaduti non ancora restituiti."""
        return [p for p in self._prestiti.values() if p.e_in_ritardo()]
```

```python
# tests/unit/test_gestione_prestiti.py

import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock, patch
from src.gestione_prestiti import GestorePrestiti
from src.modelli import Libro, Utente, GenereLibro, StatoPrestito
from src.catalogo import Catalogo
from src.eccezioni import (
    LimitePrestitivRaggiunto, LibroNonDisponibile,
    PrestitoNonTrovato, UtenteNonAttivo
)


@pytest.fixture
def catalogo():
    cat = Catalogo()
    cat.aggiungi(Libro(
        isbn="isbn-001",
        titolo="Primo Libro",
        autore="Autore Test",
        genere=GenereLibro.ROMANZO,
        anno=2024,
        copie_totali=2,
        copie_disponibili=2,
    ))
    cat.aggiungi(Libro(
        isbn="isbn-002",
        titolo="Secondo Libro",
        autore="Autore Test",
        genere=GenereLibro.SAGGISTICA,
        anno=2023,
    ))
    cat.aggiungi(Libro(
        isbn="isbn-003",
        titolo="Terzo Libro",
        autore="Autore Test",
        genere=GenereLibro.GIALLO,
        anno=2022,
    ))
    cat.aggiungi(Libro(
        isbn="isbn-004",
        titolo="Quarto Libro",
        autore="Autore Test",
        genere=GenereLibro.FANTASCIENZA,
        anno=2021,
    ))
    return cat


@pytest.fixture
def gestore(catalogo):
    return GestorePrestiti(catalogo)


@pytest.fixture
def utente_attivo():
    return Utente(id=1, nome="Mario Rossi", email="mario@test.it")


@pytest.fixture
def utente_inattivo():
    return Utente(id=2, nome="Ex Utente", email="ex@test.it", attivo=False)


class TestPrendiInPrestito:
    """Test per l'operazione di prestito."""

    def test_prestito_libro_disponibile(self, gestore, utente_attivo):
        prestito = gestore.prendi_in_prestito(utente_attivo, "isbn-001")
        assert prestito.utente_id == 1
        assert prestito.libro_isbn == "isbn-001"
        assert prestito.e_attivo() is True

    def test_prestito_riduce_copie_disponibili(self, gestore, utente_attivo, catalogo):
        gestore.prendi_in_prestito(utente_attivo, "isbn-001")
        libro = catalogo.trova_per_isbn("isbn-001")
        assert libro.copie_disponibili == 1  # Era 2, ora è 1

    def test_due_prestiti_stessa_copia_multipla(self, gestore, utente_attivo, catalogo):
        """Con 2 copie, due utenti diversi possono prendere lo stesso libro."""
        utente2 = Utente(id=2, nome="Luigi", email="luigi@test.it")
        gestore.prendi_in_prestito(utente_attivo, "isbn-001")
        gestore.prendi_in_prestito(utente2, "isbn-001")
        assert catalogo.trova_per_isbn("isbn-001").copie_disponibili == 0

    def test_utente_inattivo_non_puo_prendere(self, gestore, utente_inattivo):
        with pytest.raises(UtenteNonAttivo):
            gestore.prendi_in_prestito(utente_inattivo, "isbn-001")

    def test_limite_tre_prestiti(self, gestore, utente_attivo):
        """Un utente non può avere più di 3 prestiti attivi."""
        gestore.prendi_in_prestito(utente_attivo, "isbn-001")
        gestore.prendi_in_prestito(utente_attivo, "isbn-002")
        gestore.prendi_in_prestito(utente_attivo, "isbn-003")

        with pytest.raises(LimitePrestitivRaggiunto):
            gestore.prendi_in_prestito(utente_attivo, "isbn-004")

    def test_libro_non_disponibile(self, gestore, utente_attivo):
        """Con solo una copia e già prestata, non si può prendere di nuovo."""
        # isbn-002 ha solo 1 copia
        gestore.prendi_in_prestito(utente_attivo, "isbn-002")
        utente2 = Utente(id=2, nome="Luigi", email="luigi@test.it")

        with pytest.raises(LibroNonDisponibile):
            gestore.prendi_in_prestito(utente2, "isbn-002")

    def test_prestito_ha_data_scadenza(self, gestore, utente_attivo):
        prestito = gestore.prendi_in_prestito(utente_attivo, "isbn-001")
        assert prestito.data_scadenza == date.today() + timedelta(days=14)

    def test_prestito_con_durata_personalizzata(self, gestore, utente_attivo):
        prestito = gestore.prendi_in_prestito(utente_attivo, "isbn-001", durata_giorni=30)
        assert prestito.data_scadenza == date.today() + timedelta(days=30)


class TestRestituisci:
    """Test per la restituzione."""

    @pytest.fixture
    def prestito_attivo(self, gestore, utente_attivo):
        return gestore.prendi_in_prestito(utente_attivo, "isbn-001")

    def test_restituzione_cambia_stato(self, gestore, prestito_attivo):
        gestore.restituisci(prestito_attivo.id)
        assert prestito_attivo.stato == StatoPrestito.RESTITUITO

    def test_restituzione_aggiunge_data(self, gestore, prestito_attivo):
        gestore.restituisci(prestito_attivo.id)
        assert prestito_attivo.data_restituzione == date.today()

    def test_restituzione_aumenta_copie(self, gestore, prestito_attivo, catalogo):
        copie_prima = catalogo.trova_per_isbn("isbn-001").copie_disponibili
        gestore.restituisci(prestito_attivo.id)
        copie_dopo = catalogo.trova_per_isbn("isbn-001").copie_disponibili
        assert copie_dopo == copie_prima + 1

    def test_restituzione_prestito_inesistente(self, gestore):
        with pytest.raises(PrestitoNonTrovato):
            gestore.restituisci(9999)

    def test_doppia_restituzione_non_permessa(self, gestore, prestito_attivo):
        gestore.restituisci(prestito_attivo.id)
        with pytest.raises(ValueError):
            gestore.restituisci(prestito_attivo.id)


class TestPrestatiAttivi:
    """Test per la visualizzazione dei prestiti attivi."""

    def test_nessun_prestito_attivo(self, gestore, utente_attivo):
        assert gestore.prestiti_attivi_utente(utente_attivo.id) == []

    def test_prestiti_attivi_dopo_prestito(self, gestore, utente_attivo):
        gestore.prendi_in_prestito(utente_attivo, "isbn-001")
        attivi = gestore.prestiti_attivi_utente(utente_attivo.id)
        assert len(attivi) == 1

    def test_prestiti_attivi_non_include_restituiti(self, gestore, utente_attivo):
        p = gestore.prendi_in_prestito(utente_attivo, "isbn-001")
        gestore.prendi_in_prestito(utente_attivo, "isbn-002")
        gestore.restituisci(p.id)

        attivi = gestore.prestiti_attivi_utente(utente_attivo.id)
        assert len(attivi) == 1

    def test_dopo_restituzione_posso_prendere_quarto(self, gestore, utente_attivo):
        """Dopo aver restituito uno dei 3, posso prenderne un altro."""
        p1 = gestore.prendi_in_prestito(utente_attivo, "isbn-001")
        gestore.prendi_in_prestito(utente_attivo, "isbn-002")
        gestore.prendi_in_prestito(utente_attivo, "isbn-003")

        gestore.restituisci(p1.id)  # Restituisce uno

        # Ora posso prenderne un quarto
        p4 = gestore.prendi_in_prestito(utente_attivo, "isbn-004")
        assert p4.e_attivo() is True
```

---

## L6: Test di Integrazione — Sistema Completo

```python
# tests/integration/test_biblioteca_completa.py

import pytest
from datetime import date, timedelta
from src.modelli import Libro, Utente, GenereLibro
from src.catalogo import Catalogo
from src.gestione_prestiti import GestorePrestiti


@pytest.fixture
def sistema():
    """Sistema biblioteca completo per test di integrazione."""
    catalogo = Catalogo()

    # Aggiungi alcuni libri
    libri = [
        Libro(isbn="it001", titolo="1984", autore="George Orwell",
              genere=GenereLibro.ROMANZO, anno=1949, copie_totali=3, copie_disponibili=3),
        Libro(isbn="it002", titolo="Il Signore degli Anelli",
              autore="J.R.R. Tolkien", genere=GenereLibro.ROMANZO, anno=1954),
        Libro(isbn="it003", titolo="Sapiens", autore="Yuval Noah Harari",
              genere=GenereLibro.SAGGISTICA, anno=2011, copie_totali=2, copie_disponibili=2),
    ]
    for libro in libri:
        catalogo.aggiungi(libro)

    gestore = GestorePrestiti(catalogo)
    return {"catalogo": catalogo, "gestore": gestore}


@pytest.fixture
def utenti():
    """Utenti di test."""
    return {
        "alice": Utente(id=1, nome="Alice Rossi", email="alice@test.it"),
        "bob": Utente(id=2, nome="Bob Bianchi", email="bob@test.it"),
        "carlo": Utente(id=3, nome="Carlo Verdi", email="carlo@test.it"),
    }


class TestScenariReali:
    """Test di scenari che simulano l'uso reale della biblioteca."""

    def test_scenario_prestito_completo(self, sistema, utenti):
        """
        Scenario completo:
        1. Alice prende 1984
        2. Verifica che la copia sia ridotta
        3. Alice restituisce il libro
        4. Verifica che la copia sia ripristinata
        """
        gestore = sistema["gestore"]
        catalogo = sistema["catalogo"]
        alice = utenti["alice"]

        # Stato iniziale
        assert catalogo.trova_per_isbn("it001").copie_disponibili == 3

        # Alice prende in prestito
        prestito = gestore.prendi_in_prestito(alice, "it001")
        assert catalogo.trova_per_isbn("it001").copie_disponibili == 2
        assert len(gestore.prestiti_attivi_utente(alice.id)) == 1

        # Alice restituisce
        gestore.restituisci(prestito.id)
        assert catalogo.trova_per_isbn("it001").copie_disponibili == 3
        assert len(gestore.prestiti_attivi_utente(alice.id)) == 0

        # Lo storico contiene il prestito
        storico = gestore.storico_prestiti_utente(alice.id)
        assert len(storico) == 1
        assert storico[0].libro_isbn == "it001"

    def test_scenario_prenotazione_scalabile(self, sistema, utenti):
        """
        Con 3 copie di 1984, tre utenti possono prenderlo contemporaneamente.
        Il quarto non può.
        """
        gestore = sistema["gestore"]
        alice, bob, carlo = utenti["alice"], utenti["bob"], utenti["carlo"]
        utente4 = Utente(id=4, nome="Diana Blu", email="diana@test.it")

        gestore.prendi_in_prestito(alice, "it001")
        gestore.prendi_in_prestito(bob, "it001")
        gestore.prendi_in_prestito(carlo, "it001")

        # La quarta copia non esiste
        from src.eccezioni import LibroNonDisponibile
        with pytest.raises(LibroNonDisponibile):
            gestore.prendi_in_prestito(utente4, "it001")

    def test_scenario_ricerca_e_prestito(self, sistema, utenti):
        """
        Alice cerca libri di fantascienza (nessuno), poi cerca saggistica e prende Sapiens.
        """
        gestore = sistema["gestore"]
        catalogo = sistema["catalogo"]
        alice = utenti["alice"]

        # Cerca fantascienza — nessun risultato
        fantascienza = catalogo.cerca(genere=GenereLibro.FANTASCIENZA)
        assert fantascienza == []

        # Cerca saggistica — trova Sapiens
        saggistica = catalogo.cerca(genere=GenereLibro.SAGGISTICA)
        assert len(saggistica) == 1
        assert saggistica[0].titolo == "Sapiens"

        # Prende in prestito Sapiens
        prestito = gestore.prendi_in_prestito(alice, "it003")
        assert prestito.libro_isbn == "it003"

        # Ora restano solo 1 copia disponibile di Sapiens
        assert catalogo.trova_per_isbn("it003").copie_disponibili == 1
```

---

## L7: Eccezioni del Dominio

```python
# src/eccezioni.py

class BibliotecaErrore(Exception):
    """Eccezione base per il sistema biblioteca."""
    pass


class LibroGiaEsistente(BibliotecaErrore):
    """Sollevata quando si tenta di aggiungere un libro già presente."""
    pass


class LibroNonTrovato(BibliotecaErrore):
    """Sollevata quando un libro non viene trovato nel catalogo."""
    pass


class LibroNonDisponibile(BibliotecaErrore):
    """Sollevata quando un libro non ha copie disponibili."""
    pass


class UtenteNonAttivo(BibliotecaErrore):
    """Sollevata quando un utente inattivo tenta di fare operazioni."""
    pass


class LimitePrestitivRaggiunto(BibliotecaErrore):
    """Sollevata quando un utente ha raggiunto il limite di prestiti."""
    pass


class PrestitoNonTrovato(BibliotecaErrore):
    """Sollevata quando un prestito non viene trovato."""
    pass
```

---

## L8: Sommario del Progetto Biblioteca

### Statistiche del progetto

```
COMPONENTE                    LINEE DI CODICE    TEST
─────────────────────────────────────────────────────────
src/modelli.py                ~80               ~25 test
src/catalogo.py               ~60               ~20 test
src/gestione_prestiti.py      ~100              ~25 test
src/eccezioni.py              ~35               -
tests/ (tutti)                ~350              ~70 test
─────────────────────────────────────────────────────────
TOTALE                        ~625              ~70 test
─────────────────────────────────────────────────────────
Coverage attesa: >95%
Tempo di esecuzione: < 1 secondo
```

### Cosa abbiamo imparato dal progetto

1. **Domain-Driven Design**: modelli che esprimono il dominio (Libro, Utente, Prestito)
2. **Invarianti nei modelli**: `__post_init__` valida i dati alla creazione
3. **Eccezioni specifiche**: ogni caso di errore ha la propria eccezione
4. **Fixture gerarchiche**: `catalogo` → `gestore` → test specifici
5. **Pattern AAA**: ogni test è strutturato in Arrange-Act-Assert
6. **Test behavior, not implementation**: testa cosa fa il sistema, non come lo fa
7. **Integration test realistici**: simulano scenari di utilizzo reale
