# Tutorial Lab — Governance dei Workflow: Inventario, Approval Gate e Change Management

> **Campo di studio:** 09-AUTOMAZIONI-FLUSSI-DI-LAVORO
> **Modulo sorgente:** `07-governance-automazione.md`
> **Livello:** intermediate
> **Tempo stimato:** 2.5 ore
> **Prerequisiti:** Python 3.11+, conoscenza base YAML/JSON, accesso Git
> **Versioni di riferimento:** Python 3.11+, PyYAML 6.x, SQLite (stdlib)

---

## Obiettivi del Lab

Al termine di questo tutorial saprai:

1. Costruire un inventario centralizzato di tutti i workflow attivi
2. Implementare un approval gate per le modifiche ai workflow critici
3. Gestire il change management con audit trail immutabile
4. Classificare workflow per criticità e proprietà
5. Generare documentazione automatica dall'inventario
6. Configurare notifiche per workflow deprecati o senza proprietario

---

## Lab Environment Setup

```bash
# Dipendenze
pip install pyyaml jinja2 sqlite-utils structlog

# Struttura directory del lab
mkdir -p governance/{inventario,approvazioni,templates,audit}
touch governance/__init__.py
```

---

## Analogia Introduttiva

> **La governance dei workflow è come il registro fondiario di un comune**:
> ogni proprietà (workflow) ha un proprietario registrato,
> una categoria (residenziale/commerciale/industriale → low/medium/critical),
> e qualsiasi modifica richiede permesso edilizio (approval gate).
>
> Senza registro: nessuno sa quante automazioni esistono,
> chi le gestisce, o cosa succede quando il proprietario cambia azienda.
>
> Con registro: puoi rispondere in 30 secondi a "chi è responsabile
> del workflow che processa le fatture estere?" e bloccare modifiche
> non autorizzate con un processo approvativo documentato.

---

## Architettura Governance

```
┌──────────────────────────────────────────────────────────────────────┐
│                    SISTEMA DI GOVERNANCE                              │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                 INVENTARIO (SQLite)                          │    │
│  │  workflow_id │ nome │ piattaforma │ owner │ criticità │ ...  │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                         ▲                   ▲                         │
│                 SYNC/IMPORT                AUDIT TRAIL                │
│                         │                   │                         │
│  ┌──────────────────────┤                   ├──────────────────────┐  │
│  │  n8n API             │                   │  change_log.sqlite   │  │
│  │  Make export         │                   │  (append-only)       │  │
│  │  YAML manifests      │                   └──────────────────────┘  │
│  └──────────────────────┘                                             │
│                                                                       │
│  APPROVAL GATE:                                                       │
│  [Richiesta modifica] → [Classificazione] → [Approvatori notificati] │
│         │                                         │                   │
│         ▼                                         ▼                   │
│  [Audit log: stato=pending]            [Audit log: stato=approved]   │
│         │                                                             │
│         ▼ (dopo approvazione)                                         │
│  [Deploy workflow modificato]                                         │
│  [Audit log: stato=deployed]                                         │
└──────────────────────────────────────────────────────────────────────┘
```

---

## PART A — Inventario Centralizzato

### A1 — Schema Workflow Manifest (YAML)

```yaml
# governance/inventario/fatturazione-mensile.yaml
# Manifest YAML per ogni workflow in governance

workflow:
  id: "WF-FINANCE-001"
  nome: "Fatturazione Mensile"
  descrizione: >
    Genera e invia fatture mensili per tutti i clienti attivi.
    Eseguito il 28 di ogni mese alle 06:00.
  
  classificazione:
    criticità: "critical"          # low | medium | high | critical
    dominio: "finance"
    impatto_business: "alto"       # basso | medio | alto
    dati_sensibili: true           # contiene PII o dati finanziari?
    gdpr_relevant: true
  
  piattaforma:
    tipo: "n8n"                    # n8n | make | zapier | python | ansible
    endpoint: "http://n8n:5678"
    workflow_id_esterno: "42"      # ID interno alla piattaforma
    versione: "2.1.0"
  
  ownership:
    team: "Finance Engineering"
    owner_primario: "lucia.verdi@azienda.it"
    owner_backup: "marco.bianchi@azienda.it"
    stakeholder:
      - "cfo@azienda.it"
      - "contabilita@azienda.it"
  
  schedule:
    tipo: "cron"
    espressione: "0 6 28 * *"     # min ora giorno mese weekday
    timezone: "Europe/Rome"
    durata_attesa_max: "2h"       # alert se supera questa durata
  
  dipendenze:
    servizi_esterni:
      - nome: "ERP Finance"
        url: "https://erp.azienda.it/api"
        timeout: "30s"
        critico: true
      - nome: "SMTP Provider"
        url: "smtp://mail.azienda.it:587"
        critico: true
    workflow_dipendenti:
      - "WF-FINANCE-003"           # Riconciliazione dipende da questo
  
  monitoring:
    alert_on_failure: true
    alert_email:
      - "lucia.verdi@azienda.it"
      - "itops@azienda.it"
    sla_max_errori_consecutivi: 1  # alert dopo N errori consecutivi
  
  governance:
    data_creazione: "2025-03-01"
    ultima_revisione: "2026-01-10"
    prossima_revisione: "2026-07-10"   # revisione semestrale
    approvazione_richiesta: true        # true = richiede approval per modifiche
    approvatori:
      - "cfo@azienda.it"
      - "cto@azienda.it"
    stato: "active"                     # active | deprecated | disabled | draft
    note_deprecazione: ""
```

