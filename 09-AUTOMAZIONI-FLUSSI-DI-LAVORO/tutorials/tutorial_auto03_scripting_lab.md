# Tutorial Lab — Scripting per Automazione: Bash, Python e Scheduling

> **Campo di studio:** 09-AUTOMAZIONI-FLUSSI-DI-LAVORO
> **Modulo sorgente:** `03-scripting-automazione.md`
> **Livello:** beginner → intermediate
> **Tempo stimato:** 2-3 ore (lab completo)
> **Prerequisiti:** Linux bash base, Python 3.11+ base, concetto di cron job
> **Versioni di riferimento:** Python 3.11+ · schedule 1.2.x · APScheduler 3.10.x

---

## Obiettivi del Lab

Al termine di questo tutorial saprai:

1. Scrivere script Bash robusti con `set -euo pipefail`, logging e trap
2. Strutturare script Python per automazione con argparse, logging e exit codes
3. Schedulare task con cron (sistema) e schedule/APScheduler (Python)
4. Implementare lock file per prevenire esecuzioni parallele
5. Rotazione log con logrotate e Python logging.handlers.RotatingFileHandler
6. Convertire script manuali in servizi systemd affidabili

---

## Lab Environment Setup

```bash
# Verifica prerequisiti
python3 --version   # 3.11+
bash --version      # 5.x

# Python deps
pip install schedule==1.2.2 APScheduler==3.10.4 structlog==24.0.0

# Struttura progetto
mkdir -p scripting-lab/{bash,python,scheduling,systemd}
cd scripting-lab
```

---

## Analogia Introduttiva

> **Uno script Bash è come una lista della spesa eseguita automaticamente**:
> funziona perfettamente quando tutto è disponibile,
> ma se il negozio è chiuso (errore), continua stoicamente con il prossimo
> articolo — a meno che tu non dica "se manca la farina, fermati".
>
> `set -euo pipefail` è quel segnale di stop:
> "se qualcosa va storto, fermati SUBITO e dimmi cosa è successo".
> Senza di esso, lo script continua silenziosamente dopo un errore
> e arrivi alla fine con dati a metà — il peggior scenario.
>
> Python è come lo stesso processo ma con un cuoco professionista:
> può gestire eccezioni specifiche, loggare strutturato,
> fare retry, gestire state — molto più espressivo per logica complessa.
> Bash è perfetto per orchestrare comandi OS; Python per logica applicativa.

---

## Architettura

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SCHEDULING LAYERS                                  │
│                                                                       │
│  ┌─────────────────┐  ┌──────────────────┐  ┌──────────────────┐   │
│  │   CRON (OS)     │  │ schedule (Python) │  │  APScheduler     │   │
│  │                 │  │                  │  │                  │   │
│  │ * * * * * cmd   │  │ schedule.every() │  │ cron/interval    │   │
│  │ (minuto preciso)│  │ .do(fn)          │  │ +persisted state │   │
│  │ riavvia da zero │  │ loop run_pending │  │ +redis jobstore  │   │
│  └────────┬────────┘  └────────┬─────────┘  └────────┬─────────┘  │
│           │                    │                      │             │
└───────────┼────────────────────┼──────────────────────┼─────────────┘
            │                    │                      │
            ▼                    ▼                      ▼
    SCRIPT (Bash/Python)    FUNZIONE PYTHON         WORKER FUNCTION
    lock file               single process          multi-process safe
    log rotation            in-memory               persistente su restart
    exit codes              no persistence          missioni time-sensitive
```

---

## PART A — Script Bash Robusti

### A1 — Template Bash Standard

```bash
#!/usr/bin/env bash
# file: bash/template_robusto.sh
#
# Template per script Bash production-grade.
# Principi:
# - set -euo pipefail: fail fast, no silent errors
# - Logging strutturato con timestamp e livello
# - Lock file: impedisce esecuzioni parallele accidentali
# - Trap: pulizia garantita anche su SIGINT/SIGTERM
# - Exit codes standard: 0=successo 1=errore generico 2=configurazione 3=lock

set -euo pipefail
IFS=$'\n\t'  # Parsing sicuro: niente word splitting su spazi

# ─── Costanti ────────────────────────────────────────────────────────────────

readonly SCRIPT_NAME="$(basename "${BASH_SOURCE[0]}")"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly LOG_FILE="${LOG_DIR:-/var/log/automazione}/${SCRIPT_NAME%.sh}.log"
readonly LOCK_FILE="/var/run/${SCRIPT_NAME%.sh}.lock"
readonly MAX_LOG_SIZE_MB=50

