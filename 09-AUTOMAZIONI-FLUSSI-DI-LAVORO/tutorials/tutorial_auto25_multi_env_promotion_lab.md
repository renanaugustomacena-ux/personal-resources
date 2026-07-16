# Tutorial Lab — Multi-Environment Promotion e Secret Management

> **Campo di studio:** 09-AUTOMAZIONI-FLUSSI-DI-LAVORO
> **Modulo sorgente:** `25-multi-environment-promotion.md`
> **Livello:** intermediate → advanced
> **Tempo stimato:** 2-3 ore
> **Prerequisiti:** Docker, Git, n8n base, CI/CD concetti
> **Versioni di riferimento:** n8n 1.x · Docker Compose · Python 3.11+

---

## Obiettivi del Lab

Al termine di questo tutorial saprai:

1. Strutturare pipeline dev → staging → prod per workflow n8n
2. Gestire segreti differenziati per ambiente senza hard-code
3. Implementare smoke test automatici post-deployment
4. Gestire variabili d'ambiente con override per livello
5. Costruire gate di promozione manuale con approvazione
6. Diagnosticare differenze di comportamento tra ambienti

---

## Lab Environment Setup

```bash
python3 --version    # 3.11+
docker compose version

# Crea 3 ambienti n8n locali su porte diverse
mkdir -p multi-env-lab/{dev,staging,prod,scripts,configs,tests}
cd multi-env-lab
```

---

## Analogia Introduttiva

> **La promozione multi-environment è come testare una ricetta**:
> prima la cucini a casa per te (DEV) — puoi sbagliare senza conseguenze,
> poi la presenti a una cena con amici fidati (STAGING) — feedback reale,
> infine la servi al ristorante pagante (PROD) — zero errori tollerati.
>
> Il **secret management** è come la cassaforte degli ingredienti segreti:
> le chiavi della cassaforte DEV le dai a tutti gli sviluppatori,
> quelle STAGING solo al team QA,
> quelle PROD solo all'automazione CI/CD con log di audit.
>
> Un workflow che "funziona sul mio computer ma non in produzione"
> è quasi sempre un problema di variabili d'ambiente differenti
> o segreti configurati male — non di codice.

---

## Architettura Multi-Environment

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PIPELINE DI PROMOZIONE                                 │
│                                                                           │
│  Git push → CI
│  │                                                                        │
│  ▼                                                                        │
│  ┌─────────────────┐                                                      │
│  │    DEV          │ ← Auto-deploy ogni push                              │
│  │  n8n :5678      │ ← Dati: fixture/test                                │
│  │  DB locale      │ ← Segreti: .env.dev (poco sicuro OK)                │
│  └────────┬────────┘                                                      │
│           │ ✓ test automatici passano                                     │
│           │ gate: automatico                                              │
│           ▼                                                               │
│  ┌─────────────────┐                                                      │
│  │   STAGING       │ ← Deploy su approvazione PR merge                   │
│  │  n8n :5679      │ ← Dati: produzione-like                             │
│  │  DB staging     │ ← Segreti: CI secrets (scoped staging)              │
│  └────────┬────────┘                                                      │
│           │ ✓ QA approval + smoke test                                   │
│           │ gate: MANUALE (QA lead approva)                              │
│           ▼                                                               │
│  ┌─────────────────┐                                                      │
│  │    PROD         │ ← Deploy dopo approvazione esplicita                 │
│  │  n8n :5680      │ ← Dati: reali                                        │
│  │  DB prod        │ ← Segreti: Vault/SecretManager (massima sicurezza)  │
│  └─────────────────┘                                                      │
│                                                                           │
│  VARIABILI PER AMBIENTE:                                                  │
│  comune.env    → condivise tra tutti                                     │
│  dev.env       → override DEV                                            │
│  staging.env   → override STAGING                                        │
│  prod.env      → override PROD (solo CI, mai locale!)                   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## PART A — Configurazione Multi-Ambiente

### A1 — Docker Compose per 3 Ambienti Locali

