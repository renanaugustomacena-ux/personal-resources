# Tutorial Lab — Cost Monitoring e Budget Alert per Automazioni

> **Campo di studio:** 09-AUTOMAZIONI-FLUSSI-DI-LAVORO
> **Modulo sorgente:** `19-cost-monitoring-piattaforme.md`
> **Livello:** intermediate
> **Tempo stimato:** 2 ore
> **Prerequisiti:** Python base, CSV/JSON, Prometheus (opzionale)
> **Versioni di riferimento:** Python 3.11+ · matplotlib 3.x (opzionale)

---

## Obiettivi del Lab

Al termine di questo tutorial saprai:

1. Tracciare il costo per operazione di ogni piattaforma (n8n, Make, Zapier)
2. Implementare budget alert automatici con soglie configurabili
3. Analizzare trend di consumo e proiettare costi futuri
4. Rilevare anomalie di costo con detection euristica
5. Generare report mensili in formato CSV/JSON
6. Integrare metriche costo con Prometheus/Grafana

---

## Lab Environment Setup

```bash
python3 --version    # 3.11+
pip install matplotlib==3.9.0  # Opzionale, per grafici

mkdir -p cost-lab/{tracker,alerts,reports,data}
cd cost-lab
```

---

## Analogia Introduttiva

> **Monitorare i costi di automazione è come leggere il contatore della luce**:
> non basta sapere che il frigorifero funziona —
> devi sapere QUANTO consuma ogni elettrodomestico
> per capire dove ottimizzare.
>
> Il paradosso delle piattaforme no-code:
> "Risparmio tempo" non significa "risparmio denaro".
> Se un workflow fa 10.000 operazioni al mese e ogni operazione
> costa 0.5 centesimi, stai pagando 50€/mese.
> Forse uno script Python da 2 ore costa meno.
>
> Il **budget alert** è il timer del forno:
> ti avverte prima che il pane bruci (prima di ricevere una bolletta shock).

---

## PART A — Cost Tracker

### A1 — Modello Dati Costi

```python
#!/usr/bin/env python3
# file: tracker/cost_model.py
"""
Modello dati per tracciare costi di piattaforme di automazione.
Supporta: n8n (costo infrastruttura), Make/Zapier (costo per operazione).
"""
from __future__ import annotations

import csv
import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional
from enum import Enum


class TipoCosto(str, Enum):
    INFRASTRUTTURA = "infrastruttura"    # Server, VPS, Docker
    LICENZA = "licenza"                  # Abbonamento mensile fisso
    PER_OPERAZIONE = "per_operazione"    # Task/scenario/execution
    PER_CHIAMATA_API = "per_api_call"    # Chiamate API esterne (es. OpenAI)
    STORAGE = "storage"                  # Archiviazione dati


@dataclass
class EventoCosto:
    """Un singolo evento di costo."""
    timestamp_iso: str
    piattaforma: str           # "n8n" | "make" | "zapier" | "power_automate"
    tipo: TipoCosto
    workflow_id: str
    workflow_nome: str
    n_operazioni: int = 1
    costo_unitario_eur: float = 0.0
    costo_totale_eur: float = 0.0
    metadata: dict = field(default_factory=dict)


@dataclass
class PianoTariffario:
    """Tariffa di una piattaforma."""
    piattaforma: str
    nome_piano: str
    costo_fisso_mese: float          # € costo mensile fisso
    operazioni_incluse: int          # Operazioni incluse nel fisso
    costo_per_1000_extra: float      # € per 1000 operazioni oltre incluse
    costo_infrastruttura_mese: float # € per server/hosting (solo self-hosted)
    valuta: str = "EUR"


PIANI_STANDARD = [
    PianoTariffario("n8n_self", "Self-hosted", 0.0, 999_999_999, 0.0, 40.0),
    PianoTariffario("n8n_cloud", "Cloud Starter", 20.0, 2500, 0.0, 0.0),
    PianoTariffario("make_core", "Make Core", 9.0, 10_000, 0.49, 0.0),
    PianoTariffario("make_pro", "Make Pro", 29.0, 40_000, 0.49, 0.0),
    PianoTariffario("zapier_starter", "Zapier Starter", 29.99, 750, 1.60, 0.0),
    PianoTariffario("zapier_professional", "Zapier Professional", 73.50, 2000, 1.60, 0.0),
    PianoTariffario("power_automate", "Power Automate Premium", 15.0, 5000, 0.40, 0.0),
]


def calcola_costo_mensile(piano: PianoTariffario, operazioni_mese: int) -> float:
    """Calcola il costo mensile reale dato un numero di operazioni."""
    costo_base = piano.costo_fisso_mese + piano.costo_infrastruttura_mese
    extra = max(0, operazioni_mese - piano.operazioni_incluse)
    costo_extra = (extra / 1000) * piano.costo_per_1000_extra
    return costo_base + costo_extra


def trova_piano_ottimale(piattaforma: str, operazioni_mese: int) -> PianoTariffario:
    """Trova il piano più economico per un dato volume di operazioni."""
    piani_piattaforma = [p for p in PIANI_STANDARD if p.piattaforma.startswith(piattaforma)]
    
    if not piani_piattaforma:
        raise ValueError(f"Piattaforma non trovata: {piattaforma}")
    
    return min(piani_piattaforma, key=lambda p: calcola_costo_mensile(p, operazioni_mese))
```

