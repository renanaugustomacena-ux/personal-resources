# Tutorial Lab — Ricette PMI: Automazioni Verticali per Contabilità, CRM, E-Commerce, HR

> **Campo di studio:** 09-AUTOMAZIONI-FLUSSI-DI-LAVORO
> **Modulo sorgente:** `21-ricette-automazione-pmi.md`
> **Livello:** intermediate → advanced
> **Tempo stimato:** 3 ore
> **Prerequisiti:** n8n base, Python 3.11+, concetti API REST
> **Versioni di riferimento:** n8n 1.x, Python 3.11+

---

## Obiettivi del Lab

Al termine di questo tutorial saprai:

1. Applicare ricette di automazione pronte all'uso per contesti PMI reali
2. Costruire workflow verticali per contabilità (fatture, riconciliazione, IVA)
3. Automatizzare il CRM (lead scoring, follow-up, pipeline management)
4. Gestire l'e-commerce (ordini, inventario, report vendite)
5. Automatizzare l'HR (payroll check, ferie, onboarding/offboarding)
6. Adattare ricette generiche al contesto specifico dell'azienda

---

## Lab Environment Setup

```bash
# Python per backend delle ricette
pip install httpx pandas openpyxl jinja2 structlog schedule

# n8n per workflow orchestration
# (già avviato dal tutorial 09 o 08)
docker run -d --name n8n-ricette -p 5679:5678 \
  -e N8N_ENCRYPTION_KEY="$(openssl rand -hex 32)" \
  n8nio/n8n:latest
```

---

## Analogia Introduttiva

> **Le ricette PMI sono come i template di una cucina professionale**:
> uno chef stellato non reinventa il ragù ogni volta — ha una ricetta base
> che adatta agli ingredienti del giorno (tipologia cliente, volume dati, tool disponibili).
>
> Una **ricetta di automazione** fa lo stesso:
> "Ricevuta fattura → estrazione dati → verifica IVA → registrazione contabile"
> è un pattern che funziona per il dentista, la falegnameria e il consulente IT.
> Cambia solo il modo in cui la fattura arriva (email, PDF, API, EDI),
> ma la logica di business è la stessa.
>
> Il valore delle ricette è **time-to-value**: invece di progettare da zero,
> parti da qualcosa che funziona e personalizza il 20% che è unico.

---

## Architettura Ricette PMI

