# Tutorial Lab — Fondamenti dell'Automazione: ROI, Idempotenza, Error Handling

> **Campo di studio:** 09-AUTOMAZIONI-FLUSSI-DI-LAVORO
> **Modulo sorgente:** `01-fondamenti-automazione.md`
> **Livello:** novice → competent
> **Tempo stimato:** 2-3 ore (lab completo)
> **Prerequisiti:** HTTP/REST/JSON basics, Python 3.11+ base, concetti file system e scheduling
> **Versioni di riferimento:** indipendente da piattaforma · Python 3.11+

---

## Obiettivi del Lab

Al termine di questo tutorial saprai:

1. Calcolare il ROI di un'automazione con il modello tempo-risparmiato vs tempo-investito
2. Applicare la matrice decisionale per scegliere l'approccio corretto (script, no-code, cron)
3. Progettare operazioni idempotenti e riconoscere quelle non-idempotenti
4. Implementare strategie di error handling: retry, fail-fast, fail-safe
5. Costruire un audit trail per tracciabilità e compliance
6. Applicare il pattern "if you do it twice, automate it" a casi reali PMI italiane

---

## Lab Environment Setup

```bash
# Nessuna dipendenza esterna necessaria per la maggior parte di questo lab
# Solo Python standard library + opzionale structlog per il logging avanzato

python3 --version  # Richiede 3.11+

# Opzionale: structlog per logging strutturato
pip install structlog==24.0.0

# Crea struttura progetto
mkdir -p fondamenti-lab/{roi,idempotency,error_handling,audit}
cd fondamenti-lab
```

---

## Analogia Introduttiva

> **L'automazione è come assumere un dipendente robot**:
> costa tempo investirlo (sviluppo, test, manutenzione),
> ma lavora 24/7 senza vacanze, non fa errori per stanchezza,
> e non dimentica i passi di un processo.
>
> La domanda NON è "posso automatizzare questo?" — tecnicamente sì, quasi sempre.
> La domanda è **"DEVO automatizzare questo? Il ROI giustifica l'investimento?"**
>
> Un'automazione che risparmia 10 minuti alla settimana ma richiede
> 40 ore di sviluppo ha un payback di **4 anni**. Non vale.
> Un'automazione che risparmia 2 ore al giorno e richiede 8 ore = payback **4 giorni**. Vale sempre.

---

## PART A — Calcolo ROI

### A1 — Modello ROI Semplificato

```
FORMULA ROI AUTOMAZIONE:

  COSTO = (Ore sviluppo × tariffa oraria) + (Ore manutenzione/anno × tariffa × anni)
  RISPARMIO = Ore risparmiate/esecuzione × esecuzioni/anno × tariffa oraria × anni
  
  ROI = (RISPARMIO - COSTO) / COSTO × 100%
  PAYBACK = COSTO / (Risparmio annuo)
  
  SOGLIA: payback < 6 mesi = investimento ottimo
          payback 6-18 mesi = valutare opportunità costo
          payback > 18 mesi = spesso non vale (a meno di compliance/qualità)
```

### A2 — ROI Calculator Python

