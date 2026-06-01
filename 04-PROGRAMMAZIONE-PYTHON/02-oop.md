---
corso: "Programmazione Python"
fase: "1 — Fondamenti"
modulo: "02"
titolo: "Programmazione Orientata agli Oggetti (OOP)"
versione: "Python 3.12+"
livello: "Intermedio-Avanzato"
prerequisiti:
  - "01 — Fondamenti del Linguaggio"
  - "03 — Funzioni e Scope"
obiettivi:
  - "Padroneggiare classi, ereditarieta, polimorfismo e MRO"
  - "Utilizzare dataclass, NamedTuple e Protocol"
  - "Comprendere descriptor, metaclassi e __init_subclass__"
  - "Implementare ABC e interfacce con typing.Protocol"
  - "Applicare composizione, dependency injection e pattern OOP"
  - "Scrivere codice OOP testabile e manutenibile"
tag: [oop, classi, ereditarieta, polimorfismo, dataclass, Protocol, metaclassi, descriptor]
---

# Programmazione Orientata agli Oggetti (OOP) — Guida Completa

> **Modulo 02** · **Aggiornamento:** 2026-05-24 · **Versione:** Python 3.12+

> ### Obiettivi di apprendimento
>
> **Prerequisiti:** [Fondamenti del Linguaggio](01-fondamenti-linguaggio.md), [Funzioni e Scope](03-funzioni-scope.md)
>
> Al termine di questo modulo saprai:
> 1. Padroneggiare classi, ereditarieta, polimorfismo e MRO (Method Resolution Order)
> 2. Utilizzare dataclass, NamedTuple e frozen dataclass per dati strutturati
> 3. Comprendere descriptor, metaclassi e `__init_subclass__` per meta-programmazione
> 4. Implementare ABC e interfacce strutturali con `typing.Protocol`
> 5. Applicare composizione e dependency injection per codice disaccoppiato
> 6. Scrivere codice OOP testabile, manutenibile e conforme ai principi SOLID
>
> **Tempo stimato:** 8-10 ore · **Livello:** Intermedio-Avanzato

---

**Corso:** Programmazione Python — Percorso Completo
**Fase:** Fondamenti avanzati (modulo 2 di 35)
**Livello:** Intermedio → Avanzato
**Prerequisiti:** Modulo 01 (fondamenti del linguaggio), familiarità con funzioni, scope, namespace
**Tempo stimato:** 20-25 ore di studio + esercizi

### Obiettivi di apprendimento

Al termine di questo modulo lo studente sarà in grado di:

1. Progettare gerarchie di classi coerenti, applicando correttamente ereditarietà, composizione e mixin.
2. Comprendere e usare il protocollo descriptor, le metaclassi e `__init_subclass__` per personalizzare la creazione di classi.
3. Diagnosticare problemi legati alla MRO (C3 linearization), al diamond problem e all'uso cooperativo di `super()`.
4. Padroneggiare `dataclass` con le opzioni avanzate (`kw_only`, `match_args`, `slots`, `frozen`) e sapere quando preferirle a classi normali.
5. Implementare Protocol (PEP 544) per structural subtyping e ABC per nominal subtyping, scegliendo lo strumento giusto per ogni contesto.
6. Applicare design pattern OOP idiomatici in Python: Strategy con Protocol, Factory, Registry, Observer.
7. Evitare le trappole più comuni: variabili di classe mutabili, `__hash__`/`__eq__` incoerenti, MRO non risolvibile, descriptor vs property.

---

## Idee guida

1. **dataclasses > manual `__init__`.** Less boilerplate.
2. **`__slots__` per memory if many instances.**
3. **ABC per interfaces; Protocol per structural typing.**
4. **Composition over inheritance; mixin sparingly.**
5. **Metaclassi: potenti ma quasi sempre evitabili — preferire `__init_subclass__` e descriptor.**
6. **Il protocollo descriptor è il meccanismo su cui si reggono `property`, `classmethod`, `staticmethod` e il binding dei metodi.**
7. **`super()` è cooperativo: ogni classe nella MRO deve propagare la chiamata.**

---

## Mappa concettuale — Gerarchia di classi e protocolli

```
                            ┌────────────────┐
                            │    object       │  ← radice universale
                            └───────┬────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
      ┌───────▼───────┐    ┌───────▼───────┐    ┌────────▼───────┐
      │     type       │    │     ABC       │    │    Protocol    │
      │  (metaclasse)  │    │  (nominale)   │    │ (strutturale)  │
      └───────┬────────┘    └───────┬───────┘    └────────┬───────┘
              │                     │                     │
     crea classi            contratto esplicito    duck typing statico
     __new__, __init__      @abstractmethod        PEP 544
     __init_subclass__      register()             runtime_checkable
     __set_name__           collections.abc
              │                     │                     │
              ▼                     ▼                     ▼
    ┌──────────────────────────────────────────────────────────────┐
    │                    Classe concreta                           │
    │  ┌──────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐ │
    │  │ __init__ │  │ __slots__ │  │ @property │  │ descriptor│ │
    │  │ __repr__ │  │ @dataclass│  │ __get__   │  │ __set__   │ │
    │  │ __eq__   │  │ frozen    │  │ __delete__│  │ __set_    │ │
    │  │ __hash__ │  │ kw_only   │  │           │  │  name__   │ │
    │  └──────────┘  └───────────┘  └───────────┘  └───────────┘ │
    └──────────────────────────────────────────────────────────────┘
              │                           │
      ┌───────┴───────┐          ┌────────┴────────┐
      │  Ereditarietà │          │  Composizione   │
      │  (is-a)       │          │  (has-a)        │
      │  MRO / C3     │          │  Delega         │
      │  super()      │          │  Iniezione      │
      │  Mixin        │          │  Strategy       │
      └───────────────┘          └─────────────────┘

    Enum ──── StrEnum ──── IntEnum ──── Flag ──── IntFlag
```

---

## Indice

