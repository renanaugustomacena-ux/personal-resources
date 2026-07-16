# Tutorial Lab — Workflow Versioning e Rollback Strategies

> **Campo di studio:** 09-AUTOMAZIONI-FLUSSI-DI-LAVORO
> **Modulo sorgente:** `18-workflow-versioning-rollback.md`
> **Livello:** intermediate
> **Tempo stimato:** 2-3 ore
> **Prerequisiti:** Git base, n8n basic, concetti di CI/CD
> **Versioni di riferimento:** n8n 1.x · Git 2.x · Python 3.11+

---

## Obiettivi del Lab

Al termine di questo tutorial saprai:

1. Versionare workflow n8n come JSON in Git con pipeline CI/CD
2. Applicare strategie di deployment: blue-green e canary per workflow
3. Implementare rollback automatico su failure detection
4. Comparare versioni di workflow con diff leggibile
5. Gestire environment-specific variables (dev/staging/prod)
6. Costruire un change management process per workflow critici

---

## Lab Environment Setup

```bash
git --version         # 2.x
python3 --version     # 3.11+
jq --version          # Per parsing JSON (opzionale ma utile)

# Struttura progetto
mkdir -p workflow-versioning/{workflows,scripts,ci,environments}
cd workflow-versioning
git init
```

---

## Analogia Introduttiva

> **Il versioning dei workflow è come tenere un registro delle ricette**:
> ogni volta che modifichi la ricetta del ragù,
> non la cancelli — la annoti con data e motivazione.
> Se la nuova versione risulta peggio dell'originale,
> puoi tornare esattamente alla versione di 3 mesi fa.
>
> Il **rollback** è l'equivalente di trovare il vecchio quaderno:
> "ah sì, usavo il vino bianco non il rosso — torniamo a quella versione".
>
> In produzione, un workflow gestisce pagamenti, ordini, fatture.
> Senza versioning: un bug → non sai cosa hai cambiato,
> non puoi tornare indietro, perdi ore a debuggare.
> Con versioning: rollback in 5 minuti, audit trail completo.

---

## Architettura Versioning

```
developer ──git commit──▶ repository
                               │
                       ┌───────▼───────┐
                       │   CI PIPELINE  │
                       │               │
                       │  ✓ validate   │
                       │  ✓ lint       │
                       │  ✓ test       │
                       └───────┬───────┘
                               │ approved PR
                    ┌──────────▼──────────┐
                    │  DEPLOYMENT SCRIPT   │
                    │                      │
                    │  dev → staging → prod│
                    │  (con gate manuali)  │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼──────────────────┐
              ▼                ▼                   ▼
       n8n-DEV            n8n-STAGING          n8n-PROD
    (auto deploy)      (gate: QA approval)   (gate: prod deploy)
    
ROLLBACK:
  detection:  error rate > threshold | manual trigger
  action:     git revert + redeploy precedente versione
  tempo:      < 5 minuti
```

---

## PART A — Workflow come Codice

### A1 — Struttura Repository Workflow

```bash
# Struttura raccomandata per workflow n8n versionati in Git

workflow-versioning/
├── workflows/
│   ├── ordini-processing/
│   │   ├── workflow.json          ← Workflow n8n esportato
│   │   ├── README.md              ← Descrizione, trigger, dipendenze
│   │   └── tests/
│   │       └── test_ordine_completo.py
│   │
│   ├── fatture-sdi/
│   │   ├── workflow.json
│   │   ├── README.md
│   │   └── tests/
│   │
│   └── newsletter-automation/
│       ├── workflow.json
│       └── README.md
│
├── environments/
│   ├── dev.env.json               ← Variabili dev (no segreti!)
│   ├── staging.env.json           ← Variabili staging
│   └── prod.env.json              ← Variabili prod
│
├── scripts/
│   ├── export_workflow.sh         ← Esporta workflow da n8n via API
│   ├── import_workflow.sh         ← Importa workflow in n8n via API
│   ├── validate_workflow.py       ← Valida JSON workflow
│   └── diff_workflow.py           ← Confronto visuale versioni
│
└── ci/
    ├── .github/workflows/
    │   └── deploy-workflows.yml   ← GitHub Actions
    └── .gitlab-ci.yml             ← GitLab CI (alternativa)
```

### A2 — Script Export/Import via API n8n