```python
#!/usr/bin/env python3
# file: roi/roi_calculator.py
"""
Calcolatore ROI per automazioni.
Implementa il modello: (Tempo risparmiato × valore) vs (Tempo investito × costo)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ParametriROI:
    """Parametri per il calcolo ROI di un'automazione."""
    nome: str
    
    # Processo manuale attuale
    ore_per_esecuzione: float    # ore umane per esecuzione manuale
    esecuzioni_settimana: float  # quante volte si esegue a settimana
    tariffa_oraria: float        # costo orario del personale (€/h)
    tasso_errore_manuale: float  # % di errori nel processo manuale (es. 0.05 = 5%)
    costo_per_errore: float      # costo medio di correzione di un errore (€)
    
    # Investimento automazione
    ore_sviluppo: float          # ore per sviluppare l'automazione
    ore_manutenzione_anno: float # ore/anno manutenzione e aggiornamenti
    anni_orizzonte: int          # orizzonte di valutazione (anni)
    
    # Opzionale: risparmio qualitativo
    valore_compliance: float = 0.0    # valore annuo della compliance/audit trail
    valore_scalabilita: float = 0.0   # valore annuo della scalabilità


@dataclass
class RisultatoROI:
    """Risultato del calcolo ROI."""
    nome: str
    costo_totale: float
    risparmio_tempo: float
    risparmio_errori: float
    risparmio_totale: float
    roi_percentuale: float
    payback_mesi: float
    raccomandazione: str
    dettaglio: dict = field(default_factory=dict)


def calcola_roi(params: ParametriROI) -> RisultatoROI:
    """Calcola il ROI completo di un'automazione."""
    ore_risparmiate_anno = params.ore_per_esecuzione * params.esecuzioni_settimana * 52
    
    # Costi
    costo_sviluppo = params.ore_sviluppo * params.tariffa_oraria
    costo_manutenzione_totale = (
        params.ore_manutenzione_anno * params.tariffa_oraria * params.anni_orizzonte
    )
    costo_totale = costo_sviluppo + costo_manutenzione_totale
    
    # Risparmio tempo
    risparmio_tempo_anno = ore_risparmiate_anno * params.tariffa_oraria
    risparmio_tempo_totale = risparmio_tempo_anno * params.anni_orizzonte
    
    # Risparmio errori
    errori_anno = params.esecuzioni_settimana * 52 * params.tasso_errore_manuale
    risparmio_errori_anno = errori_anno * params.costo_per_errore
    risparmio_errori_totale = risparmio_errori_anno * params.anni_orizzonte
    
    # Risparmio qualitativo
    risparmio_qualitativo = (
        params.valore_compliance + params.valore_scalabilita
    ) * params.anni_orizzonte
    
    # Totali
    risparmio_totale = risparmio_tempo_totale + risparmio_errori_totale + risparmio_qualitativo
    
    roi = ((risparmio_totale - costo_totale) / costo_totale * 100) if costo_totale > 0 else 0
    payback_mesi = (costo_totale / (risparmio_tempo_anno + risparmio_errori_anno) * 12
                    if (risparmio_tempo_anno + risparmio_errori_anno) > 0 else float("inf"))
    
    # Raccomandazione
    if payback_mesi < 6:
        raccomandazione = "OTTIMO — automatizzare subito"
    elif payback_mesi < 18:
        raccomandazione = "POSITIVO — automatizzare con priorità media"
    elif payback_mesi < 36:
        raccomandazione = "BORDERLINE — valutare costi opportunità"
    else:
        raccomandazione = "NON CONSIGLIATO — a meno di requisiti compliance/qualità"
    
    return RisultatoROI(
        nome=params.nome,
        costo_totale=costo_totale,
        risparmio_tempo=risparmio_tempo_totale,
        risparmio_errori=risparmio_errori_totale,
        risparmio_totale=risparmio_totale,
        roi_percentuale=roi,
        payback_mesi=payback_mesi,
        raccomandazione=raccomandazione,
        dettaglio={
            "ore_risparmiate_anno": ore_risparmiate_anno,
            "errori_eliminati_anno": errori_anno,
            "costo_sviluppo": costo_sviluppo,
            "costo_manutenzione_totale": costo_manutenzione_totale,
        }
    )


def stampa_report(r: RisultatoROI) -> None:
    """Stampa il report ROI formattato."""
    print(f"\n{'=' * 60}")
    print(f"ROI ANALYSIS: {r.nome}")
    print(f"{'=' * 60}")
    print(f"INVESTIMENTO:")
    print(f"  Costo totale ({r.dettaglio.get('costo_sviluppo', 0):.0f}€ sviluppo "
          f"+ {r.dettaglio.get('costo_manutenzione_totale', 0):.0f}€ manutenzione):")
    print(f"  → {r.costo_totale:,.0f}€")
    print(f"\nRISPARMIO STIMATO:")
    print(f"  Risparmio tempo:    {r.risparmio_tempo:>10,.0f}€")
    print(f"  Risparmio errori:   {r.risparmio_errori:>10,.0f}€")
    print(f"  TOTALE:             {r.risparmio_totale:>10,.0f}€")
    print(f"\nMETRICHE:")
    print(f"  ROI:                {r.roi_percentuale:>10.1f}%")
    print(f"  Payback:            {r.payback_mesi:>10.1f} mesi")
    print(f"  Ore risparmiate/a:  {r.dettaglio.get('ore_risparmiate_anno', 0):>10.0f}h")
    print(f"\nRACCOMANDAZIONE: {r.raccomandazione}")
    print(f"{'=' * 60}")


# ─── Casi d'uso PMI italiane ──────────────────────────────────────────────────

CASI_USO_PMI = [
    ParametriROI(
        nome="Riconciliazione estratti conto banca → contabilità",
        ore_per_esecuzione=3.0,
        esecuzioni_settimana=1.0,
        tariffa_oraria=35.0,
        tasso_errore_manuale=0.03,
        costo_per_errore=150.0,
        ore_sviluppo=24.0,
        ore_manutenzione_anno=8.0,
        anni_orizzonte=3,
        valore_compliance=2000.0,
    ),
    ParametriROI(
        nome="Generazione fatture XML SDI da gestionale",
        ore_per_esecuzione=0.5,
        esecuzioni_settimana=20.0,
        tariffa_oraria=25.0,
        tasso_errore_manuale=0.02,
        costo_per_errore=200.0,
        ore_sviluppo=40.0,
        ore_manutenzione_anno=12.0,
        anni_orizzonte=3,
        valore_compliance=5000.0,
    ),
    ParametriROI(
        nome="Report vendite settimanale Excel",
        ore_per_esecuzione=2.0,
        esecuzioni_settimana=1.0,
        tariffa_oraria=30.0,
        tasso_errore_manuale=0.05,
        costo_per_errore=50.0,
        ore_sviluppo=16.0,
        ore_manutenzione_anno=4.0,
        anni_orizzonte=2,
    ),
    ParametriROI(
        nome="Backup manuale file server",
        ore_per_esecuzione=0.25,
        esecuzioni_settimana=5.0,
        tariffa_oraria=20.0,
        tasso_errore_manuale=0.10,
        costo_per_errore=500.0,
        ore_sviluppo=4.0,
        ore_manutenzione_anno=2.0,
        anni_orizzonte=3,
        valore_compliance=1000.0,
    ),
]


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("ANALISI ROI — AUTOMAZIONI PMI ITALIANE")
    print("=" * 60)
    
    results = [calcola_roi(caso) for caso in CASI_USO_PMI]
    for r in sorted(results, key=lambda x: x.payback_mesi):
        stampa_report(r)
    
    print("\nRIEPILOGO (ordinato per payback):")
    print(f"{'Processo':<45} {'ROI %':>8} {'Payback':>10}")
    print("-" * 65)
    for r in sorted(results, key=lambda x: x.payback_mesi):
        print(f"{r.nome[:44]:<45} {r.roi_percentuale:>7.0f}% {r.payback_mesi:>9.1f}m")
```