### A2 — Inventario Manager Python

```python
# governance/inventario_manager.py
from __future__ import annotations

import sqlite3
import yaml
from dataclasses import dataclass, asdict
from datetime import date
from pathlib import Path
from typing import Iterator

import structlog

log = structlog.get_logger()

DB_PATH = Path("governance/inventario.sqlite")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS workflow (
    id TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    descrizione TEXT,
    criticita TEXT NOT NULL,
    dominio TEXT,
    piattaforma TEXT NOT NULL,
    owner TEXT NOT NULL,
    owner_backup TEXT,
    stato TEXT NOT NULL DEFAULT 'active',
    data_creazione TEXT,
    ultima_revisione TEXT,
    prossima_revisione TEXT,
    approvazione_richiesta INTEGER NOT NULL DEFAULT 0,
    dati_sensibili INTEGER NOT NULL DEFAULT 0,
    gdpr_relevant INTEGER NOT NULL DEFAULT 0,
    schedule TEXT,
    raw_yaml TEXT
);

CREATE TABLE IF NOT EXISTS workflow_tag (
    workflow_id TEXT NOT NULL,
    tag TEXT NOT NULL,
    FOREIGN KEY (workflow_id) REFERENCES workflow(id)
);
"""

def init_db(db_path: Path = DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    return conn

def importa_da_yaml(manifest_path: Path, conn: sqlite3.Connection) -> str:
    """Importa o aggiorna un workflow dall'YAML manifest. Restituisce il workflow_id."""
    raw = manifest_path.read_text(encoding="utf-8")
    dati = yaml.safe_load(raw)
    wf = dati["workflow"]
    wf_id = wf["id"]

    conn.execute("""
        INSERT INTO workflow (id, nome, descrizione, criticita, dominio, piattaforma,
            owner, owner_backup, stato, data_creazione, ultima_revisione,
            prossima_revisione, approvazione_richiesta, dati_sensibili, gdpr_relevant,
            schedule, raw_yaml)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            nome=excluded.nome,
            descrizione=excluded.descrizione,
            criticita=excluded.criticita,
            dominio=excluded.dominio,
            owner=excluded.owner,
            owner_backup=excluded.owner_backup,
            stato=excluded.stato,
            ultima_revisione=excluded.ultima_revisione,
            prossima_revisione=excluded.prossima_revisione,
            approvazione_richiesta=excluded.approvazione_richiesta,
            raw_yaml=excluded.raw_yaml
    """, (
        wf_id, wf["nome"], wf.get("descrizione", ""),
        wf["classificazione"]["criticità"],
        wf["classificazione"].get("dominio", ""),
        wf["piattaforma"]["tipo"],
        wf["ownership"]["owner_primario"],
        wf["ownership"].get("owner_backup", ""),
        wf["governance"]["stato"],
        wf["governance"]["data_creazione"],
        wf["governance"]["ultima_revisione"],
        wf["governance"]["prossima_revisione"],
        int(wf["governance"]["approvazione_richiesta"]),
        int(wf["classificazione"]["dati_sensibili"]),
        int(wf["classificazione"]["gdpr_relevant"]),
        wf.get("schedule", {}).get("espressione", ""),
        raw,
    ))
    conn.commit()
    log.info("workflow_importato", workflow_id=wf_id, path=str(manifest_path))
    return wf_id

def sync_inventario(directory: Path, conn: sqlite3.Connection) -> dict[str, int]:
    """Sincronizza tutti gli YAML in una directory. Restituisce statistiche."""
    manifest_files = list(directory.glob("*.yaml"))
    importati = 0
    errori = 0
    for f in manifest_files:
        try:
            importa_da_yaml(f, conn)
            importati += 1
        except Exception as e:
            log.error("errore_import", file=str(f), errore=str(e))
            errori += 1
    return {"importati": importati, "errori": errori, "totale": len(manifest_files)}

def cerca_workflow(conn: sqlite3.Connection,
                   criticita: str | None = None,
                   dominio: str | None = None,
                   owner: str | None = None,
                   stato: str = "active") -> list[sqlite3.Row]:
    condizioni = ["stato = ?"]
    parametri: list = [stato]
    if criticita:
        condizioni.append("criticita = ?")
        parametri.append(criticita)
    if dominio:
        condizioni.append("dominio = ?")
        parametri.append(dominio)
    if owner:
        condizioni.append("(owner = ? OR owner_backup = ?)")
        parametri.extend([owner, owner])
    where = " AND ".join(condizioni)
    return conn.execute(f"SELECT * FROM workflow WHERE {where} ORDER BY criticita DESC, nome", parametri).fetchall()

def workflow_in_revisione_entro(conn: sqlite3.Connection, giorni: int = 30) -> list[sqlite3.Row]:
    """Workflow con revisione scaduta o in scadenza entro N giorni."""
    oggi = date.today().isoformat()
    limite = date.today().replace(day=date.today().day + giorni).isoformat() if giorni < 28 else (
        f"{date.today().year + (1 if date.today().month + giorni // 30 > 12 else 0)}-"
        f"{((date.today().month + giorni // 30 - 1) % 12) + 1:02d}-"
        f"{date.today().day:02d}"
    )
    return conn.execute("""
        SELECT * FROM workflow
        WHERE stato = 'active' AND prossima_revisione <= ?
        ORDER BY prossima_revisione
    """, (limite,)).fetchall()
```

