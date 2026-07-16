# Tutorial Lab — Piattaforme No-Code: Confronto, Criteri di Scelta e TCO

> **Campo di studio:** 09-AUTOMAZIONI-FLUSSI-DI-LAVORO
> **Modulo sorgente:** `02-piattaforme-low-code.md`
> **Livello:** beginner → intermediate
> **Tempo stimato:** 2 ore
> **Prerequisiti:** concetti HTTP/webhook base, JSON, comprensione business processes
> **Versioni di riferimento:** n8n 1.x · Make (ex Integromat) · Zapier · Power Automate

---

## Obiettivi del Lab

Al termine di questo tutorial saprai:

1. Confrontare n8n, Make, Zapier e Power Automate su criteri oggettivi
2. Calcolare il TCO (Total Cost of Ownership) su 3 anni per ogni piattaforma
3. Applicare la matrice decisionale per scegliere la piattaforma giusta
4. Identificare quando il no-code NON è la scelta giusta
5. Stimare il volume di operazioni e scegliere il piano appropriato
6. Valutare lock-in, vendor risk e migration path

---

## Lab Environment Setup

```python
# Nessuna dipendenza esterna — solo Python stdlib
python3 --version   # 3.11+

# Tutto il lab si esegue come script Python standalone
```

---

## Analogia Introduttiva

> **Le piattaforme no-code sono come le officine chiavi in mano**:
> invece di comprare un tornio, imparare a usarlo e formare un tecnico,
> porti il tuo pezzo e loro te lo lavorano.
> Più veloce per pezzi standard, meno flessibile per pezzi personalizzati.
>
> La differenza tra le piattaforme è come la differenza tra
> un'officina al piano di sotto (n8n self-hosted — tua, under your control)
> e un'officina internazionale in cloud (Zapier — loro server, tu paghi per ogni pezzo).
>
> Scegliere la piattaforma sbagliata significa:
> - **Vendor lock-in**: quando vuoi cambiare, devi ricostruire tutto
> - **Bill shock**: il prezzo per operazione sembra basso,
>   finché non calcoli 50.000 operazioni/mese a 0.02€ ciascuna
> - **GDPR risk**: dati sensibili che transitano su server esteri

---

## PART A — Confronto Piattaforme

### A1 — Matrice Comparativa