```bash
#!/usr/bin/env bash
# file: scripts/export_workflow.sh
# Esporta tutti i workflow da n8n via API REST
# n8n espone: GET /api/v1/workflows

set -euo pipefail

N8N_URL="${N8N_URL:-http://localhost:5678}"
N8N_API_KEY="${N8N_API_KEY:?Variabile N8N_API_KEY obbligatoria}"
OUTPUT_DIR="${1:-./workflows}"

echo "Export workflow da ${N8N_URL}..."

# Lista tutti i workflow
workflows=$(curl -s \
    -H "X-N8N-API-KEY: ${N8N_API_KEY}" \
    "${N8N_URL}/api/v1/workflows" | \
    python3 -c "import json,sys; [print(w['id'], w['name']) for w in json.load(sys.stdin)['data']]"
)

while IFS=" " read -r wf_id wf_name; do
    # Sanitizza nome per filesystem
    safe_name=$(echo "${wf_name}" | tr " /" "_-" | tr '[:upper:]' '[:lower:]')
    out_dir="${OUTPUT_DIR}/${safe_name}"
    mkdir -p "${out_dir}"
    
    # Esporta workflow completo
    curl -s \
        -H "X-N8N-API-KEY: ${N8N_API_KEY}" \
        "${N8N_URL}/api/v1/workflows/${wf_id}" \
        | python3 -c "
import json, sys
wf = json.load(sys.stdin)
# Rimuovi campi non-deterministic (timestamps, IDs interni non necessari)
wf.pop('updatedAt', None)
wf.pop('createdAt', None)
print(json.dumps(wf, indent=2, ensure_ascii=False, sort_keys=True))
" > "${out_dir}/workflow.json"
    
    echo "  Esportato: ${wf_name} → ${out_dir}/workflow.json"
done <<< "${workflows}"

echo "Export completato!"
```

```bash
#!/usr/bin/env bash
# file: scripts/import_workflow.sh
# Importa/aggiorna workflow in n8n via API

set -euo pipefail

N8N_URL="${N8N_URL:-http://localhost:5678}"
N8N_API_KEY="${N8N_API_KEY:?}"
WORKFLOW_JSON="${1:?Percorso workflow.json richiesto}"
ENV_FILE="${2:-./environments/dev.env.json}"

echo "Import workflow: ${WORKFLOW_JSON}"

# Leggi variabili ambiente e iniettale nel workflow
python3 - "${WORKFLOW_JSON}" "${ENV_FILE}" << 'PYEOF'
import json, sys

wf_path = sys.argv[1]
env_path = sys.argv[2]

with open(wf_path) as f:
    wf = json.load(f)

try:
    with open(env_path) as f:
        env = json.load(f)
except FileNotFoundError:
    env = {}

# Sostituisci placeholder %%VAR%% con variabili ambiente
wf_str = json.dumps(wf)
for key, value in env.items():
    wf_str = wf_str.replace(f"%%{key}%%", str(value))

wf_final = json.loads(wf_str)

# Verifica che non rimangano placeholder non sostituiti
import re
rimasti = re.findall(r'%%\w+%%', wf_str)
if rimasti:
    print(f"WARNING: Placeholder non sostituiti: {rimasti}", file=sys.stderr)

print(json.dumps(wf_final))
PYEOF
```

### A3 — Validatore Workflow

