---
corso: "Automazioni e Flussi di Lavoro"
fase: "6 — Governance"
modulo: 24
titolo: "Audit Logging Compliance — GDPR, SOX, HIPAA per Workflow"
versione: "Python 3.11+, PostgreSQL 15+, Wazuh 4.7+, Elasticsearch 8.x, Loki 2.9+"
livello: "proficient"
prerequisiti: ["Modulo 07 — Logging e Monitoring", "Concetti compliance GDPR/SOX/HIPAA", "JSON, Python, SQL"]
obiettivi:
  - "Strutturare audit log con schema immutabile e campi obbligatori per compliance GDPR, SOX e HIPAA"
  - "Implementare retention policy configurabile con lifecycle management e archiviazione a norma"
  - "Garantire tamper-evidence con hash chain, WORM storage e firma digitale dei log"
  - "Configurare SIEM forwarding verso Wazuh/Elasticsearch e alerting su eventi anomali"
  - "Applicare pseudonimizzazione e data lineage per tracciare il flusso dei dati personali nei workflow"
tag: [audit-log, compliance, gdpr, sox, hipaa, siem, tamper-evidence, pseudonimizzazione, data-lineage]
---

# Audit Logging Compliance — GDPR, SOX, HIPAA per Workflow

> **Obiettivi di apprendimento**
> 1. Strutturare audit log con schema immutabile e campi obbligatori per compliance GDPR, SOX e HIPAA
> 2. Implementare retention policy configurabile con lifecycle management e archiviazione a norma
> 3. Garantire tamper-evidence con hash chain, WORM storage e firma digitale dei log
> 4. Configurare SIEM forwarding verso Wazuh/Elasticsearch e alerting su eventi anomali
> 5. Applicare pseudonimizzazione e data lineage per tracciare il flusso dei dati personali nei workflow

> **Modulo del corso:** Automazioni e Flussi di Lavoro
> **Posizione:** Fase 5 — Governance · Modulo 24 (nuovo)
> **Prerequisiti:** Modulo 07; concetti compliance; familiarita con JSON, Python, SQL.
> **Obiettivi:** strutturare audit log per compliance; retention policy; tamper-evidence; SIEM forward; pseudonimizzazione; data lineage.
> **Tempo:** lettura 60 min · lab 240 min
> **Livello:** proficient
> **Ultimo aggiornamento:** 2026-05-24
> **Versioni:** Python 3.11+, PostgreSQL 15+, Wazuh 4.7+, Elasticsearch 8.x, Loki 2.9+.

---

## Indice