```python
#!/usr/bin/env python3
# file: confronto_piattaforme.py
"""
Matrice di confronto completa tra piattaforme no-code di automazione.
Tutti i dati sono basati su prezzi pubblici e caratteristiche documentate.
AGGIORNARE i prezzi prima dell'uso (cambiano frequentemente).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Piattaforma:
    nome: str
    vendor: str
    modello_deployment: str  # "SaaS" | "Self-hosted" | "Entrambi"
    
    # Pricing (approssimativo, verificare sito ufficiale)
    piano_gratuito: bool
    prezzo_base_mese: float          # € al mese (piano entry)
    unita_di_misura: str             # "task" | "scenario_runs" | "esecuzioni"
    incluse_nel_base: int            # N unità incluse nel piano base
    prezzo_extra_per_1000: float     # € per 1000 unità extra
    
    # Caratteristiche tecniche
    n_integrazioni: int              # App/servizi integrati nativamente
    custom_code: bool                # Supporta codice custom (JS/Python)
    webhook_support: bool
    data_mapping: str                # "semplice" | "avanzato" | "programmabile"
    error_handling: str              # "base" | "medio" | "avanzato"
    versioning: bool
    
    # Dati
    gdpr_data_residency_eu: bool     # Opzione server EU
    self_hosted_option: bool         # Può essere installato on-premise
    
    # Team
    collaborazione_team: bool
    sso_saml: bool
    ruoli_permessi: bool
    
    # Support
    supporto_email: bool
    supporto_telefono: bool
    sla_uptime: Optional[str]
    
    # Note
    note: str


PIATTAFORME = [
    Piattaforma(
        nome="n8n",
        vendor="n8n GmbH (open source)",
        modello_deployment="Entrambi",
        piano_gratuito=True,  # Self-hosted: sempre gratis
        prezzo_base_mese=20.0,  # Cloud: piano Starter
        unita_di_misura="esecuzioni",
        incluse_nel_base=2500,
        prezzo_extra_per_1000=0.0,  # Self-hosted: illimitato
        n_integrazioni=400,
        custom_code=True,  # Nodo "Code" con JS/Python
        webhook_support=True,
        data_mapping="programmabile",  # Espressioni JS full
        error_handling="avanzato",  # Retry, error workflow, DLQ
        versioning=True,  # Workflow versioning con storia
        gdpr_data_residency_eu=True,
        self_hosted_option=True,
        collaborazione_team=True,
        sso_saml=True,  # Piano Enterprise
        ruoli_permessi=True,
        supporto_email=True,
        supporto_telefono=False,  # Solo Enterprise
        sla_uptime="99.9%",
        note="Best choice per GDPR-sensitive data e developer teams. "
             "Self-hosted = zero cost operazioni, solo infrastruttura.",
    ),
    Piattaforma(
        nome="Make (ex Integromat)",
        vendor="Celonis (acquisita 2022)",
        modello_deployment="SaaS",
        piano_gratuito=True,
        prezzo_base_mese=9.0,  # Piano Core
        unita_di_misura="operazioni",
        incluse_nel_base=10000,
        prezzo_extra_per_1000=0.49,
        n_integrazioni=1500,
        custom_code=True,  # Modulo HTTP + JSON
        webhook_support=True,
        data_mapping="avanzato",  # Visual mapper + funzioni
        error_handling="medio",
        versioning=True,  # Blueprint versioning
        gdpr_data_residency_eu=True,
        self_hosted_option=False,
        collaborazione_team=True,
        sso_saml=True,  # Piano Teams+
        ruoli_permessi=True,
        supporto_email=True,
        supporto_telefono=True,
        sla_uptime="99.9%",
        note="Ottimo visual data mapping. Più integrazioni native di n8n. "
             "Ideale per mid-market europeo con team non-tecnici.",
    ),
    Piattaforma(
        nome="Zapier",
        vendor="Zapier Inc.",
        modello_deployment="SaaS",
        piano_gratuito=True,  # 5 Zap gratuiti
        prezzo_base_mese=29.99,  # Piano Starter (fatturazione annuale)
        unita_di_misura="task",
        incluse_nel_base=750,
        prezzo_extra_per_1000=1.60,
        n_integrazioni=7000,  # Numero più alto del mercato
        custom_code=True,  # Code by Zapier (JS/Python)
        webhook_support=True,
        data_mapping="avanzato",
        error_handling="base",
        versioning=False,  # Storico limitato
        gdpr_data_residency_eu=False,  # Server US principalmente
        self_hosted_option=False,
        collaborazione_team=True,
        sso_saml=True,  # Piano Business+
        ruoli_permessi=True,
        supporto_email=True,
        supporto_telefono=False,
        sla_uptime="99.9%",
        note="Più integrazioni disponibili. Ideale per startup che usano molti SaaS US. "
             "Costoso ad alto volume. Attenzione GDPR: dati transitano su server US.",
    ),
    Piattaforma(
        nome="Power Automate",
        vendor="Microsoft",
        modello_deployment="SaaS",
        piano_gratuito=False,  # Incluso in M365 Business
        prezzo_base_mese=15.0,  # Power Automate Premium/utente/mese
        unita_di_misura="flow_runs",
        incluse_nel_base=5000,
        prezzo_extra_per_1000=0.40,
        n_integrazioni=1000,
        custom_code=True,  # Azure Functions integration
        webhook_support=True,
        data_mapping="avanzato",
        error_handling="medio",
        versioning=True,
        gdpr_data_residency_eu=True,
        self_hosted_option=False,  # On-premises gateway disponibile
        collaborazione_team=True,
        sso_saml=True,  # Azure AD nativo
        ruoli_permessi=True,
        supporto_email=True,
        supporto_telefono=True,
        sla_uptime="99.9%",
        note="Scelta naturale per aziende già su Microsoft 365. "
             "Integrazione nativa con Teams, SharePoint, Dynamics 365. "
             "Problematico fuori dall'ecosistema Microsoft.",
    ),
]


def stampa_confronto():
    """Stampa tabella comparativa formattata."""
    print("\n" + "=" * 80)
    print("CONFRONTO PIATTAFORME NO-CODE AUTOMAZIONE")
    print("=" * 80)
    
    campi = [
        ("Vendor", lambda p: p.vendor),
        ("Deployment", lambda p: p.modello_deployment),
        ("Prezzo base/mese", lambda p: f"€{p.prezzo_base_mese:.2f}"),
        ("Unità incluse", lambda p: f"{p.incluse_nel_base:,} {p.unita_di_misura}"),
        ("Extra/1k", lambda p: f"€{p.prezzo_extra_per_1000:.2f}" if p.prezzo_extra_per_1000 else "∞ (self-hosted)"),
        ("Integrazioni", lambda p: str(p.n_integrazioni)),
        ("Codice custom", lambda p: "✓" if p.custom_code else "✗"),
        ("GDPR EU", lambda p: "✓" if p.gdpr_data_residency_eu else "✗"),
        ("Self-hosted", lambda p: "✓" if p.self_hosted_option else "✗"),
        ("SSO/SAML", lambda p: "✓" if p.sso_saml else "✗"),
    ]
    
    col_w = 22
    header = f"{'Campo':<20}" + "".join(f"{p.nome:<{col_w}}" for p in PIATTAFORME)
    print(header)
    print("-" * (20 + col_w * len(PIATTAFORME)))
    
    for label, fn in campi:
        row = f"{label:<20}" + "".join(f"{fn(p):<{col_w}}" for p in PIATTAFORME)
        print(row)
    
    print("\nNOTE:")
    for p in PIATTAFORME:
        print(f"  [{p.nome}] {p.note}")


if __name__ == "__main__":
    stampa_confronto()
```