```
┌─────────────────────────────────────────────────────────────────────┐
│                    RICETTE PER DOMINIO PMI                           │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                  CONTABILITÀ                                    │ │
│  │  Fattura → OCR/Parse → Verifica IVA → Registra → Archivia      │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                     CRM                                         │ │
│  │  Lead → Score → Nurture → Pipeline → Close → Customer          │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                  E-COMMERCE                                     │ │
│  │  Ordine → Verifica Stock → Fulfillment → Tracking → Review     │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                      HR                                         │ │
│  │  Richiesta → Approvazione → Aggiornamento → Notifica → Log     │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## PART A — Ricette Contabilità

### A1 — Ricetta: Fatture Passive Automatizzate

```python
# ricette/contabilita/fatture_passive.py
"""
Ricetta: Fattura passiva in arrivo via email
→ Parse PDF → Estrai importi → Verifica IVA → Genera entry contabile
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

@dataclass
class FatturaPassiva:
    numero: str
    fornitore: str
    partita_iva_fornitore: str
    data_emissione: str
    imponibile: Decimal
    iva_pct: Decimal
    iva_importo: Decimal
    totale: Decimal
    scadenza: str

def verifica_coerenza_iva(fattura: FatturaPassiva, tolleranza: Decimal = Decimal("0.02")) -> list[str]:
    """Verifica che IVA = imponibile × aliquota. Restituisce lista di anomalie."""
    anomalie = []
    iva_calcolata = (fattura.imponibile * fattura.iva_pct / 100).quantize(
        Decimal("0.01"), ROUND_HALF_UP
    )
    if abs(iva_calcolata - fattura.iva_importo) > tolleranza:
        anomalie.append(
            f"IVA non coerente: dichiarata €{fattura.iva_importo}, "
            f"calcolata €{iva_calcolata} (diff: €{abs(iva_calcolata - fattura.iva_importo)})"
        )
    totale_calcolato = fattura.imponibile + fattura.iva_importo
    if abs(totale_calcolato - fattura.totale) > tolleranza:
        anomalie.append(
            f"Totale non coerente: dichiarato €{fattura.totale}, "
            f"calcolato €{totale_calcolato}"
        )
    aliquote_it = {Decimal("0"), Decimal("4"), Decimal("5"), Decimal("10"), Decimal("22")}
    if fattura.iva_pct not in aliquote_it:
        anomalie.append(f"Aliquota IVA inusuale: {fattura.iva_pct}% (attese: {aliquote_it})")
    return anomalie

def genera_entry_contabile(fattura: FatturaPassiva, conto_costi: str = "640") -> dict:
    """Genera la prima nota contabile doppio corredo."""
    return {
        "tipo": "primanota",
        "data": fattura.data_emissione,
        "numero_documento": fattura.numero,
        "fornitore": fattura.fornitore,
        "righe": [
            {
                "conto": conto_costi,
                "descrizione": f"Costi fattura {fattura.numero} - {fattura.fornitore}",
                "dare": str(fattura.imponibile),
                "avere": "0.00",
            },
            {
                "conto": "604",
                "descrizione": f"IVA a credito {fattura.iva_pct}%",
                "dare": str(fattura.iva_importo),
                "avere": "0.00",
            },
            {
                "conto": "400",
                "descrizione": f"Debito verso {fattura.fornitore}",
                "dare": "0.00",
                "avere": str(fattura.totale),
            },
        ],
        "totale_dare": str(fattura.totale),
        "totale_avere": str(fattura.totale),
        "in_pareggio": fattura.totale == fattura.totale,
    }

def estrai_scadenze_mese(fatture: list[FatturaPassiva], anno: int, mese: int) -> list[FatturaPassiva]:
    """Filtra fatture in scadenza in un dato mese."""
    prefisso = f"{anno}-{mese:02d}"
    return [f for f in fatture if f.scadenza.startswith(prefisso)]

# DEMO
if __name__ == "__main__":
    fattura = FatturaPassiva(
        numero="2026/001", fornitore="Fornitore SRL",
        partita_iva_fornitore="12345678901",
        data_emissione="2026-01-10", imponibile=Decimal("1000.00"),
        iva_pct=Decimal("22"), iva_importo=Decimal("220.00"),
        totale=Decimal("1220.00"), scadenza="2026-02-10",
    )
    anomalie = verifica_coerenza_iva(fattura)
    if anomalie:
        for a in anomalie:
            print(f"⚠ ANOMALIA: {a}")
    else:
        print("✅ Fattura verificata — nessuna anomalia IVA")
        entry = genera_entry_contabile(fattura)
        print(f"Prima nota: {len(entry['righe'])} righe, totale €{entry['totale_dare']}")
```

---

## PART B — Ricette CRM

### B1 — Ricetta: Lead Scoring Automatico

```python
# ricette/crm/lead_scoring.py
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

@dataclass
class Lead:
    id: str
    email: str
    nome: str
    azienda: str
    dimensione_azienda: str     # "1-10" | "11-50" | "51-200" | "200+"
    settore: str
    interesse: list[str]        # ["pricing", "demo", "trial", "contact"]
    fonte: str                  # "form" | "linkedin" | "referral" | "evento"
    numero_visite: int
    download_risorse: int
    risposto_email: bool
    data_primo_contatto: date
    budget_stimato: str         # "< 1k" | "1k-5k" | "5k-20k" | "> 20k"

@dataclass
class RisultatoScore:
    lead_id: str
    punteggio: int
    categoria: str              # "cold" | "warm" | "hot" | "sql"
    azioni_consigliate: list[str]
    motivazioni: dict[str, int]

def calcola_score_lead(lead: Lead) -> RisultatoScore:
    """
    Formula di lead scoring basata su BANT + engagement:
    Budget, Authority (dimensione), Need (settore/interesse), Timeline (reattività)
    """
    motivazioni: dict[str, int] = {}
    punteggio = 0

    # Budget
    budget_punti = {"< 1k": 5, "1k-5k": 15, "5k-20k": 25, "> 20k": 35}
    p = budget_punti.get(lead.budget_stimato, 0)
    punteggio += p
    motivazioni["budget"] = p

    # Dimensione azienda (Authority proxy)
    dim_punti = {"1-10": 5, "11-50": 15, "51-200": 20, "200+": 25}
    p = dim_punti.get(lead.dimensione_azienda, 0)
    punteggio += p
    motivazioni["dimensione"] = p

    # Engagement digitale
    engagement = min(20, lead.numero_visite * 2 + lead.download_risorse * 5)
    punteggio += engagement
    motivazioni["engagement"] = engagement

    # Segnali di interesse
    segnali_alto_valore = {"pricing", "demo", "trial"}
    segnali_trovati = len(set(lead.interesse) & segnali_alto_valore)
    p = segnali_trovati * 10
    punteggio += p
    motivazioni["segnali_interesse"] = p

    # Reattività email
    if lead.risposto_email:
        punteggio += 15
        motivazioni["risposta_email"] = 15

    # Fonte
    fonte_punti = {"referral": 20, "evento": 15, "linkedin": 10, "form": 5}
    p = fonte_punti.get(lead.fonte, 0)
    punteggio += p
    motivazioni["fonte"] = p

    # Categorizzazione
    if punteggio >= 80:
        categoria = "sql"  # Sales Qualified Lead
        azioni = ["Contatto diretto entro 24h", "Demo personalizzata", "Proposta commerciale"]
    elif punteggio >= 60:
        categoria = "hot"
        azioni = ["Email personalizzata entro 48h", "Invio case study settore", "Proposta trial"]
    elif punteggio >= 35:
        categoria = "warm"
        azioni = ["Nurturing email settimanale", "Invito webinar", "Newsletter"]
    else:
        categoria = "cold"
        azioni = ["Inserisci in sequenza nurturing automatica", "Monitoraggio passivo"]

    return RisultatoScore(
        lead_id=lead.id,
        punteggio=punteggio,
        categoria=categoria,
        azioni_consigliate=azioni,
        motivazioni=motivazioni,
    )

def segmenta_pipeline(leads: list[Lead]) -> dict[str, list[RisultatoScore]]:
    """Segmenta tutta la pipeline per categoria."""
    pipeline: dict[str, list[RisultatoScore]] = {"sql": [], "hot": [], "warm": [], "cold": []}
    for lead in leads:
        score = calcola_score_lead(lead)
        pipeline[score.categoria].append(score)
    return pipeline
```

---

## PART C — Ricette E-Commerce

### C1 — Ricetta: Pipeline Ordini Automatizzata

```python
# ricette/ecommerce/ordine_pipeline.py
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import AsyncIterator

import httpx
import structlog

log = structlog.get_logger()

class StatoOrdine(Enum):
    RICEVUTO = "ricevuto"
    PAGAMENTO_VERIFICATO = "pagamento_verificato"
    IN_PREPARAZIONE = "in_preparazione"
    SPEDITO = "spedito"
    CONSEGNATO = "consegnato"
    RESO = "reso"
    ANNULLATO = "annullato"

@dataclass
class Ordine:
    id: str
    cliente_email: str
    prodotti: list[dict]
    importo_totale: float
    stato: StatoOrdine
    data_ordine: datetime
    codice_tracciamento: str = ""

@dataclass
class EsitoStep:
    step: str
    ok: bool
    messaggio: str
    dati_aggiornati: dict

async def verifica_pagamento(ordine: Ordine, gateway_url: str) -> EsitoStep:
    """Step 1: verifica pagamento con gateway."""
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(f"{gateway_url}/payments/{ordine.id}")
            dati = resp.json()
            pagato = dati.get("status") == "captured"
            return EsitoStep(
                step="verifica_pagamento", ok=pagato,
                messaggio="Pagamento confermato" if pagato else f"Stato: {dati.get('status')}",
                dati_aggiornati={"importo_catturato": dati.get("amount", 0)},
            )
        except Exception as e:
            return EsitoStep("verifica_pagamento", False, str(e), {})

async def aggiorna_inventario(prodotti: list[dict], api_url: str) -> EsitoStep:
    """Step 2: decrementa stock prodotti."""
    errori = []
    async with httpx.AsyncClient(timeout=10) as client:
        for prodotto in prodotti:
            try:
                resp = await client.patch(
                    f"{api_url}/prodotti/{prodotto['sku']}/stock",
                    json={"decremento": prodotto["quantita"]},
                )
                if resp.status_code != 200:
                    errori.append(f"SKU {prodotto['sku']}: HTTP {resp.status_code}")
            except Exception as e:
                errori.append(f"SKU {prodotto['sku']}: {e}")
    return EsitoStep(
        step="aggiorna_inventario", ok=len(errori) == 0,
        messaggio="OK" if not errori else "; ".join(errori),
        dati_aggiornati={"prodotti_aggiornati": len(prodotti) - len(errori)},
    )

async def processa_ordine_completo(ordine: Ordine, config: dict) -> list[EsitoStep]:
    """Esegue l'intera pipeline ordine step by step."""
    risultati: list[EsitoStep] = []

    step1 = await verifica_pagamento(ordine, config["gateway_url"])
    risultati.append(step1)
    if not step1.ok:
        log.error("ordine_bloccat_pagamento", ordine_id=ordine.id)
        return risultati

    step2 = await aggiorna_inventario(ordine.prodotti, config["api_url"])
    risultati.append(step2)
    log.info("pipeline_completata",
             ordine_id=ordine.id, steps=len(risultati),
             tutti_ok=all(r.ok for r in risultati))
    return risultati
