# Tutorial Lab — Progetti Pratici: Capstone Multi-Platform Onboarding PMI

> **Campo di studio:** 09-AUTOMAZIONI-FLUSSI-DI-LAVORO
> **Modulo sorgente:** `08-progetti-pratici-automazione.md`
> **Livello:** advanced
> **Tempo stimato:** 4 ore
> **Prerequisiti:** Tutti i tutorial precedenti, Docker Compose, Python 3.11+, n8n base
> **Versioni di riferimento:** n8n 1.x, Python 3.11+, Docker Compose 3.8

---

## Obiettivi del Lab

Al termine di questo tutorial saprai:

1. Progettare un sistema di automazione end-to-end per una PMI reale
2. Integrare più piattaforme: n8n + webhook + Python + notifiche
3. Gestire onboarding clienti con workflow multi-step e gate di approvazione
4. Costruire un sistema di notifiche multi-canale (email + Slack + webhook)
5. Implementare monitoring e recovery automatico del sistema
6. Documentare e passare in produzione un progetto di automazione completo

---

## Lab Environment Setup

```yaml
# docker-compose.yml — infrastruttura completa del progetto capstone
version: "3.8"

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: n8n
      POSTGRES_USER: n8n
      POSTGRES_PASSWORD: n8n_secret
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U n8n"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

  n8n:
    image: n8nio/n8n:latest
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      DB_TYPE: postgresdb
      DB_POSTGRESDB_HOST: postgres
      DB_POSTGRESDB_DATABASE: n8n
      DB_POSTGRESDB_USER: n8n
      DB_POSTGRESDB_PASSWORD: n8n_secret
      N8N_ENCRYPTION_KEY: "${N8N_ENCRYPTION_KEY}"
      WEBHOOK_URL: "http://localhost:5678"
      EXECUTIONS_MODE: regular
    ports:
      - "5678:5678"
    volumes:
      - n8n_data:/home/node/.n8n

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    depends_on:
      - postgres
      - redis
    environment:
      DATABASE_URL: "postgresql://n8n:n8n_secret@postgres/n8n"
      REDIS_URL: "redis://redis:6379"
      N8N_WEBHOOK_SECRET: "${N8N_WEBHOOK_SECRET}"
    ports:
      - "8000:8000"

volumes:
  postgres_data:
  redis_data:
  n8n_data:
```

```bash
# Avvio e verifica
echo "N8N_ENCRYPTION_KEY=$(openssl rand -hex 32)" > .env
echo "N8N_WEBHOOK_SECRET=$(openssl rand -hex 16)" >> .env

docker compose up -d
docker compose ps  # tutti healthy?
curl http://localhost:5678/healthz  # n8n OK
curl http://localhost:8000/health   # backend OK
```

---

## Analogia Introduttiva

> **Il capstone è come costruire il sistema nervoso di una PMI**:
> il cervello (n8n) riceve segnali (webhook) e coordina le risposte,
> le braccia (Python backend) eseguono le azioni pesanti,
> le orecchie (trigger) ascoltano eventi da email, form e API esterne.
>
> Quando un nuovo cliente firma il contratto:
> il sistema sa autonomamente creare la cartella drive,
> avvisare il team commerciale su Slack,
> schedulare la chiamata di onboarding in calendario,
> e aprire il ticket di setup in Jira — tutto senza intervento umano.
>
> La differenza da "una serie di script" a "un sistema di automazione"
> è la **coesione**: ogni componente conosce il suo ruolo,
> le failure sono gestite, e lo stato è sempre osservabile.

---

## Architettura del Progetto

```
┌─────────────────────────────────────────────────────────────────────┐
│              ONBOARDING PMI — ARCHITETTURA SISTEMA                   │
│                                                                       │
│  CANALI INGRESSO:                                                    │
│  [Form Typeform] ──────────────────────────────────┐                │
│  [Email Outlook] ──────────────────────────────────┤                │
│  [Contratto DocuSign] ─────────────────────────────┤                │
│                                                     ▼                │
│                                          ┌─────────────────┐        │
│                                          │  n8n Webhook    │        │
│                                          │  Gateway        │        │
│                                          └────────┬────────┘        │
│                                                   │                  │
│                    ┌──────────────────────────────┤                  │
│                    │                              │                  │
│                    ▼                              ▼                  │
│         ┌──────────────────┐          ┌─────────────────────┐      │
│         │  Python Backend  │          │  n8n Workflow Engine │      │
│         │  • Validazione   │◄────────►│  • Orchestrazione   │      │
│         │  • DB operations │          │  • Scheduling       │      │
│         │  • PDF/Email     │          │  • Notifiche        │      │
│         └──────────────────┘          └─────────────────────┘      │
│                    │                              │                  │
│                    ▼                              ▼                  │
│         ┌──────────────────────────────────────────────────────┐    │
│         │              DESTINAZIONI OUTPUT                      │    │
│         │  Gmail │ Slack │ Google Drive │ CRM │ Calendario      │   │
│         └──────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## PART A — Backend Python

### A1 — API Backend del Sistema

```python
# backend/main.py
from __future__ import annotations

