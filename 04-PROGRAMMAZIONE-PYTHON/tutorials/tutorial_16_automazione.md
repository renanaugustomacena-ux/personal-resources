# Tutorial 16 — Automazione in Python: Scheduling, File System, Processi

> **Companion a:** `16-automazione.md`
> **Scope:** schedule, APScheduler, watchdog, subprocess, shutil, pathlib, automazione email/file/sistema
> **Prerequisiti:** `tutorial_01_fondamenti_linguaggio.md`, `tutorial_10_programmazione_asincrona.md`
> **Durata stimata:** 14-18 ore
> **Stack:** Python 3.12+, APScheduler 3.x, watchdog 4.x, structlog

---

## Mappa concettuale

```
Automazione Python
│
├── Scheduling
│   ├── schedule — semplice, in-process
│   ├── APScheduler — robusto, persistente, trigger multipli
│   │   ├── Trigger: interval, cron, date
│   │   ├── Job Store: memoria, SQLAlchemy, Redis
│   │   └── Executor: thread, process, asyncio
│   └── cron (OS) — via subprocess/systemd
│
├── File System
│   ├── pathlib.Path — API moderna per percorsi
│   ├── shutil — copia, spostamento, archivi
│   ├── watchdog — monitoraggio modifiche fs
│   └── tempfile — file/directory temporanei
│
├── Processi e Shell
│   ├── subprocess — esecuzione comandi
│   ├── os.environ — variabili ambiente
│   └── psutil — processi, CPU, memoria
│
├── Email e Notifiche
│   ├── smtplib — SMTP standard
│   ├── email.message — costruzione email
│   └── MIMEMultipart — allegati, HTML
│
└── Pattern avanzati
    ├── Pipeline di task
    ├── Retry automatico
    ├── Logging strutturato con correlation ID
    └── Health check periodico
```

---

# Parte A — Scheduling

---

## A1. schedule: scheduling semplice in-process

```python
import schedule
import time
import logging

logger = logging.getLogger(__name__)

def backup_database() -> None:
    logger.info("Avvio backup database")
    # ... logica backup
    logger.info("Backup completato")

def invia_report() -> None:
    logger.info("Generazione report giornaliero")
    # ... genera e invia report

def pulizia_log() -> None:
    logger.info("Pulizia log vecchi")

# Definizione schedule
schedule.every(1).hours.do(backup_database)
schedule.every().day.at("08:00").do(invia_report)
schedule.every().monday.at("09:00").do(invia_report)
schedule.every().week.do(pulizia_log)
schedule.every(30).minutes.do(lambda: logger.info("Health check OK"))

# Loop principale
def avvia_scheduler() -> None:
    logger.info("Scheduler avviato")
    while True:
        schedule.run_pending()
        time.sleep(1)   # check ogni secondo

if __name__ == "__main__":
    import signal
    running = True
    def stop(sig, frame):
        global running
        running = False
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    logger.info("Scheduler avviato, Ctrl+C per fermare")
    while running:
        schedule.run_pending()
        time.sleep(1)
    logger.info("Scheduler fermato")
```

> **Analogia:** `schedule` è come una sveglia multi-allarme sul comodino. Imposti quando suonare e cosa fare, e il loop `run_pending()` controlla ogni secondo se è ora. Semplice e affidabile per processi singoli. `APScheduler` è invece come un sistema di automazione aziendale: può eseguire job su più macchine, ricordare i job anche dopo il riavvio, e gestire job falliti.

---

## A2. APScheduler: scheduling professionale

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
import asyncio
import logging

logger = logging.getLogger(__name__)

# Scheduler asincrono (per uso con asyncio)
async def crea_scheduler_async() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="Europe/Rome")

    def listener_eventi(event):
        if event.exception:
            logger.error(f"Job {event.job_id} fallito: {event.exception}")
        else:
            logger.info(f"Job {event.job_id} completato, valore: {event.retval}")

    scheduler.add_listener(listener_eventi, EVENT_JOB_ERROR | EVENT_JOB_EXECUTED)

    return scheduler

