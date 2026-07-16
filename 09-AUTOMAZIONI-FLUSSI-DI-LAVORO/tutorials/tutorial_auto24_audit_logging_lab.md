# Tutorial Lab — Audit Logging e Compliance per Automazioni

> **Campo di studio:** 09-AUTOMAZIONI-FLUSSI-DI-LAVORO
> **Modulo sorgente:** `24-audit-logging-compliance.md`
> **Livello:** intermediate → advanced
> **Tempo stimato:** 2-3 ore
> **Prerequisiti:** Python base, SQLite/PostgreSQL base, concetti GDPR
> **Versioni di riferimento:** Python 3.11+ · PostgreSQL 16 · OTel Logs 1.x

---

## Obiettivi del Lab

Al termine di questo tutorial saprai:

1. Progettare un audit log immutabile per workflow automatizzati
2. Implementare structured logging con correlazione trace/span
3. Garantire requisiti GDPR: pseudonimizzazione, retention automatica, right-to-erasure
4. Costruire report di compliance automatici da audit trail
5. Proteggere l'audit log da tampering (firma hash, append-only)
6. Integrare audit log con OTel per correlazione con trace distribuiti

---

## Lab Environment Setup

```bash
python3 --version    # 3.11+
docker run -d --name postgres-audit -p 5432:5432 \
  -e POSTGRES_PASSWORD=auditlab \
  -e POSTGRES_DB=audit \
  postgres:16-alpine

pip install psycopg2-binary==2.9.9 cryptography==43.0.0 structlog==24.0.0
```

---

## Analogia Introduttiva

> **L'audit log è il notaio dei sistemi informatici**:
> certifica che una certa azione è avvenuta, da chi, quando, e con quale esito.
> Come il notaio, non può modificare gli atti già firmati
> (immutabilità), e conserva tutto il necessario per ricostruire
> la storia di una pratica (tracciabilità).
>
> La differenza tra un log normale e un audit log:
> - Log normale: "cosa è successo" (debug)
> - Audit log: "chi ha fatto cosa, su cosa, quando, con quale autorizzazione" (compliance)
>
> Il GDPR richiede audit log per: accessi a dati personali,
> modifiche, esportazioni, cancellazioni. Senza: sanzione fino a 4% fatturato globale.
> Con un audit log ben progettato: dimostri compliance in 5 minuti.

---

## PART A — Schema Audit Log

### A1 — Schema PostgreSQL Immutabile