# ─── Logging ─────────────────────────────────────────────────────────────────

log() {
    local level="$1"
    shift
    local messaggio="$*"
    local timestamp
    timestamp="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    
    # JSON-like per parsing con jq/Elasticsearch
    local entry="{\"ts\":\"${timestamp}\",\"level\":\"${level}\",\"script\":\"${SCRIPT_NAME}\",\"msg\":\"${messaggio}\"}"
    echo "${entry}" | tee -a "${LOG_FILE}" >&2
}

info()    { log "INFO"  "$@"; }
warning() { log "WARN"  "$@"; }
error()   { log "ERROR" "$@"; }
debug()   { [[ "${DEBUG:-0}" == "1" ]] && log "DEBUG" "$@" || true; }

# ─── Lock file ───────────────────────────────────────────────────────────────

acquisisci_lock() {
    # Usa set -C (noclobber) per creazione atomica
    if ! ( set -C; echo "$$" > "${LOCK_FILE}" ) 2>/dev/null; then
        local pid_bloccante
        pid_bloccante="$(cat "${LOCK_FILE}" 2>/dev/null || echo "sconosciuto")"
        
        # Controlla se il processo è ancora vivo
        if kill -0 "${pid_bloccante}" 2>/dev/null; then
            error "Script già in esecuzione (PID ${pid_bloccante}). Esco."
            exit 3
        else
            warning "Lock stale trovato (PID ${pid_bloccante} non esiste). Rimozione."
            rm -f "${LOCK_FILE}"
            echo "$$" > "${LOCK_FILE}"
        fi
    fi
    info "Lock acquisito (PID $$)"
}

rilascia_lock() {
    rm -f "${LOCK_FILE}"
    debug "Lock rilasciato"
}

# ─── Trap ────────────────────────────────────────────────────────────────────

pulizia() {
    local exit_code="${?:-0}"
    rilascia_lock
    if [[ "${exit_code}" -ne 0 ]]; then
        error "Script terminato con errore (exit code: ${exit_code})"
    else
        info "Script completato con successo"
    fi
}

trap pulizia EXIT
trap 'error "Interrotto da SIGINT"; exit 130' INT
trap 'error "Terminato da SIGTERM"; exit 143' TERM

# ─── Funzioni utility ─────────────────────────────────────────────────────────

verifica_prerequisiti() {
    local dipendenze=("curl" "jq" "python3")
    local mancanti=()
    
    for cmd in "${dipendenze[@]}"; do
        if ! command -v "${cmd}" &>/dev/null; then
            mancanti+=("${cmd}")
        fi
    done
    
    if [[ "${#mancanti[@]}" -gt 0 ]]; then
        error "Dipendenze mancanti: ${mancanti[*]}"
        error "Installa con: apt install ${mancanti[*]}"
        exit 2
    fi
    info "Prerequisiti verificati"
}

esegui_con_timeout() {
    local timeout_s="$1"
    shift
    timeout "${timeout_s}" "$@" || {
        local rc=$?
        if [[ "${rc}" -eq 124 ]]; then
            error "Comando '$*' scaduto dopo ${timeout_s}s"
        fi
        return "${rc}"
    }
}

# ─── Logica principale ────────────────────────────────────────────────────────

main() {
    # Crea directory log se non esiste
    mkdir -p "$(dirname "${LOG_FILE}")"
    
    info "Avvio ${SCRIPT_NAME} (PID $$)"
    acquisisci_lock
    verifica_prerequisiti
    
    # ─── Logica del task ───────────────────────────────────────────────
    
    info "Inizio elaborazione file in /data/input"
    
    local file_processati=0
    local file_errori=0
    
    # Loop sicuro su file (gestisce spazi nel nome)
    while IFS= read -r -d '' file; do
        debug "Processing: ${file}"
        
        if esegui_con_timeout 30 python3 -c "print('${file}')"; then
            ((file_processati++)) || true
            info "File elaborato: ${file}"
        else
            ((file_errori++)) || true
            warning "File fallito: ${file}"
        fi
    done < <(find /data/input -name "*.csv" -print0 2>/dev/null)
    
    info "Elaborazione completata: ${file_processati} ok, ${file_errori} errori"
    
    # Exit con errore se troppi errori
    if [[ "${file_errori}" -gt 10 ]]; then
        error "Troppi errori (${file_errori}) — controllare i dati"
        exit 1
    fi
}