async def job_asincrono() -> str:
    await asyncio.sleep(1)
    logger.info("Job asincrono eseguito")
    return "completato"

def job_sincrono(parametro: str) -> None:
    logger.info(f"Job sincrono con parametro: {parametro}")

async def main_con_scheduler():
    scheduler = await crea_scheduler_async()

    # Trigger interval — ogni N unità di tempo
    scheduler.add_job(
        job_asincrono,
        trigger=IntervalTrigger(minutes=5),
        id="job_intervallo",
        name="Job ogni 5 minuti",
        max_instances=1,          # non più di 1 istanza contemporanea
        coalesce=True,            # raggruppa esecuzioni mancate
        misfire_grace_time=60,    # tolleranza ritardo in secondi
    )

    # Trigger cron — espressione cron standard
    scheduler.add_job(
        job_sincrono,
        args=["dati_giornalieri"],
        trigger=CronTrigger(hour=8, minute=0, day_of_week="mon-fri"),
        id="report_mattina",
        name="Report mattutino",
    )

    # Trigger date — una volta sola
    from apscheduler.triggers.date import DateTrigger
    from datetime import datetime, timedelta
    scheduler.add_job(
        job_sincrono,
        args=["pulizia_mensile"],
        trigger=DateTrigger(run_date=datetime.now() + timedelta(seconds=10)),
        id="una_tantum",
    )

    scheduler.start()
    logger.info("Scheduler APScheduler avviato")

    try:
        await asyncio.Event().wait()   # mantieni in vita
    finally:
        scheduler.shutdown()

asyncio.run(main_con_scheduler())
```

---

# Parte B — File System

---

## B1. pathlib: gestione percorsi

```python
from pathlib import Path
import shutil

# Percorso corrente e navigazione
p = Path(".")
home = Path.home()
cwd = Path.cwd()

# Costruzione percorsi — cross-platform
progetto = Path("/progetti") / "mio-progetto" / "src"
config = Path.home() / ".config" / "myapp" / "settings.toml"

# Operazioni su file
log_file = Path("logs") / "app.log"
log_file.parent.mkdir(parents=True, exist_ok=True)   # crea directory se non esiste
log_file.touch()   # crea file se non esiste

# Lettura e scrittura
log_file.write_text("Prima riga\n", encoding="utf-8")
contenuto = log_file.read_text(encoding="utf-8")

# Append
with log_file.open("a", encoding="utf-8") as f:
    f.write("Seconda riga\n")

# Glob — ricerca file
py_files = list(Path(".").glob("**/*.py"))
test_files = list(Path(".").glob("tests/test_*.py"))

# Informazioni file
if log_file.exists():
    stat = log_file.stat()
    print(f"Dimensione: {stat.st_size} bytes")
    print(f"Modificato: {stat.st_mtime}")
    print(f"Estensione: {log_file.suffix}")
    print(f"Nome: {log_file.name}")
    print(f"Stem: {log_file.stem}")

# Rinomina e spostamento
nuovo_nome = log_file.with_suffix(".bak")
log_file.rename(nuovo_nome)   # spostamento nella stessa partizione

# Copia con shutil
shutil.copy2(nuovo_nome, "/backup/app.log.bak")   # copia con metadati

# Eliminazione
nuovo_nome.unlink()   # elimina file
# shutil.rmtree(directory)   # elimina directory ricorsivamente

# Directory temporanea
import tempfile
with tempfile.TemporaryDirectory() as tmpdir:
    tmp_path = Path(tmpdir)
    (tmp_path / "test.txt").write_text("temporaneo")
    # Eliminata automaticamente all'uscita del with
```

---

## B2. watchdog: monitoraggio modifiche filesystem

```python
from watchdog.observers import Observer
from watchdog.events import (
    FileSystemEventHandler,
    FileCreatedEvent,
    FileModifiedEvent,
    FileDeletedEvent,
    FileMovedEvent,
)
from pathlib import Path
import time
import logging

logger = logging.getLogger(__name__)

