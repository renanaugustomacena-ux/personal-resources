# Tutorial: Espressioni Regolari e Text Processing — Dal Principiante all'Esperto

> **Companion to:** `06-regex-e-text-processing.md`
> **Scope:** sintassi regex completa, caratteri speciali, quantificatori, gruppi, lookahead/lookbehind, flags, re.match/search/findall/sub/split, NFA engine, ReDoS, unicodedata, difflib, fuzzy matching
> **Prerequisiti:** `tutorial_01_fondamenti_linguaggio.md` completato
> **Durata stimata:** 25–30 ore
> **Lingua:** Italiano

---

## Indice Generale

- [Prima di Iniziare](#prima-di-iniziare)
- [Parte A — Le Basi delle Regex](#parte-a--le-basi-delle-regex)
  - [A.1 Cos'e una Regex](#a1-cose-una-regex)
  - [A.2 I Caratteri Speciali, Uno per Uno](#a2-i-caratteri-speciali-uno-per-uno)
  - [A.3 Classi di Caratteri Predefinite](#a3-classi-di-caratteri-predefinite)
  - [A.4 Quantificatori — Quante Volte?](#a4-quantificatori--quante-volte)
- [Parte B — Il Modulo re in Profondita](#parte-b--il-modulo-re-in-profondita)
  - [B.1 Le Funzioni Fondamentali](#b1-le-funzioni-fondamentali)
  - [B.2 re.sub — Sostituire con Pattern](#b2-resub--sostituire-con-pattern)
  - [B.3 re.split — Dividere con Pattern](#b3-resplit--dividere-con-pattern)
  - [B.4 Flag — Modificatori di Comportamento](#b4-flag--modificatori-di-comportamento)
  - [B.5 Gruppi di Cattura](#b5-gruppi-di-cattura)
  - [B.6 Lookahead e Lookbehind](#b6-lookahead-e-lookbehind)
- [Parte C — Tecniche Avanzate](#parte-c--tecniche-avanzate)
  - [C.1 re.compile e Precompilazione](#c1-recompile-e-precompilazione)
  - [C.2 Il Motore NFA e il Backtracking](#c2-il-motore-nfa-e-il-backtracking)
  - [C.3 ReDoS — Attacchi alle Regex](#c3-redos--attacchi-alle-regex)
  - [C.4 unicodedata — Testo Internazionale](#c4-unicodedata--testo-internazionale)
  - [C.5 difflib — Confrontare Testi](#c5-difflib--confrontare-testi)
  - [C.6 Fuzzy Matching con rapidfuzz](#c6-fuzzy-matching-con-rapidfuzz)
  - [C.7 Pipeline di Text Processing](#c7-pipeline-di-text-processing)
- [Parte D — Esercizi Pratici](#parte-d--esercizi-pratici)
- [Parte E — Per gli Esperti](#parte-e--per-gli-esperti)
- [Riepilogo Finale](#riepilogo-finale)

---

## Prima di Iniziare

### Perche questo tutorial esiste

Il modulo `re` di Python e uno strumento potentissimo che praticamente ogni sviluppatore Python incontra prima o poi. Il problema? La sintassi delle espressioni regolari sembra criptica alla prima lettura — una zuppa di simboli come `(?P<nome>\w+)(?=\d{2,4})` che intimorisce chi non la conosce.

Questo tutorial parte da zero e arriva fino agli usi avanzati, compreso il fuzzy matching e la prevenzione degli attacchi ReDoS. Ogni concetto viene introdotto con un'analogia concreta, poi mostrato con codice funzionante.

### Come usare questo tutorial

Ogni sezione segue questo schema:

1. **Analogia** — spiega il concetto in linguaggio naturale
2. **Sintassi** — mostra la forma esatta da usare in Python
3. **Esempi** — minimo 3 esempi commentati riga per riga
4. **Smontaggio** — per i pattern complessi, ogni pezzo viene spiegato

Non saltare la parte sulle analogie: le regex sembrano magia finche non si capisce il modello mentale sottostante. Una volta acquisito quel modello, ogni pattern diventa leggibile.

### Ambiente di lavoro

```python
# Verifica della tua versione Python
import sys
print(sys.version)  # Necessario: Python 3.9+

# Importa il modulo re (nella libreria standard, nessuna installazione richiesta)
import re

# Per le sezioni avanzate, installerai:
# pip install regex        # alternativa avanzata a re
# pip install rapidfuzz    # fuzzy matching moderno
```

### Il "test rapido" per verificare di aver capito

Dopo ogni sezione, c'e un piccolo esercizio di verifica. La soluzione e sempre nascosta subito sotto. Prova a risolverlo prima di guardare — anche un tentativo sbagliato rafforza l'apprendimento.

---

## Parte A — Le Basi delle Regex

---

### A.1 Cos'e una Regex

#### L'analogia del detective

Immagina di dover trovare una persona in una citta. Hai due opzioni:

**Opzione 1 — Ricerca esatta:** "Cerco Mario Rossi, via Roma 14, Roma." Funziona solo se sai esattamente chi stai cercando.

**Opzione 2 — Descrizione vaga ma precisa:** "Cerco chiunque si chiami Mario, abiti in una via che inizia per 'R', e viva a Roma." Questa descrizione puo trovare piu persone, ma segue regole precise.

Le **espressioni regolari** sono la seconda opzione applicata ai testi. Una regex non cerca una stringa esatta — descrive un **pattern**, una struttura, un formato che ti interessa trovare.

```
Stringa esatta:  "mario@email.it"  ← trova SOLO questo
Regex:           "[a-z]+@[a-z]+\.[a-z]+"  ← trova QUALUNQUE email simile
```

#### La definizione formale (semplificata)

Una **espressione regolare** (abbreviata regex o regexp) e una sequenza di caratteri che definisce un pattern di ricerca. Viene usata per:

- **Trovare** testo che corrisponde a un certo formato
- **Validare** che un input rispetti un certo schema
- **Estrarre** parti specifiche di un testo
- **Sostituire** testo che corrisponde a un pattern
- **Dividere** un testo in base a separatori variabili

#### Il tuo primo esempio funzionante

```python
import re

testo = "Il numero di telefono e 333-1234567, grazie"

# Cerca un pattern: tre cifre, un trattino, sette cifre
# \d = "una cifra qualsiasi" (d sta per digit)
# {3} = "esattamente 3 volte"
match = re.search(r"\d{3}-\d{7}", testo)

if match:
    print(f"Trovato: {match.group()}")  # Trovato: 333-1234567
    print(f"Posizione: {match.span()}")  # Posizione: (25, 37)
```

Smontiamo il pattern `r"\d{3}-\d{7}"` pezzo per pezzo:

```
\d     → "una qualsiasi cifra (0-9)"
{3}    → "esattamente 3 volte"
-      → "un trattino letterale"
\d     → "una qualsiasi cifra (0-9)"
{7}    → "esattamente 7 volte"
```

Il prefisso `r` prima della stringa significa **raw string**: il backslash viene passato direttamente al motore regex senza essere interpretato da Python. Usalo SEMPRE nelle regex.

#### Perche `r"..."` e non `"..."`?

```python
# SENZA raw string: Python interpreta \d come "d" (backslash non valido)
print("\d")   # stampa: \d (Python lo lascia stare, ma e ambiguo)

# CON raw string: il backslash arriva intatto al motore regex
print(r"\d")  # stampa: \d (questo e quello che vogliamo)

# Il problema diventa evidente con \n:
print("\n")   # newline! Python lo interpreta
print(r"\n")  # \n letterale, il motore regex lo legge come "newline"

# Regola: usa SEMPRE r"..." per le regex
pattern_sbagliato = "\d+"    # potenziale problema
pattern_corretto  = r"\d+"   # sempre sicuro
```

---

### A.2 I Caratteri Speciali, Uno per Uno

I **metacaratteri** sono caratteri che nelle regex hanno un significato speciale — non rappresentano se stessi ma istruzioni per il motore. Sono quattordici:

```
.  ^  $  *  +  ?  {  }  [  ]  \  |  (  )
```

Analizziamo ognuno con la sua analogia e tre esempi pratici.

---

#### Il Punto `.` — "Qualsiasi Carattere"

**Analogia:** Il punto e come un jolly nel gioco delle carte — puo essere qualsiasi cosa. In una regex, `.` corrisponde a qualsiasi singolo carattere, tranne il newline `\n` (per default).

```python
import re

# Esempio 1: trova qualsiasi parola di 4 lettere che inizia per 'c' e finisce per 'a'
testo = "casa cosa cesa cusa c1sa"
risultato = re.findall(r"c.sa", testo)
print(risultato)
# Output: ['casa', 'cosa', 'cesa', 'cusa', 'c1sa']
# Il punto ha accettato: 'a', 'o', 'e', 'u', '1' — qualsiasi cosa!

# Esempio 2: trova tre caratteri qualsiasi seguiti da "it"
testo = "mio sito web: edit.it / exit.it"
risultato = re.findall(r"...it", testo)
print(risultato)
# Output: ['edit', 'exit']
# Ogni punto ha catturato un carattere diverso

# Esempio 3: il punto NON cattura il newline (per default)
testo_multiriga = "inizio\nfine"
risultato = re.findall(r"inizio.fine", testo_multiriga)
print(risultato)
# Output: [] — il punto non ha attraversato il newline
# Per attraversare il newline, si usa il flag re.DOTALL
risultato_dotall = re.findall(r"inizio.fine", testo_multiriga, re.DOTALL)
print(risultato_dotall)
# Output: ['inizio\nfine'] — ora cattura anche i newline
```

**Come fare match su un punto letterale:** usa `\.` (backslash + punto)

```python
# Cercare "file.txt" letteralmente
re.findall(r"file\.txt", "file.txt filetxt file-txt")
# Output: ['file.txt'] — solo quello con il punto vero
```

---

#### L'Asterisco `*` — "Zero o Piu Volte"

**Analogia:** L'asterisco e come un foglio di presenze che non obbliga nessuno. Dice: "questo elemento puo esserci zero volte, una volta, o mille volte — non importa."

```python
import re

# Esempio 1: 'b' puo comparire zero o piu volte tra 'a' e 'c'
testo = "ac abc abbc abbbc"
risultato = re.findall(r"ab*c", testo)
print(risultato)
# Output: ['ac', 'abc', 'abbc', 'abbbc']
# 'ac'    → zero 'b'
# 'abc'   → una 'b'
# 'abbc'  → due 'b'
# 'abbbc' → tre 'b'

# Esempio 2: spazi opzionali (zero o piu) tra parole
testo = "ciao     mondo  Python"
risultato = re.findall(r"\w+\s*\w*", testo)
print(risultato)
# \s* accetta qualsiasi numero di spazi, incluso nessuno

# Esempio 3: attenzione al "zero o piu" — puo trovare stringhe vuote!
testo = "abc"
risultato = re.findall(r"x*", testo)
print(risultato)
# Output: ['', '', '', ''] — trova stringhe vuote tra ogni carattere!
# Questo e un comportamento comune che sorprende i principianti
```

---

#### Il Segno Piu `+` — "Uno o Piu Volte"

**Analogia:** Il `+` e l'asterisco con un minimo garantito. Mentre `*` accetta "anche zero", `+` pretende almeno uno. E come un ristorante che richiede almeno una consumazione.

```python
import re

# Esempio 1: confronto tra * e +
testo = "ac abc abbc"
print(re.findall(r"ab*c", testo))  # ['ac', 'abc', 'abbc'] — 'ac' incluso
print(re.findall(r"ab+c", testo))  # ['abc', 'abbc'] — 'ac' escluso (zero 'b')

# Esempio 2: trovare sequenze di cifre (almeno una)
testo = "prezzo: 42 euro, sconto 0 euro"
risultato = re.findall(r"\d+", testo)
print(risultato)
# Output: ['42', '0']
# \d+ ha trovato numeri di qualsiasi lunghezza, purche almeno una cifra

# Esempio 3: trovare parole (almeno un carattere word)
testo = "un testo con   molti spazi   tra le parole"
parole = re.findall(r"\w+", testo)
print(parole)
# Output: ['un', 'testo', 'con', 'molti', 'spazi', 'tra', 'le', 'parole']
# \w+ cattura ogni sequenza di caratteri alfanumerici
```

---

#### Il Punto Interrogativo `?` — "Opzionale (Zero o Una Volta)"

**Analogia:** Il `?` e come il suffisso "-ish" in inglese o "circa" in italiano — indica che qualcosa puo esserci o meno. "Mangio alle 8?" — forse si, forse no, non cambia il senso della frase.

```python
import re

# Esempio 1: ortografia alternativa ('colour' vs 'color')
testo = "color colour"
risultato = re.findall(r"colou?r", testo)
print(risultato)
# Output: ['color', 'colour']
# La 'u' e opzionale: u? significa "zero o una 'u'"

# Esempio 2: prefisso internazionale telefonico opzionale
testo = "+39 333-1234567 e anche 333-7654321"
risultato = re.findall(r"(?:\+39\s?)?\d{3}-\d{7}", testo)
print(risultato)
# Output: ['+39 333-1234567', '333-7654321']
# Il blocco (?:\+39\s?)? e opzionale nel suo insieme

# Esempio 3: il segno meno opzionale nei numeri negativi
testo = "temperature: -5, 0, +3, 18"
risultato = re.findall(r"-?\d+", testo)
print(risultato)
# Output: ['-5', '0', '3', '18']
# Nota: '+3' diventa '3' perche + non e gestito (solo - e opzionale)
```

**Attenzione:** `?` ha anche un secondo uso — quando segue un altro quantificatore, lo rende "lazy" (pigro). Lo vediamo in A.4.

---

#### Il Cappello `^` — "Inizio della Stringa"

**Analogia:** Il `^` e come un buttafuori che controlla solo l'ingresso. Si preoccupa solo di cosa c'e all'inizio — il resto non lo interessa (a meno che non si usi con `re.MULTILINE`).

```python
import re

# Esempio 1: trovare righe che iniziano con "Errore"
testi = ["Errore: connessione rifiutata", "INFO: server avviato", "Errore: timeout"]
for t in testi:
    if re.search(r"^Errore", t):
        print(f"Errore trovato: {t}")
# Output:
# Errore trovato: Errore: connessione rifiutata
# Errore trovato: Errore: timeout

# Esempio 2: validare che una stringa inizi con una lettera maiuscola
test_stringhe = ["Mario Rossi", "mario rossi", "123 numeri", "Python"]
for s in test_stringhe:
    if re.match(r"^[A-Z]", s):
        print(f"  Inizia con maiuscola: '{s}'")
    else:
        print(f"  Non inizia con maiuscola: '{s}'")

# Esempio 3: con re.MULTILINE, ^ funziona su ogni riga
testo = "Prima riga\nSeconda riga\nTerza riga"
risultato = re.findall(r"^\w+", testo, re.MULTILINE)
print(risultato)
# Output: ['Prima', 'Seconda', 'Terza']
# Senza re.MULTILINE: ['Prima']
```

---

#### Il Dollaro `$` — "Fine della Stringa"

**Analogia:** Il `$` e l'opposto del `^` — e il buttafuori dell'uscita. Verifica solo cosa c'e alla fine.

```python
import re

# Esempio 1: trovare file Python (terminano con .py)
file = ["script.py", "dati.csv", "modulo.py", "immagine.png"]
py_files = [f for f in file if re.search(r"\.py$", f)]
print(py_files)
# Output: ['script.py', 'modulo.py']

# Esempio 2: validare che una stringa termini con punto esclamativo o interrogativo
frasi = ["Ciao!", "Come stai?", "Questo e un fatto.", "Ciao", "Attenzione!"]
for f in frasi:
    if re.search(r"[!?]$", f):
        print(f"  Frase esclamativa/interrogativa: '{f}'")

# Esempio 3: combinare ^ e $ per validare l'intera stringa
# Solo numeri, esattamente 5 cifre (es. CAP italiano)
cap_validi = ["20121", "00100", "12345", "1234", "123456", "2012a"]
for cap in cap_validi:
    if re.fullmatch(r"\d{5}", cap):
        print(f"  CAP valido: {cap}")
    else:
        print(f"  CAP non valido: {cap}")
# Output:
# CAP valido: 20121
# CAP valido: 00100
# CAP valido: 12345
# CAP non valido: 1234    (troppo corto)
# CAP non valido: 123456  (troppo lungo)
# CAP non valido: 2012a   (contiene una lettera)
```

---

#### Il Pipe `|` — "Oppure (OR Logico)"

**Analogia:** Il `|` e come un cartello con due frecce: "Roma O Milano". Dice al motore: "prova questa alternativa, e se non funziona, prova quella."

```python
import re

# Esempio 1: cercare animali diversi
testo = "ho un gatto, poi un cane, e anche un pesce"
risultato = re.findall(r"gatto|cane|pesce", testo)
print(risultato)
# Output: ['gatto', 'cane', 'pesce']

# Esempio 2: cercare colori in italiano e inglese
testo = "la macchina rossa, the red car, la voiture rouge"
risultato = re.findall(r"rossa|rosso|red|rouge", testo)
print(risultato)
# Output: ['rossa', 'red', 'rouge']

# Esempio 3: validare estensioni file
def e_immagine(nome_file: str) -> bool:
    """Controlla se un file e un'immagine."""
    return bool(re.search(r"\.(jpg|jpeg|png|gif|webp|svg)$", nome_file, re.IGNORECASE))

print(e_immagine("foto.jpg"))   # True
print(e_immagine("foto.JPG"))   # True (grazie a re.IGNORECASE)
print(e_immagine("dati.csv"))   # False
print(e_immagine("img.png"))    # True
```

**Importante:** `|` ha la precedenza piu bassa tra tutti i metacaratteri. `cat|dog food` significa `cat` OPPURE `dog food` — non `cat food` OPPURE `dog food`. Per limitare lo scope dell'alternativa, usa i gruppi `( )`.

```python
# Senza gruppi: "cat" OPPURE "dog food"
re.findall(r"cat|dog food", "I have cat food and dog food")
# Output: ['cat', 'dog food']

# Con gruppi: "cat food" OPPURE "dog food"
re.findall(r"(?:cat|dog) food", "I have cat food and dog food")
# Output: ['cat food', 'dog food']
```

---

#### Il Backslash `\` — "Carattere di Escape"

**Analogia:** Il backslash e come le virgolette in un dialogo: "disse 'ciao'". Le virgolette interne non terminano il dialogo — sono "virgolette vere" dentro. Il `\` dice: "il prossimo carattere e letterale, non un metacarattere."

```python
import re

# Esempio 1: cercare un punto letterale (non il metacarattere .)
testo = "versione 3.12 e versione 412"
# Senza escape: il punto cattura qualsiasi carattere
print(re.findall(r"3.12", testo))   # ['3.12', '3 12'... potenzialmente]
# Con escape: il punto e letterale
print(re.findall(r"3\.12", testo))  # ['3.12'] — solo il punto vero

# Esempio 2: cercare parentesi letterali
testo = "funzione(arg1, arg2) e altra()"
# Le parentesi senza escape hanno significato speciale (gruppi)
print(re.findall(r"\w+\(\w*\)", testo))
# Output: ['funzione(arg1', 'altra()']  — attenzione ai limiti
# Versione migliorata:
print(re.findall(r"\w+\([^)]*\)", testo))
# Output: ['funzione(arg1, arg2)', 'altra()']

# Esempio 3: cercare il carattere backslash stesso
# Per trovare un backslash, si usa \\ (due backslash nella raw string)
testo = r"percorso C:\Users\mario\file.txt"
risultato = re.findall(r"\\[A-Za-z]+", testo)
print(risultato)
# Output: ['\\Users', '\\mario']
```

**Il backslash puo anche creare sequenze speciali:**

| Sequenza | Significato |
|----------|-------------|
| `\d` | cifra (digit) |
| `\w` | carattere "word" |
| `\s` | spazio bianco |
| `\n` | newline |
| `\t` | tab |
| `\b` | word boundary (confine di parola) |

---

#### Le Parentesi Tonde `( )` — "Raggruppa e Cattura"

**Analogia:** Le parentesi tonde sono come le parentesi in matematica: raggruppano elementi insieme. Ma in regex hanno un superpotere: tutto quello che sta dentro viene "fotografato" e puoi recuperarlo dopo.

```python
import re

# Esempio 1: estrarre il dominio da un'email
email = "mario.rossi@esempio.it"
match = re.search(r"(\w+)@(\w+)\.(\w+)", email)
if match:
    print(f"Utente: {match.group(1)}")   # mario
    print(f"Dominio: {match.group(2)}")  # esempio
    print(f"TLD: {match.group(3)}")      # it

# Esempio 2: estrarre data in formato gg/mm/aaaa
testo = "Nato il 15/03/1990"
match = re.search(r"(\d{2})/(\d{2})/(\d{4})", testo)
if match:
    giorno, mese, anno = match.groups()  # unpacking di tutti i gruppi
    print(f"Giorno: {giorno}, Mese: {mese}, Anno: {anno}")
    # Output: Giorno: 15, Mese: 03, Anno: 1990

# Esempio 3: le parentesi cambiano il comportamento di findall
testo = "prezzo: 42 euro, sconto: 5 euro"

# Senza gruppi: findall restituisce i match completi
print(re.findall(r"\d+ euro", testo))
# Output: ['42 euro', '5 euro']

# Con gruppi: findall restituisce SOLO il contenuto dei gruppi
print(re.findall(r"(\d+) euro", testo))
# Output: ['42', '5'] — solo i numeri!
```

---

#### Le Parentesi Quadre `[ ]` — "Scegli da Questo Insieme"

**Analogia:** Le parentesi quadre sono come un menu a scelta multipla — definisci un insieme di caratteri accettabili e il motore ne sceglie uno.

```python
import re

# Esempio 1: qualsiasi vocale
testo = "programmazione"
vocali = re.findall(r"[aeiou]", testo)
print(vocali)
# Output: ['o', 'a', 'a', 'i', 'o', 'e']

# Esempio 2: intervalli [a-z], [A-Z], [0-9]
testo = "Hello World 123"
# Tutte le lettere minuscole
print(re.findall(r"[a-z]+", testo))  # ['ello', 'orld']
# Tutte le lettere
print(re.findall(r"[A-Za-z]+", testo))  # ['Hello', 'World']
# Tutte le cifre
print(re.findall(r"[0-9]+", testo))  # ['123']

# Esempio 3: negazione con [^...]
testo = "abc123def456"
# Tutto tranne le cifre
print(re.findall(r"[^0-9]+", testo))  # ['abc', 'def']
# Tutto tranne le lettere minuscole
print(re.findall(r"[^a-z]+", testo))  # ['123', '456']
```

**Regole speciali dentro `[ ]`:**
- Il punto `.` dentro `[ ]` e letterale (non metacarattere)
- Il `^` all'inizio inverte l'insieme
- Il `-` tra caratteri definisce un intervallo; altrove e letterale

```python
# Separatori flessibili: virgola, punto e virgola, spazio o tab
re.split(r"[,;\s]+", "mela, pera;banana  kiwi")
# Output: ['mela', 'pera', 'banana', 'kiwi']

# Caratteri validi per un nome file
re.findall(r"[A-Za-z0-9._-]+", "file_01.txt e file-02.csv")
# Output: ['file_01.txt', 'file-02.csv']
```

---

#### Le Parentesi Graffe `{ }` — "Esattamente Quante Volte"

**Analogia:** Le parentesi graffe sono come le istruzioni di un ricetta: "aggiungi esattamente 3 cucchiai di sale, non 2, non 4 — 3."

```python
import re

# Esempio 1: esattamente n ripetizioni
testo = "aa aaa aaaa aaaaa"
print(re.findall(r"a{3}", testo))    # ['aaa', 'aaa', 'aaa']
# Trova tutte le sequenze di esattamente 3 'a' (puo essere dentro parole piu lunghe)

# Esempio 2: range di ripetizioni {n,m}
# Codice postale USA: 5 cifre obbligatorie, con estensione opzionale di 4 cifre
codici = ["12345", "1234", "123456789", "12345-6789"]
for c in codici:
    if re.fullmatch(r"\d{5}(-\d{4})?", c):
        print(f"  Valido: {c}")
    else:
        print(f"  Non valido: {c}")
# Valido: 12345
# Non valido: 1234      (troppo corto)
# Non valido: 123456789 (troppo lungo)
# Valido: 12345-6789

# Esempio 3: almeno n ripetizioni {n,}
testo = "a aa aaa aaaa aaaaa"
print(re.findall(r"\ba{3,}\b", testo))  # ['aaa', 'aaaa', 'aaaaa']
# \b = confine di parola (ne parleremo presto)
```

---

### A.3 Classi di Caratteri Predefinite

Python fornisce scorciatoie per le classi di caratteri piu comuni. Invece di scrivere `[0-9]` ogni volta, puoi scrivere `\d`.

#### Tabella mnemonica completa

| Classe | Significato | Equivalente | Come ricordarlo |
|--------|-------------|-------------|-----------------|
| `\d` | Cifra decimale | `[0-9]` | **d**igit |
| `\D` | NON cifra | `[^0-9]` | **D**igit negato (maiuscola = negazione) |
| `\w` | Carattere "word" | `[a-zA-Z0-9_]` | **w**ord character |
| `\W` | NON word character | `[^a-zA-Z0-9_]` | **W**ord negato |
| `\s` | Spazio bianco | `[ \t\n\r\f\v]` | **s**pace |
| `\S` | NON spazio bianco | `[^ \t\n\r\f\v]` | **S**pace negato |
| `\b` | Confine di parola | (posizione) | **b**oundary |
| `\B` | NON confine di parola | (posizione) | **B**oundary negato |

**La regola d'oro:** lettera minuscola = classe positiva, lettera maiuscola = negazione.

#### Esempi pratici per ogni classe

```python
import re

# --- \d e \D ---
testo = "Ordine #4521 del 15/03/2025, totale: 99.90 euro"

# \d+ → sequenze di cifre
cifre = re.findall(r"\d+", testo)
print(f"Cifre trovate: {cifre}")
# Output: ['4521', '15', '03', '2025', '99', '90']

# \D+ → tutto tranne le cifre
non_cifre = re.findall(r"\D+", testo)
print(f"Non-cifre: {non_cifre}")
# Output: ['Ordine #', ' del ', '/', '/', ', totale: ', '.', ' euro']

# --- \w e \W ---
testo = "nome_utente = 'Mario_2025'"

# \w+ → parole (alfanumerici + underscore)
parole = re.findall(r"\w+", testo)
print(f"Parole: {parole}")
# Output: ['nome_utente', 'Mario_2025']

# \W+ → non-parole (punteggiatura, spazi)
separatori = re.findall(r"\W+", testo)
print(f"Separatori: {separatori}")
# Output: [' = ', "'", "'"]

# --- \s e \S ---
testo = "   colonne\tseparate\tda\ttab   "

# Pulizia degli spazi: dividi per qualsiasi spazio bianco
parti = re.split(r"\s+", testo.strip())
print(f"Parti: {parti}")
# Output: ['colonne', 'separate', 'da', 'tab']

# Tutto tranne spazi
non_spazi = re.findall(r"\S+", testo)
print(f"Non-spazi: {non_spazi}")
# Output: ['colonne', 'separate', 'da', 'tab']
```

#### Il Word Boundary `\b` — Confine di Parola

`\b` non cattura caratteri — e una **posizione** tra un carattere `\w` e un carattere `\W` (o l'inizio/fine della stringa). Serve per trovare parole intere.

```python
import re

testo = "era primavera e c'era una volta"

# Senza \b: trova "era" ovunque, anche dentro "primavera" e "c'era"
print(re.findall(r"era", testo))
# Output: ['era', 'era', 'era']
#                  ^^^              ^^^   ^^^
#          parola  dentro  c'era  parola

# Con \b: trova solo "era" come parola intera
print(re.findall(r"\bera\b", testo))
# Output: ['era', 'era']
#          inizio  c'era   ← la ' conta come confine di parola!

# Spiegazione visiva:
# "era"     → \b[era]\b → parola intera: MATCH
# "primavera" → non ha \b prima di "era" → NO MATCH (era e dentro la parola)
# "c'era"   → la ' e \W, quindi c'e \b prima di "era" → MATCH
```

```python
# Caso pratico: cercare la parola "log" senza catturare "login", "logout"
testo_log = "Scrivo nel log, poi mi logout e la login fallisce"
print(re.findall(r"\blog\b", testo_log))
# Output: ['log'] — solo "log" da solo, non "login" o "logout"
```

---

### A.4 Quantificatori — Quante Volte?

I quantificatori controllano quante volte un elemento deve ripetersi nel pattern.

#### Tabella riepilogativa

| Quantificatore | Significato | Esempio |
|----------------|-------------|---------|
| `*` | Zero o piu volte | `ab*c` → ac, abc, abbc... |
| `+` | Una o piu volte | `ab+c` → abc, abbc... (non ac) |
| `?` | Zero o una volta | `colou?r` → color, colour |
| `{n}` | Esattamente n volte | `\d{4}` → 1990, 2025 |
| `{n,}` | Almeno n volte | `\d{2,}` → 12, 123, 1234... |
| `{n,m}` | Da n a m volte | `\d{2,4}` → 12, 123, 1234 |

#### Greedy vs Lazy — Il Cuore del Problema

Per default, tutti i quantificatori sono **greedy** (golosi): cercano di catturare la quantita **massima** possibile di testo. Aggiungendo `?` dopo un quantificatore, lo si rende **lazy** (pigro): cattura la quantita **minima**.

**Analogia:** Immagina una lunga tavola di cibo. Il quantificatore greedy e il commensale che riempie il piatto il piu possibile, dal primo all'ultimo boccone disponibile. Il lazy e quello che prende solo il minimo indispensabile e si ferma.

```
GREEDY → cattura da QUI     fino a LAGGIUU (il massimo possibile)
LAZY   → cattura da QUI fino a LI (il minimo necessario)
```

```python
import re

html = "<b>grassetto</b> e <i>corsivo</i>"

# GREEDY: .+ cattura il massimo possibile
# Parte dall'apertura '<' e va avanti fino all'ultimo '>' che trova
greedy = re.findall(r"<.+>", html)
print(f"Greedy: {greedy}")
# Output: ['<b>grassetto</b> e <i>corsivo</i>']
# Ha catturato TUTTO dall'apertura alla chiusura finale!

# LAZY: .+? cattura il minimo necessario
# Si ferma al primo '>' che incontra
lazy = re.findall(r"<.+?>", html)
print(f"Lazy:   {lazy}")
# Output: ['<b>', '</b>', '<i>', '</i>']
# Ha trovato ogni tag singolarmente!
```

**Visualizzazione passo per passo del greedy:**

```
Testo:   < b > g r a s s e t t o < / b > _ e _ < i > c o r s i v o < / i >
Pattern: < . + >

Il motore prova:
1. < corrisponde a '<'
2. .+ inizia a mangiare tutto: b>grassetto</b> e <i>corsivo</i>
3. Cerca '>' → non trovato alla fine
4. BACKTRACK di 1: .+ rilascia l'ultimo carattere
5. Continua finche trova '>' nell'ultima posizione
6. MATCH: l'intera stringa tra il primo '<' e l'ultimo '>'
```

**Visualizzazione del lazy:**

```
Pattern: < . + ? >

1. < corrisponde a '<'
2. .+? prende il minimo: 'b'
3. Cerca '>' → trovato! MATCH: '<b>'
4. Ricomincia dalla posizione successiva
5. Ripete per ogni tag
```

```python
import re

# Altri esempi greedy vs lazy:

# {n,m} greedy vs {n,m}?
testo = "12345"
print(re.findall(r"\d{2,4}", testo))    # Greedy: ['1234'] (prende 4)
print(re.findall(r"\d{2,4}?", testo))  # Lazy:   ['12', '34'] (prende 2)

# * greedy vs *?
testo = '"primo" qualcosa "secondo"'
print(re.findall(r'".*"', testo))    # Greedy: ['"primo" qualcosa "secondo"']
print(re.findall(r'".*?"', testo))   # Lazy:   ['"primo"', '"secondo"']

# Caso pratico: estrarre il contenuto di tag specifici
html = "<div>primo</div> testo <div>secondo</div>"
print(re.findall(r"<div>.*?</div>", html))
# Output: ['<div>primo</div>', '<div>secondo</div>']
# Il lazy e essenziale qui!
```

#### Riepilogo Visivo: Greedy vs Lazy

```
Quantificatore  Tipo      Comportamento
─────────────────────────────────────────────────
*               greedy    massimo possibile
*?              lazy      minimo possibile
+               greedy    massimo possibile (almeno 1)
+?              lazy      minimo possibile (almeno 1)
?               greedy    1 se possibile, poi 0
??              lazy      0 se possibile, poi 1
{n,m}           greedy    m se possibile, poi n
{n,m}?          lazy      n se possibile, poi m
```

#### Esercizio di Verifica A.4

**Problema:** Dato il testo `"Prezzo: €10, Sconto: €3, Totale: €7"`, usa una regex per estrarre solo i numeri dopo il simbolo `€`.

```python
import re
testo = "Prezzo: €10, Sconto: €3, Totale: €7"
# Scrivi il tuo pattern qui...
```

<details>
<summary>Soluzione (clicca per espandere)</summary>

```python
import re
testo = "Prezzo: €10, Sconto: €3, Totale: €7"

# Soluzione 1: con carattere letterale €
risultato = re.findall(r"€(\d+)", testo)
print(risultato)  # ['10', '3', '7']
# Le parentesi catturano solo il numero, non il simbolo €

# Soluzione 2: con lookbehind (anticipazione di B.6)
risultato = re.findall(r"(?<=€)\d+", testo)
print(risultato)  # ['10', '3', '7']
# (?<=€) significa "preceduto da €" senza catturarlo
```

</details>

---

## Conclusione del Blocco 1

In questo blocco hai imparato:

- Cos'e una regex e perche usare sempre `r"..."` (raw string)
- I 14 metacaratteri, ciascuno con analogia e 3+ esempi:
  - `.` (punto — qualsiasi carattere)
  - `*` (asterisco — zero o piu)
  - `+` (piu — uno o piu)
  - `?` (punto interrogativo — opzionale)
  - `^` (cappello — inizio stringa)
  - `$` (dollaro — fine stringa)
  - `|` (pipe — OR logico)
  - `\` (backslash — escape)
  - `( )` (parentesi tonde — raggruppa e cattura)
  - `[ ]` (parentesi quadre — insieme di caratteri)
  - `{ }` (parentesi graffe — conta le ripetizioni)
- Le classi predefinite `\d \w \s \D \W \S \b \B`
- La differenza fondamentale tra quantificatori greedy e lazy

Nel **Blocco 2** continueremo con le funzioni del modulo `re` (match, search, findall, finditer, sub, split), le flag, i gruppi avanzati (nominati, non catturanti) e i lookahead/lookbehind.

---

---

## Parte B — Il Modulo re in Profondita

---

### B.1 Le Funzioni Fondamentali

Python mette a disposizione sei funzioni principali nel modulo `re`. Le differenze tra loro sono sottili ma fondamentali per usarle correttamente.

```
re.match()     - Cerca il pattern SOLO all'inizio della stringa
re.search()    - Cerca la PRIMA occorrenza in qualsiasi posizione
re.fullmatch() - L'INTERA stringa deve corrispondere al pattern
re.findall()   - Restituisce UNA LISTA di tutte le corrispondenze
re.finditer()  - Restituisce un ITERATORE di Match object
```

**Analogia:** Immagina di cercare un oggetto in una stanza.
- `match` = guarda solo sulla porta d'ingresso
- `search` = cerca in tutta la stanza, si ferma al primo trovato
- `fullmatch` = verifica che TUTTA la stanza sia fatta di quell'oggetto
- `findall` = trova tutti gli oggetti di quel tipo e li mette in una lista
- `finditer` = ti da un elenco di istruzioni per trovare ogni oggetto uno alla volta

#### re.match() vs re.search() vs re.fullmatch()

```python
import re

testo = "Python 3.12 e fantastico"

# match(): SOLO all'inizio della stringa
re.match(r"Python", testo)       # Match - inizia con "Python"
re.match(r"fantastico", testo)   # None - non e all'inizio

# search(): in QUALSIASI posizione
re.search(r"Python", testo)      # Match
re.search(r"fantastico", testo)  # Match - trovato in mezzo

# fullmatch(): TUTTA la stringa deve corrispondere
re.fullmatch(r"\d+", "12345")    # Match
re.fullmatch(r"\d+", "12345abc") # None - il suffisso "abc" non rientra

# ATTENZIONE: match() non e sufficiente per validazione!
print(bool(re.match(r"\d{5}", "123456")))     # True! (match trova le prime 5)
print(bool(re.fullmatch(r"\d{5}", "123456"))) # False  (intera stringa deve matchare)
```

Accedere al Match object:

```python
import re

m = re.match(r"Python (\d+\.\d+)", "Python 3.12 e fantastico")
if m:
    print(f"Match completo: {m.group(0)}")   # Python 3.12
    print(f"Primo gruppo: {m.group(1)}")     # 3.12
    print(f"Posizione: {m.span()}")          # (0, 10)
```

#### re.findall() — Comportamento con Gruppi

Il comportamento di `findall` cambia in base ai gruppi presenti nel pattern. Questa distinzione e fondamentale e causa molti bug nei principianti.

```python
import re

testo = "Email: mario@test.it e luca@posta.com e anna@email.org"

# 0 gruppi: restituisce i match completi
print(re.findall(r"[a-z]+@[a-z]+\.[a-z]+", testo))
# Output: ['mario@test.it', 'luca@posta.com', 'anna@email.org']

# 1 gruppo: restituisce solo il contenuto del gruppo (non il match completo!)
print(re.findall(r"([a-z]+)@[a-z]+\.[a-z]+", testo))
# Output: ['mario', 'luca', 'anna']

# N gruppi: restituisce lista di tuple
print(re.findall(r"([a-z]+)@([a-z]+)\.([a-z]+)", testo))
# Output: [('mario', 'test', 'it'), ('luca', 'posta', 'com'), ('anna', 'email', 'org')]

# RIEPILOGO:
# 0 gruppi → lista di stringhe (i match completi)
# 1 gruppo → lista di stringhe (il contenuto del gruppo)
# N gruppi → lista di tuple (una per match, un elemento per gruppo)
```

#### re.finditer() — Match Object con Posizioni

```python
import re

testo = "Temperatura 22.5C alle 14:30, poi 18.3C alle 20:00"

# findall: solo i valori, senza posizione
print(re.findall(r"\d+\.\d+", testo))
# Output: ['22.5', '18.3']

# finditer: match object completi con posizioni e metadati
for match in re.finditer(r"\d+\.\d+", testo):
    print(f"Trovato '{match.group()}' tra posizione {match.start()} e {match.end()}")
# Trovato '22.5' tra posizione 12 e 16
# Trovato '18.3' tra posizione 34 e 38

# Preferisci finditer quando:
# 1. Il testo e molto grande (risparmia memoria)
# 2. Hai bisogno delle posizioni
# 3. Hai bisogno dei gruppi nominati per ogni match
```

#### Il Match Object — Tutte le Proprieta

```python
import re

testo = "Nome: Mario Rossi, Eta: 35 anni"
pattern = r"(?P<nome>[A-Z]\w+)\s+(?P<cognome>[A-Z]\w+),\s+Eta:\s+(?P<eta>\d+)"

m = re.search(pattern, testo)
if m:
    print(m.group())          # Match completo
    print(m.group(1))         # Primo gruppo: 'Mario'
    print(m.group("nome"))    # Per nome: 'Mario'
    print(m.group("cognome")) # Per nome: 'Rossi'
    print(m.groups())         # ('Mario', 'Rossi', '35')
    print(m.groupdict())      # {'nome': 'Mario', 'cognome': 'Rossi', 'eta': '35'}
    print(m.start())          # Indice inizio match
    print(m.end())            # Indice fine match (esclusivo)
    print(m.span())           # (inizio, fine) come tupla
    print(m.span("nome"))     # (inizio, fine) del gruppo "nome"
```

---

### B.2 re.sub — Sostituire con Pattern

Sintassi: `re.sub(pattern, replacement, string, count=0, flags=0)`

```python
import re

# Sostituzione semplice
testo = "Contattare il 333-1234567 oppure il 06-12345678"
print(re.sub(r"\d", "X", testo))
# Output: 'Contattare il XXX-XXXXXXX oppure il XX-XXXXXXXX'

# Limitare il numero di sostituzioni
print(re.sub(r"\d", "X", testo, count=5))
# Output: 'Contattare il XXX-XX34567 oppure il 06-12345678'

# Usare i GRUPPI nella sostituzione con \1, \2, ...
# Smontaggio del pattern r"(\d{4})-(\d{2})-(\d{2})":
#   (\d{4})  → gruppo 1: anno (4 cifre)
#   -        → trattino letterale
#   (\d{2})  → gruppo 2: mese (2 cifre)
#   -        → trattino letterale
#   (\d{2})  → gruppo 3: giorno (2 cifre)
date = "2025-03-15 e 2025-12-25"
print(re.sub(r"(\d{4})-(\d{2})-(\d{2})", r"\3/\2/\1", date))
# Output: '15/03/2025 e 25/12/2025'

# Gruppi nominati nella sostituzione: \g<nome>
email = "scrivi a mario@email.it e luca@posta.com"
print(re.sub(
    r"(?P<utente>\w+)@(?P<dominio>\w+\.\w+)",
    r"\g<utente> [at] \g<dominio>",
    email
))
# Output: 'scrivi a mario [at] email.it e luca [at] posta.com'
```

#### re.sub con Funzione di Callback

Il replacement puo essere una **funzione** che riceve il Match object e restituisce la stringa di sostituzione. Permette trasformazioni impossibili con stringhe statiche.

```python
import re

# Raddoppiare ogni numero
def doppio(match: re.Match) -> str:
    return str(int(match.group()) * 2)

print(re.sub(r"\d+", doppio, "Ho 3 gatti e 5 cani, in tutto 8 animali"))
# Output: 'Ho 6 gatti e 10 cani, in tutto 16 animali'

# Conversione gradi Fahrenheit -> Celsius
def f_to_c(match: re.Match) -> str:
    fahrenheit = float(match.group(1))
    celsius = (fahrenheit - 32) * 5 / 9
    return f"{celsius:.1f}C"

print(re.sub(r"(\d+(?:\.\d+)?)F", f_to_c, "Oggi 72F, domani 68F, massima 85F"))
# Output: 'Oggi 22.2C, domani 20.0C, massima 29.4C'

# re.subn(): come sub, ma restituisce anche il numero di sostituzioni
result, n = re.subn(r"\d+", "NUM", "abc123def456ghi789")
print(f"Risultato: {result}, Sostituzioni: {n}")
# Risultato: 'abcNUMdefNUMghiNUM', Sostituzioni: 3
```

---

### B.3 re.split — Dividere con Pattern

```python
import re

# Split su spazi multipli (tab, newline, spazi)
print(re.split(r"\s+", "parola1   parola2\tparola3\nparola4"))
# Output: ['parola1', 'parola2', 'parola3', 'parola4']

# Separatori multipli (virgola, punto e virgola, spazio)
print(re.split(r"[,;\s]+", "mela, pera; banana   kiwi"))
# Output: ['mela', 'pera', 'banana', 'kiwi']

# Includere il separatore nel risultato (con gruppo catturante)
print(re.split(r"(:+)", "uno:due::tre:::quattro"))
# Output: ['uno', ':', 'due', '::', 'tre', ':::', 'quattro']
# Il gruppo catturante include il separatore nella lista risultante

# Limitare il numero di split
print(re.split(r":", "uno:due:tre:quattro", maxsplit=2))
# Output: ['uno', 'due', 'tre:quattro']
```

---

### B.4 Flag — Modificatori di Comportamento

| Flag | Scorciatoia | Effetto |
|------|-------------|---------|
| `re.IGNORECASE` | `re.I` | Ignora maiuscole/minuscole |
| `re.MULTILINE` | `re.M` | `^` e `$` su ogni riga |
| `re.DOTALL` | `re.S` | `.` cattura anche newline |
| `re.VERBOSE` | `re.X` | Permette commenti nel pattern |
| `re.ASCII` | `re.A` | Classi solo ASCII |

```python
import re

# --- IGNORECASE ---
testo = "Python PYTHON python"
print(re.findall(r"python", testo, re.IGNORECASE))
# Output: ['Python', 'PYTHON', 'python']
# Inline equivalente: (?i)python

# --- MULTILINE ---
testo_ml = "# Titolo\nParagrafo.\n# Sottotitolo"
print(re.findall(r"^#.*$", testo_ml, re.MULTILINE))
# Output: ['# Titolo', '# Sottotitolo']
# Senza MULTILINE: solo ['# Titolo']

# --- DOTALL ---
html = "<div>\ncontenuto\nmultiriga\n</div>"
print(re.findall(r"<div>(.+)</div>", html, re.DOTALL))
# Output: ['\ncontenuto\nmultiriga\n']

# --- VERBOSE: pattern leggibili con commenti ---
EMAIL = re.compile(r"""
    ^                       # Inizio stringa
    [a-zA-Z0-9._%+-]+      # Parte locale: lettere, cifre, ._%+-
    @                       # Simbolo @ obbligatorio
    [a-zA-Z0-9.-]+         # Nome dominio
    \.                      # Punto prima del TLD
    [a-zA-Z]{2,}           # TLD (almeno 2 lettere)
    $                       # Fine stringa
""", re.VERBOSE)
print(bool(EMAIL.match("mario@esempio.it")))    # True
print(bool(EMAIL.match("non-una-email")))       # False

# --- Combinare flag con | ---
testo = "Python e\nPYTHON E\npython e"
print(re.findall(r"^python.+$", testo, re.M | re.I))
# Output: ['Python e', 'PYTHON E', 'python e']
```

---

### B.5 Gruppi di Cattura

#### Gruppi Non-Catturanti `(?:...)`

```python
import re

testo = "Visita https://example.com o ftp://files.it"

# PROBLEMA: con gruppo catturante, findall restituisce solo il protocollo
print(re.findall(r"(https?|ftp)://\S+", testo))
# Output: ['https', 'ftp']  — sbagliato!

# SOLUZIONE: con gruppo non-catturante (?:...)
print(re.findall(r"(?:https?|ftp)://\S+", testo))
# Output: ['https://example.com', 'ftp://files.it']  — corretto!

# Regola: usa (?:) quando raggruppi solo per struttura del pattern
#         usa ()  quando hai bisogno del contenuto catturato
```

#### Gruppi Nominati `(?P<nome>...)`

```python
import re

# Smontaggio del pattern con gruppi nominati:
# (?P<data>\d{4}-\d{2}-\d{2})  → gruppo "data"
# \s+                            → spazi
# (?P<ora>\d{2}:\d{2}:\d{2})   → gruppo "ora"
# \s+                            → spazi
# (?P<livello>...)               → gruppo "livello"
# \s+                            → spazi
# (?P<messaggio>.+)              → gruppo "messaggio"

log_pattern = re.compile(r"""
    (?P<data>\d{4}-\d{2}-\d{2})
    \s+
    (?P<ora>\d{2}:\d{2}:\d{2})
    \s+
    (?P<livello>DEBUG|INFO|WARNING|ERROR|CRITICAL)
    \s+
    (?P<messaggio>.+)
""", re.VERBOSE)

riga = "2025-03-15 10:30:00 ERROR Database non raggiungibile"
m = log_pattern.match(riga)
if m:
    entry = m.groupdict()
    print(f"[{entry['livello']}] {entry['data']}: {entry['messaggio']}")
    # [ERROR] 2025-03-15: Database non raggiungibile
```

#### Backreference `\1` e `(?P=nome)`

```python
import re

# Trova parole duplicate consecutive
testo = "il il gatto dorme dorme bene questa sera sera"
print(re.findall(r"\b(\w+)\s+\1\b", testo))
# Output: ['il', 'dorme', 'sera']

# Smontaggio di r"\b(\w+)\s+\1\b":
# \b     → confine di parola
# (\w+)  → gruppo 1: cattura una parola
# \s+    → spazi tra le due istanze
# \1     → STESSA parola catturata dal gruppo 1
# \b     → confine di parola

# (?P=nome) con verifica tag HTML
html = "<b>grassetto</b> <i>corsivo</i>"
for m in re.finditer(r"<(?P<tag>\w+)>.*?</(?P=tag)>", html):
    print(f"Tag '{m.group('tag')}': {m.group()}")
# Tag 'b': <b>grassetto</b>
# Tag 'i': <i>corsivo</i>
```

---

### B.6 Lookahead e Lookbehind

Le asserzioni lookaround sono **a larghezza zero**: verificano il contesto senza consumare caratteri.

```
Tipo                  Sintassi     Significato
---------------------------------------------------
Positive lookahead    (?=...)      "seguito da ..."
Negative lookahead    (?!...)      "NON seguito da ..."
Positive lookbehind   (?<=...)     "preceduto da ..."
Negative lookbehind   (?<!...)     "NON preceduto da ..."
```

```python
import re

# --- Positive lookahead (?=...) ---
# Trova numeri seguiti da "euro" senza catturare "euro"
testo = "Costa 50 euro, non 30 dollari ne 20 yen"
print(re.findall(r"\d+(?=\s+euro)", testo))
# Output: ['50']

# Validazione password con lookahead multipli
PWD = re.compile(r"""
    ^
    (?=.*[A-Z])          # Almeno una maiuscola
    (?=.*[a-z])          # Almeno una minuscola
    (?=.*\d)             # Almeno una cifra
    (?=.*[!@#$%^&*])    # Almeno un carattere speciale
    .{8,}
    $
""", re.VERBOSE)
print(bool(PWD.match("Sicura1!")))           # True
print(bool(PWD.match("senza_Numero!")))      # False

# --- Negative lookahead (?!...) ---
# Trova numeri NON seguiti da "px"
testo = "margin: 10px; padding: 20em; font: 14px"
print(re.findall(r"\b\d+(?!px)\b", testo))
# Output: ['20']  — '10' e '14' esclusi perche seguiti da 'px'

# --- Positive lookbehind (?<=...) ---
# Trova numeri preceduti da '$'
testo = "Prezzo: $100 e $250, quantita: 5"
print(re.findall(r"(?<=\$)\d+", testo))
# Output: ['100', '250']  — '5' escluso (non ha $ prima)

# --- Negative lookbehind (?<!...) ---
# Trova numeri NON preceduti da '$'
print(re.findall(r"(?<!\$)\b\d+\b", testo))
# Output: ['5']  — '100' e '250' esclusi (hanno $ prima)

# Combinare lookbehind e lookahead
# Contenuto tra parentesi senza le parentesi stesse
testo = "Questo (concetto) e (importante)"
print(re.findall(r"(?<=\()[\w\s]+(?=\))", testo))
# Output: ['concetto', 'importante']
```

**Limite di `re`:** il lookbehind richiede lunghezza **fissa** (no `*`, `+`, `{n,m}`).
Il modulo `regex` (terze parti, `pip install regex`) supera questa limitazione.

---

## Conclusione del Blocco 2

In questo blocco hai imparato:

- `match()` vs `search()` vs `fullmatch()` — quando usare quale
- Il comportamento critico di `findall()` con 0, 1 o N gruppi
- `finditer()` per grandi dataset con posizioni precise
- Il Match object: `group()`, `groups()`, `groupdict()`, `span()`
- `re.sub()` con stringa, riferimenti a gruppi e callback function
- `re.split()` con separatori variabili e inclusione del separatore
- Le 5 flag principali: I M S X A
- I tre tipi di gruppi: `()`, `(?:)`, `(?P<nome>)`
- Backreference numeriche `\1` e nominate `(?P=nome)`
- I quattro lookaround con esempi pratici

Nel **Blocco 3** entreremo nelle tecniche avanzate: precompilazione, motore NFA, ReDoS, unicodedata, difflib e fuzzy matching.

---


---

## Parte C — Tecniche Avanzate

---

### C.1 re.compile e Precompilazione

#### Quando e Perche Compilare

`re.compile()` trasforma una stringa pattern in un **oggetto regex compilato**. Questo oggetto ha gli stessi metodi delle funzioni del modulo `re` (match, search, findall, ecc.), ma il pattern e gia compilato in bytecode.

**Quando usarlo:**
1. Il pattern e usato **piu di una volta** (loop, funzione ripetuta)
2. Vuoi dare un **nome significativo** al pattern
3. Vuoi specificare le **flag una volta sola**
4. Vuoi che il pattern sia una **costante a livello di modulo**

```python
import re

# ANTI-PATTERN: ri-compila ogni volta (anche se la cache di re mitiga il costo)
def cerca_errori_lento(righe: list) -> list:
    risultati = []
    for riga in righe:
        # re.search() internamente compila (o recupera dalla cache)
        if re.search(r"ERROR\s+\d+:\s+(.+)", riga):
            risultati.append(riga)
    return risultati

# PATTERN CORRETTO: compila una volta, riusa molte volte
PATTERN_ERRORE = re.compile(r"ERROR\s+\d+:\s+(.+)")

def cerca_errori_veloce(righe: list) -> list:
    # PATTERN_ERRORE.search() usa l'oggetto gia compilato
    return [riga for riga in righe if PATTERN_ERRORE.search(riga)]
```

#### L'Oggetto Compilato — Tutte le Proprieta

```python
import re

pattern = re.compile(r"(?P<utente>[a-z]+)@(?P<dominio>[a-z]+)\.(?P<tld>[a-z]{2,})",
                     re.IGNORECASE)

# Stessi metodi del modulo re
pattern.match("mario@test.it")
pattern.search("email: mario@test.it fine")
pattern.findall("mario@test.it e luca@posta.com")
pattern.finditer("mario@test.it e luca@posta.com")
pattern.sub(r"\g<utente> [at] \g<dominio>", "mario@test.it")
pattern.split("before@sep.com after")

# Proprieta informative
print(pattern.pattern)    # Il pattern originale come stringa
print(pattern.flags)      # Le flag attive come intero
print(pattern.groups)     # Numero di gruppi: 3
print(pattern.groupindex) # {'utente': 1, 'dominio': 2, 'tld': 3}
```

#### Organizzare i Pattern nel Progetto

Per progetti reali, crea un file `patterns.py` che centralizza tutti i pattern:

```python
# patterns.py — costanti regex del progetto

import re

# Validazione input utente
EMAIL = re.compile(
    r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
)
CODICE_FISCALE = re.compile(
    r"^[A-Z]{6}\d{2}[ABCDEHLMPRST]\d{2}[A-Z]\d{3}[A-Z]$",
    re.IGNORECASE
)
PARTITA_IVA = re.compile(r"^\d{11}$")
IBAN_IT = re.compile(
    r"^IT\d{2}[A-Z]\d{10}[A-Z0-9]{12}$",
    re.IGNORECASE
)

# Parsing log applicativo
LOG_STANDARD = re.compile(
    r"(?P<data>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+"
    r"(?P<livello>DEBUG|INFO|WARNING|ERROR|CRITICAL)\s+"
    r"\[(?P<sorgente>[^\]]+)\]\s+"
    r"(?P<messaggio>.+)"
)

# Estrazione dati
URL = re.compile(
    r"https?://[^\s<>\"']+(?:\([^\s<>\"']*\))*[^\s<>\"'.,;:!?)\]]"
)
IPV4 = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}"
    r"(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"
)
```

**Nota sulla cache di `re`:** il modulo `re` mantiene una LRU cache dei pattern compilati recentemente (fino a 512 pattern in Python 3.12+). Quindi le funzioni come `re.search(r"pattern", testo)` non ricompilano il pattern ad ogni chiamata. Tuttavia, la precompilazione esplicita e preferibile perche:
- E piu chiara nelle intenzioni
- L'oggetto non subisce eviction dalla cache
- Permette di specificare le flag in modo visibile

---

### C.2 Il Motore NFA e il Backtracking

#### Cos'e un NFA

Il modulo `re` di Python usa un motore **NFA (Non-deterministic Finite Automaton) con backtracking**. Per capire perche questo e importante, serve capire come funziona il matching.

**Analogia del labirinto:** Immagina il testo come un labirinto e la regex come le istruzioni per navigarlo. Il motore NFA e come un esploratore che:
1. Sceglie un percorso al primo bivio
2. Va avanti finche puo
3. Se incontra un vicolo cieco, **torna indietro** (backtrack) all'ultimo bivio
4. Prova il percorso alternativo
5. Ripete finche trova l'uscita (match) o esaurisce tutte le strade (no match)

```python
import re

# Visualizzazione del backtracking
# Pattern: r"(a|ab)c"
# Input: "abc"

# Passo 1: il motore prova "a" (prima alternativa)
#   - Corrisponde alla 'a' di "abc"
#   - Cerca ora 'c': trova 'b', fallisce
# Passo 2: BACKTRACK — torna all'inizio del gruppo
#   - Prova "ab" (seconda alternativa)
#   - Corrisponde a "ab"
#   - Cerca ora 'c': trova 'c', successo!

m = re.search(r"(a|ab)c", "abc")
print(m.group())   # 'abc'
print(m.group(1))  # 'ab' — la seconda alternativa ha vinto
```

#### NFA vs DFA — La Differenza Cruciale

| Caratteristica | NFA (Python `re`) | DFA (`re2`, `grep -E`) |
|---|---|---|
| Backtracking | Si | No |
| Backreference (`\1`) | Supportate | Non supportate |
| Lookahead/Lookbehind | Supportati | Non supportati |
| Complessita peggiore | O(2^n) — esponenziale | O(n) — lineare |
| Cattura gruppi | Si | Limitata |

Python ha scelto NFA perche supporta tutte le funzionalita avanzate. Il prezzo e che pattern mal costruiti possono avere comportamenti esponenziali su certi input.

#### Come il Backtracking Funziona — Esempio Dettagliato

```python
import re

testo = "aabab"
pattern = re.compile(r"a*b")

# Il motore tenta di fare match partendo da posizione 0:
# 1. a* (greedy): cattura 'aa' (il massimo possibile)
# 2. Cerca 'b': trova 'b' — MATCH! 'aab' a posizione 0-3
#
# Poi cerca dalla posizione 3:
# 1. a* : cattura 'a' (greedy)
# 2. Cerca 'b': trova 'b' — MATCH! 'ab' a posizione 3-5

print(re.findall(r"a*b", testo))  # ['aab', 'ab']

# Con un pattern piu complesso:
# Il backtracking e essenziale per trovare il match corretto
m = re.search(r"a+b+", "aaabbb ciao")
# a+ cattura 'aaa', b+ cattura 'bbb' — match immediato, poco backtracking

m = re.search(r"a+b*a", "aaaa")
# a+ cattura 'aaaa' (greedy), b* cattura '' (zero b), cerca 'a' — fallisce
# BACKTRACK: a+ rilascia un 'a', ora cattura 'aaa'
# b* cattura '', cerca 'a' — trova 'a'! MATCH: 'aaaa'? no, ricontrolla...
# Questo processo si ripete...
```

---

### C.3 ReDoS — Attacchi alle Regex

#### Cos'e il ReDoS

Il **ReDoS (Regular Expression Denial of Service)** e un attacco che sfrutta il backtracking catastrofico: un input appositamente costruito causa un numero **esponenziale** di tentativi di backtracking, bloccando il programma per secondi, minuti, o anche ore.

**Quando si verifica:**
1. Pattern con **quantificatori annidati**: `(a+)+`
2. Pattern con **alternative sovrapposte**: `(\w+|\d+)+`
3. L'input **non corrisponde** al pattern, forzando il motore a esplorare tutte le combinazioni

```python
import re
import time

# PATTERN PERICOLOSO: quantificatori annidati
# (a+)+ su input "aaaaaaaaaaaaaaaaaX" causa backtracking esponenziale
pattern = re.compile(r"^(a+)+$")

# Misura il tempo con input crescente
for n in [10, 15, 20, 22]:
    input_str = "a" * n + "X"  # non corrisponde (c'e una X finale)
    inizio = time.perf_counter()
    pattern.search(input_str)
    durata = time.perf_counter() - inizio
    print(f"n={n:2d}: {durata:.4f}s")
    if durata > 3.0:
        print("  TROPPO LENTO — crescita esponenziale!")
        break

# Output tipico:
# n=10: 0.0001s
# n=15: 0.0030s
# n=20: 0.0900s
# n=22: 0.3600s  <- cresce esponenzialmente!
```

#### Perche `(a+)+` e Catastrofico

**Spiegazione visiva:** per la stringa "aaX" (3 lettere 'a' poi 'X'):

```
Il pattern (a+)+ puo matchare "aaa" in molti modi diversi:
- (a)(a)(a)       — tre gruppi da 1
- (a)(aa)         — un gruppo da 1, uno da 2
- (aa)(a)         — un gruppo da 2, uno da 1
- (aaa)           — un gruppo da 3

Per n 'a', ci sono 2^(n-1) modi diversi!
Con n=20: 2^19 = 524.288 combinazioni da provare se il match fallisce
Con n=30: 2^29 = 536.870.912 combinazioni — piu di mezzo miliardo!
```

#### Pattern Vulnerabili — Elenco Completo

```python
# TUTTI QUESTI PATTERN SONO VULNERABILI a ReDoS:

# 1. Quantificatori annidati
r"(a+)+"           # a+ ripetuto con +
r"(a*)*"           # a* ripetuto con *
r"(a+)*"           # a+ ripetuto con *
r"(a|b+)+"         # alternativa con quantificatore annidato

# 2. Alternative sovrapposte (le alternative condividono caratteri)
r"(a|a)+"          # entrambe matchano 'a'
r"(\w+|\d+)+"      # \d e sottoinsieme di \w — overlap!
r"(\w|\w\w)+"      # entrambe matchano caratteri word

# 3. Pattern email naive molto diffuso (PERICOLOSO in produzione!)
r"^([a-zA-Z0-9]+\.)+[a-zA-Z]{2,}$"

# 4. Sequenze sovrapposte
r"(\w+\s+)+\w+"    # parole separate da spazi — vulnerabile se l'input non finisce con \w
```

#### Come Evitare il ReDoS

**Strategia 1: Riformulare il Pattern**

```python
import re

# VULNERABILE
# re.compile(r"(a+)+$")

# SICURO: rimuovere i quantificatori annidati
re.compile(r"a+$")   # equivalente, senza backtracking catastrofico

# VULNERABILE
# re.compile(r"(\w+|\d+)+")

# SICURO: usare classi di caratteri invece di alternative sovrapposte
re.compile(r"\w+")   # equivalente, molto piu efficiente

# VULNERABILE — pattern email naive
# re.compile(r"^([a-zA-Z0-9]+\.)+[a-zA-Z]{2,}$")

# PIU SICURO — classi di caratteri specifiche senza ambiguita
EMAIL_SICURO = re.compile(
    r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
)
```

**Strategia 2: Limitare la Lunghezza dell'Input**

```python
import re

MAX_LUNGHEZZA_EMAIL = 254  # RFC 5321

def valida_email_sicuro(email: str) -> bool:
    """Validazione email sicura contro ReDoS."""
    # Passo 1: controlla la lunghezza PRIMA di applicare la regex
    if len(email) > MAX_LUNGHEZZA_EMAIL:
        return False

    # Passo 2: usa un pattern non vulnerabile
    pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    return bool(pattern.match(email))
```

**Strategia 3: Usare `re2` per Input Non Fidato**

```python
# pip install google-re2
import re2  # motore DFA: tempo lineare, immune a ReDoS

# re2 ha API compatibile con re
pattern = re2.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
match = pattern.search("mario@test.it")

# re2 non supporta backreference e lookaround,
# ma per filtraggio di input non fidato e la scelta migliore
```

**Strategia 4: Atomic Groups / Possessive Quantifiers (modulo `regex`)**

```python
import regex  # pip install regex

# Atomic group (?>...): una volta fatto match, non rilascia MAI
# Equivale a un possessive quantifier
pattern_atomico = regex.compile(r"(?>a+)b")
# Con "aaab": a+ cattura "aaa", cerca 'b' trova 'b' — MATCH
# Ma "aab" NON fa backtrack — atomic group blocca il rilascio

# Possessive quantifier *+ ++: non rilascia mai caratteri
pattern_possessive = regex.compile(r"a++b")
# Equivalente all'atomic group ma piu conciso

# Questi eliminano il backtracking catastrofico alla radice
```

#### Tabella di Diagnosi Rapida

```
Vedi nel tuo pattern...    Rischio ReDoS?   Soluzione
-----------------------------------------------------------
(a+)+                      ALTO             a+
(a*)*                      ALTO             a*
(\w+|\d+)+                 ALTO             \w+
(.+)*                      ALTO             .+
([a-z]+\.)+                MEDIO-ALTO       [a-z.]+
\w+\s+\w+\s+               BASSO            OK per input breve
```

---

### C.4 unicodedata — Testo Internazionale

Il modulo `unicodedata` fornisce accesso al **Unicode Character Database (UCD)** — il catalogo ufficiale di tutti i caratteri Unicode, con le loro proprieta.

#### Funzioni Fondamentali

```python
import unicodedata

# name(): restituisce il nome ufficiale Unicode di un carattere
print(unicodedata.name("A"))        # 'LATIN CAPITAL LETTER A'
print(unicodedata.name("e"))        # 'LATIN SMALL LETTER E WITH ACUTE'
print(unicodedata.name("€"))        # 'EURO SIGN'
print(unicodedata.name("☃"))        # 'SNOWMAN'
print(unicodedata.name("a", "?"))   # 'LATIN SMALL LETTER A' (terzo arg = default)

# lookup(): trova un carattere dal suo nome Unicode
print(unicodedata.lookup("SNOWMAN"))    # '☃'
print(unicodedata.lookup("EURO SIGN"))  # '€'
print(unicodedata.lookup("LATIN SMALL LETTER A"))  # 'a'

# category(): restituisce la categoria Unicode del carattere
print(unicodedata.category("A"))   # 'Lu'  (Letter, uppercase)
print(unicodedata.category("a"))   # 'Ll'  (Letter, lowercase)
print(unicodedata.category("1"))   # 'Nd'  (Number, decimal digit)
print(unicodedata.category(" "))   # 'Zs'  (Separator, space)
print(unicodedata.category("!"))   # 'Po'  (Punctuation, other)
print(unicodedata.category("\n"))  # 'Cc'  (Other, control)
```

#### Tabella delle Categorie Unicode Principali

| Codice | Significato | Esempio |
|--------|-------------|---------|
| `Lu` | Letter, uppercase | A, B, Z |
| `Ll` | Letter, lowercase | a, b, z |
| `Lt` | Letter, titlecase | Dz (forma mista) |
| `Nd` | Number, decimal digit | 0-9, cifre arabe |
| `Zs` | Separator, space | spazio, no-break space |
| `Po` | Punctuation, other | ! . , ; |
| `Pc` | Punctuation, connector | _ |
| `Mn` | Mark, non-spacing | accento combinante |
| `Cc` | Other, control | \n \t \r |

#### Normalizzazione Unicode

Lo stesso carattere visivo puo avere rappresentazioni diverse in Unicode. La normalizzazione risolve questo problema.

```python
import unicodedata

# La lettera "e" puo essere:
# 1. Un singolo code point U+00E9 (forma precomposta)
precomposta = "é"     # 'e' con accento

# 2. Due code point: 'e' + accento combinante U+0301
decomposta = "é"     # 'e' + combining acute accent

# Visivamente identiche ma diversi internamente:
print(f"Visive: {precomposta} == {decomposta}")     # e == e (visivo uguale)
print(f"Uguali: {precomposta == decomposta}")        # False!
print(f"Lunghezza precomposta: {len(precomposta)}")  # 1
print(f"Lunghezza decomposta: {len(decomposta)}")    # 2

# NFC — Canonical Decomposition followed by Canonical Composition
# Produce la forma precomposta (una sola code point per carattere base + accento)
nfc = unicodedata.normalize("NFC", decomposta)
print(f"NFC == precomposta: {nfc == precomposta}")   # True

# NFD — Canonical Decomposition
# Produce la forma decomposta (separato il carattere base dall'accento)
nfd = unicodedata.normalize("NFD", precomposta)
print(f"NFD == decomposta: {nfd == decomposta}")     # True

# REGOLA D'ORO: normalizza sempre in NFC prima di confrontare stringhe
def confronta_unicode(s1: str, s2: str) -> bool:
    return unicodedata.normalize("NFC", s1) == unicodedata.normalize("NFC", s2)
```

#### Rimuovere Accenti (Uso Pratico Molto Comune)

```python
import unicodedata

def rimuovi_accenti(testo: str) -> str:
    """Rimuove accenti e diacritici mantenendo le lettere base.
    
    Funziona per tutte le lingue con accenti (italiano, francese, spagnolo...).
    """
    # Passo 1: NFD decompone i caratteri (base + combining marks separati)
    decomposto = unicodedata.normalize("NFD", testo)
    
    # Passo 2: rimuovi solo i combining marks (categoria 'Mn')
    # 'Mn' = Mark, non-spacing (gli accenti combinanti)
    return "".join(c for c in decomposto if unicodedata.category(c) != "Mn")

# Test con parole italiane
test = ["cafe", "citta", "eta", "perche", "pieta", "gia", "piu"]
for parola in test:
    print(f"  {parola} -> {rimuovi_accenti(parola)}")
# cafe -> cafe
# citta -> citta
# eta -> eta
# perche -> perche

# Uso pratico: generare slug URL da titoli con accenti
def genera_slug(testo: str) -> str:
    """Genera uno slug URL-safe da testo italiano."""
    import re
    # 1. Rimuovi accenti
    senza_accenti = rimuovi_accenti(testo)
    # 2. Minuscolo
    minuscolo = senza_accenti.lower()
    # 3. Sostituisci tutto cio che non e alfanumerico con trattino
    slug = re.sub(r"[^a-z0-9]+", "-", minuscolo)
    # 4. Rimuovi trattini iniziali/finali
    return slug.strip("-")

print(genera_slug("Citta e Regioni d'Italia: Guida Completa"))
# citta-e-regioni-d-italia-guida-completa
```

#### Normalizzazione NFKC — Compatibilita

NFKC va oltre NFC: converte anche varianti tipografiche (apici, pedici, larghezza piena, legature) nel loro equivalente standard.

```python
import unicodedata

# Esempi di NFKC
esempi = [
    ("Hello", "Hello (larghezza piena -> ASCII)"),
    ("2",     "2 (cifra a pedice -> normale)"),
    ("fi",    "fi (ligatura fi -> f+i)"),
    ("½","1/2 (frazione -> caratteri separati)"),
]

for originale, descrizione in esempi:
    nfkc = unicodedata.normalize("NFKC", originale)
    print(f"  '{originale}' -> '{nfkc}' ({descrizione})")

# ATTENZIONE: NFKC e "lossy" — perde informazione tipografica
# Usala solo quando la perdita e accettabile (ricerca, slug, confronto)
```

#### Rilevamento Testo Sospetto (Sicurezza)

```python
import unicodedata

def contiene_omoglifi(testo: str) -> bool:
    """Rileva se il testo mescola script diversi (potenziale IDN homograph attack).
    
    Gli attaccanti usano caratteri cirillici visivamente identici a quelli latini
    per creare nomi utente o URL che sembrano legittimi.
    Esempio: 'pаypal.com' (la 'a' e cirillica!) vs 'paypal.com'
    """
    scripts_trovati = set()
    for c in testo:
        cat = unicodedata.category(c)
        if cat.startswith("L"):  # solo lettere
            nome = unicodedata.name(c, "")
            script = nome.split()[0] if nome else "UNKNOWN"
            scripts_trovati.add(script)
    return len(scripts_trovati) > 1

print(contiene_omoglifi("paypal"))    # False — solo LATIN
print(contiene_omoglifi("pаypal"))    # True — 'а' e CYRILLIC!
# La 'a' cirillica (U+0430) e identica visivamente a 'a' latina (U+0061)
```

---

### C.5 difflib — Confrontare Testi

Il modulo `difflib` della libreria standard fornisce algoritmi per il confronto tra sequenze di testo — utilissimo per mostrare differenze tra versioni di file, implementare "fuzzy matching" base, e suggerire correzioni.

#### SequenceMatcher — Il Cuore di difflib

```python
import difflib

# Confronto tra due stringhe: quanto sono simili?
s1 = "abcdef"
s2 = "abcxef"

matcher = difflib.SequenceMatcher(None, s1, s2)
print(f"Similarita: {matcher.ratio():.2%}")   # 83.33%

# get_opcodes(): operazioni per trasformare s1 in s2
for tag, i1, i2, j1, j2 in matcher.get_opcodes():
    if tag == "equal":
        print(f"  UGUALE: '{s1[i1:i2]}'")
    elif tag == "replace":
        print(f"  SOSTITUISCI: '{s1[i1:i2]}' -> '{s2[j1:j2]}'")
    elif tag == "delete":
        print(f"  ELIMINA: '{s1[i1:i2]}'")
    elif tag == "insert":
        print(f"  INSERISCI: '{s2[j1:j2]}'")
# UGUALE: 'abc'
# SOSTITUISCI: 'd' -> 'x'
# UGUALE: 'ef'

# Confronto su liste di righe (tipico per confronto file)
righe1 = ["riga uno\n", "riga due\n", "riga tre\n"]
righe2 = ["riga uno\n", "riga MODIFICATA\n", "riga tre\n", "riga nuova\n"]

matcher2 = difflib.SequenceMatcher(None, righe1, righe2)
print(f"Similarita file: {matcher2.ratio():.2%}")  # 66.67%
```

#### unified_diff — Output in Formato Standard

```python
import difflib

v1 = ["alpha\n", "beta\n", "gamma\n", "delta\n"]
v2 = ["alpha\n", "BETA\n", "gamma\n", "epsilon\n", "delta\n"]

# unified_diff produce output identico a 'diff -u' Unix
diff = difflib.unified_diff(v1, v2,
                             fromfile="originale.txt",
                             tofile="modificato.txt",
                             n=2)  # 2 righe di contesto

print("".join(diff))
# --- originale.txt
# +++ modificato.txt
# @@ -1,4 +1,5 @@
#  alpha
# -beta
# +BETA
#  gamma
# +epsilon
#  delta

# Calcolare statistiche sul diff
def calcola_diff_stats(a: list, b: list) -> dict:
    matcher = difflib.SequenceMatcher(None, a, b)
    stats = {"inserite": 0, "rimosse": 0, "sostituite": 0, "invariate": 0}
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            stats["invariate"] += i2 - i1
        elif tag == "insert":
            stats["inserite"] += j2 - j1
        elif tag == "delete":
            stats["rimosse"] += i2 - i1
        elif tag == "replace":
            stats["sostituite"] += max(i2 - i1, j2 - j1)
    return stats

print(calcola_diff_stats(v1, v2))
# {'inserite': 1, 'rimosse': 0, 'sostituite': 1, 'invariate': 3}
```

#### get_close_matches — Suggerimenti di Correzione

```python
import difflib

# Trovare parole simili in una lista
parole_valide = ["python", "java", "javascript", "ruby", "rust", "go", "scala"]

# Parametri:
# word    → la parola da cercare
# possibilities → la lista in cui cercare
# n       → numero massimo di risultati (default: 3)
# cutoff  → soglia minima di similarita da 0.0 a 1.0 (default: 0.6)

print(difflib.get_close_matches("pythn", parole_valide, n=3, cutoff=0.6))
# Output: ['python']

print(difflib.get_close_matches("jav", parole_valide, n=3, cutoff=0.5))
# Output: ['java', 'javascript']

# Caso pratico: suggerire comandi quando l'utente digita male
COMANDI_VALIDI = ["install", "update", "remove", "search", "list", "info", "help"]

def suggerisci_comando(input_utente: str) -> str:
    suggerimenti = difflib.get_close_matches(
        input_utente, COMANDI_VALIDI, n=1, cutoff=0.6
    )
    if suggerimenti:
        return f"Forse intendevi '{suggerimenti[0]}'?"
    return "Comando non riconosciuto. Digita 'help' per la lista."

print(suggerisci_comando("instll"))   # "Forse intendevi 'install'?"
print(suggerisci_comando("updte"))    # "Forse intendevi 'update'?"
print(suggerisci_comando("xyz"))      # "Comando non riconosciuto..."
```

#### HtmlDiff — Confronto Visivo in HTML

```python
import difflib

v1 = ["Prima versione del testo\n", "Seconda riga invariata\n"]
v2 = ["Versione MODIFICATA del testo\n", "Seconda riga invariata\n"]

# Genera una pagina HTML con le differenze evidenziate
d = difflib.HtmlDiff()
html = d.make_file(v1, v2, fromdesc="Originale", todesc="Modificato")

# Salva su file per visualizzazione nel browser
with open("diff.html", "w", encoding="utf-8") as f:
    f.write(html)
print("Diff HTML generata in diff.html")
```

---

### C.6 Fuzzy Matching con rapidfuzz

Il fuzzy matching trova corrispondenze approssimate tra stringhe — fondamentale per correzione ortografica, deduplicazione dati, ricerca tollerante agli errori di battitura.

#### Installazione e Concetti Base

```python
# pip install rapidfuzz
from rapidfuzz import fuzz, process

# La distanza di Levenshtein conta le operazioni minime per trasformare
# una stringa nell'altra: inserzioni, delezioni, sostituzioni.
# Esempio: "cat" -> "car" = 1 sostituzione (t->r), distanza = 1
# Esempio: "cat" -> "cats" = 1 inserzione (s), distanza = 1
```

#### Le Funzioni Principali di rapidfuzz

```python
from rapidfuzz import fuzz

# --- ratio() --- 
# Similarita globale basata sulla distanza di Levenshtein
# Restituisce un valore da 0 (completamente diverso) a 100 (identico)
print(fuzz.ratio("mario rossi", "mario rossi"))    # 100.0 (identico)
print(fuzz.ratio("mario rossi", "mario rosi"))     # 95.24 (un errore)
print(fuzz.ratio("mario rossi", "luca bianchi"))   # 23.53 (molto diverso)

# --- partial_ratio() ---
# Cerca la stringa piu corta come sottostringa della piu lunga
# Utile quando una stringa e contenuta in un testo piu lungo
print(fuzz.partial_ratio("mario", "mario rossi avvocato"))   # 100.0
print(fuzz.ratio("mario", "mario rossi avvocato"))           # 42.11 (penalizza la lunghezza diversa)

# --- token_sort_ratio() ---
# Ordina le parole alfabeticamente prima di confrontare
# Utile per confrontare stringhe con parole nello stesso ordine diverso
print(fuzz.ratio("rossi mario", "mario rossi"))              # 50.0 (ordine diverso)
print(fuzz.token_sort_ratio("rossi mario", "mario rossi"))   # 100.0 (ordine irrilevante)

# --- token_set_ratio() ---
# Come token_sort_ratio ma gestisce anche parole ripetute e sottoinsiemi
print(fuzz.token_set_ratio("mario rossi avv.", "avv mario rossi"))  # 100.0
```

#### Quando Usare Quale Funzione

```
Funzione              Quando usarla
---------------------------------------------------------------------------
ratio()               Confronto diretto, stessa lunghezza attesa
partial_ratio()       Cerca una stringa dentro un testo piu lungo
token_sort_ratio()    Stesse parole ma ordine diverso (nomi propri)
token_set_ratio()     Parole in comune, possibili parole extra
```

#### process.extract() — Trovare i Migliori Match

```python
from rapidfuzz import process

# Lista di scelte valide
nomi = ["Mario Rossi", "Luca Bianchi", "Anna Verdi", "Marco Ferrari", "Sara Neri"]

# Cerca l'input "mrio rossi" (errore di battitura) nella lista
risultati = process.extract("mrio rossi", nomi, limit=3)
print(risultati)
# Output: [('Mario Rossi', 94.12, 0), ('Luca Bianchi', 52.17, 1), ...]
# Formato: (match, punteggio, indice)

# extractOne: restituisce solo il migliore
migliore = process.extractOne("mrio rossi", nomi)
print(migliore)  # ('Mario Rossi', 94.12, 0)

# Caso pratico: ricerca fuzzy in un catalogo prodotti
catalogo = [
    "Laptop Dell XPS 15",
    "MacBook Pro 14 pollici",
    "ThinkPad X1 Carbon",
    "HP EliteBook 840",
    "Asus ZenBook Pro",
]

def cerca_prodotto(query: str, soglia: int = 60) -> list:
    """Cerca prodotti con matching approssimato."""
    risultati = process.extract(query, catalogo, limit=3)
    return [(nome, score) for nome, score, _ in risultati if score >= soglia]

print(cerca_prodotto("laptop dell"))
# [('Laptop Dell XPS 15', 90.0), ...]

print(cerca_prodotto("macbok pro"))   # errore di battitura
# [('MacBook Pro 14 pollici', 83.3), ...]
```

#### Deduplicazione di Dataset con rapidfuzz

```python
from rapidfuzz import fuzz, process

# Dataset con duplicati e varianti
clienti = [
    "Mario Rossi",
    "mario rossi",      # uguale ma minuscolo
    "M. Rossi",         # abbreviazione
    "Rossi Mario",      # ordine inverso
    "Luca Bianchi",
    "L. Bianchi",
    "Luca Bianchi",     # duplicato esatto
]

def trova_duplicati(lista: list, soglia: int = 85) -> list:
    """Trova coppie di stringhe simili oltre la soglia."""
    duplicati = []
    for i, s1 in enumerate(lista):
        for j, s2 in enumerate(lista[i+1:], i+1):
            score = fuzz.token_set_ratio(s1.lower(), s2.lower())
            if score >= soglia:
                duplicati.append((s1, s2, score))
    return duplicati

for a, b, score in trova_duplicati(clienti, soglia=80):
    print(f"  '{a}' ~ '{b}' (score: {score:.0f})")
# 'Mario Rossi' ~ 'mario rossi' (score: 100)
# 'Mario Rossi' ~ 'Rossi Mario' (score: 100)
# 'Luca Bianchi' ~ 'Luca Bianchi' (score: 100)
```

---

### C.7 Pipeline di Text Processing

Una **pipeline di text processing** e una sequenza di trasformazioni applicate al testo in ordine. Ogni stadio prende l'output del precedente come input.

```
Input grezzo
    |
    v
[Normalizzazione Unicode] -- NFC, rimozione caratteri di controllo
    |
    v
[Pulizia HTML]            -- rimozione tag, entity decoding
    |
    v
[Normalizzazione testo]   -- minuscolo, spazi, punteggiatura
    |
    v
[Tokenizzazione]          -- divisione in parole/frasi
    |
    v
Output normalizzato
```

#### Implementazione della Pipeline

```python
import re
import unicodedata
import html


def fase_1_unicode(testo: str) -> str:
    """Normalizza la forma Unicode e rimuove caratteri di controllo."""
    # NFC: forma precomposta canonica
    testo = unicodedata.normalize("NFC", testo)
    # Rimuovi caratteri di controllo (categoria Cc) tranne spazi funzionali
    testo = "".join(
        c for c in testo
        if unicodedata.category(c) != "Cc" or c in "\n\r\t"
    )
    return testo


def fase_2_html(testo: str) -> str:
    """Rimuove tag HTML e decodifica entity HTML."""
    # Decodifica entity HTML: &amp; -> &, &lt; -> <, &#39; -> '
    testo = html.unescape(testo)
    # Rimuovi tag HTML
    testo = re.sub(r"<[^>]+>", " ", testo)
    return testo


def fase_3_normalizzazione(testo: str) -> str:
    """Normalizza spazi, trattini tipografici e apostrofi."""
    # Normalizza trattini tipografici
    testo = testo.replace("–", "-")   # en dash
    testo = testo.replace("—", "-")   # em dash
    # Normalizza apostrofi tipografici
    testo = testo.replace("‘", "'")   # left single quote
    testo = testo.replace("’", "'")   # right single quote
    # Comprimi spazi multipli
    testo = re.sub(r"\s+", " ", testo)
    return testo.strip()


def fase_4_tokenizza(testo: str) -> list:
    """Tokenizza il testo in parole e punteggiatura."""
    # Pattern che preserva:
    # - parole con apostrofi (l'uomo, don't)
    # - numeri con decimali
    # - punteggiatura singola
    pattern = re.compile(r"""
        \b\w+(?:'\w+)*\b   |   # parola (incluse contrazioni)
        \d+(?:[.,]\d+)?    |   # numero (intero o decimale)
        [^\w\s]                # punteggiatura
    """, re.VERBOSE | re.UNICODE)
    return pattern.findall(testo)


def processa_testo(testo_grezzo: str) -> list:
    """Pipeline completa di text processing."""
    testo = fase_1_unicode(testo_grezzo)
    testo = fase_2_html(testo)
    testo = fase_3_normalizzazione(testo)
    token = fase_4_tokenizza(testo)
    return token


# Test della pipeline
testo_sporco = """
<p>L&apos;uomo ha detto: &ldquo;Ciao&rdquo;&#33;</p>
<br/>Il prezzo – 50&euro; — e incluso.
"""

token = processa_testo(testo_sporco)
print("Token risultanti:")
print(token)
# ["L'uomo", 'ha', 'detto', ':', 'Ciao', '!', 'Il', 'prezzo', '-', '50',
#  '€', '-', 'e', 'incluso', '.']
```

---

## Conclusione del Blocco 3

In questo blocco hai imparato:

- `re.compile()`: quando e perche precompilare, come organizzare i pattern nel progetto
- Il motore NFA: il meccanismo del backtracking spiegato con l'analogia del labirinto
- ReDoS: i pattern pericolosi `(a+)+`, le strategie di difesa (riformulazione, limitazione input, re2, possessive quantifiers)
- `unicodedata`: name, category, normalize (NFC/NFD/NFKC), rimozione accenti, slug generation, rilevamento omoglifi
- `difflib`: SequenceMatcher, ratio, get_opcodes, unified_diff, get_close_matches
- `rapidfuzz`: ratio, partial_ratio, token_sort_ratio, process.extract per fuzzy matching
- Pipeline di text processing: normalizzazione Unicode, pulizia HTML, tokenizzazione

Nel **Blocco 4** troverai 10 esercizi pratici con soluzioni complete.

---


---

## Parte D — Esercizi Pratici

Dieci esercizi graduati dal piu semplice al piu complesso. Per ogni esercizio: prima prova a risolverlo da solo, poi leggi la soluzione guidata.

---

### Esercizio 1 — Validatore Email

**Obiettivo:** Scrivi una funzione `valida_email(email: str) -> bool` che validi un indirizzo email.

**Requisiti:**
- La parte locale puo contenere lettere, cifre, `.`, `_`, `%`, `+`, `-`
- Il simbolo `@` e obbligatorio e unico
- Il dominio puo contenere lettere, cifre, `.`, `-`
- Il TLD deve avere almeno 2 lettere
- Testa con almeno 5 casi validi e 5 invalidi

**Suggerimento:** usa `re.fullmatch()` per validare l'intera stringa.

```python
# Template (completa la funzione)
import re

def valida_email(email: str) -> bool:
    pattern = re.compile(r"""
        # scrivi il tuo pattern qui
    """, re.VERBOSE)
    return bool(pattern.fullmatch(email))

# Test
assert valida_email("mario.rossi@email.it"),          "email base valida"
assert valida_email("nome+tag@dominio.co.uk"),         "con + e doppio TLD"
assert valida_email("utente_01@posta.org"),            "con underscore"
assert not valida_email("senza-chiocciola.it"),        "manca @"
assert not valida_email("@manca-locale.it"),           "manca parte locale"
assert not valida_email("doppio@@dominio.it"),         "doppia @"
assert not valida_email("spazio nel mezzo@dom.it"),    "spazio nel mezzo"
assert not valida_email("solo-un-tld@dom.x"),          "TLD troppo corto"
print("Tutti i test superati!")
```

<details>
<summary>Soluzione</summary>

```python
import re

def valida_email(email: str) -> bool:
    """Valida un indirizzo email con regex VERBOSE."""
    pattern = re.compile(r"""
        ^                       # Inizio stringa
        [a-zA-Z0-9._%+-]+      # Parte locale: lettere, cifre, ._%+-
        @                       # Simbolo @ (uno e unico)
        [a-zA-Z0-9.-]+         # Dominio: lettere, cifre, ., -
        \.                      # Punto obbligatorio prima del TLD
        [a-zA-Z]{2,}           # TLD: almeno 2 lettere (.it, .com, .co.uk...)
        $                       # Fine stringa
    """, re.VERBOSE)
    return bool(pattern.fullmatch(email))

# Test completi
casi_validi = [
    "mario.rossi@email.it",
    "nome+tag@dominio.co.uk",
    "utente_01@posta.org",
    "a@b.it",
    "x.y.z@a.b.c.com",
]
casi_invalidi = [
    "senza-chiocciola.it",
    "@manca-locale.it",
    "doppio@@dominio.it",
    "spazio nel mezzo@dom.it",
    "solo-un-tld@dom.x",
]

for email in casi_validi:
    assert valida_email(email), f"Doveva essere valida: {email}"
    print(f"  OK valida: {email}")

for email in casi_invalidi:
    assert not valida_email(email), f"Doveva essere invalida: {email}"
    print(f"  OK invalida: {email}")

print("Tutti i test superati!")
```

**Smontaggio del pattern:**
```
^                   → inizio stringa (assicura match dal primo carattere)
[a-zA-Z0-9._%+-]+  → parte locale: uno o piu tra lettere, cifre e simboli permessi
@                   → simbolo @ letterale (obbligatorio)
[a-zA-Z0-9.-]+     → dominio: lettere, cifre, punto, trattino
\.                  → punto LETTERALE (non metacarattere) prima del TLD
[a-zA-Z]{2,}       → TLD: solo lettere, almeno 2
$                   → fine stringa (assicura match fino all'ultimo carattere)
```

</details>

---

### Esercizio 2 — Validatore Codice Fiscale Italiano

**Obiettivo:** Valida un Codice Fiscale italiano usando regex.

**Formato del CF:** `LLLLLLDDLDDLDDDA` (16 caratteri)
- 6 lettere (3 cognome + 3 nome)
- 2 cifre (anno di nascita)
- 1 lettera (mese: A=gen, B=feb, C=mar, D=apr, E=mag, H=giu, L=lug, M=ago, P=set, R=ott, S=nov, T=dic)
- 2 cifre (giorno di nascita, femmine: +40)
- 1 lettera + 3 cifre (codice catastale comune)
- 1 lettera (carattere di controllo)

```python
import re

def valida_cf(cf: str) -> bool:
    """Valida la struttura sintattica di un CF italiano."""
    # scrivi qui il tuo pattern
    pass

# Test
assert valida_cf("RSSMRA85M01H501Z")
assert valida_cf("rssmra85m01h501z")  # case-insensitive
assert not valida_cf("RSSMRA85X01H501Z")  # X non e un mese valido
assert not valida_cf("RSM1234567890Z")     # struttura sbagliata
print("Test CF superati!")
```

<details>
<summary>Soluzione</summary>

```python
import re

def valida_cf(cf: str) -> bool:
    """Valida la struttura sintattica di un CF italiano.
    
    Formato: LLLLLL DD L DD L DDD L
             cognome anno mese giorno comune ctrl
    
    Nota: non verifica la validita del carattere di controllo (richiederebbe
    algoritmo aggiuntivo non implementabile con sola regex).
    """
    pattern = re.compile(r"""
        ^
        [A-Z]{6}               # 6 lettere: 3 cognome + 3 nome
        \d{2}                  # Anno di nascita (2 cifre)
        [ABCDEHLMPRST]         # Mese: solo le lettere valide
                               # A=gen B=feb C=mar D=apr E=mag H=giu
                               # L=lug M=ago P=set R=ott S=nov T=dic
        \d{2}                  # Giorno: 01-31 (femmine: +40 = 41-71)
        [A-Z]\d{3}             # Codice catastale: 1 lettera + 3 cifre
        [A-Z]                  # Carattere di controllo
        $
    """, re.VERBOSE | re.IGNORECASE)
    
    return bool(pattern.match(cf))

# Test
casi_validi = [
    "RSSMRA85M01H501Z",   # Mario Rossi maschile
    "rssmra85m01h501z",   # case-insensitive
    "VRDLRA00A41D612X",   # Laura Verdi femminile (41 = 01 + 40)
]
casi_invalidi = [
    "RSSMRA85X01H501Z",   # X non e un mese valido
    "RSM1234567890Z",      # troppo corto e struttura sbagliata
    "12SMRA85M01H501Z",   # inizia con cifre invece di lettere
    "RSSMRA85M01H5010",   # cifra finale invece di lettera
]

for cf in casi_validi:
    assert valida_cf(cf), f"Doveva essere valido: {cf}"
    print(f"  OK valido: {cf}")

for cf in casi_invalidi:
    assert not valida_cf(cf), f"Doveva essere invalido: {cf}"
    print(f"  OK invalido: {cf}")
```

</details>

---

### Esercizio 3 — Validatore IBAN Italiano

**Obiettivo:** Valida un IBAN italiano con verifica del checksum ISO 7064.

**Formato IBAN IT:** `IT` + 2 cifre di controllo + 1 lettera (CIN) + 5 cifre (ABI) + 5 cifre (CAB) + 12 alfanumerici = 27 caratteri totali.

La funzione deve:
1. Accettare spazi tra gruppi (es. `IT60 X054 2811 ...`)
2. Verificare la struttura con regex
3. Verificare il checksum MOD 97 (algoritmo ISO 7064)

<details>
<summary>Soluzione</summary>

```python
import re

def valida_iban_it(iban: str) -> bool:
    """Valida un IBAN italiano con verifica struttura e checksum.
    
    Algoritmo checksum ISO 7064:
    1. Sposta le prime 4 caratteri alla fine
    2. Converti lettere in numeri: A=10, B=11, ..., Z=35
    3. Il numero risultante MOD 97 deve essere 1
    """
    # Normalizzazione: rimuovi spazi e converti in maiuscolo
    iban = iban.replace(" ", "").upper()
    
    # Passo 1: verifica struttura con regex
    # IT + 2 cifre + 1 LETTERA (CIN) + 5 cifre (ABI) + 5 cifre (CAB) + 12 alfanumerici
    pattern = re.compile(
        r"^IT"          # Paese: IT
        r"\d{2}"        # Check digits: 2 cifre
        r"[A-Z]"        # CIN: 1 lettera
        r"\d{5}"        # ABI: 5 cifre (codice banca)
        r"\d{5}"        # CAB: 5 cifre (codice filiale)
        r"[A-Z0-9]{12}" # Numero conto: 12 alfanumerici
        r"$"
    )
    if not pattern.match(iban):
        return False
    
    # Passo 2: verifica lunghezza (deve essere esattamente 27)
    if len(iban) != 27:
        return False
    
    # Passo 3: calcola checksum ISO 7064
    # Sposta prime 4 caratteri alla fine
    riordinato = iban[4:] + iban[:4]
    
    # Converti ogni carattere:
    # cifre rimangono cifre, lettere diventano numeri (A=10, B=11, ...)
    numerico = ""
    for c in riordinato:
        if c.isdigit():
            numerico += c
        else:
            numerico += str(ord(c) - ord("A") + 10)
    
    # Il numero risultante MOD 97 deve essere 1
    return int(numerico) % 97 == 1


# Test
iban_validi = [
    "IT60 X054 2811 1010 0000 0123 456",  # Con spazi
    "IT60X0542811101000000123456",          # Senza spazi
]
iban_invalidi = [
    "IT00X0542811101000000123456",  # Checksum errato
    "DE89370400440532013000",        # IBAN tedesco
    "IT60X054281110100000012345",    # Troppo corto (26 caratteri)
]

for iban in iban_validi:
    result = valida_iban_it(iban)
    print(f"  {'OK' if result else 'ERRORE'} valido: {iban}")

for iban in iban_invalidi:
    result = valida_iban_it(iban)
    print(f"  {'OK' if not result else 'ERRORE'} invalido: {iban}")
```

**Smontaggio del pattern:**
```
^IT           → la stringa deve iniziare con "IT"
\d{2}         → due cifre: check digits
[A-Z]         → una lettera: CIN (codice identificativo numerico)
\d{5}         → cinque cifre: ABI (codice banca)
\d{5}         → cinque cifre: CAB (codice filiale)
[A-Z0-9]{12}  → dodici caratteri alfanumerici: numero conto
$             → fine stringa
```

</details>

---

### Esercizio 4 — Validatore Targa Italiana

**Obiettivo:** Valida targhe italiane nei diversi formati storici.

**Formati:**
- Nuovo formato (dal 1994): 2 lettere + 3 cifre + 2 lettere (es. `AB123CD`)
- Vecchio formato (pre-1994): 2 lettere + 6 cifre (es. `MI123456`)
- Moto: 2 lettere + 5 cifre (es. `AB12345`)

<details>
<summary>Soluzione</summary>

```python
import re
from dataclasses import dataclass

@dataclass
class Targa:
    valida: bool
    formato: str
    targa_normalizzata: str

def valida_targa_it(targa: str) -> Targa:
    """Valida e classifica una targa italiana."""
    # Normalizzazione
    targa = targa.replace(" ", "").replace("-", "").upper()
    
    # Formato nuovo (1994 - oggi): AA 000 AA
    if re.fullmatch(r"[A-Z]{2}\d{3}[A-Z]{2}", targa):
        return Targa(True, "auto (nuovo, 1994+)", targa)
    
    # Formato vecchio (pre-1994): AA 000000 (2 lettere + 6 cifre)
    if re.fullmatch(r"[A-Z]{2}\d{6}", targa):
        return Targa(True, "auto (vecchio, pre-1994)", targa)
    
    # Moto: AA 00000 (2 lettere + 5 cifre)
    if re.fullmatch(r"[A-Z]{2}\d{5}", targa):
        return Targa(True, "motociclo", targa)
    
    return Targa(False, "non valida", targa)


# Test
targhe = [
    "AB123CD",    # nuovo formato
    "AB 123 CD",  # con spazi
    "MI123456",   # vecchio formato
    "AB12345",    # moto
    "1234ABC",    # invalida
    "ABCDEFG",    # invalida
    "AB12C",      # troppo corta
]

for t in targhe:
    result = valida_targa_it(t)
    stato = "Valida" if result.valida else "Non valida"
    print(f"  {stato} [{result.formato}]: '{t}' -> '{result.targa_normalizzata}'")
```

</details>

---

### Esercizio 5 — Estrattore URL da Testo

**Obiettivo:** Estrai tutti gli URL da un testo libero.

**Requisiti:**
- Supporta http, https, ftp
- Gestisce URL con path, query string e fragment
- Gestisce URL con parentesi bilanciate (wiki: `https://it.wikipedia.org/wiki/Ciao_(saluto)`)
- Non cattura punteggiatura finale (virgola, punto, punto esclamativo)

<details>
<summary>Soluzione</summary>

```python
import re

# Pattern URL che gestisce i casi edge comuni
URL_PATTERN = re.compile(r"""
    (?:https?|ftp)      # Protocollo: http, https, ftp
    ://                  # Separatore
    (?:
        [^\s<>\"'()\[\]]    # Caratteri validi nell'URL (esclusi alcuni delimitatori)
        |
        \(                  # Parentesi aperta
        [^\s<>\"'()\[\]]*   # Contenuto dentro parentesi
        \)                  # Parentesi chiusa
    )+                   # Uno o piu di questi
    (?<![.,;:!?'")\]])  # Lookbehind: non terminare con punteggiatura
""", re.VERBOSE)

def estrai_url(testo: str) -> list:
    """Estrae tutti gli URL da un testo."""
    return URL_PATTERN.findall(testo)


# Test
testo = """
Visita https://www.python.org per la documentazione ufficiale.
Guarda anche http://docs.python.org/3/library/re.html!
Wikipedia: https://it.wikipedia.org/wiki/Python_(linguaggio)
FTP: ftp://files.example.com/data/file.csv
Non e un URL: httpsnowhere.it
URL con query: https://search.example.com/q?term=python&lang=it#risultati
"""

urls = estrai_url(testo)
for url in urls:
    print(f"  -> {url}")
# -> https://www.python.org
# -> http://docs.python.org/3/library/re.html
# -> https://it.wikipedia.org/wiki/Python_(linguaggio)
# -> ftp://files.example.com/data/file.csv
# -> https://search.example.com/q?term=python&lang=it#risultati
```

**Smontaggio del lookbehind finale:**
```
(?<![.,;:!?'")\]])
```
Questo negative lookbehind verifica che l'ultimo carattere dell'URL non sia punteggiatura. Senza di esso, verrebbero catturate la virgola in `visita https://esempio.com, poi...` come parte dell'URL.

</details>

---

### Esercizio 6 — Parser Log Apache

**Obiettivo:** Parsa righe di log in formato Apache Combined Log Format.

**Formato:** `IP - UTENTE [DATA] "METODO URL PROTOCOLLO" STATUS DIMENSIONE "REFERER" "USER_AGENT"`

**Esempio:**
```
192.168.1.1 - mario [15/Mar/2025:10:30:00 +0100] "GET /index.html HTTP/1.1" 200 1234 "http://example.com" "Mozilla/5.0"
```

<details>
<summary>Soluzione</summary>

```python
import re
from dataclasses import dataclass
from typing import Optional

@dataclass
class LogEntry:
    ip: str
    utente: str
    data: str
    metodo: str
    url: str
    protocollo: str
    status: int
    dimensione: Optional[int]  # Puo essere - (nessun body)
    referer: Optional[str]
    user_agent: str

# Pattern Apache Combined Log Format
# Smontaggio parte per parte:
APACHE_COMBINED = re.compile(r"""
    (?P<ip>\d{1,3}(?:\.\d{1,3}){3})  # IP: quattro gruppi di cifre separati da punto
    \s+-\s+                            # Separatore con campo identita (-)
    (?P<utente>\S+)                    # Utente autenticato (- se anonimo)
    \s+
    \[(?P<data>[^\]]+)\]              # Data tra parentesi quadre
    \s+
    "(?P<metodo>[A-Z]+)               # Metodo HTTP (GET, POST, ...)
    \s+(?P<url>\S+)                   # URL richiesto
    \s+(?P<protocollo>HTTP/[\d.]+)"   # Versione protocollo
    \s+(?P<status>\d{3})              # Codice di stato HTTP
    \s+(?P<dimensione>\d+|-)          # Dimensione risposta (- se nessuna)
    (?:                               # Parte opzionale (Combined vs Common)
        \s+"(?P<referer>[^"]*)"       # Referer tra virgolette
        \s+"(?P<user_agent>[^"]*)"   # User agent tra virgolette
    )?
""", re.VERBOSE)

def parsa_riga_apache(riga: str) -> Optional[LogEntry]:
    """Parsa una riga di log Apache. Restituisce None se non corrisponde."""
    m = APACHE_COMBINED.search(riga.strip())
    if not m:
        return None
    
    dimensione_str = m.group("dimensione")
    return LogEntry(
        ip=m.group("ip"),
        utente=m.group("utente"),
        data=m.group("data"),
        metodo=m.group("metodo"),
        url=m.group("url"),
        protocollo=m.group("protocollo"),
        status=int(m.group("status")),
        dimensione=int(dimensione_str) if dimensione_str != "-" else None,
        referer=m.group("referer") or None,
        user_agent=m.group("user_agent") or "N/A",
    )


# Test
righe_log = [
    '192.168.1.1 - mario [15/Mar/2025:10:30:00 +0100] "GET /index.html HTTP/1.1" 200 1234 "http://example.com" "Mozilla/5.0"',
    '10.0.0.2 - - [15/Mar/2025:10:31:00 +0100] "POST /api/login HTTP/1.1" 401 89 "-" "curl/7.84.0"',
    '203.0.113.5 - admin [15/Mar/2025:10:32:00 +0100] "GET /admin HTTP/1.1" 403 156',
]

for riga in righe_log:
    entry = parsa_riga_apache(riga)
    if entry:
        print(f"  [{entry.status}] {entry.ip} {entry.metodo} {entry.url}")
    else:
        print(f"  RIGA NON PARSATA: {riga[:40]}...")
# [200] 192.168.1.1 GET /index.html
# [401] 10.0.0.2 POST /api/login
# [403] 203.0.113.5 GET /admin
```

</details>

---

### Esercizio 7 — Sostitutore di Formati Data

**Obiettivo:** Converti date tra formati diversi in un testo.

**Requisiti:**
- Riconosci formato ISO (`2025-03-15`) e formato italiano (`15/03/2025` o `15-03-2025`)
- Converti da ISO a italiano
- Converti da italiano a ISO
- Gestisci separatori misti (`/` e `-`)

<details>
<summary>Soluzione</summary>

```python
import re

# Pattern per formato ISO: aaaa-mm-gg
ISO = re.compile(
    r"\b(?P<anno>(?:19|20)\d{2})"  # Anno: 1900-2099
    r"-"
    r"(?P<mese>0[1-9]|1[0-2])"     # Mese: 01-12
    r"-"
    r"(?P<giorno>0[1-9]|[12]\d|3[01])\b"  # Giorno: 01-31
)

# Pattern per formato italiano: gg/mm/aaaa o gg-mm-aaaa
ITALIANO = re.compile(
    r"\b(?P<giorno>0[1-9]|[12]\d|3[01])"  # Giorno: 01-31
    r"[/\-]"                                # Separatore: / o -
    r"(?P<mese>0[1-9]|1[0-2])"            # Mese: 01-12
    r"[/\-]"                                # Separatore: / o -
    r"(?P<anno>(?:19|20)\d{2})\b"          # Anno: 1900-2099
)

def iso_a_italiano(testo: str, separatore: str = "/") -> str:
    """Converte date da formato ISO a formato italiano."""
    def converti(m: re.Match) -> str:
        return f"{m.group('giorno')}{separatore}{m.group('mese')}{separatore}{m.group('anno')}"
    return ISO.sub(converti, testo)

def italiano_a_iso(testo: str) -> str:
    """Converte date da formato italiano a formato ISO."""
    def converti(m: re.Match) -> str:
        return f"{m.group('anno')}-{m.group('mese')}-{m.group('giorno')}"
    return ITALIANO.sub(converti, testo)


# Test
testo_iso = "Evento del 2025-03-15, termine il 2025-12-31, inizio il 1999-01-01"
print(iso_a_italiano(testo_iso))
# Evento del 15/03/2025, termine il 31/12/2025, inizio il 01/01/1999

testo_it = "Nato il 25/12/1990, laureato il 15-06-2015, assunto il 01/09/2020"
print(italiano_a_iso(testo_it))
# Nato il 1990-12-25, laureato il 2015-06-15, assunto il 2020-09-01
```

</details>

---

### Esercizio 8 — Estrattore Prezzi da Testo

**Obiettivo:** Estrai tutti i prezzi da un testo in italiano.

**Formati da riconoscere:**
- `50 euro` o `50 EUR`
- `€ 1.234,56` o `1.234,56 €`
- `€50` o `50€`
- `euro 50` o `50 euro`
- Non catturare numeri senza simbolo valuta

<details>
<summary>Soluzione</summary>

```python
import re
from dataclasses import dataclass

@dataclass
class Prezzo:
    valore_testo: str   # come appare nel testo
    valore_float: float  # valore numerico

PREZZO_PATTERN = re.compile(r"""
    (?:
        # Formato 1: simbolo € prima del numero
        (?P<simbolo_prima>€\s*)
        (?P<valore_1>[\d]{1,3}(?:\.[\d]{3})*(?:,[\d]{1,2})?)
        |
        # Formato 2: simbolo € dopo il numero
        (?P<valore_2>[\d]{1,3}(?:\.[\d]{3})*(?:,[\d]{1,2})?)
        \s*(?P<simbolo_dopo>€)
        |
        # Formato 3: parola "euro" o "EUR" dopo il numero
        (?P<valore_3>[\d]{1,3}(?:\.[\d]{3})*(?:,[\d]{1,2})?)
        \s*(?P<euro_dopo>euro|EUR)\b
        |
        # Formato 4: parola "euro" prima del numero
        (?P<euro_prima>euro|EUR)\s+
        (?P<valore_4>[\d]{1,3}(?:\.[\d]{3})*(?:,[\d]{1,2})?)
    )
""", re.VERBOSE | re.IGNORECASE)

def normalizza_numero(s: str) -> float:
    """Converte stringa numero italiano (1.234,56) in float."""
    # Rimuovi i punti delle migliaia, sostituisci virgola decimale con punto
    return float(s.replace(".", "").replace(",", "."))

def estrai_prezzi(testo: str) -> list:
    """Estrae tutti i prezzi da un testo."""
    prezzi = []
    for m in PREZZO_PATTERN.finditer(testo):
        # Trova il gruppo con il valore
        valore_str = (m.group("valore_1") or m.group("valore_2") or
                     m.group("valore_3") or m.group("valore_4"))
        if valore_str:
            prezzi.append(Prezzo(
                valore_testo=m.group(),
                valore_float=normalizza_numero(valore_str)
            ))
    return prezzi


# Test
testo = """
Il laptop costa €1.299,00 ma con lo sconto arriva a 999 euro.
La tastiera e 79€ e il mouse 29,90 EUR.
Spedizione gratis per ordini superiori a euro 50.
"""

for p in estrai_prezzi(testo):
    print(f"  Trovato: '{p.valore_testo.strip()}' = {p.valore_float:.2f} EUR")
# Trovato: '€1.299,00' = 1299.00 EUR
# Trovato: '999 euro' = 999.00 EUR
# Trovato: '79€' = 79.00 EUR
# Trovato: '29,90 EUR' = 29.90 EUR
# Trovato: 'euro 50' = 50.00 EUR
```

</details>

---

### Esercizio 9 — Correzione Ortografica Fuzzy

**Obiettivo:** Implementa un correttore ortografico semplice usando `difflib` e `rapidfuzz`.

**Requisiti:**
- Dato un dizionario di parole corrette, suggerisci la parola giusta per ogni parola sbagliata
- Usa `difflib.get_close_matches()` come approccio base
- Usa `rapidfuzz` per un confronto piu accurato
- Mostra il punteggio di confidenza del suggerimento

<details>
<summary>Soluzione</summary>

```python
import difflib
from dataclasses import dataclass
from typing import Optional

# pip install rapidfuzz
from rapidfuzz import process, fuzz

@dataclass
class Correzione:
    parola_originale: str
    suggerimento: Optional[str]
    confidenza: float  # 0.0 - 100.0
    metodo: str

DIZIONARIO_IT = [
    "programmazione", "python", "espressione", "regolare",
    "funzione", "variabile", "stringa", "intero", "lista",
    "dizionario", "tuple", "insieme", "classe", "metodo",
    "attributo", "modulo", "pacchetto", "libreria", "importare",
    "eccezione", "errore", "debug", "test", "documenti"
]

def correggi_con_difflib(parola: str, dizionario: list) -> Correzione:
    """Correzione usando difflib.get_close_matches."""
    risultati = difflib.get_close_matches(parola, dizionario, n=1, cutoff=0.6)
    if risultati:
        # Calcola la similarita manualmente
        matcher = difflib.SequenceMatcher(None, parola, risultati[0])
        confidenza = matcher.ratio() * 100
        return Correzione(parola, risultati[0], confidenza, "difflib")
    return Correzione(parola, None, 0.0, "difflib")

def correggi_con_rapidfuzz(parola: str, dizionario: list) -> Correzione:
    """Correzione usando rapidfuzz.process.extractOne."""
    risultato = process.extractOne(
        parola, dizionario,
        scorer=fuzz.ratio,
        score_cutoff=60  # soglia minima: 60%
    )
    if risultato:
        parola_suggerita, confidenza, _ = risultato
        return Correzione(parola, parola_suggerita, confidenza, "rapidfuzz")
    return Correzione(parola, None, 0.0, "rapidfuzz")


# Test
parole_sbagliate = [
    "programazzione",   # programmazione
    "piton",            # python
    "espresione",       # espressione
    "variabiel",        # variabile
    "xyzkqj",           # nessuna corrispondenza
]

print("CORREZIONE CON DIFFLIB:")
for parola in parole_sbagliate:
    c = correggi_con_difflib(parola, DIZIONARIO_IT)
    if c.suggerimento:
        print(f"  '{c.parola_originale}' -> '{c.suggerimento}' (confidenza: {c.confidenza:.1f}%)")
    else:
        print(f"  '{c.parola_originale}' -> nessun suggerimento")

print("\nCORREZIONE CON RAPIDFUZZ:")
for parola in parole_sbagliate:
    c = correggi_con_rapidfuzz(parola, DIZIONARIO_IT)
    if c.suggerimento:
        print(f"  '{c.parola_originale}' -> '{c.suggerimento}' (confidenza: {c.confidenza:.1f}%)")
    else:
        print(f"  '{c.parola_originale}' -> nessun suggerimento")
```

</details>

---

### Esercizio 10 — Parser Markdown Semplice

**Obiettivo:** Converti un sottoinsieme di Markdown in HTML usando regex.

**Elementi da supportare:**
- Intestazioni: `# H1`, `## H2`, `### H3`
- Grassetto: `**testo**`
- Corsivo: `*testo*`
- Codice inline: `` `codice` ``
- Link: `[testo](url)`
- Righe vuote diventano separatori `<hr>` o paragrafi

<details>
<summary>Soluzione</summary>

```python
import re

def markdown_to_html(testo: str) -> str:
    """Converte un sottoinsieme di Markdown in HTML.
    
    Nota: questo e un parser molto semplificato. Per Markdown reale
    usa librerie come 'markdown' o 'mistune' (pip install markdown).
    """
    righe = testo.split("\n")
    output = []
    
    for riga in righe:
        # Intestazioni: # Testo -> <h1>Testo</h1>
        # Smontaggio: ^(#{1,6})\s+(.+)$
        #   ^       → inizio riga
        #   (#{1,6}) → gruppo 1: da 1 a 6 cancelletti
        #   \s+     → spazio obbligatorio
        #   (.+)    → gruppo 2: testo dell'intestazione
        #   $       → fine riga
        match_h = re.match(r"^(#{1,6})\s+(.+)$", riga)
        if match_h:
            livello = len(match_h.group(1))  # numero di #
            testo_h = match_h.group(2)
            output.append(f"<h{livello}>{testo_h}</h{livello}>")
            continue
        
        # Riga vuota -> paragrafo vuoto
        if not riga.strip():
            output.append("")
            continue
        
        # Elaborazione inline sulla riga corrente
        elaborata = riga
        
        # Codice inline (PRIMA di grassetto/corsivo per evitare conflitti)
        elaborata = re.sub(r"`([^`]+)`", r"<code>\1</code>", elaborata)
        
        # Grassetto: **testo** -> <strong>testo</strong>
        # Smontaggio: \*\*(.+?)\*\*
        #   \*\* → due asterischi letterali (escaped)
        #   (.+?) → gruppo: contenuto (lazy)
        #   \*\* → due asterischi di chiusura
        elaborata = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", elaborata)
        
        # Corsivo: *testo* -> <em>testo</em>
        # Smontaggio: (?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)
        # I lookbehind/ahead evitano conflitti con **grassetto**
        elaborata = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", elaborata)
        
        # Link: [testo](url) -> <a href="url">testo</a>
        # Smontaggio: \[([^\]]+)\]\(([^)]+)\)
        #   \[         → parentesi quadra apertura (escaped)
        #   ([^\]]+)   → gruppo 1: testo del link (tutto tranne ])
        #   \]         → parentesi quadra chiusura
        #   \(         → parentesi tonda apertura
        #   ([^)]+)    → gruppo 2: URL (tutto tranne ))
        #   \)         → parentesi tonda chiusura
        elaborata = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', elaborata)
        
        output.append(elaborata)
    
    return "\n".join(output)


# Test
markdown = """# Titolo Principale

## Sezione Python

La **programmazione** in *Python* e divertente.

Usa `re.findall()` per trovare pattern.

Visita [la documentazione](https://docs.python.org) per saperne di piu.

### Sottosezione

Testo con **grassetto** e *corsivo* e `codice` insieme.
"""

html = markdown_to_html(markdown)
print(html)
# <h1>Titolo Principale</h1>
# 
# <h2>Sezione Python</h2>
# 
# La <strong>programmazione</strong> in <em>Python</em> e divertente.
# 
# Usa <code>re.findall()</code> per trovare pattern.
# 
# Visita <a href="https://docs.python.org">la documentazione</a> per saperne di piu.
# 
# <h3>Sottosezione</h3>
# 
# Testo con <strong>grassetto</strong> e <em>corsivo</em> e <code>codice</code> insieme.
```

</details>

---

## Conclusione del Blocco 4

I 10 esercizi coprono progressivamente:

1. **Email** — validazione con fullmatch e VERBOSE
2. **Codice Fiscale** — classe di caratteri avanzata `[ABCDEHLMPRST]`
3. **IBAN** — regex + algoritmo checksum (regex non basta mai da sola)
4. **Targa** — alternativa tra pattern diversi con if/elif
5. **URL** — pattern avanzato con lookbehind per punteggiatura finale
6. **Log Apache** — gruppi nominati multipli, parsing strutturato
7. **Conversion date** — sub con callback, due direzioni
8. **Prezzi** — alternativa con gruppi multipli, normalizzazione
9. **Correzione fuzzy** — difflib e rapidfuzz a confronto
10. **Markdown parser** — pipeline di sub sequenziali, ordine critico

Nel **Blocco 5** troverai le tecniche per esperti e il riepilogo finale.

---


---

## Parte E — Per gli Esperti

---

### E.1 Atomic Groups e Possessive Quantifiers

Come abbiamo visto in C.3, il backtracking catastrofico nasce quando il motore NFA deve esplorare combinazioni esponenziali. Atomic groups e possessive quantifiers eliminano questo problema alla radice.

**Questi strumenti richiedono il modulo `regex` (non disponibili in `re` standard):**

```bash
pip install regex
```

#### Atomic Groups `(?>...)`

Un atomic group impedisce il backtracking al suo interno. Una volta completato il match del gruppo, il motore non ci entra piu per cercare alternative.

```python
import regex

# Confronto: con e senza atomic group
# Pattern: (a+)b
# Input: "aaac" (non corrisponde — c invece di b)

# Senza atomic group: backtracking normale
pattern_normale = regex.compile(r"(a+)b")
# Tentativi con "aaac":
# 1. (a+) cattura "aaa", cerca 'b', trova 'c' — fallisce
# 2. BACKTRACK: (a+) cattura "aa", cerca 'b', trova 'c' — fallisce
# 3. BACKTRACK: (a+) cattura "a", cerca 'b', trova 'a' — fallisce
# 4. Fallimento dopo 3 backtrack

# Con atomic group: nessun backtracking
pattern_atomico = regex.compile(r"(?>a+)b")
# Tentativi con "aaac":
# 1. (?>a+) cattura "aaa" (greedy), cerca 'b', trova 'c' — fallisce
# 2. Atomic group: NESSUN BACKTRACK — fallisce immediatamente

# Su input valido, il risultato e identico:
print(regex.search(r"(a+)b", "aaab"))       # Match: 'aaab'
print(regex.search(r"(?>a+)b", "aaab"))     # Match: 'aaab'

# Su input non valido, l'atomic group e molto piu veloce:
print(regex.search(r"(a+)b", "aaac"))       # None (dopo backtracking)
print(regex.search(r"(?>a+)b", "aaac"))     # None (immediato)
```

#### Possessive Quantifiers `*+`, `++`, `?+`

I possessive quantifiers sono zucchero sintattico per atomic groups:
- `a*+` equivale a `(?>a*)`
- `a++` equivale a `(?>a+)`
- `a?+` equivale a `(?>a?)`

```python
import regex

# Esempio: parsing di campi CSV
# Il [^"]* dentro le virgolette non dovrebbe mai includere virgolette
# Il possessive rende impossibile il backtracking catastrofico

# Greedy standard (funziona ma con potenziale backtracking)
csv_greedy = regex.compile(r'"[^"]*"')

# Possessive (piu efficiente su input non valido)
csv_possessive = regex.compile(r'"[^"]*+"')
# [^"]   → qualsiasi carattere tranne virgolette
# *+     → zero o piu volte (possessive — non rilascia mai)

testo = '"campo1","campo2","campo3"'
print(regex.findall(r'"[^"]*+"', testo))
# Output: ['"campo1"', '"campo2"', '"campo3"']

# La differenza emerge con input malformato (virgolette non chiuse):
# '"campo aperto   <- qui il possessive fallisce SUBITO
# mentre il greedy fa backtracking su ogni carattere
```

#### Quando Usare Atomic Groups / Possessive

```
USALI quando:
1. Stai processando input non fidato (prevenzione ReDoS)
2. Il pattern ha classi di caratteri non sovrapposte (es. [^"] seguito da ")
3. Sai che il backtracking non portera a nuovi match

NON servono quando:
1. Il pattern e gia sicuro (nessun quantificatore annidato)
2. Il testo e breve e noto
3. Usi gia re2 (che non ha backtracking per definizione)
```

---

### E.2 Proprieta Unicode con il Modulo regex

Il modulo `regex` supporta le **Unicode Property Escapes** con la sintassi `\p{Property}`, allineandosi allo standard UTS #18.

```python
import regex

# \p{L} — qualsiasi lettera, in qualsiasi script
print(regex.findall(r"\p{L}+", "Hello Мир world 世界"))
# Output: ['Hello', 'Мир', 'world', '世界']

# \p{N} — qualsiasi numero, in qualsiasi sistema numerico
print(regex.findall(r"\p{N}+", "Prezzo: 42€ oppure 123"))
# Output: ['42', '123']

# Script specifici
print(regex.findall(r"\p{Cyrillic}+", "Hello Мир World"))
# Output: ['Мир']

print(regex.findall(r"\p{Han}+", "Hello 世界 World"))
# Output: ['世界']

print(regex.findall(r"\p{Greek}+", "Simboli: αβγδε e abc"))
# Output: ['αβγδε']

# Categorie granulari
print(regex.findall(r"\p{Lu}+", "HELLO World"))
# Output: ['HELLO', 'W']  — solo lettere maiuscole

print(regex.findall(r"\p{Ll}+", "HELLO World"))
# Output: ['orld']  — solo lettere minuscole

# Negazione con \P (maiuscolo)
print(regex.findall(r"\P{L}+", "abc 123 !"))
# Output: [' ', ' ', '!']  — tutto tranne lettere

# Operazioni su insiemi (richiede Version 1)
pattern = regex.compile(r"[\p{L}&&[^\p{Latin}]]+", flags=regex.V1)
print(pattern.findall("Hello Мир 世界"))
# Output: ['Мир', '世界']  — lettere non-latine
```

---

### E.3 Pattern Condizionali

Il modulo `regex` supporta anche i **pattern condizionali**: `(?(id)yes|no)` — "se il gruppo `id` ha fatto match, usa il pattern `yes`, altrimenti usa `no`".

```python
import regex

# Formato: (?(1)pattern_se_gruppo1_ha_matchato|pattern_altrimenti)
# Utile per gestire formati opzionali che cambiano la struttura successiva

# Esempio: numeri con segno opzionale
# Se c'e il segno '-' o '+', ci aspettiamo solo cifre dopo
# Altrimenti, potrebbe esserci anche una virgola decimale
pattern = regex.compile(r"(-|\+)?(?(1)\d+|\d+(?:,\d+)?)")

test = ["-42", "+100", "3,14", "99"]
for t in test:
    m = pattern.fullmatch(t)
    if m:
        print(f"  Match: '{t}' segno={m.group(1)}")
    else:
        print(f"  No match: '{t}'")
```

---

### E.4 pyparsing — Parser per Linguaggi Strutturati

Quando le regex non bastano (linguaggi context-free, grammatiche ricorsive), `pyparsing` offre un framework per costruire parser leggibili.

```python
# pip install pyparsing
from pyparsing import (
    Word, alphas, alphanums, nums, Suppress, Group,
    Optional, Literal, oneOf, pyparsing_common,
    QuotedString, ZeroOrMore
)

# --- Parser di configurazione chiave=valore ---
chiave = Word(alphas + "_", alphanums + "_")
valore_num = pyparsing_common.number
valore_str = QuotedString('"') | QuotedString("'")
valore_bare = Word(alphanums + "._-/")
valore = valore_str | valore_num | valore_bare

coppia = chiave + Suppress(Literal("=")) + valore

risultato = coppia.parseString("database_host=localhost")
print(risultato.asList())  # ['database_host', 'localhost']

risultato = coppia.parseString('porta=5432')
print(risultato.asList())  # ['porta', 5432]

# --- Quando usare pyparsing vs regex ---
# pyparsing e preferibile quando:
# 1. Il formato ha struttura ricorsiva (es. espressioni matematiche)
# 2. Il formato ha regole context-sensitive
# 3. La leggibilita e la manutenibilita sono prioritarie
# 4. Hai bisogno di messaggi di errore precisi

# --- Parser di espressioni matematiche semplici ---
from pyparsing import infixNotation, opAssoc

numero = pyparsing_common.number
operazione = infixNotation(
    numero,
    [
        (oneOf("* /"), 2, opAssoc.LEFT),   # moltiplicazione/divisione
        (oneOf("+ -"), 2, opAssoc.LEFT),   # addizione/sottrazione
    ]
)

risultato = operazione.parseString("3 + 4 * 2 - 1")
print(risultato.asList())
# [3, '+', [4, '*', 2], '-', 1]
# Nota: la precedenza degli operatori e rispettata grazie a infixNotation
```

---

### E.5 Performance Regex — Regole di Ottimizzazione

#### Regola 1: Ordine delle Alternative

Nelle alternative `a|b|c`, il motore testa le opzioni da sinistra a destra. Metti le opzioni **piu comuni prima** per ridurre i tentativi medi.

```python
import re
import timeit

testo = "INFO " * 10000 + "ERROR " + "WARNING "

# LENTO: le alternative meno comuni sono testate prima
p_lento = re.compile(r"(?:CRITICAL|ERROR|WARNING|INFO)\b")

# VELOCE: le alternative piu comuni sono testate prima
p_veloce = re.compile(r"(?:INFO|WARNING|ERROR|CRITICAL)\b")

t_lento = timeit.timeit(lambda: p_lento.findall(testo), number=100)
t_veloce = timeit.timeit(lambda: p_veloce.findall(testo), number=100)

print(f"Lento:  {t_lento:.4f}s")
print(f"Veloce: {t_veloce:.4f}s")
print(f"Speedup: {t_lento/t_veloce:.1f}x")
```

#### Regola 2: Classi di Caratteri vs Alternativa

Le classi di caratteri `[abc]` sono quasi sempre piu veloci delle alternative `(a|b|c)` per singoli caratteri.

```python
import re
import timeit

testo = "a" * 10000

# LENTO: alternativa per caratteri singoli
p_alt = re.compile(r"(a|e|i|o|u)+")

# VELOCE: classe di caratteri
p_cls = re.compile(r"[aeiou]+")

t_alt = timeit.timeit(lambda: p_alt.findall(testo), number=1000)
t_cls = timeit.timeit(lambda: p_cls.findall(testo), number=1000)

print(f"Alternativa: {t_alt:.4f}s")
print(f"Classe:      {t_cls:.4f}s")
# La classe e tipicamente 2-5x piu veloce
```

#### Regola 3: Anchors Riducono il Lavoro

Usare `^` e `$` quando appropriato permette al motore di fallire subito senza esaminare tutta la stringa.

```python
import re

# Senza anchor: il motore prova il match a ogni posizione
p_senza = re.compile(r"python")
# Su una stringa di 1000 caratteri: prova il match 1000 volte

# Con anchor: il motore prova solo all'inizio
p_con = re.compile(r"^python")
# Su una stringa di 1000 caratteri: prova il match UNA volta
```

#### Regola 4: Evitare Backtracking con Pattern Specifici

Piu le classi di caratteri sono specifiche, meno backtracking e necessario.

```python
import re

# GENERICO (piu backtracking potenziale)
p_generico = re.compile(r"(.+)@(.+)\.(.+)")

# SPECIFICO (meno backtracking)
p_specifico = re.compile(r"([^@]+)@([^.]+)\.(.+)")
# [^@]+ = tutto tranne @ (non puo mai catturare @ per sbaglio)
# [^.]+ = tutto tranne . (non puo mai catturare . per sbaglio)

# Il pattern specifico fallisce piu velocemente su input non valido
# e fa meno backtracking su input valido
```

#### Regola 5: re.DEBUG — Ispezionare il Bytecode

```python
import re

# re.DEBUG stampa la struttura interna del pattern compilato
# Utile per capire cosa sta facendo il motore
pattern = re.compile(r"(?P<utente>\w+)@(?P<dominio>\w+)\.\w+", re.DEBUG)

# Output (semplificato):
# SUBPATTERN 1 0 0
#   MAX_REPEAT 1 MAXREPEAT
#     IN
#       CATEGORY CATEGORY_WORD
# LITERAL 64  (@)
# ...
```

---

### E.6 Regex per la Sicurezza

Le regex svolgono un ruolo cruciale nella sicurezza applicativa. Ecco i pattern piu importanti e le insidie da evitare.

#### Input Sanitization con re.escape()

```python
import re

def cerca_nel_testo(query: str, testo: str) -> list:
    """Cerca una query fornita dall'utente in modo sicuro.
    
    SENZA re.escape():
    - L'utente potrebbe inserire "a+b" e la regex cercherebbe
      uno o piu 'a' seguiti da 'b' — non il testo letterale "a+b"
    
    CON re.escape():
    - Ogni carattere speciale viene neutralizzato
    - "a+b" diventa r"a\+b" — ricerca letterale
    """
    pattern_sicuro = re.compile(re.escape(query), re.IGNORECASE)
    return pattern_sicuro.findall(testo)

# Utente digita: "price: $10.99"
query_utente = "price: $10.99"
testo = "The price: $10.99 is valid"

# SICURO: re.escape neutralizza $ e .
risultati = cerca_nel_testo(query_utente, testo)
print(risultati)  # ['price: $10.99']

# INSICURO senza re.escape:
# re.compile(query_utente) potrebbe comportarsi in modo inatteso
# perche $ e . hanno significati speciali
```

#### Validazione di Input per Sicurezza

```python
import re

# Pattern per validare nomi di file (prevenire path traversal)
NOME_FILE_SICURO = re.compile(r"^[a-zA-Z0-9._-]{1,255}$")

def valida_nome_file(nome: str) -> bool:
    """Verifica che un nome file sia sicuro.
    Blocca: /, \\, .., caratteri di controllo, sequenze pericolose.
    """
    if ".." in nome or "/" in nome or "\\" in nome:
        return False
    return bool(NOME_FILE_SICURO.match(nome))

# Test
nomi = ["report.pdf", "../../../etc/passwd", "file name.txt", "normal_file-01.csv"]
for nome in nomi:
    print(f"  {'OK' if valida_nome_file(nome) else 'BLOCCATO'}: '{nome}'")
# OK: 'report.pdf'
# BLOCCATO: '../../../etc/passwd'
# BLOCCATO: 'file name.txt'  (spazio non permesso)
# OK: 'normal_file-01.csv'

# Pattern per validare token/API key (es. JWT-like)
TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9\-_]{20,200}$")

def valida_token(token: str) -> bool:
    return bool(TOKEN_PATTERN.match(token))

# Pattern per rilevare SQL injection di base (uso difensivo)
SQL_INJECTION_PATTERNS = [
    re.compile(r"('|--|;|\/\*|\*\/)", re.IGNORECASE),
    re.compile(r"\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|EXEC)\b", re.IGNORECASE),
]

def rileva_sql_injection(input_utente: str) -> bool:
    """Rilevamento base di possibili SQL injection.
    NON e sufficiente da solo — usa sempre parametric queries.
    """
    return any(p.search(input_utente) for p in SQL_INJECTION_PATTERNS)

# Test
inputs = ["Mario Rossi", "'; DROP TABLE users; --", "1 UNION SELECT * FROM passwords"]
for i in inputs:
    rilevato = rileva_sql_injection(i)
    print(f"  SQL injection {'RILEVATA' if rilevato else 'non trovata'}: '{i}'")
```

---

## Parte F — Riepilogo Finale

---

### Cheat Sheet Regex — Tabella Visiva Completa

#### Metacaratteri

```
Metacarattere  Significato                        Esempio           Trova
-------------  ----------------------------------  ----------------  ------------------
.              Qualsiasi carattere (no \n)         c.sa              casa, cosa, c1sa
^              Inizio stringa/riga                 ^Python           "Python..." si
$              Fine stringa/riga                   \.py$             "file.py" si
*              Zero o piu (greedy)                 ab*c              ac, abc, abbc
+              Uno o piu (greedy)                  ab+c              abc, abbc (no ac)
?              Zero o uno (opzionale)              colou?r           color, colour
*?             Zero o piu (lazy)                   <.+?>             <b>, </b>
+?             Uno o piu (lazy)                    <.+>              <b>...</b>
|              OR logico                           gatto|cane        gatto o cane
\              Escape / sequenza speciale          \.                punto letterale
(  )           Gruppo catturante                   (\d{4})           "2025" catturato
(?:  )         Gruppo non catturante               (?:https?|ftp)    raggruppa senza cattura
(?P<n>  )      Gruppo nominato                     (?P<anno>\d{4})   accesso per nome
[  ]           Classe di caratteri                 [aeiou]           vocali
[^  ]          Classe negata                       [^0-9]            non-cifre
{n}            Esattamente n volte                 \d{4}             4 cifre
{n,m}          Da n a m volte                      \d{2,4}           2, 3 o 4 cifre
{n,}           Almeno n volte                      \d{2,}            2+ cifre
```

#### Classi Predefinite

```
Classe  Equivalente        Significato               Come ricordarlo
------  -----------------  ------------------------  ---------------
\d      [0-9]              Cifra                     digit
\D      [^0-9]             Non cifra                 Digit negato
\w      [a-zA-Z0-9_]       Carattere word            word
\W      [^a-zA-Z0-9_]      Non word                  Word negato
\s      [ \t\n\r\f\v]      Spazio bianco             space
\S      [^ \t\n\r\f\v]     Non spazio                Space negato
\b      (posizione)        Confine parola            boundary
\B      (posizione)        Non confine parola        Boundary negato
```

#### Lookaround

```
Tipo                   Sintassi    Significato              Esempio
---------------------  ----------  -----------------------  ---------------------------
Positive lookahead     (?=...)     "seguito da"             \d+(?=€) → numeri prima di €
Negative lookahead     (?!...)     "non seguito da"         \d+(?!px) → numeri non prima di px
Positive lookbehind    (?<=...)    "preceduto da"           (?<=€)\d+ → numeri dopo €
Negative lookbehind    (?<!...)    "non preceduto da"       (?<!€)\d+ → numeri non dopo €
```

#### Flag

```
Flag            Scorciatoia  Effetto
--------------  -----------  -----------------------------------------------
re.IGNORECASE   re.I         Ignora maiuscole/minuscole
re.MULTILINE    re.M         ^ e $ corrispondono a ogni riga
re.DOTALL       re.S         . cattura anche \n
re.VERBOSE      re.X         Permette spazi e commenti nel pattern
re.ASCII        re.A         \w \d \s solo ASCII (disabilita Unicode)
```

---

### Checklist di Buone Pratiche (30+)

#### Fondamentali

1. Usa **sempre** il prefisso `r` nelle stringhe regex: `r"\d+"` non `"\d+"`
2. Usa `re.fullmatch()` per la **validazione**, non `re.match()`
3. Controlla **sempre** se il risultato di `search()`/`match()` e `None` prima di usarlo
4. Usa `if match := re.search(...)` (walrus operator, Python 3.8+) per codice conciso
5. Non usare regex per operazioni che `str.split()`, `str.replace()` o `str.find()` bastano

#### Leggibilita

6. Usa `re.VERBOSE` per qualsiasi pattern piu lungo di 30 caratteri
7. Usa **gruppi nominati** `(?P<nome>...)` in pattern con 3+ gruppi
8. Commenta il significato di ogni sotto-pattern non ovvio
9. Dai nomi descrittivi alle regex compilate: `EMAIL_PATTERN` non `p1`
10. Separa i pattern complessi su piu righe con la concatenazione implicita di stringhe

#### Performance

11. Precompila i pattern usati in loop o in funzioni ripetute con `re.compile()`
12. Posiziona i match piu comuni **prima** nelle alternazioni: `INFO|WARNING|ERROR|CRITICAL`
13. Usa classi di caratteri `[abc]` invece di alternazioni `(a|b|c)` per singoli caratteri
14. Usa `^` e `$` quando il match deve essere all'inizio/fine — riduce i tentativi
15. Per input non fidato in produzione, valuta `re2` (pip install google-re2)

#### Sicurezza

16. **Non costruire pattern con f-string da input utente**: `re.compile(f"cerca_{user_input}")` e vulnerabile
17. Usa **sempre** `re.escape()` quando il testo da cercare proviene dall'utente
18. Limita la **lunghezza massima** dell'input prima di applicare regex complesse
19. Evita pattern con **quantificatori annidati**: `(a+)+`, `(a*)*`, `(a|b+)+`
20. Usa **atomic groups** o **possessive quantifiers** (con `regex`) per input non fidato

#### Correttezza

21. Testa il pattern con casi validi, invalidi, e **casi limite** (stringa vuota, caratteri speciali)
22. Verifica che il pattern funzioni con `re.UNICODE` per testi internazionali
23. Attenzione alle **backreference** in `re.sub()`: `\1` nella stringa di sostituzione, non nel pattern
24. In `re.split()`, usa un **gruppo catturante** se vuoi includere il separatore nel risultato
25. Ricorda che `re.findall()` con gruppi restituisce i **contenuti dei gruppi**, non i match completi

#### Unicode

26. Normalizza sempre in **NFC** prima di confrontare stringhe: `unicodedata.normalize("NFC", s)`
27. Per rimuovere accenti, usa **NFD + filtro categoria Mn**: non fare replace manuale degli accenti
28. Per testo multilingue, **non usare `re.ASCII`** — mantieni il default Unicode
29. Usa `unicodedata.category()` per classificare caratteri in modo robusto
30. Per script multipli, usa il modulo `regex` con `\p{Script}` invece di range ASCII

#### Avanzate

31. Usa `re.DEBUG` per ispezionare il bytecode interno di un pattern complesso
32. Per fuzzy matching usa `rapidfuzz` (piu veloce di `difflib` per grandi dataset)
33. Per parsing di linguaggi strutturati, considera `pyparsing` invece di regex
34. Documenta sempre i limiti noti del pattern (es. "non verifica checksum", "non supporta TLD lunghi")
35. Per log analysis, considera `parse` (pip install parse) per pattern piu leggibili delle regex

---

### Glossario dei Termini

| Termine | Definizione |
|---------|-------------|
| **Anchor** | Asserzione a larghezza zero che corrisponde a una posizione (non un carattere): `^` `$` `\b` `\B` |
| **Atomic group** | `(?>...)` — gruppo che impedisce il backtracking al suo interno. Solo nel modulo `regex` |
| **Backreference** | `\1` o `(?P=nome)` — riferimento a testo gia catturato da un gruppo precedente |
| **Backtracking** | Meccanismo del motore NFA: quando un percorso fallisce, torna al bivio precedente e prova l'alternativa |
| **Capturing group** | `(...)` — gruppo che cattura il testo per uso successivo |
| **Catastrophic backtracking** | Backtracking esponenziale causato da pattern ambigui. Vedi ReDoS |
| **Character class** | `[...]` — insieme di caratteri accettabili in una posizione del pattern |
| **Combining mark** | Carattere Unicode (categoria `Mn`) che si combina con il carattere precedente: accento, dieresi |
| **DFA** | Deterministic Finite Automaton. Motore regex senza backtracking, tempo lineare. Usato da `re2` |
| **Flag** | Modificatore del comportamento del motore: `IGNORECASE`, `MULTILINE`, `DOTALL`, `VERBOSE` |
| **Fuzzy matching** | Matching approssimato che tollera errori (inserzioni, delezioni, sostituzioni) |
| **Greedy** | Quantificatore che cattura il massimo possibile: `*`, `+`, `?`, `{n,m}` |
| **Lazy** | Quantificatore che cattura il minimo possibile: `*?`, `+?`, `??`, `{n,m}?` |
| **Levenshtein distance** | Numero minimo di operazioni (inserzione, delezione, sostituzione) per trasformare una stringa in un'altra |
| **Lookahead** | `(?=...)` o `(?!...)` — verifica cio che segue senza consumare caratteri |
| **Lookbehind** | `(?<=...)` o `(?<!...)` — verifica cio che precede senza consumare caratteri |
| **Match object** | Oggetto restituito da `match()`, `search()`, `finditer()` con info sul match |
| **Metacarattere** | Carattere con significato speciale nella regex: `. ^ $ * + ? { } [ ] \ | ( )` |
| **NFA** | Non-deterministic Finite Automaton. Motore con backtracking usato da Python `re`. Supporta tutte le feature avanzate |
| **NFC / NFD** | Forme di normalizzazione Unicode. NFC: precomposta. NFD: decomposta |
| **NFKC / NFKD** | Normalizzazione di compatibilita. Converte varianti tipografiche nella forma canonica |
| **Non-capturing group** | `(?:...)` — raggruppa senza catturare. Usato per struttura, non per estrazione |
| **Named group** | `(?P<nome>...)` — gruppo con nome. Accesso con `match.group("nome")` e `match.groupdict()` |
| **Possessive quantifier** | `*+`, `++`, `?+` — cattura il massimo, non rilascia mai. Solo in `regex` |
| **Raw string** | `r"..."` — stringa in cui il backslash non e interpretato da Python. Essenziale nelle regex |
| **ReDoS** | Regular Expression Denial of Service. Attacco che sfrutta backtracking esponenziale |
| **Slug** | Stringa URL-safe derivata da testo (es. "Ciao Mondo" -> "ciao-mondo") |
| **Token** | Unita minima di testo con significato (parola, numero, punteggiatura) nella tokenizzazione |
| **Word boundary** | `\b` — posizione tra un carattere `\w` e un `\W`, o inizio/fine stringa |
| **Zero-width assertion** | Asserzione che verifica una posizione senza consumare caratteri: anchor e lookaround |

---

### Prossimi Passi — Link al Tutorial 07

Hai completato il Tutorial 06 sulle Espressioni Regolari e il Text Processing. I concetti appresi qui — pattern matching, normalizzazione Unicode, confronto fuzzy — sono fondamentali per i moduli successivi.

**tutorial_07_gestione_errori_eccezioni.md**
- Gestione delle eccezioni `re.error` nei pattern malformati
- Exception handling nelle pipeline di text processing
- Logging strutturato per sistemi di parsing
- Context manager per risorse di parsing

**Concetti di questo tutorial usati nel modulo 07:**
```python
import re

try:
    # re.error viene sollevata per pattern non validi
    pattern = re.compile(r"[non chiusa")  # manca ]
except re.error as e:
    print(f"Pattern non valido: {e}")
    # pattern non valido: unterminated character set at position 1

# Pattern utile per i log del modulo 07:
LOG_EXCEPTION = re.compile(
    r"(?P<tipo>\w+Error|Exception):\s+(?P<messaggio>.+)"
)
```

**Librerie esterne da esplorare dopo questo tutorial:**
- `pyparsing` — per parser di grammatiche formali
- `parsimonious` — PEG parser in Python puro
- `lark` — parser Earley e LALR per grammatiche ambigue
- `spaCy` — NLP con tokenizzazione e NER avanzati
- `nltk` — toolkit NLP con corpora e modelli pre-addestrati

---

### Riepilogo Struttura del Tutorial

```
Tutorial 06 — Regex e Text Processing
│
├── Parte A — Le Basi (Blocco 1)
│   ├── A.1 Cos'e una Regex
│   ├── A.2 I 14 Metacaratteri (uno per uno)
│   ├── A.3 Classi di Caratteri Predefinite
│   └── A.4 Quantificatori: Greedy vs Lazy
│
├── Parte B — Il Modulo re (Blocco 2)
│   ├── B.1 match / search / fullmatch / findall / finditer
│   ├── B.2 re.sub con stringa, gruppi, callback
│   ├── B.3 re.split con pattern variabili
│   ├── B.4 Flag: I M S X A
│   ├── B.5 Gruppi: (), (?:), (?P<>), backreference
│   └── B.6 Lookahead e Lookbehind
│
├── Parte C — Tecniche Avanzate (Blocco 3)
│   ├── C.1 re.compile: quando e perche
│   ├── C.2 Il Motore NFA: backtracking
│   ├── C.3 ReDoS: pattern pericolosi e difese
│   ├── C.4 unicodedata: NFC/NFD, accenti, slug
│   ├── C.5 difflib: unified_diff, get_close_matches
│   ├── C.6 rapidfuzz: ratio, partial_ratio, process.extract
│   └── C.7 Pipeline di Text Processing
│
├── Parte D — Esercizi Pratici (Blocco 4)
│   ├── Es.1 Validatore Email
│   ├── Es.2 Validatore Codice Fiscale
│   ├── Es.3 Validatore IBAN con checksum
│   ├── Es.4 Validatore Targa Italiana
│   ├── Es.5 Estrattore URL
│   ├── Es.6 Parser Log Apache
│   ├── Es.7 Sostitutore Formati Data
│   ├── Es.8 Estrattore Prezzi
│   ├── Es.9 Correzione Ortografica Fuzzy
│   └── Es.10 Parser Markdown
│
└── Parte E — Per gli Esperti + Riepilogo (Blocco 5)
    ├── E.1 Atomic Groups e Possessive Quantifiers
    ├── E.2 Proprieta Unicode con modulo regex
    ├── E.3 Pattern Condizionali
    ├── E.4 pyparsing Intro
    ├── E.5 Performance Regex
    ├── E.6 Regex per la Sicurezza
    ├── Cheat Sheet Visivo
    ├── Checklist 35 Buone Pratiche
    ├── Glossario Completo
    └── Link a Tutorial 07
```

---

> **Companion:** `06-regex-e-text-processing.md`
> **Tutorial creato:** 2026-07-15
> **Versione:** Python 3.12+ / regex 2024.x / rapidfuzz 3.x

