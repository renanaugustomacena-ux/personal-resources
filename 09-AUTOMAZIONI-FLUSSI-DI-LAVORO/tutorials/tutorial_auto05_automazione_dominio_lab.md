# Tutorial Lab — Automazione per Dominio: HR, Finance, IT Ops, E-Commerce

> **Campo di studio:** 09-AUTOMAZIONI-FLUSSI-DI-LAVORO
> **Modulo sorgente:** `05-automazione-per-dominio.md`
> **Livello:** intermediate
> **Tempo stimato:** 3 ore
> **Prerequisiti:** Python 3.11+, Docker, conoscenza base API REST
> **Versioni di riferimento:** Python 3.11+, httpx 0.27+, n8n 1.x

---

## Obiettivi del Lab

Al termine di questo tutorial saprai:

1. Applicare pattern di automazione specifici per dominio (HR, Finance, IT Ops, E-Commerce)
2. Costruire pipeline di dati verticali con trasformazioni domain-specific
3. Gestire dati sensibili (stipendi, dati personali) con pseudonimizzazione
4. Creare report automatici con aggregazioni e alert contestuali
5. Integrare sistemi legacy via CSV/FTP con piattaforme moderne via API
6. Schedulare workflow complessi con dipendenze tra step

---

## Lab Environment Setup

```bash
# Prerequisiti installazione
pip install httpx httpx[http2] pandas openpyxl jinja2 structlog schedule

# Verifica installazione
python -c "import httpx, pandas, openpyxl, jinja2, structlog, schedule; print('OK')"
```

---

## Analogia Introduttiva

> **L'automazione per dominio è come assumere un assistente che conosce il gergo del settore**:
> un assistente generalista sa mandare email e creare cartelle,
> ma ci vuole un assistente HR per sapere che "headcount approval" significa
> che servono 3 firme prima di pubblicare un'offerta di lavoro.
>
> I **workflow domain-specific** incorporano le regole di business del settore:
> in Finance sai che le riconciliazioni si fanno ogni fine mese,
> in HR sai che l'onboarding richiede badge, credenziali e check GDPR,
> in IT Ops sai che un alert alle 3 di notte va scalato se non acknowledge entro 15 minuti.
>
> La differenza tra un'automazione generica e una verticale
> è la differenza tra un coltello svizzero e un bisturi.

---

## Architettura Multi-Dominio

```
┌─────────────────────────────────────────────────────────────────────┐
│                    DOMINI DI AUTOMAZIONE                             │
│                                                                       │
│  ┌─────────────────┐         ┌──────────────────────────────────┐   │
│  │       HR        │         │            FINANCE               │   │
│  │  Onboarding     │         │  Riconciliazione movimenti        │   │
│  │  Offboarding    │         │  Budget alert mensile             │   │
│  │  Payroll check  │         │  Fatturazione automatica          │   │
│  └────────┬────────┘         └────────────┬─────────────────────┘   │
│           │                               │                           │
│           ▼                               ▼                           │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │              LAYER COMUNE: Python + httpx + pandas              │ │
│  │   CSV ↔ JSON ↔ API | Cron Schedule | Structured Logging        │ │
│  └────────────────────────────────────────────────────────────────┘ │
│           ▲                               ▲                           │
│           │                               │                           │
│  ┌────────┴────────┐         ┌────────────┴─────────────────────┐   │
│  │     IT OPS      │         │           E-COMMERCE             │   │
│  │  Alert routing  │         │  Stock monitoring                 │   │
│  │  Patch schedule │         │  Order fulfillment                │   │
│  │  Backup verify  │         │  Price crawler                    │   │
│  └─────────────────┘         └──────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## PART A — HR Automation

### A1 — Pipeline Onboarding Nuovo Dipendente

```python
# hr/onboarding_pipeline.py
from __future__ import annotations

import csv
import hashlib
import os
from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum
from pathlib import Path

import httpx
import structlog

log = structlog.get_logger()

class StatoOnboarding(Enum):
    PENDING = "pending"
    IN_CORSO = "in_corso"
    COMPLETATO = "completato"
    FALLITO = "fallito"