import hashlib
import hmac
import json
import os
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

from fastapi import FastAPI, Request, HTTPException, Header, Depends
from fastapi.responses import JSONResponse
import asyncpg
import redis.asyncio as aioredis
import structlog

log = structlog.get_logger()
app = FastAPI(title="Onboarding PMI Backend", version="1.0.0")

N8N_WEBHOOK_SECRET = os.environ["N8N_WEBHOOK_SECRET"]
DATABASE_URL = os.environ["DATABASE_URL"]
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")

class StatoCliente(Enum):
    LEAD = "lead"
    CONTRATTO_FIRMATO = "contratto_firmato"
    ONBOARDING_IN_CORSO = "onboarding_in_corso"
    ATTIVO = "attivo"
    INATTIVO = "inattivo"

@dataclass
class Cliente:
    id: str
    ragione_sociale: str
    email_referente: str
    telefono: str
    settore: str
    dimensione: str  # micro | piccola | media
    piano: str       # base | pro | enterprise
    stato: StatoCliente
    creato_at: str

def verifica_firma_webhook(payload: bytes, firma: str, segreto: str) -> bool:
    attesa = "sha256=" + hmac.new(
        segreto.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(attesa, firma)

@app.post("/webhook/nuovo-cliente")
async def ricevi_nuovo_cliente(
    request: Request,
    x_webhook_signature: str = Header(None),
):
    corpo = await request.body()
    if not verifica_firma_webhook(corpo, x_webhook_signature or "", N8N_WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Firma webhook non valida")

    dati = json.loads(corpo)
    cliente_id = str(uuid.uuid4())[:8].upper()
    cliente = Cliente(
        id=cliente_id,
        ragione_sociale=dati["ragione_sociale"],
        email_referente=dati["email_referente"],
        telefono=dati.get("telefono", ""),
        settore=dati.get("settore", "altro"),
        dimensione=dati.get("dimensione", "piccola"),
        piano=dati.get("piano", "base"),
        stato=StatoCliente.CONTRATTO_FIRMATO,
        creato_at=datetime.utcnow().isoformat(),
    )
    log.info("nuovo_cliente_ricevuto",
             cliente_id=cliente_id,
             ragione_sociale=cliente.ragione_sociale,
             piano=cliente.piano)
    # In produzione: salva su DB (asyncpg) e triggera n8n
    return JSONResponse({
        "status": "accepted",
        "cliente_id": cliente_id,
        "messaggio": f"Cliente {cliente.ragione_sociale} in elaborazione",
    }, status_code=202)

@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}
```

### A2 — Notifiche Multi-Canale

```python
# backend/notifiche.py
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol

import httpx
import structlog

log = structlog.get_logger()

class CanalNotifica(Protocol):
    async def invia(self, messaggio: str, destinatario: str) -> bool: ...

@dataclass
class NotificaSlack:
    webhook_url: str

    async def invia(self, messaggio: str, destinatario: str = "") -> bool:
        payload = {
            "text": messaggio,
            "channel": destinatario or "#automazione-eventi",
        }
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                resp = await client.post(self.webhook_url, json=payload)
                resp.raise_for_status()
                log.info("notifica_slack_inviata", canale=destinatario)
                return True
            except httpx.HTTPError as e:
                log.error("notifica_slack_fallita", errore=str(e))
                return False

@dataclass
class NotificaEmail:
    smtp_host: str
    smtp_port: int = 587
    username: str = ""
    password: str = ""

    async def invia(self, messaggio: str, destinatario: str) -> bool:
        log.info("email_simulata", destinatario=destinatario,
                 lunghezza_msg=len(messaggio))
        return True

class BroadcastNotifiche:
    """Invia notifica su tutti i canali configurati."""
    def __init__(self, canali: list[CanalNotifica]) -> None:
        self._canali = canali

    async def invia_tutti(self, messaggio: str, destinatari: list[str]) -> dict[str, bool]:
        risultati = {}
        for i, canale in enumerate(self._canali):
            for dest in destinatari:
                ok = await canale.invia(messaggio, dest)
                risultati[f"{type(canale).__name__}:{dest}"] = ok
        return risultati
```

---

## PART B — Workflow n8n per Onboarding

### B1 — Configurazione Workflow n8n (JSON Export)

```json
{
  "name": "Onboarding PMI - Nuovo Cliente",
  "nodes": [
    {
      "name": "Webhook Ingresso",
      "type": "n8n-nodes-base.webhook",
      "parameters": {
        "path": "nuovo-cliente",
        "responseMode": "responseNode",
        "options": {
          "allowedMethods": ["POST"]
        }
      },
      "position": [250, 300]
    },
    {
      "name": "Valida Payload",
      "type": "n8n-nodes-base.code",
      "parameters": {
        "jsCode": "const body = $input.item.json.body;\nconst campiObbligatori = ['ragione_sociale', 'email_referente', 'piano'];\nfor (const campo of campiObbligatori) {\n  if (!body[campo]) throw new Error(`Campo obbligatorio mancante: ${campo}`);\n}\nreturn { json: body };"
      },
      "position": [450, 300]
    },
    {
      "name": "Chiama Backend Python",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "http://backend:8000/webhook/nuovo-cliente",
        "method": "POST",
        "sendHeaders": true,
        "headerParameters": {
          "parameters": [
            {"name": "Content-Type", "value": "application/json"},
            {"name": "X-Webhook-Signature", "value": "={{$env.N8N_WEBHOOK_SECRET}}"}
          ]
        },
        "sendBody": true,
        "bodyParameters": {
          "parameters": [
            {"name": "ragione_sociale", "value": "={{$json.ragione_sociale}}"},
            {"name": "email_referente", "value": "={{$json.email_referente}}"},
            {"name": "piano", "value": "={{$json.piano}}"}
          ]
        }
      },
      "position": [650, 300]
    },
    {
      "name": "Notifica Slack Team Commerciale",
      "type": "n8n-nodes-base.slack",
      "parameters": {
        "channel": "#nuovi-clienti",
        "text": "🎉 Nuovo cliente onboarding: *{{$json.ragione_sociale}}* (Piano: {{$json.piano}})\nEmail: {{$json.email_referente}}"
      },
      "position": [850, 200]
    },
    {
      "name": "Email Benvenuto al Cliente",
      "type": "n8n-nodes-base.emailSend",
      "parameters": {
        "toEmail": "={{$json.email_referente}}",
        "subject": "Benvenuto in Azienda! — Prossimi passi",
        "text": "Gentile {{$json.ragione_sociale}},\n\nGrazie per aver scelto il nostro servizio.\n\nIl vostro account è in fase di configurazione...",
        "fromEmail": "onboarding@azienda.it"
      },
      "position": [850, 400]
    }
  ],
  "connections": {
    "Webhook Ingresso": {"main": [[{"node": "Valida Payload", "type": "main", "index": 0}]]},
    "Valida Payload": {"main": [[{"node": "Chiama Backend Python", "type": "main", "index": 0}]]},
    "Chiama Backend Python": {"main": [[
      {"node": "Notifica Slack Team Commerciale", "type": "main", "index": 0},
      {"node": "Email Benvenuto al Cliente", "type": "main", "index": 0}
    ]]}
  }
}
```

---

## PART C — Monitoring e Recovery

### C1 — Health Check e Auto-Recovery

```python
# scripts/monitor_sistema.py
"""
Script di monitoring del sistema onboarding PMI.
Eseguire come cron ogni 5 minuti: */5 * * * * python monitor_sistema.py
"""
from __future__ import annotations