### A3 — Matrice Decisionale (Quale Approccio?)

```python
#!/usr/bin/env python3
# file: roi/matrice_decisionale.py
"""
Matrice decisionale: quale approccio di automazione scegliere?
Criteri: volume, complessità logica, frequenza, manutenibilità, team skills.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum


class Approccio(str, Enum):
    CRON_BASH = "Cron + Bash/Script"
    PYTHON_SCRIPT = "Python Script"
    NO_CODE = "No-code (n8n/Make/Zapier)"
    API_INTEGRATION = "Integrazione API diretta"
    ANSIBLE = "Ansible/Terraform (IaC)"
    MESSAGE_QUEUE = "Message Queue (RabbitMQ/Kafka)"


@dataclass
class CriterioValutazione:
    volume_giornaliero: int        # numero esecuzioni/giorno
    complessita_logica: int        # 1=semplice 5=molto complessa
    team_technical_skill: int      # 1=no-code team 5=dev team esperto
    integrazioni_esterne: int      # numero di API/sistemi esterni
    latenza_richiesta_ms: int      # latenza massima accettabile (ms)
    dati_sensibili: bool           # GDPR/PII?
    intervento_umano: bool         # richiede approvazione umana?


def suggerisci_approccio(c: CriterioValutazione) -> list[tuple[Approccio, str]]:
    """Suggerisce gli approcci più adatti e il motivo."""
    suggerimenti: list[tuple[Approccio, str, int]] = []  # (approccio, motivo, score)
    
    # Cron + Bash: semplice, bassa frequenza, bassa complessità
    if c.complessita_logica <= 2 and c.volume_giornaliero <= 100 and not c.dati_sensibili:
        suggerimenti.append((
            Approccio.CRON_BASH,
            "Semplice e senza dipendenze — ideale per task OS-level",
            10 - c.complessita_logica
        ))
    
    # No-code: integrazioni multiple, team non-tecnico
    if c.integrazioni_esterne >= 2 and c.team_technical_skill <= 3 and not c.intervento_umano:
        suggerimenti.append((
            Approccio.NO_CODE,
            "Più integrazioni, team mixed — n8n/Make abbassano barriera tecnica",
            8
        ))
    
    # Python: logica complessa, team tecnico
    if c.complessita_logica >= 3 and c.team_technical_skill >= 3:
        suggerimenti.append((
            Approccio.PYTHON_SCRIPT,
            "Logica complessa — Python offre flessibilità massima e testabilità",
            7 + c.complessita_logica
        ))
    
    # Message Queue: alto volume, latenza bassa
    if c.volume_giornaliero > 10000 or c.latenza_richiesta_ms < 100:
        suggerimenti.append((
            Approccio.MESSAGE_QUEUE,
            "Alto volume o bassa latenza — message broker necessario",
            12
        ))
    
    # Ansible: configurazione infrastruttura
    if c.team_technical_skill >= 4 and not c.integrazioni_esterne:
        suggerimenti.append((
            Approccio.ANSIBLE,
            "Configurazione server/infrastruttura — IaC è la scelta giusta",
            9
        ))
    
    if not suggerimenti:
        suggerimenti.append((
            Approccio.PYTHON_SCRIPT,
            "Default: Python è l'approccio più versatile",
            5
        ))
    
    # Ordina per score decrescente
    return [(s[0], s[1]) for s in sorted(suggerimenti, key=lambda x: -x[2])]


if __name__ == "__main__":
    casi = [
        ("Invio newsletter settimanale (Mailchimp + CRM)", CriterioValutazione(
            volume_giornaliero=1, complessita_logica=2, team_technical_skill=2,
            integrazioni_esterne=3, latenza_richiesta_ms=60000, dati_sensibili=True,
            intervento_umano=False
        )),
        ("Backup DB ogni notte + upload S3", CriterioValutazione(
            volume_giornaliero=1, complessita_logica=2, team_technical_skill=4,
            integrazioni_esterne=1, latenza_richiesta_ms=600000, dati_sensibili=False,
            intervento_umano=False
        )),
        ("Processing ordini e-commerce real-time (1000+/giorno)", CriterioValutazione(
            volume_giornaliero=1000, complessita_logica=4, team_technical_skill=4,
            integrazioni_esterne=4, latenza_richiesta_ms=500, dati_sensibili=True,
            intervento_umano=False
        )),
    ]
    
    for nome, criterio in casi:
        print(f"\n{'=' * 60}")
        print(f"Caso: {nome}")
        suggerimenti = suggerisci_approccio(criterio)
        for i, (approccio, motivo) in enumerate(suggerimenti[:3], 1):
            print(f"  {i}. {approccio.value}")
            print(f"     → {motivo}")
```