# ─── Argomenti ───────────────────────────────────────────────────────────────

usage() {
    cat <<EOF
Uso: ${SCRIPT_NAME} [OPZIONI]

Opzioni:
  -h, --help    Mostra questo aiuto
  -d, --debug   Abilita log di debug
  -n, --dry-run Simula senza cambiamenti
EOF
}

DRY_RUN=0
while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)   usage; exit 0 ;;
        -d|--debug)  DEBUG=1 ;;
        -n|--dry-run) DRY_RUN=1; warning "Modalità DRY RUN" ;;
        *) error "Opzione sconosciuta: $1"; usage; exit 2 ;;
    esac
    shift
done

main "$@"
```

### A2 — Script Backup con Rotazione

```bash
#!/usr/bin/env bash
# file: bash/backup_database.sh
# Script backup PostgreSQL con rotazione automatica

set -euo pipefail

readonly DB_HOST="${DB_HOST:-localhost}"
readonly DB_PORT="${DB_PORT:-5432}"
readonly DB_NAME="${DB_NAME:?Variabile DB_NAME obbligatoria}"
readonly DB_USER="${DB_USER:?Variabile DB_USER obbligatoria}"
readonly BACKUP_DIR="${BACKUP_DIR:-/var/backups/postgresql}"
readonly RETENTION_DAYS="${RETENTION_DAYS:-7}"
readonly LOG_FILE="/var/log/backup_db.log"

log() { echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ") $1 ${*:2}" | tee -a "${LOG_FILE}"; }

main() {
    local timestamp
    timestamp="$(date +"%Y%m%d_%H%M%S")"
    local backup_file="${BACKUP_DIR}/${DB_NAME}_${timestamp}.sql.gz"
    
    mkdir -p "${BACKUP_DIR}"
    log "INFO" "Inizio backup: ${DB_NAME} → ${backup_file}"
    
    # Backup con pg_dump + compressione in pipeline
    PGPASSWORD="${DB_PASSWORD:?}" pg_dump \
        --host="${DB_HOST}" \
        --port="${DB_PORT}" \
        --username="${DB_USER}" \
        --format=plain \
        --no-password \
        "${DB_NAME}" | gzip -9 > "${backup_file}"
    
    local dimensione
    dimensione="$(du -sh "${backup_file}" | cut -f1)"
    log "INFO" "Backup completato: ${dimensione} → ${backup_file}"
    
    # Verifica integrità (decomprime l'header)
    if ! gzip -t "${backup_file}"; then
        log "ERROR" "Backup corrotto: ${backup_file}"
        rm -f "${backup_file}"
        exit 1
    fi
    log "INFO" "Integrità verificata"
    
    # Rotazione: rimuove backup più vecchi di RETENTION_DAYS giorni
    local eliminati
    eliminati=$(find "${BACKUP_DIR}" -name "${DB_NAME}_*.sql.gz" \
        -mtime "+${RETENTION_DAYS}" -delete -print | wc -l)
    log "INFO" "Rotazione: eliminati ${eliminati} backup > ${RETENTION_DAYS} giorni"
    
    # Conta backup rimanenti
    local rimasti
    rimasti=$(find "${BACKUP_DIR}" -name "${DB_NAME}_*.sql.gz" | wc -l)
    log "INFO" "Backup presenti: ${rimasti}"
}