```sql
-- file: schema/audit_log.sql
-- Schema audit log immutabile per workflow automatizzati
-- Principi: append-only, no UPDATE/DELETE, hash chain per tamper detection

CREATE TABLE IF NOT EXISTS audit_log (
    id              BIGSERIAL PRIMARY KEY,
    
    -- Identificazione evento
    evento_id       UUID NOT NULL DEFAULT gen_random_uuid() UNIQUE,
    timestamp_utc   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    sequence_num    BIGINT NOT NULL,  -- Numero sequenziale per ordinamento affidabile
    
    -- Chi ha eseguito l'azione
    attore_tipo     TEXT NOT NULL,   -- "utente" | "servizio" | "workflow" | "scheduled_job"
    attore_id       TEXT NOT NULL,   -- ID opaco (non email/nome — pseudonimizzato!)
    
    -- Cosa è stato fatto
    azione          TEXT NOT NULL,   -- "crea" | "legge" | "modifica" | "cancella" | "esporta"
    risorsa_tipo    TEXT NOT NULL,   -- "ordine" | "fattura" | "cliente" | "workflow"
    risorsa_id      TEXT NOT NULL,   -- ID risorsa coinvolta
    
    -- Risultato
    esito           TEXT NOT NULL CHECK (esito IN ('successo', 'fallimento', 'parziale')),
    codice_errore   TEXT,            -- Codice errore se esito != successo
    
    -- Contesto
    workflow_id     TEXT,            -- ID workflow n8n (se applicabile)
    trace_id        TEXT,            -- OTel trace ID per correlazione
    span_id         TEXT,            -- OTel span ID
    indirizzo_ip    TEXT,            -- Pseudonimizzato: hash(ip + salt)
    user_agent_hash TEXT,            -- Hash dello user agent
    
    -- Dettagli (JSON senza PII!)
    dettagli        JSONB,
    
    -- Integrità: ogni riga firma quella precedente
    hash_riga       TEXT NOT NULL,   -- SHA-256(evento_id||timestamp||azione||risorsa_id||hash_prev)
    hash_precedente TEXT             -- Hash della riga precedente (NULL per la prima riga)
);

-- ─── Protezioni ────────────────────────────────────────────────────────────────

-- Sequenza numerica monotonica (più affidabile di timestamp per ordinamento)
CREATE SEQUENCE IF NOT EXISTS audit_sequence START 1;

-- Indici per query frequenti
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log (timestamp_utc DESC);
CREATE INDEX IF NOT EXISTS idx_audit_risorsa ON audit_log (risorsa_tipo, risorsa_id, timestamp_utc DESC);
CREATE INDEX IF NOT EXISTS idx_audit_attore ON audit_log (attore_id, timestamp_utc DESC);
CREATE INDEX IF NOT EXISTS idx_audit_azione ON audit_log (azione, timestamp_utc DESC);
CREATE INDEX IF NOT EXISTS idx_audit_trace ON audit_log (trace_id) WHERE trace_id IS NOT NULL;

-- Nega UPDATE e DELETE all'utente applicazione
-- Crea utente con solo INSERT + SELECT:
-- CREATE ROLE audit_writer WITH LOGIN PASSWORD 'CHANGEME';
-- GRANT INSERT, SELECT ON audit_log TO audit_writer;
-- GRANT USAGE ON SEQUENCE audit_sequence TO audit_writer;
-- (nessun UPDATE, DELETE, TRUNCATE!)

-- ─── Retention automatica via partitioning ────────────────────────────────────
-- Per retention policy: partiziona per mese, DROP vecchie partizioni
-- Esempio: pg_partman per gestione automatica

COMMENT ON TABLE audit_log IS 
  'Audit log immutabile. Nessun UPDATE/DELETE permesso. GDPR compliant.';
COMMENT ON COLUMN audit_log.attore_id IS 
  'ID opaco — mai email/nome diretto. Usa mapping separato per right-to-erasure.';
COMMENT ON COLUMN audit_log.indirizzo_ip IS 
  'SHA-256(ip + daily_salt) — non reversibile. Per GDPR: pseudonimizzato.';
```

### A2 — AuditLogger Python