```yaml
# file: docker-compose-multi.yml
# Avvia tutti e 3 gli ambienti n8n in locale per test
# SOLO per sviluppo locale — in produzione ogni ambiente è un host separato

version: "3.9"

x-n8n-base: &n8n-base
  image: n8nio/n8n:1.0.0
  restart: unless-stopped
  depends_on:
    - postgres

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_PASSWORD: ${DB_ROOT_PASS:-localonly}
      POSTGRES_MULTIPLE_DATABASES: n8n_dev,n8n_staging,n8n_prod
    volumes:
      - pg_data:/var/lib/postgresql/data
      - ./scripts/init-multiple-db.sh:/docker-entrypoint-initdb.d/init.sh
    networks: [multi-env]

  n8n-dev:
    <<: *n8n-base
    ports: ["5678:5678"]
    environment:
      DB_TYPE: postgresdb
      DB_POSTGRESDB_HOST: postgres
      DB_POSTGRESDB_DATABASE: n8n_dev
      DB_POSTGRESDB_USER: n8n_dev
      DB_POSTGRESDB_PASSWORD: ${N8N_DEV_DB_PASS:-devonly}
      N8N_ENCRYPTION_KEY: ${N8N_DEV_ENC_KEY:-devkey-not-for-prod}
      N8N_ENVIRONMENT: development
      WEBHOOK_URL: http://localhost:5678
      # No auth in dev (solo locale!)
      N8N_BASIC_AUTH_ACTIVE: "false"
      N8N_USER_MANAGEMENT_DISABLED: "true"
    env_file: [configs/common.env, configs/dev.env]
    networks: [multi-env]

  n8n-staging:
    <<: *n8n-base
    ports: ["5679:5678"]
    environment:
      DB_TYPE: postgresdb
      DB_POSTGRESDB_HOST: postgres
      DB_POSTGRESDB_DATABASE: n8n_staging
      DB_POSTGRESDB_USER: n8n_staging
      DB_POSTGRESDB_PASSWORD: ${N8N_STAGING_DB_PASS:?}
      N8N_ENCRYPTION_KEY: ${N8N_STAGING_ENC_KEY:?}
      N8N_ENVIRONMENT: staging
      WEBHOOK_URL: http://localhost:5679
    env_file: [configs/common.env, configs/staging.env]
    networks: [multi-env]

  n8n-prod:
    <<: *n8n-base
    ports: ["5680:5678"]
    environment:
      DB_TYPE: postgresdb
      DB_POSTGRESDB_HOST: postgres
      DB_POSTGRESDB_DATABASE: n8n_prod
      DB_POSTGRESDB_USER: n8n_prod
      DB_POSTGRESDB_PASSWORD: ${N8N_PROD_DB_PASS:?}
      N8N_ENCRYPTION_KEY: ${N8N_PROD_ENC_KEY:?}
      N8N_ENVIRONMENT: production
      WEBHOOK_URL: https://n8n.azienda.it
      N8N_BASIC_AUTH_ACTIVE: "true"
      N8N_BASIC_AUTH_USER: ${N8N_PROD_AUTH_USER:?}
      N8N_BASIC_AUTH_PASSWORD: ${N8N_PROD_AUTH_PASS:?}
    env_file: [configs/common.env, configs/prod.env]
    networks: [multi-env]

networks:
  multi-env:
    driver: bridge

volumes:
  pg_data:
```

### A2 — Gestione Variabili per Ambiente

```bash
# file: configs/common.env
# Variabili COMUNI a tutti gli ambienti
# NESSUN segreto qui — solo configurazione non sensibile

N8N_LOG_LEVEL=info
N8N_LOG_OUTPUT=console
N8N_METRICS=true
N8N_METRICS_PORT=9091
EXECUTIONS_DATA_PRUNE=true
EXECUTIONS_DATA_MAX_AGE=168      # 7 giorni
GENERIC_TIMEZONE=Europe/Rome
```

```bash
# file: configs/dev.env
# Override DEV — config meno restrittiva per sviluppo

N8N_LOG_LEVEL=debug
N8N_USER_MANAGEMENT_JWT_SECRET=dev-secret-not-for-prod
N8N_EMAIL_MODE=smtp
N8N_SMTP_HOST=mailhog           # Server email locale per test
N8N_SMTP_PORT=1025
EXECUTIONS_DATA_MAX_AGE=24       # Meno retention in dev
```

```bash
# file: configs/staging.env
# Override STAGING — simile a prod ma con endpoint test

N8N_EMAIL_MODE=smtp
N8N_SMTP_HOST=${SMTP_HOST_STAGING:?}
N8N_SMTP_PORT=587
N8N_SMTP_SSL=true
```