---

## PART B — Idempotenza

### B1 — Idempotente vs Non-Idempotente

```python
#!/usr/bin/env python3
# file: idempotency/demo_idempotenza.py
"""
Dimostra la differenza tra operazioni idempotenti e non-idempotenti.
Un'operazione è idempotente se applicarla N volte produce lo stesso effetto di 1 volta.
"""
import json
import os
import sqlite3
from pathlib import Path

# ─── Operazioni NON idempotenti (pericolose in retry) ──────────────────────────

def aggiungi_riga_senza_dedup(db: sqlite3.Connection, ordine_id: str, importo: float) -> int:
    """
    NON idempotente: ogni chiamata aggiunge una nuova riga.
    Se l'INSERT fallisce a metà e viene ritentato → doppio addebito!
    """
    cur = db.execute(
        "INSERT INTO transazioni (ordine_id, importo) VALUES (?, ?)",
        (ordine_id, importo)
    )
    db.commit()
    return cur.lastrowid


def incrementa_contatore(db: sqlite3.Connection, chiave: str) -> int:
    """
    NON idempotente: ogni chiamata incrementa il contatore.
    Retry = contatore sbagliato.
    """
    db.execute(
        "UPDATE contatori SET valore = valore + 1 WHERE chiave = ?",
        (chiave,)
    )
    db.commit()
    row = db.execute("SELECT valore FROM contatori WHERE chiave = ?", (chiave,)).fetchone()
    return row[0] if row else 0


# ─── Versioni idempotenti (safe in retry) ─────────────────────────────────────

def aggiungi_transazione_idempotente(
    db: sqlite3.Connection,
    idempotency_key: str,
    ordine_id: str,
    importo: float
) -> dict:
    """
    Idempotente: usa idempotency_key per prevenire duplicati.
    Stessa chiave → stesso risultato, zero effetti collaterali.
    """
    # Controlla se esiste già
    esistente = db.execute(
        "SELECT id, importo FROM transazioni WHERE idempotency_key = ?",
        (idempotency_key,)
    ).fetchone()
    
    if esistente:
        return {"id": esistente[0], "importo": esistente[1], "duplicato": True}
    
    cur = db.execute(
        "INSERT INTO transazioni (idempotency_key, ordine_id, importo) VALUES (?, ?, ?)",
        (idempotency_key, ordine_id, importo)
    )
    db.commit()
    return {"id": cur.lastrowid, "importo": importo, "duplicato": False}


def set_configurazione(db: sqlite3.Connection, chiave: str, valore: str) -> None:
    """
    Idempotente: SET è sempre idempotente, INCREMENT non lo è.
    Stessa chiamata N volte = stato finale identico.
    """
    db.execute(
        "INSERT INTO configurazione (chiave, valore) VALUES (?, ?) "
        "ON CONFLICT(chiave) DO UPDATE SET valore = excluded.valore",
        (chiave, valore)
    )
    db.commit()


def crea_directory_idempotente(path: str) -> bool:
    """
    Idempotente: mkdir -p non fallisce se la directory esiste già.
    os.makedirs(exist_ok=True) è la versione Python.
    """
    Path(path).mkdir(parents=True, exist_ok=True)
    return True  # Sempre True — non importa se esisteva già


def scrivi_file_idempotente(path: str, contenuto: str) -> None:
    """
    Idempotente: sovrascrivere un file con lo stesso contenuto è sicuro.
    Atomico: scrivi su temp file, poi rinomina (rename è atomico su POSIX).
    """
    target = Path(path)
    temp = target.with_suffix(".tmp")
    temp.write_text(contenuto, encoding="utf-8")
    temp.replace(target)  # Atomico su POSIX


# ─── Demo ─────────────────────────────────────────────────────────────────────

def demo():
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE transazioni (id INTEGER PRIMARY KEY, idempotency_key TEXT UNIQUE, ordine_id TEXT, importo REAL)")
    db.execute("CREATE TABLE configurazione (chiave TEXT PRIMARY KEY, valore TEXT)")
    db.execute("CREATE TABLE contatori (chiave TEXT PRIMARY KEY, valore INTEGER DEFAULT 0)")
    db.execute("INSERT INTO contatori VALUES ('pagine_visitate', 0)")
    db.commit()
    
    print("=== DEMO IDEMPOTENZA ===\n")
    
    # Test 1: Non idempotente (simula retry)
    print("1. Transazione NON idempotente (simula 3 retry):")
    for i in range(3):
        try:
            aggiungi_riga_senza_dedup(db, "ORD-001", 49.99)
        except Exception as e:
            print(f"   Tentativo {i+1}: ERRORE — {e}")
    count = db.execute("SELECT COUNT(*) FROM transazioni WHERE ordine_id='ORD-001'").fetchone()[0]
    print(f"   Righe create: {count} (atteso: 1, pericoloso!)")
    
    # Pulizia
    db.execute("DELETE FROM transazioni")
    db.commit()
    
    # Test 2: Idempotente (stesso retry, risultato corretto)
    print("\n2. Transazione IDEMPOTENTE (simula 3 retry):")
    for i in range(3):
        result = aggiungi_transazione_idempotente(db, "idem-key-001", "ORD-001", 49.99)
        print(f"   Tentativo {i+1}: id={result['id']}, duplicato={result['duplicato']}")
    count = db.execute("SELECT COUNT(*) FROM transazioni").fetchone()[0]
    print(f"   Righe create: {count} (atteso: 1, corretto!)")
    
    # Test 3: SET vs INCREMENT
    print("\n3. Configurazione: SET idempotente vs UPSERT:")
    for _ in range(5):
        set_configurazione(db, "max_retry", "3")
    row = db.execute("SELECT COUNT(*) FROM configurazione WHERE chiave='max_retry'").fetchone()
    print(f"   Righe configurazione: {row[0]} (atteso: 1, corretto!)")
    
    print("\n=== RIEPILOGO IDEMPOTENZA ===")
    print("  Idempotenti:     SET, DELETE, GET, mkdir -p, file overwrite")
    print("  Non idempotenti: INSERT, INCREMENT, APPEND, POST senza idempotency key")
    print("  Regola:          Ogni task automatizzato DEVE essere idempotente")

if __name__ == "__main__":
    demo()
```