```python
#!/usr/bin/env python3
# file: scripts/validate_workflow.py
"""
Validatore per workflow n8n JSON.
Controlla: struttura, segreti hard-coded, nodi deprecati, connessioni.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProblemaValidazione:
    livello: str   # "ERROR" | "WARNING" | "INFO"
    messaggio: str
    percorso: str = ""


def valida_workflow(wf_path: Path) -> list[ProblemaValidazione]:
    """Valida un workflow n8n e ritorna lista di problemi."""
    problemi: list[ProblemaValidazione] = []
    
    try:
        with open(wf_path) as f:
            wf = json.load(f)
    except json.JSONDecodeError as e:
        return [ProblemaValidazione("ERROR", f"JSON non valido: {e}")]
    
    # ─── Struttura obbligatoria ────────────────────────────────────────
    for campo in ["name", "nodes", "connections"]:
        if campo not in wf:
            problemi.append(ProblemaValidazione(
                "ERROR", f"Campo obbligatorio mancante: '{campo}'"
            ))
    
    if "nodes" not in wf:
        return problemi  # Non possiamo continuare senza nodi
    
    nodes = wf.get("nodes", [])
    
    # ─── Check segreti hard-coded ─────────────────────────────────────
    pattern_segreti = [
        r"(?i)password['\"\s]*[:=]['\"\s]*\w{4,}",
        r"(?i)api_key['\"\s]*[:=]['\"\s]*\w{8,}",
        r"(?i)secret['\"\s]*[:=]['\"\s]*\w{8,}",
        r"(?i)token['\"\s]*[:=]['\"\s]*[a-zA-Z0-9\-_]{20,}",
        r"Bearer\s+[a-zA-Z0-9\-_\.]{30,}",
    ]
    wf_str = json.dumps(wf)
    for pattern in pattern_segreti:
        if re.search(pattern, wf_str):
            problemi.append(ProblemaValidazione(
                "ERROR",
                f"Possibile segreto hard-coded rilevato (pattern: {pattern[:40]}). "
                "Usa variabili d'ambiente o Credential store n8n."
            ))
    
    # ─── Placeholder non sostituiti ───────────────────────────────────
    placeholder = re.findall(r"%%\w+%%", wf_str)
    for ph in set(placeholder):
        problemi.append(ProblemaValidazione(
            "WARNING", f"Placeholder non sostituito: {ph}"
        ))
    
    # ─── Nodi senza connessione (orphan nodes) ─────────────────────────
    nodo_ids = {n.get("id") for n in nodes if n.get("id")}
    connections = wf.get("connections", {})
    nodi_connessi = set()
    
    for source_nodo, conn_data in connections.items():
        nodi_connessi.add(source_nodo)
        for output_list in conn_data.get("main", []):
            for conn in output_list:
                nodi_connessi.add(conn.get("node", ""))
    
    nomi_nodi = {n.get("name") for n in nodes}
    orfani = nomi_nodi - nodi_connessi
    
    # Il trigger node è correttamente non connesso come input
    for nodo in nodes:
        if nodo.get("type", "").startswith("n8n-nodes-base.webhook") or \
           nodo.get("type", "").startswith("n8n-nodes-base.manualTrigger"):
            orfani.discard(nodo.get("name"))
    
    for orfano in orfani:
        if orfano:
            problemi.append(ProblemaValidazione(
                "WARNING", f"Nodo non connesso (possibile orfano): '{orfano}'"
            ))
    
    # ─── Nodi disabilitati ────────────────────────────────────────────
    nodi_disabilitati = [n.get("name") for n in nodes if n.get("disabled")]
    for nd in nodi_disabilitati:
        problemi.append(ProblemaValidazione(
            "INFO", f"Nodo disabilitato: '{nd}' (intenzionale?)"
        ))
    
    return problemi


def valida_directory(workflows_dir: Path) -> int:
    """Valida tutti i workflow.json in una directory. Ritorna n. errori."""
    errori_totali = 0
    
    for wf_file in sorted(workflows_dir.rglob("workflow.json")):
        print(f"\n  Validazione: {wf_file}")
        problemi = valida_workflow(wf_file)
        
        if not problemi:
            print("    ✓ Nessun problema trovato")
            continue
        
        for p in problemi:
            simbolo = "✗" if p.livello == "ERROR" else "⚠" if p.livello == "WARNING" else "ℹ"
            print(f"    {simbolo} [{p.livello}] {p.messaggio}")
            if p.livello == "ERROR":
                errori_totali += 1
    
    return errori_totali


if __name__ == "__main__":
    workflows_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("./workflows")
    
    if not workflows_dir.exists():
        print(f"Directory non trovata: {workflows_dir}")
        sys.exit(2)
    
    print(f"Validazione workflow in: {workflows_dir}")
    errori = valida_directory(workflows_dir)
    
    if errori > 0:
        print(f"\n✗ Trovati {errori} errori — commit bloccato")
        sys.exit(1)
    else:
        print("\n✓ Tutti i workflow validi")
        sys.exit(0)
```

---

## PART B — Deployment Strategies

### B1 — Blue-Green Deployment per Workflow