main
```

---

## PART B — Script Python Strutturati

### B1 — Template Python Standard

```python
#!/usr/bin/env python3
# file: python/template_python.py
"""
Template Python per automazioni production-grade.
Principi: argparse, logging strutturato, exit codes, gestione errori.
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# ─── Logging strutturato ──────────────────────────────────────────────────────

def configura_logging(livello: str = "INFO", log_file: Optional[Path] = None) -> logging.Logger:
    """
    Configura logging JSON con rotazione opzionale.
    Usa %(filename)s:%(lineno)d per tracciabilità nel codice.
    """
    import json
    
    class JsonFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            log_entry = {
                "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%SZ"),
                "level": record.levelname,
                "logger": record.name,
                "msg": record.getMessage(),
                "file": f"{record.filename}:{record.lineno}",
            }
            if record.exc_info:
                log_entry["exception"] = self.formatException(record.exc_info)
            return json.dumps(log_entry)
    
    logger = logging.getLogger("automazione")
    logger.setLevel(getattr(logging, livello.upper()))
    
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stderr)]
    
    if log_file:
        from logging.handlers import RotatingFileHandler
        handlers.append(RotatingFileHandler(
            log_file,
            maxBytes=50 * 1024 * 1024,  # 50 MB
            backupCount=5,
            encoding="utf-8",
        ))
    
    formatter = JsonFormatter()
    for handler in handlers:
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger


# ─── Lock file ────────────────────────────────────────────────────────────────

class LockFile:
    """Context manager per lock file — previene esecuzioni parallele."""

    def __init__(self, path: Path):
        self.path = path
        self._owned = False

    def __enter__(self) -> "LockFile":
        if self.path.exists():
            pid_str = self.path.read_text().strip()
            try:
                pid = int(pid_str)
                os.kill(pid, 0)  # Controlla se il PID è vivo (0 = no segnale)
                raise RuntimeError(
                    f"Script già in esecuzione (PID {pid}). Lock: {self.path}"
                )
            except (ProcessLookupError, PermissionError):
                # PID non esiste o non accessibile → lock stale
                logging.warning("Lock stale (PID %s) rimosso", pid_str)
        
        self.path.write_text(str(os.getpid()))
        self._owned = True
        return self

    def __exit__(self, *args):
        if self._owned and self.path.exists():
            self.path.unlink()


# ─── Config da ambiente ───────────────────────────────────────────────────────

@dataclass
class Config:
    """Configurazione da variabili d'ambiente (no hard-code!)."""
    input_dir: Path
    output_dir: Path
    db_url: str
    max_workers: int = 4
    dry_run: bool = False
    
    @classmethod
    def da_env(cls) -> "Config":
        """Crea Config dalle variabili d'ambiente."""
        missing = []
        for required in ["INPUT_DIR", "OUTPUT_DIR", "DATABASE_URL"]:
            if not os.environ.get(required):
                missing.append(required)
        
        if missing:
            raise EnvironmentError(f"Variabili d'ambiente mancanti: {', '.join(missing)}")
        
        return cls(
            input_dir=Path(os.environ["INPUT_DIR"]),
            output_dir=Path(os.environ["OUTPUT_DIR"]),
            db_url=os.environ["DATABASE_URL"],
            max_workers=int(os.environ.get("MAX_WORKERS", "4")),
            dry_run=os.environ.get("DRY_RUN", "0") == "1",
        )


# ─── Logica principale ────────────────────────────────────────────────────────

def processa_file(path: Path, config: Config) -> dict:
    """Processa un singolo file — restituisce risultato o solleva eccezione."""
    logger = logging.getLogger("automazione")
    
    if not path.exists():
        raise FileNotFoundError(f"File non trovato: {path}")
    if not path.is_file():
        raise ValueError(f"Non è un file: {path}")
    
    logger.debug("Processing: %s", path.name)
    
    if config.dry_run:
        return {"file": str(path), "status": "dry_run_skip"}
    
    # Logica effettiva...
    start = time.monotonic()
    time.sleep(0.001)  # Simula elaborazione
    
    return {
        "file": str(path),
        "status": "ok",
        "bytes": path.stat().st_size,
        "durata_ms": int((time.monotonic() - start) * 1000),
    }


def main(args: argparse.Namespace) -> int:
    """
    Entry point — ritorna exit code:
    0 = successo
    1 = errore durante l'elaborazione
    2 = errore di configurazione
    """
    logger = configura_logging(
        livello="DEBUG" if args.debug else "INFO",
        log_file=Path(args.log_file) if args.log_file else None,
    )
    
    try:
        config = Config.da_env()
    except EnvironmentError as e:
        logger.error("Configurazione non valida: %s", e)
        return 2
    
    if args.dry_run:
        config.dry_run = True
        logger.info("Modalità DRY RUN — nessun cambiamento reale")
    
    lock_path = Path("/tmp/automazione.lock")
    
    try:
        with LockFile(lock_path):
            logger.info("Avvio elaborazione. Input: %s", config.input_dir)
            
            files = list(config.input_dir.glob("*.csv")) if config.input_dir.exists() else []
            logger.info("File trovati: %d", len(files))
            
            ok = 0
            errori = 0
            
            for f in files:
                try:
                    result = processa_file(f, config)
                    ok += 1
                    logger.debug("OK: %s", result)
                except Exception as e:
                    errori += 1
                    logger.error("FAIL: %s — %s", f.name, e)
            
            logger.info("Completato: %d ok, %d errori", ok, errori)
            return 0 if errori == 0 else 1
    
    except RuntimeError as e:
        logger.error("%s", e)
        return 3