```

---

## PART D — Ricette HR

### D1 — Ricetta: Gestione Richieste Ferie

```python
# ricette/hr/gestione_ferie.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum

class StatoRichiesta(Enum):
    IN_ATTESA = "in_attesa"
    APPROVATA = "approvata"
    RIFIUTATA = "rifiutata"
    ANNULLATA = "annullata"

@dataclass
class RichiestaFerie:
    id: str
    dipendente_id: str
    data_inizio: date
    data_fine: date
    tipo: str               # "ferie" | "permesso" | "malattia" | "rol"
    note: str = ""

    def giorni_lavorativi(self) -> int:
        """Conta giorni lavorativi (lun-ven) nel periodo."""
        giorni = 0
        corrente = self.data_inizio
        while corrente <= self.data_fine:
            if corrente.weekday() < 5:  # 0-4 = lun-ven
                giorni += 1
            corrente += timedelta(days=1)
        return giorni

@dataclass
class SaldoFerie:
    dipendente_id: str
    anno: int
    giorni_totali: float
    giorni_usati: float
    giorni_pianificati: float

    def giorni_disponibili(self) -> float:
        return self.giorni_totali - self.giorni_usati - self.giorni_pianificati

def valida_richiesta(richiesta: RichiestaFerie, saldo: SaldoFerie) -> list[str]:
    """Restituisce lista di errori. Lista vuota = richiesta valida."""
    errori = []
    if richiesta.data_inizio > richiesta.data_fine:
        errori.append("Data inizio successiva a data fine")
    if richiesta.data_inizio < date.today():
        errori.append("Non si possono richiedere ferie nel passato")
    giorni_richiesti = richiesta.giorni_lavorativi()
    if richiesta.tipo == "ferie" and giorni_richiesti > saldo.giorni_disponibili():
        errori.append(
            f"Saldo insufficiente: richiesti {giorni_richiesti} giorni, "
            f"disponibili {saldo.giorni_disponibili()}"
        )
    if richiesta.tipo == "ferie" and richiesta.data_inizio < date.today() + timedelta(days=3):
        errori.append("Le ferie richiedono almeno 3 giorni di preavviso")
    return errori

