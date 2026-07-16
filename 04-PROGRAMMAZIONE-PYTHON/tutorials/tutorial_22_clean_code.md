# Tutorial 22 — Clean Code in Python: Principi SOLID, Refactoring, Leggibilità

> **Companion a:** `22-clean-code.md`
> **Scope:** SOLID, naming, funzioni, classi, refactoring, code smell, metriche qualità
> **Prerequisiti:** `tutorial_02_oop.md`, `tutorial_21_design_patterns.md`
> **Durata stimata:** 12-16 ore

---

## Mappa concettuale

```
Clean Code
│
├── Naming — nomi che comunicano
│   ├── Variabili: sostantivi descrittivi
│   ├── Funzioni: verbi + oggetto
│   ├── Classi: sostantivi singolari
│   └── Evitare: abbreviazioni, numeri magici, prefissi
│
├── Funzioni
│   ├── Una sola responsabilità
│   ├── Pochi parametri (≤3 ideale)
│   ├── Nessun side effect nascosto
│   └── Livello di astrazione uniforme
│
├── Classi
│   ├── SRP — Single Responsibility
│   ├── OCP — Open/Closed
│   ├── LSP — Liskov Substitution
│   ├── ISP — Interface Segregation
│   └── DIP — Dependency Inversion
│
├── Code Smell — segnali di problema
│   ├── God Class — fa troppo
│   ├── Long Method — troppo codice
│   ├── Primitive Obsession — troppi tipi primitivi
│   ├── Feature Envy — accede troppo ad altri oggetti
│   └── Dead Code — codice non raggiunto
│
├── Refactoring — tecniche
│   ├── Extract Function/Class
│   ├── Rename
│   ├── Introduce Parameter Object
│   ├── Replace Conditional with Polymorphism
│   └── Guard Clause
│
└── Metriche
    ├── Cyclomatic Complexity — ≤10 per funzione
    ├── Cognitive Complexity — ≤15
    ├── Lines per function — ≤20
    └── ruff / pylint / radon
```

---

# Parte A — Naming e leggibilità

---

## A1. Naming che comunica

```python
# SBAGLIATO — nomi senza significato
def f(l, x, y):
    r = []
    for i in l:
        if i[x] > y:
            r.append(i)
    return r

# CORRETTO — nomi che raccontano l'intenzione
def filtra_prodotti_sopra_prezzo(
    prodotti: list[dict],
    campo_prezzo: str,
    soglia: float,
) -> list[dict]:
    return [p for p in prodotti if p[campo_prezzo] > soglia]

# SBAGLIATO — abbreviazioni criptiche
def calc_ret_on_inv(net_inc, inv):
    return net_inc / inv * 100

# CORRETTO — nome completo, anche se lungo
def calcola_ritorno_su_investimento(reddito_netto: float, investimento: float) -> float:
    if investimento == 0:
        raise ValueError("L'investimento non può essere zero")
    return reddito_netto / investimento * 100

# SBAGLIATO — numeri magici
def calcola_stipendio(ore_lavorate: float) -> float:
    return ore_lavorate * 27.5 * 1.22 if ore_lavorate > 160 else ore_lavorate * 27.5

# CORRETTO — costanti nominate
TARIFFA_ORARIA = 27.5
ALIQUOTA_STRAORDINARIO = 1.22
ORE_MENSILI_STANDARD = 160

def calcola_stipendio(ore_lavorate: float) -> float:
    if ore_lavorate > ORE_MENSILI_STANDARD:
        ore_extra = ore_lavorate - ORE_MENSILI_STANDARD
        return (ORE_MENSILI_STANDARD + ore_extra * ALIQUOTA_STRAORDINARIO) * TARIFFA_ORARIA
    return ore_lavorate * TARIFFA_ORARIA
```

> **Analogia:** Un codice con nomi buoni è come un libro con titoli di capitoli chiari — puoi navigarlo senza leggerlo tutto. Un codice con `x`, `tmp`, `data` è come un libro senza titoli: devi leggere ogni pagina per capire dove sei.

---

## A2. Funzioni: una sola responsabilità

