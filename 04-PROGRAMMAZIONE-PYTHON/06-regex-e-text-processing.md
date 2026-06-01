---
corso: "Programmazione Python"
fase: "2 — Strumenti Essenziali"
modulo: "06"
titolo: "Regex e Text Processing"
versione: "Python 3.12+ / regex 2024.x"
livello: "Intermedio"
prerequisiti:
  - "01 — Fondamenti del Linguaggio"
  - "03 — Funzioni e Scope"
  - "05 — Gestione File e I/O"
obiettivi:
  - "Padroneggiare la sintassi delle espressioni regolari in Python"
  - "Utilizzare il modulo re e la libreria regex per pattern matching complesso"
  - "Applicare tecniche di text processing a scenari reali (log, dati, NLP)"
  - "Riconoscere e prevenire vulnerabilita ReDoS"
  - "Costruire pipeline di elaborazione testo composte e performanti"
  - "Utilizzare Unicode-aware regex per testi multilingue"
tag: [regex, text-processing, re, pattern-matching, NLP-prep, Unicode, parsing]
---

# Regex e Text Processing — Guida Completa

> **Modulo 06** · **Aggiornamento:** 2026-05-24 · **Versione:** Python 3.12+ / regex 2024.x

> ### Obiettivi di apprendimento
>
> **Prerequisiti:** [Fondamenti](01-fondamenti-linguaggio.md), [Funzioni e Scope](03-funzioni-scope.md), [Gestione File e I/O](05-gestione-file-io.md)
>
> Al termine di questo modulo saprai:
> 1. Padroneggiare la sintassi delle espressioni regolari in Python
> 2. Utilizzare il modulo `re` e la libreria `regex` per pattern matching complesso
> 3. Applicare tecniche di text processing a scenari reali (log analysis, data extraction, NLP)
> 4. Riconoscere e prevenire vulnerabilita ReDoS nelle regex
> 5. Costruire pipeline di elaborazione testo composte e performanti
> 6. Utilizzare Unicode-aware regex per testi multilingue
>
> **Tempo stimato:** 6-8 ore · **Livello:** Intermedio

## Idee guida
1. **`re.compile` per pattern reused.**
2. **Raw strings `r"..."` per regex.**
3. **ReDoS: catastrophic backtracking; usa `re2` per untrusted input.**
4. **Named groups `(?P<name>...)` per readability.**


## Mappa concettuale

```
           ┌────────────────────────────────────┐
           │     REGEX & TEXT PROCESSING         │
           └──────────┬─────────────────────────┘
                      │
     ┌────────────────┼────────────────────┐
     │                │                    │
┌────▼────┐    ┌──────▼──────┐    ┌───────▼───────┐
│ Sintassi │   │  Modulo re  │    │ Text Process  │
│  Regex   │   │  (stdlib)   │    │  Avanzato     │
└────┬────┘    └──────┬──────┘    └───────┬───────┘
     │                │                    │
 ┌───┴────┐    ┌──────┴──────┐    ┌───────┴────────┐
 │Metacar.│    │match/search │    │str methods     │
 │Classi  │    │findall/sub  │    │textwrap        │
 │Quantif.│    │compile/split│    │difflib         │
 │Gruppi  │    │Flag (I,M,S) │    │Template/Jinja2 │
 │Look*   │    │Match Object │    │unicodedata     │
 └───┬────┘    └──────┬──────┘    └───────┬────────┘
     │                │                    │
     └──────┬─────────┴────────┬───────────┘
            │                  │
  ┌─────────▼──────┐  ┌───────▼──────────┐
  │   Internals    │  │   Alternative    │
  │  (NFA engine,  │  │ (parse, pyparsing│
  │   caching,     │  │  regex, re2)     │
  │   backtrack)   │  │                  │
  └────────────────┘  └──────────────────┘
```

## Indice