---

## PART C — Error Handling

### C1 — Pattern Fail-Fast vs Fail-Safe

```python
#!/usr/bin/env python3
# file: error_handling/patterns.py
"""
Pattern di error handling per automazioni.

FAIL-FAST: fallisci immediatamente e rumorosamente.
  Usato in: test, validazione input, operazioni critiche irreversibili.
  Vantaggio: l'errore è visibile subito, non nascosto.

FAIL-SAFE: continua con degradazione elegante.
  Usato in: produzione, processi batch, elaborazione di liste.
  Vantaggio: un errore non blocca tutto.

RETRY: riprova automaticamente dopo fallimento transitorio.
  Usato per: timeout rete, servizi temporaneamente down.
  NON usare per: errori permanenti (400 Bad Request, dati invalidi).
"""
from __future__ import annotations

import time
import random
import logging
from dataclasses import dataclass
from typing import Callable, Optional, TypeVar

T = TypeVar("T")
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")


# ─── Fail-Fast ────────────────────────────────────────────────────────────────

def valida_ordine_fail_fast(ordine: dict) -> None:
    """
    Fail-fast: solleva eccezione al primo problema.
    Usato in validazione input — non processare dati invalidi.
    """
    if not ordine.get("ordine_id"):
        raise ValueError("ordine_id obbligatorio")
    if not isinstance(ordine.get("importo"), (int, float)):
        raise TypeError(f"importo deve essere numerico, ricevuto: {type(ordine.get('importo'))}")
    if ordine["importo"] <= 0:
        raise ValueError(f"importo deve essere > 0, ricevuto: {ordine['importo']}")
    if not ordine.get("cliente_id"):
        raise ValueError("cliente_id obbligatorio")


# ─── Fail-Safe ────────────────────────────────────────────────────────────────

def processa_batch_fail_safe(
    ordini: list[dict],
    processor_fn: Callable[[dict], bool],
) -> dict:
    """
    Fail-safe: processa tutti gli ordini, raccoglie gli errori.
    Gli ordini che falliscono non bloccano gli altri.
    """
    ok = []
    failed = []
    
    for ordine in ordini:
        try:
            success = processor_fn(ordine)
            if success:
                ok.append(ordine["ordine_id"])
            else:
                failed.append({"ordine_id": ordine["ordine_id"], "error": "processing_returned_false"})
        except Exception as e:
            logger.error("Ordine fallito: %s — %s", ordine.get("ordine_id", "?"), e)
            failed.append({"ordine_id": ordine.get("ordine_id", "?"), "error": str(e)})
    
    result = {
        "totale": len(ordini),
        "ok": len(ok),
        "failed": len(failed),
        "ok_ids": ok,
        "failed_details": failed,
    }
    
    if failed:
        logger.warning("Batch completato con %d errori su %d", len(failed), len(ordini))
    else:
        logger.info("Batch completato: tutti %d ok", len(ordini))
    
    return result


# ─── Retry semplice ───────────────────────────────────────────────────────────

@dataclass
class RetryConfig:
    max_tentativi: int = 3
    attesa_iniziale_s: float = 1.0
    moltiplicatore: float = 2.0
    jitter_massimo_s: float = 0.5
    errori_retriable: tuple = (ConnectionError, TimeoutError)


def con_retry(
    fn: Callable[[], T],
    config: RetryConfig = RetryConfig(),
    nome: str = "operazione",
) -> T:
    """
    Esegue fn con retry + exponential backoff + jitter.
    Riprova solo per errori retriable (es. rete).
    """
    ultimo_errore: Optional[Exception] = None
    
    for tentativo in range(1, config.max_tentativi + 1):
        try:
            result = fn()
            if tentativo > 1:
                logger.info("%s: successo al tentativo %d", nome, tentativo)
            return result
        except config.errori_retriable as e:
            ultimo_errore = e
            if tentativo < config.max_tentativi:
                attesa = (
                    config.attesa_iniziale_s * (config.moltiplicatore ** (tentativo - 1))
                    + random.uniform(0, config.jitter_massimo_s)
                )
                logger.warning("%s: tentativo %d/%d fallito (%s). Retry in %.1fs",
                               nome, tentativo, config.max_tentativi, e, attesa)
                time.sleep(attesa)
            else:
                logger.error("%s: tutti i tentativi esauriti", nome)
        except Exception as e:
            # Errore NON retriable → fail-fast
            logger.error("%s: errore non retriable — %s", nome, e)
            raise
    
    raise RuntimeError(f"{nome}: fallito dopo {config.max_tentativi} tentativi") from ultimo_errore


# ─── Demo ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Test fail-fast
    print("=== FAIL-FAST ===")
    try:
        valida_ordine_fail_fast({"ordine_id": "ORD-1", "importo": -5, "cliente_id": "C-1"})
    except ValueError as e:
        print(f"  Errore catturato: {e}")
    
    # Test fail-safe batch
    print("\n=== FAIL-SAFE BATCH ===")
    def processor_mock(ordine: dict) -> bool:
        if "FAIL" in ordine.get("ordine_id", ""):
            raise RuntimeError("Simulazione errore")
        return True
    
    ordini_test = [
        {"ordine_id": "ORD-001", "importo": 100.0},
        {"ordine_id": "ORD-FAIL-002", "importo": 200.0},
        {"ordine_id": "ORD-003", "importo": 300.0},
        {"ordine_id": "ORD-FAIL-004", "importo": 400.0},
        {"ordine_id": "ORD-005", "importo": 500.0},
    ]
    
    result = processa_batch_fail_safe(ordini_test, processor_mock)
    print(f"  Risultato: {result['ok']}/{result['totale']} ok, {result['failed']} falliti")
    
    # Test retry
    print("\n=== RETRY ===")
    tentativo_count = [0]
    def servizio_instabile():
        tentativo_count[0] += 1
        if tentativo_count[0] < 3:
            raise ConnectionError(f"Servizio non raggiungibile (tentativo {tentativo_count[0]})")
        return "successo"
    
    result = con_retry(servizio_instabile, nome="API_Pagamenti")
    print(f"  Risultato: {result}")
```