# ─── CLI ─────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Script automazione template",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--debug", action="store_true", help="Abilita log debug")
    parser.add_argument("--dry-run", action="store_true", help="Simula senza cambiamenti")
    parser.add_argument("--log-file", help="Path file di log (opzionale)")
    return parser.parse_args()


if __name__ == "__main__":
    sys.exit(main(parse_args()))
```

---

## PART C — Scheduling

### C1 — Cron System

```bash
# ─── Gestione crontab ────────────────────────────────────────────────────────

# Visualizza crontab corrente
crontab -l

# Modifica
crontab -e

# Formato: minuto ora giorno mese giorno_settimana comando
# ┌──────── minuto (0-59)
# │ ┌────── ora (0-23)
# │ │ ┌──── giorno del mese (1-31)
# │ │ │ ┌── mese (1-12)
# │ │ │ │ ┌ giorno della settimana (0-7, 0=domenica=7)
# │ │ │ │ │
# * * * * *  /path/to/command

# Esempi pratici:
# Backup ogni notte alle 2:30
# 30 2 * * * /opt/automazione/backup_database.sh >> /var/log/backup.log 2>&1

# Report ogni lunedì mattina alle 8:00
# 0 8 * * 1 /opt/automazione/report_vendite.sh

# Sync ogni 15 minuti (attenzione: usa lock file!)
# */15 * * * * flock -n /tmp/sync.lock /opt/automazione/sync_crm.sh

# Pulizia temporanei ogni domenica alle 4:00
# 0 4 * * 0 find /tmp/automazione -mtime +7 -delete

# ─── Cron best practice ───────────────────────────────────────────────────────
# 1. SEMPRE redirect output: >> log 2>&1
# 2. Usa percorsi ASSOLUTI (cron non ha PATH normale)
# 3. Imposta MAILTO per ricevere errori via email: MAILTO=ops@azienda.it
# 4. Usa flock per lock file atomico o implementa il tuo
# 5. Testa lo script manualmente prima di schedularlo in cron
# 6. Preferisci systemd timer per nuovi servizi (più robusto di cron)

# File cron in /etc/cron.d/ (root, con utente esplicito):
cat > /etc/cron.d/automazione-backup << 'EOF'
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
MAILTO=ops@azienda.it

# Backup notturno
30 2 * * * ansible /opt/automazione/backup_database.sh
EOF
```

### C2 — schedule (Python) — Scheduling Semplice In-Process

```python
#!/usr/bin/env python3
# file: scheduling/schedule_semplice.py
"""
schedule: scheduling Python semplice per script long-running.
Perfetto per: worker monoliti, task senza persistenza, prototipi.
Limitazione: se il processo si riavvia, perde lo stato dei job.
"""
from __future__ import annotations

import logging
import time
import signal
import threading
from typing import Callable

import schedule

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ─── Flag di shutdown graceful ────────────────────────────────────────────────

_running = threading.Event()
_running.set()  # True = in esecuzione


def shutdown_handler(signum, frame):
    logger.info("Segnale %d ricevuto — shutdown graceful in corso", signum)
    _running.clear()


signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)


# ─── Task definizioni ─────────────────────────────────────────────────────────

def backup_giornaliero():
    """Task backup — eseguito ogni giorno alle 02:30."""
    logger.info("Inizio backup giornaliero")
    try:
        # Chiama script bash o logica Python
        time.sleep(0.1)  # Simula backup
        logger.info("Backup completato")
    except Exception:
        logger.exception("Backup fallito")
        # NON sollevare: schedule cancella il job se solleva


def sync_crm():
    """Task sincronizzazione CRM — ogni 15 minuti."""
    logger.info("Sync CRM")
    # Logica sync...


def report_settimanale():
    """Report ogni lunedì alle 08:00."""
    logger.info("Generazione report settimanale")
    # Genera Excel/PDF...


def pulizia_temporanei():
    """Pulizia file temporanei ogni domenica."""
    import shutil
    from pathlib import Path
    logger.info("Pulizia temporanei")
    # shutil.rmtree con gestione errori...


# ─── Configurazione schedule ──────────────────────────────────────────────────