class GestoreModifiche(FileSystemEventHandler):
    def __init__(self, cartella_monitorata: Path) -> None:
        self.cartella = cartella_monitorata
        self._processati: set[str] = set()

    def on_created(self, event: FileCreatedEvent) -> None:
        if event.is_directory:
            return
        percorso = Path(event.src_path)
        if percorso.suffix == ".csv":
            logger.info(f"Nuovo CSV rilevato: {percorso.name}")
            self._elabora_csv(percorso)

    def on_modified(self, event: FileModifiedEvent) -> None:
        if event.is_directory:
            return
        percorso = Path(event.src_path)
        logger.debug(f"Modificato: {percorso.name}")

    def on_deleted(self, event: FileDeletedEvent) -> None:
        logger.warning(f"Eliminato: {event.src_path}")

    def on_moved(self, event: FileMovedEvent) -> None:
        logger.info(f"Spostato: {event.src_path} → {event.dest_path}")

    def _elabora_csv(self, percorso: Path) -> None:
        chiave = str(percorso)
        if chiave in self._processati:
            return
        self._processati.add(chiave)
        try:
            # Attendi che il file sia completamente scritto
            dimensione_precedente = -1
            while True:
                dimensione_attuale = percorso.stat().st_size
                if dimensione_attuale == dimensione_precedente:
                    break
                dimensione_precedente = dimensione_attuale
                time.sleep(0.1)
            logger.info(f"Elaboro {percorso.name} ({dimensione_attuale} bytes)")
            # ... logica elaborazione
        except Exception as e:
            logger.error(f"Errore elaborazione {percorso}: {e}")