```python
# SBAGLIATO: funzione che fa troppe cose
def processa_ordine(ordine_id: int, email_utente: str) -> bool:
    # 1. Recupera ordine
    import sqlite3
    conn = sqlite3.connect("db.sqlite3")
    row = conn.execute("SELECT * FROM ordini WHERE id = ?", (ordine_id,)).fetchone()
    if row is None:
        return False
    # 2. Valida
    if row[3] <= 0:
        return False
    # 3. Calcola totale con IVA
    totale = row[3] * 1.22
    # 4. Aggiorna DB
    conn.execute("UPDATE ordini SET stato='confermato', totale_iva=? WHERE id=?", (totale, ordine_id))
    conn.commit()
    # 5. Invia email
    import smtplib
    # ... 20 righe di SMTP
    return True

# CORRETTO: ogni funzione ha UN scopo
def recupera_ordine(ordine_id: int, conn) -> dict | None:
    row = conn.execute("SELECT id, importo FROM ordini WHERE id = ?", (ordine_id,)).fetchone()
    return {"id": row[0], "importo": row[1]} if row else None

def valida_ordine(ordine: dict) -> bool:
    return ordine.get("importo", 0) > 0

def calcola_totale_con_iva(importo: float, aliquota_iva: float = 0.22) -> float:
    return round(importo * (1 + aliquota_iva), 2)

def aggiorna_stato_ordine(ordine_id: int, totale: float, conn) -> None:
    conn.execute(
        "UPDATE ordini SET stato='confermato', totale_iva=? WHERE id=?",
        (totale, ordine_id),
    )
    conn.commit()

def invia_conferma_email(email: str, ordine_id: int, totale: float) -> None:
    pass  # logica email separata

def processa_ordine_v2(ordine_id: int, email_utente: str, conn) -> bool:
    ordine = recupera_ordine(ordine_id, conn)
    if ordine is None or not valida_ordine(ordine):
        return False
    totale = calcola_totale_con_iva(ordine["importo"])
    aggiorna_stato_ordine(ordine_id, totale, conn)
    invia_conferma_email(email_utente, ordine_id, totale)
    return True
```

---

# Parte B — SOLID in Python

---

## B1. SRP e OCP

```python
# SRP: Single Responsibility
# SBAGLIATO: Report gestisce sia la logica che la stampa
class Report:
    def genera(self, dati: list) -> str: return str(dati)
    def stampa_su_console(self, testo: str): print(testo)
    def salva_su_file(self, testo: str, percorso: str): pass
    def invia_per_email(self, testo: str, email: str): pass

# CORRETTO: responsabilità separate
class GeneratoreReport:
    def genera(self, dati: list) -> str: return str(dati)

class StampanteReport:
    def stampa(self, testo: str) -> None: print(testo)

class SalvatorReport:
    def salva(self, testo: str, percorso: str) -> None:
        open(percorso, "w").write(testo)

# OCP: Open/Closed
# SBAGLIATO: aggiungere un formato richiede modificare la classe
class ExporterMale:
    def esporta(self, dati: list, formato: str) -> str:
        if formato == "json":
            import json; return json.dumps(dati)
        elif formato == "csv":
            return ",".join(str(x) for x in dati)
        # Aggiungere XML richiede modificare questo codice!

# CORRETTO: open per estensione, closed per modifica
from typing import Protocol

class FormatoExport(Protocol):
    def esporta(self, dati: list) -> str: ...

class ExportJSON:
    def esporta(self, dati: list) -> str:
        import json; return json.dumps(dati)

class ExportCSV:
    def esporta(self, dati: list) -> str:
        return "\n".join(",".join(str(x) for x in riga) for riga in dati)

class Exporter:
    def __init__(self, formato: FormatoExport) -> None:
        self._formato = formato
    def esporta(self, dati: list) -> str:
        return self._formato.esporta(dati)
```

---

## B2. LSP, ISP, DIP

```python
from abc import ABC, abstractmethod

# LSP: Liskov Substitution
class FormaGeometrica(ABC):
    @abstractmethod
    def area(self) -> float: ...
    @abstractmethod
    def perimetro(self) -> float: ...

class Rettangolo(FormaGeometrica):
    def __init__(self, larghezza: float, altezza: float) -> None:
        self.larghezza = larghezza
        self.altezza = altezza
    def area(self) -> float: return self.larghezza * self.altezza
    def perimetro(self) -> float: return 2 * (self.larghezza + self.altezza)

class Cerchio(FormaGeometrica):
    def __init__(self, raggio: float) -> None:
        self.raggio = raggio
    def area(self) -> float: return 3.14159 * self.raggio ** 2
    def perimetro(self) -> float: return 2 * 3.14159 * self.raggio

# Funzione che funziona con QUALSIASI FormaGeometrica — LSP
def stampa_info(forma: FormaGeometrica) -> None:
    print(f"Area: {forma.area():.2f}, Perimetro: {forma.perimetro():.2f}")

# ISP: Interface Segregation
class StampanteMultifunzione(Protocol):
    def stampa(self) -> None: ...
    def scansiona(self) -> None: ...
    def invia_fax(self) -> None: ...

# CORRETTO: interfacce piccole e specifiche
class Stampante(Protocol):
    def stampa(self) -> None: ...

class Scanner(Protocol):
    def scansiona(self) -> None: ...

class FaxMachine(Protocol):
    def invia_fax(self) -> None: ...

# DIP: Dependency Inversion
class ServizioEmailConcreto:
    def invia(self, a: str, oggetto: str, corpo: str) -> None:
        print(f"Email a {a}: {oggetto}")

# SBAGLIATO: dipendenza da implementazione concreta
class NotificatoreMailSbagliato:
    def __init__(self) -> None:
        self._servizio = ServizioEmailConcreto()   # hardcoded!

# CORRETTO: dipendenza da astrazione (Protocol o ABC)
class ServizioNotifiche(Protocol):
    def invia(self, destinatario: str, oggetto: str, corpo: str) -> None: ...

class Notificatore:
    def __init__(self, servizio: ServizioNotifiche) -> None:
        self._servizio = servizio   # iniettato — testabile e intercambiabile

    def notifica_utente(self, email: str, msg: str) -> None:
        self._servizio.invia(email, "Notifica", msg)
```