def configura_schedule():
    """Registra tutti i job nel scheduler."""
    schedule.every().day.at("02:30").do(backup_giornaliero).tag("backup")
    schedule.every(15).minutes.do(sync_crm).tag("sync")
    schedule.every().monday.at("08:00").do(report_settimanale).tag("report")
    schedule.every().sunday.at("04:00").do(pulizia_temporanei).tag("cleanup")
    
    logger.info("Schedule configurato: %d job", len(schedule.jobs))
    for job in schedule.jobs:
        logger.info("  %s → prossima esecuzione: %s", job.tags, job.next_run)


# ─── Loop principale ──────────────────────────────────────────────────────────

def run():
    """Loop di esecuzione — si ferma su SIGTERM/SIGINT."""
    configura_schedule()
    logger.info("Worker avviato — attesa job schedulati")
    
    while _running.is_set():
        schedule.run_pending()
        # Calcola tempo al prossimo job per non spinare inutilmente
        idle_seconds = schedule.idle_seconds()
        if idle_seconds is not None and idle_seconds > 0:
            time.sleep(min(idle_seconds, 1.0))  # Max 1s di attesa
        else:
            time.sleep(0.1)
    
    logger.info("Worker fermato")


if __name__ == "__main__":
    run()
```

### C3 — APScheduler (Python) — Scheduling Avanzato con Persistenza

```python
#!/usr/bin/env python3
# file: scheduling/apscheduler_avanzato.py
"""
APScheduler: scheduling avanzato con persistenza Redis.
Adatto per: microservizi, task che devono sopravvivere al riavvio,
scheduling dinamico (add/remove job a runtime).
"""
from __future__ import annotations

import logging
import os
import signal
import time
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def on_job_executed(event):
    """Callback: eseguito dopo ogni job completato con successo."""
    logger.info("Job completato: %s (durata: %.2fs)",
                event.job_id, event.retval or 0)


def on_job_error(event):
    """Callback: eseguito dopo ogni job fallito."""
    logger.error("Job fallito: %s — %s", event.job_id, event.exception)


def crea_scheduler(redis_url: str) -> BackgroundScheduler:
    """
    Crea scheduler con:
    - RedisJobStore: job persistiti su Redis (sopravvivono al restart)
    - ThreadPoolExecutor: task I/O-bound (HTTP, filesystem)
    - ProcessPoolExecutor: task CPU-bound (calcoli, compressione)
    """
    jobstores = {
        "default": RedisJobStore(
            jobs_key="apscheduler:jobs",
            run_times_key="apscheduler:run_times",
            url=redis_url,
        )
    }
    
    executors = {
        "default": ThreadPoolExecutor(max_workers=10),
        "processpool": ProcessPoolExecutor(max_workers=4),
    }
    
    job_defaults = {
        "coalesce": True,    # Esegue una sola volta se in ritardo (non accumula)
        "max_instances": 1,  # Una sola istanza parallela per job
        "misfire_grace_time": 300,  # Esegui job in ritardo fino a 5 minuti
    }
    
    scheduler = BackgroundScheduler(
        jobstores=jobstores,
        executors=executors,
        job_defaults=job_defaults,
        timezone="Europe/Rome",
    )
    
    # Registra listener per metriche
    scheduler.add_listener(on_job_executed, EVENT_JOB_EXECUTED)
    scheduler.add_listener(on_job_error, EVENT_JOB_ERROR)
    
    return scheduler


# ─── Task ─────────────────────────────────────────────────────────────────────

def elabora_ordini_pendenti():
    """Processa ordini non elaborati nel DB."""
    logger.info("[ordini] Elaborazione ordini pendenti")
    # Query DB, processa, update status...


def invia_report_direttori():
    """Report direzione ogni lunedì 9:00."""
    logger.info("[report] Generazione report direttori")
    # Genera PDF, invia email...