import asyncio
import os
import sys
from dataclasses import dataclass
from datetime import datetime

import httpx
import structlog

log = structlog.get_logger()

@dataclass
class ComponenteSistema:
    nome: str
    url: str
    endpoint_health: str
    critico: bool

COMPONENTI = [
    ComponenteSistema("n8n", "http://localhost:5678", "/healthz", True),
    ComponenteSistema("backend", "http://localhost:8000", "/health", True),
    ComponenteSistema("postgres", "http://localhost:5432", "", False),
]

@dataclass
class RisultatoHealth:
    componente: str
    ok: bool
    latenza_ms: float
    errore: str | None

async def controlla_componente(comp: ComponenteSistema) -> RisultatoHealth:
    if not comp.endpoint_health:
        return RisultatoHealth(comp.nome, True, 0.0, None)
    inizio = asyncio.get_event_loop().time()
    async with httpx.AsyncClient(timeout=5) as client:
        try:
            resp = await client.get(comp.url + comp.endpoint_health)
            latenza = (asyncio.get_event_loop().time() - inizio) * 1000
            return RisultatoHealth(
                comp.nome,
                resp.status_code == 200,
                latenza,
                None if resp.status_code == 200 else f"HTTP {resp.status_code}",
            )
        except Exception as e:
            latenza = (asyncio.get_event_loop().time() - inizio) * 1000
            return RisultatoHealth(comp.nome, False, latenza, str(e))