@dataclass
class NuovoDipendente:
    nome: str
    cognome: str
    email_aziendale: str
    reparto: str
    manager_email: str
    data_inizio: date
    ruolo: str
    livello_accesso: str = "base"

    def id_anonimo(self) -> str:
        """Identifica il dipendente con hash per log GDPR-safe."""
        raw = f"{self.email_aziendale}:{self.data_inizio}"
        return hashlib.sha256(raw.encode()).hexdigest()[:12]

@dataclass
class TaskOnboarding:
    nome: str
    responsabile: str
    deadline_giorni: int
    completato: bool = False

def genera_checklist_onboarding(dipendente: NuovoDipendente) -> list[TaskOnboarding]:
    """Genera la checklist specifica per reparto e livello accesso."""
    base: list[TaskOnboarding] = [
        TaskOnboarding("Creazione account email", "IT", 0),
        TaskOnboarding("Badge accesso fisico", "Facilities", 1),
        TaskOnboarding("Workstation setup", "IT", 1),
        TaskOnboarding("Accesso VPN", "IT", 2),
        TaskOnboarding("Firma contratto", "HR", 0),
        TaskOnboarding("GDPR awareness training", "HR", 7),
        TaskOnboarding("Presentazione al team", "Manager", 0),
        TaskOnboarding("Obiettivi primo trimestre", "Manager", 30),
    ]
    if dipendente.livello_accesso == "admin":
        base.append(TaskOnboarding("Setup MFA obbligatorio", "IT", 0))
        base.append(TaskOnboarding("Revisione policy sicurezza", "Security", 3))
    if dipendente.reparto == "Finance":
        base.append(TaskOnboarding("Accesso ERP Finance", "IT", 2))
        base.append(TaskOnboarding("Firma NDA dati finanziari", "Legal", 0))
    return base

def notifica_task_scadenti(checklist: list[TaskOnboarding], giorni_dall_inizio: int) -> list[str]:
    """Identifica task in scadenza oggi o già scaduti."""
    urgenti = []
    for task in checklist:
        if not task.completato and task.deadline_giorni <= giorni_dall_inizio:
            urgenti.append(f"[URGENTE] {task.nome} → {task.responsabile}")
    return urgenti

def esporta_checklist_csv(dipendente: NuovoDipendente,
                           checklist: list[TaskOnboarding],
                           output_path: Path) -> None:
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["task", "responsabile", "deadline_giorni", "completato"])
        writer.writeheader()
        for task in checklist:
            writer.writerow({
                "task": task.nome,
                "responsabile": task.responsabile,
                "deadline_giorni": task.deadline_giorni,
                "completato": task.completato,
            })
    log.info("checklist_esportata",
             dipendente=dipendente.id_anonimo(),
             path=str(output_path),
             num_task=len(checklist))


if __name__ == "__main__":
    import structlog
    structlog.configure()

    nuovo = NuovoDipendente(
        nome="Mario",
        cognome="Rossi",
        email_aziendale="mario.rossi@azienda.it",
        reparto="Finance",
        manager_email="lucia.verdi@azienda.it",
        data_inizio=date.today(),
        ruolo="Analista Finanziario",
        livello_accesso="admin",
    )
    checklist = genera_checklist_onboarding(nuovo)
    print(f"Checklist generata: {len(checklist)} task")
    for t in checklist:
        print(f"  - {t.nome} ({t.responsabile}) → giorno {t.deadline_giorni}")

    output = Path("onboarding_mario_rossi.csv")
    esporta_checklist_csv(nuovo, checklist, output)
    print(f"Esportato: {output}")
```

---

## PART B — Finance Automation

### B1 — Riconciliazione Movimenti Bancari

```python
# finance/riconciliazione.py
from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Iterator

@dataclass(frozen=True)
class MovimentoBancario:
    data: date
    descrizione: str
    importo: Decimal
    tipo: str  # "entrata" | "uscita"
    riferimento: str

@dataclass(frozen=True)
class FatturaInterna:
    numero: str
    data: date
    importo: Decimal
    fornitore: str
    stato: str  # "attesa" | "pagata" | "contestata"