```python
#!/usr/bin/env python3
# file: scripts/blue_green_deploy.py
"""
Blue-Green deployment per workflow n8n.

Concetto:
  BLUE = versione corrente in produzione (attiva)
  GREEN = nuova versione (preparata ma inattiva)
  
  Deploy: attiva GREEN, verifica, poi disattiva BLUE
  Rollback: attiva BLUE, disattiva GREEN (in < 30 secondi)
  
In n8n: si implementa tramite workflow attivi/inattivi
+ routing via variabile d'ambiente che punta al workflow ID corretto.
"""
from __future__ import annotations

import json
import time
import httpx
import os
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ColoreDeployment(str, Enum):
    BLUE = "blue"
    GREEN = "green"


@dataclass
class WorkflowDeployment:
    """Rappresenta una versione deployata di un workflow."""
    workflow_id: str
    colore: ColoreDeployment
    nome: str
    versione_git: str
    deployato_at: float
    attivo: bool


class BlueGreenDeployer:
    """
    Gestisce blue-green deployment per workflow n8n.
    
    Prerequisito: due versioni del workflow già presenti in n8n,
    una con suffisso " [BLUE]" e una con " [GREEN]".
    """

    def __init__(self, n8n_url: str, api_key: str):
        self._base_url = n8n_url
        self._headers = {"X-N8N-API-KEY": api_key}

    def _get(self, path: str) -> dict:
        with httpx.Client() as client:
            r = client.get(f"{self._base_url}{path}", headers=self._headers, timeout=10)
            r.raise_for_status()
            return r.json()

    def _patch(self, path: str, json_data: dict) -> dict:
        with httpx.Client() as client:
            r = client.patch(f"{self._base_url}{path}", headers=self._headers,
                            json=json_data, timeout=10)
            r.raise_for_status()
            return r.json()

    def trova_coppia(self, nome_base: str) -> tuple[Optional[str], Optional[str]]:
        """
        Trova gli ID dei workflow [BLUE] e [GREEN].
        Ritorna (blue_id, green_id).
        """
        workflows = self._get("/api/v1/workflows")["data"]
        blue_id = None
        green_id = None
        
        for wf in workflows:
            if wf["name"] == f"{nome_base} [BLUE]":
                blue_id = wf["id"]
            elif wf["name"] == f"{nome_base} [GREEN]":
                green_id = wf["id"]
        
        return blue_id, green_id

    def attiva_workflow(self, wf_id: str, attivo: bool) -> None:
        """Attiva o disattiva un workflow."""
        self._patch(f"/api/v1/workflows/{wf_id}", {"active": attivo})

    def deploy(
        self,
        nome_base: str,
        nuovo_colore: ColoreDeployment = ColoreDeployment.GREEN,
        verify_fn=None,
        verify_timeout_s: float = 30.0,
    ) -> bool:
        """
        Esegue il deployment:
        1. Attiva il nuovo colore
        2. Verifica (se verify_fn fornita)
        3. Disattiva il vecchio colore
        4. Rollback se verifica fallisce
        """
        blue_id, green_id = self.trova_coppia(nome_base)
        
        if not blue_id or not green_id:
            raise ValueError(f"Non trovata coppia BLUE/GREEN per '{nome_base}'")
        
        nuovo_id = green_id if nuovo_colore == ColoreDeployment.GREEN else blue_id
        vecchio_id = blue_id if nuovo_colore == ColoreDeployment.GREEN else green_id
        
        print(f"Deploy {nome_base}: {nuovo_colore.value} (ID: {nuovo_id})")
        
        # Step 1: Attiva nuovo
        self.attiva_workflow(nuovo_id, True)
        print(f"  ✓ {nuovo_colore.value} attivato")
        
        # Step 2: Verifica
        if verify_fn:
            print(f"  Verifica (timeout: {verify_timeout_s}s)...")
            start = time.monotonic()
            
            try:
                ok = verify_fn(nuovo_id)
                if not ok:
                    raise RuntimeError("Verifica fallita")
                print("  ✓ Verifica passata")
            except Exception as e:
                print(f"  ✗ Verifica fallita: {e} — ROLLBACK")
                self.attiva_workflow(nuovo_id, False)
                self.attiva_workflow(vecchio_id, True)
                print(f"  ✓ Rollback completato — {vecchio_id} ripristinato")
                return False
        
        # Step 3: Disattiva vecchio
        self.attiva_workflow(vecchio_id, False)
        print(f"  ✓ Vecchio ({vecchio_id}) disattivato")
        print(f"✓ Deploy completato: {nome_base} ora su {nuovo_colore.value}")
        return True

    def rollback(self, nome_base: str) -> None:
        """Rollback immediato: attiva BLUE, disattiva GREEN."""
        blue_id, green_id = self.trova_coppia(nome_base)
        if blue_id:
            self.attiva_workflow(blue_id, True)
        if green_id:
            self.attiva_workflow(green_id, False)
        print(f"Rollback completato: {nome_base} → BLUE")
```