```
# file: configs/prod.env (mai committare questo file!)
# Contenuto gestito da secret manager (Vault/AWS SSM/GitHub Secrets)
# Il CI scarica questo file a runtime, lo usa, poi lo elimina

N8N_EMAIL_MODE=smtp
N8N_SMTP_HOST=${SMTP_HOST_PROD:?}
N8N_SMTP_USER=${SMTP_USER_PROD:?}
N8N_SMTP_PASS=${SMTP_PASS_PROD:?}
```

---

## PART B — Script di Promozione

### B1 — Promotion Pipeline Python

```python
#!/usr/bin/env python3
# file: scripts/promote.py
"""
Script di promozione workflow tra ambienti.
Esegue: validazione → deploy → smoke test → conferma o rollback.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from enum import Enum
from typing import Optional
import httpx


class Ambiente(str, Enum):
    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"


AMBIENTE_CONFIG = {
    Ambiente.DEV: {
        "url": os.environ.get("N8N_DEV_URL", "http://localhost:5678"),
        "api_key": os.environ.get("N8N_DEV_API_KEY", ""),
        "richiede_approvazione": False,
    },
    Ambiente.STAGING: {
        "url": os.environ.get("N8N_STAGING_URL", "http://localhost:5679"),
        "api_key": os.environ.get("N8N_STAGING_API_KEY", ""),
        "richiede_approvazione": False,
    },
    Ambiente.PROD: {
        "url": os.environ.get("N8N_PROD_URL", "http://localhost:5680"),
        "api_key": os.environ.get("N8N_PROD_API_KEY", ""),
        "richiede_approvazione": True,
    },
}


def leggi_workflow(path: str) -> dict:
    """Legge workflow JSON da file."""
    with open(path) as f:
        return json.load(f)


def deploy_workflow(
    wf_json: dict,
    target_url: str,
    api_key: str,
    env_vars: dict[str, str],
) -> str:
    """
    Deploya workflow in n8n via API.
    Sostituisce placeholder %%VAR%% con variabili ambiente specifiche.
    Ritorna workflow_id deployato.
    """
    # Sostituisci variabili
    wf_str = json.dumps(wf_json)
    for k, v in env_vars.items():
        wf_str = wf_str.replace(f"%%{k}%%", v)
    
    wf_final = json.loads(wf_str)
    
    headers = {"X-N8N-API-KEY": api_key, "Content-Type": "application/json"}
    
    with httpx.Client(timeout=30) as client:
        # Controlla se esiste già
        resp = client.get(f"{target_url}/api/v1/workflows", headers=headers)
        resp.raise_for_status()
        workflows = resp.json()["data"]
        
        esistente = next((w for w in workflows if w["name"] == wf_final.get("name")), None)
        
        if esistente:
            # Aggiorna
            resp = client.put(
                f"{target_url}/api/v1/workflows/{esistente['id']}",
                headers=headers,
                json=wf_final,
            )
        else:
            # Crea nuovo
            resp = client.post(
                f"{target_url}/api/v1/workflows",
                headers=headers,
                json=wf_final,
            )
        
        resp.raise_for_status()
        return resp.json()["id"]


def leggi_env_vars(ambiente: Ambiente) -> dict[str, str]:
    """Legge variabili d'ambiente specifiche per l'ambiente."""
    env_file = f"configs/{ambiente.value}.env"
    vars_: dict[str, str] = {}
    
    try:
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    # Risolvi variabili d'ambiente (${VAR:?})
                    if value.startswith("${") and value.endswith("}"):
                        var_name = value[2:-1].rstrip(":?")
                        value = os.environ.get(var_name, "")
                    vars_[key.strip()] = value.strip()
    except FileNotFoundError:
        pass
    
    return vars_


def smoke_test(ambiente: Ambiente) -> list[str]:
    """
    Smoke test post-deployment.
    Ritorna lista di errori (vuota = tutto ok).
    """
    config = AMBIENTE_CONFIG[ambiente]
    url = config["url"]
    api_key = config["api_key"]
    headers = {"X-N8N-API-KEY": api_key}
    errori = []
    
    with httpx.Client(timeout=10) as client:
        # Test 1: Health check n8n
        try:
            r = client.get(f"{url}/healthz")
            if r.status_code != 200:
                errori.append(f"Health check fallito: {r.status_code}")
        except httpx.ConnectError:
            errori.append(f"n8n non raggiungibile: {url}")
            return errori  # Non continuare se non raggiungibile
        
        # Test 2: API accessibile
        try:
            r = client.get(f"{url}/api/v1/workflows", headers=headers)
            if r.status_code == 401:
                errori.append("API Key non valida")
            elif r.status_code != 200:
                errori.append(f"API non accessibile: {r.status_code}")
        except Exception as e:
            errori.append(f"Errore API: {e}")
        
        # Test 3: Webhook attivi
        try:
            r = client.get(f"{url}/api/v1/workflows", headers=headers)
            if r.status_code == 200:
                workflows = r.json()["data"]
                webhook_workflows = [
                    w for w in workflows
                    if any(n.get("type", "").startswith("n8n-nodes-base.webhook")
                           for n in w.get("nodes", []))
                ]
                attivi = [w for w in webhook_workflows if w.get("active")]
                if len(attivi) < len(webhook_workflows):
                    errori.append(
                        f"{len(webhook_workflows) - len(attivi)} workflow con webhook non attivi"
                    )
        except Exception:
            pass
    
    return errori


def promuovi(
    workflow_path: str,
    da: Ambiente,
    a: Ambiente,
    forza: bool = False,
) -> bool:
    """
    Promuovi un workflow da un ambiente a un altro.
    Ritorna True se promozione completata con successo.
    """
    print(f"\n{'='*60}")
    print(f"PROMOZIONE: {da.value} → {a.value}")
    print(f"Workflow: {workflow_path}")
    print(f"{'='*60}")
    
    target_config = AMBIENTE_CONFIG[a]
    
    # Richiede approvazione esplicita per prod
    if target_config["richiede_approvazione"] and not forza:
        print(f"\n⚠ PROMOZIONE A {a.value.upper()} richiede approvazione manuale")
        risposta = input("Confermi il deploy in produzione? [sì/no]: ").strip().lower()
        if risposta not in ("sì", "si", "s", "yes", "y"):
            print("  Promozione annullata dall'utente")
            return False
    
    # Leggi e valida workflow
    print("\n1. Lettura workflow...")
    try:
        wf = leggi_workflow(workflow_path)
        print(f"  ✓ '{wf.get('name', 'N/D')}'")
    except Exception as e:
        print(f"  ✗ Errore lettura: {e}")
        return False
    
    # Carica variabili ambiente target
    env_vars = leggi_env_vars(a)
    
    # Deploy
    print(f"\n2. Deploy su {a.value}...")
    try:
        wf_id = deploy_workflow(
            wf,
            target_config["url"],
            target_config["api_key"],
            env_vars,
        )
        print(f"  ✓ Deployato (ID: {wf_id})")
    except Exception as e:
        print(f"  ✗ Deploy fallito: {e}")
        return False
    
    # Smoke test
    print(f"\n3. Smoke test su {a.value}...")
    time.sleep(2)  # Attendi stabilizzazione
    
    errori = smoke_test(a)
    
    if errori:
        print(f"  ✗ Smoke test FALLITO:")
        for err in errori:
            print(f"     - {err}")
        print("\n  ROLLBACK: non implementato in questa demo")
        return False
    else:
        print(f"  ✓ Tutti i test passati")
    
    print(f"\n✓ PROMOZIONE COMPLETATA: {workflow_path} è ora su {a.value}")
    return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Promuovi workflow tra ambienti")
    parser.add_argument("workflow", help="Path al file workflow.json")
    parser.add_argument("--da", default="staging", choices=[e.value for e in Ambiente])
    parser.add_argument("--a", default="prod", choices=[e.value for e in Ambiente], dest="a_env")
    parser.add_argument("--forza", action="store_true", help="Salta richiesta approvazione")
    
    args = parser.parse_args()
    
    successo = promuovi(
        args.workflow,
        Ambiente(args.da),
        Ambiente(args.a_env),
        forza=args.forza,
    )
    sys.exit(0 if successo else 1)
```