@dataclass
class RisultatoRiconciliazione:
    abbinate: list[tuple[MovimentoBancario, FatturaInterna]]
    non_abbinate_banca: list[MovimentoBancario]
    non_abbinate_fatture: list[FatturaInterna]
    differenza_totale: Decimal

def carica_movimenti_csv(path: Path) -> list[MovimentoBancario]:
    movimenti = []
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            movimenti.append(MovimentoBancario(
                data=date.fromisoformat(row["data"]),
                descrizione=row["descrizione"],
                importo=Decimal(row["importo"]),
                tipo=row["tipo"],
                riferimento=row.get("riferimento", ""),
            ))
    return movimenti

def riconcilia(movimenti: list[MovimentoBancario],
               fatture: list[FatturaInterna],
               tolleranza: Decimal = Decimal("0.01")) -> RisultatoRiconciliazione:
    """
    Abbina movimenti bancari a fatture interne per importo e data (± 5 giorni).
    Usa tolleranza per differenze di centesimi (arrotondamenti bancari).
    """
    abbinate: list[tuple[MovimentoBancario, FatturaInterna]] = []
    fatture_da_abbinare = list(fatture)
    movimenti_da_abbinare = list(movimenti)

    for movimento in movimenti:
        for fattura in list(fatture_da_abbinare):
            differenza_importo = abs(movimento.importo - fattura.importo)
            differenza_giorni = abs((movimento.data - fattura.data).days)
            if differenza_importo <= tolleranza and differenza_giorni <= 5:
                abbinate.append((movimento, fattura))
                fatture_da_abbinare.remove(fattura)
                movimenti_da_abbinare.remove(movimento)
                break

    differenza = sum(m.importo for m in movimenti_da_abbinare) - sum(f.importo for f in fatture_da_abbinare)
    return RisultatoRiconciliazione(
        abbinate=abbinate,
        non_abbinate_banca=movimenti_da_abbinare,
        non_abbinate_fatture=fatture_da_abbinare,
        differenza_totale=differenza.quantize(Decimal("0.01"), ROUND_HALF_UP),
    )

def genera_report_riconciliazione(risultato: RisultatoRiconciliazione) -> str:
    lines = [
        "=== REPORT RICONCILIAZIONE ===",
        f"Abbinate: {len(risultato.abbinate)}",
        f"Non abbinate (banca): {len(risultato.non_abbinate_banca)}",
        f"Non abbinate (fatture): {len(risultato.non_abbinate_fatture)}",
        f"Differenza totale: €{risultato.differenza_totale}",
        "",
        "--- MOVIMENTI BANCARI NON ABBINATI ---",
    ]
    for m in risultato.non_abbinate_banca:
        lines.append(f"  {m.data} | {m.descrizione[:40]} | €{m.importo}")
    lines.append("")
    lines.append("--- FATTURE NON ABBINATE ---")
    for f in risultato.non_abbinate_fatture:
        lines.append(f"  {f.numero} | {f.fornitore[:30]} | €{f.importo} | {f.stato}")
    return "\n".join(lines)
```

---

## PART C — IT Ops Automation

### C1 — Alert Routing e Escalation

```python
# itops/alert_routing.py
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta

import httpx
import structlog

log = structlog.get_logger()