```python
#!/usr/bin/env python3
# file: audit/audit_logger.py
"""
Audit logger con hash chain per tamper detection.
Principi GDPR:
- No PII diretto: hash attori, pseudonimizza IP
- Retention automatica con TTL configurabile
- Right-to-erasure: tramite mapping table separata
"""
from __future__ import annotations

import hashlib
import json
import os
import time
import uuid
import logging
from contextlib import contextmanager
from dataclasses import dataclass, asdict
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ─── Costanti ──────────────────────────────────────────────────────────────────

AUDIT_RETENTION_GIORNI = int(os.environ.get("AUDIT_RETENTION_GIORNI", "2555"))  # 7 anni
IP_SALT = os.environ.get("AUDIT_IP_SALT", "cambia-questa-salt-ogni-giorno")

AZIONI_VALIDE = frozenset({
    "crea", "legge", "modifica", "cancella", "esporta",
    "autentica", "deautentica", "accede", "rifiuta",
    "avvia_workflow", "completa_workflow", "fallisce_workflow",
})

TIPI_RISORSA_VALIDI = frozenset({
    "ordine", "fattura", "cliente", "prodotto",
    "workflow", "utente", "configurazione", "report",
})


@dataclass
class EventoAudit:
    """Singolo evento audit. Immutabile dopo creazione."""
    attore_tipo: str    # "utente" | "servizio" | "workflow"
    attore_id: str      # ID opaco (già pseudonimizzato)
    azione: str
    risorsa_tipo: str
    risorsa_id: str
    esito: str          # "successo" | "fallimento" | "parziale"
    
    # Opzionali
    codice_errore: Optional[str] = None
    workflow_id: Optional[str] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    ip_address: Optional[str] = None     # Viene hashato prima del salvataggio
    user_agent: Optional[str] = None     # Viene hashato
    dettagli: Optional[dict] = None


def pseudonimizza_ip(ip: str, salt: str = IP_SALT) -> str:
    """
    SHA-256(ip + daily_salt) — non reversibile.
    Stessa IP → stesso hash nello stesso giorno.
    Rotazione salt giornaliera: non correlabile tra giorni diversi.
    """
    return hashlib.sha256(f"{ip}:{salt}".encode()).hexdigest()[:16]


def calcola_hash_riga(
    evento_id: str,
    timestamp_iso: str,
    azione: str,
    risorsa_id: str,
    hash_precedente: Optional[str],
) -> str:
    """
    Hash di integrità per tamper detection.
    Concatena campi chiave + hash precedente → chain verificabile.
    """
    contenuto = f"{evento_id}|{timestamp_iso}|{azione}|{risorsa_id}|{hash_precedente or 'GENESIS'}"
    return hashlib.sha256(contenuto.encode()).hexdigest()


class AuditLogger:
    """
    Audit logger production-grade con:
    - Hash chain per tamper detection
    - Pseudonimizzazione PII
    - Append-only semantics
    - Correlazione OTel trace
    """

    def __init__(self, connstring: str):
        import psycopg2
        self._conn = psycopg2.connect(connstring)
        self._conn.autocommit = False
        self._inizializza_schema()

    def _inizializza_schema(self) -> None:
        with self._conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id BIGSERIAL PRIMARY KEY,
                    evento_id UUID NOT NULL UNIQUE,
                    timestamp_utc TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    sequence_num BIGINT NOT NULL,
                    attore_tipo TEXT NOT NULL,
                    attore_id TEXT NOT NULL,
                    azione TEXT NOT NULL,
                    risorsa_tipo TEXT NOT NULL,
                    risorsa_id TEXT NOT NULL,
                    esito TEXT NOT NULL,
                    codice_errore TEXT,
                    workflow_id TEXT,
                    trace_id TEXT,
                    span_id TEXT,
                    indirizzo_ip_hash TEXT,
                    user_agent_hash TEXT,
                    dettagli JSONB,
                    hash_riga TEXT NOT NULL,
                    hash_precedente TEXT
                )
            """)
            cur.execute("CREATE SEQUENCE IF NOT EXISTS audit_sequence START 1")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_audit_risorsa ON audit_log (risorsa_tipo, risorsa_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_audit_attore ON audit_log (attore_id)")
        self._conn.commit()

    def _ottieni_hash_precedente(self) -> Optional[str]:
        """Recupera l'hash dell'ultima riga inserita."""
        with self._conn.cursor() as cur:
            cur.execute("SELECT hash_riga FROM audit_log ORDER BY sequence_num DESC LIMIT 1")
            row = cur.fetchone()
            return row[0] if row else None

    def registra(self, evento: EventoAudit) -> str:
        """
        Registra un evento nell'audit log.
        Thread-safe con lock a livello DB (SELECT ... FOR UPDATE).
        
        Ritorna evento_id.
        """
        # Validazione
        if evento.azione not in AZIONI_VALIDE:
            raise ValueError(f"Azione non valida: {evento.azione}")
        if evento.risorsa_tipo not in TIPI_RISORSA_VALIDI:
            raise ValueError(f"Tipo risorsa non valido: {evento.risorsa_tipo}")
        if evento.esito not in ("successo", "fallimento", "parziale"):
            raise ValueError(f"Esito non valido: {evento.esito}")
        
        evento_id = str(uuid.uuid4())
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        
        # Pseudonimizza PII
        ip_hash = pseudonimizza_ip(evento.ip_address) if evento.ip_address else None
        ua_hash = hashlib.sha256(evento.user_agent.encode()).hexdigest()[:16] if evento.user_agent else None
        
        # Rimuovi PII dai dettagli
        dettagli_sicuri = _rimuovi_pii(evento.dettagli) if evento.dettagli else None
        
        with self._conn.cursor() as cur:
            # Lock pessimistico per garantire serializzazione della hash chain
            cur.execute("SELECT pg_advisory_xact_lock(1234567890)")
            
            hash_prev = self._ottieni_hash_precedente()
            hash_riga = calcola_hash_riga(evento_id, timestamp, evento.azione,
                                          evento.risorsa_id, hash_prev)
            
            cur.execute("SELECT nextval('audit_sequence')")
            seq_num = cur.fetchone()[0]
            
            cur.execute("""
                INSERT INTO audit_log (
                    evento_id, timestamp_utc, sequence_num,
                    attore_tipo, attore_id, azione, risorsa_tipo, risorsa_id, esito,
                    codice_errore, workflow_id, trace_id, span_id,
                    indirizzo_ip_hash, user_agent_hash, dettagli,
                    hash_riga, hash_precedente
                ) VALUES (
                    %s, NOW(), %s,
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s
                )
            """, (
                evento_id, seq_num,
                evento.attore_tipo, evento.attore_id, evento.azione,
                evento.risorsa_tipo, evento.risorsa_id, evento.esito,
                evento.codice_errore, evento.workflow_id,
                evento.trace_id, evento.span_id,
                ip_hash, ua_hash, json.dumps(dettagli_sicuri) if dettagli_sicuri else None,
                hash_riga, hash_prev
            ))
        
        self._conn.commit()
        return evento_id

    def verifica_integrità(self, limit: int = 1000) -> dict:
        """
        Verifica la hash chain dall'inizio.
        Rileva tampering: qualsiasi modifica rompe la chain.
        """
        with self._conn.cursor() as cur:
            cur.execute("""
                SELECT evento_id, timestamp_utc::text, azione, risorsa_id,
                       hash_riga, hash_precedente
                FROM audit_log
                ORDER BY sequence_num ASC
                LIMIT %s
            """, (limit,))
            righe = cur.fetchall()
        
        errori = []
        hash_atteso = None
        
        for i, (evento_id, ts, azione, risorsa_id, hash_riga, hash_prev) in enumerate(righe):
            # Verifica hash della riga
            hash_calcolato = calcola_hash_riga(str(evento_id), ts, azione, risorsa_id, hash_prev)
            
            if hash_calcolato != hash_riga:
                errori.append(f"Riga {i+1} ({evento_id}): hash non corrisponde!")
            
            # Verifica collegamento alla riga precedente
            if i > 0 and hash_prev != hash_atteso:
                errori.append(f"Riga {i+1}: hash_precedente non corrisponde alla riga {i}!")
            
            hash_atteso = hash_riga
        
        return {
            "righe_verificate": len(righe),
            "integra": len(errori) == 0,
            "errori": errori,
        }

    def cerca(
        self,
        risorsa_tipo: Optional[str] = None,
        risorsa_id: Optional[str] = None,
        attore_id: Optional[str] = None,
        azione: Optional[str] = None,
        da: Optional[str] = None,   # ISO timestamp
        a: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict]:
        """Ricerca nel audit log con filtri multipli."""
        conditions = []
        params = []
        
        if risorsa_tipo:
            conditions.append("risorsa_tipo = %s")
            params.append(risorsa_tipo)
        if risorsa_id:
            conditions.append("risorsa_id = %s")
            params.append(risorsa_id)
        if attore_id:
            conditions.append("attore_id = %s")
            params.append(attore_id)
        if azione:
            conditions.append("azione = %s")
            params.append(azione)
        if da:
            conditions.append("timestamp_utc >= %s")
            params.append(da)
        if a:
            conditions.append("timestamp_utc <= %s")
            params.append(a)
        
        where = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        with self._conn.cursor() as cur:
            cur.execute(f"""
                SELECT evento_id::text, timestamp_utc::text, attore_tipo, attore_id,
                       azione, risorsa_tipo, risorsa_id, esito, workflow_id,
                       trace_id, codice_errore, dettagli
                FROM audit_log
                {where}
                ORDER BY timestamp_utc DESC
                LIMIT %s
            """, params + [limit])
            
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


def _rimuovi_pii(dettagli: dict) -> dict:
    """
    Rimuove PII dai dettagli prima del salvataggio.
    Campi considerati PII: email, nome, cognome, CF, telefono, indirizzo.
    """
    CAMPI_PII = frozenset({
        "email", "nome", "cognome", "first_name", "last_name",
        "telefono", "phone", "cf", "codice_fiscale", "piva",
        "indirizzo", "address", "iban", "carta_credito",
    })
    
    def pulisci(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {
                k: "[REDACTED]" if k.lower() in CAMPI_PII else pulisci(v)
                for k, v in obj.items()
            }
        if isinstance(obj, list):
            return [pulisci(item) for item in obj]
        return obj
    
    return pulisci(dettagli)


# ─── Context manager ──────────────────────────────────────────────────────────

@contextmanager
def audit_azione(
    audit: AuditLogger,
    attore_tipo: str,
    attore_id: str,
    azione: str,
    risorsa_tipo: str,
    risorsa_id: str,
    dettagli: Optional[dict] = None,
    workflow_id: Optional[str] = None,
):
    """
    Context manager per auditare operazioni automaticamente.
    Registra successo o fallimento + codice errore.
    """
    from opentelemetry import trace as otel_trace
    
    span = otel_trace.get_current_span()
    trace_id = None
    span_id = None
    if span and span.is_recording():
        ctx = span.get_span_context()
        trace_id = f"{ctx.trace_id:032x}"
        span_id = f"{ctx.span_id:016x}"
    
    try:
        yield
        audit.registra(EventoAudit(
            attore_tipo=attore_tipo,
            attore_id=attore_id,
            azione=azione,
            risorsa_tipo=risorsa_tipo,
            risorsa_id=risorsa_id,
            esito="successo",
            dettagli=dettagli,
            workflow_id=workflow_id,
            trace_id=trace_id,
            span_id=span_id,
        ))
    except Exception as e:
        audit.registra(EventoAudit(
            attore_tipo=attore_tipo,
            attore_id=attore_id,
            azione=azione,
            risorsa_tipo=risorsa_tipo,
            risorsa_id=risorsa_id,
            esito="fallimento",
            codice_errore=f"{type(e).__name__}: {str(e)[:100]}",
            dettagli=dettagli,
            workflow_id=workflow_id,
            trace_id=trace_id,
            span_id=span_id,
        ))
        raise
```

