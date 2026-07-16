# Tutorial 02 — Programmazione Orientata agli Oggetti in Python: Dal Principiante all'Esperto

> **Companion a:** `02-oop.md`
> **Scope:** Classi, ereditarietà, polimorfismo, MRO, dunder methods, dataclass, ABC, Protocol, descriptor, metaclassi
> **Prerequisiti:** `tutorial_01_fondamenti_linguaggio.md` — funzioni, scope, namespace, tipi built-in
> **Durata stimata:** 20-30 ore di studio + esercizi
> **Lingua:** Italiano — termini tecnici in inglese preservati
> **Versione Python:** 3.12+

---

## Indice Generale

- [Parte A — Basi Assolute](#parte-a--basi-assolute)
  - [A1. Perché l'OOP? Il problema che risolve](#a1-perché-lOOP-il-problema-che-risolve)
  - [A2. Classi e oggetti: blueprint e istanze](#a2-classi-e-oggetti-blueprint-e-istanze)
  - [A3. Il costruttore `__init__` e il parametro `self`](#a3-il-costruttore-__init__-e-il-parametro-self)
  - [A4. Attributi di istanza vs attributi di classe](#a4-attributi-di-istanza-vs-attributi-di-classe)
  - [A5. Metodi di istanza, `@classmethod`, `@staticmethod`](#a5-metodi-di-istanza-classmethod-staticmethod)
  - [A6. Rappresentazione testuale: `__str__` e `__repr__`](#a6-rappresentazione-testuale-__str__-e-__repr__)
  - [A7. Incapsulamento: visibilità e `@property`](#a7-incapsulamento-visibilità-e-property)
  - [A8. Ereditarietà singola e `super()`](#a8-ereditarietà-singola-e-super)
  - [A9. Polimorfismo e duck typing](#a9-polimorfismo-e-duck-typing)
- [Parte B — Comprensione Profonda](#parte-b--comprensione-profonda)
  - [B1. Ereditarietà multipla e MRO (Linearizzazione C3)](#b1-ereditarietà-multipla-e-mro-linearizzazione-c3)
  - [B2. Mixin: composizione tramite ereditarietà disciplinata](#b2-mixin-composizione-tramite-ereditarietà-disciplinata)
  - [B3. Dunder methods completi](#b3-dunder-methods-completi)
  - [B4. La trappola degli attributi di classe mutabili](#b4-la-trappola-degli-attributi-di-classe-mutabili)
  - [B5. dataclass: zero boilerplate per classi dati](#b5-dataclass-zero-boilerplate-per-classi-dati)
  - [B6. `__slots__`: memoria ottimizzata](#b6-__slots__-memoria-ottimizzata)
  - [B7. Enum: costanti tipizzate](#b7-enum-costanti-tipizzate)
  - [B8. Abstract Base Classes (ABC)](#b8-abstract-base-classes-abc)
  - [B9. Protocol: duck typing statico (PEP 544)](#b9-protocol-duck-typing-statico-pep-544)
- [Parte C — Esercizi Pratici Guidati](#parte-c--esercizi-pratici-guidati)
  - [C1. Esercizi progressivi con soluzione](#c1-esercizi-progressivi-con-soluzione)
  - [C2. Mini-progetto: sistema di gestione biblioteca](#c2-mini-progetto-sistema-di-gestione-biblioteca)
- [Parte D — Approfondimento per Esperti](#parte-d--approfondimento-per-esperti)
  - [D1. Protocollo Descriptor](#d1-protocollo-descriptor)
  - [D2. Metaclassi e `__init_subclass__`](#d2-metaclassi-e-__init_subclass__)
  - [D3. Design Pattern avanzati in Python OOP](#d3-design-pattern-avanzati-in-python-oop)
  - [D4. Composizione vs ereditarietà: framework decisionale](#d4-composizione-vs-ereditarietà-framework-decisionale)
- [Parte E — Riepilogo, Checklist e Prossimi Passi](#parte-e--riepilogo-checklist-e-prossimi-passi)

---

## Mappa concettuale

```
                            ┌────────────────┐
                            │    object       │  ← radice universale di tutto
                            └───────┬────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
      ┌───────▼───────┐    ┌───────▼───────┐    ┌────────▼───────┐
      │     type       │    │     ABC       │    │    Protocol    │
      │  (metaclasse)  │    │  (nominale)   │    │ (strutturale)  │
      └───────┬────────┘    └───────┬───────┘    └────────┬───────┘
              │                     │                     │
     crea le classi        contratto esplicito    duck typing statico
     __init_subclass__     @abstractmethod        PEP 544
     __set_name__          register()             runtime_checkable
              │                     │                     │
              ▼                     ▼                     ▼
    ┌──────────────────────────────────────────────────────────────┐
    │                    Classe concreta                           │
    │  ┌──────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐ │
    │  │ __init__ │  │ __slots__ │  │ @property │  │ descriptor│ │
    │  │ __repr__ │  │ @dataclass│  │ __get__   │  │ __set__   │ │
    │  │ __eq__   │  │ frozen    │  │ __delete__│  │__set_name_│ │
    │  │ __hash__ │  │ kw_only   │  │           │  │           │ │
    │  └──────────┘  └───────────┘  └───────────┘  └───────────┘ │
    └──────────────────────────────────────────────────────────────┘
              │                           │
      ┌───────┴───────┐          ┌────────┴────────┐
      │  Ereditarietà │          │  Composizione   │
      │  (is-a)       │          │  (has-a)        │
      │  MRO C3       │          │  Delega         │
      │  super()      │          │  Injezione DI   │
      └───────────────┘          └─────────────────┘
```

---

# Parte A — Basi Assolute

---

## A1. Perché l'OOP? Il problema che risolve

> **Analogia:** Immagina di costruire una città senza progetto architettonico. Ogni edificio è fatto da mattoni sparsi dappertutto, senza strade né indirizzi. Trovare un appartamento specifico diventa impossibile. L'OOP è il piano urbanistico: raggruppa mattoni correlati in edifici con indirizzi precisi, in modo che tutto sia trovabile e modificabile senza demolire il resto della città.

Prima dell'OOP, i programmi erano scritti in stile **procedurale**: una sequenza di funzioni che operano su variabili globali. Questo funziona bene per programmi piccoli, ma scala male.

**Il problema procedurale:**

```python
# Stile procedurale — dati e logica sparsi
nome_cliente = "Anna"
saldo_cliente = 1000.0
email_cliente = "anna@example.com"

nome_cliente2 = "Marco"
saldo_cliente2 = 500.0
email_cliente2 = "marco@example.com"

def deposita(saldo, importo):
    return saldo + importo

def preleva(saldo, importo):
    if importo > saldo:
        return saldo, False
    return saldo - importo, True

# Problema: chi appartiene a chi? Facile fare errori.
saldo_cliente = deposita(saldo_cliente, 200)
saldo_cliente2, ok = preleva(saldo_cliente2, 600)  # errore silenzioso
```

**La soluzione OOP:** raggruppare dati e comportamenti correlati in un'unica entità — la **classe**.

```python
class ContoBancario:
    def __init__(self, nome, saldo_iniziale):
        self.nome = nome
        self.saldo = saldo_iniziale

    def deposita(self, importo):
        self.saldo += importo

    def preleva(self, importo):
        if importo > self.saldo:
            raise ValueError(f"Fondi insufficienti: disponibile {self.saldo}")
        self.saldo -= importo

# Ora ogni oggetto porta con sé i propri dati e la propria logica.
anna = ContoBancario("Anna", 1000.0)
marco = ContoBancario("Marco", 500.0)

anna.deposita(200)
marco.preleva(100)
```

I quattro pilastri dell'OOP:

| Pilastro | Significato in Python |
|---|---|
| **Incapsulamento** | Dati + metodi in un'unica classe; visibilità controllata con `_` e `__` |
| **Ereditarietà** | Sottoclasse eredita attributi e metodi dalla superclasse |
| **Polimorfismo** | Oggetti diversi rispondono allo stesso messaggio in modi diversi |
| **Astrazione** | Esponi solo l'interfaccia pubblica; nascondi i dettagli implementativi |

---

## A2. Classi e oggetti: blueprint e istanze

> **Analogia:** La classe è il _progetto di un edificio_. L'istanza è l'edificio costruito. Dal progetto si possono costruire migliaia di edifici, ognuno con i propri inquilini e il proprio arredamento, ma tutti con la stessa struttura portante.

```python
class Automobile:
    """Blueprint per qualsiasi automobile."""

    # Attributo di classe — condiviso tra tutte le istanze
    numero_ruote = 4

    def __init__(self, marca: str, modello: str, anno: int):
        # Attributi di istanza — unici per ogni oggetto
        self.marca = marca
        self.modello = modello
        self.anno = anno
        self.velocita = 0       # stato iniziale

    def accelera(self, incremento: int) -> int:
        self.velocita += incremento
        return self.velocita

    def frena(self, decremento: int) -> int:
        self.velocita = max(0, self.velocita - decremento)
        return self.velocita

    def descrizione(self) -> str:
        return f"{self.marca} {self.modello} ({self.anno})"
```

**Istanziazione** — creare oggetti concreti dal blueprint:

```python
fiat = Automobile("Fiat", "500", 2022)
bmw = Automobile("BMW", "M3", 2024)

print(fiat.descrizione())   # Fiat 500 (2022)
print(bmw.descrizione())    # BMW M3 (2024)

fiat.accelera(50)
print(fiat.velocita)   # 50
print(bmw.velocita)    # 0 — ogni istanza ha il proprio stato

# Attributo di classe — accessibile sia dalla classe che dall'istanza
print(Automobile.numero_ruote)   # 4
print(fiat.numero_ruote)         # 4
```

Internamente, quando si scrive `fiat = Automobile("Fiat", "500", 2022)`:
1. Python chiama `Automobile.__new__(Automobile)` per creare un oggetto vuoto
2. Chiama `Automobile.__init__(fiat, "Fiat", "500", 2022)` per inizializzarlo
3. Restituisce l'oggetto pronto all'uso

---

## A3. Il costruttore `__init__` e il parametro `self`

Il metodo `__init__` è l'**inizializzatore** (non un vero costruttore in senso tecnico — quello è `__new__`, ma per l'utilizzo quotidiano la distinzione è irrilevante). Il suo compito: impostare lo stato iniziale dell'oggetto.

**`self`** è il riferimento all'istanza corrente. Python lo passa automaticamente come primo argomento di ogni metodo di istanza. Il nome è una convenzione fortissima — non usare altro.

```python
class Persona:
    def __init__(self, nome: str, eta: int):
        # Assegnare tutti gli attributi in __init__
        # rende immediatamente chiaro cosa gestisce la classe
        self.nome = nome
        self.eta = eta
        self._visite_mediche = []  # attributo con valore di default

    def aggiungi_visita(self, data: str, medico: str) -> None:
        self._visite_mediche.append({"data": data, "medico": medico})

    def num_visite(self) -> int:
        return len(self._visite_mediche)
```

**Buona pratica:** inizializza **tutti** gli attributi in `__init__`, anche quelli con valore predefinito. Aggiungere attributi dinamicamente nei metodi rende il codice difficile da leggere.

```python
# Male — attributo creato fuori da __init__
class Male:
    def __init__(self, nome):
        self.nome = nome

    def attiva(self):
        self.attivo = True  # chi lo sa che esiste?

# Bene — tutto dichiarato in __init__
class Bene:
    def __init__(self, nome):
        self.nome = nome
        self.attivo = False  # chiaro fin dall'inizio
```

---

## A4. Attributi di istanza vs attributi di classe

```python
class Contatore:
    totale_istanze = 0        # attributo di CLASSE — condiviso

    def __init__(self, nome: str):
        self.nome = nome      # attributo di ISTANZA — unico
        self.valore = 0
        Contatore.totale_istanze += 1   # modifica l'attributo di classe

    def incrementa(self, n: int = 1) -> None:
        self.valore += n

c1 = Contatore("primo")
c2 = Contatore("secondo")

print(Contatore.totale_istanze)  # 2  — visto dalla classe
print(c1.totale_istanze)         # 2  — visibile anche dall'istanza
print(c1.valore)                 # 0  — unico per c1
print(c2.valore)                 # 0  — unico per c2

c1.incrementa(5)
print(c1.valore)   # 5
print(c2.valore)   # 0  — non influenzato
```

**Regola cruciale — attributi mutabili:** non mettere mai un `list`, `dict` o `set` come attributo di classe se vuoi che ogni istanza abbia il proprio. Vedi [B4](#b4-la-trappola-degli-attributi-di-classe-mutabili) per l'approfondimento.

---

## A5. Metodi di istanza, `@classmethod`, `@staticmethod`

```python
from datetime import datetime

class Evento:
    categoria_default = "generico"

    def __init__(self, titolo: str, data: datetime):
        self.titolo = titolo
        self.data = data
        self.partecipanti: list[str] = []

    # ── Metodo di istanza ─────────────────────────────────────────
    # Riceve self → accede ai dati dell'istanza specifica
    def aggiungi_partecipante(self, nome: str) -> None:
        self.partecipanti.append(nome)

    def info(self) -> str:
        return f"{self.titolo} il {self.data:%d/%m/%Y} — {len(self.partecipanti)} partecipanti"

    # ── Metodo di classe ──────────────────────────────────────────
    # Riceve cls → accede alla classe, non all'istanza
    # Uso tipico: costruttori alternativi (factory method)
    @classmethod
    def da_stringa(cls, s: str) -> "Evento":
        """Crea un Evento dalla stringa 'titolo|YYYY-MM-DD'."""
        titolo, data_str = s.split("|")
        data = datetime.strptime(data_str.strip(), "%Y-%m-%d")
        return cls(titolo.strip(), data)

    @classmethod
    def imposta_categoria_default(cls, categoria: str) -> None:
        cls.categoria_default = categoria

    # ── Metodo statico ────────────────────────────────────────────
    # Non riceve né self né cls → funzione di utilità collegata alla classe
    @staticmethod
    def valida_titolo(titolo: str) -> bool:
        return bool(titolo) and len(titolo) <= 200


# Metodo di istanza — richiede un'istanza
e1 = Evento("Conferenza Python", datetime(2026, 9, 15))
e1.aggiungi_partecipante("Anna")
print(e1.info())   # Conferenza Python il 15/09/2026 — 1 partecipanti

# Metodo di classe — invocato sulla classe, non sull'istanza
e2 = Evento.da_stringa("Workshop OOP | 2026-10-01")
print(e2.titolo)   # Workshop OOP

# Metodo statico — non richiede istanza
print(Evento.valida_titolo(""))   # False
print(Evento.valida_titolo("ok")) # True
```

**Quando usare quale:**
- **Metodo di istanza** → quando serve accedere o modificare lo stato dell'oggetto (`self`)
- **`@classmethod`** → factory method, accesso a stato di classe, sottoclassi-compatibile (`cls`)
- **`@staticmethod`** → funzione di utilità logicamente legata alla classe ma senza dipendenze su istanza o classe

---

## A6. Rappresentazione testuale: `__str__` e `__repr__`

```python
class Prodotto:
    def __init__(self, nome: str, prezzo: float, sku: str):
        self.nome = nome
        self.prezzo = prezzo
        self.sku = sku

    def __repr__(self) -> str:
        """Per sviluppatori: non ambiguo, idealmente riproducibile.
        Usato nella shell interattiva, nei log, dentro liste e dizionari."""
        return f"Prodotto(nome={self.nome!r}, prezzo={self.prezzo!r}, sku={self.sku!r})"

    def __str__(self) -> str:
        """Per utenti finali: leggibile e formattato.
        Usato da print() e str()."""
        return f"{self.nome} — €{self.prezzo:.2f} (SKU: {self.sku})"


p = Prodotto("Laptop", 999.99, "LAP-001")

print(p)          # Prodotto — €999.99 (SKU: LAP-001)     — usa __str__
print(repr(p))    # Prodotto(nome='Laptop', prezzo=999.99, sku='LAP-001')   — usa __repr__

# Dentro una lista Python usa __repr__:
lista = [p, Prodotto("Mouse", 29.90, "MOU-005")]
print(lista)      # [Prodotto(nome='Laptop'...), Prodotto(nome='Mouse'...)]
```

**Regola pratica:**
- Definisci **sempre** `__repr__` — è il minimo sindacale per il debugging
- Aggiungi `__str__` quando la rappresentazione leggibile deve essere diversa da quella tecnica
- Se manca `__str__`, Python usa `__repr__` al suo posto

---

## A7. Incapsulamento: visibilità e `@property`

> **Analogia:** Un'automobile espone un volante, un pedale dell'acceleratore e uno del freno. Non espone il carburatore o il sistema di iniezione. Puoi guidare senza sapere come funziona internamente. L'incapsulamento fa lo stesso: esponi un'interfaccia pulita e nascondi la complessità.

Python non ha modificatori di accesso come `private` in Java. Usa **convenzioni di denominazione:**

```python
class ContoBancario:
    def __init__(self, titolare: str, saldo: float):
        self.titolare = titolare          # pubblico — parte dell'interfaccia
        self._valuta = "EUR"              # protetto — usa con cautela (per convenzione)
        self.__saldo = saldo              # privato — name mangling attivo

    def get_saldo(self) -> float:
        return self.__saldo

    def deposita(self, importo: float) -> None:
        if importo <= 0:
            raise ValueError("L'importo deve essere positivo")
        self.__saldo += importo
```

Il **name mangling** di `__saldo` lo trasforma in `_ContoBancario__saldo`, evitando collisioni in gerarchie di ereditarietà:

```python
c = ContoBancario("Anna", 1000.0)
# c.__saldo             → AttributeError
# c._ContoBancario__saldo  → 1000.0 (possibile ma sconsigliato)
```

### Il decoratore `@property`

Preferire `@property` ai getter/setter espliciti — è la via pythonica:

```python
class Temperatura:
    def __init__(self, celsius: float = 0.0):
        self._celsius = celsius

    @property
    def celsius(self) -> float:
        return self._celsius

    @celsius.setter
    def celsius(self, valore: float) -> None:
        if valore < -273.15:
            raise ValueError("Temperatura sotto lo zero assoluto")
        self._celsius = valore

    @property
    def fahrenheit(self) -> float:
        """Proprietà derivata — solo lettura."""
        return self._celsius * 9 / 5 + 32

    @property
    def kelvin(self) -> float:
        return self._celsius + 273.15


t = Temperatura(100)
print(t.fahrenheit)   # 212.0
print(t.kelvin)       # 373.15

t.celsius = 25        # chiama il setter con validazione
# t.celsius = -300    # ValueError
```

**Vantaggio fondamentale:** il codice che usa la classe scrive `t.celsius = 25` (attributo) anziché `t.set_celsius(25)` (metodo). Se in futuro serve validazione, si aggiunge il setter senza cambiare l'API pubblica.

---

## A8. Ereditarietà singola e `super()`

> **Analogia:** La sottoclasse è come un dipendente specializzato che eredita le competenze base dell'azienda (superclasse) e le arricchisce con abilità specifiche del proprio ruolo. Non deve reinventare il modo di rispondere al telefono — lo eredita e lo può personalizzare.

```python
class Animale:
    def __init__(self, nome: str, eta: int):
        self.nome = nome
        self.eta = eta

    def parla(self) -> str:
        raise NotImplementedError(f"{type(self).__name__} deve implementare parla()")

    def descrizione(self) -> str:
        return f"{self.nome} ({self.eta} anni)"

    def __repr__(self) -> str:
        return f"{type(self).__name__}(nome={self.nome!r}, eta={self.eta!r})"


class Cane(Animale):
    def __init__(self, nome: str, eta: int, razza: str):
        super().__init__(nome, eta)   # delega l'init al genitore
        self.razza = razza

    def parla(self) -> str:
        return f"{self.nome} dice: Bau!"

    def riporta(self, oggetto: str) -> str:
        return f"{self.nome} riporta {oggetto}"


class Gatto(Animale):
    def __init__(self, nome: str, eta: int, indoor: bool = True):
        super().__init__(nome, eta)
        self.indoor = indoor

    def parla(self) -> str:
        return f"{self.nome} dice: Miao!"


rex = Cane("Rex", 5, "Pastore Tedesco")
print(rex.descrizione())      # Rex (5 anni)  — metodo EREDITATO
print(rex.parla())            # Rex dice: Bau! — metodo SOVRASCRITTO
print(rex.riporta("palla"))   # Rex riporta palla — metodo ESCLUSIVO

print(isinstance(rex, Cane))    # True
print(isinstance(rex, Animale)) # True — la relazione è transitiva
print(issubclass(Cane, Animale)) # True
```

**`super()`** — non chiama il "genitore diretto" ma la classe successiva nella MRO (Method Resolution Order). In ereditarietà singola coincidono, ma in ereditarietà multipla questa distinzione diventa cruciale (vedi B1).

### Override e estensione

```python
class VeicoloElettrico(Automobile):
    def __init__(self, marca: str, modello: str, anno: int, kwh: float):
        super().__init__(marca, modello, anno)
        self.capacita_batteria_kwh = kwh
        self.carica_percentuale = 100

    def accelera(self, incremento: int) -> int:
        """Override: consuma anche la batteria."""
        consumo = incremento * 0.1   # kWh per ogni km/h di accelerazione
        if self.carica_percentuale < 5:
            raise RuntimeError("Batteria quasi scarica!")
        self.carica_percentuale = max(0, self.carica_percentuale - consumo)
        return super().accelera(incremento)  # chiama il metodo del genitore

    def ricarica(self) -> None:
        self.carica_percentuale = 100
```

---

## A9. Polimorfismo e duck typing

> **Analogia:** Una presa elettrica standard accetta qualsiasi spina conforme alla norma — non le importa se è collegata a un frullatore, un laptop o un caricabatterie. Il polimorfismo funziona allo stesso modo: la funzione `fai_parlare()` accetta qualsiasi oggetto che "sappia parlare", indipendentemente dal tipo.

In Python il polimorfismo si ottiene principalmente tramite **duck typing**: *"Se cammina come un'anatra e starnazza come un'anatra, allora è un'anatra."*

```python
class Cane:
    def parla(self) -> str:
        return "Bau!"

class Gatto:
    def parla(self) -> str:
        return "Miao!"

class Pappagallo:
    def parla(self) -> str:
        return "Ciao bello!"

class Robot:
    def parla(self) -> str:
        return "01001000 01101001"


def fai_parlare(essere) -> None:
    """Funziona con qualsiasi oggetto che abbia un metodo parla()."""
    print(essere.parla())


animali = [Cane(), Gatto(), Pappagallo(), Robot()]
for a in animali:
    fai_parlare(a)
# Bau!
# Miao!
# Ciao bello!
# 01001000 01101001
```

`Cane`, `Gatto`, `Pappagallo` e `Robot` non hanno nessuna relazione di ereditarietà. Funzionano lo stesso perché **implementano tutti il metodo `parla()`**.

### Overloading degli operatori

Python permette di ridefinire gli operatori per le classi custom tramite i dunder method:

```python
class Vettore2D:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def __add__(self, altro: "Vettore2D") -> "Vettore2D":
        return Vettore2D(self.x + altro.x, self.y + altro.y)

    def __mul__(self, scalare: float) -> "Vettore2D":
        return Vettore2D(self.x * scalare, self.y * scalare)

    def __rmul__(self, scalare: float) -> "Vettore2D":
        return self.__mul__(scalare)   # 3 * v funziona come v * 3

    def __eq__(self, altro: object) -> bool:
        if not isinstance(altro, Vettore2D):
            return NotImplemented
        return self.x == altro.x and self.y == altro.y

    def magnitudine(self) -> float:
        return (self.x ** 2 + self.y ** 2) ** 0.5

    def __repr__(self) -> str:
        return f"Vettore2D({self.x}, {self.y})"


v1 = Vettore2D(3, 4)
v2 = Vettore2D(1, 2)

print(v1 + v2)     # Vettore2D(4, 6)
print(v1 * 2)      # Vettore2D(6, 8)
print(3 * v2)      # Vettore2D(3, 6)  — usa __rmul__
print(v1 == Vettore2D(3, 4))   # True
print(v1.magnitudine())         # 5.0
```

**Nota su `NotImplemented`:** restituire `NotImplemented` (non `raise NotImplementedError`) dai metodi di confronto permette a Python di provare l'operazione inversa (`altro.__eq__(self)`) prima di lanciare un errore.

---

# Parte B — Comprensione Profonda

---

## B1. Ereditarietà multipla e MRO (Linearizzazione C3)

> **Analogia:** Immagina di ricevere istruzioni da due capi gerarchici che entrambi "hanno ereditato" le stesse direttive da un direttore comune. Senza un protocollo chiaro, potresti ricevere le stesse istruzioni due volte, o peggio, versioni contraddittorie. Il MRO C3 è il protocollo che stabilisce l'ordine esatto in cui consultare ogni "capo".

Python supporta l'ereditarietà multipla e risolve le ambiguità con l'algoritmo **C3 linearization**:

```python
class A:
    def saluta(self) -> str:
        return "Ciao da A"

class B(A):
    def saluta(self) -> str:
        return "Ciao da B"

class C(A):
    def saluta(self) -> str:
        return "Ciao da C"

class D(B, C):
    pass


d = D()
print(d.saluta())    # "Ciao da B"
print(D.__mro__)
# (<class 'D'>, <class 'B'>, <class 'C'>, <class 'A'>, <class 'object'>)
```

La MRO di `D` è `[D, B, C, A, object]`. Quando si cerca `saluta()`:
1. `D` — non definisce `saluta()`, vai avanti
2. `B` — trovato! Restituisce "Ciao da B"

**L'algoritmo C3** garantisce tre proprietà:
- Le sottoclassi vengono sempre prima delle superclassi
- L'ordine di elencazione dei genitori è rispettato
- Ogni classe appare una sola volta

```python
# Visualizzare la MRO di qualsiasi classe
for cls in D.__mro__:
    print(cls.__name__)
# D → B → C → A → object
```

### `super()` cooperativo

`super()` chiama la **classe successiva nella MRO**, non il genitore diretto. Questo è fondamentale con i mixin:

```python
class Base:
    def __init__(self, **kwargs):
        super().__init__()   # propaga a object

class MixinLog(Base):
    def __init__(self, **kwargs):
        print(f"MixinLog init: {kwargs.get('nome', '?')}")
        super().__init__(**kwargs)

class MixinAudit(Base):
    def __init__(self, **kwargs):
        print("MixinAudit init")
        super().__init__(**kwargs)

class Servizio(MixinLog, MixinAudit):
    def __init__(self, nome: str, **kwargs):
        print(f"Servizio init: {nome}")
        super().__init__(nome=nome, **kwargs)


# MRO: Servizio → MixinLog → MixinAudit → Base → object
s = Servizio("api-gateway")
# Servizio init: api-gateway
# MixinLog init: api-gateway
# MixinAudit init
```

Ogni `__init__` chiama `super().__init__(**kwargs)` e la chiamata si propaga lungo la MRO. Se una classe nella catena non chiama `super()`, le classi successive non vengono inizializzate — un bug insidioso.

### MRO non risolvibile

Se due basi stabiliscono ordini contraddittori, Python lancia `TypeError` a tempo di definizione:

```python
class X: pass
class Y: pass
class A(X, Y): pass   # A dice: X prima di Y
class B(Y, X): pass   # B dice: Y prima di X

# class C(A, B): pass
# TypeError: Cannot create a consistent method resolution order (MRO)
```

---

## B2. Mixin: composizione tramite ereditarietà disciplinata

Un **mixin** è una classe progettata per aggiungere funzionalità specifiche senza essere mai istanziata da sola. Regole per un buon mixin:
- Piccolo e focalizzato su una sola responsabilità
- Senza stato proprio (no attributi nell'`__init__`) o con stato minimo
- Nome che termina con `Mixin`

```python
import json
from datetime import datetime


class JsonMixin:
    """Aggiunge serializzazione/deserializzazione JSON a qualsiasi classe."""

    def to_json(self) -> str:
        return json.dumps(self.__dict__, default=str, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "JsonMixin":
        dati = json.loads(json_str)
        return cls(**dati)


class TimestampMixin:
    """Aggiunge timestamp di creazione e ultima modifica."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.creato_il = datetime.now().isoformat()
        self.modificato_il = self.creato_il

    def aggiorna_timestamp(self) -> None:
        self.modificato_il = datetime.now().isoformat()


class ValidazioneMixin:
    """Aggiunge validazione degli attributi tramite _validazioni."""

    def valida(self) -> list[str]:
        """Restituisce lista di errori (vuota = valido)."""
        errori = []
        for nome, validatore in getattr(self, "_validazioni", {}).items():
            valore = getattr(self, nome, None)
            try:
                validatore(valore)
            except (ValueError, TypeError) as e:
                errori.append(f"{nome}: {e}")
        return errori


class Utente(JsonMixin, TimestampMixin):
    _validazioni = {
        "email": lambda v: None if "@" in (v or "") else (_ for _ in ()).throw(ValueError("email non valida")),
    }

    def __init__(self, nome: str, email: str):
        self.nome = nome
        self.email = email
        super().__init__()  # inizializza i mixin

    def __repr__(self) -> str:
        return f"Utente(nome={self.nome!r}, email={self.email!r})"


u = Utente("Anna", "anna@example.com")
print(u.to_json())
# {
#   "nome": "Anna",
#   "email": "anna@example.com",
#   "creato_il": "...",
#   "modificato_il": "..."
# }
```

---

## B3. Dunder methods completi

I **dunder methods** (da _double underscore_) personalizzano il comportamento degli oggetti con operatori e funzioni built-in. Python li chiama automaticamente.

### Confronto e hashing

```python
from functools import total_ordering

@total_ordering
class Versione:
    """Con @total_ordering: basta __eq__ + uno tra __lt__/__gt__/__le__/__ge__."""

    def __init__(self, major: int, minor: int, patch: int = 0):
        self.major = major
        self.minor = minor
        self.patch = patch

    def _come_tupla(self) -> tuple:
        return (self.major, self.minor, self.patch)

    def __eq__(self, altro: object) -> bool:
        if not isinstance(altro, Versione):
            return NotImplemented
        return self._come_tupla() == altro._come_tupla()

    def __lt__(self, altro: "Versione") -> bool:
        if not isinstance(altro, Versione):
            return NotImplemented
        return self._come_tupla() < altro._come_tupla()

    def __hash__(self) -> int:
        # Se definisci __eq__, devi definire anche __hash__
        # (o Python lo imposta a None rendendoti non-hashable)
        return hash(self._come_tupla())

    def __repr__(self) -> str:
        return f"Versione({self.major}, {self.minor}, {self.patch})"

    def __str__(self) -> str:
        return f"v{self.major}.{self.minor}.{self.patch}"


v1 = Versione(2, 0)
v2 = Versione(1, 9, 5)
v3 = Versione(2, 0)

print(v1 > v2)    # True   — generato da @total_ordering
print(v1 == v3)   # True
print(v1 in {v3}) # True   — usa __hash__ e __eq__
print(sorted([v1, v2, v3]))  # [Versione(1, 9, 5), Versione(2, 0, 0), Versione(2, 0, 0)]
```

**Contratto `__hash__`/`__eq__`:**
- Se `a == b` → `hash(a) == hash(b)` (**obbligatorio**)
- Se si definisce `__eq__` senza `__hash__` → `__hash__` è impostato a `None` (non hashable)
- Gli oggetti mutabili non dovrebbero essere hashable: il valore cambierebbe dopo l'inserimento in un dict/set

### Container protocol

```python
class PilaFinita:
    """Pila (stack) a capacità limitata con supporto ai protocolli Python."""

    def __init__(self, capacita: int):
        self._capacita = capacita
        self._dati: list = []

    def push(self, elemento) -> None:
        if len(self._dati) >= self._capacita:
            raise OverflowError(f"Pila piena (max {self._capacita} elementi)")
        self._dati.append(elemento)

    def pop(self):
        if not self._dati:
            raise IndexError("Pila vuota")
        return self._dati.pop()

    def __len__(self) -> int:
        return len(self._dati)

    def __contains__(self, elemento) -> bool:
        return elemento in self._dati

    def __iter__(self):
        return iter(reversed(self._dati))   # LIFO

    def __getitem__(self, indice: int):
        return self._dati[-(indice + 1)]    # 0 = top della pila

    def __bool__(self) -> bool:
        return bool(self._dati)

    def __repr__(self) -> str:
        return f"PilaFinita(capacita={self._capacita}, dati={self._dati})"


pila = PilaFinita(5)
pila.push(1)
pila.push(2)
pila.push(3)

print(len(pila))        # 3
print(2 in pila)        # True
print(list(pila))       # [3, 2, 1]  — LIFO
print(pila[0])          # 3  — top
print(bool(pila))       # True
```

### Context manager

```python
class GestoreTransazione:
    """Context manager per transazioni con commit/rollback automatico."""

    def __init__(self, connessione):
        self.conn = connessione
        self.salvato = False

    def __enter__(self):
        self.conn.begin()
        return self

    def __exit__(self, tipo_exc, valore_exc, traceback):
        if tipo_exc is not None:
            self.conn.rollback()
            print(f"Rollback: {tipo_exc.__name__}: {valore_exc}")
            return False    # rilancia l'eccezione
        self.conn.commit()
        self.salvato = True
        return True

# with GestoreTransazione(conn) as tx:
#     conn.esegui("INSERT INTO ordini VALUES (...)")
#     conn.esegui("UPDATE magazzino SET qty = qty - 1")
#     # Se qualcosa lancia, rollback automatico
```

### Accesso agli attributi

```python
class ConfigDinamica:
    """Oggetto di configurazione che accetta attributi arbitrari."""

    def __init__(self, **valori_default):
        # Accesso diretto a __dict__ per evitare ricorsione in __setattr__
        object.__setattr__(self, "_dati", dict(valori_default))
        object.__setattr__(self, "_modificati", set())

    def __getattr__(self, nome: str):
        """Chiamato SOLO quando l'attributo non è trovato normalmente."""
        dati = object.__getattribute__(self, "_dati")
        if nome in dati:
            return dati[nome]
        raise AttributeError(f"Configurazione senza chiave '{nome}'")

    def __setattr__(self, nome: str, valore) -> None:
        """Chiamato per OGNI assegnamento."""
        dati = object.__getattribute__(self, "_dati")
        modificati = object.__getattribute__(self, "_modificati")
        dati[nome] = valore
        modificati.add(nome)

    def __repr__(self) -> str:
        dati = object.__getattribute__(self, "_dati")
        return f"ConfigDinamica({dati})"


cfg = ConfigDinamica(host="localhost", porta=8080)
print(cfg.host)    # localhost
cfg.debug = True
print(cfg.debug)   # True
```

---

## B4. La trappola degli attributi di classe mutabili

Questa è una delle trappole più comuni per chi inizia con Python OOP.

```python
# ❌ SBAGLIATO — lista mutabile come attributo di CLASSE
class SquadraRotta:
    giocatori = []     # CONDIVISA tra tutte le istanze!

    def __init__(self, nome: str):
        self.nome = nome

    def aggiungi(self, giocatore: str) -> None:
        self.giocatori.append(giocatore)  # modifica la lista CONDIVISA


roma = SquadraRotta("Roma")
napoli = SquadraRotta("Napoli")

roma.aggiungi("Totti")
napoli.aggiungi("Maradona")

print(roma.giocatori)    # ['Totti', 'Maradona']  ← SORPRESA!
print(napoli.giocatori)  # ['Totti', 'Maradona']  ← stessa lista!
print(roma.giocatori is napoli.giocatori)   # True
```

**Perché succede:** `self.giocatori.append(...)` non crea un nuovo attributo di istanza. Modifica la lista in-place, e quella lista è condivisa tra tutte le istanze come attributo di classe.

```python
# ✅ CORRETTO — lista inizializzata in __init__
class Squadra:
    sport = "calcio"   # OK — stringa immutabile, condivisione intenzionale

    def __init__(self, nome: str):
        self.nome = nome
        self.giocatori = []   # ogni istanza ha la propria lista

    def aggiungi(self, giocatore: str) -> None:
        self.giocatori.append(giocatore)


roma = Squadra("Roma")
napoli = Squadra("Napoli")

roma.aggiungi("Totti")
napoli.aggiungi("Maradona")

print(roma.giocatori)    # ['Totti']
print(napoli.giocatori)  # ['Maradona']
```

**Regola:**
- Attributi di classe **immutabili** (`int`, `str`, `tuple`, `frozenset`) → sicuri da condividere
- Attributi di classe **mutabili** (`list`, `dict`, `set`) → quasi sempre un bug. Inizializza in `__init__`
- Eccezione: contatori o registri **intenzionalmente** condivisi (es. `totale_istanze`)

---

## B5. dataclass: zero boilerplate per classi dati

Il decoratore `@dataclass` (PEP 557, Python 3.7+) genera automaticamente `__init__`, `__repr__` e `__eq__` dalle annotazioni di tipo:

```python
from dataclasses import dataclass, field
from datetime import datetime

# Senza @dataclass — tutto a mano
class ProdottoManuale:
    def __init__(self, nome: str, prezzo: float, tags: list[str] | None = None):
        self.nome = nome
        self.prezzo = prezzo
        self.tags = tags if tags is not None else []

    def __repr__(self):
        return f"ProdottoManuale(nome={self.nome!r}, prezzo={self.prezzo!r}, tags={self.tags!r})"

    def __eq__(self, altro):
        if not isinstance(altro, ProdottoManuale):
            return NotImplemented
        return (self.nome, self.prezzo, self.tags) == (altro.nome, altro.prezzo, altro.tags)

# Con @dataclass — equivalente ma in ~5 righe
@dataclass
class Prodotto:
    nome: str
    prezzo: float
    tags: list[str] = field(default_factory=list)   # mai usare [] come default!
```

### Opzioni avanzate

```python
@dataclass(frozen=True)   # immutabile e hashable
class Coordinata:
    lat: float
    lon: float

c = Coordinata(41.9028, 12.4964)
# c.lat = 0    # FrozenInstanceError!
print(hash(c)) # funziona perché frozen=True genera __hash__


@dataclass(order=True)   # genera <, <=, >, >=
class Priorita:
    livello: int        # confronto basato sull'ordine dei campi
    etichetta: str = ""

p1 = Priorita(1, "bassa")
p2 = Priorita(3, "alta")
print(p1 < p2)   # True


@dataclass(slots=True)   # usa __slots__ (Python 3.10+)
class PuntoVeloce:
    x: float
    y: float


@dataclass(kw_only=True)   # tutti i campi keyword-only (Python 3.10+)
class Configurazione:
    host: str
    porta: int = 8080
    debug: bool = False

# c = Configurazione("localhost")  # TypeError — deve essere kw_only
cfg = Configurazione(host="localhost", debug=True)
```

### `__post_init__` e `InitVar`

```python
from dataclasses import dataclass, field, InitVar
import hashlib

@dataclass
class Utente:
    username: str
    password_hash: str = field(init=False, repr=False)
    password: InitVar[str] = None    # parametro solo per __init__, non diventa attributo
    creato_il: datetime = field(default_factory=datetime.now, init=False)

    def __post_init__(self, password: str) -> None:
        """Chiamato DOPO il __init__ generato — per validazione e campi derivati."""
        if not password or len(password) < 8:
            raise ValueError("Password troppo corta (min 8 caratteri)")
        self.password_hash = hashlib.sha256(password.encode()).hexdigest()


u = Utente(username="anna", password="sicura123")
print(u.username)        # anna
print(u.password_hash)   # sha256 hash
# u.password             # AttributeError — non esiste come attributo
```

### `dataclasses.replace()` per oggetti frozen

```python
from dataclasses import replace

@dataclass(frozen=True)
class Ordine:
    id: int
    stato: str
    importo: float

o1 = Ordine(42, "BOZZA", 150.0)
# Crea nuova istanza con stato modificato, senza toccare o1
o2 = replace(o1, stato="CONFERMATO")
print(o1)   # Ordine(id=42, stato='BOZZA', importo=150.0)
print(o2)   # Ordine(id=42, stato='CONFERMATO', importo=150.0)
```

---

## B6. `__slots__`: memoria ottimizzata

Per default, ogni istanza ha un dizionario `__dict__` che memorizza i suoi attributi. Con `__slots__`, Python sostituisce il dizionario con una struttura a dimensione fissa:

```python
import sys

class Normale:
    def __init__(self, x: float, y: float, z: float):
        self.x = x
        self.y = y
        self.z = z

class ConSlots:
    __slots__ = ("x", "y", "z")

    def __init__(self, x: float, y: float, z: float):
        self.x = x
        self.y = y
        self.z = z


n = Normale(1.0, 2.0, 3.0)
s = ConSlots(1.0, 2.0, 3.0)

print(sys.getsizeof(n) + sys.getsizeof(n.__dict__))   # ~200 bytes
print(sys.getsizeof(s))                                 # ~64 bytes

# Con 1 milione di istanze: ~130 MB di differenza
```

**Trade-off:**
- `__slots__` non ha `__dict__` → non si possono aggiungere attributi dinamicamente
- In gerarchie, ogni sottoclasse deve definire i propri `__slots__` (solo i nuovi attributi)
- Aggiungere `"__weakref__"` agli slot se si usano weak reference

```python
class Base:
    __slots__ = ("x", "y")

class Derivata(Base):
    __slots__ = ("z",)   # solo i nuovi — x, y sono già in Base

    def __init__(self, x, y, z):
        self.x = x   # slot ereditato
        self.y = y   # slot ereditato
        self.z = z   # slot proprio
```

**Quando usare `__slots__`:** migliaia/milioni di istanze, attributi fissi, applicazioni sensibili alla memoria.

---

## B7. Enum: costanti tipizzate

Le enumerazioni rappresentano insiemi fissi di costanti nominali. Sono preferibili a stringhe o interi grezzi perché forniscono type safety e autocompletamento.

```python
from enum import Enum, IntEnum, StrEnum, Flag, auto, unique


class StatoOrdine(Enum):
    BOZZA = "bozza"
    CONFERMATO = "confermato"
    IN_SPEDIZIONE = "in_spedizione"
    CONSEGNATO = "consegnato"
    ANNULLATO = "annullato"

    @classmethod
    def da_stringa(cls, valore: str) -> "StatoOrdine":
        try:
            return cls(valore.lower())
        except ValueError:
            validi = [s.value for s in cls]
            raise ValueError(f"Stato '{valore}' non valido. Validi: {validi}")

    def puo_transitare_a(self, nuovo: "StatoOrdine") -> bool:
        transizioni: dict["StatoOrdine", set["StatoOrdine"]] = {
            StatoOrdine.BOZZA: {StatoOrdine.CONFERMATO, StatoOrdine.ANNULLATO},
            StatoOrdine.CONFERMATO: {StatoOrdine.IN_SPEDIZIONE, StatoOrdine.ANNULLATO},
            StatoOrdine.IN_SPEDIZIONE: {StatoOrdine.CONSEGNATO},
            StatoOrdine.CONSEGNATO: set(),
            StatoOrdine.ANNULLATO: set(),
        }
        return nuovo in transizioni[self]


s = StatoOrdine.BOZZA
print(s.name)    # BOZZA
print(s.value)   # bozza
print(s.puo_transitare_a(StatoOrdine.CONFERMATO))  # True
print(s.puo_transitare_a(StatoOrdine.CONSEGNATO))  # False
```

```python
# IntEnum — compatibile con int
class Priorita(IntEnum):
    BASSA = 1
    MEDIA = 2
    ALTA = 3
    CRITICA = 4

print(Priorita.ALTA > 2)              # True
print(sorted([Priorita.ALTA, Priorita.BASSA]))  # [<Priorita.BASSA: 1>, ...]

# StrEnum — compatibile con str (Python 3.11+)
class Ruolo(StrEnum):
    ADMIN = "admin"
    UTENTE = "utente"
    OSPITE = "ospite"

print(f"Ruolo: {Ruolo.ADMIN}")  # "Ruolo: admin"
```

```python
# Flag — combinazioni con operatori bitwise
class Permesso(Flag):
    NESSUNO = 0
    LETTURA = auto()
    SCRITTURA = auto()
    ESECUZIONE = auto()
    ADMIN = LETTURA | SCRITTURA | ESECUZIONE

utente = Permesso.LETTURA | Permesso.SCRITTURA
print(Permesso.LETTURA in utente)     # True
print(Permesso.ESECUZIONE in utente)  # False
print(Permesso.ADMIN in Permesso.ADMIN)  # True
```

---

## B8. Abstract Base Classes (ABC)

Le ABC definiscono un contratto che le sottoclassi **devono** rispettare. Se una sottoclasse non implementa tutti i metodi astratti, non può essere istanziata.

```python
from abc import ABC, abstractmethod


class FormaGeometrica(ABC):
    """Contratto: ogni forma deve calcolare area e perimetro."""

    @abstractmethod
    def area(self) -> float:
        """Calcola l'area della forma."""
        ...

    @abstractmethod
    def perimetro(self) -> float:
        """Calcola il perimetro della forma."""
        ...

    def descrizione(self) -> str:
        """Metodo concreto — ereditato da tutte le sottoclassi."""
        return (
            f"{type(self).__name__}: "
            f"area={self.area():.4f}, perimetro={self.perimetro():.4f}"
        )


# forma = FormaGeometrica()   # TypeError — non si può istanziare una ABC


class Cerchio(FormaGeometrica):
    def __init__(self, raggio: float):
        self.raggio = raggio

    def area(self) -> float:
        import math
        return math.pi * self.raggio ** 2

    def perimetro(self) -> float:
        import math
        return 2 * math.pi * self.raggio


class Rettangolo(FormaGeometrica):
    def __init__(self, base: float, altezza: float):
        self.base = base
        self.altezza = altezza

    def area(self) -> float:
        return self.base * self.altezza

    def perimetro(self) -> float:
        return 2 * (self.base + self.altezza)


forme = [Cerchio(5), Rettangolo(4, 6)]
for f in forme:
    print(f.descrizione())
# Cerchio: area=78.5398, perimetro=31.4159
# Rettangolo: area=24.0000, perimetro=20.0000
```

### `collections.abc` — ABC della libreria standard

Estendere le ABC di `collections.abc` è il modo raccomandato per implementare tipi container personalizzati:

```python
from collections.abc import MutableSequence


class SerieStorica(MutableSequence):
    """Sequenza mutabile di misurazioni numeriche."""

    def __init__(self, valori: list[float] | None = None):
        self._dati: list[float] = list(valori or [])

    # Metodi ASTRATTI obbligatori di MutableSequence
    def __getitem__(self, indice):
        return self._dati[indice]

    def __setitem__(self, indice, valore):
        if not isinstance(valore, (int, float)):
            raise TypeError("Solo valori numerici")
        self._dati[indice] = float(valore)

    def __delitem__(self, indice):
        del self._dati[indice]

    def __len__(self) -> int:
        return len(self._dati)

    def insert(self, indice: int, valore: float) -> None:
        self._dati.insert(indice, float(valore))

    # MutableSequence fornisce GRATIS: append, extend, count, index,
    # remove, pop, __contains__, __iter__, __reversed__, __iadd__, sort...

    def media(self) -> float:
        if not self._dati:
            raise ValueError("Serie vuota")
        return sum(self._dati) / len(self._dati)


s = SerieStorica([10.5, 11.2, 9.8, 12.1])
s.append(13.0)             # gratis da MutableSequence
print(len(s))              # 5
print(s.media())           # 11.32
print(10.5 in s)           # True  — __contains__ gratis
print(list(reversed(s)))   # reversed gratis
```

---

## B9. Protocol: duck typing statico (PEP 544)

I `Protocol` (Python 3.8+) definiscono interfacce **strutturali**: una classe soddisfa un protocollo se implementa i metodi richiesti, **senza ereditarietà esplicita**.

```python
from typing import Protocol, runtime_checkable


@runtime_checkable
class Serializzabile(Protocol):
    def to_bytes(self) -> bytes: ...
    def to_json(self) -> str: ...


class MessaggioEmail:
    def __init__(self, oggetto: str, corpo: str):
        self.oggetto = oggetto
        self.corpo = corpo

    def to_bytes(self) -> bytes:
        return f"{self.oggetto}\n{self.corpo}".encode()

    def to_json(self) -> str:
        import json
        return json.dumps({"oggetto": self.oggetto, "corpo": self.corpo})


class EventoLog:
    def __init__(self, livello: str, messaggio: str):
        self.livello = livello
        self.messaggio = messaggio

    def to_bytes(self) -> bytes:
        return f"[{self.livello}] {self.messaggio}".encode()

    def to_json(self) -> str:
        import json
        return json.dumps({"livello": self.livello, "messaggio": self.messaggio})


def invia_a_coda(elemento: Serializzabile) -> None:
    """Funziona con qualsiasi oggetto che soddisfi il protocollo."""
    payload = elemento.to_bytes()
    print(f"Invio {len(payload)} bytes: {payload[:50]}")


# Nessuna ereditarietà — funziona tramite structural subtyping
invia_a_coda(MessaggioEmail("Test", "Corpo del messaggio"))
invia_a_coda(EventoLog("ERROR", "Connessione persa"))

# Con @runtime_checkable, isinstance() funziona
print(isinstance(MessaggioEmail("x", "y"), Serializzabile))   # True
print(isinstance(42, Serializzabile))                           # False
```

### ABC vs Protocol — quando usare quale

| Criterio | ABC | Protocol |
|---|---|---|
| Tipo di subtyping | Nominale (ereditarietà esplicita) | Strutturale (implementazione implicita) |
| Metodi concreti ereditabili | Sì | No |
| Compatibile con classi terze | Tramite `register()` | Automatico |
| Verifica statica (mypy) | Sì | Sì |
| Caso d'uso tipico | Framework, API con contratto forte | Librerie, type hints, duck typing |

**Regola pratica:** se la classe base deve fornire implementazioni parziali (metodi concreti), usa ABC. Se serve solo verificare la compatibilità strutturale, usa Protocol.

---

# Parte C — Esercizi Pratici Guidati

---

## C1. Esercizi progressivi con soluzione

### Esercizio 1 — Classe base con property

**Obiettivo:** creare una classe `Rettangolo` con property validate per `base` e `altezza` (devono essere > 0).

```python
# Implementa qui
from dataclasses import dataclass


class Rettangolo:
    def __init__(self, base: float, altezza: float):
        self.base = base          # passa per il setter
        self.altezza = altezza

    @property
    def base(self) -> float:
        return self._base

    @base.setter
    def base(self, valore: float) -> None:
        if valore <= 0:
            raise ValueError(f"base deve essere > 0, ricevuto {valore}")
        self._base = float(valore)

    @property
    def altezza(self) -> float:
        return self._altezza

    @altezza.setter
    def altezza(self, valore: float) -> None:
        if valore <= 0:
            raise ValueError(f"altezza deve essere > 0, ricevuto {valore}")
        self._altezza = float(valore)

    @property
    def area(self) -> float:
        return self._base * self._altezza

    @property
    def perimetro(self) -> float:
        return 2 * (self._base + self._altezza)

    def __repr__(self) -> str:
        return f"Rettangolo(base={self._base}, altezza={self._altezza})"


# Test
r = Rettangolo(5, 3)
print(r.area)       # 15.0
print(r.perimetro)  # 16.0
r.base = 10
print(r.area)       # 30.0
try:
    r.base = -1
except ValueError as e:
    print(e)        # base deve essere > 0, ricevuto -1
```

### Esercizio 2 — Ereditarietà e polimorfismo

**Obiettivo:** implementare una gerarchia di conti bancari.

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Transazione:
    tipo: str           # "deposito" o "prelievo"
    importo: float
    timestamp: datetime = field(default_factory=datetime.now)

    def __repr__(self) -> str:
        segno = "+" if self.tipo == "deposito" else "-"
        return f"{self.timestamp:%H:%M:%S} {segno}€{self.importo:.2f}"


class ContoBase(ABC):
    def __init__(self, numero: str, titolare: str, saldo_iniziale: float = 0.0):
        self.numero = numero
        self.titolare = titolare
        self._saldo = float(saldo_iniziale)
        self._storico: list[Transazione] = []

    @property
    def saldo(self) -> float:
        return self._saldo

    def deposita(self, importo: float) -> None:
        if importo <= 0:
            raise ValueError("Importo deve essere positivo")
        self._saldo += importo
        self._storico.append(Transazione("deposito", importo))

    @abstractmethod
    def preleva(self, importo: float) -> None:
        """Le sottoclassi implementano la logica di prelievo."""
        ...

    def estratto_conto(self) -> str:
        righe = [f"Conto {self.numero} — {self.titolare}"]
        righe.extend(str(t) for t in self._storico[-5:])
        righe.append(f"Saldo: €{self._saldo:.2f}")
        return "\n".join(righe)

    def __repr__(self) -> str:
        return f"{type(self).__name__}(numero={self.numero!r}, saldo={self._saldo:.2f})"


class ContoCorrente(ContoBase):
    """Conto con scoperto autorizzato."""

    def __init__(self, numero: str, titolare: str, saldo_iniziale: float = 0.0,
                 scoperto_max: float = 500.0):
        super().__init__(numero, titolare, saldo_iniziale)
        self.scoperto_max = scoperto_max

    def preleva(self, importo: float) -> None:
        if importo <= 0:
            raise ValueError("Importo deve essere positivo")
        if self._saldo - importo < -self.scoperto_max:
            raise ValueError(
                f"Prelievo non autorizzato. Scoperto max: €{self.scoperto_max}"
            )
        self._saldo -= importo
        self._storico.append(Transazione("prelievo", importo))


class ContoRisparmio(ContoBase):
    """Conto senza scoperto, con tasso di interesse mensile."""

    def __init__(self, numero: str, titolare: str, saldo_iniziale: float = 0.0,
                 tasso_mensile: float = 0.002):
        super().__init__(numero, titolare, saldo_iniziale)
        self.tasso_mensile = tasso_mensile

    def preleva(self, importo: float) -> None:
        if importo <= 0:
            raise ValueError("Importo deve essere positivo")
        if importo > self._saldo:
            raise ValueError(f"Fondi insufficienti: disponibile €{self._saldo:.2f}")
        self._saldo -= importo
        self._storico.append(Transazione("prelievo", importo))

    def applica_interessi(self) -> float:
        interessi = self._saldo * self.tasso_mensile
        self.deposita(interessi)
        return interessi


# Test
cc = ContoCorrente("CC-001", "Anna", 1000.0)
cr = ContoRisparmio("CR-001", "Anna", 5000.0, tasso_mensile=0.003)

cc.deposita(500)
cc.preleva(1800)   # usa lo scoperto
print(cc.estratto_conto())

interessi = cr.applica_interessi()
print(f"Interessi mensili: €{interessi:.2f}")
print(cr.estratto_conto())
```

### Esercizio 3 — dataclass con pattern matching

```python
from dataclasses import dataclass
from typing import Union

@dataclass
class Numero:
    valore: float

@dataclass
class Somma:
    sinistra: "Espressione"
    destra: "Espressione"

@dataclass
class Prodotto:
    sinistra: "Espressione"
    destra: "Espressione"

@dataclass
class Negazione:
    operando: "Espressione"

Espressione = Union[Numero, Somma, Prodotto, Negazione]


def valuta(expr: Espressione) -> float:
    match expr:
        case Numero(valore=v):
            return v
        case Somma(sinistra=s, destra=d):
            return valuta(s) + valuta(d)
        case Prodotto(sinistra=s, destra=d):
            return valuta(s) * valuta(d)
        case Negazione(operando=o):
            return -valuta(o)
        case _:
            raise TypeError(f"Espressione sconosciuta: {type(expr)}")


# (2 + 3) * -4 = -20
expr = Prodotto(
    Somma(Numero(2), Numero(3)),
    Negazione(Numero(4))
)
print(valuta(expr))   # -20.0
```

---

## C2. Mini-progetto: sistema di gestione biblioteca

Un sistema completo che integra tutti i concetti della Parte A e B.

```python
"""
Sistema di gestione biblioteca — mini-progetto OOP.

Esegui con:
    python biblioteca.py

Requisiti: Python 3.12+, nessuna dipendenza esterna.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum, auto
from typing import Protocol


# ── Enum ──────────────────────────────────────────────────────────

class GenereLibro(Enum):
    NARRATIVA = auto()
    SAGGISTICA = auto()
    TECNOLOGIA = auto()
    SCIENZE = auto()
    STORIA = auto()
    ALTRO = auto()


class StatoPrestito(Enum):
    ATTIVO = "attivo"
    RESTITUITO = "restituito"
    IN_RITARDO = "in_ritardo"


# ── Dataclass ─────────────────────────────────────────────────────

@dataclass
class Libro:
    isbn: str
    titolo: str
    autore: str
    genere: GenereLibro
    anno: int
    disponibile: bool = True

    def __post_init__(self) -> None:
        if not self.isbn or len(self.isbn) not in (10, 13):
            raise ValueError(f"ISBN non valido: {self.isbn!r}")
        if self.anno < 1450 or self.anno > date.today().year:
            raise ValueError(f"Anno non valido: {self.anno}")

    def __str__(self) -> str:
        stato = "disponibile" if self.disponibile else "in prestito"
        return f'"{self.titolo}" di {self.autore} [{self.genere.name}] — {stato}'


@dataclass
class Prestito:
    libro: Libro
    utente: "UtenteBase"
    data_inizio: date = field(default_factory=date.today)
    durata_giorni: int = 30
    data_restituzione: date | None = None

    @property
    def data_scadenza(self) -> date:
        return self.data_inizio + timedelta(days=self.durata_giorni)

    @property
    def stato(self) -> StatoPrestito:
        if self.data_restituzione is not None:
            return StatoPrestito.RESTITUITO
        if date.today() > self.data_scadenza:
            return StatoPrestito.IN_RITARDO
        return StatoPrestito.ATTIVO

    @property
    def giorni_restanti(self) -> int:
        if self.stato == StatoPrestito.RESTITUITO:
            return 0
        return (self.data_scadenza - date.today()).days

    def restituisci(self) -> None:
        if self.stato == StatoPrestito.RESTITUITO:
            raise ValueError("Libro già restituito")
        self.data_restituzione = date.today()
        self.libro.disponibile = True

    def __str__(self) -> str:
        return (
            f"Prestito '{self.libro.titolo}' → {self.utente.nome} "
            f"[{self.stato.value}] scade {self.data_scadenza}"
        )


# ── Protocol ──────────────────────────────────────────────────────

class NotificatoreProtocol(Protocol):
    def invia(self, destinatario: str, oggetto: str, corpo: str) -> None: ...


class ConsolaNotificatore:
    def invia(self, destinatario: str, oggetto: str, corpo: str) -> None:
        print(f"[NOTIFICA → {destinatario}] {oggetto}: {corpo}")


# ── ABC per utenti ────────────────────────────────────────────────

class UtenteBase(ABC):
    def __init__(self, id_utente: str, nome: str, email: str):
        self.id_utente = id_utente
        self.nome = nome
        self.email = email
        self._prestiti_attivi: list[Prestito] = []

    @property
    def num_prestiti_attivi(self) -> int:
        return sum(
            1 for p in self._prestiti_attivi
            if p.stato != StatoPrestito.RESTITUITO
        )

    @property
    @abstractmethod
    def limite_prestiti(self) -> int:
        """Numero massimo di libri in prestito contemporaneamente."""
        ...

    def puo_prendere_in_prestito(self) -> bool:
        return self.num_prestiti_attivi < self.limite_prestiti

    def registra_prestito(self, prestito: Prestito) -> None:
        self._prestiti_attivi.append(prestito)

    def __repr__(self) -> str:
        return f"{type(self).__name__}(id={self.id_utente!r}, nome={self.nome!r})"


class UtenteStandard(UtenteBase):
    @property
    def limite_prestiti(self) -> int:
        return 3


class UtenteStudente(UtenteBase):
    def __init__(self, id_utente: str, nome: str, email: str, istituto: str):
        super().__init__(id_utente, nome, email)
        self.istituto = istituto

    @property
    def limite_prestiti(self) -> int:
        return 5


class UtenteProfessore(UtenteBase):
    @property
    def limite_prestiti(self) -> int:
        return 10


# ── Classe principale Biblioteca ──────────────────────────────────

class Biblioteca:
    def __init__(self, nome: str, notificatore: NotificatoreProtocol | None = None):
        self.nome = nome
        self._catalogo: dict[str, Libro] = {}         # isbn → Libro
        self._utenti: dict[str, UtenteBase] = {}       # id_utente → UtenteBase
        self._prestiti: list[Prestito] = []
        self._notificatore = notificatore or ConsolaNotificatore()

    # ── Gestione catalogo ─────────────────────────────────────────

    def aggiungi_libro(self, libro: Libro) -> None:
        if libro.isbn in self._catalogo:
            raise ValueError(f"ISBN {libro.isbn} già presente nel catalogo")
        self._catalogo[libro.isbn] = libro

    def cerca_per_autore(self, autore: str) -> list[Libro]:
        termine = autore.lower()
        return [l for l in self._catalogo.values() if termine in l.autore.lower()]

    def cerca_per_genere(self, genere: GenereLibro) -> list[Libro]:
        return [l for l in self._catalogo.values() if l.genere == genere]

    def libri_disponibili(self) -> list[Libro]:
        return [l for l in self._catalogo.values() if l.disponibile]

    # ── Gestione utenti ───────────────────────────────────────────

    def registra_utente(self, utente: UtenteBase) -> None:
        if utente.id_utente in self._utenti:
            raise ValueError(f"Utente {utente.id_utente} già registrato")
        self._utenti[utente.id_utente] = utente

    # ── Prestiti ──────────────────────────────────────────────────

    def presta(self, isbn: str, id_utente: str, durata: int = 30) -> Prestito:
        libro = self._catalogo.get(isbn)
        if libro is None:
            raise KeyError(f"ISBN {isbn} non trovato")
        if not libro.disponibile:
            raise ValueError(f'"{libro.titolo}" non è disponibile')

        utente = self._utenti.get(id_utente)
        if utente is None:
            raise KeyError(f"Utente {id_utente} non trovato")
        if not utente.puo_prendere_in_prestito():
            raise ValueError(
                f"{utente.nome} ha raggiunto il limite ({utente.limite_prestiti} libri)"
            )

        libro.disponibile = False
        prestito = Prestito(libro, utente, durata_giorni=durata)
        self._prestiti.append(prestito)
        utente.registra_prestito(prestito)

        self._notificatore.invia(
            utente.email,
            "Prestito confermato",
            f'Hai preso in prestito "{libro.titolo}". Scade: {prestito.data_scadenza}'
        )
        return prestito

    def restituisci(self, prestito: Prestito) -> None:
        prestito.restituisci()
        self._notificatore.invia(
            prestito.utente.email,
            "Restituzione registrata",
            f'"{prestito.libro.titolo}" restituito. Grazie!'
        )

    def prestiti_in_ritardo(self) -> list[Prestito]:
        return [p for p in self._prestiti if p.stato == StatoPrestito.IN_RITARDO]

    def report(self) -> str:
        attivi = [p for p in self._prestiti if p.stato == StatoPrestito.ATTIVO]
        in_ritardo = self.prestiti_in_ritardo()
        return (
            f"═══ {self.nome} ═══\n"
            f"Catalogo: {len(self._catalogo)} libri "
            f"({len(self.libri_disponibili())} disponibili)\n"
            f"Utenti: {len(self._utenti)}\n"
            f"Prestiti attivi: {len(attivi)}\n"
            f"In ritardo: {len(in_ritardo)}"
        )


# ── Entry point ────────────────────────────────────────────────────

def main() -> None:
    bib = Biblioteca("Biblioteca Comunale")

    # Popola catalogo
    libri = [
        Libro("9780132350884", "Clean Code", "Robert C. Martin", GenereLibro.TECNOLOGIA, 2008),
        Libro("9780201633610", "Design Patterns", "Gang of Four", GenereLibro.TECNOLOGIA, 1994),
        Libro("9788807902499", "Il Gattopardo", "Giuseppe Tomasi di Lampedusa", GenereLibro.NARRATIVA, 1958),
        Libro("9788804667001", "Sapiens", "Yuval Noah Harari", GenereLibro.SAGGISTICA, 2011),
        Libro("9780062316097", "The Martian", "Andy Weir", GenereLibro.NARRATIVA, 2011),
    ]
    for libro in libri:
        bib.aggiungi_libro(libro)

    # Registra utenti
    anna = UtenteStudente("U001", "Anna Rossi", "anna@uni.it", "Politecnico")
    marco = UtenteProfessore("U002", "Prof. Marco Bianchi", "marco@uni.it")
    bib.registra_utente(anna)
    bib.registra_utente(marco)

    # Prestiti
    p1 = bib.presta("9780132350884", "U001")
    p2 = bib.presta("9788804667001", "U002")

    print("\n" + bib.report())
    print()

    # Cerca
    tech = bib.cerca_per_genere(GenereLibro.TECNOLOGIA)
    print(f"Libri di tecnologia: {[l.titolo for l in tech]}")

    # Restituzione
    bib.restituisci(p1)
    print(f"\nDopo restituzione:")
    print(bib.report())


if __name__ == "__main__":
    main()
```

**Output atteso:**
```
[NOTIFICA → anna@uni.it] Prestito confermato: Hai preso in prestito "Clean Code". Scade: 2026-08-15
[NOTIFICA → marco@uni.it] Prestito confermato: Hai preso in prestito "Sapiens". Scade: 2026-08-15

═══ Biblioteca Comunale ═══
Catalogo: 5 libri (3 disponibili)
Utenti: 2
Prestiti attivi: 2
In ritardo: 0

Libri di tecnologia: ['Clean Code', 'Design Patterns']
[NOTIFICA → anna@uni.it] Restituzione registrata: "Clean Code" restituito. Grazie!

Dopo restituzione:
═══ Biblioteca Comunale ═══
Catalogo: 5 libri (4 disponibili)
Utenti: 2
Prestiti attivi: 1
In ritardo: 0
```

---

# Parte D — Approfondimento per Esperti

---

## D1. Protocollo Descriptor

> **Analogia:** Il descriptor è come un intermediario doganale: ogni volta che qualcuno vuole accedere a un "pacco" (attributo), il descriptor intercetta la richiesta, la verifica, la trasforma se necessario, e poi la consegna. La `@property` è semplicemente un descriptor pre-confezionato per i casi più comuni.

Un descriptor è qualsiasi oggetto che implementa `__get__`, `__set__` o `__delete__`. Quando è assegnato come attributo di **classe** (non di istanza), Python lo invoca automaticamente durante l'accesso agli attributi.

```python
class MioDescriptor:
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self          # accesso dalla classe
        return obj.__dict__.get("_valore_desc", None)

    def __set__(self, obj, valore):
        print(f"__set__ chiamato con {valore!r}")
        obj.__dict__["_valore_desc"] = valore

    def __delete__(self, obj):
        obj.__dict__.pop("_valore_desc", None)


class MiaClasse:
    attr = MioDescriptor()   # deve essere attributo di CLASSE, non di istanza


m = MiaClasse()
m.attr = 42         # chiama MioDescriptor.__set__
print(m.attr)       # chiama MioDescriptor.__get__  → 42
del m.attr          # chiama MioDescriptor.__delete__
```

### Data descriptor vs non-data descriptor

- **Data descriptor** (definisce `__set__` o `__delete__`): ha **priorità** su `__dict__` dell'istanza
- **Non-data descriptor** (solo `__get__`): `__dict__` dell'istanza ha **priorità** su di esso

Ordine di risoluzione degli attributi:
1. Data descriptor della classe (MRO)
2. `__dict__` dell'istanza
3. Non-data descriptor della classe

Le funzioni Python sono non-data descriptor: il loro `__get__` produce il *bound method* che passa automaticamente `self`.

### Descriptor riutilizzabile con `__set_name__`

Il pattern più potente: un descriptor che sa il proprio nome grazie a `__set_name__` (PEP 487):

```python
class Campo:
    """Descriptor generico per validazione di attributi."""

    def __init__(self, tipo: type, *, minimo=None, massimo=None, obbligatorio: bool = True):
        self.tipo = tipo
        self.minimo = minimo
        self.massimo = massimo
        self.obbligatorio = obbligatorio

    def __set_name__(self, owner, name: str) -> None:
        """Chiamato alla creazione della classe — fornisce il nome dell'attributo."""
        self.nome_pubblico = name
        self.nome_storage = f"_campo_{name}"

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return getattr(obj, self.nome_storage, None)

    def __set__(self, obj, valore) -> None:
        if valore is None and self.obbligatorio:
            raise ValueError(f"{self.nome_pubblico!r} è obbligatorio")
        if valore is not None:
            if not isinstance(valore, self.tipo):
                raise TypeError(
                    f"{self.nome_pubblico!r} deve essere {self.tipo.__name__}, "
                    f"ricevuto {type(valore).__name__}"
                )
            if self.minimo is not None and valore < self.minimo:
                raise ValueError(f"{self.nome_pubblico!r} deve essere >= {self.minimo}")
            if self.massimo is not None and valore > self.massimo:
                raise ValueError(f"{self.nome_pubblico!r} deve essere <= {self.massimo}")
        setattr(obj, self.nome_storage, valore)

    def __delete__(self, obj) -> None:
        if hasattr(obj, self.nome_storage):
            delattr(obj, self.nome_storage)


class Prodotto:
    nome = Campo(str)
    prezzo = Campo(float, minimo=0.0)
    quantita = Campo(int, minimo=0, massimo=100_000)
    sconto = Campo(float, minimo=0.0, massimo=100.0, obbligatorio=False)

    def __init__(self, nome: str, prezzo: float, quantita: int, sconto: float = 0.0):
        self.nome = nome
        self.prezzo = prezzo
        self.quantita = quantita
        self.sconto = sconto

    def prezzo_scontato(self) -> float:
        return self.prezzo * (1 - (self.sconto or 0) / 100)

    def __repr__(self) -> str:
        return f"Prodotto(nome={self.nome!r}, prezzo={self.prezzo}, quantita={self.quantita})"


p = Prodotto("Laptop", 999.0, 10, sconto=15.0)
print(p.prezzo_scontato())   # 849.15

try:
    p.prezzo = -10
except ValueError as e:
    print(e)   # 'prezzo' deve essere >= 0.0

try:
    p.nome = 123
except TypeError as e:
    print(e)   # 'nome' deve essere str, ricevuto int
```

**Quando usare i descriptor vs `@property`:**
- `@property` → logica di validazione su **un singolo attributo** di una classe
- Descriptor → stessa logica applicata a **molti attributi** o **molte classi** diverse

---

## D2. Metaclassi e `__init_subclass__`

> **Analogia:** Se una classe è il progetto di un edificio, la metaclasse è il regolamento edilizio comunale che stabilisce le regole per _come_ si possono fare i progetti. Normalmente non si scrive regolamenti edilizi — si costruiscono edifici. Ma i progettisti di framework ne hanno bisogno.

### `type` come metaclasse predefinita

In Python, le classi stesse sono oggetti — istanze della metaclasse `type`:

```python
print(type(int))     # <class 'type'>
print(type(list))    # <class 'type'>
print(type(type))    # <class 'type'>   — type è istanza di sé stessa!
```

`type()` con tre argomenti crea classi dinamicamente:

```python
# Equivalente a: class Punto: x = 0; y = 0
Punto = type("Punto", (), {"x": 0, "y": 0})
p = Punto()
p.x = 5
print(p.x)   # 5
```

### `__init_subclass__` — l'alternativa leggera alle metaclassi (PEP 487)

Nella stragrande maggioranza dei casi, `__init_subclass__` sostituisce le metaclassi senza la loro complessità:

```python
class Plugin:
    """Sistema di plugin con auto-registrazione."""
    _registro: dict[str, type["Plugin"]] = {}

    def __init_subclass__(cls, *, nome: str = "", **kwargs) -> None:
        """Chiamato OGNI VOLTA che viene definita una sottoclasse di Plugin."""
        super().__init_subclass__(**kwargs)
        chiave = nome or cls.__name__
        Plugin._registro[chiave] = cls
        print(f"Plugin registrato: {chiave!r} → {cls.__name__}")

    @classmethod
    def crea(cls, nome: str, **kwargs) -> "Plugin":
        classe = cls._registro.get(nome)
        if classe is None:
            disponibili = list(cls._registro.keys())
            raise ValueError(f"Plugin {nome!r} sconosciuto. Disponibili: {disponibili}")
        return classe(**kwargs)

    def esegui(self) -> str:
        raise NotImplementedError


class PluginCSV(Plugin, nome="csv"):
    def __init__(self, separatore: str = ","):
        self.separatore = separatore

    def esegui(self) -> str:
        return f"Parsing CSV con separatore {self.separatore!r}"


class PluginJSON(Plugin, nome="json"):
    def esegui(self) -> str:
        return "Parsing JSON"


class PluginXML(Plugin):   # nome di default = "PluginXML"
    def esegui(self) -> str:
        return "Parsing XML"


p = Plugin.crea("csv", separatore=";")
print(p.esegui())   # Parsing CSV con separatore ';'
print(Plugin._registro.keys())   # dict_keys(['csv', 'json', 'PluginXML'])
```

### Metaclasse personalizzata

Usa le metaclassi **solo** quando `__init_subclass__` non basta — ad esempio per modificare il namespace della classe durante la creazione:

```python
class ValidazioneContrattoMeta(type):
    """Metaclasse che verifica i campi obbligatori a tempo di definizione."""

    CAMPI_OBBLIGATORI = {"nome_tabella", "chiave_primaria"}

    def __new__(mcs, nome: str, basi: tuple, namespace: dict):
        cls = super().__new__(mcs, nome, basi, namespace)

        # Verifica solo le classi concrete (non la classe base stessa)
        if basi and not namespace.get("__abstract__", False):
            mancanti = mcs.CAMPI_OBBLIGATORI - set(namespace.keys())
            if mancanti:
                raise TypeError(
                    f"La classe {nome!r} deve definire: {sorted(mancanti)}"
                )
        return cls


class Modello(metaclass=ValidazioneContrattoMeta):
    __abstract__ = True   # esclusa dalla verifica

    def salva(self) -> None:
        print(f"INSERT INTO {self.nome_tabella} ...")


class Utente(Modello):
    nome_tabella = "utenti"
    chiave_primaria = "id"

    def __init__(self, id: int, nome: str):
        self.id = id
        self.nome = nome


# class Rotto(Modello):   # TypeError — mancano nome_tabella e chiave_primaria
#     pass

u = Utente(1, "Anna")
u.salva()   # INSERT INTO utenti ...
```

**Linea guida:** preferisci sempre `__init_subclass__` alla metaclasse. Usa le metaclassi solo per:
- Modificare il namespace della classe durante la creazione
- Framework ORM o framework di test che richiedono controllo profondo sulla creazione delle classi
- Conflitti tra metaclassi di librerie diverse

---

## D3. Design Pattern avanzati in Python OOP

### Strategy con Protocol

```python
from typing import Protocol


class StrategiaSconto(Protocol):
    def calcola(self, prezzo: float, quantita: int) -> float: ...


class ScontoPercentuale:
    def __init__(self, percentuale: float):
        self.percentuale = percentuale

    def calcola(self, prezzo: float, quantita: int) -> float:
        return prezzo * quantita * (1 - self.percentuale / 100)


class ScontoVolume:
    """Sconto progressivo in base alla quantità."""
    FASCE = [(100, 0.15), (50, 0.10), (20, 0.05), (0, 0.0)]

    def calcola(self, prezzo: float, quantita: int) -> float:
        for soglia, sconto in self.FASCE:
            if quantita >= soglia:
                return prezzo * quantita * (1 - sconto)
        return prezzo * quantita


class ScontoFedelta:
    def __init__(self, anni_cliente: int):
        self.anni = anni_cliente

    def calcola(self, prezzo: float, quantita: int) -> float:
        sconto = min(self.anni * 2, 25) / 100
        return prezzo * quantita * (1 - sconto)


class Ordine:
    def __init__(self, strategia: StrategiaSconto):
        self._strategia = strategia
        self._righe: list[tuple[str, float, int]] = []

    def aggiungi(self, prodotto: str, prezzo: float, quantita: int) -> None:
        self._righe.append((prodotto, prezzo, quantita))

    @property
    def totale(self) -> float:
        return sum(
            self._strategia.calcola(prezzo, qty)
            for _, prezzo, qty in self._righe
        )

    def cambia_strategia(self, nuova: StrategiaSconto) -> None:
        self._strategia = nuova


ordine = Ordine(ScontoVolume())
ordine.aggiungi("Prodotto A", 10.0, 60)
print(f"Totale con sconto volume: €{ordine.totale:.2f}")   # €540.00 (10% su 60 unità)

ordine.cambia_strategia(ScontoFedelta(anni_cliente=5))
print(f"Totale con sconto fedeltà: €{ordine.totale:.2f}")  # €540.00 (10% su 5 anni)
```

### Registry Pattern con `__init_subclass__`

Visto in D2. Ecco un'applicazione concreta per serializzatori:

```python
import json
from typing import Any


class Serializzatore:
    _formati: dict[str, type["Serializzatore"]] = {}

    def __init_subclass__(cls, *, formato: str, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        Serializzatore._formati[formato] = cls

    @classmethod
    def per_formato(cls, formato: str) -> "Serializzatore":
        if formato not in cls._formati:
            raise ValueError(f"Formato non supportato: {formato!r}")
        return cls._formati[formato]()

    def serializza(self, dati: Any) -> str:
        raise NotImplementedError

    def deserializza(self, testo: str) -> Any:
        raise NotImplementedError


class SerializzatoreJSON(Serializzatore, formato="json"):
    def serializza(self, dati: Any) -> str:
        return json.dumps(dati, ensure_ascii=False, indent=2)

    def deserializza(self, testo: str) -> Any:
        return json.loads(testo)


class SerializzatoreCSV(Serializzatore, formato="csv"):
    def serializza(self, dati: list[dict]) -> str:
        if not dati:
            return ""
        intestazioni = list(dati[0].keys())
        righe = [",".join(intestazioni)]
        for riga in dati:
            righe.append(",".join(str(riga.get(h, "")) for h in intestazioni))
        return "\n".join(righe)

    def deserializza(self, testo: str) -> list[dict]:
        righe = testo.strip().split("\n")
        intestazioni = righe[0].split(",")
        return [dict(zip(intestazioni, r.split(","))) for r in righe[1:]]


# Uso disaccoppiato dal formato specifico
s = Serializzatore.per_formato("json")
dati = [{"nome": "Anna", "eta": 30}, {"nome": "Marco", "eta": 25}]
print(s.serializza(dati))
```

### Observer Pattern con weak reference

```python
import weakref
from typing import Any


class EventBus:
    """Bus di eventi con weak reference — evita memory leak."""

    def __init__(self):
        self._ascoltatori: dict[str, list[weakref.ref]] = {}

    def registra(self, evento: str, callback) -> None:
        if evento not in self._ascoltatori:
            self._ascoltatori[evento] = []
        ref = weakref.ref(callback.__self__ if hasattr(callback, "__self__") else callback)
        self._ascoltatori[evento].append(ref)

    def emetti(self, evento: str, **dati: Any) -> None:
        for ref in list(self._ascoltatori.get(evento, [])):
            callback = ref()
            if callback is not None:
                callback(**dati)
            else:
                # Rimuovi i ref morti
                self._ascoltatori[evento].remove(ref)


class Logger:
    def on_ordine_creato(self, **dati: Any) -> None:
        print(f"[LOG] Ordine creato: {dati}")

class Notificatore:
    def on_ordine_creato(self, **dati: Any) -> None:
        print(f"[EMAIL] Conferma ordine #{dati.get('id')} a {dati.get('email')}")


bus = EventBus()
logger = Logger()
notif = Notificatore()

bus.registra("ordine_creato", logger.on_ordine_creato)
bus.registra("ordine_creato", notif.on_ordine_creato)

bus.emetti("ordine_creato", id=42, email="cliente@example.com", importo=150.0)
# [LOG] Ordine creato: {'id': 42, 'email': '...', 'importo': 150.0}
# [EMAIL] Conferma ordine #42 a cliente@example.com
```

### State Pattern con Enum e transizioni validate

```python
from dataclasses import dataclass, field
from enum import Enum, auto


class StatoDocumento(Enum):
    BOZZA = auto()
    IN_REVISIONE = auto()
    APPROVATO = auto()
    PUBBLICATO = auto()
    ARCHIVIATO = auto()


TRANSIZIONI: dict[StatoDocumento, set[StatoDocumento]] = {
    StatoDocumento.BOZZA: {StatoDocumento.IN_REVISIONE, StatoDocumento.ARCHIVIATO},
    StatoDocumento.IN_REVISIONE: {StatoDocumento.APPROVATO, StatoDocumento.BOZZA},
    StatoDocumento.APPROVATO: {StatoDocumento.PUBBLICATO, StatoDocumento.BOZZA},
    StatoDocumento.PUBBLICATO: {StatoDocumento.ARCHIVIATO},
    StatoDocumento.ARCHIVIATO: set(),
}


@dataclass
class Documento:
    titolo: str
    autore: str
    contenuto: str = ""
    stato: StatoDocumento = StatoDocumento.BOZZA
    _storico: list[tuple[StatoDocumento, StatoDocumento]] = field(
        default_factory=list, init=False, repr=False
    )

    def transita(self, nuovo_stato: StatoDocumento) -> None:
        consentiti = TRANSIZIONI[self.stato]
        if nuovo_stato not in consentiti:
            consentiti_str = [s.name for s in consentiti]
            raise ValueError(
                f"Transizione {self.stato.name} → {nuovo_stato.name} non consentita. "
                f"Transizioni valide: {consentiti_str}"
            )
        self._storico.append((self.stato, nuovo_stato))
        self.stato = nuovo_stato

    def storico(self) -> list[str]:
        return [f"{da.name} → {a.name}" for da, a in self._storico]


doc = Documento("Guida OOP", "Anna")
doc.transita(StatoDocumento.IN_REVISIONE)
doc.transita(StatoDocumento.APPROVATO)
doc.transita(StatoDocumento.PUBBLICATO)
print(doc.stato.name)   # PUBBLICATO
print(doc.storico())
# ['BOZZA → IN_REVISIONE', 'IN_REVISIONE → APPROVATO', 'APPROVATO → PUBBLICATO']

try:
    doc.transita(StatoDocumento.BOZZA)   # non consentito da PUBBLICATO
except ValueError as e:
    print(e)
```

---

## D4. Composizione vs ereditarietà: framework decisionale

> **Analogia:** L'ereditarietà è come l'acquisizione di un'azienda intera — prendi tutto, inclusi i bagagli non desiderati. La composizione è come assumere consulenti specifici per ogni esigenza — ognuno porta solo le competenze necessarie.

### Checklist decisionale

Prima di usare l'ereditarietà, chiediti:

1. **La relazione è veramente "è un"?** Un cane è un animale ✓. Un'automobile è un motore ✗.
2. **La sottoclasse rispetta il LSP (Liskov Substitution Principle)?** Si può usare la sottoclasse ovunque ci si aspetta la superclasse, senza sorprese?
3. **Si sovrascrivono molti metodi del genitore?** Spesso indica che la composizione è più appropriata.
4. **La gerarchia è già profonda (> 3 livelli)?** Ogni livello aggiunto aumenta la fragilità.
5. **Serve funzionalità da più fonti indipendenti?** Composizione (o mixin disciplinati).

### Esempio pratico: refactoring da ereditarietà a composizione

```python
# ❌ Ereditarietà — fragile e concettualmente sbagliata
class MotoreCombustione:
    def avvia(self) -> str:
        return "Vroom!"

class AutomobileRotta(MotoreCombustione):  # un'auto NON È un motore
    pass


# ✅ Composizione — corretta e flessibile
class Motore(ABC):
    @abstractmethod
    def avvia(self) -> str: ...

    @abstractmethod
    def stato(self) -> dict: ...


class MotoreBenzina(Motore):
    def __init__(self, cilindrata: float):
        self.cilindrata = cilindrata
        self._acceso = False

    def avvia(self) -> str:
        self._acceso = True
        return f"Vroom! ({self.cilindrata}L)"

    def stato(self) -> dict:
        return {"tipo": "benzina", "acceso": self._acceso, "cilindrata": self.cilindrata}


class MotoreElettrico(Motore):
    def __init__(self, potenza_kw: float):
        self.potenza_kw = potenza_kw
        self._carica = 100.0

    def avvia(self) -> str:
        return f"Whirr... ({self.potenza_kw}kW, {self._carica:.0f}% carica)"

    def stato(self) -> dict:
        return {"tipo": "elettrico", "potenza_kw": self.potenza_kw, "carica": self._carica}


class Automobile:
    """Ha un motore — non è un motore."""

    def __init__(self, marca: str, modello: str, motore: Motore):
        self.marca = marca
        self.modello = modello
        self._motore = motore       # composizione: motore iniettato

    def avvia(self) -> str:
        return f"{self.marca} {self.modello}: {self._motore.avvia()}"

    def stato_motore(self) -> dict:
        return self._motore.stato()


# Il motore può essere sostituito senza modificare Automobile
fiat = Automobile("Fiat", "500", MotoreBenzina(1.2))
tesla = Automobile("Tesla", "Model 3", MotoreElettrico(250))

print(fiat.avvia())    # Fiat 500: Vroom! (1.2L)
print(tesla.avvia())   # Tesla Model 3: Whirr... (250kW, 100% carica)
```

### Dependency Injection

La composizione si combina naturalmente con la Dependency Injection: le dipendenze vengono iniettate anziché create internamente, rendendo il codice testabile:

```python
from typing import Protocol


class PersistenzaProtocol(Protocol):
    def salva(self, chiave: str, dati: dict) -> None: ...
    def leggi(self, chiave: str) -> dict | None: ...


class PersistenzaMemoria:
    """Implementazione in-memory — perfetta per i test."""
    def __init__(self):
        self._store: dict[str, dict] = {}

    def salva(self, chiave: str, dati: dict) -> None:
        self._store[chiave] = dict(dati)

    def leggi(self, chiave: str) -> dict | None:
        return self._store.get(chiave)


class PersistenzaFile:
    """Implementazione su file JSON — per produzione."""
    def __init__(self, percorso: str):
        self._percorso = percorso

    def salva(self, chiave: str, dati: dict) -> None:
        import json
        try:
            with open(self._percorso) as f:
                store = json.load(f)
        except FileNotFoundError:
            store = {}
        store[chiave] = dati
        with open(self._percorso, "w") as f:
            json.dump(store, f)

    def leggi(self, chiave: str) -> dict | None:
        import json
        try:
            with open(self._percorso) as f:
                return json.load(f).get(chiave)
        except FileNotFoundError:
            return None


class ServizioUtenti:
    def __init__(self, persistenza: PersistenzaProtocol):
        self._db = persistenza   # dipendenza iniettata

    def crea(self, id: str, nome: str, email: str) -> dict:
        utente = {"id": id, "nome": nome, "email": email}
        self._db.salva(f"utente:{id}", utente)
        return utente

    def trova(self, id: str) -> dict | None:
        return self._db.leggi(f"utente:{id}")


# In produzione
# servizio = ServizioUtenti(PersistenzaFile("utenti.json"))

# Nei test
db_test = PersistenzaMemoria()
servizio = ServizioUtenti(db_test)
u = servizio.crea("U001", "Anna", "anna@test.it")
print(servizio.trova("U001"))   # {'id': 'U001', 'nome': 'Anna', 'email': 'anna@test.it'}
print(servizio.trova("U999"))   # None
```

---

# Parte E — Riepilogo, Checklist e Prossimi Passi

---

## Riepilogo concettuale

```
OOP in Python — Mappa dei concetti

PILASTRI FONDAMENTALI
├── Incapsulamento
│   ├── self.attr (pubblico)
│   ├── self._attr (protetto per convenzione)
│   ├── self.__attr (name mangling → _Classe__attr)
│   └── @property (getter/setter/deleter con sintassi attributo)
│
├── Ereditarietà
│   ├── Singola: class Figlio(Genitore)
│   ├── Multipla: class C(A, B)
│   ├── MRO C3: D.__mro__ = [D, B, C, A, object]
│   ├── super(): classe successiva nella MRO
│   └── Mixin: aggiunta disciplinata di funzionalità
│
├── Polimorfismo
│   ├── Duck typing: "se ha parla(), funziona"
│   ├── Override: sottoclasse ridefinisce metodo del genitore
│   └── Dunder methods: __add__, __eq__, __len__, __iter__...
│
└── Astrazione
    ├── ABC + @abstractmethod: contratto nominale
    ├── Protocol: contratto strutturale (PEP 544)
    └── @property: nasconde implementazione

CLASSI SPECIALI
├── @dataclass: zero boilerplate per classi dati
│   ├── frozen=True → immutabile + hashable
│   ├── order=True → genera <, <=, >, >=
│   ├── slots=True → __slots__ automatico (3.10+)
│   └── kw_only=True → keyword-only args (3.10+)
├── Enum: costanti tipizzate (Enum, IntEnum, StrEnum, Flag)
└── __slots__: memoria ottimizzata

AVANZATO
├── Descriptor: __get__, __set__, __delete__, __set_name__
├── Metaclassi: type sottoclassato, __new__, __init__
└── __init_subclass__: hook leggero sulle sottoclassi (PEP 487)

PATTERN
├── Strategy + Protocol: algoritmi intercambiabili
├── Registry + __init_subclass__: auto-registrazione plugin
├── Observer + weakref: notifiche senza memory leak
├── State + Enum: macchina a stati validata
└── Dependency Injection: composizione + Protocol
```

---

## Checklist di competenze

Segna ✓ quando sei sicuro di ogni competenza:

**Parte A — Basi**
- [ ] Sai definire una classe con attributi di istanza e di classe
- [ ] Capisci la differenza tra `self.attr` e `Classe.attr`
- [ ] Sai scrivere `__repr__` e `__str__` appropriati
- [ ] Sai usare `@property` con getter, setter e deleter
- [ ] Sai implementare ereditarietà singola con `super()`
- [ ] Sai usare `@classmethod` e `@staticmethod` appropriatamente

**Parte B — Comprensione**
- [ ] Sai leggere e spiegare la MRO di una classe con `__mro__`
- [ ] Capisci il comportamento cooperativo di `super()` in ereditarietà multipla
- [ ] Sai scrivere un mixin corretto (nessun `__init__` pesante, focalizzato)
- [ ] Sai usare `@dataclass` con `field()`, `__post_init__`, `frozen`, `slots`
- [ ] Capisci la trappola degli attributi di classe mutabili
- [ ] Sai scegliere tra ABC e Protocol

**Parte D — Avanzato**
- [ ] Sai scrivere un descriptor con `__set_name__`
- [ ] Capisci data descriptor vs non-data descriptor e la priorità di risoluzione
- [ ] Sai usare `__init_subclass__` per auto-registrazione
- [ ] Sai implementare Strategy, Registry, Observer e State in Python idiomatico
- [ ] Sai decidere tra ereditarietà e composizione con il framework decisionale

---

## Anti-pattern da evitare

| Anti-pattern | Problema | Soluzione |
|---|---|---|
| Lista come attributo di classe | Condivisa tra tutte le istanze | Inizializza in `__init__` |
| Ereditarietà per riutilizzo del codice | Crea accoppiamento forte e relazioni "is-a" false | Usa composizione |
| Override che "disabilita" metodi | Viola il Liskov Substitution Principle | Riprogetta la gerarchia |
| `__eq__` senza `__hash__` | Oggetti non usabili in set/dict | Definisci `__hash__` coerente |
| `raise NotImplementedError` nei comparatori | Impedisce l'operazione riflessa | Restituisci `NotImplemented` |
| Descriptor sull'istanza anziché sulla classe | Non viene invocato dal protocollo descriptor | Assegna alla classe, non a `self` |
| Gerarchie profonde (> 3 livelli) | Fragili, difficili da mantenere | Appiattisci con composizione |
| Metaclasse quando basta `__init_subclass__` | Complessità inutile | Usa `__init_subclass__` |
| `import` inside `__init__` ripetuto | Micro-overhead ad ogni istanziazione | Importa a livello di modulo |

---

## Troubleshooting rapido

**`TypeError: Cannot create a consistent MRO`**
- Causa: ordine contraddittorio tra basi — es. `A(X, Y)` e `B(Y, X)` poi `C(A, B)`
- Fix: riordina le basi in modo coerente o rivedi la gerarchia

**`AttributeError: 'MiaClasse' object has no attribute 'attr'` ma l'attributo esiste**
- Causa 1: il descriptor è sull'istanza anziché sulla classe
- Causa 2: `__init__` non ha assegnato l'attributo perché una branch non è stata raggiunta

**`TypeError: unhashable type: 'MiaClasse'`**
- Causa: definito `__eq__` senza `__hash__`
- Fix: aggiungi `__hash__` coerente con `__eq__`, oppure `__hash__ = None` se mutabile

**`FrozenInstanceError`**
- Causa: tentativo di modificare un attributo di una `@dataclass(frozen=True)`
- Fix: usa `dataclasses.replace(istanza, campo=nuovo_valore)`

**Descriptor non intercetta l'accesso**
- Causa: assegnato a `self.desc = MioDescriptor()` anziché a `Classe.desc = MioDescriptor()`
- Fix: il descriptor deve essere attributo di **classe**

**`__init__` di un mixin non chiamato**
- Causa: la classe non chiama `super().__init__(**kwargs)` e interrompe la catena MRO
- Fix: ogni `__init__` nella catena deve chiamare `super().__init__(**kwargs)`

---

## Prossimi passi

Dopo aver completato questo tutorial, il percorso naturale è:

| Modulo | Collegamento con questo tutorial |
|---|---|
| `tutorial_03_strutture_dati_avanzate.md` | `collections.abc`, implementazioni custom di container |
| `tutorial_04_decoratori_generatori_context_manager.md` | Decoratori di classe, `contextlib`, generatori come alternativa a `__iter__` |
| `tutorial_08_testing.md` | Testing di classi OOP, mock di dipendenze iniettate, `pytest` con fixture |
| `tutorial_09_type_hints_mypy.md` | `Protocol`, `Generic`, `TypeVar`, verifica statica delle gerarchie |
| `tutorial_21_design_patterns.md` | Pattern GoF completi, SOLID in Python, architettura |
| `tutorial_22_clean_code.md` | Principi di design, SRP, code smell, refactoring OOP |

---

## Risorse di riferimento

**Documentazione ufficiale:**
- [Python Data Model](https://docs.python.org/3/reference/datamodel.html) — modello a oggetti, dunder methods, descriptor
- [Descriptor HowTo Guide](https://docs.python.org/3/howto/descriptor.html) — Raymond Hettinger, fondamentale
- [abc module](https://docs.python.org/3/library/abc.html)
- [collections.abc](https://docs.python.org/3/library/collections.abc.html)
- [dataclasses](https://docs.python.org/3/library/dataclasses.html)
- [enum](https://docs.python.org/3/library/enum.html)

**PEP di riferimento:**
- PEP 487 — `__init_subclass__` e `__set_name__`
- PEP 544 — Protocol (structural subtyping)
- PEP 557 — Data Classes
- PEP 634 — Structural Pattern Matching
- PEP 3119 — Abstract Base Classes

**Libri:**
- Luciano Ramalho, *Fluent Python* (2nd ed., 2022) — capitoli 11-16 su descriptor, metaclassi, overloading
- Brett Slatkin, *Effective Python* (3rd ed., 2024) — item su metaclassi, descriptor, `__init_subclass__`

---

> **Fine del Tutorial 02 — Programmazione Orientata agli Oggetti**
>
> Prossimo tutorial: `tutorial_03_strutture_dati_avanzate.md`