---

## PART B — Approval Gate

### B1 — Sistema di Approvazione Modifiche

```python
# governance/approval_gate.py
from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path

import structlog

log = structlog.get_logger()

class StatoApprovazione(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"

SCHEMA_APPROVAZIONI = """
CREATE TABLE IF NOT EXISTS richiesta_modifica (
    id TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL,
    richiedente TEXT NOT NULL,
    tipo_modifica TEXT NOT NULL,
    descrizione TEXT NOT NULL,
    hash_vecchia_versione TEXT,
    hash_nuova_versione TEXT,
    stato TEXT NOT NULL DEFAULT 'pending',
    creata_at TEXT NOT NULL,
    scade_at TEXT NOT NULL,
    approvata_at TEXT,
    approvata_da TEXT,
    note TEXT,
    FOREIGN KEY (workflow_id) REFERENCES workflow(id)
);

CREATE TABLE IF NOT EXISTS voto_approvazione (
    id TEXT PRIMARY KEY,
    richiesta_id TEXT NOT NULL,
    approvatore TEXT NOT NULL,
    voto TEXT NOT NULL,           -- approved | rejected
    commento TEXT,
    votato_at TEXT NOT NULL,
    FOREIGN KEY (richiesta_id) REFERENCES richiesta_modifica(id)
);
"""

@dataclass
class RichiestaModifica:
    workflow_id: str
    richiedente: str
    tipo_modifica: str       # "logica" | "schedule" | "credenziali" | "deprecazione"
    descrizione: str
    vecchia_versione: str | None = None
    nuova_versione: str | None = None

def crea_richiesta(richiesta: RichiestaModifica, conn: sqlite3.Connection,
                    ore_validita: int = 72) -> str:
    """Crea una richiesta di modifica. Restituisce l'ID della richiesta."""
    richiesta_id = str(uuid.uuid4())[:8].upper()
    ora = datetime.utcnow()
    hash_vecchio = (
        hashlib.sha256(richiesta.vecchia_versione.encode()).hexdigest()[:16]
        if richiesta.vecchia_versione else None
    )
    hash_nuovo = (
        hashlib.sha256(richiesta.nuova_versione.encode()).hexdigest()[:16]
        if richiesta.nuova_versione else None
    )
    conn.execute("""
        INSERT INTO richiesta_modifica
            (id, workflow_id, richiedente, tipo_modifica, descrizione,
             hash_vecchia_versione, hash_nuova_versione, stato, creata_at, scade_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
    """, (
        richiesta_id, richiesta.workflow_id, richiesta.richiedente,
        richiesta.tipo_modifica, richiesta.descrizione,
        hash_vecchio, hash_nuovo,
        ora.isoformat(),
        ora.replace(hour=ora.hour + ore_validita % 24,
                    day=ora.day + ore_validita // 24).isoformat(),
    ))
    conn.commit()
    log.info("richiesta_creata",
             richiesta_id=richiesta_id,
             workflow_id=richiesta.workflow_id,
             richiedente=richiesta.richiedente,
             tipo=richiesta.tipo_modifica)
    return richiesta_id

def vota(richiesta_id: str, approvatore: str, voto: str,
         commento: str, conn: sqlite3.Connection) -> None:
    """Registra un voto (approved/rejected) di un approvatore."""
    if voto not in ("approved", "rejected"):
        raise ValueError(f"Voto non valido: {voto}")
    conn.execute("""
        INSERT INTO voto_approvazione (id, richiesta_id, approvatore, voto, commento, votato_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT DO NOTHING
    """, (str(uuid.uuid4()), richiesta_id, approvatore, voto,
          commento, datetime.utcnow().isoformat()))
    conn.commit()
    log.info("voto_registrato",
             richiesta_id=richiesta_id, approvatore=approvatore, voto=voto)

def calcola_consenso(richiesta_id: str, conn: sqlite3.Connection,
                      quorum: int = 2) -> StatoApprovazione:
    """Determina lo stato corrente basato sui voti ricevuti."""
    voti = conn.execute("""
        SELECT voto, COUNT(*) as n FROM voto_approvazione
        WHERE richiesta_id = ? GROUP BY voto
    """, (richiesta_id,)).fetchall()
    voti_dict = {v["voto"]: v["n"] for v in voti}
    approvazioni = voti_dict.get("approved", 0)
    rifiuti = voti_dict.get("rejected", 0)
    if rifiuti > 0:
        return StatoApprovazione.REJECTED
    if approvazioni >= quorum:
        return StatoApprovazione.APPROVED
    return StatoApprovazione.PENDING
```

