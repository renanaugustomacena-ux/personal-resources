---
corso: "Programmazione Python"
fase: "4 — Applicazioni Specializzate"
modulo: "16"
titolo: "Automazione con Python"
versione: "subprocess (stdlib) / paramiko 3.x / APScheduler 3.10+ / watchdog 4.x / fabric 3.x"
livello: "Intermedio"
prerequisiti:
  - "01-06 — Python Base"
  - "05 — Gestione File e I/O"
  - "07 — Error Handling e Logging"
obiettivi:
  - "Automatizzare task di sistema con subprocess e shutil"
  - "Gestire connessioni SSH e deployment remoto con paramiko e fabric"
  - "Schedulare job con APScheduler e cron expression"
  - "Monitorare filesystem con watchdog per trigger automatici"
  - "Costruire pipeline di automazione robuste con error handling"
  - "Integrare automazione Python con CI/CD e orchestratori"
tag: [automazione, subprocess, paramiko, fabric, APScheduler, watchdog, cron, DevOps]
---

# Automazione con Python — Guida Completa

> **Modulo 16** · **Aggiornamento:** 2026-05-24 · **Versione:** subprocess (stdlib) / paramiko 3.x / APScheduler 3.10+ / watchdog 4.x / fabric 3.x

> ### Obiettivi di apprendimento
>
> **Prerequisiti:** [Python Base](01-fondamenti-linguaggio.md), [Gestione File e I/O](05-gestione-file-io.md), [Error Handling](07-error-handling-e-logging.md)
>
> Al termine di questo modulo saprai:
> 1. Automatizzare task di sistema con `subprocess` e `shutil`
> 2. Gestire connessioni SSH e deployment remoto con paramiko e fabric
> 3. Schedulare job con APScheduler e cron expression
> 4. Monitorare filesystem con watchdog per trigger automatici
> 5. Costruire pipeline di automazione robuste con error handling e retry
> 6. Integrare automazione Python con CI/CD e orchestratori
>
> **Tempo stimato:** 6-8 ore · **Livello:** Intermedio

## Idee guida
1. **`subprocess.run` > `os.system`.** Capture output, errors.
2. **`schedule` library per cron-like in-process.**
3. **`watchdog` per file system events.**
4. **`pyinfra` python-based config mgmt; alternative Ansible.**

### Mappa concettuale

```
                      ┌──────────────────────┐
                      │   AUTOMAZIONE PYTHON  │
                      └──────────┬───────────┘
          ┌──────────────────────┼──────────────────────┐
          ▼                      ▼                      ▼
 ┌─────────────────┐   ┌─────────────────┐    ┌─────────────────┐
 │  File System     │   │  Sistema OS      │    │  Rete & Remoto  │
 │  pathlib         │   │  subprocess      │    │  paramiko SSH   │
 │  watchdog        │   │  psutil          │    │  fabric 3.x     │
 │  shutil          │   │  os / platform   │    │  ansible-runner │
 └────────┬────────┘   └────────┬────────┘    └────────┬────────┘
          │                     │                      │
          ▼                     ▼                      ▼
 ┌─────────────────┐   ┌─────────────────┐    ┌─────────────────┐
 │  Scheduling      │   │  Email           │    │  Report          │
 │  APScheduler     │   │  smtplib         │    │  Jinja2 + PDF   │
 │  cron + Python   │   │  imaplib         │    │  openpyxl       │
 │  schedule        │   │  email (stdlib)  │    │  weasyprint     │
 └─────────────────┘   └─────────────────┘    └─────────────────┘
```


Python e il linguaggio di riferimento per l'automazione in ambito IT grazie alla sua sintassi leggibile, al vasto ecosistema di librerie e alla capacita di interagire con sistemi operativi, reti, servizi web e applicazioni desktop. Per un professionista IT — che si tratti di un system administrator, un network engineer o un DevOps engineer — Python rappresenta lo strumento ideale per eliminare le attivita ripetitive, ridurre gli errori umani e costruire flussi di lavoro affidabili e riproducibili. Questa guida copre in profondita ogni ambito dell'automazione: dal file system alla rete, dalla posta elettronica alla schedulazione, dall'Active Directory alla generazione di report.

---

## Indice