---

## PART D — Audit Trail

### D1 — Struttura Audit Log

```python
#!/usr/bin/env python3
# file: audit/audit_logger.py
"""
Audit trail per automazioni: chi ha fatto cosa, quando, con quale risultato.
Requisiti GDPR/compliance: immutabile, strutturato, ricercabile.
"""
from __future__ import annotations

import json
import sqlite3
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Optional


@dataclass
class EventoAudit:
    """Singolo evento nel audit trail."""
    evento_id: str
    timestamp_iso: str
    processo: str          # es. "riconciliazione_banca"
    azione: str            # es. "elabora_transazione"
    esito: str             # "success" | "failure" | "skip"
    entita_tipo: str       # es. "transazione"
    entita_id: str         # es. "TRX-2026-001"
    utente_o_servizio: str
    dettagli: dict         # payload JSON (senza PII!)
    errore: Optional[str]  # se esito=="failure"
    durata_ms: Optional[int]


class AuditLogger:
    """
    Logger audit su SQLite (produzione: PostgreSQL/BigQuery/Elasticsearch).
    Principi:
    - Immutabile: nessun UPDATE/DELETE
    - Strutturato: JSON searchable
    - Senza PII: niente nomi/email/CF nel log
    """

    def __init__(self, db_path: Path):
        self.conn = sqlite3.connect(str(db_path), isolation_level=None)
        self._init_schema()

    def _init_schema(self) -> None:
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                evento_id       TEXT PRIMARY KEY,
                timestamp_iso   TEXT NOT NULL,
                processo        TEXT NOT NULL,
                azione          TEXT NOT NULL,
                esito           TEXT NOT NULL,
                entita_tipo     TEXT,
                entita_id       TEXT,
                utente_o_servizio TEXT NOT NULL,
                dettagli        TEXT,
                errore          TEXT,
                durata_ms       INTEGER
            )
        """)
        self.conn.execute("CREATE INDEX IF NOT EXISTS audit_processo ON audit_log(processo, timestamp_iso)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS audit_entita ON audit_log(entita_tipo, entita_id)")

    def registra(self, evento: EventoAudit) -> None:
        """Registra un evento nell'audit trail (append-only)."""
        self.conn.execute(
            """INSERT INTO audit_log
               (evento_id, timestamp_iso, processo, azione, esito, entita_tipo, entita_id,
                utente_o_servizio, dettagli, errore, durata_ms)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (
                evento.evento_id,
                evento.timestamp_iso,
                evento.processo,
                evento.azione,
                evento.esito,
                evento.entita_tipo,
                evento.entita_id,
                evento.utente_o_servizio,
                json.dumps(evento.dettagli),
                evento.errore,
                evento.durata_ms,
            )
        )

    def cerca(
        self,
        processo: Optional[str] = None,
        entita_id: Optional[str] = None,
        esito: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict]:
        """Cerca eventi nell'audit trail."""
        query = "SELECT * FROM audit_log WHERE 1=1"
        params = []
        if processo:
            query += " AND processo = ?"
            params.append(processo)
        if entita_id:
            query += " AND entita_id = ?"
            params.append(entita_id)
        if esito:
            query += " AND esito = ?"
            params.append(esito)
        query += f" ORDER BY timestamp_iso DESC LIMIT {limit}"
        
        rows = self.conn.execute(query, params).fetchall()
        cols = [d[0] for d in self.conn.execute("SELECT * FROM audit_log LIMIT 0").description]
        return [dict(zip(cols, row)) for row in rows]


# ─── Context manager per audit automatico ─────────────────────────────────────

from contextlib import contextmanager

@contextmanager
def audit_step(
    logger: AuditLogger,
    processo: str,
    azione: str,
    entita_tipo: str,
    entita_id: str,
    servizio: str = "automation",
    dettagli: Optional[dict] = None,
):
    """
    Context manager per auditare un'operazione automaticamente.
    Registra start, durata, esito (success/failure) e errore.
    """
    start = time.monotonic()
    evento = EventoAudit(
        evento_id=str(uuid.uuid4()),
        timestamp_iso=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        processo=processo,
        azione=azione,
        esito="success",  # aggiornato in finally
        entita_tipo=entita_tipo,
        entita_id=entita_id,
        utente_o_servizio=servizio,
        dettagli=dettagli or {},
        errore=None,
        durata_ms=None,
    )
    try:
        yield evento
        evento.esito = "success"
    except Exception as e:
        evento.esito = "failure"
        evento.errore = f"{type(e).__name__}: {str(e)}"
        raise
    finally:
        evento.durata_ms = int((time.monotonic() - start) * 1000)
        logger.registra(evento)


# Demo
if __name__ == "__main__":
    db_path = Path("/tmp/audit_demo.db")
    audit = AuditLogger(db_path)
    
    print("=== DEMO AUDIT TRAIL ===\n")
    
    # Simula elaborazione batch con audit
    transazioni = [
        {"id": "TRX-001", "importo": 150.00, "tipo": "credito"},
        {"id": "TRX-002", "importo": -999.99, "tipo": "INVALIDO"},
        {"id": "TRX-003", "importo": 75.50, "tipo": "debito"},
    ]
    
    for trx in transazioni:
        try:
            with audit_step(
                audit,
                processo="riconciliazione_banca",
                azione="elabora_transazione",
                entita_tipo="transazione",
                entita_id=trx["id"],
                dettagli={"tipo": trx["tipo"], "importo_range": ">0" if trx["importo"] > 0 else "<0"}
            ):
                if trx["importo"] < 0:
                    raise ValueError("Importo negativo non atteso")
                time.sleep(0.01)  # Simula elaborazione
                print(f"  {trx['id']}: elaborata")
        except ValueError as e:
            print(f"  {trx['id']}: ERRORE — {e}")
    
    # Mostra audit trail
    print("\nAUDIT TRAIL:")
    eventi = audit.cerca(processo="riconciliazione_banca")
    for e in eventi:
        print(f"  [{e['esito']:8s}] {e['azione']} → {e['entita_id']} ({e['durata_ms']}ms)"
              + (f" | {e['errore']}" if e['errore'] else ""))
    
    failures = audit.cerca(esito="failure")
    print(f"\nTotal failures: {len(failures)}")
```