def aggiorna_cambio_valute():
    """Aggiorna tassi di cambio ogni ora."""
    logger.info("[forex] Aggiornamento cambio valute")
    # httpx.get("https://api.exchangerates.io/...")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    scheduler = crea_scheduler(redis_url)
    
    # Aggiungi job (se non esistono già nel RedisJobStore)
    # replace_existing=True: aggiorna se già presente
    scheduler.add_job(
        func=elabora_ordini_pendenti,
        trigger="interval",
        minutes=5,
        id="elabora_ordini",
        name="Elabora ordini pendenti",
        replace_existing=True,
    )
    
    scheduler.add_job(
        func=invia_report_direttori,
        trigger="cron",
        day_of_week="mon",
        hour=9, minute=0,
        id="report_settimanale",
        name="Report settimanale direttori",
        replace_existing=True,
    )
    
    scheduler.add_job(
        func=aggiorna_cambio_valute,
        trigger="cron",
        minute=0,  # Ogni ora all'ora esatta
        id="forex_update",
        replace_existing=True,
    )
    
    scheduler.start()
    logger.info("Scheduler avviato con %d job", len(scheduler.get_jobs()))
    
    # Shutdown graceful
    stop_event = __import__("threading").Event()
    signal.signal(signal.SIGTERM, lambda *_: stop_event.set())
    signal.signal(signal.SIGINT, lambda *_: stop_event.set())
    
    try:
        stop_event.wait()
    finally:
        logger.info("Shutdown scheduler...")
        scheduler.shutdown(wait=True)
        logger.info("Scheduler fermato")


if __name__ == "__main__":
    main()
```

---

## PART D — systemd Unit File

### D1 — Conversione Script in Servizio systemd

```ini
# file: systemd/automazione-scheduler.service
# Copia in: /etc/systemd/system/automazione-scheduler.service
# Poi: systemctl daemon-reload && systemctl enable --now automazione-scheduler

[Unit]
Description=Scheduler Automazioni Aziendali
Documentation=https://wiki.interno/automazioni
After=network-online.target redis.service
Wants=network-online.target
Requires=redis.service

[Service]
Type=simple
User=automazione
Group=automazione
WorkingDirectory=/opt/automazione

# Variabili d'ambiente da file (non hardcoded!)
EnvironmentFile=/etc/automazione/env

# Comando
ExecStart=/opt/automazione/venv/bin/python -m scheduling.apscheduler_avanzato

# Restart automatico
Restart=always
RestartSec=10
StartLimitIntervalSec=300
StartLimitBurst=3

# Shutdown graceful: manda SIGTERM, attendi 30s, poi SIGKILL
TimeoutStopSec=30
KillMode=mixed
KillSignal=SIGTERM

# Log su journald (visualizza con: journalctl -u automazione-scheduler -f)
StandardOutput=journal
StandardError=journal
SyslogIdentifier=automazione

# Sicurezza
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=/opt/automazione/data /var/log/automazione
PrivateTmp=yes

[Install]
WantedBy=multi-user.target
```

```bash
# file per /etc/automazione/env (chmod 640, group=automazione)
# NON committare questo file! Gestirlo con Ansible Vault o segreti CI

DATABASE_URL=postgresql://app:CHANGEME@localhost:5432/produzione
REDIS_URL=redis://localhost:6379/0
INPUT_DIR=/opt/automazione/data/input
OUTPUT_DIR=/opt/automazione/data/output
MAX_WORKERS=4
LOG_FILE=/var/log/automazione/scheduler.log
```

---

## Esercizi

### Esercizio 1 — Bash Idempotente (20 min)

Riscrivi questo script in modo idempotente con lock file e logging:

```bash
#!/bin/bash
# PROBLEMA: non idempotente, nessun error handling
mkdir /opt/app
cp config.yml /opt/app/
chown www-data /opt/app
```

### Esercizio 2 — Schedule con Error Recovery (20 min)

Aggiungi a `schedule_semplice.py`:
- Decoratore `@con_retry(max=3)` che ritenta un task fallito dopo 60s
- Contatore globale di fallimenti consecutivi per ogni tag
- Alert log se un job fallisce 3 volte di seguito

### Esercizio 3 — systemd Timer vs Cron (15 min)

Crea un `automazione-backup.timer` (systemd timer) equivalente al cron job:
```
30 2 * * * /opt/automazione/backup_database.sh
```

Hint:
```ini
[Timer]
OnCalendar=*-*-* 02:30:00
Persistent=true  # Recupera missioni se il sistema era spento
```

---

## Riferimenti

- Bash Strict Mode: http://redsymbol.net/articles/unofficial-bash-strict-mode/
- schedule docs: https://schedule.readthedocs.io/
- APScheduler docs: https://apscheduler.readthedocs.io/
- systemd timer: https://www.freedesktop.org/software/systemd/man/systemd.timer.html
- Modulo sorgente: `03-scripting-automazione.md`