### A2 — Cost Tracker con Persistenza

```python
#!/usr/bin/env python3
# file: tracker/cost_tracker.py
"""
Tracker costi con persistenza su CSV.
Accumula eventi, calcola totali, rileva anomalie.
"""
from __future__ import annotations

import csv
import json
import time
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from tracker.cost_model import EventoCosto, TipoCosto


class CostTracker:
    """
    Tracker costi append-only su CSV.
    CSV è scelto perché: leggibile, esportabile, versionabile in git.
    """

    def __init__(self, data_path: Path = Path("./data/costi.csv")):
        self._path = data_path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        
        if not self._path.exists():
            self._scrivi_header()

    def _scrivi_header(self) -> None:
        with open(self._path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self._fieldnames())
            writer.writeheader()

    def _fieldnames(self) -> list[str]:
        return [
            "timestamp_iso", "piattaforma", "tipo", "workflow_id",
            "workflow_nome", "n_operazioni", "costo_unitario_eur",
            "costo_totale_eur",
        ]

    def registra(self, evento: EventoCosto) -> None:
        """Append-only: aggiunge evento al CSV."""
        with open(self._path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self._fieldnames())
            row = {k: getattr(evento, k) for k in self._fieldnames()}
            row["tipo"] = evento.tipo.value
            writer.writerow(row)

    def leggi_tutti(self) -> list[dict]:
        """Legge tutti gli eventi dal CSV."""
        if not self._path.exists():
            return []
        
        with open(self._path, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def totale_per_piattaforma(
        self,
        da: Optional[str] = None,
        a: Optional[str] = None,
    ) -> dict[str, float]:
        """Somma costi per piattaforma nel periodo specificato."""
        eventi = self.leggi_tutti()
        totali: dict[str, float] = {}
        
        for ev in eventi:
            ts = ev["timestamp_iso"]
            if da and ts < da:
                continue
            if a and ts > a:
                continue
            
            piattaforma = ev["piattaforma"]
            costo = float(ev.get("costo_totale_eur", 0))
            totali[piattaforma] = totali.get(piattaforma, 0.0) + costo
        
        return totali

    def operazioni_per_workflow(
        self,
        piattaforma: Optional[str] = None,
    ) -> dict[str, dict]:
        """Conteggio operazioni e costi per workflow."""
        eventi = self.leggi_tutti()
        result: dict[str, dict] = {}
        
        for ev in eventi:
            if piattaforma and ev["piattaforma"] != piattaforma:
                continue
            
            nome = ev["workflow_nome"]
            if nome not in result:
                result[nome] = {
                    "operazioni": 0,
                    "costo_totale": 0.0,
                    "piattaforma": ev["piattaforma"],
                }
            
            result[nome]["operazioni"] += int(ev.get("n_operazioni", 1))
            result[nome]["costo_totale"] += float(ev.get("costo_totale_eur", 0))
        
        return result

    def costo_giornaliero(
        self,
        giorni: int = 30,
    ) -> dict[str, float]:
        """Costo totale per giorno negli ultimi N giorni."""
        eventi = self.leggi_tutti()
        giornaliero: dict[str, float] = {}
        
        for ev in eventi:
            giorno = ev["timestamp_iso"][:10]  # YYYY-MM-DD
            costo = float(ev.get("costo_totale_eur", 0))
            giornaliero[giorno] = giornaliero.get(giorno, 0.0) + costo
        
        # Ordina e prendi ultimi N giorni
        return dict(sorted(giornaliero.items())[-giorni:])
```

---

## PART B — Budget Alert

### B1 — Alert Engine