---

## PART C — Secret Management

### C1 — Gerarchia di Sicurezza per Segreti

```python
#!/usr/bin/env python3
# file: scripts/secret_manager.py
"""
Astrazione per recupero segreti da diversi provider.
Stessa interfaccia per: variabili env, .env file, HashiCorp Vault, AWS SSM.
"""
from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Optional


class SecretsProvider(ABC):
    """Interfaccia comune per recupero segreti."""

    @abstractmethod
    def get(self, chiave: str) -> Optional[str]:
        """Recupera un segreto per chiave. None se non trovato."""

    def get_required(self, chiave: str) -> str:
        """Come get(), ma solleva se non trovato."""
        valore = self.get(chiave)
        if valore is None:
            raise KeyError(f"Segreto obbligatorio non trovato: '{chiave}'")
        return valore


class EnvSecretsProvider(SecretsProvider):
    """Segreti da variabili d'ambiente (dev/CI)."""

    def get(self, chiave: str) -> Optional[str]:
        return os.environ.get(chiave)


class EnvFileSecretsProvider(SecretsProvider):
    """Segreti da file .env (dev locale)."""

    def __init__(self, file_path: str):
        self._secrets: dict[str, str] = {}
        try:
            with open(file_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, _, value = line.partition("=")
                        self._secrets[key.strip()] = value.strip().strip('"').strip("'")
        except FileNotFoundError:
            pass

    def get(self, chiave: str) -> Optional[str]:
        return self._secrets.get(chiave)


class ChainSecretsProvider(SecretsProvider):
    """
    Provider a catena: cerca in ordine finché trova.
    Uso tipico: env vars → .env file → default
    """

    def __init__(self, *providers: SecretsProvider):
        self._providers = providers

    def get(self, chiave: str) -> Optional[str]:
        for provider in self._providers:
            valore = provider.get(chiave)
            if valore is not None:
                return valore
        return None


class MockSecretsProvider(SecretsProvider):
    """Provider mock per test — non usare in produzione."""

    def __init__(self, segreti: dict[str, str]):
        self._segreti = segreti

    def get(self, chiave: str) -> Optional[str]:
        return self._segreti.get(chiave)


def crea_provider(ambiente: str) -> SecretsProvider:
    """
    Factory: crea il provider appropriato per ambiente.
    
    dev:     .env.dev + env vars
    staging: env vars (CI)
    prod:    env vars (CI con segreti sicuri)
    """
    if ambiente == "dev":
        return ChainSecretsProvider(
            EnvSecretsProvider(),
            EnvFileSecretsProvider(f"configs/.env.{ambiente}.secrets"),
        )
    elif ambiente in ("staging", "prod"):
        # In CI: segreti iniettati come env vars dal CI/CD platform
        return EnvSecretsProvider()
    else:
        raise ValueError(f"Ambiente sconosciuto: {ambiente}")


# ─── Demo ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== SECRET MANAGER DEMO ===\n")
    
    # Simula provider chain
    provider = ChainSecretsProvider(
        MockSecretsProvider({"API_KEY": "test-key-123"}),
        EnvSecretsProvider(),
    )
    
    print(f"API_KEY: {provider.get('API_KEY')}")
    print(f"DB_PASS: {provider.get('DB_PASS')} (non trovato → None)")
    
    try:
        provider.get_required("MISSING_SECRET")
    except KeyError as e:
        print(f"get_required fallisce correttamente: {e}")
    
    print("\nIn produzione:")
    print("  DEV:     ChainProvider(env vars, .env.dev.secrets)")
    print("  STAGING: EnvProvider (CI injector)")
    print("  PROD:    EnvProvider (CI con Vault/AWS SSM integration)")
```