1. [Panoramica](#panoramica)
2. [Automazione File System](#automazione-file-system)
   - [pathlib per operazioni su file](#pathlib-per-operazioni-su-file)
   - [Rinomina batch, organizzazione e pulizia](#rinomina-batch-organizzazione-e-pulizia)
   - [Monitoraggio file con watchdog](#monitoraggio-file-con-watchdog)
   - [Sincronizzazione directory](#sincronizzazione-directory)
   - [Script di backup automatizzati](#script-di-backup-automatizzati)
3. [Automazione Sistema Operativo](#automazione-sistema-operativo)
   - [subprocess](#subprocess)
   - [os e platform](#os-e-platform)
   - [psutil](#psutil)
4. [Automazione Rete](#automazione-rete)
   - [paramiko (SSH)](#paramiko-ssh)
   - [netmiko](#netmiko)
   - [fabric](#fabric)
5. [Automazione Email](#automazione-email)
   - [smtplib](#smtplib)
   - [imaplib](#imaplib)
   - [Modulo email](#modulo-email)
6. [Automazione Web](#automazione-web)
7. [Scheduling](#scheduling)
   - [schedule](#schedule)
   - [APScheduler](#apscheduler)
   - [Cron + Python](#cron--python)
8. [Automazione Windows](#automazione-windows)
   - [pywin32](#pywin32)
   - [Integrazione PowerShell](#integrazione-powershell)
9. [Automazione Active Directory](#automazione-active-directory)
10. [Automazione Report](#automazione-report)
11. [Best Practices](#best-practices)
12. [Sicurezza di subprocess — shell=False e Sanitizzazione](#sicurezza-di-subprocess--shellfalse-e-sanitizzazione)
13. [Task Scheduling Avanzato — APScheduler e Cron](#task-scheduling-avanzato--apscheduler-e-cron)
14. [File System Monitoring Avanzato con watchdog](#file-system-monitoring-avanzato-con-watchdog)
15. [Fabric 3.x — Deploy e Orchestrazione Remota](#fabric-3x--deploy-e-orchestrazione-remota)
16. [ansible-runner — Automazione Infrastruttura da Python](#ansible-runner--automazione-infrastruttura-da-python)
17. [Script di System Administration](#script-di-system-administration)
18. [Automazione Processi Avanzata — pexpect e Signal Handling](#automazione-processi-avanzata--pexpect-e-signal-handling)
19. [Desktop Automation — pyautogui e pygetwindow](#desktop-automation--pyautogui-e-pygetwindow)
20. [Automazione Documenti — python-docx e pypdf](#automazione-documenti--python-docx-e-pypdf)
21. [Cloud Automation — boto3 e azure-sdk](#cloud-automation--boto3-e-azure-sdk)
22. [Sistemi di Notifica — Slack, Discord e Teams](#sistemi-di-notifica--slack-discord-e-teams)
23. [Data Pipeline Automation](#data-pipeline-automation)
24. [Gestione Configurazione per l'Automazione](#gestione-configurazione-per-lautomazione)
25. [Error Handling e Retry Pattern per l'Automazione](#error-handling-e-retry-pattern-per-lautomazione)
26. [Windows Task Scheduler da Python](#windows-task-scheduler-da-python)
27. [Browser Automation Avanzata — Playwright](#browser-automation-avanzata--playwright)
28. [FAQ](#faq)
29. [Esercizi](#esercizi)
30. [Letture](#letture)
31. [Glossario](#glossario)

---

## Panoramica

L'automazione consiste nell'eliminare l'intervento manuale da processi ripetitivi, delegando al software l'esecuzione di operazioni che altrimenti richiederebbero tempo, attenzione e un margine costante di errore umano. In ambito IT, le attivita che si prestano all'automazione sono innumerevoli: provisioning di utenti, backup di configurazioni, monitoraggio di risorse, distribuzione di report, gestione di dispositivi di rete, pulizia di file system.

Python si distingue dagli script Bash o PowerShell per diversi motivi:

- **Portabilita**: lo stesso script gira su Linux, macOS e Windows senza modifiche sostanziali.
- **Leggibilita**: la sintassi pulita rende gli script manutenibili anche a distanza di mesi.
- **Ecosistema**: migliaia di librerie coprono ogni esigenza, da SSH a LDAP, da Excel alla generazione di PDF.
- **Gestione errori**: il sistema di eccezioni consente di costruire automazioni robuste con retry, fallback e logging strutturato.
- **Integrazione**: Python si interfaccia facilmente con API REST, database, code di messaggi, servizi cloud.

### Casi d'uso tipici per professionisti IT

| Ambito | Esempio |
|--------|---------|
| File system | Pulizia automatica di log vecchi, organizzazione di file per data |
| Sistema operativo | Monitoraggio CPU/RAM con alert via email |
| Rete | Backup configurazioni switch e router ogni notte |
| Email | Invio report giornalieri con allegati Excel |
| Active Directory | Creazione massiva di utenti da file CSV |
| Web | Verifica disponibilita siti e API con notifiche |
| Report | Generazione automatica di PDF con grafici e tabelle |

---

## Automazione File System

### pathlib per operazioni su file

Il modulo `pathlib`, introdotto in Python 3.4, fornisce un'interfaccia orientata agli oggetti per la manipolazione dei percorsi del file system. Rispetto al vecchio `os.path`, `pathlib` offre una sintassi piu leggibile e un'API coerente.

```python
from pathlib import Path

# Percorsi e navigazione
home = Path.home()
progetto = Path("/opt/automazione/dati")
file_config = progetto / "config" / "settings.json"

# Informazioni sul file
print(file_config.exists())        # True/False
print(file_config.is_file())       # True/False
print(file_config.suffix)          # .json
print(file_config.stem)            # settings
print(file_config.parent)          # /opt/automazione/dati/config
print(file_config.stat().st_size)  # dimensione in byte

# Lettura e scrittura
contenuto = file_config.read_text(encoding="utf-8")
file_config.write_text('{"chiave": "valore"}', encoding="utf-8")

# Iterazione sui file di una directory
for f in progetto.iterdir():
    if f.is_file():
        print(f.name, f.stat().st_size)

# Glob pattern — ricerca ricorsiva
for log in progetto.rglob("*.log"):
    print(log)

# Creazione directory con parents
nuova_dir = progetto / "archivio" / "2026" / "03"
nuova_dir.mkdir(parents=True, exist_ok=True)
```

### Rinomina batch, organizzazione e pulizia

Uno degli scenari di automazione piu comuni e la rinomina massiva di file, l'organizzazione per tipo o data e la pulizia di file obsoleti.

```python
from pathlib import Path
from datetime import datetime, timedelta
import shutil

# --- Rinomina batch ---
# Rinomina tutti i file .jpeg in .jpg con prefisso sequenziale
cartella = Path("/dati/immagini")
for i, file in enumerate(sorted(cartella.glob("*.jpeg")), start=1):
    nuovo_nome = f"foto_{i:04d}.jpg"
    file.rename(file.parent / nuovo_nome)
    print(f"Rinominato: {file.name} -> {nuovo_nome}")


# --- Organizzazione per estensione ---
# Smista i file in sottocartelle per tipo
sorgente = Path("/home/utente/Download")
mapping_estensioni = {
    ".pdf": "Documenti",
    ".docx": "Documenti",
    ".xlsx": "Fogli_Calcolo",
    ".jpg": "Immagini",
    ".png": "Immagini",
    ".mp4": "Video",
    ".zip": "Archivi",
    ".tar.gz": "Archivi",
}

for file in sorgente.iterdir():
    if file.is_file():
        cartella_dest = mapping_estensioni.get(file.suffix.lower(), "Altro")
        dest = sorgente / cartella_dest
        dest.mkdir(exist_ok=True)
        shutil.move(str(file), str(dest / file.name))


# --- Pulizia file vecchi ---
# Elimina i file .log piu vecchi di 30 giorni
log_dir = Path("/var/log/applicazione")
soglia = datetime.now() - timedelta(days=30)

for log_file in log_dir.glob("*.log"):
    data_modifica = datetime.fromtimestamp(log_file.stat().st_mtime)
    if data_modifica < soglia:
        log_file.unlink()
        print(f"Eliminato: {log_file.name} (modificato il {data_modifica:%Y-%m-%d})")
```

### Monitoraggio file con watchdog

La libreria `watchdog` consente di monitorare il file system in tempo reale, eseguendo azioni quando vengono creati, modificati, spostati o eliminati file e directory.

```python
# pip install watchdog

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")


class GestoreEventi(FileSystemEventHandler):
    """Gestisce gli eventi del file system."""

    def on_created(self, event):
        if not event.is_directory:
            logging.info(f"File creato: {event.src_path}")
            # Logica personalizzata: elaborare il file, spostarlo, ecc.

    def on_modified(self, event):
        if not event.is_directory:
            logging.info(f"File modificato: {event.src_path}")

    def on_deleted(self, event):
        if not event.is_directory:
            logging.info(f"File eliminato: {event.src_path}")

    def on_moved(self, event):
        if not event.is_directory:
            logging.info(f"File spostato: {event.src_path} -> {event.dest_path}")


# Configurazione e avvio
percorso_monitorato = "/dati/ingresso"
gestore = GestoreEventi()
observer = Observer()
observer.schedule(gestore, percorso_monitorato, recursive=True)
observer.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()

observer.join()
```

Un caso d'uso concreto e il monitoraggio di una cartella di ingresso dove vengono depositati file CSV: lo script li rileva, li elabora e li sposta in una cartella di archivio.

### Sincronizzazione directory

La sincronizzazione di directory e fondamentale per mantenere copie allineate di dati su percorsi diversi — ad esempio tra un server di produzione e uno di backup.

```python
from pathlib import Path
import shutil
import filecmp
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def sincronizza_directory(sorgente: Path, destinazione: Path) -> dict:
    """
    Sincronizza la directory sorgente con la destinazione.
    Copia file nuovi e aggiornati, rimuove file non piu presenti nella sorgente.
    """
    statistiche = {"copiati": 0, "aggiornati": 0, "rimossi": 0, "errori": 0}
    destinazione.mkdir(parents=True, exist_ok=True)

    # Copia e aggiornamento
    for item in sorgente.rglob("*"):
        percorso_relativo = item.relative_to(sorgente)
        dest_item = destinazione / percorso_relativo

        if item.is_dir():
            dest_item.mkdir(parents=True, exist_ok=True)
        elif item.is_file():
            try:
                if not dest_item.exists():
                    shutil.copy2(str(item), str(dest_item))
                    statistiche["copiati"] += 1
                    logger.info(f"Copiato: {percorso_relativo}")
                elif not filecmp.cmp(str(item), str(dest_item), shallow=False):
                    shutil.copy2(str(item), str(dest_item))
                    statistiche["aggiornati"] += 1
                    logger.info(f"Aggiornato: {percorso_relativo}")
            except OSError as e:
                statistiche["errori"] += 1
                logger.error(f"Errore su {percorso_relativo}: {e}")

    # Rimozione file orfani nella destinazione
    for item in destinazione.rglob("*"):
        if item.is_file():
            percorso_relativo = item.relative_to(destinazione)
            if not (sorgente / percorso_relativo).exists():
                item.unlink()
                statistiche["rimossi"] += 1
                logger.info(f"Rimosso: {percorso_relativo}")

    return statistiche


# Utilizzo
risultato = sincronizza_directory(
    Path("/dati/produzione"),
    Path("/backup/produzione")
)
print(f"Sincronizzazione completata: {risultato}")
```

### Script di backup automatizzati

Un sistema di backup robusto deve gestire la compressione, la rotazione degli archivi e la verifica di integrita.

```python
from pathlib import Path
from datetime import datetime
import tarfile
import hashlib
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GestoreBackup:
    """Gestisce backup compressi con rotazione e verifica integrita."""

    def __init__(self, sorgente: Path, destinazione: Path, max_backup: int = 7):
        self.sorgente = sorgente
        self.destinazione = destinazione
        self.max_backup = max_backup
        self.destinazione.mkdir(parents=True, exist_ok=True)

    def crea_backup(self) -> Path:
        """Crea un archivio tar.gz della directory sorgente."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_archivio = f"backup_{self.sorgente.name}_{timestamp}.tar.gz"
        percorso_archivio = self.destinazione / nome_archivio

        logger.info(f"Creazione backup: {percorso_archivio}")
        with tarfile.open(percorso_archivio, "w:gz") as tar:
            tar.add(self.sorgente, arcname=self.sorgente.name)

        # Calcolo checksum per verifica integrita
        checksum = self._calcola_checksum(percorso_archivio)
        metadati = {
            "file": nome_archivio,
            "timestamp": timestamp,
            "checksum_sha256": checksum,
            "dimensione_byte": percorso_archivio.stat().st_size,
        }

        percorso_metadati = percorso_archivio.with_suffix(".json")
        percorso_metadati.write_text(json.dumps(metadati, indent=2))
        logger.info(f"Backup completato: {metadati['dimensione_byte']} byte, SHA256: {checksum[:16]}...")

        self._ruota_backup()
        return percorso_archivio

    def _calcola_checksum(self, percorso: Path) -> str:
        """Calcola il checksum SHA-256 di un file."""
        sha256 = hashlib.sha256()
        with open(percorso, "rb") as f:
            for blocco in iter(lambda: f.read(8192), b""):
                sha256.update(blocco)
        return sha256.hexdigest()

    def _ruota_backup(self):
        """Mantiene solo gli ultimi N backup, eliminando i piu vecchi."""
        archivi = sorted(self.destinazione.glob("backup_*.tar.gz"))
        while len(archivi) > self.max_backup:
            vecchio = archivi.pop(0)
            vecchio.unlink()
            metadati = vecchio.with_suffix(".json")
            if metadati.exists():
                metadati.unlink()
            logger.info(f"Backup ruotato (eliminato): {vecchio.name}")

    def verifica_backup(self, percorso_archivio: Path) -> bool:
        """Verifica l'integrita di un backup confrontando il checksum."""
        percorso_metadati = percorso_archivio.with_suffix(".json")
        if not percorso_metadati.exists():
            logger.error("File metadati non trovato")
            return False

        metadati = json.loads(percorso_metadati.read_text())
        checksum_attuale = self._calcola_checksum(percorso_archivio)
        valido = checksum_attuale == metadati["checksum_sha256"]

        if valido:
            logger.info("Verifica integrita: OK")
        else:
            logger.error("Verifica integrita: FALLITA — il backup potrebbe essere corrotto")

        return valido


# Utilizzo
gestore = GestoreBackup(
    sorgente=Path("/opt/applicazione/dati"),
    destinazione=Path("/backup/applicazione"),
    max_backup=7
)
archivio = gestore.crea_backup()
gestore.verifica_backup(archivio)
```

---

## Automazione Sistema Operativo

### subprocess

Il modulo `subprocess` e lo strumento standard per eseguire comandi esterni dal codice Python. Sostituisce i vecchi `os.system()` e `os.popen()` con un'interfaccia piu sicura e flessibile.

#### `run()` — esecuzione semplice

```python
import subprocess

# Esecuzione base — cattura stdout e stderr
risultato = subprocess.run(
    ["ls", "-la", "/var/log"],
    capture_output=True,
    text=True,           # restituisce stringhe invece di bytes
    timeout=30           # timeout in secondi
)

print(f"Return code: {risultato.returncode}")
print(f"Output:\n{risultato.stdout}")

if risultato.returncode != 0:
    print(f"Errore:\n{risultato.stderr}")


# check=True solleva CalledProcessError se il comando fallisce
try:
    subprocess.run(
        ["systemctl", "status", "nginx"],
        check=True,
        capture_output=True,
        text=True,
        timeout=10
    )
except subprocess.CalledProcessError as e:
    print(f"Comando fallito con codice {e.returncode}")
    print(f"Stderr: {e.stderr}")
except subprocess.TimeoutExpired:
    print("Il comando ha superato il timeout")
```

#### `Popen` — controllo avanzato

`Popen` offre il controllo completo sull'esecuzione, permettendo di interagire con stdin, stdout e stderr del processo in modo asincrono.

```python
import subprocess

# Pipe tra due comandi: equivalente a "ps aux | grep python"
ps = subprocess.Popen(
    ["ps", "aux"],
    stdout=subprocess.PIPE
)
grep = subprocess.Popen(
    ["grep", "python"],
    stdin=ps.stdout,
    stdout=subprocess.PIPE,
    text=True
)
ps.stdout.close()  # consente a ps di ricevere SIGPIPE se grep termina
output, _ = grep.communicate()
print(output)


# Invio di input a un processo
processo = subprocess.Popen(
    ["python3", "-c", "nome = input('Nome: '); print(f'Ciao, {nome}!')"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)
stdout, stderr = processo.communicate(input="Marco\n", timeout=10)
print(stdout)  # Ciao, Marco!
```

#### Funzione wrapper riutilizzabile

```python
import subprocess
import logging

logger = logging.getLogger(__name__)


def esegui_comando(
    comando: list[str],
    timeout: int = 60,
    cwd: str | None = None,
    env: dict | None = None
) -> dict:
    """
    Esegue un comando esterno con gestione completa degli errori.
    Restituisce un dizionario con codice, stdout, stderr e successo.
    """
    try:
        risultato = subprocess.run(
            comando,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
            env=env
        )
        successo = risultato.returncode == 0
        if not successo:
            logger.warning(f"Comando {comando[0]} terminato con codice {risultato.returncode}")

        return {
            "successo": successo,
            "codice": risultato.returncode,
            "stdout": risultato.stdout.strip(),
            "stderr": risultato.stderr.strip(),
        }

    except subprocess.TimeoutExpired:
        logger.error(f"Timeout superato per: {' '.join(comando)}")
        return {"successo": False, "codice": -1, "stdout": "", "stderr": "Timeout"}

    except FileNotFoundError:
        logger.error(f"Comando non trovato: {comando[0]}")
        return {"successo": False, "codice": -1, "stdout": "", "stderr": "Comando non trovato"}


# Utilizzo
info = esegui_comando(["df", "-h"])
if info["successo"]:
    print(info["stdout"])
```

### os e platform

I moduli `os` e `platform` forniscono informazioni dettagliate sul sistema operativo e sull'ambiente di esecuzione.

```python
import os
import platform

# --- Informazioni sul sistema ---
print(f"Sistema operativo: {platform.system()}")         # Linux, Windows, Darwin
print(f"Versione: {platform.version()}")
print(f"Architettura: {platform.machine()}")             # x86_64, aarch64
print(f"Hostname: {platform.node()}")
print(f"Python: {platform.python_version()}")

# --- Variabili d'ambiente ---
# Lettura
path = os.environ.get("PATH", "")
home = os.environ.get("HOME", "/root")
db_url = os.environ.get("DATABASE_URL")  # None se non definita

# Impostazione (solo per il processo corrente e figli)
os.environ["APP_ENV"] = "production"
os.environ["LOG_LEVEL"] = "INFO"

# --- Gestione processi ---
print(f"PID corrente: {os.getpid()}")
print(f"PID processo padre: {os.getppid()}")
print(f"Utente corrente: {os.getlogin()}")
print(f"CPU disponibili: {os.cpu_count()}")
```

### psutil

La libreria `psutil` (process and system utilities) fornisce un'interfaccia cross-platform per il monitoraggio di risorse di sistema: CPU, memoria, disco, rete e processi.

```python
# pip install psutil

import psutil
from datetime import datetime


# --- CPU ---
print(f"CPU logiche: {psutil.cpu_count()}")
print(f"CPU fisiche: {psutil.cpu_count(logical=False)}")
print(f"Utilizzo CPU: {psutil.cpu_percent(interval=1)}%")
print(f"Utilizzo per core: {psutil.cpu_percent(interval=1, percpu=True)}")
print(f"Frequenza: {psutil.cpu_freq().current:.0f} MHz")

# --- Memoria ---
mem = psutil.virtual_memory()
print(f"RAM totale: {mem.total / (1024**3):.1f} GB")
print(f"RAM usata: {mem.used / (1024**3):.1f} GB ({mem.percent}%)")
print(f"RAM disponibile: {mem.available / (1024**3):.1f} GB")

swap = psutil.swap_memory()
print(f"Swap usata: {swap.used / (1024**3):.1f} GB ({swap.percent}%)")

# --- Disco ---
for partizione in psutil.disk_partitions():
    try:
        uso = psutil.disk_usage(partizione.mountpoint)
        print(f"{partizione.device}: {uso.percent}% usato "
              f"({uso.used / (1024**3):.1f}/{uso.total / (1024**3):.1f} GB)")
    except PermissionError:
        continue

# --- Rete ---
contatori_rete = psutil.net_io_counters()
print(f"Dati inviati: {contatori_rete.bytes_sent / (1024**2):.1f} MB")
print(f"Dati ricevuti: {contatori_rete.bytes_recv / (1024**2):.1f} MB")

# --- Uptime ---
boot = datetime.fromtimestamp(psutil.boot_time())
uptime = datetime.now() - boot
print(f"Avvio sistema: {boot:%Y-%m-%d %H:%M:%S}")
print(f"Uptime: {uptime.days} giorni, {uptime.seconds // 3600} ore")
```

#### Sistema di monitoraggio con alert

```python
import psutil
import logging
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("monitor")


@dataclass
class SoglieAlert:
    cpu_percentuale: float = 90.0
    ram_percentuale: float = 85.0
    disco_percentuale: float = 90.0
    swap_percentuale: float = 50.0


def controlla_sistema(soglie: SoglieAlert) -> list[str]:
    """Controlla le risorse di sistema e restituisce una lista di alert."""
    alert = []

    # CPU
    cpu = psutil.cpu_percent(interval=2)
    if cpu > soglie.cpu_percentuale:
        msg = f"ALERT CPU: utilizzo al {cpu}% (soglia: {soglie.cpu_percentuale}%)"
        alert.append(msg)
        logger.warning(msg)

    # RAM
    ram = psutil.virtual_memory()
    if ram.percent > soglie.ram_percentuale:
        msg = f"ALERT RAM: utilizzo al {ram.percent}% (soglia: {soglie.ram_percentuale}%)"
        alert.append(msg)
        logger.warning(msg)

    # Disco
    for part in psutil.disk_partitions():
        try:
            uso = psutil.disk_usage(part.mountpoint)
            if uso.percent > soglie.disco_percentuale:
                msg = (f"ALERT DISCO {part.mountpoint}: "
                       f"utilizzo al {uso.percent}% (soglia: {soglie.disco_percentuale}%)")
                alert.append(msg)
                logger.warning(msg)
        except PermissionError:
            continue

    # Swap
    swap = psutil.swap_memory()
    if swap.percent > soglie.swap_percentuale:
        msg = f"ALERT SWAP: utilizzo al {swap.percent}% (soglia: {soglie.swap_percentuale}%)"
        alert.append(msg)
        logger.warning(msg)

    if not alert:
        logger.info("Tutti i parametri nella norma")

    return alert


# Utilizzo
alert_attivi = controlla_sistema(SoglieAlert(cpu_percentuale=80.0))
if alert_attivi:
    # Qui si potrebbe inviare un'email o una notifica Slack
    print(f"Rilevati {len(alert_attivi)} alert")
```

---

## Automazione Rete

### paramiko (SSH)

`paramiko` e la libreria di riferimento per connessioni SSH in Python. Supporta l'esecuzione di comandi remoti, il trasferimento di file via SFTP e l'autenticazione tramite chiave.

```python
# pip install paramiko

import paramiko
import logging

logger = logging.getLogger(__name__)


class GestoreSSH:
    """Gestisce connessioni SSH con autenticazione per chiave o password."""

    def __init__(self, hostname: str, username: str,
                 password: str | None = None,
                 chiave_privata: str | None = None,
                 porta: int = 22):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.chiave_privata = chiave_privata
        self.porta = porta
        self.client = None

    def connetti(self):
        """Stabilisce la connessione SSH."""
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        kwargs = {
            "hostname": self.hostname,
            "port": self.porta,
            "username": self.username,
            "timeout": 10,
        }

        if self.chiave_privata:
            kwargs["key_filename"] = self.chiave_privata
        elif self.password:
            kwargs["password"] = self.password

        self.client.connect(**kwargs)
        logger.info(f"Connesso a {self.hostname}")

    def esegui_comando(self, comando: str, timeout: int = 30) -> dict:
        """Esegue un comando remoto e restituisce il risultato."""
        if not self.client:
            raise RuntimeError("Non connesso — chiamare connetti() prima")

        stdin, stdout, stderr = self.client.exec_command(comando, timeout=timeout)
        return {
            "stdout": stdout.read().decode().strip(),
            "stderr": stderr.read().decode().strip(),
            "codice": stdout.channel.recv_exit_status(),
        }

    def trasferisci_file(self, locale: str, remoto: str):
        """Trasferisce un file dal sistema locale al server remoto via SFTP."""
        sftp = self.client.open_sftp()
        sftp.put(locale, remoto)
        sftp.close()
        logger.info(f"File trasferito: {locale} -> {self.hostname}:{remoto}")

    def scarica_file(self, remoto: str, locale: str):
        """Scarica un file dal server remoto al sistema locale."""
        sftp = self.client.open_sftp()
        sftp.get(remoto, locale)
        sftp.close()
        logger.info(f"File scaricato: {self.hostname}:{remoto} -> {locale}")

    def disconnetti(self):
        """Chiude la connessione SSH."""
        if self.client:
            self.client.close()
            logger.info(f"Disconnesso da {self.hostname}")

    def __enter__(self):
        self.connetti()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnetti()


# Utilizzo con context manager
with GestoreSSH("192.168.1.10", "admin", chiave_privata="/home/utente/.ssh/id_rsa") as ssh:
    risultato = ssh.esegui_comando("df -h")
    print(risultato["stdout"])

    ssh.trasferisci_file("/tmp/config.yaml", "/etc/app/config.yaml")
```

#### Esecuzione su host multipli

```python
from concurrent.futures import ThreadPoolExecutor, as_completed


def esegui_su_host(host: str, comando: str) -> dict:
    """Esegue un comando su un singolo host."""
    try:
        with GestoreSSH(host, "admin", chiave_privata="/home/utente/.ssh/id_rsa") as ssh:
            risultato = ssh.esegui_comando(comando)
            return {"host": host, "successo": True, **risultato}
    except Exception as e:
        return {"host": host, "successo": False, "errore": str(e)}


# Esecuzione parallela su piu host
host_list = ["192.168.1.10", "192.168.1.11", "192.168.1.12", "192.168.1.13"]
comando = "uptime && free -h"

with ThreadPoolExecutor(max_workers=10) as executor:
    futures = {executor.submit(esegui_su_host, host, comando): host for host in host_list}

    for future in as_completed(futures):
        risultato = future.result()
        host = risultato["host"]
        if risultato["successo"]:
            print(f"[{host}] OK:\n{risultato['stdout']}\n")
        else:
            print(f"[{host}] ERRORE: {risultato['errore']}\n")
```

### netmiko

`netmiko` e costruita su `paramiko` e semplifica l'interazione con dispositivi di rete (Cisco IOS, Juniper JunOS, Aruba, Palo Alto, ecc.). Gestisce automaticamente prompt, paginazione e tempi di attesa specifici per ogni piattaforma.

```python
# pip install netmiko

from netmiko import ConnectHandler
import logging

logger = logging.getLogger(__name__)

# Definizione del dispositivo
cisco_switch = {
    "device_type": "cisco_ios",
    "host": "192.168.1.1",
    "username": "admin",
    "password": "secret123",
    "secret": "enable_secret",  # password di enable
    "timeout": 20,
}

# Connessione e comandi show
with ConnectHandler(**cisco_switch) as conn:
    conn.enable()  # entra in modalita privilegiata

    # Comandi show
    output = conn.send_command("show interfaces status")
    print(output)

    versione = conn.send_command("show version", use_textfsm=True)
    # use_textfsm=True restituisce output strutturato (lista di dizionari)
    print(versione)


# --- Backup configurazione ---
def backup_configurazione(dispositivo: dict, cartella_backup: str) -> str:
    """Esegue il backup della configurazione di un dispositivo di rete."""
    with ConnectHandler(**dispositivo) as conn:
        conn.enable()
        config = conn.send_command("show running-config")

        from pathlib import Path
        from datetime import datetime

        nome_file = f"{dispositivo['host']}_{datetime.now():%Y%m%d_%H%M%S}.cfg"
        percorso = Path(cartella_backup) / nome_file
        percorso.write_text(config)
        logger.info(f"Backup salvato: {percorso}")
        return str(percorso)


# --- Modifica configurazione in blocco ---
def applica_configurazione(dispositivo: dict, comandi: list[str]) -> str:
    """Applica una lista di comandi di configurazione al dispositivo."""
    with ConnectHandler(**dispositivo) as conn:
        conn.enable()
        output = conn.send_config_set(comandi)
        conn.save_config()
        return output


# Esempio: configurazione VLAN su piu switch
comandi_vlan = [
    "vlan 100",
    "name GESTIONE",
    "vlan 200",
    "name PRODUZIONE",
    "vlan 300",
    "name OSPITI",
]

lista_switch = [
    {"device_type": "cisco_ios", "host": "192.168.1.1", "username": "admin", "password": "secret"},
    {"device_type": "cisco_ios", "host": "192.168.1.2", "username": "admin", "password": "secret"},
]

for switch in lista_switch:
    output = applica_configurazione(switch, comandi_vlan)
    print(f"[{switch['host']}] Configurazione applicata")
```

### fabric

`fabric` semplifica l'esecuzione di comandi remoti e il trasferimento di file, offrendo un'API di alto livello particolarmente comoda per task di deploy e automazione sistemistica.

```python
# pip install fabric

from fabric import Connection, task
from invoke import Responder


# Connessione base
conn = Connection(
    host="192.168.1.10",
    user="admin",
    connect_kwargs={"key_filename": "/home/utente/.ssh/id_rsa"}
)

# Esecuzione comandi
risultato = conn.run("hostname && uptime", hide=True)
print(risultato.stdout)

# Trasferimento file
conn.put("/tmp/script.sh", "/opt/scripts/script.sh")
conn.get("/var/log/app.log", "/tmp/app.log")

# Esecuzione con sudo
sudopass = Responder(pattern=r"\[sudo\] password", response="password\n")
conn.run("sudo systemctl restart nginx", pty=True, watchers=[sudopass])


# --- Task riutilizzabili ---
def deploy_applicazione(hosts: list[str], pacchetto: str):
    """Deploy di un pacchetto su una lista di server."""
    for host in hosts:
        conn = Connection(host, user="deploy",
                          connect_kwargs={"key_filename": "/home/deploy/.ssh/id_rsa"})

        print(f"[{host}] Upload pacchetto...")
        conn.put(pacchetto, "/tmp/app.tar.gz")

        print(f"[{host}] Estrazione e installazione...")
        conn.run("cd /opt/app && tar xzf /tmp/app.tar.gz")
        conn.run("cd /opt/app && pip install -r requirements.txt")

        print(f"[{host}] Riavvio servizio...")
        conn.sudo("systemctl restart app.service")

        print(f"[{host}] Deploy completato")


deploy_applicazione(
    hosts=["web01.example.com", "web02.example.com"],
    pacchetto="/builds/app-latest.tar.gz"
)
```

---

## Automazione Email

### smtplib

Il modulo `smtplib` della libreria standard permette di inviare email tramite il protocollo SMTP. Supporta connessioni TLS/SSL, autenticazione e invio di messaggi con allegati.

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path


def invia_email(
    destinatario: str,
    oggetto: str,
    corpo_html: str,
    allegati: list[str] | None = None,
    mittente: str = "automazione@azienda.com",
    smtp_server: str = "smtp.gmail.com",
    smtp_porta: int = 587,
    smtp_utente: str = "automazione@azienda.com",
    smtp_password: str = "app_password_here"
):
    """Invia un'email HTML con allegati opzionali."""

    messaggio = MIMEMultipart("mixed")
    messaggio["From"] = mittente
    messaggio["To"] = destinatario
    messaggio["Subject"] = oggetto

    # Corpo HTML
    corpo = MIMEText(corpo_html, "html", "utf-8")
    messaggio.attach(corpo)

    # Allegati
    if allegati:
        for percorso_allegato in allegati:
            file_path = Path(percorso_allegato)
            with open(file_path, "rb") as f:
                parte = MIMEBase("application", "octet-stream")
                parte.set_payload(f.read())
            encoders.encode_base64(parte)
            parte.add_header(
                "Content-Disposition",
                f"attachment; filename={file_path.name}"
            )
            messaggio.attach(parte)

    # Invio
    with smtplib.SMTP(smtp_server, smtp_porta) as server:
        server.starttls()
        server.login(smtp_utente, smtp_password)
        server.send_message(messaggio)


# Utilizzo — email con report allegato
invia_email(
    destinatario="team@azienda.com",
    oggetto="Report Giornaliero — Stato Sistemi",
    corpo_html="""
    <h2>Report Giornaliero</h2>
    <p>In allegato il report dello stato dei sistemi.</p>
    <table border="1" cellpadding="5">
        <tr><th>Server</th><th>Stato</th><th>CPU</th></tr>
        <tr><td>web01</td><td style="color:green">OK</td><td>23%</td></tr>
        <tr><td>web02</td><td style="color:green">OK</td><td>45%</td></tr>
        <tr><td>db01</td><td style="color:red">CRITICO</td><td>95%</td></tr>
    </table>
    """,
    allegati=["/tmp/report_sistemi.xlsx"]
)
```

#### Configurazione per provider comuni

```python
# Gmail — richiede "App Password" (non la password dell'account)
GMAIL = {
    "smtp_server": "smtp.gmail.com",
    "smtp_porta": 587,  # TLS
}

# Office 365 / Microsoft 365
OFFICE365 = {
    "smtp_server": "smtp.office365.com",
    "smtp_porta": 587,  # TLS
}

# Connessione diretta con SSL (porta 465)
with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
    server.login(utente, password)
    server.send_message(messaggio)
```

### imaplib

Il modulo `imaplib` consente di leggere, cercare e gestire email tramite il protocollo IMAP.

```python
import imaplib
import email
from email.header import decode_header
from pathlib import Path


class LettoreEmail:
    """Legge e gestisce email tramite IMAP."""

    def __init__(self, server: str, utente: str, password: str):
        self.mail = imaplib.IMAP4_SSL(server)
        self.mail.login(utente, password)

    def cerca_email(self, cartella: str = "INBOX",
                    criterio: str = "ALL",
                    limite: int = 10) -> list[dict]:
        """Cerca email in una cartella con un criterio specifico."""
        self.mail.select(cartella)
        stato, dati = self.mail.search(None, criterio)

        if stato != "OK":
            return []

        id_messaggi = dati[0].split()
        risultati = []

        # Prende gli ultimi N messaggi
        for msg_id in id_messaggi[-limite:]:
            stato, msg_data = self.mail.fetch(msg_id, "(RFC822)")
            if stato != "OK":
                continue

            msg = email.message_from_bytes(msg_data[0][1])

            # Decodifica l'oggetto
            oggetto, encoding = decode_header(msg["Subject"])[0]
            if isinstance(oggetto, bytes):
                oggetto = oggetto.decode(encoding or "utf-8")

            risultati.append({
                "id": msg_id.decode(),
                "da": msg["From"],
                "oggetto": oggetto,
                "data": msg["Date"],
                "messaggio": msg,
            })

        return risultati

    def scarica_allegati(self, messaggio, cartella_dest: str) -> list[str]:
        """Scarica tutti gli allegati di un messaggio."""
        percorsi = []
        dest = Path(cartella_dest)
        dest.mkdir(parents=True, exist_ok=True)

        for parte in messaggio.walk():
            if parte.get_content_maintype() == "multipart":
                continue
            if parte.get("Content-Disposition") is None:
                continue

            nome_file = parte.get_filename()
            if nome_file:
                # Decodifica il nome del file se necessario
                decoded, enc = decode_header(nome_file)[0]
                if isinstance(decoded, bytes):
                    nome_file = decoded.decode(enc or "utf-8")

                percorso = dest / nome_file
                percorso.write_bytes(parte.get_payload(decode=True))
                percorsi.append(str(percorso))

        return percorsi

    def chiudi(self):
        self.mail.close()
        self.mail.logout()


# Utilizzo
lettore = LettoreEmail("imap.gmail.com", "utente@gmail.com", "app_password")

# Cerca email non lette da un mittente specifico
email_trovate = lettore.cerca_email(
    criterio='(UNSEEN FROM "report@azienda.com")',
    limite=5
)

for em in email_trovate:
    print(f"Da: {em['da']} | Oggetto: {em['oggetto']}")
    allegati = lettore.scarica_allegati(em["messaggio"], "/tmp/allegati")
    if allegati:
        print(f"  Allegati scaricati: {allegati}")

lettore.chiudi()
```

### Modulo email

Il modulo `email` della libreria standard offre strumenti per costruire messaggi MIME complessi con parti multiple.

```python
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from pathlib import Path


def crea_messaggio_multipart(
    mittente: str,
    destinatario: str,
    oggetto: str,
    testo: str,
    html: str,
    immagini_inline: dict[str, str] | None = None
) -> MIMEMultipart:
    """
    Crea un messaggio multipart con versione testo e HTML.
    Le immagini inline vengono referenziate nell'HTML con cid:nome_immagine.
    """
    messaggio = MIMEMultipart("related")
    messaggio["From"] = mittente
    messaggio["To"] = destinatario
    messaggio["Subject"] = oggetto

    # Parte alternativa (testo + HTML)
    alternativa = MIMEMultipart("alternative")
    alternativa.attach(MIMEText(testo, "plain", "utf-8"))
    alternativa.attach(MIMEText(html, "html", "utf-8"))
    messaggio.attach(alternativa)

    # Immagini inline
    if immagini_inline:
        for cid, percorso in immagini_inline.items():
            dati = Path(percorso).read_bytes()
            img = MIMEImage(dati)
            img.add_header("Content-ID", f"<{cid}>")
            img.add_header("Content-Disposition", "inline", filename=Path(percorso).name)
            messaggio.attach(img)

    return messaggio


# Utilizzo — email con logo inline
msg = crea_messaggio_multipart(
    mittente="sistema@azienda.com",
    destinatario="team@azienda.com",
    oggetto="Report con Logo",
    testo="Report disponibile (visualizzare in HTML per il formato completo).",
    html='<h1>Report</h1><img src="cid:logo"><p>Dettagli del report...</p>',
    immagini_inline={"logo": "/opt/risorse/logo.png"}
)
```

---

## Automazione Web

L'automazione web comprende due ambiti principali: le chiamate dirette ad API REST tramite `requests` e l'automazione del browser tramite `Selenium` o `Playwright`.

```python
# --- requests per API REST ---
# pip install requests

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def crea_sessione_resiliente(
    tentativi: int = 3,
    backoff: float = 0.5,
    codici_retry: tuple = (500, 502, 503, 504)
) -> requests.Session:
    """Crea una sessione HTTP con retry automatico."""
    sessione = requests.Session()
    retry = Retry(
        total=tentativi,
        backoff_factor=backoff,
        status_forcelist=codici_retry,
    )
    adattatore = HTTPAdapter(max_retries=retry)
    sessione.mount("http://", adattatore)
    sessione.mount("https://", adattatore)
    return sessione


sessione = crea_sessione_resiliente()

# GET con parametri
risposta = sessione.get(
    "https://api.esempio.com/utenti",
    params={"ruolo": "admin", "attivo": True},
    headers={"Authorization": "Bearer token123"},
    timeout=10
)
risposta.raise_for_status()
utenti = risposta.json()

# POST con payload JSON
nuovo_utente = {"nome": "Mario Rossi", "email": "mario@azienda.com"}
risposta = sessione.post(
    "https://api.esempio.com/utenti",
    json=nuovo_utente,
    timeout=10
)
```

```python
# --- Selenium per automazione browser ---
# pip install selenium

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


def configura_browser(headless: bool = True) -> webdriver.Chrome:
    """Configura e restituisce un'istanza di Chrome."""
    opzioni = Options()
    if headless:
        opzioni.add_argument("--headless")
    opzioni.add_argument("--no-sandbox")
    opzioni.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=opzioni)


# Esempio: login automatico e download report
driver = configura_browser(headless=True)
wait = WebDriverWait(driver, 10)

try:
    driver.get("https://portale.azienda.com/login")

    # Compilazione form di login
    campo_utente = wait.until(EC.presence_of_element_located((By.ID, "username")))
    campo_utente.send_keys("admin")
    driver.find_element(By.ID, "password").send_keys("secret123")
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    # Attesa caricamento dashboard
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "dashboard")))

    # Navigazione alla pagina report
    driver.get("https://portale.azienda.com/report/esporta")

    # Click sul pulsante di download
    btn_download = wait.until(EC.element_to_be_clickable((By.ID, "btn-esporta")))
    btn_download.click()

    # Upload di un file
    driver.get("https://portale.azienda.com/importa")
    campo_file = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
    campo_file.send_keys("/tmp/dati.csv")

finally:
    driver.quit()
```

```python
# --- Playwright (alternativa moderna a Selenium) ---
# pip install playwright && playwright install

from playwright.sync_api import sync_playwright


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    pagina = browser.new_page()

    pagina.goto("https://portale.azienda.com/login")
    pagina.fill("#username", "admin")
    pagina.fill("#password", "secret123")
    pagina.click("button[type='submit']")

    # Attesa navigazione
    pagina.wait_for_url("**/dashboard")

    # Screenshot per documentazione o debug
    pagina.screenshot(path="/tmp/dashboard.png")

    browser.close()
```

---

## Scheduling

### schedule

La libreria `schedule` offre un'API semplice e leggibile per pianificare l'esecuzione periodica di funzioni Python.

```python
# pip install schedule

import schedule
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def pulizia_log():
    """Elimina i file di log piu vecchi di 7 giorni."""
    logger.info("Esecuzione pulizia log...")
    # logica di pulizia
    logger.info("Pulizia completata")


def backup_database():
    """Esegue il backup del database."""
    logger.info("Backup database in corso...")
    # logica di backup
    logger.info("Backup completato")


def report_stato():
    """Genera e invia il report sullo stato dei sistemi."""
    logger.info("Generazione report stato...")
    # logica di report


# Pianificazione
schedule.every(10).minutes.do(report_stato)
schedule.every().hour.do(pulizia_log)
schedule.every().day.at("02:00").do(backup_database)
schedule.every().monday.at("09:00").do(report_stato)

# Loop principale con gestione errori
while True:
    try:
        schedule.run_pending()
        time.sleep(1)
    except Exception as e:
        logger.error(f"Errore nel task schedulato: {e}")
        time.sleep(60)  # attende prima di riprovare
```

### APScheduler

`APScheduler` (Advanced Python Scheduler) e una libreria piu avanzata che supporta diversi tipi di trigger, job store persistenti e l'esecuzione in background.

```python
# pip install apscheduler

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Callback per eventi
def listener_eventi(evento):
    if evento.exception:
        logger.error(f"Job {evento.job_id} fallito: {evento.exception}")
    else:
        logger.info(f"Job {evento.job_id} completato con successo")


# --- BackgroundScheduler (non blocca il thread principale) ---
scheduler = BackgroundScheduler(
    jobstores={
        "default": SQLAlchemyJobStore(url="sqlite:///jobs.db")  # persistenza
    }
)

scheduler.add_listener(listener_eventi, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)


# Job con trigger a intervallo
def controlla_servizi():
    logger.info("Controllo servizi in corso...")

scheduler.add_job(
    controlla_servizi,
    trigger=IntervalTrigger(minutes=5),
    id="controllo_servizi",
    replace_existing=True,
    misfire_grace_time=60
)

# Job con trigger cron
def backup_notturno():
    logger.info("Backup notturno in corso...")

scheduler.add_job(
    backup_notturno,
    trigger=CronTrigger(hour=2, minute=0),
    id="backup_notturno",
    replace_existing=True
)

# Job con trigger cron complesso (lunedi-venerdi alle 8:30)
def report_mattutino():
    logger.info("Report mattutino...")

scheduler.add_job(
    report_mattutino,
    trigger=CronTrigger(day_of_week="mon-fri", hour=8, minute=30),
    id="report_mattutino",
    replace_existing=True
)

# Job a data specifica
from datetime import datetime
scheduler.add_job(
    lambda: logger.info("Manutenzione programmata!"),
    trigger="date",
    run_date=datetime(2026, 4, 1, 3, 0, 0),
    id="manutenzione_programmata"
)

scheduler.start()

# Il programma principale continua a funzionare
# scheduler.shutdown() per fermarlo
```

### Cron + Python

Su sistemi Linux, `cron` e il metodo tradizionale per pianificare l'esecuzione di script. La libreria `python-crontab` consente di gestire il crontab programmaticamente.

```python
# pip install python-crontab

from crontab import CronTab


# --- Gestione programmatica del crontab ---
cron = CronTab(user="automazione")

# Creazione di un nuovo job
job = cron.new(command="/usr/bin/python3 /opt/scripts/backup.py >> /var/log/backup.log 2>&1")
job.setall("0 2 * * *")  # ogni giorno alle 02:00
job.set_comment("Backup giornaliero automatico")
job.enable()

# Altro job: pulizia ogni lunedi alle 06:00
job_pulizia = cron.new(command="/usr/bin/python3 /opt/scripts/pulizia.py")
job_pulizia.setall("0 6 * * 1")
job_pulizia.set_comment("Pulizia settimanale")

# Salvare le modifiche
cron.write()

# Elenco dei job attivi
for job in cron:
    print(f"{job.slices} | {job.command} | Abilitato: {job.is_enabled()}")

# Rimuovere un job per commento
cron.remove_all(comment="Backup giornaliero automatico")
cron.write()
```

#### Struttura consigliata per script cron

```python
#!/usr/bin/env python3
"""
Script di backup eseguito da cron.
Crontab: 0 2 * * * /usr/bin/python3 /opt/scripts/backup.py
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

# Configurazione logging — fondamentale per il debug di script cron
LOG_DIR = Path("/var/log/automazione")
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "backup.log"),
        logging.StreamHandler()  # utile anche per catturare output in cron
    ]
)
logger = logging.getLogger(__name__)


def main():
    logger.info("=== Inizio backup ===")
    try:
        # Logica di backup
        pass  # sostituire con la logica reale

        logger.info("=== Backup completato con successo ===")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Backup fallito: {e}", exc_info=True)
        # Qui si potrebbe inviare un'email di notifica
        sys.exit(1)


if __name__ == "__main__":
    main()
```

#### systemd timer (alternativa moderna a cron)

```ini
# /etc/systemd/system/backup.service
[Unit]
Description=Script di backup Python

[Service]
Type=oneshot
User=automazione
ExecStart=/usr/bin/python3 /opt/scripts/backup.py
```

```ini
# /etc/systemd/system/backup.timer
[Unit]
Description=Timer per backup giornaliero

[Timer]
OnCalendar=*-*-* 02:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

---

## Automazione Windows

### pywin32

`pywin32` fornisce l'accesso alle API di Windows e all'automazione COM, consentendo di controllare programmaticamente applicazioni come Excel, Word e Outlook.

```python
# pip install pywin32

import win32com.client
import win32api
import win32con
import win32service
import win32serviceutil


# --- Automazione Excel tramite COM ---
def genera_report_excel(dati: list[dict], percorso_output: str):
    """Genera un report Excel formattato tramite COM automation."""
    excel = win32com.client.Dispatch("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False

    try:
        wb = excel.Workbooks.Add()
        ws = wb.ActiveSheet
        ws.Name = "Report"

        # Intestazioni
        intestazioni = list(dati[0].keys())
        for col, intestazione in enumerate(intestazioni, start=1):
            cella = ws.Cells(1, col)
            cella.Value = intestazione
            cella.Font.Bold = True
            cella.Interior.ColorIndex = 15  # grigio chiaro

        # Dati
        for riga, record in enumerate(dati, start=2):
            for col, chiave in enumerate(intestazioni, start=1):
                ws.Cells(riga, col).Value = record[chiave]

        # Formattazione automatica
        ws.Columns.AutoFit()

        # Salvataggio
        wb.SaveAs(percorso_output)
        print(f"Report salvato: {percorso_output}")

    finally:
        wb.Close(SaveChanges=False)
        excel.Quit()


# --- Automazione Outlook ---
def invia_email_outlook(destinatario: str, oggetto: str, corpo: str, allegati: list[str] = None):
    """Invia un'email tramite Outlook installato localmente."""
    outlook = win32com.client.Dispatch("Outlook.Application")
    mail = outlook.CreateItem(0)  # 0 = olMailItem

    mail.To = destinatario
    mail.Subject = oggetto
    mail.HTMLBody = corpo

    if allegati:
        for allegato in allegati:
            mail.Attachments.Add(allegato)

    mail.Send()


# --- Gestione servizi Windows ---
def gestisci_servizio(nome: str, azione: str):
    """Avvia, ferma o controlla lo stato di un servizio Windows."""
    if azione == "stato":
        stato = win32serviceutil.QueryServiceStatus(nome)[1]
        stati = {
            win32service.SERVICE_RUNNING: "In esecuzione",
            win32service.SERVICE_STOPPED: "Fermato",
            win32service.SERVICE_START_PENDING: "In avvio",
            win32service.SERVICE_STOP_PENDING: "In arresto",
        }
        return stati.get(stato, f"Sconosciuto ({stato})")

    elif azione == "avvia":
        win32serviceutil.StartService(nome)

    elif azione == "ferma":
        win32serviceutil.StopService(nome)

    elif azione == "riavvia":
        win32serviceutil.RestartService(nome)


# --- Operazioni sul registro di Windows ---
def leggi_registro(chiave: str, valore: str) -> str:
    """Legge un valore dal registro di Windows."""
    try:
        reg_key = win32api.RegOpenKey(win32con.HKEY_LOCAL_MACHINE, chiave)
        valore_reg, tipo = win32api.RegQueryValueEx(reg_key, valore)
        win32api.RegCloseKey(reg_key)
        return valore_reg
    except Exception as e:
        return f"Errore: {e}"


# --- Query WMI ---
import wmi

def info_sistema_wmi():
    """Recupera informazioni di sistema tramite WMI."""
    c = wmi.WMI()

    # Informazioni sul computer
    for sistema in c.Win32_ComputerSystem():
        print(f"Nome: {sistema.Name}")
        print(f"Dominio: {sistema.Domain}")
        print(f"RAM totale: {int(sistema.TotalPhysicalMemory) / (1024**3):.1f} GB")

    # Dischi
    for disco in c.Win32_LogicalDisk(DriveType=3):
        spazio_libero = int(disco.FreeSpace) / (1024**3)
        spazio_totale = int(disco.Size) / (1024**3)
        print(f"Disco {disco.Caption}: {spazio_libero:.1f}/{spazio_totale:.1f} GB liberi")

    # Software installato
    for prodotto in c.Win32_Product():
        print(f"Software: {prodotto.Name} v{prodotto.Version}")
```

### Integrazione PowerShell

Python puo eseguire script e comandi PowerShell tramite `subprocess`, catturandone l'output in formati strutturati.

```python
import subprocess
import json


def esegui_powershell(comando: str, formato_json: bool = True) -> dict | str:
    """
    Esegue un comando PowerShell e restituisce il risultato.
    Se formato_json=True, aggiunge ConvertTo-Json e parsa l'output.
    """
    if formato_json:
        comando_completo = f"{comando} | ConvertTo-Json -Depth 5"
    else:
        comando_completo = comando

    risultato = subprocess.run(
        ["powershell", "-NoProfile", "-Command", comando_completo],
        capture_output=True,
        text=True,
        timeout=60
    )

    if risultato.returncode != 0:
        raise RuntimeError(f"PowerShell errore: {risultato.stderr}")

    if formato_json and risultato.stdout.strip():
        return json.loads(risultato.stdout)

    return risultato.stdout.strip()


# Esempi di utilizzo

# Informazioni sui servizi
servizi = esegui_powershell("Get-Service | Where-Object {$_.Status -eq 'Running'} | Select-Object Name, DisplayName")
for servizio in servizi:
    print(f"{servizio['Name']}: {servizio['DisplayName']}")

# Utenti Active Directory (richiede modulo AD installato)
utenti = esegui_powershell(
    "Get-ADUser -Filter * -Properties LastLogonDate | "
    "Select-Object SamAccountName, Name, LastLogonDate"
)

# Spazio disco
dischi = esegui_powershell(
    "Get-PSDrive -PSProvider FileSystem | Select-Object Name, Used, Free"
)

# Esecuzione di script PowerShell
risultato = esegui_powershell(
    "& 'C:\\Scripts\\manutenzione.ps1' -Parametro1 'valore'",
    formato_json=False
)
```

---

## Automazione Active Directory

La libreria `ldap3` consente di interagire con Active Directory e qualsiasi server LDAP per gestire utenti, gruppi, password e attributi.

```python
# pip install ldap3

from ldap3 import Server, Connection, ALL, MODIFY_REPLACE, MODIFY_ADD, MODIFY_DELETE
from ldap3.extend.microsoft.addMembersToGroups import ad_add_members_to_groups
from ldap3.extend.microsoft.removeMembersFromGroups import ad_remove_members_from_groups
import logging
import csv

logger = logging.getLogger(__name__)


class GestoreAD:
    """Gestisce operazioni su Active Directory tramite LDAP."""

    def __init__(self, server: str, utente: str, password: str, base_dn: str):
        self.base_dn = base_dn
        self.server = Server(server, get_info=ALL, use_ssl=True)
        self.conn = Connection(
            self.server,
            user=utente,
            password=password,
            auto_bind=True
        )
        logger.info(f"Connesso a {server}")

    def cerca_utente(self, filtro: str, attributi: list[str] = None) -> list[dict]:
        """Cerca utenti con un filtro LDAP."""
        if attributi is None:
            attributi = ["sAMAccountName", "cn", "mail", "memberOf", "userAccountControl"]

        self.conn.search(
            search_base=self.base_dn,
            search_filter=filtro,
            attributes=attributi
        )

        risultati = []
        for entry in self.conn.entries:
            risultati.append({attr: str(entry[attr]) for attr in attributi if attr in entry.entry_attributes})

        return risultati

    def crea_utente(
        self,
        nome: str,
        cognome: str,
        username: str,
        password: str,
        ou: str,
        email: str = None,
        gruppi: list[str] = None
    ) -> bool:
        """Crea un nuovo utente in Active Directory."""
        dn = f"CN={nome} {cognome},{ou},{self.base_dn}"

        attributi = {
            "objectClass": ["top", "person", "organizationalPerson", "user"],
            "sAMAccountName": username,
            "userPrincipalName": f"{username}@{self.base_dn.replace('DC=', '').replace(',', '.')}",
            "givenName": nome,
            "sn": cognome,
            "cn": f"{nome} {cognome}",
            "displayName": f"{nome} {cognome}",
        }

        if email:
            attributi["mail"] = email

        # Creazione utente
        successo = self.conn.add(dn, attributes=attributi)
        if not successo:
            logger.error(f"Errore creazione utente {username}: {self.conn.result}")
            return False

        # Impostazione password
        from ldap3.extend.microsoft.modifyPassword import ad_modify_password
        ad_modify_password(self.conn, dn, None, password)

        # Abilitazione account (rimozione flag ACCOUNTDISABLE)
        self.conn.modify(dn, {
            "userAccountControl": [(MODIFY_REPLACE, [512])]  # NORMAL_ACCOUNT
        })

        # Aggiunta ai gruppi
        if gruppi:
            for gruppo_dn in gruppi:
                ad_add_members_to_groups(self.conn, dn, gruppo_dn)
                logger.info(f"Utente {username} aggiunto al gruppo {gruppo_dn}")

        logger.info(f"Utente creato: {username}")
        return True

    def modifica_utente(self, username: str, modifiche: dict) -> bool:
        """Modifica gli attributi di un utente esistente."""
        utenti = self.cerca_utente(f"(sAMAccountName={username})")
        if not utenti:
            logger.error(f"Utente {username} non trovato")
            return False

        # Recupera il DN completo
        self.conn.search(
            self.base_dn,
            f"(sAMAccountName={username})",
            attributes=["distinguishedName"]
        )
        dn = str(self.conn.entries[0].distinguishedName)

        changes = {}
        for attributo, valore in modifiche.items():
            changes[attributo] = [(MODIFY_REPLACE, [valore])]

        successo = self.conn.modify(dn, changes)
        if successo:
            logger.info(f"Utente {username} modificato: {list(modifiche.keys())}")
        else:
            logger.error(f"Errore modifica {username}: {self.conn.result}")

        return successo

    def disabilita_utente(self, username: str) -> bool:
        """Disabilita un account utente."""
        return self.modifica_utente(username, {"userAccountControl": 514})  # ACCOUNTDISABLE

    def reset_password(self, username: str, nuova_password: str) -> bool:
        """Resetta la password di un utente."""
        self.conn.search(self.base_dn, f"(sAMAccountName={username})", attributes=["distinguishedName"])
        if not self.conn.entries:
            return False

        dn = str(self.conn.entries[0].distinguishedName)
        from ldap3.extend.microsoft.modifyPassword import ad_modify_password
        risultato = ad_modify_password(self.conn, dn, None, nuova_password)
        if risultato:
            logger.info(f"Password resettata per {username}")
        return risultato

    def gestisci_gruppo(self, gruppo_dn: str, utenti_dn: list[str], azione: str = "aggiungi"):
        """Aggiunge o rimuove utenti da un gruppo."""
        if azione == "aggiungi":
            ad_add_members_to_groups(self.conn, utenti_dn, gruppo_dn)
        elif azione == "rimuovi":
            ad_remove_members_from_groups(self.conn, utenti_dn, gruppo_dn, fix=True)

    def chiudi(self):
        self.conn.unbind()


# --- Operazioni in blocco da CSV ---
def crea_utenti_da_csv(percorso_csv: str, gestore: GestoreAD):
    """
    Crea utenti in blocco da un file CSV.
    Colonne attese: nome, cognome, username, email, ou, gruppi
    """
    with open(percorso_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for riga in reader:
            gruppi = riga.get("gruppi", "").split(";") if riga.get("gruppi") else None
            successo = gestore.crea_utente(
                nome=riga["nome"],
                cognome=riga["cognome"],
                username=riga["username"],
                password="Password_Temporanea1!",
                ou=riga["ou"],
                email=riga.get("email"),
                gruppi=gruppi
            )
            stato = "OK" if successo else "ERRORE"
            print(f"[{stato}] {riga['username']}")


# Utilizzo
ad = GestoreAD(
    server="ldaps://dc01.azienda.local",
    utente="CN=Admin,OU=ServiceAccounts,DC=azienda,DC=local",
    password="admin_password",
    base_dn="DC=azienda,DC=local"
)

# Cerca tutti gli utenti del reparto IT
utenti_it = ad.cerca_utente("(&(objectClass=user)(department=IT))")
for u in utenti_it:
    print(f"{u['sAMAccountName']}: {u.get('mail', 'N/A')}")

# Creazione massiva
crea_utenti_da_csv("/dati/nuovi_utenti.csv", ad)

ad.chiudi()
```

---

## Automazione Report

La generazione automatica di report combina la raccolta di dati, la formattazione e la distribuzione. Python offre strumenti per produrre report in HTML, PDF e Excel.

### Report HTML con Jinja2

```python
# pip install jinja2

from jinja2 import Template
from pathlib import Path
from datetime import datetime


def genera_report_html(dati: dict, template_path: str, output_path: str) -> str:
    """Genera un report HTML utilizzando un template Jinja2."""

    template_str = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>{{ titolo }}</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
            table { border-collapse: collapse; width: 100%; margin: 20px 0; }
            th, td { border: 1px solid #ddd; padding: 10px; text-align: left; }
            th { background-color: #3498db; color: white; }
            tr:nth-child(even) { background-color: #f2f2f2; }
            .ok { color: green; font-weight: bold; }
            .critico { color: red; font-weight: bold; }
            .footer { margin-top: 30px; font-size: 0.8em; color: #777; }
        </style>
    </head>
    <body>
        <h1>{{ titolo }}</h1>
        <p>Generato il {{ data_generazione }} da {{ autore }}</p>

        <h2>Stato dei Server</h2>
        <table>
            <tr>
                <th>Server</th><th>Stato</th><th>CPU</th><th>RAM</th><th>Disco</th>
            </tr>
            {% for server in server_list %}
            <tr>
                <td>{{ server.nome }}</td>
                <td class="{{ 'ok' if server.stato == 'OK' else 'critico' }}">{{ server.stato }}</td>
                <td>{{ server.cpu }}%</td>
                <td>{{ server.ram }}%</td>
                <td>{{ server.disco }}%</td>
            </tr>
            {% endfor %}
        </table>

        {% if alert %}
        <h2>Alert Attivi</h2>
        <ul>
            {% for a in alert %}
            <li class="critico">{{ a }}</li>
            {% endfor %}
        </ul>
        {% endif %}

        <div class="footer">
            Report generato automaticamente dal sistema di monitoraggio.
        </div>
    </body>
    </html>
    """

    template = Template(template_str)
    html = template.render(**dati, data_generazione=datetime.now().strftime("%d/%m/%Y %H:%M"))

    Path(output_path).write_text(html, encoding="utf-8")
    return output_path


# Utilizzo
dati_report = {
    "titolo": "Report Infrastruttura — Marzo 2026",
    "autore": "Sistema Monitoraggio",
    "server_list": [
        {"nome": "web01", "stato": "OK", "cpu": 23, "ram": 45, "disco": 60},
        {"nome": "web02", "stato": "OK", "cpu": 31, "ram": 52, "disco": 55},
        {"nome": "db01", "stato": "CRITICO", "cpu": 95, "ram": 88, "disco": 92},
    ],
    "alert": ["db01: CPU al 95%", "db01: disco al 92%"]
}

genera_report_html(dati_report, "", "/tmp/report_infrastruttura.html")
```

### Report PDF con WeasyPrint

```python
# pip install weasyprint

from weasyprint import HTML


def html_a_pdf(html_path: str, pdf_path: str):
    """Converte un report HTML in PDF."""
    HTML(filename=html_path).write_pdf(pdf_path)
    print(f"PDF generato: {pdf_path}")


# Da stringa HTML a PDF direttamente
def genera_pdf_diretto(contenuto_html: str, pdf_path: str):
    """Genera un PDF direttamente da una stringa HTML."""
    HTML(string=contenuto_html).write_pdf(pdf_path)


# Pipeline completa: dati -> HTML -> PDF -> email
html_path = genera_report_html(dati_report, "", "/tmp/report.html")
html_a_pdf(html_path, "/tmp/report.pdf")
# invia_email(..., allegati=["/tmp/report.pdf"])
```

### Report Excel con openpyxl

```python
# pip install openpyxl

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.chart import BarChart, Reference


def genera_report_excel(dati: list[dict], percorso: str):
    """Genera un report Excel formattato con grafici."""

    wb = Workbook()
    ws = wb.active
    ws.title = "Report Sistemi"

    # Stili
    font_intestazione = Font(bold=True, color="FFFFFF", size=12)
    sfondo_intestazione = PatternFill(start_color="2980B9", end_color="2980B9", fill_type="solid")
    bordo = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin")
    )

    # Intestazioni
    intestazioni = list(dati[0].keys())
    for col, intestazione in enumerate(intestazioni, start=1):
        cella = ws.cell(row=1, column=col, value=intestazione.upper())
        cella.font = font_intestazione
        cella.fill = sfondo_intestazione
        cella.alignment = Alignment(horizontal="center")
        cella.border = bordo

    # Dati
    for riga, record in enumerate(dati, start=2):
        for col, chiave in enumerate(intestazioni, start=1):
            cella = ws.cell(row=riga, column=col, value=record[chiave])
            cella.border = bordo
            cella.alignment = Alignment(horizontal="center")

    # Larghezza colonne automatica
    for col_idx, intestazione in enumerate(intestazioni, start=1):
        max_lunghezza = max(len(str(intestazione)), *(len(str(r[intestazione])) for r in dati))
        ws.column_dimensions[ws.cell(row=1, column=col_idx).column_letter].width = max_lunghezza + 4

    # Grafico a barre
    chart = BarChart()
    chart.title = "Utilizzo Risorse per Server"
    chart.x_axis.title = "Server"
    chart.y_axis.title = "Percentuale (%)"

    # Assumendo che colonne 3, 4, 5 siano cpu, ram, disco
    categorie = Reference(ws, min_col=1, min_row=2, max_row=len(dati) + 1)
    for col_idx in range(3, 6):
        valori = Reference(ws, min_col=col_idx, min_row=1, max_row=len(dati) + 1)
        chart.add_data(valori, titles_from_data=True)

    chart.set_categories(categorie)
    chart.shape = 4
    ws.add_chart(chart, "G2")

    wb.save(percorso)
    print(f"Report Excel salvato: {percorso}")


# Utilizzo
dati_excel = [
    {"server": "web01", "stato": "OK", "cpu": 23, "ram": 45, "disco": 60},
    {"server": "web02", "stato": "OK", "cpu": 31, "ram": 52, "disco": 55},
    {"server": "db01", "stato": "CRITICO", "cpu": 95, "ram": 88, "disco": 92},
    {"server": "app01", "stato": "OK", "cpu": 40, "ram": 60, "disco": 70},
]

genera_report_excel(dati_excel, "/tmp/report_sistemi.xlsx")
```

### Pipeline completa di report automatizzato

```python
from datetime import datetime
from pathlib import Path


def pipeline_report_giornaliero():
    """
    Pipeline completa: raccoglie dati, genera report in piu formati
    e lo distribuisce via email.
    """

    # 1. Raccolta dati (da psutil, API, database, ecc.)
    dati_server = raccogli_dati_server()  # funzione personalizzata

    # 2. Generazione report in piu formati
    timestamp = datetime.now().strftime("%Y%m%d")
    report_dir = Path("/opt/report") / timestamp
    report_dir.mkdir(parents=True, exist_ok=True)

    html_path = genera_report_html(
        dati_server,
        template_path="/opt/templates/report.html.j2",
        output_path=str(report_dir / "report.html")
    )

    pdf_path = str(report_dir / "report.pdf")
    html_a_pdf(html_path, pdf_path)

    excel_path = str(report_dir / "report.xlsx")
    genera_report_excel(dati_server["server_list"], excel_path)

    # 3. Distribuzione via email
    invia_email(
        destinatario="team-infrastruttura@azienda.com",
        oggetto=f"Report Infrastruttura — {datetime.now():%d/%m/%Y}",
        corpo_html=Path(html_path).read_text(),
        allegati=[pdf_path, excel_path]
    )

    print(f"Report generato e distribuito: {report_dir}")
```

---

## Best Practices

1. **Utilizzare sempre la gestione strutturata degli errori.** Ogni script di automazione deve prevedere blocchi `try/except` specifici con logging dettagliato. Gli errori non gestiti in script eseguiti da cron o scheduler passano inosservati e causano fallimenti silenti. Registrare sempre il traceback completo con `exc_info=True` e implementare meccanismi di notifica per gli errori critici.

2. **Separare configurazione e codice.** Non inserire mai credenziali, percorsi, indirizzi IP o parametri operativi direttamente nel codice sorgente. Utilizzare file di configurazione esterni (YAML, TOML, JSON), variabili d'ambiente o un secret manager. Questo rende gli script portabili, sicuri e facili da adattare a ambienti diversi (sviluppo, staging, produzione) senza modificare il codice.

3. **Implementare logging completo fin dall'inizio.** Utilizzare il modulo `logging` della libreria standard con livelli appropriati (DEBUG per lo sviluppo, INFO per l'operativita, WARNING/ERROR per le anomalie). Configurare la rotazione dei log con `RotatingFileHandler` o `TimedRotatingFileHandler`. Un buon sistema di logging e la differenza tra risolvere un problema in cinque minuti e impiegare ore di debug.

4. **Progettare per l'idempotenza.** Uno script di automazione deve poter essere eseguito piu volte senza causare effetti collaterali indesiderati. Se uno script crea un utente, deve prima verificare che non esista gia; se sposta un file, deve controllare che non sia stato gia spostato. L'idempotenza rende gli script sicuri da rieseguire dopo errori parziali e semplifica il debugging.

5. **Adottare il principio di fail-fast con retry intelligente.** Validare i prerequisiti all'inizio dello script (file presenti, connessioni disponibili, permessi sufficienti) e fallire immediatamente se non sono soddisfatti, piuttosto che procedere parzialmente. Per le operazioni di rete, implementare retry con backoff esponenziale usando librerie come `tenacity`, limitando il numero massimo di tentativi.

6. **Scrivere script modulari e testabili.** Separare la logica in funzioni e classi con responsabilita chiare. Evitare script monolitici con centinaia di righe in un unico blocco. Ogni funzione deve fare una cosa e farla bene. Questa struttura consente di scrivere test unitari, riutilizzare componenti tra script diversi e modificare singole parti senza rischio di regressioni.

7. **Utilizzare context manager e pulizia delle risorse.** Connessioni SSH, sessioni LDAP, file aperti, browser Selenium: tutte le risorse esterne devono essere gestite con `with` o con metodi `__enter__`/`__exit__` espliciti. Una connessione non chiusa dopo un errore puo causare leak di risorse, esaurimento di sessioni e blocchi nei sistemi remoti.

8. **Implementare dry-run e verbosita configurabile.** Ogni script che modifica dati o sistemi dovrebbe supportare una modalita `--dry-run` che mostra cosa farebbe senza eseguire le modifiche. Questo e fondamentale per validare il comportamento prima dell'esecuzione reale, soprattutto per operazioni in blocco come la creazione massiva di utenti o la modifica di configurazioni di rete.

9. **Documentare con docstring e commenti operativi.** Ogni script deve includere una docstring iniziale che spiega lo scopo, i prerequisiti, i parametri di configurazione e il crontab previsto. I commenti nel codice devono spiegare il "perche", non il "cosa". Includere esempi di utilizzo e informazioni sulla frequenza di esecuzione prevista.

10. **Monitorare le automazioni stesse.** Uno script di automazione che fallisce silenziosamente e peggio di non avere automazione. Implementare heartbeat (un segnale periodico che conferma che lo script e attivo), alert sui fallimenti, dashboard di stato e metriche di esecuzione (durata, numero di operazioni, tasso di errore). Strumenti come Prometheus, Grafana o anche un semplice file di stato possono fare la differenza tra un sistema affidabile e uno fragile.

---

## Sicurezza di subprocess — shell=False e Sanitizzazione

L'uso di `subprocess` con `shell=True` e una delle vulnerabilita piu comuni negli script di automazione Python. Quando `shell=True` e attivo, l'intero comando viene passato alla shell del sistema operativo, esponendo il codice a **command injection**.

### Il problema di shell=True

```python
import subprocess

# VULNERABILE — mai fare questo con input non fidato
nome_file = input("Nome del file: ")
subprocess.run(f"cat {nome_file}", shell=True)  # shell=True!
# Un utente malintenzionato puo inserire: "file.txt; rm -rf /"

# SICURO — usare sempre shell=False (default)
subprocess.run(["cat", nome_file])  # shell=False (default)
# Il nome del file e trattato come singolo argomento, non interpretato dalla shell
```

### Regole per subprocess sicuro

```python
import subprocess
import shlex
from pathlib import Path


def esegui_comando_sicuro(
    comando: list[str],
    timeout: int = 30,
    cwd: str | None = None,
) -> subprocess.CompletedProcess:
    """Esegue un comando con tutte le precauzioni di sicurezza."""
    return subprocess.run(
        comando,
        shell=False,           # MAI True con input esterno
        capture_output=True,
        text=True,
        timeout=timeout,       # Previene blocchi infiniti
        cwd=cwd,
        env=None,              # Eredita l'ambiente corrente
        check=False,           # Non lanciare eccezione su exit code != 0
    )


def valida_percorso(percorso_utente: str, base_consentita: Path) -> Path:
    """Valida un percorso per prevenire path traversal."""
    percorso = (base_consentita / percorso_utente).resolve()
    if not percorso.is_relative_to(base_consentita):
        raise ValueError(f"Path traversal rilevato: {percorso_utente}")
    return percorso


# Quando serve costruire un comando da stringa (raro ma legittimo)
comando_stringa = "ls -la /var/log"
comando_lista = shlex.split(comando_stringa)  # ['ls', '-la', '/var/log']
subprocess.run(comando_lista)  # shell=False con lista
```

### Gestione output e codici di uscita

```python
import subprocess
import logging

log = logging.getLogger(__name__)


def esegui_con_logging(comando: list[str], descrizione: str) -> bool:
    """Esegue un comando con logging completo."""
    log.info("Esecuzione: %s — %s", descrizione, " ".join(comando))

    try:
        risultato = subprocess.run(
            comando, capture_output=True, text=True, timeout=60
        )
    except subprocess.TimeoutExpired:
        log.error("Timeout: %s", descrizione)
        return False
    except FileNotFoundError:
        log.error("Comando non trovato: %s", comando[0])
        return False

    if risultato.returncode != 0:
        log.error(
            "Fallito (exit %d): %s\nstderr: %s",
            risultato.returncode, descrizione, risultato.stderr.strip(),
        )
        return False

    log.info("Completato: %s\nOutput: %s", descrizione, risultato.stdout.strip()[:500])
    return True
```

---

## Task Scheduling Avanzato — APScheduler e Cron

### APScheduler — scheduling in-process

APScheduler e la libreria di riferimento per la schedulazione di task all'interno di un processo Python. Supporta trigger basati su intervallo, cron e data specifica.

```bash
pip install APScheduler
```

```python
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
import logging
from datetime import datetime

log = logging.getLogger(__name__)


def backup_database():
    """Task: backup del database."""
    log.info("Backup database avviato: %s", datetime.now().isoformat())
    # ... logica di backup ...


def pulizia_log():
    """Task: pulizia dei file di log vecchi."""
    log.info("Pulizia log avviata")
    # ... logica di pulizia ...


def monitoraggio_risorse():
    """Task: controllo risorse di sistema."""
    import psutil
    cpu = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory().percent
    log.info("CPU: %.1f%%, Memoria: %.1f%%", cpu, mem)
    if cpu > 90 or mem > 90:
        log.warning("Risorse critiche! CPU=%.1f%%, MEM=%.1f%%", cpu, mem)


def listener_errori(event):
    """Listener per gestire gli errori nei job."""
    if event.exception:
        log.error("Job %s fallito: %s", event.job_id, event.exception)
    else:
        log.debug("Job %s completato", event.job_id)


# Configurazione scheduler
scheduler = BackgroundScheduler(
    job_defaults={
        "coalesce": True,         # Se il job e in ritardo, eseguirlo una sola volta
        "max_instances": 1,       # Non eseguire piu istanze dello stesso job
        "misfire_grace_time": 300, # Tolleranza di 5 minuti per esecuzioni mancate
    }
)

scheduler.add_listener(listener_errori, EVENT_JOB_ERROR | EVENT_JOB_EXECUTED)

# Job con trigger cron — "ogni giorno alle 02:00"
scheduler.add_job(
    backup_database,
    trigger=CronTrigger(hour=2, minute=0),
    id="backup_db",
    name="Backup Database Giornaliero",
)

# Job con trigger intervallo — "ogni 5 minuti"
scheduler.add_job(
    monitoraggio_risorse,
    trigger=IntervalTrigger(minutes=5),
    id="monitor_risorse",
    name="Monitoraggio Risorse",
)

# Job con trigger cron complesso — "ogni domenica alle 03:00"
scheduler.add_job(
    pulizia_log,
    trigger=CronTrigger(day_of_week="sun", hour=3),
    id="pulizia_log",
    name="Pulizia Log Settimanale",
)

scheduler.start()
```

### Integrazione cron con Python

```python
#!/usr/bin/env python3
"""Script eseguibile da cron con gestione lock e logging."""
import fcntl
import sys
import logging
from pathlib import Path
from datetime import datetime

LOCK_FILE = Path("/tmp/mio_script.lock")
LOG_FILE = Path("/var/log/mio_script.log")

logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)


def acquisisci_lock() -> bool:
    """Previene esecuzioni concorrenti dello stesso script."""
    try:
        lock_fd = open(LOCK_FILE, "w")
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        lock_fd.write(str(datetime.now().isoformat()))
        return True
    except (IOError, OSError):
        log.warning("Script gia in esecuzione — uscita")
        return False


def main():
    if not acquisisci_lock():
        sys.exit(0)

    log.info("Inizio esecuzione")
    try:
        # ... logica dello script ...
        log.info("Esecuzione completata con successo")
    except Exception:
        log.exception("Errore durante l'esecuzione")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

```bash
# Crontab — eseguire lo script ogni ora
# crontab -e
0 * * * * /opt/venv/bin/python /opt/scripts/mio_script.py >> /var/log/cron_mio_script.log 2>&1
```

---

## File System Monitoring Avanzato con watchdog

La libreria `watchdog` monitora le modifiche al filesystem in tempo reale. L'uso avanzato include filtri per tipo di file, debounce per eventi multipli e gestione degli errori.

```python
import time
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import (
    FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent,
    FileDeletedEvent, FileMovedEvent,
)
import logging

log = logging.getLogger(__name__)


class MonitorAvanzato(FileSystemEventHandler):
    """Handler con debounce, filtri e logging strutturato."""

    def __init__(self, estensioni: set[str] | None = None, debounce_sec: float = 1.0):
        self.estensioni = estensioni  # es. {".py", ".json", ".yaml"}
        self.debounce_sec = debounce_sec
        self._ultimo_evento: dict[str, float] = {}

    def _filtro_estensione(self, path: str) -> bool:
        if self.estensioni is None:
            return True
        return Path(path).suffix.lower() in self.estensioni

    def _debounce(self, path: str) -> bool:
        ora = time.time()
        ultimo = self._ultimo_evento.get(path, 0)
        if ora - ultimo < self.debounce_sec:
            return False
        self._ultimo_evento[path] = ora
        return True

    def on_created(self, event: FileCreatedEvent):
        if event.is_directory or not self._filtro_estensione(event.src_path):
            return
        if self._debounce(event.src_path):
            log.info("CREATO: %s", event.src_path)

    def on_modified(self, event: FileModifiedEvent):
        if event.is_directory or not self._filtro_estensione(event.src_path):
            return
        if self._debounce(event.src_path):
            log.info("MODIFICATO: %s", event.src_path)

    def on_deleted(self, event: FileDeletedEvent):
        if event.is_directory or not self._filtro_estensione(event.src_path):
            return
        log.info("ELIMINATO: %s", event.src_path)

    def on_moved(self, event: FileMovedEvent):
        if event.is_directory:
            return
        log.info("SPOSTATO: %s -> %s", event.src_path, event.dest_path)


def avvia_monitoraggio(cartella: str, estensioni: set[str] | None = None):
    """Avvia il monitoraggio di una cartella."""
    handler = MonitorAvanzato(estensioni=estensioni)
    observer = Observer()
    observer.schedule(handler, cartella, recursive=True)
    observer.start()
    log.info("Monitoraggio avviato: %s", cartella)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


# Utilizzo
# avvia_monitoraggio("/opt/dati", estensioni={".csv", ".json", ".xml"})
```

---

## Fabric 3.x — Deploy e Orchestrazione Remota

Fabric 3.x e una libreria per eseguire comandi su host remoti via SSH. A differenza di Fabric 1.x, la versione 3 si basa su `Invoke` per l'esecuzione locale e `Paramiko` per SSH.

```bash
pip install fabric
```

```python
"""fabfile.py — task di deploy con Fabric 3.x."""
from fabric import Connection, task
from invoke import Responder
import logging

log = logging.getLogger(__name__)


@task
def deploy(c, host, branch="main"):
    """Deploy dell'applicazione su un server remoto."""
    conn = Connection(
        host=host,
        user="deploy",
        connect_kwargs={"key_filename": "/home/deploy/.ssh/id_ed25519"},
        connect_timeout=10,
    )

    with conn:
        # 1. Pull del codice
        conn.run(f"cd /opt/app && git fetch origin && git checkout {branch} && git pull")

        # 2. Aggiornamento dipendenze
        conn.run("cd /opt/app && /opt/app/.venv/bin/pip install -r requirements.txt")

        # 3. Migrazioni database
        conn.run("cd /opt/app && /opt/app/.venv/bin/python manage.py migrate --noinput")

        # 4. Restart servizio
        conn.sudo("systemctl restart app.service")

        # 5. Health check
        risultato = conn.run("curl -sf http://localhost:8000/health || exit 1")
        if risultato.ok:
            log.info("Deploy completato su %s", host)
        else:
            log.error("Health check fallito su %s", host)


@task
def deploy_fleet(c, branch="main"):
    """Deploy su tutti i server del fleet."""
    hosts = ["web01.example.com", "web02.example.com", "web03.example.com"]
    for host in hosts:
        try:
            deploy(c, host=host, branch=branch)
        except Exception:
            log.exception("Deploy fallito su %s — continuo con gli altri", host)
```

---

## ansible-runner — Automazione Infrastruttura da Python

`ansible-runner` consente di eseguire playbook Ansible direttamente da codice Python, integrando l'automazione Ansible in applicazioni e script.

```bash
pip install ansible-runner
```

```python
import ansible_runner
import json
from pathlib import Path


def esegui_playbook(playbook: str, inventory: str, extra_vars: dict | None = None):
    """Esegue un playbook Ansible e restituisce i risultati."""
    risultato = ansible_runner.run(
        playbook=playbook,
        inventory=inventory,
        extravars=extra_vars or {},
        quiet=False,
    )

    print(f"Stato: {risultato.status}")  # successful, failed, timeout
    print(f"RC: {risultato.rc}")

    # Iterare sugli eventi
    for evento in risultato.events:
        if evento.get("event") == "runner_on_failed":
            host = evento["event_data"].get("host", "sconosciuto")
            task = evento["event_data"].get("task", "sconosciuta")
            print(f"FALLITO: {host} — task: {task}")

    return risultato.status == "successful"


# Utilizzo
esegui_playbook(
    playbook="site.yml",
    inventory="/etc/ansible/hosts",
    extra_vars={"app_version": "2.4.1", "environment": "production"},
)
```

---

## Script di System Administration

### Monitoraggio salute dei servizi

```python
"""Script di monitoraggio servizi con alert e report."""
import subprocess
import psutil
import logging
from dataclasses import dataclass
from datetime import datetime

log = logging.getLogger(__name__)


@dataclass
class StatoServizio:
    nome: str
    attivo: bool
    pid: int | None = None
    cpu_percent: float = 0.0
    mem_mb: float = 0.0
    uptime_sec: float = 0.0


def controlla_servizio_systemd(nome: str) -> StatoServizio:
    """Controlla lo stato di un servizio systemd."""
    risultato = subprocess.run(
        ["systemctl", "is-active", nome],
        capture_output=True, text=True, timeout=10,
    )
    attivo = risultato.stdout.strip() == "active"

    pid = None
    cpu = 0.0
    mem = 0.0
    if attivo:
        pid_result = subprocess.run(
            ["systemctl", "show", nome, "--property=MainPID", "--value"],
            capture_output=True, text=True, timeout=10,
        )
        try:
            pid = int(pid_result.stdout.strip())
            proc = psutil.Process(pid)
            cpu = proc.cpu_percent(interval=0.5)
            mem = proc.memory_info().rss / (1024 * 1024)
        except (ValueError, psutil.NoSuchProcess):
            pass

    return StatoServizio(nome=nome, attivo=attivo, pid=pid, cpu_percent=cpu, mem_mb=mem)


def report_servizi(servizi: list[str]) -> list[StatoServizio]:
    """Genera un report sullo stato di tutti i servizi."""
    risultati = []
    for servizio in servizi:
        stato = controlla_servizio_systemd(servizio)
        risultati.append(stato)
        emoji = "OK" if stato.attivo else "ERRORE"
        log.info(
            "[%s] %s — PID=%s, CPU=%.1f%%, MEM=%.1fMB",
            emoji, stato.nome, stato.pid, stato.cpu_percent, stato.mem_mb,
        )
    return risultati


# Utilizzo
# servizi = ["nginx", "postgresql", "redis-server", "app.service"]
# report_servizi(servizi)
```

---

## Automazione Processi Avanzata — pexpect e Signal Handling

### pexpect — Interazione con processi interattivi

`pexpect` consente di automatizzare processi interattivi che richiedono input da parte dell'utente — ad esempio `ssh`, `ftp`, `passwd`, `su`, `mysql` e qualsiasi applicazione a riga di comando che presenta prompt e attende risposte. A differenza di `subprocess`, che lavora con pipe di input/output, `pexpect` simula un terminale (pseudo-TTY) e puo leggere l'output in modo incrementale, reagendo a pattern specifici.

```python
# pip install pexpect

import pexpect
import logging

logger = logging.getLogger(__name__)


def ssh_interattivo(host: str, utente: str, password: str, comando: str) -> str:
    """
    Esegue un comando su un host remoto tramite SSH interattivo.
    Gestisce prompt di password e conferma host sconosciuto.
    """
    sessione = pexpect.spawn(f"ssh {utente}@{host}", timeout=30, encoding="utf-8")

    try:
        indice = sessione.expect([
            r"Are you sure you want to continue connecting",  # host sconosciuto
            r"[Pp]assword:",                                   # richiesta password
            pexpect.TIMEOUT,
            pexpect.EOF,
        ])

        if indice == 0:
            sessione.sendline("yes")
            sessione.expect(r"[Pp]assword:")
            sessione.sendline(password)
        elif indice == 1:
            sessione.sendline(password)
        else:
            raise RuntimeError("Timeout o connessione chiusa durante SSH")

        # Attende il prompt della shell
        sessione.expect(r"[\$#]\s*$")

        # Esecuzione comando
        sessione.sendline(comando)
        sessione.expect(r"[\$#]\s*$")
        output = sessione.before.strip()

        sessione.sendline("exit")
        sessione.expect(pexpect.EOF)

        return output

    except pexpect.ExceptionPexpect as e:
        logger.error("Errore pexpect: %s", e)
        raise
    finally:
        sessione.close()


def cambio_password_interattivo(utente: str, vecchia: str, nuova: str) -> bool:
    """Cambia la password di un utente locale tramite il comando passwd."""
    sessione = pexpect.spawn(f"passwd {utente}", timeout=15, encoding="utf-8")

    try:
        sessione.expect(r"[Cc]urrent.*[Pp]assword|[Oo]ld.*[Pp]assword")
        sessione.sendline(vecchia)

        sessione.expect(r"[Nn]ew.*[Pp]assword")
        sessione.sendline(nuova)

        sessione.expect(r"[Rr]etype|[Rr]e-enter|[Cc]onfirm")
        sessione.sendline(nuova)

        indice = sessione.expect([
            r"successfully|updated|changed",
            r"[Ee]rror|[Ff]ailed|[Bb]ad",
            pexpect.EOF,
        ])

        return indice == 0

    except pexpect.ExceptionPexpect as e:
        logger.error("Cambio password fallito: %s", e)
        return False
    finally:
        sessione.close()


def automazione_ftp(host: str, utente: str, password: str, file_remoto: str, file_locale: str):
    """Scarica un file da un server FTP tramite sessione interattiva."""
    sessione = pexpect.spawn(f"ftp {host}", timeout=30, encoding="utf-8")

    sessione.expect(r"[Nn]ame")
    sessione.sendline(utente)

    sessione.expect(r"[Pp]assword")
    sessione.sendline(password)

    sessione.expect(r"ftp>")
    sessione.sendline("binary")

    sessione.expect(r"ftp>")
    sessione.sendline(f"get {file_remoto} {file_locale}")

    sessione.expect(r"ftp>")
    sessione.sendline("bye")
    sessione.expect(pexpect.EOF)
    sessione.close()

    logger.info("File scaricato: %s -> %s", file_remoto, file_locale)
```

### Signal Handling nei processi di automazione

La gestione dei segnali e fondamentale per script di automazione che devono eseguire cleanup prima della terminazione, gestire interruzioni esterne (SIGTERM, SIGHUP) o implementare reload della configurazione (SIGUSR1). Python espone il modulo `signal` della libreria standard per registrare handler personalizzati.

```python
import signal
import sys
import logging
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class DaemonAutomazione:
    """
    Daemon di automazione con gestione segnali robusta.
    Supporta:
    - SIGTERM / SIGINT: shutdown graceful con cleanup
    - SIGHUP: reload configurazione senza restart
    - SIGUSR1: dump dello stato corrente su file
    """

    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.config: dict[str, Any] = {}
        self._running = True
        self._setup_segnali()

    def _setup_segnali(self):
        """Registra gli handler per i segnali."""
        signal.signal(signal.SIGTERM, self._gestisci_terminazione)
        signal.signal(signal.SIGINT, self._gestisci_terminazione)
        signal.signal(signal.SIGHUP, self._gestisci_reload)
        signal.signal(signal.SIGUSR1, self._gestisci_dump_stato)

    def _gestisci_terminazione(self, signum: int, frame):
        """Handler per SIGTERM e SIGINT — shutdown graceful."""
        nome_segnale = signal.Signals(signum).name
        logger.info("Ricevuto %s — avvio shutdown graceful...", nome_segnale)
        self._running = False

    def _gestisci_reload(self, signum: int, frame):
        """Handler per SIGHUP — ricarica la configurazione."""
        logger.info("Ricevuto SIGHUP — ricaricamento configurazione...")
        try:
            self._carica_config()
            logger.info("Configurazione ricaricata con successo")
        except Exception as e:
            logger.error("Errore ricaricamento configurazione: %s", e)

    def _gestisci_dump_stato(self, signum: int, frame):
        """Handler per SIGUSR1 — scrive lo stato su file."""
        stato_path = Path("/tmp/daemon_stato.txt")
        stato_path.write_text(
            f"PID: {os.getpid()}\n"
            f"Running: {self._running}\n"
            f"Config: {self.config}\n"
            f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        )
        logger.info("Stato scritto su %s", stato_path)

    def _carica_config(self):
        """Carica la configurazione dal file."""
        import json
        self.config = json.loads(self.config_path.read_text(encoding="utf-8"))

    def cleanup(self):
        """Esegue il cleanup delle risorse prima dello shutdown."""
        logger.info("Cleanup risorse in corso...")
        # Chiudere connessioni DB, file aperti, sessioni SSH, ecc.
        logger.info("Cleanup completato")

    def esegui(self):
        """Loop principale del daemon."""
        self._carica_config()
        logger.info("Daemon avviato — PID %d", os.getpid())

        try:
            while self._running:
                # Logica di automazione periodica
                time.sleep(self.config.get("intervallo_secondi", 60))
        finally:
            self.cleanup()
            logger.info("Daemon terminato")
            sys.exit(0)


import os

# Utilizzo
# daemon = DaemonAutomazione(Path("/etc/automazione/config.json"))
# daemon.esegui()
#
# Da terminale:
# kill -SIGHUP <PID>   -> ricarica configurazione
# kill -SIGUSR1 <PID>  -> dump stato
# kill -SIGTERM <PID>  -> shutdown graceful
```

### Gestione avanzata di processi con subprocess e segnali

```python
import subprocess
import signal
import os
import time
import logging

logger = logging.getLogger(__name__)


class GestoreProcessi:
    """Gestisce processi figli con timeout, segnali e cleanup."""

    def __init__(self):
        self._processi_attivi: dict[int, subprocess.Popen] = {}

    def avvia_processo(self, comando: list[str], nome: str = "") -> subprocess.Popen:
        """Avvia un processo figlio e lo traccia."""
        proc = subprocess.Popen(
            comando,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid,  # crea un nuovo process group
        )
        self._processi_attivi[proc.pid] = proc
        logger.info("Processo avviato: %s (PID=%d) — %s", nome or comando[0], proc.pid, " ".join(comando))
        return proc

    def termina_processo(self, pid: int, timeout: int = 10) -> bool:
        """Termina un processo con SIGTERM, fallback a SIGKILL."""
        proc = self._processi_attivi.get(pid)
        if not proc:
            return False

        # Prima prova con SIGTERM (terminazione graceful)
        try:
            os.killpg(os.getpgid(pid), signal.SIGTERM)
        except ProcessLookupError:
            del self._processi_attivi[pid]
            return True

        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            # Fallback a SIGKILL (terminazione forzata)
            logger.warning("Processo %d non risponde a SIGTERM — invio SIGKILL", pid)
            os.killpg(os.getpgid(pid), signal.SIGKILL)
            proc.wait(timeout=5)

        del self._processi_attivi[pid]
        return True

    def termina_tutti(self):
        """Termina tutti i processi attivi."""
        for pid in list(self._processi_attivi.keys()):
            self.termina_processo(pid)

    def controlla_stato(self) -> dict[int, str]:
        """Verifica lo stato di tutti i processi tracciati."""
        stati = {}
        for pid, proc in list(self._processi_attivi.items()):
            ret = proc.poll()
            if ret is None:
                stati[pid] = "in esecuzione"
            else:
                stati[pid] = f"terminato (exit code: {ret})"
                del self._processi_attivi[pid]
        return stati
```

---

## Desktop Automation — pyautogui e pygetwindow

L'automazione desktop consente di controllare programmaticamente mouse, tastiera e finestre del sistema operativo. Questo e utile per automatizzare applicazioni GUI che non espongono API, per test di interfaccia e per la creazione di macro ripetitive.

### pyautogui — Controllo mouse e tastiera

`pyautogui` e una libreria cross-platform (Windows, macOS, Linux) per il controllo del mouse e della tastiera. Supporta click, digitazione, screenshot, riconoscimento di immagini sullo schermo e hotkey.

```python
# pip install pyautogui pillow

import pyautogui
import time
import logging

logger = logging.getLogger(__name__)

# --- Configurazione di sicurezza ---
# FAILSAFE: spostare il mouse nell'angolo in alto a sinistra interrompe lo script
pyautogui.FAILSAFE = True
# Pausa tra ogni azione (previene azioni troppo rapide)
pyautogui.PAUSE = 0.5


# --- Informazioni sullo schermo ---
larghezza, altezza = pyautogui.size()
print(f"Risoluzione schermo: {larghezza}x{altezza}")
x, y = pyautogui.position()
print(f"Posizione mouse corrente: ({x}, {y})")


# --- Controllo del mouse ---
def click_sicuro(x: int, y: int, verifica_posizione: bool = True):
    """Click con verifica della posizione prima dell'azione."""
    if verifica_posizione:
        if x < 0 or y < 0 or x > larghezza or y > altezza:
            raise ValueError(f"Coordinate fuori schermo: ({x}, {y})")

    pyautogui.moveTo(x, y, duration=0.3)  # movimento fluido
    time.sleep(0.1)  # piccola pausa per la stabilita
    pyautogui.click()
    logger.info("Click eseguito: (%d, %d)", x, y)


# Movimenti del mouse
pyautogui.moveTo(500, 300, duration=0.5)    # movimento assoluto con durata
pyautogui.moveRel(100, 0, duration=0.2)     # movimento relativo
pyautogui.click(500, 300)                    # click sinistro
pyautogui.doubleClick(500, 300)              # doppio click
pyautogui.rightClick(500, 300)               # click destro
pyautogui.scroll(3)                          # scroll su di 3 unita
pyautogui.scroll(-3)                         # scroll giu di 3 unita


# --- Controllo della tastiera ---
pyautogui.write("Testo da digitare", interval=0.05)  # digitazione con intervallo
pyautogui.press("enter")                               # singolo tasto
pyautogui.press("tab")
pyautogui.hotkey("ctrl", "s")                          # combinazione di tasti
pyautogui.hotkey("ctrl", "a")                          # seleziona tutto
pyautogui.hotkey("ctrl", "c")                          # copia
pyautogui.hotkey("alt", "f4")                          # chiudi finestra


# --- Screenshot e riconoscimento immagini ---
def trova_e_clicca(immagine: str, confidenza: float = 0.9, timeout: int = 10) -> bool:
    """
    Cerca un'immagine sullo schermo e ci clicca sopra.
    Utile per automatizzare interfacce dove le coordinate cambiano.
    """
    inizio = time.time()
    while time.time() - inizio < timeout:
        posizione = pyautogui.locateOnScreen(immagine, confidence=confidenza)
        if posizione:
            centro = pyautogui.center(posizione)
            pyautogui.click(centro)
            logger.info("Immagine trovata e cliccata: %s a (%d, %d)", immagine, centro.x, centro.y)
            return True
        time.sleep(0.5)

    logger.warning("Immagine non trovata entro %d secondi: %s", timeout, immagine)
    return False


# Screenshot
screenshot = pyautogui.screenshot()
screenshot.save("/tmp/schermata.png")

# Screenshot di una regione specifica
regione = pyautogui.screenshot(region=(0, 0, 500, 400))
regione.save("/tmp/regione.png")
```

### Automazione di workflow desktop completi

```python
import pyautogui
import time
import subprocess


def apri_applicazione_e_compila(app_path: str, dati: dict[str, str]):
    """
    Esempio: apre un'applicazione desktop, naviga nei campi
    e compila un form automaticamente.
    """
    # Avvia l'applicazione
    subprocess.Popen([app_path])
    time.sleep(3)  # attende il caricamento

    for campo, valore in dati.items():
        pyautogui.press("tab")          # passa al campo successivo
        time.sleep(0.2)
        pyautogui.hotkey("ctrl", "a")   # seleziona contenuto esistente
        pyautogui.write(valore, interval=0.03)
        time.sleep(0.1)

    # Conferma il form
    pyautogui.hotkey("alt", "enter")


def screenshot_periodico(cartella: str, intervallo: int = 60, durata: int = 3600):
    """Cattura screenshot periodici per documentazione o monitoraggio."""
    from pathlib import Path
    from datetime import datetime

    dest = Path(cartella)
    dest.mkdir(parents=True, exist_ok=True)
    fine = time.time() + durata

    while time.time() < fine:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        percorso = dest / f"screenshot_{timestamp}.png"
        pyautogui.screenshot(str(percorso))
        time.sleep(intervallo)
```

### pygetwindow — Gestione finestre

```python
# pip install pygetwindow

import pygetwindow as gw


def trova_finestra(titolo_parziale: str):
    """Trova e attiva una finestra per titolo parziale."""
    finestre = gw.getWindowsWithTitle(titolo_parziale)
    if not finestre:
        raise RuntimeError(f"Nessuna finestra trovata con titolo: {titolo_parziale}")

    finestra = finestre[0]
    finestra.activate()       # porta in primo piano
    finestra.maximize()       # massimizza
    return finestra


def elenca_finestre_aperte() -> list[dict]:
    """Restituisce informazioni su tutte le finestre aperte."""
    risultati = []
    for finestra in gw.getAllWindows():
        if finestra.title:  # ignora finestre senza titolo
            risultati.append({
                "titolo": finestra.title,
                "posizione": (finestra.left, finestra.top),
                "dimensione": (finestra.width, finestra.height),
                "visibile": finestra.visible,
                "minimizzata": finestra.isMinimized,
            })
    return risultati


def disponi_finestre_affiancate(titoli: list[str]):
    """Dispone due finestre affiancate sullo schermo."""
    import pyautogui
    larghezza_schermo, altezza_schermo = pyautogui.size()
    meta_larghezza = larghezza_schermo // 2

    for i, titolo in enumerate(titoli[:2]):
        finestre = gw.getWindowsWithTitle(titolo)
        if finestre:
            finestra = finestre[0]
            finestra.restore()
            finestra.moveTo(i * meta_larghezza, 0)
            finestra.resizeTo(meta_larghezza, altezza_schermo)
```

---

## Automazione Documenti — python-docx e pypdf

L'automazione della generazione e manipolazione di documenti e uno degli ambiti piu richiesti in contesto aziendale: report periodici, contratti personalizzati, unione di PDF, estrazione di testo e compilazione di template.

### python-docx — Creazione e modifica di documenti Word

```python
# pip install python-docx

from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def genera_documento_da_template(
    dati: dict,
    output_path: str,
    logo_path: str | None = None
) -> str:
    """
    Genera un documento Word formattato con intestazione, tabelle,
    paragrafi e footer da un dizionario di dati.
    """
    doc = Document()

    # --- Stili e intestazione ---
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)

    # Logo se disponibile
    if logo_path and Path(logo_path).exists():
        doc.add_picture(logo_path, width=Inches(2))

    # Titolo
    titolo = doc.add_heading(dati["titolo"], level=1)
    titolo.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Sottotitolo con data
    sottotitolo = doc.add_paragraph()
    sottotitolo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = sottotitolo.add_run(f"Generato il {dati['data']}")
    run.font.size = Pt(10)
    run.font.color.rgb = RGBColor(128, 128, 128)

    doc.add_paragraph()  # spazio

    # --- Corpo del documento ---
    for sezione in dati.get("sezioni", []):
        doc.add_heading(sezione["titolo"], level=2)
        doc.add_paragraph(sezione["contenuto"])

    # --- Tabella dati ---
    if "tabella" in dati:
        doc.add_heading("Dati di Riepilogo", level=2)
        righe_dati = dati["tabella"]
        intestazioni = list(righe_dati[0].keys())

        tabella = doc.add_table(rows=1, cols=len(intestazioni))
        tabella.style = "Light Grid Accent 1"
        tabella.alignment = WD_TABLE_ALIGNMENT.CENTER

        # Intestazioni tabella
        for i, intestazione in enumerate(intestazioni):
            cella = tabella.rows[0].cells[i]
            cella.text = intestazione.upper()
            for paragraph in cella.paragraphs:
                for run in paragraph.runs:
                    run.font.bold = True
                    run.font.size = Pt(10)

        # Righe dati
        for riga in righe_dati:
            row = tabella.add_row()
            for i, intestazione in enumerate(intestazioni):
                row.cells[i].text = str(riga[intestazione])

    # --- Footer ---
    sezione_doc = doc.sections[0]
    footer = sezione_doc.footer
    paragrafo_footer = footer.paragraphs[0]
    paragrafo_footer.text = dati.get("footer", "Documento generato automaticamente")
    paragrafo_footer.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.save(output_path)
    logger.info("Documento Word generato: %s", output_path)
    return output_path


def compila_template_word(template_path: str, segnaposti: dict[str, str], output_path: str):
    """
    Compila un template Word sostituendo i segnaposti {{chiave}} con i valori.
    Utile per contratti, lettere, certificati personalizzati.
    """
    doc = Document(template_path)

    for paragrafo in doc.paragraphs:
        for chiave, valore in segnaposti.items():
            placeholder = "{{" + chiave + "}}"
            if placeholder in paragrafo.text:
                for run in paragrafo.runs:
                    if placeholder in run.text:
                        run.text = run.text.replace(placeholder, valore)

    # Sostituisci anche nelle tabelle
    for tabella in doc.tables:
        for riga in tabella.rows:
            for cella in riga.cells:
                for paragrafo in cella.paragraphs:
                    for chiave, valore in segnaposti.items():
                        placeholder = "{{" + chiave + "}}"
                        if placeholder in paragrafo.text:
                            for run in paragrafo.runs:
                                if placeholder in run.text:
                                    run.text = run.text.replace(placeholder, valore)

    doc.save(output_path)
    logger.info("Template compilato: %s -> %s", template_path, output_path)


# Utilizzo
genera_documento_da_template(
    dati={
        "titolo": "Report Infrastruttura Q1 2026",
        "data": "2026-03-31",
        "sezioni": [
            {"titolo": "Uptime", "contenuto": "Uptime medio del 99.7% nel trimestre."},
            {"titolo": "Incidenti", "contenuto": "3 incidenti risolti entro 2 ore."},
        ],
        "tabella": [
            {"server": "web01", "uptime": "99.9%", "incidenti": 0},
            {"server": "db01", "uptime": "99.2%", "incidenti": 2},
        ],
        "footer": "Report generato dal sistema di monitoraggio — Confidenziale",
    },
    output_path="/tmp/report_q1.docx",
)
```

### pypdf — Manipolazione di file PDF

La libreria `pypdf` (successore di PyPDF2) consente di leggere, unire, dividere, ruotare, crittografare e estrarre testo da file PDF senza dipendenze esterne.

```python
# pip install pypdf

from pypdf import PdfReader, PdfWriter, PdfMerger
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class GestorePDF:
    """Operazioni comuni su file PDF: merge, split, estrazione, protezione."""

    @staticmethod
    def unisci_pdf(file_input: list[str], output: str) -> str:
        """Unisce piu file PDF in un unico documento."""
        merger = PdfMerger()
        for pdf_path in file_input:
            merger.append(pdf_path)
            logger.info("Aggiunto al merge: %s", pdf_path)

        merger.write(output)
        merger.close()
        logger.info("PDF uniti in: %s (%d file)", output, len(file_input))
        return output

    @staticmethod
    def dividi_pdf(input_path: str, output_dir: str) -> list[str]:
        """Divide un PDF in singole pagine."""
        reader = PdfReader(input_path)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        file_generati = []

        for i, pagina in enumerate(reader.pages):
            writer = PdfWriter()
            writer.add_page(pagina)
            nome_file = output_path / f"pagina_{i + 1:03d}.pdf"
            with open(nome_file, "wb") as f:
                writer.write(f)
            file_generati.append(str(nome_file))

        logger.info("PDF diviso in %d pagine: %s", len(file_generati), output_dir)
        return file_generati

    @staticmethod
    def estrai_testo(pdf_path: str) -> str:
        """Estrae tutto il testo da un PDF."""
        reader = PdfReader(pdf_path)
        testo_completo = []
        for i, pagina in enumerate(reader.pages):
            testo = pagina.extract_text()
            if testo:
                testo_completo.append(f"--- Pagina {i + 1} ---\n{testo}")
        return "\n\n".join(testo_completo)

    @staticmethod
    def proteggi_pdf(input_path: str, output_path: str, password: str):
        """Aggiunge protezione con password a un PDF."""
        reader = PdfReader(input_path)
        writer = PdfWriter()

        for pagina in reader.pages:
            writer.add_page(pagina)

        writer.encrypt(user_password=password, owner_password=password)

        with open(output_path, "wb") as f:
            writer.write(f)

        logger.info("PDF protetto con password: %s", output_path)

    @staticmethod
    def estrai_metadati(pdf_path: str) -> dict:
        """Estrae i metadati di un PDF."""
        reader = PdfReader(pdf_path)
        meta = reader.metadata
        return {
            "titolo": meta.title if meta else None,
            "autore": meta.author if meta else None,
            "soggetto": meta.subject if meta else None,
            "creatore": meta.creator if meta else None,
            "numero_pagine": len(reader.pages),
        }

    @staticmethod
    def ruota_pagine(input_path: str, output_path: str, gradi: int = 90, pagine: list[int] | None = None):
        """Ruota pagine specifiche di un PDF (o tutte se pagine=None)."""
        reader = PdfReader(input_path)
        writer = PdfWriter()

        for i, pagina in enumerate(reader.pages):
            if pagine is None or i in pagine:
                pagina.rotate(gradi)
            writer.add_page(pagina)

        with open(output_path, "wb") as f:
            writer.write(f)

        logger.info("Pagine ruotate (%d gradi): %s", gradi, output_path)

    @staticmethod
    def aggiungi_watermark(input_path: str, watermark_path: str, output_path: str):
        """Sovrappone un watermark a tutte le pagine di un PDF."""
        reader_originale = PdfReader(input_path)
        reader_watermark = PdfReader(watermark_path)
        watermark_page = reader_watermark.pages[0]
        writer = PdfWriter()

        for pagina in reader_originale.pages:
            pagina.merge_page(watermark_page)
            writer.add_page(pagina)

        with open(output_path, "wb") as f:
            writer.write(f)

        logger.info("Watermark applicato: %s -> %s", input_path, output_path)


# Utilizzo
gestore = GestorePDF()

# Unire report mensili
gestore.unisci_pdf(
    ["/tmp/report_gen.pdf", "/tmp/report_feb.pdf", "/tmp/report_mar.pdf"],
    "/tmp/report_q1_completo.pdf"
)

# Estrarre testo per indicizzazione
testo = gestore.estrai_testo("/tmp/contratto.pdf")

# Proteggere un documento riservato
gestore.proteggi_pdf("/tmp/report_riservato.pdf", "/tmp/report_protetto.pdf", "s3cur3_P4ss!")
```

---

## Cloud Automation — boto3 e azure-sdk

L'automazione cloud consente di gestire programmaticamente risorse su AWS, Azure e altri provider, eliminando le operazioni manuali dalla console web. Python e il linguaggio piu utilizzato per l'automazione cloud grazie agli SDK ufficiali di tutti i principali provider.

### boto3 — Automazione AWS

`boto3` e l'SDK ufficiale di AWS per Python. Permette di gestire tutti i servizi AWS: EC2, S3, IAM, Lambda, RDS, CloudWatch e centinaia di altri.

```python
# pip install boto3

import boto3
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)


class GestoreAWS:
    """Operazioni comuni su AWS: S3, EC2, IAM."""

    def __init__(self, region: str = "eu-west-1"):
        self.session = boto3.Session(region_name=region)

    # --- S3 ---
    def elenca_bucket(self) -> list[str]:
        """Elenca tutti i bucket S3."""
        s3 = self.session.client("s3")
        risposta = s3.list_buckets()
        return [bucket["Name"] for bucket in risposta["Buckets"]]

    def upload_file(self, bucket: str, file_locale: str, chiave_s3: str):
        """Carica un file su S3."""
        s3 = self.session.client("s3")
        try:
            s3.upload_file(file_locale, bucket, chiave_s3)
            logger.info("Upload completato: %s -> s3://%s/%s", file_locale, bucket, chiave_s3)
        except ClientError as e:
            logger.error("Errore upload S3: %s", e)
            raise

    def scarica_file(self, bucket: str, chiave_s3: str, file_locale: str):
        """Scarica un file da S3."""
        s3 = self.session.client("s3")
        s3.download_file(bucket, chiave_s3, file_locale)
        logger.info("Download completato: s3://%s/%s -> %s", bucket, chiave_s3, file_locale)

    def sincronizza_cartella_s3(self, cartella_locale: str, bucket: str, prefisso: str = ""):
        """Carica tutti i file di una cartella locale su S3."""
        from pathlib import Path
        s3 = self.session.client("s3")
        cartella = Path(cartella_locale)

        for file in cartella.rglob("*"):
            if file.is_file():
                chiave = f"{prefisso}/{file.relative_to(cartella)}" if prefisso else str(file.relative_to(cartella))
                s3.upload_file(str(file), bucket, chiave)
                logger.info("Sincronizzato: %s", chiave)

    # --- EC2 ---
    def elenca_istanze(self, filtro_stato: str = "running") -> list[dict]:
        """Elenca le istanze EC2 filtrate per stato."""
        ec2 = self.session.client("ec2")
        risposta = ec2.describe_instances(
            Filters=[{"Name": "instance-state-name", "Values": [filtro_stato]}]
        )
        istanze = []
        for riserva in risposta["Reservations"]:
            for istanza in riserva["Instances"]:
                nome = ""
                for tag in istanza.get("Tags", []):
                    if tag["Key"] == "Name":
                        nome = tag["Value"]
                istanze.append({
                    "id": istanza["InstanceId"],
                    "nome": nome,
                    "tipo": istanza["InstanceType"],
                    "stato": istanza["State"]["Name"],
                    "ip_privato": istanza.get("PrivateIpAddress"),
                    "ip_pubblico": istanza.get("PublicIpAddress"),
                })
        return istanze

    def gestisci_istanza(self, instance_id: str, azione: str):
        """Avvia, ferma o riavvia un'istanza EC2."""
        ec2 = self.session.client("ec2")
        azioni = {
            "avvia": ec2.start_instances,
            "ferma": ec2.stop_instances,
            "riavvia": ec2.reboot_instances,
        }
        if azione not in azioni:
            raise ValueError(f"Azione non valida: {azione}. Valide: {list(azioni.keys())}")

        azioni[azione](InstanceIds=[instance_id])
        logger.info("Istanza %s: azione '%s' eseguita", instance_id, azione)

    # --- CloudWatch ---
    def crea_allarme(self, nome: str, instance_id: str, metrica: str, soglia: float):
        """Crea un allarme CloudWatch per un'istanza EC2."""
        cloudwatch = self.session.client("cloudwatch")
        cloudwatch.put_metric_alarm(
            AlarmName=nome,
            Namespace="AWS/EC2",
            MetricName=metrica,
            Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
            Statistic="Average",
            Period=300,
            EvaluationPeriods=2,
            Threshold=soglia,
            ComparisonOperator="GreaterThanThreshold",
            AlarmActions=[],  # aggiungere ARN di SNS topic per notifiche
        )
        logger.info("Allarme creato: %s (soglia: %.1f)", nome, soglia)


# Utilizzo
aws = GestoreAWS(region="eu-west-1")

# Backup locale su S3
aws.upload_file("backup-azienda", "/tmp/backup_db.tar.gz", "database/2026/05/backup_db.tar.gz")

# Elenco istanze running
for ist in aws.elenca_istanze():
    print(f"  {ist['nome']} ({ist['id']}): {ist['tipo']} — IP: {ist['ip_privato']}")
```

### azure-sdk — Automazione Microsoft Azure

```python
# pip install azure-identity azure-mgmt-compute azure-mgmt-resource azure-storage-blob

from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.storage.blob import BlobServiceClient
import logging

logger = logging.getLogger(__name__)


class GestoreAzure:
    """Operazioni comuni su Azure: VM, Storage, Resource Groups."""

    def __init__(self, subscription_id: str):
        self.credential = DefaultAzureCredential()
        self.subscription_id = subscription_id

    def elenca_vm(self, resource_group: str) -> list[dict]:
        """Elenca le virtual machine in un resource group."""
        compute = ComputeManagementClient(self.credential, self.subscription_id)
        vm_list = compute.virtual_machines.list(resource_group)
        risultati = []
        for vm in vm_list:
            risultati.append({
                "nome": vm.name,
                "posizione": vm.location,
                "dimensione": vm.hardware_profile.vm_size,
                "stato": vm.provisioning_state,
            })
        return risultati

    def gestisci_vm(self, resource_group: str, vm_name: str, azione: str):
        """Avvia, ferma o riavvia una VM Azure."""
        compute = ComputeManagementClient(self.credential, self.subscription_id)
        azioni = {
            "avvia": compute.virtual_machines.begin_start,
            "ferma": compute.virtual_machines.begin_deallocate,
            "riavvia": compute.virtual_machines.begin_restart,
        }
        if azione not in azioni:
            raise ValueError(f"Azione non valida: {azione}")

        operazione = azioni[azione](resource_group, vm_name)
        operazione.result()  # attende il completamento
        logger.info("VM %s: azione '%s' completata", vm_name, azione)

    def upload_blob(self, connection_string: str, container: str, file_locale: str, blob_name: str):
        """Carica un file su Azure Blob Storage."""
        blob_service = BlobServiceClient.from_connection_string(connection_string)
        blob_client = blob_service.get_blob_client(container=container, blob=blob_name)

        with open(file_locale, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)

        logger.info("Blob caricato: %s -> %s/%s", file_locale, container, blob_name)

    def elenca_resource_groups(self) -> list[dict]:
        """Elenca tutti i resource group della sottoscrizione."""
        resource = ResourceManagementClient(self.credential, self.subscription_id)
        gruppi = []
        for rg in resource.resource_groups.list():
            gruppi.append({
                "nome": rg.name,
                "posizione": rg.location,
                "stato": rg.properties.provisioning_state,
            })
        return gruppi
```

---

## Sistemi di Notifica — Slack, Discord e Teams

I sistemi di notifica sono un componente essenziale delle pipeline di automazione: informano i team quando un job viene completato, un errore si verifica o una soglia viene superata. Python puo integrarsi con Slack, Discord, Microsoft Teams e altri servizi tramite webhook e API.

### Slack — Webhook e Bot

```python
# pip install requests

import requests
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class NotificatoreSlack:
    """Invia notifiche a Slack tramite webhook o Bot API."""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def invia_messaggio(self, testo: str, canale: str | None = None) -> bool:
        """Invia un messaggio semplice a Slack."""
        payload = {"text": testo}
        if canale:
            payload["channel"] = canale

        risposta = requests.post(
            self.webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        successo = risposta.status_code == 200
        if not successo:
            logger.error("Errore Slack (%d): %s", risposta.status_code, risposta.text)
        return successo

    def invia_alert(self, titolo: str, messaggio: str, severita: str = "warning"):
        """Invia un alert formattato con Block Kit."""
        colori = {"info": "#36a64f", "warning": "#ff9900", "error": "#ff0000", "critical": "#990000"}
        colore = colori.get(severita, "#cccccc")

        payload = {
            "attachments": [{
                "color": colore,
                "blocks": [
                    {
                        "type": "header",
                        "text": {"type": "plain_text", "text": f"[{severita.upper()}] {titolo}"}
                    },
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": messaggio}
                    },
                    {
                        "type": "context",
                        "elements": [
                            {"type": "mrkdwn", "text": f"Timestamp: {datetime.now().isoformat()}"}
                        ]
                    }
                ]
            }]
        }

        return self._invia_payload(payload)

    def invia_report_job(self, nome_job: str, stato: str, durata_sec: float, dettagli: str = ""):
        """Invia un report sullo stato di un job di automazione."""
        emoji = ":white_check_mark:" if stato == "successo" else ":x:"
        testo = (
            f"{emoji} *Job: {nome_job}*\n"
            f"Stato: `{stato}`\n"
            f"Durata: {durata_sec:.1f}s\n"
        )
        if dettagli:
            testo += f"Dettagli: {dettagli}"

        return self.invia_messaggio(testo)

    def _invia_payload(self, payload: dict) -> bool:
        risposta = requests.post(self.webhook_url, json=payload, timeout=10)
        return risposta.status_code == 200


# Utilizzo
# slack = NotificatoreSlack(webhook_url=os.environ["SLACK_WEBHOOK_URL"])
# slack.invia_alert("Disco quasi pieno", "Server db01: utilizzo disco al 92%", severita="warning")
# slack.invia_report_job("backup_notturno", "successo", durata_sec=145.3)
```

### Discord — Webhook

```python
import requests
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class NotificatoreDiscord:
    """Invia notifiche a Discord tramite webhook."""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def invia_messaggio(self, contenuto: str, username: str = "AutomationBot") -> bool:
        """Invia un messaggio semplice a Discord."""
        payload = {"content": contenuto, "username": username}
        risposta = requests.post(self.webhook_url, json=payload, timeout=10)
        return risposta.status_code in (200, 204)

    def invia_embed(self, titolo: str, descrizione: str, colore: int = 0x00FF00, campi: list[dict] | None = None):
        """Invia un messaggio con embed formattato."""
        embed = {
            "title": titolo,
            "description": descrizione,
            "color": colore,
            "timestamp": datetime.now().isoformat(),
            "footer": {"text": "Sistema Automazione"},
        }
        if campi:
            embed["fields"] = [
                {"name": c["nome"], "value": c["valore"], "inline": c.get("inline", True)}
                for c in campi
            ]

        payload = {"embeds": [embed], "username": "AutomationBot"}
        risposta = requests.post(self.webhook_url, json=payload, timeout=10)
        return risposta.status_code in (200, 204)


# Utilizzo
# discord = NotificatoreDiscord(webhook_url=os.environ["DISCORD_WEBHOOK_URL"])
# discord.invia_embed(
#     titolo="Backup Completato",
#     descrizione="Il backup notturno e stato completato con successo.",
#     colore=0x00FF00,  # verde
#     campi=[
#         {"nome": "Server", "valore": "db01"},
#         {"nome": "Durata", "valore": "2m 15s"},
#         {"nome": "Dimensione", "valore": "3.2 GB"},
#     ]
# )
```

### Microsoft Teams — Webhook

```python
import requests
import logging

logger = logging.getLogger(__name__)


class NotificatoreTeams:
    """Invia notifiche a Microsoft Teams tramite webhook (Adaptive Cards)."""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def invia_card(self, titolo: str, messaggio: str, severita: str = "info") -> bool:
        """Invia una Adaptive Card a Teams."""
        colori = {"info": "good", "warning": "warning", "error": "attention"}

        card = {
            "type": "message",
            "attachments": [{
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "type": "AdaptiveCard",
                    "version": "1.4",
                    "body": [
                        {
                            "type": "TextBlock",
                            "text": titolo,
                            "weight": "bolder",
                            "size": "medium",
                            "color": colori.get(severita, "default"),
                        },
                        {
                            "type": "TextBlock",
                            "text": messaggio,
                            "wrap": True,
                        },
                    ],
                }
            }]
        }

        risposta = requests.post(self.webhook_url, json=card, timeout=10)
        successo = risposta.status_code == 200
        if not successo:
            logger.error("Errore Teams (%d): %s", risposta.status_code, risposta.text)
        return successo
```

### Notificatore unificato multi-canale

```python
from dataclasses import dataclass
import os
import logging

logger = logging.getLogger(__name__)


@dataclass
class ConfigNotifiche:
    slack_webhook: str | None = None
    discord_webhook: str | None = None
    teams_webhook: str | None = None


class NotificatoreUnificato:
    """Invia notifiche a tutti i canali configurati."""

    def __init__(self, config: ConfigNotifiche):
        self.canali = []
        if config.slack_webhook:
            self.canali.append(NotificatoreSlack(config.slack_webhook))
        if config.discord_webhook:
            self.canali.append(NotificatoreDiscord(config.discord_webhook))
        if config.teams_webhook:
            self.canali.append(NotificatoreTeams(config.teams_webhook))

    def notifica(self, titolo: str, messaggio: str, severita: str = "info"):
        """Invia una notifica a tutti i canali configurati."""
        for canale in self.canali:
            try:
                if isinstance(canale, NotificatoreSlack):
                    canale.invia_alert(titolo, messaggio, severita)
                elif isinstance(canale, NotificatoreDiscord):
                    colori = {"info": 0x00FF00, "warning": 0xFF9900, "error": 0xFF0000}
                    canale.invia_embed(titolo, messaggio, colori.get(severita, 0xCCCCCC))
                elif isinstance(canale, NotificatoreTeams):
                    canale.invia_card(titolo, messaggio, severita)
            except Exception as e:
                logger.error("Errore invio notifica su %s: %s", type(canale).__name__, e)


# Utilizzo
# notificatore = NotificatoreUnificato(ConfigNotifiche(
#     slack_webhook=os.environ.get("SLACK_WEBHOOK_URL"),
#     discord_webhook=os.environ.get("DISCORD_WEBHOOK_URL"),
# ))
# notificatore.notifica("Backup fallito", "Il backup del database db01 ha fallito dopo 3 tentativi.", "error")
```

---

## Data Pipeline Automation

Le pipeline di dati automatizzate combinano monitoraggio del filesystem, trasformazione dei dati, caricamento in database e generazione di report. Python eccelle in questo ambito grazie alla sinergia tra librerie come `watchdog`, `pandas`, `sqlite3`/`sqlalchemy` e `openpyxl`.

### Pipeline completa: file ingresso -> elaborazione -> database -> report

```python
from pathlib import Path
from datetime import datetime
import sqlite3
import csv
import json
import logging
import hashlib

logger = logging.getLogger(__name__)


class PipelineDati:
    """
    Pipeline di automazione dati con le seguenti fasi:
    1. Rilevamento file in ingresso
    2. Validazione formato e contenuto
    3. Trasformazione e pulizia
    4. Caricamento in database
    5. Archiviazione file originale
    6. Generazione report
    """

    def __init__(self, config: dict):
        self.ingresso = Path(config["cartella_ingresso"])
        self.archivio = Path(config["cartella_archivio"])
        self.errori = Path(config["cartella_errori"])
        self.db_path = config["database"]

        # Creazione directory necessarie
        for cartella in [self.ingresso, self.archivio, self.errori]:
            cartella.mkdir(parents=True, exist_ok=True)

    def elabora_file(self, percorso: Path) -> dict:
        """Elabora un singolo file CSV attraverso tutte le fasi della pipeline."""
        risultato = {
            "file": percorso.name,
            "timestamp": datetime.now().isoformat(),
            "stato": "in_corso",
            "righe_elaborate": 0,
            "errori": [],
        }

        try:
            # Fase 1: Validazione
            dati = self._valida_file(percorso)
            logger.info("Validazione OK: %s (%d righe)", percorso.name, len(dati))

            # Fase 2: Trasformazione
            dati_puliti = self._trasforma_dati(dati)

            # Fase 3: Caricamento
            righe_inserite = self._carica_in_database(dati_puliti)
            risultato["righe_elaborate"] = righe_inserite

            # Fase 4: Archiviazione
            self._archivia_file(percorso)
            risultato["stato"] = "completato"
            logger.info("Pipeline completata per %s: %d righe", percorso.name, righe_inserite)

        except Exception as e:
            risultato["stato"] = "errore"
            risultato["errori"].append(str(e))
            self._sposta_in_errori(percorso)
            logger.error("Pipeline fallita per %s: %s", percorso.name, e)

        return risultato

    def _valida_file(self, percorso: Path) -> list[dict]:
        """Valida il formato e il contenuto del file CSV."""
        if percorso.stat().st_size == 0:
            raise ValueError("File vuoto")

        if percorso.stat().st_size > 100 * 1024 * 1024:  # 100 MB max
            raise ValueError("File troppo grande (limite: 100 MB)")

        with open(percorso, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            dati = list(reader)

        if not dati:
            raise ValueError("Nessuna riga di dati nel file")

        return dati

    def _trasforma_dati(self, dati: list[dict]) -> list[dict]:
        """Pulisce e trasforma i dati."""
        dati_puliti = []
        for riga in dati:
            riga_pulita = {}
            for chiave, valore in riga.items():
                chiave_pulita = chiave.strip().lower().replace(" ", "_")
                valore_pulito = valore.strip() if isinstance(valore, str) else valore
                riga_pulita[chiave_pulita] = valore_pulito
            dati_puliti.append(riga_pulita)
        return dati_puliti

    def _carica_in_database(self, dati: list[dict]) -> int:
        """Carica i dati in SQLite."""
        if not dati:
            return 0

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        colonne = list(dati[0].keys())
        colonne_def = ", ".join(f'"{col}" TEXT' for col in colonne)
        cursor.execute(f'CREATE TABLE IF NOT EXISTS dati_importati ({colonne_def}, _importato_il TEXT)')

        placeholders = ", ".join(["?"] * (len(colonne) + 1))
        timestamp = datetime.now().isoformat()

        for riga in dati:
            valori = [riga.get(col, "") for col in colonne] + [timestamp]
            cursor.execute(f"INSERT INTO dati_importati VALUES ({placeholders})", valori)

        conn.commit()
        conn.close()
        return len(dati)

    def _archivia_file(self, percorso: Path):
        """Sposta il file nell'archivio con timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = self.archivio / f"{timestamp}_{percorso.name}"
        percorso.rename(dest)

    def _sposta_in_errori(self, percorso: Path):
        """Sposta il file nella cartella errori."""
        if percorso.exists():
            dest = self.errori / f"ERR_{datetime.now():%Y%m%d_%H%M%S}_{percorso.name}"
            percorso.rename(dest)

    def elabora_tutti(self) -> list[dict]:
        """Elabora tutti i file CSV nella cartella di ingresso."""
        risultati = []
        for file_csv in sorted(self.ingresso.glob("*.csv")):
            risultato = self.elabora_file(file_csv)
            risultati.append(risultato)
        return risultati


# Integrazione con watchdog per trigger automatico
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time


class TriggerPipeline(FileSystemEventHandler):
    """Trigger automatico della pipeline quando arriva un nuovo file."""

    def __init__(self, pipeline: PipelineDati):
        self.pipeline = pipeline

    def on_created(self, event):
        if event.is_directory or not event.src_path.endswith(".csv"):
            return
        # Attende che il file sia completamente scritto
        time.sleep(1)
        percorso = Path(event.src_path)
        if percorso.exists():
            risultato = self.pipeline.elabora_file(percorso)
            logger.info("Pipeline trigger automatico: %s", risultato)


# Utilizzo
# pipeline = PipelineDati({
#     "cartella_ingresso": "/opt/dati/ingresso",
#     "cartella_archivio": "/opt/dati/archivio",
#     "cartella_errori": "/opt/dati/errori",
#     "database": "/opt/dati/pipeline.db",
# })
#
# trigger = TriggerPipeline(pipeline)
# observer = Observer()
# observer.schedule(trigger, "/opt/dati/ingresso", recursive=False)
# observer.start()
```

---

## Gestione Configurazione per l'Automazione

La gestione della configurazione e un aspetto critico per script di automazione robusti. Separare la configurazione dal codice consente di adattare il comportamento degli script senza modificare il sorgente, gestire ambienti multipli (sviluppo, staging, produzione) e mantenere i segreti fuori dal version control.

### python-dotenv — File .env

```python
# pip install python-dotenv

from dotenv import load_dotenv
import os
from pathlib import Path


def carica_configurazione(env_file: str = ".env") -> dict:
    """
    Carica le variabili d'ambiente dal file .env.
    Le variabili d'ambiente di sistema hanno precedenza sul file .env.
    """
    env_path = Path(env_file)
    if env_path.exists():
        load_dotenv(env_path, override=False)  # override=False: non sovrascrive variabili gia definite

    config = {
        "database_url": os.environ.get("DATABASE_URL", "sqlite:///default.db"),
        "smtp_server": os.environ.get("SMTP_SERVER", "localhost"),
        "smtp_porta": int(os.environ.get("SMTP_PORT", "587")),
        "log_level": os.environ.get("LOG_LEVEL", "INFO"),
        "backup_path": os.environ.get("BACKUP_PATH", "/tmp/backup"),
        "slack_webhook": os.environ.get("SLACK_WEBHOOK_URL"),
        "max_retry": int(os.environ.get("MAX_RETRY", "3")),
    }

    # Validazione — fail fast se mancano configurazioni obbligatorie
    obbligatorie = ["database_url", "smtp_server"]
    mancanti = [k for k in obbligatorie if not config.get(k)]
    if mancanti:
        raise EnvironmentError(f"Variabili d'ambiente mancanti: {mancanti}")

    return config
```

### TOML e YAML — Configurazione strutturata

```python
# --- TOML (stdlib da Python 3.11+) ---
import tomllib  # Python 3.11+
from pathlib import Path


def carica_config_toml(percorso: str) -> dict:
    """Carica configurazione da file TOML."""
    with open(percorso, "rb") as f:
        return tomllib.load(f)


# config.toml:
# [database]
# url = "postgresql://user:pass@host/db"
# pool_size = 10
#
# [backup]
# path = "/backup"
# retention_days = 30
# compressione = true
#
# [notifiche]
# canali = ["slack", "email"]
# [notifiche.slack]
# webhook_url = "https://hooks.slack.com/..."


# --- YAML ---
# pip install pyyaml

import yaml


def carica_config_yaml(percorso: str) -> dict:
    """Carica configurazione da file YAML con gestione sicura."""
    with open(percorso, "r", encoding="utf-8") as f:
        # safe_load previene l'esecuzione di codice arbitrario
        return yaml.safe_load(f)


def salva_config_yaml(config: dict, percorso: str):
    """Salva configurazione in formato YAML."""
    with open(percorso, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
```

### dynaconf — Configurazione multi-ambiente

```python
# pip install dynaconf

from dynaconf import Dynaconf


def crea_configurazione() -> Dynaconf:
    """
    Configura dynaconf con supporto multi-ambiente.
    Carica da: settings.toml, .secrets.toml, variabili d'ambiente.
    L'ambiente e determinato dalla variabile ENV_FOR_DYNACONF.
    """
    settings = Dynaconf(
        envvar_prefix="AUTOMAZIONE",         # variabili come AUTOMAZIONE_DATABASE_URL
        settings_files=["settings.toml", ".secrets.toml"],
        environments=True,                    # supporto [development], [production]
        load_dotenv=True,                     # carica anche .env
    )
    return settings


# settings.toml:
# [default]
# log_level = "INFO"
# max_retry = 3
#
# [development]
# database_url = "sqlite:///dev.db"
# debug = true
#
# [production]
# database_url = "postgresql://prod:5432/app"
# debug = false

# .secrets.toml (non versionato):
# [default]
# smtp_password = "valore_segreto"
# api_key = "chiave_segreta"

# Utilizzo
# export ENV_FOR_DYNACONF=production
# settings = crea_configurazione()
# print(settings.DATABASE_URL)  # postgresql://prod:5432/app
```

---

## Error Handling e Retry Pattern per l'Automazione

Le operazioni di automazione — chiamate di rete, accessi a database, trasferimenti di file, interazioni con API esterne — sono soggette a fallimenti transitori. Un sistema di retry ben progettato e la differenza tra un'automazione fragile e una resiliente.

### tenacity — Retry avanzato

`tenacity` e la libreria di riferimento per implementare retry con backoff esponenziale, jitter, condizioni personalizzate e callback. E l'evoluzione mantenuta di `retrying`.

```python
# pip install tenacity

from tenacity import (
    retry,
    stop_after_attempt,
    stop_after_delay,
    wait_exponential,
    wait_random,
    retry_if_exception_type,
    retry_if_result,
    before_sleep_log,
    after_log,
    RetryError,
)
import requests
import logging

logger = logging.getLogger(__name__)


# --- Retry base con backoff esponenziale ---
@retry(
    stop=stop_after_attempt(5),                        # massimo 5 tentativi
    wait=wait_exponential(multiplier=1, min=2, max=30), # attesa: 2s, 4s, 8s, 16s, 30s
    retry=retry_if_exception_type((requests.ConnectionError, requests.Timeout)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
)
def chiamata_api_resiliente(url: str, payload: dict) -> dict:
    """Chiamata API con retry automatico su errori di rete."""
    risposta = requests.post(url, json=payload, timeout=10)
    risposta.raise_for_status()
    return risposta.json()


# --- Retry con condizione sul risultato ---
@retry(
    stop=stop_after_attempt(10),
    wait=wait_exponential(multiplier=2, min=5, max=60),
    retry=retry_if_result(lambda r: r.get("stato") != "completato"),
)
def attendi_completamento_job(job_id: str) -> dict:
    """Polling su un job asincrono fino al completamento."""
    risposta = requests.get(f"https://api.esempio.com/jobs/{job_id}", timeout=10)
    return risposta.json()


# --- Retry con timeout totale ---
@retry(
    stop=stop_after_delay(300),  # timeout totale di 5 minuti
    wait=wait_exponential(multiplier=1, min=1, max=30) + wait_random(0, 2),  # jitter
)
def operazione_con_timeout_totale():
    """Riprova per un massimo di 5 minuti con jitter."""
    pass


# --- Classe con retry configurabile ---
class ClienteAPIResiliente:
    """Client HTTP con retry, circuit breaker e logging."""

    def __init__(self, base_url: str, max_tentativi: int = 3, timeout: int = 10):
        self.base_url = base_url
        self.max_tentativi = max_tentativi
        self.timeout = timeout
        self.sessione = requests.Session()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((requests.ConnectionError, requests.Timeout)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    def get(self, endpoint: str, params: dict | None = None) -> dict:
        """GET con retry automatico."""
        risposta = self.sessione.get(
            f"{self.base_url}{endpoint}",
            params=params,
            timeout=self.timeout,
        )
        risposta.raise_for_status()
        return risposta.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((requests.ConnectionError, requests.Timeout)),
    )
    def post(self, endpoint: str, data: dict) -> dict:
        """POST con retry automatico."""
        risposta = self.sessione.post(
            f"{self.base_url}{endpoint}",
            json=data,
            timeout=self.timeout,
        )
        risposta.raise_for_status()
        return risposta.json()
```

### Circuit Breaker Pattern

Il pattern Circuit Breaker previene il sovraccarico di servizi gia in difficolta, interrompendo temporaneamente le chiamate dopo un certo numero di fallimenti consecutivi.

```python
import time
import logging
from enum import Enum
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class StatoCircuito(Enum):
    CHIUSO = "chiuso"           # funzionamento normale
    APERTO = "aperto"           # blocca le chiamate
    SEMI_APERTO = "semi_aperto"  # permette una chiamata di test


@dataclass
class CircuitBreaker:
    """
    Implementazione del pattern Circuit Breaker.
    - CHIUSO: le chiamate passano normalmente
    - APERTO: le chiamate vengono bloccate (fail-fast)
    - SEMI_APERTO: una singola chiamata passa per testare il recupero
    """
    soglia_fallimenti: int = 5
    timeout_reset_sec: float = 60.0
    _stato: StatoCircuito = field(default=StatoCircuito.CHIUSO, init=False)
    _contatore_fallimenti: int = field(default=0, init=False)
    _ultimo_fallimento: float = field(default=0.0, init=False)

    @property
    def stato(self) -> StatoCircuito:
        if self._stato == StatoCircuito.APERTO:
            if time.time() - self._ultimo_fallimento >= self.timeout_reset_sec:
                self._stato = StatoCircuito.SEMI_APERTO
                logger.info("Circuit breaker: APERTO -> SEMI_APERTO")
        return self._stato

    def esegui(self, funzione, *args, **kwargs):
        """Esegue una funzione attraverso il circuit breaker."""
        stato_corrente = self.stato

        if stato_corrente == StatoCircuito.APERTO:
            raise RuntimeError("Circuit breaker APERTO — servizio non disponibile")

        try:
            risultato = funzione(*args, **kwargs)
            self._registra_successo()
            return risultato

        except Exception as e:
            self._registra_fallimento()
            raise

    def _registra_successo(self):
        """Registra un successo — resetta il circuito a CHIUSO."""
        if self._stato == StatoCircuito.SEMI_APERTO:
            logger.info("Circuit breaker: SEMI_APERTO -> CHIUSO")
        self._stato = StatoCircuito.CHIUSO
        self._contatore_fallimenti = 0

    def _registra_fallimento(self):
        """Registra un fallimento — potrebbe aprire il circuito."""
        self._contatore_fallimenti += 1
        self._ultimo_fallimento = time.time()

        if self._contatore_fallimenti >= self.soglia_fallimenti:
            self._stato = StatoCircuito.APERTO
            logger.warning(
                "Circuit breaker: CHIUSO -> APERTO dopo %d fallimenti consecutivi",
                self._contatore_fallimenti,
            )


# Utilizzo
# breaker = CircuitBreaker(soglia_fallimenti=3, timeout_reset_sec=30)
# try:
#     risultato = breaker.esegui(chiamata_api_resiliente, url, payload)
# except RuntimeError:
#     logger.warning("Servizio non disponibile — circuit breaker aperto")
```

---

## Windows Task Scheduler da Python

Su sistemi Windows, il Task Scheduler e l'equivalente di cron per la pianificazione di task. Python puo interagire con il Task Scheduler tramite `subprocess` con il comando `schtasks` o tramite l'interfaccia COM.

### schtasks via subprocess

```python
import subprocess
import logging

logger = logging.getLogger(__name__)


class GestoreTaskScheduler:
    """Gestisce i task pianificati di Windows tramite schtasks."""

    @staticmethod
    def crea_task(
        nome: str,
        comando: str,
        schedule_type: str = "DAILY",
        ora: str = "02:00",
        utente: str = "SYSTEM",
    ) -> bool:
        """
        Crea un task pianificato in Windows Task Scheduler.

        schedule_type: MINUTE, HOURLY, DAILY, WEEKLY, MONTHLY, ONCE
        """
        cmd = [
            "schtasks", "/Create",
            "/TN", nome,
            "/TR", comando,
            "/SC", schedule_type,
            "/ST", ora,
            "/RU", utente,
            "/F",  # sovrascrive se esiste
        ]

        risultato = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        successo = risultato.returncode == 0

        if successo:
            logger.info("Task creato: %s (%s alle %s)", nome, schedule_type, ora)
        else:
            logger.error("Errore creazione task: %s", risultato.stderr)

        return successo

    @staticmethod
    def elimina_task(nome: str) -> bool:
        """Elimina un task pianificato."""
        risultato = subprocess.run(
            ["schtasks", "/Delete", "/TN", nome, "/F"],
            capture_output=True, text=True, timeout=30,
        )
        return risultato.returncode == 0

    @staticmethod
    def esegui_task(nome: str) -> bool:
        """Esegue immediatamente un task pianificato."""
        risultato = subprocess.run(
            ["schtasks", "/Run", "/TN", nome],
            capture_output=True, text=True, timeout=30,
        )
        return risultato.returncode == 0

    @staticmethod
    def elenca_task(filtro: str = "") -> str:
        """Elenca i task pianificati, opzionalmente filtrati per nome."""
        cmd = ["schtasks", "/Query", "/FO", "LIST", "/V"]
        risultato = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if filtro:
            righe = [r for r in risultato.stdout.split("\n") if filtro.lower() in r.lower()]
            return "\n".join(righe)

        return risultato.stdout

    @staticmethod
    def stato_task(nome: str) -> dict:
        """Recupera lo stato di un task specifico."""
        risultato = subprocess.run(
            ["schtasks", "/Query", "/TN", nome, "/FO", "LIST", "/V"],
            capture_output=True, text=True, timeout=30,
        )

        info = {}
        for riga in risultato.stdout.split("\n"):
            if ":" in riga:
                parti = riga.split(":", 1)
                if len(parti) == 2:
                    chiave = parti[0].strip()
                    valore = parti[1].strip()
                    info[chiave] = valore

        return info


# Utilizzo (solo su Windows)
# scheduler = GestoreTaskScheduler()
#
# # Crea un task per il backup giornaliero alle 02:00
# scheduler.crea_task(
#     nome="Backup_Database_Giornaliero",
#     comando=r"C:\Python311\python.exe C:\Scripts\backup_db.py",
#     schedule_type="DAILY",
#     ora="02:00",
# )
#
# # Task settimanale ogni lunedi alle 08:00
# scheduler.crea_task(
#     nome="Report_Settimanale",
#     comando=r"C:\Python311\python.exe C:\Scripts\report.py",
#     schedule_type="WEEKLY",
#     ora="08:00",
# )
```

---

## Browser Automation Avanzata — Playwright

Playwright offre un'alternativa moderna e piu affidabile a Selenium per l'automazione del browser. Supporta Chromium, Firefox e WebKit con un'API unificata, auto-wait intelligente e isolamento tramite browser context.

```python
# pip install playwright
# playwright install

from playwright.sync_api import sync_playwright, Page, BrowserContext
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class AutomazioneBrowser:
    """Automazione browser con Playwright — operazioni comuni."""

    def __init__(self, headless: bool = True, browser_type: str = "chromium"):
        self.headless = headless
        self.browser_type = browser_type
        self._playwright = None
        self._browser = None

    def __enter__(self):
        self._playwright = sync_playwright().start()
        launcher = getattr(self._playwright, self.browser_type)
        self._browser = launcher.launch(headless=self.headless)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()

    def nuovo_contesto(self, **kwargs) -> BrowserContext:
        """Crea un contesto browser isolato (cookie, storage separati)."""
        return self._browser.new_context(**kwargs)

    def screenshot_pagina(self, url: str, output: str, attesa_sel: str | None = None, full_page: bool = True):
        """Cattura uno screenshot di una pagina web."""
        pagina = self._browser.new_page()
        try:
            pagina.goto(url, wait_until="networkidle")
            if attesa_sel:
                pagina.wait_for_selector(attesa_sel, timeout=15000)
            pagina.screenshot(path=output, full_page=full_page)
            logger.info("Screenshot salvato: %s", output)
        finally:
            pagina.close()

    def verifica_disponibilita(self, urls: list[str]) -> list[dict]:
        """Verifica la disponibilita di una lista di URL."""
        risultati = []
        pagina = self._browser.new_page()

        for url in urls:
            inizio = datetime.now()
            try:
                risposta = pagina.goto(url, wait_until="domcontentloaded", timeout=15000)
                durata = (datetime.now() - inizio).total_seconds()
                risultati.append({
                    "url": url,
                    "stato": risposta.status if risposta else 0,
                    "ok": risposta.ok if risposta else False,
                    "durata_sec": durata,
                })
            except Exception as e:
                durata = (datetime.now() - inizio).total_seconds()
                risultati.append({
                    "url": url,
                    "stato": 0,
                    "ok": False,
                    "durata_sec": durata,
                    "errore": str(e),
                })

        pagina.close()
        return risultati

    def scraping_autenticato(
        self,
        login_url: str,
        target_url: str,
        credenziali: dict,
        selettori: dict,
    ) -> str:
        """
        Esegue login e poi naviga a una pagina protetta per estrarre contenuto.
        selettori: {"username": "#user", "password": "#pass", "submit": "button[type=submit]", "contenuto": ".data"}
        """
        pagina = self._browser.new_page()
        try:
            pagina.goto(login_url, wait_until="networkidle")
            pagina.fill(selettori["username"], credenziali["username"])
            pagina.fill(selettori["password"], credenziali["password"])
            pagina.click(selettori["submit"])
            pagina.wait_for_load_state("networkidle")

            pagina.goto(target_url, wait_until="networkidle")
            contenuto = pagina.inner_text(selettori["contenuto"])
            return contenuto
        finally:
            pagina.close()


# Utilizzo
# with AutomazioneBrowser(headless=True) as browser:
#     # Screenshot di una pagina
#     browser.screenshot_pagina("https://esempio.com", "/tmp/home.png")
#
#     # Verifica disponibilita di piu siti
#     risultati = browser.verifica_disponibilita([
#         "https://sito1.com",
#         "https://sito2.com",
#         "https://api.interna.com/health",
#     ])
#     for r in risultati:
#         stato = "OK" if r["ok"] else "ERRORE"
#         print(f"  [{stato}] {r['url']} — {r['durata_sec']:.2f}s")
```

---

## FAQ

### 1. Perche subprocess.run e preferibile a os.system?

`subprocess.run` offre: cattura di stdout/stderr, gestione del return code, timeout, esecuzione senza shell (previene command injection), e un'API coerente. `os.system` non cattura l'output, non gestisce errori e usa sempre la shell.

### 2. Come gestisco i segreti negli script di automazione?

Mai hardcoded nel codice. Usare: variabili d'ambiente (`os.environ`), file `.env` caricati con `python-dotenv` (non versionati), oppure un secret manager (HashiCorp Vault, AWS Secrets Manager). Validare la presenza dei segreti all'avvio.

### 3. APScheduler o cron?

**APScheduler** quando lo scheduling e parte dell'applicazione Python (web app, daemon). **Cron** quando gli script sono indipendenti e il sistema operativo gestisce l'esecuzione. APScheduler offre persistence dei job (con SQLAlchemy o MongoDB) e trigger piu flessibili.

### 4. Come prevengo esecuzioni concorrenti dello stesso script?

Usare file lock con `fcntl.flock()` su Linux/macOS o `msvcrt.locking()` su Windows. In alternativa, APScheduler con `max_instances=1` previene esecuzioni sovrapposte nativamente.

### 5. Fabric 3 o Ansible per l'automazione remota?

**Fabric** per task semplici su pochi server (deploy, restart, log collection). **Ansible** per infrastruttura complessa con inventari, ruoli, e idempotenza garantita. `ansible-runner` permette di usare Ansible da Python per il meglio di entrambi.

### 6. Come gestisco gli errori in catene di operazioni?

Pattern "fail-fast con cleanup": eseguire ogni operazione in ordine, interrompere alla prima failure, e eseguire il rollback delle operazioni gia completate. Usare context manager personalizzati per il cleanup automatico delle risorse.

### 7. watchdog funziona su tutti i sistemi operativi?

Si. Su Linux usa `inotify`, su macOS usa `FSEvents`, su Windows usa `ReadDirectoryChangesW`. Le differenze sono trasparenti grazie all'astrazione fornita dalla libreria. Su filesystem di rete (NFS, CIFS) il polling e talvolta necessario.

### 8. Come testo uno script di automazione senza eseguire le azioni reali?

Implementare una modalita `--dry-run` che logga le azioni senza eseguirle. Strutturare il codice con dependency injection: le funzioni ricevono un "executor" che in test e un mock. Usare `unittest.mock.patch` per sostituire `subprocess.run` e le connessioni SSH.

### 9. Come monitoro le automazioni in produzione?

Implementare: (1) heartbeat periodico (file timestamp o endpoint HTTP), (2) logging strutturato con livelli appropriati, (3) metriche di esecuzione (durata, successo/fallimento) esportate a Prometheus o scritte in un file JSON, (4) alert su Slack/email per fallimenti.

### 10. Come gestisco la parallelizzazione negli script di automazione?

`concurrent.futures.ThreadPoolExecutor` per operazioni I/O-bound (SSH, HTTP, file). `ProcessPoolExecutor` per operazioni CPU-bound. `asyncio` per concorrenza piu fine. Limitare sempre il numero di worker per non sovraccaricare i sistemi target.

---

## Esercizi

### Esercizio 1 — subprocess sicuro (Fondamentale)

Scrivere un modulo `safe_exec.py` che avvolga `subprocess.run` con: `shell=False` forzato, timeout obbligatorio, validazione del percorso dell'eseguibile, logging strutturato di input/output, gestione di tutti i codici di uscita. Testare con almeno 5 comandi diversi.

### Esercizio 2 — Monitoraggio filesystem con watchdog

Creare uno script che monitora una cartella di upload (`/opt/uploads`), e per ogni file CSV creato: (1) lo valida (encoding, numero colonne), (2) lo sposta in `/opt/dati/`, (3) lo rinomina con timestamp, (4) registra l'operazione in un log. Gestire file corrotti e duplicati.

### Esercizio 3 — Scheduler con APScheduler

Implementare un daemon Python con APScheduler che esegue: backup incrementale ogni ora, pulizia log ogni giorno alle 03:00, report settimanale ogni lunedi alle 08:00. I job devono persistere in SQLite e sopravvivere ai restart. Implementare un endpoint HTTP per visualizzare lo stato dei job.

### Esercizio 4 — Deploy multi-server con Fabric

Scrivere un `fabfile.py` per il deploy di un'applicazione su 3 server: upload del pacchetto, stop servizio, aggiornamento, start servizio, health check. Se il health check fallisce, eseguire il rollback automatico alla versione precedente.

### Esercizio 5 — Automazione con ansible-runner

Creare uno script Python che utilizza `ansible-runner` per: (1) aggiornare i pacchetti di sistema, (2) distribuire un file di configurazione da un template Jinja2, (3) riavviare un servizio. Catturare gli eventi Ansible e generare un report JSON.

### Esercizio 6 — Backup automatizzato con verifica

Scrivere uno script di backup che: comprima una cartella in `.tar.gz`, calcoli il checksum SHA-256, lo carichi su un server remoto via SFTP (paramiko), verifichi l'integrita confrontando i checksum, e invii un report via email. Gestire interruzioni e retry.

### Esercizio 7 — System health dashboard

Creare uno script che raccoglie metriche di sistema (CPU, RAM, disco, servizi systemd) da N server via SSH, aggrega i dati in un report HTML generato con Jinja2, e lo invia via email ogni mattina. Implementare parallelismo con `concurrent.futures`.

### Esercizio 8 — Pipeline di automazione end-to-end

Progettare e implementare una pipeline completa: (1) monitoraggio filesystem per nuovi file CSV, (2) validazione e pulizia dati con pandas, (3) caricamento in SQLite, (4) generazione report Excel con openpyxl, (5) invio email con allegato. Ogni fase deve avere logging e retry.

---

## Letture

- Documentazione subprocess (Python stdlib). https://docs.python.org/3/library/subprocess.html
- Documentazione pathlib (Python stdlib). https://docs.python.org/3/library/pathlib.html
- Documentazione APScheduler. https://apscheduler.readthedocs.io/en/3.x/
- Documentazione watchdog. https://python-watchdog.readthedocs.io/en/stable/
- Documentazione Fabric 3. https://www.fabfile.org/
- Documentazione paramiko. https://www.paramiko.org/
- Documentazione ansible-runner. https://ansible-runner.readthedocs.io/en/stable/
- Documentazione psutil. https://psutil.readthedocs.io/en/latest/
- Documentazione schedule. https://schedule.readthedocs.io/en/stable/
- Documentazione python-dotenv. https://saurabh-kumar.com/python-dotenv/
- Documentazione Jinja2. https://jinja.palletsprojects.com/en/3.1.x/
- Real Python — subprocess. https://realpython.com/python-subprocess/
- CWE-78: OS Command Injection. https://cwe.mitre.org/data/definitions/78.html
- Documentazione pexpect. https://pexpect.readthedocs.io/en/stable/
- Documentazione pyautogui. https://pyautogui.readthedocs.io/en/latest/
- Documentazione pygetwindow. https://github.com/asweigart/PyGetWindow
- Documentazione python-docx. https://python-docx.readthedocs.io/en/latest/
- Documentazione pypdf. https://pypdf.readthedocs.io/en/stable/
- Documentazione boto3 (AWS SDK). https://boto3.amazonaws.com/v1/documentation/api/latest/index.html
- Documentazione azure-sdk-for-python. https://learn.microsoft.com/en-us/azure/developer/python/sdk/azure-sdk-overview
- Documentazione tenacity. https://tenacity.readthedocs.io/en/latest/
- Documentazione dynaconf. https://www.dynaconf.com/
- Documentazione Playwright Python. https://playwright.dev/python/docs/intro

---

## Glossario

| Termine | Definizione |
|---------|-------------|
| **ansible-runner** | Libreria Python per eseguire playbook Ansible programmaticamente, integrando Ansible in applicazioni Python. |
| **APScheduler** | Advanced Python Scheduler — libreria per la schedulazione di task con trigger cron, intervallo e data. |
| **Backoff esponenziale** | Strategia di retry in cui l'intervallo tra i tentativi cresce esponenzialmente (es. 1s, 2s, 4s, 8s). |
| **Command injection** | Vulnerabilita in cui input non sanitizzato viene eseguito come comando di sistema (CWE-78). |
| **Context manager** | Oggetto Python che gestisce le risorse con `__enter__`/`__exit__`, usato con `with` per garantire il cleanup. |
| **Cron** | Scheduler di sistema Unix che esegue comandi a intervalli regolari secondo espressioni temporali (`crontab`). |
| **Debounce** | Tecnica per ignorare eventi ripetuti in rapida successione, elaborando solo l'ultimo di una serie. |
| **Dry-run** | Modalita di esecuzione che mostra le azioni che verrebbero eseguite senza effettivamente eseguirle. |
| **Fabric** | Libreria Python per eseguire comandi su host remoti via SSH, basata su Invoke e Paramiko (v3.x). |
| **File lock** | Meccanismo per impedire l'accesso concorrente a un file, usato per prevenire esecuzioni parallele di script. |
| **Heartbeat** | Segnale periodico che conferma che un processo e attivo e funzionante. |
| **Idempotenza** | Proprieta di un'operazione che produce lo stesso risultato se eseguita una o piu volte. |
| **inotify** | Sottosistema del kernel Linux per il monitoraggio delle modifiche al filesystem. |
| **Paramiko** | Libreria Python per connessioni SSH/SFTP, usata come backend da Fabric e altri strumenti. |
| **psutil** | Libreria Python per il monitoraggio delle risorse di sistema (CPU, memoria, disco, rete, processi). |
| **schedule** | Libreria leggera per la schedulazione in-process di task a intervalli regolari. |
| **shell=False** | Parametro di `subprocess.run` che esegue il comando senza interpretazione della shell — default e raccomandato. |
| **systemd** | Sistema di init e gestione servizi per Linux, controllabile programmaticamente via `systemctl`. |
| **Tenacity** | Libreria Python per retry con backoff esponenziale, jitter e condizioni configurabili. |
| **watchdog** | Libreria Python per il monitoraggio delle modifiche al filesystem tramite eventi OS nativi. |
| **boto3** | SDK ufficiale AWS per Python — gestione programmatica di S3, EC2, Lambda, CloudWatch e tutti i servizi AWS. |
| **azure-sdk** | Insieme di librerie Python per l'automazione di risorse Microsoft Azure (VM, Blob Storage, Resource Groups). |
| **Circuit Breaker** | Pattern di resilienza che interrompe le chiamate a un servizio guasto, evitando sovraccarico e consentendo il recupero. |
| **dynaconf** | Libreria Python per la gestione multi-ambiente di configurazioni, con supporto TOML, YAML, .env, Redis e Vault. |
| **pexpect** | Libreria Python per l'automazione di processi interattivi (SSH, FTP, passwd) tramite pseudo-terminale. |
| **Playwright** | Framework Microsoft per browser automation con supporto Chromium, Firefox e WebKit, API sync e async. |
| **pyautogui** | Libreria Python per il controllo programmatico di mouse e tastiera, con riconoscimento immagini sullo schermo. |
| **pygetwindow** | Libreria Python per il controllo delle finestre desktop: posizionamento, ridimensionamento, focus. |
| **pypdf** | Libreria Python per la manipolazione di PDF: merge, split, cifratura, watermark, estrazione testo e metadati. |
| **python-docx** | Libreria Python per la creazione e manipolazione di documenti Word (.docx) con paragrafi, tabelle e stili. |
| **Signal handling** | Gestione dei segnali POSIX (SIGTERM, SIGHUP, SIGUSR1) per il controllo di daemon e processi long-running. |
| **Webhook** | Callback HTTP che un servizio invia a un URL quando si verifica un evento — usato per notifiche Slack, Discord, Teams. |

---

> **Moduli correlati**: [15-web-scraping.md](15-web-scraping.md) (scraping automatizzato), [17-network-programming.md](17-network-programming.md) (SSH, SMTP, SNMP), [07-error-handling-e-logging.md](07-error-handling-e-logging.md) (logging strutturato), [10-programmazione-asincrona.md](10-programmazione-asincrona.md) (asyncio per concorrenza), [19-cli-tools.md](19-cli-tools.md) (CLI per script di automazione), [31-osservabilita-otel-prometheus.md](31-osservabilita-otel-prometheus.md) (monitoraggio).