```python
#!/usr/bin/env python3
# file: alerts/budget_alert.py
"""
Sistema di alert per budget superamento e anomalie di costo.
"""
from __future__ import annotations

import json
import time
import logging
from dataclasses import dataclass
from typing import Callable, Optional

from tracker.cost_tracker import CostTracker

logger = logging.getLogger(__name__)


@dataclass
class RegolaBudget:
    """Regola di alert per budget."""
    nome: str
    piattaforma: Optional[str]       # None = tutte le piattaforme
    soglia_eur: float                # Alert quando costo supera questa soglia
    periodo: str                     # "giorno" | "settimana" | "mese"
    severita: str                    # "info" | "warning" | "critical"
    webhook_url: Optional[str] = None  # URL per notifica (Slack, Teams, etc.)


@dataclass
class AlertGenerato:
    """Alert generato dal sistema."""
    regola: str
    timestamp: str
    severita: str
    messaggio: str
    costo_attuale: float
    soglia: float
    percentuale: float


class BudgetAlertEngine:
    """
    Motore di alert per budget piattaforme.
    Valuta le regole e genera alert quando le soglie vengono superate.
    """

    def __init__(self, tracker: CostTracker):
        self._tracker = tracker
        self._regole: list[RegolaBudget] = []
        self._notificati: set[str] = set()  # Evita alert duplicati

    def aggiungi_regola(self, regola: RegolaBudget) -> None:
        self._regole.append(regola)

    def _calcola_costo_periodo(self, piattaforma: Optional[str], periodo: str) -> float:
        """Calcola il costo nel periodo specificato."""
        ora = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        if periodo == "giorno":
            da = time.strftime("%Y-%m-%dT00:00:00Z")
        elif periodo == "settimana":
            # Lunedì scorso
            import datetime
            oggi = datetime.date.today()
            lunedi = oggi - datetime.timedelta(days=oggi.weekday())
            da = f"{lunedi}T00:00:00Z"
        elif periodo == "mese":
            da = time.strftime("%Y-%m-01T00:00:00Z")
        else:
            da = "2000-01-01T00:00:00Z"
        
        totali = self._tracker.totale_per_piattaforma(da=da)
        
        if piattaforma:
            return totali.get(piattaforma, 0.0)
        else:
            return sum(totali.values())

    def valuta(self) -> list[AlertGenerato]:
        """Valuta tutte le regole e ritorna gli alert attivi."""
        alert_attivi = []
        
        for regola in self._regole:
            costo = self._calcola_costo_periodo(regola.piattaforma, regola.periodo)
            
            if costo > regola.soglia:
                percentuale = (costo / regola.soglia) * 100
                
                # Chiave per dedup: stesso alert entro la stessa ora
                dedup_key = f"{regola.nome}:{time.strftime('%Y-%m-%dT%H')}"
                
                if dedup_key not in self._notificati:
                    self._notificati.add(dedup_key)
                    
                    alert = AlertGenerato(
                        regola=regola.nome,
                        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        severita=regola.severita,
                        messaggio=(
                            f"[{regola.severita.upper()}] Budget {regola.nome}: "
                            f"€{costo:.2f} / €{regola.soglia:.2f} "
                            f"({percentuale:.0f}%) nel {regola.periodo}"
                        ),
                        costo_attuale=costo,
                        soglia=regola.soglia,
                        percentuale=percentuale,
                    )
                    
                    alert_attivi.append(alert)
                    logger.warning(alert.messaggio)
                    
                    # Invia notifica webhook se configurata
                    if regola.webhook_url:
                        self._invia_webhook(regola.webhook_url, alert)
        
        return alert_attivi

    def _invia_webhook(self, url: str, alert: AlertGenerato) -> None:
        """Invia alert a webhook (Slack, Teams, ecc.)."""
        try:
            import httpx
            payload = {
                "text": alert.messaggio,
                "attachments": [{
                    "color": "danger" if alert.severita == "critical" else "warning",
                    "fields": [
                        {"title": "Costo attuale", "value": f"€{alert.costo_attuale:.2f}", "short": True},
                        {"title": "Soglia", "value": f"€{alert.soglia:.2f}", "short": True},
                    ]
                }]
            }
            httpx.post(url, json=payload, timeout=5)
        except Exception as e:
            logger.error("Invio webhook fallito: %s", e)
```

---

## PART C — Report Mensile

### C1 — Report Generator