1. [Idee guida](#idee-guida)
2. [Perche l'audit logging e critico per i workflow](#perche-laudit-logging-e-critico-per-i-workflow)
3. [Normative di riferimento — panoramica completa](#normative-di-riferimento--panoramica-completa)
4. [Schema audit event — progettazione completa](#schema-audit-event--progettazione-completa)
5. [Implementazione Python — audit logger robusto](#implementazione-python--audit-logger-robusto)
6. [Tamper-evidence: hash chain](#tamper-evidence-hash-chain)
7. [Append-only storage — PostgreSQL](#append-only-storage--postgresql)
8. [Append-only storage — Elasticsearch / OpenSearch](#append-only-storage--elasticsearch--opensearch)
9. [Retention policy per regolamento](#retention-policy-per-regolamento)
10. [GDPR e right to be forgotten — pseudonimizzazione](#gdpr-e-right-to-be-forgotten--pseudonimizzazione)
11. [SIEM forward — architettura e configurazione](#siem-forward--architettura-e-configurazione)
12. [Wazuh — configurazione completa per audit workflow](#wazuh--configurazione-completa-per-audit-workflow)
13. [Integrazione con orchestratori di workflow](#integrazione-con-orchestratori-di-workflow)
14. [Data lineage e audit trail per ETL](#data-lineage-e-audit-trail-per-etl)
15. [Access control sugli audit log](#access-control-sugli-audit-log)
16. [Monitoring e alerting sull'integrita degli audit log](#monitoring-e-alerting-sullintegrita-degli-audit-log)
17. [Architettura multi-tenant per audit](#architettura-multi-tenant-per-audit)
18. [Esportazione e reportistica per auditor](#esportazione-e-reportistica-per-auditor)
19. [Anti-pattern e errori comuni](#anti-pattern-e-errori-comuni)
20. [Esercizi](#esercizi)
21. [Troubleshooting — 15 problemi comuni](#troubleshooting--15-problemi-comuni)
22. [FAQ — 15 domande e risposte](#faq--15-domande-e-risposte)
23. [Auto-valutazione](#auto-valutazione)
24. [Letture primarie consigliate](#letture-primarie-consigliate)
25. [Collegamenti incrociati](#collegamenti-incrociati)
26. [Glossario locale](#glossario-locale)

---

## Idee guida

1. **Audit log = legalmente vincolante.** Una volta scritto, mai cancellabile fino a fine retention.
2. **Tamper-evidence: hash chain o blockchain-light.** Detect modifiche post-fatto.
3. **GDPR: 5 anni, ma include "right to be forgotten".** Conflitto risolto via pseudonimizzazione.
4. **SIEM forward = mandatory in produzione.** Local logs sono primo target di un attaccante.
5. **Audit log structured (JSON), non free-text.** Searchable, parsable, alertable.
6. **Separation of duty.** Chi produce l'audit log non deve poter cancellarlo.
7. **Retention != backup.** Retention e obbligo legale; backup e disaster recovery. Servono entrambi.
8. **Ogni workflow execution genera audit events.** Non solo gli errori — anche i successi sono evidenza.
9. **Clock synchronization.** Audit timestamp affidabile richiede NTP sincronizzato su tutti i nodi.
10. **Data lineage e audit sono complementari.** L'audit dice chi ha fatto cosa; il lineage dice da dove vengono i dati.

---

## Perche l'audit logging e critico per i workflow

### Il contesto normativo

Un workflow di automazione che processa dati personali (GDPR), dati finanziari (SOX), o dati sanitari (HIPAA) deve produrre un audit trail che risponda a queste domande:

| Domanda | Risposta nell'audit log |
|---|---|
| Chi ha avviato il workflow? | `actor.id`, `actor.type`, `actor.ip` |
| Quando e stato eseguito? | `timestamp` (UTC ISO 8601) |
| Cosa ha fatto? | `action`, `resource.type`, `resource.id` |
| Quale input ha ricevuto? | `metadata.input_hash` (hash, mai dati grezzi) |
| Quale output ha prodotto? | `metadata.output_hash` |
| E riuscito o fallito? | `outcome` (success/failure/partial) |
| E stato modificato dopo? | `hash_prev` (hash chain per tamper detection) |
| Quale versione del workflow? | `workflow.version`, `workflow.commit_sha` |
| In quale ambiente? | `environment` (dev/staging/prod) |

### Scenari reali

**Scenario 1 — audit GDPR:** Un utente esercita il diritto di accesso (Art. 15). L'azienda deve dimostrare tutti i trattamenti effettuati sui dati dell'utente. L'audit log, filtrando per `actor.id = user-123` o `resource.data_subjects contains user-123`, fornisce l'elenco completo.

**Scenario 2 — audit SOX:** Un revisore contabile chiede evidenza di tutti i workflow che hanno toccato dati finanziari nell'ultimo quarter. L'audit log, filtrando per `resource.type = financial_record` e `timestamp between Q1_start AND Q1_end`, genera il report.

**Scenario 3 — incident response:** Un workflow ha inviato email a destinatari sbagliati. L'audit trail mostra la catena completa: chi ha modificato la configurazione, quando, e quale esecuzione ha usato la configurazione errata.

**Scenario 4 — compliance HIPAA:** Un workflow che processa cartelle cliniche deve registrare ogni accesso (read, write, delete) ai Protected Health Information (PHI). L'audit log deve essere conservato 6 anni e non deve contenere PHI nei campi non protetti.

---

## Normative di riferimento — panoramica completa

### GDPR (Regolamento UE 2016/679)

| Articolo | Requisito audit | Impatto sul logging |
|---|---|---|
| Art. 5(2) | Accountability | Dimostrare conformita con log |
| Art. 15 | Diritto di accesso | Query audit log per data subject |
| Art. 17 | Right to be forgotten | Pseudonimizzazione negli audit log |
| Art. 25 | Privacy by design | Minimizzazione dati negli audit event |
| Art. 30 | Registro trattamenti | Audit log come prova |
| Art. 33 | Notifica breach | Audit log per ricostruire l'incidente |
| Art. 35 | DPIA | Audit log come input per valutazione rischio |

**Retention GDPR:** Non c'e un termine fisso universale. La retention dipende dallo scopo del trattamento. La prassi e 5 anni come default, ma deve essere giustificata caso per caso.

### SOX (Sarbanes-Oxley Act, 2002)

| Sezione | Requisito | Impatto |
|---|---|---|
| Sec. 302 | Certificazione controlli interni | Audit trail per workflow finanziari |
| Sec. 404 | Valutazione controlli interni | Evidenza che i controlli funzionano |
| Sec. 802 | Distruzione documenti | Vietato cancellare audit log prima di 7 anni |

**Retention SOX:** 7 anni obbligatori. Nessuna eccezione.

### HIPAA (Health Insurance Portability and Accountability Act)

| Regola | Requisito | Impatto |
|---|---|---|
| Security Rule §164.312(b) | Audit controls | Log accesso a ePHI |
| Security Rule §164.308(a)(1)(ii)(D) | Information system activity review | Revisione periodica audit log |
| Privacy Rule §164.528 | Accounting of disclosures | Log ogni disclosure di PHI |

**Retention HIPAA:** 6 anni dalla data di creazione o dall'ultimo uso del record, il piu recente.

### PCI-DSS v4.0

| Requisito | Descrizione | Impatto |
|---|---|---|
| 10.1 | Log accesso a dati cardholder | Ogni accesso a PAN deve essere loggato |
| 10.2 | Contenuto audit trail | Identita utente, tipo evento, data/ora, successo/fallimento |
| 10.3 | Protezione audit trail | Immutabilita, integrity, accesso limitato |
| 10.7 | Retention | 12 mesi minimo, 3 mesi immediatamente disponibili |

### AGID / CAD (Codice Amministrazione Digitale — Italia)

| Norma | Requisito | Retention |
|---|---|---|
| Art. 43-44 CAD | Conservazione digitale | 10 anni |
| Linee guida AgID | Formato, metadati, firma | Conforme a UNI 11386 (SInCRO) |
| DPCM 3/12/2013 | Regole conservazione | Responsabile conservazione obbligatorio |

### NIS2 (Direttiva UE 2022/2555)

Applicabile a partire da ottobre 2024, impone obblighi di logging per operatori di servizi essenziali e importanti:

| Requisito | Impatto |
|---|---|
| Art. 21 | Misure di gestione rischio cyber, incluso logging |
| Art. 23 | Notifica incidenti: audit log come evidenza |
| Art. 32 | Poteri di vigilanza: auditor possono richiedere log |

### Matrice comparativa retention

| Regolamento | Retention minima | Online (query rapida) | Archive (cold) | Note |
|---|---|---|---|---|
| GDPR | 5 anni (default) | 1 anno | 4 anni | Variabile per scopo specifico |
| SOX | 7 anni | 2 anni | 5 anni | Audit finanziario |
| HIPAA | 6 anni | 1 anno | 5 anni | Dalla creazione o ultimo uso |
| PCI-DSS | 1 anno | 3 mesi | 9 mesi | Hot 3 mesi obbligatori |
| AGID (IT) | 10 anni | 2 anni | 8 anni | Conservazione digitale |
| NIS2 | Non specificato | Best practice: 2 anni | Best practice: 5 anni | Segui regolamento settoriale |

---

## Schema audit event — progettazione completa

### Schema JSON minimo

```json
{
  "event_id": "evt_2026-05-22T14:32:11.234Z_a1b2c3d4",
  "timestamp": "2026-05-22T14:32:11.234Z",
  "timestamp_ingested": "2026-05-22T14:32:11.300Z",
  "version": "1.2.0",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7",
  "actor": {
    "type": "user",
    "id": "user-123",
    "email_hash": "sha256:abc...",
    "ip": "203.0.113.5",
    "user_agent": "Mozilla/5.0...",
    "auth_method": "oauth2_pkce",
    "session_id": "sess-456"
  },
  "action": "workflow.execute",
  "action_category": "workflow_management",
  "resource": {
    "type": "workflow",
    "id": "onboarding-v2",
    "name": "Employee Onboarding",
    "version": "2.3.1",
    "environment": "production"
  },
  "outcome": "success",
  "outcome_reason": null,
  "metadata": {
    "input_hash": "sha256:e3b0c44298fc1c...",
    "output_hash": "sha256:d7a8fbb307d78...",
    "records_processed": 42,
    "duration_ms": 1523,
    "workflow_run_id": "run-789",
    "trigger_type": "scheduled",
    "data_subjects": ["pseudonym-abc"],
    "data_categories": ["personal_data", "financial_data"],
    "legal_basis": "gdpr_art6_1b_contract"
  },
  "source": {
    "service": "workflow-engine",
    "version": "3.1.0",
    "host": "worker-node-03",
    "commit_sha": "a1b2c3d"
  },
  "hash_prev": "sha256:previous_event_hash_here",
  "hash_self": "sha256:this_event_hash_here"
}
```

### JSON Schema per validazione

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://internal.company.com/schemas/audit-event/v1.2.0",
  "title": "Audit Event",
  "description": "Schema per eventi di audit compliance-ready",
  "type": "object",
  "required": [
    "event_id", "timestamp", "version", "actor",
    "action", "resource", "outcome", "hash_prev"
  ],
  "properties": {
    "event_id": {
      "type": "string",
      "pattern": "^evt_[0-9T:.Z-]+_[a-f0-9]+$",
      "description": "ID univoco evento, non riutilizzabile"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "UTC ISO 8601 con millisecondi"
    },
    "timestamp_ingested": {
      "type": "string",
      "format": "date-time",
      "description": "Timestamp ricezione dal sistema di audit"
    },
    "version": {
      "type": "string",
      "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+$",
      "description": "Versione dello schema audit event"
    },
    "trace_id": {
      "type": "string",
      "pattern": "^[a-f0-9]{32}$"
    },
    "span_id": {
      "type": "string",
      "pattern": "^[a-f0-9]{16}$"
    },
    "actor": {
      "type": "object",
      "required": ["type", "id"],
      "properties": {
        "type": {
          "type": "string",
          "enum": ["user", "service", "system", "api_key", "webhook"]
        },
        "id": { "type": "string", "minLength": 1 },
        "email_hash": { "type": "string" },
        "ip": { "type": "string", "format": "ipv4" },
        "user_agent": { "type": "string" },
        "auth_method": {
          "type": "string",
          "enum": [
            "oauth2_pkce", "oauth2_client_credentials",
            "api_key", "mtls", "saml", "internal"
          ]
        },
        "session_id": { "type": "string" }
      }
    },
    "action": {
      "type": "string",
      "pattern": "^[a-z_]+\\.[a-z_]+$",
      "description": "Formato: resource_type.verb"
    },
    "action_category": {
      "type": "string",
      "enum": [
        "workflow_management", "data_access", "data_modification",
        "data_deletion", "configuration_change", "authentication",
        "authorization", "system_event", "export", "disclosure"
      ]
    },
    "resource": {
      "type": "object",
      "required": ["type", "id"],
      "properties": {
        "type": { "type": "string" },
        "id": { "type": "string" },
        "name": { "type": "string" },
        "version": { "type": "string" },
        "environment": {
          "type": "string",
          "enum": ["development", "staging", "production"]
        }
      }
    },
    "outcome": {
      "type": "string",
      "enum": ["success", "failure", "partial", "denied"]
    },
    "outcome_reason": {
      "type": ["string", "null"],
      "description": "Motivo in caso di failure/denied"
    },
    "metadata": {
      "type": "object",
      "properties": {
        "input_hash": { "type": "string" },
        "output_hash": { "type": "string" },
        "records_processed": { "type": "integer", "minimum": 0 },
        "duration_ms": { "type": "integer", "minimum": 0 },
        "data_subjects": {
          "type": "array",
          "items": { "type": "string" },
          "description": "Pseudonimi dei data subject coinvolti"
        },
        "data_categories": {
          "type": "array",
          "items": { "type": "string" }
        },
        "legal_basis": { "type": "string" }
      }
    },
    "source": {
      "type": "object",
      "properties": {
        "service": { "type": "string" },
        "version": { "type": "string" },
        "host": { "type": "string" },
        "commit_sha": { "type": "string" }
      }
    },
    "hash_prev": { "type": "string" },
    "hash_self": { "type": "string" }
  },
  "additionalProperties": false
}
```

### Validazione in Python

```python
import jsonschema
import json
from pathlib import Path

def load_schema(schema_path: str) -> dict:
    """Carica JSON Schema dal filesystem."""
    return json.loads(Path(schema_path).read_text())

def validate_audit_event(event: dict, schema: dict) -> tuple[bool, str]:
    """Valida un audit event contro lo schema.

    Returns:
        (is_valid, error_message)
    """
    try:
        jsonschema.validate(instance=event, schema=schema)
        return True, ""
    except jsonschema.ValidationError as e:
        return False, f"Validation error at {e.json_path}: {e.message}"
    except jsonschema.SchemaError as e:
        return False, f"Schema error: {e.message}"

# Utilizzo
schema = load_schema("schemas/audit-event-v1.2.0.json")
event = {
    "event_id": "evt_2026-05-22T14:32:11.234Z_a1b2c3d4",
    "timestamp": "2026-05-22T14:32:11.234Z",
    "version": "1.2.0",
    "actor": {"type": "user", "id": "user-123"},
    "action": "workflow.execute",
    "resource": {"type": "workflow", "id": "onboarding-v2"},
    "outcome": "success",
    "hash_prev": "sha256:abc123",
}
is_valid, error = validate_audit_event(event, schema)
```

### Tassonomia azioni standard

| action | action_category | Descrizione |
|---|---|---|
| `workflow.execute` | workflow_management | Esecuzione workflow |
| `workflow.create` | workflow_management | Creazione workflow |
| `workflow.update` | configuration_change | Modifica workflow |
| `workflow.delete` | configuration_change | Cancellazione workflow |
| `workflow.enable` | configuration_change | Abilitazione workflow |
| `workflow.disable` | configuration_change | Disabilitazione workflow |
| `data.read` | data_access | Lettura dati |
| `data.write` | data_modification | Scrittura dati |
| `data.delete` | data_deletion | Cancellazione dati |
| `data.export` | export | Esportazione dati |
| `data.disclose` | disclosure | Divulgazione a terzi (HIPAA) |
| `config.update` | configuration_change | Modifica configurazione |
| `auth.login` | authentication | Login utente |
| `auth.logout` | authentication | Logout utente |
| `auth.login_failed` | authentication | Login fallito |
| `authz.denied` | authorization | Accesso negato |
| `credential.rotate` | configuration_change | Rotazione credenziali |

---

## Implementazione Python — audit logger robusto

### Modulo audit_logger.py

```python
"""
Audit logger robusto per workflow automation.

Caratteristiche:
- Append-only: una volta scritto, non modificabile
- Hash chain: ogni evento include hash del precedente
- Validazione schema: ogni evento validato prima della scrittura
- Multi-backend: PostgreSQL, file, Elasticsearch
- Async batch: buffer + flush periodico per performance
- Retry: tentativi multipli in caso di errore backend
"""

import hashlib
import json
import logging
import time
import threading
import uuid
from collections import deque
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

logger = logging.getLogger("audit")


class ActorType(str, Enum):
    USER = "user"
    SERVICE = "service"
    SYSTEM = "system"
    API_KEY = "api_key"
    WEBHOOK = "webhook"


class Outcome(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    DENIED = "denied"


class ActionCategory(str, Enum):
    WORKFLOW_MANAGEMENT = "workflow_management"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    DATA_DELETION = "data_deletion"
    CONFIGURATION_CHANGE = "configuration_change"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    SYSTEM_EVENT = "system_event"
    EXPORT = "export"
    DISCLOSURE = "disclosure"


@dataclass(frozen=True)
class Actor:
    """Attore che ha generato l'evento. Frozen per immutabilita."""
    type: ActorType
    id: str
    email_hash: str = ""
    ip: str = ""
    user_agent: str = ""
    auth_method: str = ""
    session_id: str = ""


@dataclass(frozen=True)
class Resource:
    """Risorsa su cui l'azione e stata eseguita."""
    type: str
    id: str
    name: str = ""
    version: str = ""
    environment: str = ""


@dataclass(frozen=True)
class AuditEvent:
    """Singolo evento di audit, immutabile dopo creazione."""
    event_id: str
    timestamp: str
    version: str
    actor: Actor
    action: str
    action_category: ActionCategory
    resource: Resource
    outcome: Outcome
    outcome_reason: Optional[str] = None
    trace_id: str = ""
    span_id: str = ""
    metadata: dict = field(default_factory=dict)
    source: dict = field(default_factory=dict)
    hash_prev: str = ""
    hash_self: str = ""

    def to_dict(self) -> dict:
        """Serializza in dict per JSON export."""
        d = asdict(self)
        d["actor"]["type"] = self.actor.type.value
        d["outcome"] = self.outcome.value
        d["action_category"] = self.action_category.value
        return d

    def to_json(self) -> str:
        """Serializza in JSON stringa."""
        return json.dumps(self.to_dict(), default=str, ensure_ascii=False)


def compute_event_hash(event_json: str) -> str:
    """Calcola SHA-256 dell'evento per la hash chain."""
    return f"sha256:{hashlib.sha256(event_json.encode('utf-8')).hexdigest()}"


def hash_pii(value: str, salt: str) -> str:
    """Hash di un valore PII con salt per pseudonimizzazione.

    ATTENZIONE: Non usare per password. Usare solo per
    pseudonimizzazione audit log (GDPR Art. 4(5)).
    """
    combined = f"{salt}:{value}"
    return f"sha256:{hashlib.sha256(combined.encode('utf-8')).hexdigest()}"


class AuditLoggerBackend:
    """Interfaccia base per backend di audit logging."""

    def write(self, event: AuditEvent) -> bool:
        """Scrive un evento. Ritorna True se successo."""
        raise NotImplementedError

    def write_batch(self, events: list[AuditEvent]) -> int:
        """Scrive un batch. Ritorna numero eventi scritti."""
        raise NotImplementedError

    def flush(self) -> None:
        """Forza flush del buffer."""
        pass

    def close(self) -> None:
        """Chiude connessioni."""
        pass


class FileAuditBackend(AuditLoggerBackend):
    """Backend append-only su file.

    Ogni riga e un JSON event. Il file e append-only:
    nessuna operazione di modifica o cancellazione.
    """

    def __init__(self, path: str, max_file_size_mb: int = 100):
        self._path = path
        self._max_file_size_mb = max_file_size_mb
        self._lock = threading.Lock()

    def write(self, event: AuditEvent) -> bool:
        line = event.to_json() + "\n"
        with self._lock:
            with open(self._path, "a", encoding="utf-8") as f:
                f.write(line)
        return True

    def write_batch(self, events: list[AuditEvent]) -> int:
        lines = "".join(e.to_json() + "\n" for e in events)
        with self._lock:
            with open(self._path, "a", encoding="utf-8") as f:
                f.write(lines)
        return len(events)


class PostgreSQLAuditBackend(AuditLoggerBackend):
    """Backend PostgreSQL con tabella append-only.

    La tabella usa GRANT/REVOKE per impedire UPDATE e DELETE
    all'utente applicativo. Solo INSERT permesso.
    """

    def __init__(self, dsn: str):
        import psycopg2
        self._conn = psycopg2.connect(dsn)
        self._conn.autocommit = False

    def write(self, event: AuditEvent) -> bool:
        return self.write_batch([event]) == 1

    def write_batch(self, events: list[AuditEvent]) -> int:
        cursor = self._conn.cursor()
        try:
            for event in events:
                cursor.execute(
                    """
                    INSERT INTO audit_events (
                        event_id, timestamp_utc, version, actor_type, actor_id,
                        action, action_category, resource_type, resource_id,
                        outcome, outcome_reason, trace_id, metadata_json,
                        source_json, hash_prev, hash_self
                    ) VALUES (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s
                    )
                    """,
                    (
                        event.event_id,
                        event.timestamp,
                        event.version,
                        event.actor.type.value,
                        event.actor.id,
                        event.action,
                        event.action_category.value,
                        event.resource.type,
                        event.resource.id,
                        event.outcome.value,
                        event.outcome_reason,
                        event.trace_id,
                        json.dumps(event.metadata, default=str),
                        json.dumps(event.source, default=str),
                        event.hash_prev,
                        event.hash_self,
                    ),
                )
            self._conn.commit()
            return len(events)
        except Exception:
            self._conn.rollback()
            raise

    def close(self) -> None:
        self._conn.close()


class AuditLogger:
    """Logger di audit principale con buffer asincrono e hash chain.

    Uso:
        audit = AuditLogger(backend=PostgreSQLAuditBackend(dsn), ...)
        audit.log(actor=..., action=..., resource=..., outcome=...)
        audit.close()  # flush finale
    """

    SCHEMA_VERSION = "1.2.0"

    def __init__(
        self,
        backend: AuditLoggerBackend,
        service_name: str = "workflow-engine",
        service_version: str = "1.0.0",
        pii_salt: str = "",
        buffer_size: int = 100,
        flush_interval_seconds: float = 5.0,
    ):
        self._backend = backend
        self._service_name = service_name
        self._service_version = service_version
        self._pii_salt = pii_salt
        self._buffer: deque[AuditEvent] = deque(maxlen=buffer_size * 2)
        self._buffer_size = buffer_size
        self._flush_interval = flush_interval_seconds
        self._last_hash = "sha256:genesis"
        self._lock = threading.Lock()
        self._closed = False

        # Timer periodico per flush
        self._flush_timer = None
        self._schedule_flush()

    def _schedule_flush(self) -> None:
        """Schedula flush periodico."""
        if self._closed:
            return
        self._flush_timer = threading.Timer(
            self._flush_interval, self._timed_flush
        )
        self._flush_timer.daemon = True
        self._flush_timer.start()

    def _timed_flush(self) -> None:
        """Callback flush periodico."""
        self.flush()
        self._schedule_flush()

    def log(
        self,
        actor: Actor,
        action: str,
        action_category: ActionCategory,
        resource: Resource,
        outcome: Outcome,
        outcome_reason: Optional[str] = None,
        trace_id: str = "",
        span_id: str = "",
        metadata: Optional[dict] = None,
    ) -> str:
        """Registra un audit event.

        Returns:
            event_id dell'evento creato.
        """
        if self._closed:
            raise RuntimeError("AuditLogger is closed")

        now = datetime.now(timezone.utc)
        event_id = f"evt_{now.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]}Z_{uuid.uuid4().hex[:8]}"

        event = AuditEvent(
            event_id=event_id,
            timestamp=now.isoformat(timespec="milliseconds"),
            version=self.SCHEMA_VERSION,
            actor=actor,
            action=action,
            action_category=action_category,
            resource=resource,
            outcome=outcome,
            outcome_reason=outcome_reason,
            trace_id=trace_id,
            span_id=span_id,
            metadata=metadata or {},
            source={
                "service": self._service_name,
                "version": self._service_version,
                "host": _get_hostname(),
            },
            hash_prev=self._last_hash,
        )

        # Calcola hash dell'evento (senza hash_self, poi aggiungilo)
        event_json = event.to_json()
        event_hash = compute_event_hash(event_json)

        # Crea evento finale con hash_self
        event = AuditEvent(
            **{
                **asdict(event),
                "actor": event.actor,
                "resource": event.resource,
                "outcome": event.outcome,
                "action_category": event.action_category,
                "hash_self": event_hash,
            }
        )

        with self._lock:
            self._buffer.append(event)
            self._last_hash = event_hash

            if len(self._buffer) >= self._buffer_size:
                self._do_flush()

        return event_id

    def flush(self) -> int:
        """Forza flush del buffer. Ritorna numero eventi scritti."""
        with self._lock:
            return self._do_flush()

    def _do_flush(self) -> int:
        """Flush interno (deve essere chiamato con lock acquisito)."""
        if not self._buffer:
            return 0

        events = list(self._buffer)
        self._buffer.clear()

        try:
            written = self._backend.write_batch(events)
            logger.info("Flushed %d audit events", written)
            return written
        except Exception as e:
            # Re-inserisci gli eventi nel buffer per retry
            for event in reversed(events):
                self._buffer.appendleft(event)
            logger.error("Flush fallito, %d eventi in buffer: %s", len(events), e)
            raise

    def close(self) -> None:
        """Flush finale e chiusura."""
        self._closed = True
        if self._flush_timer:
            self._flush_timer.cancel()
        self.flush()
        self._backend.close()


def _get_hostname() -> str:
    """Ritorna hostname del nodo."""
    import socket
    return socket.gethostname()
```

### Utilizzo nel workflow

```python
from audit_logger import (
    AuditLogger, PostgreSQLAuditBackend,
    Actor, ActorType, Resource, Outcome, ActionCategory,
    hash_pii,
)

# Inizializzazione (una volta all'avvio)
backend = PostgreSQLAuditBackend(dsn="postgresql://audit_writer:***@db:5432/audit")
audit = AuditLogger(
    backend=backend,
    service_name="etl-engine",
    service_version="2.1.0",
    pii_salt="random-salt-from-vault",
)

# In un workflow handler
def handle_order_processing(user_id: str, user_email: str, order_id: str):
    actor = Actor(
        type=ActorType.USER,
        id=user_id,
        email_hash=hash_pii(user_email, audit._pii_salt),
        ip=get_client_ip(),
        auth_method="oauth2_pkce",
    )
    resource = Resource(
        type="order",
        id=order_id,
        environment="production",
    )

    # Log inizio
    audit.log(
        actor=actor,
        action="workflow.execute",
        action_category=ActionCategory.WORKFLOW_MANAGEMENT,
        resource=resource,
        outcome=Outcome.SUCCESS,
        metadata={
            "input_hash": compute_event_hash(json.dumps({"order_id": order_id})),
            "trigger_type": "api_call",
        },
    )

    try:
        result = process_order(order_id)

        # Log successo con output hash
        audit.log(
            actor=actor,
            action="data.write",
            action_category=ActionCategory.DATA_MODIFICATION,
            resource=Resource(type="order_result", id=order_id, environment="production"),
            outcome=Outcome.SUCCESS,
            metadata={
                "output_hash": compute_event_hash(json.dumps(result)),
                "records_processed": result["count"],
            },
        )
    except Exception as e:
        # Log fallimento
        audit.log(
            actor=actor,
            action="workflow.execute",
            action_category=ActionCategory.WORKFLOW_MANAGEMENT,
            resource=resource,
            outcome=Outcome.FAILURE,
            outcome_reason=str(e),
        )
        raise

# Shutdown
audit.close()
```

---

## Tamper-evidence: hash chain

### Principio

Ogni audit event include l'hash dell'evento precedente (`hash_prev`). Questo crea una catena: se qualcuno modifica un evento intermedio, l'hash non corrispondera piu, e la verifica fallira.

```
Event 1:  hash_prev = "sha256:genesis"
          hash_self = SHA256(event_1_json) = "sha256:aaa..."

Event 2:  hash_prev = "sha256:aaa..."  ← deve matchare hash_self di Event 1
          hash_self = SHA256(event_2_json) = "sha256:bbb..."

Event 3:  hash_prev = "sha256:bbb..."  ← deve matchare hash_self di Event 2
          hash_self = SHA256(event_3_json) = "sha256:ccc..."
```

Se qualcuno modifica Event 2, il suo `hash_self` cambiera, ma `hash_prev` di Event 3 conterr il vecchio hash. La catena e rotta.

### Implementazione verifica integrita

```python
import json
import hashlib
from pathlib import Path


def verify_audit_chain(audit_file: str) -> tuple[bool, int, str]:
    """Verifica l'integrita della hash chain in un file audit log.

    Args:
        audit_file: Path al file JSONL di audit.

    Returns:
        (is_valid, events_verified, error_message)
    """
    events = []
    with open(audit_file, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                events.append((line_num, json.loads(line)))
            except json.JSONDecodeError as e:
                return False, line_num - 1, f"Riga {line_num}: JSON invalido: {e}"

    if not events:
        return True, 0, "Nessun evento da verificare"

    expected_prev = "sha256:genesis"

    for line_num, event in events:
        # Verifica hash_prev
        actual_prev = event.get("hash_prev", "")
        if actual_prev != expected_prev:
            return (
                False,
                line_num - 1,
                f"Riga {line_num}: hash_prev mismatch. "
                f"Atteso: {expected_prev[:20]}... "
                f"Trovato: {actual_prev[:20]}..."
            )

        # Ricalcola hash dell'evento (escluso hash_self)
        event_copy = {k: v for k, v in event.items() if k != "hash_self"}
        event_json = json.dumps(event_copy, sort_keys=True, default=str)
        computed_hash = f"sha256:{hashlib.sha256(event_json.encode()).hexdigest()}"

        # Verifica hash_self
        stored_hash = event.get("hash_self", "")
        if stored_hash and stored_hash != computed_hash:
            return (
                False,
                line_num,
                f"Riga {line_num}: hash_self mismatch. "
                f"L'evento e stato modificato dopo la scrittura."
            )

        expected_prev = computed_hash

    return True, len(events), ""


def verify_and_report(audit_file: str) -> None:
    """Verifica e stampa report."""
    is_valid, count, error = verify_audit_chain(audit_file)

    if is_valid:
        print(f"PASS: {count} eventi verificati. Catena integra.")
    else:
        print(f"FAIL: catena rotta dopo {count} eventi.")
        print(f"Dettaglio: {error}")
        print("AZIONE RICHIESTA: indagare manomissione o corruzione dati.")


# Esecuzione scheduled (cron)
# 0 */6 * * * python -m audit_tools verify /var/log/audit/events.jsonl
```

### Verifica periodica automatizzata

```python
"""Script per verifica periodica integrita audit log.

Eseguire via cron o systemd timer:
    0 */4 * * * /usr/bin/python3 /opt/audit/verify_chain.py
"""

import sys
import json
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timezone


def main():
    audit_files = [
        "/var/log/audit/workflow-events.jsonl",
        "/var/log/audit/auth-events.jsonl",
        "/var/log/audit/data-access-events.jsonl",
    ]

    failures = []
    for path in audit_files:
        is_valid, count, error = verify_audit_chain(path)
        if not is_valid:
            failures.append({"file": path, "count": count, "error": error})

    if failures:
        alert_body = json.dumps({
            "alert": "AUDIT_CHAIN_INTEGRITY_FAILURE",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "failures": failures,
            "severity": "CRITICAL",
        }, indent=2)

        # Invio alert (esempio: email)
        send_alert_email(
            subject="[CRITICAL] Audit log integrity failure",
            body=alert_body,
        )

        # Log su stderr per journald/syslog
        print(alert_body, file=sys.stderr)
        sys.exit(1)

    print(f"OK: {len(audit_files)} file verificati, catena integra.")
    sys.exit(0)


def send_alert_email(subject: str, body: str) -> None:
    """Invio email alert via SMTP locale."""
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = "audit-monitor@internal.company.com"
    msg["To"] = "security-team@internal.company.com"

    with smtplib.SMTP("localhost", 25) as smtp:
        smtp.send_message(msg)
```

### Alternativa: Merkle tree per audit log

Per volumi molto alti (milioni di eventi/giorno), la hash chain lineare diventa lenta da verificare. Un Merkle tree permette verifiche parziali in O(log n).

```python
import hashlib
from typing import Optional


class MerkleNode:
    """Nodo di un Merkle tree per audit events."""

    def __init__(
        self,
        hash_value: str,
        left: Optional["MerkleNode"] = None,
        right: Optional["MerkleNode"] = None,
    ):
        self.hash_value = hash_value
        self.left = left
        self.right = right


def build_merkle_tree(event_hashes: list[str]) -> Optional[MerkleNode]:
    """Costruisce un Merkle tree da una lista di hash di eventi.

    Args:
        event_hashes: Lista di hash SHA-256 degli eventi.

    Returns:
        Nodo radice del Merkle tree. None se lista vuota.
    """
    if not event_hashes:
        return None

    # Foglie
    nodes = [MerkleNode(h) for h in event_hashes]

    # Padding se numero dispari
    while len(nodes) > 1:
        if len(nodes) % 2 == 1:
            nodes.append(nodes[-1])  # duplica ultimo

        next_level = []
        for i in range(0, len(nodes), 2):
            combined = nodes[i].hash_value + nodes[i + 1].hash_value
            parent_hash = hashlib.sha256(combined.encode()).hexdigest()
            next_level.append(MerkleNode(
                hash_value=parent_hash,
                left=nodes[i],
                right=nodes[i + 1],
            ))
        nodes = next_level

    return nodes[0]


def get_merkle_root(event_hashes: list[str]) -> str:
    """Ritorna il Merkle root hash. Utile per verifica rapida."""
    tree = build_merkle_tree(event_hashes)
    return tree.hash_value if tree else ""
```

---

## Append-only storage — PostgreSQL

### Schema tabella

```sql
-- Tabella audit events: append-only, niente UPDATE/DELETE
CREATE TABLE audit_events (
    id                BIGSERIAL PRIMARY KEY,
    event_id          TEXT NOT NULL UNIQUE,
    timestamp_utc     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    timestamp_ingested TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    version           TEXT NOT NULL DEFAULT '1.2.0',
    actor_type        TEXT NOT NULL,
    actor_id          TEXT NOT NULL,
    action            TEXT NOT NULL,
    action_category   TEXT NOT NULL,
    resource_type     TEXT NOT NULL,
    resource_id       TEXT NOT NULL,
    outcome           TEXT NOT NULL,
    outcome_reason    TEXT,
    trace_id          TEXT,
    span_id           TEXT,
    metadata_json     JSONB NOT NULL DEFAULT '{}',
    source_json       JSONB NOT NULL DEFAULT '{}',
    hash_prev         TEXT NOT NULL,
    hash_self         TEXT NOT NULL,
    -- Partizionamento per data (retention)
    created_date      DATE NOT NULL DEFAULT CURRENT_DATE
) PARTITION BY RANGE (created_date);

-- Partizioni mensili (automaticare con pg_partman)
CREATE TABLE audit_events_2026_01 PARTITION OF audit_events
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
CREATE TABLE audit_events_2026_02 PARTITION OF audit_events
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');
-- ... generare con pg_partman o script

-- Indici per query compliance
CREATE INDEX idx_audit_actor ON audit_events (actor_id, timestamp_utc);
CREATE INDEX idx_audit_action ON audit_events (action, timestamp_utc);
CREATE INDEX idx_audit_resource ON audit_events (resource_type, resource_id);
CREATE INDEX idx_audit_outcome ON audit_events (outcome, timestamp_utc);
CREATE INDEX idx_audit_trace ON audit_events (trace_id) WHERE trace_id IS NOT NULL;
CREATE INDEX idx_audit_data_subjects ON audit_events
    USING GIN ((metadata_json -> 'data_subjects'));
CREATE INDEX idx_audit_timestamp ON audit_events (timestamp_utc);

-- Full-text search sui metadata (per audit investigativo)
CREATE INDEX idx_audit_metadata_fts ON audit_events
    USING GIN (to_tsvector('simple', metadata_json::text));
```

### Protezione append-only con GRANT/REVOKE

```sql
-- Utente applicativo: solo INSERT + SELECT, mai UPDATE/DELETE
CREATE ROLE audit_writer LOGIN PASSWORD '***';
GRANT CONNECT ON DATABASE audit_db TO audit_writer;
GRANT USAGE ON SCHEMA public TO audit_writer;
GRANT INSERT, SELECT ON audit_events TO audit_writer;
GRANT USAGE, SELECT ON SEQUENCE audit_events_id_seq TO audit_writer;

-- ESPLICITAMENTE nega UPDATE e DELETE
REVOKE UPDATE, DELETE ON audit_events FROM audit_writer;

-- Utente per auditor: solo SELECT
CREATE ROLE audit_reader LOGIN PASSWORD '***';
GRANT CONNECT ON DATABASE audit_db TO audit_reader;
GRANT USAGE ON SCHEMA public TO audit_reader;
GRANT SELECT ON audit_events TO audit_reader;
REVOKE INSERT, UPDATE, DELETE ON audit_events FROM audit_reader;

-- Utente admin (solo per DBA, con MFA):
-- puo fare DROP PARTITION per retention, ma non DELETE singoli record
CREATE ROLE audit_admin LOGIN PASSWORD '***';
GRANT ALL ON audit_events TO audit_admin;
```

### Trigger anti-UPDATE/DELETE

```sql
-- Trigger che impedisce UPDATE e DELETE anche se i permessi fossero bypassati
CREATE OR REPLACE FUNCTION prevent_audit_mutation()
RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'Audit events are immutable. Operation % denied.', TG_OP;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_audit_no_update
    BEFORE UPDATE ON audit_events
    FOR EACH ROW
    EXECUTE FUNCTION prevent_audit_mutation();

CREATE TRIGGER trg_audit_no_delete
    BEFORE DELETE ON audit_events
    FOR EACH ROW
    EXECUTE FUNCTION prevent_audit_mutation();
```

### Retention con partizionamento

```sql
-- Funzione per creare partizioni future automaticamente
CREATE OR REPLACE FUNCTION create_future_partitions(months_ahead INT DEFAULT 3)
RETURNS void AS $$
DECLARE
    start_date DATE;
    end_date DATE;
    partition_name TEXT;
BEGIN
    FOR i IN 0..months_ahead LOOP
        start_date := date_trunc('month', CURRENT_DATE + (i || ' months')::interval);
        end_date := start_date + '1 month'::interval;
        partition_name := 'audit_events_' || to_char(start_date, 'YYYY_MM');

        BEGIN
            EXECUTE format(
                'CREATE TABLE IF NOT EXISTS %I PARTITION OF audit_events
                 FOR VALUES FROM (%L) TO (%L)',
                partition_name, start_date, end_date
            );
            RAISE NOTICE 'Created partition: %', partition_name;
        EXCEPTION WHEN duplicate_table THEN
            -- Partizione esiste gia
            NULL;
        END;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Funzione per drop partizioni scadute (retention)
CREATE OR REPLACE FUNCTION drop_expired_partitions(retention_months INT)
RETURNS TABLE(partition_dropped TEXT, rows_before BIGINT) AS $$
DECLARE
    cutoff_date DATE;
    rec RECORD;
BEGIN
    cutoff_date := CURRENT_DATE - (retention_months || ' months')::interval;

    FOR rec IN
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public'
          AND tablename LIKE 'audit_events_%'
        ORDER BY tablename
    LOOP
        -- Estrai data dalla partizione
        DECLARE
            partition_date DATE;
            row_count BIGINT;
        BEGIN
            partition_date := to_date(
                replace(rec.tablename, 'audit_events_', ''),
                'YYYY_MM'
            );

            IF partition_date < cutoff_date THEN
                EXECUTE format('SELECT count(*) FROM %I', rec.tablename) INTO row_count;

                -- Log prima del drop (audit dell'audit)
                RAISE NOTICE 'Dropping partition % (% rows, before cutoff %)',
                    rec.tablename, row_count, cutoff_date;

                EXECUTE format('DROP TABLE %I', rec.tablename);

                partition_dropped := rec.tablename;
                rows_before := row_count;
                RETURN NEXT;
            END IF;
        EXCEPTION WHEN OTHERS THEN
            RAISE WARNING 'Cannot parse partition date from %: %',
                rec.tablename, SQLERRM;
        END;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Cron: retention GDPR (60 mesi) e SOX (84 mesi)
-- Usare pg_cron o crontab esterno
-- SELECT drop_expired_partitions(60);  -- GDPR
-- SELECT drop_expired_partitions(84);  -- SOX
```

---

## Append-only storage — Elasticsearch / OpenSearch

### Index template per audit events

```json
{
  "index_patterns": ["audit-events-*"],
  "template": {
    "settings": {
      "number_of_shards": 2,
      "number_of_replicas": 1,
      "index.lifecycle.name": "audit-retention-policy",
      "index.lifecycle.rollover_alias": "audit-events",
      "index.blocks.read_only_allow_delete": false
    },
    "mappings": {
      "dynamic": "strict",
      "properties": {
        "event_id": { "type": "keyword" },
        "timestamp": { "type": "date", "format": "strict_date_optional_time" },
        "timestamp_ingested": { "type": "date" },
        "version": { "type": "keyword" },
        "trace_id": { "type": "keyword" },
        "span_id": { "type": "keyword" },
        "actor": {
          "properties": {
            "type": { "type": "keyword" },
            "id": { "type": "keyword" },
            "email_hash": { "type": "keyword" },
            "ip": { "type": "ip" },
            "user_agent": { "type": "text", "fields": { "raw": { "type": "keyword" }}},
            "auth_method": { "type": "keyword" },
            "session_id": { "type": "keyword" }
          }
        },
        "action": { "type": "keyword" },
        "action_category": { "type": "keyword" },
        "resource": {
          "properties": {
            "type": { "type": "keyword" },
            "id": { "type": "keyword" },
            "name": { "type": "text", "fields": { "raw": { "type": "keyword" }}},
            "version": { "type": "keyword" },
            "environment": { "type": "keyword" }
          }
        },
        "outcome": { "type": "keyword" },
        "outcome_reason": { "type": "text" },
        "metadata": {
          "properties": {
            "input_hash": { "type": "keyword" },
            "output_hash": { "type": "keyword" },
            "records_processed": { "type": "integer" },
            "duration_ms": { "type": "integer" },
            "data_subjects": { "type": "keyword" },
            "data_categories": { "type": "keyword" },
            "legal_basis": { "type": "keyword" },
            "workflow_run_id": { "type": "keyword" },
            "trigger_type": { "type": "keyword" }
          }
        },
        "source": {
          "properties": {
            "service": { "type": "keyword" },
            "version": { "type": "keyword" },
            "host": { "type": "keyword" },
            "commit_sha": { "type": "keyword" }
          }
        },
        "hash_prev": { "type": "keyword" },
        "hash_self": { "type": "keyword" }
      }
    }
  }
}
```

### ILM (Index Lifecycle Management) per retention

```json
{
  "policy": {
    "phases": {
      "hot": {
        "min_age": "0ms",
        "actions": {
          "rollover": {
            "max_age": "30d",
            "max_primary_shard_size": "50gb"
          },
          "set_priority": { "priority": 100 }
        }
      },
      "warm": {
        "min_age": "90d",
        "actions": {
          "shrink": { "number_of_shards": 1 },
          "forcemerge": { "max_num_segments": 1 },
          "set_priority": { "priority": 50 },
          "allocate": {
            "number_of_replicas": 1,
            "require": { "data": "warm" }
          }
        }
      },
      "cold": {
        "min_age": "365d",
        "actions": {
          "set_priority": { "priority": 0 },
          "allocate": {
            "number_of_replicas": 0,
            "require": { "data": "cold" }
          },
          "searchable_snapshot": {
            "snapshot_repository": "audit-snapshots"
          }
        }
      },
      "delete": {
        "min_age": "2555d",
        "actions": {
          "delete": {}
        }
      }
    }
  }
}
```

Nota: `2555d` = 7 anni (SOX). Adattare per il regolamento applicabile.

### Protezione anti-delete su Elasticsearch

```bash
# Blocca eliminazione di documenti sugli indici audit
# (richiede X-Pack security o OpenSearch security plugin)

# Role che puo solo leggere e indicizzare, non cancellare
PUT /_security/role/audit_writer
{
  "indices": [
    {
      "names": ["audit-events-*"],
      "privileges": ["create_index", "create", "index", "read"],
      "field_security": { "grant": ["*"] }
    }
  ]
}

# Role per auditor: solo lettura
PUT /_security/role/audit_reader
{
  "indices": [
    {
      "names": ["audit-events-*"],
      "privileges": ["read"],
      "field_security": { "grant": ["*"] }
    }
  ]
}
```

---

## Retention policy per regolamento

### Implementazione retention multi-regolamento

```python
"""
Gestore retention per audit log con supporto multi-regolamento.

Ogni tenant/progetto puo avere regolamenti diversi applicabili.
La retention effettiva e il MAX tra tutti i regolamenti applicabili.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum


class Regulation(str, Enum):
    GDPR = "gdpr"
    SOX = "sox"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"
    AGID = "agid"
    NIS2 = "nis2"


@dataclass
class RetentionPolicy:
    """Policy di retention per un regolamento."""
    regulation: Regulation
    total_months: int       # Mesi totali di retention
    hot_months: int         # Mesi in storage hot (query rapida)
    warm_months: int        # Mesi in storage warm (query lenta)
    cold_months: int        # Mesi in storage cold/archive
    notes: str = ""


# Policies predefinite per regolamento
DEFAULT_POLICIES: dict[Regulation, RetentionPolicy] = {
    Regulation.GDPR: RetentionPolicy(
        regulation=Regulation.GDPR,
        total_months=60,   # 5 anni
        hot_months=12,
        warm_months=24,
        cold_months=24,
        notes="Variabile per scopo specifico del trattamento",
    ),
    Regulation.SOX: RetentionPolicy(
        regulation=Regulation.SOX,
        total_months=84,   # 7 anni
        hot_months=24,
        warm_months=36,
        cold_months=24,
        notes="Audit finanziario obbligatorio",
    ),
    Regulation.HIPAA: RetentionPolicy(
        regulation=Regulation.HIPAA,
        total_months=72,   # 6 anni
        hot_months=12,
        warm_months=36,
        cold_months=24,
        notes="Dalla creazione o ultimo uso del record",
    ),
    Regulation.PCI_DSS: RetentionPolicy(
        regulation=Regulation.PCI_DSS,
        total_months=12,   # 1 anno
        hot_months=3,      # 3 mesi online obbligatori
        warm_months=9,
        cold_months=0,
        notes="3 mesi hot obbligatori per PCI-DSS 10.7",
    ),
    Regulation.AGID: RetentionPolicy(
        regulation=Regulation.AGID,
        total_months=120,  # 10 anni
        hot_months=24,
        warm_months=48,
        cold_months=48,
        notes="Conservazione digitale ex CAD Art. 43-44",
    ),
    Regulation.NIS2: RetentionPolicy(
        regulation=Regulation.NIS2,
        total_months=60,   # 5 anni (best practice)
        hot_months=24,
        warm_months=36,
        cold_months=0,
        notes="Non specificato; seguire regolamento settoriale",
    ),
}


def compute_effective_retention(
    applicable_regulations: list[Regulation],
) -> RetentionPolicy:
    """Calcola la retention effettiva come MAX di tutti i regolamenti applicabili.

    Args:
        applicable_regulations: Lista di regolamenti applicabili.

    Returns:
        RetentionPolicy con i valori massimi tra tutti i regolamenti.
    """
    if not applicable_regulations:
        raise ValueError("Almeno un regolamento deve essere specificato")

    policies = [DEFAULT_POLICIES[r] for r in applicable_regulations]

    return RetentionPolicy(
        regulation=Regulation.GDPR,  # placeholder
        total_months=max(p.total_months for p in policies),
        hot_months=max(p.hot_months for p in policies),
        warm_months=max(p.warm_months for p in policies),
        cold_months=max(p.cold_months for p in policies),
        notes=f"Effective retention from: {', '.join(r.value for r in applicable_regulations)}",
    )


def get_retention_cutoff(
    policy: RetentionPolicy,
    tier: str = "total",
) -> datetime:
    """Calcola la data di cutoff per un tier di storage.

    Args:
        policy: Policy di retention.
        tier: "hot", "warm", "cold", "total"

    Returns:
        datetime: Date prima della quale i dati possono essere migrati/cancellati.
    """
    now = datetime.now(timezone.utc)
    months = {
        "hot": policy.hot_months,
        "warm": policy.hot_months + policy.warm_months,
        "cold": policy.hot_months + policy.warm_months + policy.cold_months,
        "total": policy.total_months,
    }
    return now - timedelta(days=months[tier] * 30)


# Esempio:
# Azienda italiana che processa dati sanitari e finanziari
# Applicabili: GDPR + HIPAA + SOX + AGID
effective = compute_effective_retention([
    Regulation.GDPR,
    Regulation.HIPAA,
    Regulation.SOX,
    Regulation.AGID,
])
# effective.total_months = 120 (AGID domina con 10 anni)
# effective.hot_months = 24 (SOX/AGID dominano)
```

---

## GDPR e right to be forgotten — pseudonimizzazione

### Il conflitto

Il GDPR Art. 17 da al data subject il diritto alla cancellazione dei propri dati personali. Ma l'audit log deve essere immutabile per compliance (Art. 5(2) accountability). Come risolvere?

**Soluzione: pseudonimizzazione all'ingresso.** I dati personali non entrano mai nell'audit log in chiaro. Entrano come pseudonimi (hash con salt) o riferimenti a un registro pseudonimi separato.

### Architettura pseudonimizzazione

```
                    ┌──────────────────┐
                    │  Pseudonym Store  │
                    │  (encrypted DB)   │
                    │                   │
                    │ user-123 → psn_a1 │
                    │ user-456 → psn_b2 │
                    └────────┬─────────┘
                             │ lookup
                             │
┌──────────┐    ┌────────────▼───────────┐    ┌──────────────┐
│ Workflow  │───▶│  Audit Logger          │───▶│ Audit Store  │
│ Engine    │    │  (pseudonimizza prima  │    │ (immutabile) │
│           │    │   di scrivere)         │    │              │
└──────────┘    └────────────────────────┘    │ actor.id =   │
                                               │  "psn_a1"    │
                                               │ (no PII)     │
                                               └──────────────┘
```

Quando il data subject esercita il diritto all'oblio:
1. Si cancella la mappatura `user-123 → psn_a1` dal Pseudonym Store.
2. L'audit log resta intatto (immutabile), ma `psn_a1` non e piu riconducibile a nessuna persona.
3. La hash chain resta valida.

### Implementazione

```python
"""
Pseudonym store per GDPR Art. 17 compatibility.

Il pseudonym store e un database separato, criptato,
con accesso ristretto. La cancellazione del mapping
rende l'audit log non riconducibile al data subject.
"""

import hashlib
import secrets
import json
from datetime import datetime, timezone


class PseudonymStore:
    """Gestisce mapping tra identita reale e pseudonimo.

    Il database sottostante DEVE essere criptato at rest.
    L'accesso DEVE essere limitato a ruoli DPO/privacy.
    """

    def __init__(self, db_connection):
        self._db = db_connection

    def get_or_create_pseudonym(self, real_id: str, id_type: str = "user") -> str:
        """Ritorna il pseudonimo per un ID reale, creandolo se necessario.

        Args:
            real_id: Identificativo reale (email, user_id, ecc.)
            id_type: Tipo di identificativo.

        Returns:
            Pseudonimo stabile (stesso input = stesso output).
        """
        cursor = self._db.cursor()
        cursor.execute(
            "SELECT pseudonym FROM pseudonym_mappings "
            "WHERE real_id = %s AND id_type = %s",
            (real_id, id_type),
        )
        row = cursor.fetchone()
        if row:
            return row[0]

        # Genera nuovo pseudonimo
        pseudonym = f"psn_{secrets.token_hex(12)}"

        cursor.execute(
            "INSERT INTO pseudonym_mappings "
            "(real_id, id_type, pseudonym, created_at) "
            "VALUES (%s, %s, %s, %s)",
            (real_id, id_type, pseudonym, datetime.now(timezone.utc)),
        )
        self._db.commit()
        return pseudonym

    def resolve_pseudonym(self, pseudonym: str) -> dict | None:
        """Risolve un pseudonimo all'identita reale.

        Accesso ristretto: solo DPO/privacy officer.
        Ogni risoluzione e loggata nell'audit log.
        """
        cursor = self._db.cursor()
        cursor.execute(
            "SELECT real_id, id_type FROM pseudonym_mappings "
            "WHERE pseudonym = %s",
            (pseudonym,),
        )
        row = cursor.fetchone()
        if row:
            return {"real_id": row[0], "id_type": row[1]}
        return None

    def forget(self, real_id: str) -> int:
        """Implementa Right to be Forgotten (GDPR Art. 17).

        Cancella TUTTE le mappature per un dato real_id.
        Dopo questa operazione, gli audit log con i pseudonimi
        corrispondenti non sono piu riconducibili alla persona.

        Returns:
            Numero di mappature cancellate.
        """
        cursor = self._db.cursor()

        # Prima, logga la richiesta di oblio (meta-audit)
        cursor.execute(
            "INSERT INTO forget_requests "
            "(real_id_hash, requested_at, completed_at) "
            "VALUES (%s, %s, %s)",
            (
                hashlib.sha256(real_id.encode()).hexdigest(),
                datetime.now(timezone.utc),
                datetime.now(timezone.utc),
            ),
        )

        # Poi, cancella le mappature
        cursor.execute(
            "DELETE FROM pseudonym_mappings WHERE real_id = %s",
            (real_id,),
        )
        deleted = cursor.rowcount
        self._db.commit()

        return deleted

    def list_pseudonyms_for_subject(self, real_id: str) -> list[str]:
        """Lista tutti i pseudonimi di un data subject.

        Usato per GDPR Art. 15 (diritto di accesso):
        con i pseudonimi, si possono cercare tutti gli audit events
        relativi al data subject.
        """
        cursor = self._db.cursor()
        cursor.execute(
            "SELECT pseudonym FROM pseudonym_mappings WHERE real_id = %s",
            (real_id,),
        )
        return [row[0] for row in cursor.fetchall()]
```

### Schema tabelle pseudonym store

```sql
-- Database SEPARATO, criptato at rest, accesso ristretto
CREATE DATABASE pseudonym_store;

-- Mappatura identita → pseudonimo
CREATE TABLE pseudonym_mappings (
    id          BIGSERIAL PRIMARY KEY,
    real_id     TEXT NOT NULL,
    id_type     TEXT NOT NULL DEFAULT 'user',
    pseudonym   TEXT NOT NULL UNIQUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (real_id, id_type)
);

-- Indice per lookup rapido
CREATE INDEX idx_psn_real ON pseudonym_mappings (real_id);
CREATE INDEX idx_psn_pseudo ON pseudonym_mappings (pseudonym);

-- Registro richieste di oblio (non cancellabile)
CREATE TABLE forget_requests (
    id              BIGSERIAL PRIMARY KEY,
    real_id_hash    TEXT NOT NULL,  -- hash, non il real_id
    requested_at    TIMESTAMPTZ NOT NULL,
    completed_at    TIMESTAMPTZ,
    status          TEXT DEFAULT 'completed'
);

-- Accesso: solo DPO / privacy officer
GRANT SELECT, INSERT, UPDATE, DELETE ON pseudonym_mappings TO privacy_officer;
GRANT SELECT, INSERT ON forget_requests TO privacy_officer;
REVOKE ALL ON pseudonym_mappings FROM audit_writer;
REVOKE ALL ON forget_requests FROM audit_writer;
```

---

## SIEM forward — architettura e configurazione

### Perche SIEM forward e mandatory

I log locali sono il primo target di un attaccante. Dopo aver compromesso un sistema, l'attaccante cancella o modifica i log locali per coprire le tracce. Il SIEM forward invia i log a un sistema centralizzato immediatamente, prima che l'attaccante possa intervenire.

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Workflow A   │    │  Workflow B   │    │  Workflow C   │
│  audit log    │    │  audit log    │    │  audit log    │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                    │                    │
       └────────────────────┼────────────────────┘
                            │ Syslog/HTTPS/Kafka
                    ┌───────▼──────────┐
                    │     SIEM          │
                    │  (Wazuh/Splunk/   │
                    │   Elastic SIEM/   │
                    │   Microsoft       │
                    │   Sentinel)       │
                    │                   │
                    │  - Correlazione   │
                    │  - Alerting       │
                    │  - Threat detect  │
                    │  - Compliance     │
                    │    reporting      │
                    └──────────────────┘
```

### Forward via rsyslog

```bash
# /etc/rsyslog.d/60-audit-forward.conf

# Carica modulo output TCP/TLS
module(load="omfwd")

# Template JSON per audit events
template(name="AuditJsonTemplate" type="string"
    string="%msg%\n")

# Forward audit log al SIEM
if $programname == 'audit-workflow' then {
    action(
        type="omfwd"
        target="siem.internal.company.com"
        port="1514"
        protocol="tcp"
        template="AuditJsonTemplate"
        queue.type="LinkedList"
        queue.filename="audit_fwd_queue"
        queue.maxDiskSpace="1g"
        queue.saveOnShutdown="on"
        action.resumeRetryCount="-1"
        action.resumeInterval="30"
    )
}
```

### Forward via Fluentd/Fluent Bit

```yaml
# fluent-bit.conf per forward audit log
[SERVICE]
    Flush         5
    Daemon        Off
    Log_Level     info
    Parsers_File  parsers.conf

[INPUT]
    Name          tail
    Path          /var/log/audit/workflow-events.jsonl
    Parser        json
    Tag           audit.workflow
    DB            /var/lib/fluent-bit/audit-tail.db
    Read_from_Head True
    Refresh_Interval 5

[FILTER]
    Name          modify
    Match         audit.*
    Add           cluster production-eu
    Add           source fluent-bit

[OUTPUT]
    Name          forward
    Match         audit.*
    Host          siem.internal.company.com
    Port          24224
    tls           On
    tls.verify    On
    tls.ca_file   /etc/fluent-bit/ca.pem
    Retry_Limit   False

[OUTPUT]
    Name          es
    Match         audit.*
    Host          elasticsearch.internal.company.com
    Port          9200
    Index         audit-events
    Type          _doc
    tls           On
    HTTP_User     audit_writer
    HTTP_Passwd   ${ELASTIC_PASSWORD}
    Logstash_Format On
    Logstash_Prefix audit-events
    Retry_Limit   False
```

### Forward via OTel Collector

Se gia usi OTel Collector (vedi Modulo 23), puoi usarlo anche per audit log forwarding:

```yaml
# otel-collector per audit log forward
receivers:
  filelog:
    include: ["/var/log/audit/workflow-events.jsonl"]
    operators:
      - type: json_parser
        timestamp:
          parse_from: attributes.timestamp
          layout: "%Y-%m-%dT%H:%M:%S.%LZ"

processors:
  attributes/audit:
    actions:
      - key: log.type
        value: audit_event
        action: upsert
      - key: compliance.required
        value: "true"
        action: upsert

exporters:
  # SIEM
  syslog:
    endpoint: "siem.internal.company.com:1514"
    protocol: rfc5424
    tls:
      cert_file: /etc/otel/client.pem
      key_file: /etc/otel/client-key.pem

  # Backup su object storage
  file:
    path: /mnt/audit-backup/events.jsonl
    rotation:
      max_megabytes: 100
      max_days: 2555  # 7 anni SOX

service:
  pipelines:
    logs/audit:
      receivers: [filelog]
      processors: [attributes/audit]
      exporters: [syslog, file]
```

---

## Wazuh — configurazione completa per audit workflow

### Architettura Wazuh per audit

```
┌──────────────────────────────────────────────┐
│                Wazuh Server                    │
│  ┌─────────────┐  ┌──────────────────────┐   │
│  │ wazuh-manager│  │ wazuh-indexer        │   │
│  │  (analysis)  │  │ (OpenSearch-based)   │   │
│  └──────┬──────┘  └──────────┬───────────┘   │
│         │                     │               │
│  ┌──────▼──────────────────────▼──────────┐   │
│  │           Wazuh Dashboard               │   │
│  │  (Kibana-based, compliance reports)     │   │
│  └────────────────────────────────────────┘   │
└──────────────────────────────────────────────┘
         ▲              ▲              ▲
         │              │              │
    ┌────┴───┐    ┌────┴───┐    ┌────┴───┐
    │ Agent  │    │ Agent  │    │ Agent  │
    │ Node A │    │ Node B │    │ Node C │
    └────────┘    └────────┘    └────────┘
```

### Decoder custom per audit events

```xml
<!-- /var/ossec/etc/decoders/audit-workflow-decoder.xml -->
<decoder name="audit-workflow">
  <prematch>^{"event_id":"evt_</prematch>
  <plugin_decoder>JSON_Decoder</plugin_decoder>
</decoder>
```

### Regole custom per workflow audit

```xml
<!-- /var/ossec/etc/rules/audit-workflow-rules.xml -->
<group name="audit,workflow,">

  <!-- Base rule: ogni audit event -->
  <rule id="100100" level="3">
    <decoded_as>audit-workflow</decoded_as>
    <description>Workflow audit event: $(action)</description>
  </rule>

  <!-- Workflow fallito -->
  <rule id="100101" level="7">
    <if_sid>100100</if_sid>
    <field name="outcome">failure</field>
    <description>Workflow execution FAILED: $(resource.id)</description>
    <group>workflow_failure,</group>
  </rule>

  <!-- Accesso negato -->
  <rule id="100102" level="10">
    <if_sid>100100</if_sid>
    <field name="outcome">denied</field>
    <description>Workflow access DENIED for $(actor.id) on $(resource.id)</description>
    <group>authorization_failure,</group>
  </rule>

  <!-- Cancellazione dati (potenziale data breach) -->
  <rule id="100103" level="12">
    <if_sid>100100</if_sid>
    <field name="action">data.delete</field>
    <description>DATA DELETION by $(actor.id) on $(resource.type)/$(resource.id)</description>
    <group>data_deletion,gdpr,</group>
  </rule>

  <!-- Esportazione dati (potenziale data exfiltration) -->
  <rule id="100104" level="10">
    <if_sid>100100</if_sid>
    <field name="action">data.export</field>
    <description>DATA EXPORT by $(actor.id): $(resource.type)/$(resource.id)</description>
    <group>data_export,gdpr,</group>
  </rule>

  <!-- Modifica configurazione workflow -->
  <rule id="100105" level="7">
    <if_sid>100100</if_sid>
    <field name="action_category">configuration_change</field>
    <description>Configuration change by $(actor.id): $(action) on $(resource.id)</description>
    <group>config_change,</group>
  </rule>

  <!-- Multipli fallimenti in poco tempo (correlazione) -->
  <rule id="100110" level="12" frequency="5" timeframe="300">
    <if_matched_sid>100101</if_matched_sid>
    <same_field>resource.id</same_field>
    <description>REPEATED workflow failures: $(resource.id) - 5+ in 5 min</description>
    <group>workflow_instability,</group>
  </rule>

  <!-- Login falliti multipli (brute force) -->
  <rule id="100111" level="14" frequency="10" timeframe="60">
    <if_matched_sid>100102</if_matched_sid>
    <same_field>actor.ip</same_field>
    <description>BRUTE FORCE suspected from $(actor.ip): 10+ denied in 1 min</description>
    <group>brute_force,authentication,</group>
  </rule>

  <!-- Esportazione massiva (data exfiltration) -->
  <rule id="100112" level="14" frequency="20" timeframe="3600">
    <if_matched_sid>100104</if_matched_sid>
    <same_field>actor.id</same_field>
    <description>MASS DATA EXPORT by $(actor.id): 20+ exports in 1 hour</description>
    <group>data_exfiltration,incident,</group>
  </rule>

  <!-- Hash chain integrity failure -->
  <rule id="100120" level="15">
    <decoded_as>audit-workflow</decoded_as>
    <match>AUDIT_CHAIN_INTEGRITY_FAILURE</match>
    <description>CRITICAL: Audit log integrity compromised - hash chain broken</description>
    <group>integrity_failure,incident,</group>
  </rule>

</group>
```

### Configurazione agent Wazuh

```xml
<!-- /var/ossec/etc/ossec.conf (agent) -->
<ossec_config>
  <localfile>
    <log_format>json</log_format>
    <location>/var/log/audit/workflow-events.jsonl</location>
    <label key="log.type">audit_workflow</label>
  </localfile>

  <localfile>
    <log_format>json</log_format>
    <location>/var/log/audit/auth-events.jsonl</location>
    <label key="log.type">audit_auth</label>
  </localfile>
</ossec_config>
```

---

## Integrazione con orchestratori di workflow

### n8n — audit via webhook node

n8n non ha audit logging nativo strutturato. L'approccio e intercettare gli eventi tramite webhook o workflow dedicato.

```json
{
  "name": "Audit Logger Workflow",
  "nodes": [
    {
      "name": "Webhook Trigger",
      "type": "n8n-nodes-base.webhook",
      "parameters": {
        "path": "/audit/event",
        "httpMethod": "POST",
        "authentication": "headerAuth"
      }
    },
    {
      "name": "Validate Schema",
      "type": "n8n-nodes-base.code",
      "parameters": {
        "jsCode": "const event = $input.first().json;\nconst required = ['event_id','timestamp','actor','action','resource','outcome'];\nfor (const field of required) {\n  if (!event[field]) throw new Error(`Missing field: ${field}`);\n}\nreturn [{json: event}];"
      }
    },
    {
      "name": "Write to PostgreSQL",
      "type": "n8n-nodes-base.postgres",
      "parameters": {
        "operation": "insert",
        "table": "audit_events",
        "columns": "event_id, timestamp_utc, actor_type, actor_id, action, resource_type, resource_id, outcome, metadata_json, hash_prev, hash_self"
      }
    },
    {
      "name": "Forward to SIEM",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "POST",
        "url": "https://siem.internal/api/events",
        "sendBody": true,
        "bodyParameters": {
          "parameters": [
            { "name": "event", "value": "={{ JSON.stringify($json) }}" }
          ]
        }
      }
    }
  ]
}
```

### Temporal — interceptor per audit automatico

```python
from temporalio.client import Client, Interceptor
from temporalio.worker import Worker
from temporalio import workflow, activity

class AuditInterceptor(Interceptor):
    """Interceptor Temporal che genera audit events per ogni operazione."""

    def __init__(self, audit_logger: AuditLogger):
        self._audit = audit_logger

    def intercept_activity(self, next, info):
        """Wrappa ogni activity con audit logging."""
        actor = Actor(
            type=ActorType.SYSTEM,
            id=f"temporal-worker-{info.worker_id}",
            auth_method="internal",
        )
        resource = Resource(
            type="temporal_activity",
            id=info.activity_type,
            environment=get_environment(),
        )

        # Log inizio
        self._audit.log(
            actor=actor,
            action="workflow.execute",
            action_category=ActionCategory.WORKFLOW_MANAGEMENT,
            resource=resource,
            outcome=Outcome.SUCCESS,
            metadata={
                "workflow_id": info.workflow_id,
                "workflow_run_id": info.workflow_run_id,
                "activity_id": info.activity_id,
                "attempt": info.attempt,
            },
        )

        try:
            result = next(info)
            return result
        except Exception as e:
            self._audit.log(
                actor=actor,
                action="workflow.execute",
                action_category=ActionCategory.WORKFLOW_MANAGEMENT,
                resource=resource,
                outcome=Outcome.FAILURE,
                outcome_reason=str(e),
            )
            raise
```

### Apache Airflow — callback per audit

```python
from airflow import DAG
from airflow.models import TaskInstance
from datetime import datetime


def audit_on_success(context):
    """Callback Airflow: logga successo nel sistema di audit."""
    ti: TaskInstance = context["task_instance"]
    audit.log(
        actor=Actor(type=ActorType.SYSTEM, id="airflow-scheduler"),
        action="workflow.execute",
        action_category=ActionCategory.WORKFLOW_MANAGEMENT,
        resource=Resource(
            type="airflow_task",
            id=f"{ti.dag_id}.{ti.task_id}",
            version=str(context.get("dag_run").run_id),
            environment=get_environment(),
        ),
        outcome=Outcome.SUCCESS,
        metadata={
            "execution_date": str(context["execution_date"]),
            "duration_seconds": ti.duration,
            "try_number": ti.try_number,
        },
    )


def audit_on_failure(context):
    """Callback Airflow: logga fallimento."""
    ti: TaskInstance = context["task_instance"]
    audit.log(
        actor=Actor(type=ActorType.SYSTEM, id="airflow-scheduler"),
        action="workflow.execute",
        action_category=ActionCategory.WORKFLOW_MANAGEMENT,
        resource=Resource(
            type="airflow_task",
            id=f"{ti.dag_id}.{ti.task_id}",
            environment=get_environment(),
        ),
        outcome=Outcome.FAILURE,
        outcome_reason=str(context.get("exception", "Unknown error")),
        metadata={
            "execution_date": str(context["execution_date"]),
            "try_number": ti.try_number,
        },
    )


# Applicazione globale a tutti i DAG
default_args = {
    "on_success_callback": audit_on_success,
    "on_failure_callback": audit_on_failure,
}
```

---

## Data lineage e audit trail per ETL

### Il problema

L'audit log dice chi ha fatto cosa e quando. Il data lineage dice da dove vengono i dati e dove vanno. Per compliance piena (specialmente GDPR Art. 30 e SOX), servono entrambi.

### Schema data lineage event

```python
@dataclass(frozen=True)
class LineageEvent:
    """Evento di data lineage per workflow ETL."""
    lineage_id: str
    timestamp: str
    workflow_run_id: str
    step_name: str
    operation: str  # "read", "transform", "write", "delete"
    source: dict    # {"type": "postgres", "database": "orders", "table": "orders"}
    destination: dict  # {"type": "s3", "bucket": "data-lake", "path": "..."}
    record_count: int
    schema_hash: str  # hash dello schema dei dati
    transformation: str  # descrizione della trasformazione
    data_categories: list[str]  # ["personal_data", "financial_data"]
    data_subjects_count: int  # quanti data subject coinvolti
    legal_basis: str


def emit_lineage_event(
    workflow_run_id: str,
    step_name: str,
    operation: str,
    source: dict,
    destination: dict,
    record_count: int,
    data_categories: list[str],
) -> None:
    """Emetti evento di lineage nell'audit log."""
    audit.log(
        actor=Actor(type=ActorType.SYSTEM, id="etl-engine"),
        action=f"data.{operation}",
        action_category=ActionCategory.DATA_MODIFICATION,
        resource=Resource(
            type="data_pipeline",
            id=f"{workflow_run_id}/{step_name}",
            environment=get_environment(),
        ),
        outcome=Outcome.SUCCESS,
        metadata={
            "lineage": {
                "source": source,
                "destination": destination,
                "record_count": record_count,
                "data_categories": data_categories,
                "operation": operation,
            }
        },
    )
```

---

## Access control sugli audit log

### Principio: separation of duty

| Ruolo | Puo leggere audit | Puo scrivere audit | Puo cancellare audit |
|---|---|---|---|
| Applicazione (workflow) | No | Si (solo INSERT) | No |
| SRE / Ops | Si (query) | No | No |
| Auditor esterno | Si (query + export) | No | No |
| DPO / Privacy officer | Si (con pseudonimi risolti) | No | No (solo forget su pseudonym store) |
| DBA | Si | No | Si (solo DROP PARTITION per retention, con approvazione) |
| Security team | Si (via SIEM) | No | No |

### Implementazione RBAC

```python
from enum import Enum
from functools import wraps


class AuditPermission(str, Enum):
    READ = "audit:read"
    WRITE = "audit:write"
    EXPORT = "audit:export"
    RESOLVE_PSEUDONYM = "audit:resolve_pseudonym"
    DELETE_PARTITION = "audit:delete_partition"
    FORGET_SUBJECT = "audit:forget_subject"


ROLE_PERMISSIONS: dict[str, set[AuditPermission]] = {
    "audit_writer": {AuditPermission.WRITE},
    "sre": {AuditPermission.READ},
    "auditor": {AuditPermission.READ, AuditPermission.EXPORT},
    "dpo": {
        AuditPermission.READ,
        AuditPermission.EXPORT,
        AuditPermission.RESOLVE_PSEUDONYM,
        AuditPermission.FORGET_SUBJECT,
    },
    "dba": {AuditPermission.READ, AuditPermission.DELETE_PARTITION},
}


def require_permission(permission: AuditPermission):
    """Decoratore che verifica il permesso prima dell'operazione."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_user = get_current_user()
            user_role = current_user.role
            allowed = ROLE_PERMISSIONS.get(user_role, set())

            if permission not in allowed:
                # Log tentativo di accesso negato
                audit.log(
                    actor=Actor(
                        type=ActorType.USER,
                        id=current_user.id,
                        ip=current_user.ip,
                    ),
                    action="authz.denied",
                    action_category=ActionCategory.AUTHORIZATION,
                    resource=Resource(type="audit_system", id=func.__name__),
                    outcome=Outcome.DENIED,
                    outcome_reason=f"Missing permission: {permission.value}",
                )
                raise PermissionError(
                    f"Permission {permission.value} required. "
                    f"Role {user_role} does not have it."
                )

            return func(*args, **kwargs)
        return wrapper
    return decorator


# Esempio utilizzo
@require_permission(AuditPermission.EXPORT)
def export_audit_events(
    start_date: str, end_date: str, format: str = "csv"
) -> str:
    """Esporta audit events per auditor esterno."""
    # ... implementazione
    pass

@require_permission(AuditPermission.FORGET_SUBJECT)
def execute_forget_request(real_id: str) -> int:
    """Esegue richiesta di oblio. Solo DPO."""
    return pseudonym_store.forget(real_id)
```

---

## Monitoring e alerting sull'integrita degli audit log

### Metriche da monitorare

```python
from opentelemetry import metrics

meter = metrics.get_meter("audit.health")

# Volume di audit events
audit_events_total = meter.create_counter(
    "audit.events.total",
    description="Audit events scritti per tipo e outcome",
)

# Latenza di scrittura audit
audit_write_duration = meter.create_histogram(
    "audit.write.duration_seconds",
    description="Tempo di scrittura audit event",
)

# Errori di scrittura
audit_write_errors = meter.create_counter(
    "audit.write.errors.total",
    description="Errori di scrittura audit event",
)

# Buffer depth
audit_buffer_depth = meter.create_up_down_counter(
    "audit.buffer.depth",
    description="Elementi nel buffer di audit",
)

# Hash chain verification result
audit_chain_verified = meter.create_counter(
    "audit.chain.verification.total",
    description="Risultati verifica hash chain",
)
```

### Prometheus alerting rules per audit health

```yaml
# prometheus-rules/audit-health.yml
groups:
  - name: audit_health
    rules:
      # Nessun audit event da troppo tempo (sistema potenzialmente compromesso)
      - alert: AuditLogSilent
        expr: |
          rate(audit_events_total[5m]) == 0
          AND
          rate(workflow_executions_total[5m]) > 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Audit logging stopped while workflows are running"
          description: |
            Workflow sono in esecuzione ma nessun audit event registrato
            negli ultimi 5 minuti. Possibile compromissione del sistema
            di audit o errore di configurazione.

      # Errori di scrittura audit
      - alert: AuditWriteErrors
        expr: rate(audit_write_errors_total[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Audit log write errors detected"

      # Buffer audit pieno (rischio perdita eventi)
      - alert: AuditBufferFull
        expr: audit_buffer_depth > 500
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Audit buffer near capacity — events may be lost"

      # Hash chain verification failure
      - alert: AuditChainBroken
        expr: increase(audit_chain_verification_total{result="failure"}[1h]) > 0
        labels:
          severity: critical
        annotations:
          summary: "AUDIT LOG INTEGRITY COMPROMISED"
          description: |
            La verifica hash chain ha rilevato una discrepanza.
            Possibile manomissione degli audit log.
            AZIONE IMMEDIATA: isolare il sistema, preservare le evidence,
            avviare incident response.
```

---

## Architettura multi-tenant per audit

### Il problema

In un sistema multi-tenant (SaaS), ogni tenant deve vedere solo i propri audit log. I regolamenti applicabili possono variare per tenant (un tenant europeo ha GDPR, uno americano ha SOX/HIPAA).

### Approccio: tenant isolation via partizionamento

```sql
-- Partizionamento per tenant + data
CREATE TABLE audit_events_mt (
    id                BIGSERIAL,
    tenant_id         TEXT NOT NULL,
    event_id          TEXT NOT NULL,
    timestamp_utc     TIMESTAMPTZ NOT NULL,
    -- ... altri campi come sopra
    PRIMARY KEY (tenant_id, id)
) PARTITION BY LIST (tenant_id);

-- Partizione per tenant
CREATE TABLE audit_events_mt_tenant_acme
    PARTITION OF audit_events_mt FOR VALUES IN ('tenant-acme')
    PARTITION BY RANGE (timestamp_utc);

CREATE TABLE audit_events_mt_tenant_globex
    PARTITION OF audit_events_mt FOR VALUES IN ('tenant-globex')
    PARTITION BY RANGE (timestamp_utc);

-- Row Level Security per isolation
ALTER TABLE audit_events_mt ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON audit_events_mt
    USING (tenant_id = current_setting('app.current_tenant'));
```

### Configurazione retention per-tenant

```python
TENANT_REGULATIONS: dict[str, list[Regulation]] = {
    "tenant-acme": [Regulation.GDPR, Regulation.SOX],          # EU + financial
    "tenant-globex": [Regulation.HIPAA, Regulation.SOX],       # US healthcare + financial
    "tenant-initech": [Regulation.GDPR, Regulation.AGID],      # IT public sector
    "tenant-umbrella": [Regulation.PCI_DSS, Regulation.GDPR],  # EU e-commerce
}

def get_tenant_retention(tenant_id: str) -> RetentionPolicy:
    """Ritorna la retention effettiva per un tenant."""
    regulations = TENANT_REGULATIONS.get(tenant_id, [Regulation.GDPR])
    return compute_effective_retention(regulations)
```

---

## Esportazione e reportistica per auditor

### Formato export per auditor

```python
import csv
import io
from datetime import datetime, timezone


def export_audit_to_csv(
    events: list[dict],
    include_metadata: bool = True,
) -> str:
    """Esporta audit events in CSV per auditor esterno.

    Formato conforme a SOX Sec. 404 requirements.
    """
    output = io.StringIO()
    fieldnames = [
        "event_id", "timestamp", "actor_type", "actor_id",
        "action", "action_category", "resource_type", "resource_id",
        "outcome", "outcome_reason", "trace_id",
    ]
    if include_metadata:
        fieldnames.extend([
            "records_processed", "duration_ms",
            "data_categories", "legal_basis",
        ])

    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()

    for event in events:
        row = {
            "event_id": event["event_id"],
            "timestamp": event["timestamp"],
            "actor_type": event["actor"]["type"],
            "actor_id": event["actor"]["id"],
            "action": event["action"],
            "action_category": event.get("action_category", ""),
            "resource_type": event["resource"]["type"],
            "resource_id": event["resource"]["id"],
            "outcome": event["outcome"],
            "outcome_reason": event.get("outcome_reason", ""),
            "trace_id": event.get("trace_id", ""),
        }
        if include_metadata:
            meta = event.get("metadata", {})
            row["records_processed"] = meta.get("records_processed", "")
            row["duration_ms"] = meta.get("duration_ms", "")
            row["data_categories"] = ",".join(meta.get("data_categories", []))
            row["legal_basis"] = meta.get("legal_basis", "")

        writer.writerow(row)

    return output.getvalue()


def generate_compliance_report(
    start_date: datetime,
    end_date: datetime,
    regulation: str,
) -> dict:
    """Genera report compliance per un periodo e regolamento.

    Returns:
        Dict con statistiche e dettagli per l'auditor.
    """
    events = query_audit_events(start_date, end_date)

    report = {
        "report_id": f"rpt_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
        },
        "regulation": regulation,
        "statistics": {
            "total_events": len(events),
            "by_outcome": count_by_field(events, "outcome"),
            "by_action_category": count_by_field(events, "action_category"),
            "by_actor_type": count_by_field(events, lambda e: e["actor"]["type"]),
            "unique_actors": len(set(e["actor"]["id"] for e in events)),
            "unique_resources": len(set(e["resource"]["id"] for e in events)),
        },
        "security_events": {
            "access_denied": len([e for e in events if e["outcome"] == "denied"]),
            "data_deletions": len([e for e in events if e["action"] == "data.delete"]),
            "data_exports": len([e for e in events if e["action"] == "data.export"]),
            "config_changes": len([
                e for e in events
                if e.get("action_category") == "configuration_change"
            ]),
        },
        "chain_integrity": verify_audit_chain_for_period(start_date, end_date),
    }

    return report
```

---

## Anti-pattern e errori comuni

### 1. Log dati personali in chiaro nell'audit event

```python
# SBAGLIATO: PII in chiaro
audit.log(
    actor=Actor(type=ActorType.USER, id="mario.rossi@example.com"),
    # ...
)

# CORRETTO: pseudonimo
audit.log(
    actor=Actor(
        type=ActorType.USER,
        id=pseudonym_store.get_or_create_pseudonym("mario.rossi@example.com"),
        email_hash=hash_pii("mario.rossi@example.com", salt),
    ),
    # ...
)
```

### 2. Permettere UPDATE/DELETE sulla tabella audit

La tabella DEVE avere trigger anti-mutation e permessi REVOKE su UPDATE e DELETE.

### 3. Audit log sullo stesso volume del servizio

Se l'attaccante compromette il servizio, puo accedere ai log locali. Forward SIEM obbligatorio.

### 4. Non validare lo schema

Audit event malformati non sono utilizzabili in sede di audit. Validare SEMPRE contro JSON Schema prima della scrittura.

### 5. Retention uniforme per tutti i regolamenti

Ogni regolamento ha retention diversa. Usare il MAX tra tutti i regolamenti applicabili.

### 6. Hash chain senza verifica periodica

Costruire la hash chain e inutile se non la si verifica. Schedulare verifica ogni 4-6 ore.

### 7. Non loggare i fallimenti dell'audit system

Se l'audit logger fallisce, chi lo sa? Monitorare con metriche separate e alerting.

### 8. Clock skew tra nodi

NTP non sincronizzato = timestamp inaffidabili = ordine eventi ambiguo. Usare `chrony` o `systemd-timesyncd` su tutti i nodi.

### 9. Free-text nei log

```python
# SBAGLIATO
logger.info(f"User {email} executed workflow {name} at {time}")

# CORRETTO
audit.log(
    actor=Actor(type=ActorType.USER, id=pseudonym),
    action="workflow.execute",
    resource=Resource(type="workflow", id=name),
    outcome=Outcome.SUCCESS,
)
```

### 10. Ignorare l'audit dell'audit

Chi accede agli audit log? Chi esporta? Chi esegue il `forget`? Tutte queste operazioni devono essere auditate.

---

## Esercizi

### Esercizio 1 — Schema audit event (45 min)

**Obiettivo:** Definire un JSON Schema per il tuo dominio specifico e validarlo.

1. Scegli un dominio (e-commerce, healthcare, fintech, HR).
2. Definisci almeno 10 azioni specifiche del dominio (es. `order.create`, `patient.access`, `payment.process`).
3. Scrivi il JSON Schema con validazione `jsonschema`.
4. Crea 5 eventi validi e 3 invalidi; verifica che la validazione funzioni correttamente.
5. Aggiungi il campo `data_categories` con i valori appropriati per il dominio.

### Esercizio 2 — Hash chain con verifica (60 min)

**Obiettivo:** Implementare un append-only log con hash chain e verificarne l'integrita.

1. Implementa `AuditLogger` con `FileAuditBackend` e hash chain.
2. Scrivi 100 eventi di test.
3. Implementa `verify_audit_chain()`.
4. Verifica che la catena sia valida.
5. Modifica manualmente un evento nel file (simula tampering).
6. Riesegui la verifica: deve fallire e indicare l'evento modificato.
7. Bonus: implementa Merkle tree e confronta i tempi di verifica.

### Esercizio 3 — PostgreSQL append-only (60 min)

**Obiettivo:** Configurare PostgreSQL per audit append-only con RBAC.

1. Crea database `audit_db` con la tabella `audit_events`.
2. Crea ruoli `audit_writer`, `audit_reader`, `audit_admin`.
3. Configura GRANT/REVOKE appropriati.
4. Aggiungi trigger anti-UPDATE/DELETE.
5. Testa: verifica che `audit_writer` non possa fare UPDATE o DELETE.
6. Implementa partizionamento mensile e funzione retention.
7. Bonus: configura `pg_cron` per retention automatizzata.

### Esercizio 4 — SIEM forward Wazuh (90 min)

**Obiettivo:** Configurare forward audit log a Wazuh con regole custom.

1. Installa Wazuh (Docker Compose o VM).
2. Configura decoder e regole custom per workflow audit events.
3. Configura agent Wazuh per leggere il file audit.
4. Genera eventi di test (successi, fallimenti, accessi negati).
5. Verifica che gli eventi appaiano nella Wazuh Dashboard.
6. Verifica che gli alert scattino per pattern sospetti (brute force, mass export).

### Esercizio 5 — Pseudonimizzazione GDPR (45 min)

**Obiettivo:** Implementare pseudonymization store con forget capability.

1. Crea database `pseudonym_store` con le tabelle necessarie.
2. Implementa `PseudonymStore` con metodi `get_or_create_pseudonym`, `resolve_pseudonym`, `forget`.
3. Integra con `AuditLogger`: ogni log usa pseudonimi per actor.
4. Scrivi 20 audit events per 5 utenti diversi.
5. Esegui `forget("user-3")`.
6. Verifica: gli audit events con il pseudonimo di user-3 esistono ancora, ma il pseudonimo non e piu risolvibile.

---

## Troubleshooting — 15 problemi comuni

### 1. Audit events non arrivano al SIEM

**Sintomo:** Dashboard SIEM vuota nonostante workflow in esecuzione.

**Diagnosi:**
1. Verifica che il file di audit esista e contenga eventi: `tail -5 /var/log/audit/workflow-events.jsonl`
2. Verifica che l'agent Wazuh/Fluentd stia leggendo il file: `systemctl status wazuh-agent`
3. Verifica connettivita di rete verso il SIEM: `nc -zv siem.internal 1514`
4. Controlla i log dell'agent per errori di parsing o connessione.

**Soluzione:** Di solito e un problema di permessi (l'agent non puo leggere il file) o di formato (decoder non matcha il JSON).

### 2. Hash chain rotta dopo restart del servizio

**Sintomo:** `verify_audit_chain()` fallisce al primo evento dopo il restart.

**Causa:** Il `last_hash` non e stato persistito allo shutdown. Al restart, ricomincia da "genesis" invece che dall'ultimo hash valido.

**Soluzione:** Persistere `last_hash` su disco al flush/shutdown. Al startup, leggere l'ultimo hash dal file di audit o dal database.

```python
def _recover_last_hash(self) -> str:
    """Recupera l'ultimo hash dalla tabella audit."""
    cursor = self._db.cursor()
    cursor.execute("SELECT hash_self FROM audit_events ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    return row[0] if row else "sha256:genesis"
```

### 3. Performance degradata con volumi alti

**Sintomo:** Audit logging rallenta il workflow.

**Causa:** Flush sincrono ad ogni evento, o buffer troppo piccolo.

**Soluzione:**
- Aumentare `buffer_size` (es. 500-1000).
- Usare flush asincrono con timer (gia implementato nel logger sopra).
- Usare batch insert in PostgreSQL.
- Per volumi estremi, usare Kafka come buffer intermedio.

### 4. Partition PostgreSQL non creata

**Sintomo:** `INSERT` fallisce con `no partition of relation "audit_events" found for row`.

**Causa:** La partizione per il mese corrente non esiste.

**Soluzione:** Eseguire `SELECT create_future_partitions(3)` via cron mensile, oppure usare `pg_partman` per automazione.

### 5. Elasticsearch ILM non applica retention

**Sintomo:** Indici vecchi non vengono cancellati.

**Diagnosi:** `GET _ilm/policy/audit-retention-policy` e verificare che la policy sia associata agli indici.

**Soluzione:** Verificare che l'index template abbia `index.lifecycle.name` corretto e che il rollover alias sia configurato.

### 6. Pseudonimo non risolvibile dopo forget

**Sintomo:** DPO cerca di risolvere un pseudonimo e ottiene `None`.

**Causa:** Questo e il comportamento atteso! Il `forget()` cancella la mappatura. Se il DPO ha bisogno di verificare che il forget sia avvenuto, consultare la tabella `forget_requests`.

### 7. Clock skew tra nodi causa ordine eventi sbagliato

**Sintomo:** Audit events con timestamp non monotonicamente crescente.

**Diagnosi:** `chronyc tracking` o `timedatectl status` su ogni nodo.

**Soluzione:** Configurare NTP su tutti i nodi. Usare `timestamp_ingested` (lato server audit) come timestamp autorevole per l'ordinamento.

### 8. Audit log contiene PII in chiaro

**Sintomo:** Audit esterno trova email/nomi in chiaro negli audit events.

**Causa:** Mancata pseudonimizzazione nell'integrazione con il workflow.

**Soluzione:** Audit di tutti i punti di ingresso dell'audit logger. Aggiungere validazione pre-scrittura che rifiuta campi con pattern email/telefono.

### 9. Wazuh decoder non parsa il JSON

**Sintomo:** Eventi appaiono in Wazuh come "unknown" o non matchano le regole.

**Diagnosi:** `/var/ossec/bin/wazuh-logtest` e incollare un evento di esempio.

**Soluzione:** Verificare il `prematch` nel decoder. Deve matchare l'inizio esatto dell'evento JSON.

### 10. Trigger anti-DELETE bloccante per la retention

**Sintomo:** `DROP TABLE audit_events_2024_01` fallisce con "Operation DELETE denied".

**Causa:** Il trigger si attiva su DELETE di righe, non su DROP TABLE. Ma se stai usando `DELETE FROM` invece di `DROP TABLE`, il trigger e corretto nel bloccarlo.

**Soluzione:** Per la retention, usare `DROP TABLE partition_name` (non `DELETE FROM`), che non attiva i trigger a livello di riga.

### 11. Buffer overflow sotto carico

**Sintomo:** Log warning "buffer near capacity" e possibile perdita eventi.

**Soluzione:** Aumentare `maxlen` del buffer, ridurre `flush_interval`, o aggiungere backpressure (rallentare il workflow se il buffer e pieno).

### 12. Export CSV troppo grande per l'auditor

**Sintomo:** File CSV da GB, inutilizzabile.

**Soluzione:** Filtrare per `action_category`, `resource.type`, e intervallo temporale. Generare report riassuntivi prima dell'export dettagliato.

### 13. Retention diversa per tenant non rispettata

**Sintomo:** Dati di un tenant cancellati troppo presto o troppo tardi.

**Causa:** Retention globale invece che per-tenant.

**Soluzione:** Partizionare per tenant E per data. Applicare retention per-tenant basata sui regolamenti configurati.

### 14. Audit events duplicati dopo retry

**Sintomo:** Lo stesso evento appare due volte nel log.

**Causa:** Flush fallito, retry riuscito, ma il primo tentativo era andato a buon fine.

**Soluzione:** Usare `event_id` come chiave unica. In PostgreSQL, `INSERT ... ON CONFLICT (event_id) DO NOTHING`. In Elasticsearch, usare `event_id` come `_id` del documento.

### 15. SIEM forward fallisce silenziosamente

**Sintomo:** Nessun errore visibile, ma gli eventi non arrivano al SIEM.

**Diagnosi:** Verificare la coda di rsyslog/fluentd (`queue.filename`, disk usage). Verificare che il SIEM sia raggiungibile.

**Soluzione:** Monitorare la coda con metriche (profondita coda, eta del messaggio piu vecchio). Alert se la coda cresce.

---

## FAQ — 15 domande e risposte

### 1. Posso usare un database NoSQL per gli audit log?

Si, ma con cautele. MongoDB, DynamoDB, e Cassandra possono funzionare. Requisiti chiave: (a) supporto per append-only (niente UPDATE/DELETE per l'utente applicativo), (b) retention policy, (c) query per actor/action/resource/timerange. Elasticsearch/OpenSearch e la scelta piu comune per volumi alti grazie alle capacita di ricerca.

### 2. L'hash chain e sufficiente come tamper-evidence?

Per la maggior parte dei regolamenti, si. Per contesti ad altissima assurance (es. governo, difesa), considerare anche firma digitale (PKI) di ogni evento o di batch di eventi, e/o uso di timestamping authority (TSA) conforme eIDAS.

### 3. Quanto spazio occupano gli audit log?

Dipende dal volume di workflow. Stima: un evento JSON compresso occupa ~500 byte. A 1000 esecuzioni/giorno, sono ~500 KB/giorno, ~180 MB/anno. A 100.000 esecuzioni/giorno, ~50 MB/giorno, ~18 GB/anno. Con 7 anni di retention (SOX): ~126 GB. Includere un buffer 3x per crescita.

### 4. Devo loggare anche gli accessi in lettura (data.read)?

Dipende dal regolamento. HIPAA richiede logging di ogni accesso a ePHI, incluse le letture. GDPR non lo richiede esplicitamente, ma e best practice per accountability. SOX richiede logging di ogni accesso a dati finanziari. Consiglio: loggare tutto, filtrare dopo.

### 5. Come gestisco l'audit logging in ambienti serverless (Lambda/Cloud Functions)?

Le funzioni serverless sono effimere. Non puoi usare buffer in memoria. Opzioni: (a) scrivere direttamente in un servizio di logging cloud (CloudWatch, Cloud Logging), (b) inviare a una coda (SQS, Pub/Sub) che un consumer scrive nel sistema di audit, (c) usare un sidecar o extension Lambda per buffering.

### 6. L'audit log deve essere criptato at rest?

Si, obbligatorio per HIPAA, fortemente consigliato per GDPR e SOX. Usare encryption at rest del database (TDE per PostgreSQL, encrypted volumes per Elasticsearch). Per file-based, usare LUKS o dm-crypt.

### 7. Come faccio a dimostrare che l'audit log non e stato modificato?

Hash chain + verifica periodica documentata + SIEM forward (copia indipendente) + eventuale firma digitale. L'auditor puo confrontare gli hash nel log locale con quelli nel SIEM.

### 8. Qual e la differenza tra audit log e application log?

L'audit log risponde a "chi ha fatto cosa, quando, con quale esito" per scopi legali e di compliance. L'application log registra eventi tecnici (debug, errori, performance) per scopi operativi. Possono sovrapporsi, ma hanno requisiti diversi di retention, immutabilita, e formato.

### 9. Posso usare lo stesso sistema per audit log e application log?

Sconsigliato. L'audit log ha requisiti di immutabilita, retention, e accesso che differiscono dall'application log. Mantenere sistemi separati con pipeline diverse. Se proprio devi unificarli, usa tagging (`log.type: audit` vs `log.type: application`) e applica retention e accesso diversificati.

### 10. Come gestisco l'audit di workflow asincroni long-running?

Usa il `workflow_run_id` come chiave di correlazione. Ogni step emette un audit event con lo stesso `workflow_run_id`. Alla fine del workflow (successo o fallimento), emetti un evento di completamento. Per Temporal/Airflow, gli interceptor/callback fanno questo automaticamente.

### 11. Serve un Data Protection Officer (DPO) per gestire gli audit log?

Per GDPR, il DPO e obbligatorio per autorita pubbliche, organizzazioni che fanno monitoraggio sistematico su larga scala, e organizzazioni che trattano dati sensibili su larga scala. Per SOX, il ruolo equivalente e il Chief Compliance Officer. Per HIPAA, il Privacy Officer. Indipendentemente dall'obbligo, avere un responsabile del sistema di audit e best practice.

### 12. Come testo il sistema di audit in staging?

Usa dati sintetici (mai dati di produzione). Genera eventi con un generatore di test che copre tutti gli action types. Verifica: (a) eventi scritti correttamente, (b) hash chain valida, (c) retention applicata, (d) SIEM riceve gli eventi, (e) alert scattano per pattern sospetti.

### 13. Cosa succede se l'audit logger va in errore durante un workflow?

Dipende dalla criticita. Per workflow regolamentati (SOX, HIPAA), il workflow DEVE fallire se l'audit non e scritto (audit before action). Per workflow meno critici, l'audit puo essere best-effort con alerting sull'errore. Mai silenziare l'errore.

### 14. Come gestisco il GDPR Art. 15 (diritto di accesso) con audit log pseudonimizzati?

1. Il DPO riceve la richiesta di accesso da un data subject.
2. Cerca nel pseudonym store tutti i pseudonimi del data subject.
3. Query l'audit log per tutti gli eventi con quei pseudonimi.
4. Genera un report con gli eventi (senza rivelare i pseudonimi di altri data subject).
5. Fornisce il report al data subject.

### 15. Qual e il costo di un sistema di audit completo?

Componenti: storage (DB + object storage per archive), SIEM (licenza o self-hosted), monitoring, personale. Per PMI con Wazuh (open source) + PostgreSQL: costo infrastruttura ~50-200 EUR/mese. Per enterprise con Splunk/Elastic Cloud: 1000-10000+ EUR/mese a seconda del volume di dati ingeriti.

---

## Auto-valutazione

1. Audit log immutability: quali 3 meccanismi la implementano?
2. Tamper-evidence: descrivi il funzionamento della hash chain.
3. GDPR vs HIPAA retention: qual e la differenza e perche?
4. Right to be forgotten vs audit immutability: come risolvere il conflitto?
5. SIEM forward: perche e obbligatorio in produzione?
6. Perche l'actor.id nell'audit event deve essere pseudonimizzato?
7. Quale ruolo puo cancellare audit log e con quali vincoli?
8. SOX Sec. 802: cosa vieta e per quanto tempo?
9. PCI-DSS 10.7: quanti mesi devono essere immediatamente disponibili?
10. Come si calcola la retention effettiva con piu regolamenti applicabili?
11. Merkle tree vs hash chain lineare: vantaggi e svantaggi.
12. Perche servono due timestamp (event + ingested)?
13. Come si monitora la salute del sistema di audit?
14. Cosa succede se il clock di un nodo e fuori sync?
15. In un sistema multi-tenant, come si garantisce l'isolation degli audit log?

---

## Letture primarie consigliate

- GDPR Art. 5, 15, 17, 25, 30, 33, 35. Testo completo: eur-lex.europa.eu.
- SOX Act, Sec. 302, 404, 802. Testo completo: sec.gov.
- HIPAA Security Rule §164.312(b), §164.308(a)(1)(ii)(D). Testo completo: hhs.gov.
- NIST SP 800-92 — Guide to Computer Security Log Management.
- NIST SP 800-53 Rev. 5 — AU (Audit and Accountability) control family.
- PCI-DSS v4.0, Requirement 10. Testo completo: pcisecuritystandards.org.
- ISO 27001:2022, Annex A.8.15 (Logging).
- CAD (Codice Amministrazione Digitale), Art. 43-44.
- W3C Trace Context specification (per correlazione con OTel, vedi Modulo 23).
- Vedi `00-BIBLIOGRAFIA.md` per riferimenti completi.

---

## Collegamenti incrociati

- Modulo 07 — governance.
- Modulo 23 — osservabilita (OTel traces/metrics/logs per correlazione audit ↔ observability).
- Modulo 25 — multi-environment promotion (audit per promozioni dev→staging→prod).
- Modulo 20 — OAuth2 flows (audit di token grant/refresh/revoke).

---

## Glossario locale

| Termine | Definizione |
|---|---|
| **Audit log** | Registro tracciabile e immutabile delle operazioni, con valore legale. |
| **Tamper-evidence** | Capacita di rilevare modifiche post-fatto tramite hash chain o firma digitale. |
| **Hash chain** | Ogni record include l'hash del precedente, formando una catena verificabile. |
| **Merkle tree** | Struttura dati ad albero dove ogni nodo e l'hash dei figli; verifica in O(log n). |
| **Pseudonimizzazione** | Sostituzione dati personali con token non riconducibile senza tabella di mapping (GDPR Art. 4(5)). |
| **Anonimizzazione** | Rimozione irreversibile dell'identita; i dati anonimizzati non sono dati personali. |
| **SIEM** | Security Information and Event Management — sistema centralizzato di log analysis e alerting. |
| **SIEM forward** | Invio automatico dei log al SIEM per centralizzazione e analisi. |
| **Retention** | Tempo minimo di conservazione obbligatoria per legge. |
| **Right to be forgotten** | GDPR Art. 17 — diritto del data subject alla cancellazione dei propri dati. |
| **Data lineage** | Tracciamento dell'origine, trasformazione e destinazione dei dati in un pipeline. |
| **Append-only** | Modello di storage dove solo INSERT e permesso; UPDATE e DELETE vietati. |
| **Partition pruning** | Tecnica PostgreSQL per DROP di intere partizioni per retention efficiente. |
| **ILM** | Index Lifecycle Management — gestione automatica del ciclo di vita degli indici Elasticsearch. |
| **SOX** | Sarbanes-Oxley Act (2002) — legge USA per la trasparenza finanziaria aziendale. |
| **HIPAA** | Health Insurance Portability and Accountability Act — legge USA per la protezione dati sanitari. |
| **PCI-DSS** | Payment Card Industry Data Security Standard — standard per protezione dati carte di pagamento. |
| **AGID** | Agenzia per l'Italia Digitale — ente per la digitalizzazione della PA italiana. |
| **CAD** | Codice dell'Amministrazione Digitale — normativa italiana sulla conservazione digitale. |
| **NIS2** | Direttiva UE 2022/2555 sulla sicurezza delle reti e dei sistemi informativi. |
| **DPO** | Data Protection Officer — responsabile protezione dati (GDPR Art. 37-39). |
| **ePHI** | Electronic Protected Health Information — dati sanitari elettronici protetti (HIPAA). |
| **eIDAS** | Regolamento UE sull'identificazione elettronica e servizi fiduciari. |
| **TSA** | Timestamping Authority — servizio di marca temporale conforme eIDAS. |
| **RBAC** | Role-Based Access Control — controllo accessi basato sui ruoli. |
| **RLS** | Row Level Security — policy PostgreSQL per isolation a livello di riga. |
| **SInCRO** | Standard UNI 11386 per la struttura dell'Indice di Conservazione. |