---

## Esercizi

### Esercizio 1 — ROI della tua automazione (20 min)

Calcola il ROI di un'automazione che fai manualmente nel tuo lavoro:

```python
from roi.roi_calculator import ParametriROI, calcola_roi, stampa_report

mia_automazione = ParametriROI(
    nome="...",                      # descrizione del tuo processo manuale
    ore_per_esecuzione=...,          # quante ore ci vuoi tu
    esecuzioni_settimana=...,        # quante volte alla settimana
    tariffa_oraria=30.0,             # costo orario del tuo tempo
    tasso_errore_manuale=0.05,       # stima errori
    costo_per_errore=100.0,          # costo medio correzione errore
    ore_sviluppo=...,                # ore per automatizzare
    ore_manutenzione_anno=4.0,       # ore manutenzione/anno
    anni_orizzonte=2,
)
stampa_report(calcola_roi(mia_automazione))
```

### Esercizio 2 — Rendi idempotente questa funzione (15 min)

```python
# PROBLEMA: questa funzione non è idempotente
def invia_email_benvenuto(cliente_id: str, email: str) -> None:
    """Invia email di benvenuto al nuovo cliente."""
    # Chiamata SMTP...
    pass

# TODO: Riscrivila usando un "sent_log" in Redis/SQLite
# che impedisce l'invio duplicato per lo stesso cliente_id
```

### Esercizio 3 — Audit un'operazione critica (20 min)

```python
from audit.audit_logger import AuditLogger, audit_step
from pathlib import Path

audit = AuditLogger(Path("/tmp/esercizio_audit.db"))

# Wrappa questa funzione con audit_step
def cancella_utente(utente_id: str) -> None:
    """Cancella un utente dal sistema."""
    # In realtà: soft-delete nel DB
    print(f"Utente {utente_id} cancellato")

# TODO: aggiungi audit_step intorno a cancella_utente
# e verifica che fallimenti vengano registrati con esito="failure"
```

---

## Riferimenti

- "Automate the Boring Stuff with Python" — Al Sweigart (free online)
- Martin Fowler on Idempotency: https://martinfowler.com/bliki/Idempotence.html
- Google SRE Book — Chapter 17: Testing for Reliability
- Modulo sorgente: `01-fondamenti-automazione.md`