1. [Panoramica](#panoramica)
2. [Fondamenti Regex](#fondamenti-regex)
   - [Sintassi Base](#sintassi-base)
   - [Anchors e Boundaries](#anchors-e-boundaries)
   - [Gruppi e Riferimenti](#gruppi-e-riferimenti)
   - [Lookahead e Lookbehind](#lookahead-e-lookbehind)
3. [Modulo re — Internals](#modulo-re--internals)
   - [Architettura del Motore NFA](#architettura-del-motore-nfa)
   - [Funzioni Principali](#funzioni-principali)
   - [Flag](#flag)
   - [Match Object](#match-object)
4. [Pattern Pratici](#pattern-pratici)
5. [Atomic Groups e Possessive Quantifiers](#atomic-groups-e-possessive-quantifiers)
6. [Performance Regex](#performance-regex)
   - [Catastrophic Backtracking](#catastrophic-backtracking)
   - [Cache e Compilazione](#cache-e-compilazione)
   - [Benchmark e Profilazione](#benchmark-e-profilazione)
7. [Alternative a re](#alternative-a-re)
   - [regex (modulo terze parti)](#regex-modulo-terze-parti)
   - [re2 e google-re2](#re2-e-google-re2)
   - [parse](#parse)
   - [pyparsing](#pyparsing)
8. [Text Processing Avanzato](#text-processing-avanzato)
   - [String Methods per Text Processing](#string-methods-per-text-processing)
   - [textwrap Module](#textwrap-module)
   - [difflib](#difflib)
   - [Template Strings](#template-strings)
9. [Elaborazione Testi Strutturati](#elaborazione-testi-strutturati)
   - [Log Parsing](#log-parsing)
   - [Parsing Configurazioni](#parsing-configurazioni)
10. [Unicode e Internazionalizzazione](#unicode-e-internazionalizzazione)
    - [Normalizzazione Avanzata con unicodedata](#normalizzazione-avanzata-con-unicodedata)
11. [Best Practices](#best-practices)
12. [Esercizi](#esercizi)
13. [Letture](#letture)
14. [Glossario](#glossario)

---

## Panoramica

Le espressioni regolari (regex, abbreviazione di *regular expressions*) rappresentano uno degli strumenti piu potenti e versatili nell'arsenale di qualsiasi programmatore. Si tratta di sequenze di caratteri che definiscono un **pattern di ricerca**, utilizzato per effettuare operazioni di matching, ricerca, sostituzione e validazione su stringhe di testo.

In Python, il modulo `re` della libreria standard fornisce un'implementazione completa e performante del motore regex. Le espressioni regolari trovano impiego in innumerevoli scenari: dalla validazione di input utente (email, numeri di telefono, codici fiscali) al parsing di file di log, dalla pulizia e trasformazione di dati testuali all'estrazione di informazioni strutturate da documenti non strutturati.

Il text processing, ovvero l'elaborazione del testo, va oltre le semplici regex e comprende un ecosistema di strumenti e tecniche per manipolare, analizzare e trasformare contenuti testuali. Python eccelle in questo ambito grazie alla ricchezza dei metodi built-in delle stringhe, ai moduli specializzati come `textwrap` e `difflib`, e al supporto nativo per Unicode.

Questa guida copre l'intero spettro: dai fondamenti della sintassi regex fino alle tecniche avanzate di elaborazione testuale, con particolare attenzione ai pattern pratici utilizzati quotidianamente nello sviluppo software.

---

## Fondamenti Regex

### Sintassi Base

#### Literal Characters e Metacharacters

Nella forma piu semplice, una regex e composta da caratteri letterali che corrispondono esattamente a se stessi. La stringa `ciao` corrisponde esattamente alla sequenza "ciao" all'interno del testo.

I **metacaratteri** sono caratteri speciali che assumono un significato particolare all'interno di un pattern regex:

```
.  ^  $  *  +  ?  {  }  [  ]  \  |  (  )
```

Significato dei metacaratteri principali:

| Metacarattere | Significato |
|---------------|-------------|
| `.` | Corrisponde a qualsiasi carattere singolo (eccetto newline, di default) |
| `^` | Inizio della stringa (o della riga in modalita multiline) |
| `$` | Fine della stringa (o della riga in modalita multiline) |
| `*` | Zero o piu ripetizioni del carattere/gruppo precedente |
| `+` | Una o piu ripetizioni del carattere/gruppo precedente |
| `?` | Zero o una occorrenza del carattere/gruppo precedente |
| `\|` | Alternativa (OR logico) |
| `\` | Carattere di escape, annulla il significato speciale del metacarattere seguente |

```python
import re

# Il punto corrisponde a qualsiasi carattere
re.findall(r"c.sa", "casa cosa cesa cusa")
# ['casa', 'cosa', 'cesa', 'cusa']

# Per cercare un punto letterale, serve l'escape
re.findall(r"file\.txt", "file.txt filetxt file-txt")
# ['file.txt']

# L'alternativa con |
re.findall(r"gatto|cane", "ho un gatto e un cane")
# ['gatto', 'cane']
```

#### Character Classes (Classi di Caratteri)

Le classi di caratteri permettono di definire un insieme di caratteri ammessi in una determinata posizione del pattern.

```python
# [abc] — corrisponde a 'a', 'b' o 'c'
re.findall(r"[aeiou]", "programmazione")
# ['o', 'a', 'a', 'i', 'o', 'e']

# [a-z] — intervallo: qualsiasi lettera minuscola da 'a' a 'z'
re.findall(r"[a-z]+", "Ciao Mondo 123")
# ['iao', 'ondo']

# [A-Za-z] — qualsiasi lettera (maiuscola o minuscola)
re.findall(r"[A-Za-z]+", "Ciao Mondo 123")
# ['Ciao', 'Mondo']

# [0-9] — qualsiasi cifra
re.findall(r"[0-9]+", "Anno 2025, mese 03")
# ['2025', '03']

# [^abc] — negazione: qualsiasi carattere TRANNE 'a', 'b', 'c'
re.findall(r"[^0-9]+", "abc123def456")
# ['abc', 'def']

# Combinazione di intervalli
re.findall(r"[A-Za-z0-9_]+", "utente_01 email@test.it")
# ['utente_01', 'email', 'test', 'it']
```

#### Classi Predefinite

Python fornisce abbreviazioni comode per le classi di caratteri piu utilizzate:

| Classe | Equivalente | Significato |
|--------|-------------|-------------|
| `\d` | `[0-9]` | Qualsiasi cifra decimale |
| `\D` | `[^0-9]` | Qualsiasi carattere NON cifra |
| `\w` | `[a-zA-Z0-9_]` | Qualsiasi carattere "word" (lettere, cifre, underscore) |
| `\W` | `[^a-zA-Z0-9_]` | Qualsiasi carattere NON "word" |
| `\s` | `[ \t\n\r\f\v]` | Qualsiasi spazio bianco (spazio, tab, newline, ecc.) |
| `\S` | `[^ \t\n\r\f\v]` | Qualsiasi carattere NON spazio bianco |
| `\b` | — | Confine di parola (word boundary) |
| `\B` | — | NON confine di parola |

```python
# \d — cifre
re.findall(r"\d+", "Ordine #4521 del 15/03/2025")
# ['4521', '15', '03', '2025']

# \w — caratteri word
re.findall(r"\w+", "nome_utente = 'Mario'")
# ['nome_utente', 'Mario']

# \s — spazi bianchi
re.split(r"\s+", "parola1   parola2\tparola3\nparola4")
# ['parola1', 'parola2', 'parola3', 'parola4']

# Combinazioni utili
re.findall(r"\b\w{5}\b", "Il gatto nero dorme sulla sedia comoda")
# ['gatto', 'dorme', 'sulla', 'sedia']
```

#### Quantificatori

I quantificatori specificano quante volte un elemento del pattern deve ripetersi.

| Quantificatore | Significato |
|----------------|-------------|
| `*` | Zero o piu volte |
| `+` | Una o piu volte |
| `?` | Zero o una volta (opzionale) |
| `{n}` | Esattamente n volte |
| `{n,}` | Almeno n volte |
| `{n,m}` | Da n a m volte (inclusi) |

```python
# * — zero o piu
re.findall(r"ab*c", "ac abc abbc abbbc")
# ['ac', 'abc', 'abbc', 'abbbc']

# + — uno o piu
re.findall(r"ab+c", "ac abc abbc abbbc")
# ['abc', 'abbc', 'abbbc']

# ? — zero o uno (opzionale)
re.findall(r"colou?r", "color colour")
# ['color', 'colour']

# {n} — esattamente n volte
re.findall(r"\d{4}", "Anno 2025, codice 12345")
# ['2025', '1234']

# {n,m} — da n a m volte
re.findall(r"\d{2,4}", "1 12 123 1234 12345")
# ['12', '123', '1234', '1234']
```

#### Greedy vs Lazy Quantifiers

Per default, i quantificatori sono **greedy** (golosi): cercano di catturare la quantita massima possibile di testo. Aggiungendo `?` dopo un quantificatore, lo si rende **lazy** (pigro): cattura la quantita minima possibile.

```python
testo = "<b>grassetto</b> e <i>corsivo</i>"

# Greedy (default): cattura il piu possibile
re.findall(r"<.+>", testo)
# ['<b>grassetto</b> e <i>corsivo</i>']

# Lazy: cattura il meno possibile
re.findall(r"<.+?>", testo)
# ['<b>', '</b>', '<i>', '</i>']

# Lazy applicato ad altri quantificatori
re.findall(r"\d{2,4}?", "12345")   # {2,4}? prende il minimo: 2
# ['12', '34']

re.findall(r"\d{2,4}", "12345")    # {2,4} prende il massimo: 4
# ['1234']
```

La distinzione greedy/lazy e fondamentale quando si lavora con delimitatori come tag HTML, virgolette o parentesi.

---

### Anchors e Boundaries

Gli anchors non corrispondono a caratteri effettivi ma a **posizioni** all'interno della stringa.

#### `^` (Inizio) e `$` (Fine)

```python
# ^ — la stringa DEVE iniziare con il pattern
re.search(r"^Python", "Python e fantastico")    # Match
re.search(r"^Python", "Io amo Python")           # None

# $ — la stringa DEVE terminare con il pattern
re.search(r"\.py$", "script.py")                 # Match
re.search(r"\.py$", "script.py.bak")             # None

# Combinazione: l'intera stringa deve corrispondere
re.search(r"^\d{5}$", "12345")                   # Match (esattamente 5 cifre)
re.search(r"^\d{5}$", "123456")                  # None
```

#### `\b` (Word Boundary)

Il word boundary `\b` corrisponde alla posizione tra un carattere `\w` e un carattere `\W` (o l'inizio/fine della stringa). E essenziale per cercare parole intere.

```python
# Senza word boundary
re.findall(r"era", "era primavera e c'era una volta")
# ['era', 'era', 'era']  — trova anche "primav-era" e "c'-era"

# Con word boundary
re.findall(r"\bera\b", "era primavera e c'era una volta")
# ['era', 'era']  — trova solo "era" come parola intera

# \B — NON word boundary (posizione interna alla parola)
re.findall(r"\Bera\b", "era primavera e c'era una volta")
# ['era']  — solo "primav-era"
```

#### Modalita Multiline

In modalita multiline, `^` e `$` corrispondono rispettivamente all'inizio e alla fine di ogni riga, non solo dell'intera stringa.

```python
testo = """Prima riga
Seconda riga
Terza riga"""

# Senza MULTILINE: ^ corrisponde solo all'inizio dell'intera stringa
re.findall(r"^\w+", testo)
# ['Prima']

# Con MULTILINE: ^ corrisponde all'inizio di ogni riga
re.findall(r"^\w+", testo, re.MULTILINE)
# ['Prima', 'Seconda', 'Terza']

# Trovare tutte le righe che iniziano con una lettera maiuscola
re.findall(r"^[A-Z].+$", testo, re.MULTILINE)
# ['Prima riga', 'Seconda riga', 'Terza riga']
```

---

### Gruppi e Riferimenti

#### Capturing Groups `()`

Le parentesi tonde creano **gruppi di cattura** che permettono di estrarre porzioni specifiche del match.

```python
# Gruppo di cattura per estrarre parti specifiche
match = re.search(r"(\d{2})/(\d{2})/(\d{4})", "Data: 15/03/2025")
if match:
    giorno = match.group(1)    # '15'
    mese = match.group(2)      # '03'
    anno = match.group(3)      # '2025'
    tutto = match.group(0)     # '15/03/2025' (match intero)

# findall con gruppi restituisce tuple
re.findall(r"(\w+)@(\w+)\.(\w+)", "mario@email.it luca@posta.com")
# [('mario', 'email', 'it'), ('luca', 'posta', 'com')]
```

#### Non-Capturing Groups `(?:...)`

Quando si ha bisogno di raggruppare ma non di catturare, si usano i gruppi non catturanti.

```python
# Gruppo catturante (non desiderato se serve solo il raggruppamento)
re.findall(r"(https?|ftp)://\S+", "Visita https://example.com o ftp://files.it")
# ['https', 'ftp']  — cattura solo il protocollo!

# Gruppo non catturante — il raggruppamento funziona ma non cattura
re.findall(r"(?:https?|ftp)://\S+", "Visita https://example.com o ftp://files.it")
# ['https://example.com', 'ftp://files.it']  — cattura l'intero URL
```

#### Named Groups `(?P<nome>...)`

I gruppi con nome migliorano la leggibilita del codice e permettono l'accesso tramite nome.

```python
pattern = r"(?P<giorno>\d{2})/(?P<mese>\d{2})/(?P<anno>\d{4})"
match = re.search(pattern, "Nato il 25/12/1990")

if match:
    print(match.group("giorno"))   # '25'
    print(match.group("mese"))     # '12'
    print(match.group("anno"))     # '1990'
    print(match.groupdict())       # {'giorno': '25', 'mese': '12', 'anno': '1990'}
```

#### Backreference `\1` e `(?P=nome)`

I riferimenti all'indietro permettono di fare match su testo gia catturato da un gruppo precedente.

```python
# \1 — backreference numerica
# Trova parole duplicate consecutive
re.findall(r"\b(\w+)\s+\1\b", "il il gatto dorme dorme bene")
# ['il', 'dorme']

# (?P=nome) — backreference con nome
pattern = r"(?P<tag>\w+)>.*?</(?P=tag)>"
re.findall(r"<(?P<tag>\w+)>.*?</(?P=tag)>", "<b>testo</b> <i>altro</i>")
# ['b', 'i']

# Uso pratico: trovare stringhe tra virgolette (singole o doppie) corrispondenti
re.findall(r"""(["'])(.+?)\1""", """Disse "ciao" e 'addio'""")
# [('"', 'ciao'), ("'", 'addio')]
```

#### Alternation `|`

L'operatore `|` funziona come un OR logico e puo essere combinato con i gruppi.

```python
# Alternativa semplice
re.findall(r"gatto|cane|pesce", "ho un gatto e un cane")
# ['gatto', 'cane']

# Alternativa dentro un gruppo (per limitare lo scope)
re.findall(r"(?:lun|mar|mer|gio|ven|sab|dom)edi",
           "lunedi martedi mercoledi giovedi venerdi sabato domenica")
# ['lunedi', 'martedi', 'mercoledi', 'giovedi', 'venerdi']
```

---

### Lookahead e Lookbehind

I lookahead e lookbehind sono **asserzioni a larghezza zero**: verificano una condizione senza consumare caratteri nel match. Questo li rende strumenti potentissimi per match condizionali.

#### Positive Lookahead `(?=...)`

Verifica che cio che segue corrisponda al pattern, senza includerlo nel match.

```python
# Trova parole seguite da un numero
re.findall(r"\w+(?=\d)", "item1 item2 nome cognome item3")
# ['item', 'item', 'item']

# Trova importi seguiti da "euro"
re.findall(r"\d+(?=\s*euro)", "Costa 50 euro, non 30 dollari")
# ['50']
```

#### Negative Lookahead `(?!...)`

Verifica che cio che segue NON corrisponda al pattern.

```python
# Trova numeri NON seguiti da "px"
re.findall(r"\d+(?!px)", "10px 20em 30px 40rem")
# ['1', '20', '3', '40']  — nota: '1' da '10' e '3' da '30' (la cifra prima di 'p')

# Versione piu precisa con word boundary
re.findall(r"\b\d+(?!px)\b", "10px 20em 30px 40rem")
# ['20', '40']
```

#### Positive Lookbehind `(?<=...)`

Verifica che cio che precede corrisponda al pattern.

```python
# Trova numeri preceduti dal simbolo euro
re.findall(r"(?<=\$)\d+", "Prezzo: $100 e $250")
# ['100', '250']

# Estrarre il valore dopo "prezzo:"
re.findall(r"(?<=prezzo:\s)\d+", "prezzo: 42")
# ['42']
```

#### Negative Lookbehind `(?<!...)`

Verifica che cio che precede NON corrisponda al pattern.

```python
# Trova numeri NON preceduti dal simbolo $
re.findall(r"(?<!\$)\b\d+\b", "Costo $100 e 250 pezzi")
# ['250']

# Combinazione lookbehind + lookahead
# Trova parole tra parentesi senza includere le parentesi
re.findall(r"(?<=\()[\w\s]+(?=\))", "testo (importante) e altro (fondamentale)")
# ['importante', 'fondamentale']
```

**Nota importante**: in Python, il lookbehind richiede un pattern a lunghezza fissa. Non e possibile usare quantificatori variabili come `*` o `+` nel lookbehind (ad esempio `(?<=\d+)` genera un errore). Si puo pero usare l'alternativa con lunghezze fisse: `(?<=\d{2}|\d{3})`.

---

## Modulo re — Internals

### Architettura del Motore NFA

Il modulo `re` di Python utilizza un motore a **NFA (Non-deterministic Finite Automaton)** con backtracking. Comprendere questo meccanismo e essenziale per scrivere regex efficienti e prevenire problemi di performance.

#### Come Funziona il Matching NFA

Quando il motore incontra un'alternativa (es. `a|b`, oppure un quantificatore greedy come `.*`), salva un **punto di ritorno** (backtrack point). Se il percorso corrente fallisce, il motore torna all'ultimo punto di ritorno e prova l'alternativa successiva. Questo processo si chiama **backtracking**.

```python
import re

# Il motore prova "a" prima, poi "ab" se "a" da solo non porta a un match completo
pattern = re.compile(r"(a|ab)c")

# Tracciamo il comportamento:
# Input: "abc"
# 1. Prova "a" → match "a", poi cerca "c" → trova "b", fallisce
# 2. Backtrack → prova "ab" → match "ab", poi cerca "c" → trova "c", successo!
match = pattern.search("abc")
print(match.group())  # "abc"
```

#### NFA vs DFA

I motori regex si dividono in due famiglie:

| Caratteristica | NFA (Python `re`) | DFA (`re2`, `grep -E`) |
|---|---|---|
| Backtracking | Si | No |
| Backreference | Supportate | Non supportate |
| Lookahead/Lookbehind | Supportati | Non supportati |
| Complessita nel caso peggiore | Esponenziale O(2^n) | Lineare O(n) |
| Cattura gruppi | Si | Limitata |
| Possessive quantifiers | No (serve `regex`) | N/A |

Python ha scelto NFA perche supporta tutte le funzionalita avanzate (backreference, lookaround), ma questo significa che pattern mal costruiti possono causare tempi di esecuzione esponenziali.

#### La Cache Interna di `re`

Il modulo `re` mantiene una **LRU cache** dei pattern compilati. Il comportamento e cambiato nelle diverse versioni di Python:

```python
import re

# Python 3.12+: la cache contiene fino a 512 pattern
# Le funzioni re.match(), re.search(), ecc. compilano e cacheano implicitamente

# Verifica della cache interna (implementazione CPython)
print(re._cache)         # dizionario dei pattern cacheati
print(re._MAXCACHE)      # 512 (default)

# Pulizia manuale della cache
re.purge()

# BEST PRACTICE: per pattern usati in loop, precompilare esplicitamente
# e meno soggetto a eviction dalla cache
pattern_log = re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}")

# Nota: la precompilazione esplicita NON passa per la cache,
# l'oggetto compilato e una variabile locale o di modulo
```

#### Fasi della Compilazione

Quando si chiama `re.compile()`, il pattern attraversa quattro fasi:

1. **Parsing** — Il pattern stringa viene trasformato in un AST (Abstract Syntax Tree) dal parser interno (`sre_parse`).
2. **Ottimizzazione** — L'AST viene ottimizzato: ancore ridondanti rimosse, classi di caratteri semplificate.
3. **Compilazione** — L'AST viene compilato in bytecode specifico per il motore regex (`sre_compile`).
4. **Esecuzione** — Il bytecode viene eseguito dal motore C (`_sre`) contro la stringa di input.

```python
import sre_parse

# Ispezione dell'AST di un pattern
parsed = sre_parse.parse(r"(\d{3})-(\d{4})")
print(parsed.dump())
# Mostra la struttura interna del pattern compilato

# Il bytecode compilato e accessibile (ma non documentato)
pattern = re.compile(r"(\d{3})-(\d{4})")
print(pattern.pattern)   # il pattern originale
print(pattern.flags)     # le flag attive
print(pattern.groups)    # numero di gruppi: 2
print(pattern.groupindex)  # dict vuoto (nessun named group)
```

---

### Funzioni Principali

#### `re.match()` vs `re.search()` vs `re.fullmatch()`

Tre funzioni fondamentali con comportamento distinto:

```python
testo = "Python 3.12 e fantastico"

# re.match() — cerca SOLO all'inizio della stringa
re.match(r"Python", testo)      # Match! (inizia con "Python")
re.match(r"fantastico", testo)  # None (non inizia con "fantastico")

# re.search() — cerca la PRIMA occorrenza in qualsiasi posizione
re.search(r"Python", testo)      # Match
re.search(r"fantastico", testo)  # Match (trovato nella stringa)
re.search(r"\d+\.\d+", testo)   # Match: '3.12'

# re.fullmatch() — l'INTERA stringa deve corrispondere al pattern
re.fullmatch(r"\d+", "12345")     # Match
re.fullmatch(r"\d+", "123abc")    # None (non tutta la stringa e fatta di cifre)
re.fullmatch(r".+", testo)        # Match (qualsiasi stringa non vuota)
```

**Regola pratica**: usare `match()` per verificare il prefisso, `search()` per cercare in qualsiasi punto, `fullmatch()` per validare l'intera stringa.

#### `re.findall()` e `re.finditer()`

```python
testo = "Temperatura: 22.5C alle 14:30, poi 18.3C alle 20:00"

# findall — restituisce una lista di tutte le corrispondenze
re.findall(r"\d+\.\d+", testo)
# ['22.5', '18.3']

# Con gruppi, findall restituisce i contenuti dei gruppi
re.findall(r"(\d+):(\d+)", testo)
# [('14', '30'), ('20', '00')]

# finditer — restituisce un iteratore di Match object
# Piu efficiente per grandi dataset e fornisce piu informazioni
for match in re.finditer(r"\d+\.\d+", testo):
    print(f"Trovato '{match.group()}' alla posizione {match.start()}-{match.end()}")
# Trovato '22.5' alla posizione 14-18
# Trovato '18.3' alla posizione 35-39
```

`finditer` e preferibile quando si lavora con testi molto grandi, poiche non crea l'intera lista in memoria, oppure quando servono informazioni sulla posizione del match.

#### `re.sub()` e `re.subn()`

```python
# sub — sostituzione con stringa
testo = "Contattare il 333-1234567 oppure il 06-12345678"
re.sub(r"\d", "X", testo)
# 'Contattare il XXX-XXXXXXX oppure il XX-XXXXXXXX'

# sub con limitazione del numero di sostituzioni
re.sub(r"\d", "X", testo, count=5)
# 'Contattare il XXX-XXXXX67 oppure il 06-12345678'

# sub con riferimento ai gruppi nella stringa di sostituzione
date = "2025-03-15 e 2025-12-25"
re.sub(r"(\d{4})-(\d{2})-(\d{2})", r"\3/\2/\1", date)
# '15/03/2025 e 25/12/2025'

# sub con funzione di callback
def doppio(match):
    return str(int(match.group()) * 2)

re.sub(r"\d+", doppio, "Ho 3 gatti e 5 cani")
# 'Ho 6 gatti e 10 cani'

# sub con named group
re.sub(r"(?P<nome>\w+)@(?P<dominio>\w+\.\w+)",
       r"\g<nome> [at] \g<dominio>",
       "scrivi a mario@email.it")
# 'scrivi a mario [at] email.it'

# subn — come sub, ma restituisce anche il numero di sostituzioni effettuate
risultato, n_sostituzioni = re.subn(r"\d", "X", "abc123def456")
# risultato = 'abcXXXdefXXX', n_sostituzioni = 6
```

#### `re.split()`

```python
# Split con regex — molto piu potente di str.split()
re.split(r"\s+", "parole   con  molti    spazi")
# ['parole', 'con', 'molti', 'spazi']

# Split con separatori multipli
re.split(r"[;,\s]+", "mela, pera; banana   kiwi")
# ['mela', 'pera', 'banana', 'kiwi']

# Split con cattura del separatore (usando gruppi)
re.split(r"(\s*;\s*|\s*,\s*)", "a, b; c,d")
# ['a', ', ', 'b', '; ', 'c', ',', 'd']

# Limitare il numero di split
re.split(r":", "uno:due:tre:quattro", maxsplit=2)
# ['uno', 'due', 'tre:quattro']
```

#### `re.compile()` — Precompilazione

Quando un pattern viene utilizzato ripetutamente, conviene precompilarlo in un oggetto regex. Questo evita la ri-compilazione ad ogni chiamata e migliora le prestazioni.

```python
# Compilazione del pattern
pattern_email = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

# Uso dell'oggetto compilato (stessi metodi del modulo re)
emails = [
    "mario.rossi@email.it",
    "non-una-email",
    "luca@posta.com",
    "invalido@",
]

for email in emails:
    if pattern_email.fullmatch(email):
        print(f"  Valida: {email}")
    else:
        print(f"  Invalida: {email}")

# L'oggetto compilato supporta tutti i metodi
pattern_numero = re.compile(r"\d+")
pattern_numero.findall("abc 123 def 456")     # ['123', '456']
pattern_numero.sub("NUM", "abc 123 def 456")  # 'abc NUM def NUM'
pattern_numero.split("abc123def456ghi")        # ['abc', 'def', 'ghi']
```

**Nota sulle prestazioni**: Python mantiene una cache interna dei pattern compilati recentemente (fino a 512 pattern). La precompilazione esplicita e comunque consigliata per chiarezza e per pattern utilizzati in loop.

---

### Flag

Le flag modificano il comportamento del motore regex. Possono essere passate come argomento alle funzioni `re` oppure inserite direttamente nel pattern con la sintassi inline `(?flag)`.

#### `re.IGNORECASE` (`re.I`)

Rende il matching case-insensitive.

```python
re.findall(r"python", "Python PYTHON python PyThOn", re.IGNORECASE)
# ['Python', 'PYTHON', 'python', 'PyThOn']

# Sintassi inline equivalente
re.findall(r"(?i)python", "Python PYTHON python")
# ['Python', 'PYTHON', 'python']
```

#### `re.MULTILINE` (`re.M`)

Fa si che `^` e `$` corrispondano all'inizio e alla fine di ogni riga.

```python
testo = """# Titolo
Paragrafo 1
# Sottotitolo
Paragrafo 2"""

re.findall(r"^# .+$", testo, re.MULTILINE)
# ['# Titolo', '# Sottotitolo']
```

#### `re.DOTALL` (`re.S`)

Fa si che `.` corrisponda anche al carattere newline `\n`.

```python
testo = """<div>
contenuto
multiriga
</div>"""

# Senza DOTALL: il punto non cattura i newline
re.findall(r"<div>(.+)</div>", testo)
# []

# Con DOTALL: il punto cattura anche i newline
re.findall(r"<div>(.+)</div>", testo, re.DOTALL)
# ['\ncontenuto\nmultiriga\n']
```

#### `re.VERBOSE` (`re.X`)

Permette di scrivere regex leggibili, con commenti e spaziatura ignorata. E una best practice per pattern complessi.

```python
pattern_email = re.compile(r"""
    ^                       # Inizio stringa
    [a-zA-Z0-9._%+-]+      # Nome utente: alfanumerici e caratteri speciali
    @                       # Simbolo @ (obbligatorio)
    [a-zA-Z0-9.-]+         # Nome dominio
    \.                      # Punto prima dell'estensione
    [a-zA-Z]{2,}           # Estensione dominio (almeno 2 caratteri)
    $                       # Fine stringa
""", re.VERBOSE)

pattern_email.match("utente@dominio.it")   # Match
```

#### `re.ASCII` (`re.A`)

Forza le classi `\w`, `\b`, `\d`, `\s` a fare match solo su caratteri ASCII (disattivando il matching Unicode di default in Python 3).

```python
# Di default, \w include anche caratteri Unicode (lettere accentate, ecc.)
re.findall(r"\w+", "cafe resume")
# ['cafe', 'resume'] — ma con accenti: re.findall(r"\w+", "cafe resume")

# Con re.ASCII, solo caratteri ASCII
re.findall(r"\w+", "cafe naif", re.ASCII)
# ['caf', 'naif'] — la 'e' accentata non e \w in modalita ASCII
```

#### Combinazione di Flag

Le flag possono essere combinate con l'operatore bitwise OR `|`.

```python
# Combinare MULTILINE e IGNORECASE
testo = """Python e potente
PYTHON E VELOCE
python e semplice"""

re.findall(r"^python.+$", testo, re.MULTILINE | re.IGNORECASE)
# ['Python e potente', 'PYTHON E VELOCE', 'python e semplice']

# Combinazione inline
re.findall(r"(?mi)^python.+$", testo)
# Stesso risultato
```

---

### Match Object

Quando `re.match()`, `re.search()` o `re.finditer()` trovano una corrispondenza, restituiscono un **Match object** che fornisce informazioni dettagliate sul match.

#### `group()`, `groups()`, `groupdict()`

```python
pattern = r"(?P<nome>\w+)\s+(?P<cognome>\w+),\s+eta:\s+(?P<eta>\d+)"
match = re.search(pattern, "Mario Rossi, eta: 35")

if match:
    # group() senza argomenti o group(0) — l'intero match
    match.group()       # 'Mario Rossi, eta: 35'
    match.group(0)      # 'Mario Rossi, eta: 35'

    # group(n) — il gruppo n-esimo
    match.group(1)      # 'Mario'
    match.group(2)      # 'Rossi'
    match.group(3)      # '35'

    # group con nome
    match.group("nome")     # 'Mario'
    match.group("cognome")  # 'Rossi'
    match.group("eta")      # '35'

    # groups() — tuple di tutti i gruppi catturati
    match.groups()      # ('Mario', 'Rossi', '35')

    # groupdict() — dizionario dei named groups
    match.groupdict()   # {'nome': 'Mario', 'cognome': 'Rossi', 'eta': '35'}
```

#### `start()`, `end()`, `span()`

```python
testo = "Il codice e ABC-1234 trovato qui"
match = re.search(r"[A-Z]+-\d+", testo)

if match:
    match.start()    # 12  (indice di inizio del match)
    match.end()      # 20  (indice di fine del match, esclusivo)
    match.span()     # (12, 20)  (tuple inizio, fine)

    # Funziona anche per singoli gruppi
    # match.start(1), match.end(1), match.span(1)
```

---

## Pattern Pratici

In questa sezione sono raccolti pattern regex pronti all'uso per scenari comuni, ciascuno con spiegazione dettagliata.

### Validazione Email

```python
pattern_email = re.compile(r"""
    ^
    [a-zA-Z0-9._%+-]+       # Parte locale: lettere, numeri, ._%+-
    @                         # Separatore @
    [a-zA-Z0-9.-]+           # Dominio: lettere, numeri, .-
    \.                        # Punto obbligatorio
    [a-zA-Z]{2,}             # TLD: almeno 2 lettere
    $
""", re.VERBOSE)

# Test
assert pattern_email.match("mario.rossi@email.it")
assert pattern_email.match("nome+tag@dominio.co.uk")
assert not pattern_email.match("senza-chiocciola.it")
assert not pattern_email.match("@manca-locale.it")
```

**Nota**: la validazione email perfetta secondo RFC 5322 e estremamente complessa. Per scopi pratici, questo pattern copre la grande maggioranza dei casi. In produzione, e consigliabile inviare un'email di verifica piuttosto che affidarsi solo alla regex.

### Parsing URL

```python
pattern_url = re.compile(r"""
    (?P<protocollo>https?|ftp)     # Protocollo: http, https, ftp
    ://                             # Separatore
    (?P<dominio>[a-zA-Z0-9.-]+)    # Nome dominio
    (?::(?P<porta>\d+))?           # Porta (opzionale)
    (?P<percorso>/[^\s?#]*)?       # Percorso (opzionale)
    (?:\?(?P<query>[^\s#]*))?      # Query string (opzionale)
    (?:\#(?P<frammento>[^\s]*))?   # Frammento (opzionale)
""", re.VERBOSE)

match = pattern_url.search("Visita https://www.example.com:8080/pagina?q=test#sezione")
if match:
    print(match.groupdict())
    # {'protocollo': 'https', 'dominio': 'www.example.com', 'porta': '8080',
    #  'percorso': '/pagina', 'query': 'q=test', 'frammento': 'sezione'}
```

### Indirizzo IP (IPv4 e IPv6)

```python
# IPv4 — ogni ottetto da 0 a 255
pattern_ipv4 = re.compile(r"""
    ^
    (?:
        (?:25[0-5]|2[0-4]\d|[01]?\d\d?)   # Ottetto: 0-255
        \.                                   # Separatore punto
    ){3}                                     # Ripetuto 3 volte (primi 3 ottetti + punto)
    (?:25[0-5]|2[0-4]\d|[01]?\d\d?)        # Ultimo ottetto (senza punto finale)
    $
""", re.VERBOSE)

assert pattern_ipv4.match("192.168.1.1")
assert pattern_ipv4.match("0.0.0.0")
assert pattern_ipv4.match("255.255.255.255")
assert not pattern_ipv4.match("256.1.1.1")
assert not pattern_ipv4.match("192.168.1")

# IPv6 — forma semplificata (8 gruppi di 4 cifre hex)
pattern_ipv6 = re.compile(r"""
    ^
    (?:[0-9a-fA-F]{1,4}:){7}    # 7 gruppi di 1-4 cifre hex seguiti da :
    [0-9a-fA-F]{1,4}            # Ultimo gruppo
    $
""", re.VERBOSE)

assert pattern_ipv6.match("2001:0db8:85a3:0000:0000:8a2e:0370:7334")
```

### Numero di Telefono (Formato Italiano)

```python
pattern_telefono_it = re.compile(r"""
    ^
    (?:\+39\s?)?                   # Prefisso internazionale +39 (opzionale)
    (?:
        0\d{1,4}                   # Prefisso fisso (0 + 1-4 cifre)
        [\s.-]?                    # Separatore opzionale
        \d{5,8}                    # Numero fisso (5-8 cifre)
        |
        3[0-9]{1,2}               # Prefisso mobile (3xx)
        [\s.-]?                    # Separatore opzionale
        \d{6,8}                    # Numero mobile (6-8 cifre)
    )
    $
""", re.VERBOSE)

assert pattern_telefono_it.match("+39 02 12345678")    # Fisso Milano
assert pattern_telefono_it.match("333 1234567")         # Mobile
assert pattern_telefono_it.match("+39 06 1234567")      # Fisso Roma
assert pattern_telefono_it.match("3401234567")           # Mobile senza spazi
```

### Formati Data

```python
# Formato dd/mm/yyyy (italiano) con validazione di base
pattern_data_it = re.compile(r"""
    ^
    (?:0[1-9]|[12]\d|3[01])       # Giorno: 01-31
    [/\-.]                          # Separatore: / - .
    (?:0[1-9]|1[0-2])             # Mese: 01-12
    [/\-.]                          # Separatore
    (?:19|20)\d{2}                 # Anno: 1900-2099
    $
""", re.VERBOSE)

assert pattern_data_it.match("15/03/2025")
assert pattern_data_it.match("01-12-1999")
assert not pattern_data_it.match("32/01/2025")   # Giorno > 31

# Formato yyyy-mm-dd (ISO 8601)
pattern_data_iso = re.compile(r"""
    ^
    (?:19|20)\d{2}                 # Anno
    -
    (?:0[1-9]|1[0-2])             # Mese
    -
    (?:0[1-9]|[12]\d|3[01])       # Giorno
    $
""", re.VERBOSE)

assert pattern_data_iso.match("2025-03-15")
```

### Validazione Robustezza Password

```python
pattern_password = re.compile(r"""
    ^
    (?=.*[a-z])             # Almeno una lettera minuscola (lookahead)
    (?=.*[A-Z])             # Almeno una lettera maiuscola (lookahead)
    (?=.*\d)                # Almeno una cifra (lookahead)
    (?=.*[!@\#$%^&*(),.?]) # Almeno un carattere speciale (lookahead)
    .{8,}                   # Lunghezza minima 8 caratteri
    $
""", re.VERBOSE)

assert pattern_password.match("Sicura1!")
assert pattern_password.match("P@ssw0rd123")
assert not pattern_password.match("senzamaiuscole1!")
assert not pattern_password.match("SENZAMINUSCOLE1!")
assert not pattern_password.match("SenzaNumeri!")
assert not pattern_password.match("Corta1!")    # Troppo corta (7 caratteri)
```

### Parsing Righe di Log

```python
# Formato Apache Common Log
pattern_apache = re.compile(r"""
    (?P<ip>\S+)                    # IP del client
    \s+\S+\s+\S+\s+               # Identita e utente (spesso -)
    \[(?P<data>[^\]]+)\]           # Data tra parentesi quadre
    \s+"(?P<metodo>\w+)            # Metodo HTTP
    \s+(?P<url>\S+)               # URL richiesto
    \s+\S+"\s+                     # Protocollo HTTP
    (?P<status>\d{3})              # Codice di stato
    \s+(?P<dimensione>\d+|-)       # Dimensione risposta
""", re.VERBOSE)

riga_log = '192.168.1.1 - - [15/Mar/2025:10:30:00 +0100] "GET /index.html HTTP/1.1" 200 1234'
match = pattern_apache.search(riga_log)
if match:
    print(match.groupdict())
    # {'ip': '192.168.1.1', 'data': '15/Mar/2025:10:30:00 +0100',
    #  'metodo': 'GET', 'url': '/index.html', 'status': '200', 'dimensione': '1234'}

# Formato syslog
pattern_syslog = re.compile(r"""
    (?P<data>\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})  # Data: "Mar 15 10:30:00"
    \s+(?P<host>\S+)                                   # Hostname
    \s+(?P<processo>\S+?)                              # Nome processo
    (?:\[(?P<pid>\d+)\])?                              # PID (opzionale)
    :\s+(?P<messaggio>.+)                              # Messaggio
""", re.VERBOSE)
```

### Estrazione Campi CSV

```python
# Gestisce campi tra virgolette che possono contenere virgole
pattern_csv = re.compile(r"""
    (?:^|,)                      # Inizio stringa o virgola separatrice
    (?:
        "([^"]*(?:""[^"]*)*)"    # Campo tra virgolette (con escape "")
        |                         # oppure
        ([^,]*)                   # Campo senza virgolette
    )
""", re.VERBOSE)

riga = '"Mario Rossi","Via Roma, 10","Milano"'
campi = [g1 or g2 for g1, g2 in pattern_csv.findall(riga)]
# ['Mario Rossi', 'Via Roma, 10', 'Milano']
```

**Nota**: per il parsing CSV reale, e fortemente consigliato usare il modulo `csv` della libreria standard, che gestisce correttamente tutti i casi limite.

### Estrazione Tag HTML

```python
# Pattern base per tag HTML (solo per casi semplici)
pattern_tag = re.compile(r"""
    <                        # Apertura tag
    (?P<chiusura>/)?         # Slash di chiusura (opzionale)
    (?P<tag>[a-zA-Z]\w*)     # Nome del tag
    (?P<attributi>[^>]*)     # Attributi (tutto fino a >)
    /?>                      # Chiusura tag (con possibile />)
""", re.VERBOSE)

html = '<div class="contenitore"><p>Testo</p></div><br/>'
for match in pattern_tag.finditer(html):
    print(match.groupdict())
# {'chiusura': None, 'tag': 'div', 'attributi': ' class="contenitore"'}
# {'chiusura': None, 'tag': 'p', 'attributi': ''}
# {'chiusura': '/', 'tag': 'p', 'attributi': ''}
# {'chiusura': '/', 'tag': 'div', 'attributi': ''}
# {'chiusura': None, 'tag': 'br', 'attributi': ''}
```

**Avvertenza importante**: le regex NON sono lo strumento adeguato per il parsing completo dell'HTML. L'HTML non e un linguaggio regolare e i casi limite sono innumerevoli. Per il parsing HTML reale, utilizzare librerie dedicate come `BeautifulSoup` o `lxml`.

### Numero Carta di Credito

```python
pattern_cc = re.compile(r"""
    ^
    (?:
        4\d{12}(?:\d{3})?           # Visa: inizia con 4, 13 o 16 cifre
        |
        5[1-5]\d{14}                # MasterCard: inizia con 51-55, 16 cifre
        |
        3[47]\d{13}                 # American Express: inizia con 34 o 37, 15 cifre
        |
        6(?:011|5\d{2})\d{12}      # Discover: inizia con 6011 o 65, 16 cifre
    )
    $
""", re.VERBOSE)
```

**Nota**: la validazione completa di un numero di carta di credito richiede anche l'algoritmo di Luhn (checksum), che non e implementabile con le sole regex.

### Codice Fiscale Italiano

```python
pattern_cf = re.compile(r"""
    ^
    [A-Z]{6}          # 6 lettere: 3 per cognome + 3 per nome
    \d{2}             # Anno di nascita (2 cifre)
    [ABCDEHLMPRST]    # Mese di nascita (lettera codificata)
    \d{2}             # Giorno di nascita (01-71; femmine: giorno + 40)
    [A-Z]\d{3}        # Comune: lettera + 3 cifre (codice catastale)
    [A-Z]             # Carattere di controllo
    $
""", re.VERBOSE | re.IGNORECASE)

assert pattern_cf.match("RSSMRA85M01H501Z")  # Esempio fittizio
assert not pattern_cf.match("RSSMRA85X01H501Z")  # 'X' non e un mese valido
```

---

## Atomic Groups e Possessive Quantifiers

Il modulo `re` della libreria standard **non supporta** atomic groups ne possessive quantifiers. Queste funzionalita sono disponibili tramite il modulo terze parti `regex` (drop-in replacement di `re`).

### Il Problema: Backtracking Inutile

Consideriamo un pattern greedy: quando il quantificatore ha consumato troppo, il motore fa backtracking per provare match piu corti. In molti casi, questo backtracking e inutile perche sappiamo che la prima scelta era quella corretta.

```python
# Con re standard: il .* consuma tutto, poi fa backtracking carattere per carattere
# per trovare "foo" alla fine
import re

testo = "a" * 1000 + "foo"
pattern = re.compile(r".*foo")
# Funziona ma il .* fa backtracking 1000 volte prima di trovare "foo"
match = pattern.search(testo)
```

### Atomic Groups `(?>...)`

Un atomic group impedisce il backtracking al suo interno. Una volta che il motore ha trovato un match per il contenuto del gruppo, non torna piu indietro per provare alternative.

```python
import regex  # pip install regex

# SENZA atomic group: backtracking normale
# Il motore prova tutte le combinazioni di a+
pattern_normale = regex.compile(r"(a+)ab")
# Con "aaab": a+ cattura "aaa", poi cerca "ab" → fallisce
# Backtrack: a+ cattura "aa", poi cerca "ab" → match!

# CON atomic group: nessun backtracking dentro (?>...)
pattern_atomico = regex.compile(r"(?>a+)ab")
# Con "aaab": a+ cattura "aaab", poi cerca "ab" → fallisce
# Nessun backtracking dentro l'atomic group → match fallisce completamente

print(pattern_normale.search("aaab"))    # Match
print(pattern_atomico.search("aaab"))    # None
```

### Possessive Quantifiers `*+`, `++`, `?+`

I possessive quantifiers sono zucchero sintattico per atomic groups. `a++` equivale a `(?>a+)`: il quantificatore consuma tutto il possibile e non rilascia mai caratteri tramite backtracking.

```python
import regex

# Quantificatori standard vs possessive
# *  → greedy, puo rilasciare (backtrack)
# *? → lazy, espande su richiesta
# *+ → possessive, non rilascia mai

# Esempio: validazione di stringhe tra virgolette
# Pattern standard — puo causare backtracking
pattern_greedy = regex.compile(r'"[^"]*"')

# Pattern possessive — piu efficiente, nessun backtracking
pattern_possessive = regex.compile(r'"[^"]*+"')

# Entrambi producono lo stesso risultato su input valido
testo = '"ciao mondo" e "altro testo"'
print(regex.findall(r'"[^"]*"', testo))    # ['"ciao mondo"', '"altro testo"']
print(regex.findall(r'"[^"]*+"', testo))   # ['"ciao mondo"', '"altro testo"']

# La differenza emerge con input che NON fanno match:
# il possessive fallisce immediatamente senza backtracking
```

### Tabella Riassuntiva

| Quantificatore | Nome | Comportamento |
|---|---|---|
| `a*` | Greedy | Cattura il massimo, rilascia tramite backtracking |
| `a*?` | Lazy | Cattura il minimo, espande su richiesta |
| `a*+` | Possessive | Cattura il massimo, non rilascia MAI |
| `(?>a*)` | Atomic group | Equivalente a `a*+` |

### Quando Usare Possessive/Atomic

- **Pattern di validazione** dove il fallimento deve essere rapido: `^[a-zA-Z]++$`
- **Pattern con classi di caratteri non sovrapposte**: `[^"]*+"` (il `"` finale non puo mai essere consumato dal `[^"]*+`)
- **Prevenzione di ReDoS** in contesti dove si processano input non fidati

```python
import regex

# Esempio sicuro per parsing di campi delimitati
pattern_csv = regex.compile(r"""
    (?:^|,)
    (?:
        "([^"]*+)"     # campo tra virgolette (possessive)
        |
        ([^,]*+)       # campo senza virgolette (possessive)
    )
""", regex.VERBOSE)
```

---

## Performance Regex

### Catastrophic Backtracking

Il catastrophic backtracking (noto anche come **ReDoS — Regular Expression Denial of Service**) si verifica quando un pattern regex causa un numero esponenziale di combinazioni di backtracking su determinati input. E uno dei problemi di sicurezza piu insidiosi legati alle regex.

#### Come Si Verifica

Il problema emerge quando:
1. Il pattern contiene **quantificatori annidati** (es. `(a+)+`)
2. Il pattern contiene **alternative sovrapposte** (es. `(a|a)+`)
3. L'input non corrisponde al pattern, forzando il motore a esplorare tutte le combinazioni

```python
import re
import time

# PATTERN PERICOLOSO: quantificatori annidati
# (a+)+ su input "aaaaaaaaaaaaaaaaaaaX" causa backtracking esponenziale
pattern_pericoloso = re.compile(r"^(a+)+$")

# Misura il tempo con input crescente
for n in [10, 15, 20, 22, 24]:
    input_str = "a" * n + "X"
    inizio = time.perf_counter()
    pattern_pericoloso.search(input_str)
    durata = time.perf_counter() - inizio
    print(f"n={n:2d}: {durata:.4f}s")
    if durata > 5:
        print("  TROPPO LENTO — interrotto")
        break

# Output tipico:
# n=10: 0.0001s
# n=15: 0.0028s
# n=20: 0.0879s
# n=22: 0.3521s
# n=24: 1.4082s  ← cresce esponenzialmente!
```

#### Pattern Comuni Vulnerabili

```python
# TUTTI QUESTI PATTERN SONO VULNERABILI A ReDoS:

# 1. Quantificatori annidati
r"(a+)+"           # a+ ripetuto con +
r"(a*)*"           # a* ripetuto con *
r"(a+)*"           # a+ ripetuto con *
r"(a|b+)+"         # alternativa con quantificatore annidato

# 2. Alternative sovrapposte
r"(a|a)+"          # entrambe le alternative matchano 'a'
r"(\w+|\d+)+"      # \d e sottoinsieme di \w

# 3. Pattern di validazione email naive
r"^([a-zA-Z0-9]+\.)+[a-zA-Z]{2,}$"  # pericoloso!

# CORREZIONI:
# 1. Rimuovere i quantificatori annidati
r"a+"              # equivalente semplice
# 2. Rendere le alternative non sovrapposte
r"[ab]+"           # classe di caratteri al posto di alternativa
# 3. Usare atomic groups (con modulo regex)
# oppure riformulare senza ambiguita
```

#### Difese Contro il ReDoS

```python
import re
import signal

# 1. TIMEOUT — interrompi il matching dopo N secondi
class RegexTimeout(Exception):
    pass

def handler_timeout(signum, frame):
    raise RegexTimeout("Timeout regex")

def match_con_timeout(pattern, testo, timeout_sec=2):
    """Esegue il matching con un timeout di sicurezza."""
    old_handler = signal.signal(signal.SIGALRM, handler_timeout)
    signal.alarm(timeout_sec)
    try:
        return pattern.search(testo)
    except RegexTimeout:
        return None
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

# 2. LIMITAZIONE LUNGHEZZA INPUT
def match_sicuro(pattern, testo, max_lunghezza=10000):
    """Rifiuta input troppo lunghi prima del matching."""
    if len(testo) > max_lunghezza:
        raise ValueError(f"Input troppo lungo: {len(testo)} > {max_lunghezza}")
    return pattern.search(testo)

# 3. USARE re2 per input non fidato (vedi sezione Alternative)
```

### Cache e Compilazione

#### Quando Precompilare

La precompilazione con `re.compile()` e consigliata quando:
- Il pattern e usato in un **loop** o in una funzione chiamata ripetutamente
- Si vuole **assegnare un nome significativo** al pattern
- Si vogliono **specificare le flag** una volta sola

```python
import re

# ANTI-PATTERN: compilazione ripetuta nel loop
def cerca_errori_lento(righe: list[str]) -> list[str]:
    risultati = []
    for riga in righe:
        # re.search() compila il pattern internamente ogni volta
        # (la cache mitiga il costo, ma e meno esplicito)
        if re.search(r"ERROR\s+\d+:\s+(.+)", riga):
            risultati.append(riga)
    return risultati

# PATTERN CORRETTO: compilazione una volta sola
PATTERN_ERRORE = re.compile(r"ERROR\s+\d+:\s+(.+)")

def cerca_errori_veloce(righe: list[str]) -> list[str]:
    risultati = []
    for riga in righe:
        if PATTERN_ERRORE.search(riga):
            risultati.append(riga)
    return risultati

# Ancora meglio: list comprehension con pattern precompilato
def cerca_errori_idiomatico(righe: list[str]) -> list[str]:
    return [riga for riga in righe if PATTERN_ERRORE.search(riga)]
```

#### Organizzazione dei Pattern nel Progetto

```python
# patterns.py — modulo centralizzato per i pattern regex del progetto

import re

# Pattern di validazione
EMAIL = re.compile(
    r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
)
CODICE_FISCALE = re.compile(
    r"^[A-Z]{6}\d{2}[ABCDEHLMPRST]\d{2}[A-Z]\d{3}[A-Z]$",
    re.IGNORECASE
)
PARTITA_IVA = re.compile(r"^\d{11}$")

# Pattern di parsing
LOG_STANDARD = re.compile(
    r"(?P<data>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+"
    r"(?P<livello>DEBUG|INFO|WARNING|ERROR|CRITICAL)\s+"
    r"\[(?P<sorgente>[^\]]+)\]\s+"
    r"(?P<messaggio>.+)"
)

# Pattern di estrazione
IPV4 = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}"
    r"(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"
)
```

### Benchmark e Profilazione

```python
import re
import timeit

# Confronto tra pattern equivalenti con performance diverse
testo = "utente_12345@dominio.example.com"

# Pattern 1: con backtracking potenziale
p1 = re.compile(r"(.+)@(.+)\.(.+)")

# Pattern 2: con classi di caratteri specifiche (piu efficiente)
p2 = re.compile(r"([^@]+)@([^.]+)\.(.+)")

# Pattern 3: con possessive (richiede regex)
# p3 = regex.compile(r"([^@]++)@([^.]++)\.(.+)")

# Benchmark
tempo1 = timeit.timeit(lambda: p1.search(testo), number=100000)
tempo2 = timeit.timeit(lambda: p2.search(testo), number=100000)
print(f"Pattern generico (.+):   {tempo1:.4f}s")
print(f"Pattern specifico ([^@]+): {tempo2:.4f}s")
# Il pattern con classi negated e tipicamente 2-5x piu veloce

# Profilazione dettagliata con re.DEBUG
re.compile(r"(?P<utente>[^@]+)@(?P<dominio>[^.]+)\.(?P<tld>.+)", re.DEBUG)
# Mostra il bytecode generato dal compilatore regex
```

---

## Alternative a re

### regex (modulo terze parti)

Il modulo `regex` (installabile con `pip install regex`) e un **drop-in replacement** di `re` che aggiunge funzionalita assenti nella libreria standard, mantenendo piena compatibilita con l'API di `re`.

```python
import regex  # pip install regex

# 1. Atomic groups e possessive quantifiers
pattern = regex.compile(r"(?>a+)b")

# 2. Unicode categories e script properties
# \p{L} — qualsiasi lettera Unicode (qualsiasi script)
# \p{Cyrillic} — solo caratteri cirillici
# \p{Han} — caratteri cinesi
regex.findall(r"\p{L}+", "Hello Мир 世界")
# ['Hello', 'Мир', '世界']

# 3. Fuzzy matching (matching approssimato)
pattern_fuzzy = regex.compile(r"(programmazione){e<=2}")
# Consente fino a 2 errori (inserzioni, delezioni, sostituzioni)
match = pattern_fuzzy.search("programazione")  # 1 lettera mancante
print(match.group())  # "programazione"
print(match.fuzzy_counts)  # (0, 1, 0) — 0 sostituzioni, 1 delezione, 0 inserzioni

# 4. Overlapping matches
regex.findall(r"\w{3}", "abcdef", overlapped=True)
# ['abc', 'bcd', 'cde', 'def']

# 5. Nested sets e set operations
# [a-z&&[^aeiou]] — consonanti (intersezione e negazione)
regex.findall(r"[\p{L}&&[^\p{Lu}]]+", "Hello MONDO ciao")
# ['ello', 'ciao']  — solo lettere minuscole

# 6. Branch reset groups (?|...)
# I gruppi in alternative diverse condividono lo stesso numero
pattern = regex.compile(r"(?|(\d+)-(\d+)|(\w+):(\w+))")
```

### regex (mrab-regex) — Approfondimento Completo

Il modulo `regex` (noto anche come `mrab-regex`, dal nome del suo autore Matthew Barnett) merita un approfondimento dedicato poiche rappresenta il superset piu completo e maturo di `re` disponibile nell'ecosistema Python. A differenza di `re`, che evolve lentamente per ragioni di retrocompatibilita, `regex` integra funzionalita provenienti da altri motori regex (Perl, .NET, Java) in un'unica libreria coerente.

#### Fuzzy Matching Avanzato

Il fuzzy matching del modulo `regex` consente di trovare corrispondenze approssimate, specificando il numero massimo di errori ammessi per tipo: inserzioni (i), delezioni (d) e sostituzioni (s). Questo e fondamentale per scenari reali in cui i dati contengono errori di battitura, OCR impreciso o traslitterazioni imperfette.

```python
import regex

# Sintassi base: {tipo_errore<=n}
# e = qualsiasi errore, i = inserzione, d = delezione, s = sostituzione
pattern_base = regex.compile(r"(programmazione){e<=2}")
match = pattern_base.search("programazione Python")  # 1 lettera mancante
print(match.group())          # "programazione"
print(match.fuzzy_counts)     # (0, 1, 0) → (sostituzioni, delezioni, inserzioni)
print(match.fuzzy_changes)    # dettaglio posizionale degli errori

# Controllo granulare per tipo di errore
pattern_preciso = regex.compile(r"(database){i<=1,d<=1,s<=0}")
# Ammette 1 inserzione e 1 delezione, ma nessuna sostituzione
print(regex.search(pattern_preciso, "dataase"))     # Match (1 delezione: 'b')
print(regex.search(pattern_preciso, "databbase"))   # Match (1 inserzione: 'b')
print(regex.search(pattern_preciso, "dxtabase"))    # None (sostituzione non ammessa)

# ENHANCEMATCH: migliora il fit del match trovato
pattern_enhanced = regex.compile(r"(?e)(ricevuta){e<=3}")
match = pattern_enhanced.search("ricvuta fiscale")
# Il flag (?e) cerca di minimizzare il numero di errori effettivi

# BESTMATCH: cerca il match con il minor numero di errori
pattern_best = regex.compile(r"(?b)(fattura){e<=3}")
match = pattern_best.search("fatura elettronica e fattura cartacea")
# Preferisce "fattura" (0 errori) rispetto a "fatura" (1 errore)
print(match.group())  # "fattura"
```

Il fuzzy matching e particolarmente utile per:
- **Correzione OCR**: documenti scansionati con errori di riconoscimento
- **Deduplicazione dati**: trovare record simili in database con errori di immissione
- **Ricerca tollerante**: implementare ricerche che tollerino errori di battitura
- **Matching indirizzi**: confrontare indirizzi con abbreviazioni e varianti

#### Categorie Unicode e Script Properties

Mentre `re` offre solo le classi base (`\w`, `\d`, `\s`) che in Python 3 sono Unicode-aware, il modulo `regex` aggiunge il supporto completo per le **Unicode Property Escapes** tramite la sintassi `\p{...}`, allineandosi allo standard UTS #18 per le espressioni regolari Unicode.

```python
import regex

# Categorie generali Unicode
regex.findall(r"\p{L}+", "Hello Мир 世界 مرحبا")
# ['Hello', 'Мир', '世界', 'مرحبا'] — tutte le lettere, qualsiasi script

regex.findall(r"\p{N}+", "Prezzo: 42€ oppure ١٢٣")
# ['42', '١٢٣'] — tutti i numeri, incluse cifre arabe orientali

regex.findall(r"\p{P}+", "Ciao! Come stai? Bene, grazie.")
# ['!', '?', ',', '.'] — tutta la punteggiatura

# Script specifici
regex.findall(r"\p{Cyrillic}+", "Hello Мир World")
# ['Мир'] — solo caratteri cirillici

regex.findall(r"\p{Han}+", "Parola 世界 end")
# ['世界'] — solo caratteri cinesi (Han)

regex.findall(r"\p{Greek}+", "Simboli: αβγ e lettere: abc")
# ['αβγ'] — solo caratteri greci

regex.findall(r"\p{Arabic}+", "Testo مرحبا fine")
# ['مرحبا'] — solo caratteri arabi

# Categorie granulari
regex.findall(r"\p{Lu}+", "Hello MONDO ciao")
# ['H', 'MONDO'] — solo lettere maiuscole (Letter, uppercase)

regex.findall(r"\p{Ll}+", "Hello MONDO ciao")
# ['ello', 'ciao'] — solo lettere minuscole (Letter, lowercase)

regex.findall(r"\p{Nd}+", "ABC 123 ٤٥٦")
# ['123', '٤٥٦'] — cifre decimali di qualsiasi script

# Negazione delle proprieta
regex.findall(r"\P{L}+", "Ciao 123!")
# [' ', ' ', '!'] — tutto cio che NON e una lettera

# Combinazione con altre feature regex
# Trova parole in script latino con almeno 4 caratteri
regex.findall(r"\b\p{Latin}{4,}\b", "Hello Мир mondo parola")
# ['Hello', 'mondo', 'parola']
```

#### Operazioni su Set di Caratteri (Nested Sets)

Il modulo `regex` supporta operazioni insiemistiche sulle classi di caratteri, una funzionalita assente in `re` che permette intersezioni, unioni e differenze.

```python
import regex

# Intersezione: lettere che sono anche ASCII
# [lettere Unicode] && [ASCII printable]
regex.findall(r"[\p{L}&&[\x00-\x7f]]+", "Hello cafe Мир")
# ['Hello', 'caf', 'r'] — solo lettere ASCII (la 'e' accentata e esclusa)

# Differenza: lettere Unicode MENO le latine
regex.findall(r"[\p{L}--\p{Latin}]+", "Hello Мир 世界 parola")
# ['Мир', '世界'] — lettere non-latine

# Simmetrica: consonanti latine (lettere meno vocali)
regex.findall(r"[\p{Latin}--[aeiouAEIOU]]+", "Hello World")
# ['H', 'll', 'W', 'rld'] — solo consonanti latine

# Unione implicita (come nelle classi standard)
regex.findall(r"[\p{Greek}\p{Cyrillic}]+", "αβγ abc Мир")
# ['αβγ', 'Мир'] — greco e cirillico insieme
```

#### Branch Reset Groups `(?|...)`

I branch reset groups permettono a gruppi in alternative diverse di condividere lo stesso numero di cattura, semplificando l'estrazione da pattern con alternative strutturalmente diverse.

```python
import regex

# Senza branch reset: i gruppi hanno numeri diversi per ogni alternativa
pattern_senza = regex.compile(r"(\d+)-(\d+)|(\w+):(\w+)")
match = pattern_senza.match("abc:def")
# group(1)=None, group(2)=None, group(3)='abc', group(4)='def'

# Con branch reset: i gruppi condividono lo stesso numero
pattern_con = regex.compile(r"(?|(\d+)-(\d+)|(\w+):(\w+))")
match = pattern_con.match("abc:def")
# group(1)='abc', group(2)='def' — indipendentemente dal ramo che ha fatto match
match2 = pattern_con.match("123-456")
# group(1)='123', group(2)='456' — stessi numeri di gruppo
```

#### Modalita Version 0 e Version 1

Il modulo `regex` ha due comportamenti configurabili che influenzano la semantica di alcune operazioni.

```python
import regex

# Version 0 (default): compatibile con re
# Le classi di caratteri vuote generano errore come in re
# regex.compile(r"[]") → errore

# Version 1: comportamento esteso
# Abilita nested sets, operazioni insiemistiche, e altre feature avanzate
pattern = regex.compile(r"[\p{L}--\p{ASCII}]+", flags=regex.V1)
# Trova lettere non-ASCII
regex.findall(pattern, "cafe resume")
# ['e', 'e'] — solo le lettere accentate (non-ASCII)

# Impostazione globale
regex.DEFAULT_VERSION = regex.V1
```

#### Timeout e Sicurezza

A differenza di `re`, il modulo `regex` supporta un parametro `timeout` nativo per prevenire blocchi da catastrophic backtracking.

```python
import regex

# Timeout nativo in secondi
try:
    regex.search(r"(a+)+b", "a" * 30 + "c", timeout=2.0)
except regex.error:
    print("Timeout: il pattern ha impiegato troppo tempo")

# Combinato con possessive quantifiers per sicurezza
pattern_sicuro = regex.compile(r"(a++)b")  # mai backtracking
```

### re2 e google-re2

`re2` e una libreria regex di Google che utilizza un motore **DFA**, garantendo tempo di esecuzione **lineare** rispetto alla lunghezza dell'input. Non supporta backreference ne lookaround, ma e immune al catastrophic backtracking.

```python
# pip install google-re2
import re2  # type: ignore

# API compatibile con re
pattern = re2.compile(r"\d{4}-\d{2}-\d{2}")
match = pattern.search("Data: 2026-05-23")
print(match.group())  # "2026-05-23"

# Caso d'uso: filtraggio su input non fidato (es. log da rete)
# re2 e SICURO contro ReDoS per costruzione
pattern_sicuro = re2.compile(r"(a+)+b")  # re2 lo gestisce in tempo lineare

# Limitazioni di re2:
# - NO backreference (\1, (?P=nome))
# - NO lookahead/lookbehind
# - NO atomic groups (non necessari, il DFA non fa backtracking)
# - Supporto Unicode limitato

# Strategia ibrida:
# - re2 per input non fidato (sicurezza)
# - re per pattern con backreference/lookaround (funzionalita)
```

### parse

La libreria `parse` e l'opposto di `format()`: se `format()` trasforma dati in stringhe, `parse` estrae dati da stringhe. E un'alternativa leggibile alle regex per pattern semplici.

```python
from parse import parse, compile as parse_compile

# Estrazione base
risultato = parse("Utente {nome} ha {eta:d} anni", "Utente Marco ha 30 anni")
print(risultato["nome"])  # "Marco"
print(risultato["eta"])   # 30 (intero, grazie a :d)

# Formati tipizzati
r = parse("{data:ti} - {livello} - {messaggio}", "2026-05-23T10:30:00 - ERROR - Connessione fallita")
print(r["data"])      # datetime(2026, 5, 23, 10, 30)
print(r["livello"])   # "ERROR"

# Pattern precompilato (per uso ripetuto)
pattern_log = parse_compile(
    "{data:ti} {livello} [{sorgente}] {messaggio}"
)
for riga in righe_log:
    risultato = pattern_log.parse(riga)
    if risultato:
        print(risultato.named)

# Confronto con regex equivalente:
# Regex:  r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}) (\w+) \[([^\]]+)\] (.+)"
# Parse:  "{data:ti} {livello} [{sorgente}] {messaggio}"
# La versione con parse e drammaticamente piu leggibile
```

### pyparsing

`pyparsing` e una libreria per la costruzione di parser top-down ricorsivi in Python puro. E adatta per parsing di linguaggi strutturati dove le regex non sono sufficienti.

```python
from pyparsing import (
    Word, alphas, alphanums, nums, Suppress, Group,
    Optional, Literal, oneOf, pyparsing_common
)

# Parsing di un formato chiave=valore
chiave = Word(alphas + "_", alphanums + "_")
valore = Word(alphanums + "._-/")
assegnazione = chiave + Suppress(Literal("=")) + valore

# Parsing
risultato = assegnazione.parseString("database_host=localhost")
print(risultato.asList())  # ['database_host', 'localhost']

# Parsing di espressioni aritmetiche (impossibile con regex)
from pyparsing import infixNotation, opAssoc

numero = pyparsing_common.number
operazione = infixNotation(
    numero,
    [
        (oneOf("* /"), 2, opAssoc.LEFT),
        (oneOf("+ -"), 2, opAssoc.LEFT),
    ]
)

risultato = operazione.parseString("3 + 4 * 2 - 1")
print(risultato.asList())  # [[3, '+', [4, '*', 2], '-', 1]]

# Parsing di un formato log personalizzato
timestamp = pyparsing_common.iso8601_datetime
livello = oneOf("DEBUG INFO WARNING ERROR CRITICAL")
sorgente = Suppress("[") + Word(alphanums + "._") + Suppress("]")
messaggio = Word(alphanums + " ._-:=/")

riga_log = timestamp + livello + sorgente + messaggio
```

### Quando Usare Cosa

| Strumento | Caso d'uso | Pro | Contro |
|---|---|---|---|
| `re` (stdlib) | Pattern standard | Zero dipendenze, API nota | No possessive, ReDoS |
| `regex` | Pattern avanzati | Superset di `re`, fuzzy | Dipendenza esterna |
| `re2` | Input non fidato | Immune a ReDoS, veloce | No backreference/lookaround |
| `parse` | Estrazione semplice | Molto leggibile | Limitato a pattern semplici |
| `pyparsing` | Linguaggi strutturati | Parser ricorsivi | Piu verboso, curva di apprendimento |
| `str` methods | Operazioni banali | Piu veloce, piu chiaro | Nessun pattern matching |

---

## Text Processing Avanzato

### String Methods per Text Processing

Python offre metodi built-in delle stringhe estremamente utili per l'elaborazione del testo, che spesso rappresentano un'alternativa piu semplice e leggibile alle regex.

#### split, rsplit, partition

```python
# split — divide da sinistra
"uno,due,tre,quattro".split(",")
# ['uno', 'due', 'tre', 'quattro']

# split con maxsplit
"uno,due,tre,quattro".split(",", maxsplit=2)
# ['uno', 'due', 'tre,quattro']

# rsplit — divide da destra
"uno,due,tre,quattro".rsplit(",", maxsplit=2)
# ['uno,due', 'tre', 'quattro']

# partition — divide in 3 parti (prima, separatore, dopo)
"chiave=valore=extra".partition("=")
# ('chiave', '=', 'valore=extra')

# rpartition — come partition ma da destra
"chiave=valore=extra".rpartition("=")
# ('chiave=valore', '=', 'extra')

# splitlines — divide per righe (gestisce \n, \r\n, \r)
"riga1\nriga2\r\nriga3".splitlines()
# ['riga1', 'riga2', 'riga3']
```

#### strip, lstrip, rstrip

```python
# strip — rimuove spazi bianchi (o caratteri specificati) da entrambi i lati
"   ciao mondo   ".strip()           # 'ciao mondo'
"---ciao---".strip("-")               # 'ciao'
"xxxciaoxxx".strip("x")              # 'ciao'

# lstrip — solo a sinistra
"   ciao   ".lstrip()                # 'ciao   '

# rstrip — solo a destra
"   ciao   ".rstrip()                # '   ciao'

# removeprefix e removesuffix (Python 3.9+)
"HelloWorld".removeprefix("Hello")    # 'World'
"file.txt".removesuffix(".txt")       # 'file'
```

#### replace, translate, maketrans

```python
# replace — sostituzione semplice
"ciao mondo ciao".replace("ciao", "hello")
# 'hello mondo hello'

# replace con limite
"aaa".replace("a", "b", 2)
# 'bba'

# translate + maketrans — sostituzione carattere per carattere (efficiente)
tabella = str.maketrans("aeiou", "AEIOU")
"ciao mondo".translate(tabella)
# 'cIAO mOndO'

# maketrans con terzo argomento (caratteri da rimuovere)
tabella = str.maketrans("", "", "aeiou")
"ciao mondo".translate(tabella)
# 'c mnd'

# Uso per pulizia del testo
rimuovi_punteggiatura = str.maketrans("", "", ".,;:!?")
"Ciao! Come stai? Bene, grazie.".translate(rimuovi_punteggiatura)
# 'Ciao Come stai Bene grazie'
```

#### encode/decode e Unicode Handling

```python
# Encoding: str -> bytes
testo = "Ciao, come va?"
testo_bytes = testo.encode("utf-8")
# b'Ciao, come va?'

# Decoding: bytes -> str
testo_bytes.decode("utf-8")
# 'Ciao, come va?'

# Gestione errori di encoding
"cafe\u0301".encode("ascii", errors="ignore")      # b'cafe'
"cafe\u0301".encode("ascii", errors="replace")      # b'caf?'
"cafe\u0301".encode("ascii", errors="xmlcharrefreplace")  # b'caf&#769;'

# Rilevamento e conversione encoding
testo_latin1 = "ciao".encode("latin-1")
testo_latin1.decode("latin-1")   # 'ciao'
```

---

### textwrap Module

Il modulo `textwrap` offre funzioni per la formattazione del testo, molto utili per output su terminale, generazione di report e formattazione di documentazione.

```python
import textwrap

testo_lungo = ("Questo e un testo molto lungo che serve come esempio per "
               "dimostrare le funzionalita del modulo textwrap di Python. "
               "Il modulo e particolarmente utile per formattare l'output "
               "su terminale o per generare testo leggibile.")

# wrap — restituisce una lista di righe della larghezza specificata
righe = textwrap.wrap(testo_lungo, width=50)
for riga in righe:
    print(riga)
# Questo e un testo molto lungo che serve come
# esempio per dimostrare le funzionalita del
# modulo textwrap di Python. Il modulo e
# particolarmente utile per formattare l'output
# su terminale o per generare testo leggibile.

# fill — come wrap, ma restituisce una singola stringa con newline
print(textwrap.fill(testo_lungo, width=50))

# dedent — rimuove l'indentazione comune
codice = """
    def saluta():
        print("Ciao!")
        return True
"""
print(textwrap.dedent(codice))
# (nessuna indentazione extra)

# indent — aggiunge un prefisso a ogni riga
testo = "Riga uno\nRiga due\nRiga tre"
print(textwrap.indent(testo, "  > "))
#   > Riga uno
#   > Riga due
#   > Riga tre

# indent con predicato (applica solo a righe non vuote)
testo_con_vuote = "Riga 1\n\nRiga 3\n\nRiga 5"
print(textwrap.indent(testo_con_vuote, "| ", predicate=lambda line: line.strip()))
# | Riga 1
#
# | Riga 3
#
# | Riga 5

# shorten — tronca il testo alla larghezza specificata
textwrap.shorten(testo_lungo, width=60, placeholder="...")
# 'Questo e un testo molto lungo che serve come esempio...'
```

#### Classe TextWrapper — Configurazione Avanzata

Per esigenze ripetitive o complesse, la classe `TextWrapper` offre un controllo granulare sulla formattazione. Invece di chiamare le funzioni standalone ogni volta con gli stessi parametri, si crea un oggetto `TextWrapper` configurato una volta e riutilizzato.

```python
import textwrap

# TextWrapper con configurazione completa
wrapper = textwrap.TextWrapper(
    width=60,                      # Larghezza massima per riga
    initial_indent="  ",           # Indentazione prima riga
    subsequent_indent="    ",      # Indentazione righe successive (hanging indent)
    break_long_words=True,         # Spezza parole lunghe oltre width
    break_on_hyphens=True,         # Spezza sui trattini
    max_lines=3,                   # Numero massimo di righe (Python 3.4+)
    placeholder=" [...]",          # Testo di troncamento con max_lines
    expand_tabs=True,              # Converte tab in spazi
    tabsize=4,                     # Dimensione tab in spazi
    drop_whitespace=True,          # Rimuove spazi a inizio/fine riga
    fix_sentence_endings=False,    # Doppio spazio dopo fine frase (stile tipografico)
)

paragrafo = ("La programmazione funzionale enfatizza l'uso di funzioni pure, "
             "immutabilita dei dati e composizione di funzioni. Questo paradigma "
             "riduce gli effetti collaterali e rende il codice piu facile da "
             "testare, debuggare e ragionare in contesti concorrenti. Python supporta "
             "molti pattern funzionali attraverso lambda, map, filter, reduce e "
             "le comprehension, pur non essendo un linguaggio puramente funzionale.")

print(wrapper.fill(paragrafo))
#   La programmazione funzionale enfatizza l'uso di
#     funzioni pure, immutabilita dei dati e
#     composizione di funzioni. Questo paradigma [...]
```

#### Hanging Indent e Formattazione Lista

Il pattern del **hanging indent** (prima riga allineata a sinistra, righe successive indentate) e fondamentale per generare documentazione, help text CLI e output strutturato.

```python
import textwrap

# Hanging indent per descrizioni di opzioni CLI
def formatta_opzione(flag: str, descrizione: str, larghezza: int = 72) -> str:
    """Formatta un'opzione CLI con hanging indent."""
    prefisso = f"  {flag:<20s} "
    wrapper = textwrap.TextWrapper(
        width=larghezza,
        initial_indent=prefisso,
        subsequent_indent=" " * len(prefisso),
    )
    return wrapper.fill(descrizione)

opzioni = [
    ("--output, -o", "Specifica il percorso del file di output. Se non indicato, "
                     "il risultato viene stampato su stdout."),
    ("--verbose, -v", "Abilita l'output dettagliato. Puo essere ripetuto fino a "
                      "tre volte per aumentare il livello di verbosita (-vvv)."),
    ("--format", "Formato dell'output. Valori accettati: json, csv, table, yaml. "
                 "Default: table. Il formato json include metadati aggiuntivi."),
]

for flag, desc in opzioni:
    print(formatta_opzione(flag, desc))
    print()
```

#### dedent con Pipeline di Pulizia

`textwrap.dedent()` e particolarmente utile per stringhe multiriga definite dentro funzioni con indentazione. Combinato con `strip()`, elimina righe vuote iniziali e finali.

```python
import textwrap

def genera_config():
    """Genera configurazione YAML pulita nonostante l'indentazione del codice."""
    config = textwrap.dedent("""\
        server:
          host: 0.0.0.0
          port: 8080
          workers: 4
        database:
          url: postgresql://localhost/app
          pool_size: 10
        logging:
          level: INFO
          format: "%(asctime)s [%(levelname)s] %(message)s"
    """)
    return config

# indent con predicato avanzato — indenta solo righe che contengono codice
sorgente = "# commento\n\ndef func():\n    pass\n\n# altro commento"
risultato = textwrap.indent(sorgente, ">>> ", predicate=lambda l: not l.startswith("#"))
print(risultato)
# # commento
#
# >>> def func():
# >>>     pass
#
# # altro commento
```

#### shorten con Contesto Preservato

`textwrap.shorten()` e intelligente: non tronca nel mezzo di una parola e rispetta il parametro `placeholder`. E ideale per anteprime, notifiche e UI con spazio limitato.

```python
import textwrap

# Troncamento intelligente per notifiche
notifiche = [
    "Nuovo commit pushato su main: fix del parser CSV che gestiva male i campi con virgolette",
    "Build fallita: test_integrazione_api ha restituito status 500 sul server di staging",
    "PR #142 approvata e mergiata: refactoring completo del modulo di autenticazione OAuth2",
]

for n in notifiche:
    print(textwrap.shorten(n, width=50, placeholder=" ..."))
# Nuovo commit pushato su main: fix del ...
# Build fallita: test_integrazione_api ha ...
# PR #142 approvata e mergiata: refactoring ...

# placeholder personalizzato con indicazione di lunghezza
testo = "Questo e un articolo molto lungo sulla sicurezza informatica moderna"
textwrap.shorten(testo, width=40, placeholder=" [continua]")
# 'Questo e un articolo molto [continua]'
```

---

### difflib

Il modulo `difflib` fornisce strumenti per il confronto tra sequenze, particolarmente utile per il confronto di testi e il fuzzy matching.

```python
import difflib

# SequenceMatcher — confronto tra sequenze
s = difflib.SequenceMatcher(None, "abcdef", "abcxef")
s.ratio()              # 0.8333... (similarita)
s.get_matching_blocks()
# [Match(a=0, b=0, size=3), Match(a=4, b=4, size=2), Match(a=6, b=6, size=0)]

# get_opcodes — operazioni per trasformare una sequenza nell'altra
for tag, i1, i2, j1, j2 in s.get_opcodes():
    print(f"{tag:8s} a[{i1}:{i2}] --> b[{j1}:{j2}]")
# equal    a[0:3] --> b[0:3]    ('abc' == 'abc')
# replace  a[3:4] --> b[3:4]    ('d' -> 'x')
# equal    a[4:6] --> b[4:6]    ('ef' == 'ef')

# unified_diff — output in formato diff unificato
testo1 = ["riga 1\n", "riga 2\n", "riga 3\n", "riga 4\n"]
testo2 = ["riga 1\n", "riga modificata\n", "riga 3\n", "riga nuova\n", "riga 4\n"]

diff = difflib.unified_diff(testo1, testo2, fromfile="originale.txt", tofile="modificato.txt")
print("".join(diff))
# --- originale.txt
# +++ modificato.txt
# @@ -1,4 +1,5 @@
#  riga 1
# -riga 2
# +riga modificata
#  riga 3
# +riga nuova
#  riga 4

# Fuzzy string matching con get_close_matches
parole = ["python", "java", "javascript", "ruby", "rust", "go", "scala"]
difflib.get_close_matches("pythn", parole, n=3, cutoff=0.6)
# ['python']

difflib.get_close_matches("jav", parole, n=3, cutoff=0.5)
# ['java']

# HtmlDiff — genera un confronto HTML visuale
d = difflib.HtmlDiff()
html_diff = d.make_file(testo1, testo2,
                         fromdesc="Originale", todesc="Modificato")
# Genera una pagina HTML completa con le differenze evidenziate
```

Il fuzzy matching e particolarmente utile per funzionalita di "auto-correzione" o "suggerimenti" quando l'utente commette errori di battitura.

```python
# Esempio pratico: suggerimento comandi
comandi_validi = ["install", "update", "remove", "search", "list", "info", "help"]

def suggerisci_comando(input_utente):
    """Suggerisce il comando piu simile a quello digitato."""
    suggerimenti = difflib.get_close_matches(input_utente, comandi_validi, n=1, cutoff=0.6)
    if suggerimenti:
        return f"Forse intendevi '{suggerimenti[0]}'?"
    return "Comando non riconosciuto. Digita 'help' per la lista dei comandi."

print(suggerisci_comando("instll"))     # "Forse intendevi 'install'?"
print(suggerisci_comando("updte"))      # "Forse intendevi 'update'?"
print(suggerisci_comando("xyz"))        # "Comando non riconosciuto..."
```

#### context_diff e ndiff — Formati Alternativi

Oltre a `unified_diff`, `difflib` offre altri formati di output utili in contesti diversi.

```python
import difflib

originale = ["alpha\n", "beta\n", "gamma\n", "delta\n"]
modificato = ["alpha\n", "BETA\n", "gamma\n", "epsilon\n", "delta\n"]

# context_diff — mostra il contesto attorno alle modifiche (stile diff -c)
diff_ctx = difflib.context_diff(originale, modificato,
                                 fromfile="v1.txt", tofile="v2.txt", n=1)
print("".join(diff_ctx))
# *** v1.txt
# --- v2.txt
# ***************
# *** 1,4 ****
# ...

# ndiff — diff riga per riga con indicatori intra-riga
diff_n = difflib.ndiff(originale, modificato)
print("".join(diff_n))
# Le righe modificate mostrano con '^' le posizioni esatte del cambiamento:
#   alpha
# - beta
# + BETA
# ?  ^^^
#   gamma
# + epsilon
#   delta
```

#### SequenceMatcher Avanzato — Analisi Blocchi e Junk

`SequenceMatcher` e il cuore di `difflib`. Il parametro `isjunk` permette di ignorare elementi irrilevanti nel confronto, e `autojunk` gestisce automaticamente le euristiche per sequenze lunghe.

```python
import difflib

# SequenceMatcher con isjunk per ignorare spazi
s = difflib.SequenceMatcher(
    isjunk=lambda x: x == " ",
    a="hello world",
    b="helo  wrld"
)
print(f"Similarita (ignorando spazi): {s.ratio():.3f}")  # 0.857

# get_matching_blocks per trovare le sottosequenze comuni piu lunghe
codice_v1 = [
    "import os\n", "import sys\n", "\n",
    "def main():\n", "    print('v1')\n", "    return 0\n",
]
codice_v2 = [
    "import os\n", "import sys\n", "import json\n", "\n",
    "def main():\n", "    print('v2')\n", "    logging.info('start')\n", "    return 0\n",
]

matcher = difflib.SequenceMatcher(None, codice_v1, codice_v2)
for blocco in matcher.get_matching_blocks():
    if blocco.size > 0:
        print(f"Match: a[{blocco.a}:{blocco.a+blocco.size}] = "
              f"b[{blocco.b}:{blocco.b+blocco.size}] ({blocco.size} righe)")

# Rapporto di similarita tra file
print(f"\nSimilarita: {matcher.ratio():.1%}")  # ~71.4%
```

#### Generazione di Patch e Confronto File

Un caso d'uso pratico: generare patch leggibili per sistemi di revisione del codice o audit automatizzati.

```python
import difflib
from pathlib import Path

def genera_patch(file_originale: str, file_modificato: str) -> str:
    """Genera un patch unificato tra due file."""
    orig = Path(file_originale).read_text(encoding="utf-8").splitlines(keepends=True)
    mod = Path(file_modificato).read_text(encoding="utf-8").splitlines(keepends=True)

    diff = difflib.unified_diff(
        orig, mod,
        fromfile=file_originale,
        tofile=file_modificato,
        n=3  # righe di contesto
    )
    return "".join(diff)

def calcola_statistiche_diff(a: list[str], b: list[str]) -> dict:
    """Calcola statistiche sulle differenze tra due sequenze di righe."""
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

# Esempio di utilizzo
a = ["riga 1\n", "riga 2\n", "riga 3\n"]
b = ["riga 1\n", "riga modificata\n", "riga 3\n", "riga 4\n"]
print(calcola_statistiche_diff(a, b))
# {'inserite': 1, 'rimosse': 0, 'sostituite': 1, 'invariate': 2}
```

---

### Template Strings

#### string.Template

Il modulo `string` fornisce una classe `Template` per la sostituzione di variabili nei template, piu sicura di `str.format()` quando il template proviene da fonti esterne non fidate.

```python
from string import Template

# Template base con $variabile
tmpl = Template("Ciao $nome, benvenuto a $citta!")
risultato = tmpl.substitute(nome="Mario", citta="Roma")
# 'Ciao Mario, benvenuto a Roma!'

# safe_substitute — non genera errori per variabili mancanti
tmpl = Template("$saluto $nome, oggi e $giorno")
tmpl.safe_substitute(saluto="Ciao", nome="Luca")
# 'Ciao Luca, oggi e $giorno'  — $giorno resta invariato

# Template con ${variabile} per disambiguare
tmpl = Template("File: ${nome}_backup.${estensione}")
tmpl.substitute(nome="database", estensione="sql")
# 'File: database_backup.sql'

# Uso con dizionario
dati = {"prodotto": "Laptop", "prezzo": "999.99", "valuta": "EUR"}
Template("$prodotto: $prezzo $valuta").substitute(dati)
# 'Laptop: 999.99 EUR'
```

**Quando usare `Template` invece di f-string o `str.format()`**: quando il template viene fornito dall'utente o da una fonte esterna. `Template` e piu sicuro perche non permette l'esecuzione di espressioni arbitrarie, a differenza di `str.format()` che puo esporre attributi degli oggetti.

#### Panoramica su Jinja2

Per esigenze di templating piu avanzate, la libreria esterna **Jinja2** e lo standard de facto in Python.

```python
# pip install Jinja2
from jinja2 import Template, Environment, FileSystemLoader

# Template base
tmpl = Template("Ciao {{ nome }}, hai {{ eta }} anni.")
tmpl.render(nome="Mario", eta=30)
# 'Ciao Mario, hai 30 anni.'

# Template con logica
tmpl = Template("""
Prodotti disponibili:
{% for prodotto in prodotti %}
  - {{ prodotto.nome }}: {{ prodotto.prezzo }}€
    {% if prodotto.sconto %}(SCONTO: -{{ prodotto.sconto }}%){% endif %}
{% endfor %}
""")

prodotti = [
    {"nome": "Laptop", "prezzo": 999, "sconto": 10},
    {"nome": "Mouse", "prezzo": 29, "sconto": None},
    {"nome": "Tastiera", "prezzo": 79, "sconto": 15},
]
print(tmpl.render(prodotti=prodotti))

# Filtri integrati
tmpl = Template("{{ nome|upper }} - {{ descrizione|truncate(30) }}")

# Caricamento template da file
env = Environment(loader=FileSystemLoader("templates/"))
template = env.get_template("pagina.html")
output = template.render(titolo="Home", contenuto="Benvenuto!")
```

#### Jinja2 — Autoescaping e Sicurezza

Quando si genera HTML, l'autoescaping previene attacchi XSS neutralizzando automaticamente i caratteri pericolosi nei valori interpolati. E **obbligatorio** abilitarlo per qualsiasi output web-facing.

```python
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Environment con autoescaping per HTML e XML
env = Environment(
    loader=FileSystemLoader("templates/"),
    autoescape=select_autoescape(
        enabled_extensions=("html", "xml"),
        default_for_string=True,
    ),
    trim_blocks=True,          # Rimuove newline dopo tag di blocco
    lstrip_blocks=True,        # Rimuove spazi prima di tag di blocco
)

# L'input malevolo viene neutralizzato automaticamente
from jinja2 import Template
env_safe = Environment(autoescape=True)
tmpl = env_safe.from_string("<p>{{ commento }}</p>")
tmpl.render(commento='<script>alert("XSS")</script>')
# '<p>&lt;script&gt;alert("XSS")&lt;/script&gt;</p>'

# Marcare contenuto come sicuro quando si e certi della provenienza
from markupsafe import Markup
html_fidato = Markup("<strong>Grassetto sicuro</strong>")
tmpl.render(commento=html_fidato)
# '<p><strong>Grassetto sicuro</strong></p>'
```

#### Jinja2 — Sandboxed Environment

Per template forniti da utenti non fidati, `SandboxedEnvironment` impedisce l'accesso ad attributi e metodi pericolosi, bloccando tentativi di escape dalla sandbox.

```python
from jinja2.sandbox import SandboxedEnvironment

sandbox = SandboxedEnvironment()

# Template sicuro — funziona normalmente
tmpl = sandbox.from_string("{{ nome|upper }}")
tmpl.render(nome="mario")  # 'MARIO'

# Template pericoloso — bloccato dalla sandbox
try:
    tmpl = sandbox.from_string("{{ ''.__class__.__mro__[1].__subclasses__() }}")
    tmpl.render()
except SecurityError as e:
    print(f"Bloccato: {e}")
    # Accesso a __class__, __mro__, __subclasses__ e negato
```

#### Jinja2 — Filtri Personalizzati e Template Inheritance

I filtri personalizzati estendono le capacita di Jinja2. L'ereditarieta dei template (template inheritance) permette di definire layout base riutilizzabili.

```python
from jinja2 import Environment, BaseLoader
import json
from datetime import datetime

env = Environment(loader=BaseLoader(), autoescape=True)

# Filtro personalizzato: formattazione data italiana
def filtro_data_italiana(dt: datetime, formato: str = "%d/%m/%Y") -> str:
    mesi = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
            "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]
    if formato == "esteso":
        return f"{dt.day} {mesi[dt.month - 1]} {dt.year}"
    return dt.strftime(formato)

# Filtro personalizzato: formattazione valuta
def filtro_valuta(valore: float, simbolo: str = "EUR", decimali: int = 2) -> str:
    formattato = f"{valore:,.{decimali}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{formattato} {simbolo}"

# Registrazione filtri
env.filters["data_it"] = filtro_data_italiana
env.filters["valuta"] = filtro_valuta

tmpl = env.from_string(
    "Fattura del {{ data|data_it('esteso') }}: {{ totale|valuta }}"
)
print(tmpl.render(data=datetime(2026, 5, 24), totale=1499.90))
# 'Fattura del 24 maggio 2026: 1.499,90 EUR'
```

```python
# Template Inheritance — layout base e pagine derivate
layout_base = """
<!DOCTYPE html>
<html lang="it">
<head><title>{% block titolo %}Sito{% endblock %}</title></head>
<body>
  <nav>{% block nav %}Menu principale{% endblock %}</nav>
  <main>{% block contenuto %}{% endblock %}</main>
  <footer>{% block footer %}&copy; 2026{% endblock %}</footer>
</body>
</html>
"""

pagina_prodotto = """
{% extends "layout.html" %}
{% block titolo %}{{ prodotto.nome }} — Catalogo{% endblock %}
{% block contenuto %}
  <h1>{{ prodotto.nome }}</h1>
  <p class="prezzo">{{ prodotto.prezzo|valuta }}</p>
  <p>{{ prodotto.descrizione }}</p>
{% endblock %}
"""

# Macro — funzioni riutilizzabili dentro i template
form_macro = """
{% macro campo_input(nome, tipo="text", label="", required=false) %}
  <div class="form-group">
    <label for="{{ nome }}">{{ label or nome|capitalize }}</label>
    <input type="{{ tipo }}" id="{{ nome }}" name="{{ nome }}"
           {{ "required" if required }}>
  </div>
{% endmacro %}

{{ campo_input("email", tipo="email", label="Email", required=true) }}
{{ campo_input("telefono", tipo="tel", label="Telefono") }}
"""
```

#### Elaborazione HTML/XML con lxml e selectolax

Per il parsing e la manipolazione di documenti HTML e XML, Python offre diverse librerie con differenti trade-off tra velocita, facilita d'uso e completezza.

```python
# --- lxml: parsing HTML/XML con supporto XPath e XSLT ---
# pip install lxml
from lxml import html, etree

# Parsing di un frammento HTML
documento = html.fromstring("""
<div class="articolo">
    <h2>Titolo Articolo</h2>
    <p class="autore">Mario Rossi</p>
    <p class="contenuto">Testo dell'articolo...</p>
    <ul class="tag">
        <li>python</li>
        <li>parsing</li>
        <li>xml</li>
    </ul>
</div>
""")

# XPath — query potenti per navigare il DOM
titolo = documento.xpath("//h2/text()")[0]              # 'Titolo Articolo'
autore = documento.xpath("//p[@class='autore']/text()")[0]  # 'Mario Rossi'
tags = documento.xpath("//ul[@class='tag']/li/text()")  # ['python', 'parsing', 'xml']

# CSS selectors (lxml.cssselect)
from lxml.cssselect import CSSSelector
sel_contenuto = CSSSelector("p.contenuto")
paragrafi = sel_contenuto(documento)  # lista di elementi

# Parsing XML con namespace
xml_doc = etree.fromstring("""
<feed xmlns="http://www.w3.org/2005/Atom">
    <title>Blog Python</title>
    <entry>
        <title>Regex Avanzate</title>
        <published>2026-05-24T10:00:00Z</published>
    </entry>
</feed>
""")
ns = {"atom": "http://www.w3.org/2005/Atom"}
titoli = xml_doc.xpath("//atom:entry/atom:title/text()", namespaces=ns)
# ['Regex Avanzate']
```

```python
# --- selectolax: parser HTML ultraveloce (basato su Modest/Lexbor) ---
# pip install selectolax
from selectolax.parser import HTMLParser

html_raw = """
<html>
<body>
    <div class="prodotto" data-id="101">
        <h3>Laptop Pro</h3>
        <span class="prezzo">999.00</span>
    </div>
    <div class="prodotto" data-id="102">
        <h3>Mouse Wireless</h3>
        <span class="prezzo">29.90</span>
    </div>
</body>
</html>
"""

parser = HTMLParser(html_raw)

# CSS selectors — API semplice e prestazioni eccellenti
prodotti = parser.css("div.prodotto")
for p in prodotti:
    nome = p.css_first("h3").text()
    prezzo = p.css_first("span.prezzo").text()
    data_id = p.attributes.get("data-id", "")
    print(f"[{data_id}] {nome}: {prezzo} EUR")
# [101] Laptop Pro: 999.00 EUR
# [102] Mouse Wireless: 29.90 EUR

# selectolax e 20-50x piu veloce di BeautifulSoup4 per parsing puro,
# rendendolo ideale per scraping ad alto volume e pipeline ETL.
# Limitazione: non supporta XPath, solo CSS selectors.
```

---

## Elaborazione Testi Strutturati

### Log Parsing

Il parsing dei file di log e una delle applicazioni piu comuni delle regex. Vediamo come costruire un parser strutturato.

```python
import re
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LogEntry:
    """Rappresenta una singola riga di log parsata."""
    timestamp: datetime
    livello: str
    sorgente: str
    messaggio: str
    extra: dict = field(default_factory=dict)


class LogParser:
    """Parser generico per file di log con pattern configurabili."""

    # Pattern per diversi formati di log
    PATTERNS = {
        "standard": re.compile(
            r"(?P<data>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?)\s+"
            r"(?P<livello>DEBUG|INFO|WARNING|ERROR|CRITICAL)\s+"
            r"\[(?P<sorgente>[^\]]+)\]\s+"
            r"(?P<messaggio>.+)"
        ),
        "apache_access": re.compile(
            r"(?P<ip>\S+)\s+\S+\s+\S+\s+"
            r"\[(?P<data>[^\]]+)\]\s+"
            r'"(?P<metodo>\w+)\s+(?P<url>\S+)\s+\S+"\s+'
            r"(?P<status>\d{3})\s+(?P<dimensione>\d+|-)"
        ),
        "syslog": re.compile(
            r"(?P<data>\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+"
            r"(?P<host>\S+)\s+"
            r"(?P<sorgente>\S+?)(?:\[(?P<pid>\d+)\])?:\s+"
            r"(?P<messaggio>.+)"
        ),
    }

    FORMATI_DATA = {
        "standard": "%Y-%m-%d %H:%M:%S",
        "apache_access": "%d/%b/%Y:%H:%M:%S %z",
        "syslog": "%b %d %H:%M:%S",
    }

    def __init__(self, formato: str = "standard"):
        if formato not in self.PATTERNS:
            raise ValueError(f"Formato non supportato: {formato}")
        self.formato = formato
        self.pattern = self.PATTERNS[formato]
        self.formato_data = self.FORMATI_DATA[formato]

    def parse_riga(self, riga: str) -> Optional[dict]:
        """Parsa una singola riga di log."""
        match = self.pattern.search(riga.strip())
        if match:
            return match.groupdict()
        return None

    def parse_file(self, percorso: str):
        """Genera entry parsate da un file di log."""
        with open(percorso, "r", encoding="utf-8") as f:
            for numero_riga, riga in enumerate(f, 1):
                risultato = self.parse_riga(riga)
                if risultato:
                    risultato["numero_riga"] = numero_riga
                    yield risultato

    def filtra_per_livello(self, percorso: str, livello: str):
        """Filtra le entry per livello di log."""
        for entry in self.parse_file(percorso):
            if entry.get("livello", "").upper() == livello.upper():
                yield entry

    def cerca_pattern(self, percorso: str, pattern: str):
        """Cerca un pattern specifico nei messaggi di log."""
        regex = re.compile(pattern)
        for entry in self.parse_file(percorso):
            messaggio = entry.get("messaggio", "")
            if regex.search(messaggio):
                yield entry


# Esempio di utilizzo
parser = LogParser("standard")

# Parsing di righe singole
righe = [
    "2025-03-15 10:30:00 INFO [app.server] Server avviato sulla porta 8080",
    "2025-03-15 10:30:05 ERROR [app.database] Connessione al database fallita",
    "2025-03-15 10:30:10 WARNING [app.cache] Cache quasi piena (95%)",
]

for riga in righe:
    risultato = parser.parse_riga(riga)
    if risultato:
        print(f"[{risultato['livello']}] {risultato['sorgente']}: {risultato['messaggio']}")
```

#### Pattern Regex per Estrazione Dati Strutturati

Oltre al log parsing, le regex sono lo strumento principale per estrarre dati strutturati da testo semi-strutturato: email, URL, indirizzi IP, codici fiscali, coordinate e formati proprietari.

```python
import re
from typing import NamedTuple

class DatoEstratto(NamedTuple):
    tipo: str
    valore: str
    posizione: tuple[int, int]

# Raccolta di pattern per estrazione multi-formato
ESTRATTORI = {
    "email": re.compile(
        r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b"
    ),
    "ipv4": re.compile(
        r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}"
        r"(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"
    ),
    "url": re.compile(
        r"https?://[^\s<>\"']+(?:\([^\s<>\"']*\))*[^\s<>\"'.,;:!?\)\]]"
    ),
    "data_iso": re.compile(
        r"\b\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])\b"
    ),
    "codice_fiscale_it": re.compile(
        r"\b[A-Z]{6}\d{2}[A-EHLMPRST]\d{2}[A-Z]\d{3}[A-Z]\b",
        re.IGNORECASE
    ),
    "iban_it": re.compile(
        r"\bIT\d{2}\s?[A-Z]\d{3}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{3}\b",
        re.IGNORECASE
    ),
    "coordinata_gps": re.compile(
        r"(?P<lat>-?\d{1,2}\.\d{4,8})\s*,\s*(?P<lon>-?\d{1,3}\.\d{4,8})"
    ),
}

def estrai_tutti(testo: str) -> list[DatoEstratto]:
    """Estrae tutti i dati strutturati riconosciuti da un testo."""
    risultati = []
    for tipo, pattern in ESTRATTORI.items():
        for match in pattern.finditer(testo):
            risultati.append(DatoEstratto(
                tipo=tipo,
                valore=match.group(),
                posizione=(match.start(), match.end())
            ))
    return sorted(risultati, key=lambda d: d.posizione[0])

# Test
report = """
Incidente registrato il 2026-05-24 dal server 192.168.1.100.
Contatto: admin@esempio.it — dettagli su https://esempio.it/report/42
Coordinate datacenter: 41.9028, 12.4964
CF responsabile: RSSMRA85M01H501Z
IBAN per rimborso: IT60 X054 2811 1010 0000 0123 456
"""

for dato in estrai_tutti(report):
    print(f"  [{dato.tipo}] {dato.valore}")
# [data_iso] 2026-05-24
# [ipv4] 192.168.1.100
# [email] admin@esempio.it
# [url] https://esempio.it/report/42
# [coordinata_gps] 41.9028, 12.4964
# [codice_fiscale_it] RSSMRA85M01H501Z
# [iban_it] IT60 X054 2811 1010 0000 0123 456
```

#### Validazione Multi-Formato con Pattern Compositi

Per validazione robusta, i pattern singoli possono essere combinati in validatori compositi che forniscono feedback dettagliato sull'errore specifico.

```python
import re
from dataclasses import dataclass

@dataclass
class RisultatoValidazione:
    valido: bool
    errori: list[str]
    valore_normalizzato: str = ""

def valida_email_dettagliato(email: str) -> RisultatoValidazione:
    """Validazione email con feedback granulare sugli errori."""
    errori = []
    email = email.strip()

    if not email:
        return RisultatoValidazione(False, ["Email vuota"])

    # Controlla struttura base
    if "@" not in email:
        errori.append("Manca il carattere @")
        return RisultatoValidazione(False, errori)

    locale, dominio = email.rsplit("@", 1)

    # Validazione parte locale
    if len(locale) == 0:
        errori.append("Parte locale vuota (prima di @)")
    elif len(locale) > 64:
        errori.append(f"Parte locale troppo lunga ({len(locale)} > 64 caratteri)")
    elif not re.match(r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+$", locale):
        errori.append("Parte locale contiene caratteri non validi")
    elif locale.startswith(".") or locale.endswith("."):
        errori.append("Parte locale non puo iniziare o finire con un punto")
    elif ".." in locale:
        errori.append("Parte locale contiene punti consecutivi")

    # Validazione dominio
    if len(dominio) == 0:
        errori.append("Dominio vuoto (dopo @)")
    elif len(dominio) > 253:
        errori.append(f"Dominio troppo lungo ({len(dominio)} > 253 caratteri)")
    elif not re.match(r"^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?(\.[a-zA-Z]{2,})+$", dominio):
        errori.append("Formato dominio non valido")

    normalizzato = f"{locale}@{dominio.lower()}" if not errori else ""
    return RisultatoValidazione(not errori, errori, normalizzato)

# Test
for test in ["user@example.com", "user@.com", "u..ser@x.com", "", "a@b"]:
    r = valida_email_dettagliato(test)
    stato = "OK" if r.valido else "ERRORE"
    print(f"[{stato}] '{test}' — {r.errori or r.valore_normalizzato}")
```

---

### Parsing Configurazioni

Le regex sono utili anche per il parsing di formati di configurazione personalizzati.

```python
import re
from collections import OrderedDict


class ConfigParser:
    """Parser per file di configurazione key=value con supporto sezioni."""

    PATTERN_SEZIONE = re.compile(r"^\[(?P<sezione>[^\]]+)\]\s*$")
    PATTERN_KV = re.compile(r"^(?P<chiave>[a-zA-Z_]\w*)\s*=\s*(?P<valore>.+?)\s*$")
    PATTERN_COMMENTO = re.compile(r"^\s*[#;]")
    PATTERN_VUOTA = re.compile(r"^\s*$")

    # Pattern per interpolazione variabili ${sezione.chiave} o ${chiave}
    PATTERN_VARIABILE = re.compile(r"\$\{(?:(?P<sez>\w+)\.)?(?P<var>\w+)\}")

    def __init__(self):
        self.config = OrderedDict()
        self._sezione_corrente = "DEFAULT"

    def parse(self, testo: str) -> OrderedDict:
        """Parsa il testo di configurazione e restituisce un dizionario ordinato."""
        self.config = OrderedDict()
        self._sezione_corrente = "DEFAULT"
        self.config[self._sezione_corrente] = OrderedDict()

        for numero, riga in enumerate(testo.splitlines(), 1):
            # Ignora righe vuote e commenti
            if self.PATTERN_VUOTA.match(riga) or self.PATTERN_COMMENTO.match(riga):
                continue

            # Controlla se e un'intestazione di sezione
            match_sezione = self.PATTERN_SEZIONE.match(riga)
            if match_sezione:
                self._sezione_corrente = match_sezione.group("sezione")
                if self._sezione_corrente not in self.config:
                    self.config[self._sezione_corrente] = OrderedDict()
                continue

            # Controlla se e una coppia chiave=valore
            match_kv = self.PATTERN_KV.match(riga)
            if match_kv:
                chiave = match_kv.group("chiave")
                valore = self._processa_valore(match_kv.group("valore"))
                self.config[self._sezione_corrente][chiave] = valore
                continue

            raise ValueError(f"Riga {numero} non valida: {riga!r}")

        return self.config

    def _processa_valore(self, valore: str):
        """Processa il valore: converte tipi, rimuove virgolette, interpola variabili."""
        # Rimuove virgolette
        if (valore.startswith('"') and valore.endswith('"')) or \
           (valore.startswith("'") and valore.endswith("'")):
            return valore[1:-1]

        # Converte booleani
        if valore.lower() in ("true", "yes", "on"):
            return True
        if valore.lower() in ("false", "no", "off"):
            return False

        # Converte numeri
        try:
            return int(valore)
        except ValueError:
            pass
        try:
            return float(valore)
        except ValueError:
            pass

        return valore

    def get(self, sezione: str, chiave: str, default=None):
        """Recupera un valore dalla configurazione."""
        return self.config.get(sezione, {}).get(chiave, default)


# Esempio di utilizzo
config_testo = """
# Configurazione applicazione
# Questo e un commento

[server]
host = 0.0.0.0
porta = 8080
debug = true
nome = "Server Principale"

[database]
tipo = postgresql
host = localhost
porta = 5432
nome_db = myapp
utente = admin
password = "s3cr3t"
pool_size = 10

[logging]
livello = INFO
file = /var/log/myapp.log
rotazione = true
max_dimensione = 10485760
"""

parser = ConfigParser()
config = parser.parse(config_testo)

# Accesso ai valori
print(parser.get("server", "host"))       # '0.0.0.0'
print(parser.get("server", "porta"))      # 8080 (int)
print(parser.get("server", "debug"))      # True (bool)
print(parser.get("database", "nome_db"))  # 'myapp'

# Iterazione sulle sezioni
for sezione, valori in config.items():
    print(f"\n[{sezione}]")
    for chiave, valore in valori.items():
        print(f"  {chiave} = {valore!r} ({type(valore).__name__})")
```

---

## Unicode e Internazionalizzazione

### Unicode in Python 3

In Python 3, il tipo `str` e nativamente Unicode. Questo significa che tutte le stringhe possono contenere caratteri di qualsiasi lingua o simbolo Unicode senza necessita di prefissi speciali.

```python
# Le stringhe Python 3 sono Unicode per default
testo_it = "Ciao, come stai?"
testo_jp = "Hello"
testo_ar = "Arabic text"
testo_emoji = "Python e divertente!"

# len() conta i caratteri Unicode, non i byte
len("cafe")   # 4 caratteri

# Caratteri Unicode per nome o code point
"\N{SNOWMAN}"               # '☃'
"\u2603"                     # '☃'
"\U0001F600"                 # Emoji (code point > FFFF)
```

### Encoding e Decoding

La distinzione tra `str` (testo Unicode) e `bytes` (dati binari) e fondamentale in Python 3.

```python
# Encoding: str -> bytes
testo = "Ciao, come va?"
utf8_bytes = testo.encode("utf-8")
latin1_bytes = testo.encode("latin-1")
ascii_bytes = testo.encode("ascii", errors="replace")  # '?' per caratteri non-ASCII

print(f"UTF-8:   {utf8_bytes}")     # Possono avere lunghezze diverse
print(f"Latin-1: {latin1_bytes}")

# Decoding: bytes -> str
utf8_bytes.decode("utf-8")

# Errori comuni: decodifica con encoding sbagliato
try:
    utf8_bytes.decode("ascii")
except UnicodeDecodeError as e:
    print(f"Errore di decodifica: {e}")

# Strategie di gestione errori
problematico = b"\xff\xfe"
problematico.decode("utf-8", errors="ignore")      # Ignora byte non validi
problematico.decode("utf-8", errors="replace")      # Sostituisce con U+FFFD
problematico.decode("utf-8", errors="backslashreplace")  # Mostra escape
```

### Modulo unicodedata

```python
import unicodedata

# Ottenere informazioni su un carattere
unicodedata.name("A")            # 'LATIN CAPITAL LETTER A'
unicodedata.name("\u00e9")       # 'LATIN SMALL LETTER E WITH ACUTE'
unicodedata.category("A")       # 'Lu' (Letter, uppercase)
unicodedata.category("9")       # 'Nd' (Number, decimal digit)
unicodedata.category("!")       # 'Po' (Punctuation, other)

# Cercare un carattere per nome
unicodedata.lookup("SNOWMAN")    # '☃'
unicodedata.lookup("EURO SIGN")  # '€'
```

### Gestione Caratteri Speciali

```python
import unicodedata

# Rimozione accenti (decomposizione + rimozione combining characters)
def rimuovi_accenti(testo: str) -> str:
    """Rimuove gli accenti da una stringa mantenendo le lettere base."""
    # Decompone in caratteri base + combining marks
    decomposto = unicodedata.normalize("NFD", testo)
    # Rimuove i combining characters (categoria 'M')
    return "".join(c for c in decomposto if unicodedata.category(c) != "Mn")

rimuovi_accenti("cafe resume naive")
# 'cafe resume naive'

rimuovi_accenti("citta perche pieta")
# 'citta perche pieta'

# Pulizia testo: rimozione caratteri di controllo
def pulisci_testo(testo: str) -> str:
    """Rimuove caratteri di controllo invisibili mantenendo spazi e newline."""
    return "".join(
        c for c in testo
        if unicodedata.category(c) != "Cc" or c in "\n\r\t"
    )
```

### Normalizzazione Unicode (NFC, NFD)

La normalizzazione e cruciale per il confronto corretto delle stringhe Unicode, poiche lo stesso carattere visivo puo avere rappresentazioni diverse.

```python
import unicodedata

# La lettera "e" puo essere rappresentata in due modi:
# 1. Precomposta: U+00E9 (un singolo code point)
precomposta = "\u00e9"         # e

# 2. Decomposta: U+0065 + U+0301 (lettera 'e' + combining acute accent)
decomposta = "e\u0301"         # e + accento

# Visivamente sono identiche, ma...
print(precomposta == decomposta)    # False!
print(len(precomposta))             # 1
print(len(decomposta))              # 2

# La normalizzazione risolve il problema
# NFC (Canonical Decomposition, followed by Canonical Composition)
# -> forma precomposta
nfc = unicodedata.normalize("NFC", decomposta)
print(nfc == precomposta)           # True

# NFD (Canonical Decomposition) -> forma decomposta
nfd = unicodedata.normalize("NFD", precomposta)
print(nfd == decomposta)            # True

# Best practice: normalizzare sempre in NFC per i confronti
def confronta_stringhe(s1: str, s2: str) -> bool:
    """Confronto Unicode-safe di due stringhe."""
    return unicodedata.normalize("NFC", s1) == unicodedata.normalize("NFC", s2)

# NFKC e NFKD — normalizzazione di compatibilita
# Converte anche varianti tipografiche
unicodedata.normalize("NFKC", "Hello")    # 'Hello' (larghezza piena -> ASCII)
unicodedata.normalize("NFKC", "2")        # '2'     (cifra a pedice -> normale)
```

---

### Normalizzazione Avanzata con unicodedata

La normalizzazione del testo e cruciale per confronti affidabili, ricerche e deduplicazione. Il modulo `unicodedata` fornisce gli strumenti per gestire le complessita del testo Unicode.

#### Transliteration e Slug Generation

```python
import unicodedata
import re

def genera_slug(testo: str) -> str:
    """Genera uno slug URL-safe da un testo Unicode arbitrario."""
    # 1. Normalizza in NFD (decomponi i caratteri composti)
    normalizzato = unicodedata.normalize("NFD", testo)

    # 2. Rimuovi i combining marks (accenti, diacritici)
    senza_accenti = "".join(
        c for c in normalizzato
        if unicodedata.category(c) != "Mn"
    )

    # 3. Converti in ASCII lowercase
    ascii_text = senza_accenti.encode("ascii", errors="ignore").decode("ascii").lower()

    # 4. Sostituisci spazi e caratteri non alfanumerici con trattini
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text)

    # 5. Rimuovi trattini iniziali e finali
    return slug.strip("-")

print(genera_slug("Citta e Regioni d'Italia"))
# "citta-e-regioni-d-italia"

print(genera_slug("Programmazione Python: Guida Completa!"))
# "programmazione-python-guida-completa"
```

#### Rilevamento Script e Categorie

```python
import unicodedata

def analizza_testo(testo: str) -> dict:
    """Analizza la composizione Unicode di un testo."""
    categorie = {}
    for c in testo:
        cat = unicodedata.category(c)
        nome_cat = {
            "Lu": "Lettera maiuscola", "Ll": "Lettera minuscola",
            "Nd": "Cifra decimale", "Zs": "Spazio",
            "Po": "Punteggiatura", "Pc": "Connettore",
            "Mn": "Mark non-spacing", "Cc": "Controllo",
        }.get(cat, cat)
        categorie[nome_cat] = categorie.get(nome_cat, 0) + 1
    return categorie

print(analizza_testo("Ciao, mondo! 123"))
# {'Lettera maiuscola': 1, 'Lettera minuscola': 8, ...}

def contiene_script_misto(testo: str) -> bool:
    """Rileva se il testo mescola script diversi (possibile IDN homograph attack)."""
    scripts = set()
    for c in testo:
        cat = unicodedata.category(c)
        if cat.startswith("L"):  # solo lettere
            nome = unicodedata.name(c, "")
            script = nome.split()[0] if nome else "UNKNOWN"
            scripts.add(script)
    return len(scripts) > 1

# Utile per rilevare phishing con caratteri cirillici simili a latini
print(contiene_script_misto("paypal"))     # False (solo latino)
print(contiene_script_misto("pаypal"))     # True (la 'а' e cirillica!)
```

#### Pulizia Testo Multilingue per NLP

```python
import unicodedata
import re

def pulisci_per_nlp(testo: str) -> str:
    """Pipeline di pulizia testo per preprocessing NLP."""
    # 1. Normalizza in NFC (forma precomposta canonica)
    testo = unicodedata.normalize("NFC", testo)

    # 2. Rimuovi caratteri di controllo (tranne newline e tab)
    testo = "".join(
        c for c in testo
        if unicodedata.category(c) != "Cc" or c in "\n\r\t"
    )

    # 3. Normalizza spazi bianchi (inclusi non-breaking space, etc.)
    testo = re.sub(r"[  -​  　]", " ", testo)

    # 4. Normalizza trattini e apostrofi tipografici
    testo = testo.replace("–", "-")   # en dash
    testo = testo.replace("—", "-")   # em dash
    testo = testo.replace("‘", "'")   # left single quote
    testo = testo.replace("’", "'")   # right single quote
    testo = testo.replace("“", '"')   # left double quote
    testo = testo.replace("”", '"')   # right double quote

    # 5. Comprimi spazi multipli
    testo = re.sub(r" {2,}", " ", testo)

    return testo.strip()
```

#### NFKC e NFKD — Normalizzazione di Compatibilita Approfondita

Le forme NFKC e NFKD (K = Kompatibility) vanno oltre la normalizzazione canonica: convertono anche varianti tipografiche, ligature e forme alternative nei loro equivalenti standard. Questo e fondamentale per la sicurezza (prevenzione IDN homograph attack) e per la ricerca full-text.

```python
import unicodedata

# Differenze tra NFC/NFD e NFKC/NFKD
casi_nfkc = [
    ("ﬁ",    "fi",   "Ligatura fi"),
    ("½",    "1⁄2",  "Frazione volgare"),
    ("Hello", "Hello", "Fullwidth Latin"),
    ("²",    "2",    "Superscript"),
    ("ℌ",    "H",    "Letter-like symbol"),
    ("①",   "1",    "Circled digit"),
    ("㍻",   "平成", "CJK compatibility"),
]

for originale, atteso, desc in casi_nfkc:
    normalizzato = unicodedata.normalize("NFKC", originale)
    ok = "v" if normalizzato == atteso else "x"
    print(f"[{ok}] {desc}: '{originale}' -> '{normalizzato}'")

# Attenzione: NFKC e lossy — perde informazione tipografica.
# Usare solo quando la perdita e accettabile (ricerca, confronto, slug).
```

#### Rilevamento Confusable e Homoglyph — Sicurezza Unicode

I caratteri confusable (omoglifi) sono visivamente identici ma hanno code point diversi. Vengono sfruttati per phishing, spoofing di nomi utente e bypass di filtri.

```python
import unicodedata

# Mappa di omoglifi comuni usati in attacchi
CONFUSABLE_MAP = {
    "а": "a",  # Cirillico а → Latino a
    "е": "e",  # Cirillico е → Latino e
    "о": "o",  # Cirillico о → Latino o
    "р": "p",  # Cirillico р → Latino p
    "с": "c",  # Cirillico с → Latino c
    "у": "y",  # Cirillico у → Latino y
    "ѕ": "s",  # Cirillico ѕ → Latino s
    "і": "i",  # Cirillico і → Latino i
}

def skeleton(testo: str) -> str:
    """Converte il testo nella forma 'skeleton' per rilevamento confusable.

    Basato su Unicode TR39 (Security Mechanisms). La forma skeleton
    normalizza il testo in modo che omoglifi mappino allo stesso risultato.
    """
    # Passo 1: NFKD per decomporre varianti di compatibilita
    nfkd = unicodedata.normalize("NFKD", testo)
    # Passo 2: rimuovi combining marks
    senza_marks = "".join(c for c in nfkd if unicodedata.category(c) != "Mn")
    # Passo 3: mappa confusable noti
    mappato = "".join(CONFUSABLE_MAP.get(c, c) for c in senza_marks)
    # Passo 4: lowercase e NFC finale
    return unicodedata.normalize("NFC", mappato.lower())

# Rilevamento: due stringhe sono confusable se hanno lo stesso skeleton
def sono_confusable(s1: str, s2: str) -> bool:
    return skeleton(s1) == skeleton(s2)

print(sono_confusable("paypal", "pаypаl"))  # True — 'а' cirillica
print(sono_confusable("apple", "аpple"))    # True — prima 'а' cirillica
print(sono_confusable("google", "gооgle"))  # True — 'о' cirillica
print(sono_confusable("hello", "world"))    # False — genuinamente diversi
```

#### Tokenizzazione Testo con la Libreria Standard

Prima di ricorrere a librerie NLP esterne (spaCy, NLTK), Python offre strumenti stdlib sufficienti per molti task di tokenizzazione.

```python
import re
import shlex

# Tokenizzazione base: split su spazi bianchi
testo = "La volpe  veloce\tsalta\nil recinto"
testo.split()  # ['La', 'volpe', 'veloce', 'salta', 'il', 'recinto']

# Tokenizzazione regex: preserva punteggiatura come token separati
def tokenizza(testo: str) -> list[str]:
    """Tokenizzatore regex che separa parole, numeri e punteggiatura."""
    pattern = re.compile(r"""
        \b\w+(?:'\w+)*\b   |  # parole (incluse contrazioni: l'uomo, don't)
        \d+(?:\.\d+)?       |  # numeri (interi e decimali)
        [^\w\s]                # punteggiatura singola
    """, re.VERBOSE | re.UNICODE)
    return pattern.findall(testo)

print(tokenizza("L'uomo ha 3.14 motivi, ma non 0!"))
# ["L'uomo", 'ha', '3.14', 'motivi', ',', 'ma', 'non', '0', '!']

# shlex — tokenizzazione shell-like (rispetta quoting)
comando = 'grep -r "errore critico" --include="*.log" /var/log/'
shlex.split(comando)
# ['grep', '-r', 'errore critico', '--include=*.log', '/var/log/']

# Tokenizzazione per frasi con regex
def separa_frasi(testo: str) -> list[str]:
    """Divide il testo in frasi usando euristiche sulla punteggiatura."""
    frasi = re.split(r'(?<=[.!?])\s+(?=[A-ZÀ-Ü])', testo)
    return [f.strip() for f in frasi if f.strip()]

paragrafo = ("Python e un linguaggio versatile. Supporta molti paradigmi! "
             "E tu, lo usi? Io lo uso ogni giorno.")
print(separa_frasi(paragrafo))
# ['Python e un linguaggio versatile.',
#  'Supporta molti paradigmi!',
#  'E tu, lo usi?',
#  'Io lo uso ogni giorno.']
```

---

## Best Practices

Di seguito sono elencate le best practices fondamentali per lavorare efficacemente con le regex e il text processing in Python.

### 1. Utilizzare Sempre le Raw Strings

Utilizzare il prefisso `r` davanti alle stringhe regex per evitare conflitti con i caratteri di escape di Python. Senza raw string, il backslash viene interpretato prima da Python e poi dal motore regex, causando comportamenti inattesi.

```python
# ERRATO: il backslash viene interpretato da Python
re.search("\bparola\b", "una parola qui")        # Potrebbe non funzionare come atteso

# CORRETTO: raw string, il backslash arriva intatto al motore regex
re.search(r"\bparola\b", "una parola qui")       # Funziona correttamente
```

### 2. Precompilare i Pattern Riutilizzati

Quando un pattern viene usato piu volte (in un loop, in una funzione chiamata ripetutamente), precompilarlo con `re.compile()` migliora la leggibilita e puo migliorare le prestazioni.

```python
# SUBOTTIMALE: ricompilato ad ogni iterazione
for riga in migliaia_di_righe:
    match = re.search(r"ERROR\s+(\d+):\s+(.+)", riga)

# OTTIMALE: compilato una volta sola
pattern_errore = re.compile(r"ERROR\s+(\d+):\s+(.+)")
for riga in migliaia_di_righe:
    match = pattern_errore.search(riga)
```

### 3. Usare `re.VERBOSE` per Pattern Complessi

I pattern lunghi e complessi diventano rapidamente illeggibili. La flag `re.VERBOSE` permette di aggiungere spazi e commenti, rendendo il pattern auto-documentante.

```python
# ILLEGGIBILE
pattern = re.compile(r"^(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)$")

# LEGGIBILE
pattern = re.compile(r"""
    ^
    (?:
        (?:25[0-5]|2[0-4]\d|[01]?\d\d?)    # Ottetto (0-255)
        \.                                    # Punto separatore
    ){3}                                      # Primi 3 ottetti
    (?:25[0-5]|2[0-4]\d|[01]?\d\d?)         # Ultimo ottetto
    $
""", re.VERBOSE)
```

### 4. Preferire le Funzioni Built-in Quando Possibile

Per operazioni semplici, i metodi delle stringhe sono piu leggibili, piu veloci e meno soggetti a errori rispetto alle regex.

```python
# NON NECESSARIO usare regex per questo
re.sub(r"ciao", "hello", testo)

# MEGLIO: metodo str.replace()
testo.replace("ciao", "hello")

# NON NECESSARIO: regex per split semplice
re.split(r",", "a,b,c")

# MEGLIO: str.split()
"a,b,c".split(",")

# Usare regex SOLO quando serve la potenza espressiva
re.split(r"[,;\s]+", "a, b; c  d")   # Qui la regex e giustificata
```

### 5. Usare Gruppi Non Catturanti Quando Non Serve la Cattura

Usare `(?:...)` invece di `(...)` quando il gruppo serve solo per raggruppare e non per estrarre contenuto. Questo migliora la chiarezza del codice e, marginalmente, le prestazioni.

```python
# Il gruppo serve solo per l'alternativa, non per la cattura
re.findall(r"(?:http|https|ftp)://\S+", testo)   # Buona pratica
```

### 6. Attenzione al Backtracking Catastrofico

Pattern con quantificatori annidati possono causare un backtracking esponenziale, bloccando l'esecuzione su certi input. Evitare pattern come `(a+)+`, `(a|b)*a` con input non corrispondenti molto lunghi.

```python
# PERICOLOSO: backtracking potenzialmente catastrofico
# re.match(r"(a+)+b", "a" * 30 + "c")  # Puo richiedere tempi lunghissimi!

# SICURO: riformulazione del pattern
re.match(r"a+b", "a" * 30 + "c")       # Immediato

# Usare atomic groups o possessive quantifiers se disponibili,
# oppure riformulare il pattern per eliminare l'ambiguita.
```

### 7. Validare i Pattern in Modo Incrementale

Sviluppare e testare i pattern regex in modo incrementale, partendo dal caso piu semplice e aggiungendo complessita gradualmente.

```python
# Passo 1: pattern base
r"\d+"

# Passo 2: aggiungere struttura
r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"

# Passo 3: aggiungere validazione
r"(?:25[0-5]|2[0-4]\d|[01]?\d\d?)"

# Passo 4: comporre il pattern completo
r"^(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)$"
```

### 8. Non Usare Regex per Parsing di Linguaggi Strutturati

Le regex operano su linguaggi regolari e non sono adatte per linguaggi context-free come HTML, XML, JSON, o i linguaggi di programmazione. Utilizzare sempre i parser appropriati.

```python
# ERRATO: parsing HTML con regex (fragile e incompleto)
re.findall(r"<a href=\"(.*?)\">(.*?)</a>", html)

# CORRETTO: usare un parser dedicato
from html.parser import HTMLParser
# oppure
from bs4 import BeautifulSoup
```

### 9. Gestire Sempre i Casi di Mancato Match

Le funzioni `re.match()` e `re.search()` restituiscono `None` quando non trovano corrispondenze. Controllare sempre il risultato prima di accedere ai metodi del Match object.

```python
# ERRATO: puo generare AttributeError se il match fallisce
valore = re.search(r"\d+", testo).group()

# CORRETTO: verifica esplicita
match = re.search(r"\d+", testo)
if match:
    valore = match.group()
else:
    valore = None

# ALTERNATIVA Python 3.8+: walrus operator
if match := re.search(r"\d+", testo):
    valore = match.group()
```

### 10. Documentare i Pattern Complessi

Ogni pattern regex non banale dovrebbe essere documentato con un commento che ne spiega lo scopo, il formato atteso dell'input e i limiti noti.

```python
# Pattern per il Codice Fiscale italiano
# Formato: LLLLLLDDLDDLDDDA
#   - 6 lettere (3 cognome + 3 nome)
#   - 2 cifre (anno nascita)
#   - 1 lettera (mese, codificata A-T escludendo alcune)
#   - 2 cifre (giorno, +40 per femmine)
#   - 1 lettera + 3 cifre (codice catastale comune)
#   - 1 lettera (carattere di controllo)
# Limiti: non verifica la validita del carattere di controllo
PATTERN_CF = re.compile(
    r"^[A-Z]{6}\d{2}[ABCDEHLMPRST]\d{2}[A-Z]\d{3}[A-Z]$",
    re.IGNORECASE
)
```

---

Questa guida copre i fondamenti e le tecniche avanzate per il lavoro con le espressioni regolari e l'elaborazione del testo in Python. La padronanza di questi strumenti consente di affrontare efficacemente una vasta gamma di problemi: dalla validazione di input alla trasformazione di dati, dal parsing di file di log alla manipolazione di testi strutturati e non strutturati. La chiave per l'uso efficace delle regex e trovare il giusto equilibrio tra la potenza espressiva dei pattern e la leggibilita del codice, ricorrendo ai metodi built-in delle stringhe quando sufficienti e alle regex solo quando realmente necessario.

---

## Esercizi

### Esercizio 1 — Validatore di IBAN Italiano

Scrivi una funzione `valida_iban_it(iban: str) -> bool` che validi un IBAN italiano. L'IBAN italiano ha il formato: `IT` + 2 cifre di controllo + 1 lettera (CIN) + 5 cifre (ABI) + 5 cifre (CAB) + 12 caratteri alfanumerici (conto corrente). Totale: 27 caratteri. La funzione deve accettare spazi tra gruppi e restituire `True`/`False`. Testa con almeno 5 casi validi e 5 invalidi.

### Esercizio 2 — Parser di Markdown Links

Scrivi un parser che estragga tutti i link da un testo Markdown. Un link Markdown ha il formato `[testo](url)`, ma puo anche avere un titolo: `[testo](url "titolo")`. La funzione deve restituire una lista di dizionari con chiavi `testo`, `url` e `titolo` (opzionale). Gestisci anche link annidati in grassetto o corsivo: `**[testo](url)**`.

### Esercizio 3 — Rilevatore di ReDoS

Scrivi una funzione `rileva_redos(pattern: str) -> list[str]` che analizzi una stringa regex e restituisca una lista di potenziali vulnerabilita ReDoS. Cerca pattern pericolosi come: quantificatori annidati `(a+)+`, alternative sovrapposte `(\w+|\d+)+`, e quantificatori in sequenza con overlap `\w+\w+`. Nota: questo e un rilevatore euristico, non un analizzatore formale.

### Esercizio 4 — Normalizzatore di Testo Multilingue

Costruisci una classe `NormalizzatoreTesto` con i seguenti metodi:
- `normalizza_unicode(testo)` — applica NFC e rimuove combining marks
- `normalizza_spazi(testo)` — unifica tutti i tipi di spazi bianchi Unicode
- `rimuovi_caratteri_controllo(testo)` — rimuove tutti i Cc tranne newline
- `genera_slug(testo)` — produce uno slug URL-safe
- `rileva_script(testo) -> set[str]` — restituisce gli script Unicode presenti

Testa con input contenente testo italiano, giapponese, arabo e russo.

### Esercizio 5 — Pipeline di Log Analysis

Costruisci un sistema di analisi log che:
1. Parsi file di log in formato Apache Combined, Syslog e JSON strutturato
2. Rilevi automaticamente il formato del log (auto-detection del pattern)
3. Estragga metriche: conteggio per livello, top 10 IP, top 10 URL, distribuzione temporale
4. Identifichi anomalie: burst di errori (>10 errori in 1 minuto), IP con troppe richieste
5. Produca un report in formato testo con le metriche calcolate

Usa `re.compile()` per tutti i pattern, `difflib` per il fuzzy matching dei messaggi di errore simili, e `textwrap` per formattare il report.

### Esercizio 6 — Confronto Performance: re vs regex vs re2

Scrivi un benchmark che confronti le performance di `re`, `regex` e `re2` (se disponibile) su:
1. Pattern semplice su testo grande (1M caratteri): estrazione di tutti gli indirizzi email
2. Pattern con backreference: trovare parole duplicate consecutive
3. Pattern vulnerabile a ReDoS: misura il tempo con input crescente
4. Pattern con Unicode: estrazione di parole in diversi script

Per ogni caso, misura: tempo medio, deviazione standard, throughput (MB/s). Presenta i risultati in una tabella formattata.

### Esercizio 7 — Motore di Template

Implementa un motore di template semplice che supporti:
- Sostituzione di variabili: `{{ variabile }}`
- Condizionali: `{% if condizione %}...{% endif %}`
- Loop: `{% for item in lista %}...{% endfor %}`
- Filtri: `{{ variabile | upper }}`, `{{ variabile | truncate(30) }}`

Usa le regex per il parsing dei tag template e una funzione per l'evaluazione. Non usare `eval()` — implementa un semplice interprete per le espressioni ammesse.

### Esercizio 8 — Estrattore Dati Strutturati da Testo Libero

Scrivi un modulo `estrattore.py` che, dato un testo in linguaggio naturale italiano, estragga automaticamente:
- **Date**: tutti i formati italiani (`15 marzo 2026`, `15/03/2026`, `2026-03-15`)
- **Importi monetari**: `€ 1.234,56`, `1234.56 EUR`, `euro 50`
- **Numeri di telefono**: fissi e mobili, con o senza prefisso internazionale
- **Indirizzi email**: con validazione base RFC 5321
- **URL**: http, https, ftp, con o senza www
- **Codici fiscali e partite IVA**

Per ogni tipo, la funzione deve restituire una lista di dizionari con: `tipo`, `valore`, `posizione_inizio`, `posizione_fine`, `contesto` (10 caratteri prima e dopo). Testa con un testo di almeno 500 parole contenente tutti i tipi di dato.

### Esercizio 9 — Text Diff Visuale

Usando `difflib`, costruisci uno strumento CLI che:
1. Accetti due file di testo come argomento
2. Produca un diff con contesto configurabile (default: 3 righe)
3. Supporti output in formato: unified diff, side-by-side, HTML
4. Calcoli metriche: righe aggiunte, rimosse, modificate, invariate, percentuale di similarita
5. Supporti il confronto case-insensitive e ignorando spazi bianchi

### Esercizio 10 — Regex Debugger

Implementa un visualizzatore di matching regex passo-passo:
1. Accetta un pattern e un testo di input
2. Mostra ogni passo del matching: posizione corrente, stato del pattern, gruppi catturati fino a quel momento
3. Evidenzia i punti di backtracking
4. Calcola e mostra il numero totale di passi e il tempo impiegato
5. Suggerisci ottimizzazioni se rileva pattern inefficienti

Usa `sre_parse` per analizzare il pattern e `re.finditer()` per i match reali. Il debug passo-passo puo essere approssimato mostrando i risultati incrementali su sottostringhe crescenti.

### Soluzioni Guidate

#### Soluzione Esercizio 1 — IBAN Italiano

```python
import re

def valida_iban_it(iban: str) -> bool:
    """Valida un IBAN italiano con verifica strutturale e checksum."""
    # Rimuovi spazi
    iban = iban.replace(" ", "").upper()

    # Verifica struttura: IT + 2 cifre + 1 lettera + 5 cifre + 5 cifre + 12 alfanum
    pattern = re.compile(r"^IT\d{2}[A-Z]\d{10}[A-Z0-9]{12}$")
    if not pattern.match(iban):
        return False

    # Verifica lunghezza
    if len(iban) != 27:
        return False

    # Verifica checksum ISO 7064 (mod 97)
    # Sposta le prime 4 cifre alla fine
    riordinato = iban[4:] + iban[:4]

    # Converti lettere in numeri: A=10, B=11, ..., Z=35
    numerico = ""
    for c in riordinato:
        if c.isdigit():
            numerico += c
        else:
            numerico += str(ord(c) - ord("A") + 10)

    # Il numero risultante deve essere congruente a 1 modulo 97
    return int(numerico) % 97 == 1


# Test
assert valida_iban_it("IT60 X054 2811 1010 0000 0123 456")
assert valida_iban_it("IT60X0542811101000000123456")
assert not valida_iban_it("IT00X0542811101000000123456")
assert not valida_iban_it("DE89370400440532013000")  # IBAN tedesco
assert not valida_iban_it("IT60X054281110100000012345")  # troppo corto
```

#### Soluzione Esercizio 2 — Parser di Markdown Links

```python
import re
from dataclasses import dataclass

@dataclass
class MarkdownLink:
    testo: str
    url: str
    titolo: str | None = None

def estrai_link_markdown(testo: str) -> list[MarkdownLink]:
    """Estrae tutti i link da un testo Markdown."""
    # Pattern per link con titolo opzionale
    # [testo](url) oppure [testo](url "titolo")
    pattern = re.compile(r"""
        \[                          # apertura parentesi quadra
        (?P<testo>[^\]]+)           # testo del link (tutto tranne ])
        \]                          # chiusura parentesi quadra
        \(                          # apertura parentesi tonda
        (?P<url>\S+?)               # URL (non-greedy, no spazi)
        (?:\s+"(?P<titolo>[^"]*)")? # titolo opzionale tra virgolette
        \)                          # chiusura parentesi tonda
    """, re.VERBOSE)

    risultati = []
    for match in pattern.finditer(testo):
        risultati.append(MarkdownLink(
            testo=match.group("testo"),
            url=match.group("url"),
            titolo=match.group("titolo")
        ))
    return risultati

# Test
md = """
Visita [Python](https://python.org) e [la guida](https://docs.python.org "Documentazione").
Anche **[grassetto link](https://bold.example.com)** funziona.
"""
links = estrai_link_markdown(md)
for link in links:
    print(f"{link.testo} -> {link.url} (titolo: {link.titolo})")
```

---

## Letture

### Documentazione Ufficiale

- **Python `re` module** — [docs.python.org/3/library/re.html](https://docs.python.org/3/library/re.html) — Riferimento completo del modulo `re`, incluso il dettaglio di tutte le flag, funzioni e sintassi dei pattern.
- **Python HOWTO: Regular Expressions** — [docs.python.org/3/howto/regex.html](https://docs.python.org/3/howto/regex.html) — Tutorial ufficiale di Python sulle regex, scritto da A.M. Kuchling, con approccio graduale dai fondamenti ai pattern avanzati.
- **Python `unicodedata` module** — [docs.python.org/3/library/unicodedata.html](https://docs.python.org/3/library/unicodedata.html) — Riferimento per l'accesso al Unicode Character Database.
- **Python `textwrap` module** — [docs.python.org/3/library/textwrap.html](https://docs.python.org/3/library/textwrap.html)
- **Python `difflib` module** — [docs.python.org/3/library/difflib.html](https://docs.python.org/3/library/difflib.html)

### Librerie Terze Parti

- **regex (PyPI)** — [pypi.org/project/regex](https://pypi.org/project/regex/) — Drop-in replacement di `re` con supporto per atomic groups, possessive quantifiers, fuzzy matching, Unicode properties.
- **google-re2 (PyPI)** — [pypi.org/project/google-re2](https://pypi.org/project/google-re2/) — Binding Python per il motore RE2 di Google (DFA, immune a ReDoS).
- **parse (PyPI)** — [pypi.org/project/parse](https://pypi.org/project/parse/) — L'inverso di `format()`: estrae dati da stringhe con una sintassi leggibile.
- **pyparsing (PyPI)** — [pypi.org/project/pyparsing](https://pypi.org/project/pyparsing/) — Costruzione di parser top-down ricorsivi in Python puro.

### Approfondimenti Tecnici

- **Russ Cox: Regular Expression Matching Can Be Simple And Fast** — [swtch.com/~rsc/regexp/regexp1.html](https://swtch.com/~rsc/regexp/regexp1.html) — Articolo fondamentale sulla differenza tra NFA e DFA, e perche il backtracking e un problema. Scritto dall'autore di RE2.
- **OWASP ReDoS** — [owasp.org/www-community/attacks/Regular_expression_Denial_of_Service_-_ReDoS](https://owasp.org/www-community/attacks/Regular_expression_Denial_of_Service_-_ReDoS) — Documentazione OWASP sulla vulnerabilita ReDoS.
- **Unicode Technical Report #15: Unicode Normalization Forms** — [unicode.org/reports/tr15/](https://unicode.org/reports/tr15/) — Specifica ufficiale delle forme di normalizzazione NFC, NFD, NFKC, NFKD.

### Cross-link Interni

- [Modulo 01 — Fondamenti Python](01-fondamenti.md) — Tipi `str`, `bytes`, encoding, metodi stringa
- [Modulo 07 — Error Handling](07-error-handling.md) — Gestione eccezioni nei parser
- [Modulo 08 — Testing](08-testing.md) — Testing di pattern regex e parser
- [Modulo 14 — Data Processing](14-data-processing.md) — Pipeline di elaborazione dati
- [Modulo 18 — Sicurezza](18-sicurezza.md) — ReDoS, input validation, sanitization
- [Modulo 29 — Pydantic e Validazione](29-pydantic-e-validazione.md) — Validazione con regex in `Field(pattern=...)`

---

## Glossario

| Termine | Definizione |
|---|---|
| **Anchor** | Asserzione a larghezza zero che corrisponde a una posizione nella stringa (es. `^`, `$`, `\b`), non a un carattere. |
| **Atomic group** | Gruppo `(?>...)` che impedisce il backtracking al suo interno una volta completato il match. Non supportato da `re`, disponibile in `regex`. |
| **Backtracking** | Meccanismo del motore NFA per cui, quando un percorso di matching fallisce, il motore torna all'ultimo punto di decisione e prova l'alternativa successiva. |
| **Backreference** | Riferimento `\1` o `(?P=nome)` a testo gia catturato da un gruppo precedente nello stesso match. |
| **Catastrophic backtracking** | Condizione in cui il backtracking esplode esponenzialmente, causando tempi di esecuzione praticamente infiniti. Vedi ReDoS. |
| **Character class** | Insieme di caratteri ammessi in una posizione del pattern, delimitato da `[...]`. Es. `[a-z]`, `[^0-9]`. |
| **Combining mark** | Carattere Unicode (categoria `Mn`) che si combina con il carattere precedente per formare un glifo composto (es. accento combinante U+0301). |
| **DFA** | Deterministic Finite Automaton. Motore regex che non fa backtracking e garantisce tempo lineare. Usato da `re2`, `grep -E`. |
| **Flag** | Modificatore del comportamento del motore regex: `IGNORECASE`, `MULTILINE`, `DOTALL`, `VERBOSE`, `ASCII`. |
| **Fuzzy matching** | Matching approssimato che tollera un numero configurabile di errori (inserzioni, delezioni, sostituzioni). Supportato dal modulo `regex`. |
| **Greedy** | Quantificatore che cattura la quantita massima di testo possibile. E il comportamento predefinito di `*`, `+`, `?`, `{n,m}`. |
| **Lazy** | Quantificatore che cattura la quantita minima di testo possibile. Si ottiene aggiungendo `?` dopo il quantificatore: `*?`, `+?`. |
| **Lookahead** | Asserzione `(?=...)` (positiva) o `(?!...)` (negativa) che verifica cosa segue senza consumare caratteri. |
| **Lookbehind** | Asserzione `(?<=...)` (positiva) o `(?<!...)` (negativa) che verifica cosa precede senza consumare caratteri. In `re` richiede lunghezza fissa. |
| **Match object** | Oggetto restituito da `re.match()`, `re.search()`, `re.finditer()` che contiene informazioni sul match: gruppi, posizioni, span. |
| **NFA** | Non-deterministic Finite Automaton. Motore regex con backtracking usato da Python `re`, Perl, Java, .NET. Supporta tutte le funzionalita avanzate ma puo avere complessita esponenziale. |
| **NFC** | Canonical Decomposition followed by Canonical Composition. Forma di normalizzazione Unicode che produce la rappresentazione precomposta. Raccomandata per confronti. |
| **NFD** | Canonical Decomposition. Forma di normalizzazione Unicode che produce la rappresentazione decomposta. |
| **Possessive quantifier** | Quantificatore `*+`, `++`, `?+` che cattura il massimo possibile e non rilascia mai caratteri tramite backtracking. Non supportato da `re`, disponibile in `regex`. |
| **Raw string** | Stringa con prefisso `r` (es. `r"\b\w+\b"`) in cui il backslash non e interpretato come escape di Python. Essenziale per le regex. |
| **ReDoS** | Regular Expression Denial of Service. Attacco che sfrutta pattern regex vulnerabili per causare tempi di esecuzione esponenziali su input malevoli. |
| **Shrinking** | In `unicodedata`: normalizzazione di compatibilita (NFKC/NFKD) che converte varianti tipografiche nella forma canonica. In Hypothesis: riduzione dell'input al caso minimo che causa il fallimento. |
| **Transliteration** | Conversione di caratteri da uno script a un altro (es. cirillico → latino). In Python si usa `unicodedata.normalize("NFD")` + rimozione combining marks come approssimazione. |
| **Unicode category** | Classificazione di ogni code point Unicode: `Lu` (lettera maiuscola), `Ll` (minuscola), `Nd` (cifra), `Zs` (spazio), `Mn` (combining mark), ecc. |
| **Word boundary** | Asserzione `\b` che corrisponde alla posizione tra un carattere `\w` e un carattere `\W`, o tra `\w` e l'inizio/fine della stringa. |