---

## PART B — Calcolo TCO

### B1 — TCO Calculator su 3 Anni

```python
#!/usr/bin/env python3
# file: tco_calculator.py
"""
Total Cost of Ownership calculator per piattaforme no-code.
Considera: licenze, infrastruttura, ore sviluppo, formazione, manutenzione.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ScenarioUso:
    """Scenario d'uso aziendale per il calcolo TCO."""
    nome: str
    operazioni_mese: int         # Task/run/esecuzioni al mese
    n_workflow: int              # Numero di workflow da costruire
    n_utenti: int                # Utenti che gestiscono la piattaforma
    ore_sviluppo_iniziale: float # Ore totali per costruire tutti i workflow
    ore_manutenzione_mese: float # Ore/mese manutenzione ongoing
    tariffa_oraria: float        # Costo orario sviluppatore/BizAnalyst (€)


@dataclass
class TcoRisultato:
    piattaforma: str
    scenario: str
    
    # Costi anno 1
    licenza_anno1: float
    infrastruttura_anno1: float  # 0 per SaaS, server cost per self-hosted
    sviluppo_anno1: float
    formazione_anno1: float
    
    # Anni 2-3
    licenza_anni23: float
    manutenzione_anni23: float
    
    # Totali
    tco_3anni: float
    costo_medio_mensile: float


def calcola_tco_n8n_self_hosted(scenario: ScenarioUso) -> TcoRisultato:
    """
    n8n self-hosted: zero licenza, costo server.
    Stima server: VPS 4CPU 8GB RAM ≈ €40/mese + 2h DevOps/mese.
    """
    costo_server_mese = 40.0
    ore_devops_mese = 2.0  # Update, backup, monitoring
    
    licenza_anno1 = 0.0  # Open source
    infrastruttura_anno1 = costo_server_mese * 12
    sviluppo_anno1 = scenario.ore_sviluppo_iniziale * scenario.tariffa_oraria
    formazione_anno1 = 8.0 * scenario.n_utenti * scenario.tariffa_oraria  # 1 giornata formazione
    
    licenza_anni23 = 0.0
    manutenzione_anni23 = (
        scenario.ore_manutenzione_mese * scenario.tariffa_oraria
        + costo_server_mese
        + ore_devops_mese * scenario.tariffa_oraria
    ) * 12 * 2
    
    tco = licenza_anno1 + infrastruttura_anno1 + sviluppo_anno1 + formazione_anno1 + manutenzione_anni23
    
    return TcoRisultato(
        piattaforma="n8n self-hosted",
        scenario=scenario.nome,
        licenza_anno1=licenza_anno1,
        infrastruttura_anno1=infrastruttura_anno1,
        sviluppo_anno1=sviluppo_anno1,
        formazione_anno1=formazione_anno1,
        licenza_anni23=licenza_anni23,
        manutenzione_anni23=manutenzione_anni23,
        tco_3anni=tco,
        costo_medio_mensile=tco / 36,
    )


def calcola_tco_make(scenario: ScenarioUso) -> TcoRisultato:
    """Make: prezzo basato su operazioni."""
    ops_mese = scenario.operazioni_mese
    
    # Scegli piano
    if ops_mese <= 10_000:
        piano_mese = 9.0
        ops_incluse = 10_000
    elif ops_mese <= 40_000:
        piano_mese = 29.0
        ops_incluse = 40_000
    elif ops_mese <= 150_000:
        piano_mese = 99.0
        ops_incluse = 150_000
    else:
        piano_mese = 299.0
        ops_incluse = 800_000
    
    extra_ops = max(0, ops_mese - ops_incluse)
    extra_mese = (extra_ops / 1000) * 0.49
    
    licenza_anno1 = (piano_mese + extra_mese) * 12
    infrastruttura_anno1 = 0.0
    sviluppo_anno1 = scenario.ore_sviluppo_iniziale * scenario.tariffa_oraria
    formazione_anno1 = 16.0 * scenario.n_utenti * scenario.tariffa_oraria  # 2 giorni
    
    licenza_anni23 = (piano_mese + extra_mese) * 12 * 2
    manutenzione_anni23 = scenario.ore_manutenzione_mese * scenario.tariffa_oraria * 12 * 2
    
    tco = licenza_anno1 + sviluppo_anno1 + formazione_anno1 + licenza_anni23 + manutenzione_anni23
    
    return TcoRisultato(
        piattaforma="Make",
        scenario=scenario.nome,
        licenza_anno1=licenza_anno1,
        infrastruttura_anno1=infrastruttura_anno1,
        sviluppo_anno1=sviluppo_anno1,
        formazione_anno1=formazione_anno1,
        licenza_anni23=licenza_anni23,
        manutenzione_anni23=manutenzione_anni23,
        tco_3anni=tco,
        costo_medio_mensile=tco / 36,
    )


def calcola_tco_zapier(scenario: ScenarioUso) -> TcoRisultato:
    """Zapier: piano basato su task."""
    tasks_mese = scenario.operazioni_mese
    
    if tasks_mese <= 750:
        piano_mese = 29.99
    elif tasks_mese <= 2000:
        piano_mese = 73.50
    elif tasks_mese <= 10_000:
        piano_mese = 139.0
    elif tasks_mese <= 25_000:
        piano_mese = 239.0
    else:
        piano_mese = 399.0
    
    licenza_anno1 = piano_mese * 12
    infrastruttura_anno1 = 0.0
    sviluppo_anno1 = scenario.ore_sviluppo_iniziale * scenario.tariffa_oraria * 0.7  # Più veloce
    formazione_anno1 = 8.0 * scenario.n_utenti * scenario.tariffa_oraria
    
    licenza_anni23 = piano_mese * 12 * 2
    manutenzione_anni23 = scenario.ore_manutenzione_mese * scenario.tariffa_oraria * 12 * 2
    
    tco = licenza_anno1 + sviluppo_anno1 + formazione_anno1 + licenza_anni23 + manutenzione_anni23
    
    return TcoRisultato(
        piattaforma="Zapier",
        scenario=scenario.nome,
        licenza_anno1=licenza_anno1,
        infrastruttura_anno1=infrastruttura_anno1,
        sviluppo_anno1=sviluppo_anno1,
        formazione_anno1=formazione_anno1,
        licenza_anni23=licenza_anni23,
        manutenzione_anni23=manutenzione_anni23,
        tco_3anni=tco,
        costo_medio_mensile=tco / 36,
    )


def stampa_tco(risultati: list[TcoRisultato]) -> None:
    """Stampa confronto TCO."""
    if not risultati:
        return
    
    print(f"\n{'=' * 65}")
    print(f"TCO 3 ANNI — Scenario: {risultati[0].scenario}")
    print(f"{'=' * 65}")
    print(f"{'Voce':<30} " + " ".join(f"{r.piattaforma:>12}" for r in risultati))
    print("-" * 65)
    
    voci = [
        ("Licenza anno 1", lambda r: r.licenza_anno1),
        ("Infrastruttura anno 1", lambda r: r.infrastruttura_anno1),
        ("Sviluppo iniziale", lambda r: r.sviluppo_anno1),
        ("Formazione", lambda r: r.formazione_anno1),
        ("Licenza anni 2-3", lambda r: r.licenza_anni23),
        ("Manutenzione anni 2-3", lambda r: r.manutenzione_anni23),
    ]
    
    for voce, fn in voci:
        print(f"{voce:<30} " + " ".join(f"€{fn(r):>9,.0f}" for r in risultati))
    
    print("-" * 65)
    print(f"{'TOTALE TCO 3 ANNI':<30} " + " ".join(f"€{r.tco_3anni:>9,.0f}" for r in risultati))
    print(f"{'Costo medio mensile':<30} " + " ".join(f"€{r.costo_medio_mensile:>9,.0f}" for r in risultati))
    
    # Raccomandazione
    migliore = min(risultati, key=lambda r: r.tco_3anni)
    print(f"\n→ TCO più basso: {migliore.piattaforma} (€{migliore.tco_3anni:,.0f})")


if __name__ == "__main__":
    from confronto_piattaforme import stampa_confronto
    stampa_confronto()
    
    # Scenario PMI italiana: 50.000 operazioni/mese
    scenario_pmi = ScenarioUso(
        nome="PMI 50k operazioni/mese",
        operazioni_mese=50_000,
        n_workflow=15,
        n_utenti=3,
        ore_sviluppo_iniziale=120.0,
        ore_manutenzione_mese=8.0,
        tariffa_oraria=35.0,
    )
    
    risultati = [
        calcola_tco_n8n_self_hosted(scenario_pmi),
        calcola_tco_make(scenario_pmi),
        calcola_tco_zapier(scenario_pmi),
    ]
    stampa_tco(risultati)
    
    # Scenario startup: volume basso
    scenario_startup = ScenarioUso(
        nome="Startup 5k operazioni/mese",
        operazioni_mese=5_000,
        n_workflow=5,
        n_utenti=1,
        ore_sviluppo_iniziale=40.0,
        ore_manutenzione_mese=2.0,
        tariffa_oraria=40.0,
    )
    
    risultati_startup = [
        calcola_tco_n8n_self_hosted(scenario_startup),
        calcola_tco_make(scenario_startup),
        calcola_tco_zapier(scenario_startup),
    ]
    stampa_tco(risultati_startup)
```