---

## PART C — Documentazione Automatica

### C1 — Generatore Report Inventario

```python
# governance/genera_report.py
from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path

from jinja2 import Environment, BaseLoader

TEMPLATE_MARKDOWN = """
# Inventario Workflow Automazione
*Generato il {{ data_generazione }}*

## Sommario

| Criticità | Conteggio |
|-----------|-----------|
{% for c in sommario_criticita %}| {{ c.criticita }} | {{ c.conteggio }} |
{% endfor %}

**Totale workflow attivi:** {{ totale }}

---

## Workflow per Dominio

{% for dominio, workflows in per_dominio.items() %}
### {{ dominio | title }}

{% for wf in workflows %}
#### {{ wf['nome'] }} (`{{ wf['id'] }}`)
- **Owner:** {{ wf['owner'] }}{% if wf['owner_backup'] %} / {{ wf['owner_backup'] }}{% endif %}
- **Piattaforma:** {{ wf['piattaforma'] }}
- **Criticità:** {{ wf['criticita'] }}
- **Dati sensibili:** {{ 'Sì' if wf['dati_sensibili'] else 'No' }}
- **Prossima revisione:** {{ wf['prossima_revisione'] }}

{% endfor %}
{% endfor %}

---

## Workflow in Scadenza Revisione (prossimi 30 giorni)

{% if in_revisione %}
| ID | Nome | Owner | Revisione |
|----|------|-------|-----------|
{% for wf in in_revisione %}| {{ wf['id'] }} | {{ wf['nome'] }} | {{ wf['owner'] }} | {{ wf['prossima_revisione'] }} |
{% endfor %}
{% else %}
*Nessun workflow in scadenza.*
{% endif %}
"""

def genera_report_markdown(conn: sqlite3.Connection, output_path: Path) -> None:
    workflow_attivi = conn.execute(
        "SELECT * FROM workflow WHERE stato='active' ORDER BY dominio, criticita DESC, nome"
    ).fetchall()

    sommario = conn.execute("""
        SELECT criticita, COUNT(*) as conteggio
        FROM workflow WHERE stato='active'
        GROUP BY criticita ORDER BY criticita DESC
    """).fetchall()

    per_dominio: dict[str, list] = {}
    for wf in workflow_attivi:
        dom = wf["dominio"] or "altri"
        per_dominio.setdefault(dom, []).append(dict(wf))

    oggi = date.today().isoformat()
    limite_30gg = date.today().replace(month=date.today().month + 1 if date.today().month < 12 else 1,
                                       year=date.today().year if date.today().month < 12 else date.today().year + 1)
    in_revisione = conn.execute("""
        SELECT id, nome, owner, prossima_revisione FROM workflow
        WHERE stato='active' AND prossima_revisione <= ?
        ORDER BY prossima_revisione
    """, (limite_30gg.isoformat(),)).fetchall()

    env = Environment(loader=BaseLoader())
    template = env.from_string(TEMPLATE_MARKDOWN)
    contenuto = template.render(
        data_generazione=oggi,
        sommario_criticita=[dict(r) for r in sommario],
        totale=len(workflow_attivi),
        per_dominio=per_dominio,
        in_revisione=[dict(r) for r in in_revisione],
    )
    output_path.write_text(contenuto, encoding="utf-8")
    print(f"Report generato: {output_path} ({len(workflow_attivi)} workflow)")
```