---

## PART D — Test di Promozione

### D1 — Checklist Pre-Promozione

```python
#!/usr/bin/env python3
# file: tests/pre_promotion_checklist.py
"""
Checklist automatica prima di promuovere a produzione.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Callable


@dataclass_check := []

def check(nome: str):
    """Decoratore per registrare check."""
    def decorator(fn: Callable):
        dataclass_check.append((nome, fn))
        return fn
    return decorator


# Tutti i check da eseguire prima di promuovere
CHECKS = []


def aggiungi_check(nome: str, fn: Callable) -> None:
    CHECKS.append((nome, fn))


def check_nessun_placeholder(wf_path: Path) -> tuple[bool, str]:
    """Nessun placeholder %%VAR%% rimasto nel workflow."""
    contenuto = wf_path.read_text()
    rimasti = re.findall(r"%%\w+%%", contenuto)
    if rimasti:
        return False, f"Placeholder non sostituiti: {rimasti}"
    return True, "OK"


def check_nessun_segreto_hardcoded(wf_path: Path) -> tuple[bool, str]:
    """Nessun segreto hard-coded nel JSON."""
    contenuto = wf_path.read_text()
    pattern = [
        r"(?i)password['\"\s]*[:=]['\"\s]*\w{4,}",
        r"Bearer\s+[a-zA-Z0-9\-_\.]{30,}",
        r"(?i)api[-_]?key['\"\s]*[:=]['\"\s]*\w{8,}",
    ]
    for p in pattern:
        if re.search(p, contenuto):
            return False, f"Pattern segreto trovato: {p[:40]}"
    return True, "OK"


def check_json_valido(wf_path: Path) -> tuple[bool, str]:
    """JSON deve essere valido."""
    try:
        json.loads(wf_path.read_text())
        return True, "OK"
    except json.JSONDecodeError as e:
        return False, f"JSON non valido: {e}"


def check_nome_workflow_non_test(wf_path: Path) -> tuple[bool, str]:
    """Nome workflow non contiene 'test', 'dev', 'tmp'."""
    wf = json.loads(wf_path.read_text())
    nome = wf.get("name", "").lower()
    parole_vietate = {"test", "dev", "tmp", "debug", "wip", "draft"}
    trovate = [p for p in parole_vietate if p in nome]
    if trovate:
        return False, f"Nome workflow contiene parole non-prod: {trovate}"
    return True, "OK"


def esegui_checklist(wf_path: Path) -> bool:
    """Esegui tutti i check e stampa risultato."""
    checks = [
        ("JSON valido", check_json_valido),
        ("Nessun placeholder", check_nessun_placeholder),
        ("Nessun segreto hardcoded", check_nessun_segreto_hardcoded),
        ("Nome workflow non-test", check_nome_workflow_non_test),
    ]
    
    print(f"\nChecklist pre-promozione: {wf_path.name}")
    print("-" * 50)
    
    tutti_ok = True
    for nome, fn in checks:
        try:
            ok, messaggio = fn(wf_path)
        except Exception as e:
            ok, messaggio = False, f"Eccezione: {e}"
        
        simbolo = "✓" if ok else "✗"
        print(f"  {simbolo} {nome}: {messaggio}")
        if not ok:
            tutti_ok = False
    
    print("-" * 50)
    if tutti_ok:
        print("  → Workflow pronto per promozione")
    else:
        print("  → BLOCCO: risolvi i problemi prima di promuovere")
    
    return tutti_ok


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Uso: {sys.argv[0]} <workflow.json>")
        sys.exit(1)
    
    wf_path = Path(sys.argv[1])
    ok = esegui_checklist(wf_path)
    sys.exit(0 if ok else 1)
```