def calcola_copertura_team(richieste_approvate: list[RichiestaFerie],
                            dimensione_team: int, soglia_min_pct: float = 0.6) -> list[tuple[date, float]]:
    """
    Identifica giorni con copertura team sotto soglia.
    Restituisce lista di (giorno, pct_presente).
    """
    giorni_critici = []
    if not richieste_approvate:
        return giorni_critici
    data_min = min(r.data_inizio for r in richieste_approvate)
    data_max = max(r.data_fine for r in richieste_approvate)
    corrente = data_min
    while corrente <= data_max:
        if corrente.weekday() < 5:
            assenti = sum(1 for r in richieste_approvate
                         if r.data_inizio <= corrente <= r.data_fine)
            pct_presente = (dimensione_team - assenti) / dimensione_team
            if pct_presente < soglia_min_pct:
                giorni_critici.append((corrente, pct_presente))
        corrente += timedelta(days=1)
    return giorni_critici


if __name__ == "__main__":
    saldo = SaldoFerie("EMP-001", 2026, giorni_totali=20, giorni_usati=5, giorni_pianificati=3)
    richiesta = RichiestaFerie(
        id="RIC-001", dipendente_id="EMP-001",
        data_inizio=date(2026, 8, 3), data_fine=date(2026, 8, 14),
        tipo="ferie",
    )
    errori = valida_richiesta(richiesta, saldo)
    if errori:
        for e in errori:
            print(f"❌ {e}")
    else:
        giorni = richiesta.giorni_lavorativi()
        print(f"✅ Richiesta valida: {giorni} giorni lavorativi")
        print(f"   Saldo dopo approvazione: {saldo.giorni_disponibili() - giorni} giorni")