```python
#!/usr/bin/env python3
# file: reports/monthly_report.py
"""
Generazione report mensile costi.
Output: CSV, JSON, e opzionale grafico matplotlib.
"""
from __future__ import annotations

import csv
import json
import time
from pathlib import Path
from typing import Optional

from tracker.cost_tracker import CostTracker
from tracker.cost_model import PIANI_STANDARD, calcola_costo_mensile


def genera_report_mensile(
    tracker: CostTracker,
    anno: int,
    mese: int,
    output_dir: Path = Path("./reports"),
) -> dict:
    """
    Genera report mensile completo.
    
    Sezioni:
    1. Sommario costi per piattaforma
    2. Top 10 workflow per costo
    3. Confronto con mese precedente
    4. Proiezione costi prossimo mese
    5. Raccomandazioni
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    da = f"{anno}-{mese:02d}-01T00:00:00Z"
    a = f"{anno}-{mese:02d}-31T23:59:59Z"
    
    # ─── Dati ────────────────────────────────────────────────────────────────
    
    totali_piattaforma = tracker.totale_per_piattaforma(da=da, a=a)
    workflow_costs = tracker.operazioni_per_workflow()
    
    # Top 10 workflow per costo
    top10 = sorted(
        workflow_costs.items(),
        key=lambda x: x[1]["costo_totale"],
        reverse=True
    )[:10]
    
    # ─── Proiezione ──────────────────────────────────────────────────────────
    
    giorni_nel_mese = 30  # Approssimazione
    giorni_trascorsi = min(
        int(time.strftime("%d")),
        giorni_nel_mese
    )
    
    proiezioni = {}
    if giorni_trascorsi > 0:
        for piattaforma, costo in totali_piattaforma.items():
            rata_giornaliera = costo / giorni_trascorsi
            proiezioni[piattaforma] = rata_giornaliera * giorni_nel_mese
    
    # ─── Raccomandazioni ─────────────────────────────────────────────────────
    
    raccomandazioni = []
    
    for piattaforma, costo_attuale in totali_piattaforma.items():
        ops_mese = sum(
            v["operazioni"] for v in workflow_costs.values()
            if v["piattaforma"] == piattaforma
        )
        
        # Confronta con piano ottimale
        try:
            prefisso = piattaforma.split("_")[0]
            piano_opt = trova_piano_ottimale = min(
                [p for p in PIANI_STANDARD if p.piattaforma.startswith(prefisso)],
                key=lambda p: calcola_costo_mensile(p, ops_mese)
            )
            costo_ottimale = calcola_costo_mensile(piano_opt, ops_mese)
            
            if costo_ottimale < costo_attuale * 0.8:  # >20% risparmio
                raccomandazioni.append({
                    "piattaforma": piattaforma,
                    "tipo": "cambio_piano",
                    "messaggio": (
                        f"Passando al piano '{piano_opt.nome_piano}' "
                        f"potresti risparmiare €{costo_attuale - costo_ottimale:.2f}/mese"
                    ),
                    "risparmio_eur": costo_attuale - costo_ottimale,
                })
        except (ValueError, StopIteration):
            pass
    
    # ─── Compila report ───────────────────────────────────────────────────────
    
    report = {
        "periodo": f"{anno}-{mese:02d}",
        "generato_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sommario": {
            "costo_totale_eur": sum(totali_piattaforma.values()),
            "per_piattaforma": totali_piattaforma,
        },
        "top_workflow_per_costo": [
            {
                "nome": nome,
                "piattaforma": dati["piattaforma"],
                "operazioni": dati["operazioni"],
                "costo_eur": dati["costo_totale"],
            }
            for nome, dati in top10
        ],
        "proiezioni_mese_corrente": proiezioni,
        "raccomandazioni": raccomandazioni,
    }
    
    # ─── Salva JSON ───────────────────────────────────────────────────────────
    
    json_path = output_dir / f"report_{anno}_{mese:02d}.json"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    
    # ─── Salva CSV ────────────────────────────────────────────────────────────
    
    csv_path = output_dir / f"report_{anno}_{mese:02d}.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Sezione", "Piattaforma", "Metrica", "Valore"])
        
        for piattaforma, costo in totali_piattaforma.items():
            writer.writerow(["Costo", piattaforma, "Totale EUR", f"{costo:.4f}"])
        
        for nome, dati in top10:
            writer.writerow([
                "Top Workflow", dati["piattaforma"], nome,
                f"€{dati['costo_totale']:.4f} ({dati['operazioni']} ops)"
            ])
        
        for r in raccomandazioni:
            writer.writerow([
                "Raccomandazione", r["piattaforma"],
                r["tipo"], f"Risparmio €{r.get('risparmio_eur', 0):.2f}"
            ])
    
    print(f"Report salvato: {json_path}, {csv_path}")
    return report


# ─── Demo ─────────────────────────────────────────────────────────────────────

def demo():
    """Demo: popola dati di test e genera report."""
    from tracker.cost_model import EventoCosto, TipoCosto
    
    tracker = CostTracker(Path("./data/demo_costi.csv"))
    
    # Simula un mese di attività
    import datetime
    oggi = datetime.date.today()
    
    workflow_costi = [
        ("wf-001", "Riconciliazione banca", "make", 500, 0.049),
        ("wf-002", "Fatture SDI", "n8n_self", 200, 0.0),
        ("wf-003", "Newsletter weekly", "zapier_starter", 100, 0.016),
        ("wf-004", "Alert scorte", "make", 1500, 0.049),
        ("wf-005", "Sync CRM", "n8n_self", 800, 0.0),
    ]
    
    for i in range(15):  # 15 giorni di dati
        giorno = oggi - datetime.timedelta(days=i)
        for wf_id, wf_nome, piattaforma, ops_giorno, costo_unit in workflow_costi:
            costo = ops_giorno * costo_unit
            tracker.registra(EventoCosto(
                timestamp_iso=f"{giorno}T10:00:00Z",
                piattaforma=piattaforma,
                tipo=TipoCosto.PER_OPERAZIONE,
                workflow_id=wf_id,
                workflow_nome=wf_nome,
                n_operazioni=ops_giorno,
                costo_unitario_eur=costo_unit,
                costo_totale_eur=costo,
            ))
    
    # Genera report
    report = genera_report_mensile(tracker, oggi.year, oggi.month)
    
    print("\n=== REPORT MENSILE ===")
    print(f"Costo totale: €{report['sommario']['costo_totale_eur']:.2f}")
    print("\nPer piattaforma:")
    for pf, costo in report["sommario"]["per_piattaforma"].items():
        print(f"  {pf}: €{costo:.2f}")
    
    print("\nTop workflow per costo:")
    for wf in report["top_workflow_per_costo"][:3]:
        print(f"  [{wf['piattaforma']}] {wf['nome']}: €{wf['costo_eur']:.2f}")
    
    if report["raccomandazioni"]:
        print("\nRaccomandazioni:")
        for r in report["raccomandazioni"]:
            print(f"  → {r['messaggio']}")


if __name__ == "__main__":
    demo()
```