---

## PART C — Quando il No-Code NON Basta

### C1 — Matrice Decisionale No-Code vs Custom

```python
#!/usr/bin/env python3
# file: matrice_nocode_custom.py
"""
Quando usare no-code, quando scrivere codice custom.
"""

REGOLE = """
╔════════════════════════════════════════════════════════════════════╗
║           MATRICE DECISIONALE: NO-CODE vs CUSTOM CODE             ║
╠════════════════════════════════════════════════════════════════════╣
║                                                                    ║
║  USA NO-CODE se:                  USA CUSTOM CODE se:             ║
║  ─────────────────────────────    ──────────────────────────────  ║
║  ✓ Integrazioni API standard      ✗ Logica business complessa     ║
║  ✓ Workflow lineari               ✗ Algoritmi custom              ║
║  ✓ Team non-tecnico               ✗ Performance < 100ms           ║
║  ✓ Prototipo in <1 settimana      ✗ Testing automatico richiesto  ║
║  ✓ Budget limitato inizialmente   ✗ High throughput (>10k/min)    ║
║  ✓ SaaS connectors pre-built      ✗ Data transformation complessa ║
║  ✓ Trigger event-based semplici   ✗ Stateful workflow (saga)      ║
║  ✓ Notifiche e alert              ✗ Compliance audit trail        ║
║                                                                    ║
╠════════════════════════════════════════════════════════════════════╣
║                                                                    ║
║  SEGNALI DI ALLARME nel no-code:                                  ║
║  ⚠ Stai aggiungendo "webhook + custom code node" ovunque         ║
║    → Probabilmente serve uno script Python                        ║
║  ⚠ Workflow con >50 nodi                                          ║
║    → Difficile da mantenere, meglio codice strutturato            ║
║  ⚠ Stesso workflow duplicato per ogni cliente                     ║
║    → Serve parametrizzazione → codice custom                     ║
║  ⚠ Debugging impossibile (impossibile capire cosa ha fatto)       ║
║    → Mancano trace + logging → custom code + OTel                ║
║                                                                    ║
╠════════════════════════════════════════════════════════════════════╣
║                                                                    ║
║  LOCK-IN RISK:                                                     ║
║  n8n self-hosted: BASSO — export JSON, migrazione possibile       ║
║  Make:           MEDIO — blueprint proprietario                   ║
║  Zapier:         MEDIO — Zap format proprietario                  ║
║  Power Automate: ALTO — fortemente legato all'ecosistema M365     ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
"""


def valuta_scenario(
    n_integrazioni: int,
    complessita_logica: int,   # 1-5
    team_tecnico: bool,
    volume_ore_peak: int,      # esecuzioni/ora al picco
    gdpr_dati_sensibili: bool,
    budget_annuo_max: float,
) -> str:
    """Suggerisce la scelta basandosi sui parametri."""
    
    motivi_nocode = []
    motivi_custom = []
    
    if n_integrazioni > 3 and complessita_logica <= 2:
        motivi_nocode.append("Molte integrazioni standard → connectors nativi")
    if not team_tecnico:
        motivi_nocode.append("Team non tecnico → visual editor essenziale")
    
    if complessita_logica >= 4:
        motivi_custom.append("Logica complessa → meglio testabilità del codice")
    if volume_ore_peak > 10_000:
        motivi_custom.append("Alto volume → message queue + worker Python")
    if gdpr_dati_sensibili:
        motivi_custom.append("Dati sensibili → n8n self-hosted o custom API")
    
    if len(motivi_nocode) > len(motivi_custom):
        return f"CONSIGLIO: No-code\n  Motivazioni: {', '.join(motivi_nocode)}"
    elif len(motivi_custom) > len(motivi_nocode):
        return f"CONSIGLIO: Custom code\n  Motivazioni: {', '.join(motivi_custom)}"
    else:
        return f"BORDERLINE: n8n self-hosted (controllo + flessibilità)\n  Pro no-code: {motivi_nocode}\n  Pro custom: {motivi_custom}"


if __name__ == "__main__":
    print(REGOLE)
    
    # Test scenari tipici PMI italiane
    print("\nVALUTAZIONE SCENARI:")
    scenari = [
        ("Newsletter CRM → MailChimp", dict(
            n_integrazioni=3, complessita_logica=2, team_tecnico=False,
            volume_ore_peak=100, gdpr_dati_sensibili=True, budget_annuo_max=5000
        )),
        ("Processing ordini real-time", dict(
            n_integrazioni=5, complessita_logica=4, team_tecnico=True,
            volume_ore_peak=50000, gdpr_dati_sensibili=True, budget_annuo_max=20000
        )),
        ("Alert fatture scadute", dict(
            n_integrazioni=2, complessita_logica=1, team_tecnico=False,
            volume_ore_peak=50, gdpr_dati_sensibili=False, budget_annuo_max=1000
        )),
    ]
    
    for nome, params in scenari:
        print(f"\n  [{nome}]")
        print(f"  {valuta_scenario(**params)}")
```