### B2 — CI/CD Pipeline GitHub Actions

```yaml
# file: ci/.github/workflows/deploy-workflows.yml
name: Deploy Workflow n8n

on:
  push:
    branches: [main]
    paths: ['workflows/**']
  pull_request:
    paths: ['workflows/**']

jobs:
  validate:
    name: Valida workflow
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      
      - name: Valida tutti i workflow
        run: python scripts/validate_workflow.py ./workflows
      
      - name: Check formato JSON
        run: |
          for f in $(find workflows -name "*.json"); do
            python3 -c "import json; json.load(open('$f'))" \
              && echo "  OK: $f" \
              || (echo "  FAIL: $f"; exit 1)
          done

  deploy-staging:
    name: Deploy su Staging
    runs-on: ubuntu-latest
    needs: validate
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    environment: staging
    steps:
      - uses: actions/checkout@v4
      
      - name: Deploy workflow su n8n staging
        env:
          N8N_URL: ${{ secrets.N8N_STAGING_URL }}
          N8N_API_KEY: ${{ secrets.N8N_STAGING_API_KEY }}
        run: |
          for wf_dir in workflows/*/; do
            echo "Deploy: $wf_dir"
            bash scripts/import_workflow.sh \
              "${wf_dir}workflow.json" \
              "environments/staging.env.json"
          done
      
      - name: Smoke test staging
        run: python scripts/smoke_test.py --env staging

  deploy-prod:
    name: Deploy su Produzione
    runs-on: ubuntu-latest
    needs: deploy-staging
    environment: production  # Richiede approvazione manuale in GitHub
    steps:
      - uses: actions/checkout@v4
      
      - name: Deploy con blue-green
        env:
          N8N_URL: ${{ secrets.N8N_PROD_URL }}
          N8N_API_KEY: ${{ secrets.N8N_PROD_API_KEY }}
        run: python scripts/blue_green_deploy.py --workflow ordini-processing
```

---

## PART C — Diff e Change Management

### C1 — Diff Visuale tra Versioni