1. [Panoramica](#panoramica)
2. [Classi e Oggetti](#classi-e-oggetti)
3. [Incapsulamento](#incapsulamento)
4. [Ereditarietà](#ereditarietà)
5. [Polimorfismo](#polimorfismo)
6. [Metodi Speciali (Dunder Methods)](#metodi-speciali-dunder-methods)
7. [Composizione vs Ereditarietà](#composizione-vs-ereditarietà)
8. [Classi Speciali](#classi-speciali)
9. [Pattern OOP](#pattern-oop)
10. [Best Practices](#best-practices)
11. [Metaclassi](#metaclassi)
12. [Protocollo Descriptor](#protocollo-descriptor)
13. [MRO Approfondito — Linearizzazione C3](#mro-approfondito--linearizzazione-c3)
14. [Dataclass Approfondito](#dataclass-approfondito)
15. [`__slots__` Approfondito](#__slots__-approfondito)
16. [ABC Approfondito](#abc-approfondito)
17. [Protocol Approfondito — PEP 544](#protocol-approfondito--pep-544)
18. [Enum Approfondito](#enum-approfondito)
19. [Dunder Methods Approfondito](#dunder-methods-approfondito)
20. [Variabili di Classe vs Istanza — La Trappola Mutabile](#variabili-di-classe-vs-istanza--la-trappola-mutabile)
21. [Composizione vs Ereditarietà — Linee Guida Pratiche](#composizione-vs-ereditarietà--linee-guida-pratiche)
22. [Design Pattern Avanzati in Python OOP](#design-pattern-avanzati-in-python-oop)
23. [Troubleshooting](#troubleshooting)
24. [Esercizi](#esercizi)
25. [Auto-Valutazione](#auto-valutazione)
26. [Letture Consigliate](#letture-consigliate)
27. [Cross-link](#cross-link)
28. [Glossario](#glossario)

---

## Panoramica

La **Programmazione Orientata agli Oggetti** (Object-Oriented Programming, OOP) è un paradigma di programmazione che organizza il codice attorno a **oggetti** piuttosto che a funzioni e logica procedurale. Un oggetto è un'entità che racchiude al proprio interno sia i **dati** (attributi) sia i **comportamenti** (metodi) che operano su quei dati.

Python è un linguaggio **multi-paradigma**: supporta la programmazione procedurale, funzionale e orientata agli oggetti. In realtà, in Python *tutto è un oggetto* — numeri interi, stringhe, funzioni e persino le classi stesse sono oggetti. Questo rende l'OOP una parte naturale e profondamente integrata nel linguaggio.

I quattro pilastri fondamentali dell'OOP sono:

- **Incapsulamento** — raggruppare dati e metodi in un'unica entità, nascondendo i dettagli implementativi.
- **Ereditarietà** — creare nuove classi a partire da classi esistenti, riutilizzando e specializzando il comportamento.
- **Polimorfismo** — trattare oggetti di classi diverse attraverso un'interfaccia comune.
- **Astrazione** — esporre solo le informazioni essenziali, nascondendo la complessità interna.

Python adotta l'OOP fin dalle sue fondamenta: ogni valore è un oggetto, ogni tipo è una classe. Persino `int`, `list` e `NoneType` sono classi con metodi e attributi. Comprendere l'OOP in Python significa comprendere il funzionamento profondo del linguaggio stesso.

In questa guida esploreremo ciascuno di questi pilastri nel contesto di Python, con esempi pratici, pattern di design e best practices.

---

## Classi e Oggetti

Una **classe** è il concetto fondamentale dell'OOP. Rappresenta un modello (blueprint) che definisce la struttura (attributi) e il comportamento (metodi) di un certo tipo di oggetto. Un **oggetto** (o istanza) è una realizzazione concreta di quel modello: ogni oggetto ha i propri valori per gli attributi, pur condividendo la stessa struttura e gli stessi metodi definiti dalla classe.

La relazione tra classe e oggetto è analoga a quella tra un progetto architettonico e la casa costruita a partire da quel progetto: il progetto è uno, ma le case possono essere molte, ciascuna con le proprie finiture e i propri abitanti.

### Definizione di una classe

Si definisce una classe con la parola chiave `class`, seguita dal nome (per convenzione in `PascalCase`) e dai due punti. Il corpo della classe è un blocco indentato che contiene attributi e metodi:

```python
class Automobile:
    """Rappresenta un'automobile generica."""

    # Attributo di classe — condiviso tra tutte le istanze
    numero_ruote = 4

    def __init__(self, marca, modello, anno):
        """Costruttore: inizializza gli attributi dell'istanza."""
        self.marca = marca        # attributo di istanza
        self.modello = modello    # attributo di istanza
        self.anno = anno          # attributo di istanza
        self.velocita = 0         # attributo con valore predefinito

    def accelera(self, incremento):
        """Aumenta la velocità dell'automobile."""
        self.velocita += incremento
        return self.velocita

    def frena(self, decremento):
        """Diminuisce la velocità dell'automobile."""
        self.velocita = max(0, self.velocita - decremento)
        return self.velocita
```

### Il costruttore `__init__`

Il metodo `__init__` è il **costruttore** della classe (più precisamente, l'*inizializzatore*). Viene invocato automaticamente da Python ogni volta che si crea una nuova istanza. Il suo compito principale è inizializzare gli attributi dell'oggetto, assegnando valori iniziali che definiscono lo stato dell'istanza appena creata. Il metodo `__init__` non deve mai restituire un valore diverso da `None`; tentare di farlo provoca un `TypeError`.

È buona pratica inizializzare *tutti* gli attributi di istanza all'interno di `__init__`, anche quelli con valori predefiniti. Questo rende immediatamente chiaro quali dati l'oggetto gestisce, facilitando la lettura e la manutenzione del codice.

### Il parametro `self`

Il parametro `self` è un riferimento all'**istanza corrente** della classe. È il primo parametro di ogni metodo di istanza e permette di accedere agli attributi e ai metodi dell'oggetto. Quando si invoca un metodo come `auto.accelera(50)`, Python lo traduce internamente in `Automobile.accelera(auto, 50)`, passando automaticamente l'istanza come primo argomento.

Il nome `self` è una convenzione fortissima nella comunità Python — tecnicamente si potrebbe usare qualsiasi nome, ma farlo sarebbe considerato una cattiva pratica e renderebbe il codice molto meno leggibile per altri sviluppatori.

### Attributi di istanza vs attributi di classe

```python
class Contatore:
    # Attributo di classe — condiviso tra tutte le istanze
    totale_istanze = 0

    def __init__(self, nome):
        # Attributi di istanza — unici per ogni oggetto
        self.nome = nome
        self.conteggio = 0
        Contatore.totale_istanze += 1

    def incrementa(self):
        self.conteggio += 1

c1 = Contatore("alfa")
c2 = Contatore("beta")

print(Contatore.totale_istanze)  # 2 — attributo di classe
print(c1.conteggio)              # 0 — attributo di istanza
```

Gli **attributi di classe** sono definiti direttamente nel corpo della classe e sono condivisi da tutte le istanze. Gli **attributi di istanza** sono definiti dentro `__init__` (o in altri metodi tramite `self`) e sono unici per ciascun oggetto.

Attenzione: se si assegna un valore a un attributo di istanza con lo stesso nome di un attributo di classe, l'attributo di istanza *oscura* quello di classe per quell'oggetto specifico, senza modificare l'attributo di classe stesso.

### Istanziazione

Per creare un oggetto (istanza) si "chiama" la classe come se fosse una funzione, passando gli argomenti richiesti dal costruttore `__init__` (escluso `self`, che Python gestisce automaticamente):

```python
auto = Automobile("Fiat", "500", 2023)
print(auto.marca)       # "Fiat"
print(auto.accelera(50))  # 50
```

Dietro le quinte, Python esegue due operazioni: prima crea un nuovo oggetto vuoto (tramite `__new__`), poi lo inizializza chiamando `__init__` con gli argomenti forniti. Nella stragrande maggioranza dei casi non è necessario preoccuparsi di `__new__` — verrà approfondito nella sezione dedicata ai metodi speciali.

### Metodi di istanza, di classe e statici

Oltre ai metodi di istanza (quelli che ricevono `self`), Python supporta altri due tipi di metodi:

```python
class DataHelper:
    formato_predefinito = "%Y-%m-%d"

    def __init__(self, data_str):
        self.data_str = data_str

    def mostra(self):
        """Metodo di istanza — accede all'istanza tramite self."""
        return f"Data: {self.data_str}"

    @classmethod
    def da_timestamp(cls, timestamp):
        """Metodo di classe — riceve la classe (cls) anziché l'istanza.
        Utile come factory method alternativo."""
        from datetime import datetime
        data = datetime.fromtimestamp(timestamp)
        return cls(data.strftime(cls.formato_predefinito))

    @staticmethod
    def è_bisestile(anno):
        """Metodo statico — non riceve né self né cls.
        È una funzione di utilità logicamente collegata alla classe."""
        return anno % 4 == 0 and (anno % 100 != 0 or anno % 400 == 0)

# Metodo di istanza
dh = DataHelper("2026-03-27")
print(dh.mostra())             # "Data: 2026-03-27"

# Metodo di classe — alternativa al costruttore
dh2 = DataHelper.da_timestamp(1774800000)
print(dh2.mostra())

# Metodo statico — non richiede un'istanza
print(DataHelper.è_bisestile(2024))   # True
```

I **metodi di classe** (`@classmethod`) ricevono la classe come primo argomento (`cls`) e sono spesso usati come costruttori alternativi. I **metodi statici** (`@staticmethod`) non ricevono riferimenti impliciti e si comportano come funzioni normali, ma sono definiti dentro la classe per organizzazione logica.

### I metodi `__str__` e `__repr__`

Questi due metodi speciali controllano la rappresentazione testuale di un oggetto:

```python
class Punto:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __str__(self):
        """Rappresentazione leggibile — usata da print() e str()."""
        return f"Punto({self.x}, {self.y})"

    def __repr__(self):
        """Rappresentazione tecnica — usata nella shell e in repr().
        Dovrebbe restituire una stringa che, idealmente, permetta
        di ricreare l'oggetto."""
        return f"Punto(x={self.x!r}, y={self.y!r})"

p = Punto(3, 7)
print(p)        # Punto(3, 7)        — chiama __str__
print(repr(p))  # Punto(x=3, y=7)   — chiama __repr__
```

La regola generale è: `__repr__` è per gli sviluppatori, `__str__` è per gli utenti. Se si definisce solo `__repr__`, Python lo userà anche al posto di `__str__` quando quest'ultimo non è definito.

---

## Incapsulamento

L'incapsulamento è il principio di **nascondere i dettagli implementativi** di un oggetto, esponendo solo un'interfaccia pubblica controllata. Python non possiede veri modificatori di accesso (come `private` o `protected` in Java), ma utilizza **convenzioni di denominazione** per comunicare l'intento.

### Convenzioni di visibilità

```python
class ContoBancario:
    def __init__(self, titolare, saldo_iniziale=0):
        self.titolare = titolare           # pubblico
        self._valuta = "EUR"               # protetto (convenzione)
        self.__saldo = saldo_iniziale      # privato (name mangling)

    def deposita(self, importo):
        """Metodo pubblico per depositare denaro."""
        if importo > 0:
            self.__saldo += importo

    def _calcola_interessi(self):
        """Metodo protetto — uso interno o nelle sottoclassi."""
        return self.__saldo * 0.02

    def __verifica_fondi(self, importo):
        """Metodo privato — uso strettamente interno."""
        return self.__saldo >= importo
```

- **Pubblico** (`titolare`): accessibile ovunque, fa parte dell'interfaccia pubblica della classe.
- **Protetto** (`_valuta`): la convenzione del singolo underscore indica che l'attributo non dovrebbe essere usato all'esterno della classe o delle sue sottoclassi. Python non lo impedisce tecnicamente.
- **Privato** (`__saldo`): il doppio underscore attiva il **name mangling**.

### Name Mangling

Quando un attributo inizia con due underscore (e non termina con due underscore), Python ne modifica internamente il nome aggiungendo il prefisso `_NomeClasse`:

```python
conto = ContoBancario("Mario Rossi", 1000)

# print(conto.__saldo)                # AttributeError!
print(conto._ContoBancario__saldo)     # 1000 — funziona, ma è fortemente sconsigliato
```

Il name mangling serve principalmente per evitare conflitti di nomi nelle gerarchie di ereditarietà, non come meccanismo di sicurezza. Se una classe `Base` e una sottoclasse `Derivata` definiscono entrambe un attributo `__dato`, il name mangling li trasforma rispettivamente in `_Base__dato` e `_Derivata__dato`, evitando collisioni accidentali.

È importante sottolineare che la filosofia di Python riguardo alla privacy è riassunta dalla frase "siamo tutti adulti consenzienti" (*we're all consenting adults here*). Il linguaggio si affida alla disciplina dello sviluppatore piuttosto che a meccanismi di enforcement rigidi.

### Il decoratore `@property`

Il decoratore `@property` permette di definire metodi che si comportano come attributi, fornendo un'interfaccia pulita per getter, setter e deleter:

```python
class Temperatura:
    def __init__(self, celsius=0):
        self._celsius = celsius   # attributo protetto

    @property
    def celsius(self):
        """Getter — restituisce il valore in Celsius."""
        return self._celsius

    @celsius.setter
    def celsius(self, valore):
        """Setter — imposta il valore con validazione."""
        if valore < -273.15:
            raise ValueError("La temperatura non può essere inferiore allo zero assoluto")
        self._celsius = valore

    @celsius.deleter
    def celsius(self):
        """Deleter — resetta il valore."""
        print("Eliminazione del valore di temperatura")
        self._celsius = 0

    @property
    def fahrenheit(self):
        """Proprietà calcolata — solo lettura."""
        return self._celsius * 9 / 5 + 32

temp = Temperatura(25)
print(temp.celsius)      # 25     — chiama il getter
print(temp.fahrenheit)   # 77.0   — proprietà calcolata

temp.celsius = 30        # chiama il setter
# temp.celsius = -300    # ValueError!

del temp.celsius         # chiama il deleter
```

### Validazione nei setter

Le property sono lo strumento ideale per implementare la validazione dei dati:

```python
class Utente:
    def __init__(self, nome, eta, email):
        # Questi assegnamenti passano attraverso i setter
        self.nome = nome
        self.eta = eta
        self.email = email

    @property
    def nome(self):
        return self._nome

    @nome.setter
    def nome(self, valore):
        if not isinstance(valore, str) or len(valore.strip()) == 0:
            raise ValueError("Il nome deve essere una stringa non vuota")
        self._nome = valore.strip()

    @property
    def eta(self):
        return self._eta

    @eta.setter
    def eta(self, valore):
        if not isinstance(valore, int) or valore < 0 or valore > 150:
            raise ValueError("L'età deve essere un intero tra 0 e 150")
        self._eta = valore

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, valore):
        if "@" not in valore or "." not in valore.split("@")[-1]:
            raise ValueError("Indirizzo email non valido")
        self._email = valore.lower()
```

---

## Ereditarietà

L'ereditarietà permette di creare una nuova classe (**sottoclasse** o classe figlia) a partire da una classe esistente (**superclasse** o classe genitore), ereditandone attributi e metodi. La sottoclasse può estendere il genitore aggiungendo nuovi attributi e metodi, oppure sovrascrivere (override) i metodi ereditati per specializzarne il comportamento.

In Python, tutte le classi ereditano implicitamente dalla classe `object`, che è la radice della gerarchia di classi. `object` fornisce implementazioni predefinite di metodi come `__repr__`, `__eq__` e `__hash__`.

### Ereditarietà singola

```python
class Animale:
    def __init__(self, nome, eta):
        self.nome = nome
        self.eta = eta

    def parla(self):
        raise NotImplementedError("Le sottoclassi devono implementare parla()")

    def descrizione(self):
        return f"{self.nome}, {self.eta} anni"


class Cane(Animale):
    def __init__(self, nome, eta, razza):
        super().__init__(nome, eta)   # chiama il costruttore del genitore
        self.razza = razza

    def parla(self):
        return f"{self.nome} dice: Bau!"

    def riporta(self, oggetto):
        return f"{self.nome} riporta {oggetto}"


class Gatto(Animale):
    def __init__(self, nome, eta, indoor=True):
        super().__init__(nome, eta)
        self.indoor = indoor

    def parla(self):
        return f"{self.nome} dice: Miao!"


rex = Cane("Rex", 5, "Pastore Tedesco")
print(rex.descrizione())   # "Rex, 5 anni" — metodo ereditato
print(rex.parla())         # "Rex dice: Bau!" — metodo sovrascritto
print(rex.riporta("palla"))  # "Rex riporta palla" — metodo esclusivo
```

### La funzione `super()`

La funzione `super()` restituisce un oggetto proxy che delega le chiamate di metodo alla classe genitore. È fondamentale per:

- Invocare il costruttore del genitore in `__init__`.
- Estendere (anziché sostituire) i metodi ereditati.
- Gestire correttamente l'ereditarietà multipla.

```python
class Veicolo:
    def __init__(self, marca, velocita_max):
        self.marca = marca
        self.velocita_max = velocita_max

class VeicoloElettrico(Veicolo):
    def __init__(self, marca, velocita_max, capacita_batteria):
        super().__init__(marca, velocita_max)
        self.capacita_batteria = capacita_batteria
        self.carica_attuale = 100
```

### Override dei metodi

Il **method overriding** si verifica quando una sottoclasse ridefinisce un metodo ereditato dal genitore:

```python
class Forma:
    def area(self):
        return 0

    def descrizione(self):
        return f"Forma con area {self.area():.2f}"

class Cerchio(Forma):
    def __init__(self, raggio):
        self.raggio = raggio

    def area(self):
        """Override: fornisce il calcolo specifico per il cerchio."""
        import math
        return math.pi * self.raggio ** 2

class Rettangolo(Forma):
    def __init__(self, base, altezza):
        self.base = base
        self.altezza = altezza

    def area(self):
        """Override: fornisce il calcolo specifico per il rettangolo."""
        return self.base * self.altezza

c = Cerchio(5)
print(c.descrizione())  # "Forma con area 78.54" — usa l'area() del Cerchio
```

### Ereditarietà multipla

Python supporta l'ereditarietà multipla, dove una classe può ereditare da più classi genitore contemporaneamente. Questa è una caratteristica potente ma che va usata con cautela, poiché può introdurre complessità e ambiguità — il cosiddetto "problema del diamante" (diamond problem), dove la stessa classe base appare più volte nella gerarchia:

```python
class Volante:
    def vola(self):
        return "Sto volando!"

class Nuotante:
    def nuota(self):
        return "Sto nuotando!"

class Anatra(Animale, Volante, Nuotante):
    def __init__(self, nome, eta):
        super().__init__(nome, eta)

    def parla(self):
        return f"{self.nome} dice: Qua!"

papera = Anatra("Paperino", 3)
print(papera.vola())    # "Sto volando!"
print(papera.nuota())   # "Sto nuotando!"
print(papera.parla())   # "Paperino dice: Qua!"
```

### Method Resolution Order (MRO) — Linearizzazione C3

Quando una classe eredita da più genitori, Python utilizza l'algoritmo di **linearizzazione C3** per determinare l'ordine in cui vengono cercati i metodi. Questo ordine è il **Method Resolution Order** (MRO):

```python
class A:
    def saluta(self):
        return "Ciao da A"

class B(A):
    def saluta(self):
        return "Ciao da B"

class C(A):
    def saluta(self):
        return "Ciao da C"

class D(B, C):
    pass

# Visualizzare la MRO
print(D.__mro__)
# (<class 'D'>, <class 'B'>, <class 'C'>, <class 'A'>, <class 'object'>)

d = D()
print(d.saluta())  # "Ciao da B" — B viene prima di C nella MRO
```

La MRO garantisce che:
1. Le sottoclassi vengano controllate prima delle superclassi.
2. L'ordine di elencazione dei genitori venga rispettato.
3. Ogni classe appaia una sola volta nella linearizzazione.

### `isinstance()` e `issubclass()`

```python
rex = Cane("Rex", 5, "Labrador")

print(isinstance(rex, Cane))     # True
print(isinstance(rex, Animale))  # True — la relazione è transitiva
print(isinstance(rex, Gatto))    # False

print(issubclass(Cane, Animale))     # True
print(issubclass(Cane, object))      # True — tutto eredita da object
print(issubclass(Animale, Cane))     # False
```

### Pattern Mixin

Un **mixin** è una classe progettata per fornire funzionalità aggiuntive senza essere usata come classe base autonoma:

```python
class SerializzabileMixin:
    """Mixin che aggiunge la capacità di serializzazione JSON."""
    def to_json(self):
        import json
        return json.dumps(self.__dict__, default=str, indent=2)

    @classmethod
    def from_json(cls, json_str):
        import json
        dati = json.loads(json_str)
        return cls(**dati)

class TimestampMixin:
    """Mixin che aggiunge un timestamp di creazione."""
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

    def imposta_timestamp(self):
        from datetime import datetime
        self.creato_il = datetime.now().isoformat()

class Prodotto(SerializzabileMixin, TimestampMixin):
    def __init__(self, nome, prezzo):
        self.nome = nome
        self.prezzo = prezzo
        self.imposta_timestamp()

p = Prodotto("Laptop", 999.99)
print(p.to_json())
# {
#   "nome": "Laptop",
#   "prezzo": 999.99,
#   "creato_il": "2026-03-27T10:30:00.000000"
# }
```

I mixin dovrebbero essere piccoli, focalizzati su una singola funzionalità, e non dovrebbero avere un proprio `__init__` complesso.

---

## Polimorfismo

Il polimorfismo (dal greco "molte forme") è la capacità di trattare oggetti di classi diverse attraverso un'interfaccia comune. In Python il polimorfismo è particolarmente flessibile grazie al **duck typing**.

### Duck Typing

In Python, il tipo di un oggetto è meno importante di ciò che l'oggetto *sa fare*. Come recita il detto: "Se cammina come un'anatra e starnazza come un'anatra, allora è un'anatra."

```python
class Cane:
    def parla(self):
        return "Bau!"

class Gatto:
    def parla(self):
        return "Miao!"

class Pappagallo:
    def parla(self):
        return "Ciao bello!"

# Nessuna relazione di ereditarietà — funziona grazie al duck typing
def fai_parlare(animale):
    """Funziona con qualsiasi oggetto che abbia un metodo parla()."""
    print(animale.parla())

for animale in [Cane(), Gatto(), Pappagallo()]:
    fai_parlare(animale)
# Bau!
# Miao!
# Ciao bello!
```

### Overloading degli operatori

Python permette di ridefinire il comportamento degli operatori per le classi personalizzate tramite i metodi speciali:

```python
class Vettore:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, altro):
        """Operatore +"""
        return Vettore(self.x + altro.x, self.y + altro.y)

    def __eq__(self, altro):
        """Operatore =="""
        if not isinstance(altro, Vettore):
            return NotImplemented
        return self.x == altro.x and self.y == altro.y

    def __lt__(self, altro):
        """Operatore < — confronta la magnitudine."""
        return self.magnitudine() < altro.magnitudine()

    def __len__(self):
        """Funzione len() — restituisce la dimensione (2D)."""
        return 2

    def __getitem__(self, indice):
        """Accesso tramite indice — v[0], v[1]."""
        if indice == 0:
            return self.x
        elif indice == 1:
            return self.y
        raise IndexError("Indice fuori intervallo")

    def __contains__(self, valore):
        """Operatore in."""
        return valore in (self.x, self.y)

    def __iter__(self):
        """Supporto per l'iterazione."""
        yield self.x
        yield self.y

    def __call__(self, scalare):
        """Rende l'oggetto chiamabile — moltiplicazione scalare."""
        return Vettore(self.x * scalare, self.y * scalare)

    def __repr__(self):
        return f"Vettore({self.x}, {self.y})"

    def magnitudine(self):
        return (self.x ** 2 + self.y ** 2) ** 0.5

v1 = Vettore(3, 4)
v2 = Vettore(1, 2)

print(v1 + v2)        # Vettore(4, 6)
print(v1 == v2)        # False
print(v1 < v2)         # False — 5.0 < 2.236
print(len(v1))         # 2
print(v1[0])           # 3
print(3 in v1)         # True
print(list(v1))        # [3, 4]
print(v1(10))          # Vettore(30, 40) — chiamata come funzione
```

### Context Manager tramite `__enter__` e `__exit__`

```python
class GestoreFile:
    def __init__(self, percorso, modalita="r"):
        self.percorso = percorso
        self.modalita = modalita
        self.file = None

    def __enter__(self):
        """Viene chiamato all'ingresso del blocco with."""
        self.file = open(self.percorso, self.modalita)
        return self.file

    def __exit__(self, tipo_eccezione, valore_eccezione, traceback):
        """Viene chiamato all'uscita del blocco with, anche in caso di eccezione."""
        if self.file:
            self.file.close()
        # Restituire False (o None) rilancia l'eccezione,
        # True la sopprime
        return False

with GestoreFile("dati.txt", "w") as f:
    f.write("Ciao, mondo!")
# Il file viene chiuso automaticamente
```

### Abstract Base Classes (ABC)

Le **classi base astratte** definiscono un'interfaccia che le sottoclassi *devono* implementare:

```python
from abc import ABC, abstractmethod

class Forma(ABC):
    """Classe base astratta per le forme geometriche."""

    @abstractmethod
    def area(self):
        """Ogni forma deve implementare il calcolo dell'area."""
        pass

    @abstractmethod
    def perimetro(self):
        """Ogni forma deve implementare il calcolo del perimetro."""
        pass

    def descrizione(self):
        """Metodo concreto — ereditato da tutte le sottoclassi."""
        return f"{self.__class__.__name__}: area={self.area():.2f}, perimetro={self.perimetro():.2f}"

# forma = Forma()  # TypeError! Non si può istanziare una classe astratta

class Quadrato(Forma):
    def __init__(self, lato):
        self.lato = lato

    def area(self):
        return self.lato ** 2

    def perimetro(self):
        return 4 * self.lato

q = Quadrato(5)
print(q.descrizione())  # "Quadrato: area=25.00, perimetro=20.00"
```

Se una sottoclasse non implementa tutti i metodi astratti, anch'essa diventa astratta e non può essere istanziata.

### Protocol (Structural Subtyping, Python 3.8+)

I `Protocol` del modulo `typing` permettono di definire interfacce **strutturali** — un tipo è conforme a un protocollo se implementa i metodi richiesti, senza bisogno di ereditarietà esplicita:

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class Disegnabile(Protocol):
    def disegna(self) -> str:
        ...

class Cerchio:
    def disegna(self) -> str:
        return "Disegno un cerchio"

class Testo:
    def disegna(self) -> str:
        return "Disegno del testo"

class Numero:
    pass  # Non ha disegna()

def renderizza(elemento: Disegnabile) -> None:
    print(elemento.disegna())

renderizza(Cerchio())   # Funziona — Cerchio ha disegna()
renderizza(Testo())     # Funziona — Testo ha disegna()

# Verifica a runtime con @runtime_checkable
print(isinstance(Cerchio(), Disegnabile))  # True
print(isinstance(Numero(), Disegnabile))   # False
```

I Protocol sono particolarmente utili per il type checking statico con strumenti come mypy, e rappresentano l'approccio pythonic alla definizione di interfacce. La differenza fondamentale rispetto a ABC è che le classi non devono ereditare esplicitamente dal protocollo: basta che implementino i metodi richiesti. Questo approccio è detto **structural subtyping** (sottotipizzazione strutturale), in contrasto con il **nominal subtyping** (sottotipizzazione nominale) delle ABC.

---

## Metodi Speciali (Dunder Methods)

I **dunder methods** (da "double underscore", cioè "doppio underscore") sono metodi speciali il cui nome inizia e termina con due underscore (es. `__init__`, `__str__`, `__add__`). Python li invoca automaticamente in determinate situazioni — ad esempio quando si usa un operatore, si chiama una funzione built-in, o si accede a un attributo. I dunder methods permettono di personalizzare profondamente il comportamento degli oggetti, facendoli integrare naturalmente con la sintassi e le funzioni built-in del linguaggio.

Non bisogna mai inventare nuovi dunder methods con nomi personalizzati: lo spazio dei nomi `__nome__` è riservato a Python e al suo modello di dati.

### Costruzione e distruzione

```python
class Risorsa:
    _istanze_attive = 0

    def __new__(cls, *args, **kwargs):
        """Crea una nuova istanza PRIMA di __init__.
        Raramente sovrascritto, utile per Singleton e classi immutabili."""
        print(f"__new__: creazione istanza di {cls.__name__}")
        istanza = super().__new__(cls)
        return istanza

    def __init__(self, nome):
        """Inizializza l'istanza dopo la creazione."""
        print(f"__init__: inizializzazione di {nome}")
        self.nome = nome
        Risorsa._istanze_attive += 1

    def __del__(self):
        """Distruttore — chiamato quando l'oggetto viene deallocato.
        ATTENZIONE: il momento della chiamata non è garantito."""
        Risorsa._istanze_attive -= 1
        print(f"__del__: {self.nome} distrutto")
```

Il metodo `__new__` è un metodo statico che crea e restituisce l'istanza. È invocato prima di `__init__` e di solito viene sovrascritto solo in casi specifici come il pattern Singleton o per le classi immutabili (es. sottoclassi di `int`, `str`, `tuple`).

### Rappresentazione come stringa

```python
class Colore:
    def __init__(self, r, g, b):
        self.r = r
        self.g = g
        self.b = b

    def __str__(self):
        """Per print() e str() — leggibile dall'utente."""
        return f"rgb({self.r}, {self.g}, {self.b})"

    def __repr__(self):
        """Per la shell e repr() — non ambiguo, riproducibile."""
        return f"Colore(r={self.r}, g={self.g}, b={self.b})"

    def __format__(self, spec):
        """Per f-string e format() con specifica personalizzata."""
        if spec == "hex":
            return f"#{self.r:02x}{self.g:02x}{self.b:02x}"
        elif spec == "css":
            return f"rgb({self.r}, {self.g}, {self.b})"
        return str(self)

c = Colore(255, 128, 0)
print(f"{c}")        # rgb(255, 128, 0)
print(f"{c:hex}")    # #ff8000
print(f"{c:css}")    # rgb(255, 128, 0)
```

### Metodi di confronto e `@total_ordering`

```python
from functools import total_ordering

@total_ordering
class Studente:
    """Con @total_ordering basta definire __eq__ e uno tra __lt__, __gt__,
    __le__, __ge__. Il decoratore genera automaticamente gli altri."""

    def __init__(self, nome, voto):
        self.nome = nome
        self.voto = voto

    def __eq__(self, altro):
        if not isinstance(altro, Studente):
            return NotImplemented
        return self.voto == altro.voto

    def __lt__(self, altro):
        if not isinstance(altro, Studente):
            return NotImplemented
        return self.voto < altro.voto

    # @total_ordering genera __le__, __gt__, __ge__ automaticamente

s1 = Studente("Anna", 28)
s2 = Studente("Marco", 30)

print(s1 < s2)    # True
print(s1 >= s2)   # False — generato da @total_ordering
print(s1 != s2)   # True
```

Restituire `NotImplemented` (non `NotImplementedError`!) permette a Python di provare l'operazione al contrario (es. `altro.__gt__(self)`) prima di lanciare un errore.

### Operatori aritmetici

```python
class Denaro:
    def __init__(self, importo, valuta="EUR"):
        self.importo = round(importo, 2)
        self.valuta = valuta

    def __add__(self, altro):
        """self + altro"""
        if isinstance(altro, Denaro):
            if self.valuta != altro.valuta:
                raise ValueError("Valute diverse")
            return Denaro(self.importo + altro.importo, self.valuta)
        return NotImplemented

    def __radd__(self, altro):
        """altro + self — chiamato se altro non sa gestire l'operazione."""
        if altro == 0:  # Utile per sum()
            return self
        return NotImplemented

    def __iadd__(self, altro):
        """self += altro — operazione in-place."""
        if isinstance(altro, Denaro):
            if self.valuta != altro.valuta:
                raise ValueError("Valute diverse")
            self.importo = round(self.importo + altro.importo, 2)
            return self
        return NotImplemented

    def __mul__(self, scalare):
        """self * scalare"""
        if isinstance(scalare, (int, float)):
            return Denaro(self.importo * scalare, self.valuta)
        return NotImplemented

    def __rmul__(self, scalare):
        """scalare * self"""
        return self.__mul__(scalare)

    def __repr__(self):
        return f"Denaro({self.importo}, '{self.valuta}')"

a = Denaro(10.50)
b = Denaro(5.30)
print(a + b)         # Denaro(15.8, 'EUR')
print(a * 3)         # Denaro(31.5, 'EUR')
print(2 * b)         # Denaro(10.6, 'EUR')  — usa __rmul__
print(sum([a, b]))   # Denaro(15.8, 'EUR')  — usa __radd__ con 0
```

### Metodi container

```python
class Collezione:
    """Una collezione personalizzata con supporto completo per i protocolli container."""

    def __init__(self, *elementi):
        self._dati = list(elementi)

    def __len__(self):
        """len(collezione)"""
        return len(self._dati)

    def __getitem__(self, indice):
        """collezione[indice] — supporta anche lo slicing."""
        if isinstance(indice, slice):
            return Collezione(*self._dati[indice])
        return self._dati[indice]

    def __setitem__(self, indice, valore):
        """collezione[indice] = valore"""
        self._dati[indice] = valore

    def __delitem__(self, indice):
        """del collezione[indice]"""
        del self._dati[indice]

    def __contains__(self, elemento):
        """elemento in collezione"""
        return elemento in self._dati

    def __iter__(self):
        """for elemento in collezione"""
        return iter(self._dati)

    def __next__(self):
        """Supporto per next() — usato con iteratori espliciti."""
        # In genere si usa __iter__ per restituire un iteratore dedicato
        pass

    def __repr__(self):
        return f"Collezione({', '.join(repr(e) for e in self._dati)})"

c = Collezione(1, 2, 3, 4, 5)
print(len(c))       # 5
print(c[2])         # 3
print(3 in c)       # True
c[0] = 10
print(list(c))      # [10, 2, 3, 4, 5]
```

### Accesso agli attributi

```python
class OggettoDinamico:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __getattr__(self, nome):
        """Chiamato SOLO quando l'attributo NON viene trovato normalmente.
        Utile per valori predefiniti o attributi calcolati."""
        return f"Attributo '{nome}' non trovato — valore predefinito"

    def __setattr__(self, nome, valore):
        """Chiamato per OGNI assegnamento di attributo.
        Attenzione: usare self.__dict__[nome] per evitare ricorsione."""
        print(f"Impostazione: {nome} = {valore}")
        self.__dict__[nome] = valore

    def __delattr__(self, nome):
        """Chiamato quando si elimina un attributo con del."""
        print(f"Eliminazione: {nome}")
        del self.__dict__[nome]

    def __getattribute__(self, nome):
        """Chiamato per OGNI accesso ad attributo — prima di __getattr__.
        Usare con estrema cautela, può causare ricorsione infinita."""
        return super().__getattribute__(nome)
```

La differenza cruciale: `__getattr__` è chiamato solo come "ultima risorsa" quando l'attributo non esiste; `__getattribute__` è chiamato per *ogni* accesso a qualsiasi attributo.

### Hashing

```python
class PuntoImmutabile:
    """Per usare un oggetto come chiave di dizionario o in un set,
    deve essere hashable — __hash__ e __eq__ devono essere coerenti."""

    def __init__(self, x, y):
        self._x = x
        self._y = y

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y

    def __eq__(self, altro):
        if not isinstance(altro, PuntoImmutabile):
            return NotImplemented
        return self._x == altro._x and self._y == altro._y

    def __hash__(self):
        """Regola fondamentale: se a == b, allora hash(a) == hash(b)."""
        return hash((self._x, self._y))

# Ora possiamo usarlo come chiave
distanze = {PuntoImmutabile(0, 0): "origine", PuntoImmutabile(1, 1): "unità"}
```

Se si definisce `__eq__` senza `__hash__`, Python imposta `__hash__` a `None`, rendendo l'oggetto non hashable. Questo comportamento è intenzionale: se due oggetti sono uguali secondo `__eq__`, devono avere lo stesso hash. Poiché gli oggetti mutabili possono cambiare stato (e quindi il risultato di `__eq__`), sarebbe pericoloso permettere di usarli come chiavi di dizionario. Per le classi immutabili, definire sempre `__hash__` coerentemente con `__eq__`.

---

## Composizione vs Ereditarietà

Due approcci fondamentali per costruire relazioni tra classi. La scelta tra i due influenza profondamente la flessibilità e la manutenibilità del codice. Mentre l'ereditarietà modella una relazione di specializzazione ("è un tipo di"), la composizione modella una relazione di contenimento ("contiene" o "usa"). Capire quando applicare ciascun approccio è una delle competenze più importanti nella progettazione orientata agli oggetti.

### Relazione "is-a" vs "has-a"

- **Ereditarietà (is-a)**: un Cane *è* un Animale.
- **Composizione (has-a)**: un'Automobile *ha* un Motore.

### Esempio con ereditarietà

```python
class Motore:
    def avvia(self):
        return "Motore avviato"

# Approccio con ereditarietà — SBAGLIATO concettualmente
class Automobile(Motore):
    """Un'Automobile non È un Motore!"""
    pass
```

### Esempio con composizione

```python
class Motore:
    def __init__(self, cilindrata, tipo="benzina"):
        self.cilindrata = cilindrata
        self.tipo = tipo
        self.acceso = False

    def avvia(self):
        self.acceso = True
        return f"Motore {self.tipo} {self.cilindrata}cc avviato"

    def spegni(self):
        self.acceso = False
        return "Motore spento"

class Trasmissione:
    def __init__(self, tipo="manuale", marce=6):
        self.tipo = tipo
        self.marce = marce
        self.marcia_attuale = 0

    def cambia_marcia(self, marcia):
        if 0 <= marcia <= self.marce:
            self.marcia_attuale = marcia
            return f"Marcia {marcia} inserita"
        return "Marcia non valida"

class Automobile:
    """Composizione: l'auto HA un motore e una trasmissione."""

    def __init__(self, marca, modello):
        self.marca = marca
        self.modello = modello
        self.motore = Motore(1600)                    # composizione
        self.trasmissione = Trasmissione("manuale")   # composizione

    def avvia(self):
        return self.motore.avvia()   # delega al componente

    def cambia_marcia(self, marcia):
        return self.trasmissione.cambia_marcia(marcia)

auto = Automobile("Fiat", "Panda")
print(auto.avvia())                # "Motore benzina 1600cc avviato"
print(auto.cambia_marcia(1))       # "Marcia 1 inserita"
```

### Quando usare quale approccio

**Usa l'ereditarietà quando:**
- Esiste una vera relazione "è un" (un Cane è un Animale).
- Vuoi sfruttare il polimorfismo tramite una gerarchia di tipi.
- La sottoclasse è una *specializzazione* del genitore.

**Usa la composizione quando:**
- Esiste una relazione "ha un" (un'Automobile ha un Motore).
- Vuoi maggiore flessibilità nel cambiare i componenti.
- Vuoi evitare gerarchie profonde e fragili.
- Devi combinare funzionalità da più fonti senza i problemi dell'ereditarietà multipla.

La regola d'oro nel design OOP è **"prefer composition over inheritance"** (preferisci la composizione all'ereditarietà). L'ereditarietà crea un accoppiamento forte tra le classi: ogni modifica alla superclasse può avere effetti imprevisti sulle sottoclassi (il cosiddetto "fragile base class problem"). La composizione mantiene le classi indipendenti e flessibili, permettendo di sostituire i componenti senza influenzare il resto del sistema.

Un buon indicatore: se vi trovate a sovrascrivere molti metodi della classe genitore per "disabilitarli" o cambiarli radicalmente, probabilmente state forzando una relazione di ereditarietà dove la composizione sarebbe più appropriata.

---

## Classi Speciali

Python offre diverse classi e decoratori speciali che semplificano compiti comuni nella programmazione orientata agli oggetti. Le `dataclass` eliminano il codice ripetitivo per le classi incentrate sui dati, le `Enum` rappresentano insiemi fissi di costanti, e `__slots__` offre un'ottimizzazione della memoria per le classi con attributi fissi.

### dataclass (Python 3.7+)

Le **dataclass** (introdotte con la PEP 557) riducono drasticamente il codice boilerplate necessario per le classi che servono principalmente a contenere dati. Il decoratore `@dataclass` analizza le annotazioni di tipo della classe e genera automaticamente i metodi `__init__`, `__repr__` e `__eq__`:

```python
from dataclasses import dataclass, field
from typing import List

@dataclass
class Prodotto:
    """Il decoratore genera automaticamente __init__, __repr__, __eq__."""
    nome: str
    prezzo: float
    quantita: int = 0   # valore predefinito

p1 = Prodotto("Laptop", 999.99, 5)
p2 = Prodotto("Laptop", 999.99, 5)
print(p1)           # Prodotto(nome='Laptop', prezzo=999.99, quantita=5)
print(p1 == p2)     # True — __eq__ generato automaticamente
```

#### `field()` e `default_factory`

```python
@dataclass
class Squadra:
    nome: str
    giocatori: List[str] = field(default_factory=list)  # factory per mutabili
    _punteggio: int = field(default=0, repr=False)       # escluso da repr
    id_interno: str = field(init=False)                  # escluso da __init__

    def __post_init__(self):
        """Chiamato dopo __init__ — per logica di inizializzazione aggiuntiva."""
        self.id_interno = f"SQ-{self.nome.upper()[:3]}"
        if self._punteggio < 0:
            raise ValueError("Il punteggio non può essere negativo")

s = Squadra("Roma", ["Totti", "De Rossi"])
print(s)             # Squadra(nome='Roma', giocatori=['Totti', 'De Rossi'])
print(s.id_interno)  # SQ-ROM
```

Non usare mai un valore mutabile (come `[]` o `{}`) come valore predefinito diretto: usare sempre `field(default_factory=list)` o `field(default_factory=dict)`.

#### Opzioni avanzate

```python
@dataclass(frozen=True)
class Coordinata:
    """frozen=True rende l'oggetto immutabile e hashable."""
    latitudine: float
    longitudine: float

c = Coordinata(41.9028, 12.4964)
# c.latitudine = 0  # FrozenInstanceError!
print(hash(c))       # Funziona perché frozen=True genera __hash__

@dataclass(order=True)
class Versione:
    """order=True genera __lt__, __le__, __gt__, __ge__
    basandosi sull'ordine dei campi."""
    major: int
    minor: int
    patch: int = 0

print(Versione(2, 0) > Versione(1, 9, 5))   # True

@dataclass(slots=True)   # Python 3.10+
class PuntoVeloce:
    """slots=True usa __slots__ per risparmiare memoria."""
    x: float
    y: float
```

#### Confronto con namedtuple e classi normali

| Caratteristica | Classe normale | `namedtuple` | `dataclass` |
|---|---|---|---|
| `__init__` automatico | No | Si | Si |
| Mutabile | Si | No | Si (default) |
| Ereditarietà | Completa | Limitata | Completa |
| Type hints | Opzionali | Opzionali | Richiesti |
| Metodi personalizzati | Si | Si (meno naturale) | Si |
| `__eq__` automatico | No | Si | Si |
| `frozen` | Manuale | Per natura | Opzionale |
| `__slots__` | Manuale | Automatico | Opzionale (3.10+) |

### Enum

Le **enumerazioni** (modulo `enum`, presente dalla versione 3.4) rappresentano un insieme fisso di costanti nominate. Sono utili quando una variabile deve assumere solo uno di un insieme predefinito di valori — ad esempio i giorni della settimana, gli stati di un ordine, o i livelli di priorità. Rispetto a semplici costanti intere o stringhe, le Enum forniscono type safety, leggibilità e impediscono l'uso di valori non validi:

```python
from enum import Enum, IntEnum, auto, Flag, IntFlag

class Colore(Enum):
    ROSSO = 1
    VERDE = 2
    BLU = 3

print(Colore.ROSSO)         # Colore.ROSSO
print(Colore.ROSSO.name)    # "ROSSO"
print(Colore.ROSSO.value)   # 1
print(Colore(2))            # Colore.VERDE — accesso per valore
print(Colore["BLU"])        # Colore.BLU — accesso per nome

# Iterazione
for c in Colore:
    print(f"{c.name}: {c.value}")
```

#### IntEnum e StrEnum

```python
class Priorita(IntEnum):
    """IntEnum permette il confronto diretto con interi."""
    BASSA = 1
    MEDIA = 2
    ALTA = 3

print(Priorita.ALTA > 2)    # True — confrontabile con int
print(Priorita.ALTA > Priorita.MEDIA)  # True

# StrEnum disponibile da Python 3.11
from enum import StrEnum

class Stato(StrEnum):
    ATTIVO = "attivo"
    INATTIVO = "inattivo"
    SOSPESO = "sospeso"

print(f"Lo stato è: {Stato.ATTIVO}")  # "Lo stato è: attivo"
```

#### Auto values e Flag

```python
class Direzione(Enum):
    """auto() assegna valori automaticamente (1, 2, 3, ...)."""
    NORD = auto()
    SUD = auto()
    EST = auto()
    OVEST = auto()

class Permesso(Flag):
    """Flag supporta combinazioni con operatori bitwise."""
    LETTURA = auto()
    SCRITTURA = auto()
    ESECUZIONE = auto()

# Combinazione di flag
permessi_admin = Permesso.LETTURA | Permesso.SCRITTURA | Permesso.ESECUZIONE
print(Permesso.LETTURA in permessi_admin)   # True

class PermessoInt(IntFlag):
    """IntFlag è come Flag ma compatibile con int."""
    R = 4
    W = 2
    X = 1

print(PermessoInt.R | PermessoInt.W)         # PermessoInt.R|W
print(int(PermessoInt.R | PermessoInt.W))     # 6
```

### `__slots__` per l'ottimizzazione della memoria

Per impostazione predefinita, Python memorizza gli attributi di istanza in un dizionario (`__dict__`). Questo è estremamente flessibile — si possono aggiungere attributi dinamicamente in qualsiasi momento — ma ha un costo in termini di memoria. L'uso di `__slots__` sostituisce il dizionario con una struttura a dimensione fissa (simile a una struct del C), con un significativo risparmio di memoria quando si creano molte istanze:

```python
class PuntoNormale:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class PuntoSlot:
    __slots__ = ("x", "y")

    def __init__(self, x, y):
        self.x = x
        self.y = y

import sys
p_normale = PuntoNormale(1, 2)
p_slot = PuntoSlot(1, 2)

print(sys.getsizeof(p_normale.__dict__))  # ~104 bytes (dizionario)
# p_slot.__dict__                         # AttributeError! Non ha __dict__

# Con __slots__ NON è possibile aggiungere attributi dinamici:
# p_slot.z = 3   # AttributeError!
```

**Quando usare `__slots__`:**
- Quando si creano migliaia o milioni di istanze della stessa classe.
- Quando la classe ha un insieme fisso di attributi.
- In applicazioni sensibili alle prestazioni (accesso leggermente più rapido).

**Quando NON usare `__slots__`:**
- Quando serve la flessibilità di aggiungere attributi dinamici.
- In gerarchie di ereditarietà complesse (richiede attenzione nella propagazione degli slot).
- Per classi con poche istanze dove il risparmio è trascurabile.

---

## Pattern OOP

I **design pattern** (pattern di progettazione) sono soluzioni collaudate a problemi ricorrenti nella progettazione del software. Non sono codice da copiare e incollare, ma schemi concettuali che guidano la struttura delle classi e le loro interazioni. Di seguito vengono presentati quattro dei pattern più comuni, con implementazioni idiomatiche in Python.

### Singleton

Il pattern **Singleton** garantisce che una classe abbia una sola istanza in tutta l'applicazione e fornisce un punto di accesso globale a essa. È utile per risorse condivise come connessioni al database, file di configurazione o pool di thread:

```python
class Singleton:
    """Implementazione con __new__."""
    _istanza = None

    def __new__(cls, *args, **kwargs):
        if cls._istanza is None:
            cls._istanza = super().__new__(cls)
        return cls._istanza

    def __init__(self, valore=None):
        # __init__ viene chiamato ogni volta — proteggersi
        if not hasattr(self, "_inizializzato"):
            self.valore = valore
            self._inizializzato = True

s1 = Singleton("primo")
s2 = Singleton("secondo")
print(s1 is s2)        # True — stessa istanza
print(s1.valore)       # "primo" — non sovrascritto grazie al guard
```

Variante più elegante con decoratore:

```python
def singleton(cls):
    """Decoratore che rende una classe singleton."""
    istanze = {}

    def get_istanza(*args, **kwargs):
        if cls not in istanze:
            istanze[cls] = cls(*args, **kwargs)
        return istanze[cls]

    return get_istanza

@singleton
class Configurazione:
    def __init__(self):
        self.impostazioni = {}

    def imposta(self, chiave, valore):
        self.impostazioni[chiave] = valore
```

### Factory

Il pattern **Factory** (fabbrica) delega la creazione degli oggetti a un metodo o a una classe dedicata, separando la logica di creazione dal codice che usa gli oggetti. Il vantaggio principale è che il codice client non ha bisogno di conoscere la classe concreta dell'oggetto che riceve — conosce solo l'interfaccia comune:

```python
class Notifica:
    def invia(self, messaggio):
        raise NotImplementedError

class NotificaEmail(Notifica):
    def invia(self, messaggio):
        return f"Email inviata: {messaggio}"

class NotificaSMS(Notifica):
    def invia(self, messaggio):
        return f"SMS inviato: {messaggio}"

class NotificaPush(Notifica):
    def invia(self, messaggio):
        return f"Push notification: {messaggio}"

class NotificaFactory:
    """Factory che crea il tipo corretto di notifica."""

    _tipi = {
        "email": NotificaEmail,
        "sms": NotificaSMS,
        "push": NotificaPush,
    }

    @classmethod
    def crea(cls, tipo: str) -> Notifica:
        classe = cls._tipi.get(tipo.lower())
        if classe is None:
            raise ValueError(f"Tipo di notifica sconosciuto: {tipo}")
        return classe()

    @classmethod
    def registra(cls, tipo: str, classe):
        """Permette di estendere la factory con nuovi tipi."""
        cls._tipi[tipo.lower()] = classe

# Uso
notifica = NotificaFactory.crea("email")
print(notifica.invia("Ciao!"))   # "Email inviata: Ciao!"
```

### Observer

Il pattern **Observer** (osservatore) definisce una dipendenza uno-a-molti tra oggetti: quando un oggetto (il *soggetto*) cambia stato, tutti gli oggetti dipendenti (gli *osservatori*) vengono notificati e aggiornati automaticamente. Questo pattern è alla base di molti sistemi di eventi, callback e architetture reattive:

```python
class Evento:
    """Sistema di eventi basato sul pattern Observer."""

    def __init__(self):
        self._osservatori = {}

    def registra(self, nome_evento, callback):
        """Registra un osservatore per un evento specifico."""
        if nome_evento not in self._osservatori:
            self._osservatori[nome_evento] = []
        self._osservatori[nome_evento].append(callback)

    def rimuovi(self, nome_evento, callback):
        """Rimuove un osservatore."""
        if nome_evento in self._osservatori:
            self._osservatori[nome_evento].remove(callback)

    def notifica(self, nome_evento, *args, **kwargs):
        """Notifica tutti gli osservatori di un evento."""
        for callback in self._osservatori.get(nome_evento, []):
            callback(*args, **kwargs)

class Negozio:
    def __init__(self):
        self.eventi = Evento()
        self._inventario = {}

    def aggiungi_prodotto(self, nome, quantita):
        self._inventario[nome] = quantita
        self.eventi.notifica("prodotto_aggiunto", nome=nome, quantita=quantita)

    def vendi(self, nome):
        if nome in self._inventario and self._inventario[nome] > 0:
            self._inventario[nome] -= 1
            self.eventi.notifica("vendita", nome=nome)
            if self._inventario[nome] == 0:
                self.eventi.notifica("esaurito", nome=nome)

# Uso
negozio = Negozio()

# Registrazione degli osservatori
negozio.eventi.registra("vendita", lambda **kw: print(f"Venduto: {kw['nome']}"))
negozio.eventi.registra("esaurito", lambda **kw: print(f"ATTENZIONE: {kw['nome']} esaurito!"))

negozio.aggiungi_prodotto("Penna", 1)
negozio.vendi("Penna")
# Venduto: Penna
# ATTENZIONE: Penna esaurito!
```

### Strategy

Il pattern **Strategy** (strategia) permette di definire una famiglia di algoritmi, incapsularne ciascuno in una classe separata, e renderli intercambiabili. Il codice client può selezionare e cambiare l'algoritmo a runtime senza modificare il contesto che lo utilizza:

```python
from abc import ABC, abstractmethod

class StrategiaOrdinamento(ABC):
    @abstractmethod
    def ordina(self, dati: list) -> list:
        pass

class OrdinamentoBubble(StrategiaOrdinamento):
    def ordina(self, dati: list) -> list:
        risultato = dati.copy()
        n = len(risultato)
        for i in range(n):
            for j in range(0, n - i - 1):
                if risultato[j] > risultato[j + 1]:
                    risultato[j], risultato[j + 1] = risultato[j + 1], risultato[j]
        return risultato

class OrdinamentoQuick(StrategiaOrdinamento):
    def ordina(self, dati: list) -> list:
        if len(dati) <= 1:
            return dati.copy()
        pivot = dati[len(dati) // 2]
        sinistro = [x for x in dati if x < pivot]
        centro = [x for x in dati if x == pivot]
        destro = [x for x in dati if x > pivot]
        return self.ordina(sinistro) + centro + self.ordina(destro)

class Ordinatore:
    """Contesto che usa una strategia di ordinamento."""

    def __init__(self, strategia: StrategiaOrdinamento = None):
        self._strategia = strategia or OrdinamentoQuick()

    @property
    def strategia(self):
        return self._strategia

    @strategia.setter
    def strategia(self, nuova_strategia: StrategiaOrdinamento):
        self._strategia = nuova_strategia

    def ordina(self, dati: list) -> list:
        return self._strategia.ordina(dati)

# Uso
numeri = [64, 34, 25, 12, 22, 11, 90]

ordinatore = Ordinatore(OrdinamentoBubble())
print(ordinatore.ordina(numeri))   # [11, 12, 22, 25, 34, 64, 90]

# Cambio strategia a runtime
ordinatore.strategia = OrdinamentoQuick()
print(ordinatore.ordina(numeri))   # [11, 12, 22, 25, 34, 64, 90]
```

In Python, grazie alle funzioni di prima classe, il pattern Strategy può essere semplificato passando direttamente delle funzioni (o lambda) anziché creare gerarchie di classi. L'approccio con classi è preferibile quando la strategia ha uno stato interno, comprende più metodi correlati, o necessita di configurazione iniziale.

```python
# Versione semplificata con funzioni — approccio funzionale
def ordina_con_strategia(dati, strategia=sorted):
    """Accetta qualsiasi callable come strategia."""
    return strategia(dati)

# Uso con lambda o funzioni
risultato = ordina_con_strategia([3, 1, 2], strategia=lambda x: sorted(x, reverse=True))
print(risultato)  # [3, 2, 1]
```

---

## Best Practices

1. **Segui il principio di responsabilità singola (SRP).** Ogni classe dovrebbe avere un solo motivo per cambiare. Se una classe gestisce la logica di business, la persistenza dei dati e la formattazione dell'output, è tempo di suddividerla in classi distinte.

2. **Preferisci la composizione all'ereditarietà.** L'ereditarietà crea un accoppiamento forte e gerarchie rigide. La composizione offre maggiore flessibilità e permette di cambiare comportamento a runtime. Usa l'ereditarietà solo quando esiste una vera relazione "è un" e la sottoclasse rispetta il principio di sostituzione di Liskov.

3. **Programma verso le interfacce, non verso le implementazioni.** Usa ABC o Protocol per definire contratti chiari. Il codice che dipende da astrazioni è più flessibile e più facile da testare rispetto al codice che dipende da classi concrete.

4. **Mantieni le classi piccole e focalizzate.** Una classe con troppi metodi e attributi è un segnale di allarme. Se la documentazione di una classe richiede troppo testo, probabilmente sta facendo troppo. Suddividi in classi più piccole e componili.

5. **Usa le property anziché getter e setter espliciti.** Invece di `get_valore()` e `set_valore()`, usa il decoratore `@property`. Questo rende il codice più pythonic e mantiene un'interfaccia pulita, permettendo al contempo validazione e logica personalizzata.

6. **Implementa `__repr__` per ogni classe.** Una rappresentazione testuale chiara e non ambigua è indispensabile per il debugging. Come minimo, definisci `__repr__` in modo che mostri come ricreare l'oggetto. Aggiungi `__str__` quando serve una rappresentazione leggibile diversa da quella tecnica.

7. **Usa le dataclass per le classi incentrate sui dati.** Se una classe esiste principalmente per contenere dati, usa `@dataclass` per eliminare il boilerplate. Aggiungi `frozen=True` per i dati immutabili e `slots=True` (Python 3.10+) per le prestazioni.

8. **Rispetta il principio di sostituzione di Liskov (LSP).** Una sottoclasse deve poter sostituire la superclasse senza rompere il codice esistente. Se una sottoclasse deve lanciare eccezioni per metodi che la superclasse supporta, o richiede precondizioni più restrittive, probabilmente l'ereditarietà non è la relazione corretta.

9. **Restituisci `NotImplemented` (non `NotImplementedError`) dai metodi di confronto e aritmetici.** Quando un metodo speciale non sa gestire il tipo dell'operando, restituisci la costante `NotImplemented` per permettere a Python di provare l'operazione riflessa sull'altro operando. Lanciare `NotImplementedError` impedirebbe questo meccanismo.

10. **Documenta le classi e i metodi con docstring.** Le docstring sono fondamentali per comunicare l'intento, i parametri attesi, i valori di ritorno e le eccezioni possibili. Per le classi pubbliche, segui una convenzione come Google style, NumPy style o reStructuredText e sii coerente in tutto il progetto.

---

## Metaclassi

> Rif.: Python Data Model, sezione 3.3.3 — *Customizing class creation*.
> PEP 487 — *Simpler customisation of class creation* (Python 3.6+).

Le metaclassi sono uno dei concetti più avanzati del modello a oggetti di Python. Se una classe è il "progetto" per creare oggetti, una metaclasse è il "progetto" per creare classi. In Python, **le classi stesse sono oggetti** — istanze della metaclasse `type`.

### `type()` come metaclasse predefinita

Ogni classe Python è un'istanza di `type`. La funzione `type()` ha due modalità:

```python
# Modalità 1: restituisce il tipo di un oggetto
print(type(42))           # <class 'int'>
print(type("ciao"))       # <class 'str'>

# Modalità 2: crea una nuova classe dinamicamente
# type(nome, basi, namespace)
Animale = type("Animale", (), {
    "specie": "sconosciuta",
    "parla": lambda self: f"Sono un {self.specie}",
})

a = Animale()
a.specie = "cane"
print(a.parla())  # "Sono un cane"

# Equivalente a:
# class Animale:
#     specie = "sconosciuta"
#     def parla(self):
#         return f"Sono un {self.specie}"
```

La relazione è circolare: `type` è un'istanza di sé stessa, e `type` è una sottoclasse di `object`, che a sua volta è un'istanza di `type`.

```python
print(type(type))       # <class 'type'>
print(type(object))     # <class 'type'>
print(isinstance(type, object))  # True
print(issubclass(type, object))  # True
```

### Il meccanismo di creazione delle classi: `__new__` e `__init__` della metaclasse

Quando Python incontra un'istruzione `class`, la sequenza è:

1. Il corpo della classe viene eseguito come un blocco di codice, producendo un namespace (dizionario).
2. Python chiama `metaclasse.__new__(mcs, nome, basi, namespace)` per creare l'oggetto classe.
3. Python chiama `metaclasse.__init__(cls, nome, basi, namespace)` per inizializzarlo.

```python
class MetaRegistro(type):
    """Metaclasse che registra automaticamente ogni sottoclasse."""
    _registro = {}

    def __new__(mcs, nome, basi, namespace):
        cls = super().__new__(mcs, nome, basi, namespace)
        if basi:  # non registrare la classe base stessa
            mcs._registro[nome] = cls
        return cls

    def __init__(cls, nome, basi, namespace):
        super().__init__(nome, basi, namespace)

    @classmethod
    def get_registro(mcs):
        return dict(mcs._registro)


class Plugin(metaclass=MetaRegistro):
    """Classe base — le sottoclassi vengono registrate automaticamente."""
    def esegui(self):
        raise NotImplementedError


class PluginCSV(Plugin):
    def esegui(self):
        return "Elaborazione CSV"


class PluginJSON(Plugin):
    def esegui(self):
        return "Elaborazione JSON"


print(MetaRegistro.get_registro())
# {'PluginCSV': <class 'PluginCSV'>, 'PluginJSON': <class 'PluginJSON'>}
```

### `__init_subclass__` — L'alternativa leggera (PEP 487)

A partire da Python 3.6, `__init_subclass__` offre un modo più semplice per personalizzare la creazione di sottoclassi senza bisogno di una metaclasse esplicita. Questo hook viene chiamato sulla classe genitore ogni volta che viene definita una sottoclasse:

```python
class Plugin:
    """Registrazione automatica delle sottoclassi SENZA metaclasse."""
    _registro: dict[str, type] = {}

    def __init_subclass__(cls, *, tipo: str = "", **kwargs):
        super().__init_subclass__(**kwargs)
        if tipo:
            Plugin._registro[tipo] = cls
        else:
            Plugin._registro[cls.__name__] = cls

    def esegui(self):
        raise NotImplementedError

    @classmethod
    def crea(cls, tipo: str) -> "Plugin":
        """Factory method che usa il registro."""
        classe = cls._registro.get(tipo)
        if classe is None:
            raise ValueError(f"Plugin sconosciuto: {tipo}")
        return classe()


class PluginCSV(Plugin, tipo="csv"):
    def esegui(self):
        return "Elaborazione CSV"


class PluginJSON(Plugin, tipo="json"):
    def esegui(self):
        return "Elaborazione JSON"


print(Plugin._registro)
# {'csv': <class 'PluginCSV'>, 'json': <class 'PluginJSON'>}

p = Plugin.crea("csv")
print(p.esegui())  # "Elaborazione CSV"
```

Il vantaggio di `__init_subclass__` è che non richiede una metaclasse separata, funziona con l'ereditarietà normale e non introduce conflitti di metaclasse. È la scelta preferita nella stragrande maggioranza dei casi.

### `__set_name__` — Descriptor con nome automatico (PEP 487)

Il metodo `__set_name__` viene chiamato al momento della creazione della classe, permettendo ai descriptor di conoscere il nome dell'attributo a cui sono associati:

```python
class Validato:
    """Descriptor che conosce il proprio nome grazie a __set_name__."""

    def __init__(self, tipo_atteso, minimo=None, massimo=None):
        self.tipo_atteso = tipo_atteso
        self.minimo = minimo
        self.massimo = massimo

    def __set_name__(self, owner, name):
        """Chiamato automaticamente quando la classe viene creata.
        owner: la classe che contiene il descriptor.
        name: il nome dell'attributo nella classe."""
        self.nome_pubblico = name
        self.nome_privato = f"_{name}"

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return getattr(obj, self.nome_privato, None)

    def __set__(self, obj, valore):
        if not isinstance(valore, self.tipo_atteso):
            raise TypeError(
                f"{self.nome_pubblico} deve essere {self.tipo_atteso.__name__}, "
                f"ricevuto {type(valore).__name__}"
            )
        if self.minimo is not None and valore < self.minimo:
            raise ValueError(f"{self.nome_pubblico} deve essere >= {self.minimo}")
        if self.massimo is not None and valore > self.massimo:
            raise ValueError(f"{self.nome_pubblico} deve essere <= {self.massimo}")
        setattr(obj, self.nome_privato, valore)


class Studente:
    nome = Validato(str)
    eta = Validato(int, minimo=0, massimo=150)
    voto = Validato(float, minimo=0.0, massimo=30.0)

    def __init__(self, nome, eta, voto):
        self.nome = nome   # passa per Validato.__set__
        self.eta = eta
        self.voto = voto


s = Studente("Anna", 22, 28.5)
print(s.nome)   # "Anna"
# s.eta = -1    # ValueError: eta deve essere >= 0
# s.voto = "A"  # TypeError: voto deve essere float, ricevuto str
```

### Metaclasse personalizzata: esempio avanzato

Un caso d'uso classico è forzare una convenzione di codice a livello di classe — ad esempio, garantire che ogni sottoclasse definisca certi attributi:

```python
class ContrattualeMeta(type):
    """Metaclasse che verifica che ogni classe definisca
    gli attributi obbligatori dichiarati in _campi_obbligatori."""

    def __new__(mcs, nome, basi, namespace):
        cls = super().__new__(mcs, nome, basi, namespace)

        # Raccogli i campi obbligatori da tutta la gerarchia
        campi_obbligatori = set()
        for base in cls.__mro__:
            campi_obbligatori.update(
                getattr(base, "_campi_obbligatori", [])
            )

        # Verifica solo le classi concrete (non la base astratta)
        if basi and campi_obbligatori:
            for campo in campi_obbligatori:
                if campo not in namespace:
                    raise TypeError(
                        f"La classe {nome} deve definire l'attributo '{campo}'"
                    )
        return cls


class Serializzatore(metaclass=ContrattualeMeta):
    _campi_obbligatori = ["formato", "versione"]


class SerializzatoreJSON(Serializzatore):
    formato = "json"
    versione = "1.0"

    def serializza(self, dati):
        import json
        return json.dumps(dati)


# Questa classe causerebbe un errore:
# class SerializzatoreRotto(Serializzatore):
#     formato = "xml"
#     # TypeError: La classe SerializzatoreRotto deve definire l'attributo 'versione'
```

### Quando usare le metaclassi (e quando evitarle)

**Usa le metaclassi quando:**
- Devi controllare la creazione stessa della classe (non solo delle istanze).
- Devi applicare invarianti a livello di gerarchia di classi (come ORM che mappano classi a tabelle).
- Stai scrivendo un framework e hai bisogno di hook sulla definizione delle classi.

**Preferisci alternative più semplici:**
- `__init_subclass__` copre il 90% dei casi d'uso delle metaclassi (PEP 487).
- I decoratori di classe sono più leggibili per trasformazioni one-shot.
- I descriptor con `__set_name__` sono sufficienti per la validazione degli attributi.

La regola d'oro è stata formulata da Tim Peters: *"Le metaclassi sono magia più profonda di quanto il 99% degli utenti debba mai preoccuparsi. Se ti chiedi se ne hai bisogno, non ne hai bisogno."*

---

## Protocollo Descriptor

> Rif.: Python Data Model, sezione 3.3.2 — *Implementing Descriptors*.
> Guida ufficiale: *Descriptor HowTo Guide* (docs.python.org).

I descriptor sono il meccanismo fondamentale su cui si reggono `property`, `classmethod`, `staticmethod` e il binding dei metodi di istanza. Comprendere i descriptor significa comprendere come Python risolve l'accesso agli attributi.

### Cos'è un descriptor

Un descriptor è un oggetto che definisce almeno uno dei metodi `__get__`, `__set__` o `__delete__`. Quando viene assegnato come attributo di classe, Python invoca automaticamente questi metodi durante l'accesso, l'assegnamento o la cancellazione dell'attributo sull'istanza.

```python
class MioDescriptor:
    """Descriptor minimale che intercetta l'accesso agli attributi."""

    def __get__(self, obj, objtype=None):
        """Chiamato quando si accede all'attributo.
        obj: l'istanza (None se accesso dalla classe).
        objtype: la classe che possiede il descriptor."""
        print(f"__get__ chiamato: obj={obj}, objtype={objtype}")
        return 42

    def __set__(self, obj, valore):
        """Chiamato quando si assegna un valore all'attributo."""
        print(f"__set__ chiamato: obj={obj}, valore={valore}")

    def __delete__(self, obj):
        """Chiamato quando si usa del sull'attributo."""
        print(f"__delete__ chiamato: obj={obj}")


class MiaClasse:
    attr = MioDescriptor()  # descriptor come attributo di CLASSE

m = MiaClasse()
m.attr          # __get__ chiamato: obj=<...>, objtype=<class 'MiaClasse'>
m.attr = 10     # __set__ chiamato: obj=<...>, valore=10
del m.attr      # __delete__ chiamato: obj=<...>

MiaClasse.attr  # __get__ chiamato: obj=None, objtype=<class 'MiaClasse'>
```

### Data descriptor vs non-data descriptor

La distinzione è cruciale per la risoluzione degli attributi:

- **Data descriptor**: definisce `__get__` e almeno uno tra `__set__` o `__delete__`. Ha **priorità** sul dizionario dell'istanza (`__dict__`).
- **Non-data descriptor**: definisce solo `__get__`. Il dizionario dell'istanza ha **priorità** su di esso.

L'ordine di risoluzione degli attributi è:
1. Data descriptor della classe (e delle sue basi nella MRO).
2. Attributo nel `__dict__` dell'istanza.
3. Non-data descriptor della classe.
4. `__getattr__` (se definito).

```python
class DataDescriptor:
    """Data descriptor — ha sia __get__ che __set__."""
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return obj.__dict__.get("_valore_dd", "default_dd")

    def __set__(self, obj, valore):
        obj.__dict__["_valore_dd"] = valore


class NonDataDescriptor:
    """Non-data descriptor — ha solo __get__."""
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return "valore_dal_descriptor"


class Esempio:
    data = DataDescriptor()
    nondata = NonDataDescriptor()


e = Esempio()

# Data descriptor: __set__ intercetta l'assegnamento
e.data = "test"
print(e.data)  # "test" — letto dal data descriptor (__get__)

# Non-data descriptor: l'istanza __dict__ ha priorità
e.__dict__["nondata"] = "dall'istanza"
print(e.nondata)  # "dall'istanza" — il __dict__ sovrascrive il non-data descriptor
```

### Come `property` usa i descriptor internamente

Il decoratore `@property` è implementato come un data descriptor. Ecco una versione semplificata che mostra il meccanismo:

```python
class MiaProperty:
    """Reimplementazione semplificata di property come descriptor."""

    def __init__(self, fget=None, fset=None, fdel=None, doc=None):
        self.fget = fget
        self.fset = fset
        self.fdel = fdel
        self.__doc__ = doc or (fget.__doc__ if fget else None)

    def __set_name__(self, owner, name):
        self.nome = name

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        if self.fget is None:
            raise AttributeError(f"proprietà '{self.nome}' non leggibile")
        return self.fget(obj)

    def __set__(self, obj, valore):
        if self.fset is None:
            raise AttributeError(f"proprietà '{self.nome}' non scrivibile")
        self.fset(obj, valore)

    def __delete__(self, obj):
        if self.fdel is None:
            raise AttributeError(f"proprietà '{self.nome}' non cancellabile")
        self.fdel(obj)

    def setter(self, fset):
        return type(self)(self.fget, fset, self.fdel, self.__doc__)

    def deleter(self, fdel):
        return type(self)(self.fget, self.fset, fdel, self.__doc__)
```

### Binding dei metodi: come i non-data descriptor rendono i metodi "magici"

Le funzioni Python sono non-data descriptor. Il loro `__get__` produce un *bound method* quando accedute da un'istanza:

```python
class Classe:
    def metodo(self):
        return "ciao"

c = Classe()

# Accesso dalla classe — funzione non vincolata
print(type(Classe.metodo))  # <class 'function'>

# Accesso dall'istanza — metodo vincolato (bound method)
print(type(c.metodo))       # <class 'method'>

# Equivalente: la funzione.__get__() crea il binding
bound = Classe.__dict__["metodo"].__get__(c, Classe)
print(bound())  # "ciao"
```

Questo è il motivo per cui `self` viene passato automaticamente: il descriptor `__get__` della funzione crea un wrapper che "congela" l'istanza come primo argomento.

### Descriptor con storage nell'istanza

Un pattern comune è usare il descriptor per la logica (validazione, trasformazione) ma conservare il dato nell'istanza stessa, usando `__set_name__` per generare il nome di storage:

```python
class Intervallo:
    """Descriptor che limita un valore numerico a un intervallo."""

    def __init__(self, minimo=-float("inf"), massimo=float("inf")):
        self.minimo = minimo
        self.massimo = massimo

    def __set_name__(self, owner, name):
        self.nome_storage = f"_desc_{name}"

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return getattr(obj, self.nome_storage, self.minimo)

    def __set__(self, obj, valore):
        if not isinstance(valore, (int, float)):
            raise TypeError(f"Atteso numerico, ricevuto {type(valore).__name__}")
        valore_clampato = max(self.minimo, min(self.massimo, valore))
        setattr(obj, self.nome_storage, valore_clampato)


class Colore:
    r = Intervallo(0, 255)
    g = Intervallo(0, 255)
    b = Intervallo(0, 255)

    def __init__(self, r, g, b):
        self.r = r
        self.g = g
        self.b = b

    def __repr__(self):
        return f"Colore({self.r}, {self.g}, {self.b})"


c = Colore(100, 300, -10)
print(c)  # Colore(100, 255, 0) — valori clampati automaticamente
```

### Quando usare i descriptor vs `@property`

| Criterio | `@property` | Descriptor |
|---|---|---|
| Singolo attributo in una classe | Preferibile | Eccessivo |
| Stessa logica su N attributi | Codice duplicato | Riutilizzabile |
| Validazione condivisa tra classi | Non riutilizzabile | Componibile |
| Performance critica | Identica | Identica |
| Leggibilità | Molto alta | Media — richiede comprensione del protocollo |

Regola pratica: se la stessa logica di validazione/trasformazione si ripete per più attributi (nella stessa classe o in classi diverse), un descriptor è la scelta giusta. Per un singolo attributo, `@property` è più idiomatico.

---

## MRO Approfondito — Linearizzazione C3

> Rif.: PEP 3135 — *New Super* (Python 3.0+).
> Dylan paper: *A Monotonic Superclass Linearization for Dylan* (K. Barrett et al., 1996).

La sezione [Ereditarietà](#ereditarietà) ha introdotto la MRO e il suo utilizzo base. Qui approfondiamo l'algoritmo C3, il comportamento cooperativo di `super()` e la risoluzione del diamond problem.

### L'algoritmo C3 linearization passo-passo

Per una classe `C(B1, B2, ..., Bn)`, la linearizzazione C3 è definita ricorsivamente:

```
L[C] = C + merge(L[B1], L[B2], ..., L[Bn], [B1, B2, ..., Bn])
```

L'operazione `merge` seleziona il primo elemento della prima lista che non appare nella coda (posizione > 0) di nessuna altra lista. Questo garantisce:
- **Monotonicità**: se C1 precede C2 nella linearizzazione di una classe, lo stesso vale per tutte le sottoclassi.
- **Ordine locale**: l'ordine di elencazione dei genitori è preservato.

```python
class A: pass
class B(A): pass
class C(A): pass
class D(B, C): pass

# Calcolo manuale:
# L[A] = [A, object]
# L[B] = [B] + merge([A, object], [A]) = [B, A, object]
# L[C] = [C] + merge([A, object], [A]) = [C, A, object]
# L[D] = [D] + merge([B, A, object], [C, A, object], [B, C])
#       = [D, B] + merge([A, object], [C, A, object], [C])
#         A è nella coda di [C, A, object], quindi prendiamo C
#       = [D, B, C] + merge([A, object], [A, object])
#       = [D, B, C, A, object]

print(D.__mro__)
# (<class 'D'>, <class 'B'>, <class 'C'>, <class 'A'>, <class 'object'>)
```

### MRO non risolvibile

Non tutte le gerarchie sono linearizzabili. Se le condizioni di monotonicità non possono essere soddisfatte, Python lancia `TypeError` alla definizione della classe:

```python
class X: pass
class Y: pass
class A(X, Y): pass
class B(Y, X): pass

# Tentativo di creare C(A, B):
# A dice: X prima di Y
# B dice: Y prima di X
# Contraddizione!

# class C(A, B): pass
# TypeError: Cannot create a consistent method resolution order (MRO)
# for bases X, Y
```

### `super()` cooperativo

`super()` non chiama semplicemente "il genitore" — chiama la classe successiva nella MRO. Questo è il meccanismo cooperativo: ogni classe nella catena deve propagare la chiamata con `super()` per garantire che tutti i livelli vengano invocati.

```python
class Base:
    def __init__(self):
        print("Base.__init__")
        super().__init__()  # propaga a object

class Mixin1(Base):
    def __init__(self):
        print("Mixin1.__init__")
        super().__init__()  # propaga a Base (o al prossimo nella MRO)

class Mixin2(Base):
    def __init__(self):
        print("Mixin2.__init__")
        super().__init__()  # propaga a Mixin1 (nella MRO di Finale)

class Finale(Mixin2, Mixin1):
    def __init__(self):
        print("Finale.__init__")
        super().__init__()  # propaga a Mixin2

# MRO: Finale → Mixin2 → Mixin1 → Base → object
f = Finale()
# Output:
# Finale.__init__
# Mixin2.__init__
# Mixin1.__init__
# Base.__init__
```

Se una classe nella catena non chiama `super().__init__()`, la catena si interrompe e le classi successive nella MRO non vengono inizializzate — un bug insidioso.

### Diamond problem — Risoluzione in Python

Il "diamond problem" si verifica quando una classe eredita da due classi che condividono un antenato comune. Senza C3, il costruttore dell'antenato verrebbe chiamato due volte:

```python
class Risorsa:
    def __init__(self):
        print("Risorsa.__init__ (chiamata una sola volta)")
        super().__init__()
        self.inizializzata = True

class ConnessioneDB(Risorsa):
    def __init__(self):
        print("ConnessioneDB.__init__")
        super().__init__()

class ConnessioneCache(Risorsa):
    def __init__(self):
        print("ConnessioneCache.__init__")
        super().__init__()

class Servizio(ConnessioneDB, ConnessioneCache):
    def __init__(self):
        print("Servizio.__init__")
        super().__init__()

# MRO: Servizio → ConnessioneDB → ConnessioneCache → Risorsa → object
s = Servizio()
# Output:
# Servizio.__init__
# ConnessioneDB.__init__
# ConnessioneCache.__init__
# Risorsa.__init__ (chiamata una sola volta)  ← grazie alla MRO C3
```

### Pattern per `__init__` cooperativo con argomenti

Quando le classi nella catena hanno parametri diversi, il pattern standard usa `**kwargs` per propagare gli argomenti sconosciuti:

```python
class Base:
    def __init__(self, **kwargs):
        # Consuma i kwargs residui — deve essere l'ultimo nella MRO
        super().__init__()

class ConNome(Base):
    def __init__(self, nome: str, **kwargs):
        super().__init__(**kwargs)
        self.nome = nome

class ConEta(Base):
    def __init__(self, eta: int, **kwargs):
        super().__init__(**kwargs)
        self.eta = eta

class Persona(ConNome, ConEta):
    def __init__(self, nome: str, eta: int, **kwargs):
        super().__init__(nome=nome, eta=eta, **kwargs)

p = Persona(nome="Anna", eta=30)
print(p.nome, p.eta)  # Anna 30
```

---

## Dataclass Approfondito

> Rif.: PEP 557 — *Data Classes* (Python 3.7+).

La sezione [Classi Speciali](#classi-speciali) ha introdotto le dataclass con le opzioni base. Qui approfondiamo le funzionalità avanzate aggiunte nelle versioni 3.10-3.12.

### `kw_only` — Solo keyword arguments (Python 3.10+)

L'opzione `kw_only=True` forza tutti i campi (o un sottoinsieme) ad essere keyword-only, eliminando ambiguità nell'ordine dei parametri:

```python
from dataclasses import dataclass, field

@dataclass(kw_only=True)
class Configurazione:
    """Tutti i campi devono essere passati come keyword arguments."""
    host: str
    porta: int = 8080
    debug: bool = False
    workers: int = 4

# c = Configurazione("localhost")  # TypeError!
c = Configurazione(host="localhost", workers=8)
print(c)  # Configurazione(host='localhost', porta=8080, debug=False, workers=8)
```

Si può anche applicare `kw_only` solo ad alcuni campi, usando il sentinel `KW_ONLY`:

```python
from dataclasses import dataclass, field, KW_ONLY

@dataclass
class Richiesta:
    url: str           # posizionale
    metodo: str = "GET"  # posizionale con default
    _: KW_ONLY         # sentinella — tutto dopo è kw_only
    timeout: float = 30.0
    headers: dict = field(default_factory=dict)
    retry: int = 3

r = Richiesta("https://api.example.com", "POST", timeout=60.0)
print(r)
```

### `match_args` — Pattern matching strutturale (Python 3.10+)

L'opzione `match_args=True` (attiva per default) genera l'attributo `__match_args__`, necessario per il pattern matching introdotto con `match`/`case` (PEP 634):

```python
from dataclasses import dataclass

@dataclass
class Punto:
    x: float
    y: float

@dataclass
class Cerchio:
    centro: Punto
    raggio: float

@dataclass
class Rettangolo:
    origine: Punto
    larghezza: float
    altezza: float


def descrivi_forma(forma):
    match forma:
        case Cerchio(centro=Punto(0, 0), raggio=r):
            return f"Cerchio all'origine con raggio {r}"
        case Cerchio(raggio=r) if r > 100:
            return f"Cerchio grande (raggio={r})"
        case Cerchio(centro=c, raggio=r):
            return f"Cerchio in ({c.x}, {c.y}) con raggio {r}"
        case Rettangolo(larghezza=l, altezza=a) if l == a:
            return f"Quadrato con lato {l}"
        case Rettangolo(larghezza=l, altezza=a):
            return f"Rettangolo {l}x{a}"
        case _:
            return "Forma sconosciuta"


print(descrivi_forma(Cerchio(Punto(0, 0), 5)))   # Cerchio all'origine con raggio 5
print(descrivi_forma(Rettangolo(Punto(1, 1), 4, 4)))  # Quadrato con lato 4
```

### `__post_init__` — Validazione e campi derivati

`__post_init__` è il hook per la logica post-costruzione. Viene chiamato dopo il `__init__` generato:

```python
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Transazione:
    importo: float
    valuta: str = "EUR"
    timestamp: datetime = field(default_factory=datetime.now)
    id_transazione: str = field(init=False)
    _validata: bool = field(init=False, repr=False, default=False)

    def __post_init__(self):
        # Validazione
        if self.importo == 0:
            raise ValueError("L'importo non può essere zero")
        if self.valuta not in ("EUR", "USD", "GBP", "CHF"):
            raise ValueError(f"Valuta non supportata: {self.valuta}")

        # Campo derivato
        self.id_transazione = (
            f"TX-{self.timestamp:%Y%m%d%H%M%S}-"
            f"{abs(hash(self.importo)) % 10000:04d}"
        )
        self._validata = True

t = Transazione(150.0, "EUR")
print(t.id_transazione)  # TX-20260523...-XXXX
```

### `InitVar` — Parametri solo per l'inizializzazione

`InitVar` dichiara parametri che vengono passati a `__init__` e a `__post_init__` ma non diventano attributi della dataclass:

```python
from dataclasses import dataclass, field, InitVar

@dataclass
class PasswordHash:
    username: str
    password_hash: str = field(init=False, repr=False)
    password: InitVar[str] = None  # non diventa un attributo

    def __post_init__(self, password):
        if password is None:
            raise ValueError("La password è obbligatoria")
        import hashlib
        self.password_hash = hashlib.sha256(password.encode()).hexdigest()

u = PasswordHash("admin", password="segreta123")
print(u)            # PasswordHash(username='admin')
print(u.password_hash)  # hash SHA-256
# u.password        # AttributeError — non esiste come attributo
```

### Ereditarietà tra dataclass

Le dataclass supportano l'ereditarietà, ma con una regola importante: i campi con valore predefinito nella classe genitore forzano tutti i campi nella sottoclasse ad avere un valore predefinito (altrimenti si otterrebbe un `TypeError` perché i parametri posizionali seguirebbero quelli con default):

```python
from dataclasses import dataclass

@dataclass
class Entita:
    id: int
    nome: str

@dataclass
class Utente(Entita):
    email: str
    ruolo: str = "utente"

u = Utente(1, "Anna", "anna@example.com")
print(u)  # Utente(id=1, nome='Anna', email='anna@example.com', ruolo='utente')

# Problema con default nella classe base:
@dataclass
class Base:
    x: int = 0

# @dataclass
# class Derivata(Base):
#     y: int  # TypeError! campo senza default dopo campo con default
```

La soluzione per Python 3.10+ è usare `kw_only=True` nella sottoclasse:

```python
@dataclass
class BaseConDefault:
    x: int = 0

@dataclass(kw_only=True)
class DerivataSafe(BaseConDefault):
    y: int  # OK — è keyword-only, non posizionale
```

---

## `__slots__` Approfondito

La sezione [Classi Speciali](#classi-speciali) ha introdotto `__slots__` e i suoi vantaggi in termini di memoria. Qui approfondiamo i dettagli pratici.

### Misurazione del risparmio di memoria

```python
import sys

class SenzaSlot:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

class ConSlot:
    __slots__ = ("x", "y", "z")
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z


# Dimensione di una singola istanza
s1 = SenzaSlot(1, 2, 3)
s2 = ConSlot(1, 2, 3)

# L'istanza senza slot ha __dict__ + overhead
dim_senza = sys.getsizeof(s1) + sys.getsizeof(s1.__dict__)
dim_con = sys.getsizeof(s2)

print(f"Senza __slots__: {dim_senza} bytes")   # ~200+ bytes (CPython 3.12)
print(f"Con __slots__:   {dim_con} bytes")      # ~64 bytes (CPython 3.12)

# Con 1 milione di istanze, il risparmio è dell'ordine di 100+ MB.
```

Il risparmio varia in base alla versione di CPython. Da Python 3.12, i dizionari delle istanze condividono le chiavi (PEP 412), riducendo il divario per classi con pochi attributi. Ma `__slots__` resta vincente per grandi volumi.

### `__slots__` e ereditarietà

L'interazione tra `__slots__` ed ereditarietà ha regole precise:

```python
class Base:
    __slots__ = ("x", "y")

class Derivata(Base):
    __slots__ = ("z",)  # solo i NUOVI attributi

    def __init__(self, x, y, z):
        self.x = x  # slot ereditato da Base
        self.y = y  # slot ereditato da Base
        self.z = z  # slot di Derivata

d = Derivata(1, 2, 3)
# d.w = 4  # AttributeError — niente __dict__
```

Se la sottoclasse non definisce `__slots__`, avrà un `__dict__` e annullerà i benefici:

```python
class DerivataConDict(Base):
    # Nessun __slots__ → Python aggiunge __dict__
    pass

d2 = DerivataConDict()
d2.x = 1       # usa lo slot ereditato
d2.extra = 2   # funziona! usa __dict__
```

Per preservare i benefici lungo tutta la gerarchia, **ogni classe** nella catena deve definire `__slots__`.

Non ripetere gli slot del genitore nella sottoclasse — altrimenti si spreca memoria:

```python
# SBAGLIATO — duplicazione degli slot
class Errore(Base):
    __slots__ = ("x", "y", "z")  # x e y sono già in Base

# CORRETTO — solo gli slot nuovi
class Corretto(Base):
    __slots__ = ("z",)
```

### `__weakref__` e `__slots__`

Per default, le classi con `__slots__` non supportano i weak reference. Per abilitarli, aggiungere `"__weakref__"` agli slot:

```python
import weakref

class ConWeakRef:
    __slots__ = ("valore", "__weakref__")

    def __init__(self, valore):
        self.valore = valore

obj = ConWeakRef(42)
ref = weakref.ref(obj)
print(ref().valore)  # 42

class SenzaWeakRef:
    __slots__ = ("valore",)

# obj2 = SenzaWeakRef(42)
# weakref.ref(obj2)  # TypeError: cannot create weak reference
```

### `__slots__` e `__dict__` coesistenti

Se serve la flessibilità di attributi dinamici mantenendo alcuni attributi come slot:

```python
class Ibrido:
    __slots__ = ("x", "y", "__dict__")

    def __init__(self, x, y):
        self.x = x       # slot — veloce, memoria fissa
        self.y = y       # slot
        self.extra = {}  # __dict__ — flessibile

h = Ibrido(1, 2)
h.z = 3  # OK — va nel __dict__
print(h.x, h.z)  # 1 3
```

---

## ABC Approfondito

> Rif.: PEP 3119 — *Introducing Abstract Base Classes*.
> Modulo: `abc` e `collections.abc`.

La sezione [Polimorfismo](#polimorfismo) ha introdotto ABC con `@abstractmethod`. Qui approfondiamo il meccanismo del virtual subclass e le ABC della libreria standard.

### `register()` — Virtual subclass

Il metodo `register()` permette di dichiarare una classe come "sottoclasse virtuale" di una ABC senza ereditarietà effettiva. La classe registrata supera il controllo `isinstance()` e `issubclass()`, ma non è tenuta a implementare i metodi astratti (questo non viene verificato):

```python
from abc import ABC, abstractmethod

class Serializzabile(ABC):
    @abstractmethod
    def serializza(self) -> bytes:
        ...

    @abstractmethod
    def deserializza(cls, dati: bytes):
        ...


# Classe esterna che non eredita da Serializzabile
class DatoEsterno:
    def serializza(self) -> bytes:
        return b"dato_esterno"

    @classmethod
    def deserializza(cls, dati: bytes):
        return cls()


# Registrazione come virtual subclass
Serializzabile.register(DatoEsterno)

d = DatoEsterno()
print(isinstance(d, Serializzabile))    # True
print(issubclass(DatoEsterno, Serializzabile))  # True

# ATTENZIONE: register() non verifica i metodi astratti!
class ClasseVuota:
    pass

Serializzabile.register(ClasseVuota)
print(isinstance(ClasseVuota(), Serializzabile))  # True — ma non ha serializza()!
```

Il virtual subclass è utile quando si ha a che fare con classi di terze parti che non si possono modificare, ma che rispettano il contratto dell'ABC.

### `__subclasshook__` — Controllo personalizzato di `isinstance`

Per un controllo più sofisticato, è possibile definire `__subclasshook__`, che viene chiamato da `isinstance()` e `issubclass()`:

```python
from abc import ABC

class Iterabile(ABC):
    @classmethod
    def __subclasshook__(cls, C):
        if cls is Iterabile:
            # Verifica strutturale: ha un metodo __iter__?
            if any("__iter__" in B.__dict__ for B in C.__mro__):
                return True
        return NotImplemented

class MioContenitore:
    def __iter__(self):
        return iter([1, 2, 3])

print(isinstance(MioContenitore(), Iterabile))  # True — senza ereditarietà né register()
```

### `collections.abc` — Le ABC della libreria standard

Il modulo `collections.abc` fornisce ABC per i tipi container più comuni. Estendere queste ABC garantisce che la propria classe implementi tutti i metodi richiesti dal protocollo:

```python
from collections.abc import (
    Iterable,      # __iter__
    Iterator,      # __iter__, __next__
    Sequence,      # __getitem__, __len__ (+ indici, count, __contains__, __iter__, __reversed__)
    MutableSequence,  # + __setitem__, __delitem__, insert
    Mapping,       # __getitem__, __len__, __iter__ (+ keys, values, items, get, __contains__, __eq__)
    MutableMapping,   # + __setitem__, __delitem__
    Set,           # __contains__, __iter__, __len__
    Callable,      # __call__
    Hashable,      # __hash__
    Sized,         # __len__
)

# Esempio: sequenza personalizzata che implementa il protocollo completo
from collections.abc import Sequence

class SerieStorica(Sequence):
    """Sequenza immutabile di valori numerici con timestamp."""

    def __init__(self, valori: list[float]):
        self._valori = tuple(valori)  # immutabile

    def __getitem__(self, indice):
        if isinstance(indice, slice):
            return SerieStorica(self._valori[indice])
        return self._valori[indice]

    def __len__(self):
        return len(self._valori)

    # Sequence fornisce GRATUITAMENTE:
    # __contains__, __iter__, __reversed__, index, count

    def __repr__(self):
        return f"SerieStorica({list(self._valori)})"

s = SerieStorica([10.5, 11.2, 9.8, 12.1])
print(len(s))        # 4
print(s[1])          # 11.2
print(9.8 in s)      # True — __contains__ ereditato
print(s.index(12.1)) # 3 — index() ereditato
print(list(reversed(s)))  # [12.1, 9.8, 11.2, 10.5] — __reversed__ ereditato
```

### ABC vs Protocol: quando usare quale

| Criterio | ABC | Protocol |
|---|---|---|
| Tipo di subtyping | Nominale (esplicito) | Strutturale (implicito) |
| Ereditarietà richiesta | Si | No |
| Verifica a runtime | Si (`isinstance`) | Si (con `@runtime_checkable`, ma limitato) |
| Verifica statica (mypy) | Si | Si |
| Metodi concreti ereditabili | Si | No |
| Uso con classi di terze parti | Tramite `register()` | Automatico |
| Caso d'uso tipico | Framework, API con contratto forte | Librerie, type hints, duck typing statico |

Regola pratica: se la classe deve fornire implementazioni concrete parziali (come il metodo `descrizione()` in `Forma`), usare ABC. Se serve solo verificare la compatibilità strutturale, usare Protocol.

---

## Protocol Approfondito — PEP 544

> Rif.: PEP 544 — *Protocols: Structural subtyping (static duck typing)* (Python 3.8+).

La sezione [Polimorfismo](#polimorfismo) ha introdotto Protocol con un esempio base. Qui approfondiamo le funzionalità avanzate e i pattern pratici.

### Protocol con attributi

I Protocol possono dichiarare sia metodi sia attributi:

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class HasNome(Protocol):
    nome: str  # attributo obbligatorio

@runtime_checkable
class Loggabile(Protocol):
    def log(self, livello: str, messaggio: str) -> None: ...
    nome: str
    versione: str


class Servizio:
    def __init__(self, nome: str, versione: str):
        self.nome = nome
        self.versione = versione

    def log(self, livello: str, messaggio: str) -> None:
        print(f"[{livello}] {self.nome} v{self.versione}: {messaggio}")


def configura_logging(componente: Loggabile) -> None:
    componente.log("INFO", "Logging configurato")

s = Servizio("api-gateway", "2.1.0")
configura_logging(s)  # OK — Servizio soddisfa il protocollo Loggabile

print(isinstance(s, Loggabile))  # True
```

### Composizione di Protocol

I Protocol supportano l'ereditarietà per costruire protocolli più complessi:

```python
from typing import Protocol

class Leggibile(Protocol):
    def leggi(self) -> str: ...

class Scrivibile(Protocol):
    def scrivi(self, dati: str) -> None: ...

class LeggibileScrivibile(Leggibile, Scrivibile, Protocol):
    """Composto: deve avere sia leggi() che scrivi()."""
    ...

class FileDiTesto:
    def __init__(self, contenuto: str = ""):
        self._contenuto = contenuto

    def leggi(self) -> str:
        return self._contenuto

    def scrivi(self, dati: str) -> None:
        self._contenuto += dati

def copia(sorgente: Leggibile, destinazione: Scrivibile) -> None:
    dati = sorgente.leggi()
    destinazione.scrivi(dati)
```

### `runtime_checkable` — Limitazioni

Il decoratore `@runtime_checkable` abilita `isinstance()` per i Protocol, ma con limitazioni importanti:

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class ConChiudi(Protocol):
    def chiudi(self) -> None: ...

# isinstance() verifica solo che il metodo ESISTA, non la firma
class FalsoChiudi:
    def chiudi(self, forza: bool = False) -> int:  # firma diversa!
        return 0

print(isinstance(FalsoChiudi(), ConChiudi))  # True — firma non verificata!
```

Per una verifica completa delle firme, affidarsi a mypy o pyright (type checking statico).

### Protocol con metodi generici

```python
from typing import Protocol, TypeVar, Generic

T = TypeVar("T")

class Repository(Protocol[T]):
    """Protocol generico per un repository CRUD."""
    def trova(self, id: int) -> T | None: ...
    def salva(self, entita: T) -> None: ...
    def elimina(self, id: int) -> bool: ...
    def lista(self) -> list[T]: ...


class Utente:
    def __init__(self, id: int, nome: str):
        self.id = id
        self.nome = nome

class UtenteRepository:
    """Implementa Repository[Utente] senza ereditarietà esplicita."""

    def __init__(self):
        self._storage: dict[int, Utente] = {}

    def trova(self, id: int) -> Utente | None:
        return self._storage.get(id)

    def salva(self, entita: Utente) -> None:
        self._storage[entita.id] = entita

    def elimina(self, id: int) -> bool:
        return self._storage.pop(id, None) is not None

    def lista(self) -> list[Utente]:
        return list(self._storage.values())


def conta_entita(repo: Repository) -> int:
    return len(repo.lista())

repo = UtenteRepository()
repo.salva(Utente(1, "Anna"))
repo.salva(Utente(2, "Marco"))
print(conta_entita(repo))  # 2
```

---

## Enum Approfondito

La sezione [Classi Speciali](#classi-speciali) ha introdotto Enum, IntEnum, StrEnum e Flag. Qui approfondiamo i metodi personalizzati e i pattern avanzati.

### Enum con metodi e proprietà personalizzate

```python
from enum import Enum

class Pianeta(Enum):
    MERCURIO = (3.303e+23, 2.4397e6)
    VENERE   = (4.869e+24, 6.0518e6)
    TERRA    = (5.976e+24, 6.37814e6)
    MARTE    = (6.421e+23, 3.3972e6)

    def __init__(self, massa, raggio):
        self.massa = massa      # kg
        self.raggio = raggio    # m

    @property
    def gravita_superficiale(self):
        G = 6.67430e-11  # m^3 kg^-1 s^-2
        return G * self.massa / (self.raggio ** 2)

    @property
    def peso_su(self):
        """Restituisce una funzione che calcola il peso su questo pianeta."""
        def calcola(massa_kg):
            return massa_kg * self.gravita_superficiale
        return calcola

    def __str__(self):
        return f"{self.name.capitalize()} (g={self.gravita_superficiale:.2f} m/s²)"


for pianeta in Pianeta:
    print(f"{pianeta}: peso 70kg = {pianeta.peso_su(70):.1f} N")
# Mercurio (g=3.70 m/s²): peso 70kg = 259.2 N
# Terra (g=9.80 m/s²): peso 70kg = 686.3 N
```

### Enum con validazione e lookup

```python
from enum import Enum, auto

class StatoOrdine(Enum):
    CREATO = auto()
    PAGATO = auto()
    SPEDITO = auto()
    CONSEGNATO = auto()
    ANNULLATO = auto()

    @classmethod
    def da_stringa(cls, valore: str) -> "StatoOrdine":
        """Lookup case-insensitive con messaggio chiaro."""
        try:
            return cls[valore.upper()]
        except KeyError:
            validi = ", ".join(s.name for s in cls)
            raise ValueError(
                f"Stato '{valore}' non valido. Valori ammessi: {validi}"
            )

    def puo_transitare_a(self, nuovo_stato: "StatoOrdine") -> bool:
        """Matrice di transizioni valide."""
        transizioni = {
            StatoOrdine.CREATO: {StatoOrdine.PAGATO, StatoOrdine.ANNULLATO},
            StatoOrdine.PAGATO: {StatoOrdine.SPEDITO, StatoOrdine.ANNULLATO},
            StatoOrdine.SPEDITO: {StatoOrdine.CONSEGNATO},
            StatoOrdine.CONSEGNATO: set(),
            StatoOrdine.ANNULLATO: set(),
        }
        return nuovo_stato in transizioni[self]


stato = StatoOrdine.da_stringa("creato")
print(stato.puo_transitare_a(StatoOrdine.PAGATO))     # True
print(stato.puo_transitare_a(StatoOrdine.CONSEGNATO))  # False
```

### Garantire unicità dei valori

```python
from enum import Enum, unique

@unique
class CodiceErrore(Enum):
    """@unique impedisce valori duplicati."""
    NOT_FOUND = 404
    FORBIDDEN = 403
    INTERNAL_ERROR = 500
    # ERRORE = 404  # ValueError: duplicate values found in CodiceErrore: ERRORE -> NOT_FOUND
```

### Flag avanzato — Permessi combinabili

```python
from enum import Flag, auto

class Permesso(Flag):
    NESSUNO = 0
    LETTURA = auto()
    SCRITTURA = auto()
    ESECUZIONE = auto()
    ADMIN = LETTURA | SCRITTURA | ESECUZIONE

def verifica_accesso(permessi_utente: Permesso, richiesto: Permesso) -> bool:
    return richiesto in permessi_utente

utente = Permesso.LETTURA | Permesso.SCRITTURA
print(verifica_accesso(utente, Permesso.LETTURA))    # True
print(verifica_accesso(utente, Permesso.ESECUZIONE)) # False
print(verifica_accesso(utente, Permesso.ADMIN))      # False
print(verifica_accesso(Permesso.ADMIN, Permesso.LETTURA))  # True
```

---

## Dunder Methods Approfondito

La sezione [Metodi Speciali](#metodi-speciali-dunder-methods) ha coperto i dunder più comuni. Qui approfondiamo il contratto `__hash__`/`__eq__`, il protocollo context manager e le regole dei metodi di confronto.

### Il contratto `__hash__` / `__eq__`

Le regole del contratto sono dettate dalla documentazione ufficiale (Data Model, sezione 3.3.1):

1. Se `a == b`, allora `hash(a) == hash(b)` (**obbligatorio**).
2. Se `hash(a) == hash(b)`, `a == b` potrebbe essere falso (le collisioni sono ammesse).
3. Se si definisce `__eq__` senza `__hash__`, Python imposta `__hash__ = None` (non hashable).
4. Oggetti mutabili non dovrebbero definire `__hash__` perché il loro hash cambierebbe nel tempo.

```python
class Persona:
    def __init__(self, nome: str, cf: str):
        self.nome = nome
        self.cf = cf  # codice fiscale — immutabile e univoco

    def __eq__(self, altro):
        if not isinstance(altro, Persona):
            return NotImplemented
        return self.cf == altro.cf

    def __hash__(self):
        # Basato SOLO sui campi usati in __eq__
        return hash(self.cf)

    def __repr__(self):
        return f"Persona({self.nome!r}, {self.cf!r})"


p1 = Persona("Mario Rossi", "RSSMRA80A01H501Z")
p2 = Persona("Mario Rossi", "RSSMRA80A01H501Z")  # stesso CF
p3 = Persona("Mario Bianchi", "BNCMRA80A01H501Z")

print(p1 == p2)  # True — stesso CF
print(hash(p1) == hash(p2))  # True — coerente con __eq__

# Funzionano come chiavi di dizionario e in set
persone = {p1, p2, p3}
print(len(persone))  # 2 — p1 e p2 sono "la stessa persona"
```

### `__repr__` vs `__str__` — Regole operative

```python
class Connessione:
    def __init__(self, host, porta, sicura=False):
        self.host = host
        self.porta = porta
        self.sicura = sicura

    def __repr__(self):
        """Regola: deve essere non ambiguo. Idealmente eval(repr(x)) == x."""
        return (
            f"Connessione(host={self.host!r}, porta={self.porta!r}, "
            f"sicura={self.sicura!r})"
        )

    def __str__(self):
        """Regola: leggibile, orientato all'utente finale."""
        protocollo = "https" if self.sicura else "http"
        return f"{protocollo}://{self.host}:{self.porta}"

c = Connessione("api.example.com", 443, sicura=True)
print(str(c))    # https://api.example.com:443
print(repr(c))   # Connessione(host='api.example.com', porta=443, sicura=True)

# In una lista, Python usa __repr__ per gli elementi:
print([c])
# [Connessione(host='api.example.com', porta=443, sicura=True)]
```

### Context manager protocol — `__enter__` / `__exit__` avanzato

```python
class TransazioneDB:
    """Context manager con gestione esplicita di commit/rollback."""

    def __init__(self, connessione):
        self.connessione = connessione
        self.cursore = None

    def __enter__(self):
        self.cursore = self.connessione.cursor()
        return self.cursore

    def __exit__(self, tipo_eccezione, valore, traceback):
        if tipo_eccezione is not None:
            # Eccezione durante il blocco with → rollback
            self.connessione.rollback()
            print(f"Rollback a causa di: {tipo_eccezione.__name__}: {valore}")
            # return False → l'eccezione viene rilanciata
            return False
        else:
            # Nessuna eccezione → commit
            self.connessione.commit()
            return True
        # Il cursore viene chiuso in entrambi i casi
```

### Metodi di confronto — La catena completa

```python
from functools import total_ordering

# SENZA @total_ordering — implementazione manuale completa
class Versione:
    def __init__(self, major, minor, patch=0):
        self.major = major
        self.minor = minor
        self.patch = patch

    def _come_tupla(self):
        return (self.major, self.minor, self.patch)

    def __eq__(self, altro):
        if not isinstance(altro, Versione):
            return NotImplemented
        return self._come_tupla() == altro._come_tupla()

    def __lt__(self, altro):
        if not isinstance(altro, Versione):
            return NotImplemented
        return self._come_tupla() < altro._come_tupla()

    def __le__(self, altro):
        if not isinstance(altro, Versione):
            return NotImplemented
        return self._come_tupla() <= altro._come_tupla()

    def __gt__(self, altro):
        if not isinstance(altro, Versione):
            return NotImplemented
        return self._come_tupla() > altro._come_tupla()

    def __ge__(self, altro):
        if not isinstance(altro, Versione):
            return NotImplemented
        return self._come_tupla() >= altro._come_tupla()

    def __hash__(self):
        return hash(self._come_tupla())

    def __repr__(self):
        return f"Versione({self.major}, {self.minor}, {self.patch})"
```

Il pattern `_come_tupla()` è un idioma comune: si delegano tutti i confronti a una tupla, che li implementa naturalmente in ordine lessicografico.

---

## Variabili di Classe vs Istanza — La Trappola Mutabile

Questa è una delle trappole più frequenti per chi inizia con l'OOP in Python. Riguarda le variabili di classe con valori mutabili (liste, dizionari, set).

### Il problema

```python
class Squadra:
    giocatori = []  # PERICOLO: lista mutabile come attributo di classe

    def __init__(self, nome):
        self.nome = nome

    def aggiungi(self, giocatore):
        self.giocatori.append(giocatore)  # modifica la lista CONDIVISA!

roma = Squadra("Roma")
roma.aggiungi("Totti")

napoli = Squadra("Napoli")
napoli.aggiungi("Maradona")

print(roma.giocatori)    # ['Totti', 'Maradona']  — SORPRESA!
print(napoli.giocatori)  # ['Totti', 'Maradona']
print(roma.giocatori is napoli.giocatori)  # True — stessa lista!
```

### Perché succede

Gli attributi di classe sono condivisi tra tutte le istanze. Con un tipo immutabile (come `int`, `str`, `tuple`), l'assegnamento `self.x = valore` crea un attributo di istanza che oscura quello di classe — nessun problema. Ma con un tipo mutabile, `self.lista.append(...)` non crea un nuovo attributo di istanza: modifica la lista di classe in-place.

### La soluzione

Inizializzare i valori mutabili in `__init__`:

```python
class Squadra:
    sport = "calcio"  # OK — immutabile, condivisione intenzionale

    def __init__(self, nome):
        self.nome = nome
        self.giocatori = []  # ogni istanza ha la propria lista

    def aggiungi(self, giocatore):
        self.giocatori.append(giocatore)

roma = Squadra("Roma")
roma.aggiungi("Totti")

napoli = Squadra("Napoli")
napoli.aggiungi("Maradona")

print(roma.giocatori)    # ['Totti']
print(napoli.giocatori)  # ['Maradona']
```

### Regola

- **Attributi di classe immutabili** (`int`, `str`, `tuple`, `frozenset`): sicuri da condividere.
- **Attributi di classe mutabili** (`list`, `dict`, `set`): quasi sempre un bug. Inizializzare in `__init__`.
- Eccezione: quando la condivisione è *intenzionale* (es. un contatore di istanze o un registro).

---

## Composizione vs Ereditarietà — Linee Guida Pratiche

La sezione [Composizione vs Ereditarietà](#composizione-vs-ereditarietà) ha introdotto i principi. Qui forniamo un framework decisionale.

### Checklist decisionale

Domande da porsi prima di scegliere:

1. La relazione è veramente "è un" o è "ha un" / "usa un"?
2. La sottoclasse rispetta il principio di sostituzione di Liskov (LSP)?
3. Si sovrascrivono molti metodi del genitore per "disabilitarli"?
4. La gerarchia è già profonda (> 3 livelli)?
5. Servono capacità da più fonti indipendenti?

Se la risposta a 1 è "ha un", a 3, 4 o 5 è "sì": composizione.

### Mixin: il compromesso

I mixin sono una forma disciplinata di ereditarietà multipla. Regole per mixin ben progettati:

```python
# BUON mixin: piccolo, focalizzato, senza stato proprio
class JsonMixin:
    """Aggiunge serializzazione JSON."""
    def to_json(self) -> str:
        import json
        return json.dumps(self.__dict__, default=str)

class AuditMixin:
    """Aggiunge tracciamento delle modifiche."""
    def registra_modifica(self, campo: str, vecchio, nuovo):
        if not hasattr(self, "_audit_log"):
            self._audit_log = []
        self._audit_log.append({
            "campo": campo, "da": vecchio, "a": nuovo
        })

# CATTIVO mixin: troppo complesso, stato proprio, __init__ pesante
class CattivaMixin:
    def __init__(self):       # Non farlo — conflitto con __init__ delle altre classi
        self.connessione = ConnessioneDB()
        self.cache = {}
```

### Dependency Injection come alternativa

La composizione si combina naturalmente con la Dependency Injection (DI):

```python
from typing import Protocol

class Logger(Protocol):
    def log(self, messaggio: str) -> None: ...

class ConsoleLogger:
    def log(self, messaggio: str) -> None:
        print(f"[LOG] {messaggio}")

class FileLogger:
    def __init__(self, percorso: str):
        self.percorso = percorso

    def log(self, messaggio: str) -> None:
        with open(self.percorso, "a") as f:
            f.write(f"{messaggio}\n")

class Servizio:
    def __init__(self, logger: Logger):  # DI: il logger viene iniettato
        self._logger = logger

    def elabora(self, dati):
        self._logger.log(f"Elaborazione di {len(dati)} elementi")
        return [d * 2 for d in dati]

# Facile da testare: si inietta un mock
servizio = Servizio(ConsoleLogger())
servizio.elabora([1, 2, 3])
```

---

## Design Pattern Avanzati in Python OOP

### Strategy con Protocol

Il pattern Strategy si implementa idiomaticamente con Protocol anziché con ABC, sfruttando il duck typing statico:

```python
from typing import Protocol

class StrategiaSconto(Protocol):
    def calcola(self, prezzo: float) -> float: ...

class ScontoPercentuale:
    def __init__(self, percentuale: float):
        self.percentuale = percentuale

    def calcola(self, prezzo: float) -> float:
        return prezzo * (1 - self.percentuale / 100)

class ScontoFisso:
    def __init__(self, importo: float):
        self.importo = importo

    def calcola(self, prezzo: float) -> float:
        return max(0, prezzo - self.importo)

class ScontoFedelta:
    def __init__(self, anni_cliente: int):
        self.anni = anni_cliente

    def calcola(self, prezzo: float) -> float:
        sconto = min(self.anni * 2, 20)  # max 20%
        return prezzo * (1 - sconto / 100)


class Carrello:
    def __init__(self, strategia_sconto: StrategiaSconto):
        self._strategia = strategia_sconto
        self._articoli: list[float] = []

    def aggiungi(self, prezzo: float):
        self._articoli.append(prezzo)

    @property
    def totale(self) -> float:
        subtotale = sum(self._articoli)
        return self._strategia.calcola(subtotale)


# Anche una semplice lambda funziona — structural subtyping!
carrello = Carrello(ScontoPercentuale(10))
carrello.aggiungi(100.0)
carrello.aggiungi(50.0)
print(f"Totale: {carrello.totale:.2f}")  # 135.00
```

### Registry Pattern

Il pattern Registry centralizza la mappatura tra identificatori e classi, spesso combinato con `__init_subclass__`:

```python
class SerializzatoreRegistry:
    """Registry con auto-registrazione tramite __init_subclass__."""
    _formati: dict[str, type] = {}

    def __init_subclass__(cls, *, formato: str = "", **kwargs):
        super().__init_subclass__(**kwargs)
        if formato:
            SerializzatoreRegistry._formati[formato] = cls

    @classmethod
    def ottieni(cls, formato: str) -> "SerializzatoreRegistry":
        classe = cls._formati.get(formato)
        if classe is None:
            formati_disponibili = ", ".join(cls._formati.keys())
            raise ValueError(
                f"Formato '{formato}' sconosciuto. "
                f"Disponibili: {formati_disponibili}"
            )
        return classe()

    def serializza(self, dati) -> str:
        raise NotImplementedError

    def deserializza(self, testo: str):
        raise NotImplementedError


class SerializzatoreJSON(SerializzatoreRegistry, formato="json"):
    def serializza(self, dati) -> str:
        import json
        return json.dumps(dati, default=str, indent=2)

    def deserializza(self, testo: str):
        import json
        return json.loads(testo)


class SerializzatoreCSV(SerializzatoreRegistry, formato="csv"):
    def serializza(self, dati) -> str:
        if not dati:
            return ""
        intestazioni = list(dati[0].keys())
        righe = [",".join(intestazioni)]
        for riga in dati:
            righe.append(",".join(str(riga[h]) for h in intestazioni))
        return "\n".join(righe)

    def deserializza(self, testo: str):
        righe = testo.strip().split("\n")
        intestazioni = righe[0].split(",")
        return [
            dict(zip(intestazioni, riga.split(",")))
            for riga in righe[1:]
        ]


# Uso — completamente disaccoppiato dalle implementazioni
s = SerializzatoreRegistry.ottieni("json")
print(s.serializza({"nome": "Anna", "eta": 30}))
```

### Factory con decoratore

```python
class FormaFactory:
    """Factory che usa un decoratore per la registrazione."""
    _creatori: dict[str, type] = {}

    @classmethod
    def registra(cls, nome: str):
        def decoratore(classe):
            cls._creatori[nome] = classe
            return classe
        return decoratore

    @classmethod
    def crea(cls, nome: str, **kwargs):
        classe = cls._creatori.get(nome)
        if classe is None:
            raise ValueError(f"Forma '{nome}' non registrata")
        return classe(**kwargs)


@FormaFactory.registra("cerchio")
class Cerchio:
    def __init__(self, raggio: float):
        self.raggio = raggio

    def area(self):
        import math
        return math.pi * self.raggio ** 2

@FormaFactory.registra("rettangolo")
class Rettangolo:
    def __init__(self, base: float, altezza: float):
        self.base = base
        self.altezza = altezza

    def area(self):
        return self.base * self.altezza


forma = FormaFactory.crea("cerchio", raggio=5)
print(f"Area: {forma.area():.2f}")  # Area: 78.54
```

### Observer Pattern con weak reference

Il pattern Observer permette a un oggetto (il soggetto) di notificare automaticamente tutti gli osservatori registrati quando il suo stato cambia, senza che il soggetto debba conoscere i dettagli degli osservatori. In Python, l'uso di `weakref` evita che la registrazione degli observer impedisca la garbage collection degli stessi, un problema comune nelle implementazioni naive del pattern.

```python
import weakref
from typing import Protocol, Any
from dataclasses import dataclass, field


class Osservatore(Protocol):
    def aggiorna(self, soggetto: Any, evento: str, dati: Any) -> None: ...


class EventBus:
    """Observer con weak references e filtraggio per evento."""

    def __init__(self):
        self._ascoltatori: dict[str, list[weakref.ref]] = {}

    def registra(self, evento: str, osservatore: Osservatore) -> None:
        if evento not in self._ascoltatori:
            self._ascoltatori[evento] = []
        ref = weakref.ref(osservatore, lambda r, e=evento: self._pulisci(e, r))
        self._ascoltatori[evento].append(ref)

    def _pulisci(self, evento: str, ref_morto: weakref.ref) -> None:
        if evento in self._ascoltatori:
            self._ascoltatori[evento] = [
                r for r in self._ascoltatori[evento] if r is not ref_morto
            ]

    def emetti(self, evento: str, soggetto: Any = None, dati: Any = None) -> None:
        for ref in self._ascoltatori.get(evento, []):
            osservatore = ref()
            if osservatore is not None:
                osservatore.aggiorna(soggetto, evento, dati)


@dataclass
class LoggerObserver:
    prefisso: str = "[LOG]"

    def aggiorna(self, soggetto: Any, evento: str, dati: Any) -> None:
        print(f"{self.prefisso} {evento}: {dati}")


@dataclass
class MetricsObserver:
    contatore: dict[str, int] = field(default_factory=dict)

    def aggiorna(self, soggetto: Any, evento: str, dati: Any) -> None:
        self.contatore[evento] = self.contatore.get(evento, 0) + 1


bus = EventBus()
logger = LoggerObserver()
metriche = MetricsObserver()
bus.registra("ordine_creato", logger)
bus.registra("ordine_creato", metriche)

bus.emetti("ordine_creato", dati={"id": 42, "importo": 99.99})
# [LOG] ordine_creato: {'id': 42, 'importo': 99.99}
print(metriche.contatore)  # {'ordine_creato': 1}
```

L'utilizzo di `weakref` è essenziale in applicazioni di lunga durata: se un osservatore viene distrutto (ad esempio una vista UI che viene chiusa), la sua registrazione nel bus degli eventi viene automaticamente invalidata senza necessità di una chiamata esplicita di deregistrazione. Il callback passato a `weakref.ref` ripulisce la lista interna al momento della garbage collection dell'osservatore, prevenendo memory leak.

Il filtraggio per evento consente inoltre di ridurre il rumore nelle notifiche: ciascun osservatore riceve solo gli eventi a cui è interessato, evitando il costo computazionale di smistamento centralizzato. Questo approccio scala bene anche in sistemi con centinaia di tipi di evento e decine di osservatori, poiché il dispatch è O(n) rispetto ai soli osservatori registrati per quell'evento specifico.

### State Pattern con Enum e transizioni validate

Il pattern State consente a un oggetto di modificare il proprio comportamento quando il suo stato interno cambia. In Python, la combinazione di `Enum` per gli stati e un dizionario di transizioni valide produce un'implementazione compatta e sicura rispetto a transizioni illegali.

```python
from enum import Enum, auto
from dataclasses import dataclass


class StatoOrdine(Enum):
    BOZZA = auto()
    CONFERMATO = auto()
    IN_SPEDIZIONE = auto()
    CONSEGNATO = auto()
    ANNULLATO = auto()


TRANSIZIONI_VALIDE: dict[StatoOrdine, set[StatoOrdine]] = {
    StatoOrdine.BOZZA: {StatoOrdine.CONFERMATO, StatoOrdine.ANNULLATO},
    StatoOrdine.CONFERMATO: {StatoOrdine.IN_SPEDIZIONE, StatoOrdine.ANNULLATO},
    StatoOrdine.IN_SPEDIZIONE: {StatoOrdine.CONSEGNATO},
    StatoOrdine.CONSEGNATO: set(),
    StatoOrdine.ANNULLATO: set(),
}


@dataclass
class Ordine:
    codice: str
    stato: StatoOrdine = StatoOrdine.BOZZA

    def transizione(self, nuovo_stato: StatoOrdine) -> None:
        if nuovo_stato not in TRANSIZIONI_VALIDE[self.stato]:
            raise ValueError(
                f"Transizione illegale: {self.stato.name} -> {nuovo_stato.name}. "
                f"Transizioni valide: {[s.name for s in TRANSIZIONI_VALIDE[self.stato]]}"
            )
        self.stato = nuovo_stato


ordine = Ordine("ORD-001")
ordine.transizione(StatoOrdine.CONFERMATO)   # OK
ordine.transizione(StatoOrdine.IN_SPEDIZIONE)  # OK
# ordine.transizione(StatoOrdine.BOZZA)      # ValueError: transizione illegale
```

Questa implementazione rende impossibile raggiungere uno stato senza passare attraverso le transizioni definite. La tabella di transizioni è dichiarativa: aggiungere un nuovo stato richiede solo l'aggiunta di una riga nell'Enum e una voce nel dizionario, senza modificare la logica di transizione. In scenari più complessi, ogni stato può essere associato a un comportamento specifico tramite un dizionario di callable, eliminando lunghe catene di `if/elif` e rendendo il codice estensibile senza violare il principio Open/Closed.

---

## Troubleshooting

### Errore MRO: "Cannot create a consistent method resolution order"

**Sintomo:**
```python
class A(X, Y): pass
class B(Y, X): pass
class C(A, B): pass  # TypeError!
```

**Causa:** L'ordine dei genitori in `A` e `B` crea un conflitto di precedenza non risolvibile dall'algoritmo C3.

**Soluzione:** Riordinare le basi in modo coerente, oppure rivedere la gerarchia. Spesso il problema indica che l'ereditarietà multipla è forzata e la composizione sarebbe più appropriata.

### Descriptor vs Property: l'attributo non viene intercettato

**Sintomo:** Il descriptor non viene invocato quando si accede all'attributo.

**Causa comune:** Il descriptor è stato assegnato all'istanza anziché alla classe.

```python
class Validatore:
    def __get__(self, obj, objtype=None):
        return "intercettato"

# SBAGLIATO — descriptor sull'istanza, non funziona
class Sbagliato:
    def __init__(self):
        self.attr = Validatore()  # nell'istanza → non è un descriptor

# CORRETTO — descriptor sulla classe
class Corretto:
    attr = Validatore()  # nella classe → funziona come descriptor
```

### Variabile di classe mutabile condivisa

**Sintomo:** Modificare un attributo su un'istanza modifica tutte le istanze.

**Causa:** Lista, dizionario o set come attributo di classe.

**Soluzione:** Spostare l'inizializzazione in `__init__`. Vedi la sezione [Variabili di Classe vs Istanza](#variabili-di-classe-vs-istanza--la-trappola-mutabile).

### `__eq__` senza `__hash__`: oggetti non usabili in set/dict

**Sintomo:** `TypeError: unhashable type: 'MiaClasse'` quando si tenta di usare l'oggetto come chiave.

**Causa:** Definire `__eq__` senza `__hash__` rende la classe non hashable per design.

**Soluzione:** Se l'oggetto è immutabile, definire `__hash__` coerente con `__eq__`. Se è mutabile, non dovrebbe essere usato come chiave.

### `super().__init__()` non chiamato in ereditarietà multipla

**Sintomo:** Alcuni attributi non vengono inizializzati, `AttributeError` imprevisto.

**Causa:** Una classe nella catena MRO non propaga la chiamata a `super().__init__()`.

**Soluzione:** Ogni `__init__` deve chiamare `super().__init__(**kwargs)`. Usare il pattern `**kwargs` per propagare parametri sconosciuti.

### `__slots__` ereditati non funzionano

**Sintomo:** La sottoclasse ha `__dict__` nonostante il genitore usi `__slots__`.

**Causa:** La sottoclasse non definisce il proprio `__slots__`.

**Soluzione:** Definire `__slots__` in ogni classe della gerarchia, includendo solo i *nuovi* attributi.

### `frozen=True` dataclass ma serve modificare un campo

**Sintomo:** `FrozenInstanceError` su assegnamento.

**Soluzione:** Usare `dataclasses.replace()` per creare una nuova istanza con i campi modificati:

```python
from dataclasses import dataclass, replace

@dataclass(frozen=True)
class Config:
    host: str
    porta: int

c1 = Config("localhost", 8080)
c2 = replace(c1, porta=9090)  # nuova istanza, non modifica c1
print(c2)  # Config(host='localhost', porta=9090)
```

---

## Esercizi

### Esercizio 1 — Descriptor di validazione

Implementare un descriptor `Tipizzato` che accetti un tipo, un valore minimo opzionale e un valore massimo opzionale. Usarlo per creare una classe `Prodotto` con attributi `nome` (str), `prezzo` (float, >= 0), `quantita` (int, >= 0, <= 10000). Verificare che i vincoli vengano applicati sia in `__init__` che in assegnamenti successivi.

### Esercizio 2 — MRO cooperativo

Creare una gerarchia di classi `Componente`, `Loggabile`, `Cacheable`, `Servizio(Loggabile, Cacheable)` dove tutti usano `super().__init__(**kwargs)` cooperativamente. Verificare che `Servizio.__mro__` sia quello atteso e che tutti gli `__init__` vengano eseguiti.

### Esercizio 3 — ABC con `collections.abc`

Implementare una classe `Dizionario Ordinato` che estenda `MutableMapping` (da `collections.abc`). Deve mantenere le chiavi nell'ordine di inserimento e supportare tutti i metodi del protocollo Mapping. Testare con `isinstance(d, MutableMapping)`.

### Esercizio 4 — Protocol generico

Definire un Protocol `Cache[T]` con metodi `get(key: str) -> T | None`, `set(key: str, value: T, ttl: int) -> None`, `delete(key: str) -> bool`. Implementare `MemoryCache` e `FileCache`. Scrivere una funzione `popola_cache(cache: Cache[str])` che funzioni con entrambe senza ereditarietà esplicita.

### Esercizio 5 — Enum con macchina a stati

Creare un Enum `StatoDocumento` con stati (BOZZA, IN_REVISIONE, APPROVATO, PUBBLICATO, ARCHIVIATO). Aggiungere un metodo `transizioni_valide()` che restituisca l'insieme degli stati raggiungibili. Implementare una classe `Documento` che usi questo Enum e impedisca transizioni non valide.

### Esercizio 6 — Metaclasse per ORM semplificato

Creare una metaclasse `ModelMeta` che raccolga automaticamente i descriptor `Campo` (tipo, nullable, default) definiti nella classe e li registri in un attributo `_schema`. Usarla per creare `class Utente(Model): nome = Campo(str); eta = Campo(int, nullable=True)`. Implementare un metodo `to_dict()` che usi `_schema`.

### Esercizio 7 — Dataclass frozen con pattern matching

Creare una gerarchia di dataclass frozen: `Espressione` (base), `Numero(valore: float)`, `Somma(sinistra: Espressione, destra: Espressione)`, `Prodotto(sinistra: Espressione, destra: Espressione)`. Implementare una funzione `valuta(expr: Espressione) -> float` che usi `match`/`case` con pattern matching strutturale.

### Esercizio 8 — Registry con __init_subclass__

Implementare un sistema di plugin con `__init_subclass__` che registri automaticamente ogni sottoclasse. Aggiungere un metodo `Plugin.carica(nome)` che istanzi il plugin per nome. Testare con almeno tre plugin concreti.

---

## Auto-Valutazione

Rispondi a queste domande per verificare la comprensione del modulo:

1. Qual è la differenza tra un data descriptor e un non-data descriptor? In che ordine Python risolve l'accesso agli attributi?

2. Cosa succede se una classe definisce `__eq__` ma non `__hash__`? Perché questa scelta è intenzionale?

3. Come funziona l'algoritmo C3 linearization? Fai un esempio di gerarchia non linearizzabile e spiega perché.

4. Quando si usa `__init_subclass__` rispetto a una metaclasse completa? Qual è il vantaggio principale?

5. Perché un attributo di classe mutabile (es. una lista) è una trappola? Come si risolve?

6. Qual è la differenza tra ABC e Protocol? Quando preferire uno all'altro?

7. Cosa fa `__set_name__` e perché è stato introdotto (PEP 487)?

8. Spiega il pattern cooperativo di `super()` nell'ereditarietà multipla. Cosa succede se una classe nella catena MRO non chiama `super()`?

9. Come funziona `@dataclass(frozen=True, slots=True)`? Quali vincoli impone? Come si modifica un campo di una dataclass frozen?

10. Perché restituire `NotImplemented` (non `NotImplementedError`) dai metodi di confronto? Cosa permette a Python di fare?

---

## Letture Consigliate

### Documentazione ufficiale

- **Python Data Model** — docs.python.org/3/reference/datamodel.html — Sezioni 3.3.1 (special methods), 3.3.2 (descriptors), 3.3.3 (metaclasses).
- **Descriptor HowTo Guide** — docs.python.org/3/howto/descriptor.html — Guida ufficiale di Raymond Hettinger.
- **`abc` module** — docs.python.org/3/library/abc.html.
- **`collections.abc`** — docs.python.org/3/library/collections.abc.html.
- **`enum` module** — docs.python.org/3/library/enum.html.
- **`dataclasses` module** — docs.python.org/3/library/dataclasses.html.

### PEP di riferimento

- **PEP 487** — Simpler customisation of class creation (`__init_subclass__`, `__set_name__`).
- **PEP 544** — Protocols: Structural subtyping (static duck typing).
- **PEP 557** — Data Classes.
- **PEP 634** — Structural Pattern Matching (match/case).
- **PEP 3119** — Introducing Abstract Base Classes.
- **PEP 3135** — New super.

### Libri

- Luciano Ramalho, *Fluent Python* (2nd ed., O'Reilly, 2022) — capitoli 11-16 su descriptor, metaclassi, overloading di operatori.
- Brett Slatkin, *Effective Python* (3rd ed., Addison-Wesley, 2024) — item su metaclassi, descriptor, `__init_subclass__`.

---

## Cross-link

| Modulo | Relazione |
|---|---|
| [01-fondamenti-linguaggio](01-fondamenti-linguaggio.md) | Prerequisito: funzioni, scope, namespace |
| [03-strutture-dati-avanzate](03-strutture-dati-avanzate.md) | `collections.abc`, implementazioni personalizzate di container |
| [04-decoratori-generatori-context-manager](04-decoratori-generatori-context-manager.md) | Decoratori di classe, context manager protocol, `contextlib` |
| [08-testing](08-testing.md) | Mock di classi, testing OOP, dependency injection per test |
| [09-type-hints-e-mypy](09-type-hints-e-mypy.md) | Protocol, Generic, TypeVar, verifica statica |
| [21-design-patterns](21-design-patterns.md) | Pattern GoF completi, SOLID, architettura |
| [22-clean-code](22-clean-code.md) | Principi di design, SRP, composizione |

---

## Glossario

| Termine | Definizione |
|---|---|
| **ABC** | Abstract Base Class — classe base astratta che definisce un contratto via `@abstractmethod`. |
| **Binding** | Meccanismo per cui l'accesso a un metodo da un'istanza produce un *bound method* con `self` pre-impostato. |
| **C3 linearization** | Algoritmo usato da Python per calcolare la MRO nelle gerarchie con ereditarietà multipla. |
| **Data descriptor** | Descriptor che definisce `__get__` e almeno uno tra `__set__` o `__delete__`. Ha priorità su `__dict__`. |
| **Descriptor** | Oggetto che implementa `__get__`, `__set__` e/o `__delete__` e controlla l'accesso agli attributi. |
| **Diamond problem** | Ambiguità quando una classe eredita da due classi che condividono un antenato comune. Risolto dalla MRO C3. |
| **Duck typing** | Filosofia per cui il tipo di un oggetto è determinato dai metodi che implementa, non dalla sua classe. |
| **Dunder method** | Metodo speciale con nome `__nome__` (double underscore). Invocato automaticamente da Python. |
| **Frozen dataclass** | Dataclass con `frozen=True` — immutabile e hashable. |
| **Metaclasse** | Classe di una classe. Controlla la creazione delle classi. `type` è la metaclasse predefinita. |
| **Mixin** | Classe progettata per aggiungere funzionalità tramite ereditarietà multipla, senza essere usata autonomamente. |
| **MRO** | Method Resolution Order — ordine in cui Python cerca i metodi nella gerarchia di classi. |
| **Name mangling** | Trasformazione di `__attr` in `_Classe__attr` per evitare conflitti in ereditarietà. |
| **Non-data descriptor** | Descriptor che definisce solo `__get__`. L'istanza `__dict__` ha priorità. |
| **Nominal subtyping** | Sottotipizzazione basata sull'ereditarietà esplicita (es. ABC). |
| **Protocol** | Interfaccia strutturale (PEP 544) — una classe è conforme se implementa i metodi richiesti, senza ereditarietà. |
| **Structural subtyping** | Sottotipizzazione basata sulla struttura (metodi/attributi), non sull'ereditarietà. Sinonimo di static duck typing. |
| **Virtual subclass** | Classe registrata come sottoclasse di una ABC tramite `register()`, senza ereditarietà reale. |
| **`__init_subclass__`** | Hook chiamato sulla classe genitore quando viene definita una sottoclasse (PEP 487). |
| **`__set_name__`** | Hook sui descriptor, chiamato alla creazione della classe, che fornisce il nome dell'attributo (PEP 487). |
| **`__slots__`** | Dichiarazione che sostituisce `__dict__` con attributi a dimensione fissa, risparmiando memoria. |