def monitora_cartella(percorso: str, ricorsivo: bool = False) -> None:
    cartella = Path(percorso)
    cartella.mkdir(parents=True, exist_ok=True)

    handler = GestoreModifiche(cartella)
    observer = Observer()
    observer.schedule(handler, str(cartella), recursive=ricorsivo)
    observer.start()

    logger.info(f"Monitoraggio avviato su {cartella}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    logger.info("Monitoraggio fermato")
```

---

# Parte C — Subprocess e processi

---

## C1. subprocess: eseguire comandi di sistema

```python
import subprocess
import shlex
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def esegui_comando(
    comando: str | list[str],
    cwd: Path | None = None,
    env: dict | None = None,
    timeout: float = 60.0,
    check: bool = True,
) -> tuple[str, str, int]:
    """Esegui comando esterno in modo sicuro."""
    if isinstance(comando, str):
        args = shlex.split(comando)
    else:
        args = comando

    try:
        risultato = subprocess.run(
            args,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=check,
        )
        return risultato.stdout, risultato.stderr, risultato.returncode
    except subprocess.TimeoutExpired:
        raise TimeoutError(f"Comando scaduto dopo {timeout}s: {' '.join(args)}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Comando fallito (exit {e.returncode}): {e.stderr}")
        raise

def esegui_git(repo: Path, *args: str) -> str:
    """Esegui comando git su un repository."""
    stdout, stderr, code = esegui_comando(
        ["git", *args],
        cwd=repo,
    )
    return stdout.strip()

# Comandi di sistema comuni
def df_disco() -> dict[str, str]:
    """Uso disco delle partizioni."""
    stdout, _, _ = esegui_comando("df -h --output=source,size,used,avail,pcent,target")
    righe = stdout.strip().split("\n")[1:]   # salta header
    risultato = {}
    for riga in righe:
        parti = riga.split()
        if len(parti) >= 6:
            risultato[parti[5]] = {"size": parti[1], "used": parti[2], "avail": parti[3], "pct": parti[4]}
    return risultato

# Processo con output in streaming
def esegui_con_streaming(comando: list[str]) -> None:
    """Mostra output del processo in tempo reale."""
    processo = subprocess.Popen(
        comando,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert processo.stdout is not None
    for riga in processo.stdout:
        print(riga, end="")
    processo.wait()
    if processo.returncode != 0:
        raise RuntimeError(f"Processo terminato con exit code {processo.returncode}")
```

---

# Parte D — Pipeline di automazione completa

---

## D1. Pipeline ETL con scheduling e notifiche

```python
import asyncio
import logging
import smtplib
from email.message import EmailMessage
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class ConfigNotifiche:
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_pass: str
    destinatari: list[str]

def invia_notifica(
    config: ConfigNotifiche,
    soggetto: str,
    corpo: str,
    allegato: Path | None = None,
) -> None:
    msg = EmailMessage()
    msg["Subject"] = soggetto
    msg["From"] = config.smtp_user
    msg["To"] = ", ".join(config.destinatari)
    msg.set_content(corpo)

    if allegato and allegato.exists():
        dati = allegato.read_bytes()
        msg.add_attachment(dati, maintype="application", subtype="octet-stream", filename=allegato.name)

    with smtplib.SMTP(config.smtp_host, config.smtp_port) as smtp:
        smtp.starttls()
        smtp.login(config.smtp_user, config.smtp_pass)
        smtp.send_message(msg)
    logger.info(f"Notifica inviata a {config.destinatari}")

async def pipeline_giornaliera(
    sorgente: Path,
    destinazione: Path,
    config_notifiche: ConfigNotifiche,
) -> None:
    """Pipeline ETL giornaliera: estrai → trasforma → carica → notifica."""
    inizio = datetime.now()
    errori: list[str] = []

    try:
        # 1. Verifica sorgente
        if not sorgente.exists():
            raise FileNotFoundError(f"Sorgente non trovata: {sorgente}")

        # 2. Backup prima di elaborare
        backup = sorgente.with_suffix(".bak")
        import shutil
        shutil.copy2(sorgente, backup)
        logger.info(f"Backup creato: {backup}")

        # 3. Elaborazione (qui va la logica reale)
        await asyncio.sleep(0.1)  # placeholder
        destinazione.write_text(f"Elaborato il {inizio.isoformat()}")
        logger.info(f"Elaborazione completata → {destinazione}")

        # 4. Notifica successo
        durata = (datetime.now() - inizio).total_seconds()
        invia_notifica(
            config_notifiche,
            f"[OK] Pipeline completata in {durata:.1f}s",
            f"File elaborato: {sorgente.name}\nOutput: {destinazione.name}\nDurata: {durata:.1f}s",
            allegato=destinazione,
        )

    except Exception as e:
        errori.append(str(e))
        logger.error(f"Pipeline fallita: {e}")
        try:
            invia_notifica(
                config_notifiche,
                f"[ERRORE] Pipeline fallita",
                f"Errore: {e}\nSorgente: {sorgente}\nOra: {inizio.isoformat()}",
            )
        except Exception as email_err:
            logger.error(f"Anche l'invio della notifica ha fallito: {email_err}")
        raise
```

---

# Parte E — Riepilogo

## Strumenti per ogni esigenza

| Esigenza | Strumento |
|---|---|
| Job ricorrenti semplici | `schedule` |
| Job con cron, persistenza, async | `APScheduler` |
| Monitoraggio file | `watchdog` |
| Percorsi file cross-platform | `pathlib.Path` |
| Copia/spostamento/zip | `shutil` |
| Comandi di sistema | `subprocess.run()` |
| Processi, CPU, RAM | `psutil` |
| Email | `smtplib` + `email` |
| File temp | `tempfile.TemporaryDirectory()` |

## Anti-pattern

- **`os.system("rm -rf /tmp/data")`** — non cattura output né errori; usare `subprocess.run()` con `check=True`
- **Costruire comandi con f-string** — rischio injection; passare lista di argomenti a `subprocess`
- **Polling breve senza sleep** — usa `watchdog` invece di controllare ogni 0.1s in un loop
- **Non verificare se il file è completo prima di elaborarlo** — vedi pattern `stat().st_size` nel watchdog

## Prossimi passi

- `tutorial_19_cli_tools.md` — CLI con Click e Typer
- `tutorial_21_design_patterns.md` — pattern per automazioni scalabili