---

## PART B — Report di Compliance

### B1 — Report GDPR Automatici

```python
#!/usr/bin/env python3
# file: audit/compliance_report.py
"""
Generazione report di compliance GDPR da audit log.
Report tipici:
- Accessi a dati di un soggetto specifico (diritto di accesso)
- Lista esportazioni dati nell'ultimo mese
- Accessi anomali (utente accede a molte risorse insolite)
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Optional

from audit.audit_logger import AuditLogger


class ComplianceReporter:
    """Generatore report compliance da audit log."""

    def __init__(self, audit: AuditLogger):
        self.audit = audit

    def report_accessi_soggetto(self, soggetto_id: str) -> dict:
        """
        Art. 15 GDPR: il soggetto ha diritto di sapere
        chi ha acceduto ai suoi dati e quando.
        
        soggetto_id: ID interno del soggetto (non PII!)
        """
        # Cerca tutti gli accessi alla risorsa "cliente" con questo ID
        eventi = self.audit.cerca(
            risorsa_tipo="cliente",
            risorsa_id=soggetto_id,
            limit=1000,
        )
        
        # Aggrega per attore e azione
        accessi_per_attore: dict[str, list] = {}
        for ev in eventi:
            attore = ev["attore_id"]
            if attore not in accessi_per_attore:
                accessi_per_attore[attore] = []
            accessi_per_attore[attore].append({
                "timestamp": ev["timestamp_utc"],
                "azione": ev["azione"],
                "esito": ev["esito"],
            })
        
        return {
            "soggetto_id": soggetto_id,
            "periodo_analizzato": "tutto",
            "totale_accessi": len(eventi),
            "accessi_per_attore": accessi_per_attore,
            "esportazioni": [ev for ev in eventi if ev["azione"] == "esporta"],
            "modifiche": [ev for ev in eventi if ev["azione"] == "modifica"],
            "generato_at": datetime.now(timezone.utc).isoformat(),
        }

    def report_esportazioni_mese(self, anno: int, mese: int) -> dict:
        """
        Report mensile di tutte le esportazioni di dati.
        Richiesto da molti programmi di compliance (ISO 27001, SOC 2).
        """
        da = f"{anno}-{mese:02d}-01T00:00:00Z"
        al = f"{anno}-{mese:02d}-31T23:59:59Z"
        
        eventi = self.audit.cerca(azione="esporta", da=da, a=al, limit=10000)
        
        # Raggruppa per tipo risorsa
        per_tipo: dict[str, int] = {}
        per_attore: dict[str, int] = {}
        
        for ev in eventi:
            tipo = ev["risorsa_tipo"]
            attore = ev["attore_id"]
            per_tipo[tipo] = per_tipo.get(tipo, 0) + 1
            per_attore[attore] = per_attore.get(attore, 0) + 1
        
        return {
            "periodo": f"{anno}-{mese:02d}",
            "totale_esportazioni": len(eventi),
            "per_tipo_risorsa": per_tipo,
            "per_attore": per_attore,
            "top_esportatori": sorted(per_attore.items(), key=lambda x: -x[1])[:5],
        }

    def rileva_anomalie(
        self,
        soglia_accessi_ora: int = 100,
        ore_analisi: int = 24,
    ) -> list[dict]:
        """
        Rileva pattern anomali: accessi insoliti, burst di letture.
        Semplice euristica — in produzione usa ML o regole più sofisticate.
        """
        da = (datetime.now(timezone.utc) - timedelta(hours=ore_analisi)).isoformat()
        eventi = self.audit.cerca(azione="legge", da=da, limit=50000)
        
        # Conta accessi per attore nell'ultima ora
        ultima_ora = datetime.now(timezone.utc) - timedelta(hours=1)
        accessi_per_attore: dict[str, int] = {}
        
        for ev in eventi:
            ts = datetime.fromisoformat(ev["timestamp_utc"].replace("Z", "+00:00"))
            if ts >= ultima_ora:
                attore = ev["attore_id"]
                accessi_per_attore[attore] = accessi_per_attore.get(attore, 0) + 1
        
        anomalie = []
        for attore, count in accessi_per_attore.items():
            if count > soglia_accessi_ora:
                anomalie.append({
                    "attore_id": attore,
                    "accessi_ultima_ora": count,
                    "soglia": soglia_accessi_ora,
                    "severita": "critica" if count > soglia_accessi_ora * 3 else "alta",
                })
        
        return sorted(anomalie, key=lambda x: -x["accessi_ultima_ora"])


# ─── Demo ─────────────────────────────────────────────────────────────────────

def demo(connstring: str):
    """Demo completa dell'audit logger."""
    audit = AuditLogger(connstring)
    reporter = ComplianceReporter(audit)
    
    print("=== DEMO AUDIT LOGGER GDPR ===\n")
    
    # Registra alcuni eventi
    print("Registrazione eventi...")
    
    for i in range(5):
        audit.registra(EventoAudit(
            attore_tipo="workflow",
            attore_id="n8n-workflow-ordini",
            azione="legge",
            risorsa_tipo="cliente",
            risorsa_id=f"CLT-{i:03d}",
            esito="successo",
            workflow_id="wf-12345",
            dettagli={
                "motivo": "verifica credito",
                "email": "[REDACTED]",  # Già redatto
                "importo_ordine": 150.0,
            },
        ))
    
    # Registra un'esportazione
    audit.registra(EventoAudit(
        attore_tipo="utente",
        attore_id="usr-admin-hashed",
        azione="esporta",
        risorsa_tipo="ordine",
        risorsa_id="ALL",
        esito="successo",
        dettagli={"formato": "CSV", "righe": 1250},
    ))
    
    print("  5 accessi + 1 esportazione registrati\n")
    
    # Verifica integrità
    print("Verifica integrità hash chain...")
    integrita = audit.verifica_integrità()
    print(f"  Righe: {integrita['righe_verificate']}")
    print(f"  Integra: {'✓' if integrita['integra'] else '✗ TAMPERING RILEVATO!'}")
    if integrita["errori"]:
        for e in integrita["errori"]:
            print(f"  ERRORE: {e}")
    
    # Report accessi soggetto
    print("\nReport accessi soggetto CLT-000...")
    report = reporter.report_accessi_soggetto("CLT-000")
    print(f"  Totale accessi: {report['totale_accessi']}")
    print(f"  Attori: {list(report['accessi_per_attore'].keys())}")
    
    print("\nAudit demo completato!")


if __name__ == "__main__":
    from audit.audit_logger import EventoAudit
    
    connstring = "postgresql://postgres:auditlab@localhost:5432/audit"
    try:
        demo(connstring)
    except Exception as e:
        print(f"Errore: {e}")
        print("Assicurati che PostgreSQL sia in running: docker run -d -p 5432:5432 ...")
```