---

## PART D — Change Log Audit Trail

### D1 — Log Immutabile delle Modifiche

```python
# governance/audit_trail.py
from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime
from pathlib import Path

SCHEMA_AUDIT = """
CREATE TABLE IF NOT EXISTS audit_log (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    tipo_evento TEXT NOT NULL,
    workflow_id TEXT NOT NULL,
    attore TEXT NOT NULL,
    dettagli TEXT NOT NULL,
    hash_evento TEXT NOT NULL,
    hash_precedente TEXT
);
"""

def calcola_hash_evento(timestamp: str, tipo: str, wf_id: str,
                          attore: str, dettagli: str, hash_prec: str | None) -> str:
    contenuto = f"{timestamp}|{tipo}|{wf_id}|{attore}|{dettagli}|{hash_prec or ''}"
    return hashlib.sha256(contenuto.encode()).hexdigest()[:32]

def registra_evento(conn: sqlite3.Connection,
                     tipo_evento: str, workflow_id: str,
                     attore: str, dettagli: dict) -> int:
    """Registra evento nell'audit trail con chain di hash. Restituisce seq."""
    ultimo = conn.execute(
        "SELECT hash_evento FROM audit_log ORDER BY seq DESC LIMIT 1"
    ).fetchone()
    hash_prec = ultimo["hash_evento"] if ultimo else None
    ts = datetime.utcnow().isoformat()
    dettagli_str = json.dumps(dettagli, ensure_ascii=False, sort_keys=True)
    hash_ev = calcola_hash_evento(ts, tipo_evento, workflow_id, attore, dettagli_str, hash_prec)
    cursor = conn.execute("""
        INSERT INTO audit_log (timestamp, tipo_evento, workflow_id, attore, dettagli, hash_evento, hash_precedente)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (ts, tipo_evento, workflow_id, attore, dettagli_str, hash_ev, hash_prec))
    conn.commit()
    return cursor.lastrowid

def verifica_integrita_audit(conn: sqlite3.Connection) -> tuple[bool, list[int]]:
    """Verifica la chain di hash. Restituisce (integra, seq_corrotti)."""
    eventi = conn.execute(
        "SELECT seq, timestamp, tipo_evento, workflow_id, attore, dettagli, hash_evento, hash_precedente "
        "FROM audit_log ORDER BY seq"
    ).fetchall()
    corrotti = []
    hash_prec_atteso = None
    for ev in eventi:
        hash_calc = calcola_hash_evento(
            ev["timestamp"], ev["tipo_evento"],
            ev["workflow_id"], ev["attore"],
            ev["dettagli"], hash_prec_atteso,
        )
        if hash_calc != ev["hash_evento"]:
            corrotti.append(ev["seq"])
        hash_prec_atteso = ev["hash_evento"]
    return len(corrotti) == 0, corrotti
```

---

## Esercizi

### Esercizio 1 — Import Batch Manifests (20 min)

1. Crea almeno 3 file YAML nella cartella `governance/inventario/` (usando il template della sezione A1)
2. Esegui `sync_inventario()` per importarli nel database
3. Usa `cerca_workflow(conn, criticita="critical")` per trovare i workflow critici
4. Verifica che `workflow_in_revisione_entro(conn, 90)` restituisca risultati sensati

### Esercizio 2 — Approval Pipeline Completa (30 min)

Simula il ciclo completo:
1. Crea richiesta modifica per un workflow "critical"
2. Registra 2 voti "approved" da due approvatori diversi
3. Verifica che `calcola_consenso()` restituisca `APPROVED` con quorum=2
4. Registra l'evento nell'audit trail con `registra_evento()`
5. Verifica l'integrità con `verifica_integrita_audit()`

### Esercizio 3 — Report Automatico (15 min)

Esegui `genera_report_markdown()` e analizza il Markdown generato:
- Quanti workflow sono nel tuo inventario?
- Quali sono in scadenza revisione?
- Aggiungi una sezione "Workflow senza owner_backup" al template

---

## Riferimenti

- PyYAML: https://pyyaml.org/wiki/PyYAMLDocumentation
- Jinja2: https://jinja.palletsprojects.com/
- SQLite Python: https://docs.python.org/3/library/sqlite3.html
- Modulo sorgente: `07-governance-automazione.md`