---

## Esercizi

### Esercizio 1 — TCO della tua Azienda (20 min)

```python
from tco_calculator import ScenarioUso, calcola_tco_n8n_self_hosted, calcola_tco_make, stampa_tco

mio_scenario = ScenarioUso(
    nome="Il mio caso d'uso",
    operazioni_mese=...,          # Stima le tue operazioni mensili
    n_workflow=...,               # Quanti workflow da costruire
    n_utenti=...,                 # Utenti della piattaforma
    ore_sviluppo_iniziale=...,    # Ore totali per implementare
    ore_manutenzione_mese=...,    # Ore/mese manutenzione
    tariffa_oraria=35.0,         # Costo orario team
)

risultati = [calcola_tco_n8n_self_hosted(mio_scenario), calcola_tco_make(mio_scenario)]
stampa_tco(risultati)
```

### Esercizio 2 — Break-Even Analysis (15 min)

A quale volume di operazioni diventa conveniente n8n self-hosted rispetto a Make?

```python
for ops in [5_000, 10_000, 25_000, 50_000, 100_000, 250_000]:
    scenario = ScenarioUso("test", ops, 10, 2, 80.0, 4.0, 35.0)
    n8n = calcola_tco_n8n_self_hosted(scenario).tco_3anni
    make = calcola_tco_make(scenario).tco_3anni
    winner = "n8n" if n8n < make else "Make"
    diff = abs(n8n - make)
    print(f"  {ops:>8,} ops/mese → {winner} (diff: €{diff:,.0f})")
```

---

## Riferimenti

- n8n Docs: https://docs.n8n.io/
- Make (Integromat) Pricing: https://www.make.com/en/pricing
- Zapier Pricing: https://zapier.com/pricing
- Power Automate Pricing: https://powerautomate.microsoft.com/pricing/
- Modulo sorgente: `02-piattaforme-low-code.md`