---

# Parte C — Refactoring

---

## C1. Guard clauses e early return

```python
# SBAGLIATO: profondità eccessiva
def processa(utente, ordine, prodotto):
    if utente is not None:
        if utente.attivo:
            if ordine is not None:
                if ordine.stato == "approvato":
                    if prodotto.disponibile:
                        return prodotto.prezzo * ordine.quantita
                    else:
                        return 0
                else:
                    return 0
            else:
                return 0
        else:
            return 0
    else:
        return 0

# CORRETTO: guard clauses — elimina nesting con early return
def processa_v2(utente, ordine, prodotto) -> float:
    if utente is None or not utente.attivo:
        return 0
    if ordine is None or ordine.stato != "approvato":
        return 0
    if not prodotto.disponibile:
        return 0
    return prodotto.prezzo * ordine.quantita
```

---

## C2. Replace conditional with polymorphism

```python
# SBAGLIATO: switch-case su tipo
def calcola_sconto(tipo_cliente: str, importo: float) -> float:
    if tipo_cliente == "normale":
        return 0.0
    elif tipo_cliente == "premium":
        return importo * 0.10
    elif tipo_cliente == "vip":
        return importo * 0.20
    elif tipo_cliente == "partner":
        return importo * 0.30
    return 0.0

# CORRETTO: polimorfismo tramite Protocol
from typing import Protocol

class CalcolatoreSconto(Protocol):
    def calcola(self, importo: float) -> float: ...

class ScontoNormale:
    def calcola(self, importo: float) -> float: return 0.0

class ScontoPremium:
    def calcola(self, importo: float) -> float: return importo * 0.10

class ScontoVIP:
    def calcola(self, importo: float) -> float: return importo * 0.20

SCONTI: dict[str, CalcolatoreSconto] = {
    "normale": ScontoNormale(),
    "premium": ScontoPremium(),
    "vip": ScontoVIP(),
}

def calcola_sconto_v2(tipo_cliente: str, importo: float) -> float:
    calcolatore = SCONTI.get(tipo_cliente, ScontoNormale())
    return calcolatore.calcola(importo)
```

---

# Parte D — Strumenti qualità

---

## D1. ruff, pylint, radon

```toml
# pyproject.toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "B", "C", "UP"]
ignore = ["E501"]

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["S101"]   # assert OK nei test
```

```bash
# Analisi qualità
ruff check .               # lint veloce
ruff format .              # format
pylint src/                # analisi approfondita
radon cc src/ -a           # complessità ciclomatica media
radon mi src/              # maintainability index
mypy src/ --strict         # type checking
```

---

# Parte E — Riepilogo

## Code Smell → Refactoring

| Smell | Tecnica |
|---|---|
| Funzione lunga (>20 righe) | Extract Function |
| Molti parametri (>3) | Introduce Parameter Object |
| If/elif a cascata su tipo | Replace with Polymorphism |
| Nesting profondo | Guard Clause / Early Return |
| Codice duplicato | Extract Function, Template Method |
| God Class | Extract Class, SRP |
| Commenti che spiegano il codice | Rinomina la funzione |
| Numero magico | Costante nominata |

## Regola del Boy Scout

> Lascia il codice **più pulito** di come lo hai trovato. Non fare refactoring massiccio: correggi un nome, estrai una funzione, rimuovi un commento obsoleto — ogni volta che tocchi un file.

## Prossimi passi

- `tutorial_21_design_patterns.md` — pattern che esprimono le intenzioni nel codice
- `tutorial_25_performance.md` — performance senza sacrificare leggibilità