---

## Esercizi

### Esercizio 1 — Alert Personalizzato (20 min)

```python
from alerts.budget_alert import BudgetAlertEngine, RegolaBudget
from tracker.cost_tracker import CostTracker

tracker = CostTracker()
engine = BudgetAlertEngine(tracker)

# Aggiungi regole personalizzate per la tua situazione
engine.aggiungi_regola(RegolaBudget(
    nome="Budget Make mensile",
    piattaforma="make",
    soglia_eur=100.0,       # Alert se superi €100/mese
    periodo="mese",
    severita="critical",
    webhook_url=None,        # Aggiungi URL Slack/Teams qui
))

engine.aggiungi_regola(RegolaBudget(
    nome="Budget giornaliero totale",
    piattaforma=None,        # Tutte le piattaforme
    soglia_eur=10.0,
    periodo="giorno",
    severita="warning",
))

alert_attivi = engine.valuta()
for alert in alert_attivi:
    print(f"ALERT: {alert.messaggio}")
```

### Esercizio 2 — Proiezione con Trend (25 min)

Implementa una proiezione che considera il trend (crescita/decrescita) invece di
assumere una rata costante:

```python
def proietta_con_trend(
    giornaliero: dict[str, float],
    giorni_futuro: int = 30,
) -> dict:
    """
    Calcola trend lineare e proietta il costo futuro.
    Ritorna: {costo_proiettato, trend_giornaliero, intervallo_confidenza}
    """
    # Usa scipy.stats.linregress o implementazione manuale
    pass
```

### Esercizio 3 — Dashboard Testuale (20 min)

```python
def stampa_dashboard(tracker: CostTracker) -> None:
    """Dashboard testuale con ASCII art per il terminale."""
    giornaliero = tracker.costo_giornaliero(giorni=7)
    max_costo = max(giornaliero.values()) if giornaliero else 1
    
    print("COSTO ULTIMI 7 GIORNI:")
    for giorno, costo in giornaliero.items():
        barre = int((costo / max_costo) * 30)
        print(f"  {giorno[-5:]} │{'█' * barre} €{costo:.2f}")
```

---

## Riferimenti

- Make Pricing Calculator: https://www.make.com/en/pricing
- Zapier Pricing: https://zapier.com/pricing
- n8n Pricing: https://n8n.io/pricing
- Prometheus Cost Metrics: https://prometheus.io/docs/
- Modulo sorgente: `19-cost-monitoring-piattaforme.md`