```

---

## Esercizi

### Esercizio 1 — Ricetta Contabilità: Report IVA Mensile (25 min)

Implementa `genera_report_iva(fatture, anno, mese)` che:
- Raggruppa fatture per aliquota IVA (0%, 4%, 10%, 22%)
- Calcola imponibile totale e IVA totale per aliquota
- Restituisce un dizionario con le liquidazioni da versare
- Genera un CSV con le righe di dettaglio

### Esercizio 2 — Ricetta CRM: Sequenza Follow-Up (20 min)

Implementa `pianifica_followup(lead, data_primo_contatto)` che:
- Per lead "hot": schedule email a +1gg, +3gg, +7gg
- Per lead "warm": schedule email a +3gg, +10gg, +21gg
- Per lead "cold": schedule email a +7gg, +30gg
- Restituisce lista di `{"data": ..., "template": ..., "canale": ...}`

### Esercizio 3 — Ricetta HR: Calendario Assenze Team (20 min)

Dato un team di 8 persone con richieste ferie diverse:
1. Carica le richieste da un CSV (crea dati di test realistici per agosto)
2. Chiama `calcola_copertura_team()` con soglia 60%
3. Stampa i giorni critici con il numero di persone presenti
4. Genera un alert se ci sono più di 3 giorni critici consecutivi

---

## Riferimenti

- pandas: https://pandas.pydata.org/
- httpx async: https://www.python-httpx.org/async/
- Python datetime: https://docs.python.org/3/library/datetime.html
- Modulo sorgente: `21-ricette-automazione-pmi.md`