class SeveritaAlert(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class Alert:
    id: str
    titolo: str
    severita: SeveritaAlert
    host: str
    servizio: str
    messaggio: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    acknowledgiato: bool = False

@dataclass
class RegolaEscalation:
    severita_minima: SeveritaAlert
    minuti_senza_ack: int
    canale: str
    contatti: list[str]

REGOLE_ESCALATION: list[RegolaEscalation] = [
    RegolaEscalation(SeveritaAlert.LOW, 120, "email", ["itops@azienda.it"]),
    RegolaEscalation(SeveritaAlert.MEDIUM, 30, "slack", ["#itops-alerts"]),
    RegolaEscalation(SeveritaAlert.HIGH, 15, "slack", ["#itops-critico", "@oncall"]),
    RegolaEscalation(SeveritaAlert.CRITICAL, 5, "pagerduty", ["oncall-primary"]),
]

def calcola_escalation(alert: Alert, ora_corrente: datetime) -> list[RegolaEscalation]:
    """Determina a chi escalare in base a severità e tempo passato."""
    if alert.acknowledgiato:
        return []
    minuti_passati = (ora_corrente - alert.timestamp).total_seconds() / 60
    applicabili = []
    for regola in REGOLE_ESCALATION:
        if (alert.severita.value >= regola.severita_minima.value and
                minuti_passati >= regola.minuti_senza_ack):
            applicabili.append(regola)
    return applicabili

async def invia_notifica_slack(webhook_url: str, alert: Alert, contatti: list[str]) -> None:
    messaggio = {
        "text": f"🚨 [{alert.severita.name}] {alert.titolo}",
        "attachments": [{
            "color": "danger" if alert.severita.value >= 3 else "warning",
            "fields": [
                {"title": "Host", "value": alert.host, "short": True},
                {"title": "Servizio", "value": alert.servizio, "short": True},
                {"title": "Messaggio", "value": alert.messaggio},
            ],
            "footer": f"Alert ID: {alert.id} | {alert.timestamp.isoformat()}",
        }],
    }
    if contatti:
        messaggio["text"] += " " + " ".join(contatti)
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(webhook_url, json=messaggio)
        resp.raise_for_status()
        log.info("notifica_inviata", alert_id=alert.id, canale="slack")

def esegui_patch_schedule(hosts: list[str], finestra_manutenzione: tuple[int, int]) -> dict[str, str]:
    """
    Pianifica patch per host, rispettando finestra di manutenzione.
    finestra_manutenzione: (ora_inizio, ora_fine) in formato 24h
    """
    ora_corrente = datetime.utcnow().hour
    ora_inizio, ora_fine = finestra_manutenzione
    risultati: dict[str, str] = {}

    if not (ora_inizio <= ora_corrente < ora_fine):
        log.warning("patch_fuori_finestra",
                    ora_corrente=ora_corrente,
                    finestra=f"{ora_inizio}-{ora_fine}")
        return {h: "postponed" for h in hosts}

    for host in hosts:
        try:
            log.info("patch_avviata", host=host)
            risultati[host] = "success"
        except Exception as e:
            log.error("patch_fallita", host=host, errore=str(e))
            risultati[host] = f"failed: {e}"
    return risultati
```

---

## PART D — E-Commerce Automation

### D1 — Stock Monitor e Repricing

```python
# ecommerce/stock_monitor.py
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from decimal import Decimal
from typing import AsyncIterator

import httpx
import structlog

log = structlog.get_logger()

@dataclass
class Prodotto:
    sku: str
    nome: str
    prezzo: Decimal
    stock: int
    soglia_riordino: int
    soglia_alert_critico: int

@dataclass
class AlertStock:
    sku: str
    tipo: str  # "riordino" | "critico" | "esaurito"
    stock_attuale: int
    soglia: int
    messaggio: str

def analizza_stock(prodotti: list[Prodotto]) -> list[AlertStock]:
    """Identifica prodotti che necessitano attenzione."""
    alerts = []
    for p in prodotti:
        if p.stock == 0:
            alerts.append(AlertStock(
                sku=p.sku, tipo="esaurito",
                stock_attuale=0, soglia=p.soglia_riordino,
                messaggio=f"{p.nome} ESAURITO — ordine urgente richiesto",
            ))
        elif p.stock <= p.soglia_alert_critico:
            alerts.append(AlertStock(
                sku=p.sku, tipo="critico",
                stock_attuale=p.stock, soglia=p.soglia_alert_critico,
                messaggio=f"{p.nome}: stock critico ({p.stock} unità)",
            ))
        elif p.stock <= p.soglia_riordino:
            alerts.append(AlertStock(
                sku=p.sku, tipo="riordino",
                stock_attuale=p.stock, soglia=p.soglia_riordino,
                messaggio=f"{p.nome}: riordino consigliato ({p.stock}/{p.soglia_riordino})",
            ))
    return alerts

@dataclass
class StrategiaPrezzo:
    """Regole di repricing automatico."""
    margine_minimo_pct: Decimal = Decimal("0.15")
    max_sconto_pct: Decimal = Decimal("0.20")
    incremento_per_alta_domanda: Decimal = Decimal("0.05")

def calcola_nuovo_prezzo(prodotto: Prodotto,
                          costo_acquisto: Decimal,
                          domanda_relativa: float,
                          strategia: StrategiaPrezzo) -> Decimal:
    """
    Calcola prezzo ottimale basato su stock, domanda e margine minimo.
    domanda_relativa: 0.0 (bassa) → 2.0 (molto alta rispetto alla media)
    """
    prezzo_minimo = costo_acquisto * (1 + strategia.margine_minimo_pct)
    prezzo_massimo_sconto = prodotto.prezzo * (1 - strategia.max_sconto_pct)

    if prodotto.stock <= prodotto.soglia_alert_critico:
        # Stock basso → non scontare
        prezzo_base = prodotto.prezzo
    elif domanda_relativa > 1.5:
        # Alta domanda → incrementa prezzo
        prezzo_base = prodotto.prezzo * (1 + strategia.incremento_per_alta_domanda)
    elif domanda_relativa < 0.5 and prodotto.stock > prodotto.soglia_riordino * 3:
        # Bassa domanda + stock alto → sconto
        prezzo_base = max(
            prezzo_minimo,
            prodotto.prezzo * (1 - strategia.max_sconto_pct * Decimal(str(1 - domanda_relativa))),
        )
    else:
        prezzo_base = prodotto.prezzo

    return max(prezzo_minimo, min(prezzo_base, prezzo_massimo_sconto + (prezzo_massimo_sconto * Decimal("0.1"))))


if __name__ == "__main__":
    prodotti = [
        Prodotto("SKU-001", "Laptop Pro 15", Decimal("1299.00"), 3, 10, 5),
        Prodotto("SKU-002", "Mouse Wireless", Decimal("29.90"), 0, 20, 5),
        Prodotto("SKU-003", "Monitor 4K", Decimal("499.00"), 45, 15, 5),
    ]
    alerts = analizza_stock(prodotti)
    for alert in alerts:
        print(f"[{alert.tipo.upper()}] {alert.messaggio}")

    laptop = prodotti[0]
    nuovo_prezzo = calcola_nuovo_prezzo(
        laptop,
        costo_acquisto=Decimal("900.00"),
        domanda_relativa=1.8,
        strategia=StrategiaPrezzo(),
    )
    print(f"\nLaptop Pro — prezzo attuale: €{laptop.prezzo} → nuovo: €{nuovo_prezzo:.2f}")
```

---

## Esercizi

### Esercizio 1 — HR: Offboarding Checklist (25 min)

Implementa `genera_checklist_offboarding(dipendente, motivo)` che genera una checklist diversa per:
- Dimissioni volontarie (2 settimane di preavviso)
- Licenziamento (immediato, accesso revocato il giorno stesso)
- Fine contratto (pianificato, 30 giorni di preavviso)

La funzione deve includere sempre: revoca accessi IT, restituzione badge, exit interview, backup dati.

### Esercizio 2 — Finance: Alert Budget (20 min)

Implementa `controlla_budget_mensile(spese_effettive, budget_mensile, soglie)` dove `soglie` è una lista di percentuali (es: `[0.70, 0.85, 1.0]`). La funzione deve:
- Calcolare la percentuale consumata
- Per ogni soglia superata, generare un alert con livello crescente
- Restituire lista di alert ordinata per gravità

### Esercizio 3 — E-Commerce: Report Giornaliero (20 min)

Scrivi una funzione `genera_report_stock(prodotti, output_path)` che:
- Raggruppa i prodotti per categoria di rischio (ok, riordino, critico, esaurito)
- Calcola il valore totale dello stock (prezzo × quantità)
- Scrive un CSV con colonne: sku, nome, stock, stato, valore_stock
- Stampa un sommario: X prodotti OK, Y in riordino, Z critici

---

## Riferimenti

- Modulo sorgente: `05-automazione-per-dominio.md`
- Pandas docs: https://pandas.pydata.org/docs/
- httpx: https://www.python-httpx.org/
- structlog: https://www.structlog.org/