---

## Esercizi

### Esercizio 1 — Right to Erasure (GDPR Art. 17) (25 min)

```python
def cancella_dati_soggetto(soggetto_id: str, audit: AuditLogger) -> dict:
    """
    GDPR Art. 17: Diritto all'oblio.
    NON cancella le righe audit (log è immutabile per legge!)
    MA sostituisce il soggetto_id con token anonimo.
    
    Implementa:
    1. Trova tutti i record dove risorsa_id = soggetto_id
    2. Aggiorna a risorsa_id = "ERASED-" + hash(soggetto_id)
    3. Registra l'erasure request come evento audit
    """
    pass
```

### Esercizio 2 — Alert in Tempo Reale (20 min)

Aggiungi a `ComplianceReporter` un metodo `abbona_anomalie()` che:
- Controlla ogni 5 minuti per accessi anomali
- Invia alert via webhook se rilevate anomalie critiche

### Esercizio 3 — Export GDPR Portabilità (25 min)

Implementa `esporta_dati_soggetto(soggetto_id)` che ritorna:
- Tutti gli eventi audit relativi al soggetto
- In formato JSON strutturato (per GDPR Art. 20 portabilità dati)

---

## Riferimenti

- GDPR Art. 15, 17, 20: https://gdpr-info.eu/
- PostgreSQL Audit Logging: https://www.pgaudit.org/
- OWASP Logging Guide: https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html
- Modulo sorgente: `24-audit-logging-compliance.md`