```python
#!/usr/bin/env python3
# file: scripts/diff_workflow.py
"""
Confronto visuale tra due versioni di un workflow n8n.
Usa git diff internamente per mostrare cambiamenti significativi.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def normalizza_workflow(wf: dict) -> dict:
    """Normalizza workflow per confronto (rimuove campi non rilevanti)."""
    wf_copy = json.loads(json.dumps(wf))
    wf_copy.pop("updatedAt", None)
    wf_copy.pop("createdAt", None)
    wf_copy.pop("id", None)
    
    # Normalizza nodi: ordina per nome per confronto stabile
    if "nodes" in wf_copy:
        wf_copy["nodes"] = sorted(
            wf_copy["nodes"],
            key=lambda n: n.get("name", "")
        )
    
    return wf_copy


def estrai_summary_modifiche(wf_old: dict, wf_new: dict) -> list[str]:
    """Estrae summary leggibile delle modifiche."""
    modifiche = []
    
    # Nodi aggiunti/rimossi
    nodi_old = {n["name"] for n in wf_old.get("nodes", [])}
    nodi_new = {n["name"] for n in wf_new.get("nodes", [])}
    
    aggiunti = nodi_new - nodi_old
    rimossi = nodi_old - nodi_new
    
    for n in aggiunti:
        modifiche.append(f"  + Nodo AGGIUNTO: '{n}'")
    for n in rimossi:
        modifiche.append(f"  - Nodo RIMOSSO: '{n}'")
    
    # Nodi modificati
    nodi_old_map = {n["name"]: n for n in wf_old.get("nodes", [])}
    nodi_new_map = {n["name"]: n for n in wf_new.get("nodes", [])}
    
    for nome in nodi_old & nodi_new:
        old_n = json.dumps(nodi_old_map[nome], sort_keys=True)
        new_n = json.dumps(nodi_new_map[nome], sort_keys=True)
        if old_n != new_n:
            modifiche.append(f"  ~ Nodo MODIFICATO: '{nome}'")
    
    # Connessioni cambiate
    conn_old = json.dumps(wf_old.get("connections", {}), sort_keys=True)
    conn_new = json.dumps(wf_new.get("connections", {}), sort_keys=True)
    if conn_old != conn_new:
        modifiche.append("  ~ CONNESSIONI modificate")
    
    # Nome workflow
    if wf_old.get("name") != wf_new.get("name"):
        modifiche.append(f"  ~ Nome: '{wf_old.get('name')}' → '{wf_new.get('name')}'")
    
    return modifiche or ["  (nessuna modifica rilevante)"]


def confronta_file(file_old: Path, file_new: Path) -> None:
    """Mostra diff tra due file workflow.json."""
    with open(file_old) as f:
        wf_old = json.load(f)
    with open(file_new) as f:
        wf_new = json.load(f)
    
    print(f"\n{'=' * 60}")
    print(f"DIFF WORKFLOW")
    print(f"  OLD: {file_old}")
    print(f"  NEW: {file_new}")
    print(f"{'=' * 60}")
    
    modifiche = estrai_summary_modifiche(wf_old, wf_new)
    print("\nModifiche:")
    for m in modifiche:
        print(m)
    
    # Diff raw JSON normalizzato
    old_norm = json.dumps(normalizza_workflow(wf_old), indent=2, sort_keys=True)
    new_norm = json.dumps(normalizza_workflow(wf_new), indent=2, sort_keys=True)
    
    if old_norm == new_norm:
        print("\n✓ Nessuna differenza significativa trovata")
    else:
        print("\nDiff dettagliato:")
        # Usa git diff per colorare l'output
        import tempfile, os
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f_old:
            f_old.write(old_norm)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f_new:
            f_new.write(new_norm)
        
        try:
            result = subprocess.run(
                ["git", "diff", "--no-index", f_old.name, f_new.name],
                capture_output=True, text=True
            )
            print(result.stdout[:5000])  # Limita output
        finally:
            os.unlink(f_old.name)
            os.unlink(f_new.name)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Uso: {sys.argv[0]} <workflow_old.json> <workflow_new.json>")
        sys.exit(1)
    
    confronta_file(Path(sys.argv[1]), Path(sys.argv[2]))
```

---

## Esercizi

### Esercizio 1 — Versiona il tuo Workflow (20 min)

```bash
# 1. Esporta un workflow da n8n
export N8N_API_KEY="tuachiave"
bash scripts/export_workflow.sh ./workflows

# 2. Aggiungi a Git con commit semantico
git add workflows/
git commit -m "feat(ordini): aggiunge validazione CF per ordini B2B"

# 3. Modifica il workflow in n8n
# 4. Riesporta e verifica il diff
bash scripts/export_workflow.sh ./workflows
git diff workflows/
```

### Esercizio 2 — Rollback Manuale (15 min)

```bash
# Simula un deploy sbagliato
git log --oneline -5

# Torna alla versione precedente
git show HEAD~1:workflows/ordini-processing/workflow.json > /tmp/rollback.json

# Importa la versione rollback
bash scripts/import_workflow.sh /tmp/rollback.json

# Verifica che il workflow sia tornato alla versione precedente
```

### Esercizio 3 — Pre-commit Hook (20 min)

```bash
# Crea pre-commit hook che valida i workflow prima del commit
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
echo "Validazione workflow..."
python scripts/validate_workflow.py ./workflows
if [ $? -ne 0 ]; then
    echo "✗ Workflow non validi — commit bloccato"
    exit 1
fi
echo "✓ Tutti i workflow validi"
EOF
chmod +x .git/hooks/pre-commit
```

---

## Riferimenti

- n8n API Reference: https://docs.n8n.io/api/
- GitHub Actions: https://docs.github.com/actions
- Blue-Green Deployment (Fowler): https://martinfowler.com/bliki/BlueGreenDeployment.html
- Modulo sorgente: `18-workflow-versioning-rollback.md`