async def controlla_tutto() -> list[RisultatoHealth]:
    return await asyncio.gather(*[controlla_componente(c) for c in COMPONENTI])

async def main() -> None:
    log.info("health_check_avviato", timestamp=datetime.utcnow().isoformat())
    risultati = await controlla_tutto()
    critici_down = []
    for r in risultati:
        status = "✅ OK" if r.ok else "❌ DOWN"
        log.info("componente_status",
                 componente=r.componente, ok=r.ok,
                 latenza_ms=round(r.latenza_ms, 1), errore=r.errore)
        print(f"  {status} {r.componente} ({r.latenza_ms:.0f}ms)"
              + (f" — {r.errore}" if r.errore else ""))
        comp = next((c for c in COMPONENTI if c.nome == r.componente), None)
        if comp and comp.critico and not r.ok:
            critici_down.append(r.componente)

    if critici_down:
        log.error("componenti_critici_down", componenti=critici_down)
        sys.exit(1)
    log.info("sistema_ok")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## PART D — Deploy e Passaggio in Produzione

### D1 — Checklist Pre-Produzione

```
CHECKLIST DEPLOY PRODUZIONE:

□ SICUREZZA
  □ N8N_ENCRYPTION_KEY: 32 byte random (openssl rand -hex 32)
  □ N8N_WEBHOOK_SECRET: 16 byte random
  □ POSTGRES_PASSWORD: password forte (non "n8n_secret")
  □ TLS attivo (reverse proxy Nginx/Caddy/Traefik)
  □ Backup database configurato e testato
  □ Firewall: solo porte 443/80 esposte

□ CONFIGURAZIONE
  □ WEBHOOK_URL punta al dominio produzione (non localhost)
  □ Email SMTP configurato con credenziali reali
  □ Slack webhook configurato
  □ Variabili d'ambiente in vault (non .env file in git)

□ MONITORING
  □ Cron health check ogni 5 minuti
  □ Alert email per errori critici
  □ Log rotation configurato
  □ Spazio disco monitorato

□ TESTING
  □ Test end-to-end eseguito in staging
  □ Rollback procedure documentata e testata
  □ Load test: 100 webhook/ora senza degrado

□ DOCUMENTAZIONE
  □ RUNBOOK: procedura restart componenti
  □ Contatto on-call documentato
  □ Governance manifest creati per tutti i workflow

PROCEDURA ROLLBACK:
  docker compose stop n8n backend
  docker compose pull  # torna alla precedente con tag specifico
  docker compose up -d
  # Verifica: ./scripts/monitor_sistema.py
```

---

## Esercizi

### Esercizio 1 — Deploy Completo (60 min)

1. Clona il progetto, configura `.env` con i segreti generati
2. Esegui `docker compose up -d` e verifica tutti i servizi healthy
3. Configura il workflow n8n importando il JSON dalla sezione B1
4. Testa con curl un webhook di nuovo cliente
5. Verifica: email simulata loggata, messaggio Slack inviato, cliente_id generato

### Esercizio 2 — Recovery Automatico (25 min)

1. Ferma il backend: `docker compose stop backend`
2. Esegui `python scripts/monitor_sistema.py` — deve rilevare il problema
3. Scrivi uno script `auto_recover.py` che:
   - Se il backend è down → esegue `docker compose start backend`
   - Attende 15 secondi
   - Riverifica il health check
   - Loga il risultato del recovery

### Esercizio 3 — Metriche di Business (20 min)

Aggiungi al backend `/metrics` che restituisce:
```json
{
  "clienti_totali": 42,
  "onboarding_in_corso": 5,
  "tasso_completamento_24h": 0.87,
  "piano_piu_popolare": "pro"
}
```
Dati reali dal database (usa asyncpg per query SQL).

---

## Riferimenti

- FastAPI docs: https://fastapi.tiangolo.com/
- n8n self-hosting: https://docs.n8n.io/hosting/
- Docker Compose reference: https://docs.docker.com/compose/
- Modulo sorgente: `08-progetti-pratici-automazione.md`