---

## Esercizi

### Esercizio 1 — Pipeline Locale Completa (30 min)

```bash
# 1. Avvia i 3 ambienti
docker compose -f docker-compose-multi.yml up -d

# 2. Esporta un workflow da DEV
N8N_API_KEY=devkey bash scripts/export_workflow.sh --url http://localhost:5678 ./workflows/

# 3. Esegui checklist pre-promozione
python tests/pre_promotion_checklist.py ./workflows/ordini-processing/workflow.json

# 4. Promuovi su staging
python scripts/promote.py ./workflows/ordini-processing/workflow.json --da dev --a staging

# 5. Verifica smoke test
python scripts/promote.py ./workflows/ordini-processing/workflow.json --da staging --a prod
```

### Esercizio 2 — Secret Rotation (20 min)

Implementa un script `rotate_secrets.sh` che:
1. Genera una nuova `N8N_ENCRYPTION_KEY`
2. Fa un backup del DB prima della rotazione
3. Aggiorna la chiave nell'environment
4. Riavvia n8n e verifica health

### Esercizio 3 — Environment Diff (15 min)

Script che confronta configurazioni tra ambienti:
```python
def confronta_ambienti(env1: str, env2: str) -> dict:
    """
    Confronta le config di due ambienti.
    Mostra: variabili diverse, mancanti in uno dei due.
    """
    pass
```

---

## Riferimenti

- n8n Environment Variables: https://docs.n8n.io/hosting/configuration/
- HashiCorp Vault: https://developer.hashicorp.com/vault
- GitHub Environments: https://docs.github.com/actions/deployment/targeting-different-environments
- Modulo sorgente: `25-multi-environment-promotion.md`
